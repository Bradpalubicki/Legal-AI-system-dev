"""
LexisNexis API Client

Comprehensive client for LexisNexis API integration including search,
document retrieval, Shepard's Citations analysis, and authentication management.
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


class LexisNexisCredentials(BaseModel):
    """LexisNexis API credentials"""
    client_id: str
    client_secret: str
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    subscription_id: Optional[str] = None


class LexisNexisAuthToken(BaseModel):
    """LexisNexis authentication token"""
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    refresh_token: Optional[str] = None
    scope: List[str] = []
    subscription_level: Optional[str] = None


class SherardsResult(BaseModel):
    """Shepard's Citations analysis result"""
    citation: str
    shepards_signal: str  # positive, negative, warning, neutral
    treatment_status: str
    citing_decisions: int
    citing_secondary: int
    citing_statutes: int
    
    # Treatment Analysis
    followed: bool = False
    distinguished: bool = False
    explained: bool = False
    criticized: bool = False
    questioned: bool = False
    overruled: bool = False
    superseded: bool = False
    
    # Analysis Categories
    positive_treatment: List[Dict] = []
    negative_treatment: List[Dict] = []
    neutral_treatment: List[Dict] = []
    warning_treatment: List[Dict] = []
    
    # Prior and Subsequent History
    prior_history: List[Dict] = []
    subsequent_history: List[Dict] = []
    
    # Commentary and Analysis
    law_review_citations: int = 0
    treatise_citations: int = 0
    encyclopedia_citations: int = 0


class LexisNexisHeadnote(BaseModel):
    """LexisNexis headnote structure"""
    headnote_number: str
    topic: str
    classification: str
    text: str
    legal_topic_hierarchy: List[str] = []
    more_like_this_count: int = 0


class LexisNexisClient:
    """
    Comprehensive LexisNexis API client with advanced search capabilities,
    Shepard's Citations integration, and authentication management.
    """
    
    def __init__(self, credentials: LexisNexisCredentials):
        self.credentials = credentials
        self.auth_token: Optional[LexisNexisAuthToken] = None
        self.base_url = "https://api.lexisnexis.com"
        self.session: Optional[ClientSession] = None
        
        # Rate limiting (more conservative for LexisNexis)
        self.rate_limit = 50  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.request_timestamps: List[datetime] = []
        
        # Usage tracking
        self.usage_metrics = APIUsageMetrics(
            provider=ResearchProvider.LEXISNEXIS,
            user_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set per user
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow()
        )
        
        logger.info("LexisNexis client initialized")
    
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
        """Authenticate with LexisNexis API"""
        try:
            auth_url = f"{self.base_url}/v1/oauth2/token"
            
            # LexisNexis typically uses client credentials flow
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "scope": "search documents shepards headnotes"
            }
            
            # If username/password provided, use resource owner password flow
            if self.credentials.username and self.credentials.password:
                payload.update({
                    "grant_type": "password",
                    "username": self.credentials.username,
                    "password": self.credentials.password
                })
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            async with self.session.post(auth_url, data=payload, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    self.auth_token = LexisNexisAuthToken(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_at=expires_at,
                        refresh_token=token_data.get("refresh_token"),
                        scope=token_data.get("scope", "").split(),
                        subscription_level=token_data.get("subscription_level")
                    )
                    
                    logger.info("Successfully authenticated with LexisNexis API")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"LexisNexis authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LexisNexis authentication error: {str(e)}")
            return False
    
    async def ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token"""
        if not self.auth_token:
            return await self.authenticate()
        
        # Check if token is expired or expires soon (5 minutes buffer)
        if self.auth_token.expires_at <= datetime.utcnow() + timedelta(minutes=5):
            return await self.authenticate()  # LexisNexis typically doesn't support refresh tokens
        
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
            raise Exception("Failed to authenticate with LexisNexis API")
        
        # Rate limiting check
        await self._check_rate_limit()
        
        # Prepare headers
        request_headers = {
            "Authorization": f"{self.auth_token.token_type} {self.auth_token.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
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
            logger.error(f"LexisNexis API request failed: {str(e)}")
            raise
    
    async def search(self, query: ResearchQuery) -> SearchResult:
        """Perform comprehensive legal research search"""
        try:
            logger.info(f"Executing LexisNexis search: {query.query_text[:100]}...")
            
            # Build search payload
            search_payload = await self._build_search_payload(query)
            
            # Execute search
            status, response_data = await self._make_request(
                "POST", "/v2/search", data=search_payload
            )
            
            if status != 200:
                raise Exception(f"Search failed with status {status}: {response_data}")
            
            # Parse search results
            search_result = await self._parse_search_results(response_data, query)
            
            logger.info(f"LexisNexis search completed: {search_result.results_returned} results")
            return search_result
            
        except Exception as e:
            logger.error(f"LexisNexis search error: {str(e)}")
            raise
    
    async def get_document(self, document_id: str, include_full_text: bool = True) -> LegalDocument:
        """Retrieve full legal document by ID"""
        try:
            params = {
                "documentId": document_id,
                "includeFullText": include_full_text,
                "includeMetadata": True,
                "includeCitations": True,
                "includeHeadnotes": True
            }
            
            status, doc_data = await self._make_request(
                "GET", "/v2/documents", params=params
            )
            
            if status != 200:
                raise Exception(f"Document retrieval failed: {status}")
            
            document = await self._parse_document(doc_data)
            
            logger.info(f"Retrieved LexisNexis document: {document.title}")
            return document
            
        except Exception as e:
            logger.error(f"Document retrieval error: {str(e)}")
            raise
    
    async def shepards_analysis(self, citation: str) -> SherardsResult:
        """Perform Shepard's Citations analysis"""
        try:
            logger.info(f"Running Shepard's analysis for: {citation}")
            
            payload = {
                "citation": citation,
                "analysisType": "FULL",
                "includePriorHistory": True,
                "includeSubsequentHistory": True,
                "includeTreatmentSummary": True,
                "maxCitingReferences": 100
            }
            
            status, shepards_data = await self._make_request(
                "POST", "/v2/shepards", data=payload
            )
            
            if status != 200:
                raise Exception(f"Shepard's analysis failed: {status}")
            
            result = await self._parse_shepards_result(shepards_data)
            
            logger.info(f"Shepard's analysis completed for {citation}")
            return result
            
        except Exception as e:
            logger.error(f"Shepard's analysis error: {str(e)}")
            raise
    
    async def validate_citation(self, citation: str) -> CitationValidationResult:
        """Validate and normalize legal citation"""
        try:
            payload = {
                "citation": citation,
                "normalize": True,
                "includeParallelCitations": True,
                "validateFormat": True
            }
            
            status, validation_data = await self._make_request(
                "POST", "/v2/citations/validate", data=payload
            )
            
            if status == 200:
                return await self._parse_citation_validation(validation_data, citation)
            else:
                # Citation not found or invalid
                return CitationValidationResult(
                    original_citation=citation,
                    is_valid=False,
                    confidence_score=0.0,
                    validation_method="lexisnexis_api",
                    errors=[f"Citation validation failed: {validation_data}"],
                    validation_source=ResearchProvider.LEXISNEXIS
                )
                
        except Exception as e:
            logger.error(f"Citation validation error: {str(e)}")
            return CitationValidationResult(
                original_citation=citation,
                is_valid=False,
                confidence_score=0.0,
                validation_method="lexisnexis_api",
                errors=[f"Validation error: {str(e)}"],
                validation_source=ResearchProvider.LEXISNEXIS
            )
    
    async def get_headnotes(self, document_id: str) -> List[LexisNexisHeadnote]:
        """Get headnotes for a specific document"""
        try:
            params = {"documentId": document_id}
            
            status, headnote_data = await self._make_request(
                "GET", "/v2/headnotes", params=params
            )
            
            if status != 200:
                raise Exception(f"Headnotes retrieval failed: {status}")
            
            headnotes = []
            for item in headnote_data.get("headnotes", []):
                headnotes.append(LexisNexisHeadnote(
                    headnote_number=item.get("number", ""),
                    topic=item.get("topic", ""),
                    classification=item.get("classification", ""),
                    text=item.get("text", ""),
                    legal_topic_hierarchy=item.get("topicHierarchy", []),
                    more_like_this_count=item.get("moreLikeThisCount", 0)
                ))
            
            return headnotes
            
        except Exception as e:
            logger.error(f"Headnotes retrieval error: {str(e)}")
            return []
    
    async def search_by_topic(self, topic: str, jurisdiction: Optional[str] = None) -> SearchResult:
        """Search documents by legal topic"""
        try:
            # Create specialized query for topic search
            query = ResearchQuery(
                query_text=f"TOPIC({topic})",
                search_type="boolean",
                document_types=[DocumentType.CASE],
                max_results=100,
                terms_and_connectors=True
            )
            
            if jurisdiction:
                query.jurisdictions = [jurisdiction]
            
            return await self.search(query)
            
        except Exception as e:
            logger.error(f"Topic search error: {str(e)}")
            raise
    
    async def search_law_reviews(self, query_text: str, max_results: int = 50) -> SearchResult:
        """Search law reviews and journals"""
        try:
            query = ResearchQuery(
                query_text=query_text,
                document_types=[DocumentType.JOURNAL],
                max_results=max_results,
                include_secondary=True
            )
            
            return await self.search(query)
            
        except Exception as e:
            logger.error(f"Law review search error: {str(e)}")
            raise
    
    async def get_practice_area_documents(
        self,
        practice_area: str,
        document_type: DocumentType = DocumentType.SECONDARY
    ) -> SearchResult:
        """Get documents for specific practice area"""
        try:
            query = ResearchQuery(
                query_text=f"PRACTICE-AREA({practice_area})",
                search_type="boolean",
                document_types=[document_type],
                practice_area=practice_area,
                terms_and_connectors=True,
                max_results=100
            )
            
            return await self.search(query)
            
        except Exception as e:
            logger.error(f"Practice area search error: {str(e)}")
            raise
    
    async def _build_search_payload(self, query: ResearchQuery) -> Dict[str, Any]:
        """Build LexisNexis API search payload"""
        payload = {
            "query": query.query_text,
            "searchOptions": {
                "maxResults": min(query.max_results, 100),  # LexisNexis limit per request
                "sortBy": query.sort_by,
                "includeMetadata": True,
                "includeSnippets": True
            }
        }
        
        # Content filters
        content_filters = {}
        
        # Document type filters
        if query.document_types:
            source_types = []
            for doc_type in query.document_types:
                if doc_type == DocumentType.CASE:
                    source_types.append("cases")
                elif doc_type == DocumentType.STATUTE:
                    source_types.append("statutes")
                elif doc_type == DocumentType.REGULATION:
                    source_types.append("regulations")
                elif doc_type == DocumentType.JOURNAL:
                    source_types.append("law-reviews")
                elif doc_type == DocumentType.TREATISE:
                    source_types.append("treatises")
                elif doc_type == DocumentType.SECONDARY:
                    source_types.extend(["secondary", "practice-materials"])
                elif doc_type == DocumentType.NEWS:
                    source_types.append("news")
            
            if source_types:
                content_filters["sourceType"] = source_types
        
        # Jurisdiction filters
        if query.jurisdictions:
            content_filters["jurisdiction"] = query.jurisdictions
        
        # Date filters
        date_filter = {}
        if query.date_from:
            date_filter["from"] = query.date_from.isoformat()
        if query.date_to:
            date_filter["to"] = query.date_to.isoformat()
        if date_filter:
            content_filters["dateRange"] = date_filter
        
        # Court level filters
        if query.court_levels:
            court_levels = [level.value for level in query.court_levels]
            content_filters["courtLevel"] = court_levels
        
        # Publication status
        if not query.include_unpublished:
            content_filters["publicationStatus"] = ["published"]
        
        if content_filters:
            payload["contentFilters"] = content_filters
        
        # Search type specific options
        if query.search_type == "boolean" or query.terms_and_connectors:
            payload["searchOptions"]["queryType"] = "boolean"
        else:
            payload["searchOptions"]["queryType"] = "natural"
        
        # Practice area
        if query.practice_area:
            payload["practiceArea"] = query.practice_area
        
        return payload
    
    async def _parse_search_results(self, response_data: Dict, query: ResearchQuery) -> SearchResult:
        """Parse LexisNexis search results into standard format"""
        documents = []
        
        results_list = response_data.get("results", [])
        for item in results_list:
            try:
                document = await self._parse_search_result_item(item)
                documents.append(document)
            except Exception as e:
                logger.warning(f"Failed to parse search result item: {str(e)}")
                continue
        
        # Extract metadata
        metadata = response_data.get("metadata", {})
        total_results = metadata.get("totalResults", len(documents))
        search_time = metadata.get("searchTimeMs", 0)
        
        # Build facets
        facets = response_data.get("facets", {})
        
        return SearchResult(
            query=query,
            documents=documents,
            total_results=total_results,
            results_returned=len(documents),
            westlaw_results=0,
            lexisnexis_results=len(documents),
            search_time_ms=search_time,
            providers_searched=[ResearchProvider.LEXISNEXIS],
            search_strategy="lexisnexis_api",
            jurisdiction_facets=facets.get("jurisdiction", {}),
            court_facets=facets.get("court", {}),
            date_facets=facets.get("date", {}),
            document_type_facets=facets.get("sourceType", {}),
            has_more_results=total_results > len(documents)
        )
    
    async def _parse_search_result_item(self, item: Dict) -> LegalDocument:
        """Parse individual search result item"""
        # Extract citation information
        citation_text = item.get("citation", "")
        citation = Citation(
            raw_citation=citation_text,
            normalized_citation=item.get("normalizedCitation", citation_text),
            document_type=self._map_document_type(item.get("sourceType", "")),
            jurisdiction_level=self._map_jurisdiction_level(item.get("jurisdiction", "")),
            provider=ResearchProvider.LEXISNEXIS,
            provider_document_id=item.get("documentId", ""),
            lexis_shepards=item.get("shepardsId", "")
        )
        
        # Parse citation components
        citation_parts = item.get("citationParts", {})
        if citation_parts:
            citation.case_name = citation_parts.get("caseName", "")
            citation.volume = citation_parts.get("volume", "")
            citation.reporter = citation_parts.get("reporter", "")
            citation.page = citation_parts.get("page", "")
            citation.court = citation_parts.get("court", "")
            if "year" in citation_parts:
                citation.year = int(citation_parts["year"])
        
        # Create document
        document = LegalDocument(
            provider_id=item.get("documentId", ""),
            provider=ResearchProvider.LEXISNEXIS,
            title=item.get("title", ""),
            document_type=self._map_document_type(item.get("sourceType", "")),
            citation=citation,
            summary=item.get("summary", ""),
            headnotes=item.get("headnotes", []),
            court=item.get("court", ""),
            judges=item.get("judges", []),
            jurisdiction=item.get("jurisdiction", ""),
            jurisdiction_level=self._map_jurisdiction_level(item.get("jurisdiction", "")),
            court_level=self._map_court_level(item.get("courtLevel", "")),
            topics=item.get("topics", []),
            practice_areas=item.get("practiceAreas", []),
            legal_issues=item.get("legalIssues", []),
            is_published=item.get("isPublished", True),
            is_precedential=item.get("isPrecedential", True),
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
        
        # Parse additional LexisNexis specific data
        if "treatmentAnalysis" in item:
            document.treatment_analysis = item["treatmentAnalysis"]
        
        if "shepardsSignal" in item:
            document.shepard_treatment = item["shepardsSignal"]
        
        return document
    
    async def _parse_document(self, doc_data: Dict) -> LegalDocument:
        """Parse full document data"""
        # Similar to _parse_search_result_item but with more complete data
        return await self._parse_search_result_item(doc_data)
    
    async def _parse_shepards_result(self, shepards_data: Dict) -> SherardsResult:
        """Parse Shepard's Citations analysis results"""
        return SherardsResult(
            citation=shepards_data.get("citation", ""),
            shepards_signal=shepards_data.get("signal", "neutral"),
            treatment_status=shepards_data.get("treatmentStatus", "Valid"),
            citing_decisions=shepards_data.get("citingDecisionsCount", 0),
            citing_secondary=shepards_data.get("citingSecondaryCount", 0),
            citing_statutes=shepards_data.get("citingStatutesCount", 0),
            followed=shepards_data.get("hasBeenFollowed", False),
            distinguished=shepards_data.get("hasBeenDistinguished", False),
            explained=shepards_data.get("hasBeenExplained", False),
            criticized=shepards_data.get("hasBeenCriticized", False),
            questioned=shepards_data.get("hasBeenQuestioned", False),
            overruled=shepards_data.get("hasBeenOverruled", False),
            superseded=shepards_data.get("hasBeenSuperseded", False),
            positive_treatment=shepards_data.get("positiveTreatment", []),
            negative_treatment=shepards_data.get("negativeTreatment", []),
            neutral_treatment=shepards_data.get("neutralTreatment", []),
            warning_treatment=shepards_data.get("warningTreatment", []),
            prior_history=shepards_data.get("priorHistory", []),
            subsequent_history=shepards_data.get("subsequentHistory", []),
            law_review_citations=shepards_data.get("lawReviewCitations", 0),
            treatise_citations=shepards_data.get("treatiseCitations", 0),
            encyclopedia_citations=shepards_data.get("encyclopediaCitations", 0)
        )
    
    async def _parse_citation_validation(self, validation_data: Dict, original_citation: str) -> CitationValidationResult:
        """Parse citation validation results"""
        document_data = validation_data.get("document")
        document = None
        if document_data:
            document = await self._parse_search_result_item(document_data)
        
        return CitationValidationResult(
            original_citation=original_citation,
            is_valid=validation_data.get("isValid", False),
            confidence_score=validation_data.get("confidence", 0.0),
            validation_method="lexisnexis_api",
            normalized_citation=validation_data.get("normalizedCitation"),
            parallel_citations=validation_data.get("parallelCitations", []),
            document=document,
            validation_source=ResearchProvider.LEXISNEXIS
        )
    
    def _map_document_type(self, lexis_type: str) -> DocumentType:
        """Map LexisNexis source type to standard document type"""
        type_mapping = {
            "cases": DocumentType.CASE,
            "statutes": DocumentType.STATUTE,
            "regulations": DocumentType.REGULATION,
            "law-reviews": DocumentType.JOURNAL,
            "treatises": DocumentType.TREATISE,
            "secondary": DocumentType.SECONDARY,
            "practice-materials": DocumentType.SECONDARY,
            "forms": DocumentType.FORM,
            "news": DocumentType.NEWS
        }
        return type_mapping.get(lexis_type.lower(), DocumentType.SECONDARY)
    
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