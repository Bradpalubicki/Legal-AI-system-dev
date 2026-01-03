"""
Activity Tracker Module

Comprehensive activity tracking system for legal case workflows
with real-time monitoring and pattern recognition capabilities.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_
import logging
from collections import defaultdict, deque
import asyncio
import json

logger = logging.getLogger(__name__)

class ActivityType(Enum):
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_MODIFIED = "document_modified"
    DOCUMENT_ACCESSED = "document_accessed"
    DOCUMENT_DELETED = "document_deleted"
    
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    CASE_STATUS_CHANGED = "case_status_changed"
    CASE_CLOSED = "case_closed"
    
    CLIENT_INTERACTION = "client_interaction"
    CLIENT_MEETING = "client_meeting"
    CLIENT_COMMUNICATION = "client_communication"
    
    COURT_FILING = "court_filing"
    COURT_HEARING = "court_hearing"
    COURT_ORDER = "court_order"
    
    BILLING_CREATED = "billing_created"
    BILLING_SENT = "billing_sent"
    PAYMENT_RECEIVED = "payment_received"
    
    DEADLINE_CREATED = "deadline_created"
    DEADLINE_MODIFIED = "deadline_modified"
    DEADLINE_COMPLETED = "deadline_completed"
    DEADLINE_MISSED = "deadline_missed"
    
    RESEARCH_CONDUCTED = "research_conducted"
    RESEARCH_SAVED = "research_saved"
    
    SETTLEMENT_NEGOTIATION = "settlement_negotiation"
    SETTLEMENT_OFFER = "settlement_offer"
    SETTLEMENT_REACHED = "settlement_reached"
    
    ATTORNEY_LOGIN = "attorney_login"
    ATTORNEY_LOGOUT = "attorney_logout"
    
    SYSTEM_ALERT = "system_alert"
    SYSTEM_ERROR = "system_error"

@dataclass
class ActivityEvent:
    id: Optional[int] = None
    activity_type: ActivityType = ActivityType.DOCUMENT_CREATED
    case_id: Optional[int] = None
    attorney_id: Optional[int] = None
    client_id: Optional[int] = None
    document_id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    duration_seconds: Optional[float] = None
    outcome: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical
    tags: Set[str] = field(default_factory=set)

@dataclass
class ActivityMetrics:
    total_activities: int = 0
    activities_by_type: Dict[ActivityType, int] = field(default_factory=dict)
    activities_by_hour: Dict[int, int] = field(default_factory=dict)
    activities_by_day: Dict[str, int] = field(default_factory=dict)
    activities_by_attorney: Dict[int, int] = field(default_factory=dict)
    activities_by_case: Dict[int, int] = field(default_factory=dict)
    avg_activities_per_day: float = 0.0
    peak_activity_hour: Optional[int] = None
    peak_activity_day: Optional[str] = None
    most_active_attorney: Optional[int] = None
    most_active_case: Optional[int] = None
    activity_velocity: float = 0.0  # activities per hour
    session_duration_avg: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

class ActivityTracker:
    def __init__(self):
        self.activity_buffer: deque = deque(maxlen=10000)
        self.session_tracker: Dict[str, Dict[str, Any]] = {}
        self.real_time_metrics: ActivityMetrics = ActivityMetrics()
        self.activity_patterns: Dict[str, Any] = {}
        self.anomaly_thresholds: Dict[str, float] = {
            'hourly_activity_threshold': 100,
            'session_duration_threshold': 14400,  # 4 hours
            'error_rate_threshold': 0.05,
            'velocity_spike_threshold': 3.0
        }
        
    async def track_activity(
        self,
        activity_type: ActivityType,
        case_id: Optional[int] = None,
        attorney_id: Optional[int] = None,
        client_id: Optional[int] = None,
        document_id: Optional[int] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        request_info: Optional[Dict[str, str]] = None,
        db: Optional[AsyncSession] = None
    ) -> ActivityEvent:
        """Track a single activity event."""
        try:
            event = ActivityEvent(
                activity_type=activity_type,
                case_id=case_id,
                attorney_id=attorney_id,
                client_id=client_id,
                document_id=document_id,
                description=description,
                metadata=metadata or {},
                ip_address=request_info.get('ip_address') if request_info else None,
                user_agent=request_info.get('user_agent') if request_info else None,
                session_id=request_info.get('session_id') if request_info else None
            )
            
            # Add to buffer for real-time processing
            self.activity_buffer.append(event)
            
            # Update session tracking
            if event.session_id:
                await self._update_session_tracking(event)
            
            # Update real-time metrics
            await self._update_real_time_metrics(event)
            
            # Persist to database if available
            if db:
                await self._persist_activity(event, db)
            
            # Check for anomalies
            await self._check_activity_anomalies(event)
            
            logger.info(f"Activity tracked: {activity_type.value} for case {case_id}")
            return event
            
        except Exception as e:
            logger.error(f"Error tracking activity: {e}")
            raise

    async def track_session_start(
        self,
        session_id: str,
        attorney_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Track the start of a user session."""
        self.session_tracker[session_id] = {
            'attorney_id': attorney_id,
            'start_time': datetime.utcnow(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'activity_count': 0,
            'last_activity': datetime.utcnow(),
            'pages_visited': set(),
            'actions_performed': []
        }
        
        await self.track_activity(
            ActivityType.ATTORNEY_LOGIN,
            attorney_id=attorney_id,
            description=f"Attorney logged in from {ip_address}",
            request_info={
                'session_id': session_id,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )

    async def track_session_end(self, session_id: str) -> None:
        """Track the end of a user session."""
        if session_id not in self.session_tracker:
            return
            
        session_data = self.session_tracker[session_id]
        duration = (datetime.utcnow() - session_data['start_time']).total_seconds()
        
        await self.track_activity(
            ActivityType.ATTORNEY_LOGOUT,
            attorney_id=session_data['attorney_id'],
            description=f"Attorney logged out after {duration:.0f} seconds",
            metadata={
                'session_duration': duration,
                'activity_count': session_data['activity_count'],
                'pages_visited': len(session_data['pages_visited'])
            },
            request_info={'session_id': session_id}
        )
        
        del self.session_tracker[session_id]

    async def get_activity_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        case_ids: Optional[List[int]] = None,
        attorney_ids: Optional[List[int]] = None,
        db: Optional[AsyncSession] = None
    ) -> ActivityMetrics:
        """Get comprehensive activity metrics for specified period."""
        try:
            if not db:
                return self.real_time_metrics
                
            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Build query filters
            filters = [
                # Assuming ActivityEvent model exists in database
                # ActivityEvent.timestamp >= start_date,
                # ActivityEvent.timestamp <= end_date
            ]
            
            if case_ids:
                # filters.append(ActivityEvent.case_id.in_(case_ids))
                pass
            if attorney_ids:
                # filters.append(ActivityEvent.attorney_id.in_(attorney_ids))
                pass
            
            metrics = ActivityMetrics()
            
            # Calculate metrics from database
            # This would require actual database queries
            # For now, return real-time metrics
            return self.real_time_metrics
            
        except Exception as e:
            logger.error(f"Error getting activity metrics: {e}")
            return ActivityMetrics()

    async def get_activity_timeline(
        self,
        case_id: Optional[int] = None,
        attorney_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        activity_types: Optional[List[ActivityType]] = None,
        db: Optional[AsyncSession] = None
    ) -> List[ActivityEvent]:
        """Get chronological timeline of activities."""
        try:
            # Filter from buffer for recent activities
            timeline = []
            
            for event in self.activity_buffer:
                if case_id and event.case_id != case_id:
                    continue
                if attorney_id and event.attorney_id != attorney_id:
                    continue
                if start_date and event.timestamp < start_date:
                    continue
                if end_date and event.timestamp > end_date:
                    continue
                if activity_types and event.activity_type not in activity_types:
                    continue
                    
                timeline.append(event)
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x.timestamp, reverse=True)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting activity timeline: {e}")
            return []

    async def detect_activity_patterns(
        self,
        lookback_days: int = 30,
        min_pattern_frequency: int = 3
    ) -> Dict[str, Any]:
        """Detect recurring patterns in activities."""
        try:
            patterns = {
                'hourly_patterns': defaultdict(int),
                'daily_patterns': defaultdict(int),
                'sequence_patterns': defaultdict(int),
                'attorney_patterns': defaultdict(lambda: defaultdict(int)),
                'case_patterns': defaultdict(lambda: defaultdict(int)),
                'anomalous_patterns': []
            }
            
            # Analyze recent activities from buffer
            cutoff_time = datetime.utcnow() - timedelta(days=lookback_days)
            recent_activities = [
                event for event in self.activity_buffer
                if event.timestamp >= cutoff_time
            ]
            
            # Detect hourly patterns
            for event in recent_activities:
                hour = event.timestamp.hour
                patterns['hourly_patterns'][hour] += 1
            
            # Detect daily patterns
            for event in recent_activities:
                day = event.timestamp.strftime('%A')
                patterns['daily_patterns'][day] += 1
            
            # Detect sequence patterns
            activity_sequence = [event.activity_type for event in recent_activities[-100:]]
            for i in range(len(activity_sequence) - 2):
                sequence = f"{activity_sequence[i].value} -> {activity_sequence[i+1].value}"
                patterns['sequence_patterns'][sequence] += 1
            
            # Detect attorney-specific patterns
            for event in recent_activities:
                if event.attorney_id:
                    patterns['attorney_patterns'][event.attorney_id][event.activity_type] += 1
            
            # Detect case-specific patterns
            for event in recent_activities:
                if event.case_id:
                    patterns['case_patterns'][event.case_id][event.activity_type] += 1
            
            # Filter patterns by minimum frequency
            filtered_patterns = {}
            for pattern_type, pattern_data in patterns.items():
                if pattern_type == 'anomalous_patterns':
                    filtered_patterns[pattern_type] = pattern_data
                    continue
                    
                filtered_data = {
                    k: v for k, v in pattern_data.items()
                    if (isinstance(v, int) and v >= min_pattern_frequency) or
                       (isinstance(v, dict) and any(count >= min_pattern_frequency for count in v.values()))
                }
                filtered_patterns[pattern_type] = filtered_data
            
            return filtered_patterns
            
        except Exception as e:
            logger.error(f"Error detecting activity patterns: {e}")
            return {}

    async def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active sessions."""
        try:
            current_time = datetime.utcnow()
            active_sessions = {}
            
            for session_id, session_data in self.session_tracker.items():
                # Consider session active if last activity was within 30 minutes
                time_since_last = (current_time - session_data['last_activity']).total_seconds()
                if time_since_last <= 1800:  # 30 minutes
                    session_duration = (current_time - session_data['start_time']).total_seconds()
                    active_sessions[session_id] = {
                        'attorney_id': session_data['attorney_id'],
                        'duration_seconds': session_duration,
                        'activity_count': session_data['activity_count'],
                        'last_activity': session_data['last_activity'],
                        'pages_visited': len(session_data['pages_visited']),
                        'ip_address': session_data.get('ip_address')
                    }
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return {}

    async def _update_session_tracking(self, event: ActivityEvent) -> None:
        """Update session tracking data."""
        if event.session_id in self.session_tracker:
            session_data = self.session_tracker[event.session_id]
            session_data['activity_count'] += 1
            session_data['last_activity'] = event.timestamp
            session_data['actions_performed'].append({
                'action': event.activity_type.value,
                'timestamp': event.timestamp,
                'description': event.description
            })

    async def _update_real_time_metrics(self, event: ActivityEvent) -> None:
        """Update real-time metrics with new event."""
        metrics = self.real_time_metrics
        metrics.total_activities += 1
        
        # Update activity type counts
        if event.activity_type in metrics.activities_by_type:
            metrics.activities_by_type[event.activity_type] += 1
        else:
            metrics.activities_by_type[event.activity_type] = 1
        
        # Update hourly counts
        hour = event.timestamp.hour
        if hour in metrics.activities_by_hour:
            metrics.activities_by_hour[hour] += 1
        else:
            metrics.activities_by_hour[hour] = 1
        
        # Update daily counts
        day = event.timestamp.strftime('%Y-%m-%d')
        if day in metrics.activities_by_day:
            metrics.activities_by_day[day] += 1
        else:
            metrics.activities_by_day[day] = 1
        
        # Update attorney counts
        if event.attorney_id:
            if event.attorney_id in metrics.activities_by_attorney:
                metrics.activities_by_attorney[event.attorney_id] += 1
            else:
                metrics.activities_by_attorney[event.attorney_id] = 1
        
        # Update case counts
        if event.case_id:
            if event.case_id in metrics.activities_by_case:
                metrics.activities_by_case[event.case_id] += 1
            else:
                metrics.activities_by_case[event.case_id] = 1
        
        # Calculate peak values
        if metrics.activities_by_hour:
            metrics.peak_activity_hour = max(metrics.activities_by_hour, key=metrics.activities_by_hour.get)
        
        if metrics.activities_by_attorney:
            metrics.most_active_attorney = max(metrics.activities_by_attorney, key=metrics.activities_by_attorney.get)
        
        if metrics.activities_by_case:
            metrics.most_active_case = max(metrics.activities_by_case, key=metrics.activities_by_case.get)
        
        metrics.last_updated = datetime.utcnow()

    async def _persist_activity(self, event: ActivityEvent, db: AsyncSession) -> None:
        """Persist activity event to database."""
        try:
            # This would create a database record
            # Implementation depends on your database models
            pass
        except Exception as e:
            logger.error(f"Error persisting activity: {e}")

    async def _check_activity_anomalies(self, event: ActivityEvent) -> None:
        """Check for anomalous activity patterns."""
        try:
            # Check for unusual activity velocity
            recent_activities = [
                e for e in self.activity_buffer
                if (event.timestamp - e.timestamp).total_seconds() <= 3600  # Last hour
            ]
            
            hourly_velocity = len(recent_activities)
            if hourly_velocity > self.anomaly_thresholds['hourly_activity_threshold']:
                await self.track_activity(
                    ActivityType.SYSTEM_ALERT,
                    attorney_id=event.attorney_id,
                    description=f"Unusual activity velocity: {hourly_velocity} activities in last hour",
                    metadata={'velocity': hourly_velocity, 'threshold': self.anomaly_thresholds['hourly_activity_threshold']},
                    severity='warning'
                )
            
            # Check for unusual session duration
            if event.session_id and event.session_id in self.session_tracker:
                session_data = self.session_tracker[event.session_id]
                duration = (event.timestamp - session_data['start_time']).total_seconds()
                
                if duration > self.anomaly_thresholds['session_duration_threshold']:
                    await self.track_activity(
                        ActivityType.SYSTEM_ALERT,
                        attorney_id=event.attorney_id,
                        description=f"Unusually long session: {duration:.0f} seconds",
                        metadata={'duration': duration, 'threshold': self.anomaly_thresholds['session_duration_threshold']},
                        severity='info'
                    )
            
        except Exception as e:
            logger.error(f"Error checking activity anomalies: {e}")