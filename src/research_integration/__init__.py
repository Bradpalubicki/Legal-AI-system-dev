"""
Research Integration System

Comprehensive legal research platform integrating Westlaw and LexisNexis APIs
with unified search, citation validation, advanced research analytics, and
intelligent caching for optimized performance and cost management.
"""

from .westlaw_client import WestlawClient, WestlawCredentials
from .lexisnexis_client import LexisNexisClient, LexisNexisCredentials
from .unified_search import UnifiedSearchEngine, SearchStrategy
from .citation_validator import CitationValidator
from .research_cache import ResearchCache, CacheConfig
from .research_analytics import ResearchAnalytics

# API router for FastAPI integration
from .research_api import router as research_router

__all__ = [
    # Core Clients
    "WestlawClient",
    "WestlawCredentials", 
    "LexisNexisClient",
    "LexisNexisCredentials",
    
    # Unified Services
    "UnifiedSearchEngine",
    "SearchStrategy",
    "CitationValidator",
    "ResearchCache",
    "CacheConfig",
    "ResearchAnalytics",
    
    # API Integration
    "research_router"
]