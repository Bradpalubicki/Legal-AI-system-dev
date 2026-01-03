"""
CourtSync Calendar Module

Provides automatic hearing detection, calendar synchronization,
and court schedule management for legal professionals.
"""

from .hearing_detector import HearingDetector, HearingEvent
from .calendar_sync import CalendarSyncEngine, SyncManager
from .court_data_integration import CourtDataProvider, ECFIntegration
from .conflict_resolver import ConflictResolver, ScheduleConflict
from .courtsync_manager import CourtSyncManager

__all__ = [
    'HearingDetector',
    'HearingEvent', 
    'CalendarSyncEngine',
    'SyncManager',
    'CourtDataProvider',
    'ECFIntegration',
    'ConflictResolver',
    'ScheduleConflict',
    'CourtSyncManager'
]