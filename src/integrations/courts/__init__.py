"""
Court API Integrations Module

Comprehensive integration system for federal and state court APIs,
including PACER, CM/ECF, and various state-specific court systems.
"""

from .federal_courts import (
    PacerAPIClient,
    CMECFIntegration,
    FederalCourtCalendar,
    JudgeAssignmentAPI
)

from .state_courts import (
    CaliforniaCourtAPI,
    NewYorkECourtAPI,
    TexasReSearchAPI,
    FloridaECourtAPI,
    IllinoisOdysseyAPI,
    StateCourtManager
)

from .fallback_methods import (
    CourtScrapingEngine,
    ManualDataEntry,
    EmailParser,
    PDFExtractor,
    PhoneVerification,
    FallbackManager
)

from .court_manager import (
    CourtIntegrationManager,
    CourtAPIResponse,
    CourtDataRequest,
    CourtSystemType
)

__version__ = "1.0.0"
__author__ = "Legal AI System"

__all__ = [
    # Federal Courts
    "PacerAPIClient",
    "CMECFIntegration",
    "FederalCourtCalendar",
    "JudgeAssignmentAPI",

    # State Courts
    "CaliforniaCourtAPI",
    "NewYorkECourtAPI",
    "TexasReSearchAPI",
    "FloridaECourtAPI",
    "IllinoisOdysseyAPI",
    "StateCourtManager",

    # Fallback Methods
    "CourtScrapingEngine",
    "ManualDataEntry",
    "EmailParser",
    "PDFExtractor",
    "PhoneVerification",
    "FallbackManager",

    # Core Management
    "CourtIntegrationManager",
    "CourtAPIResponse",
    "CourtDataRequest",
    "CourtSystemType"
]