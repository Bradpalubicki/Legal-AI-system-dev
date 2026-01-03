"""
Advanced Conflict Detection System

Enhanced conflict detection with sophisticated algorithms for legal calendar management,
including predictive conflict analysis, resource optimization, and intelligent scheduling.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import json
from abc import ABC, abstractmethod
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import networkx as nx

from .hearing_detector import HearingEvent, HearingType, HearingStatus, Location
from .conflict_resolver import ScheduleConflict, ConflictType, ConflictSeverity

logger = logging.getLogger(__name__)


class ConflictPredictionModel(Enum):
    """Models for predicting conflicts."""
    RULE_BASED = "rule_based"
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"


class ResourceType(Enum):
    """Types of legal resources that can conflict."""
    JUDGE = "judge"
    COURTROOM = "courtroom"
    ATTORNEY = "attorney"
    CLIENT = "client"
    COURT_REPORTER = "court_reporter"
    INTERPRETER = "interpreter"
    WITNESS = "witness"
    EQUIPMENT = "equipment"
    PARKING = "parking"


@dataclass
class ResourceRequirement:
    """Represents a resource requirement for an event."""
    resource_type: ResourceType
    resource_id: str
    resource_name: str
    required_from: datetime
    required_until: datetime
    criticality: str = "required"  # required, preferred, optional
    setup_time_minutes: int = 0
    cleanup_time_minutes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConflictPattern:
    """Represents a pattern of conflicts for analysis."""
    pattern_id: str
    pattern_type: str
    frequency: int
    locations: List[str]
    time_patterns: List[str]
    resource_conflicts: List[ResourceType]
    severity_distribution: Dict[ConflictSeverity, int]
    resolution_success_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulingConstraint:
    """Represents scheduling constraints and preferences."""
    constraint_id: str
    constraint_type: str  # hard, soft, preference
    description: str
    applies_to: List[str]  # event types, locations, resources
    time_restrictions: Optional[Dict[str, Any]] = None
    resource_restrictions: Optional[Dict[str, Any]] = None
    priority_weight: float = 1.0
    violation_penalty: float = 100.0


class AdvancedConflictDetector:
    """Enhanced conflict detection with predictive capabilities."""
    
    def __init__(self):
        self.conflict_history: List[ScheduleConflict] = []
        self.resource_registry: Dict[str, Dict[str, Any]] = {}
        self.scheduling_constraints: List[SchedulingConstraint] = []
        self.conflict_patterns: List[ConflictPattern] = []
        self.prediction_model = ConflictPredictionModel.HYBRID
        
        # Enhanced detection parameters
        self.time_buffer_matrix = self._initialize_time_buffers()
        self.resource_dependencies = self._initialize_resource_dependencies()
        self.location_clusters = {}
        self.temporal_patterns = {}
        
        self._setup_default_constraints()
    
    def _initialize_time_buffers(self) -> Dict[Tuple[HearingType, HearingType], int]:
        """Initialize time buffer requirements between different hearing types."""
        return {
            # High-priority transitions requiring longer buffers
            (HearingType.TRIAL, HearingType.TRIAL): 60,  # 1 hour between trials
            (HearingType.TRIAL, HearingType.MOTION_HEARING): 30,
            (HearingType.MOTION_HEARING, HearingType.TRIAL): 45,
            
            # Standard transitions
            (HearingType.MOTION_HEARING, HearingType.MOTION_HEARING): 20,
            (HearingType.STATUS_CONFERENCE, HearingType.MOTION_HEARING): 15,
            (HearingType.DEPOSITION, HearingType.HEARING): 30,
            
            # Quick transitions for similar event types
            (HearingType.STATUS_CONFERENCE, HearingType.STATUS_CONFERENCE): 10,
            (HearingType.CASE_MANAGEMENT, HearingType.STATUS_CONFERENCE): 10,
        }
    
    def _initialize_resource_dependencies(self) -> Dict[ResourceType, List[ResourceType]]:
        """Initialize resource dependencies (resources that must be available together)."""
        return {
            ResourceType.JUDGE: [ResourceType.COURTROOM, ResourceType.COURT_REPORTER],
            ResourceType.COURTROOM: [ResourceType.JUDGE],
            ResourceType.COURT_REPORTER: [ResourceType.JUDGE, ResourceType.COURTROOM],
            ResourceType.INTERPRETER: [ResourceType.JUDGE, ResourceType.COURTROOM],
            ResourceType.ATTORNEY: [],
            ResourceType.CLIENT: [ResourceType.ATTORNEY],
            ResourceType.WITNESS: [],
            ResourceType.EQUIPMENT: [ResourceType.COURTROOM],
            ResourceType.PARKING: []
        }
    
    def _setup_default_constraints(self):
        """Set up default scheduling constraints."""
        default_constraints = [
            SchedulingConstraint(
                constraint_id="no_back_to_back_trials",
                constraint_type="hard",
                description="Trials cannot be scheduled back-to-back",
                applies_to=["trial"],
                time_restrictions={"min_gap_minutes": 60},
                violation_penalty=1000.0
            ),
            SchedulingConstraint(
                constraint_id="lunch_break_protection",
                constraint_type="soft",
                description="Protect lunch hours (12-1 PM)",
                applies_to=["all"],
                time_restrictions={
                    "protected_hours": [(time(12, 0), time(13, 0))]
                },
                violation_penalty=50.0
            ),
            SchedulingConstraint(
                constraint_id="judge_daily_limit",
                constraint_type="soft",
                description="Judges should not have more than 8 hearings per day",
                applies_to=["judge"],
                resource_restrictions={"max_daily_events": 8},
                violation_penalty=75.0
            ),
            SchedulingConstraint(
                constraint_id="same_building_preference",
                constraint_type="preference",
                description="Prefer scheduling consecutive hearings in same building",
                applies_to=["all"],
                priority_weight=0.3,
                violation_penalty=10.0
            )
        ]
        
        self.scheduling_constraints.extend(default_constraints)
    
    async def detect_advanced_conflicts(self, events: List[HearingEvent],
                                      prediction_horizon_days: int = 30) -> List[ScheduleConflict]:
        """Detect conflicts using advanced algorithms and predictive analysis."""
        conflicts = []
        
        # Basic conflict detection
        basic_conflicts = await self._detect_basic_conflicts(events)
        conflicts.extend(basic_conflicts)
        
        # Resource-based conflict detection
        resource_conflicts = await self._detect_resource_conflicts(events)
        conflicts.extend(resource_conflicts)
        
        # Pattern-based conflict detection
        pattern_conflicts = await self._detect_pattern_conflicts(events)
        conflicts.extend(pattern_conflicts)
        
        # Predictive conflict detection
        if prediction_horizon_days > 0:
            predictive_conflicts = await self._detect_predictive_conflicts(
                events, prediction_horizon_days
            )
            conflicts.extend(predictive_conflicts)
        
        # Constraint violation detection
        constraint_conflicts = await self._detect_constraint_violations(events)
        conflicts.extend(constraint_conflicts)
        
        # Clustering-based conflict detection
        cluster_conflicts = await self._detect_cluster_conflicts(events)
        conflicts.extend(cluster_conflicts)
        
        # Remove duplicates and rank by severity
        unique_conflicts = self._deduplicate_and_rank_conflicts(conflicts)
        
        logger.info(f"Advanced conflict detection found {len(unique_conflicts)} conflicts")
        return unique_conflicts
    
    async def _detect_basic_conflicts(self, events: List[HearingEvent]) -> List[ScheduleConflict]:
        """Enhanced basic time-based conflict detection."""
        conflicts = []
        
        # Sort events by time
        sorted_events = sorted(events, key=lambda e: e.date_time)
        
        for i, event1 in enumerate(sorted_events):
            for j, event2 in enumerate(sorted_events[i+1:], i+1):
                # Calculate time overlap
                overlap_info = self._calculate_time_overlap(event1, event2)
                
                if overlap_info['overlap_minutes'] > 0:
                    # Determine conflict severity based on overlap and event types
                    severity = self._calculate_conflict_severity(
                        event1, event2, overlap_info['overlap_minutes']
                    )
                    
                    # Get required buffer time
                    required_buffer = self._get_required_buffer_time(event1, event2)
                    
                    conflict = ScheduleConflict(
                        conflict_id=f"time_conflict_{event1.hearing_id}_{event2.hearing_id}",
                        conflict_type=ConflictType.OVERLAPPING if overlap_info['overlap_minutes'] < 60 else ConflictType.DOUBLE_BOOKING,
                        severity=severity,
                        primary_event=event1,
                        conflicting_events=[event2],
                        description=f"Time conflict: {overlap_info['overlap_minutes']} minute overlap, requires {required_buffer} minute buffer",
                        detected_at=datetime.now(),
                        time_overlap_minutes=overlap_info['overlap_minutes'],
                        metadata={
                            'required_buffer_minutes': required_buffer,
                            'gap_minutes': overlap_info['gap_minutes'],
                            'conflict_score': overlap_info['overlap_minutes'] / required_buffer
                        }
                    )
                    
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_resource_conflicts(self, events: List[HearingEvent]) -> List[ScheduleConflict]:
        """Detect conflicts based on resource availability."""
        conflicts = []
        resource_bookings: Dict[str, List[Tuple[HearingEvent, datetime, datetime]]] = {}
        
        # Extract resource requirements for each event
        for event in events:
            resources = self._extract_event_resources(event)
            
            for resource in resources:
                resource_key = f"{resource.resource_type.value}:{resource.resource_id}"
                
                if resource_key not in resource_bookings:
                    resource_bookings[resource_key] = []
                
                # Add setup and cleanup time
                start_with_setup = resource.required_from - timedelta(minutes=resource.setup_time_minutes)
                end_with_cleanup = resource.required_until + timedelta(minutes=resource.cleanup_time_minutes)
                
                resource_bookings[resource_key].append((event, start_with_setup, end_with_cleanup))
        
        # Check for resource conflicts
        for resource_key, bookings in resource_bookings.items():
            bookings.sort(key=lambda x: x[1])  # Sort by start time
            
            for i, (event1, start1, end1) in enumerate(bookings):
                for j, (event2, start2, end2) in enumerate(bookings[i+1:], i+1):
                    # Check for overlap
                    if start2 < end1:
                        overlap_minutes = int((min(end1, end2) - max(start1, start2)).total_seconds() / 60)
                        
                        if overlap_minutes > 0:
                            resource_type, resource_id = resource_key.split(':', 1)
                            
                            conflict = ScheduleConflict(
                                conflict_id=f"resource_conflict_{resource_key}_{event1.hearing_id}_{event2.hearing_id}",
                                conflict_type=ConflictType.RESOURCE_CONFLICT,
                                severity=ConflictSeverity.HIGH if resource_type in ['judge', 'courtroom'] else ConflictSeverity.MEDIUM,
                                primary_event=event1,
                                conflicting_events=[event2],
                                description=f"Resource conflict: {resource_type} {resource_id} double-booked",
                                detected_at=datetime.now(),
                                time_overlap_minutes=overlap_minutes,
                                metadata={
                                    'resource_type': resource_type,
                                    'resource_id': resource_id,
                                    'setup_time': self._get_resource_setup_time(resource_key),
                                    'cleanup_time': self._get_resource_cleanup_time(resource_key)
                                }
                            )
                            
                            conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_pattern_conflicts(self, events: List[HearingEvent]) -> List[ScheduleConflict]:
        """Detect conflicts based on historical patterns."""
        conflicts = []
        
        # Analyze temporal patterns
        temporal_clusters = self._analyze_temporal_patterns(events)
        
        for cluster_id, cluster_events in temporal_clusters.items():
            if len(cluster_events) > 2:  # Potential over-scheduling
                # Check if this pattern historically causes problems
                pattern_risk = self._assess_pattern_risk(cluster_events)
                
                if pattern_risk > 0.6:  # High risk threshold
                    # Create pattern-based conflict
                    primary_event = cluster_events[0]
                    conflicting_events = cluster_events[1:]
                    
                    conflict = ScheduleConflict(
                        conflict_id=f"pattern_conflict_{cluster_id}_{primary_event.hearing_id}",
                        conflict_type=ConflictType.OVERLAPPING,
                        severity=ConflictSeverity.MEDIUM,
                        primary_event=primary_event,
                        conflicting_events=conflicting_events,
                        description=f"Pattern-based conflict: cluster of {len(cluster_events)} events with {pattern_risk:.1%} historical failure rate",
                        detected_at=datetime.now(),
                        metadata={
                            'cluster_id': cluster_id,
                            'pattern_risk': pattern_risk,
                            'cluster_size': len(cluster_events),
                            'detection_method': 'temporal_pattern_analysis'
                        }
                    )
                    
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_predictive_conflicts(self, events: List[HearingEvent],
                                         horizon_days: int) -> List[ScheduleConflict]:
        """Predict future conflicts based on scheduling trends."""
        conflicts = []
        
        # Build scheduling trend model
        trend_model = self._build_scheduling_trend_model(events)
        
        # Generate prediction windows
        prediction_windows = self._generate_prediction_windows(horizon_days)
        
        for window_start, window_end in prediction_windows:
            # Predict resource utilization
            resource_predictions = self._predict_resource_utilization(
                events, window_start, window_end, trend_model
            )
            
            # Identify over-utilization risks
            for resource_key, utilization_data in resource_predictions.items():
                if utilization_data['predicted_utilization'] > 0.9:  # 90% utilization threshold
                    # Create predictive conflict
                    at_risk_events = utilization_data['contributing_events']
                    
                    if len(at_risk_events) > 1:
                        conflict = ScheduleConflict(
                            conflict_id=f"predictive_conflict_{resource_key}_{window_start.date()}",
                            conflict_type=ConflictType.RESOURCE_CONFLICT,
                            severity=ConflictSeverity.MEDIUM,
                            primary_event=at_risk_events[0],
                            conflicting_events=at_risk_events[1:],
                            description=f"Predicted resource over-utilization: {resource_key} at {utilization_data['predicted_utilization']:.1%}",
                            detected_at=datetime.now(),
                            metadata={
                                'prediction_window_start': window_start.isoformat(),
                                'prediction_window_end': window_end.isoformat(),
                                'predicted_utilization': utilization_data['predicted_utilization'],
                                'confidence': utilization_data['confidence'],
                                'detection_method': 'predictive_analysis'
                            }
                        )
                        
                        conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_constraint_violations(self, events: List[HearingEvent]) -> List[ScheduleConflict]:
        """Detect violations of scheduling constraints."""
        conflicts = []
        
        for constraint in self.scheduling_constraints:
            violations = self._check_constraint_violations(events, constraint)
            
            for violation in violations:
                conflict = ScheduleConflict(
                    conflict_id=f"constraint_violation_{constraint.constraint_id}_{violation['event'].hearing_id}",
                    conflict_type=self._map_constraint_to_conflict_type(constraint),
                    severity=self._map_constraint_severity(constraint),
                    primary_event=violation['event'],
                    conflicting_events=violation.get('conflicting_events', []),
                    description=f"Constraint violation: {constraint.description}",
                    detected_at=datetime.now(),
                    metadata={
                        'constraint_id': constraint.constraint_id,
                        'constraint_type': constraint.constraint_type,
                        'violation_details': violation['details'],
                        'penalty_score': constraint.violation_penalty
                    }
                )
                
                conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_cluster_conflicts(self, events: List[HearingEvent]) -> List[ScheduleConflict]:
        """Detect conflicts using clustering analysis of event characteristics."""
        conflicts = []
        
        if len(events) < 3:
            return conflicts
        
        # Prepare data for clustering
        event_features = []
        event_mapping = {}
        
        for i, event in enumerate(events):
            features = self._extract_clustering_features(event)
            event_features.append(features)
            event_mapping[i] = event
        
        # Normalize features
        scaler = StandardScaler()
        normalized_features = scaler.fit_transform(event_features)
        
        # Perform DBSCAN clustering
        clustering = DBSCAN(eps=0.5, min_samples=2)
        cluster_labels = clustering.fit_predict(normalized_features)
        
        # Analyze clusters for potential conflicts
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label != -1:  # Ignore noise points
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(event_mapping[i])
        
        # Check dense clusters for conflicts
        for cluster_id, cluster_events in clusters.items():
            if len(cluster_events) > 2:
                cluster_risk = self._assess_cluster_conflict_risk(cluster_events)
                
                if cluster_risk > 0.5:
                    conflict = ScheduleConflict(
                        conflict_id=f"cluster_conflict_{cluster_id}_{datetime.now().timestamp()}",
                        conflict_type=ConflictType.OVERLAPPING,
                        severity=ConflictSeverity.MEDIUM,
                        primary_event=cluster_events[0],
                        conflicting_events=cluster_events[1:],
                        description=f"Cluster-based conflict: {len(cluster_events)} events in high-risk cluster",
                        detected_at=datetime.now(),
                        metadata={
                            'cluster_id': cluster_id,
                            'cluster_risk': cluster_risk,
                            'cluster_size': len(cluster_events),
                            'detection_method': 'dbscan_clustering'
                        }
                    )
                    
                    conflicts.append(conflict)
        
        return conflicts
    
    def _calculate_time_overlap(self, event1: HearingEvent, event2: HearingEvent) -> Dict[str, int]:
        """Calculate detailed time overlap information between two events."""
        start1 = event1.date_time
        end1 = event1.end_time or start1 + timedelta(hours=1)
        start2 = event2.date_time
        end2 = event2.end_time or start2 + timedelta(hours=1)
        
        # Calculate overlap
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        overlap_minutes = max(0, int((overlap_end - overlap_start).total_seconds() / 60))
        
        # Calculate gap (negative if overlapping, positive if separated)
        if end1 <= start2:
            gap_minutes = int((start2 - end1).total_seconds() / 60)
        elif end2 <= start1:
            gap_minutes = int((start1 - end2).total_seconds() / 60)
        else:
            gap_minutes = -overlap_minutes  # Negative indicates overlap
        
        return {
            'overlap_minutes': overlap_minutes,
            'gap_minutes': gap_minutes,
            'start1': start1,
            'end1': end1,
            'start2': start2,
            'end2': end2
        }
    
    def _calculate_conflict_severity(self, event1: HearingEvent, event2: HearingEvent,
                                   overlap_minutes: int) -> ConflictSeverity:
        """Calculate conflict severity based on event types and overlap."""
        # Base severity on overlap duration
        if overlap_minutes >= 60:
            base_severity = ConflictSeverity.CRITICAL
        elif overlap_minutes >= 30:
            base_severity = ConflictSeverity.HIGH
        elif overlap_minutes >= 15:
            base_severity = ConflictSeverity.MEDIUM
        else:
            base_severity = ConflictSeverity.LOW
        
        # Adjust based on event importance
        priority_boost = 0
        
        high_priority_types = [HearingType.TRIAL, HearingType.ORAL_ARGUMENT, HearingType.SENTENCING]
        if event1.hearing_type in high_priority_types or event2.hearing_type in high_priority_types:
            priority_boost = 1
        
        # Same judge makes conflicts more severe
        if event1.judge and event2.judge and event1.judge == event2.judge:
            priority_boost += 1
        
        # Upgrade severity if needed
        severity_levels = [ConflictSeverity.LOW, ConflictSeverity.MEDIUM, 
                          ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
        current_index = severity_levels.index(base_severity)
        new_index = min(len(severity_levels) - 1, current_index + priority_boost)
        
        return severity_levels[new_index]
    
    def _get_required_buffer_time(self, event1: HearingEvent, event2: HearingEvent) -> int:
        """Get required buffer time between two events."""
        type_pair = (event1.hearing_type, event2.hearing_type)
        
        # Check specific pair buffer
        if type_pair in self.time_buffer_matrix:
            return self.time_buffer_matrix[type_pair]
        
        # Check reverse pair
        reverse_pair = (event2.hearing_type, event1.hearing_type)
        if reverse_pair in self.time_buffer_matrix:
            return self.time_buffer_matrix[reverse_pair]
        
        # Default buffer based on event types
        default_buffers = {
            HearingType.TRIAL: 45,
            HearingType.MOTION_HEARING: 20,
            HearingType.HEARING: 15,
            HearingType.DEPOSITION: 30,
            HearingType.STATUS_CONFERENCE: 10
        }
        
        buffer1 = default_buffers.get(event1.hearing_type, 15)
        buffer2 = default_buffers.get(event2.hearing_type, 15)
        
        return max(buffer1, buffer2)
    
    def _extract_event_resources(self, event: HearingEvent) -> List[ResourceRequirement]:
        """Extract resource requirements from an event."""
        resources = []
        
        # Judge resource
        if event.judge:
            resources.append(ResourceRequirement(
                resource_type=ResourceType.JUDGE,
                resource_id=event.judge.lower().replace(' ', '_'),
                resource_name=event.judge,
                required_from=event.date_time - timedelta(minutes=15),  # Prep time
                required_until=event.end_time or event.date_time + timedelta(hours=1),
                setup_time_minutes=15,
                cleanup_time_minutes=5
            ))
        
        # Courtroom resource
        if event.location and event.location.courtroom:
            resources.append(ResourceRequirement(
                resource_type=ResourceType.COURTROOM,
                resource_id=f"{event.location.court_name}_{event.location.courtroom}".lower().replace(' ', '_'),
                resource_name=f"{event.location.court_name} - {event.location.courtroom}",
                required_from=event.date_time - timedelta(minutes=30),  # Setup time
                required_until=event.end_time or event.date_time + timedelta(hours=1),
                setup_time_minutes=30,
                cleanup_time_minutes=15
            ))
        
        # Court reporter (required for most hearings)
        if event.hearing_type in [HearingType.TRIAL, HearingType.HEARING, HearingType.MOTION_HEARING]:
            resources.append(ResourceRequirement(
                resource_type=ResourceType.COURT_REPORTER,
                resource_id=f"reporter_{event.location.court_name if event.location else 'default'}".lower().replace(' ', '_'),
                resource_name="Court Reporter",
                required_from=event.date_time - timedelta(minutes=10),
                required_until=event.end_time or event.date_time + timedelta(hours=1),
                setup_time_minutes=10,
                cleanup_time_minutes=5
            ))
        
        # Attorneys
        for attorney in event.attorneys or []:
            resources.append(ResourceRequirement(
                resource_type=ResourceType.ATTORNEY,
                resource_id=attorney.lower().replace(' ', '_'),
                resource_name=attorney,
                required_from=event.date_time - timedelta(minutes=30),  # Prep time
                required_until=event.end_time or event.date_time + timedelta(hours=1),
                setup_time_minutes=30,
                cleanup_time_minutes=15
            ))
        
        return resources
    
    def _get_resource_setup_time(self, resource_key: str) -> int:
        """Get setup time for a resource type."""
        resource_type = resource_key.split(':', 1)[0]
        setup_times = {
            'judge': 15,
            'courtroom': 30,
            'attorney': 30,
            'court_reporter': 10,
            'equipment': 45,
            'interpreter': 15
        }
        return setup_times.get(resource_type, 15)
    
    def _get_resource_cleanup_time(self, resource_key: str) -> int:
        """Get cleanup time for a resource type."""
        resource_type = resource_key.split(':', 1)[0]
        cleanup_times = {
            'judge': 5,
            'courtroom': 15,
            'attorney': 15,
            'court_reporter': 5,
            'equipment': 30,
            'interpreter': 5
        }
        return cleanup_times.get(resource_type, 10)
    
    def _analyze_temporal_patterns(self, events: List[HearingEvent]) -> Dict[str, List[HearingEvent]]:
        """Analyze temporal patterns in events."""
        clusters = {}
        
        # Group events by time windows (2-hour blocks)
        for event in events:
            hour_block = event.date_time.hour // 2  # 2-hour blocks
            day_key = f"{event.date_time.date()}_{hour_block}"
            
            if day_key not in clusters:
                clusters[day_key] = []
            clusters[day_key].append(event)
        
        return clusters
    
    def _assess_pattern_risk(self, events: List[HearingEvent]) -> float:
        """Assess risk of a pattern based on historical data."""
        # This would integrate with historical conflict data
        # For now, use heuristics based on event density and types
        
        if len(events) <= 2:
            return 0.0
        
        # Calculate time density
        time_span = (max(e.date_time for e in events) - min(e.date_time for e in events)).total_seconds() / 3600
        density = len(events) / max(time_span, 0.5)  # events per hour
        
        # Risk increases with density
        density_risk = min(density / 3.0, 1.0)  # Normalize to 0-1
        
        # High-priority events increase risk
        priority_events = sum(1 for e in events if e.hearing_type in [HearingType.TRIAL, HearingType.ORAL_ARGUMENT])
        priority_risk = priority_events / len(events)
        
        # Same judge increases risk
        judges = set(e.judge for e in events if e.judge)
        judge_risk = 0.5 if len(judges) == 1 and len(events) > 2 else 0.0
        
        return min((density_risk + priority_risk + judge_risk) / 2.0, 1.0)
    
    def _build_scheduling_trend_model(self, events: List[HearingEvent]) -> Dict[str, Any]:
        """Build a simple trend model from current events."""
        model = {
            'hourly_distribution': {},
            'daily_distribution': {},
            'resource_utilization': {},
            'type_frequency': {}
        }
        
        # Analyze hourly patterns
        for event in events:
            hour = event.date_time.hour
            model['hourly_distribution'][hour] = model['hourly_distribution'].get(hour, 0) + 1
        
        # Analyze daily patterns
        for event in events:
            weekday = event.date_time.weekday()
            model['daily_distribution'][weekday] = model['daily_distribution'].get(weekday, 0) + 1
        
        # Analyze resource utilization
        for event in events:
            resources = self._extract_event_resources(event)
            for resource in resources:
                key = f"{resource.resource_type.value}:{resource.resource_id}"
                model['resource_utilization'][key] = model['resource_utilization'].get(key, 0) + 1
        
        # Analyze hearing type frequency
        for event in events:
            type_key = event.hearing_type.value
            model['type_frequency'][type_key] = model['type_frequency'].get(type_key, 0) + 1
        
        return model
    
    def _generate_prediction_windows(self, horizon_days: int) -> List[Tuple[datetime, datetime]]:
        """Generate time windows for predictive analysis."""
        windows = []
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Create weekly windows
        for week in range(0, horizon_days, 7):
            window_start = start_date + timedelta(days=week)
            window_end = window_start + timedelta(days=7)
            windows.append((window_start, window_end))
        
        return windows
    
    def _predict_resource_utilization(self, events: List[HearingEvent],
                                    window_start: datetime, window_end: datetime,
                                    trend_model: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Predict resource utilization in a time window."""
        predictions = {}
        
        # Get events in the window
        window_events = [
            e for e in events 
            if window_start <= e.date_time < window_end
        ]
        
        # Calculate current utilization
        resource_hours = {}
        total_window_hours = (window_end - window_start).total_seconds() / 3600
        business_hours_per_day = 8  # Assume 8 business hours per day
        available_business_hours = (total_window_hours / 24) * business_hours_per_day
        
        for event in window_events:
            resources = self._extract_event_resources(event)
            event_duration = ((event.end_time or event.date_time + timedelta(hours=1)) - event.date_time).total_seconds() / 3600
            
            for resource in resources:
                key = f"{resource.resource_type.value}:{resource.resource_id}"
                resource_hours[key] = resource_hours.get(key, 0) + event_duration
        
        # Calculate utilization and predict issues
        for resource_key, used_hours in resource_hours.items():
            utilization = used_hours / available_business_hours
            
            # Simple prediction: if utilization > 70%, flag as risk
            if utilization > 0.7:
                contributing_events = [
                    e for e in window_events
                    if any(r.resource_id == resource_key.split(':', 1)[1] 
                          for r in self._extract_event_resources(e))
                ]
                
                predictions[resource_key] = {
                    'predicted_utilization': utilization,
                    'used_hours': used_hours,
                    'available_hours': available_business_hours,
                    'contributing_events': contributing_events,
                    'confidence': 0.7  # Simple confidence measure
                }
        
        return predictions
    
    def _check_constraint_violations(self, events: List[HearingEvent],
                                   constraint: SchedulingConstraint) -> List[Dict[str, Any]]:
        """Check for violations of a specific constraint."""
        violations = []
        
        if constraint.constraint_id == "no_back_to_back_trials":
            trials = [e for e in events if e.hearing_type == HearingType.TRIAL]
            trials.sort(key=lambda e: e.date_time)
            
            for i in range(len(trials) - 1):
                trial1 = trials[i]
                trial2 = trials[i + 1]
                
                gap = (trial2.date_time - (trial1.end_time or trial1.date_time + timedelta(hours=1))).total_seconds() / 60
                min_gap = constraint.time_restrictions.get('min_gap_minutes', 60)
                
                if gap < min_gap:
                    violations.append({
                        'event': trial1,
                        'conflicting_events': [trial2],
                        'details': f"Gap of {gap:.0f} minutes is less than required {min_gap} minutes"
                    })
        
        elif constraint.constraint_id == "lunch_break_protection":
            protected_hours = constraint.time_restrictions.get('protected_hours', [])
            
            for event in events:
                event_start_time = event.date_time.time()
                event_end_time = (event.end_time or event.date_time + timedelta(hours=1)).time()
                
                for start_protected, end_protected in protected_hours:
                    if (event_start_time < end_protected and event_end_time > start_protected):
                        violations.append({
                            'event': event,
                            'details': f"Event overlaps with protected time {start_protected}-{end_protected}"
                        })
        
        elif constraint.constraint_id == "judge_daily_limit":
            # Group events by judge and date
            judge_daily_events = {}
            
            for event in events:
                if event.judge:
                    date_key = event.date_time.date()
                    judge_key = f"{event.judge}:{date_key}"
                    
                    if judge_key not in judge_daily_events:
                        judge_daily_events[judge_key] = []
                    judge_daily_events[judge_key].append(event)
            
            max_daily = constraint.resource_restrictions.get('max_daily_events', 8)
            
            for judge_date_key, daily_events in judge_daily_events.items():
                if len(daily_events) > max_daily:
                    violations.append({
                        'event': daily_events[0],  # Primary event
                        'conflicting_events': daily_events[1:],
                        'details': f"Judge has {len(daily_events)} events, exceeding limit of {max_daily}"
                    })
        
        return violations
    
    def _map_constraint_to_conflict_type(self, constraint: SchedulingConstraint) -> ConflictType:
        """Map constraint to conflict type."""
        mapping = {
            "no_back_to_back_trials": ConflictType.OVERLAPPING,
            "lunch_break_protection": ConflictType.COURT_CLOSURE,
            "judge_daily_limit": ConflictType.RESOURCE_CONFLICT,
            "same_building_preference": ConflictType.TRAVEL_TIME
        }
        return mapping.get(constraint.constraint_id, ConflictType.OVERLAPPING)
    
    def _map_constraint_severity(self, constraint: SchedulingConstraint) -> ConflictSeverity:
        """Map constraint type to severity."""
        severity_mapping = {
            "hard": ConflictSeverity.CRITICAL,
            "soft": ConflictSeverity.HIGH,
            "preference": ConflictSeverity.LOW
        }
        return severity_mapping.get(constraint.constraint_type, ConflictSeverity.MEDIUM)
    
    def _extract_clustering_features(self, event: HearingEvent) -> List[float]:
        """Extract features for clustering analysis."""
        features = []
        
        # Time-based features
        features.append(event.date_time.hour)  # Hour of day
        features.append(event.date_time.weekday())  # Day of week
        features.append((event.date_time.date() - datetime.now().date()).days)  # Days from now
        
        # Event type (one-hot encoded)
        hearing_types = list(HearingType)
        for ht in hearing_types:
            features.append(1.0 if event.hearing_type == ht else 0.0)
        
        # Duration
        duration_hours = 1.0  # Default
        if event.end_time:
            duration_hours = (event.end_time - event.date_time).total_seconds() / 3600
        features.append(duration_hours)
        
        # Location (encoded as hash)
        location_hash = 0.0
        if event.location and event.location.court_name:
            location_hash = float(hash(event.location.court_name) % 1000) / 1000.0
        features.append(location_hash)
        
        # Judge (encoded as hash)
        judge_hash = 0.0
        if event.judge:
            judge_hash = float(hash(event.judge) % 1000) / 1000.0
        features.append(judge_hash)
        
        # Confidence
        features.append(event.confidence)
        
        return features
    
    def _assess_cluster_conflict_risk(self, cluster_events: List[HearingEvent]) -> float:
        """Assess conflict risk for a cluster of events."""
        if len(cluster_events) <= 1:
            return 0.0
        
        # Time density risk
        times = [e.date_time for e in cluster_events]
        time_span = (max(times) - min(times)).total_seconds() / 3600
        density_risk = len(cluster_events) / max(time_span, 0.5)
        density_risk = min(density_risk / 4.0, 1.0)  # Normalize
        
        # Judge overlap risk
        judges = [e.judge for e in cluster_events if e.judge]
        judge_overlap = len(judges) - len(set(judges))
        judge_risk = judge_overlap / max(len(cluster_events), 1)
        
        # Location overlap risk
        locations = [e.location.court_name for e in cluster_events if e.location]
        location_overlap = len(locations) - len(set(locations))
        location_risk = location_overlap / max(len(cluster_events), 1)
        
        # Combine risks
        total_risk = (density_risk + judge_risk + location_risk) / 3.0
        return min(total_risk, 1.0)
    
    def _deduplicate_and_rank_conflicts(self, conflicts: List[ScheduleConflict]) -> List[ScheduleConflict]:
        """Remove duplicates and rank conflicts by severity and impact."""
        # Remove duplicates based on involved events
        seen_signatures = set()
        unique_conflicts = []
        
        for conflict in conflicts:
            # Create signature based on involved events
            event_ids = [conflict.primary_event.hearing_id]
            event_ids.extend([e.hearing_id for e in conflict.conflicting_events])
            event_ids.sort()
            signature = f"{conflict.conflict_type.value}:{'|'.join(event_ids)}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_conflicts.append(conflict)
        
        # Rank by severity and impact
        severity_order = {
            ConflictSeverity.CRITICAL: 4,
            ConflictSeverity.HIGH: 3,
            ConflictSeverity.MEDIUM: 2,
            ConflictSeverity.LOW: 1
        }
        
        unique_conflicts.sort(key=lambda c: (
            severity_order.get(c.severity, 0),
            c.time_overlap_minutes,
            len(c.conflicting_events)
        ), reverse=True)
        
        return unique_conflicts
    
    def add_constraint(self, constraint: SchedulingConstraint):
        """Add a custom scheduling constraint."""
        self.scheduling_constraints.append(constraint)
        logger.info(f"Added scheduling constraint: {constraint.constraint_id}")
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a scheduling constraint."""
        original_count = len(self.scheduling_constraints)
        self.scheduling_constraints = [
            c for c in self.scheduling_constraints 
            if c.constraint_id != constraint_id
        ]
        removed = len(self.scheduling_constraints) < original_count
        if removed:
            logger.info(f"Removed scheduling constraint: {constraint_id}")
        return removed
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected conflicts."""
        if not self.conflict_history:
            return {'total_conflicts': 0, 'message': 'No conflict history available'}
        
        # Basic statistics
        total_conflicts = len(self.conflict_history)
        severity_counts = {}
        type_counts = {}
        
        for conflict in self.conflict_history:
            severity = conflict.severity.value
            conflict_type = conflict.conflict_type.value
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1
        
        # Calculate resolution rates
        resolved_conflicts = sum(1 for c in self.conflict_history 
                               if c.resolution_status.value in ['resolved'])
        resolution_rate = resolved_conflicts / total_conflicts * 100 if total_conflicts > 0 else 0
        
        return {
            'total_conflicts': total_conflicts,
            'severity_distribution': severity_counts,
            'type_distribution': type_counts,
            'resolution_rate': resolution_rate,
            'avg_conflicts_per_day': total_conflicts / max(30, 1),  # Assume 30-day history
            'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            'most_common_severity': max(severity_counts.items(), key=lambda x: x[1])[0] if severity_counts else None
        }


# Example usage
async def example_advanced_conflict_detection():
    """Example usage of advanced conflict detection."""
    
    # Create sample events with various conflict scenarios
    events = [
        # Overlapping trials with same judge
        HearingEvent(
            hearing_id="trial_1",
            case_number="CASE001",
            case_title="Smith v. Jones",
            hearing_type=HearingType.TRIAL,
            date_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            judge="Judge Johnson",
            location=Location(court_name="Downtown Courthouse", courtroom="101"),
            attorneys=["Attorney Smith", "Attorney Brown"],
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="trial_2",
            case_number="CASE002",
            case_title="Brown v. Davis",
            hearing_type=HearingType.TRIAL,
            date_time=datetime(2024, 1, 15, 11, 0),  # Overlapping
            end_time=datetime(2024, 1, 15, 14, 0),
            judge="Judge Johnson",  # Same judge
            location=Location(court_name="Downtown Courthouse", courtroom="102"),
            attorneys=["Attorney Wilson", "Attorney Taylor"],
            status=HearingStatus.SCHEDULED
        ),
        # Resource conflict - same courtroom
        HearingEvent(
            hearing_id="hearing_1",
            case_number="CASE003",
            case_title="Wilson v. Anderson",
            hearing_type=HearingType.MOTION_HEARING,
            date_time=datetime(2024, 1, 15, 14, 0),
            end_time=datetime(2024, 1, 15, 15, 0),
            judge="Judge Miller",
            location=Location(court_name="Downtown Courthouse", courtroom="101"),
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="hearing_2",
            case_number="CASE004",
            case_title="Taylor v. Clark",
            hearing_type=HearingType.HEARING,
            date_time=datetime(2024, 1, 15, 14, 30),  # Overlapping courtroom use
            end_time=datetime(2024, 1, 15, 15, 30),
            judge="Judge White",
            location=Location(court_name="Downtown Courthouse", courtroom="101"),  # Same courtroom
            status=HearingStatus.SCHEDULED
        ),
        # Dense clustering
        HearingEvent(
            hearing_id="status_1",
            case_number="CASE005",
            case_title="Miller v. Johnson",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 16, 9, 0),
            end_time=datetime(2024, 1, 16, 9, 30),
            judge="Judge Davis",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="status_2",
            case_number="CASE006",
            case_title="Clark v. Wilson",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 16, 9, 15),  # Dense scheduling
            end_time=datetime(2024, 1, 16, 9, 45),
            judge="Judge Davis",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="status_3",
            case_number="CASE007",
            case_title="Anderson v. Taylor",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 16, 9, 30),  # Dense scheduling
            end_time=datetime(2024, 1, 16, 10, 0),
            judge="Judge Davis",
            status=HearingStatus.SCHEDULED
        ),
    ]
    
    # Initialize advanced conflict detector
    detector = AdvancedConflictDetector()
    
    # Add custom constraints
    custom_constraint = SchedulingConstraint(
        constraint_id="max_3_hearings_per_hour",
        constraint_type="soft",
        description="No more than 3 hearings per hour in same building",
        applies_to=["all"],
        violation_penalty=25.0
    )
    detector.add_constraint(custom_constraint)
    
    # Detect conflicts
    print("Detecting advanced conflicts...")
    conflicts = await detector.detect_advanced_conflicts(events, prediction_horizon_days=7)
    
    print(f"\nDetected {len(conflicts)} conflicts:")
    print("=" * 60)
    
    for i, conflict in enumerate(conflicts, 1):
        print(f"\n{i}. {conflict.conflict_type.value.upper()}")
        print(f"   Severity: {conflict.severity.value}")
        print(f"   Description: {conflict.description}")
        print(f"   Primary Event: {conflict.primary_event.case_title}")
        print(f"   Conflicting Events: {len(conflict.conflicting_events)}")
        
        if conflict.metadata:
            print(f"   Metadata: {json.dumps(conflict.metadata, indent=8)}")
    
    # Get conflict statistics
    detector.conflict_history = conflicts  # Simulate history
    stats = detector.get_conflict_statistics()
    
    print(f"\n\nConflict Statistics:")
    print("=" * 30)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(example_advanced_conflict_detection())