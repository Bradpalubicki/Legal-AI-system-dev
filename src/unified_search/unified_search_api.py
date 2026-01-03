"""
Unified Search API

Comprehensive REST API for unified legal database search across multiple
providers with advanced result fusion, ranking, and filtering capabilities.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from .database_models import (
    UnifiedQuery, UnifiedSearchResult, UnifiedDocument, SearchStrategy,
    DatabaseProvider, ContentType, DatabaseConfiguration
)
from .search_orchestrator import SearchOrchestrator
from .result_fusion import ResultFusionEngine
from .providers.courtlistener_client import CourtListenerCredentials
from .providers.justia_client import JustiaCredentials
from .providers.heinonline_client import HeinOnlineCredentials
from .providers.government_clients import GovernmentCredentials

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1/unified-search", tags=["Unified Legal Search"])

# Global search orchestrator instance (would be dependency injected in production)
search_orchestrator: Optional[SearchOrchestrator] = None
result_fusion_engine = ResultFusionEngine()


# Request/Response Models
class SearchRequest(BaseModel):
    """Unified search request"""
    query_text: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    query_type: str = Field("natural_language", description="Query type: natural_language, boolean, citation, field")
    
    # Content filters
    content_types: List[ContentType] = Field(default=[], description="Filter by content types")
    jurisdictions: List[str] = Field(default=[], description="Filter by jurisdictions")
    courts: List[str] = Field(default=[], description="Filter by courts")
    
    # Date filters
    date_from: Optional[date] = Field(None, description="Start date filter")
    date_to: Optional[date] = Field(None, description="End date filter")
    decision_date_from: Optional[date] = Field(None, description="Decision date start filter")
    decision_date_to: Optional[date] = Field(None, description="Decision date end filter")
    
    # Advanced filters
    case_law_only: bool = Field(False, description="Search only case law")
    primary_law_only: bool = Field(False, description="Search only primary legal sources")
    secondary_sources_only: bool = Field(False, description="Search only secondary sources")
    unpublished_opinions: bool = Field(True, description="Include unpublished opinions")
    
    # Search configuration
    max_results: int = Field(100, ge=1, le=500, description="Maximum number of results")
    sort_by: str = Field("relevance", description="Sort by: relevance, date, jurisdiction, court")
    include_cited_cases: bool = Field(False, description="Include cited cases analysis")
    include_citing_cases: bool = Field(False, description="Include citing cases analysis")
    
    # Provider preferences
    preferred_providers: List[DatabaseProvider] = Field(default=[], description="Preferred database providers")
    exclude_providers: List[DatabaseProvider] = Field(default=[], description="Excluded database providers")
    free_sources_only: bool = Field(False, description="Search only free sources")
    
    # Quality requirements
    min_reliability_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum reliability score")
    require_full_text: bool = Field(False, description="Require full text availability")
    
    # User context
    practice_area: Optional[str] = Field(None, description="Practice area context")
    research_purpose: Optional[str] = Field(None, description="Purpose of research")
    
    # Execution settings
    timeout_seconds: int = Field(30, ge=5, le=120, description="Search timeout in seconds")
    strategy_id: Optional[str] = Field(None, description="Custom search strategy ID")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from'] and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v


class SearchResponse(BaseModel):
    """Unified search response"""
    search_id: str
    query: SearchRequest
    
    # Results summary
    total_results: int
    results_returned: int
    documents: List[Dict[str, Any]]  # Simplified document representation
    
    # Provider breakdown
    provider_results: Dict[str, int]
    provider_response_times: Dict[str, float]
    providers_searched: List[str]
    providers_failed: List[str]
    
    # Search execution
    search_time_ms: float
    
    # Result quality
    average_relevance: float
    coverage_completeness: float
    result_diversity: float
    
    # Cost information
    total_cost: float
    cost_by_provider: Dict[str, float]
    
    # Pagination
    page: int = 1
    page_size: int = 100
    has_next_page: bool = False
    
    # Recommendations
    suggested_refinements: List[str] = []
    related_queries: List[str] = []
    
    # Metadata
    executed_at: datetime
    cache_used: bool = False


class DocumentDetailResponse(BaseModel):
    """Detailed document response"""
    document_id: str
    source_provider: str
    source_url: Optional[str]
    
    # Document identification
    title: str
    document_type: str
    citation: Optional[str]
    docket_number: Optional[str]
    
    # Content
    full_text: Optional[str]
    summary: Optional[str]
    headnotes: List[str] = []
    key_passages: List[str] = []
    
    # Legal information
    court: Optional[str]
    jurisdiction: Optional[str]
    judges: List[str] = []
    attorneys: List[str] = []
    parties: List[str] = []
    
    # Dates
    decision_date: Optional[date]
    filing_date: Optional[date]
    publication_date: Optional[date]
    
    # Classification
    legal_topics: List[str] = []
    practice_areas: List[str] = []
    subject_headings: List[str] = []
    
    # Citation analysis
    cited_cases: List[str] = []
    citing_cases: List[str] = []
    statutes_cited: List[str] = []
    treatment_status: Optional[str]
    
    # Quality metrics
    relevance_score: float
    authority_score: float
    recency_score: float
    
    # Access information
    is_free_access: bool
    full_text_available: bool
    
    # Metadata
    indexed_at: datetime
    last_updated: datetime


class SearchStrategyRequest(BaseModel):
    """Custom search strategy configuration"""
    strategy_id: str
    name: str
    description: str
    
    # Provider configuration
    provider_priorities: Dict[str, int] = {}
    max_providers: int = Field(10, ge=1, le=20)
    parallel_execution: bool = True
    
    # Result fusion
    fusion_method: str = Field("weighted_score", description="Fusion method")
    deduplication_threshold: float = Field(0.85, ge=0.0, le=1.0)
    max_total_results: int = Field(100, ge=1, le=1000)
    
    # Quality thresholds
    min_relevance_score: float = Field(0.0, ge=0.0, le=1.0)
    min_authority_score: float = Field(0.0, ge=0.0, le=1.0)
    diversity_weight: float = Field(0.1, ge=0.0, le=1.0)
    
    # Cost management
    max_total_cost: Optional[float] = Field(None, ge=0.0)
    prefer_free_sources: bool = False
    
    # Timeout management
    per_provider_timeout_ms: int = Field(5000, ge=1000, le=30000)
    total_timeout_ms: int = Field(15000, ge=5000, le=60000)


# Dependency injection
async def get_search_orchestrator():
    """Get search orchestrator instance"""
    global search_orchestrator
    if not search_orchestrator:
        # Initialize with default credentials
        search_orchestrator = SearchOrchestrator()
        await search_orchestrator.initialize()
    return search_orchestrator


async def get_fusion_engine():
    """Get result fusion engine"""
    return result_fusion_engine


# API Endpoints
@router.post("/search", response_model=SearchResponse)
async def unified_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    orchestrator: SearchOrchestrator = Depends(get_search_orchestrator)
):
    """
    Execute unified search across multiple legal databases
    """
    try:
        logger.info(f"Unified search request: '{request.query_text[:100]}...'")
        
        # Convert request to internal query model
        unified_query = UnifiedQuery(
            query_text=request.query_text,
            query_type=request.query_type,
            content_types=request.content_types,
            jurisdictions=request.jurisdictions,
            courts=request.courts,
            date_from=request.date_from,
            date_to=request.date_to,
            decision_date_from=request.decision_date_from,
            decision_date_to=request.decision_date_to,
            case_law_only=request.case_law_only,
            primary_law_only=request.primary_law_only,
            secondary_sources_only=request.secondary_sources_only,
            unpublished_opinions=request.unpublished_opinions,
            max_results=request.max_results,
            sort_by=request.sort_by,
            include_cited_cases=request.include_cited_cases,
            include_citing_cases=request.include_citing_cases,
            preferred_providers=request.preferred_providers,
            exclude_providers=request.exclude_providers,
            free_sources_only=request.free_sources_only,
            min_reliability_score=request.min_reliability_score,
            require_full_text=request.require_full_text,
            practice_area=request.practice_area,
            research_purpose=request.research_purpose,
            timeout_seconds=request.timeout_seconds
        )
        
        # Get search strategy
        strategy = None
        if request.strategy_id:
            # Load custom strategy (implementation would depend on storage)
            strategy = await load_search_strategy(request.strategy_id)
        
        # Execute search
        search_result = await orchestrator.search(unified_query, strategy)
        
        # Convert to API response
        response = SearchResponse(
            search_id=str(search_result.search_id),
            query=request,
            total_results=search_result.total_results,
            results_returned=search_result.results_returned,
            documents=[_convert_document_to_dict(doc) for doc in search_result.documents],
            provider_results=search_result.provider_results,
            provider_response_times=search_result.provider_response_times,
            providers_searched=[p.value for p in search_result.providers_searched],
            providers_failed=[p.value for p in search_result.providers_failed],
            search_time_ms=search_result.search_time_ms,
            average_relevance=search_result.average_relevance,
            coverage_completeness=search_result.coverage_completeness,
            result_diversity=search_result.result_diversity,
            total_cost=search_result.total_cost,
            cost_by_provider=search_result.cost_by_provider,
            page=search_result.page,
            page_size=search_result.page_size,
            has_next_page=search_result.has_next_page,
            suggested_refinements=search_result.suggested_refinements,
            related_queries=search_result.related_queries,
            executed_at=search_result.executed_at,
            cache_used=search_result.cache_used
        )
        
        # Schedule background analytics update
        background_tasks.add_task(
            update_search_analytics,
            search_result, request
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Unified search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/document/{provider}/{document_id}", response_model=DocumentDetailResponse)
async def get_document_detail(
    provider: str,
    document_id: str,
    orchestrator: SearchOrchestrator = Depends(get_search_orchestrator)
):
    """
    Get detailed information for a specific document
    """
    try:
        # Convert provider string to enum
        try:
            provider_enum = DatabaseProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        # Retrieve document
        document = await orchestrator.get_document(provider_enum, document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert to response model
        response = DocumentDetailResponse(
            document_id=document.source_document_id,
            source_provider=document.source_provider.value,
            source_url=document.source_url,
            title=document.title,
            document_type=document.document_type.value,
            citation=document.citation,
            docket_number=document.docket_number,
            full_text=document.full_text,
            summary=document.summary,
            headnotes=document.headnotes,
            key_passages=document.key_passages,
            court=document.court,
            jurisdiction=document.jurisdiction,
            judges=document.judges,
            attorneys=document.attorneys,
            parties=document.parties,
            decision_date=document.decision_date,
            filing_date=document.filing_date,
            publication_date=document.publication_date,
            legal_topics=document.legal_topics,
            practice_areas=document.practice_areas,
            subject_headings=document.subject_headings,
            cited_cases=document.cited_cases,
            citing_cases=document.citing_cases,
            statutes_cited=document.statutes_cited,
            treatment_status=document.treatment_status,
            relevance_score=document.relevance_score,
            authority_score=document.authority_score,
            recency_score=document.recency_score,
            is_free_access=document.is_free_access,
            full_text_available=document.full_text_available,
            indexed_at=document.indexed_at,
            last_updated=document.last_updated
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document retrieval failed: {str(e)}")


@router.get("/providers/status")
async def get_provider_status(
    orchestrator: SearchOrchestrator = Depends(get_search_orchestrator)
):
    """
    Get status of all database providers
    """
    try:
        status = await orchestrator.get_provider_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Provider status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/strategies", status_code=201)
async def create_search_strategy(request: SearchStrategyRequest):
    """
    Create a custom search strategy
    """
    try:
        # Convert request to internal model
        strategy = SearchStrategy(
            strategy_id=request.strategy_id,
            name=request.name,
            description=request.description,
            provider_priorities={
                DatabaseProvider(k): v for k, v in request.provider_priorities.items()
                if k in [p.value for p in DatabaseProvider]
            },
            max_providers=request.max_providers,
            parallel_execution=request.parallel_execution,
            fusion_method=request.fusion_method,
            deduplication_threshold=request.deduplication_threshold,
            max_total_results=request.max_total_results,
            min_relevance_score=request.min_relevance_score,
            min_authority_score=request.min_authority_score,
            diversity_weight=request.diversity_weight,
            max_total_cost=request.max_total_cost,
            prefer_free_sources=request.prefer_free_sources,
            per_provider_timeout_ms=request.per_provider_timeout_ms,
            total_timeout_ms=request.total_timeout_ms
        )
        
        # Save strategy (implementation would depend on storage)
        await save_search_strategy(strategy)
        
        return {"message": f"Search strategy '{request.strategy_id}' created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Strategy creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Strategy creation failed: {str(e)}")


@router.get("/strategies")
async def list_search_strategies():
    """
    List all available search strategies
    """
    try:
        strategies = await load_all_search_strategies()
        return {"strategies": [
            {
                "strategy_id": s.strategy_id,
                "name": s.name,
                "description": s.description,
                "created_at": s.created_at,
                "is_active": s.is_active
            }
            for s in strategies
        ]}
        
    except Exception as e:
        logger.error(f"Strategy listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Strategy listing failed: {str(e)}")


@router.get("/analytics/search-metrics")
async def get_search_metrics(
    start_date: Optional[date] = Query(None, description="Start date for metrics"),
    end_date: Optional[date] = Query(None, description="End date for metrics")
):
    """
    Get search analytics and metrics
    """
    try:
        metrics = await load_search_metrics(start_date, end_date)
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.get("/suggestions/query")
async def get_query_suggestions(
    query: str = Query(..., min_length=2, description="Partial query for suggestions")
):
    """
    Get query suggestions based on partial input
    """
    try:
        suggestions = await generate_query_suggestions(query)
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Query suggestions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query suggestions failed: {str(e)}")


# Utility Functions
def _convert_document_to_dict(doc: UnifiedDocument) -> Dict[str, Any]:
    """Convert UnifiedDocument to dictionary for API response"""
    return {
        "document_id": doc.source_document_id,
        "source_provider": doc.source_provider.value if doc.source_provider else None,
        "source_url": doc.source_url,
        "title": doc.title,
        "document_type": doc.document_type.value if doc.document_type else None,
        "citation": doc.citation,
        "summary": doc.summary,
        "court": doc.court,
        "jurisdiction": doc.jurisdiction,
        "decision_date": doc.decision_date.isoformat() if doc.decision_date else None,
        "legal_topics": doc.legal_topics,
        "relevance_score": doc.relevance_score,
        "authority_score": doc.authority_score,
        "recency_score": doc.recency_score,
        "is_free_access": doc.is_free_access,
        "full_text_available": doc.full_text_available
    }


# Background Tasks
async def update_search_analytics(search_result: UnifiedSearchResult, request: SearchRequest):
    """Update search analytics in background"""
    try:
        # Implementation would update analytics database
        logger.info(f"Updating search analytics for query: {request.query_text[:50]}...")
        # Add analytics logic here
    except Exception as e:
        logger.error(f"Analytics update failed: {str(e)}")


# Storage Functions (would be implemented with actual storage backend)
async def load_search_strategy(strategy_id: str) -> Optional[SearchStrategy]:
    """Load search strategy by ID"""
    # Implementation would load from database/storage
    return None


async def save_search_strategy(strategy: SearchStrategy):
    """Save search strategy"""
    # Implementation would save to database/storage
    pass


async def load_all_search_strategies() -> List[SearchStrategy]:
    """Load all search strategies"""
    # Implementation would load from database/storage
    return []


async def load_search_metrics(start_date: Optional[date], end_date: Optional[date]) -> Dict[str, Any]:
    """Load search metrics"""
    # Implementation would load from analytics database
    return {
        "total_searches": 0,
        "average_response_time": 0.0,
        "provider_usage": {},
        "popular_queries": [],
        "success_rate": 1.0
    }


async def generate_query_suggestions(partial_query: str) -> List[str]:
    """Generate query suggestions"""
    # Implementation would use search history, common patterns, etc.
    return [
        f"{partial_query} case law",
        f"{partial_query} statute",
        f"{partial_query} regulation",
        f"{partial_query} federal",
        f"{partial_query} supreme court"
    ]


# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "unified-legal-search"
    }