"""
Government Database Clients

Comprehensive integration with US government legal databases including
GovInfo, Congress.gov, Supreme Court, and federal agency databases.
"""

import asyncio
import logging
import re
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from urllib.parse import quote, urlencode

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from ..database_models import (
    DatabaseProvider, UnifiedQuery, UnifiedDocument, UnifiedSearchResult,
    ContentType, DatabaseCapability, AccessType
)

logger = logging.getLogger(__name__)


class GovernmentCredentials:
    """Credentials for government API access"""
    def __init__(
        self,
        govinfo_api_key: Optional[str] = None,
        congress_api_key: Optional[str] = None
    ):
        self.govinfo_api_key = govinfo_api_key
        self.congress_api_key = congress_api_key


class GovInfoClient:
    """
    GovInfo API client for federal documents, regulations, and publications.
    Provides access to Federal Register, CFR, Congressional materials, and more.
    """
    
    def __init__(self, credentials: Optional[GovernmentCredentials] = None):
        self.credentials = credentials
        self.base_url = "https://api.govinfo.gov"
        self.session: Optional[ClientSession] = None
        
        # Rate limiting (GovInfo is generous but we should be respectful)
        self.rate_limit = 120  # requests per minute
        self.rate_limit_window = 60
        self.request_timestamps: List[datetime] = []
        
        self.capabilities = [
            DatabaseCapability.FULL_TEXT_SEARCH,
            DatabaseCapability.DATE_FILTERING,
            DatabaseCapability.DOCUMENT_TYPE_FILTERING,
            DatabaseCapability.FULL_DOCUMENT_ACCESS,
            DatabaseCapability.API_ACCESS,
            DatabaseCapability.BULK_DOWNLOAD
        ]
        
        logger.info("GovInfo client initialized")
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = ClientTimeout(total=30, connect=10)
        headers = {
            "User-Agent": "LegalAI-UnifiedSearch/1.0 (Research Tool)",
            "Accept": "application/json"
        }
        
        self.session = ClientSession(timeout=timeout, headers=headers)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search GovInfo database"""
        try:
            logger.info(f"Executing GovInfo search: {query.query_text[:100]}...")
            
            # Search different collections based on content types
            all_results = []
            
            if ContentType.REGULATIONS in query.content_types or not query.content_types:
                cfr_results = await self._search_cfr(query)
                all_results.extend(cfr_results)
                
                fed_register_results = await self._search_federal_register(query)
                all_results.extend(fed_register_results)
            
            if ContentType.CONGRESSIONAL_MATERIALS in query.content_types or not query.content_types:
                congressional_results = await self._search_congressional(query)
                all_results.extend(congressional_results)
            
            return all_results[:query.max_results]
            
        except Exception as e:
            logger.error(f"GovInfo search failed: {str(e)}")
            return []
    
    async def _search_cfr(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Code of Federal Regulations"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/collections/cfr"
            params = {
                "q": query.query_text,
                "format": "json",
                "pageSize": min(query.max_results, 100)
            }
            
            if query.date_from:
                params["publishedDate"] = f"{query.date_from.isoformat()}:"
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                return await self._parse_cfr_results(data)
                
        except Exception as e:
            logger.error(f"GovInfo CFR search error: {str(e)}")
            return []
    
    async def _search_federal_register(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Federal Register"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/collections/fr"
            params = {
                "q": query.query_text,
                "format": "json", 
                "pageSize": min(query.max_results, 100)
            }
            
            if query.date_from:
                params["publishedDate"] = f"{query.date_from.isoformat()}:"
            if query.date_to:
                params["publishedDate"] = f":{query.date_to.isoformat()}"
            if query.date_from and query.date_to:
                params["publishedDate"] = f"{query.date_from.isoformat()}:{query.date_to.isoformat()}"
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                return await self._parse_federal_register_results(data)
                
        except Exception as e:
            logger.error(f"GovInfo Federal Register search error: {str(e)}")
            return []
    
    async def _search_congressional(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Congressional materials"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/collections/bills"
            params = {
                "q": query.query_text,
                "format": "json",
                "pageSize": min(query.max_results, 50)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                return await self._parse_congressional_results(data)
                
        except Exception as e:
            logger.error(f"GovInfo Congressional search error: {str(e)}")
            return []
    
    async def _parse_cfr_results(self, data: Dict[str, Any]) -> List[UnifiedDocument]:
        """Parse CFR search results"""
        documents = []
        
        try:
            packages = data.get("packages", [])
            
            for package in packages:
                doc = UnifiedDocument(
                    source_provider=DatabaseProvider.GOVINFO,
                    source_document_id=package.get("packageId", ""),
                    source_url=package.get("packageLink", ""),
                    title=package.get("title", ""),
                    document_type=ContentType.REGULATIONS,
                    citation=self._extract_cfr_citation(package.get("title", "")),
                    summary=package.get("summary", ""),
                    jurisdiction="Federal",
                    publication_date=self._parse_govinfo_date(package.get("dateIssued")),
                    is_free_access=True,
                    full_text_available=True,
                    provider_metadata=package
                )
                
                doc.authority_score = 0.9  # Federal regulations have high authority
                doc.recency_score = self._calculate_recency_score(doc.publication_date)
                
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Error parsing CFR results: {str(e)}")
        
        return documents
    
    async def _parse_federal_register_results(self, data: Dict[str, Any]) -> List[UnifiedDocument]:
        """Parse Federal Register results"""
        documents = []
        
        try:
            packages = data.get("packages", [])
            
            for package in packages:
                doc = UnifiedDocument(
                    source_provider=DatabaseProvider.GOVINFO,
                    source_document_id=package.get("packageId", ""),
                    source_url=package.get("packageLink", ""),
                    title=package.get("title", ""),
                    document_type=ContentType.REGULATIONS,
                    summary=package.get("summary", ""),
                    jurisdiction="Federal",
                    publication_date=self._parse_govinfo_date(package.get("dateIssued")),
                    is_free_access=True,
                    full_text_available=True,
                    provider_metadata=package
                )
                
                doc.authority_score = 0.8  # Federal Register has high authority
                doc.recency_score = self._calculate_recency_score(doc.publication_date)
                
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Error parsing Federal Register results: {str(e)}")
        
        return documents
    
    async def _parse_congressional_results(self, data: Dict[str, Any]) -> List[UnifiedDocument]:
        """Parse Congressional materials results"""
        documents = []
        
        try:
            packages = data.get("packages", [])
            
            for package in packages:
                doc = UnifiedDocument(
                    source_provider=DatabaseProvider.GOVINFO,
                    source_document_id=package.get("packageId", ""),
                    source_url=package.get("packageLink", ""),
                    title=package.get("title", ""),
                    document_type=ContentType.CONGRESSIONAL_MATERIALS,
                    summary=package.get("summary", ""),
                    jurisdiction="Federal",
                    publication_date=self._parse_govinfo_date(package.get("dateIssued")),
                    is_free_access=True,
                    full_text_available=True,
                    provider_metadata=package
                )
                
                doc.authority_score = 0.8  # Congressional materials have high authority
                doc.recency_score = self._calculate_recency_score(doc.publication_date)
                
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Error parsing Congressional results: {str(e)}")
        
        return documents
    
    def _extract_cfr_citation(self, title: str) -> Optional[str]:
        """Extract CFR citation from title"""
        try:
            # Look for CFR citation pattern
            pattern = r'\d+\s*C\.?F\.?R\.?\s*§?\s*\d+(\.\d+)?'
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0)
            return None
        except:
            return None
    
    def _parse_govinfo_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse GovInfo date format"""
        if not date_str:
            return None
        
        try:
            # GovInfo typically uses YYYY-MM-DD format
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            else:
                return datetime.fromisoformat(date_str).date()
        except:
            return None
    
    def _calculate_recency_score(self, pub_date: Optional[date]) -> float:
        """Calculate recency score"""
        if not pub_date:
            return 0.5
        
        try:
            today = date.today()
            years_old = (today - pub_date).days / 365.25
            
            if years_old <= 0.5:
                return 1.0
            elif years_old <= 1:
                return 0.9
            elif years_old <= 2:
                return 0.8
            elif years_old <= 5:
                return 0.6
            else:
                return 0.4
                
        except:
            return 0.5
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        
        # Remove timestamps outside the rate limit window
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if (now - ts).total_seconds() < self.rate_limit_window
        ]
        
        # Check if we're at the rate limit
        if len(self.request_timestamps) >= self.rate_limit:
            oldest_request = min(self.request_timestamps)
            wait_time = self.rate_limit_window - (now - oldest_request).total_seconds()
            if wait_time > 0:
                logger.info(f"GovInfo rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        self.request_timestamps.append(now)


class CongressGovClient:
    """
    Congress.gov API client for legislative information.
    Provides access to bills, resolutions, amendments, and legislative history.
    """
    
    def __init__(self, credentials: Optional[GovernmentCredentials] = None):
        self.credentials = credentials
        self.base_url = "https://api.congress.gov/v3"
        self.session: Optional[ClientSession] = None
        
        # Rate limiting
        self.rate_limit = 100  # requests per minute
        self.rate_limit_window = 60
        self.request_timestamps: List[datetime] = []
        
        self.capabilities = [
            DatabaseCapability.FULL_TEXT_SEARCH,
            DatabaseCapability.DATE_FILTERING,
            DatabaseCapability.FIELD_SEARCH,
            DatabaseCapability.FULL_DOCUMENT_ACCESS,
            DatabaseCapability.API_ACCESS
        ]
        
        logger.info("Congress.gov client initialized")
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = ClientTimeout(total=30, connect=10)
        headers = {
            "User-Agent": "LegalAI-UnifiedSearch/1.0 (Research Tool)",
            "Accept": "application/json"
        }
        
        if self.credentials and self.credentials.congress_api_key:
            headers["X-API-Key"] = self.credentials.congress_api_key
        
        self.session = ClientSession(timeout=timeout, headers=headers)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Congress.gov database"""
        try:
            logger.info(f"Executing Congress.gov search: {query.query_text[:100]}...")
            
            all_results = []
            
            # Search bills
            bill_results = await self._search_bills(query)
            all_results.extend(bill_results)
            
            # Search amendments
            if len(all_results) < query.max_results:
                amendment_results = await self._search_amendments(query)
                all_results.extend(amendment_results)
            
            return all_results[:query.max_results]
            
        except Exception as e:
            logger.error(f"Congress.gov search failed: {str(e)}")
            return []
    
    async def _search_bills(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Congressional bills"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/bill"
            params = {
                "q": query.query_text,
                "format": "json",
                "limit": min(query.max_results, 250)
            }
            
            # Add Congress session filter if date specified
            if query.date_from and query.date_from.year >= 1973:
                congress_num = ((query.date_from.year - 1789) // 2) + 1
                params["congress"] = congress_num
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                return await self._parse_bill_results(data)
                
        except Exception as e:
            logger.error(f"Congress.gov bill search error: {str(e)}")
            return []
    
    async def _search_amendments(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Congressional amendments"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/amendment"
            params = {
                "q": query.query_text,
                "format": "json",
                "limit": min(query.max_results, 100)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                return await self._parse_amendment_results(data)
                
        except Exception as e:
            logger.error(f"Congress.gov amendment search error: {str(e)}")
            return []
    
    async def _parse_bill_results(self, data: Dict[str, Any]) -> List[UnifiedDocument]:
        """Parse Congressional bill results"""
        documents = []
        
        try:
            bills = data.get("bills", [])
            
            for bill in bills:
                # Extract basic information
                title = bill.get("title", "")
                number = bill.get("number", "")
                bill_type = bill.get("type", "")
                congress = bill.get("congress", "")
                
                # Create bill identifier
                bill_id = f"{bill_type}{number}-{congress}"
                
                # Extract dates
                introduced_date = self._parse_congress_date(bill.get("introducedDate"))
                
                # Extract sponsors
                sponsors = []
                if "sponsors" in bill:
                    for sponsor in bill["sponsors"]:
                        sponsor_name = sponsor.get("fullName", "")
                        if sponsor_name:
                            sponsors.append(sponsor_name)
                
                doc = UnifiedDocument(
                    source_provider=DatabaseProvider.CONGRESS_GOV,
                    source_document_id=bill_id,
                    source_url=bill.get("url", ""),
                    title=title,
                    document_type=ContentType.CONGRESSIONAL_MATERIALS,
                    citation=bill_id,
                    summary=bill.get("summary", {}).get("text", "") if bill.get("summary") else "",
                    jurisdiction="Federal",
                    filing_date=introduced_date,
                    parties=sponsors,
                    legal_topics=bill.get("subjects", {}).get("legislativeSubjects", []) if bill.get("subjects") else [],
                    is_free_access=True,
                    full_text_available=True,
                    provider_metadata=bill
                )
                
                doc.authority_score = 0.8  # Congressional materials have high authority
                doc.recency_score = self._calculate_recency_score(introduced_date)
                
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Error parsing Congressional bill results: {str(e)}")
        
        return documents
    
    async def _parse_amendment_results(self, data: Dict[str, Any]) -> List[UnifiedDocument]:
        """Parse Congressional amendment results"""
        documents = []
        
        try:
            amendments = data.get("amendments", [])
            
            for amendment in amendments:
                title = amendment.get("description", "") or amendment.get("purpose", "")
                number = amendment.get("number", "")
                amendment_type = amendment.get("type", "")
                congress = amendment.get("congress", "")
                
                amendment_id = f"{amendment_type}{number}-{congress}"
                
                submitted_date = self._parse_congress_date(amendment.get("submittedDate"))
                
                doc = UnifiedDocument(
                    source_provider=DatabaseProvider.CONGRESS_GOV,
                    source_document_id=amendment_id,
                    source_url=amendment.get("url", ""),
                    title=title,
                    document_type=ContentType.CONGRESSIONAL_MATERIALS,
                    citation=amendment_id,
                    summary=amendment.get("description", ""),
                    jurisdiction="Federal",
                    filing_date=submitted_date,
                    is_free_access=True,
                    full_text_available=True,
                    provider_metadata=amendment
                )
                
                doc.authority_score = 0.7  # Amendments have good authority
                doc.recency_score = self._calculate_recency_score(submitted_date)
                
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Error parsing Congressional amendment results: {str(e)}")
        
        return documents
    
    def _parse_congress_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse Congress.gov date format"""
        if not date_str:
            return None
        
        try:
            # Congress.gov uses YYYY-MM-DD format
            return datetime.fromisoformat(date_str).date()
        except:
            return None
    
    def _calculate_recency_score(self, intro_date: Optional[date]) -> float:
        """Calculate recency score for legislative materials"""
        if not intro_date:
            return 0.5
        
        try:
            today = date.today()
            years_old = (today - intro_date).days / 365.25
            
            # Legislative materials stay relevant longer
            if years_old <= 1:
                return 1.0
            elif years_old <= 2:
                return 0.9
            elif years_old <= 5:
                return 0.8
            elif years_old <= 10:
                return 0.6
            else:
                return 0.4
                
        except:
            return 0.5
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if (now - ts).total_seconds() < self.rate_limit_window
        ]
        
        if len(self.request_timestamps) >= self.rate_limit:
            oldest_request = min(self.request_timestamps)
            wait_time = self.rate_limit_window - (now - oldest_request).total_seconds()
            if wait_time > 0:
                logger.info(f"Congress.gov rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        self.request_timestamps.append(now)


class SupremeCourtClient:
    """
    Supreme Court database client for opinions, oral arguments, and case information.
    Web scraping client for supremecourt.gov resources.
    """
    
    def __init__(self):
        self.base_url = "https://www.supremecourt.gov"
        self.session: Optional[ClientSession] = None
        
        # Conservative rate limiting for respectful scraping
        self.rate_limit = 20  # requests per minute
        self.rate_limit_window = 60
        self.request_timestamps: List[datetime] = []
        
        self.capabilities = [
            DatabaseCapability.FULL_TEXT_SEARCH,
            DatabaseCapability.DATE_FILTERING,
            DatabaseCapability.FULL_DOCUMENT_ACCESS
        ]
        
        logger.info("Supreme Court client initialized")
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = ClientTimeout(total=30, connect=10)
        headers = {
            "User-Agent": "LegalAI-UnifiedSearch/1.0 (Research Tool)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        self.session = ClientSession(timeout=timeout, headers=headers)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Supreme Court database"""
        try:
            logger.info(f"Executing Supreme Court search: {query.query_text[:100]}...")
            
            # Search opinions
            opinions = await self._search_opinions(query)
            
            return opinions[:query.max_results]
            
        except Exception as e:
            logger.error(f"Supreme Court search failed: {str(e)}")
            return []
    
    async def _search_opinions(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search Supreme Court opinions"""
        try:
            await self._check_rate_limit()
            
            # Supreme Court website search
            search_url = f"{self.base_url}/search"
            params = {
                "q": query.query_text,
                "content_type": "opinion"
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return await self._parse_opinion_results(soup)
                
        except Exception as e:
            logger.error(f"Supreme Court opinion search error: {str(e)}")
            return []
    
    async def _parse_opinion_results(self, soup: BeautifulSoup) -> List[UnifiedDocument]:
        """Parse Supreme Court opinion search results"""
        documents = []
        
        try:
            # Look for result containers (this would need to be adjusted based on actual HTML structure)
            result_containers = soup.find_all("div", class_="search-result") or soup.find_all("article")
            
            for container in result_containers:
                try:
                    # Extract title and URL
                    title_link = container.find("h2") or container.find("h3")
                    if not title_link:
                        continue
                    
                    link = title_link.find("a")
                    if not link:
                        continue
                    
                    title = link.get_text(strip=True)
                    url = link.get("href", "")
                    if url and not url.startswith("http"):
                        url = self.base_url + url
                    
                    # Extract case information
                    case_info = container.get_text()
                    decision_date = self._extract_supreme_court_date(case_info)
                    
                    doc = UnifiedDocument(
                        source_provider=DatabaseProvider.SUPREMECOURT_GOV,
                        source_document_id=url,
                        source_url=url,
                        title=title,
                        document_type=ContentType.CASES,
                        court="United States Supreme Court",
                        jurisdiction="Federal",
                        decision_date=decision_date,
                        is_free_access=True,
                        full_text_available=True,
                        provider_metadata={"container_html": str(container)[:500]}
                    )
                    
                    doc.authority_score = 1.0  # Supreme Court has highest authority
                    doc.recency_score = self._calculate_recency_score(decision_date)
                    
                    documents.append(doc)
                    
                except Exception as e:
                    logger.error(f"Error parsing Supreme Court result: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Supreme Court results: {str(e)}")
        
        return documents
    
    def _extract_supreme_court_date(self, text: str) -> Optional[date]:
        """Extract decision date from Supreme Court case text"""
        try:
            # Look for date patterns
            date_patterns = [
                r'(\w+ \d{1,2}, \d{4})',  # Month Day, Year
                r'(\d{1,2}/\d{1,2}/\d{4})'  # MM/DD/YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        date_str = match.group(1)
                        if "/" in date_str:
                            return datetime.strptime(date_str, "%m/%d/%Y").date()
                        else:
                            return datetime.strptime(date_str, "%B %d, %Y").date()
                    except:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting Supreme Court date: {str(e)}")
            return None
    
    def _calculate_recency_score(self, decision_date: Optional[date]) -> float:
        """Calculate recency score"""
        if not decision_date:
            return 0.5
        
        try:
            today = date.today()
            years_old = (today - decision_date).days / 365.25
            
            # Supreme Court cases remain highly relevant
            if years_old <= 5:
                return 1.0
            elif years_old <= 10:
                return 0.9
            elif years_old <= 20:
                return 0.8
            elif years_old <= 50:
                return 0.7
            else:
                return 0.6  # Even very old Supreme Court cases retain authority
                
        except:
            return 0.5
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if (now - ts).total_seconds() < self.rate_limit_window
        ]
        
        if len(self.request_timestamps) >= self.rate_limit:
            oldest_request = min(self.request_timestamps)
            wait_time = self.rate_limit_window - (now - oldest_request).total_seconds()
            if wait_time > 0:
                logger.info(f"Supreme Court rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        self.request_timestamps.append(now)