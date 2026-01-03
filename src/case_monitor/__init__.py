"""
Automated Case Monitoring System for Legal AI

Provides continuous monitoring of PACER cases with automated change detection,
notification systems, and intelligent update scheduling. Monitors docket entries,
document availability, and case status changes in real-time.

Features:
- Automated PACER checking every 15 minutes
- Intelligent change detection and delta tracking
- Multi-channel notification system (email, webhook, in-app)
- Priority-based monitoring with escalation rules
- Cost-optimized monitoring strategies
- Compliance with PACER rate limiting
- Bulk monitoring for law firms
- Historical change tracking and analytics
"""

from .monitor import CaseMonitor, MonitorConfig
from .models import (
    MonitoredCase, MonitoringRule, ChangeDetection, NotificationEvent,
    MonitorStatus, ChangeType, NotificationChannel, AlertSeverity
)
from .scheduler import MonitorScheduler, ScheduleConfig
from .detector import ChangeDetector, DeltaAnalysis
from .notifier import NotificationManager, NotificationConfig
from .analytics import MonitoringAnalytics, MonitoringReport

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    "CaseMonitor",
    "MonitorConfig",
    "MonitoredCase",
    "MonitoringRule",
    "ChangeDetection", 
    "NotificationEvent",
    "MonitorStatus",
    "ChangeType",
    "NotificationChannel",
    "AlertSeverity",
    "MonitorScheduler",
    "ScheduleConfig",
    "ChangeDetector",
    "DeltaAnalysis", 
    "NotificationManager",
    "NotificationConfig",
    "MonitoringAnalytics",
    "MonitoringReport"
]