"""
Conflict Prevention System for Legal Calendar Management

Proactive conflict prevention using predictive analytics, intelligent constraints,
and automated scheduling safeguards to prevent conflicts before they occur.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set, Callable
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import json
from abc import ABC, abstractmethod
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import networkx as nx

from .hearing_detector import HearingEvent, HearingType, HearingStatus, Location
from .advanced_conflict_detection import AdvancedConflictDetector, ScheduleConflict, ConflictType, ConflictSeverity
from .travel_time_calculator import TravelTimeCalculator, TravelTimeRequest, TransportMode
from .intelligent_scheduler import IntelligentScheduler, SchedulingSlot, Schedule

logger = logging.getLogger(__name__)


class PreventionStrategy(Enum):
    """Conflict prevention strategies."""
    PREDICTIVE_BLOCKING = "predictive_blocking"      # Block problematic time slots
    ADAPTIVE_BUFFERING = "adaptive_buffering"        # Dynamic buffer time adjustment
    INTELLIGENT_ROUTING = "intelligent_routing"       # Optimize travel sequences
    RESOURCE_BALANCING = "resource_balancing"        # Balance resource utilization
    PATTERN_LEARNING = "pattern_learning"            # Learn from historical patterns
    REAL_TIME_MONITORING = "real_time_monitoring"    # Continuous monitoring and adjustment
    STAKEHOLDER_COORDINATION = "stakeholder_coordination"  # Coordinate with all parties


class RiskLevel(Enum):
    """Risk levels for conflict prediction."""
    VERY_LOW = "very_low"    # 0-20%
    LOW = "low"             # 20-40%
    MEDIUM = "medium"       # 40-60%
    HIGH = "high"           # 60-80%
    CRITICAL = "critical"   # 80-100%


class PreventionAction(Enum):
    """Actions that can be taken to prevent conflicts."""
    BLOCK_SLOT = "block_slot"
    ADJUST_BUFFER = "adjust_buffer"
    SUGGEST_ALTERNATIVE = "suggest_alternative"
    NOTIFY_STAKEHOLDERS = "notify_stakeholders"
    RESCHEDULE_PROACTIVELY = "reschedule_proactively"
    RESERVE_BACKUP_RESOURCES = "reserve_backup_resources"
    COORDINATE_LOGISTICS = "coordinate_logistics"


@dataclass
class ConflictRisk:
    """Represents a predicted conflict risk."""
    risk_id: str
    risk_type: str
    risk_level: RiskLevel
    probability: float  # 0.0 to 1.0
    potential_impact: str  # description of impact
    
    # Risk context
    affected_events: List[str]  # Event IDs
    risk_factors: Dict[str, float]
    temporal_window: Tuple[datetime, datetime]
    location: Optional[str] = None
    resources_at_risk: List[str] = field(default_factory=list)
    
    # Prevention recommendations
    recommended_actions: List[PreventionAction] = field(default_factory=list)
    prevention_cost: float = 0.0  # Cost of prevention measures
    inaction_cost: float = 0.0   # Cost of not preventing
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    confidence: float = 0.8
    historical_precedent: bool = False
    
    def is_actionable(self) -> bool:
        """Check if risk is actionable (not expired and above threshold)."""
        return (datetime.now() < self.expires_at and 
                self.probability > 0.3 and 
                self.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL])
    
    def get_priority_score(self) -> float:
        """Calculate priority score for risk handling."""
        risk_weights = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.8,
            RiskLevel.MEDIUM: 0.6,
            RiskLevel.LOW: 0.4,
            RiskLevel.VERY_LOW: 0.2
        }
        
        base_score = self.probability * risk_weights.get(self.risk_level, 0.5)
        impact_multiplier = max(1.0, self.inaction_cost / max(self.prevention_cost, 1.0))
        time_urgency = max(0.1, 1.0 - (self.expires_at - datetime.now()).total_seconds() / 86400)
        
        return base_score * impact_multiplier * time_urgency
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'risk_id': self.risk_id,
            'risk_type': self.risk_type,
            'risk_level': self.risk_level.value,
            'probability': self.probability,
            'potential_impact': self.potential_impact,
            'affected_events': self.affected_events,
            'risk_factors': self.risk_factors,
            'temporal_window': [self.temporal_window[0].isoformat(), self.temporal_window[1].isoformat()],
            'location': self.location,
            'resources_at_risk': self.resources_at_risk,
            'recommended_actions': [action.value for action in self.recommended_actions],
            'prevention_cost': self.prevention_cost,
            'inaction_cost': self.inaction_cost,
            'detected_at': self.detected_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'confidence': self.confidence,
            'historical_precedent': self.historical_precedent,
            'priority_score': self.get_priority_score(),
            'is_actionable': self.is_actionable()
        }


@dataclass
class PreventionRule:
    """Rule for conflict prevention."""
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    
    # Rule conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    triggers: List[str] = field(default_factory=list)  # What events trigger this rule
    
    # Rule actions
    actions: List[PreventionAction] = field(default_factory=list)
    priority: int = 100  # Lower number = higher priority
    
    # Rule evaluation
    success_rate: float = 0.0  # Historical success rate
    last_applied: Optional[datetime] = None
    application_count: int = 0
    
    def matches_conditions(self, context: Dict[str, Any]) -> bool:
        """Check if rule conditions match the context."""
        for condition_key, condition_value in self.conditions.items():
            if condition_key not in context:
                return False
            
            context_value = context[condition_key]
            
            # Handle different condition types
            if isinstance(condition_value, dict):
                if 'min' in condition_value and context_value < condition_value['min']:
                    return False
                if 'max' in condition_value and context_value > condition_value['max']:
                    return False
            elif isinstance(condition_value, list):
                if context_value not in condition_value:
                    return False
            elif context_value != condition_value:
                return False
        
        return True


class ConflictPredictor:
    """Predicts potential conflicts using machine learning and statistical analysis."""
    
    def __init__(self):
        self.models = {
            'time_conflict': RandomForestClassifier(n_estimators=100, random_state=42),
            'resource_conflict': RandomForestClassifier(n_estimators=100, random_state=42),
            'travel_conflict': RandomForestClassifier(n_estimators=100, random_state=42)
        }
        
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
        self.feature_scaler = StandardScaler()
        
        # Historical patterns
        self.conflict_patterns = {}
        self.success_patterns = {}
        
    async def predict_conflicts(self, events: List[HearingEvent],
                              schedule: Optional[Schedule] = None,
                              prediction_horizon_days: int = 7) -> List[ConflictRisk]:
        """Predict potential conflicts in upcoming events."""
        risks = []
        
        # Time-based conflict prediction
        time_risks = await self._predict_time_conflicts(events, prediction_horizon_days)
        risks.extend(time_risks)
        
        # Resource-based conflict prediction
        resource_risks = await self._predict_resource_conflicts(events, prediction_horizon_days)
        risks.extend(resource_risks)
        
        # Travel-based conflict prediction
        travel_risks = await self._predict_travel_conflicts(events, prediction_horizon_days)
        risks.extend(travel_risks)
        
        # Pattern-based conflict prediction
        pattern_risks = await self._predict_pattern_conflicts(events, prediction_horizon_days)
        risks.extend(pattern_risks)
        
        # Anomaly detection
        anomaly_risks = await self._detect_scheduling_anomalies(events)
        risks.extend(anomaly_risks)
        
        # Sort by priority and remove duplicates
        unique_risks = self._deduplicate_risks(risks)
        unique_risks.sort(key=lambda r: r.get_priority_score(), reverse=True)
        
        logger.info(f"Predicted {len(unique_risks)} potential conflict risks")
        return unique_risks
    
    async def _predict_time_conflicts(self, events: List[HearingEvent],
                                    horizon_days: int) -> List[ConflictRisk]:
        """Predict time-based conflicts."""
        risks = []
        
        # Group events by time windows
        time_windows = self._create_time_windows(events, hours=2)  # 2-hour windows
        
        for window_start, window_events in time_windows.items():
            if len(window_events) > 3:  # Potential over-scheduling
                # Calculate conflict probability
                event_density = len(window_events)
                judges_involved = len(set(e.judge for e in window_events if e.judge))
                locations_involved = len(set(e.location.court_name if e.location else 'unknown' 
                                           for e in window_events))
                
                # Simple heuristic for conflict probability
                density_risk = min(1.0, event_density / 8.0)  # Risk increases with density
                judge_risk = 0.8 if judges_involved == 1 else 0.2  # Same judge = high risk
                location_risk = 0.6 if locations_involved == 1 else 0.3  # Same location = medium risk
                
                probability = (density_risk + judge_risk + location_risk) / 3.0
                
                if probability > 0.4:  # Above threshold
                    risk = ConflictRisk(
                        risk_id=f"time_conflict_{window_start.timestamp()}",
                        risk_type="temporal_overcrowding",
                        risk_level=self._probability_to_risk_level(probability),
                        probability=probability,
                        potential_impact=f"Multiple events ({len(window_events)}) in 2-hour window may conflict",
                        affected_events=[e.hearing_id for e in window_events],
                        risk_factors={
                            'event_density': density_risk,
                            'judge_conflict_risk': judge_risk,
                            'location_conflict_risk': location_risk
                        },
                        temporal_window=(window_start, window_start + timedelta(hours=2)),
                        recommended_actions=[
                            PreventionAction.ADJUST_BUFFER,
                            PreventionAction.SUGGEST_ALTERNATIVE,
                            PreventionAction.NOTIFY_STAKEHOLDERS
                        ],
                        prevention_cost=50.0 * len(window_events),
                        inaction_cost=200.0 * probability
                    )
                    risks.append(risk)
        
        return risks
    
    async def _predict_resource_conflicts(self, events: List[HearingEvent],
                                        horizon_days: int) -> List[ConflictRisk]:
        """Predict resource-based conflicts."""
        risks = []
        
        # Group events by resource usage
        resource_schedules = {}
        
        for event in events:
            # Extract required resources
            resources = self._extract_event_resources(event)
            
            for resource_type, resource_id in resources:
                key = f"{resource_type}:{resource_id}"
                
                if key not in resource_schedules:
                    resource_schedules[key] = []
                
                resource_schedules[key].append(event)
        
        # Analyze each resource for over-utilization
        for resource_key, resource_events in resource_schedules.items():
            if len(resource_events) > 1:
                # Check for time overlaps
                overlaps = self._find_time_overlaps(resource_events)
                
                if overlaps:
                    probability = min(1.0, len(overlaps) / len(resource_events))
                    
                    risk = ConflictRisk(
                        risk_id=f"resource_conflict_{hash(resource_key)}",
                        risk_type="resource_overutilization",
                        risk_level=self._probability_to_risk_level(probability),
                        probability=probability,
                        potential_impact=f"Resource {resource_key} has {len(overlaps)} potential conflicts",
                        affected_events=[e.hearing_id for e in resource_events],
                        risk_factors={'overlap_count': len(overlaps)},
                        temporal_window=(
                            min(e.date_time for e in resource_events),
                            max(e.end_time or e.date_time + timedelta(hours=1) for e in resource_events)
                        ),
                        resources_at_risk=[resource_key],
                        recommended_actions=[
                            PreventionAction.RESCHEDULE_PROACTIVELY,
                            PreventionAction.RESERVE_BACKUP_RESOURCES
                        ],
                        prevention_cost=100.0,
                        inaction_cost=500.0 * probability
                    )
                    risks.append(risk)
        
        return risks
    
    async def _predict_travel_conflicts(self, events: List[HearingEvent],
                                      horizon_days: int) -> List[ConflictRisk]:
        """Predict travel-related conflicts."""
        risks = []
        
        # Group events by attorney/party to check travel feasibility
        participant_schedules = {}
        
        for event in events:
            participants = (event.attorneys or []) + (event.parties or [])
            
            for participant in participants:
                if participant not in participant_schedules:
                    participant_schedules[participant] = []
                participant_schedules[participant].append(event)
        
        # Check each participant's travel requirements
        for participant, participant_events in participant_schedules.items():
            if len(participant_events) > 1:
                # Sort by time
                participant_events.sort(key=lambda e: e.date_time)
                
                # Check consecutive events for travel conflicts
                for i in range(len(participant_events) - 1):
                    event1, event2 = participant_events[i], participant_events[i + 1]
                    
                    # Calculate time gap
                    end1 = event1.end_time or event1.date_time + timedelta(hours=1)
                    gap_minutes = (event2.date_time - end1).total_seconds() / 60
                    
                    # Estimate required travel time (simplified)
                    required_travel = self._estimate_travel_time(event1, event2)
                    
                    if gap_minutes < required_travel:
                        probability = min(1.0, required_travel / gap_minutes) if gap_minutes > 0 else 1.0
                        
                        risk = ConflictRisk(
                            risk_id=f"travel_conflict_{event1.hearing_id}_{event2.hearing_id}",
                            risk_type="insufficient_travel_time",
                            risk_level=self._probability_to_risk_level(probability),
                            probability=probability,
                            potential_impact=f"Insufficient travel time for {participant} between events",
                            affected_events=[event1.hearing_id, event2.hearing_id],
                            risk_factors={
                                'required_travel_minutes': required_travel,
                                'available_gap_minutes': gap_minutes,
                                'participant': participant
                            },
                            temporal_window=(event1.date_time, event2.date_time),
                            recommended_actions=[
                                PreventionAction.ADJUST_BUFFER,
                                PreventionAction.SUGGEST_ALTERNATIVE,
                                PreventionAction.COORDINATE_LOGISTICS
                            ],
                            prevention_cost=25.0,
                            inaction_cost=150.0 * probability
                        )
                        risks.append(risk)
        
        return risks
    
    async def _predict_pattern_conflicts(self, events: List[HearingEvent],
                                       horizon_days: int) -> List[ConflictRisk]:
        """Predict conflicts based on historical patterns."""
        risks = []
        
        # This would analyze historical conflict patterns
        # For now, implement basic pattern detection
        
        # Pattern 1: Friday afternoon scheduling (historically problematic)
        friday_afternoon_events = [
            e for e in events 
            if e.date_time.weekday() == 4 and e.date_time.hour >= 14
        ]
        
        if len(friday_afternoon_events) > 2:
            risk = ConflictRisk(
                risk_id=f"pattern_friday_afternoon_{datetime.now().timestamp()}",
                risk_type="problematic_time_pattern",
                risk_level=RiskLevel.MEDIUM,
                probability=0.6,
                potential_impact="Friday afternoon scheduling historically leads to delays and conflicts",
                affected_events=[e.hearing_id for e in friday_afternoon_events],
                risk_factors={'pattern_type': 'friday_afternoon_overload'},
                temporal_window=(
                    min(e.date_time for e in friday_afternoon_events),
                    max(e.date_time for e in friday_afternoon_events)
                ),
                recommended_actions=[PreventionAction.SUGGEST_ALTERNATIVE],
                historical_precedent=True,
                prevention_cost=30.0,
                inaction_cost=120.0
            )
            risks.append(risk)
        
        return risks
    
    async def _detect_scheduling_anomalies(self, events: List[HearingEvent]) -> List[ConflictRisk]:
        """Detect anomalous scheduling patterns that might lead to conflicts."""
        risks = []
        
        if not events or not self.is_trained:
            return risks
        
        # Extract features for anomaly detection
        features = []
        event_mapping = {}
        
        for i, event in enumerate(events):
            feature_vector = self._extract_anomaly_features(event)
            features.append(feature_vector)
            event_mapping[i] = event
        
        # Detect anomalies
        if len(features) > 1:
            try:
                anomaly_scores = self.anomaly_detector.decision_function(features)
                anomalies = self.anomaly_detector.predict(features)
                
                for i, (score, is_anomaly) in enumerate(zip(anomaly_scores, anomalies)):
                    if is_anomaly == -1:  # Anomaly detected
                        event = event_mapping[i]
                        probability = min(1.0, abs(score) / 2.0)  # Normalize score to probability
                        
                        risk = ConflictRisk(
                            risk_id=f"anomaly_{event.hearing_id}",
                            risk_type="scheduling_anomaly",
                            risk_level=self._probability_to_risk_level(probability),
                            probability=probability,
                            potential_impact=f"Unusual scheduling pattern detected for {event.case_title}",
                            affected_events=[event.hearing_id],
                            risk_factors={'anomaly_score': float(score)},
                            temporal_window=(event.date_time, event.date_time + timedelta(hours=2)),
                            recommended_actions=[PreventionAction.NOTIFY_STAKEHOLDERS],
                            confidence=0.6,  # Lower confidence for anomaly detection
                            prevention_cost=20.0,
                            inaction_cost=80.0 * probability
                        )
                        risks.append(risk)
            
            except Exception as e:
                logger.warning(f"Anomaly detection failed: {str(e)}")
        
        return risks
    
    def _create_time_windows(self, events: List[HearingEvent], hours: int) -> Dict[datetime, List[HearingEvent]]:
        """Create time windows for event analysis."""
        windows = {}
        
        for event in events:
            # Round down to nearest hour boundary
            window_start = event.date_time.replace(minute=0, second=0, microsecond=0)
            
            if window_start not in windows:
                windows[window_start] = []
            windows[window_start].append(event)
        
        return windows
    
    def _extract_event_resources(self, event: HearingEvent) -> List[Tuple[str, str]]:
        """Extract required resources from an event."""
        resources = []
        
        if event.judge:
            resources.append(('judge', event.judge))
        
        if event.location and event.location.courtroom:
            resources.append(('courtroom', f"{event.location.court_name}_{event.location.courtroom}"))
        
        for attorney in event.attorneys or []:
            resources.append(('attorney', attorney))
        
        return resources
    
    def _find_time_overlaps(self, events: List[HearingEvent]) -> List[Tuple[HearingEvent, HearingEvent]]:
        """Find time overlaps between events."""
        overlaps = []
        
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                end1 = event1.end_time or event1.date_time + timedelta(hours=1)
                end2 = event2.end_time or event2.date_time + timedelta(hours=1)
                
                # Check for overlap
                if event1.date_time < end2 and event2.date_time < end1:
                    overlaps.append((event1, event2))
        
        return overlaps
    
    def _estimate_travel_time(self, event1: HearingEvent, event2: HearingEvent) -> int:
        """Estimate travel time between events (simplified)."""
        # This is a simplified version - would use actual travel time calculator
        if (event1.location and event2.location and 
            event1.location.court_name == event2.location.court_name):
            return 15  # Same courthouse
        else:
            return 45  # Different locations
    
    def _probability_to_risk_level(self, probability: float) -> RiskLevel:
        """Convert probability to risk level."""
        if probability >= 0.8:
            return RiskLevel.CRITICAL
        elif probability >= 0.6:
            return RiskLevel.HIGH
        elif probability >= 0.4:
            return RiskLevel.MEDIUM
        elif probability >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def _extract_anomaly_features(self, event: HearingEvent) -> List[float]:
        """Extract features for anomaly detection."""
        features = []
        
        # Time-based features
        features.append(event.date_time.hour)
        features.append(event.date_time.weekday())
        features.append(event.date_time.day)
        
        # Event type (one-hot encoded)
        hearing_types = list(HearingType)
        for ht in hearing_types:
            features.append(1.0 if event.hearing_type == ht else 0.0)
        
        # Duration
        if event.end_time:
            duration = (event.end_time - event.date_time).total_seconds() / 3600
        else:
            duration = 1.0  # Default 1 hour
        features.append(duration)
        
        # Confidence
        features.append(event.confidence)
        
        # Location (simplified)
        location_hash = 0.0
        if event.location:
            location_hash = hash(event.location.court_name or '') % 1000 / 1000.0
        features.append(location_hash)
        
        return features
    
    def _deduplicate_risks(self, risks: List[ConflictRisk]) -> List[ConflictRisk]:
        """Remove duplicate risks."""
        seen_signatures = set()
        unique_risks = []
        
        for risk in risks:
            # Create signature based on risk type and affected events
            affected_events = sorted(risk.affected_events)
            signature = f"{risk.risk_type}:{':'.join(affected_events)}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_risks.append(risk)
        
        return unique_risks
    
    def train_models(self, historical_events: List[HearingEvent], 
                    historical_conflicts: List[ScheduleConflict]):
        """Train prediction models with historical data."""
        if len(historical_events) < 50 or len(historical_conflicts) < 10:
            logger.warning("Insufficient data for training conflict prediction models")
            return
        
        # Prepare training data
        # This is a simplified version - would extract comprehensive features
        features = []
        labels = []
        
        for event in historical_events:
            feature_vector = self._extract_anomaly_features(event)
            features.append(feature_vector)
            
            # Label: 1 if event was involved in a conflict, 0 otherwise
            was_in_conflict = any(
                event.hearing_id in [conflict.primary_event.hearing_id] + 
                [e.hearing_id for e in conflict.conflicting_events]
                for conflict in historical_conflicts
            )
            labels.append(1 if was_in_conflict else 0)
        
        # Train models
        features = np.array(features)
        labels = np.array(labels)
        
        # Scale features
        features_scaled = self.feature_scaler.fit_transform(features)
        
        # Train classifiers
        for model_name, model in self.models.items():
            try:
                model.fit(features_scaled, labels)
                logger.info(f"Trained {model_name} model with {len(features)} samples")
            except Exception as e:
                logger.error(f"Failed to train {model_name} model: {str(e)}")
        
        # Train anomaly detector
        try:
            self.anomaly_detector.fit(features_scaled)
            self.is_trained = True
            logger.info("Anomaly detection model trained successfully")
        except Exception as e:
            logger.error(f"Failed to train anomaly detector: {str(e)}")


class ConflictPreventionSystem:
    """Main conflict prevention system."""
    
    def __init__(self, travel_calculator: TravelTimeCalculator, 
                 scheduler: IntelligentScheduler):
        self.travel_calculator = travel_calculator
        self.scheduler = scheduler
        self.predictor = ConflictPredictor()
        self.conflict_detector = AdvancedConflictDetector()
        
        # Prevention rules and strategies
        self.prevention_rules: List[PreventionRule] = []
        self.active_strategies: Set[PreventionStrategy] = set()
        
        # State tracking
        self.blocked_slots: Set[str] = set()
        self.dynamic_buffers: Dict[str, int] = {}  # event_id -> buffer_minutes
        self.monitored_risks: Dict[str, ConflictRisk] = {}
        
        # Statistics
        self.prevention_stats = {
            'risks_detected': 0,
            'conflicts_prevented': 0,
            'false_positives': 0,
            'total_savings': 0.0
        }
        
        self._initialize_default_rules()
        self._initialize_default_strategies()
    
    def _initialize_default_rules(self):
        """Initialize default prevention rules."""
        default_rules = [
            PreventionRule(
                rule_id="block_overloaded_slots",
                name="Block Overloaded Time Slots",
                description="Block time slots when too many events are scheduled",
                conditions={'events_in_window': {'min': 4}},
                actions=[PreventionAction.BLOCK_SLOT],
                priority=10
            ),
            PreventionRule(
                rule_id="enforce_travel_buffers",
                name="Enforce Travel Time Buffers",
                description="Ensure adequate travel time between events",
                conditions={'insufficient_travel_time': True},
                actions=[PreventionAction.ADJUST_BUFFER],
                priority=20
            ),
            PreventionRule(
                rule_id="prevent_judge_conflicts",
                name="Prevent Judge Double-Booking",
                description="Prevent scheduling conflicts for judges",
                conditions={'judge_overlap': True},
                actions=[PreventionAction.SUGGEST_ALTERNATIVE, PreventionAction.NOTIFY_STAKEHOLDERS],
                priority=5
            ),
            PreventionRule(
                rule_id="resource_balancing",
                name="Balance Resource Utilization",
                description="Balance workload across available resources",
                conditions={'resource_utilization': {'max': 0.9}},
                actions=[PreventionAction.SUGGEST_ALTERNATIVE],
                priority=30
            )
        ]
        
        self.prevention_rules.extend(default_rules)
        self.prevention_rules.sort(key=lambda r: r.priority)
    
    def _initialize_default_strategies(self):
        """Initialize default prevention strategies."""
        self.active_strategies = {
            PreventionStrategy.PREDICTIVE_BLOCKING,
            PreventionStrategy.ADAPTIVE_BUFFERING,
            PreventionStrategy.INTELLIGENT_ROUTING,
            PreventionStrategy.REAL_TIME_MONITORING
        }
    
    async def analyze_and_prevent(self, events: List[HearingEvent],
                                schedule: Optional[Schedule] = None,
                                prediction_horizon_days: int = 7) -> Dict[str, Any]:
        """Analyze potential conflicts and take preventive actions."""
        start_time = datetime.now()
        
        # Predict conflicts
        predicted_risks = await self.predictor.predict_conflicts(
            events, schedule, prediction_horizon_days
        )
        
        # Filter actionable risks
        actionable_risks = [risk for risk in predicted_risks if risk.is_actionable()]
        
        # Apply prevention strategies
        prevention_results = {}
        for strategy in self.active_strategies:
            if strategy == PreventionStrategy.PREDICTIVE_BLOCKING:
                result = await self._apply_predictive_blocking(actionable_risks)
                prevention_results['predictive_blocking'] = result
            
            elif strategy == PreventionStrategy.ADAPTIVE_BUFFERING:
                result = await self._apply_adaptive_buffering(actionable_risks, events)
                prevention_results['adaptive_buffering'] = result
            
            elif strategy == PreventionStrategy.INTELLIGENT_ROUTING:
                result = await self._apply_intelligent_routing(actionable_risks, events)
                prevention_results['intelligent_routing'] = result
            
            elif strategy == PreventionStrategy.REAL_TIME_MONITORING:
                result = await self._apply_real_time_monitoring(actionable_risks)
                prevention_results['real_time_monitoring'] = result
        
        # Apply prevention rules
        rule_results = await self._apply_prevention_rules(actionable_risks, events)
        prevention_results['rule_applications'] = rule_results
        
        # Update statistics
        self.prevention_stats['risks_detected'] += len(predicted_risks)
        
        # Store monitored risks
        for risk in actionable_risks:
            self.monitored_risks[risk.risk_id] = risk
        
        analysis_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'analysis_duration_seconds': analysis_time,
            'total_risks_predicted': len(predicted_risks),
            'actionable_risks': len(actionable_risks),
            'prevention_strategies_applied': list(self.active_strategies),
            'prevention_results': prevention_results,
            'risks_by_level': self._categorize_risks_by_level(predicted_risks),
            'recommended_actions': self._consolidate_recommended_actions(actionable_risks),
            'estimated_cost_savings': sum(r.inaction_cost - r.prevention_cost 
                                        for r in actionable_risks),
            'risks': [risk.to_dict() for risk in actionable_risks]
        }
    
    async def _apply_predictive_blocking(self, risks: List[ConflictRisk]) -> Dict[str, Any]:
        """Apply predictive slot blocking strategy."""
        blocked_count = 0
        blocked_periods = []
        
        for risk in risks:
            if PreventionAction.BLOCK_SLOT in risk.recommended_actions:
                # Block time slots that are likely to cause conflicts
                start_time, end_time = risk.temporal_window
                
                # Create blocked period
                blocked_period = {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'reason': risk.potential_impact,
                    'risk_id': risk.risk_id
                }
                
                blocked_periods.append(blocked_period)
                blocked_count += 1
                
                # Add to blocked slots (simplified)
                slot_id = f"blocked_{start_time.timestamp()}"
                self.blocked_slots.add(slot_id)
        
        return {
            'blocked_slots': blocked_count,
            'blocked_periods': blocked_periods,
            'total_blocked_slots': len(self.blocked_slots)
        }
    
    async def _apply_adaptive_buffering(self, risks: List[ConflictRisk], 
                                      events: List[HearingEvent]) -> Dict[str, Any]:
        """Apply adaptive buffering strategy."""
        buffer_adjustments = []
        
        for risk in risks:
            if (risk.risk_type == "insufficient_travel_time" and 
                PreventionAction.ADJUST_BUFFER in risk.recommended_actions):
                
                affected_events = risk.affected_events
                required_buffer = risk.risk_factors.get('required_travel_minutes', 30)
                
                for event_id in affected_events:
                    # Increase buffer time
                    current_buffer = self.dynamic_buffers.get(event_id, 15)  # Default 15 min
                    new_buffer = max(current_buffer, int(required_buffer * 1.2))  # 20% safety margin
                    
                    self.dynamic_buffers[event_id] = new_buffer
                    
                    buffer_adjustments.append({
                        'event_id': event_id,
                        'previous_buffer': current_buffer,
                        'new_buffer': new_buffer,
                        'reason': risk.potential_impact
                    })
        
        return {
            'buffer_adjustments': len(buffer_adjustments),
            'adjustments': buffer_adjustments,
            'total_dynamic_buffers': len(self.dynamic_buffers)
        }
    
    async def _apply_intelligent_routing(self, risks: List[ConflictRisk], 
                                       events: List[HearingEvent]) -> Dict[str, Any]:
        """Apply intelligent routing strategy."""
        routing_suggestions = []
        
        # Group events by participants to optimize travel sequences
        participant_schedules = {}
        for event in events:
            participants = (event.attorneys or []) + (event.parties or [])
            for participant in participants:
                if participant not in participant_schedules:
                    participant_schedules[participant] = []
                participant_schedules[participant].append(event)
        
        for participant, participant_events in participant_schedules.items():
            if len(participant_events) > 2:
                # Sort events by time
                participant_events.sort(key=lambda e: e.date_time)
                
                # Analyze travel sequence
                travel_optimization = await self._optimize_travel_sequence(participant_events)
                
                if travel_optimization['improvements']:
                    routing_suggestions.append({
                        'participant': participant,
                        'current_sequence': [e.hearing_id for e in participant_events],
                        'optimizations': travel_optimization['improvements'],
                        'estimated_savings': travel_optimization['time_savings_minutes']
                    })
        
        return {
            'routing_optimizations': len(routing_suggestions),
            'suggestions': routing_suggestions,
            'total_time_savings_minutes': sum(s['estimated_savings'] for s in routing_suggestions)
        }
    
    async def _apply_real_time_monitoring(self, risks: List[ConflictRisk]) -> Dict[str, Any]:
        """Apply real-time monitoring strategy."""
        monitoring_alerts = []
        
        for risk in risks:
            if risk.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                # Set up monitoring alert
                alert = {
                    'risk_id': risk.risk_id,
                    'alert_type': 'high_risk_monitoring',
                    'monitor_until': risk.expires_at.isoformat(),
                    'check_interval_minutes': 30 if risk.risk_level == RiskLevel.CRITICAL else 60,
                    'escalation_threshold': 0.1,  # Escalate if probability increases by 10%
                    'notification_channels': ['email', 'dashboard']
                }
                monitoring_alerts.append(alert)
        
        return {
            'monitoring_alerts_created': len(monitoring_alerts),
            'alerts': monitoring_alerts,
            'total_monitored_risks': len(self.monitored_risks)
        }
    
    async def _apply_prevention_rules(self, risks: List[ConflictRisk], 
                                    events: List[HearingEvent]) -> List[Dict[str, Any]]:
        """Apply prevention rules to risks."""
        rule_applications = []
        
        for rule in self.prevention_rules:
            if not rule.enabled:
                continue
            
            applicable_risks = []
            
            for risk in risks:
                # Create context for rule evaluation
                context = {
                    'risk_type': risk.risk_type,
                    'risk_level': risk.risk_level.value,
                    'probability': risk.probability,
                    'events_in_window': len(risk.affected_events)
                }
                
                # Add risk-specific context
                context.update(risk.risk_factors)
                
                if rule.matches_conditions(context):
                    applicable_risks.append(risk)
            
            if applicable_risks:
                # Apply rule actions
                application_result = {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'applicable_risks': len(applicable_risks),
                    'actions_taken': []
                }
                
                for action in rule.actions:
                    action_result = await self._execute_prevention_action(
                        action, applicable_risks, events
                    )
                    application_result['actions_taken'].append({
                        'action': action.value,
                        'result': action_result
                    })
                
                # Update rule statistics
                rule.application_count += 1
                rule.last_applied = datetime.now()
                
                rule_applications.append(application_result)
        
        return rule_applications
    
    async def _execute_prevention_action(self, action: PreventionAction,
                                       risks: List[ConflictRisk],
                                       events: List[HearingEvent]) -> Dict[str, Any]:
        """Execute a specific prevention action."""
        if action == PreventionAction.BLOCK_SLOT:
            blocked_slots = []
            for risk in risks:
                start_time, end_time = risk.temporal_window
                slot_key = f"blocked_{start_time.timestamp()}"
                self.blocked_slots.add(slot_key)
                blocked_slots.append(slot_key)
            
            return {'blocked_slots': blocked_slots}
        
        elif action == PreventionAction.NOTIFY_STAKEHOLDERS:
            notifications = []
            for risk in risks:
                notification = {
                    'risk_id': risk.risk_id,
                    'message': f"Potential conflict detected: {risk.potential_impact}",
                    'priority': risk.risk_level.value,
                    'affected_events': risk.affected_events
                }
                notifications.append(notification)
            
            return {'notifications_sent': len(notifications), 'notifications': notifications}
        
        elif action == PreventionAction.SUGGEST_ALTERNATIVE:
            suggestions = []
            for risk in risks:
                # Generate alternative scheduling suggestions
                alternative_slots = await self._generate_alternative_suggestions(risk, events)
                if alternative_slots:
                    suggestions.append({
                        'risk_id': risk.risk_id,
                        'alternatives': alternative_slots
                    })
            
            return {'suggestions_generated': len(suggestions), 'suggestions': suggestions}
        
        else:
            return {'action': action.value, 'status': 'not_implemented'}
    
    async def _optimize_travel_sequence(self, events: List[HearingEvent]) -> Dict[str, Any]:
        """Optimize travel sequence for a participant's events."""
        if len(events) < 2:
            return {'improvements': [], 'time_savings_minutes': 0}
        
        # This is a simplified version - would use actual travel optimization
        improvements = []
        time_savings = 0
        
        # Check for potential reordering opportunities
        for i in range(len(events) - 1):
            event1, event2 = events[i], events[i + 1]
            
            # If events can be swapped to reduce travel time
            if (event1.location and event2.location and 
                event1.location.court_name != event2.location.court_name):
                
                improvements.append({
                    'suggestion': f"Consider swapping {event1.hearing_id} and {event2.hearing_id}",
                    'reason': 'Reduce travel time',
                    'estimated_savings_minutes': 20
                })
                time_savings += 20
        
        return {
            'improvements': improvements,
            'time_savings_minutes': time_savings
        }
    
    async def _generate_alternative_suggestions(self, risk: ConflictRisk, 
                                              events: List[HearingEvent]) -> List[Dict[str, Any]]:
        """Generate alternative scheduling suggestions for a risk."""
        suggestions = []
        
        # Find affected events
        affected_events = [e for e in events if e.hearing_id in risk.affected_events]
        
        if not affected_events:
            return suggestions
        
        # Generate time-based alternatives
        for event in affected_events:
            # Suggest earlier or later times
            earlier_time = event.date_time - timedelta(hours=1)
            later_time = event.date_time + timedelta(hours=1)
            
            suggestions.extend([
                {
                    'event_id': event.hearing_id,
                    'current_time': event.date_time.isoformat(),
                    'suggested_time': earlier_time.isoformat(),
                    'reason': 'Avoid conflict window',
                    'confidence': 0.8
                },
                {
                    'event_id': event.hearing_id,
                    'current_time': event.date_time.isoformat(),
                    'suggested_time': later_time.isoformat(),
                    'reason': 'Avoid conflict window',
                    'confidence': 0.7
                }
            ])
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _categorize_risks_by_level(self, risks: List[ConflictRisk]) -> Dict[str, int]:
        """Categorize risks by level."""
        categorization = {}
        for level in RiskLevel:
            categorization[level.value] = sum(1 for r in risks if r.risk_level == level)
        return categorization
    
    def _consolidate_recommended_actions(self, risks: List[ConflictRisk]) -> Dict[str, int]:
        """Consolidate recommended actions across all risks."""
        action_counts = {}
        
        for risk in risks:
            for action in risk.recommended_actions:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1
        
        return action_counts
    
    def get_prevention_statistics(self) -> Dict[str, Any]:
        """Get comprehensive prevention statistics."""
        return {
            'prevention_stats': self.prevention_stats.copy(),
            'active_strategies': [s.value for s in self.active_strategies],
            'prevention_rules': len(self.prevention_rules),
            'blocked_slots': len(self.blocked_slots),
            'dynamic_buffers': len(self.dynamic_buffers),
            'monitored_risks': len(self.monitored_risks),
            'rule_applications': {
                rule.rule_id: {
                    'name': rule.name,
                    'application_count': rule.application_count,
                    'last_applied': rule.last_applied.isoformat() if rule.last_applied else None,
                    'success_rate': rule.success_rate
                }
                for rule in self.prevention_rules
            }
        }
    
    async def update_risk_outcomes(self, risk_id: str, outcome: str, actual_cost: float = 0.0):
        """Update the outcome of a predicted risk for learning."""
        if risk_id in self.monitored_risks:
            risk = self.monitored_risks[risk_id]
            
            if outcome == 'prevented':
                self.prevention_stats['conflicts_prevented'] += 1
                self.prevention_stats['total_savings'] += risk.inaction_cost - actual_cost
            elif outcome == 'false_positive':
                self.prevention_stats['false_positives'] += 1
            
            # Remove from monitored risks
            del self.monitored_risks[risk_id]
            
            logger.info(f"Updated outcome for risk {risk_id}: {outcome}")


# Example usage
async def example_conflict_prevention():
    """Example usage of the conflict prevention system."""
    
    from .travel_time_calculator import TravelTimeCalculator
    from .intelligent_scheduler import IntelligentScheduler
    
    # Initialize components
    travel_calculator = TravelTimeCalculator()
    scheduler = IntelligentScheduler(travel_calculator)
    prevention_system = ConflictPreventionSystem(travel_calculator, scheduler)
    
    # Create sample events with potential conflicts
    events = [
        HearingEvent(
            hearing_id="trial_1",
            case_number="CASE001",
            case_title="Smith v. Jones",
            hearing_type=HearingType.TRIAL,
            date_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            judge="Judge Johnson",
            attorneys=["Attorney Smith", "Attorney Brown"],
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="motion_1",
            case_number="CASE002",
            case_title="Brown v. Davis",
            hearing_type=HearingType.MOTION_HEARING,
            date_time=datetime(2024, 1, 15, 10, 30),  # Overlaps with trial
            end_time=datetime(2024, 1, 15, 11, 30),
            judge="Judge Johnson",  # Same judge as trial
            attorneys=["Attorney Wilson"],
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="hearing_1",
            case_number="CASE003",
            case_title="Wilson v. Anderson",
            hearing_type=HearingType.HEARING,
            date_time=datetime(2024, 1, 15, 11, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
            judge="Judge Miller",
            attorneys=["Attorney Smith"],  # Same attorney as trial - travel conflict
            location=Location(name="Uptown Courthouse"),  # Different location
            status=HearingStatus.SCHEDULED
        ),
        # Friday afternoon overload
        HearingEvent(
            hearing_id="status_1",
            case_number="CASE004",
            case_title="Case 4",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 19, 14, 0),  # Friday afternoon
            judge="Judge Davis",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="status_2",
            case_number="CASE005",
            case_title="Case 5",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 19, 15, 0),  # Friday afternoon
            judge="Judge Davis",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="status_3",
            case_number="CASE006",
            case_title="Case 6",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 19, 16, 0),  # Friday afternoon
            judge="Judge Davis",
            status=HearingStatus.SCHEDULED
        )
    ]
    
    print("Conflict Prevention System Demo")
    print("=" * 50)
    
    # Analyze and prevent conflicts
    print("Analyzing potential conflicts and applying prevention strategies...")
    results = await prevention_system.analyze_and_prevent(events, prediction_horizon_days=14)
    
    print(f"\nAnalysis Results:")
    print(f"Analysis duration: {results['analysis_duration_seconds']:.2f} seconds")
    print(f"Total risks predicted: {results['total_risks_predicted']}")
    print(f"Actionable risks: {results['actionable_risks']}")
    print(f"Estimated cost savings: ${results['estimated_cost_savings']:.2f}")
    
    print(f"\nRisks by Level:")
    for level, count in results['risks_by_level'].items():
        if count > 0:
            print(f"  {level.upper()}: {count} risks")
    
    print(f"\nRecommended Actions:")
    for action, count in results['recommended_actions'].items():
        print(f"  {action}: {count} times")
    
    print(f"\nPrevention Strategy Results:")
    for strategy, result in results['prevention_results'].items():
        print(f"  {strategy}:")
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    print(f"    {key}: {value}")
                elif isinstance(value, list) and len(value) <= 3:
                    print(f"    {key}: {len(value)} items")
    
    print(f"\nDetected Risks:")
    print("-" * 30)
    for risk in results['risks']:
        print(f"Risk: {risk['risk_type']} ({risk['risk_level']})")
        print(f"  Probability: {risk['probability']:.1%}")
        print(f"  Impact: {risk['potential_impact']}")
        print(f"  Affected Events: {len(risk['affected_events'])}")
        print(f"  Priority Score: {risk['priority_score']:.2f}")
        print(f"  Actions: {', '.join(risk['recommended_actions'])}")
        print()
    
    # Get system statistics
    print("Prevention System Statistics:")
    print("-" * 30)
    stats = prevention_system.get_prevention_statistics()
    print(json.dumps(stats, indent=2, default=str))
    
    # Simulate updating risk outcomes
    print("\nSimulating risk outcome updates...")
    for risk in results['risks'][:2]:  # Update first 2 risks
        outcome = "prevented" if risk['probability'] > 0.5 else "false_positive"
        await prevention_system.update_risk_outcomes(risk['risk_id'], outcome)
        print(f"Updated risk {risk['risk_id']}: {outcome}")
    
    # Final statistics
    final_stats = prevention_system.get_prevention_statistics()
    print(f"\nFinal Statistics:")
    print(f"Conflicts prevented: {final_stats['prevention_stats']['conflicts_prevented']}")
    print(f"False positives: {final_stats['prevention_stats']['false_positives']}")
    print(f"Total savings: ${final_stats['prevention_stats']['total_savings']:.2f}")


if __name__ == "__main__":
    asyncio.run(example_conflict_prevention())