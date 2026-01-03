"""
Intelligent Alerts Engine

Advanced alert system with ML-powered classification, risk assessment,
and intelligent prioritization for legal case management.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import logging
import json
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from .case_monitor import CaseAlert, AlertType, AlertPriority
from .deadline_tracker import DeadlineAlert
from .document_watcher import DocumentAlert
from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class AlertClassification(str, Enum):
    """AI-powered alert classifications."""
    URGENT_ACTION_REQUIRED = "urgent_action_required"
    DEADLINE_CRITICAL = "deadline_critical"
    COMPLIANCE_RISK = "compliance_risk"
    CLIENT_COMMUNICATION_NEEDED = "client_communication_needed"
    DOCUMENT_REVIEW_REQUIRED = "document_review_required"
    FINANCIAL_ATTENTION = "financial_attention"
    PROCEDURAL_ISSUE = "procedural_issue"
    OPPORTUNITY = "opportunity"
    INFORMATIONAL = "informational"


class RiskLevel(str, Enum):
    """Risk levels for alert prioritization."""
    CRITICAL = "critical"      # Immediate malpractice/sanctions risk
    HIGH = "high"             # Significant case impact risk
    MEDIUM = "medium"         # Moderate risk to case or client
    LOW = "low"               # Minor procedural risk
    MINIMAL = "minimal"       # Informational only


class AlertSource(str, Enum):
    """Sources of alerts."""
    CASE_MONITOR = "case_monitor"
    DEADLINE_TRACKER = "deadline_tracker"
    DOCUMENT_WATCHER = "document_watcher"
    COMPLIANCE_MONITOR = "compliance_monitor"
    COURT_CALENDAR = "court_calendar"
    RESEARCH_ANALYZER = "research_analyzer"
    EXTERNAL_API = "external_api"


@dataclass
class RiskAssessment:
    """Risk assessment for an alert."""
    risk_level: RiskLevel
    risk_factors: List[str] = field(default_factory=list)
    potential_consequences: List[str] = field(default_factory=list)
    mitigation_steps: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntelligentAlert:
    """Enhanced alert with AI-powered analysis."""
    id: str
    source: AlertSource
    original_alert: Any  # Original alert object
    classification: AlertClassification
    risk_assessment: RiskAssessment
    priority_score: float  # 0.0 to 1.0
    context_analysis: Dict[str, Any] = field(default_factory=dict)
    related_alerts: List[str] = field(default_factory=list)
    auto_actions_taken: List[str] = field(default_factory=list)
    escalation_path: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertPattern(BaseModel):
    """Pattern recognition for alert correlation."""
    pattern_id: str
    name: str
    description: str
    alert_types: List[AlertType]
    time_window_hours: int = 24
    min_occurrences: int = 2
    correlation_rules: Dict[str, Any] = Field(default_factory=dict)
    escalation_threshold: int = 3
    is_active: bool = True


class NotificationRule(BaseModel):
    """Rule for intelligent notification routing."""
    rule_id: str
    name: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    target_roles: List[str] = Field(default_factory=list)
    notification_methods: List[str] = Field(default_factory=list)
    urgency_threshold: float = 0.7
    suppress_duplicates: bool = True
    escalation_delay_minutes: int = 60
    is_active: bool = True


class IntelligentAlertsEngine:
    """
    Advanced alert processing engine with ML-powered classification and risk assessment.
    """
    
    def __init__(self):
        self.processed_alerts: Dict[str, IntelligentAlert] = {}
        self.alert_patterns: List[AlertPattern] = []
        self.notification_rules: List[NotificationRule] = []
        self.risk_models: Dict[str, Any] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.context_cache: Dict[str, Any] = {}
        
        # Load default patterns and rules
        self._load_default_patterns()
        self._load_default_notification_rules()
        self._initialize_risk_models()
        
    def _load_default_patterns(self):
        """Load default alert correlation patterns."""
        default_patterns = [
            AlertPattern(
                pattern_id="deadline_cascade",
                name="Deadline Cascade Pattern",
                description="Multiple related deadlines approaching simultaneously",
                alert_types=[AlertType.DEADLINE_APPROACHING, AlertType.DEADLINE_OVERDUE],
                time_window_hours=72,
                min_occurrences=3,
                correlation_rules={
                    "same_case": True,
                    "deadline_proximity_days": 7
                },
                escalation_threshold=5
            ),
            AlertPattern(
                pattern_id="document_activity_surge",
                name="Document Activity Surge",
                description="Unusual increase in document activity",
                alert_types=[AlertType.DOCUMENT_FILED, AlertType.OPPOSING_COUNSEL_ACTIVITY],
                time_window_hours=24,
                min_occurrences=4,
                correlation_rules={
                    "case_related": True,
                    "activity_threshold": 3
                }
            ),
            AlertPattern(
                pattern_id="compliance_violation_cluster",
                name="Compliance Violation Cluster",
                description="Multiple compliance issues in related areas",
                alert_types=[AlertType.COMPLIANCE_VIOLATION],
                time_window_hours=48,
                min_occurrences=2,
                correlation_rules={
                    "violation_type_related": True
                },
                escalation_threshold=2
            ),
            AlertPattern(
                pattern_id="case_crisis_indicators",
                name="Case Crisis Indicators",
                description="Multiple indicators suggesting case is in crisis",
                alert_types=[
                    AlertType.DEADLINE_OVERDUE,
                    AlertType.BUDGET_EXCEEDED,
                    AlertType.COMPLIANCE_VIOLATION,
                    AlertType.COURT_ORDER_RECEIVED
                ],
                time_window_hours=48,
                min_occurrences=3,
                escalation_threshold=3
            )
        ]
        
        self.alert_patterns.extend(default_patterns)
        
    def _load_default_notification_rules(self):
        """Load default notification routing rules."""
        default_rules = [
            NotificationRule(
                rule_id="critical_deadline_escalation",
                name="Critical Deadline Escalation",
                conditions={
                    "classification": "deadline_critical",
                    "risk_level": "critical",
                    "days_until_deadline": {"<=": 1}
                },
                target_roles=["responsible_attorney", "supervising_partner", "case_manager"],
                notification_methods=["email", "sms", "push_notification", "phone_call"],
                urgency_threshold=0.9,
                escalation_delay_minutes=15
            ),
            NotificationRule(
                rule_id="court_document_immediate",
                name="Court Document Immediate Notice",
                conditions={
                    "alert_type": "new_court_document",
                    "document_type": ["court_order", "judgment", "motion_granted"]
                },
                target_roles=["responsible_attorney", "case_manager"],
                notification_methods=["email", "push_notification"],
                urgency_threshold=0.8,
                suppress_duplicates=False
            ),
            NotificationRule(
                rule_id="compliance_risk_escalation",
                name="Compliance Risk Escalation",
                conditions={
                    "classification": "compliance_risk",
                    "risk_level": ["critical", "high"]
                },
                target_roles=["compliance_officer", "managing_partner", "responsible_attorney"],
                notification_methods=["email", "secure_message"],
                escalation_delay_minutes=30
            ),
            NotificationRule(
                rule_id="client_communication_standard",
                name="Client Communication Standard",
                conditions={
                    "classification": "client_communication_needed",
                    "urgency": {">=": 0.6}
                },
                target_roles=["responsible_attorney", "client_relations"],
                notification_methods=["email", "task_assignment"],
                escalation_delay_minutes=120
            )
        ]
        
        self.notification_rules.extend(default_rules)
        
    def _initialize_risk_models(self):
        """Initialize ML models for risk assessment."""
        # In production, these would be trained ML models
        self.risk_models = {
            "deadline_risk": {
                "weights": {
                    "days_until_due": -0.3,
                    "case_complexity": 0.2,
                    "attorney_workload": 0.1,
                    "deadline_type_criticality": 0.4
                },
                "thresholds": {
                    "critical": 0.8,
                    "high": 0.6,
                    "medium": 0.4,
                    "low": 0.2
                }
            },
            "document_risk": {
                "weights": {
                    "document_type_criticality": 0.4,
                    "change_type_impact": 0.3,
                    "case_stage_sensitivity": 0.2,
                    "stakeholder_impact": 0.1
                },
                "thresholds": {
                    "critical": 0.75,
                    "high": 0.55,
                    "medium": 0.35,
                    "low": 0.15
                }
            },
            "case_health": {
                "weights": {
                    "overdue_deadlines": 0.3,
                    "budget_variance": 0.2,
                    "activity_level": -0.1,
                    "client_satisfaction": -0.2,
                    "timeline_adherence": -0.2
                }
            }
        }
        
    async def process_alert(
        self,
        source: AlertSource,
        alert: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> IntelligentAlert:
        """Process an incoming alert with AI analysis."""
        try:
            # Extract basic information from alert
            alert_id = self._generate_alert_id(source, alert)
            
            # Classify the alert
            classification = await self._classify_alert(alert, source, context)
            
            # Assess risk
            risk_assessment = await self._assess_risk(alert, classification, context)
            
            # Calculate priority score
            priority_score = await self._calculate_priority_score(
                alert, classification, risk_assessment, context
            )
            
            # Analyze context and relationships
            context_analysis = await self._analyze_context(alert, source, context)
            
            # Find related alerts
            related_alerts = await self._find_related_alerts(alert, context)
            
            # Determine escalation path
            escalation_path = await self._determine_escalation_path(
                classification, risk_assessment, context
            )
            
            # Create intelligent alert
            intelligent_alert = IntelligentAlert(
                id=alert_id,
                source=source,
                original_alert=alert,
                classification=classification,
                risk_assessment=risk_assessment,
                priority_score=priority_score,
                context_analysis=context_analysis,
                related_alerts=related_alerts,
                escalation_path=escalation_path,
                processed_at=datetime.utcnow()
            )
            
            # Store processed alert
            self.processed_alerts[alert_id] = intelligent_alert
            
            # Check for patterns and correlations
            await self._check_alert_patterns(intelligent_alert)
            
            # Execute auto-actions if applicable
            await self._execute_auto_actions(intelligent_alert)
            
            # Log processing
            logger.info(f"Processed {source} alert: {classification} (priority: {priority_score:.2f})")
            
            return intelligent_alert
            
        except Exception as e:
            logger.error(f"Error processing alert from {source}: {str(e)}")
            raise
            
    def _generate_alert_id(self, source: AlertSource, alert: Any) -> str:
        """Generate unique alert ID."""
        timestamp = int(datetime.utcnow().timestamp())
        
        # Try to get original alert ID
        original_id = getattr(alert, 'id', 'unknown')
        
        return f"{source.value}_{original_id}_{timestamp}"
        
    async def _classify_alert(
        self,
        alert: Any,
        source: AlertSource,
        context: Optional[Dict[str, Any]]
    ) -> AlertClassification:
        """Classify alert using ML-powered analysis."""
        
        # Extract features for classification
        features = await self._extract_classification_features(alert, source, context)
        
        # Simple rule-based classification (would use ML model in production)
        if source == AlertSource.DEADLINE_TRACKER:
            deadline_alert = alert
            if hasattr(deadline_alert, 'days_until_due'):
                if deadline_alert.days_until_due <= 0:
                    return AlertClassification.URGENT_ACTION_REQUIRED
                elif deadline_alert.days_until_due <= 1:
                    return AlertClassification.DEADLINE_CRITICAL
                else:
                    return AlertClassification.DEADLINE_CRITICAL
                    
        elif source == AlertSource.DOCUMENT_WATCHER:
            doc_alert = alert
            if hasattr(doc_alert, 'alert_type'):
                if doc_alert.alert_type == "new_court_document":
                    return AlertClassification.URGENT_ACTION_REQUIRED
                elif doc_alert.alert_type == "document_deleted":
                    return AlertClassification.DOCUMENT_REVIEW_REQUIRED
                else:
                    return AlertClassification.DOCUMENT_REVIEW_REQUIRED
                    
        elif source == AlertSource.CASE_MONITOR:
            case_alert = alert
            if hasattr(case_alert, 'alert_type'):
                if case_alert.alert_type == AlertType.COMPLIANCE_VIOLATION:
                    return AlertClassification.COMPLIANCE_RISK
                elif case_alert.alert_type == AlertType.BUDGET_EXCEEDED:
                    return AlertClassification.FINANCIAL_ATTENTION
                elif case_alert.alert_type in [
                    AlertType.DEADLINE_OVERDUE, 
                    AlertType.COURT_ORDER_RECEIVED
                ]:
                    return AlertClassification.URGENT_ACTION_REQUIRED
                else:
                    return AlertClassification.PROCEDURAL_ISSUE
                    
        # Default classification
        return AlertClassification.INFORMATIONAL
        
    async def _extract_classification_features(
        self,
        alert: Any,
        source: AlertSource,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract features for ML classification."""
        features = {
            "source": source.value,
            "timestamp": datetime.utcnow().hour,  # Time of day
            "day_of_week": datetime.utcnow().weekday(),
        }
        
        # Add alert-specific features
        if hasattr(alert, 'priority'):
            features['priority'] = alert.priority
        if hasattr(alert, 'alert_type'):
            features['alert_type'] = str(alert.alert_type)
            
        # Add context features
        if context:
            features.update({
                "case_id": context.get("case_id"),
                "case_type": context.get("case_type"),
                "case_stage": context.get("case_stage"),
                "attorney_workload": context.get("attorney_workload", 0.5)
            })
            
        return features
        
    async def _assess_risk(
        self,
        alert: Any,
        classification: AlertClassification,
        context: Optional[Dict[str, Any]]
    ) -> RiskAssessment:
        """Assess risk level and consequences."""
        risk_factors = []
        potential_consequences = []
        mitigation_steps = []
        
        # Determine base risk level from classification
        if classification == AlertClassification.URGENT_ACTION_REQUIRED:
            risk_level = RiskLevel.CRITICAL
            risk_factors.append("Immediate action required")
            potential_consequences.extend([
                "Missed deadlines", 
                "Sanctions", 
                "Malpractice exposure"
            ])
            mitigation_steps.extend([
                "Take immediate corrective action",
                "Notify supervising attorney",
                "Document response"
            ])
            
        elif classification == AlertClassification.DEADLINE_CRITICAL:
            risk_level = RiskLevel.HIGH
            risk_factors.append("Critical deadline approaching")
            potential_consequences.extend([
                "Missed filing deadline",
                "Loss of rights",
                "Client prejudice"
            ])
            mitigation_steps.extend([
                "Prioritize deadline compliance",
                "Prepare necessary filings",
                "Set additional reminders"
            ])
            
        elif classification == AlertClassification.COMPLIANCE_RISK:
            risk_level = RiskLevel.HIGH
            risk_factors.append("Compliance violation detected")
            potential_consequences.extend([
                "Regulatory sanctions",
                "Professional discipline",
                "Client relationship damage"
            ])
            mitigation_steps.extend([
                "Review compliance requirements",
                "Implement corrective measures",
                "Report to compliance officer"
            ])
            
        elif classification in [
            AlertClassification.CLIENT_COMMUNICATION_NEEDED,
            AlertClassification.DOCUMENT_REVIEW_REQUIRED
        ]:
            risk_level = RiskLevel.MEDIUM
            risk_factors.append("Process issue requiring attention")
            potential_consequences.extend([
                "Client dissatisfaction",
                "Process delays",
                "Quality concerns"
            ])
            mitigation_steps.extend([
                "Address within business day",
                "Follow standard procedures",
                "Document resolution"
            ])
            
        else:
            risk_level = RiskLevel.LOW
            risk_factors.append("Routine matter")
            potential_consequences.append("Minor process impact")
            mitigation_steps.append("Handle per standard workflow")
            
        # Adjust risk based on context
        if context:
            case_complexity = context.get("case_complexity", 0.5)
            if case_complexity > 0.8:
                risk_factors.append("High-complexity case")
                if risk_level == RiskLevel.MEDIUM:
                    risk_level = RiskLevel.HIGH
                elif risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
                    
        # Calculate confidence score (simplified)
        confidence_score = 0.8 if context else 0.6
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_factors=risk_factors,
            potential_consequences=potential_consequences,
            mitigation_steps=mitigation_steps,
            confidence_score=confidence_score
        )
        
    async def _calculate_priority_score(
        self,
        alert: Any,
        classification: AlertClassification,
        risk_assessment: RiskAssessment,
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate priority score (0.0 to 1.0)."""
        base_scores = {
            AlertClassification.URGENT_ACTION_REQUIRED: 0.95,
            AlertClassification.DEADLINE_CRITICAL: 0.90,
            AlertClassification.COMPLIANCE_RISK: 0.85,
            AlertClassification.CLIENT_COMMUNICATION_NEEDED: 0.70,
            AlertClassification.DOCUMENT_REVIEW_REQUIRED: 0.65,
            AlertClassification.FINANCIAL_ATTENTION: 0.60,
            AlertClassification.PROCEDURAL_ISSUE: 0.50,
            AlertClassification.OPPORTUNITY: 0.40,
            AlertClassification.INFORMATIONAL: 0.20
        }
        
        base_score = base_scores.get(classification, 0.5)
        
        # Adjust based on risk level
        risk_multipliers = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.9,
            RiskLevel.MEDIUM: 0.8,
            RiskLevel.LOW: 0.7,
            RiskLevel.MINIMAL: 0.6
        }
        
        risk_multiplier = risk_multipliers.get(risk_assessment.risk_level, 0.8)
        
        # Adjust based on urgency indicators
        urgency_bonus = 0.0
        if hasattr(alert, 'days_until_due'):
            days = getattr(alert, 'days_until_due', 30)
            if days <= 0:
                urgency_bonus = 0.1
            elif days <= 1:
                urgency_bonus = 0.05
                
        # Context adjustments
        context_adjustment = 0.0
        if context:
            # High-value cases get priority boost
            case_value = context.get("case_value", 0)
            if case_value > 100000:
                context_adjustment += 0.05
            elif case_value > 1000000:
                context_adjustment += 0.1
                
            # VIP clients get priority boost
            if context.get("client_vip", False):
                context_adjustment += 0.05
                
        final_score = min(1.0, base_score * risk_multiplier + urgency_bonus + context_adjustment)
        return round(final_score, 3)
        
    async def _analyze_context(
        self,
        alert: Any,
        source: AlertSource,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze alert context for additional insights."""
        analysis = {
            "source": source.value,
            "processed_at": datetime.utcnow().isoformat(),
            "business_hours": self._is_business_hours(),
            "weekend": datetime.utcnow().weekday() >= 5
        }
        
        # Add alert-specific context
        if hasattr(alert, 'case_id'):
            case_id = getattr(alert, 'case_id')
            analysis["case_id"] = case_id
            
            # Get case context from cache or database
            case_context = await self._get_case_context(case_id)
            analysis.update(case_context)
            
        # Add timing analysis
        analysis["timing_analysis"] = await self._analyze_timing_context(alert)
        
        # Add workload context
        analysis["workload_context"] = await self._analyze_workload_context(alert, context)
        
        return analysis
        
    def _is_business_hours(self) -> bool:
        """Check if current time is during business hours."""
        now = datetime.utcnow()
        # Assuming 9 AM to 6 PM business hours (simplified)
        return 9 <= now.hour < 18 and now.weekday() < 5
        
    async def _get_case_context(self, case_id: int) -> Dict[str, Any]:
        """Get cached context for a case."""
        cache_key = f"case_{case_id}"
        
        if cache_key in self.context_cache:
            cached_context = self.context_cache[cache_key]
            # Check if cache is still valid (1 hour)
            if (datetime.utcnow() - cached_context["cached_at"]).seconds < 3600:
                return cached_context["data"]
                
        # Would fetch from database in real implementation
        context = {
            "case_stage": "discovery",
            "case_complexity": 0.7,
            "case_value": 500000,
            "attorney_count": 2,
            "client_vip": False,
            "recent_activity_level": 0.6
        }
        
        # Cache the context
        self.context_cache[cache_key] = {
            "data": context,
            "cached_at": datetime.utcnow()
        }
        
        return context
        
    async def _analyze_timing_context(self, alert: Any) -> Dict[str, Any]:
        """Analyze timing context of alert."""
        now = datetime.utcnow()
        
        return {
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
            "is_business_hours": self._is_business_hours(),
            "is_end_of_day": now.hour >= 17,
            "is_end_of_week": now.weekday() == 4 and now.hour >= 15,
            "is_holiday_period": False  # Would check holiday calendar
        }
        
    async def _analyze_workload_context(
        self,
        alert: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze current workload context."""
        # Would analyze actual workload data in production
        return {
            "current_alert_volume": len(self.processed_alerts),
            "recent_alert_trend": "stable",  # increasing, decreasing, stable
            "team_availability": 0.7,
            "critical_alerts_pending": len([
                a for a in self.processed_alerts.values() 
                if a.risk_assessment.risk_level == RiskLevel.CRITICAL and not a.resolved_at
            ])
        }
        
    async def _find_related_alerts(
        self,
        alert: Any,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Find alerts related to this one."""
        related = []
        
        # Find alerts for same case
        if hasattr(alert, 'case_id'):
            case_id = getattr(alert, 'case_id')
            for alert_id, processed_alert in self.processed_alerts.items():
                if (hasattr(processed_alert.original_alert, 'case_id') and
                    getattr(processed_alert.original_alert, 'case_id') == case_id and
                    not processed_alert.resolved_at):
                    related.append(alert_id)
                    
        # Find alerts of similar type within time window
        alert_type = getattr(alert, 'alert_type', None)
        if alert_type:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            for alert_id, processed_alert in self.processed_alerts.items():
                if (hasattr(processed_alert.original_alert, 'alert_type') and
                    getattr(processed_alert.original_alert, 'alert_type') == alert_type and
                    processed_alert.created_at > cutoff_time and
                    not processed_alert.resolved_at):
                    related.append(alert_id)
                    
        return list(set(related))  # Remove duplicates
        
    async def _determine_escalation_path(
        self,
        classification: AlertClassification,
        risk_assessment: RiskAssessment,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Determine escalation path for alert."""
        escalation_path = ["responsible_attorney"]
        
        if risk_assessment.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            escalation_path.append("supervising_attorney")
            
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            escalation_path.append("managing_partner")
            
        if classification == AlertClassification.COMPLIANCE_RISK:
            escalation_path.append("compliance_officer")
            
        if classification == AlertClassification.CLIENT_COMMUNICATION_NEEDED:
            escalation_path.append("client_relations_manager")
            
        return escalation_path
        
    async def _check_alert_patterns(self, intelligent_alert: IntelligentAlert):
        """Check for alert patterns and correlations."""
        for pattern in self.alert_patterns:
            if not pattern.is_active:
                continue
                
            if await self._alert_matches_pattern(intelligent_alert, pattern):
                await self._handle_pattern_match(intelligent_alert, pattern)
                
    async def _alert_matches_pattern(
        self,
        alert: IntelligentAlert,
        pattern: AlertPattern
    ) -> bool:
        """Check if alert matches a correlation pattern."""
        # Check if alert type matches
        original_alert = alert.original_alert
        if hasattr(original_alert, 'alert_type'):
            alert_type = getattr(original_alert, 'alert_type')
            if alert_type not in pattern.alert_types:
                return False
                
        # Check time window
        cutoff_time = datetime.utcnow() - timedelta(hours=pattern.time_window_hours)
        
        # Count matching alerts in time window
        matching_alerts = []
        for processed_alert in self.processed_alerts.values():
            if processed_alert.created_at < cutoff_time:
                continue
                
            if self._alerts_correlate(alert, processed_alert, pattern):
                matching_alerts.append(processed_alert)
                
        return len(matching_alerts) >= pattern.min_occurrences
        
    def _alerts_correlate(
        self,
        alert1: IntelligentAlert,
        alert2: IntelligentAlert,
        pattern: AlertPattern
    ) -> bool:
        """Check if two alerts correlate according to pattern rules."""
        rules = pattern.correlation_rules
        
        # Check same case correlation
        if rules.get("same_case", False):
            case1 = getattr(alert1.original_alert, 'case_id', None)
            case2 = getattr(alert2.original_alert, 'case_id', None)
            if case1 != case2:
                return False
                
        # Check deadline proximity
        if "deadline_proximity_days" in rules:
            # Would implement deadline proximity check
            pass
            
        return True
        
    async def _handle_pattern_match(
        self,
        alert: IntelligentAlert,
        pattern: AlertPattern
    ):
        """Handle when an alert pattern is detected."""
        logger.warning(f"Alert pattern detected: {pattern.name}")
        
        # Increase priority of related alerts
        for related_id in alert.related_alerts:
            if related_id in self.processed_alerts:
                related_alert = self.processed_alerts[related_id]
                related_alert.priority_score = min(1.0, related_alert.priority_score + 0.1)
                
        # Check escalation threshold
        matching_count = len(alert.related_alerts) + 1
        if matching_count >= pattern.escalation_threshold:
            await self._escalate_pattern(pattern, alert, matching_count)
            
    async def _escalate_pattern(
        self,
        pattern: AlertPattern,
        alert: IntelligentAlert,
        matching_count: int
    ):
        """Escalate when pattern threshold is reached."""
        logger.critical(f"Pattern escalation: {pattern.name} with {matching_count} matching alerts")
        
        # Would send escalation notifications
        # Update alert escalation path
        if "managing_partner" not in alert.escalation_path:
            alert.escalation_path.append("managing_partner")
            
    async def _execute_auto_actions(self, alert: IntelligentAlert):
        """Execute automated actions for high-priority alerts."""
        auto_actions = []
        
        # Critical alerts get immediate notifications
        if alert.risk_assessment.risk_level == RiskLevel.CRITICAL:
            auto_actions.append("immediate_notification_sent")
            # Would actually send notifications here
            
        # Deadline alerts get calendar reminders
        if alert.classification == AlertClassification.DEADLINE_CRITICAL:
            auto_actions.append("calendar_reminder_created")
            # Would create calendar entries here
            
        # Compliance alerts get logged
        if alert.classification == AlertClassification.COMPLIANCE_RISK:
            auto_actions.append("compliance_log_updated")
            # Would update compliance tracking here
            
        alert.auto_actions_taken = auto_actions
        
        if auto_actions:
            logger.info(f"Executed auto-actions for alert {alert.id}: {', '.join(auto_actions)}")
            
    # Public API methods
    
    async def get_intelligent_alerts(
        self,
        classification: Optional[AlertClassification] = None,
        risk_level: Optional[RiskLevel] = None,
        unresolved_only: bool = True,
        limit: Optional[int] = None
    ) -> List[IntelligentAlert]:
        """Get intelligent alerts with filtering."""
        alerts = []
        
        for alert in self.processed_alerts.values():
            if unresolved_only and alert.resolved_at:
                continue
                
            if classification and alert.classification != classification:
                continue
                
            if risk_level and alert.risk_assessment.risk_level != risk_level:
                continue
                
            alerts.append(alert)
            
        # Sort by priority score (descending)
        alerts.sort(key=lambda x: x.priority_score, reverse=True)
        
        if limit:
            alerts = alerts[:limit]
            
        return alerts
        
    async def acknowledge_alert(self, alert_id: str, user_id: int) -> bool:
        """Acknowledge an intelligent alert."""
        if alert_id in self.processed_alerts:
            self.processed_alerts[alert_id].acknowledged_at = datetime.utcnow()
            logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
            return True
        return False
        
    async def resolve_alert(self, alert_id: str, user_id: int, resolution_notes: Optional[str] = None) -> bool:
        """Resolve an intelligent alert."""
        if alert_id in self.processed_alerts:
            alert = self.processed_alerts[alert_id]
            alert.resolved_at = datetime.utcnow()
            if resolution_notes:
                alert.context_analysis["resolution_notes"] = resolution_notes
            logger.info(f"Alert {alert_id} resolved by user {user_id}")
            return True
        return False
        
    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert processing statistics."""
        total_alerts = len(self.processed_alerts)
        
        # Count by classification
        classification_counts = defaultdict(int)
        risk_level_counts = defaultdict(int)
        
        resolved_count = 0
        acknowledged_count = 0
        
        for alert in self.processed_alerts.values():
            classification_counts[alert.classification] += 1
            risk_level_counts[alert.risk_assessment.risk_level] += 1
            
            if alert.resolved_at:
                resolved_count += 1
            if alert.acknowledged_at:
                acknowledged_count += 1
                
        return {
            "total_alerts": total_alerts,
            "resolved_alerts": resolved_count,
            "acknowledged_alerts": acknowledged_count,
            "active_alerts": total_alerts - resolved_count,
            "classification_breakdown": dict(classification_counts),
            "risk_level_breakdown": dict(risk_level_counts),
            "active_patterns": len([p for p in self.alert_patterns if p.is_active]),
            "notification_rules": len([r for r in self.notification_rules if r.is_active])
        }