"""
Court Data Integration Module for CourtSync

Provides comprehensive integration with court systems, ECF, PACER,
and other legal data sources for automatic hearing detection and calendar sync.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import logging
from abc import ABC, abstractmethod
import asyncio

import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import xmltodict
from dateutil import parser
import pandas as pd

from .hearing_detector import HearingEvent, HearingType, HearingStatus, Location, HearingDetector

logger = logging.getLogger(__name__)


class CourtSystem(Enum):
    """Types of court systems."""
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_APPEALS = "federal_appeals"
    FEDERAL_SUPREME = "federal_supreme"
    STATE_SUPERIOR = "state_superior"
    STATE_APPELLATE = "state_appellate"
    STATE_SUPREME = "state_supreme"
    BANKRUPTCY = "bankruptcy"
    FAMILY = "family"
    PROBATE = "probate"
    MUNICIPAL = "municipal"
    TRAFFIC = "traffic"


class DataSource(Enum):
    """Data sources for court information."""
    ECF = "ecf"  # Electronic Case Filing
    PACER = "pacer"  # Public Access to Court Electronic Records
    STATE_ECF = "state_ecf"  # State Electronic Court Filing
    COURT_WEBSITE = "court_website"
    RSS_FEED = "rss_feed"
    EMAIL_NOTIFICATIONS = "email_notifications"
    CALENDAR_FEED = "calendar_feed"
    API = "api"
    MANUAL_ENTRY = "manual_entry"


class UpdateFrequency(Enum):
    """Update frequency for data sources."""
    REAL_TIME = "real_time"
    EVERY_5_MINUTES = "every_5_minutes"
    EVERY_15_MINUTES = "every_15_minutes"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_DEMAND = "on_demand"


@dataclass
class CourtInfo:
    """Information about a court."""
    court_id: str
    name: str
    system_type: CourtSystem
    jurisdiction: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    ecf_url: Optional[str] = None
    pacer_url: Optional[str] = None
    timezone: str = "UTC"
    business_hours: Optional[Tuple[time, time]] = None
    holidays: List[datetime] = field(default_factory=list)
    
    def full_name(self) -> str:
        """Get full formatted court name."""
        return f"{self.name}, {self.jurisdiction}"


@dataclass
class DataSourceConfig:
    """Configuration for a court data source."""
    source_id: str
    court_id: str
    source_type: DataSource
    enabled: bool = True
    url: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    update_frequency: UpdateFrequency = UpdateFrequency.HOURLY
    filters: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    last_update: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HearingUpdate:
    """Represents an update to hearing information."""
    hearing_id: str
    update_type: str  # created, modified, cancelled, rescheduled
    court_id: str
    source: DataSource
    timestamp: datetime
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    raw_data: Optional[str] = None


class CourtDataProvider(ABC):
    """Abstract base class for court data providers."""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.session = None
        self.driver = None  # For Selenium-based providers
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the court system."""
        pass
    
    @abstractmethod
    async def fetch_hearings(self, start_date: datetime, end_date: datetime) -> List[HearingEvent]:
        """Fetch hearings from the court system."""
        pass
    
    @abstractmethod
    async def get_case_information(self, case_number: str) -> Optional[Dict[str, Any]]:
        """Get detailed case information."""
        pass
    
    @abstractmethod
    async def check_for_updates(self, since: datetime) -> List[HearingUpdate]:
        """Check for updates since the given timestamp."""
        pass
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()


class PACERProvider(CourtDataProvider):
    """PACER (Public Access to Court Electronic Records) provider."""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.base_url = "https://pcl.uscourts.gov"
        self.login_url = f"{self.base_url}/pcl/pages/login.jsf"
        self.authenticated = False
        
    async def authenticate(self) -> bool:
        """Authenticate with PACER."""
        if not self.config.credentials:
            logger.error("PACER credentials not provided")
            return False
        
        try:
            self.session = aiohttp.ClientSession()
            
            # Get login page to extract session tokens
            async with self.session.get(self.login_url) as response:
                login_page = await response.text()
                soup = BeautifulSoup(login_page, 'html.parser')
                
                # Extract CSRF token and other hidden fields
                hidden_inputs = soup.find_all('input', type='hidden')
                form_data = {inp.get('name'): inp.get('value') for inp in hidden_inputs if inp.get('name')}
                
                # Add credentials
                form_data.update({
                    'login:loginName': self.config.credentials['username'],
                    'login:password': self.config.credentials['password'],
                    'login:clientCode': self.config.credentials.get('client_code', ''),
                    'login:fbtnLogin': 'Login'
                })
            
            # Submit login form
            async with self.session.post(self.login_url, data=form_data) as response:
                result_page = await response.text()
                
                # Check for successful login
                if "Welcome" in result_page and "logout" in result_page.lower():
                    self.authenticated = True
                    logger.info("PACER authentication successful")
                    return True
                else:
                    logger.error("PACER authentication failed")
                    return False
        
        except Exception as e:
            logger.error(f"PACER authentication error: {str(e)}")
            return False
    
    async def fetch_hearings(self, start_date: datetime, end_date: datetime) -> List[HearingEvent]:
        """Fetch hearings from PACER."""
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        hearings = []
        
        try:
            # Search for cases with hearings in the date range
            search_url = f"{self.base_url}/pcl/pages/search.jsf"
            
            # Build search parameters
            search_data = {
                'searchType': 'hearing',
                'startDate': start_date.strftime('%m/%d/%Y'),
                'endDate': end_date.strftime('%m/%d/%Y'),
                'courtId': self.config.court_id
            }
            
            async with self.session.post(search_url, data=search_data) as response:
                search_results = await response.text()
                
                # Parse search results
                hearings = await self._parse_pacer_hearings(search_results)
                
            logger.info(f"Fetched {len(hearings)} hearings from PACER")
            
        except Exception as e:
            logger.error(f"Failed to fetch PACER hearings: {str(e)}")
        
        return hearings
    
    async def _parse_pacer_hearings(self, html_content: str) -> List[HearingEvent]:
        """Parse PACER hearing search results."""
        hearings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for hearing entries in the results table
        hearing_rows = soup.find_all('tr', class_=['odd', 'even'])
        
        for row in hearing_rows:
            try:
                cells = row.find_all('td')
                if len(cells) >= 6:  # Expected number of columns
                    # Extract hearing information
                    case_number = cells[0].get_text(strip=True)
                    case_title = cells[1].get_text(strip=True)
                    hearing_date = cells[2].get_text(strip=True)
                    hearing_time = cells[3].get_text(strip=True)
                    courtroom = cells[4].get_text(strip=True)
                    hearing_type = cells[5].get_text(strip=True)
                    
                    # Parse date and time
                    datetime_str = f"{hearing_date} {hearing_time}"
                    parsed_datetime = parser.parse(datetime_str)
                    
                    # Create hearing event
                    hearing = HearingEvent(
                        hearing_id=f"pacer_{hash(f'{case_number}_{parsed_datetime}')}",
                        case_number=case_number,
                        case_title=case_title,
                        hearing_type=self._classify_hearing_type(hearing_type),
                        date_time=parsed_datetime,
                        end_time=parsed_datetime + timedelta(hours=1),
                        location=Location(
                            court_name=self.config.metadata.get('court_name', 'Federal Court'),
                            courtroom=courtroom
                        ),
                        status=HearingStatus.SCHEDULED,
                        confidence=0.95,  # High confidence for official court data
                        source="pacer",
                        source_document_id=case_number
                    )
                    
                    hearings.append(hearing)
            
            except Exception as e:
                logger.warning(f"Failed to parse PACER hearing row: {str(e)}")
                continue
        
        return hearings
    
    def _classify_hearing_type(self, hearing_type_str: str) -> HearingType:
        """Classify hearing type from PACER description."""
        hearing_type_lower = hearing_type_str.lower()
        
        if 'motion' in hearing_type_lower:
            return HearingType.MOTION_HEARING
        elif 'trial' in hearing_type_lower:
            return HearingType.TRIAL
        elif 'status' in hearing_type_lower:
            return HearingType.STATUS_CONFERENCE
        elif 'settlement' in hearing_type_lower:
            return HearingType.SETTLEMENT_CONFERENCE
        elif 'pretrial' in hearing_type_lower or 'pre-trial' in hearing_type_lower:
            return HearingType.PRETRIAL_CONFERENCE
        elif 'arraignment' in hearing_type_lower:
            return HearingType.ARRAIGNMENT
        elif 'sentencing' in hearing_type_lower:
            return HearingType.SENTENCING
        elif 'oral argument' in hearing_type_lower:
            return HearingType.ORAL_ARGUMENT
        else:
            return HearingType.HEARING
    
    async def get_case_information(self, case_number: str) -> Optional[Dict[str, Any]]:
        """Get detailed case information from PACER."""
        if not self.authenticated:
            if not await self.authenticate():
                return None
        
        try:
            # Navigate to case details page
            case_url = f"{self.base_url}/pcl/pages/case.jsf?caseNumber={case_number}"
            
            async with self.session.get(case_url) as response:
                case_page = await response.text()
                
                # Parse case information
                soup = BeautifulSoup(case_page, 'html.parser')
                
                case_info = {
                    'case_number': case_number,
                    'case_title': self._extract_case_title(soup),
                    'judge': self._extract_judge(soup),
                    'filed_date': self._extract_filed_date(soup),
                    'case_type': self._extract_case_type(soup),
                    'parties': self._extract_parties(soup),
                    'attorneys': self._extract_attorneys(soup),
                    'status': self._extract_case_status(soup)
                }
                
                return case_info
        
        except Exception as e:
            logger.error(f"Failed to get PACER case information for {case_number}: {str(e)}")
            return None
    
    def _extract_case_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract case title from PACER case page."""
        title_elem = soup.find('span', class_='caseTitle')
        return title_elem.get_text(strip=True) if title_elem else None
    
    def _extract_judge(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract judge name from PACER case page."""
        judge_elem = soup.find('span', class_='assignedJudge')
        if judge_elem:
            judge_text = judge_elem.get_text(strip=True)
            # Clean up judge name
            judge_text = re.sub(r'^(Hon\.|Judge)\s+', '', judge_text, flags=re.IGNORECASE)
            return judge_text
        return None
    
    def _extract_filed_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract filed date from PACER case page."""
        date_elem = soup.find('span', class_='filedDate')
        if date_elem:
            try:
                return parser.parse(date_elem.get_text(strip=True))
            except (ValueError, parser.ParserError):
                pass
        return None
    
    def _extract_case_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract case type from PACER case page."""
        type_elem = soup.find('span', class_='caseType')
        return type_elem.get_text(strip=True) if type_elem else None
    
    def _extract_parties(self, soup: BeautifulSoup) -> List[str]:
        """Extract party names from PACER case page."""
        parties = []
        party_section = soup.find('div', class_='parties')
        if party_section:
            party_elems = party_section.find_all('span', class_='partyName')
            parties = [elem.get_text(strip=True) for elem in party_elems]
        return parties
    
    def _extract_attorneys(self, soup: BeautifulSoup) -> List[str]:
        """Extract attorney names from PACER case page."""
        attorneys = []
        attorney_section = soup.find('div', class_='attorneys')
        if attorney_section:
            attorney_elems = attorney_section.find_all('span', class_='attorneyName')
            attorneys = [elem.get_text(strip=True) for elem in attorney_elems]
        return attorneys
    
    def _extract_case_status(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract case status from PACER case page."""
        status_elem = soup.find('span', class_='caseStatus')
        return status_elem.get_text(strip=True) if status_elem else None
    
    async def check_for_updates(self, since: datetime) -> List[HearingUpdate]:
        """Check for hearing updates since the given timestamp."""
        updates = []
        
        # PACER doesn't have a direct update API, so we fetch recent hearings
        # and compare with stored data to detect changes
        end_date = datetime.now() + timedelta(days=90)
        recent_hearings = await self.fetch_hearings(since, end_date)
        
        # This would typically compare with stored hearing data
        # and identify new, modified, or cancelled hearings
        for hearing in recent_hearings:
            update = HearingUpdate(
                hearing_id=hearing.hearing_id,
                update_type="detected",  # Would be more specific in real implementation
                court_id=self.config.court_id,
                source=DataSource.PACER,
                timestamp=datetime.now(),
                new_data=hearing.to_dict()
            )
            updates.append(update)
        
        return updates


class ECFProvider(CourtDataProvider):
    """Electronic Case Filing (ECF) provider."""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.ecf_url = config.url or "https://ecf.uscourts.gov"
        self.authenticated = False
        
        # Set up Selenium WebDriver for ECF (often requires JavaScript)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = None
    
    async def authenticate(self) -> bool:
        """Authenticate with ECF system."""
        if not self.config.credentials:
            logger.error("ECF credentials not provided")
            return False
        
        try:
            # Initialize WebDriver
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to ECF login page
            login_url = f"{self.ecf_url}/cgi-bin/login.pl"
            self.driver.get(login_url)
            
            # Fill in credentials
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            password_field = self.driver.find_element(By.NAME, "key")
            
            username_field.send_keys(self.config.credentials['username'])
            password_field.send_keys(self.config.credentials['password'])
            
            # Submit login form
            login_button = self.driver.find_element(By.NAME, "login_button")
            login_button.click()
            
            # Wait for redirect and check for successful login
            WebDriverWait(self.driver, 10).until(
                lambda driver: "login.pl" not in driver.current_url
            )
            
            # Check for login success indicators
            page_source = self.driver.page_source
            if "Menu" in page_source and "Utilities" in page_source:
                self.authenticated = True
                logger.info("ECF authentication successful")
                return True
            else:
                logger.error("ECF authentication failed")
                return False
        
        except Exception as e:
            logger.error(f"ECF authentication error: {str(e)}")
            return False
    
    async def fetch_hearings(self, start_date: datetime, end_date: datetime) -> List[HearingEvent]:
        """Fetch hearings from ECF system."""
        if not self.authenticated:
            if not await self.authenticate():
                return []
        
        hearings = []
        
        try:
            # Navigate to calendar/hearing search
            calendar_url = f"{self.ecf_url}/cgi-bin/calendar.pl"
            self.driver.get(calendar_url)
            
            # Set date range
            start_date_field = self.driver.find_element(By.NAME, "date_from")
            end_date_field = self.driver.find_element(By.NAME, "date_to")
            
            start_date_field.clear()
            start_date_field.send_keys(start_date.strftime('%m/%d/%Y'))
            
            end_date_field.clear()
            end_date_field.send_keys(end_date.strftime('%m/%d/%Y'))
            
            # Submit search
            search_button = self.driver.find_element(By.NAME, "search")
            search_button.click()
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Parse results
            hearings = await self._parse_ecf_calendar(self.driver.page_source)
            
            logger.info(f"Fetched {len(hearings)} hearings from ECF")
            
        except Exception as e:
            logger.error(f"Failed to fetch ECF hearings: {str(e)}")
        
        return hearings
    
    async def _parse_ecf_calendar(self, html_content: str) -> List[HearingEvent]:
        """Parse ECF calendar results."""
        hearings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for calendar entries
        calendar_table = soup.find('table')
        if calendar_table:
            rows = calendar_table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        # Extract hearing details
                        date_time_str = cells[0].get_text(strip=True)
                        case_number = cells[1].get_text(strip=True)
                        case_title = cells[2].get_text(strip=True)
                        hearing_type = cells[3].get_text(strip=True)
                        judge = cells[4].get_text(strip=True)
                        
                        # Parse datetime
                        parsed_datetime = parser.parse(date_time_str)
                        
                        # Create hearing event
                        hearing = HearingEvent(
                            hearing_id=f"ecf_{hash(f'{case_number}_{parsed_datetime}')}",
                            case_number=case_number,
                            case_title=case_title,
                            hearing_type=self._classify_hearing_type(hearing_type),
                            date_time=parsed_datetime,
                            end_time=parsed_datetime + timedelta(hours=1),
                            judge=judge if judge != "TBD" else None,
                            location=Location(
                                court_name=self.config.metadata.get('court_name', 'Federal Court')
                            ),
                            status=HearingStatus.SCHEDULED,
                            confidence=0.95,
                            source="ecf",
                            source_document_id=case_number
                        )
                        
                        hearings.append(hearing)
                
                except Exception as e:
                    logger.warning(f"Failed to parse ECF calendar row: {str(e)}")
                    continue
        
        return hearings
    
    def _classify_hearing_type(self, hearing_type_str: str) -> HearingType:
        """Classify hearing type from ECF description."""
        # Similar to PACER classification but with ECF-specific terms
        hearing_type_lower = hearing_type_str.lower()
        
        if 'motion' in hearing_type_lower:
            return HearingType.MOTION_HEARING
        elif 'trial' in hearing_type_lower:
            return HearingType.TRIAL
        elif 'status' in hearing_type_lower or 'case management' in hearing_type_lower:
            return HearingType.STATUS_CONFERENCE
        elif 'settlement' in hearing_type_lower:
            return HearingType.SETTLEMENT_CONFERENCE
        elif 'pretrial' in hearing_type_lower:
            return HearingType.PRETRIAL_CONFERENCE
        elif 'scheduling' in hearing_type_lower:
            return HearingType.SCHEDULING_CONFERENCE
        else:
            return HearingType.HEARING
    
    async def get_case_information(self, case_number: str) -> Optional[Dict[str, Any]]:
        """Get case information from ECF."""
        if not self.authenticated:
            if not await self.authenticate():
                return None
        
        try:
            # Navigate to case query page
            query_url = f"{self.ecf_url}/cgi-bin/qry_by_case.pl"
            self.driver.get(query_url)
            
            # Enter case number
            case_field = self.driver.find_element(By.NAME, "case_num")
            case_field.send_keys(case_number)
            
            # Submit query
            submit_button = self.driver.find_element(By.NAME, "submit")
            submit_button.click()
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Parse case information
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            case_info = {
                'case_number': case_number,
                'case_title': self._extract_case_title_ecf(soup),
                'judge': self._extract_judge_ecf(soup),
                'filed_date': self._extract_filed_date_ecf(soup),
                'case_type': self._extract_case_type_ecf(soup),
                'parties': self._extract_parties_ecf(soup),
                'status': self._extract_case_status_ecf(soup)
            }
            
            return case_info
        
        except Exception as e:
            logger.error(f"Failed to get ECF case information for {case_number}: {str(e)}")
            return None
    
    def _extract_case_title_ecf(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract case title from ECF case page."""
        # ECF has different HTML structure than PACER
        title_elem = soup.find('b')  # Case title is often the first bold element
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove case number prefix if present
            title_text = re.sub(r'^\d+[-:]\d+[-:]?\w*\s+', '', title_text)
            return title_text
        return None
    
    def _extract_judge_ecf(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract judge from ECF case page."""
        # Look for text containing "Judge"
        judge_pattern = re.compile(r'Judge:\s*([^<\n]+)', re.IGNORECASE)
        match = judge_pattern.search(str(soup))
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_filed_date_ecf(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract filed date from ECF case page."""
        # Look for date patterns
        date_pattern = re.compile(r'Filed:\s*(\d{2}/\d{2}/\d{4})')
        match = date_pattern.search(str(soup))
        if match:
            try:
                return parser.parse(match.group(1))
            except (ValueError, parser.ParserError):
                pass
        return None
    
    def _extract_case_type_ecf(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract case type from ECF case page."""
        # Case type is often in a specific table cell
        type_pattern = re.compile(r'Nature of Suit:\s*([^<\n]+)', re.IGNORECASE)
        match = type_pattern.search(str(soup))
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_parties_ecf(self, soup: BeautifulSoup) -> List[str]:
        """Extract parties from ECF case page."""
        parties = []
        # Look for party information in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                if 'plaintiff' in row.get_text().lower() or 'defendant' in row.get_text().lower():
                    cells = row.find_all('td')
                    if cells:
                        party_name = cells[-1].get_text(strip=True)
                        if party_name and party_name not in parties:
                            parties.append(party_name)
        return parties
    
    def _extract_case_status_ecf(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract case status from ECF case page."""
        status_pattern = re.compile(r'Status:\s*([^<\n]+)', re.IGNORECASE)
        match = status_pattern.search(str(soup))
        if match:
            return match.group(1).strip()
        return None
    
    async def check_for_updates(self, since: datetime) -> List[HearingUpdate]:
        """Check for updates in ECF system."""
        updates = []
        
        # ECF systems often have docket feeds or notification systems
        # This is a simplified implementation
        try:
            if self.authenticated:
                # Check for recent docket entries
                recent_url = f"{self.ecf_url}/cgi-bin/recent_entries.pl"
                self.driver.get(recent_url)
                
                # Parse recent entries for hearing-related updates
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Look for entries that mention hearings or scheduling
                entries = soup.find_all('tr')
                for entry in entries:
                    entry_text = entry.get_text().lower()
                    if any(keyword in entry_text for keyword in ['hearing', 'scheduled', 'continued', 'cancelled']):
                        # Extract update information
                        cells = entry.find_all('td')
                        if len(cells) >= 3:
                            case_number = cells[0].get_text(strip=True)
                            entry_date = cells[1].get_text(strip=True)
                            description = cells[2].get_text(strip=True)
                            
                            try:
                                entry_datetime = parser.parse(entry_date)
                                if entry_datetime >= since:
                                    update = HearingUpdate(
                                        hearing_id=f"ecf_update_{hash(description)}",
                                        update_type="docket_entry",
                                        court_id=self.config.court_id,
                                        source=DataSource.ECF,
                                        timestamp=entry_datetime,
                                        new_data={
                                            'case_number': case_number,
                                            'description': description,
                                            'entry_date': entry_date
                                        }
                                    )
                                    updates.append(update)
                            except (ValueError, parser.ParserError):
                                continue
        
        except Exception as e:
            logger.error(f"Failed to check ECF updates: {str(e)}")
        
        return updates


class StateCourtProvider(CourtDataProvider):
    """Provider for state court systems."""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.state_code = config.metadata.get('state_code', 'CA')
        self.authenticated = False
    
    async def authenticate(self) -> bool:
        """Authenticate with state court system."""
        # State systems vary widely - this is a generic implementation
        self.session = aiohttp.ClientSession()
        self.authenticated = True
        return True
    
    async def fetch_hearings(self, start_date: datetime, end_date: datetime) -> List[HearingEvent]:
        """Fetch hearings from state court system."""
        hearings = []
        
        try:
            # Many state courts have public calendar feeds
            if self.config.url:
                async with self.session.get(
                    self.config.url,
                    params={
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d')
                    }
                ) as response:
                    data = await response.json()
                    hearings = await self._parse_state_calendar_data(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch state court hearings: {str(e)}")
        
        return hearings
    
    async def _parse_state_calendar_data(self, data: Any) -> List[HearingEvent]:
        """Parse state court calendar data."""
        hearings = []
        
        # Handle different data formats (JSON, XML, etc.)
        if isinstance(data, list):
            for item in data:
                try:
                    hearing = HearingEvent(
                        hearing_id=f"state_{item.get('id', hash(str(item)))}",
                        case_number=item.get('case_number', 'UNKNOWN'),
                        case_title=item.get('case_title', 'Unknown Case'),
                        hearing_type=self._map_state_hearing_type(item.get('hearing_type')),
                        date_time=parser.parse(item.get('date_time')),
                        end_time=parser.parse(item.get('end_time')) if item.get('end_time') else None,
                        judge=item.get('judge'),
                        location=Location(
                            court_name=item.get('court_name', f"{self.state_code} State Court"),
                            courtroom=item.get('courtroom'),
                            address=item.get('address')
                        ),
                        status=HearingStatus.SCHEDULED,
                        confidence=0.9,
                        source="state_court",
                        source_document_id=item.get('case_number')
                    )
                    hearings.append(hearing)
                
                except Exception as e:
                    logger.warning(f"Failed to parse state court hearing: {str(e)}")
                    continue
        
        return hearings
    
    def _map_state_hearing_type(self, hearing_type: Optional[str]) -> HearingType:
        """Map state court hearing type to standard type."""
        if not hearing_type:
            return HearingType.HEARING
        
        hearing_type_lower = hearing_type.lower()
        
        if 'trial' in hearing_type_lower:
            return HearingType.TRIAL
        elif 'motion' in hearing_type_lower:
            return HearingType.MOTION_HEARING
        elif 'status' in hearing_type_lower:
            return HearingType.STATUS_CONFERENCE
        elif 'settlement' in hearing_type_lower:
            return HearingType.SETTLEMENT_CONFERENCE
        elif 'family' in hearing_type_lower:
            return HearingType.HEARING
        else:
            return HearingType.HEARING
    
    async def get_case_information(self, case_number: str) -> Optional[Dict[str, Any]]:
        """Get case information from state court system."""
        # Implementation varies by state
        return None
    
    async def check_for_updates(self, since: datetime) -> List[HearingUpdate]:
        """Check for updates in state court system."""
        # Implementation varies by state
        return []


class CourtDataIntegrationManager:
    """Manages integration with multiple court data sources."""
    
    def __init__(self, hearing_detector: HearingDetector):
        self.hearing_detector = hearing_detector
        self.providers: Dict[str, CourtDataProvider] = {}
        self.courts: Dict[str, CourtInfo] = {}
        self.active_sources: Set[str] = set()
        self.update_scheduler = None
        
    def register_court(self, court: CourtInfo):
        """Register a court for data integration."""
        self.courts[court.court_id] = court
        logger.info(f"Registered court: {court.full_name()}")
    
    def register_provider(self, provider_id: str, provider: CourtDataProvider):
        """Register a court data provider."""
        self.providers[provider_id] = provider
        logger.info(f"Registered provider: {provider_id}")
    
    async def initialize_providers(self) -> Dict[str, bool]:
        """Initialize and authenticate all providers."""
        auth_results = {}
        
        for provider_id, provider in self.providers.items():
            try:
                success = await provider.authenticate()
                auth_results[provider_id] = success
                
                if success:
                    self.active_sources.add(provider_id)
                    logger.info(f"Provider {provider_id} initialized successfully")
                else:
                    logger.warning(f"Provider {provider_id} initialization failed")
            
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_id}: {str(e)}")
                auth_results[provider_id] = False
        
        return auth_results
    
    async def fetch_all_hearings(self, start_date: datetime, end_date: datetime) -> Dict[str, List[HearingEvent]]:
        """Fetch hearings from all active providers."""
        results = {}
        
        # Fetch from all providers in parallel
        fetch_tasks = []
        for provider_id in self.active_sources:
            provider = self.providers[provider_id]
            task = asyncio.create_task(provider.fetch_hearings(start_date, end_date))
            fetch_tasks.append((provider_id, task))
        
        # Collect results
        for provider_id, task in fetch_tasks:
            try:
                hearings = await task
                results[provider_id] = hearings
                logger.info(f"Fetched {len(hearings)} hearings from {provider_id}")
            except Exception as e:
                logger.error(f"Failed to fetch hearings from {provider_id}: {str(e)}")
                results[provider_id] = []
        
        return results
    
    async def detect_hearings_from_sources(self, start_date: datetime, end_date: datetime) -> List[HearingEvent]:
        """Fetch court data and detect additional hearings."""
        all_hearings = []
        
        # Fetch from all sources
        source_results = await self.fetch_all_hearings(start_date, end_date)
        
        # Process results through hearing detector for additional validation/enhancement
        for source, hearings in source_results.items():
            for hearing in hearings:
                # Use hearing detector to validate and potentially enhance the hearing data
                if hearing.raw_text:
                    detected_hearings = await self.hearing_detector.detect_hearings(
                        text=hearing.raw_text,
                        source=source,
                        case_number=hearing.case_number,
                        case_title=hearing.case_title
                    )
                    
                    # Merge with original hearing data
                    if detected_hearings:
                        enhanced_hearing = detected_hearings[0]
                        # Keep original data but add enhancements
                        enhanced_hearing.hearing_id = hearing.hearing_id
                        enhanced_hearing.confidence = max(hearing.confidence, enhanced_hearing.confidence)
                        all_hearings.append(enhanced_hearing)
                    else:
                        all_hearings.append(hearing)
                else:
                    all_hearings.append(hearing)
        
        # Remove duplicates based on case number and date
        unique_hearings = self._deduplicate_hearings(all_hearings)
        
        logger.info(f"Detected {len(unique_hearings)} unique hearings from all sources")
        return unique_hearings
    
    def _deduplicate_hearings(self, hearings: List[HearingEvent]) -> List[HearingEvent]:
        """Remove duplicate hearings based on case number and datetime."""
        seen = set()
        unique_hearings = []
        
        for hearing in hearings:
            # Create a key based on case number and datetime
            key = (hearing.case_number, hearing.date_time.replace(second=0, microsecond=0))
            
            if key not in seen:
                seen.add(key)
                unique_hearings.append(hearing)
            else:
                # If duplicate, keep the one with higher confidence
                existing_index = next(
                    (i for i, h in enumerate(unique_hearings) 
                     if (h.case_number, h.date_time.replace(second=0, microsecond=0)) == key),
                    None
                )
                
                if existing_index is not None and hearing.confidence > unique_hearings[existing_index].confidence:
                    unique_hearings[existing_index] = hearing
        
        return unique_hearings
    
    async def check_all_updates(self, since: datetime) -> Dict[str, List[HearingUpdate]]:
        """Check for updates from all active sources."""
        results = {}
        
        update_tasks = []
        for provider_id in self.active_sources:
            provider = self.providers[provider_id]
            task = asyncio.create_task(provider.check_for_updates(since))
            update_tasks.append((provider_id, task))
        
        for provider_id, task in update_tasks:
            try:
                updates = await task
                results[provider_id] = updates
                logger.info(f"Found {len(updates)} updates from {provider_id}")
            except Exception as e:
                logger.error(f"Failed to check updates from {provider_id}: {str(e)}")
                results[provider_id] = []
        
        return results
    
    def get_court_info(self, court_id: str) -> Optional[CourtInfo]:
        """Get information about a specific court."""
        return self.courts.get(court_id)
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        status = {}
        
        for provider_id, provider in self.providers.items():
            status[provider_id] = {
                'active': provider_id in self.active_sources,
                'authenticated': getattr(provider, 'authenticated', False),
                'last_update': provider.config.last_update.isoformat() if provider.config.last_update else None,
                'court_id': provider.config.court_id,
                'source_type': provider.config.source_type.value
            }
        
        return status
    
    async def cleanup(self):
        """Clean up all providers and resources."""
        cleanup_tasks = []
        
        for provider in self.providers.values():
            cleanup_tasks.append(asyncio.create_task(provider.cleanup()))
        
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        logger.info("Court data integration cleanup completed")


# Example usage
async def example_usage():
    """Example usage of court data integration."""
    
    # Initialize hearing detector
    hearing_detector = HearingDetector()
    
    # Create integration manager
    integration_manager = CourtDataIntegrationManager(hearing_detector)
    
    # Register courts
    federal_court = CourtInfo(
        court_id="cacd",
        name="US District Court for the Central District of California",
        system_type=CourtSystem.FEDERAL_DISTRICT,
        jurisdiction="California Central",
        website="https://www.cacd.uscourts.gov",
        timezone="America/Los_Angeles"
    )
    
    integration_manager.register_court(federal_court)
    
    # Register providers
    pacer_config = DataSourceConfig(
        source_id="pacer_cacd",
        court_id="cacd",
        source_type=DataSource.PACER,
        url="https://pcl.uscourts.gov",
        credentials={
            'username': 'your_pacer_username',
            'password': 'your_pacer_password',
            'client_code': 'your_client_code'
        },
        update_frequency=UpdateFrequency.HOURLY,
        metadata={'court_name': 'US District Court CACD'}
    )
    
    pacer_provider = PACERProvider(pacer_config)
    integration_manager.register_provider("pacer_cacd", pacer_provider)
    
    # Initialize providers
    auth_results = await integration_manager.initialize_providers()
    print(f"Provider authentication results: {auth_results}")
    
    # Fetch hearings
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days=30)
    
    hearings = await integration_manager.detect_hearings_from_sources(start_date, end_date)
    print(f"Detected {len(hearings)} hearings")
    
    for hearing in hearings[:5]:  # Show first 5
        print(f"- {hearing.case_title} on {hearing.date_time} ({hearing.source})")
    
    # Check for updates
    updates = await integration_manager.check_all_updates(datetime.now() - timedelta(hours=24))
    print(f"Found updates: {sum(len(u) for u in updates.values())}")
    
    # Get provider status
    status = integration_manager.get_provider_status()
    print(f"Provider status: {status}")
    
    # Cleanup
    await integration_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(example_usage())