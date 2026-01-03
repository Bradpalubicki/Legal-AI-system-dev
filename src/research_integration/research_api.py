"""
Research API

Comprehensive REST API endpoints for legal research integration providing
unified search, citation validation, analytics, and research management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .unified_search import UnifiedSearchEngine, SearchStrategy
from .citation_validator import CitationValidator
from .research_cache import ResearchCache
from .research_analytics import ResearchAnalytics
from .westlaw_client import WestlawCredentials
from .lexisnexis_client import LexisNexisCredentials
from .models import (
    ResearchQuery, SearchResult, LegalDocument, Citation,
    ResearchProject, ResearchAlert, ResearchSession,
    DocumentType, ResearchProvider, SearchType
)
from ...shared.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])

# Initialize research components
search_engine: Optional[UnifiedSearchEngine] = None
citation_validator: Optional[CitationValidator] = None
research_cache: Optional[ResearchCache] = None
research_analytics: Optional[ResearchAnalytics] = None


# Request/Response Models
class SearchRequest(BaseModel):
    query_text: str
    search_type: SearchType = SearchType.NATURAL_LANGUAGE
    providers: List[ResearchProvider] = [ResearchProvider.BOTH]
    document_types: List[DocumentType] = []
    jurisdictions: List[str] = []
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    max_results: int = 50
    practice_area: Optional[str] = None
    
    # Advanced search options
    terms_and_connectors: bool = False
    include_unpublished: bool = False
    sort_by: str = "relevance"


class ComprehensiveSearchRequest(BaseModel):
    query_text: str
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None


class CitationValidationRequest(BaseModel):
    citations: List[str]
    use_cache: bool = True
    validate_online: bool = True


class ResearchProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    practice_area: str
    tags: List[str] = []
    client_matter: Optional[UUID] = None


class ResearchAlertRequest(BaseModel):
    name: str
    query: SearchRequest
    frequency: str = "weekly"
    email_notifications: bool = True


class AnalyticsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    metrics: List[str] = ["performance", "usage", "costs"]


# Startup/Shutdown Events
async def initialize_research_system():
    """Initialize research system components"""
    global search_engine, citation_validator, research_cache, research_analytics
    
    try:
        # Initialize credentials (would come from config/environment)
        westlaw_creds = WestlawCredentials(
            client_id="demo_client",
            client_secret="demo_secret"
        )
        lexisnexis_creds = LexisNexisCredentials(
            client_id="demo_client", 
            client_secret="demo_secret"
        )
        
        # Initialize components
        search_engine = UnifiedSearchEngine(
            westlaw_credentials=westlaw_creds,
            lexisnexis_credentials=lexisnexis_creds
        )
        
        citation_validator = CitationValidator(
            westlaw_client=search_engine.westlaw_client,
            lexisnexis_client=search_engine.lexisnexis_client
        )
        
        research_cache = ResearchCache()
        research_analytics = ResearchAnalytics()
        
        # Initialize all components
        await search_engine.initialize()
        await research_cache.initialize()
        
        logger.info("Research system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize research system: {str(e)}")
        raise


async def shutdown_research_system():
    """Shutdown research system components"""
    global search_engine, research_cache
    
    try:
        if search_engine:
            await search_engine.close()
        
        if research_cache:
            await research_cache.close()
        
        logger.info("Research system shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during research system shutdown: {str(e)}")


# Search Endpoints
@router.post("/search", response_model=SearchResult)
async def unified_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Perform unified search across Westlaw and LexisNexis
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Research system not initialized")
    
    try:
        # Convert request to ResearchQuery
        query = ResearchQuery(
            query_text=request.query_text,
            search_type=request.search_type,
            providers=request.providers,
            document_types=request.document_types,
            jurisdictions=request.jurisdictions,
            max_results=request.max_results,
            practice_area=request.practice_area,
            terms_and_connectors=request.terms_and_connectors,
            include_unpublished=request.include_unpublished,
            sort_by=request.sort_by,
            researcher_id=getattr(current_user, 'id', None)
        )
        
        # Add date filters
        if request.date_from:
            query.date_from = datetime.fromisoformat(request.date_from).date()
        if request.date_to:
            query.date_to = datetime.fromisoformat(request.date_to).date()
        
        # Check cache first
        cached_result = None
        if research_cache:
            cached_result = await research_cache.get_cached_search_result(query)
        
        if cached_result:
            logger.info("Returning cached search result")
            return cached_result
        
        # Execute search
        start_time = datetime.utcnow()
        result = await search_engine.search(query)
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Cache result
        if research_cache:
            background_tasks.add_task(
                research_cache.cache_search_result,
                query, result
            )
        
        # Record analytics
        if research_analytics:
            background_tasks.add_task(
                research_analytics.record_query_execution,
                query, result, response_time_ms, getattr(current_user, 'id', None)
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Unified search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search/comprehensive")
async def comprehensive_search(
    request: ComprehensiveSearchRequest,
    current_user = Depends(get_current_user)
):
    """
    Perform comprehensive search across all document types
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Research system not initialized")
    
    try:
        results = await search_engine.comprehensive_search(
            request.query_text,
            request.jurisdiction,
            request.practice_area
        )
        
        return {
            "query": request.query_text,
            "jurisdiction": request.jurisdiction,
            "practice_area": request.practice_area,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Comprehensive search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comprehensive search failed: {str(e)}")


@router.get("/search/cases")
async def search_cases(
    query: str = Query(..., description="Search query"),
    jurisdiction: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    max_results: int = Query(50, le=200),
    current_user = Depends(get_current_user)
):
    """
    Specialized case law search
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Research system not initialized")
    
    try:
        result = await search_engine.search_cases(
            query, jurisdiction, date_from, date_to, max_results
        )
        return result
        
    except Exception as e:
        logger.error(f"Case search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Case search failed: {str(e)}")


@router.get("/search/statutes")
async def search_statutes(
    query: str = Query(..., description="Search query"),
    jurisdiction: Optional[str] = Query(None),
    max_results: int = Query(50, le=200),
    current_user = Depends(get_current_user)
):
    """
    Specialized statute search
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Research system not initialized")
    
    try:
        result = await search_engine.search_statutes(query, jurisdiction, max_results)
        return result
        
    except Exception as e:
        logger.error(f"Statute search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Statute search failed: {str(e)}")


@router.get("/search/secondary")
async def search_secondary_sources(
    query: str = Query(..., description="Search query"),
    practice_area: Optional[str] = Query(None),
    max_results: int = Query(50, le=200),
    current_user = Depends(get_current_user)
):
    """
    Specialized secondary sources search
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Research system not initialized")
    
    try:
        result = await search_engine.search_secondary_sources(query, practice_area, max_results)
        return result
        
    except Exception as e:
        logger.error(f"Secondary sources search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Secondary sources search failed: {str(e)}")


# Document Endpoints
@router.get("/documents/{document_id}")
async def get_document(
    document_id: str = Path(..., description="Document ID"),
    provider: Optional[ResearchProvider] = Query(None),
    include_full_text: bool = Query(True),
    current_user = Depends(get_current_user)
):
    """
    Retrieve full document by ID
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Research system not initialized")
    
    try:
        # Check cache first
        cached_document = None
        if research_cache:
            cached_document = await research_cache.get_cached_document(document_id, provider)
        
        if cached_document:
            return cached_document
        
        # Retrieve from provider
        document = None
        if provider == ResearchProvider.WESTLAW and search_engine.westlaw_client:
            document = await search_engine.westlaw_client.get_document(document_id, include_full_text)
        elif provider == ResearchProvider.LEXISNEXIS and search_engine.lexisnexis_client:
            document = await search_engine.lexisnexis_client.get_document(document_id, include_full_text)
        else:
            # Try both providers
            if search_engine.westlaw_client:
                try:
                    document = await search_engine.westlaw_client.get_document(document_id, include_full_text)
                except:
                    pass
            
            if not document and search_engine.lexisnexis_client:
                try:
                    document = await search_engine.lexisnexis_client.get_document(document_id, include_full_text)
                except:
                    pass
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Cache document
        if research_cache:
            await research_cache.cache_document(document, provider)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document retrieval failed: {str(e)}")


# Citation Endpoints
@router.post("/citations/validate")
async def validate_citations(
    request: CitationValidationRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Validate multiple citations
    """
    if not citation_validator:
        raise HTTPException(status_code=503, detail="Citation validator not initialized")
    
    try:
        results = await citation_validator.validate_multiple_citations(
            request.citations, request.use_cache
        )
        
        # Record analytics for citation validations
        if research_analytics:
            for citation in request.citations:
                # Record citation validation activity
                pass
        
        return {
            "validations": results,
            "total_citations": len(request.citations),
            "valid_citations": sum(1 for r in results.values() if r.is_valid)
        }
        
    except Exception as e:
        logger.error(f"Citation validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Citation validation failed: {str(e)}")


@router.get("/citations/normalize/{citation}")
async def normalize_citation(
    citation: str = Path(..., description="Citation to normalize"),
    current_user = Depends(get_current_user)
):
    """
    Normalize citation to standard format
    """
    if not citation_validator:
        raise HTTPException(status_code=503, detail="Citation validator not initialized")
    
    try:
        normalized = await citation_validator.normalize_citation(citation)
        
        if not normalized:
            raise HTTPException(status_code=400, detail="Citation could not be normalized")
        
        return {
            "original_citation": citation,
            "normalized_citation": normalized
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Citation normalization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Normalization failed: {str(e)}")


@router.post("/citations/extract")
async def extract_citations_from_text(
    text: str = Body(..., embed=True),
    current_user = Depends(get_current_user)
):
    """
    Extract citations from text
    """
    if not citation_validator:
        raise HTTPException(status_code=503, detail="Citation validator not initialized")
    
    try:
        citations = await citation_validator.extract_citations_from_text(text)
        
        return {
            "text_length": len(text),
            "citations_found": len(citations),
            "citations": citations
        }
        
    except Exception as e:
        logger.error(f"Citation extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Citation extraction failed: {str(e)}")


@router.get("/citations/bluebook/{citation}")
async def get_bluebook_format(
    citation: str = Path(..., description="Citation to format"),
    current_user = Depends(get_current_user)
):
    """
    Get Bluebook formatted citation
    """
    if not citation_validator:
        raise HTTPException(status_code=503, detail="Citation validator not initialized")
    
    try:
        bluebook_format = await citation_validator.get_bluebook_format(citation)
        
        if not bluebook_format:
            raise HTTPException(status_code=400, detail="Citation could not be formatted in Bluebook style")
        
        return {
            "original_citation": citation,
            "bluebook_citation": bluebook_format
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bluebook formatting failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bluebook formatting failed: {str(e)}")


# Analytics Endpoints
@router.get("/analytics/user-profile/{user_id}")
async def get_user_research_profile(
    user_id: UUID = Path(..., description="User ID"),
    current_user = Depends(get_current_user)
):
    """
    Get user research profile and analytics
    """
    if not research_analytics:
        raise HTTPException(status_code=503, detail="Research analytics not initialized")
    
    try:
        profile = await research_analytics.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")


@router.get("/analytics/system-metrics")
async def get_system_metrics(
    start_date: datetime = Query(..., description="Start date for metrics"),
    end_date: datetime = Query(..., description="End date for metrics"),
    current_user = Depends(get_current_user)
):
    """
    Get system-wide performance metrics
    """
    if not research_analytics:
        raise HTTPException(status_code=503, detail="Research analytics not initialized")
    
    try:
        metrics = await research_analytics.get_system_performance_metrics(start_date, end_date)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")


@router.get("/analytics/popular-queries")
async def get_popular_queries(
    limit: int = Query(10, le=50),
    current_user = Depends(get_current_user)
):
    """
    Get most popular research queries
    """
    if not research_analytics:
        raise HTTPException(status_code=503, detail="Research analytics not initialized")
    
    try:
        popular_queries = await research_analytics.get_popular_queries(limit)
        return {
            "popular_queries": popular_queries,
            "count": len(popular_queries)
        }
        
    except Exception as e:
        logger.error(f"Failed to get popular queries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve popular queries")


@router.get("/analytics/trends/{trend_type}")
async def get_research_trends(
    trend_type: str = Path(..., description="Type of trend to analyze"),
    time_period: str = Query("weekly", description="Time period for trend analysis"),
    lookback_days: int = Query(30, description="Days to look back for trend analysis"),
    current_user = Depends(get_current_user)
):
    """
    Get research trend analysis
    """
    if not research_analytics:
        raise HTTPException(status_code=503, detail="Research analytics not initialized")
    
    try:
        trend = await research_analytics.analyze_research_trends(
            trend_type, time_period, lookback_days
        )
        return trend
        
    except Exception as e:
        logger.error(f"Failed to analyze trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze trends")


@router.get("/analytics/costs")
async def get_cost_analysis(
    start_date: datetime = Query(..., description="Start date for cost analysis"),
    end_date: datetime = Query(..., description="End date for cost analysis"),
    monthly_budget: Optional[float] = Query(None, description="Monthly budget for comparison"),
    current_user = Depends(get_current_user)
):
    """
    Get comprehensive cost analysis
    """
    if not research_analytics:
        raise HTTPException(status_code=503, detail="Research analytics not initialized")
    
    try:
        cost_analysis = await research_analytics.generate_cost_analysis(
            start_date, end_date, monthly_budget
        )
        return cost_analysis
        
    except Exception as e:
        logger.error(f"Failed to generate cost analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate cost analysis")


# Cache Management Endpoints
@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: Optional[str] = Query(None, description="Pattern to match for invalidation"),
    category: Optional[str] = Query(None, description="Cache category to invalidate"),
    current_user = Depends(get_current_user)
):
    """
    Invalidate cache entries
    """
    if not research_cache:
        raise HTTPException(status_code=503, detail="Research cache not initialized")
    
    try:
        invalidated_count = await research_cache.invalidate_cache(pattern, category)
        
        return {
            "invalidated_count": invalidated_count,
            "pattern": pattern,
            "category": category
        }
        
    except Exception as e:
        logger.error(f"Cache invalidation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache invalidation failed")


@router.get("/cache/statistics")
async def get_cache_statistics(
    current_user = Depends(get_current_user)
):
    """
    Get cache performance statistics
    """
    if not research_cache:
        raise HTTPException(status_code=503, detail="Research cache not initialized")
    
    try:
        stats = await research_cache.get_cache_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")


# System Status Endpoints
@router.get("/status")
async def get_system_status():
    """
    Get research system status
    """
    try:
        status = {
            "search_engine": search_engine is not None,
            "citation_validator": citation_validator is not None,
            "research_cache": research_cache is not None,
            "research_analytics": research_analytics is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check provider availability
        if search_engine:
            providers = search_engine.get_available_providers()
            status["available_providers"] = [p.value for p in providers]
            
            # Get usage metrics
            usage_metrics = search_engine.get_usage_metrics()
            status["usage_metrics"] = usage_metrics
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# Background task endpoints
@router.post("/cache/warm")
async def warm_cache(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    queries: List[str] = Body(..., description="List of queries to warm cache with")
):
    """
    Warm cache with common queries
    """
    if not research_cache or not search_engine:
        raise HTTPException(status_code=503, detail="Required services not initialized")
    
    try:
        # Convert strings to ResearchQuery objects
        research_queries = []
        for query_text in queries:
            research_queries.append(ResearchQuery(query_text=query_text))
        
        # Add cache warming as background task
        background_tasks.add_task(
            research_cache.warm_cache,
            research_queries,
            search_engine
        )
        
        return {
            "message": "Cache warming started",
            "query_count": len(queries)
        }
        
    except Exception as e:
        logger.error(f"Cache warming failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache warming failed")


# User interaction tracking
@router.post("/interactions")
async def record_interaction(
    user_id: UUID = Body(...),
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    query_id: UUID = Body(...),
    interaction_type: str = Body(...),
    metadata: Optional[Dict[str, Any]] = Body(None)
):
    """
    Record user interaction for analytics
    """
    if not research_analytics:
        return {"message": "Analytics not available"}
    
    try:
        background_tasks.add_task(
            research_analytics.record_user_interaction,
            user_id, query_id, interaction_type, metadata
        )
        
        return {"message": "Interaction recorded"}
        
    except Exception as e:
        logger.error(f"Failed to record interaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record interaction")