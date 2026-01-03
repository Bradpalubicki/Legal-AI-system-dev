"""
Justia API Client

Free legal database integration for comprehensive US law access including
federal and state cases, statutes, regulations, and legal forms.
"""

import asyncio
import logging
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Any
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


class JustiaCredentials:
    """Justia API credentials (free service, may require API key in future)"""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # Currently not required, but future-proofing


class JustiaClient:
    """
    Justia API client providing access to comprehensive US legal database
    including federal cases, state cases, statutes, regulations, and forms.
    """
    
    def __init__(self, credentials: Optional[JustiaCredentials] = None):
        self.credentials = credentials
        self.base_url = "https://law.justia.com"
        self.session: Optional[ClientSession] = None
        
        # Rate limiting for respectful usage
        self.rate_limit = 30  # requests per minute
        self.rate_limit_window = 60
        self.request_timestamps: List[datetime] = []
        
        # Supported capabilities
        self.capabilities = [
            DatabaseCapability.FULL_TEXT_SEARCH,
            DatabaseCapability.CITATION_SEARCH,
            DatabaseCapability.BOOLEAN_SEARCH,
            DatabaseCapability.FIELD_SEARCH,
            DatabaseCapability.DATE_FILTERING,
            DatabaseCapability.JURISDICTION_FILTERING,
            DatabaseCapability.COURT_FILTERING,
            DatabaseCapability.DOCUMENT_TYPE_FILTERING,
            DatabaseCapability.FULL_DOCUMENT_ACCESS
        ]
        
        logger.info("Justia client initialized")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = ClientTimeout(total=30, connect=10)
        headers = {
            "User-Agent": "LegalAI-UnifiedSearch/1.0 (Research Tool)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive"
        }
        
        if self.credentials and self.credentials.api_key:
            headers["Authorization"] = f"Bearer {self.credentials.api_key}"
        
        self.session = ClientSession(timeout=timeout, headers=headers)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: UnifiedQuery) -> UnifiedSearchResult:
        """Search Justia database"""
        try:
            logger.info(f"Executing Justia search: {query.query_text[:100]}...")
            
            # Execute searches across different content types
            search_results = []
            
            # Search federal cases
            if ContentType.CASES in query.content_types or not query.content_types:
                federal_cases = await self._search_federal_cases(query)
                search_results.extend(federal_cases)
                
                # Search state cases if within limits
                if len(search_results) < query.max_results:
                    state_cases = await self._search_state_cases(query)
                    search_results.extend(state_cases)
            
            # Search statutes
            if ContentType.STATUTES in query.content_types:
                statutes = await self._search_statutes(query)
                search_results.extend(statutes)
            
            # Search regulations
            if ContentType.REGULATIONS in query.content_types:
                regulations = await self._search_regulations(query)
                search_results.extend(regulations)
            
            # Limit to requested maximum
            search_results = search_results[:query.max_results]
            
            # Create unified result
            result = UnifiedSearchResult(
                query=query,
                total_results=len(search_results),
                results_returned=len(search_results),
                documents=search_results,
                provider_results={DatabaseProvider.JUSTIA.value: len(search_results)},
                providers_searched=[DatabaseProvider.JUSTIA],
                total_cost=0.0,  # Free service
                cost_by_provider={DatabaseProvider.JUSTIA.value: 0.0}
            )
            
            logger.info(f"Justia search completed: {len(search_results)} results")
            return result
            
        except Exception as e:
            logger.error(f"Justia search failed: {str(e)}")
            return UnifiedSearchResult(
                query=query,
                providers_failed=[DatabaseProvider.JUSTIA]
            )
    
    async def get_document(self, document_id: str) -> Optional[UnifiedDocument]:
        """Retrieve specific document by URL"""
        try:
            await self._check_rate_limit()
            
            async with self.session.get(document_id) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return await self._parse_document_page(soup, document_id)
                
        except Exception as e:
            logger.error(f"Justia document retrieval failed: {str(e)}")
            return None
    
    async def _search_federal_cases(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search federal cases"""
        try:
            await self._check_rate_limit()
            
            # Build search URL for federal cases
            search_url = f"{self.base_url}/cases/federal/us/"
            params = {
                "q": query.query_text
            }
            
            # Add date filters
            if query.date_from:
                params["year_start"] = str(query.date_from.year)
            if query.date_to:
                params["year_end"] = str(query.date_to.year)
            
            # Execute search
            async with self.session.get(search_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Justia federal cases search failed: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parse results
                return await self._parse_case_results(soup, ContentType.CASES, "Federal")
                
        except Exception as e:
            logger.error(f"Justia federal cases search error: {str(e)}")
            return []
    
    async def _search_state_cases(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search state cases"""
        try:
            documents = []
            
            # Search major state jurisdictions
            priority_states = ["california", "new-york", "texas", "florida", "illinois"]
            
            for state in priority_states:
                if len(documents) >= query.max_results:
                    break
                
                try:
                    await self._check_rate_limit()
                    
                    search_url = f"{self.base_url}/cases/{state}/"
                    params = {"q": query.query_text}
                    
                    async with self.session.get(search_url, params=params) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            state_results = await self._parse_case_results(soup, ContentType.CASES, state.title().replace("-", " "))
                            documents.extend(state_results)
                
                except Exception as e:
                    logger.error(f"Error searching {state} cases: {str(e)}")
                    continue
            
            return documents[:query.max_results]
            
        except Exception as e:
            logger.error(f"Justia state cases search error: {str(e)}")
            return []
    
    async def _search_statutes(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search statutes"""
        try:
            await self._check_rate_limit()
            
            search_url = f"{self.base_url}/codes/us/"
            params = {"q": query.query_text}
            
            async with self.session.get(search_url, params=params) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return await self._parse_statute_results(soup)
                
        except Exception as e:
            logger.error(f"Justia statutes search error: {str(e)}")
            return []
    
    async def _search_regulations(self, query: UnifiedQuery) -> List[UnifiedDocument]:
        """Search regulations (CFR)"""
        try:
            await self._check_rate_limit()
            
            search_url = f"{self.base_url}/cfr/"
            params = {"q": query.query_text}
            
            async with self.session.get(search_url, params=params) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return await self._parse_regulation_results(soup)
                
        except Exception as e:
            logger.error(f"Justia regulations search error: {str(e)}")
            return []
    
    async def _parse_case_results(
        self,
        soup: BeautifulSoup,
        content_type: ContentType,
        jurisdiction: str
    ) -> List[UnifiedDocument]:
        """Parse case search results"""
        documents = []
        
        try:
            # Look for result containers
            result_containers = soup.find_all("div", class_="result") or soup.find_all("article")
            
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
                    
                    # Extract citation
                    citation = self._extract_citation(container)
                    
                    # Extract summary
                    summary_elem = container.find("p") or container.find("div", class_="summary")
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    # Extract court and date
                    court, decision_date = self._extract_court_and_date(container, jurisdiction)
                    
                    # Create document
                    doc = UnifiedDocument(
                        source_provider=DatabaseProvider.JUSTIA,
                        source_document_id=url,
                        source_url=url,
                        title=title,
                        document_type=content_type,
                        citation=citation,
                        summary=summary,
                        court=court,
                        jurisdiction=jurisdiction,
                        decision_date=decision_date,
                        is_free_access=True,
                        full_text_available=True,
                        provider_metadata={
                            "container_html": str(container)[:500]
                        }
                    )
                    
                    # Calculate scores
                    doc.relevance_score = self._calculate_relevance_score(title, summary)
                    doc.authority_score = self._calculate_authority_score(court, jurisdiction)
                    doc.recency_score = self._calculate_recency_score(decision_date)
                    
                    documents.append(doc)
                    
                except Exception as e:
                    logger.error(f"Error parsing case result: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing case results: {str(e)}")
        
        return documents
    
    async def _parse_statute_results(self, soup: BeautifulSoup) -> List[UnifiedDocument]:
        """Parse statute search results"""
        documents = []
        
        try:
            result_containers = soup.find_all("div", class_="result") or soup.find_all("article")
            
            for container in result_containers:
                try:
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
                    
                    # Extract statute citation (USC, etc.)
                    citation = self._extract_statute_citation(title, container)
                    
                    summary_elem = container.find("p")
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    doc = UnifiedDocument(
                        source_provider=DatabaseProvider.JUSTIA,
                        source_document_id=url,
                        source_url=url,
                        title=title,
                        document_type=ContentType.STATUTES,
                        citation=citation,
                        summary=summary,
                        jurisdiction="Federal",
                        is_free_access=True,
                        full_text_available=True
                    )
                    
                    doc.relevance_score = self._calculate_relevance_score(title, summary)
                    doc.authority_score = 0.9  # Statutes have high authority
                    doc.recency_score = 0.8    # Statutes are generally current
                    
                    documents.append(doc)
                    
                except Exception as e:
                    logger.error(f"Error parsing statute result: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing statute results: {str(e)}")
        
        return documents
    
    async def _parse_regulation_results(self, soup: BeautifulSoup) -> List[UnifiedDocument]:
        """Parse regulation (CFR) search results"""
        documents = []
        
        try:
            result_containers = soup.find_all("div", class_="result") or soup.find_all("article")
            
            for container in result_containers:
                try:
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
                    
                    # Extract CFR citation
                    citation = self._extract_cfr_citation(title, container)
                    
                    summary_elem = container.find("p")
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    doc = UnifiedDocument(
                        source_provider=DatabaseProvider.JUSTIA,
                        source_document_id=url,
                        source_url=url,
                        title=title,
                        document_type=ContentType.REGULATIONS,
                        citation=citation,
                        summary=summary,
                        jurisdiction="Federal",
                        is_free_access=True,
                        full_text_available=True
                    )
                    
                    doc.relevance_score = self._calculate_relevance_score(title, summary)
                    doc.authority_score = 0.8  # Regulations have high authority
                    doc.recency_score = 0.8    # Regulations are generally current
                    
                    documents.append(doc)
                    
                except Exception as e:
                    logger.error(f"Error parsing regulation result: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing regulation results: {str(e)}")
        
        return documents
    
    async def _parse_document_page(self, soup: BeautifulSoup, url: str) -> Optional[UnifiedDocument]:
        """Parse individual document page for full content"""
        try:
            # Extract title
            title_elem = soup.find("h1") or soup.find("title")
            title = title_elem.get_text(strip=True) if title_elem else "Document"
            
            # Extract full text
            content_selectors = [
                "div.content", "div.case-content", "div.statute-content",
                "article", "main", ".document-content"
            ]
            
            full_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    full_text = content_elem.get_text(separator="\n", strip=True)
                    break
            
            # Determine document type from URL
            document_type = ContentType.CASES
            if "/codes/" in url:
                document_type = ContentType.STATUTES
            elif "/cfr/" in url:
                document_type = ContentType.REGULATIONS
            
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.JUSTIA,
                source_document_id=url,
                source_url=url,
                title=title,
                document_type=document_type,
                full_text=full_text,
                is_free_access=True,
                full_text_available=bool(full_text),
                provider_metadata={"parsed_from_page": True}
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing document page: {str(e)}")
            return None
    
    def _extract_citation(self, container) -> Optional[str]:
        """Extract citation from result container"""
        try:
            # Look for citation patterns
            text = container.get_text()
            
            # Common citation patterns
            patterns = [
                r'\d+\s+U\.S\.\s+\d+',        # US Reports
                r'\d+\s+S\.\s?Ct\.\s+\d+',    # Supreme Court Reporter
                r'\d+\s+F\.\d*d?\s+\d+',      # Federal Reporter
                r'\d+\s+F\.\s?Supp\.\s?\d*\s+\d+',  # Federal Supplement
                r'\d{4}\s+\w+\s+\d+',         # Year Court Number format
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting citation: {str(e)}")
            return None
    
    def _extract_statute_citation(self, title: str, container) -> Optional[str]:
        """Extract statute citation (USC, etc.)"""
        try:
            text = f"{title} {container.get_text()}"
            
            patterns = [
                r'\d+\s+U\.S\.C\.?\s+§?\s*\d+',      # US Code
                r'\d+\s+USC\s+§?\s*\d+',             # US Code abbreviated
                r'Section\s+\d+',                     # Section reference
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting statute citation: {str(e)}")
            return None
    
    def _extract_cfr_citation(self, title: str, container) -> Optional[str]:
        """Extract CFR citation"""
        try:
            text = f"{title} {container.get_text()}"
            
            patterns = [
                r'\d+\s+C\.?F\.?R\.?\s+§?\s*\d+',    # CFR
                r'\d+\s+CFR\s+§?\s*\d+',             # CFR abbreviated
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting CFR citation: {str(e)}")
            return None
    
    def _extract_court_and_date(self, container, jurisdiction: str) -> tuple[Optional[str], Optional[date]]:
        """Extract court name and decision date"""
        court = None
        decision_date = None
        
        try:
            text = container.get_text()
            
            # Extract date
            date_patterns = [
                r'(\w+\s+\d{1,2},\s+\d{4})',  # Month Day, Year
                r'(\d{1,2}/\d{1,2}/\d{4})',   # MM/DD/YYYY
                r'(\d{4}-\d{2}-\d{2})',       # YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        date_str = match.group(1)
                        if "/" in date_str:
                            decision_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                        elif "-" in date_str:
                            decision_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        else:
                            decision_date = datetime.strptime(date_str, "%B %d, %Y").date()
                        break
                    except:
                        continue
            
            # Extract court (simplified - would need more sophisticated parsing)
            if jurisdiction.lower() == "federal":
                if "supreme court" in text.lower():
                    court = "United States Supreme Court"
                elif "court of appeals" in text.lower() or "circuit" in text.lower():
                    court = "US Court of Appeals"
                elif "district" in text.lower():
                    court = "US District Court"
                else:
                    court = f"Federal Court ({jurisdiction})"
            else:
                court = f"{jurisdiction} Court"
        
        except Exception as e:
            logger.error(f"Error extracting court and date: {str(e)}")
        
        return court, decision_date
    
    def _calculate_relevance_score(self, title: str, summary: str) -> float:
        """Calculate relevance score (simplified)"""
        try:
            # Basic scoring based on content length and structure
            title_words = len(title.split()) if title else 0
            summary_words = len(summary.split()) if summary else 0
            
            # More content generally means more relevant result
            if title_words > 5 and summary_words > 20:
                return 0.8
            elif title_words > 3 and summary_words > 10:
                return 0.6
            else:
                return 0.4
                
        except:
            return 0.5
    
    def _calculate_authority_score(self, court: Optional[str], jurisdiction: str) -> float:
        """Calculate authority score based on court level"""
        try:
            if not court:
                return 0.5
            
            court_lower = court.lower()
            
            # Supreme Court
            if "supreme court" in court_lower:
                return 1.0
            
            # Appeals/Circuit Courts
            if any(word in court_lower for word in ["appeals", "circuit"]):
                return 0.8
            
            # District Courts
            if "district" in court_lower:
                return 0.6
            
            # Federal vs State
            if jurisdiction.lower() == "federal":
                return 0.7
            else:
                return 0.6
            
        except:
            return 0.5
    
    def _calculate_recency_score(self, decision_date: Optional[date]) -> float:
        """Calculate recency score based on decision date"""
        if not decision_date:
            return 0.5
        
        try:
            today = date.today()
            years_old = (today - decision_date).days / 365.25
            
            if years_old <= 1:
                return 1.0
            elif years_old <= 5:
                return 0.8
            elif years_old <= 10:
                return 0.6
            elif years_old <= 20:
                return 0.4
            else:
                return 0.2
                
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
            # Wait until we can make another request
            oldest_request = min(self.request_timestamps)
            wait_time = self.rate_limit_window - (now - oldest_request).total_seconds()
            if wait_time > 0:
                logger.info(f"Justia rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(now)