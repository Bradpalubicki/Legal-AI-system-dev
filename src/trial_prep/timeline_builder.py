"""
Timeline and Chronology Builder

Comprehensive timeline generation system for trial preparation including
chronological analysis of events, evidence mapping, witness correlation,
and visual timeline creation for case presentation.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
from pathlib import Path
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of timeline events."""
    INCIDENT = "incident"
    DOCUMENT_CREATED = "document_created"
    COMMUNICATION = "communication"
    MEETING = "meeting"
    TRANSACTION = "transaction"
    LEGAL_ACTION = "legal_action"
    WITNESS_OBSERVATION = "witness_observation"
    EVIDENCE_COLLECTED = "evidence_collected"
    INVESTIGATION = "investigation"
    CONTRACT_SIGNED = "contract_signed"
    DEADLINE = "deadline"
    COURT_FILING = "court_filing"
    DISCOVERY = "discovery"
    DEPOSITION = "deposition"
    HEARING = "hearing"
    SETTLEMENT_DISCUSSION = "settlement_discussion"

class EventImportance(Enum):
    """Importance level of timeline events."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1

class TimelineType(Enum):
    """Types of timelines that can be generated."""
    COMPREHENSIVE = "comprehensive"
    FACTUAL_ONLY = "factual_only"
    LEGAL_ACTIONS = "legal_actions"
    COMMUNICATIONS = "communications"
    EVIDENCE_BASED = "evidence_based"
    WITNESS_PERSPECTIVE = "witness_perspective"
    CAUSATION_FOCUSED = "causation_focused"

class EventSource(Enum):
    """Source of timeline event information."""
    DOCUMENT = "document"
    WITNESS_STATEMENT = "witness_statement"
    DEPOSITION = "deposition"
    EVIDENCE = "evidence"
    PUBLIC_RECORD = "public_record"
    EXPERT_ANALYSIS = "expert_analysis"
    INVESTIGATION = "investigation"
    OPPOSING_PARTY = "opposing_party"

class VerificationLevel(Enum):
    """Level of verification for timeline events."""
    CONFIRMED = "confirmed"
    CORROBORATED = "corroborated"
    SINGLE_SOURCE = "single_source"
    DISPUTED = "disputed"
    ALLEGED = "alleged"
    INFERRED = "inferred"

@dataclass
class TimelineEvent:
    """Individual event in a case timeline."""
    event_id: str
    title: str
    description: str
    event_type: EventType
    date: date
    time: Optional[datetime] = None
    
    # Importance and verification
    importance: EventImportance = EventImportance.MEDIUM
    verification_level: VerificationLevel = VerificationLevel.SINGLE_SOURCE
    
    # Sources and evidence
    sources: List[str] = field(default_factory=list)  # Document/evidence IDs
    source_type: EventSource = EventSource.DOCUMENT
    supporting_evidence: List[str] = field(default_factory=list)
    
    # Relationships
    related_events: List[str] = field(default_factory=list)  # Event IDs
    caused_by: Optional[str] = None  # Event ID
    caused_events: List[str] = field(default_factory=list)  # Event IDs
    
    # Participants
    people_involved: List[str] = field(default_factory=list)
    organizations_involved: List[str] = field(default_factory=list)
    witnesses: List[str] = field(default_factory=list)  # Witness IDs
    
    # Location and context
    location: Optional[str] = None
    jurisdiction: Optional[str] = None
    context: str = ""
    
    # Legal significance
    legal_relevance: str = ""
    statute_of_limitations_impact: bool = False
    liability_impact: str = ""
    damages_impact: str = ""
    
    # Metadata
    confidence_score: float = 0.7  # 0-1 scale
    disputed_aspects: List[str] = field(default_factory=list)
    alternative_versions: List[str] = field(default_factory=list)
    
    # Processing metadata
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    last_modified: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)

@dataclass
class CaseTimeline:
    """Complete timeline for a legal case."""
    timeline_id: str
    case_id: str
    title: str
    timeline_type: TimelineType
    
    # Events and structure
    events: List[str] = field(default_factory=list)  # Event IDs in chronological order
    key_dates: Dict[str, str] = field(default_factory=dict)  # Special dates
    phases: List[Dict[str, Any]] = field(default_factory=list)  # Case phases
    
    # Analysis results
    gaps_identified: List[str] = field(default_factory=list)
    inconsistencies: List[str] = field(default_factory=list)
    causation_chains: List[List[str]] = field(default_factory=list)  # Chains of event IDs
    
    # Temporal analysis
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: int = 0
    critical_period_start: Optional[date] = None
    critical_period_end: Optional[date] = None
    
    # Presentation settings
    visual_style: str = "standard"
    highlight_events: List[str] = field(default_factory=list)  # Event IDs to highlight
    color_coding: Dict[str, str] = field(default_factory=dict)  # Event type colors
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    version: int = 1

class TimelineAnalyzer:
    """Analyzes timeline events for patterns, gaps, and inconsistencies."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".TimelineAnalyzer")
    
    def analyze_timeline_completeness(self, timeline: CaseTimeline, 
                                    events: List[TimelineEvent]) -> Dict[str, Any]:
        """Analyze timeline for completeness and identify gaps."""
        analysis = {
            'completeness_score': 0.0,
            'temporal_gaps': [],
            'missing_evidence_periods': [],
            'sparse_documentation_periods': [],
            'recommendations': []
        }
        
        if not events:
            analysis['recommendations'].append("No events in timeline")
            return analysis
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda e: e.date)
        
        # Identify temporal gaps
        gaps = []
        for i in range(len(sorted_events) - 1):
            current_event = sorted_events[i]
            next_event = sorted_events[i + 1]
            
            gap_days = (next_event.date - current_event.date).days
            
            # Significant gaps (more than 30 days with no events)
            if gap_days > 30:
                gaps.append({
                    'start_date': current_event.date,
                    'end_date': next_event.date,
                    'duration_days': gap_days,
                    'before_event': current_event.title,
                    'after_event': next_event.title
                })
        
        analysis['temporal_gaps'] = gaps
        
        # Analyze documentation density
        event_density = self._calculate_event_density(sorted_events)
        sparse_periods = [period for period, density in event_density.items() if density < 0.1]
        analysis['sparse_documentation_periods'] = sparse_periods
        
        # Calculate completeness score
        total_days = (sorted_events[-1].date - sorted_events[0].date).days
        documented_days = len(set(event.date for event in sorted_events))
        
        if total_days > 0:
            analysis['completeness_score'] = documented_days / total_days
        else:
            analysis['completeness_score'] = 1.0
        
        # Generate recommendations
        recommendations = []
        
        if len(gaps) > 0:
            recommendations.append(f"Investigate {len(gaps)} significant temporal gaps")
        
        if analysis['completeness_score'] < 0.3:
            recommendations.append("Timeline appears incomplete - gather more evidence")
        
        if len(sparse_periods) > 0:
            recommendations.append("Focus on periods with sparse documentation")
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def identify_causation_chains(self, events: List[TimelineEvent]) -> List[List[str]]:
        """Identify chains of causally related events."""
        chains = []
        processed_events = set()
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda e: e.date)
        
        for event in sorted_events:
            if event.event_id in processed_events:
                continue
            
            # Start a new chain
            chain = self._build_causation_chain(event, events)
            if len(chain) > 1:  # Only include chains with multiple events
                chains.append(chain)
                processed_events.update(chain)
        
        return chains
    
    def detect_timeline_inconsistencies(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Detect logical inconsistencies in timeline."""
        inconsistencies = []
        
        # Check for impossible temporal relationships
        for event in events:
            for caused_event_id in event.caused_events:
                caused_event = next((e for e in events if e.event_id == caused_event_id), None)
                if caused_event and caused_event.date < event.date:
                    inconsistencies.append({
                        'type': 'temporal_impossibility',
                        'description': f'Event "{event.title}" supposedly caused "{caused_event.title}" but occurred after it',
                        'events_involved': [event.event_id, caused_event_id],
                        'severity': 'high'
                    })
        
        # Check for conflicting witness accounts
        witness_events = defaultdict(list)
        for event in events:
            for witness in event.witnesses:
                witness_events[witness].append(event)
        
        for witness, witness_event_list in witness_events.items():
            # Check for same-time conflicting locations
            same_day_events = defaultdict(list)
            for event in witness_event_list:
                same_day_events[event.date].append(event)
            
            for date_events in same_day_events.values():
                if len(date_events) > 1:
                    locations = [e.location for e in date_events if e.location]
                    if len(set(locations)) > 1:  # Different locations on same day
                        inconsistencies.append({
                            'type': 'witness_location_conflict',
                            'description': f'Witness {witness} reported being in different locations on same day',
                            'events_involved': [e.event_id for e in date_events],
                            'severity': 'medium'
                        })
        
        # Check for disputed event conflicts
        for event in events:
            if event.verification_level == VerificationLevel.DISPUTED:
                inconsistencies.append({
                    'type': 'disputed_event',
                    'description': f'Event "{event.title}" has disputed aspects: {", ".join(event.disputed_aspects)}',
                    'events_involved': [event.event_id],
                    'severity': 'medium'
                })
        
        return inconsistencies
    
    def analyze_critical_periods(self, events: List[TimelineEvent], 
                               case_type: str = "general") -> Dict[str, Any]:
        """Identify critical time periods in the case."""
        analysis = {
            'critical_periods': [],
            'statute_limitations_dates': [],
            'high_activity_periods': [],
            'decision_points': []
        }
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda e: e.date)
        
        # Identify high-importance event clusters
        importance_threshold = EventImportance.HIGH.value
        critical_events = [e for e in sorted_events if e.importance.value >= importance_threshold]
        
        # Group critical events into periods
        if critical_events:
            periods = self._cluster_events_by_time(critical_events, max_gap_days=14)
            analysis['critical_periods'] = periods
        
        # Identify statute of limitations considerations
        sol_events = [e for e in sorted_events if e.statute_of_limitations_impact]
        analysis['statute_limitations_dates'] = [
            {'date': e.date, 'event': e.title, 'impact': e.legal_relevance}
            for e in sol_events
        ]
        
        # Identify high-activity periods (many events in short time)
        activity_periods = self._identify_high_activity_periods(sorted_events)
        analysis['high_activity_periods'] = activity_periods
        
        # Identify decision points (events that triggered other events)
        decision_events = [e for e in sorted_events if len(e.caused_events) > 0]
        analysis['decision_points'] = [
            {
                'date': e.date,
                'event': e.title,
                'consequences': len(e.caused_events),
                'impact': e.legal_relevance
            }
            for e in decision_events
        ]
        
        return analysis
    
    def _calculate_event_density(self, events: List[TimelineEvent]) -> Dict[str, float]:
        """Calculate event density over time periods."""
        if not events:
            return {}
        
        # Group events by month
        monthly_counts = defaultdict(int)
        for event in events:
            month_key = f"{event.date.year}-{event.date.month:02d}"
            monthly_counts[month_key] += 1
        
        # Calculate density as events per month
        return dict(monthly_counts)
    
    def _build_causation_chain(self, start_event: TimelineEvent, 
                             all_events: List[TimelineEvent]) -> List[str]:
        """Build causation chain starting from an event."""
        chain = [start_event.event_id]
        event_dict = {e.event_id: e for e in all_events}
        
        # Follow forward causation
        current_events = [start_event]
        processed = {start_event.event_id}
        
        while current_events:
            next_events = []
            for current in current_events:
                for caused_id in current.caused_events:
                    if caused_id in event_dict and caused_id not in processed:
                        chain.append(caused_id)
                        next_events.append(event_dict[caused_id])
                        processed.add(caused_id)
            
            current_events = next_events
        
        return chain
    
    def _cluster_events_by_time(self, events: List[TimelineEvent], 
                              max_gap_days: int = 7) -> List[Dict[str, Any]]:
        """Cluster events into time periods."""
        if not events:
            return []
        
        clusters = []
        current_cluster = [events[0]]
        
        for i in range(1, len(events)):
            days_gap = (events[i].date - current_cluster[-1].date).days
            
            if days_gap <= max_gap_days:
                current_cluster.append(events[i])
            else:
                # Finalize current cluster and start new one
                if len(current_cluster) > 1:  # Only include multi-event clusters
                    clusters.append({
                        'start_date': current_cluster[0].date,
                        'end_date': current_cluster[-1].date,
                        'event_count': len(current_cluster),
                        'events': [e.event_id for e in current_cluster],
                        'importance_score': sum(e.importance.value for e in current_cluster) / len(current_cluster)
                    })
                
                current_cluster = [events[i]]
        
        # Don't forget the last cluster
        if len(current_cluster) > 1:
            clusters.append({
                'start_date': current_cluster[0].date,
                'end_date': current_cluster[-1].date,
                'event_count': len(current_cluster),
                'events': [e.event_id for e in current_cluster],
                'importance_score': sum(e.importance.value for e in current_cluster) / len(current_cluster)
            })
        
        return clusters
    
    def _identify_high_activity_periods(self, events: List[TimelineEvent], 
                                      window_days: int = 30) -> List[Dict[str, Any]]:
        """Identify periods with unusually high event activity."""
        if not events or len(events) < 3:
            return []
        
        # Calculate average event frequency
        total_days = (events[-1].date - events[0].date).days
        avg_frequency = len(events) / max(total_days, 1)
        
        high_activity_periods = []
        
        # Use sliding window to find high-activity periods
        for i, event in enumerate(events):
            window_end = event.date + timedelta(days=window_days)
            window_events = [e for e in events[i:] if e.date <= window_end]
            
            if len(window_events) > avg_frequency * window_days * 2:  # 2x average activity
                high_activity_periods.append({
                    'start_date': event.date,
                    'end_date': window_end,
                    'event_count': len(window_events),
                    'frequency_ratio': len(window_events) / (avg_frequency * window_days),
                    'events': [e.event_id for e in window_events]
                })
        
        return high_activity_periods

class TimelineBuilder:
    """Main timeline building system coordinating all components."""
    
    def __init__(self):
        self.timelines: Dict[str, CaseTimeline] = {}
        self.events: Dict[str, TimelineEvent] = {}
        self.analyzer = TimelineAnalyzer()
        self.logger = logging.getLogger(__name__ + ".TimelineBuilder")
    
    def create_timeline(self, case_id: str, title: str, 
                       timeline_type: TimelineType = TimelineType.COMPREHENSIVE) -> str:
        """Create new case timeline."""
        timeline_id = str(uuid.uuid4())
        
        timeline = CaseTimeline(
            timeline_id=timeline_id,
            case_id=case_id,
            title=title,
            timeline_type=timeline_type
        )
        
        self.timelines[timeline_id] = timeline
        self.logger.info(f"Created timeline: {timeline_id}")
        return timeline_id
    
    def add_event(self, event: TimelineEvent) -> str:
        """Add event to the system."""
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        
        self.events[event.event_id] = event
        self.logger.info(f"Added timeline event: {event.event_id}")
        return event.event_id
    
    def add_event_to_timeline(self, timeline_id: str, event_id: str) -> bool:
        """Add event to specific timeline."""
        if timeline_id not in self.timelines or event_id not in self.events:
            return False
        
        timeline = self.timelines[timeline_id]
        if event_id not in timeline.events:
            timeline.events.append(event_id)
            
            # Update timeline date bounds
            event = self.events[event_id]
            if not timeline.start_date or event.date < timeline.start_date:
                timeline.start_date = event.date
            if not timeline.end_date or event.date > timeline.end_date:
                timeline.end_date = event.date
            
            # Update duration
            if timeline.start_date and timeline.end_date:
                timeline.duration_days = (timeline.end_date - timeline.start_date).days
            
            # Re-sort events chronologically
            timeline.events.sort(key=lambda eid: self.events[eid].date)
            
            timeline.last_updated = datetime.now()
            
            self.logger.info(f"Added event {event_id} to timeline {timeline_id}")
            
        return True
    
    def build_timeline_from_documents(self, case_id: str, documents: List[Dict[str, Any]],
                                    timeline_title: str = "Case Timeline") -> str:
        """Build timeline by extracting events from documents."""
        timeline_id = self.create_timeline(case_id, timeline_title)
        
        for doc in documents:
            events = self._extract_events_from_document(doc)
            for event in events:
                event_id = self.add_event(event)
                self.add_event_to_timeline(timeline_id, event_id)
        
        # Analyze timeline after building
        self._analyze_timeline_post_build(timeline_id)
        
        return timeline_id
    
    def build_timeline_from_evidence(self, case_id: str, evidence_items: List[Dict[str, Any]],
                                   timeline_title: str = "Evidence Timeline") -> str:
        """Build timeline from evidence items."""
        timeline_id = self.create_timeline(case_id, timeline_title, TimelineType.EVIDENCE_BASED)
        
        for evidence in evidence_items:
            event = self._create_event_from_evidence(evidence)
            if event:
                event_id = self.add_event(event)
                self.add_event_to_timeline(timeline_id, event_id)
        
        self._analyze_timeline_post_build(timeline_id)
        return timeline_id
    
    def generate_witness_timeline(self, witness_id: str, witness_statements: List[Dict[str, Any]],
                                case_id: str) -> str:
        """Generate timeline from specific witness perspective."""
        timeline_title = f"Witness {witness_id} Timeline"
        timeline_id = self.create_timeline(case_id, timeline_title, TimelineType.WITNESS_PERSPECTIVE)
        
        for statement in witness_statements:
            events = self._extract_events_from_witness_statement(statement, witness_id)
            for event in events:
                event_id = self.add_event(event)
                self.add_event_to_timeline(timeline_id, event_id)
        
        return timeline_id
    
    def merge_timelines(self, primary_timeline_id: str, 
                       secondary_timeline_ids: List[str],
                       merged_title: str = "Merged Timeline") -> str:
        """Merge multiple timelines into a comprehensive view."""
        if primary_timeline_id not in self.timelines:
            raise ValueError(f"Primary timeline {primary_timeline_id} not found")
        
        primary_timeline = self.timelines[primary_timeline_id]
        
        # Create new merged timeline
        merged_id = self.create_timeline(primary_timeline.case_id, merged_title)
        merged_timeline = self.timelines[merged_id]
        
        # Add all events from primary timeline
        for event_id in primary_timeline.events:
            self.add_event_to_timeline(merged_id, event_id)
        
        # Add events from secondary timelines
        for timeline_id in secondary_timeline_ids:
            if timeline_id in self.timelines:
                secondary_timeline = self.timelines[timeline_id]
                for event_id in secondary_timeline.events:
                    if event_id not in merged_timeline.events:
                        self.add_event_to_timeline(merged_id, event_id)
        
        # Analyze merged timeline
        self._analyze_timeline_post_build(merged_id)
        
        return merged_id
    
    def identify_timeline_gaps(self, timeline_id: str) -> Dict[str, Any]:
        """Identify and analyze gaps in timeline."""
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")
        
        timeline = self.timelines[timeline_id]
        timeline_events = [self.events[eid] for eid in timeline.events]
        
        return self.analyzer.analyze_timeline_completeness(timeline, timeline_events)
    
    def generate_timeline_summary(self, timeline_id: str) -> Dict[str, Any]:
        """Generate comprehensive timeline summary."""
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")
        
        timeline = self.timelines[timeline_id]
        timeline_events = [self.events[eid] for eid in timeline.events]
        
        summary = {
            'timeline_info': {
                'title': timeline.title,
                'type': timeline.timeline_type.value,
                'total_events': len(timeline_events),
                'date_range': f"{timeline.start_date} to {timeline.end_date}" if timeline.start_date and timeline.end_date else "N/A",
                'duration_days': timeline.duration_days
            },
            'event_breakdown': {},
            'completeness_analysis': {},
            'critical_periods': {},
            'inconsistencies': [],
            'causation_chains': [],
            'key_insights': []
        }
        
        if not timeline_events:
            summary['key_insights'].append("Timeline contains no events")
            return summary
        
        # Event type breakdown
        type_counts = {}
        importance_counts = {}
        verification_counts = {}
        
        for event in timeline_events:
            # Type counts
            event_type = event.event_type.value
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
            
            # Importance counts
            importance = event.importance.name
            importance_counts[importance] = importance_counts.get(importance, 0) + 1
            
            # Verification counts
            verification = event.verification_level.name
            verification_counts[verification] = verification_counts.get(verification, 0) + 1
        
        summary['event_breakdown'] = {
            'by_type': type_counts,
            'by_importance': importance_counts,
            'by_verification': verification_counts
        }
        
        # Completeness analysis
        summary['completeness_analysis'] = self.analyzer.analyze_timeline_completeness(
            timeline, timeline_events
        )
        
        # Critical periods analysis
        summary['critical_periods'] = self.analyzer.analyze_critical_periods(timeline_events)
        
        # Inconsistency detection
        summary['inconsistencies'] = self.analyzer.detect_timeline_inconsistencies(timeline_events)
        
        # Causation chain analysis
        summary['causation_chains'] = self.analyzer.identify_causation_chains(timeline_events)
        
        # Generate key insights
        insights = []
        
        critical_event_count = importance_counts.get('CRITICAL', 0)
        if critical_event_count > 0:
            insights.append(f"Timeline contains {critical_event_count} critical events")
        
        disputed_count = verification_counts.get('DISPUTED', 0)
        if disputed_count > 0:
            insights.append(f"{disputed_count} events have disputed aspects requiring attention")
        
        if len(summary['inconsistencies']) > 0:
            insights.append(f"Timeline contains {len(summary['inconsistencies'])} inconsistencies")
        
        if len(summary['causation_chains']) > 0:
            insights.append(f"Identified {len(summary['causation_chains'])} causation chains")
        
        if summary['completeness_analysis'].get('completeness_score', 0) < 0.5:
            insights.append("Timeline appears incomplete - significant gaps identified")
        
        summary['key_insights'] = insights
        
        return summary
    
    def export_timeline(self, timeline_id: str, format: str = "json") -> Dict[str, Any]:
        """Export timeline in specified format."""
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")
        
        timeline = self.timelines[timeline_id]
        timeline_events = [self.events[eid] for eid in timeline.events]
        
        export_data = {
            'timeline': timeline,
            'events': timeline_events,
            'summary': self.generate_timeline_summary(timeline_id),
            'exported_date': datetime.now()
        }
        
        if format == "json":
            return export_data
        elif format == "csv":
            # Convert to CSV-friendly format
            csv_data = []
            for event in timeline_events:
                csv_data.append({
                    'Date': event.date,
                    'Time': event.time.strftime("%H:%M") if event.time else "",
                    'Title': event.title,
                    'Description': event.description,
                    'Type': event.event_type.value,
                    'Importance': event.importance.name,
                    'Verification': event.verification_level.name,
                    'Location': event.location or "",
                    'People Involved': "; ".join(event.people_involved),
                    'Legal Relevance': event.legal_relevance
                })
            return {'csv_data': csv_data}
        
        return export_data
    
    def search_events(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[TimelineEvent]:
        """Search timeline events by various criteria."""
        results = []
        query_lower = query.lower()
        
        for event in self.events.values():
            # Text search in title, description, and context
            searchable_text = (
                f"{event.title} {event.description} {event.context} " +
                f"{event.legal_relevance} {' '.join(event.notes)}"
            ).lower()
            
            if query_lower in searchable_text:
                # Apply filters if provided
                if filters:
                    if 'event_type' in filters and event.event_type != filters['event_type']:
                        continue
                    if 'importance_min' in filters and event.importance.value < filters['importance_min']:
                        continue
                    if 'date_from' in filters and event.date < filters['date_from']:
                        continue
                    if 'date_to' in filters and event.date > filters['date_to']:
                        continue
                    if 'verification_level' in filters and event.verification_level != filters['verification_level']:
                        continue
                
                results.append(event)
        
        # Sort by date (most recent first)
        return sorted(results, key=lambda x: x.date, reverse=True)
    
    def _extract_events_from_document(self, document: Dict[str, Any]) -> List[TimelineEvent]:
        """Extract timeline events from document content."""
        events = []
        
        # This would be more sophisticated in a real implementation
        # For now, create a basic event representing document creation
        
        doc_date = document.get('date_created')
        if isinstance(doc_date, str):
            doc_date = datetime.strptime(doc_date, "%Y-%m-%d").date()
        elif isinstance(doc_date, datetime):
            doc_date = doc_date.date()
        
        if doc_date:
            event = TimelineEvent(
                event_id=str(uuid.uuid4()),
                title=f"Document Created: {document.get('title', 'Untitled')}",
                description=document.get('description', ''),
                event_type=EventType.DOCUMENT_CREATED,
                date=doc_date,
                sources=[document.get('document_id', '')],
                source_type=EventSource.DOCUMENT,
                legal_relevance=document.get('legal_relevance', ''),
                created_by='system'
            )
            events.append(event)
        
        return events
    
    def _create_event_from_evidence(self, evidence: Dict[str, Any]) -> Optional[TimelineEvent]:
        """Create timeline event from evidence item."""
        evidence_date = evidence.get('date_collected') or evidence.get('date_created')
        
        if not evidence_date:
            return None
        
        if isinstance(evidence_date, str):
            evidence_date = datetime.strptime(evidence_date, "%Y-%m-%d").date()
        elif isinstance(evidence_date, datetime):
            evidence_date = evidence_date.date()
        
        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            title=f"Evidence Collected: {evidence.get('title', 'Evidence Item')}",
            description=evidence.get('description', ''),
            event_type=EventType.EVIDENCE_COLLECTED,
            date=evidence_date,
            sources=[evidence.get('evidence_id', '')],
            source_type=EventSource.EVIDENCE,
            legal_relevance=evidence.get('case_relevance', ''),
            created_by='system'
        )
        
        return event
    
    def _extract_events_from_witness_statement(self, statement: Dict[str, Any], 
                                             witness_id: str) -> List[TimelineEvent]:
        """Extract events from witness statement."""
        events = []
        
        # This would involve sophisticated NLP in a real implementation
        # For now, create basic events based on statement structure
        
        statement_date = statement.get('date')
        if statement_date and isinstance(statement_date, str):
            statement_date = datetime.strptime(statement_date, "%Y-%m-%d").date()
        elif isinstance(statement_date, datetime):
            statement_date = statement_date.date()
        
        if statement_date:
            event = TimelineEvent(
                event_id=str(uuid.uuid4()),
                title=f"Witness Observation: {statement.get('subject', 'Statement')}",
                description=statement.get('content', ''),
                event_type=EventType.WITNESS_OBSERVATION,
                date=statement_date,
                sources=[statement.get('statement_id', '')],
                source_type=EventSource.WITNESS_STATEMENT,
                witnesses=[witness_id],
                verification_level=VerificationLevel.SINGLE_SOURCE,
                created_by='system'
            )
            events.append(event)
        
        return events
    
    def _analyze_timeline_post_build(self, timeline_id: str) -> None:
        """Perform analysis after timeline construction."""
        if timeline_id not in self.timelines:
            return
        
        timeline = self.timelines[timeline_id]
        timeline_events = [self.events[eid] for eid in timeline.events]
        
        # Update timeline with analysis results
        completeness_analysis = self.analyzer.analyze_timeline_completeness(timeline, timeline_events)
        timeline.gaps_identified = completeness_analysis.get('recommendations', [])
        
        inconsistencies = self.analyzer.detect_timeline_inconsistencies(timeline_events)
        timeline.inconsistencies = [inc['description'] for inc in inconsistencies]
        
        causation_chains = self.analyzer.identify_causation_chains(timeline_events)
        timeline.causation_chains = causation_chains
        
        # Identify critical periods
        critical_analysis = self.analyzer.analyze_critical_periods(timeline_events)
        critical_periods = critical_analysis.get('critical_periods', [])
        if critical_periods:
            first_period = critical_periods[0]
            timeline.critical_period_start = first_period['start_date']
            timeline.critical_period_end = first_period['end_date']