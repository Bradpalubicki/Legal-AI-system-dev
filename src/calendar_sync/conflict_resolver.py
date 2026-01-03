"""
Conflict Detection and Resolution System for CourtSync Calendar

Intelligently detects and resolves scheduling conflicts, double-bookings,
and calendar inconsistencies with automated and manual resolution strategies.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set, Callable
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod
import asyncio
import json

from .hearing_detector import HearingEvent, HearingType, HearingStatus, Location
from .calendar_sync import CalendarEvent

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of calendar conflicts."""
    DOUBLE_BOOKING = "double_booking"           # Multiple events at same time
    OVERLAPPING = "overlapping"                 # Events that overlap in time
    TRAVEL_TIME = "travel_time"                 # Insufficient travel time between locations
    COURT_CLOSURE = "court_closure"             # Event scheduled when court is closed
    ATTORNEY_UNAVAILABLE = "attorney_unavailable"  # Attorney has conflicting commitment
    RESOURCE_CONFLICT = "resource_conflict"     # Courtroom or resource double-booked
    DEADLINE_CONFLICT = "deadline_conflict"     # Hearing conflicts with deadline
    PRIORITY_CONFLICT = "priority_conflict"     # Lower priority event conflicts with higher
    DATE_INCONSISTENCY = "date_inconsistency"   # Different dates for same event across systems
    TIME_INCONSISTENCY = "time_inconsistency"   # Different times for same event
    LOCATION_INCONSISTENCY = "location_inconsistency"  # Different locations for same event
    JUDGE_UNAVAILABLE = "judge_unavailable"     # Judge has conflicting commitment


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""
    CRITICAL = "critical"       # Conflicts that must be resolved immediately
    HIGH = "high"              # Important conflicts that need attention
    MEDIUM = "medium"          # Conflicts that should be addressed
    LOW = "low"                # Minor conflicts that can be monitored
    INFO = "info"              # Informational conflicts


class ResolutionStrategy(Enum):
    """Strategies for conflict resolution."""
    MANUAL_REVIEW = "manual_review"             # Require manual intervention
    AUTO_RESCHEDULE = "auto_reschedule"         # Automatically reschedule lower priority
    PREFER_COURT = "prefer_court"               # Prefer court events over other commitments
    PREFER_RECENT = "prefer_recent"             # Prefer more recently scheduled events
    PREFER_SOURCE = "prefer_source"             # Prefer specific data sources
    NOTIFY_ONLY = "notify_only"                 # Just notify without auto-resolution
    BUFFER_TIME = "buffer_time"                 # Add buffer time between events
    BLOCK_SCHEDULING = "block_scheduling"       # Block conflicting time slots


class ResolutionStatus(Enum):
    """Status of conflict resolution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    ESCALATED = "escalated"
    FAILED = "failed"


@dataclass
class ScheduleConflict:
    """Represents a scheduling conflict."""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    primary_event: Union[HearingEvent, CalendarEvent]
    conflicting_events: List[Union[HearingEvent, CalendarEvent]]
    
    # Conflict details
    description: str
    detected_at: datetime
    location_conflict: bool = False
    time_overlap_minutes: int = 0
    travel_time_required: int = 0  # minutes
    
    # Resolution information
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolution_status: ResolutionStatus = ResolutionStatus.PENDING
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict to dictionary."""
        return {
            'conflict_id': self.conflict_id,
            'conflict_type': self.conflict_type.value,
            'severity': self.severity.value,
            'primary_event': self._event_to_dict(self.primary_event),
            'conflicting_events': [self._event_to_dict(e) for e in self.conflicting_events],
            'description': self.description,
            'detected_at': self.detected_at.isoformat(),
            'location_conflict': self.location_conflict,
            'time_overlap_minutes': self.time_overlap_minutes,
            'travel_time_required': self.travel_time_required,
            'resolution_strategy': self.resolution_strategy.value if self.resolution_strategy else None,
            'resolution_status': self.resolution_status.value,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_notes': self.resolution_notes,
            'metadata': self.metadata
        }
    
    def _event_to_dict(self, event: Union[HearingEvent, CalendarEvent]) -> Dict[str, Any]:
        """Convert event to dictionary."""
        if isinstance(event, HearingEvent):
            return event.to_dict()
        else:
            return event.to_dict()


@dataclass
class ConflictResolutionRule:
    """Rule for automatic conflict resolution."""
    rule_id: str
    name: str
    conflict_types: List[ConflictType]
    conditions: Dict[str, Any]
    strategy: ResolutionStrategy
    priority: int = 100  # Lower numbers = higher priority
    enabled: bool = True
    
    def matches(self, conflict: ScheduleConflict) -> bool:
        """Check if rule matches the conflict."""
        if conflict.conflict_type not in self.conflict_types:
            return False
        
        # Check conditions
        for condition_key, condition_value in self.conditions.items():
            if not self._evaluate_condition(conflict, condition_key, condition_value):
                return False
        
        return True
    
    def _evaluate_condition(self, conflict: ScheduleConflict, key: str, value: Any) -> bool:
        """Evaluate a single condition."""
        if key == "severity":
            return conflict.severity.value in value if isinstance(value, list) else conflict.severity.value == value
        elif key == "time_overlap_max":
            return conflict.time_overlap_minutes <= value
        elif key == "primary_event_type":
            if isinstance(conflict.primary_event, HearingEvent):
                return conflict.primary_event.hearing_type.value in value if isinstance(value, list) else conflict.primary_event.hearing_type.value == value
        elif key == "location_conflict":
            return conflict.location_conflict == value
        
        return True


@dataclass
class TravelTime:
    """Travel time information between locations."""
    from_location: str
    to_location: str
    travel_minutes: int
    transport_mode: str = "driving"  # driving, public_transit, walking
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def is_sufficient_time(self, available_minutes: int, buffer_minutes: int = 15) -> bool:
        """Check if available time is sufficient for travel."""
        return available_minutes >= (self.travel_minutes + buffer_minutes)


class ConflictDetector:
    """Detects various types of calendar conflicts."""
    
    def __init__(self):
        self.travel_times: Dict[str, TravelTime] = {}  # Cache for travel time calculations
        self.court_hours: Dict[str, Tuple[time, time]] = {}  # Court business hours
        self.court_holidays: Dict[str, List[datetime]] = {}  # Court holidays/closures
        self.attorney_schedules: Dict[str, List[Dict[str, Any]]] = {}  # Attorney availability
        
    async def detect_conflicts(self, events: List[Union[HearingEvent, CalendarEvent]],
                              reference_date: Optional[datetime] = None) -> List[ScheduleConflict]:
        """Detect all types of conflicts in the event list."""
        conflicts = []
        
        # Sort events by date for efficient comparison
        sorted_events = sorted(events, key=lambda e: e.start_time if isinstance(e, CalendarEvent) else e.date_time)
        
        # Detect different types of conflicts
        conflicts.extend(await self._detect_time_conflicts(sorted_events))
        conflicts.extend(await self._detect_location_conflicts(sorted_events))
        conflicts.extend(await self._detect_travel_conflicts(sorted_events))
        conflicts.extend(await self._detect_resource_conflicts(sorted_events))
        conflicts.extend(await self._detect_availability_conflicts(sorted_events))
        conflicts.extend(await self._detect_business_hours_conflicts(sorted_events))
        conflicts.extend(await self._detect_data_inconsistencies(sorted_events))
        
        # Remove duplicate conflicts
        unique_conflicts = self._deduplicate_conflicts(conflicts)
        
        logger.info(f"Detected {len(unique_conflicts)} unique conflicts from {len(events)} events")
        return unique_conflicts
    
    async def _detect_time_conflicts(self, events: List[Union[HearingEvent, CalendarEvent]]) -> List[ScheduleConflict]:
        """Detect time-based conflicts (double booking, overlapping)."""
        conflicts = []
        
        for i, event1 in enumerate(events):
            start1 = event1.start_time if isinstance(event1, CalendarEvent) else event1.date_time
            end1 = event1.end_time if isinstance(event1, CalendarEvent) else (event1.end_time or start1 + timedelta(hours=1))
            
            for j, event2 in enumerate(events[i+1:], i+1):
                start2 = event2.start_time if isinstance(event2, CalendarEvent) else event2.date_time
                end2 = event2.end_time if isinstance(event2, CalendarEvent) else (event2.end_time or start2 + timedelta(hours=1))
                
                # Check for overlaps
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                
                if overlap_start < overlap_end:
                    overlap_minutes = int((overlap_end - overlap_start).total_seconds() / 60)
                    
                    # Determine conflict type
                    if start1 == start2 and end1 == end2:
                        conflict_type = ConflictType.DOUBLE_BOOKING
                        severity = ConflictSeverity.CRITICAL
                    else:
                        conflict_type = ConflictType.OVERLAPPING
                        severity = ConflictSeverity.HIGH if overlap_minutes > 30 else ConflictSeverity.MEDIUM
                    
                    conflict = ScheduleConflict(
                        conflict_id=f"time_{hash(f'{start1}_{start2}')}",
                        conflict_type=conflict_type,
                        severity=severity,
                        primary_event=event1,
                        conflicting_events=[event2],
                        description=f"Time conflict: {overlap_minutes} minute overlap",
                        detected_at=datetime.now(),
                        time_overlap_minutes=overlap_minutes
                    )
                    
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_location_conflicts(self, events: List[Union[HearingEvent, CalendarEvent]]) -> List[ScheduleConflict]:
        """Detect location-based conflicts."""
        conflicts = []
        
        # Group events by courtroom/location
        location_events = {}
        
        for event in events:
            location_key = None
            
            if isinstance(event, HearingEvent):
                if event.location and event.location.courtroom:
                    location_key = f"{event.location.court_name}_{event.location.courtroom}"
            elif isinstance(event, CalendarEvent):
                if event.location:
                    location_key = event.location
            
            if location_key:
                if location_key not in location_events:
                    location_events[location_key] = []
                location_events[location_key].append(event)
        
        # Check for conflicts within each location
        for location, location_event_list in location_events.items():
            if len(location_event_list) > 1:
                # Check for time overlaps at the same location
                for i, event1 in enumerate(location_event_list):
                    start1 = event1.start_time if isinstance(event1, CalendarEvent) else event1.date_time
                    end1 = event1.end_time if isinstance(event1, CalendarEvent) else (event1.end_time or start1 + timedelta(hours=1))
                    
                    for event2 in location_event_list[i+1:]:
                        start2 = event2.start_time if isinstance(event2, CalendarEvent) else event2.date_time
                        end2 = event2.end_time if isinstance(event2, CalendarEvent) else (event2.end_time or start2 + timedelta(hours=1))
                        
                        if max(start1, start2) < min(end1, end2):
                            conflict = ScheduleConflict(
                                conflict_id=f"location_{hash(f'{location}_{start1}_{start2}')}",
                                conflict_type=ConflictType.RESOURCE_CONFLICT,
                                severity=ConflictSeverity.HIGH,
                                primary_event=event1,
                                conflicting_events=[event2],
                                description=f"Location conflict at {location}",
                                detected_at=datetime.now(),
                                location_conflict=True
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_travel_conflicts(self, events: List[Union[HearingEvent, CalendarEvent]]) -> List[ScheduleConflict]:
        """Detect conflicts due to insufficient travel time."""
        conflicts = []
        
        for i, event1 in enumerate(events[:-1]):
            event2 = events[i + 1]
            
            # Get event times and locations
            end1 = event1.end_time if isinstance(event1, CalendarEvent) else (event1.end_time or (event1.date_time + timedelta(hours=1)))
            start2 = event2.start_time if isinstance(event2, CalendarEvent) else event2.date_time
            
            available_time = (start2 - end1).total_seconds() / 60  # minutes
            
            # Get locations
            location1 = self._extract_location_string(event1)
            location2 = self._extract_location_string(event2)
            
            if location1 and location2 and location1 != location2:
                # Calculate travel time
                travel_time = await self._get_travel_time(location1, location2)
                
                if travel_time and not travel_time.is_sufficient_time(available_time):
                    conflict = ScheduleConflict(
                        conflict_id=f"travel_{hash(f'{end1}_{start2}')}",
                        conflict_type=ConflictType.TRAVEL_TIME,
                        severity=ConflictSeverity.HIGH,
                        primary_event=event1,
                        conflicting_events=[event2],
                        description=f"Insufficient travel time: {available_time:.0f} min available, {travel_time.travel_minutes} min required",
                        detected_at=datetime.now(),
                        travel_time_required=travel_time.travel_minutes
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_resource_conflicts(self, events: List[Union[HearingEvent, CalendarEvent]]) -> List[ScheduleConflict]:
        """Detect resource conflicts (judge, attorney availability)."""
        conflicts = []
        
        # Group events by judge
        judge_events = {}
        for event in events:
            if isinstance(event, HearingEvent) and event.judge:
                judge = event.judge
                if judge not in judge_events:
                    judge_events[judge] = []
                judge_events[judge].append(event)
        
        # Check for judge conflicts
        for judge, judge_event_list in judge_events.items():
            if len(judge_event_list) > 1:
                for i, event1 in enumerate(judge_event_list):
                    for event2 in judge_event_list[i+1:]:
                        # Check for time overlap
                        start1, end1 = event1.date_time, event1.end_time or event1.date_time + timedelta(hours=1)
                        start2, end2 = event2.date_time, event2.end_time or event2.date_time + timedelta(hours=1)
                        
                        if max(start1, start2) < min(end1, end2):
                            conflict = ScheduleConflict(
                                conflict_id=f"judge_{hash(f'{judge}_{start1}_{start2}')}",
                                conflict_type=ConflictType.JUDGE_UNAVAILABLE,
                                severity=ConflictSeverity.CRITICAL,
                                primary_event=event1,
                                conflicting_events=[event2],
                                description=f"Judge {judge} double-booked",
                                detected_at=datetime.now(),
                                metadata={'judge': judge}
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_availability_conflicts(self, events: List[Union[HearingEvent, CalendarEvent]]) -> List[ScheduleConflict]:
        """Detect attorney availability conflicts."""
        conflicts = []
        
        # This would check against external attorney calendars
        # For now, it's a placeholder that would integrate with calendar systems
        
        for event in events:
            if isinstance(event, HearingEvent) and event.attorneys:
                for attorney in event.attorneys:
                    # Check attorney schedule (placeholder)
                    attorney_conflicts = await self._check_attorney_availability(
                        attorney, 
                        event.date_time, 
                        event.end_time or event.date_time + timedelta(hours=1)
                    )
                    
                    for conflict_event in attorney_conflicts:
                        conflict = ScheduleConflict(
                            conflict_id=f"attorney_{hash(f'{attorney}_{event.date_time}')}",
                            conflict_type=ConflictType.ATTORNEY_UNAVAILABLE,
                            severity=ConflictSeverity.HIGH,
                            primary_event=event,
                            conflicting_events=[conflict_event],
                            description=f"Attorney {attorney} unavailable",
                            detected_at=datetime.now(),
                            metadata={'attorney': attorney}
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_business_hours_conflicts(self, events: List[Union[HearingEvent, CalendarEvent]]) -> List[ScheduleConflict]:
        """Detect events scheduled outside business hours."""
        conflicts = []
        
        for event in events:
            event_time = event.start_time if isinstance(event, CalendarEvent) else event.date_time
            
            # Check if event is during business hours
            court_id = getattr(event, 'court_id', None) or 'default'
            business_hours = self.court_hours.get(court_id, (time(9, 0), time(17, 0)))  # Default 9-5
            
            event_time_only = event_time.time()
            
            if event_time_only < business_hours[0] or event_time_only > business_hours[1]:
                conflict = ScheduleConflict(
                    conflict_id=f"hours_{hash(str(event_time))}",
                    conflict_type=ConflictType.COURT_CLOSURE,
                    severity=ConflictSeverity.MEDIUM,
                    primary_event=event,
                    conflicting_events=[],
                    description=f"Event scheduled outside business hours: {event_time_only}",
                    detected_at=datetime.now()
                )
                conflicts.append(conflict)
            
            # Check if event is on a holiday
            court_holidays = self.court_holidays.get(court_id, [])
            event_date = event_time.date()
            
            for holiday in court_holidays:
                if holiday.date() == event_date:
                    conflict = ScheduleConflict(
                        conflict_id=f"holiday_{hash(str(event_time))}",
                        conflict_type=ConflictType.COURT_CLOSURE,
                        severity=ConflictSeverity.HIGH,
                        primary_event=event,
                        conflicting_events=[],
                        description=f"Event scheduled on court holiday: {holiday.strftime('%Y-%m-%d')}",
                        detected_at=datetime.now()
                    )
                    conflicts.append(conflict)
                    break
        
        return conflicts
    
    async def _detect_data_inconsistencies(self, events: List[Union[HearingEvent, CalendarEvent]]) -> List[ScheduleConflict]:
        """Detect inconsistencies in event data across sources."""
        conflicts = []
        
        # Group events by case number
        case_events = {}
        for event in events:
            case_number = None
            if isinstance(event, HearingEvent):
                case_number = event.case_number
            elif isinstance(event, CalendarEvent):
                case_number = event.case_id
            
            if case_number and case_number != "UNKNOWN":
                if case_number not in case_events:
                    case_events[case_number] = []
                case_events[case_number].append(event)
        
        # Check for inconsistencies within each case
        for case_number, case_event_list in case_events.items():
            if len(case_event_list) > 1:
                # Check for date/time inconsistencies
                for i, event1 in enumerate(case_event_list):
                    for event2 in case_event_list[i+1:]:
                        time1 = event1.start_time if isinstance(event1, CalendarEvent) else event1.date_time
                        time2 = event2.start_time if isinstance(event2, CalendarEvent) else event2.date_time
                        
                        time_diff = abs((time1 - time2).total_seconds())
                        
                        # Same event but different times (more than 15 minutes difference)
                        if time_diff > 900 and time_diff < 3600:  # 15 minutes to 1 hour
                            conflict_type = ConflictType.TIME_INCONSISTENCY
                            if time1.date() != time2.date():
                                conflict_type = ConflictType.DATE_INCONSISTENCY
                            
                            conflict = ScheduleConflict(
                                conflict_id=f"inconsistency_{hash(f'{case_number}_{time1}_{time2}')}",
                                conflict_type=conflict_type,
                                severity=ConflictSeverity.HIGH,
                                primary_event=event1,
                                conflicting_events=[event2],
                                description=f"Data inconsistency for case {case_number}: {time_diff/60:.1f} minute difference",
                                detected_at=datetime.now()
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    def _extract_location_string(self, event: Union[HearingEvent, CalendarEvent]) -> Optional[str]:
        """Extract location string from event."""
        if isinstance(event, HearingEvent):
            if event.location:
                return f"{event.location.court_name}, {event.location.address or ''}"
        elif isinstance(event, CalendarEvent):
            return event.location
        return None
    
    async def _get_travel_time(self, location1: str, location2: str) -> Optional[TravelTime]:
        """Get travel time between two locations."""
        cache_key = f"{location1}|{location2}"
        
        # Check cache first
        if cache_key in self.travel_times:
            travel_time = self.travel_times[cache_key]
            # Check if cached data is still valid (less than 1 day old)
            if datetime.now() - travel_time.calculated_at < timedelta(days=1):
                return travel_time
        
        # Calculate travel time (placeholder - would use Google Maps API or similar)
        # For now, use a simple heuristic based on location strings
        estimated_time = self._estimate_travel_time(location1, location2)
        
        travel_time = TravelTime(
            from_location=location1,
            to_location=location2,
            travel_minutes=estimated_time
        )
        
        # Cache the result
        self.travel_times[cache_key] = travel_time
        
        return travel_time
    
    def _estimate_travel_time(self, location1: str, location2: str) -> int:
        """Simple travel time estimation (placeholder for real implementation)."""
        # This is a very basic estimation - in practice, you'd use a mapping service
        if location1 == location2:
            return 0
        
        # Check if same building/court complex
        if "courthouse" in location1.lower() and "courthouse" in location2.lower():
            if location1.split(",")[0] == location2.split(",")[0]:  # Same court building
                return 10  # 10 minutes to move between courtrooms
        
        # Default estimates based on typical travel times
        return 30  # 30 minutes default travel time
    
    async def _check_attorney_availability(self, attorney: str, start_time: datetime, 
                                         end_time: datetime) -> List[CalendarEvent]:
        """Check attorney availability (placeholder)."""
        # This would integrate with attorney calendar systems
        # For now, return empty list (no conflicts)
        return []
    
    def _deduplicate_conflicts(self, conflicts: List[ScheduleConflict]) -> List[ScheduleConflict]:
        """Remove duplicate conflicts."""
        seen = set()
        unique_conflicts = []
        
        for conflict in conflicts:
            # Create a signature based on conflict type and involved events
            event_ids = [self._get_event_id(conflict.primary_event)]
            event_ids.extend([self._get_event_id(e) for e in conflict.conflicting_events])
            event_ids.sort()  # Ensure consistent ordering
            
            signature = f"{conflict.conflict_type.value}:{':'.join(event_ids)}"
            
            if signature not in seen:
                seen.add(signature)
                unique_conflicts.append(conflict)
        
        return unique_conflicts
    
    def _get_event_id(self, event: Union[HearingEvent, CalendarEvent]) -> str:
        """Get unique ID for an event."""
        if isinstance(event, HearingEvent):
            return event.hearing_id
        elif isinstance(event, CalendarEvent):
            return event.external_event_id or str(hash(event.title + str(event.start_time)))
        return str(hash(str(event)))
    
    def set_court_hours(self, court_id: str, start_time: time, end_time: time):
        """Set business hours for a court."""
        self.court_hours[court_id] = (start_time, end_time)
    
    def set_court_holidays(self, court_id: str, holidays: List[datetime]):
        """Set holidays/closures for a court."""
        self.court_holidays[court_id] = holidays
    
    def add_attorney_schedule(self, attorney: str, schedule: List[Dict[str, Any]]):
        """Add attorney schedule information."""
        self.attorney_schedules[attorney] = schedule


class ConflictResolver:
    """Resolves calendar conflicts using various strategies."""
    
    def __init__(self):
        self.resolution_rules: List[ConflictResolutionRule] = []
        self.resolution_callbacks: Dict[ResolutionStrategy, Callable] = {}
        self.pending_conflicts: Dict[str, ScheduleConflict] = {}
        self.resolved_conflicts: Dict[str, ScheduleConflict] = {}
        
        self._setup_default_rules()
        self._setup_resolution_callbacks()
    
    def _setup_default_rules(self):
        """Set up default conflict resolution rules."""
        default_rules = [
            # Critical double bookings - require manual review
            ConflictResolutionRule(
                rule_id="critical_double_booking",
                name="Critical Double Booking",
                conflict_types=[ConflictType.DOUBLE_BOOKING],
                conditions={"severity": "critical"},
                strategy=ResolutionStrategy.MANUAL_REVIEW,
                priority=1
            ),
            
            # Judge conflicts - prefer court events
            ConflictResolutionRule(
                rule_id="judge_unavailable",
                name="Judge Unavailable",
                conflict_types=[ConflictType.JUDGE_UNAVAILABLE],
                conditions={},
                strategy=ResolutionStrategy.PREFER_COURT,
                priority=2
            ),
            
            # Travel time conflicts - add buffer
            ConflictResolutionRule(
                rule_id="travel_time",
                name="Insufficient Travel Time",
                conflict_types=[ConflictType.TRAVEL_TIME],
                conditions={},
                strategy=ResolutionStrategy.BUFFER_TIME,
                priority=3
            ),
            
            # Resource conflicts - reschedule lower priority
            ConflictResolutionRule(
                rule_id="resource_conflict",
                name="Resource Conflict",
                conflict_types=[ConflictType.RESOURCE_CONFLICT],
                conditions={"severity": ["high", "medium"]},
                strategy=ResolutionStrategy.AUTO_RESCHEDULE,
                priority=4
            ),
            
            # Business hours violations - notify only
            ConflictResolutionRule(
                rule_id="business_hours",
                name="Business Hours Violation",
                conflict_types=[ConflictType.COURT_CLOSURE],
                conditions={},
                strategy=ResolutionStrategy.NOTIFY_ONLY,
                priority=5
            ),
            
            # Data inconsistencies - prefer most recent
            ConflictResolutionRule(
                rule_id="data_inconsistency",
                name="Data Inconsistency",
                conflict_types=[ConflictType.TIME_INCONSISTENCY, ConflictType.DATE_INCONSISTENCY],
                conditions={},
                strategy=ResolutionStrategy.PREFER_RECENT,
                priority=6
            )
        ]
        
        self.resolution_rules.extend(default_rules)
        self.resolution_rules.sort(key=lambda r: r.priority)
    
    def _setup_resolution_callbacks(self):
        """Set up resolution strategy callbacks."""
        self.resolution_callbacks = {
            ResolutionStrategy.MANUAL_REVIEW: self._resolve_manual_review,
            ResolutionStrategy.AUTO_RESCHEDULE: self._resolve_auto_reschedule,
            ResolutionStrategy.PREFER_COURT: self._resolve_prefer_court,
            ResolutionStrategy.PREFER_RECENT: self._resolve_prefer_recent,
            ResolutionStrategy.NOTIFY_ONLY: self._resolve_notify_only,
            ResolutionStrategy.BUFFER_TIME: self._resolve_buffer_time,
            ResolutionStrategy.BLOCK_SCHEDULING: self._resolve_block_scheduling
        }
    
    def add_resolution_rule(self, rule: ConflictResolutionRule):
        """Add a custom resolution rule."""
        self.resolution_rules.append(rule)
        self.resolution_rules.sort(key=lambda r: r.priority)
    
    async def resolve_conflicts(self, conflicts: List[ScheduleConflict]) -> Dict[str, ResolutionStatus]:
        """Resolve a list of conflicts."""
        resolution_results = {}
        
        # Add conflicts to pending queue
        for conflict in conflicts:
            self.pending_conflicts[conflict.conflict_id] = conflict
        
        # Process conflicts
        for conflict in conflicts:
            try:
                result = await self._resolve_conflict(conflict)
                resolution_results[conflict.conflict_id] = result
                
                # Move to resolved if successful
                if result == ResolutionStatus.RESOLVED:
                    self.resolved_conflicts[conflict.conflict_id] = conflict
                    del self.pending_conflicts[conflict.conflict_id]
            
            except Exception as e:
                logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {str(e)}")
                resolution_results[conflict.conflict_id] = ResolutionStatus.FAILED
                conflict.resolution_status = ResolutionStatus.FAILED
        
        return resolution_results
    
    async def _resolve_conflict(self, conflict: ScheduleConflict) -> ResolutionStatus:
        """Resolve a single conflict."""
        # Find applicable resolution rule
        applicable_rule = None
        for rule in self.resolution_rules:
            if rule.enabled and rule.matches(conflict):
                applicable_rule = rule
                break
        
        if not applicable_rule:
            logger.warning(f"No resolution rule found for conflict {conflict.conflict_id}")
            conflict.resolution_strategy = ResolutionStrategy.MANUAL_REVIEW
            conflict.resolution_status = ResolutionStatus.ESCALATED
            return ResolutionStatus.ESCALATED
        
        # Apply resolution strategy
        conflict.resolution_strategy = applicable_rule.strategy
        conflict.resolution_status = ResolutionStatus.IN_PROGRESS
        
        resolution_callback = self.resolution_callbacks.get(applicable_rule.strategy)
        if resolution_callback:
            try:
                success = await resolution_callback(conflict)
                if success:
                    conflict.resolution_status = ResolutionStatus.RESOLVED
                    conflict.resolved_at = datetime.now()
                    conflict.resolved_by = f"auto_resolver_{applicable_rule.rule_id}"
                    return ResolutionStatus.RESOLVED
                else:
                    conflict.resolution_status = ResolutionStatus.FAILED
                    return ResolutionStatus.FAILED
            
            except Exception as e:
                logger.error(f"Resolution callback failed: {str(e)}")
                conflict.resolution_status = ResolutionStatus.FAILED
                return ResolutionStatus.FAILED
        
        else:
            conflict.resolution_status = ResolutionStatus.MANUAL_REVIEW
            return ResolutionStatus.MANUAL_REVIEW
    
    async def _resolve_manual_review(self, conflict: ScheduleConflict) -> bool:
        """Handle conflicts requiring manual review."""
        # Flag for manual review - don't auto-resolve
        logger.info(f"Conflict {conflict.conflict_id} flagged for manual review")
        conflict.resolution_notes = "Flagged for manual review due to complexity or severity"
        
        # Could trigger notifications here
        await self._notify_conflict_managers(conflict)
        
        return False  # Not automatically resolved
    
    async def _resolve_auto_reschedule(self, conflict: ScheduleConflict) -> bool:
        """Automatically reschedule lower priority events."""
        # Identify which event to reschedule
        primary_priority = self._get_event_priority(conflict.primary_event)
        conflicting_priorities = [self._get_event_priority(e) for e in conflict.conflicting_events]
        
        # Find lowest priority event
        lowest_priority = min([primary_priority] + conflicting_priorities)
        
        if primary_priority == lowest_priority:
            event_to_reschedule = conflict.primary_event
        else:
            # Find the conflicting event with lowest priority
            for i, priority in enumerate(conflicting_priorities):
                if priority == lowest_priority:
                    event_to_reschedule = conflict.conflicting_events[i]
                    break
        
        # Attempt to reschedule
        new_time = await self._find_alternative_time(event_to_reschedule, conflict)
        
        if new_time:
            await self._reschedule_event(event_to_reschedule, new_time)
            conflict.resolution_notes = f"Rescheduled event to {new_time}"
            logger.info(f"Auto-rescheduled event in conflict {conflict.conflict_id}")
            return True
        else:
            conflict.resolution_notes = "Could not find suitable alternative time"
            return False
    
    async def _resolve_prefer_court(self, conflict: ScheduleConflict) -> bool:
        """Resolve by preferring court events over other commitments."""
        # Identify court events vs other events
        court_events = []
        other_events = []
        
        all_events = [conflict.primary_event] + conflict.conflicting_events
        for event in all_events:
            if isinstance(event, HearingEvent):
                court_events.append(event)
            else:
                other_events.append(event)
        
        # Reschedule non-court events
        for event in other_events:
            new_time = await self._find_alternative_time(event, conflict)
            if new_time:
                await self._reschedule_event(event, new_time)
        
        conflict.resolution_notes = f"Preferred court events, rescheduled {len(other_events)} non-court events"
        return len(other_events) > 0
    
    async def _resolve_prefer_recent(self, conflict: ScheduleConflict) -> bool:
        """Resolve by preferring more recently created/updated events."""
        all_events = [conflict.primary_event] + conflict.conflicting_events
        
        # Find most recent event
        most_recent = max(all_events, key=lambda e: getattr(e, 'updated_at', getattr(e, 'created_at', datetime.min)))
        
        # Reschedule other events
        events_to_reschedule = [e for e in all_events if e != most_recent]
        
        rescheduled_count = 0
        for event in events_to_reschedule:
            new_time = await self._find_alternative_time(event, conflict)
            if new_time:
                await self._reschedule_event(event, new_time)
                rescheduled_count += 1
        
        conflict.resolution_notes = f"Preferred most recent event, rescheduled {rescheduled_count} others"
        return rescheduled_count > 0
    
    async def _resolve_notify_only(self, conflict: ScheduleConflict) -> bool:
        """Resolve by notification only (no automatic changes)."""
        await self._notify_conflict_managers(conflict)
        conflict.resolution_notes = "Stakeholders notified, no automatic changes made"
        logger.info(f"Sent notifications for conflict {conflict.conflict_id}")
        return True
    
    async def _resolve_buffer_time(self, conflict: ScheduleConflict) -> bool:
        """Resolve by adding buffer time between events."""
        if conflict.conflict_type != ConflictType.TRAVEL_TIME:
            return False
        
        # Calculate required buffer
        required_buffer = conflict.travel_time_required + 15  # Add 15 min extra buffer
        
        # Adjust the later event
        all_events = [conflict.primary_event] + conflict.conflicting_events
        sorted_events = sorted(all_events, key=lambda e: e.start_time if isinstance(e, CalendarEvent) else e.date_time)
        
        later_event = sorted_events[-1]
        earlier_event = sorted_events[0]
        
        # Calculate new start time for later event
        end_time = earlier_event.end_time if isinstance(earlier_event, CalendarEvent) else (earlier_event.end_time or earlier_event.date_time + timedelta(hours=1))
        new_start_time = end_time + timedelta(minutes=required_buffer)
        
        # Reschedule later event
        await self._reschedule_event(later_event, new_start_time)
        
        conflict.resolution_notes = f"Added {required_buffer} minute buffer between events"
        return True
    
    async def _resolve_block_scheduling(self, conflict: ScheduleConflict) -> bool:
        """Resolve by blocking conflicting time slots."""
        # This would integrate with scheduling systems to block time slots
        # For now, just log the action
        conflict.resolution_notes = "Time slots blocked to prevent future conflicts"
        logger.info(f"Blocked time slots for conflict {conflict.conflict_id}")
        return True
    
    def _get_event_priority(self, event: Union[HearingEvent, CalendarEvent]) -> int:
        """Get event priority for comparison (lower number = higher priority)."""
        if isinstance(event, HearingEvent):
            priority_map = {
                HearingType.TRIAL: 1,
                HearingType.HEARING: 2,
                HearingType.MOTION_HEARING: 3,
                HearingType.ORAL_ARGUMENT: 4,
                HearingType.PRETRIAL_CONFERENCE: 5,
                HearingType.STATUS_CONFERENCE: 6,
                HearingType.SETTLEMENT_CONFERENCE: 7,
                HearingType.DEPOSITION: 8
            }
            return priority_map.get(event.hearing_type, 9)
        elif isinstance(event, CalendarEvent):
            priority_map = {
                'critical': 1,
                'high': 2,
                'medium': 3,
                'low': 4
            }
            return priority_map.get(event.priority, 5)
        
        return 10  # Default lowest priority
    
    async def _find_alternative_time(self, event: Union[HearingEvent, CalendarEvent],
                                   conflict: ScheduleConflict) -> Optional[datetime]:
        """Find an alternative time for rescheduling an event."""
        # This is a simplified implementation
        # In practice, this would integrate with availability systems
        
        current_time = event.start_time if isinstance(event, CalendarEvent) else event.date_time
        
        # Try scheduling 1 hour later first
        alternative_times = [
            current_time + timedelta(hours=1),
            current_time + timedelta(hours=2),
            current_time + timedelta(days=1),
            current_time + timedelta(days=2)
        ]
        
        # Return first available time (placeholder logic)
        for alt_time in alternative_times:
            # Check if time is during business hours
            if 9 <= alt_time.hour <= 17:  # Basic business hours check
                return alt_time
        
        return None
    
    async def _reschedule_event(self, event: Union[HearingEvent, CalendarEvent],
                               new_time: datetime):
        """Reschedule an event to a new time."""
        # This would integrate with calendar systems to actually reschedule
        # For now, just update the event object
        
        if isinstance(event, CalendarEvent):
            duration = event.end_time - event.start_time if event.end_time else timedelta(hours=1)
            event.start_time = new_time
            event.end_time = new_time + duration
        elif isinstance(event, HearingEvent):
            duration = event.end_time - event.date_time if event.end_time else timedelta(hours=1)
            event.date_time = new_time
            event.end_time = new_time + duration
        
        logger.info(f"Rescheduled event to {new_time}")
    
    async def _notify_conflict_managers(self, conflict: ScheduleConflict):
        """Send notifications about conflicts to relevant stakeholders."""
        # This would integrate with notification systems
        # For now, just log
        logger.info(f"Notification sent for conflict {conflict.conflict_id}: {conflict.description}")
    
    def get_pending_conflicts(self) -> List[ScheduleConflict]:
        """Get all pending conflicts."""
        return list(self.pending_conflicts.values())
    
    def get_resolved_conflicts(self) -> List[ScheduleConflict]:
        """Get all resolved conflicts."""
        return list(self.resolved_conflicts.values())
    
    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get conflict resolution statistics."""
        total_conflicts = len(self.pending_conflicts) + len(self.resolved_conflicts)
        
        if total_conflicts == 0:
            return {'total': 0, 'pending': 0, 'resolved': 0, 'resolution_rate': 0}
        
        return {
            'total': total_conflicts,
            'pending': len(self.pending_conflicts),
            'resolved': len(self.resolved_conflicts),
            'resolution_rate': len(self.resolved_conflicts) / total_conflicts * 100,
            'by_type': self._get_conflicts_by_type(),
            'by_severity': self._get_conflicts_by_severity(),
            'by_strategy': self._get_conflicts_by_strategy()
        }
    
    def _get_conflicts_by_type(self) -> Dict[str, int]:
        """Get conflict counts by type."""
        type_counts = {}
        all_conflicts = list(self.pending_conflicts.values()) + list(self.resolved_conflicts.values())
        
        for conflict in all_conflicts:
            conflict_type = conflict.conflict_type.value
            type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1
        
        return type_counts
    
    def _get_conflicts_by_severity(self) -> Dict[str, int]:
        """Get conflict counts by severity."""
        severity_counts = {}
        all_conflicts = list(self.pending_conflicts.values()) + list(self.resolved_conflicts.values())
        
        for conflict in all_conflicts:
            severity = conflict.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return severity_counts
    
    def _get_conflicts_by_strategy(self) -> Dict[str, int]:
        """Get conflict counts by resolution strategy."""
        strategy_counts = {}
        all_conflicts = list(self.pending_conflicts.values()) + list(self.resolved_conflicts.values())
        
        for conflict in all_conflicts:
            if conflict.resolution_strategy:
                strategy = conflict.resolution_strategy.value
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return strategy_counts


# Example usage
async def example_usage():
    """Example usage of conflict detection and resolution."""
    
    # Create sample events with conflicts
    events = [
        # Double booking
        HearingEvent(
            hearing_id="hearing_1",
            case_number="CASE001",
            case_title="Smith v. Jones",
            hearing_type=HearingType.MOTION_HEARING,
            date_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
            judge="Judge Johnson",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="hearing_2",
            case_number="CASE002", 
            case_title="Brown v. Davis",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 15, 10, 30),  # Overlapping
            end_time=datetime(2024, 1, 15, 11, 30),
            judge="Judge Johnson",  # Same judge
            status=HearingStatus.SCHEDULED
        ),
        # Travel time conflict
        HearingEvent(
            hearing_id="hearing_3",
            case_number="CASE003",
            case_title="Wilson v. Taylor",
            hearing_type=HearingType.HEARING,
            date_time=datetime(2024, 1, 15, 12, 0),
            end_time=datetime(2024, 1, 15, 13, 0),
            location=Location(court_name="Downtown Courthouse", address="123 Main St"),
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="hearing_4",
            case_number="CASE004",
            case_title="Miller v. Anderson",
            hearing_type=HearingType.HEARING,
            date_time=datetime(2024, 1, 15, 13, 15),  # Only 15 min gap
            end_time=datetime(2024, 1, 15, 14, 15),
            location=Location(court_name="Uptown Courthouse", address="456 Oak Ave"),
            status=HearingStatus.SCHEDULED
        )
    ]
    
    # Initialize conflict detector
    detector = ConflictDetector()
    
    # Set court business hours
    detector.set_court_hours("default", time(9, 0), time(17, 0))
    
    # Detect conflicts
    conflicts = await detector.detect_conflicts(events)
    
    print(f"Detected {len(conflicts)} conflicts:")
    for conflict in conflicts:
        print(f"- {conflict.conflict_type.value}: {conflict.description}")
        print(f"  Severity: {conflict.severity.value}")
        print(f"  Primary event: {conflict.primary_event.case_title if isinstance(conflict.primary_event, HearingEvent) else conflict.primary_event.title}")
        print(f"  Conflicting events: {len(conflict.conflicting_events)}")
        print()
    
    # Initialize conflict resolver
    resolver = ConflictResolver()
    
    # Resolve conflicts
    resolution_results = await resolver.resolve_conflicts(conflicts)
    
    print("Resolution results:")
    for conflict_id, status in resolution_results.items():
        conflict = resolver.pending_conflicts.get(conflict_id) or resolver.resolved_conflicts.get(conflict_id)
        if conflict:
            print(f"- {conflict.conflict_type.value}: {status.value}")
            if conflict.resolution_notes:
                print(f"  Notes: {conflict.resolution_notes}")
    
    # Get statistics
    stats = resolver.get_conflict_stats()
    print(f"\nConflict statistics:")
    print(f"- Total conflicts: {stats['total']}")
    print(f"- Resolved: {stats['resolved']}")
    print(f"- Pending: {stats['pending']}")
    print(f"- Resolution rate: {stats['resolution_rate']:.1f}%")


if __name__ == "__main__":
    asyncio.run(example_usage())