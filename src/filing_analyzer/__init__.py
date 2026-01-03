"""
Intelligent Filing Analysis and Notification System

Advanced AI-powered system for analyzing legal filings, extracting key information,
assessing impact, and providing intelligent notifications with context-aware insights.

Features:
- AI-powered document analysis and classification
- Legal content extraction and summarization
- Impact assessment and urgency scoring
- Intelligent notification routing
- Deadline and action item detection
- Citation and precedent analysis
- Multi-stakeholder notification management
- Compliance and regulatory analysis
- Integration with case management systems
"""

from .analyzer import FilingAnalyzer, AnalysisConfig
from .models import (
    FilingAnalysis, FilingType, ImpactLevel, UrgencyLevel, ActionItem,
    ExtractedContent, LegalCitation, ComplianceRequirement, NotificationRule
)
from .classifier import DocumentClassifier, ClassificationResult
from .extractor import ContentExtractor, ExtractionResult
from .impact_assessor import ImpactAssessor, ImpactAnalysis
from .notification_engine import NotificationEngine, NotificationStrategy
from .compliance_checker import ComplianceChecker, ComplianceAnalysis
from .intelligence import FilingIntelligence, IntelligenceReport

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    "FilingAnalyzer",
    "AnalysisConfig",
    "FilingAnalysis",
    "FilingType",
    "ImpactLevel",
    "UrgencyLevel",
    "ActionItem",
    "ExtractedContent",
    "LegalCitation",
    "ComplianceRequirement",
    "NotificationRule",
    "DocumentClassifier",
    "ClassificationResult",
    "ContentExtractor",
    "ExtractionResult",
    "ImpactAssessor",
    "ImpactAnalysis",
    "NotificationEngine",
    "NotificationStrategy",
    "ComplianceChecker",
    "ComplianceAnalysis",
    "FilingIntelligence",
    "IntelligenceReport"
]