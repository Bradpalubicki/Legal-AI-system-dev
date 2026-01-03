"""
State Bar API Integrations
Comprehensive integration with all 50 state bar associations for attorney verification,
disciplinary records, and professional status monitoring.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote
import re
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AttorneyRecord:
    """Standardized attorney record"""
    bar_number: str
    state: str
    first_name: str
    last_name: str
    middle_name: Optional[str]
    suffix: Optional[str]

    # Status information
    status: str  # active, inactive, suspended, disbarred, retired
    admission_date: Optional[str]
    good_standing: bool

    # Contact information
    firm_name: Optional[str]
    address: Optional[Dict[str, str]]
    phone: Optional[str]
    email: Optional[str]

    # Practice information
    practice_areas: List[str]
    admissions: List[str]  # Other jurisdictions

    # Disciplinary information
    disciplinary_actions: List[Dict[str, Any]]

    # Additional data
    last_verified: datetime
    data_source: str

@dataclass
class DisciplinaryAction:
    """Disciplinary action record"""
    action_id: str
    attorney_bar_number: str
    state: str
    action_type: str  # reprimand, suspension, disbarment, etc.
    effective_date: str
    end_date: Optional[str]
    description: str
    case_number: Optional[str]
    public_record: bool
    last_updated: datetime

class StateBarAPIConfig:
    """Configuration for state bar APIs"""

    # State bar API endpoints and configurations
    STATE_CONFIGS = {
        'AL': {
            'name': 'Alabama State Bar',
            'base_url': 'https://www.alabar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 100,  # requests per hour
            'format': 'json'
        },
        'AK': {
            'name': 'Alaska Bar Association',
            'base_url': 'https://alaskabar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 50,
            'format': 'json'
        },
        'AZ': {
            'name': 'State Bar of Arizona',
            'base_url': 'https://www.azbar.org/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 200,
            'format': 'json'
        },
        'AR': {
            'name': 'Arkansas Bar Association',
            'base_url': 'https://www.arkbar.com/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'CA': {
            'name': 'State Bar of California',
            'base_url': 'https://www.calbar.ca.gov/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 500,
            'format': 'json',
            'special_features': ['public_records_search', 'disciplinary_history']
        },
        'CO': {
            'name': 'Colorado Bar Association',
            'base_url': 'https://www.cobar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'CT': {
            'name': 'Connecticut Bar Association',
            'base_url': 'https://www.ctbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'DE': {
            'name': 'Delaware State Bar Association',
            'base_url': 'https://www.dsba.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'FL': {
            'name': 'The Florida Bar',
            'base_url': 'https://www.floridabar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 300,
            'format': 'json',
            'special_features': ['public_disciplinary_search']
        },
        'GA': {
            'name': 'State Bar of Georgia',
            'base_url': 'https://www.gabar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'HI': {
            'name': 'Hawaii State Bar Association',
            'base_url': 'https://www.hsba.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 50,
            'format': 'json'
        },
        'ID': {
            'name': 'Idaho State Bar',
            'base_url': 'https://isb.idaho.gov/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'IL': {
            'name': 'Illinois State Bar Association',
            'base_url': 'https://www.isba.org/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 250,
            'format': 'json'
        },
        'IN': {
            'name': 'Indiana State Bar Association',
            'base_url': 'https://www.inbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'IA': {
            'name': 'Iowa State Bar Association',
            'base_url': 'https://www.iowabar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'KS': {
            'name': 'Kansas Bar Association',
            'base_url': 'https://www.ksbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'KY': {
            'name': 'Kentucky Bar Association',
            'base_url': 'https://www.kybar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'LA': {
            'name': 'Louisiana State Bar Association',
            'base_url': 'https://www.lsba.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'ME': {
            'name': 'Maine State Bar Association',
            'base_url': 'https://www.mainebar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'MD': {
            'name': 'Maryland State Bar Association',
            'base_url': 'https://www.msba.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'MA': {
            'name': 'Massachusetts Bar Association',
            'base_url': 'https://www.massbar.org/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 200,
            'format': 'json'
        },
        'MI': {
            'name': 'State Bar of Michigan',
            'base_url': 'https://www.michbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 200,
            'format': 'json'
        },
        'MN': {
            'name': 'Minnesota State Bar Association',
            'base_url': 'https://www.mnbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'MS': {
            'name': 'Mississippi Bar',
            'base_url': 'https://www.msbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'MO': {
            'name': 'The Missouri Bar',
            'base_url': 'https://www.mobar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'MT': {
            'name': 'State Bar of Montana',
            'base_url': 'https://www.montanabar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'NE': {
            'name': 'Nebraska State Bar Association',
            'base_url': 'https://www.nebar.com/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'NV': {
            'name': 'State Bar of Nevada',
            'base_url': 'https://www.nvbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'NH': {
            'name': 'New Hampshire Bar Association',
            'base_url': 'https://www.nhbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'NJ': {
            'name': 'New Jersey State Bar Association',
            'base_url': 'https://www.njsba.com/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 200,
            'format': 'json'
        },
        'NM': {
            'name': 'State Bar of New Mexico',
            'base_url': 'https://www.nmbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'NY': {
            'name': 'New York State Bar Association',
            'base_url': 'https://www.nysba.org/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 300,
            'format': 'json',
            'special_features': ['multiple_departments', 'appellate_divisions']
        },
        'NC': {
            'name': 'North Carolina State Bar',
            'base_url': 'https://www.ncbar.gov/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 150,
            'format': 'json'
        },
        'ND': {
            'name': 'State Bar Association of North Dakota',
            'base_url': 'https://www.sband.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'OH': {
            'name': 'Ohio State Bar Association',
            'base_url': 'https://www.ohiobar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 200,
            'format': 'json'
        },
        'OK': {
            'name': 'Oklahoma Bar Association',
            'base_url': 'https://www.okbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'OR': {
            'name': 'Oregon State Bar',
            'base_url': 'https://www.osb.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 150,
            'format': 'json'
        },
        'PA': {
            'name': 'Pennsylvania Bar Association',
            'base_url': 'https://www.pabar.org/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 200,
            'format': 'json'
        },
        'RI': {
            'name': 'Rhode Island Bar Association',
            'base_url': 'https://www.ribar.com/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'SC': {
            'name': 'South Carolina Bar',
            'base_url': 'https://www.scbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'SD': {
            'name': 'State Bar of South Dakota',
            'base_url': 'https://www.statebarofsouthdakota.com/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'TN': {
            'name': 'Tennessee Bar Association',
            'base_url': 'https://www.tba.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'TX': {
            'name': 'State Bar of Texas',
            'base_url': 'https://www.texasbar.com/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 400,
            'format': 'json',
            'special_features': ['grievance_search', 'public_disciplinary_actions']
        },
        'UT': {
            'name': 'Utah State Bar',
            'base_url': 'https://www.utahbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'VT': {
            'name': 'Vermont Bar Association',
            'base_url': 'https://www.vtbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'VA': {
            'name': 'Virginia State Bar',
            'base_url': 'https://www.vsb.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 200,
            'format': 'json'
        },
        'WA': {
            'name': 'Washington State Bar Association',
            'base_url': 'https://www.wsba.org/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 200,
            'format': 'json'
        },
        'WV': {
            'name': 'West Virginia State Bar',
            'base_url': 'https://www.wvbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 100,
            'format': 'json'
        },
        'WI': {
            'name': 'State Bar of Wisconsin',
            'base_url': 'https://www.wisbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 150,
            'format': 'json'
        },
        'WY': {
            'name': 'Wyoming State Bar',
            'base_url': 'https://www.wyomingbar.org/api',
            'auth_type': 'api_key',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'rate_limit': 75,
            'format': 'json'
        },
        'DC': {
            'name': 'District of Columbia Bar',
            'base_url': 'https://www.dcbar.org/api',
            'auth_type': 'oauth2',
            'search_endpoint': '/attorney/search',
            'verify_endpoint': '/attorney/verify',
            'disciplinary_endpoint': '/attorney/disciplinary',
            'rate_limit': 200,
            'format': 'json'
        }
    }

class StateBarAPIClient:
    """Universal client for all state bar APIs"""

    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.config = StateBarAPIConfig()
        self.rate_limiters = {}
        self.cache = {}  # Simple in-memory cache

    async def verify_attorney(self, state: str, bar_number: str = None,
                            name: str = None, **kwargs) -> Dict[str, Any]:
        """Verify attorney status across any state"""
        state = state.upper()

        if state not in self.config.STATE_CONFIGS:
            return {
                'success': False,
                'error': f'State {state} not supported',
                'state': state
            }

        state_config = self.config.STATE_CONFIGS[state]

        try:
            # Check rate limits
            if not await self._check_rate_limit(state):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'state': state
                }

            # Check cache first
            cache_key = f"{state}_{bar_number}_{name}"
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result

            # Make API request
            result = await self._make_state_api_request(state, 'verify', {
                'bar_number': bar_number,
                'name': name,
                **kwargs
            })

            # Parse and standardize result
            attorney_record = await self._parse_attorney_response(state, result)

            response = {
                'success': True,
                'state': state,
                'attorney': asdict(attorney_record) if attorney_record else None,
                'raw_response': result if attorney_record else None
            }

            # Cache successful results
            self._cache_result(cache_key, response, ttl_hours=24)

            return response

        except Exception as e:
            logger.error(f"Error verifying attorney in {state}: {e}")
            return {
                'success': False,
                'error': str(e),
                'state': state
            }

    async def search_attorneys(self, state: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search for attorneys in a specific state"""
        state = state.upper()

        if state not in self.config.STATE_CONFIGS:
            return {
                'success': False,
                'error': f'State {state} not supported',
                'state': state
            }

        try:
            # Check rate limits
            if not await self._check_rate_limit(state):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'state': state
                }

            # Make API request
            result = await self._make_state_api_request(state, 'search', query)

            # Parse results
            attorneys = []
            if result and 'attorneys' in result:
                for attorney_data in result['attorneys']:
                    attorney_record = await self._parse_attorney_response(state, {'attorney': attorney_data})
                    if attorney_record:
                        attorneys.append(asdict(attorney_record))

            return {
                'success': True,
                'state': state,
                'attorneys': attorneys,
                'total_results': len(attorneys)
            }

        except Exception as e:
            logger.error(f"Error searching attorneys in {state}: {e}")
            return {
                'success': False,
                'error': str(e),
                'state': state
            }

    async def get_disciplinary_history(self, state: str, bar_number: str) -> Dict[str, Any]:
        """Get disciplinary history for an attorney"""
        state = state.upper()

        if state not in self.config.STATE_CONFIGS:
            return {
                'success': False,
                'error': f'State {state} not supported',
                'state': state
            }

        state_config = self.config.STATE_CONFIGS[state]

        if 'disciplinary_endpoint' not in state_config:
            return {
                'success': False,
                'error': f'Disciplinary history not available for {state}',
                'state': state
            }

        try:
            # Check rate limits
            if not await self._check_rate_limit(state):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'state': state
                }

            # Make API request
            result = await self._make_state_api_request(state, 'disciplinary', {
                'bar_number': bar_number
            })

            # Parse disciplinary actions
            disciplinary_actions = []
            if result and 'disciplinary_actions' in result:
                for action_data in result['disciplinary_actions']:
                    action = DisciplinaryAction(
                        action_id=action_data.get('id', f"{state}_{bar_number}_{len(disciplinary_actions)}"),
                        attorney_bar_number=bar_number,
                        state=state,
                        action_type=action_data.get('type', 'unknown'),
                        effective_date=action_data.get('effective_date'),
                        end_date=action_data.get('end_date'),
                        description=action_data.get('description', ''),
                        case_number=action_data.get('case_number'),
                        public_record=action_data.get('public_record', True),
                        last_updated=datetime.now()
                    )
                    disciplinary_actions.append(asdict(action))

            return {
                'success': True,
                'state': state,
                'bar_number': bar_number,
                'disciplinary_actions': disciplinary_actions,
                'total_actions': len(disciplinary_actions)
            }

        except Exception as e:
            logger.error(f"Error getting disciplinary history in {state}: {e}")
            return {
                'success': False,
                'error': str(e),
                'state': state
            }

    async def bulk_verify_attorneys(self, attorney_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """Verify multiple attorneys across different states"""
        results = {}
        tasks = []

        # Group by state for efficiency
        by_state = {}
        for attorney in attorney_list:
            state = attorney.get('state', '').upper()
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(attorney)

        # Create verification tasks
        for state, attorneys in by_state.items():
            for attorney in attorneys:
                task = asyncio.create_task(
                    self.verify_attorney(
                        state=state,
                        bar_number=attorney.get('bar_number'),
                        name=attorney.get('name')
                    )
                )
                tasks.append((attorney, task))

        # Execute all tasks
        for attorney, task in tasks:
            try:
                result = await task
                key = f"{attorney.get('state', '')}_{attorney.get('bar_number', 'unknown')}"
                results[key] = result
            except Exception as e:
                key = f"{attorney.get('state', '')}_{attorney.get('bar_number', 'unknown')}"
                results[key] = {
                    'success': False,
                    'error': str(e),
                    'state': attorney.get('state', '')
                }

        return {
            'total_requested': len(attorney_list),
            'total_completed': len(results),
            'results': results
        }

    async def _make_state_api_request(self, state: str, endpoint_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to specific state bar"""
        state_config = self.config.STATE_CONFIGS[state]
        base_url = state_config['base_url']

        endpoint_map = {
            'verify': state_config.get('verify_endpoint', '/attorney/verify'),
            'search': state_config.get('search_endpoint', '/attorney/search'),
            'disciplinary': state_config.get('disciplinary_endpoint', '/attorney/disciplinary')
        }

        endpoint = endpoint_map.get(endpoint_type)
        if not endpoint:
            raise ValueError(f"Endpoint type {endpoint_type} not supported for {state}")

        url = f"{base_url}{endpoint}"

        # Get authentication headers
        headers = await self._get_auth_headers(state)

        # Clean parameters
        clean_params = {k: v for k, v in params.items() if v is not None}

        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            if state_config.get('format') == 'json':
                headers['Content-Type'] = 'application/json'
                async with session.post(url, json=clean_params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"API request failed: {response.status} - {error_text}")
            else:
                # Use GET with query parameters for non-JSON APIs
                async with session.get(url, params=clean_params, headers=headers) as response:
                    if response.status == 200:
                        if 'json' in response.content_type:
                            return await response.json()
                        else:
                            # Handle XML or other formats
                            text = await response.text()
                            return await self._parse_non_json_response(state, text)
                    else:
                        error_text = await response.text()
                        raise Exception(f"API request failed: {response.status} - {error_text}")

    async def _get_auth_headers(self, state: str) -> Dict[str, str]:
        """Get authentication headers for a state"""
        state_config = self.config.STATE_CONFIGS[state]
        auth_type = state_config.get('auth_type', 'api_key')

        headers = {
            'User-Agent': 'LegalAI-StateBarClient/1.0'
        }

        if auth_type == 'api_key':
            api_key = self.credentials.get(f'state_bar_{state.lower()}', {}).get('api_key')
            if api_key:
                headers['X-API-Key'] = api_key
                headers['Authorization'] = f'Bearer {api_key}'

        elif auth_type == 'oauth2':
            # In a real implementation, this would handle OAuth2 token management
            access_token = self.credentials.get(f'state_bar_{state.lower()}', {}).get('access_token')
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'

        return headers

    async def _parse_attorney_response(self, state: str, response: Dict[str, Any]) -> Optional[AttorneyRecord]:
        """Parse attorney response into standardized format"""
        attorney_data = response.get('attorney', response)

        if not attorney_data:
            return None

        try:
            # Extract basic information
            bar_number = attorney_data.get('bar_number') or attorney_data.get('id') or attorney_data.get('license_number')
            first_name = attorney_data.get('first_name', '')
            last_name = attorney_data.get('last_name', '')

            # Parse name if it's in full format
            if not first_name and not last_name:
                full_name = attorney_data.get('name', '')
                if full_name:
                    name_parts = full_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])

            # Extract status information
            status = attorney_data.get('status', 'unknown').lower()
            good_standing = attorney_data.get('good_standing', attorney_data.get('in_good_standing', False))

            # Handle boolean values that might be strings
            if isinstance(good_standing, str):
                good_standing = good_standing.lower() in ['true', 'yes', 'active', '1']

            # Extract contact information
            address = None
            if attorney_data.get('address'):
                address = {
                    'street': attorney_data['address'].get('street', ''),
                    'city': attorney_data['address'].get('city', ''),
                    'state': attorney_data['address'].get('state', state),
                    'zip': attorney_data['address'].get('zip', ''),
                    'country': attorney_data['address'].get('country', 'US')
                }

            # Extract practice areas
            practice_areas = attorney_data.get('practice_areas', [])
            if isinstance(practice_areas, str):
                practice_areas = [area.strip() for area in practice_areas.split(',')]

            # Extract admissions
            admissions = attorney_data.get('admissions', [])
            if isinstance(admissions, str):
                admissions = [adm.strip() for adm in admissions.split(',')]

            # Extract disciplinary actions
            disciplinary_actions = []
            if attorney_data.get('disciplinary_actions'):
                for action in attorney_data['disciplinary_actions']:
                    disciplinary_actions.append({
                        'type': action.get('type', ''),
                        'date': action.get('date', ''),
                        'description': action.get('description', ''),
                        'public': action.get('public', True)
                    })

            return AttorneyRecord(
                bar_number=str(bar_number) if bar_number else '',
                state=state,
                first_name=first_name,
                last_name=last_name,
                middle_name=attorney_data.get('middle_name'),
                suffix=attorney_data.get('suffix'),
                status=status,
                admission_date=attorney_data.get('admission_date'),
                good_standing=good_standing,
                firm_name=attorney_data.get('firm_name'),
                address=address,
                phone=attorney_data.get('phone'),
                email=attorney_data.get('email'),
                practice_areas=practice_areas,
                admissions=admissions,
                disciplinary_actions=disciplinary_actions,
                last_verified=datetime.now(),
                data_source=f"state_bar_{state.lower()}"
            )

        except Exception as e:
            logger.error(f"Error parsing attorney response for {state}: {e}")
            return None

    async def _parse_non_json_response(self, state: str, response_text: str) -> Dict[str, Any]:
        """Parse non-JSON responses (XML, HTML, etc.)"""
        # Try to parse as XML first
        try:
            root = ET.fromstring(response_text)
            return self._xml_to_dict(root)
        except ET.ParseError:
            pass

        # If it's HTML, try to extract relevant information
        if '<html' in response_text.lower():
            return self._parse_html_response(state, response_text)

        # If all else fails, return raw text
        return {'raw_response': response_text}

    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        if element.attrib:
            result.update(element.attrib)

        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()

        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result

    def _parse_html_response(self, state: str, html: str) -> Dict[str, Any]:
        """Parse HTML response for attorney information"""
        # This would implement HTML parsing logic specific to each state's format
        # For now, return a placeholder
        return {
            'format': 'html',
            'state': state,
            'parsed': False,
            'raw_html': html[:1000]  # Truncate for safety
        }

    async def _check_rate_limit(self, state: str) -> bool:
        """Check if request is within rate limits for the state"""
        state_config = self.config.STATE_CONFIGS[state]
        rate_limit = state_config.get('rate_limit', 100)

        # Simple rate limiting implementation
        if state not in self.rate_limiters:
            self.rate_limiters[state] = {
                'requests': 0,
                'reset_time': time.time() + 3600  # 1 hour window
            }

        limiter = self.rate_limiters[state]
        current_time = time.time()

        # Reset if window has passed
        if current_time >= limiter['reset_time']:
            limiter['requests'] = 0
            limiter['reset_time'] = current_time + 3600

        # Check if under limit
        if limiter['requests'] >= rate_limit:
            return False

        limiter['requests'] += 1
        return True

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if still valid"""
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if cached_item['expires'] > time.time():
                return cached_item['data']
            else:
                del self.cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, data: Dict[str, Any], ttl_hours: int = 24):
        """Cache result with TTL"""
        self.cache[cache_key] = {
            'data': data,
            'expires': time.time() + (ttl_hours * 3600)
        }

    async def get_supported_states(self) -> Dict[str, Any]:
        """Get list of supported states and their capabilities"""
        states = {}

        for state_code, config in self.config.STATE_CONFIGS.items():
            states[state_code] = {
                'name': config['name'],
                'rate_limit': config.get('rate_limit', 100),
                'features': {
                    'attorney_search': 'search_endpoint' in config,
                    'attorney_verification': 'verify_endpoint' in config,
                    'disciplinary_history': 'disciplinary_endpoint' in config,
                    'special_features': config.get('special_features', [])
                },
                'auth_type': config.get('auth_type', 'api_key'),
                'format': config.get('format', 'json')
            }

        return {
            'total_states': len(states),
            'states': states,
            'last_updated': datetime.now().isoformat()
        }

# Example usage
async def main():
    """Example usage of state bar API client"""
    # Configure credentials (in real implementation, load from secure storage)
    credentials = {
        'state_bar_ca': {'api_key': 'your_california_api_key'},
        'state_bar_ny': {'access_token': 'your_new_york_access_token'},
        'state_bar_tx': {'api_key': 'your_texas_api_key'}
    }

    client = StateBarAPIClient(credentials)

    # Verify a California attorney
    ca_result = await client.verify_attorney(
        state='CA',
        bar_number='123456'
    )
    print(f"California verification: {ca_result['success']}")

    # Search for attorneys in Texas
    tx_search = await client.search_attorneys(
        state='TX',
        query={'name': 'Smith', 'city': 'Austin'}
    )
    print(f"Texas search results: {tx_search.get('total_results', 0)}")

    # Get disciplinary history in New York
    ny_disciplinary = await client.get_disciplinary_history(
        state='NY',
        bar_number='456789'
    )
    print(f"NY disciplinary actions: {ny_disciplinary.get('total_actions', 0)}")

    # Bulk verification
    attorneys_to_verify = [
        {'state': 'CA', 'bar_number': '123456'},
        {'state': 'NY', 'bar_number': '789012'},
        {'state': 'TX', 'bar_number': '345678'}
    ]

    bulk_results = await client.bulk_verify_attorneys(attorneys_to_verify)
    print(f"Bulk verification: {bulk_results['total_completed']}/{bulk_results['total_requested']} completed")

    # Get supported states
    supported = await client.get_supported_states()
    print(f"Supported states: {supported['total_states']}")

if __name__ == "__main__":
    asyncio.run(main())