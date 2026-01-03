"""
CourtListener API Client

Free legal database integration for comprehensive case law access,
docket information, and federal court opinions.
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from ..database_models import (
    DatabaseProvider, UnifiedQuery, UnifiedDocument, UnifiedSearchResult,
    ContentType, DatabaseCapability, AccessType
)

logger = logging.getLogger(__name__)


class CourtListenerCredentials:
    """CourtListener API credentials (API key based)"""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # Optional - free tier available without key


class CourtListenerClient:
    """
    CourtListener API client providing access to comprehensive US case law,
    court opinions, dockets, oral arguments, and judicial data.
    """
    
    def __init__(self, credentials: Optional[CourtListenerCredentials] = None):
        self.credentials = credentials
        self.base_url = "https://www.courtlistener.com/api/rest/v3"
        self.session: Optional[ClientSession] = None
        
        # Rate limiting (CourtListener is generous but we should be respectful)
        self.rate_limit = 100  # requests per minute
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
            DatabaseCapability.FULL_DOCUMENT_ACCESS,
            DatabaseCapability.API_ACCESS,
            DatabaseCapability.BULK_DOWNLOAD
        ]
        
        logger.info("CourtListener client initialized")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = ClientTimeout(total=30, connect=10)
        headers = {
            "User-Agent": "LegalAI-UnifiedSearch/1.0 (Research Tool)"
        }
        
        if self.credentials and self.credentials.api_key:
            headers["Authorization"] = f"Token {self.credentials.api_key}"
        
        self.session = ClientSession(timeout=timeout, headers=headers)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: UnifiedQuery) -> UnifiedSearchResult:
        """Search CourtListener database"""
        try:
            logger.info(f"Executing CourtListener search: {query.query_text[:100]}...")
            
            # Build search parameters
            search_params = await self._build_search_params(query)
            
            # Execute search across relevant endpoints
            search_results = []
            
            # Search opinions
            if ContentType.CASES in query.content_types or not query.content_types:
                opinions = await self._search_opinions(search_params, query)
                search_results.extend(opinions)
            
            # Search dockets
            if ContentType.DOCKETS in query.content_types:
                dockets = await self._search_dockets(search_params, query)
                search_results.extend(dockets)
            
            # Search oral arguments
            if ContentType.ORAL_ARGUMENTS in query.content_types:
                oral_args = await self._search_oral_arguments(search_params, query)
                search_results.extend(oral_args)
            
            # Create unified result
            result = UnifiedSearchResult(
                query=query,
                total_results=len(search_results),
                results_returned=len(search_results),
                documents=search_results,
                provider_results={DatabaseProvider.COURTLISTENER.value: len(search_results)},
                providers_searched=[DatabaseProvider.COURTLISTENER],
                total_cost=0.0,  # Free service
                cost_by_provider={DatabaseProvider.COURTLISTENER.value: 0.0}
            )
            
            logger.info(f"CourtListener search completed: {len(search_results)} results")
            return result
            
        except Exception as e:
            logger.error(f"CourtListener search failed: {str(e)}")
            return UnifiedSearchResult(
                query=query,
                providers_failed=[DatabaseProvider.COURTLISTENER]
            )
    
    async def get_document(self, document_id: str) -> Optional[UnifiedDocument]:
        """Retrieve specific document by ID"""
        try:
            # Try different CourtListener endpoints based on ID format
            document = None
            
            # Try opinion endpoint
            try:
                document = await self._get_opinion(document_id)
            except:
                pass
            
            # Try docket endpoint if opinion failed
            if not document:
                try:
                    document = await self._get_docket(document_id)
                except:
                    pass
            
            return document
            
        except Exception as e:
            logger.error(f"CourtListener document retrieval failed: {str(e)}")
            return None
    
    async def get_court_information(self, court_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed court information"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/courts/{court_id}/"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    court_data = await response.json()
                    return court_data
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Court information retrieval failed: {str(e)}")
            return None
    
    async def get_judge_information(self, judge_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed judge information"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/people/{judge_id}/"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    judge_data = await response.json()
                    return judge_data
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Judge information retrieval failed: {str(e)}")
            return None
    
    async def _search_opinions(
        self,
        search_params: Dict[str, Any],
        query: UnifiedQuery
    ) -> List[UnifiedDocument]:
        """Search opinions endpoint"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/search/"
            
            # CourtListener search parameters
            params = {
                "q": query.query_text,
                "type": "o",  # opinions
                "format": "json",
                "order_by": "score desc" if query.sort_by == "relevance" else "dateFiled desc"
            }
            
            # Add filters
            if query.jurisdictions:
                params["court"] = ",".join(query.jurisdictions)
            
            if query.date_from:
                params["filed_after"] = query.date_from.isoformat()
            
            if query.date_to:
                params["filed_before"] = query.date_to.isoformat()
            
            # Limit results
            params["per_page"] = min(query.max_results, 100)
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"CourtListener opinions search failed: {response.status}")
                    return []
                
                data = await response.json()
                results = data.get("results", [])
                
                # Convert to unified documents
                documents = []
                for item in results:
                    doc = await self._parse_opinion_result(item)
                    if doc:
                        documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"CourtListener opinions search error: {str(e)}")
            return []
    
    async def _search_dockets(
        self,
        search_params: Dict[str, Any],
        query: UnifiedQuery
    ) -> List[UnifiedDocument]:
        """Search dockets endpoint"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/search/"
            
            params = {
                "q": query.query_text,
                "type": "r",  # dockets (RECAP)
                "format": "json",
                "order_by": "score desc" if query.sort_by == "relevance" else "dateFiled desc"
            }
            
            # Add filters
            if query.courts:
                params["court"] = ",".join(query.courts)
            
            if query.date_from:
                params["filed_after"] = query.date_from.isoformat()
            
            if query.date_to:
                params["filed_before"] = query.date_to.isoformat()
            
            params["per_page"] = min(query.max_results, 100)
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                results = data.get("results", [])
                
                documents = []
                for item in results:
                    doc = await self._parse_docket_result(item)
                    if doc:
                        documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"CourtListener dockets search error: {str(e)}")
            return []
    
    async def _search_oral_arguments(
        self,
        search_params: Dict[str, Any],
        query: UnifiedQuery
    ) -> List[UnifiedDocument]:
        """Search oral arguments"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/search/"
            
            params = {
                "q": query.query_text,
                "type": "oa",  # oral arguments
                "format": "json",
                "order_by": "score desc" if query.sort_by == "relevance" else "dateArgued desc"
            }
            
            if query.courts:
                params["court"] = ",".join(query.courts)
            
            params["per_page"] = min(query.max_results, 50)
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                results = data.get("results", [])
                
                documents = []
                for item in results:
                    doc = await self._parse_oral_argument_result(item)
                    if doc:
                        documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"CourtListener oral arguments search error: {str(e)}")
            return []
    
    async def _get_opinion(self, opinion_id: str) -> Optional[UnifiedDocument]:
        """Get specific opinion by ID"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/opinions/{opinion_id}/"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                return await self._parse_opinion_result(data)
                
        except Exception as e:
            logger.error(f"Opinion retrieval error: {str(e)}")
            return None
    
    async def _get_docket(self, docket_id: str) -> Optional[UnifiedDocument]:
        """Get specific docket by ID"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.base_url}/dockets/{docket_id}/"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                return await self._parse_docket_result(data)
                
        except Exception as e:
            logger.error(f"Docket retrieval error: {str(e)}")
            return None
    
    async def _parse_opinion_result(self, item: Dict[str, Any]) -> Optional[UnifiedDocument]:
        """Parse CourtListener opinion result"""
        try:
            # Extract basic information
            title = item.get("caseName", "")
            if not title:
                title = item.get("cluster", {}).get("caseName", "Untitled Opinion")
            
            # Create unified document
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.COURTLISTENER,
                source_document_id=str(item.get("id", "")),
                source_url=item.get("absolute_url", ""),
                title=title,
                document_type=ContentType.CASES,
                citation=item.get("citation", {}).get("neutral", ""),
                full_text=item.get("plain_text", ""),
                summary=item.get("summary", ""),
                court=item.get("court", {}).get("full_name", "") if isinstance(item.get("court"), dict) else str(item.get("court", "")),
                jurisdiction=self._map_court_to_jurisdiction(item.get("court", {})),
                judges=self._extract_judges(item),
                decision_date=self._parse_date(item.get("dateFiled")),
                filing_date=self._parse_date(item.get("dateCreated")),
                legal_topics=item.get("topics", []),
                is_free_access=True,
                full_text_available=bool(item.get("plain_text")),
                provider_metadata=item
            )
            
            # Extract additional citation information
            cluster_info = item.get("cluster", {})
            if cluster_info:
                if not doc.citation and cluster_info.get("citation"):
                    doc.citation = cluster_info["citation"]
                
                if cluster_info.get("dateDecided"):
                    doc.decision_date = self._parse_date(cluster_info["dateDecided"])
                
                # Extract parallel citations
                citations = cluster_info.get("citations", [])
                for citation in citations:
                    cite_type = citation.get("type")
                    if cite_type == "federal":
                        doc.citation = citation.get("cite", doc.citation)
            
            # Calculate relevance and authority scores
            doc.relevance_score = item.get("score", 0.0)
            doc.authority_score = self._calculate_authority_score(item)
            doc.recency_score = self._calculate_recency_score(doc.decision_date)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing opinion result: {str(e)}")
            return None
    
    async def _parse_docket_result(self, item: Dict[str, Any]) -> Optional[UnifiedDocument]:
        """Parse CourtListener docket result"""
        try:
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.COURTLISTENER,
                source_document_id=str(item.get("id", "")),
                source_url=item.get("absolute_url", ""),
                title=item.get("caseName", "Docket Entry"),
                document_type=ContentType.DOCKETS,
                docket_number=item.get("docket_number", ""),
                court=item.get("court", {}).get("full_name", "") if isinstance(item.get("court"), dict) else str(item.get("court", "")),
                jurisdiction=self._map_court_to_jurisdiction(item.get("court", {})),
                filing_date=self._parse_date(item.get("date_created")),
                parties=self._extract_parties(item),
                is_free_access=True,
                full_text_available=False,
                provider_metadata=item
            )
            
            doc.relevance_score = item.get("score", 0.0)
            doc.authority_score = 0.5  # Dockets have moderate authority
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing docket result: {str(e)}")
            return None
    
    async def _parse_oral_argument_result(self, item: Dict[str, Any]) -> Optional[UnifiedDocument]:
        """Parse CourtListener oral argument result"""
        try:
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.COURTLISTENER,
                source_document_id=str(item.get("id", "")),
                source_url=item.get("absolute_url", ""),
                title=item.get("case_name", "Oral Argument"),
                document_type=ContentType.ORAL_ARGUMENTS,
                court=item.get("panel", {}).get("court", {}).get("full_name", "") if item.get("panel") else "",
                jurisdiction=self._map_court_to_jurisdiction(item.get("panel", {}).get("court", {}) if item.get("panel") else {}),
                decision_date=self._parse_date(item.get("date_argued")),
                is_free_access=True,
                full_text_available=bool(item.get("download_url")),
                provider_metadata=item
            )
            
            doc.relevance_score = item.get("score", 0.0)
            doc.authority_score = 0.7  # Oral arguments have good authority value
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing oral argument result: {str(e)}")
            return None
    
    def _extract_judges(self, item: Dict[str, Any]) -> List[str]:
        """Extract judge names from opinion data"""
        judges = []
        
        try:
            # Try to get judges from author field
            author = item.get("author")
            if author:
                if isinstance(author, dict):
                    judge_name = author.get("name_full", "")
                    if judge_name:
                        judges.append(judge_name)
                else:
                    judges.append(str(author))
            
            # Try to get judges from cluster panel
            cluster = item.get("cluster", {})
            if cluster:
                panel = cluster.get("panel", [])
                for judge in panel:
                    if isinstance(judge, dict):
                        judge_name = judge.get("name_full", "")
                        if judge_name and judge_name not in judges:
                            judges.append(judge_name)
                    elif isinstance(judge, str) and judge not in judges:
                        judges.append(judge)
        
        except Exception as e:
            logger.error(f"Error extracting judges: {str(e)}")
        
        return judges
    
    def _extract_parties(self, item: Dict[str, Any]) -> List[str]:
        """Extract party names from docket data"""
        parties = []
        
        try:
            case_name = item.get("caseName", "")
            if " v. " in case_name:
                party_parts = case_name.split(" v. ", 1)
                parties.extend([p.strip() for p in party_parts])
            elif case_name:
                parties.append(case_name)
        
        except Exception as e:
            logger.error(f"Error extracting parties: {str(e)}")
        
        return parties
    
    def _map_court_to_jurisdiction(self, court_info: Dict[str, Any]) -> str:
        """Map court information to jurisdiction"""
        if not isinstance(court_info, dict):
            return "Unknown"
        
        court_id = court_info.get("id", "")
        
        # Federal courts
        if court_id in ["scotus", "cafc", "ca1", "ca2", "ca3", "ca4", "ca5", "ca6", "ca7", "ca8", "ca9", "ca10", "ca11", "cadc"]:
            return "Federal"
        
        # Try to extract from jurisdiction field
        jurisdiction = court_info.get("jurisdiction", "")
        if jurisdiction:
            jurisdiction_map = {
                "F": "Federal",
                "FD": "Federal", 
                "FB": "Federal",
                "FS": "Federal"
            }
            return jurisdiction_map.get(jurisdiction, jurisdiction)
        
        return "Unknown"
    
    def _calculate_authority_score(self, item: Dict[str, Any]) -> float:
        """Calculate authority score based on court level and citations"""
        try:
            court_info = item.get("court", {})
            if not isinstance(court_info, dict):
                return 0.5
            
            court_id = court_info.get("id", "")
            
            # Supreme Court
            if court_id == "scotus":
                return 1.0
            
            # Circuit Courts
            if court_id.startswith("ca") or court_id in ["cafc", "cadc"]:
                return 0.8
            
            # District Courts
            if court_id.startswith("ca") or "district" in court_info.get("full_name", "").lower():
                return 0.6
            
            # State Supreme Courts
            if "supreme" in court_info.get("full_name", "").lower():
                return 0.7
            
            # Default
            return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating authority score: {str(e)}")
            return 0.5
    
    def _calculate_recency_score(self, decision_date: Optional[date]) -> float:
        """Calculate recency score based on decision date"""
        if not decision_date:
            return 0.0
        
        try:
            today = date.today()
            days_old = (today - decision_date).days
            
            # Score decreases with age
            if days_old <= 365:  # Less than 1 year
                return 1.0
            elif days_old <= 1825:  # Less than 5 years
                return 0.8
            elif days_old <= 3650:  # Less than 10 years
                return 0.6
            elif days_old <= 7300:  # Less than 20 years
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating recency score: {str(e)}")
            return 0.0
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Handle various date formats
            if "T" in date_str:  # ISO format with time
                return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            else:  # Date only
                return datetime.fromisoformat(date_str).date()
        except:
            return None
    
    async def _build_search_params(self, query: UnifiedQuery) -> Dict[str, Any]:
        """Build search parameters for CourtListener API"""
        params = {
            "query": query.query_text,
            "max_results": query.max_results
        }
        
        # Add content type filters
        if query.content_types:
            content_mapping = {
                ContentType.CASES: "opinions",
                ContentType.DOCKETS: "dockets", 
                ContentType.ORAL_ARGUMENTS: "oral_arguments"
            }
            
            types = []
            for content_type in query.content_types:
                if content_type in content_mapping:
                    types.append(content_mapping[content_type])
            
            if types:
                params["types"] = types
        
        return params
    
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
                logger.info(f"CourtListener rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(now)