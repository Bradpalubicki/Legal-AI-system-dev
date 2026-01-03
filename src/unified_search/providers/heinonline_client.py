"""
HeinOnline API Client

Premium legal database integration for comprehensive legal research including
law journals, treaties, legislative history, and historical legal documents.
"""

import asyncio
import logging
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from uuid import UUID
from urllib.parse import quote, urlencode

import aiohttp
from aiohttp import ClientSession, ClientTimeout, BasicAuth

from ..database_models import (
    DatabaseProvider, UnifiedQuery, UnifiedDocument, UnifiedSearchResult,
    ContentType, DatabaseCapability, AccessType
)

logger = logging.getLogger(__name__)


class HeinOnlineCredentials:
    """HeinOnline API credentials"""
    def __init__(
        self,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        institution_id: Optional[str] = None
    ):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.institution_id = institution_id


class HeinOnlineClient:
    """
    HeinOnline API client providing access to comprehensive legal research
    including law reviews, historical documents, treaties, and legislative materials.
    """
    
    def __init__(self, credentials: HeinOnlineCredentials):
        self.credentials = credentials
        self.base_url = "https://heinonline.org"
        self.api_base = f"{self.base_url}/HeinOnline/api/v1"
        self.session: Optional[ClientSession] = None
        
        # Rate limiting (HeinOnline has usage limits)
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
            DatabaseCapability.DOCUMENT_TYPE_FILTERING,
            DatabaseCapability.FULL_DOCUMENT_ACCESS,
            DatabaseCapability.API_ACCESS,
            DatabaseCapability.BULK_DOWNLOAD
        ]
        
        # HeinOnline-specific collections
        self.collections = {
            "law_reviews": "lawreviews",
            "cases": "cases", 
            "statutes": "statutes",
            "treaties": "treaties",
            "legislative_history": "legislative",
            "cfr": "cfr",
            "federal_register": "fedregister",
            "international": "international",
            "legal_classics": "classics"
        }
        
        logger.info("HeinOnline client initialized")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP session with authentication"""
        timeout = ClientTimeout(total=45, connect=15)
        headers = {
            "User-Agent": "LegalAI-UnifiedSearch/1.0 (Research Tool)",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Setup authentication
        auth = None
        if self.credentials.username and self.credentials.password:
            auth = BasicAuth(self.credentials.username, self.credentials.password)
        
        if self.credentials.api_key:
            headers["X-API-Key"] = self.credentials.api_key
        
        if self.credentials.institution_id:
            headers["X-Institution-ID"] = self.credentials.institution_id
        
        self.session = ClientSession(timeout=timeout, headers=headers, auth=auth)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: UnifiedQuery) -> UnifiedSearchResult:
        """Search HeinOnline database"""
        try:
            logger.info(f"Executing HeinOnline search: {query.query_text[:100]}...")
            
            # Execute searches across different collections
            search_results = []
            
            # Determine which collections to search based on content types
            collections_to_search = self._determine_collections(query.content_types)
            
            # Search each relevant collection
            for collection in collections_to_search:
                if len(search_results) >= query.max_results:
                    break
                
                try:
                    collection_results = await self._search_collection(query, collection)
                    search_results.extend(collection_results)
                except Exception as e:
                    logger.error(f"Error searching HeinOnline collection {collection}: {str(e)}")
                    continue
            
            # Limit to requested maximum
            search_results = search_results[:query.max_results]
            
            # Create unified result
            result = UnifiedSearchResult(
                query=query,
                total_results=len(search_results),
                results_returned=len(search_results),
                documents=search_results,
                provider_results={DatabaseProvider.HEINONLINE.value: len(search_results)},
                providers_searched=[DatabaseProvider.HEINONLINE],
                total_cost=self._calculate_search_cost(len(search_results)),
                cost_by_provider={DatabaseProvider.HEINONLINE.value: self._calculate_search_cost(len(search_results))}
            )
            
            logger.info(f"HeinOnline search completed: {len(search_results)} results")
            return result
            
        except Exception as e:
            logger.error(f"HeinOnline search failed: {str(e)}")
            return UnifiedSearchResult(
                query=query,
                providers_failed=[DatabaseProvider.HEINONLINE]
            )
    
    async def get_document(self, document_id: str) -> Optional[UnifiedDocument]:
        """Retrieve specific document by ID"""
        try:
            await self._check_rate_limit()
            
            # Parse document ID (should contain collection and document info)
            collection, doc_id = self._parse_document_id(document_id)
            
            url = f"{self.api_base}/collections/{collection}/documents/{doc_id}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                return await self._parse_document_data(data, collection)
                
        except Exception as e:
            logger.error(f"HeinOnline document retrieval failed: {str(e)}")
            return None
    
    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific collection"""
        try:
            await self._check_rate_limit()
            
            url = f"{self.api_base}/collections/{collection_name}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
        except Exception as e:
            logger.error(f"Collection info retrieval failed: {str(e)}")
            return None
    
    async def _search_collection(
        self,
        query: UnifiedQuery,
        collection: str
    ) -> List[UnifiedDocument]:
        """Search a specific HeinOnline collection"""
        try:
            await self._check_rate_limit()
            
            # Build search parameters
            search_params = {
                "q": query.query_text,
                "collection": collection,
                "format": "json",
                "limit": min(query.max_results, 50)  # HeinOnline typically limits per request
            }
            
            # Add filters
            if query.date_from:
                search_params["date_start"] = query.date_from.isoformat()
            if query.date_to:
                search_params["date_end"] = query.date_to.isoformat()
            
            # Sort preference
            if query.sort_by == "relevance":
                search_params["sort"] = "relevance"
            else:
                search_params["sort"] = "date"
            
            url = f"{self.api_base}/search"
            
            async with self.session.get(url, params=search_params) as response:
                if response.status != 200:
                    logger.error(f"HeinOnline collection search failed: {response.status}")
                    return []
                
                data = await response.json()
                
                # Parse results
                results = data.get("results", [])
                documents = []
                
                for item in results:
                    doc = await self._parse_search_result(item, collection)
                    if doc:
                        documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"HeinOnline collection search error: {str(e)}")
            return []
    
    async def _parse_search_result(self, item: Dict[str, Any], collection: str) -> Optional[UnifiedDocument]:
        """Parse HeinOnline search result"""
        try:
            # Extract basic information
            title = item.get("title", "")
            document_id = f"{collection}:{item.get('id', '')}"
            url = item.get("url", "")
            
            # Determine content type based on collection
            content_type = self._map_collection_to_content_type(collection)
            
            # Extract metadata
            authors = item.get("authors", [])
            if isinstance(authors, str):
                authors = [authors]
            
            publication_info = item.get("publication", {})
            journal = publication_info.get("name", "") if isinstance(publication_info, dict) else str(publication_info)
            
            # Extract dates
            pub_date = self._parse_date(item.get("date") or item.get("publication_date"))
            
            # Extract citation
            citation = item.get("citation", "")
            
            # Extract summary/abstract
            summary = item.get("abstract", "") or item.get("summary", "")
            
            # Create unified document
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.HEINONLINE,
                source_document_id=document_id,
                source_url=url,
                title=title,
                document_type=content_type,
                citation=citation,
                summary=summary,
                authors=authors,
                publication_date=pub_date,
                legal_topics=item.get("subjects", []) or item.get("topics", []),
                is_free_access=False,  # HeinOnline is subscription-based
                full_text_available=item.get("full_text_available", True),
                provider_metadata={
                    "collection": collection,
                    "journal": journal,
                    "volume": item.get("volume"),
                    "issue": item.get("issue"),
                    "page_start": item.get("page_start"),
                    "page_end": item.get("page_end"),
                    "doi": item.get("doi"),
                    "issn": item.get("issn")
                }
            )
            
            # Calculate scores
            doc.relevance_score = item.get("relevance_score", 0.5)
            doc.authority_score = self._calculate_authority_score(collection, journal, authors)
            doc.recency_score = self._calculate_recency_score(pub_date)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing HeinOnline search result: {str(e)}")
            return None
    
    async def _parse_document_data(self, data: Dict[str, Any], collection: str) -> Optional[UnifiedDocument]:
        """Parse full document data"""
        try:
            title = data.get("title", "")
            document_id = f"{collection}:{data.get('id', '')}"
            url = data.get("url", "")
            
            content_type = self._map_collection_to_content_type(collection)
            
            # Extract full text if available
            full_text = data.get("full_text", "") or data.get("content", "")
            
            # Extract comprehensive metadata
            authors = data.get("authors", [])
            citation = data.get("citation", "")
            summary = data.get("abstract", "") or data.get("summary", "")
            
            pub_date = self._parse_date(data.get("date") or data.get("publication_date"))
            
            doc = UnifiedDocument(
                source_provider=DatabaseProvider.HEINONLINE,
                source_document_id=document_id,
                source_url=url,
                title=title,
                document_type=content_type,
                citation=citation,
                full_text=full_text,
                summary=summary,
                authors=authors,
                publication_date=pub_date,
                legal_topics=data.get("subjects", []) or data.get("topics", []),
                key_passages=data.get("key_excerpts", []),
                is_free_access=False,
                full_text_available=bool(full_text),
                provider_metadata=data
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing HeinOnline document data: {str(e)}")
            return None
    
    def _determine_collections(self, content_types: List[ContentType]) -> List[str]:
        """Determine which HeinOnline collections to search"""
        if not content_types:
            # Default collections for broad search
            return ["lawreviews", "cases", "statutes", "treaties"]
        
        collections = []
        
        for content_type in content_types:
            if content_type == ContentType.LAW_REVIEWS:
                collections.append("lawreviews")
            elif content_type == ContentType.CASES:
                collections.append("cases")
            elif content_type == ContentType.STATUTES:
                collections.append("statutes")
            elif content_type == ContentType.REGULATIONS:
                collections.append("cfr")
            elif content_type == ContentType.TREATIES:
                collections.append("treaties")
            elif content_type == ContentType.LEGISLATIVE_HISTORY:
                collections.append("legislative")
            elif content_type == ContentType.JOURNALS:
                collections.append("lawreviews")
        
        return collections or ["lawreviews", "cases"]  # Default fallback
    
    def _map_collection_to_content_type(self, collection: str) -> ContentType:
        """Map HeinOnline collection to content type"""
        mapping = {
            "lawreviews": ContentType.LAW_REVIEWS,
            "cases": ContentType.CASES,
            "statutes": ContentType.STATUTES,
            "cfr": ContentType.REGULATIONS,
            "treaties": ContentType.CONSTITUTIONS,  # Closest match
            "legislative": ContentType.LEGISLATIVE_HISTORY,
            "fedregister": ContentType.REGULATIONS,
            "international": ContentType.CASES,  # International cases
            "classics": ContentType.TREATISES
        }
        
        return mapping.get(collection, ContentType.JOURNALS)
    
    def _calculate_authority_score(
        self,
        collection: str,
        journal: str,
        authors: List[str]
    ) -> float:
        """Calculate authority score based on collection and source"""
        try:
            base_score = 0.7  # HeinOnline generally has high-quality content
            
            # Collection-based scoring
            if collection == "cases":
                base_score = 0.8
            elif collection == "lawreviews":
                # Law reviews vary in authority
                prestigious_indicators = [
                    "harvard", "yale", "stanford", "columbia", "chicago",
                    "nyu", "michigan", "virginia", "penn", "berkeley"
                ]
                if any(indicator in journal.lower() for indicator in prestigious_indicators):
                    base_score = 0.9
                else:
                    base_score = 0.7
            elif collection in ["statutes", "cfr", "treaties"]:
                base_score = 0.9  # Primary sources
            elif collection == "legislative":
                base_score = 0.8
            
            # Author count can indicate thoroughness
            if len(authors) > 1:
                base_score += 0.05
            
            return min(base_score, 1.0)
            
        except:
            return 0.7
    
    def _calculate_recency_score(self, publication_date: Optional[date]) -> float:
        """Calculate recency score"""
        if not publication_date:
            return 0.5
        
        try:
            today = date.today()
            years_old = (today - publication_date).days / 365.25
            
            if years_old <= 1:
                return 1.0
            elif years_old <= 3:
                return 0.9
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
    
    def _calculate_search_cost(self, num_results: int) -> float:
        """Calculate estimated cost for search (HeinOnline has usage-based pricing)"""
        # Simplified cost calculation - would need actual pricing model
        base_cost = 0.10  # Base search cost
        per_result_cost = 0.02  # Per result cost
        
        return base_cost + (num_results * per_result_cost)
    
    def _parse_document_id(self, document_id: str) -> tuple[str, str]:
        """Parse document ID to extract collection and document ID"""
        try:
            if ":" in document_id:
                collection, doc_id = document_id.split(":", 1)
                return collection, doc_id
            else:
                return "lawreviews", document_id  # Default collection
        except:
            return "lawreviews", document_id
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Handle various date formats
            if "T" in date_str:  # ISO format with time
                return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            elif "-" in date_str and len(date_str) == 10:  # YYYY-MM-DD
                return datetime.fromisoformat(date_str).date()
            elif "/" in date_str:  # MM/DD/YYYY or DD/MM/YYYY
                parts = date_str.split("/")
                if len(parts) == 3:
                    # Assume MM/DD/YYYY for US-based HeinOnline
                    return date(int(parts[2]), int(parts[0]), int(parts[1]))
            elif date_str.isdigit() and len(date_str) == 4:  # Just year
                return date(int(date_str), 1, 1)
        except:
            pass
        
        return None
    
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
                logger.info(f"HeinOnline rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(now)