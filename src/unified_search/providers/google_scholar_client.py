"""
Google Scholar Legal Client

Web scraping integration for Google Scholar's legal case search functionality.
Provides access to case law, legal opinions, and court documents.
"""

import asyncio
import logging
import re
import urllib.parse
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from uuid import UUID

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from ..database_models import (
    DatabaseProvider, UnifiedQuery, UnifiedDocument, UnifiedSearchResult,
    ContentType, DatabaseCapability, AccessType
)

logger = logging.getLogger(__name__)


class GoogleScholarClient:
    """
    Google Scholar Legal client for case law research.
    
    Note: This client uses web scraping as Google Scholar doesn't provide
    a public API. Use responsibly with appropriate rate limiting.
    """
    
    def __init__(self):
        self.base_url = "https://scholar.google.com"
        self.session: Optional[ClientSession] = None
        
        # Conservative rate limiting for ethical scraping
        self.rate_limit = 10  # requests per minute
        self.rate_limit_window = 60
        self.request_timestamps: List[datetime] = []
        
        # Supported capabilities
        self.capabilities = [
            DatabaseCapability.FULL_TEXT_SEARCH,
            DatabaseCapability.CITATION_SEARCH,
            DatabaseCapability.BOOLEAN_SEARCH,
            DatabaseCapability.DATE_FILTERING,
            DatabaseCapability.JURISDICTION_FILTERING,
            DatabaseCapability.COURT_FILTERING,
            DatabaseCapability.DOCUMENT_TYPE_FILTERING
        ]
        
        # Common user agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        self.current_user_agent = 0
        
        logger.info("Google Scholar Legal client initialized")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP session with appropriate headers"""
        timeout = ClientTimeout(total=30, connect=10)
        
        headers = {
            "User-Agent": self.user_agents[self.current_user_agent],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self.session = ClientSession(timeout=timeout, headers=headers)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: UnifiedQuery) -> UnifiedSearchResult:
        """Search Google Scholar Legal database"""
        try:
            logger.info(f"Executing Google Scholar search: {query.query_text[:100]}...")
            
            # Build search URL and parameters
            search_url, search_params = await self._build_search_url(query)
            
            # Execute search
            search_results = await self._execute_search(search_url, search_params, query)
            
            # Create unified result
            result = UnifiedSearchResult(
                query=query,
                total_results=len(search_results),
                results_returned=len(search_results),
                documents=search_results,
                provider_results={DatabaseProvider.GOOGLE_SCHOLAR.value: len(search_results)},
                providers_searched=[DatabaseProvider.GOOGLE_SCHOLAR],
                total_cost=0.0,  # Free service
                cost_by_provider={DatabaseProvider.GOOGLE_SCHOLAR.value: 0.0}
            )
            
            logger.info(f"Google Scholar search completed: {len(search_results)} results")
            return result
            
        except Exception as e:
            logger.error(f"Google Scholar search failed: {str(e)}")
            return UnifiedSearchResult(
                query=query,
                providers_failed=[DatabaseProvider.GOOGLE_SCHOLAR]
            )
    
    async def get_document(self, document_id: str) -> Optional[UnifiedDocument]:
        """
        Retrieve specific document by ID (URL)
        Note: document_id should be the Google Scholar URL
        """
        try:
            await self._check_rate_limit()
            
            async with self.session.get(document_id) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return await self._parse_document_page(soup, document_id)
                
        except Exception as e:
            logger.error(f"Google Scholar document retrieval failed: {str(e)}")
            return None
    
    async def _execute_search(
        self,
        search_url: str,
        search_params: Dict[str, str],
        query: UnifiedQuery
    ) -> List[UnifiedDocument]:
        """Execute search and parse results"""
        try:
            await self._check_rate_limit()
            
            # Rotate user agent for each search
            self._rotate_user_agent()
            
            async with self.session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    logger.error(f"Google Scholar search failed: {response.status}")
                    return []
                
                html = await response.text()
                
                # Check if we're being blocked
                if "blocked" in html.lower() or "captcha" in html.lower():
                    logger.warning("Google Scholar may be blocking requests")
                    return []
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parse search results
                results = await self._parse_search_results(soup, query)
                
                return results
                
        except Exception as e:
            logger.error(f"Google Scholar search execution error: {str(e)}")
            return []
    
    async def _parse_search_results(
        self,
        soup: BeautifulSoup,
        query: UnifiedQuery
    ) -> List[UnifiedDocument]:
        """Parse Google Scholar search results page"""
        documents = []
        
        try:
            # Find result containers
            result_divs = soup.find_all("div", class_="gs_r gs_or gs_scl")
            
            for div in result_divs:
                try:
                    doc = await self._parse_result_item(div)
                    if doc:
                        documents.append(doc)
                        
                        # Limit results to requested maximum
                        if len(documents) >= query.max_results:
                            break
                            
                except Exception as e:
                    logger.error(f"Error parsing individual result: {str(e)}")
                    continue
            
            logger.info(f"Parsed {len(documents)} results from Google Scholar")
            
        except Exception as e:
            logger.error(f"Error parsing Google Scholar results: {str(e)}")
        
        return documents
    
    async def _parse_result_item(self, result_div) -> Optional[UnifiedDocument]:
        """Parse individual search result item"""
        try:
            # Extract title and URL
            title_link = result_div.find("h3", class_="gs_rt")
            if not title_link:
                return None
            
            title_element = title_link.find("a")
            if title_element:
                title = title_element.get_text(strip=True)
                url = title_element.get("href", "")
            else:
                title = title_link.get_text(strip=True)
                url = ""
            
            # Clean title (remove [PDF] and other markers)
            title = re.sub(r'\[PDF\]|\[HTML\]|\[DOC\]', '', title).strip()
            
            # Extract snippet/summary
            snippet_div = result_div.find("div", class_="gs_rs")
            summary = snippet_div.get_text(strip=True) if snippet_div else ""
            
            # Extract citation information
            citation_div = result_div.find("div", class_="gs_a")
            citation_info = citation_div.get_text(strip=True) if citation_div else ""
            
            # Parse citation info to extract court, year, etc.
            court, decision_date, citation = self._parse_citation_info(citation_info)
            
            # Extract additional metadata
            metadata_div = result_div.find("div", class_="gs_fl")
            cited_by_count = 0
            related_articles = 0
            
            if metadata_div:
                cited_by_link = metadata_div.find("a", string=re.compile(r"Cited by \d+"))
                if cited_by_link:
                    match = re.search(r"Cited by (\d+)", cited_by_link.get_text())
                    if match:
                        cited_by_count = int(match.group(1))
                
                related_link = metadata_div.find("a", string=re.compile(r"Related articles"))
                if related_link:
                    related_articles = 1
            
            # Determine document type
            document_type = self._determine_document_type(title, citation_info)
            
            # Create unified document
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.GOOGLE_SCHOLAR,
                source_document_id=url or title,
                source_url=url,
                title=title,
                document_type=document_type,
                citation=citation,
                summary=summary,
                court=court,
                jurisdiction=self._map_court_to_jurisdiction(court),
                decision_date=decision_date,
                is_free_access=True,
                full_text_available=bool(url and "scholar.google.com" not in url),
                provider_metadata={
                    "citation_info": citation_info,
                    "cited_by_count": cited_by_count,
                    "has_related_articles": related_articles > 0
                }
            )
            
            # Calculate scores
            doc.relevance_score = self._calculate_relevance_score(title, summary, query.query_text if hasattr(query, 'query_text') else "")
            doc.authority_score = self._calculate_authority_score(court, cited_by_count)
            doc.recency_score = self._calculate_recency_score(decision_date)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing result item: {str(e)}")
            return None
    
    async def _parse_document_page(self, soup: BeautifulSoup, url: str) -> Optional[UnifiedDocument]:
        """Parse individual document page for full content"""
        try:
            # Extract full text content
            content_div = soup.find("div", id="gs_text") or soup.find("div", class_="gs_text")
            full_text = content_div.get_text(strip=True) if content_div else ""
            
            # Extract title
            title_element = soup.find("title")
            title = title_element.get_text(strip=True) if title_element else "Document"
            
            # Create document
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.GOOGLE_SCHOLAR,
                source_document_id=url,
                source_url=url,
                title=title,
                document_type=ContentType.CASES,
                full_text=full_text,
                is_free_access=True,
                full_text_available=bool(full_text),
                provider_metadata={"full_page": True}
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing document page: {str(e)}")
            return None
    
    def _parse_citation_info(self, citation_info: str) -> tuple[Optional[str], Optional[date], Optional[str]]:
        """Parse citation information to extract court, date, and citation"""
        court = None
        decision_date = None
        citation = None
        
        try:
            if not citation_info:
                return court, decision_date, citation
            
            # Extract year from citation info
            year_match = re.search(r'(\d{4})', citation_info)
            if year_match:
                try:
                    year = int(year_match.group(1))
                    if 1800 <= year <= datetime.now().year:  # Reasonable year range
                        decision_date = date(year, 1, 1)  # Use January 1st as placeholder
                except:
                    pass
            
            # Extract court name (often appears before year)
            parts = citation_info.split('-')
            if len(parts) > 1:
                potential_court = parts[0].strip()
                if len(potential_court) > 2 and not re.match(r'^\d+', potential_court):
                    court = potential_court
            
            # Look for citation patterns (simplified)
            citation_patterns = [
                r'\d+\s+\w+\.?\s+\d+',  # Volume Reporter Page
                r'\d{4}\s+\w+\s+\d+',   # Year Court Number
                r'No\.\s*\d+',          # Case number
            ]
            
            for pattern in citation_patterns:
                match = re.search(pattern, citation_info)
                if match:
                    citation = match.group(0)
                    break
            
            # If no specific citation found, use the whole string (truncated)
            if not citation and len(citation_info) < 100:
                citation = citation_info
        
        except Exception as e:
            logger.error(f"Error parsing citation info: {str(e)}")
        
        return court, decision_date, citation
    
    def _determine_document_type(self, title: str, citation_info: str) -> ContentType:
        """Determine document type based on title and citation"""
        title_lower = title.lower()
        citation_lower = citation_info.lower()
        
        # Check for specific document types
        if any(word in title_lower for word in ["brief", "petition", "motion"]):
            return ContentType.BRIEFS
        elif any(word in citation_lower for word in ["statute", "code", "usc", "cfr"]):
            return ContentType.STATUTES
        elif "regulation" in citation_lower:
            return ContentType.REGULATIONS
        elif any(word in title_lower for word in ["constitution", "constitutional"]):
            return ContentType.CONSTITUTIONS
        else:
            # Default to cases for most Google Scholar Legal results
            return ContentType.CASES
    
    def _map_court_to_jurisdiction(self, court: Optional[str]) -> str:
        """Map court name to jurisdiction"""
        if not court:
            return "Unknown"
        
        court_lower = court.lower()
        
        # Federal courts
        if any(word in court_lower for word in ["supreme court", "scotus", "us", "united states"]):
            return "Federal"
        elif any(word in court_lower for word in ["circuit", "court of appeals", "federal"]):
            return "Federal"
        elif "district" in court_lower and ("us" in court_lower or "united states" in court_lower):
            return "Federal"
        
        # Try to extract state from court name
        state_indicators = [
            "california", "ca", "texas", "tx", "new york", "ny", "florida", "fl",
            "illinois", "il", "pennsylvania", "pa", "ohio", "oh", "georgia", "ga",
            "michigan", "mi", "north carolina", "nc", "virginia", "va", "washington", "wa"
        ]
        
        for state in state_indicators:
            if state in court_lower:
                return state.upper() if len(state) == 2 else state.title()
        
        return "State"
    
    def _calculate_relevance_score(self, title: str, summary: str, query: str) -> float:
        """Calculate relevance score based on keyword matching"""
        try:
            if not query:
                return 0.5
            
            query_words = set(query.lower().split())
            title_words = set(title.lower().split())
            summary_words = set(summary.lower().split())
            
            # Calculate overlap
            title_overlap = len(query_words & title_words) / max(len(query_words), 1)
            summary_overlap = len(query_words & summary_words) / max(len(query_words), 1)
            
            # Weight title matches more heavily
            score = (title_overlap * 0.7) + (summary_overlap * 0.3)
            return min(score, 1.0)
            
        except:
            return 0.5
    
    def _calculate_authority_score(self, court: Optional[str], cited_by_count: int) -> float:
        """Calculate authority score based on court level and citations"""
        try:
            base_score = 0.5
            
            # Court-based scoring
            if court:
                court_lower = court.lower()
                if "supreme court" in court_lower:
                    base_score = 0.9
                elif any(word in court_lower for word in ["circuit", "court of appeals"]):
                    base_score = 0.7
                elif "district" in court_lower:
                    base_score = 0.6
            
            # Citation-based boost
            citation_boost = min(cited_by_count / 100.0, 0.3)  # Max 0.3 boost
            
            return min(base_score + citation_boost, 1.0)
            
        except:
            return 0.5
    
    def _calculate_recency_score(self, decision_date: Optional[date]) -> float:
        """Calculate recency score based on decision date"""
        if not decision_date:
            return 0.5
        
        try:
            today = date.today()
            years_old = (today - decision_date).days / 365.25
            
            # Score decreases with age
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
    
    async def _build_search_url(self, query: UnifiedQuery) -> tuple[str, Dict[str, str]]:
        """Build Google Scholar search URL and parameters"""
        search_url = f"{self.base_url}/scholar"
        
        params = {
            "q": query.query_text,
            "hl": "en",  # Language
            "as_sdt": "4",  # Case law
            "as_vis": "1",  # Include citations
        }
        
        # Add date filters
        if query.date_from or query.date_to:
            if query.date_from:
                params["as_ylo"] = str(query.date_from.year)
            if query.date_to:
                params["as_yhi"] = str(query.date_to.year)
        
        # Add jurisdiction filters (if supported)
        if query.jurisdictions:
            # Google Scholar doesn't have direct jurisdiction filtering
            # but we can modify the query
            jurisdiction_terms = " OR ".join(f'"{j}"' for j in query.jurisdictions)
            params["q"] += f" ({jurisdiction_terms})"
        
        # Add court filters
        if query.courts:
            court_terms = " OR ".join(f'"{c}"' for c in query.courts)
            params["q"] += f" ({court_terms})"
        
        # Results per page (Google Scholar typically shows 10-20)
        if query.max_results:
            params["num"] = str(min(query.max_results, 20))
        
        return search_url, params
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        self.current_user_agent = (self.current_user_agent + 1) % len(self.user_agents)
        if self.session:
            self.session._default_headers["User-Agent"] = self.user_agents[self.current_user_agent]
    
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
                logger.info(f"Google Scholar rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(now)