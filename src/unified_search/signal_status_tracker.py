"""
Signal and status tracking system for legal authorities.
Monitors case law status, tracks changes over time, and provides alerts for status changes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from collections import defaultdict

from ..types.unified_types import UnifiedDocument, ContentType
from .shepardizing_engine import TreatmentSignal, CaseStatus, ShepardAnalysis
from .citation_validator import CitationValidator


class SignalCategory(Enum):
    """Categories of legal status signals."""
    POSITIVE = "positive"      # Good law, followed, affirmed
    NEGATIVE = "negative"      # Overruled, reversed, questioned
    CAUTION = "caution"        # Criticized, limited, distinguished
    NEUTRAL = "neutral"        # Cited, mentioned, explained
    UNKNOWN = "unknown"        # Status cannot be determined


class StatusChangeType(Enum):
    """Types of status changes."""
    NEWLY_OVERRULED = "newly_overruled"
    NEWLY_QUESTIONED = "newly_questioned"
    NEWLY_CRITICIZED = "newly_criticized"
    NEWLY_FOLLOWED = "newly_followed"
    INCREASED_CRITICISM = "increased_criticism"
    DECREASED_RELIABILITY = "decreased_reliability"
    IMPROVED_STATUS = "improved_status"
    JURISDICTION_SPLIT = "jurisdiction_split"


class AlertSeverity(Enum):
    """Severity levels for status alerts."""
    CRITICAL = "critical"      # Immediate attention required
    HIGH = "high"             # Important change
    MEDIUM = "medium"         # Notable change
    LOW = "low"              # Minor change
    INFO = "info"            # Informational


@dataclass
class StatusSnapshot:
    """Snapshot of document status at a point in time."""
    document_id: str
    snapshot_date: datetime
    overall_status: CaseStatus
    signal_category: SignalCategory
    status_confidence: float
    
    # Signal counts
    positive_signals: int = 0
    negative_signals: int = 0
    caution_signals: int = 0
    neutral_signals: int = 0
    
    # Treatment details
    total_citations: int = 0
    citing_jurisdictions: Set[str] = field(default_factory=set)
    recent_treatments: List[TreatmentSignal] = field(default_factory=list)
    
    # Quality metrics
    reliability_score: float = 0.0
    precedential_value: float = 0.0
    
    # Metadata
    analysis_source: str = "automated"
    notes: Optional[str] = None


@dataclass
class StatusChange:
    """Represents a change in document status."""
    document_id: str
    change_date: datetime
    change_type: StatusChangeType
    severity: AlertSeverity
    
    # Change details
    previous_status: Optional[CaseStatus] = None
    new_status: Optional[CaseStatus] = None
    previous_confidence: float = 0.0
    new_confidence: float = 0.0
    
    # Triggering event
    triggering_case: Optional[str] = None
    triggering_signal: Optional[TreatmentSignal] = None
    
    # Description and context
    change_description: str = ""
    impact_assessment: str = ""
    recommended_action: str = ""
    
    # Supporting data
    supporting_evidence: List[str] = field(default_factory=list)
    affected_jurisdictions: Set[str] = field(default_factory=set)


@dataclass
class StatusAlert:
    """Alert about status changes."""
    alert_id: str
    document_id: str
    alert_date: datetime
    severity: AlertSeverity
    
    # Alert content
    title: str
    message: str
    detailed_analysis: Optional[str] = None
    
    # Status information
    current_status: CaseStatus
    status_changes: List[StatusChange] = field(default_factory=list)
    
    # Action items
    recommended_actions: List[str] = field(default_factory=list)
    follow_up_required: bool = False
    
    # Metadata
    alert_type: str = "status_change"
    acknowledged: bool = False
    acknowledged_date: Optional[datetime] = None


@dataclass
class TrendAnalysis:
    """Analysis of status trends over time."""
    document_id: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    
    # Trend direction
    overall_trend: str  # "improving", "declining", "stable", "volatile"
    trend_confidence: float
    
    # Trend metrics
    status_stability: float  # 0-1, higher is more stable
    signal_consistency: float  # 0-1, higher is more consistent
    jurisdictional_agreement: float  # 0-1, higher agreement across jurisdictions
    
    # Trend details
    status_trajectory: List[Tuple[datetime, CaseStatus]]
    signal_evolution: List[Tuple[datetime, Dict[TreatmentSignal, int]]]
    
    # Predictions
    predicted_status: Optional[CaseStatus] = None
    prediction_confidence: float = 0.0
    risk_factors: List[str] = field(default_factory=list)


class SignalStatusTracker:
    """
    Comprehensive signal and status tracking system for legal authorities.
    
    Monitors case law status changes, tracks treatment evolution,
    generates alerts for significant changes, and provides trend analysis.
    """
    
    def __init__(self, citation_validator: Optional[CitationValidator] = None):
        self.citation_validator = citation_validator or CitationValidator()
        self.logger = logging.getLogger(__name__)
        
        # Storage for status history
        self.status_history: Dict[str, List[StatusSnapshot]] = {}
        self.pending_alerts: Dict[str, List[StatusAlert]] = {}
        
        # Configuration
        self.monitoring_enabled = True
        self.alert_thresholds = {
            AlertSeverity.CRITICAL: 0.9,
            AlertSeverity.HIGH: 0.7,
            AlertSeverity.MEDIUM: 0.5,
            AlertSeverity.LOW: 0.3
        }
        
        # Signal categorization
        self.signal_categories = {
            SignalCategory.POSITIVE: [
                TreatmentSignal.FOLLOWED,
                TreatmentSignal.AFFIRMED,
                TreatmentSignal.CITED
            ],
            SignalCategory.NEGATIVE: [
                TreatmentSignal.OVERRULED,
                TreatmentSignal.REVERSED,
                TreatmentSignal.SUPERSEDED,
                TreatmentSignal.VACATED
            ],
            SignalCategory.CAUTION: [
                TreatmentSignal.QUESTIONED,
                TreatmentSignal.CRITICIZED,
                TreatmentSignal.LIMITED,
                TreatmentSignal.DISTINGUISHED
            ],
            SignalCategory.NEUTRAL: [
                TreatmentSignal.EXPLAINED,
                TreatmentSignal.MENTIONED,
                TreatmentSignal.NEUTRAL
            ]
        }
    
    async def track_document_status(self, 
                                  document: UnifiedDocument,
                                  shepard_analysis: ShepardAnalysis) -> StatusSnapshot:
        """
        Track and record the current status of a document.
        
        Args:
            document: Document to track
            shepard_analysis: Current Shepard's analysis
            
        Returns:
            Status snapshot
        """
        
        # Create status snapshot
        snapshot = await self._create_status_snapshot(document, shepard_analysis)
        
        # Store in history
        if document.id not in self.status_history:
            self.status_history[document.id] = []
        
        self.status_history[document.id].append(snapshot)
        
        # Check for status changes if we have previous snapshots
        if len(self.status_history[document.id]) > 1:
            await self._check_for_status_changes(document.id)
        
        self.logger.info(f"Tracked status for document {document.id}: {snapshot.overall_status.value}")
        
        return snapshot
    
    async def _create_status_snapshot(self, 
                                    document: UnifiedDocument,
                                    shepard_analysis: ShepardAnalysis) -> StatusSnapshot:
        """Create a status snapshot from Shepard's analysis."""
        
        # Categorize signals
        signal_counts = {
            SignalCategory.POSITIVE: 0,
            SignalCategory.NEGATIVE: 0,
            SignalCategory.CAUTION: 0,
            SignalCategory.NEUTRAL: 0
        }
        
        recent_treatments = []
        citing_jurisdictions = set()
        
        for citing_case in shepard_analysis.citing_cases:
            # Categorize signal
            signal = citing_case.treatment_signal
            category = self._categorize_signal(signal)
            signal_counts[category] += 1
            
            # Track recent treatments (last 2 years)
            if citing_case.decision_date and citing_case.decision_date > datetime.now() - timedelta(days=730):
                recent_treatments.append(signal)
            
            # Track jurisdictions
            if citing_case.jurisdiction:
                citing_jurisdictions.add(citing_case.jurisdiction)
        
        # Determine overall signal category
        overall_category = self._determine_overall_category(signal_counts)
        
        return StatusSnapshot(
            document_id=document.id,
            snapshot_date=datetime.now(),
            overall_status=shepard_analysis.overall_status,
            signal_category=overall_category,
            status_confidence=shepard_analysis.status_confidence,
            positive_signals=signal_counts[SignalCategory.POSITIVE],
            negative_signals=signal_counts[SignalCategory.NEGATIVE],
            caution_signals=signal_counts[SignalCategory.CAUTION],
            neutral_signals=signal_counts[SignalCategory.NEUTRAL],
            total_citations=shepard_analysis.total_citations,
            citing_jurisdictions=citing_jurisdictions,
            recent_treatments=recent_treatments,
            reliability_score=shepard_analysis.reliability_score,
            precedential_value=shepard_analysis.precedential_value,
            analysis_source="shepard_analysis"
        )
    
    def _categorize_signal(self, signal: TreatmentSignal) -> SignalCategory:
        """Categorize a treatment signal."""
        for category, signals in self.signal_categories.items():
            if signal in signals:
                return category
        return SignalCategory.UNKNOWN
    
    def _determine_overall_category(self, signal_counts: Dict[SignalCategory, int]) -> SignalCategory:
        """Determine overall signal category from counts."""
        total_signals = sum(signal_counts.values())
        
        if total_signals == 0:
            return SignalCategory.UNKNOWN
        
        # If any negative signals, prioritize those
        if signal_counts[SignalCategory.NEGATIVE] > 0:
            return SignalCategory.NEGATIVE
        
        # If significant caution signals
        caution_ratio = signal_counts[SignalCategory.CAUTION] / total_signals
        if caution_ratio > 0.3:
            return SignalCategory.CAUTION
        
        # If majority positive
        positive_ratio = signal_counts[SignalCategory.POSITIVE] / total_signals
        if positive_ratio > 0.5:
            return SignalCategory.POSITIVE
        
        return SignalCategory.NEUTRAL
    
    async def _check_for_status_changes(self, document_id: str):
        """Check for significant status changes and generate alerts."""
        
        if len(self.status_history[document_id]) < 2:
            return
        
        current_snapshot = self.status_history[document_id][-1]
        previous_snapshot = self.status_history[document_id][-2]
        
        status_changes = []
        
        # Check for status changes
        if current_snapshot.overall_status != previous_snapshot.overall_status:
            change = await self._analyze_status_change(
                document_id, previous_snapshot, current_snapshot
            )
            if change:
                status_changes.append(change)
        
        # Check for signal category changes
        if current_snapshot.signal_category != previous_snapshot.signal_category:
            change = await self._analyze_signal_category_change(
                document_id, previous_snapshot, current_snapshot
            )
            if change:
                status_changes.append(change)
        
        # Check for significant confidence changes
        confidence_change = abs(current_snapshot.status_confidence - previous_snapshot.status_confidence)
        if confidence_change > 0.2:
            change = await self._analyze_confidence_change(
                document_id, previous_snapshot, current_snapshot
            )
            if change:
                status_changes.append(change)
        
        # Check for increased negative treatment
        negative_increase = (current_snapshot.negative_signals - previous_snapshot.negative_signals)
        if negative_increase > 0:
            change = await self._analyze_negative_treatment_increase(
                document_id, previous_snapshot, current_snapshot
            )
            if change:
                status_changes.append(change)
        
        # Generate alerts for significant changes
        if status_changes:
            await self._generate_status_alerts(document_id, status_changes)
    
    async def _analyze_status_change(self, 
                                   document_id: str,
                                   previous: StatusSnapshot,
                                   current: StatusSnapshot) -> Optional[StatusChange]:
        """Analyze a status change."""
        
        # Determine change type and severity
        change_type = StatusChangeType.IMPROVED_STATUS
        severity = AlertSeverity.INFO
        
        if previous.overall_status == CaseStatus.GOOD_LAW:
            if current.overall_status == CaseStatus.BAD_LAW:
                change_type = StatusChangeType.NEWLY_OVERRULED
                severity = AlertSeverity.CRITICAL
            elif current.overall_status == CaseStatus.QUESTIONABLE:
                change_type = StatusChangeType.NEWLY_QUESTIONED
                severity = AlertSeverity.HIGH
        elif previous.overall_status == CaseStatus.QUESTIONABLE:
            if current.overall_status == CaseStatus.BAD_LAW:
                change_type = StatusChangeType.NEWLY_OVERRULED
                severity = AlertSeverity.CRITICAL
            elif current.overall_status == CaseStatus.GOOD_LAW:
                change_type = StatusChangeType.IMPROVED_STATUS
                severity = AlertSeverity.MEDIUM
        elif previous.overall_status == CaseStatus.BAD_LAW:
            if current.overall_status in [CaseStatus.GOOD_LAW, CaseStatus.QUESTIONABLE]:
                change_type = StatusChangeType.IMPROVED_STATUS
                severity = AlertSeverity.MEDIUM
        
        # Generate description
        description = f"Status changed from {previous.overall_status.value} to {current.overall_status.value}"
        
        # Impact assessment
        impact_assessment = self._assess_status_change_impact(previous, current)
        
        # Recommended action
        recommended_action = self._recommend_status_change_action(change_type, current)
        
        return StatusChange(
            document_id=document_id,
            change_date=current.snapshot_date,
            change_type=change_type,
            severity=severity,
            previous_status=previous.overall_status,
            new_status=current.overall_status,
            previous_confidence=previous.status_confidence,
            new_confidence=current.status_confidence,
            change_description=description,
            impact_assessment=impact_assessment,
            recommended_action=recommended_action
        )
    
    async def _analyze_signal_category_change(self,
                                            document_id: str,
                                            previous: StatusSnapshot,
                                            current: StatusSnapshot) -> Optional[StatusChange]:
        """Analyze a signal category change."""
        
        change_type = StatusChangeType.IMPROVED_STATUS
        severity = AlertSeverity.MEDIUM
        
        if previous.signal_category in [SignalCategory.POSITIVE, SignalCategory.NEUTRAL]:
            if current.signal_category == SignalCategory.NEGATIVE:
                change_type = StatusChangeType.NEWLY_OVERRULED
                severity = AlertSeverity.HIGH
            elif current.signal_category == SignalCategory.CAUTION:
                change_type = StatusChangeType.NEWLY_CRITICIZED
                severity = AlertSeverity.MEDIUM
        
        description = f"Signal category changed from {previous.signal_category.value} to {current.signal_category.value}"
        
        return StatusChange(
            document_id=document_id,
            change_date=current.snapshot_date,
            change_type=change_type,
            severity=severity,
            change_description=description,
            impact_assessment="Treatment perception has shifted",
            recommended_action="Review recent citing cases for context"
        )
    
    async def _analyze_confidence_change(self,
                                       document_id: str,
                                       previous: StatusSnapshot,
                                       current: StatusSnapshot) -> Optional[StatusChange]:
        """Analyze a confidence level change."""
        
        confidence_drop = previous.status_confidence - current.status_confidence
        
        if confidence_drop > 0.2:
            change_type = StatusChangeType.DECREASED_RELIABILITY
            severity = AlertSeverity.MEDIUM if confidence_drop > 0.4 else AlertSeverity.LOW
            
            description = f"Status confidence decreased by {confidence_drop:.2f}"
            impact_assessment = "Reliability of status assessment has decreased"
            recommended_action = "Investigate recent treatments causing uncertainty"
            
            return StatusChange(
                document_id=document_id,
                change_date=current.snapshot_date,
                change_type=change_type,
                severity=severity,
                previous_confidence=previous.status_confidence,
                new_confidence=current.status_confidence,
                change_description=description,
                impact_assessment=impact_assessment,
                recommended_action=recommended_action
            )
        
        return None
    
    async def _analyze_negative_treatment_increase(self,
                                                 document_id: str,
                                                 previous: StatusSnapshot,
                                                 current: StatusSnapshot) -> Optional[StatusChange]:
        """Analyze an increase in negative treatment."""
        
        increase = current.negative_signals - previous.negative_signals
        
        if increase > 0:
            change_type = StatusChangeType.INCREASED_CRITICISM
            
            if increase >= 3:
                severity = AlertSeverity.HIGH
            elif increase >= 2:
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW
            
            description = f"Negative treatment increased by {increase} case(s)"
            impact_assessment = f"Authority may be weakening with {current.negative_signals} total negative treatments"
            recommended_action = "Review new negative treatments and consider impact on reliance"
            
            return StatusChange(
                document_id=document_id,
                change_date=current.snapshot_date,
                change_type=change_type,
                severity=severity,
                change_description=description,
                impact_assessment=impact_assessment,
                recommended_action=recommended_action
            )
        
        return None
    
    def _assess_status_change_impact(self, previous: StatusSnapshot, current: StatusSnapshot) -> str:
        """Assess the impact of a status change."""
        
        if current.overall_status == CaseStatus.BAD_LAW:
            return "CRITICAL: Case should no longer be relied upon as authority"
        elif current.overall_status == CaseStatus.QUESTIONABLE:
            if previous.overall_status == CaseStatus.GOOD_LAW:
                return "CAUTION: Case authority is now questionable - use additional support"
            else:
                return "CAUTION: Case remains questionable authority"
        elif current.overall_status == CaseStatus.GOOD_LAW:
            if previous.overall_status in [CaseStatus.BAD_LAW, CaseStatus.QUESTIONABLE]:
                return "POSITIVE: Case authority has been restored or strengthened"
            else:
                return "STABLE: Case remains good authority"
        
        return "Status change requires evaluation"
    
    def _recommend_status_change_action(self, change_type: StatusChangeType, current: StatusSnapshot) -> str:
        """Recommend action based on status change type."""
        
        recommendations = {
            StatusChangeType.NEWLY_OVERRULED: "URGENT: Remove from briefs and find alternative authority",
            StatusChangeType.NEWLY_QUESTIONED: "Review questioning cases and consider additional support",
            StatusChangeType.NEWLY_CRITICIZED: "Assess criticism validity and potential impact",
            StatusChangeType.INCREASED_CRITICISM: "Monitor trend and prepare alternative authorities",
            StatusChangeType.DECREASED_RELIABILITY: "Investigate cause of uncertainty",
            StatusChangeType.IMPROVED_STATUS: "Safe to continue relying on this authority",
            StatusChangeType.JURISDICTION_SPLIT: "Check treatment in your specific jurisdiction"
        }
        
        return recommendations.get(change_type, "Monitor developments and assess impact")
    
    async def _generate_status_alerts(self, document_id: str, status_changes: List[StatusChange]):
        """Generate alerts for status changes."""
        
        # Group changes by severity
        critical_changes = [c for c in status_changes if c.severity == AlertSeverity.CRITICAL]
        high_changes = [c for c in status_changes if c.severity == AlertSeverity.HIGH]
        other_changes = [c for c in status_changes if c.severity not in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]]
        
        # Create alerts
        if critical_changes:
            await self._create_alert(document_id, critical_changes, AlertSeverity.CRITICAL)
        
        if high_changes:
            await self._create_alert(document_id, high_changes, AlertSeverity.HIGH)
        
        if other_changes:
            # Group lower severity changes into a single alert
            max_severity = max(c.severity for c in other_changes)
            await self._create_alert(document_id, other_changes, max_severity)
    
    async def _create_alert(self, 
                          document_id: str, 
                          changes: List[StatusChange], 
                          severity: AlertSeverity):
        """Create a status alert."""
        
        current_snapshot = self.status_history[document_id][-1]
        
        # Generate alert title and message
        if severity == AlertSeverity.CRITICAL:
            title = "🚨 CRITICAL: Legal Authority Status Changed"
            message = f"Document {document_id} has critical status changes requiring immediate attention"
        elif severity == AlertSeverity.HIGH:
            title = "⚠️ HIGH: Important Status Change"
            message = f"Document {document_id} has significant status changes"
        else:
            title = "📊 Status Update"
            message = f"Document {document_id} has status changes"
        
        # Detailed analysis
        detailed_analysis = self._generate_detailed_analysis(changes, current_snapshot)
        
        # Recommended actions
        recommended_actions = list(set(change.recommended_action for change in changes if change.recommended_action))
        
        # Create alert
        alert = StatusAlert(
            alert_id=f"alert_{document_id}_{int(datetime.now().timestamp())}",
            document_id=document_id,
            alert_date=datetime.now(),
            severity=severity,
            title=title,
            message=message,
            detailed_analysis=detailed_analysis,
            current_status=current_snapshot.overall_status,
            status_changes=changes,
            recommended_actions=recommended_actions,
            follow_up_required=severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]
        )
        
        # Store alert
        if document_id not in self.pending_alerts:
            self.pending_alerts[document_id] = []
        
        self.pending_alerts[document_id].append(alert)
        
        self.logger.warning(f"Generated {severity.value} alert for document {document_id}: {title}")
    
    def _generate_detailed_analysis(self, changes: List[StatusChange], current_snapshot: StatusSnapshot) -> str:
        """Generate detailed analysis for an alert."""
        
        analysis_parts = []
        
        # Current status summary
        analysis_parts.append(f"Current Status: {current_snapshot.overall_status.value}")
        analysis_parts.append(f"Signal Category: {current_snapshot.signal_category.value}")
        analysis_parts.append(f"Confidence Level: {current_snapshot.status_confidence:.2f}")
        analysis_parts.append("")
        
        # Signal breakdown
        analysis_parts.append("Signal Summary:")
        analysis_parts.append(f"  • Positive: {current_snapshot.positive_signals}")
        analysis_parts.append(f"  • Negative: {current_snapshot.negative_signals}")
        analysis_parts.append(f"  • Caution: {current_snapshot.caution_signals}")
        analysis_parts.append(f"  • Neutral: {current_snapshot.neutral_signals}")
        analysis_parts.append("")
        
        # Recent changes
        analysis_parts.append("Recent Changes:")
        for change in changes:
            analysis_parts.append(f"  • {change.change_description}")
            analysis_parts.append(f"    Impact: {change.impact_assessment}")
        analysis_parts.append("")
        
        # Jurisdictional information
        if current_snapshot.citing_jurisdictions:
            jurisdictions = ", ".join(sorted(current_snapshot.citing_jurisdictions))
            analysis_parts.append(f"Citing Jurisdictions: {jurisdictions}")
        
        return "\n".join(analysis_parts)
    
    async def analyze_status_trends(self, 
                                  document_id: str, 
                                  period_days: int = 365) -> Optional[TrendAnalysis]:
        """Analyze status trends for a document over time."""
        
        if document_id not in self.status_history:
            return None
        
        snapshots = self.status_history[document_id]
        if len(snapshots) < 2:
            return None
        
        # Filter snapshots to analysis period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        period_snapshots = [
            s for s in snapshots 
            if start_date <= s.snapshot_date <= end_date
        ]
        
        if len(period_snapshots) < 2:
            return None
        
        # Analyze trends
        trend_analysis = await self._perform_trend_analysis(
            document_id, period_snapshots, start_date, end_date
        )
        
        return trend_analysis
    
    async def _perform_trend_analysis(self,
                                    document_id: str,
                                    snapshots: List[StatusSnapshot],
                                    start_date: datetime,
                                    end_date: datetime) -> TrendAnalysis:
        """Perform detailed trend analysis."""
        
        # Extract status trajectory
        status_trajectory = [(s.snapshot_date, s.overall_status) for s in snapshots]
        
        # Extract signal evolution
        signal_evolution = []
        for snapshot in snapshots:
            signal_dict = {
                TreatmentSignal.FOLLOWED: snapshot.positive_signals,
                TreatmentSignal.QUESTIONED: snapshot.caution_signals,
                TreatmentSignal.OVERRULED: snapshot.negative_signals
            }  # Simplified
            signal_evolution.append((snapshot.snapshot_date, signal_dict))
        
        # Determine overall trend
        overall_trend, trend_confidence = self._determine_overall_trend(snapshots)
        
        # Calculate stability metrics
        status_stability = self._calculate_status_stability(snapshots)
        signal_consistency = self._calculate_signal_consistency(snapshots)
        jurisdictional_agreement = self._calculate_jurisdictional_agreement(snapshots)
        
        # Risk assessment
        risk_factors = self._identify_risk_factors(snapshots)
        
        # Prediction (simplified)
        predicted_status, prediction_confidence = self._predict_future_status(snapshots)
        
        return TrendAnalysis(
            document_id=document_id,
            analysis_period_start=start_date,
            analysis_period_end=end_date,
            overall_trend=overall_trend,
            trend_confidence=trend_confidence,
            status_stability=status_stability,
            signal_consistency=signal_consistency,
            jurisdictional_agreement=jurisdictional_agreement,
            status_trajectory=status_trajectory,
            signal_evolution=signal_evolution,
            predicted_status=predicted_status,
            prediction_confidence=prediction_confidence,
            risk_factors=risk_factors
        )
    
    def _determine_overall_trend(self, snapshots: List[StatusSnapshot]) -> Tuple[str, float]:
        """Determine overall trend direction."""
        
        if len(snapshots) < 3:
            return "stable", 0.5
        
        # Simple trend analysis based on status changes
        status_values = {
            CaseStatus.BAD_LAW: 0,
            CaseStatus.QUESTIONABLE: 1,
            CaseStatus.UNKNOWN: 2,
            CaseStatus.GOOD_LAW: 3
        }
        
        # Get status values over time
        values = [status_values.get(s.overall_status, 2) for s in snapshots]
        
        # Calculate simple linear trend
        x = list(range(len(values)))
        if len(x) > 1:
            slope = (values[-1] - values[0]) / (len(values) - 1)
            
            if slope > 0.5:
                return "improving", 0.8
            elif slope < -0.5:
                return "declining", 0.8
            elif abs(slope) < 0.1:
                return "stable", 0.9
            else:
                return "volatile", 0.6
        
        return "stable", 0.5
    
    def _calculate_status_stability(self, snapshots: List[StatusSnapshot]) -> float:
        """Calculate status stability (fewer changes = more stable)."""
        
        if len(snapshots) < 2:
            return 1.0
        
        # Count status changes
        status_changes = 0
        for i in range(1, len(snapshots)):
            if snapshots[i].overall_status != snapshots[i-1].overall_status:
                status_changes += 1
        
        # Stability = 1 - (changes / possible_changes)
        possible_changes = len(snapshots) - 1
        stability = 1.0 - (status_changes / possible_changes) if possible_changes > 0 else 1.0
        
        return stability
    
    def _calculate_signal_consistency(self, snapshots: List[StatusSnapshot]) -> float:
        """Calculate signal consistency across snapshots."""
        
        if len(snapshots) < 2:
            return 1.0
        
        # Calculate coefficient of variation for each signal type
        positive_values = [s.positive_signals for s in snapshots]
        negative_values = [s.negative_signals for s in snapshots]
        
        def coefficient_of_variation(values):
            if not values or all(v == 0 for v in values):
                return 0.0
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                return 0.0
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
            std_dev = variance ** 0.5
            return std_dev / mean_val
        
        pos_cv = coefficient_of_variation(positive_values)
        neg_cv = coefficient_of_variation(negative_values)
        
        # Lower coefficient of variation = more consistent
        avg_cv = (pos_cv + neg_cv) / 2
        consistency = max(0.0, 1.0 - avg_cv)
        
        return consistency
    
    def _calculate_jurisdictional_agreement(self, snapshots: List[StatusSnapshot]) -> float:
        """Calculate agreement across jurisdictions."""
        
        # Simplified calculation based on jurisdiction count stability
        jurisdiction_counts = [len(s.citing_jurisdictions) for s in snapshots]
        
        if not jurisdiction_counts:
            return 0.5
        
        # More stable jurisdiction count = higher agreement
        max_count = max(jurisdiction_counts)
        min_count = min(jurisdiction_counts)
        
        if max_count == 0:
            return 0.5
        
        agreement = 1.0 - ((max_count - min_count) / max_count)
        return agreement
    
    def _identify_risk_factors(self, snapshots: List[StatusSnapshot]) -> List[str]:
        """Identify risk factors from trend analysis."""
        
        risk_factors = []
        
        latest_snapshot = snapshots[-1]
        
        # Recent negative treatment
        if latest_snapshot.negative_signals > 0:
            risk_factors.append(f"Recent negative treatment ({latest_snapshot.negative_signals} cases)")
        
        # Declining confidence
        if len(snapshots) >= 2:
            confidence_change = latest_snapshot.status_confidence - snapshots[-2].status_confidence
            if confidence_change < -0.2:
                risk_factors.append("Declining status confidence")
        
        # Increasing criticism
        if len(snapshots) >= 2:
            criticism_increase = latest_snapshot.caution_signals - snapshots[-2].caution_signals
            if criticism_increase > 0:
                risk_factors.append(f"Increasing criticism ({criticism_increase} new cases)")
        
        # Low overall confidence
        if latest_snapshot.status_confidence < 0.5:
            risk_factors.append("Low overall status confidence")
        
        # Multiple jurisdictions with mixed signals
        if len(latest_snapshot.citing_jurisdictions) > 3 and latest_snapshot.caution_signals > 2:
            risk_factors.append("Jurisdictional disagreement on treatment")
        
        return risk_factors
    
    def _predict_future_status(self, snapshots: List[StatusSnapshot]) -> Tuple[Optional[CaseStatus], float]:
        """Simple prediction of future status."""
        
        if len(snapshots) < 3:
            return None, 0.0
        
        latest = snapshots[-1]
        
        # Simple rule-based prediction
        if latest.negative_signals > 0 and latest.overall_status == CaseStatus.GOOD_LAW:
            return CaseStatus.QUESTIONABLE, 0.6
        elif latest.caution_signals > latest.positive_signals and latest.overall_status == CaseStatus.GOOD_LAW:
            return CaseStatus.QUESTIONABLE, 0.4
        elif latest.positive_signals > latest.caution_signals and latest.overall_status == CaseStatus.QUESTIONABLE:
            return CaseStatus.GOOD_LAW, 0.3
        else:
            return latest.overall_status, 0.7
    
    async def get_pending_alerts(self, 
                               document_id: Optional[str] = None,
                               severity: Optional[AlertSeverity] = None) -> List[StatusAlert]:
        """Get pending alerts, optionally filtered."""
        
        alerts = []
        
        if document_id:
            alerts.extend(self.pending_alerts.get(document_id, []))
        else:
            for doc_alerts in self.pending_alerts.values():
                alerts.extend(doc_alerts)
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        # Sort by severity and date
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4
        }
        
        alerts.sort(key=lambda x: (severity_order.get(x.severity, 5), x.alert_date), reverse=True)
        
        return alerts
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        
        for document_id, alerts in self.pending_alerts.items():
            for alert in alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_date = datetime.now()
                    self.logger.info(f"Acknowledged alert {alert_id}")
                    return True
        
        return False
    
    async def get_status_summary(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of current status for a document."""
        
        if document_id not in self.status_history:
            return None
        
        latest_snapshot = self.status_history[document_id][-1]
        
        # Get trend if available
        trend_analysis = await self.analyze_status_trends(document_id, 180)  # 6 months
        
        # Get pending alerts
        pending_alerts = self.pending_alerts.get(document_id, [])
        unacknowledged_alerts = [a for a in pending_alerts if not a.acknowledged]
        
        summary = {
            "document_id": document_id,
            "current_status": latest_snapshot.overall_status.value,
            "signal_category": latest_snapshot.signal_category.value,
            "confidence": latest_snapshot.status_confidence,
            "last_updated": latest_snapshot.snapshot_date.isoformat(),
            
            "signal_counts": {
                "positive": latest_snapshot.positive_signals,
                "negative": latest_snapshot.negative_signals,
                "caution": latest_snapshot.caution_signals,
                "neutral": latest_snapshot.neutral_signals
            },
            
            "citations": {
                "total": latest_snapshot.total_citations,
                "jurisdictions": len(latest_snapshot.citing_jurisdictions),
                "recent_treatments": len(latest_snapshot.recent_treatments)
            },
            
            "quality_metrics": {
                "reliability": latest_snapshot.reliability_score,
                "precedential_value": latest_snapshot.precedential_value
            },
            
            "alerts": {
                "total_pending": len(pending_alerts),
                "unacknowledged": len(unacknowledged_alerts),
                "critical": len([a for a in unacknowledged_alerts if a.severity == AlertSeverity.CRITICAL])
            }
        }
        
        # Add trend information if available
        if trend_analysis:
            summary["trend"] = {
                "direction": trend_analysis.overall_trend,
                "confidence": trend_analysis.trend_confidence,
                "stability": trend_analysis.status_stability,
                "risk_factors": trend_analysis.risk_factors
            }
        
        return summary


# Helper functions
async def track_document_status(document: UnifiedDocument, shepard_analysis: ShepardAnalysis) -> StatusSnapshot:
    """Helper function to track document status."""
    tracker = SignalStatusTracker()
    return await tracker.track_document_status(document, shepard_analysis)

async def get_status_alerts(document_id: Optional[str] = None) -> List[StatusAlert]:
    """Helper function to get status alerts."""
    tracker = SignalStatusTracker()
    return await tracker.get_pending_alerts(document_id)