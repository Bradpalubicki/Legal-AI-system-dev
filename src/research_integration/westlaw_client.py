"""
Westlaw API Client

Comprehensive client for Westlaw Edge API integration including search,
document retrieval, KeyCite analysis, and authentication management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from pydantic import BaseModel

from .models import (
    ResearchQuery, SearchResult, LegalDocument, Citation,
    DocumentType, JurisdictionLevel, CourtLevel, ResearchProvider,
    CitationValidationResult, APIUsageMetrics
)

logger = logging.getLogger(__name__)


class WestlawCredentials(BaseModel):
    """Westlaw API credentials"""
    client_id: str
    client_secret: str
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    tenant_id: Optional[str] = None


class WestlawAuthToken(BaseModel):
    """Westlaw authentication token"""
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    refresh_token: Optional[str] = None
    scope: List[str] = []


class WestlawKeyNumbers(BaseModel):
    """Westlaw Key Number system integration"""
    key_number: str
    topic: str
    subtopic: str
    description: str
    related_cases: int = 0


class KeyCiteResult(BaseModel):
    """KeyCite analysis result"""
    citation: str
    keycite_flag: str  # red, yellow, green
    treatment_status: str
    citing_references: int
    negative_treatment: bool
    overruled: bool
    questioned: bool
    warned: bool
    distinguished: bool
    limited: bool
    superseded: bool
    
    # Citing References Breakdown
    cases_citing: int = 0
    secondary_sources: int = 0
    statutes_citing: int = 0
    regulations_citing: int = 0
    
    # History Analysis
    direct_history: List[Dict] = []
    negative_citing_refs: List[Dict] = []
    
    # Depth of Treatment
    most_cited_by: List[Dict] = []
    most_recent_citations: List[Dict] = []


class WestlawClient:
    """
    Comprehensive Westlaw Edge API client with advanced search capabilities,
    KeyCite integration, and authentication management.
    """
    
    def __init__(self, credentials: WestlawCredentials):
        self.credentials = credentials
        self.auth_token: Optional[WestlawAuthToken] = None
        self.base_url = "https://api.westlaw.com"
        self.session: Optional[ClientSession] = None
        
        # Rate limiting
        self.rate_limit = 100  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.request_timestamps: List[datetime] = []
        
        # Usage tracking
        self.usage_metrics = APIUsageMetrics(
            provider=ResearchProvider.WESTLAW,
            user_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set per user
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow()
        )
        
        logger.info("Westlaw client initialized")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize HTTP session and authenticate"""
        timeout = ClientTimeout(total=30, connect=10)
        self.session = ClientSession(timeout=timeout)
        await self.authenticate()
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authenticate with Westlaw API"""
        try:
            auth_url = f"{self.base_url}/oauth/token"
            
            # Prepare authentication payload
            if self.credentials.username and self.credentials.password:
                # Password grant
                payload = {
                    "grant_type": "password",
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret,
                    "username": self.credentials.username,
                    "password": self.credentials.password,
                    "scope": "search documents keycite headnotes"
                }
            else:
                # Client credentials grant
                payload = {
                    "grant_type": "client_credentials",
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret,
                    "scope": "search documents keycite"
                }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            async with self.session.post(auth_url, data=payload, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    self.auth_token = WestlawAuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_at=expires_at,
                        refresh_token=token_data.get("refresh_token"),
                        scope=token_data.get("scope", "").split()
                    )
                    
                    logger.info("Successfully authenticated with Westlaw API")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Westlaw authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Westlaw authentication error: {str(e)}")
            return False
    
    async def refresh_token(self) -> bool:
        """Refresh authentication token if possible"""
        if not self.auth_token or not self.auth_token.refresh_token:
            return await self.authenticate()
        
        try:
            auth_url = f"{self.base_url}/oauth/token"
            payload = {
                "grant_type": "refresh_token",
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "refresh_token": self.auth_token.refresh_token
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            async with self.session.post(auth_url, data=payload, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    self.auth_token.access_token = token_data["access_token"]
                    self.auth_token.expires_at = expires_at
                    if "refresh_token" in token_data:
                        self.auth_token.refresh_token = token_data["refresh_token"]
                    
                    logger.info("Successfully refreshed Westlaw token")
                    return True
                else:
                    logger.error(f"Token refresh failed: {response.status}")
                    return await self.authenticate()
                    
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return await self.authenticate()
    
    async def ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token"""
        if not self.auth_token:
            return await self.authenticate()
        
        # Check if token is expired or expires soon (5 minutes buffer)
        if self.auth_token.expires_at <= datetime.utcnow() + timedelta(minutes=5):
            return await self.refresh_token()
        
        return True
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Tuple[int, Dict]:
        """Make authenticated API request with rate limiting"""
        
        # Ensure authentication
        if not await self.ensure_authenticated():
            raise Exception("Failed to authenticate with Westlaw API")
        
        # Rate limiting check
        await self._check_rate_limit()
        
        # Prepare headers
        request_headers = {
            "Authorization": f"{self.auth_token.token_type} {self.auth_token.access_token}",
            "Accept": "application/json",
            "User-Agent": "LegalAI-ResearchSystem/1.0"
        }
        if headers:
            request_headers.update(headers)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = datetime.utcnow()
            
            if method.upper() == "GET":
                async with self.session.get(url, params=params, headers=request_headers) as response:
                    status = response.status
                    result = await response.json() if response.content_type == 'application/json' else await response.text()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, params=params, headers=request_headers) as response:
                    status = response.status
                    result = await response.json() if response.content_type == 'application/json' else await response.text()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Track performance
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_usage_metrics(response_time, status == 200)
            
            return status, result
            
        except Exception as e:
            logger.error(f"Westlaw API request failed: {str(e)}")
            raise
    
    async def search(self, query: ResearchQuery) -> SearchResult:
        """Perform comprehensive legal research search"""
        try:
            logger.info(f"Executing Westlaw search: {query.query_text[:100]}...")
            
            # Build search parameters
            search_params = await self._build_search_params(query)
            
            # Execute search
            status, response_data = await self._make_request(
                "GET", "/v1/search", params=search_params
            )
            
            if status != 200:
                raise Exception(f"Search failed with status {status}: {response_data}")
            
            # Parse search results
            search_result = await self._parse_search_results(response_data, query)
            
            logger.info(f"Westlaw search completed: {search_result.results_returned} results")
            return search_result
            
        except Exception as e:
            logger.error(f"Westlaw search error: {str(e)}")
            raise
    
    async def get_document(self, document_id: str, include_full_text: bool = True) -> LegalDocument:
        """Retrieve full legal document by ID"""
        try:
            params = {
                "id": document_id,
                "includeFullText": include_full_text,
                "includeMetadata": True,
                "includeCitations": True
            }
            
            status, doc_data = await self._make_request(
                "GET", "/v1/documents", params=params
            )
            
            if status != 200:
                raise Exception(f"Document retrieval failed: {status}")
            
            document = await self._parse_document(doc_data)
            
            logger.info(f"Retrieved Westlaw document: {document.title}")
            return document
            
        except Exception as e:
            logger.error(f"Document retrieval error: {str(e)}")
            raise
    
    async def keycite_analysis(self, citation: str) -> KeyCiteResult:
        """Perform KeyCite citation analysis"""
        try:
            logger.info(f"Running KeyCite analysis for: {citation}")
            
            params = {
                "citation": citation,
                "includeHistory": True,
                "includeTreatment": True,
                "includeNegativeTreatment": True,
                "maxCitingReferences": 100
            }
            
            status, keycite_data = await self._make_request(
                "GET", "/v1/keycite", params=params
            )
            
            if status != 200:
                raise Exception(f"KeyCite analysis failed: {status}")
            
            result = await self._parse_keycite_result(keycite_data)
            
            logger.info(f"KeyCite analysis completed for {citation}")
            return result
            
        except Exception as e:
            logger.error(f"KeyCite analysis error: {str(e)}")
            raise
    
    async def validate_citation(self, citation: str) -> CitationValidationResult:
        """Validate and normalize legal citation"""
        try:
            params = {
                "citation": citation,
                "normalize": True,
                "includeBluebook": True,
                "includeParallels": True
            }
            
            status, validation_data = await self._make_request(
                "GET", "/v1/citations/validate", params=params
            )
            
            if status == 200:
                return await self._parse_citation_validation(validation_data, citation)
            else:
                # Citation not found or invalid
                return CitationValidationResult(
                    original_citation=citation,
                    is_valid=False,
                    confidence_score=0.0,
                    validation_method="westlaw_api",
                    errors=[f"Citation validation failed: {validation_data}"],
                    validation_source=ResearchProvider.WESTLAW
                )
                
        except Exception as e:
            logger.error(f"Citation validation error: {str(e)}")
            return CitationValidationResult(
                original_citation=citation,
                is_valid=False,
                confidence_score=0.0,
                validation_method="westlaw_api",
                errors=[f"Validation error: {str(e)}"],
                validation_source=ResearchProvider.WESTLAW
            )
    
    async def get_key_numbers(self, topic: Optional[str] = None) -> List[WestlawKeyNumbers]:
        """Get West Key Number system information"""
        try:
            params = {}
            if topic:
                params["topic"] = topic
            
            status, key_data = await self._make_request(
                "GET", "/v1/keynumbers", params=params
            )
            
            if status != 200:
                raise Exception(f"Key Numbers retrieval failed: {status}")
            
            key_numbers = []
            for item in key_data.get("keyNumbers", []):
                key_numbers.append(WestlawKeyNumbers(
                    key_number=item.get("keyNumber", ""),
                    topic=item.get("topic", ""),
                    subtopic=item.get("subtopic", ""),
                    description=item.get("description", ""),
                    related_cases=item.get("relatedCasesCount", 0)
                ))
            
            return key_numbers
            
        except Exception as e:
            logger.error(f"Key Numbers retrieval error: {str(e)}")
            return []
    
    async def search_by_key_number(self, key_number: str, jurisdiction: Optional[str] = None) -> SearchResult:
        """Search cases by West Key Number"""
        try:
            # Create specialized query for key number search
            query = ResearchQuery(
                query_text=f"key({key_number})",
                search_type="headnote",
                document_types=[DocumentType.CASE],
                max_results=100
            )
            
            if jurisdiction:
                query.jurisdictions = [jurisdiction]
            
            return await self.search(query)
            
        except Exception as e:
            logger.error(f"Key Number search error: {str(e)}")
            raise
    
    async def _build_search_params(self, query: ResearchQuery) -> Dict[str, Any]:
        """Build Westlaw API search parameters"""
        params = {
            "query": query.query_text,
            "maxResults": min(query.max_results, 200),  # Westlaw limit
            "sortBy": query.sort_by,
            "includeMetadata": True
        }
        
        # Document type filters
        if query.document_types:
            content_types = []
            for doc_type in query.document_types:
                if doc_type == DocumentType.CASE:
                    content_types.append("cases")
                elif doc_type == DocumentType.STATUTE:
                    content_types.append("statutes")
                elif doc_type == DocumentType.REGULATION:
                    content_types.append("regulations")
                elif doc_type == DocumentType.SECONDARY:
                    content_types.extend(["law-reviews", "treatises", "practice-materials"])
            
            if content_types:
                params["contentType"] = ",".join(content_types)
        
        # Jurisdiction filters
        if query.jurisdictions:
            params["jurisdiction"] = ",".join(query.jurisdictions)
        
        # Date filters
        if query.date_from:
            params["dateFrom"] = query.date_from.isoformat()
        if query.date_to:
            params["dateTo"] = query.date_to.isoformat()
        
        # Advanced search options
        if query.terms_and_connectors:
            params["queryType"] = "boolean"
        else:
            params["queryType"] = "natural"
        
        if not query.include_unpublished:
            params["publishedOnly"] = True
        
        # Field restrictions
        if query.field_restrictions:
            for field, value in query.field_restrictions.items():
                if field == "court":
                    params["court"] = value
                elif field == "judge":
                    params["judge"] = value
                elif field == "attorney":
                    params["attorney"] = value
        
        return params
    
    async def _parse_search_results(self, response_data: Dict, query: ResearchQuery) -> SearchResult:
        """Parse Westlaw search results into standard format"""
        documents = []
        
        for item in response_data.get("results", []):
            try:
                document = await self._parse_search_result_item(item)
                documents.append(document)
            except Exception as e:
                logger.warning(f"Failed to parse search result item: {str(e)}")
                continue
        
        # Extract metadata
        total_results = response_data.get("totalResults", len(documents))
        search_time = response_data.get("searchTimeMs", 0)
        
        # Build facets
        facets = response_data.get("facets", {})
        
        return SearchResult(
            query=query,
            documents=documents,
            total_results=total_results,
            results_returned=len(documents),
            westlaw_results=len(documents),
            lexisnexis_results=0,
            search_time_ms=search_time,
            providers_searched=[ResearchProvider.WESTLAW],
            search_strategy="westlaw_api",
            jurisdiction_facets=facets.get("jurisdiction", {}),
            court_facets=facets.get("court", {}),
            date_facets=facets.get("date", {}),
            document_type_facets=facets.get("contentType", {}),
            has_more_results=total_results > len(documents)
        )
    
    async def _parse_search_result_item(self, item: Dict) -> LegalDocument:
        """Parse individual search result item"""
        # Extract citation information
        citation_text = item.get("citation", "")
        citation = Citation(
            raw_citation=citation_text,
            normalized_citation=item.get("normalizedCitation", citation_text),
            document_type=self._map_document_type(item.get("contentType", "")),
            jurisdiction_level=self._map_jurisdiction_level(item.get("jurisdiction", "")),
            provider=ResearchProvider.WESTLAW,
            provider_document_id=item.get("id", ""),
            westlaw_key=item.get("westlawKey", "")
        )
        
        # Parse case name and year from citation
        if citation_text:
            citation.case_name = item.get("title", "")
            if "year" in item:
                citation.year = int(item["year"])
        
        # Create document
        document = LegalDocument(
            provider_id=item.get("id", ""),
            provider=ResearchProvider.WESTLAW,
            title=item.get("title", ""),
            document_type=self._map_document_type(item.get("contentType", "")),
            citation=citation,
            summary=item.get("summary", ""),
            headnotes=item.get("headnotes", []),
            court=item.get("court", ""),
            jurisdiction=item.get("jurisdiction", ""),
            jurisdiction_level=self._map_jurisdiction_level(item.get("jurisdiction", "")),
            court_level=self._map_court_level(item.get("courtLevel", "")),
            topics=item.get("topics", []),
            key_numbers=item.get("keyNumbers", []),
            practice_areas=item.get("practiceAreas", []),
            relevance_score=item.get("relevanceScore", 0.0),
            provider_metadata=item
        )
        
        # Parse dates
        if "decisionDate" in item:
            try:
                document.decision_date = datetime.fromisoformat(item["decisionDate"]).date()
            except:
                pass
        
        if "filingDate" in item:
            try:
                document.filing_date = datetime.fromisoformat(item["filingDate"]).date()
            except:
                pass
        
        return document
    
    async def _parse_document(self, doc_data: Dict) -> LegalDocument:
        """Parse full document data"""
        # This would be similar to _parse_search_result_item but with more detail
        # Including full text, complete citation analysis, etc.
        return await self._parse_search_result_item(doc_data)
    
    async def _parse_keycite_result(self, keycite_data: Dict) -> KeyCiteResult:
        """Parse KeyCite analysis results"""
        return KeyCiteResult(
            citation=keycite_data.get("citation", ""),
            keycite_flag=keycite_data.get("flag", "green"),
            treatment_status=keycite_data.get("treatmentStatus", "Good Law"),
            citing_references=keycite_data.get("citingReferencesCount", 0),
            negative_treatment=keycite_data.get("hasNegativeTreatment", False),
            overruled=keycite_data.get("isOverruled", False),
            questioned=keycite_data.get("isQuestioned", False),
            warned=keycite_data.get("isWarned", False),
            distinguished=keycite_data.get("isDistinguished", False),
            limited=keycite_data.get("isLimited", False),
            superseded=keycite_data.get("isSuperseded", False),
            cases_citing=keycite_data.get("casesCiting", 0),
            secondary_sources=keycite_data.get("secondarySourcesCiting", 0),
            statutes_citing=keycite_data.get("statutesCiting", 0),
            regulations_citing=keycite_data.get("regulationsCiting", 0),
            direct_history=keycite_data.get("directHistory", []),
            negative_citing_refs=keycite_data.get("negativeCitingReferences", []),
            most_cited_by=keycite_data.get("mostCitedBy", []),
            most_recent_citations=keycite_data.get("mostRecentCitations", [])
        )
    
    async def _parse_citation_validation(self, validation_data: Dict, original_citation: str) -> CitationValidationResult:
        """Parse citation validation results"""
        return CitationValidationResult(
            original_citation=original_citation,
            is_valid=validation_data.get("isValid", False),
            confidence_score=validation_data.get("confidence", 0.0),
            validation_method="westlaw_api",
            normalized_citation=validation_data.get("normalizedCitation"),
            bluebook_citation=validation_data.get("bluebookCitation"),
            parallel_citations=validation_data.get("parallelCitations", []),
            validation_source=ResearchProvider.WESTLAW
        )
    
    def _map_document_type(self, westlaw_type: str) -> DocumentType:
        """Map Westlaw content type to standard document type"""
        type_mapping = {
            "cases": DocumentType.CASE,
            "statutes": DocumentType.STATUTE,
            "regulations": DocumentType.REGULATION,
            "law-reviews": DocumentType.JOURNAL,
            "treatises": DocumentType.TREATISE,
            "practice-materials": DocumentType.SECONDARY,
            "forms": DocumentType.FORM,
            "news": DocumentType.NEWS
        }
        return type_mapping.get(westlaw_type.lower(), DocumentType.SECONDARY)
    
    def _map_jurisdiction_level(self, jurisdiction: str) -> JurisdictionLevel:
        """Map jurisdiction string to jurisdiction level"""
        if "federal" in jurisdiction.lower() or "u.s." in jurisdiction.lower():
            return JurisdictionLevel.FEDERAL
        elif any(state in jurisdiction.upper() for state in ["CA", "NY", "TX", "FL"]):
            return JurisdictionLevel.STATE
        else:
            return JurisdictionLevel.STATE  # Default assumption
    
    def _map_court_level(self, court_level: str) -> CourtLevel:
        """Map court level string to standard court level"""
        if "supreme" in court_level.lower():
            return CourtLevel.SUPREME
        elif "appellate" in court_level.lower() or "appeal" in court_level.lower():
            return CourtLevel.APPELLATE
        elif "trial" in court_level.lower() or "district" in court_level.lower():
            return CourtLevel.TRIAL
        else:
            return CourtLevel.TRIAL  # Default assumption
    
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
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request timestamp
        self.request_timestamps.append(now)
    
    def _update_usage_metrics(self, response_time_ms: float, success: bool):
        """Update API usage metrics"""
        self.usage_metrics.api_calls += 1
        
        # Update average response time
        current_avg = self.usage_metrics.average_response_time
        total_calls = self.usage_metrics.api_calls
        self.usage_metrics.average_response_time = (
            (current_avg * (total_calls - 1) + response_time_ms) / total_calls
        )
        
        # Update error rate
        if not success:
            error_count = self.usage_metrics.api_calls * self.usage_metrics.error_rate + 1
            self.usage_metrics.error_rate = error_count / total_calls
        else:
            error_count = self.usage_metrics.api_calls * self.usage_metrics.error_rate
            self.usage_metrics.error_rate = error_count / total_calls