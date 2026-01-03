"""
Proactive Legal Assistant

24/7 intelligent monitoring system for legal cases with automated alerts,
deadline tracking, and proactive recommendations for legal professionals.

Features:
- Real-time case monitoring and analysis
- Automated deadline and task tracking
- Document change detection and analysis
- Intelligent alert prioritization
- Proactive recommendations and insights
- Court calendar integration
- Compliance monitoring and alerts
- Research trend analysis
"""

from .case_monitor import CaseMonitor, MonitoringRule, AlertPriority, AlertType
from .deadline_tracker import DeadlineTracker, DeadlineType, DeadlineAlert, TaskReminder
from .document_watcher import DocumentWatcher, DocumentChange, ChangeType, DocumentAlert
from .intelligent_alerts import IntelligentAlertsEngine, AlertClassification, RiskAssessment
from .recommendation_engine import RecommendationEngine, RecommendationType, ActionRecommendation
from .compliance_monitor import ComplianceMonitor, ComplianceRule, ComplianceViolation
from .court_calendar import CourtCalendarIntegration, HearingAlert, CalendarEvent
from .research_analyzer import ResearchAnalyzer, TrendAnalysis, LegalTrend
from .notification_dispatcher import NotificationDispatcher, NotificationChannel, DeliveryMethod
from .assistant_coordinator import ProactiveAssistantCoordinator

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    # Core Monitoring
    "CaseMonitor",
    "MonitoringRule",
    "AlertPriority",
    "AlertType",
    
    # Deadline Management
    "DeadlineTracker",
    "DeadlineType", 
    "DeadlineAlert",
    "TaskReminder",
    
    # Document Monitoring
    "DocumentWatcher",
    "DocumentChange",
    "ChangeType",
    "DocumentAlert",
    
    # Intelligence & Alerts
    "IntelligentAlertsEngine",
    "AlertClassification",
    "RiskAssessment",
    
    # Recommendations
    "RecommendationEngine",
    "RecommendationType",
    "ActionRecommendation",
    
    # Compliance
    "ComplianceMonitor",
    "ComplianceRule",
    "ComplianceViolation",
    
    # Court Integration
    "CourtCalendarIntegration",
    "HearingAlert",
    "CalendarEvent",
    
    # Research & Analysis
    "ResearchAnalyzer", 
    "TrendAnalysis",
    "LegalTrend",
    
    # Notifications
    "NotificationDispatcher",
    "NotificationChannel",
    "DeliveryMethod",
    
    # Main Coordinator
    "ProactiveAssistantCoordinator"
]