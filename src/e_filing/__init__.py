"""
E-Filing Integration System

Comprehensive electronic filing system supporting multiple court systems
including Federal (PACER/CM/ECF), state courts, and specialized jurisdictions.
Now includes multi-jurisdiction compliance framework with automated formatting
correction and jurisdiction-specific templates.
"""

from .models import *
from .services.filing_service import EFilingService
from .services.court_service import CourtService
from .adapters.federal_adapter import FederalCourtAdapter
from .adapters.state_adapter import StateCourtAdapter
from .processors.document_processor import DocumentProcessor
from .validators.filing_validator import FilingValidator
from .compliance import (
    JurisdictionManager,
    FormattingEngine,
    ComplianceValidator,
    FormatCorrector,
    TemplateManager,
    RuleEngine
)

__all__ = [
    # Models
    "FilingRequest",
    "FilingResponse", 
    "CourtDocument",
    "FilingStatus",
    
    # Services
    "EFilingService",
    "CourtService",
    
    # Adapters
    "FederalCourtAdapter",
    "StateCourtAdapter",
    
    # Processors & Validators
    "DocumentProcessor",
    "FilingValidator",
    
    # Multi-Jurisdiction Compliance System
    "JurisdictionManager",
    "FormattingEngine",
    "ComplianceValidator",
    "FormatCorrector", 
    "TemplateManager",
    "RuleEngine"
]