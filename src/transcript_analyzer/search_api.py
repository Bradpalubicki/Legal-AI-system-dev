"""
RESTful API for transcript search functionality with advanced query capabilities.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
import asyncio

from ..shared.database.connection import get_db
from ..shared.security.auth import get_current_user
from ..shared.database.models import User, Case
from .transcript_database import TranscriptDatabase, SearchQuery, SearchType, SearchScope
from .search_engine import LegalSearchEngine, LegalSearchFilter, SemanticQuery, CitationQuery


# Pydantic models for request/response
class SearchRequest(BaseModel):
    """Basic search request model."""
    query_text: str = Field(..., min_length=1, max_length=1000)
    search_type: SearchType = SearchType.FULL_TEXT
    search_scope: SearchScope = SearchScope.ALL_TRANSCRIPTS
    case_ids: List[str] = Field(default_factory=list)
    session_ids: List[str] = Field(default_factory=list)
    speakers: List[str] = Field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_annotations: bool = True
    include_context: bool = True
    max_results: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    fuzzy_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    proximity_distance: int = Field(default=10, ge=1, le=100)
    minimum_score: float = Field(default=0.1, ge=0.0, le=1.0)
    highlight_matches: bool = True


class LegalSearchRequest(BaseModel):
    """Advanced legal search request."""
    base_search: SearchRequest
    objection_types: List[str] = Field(default_factory=list)
    ruling_types: List[str] = Field(default_factory=list)
    evidence_types: List[str] = Field(default_factory=list)
    citation_types: List[str] = Field(default_factory=list)
    legal_categories: List[str] = Field(default_factory=list)
    confidence_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    importance_levels: List[str] = Field(default_factory=list)


class SemanticSearchRequest(BaseModel):
    """Semantic search request model."""
    query_text: str = Field(..., min_length=1, max_length=1000)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_results: int = Field(default=50, ge=1, le=500)
    include_related_concepts: bool = True
    expand_legal_terms: bool = True
    case_ids: List[str] = Field(default_factory=list)
    speakers: List[str] = Field(default_factory=list)


class CitationSearchRequest(BaseModel):
    """Citation search request model."""
    citation_text: str = Field(..., min_length=1)
    citation_types: List[str] = Field(default_factory=list)
    jurisdiction: Optional[str] = None
    court_level: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    case_ids: List[str] = Field(default_factory=list)


class ProximitySearchRequest(BaseModel):
    """Proximity search request model."""
    terms: List[str] = Field(..., min_items=2, max_items=10)
    proximity_distance: int = Field(default=10, ge=1, le=100)
    require_all_terms: bool = True
    case_ids: List[str] = Field(default_factory=list)
    session_ids: List[str] = Field(default_factory=list)
    max_results: int = Field(default=50, ge=1, le=500)


class TemporalSearchRequest(BaseModel):
    """Temporal search request model."""
    query_text: str = Field(..., min_length=1)
    start_time: float = Field(..., ge=0.0)
    end_time: float = Field(..., ge=0.0)
    session_id: Optional[str] = None
    max_results: int = Field(default=50, ge=1, le=500)
    
    @validator('end_time')
    def end_time_must_be_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v


class SearchMatch(BaseModel):
    """Search match response model."""
    segment_id: str
    document_id: str
    relevance_score: float
    matched_text: str
    highlighted_text: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    speaker: str
    timestamp: Optional[float] = None
    page_number: Optional[int] = None
    line_number: Optional[int] = None
    annotations: List[Dict[str, Any]] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Search response model."""
    query: Dict[str, Any]
    total_matches: int
    execution_time: float
    matches: List[SearchMatch]
    facets: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    related_queries: List[str] = Field(default_factory=list)


class TranscriptInfo(BaseModel):
    """Transcript document information."""
    id: str
    session_id: str
    case_id: str
    title: str
    proceeding_type: Optional[str]
    date_created: datetime
    date_proceeding: Optional[datetime]
    word_count: Optional[int]
    confidence_score: Optional[float]
    judge_name: Optional[str]
    participants: List[str] = Field(default_factory=list)


class SearchStatistics(BaseModel):
    """Search statistics response."""
    total_documents: int
    total_word_count: int
    total_segments: int
    recent_documents: int
    speaker_statistics: List[Dict[str, Any]]
    average_words_per_document: float


# Initialize components
transcript_db = None
search_engine = None

def get_transcript_db():
    """Get transcript database instance."""
    global transcript_db
    if transcript_db is None:
        # Initialize with database URL from config
        database_url = "postgresql://user:password@localhost/legal_ai"  # Would come from config
        transcript_db = TranscriptDatabase(database_url)
    return transcript_db

def get_search_engine():
    """Get search engine instance."""
    global search_engine
    if search_engine is None:
        search_engine = LegalSearchEngine(get_transcript_db())
    return search_engine


# Create router
router = APIRouter(prefix="/api/transcript-search", tags=["transcript-search"])


@router.post("/search", response_model=SearchResponse)
async def search_transcripts(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform full-text search across transcripts."""
    try:
        transcript_db = get_transcript_db()
        
        # Convert request to SearchQuery
        search_query = SearchQuery(
            query_text=request.query_text,
            search_type=request.search_type,
            search_scope=request.search_scope,
            case_ids=request.case_ids,
            session_ids=request.session_ids,
            speakers=request.speakers,
            date_range=(request.date_from, request.date_to) if request.date_from and request.date_to else None,
            include_annotations=request.include_annotations,
            include_context=request.include_context,
            max_results=request.max_results,
            offset=request.offset,
            fuzzy_threshold=request.fuzzy_threshold,
            proximity_distance=request.proximity_distance,
            minimum_score=request.minimum_score,
            highlight_matches=request.highlight_matches
        )
        
        # Perform search
        results = await transcript_db.search_transcripts(search_query)
        
        # Convert to response format
        return SearchResponse(
            query={
                "text": results.query.query_text,
                "type": results.query.search_type.value,
                "scope": results.query.search_scope.value,
                "filters": {
                    "case_ids": results.query.case_ids,
                    "speakers": results.query.speakers,
                    "max_results": results.query.max_results
                }
            },
            total_matches=results.total_matches,
            execution_time=results.execution_time,
            matches=[
                SearchMatch(
                    segment_id=match.segment_id,
                    document_id=match.document_id,
                    relevance_score=match.relevance_score,
                    matched_text=match.matched_text,
                    highlighted_text=match.highlighted_text,
                    context_before=match.context_before,
                    context_after=match.context_after,
                    speaker=match.speaker,
                    timestamp=match.timestamp,
                    page_number=match.page_number,
                    line_number=match.line_number,
                    annotations=match.annotations
                )
                for match in results.matches
            ],
            facets=results.facets,
            suggestions=results.suggestions,
            related_queries=results.related_queries
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/legal-search", response_model=SearchResponse)
async def legal_search(
    request: LegalSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Perform advanced legal search with specialized filters."""
    try:
        search_engine = get_search_engine()
        
        # Convert base search request
        search_query = SearchQuery(
            query_text=request.base_search.query_text,
            search_type=request.base_search.search_type,
            search_scope=request.base_search.search_scope,
            case_ids=request.base_search.case_ids,
            session_ids=request.base_search.session_ids,
            speakers=request.base_search.speakers,
            date_range=(request.base_search.date_from, request.base_search.date_to) if request.base_search.date_from and request.base_search.date_to else None,
            include_annotations=request.base_search.include_annotations,
            include_context=request.base_search.include_context,
            max_results=request.base_search.max_results,
            offset=request.base_search.offset,
            minimum_score=request.base_search.minimum_score,
            highlight_matches=request.base_search.highlight_matches
        )
        
        # Create legal filters
        legal_filters = LegalSearchFilter(
            objection_types=request.objection_types,
            ruling_types=request.ruling_types,
            evidence_types=request.evidence_types,
            citation_types=request.citation_types,
            legal_categories=request.legal_categories,
            confidence_threshold=request.confidence_threshold,
            importance_levels=request.importance_levels
        )
        
        # Perform advanced legal search
        results = await search_engine.advanced_legal_search(search_query, legal_filters)
        
        # Convert to response format
        return _convert_search_results_to_response(results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Legal search error: {str(e)}")


@router.post("/semantic-search", response_model=SearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Perform semantic search using AI embeddings."""
    try:
        search_engine = get_search_engine()
        
        # Create semantic query
        semantic_query = SemanticQuery(
            query_text=request.query_text,
            similarity_threshold=request.similarity_threshold,
            max_results=request.max_results,
            include_related_concepts=request.include_related_concepts,
            expand_legal_terms=request.expand_legal_terms
        )
        
        # Perform semantic search
        results = await search_engine.semantic_search(semantic_query)
        
        return _convert_search_results_to_response(results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")


@router.post("/citation-search", response_model=SearchResponse)
async def citation_search(
    request: CitationSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search for legal citations within transcripts."""
    try:
        search_engine = get_search_engine()
        
        # Create citation query
        citation_query = CitationQuery(
            citation_text=request.citation_text,
            citation_types=request.citation_types,
            jurisdiction=request.jurisdiction,
            court_level=request.court_level,
            date_range=(request.date_from, request.date_to) if request.date_from and request.date_to else None
        )
        
        # Perform citation search
        results = await search_engine.citation_search(citation_query)
        
        return _convert_search_results_to_response(results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Citation search error: {str(e)}")


@router.post("/proximity-search", response_model=SearchResponse)
async def proximity_search(
    request: ProximitySearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search for multiple terms within specified proximity."""
    try:
        search_engine = get_search_engine()
        
        # Perform proximity search
        results = await search_engine.multi_term_proximity_search(
            terms=request.terms,
            proximity_distance=request.proximity_distance,
            require_all_terms=request.require_all_terms
        )
        
        return _convert_search_results_to_response(results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proximity search error: {str(e)}")


@router.post("/temporal-search", response_model=SearchResponse)
async def temporal_search(
    request: TemporalSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search within specific time range of a session."""
    try:
        search_engine = get_search_engine()
        
        # Perform temporal search
        results = await search_engine.temporal_search(
            query_text=request.query_text,
            time_range=(request.start_time, request.end_time),
            session_id=request.session_id
        )
        
        return _convert_search_results_to_response(results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Temporal search error: {str(e)}")


@router.get("/contextual-search")
async def contextual_search(
    query_text: str = Query(..., min_length=1),
    context_window: int = Query(default=5, ge=1, le=20),
    speaker_context: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user)
):
    """Search with extended context around matches."""
    try:
        search_engine = get_search_engine()
        
        # Perform contextual search
        results = await search_engine.contextual_search(
            query_text=query_text,
            context_window=context_window,
            speaker_context=speaker_context
        )
        
        return _convert_search_results_to_response(results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contextual search error: {str(e)}")


@router.post("/cross-case-search")
async def cross_case_search(
    query_text: str = Body(...),
    case_ids: List[str] = Body(...),
    compare_results: bool = Body(default=True),
    current_user: User = Depends(get_current_user)
):
    """Search across multiple cases and compare results."""
    try:
        search_engine = get_search_engine()
        
        # Perform cross-case search
        results = await search_engine.search_across_cases(
            query_text=query_text,
            case_ids=case_ids,
            compare_results=compare_results
        )
        
        # Format response
        response = {}
        for case_id, case_results in results.items():
            if case_id == 'comparison':
                response[case_id] = case_results
            else:
                response[case_id] = _convert_search_results_to_response(case_results)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cross-case search error: {str(e)}")


@router.get("/transcript/{session_id}", response_model=Optional[TranscriptInfo])
async def get_transcript_info(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get transcript information by session ID."""
    try:
        transcript_db = get_transcript_db()
        
        document_info = await transcript_db.get_document_by_session(session_id)
        
        if not document_info:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return TranscriptInfo(**document_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving transcript: {str(e)}")


@router.get("/statistics", response_model=SearchStatistics)
async def get_search_statistics(
    case_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user)
):
    """Get transcript database statistics."""
    try:
        transcript_db = get_transcript_db()
        
        stats = await transcript_db.get_transcript_statistics(case_id)
        
        return SearchStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.post("/store-transcript")
async def store_transcript(
    session_id: str = Body(...),
    case_id: str = Body(...),
    transcript_content: str = Body(...),
    segments: Optional[List[Dict[str, Any]]] = Body(default=None),
    metadata: Optional[Dict[str, Any]] = Body(default=None),
    current_user: User = Depends(get_current_user)
):
    """Store a new transcript in the database."""
    try:
        transcript_db = get_transcript_db()
        
        document_id = await transcript_db.store_transcript(
            session_id=session_id,
            case_id=case_id,
            transcript_content=transcript_content,
            segments=segments,
            metadata=metadata
        )
        
        return {
            "document_id": document_id,
            "message": "Transcript stored successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing transcript: {str(e)}")


@router.post("/add-annotation")
async def add_annotation(
    document_id: str = Body(...),
    annotation_type: str = Body(...),
    title: str = Body(...),
    description: str = Body(...),
    start_segment_id: Optional[str] = Body(default=None),
    end_segment_id: Optional[str] = Body(default=None),
    metadata: Optional[Dict[str, Any]] = Body(default=None),
    current_user: User = Depends(get_current_user)
):
    """Add annotation to a transcript."""
    try:
        transcript_db = get_transcript_db()
        
        annotation_id = await transcript_db.add_annotation(
            document_id=document_id,
            annotation_type=annotation_type,
            title=title,
            description=description,
            start_segment_id=start_segment_id,
            end_segment_id=end_segment_id,
            metadata=metadata,
            created_by=str(current_user.id)
        )
        
        return {
            "annotation_id": annotation_id,
            "message": "Annotation added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding annotation: {str(e)}")


@router.get("/export-results/{format}")
async def export_search_results(
    format: str,
    query_text: str = Query(...),
    search_type: str = Query(default="full_text"),
    case_ids: Optional[str] = Query(default=None),  # Comma-separated
    max_results: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Export search results in specified format."""
    try:
        if format.lower() not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        transcript_db = get_transcript_db()
        
        # Parse search parameters
        search_query = SearchQuery(
            query_text=query_text,
            search_type=SearchType(search_type) if search_type in [t.value for t in SearchType] else SearchType.FULL_TEXT,
            case_ids=case_ids.split(",") if case_ids else [],
            max_results=max_results
        )
        
        # Perform search
        results = await transcript_db.search_transcripts(search_query)
        
        # Export results
        exported_data = await transcript_db.export_search_results(results, format)
        
        # Set appropriate content type
        media_type = "application/json" if format.lower() == "json" else "text/csv"
        
        from fastapi.responses import Response
        return Response(
            content=exported_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=search_results.{format.lower()}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


def _convert_search_results_to_response(results) -> SearchResponse:
    """Convert SearchResults to SearchResponse."""
    return SearchResponse(
        query={
            "text": results.query.query_text,
            "type": results.query.search_type.value,
            "scope": results.query.search_scope.value
        },
        total_matches=results.total_matches,
        execution_time=results.execution_time,
        matches=[
            SearchMatch(
                segment_id=match.segment_id,
                document_id=match.document_id,
                relevance_score=match.relevance_score,
                matched_text=match.matched_text,
                highlighted_text=match.highlighted_text,
                context_before=match.context_before,
                context_after=match.context_after,
                speaker=match.speaker,
                timestamp=match.timestamp,
                page_number=match.page_number,
                line_number=match.line_number,
                annotations=match.annotations
            )
            for match in results.matches
        ],
        facets=results.facets,
        suggestions=results.suggestions,
        related_queries=results.related_queries
    )