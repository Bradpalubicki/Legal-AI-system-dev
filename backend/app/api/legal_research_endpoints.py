"""
Legal Research API Endpoints

Provides endpoints for legal research, case law search, and citation processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os

from ..src.core.database import get_db
from ..src.services.legal_research import (
    LegalResearchService,
    ResearchProvider,
    ResearchQuery,
    CaseSearchResult,
    create_legal_research_service
)
from ..src.services.citation_processor import (
    CitationProcessor,
    ExtractedCitation,
    CitationType,
    CitationStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["legal-research"])


# =============================================================================
# REQUEST & RESPONSE MODELS
# =============================================================================

class CaseSearchRequest(BaseModel):
    """Request for case law search"""
    query: str = Field(..., description="Search query", min_length=3, max_length=500)
    court: Optional[str] = Field(None, description="Court filter (e.g., 'scotus', 'ca9')")
    date_filed_after: Optional[str] = Field(None, description="Date filed after (YYYY-MM-DD)")
    date_filed_before: Optional[str] = Field(None, description="Date filed before (YYYY-MM-DD)")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction filter")
    case_name: Optional[str] = Field(None, description="Case name filter")
    citation: Optional[str] = Field(None, description="Citation filter")
    limit: int = Field(default=20, le=100, description="Maximum results")
    providers: Optional[List[str]] = Field(None, description="Research providers to query")


class CaseSearchResponse(BaseModel):
    """Response for case law search"""
    total_results: int
    query: str
    results: List[CaseSearchResult]
    providers_used: List[str]


class CitationExtractionRequest(BaseModel):
    """Request for citation extraction"""
    text: str = Field(..., description="Text to extract citations from", min_length=1, max_length=50000)
    validate_citations: bool = Field(default=True, description="Validate extracted citations")
    citation_types: Optional[List[str]] = Field(None, description="Filter by citation types")


class CitationResponse(BaseModel):
    """Response with extracted citation"""
    text: str
    type: str
    status: str
    span: tuple[int, int]
    confidence: float

    # Case fields
    case_name: Optional[str] = None
    reporter: Optional[str] = None
    volume: Optional[int] = None
    page: Optional[int] = None
    year: Optional[int] = None
    court: Optional[str] = None

    # Statute fields
    title: Optional[str] = None
    section: Optional[str] = None
    jurisdiction: Optional[str] = None

    # Enrichment
    url: Optional[str] = None
    bluebook: Optional[str] = None
    full_case_name: Optional[str] = None

    class Config:
        from_attributes = True


class CitationExtractionResponse(BaseModel):
    """Response for citation extraction"""
    total_citations: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    validation_rate: float
    citations: List[CitationResponse]


class SimilarCasesRequest(BaseModel):
    """Request for similar cases search"""
    case_text: str = Field(..., description="Case text or summary", min_length=100, max_length=10000)
    jurisdiction: Optional[str] = Field(None, description="Limit to jurisdiction")
    limit: int = Field(default=10, le=50, description="Maximum results")


class CaseDetailsRequest(BaseModel):
    """Request for case details"""
    case_id: str = Field(..., description="Case identifier")
    provider: str = Field(default="courtlistener", description="Provider (courtlistener, westlaw, lexisnexis)")


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_research_service() -> LegalResearchService:
    """
    Get or create legal research service.

    Configured via environment variables:
    - COURTLISTENER_TOKEN: Free API token from CourtListener
    - WESTLAW_CLIENT_ID: Westlaw client ID (paid)
    - WESTLAW_CLIENT_SECRET: Westlaw client secret (paid)
    - LEXIS_API_KEY: LexisNexis API key (paid)
    """
    return create_legal_research_service(
        courtlistener_token=os.getenv('COURTLISTENER_TOKEN'),
        westlaw_client_id=os.getenv('WESTLAW_CLIENT_ID'),
        westlaw_client_secret=os.getenv('WESTLAW_CLIENT_SECRET'),
        lexis_api_key=os.getenv('LEXIS_API_KEY')
    )


def get_citation_processor(
    research_service: LegalResearchService = Depends(get_research_service)
) -> CitationProcessor:
    """Get citation processor with research service for validation"""
    return CitationProcessor(research_service=research_service)


# =============================================================================
# CASE LAW SEARCH ENDPOINTS
# =============================================================================

@router.post("/cases/search", response_model=CaseSearchResponse)
async def search_cases(
    request: CaseSearchRequest,
    research_service: LegalResearchService = Depends(get_research_service),
    db: Session = Depends(get_db)
):
    """
    Search case law across legal databases.

    Searches CourtListener (free) and optionally Westlaw/LexisNexis (paid).

    **Example Query**:
    ```json
    {
      "query": "fair use copyright",
      "court": "scotus",
      "limit": 10
    }
    ```

    **Supported Courts**:
    - `scotus`: Supreme Court of the United States
    - `ca1` - `ca11`: Circuit Courts of Appeals
    - `cadc`: DC Circuit
    - `cafc`: Federal Circuit

    **Returns**:
    - List of relevant cases with citations, dates, and snippets
    """
    try:
        # Parse providers
        providers = []
        if request.providers:
            for p in request.providers:
                try:
                    providers.append(ResearchProvider(p))
                except ValueError:
                    logger.warning(f"Unknown provider: {p}")

        # Create query
        query = ResearchQuery(
            query=request.query,
            court=request.court,
            date_filed_after=request.date_filed_after,
            date_filed_before=request.date_filed_before,
            jurisdiction=request.jurisdiction,
            case_name=request.case_name,
            citation=request.citation,
            limit=request.limit
        )

        # Search cases
        results = await research_service.search_cases(query, providers or None)

        # Get providers used
        providers_used = list(set([r.provider for r in results]))

        return CaseSearchResponse(
            total_results=len(results),
            query=request.query,
            results=results,
            providers_used=providers_used
        )

    except Exception as e:
        logger.error(f"Error searching cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Case search failed: {str(e)}"
        )


@router.post("/cases/details", response_model=Dict[str, Any])
async def get_case_details(
    request: CaseDetailsRequest,
    research_service: LegalResearchService = Depends(get_research_service)
):
    """
    Get full case details including opinions and metadata.

    **Parameters**:
    - `case_id`: Case identifier from search results
    - `provider`: Provider to query (default: courtlistener)

    **Returns**:
    - Full case details including:
      - Complete case name
      - All opinions
      - Docket information
      - Citations
      - Judges
      - Parties
    """
    try:
        provider = ResearchProvider(request.provider)

        details = await research_service.get_case_details(
            case_id=request.case_id,
            provider=provider
        )

        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {request.case_id} not found"
            )

        return details

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {request.provider}"
        )
    except Exception as e:
        logger.error(f"Error fetching case details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch case details: {str(e)}"
        )


@router.post("/cases/similar", response_model=CaseSearchResponse)
async def find_similar_cases(
    request: SimilarCasesRequest,
    research_service: LegalResearchService = Depends(get_research_service)
):
    """
    Find cases similar to provided text.

    Uses semantic search to find relevant case law based on
    the facts, issues, or legal concepts in the provided text.

    **Use Cases**:
    - Find precedents for current case
    - Research similar fact patterns
    - Identify relevant case law for legal issues

    **Example**:
    ```json
    {
      "case_text": "Plaintiff alleges copyright infringement for use of song snippet in commercial advertisement without permission.",
      "jurisdiction": "ca9",
      "limit": 10
    }
    ```
    """
    try:
        results = await research_service.search_similar_cases(
            case_text=request.case_text,
            jurisdiction=request.jurisdiction,
            limit=request.limit
        )

        return CaseSearchResponse(
            total_results=len(results),
            query=f"Similar to: {request.case_text[:100]}...",
            results=results,
            providers_used=list(set([r.provider for r in results]))
        )

    except Exception as e:
        logger.error(f"Error finding similar cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar cases search failed: {str(e)}"
        )


# =============================================================================
# CITATION PROCESSING ENDPOINTS
# =============================================================================

@router.post("/citations/extract", response_model=CitationExtractionResponse)
async def extract_citations(
    request: CitationExtractionRequest,
    processor: CitationProcessor = Depends(get_citation_processor)
):
    """
    Extract and validate legal citations from text.

    **Supports**:
    - Case citations (e.g., "123 F.3d 456")
    - Statutory citations (e.g., "17 U.S.C. § 107")
    - Regulatory citations (e.g., "47 C.F.R. § 15.5")

    **Features**:
    - Automatic extraction using Eyecite library
    - Optional validation against legal databases
    - Bluebook formatting
    - Citation enrichment (case names, URLs)

    **Example**:
    ```json
    {
      "text": "In Smith v. Jones, 123 F.3d 456 (9th Cir. 2000), the court held that 17 U.S.C. § 107 permits fair use.",
      "validate": true
    }
    ```
    """
    try:
        # Process document
        citations = await processor.process_document(
            text=request.text,
            validate=request.validate_citations
        )

        # Filter by type if requested
        if request.citation_types:
            valid_types = set(request.citation_types)
            citations = [c for c in citations if c.type.value in valid_types]

        # Get summary stats
        summary = processor.get_citation_summary(citations)

        # Convert to response format
        citation_responses = []
        for cite in citations:
            citation_responses.append(CitationResponse(
                text=cite.text,
                type=cite.type.value,
                status=cite.status.value,
                span=cite.span,
                confidence=cite.confidence,
                case_name=cite.case_name,
                reporter=cite.reporter,
                volume=cite.volume,
                page=cite.page,
                year=cite.year,
                court=cite.court,
                title=cite.title,
                section=cite.section,
                jurisdiction=cite.jurisdiction,
                url=cite.url,
                bluebook=cite.bluebook,
                full_case_name=cite.full_case_name
            ))

        return CitationExtractionResponse(
            total_citations=summary["total_citations"],
            by_type=summary["by_type"],
            by_status=summary["by_status"],
            validation_rate=summary["validation_rate"],
            citations=citation_responses
        )

    except Exception as e:
        logger.error(f"Error extracting citations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation extraction failed: {str(e)}"
        )


@router.get("/citations/validate/{citation}")
async def validate_citation(
    citation: str,
    processor: CitationProcessor = Depends(get_citation_processor)
):
    """
    Validate a single citation.

    **Parameters**:
    - `citation`: Citation to validate (e.g., "123 F.3d 456")

    **Returns**:
    - Validation status
    - Case details if found
    - Bluebook format
    - Confidence score
    """
    try:
        # Extract citation
        citations = processor.extractor.extract_citations(citation)

        if not citations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid citation found in input"
            )

        # Validate first citation
        cite = citations[0]
        validated = await processor.validator.validate_citation(cite)
        validated.bluebook = processor.formatter.to_bluebook(validated)

        return {
            "citation": validated.text,
            "is_valid": validated.status == CitationStatus.VALID,
            "status": validated.status.value,
            "confidence": validated.confidence,
            "bluebook": validated.bluebook,
            "case_name": validated.full_case_name,
            "url": validated.url,
            "type": validated.type.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating citation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation validation failed: {str(e)}"
        )


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/providers")
async def get_providers():
    """
    Get available legal research providers.

    **Returns**:
    - List of configured providers
    - Provider capabilities
    - Configuration status
    """
    providers = []

    if os.getenv('COURTLISTENER_TOKEN'):
        providers.append({
            "name": "CourtListener",
            "id": "courtlistener",
            "type": "free",
            "capabilities": ["case_search", "docket_search", "case_details"],
            "configured": True
        })
    else:
        providers.append({
            "name": "CourtListener",
            "id": "courtlistener",
            "type": "free",
            "capabilities": ["case_search", "docket_search", "case_details"],
            "configured": False,
            "setup_url": "https://www.courtlistener.com/help/api/"
        })

    if os.getenv('WESTLAW_CLIENT_ID') and os.getenv('WESTLAW_CLIENT_SECRET'):
        providers.append({
            "name": "Westlaw",
            "id": "westlaw",
            "type": "paid",
            "capabilities": ["case_search", "statute_search", "citation_validation"],
            "configured": True
        })
    else:
        providers.append({
            "name": "Westlaw",
            "id": "westlaw",
            "type": "paid",
            "capabilities": ["case_search", "statute_search", "citation_validation"],
            "configured": False,
            "contact": "Thomson Reuters"
        })

    if os.getenv('LEXIS_API_KEY'):
        providers.append({
            "name": "LexisNexis",
            "id": "lexisnexis",
            "type": "paid",
            "capabilities": ["case_search", "statute_search", "news_search"],
            "configured": True
        })
    else:
        providers.append({
            "name": "LexisNexis",
            "id": "lexisnexis",
            "type": "paid",
            "capabilities": ["case_search", "statute_search", "news_search"],
            "configured": False,
            "contact": "LexisNexis"
        })

    return {
        "providers": providers,
        "total": len(providers),
        "configured": sum(1 for p in providers if p.get("configured", False))
    }


@router.get("/courts")
async def get_supported_courts():
    """
    Get list of supported court identifiers.

    **Returns**:
    - Court codes and names
    - Jurisdiction levels
    """
    from ..src.services.legal_research import Court

    courts = []
    for court in Court:
        courts.append({
            "code": court.value,
            "name": court.name,
            "level": "supreme" if court == Court.SCOTUS else "appellate"
        })

    return {
        "courts": courts,
        "total": len(courts)
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['router']
