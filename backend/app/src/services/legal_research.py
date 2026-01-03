"""
Legal Research Service

Integrates with legal databases for case law research, statute lookup, and citation validation.
Supports multiple providers: CourtListener (free), Westlaw, LexisNexis.
"""

import logging
import httpx
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & MODELS
# =============================================================================

class ResearchProvider(str, Enum):
    """Legal research data providers"""
    COURTLISTENER = "courtlistener"
    WESTLAW = "westlaw"
    LEXISNEXIS = "lexisnexis"
    FREE_LAW_PROJECT = "freelawproject"


class CaseStatus(str, Enum):
    """Case status types"""
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    PRECEDENTIAL = "precedential"
    NON_PRECEDENTIAL = "non_precedential"


class Court(str, Enum):
    """Common court identifiers"""
    SCOTUS = "scotus"  # Supreme Court of the United States
    CA1 = "ca1"  # First Circuit
    CA2 = "ca2"  # Second Circuit
    CA3 = "ca3"  # Third Circuit
    CA4 = "ca4"  # Fourth Circuit
    CA5 = "ca5"  # Fifth Circuit
    CA6 = "ca6"  # Sixth Circuit
    CA7 = "ca7"  # Seventh Circuit
    CA8 = "ca8"  # Eighth Circuit
    CA9 = "ca9"  # Ninth Circuit
    CA10 = "ca10"  # Tenth Circuit
    CA11 = "ca11"  # Eleventh Circuit
    CADC = "cadc"  # DC Circuit
    CAFC = "cafc"  # Federal Circuit


class LegalCitation(BaseModel):
    """Structured legal citation"""
    full_citation: str
    case_name: Optional[str] = None
    reporter: Optional[str] = None
    volume: Optional[int] = None
    page: Optional[int] = None
    year: Optional[int] = None
    court: Optional[str] = None
    is_valid: bool = False


class CaseSearchResult(BaseModel):
    """Search result for case law"""
    id: str
    case_name: str
    citation: str
    court: str
    date_filed: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    status: Optional[str] = None
    judge: Optional[str] = None
    docket_number: Optional[str] = None
    provider: str


class StatuteResult(BaseModel):
    """Statute or code section result"""
    id: str
    title: str
    citation: str
    jurisdiction: str
    text: str
    url: Optional[str] = None
    effective_date: Optional[str] = None
    provider: str


class ResearchQuery(BaseModel):
    """Legal research query parameters"""
    query: str
    court: Optional[str] = None
    date_filed_after: Optional[str] = None
    date_filed_before: Optional[str] = None
    jurisdiction: Optional[str] = None
    case_name: Optional[str] = None
    citation: Optional[str] = None
    limit: int = Field(default=20, le=100)


# =============================================================================
# COURTLISTENER CLIENT
# =============================================================================

class CourtListenerClient:
    """
    Client for CourtListener API (Free Law Project)

    Free, open-source legal research database.
    Requires API token (free signup at courtlistener.com).
    """

    BASE_URL = "https://www.courtlistener.com/api/rest/v4"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize CourtListener client.

        Args:
            api_token: API token from CourtListener (free signup)
        """
        self.api_token = api_token
        self.session = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Token {api_token}" if api_token else "",
                "User-Agent": "Legal-AI-System/1.0"
            },
            timeout=30.0
        )

    async def search_cases(
        self,
        query: str,
        court: Optional[str] = None,
        filed_after: Optional[str] = None,
        filed_before: Optional[str] = None,
        case_name: Optional[str] = None,
        citation: Optional[str] = None,
        limit: int = 20
    ) -> List[CaseSearchResult]:
        """
        Search case law on CourtListener.

        Args:
            query: Full-text search query
            court: Court identifier (e.g., 'scotus', 'ca9')
            filed_after: Date filed after (YYYY-MM-DD)
            filed_before: Date filed before (YYYY-MM-DD)
            case_name: Filter by case name
            citation: Filter by citation
            limit: Maximum results (max 100)

        Returns:
            List of case search results
        """
        try:
            # Build query string for CourtListener API v4
            query_parts = []
            query_parts.append(query)

            if court:
                query_parts.append(f"court:{court}")
            if case_name:
                query_parts.append(f'caseName:"{case_name}"')
            if citation:
                query_parts.append(f"citation:{citation}")
            if filed_after:
                query_parts.append(f"dateFiled:[{filed_after} TO *]")
            elif filed_before:
                query_parts.append(f"dateFiled:[* TO {filed_before}]")

            params = {
                "type": "r",  # RECAP (dockets) - required for v4 API
                "q": " AND ".join(query_parts) if query_parts else query,
                "page_size": min(limit, 100),
                "order_by": "score desc"
            }

            response = await self.session.get("/search/", params=params)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("results", []):
                result = CaseSearchResult(
                    id=str(item.get("id", "")),
                    case_name=item.get("caseName", ""),
                    citation=item.get("citation", [""])[0] if item.get("citation") else "",
                    court=item.get("court", ""),
                    date_filed=item.get("dateFiled"),
                    url=f"https://www.courtlistener.com{item.get('absolute_url', '')}",
                    snippet=item.get("snippet", ""),
                    status=item.get("status"),
                    judge=item.get("judge"),
                    docket_number=item.get("docketNumber"),
                    provider=ResearchProvider.COURTLISTENER.value
                )
                results.append(result)

            logger.info(f"CourtListener search returned {len(results)} results for query: {query}")
            return results

        except httpx.HTTPError as e:
            logger.error(f"CourtListener API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching CourtListener: {e}")
            return []

    async def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full case details by ID.

        Args:
            case_id: CourtListener case ID

        Returns:
            Full case details including opinions
        """
        try:
            response = await self.session.get(f"/opinions/{case_id}/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching case {case_id}: {e}")
            return None

    async def search_dockets(
        self,
        query: str,
        court: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search court dockets.

        Args:
            query: Search query
            court: Court identifier
            limit: Maximum results

        Returns:
            List of docket entries
        """
        try:
            params = {
                "q": query,
                "page_size": min(limit, 100)
            }

            if court:
                params["court"] = court

            response = await self.session.get("/dockets/", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("results", [])

        except httpx.HTTPError as e:
            logger.error(f"Error searching dockets: {e}")
            return []

    async def close(self):
        """Close HTTP client session"""
        await self.session.aclose()


# =============================================================================
# WESTLAW CLIENT (STUB)
# =============================================================================

class WestlawClient:
    """
    Client for Westlaw API (Thomson Reuters)

    Requires paid subscription and API credentials.
    This is a stub implementation - requires actual credentials to use.
    """

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Westlaw client.

        Args:
            client_id: Westlaw API client ID
            client_secret: Westlaw API client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        logger.warning("Westlaw integration requires paid subscription and is currently a stub")

    async def search_cases(self, query: ResearchQuery) -> List[CaseSearchResult]:
        """
        Search Westlaw case law (stub).

        Note: Requires actual Westlaw API credentials and subscription.
        """
        logger.warning("Westlaw integration not yet implemented - requires paid subscription")
        return []

    async def get_case_citation(self, citation: str) -> Optional[Dict[str, Any]]:
        """Get case by Westlaw citation (stub)"""
        logger.warning("Westlaw integration not yet implemented")
        return None


# =============================================================================
# LEXISNEXIS CLIENT (STUB)
# =============================================================================

class LexisNexisClient:
    """
    Client for LexisNexis API

    Requires paid subscription and API credentials.
    This is a stub implementation - requires actual credentials to use.
    """

    def __init__(self, api_key: str):
        """
        Initialize LexisNexis client.

        Args:
            api_key: LexisNexis API key
        """
        self.api_key = api_key
        logger.warning("LexisNexis integration requires paid subscription and is currently a stub")

    async def search_cases(self, query: ResearchQuery) -> List[CaseSearchResult]:
        """
        Search LexisNexis case law (stub).

        Note: Requires actual LexisNexis API credentials and subscription.
        """
        logger.warning("LexisNexis integration not yet implemented - requires paid subscription")
        return []


# =============================================================================
# UNIFIED LEGAL RESEARCH SERVICE
# =============================================================================

class LegalResearchService:
    """
    Unified legal research service supporting multiple providers.

    Aggregates results from multiple legal databases:
    - CourtListener (free, open-source)
    - Westlaw (paid, premium)
    - LexisNexis (paid, premium)
    """

    def __init__(
        self,
        courtlistener_token: Optional[str] = None,
        westlaw_client_id: Optional[str] = None,
        westlaw_client_secret: Optional[str] = None,
        lexis_api_key: Optional[str] = None
    ):
        """
        Initialize legal research service.

        Args:
            courtlistener_token: CourtListener API token (free)
            westlaw_client_id: Westlaw client ID (paid)
            westlaw_client_secret: Westlaw client secret (paid)
            lexis_api_key: LexisNexis API key (paid)
        """
        # Initialize providers
        self.courtlistener = CourtListenerClient(courtlistener_token) if courtlistener_token else None

        self.westlaw = WestlawClient(
            westlaw_client_id, westlaw_client_secret
        ) if westlaw_client_id and westlaw_client_secret else None

        self.lexis = LexisNexisClient(lexis_api_key) if lexis_api_key else None

        # Log available providers
        available = []
        if self.courtlistener:
            available.append("CourtListener")
        if self.westlaw:
            available.append("Westlaw")
        if self.lexis:
            available.append("LexisNexis")

        logger.info(f"Legal research service initialized with providers: {', '.join(available) if available else 'None'}")

    async def search_cases(
        self,
        query: ResearchQuery,
        providers: Optional[List[ResearchProvider]] = None
    ) -> List[CaseSearchResult]:
        """
        Search case law across multiple providers.

        Args:
            query: Research query parameters
            providers: List of providers to search (default: all available)

        Returns:
            Aggregated list of case search results
        """
        results = []

        # Default to CourtListener if available and no providers specified
        if providers is None:
            providers = [ResearchProvider.COURTLISTENER] if self.courtlistener else []

        # Search CourtListener
        if ResearchProvider.COURTLISTENER in providers and self.courtlistener:
            try:
                cl_results = await self.courtlistener.search_cases(
                    query=query.query,
                    court=query.court,
                    filed_after=query.date_filed_after,
                    filed_before=query.date_filed_before,
                    case_name=query.case_name,
                    citation=query.citation,
                    limit=query.limit
                )
                results.extend(cl_results)
            except Exception as e:
                logger.error(f"Error searching CourtListener: {e}")

        # Search Westlaw (if configured)
        if ResearchProvider.WESTLAW in providers and self.westlaw:
            try:
                wl_results = await self.westlaw.search_cases(query)
                results.extend(wl_results)
            except Exception as e:
                logger.error(f"Error searching Westlaw: {e}")

        # Search LexisNexis (if configured)
        if ResearchProvider.LEXISNEXIS in providers and self.lexis:
            try:
                ln_results = await self.lexis.search_cases(query)
                results.extend(ln_results)
            except Exception as e:
                logger.error(f"Error searching LexisNexis: {e}")

        # Sort by relevance (provider-specific ranking)
        # CourtListener uses score, others may have different metrics
        return results

    async def get_case_details(
        self,
        case_id: str,
        provider: ResearchProvider = ResearchProvider.COURTLISTENER
    ) -> Optional[Dict[str, Any]]:
        """
        Get full case details from a specific provider.

        Args:
            case_id: Case identifier
            provider: Provider to query

        Returns:
            Full case details including opinions
        """
        if provider == ResearchProvider.COURTLISTENER and self.courtlistener:
            return await self.courtlistener.get_case_by_id(case_id)

        return None

    async def search_similar_cases(
        self,
        case_text: str,
        jurisdiction: Optional[str] = None,
        limit: int = 10
    ) -> List[CaseSearchResult]:
        """
        Find cases similar to provided text using semantic search.

        Args:
            case_text: Text to find similar cases for
            jurisdiction: Limit to specific jurisdiction
            limit: Maximum results

        Returns:
            List of similar cases
        """
        # Extract key terms and legal concepts
        # This could be enhanced with NLP/ML for better results
        query = ResearchQuery(
            query=case_text[:500],  # Use first 500 chars as query
            court=jurisdiction,
            limit=limit
        )

        return await self.search_cases(query)

    async def close(self):
        """Close all provider connections"""
        if self.courtlistener:
            await self.courtlistener.close()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_legal_research_service(
    courtlistener_token: Optional[str] = None,
    westlaw_client_id: Optional[str] = None,
    westlaw_client_secret: Optional[str] = None,
    lexis_api_key: Optional[str] = None
) -> LegalResearchService:
    """
    Factory function to create legal research service.

    Args:
        courtlistener_token: CourtListener API token
        westlaw_client_id: Westlaw client ID
        westlaw_client_secret: Westlaw client secret
        lexis_api_key: LexisNexis API key

    Returns:
        Configured LegalResearchService instance
    """
    return LegalResearchService(
        courtlistener_token=courtlistener_token,
        westlaw_client_id=westlaw_client_id,
        westlaw_client_secret=westlaw_client_secret,
        lexis_api_key=lexis_api_key
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'ResearchProvider',
    'CaseStatus',
    'Court',

    # Models
    'LegalCitation',
    'CaseSearchResult',
    'StatuteResult',
    'ResearchQuery',

    # Clients
    'CourtListenerClient',
    'WestlawClient',
    'LexisNexisClient',

    # Service
    'LegalResearchService',
    'create_legal_research_service',
]
