"""
Fallback Methods for Court Data Access

Implements alternative data collection methods when direct API access
is unavailable, including screen scraping, manual entry, email parsing,
PDF extraction, and phone verification.
"""

import asyncio
import logging
import re
import email
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ...core.config import settings
from .federal_courts import CourtCase, CourtDocument
from .state_courts import StateCourtCase

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - web scraping disabled")

try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PDF processing libraries not available")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not available - HTML parsing limited")

class FallbackMethod(Enum):
    """Available fallback methods"""
    SCREEN_SCRAPING = "screen_scraping"
    MANUAL_DATA_ENTRY = "manual_data_entry"
    EMAIL_PARSING = "email_parsing"
    PDF_EXTRACTION = "pdf_extraction"
    PHONE_VERIFICATION = "phone_verification"

class DataSource(Enum):
    """Data source types"""
    COURT_WEBSITE = "court_website"
    EMAIL_NOTIFICATION = "email_notification"
    PDF_DOCUMENT = "pdf_document"
    MANUAL_INPUT = "manual_input"
    PHONE_CALL = "phone_call"

@dataclass
class ScrapingTarget:
    """Web scraping target configuration"""
    url: str
    selectors: Dict[str, str]
    authentication: Optional[Dict[str, str]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    rate_limit: float = 1.0  # seconds between requests
    retry_count: int = 3

@dataclass
class FallbackResult:
    """Result from fallback data collection"""
    method: FallbackMethod
    source: DataSource
    data: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    verification_needed: bool = False
    errors: List[str] = field(default_factory=list)

class CourtScrapingEngine:
    """
    Web scraping engine for court websites with permission-based access
    """

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.scraping_targets: Dict[str, ScrapingTarget] = {}
        self.permissions: Dict[str, bool] = {}
        self._initialize_targets()

    def _initialize_targets(self):
        """Initialize known court website scraping targets"""
        self.scraping_targets = {
            'ca_superior_la': ScrapingTarget(
                url="https://www.lacourt.org/casesummary/ui/",
                selectors={
                    'case_number': 'input[name="caseNumber"]',
                    'search_button': 'input[type="submit"]',
                    'case_title': '.case-title',
                    'parties': '.party-info',
                    'status': '.case-status'
                },
                rate_limit=2.0
            ),
            'ny_supreme_nyc': ScrapingTarget(
                url="https://iapps.courts.state.ny.us/nyscef/",
                selectors={
                    'index_number': 'input[name="indexNumber"]',
                    'search_btn': '#searchBtn',
                    'case_info': '.case-information',
                    'docket': '.docket-entries'
                },
                rate_limit=1.5
            )
        }

    async def check_scraping_permission(self, court_identifier: str) -> bool:
        """Check if scraping is permitted for a court website"""
        try:
            if court_identifier in self.permissions:
                return self.permissions[court_identifier]

            target = self.scraping_targets.get(court_identifier)
            if not target:
                return False

            # Check robots.txt and terms of service
            permission_granted = await self._verify_scraping_permission(target.url)
            self.permissions[court_identifier] = permission_granted

            return permission_granted

        except Exception as e:
            logger.error(f"Error checking scraping permission: {str(e)}")
            return False

    async def _verify_scraping_permission(self, url: str) -> bool:
        """Verify scraping permission through robots.txt and ToS"""
        try:
            # In real implementation, would check robots.txt and terms of service
            # For now, return conservative False to require explicit permission
            logger.info(f"Scraping permission check for {url} - requiring explicit permission")
            return False  # Conservative approach - require explicit permission
        except Exception as e:
            logger.error(f"Error verifying scraping permission: {str(e)}")
            return False

    async def scrape_case_data(self, court_identifier: str, case_number: str) -> Optional[FallbackResult]:
        """Scrape case data from court website"""
        try:
            if not SELENIUM_AVAILABLE:
                return FallbackResult(
                    method=FallbackMethod.SCREEN_SCRAPING,
                    source=DataSource.COURT_WEBSITE,
                    data={},
                    confidence=0.0,
                    errors=["Selenium not available"]
                )

            if not await self.check_scraping_permission(court_identifier):
                return FallbackResult(
                    method=FallbackMethod.SCREEN_SCRAPING,
                    source=DataSource.COURT_WEBSITE,
                    data={},
                    confidence=0.0,
                    errors=["Scraping not permitted for this court"]
                )

            target = self.scraping_targets.get(court_identifier)
            if not target:
                return FallbackResult(
                    method=FallbackMethod.SCREEN_SCRAPING,
                    source=DataSource.COURT_WEBSITE,
                    data={},
                    confidence=0.0,
                    errors=["Court not configured for scraping"]
                )

            # Initialize browser if needed
            if not self.driver:
                await self._initialize_browser()

            # Perform scraping
            scraped_data = await self._scrape_with_selenium(target, case_number)

            return FallbackResult(
                method=FallbackMethod.SCREEN_SCRAPING,
                source=DataSource.COURT_WEBSITE,
                data=scraped_data,
                confidence=0.7 if scraped_data else 0.0,
                verification_needed=True
            )

        except Exception as e:
            logger.error(f"Error scraping case data: {str(e)}")
            return FallbackResult(
                method=FallbackMethod.SCREEN_SCRAPING,
                source=DataSource.COURT_WEBSITE,
                data={},
                confidence=0.0,
                errors=[str(e)]
            )

    async def _initialize_browser(self):
        """Initialize Selenium browser"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--user-agent=LegalAI-Bot/1.0 (Educational Use)')

            self.driver = webdriver.Chrome(options=options)

        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            self.driver = None

    async def _scrape_with_selenium(self, target: ScrapingTarget, case_number: str) -> Dict[str, Any]:
        """Perform actual scraping with Selenium"""
        try:
            if not self.driver:
                return {}

            # Navigate to court website
            self.driver.get(target.url)

            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)

            # Enter case number
            case_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, target.selectors['case_number']))
            )
            case_input.clear()
            case_input.send_keys(case_number)

            # Click search button
            search_btn = self.driver.find_element(By.CSS_SELECTOR, target.selectors['search_button'])
            search_btn.click()

            # Wait for results and extract data
            await asyncio.sleep(2)  # Wait for results

            scraped_data = {}
            for field, selector in target.selectors.items():
                if field in ['case_number', 'search_button']:
                    continue

                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    scraped_data[field] = element.text
                except Exception:
                    scraped_data[field] = None

            return scraped_data

        except Exception as e:
            logger.error(f"Error in Selenium scraping: {str(e)}")
            return {}

    async def close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

class ManualDataEntry:
    """
    Manual data entry interface for court information
    """

    def __init__(self):
        self.pending_entries: List[Dict[str, Any]] = []
        self.completed_entries: Dict[str, Dict[str, Any]] = {}

    async def request_manual_entry(self, case_number: str,
                                 court_identifier: str,
                                 required_fields: List[str],
                                 deadline: Optional[datetime] = None) -> str:
        """Request manual data entry for a case"""
        try:
            entry_id = f"ME_{datetime.now().timestamp()}"

            entry_request = {
                'entry_id': entry_id,
                'case_number': case_number,
                'court_identifier': court_identifier,
                'required_fields': required_fields,
                'requested_at': datetime.now(),
                'deadline': deadline or (datetime.now() + timedelta(days=1)),
                'status': 'pending',
                'assigned_to': None
            }

            self.pending_entries.append(entry_request)

            # In real implementation, would notify data entry personnel
            logger.info(f"Manual entry requested for case {case_number}")

            return entry_id

        except Exception as e:
            logger.error(f"Error requesting manual entry: {str(e)}")
            raise

    async def submit_manual_entry(self, entry_id: str, data: Dict[str, Any],
                                entered_by: str) -> FallbackResult:
        """Submit manually entered data"""
        try:
            entry_data = {
                'entry_id': entry_id,
                'data': data,
                'entered_by': entered_by,
                'entered_at': datetime.now(),
                'verified': False
            }

            self.completed_entries[entry_id] = entry_data

            # Remove from pending
            self.pending_entries = [
                entry for entry in self.pending_entries
                if entry['entry_id'] != entry_id
            ]

            return FallbackResult(
                method=FallbackMethod.MANUAL_DATA_ENTRY,
                source=DataSource.MANUAL_INPUT,
                data=data,
                confidence=0.8,  # Human entry generally reliable
                verification_needed=True
            )

        except Exception as e:
            logger.error(f"Error submitting manual entry: {str(e)}")
            raise

    def get_pending_entries(self) -> List[Dict[str, Any]]:
        """Get list of pending manual entries"""
        return self.pending_entries.copy()

class EmailParser:
    """
    Email parsing for court notifications and updates
    """

    def __init__(self):
        self.email_patterns = self._initialize_email_patterns()

    def _initialize_email_patterns(self) -> Dict[str, List[str]]:
        """Initialize email parsing patterns for different courts"""
        return {
            'case_number': [
                r'Case\s+No\.?\s*:?\s*([A-Z0-9\-:]+)',
                r'Index\s+No\.?\s*:?\s*([A-Z0-9\-:]+)',
                r'Docket\s+No\.?\s*:?\s*([A-Z0-9\-:]+)'
            ],
            'hearing_date': [
                r'Hearing\s+Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
                r'Court\s+Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
                r'Scheduled\s+for\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
            ],
            'judge': [
                r'Judge\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'Hon\.?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'Before\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
            ]
        }

    async def parse_court_email(self, email_content: str,
                              sender: str = '') -> FallbackResult:
        """Parse court-related email for case information"""
        try:
            extracted_data = {}

            for field, patterns in self.email_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, email_content, re.IGNORECASE)
                    if match:
                        extracted_data[field] = match.group(1)
                        break

            confidence = len(extracted_data) / len(self.email_patterns)

            return FallbackResult(
                method=FallbackMethod.EMAIL_PARSING,
                source=DataSource.EMAIL_NOTIFICATION,
                data=extracted_data,
                confidence=confidence,
                verification_needed=True
            )

        except Exception as e:
            logger.error(f"Error parsing court email: {str(e)}")
            return FallbackResult(
                method=FallbackMethod.EMAIL_PARSING,
                source=DataSource.EMAIL_NOTIFICATION,
                data={},
                confidence=0.0,
                errors=[str(e)]
            )

class PDFExtractor:
    """
    PDF document extraction for court documents
    """

    def __init__(self):
        self.pdf_patterns = self._initialize_pdf_patterns()

    def _initialize_pdf_patterns(self) -> Dict[str, List[str]]:
        """Initialize PDF text extraction patterns"""
        return {
            'case_number': [
                r'Case\s+No\.?\s*:?\s*([A-Z0-9\-:]+)',
                r'Civil\s+Action\s+No\.?\s*:?\s*([A-Z0-9\-:]+)'
            ],
            'parties': [
                r'Plaintiff\s*:?\s*([^\n]+)',
                r'Defendant\s*:?\s*([^\n]+)'
            ],
            'filing_date': [
                r'Filed\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
                r'Date\s+Filed\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
            ]
        }

    async def extract_from_pdf(self, pdf_path: Union[str, Path]) -> FallbackResult:
        """Extract court information from PDF document"""
        try:
            if not PDF_AVAILABLE:
                return FallbackResult(
                    method=FallbackMethod.PDF_EXTRACTION,
                    source=DataSource.PDF_DOCUMENT,
                    data={},
                    confidence=0.0,
                    errors=["PDF processing libraries not available"]
                )

            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return FallbackResult(
                    method=FallbackMethod.PDF_EXTRACTION,
                    source=DataSource.PDF_DOCUMENT,
                    data={},
                    confidence=0.0,
                    errors=["PDF file not found"]
                )

            # Extract text from PDF
            text_content = await self._extract_pdf_text(pdf_path)

            # Parse extracted text
            extracted_data = {}
            for field, patterns in self.pdf_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                    if match:
                        extracted_data[field] = match.group(1).strip()
                        break

            confidence = len(extracted_data) / len(self.pdf_patterns)

            return FallbackResult(
                method=FallbackMethod.PDF_EXTRACTION,
                source=DataSource.PDF_DOCUMENT,
                data=extracted_data,
                confidence=confidence,
                verification_needed=True
            )

        except Exception as e:
            logger.error(f"Error extracting from PDF: {str(e)}")
            return FallbackResult(
                method=FallbackMethod.PDF_EXTRACTION,
                source=DataSource.PDF_DOCUMENT,
                data={},
                confidence=0.0,
                errors=[str(e)]
            )

    async def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text content from PDF"""
        try:
            text_content = ""

            # Try pdfplumber first (more accurate for complex layouts)
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text_content += page.extract_text() or ""
                        text_content += "\n"
            except Exception:
                # Fallback to PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
                        text_content += "\n"

            return text_content

        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""

class PhoneVerification:
    """
    Phone verification for court information
    """

    def __init__(self):
        self.court_contacts = self._load_court_contacts()
        self.verification_log: List[Dict[str, Any]] = []

    def _load_court_contacts(self) -> Dict[str, Dict[str, str]]:
        """Load court contact information"""
        return {
            'ca_superior_la': {
                'phone': '(213) 830-0800',
                'hours': '8:00 AM - 4:30 PM PST',
                'department': 'Civil Division'
            },
            'ny_supreme_nyc': {
                'phone': '(646) 386-3730',
                'hours': '9:00 AM - 5:00 PM EST',
                'department': 'Civil Division'
            }
        }

    async def verify_case_information(self, court_identifier: str,
                                    case_number: str,
                                    information_to_verify: Dict[str, Any]) -> FallbackResult:
        """Initiate phone verification process"""
        try:
            verification_id = f"PV_{datetime.now().timestamp()}"

            verification_record = {
                'verification_id': verification_id,
                'court_identifier': court_identifier,
                'case_number': case_number,
                'information_to_verify': information_to_verify,
                'initiated_at': datetime.now(),
                'status': 'pending',
                'verified_data': {},
                'notes': []
            }

            self.verification_log.append(verification_record)

            # In real implementation, would create phone verification task
            logger.info(f"Phone verification initiated for case {case_number}")

            return FallbackResult(
                method=FallbackMethod.PHONE_VERIFICATION,
                source=DataSource.PHONE_CALL,
                data={
                    'verification_id': verification_id,
                    'status': 'pending',
                    'contact_info': self.court_contacts.get(court_identifier, {})
                },
                confidence=0.0,  # Will be updated after verification
                verification_needed=False  # This IS the verification
            )

        except Exception as e:
            logger.error(f"Error initiating phone verification: {str(e)}")
            return FallbackResult(
                method=FallbackMethod.PHONE_VERIFICATION,
                source=DataSource.PHONE_CALL,
                data={},
                confidence=0.0,
                errors=[str(e)]
            )

    async def complete_phone_verification(self, verification_id: str,
                                        verified_data: Dict[str, Any],
                                        verification_notes: str) -> bool:
        """Complete phone verification with results"""
        try:
            for record in self.verification_log:
                if record['verification_id'] == verification_id:
                    record['verified_data'] = verified_data
                    record['notes'].append(verification_notes)
                    record['status'] = 'completed'
                    record['completed_at'] = datetime.now()
                    return True

            return False

        except Exception as e:
            logger.error(f"Error completing phone verification: {str(e)}")
            return False

class FallbackManager:
    """
    Unified manager for all fallback data collection methods
    """

    def __init__(self):
        self.scraping_engine = CourtScrapingEngine()
        self.manual_entry = ManualDataEntry()
        self.email_parser = EmailParser()
        self.pdf_extractor = PDFExtractor()
        self.phone_verification = PhoneVerification()

    async def collect_case_data(self, court_identifier: str, case_number: str,
                              preferred_methods: Optional[List[FallbackMethod]] = None) -> List[FallbackResult]:
        """Collect case data using available fallback methods"""
        results = []

        methods_to_try = preferred_methods or [
            FallbackMethod.SCREEN_SCRAPING,
            FallbackMethod.MANUAL_DATA_ENTRY,
            FallbackMethod.EMAIL_PARSING,
            FallbackMethod.PDF_EXTRACTION
        ]

        for method in methods_to_try:
            try:
                if method == FallbackMethod.SCREEN_SCRAPING:
                    result = await self.scraping_engine.scrape_case_data(court_identifier, case_number)
                elif method == FallbackMethod.MANUAL_DATA_ENTRY:
                    # Request manual entry
                    entry_id = await self.manual_entry.request_manual_entry(
                        case_number, court_identifier, ['case_name', 'judge', 'status']
                    )
                    result = FallbackResult(
                        method=method,
                        source=DataSource.MANUAL_INPUT,
                        data={'entry_id': entry_id},
                        confidence=0.0,
                        verification_needed=True
                    )
                else:
                    # Skip methods that require specific input
                    continue

                if result:
                    results.append(result)

            except Exception as e:
                logger.error(f"Error with fallback method {method}: {str(e)}")
                continue

        return results

    async def get_best_result(self, results: List[FallbackResult]) -> Optional[FallbackResult]:
        """Get the best result from multiple fallback attempts"""
        if not results:
            return None

        # Sort by confidence score
        sorted_results = sorted(results, key=lambda r: r.confidence, reverse=True)
        return sorted_results[0]

    async def cleanup(self):
        """Cleanup resources"""
        await self.scraping_engine.close_browser()

    def get_available_methods(self) -> List[FallbackMethod]:
        """Get list of currently available fallback methods"""
        available = []

        if SELENIUM_AVAILABLE:
            available.append(FallbackMethod.SCREEN_SCRAPING)

        available.extend([
            FallbackMethod.MANUAL_DATA_ENTRY,
            FallbackMethod.EMAIL_PARSING,
            FallbackMethod.PHONE_VERIFICATION
        ])

        if PDF_AVAILABLE:
            available.append(FallbackMethod.PDF_EXTRACTION)

        return available