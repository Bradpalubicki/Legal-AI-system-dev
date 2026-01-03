"""
PACER HTTP Client

Low-level HTTP client for interacting with PACER's web interface and APIs.
Handles authentication, session management, form parsing, and response processing.
"""

import asyncio
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, parse_qs
import logging

import httpx
from bs4 import BeautifulSoup

from ..shared.utils.api_client import BaseAPIClient, APIResponse, APIClientError, HTTPMethod
from ..core.config import settings
from .models import PacerAccount, CourtInfo, RequestStatus


# Configure logging
logger = logging.getLogger(__name__)


class PacerError(APIClientError):
    """PACER-specific error"""
    def __init__(self, message: str, court_id: str = None, case_number: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.court_id = court_id
        self.case_number = case_number


class PacerAuthenticationError(PacerError):
    """PACER authentication error"""
    pass


class PacerRateLimitError(PacerError):
    """PACER rate limit error"""
    pass


class PacerCostLimitError(PacerError):
    """PACER cost limit exceeded error"""
    pass


@dataclass
class PacerResponse(APIResponse):
    """Enhanced API response for PACER"""
    court_id: Optional[str] = None
    case_number: Optional[str] = None
    cost_cents: int = 0
    page_count: Optional[int] = None
    document_count: int = 0
    billing_info: Optional[Dict[str, Any]] = None
    pacer_session_id: Optional[str] = None
    
    @property
    def cost_dollars(self) -> float:
        """Get cost in dollars"""
        return self.cost_cents / 100.0


class PacerSession:
    """PACER session management"""
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.csrf_token: Optional[str] = None
        self.login_cookies: Dict[str, str] = {}
        self.created_at: Optional[datetime] = None
        self.last_used_at: Optional[datetime] = None
        self.is_authenticated = False
        self.court_id: Optional[str] = None
    
    def is_valid(self, max_age_hours: int = 4) -> bool:
        """Check if session is still valid"""
        if not self.is_authenticated or not self.created_at:
            return False
        
        age = datetime.now(timezone.utc) - self.created_at
        return age < timedelta(hours=max_age_hours)
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = datetime.now(timezone.utc)


class PacerClient(BaseAPIClient):
    """PACER HTTP client with authentication and session management"""
    
    def __init__(
        self,
        account: PacerAccount,
        court_info: CourtInfo,
        timeout: float = 60.0  # PACER can be slow
    ):
        super().__init__(
            base_url=court_info.pacer_url,
            timeout=timeout,
            user_agent=f"{settings.APP_NAME}/1.0 (Legal Research)"
        )
        
        self.account = account
        self.court_info = court_info
        self.session = PacerSession()
        
        # PACER-specific settings
        self.max_retries = 2  # PACER is sensitive to rapid retries
        self.session_timeout_hours = 4
        self.cost_tracking_enabled = True
        
        # Common PACER endpoints
        self.endpoints = {
            'login': '/cgi-bin/login.pl',
            'logout': '/cgi-bin/logout.pl',
            'case_search': '/cgi-bin/iquery.pl',
            'docket_report': '/cgi-bin/DktRpt.pl',
            'document_link': '/doc1/',
            'written_opinion_report': '/cgi-bin/WrtOpRpt.pl',
            'civil_search': '/cgi-bin/CivSearch.pl',
            'criminal_search': '/cgi-bin/CrimSearch.pl',
            'bankruptcy_search': '/cgi-bin/BkrSearch.pl'
        }
    
    def get_service_name(self) -> str:
        """Get service name for logging"""
        return f"PACER-{self.court_info.court_id.upper()}"
    
    async def authenticate(self) -> bool:
        """Authenticate with PACER using account credentials"""
        
        try:
            logger.info(f"Authenticating with PACER court {self.court_info.court_id}")
            
            # Get login page to extract CSRF token and session info
            login_response = await self.get(self.endpoints['login'])
            
            if not login_response.is_success:
                raise PacerAuthenticationError(
                    f"Failed to access login page: {login_response.status_code}",
                    court_id=self.court_info.court_id
                )
            
            # Parse login form
            soup = BeautifulSoup(login_response.data, 'html.parser')
            login_form = soup.find('form')
            
            if not login_form:
                raise PacerAuthenticationError(
                    "Could not find login form on PACER page",
                    court_id=self.court_info.court_id
                )
            
            # Extract form data and CSRF token
            form_data = {}
            for input_tag in login_form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    form_data[name] = value
            
            # Add credentials
            form_data.update({
                'login': self.account.username,
                'key': self.account.password,
                'client_code': self.account.client_code
            })
            
            # Submit login form
            login_submit_response = await self.post(
                self.endpoints['login'],
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Check for successful authentication
            if self._is_authentication_successful(login_submit_response):
                self.session.is_authenticated = True
                self.session.created_at = datetime.now(timezone.utc)
                self.session.court_id = self.court_info.court_id
                self.session.login_cookies = dict(self.session.cookies) if hasattr(self.session, 'cookies') else {}
                
                # Extract session info from response
                self._extract_session_info(login_submit_response)
                
                logger.info(f"Successfully authenticated with PACER court {self.court_info.court_id}")
                return True
            
            else:
                error_msg = self._extract_error_message(login_submit_response)
                raise PacerAuthenticationError(
                    f"Authentication failed: {error_msg}",
                    court_id=self.court_info.court_id
                )
        
        except Exception as e:
            logger.error(f"PACER authentication failed: {str(e)}")
            self.session.is_authenticated = False
            
            if isinstance(e, PacerAuthenticationError):
                raise
            else:
                raise PacerAuthenticationError(
                    f"Authentication error: {str(e)}",
                    court_id=self.court_info.court_id
                )
    
    async def logout(self) -> bool:
        """Logout from PACER session"""
        
        try:
            if not self.session.is_authenticated:
                return True
            
            logout_response = await self.get(self.endpoints['logout'])
            
            self.session.is_authenticated = False
            self.session.session_id = None
            self.session.csrf_token = None
            self.session.login_cookies.clear()
            
            logger.info(f"Logged out from PACER court {self.court_info.court_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Logout error (non-critical): {str(e)}")
            # Force session cleanup even if logout request failed
            self.session.is_authenticated = False
            return True
    
    async def ensure_authenticated(self) -> bool:
        """Ensure client is authenticated, re-authenticate if needed"""
        
        if self.session.is_valid():
            self.session.update_last_used()
            return True
        
        return await self.authenticate()
    
    async def search_cases(
        self,
        search_params: Dict[str, Any],
        max_results: int = 100
    ) -> PacerResponse:
        """Search for cases in PACER"""
        
        await self.ensure_authenticated()
        
        try:
            # Determine search endpoint based on court type
            if self.court_info.court_type.value == "bankruptcy":
                search_endpoint = self.endpoints['bankruptcy_search']
            elif 'criminal' in search_params.get('case_type', '').lower():
                search_endpoint = self.endpoints['criminal_search'] 
            else:
                search_endpoint = self.endpoints['civil_search']
            
            # Get search form
            search_form_response = await self.get(search_endpoint)
            
            if not search_form_response.is_success:
                raise PacerError(
                    f"Failed to access search form: {search_form_response.status_code}",
                    court_id=self.court_info.court_id
                )
            
            # Parse search form and build form data
            form_data = self._build_search_form_data(search_form_response.data, search_params, max_results)
            
            # Submit search
            search_response = await self.post(
                search_endpoint,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Parse search results
            pacer_response = self._parse_search_response(search_response)
            pacer_response.court_id = self.court_info.court_id
            
            return pacer_response
            
        except Exception as e:
            logger.error(f"Case search failed: {str(e)}")
            if isinstance(e, PacerError):
                raise
            else:
                raise PacerError(
                    f"Search error: {str(e)}",
                    court_id=self.court_info.court_id
                )
    
    async def get_docket_report(
        self,
        case_number: str,
        include_documents: bool = True,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> PacerResponse:
        """Get docket report for a case"""
        
        await self.ensure_authenticated()
        
        try:
            logger.info(f"Fetching docket report for case {case_number}")
            
            # Get docket report form
            docket_form_response = await self.get(self.endpoints['docket_report'])
            
            if not docket_form_response.is_success:
                raise PacerError(
                    f"Failed to access docket form: {docket_form_response.status_code}",
                    court_id=self.court_info.court_id,
                    case_number=case_number
                )
            
            # Build form data for docket request
            form_data = self._build_docket_form_data(
                docket_form_response.data,
                case_number,
                include_documents,
                date_from,
                date_to
            )
            
            # Submit docket request
            docket_response = await self.post(
                self.endpoints['docket_report'],
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Parse docket report
            pacer_response = self._parse_docket_response(docket_response)
            pacer_response.court_id = self.court_info.court_id
            pacer_response.case_number = case_number
            
            return pacer_response
            
        except Exception as e:
            logger.error(f"Docket report failed for case {case_number}: {str(e)}")
            if isinstance(e, PacerError):
                raise
            else:
                raise PacerError(
                    f"Docket report error: {str(e)}",
                    court_id=self.court_info.court_id,
                    case_number=case_number
                )
    
    async def get_document(
        self,
        document_url: str,
        case_number: str
    ) -> PacerResponse:
        """Download a document from PACER"""
        
        await self.ensure_authenticated()
        
        try:
            logger.info(f"Downloading document from {document_url}")
            
            # PACER documents are usually PDFs served directly
            doc_response = await self.get(
                document_url,
                headers={'Accept': 'application/pdf,*/*'}
            )
            
            if not doc_response.is_success:
                # Check if this is a cost confirmation page
                if 'cost' in doc_response.data.lower() and 'confirm' in doc_response.data.lower():
                    return await self._handle_cost_confirmation(doc_response, document_url, case_number)
                
                raise PacerError(
                    f"Failed to download document: {doc_response.status_code}",
                    court_id=self.court_info.court_id,
                    case_number=case_number
                )
            
            # Parse document response
            pacer_response = self._parse_document_response(doc_response)
            pacer_response.court_id = self.court_info.court_id
            pacer_response.case_number = case_number
            
            return pacer_response
            
        except Exception as e:
            logger.error(f"Document download failed: {str(e)}")
            if isinstance(e, PacerError):
                raise
            else:
                raise PacerError(
                    f"Document download error: {str(e)}",
                    court_id=self.court_info.court_id,
                    case_number=case_number
                )
    
    def _is_authentication_successful(self, response: APIResponse) -> bool:
        """Check if authentication was successful"""
        
        # Check for common authentication success indicators
        if isinstance(response.data, str):
            # Look for success indicators
            success_indicators = [
                'main menu',
                'query',
                'search',
                'welcome',
                'logout'
            ]
            
            # Look for failure indicators
            failure_indicators = [
                'invalid login',
                'invalid password', 
                'login failed',
                'access denied',
                'authentication failed'
            ]
            
            data_lower = response.data.lower()
            
            if any(indicator in data_lower for indicator in failure_indicators):
                return False
            
            if any(indicator in data_lower for indicator in success_indicators):
                return True
        
        # Check HTTP status and headers
        return response.is_success
    
    def _extract_session_info(self, response: APIResponse):
        """Extract session information from login response"""
        
        try:
            # Extract session ID from cookies or HTML
            if hasattr(response, 'headers') and 'set-cookie' in response.headers:
                cookie_header = response.headers['set-cookie']
                # Parse session cookie (PACER-specific logic)
                session_match = re.search(r'JSESSIONID=([^;]+)', cookie_header)
                if session_match:
                    self.session.session_id = session_match.group(1)
            
            # Extract CSRF token from HTML if present
            if isinstance(response.data, str):
                csrf_match = re.search(r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', response.data)
                if csrf_match:
                    self.session.csrf_token = csrf_match.group(1)
            
        except Exception as e:
            logger.warning(f"Could not extract session info: {str(e)}")
    
    def _extract_error_message(self, response: APIResponse) -> str:
        """Extract error message from response"""
        
        if isinstance(response.data, str):
            # Look for common error patterns
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Check for error divs or spans
            error_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'error|alert|warning'))
            
            for element in error_elements:
                if element.get_text().strip():
                    return element.get_text().strip()
            
            # Check for specific PACER error patterns
            if 'invalid' in response.data.lower():
                return "Invalid login credentials"
            elif 'denied' in response.data.lower():
                return "Access denied"
            elif 'expired' in response.data.lower():
                return "Session expired"
        
        return f"Unknown error (HTTP {response.status_code})"
    
    def _build_search_form_data(
        self,
        form_html: str,
        search_params: Dict[str, Any],
        max_results: int
    ) -> Dict[str, str]:
        """Build form data for case search"""
        
        soup = BeautifulSoup(form_html, 'html.parser')
        search_form = soup.find('form')
        
        if not search_form:
            raise PacerError("Could not find search form")
        
        # Start with hidden form fields
        form_data = {}
        for input_tag in search_form.find_all('input', type='hidden'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                form_data[name] = value
        
        # Map search parameters to PACER form fields
        param_mapping = {
            'case_number': 'case_num',
            'party_name': 'last_name',  # or 'party_name' depending on court
            'case_title': 'case_title',
            'attorney_name': 'atty_last_name',
            'date_filed_from': 'date_from',
            'date_filed_to': 'date_to',
            'nature_of_suit': 'nos',
        }
        
        # Add search parameters
        for param_key, form_field in param_mapping.items():
            if param_key in search_params and search_params[param_key]:
                value = search_params[param_key]
                
                # Format dates for PACER
                if 'date' in param_key and isinstance(value, datetime):
                    value = value.strftime('%m/%d/%Y')
                
                form_data[form_field] = str(value)
        
        # Set result limit
        form_data['max_records'] = str(max_results)
        
        return form_data
    
    def _build_docket_form_data(
        self,
        form_html: str,
        case_number: str,
        include_documents: bool,
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> Dict[str, str]:
        """Build form data for docket report request"""
        
        soup = BeautifulSoup(form_html, 'html.parser')
        docket_form = soup.find('form')
        
        if not docket_form:
            raise PacerError("Could not find docket form")
        
        # Start with hidden form fields
        form_data = {}
        for input_tag in docket_form.find_all('input', type='hidden'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                form_data[name] = value
        
        # Add docket request parameters
        form_data.update({
            'case_num': case_number,
            'doc_links': 'on' if include_documents else '',
            'output_format': 'html'  # or 'pdf' for PDF output
        })
        
        # Add date range if specified
        if date_from:
            form_data['date_from'] = date_from.strftime('%m/%d/%Y')
        if date_to:
            form_data['date_to'] = date_to.strftime('%m/%d/%Y')
        
        return form_data
    
    def _parse_search_response(self, response: APIResponse) -> PacerResponse:
        """Parse search results from PACER response"""
        
        pacer_response = PacerResponse(
            status_code=response.status_code,
            data=[],
            headers=response.headers,
            raw_content=response.raw_content
        )
        
        if not isinstance(response.data, str):
            pacer_response.data = response.data
            return pacer_response
        
        try:
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Look for results table
            results_table = soup.find('table')
            
            if results_table:
                cases = []
                rows = results_table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:  # Minimum expected columns
                        case_data = self._parse_case_row(cells)
                        if case_data:
                            cases.append(case_data)
                
                pacer_response.data = cases
            
            # Extract cost information
            cost_info = self._extract_cost_info(response.data)
            pacer_response.cost_cents = cost_info.get('cost_cents', 0)
            pacer_response.billing_info = cost_info
            
        except Exception as e:
            logger.error(f"Failed to parse search response: {str(e)}")
            pacer_response.data = response.data
        
        return pacer_response
    
    def _parse_docket_response(self, response: APIResponse) -> PacerResponse:
        """Parse docket report from PACER response"""
        
        pacer_response = PacerResponse(
            status_code=response.status_code,
            data={},
            headers=response.headers,
            raw_content=response.raw_content
        )
        
        if not isinstance(response.data, str):
            pacer_response.data = response.data
            return pacer_response
        
        try:
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Parse docket header information
            docket_data = {
                'case_info': self._parse_case_header(soup),
                'docket_entries': self._parse_docket_entries(soup)
            }
            
            pacer_response.data = docket_data
            
            # Extract cost information
            cost_info = self._extract_cost_info(response.data)
            pacer_response.cost_cents = cost_info.get('cost_cents', 0)
            pacer_response.billing_info = cost_info
            pacer_response.document_count = len(docket_data.get('docket_entries', []))
            
        except Exception as e:
            logger.error(f"Failed to parse docket response: {str(e)}")
            pacer_response.data = response.data
        
        return pacer_response
    
    def _parse_document_response(self, response: APIResponse) -> PacerResponse:
        """Parse document download response"""
        
        pacer_response = PacerResponse(
            status_code=response.status_code,
            data=response.raw_content,
            headers=response.headers,
            raw_content=response.raw_content
        )
        
        # Estimate page count from file size (rough estimate: 50KB per page)
        if response.raw_content:
            estimated_pages = max(1, len(response.raw_content) // 50000)
            pacer_response.page_count = estimated_pages
            
            # Calculate estimated cost
            from .models import calculate_document_cost
            pacer_response.cost_cents = calculate_document_cost(estimated_pages)
        
        return pacer_response
    
    def _parse_case_row(self, cells) -> Optional[Dict[str, Any]]:
        """Parse a single case row from search results"""
        
        try:
            # This is a simplified parser - real implementation would be more robust
            case_data = {}
            
            if len(cells) > 0:
                case_data['case_number'] = cells[0].get_text().strip()
            if len(cells) > 1:
                case_data['case_title'] = cells[1].get_text().strip()
            if len(cells) > 2:
                case_data['filed_date'] = cells[2].get_text().strip()
            
            # Extract case link if present
            link = cells[0].find('a') if cells else None
            if link and link.get('href'):
                case_data['case_link'] = link.get('href')
            
            return case_data
            
        except Exception as e:
            logger.warning(f"Failed to parse case row: {str(e)}")
            return None
    
    def _parse_case_header(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse case header information from docket"""
        
        case_info = {}
        
        try:
            # Look for case title and number
            title_element = soup.find(string=re.compile(r'v\.|vs\.|versus', re.IGNORECASE))
            if title_element:
                case_info['case_title'] = title_element.strip()
            
            # Look for judge information
            judge_element = soup.find(string=re.compile(r'Judge:', re.IGNORECASE))
            if judge_element and judge_element.parent:
                case_info['judge'] = judge_element.parent.get_text().replace('Judge:', '').strip()
            
            # Extract other case details as needed
            
        except Exception as e:
            logger.warning(f"Failed to parse case header: {str(e)}")
        
        return case_info
    
    def _parse_docket_entries(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse docket entries from docket report"""
        
        entries = []
        
        try:
            # Look for docket entries table
            docket_table = soup.find('table')
            
            if docket_table:
                rows = docket_table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        entry = self._parse_docket_entry_row(cells)
                        if entry:
                            entries.append(entry)
        
        except Exception as e:
            logger.warning(f"Failed to parse docket entries: {str(e)}")
        
        return entries
    
    def _parse_docket_entry_row(self, cells) -> Optional[Dict[str, Any]]:
        """Parse a single docket entry row"""
        
        try:
            entry = {}
            
            if len(cells) > 0:
                entry['entry_number'] = cells[0].get_text().strip()
            if len(cells) > 1:
                entry['date_filed'] = cells[1].get_text().strip()
            if len(cells) > 2:
                entry['description'] = cells[2].get_text().strip()
            
            # Look for document links
            doc_links = []
            for cell in cells:
                links = cell.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href and '/doc1/' in href:
                        doc_links.append({
                            'url': href,
                            'text': link.get_text().strip()
                        })
            
            if doc_links:
                entry['document_links'] = doc_links
            
            return entry
            
        except Exception as e:
            logger.warning(f"Failed to parse docket entry: {str(e)}")
            return None
    
    def _extract_cost_info(self, html_content: str) -> Dict[str, Any]:
        """Extract billing/cost information from PACER response"""
        
        cost_info = {
            'cost_cents': 0,
            'billable_pages': 0,
            'search_cost': False
        }
        
        try:
            # Look for cost indicators in HTML
            cost_patterns = [
                r'Cost:\s*\$(\d+\.\d{2})',
                r'Billable Pages:\s*(\d+)',
                r'Search performed\s*\$(\d+\.\d{2})'
            ]
            
            for pattern in cost_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    if 'cost' in pattern.lower():
                        cost_info['cost_cents'] = int(float(match.group(1)) * 100)
                    elif 'pages' in pattern.lower():
                        cost_info['billable_pages'] = int(match.group(1))
                    elif 'search' in pattern.lower():
                        cost_info['search_cost'] = True
                        cost_info['cost_cents'] += int(float(match.group(1)) * 100)
        
        except Exception as e:
            logger.warning(f"Failed to extract cost info: {str(e)}")
        
        return cost_info
    
    async def _handle_cost_confirmation(
        self,
        response: APIResponse,
        document_url: str,
        case_number: str
    ) -> PacerResponse:
        """Handle PACER cost confirmation page"""
        
        try:
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Look for cost confirmation form
            confirm_form = soup.find('form')
            
            if not confirm_form:
                raise PacerError("Could not find cost confirmation form")
            
            # Extract estimated cost
            cost_text = soup.get_text()
            cost_match = re.search(r'\$(\d+\.\d{2})', cost_text)
            estimated_cost_cents = 0
            
            if cost_match:
                estimated_cost_cents = int(float(cost_match.group(1)) * 100)
            
            # Check against cost limits (implement cost checking logic)
            if self.cost_tracking_enabled:
                # This would check against daily/monthly limits
                pass
            
            # Build confirmation form data
            form_data = {}
            for input_tag in confirm_form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    form_data[name] = value
            
            # Submit confirmation
            confirm_response = await self.post(
                document_url,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Parse final document response
            pacer_response = self._parse_document_response(confirm_response)
            pacer_response.cost_cents = estimated_cost_cents
            
            return pacer_response
            
        except Exception as e:
            raise PacerError(
                f"Cost confirmation failed: {str(e)}",
                court_id=self.court_info.court_id,
                case_number=case_number
            )