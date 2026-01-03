"""
State Courts API Integration

Integration with major state court systems including California Courts,
New York eCourts, Texas re:SearchTX, Florida eCourts, and Illinois Odyssey.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from ...core.config import settings
from ...shared.utils.api_client import BaseAPIClient, APIResponse, HTTPMethod
from .federal_courts import CourtCase, CourtDocument

logger = logging.getLogger(__name__)

class StateJurisdiction(Enum):
    """State court jurisdictions"""
    CALIFORNIA = "ca"
    NEW_YORK = "ny"
    TEXAS = "tx"
    FLORIDA = "fl"
    ILLINOIS = "il"
    PENNSYLVANIA = "pa"
    OHIO = "oh"
    MICHIGAN = "mi"
    GEORGIA = "ga"
    NORTH_CAROLINA = "nc"

class StateCourtLevel(Enum):
    """State court levels"""
    SUPREME_COURT = "supreme"
    APPELLATE_COURT = "appellate"
    SUPERIOR_COURT = "superior"
    DISTRICT_COURT = "district"
    MUNICIPAL_COURT = "municipal"
    FAMILY_COURT = "family"
    PROBATE_COURT = "probate"
    JUVENILE_COURT = "juvenile"

@dataclass
class StateCourtCase(CourtCase):
    """State court case with additional state-specific fields"""
    jurisdiction: StateJurisdiction
    court_level: StateCourtLevel
    county: str
    case_type_code: str
    filing_fee: float = 0.0
    public_access: bool = True
    sealed: bool = False
    state_specific_data: Dict[str, Any] = field(default_factory=dict)

class CaliforniaCourtAPI(BaseAPIClient):
    """
    California Courts API Integration
    Integrates with California's court case management system
    """

    def __init__(self):
        super().__init__("https://www.courts.ca.gov/webservices")
        self.api_key = getattr(settings, 'CA_COURTS_API_KEY', '')
        self.counties = self._load_ca_counties()

    def _load_ca_counties(self) -> List[str]:
        """Load California counties"""
        return [
            "Alameda", "Alpine", "Amador", "Butte", "Calaveras",
            "Colusa", "Contra Costa", "Del Norte", "El Dorado", "Fresno",
            "Glenn", "Humboldt", "Imperial", "Inyo", "Kern",
            "Kings", "Lake", "Lassen", "Los Angeles", "Madera",
            "Marin", "Mariposa", "Mendocino", "Merced", "Modoc",
            "Mono", "Monterey", "Napa", "Nevada", "Orange",
            "Placer", "Plumas", "Riverside", "Sacramento", "San Benito",
            "San Bernardino", "San Diego", "San Francisco", "San Joaquin", "San Luis Obispo",
            "San Mateo", "Santa Barbara", "Santa Clara", "Santa Cruz", "Shasta",
            "Sierra", "Siskiyou", "Solano", "Sonoma", "Stanislaus",
            "Sutter", "Tehama", "Trinity", "Tulare", "Tuolumne",
            "Ventura", "Yolo", "Yuba"
        ]

    async def search_cases(self, county: str, **search_criteria) -> List[StateCourtCase]:
        """Search California court cases"""
        try:
            if county not in self.counties:
                logger.error(f"Invalid California county: {county}")
                return []

            params = {
                'county': county,
                'api_key': self.api_key,
                **search_criteria
            }

            response = await self.get('/case_search', params=params)

            if response.status_code == 200:
                return self._parse_ca_case_results(response.json(), county)
            else:
                logger.error(f"California court search failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching California cases: {str(e)}")
            return []

    def _parse_ca_case_results(self, data: Dict[str, Any], county: str) -> List[StateCourtCase]:
        """Parse California case search results"""
        cases = []
        try:
            for case_data in data.get('cases', []):
                case = StateCourtCase(
                    case_number=case_data.get('case_number', ''),
                    case_name=case_data.get('case_title', ''),
                    district=None,  # State court, no federal district
                    judge=case_data.get('judge_name', ''),
                    filing_date=datetime.fromisoformat(case_data.get('filing_date', '')),
                    case_type=case_data.get('case_type', ''),
                    status=case_data.get('status', ''),
                    jurisdiction=StateJurisdiction.CALIFORNIA,
                    court_level=StateCourtLevel.SUPERIOR_COURT,
                    county=county,
                    case_type_code=case_data.get('case_type_code', ''),
                    filing_fee=float(case_data.get('filing_fee', 0)),
                    state_specific_data={
                        'department': case_data.get('department'),
                        'calendar_number': case_data.get('calendar_number')
                    }
                )
                cases.append(case)
        except Exception as e:
            logger.error(f"Error parsing California case results: {str(e)}")

        return cases

    async def get_case_details(self, case_number: str, county: str) -> Optional[StateCourtCase]:
        """Get detailed California case information"""
        try:
            params = {
                'case_number': case_number,
                'county': county,
                'api_key': self.api_key
            }

            response = await self.get('/case_details', params=params)

            if response.status_code == 200:
                data = response.json()
                return self._parse_ca_case_details(data, county)

        except Exception as e:
            logger.error(f"Error getting California case details: {str(e)}")

        return None

    def _parse_ca_case_details(self, data: Dict[str, Any], county: str) -> StateCourtCase:
        """Parse detailed California case information"""
        return StateCourtCase(
            case_number=data.get('case_number', ''),
            case_name=data.get('case_title', ''),
            district=None,
            judge=data.get('judge_name', ''),
            filing_date=datetime.fromisoformat(data.get('filing_date', '')),
            case_type=data.get('case_type', ''),
            status=data.get('status', ''),
            jurisdiction=StateJurisdiction.CALIFORNIA,
            court_level=StateCourtLevel.SUPERIOR_COURT,
            county=county,
            case_type_code=data.get('case_type_code', ''),
            parties=data.get('parties', []),
            attorneys=data.get('attorneys', []),
            docket_entries=data.get('docket_entries', [])
        )

class NewYorkECourtAPI(BaseAPIClient):
    """
    New York eCourts API Integration
    Integrates with New York State's electronic court system
    """

    def __init__(self):
        super().__init__("https://iapps.courts.state.ny.us")
        self.api_key = getattr(settings, 'NY_ECOURTS_API_KEY', '')

    async def search_cases(self, court_type: str = "Supreme", **search_criteria) -> List[StateCourtCase]:
        """Search New York court cases"""
        try:
            params = {
                'court_type': court_type,
                'api_key': self.api_key,
                **search_criteria
            }

            response = await self.get('/webcivil/CaseLookup', params=params)

            if response.status_code == 200:
                return self._parse_ny_case_results(response.json())

        except Exception as e:
            logger.error(f"Error searching New York cases: {str(e)}")

        return []

    def _parse_ny_case_results(self, data: Dict[str, Any]) -> List[StateCourtCase]:
        """Parse New York case search results"""
        cases = []
        try:
            for case_data in data.get('cases', []):
                case = StateCourtCase(
                    case_number=case_data.get('index_number', ''),
                    case_name=case_data.get('case_title', ''),
                    district=None,
                    judge=case_data.get('judge', ''),
                    filing_date=datetime.fromisoformat(case_data.get('filing_date', '')),
                    case_type=case_data.get('case_type', ''),
                    status=case_data.get('status', ''),
                    jurisdiction=StateJurisdiction.NEW_YORK,
                    court_level=StateCourtLevel.SUPREME_COURT,
                    county=case_data.get('county', ''),
                    case_type_code=case_data.get('case_type_code', ''),
                    state_specific_data={
                        'index_number': case_data.get('index_number'),
                        'court_location': case_data.get('court_location')
                    }
                )
                cases.append(case)
        except Exception as e:
            logger.error(f"Error parsing New York case results: {str(e)}")

        return cases

class TexasReSearchAPI(BaseAPIClient):
    """
    Texas re:SearchTX API Integration
    Integrates with Texas court case search system
    """

    def __init__(self):
        super().__init__("https://search.txcourts.gov")
        self.api_key = getattr(settings, 'TX_RESEARCH_API_KEY', '')

    async def search_cases(self, **search_criteria) -> List[StateCourtCase]:
        """Search Texas court cases"""
        try:
            params = {
                'api_key': self.api_key,
                **search_criteria
            }

            response = await self.get('/api/cases', params=params)

            if response.status_code == 200:
                return self._parse_tx_case_results(response.json())

        except Exception as e:
            logger.error(f"Error searching Texas cases: {str(e)}")

        return []

    def _parse_tx_case_results(self, data: Dict[str, Any]) -> List[StateCourtCase]:
        """Parse Texas case search results"""
        cases = []
        try:
            for case_data in data.get('results', []):
                case = StateCourtCase(
                    case_number=case_data.get('cause_number', ''),
                    case_name=case_data.get('case_style', ''),
                    district=None,
                    judge=case_data.get('judge_name', ''),
                    filing_date=datetime.fromisoformat(case_data.get('file_date', '')),
                    case_type=case_data.get('case_type', ''),
                    status=case_data.get('disposition', ''),
                    jurisdiction=StateJurisdiction.TEXAS,
                    court_level=StateCourtLevel.DISTRICT_COURT,
                    county=case_data.get('county', ''),
                    case_type_code=case_data.get('case_type_code', ''),
                    state_specific_data={
                        'cause_number': case_data.get('cause_number'),
                        'court_number': case_data.get('court_number')
                    }
                )
                cases.append(case)
        except Exception as e:
            logger.error(f"Error parsing Texas case results: {str(e)}")

        return cases

class FloridaECourtAPI(BaseAPIClient):
    """
    Florida eCourts API Integration
    Integrates with Florida's electronic court records system
    """

    def __init__(self):
        super().__init__("https://www.flcourts.org")
        self.api_key = getattr(settings, 'FL_ECOURTS_API_KEY', '')

    async def search_cases(self, **search_criteria) -> List[StateCourtCase]:
        """Search Florida court cases"""
        try:
            params = {
                'api_key': self.api_key,
                **search_criteria
            }

            response = await self.get('/api/case_search', params=params)

            if response.status_code == 200:
                return self._parse_fl_case_results(response.json())

        except Exception as e:
            logger.error(f"Error searching Florida cases: {str(e)}")

        return []

    def _parse_fl_case_results(self, data: Dict[str, Any]) -> List[StateCourtCase]:
        """Parse Florida case search results"""
        cases = []
        try:
            for case_data in data.get('cases', []):
                case = StateCourtCase(
                    case_number=case_data.get('case_number', ''),
                    case_name=case_data.get('case_name', ''),
                    district=None,
                    judge=case_data.get('judge', ''),
                    filing_date=datetime.fromisoformat(case_data.get('filed_date', '')),
                    case_type=case_data.get('case_type', ''),
                    status=case_data.get('case_status', ''),
                    jurisdiction=StateJurisdiction.FLORIDA,
                    court_level=StateCourtLevel.SUPERIOR_COURT,
                    county=case_data.get('county', ''),
                    case_type_code=case_data.get('type_code', ''),
                    state_specific_data={
                        'division': case_data.get('division'),
                        'location_code': case_data.get('location_code')
                    }
                )
                cases.append(case)
        except Exception as e:
            logger.error(f"Error parsing Florida case results: {str(e)}")

        return cases

class IllinoisOdysseyAPI(BaseAPIClient):
    """
    Illinois Odyssey API Integration
    Integrates with Illinois court case management system
    """

    def __init__(self):
        super().__init__("https://www.illinoiscourts.gov")
        self.api_key = getattr(settings, 'IL_ODYSSEY_API_KEY', '')

    async def search_cases(self, **search_criteria) -> List[StateCourtCase]:
        """Search Illinois court cases"""
        try:
            params = {
                'api_key': self.api_key,
                **search_criteria
            }

            response = await self.get('/api/odyssey/search', params=params)

            if response.status_code == 200:
                return self._parse_il_case_results(response.json())

        except Exception as e:
            logger.error(f"Error searching Illinois cases: {str(e)}")

        return []

    def _parse_il_case_results(self, data: Dict[str, Any]) -> List[StateCourtCase]:
        """Parse Illinois case search results"""
        cases = []
        try:
            for case_data in data.get('cases', []):
                case = StateCourtCase(
                    case_number=case_data.get('case_number', ''),
                    case_name=case_data.get('case_title', ''),
                    district=None,
                    judge=case_data.get('assigned_judge', ''),
                    filing_date=datetime.fromisoformat(case_data.get('filing_date', '')),
                    case_type=case_data.get('case_category', ''),
                    status=case_data.get('case_status', ''),
                    jurisdiction=StateJurisdiction.ILLINOIS,
                    court_level=StateCourtLevel.SUPERIOR_COURT,
                    county=case_data.get('county', ''),
                    case_type_code=case_data.get('case_type', ''),
                    state_specific_data={
                        'court_division': case_data.get('division'),
                        'track_number': case_data.get('track')
                    }
                )
                cases.append(case)
        except Exception as e:
            logger.error(f"Error parsing Illinois case results: {str(e)}")

        return cases

class StateCourtManager:
    """
    Unified manager for all state court integrations
    """

    def __init__(self):
        self.integrations = {
            StateJurisdiction.CALIFORNIA: CaliforniaCourtAPI(),
            StateJurisdiction.NEW_YORK: NewYorkECourtAPI(),
            StateJurisdiction.TEXAS: TexasReSearchAPI(),
            StateJurisdiction.FLORIDA: FloridaECourtAPI(),
            StateJurisdiction.ILLINOIS: IllinoisOdysseyAPI()
        }

    async def search_all_states(self, **search_criteria) -> Dict[StateJurisdiction, List[StateCourtCase]]:
        """Search cases across all supported state jurisdictions"""
        results = {}

        tasks = []
        for jurisdiction, integration in self.integrations.items():
            task = asyncio.create_task(
                self._search_single_state(jurisdiction, integration, **search_criteria)
            )
            tasks.append((jurisdiction, task))

        for jurisdiction, task in tasks:
            try:
                cases = await task
                results[jurisdiction] = cases
            except Exception as e:
                logger.error(f"Error searching {jurisdiction}: {str(e)}")
                results[jurisdiction] = []

        return results

    async def _search_single_state(self, jurisdiction: StateJurisdiction,
                                  integration: BaseAPIClient,
                                  **search_criteria) -> List[StateCourtCase]:
        """Search cases in a single state"""
        try:
            return await integration.search_cases(**search_criteria)
        except Exception as e:
            logger.error(f"Error in {jurisdiction} search: {str(e)}")
            return []

    async def search_specific_states(self, jurisdictions: List[StateJurisdiction],
                                   **search_criteria) -> Dict[StateJurisdiction, List[StateCourtCase]]:
        """Search cases in specified state jurisdictions only"""
        results = {}

        for jurisdiction in jurisdictions:
            if jurisdiction in self.integrations:
                integration = self.integrations[jurisdiction]
                try:
                    cases = await integration.search_cases(**search_criteria)
                    results[jurisdiction] = cases
                except Exception as e:
                    logger.error(f"Error searching {jurisdiction}: {str(e)}")
                    results[jurisdiction] = []

        return results

    def get_supported_jurisdictions(self) -> List[StateJurisdiction]:
        """Get list of supported state jurisdictions"""
        return list(self.integrations.keys())

    async def get_jurisdiction_info(self, jurisdiction: StateJurisdiction) -> Dict[str, Any]:
        """Get information about a specific jurisdiction"""
        info = {
            'jurisdiction': jurisdiction.value,
            'supported': jurisdiction in self.integrations,
            'integration_type': type(self.integrations.get(jurisdiction)).__name__ if jurisdiction in self.integrations else None
        }

        if jurisdiction == StateJurisdiction.CALIFORNIA:
            info['counties'] = self.integrations[jurisdiction].counties

        return info