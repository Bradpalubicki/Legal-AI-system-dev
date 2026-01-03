"""
Unified Search System

Comprehensive unified search interface across all legal databases including
commercial providers (Westlaw, LexisNexis), free resources (CourtListener, 
Google Scholar), government databases, and specialized legal collections.
"""

from .database_models import (
    DatabaseProvider, UnifiedQuery, UnifiedDocument, UnifiedSearchResult,
    SearchStrategy, DatabaseConfiguration, ContentType, AccessType,
    DatabaseCapability, GeographicCoverage
)
from .search_orchestrator import SearchOrchestrator
from .result_fusion import ResultFusionEngine
from .unified_search_api import router as unified_search_router

# Provider clients
from .providers.courtlistener_client import CourtListenerClient, CourtListenerCredentials
from .providers.google_scholar_client import GoogleScholarClient
from .providers.justia_client import JustiaClient, JustiaCredentials
from .providers.heinonline_client import HeinOnlineClient, HeinOnlineCredentials
from .providers.government_clients import (
    GovInfoClient, CongressGovClient, SupremeCourtClient, GovernmentCredentials
)

__all__ = [
    # Core Models
    "DatabaseProvider",
    "UnifiedQuery", 
    "UnifiedDocument",
    "UnifiedSearchResult",
    "SearchStrategy",
    "DatabaseConfiguration",
    "ContentType",
    "AccessType",
    "DatabaseCapability",
    "GeographicCoverage",
    
    # Core Engine Components
    "SearchOrchestrator",
    "ResultFusionEngine",
    
    # API Router
    "unified_search_router",
    
    # Provider Clients
    "CourtListenerClient",
    "CourtListenerCredentials",
    "GoogleScholarClient", 
    "JustiaClient",
    "JustiaCredentials",
    "HeinOnlineClient",
    "HeinOnlineCredentials",
    "GovInfoClient",
    "CongressGovClient", 
    "SupremeCourtClient",
    "GovernmentCredentials"
]