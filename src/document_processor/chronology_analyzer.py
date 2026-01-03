"""
Advanced chronological event analyzer for legal timelines.
Provides event analysis, pattern detection, and chronological insights.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
import json
import networkx as nx
import pandas as pd

from .timeline_extractor import TimelineEvent, Timeline, EventType, EventCertainty, TemporalContext

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of chronological analysis."""
    PATTERN_DETECTION = "pattern_detection"
    CAUSAL_ANALYSIS = "causal_analysis"
    TIMELINE_GAPS = "timeline_gaps"
    EVENT_CLUSTERING = "event_clustering"
    PROCEDURAL_ANALYSIS = "procedural_analysis"
    TEMPORAL_PATTERNS = "temporal_patterns"
    CRITICAL_PATH = "critical_path"
    CONFLICT_DETECTION = "conflict_detection"
    TREND_ANALYSIS = "trend_analysis"
    MILESTONE_IDENTIFICATION = "milestone_identification"


class PatternType(Enum):
    """Types of patterns that can be detected."""
    PROCEDURAL_SEQUENCE = "procedural_sequence"
    RECURRING_EVENT = "recurring_event"
    SEASONAL_PATTERN = "seasonal_pattern"
    ESCALATION_PATTERN = "escalation_pattern"
    BATCH_PROCESSING = "batch_processing"
    DEADLINE_CLUSTERING = "deadline_clustering"
    COMMUNICATION_BURST = "communication_burst"
    SETTLEMENT_NEGOTIATION = "settlement_negotiation"
    DISCOVERY_PHASE = "discovery_phase"
    TRIAL_PREPARATION = "trial_preparation"


class ConflictType(Enum):
    """Types of timeline conflicts."""
    DATE_INCONSISTENCY = "date_inconsistency"
    SEQUENCE_VIOLATION = "sequence_violation"
    IMPOSSIBLE_TIMING = "impossible_timing"
    MISSING_PREREQUISITE = "missing_prerequisite"
    OVERLAPPING_EXCLUSIVE = "overlapping_exclusive"
    DEADLINE_VIOLATION = "deadline_violation"


@dataclass
class TemporalPattern:
    """Represents a detected temporal pattern."""
    pattern_id: str
    pattern_type: PatternType
    description: str
    events: List[str]  # Event IDs
    confidence: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    frequency: Optional[str]  # For recurring patterns
    characteristics: Dict[str, Any] = field(default_factory=dict)
    significance_score: float = 0.0


@dataclass
class TimelineGap:
    """Represents a gap in the timeline."""
    gap_id: str
    start_date: datetime
    end_date: datetime
    duration_days: int
    context: str
    significance: str  # low, medium, high
    suggested_events: List[str] = field(default_factory=list)
    impact_assessment: str = ""


@dataclass
class EventCluster:
    """Represents a cluster of related events."""
    cluster_id: str
    cluster_type: str
    events: List[str]  # Event IDs
    central_event: Optional[str]
    time_span: Tuple[datetime, datetime]
    density_score: float  # Events per day
    coherence_score: float  # How related events are
    description: str = ""


@dataclass
class CausalRelationship:
    """Represents a causal relationship between events."""
    relationship_id: str
    cause_event: str  # Event ID
    effect_event: str  # Event ID
    relationship_type: str  # direct, indirect, contributing
    confidence: float
    time_delay: Optional[timedelta]
    evidence: List[str] = field(default_factory=list)
    strength: str = "weak"  # weak, moderate, strong


@dataclass
class TimelineConflict:
    """Represents a conflict or inconsistency in the timeline."""
    conflict_id: str
    conflict_type: ConflictType
    description: str
    affected_events: List[str]  # Event IDs
    severity: str  # low, medium, high, critical
    suggested_resolution: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class ChronologyInsights:
    """Comprehensive insights from chronological analysis."""
    analysis_id: str
    timeline_id: str
    
    # Pattern analysis
    detected_patterns: List[TemporalPattern] = field(default_factory=list)
    
    # Gap analysis
    timeline_gaps: List[TimelineGap] = field(default_factory=list)
    
    # Event clustering
    event_clusters: List[EventCluster] = field(default_factory=list)
    
    # Causal analysis
    causal_relationships: List[CausalRelationship] = field(default_factory=list)
    
    # Conflict detection
    timeline_conflicts: List[TimelineConflict] = field(default_factory=list)
    
    # Statistical insights
    timeline_statistics: Dict[str, Any] = field(default_factory=dict)
    
    # Critical path analysis
    critical_events: List[str] = field(default_factory=list)
    milestone_events: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0


class ChronologyAnalyzer:
    """Advanced chronological event analyzer for legal timelines."""
    
    def __init__(self):
        """Initialize chronology analyzer."""
        
        # Analysis configuration
        self.analysis_config = {
            'gap_threshold_days': 30,  # Minimum days to consider a gap significant
            'cluster_time_window_days': 7,  # Time window for event clustering
            'pattern_min_events': 3,  # Minimum events to form a pattern
            'causal_max_delay_days': 60,  # Maximum delay for causal relationships
            'conflict_tolerance_hours': 24  # Tolerance for timing conflicts
        }
        
        # Legal procedural patterns
        self.procedural_sequences = {
            'litigation_filing': [
                EventType.FILING, EventType.MOTION, EventType.HEARING, EventType.ORDER
            ],
            'discovery_process': [
                EventType.DISCOVERY, EventType.DEPOSITION, EventType.MOTION, EventType.ORDER
            ],
            'settlement_negotiation': [
                EventType.COMMUNICATION, EventType.MEETING, EventType.SETTLEMENT
            ],
            'trial_preparation': [
                EventType.DISCOVERY, EventType.DEPOSITION, EventType.MOTION, EventType.TRIAL
            ]
        }
        
        # Event precedence rules (which events must come before others)
        self.precedence_rules = {
            EventType.HEARING: [EventType.FILING, EventType.MOTION],
            EventType.ORDER: [EventType.HEARING, EventType.MOTION],
            EventType.DEPOSITION: [EventType.DISCOVERY],
            EventType.TRIAL: [EventType.FILING, EventType.DISCOVERY],
            EventType.SETTLEMENT: [EventType.FILING]
        }
        
    def analyze_chronology(self, timeline: Timeline, 
                          analysis_types: List[AnalysisType] = None) -> ChronologyInsights:
        """Perform comprehensive chronological analysis of timeline.
        
        Args:
            timeline: Timeline to analyze
            analysis_types: Types of analysis to perform (all by default)
            
        Returns:
            Comprehensive chronological insights
        """
        logger.info(f"Analyzing chronology for timeline: {timeline.timeline_id}")
        
        analysis_types = analysis_types or list(AnalysisType)
        
        insights = ChronologyInsights(
            analysis_id=f"analysis_{timeline.timeline_id}_{int(datetime.utcnow().timestamp())}",
            timeline_id=timeline.timeline_id
        )
        
        # Perform different types of analysis
        if AnalysisType.PATTERN_DETECTION in analysis_types:
            insights.detected_patterns = self._detect_patterns(timeline)
        
        if AnalysisType.TIMELINE_GAPS in analysis_types:
            insights.timeline_gaps = self._identify_gaps(timeline)
        
        if AnalysisType.EVENT_CLUSTERING in analysis_types:
            insights.event_clusters = self._cluster_events(timeline)
        
        if AnalysisType.CAUSAL_ANALYSIS in analysis_types:
            insights.causal_relationships = self._analyze_causal_relationships(timeline)
        
        if AnalysisType.CONFLICT_DETECTION in analysis_types:
            insights.timeline_conflicts = self._detect_conflicts(timeline)
        
        if AnalysisType.CRITICAL_PATH in analysis_types:
            insights.critical_events, insights.milestone_events = self._identify_critical_path(timeline)
        
        # Generate statistical insights
        insights.timeline_statistics = self._generate_statistics(timeline)
        
        # Generate recommendations
        insights.recommendations = self._generate_recommendations(timeline, insights)
        
        # Calculate overall confidence
        insights.confidence_score = self._calculate_analysis_confidence(timeline, insights)
        
        return insights
    
    def _detect_patterns(self, timeline: Timeline) -> List[TemporalPattern]:
        """Detect temporal patterns in the timeline."""
        patterns = []
        
        # Detect procedural sequence patterns
        patterns.extend(self._detect_procedural_patterns(timeline))
        
        # Detect recurring event patterns
        patterns.extend(self._detect_recurring_patterns(timeline))
        
        # Detect seasonal patterns
        patterns.extend(self._detect_seasonal_patterns(timeline))
        
        # Detect escalation patterns
        patterns.extend(self._detect_escalation_patterns(timeline))
        
        # Detect batch processing patterns
        patterns.extend(self._detect_batch_patterns(timeline))
        
        # Detect communication burst patterns
        patterns.extend(self._detect_communication_bursts(timeline))
        
        return patterns
    
    def _detect_procedural_patterns(self, timeline: Timeline) -> List[TemporalPattern]:
        """Detect legal procedural sequence patterns."""
        patterns = []
        
        for sequence_name, expected_sequence in self.procedural_sequences.items():
            # Find events matching the sequence
            sequence_events = []
            for event_type in expected_sequence:
                matching_events = [
                    e for e in timeline.events 
                    if e.event_type == event_type and e.date
                ]
                if matching_events:
                    # Sort by date and take the first occurrence
                    matching_events.sort(key=lambda x: x.date)
                    sequence_events.append(matching_events[0])
            
            # Check if we have a complete or partial sequence
            if len(sequence_events) >= self.analysis_config['pattern_min_events']:
                # Verify chronological order
                if self._is_chronological_sequence(sequence_events):
                    confidence = len(sequence_events) / len(expected_sequence)
                    
                    patterns.append(TemporalPattern(
                        pattern_id=f"proc_{sequence_name}_{len(patterns)}",
                        pattern_type=PatternType.PROCEDURAL_SEQUENCE,
                        description=f"{sequence_name.replace('_', ' ').title()} sequence detected",
                        events=[e.event_id for e in sequence_events],
                        confidence=confidence,
                        start_date=sequence_events[0].date,
                        end_date=sequence_events[-1].date,
                        frequency=None,
                        characteristics={
                            'sequence_type': sequence_name,
                            'completeness': confidence,
                            'duration_days': (sequence_events[-1].date - sequence_events[0].date).days
                        },
                        significance_score=confidence * 0.8
                    ))
        
        return patterns
    
    def _detect_recurring_patterns(self, timeline: Timeline) -> List[TemporalPattern]:
        """Detect recurring event patterns."""
        patterns = []
        
        # Group events by type
        events_by_type = defaultdict(list)
        for event in timeline.events:
            if event.date:
                events_by_type[event.event_type].append(event)
        
        # Look for recurring patterns within each type
        for event_type, events in events_by_type.items():
            if len(events) >= self.analysis_config['pattern_min_events']:
                events.sort(key=lambda x: x.date)
                
                # Calculate intervals between events
                intervals = []
                for i in range(1, len(events)):
                    interval = (events[i].date - events[i-1].date).days
                    intervals.append(interval)
                
                # Check for consistent intervals (recurring pattern)
                if intervals and len(set(intervals)) <= 3:  # Allow some variation
                    avg_interval = statistics.mean(intervals)
                    
                    # Determine frequency
                    if 6 <= avg_interval <= 8:
                        frequency = "weekly"
                    elif 28 <= avg_interval <= 35:
                        frequency = "monthly"
                    elif 85 <= avg_interval <= 95:
                        frequency = "quarterly"
                    elif 360 <= avg_interval <= 370:
                        frequency = "annually"
                    else:
                        frequency = f"every_{int(avg_interval)}_days"
                    
                    confidence = 1.0 - (statistics.stdev(intervals) / max(intervals))
                    
                    patterns.append(TemporalPattern(
                        pattern_id=f"recur_{event_type.value}_{len(patterns)}",
                        pattern_type=PatternType.RECURRING_EVENT,
                        description=f"Recurring {event_type.value} events ({frequency})",
                        events=[e.event_id for e in events],
                        confidence=confidence,
                        start_date=events[0].date,
                        end_date=events[-1].date,
                        frequency=frequency,
                        characteristics={
                            'event_type': event_type.value,
                            'avg_interval_days': avg_interval,
                            'interval_variance': statistics.stdev(intervals) if len(intervals) > 1 else 0
                        },
                        significance_score=confidence * len(events) * 0.1
                    ))
        
        return patterns
    
    def _detect_seasonal_patterns(self, timeline: Timeline) -> List[TemporalPattern]:
        """Detect seasonal patterns in event timing."""
        patterns = []
        
        dated_events = [e for e in timeline.events if e.date]
        if len(dated_events) < 6:  # Need minimum events for seasonal analysis
            return patterns
        
        # Group events by month
        monthly_counts = defaultdict(list)
        for event in dated_events:
            month = event.date.month
            monthly_counts[month].append(event)
        
        # Look for months with significantly higher activity
        avg_monthly_count = len(dated_events) / 12
        peak_months = []
        
        for month, events in monthly_counts.items():
            if len(events) > avg_monthly_count * 1.5:  # 50% above average
                peak_months.append((month, events))
        
        # Create seasonal patterns for peak months
        for month, events in peak_months:
            month_name = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ][month - 1]
            
            confidence = min(1.0, len(events) / (avg_monthly_count * 2))
            
            patterns.append(TemporalPattern(
                pattern_id=f"seasonal_{month}_{len(patterns)}",
                pattern_type=PatternType.SEASONAL_PATTERN,
                description=f"Increased activity in {month_name}",
                events=[e.event_id for e in events],
                confidence=confidence,
                start_date=min(e.date for e in events),
                end_date=max(e.date for e in events),
                frequency="annual",
                characteristics={
                    'peak_month': month_name,
                    'event_count': len(events),
                    'vs_average': len(events) / avg_monthly_count
                },
                significance_score=confidence * 0.6
            ))
        
        return patterns
    
    def _detect_escalation_patterns(self, timeline: Timeline) -> List[TemporalPattern]:
        """Detect escalation patterns (increasing intensity or urgency)."""
        patterns = []
        
        # Look for patterns of increasing urgency or activity
        dated_events = [e for e in timeline.events if e.date]
        dated_events.sort(key=lambda x: x.date)
        
        # Analyze activity over time periods
        if len(dated_events) < 6:
            return patterns
        
        # Split timeline into periods
        timeline_start = dated_events[0].date
        timeline_end = dated_events[-1].date
        total_days = (timeline_end - timeline_start).days
        
        if total_days > 90:  # Only analyze if timeline is long enough
            period_days = total_days // 4  # Split into 4 periods
            
            period_counts = []
            for i in range(4):
                period_start = timeline_start + timedelta(days=i * period_days)
                period_end = timeline_start + timedelta(days=(i + 1) * period_days)
                
                period_events = [
                    e for e in dated_events 
                    if period_start <= e.date < period_end
                ]
                period_counts.append(len(period_events))
            
            # Check for increasing trend
            if self._is_increasing_trend(period_counts):
                escalation_factor = period_counts[-1] / max(1, period_counts[0])
                confidence = min(1.0, (escalation_factor - 1) / 2)
                
                patterns.append(TemporalPattern(
                    pattern_id=f"escalation_{len(patterns)}",
                    pattern_type=PatternType.ESCALATION_PATTERN,
                    description="Escalating activity pattern detected",
                    events=[e.event_id for e in dated_events],
                    confidence=confidence,
                    start_date=timeline_start,
                    end_date=timeline_end,
                    frequency=None,
                    characteristics={
                        'escalation_factor': escalation_factor,
                        'period_counts': period_counts
                    },
                    significance_score=confidence * 0.9
                ))
        
        return patterns
    
    def _detect_batch_patterns(self, timeline: Timeline) -> List[TemporalPattern]:
        """Detect batch processing patterns (clusters of similar events)."""
        patterns = []
        
        # Group events by type
        events_by_type = defaultdict(list)
        for event in timeline.events:
            if event.date:
                events_by_type[event.event_type].append(event)
        
        # Look for temporal clusters within each type
        for event_type, events in events_by_type.items():
            if len(events) >= 3:
                events.sort(key=lambda x: x.date)
                
                # Find clusters of events within short time windows
                clusters = []
                current_cluster = [events[0]]
                
                for i in range(1, len(events)):
                    time_diff = (events[i].date - current_cluster[-1].date).days
                    
                    if time_diff <= self.analysis_config['cluster_time_window_days']:
                        current_cluster.append(events[i])
                    else:
                        if len(current_cluster) >= 3:
                            clusters.append(current_cluster)
                        current_cluster = [events[i]]
                
                # Don't forget the last cluster
                if len(current_cluster) >= 3:
                    clusters.append(current_cluster)
                
                # Create patterns for significant clusters
                for cluster in clusters:
                    if len(cluster) >= 3:
                        time_span = (cluster[-1].date - cluster[0].date).days
                        density = len(cluster) / max(1, time_span)
                        
                        patterns.append(TemporalPattern(
                            pattern_id=f"batch_{event_type.value}_{len(patterns)}",
                            pattern_type=PatternType.BATCH_PROCESSING,
                            description=f"Batch of {event_type.value} events",
                            events=[e.event_id for e in cluster],
                            confidence=min(1.0, density),
                            start_date=cluster[0].date,
                            end_date=cluster[-1].date,
                            frequency=None,
                            characteristics={
                                'cluster_size': len(cluster),
                                'time_span_days': time_span,
                                'density_events_per_day': density
                            },
                            significance_score=min(1.0, density * len(cluster) * 0.1)
                        ))
        
        return patterns
    
    def _detect_communication_bursts(self, timeline: Timeline) -> List[TemporalPattern]:
        """Detect communication burst patterns."""
        patterns = []
        
        comm_events = [
            e for e in timeline.events 
            if e.event_type == EventType.COMMUNICATION and e.date
        ]
        
        if len(comm_events) >= 4:
            comm_events.sort(key=lambda x: x.date)
            
            # Look for periods of intense communication
            burst_threshold = 3  # 3+ communications within a week
            
            i = 0
            while i < len(comm_events) - burst_threshold + 1:
                burst_events = []
                
                for j in range(i, len(comm_events)):
                    if not burst_events:
                        burst_events.append(comm_events[j])
                    else:
                        time_diff = (comm_events[j].date - burst_events[0].date).days
                        if time_diff <= 7:  # Within a week
                            burst_events.append(comm_events[j])
                        else:
                            break
                
                if len(burst_events) >= burst_threshold:
                    time_span = (burst_events[-1].date - burst_events[0].date).days
                    intensity = len(burst_events) / max(1, time_span)
                    
                    patterns.append(TemporalPattern(
                        pattern_id=f"comm_burst_{len(patterns)}",
                        pattern_type=PatternType.COMMUNICATION_BURST,
                        description=f"Communication burst ({len(burst_events)} events)",
                        events=[e.event_id for e in burst_events],
                        confidence=min(1.0, intensity),
                        start_date=burst_events[0].date,
                        end_date=burst_events[-1].date,
                        frequency=None,
                        characteristics={
                            'burst_size': len(burst_events),
                            'intensity': intensity,
                            'time_span_days': time_span
                        },
                        significance_score=min(1.0, intensity * 0.5)
                    ))
                    
                    i += len(burst_events)
                else:
                    i += 1
        
        return patterns
    
    def _identify_gaps(self, timeline: Timeline) -> List[TimelineGap]:
        """Identify significant gaps in the timeline."""
        gaps = []
        
        dated_events = [e for e in timeline.events if e.date]
        if len(dated_events) < 2:
            return gaps
        
        dated_events.sort(key=lambda x: x.date)
        
        for i in range(1, len(dated_events)):
            prev_event = dated_events[i-1]
            curr_event = dated_events[i]
            
            gap_duration = (curr_event.date - prev_event.date).days
            
            if gap_duration > self.analysis_config['gap_threshold_days']:
                # Assess gap significance
                if gap_duration > 180:
                    significance = "high"
                elif gap_duration > 90:
                    significance = "medium"
                else:
                    significance = "low"
                
                # Generate context
                context = f"Gap between {prev_event.event_type.value} and {curr_event.event_type.value}"
                
                # Suggest possible events based on procedural patterns
                suggested_events = self._suggest_gap_events(prev_event, curr_event)
                
                gaps.append(TimelineGap(
                    gap_id=f"gap_{i}_{int(prev_event.date.timestamp())}",
                    start_date=prev_event.date,
                    end_date=curr_event.date,
                    duration_days=gap_duration,
                    context=context,
                    significance=significance,
                    suggested_events=suggested_events,
                    impact_assessment=f"Potential missing activity during {gap_duration}-day period"
                ))
        
        return gaps
    
    def _cluster_events(self, timeline: Timeline) -> List[EventCluster]:
        """Cluster related events together."""
        clusters = []
        
        dated_events = [e for e in timeline.events if e.date]
        if len(dated_events) < 3:
            return clusters
        
        dated_events.sort(key=lambda x: x.date)
        
        # Temporal clustering
        temporal_clusters = self._create_temporal_clusters(dated_events)
        
        # Type-based clustering
        type_clusters = self._create_type_clusters(dated_events)
        
        # Participant-based clustering
        participant_clusters = self._create_participant_clusters(dated_events)
        
        # Combine and evaluate clusters
        all_clusters = temporal_clusters + type_clusters + participant_clusters
        
        for cluster_data in all_clusters:
            if len(cluster_data['events']) >= 3:
                events = cluster_data['events']
                
                # Calculate cluster metrics
                dates = [e.date for e in events]
                time_span = (max(dates) - min(dates)).days
                density = len(events) / max(1, time_span)
                
                # Calculate coherence (how related events are)
                coherence = self._calculate_cluster_coherence(events)
                
                clusters.append(EventCluster(
                    cluster_id=f"cluster_{cluster_data['type']}_{len(clusters)}",
                    cluster_type=cluster_data['type'],
                    events=[e.event_id for e in events],
                    central_event=self._find_central_event(events),
                    time_span=(min(dates), max(dates)),
                    density_score=density,
                    coherence_score=coherence,
                    description=cluster_data.get('description', f"{cluster_data['type']} cluster")
                ))
        
        return clusters
    
    def _analyze_causal_relationships(self, timeline: Timeline) -> List[CausalRelationship]:
        """Analyze causal relationships between events."""
        relationships = []
        
        dated_events = [e for e in timeline.events if e.date]
        dated_events.sort(key=lambda x: x.date)
        
        for i, event in enumerate(dated_events):
            # Look for potential causes in preceding events
            for j in range(max(0, i-5), i):  # Look back up to 5 events
                potential_cause = dated_events[j]
                
                # Check if causal relationship is plausible
                relationship = self._evaluate_causal_relationship(potential_cause, event)
                if relationship:
                    relationships.append(relationship)
        
        return relationships
    
    def _detect_conflicts(self, timeline: Timeline) -> List[TimelineConflict]:
        """Detect conflicts and inconsistencies in the timeline."""
        conflicts = []
        
        # Check for date inconsistencies
        conflicts.extend(self._detect_date_inconsistencies(timeline))
        
        # Check for sequence violations
        conflicts.extend(self._detect_sequence_violations(timeline))
        
        # Check for impossible timing
        conflicts.extend(self._detect_impossible_timing(timeline))
        
        # Check for missing prerequisites
        conflicts.extend(self._detect_missing_prerequisites(timeline))
        
        # Check for deadline violations
        conflicts.extend(self._detect_deadline_violations(timeline))
        
        return conflicts
    
    def _identify_critical_path(self, timeline: Timeline) -> Tuple[List[str], List[str]]:
        """Identify critical events and milestones in the timeline."""
        
        critical_events = []
        milestone_events = []
        
        # Build dependency graph
        graph = nx.DiGraph()
        
        for event in timeline.events:
            graph.add_node(event.event_id, event=event)
            
            # Add edges based on causal relationships
            for cause_id in event.caused_by:
                if graph.has_node(cause_id):
                    graph.add_edge(cause_id, event.event_id)
        
        # Find critical path using topological sort and longest path
        if graph.nodes:
            try:
                # Find nodes with no dependencies (start nodes)
                start_nodes = [n for n in graph.nodes if graph.in_degree(n) == 0]
                
                # Find nodes with no dependents (end nodes)
                end_nodes = [n for n in graph.nodes if graph.out_degree(n) == 0]
                
                # Calculate critical path
                for start in start_nodes:
                    for end in end_nodes:
                        try:
                            path = nx.shortest_path(graph, start, end)
                            if len(path) > len(critical_events):
                                critical_events = path
                        except nx.NetworkXNoPath:
                            continue
                
            except Exception as e:
                logger.warning(f"Critical path calculation failed: {e}")
        
        # Identify milestone events (important event types or high confidence)
        important_types = {
            EventType.FILING, EventType.ORDER, EventType.SETTLEMENT, 
            EventType.TRIAL, EventType.CONTRACT
        }
        
        for event in timeline.events:
            if (event.event_type in important_types or 
                event.confidence > 0.8 or 
                event.certainty == EventCertainty.CERTAIN):
                milestone_events.append(event.event_id)
        
        return critical_events, milestone_events
    
    def _generate_statistics(self, timeline: Timeline) -> Dict[str, Any]:
        """Generate comprehensive timeline statistics."""
        
        dated_events = [e for e in timeline.events if e.date]
        
        stats = {
            'total_events': len(timeline.events),
            'dated_events': len(dated_events),
            'undated_events': len(timeline.events) - len(dated_events),
            'event_types': {
                et.value: len([e for e in timeline.events if e.event_type == et])
                for et in EventType
                if any(e.event_type == et for e in timeline.events)
            },
            'avg_confidence': sum(e.confidence for e in timeline.events) / len(timeline.events) if timeline.events else 0,
            'certainty_distribution': {
                ec.value: len([e for e in timeline.events if e.certainty == ec])
                for ec in EventCertainty
                if any(e.certainty == ec for e in timeline.events)
            }
        }
        
        if dated_events:
            dates = [e.date for e in dated_events]
            timeline_span = (max(dates) - min(dates)).days
            
            stats.update({
                'timeline_span_days': timeline_span,
                'timeline_start': min(dates).isoformat(),
                'timeline_end': max(dates).isoformat(),
                'avg_events_per_month': len(dated_events) / max(1, timeline_span / 30),
                'event_density': len(dated_events) / max(1, timeline_span)
            })
            
            # Monthly distribution
            monthly_dist = defaultdict(int)
            for event in dated_events:
                month_key = f"{event.date.year}-{event.date.month:02d}"
                monthly_dist[month_key] += 1
            
            stats['monthly_distribution'] = dict(monthly_dist)
        
        return stats
    
    def _generate_recommendations(self, timeline: Timeline, 
                                insights: ChronologyInsights) -> List[str]:
        """Generate recommendations based on chronological analysis."""
        recommendations = []
        
        # Recommendations based on gaps
        if insights.timeline_gaps:
            high_significance_gaps = [g for g in insights.timeline_gaps if g.significance == "high"]
            if high_significance_gaps:
                recommendations.append(
                    f"Investigate {len(high_significance_gaps)} significant timeline gaps that may contain missing events"
                )
        
        # Recommendations based on conflicts
        if insights.timeline_conflicts:
            critical_conflicts = [c for c in insights.timeline_conflicts if c.severity in ["high", "critical"]]
            if critical_conflicts:
                recommendations.append(
                    f"Resolve {len(critical_conflicts)} critical timeline conflicts to ensure accuracy"
                )
        
        # Recommendations based on patterns
        escalation_patterns = [p for p in insights.detected_patterns if p.pattern_type == PatternType.ESCALATION_PATTERN]
        if escalation_patterns:
            recommendations.append("Monitor escalation patterns for potential intervention points")
        
        # Recommendations based on clustering
        if insights.event_clusters:
            dense_clusters = [c for c in insights.event_clusters if c.density_score > 1.0]
            if dense_clusters:
                recommendations.append(
                    f"Review {len(dense_clusters)} high-activity periods for completeness"
                )
        
        # Data quality recommendations
        undated_events = [e for e in timeline.events if not e.date]
        if len(undated_events) > len(timeline.events) * 0.2:  # More than 20% undated
            recommendations.append("Improve date extraction to reduce undated events")
        
        # Confidence recommendations
        low_confidence_events = [e for e in timeline.events if e.confidence < 0.5]
        if len(low_confidence_events) > len(timeline.events) * 0.3:  # More than 30% low confidence
            recommendations.append("Review low-confidence events for accuracy")
        
        return recommendations
    
    def _calculate_analysis_confidence(self, timeline: Timeline, 
                                     insights: ChronologyInsights) -> float:
        """Calculate overall confidence in chronological analysis."""
        
        confidence_factors = []
        
        # Timeline completeness
        dated_ratio = len([e for e in timeline.events if e.date]) / max(1, len(timeline.events))
        confidence_factors.append(dated_ratio * 0.3)
        
        # Average event confidence
        if timeline.events:
            avg_event_confidence = sum(e.confidence for e in timeline.events) / len(timeline.events)
            confidence_factors.append(avg_event_confidence * 0.3)
        
        # Pattern detection success
        pattern_confidence = min(1.0, len(insights.detected_patterns) * 0.1)
        confidence_factors.append(pattern_confidence * 0.2)
        
        # Conflict severity (lower conflicts = higher confidence)
        if insights.timeline_conflicts:
            critical_conflicts = len([c for c in insights.timeline_conflicts if c.severity == "critical"])
            conflict_penalty = min(0.5, critical_conflicts * 0.1)
            confidence_factors.append((1.0 - conflict_penalty) * 0.2)
        else:
            confidence_factors.append(0.2)
        
        return sum(confidence_factors)
    
    # Helper methods
    
    def _is_chronological_sequence(self, events: List[TimelineEvent]) -> bool:
        """Check if events are in chronological order."""
        for i in range(1, len(events)):
            if events[i].date < events[i-1].date:
                return False
        return True
    
    def _is_increasing_trend(self, values: List[int]) -> bool:
        """Check if values show an increasing trend."""
        if len(values) < 3:
            return False
        
        increases = 0
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increases += 1
        
        return increases >= len(values) // 2
    
    def _suggest_gap_events(self, prev_event: TimelineEvent, 
                          next_event: TimelineEvent) -> List[str]:
        """Suggest possible events for a timeline gap."""
        suggestions = []
        
        # Based on procedural sequences
        for sequence_name, sequence in self.procedural_sequences.items():
            if prev_event.event_type in sequence and next_event.event_type in sequence:
                prev_idx = sequence.index(prev_event.event_type)
                next_idx = sequence.index(next_event.event_type)
                
                if prev_idx < next_idx:
                    # Suggest intermediate events
                    for i in range(prev_idx + 1, next_idx):
                        suggestions.append(sequence[i].value)
        
        return suggestions
    
    def _create_temporal_clusters(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Create temporal clusters of events."""
        clusters = []
        
        if not events:
            return clusters
        
        current_cluster = [events[0]]
        
        for i in range(1, len(events)):
            time_diff = (events[i].date - current_cluster[-1].date).days
            
            if time_diff <= self.analysis_config['cluster_time_window_days']:
                current_cluster.append(events[i])
            else:
                if len(current_cluster) >= 3:
                    clusters.append({
                        'type': 'temporal',
                        'events': current_cluster,
                        'description': f"Temporal cluster of {len(current_cluster)} events"
                    })
                current_cluster = [events[i]]
        
        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append({
                'type': 'temporal',
                'events': current_cluster,
                'description': f"Temporal cluster of {len(current_cluster)} events"
            })
        
        return clusters
    
    def _create_type_clusters(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Create clusters based on event types."""
        clusters = []
        
        # Group by event type
        events_by_type = defaultdict(list)
        for event in events:
            events_by_type[event.event_type].append(event)
        
        for event_type, type_events in events_by_type.items():
            if len(type_events) >= 3:
                clusters.append({
                    'type': 'event_type',
                    'events': type_events,
                    'description': f"Cluster of {event_type.value} events"
                })
        
        return clusters
    
    def _create_participant_clusters(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Create clusters based on shared participants."""
        clusters = []
        
        # Group by participants
        participant_events = defaultdict(list)
        for event in events:
            for participant in event.participants:
                participant_events[participant].append(event)
        
        for participant, part_events in participant_events.items():
            if len(part_events) >= 3:
                clusters.append({
                    'type': 'participant',
                    'events': part_events,
                    'description': f"Events involving {participant}"
                })
        
        return clusters
    
    def _calculate_cluster_coherence(self, events: List[TimelineEvent]) -> float:
        """Calculate how coherent/related events in a cluster are."""
        if len(events) <= 1:
            return 1.0
        
        coherence_score = 0.0
        comparisons = 0
        
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                event1, event2 = events[i], events[j]
                
                # Same type bonus
                if event1.event_type == event2.event_type:
                    coherence_score += 0.3
                
                # Shared participants bonus
                shared_participants = set(event1.participants) & set(event2.participants)
                if shared_participants:
                    coherence_score += len(shared_participants) * 0.2
                
                # Causal relationship bonus
                if event2.event_id in event1.leads_to or event1.event_id in event2.caused_by:
                    coherence_score += 0.4
                
                comparisons += 1
        
        return min(1.0, coherence_score / max(1, comparisons))
    
    def _find_central_event(self, events: List[TimelineEvent]) -> Optional[str]:
        """Find the most central event in a cluster."""
        if not events:
            return None
        
        # Score events by centrality (connections, confidence, importance)
        scores = {}
        
        for event in events:
            score = 0.0
            
            # Confidence bonus
            score += event.confidence * 0.3
            
            # Connection bonus
            score += len(event.caused_by) * 0.2
            score += len(event.leads_to) * 0.2
            score += len(event.concurrent_with) * 0.1
            
            # Important event type bonus
            important_types = {EventType.FILING, EventType.ORDER, EventType.SETTLEMENT, EventType.TRIAL}
            if event.event_type in important_types:
                score += 0.3
            
            scores[event.event_id] = score
        
        # Return event with highest score
        return max(scores.items(), key=lambda x: x[1])[0] if scores else events[0].event_id
    
    def _evaluate_causal_relationship(self, cause_event: TimelineEvent, 
                                    effect_event: TimelineEvent) -> Optional[CausalRelationship]:
        """Evaluate if two events have a causal relationship."""
        
        # Time constraint: effect must come after cause
        if not (cause_event.date and effect_event.date):
            return None
        
        time_delay = effect_event.date - cause_event.date
        if time_delay.days < 0 or time_delay.days > self.analysis_config['causal_max_delay_days']:
            return None
        
        # Check for known causal patterns
        if not self._might_be_causal_relationship(cause_event, effect_event):
            return None
        
        # Calculate relationship strength
        strength = "weak"
        confidence = 0.3
        
        # Direct procedural relationships
        if (cause_event.event_type, effect_event.event_type) in [
            (EventType.FILING, EventType.HEARING),
            (EventType.MOTION, EventType.ORDER),
            (EventType.HEARING, EventType.ORDER)
        ]:
            strength = "strong"
            confidence = 0.8
        
        # Shared participants strengthen relationship
        shared_participants = set(cause_event.participants) & set(effect_event.participants)
        if shared_participants:
            confidence += len(shared_participants) * 0.1
            strength = "moderate" if strength == "weak" else strength
        
        # Time proximity strengthens relationship
        if time_delay.days <= 7:
            confidence += 0.2
        elif time_delay.days <= 30:
            confidence += 0.1
        
        confidence = min(1.0, confidence)
        
        return CausalRelationship(
            relationship_id=f"causal_{cause_event.event_id}_{effect_event.event_id}",
            cause_event=cause_event.event_id,
            effect_event=effect_event.event_id,
            relationship_type="direct",
            confidence=confidence,
            time_delay=time_delay,
            strength=strength,
            evidence=[
                f"Temporal sequence: {cause_event.event_type.value} → {effect_event.event_type.value}",
                f"Time delay: {time_delay.days} days"
            ]
        )
    
    def _might_be_causal_relationship(self, prev_event: TimelineEvent, 
                                    current_event: TimelineEvent) -> bool:
        """Simple causal relationship check (from timeline_extractor)."""
        causal_patterns = {
            (EventType.FILING, EventType.HEARING): True,
            (EventType.MOTION, EventType.ORDER): True,
            (EventType.DISCOVERY, EventType.DEPOSITION): True,
            (EventType.HEARING, EventType.ORDER): True,
            (EventType.CONTRACT, EventType.PAYMENT): True,
            (EventType.INCIDENT, EventType.FILING): True
        }
        
        event_pair = (prev_event.event_type, current_event.event_type)
        return causal_patterns.get(event_pair, False)
    
    # Conflict detection methods
    
    def _detect_date_inconsistencies(self, timeline: Timeline) -> List[TimelineConflict]:
        """Detect date inconsistencies in the timeline."""
        conflicts = []
        
        # Implementation would check for impossible dates, contradictory date information, etc.
        
        return conflicts
    
    def _detect_sequence_violations(self, timeline: Timeline) -> List[TimelineConflict]:
        """Detect violations of expected procedural sequences."""
        conflicts = []
        
        # Check precedence rules
        for event in timeline.events:
            if event.event_type in self.precedence_rules:
                required_predecessors = self.precedence_rules[event.event_type]
                
                # Check if required predecessors exist
                for required_type in required_predecessors:
                    predecessors = [
                        e for e in timeline.events 
                        if (e.event_type == required_type and 
                            e.date and event.date and 
                            e.date < event.date)
                    ]
                    
                    if not predecessors:
                        conflicts.append(TimelineConflict(
                            conflict_id=f"seq_violation_{event.event_id}_{required_type.value}",
                            conflict_type=ConflictType.SEQUENCE_VIOLATION,
                            description=f"{event.event_type.value} without required {required_type.value}",
                            affected_events=[event.event_id],
                            severity="medium",
                            suggested_resolution=f"Verify if {required_type.value} occurred before {event.event_type.value}",
                            evidence=[f"No {required_type.value} found before {event.event_type.value}"]
                        ))
        
        return conflicts
    
    def _detect_impossible_timing(self, timeline: Timeline) -> List[TimelineConflict]:
        """Detect impossible timing scenarios."""
        conflicts = []
        
        # Check for events that are too close in time to be possible
        dated_events = [e for e in timeline.events if e.date]
        dated_events.sort(key=lambda x: x.date)
        
        for i in range(1, len(dated_events)):
            prev_event = dated_events[i-1]
            curr_event = dated_events[i]
            
            time_diff = (curr_event.date - prev_event.date).total_seconds() / 3600  # hours
            
            # Check for impossibly close events
            if time_diff < self.analysis_config['conflict_tolerance_hours']:
                # Some event types can't happen simultaneously
                impossible_pairs = [
                    (EventType.HEARING, EventType.HEARING),  # Can't have two hearings at once
                    (EventType.TRIAL, EventType.TRIAL),      # Can't have two trials at once
                ]
                
                if (prev_event.event_type, curr_event.event_type) in impossible_pairs:
                    conflicts.append(TimelineConflict(
                        conflict_id=f"timing_{prev_event.event_id}_{curr_event.event_id}",
                        conflict_type=ConflictType.IMPOSSIBLE_TIMING,
                        description=f"Two {prev_event.event_type.value} events too close in time",
                        affected_events=[prev_event.event_id, curr_event.event_id],
                        severity="high",
                        suggested_resolution="Verify dates and resolve timing conflict",
                        evidence=[f"Only {time_diff:.1f} hours between events"]
                    ))
        
        return conflicts
    
    def _detect_missing_prerequisites(self, timeline: Timeline) -> List[TimelineConflict]:
        """Detect missing prerequisite events."""
        conflicts = []
        
        # This would be similar to sequence violations but more comprehensive
        # Implementation would check for logical prerequisites
        
        return conflicts
    
    def _detect_deadline_violations(self, timeline: Timeline) -> List[TimelineConflict]:
        """Detect deadline violations."""
        conflicts = []
        
        deadline_events = [e for e in timeline.events if e.event_type == EventType.DEADLINE and e.date]
        
        for deadline in deadline_events:
            # Look for events that should have happened by this deadline
            # This is a simplified check - in practice would be more sophisticated
            pass
        
        return conflicts