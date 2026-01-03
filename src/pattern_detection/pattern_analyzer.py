"""
Pattern Analyzer

Core pattern detection engine that identifies meaningful patterns in legal case
activities, attorney behaviors, and case outcomes using advanced analytics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import logging
import numpy as np
from collections import defaultdict, Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field

from ..core.database import get_db_session
from ..trial_prep.models import Case, CaseStatus
from ..billing.advanced_models import TimeEntry, ExpenseEntry, Invoice, Payment


logger = logging.getLogger(__name__)


class PatternType(str, Enum):
    """Types of patterns that can be detected."""
    CASE_LIFECYCLE = "case_lifecycle"
    ATTORNEY_BEHAVIOR = "attorney_behavior"
    CLIENT_INTERACTION = "client_interaction"
    BILLING_PATTERN = "billing_pattern"
    DEADLINE_COMPLIANCE = "deadline_compliance"
    DOCUMENT_WORKFLOW = "document_workflow"
    SETTLEMENT_TIMING = "settlement_timing"
    COURT_INTERACTION = "court_interaction"
    RESOURCE_UTILIZATION = "resource_utilization"
    SEASONAL_VARIATION = "seasonal_variation"
    CASE_COMPLEXITY = "case_complexity"
    OUTCOME_CORRELATION = "outcome_correlation"


class PatternSeverity(str, Enum):
    """Severity levels for detected patterns."""
    CRITICAL = "critical"      # Requires immediate attention
    HIGH = "high"             # Should be addressed soon
    MEDIUM = "medium"         # Monitor closely
    LOW = "low"               # Informational
    INFO = "info"             # General insight


class PatternConfidence(str, Enum):
    """Confidence levels for pattern detection."""
    VERY_HIGH = "very_high"   # 90%+ confidence
    HIGH = "high"             # 80-90% confidence
    MEDIUM = "medium"         # 70-80% confidence
    LOW = "low"               # 60-70% confidence
    UNCERTAIN = "uncertain"   # <60% confidence


@dataclass
class DetectedPattern:
    """A detected pattern with metadata and analysis."""
    id: str
    pattern_type: PatternType
    severity: PatternSeverity
    confidence: PatternConfidence
    title: str
    description: str
    
    # Pattern details
    affected_cases: List[int] = field(default_factory=list)
    affected_attorneys: List[int] = field(default_factory=list)
    time_period: Tuple[datetime, datetime] = field(default_factory=lambda: (datetime.utcnow() - timedelta(days=30), datetime.utcnow()))
    
    # Statistical data
    frequency: int = 0
    trend_direction: str = "stable"  # increasing, decreasing, stable
    correlation_strength: float = 0.0
    statistical_significance: float = 0.0
    
    # Insights and recommendations
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    potential_impact: str = ""
    
    # Metadata
    detection_method: str = ""
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class PatternRule(BaseModel):
    """Rule for pattern detection."""
    rule_id: str
    name: str
    pattern_type: PatternType
    description: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    thresholds: Dict[str, float] = Field(default_factory=dict)
    lookback_days: int = 30
    min_occurrences: int = 3
    confidence_threshold: float = 0.7
    is_active: bool = True
    created_by: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PatternAnalyzer:
    """
    Advanced pattern detection engine using statistical analysis and machine learning.
    """
    
    def __init__(self):
        self.detection_rules: List[PatternRule] = []
        self.detected_patterns: Dict[str, DetectedPattern] = {}
        self.historical_data: Dict[str, List[Any]] = defaultdict(list)
        self.analysis_cache: Dict[str, Any] = {}
        
        # Configuration
        self.min_data_points = 10
        self.confidence_threshold = 0.7
        self.analysis_window_days = 90
        
        # Load default detection rules
        self._load_default_rules()
        
    def _load_default_rules(self):
        """Load default pattern detection rules."""
        default_rules = [
            PatternRule(
                rule_id="case_duration_anomaly",
                name="Case Duration Anomaly",
                pattern_type=PatternType.CASE_LIFECYCLE,
                description="Detect cases taking unusually long compared to similar cases",
                conditions={
                    "case_type_similarity": True,
                    "duration_threshold_multiplier": 2.0
                },
                thresholds={
                    "duration_deviation": 2.0,  # Standard deviations
                    "min_cases_for_comparison": 5
                },
                lookback_days=365,
                min_occurrences=3,
                created_by=0
            ),
            PatternRule(
                rule_id="attorney_workload_pattern",
                name="Attorney Workload Pattern",
                pattern_type=PatternType.ATTORNEY_BEHAVIOR,
                description="Identify patterns in attorney workload distribution",
                conditions={
                    "track_billable_hours": True,
                    "track_case_count": True,
                    "include_weekends": False
                },
                thresholds={
                    "overload_threshold": 60.0,  # Hours per week
                    "underutilization_threshold": 20.0
                },
                lookback_days=60,
                created_by=0
            ),
            PatternRule(
                rule_id="settlement_timing_pattern",
                name="Settlement Timing Pattern",
                pattern_type=PatternType.SETTLEMENT_TIMING,
                description="Analyze patterns in when cases settle",
                conditions={
                    "case_type": ["personal_injury", "contract_dispute"],
                    "settlement_stage_analysis": True
                },
                thresholds={
                    "pre_discovery_rate": 0.3,
                    "pre_trial_rate": 0.7
                },
                lookback_days=730,  # 2 years
                min_occurrences=10,
                created_by=0
            ),
            PatternRule(
                rule_id="billing_irregularity",
                name="Billing Irregularity Pattern",
                pattern_type=PatternType.BILLING_PATTERN,
                description="Detect irregular billing patterns",
                conditions={
                    "check_time_gaps": True,
                    "check_rate_variations": True,
                    "check_expense_patterns": True
                },
                thresholds={
                    "time_gap_days": 14,
                    "rate_variation_percent": 0.2,
                    "expense_deviation": 2.0
                },
                lookback_days=90,
                created_by=0
            ),
            PatternRule(
                rule_id="deadline_compliance_pattern",
                name="Deadline Compliance Pattern",
                pattern_type=PatternType.DEADLINE_COMPLIANCE,
                description="Analyze deadline compliance patterns by attorney/case type",
                conditions={
                    "include_court_deadlines": True,
                    "include_internal_deadlines": True
                },
                thresholds={
                    "compliance_rate_threshold": 0.95,
                    "critical_miss_threshold": 0.02
                },
                lookback_days=180,
                min_occurrences=5,
                created_by=0
            ),
            PatternRule(
                rule_id="client_communication_pattern",
                name="Client Communication Pattern",
                pattern_type=PatternType.CLIENT_INTERACTION,
                description="Detect patterns in client communication frequency",
                conditions={
                    "track_email_frequency": True,
                    "track_meeting_frequency": True,
                    "track_response_times": True
                },
                thresholds={
                    "communication_gap_days": 21,
                    "response_time_hours": 48
                },
                lookback_days=120,
                created_by=0
            )
        ]
        
        self.detection_rules.extend(default_rules)
        
    async def analyze_patterns(
        self,
        analysis_type: Optional[PatternType] = None,
        case_ids: Optional[List[int]] = None,
        attorney_ids: Optional[List[int]] = None,
        db: Optional[AsyncSession] = None
    ) -> List[DetectedPattern]:
        """Perform comprehensive pattern analysis."""
        if not db:
            async with get_db_session() as db:
                return await self._analyze_patterns_impl(analysis_type, case_ids, attorney_ids, db)
        return await self._analyze_patterns_impl(analysis_type, case_ids, attorney_ids, db)
        
    async def _analyze_patterns_impl(
        self,
        analysis_type: Optional[PatternType],
        case_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: AsyncSession
    ) -> List[DetectedPattern]:
        """Implementation of pattern analysis."""
        detected_patterns = []
        
        # Filter rules based on analysis type
        applicable_rules = self.detection_rules
        if analysis_type:
            applicable_rules = [r for r in self.detection_rules if r.pattern_type == analysis_type]
            
        # Load historical data for analysis
        historical_data = await self._load_historical_data(case_ids, attorney_ids, db)
        
        # Apply each detection rule
        for rule in applicable_rules:
            if not rule.is_active:
                continue
                
            try:
                patterns = await self._apply_detection_rule(rule, historical_data, db)
                detected_patterns.extend(patterns)
                
            except Exception as e:
                logger.error(f"Error applying rule {rule.rule_id}: {str(e)}")
                
        # Post-process and validate patterns
        validated_patterns = await self._validate_patterns(detected_patterns)
        
        # Store detected patterns
        for pattern in validated_patterns:
            self.detected_patterns[pattern.id] = pattern
            
        logger.info(f"Pattern analysis completed: {len(validated_patterns)} patterns detected")
        return validated_patterns
        
    async def _load_historical_data(
        self,
        case_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Load historical data for pattern analysis."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.analysis_window_days)
        
        data = {
            "cases": [],
            "time_entries": [],
            "expenses": [],
            "invoices": [],
            "payments": []
        }
        
        # Base conditions
        case_conditions = [Case.created_at >= cutoff_date]
        if case_ids:
            case_conditions.append(Case.id.in_(case_ids))
            
        # Load cases
        case_query = select(Case).where(and_(*case_conditions)).options(
            selectinload(Case.deadlines),
            selectinload(Case.documents),
            selectinload(Case.time_entries)
        )
        
        result = await db.execute(case_query)
        data["cases"] = result.scalars().all()
        
        # Get case IDs for filtering other data
        loaded_case_ids = [case.id for case in data["cases"]]
        
        # Load time entries
        time_conditions = [TimeEntry.entry_date >= cutoff_date]
        if loaded_case_ids:
            time_conditions.append(TimeEntry.matter_id.in_(loaded_case_ids))
        if attorney_ids:
            time_conditions.append(TimeEntry.timekeeper.in_(attorney_ids))
            
        time_query = select(TimeEntry).where(and_(*time_conditions))
        result = await db.execute(time_query)
        data["time_entries"] = result.scalars().all()
        
        # Load expenses
        expense_conditions = [ExpenseEntry.expense_date >= cutoff_date]
        if loaded_case_ids:
            expense_conditions.append(ExpenseEntry.matter_id.in_(loaded_case_ids))
            
        expense_query = select(ExpenseEntry).where(and_(*expense_conditions))
        result = await db.execute(expense_query)
        data["expenses"] = result.scalars().all()
        
        # Load invoices and payments
        invoice_conditions = [Invoice.invoice_date >= cutoff_date]
        if loaded_case_ids:
            invoice_conditions.append(Invoice.matter_id.in_(loaded_case_ids))
            
        invoice_query = select(Invoice).where(and_(*invoice_conditions))
        result = await db.execute(invoice_query)
        data["invoices"] = result.scalars().all()
        
        payment_conditions = [Payment.payment_date >= cutoff_date]
        if loaded_case_ids:
            payment_conditions.append(Payment.matter_id.in_(loaded_case_ids))
            
        payment_query = select(Payment).where(and_(*payment_conditions))
        result = await db.execute(payment_query)
        data["payments"] = result.scalars().all()
        
        logger.debug(f"Loaded historical data: {len(data['cases'])} cases, {len(data['time_entries'])} time entries")
        return data
        
    async def _apply_detection_rule(
        self,
        rule: PatternRule,
        historical_data: Dict[str, Any],
        db: AsyncSession
    ) -> List[DetectedPattern]:
        """Apply a specific detection rule to historical data."""
        patterns = []
        
        if rule.pattern_type == PatternType.CASE_LIFECYCLE:
            patterns.extend(await self._detect_case_lifecycle_patterns(rule, historical_data))
        elif rule.pattern_type == PatternType.ATTORNEY_BEHAVIOR:
            patterns.extend(await self._detect_attorney_behavior_patterns(rule, historical_data))
        elif rule.pattern_type == PatternType.BILLING_PATTERN:
            patterns.extend(await self._detect_billing_patterns(rule, historical_data))
        elif rule.pattern_type == PatternType.DEADLINE_COMPLIANCE:
            patterns.extend(await self._detect_deadline_compliance_patterns(rule, historical_data))
        elif rule.pattern_type == PatternType.SETTLEMENT_TIMING:
            patterns.extend(await self._detect_settlement_timing_patterns(rule, historical_data))
        elif rule.pattern_type == PatternType.CLIENT_INTERACTION:
            patterns.extend(await self._detect_client_interaction_patterns(rule, historical_data))
            
        return patterns
        
    async def _detect_case_lifecycle_patterns(
        self,
        rule: PatternRule,
        historical_data: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """Detect patterns in case lifecycles."""
        patterns = []
        cases = historical_data["cases"]
        
        if len(cases) < rule.min_occurrences:
            return patterns
            
        # Analyze case durations by type
        case_durations = defaultdict(list)
        
        for case in cases:
            if case.status in [CaseStatus.CLOSED, CaseStatus.SETTLED]:
                duration = (case.updated_at - case.created_at).days
                case_type = getattr(case, 'case_type', 'general')
                case_durations[case_type].append({
                    'case_id': case.id,
                    'duration': duration,
                    'case': case
                })
                
        # Find anomalous durations
        for case_type, durations in case_durations.items():
            if len(durations) < 3:
                continue
                
            duration_values = [d['duration'] for d in durations]
            mean_duration = np.mean(duration_values)
            std_duration = np.std(duration_values)
            
            if std_duration == 0:
                continue
                
            # Find cases that are significantly longer than average
            threshold_multiplier = rule.conditions.get("duration_threshold_multiplier", 2.0)
            threshold = mean_duration + (std_duration * threshold_multiplier)
            
            anomalous_cases = [
                d for d in durations 
                if d['duration'] > threshold
            ]
            
            if len(anomalous_cases) >= rule.min_occurrences:
                pattern = DetectedPattern(
                    id=f"case_duration_anomaly_{case_type}_{int(datetime.utcnow().timestamp())}",
                    pattern_type=PatternType.CASE_LIFECYCLE,
                    severity=self._calculate_severity(len(anomalous_cases), len(durations)),
                    confidence=self._calculate_confidence(std_duration, mean_duration),
                    title=f"Long Duration Cases - {case_type.title()}",
                    description=f"Found {len(anomalous_cases)} {case_type} cases with unusually long durations",
                    affected_cases=[d['case_id'] for d in anomalous_cases],
                    frequency=len(anomalous_cases),
                    statistical_significance=abs(threshold - mean_duration) / std_duration,
                    insights=[
                        f"Average {case_type} case duration: {mean_duration:.1f} days",
                        f"Anomalous cases averaged {np.mean([d['duration'] for d in anomalous_cases]):.1f} days",
                        f"This is {threshold / mean_duration:.1f}x longer than typical cases"
                    ],
                    recommendations=[
                        "Review workflow efficiency for this case type",
                        "Identify common bottlenecks in long-duration cases",
                        "Consider resource reallocation or process improvements"
                    ],
                    detection_method="Statistical outlier analysis",
                    supporting_data={
                        "case_type": case_type,
                        "mean_duration": mean_duration,
                        "std_duration": std_duration,
                        "threshold": threshold,
                        "anomalous_case_ids": [d['case_id'] for d in anomalous_cases]
                    }
                )
                patterns.append(pattern)
                
        return patterns
        
    async def _detect_attorney_behavior_patterns(
        self,
        rule: PatternRule,
        historical_data: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """Detect patterns in attorney behavior and workload."""
        patterns = []
        time_entries = historical_data["time_entries"]
        
        if not time_entries:
            return patterns
            
        # Analyze workload patterns by attorney
        attorney_workload = defaultdict(lambda: {
            'total_hours': 0,
            'total_entries': 0,
            'cases': set(),
            'weekly_hours': defaultdict(float),
            'daily_pattern': defaultdict(float)
        })
        
        for entry in time_entries:
            attorney_id = entry.timekeeper
            hours = entry.billable_minutes / 60.0 if entry.billable_minutes else 0
            week = entry.entry_date.strftime('%Y-W%U')
            day_of_week = entry.entry_date.weekday()
            
            attorney_workload[attorney_id]['total_hours'] += hours
            attorney_workload[attorney_id]['total_entries'] += 1
            attorney_workload[attorney_id]['cases'].add(entry.matter_id)
            attorney_workload[attorney_id]['weekly_hours'][week] += hours
            attorney_workload[attorney_id]['daily_pattern'][day_of_week] += hours
            
        # Analyze patterns
        weeks_in_period = len(set(entry.entry_date.strftime('%Y-W%U') for entry in time_entries))
        
        overloaded_attorneys = []
        underutilized_attorneys = []
        
        for attorney_id, data in attorney_workload.items():
            avg_weekly_hours = data['total_hours'] / max(weeks_in_period, 1)
            
            overload_threshold = rule.thresholds.get("overload_threshold", 60.0)
            underutil_threshold = rule.thresholds.get("underutilization_threshold", 20.0)
            
            if avg_weekly_hours > overload_threshold:
                overloaded_attorneys.append({
                    'attorney_id': attorney_id,
                    'avg_weekly_hours': avg_weekly_hours,
                    'total_cases': len(data['cases'])
                })
            elif avg_weekly_hours < underutil_threshold:
                underutilized_attorneys.append({
                    'attorney_id': attorney_id,
                    'avg_weekly_hours': avg_weekly_hours,
                    'total_cases': len(data['cases'])
                })
                
        # Create patterns for overloaded attorneys
        if overloaded_attorneys:
            pattern = DetectedPattern(
                id=f"attorney_overload_{int(datetime.utcnow().timestamp())}",
                pattern_type=PatternType.ATTORNEY_BEHAVIOR,
                severity=PatternSeverity.HIGH,
                confidence=PatternConfidence.HIGH,
                title="Attorney Workload Overload Pattern",
                description=f"Detected {len(overloaded_attorneys)} attorneys with excessive workload",
                affected_attorneys=[a['attorney_id'] for a in overloaded_attorneys],
                frequency=len(overloaded_attorneys),
                insights=[
                    f"Overloaded attorneys averaging {np.mean([a['avg_weekly_hours'] for a in overloaded_attorneys]):.1f} hours/week",
                    f"Threshold exceeded by {np.mean([a['avg_weekly_hours'] - overload_threshold for a in overloaded_attorneys]):.1f} hours/week on average",
                    "Risk of burnout and quality degradation"
                ],
                recommendations=[
                    "Redistribute case assignments to balance workload",
                    "Consider hiring additional attorneys or support staff",
                    "Implement workload monitoring and caps",
                    "Review case complexity and resource requirements"
                ],
                detection_method="Workload threshold analysis",
                supporting_data={
                    "overloaded_attorneys": overloaded_attorneys,
                    "threshold": overload_threshold,
                    "analysis_period_weeks": weeks_in_period
                }
            )
            patterns.append(pattern)
            
        # Create patterns for underutilized attorneys
        if underutilized_attorneys:
            pattern = DetectedPattern(
                id=f"attorney_underutilization_{int(datetime.utcnow().timestamp())}",
                pattern_type=PatternType.ATTORNEY_BEHAVIOR,
                severity=PatternSeverity.MEDIUM,
                confidence=PatternConfidence.HIGH,
                title="Attorney Underutilization Pattern",
                description=f"Detected {len(underutilized_attorneys)} attorneys with low utilization",
                affected_attorneys=[a['attorney_id'] for a in underutilized_attorneys],
                frequency=len(underutilized_attorneys),
                insights=[
                    f"Underutilized attorneys averaging {np.mean([a['avg_weekly_hours'] for a in underutilized_attorneys]):.1f} hours/week",
                    "Potential capacity for additional cases",
                    "May indicate skills mismatch or insufficient case flow"
                ],
                recommendations=[
                    "Assign additional cases to underutilized attorneys",
                    "Provide training in high-demand practice areas",
                    "Review billing practices and time tracking",
                    "Consider business development opportunities"
                ],
                detection_method="Workload threshold analysis",
                supporting_data={
                    "underutilized_attorneys": underutilized_attorneys,
                    "threshold": underutil_threshold,
                    "analysis_period_weeks": weeks_in_period
                }
            )
            patterns.append(pattern)
            
        return patterns
        
    async def _detect_billing_patterns(
        self,
        rule: PatternRule,
        historical_data: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """Detect irregular billing patterns."""
        patterns = []
        time_entries = historical_data["time_entries"]
        
        if not time_entries:
            return patterns
            
        # Analyze time entry gaps and patterns
        attorney_patterns = defaultdict(list)
        
        for entry in time_entries:
            attorney_patterns[entry.timekeeper].append({
                'date': entry.entry_date,
                'hours': entry.billable_minutes / 60.0 if entry.billable_minutes else 0,
                'rate': entry.hourly_rate,
                'matter_id': entry.matter_id
            })
            
        # Check each attorney's patterns
        for attorney_id, entries in attorney_patterns.items():
            # Sort by date
            entries.sort(key=lambda x: x['date'])
            
            # Check for time gaps
            time_gap_threshold = rule.thresholds.get("time_gap_days", 14)
            gaps = []
            
            for i in range(1, len(entries)):
                gap_days = (entries[i]['date'] - entries[i-1]['date']).days
                if gap_days > time_gap_threshold:
                    gaps.append({
                        'start_date': entries[i-1]['date'],
                        'end_date': entries[i]['date'],
                        'gap_days': gap_days
                    })
                    
            # Check for rate variations
            rates = [e['rate'] for e in entries if e['rate']]
            if rates:
                rate_std = np.std(rates)
                rate_mean = np.mean(rates)
                rate_cv = rate_std / rate_mean if rate_mean > 0 else 0
                
                rate_variation_threshold = rule.thresholds.get("rate_variation_percent", 0.2)
                
                if rate_cv > rate_variation_threshold:
                    # Significant rate variation detected
                    pattern = DetectedPattern(
                        id=f"billing_rate_variation_{attorney_id}_{int(datetime.utcnow().timestamp())}",
                        pattern_type=PatternType.BILLING_PATTERN,
                        severity=PatternSeverity.MEDIUM,
                        confidence=PatternConfidence.MEDIUM,
                        title=f"Billing Rate Variation - Attorney {attorney_id}",
                        description=f"Detected significant variation in billing rates",
                        affected_attorneys=[attorney_id],
                        frequency=len(entries),
                        insights=[
                            f"Rate variation coefficient: {rate_cv:.2f}",
                            f"Rate range: ${min(rates):.2f} - ${max(rates):.2f}",
                            f"Average rate: ${rate_mean:.2f}"
                        ],
                        recommendations=[
                            "Review rate structure consistency",
                            "Ensure proper rate approvals are in place",
                            "Standardize billing rates by case type or seniority"
                        ],
                        detection_method="Statistical variation analysis",
                        supporting_data={
                            "attorney_id": attorney_id,
                            "rate_stats": {
                                "mean": rate_mean,
                                "std": rate_std,
                                "cv": rate_cv,
                                "min": min(rates),
                                "max": max(rates)
                            }
                        }
                    )
                    patterns.append(pattern)
                    
            # Check for significant time gaps
            if gaps:
                total_gap_days = sum(g['gap_days'] for g in gaps)
                avg_gap = total_gap_days / len(gaps)
                
                pattern = DetectedPattern(
                    id=f"billing_time_gaps_{attorney_id}_{int(datetime.utcnow().timestamp())}",
                    pattern_type=PatternType.BILLING_PATTERN,
                    severity=PatternSeverity.LOW,
                    confidence=PatternConfidence.MEDIUM,
                    title=f"Billing Time Gaps - Attorney {attorney_id}",
                    description=f"Detected {len(gaps)} significant gaps in time entry patterns",
                    affected_attorneys=[attorney_id],
                    frequency=len(gaps),
                    insights=[
                        f"Total gaps: {len(gaps)}",
                        f"Average gap length: {avg_gap:.1f} days",
                        f"Longest gap: {max(g['gap_days'] for g in gaps)} days"
                    ],
                    recommendations=[
                        "Review time tracking compliance",
                        "Implement regular time entry reminders",
                        "Investigate reasons for time tracking gaps"
                    ],
                    detection_method="Time gap analysis",
                    supporting_data={
                        "attorney_id": attorney_id,
                        "gaps": gaps,
                        "gap_threshold": time_gap_threshold
                    }
                )
                patterns.append(pattern)
                
        return patterns
        
    async def _detect_deadline_compliance_patterns(
        self,
        rule: PatternRule,
        historical_data: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """Detect patterns in deadline compliance."""
        patterns = []
        cases = historical_data["cases"]
        
        if not cases:
            return patterns
            
        # Analyze deadline compliance by attorney and case type
        deadline_data = defaultdict(lambda: {
            'total': 0,
            'met': 0,
            'missed': 0,
            'cases': set()
        })
        
        for case in cases:
            if not hasattr(case, 'deadlines') or not case.deadlines:
                continue
                
            attorney_id = getattr(case, 'responsible_attorney', None)
            case_type = getattr(case, 'case_type', 'general')
            
            if not attorney_id:
                continue
                
            key = f"{attorney_id}_{case_type}"
            
            for deadline in case.deadlines:
                deadline_data[key]['total'] += 1
                deadline_data[key]['cases'].add(case.id)
                
                if deadline.is_completed and deadline.completed_date <= deadline.due_date:
                    deadline_data[key]['met'] += 1
                elif not deadline.is_completed and deadline.due_date < datetime.utcnow():
                    deadline_data[key]['missed'] += 1
                elif deadline.is_completed:
                    # Completed late
                    deadline_data[key]['missed'] += 1
                    
        # Identify compliance issues
        compliance_threshold = rule.thresholds.get("compliance_rate_threshold", 0.95)
        
        for key, data in deadline_data.items():
            if data['total'] < rule.min_occurrences:
                continue
                
            compliance_rate = data['met'] / data['total'] if data['total'] > 0 else 1.0
            
            if compliance_rate < compliance_threshold:
                attorney_id, case_type = key.split('_', 1)
                
                pattern = DetectedPattern(
                    id=f"deadline_compliance_{key}_{int(datetime.utcnow().timestamp())}",
                    pattern_type=PatternType.DEADLINE_COMPLIANCE,
                    severity=self._calculate_compliance_severity(compliance_rate),
                    confidence=PatternConfidence.HIGH,
                    title=f"Deadline Compliance Issue - {case_type.title()}",
                    description=f"Low deadline compliance rate detected for Attorney {attorney_id}",
                    affected_attorneys=[int(attorney_id)],
                    affected_cases=list(data['cases']),
                    frequency=data['missed'],
                    statistical_significance=abs(compliance_rate - compliance_threshold),
                    insights=[
                        f"Compliance rate: {compliance_rate:.1%}",
                        f"Total deadlines: {data['total']}",
                        f"Missed deadlines: {data['missed']}",
                        f"Below threshold of {compliance_threshold:.1%}"
                    ],
                    recommendations=[
                        "Implement enhanced deadline tracking",
                        "Provide additional training on deadline management",
                        "Review case workload and resource allocation",
                        "Consider deadline reminder automation"
                    ],
                    detection_method="Compliance rate analysis",
                    supporting_data={
                        "attorney_id": int(attorney_id),
                        "case_type": case_type,
                        "compliance_stats": data,
                        "compliance_rate": compliance_rate,
                        "threshold": compliance_threshold
                    }
                )
                patterns.append(pattern)
                
        return patterns
        
    async def _detect_settlement_timing_patterns(
        self,
        rule: PatternRule,
        historical_data: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """Detect patterns in settlement timing."""
        patterns = []
        cases = historical_data["cases"]
        
        settled_cases = [
            case for case in cases 
            if case.status == CaseStatus.SETTLED
        ]
        
        if len(settled_cases) < rule.min_occurrences:
            return patterns
            
        # Analyze settlement timing patterns
        settlement_stages = defaultdict(list)
        
        for case in settled_cases:
            # Estimate case stage at settlement (simplified)
            case_duration = (case.updated_at - case.created_at).days
            
            if case_duration < 30:
                stage = "pre_discovery"
            elif case_duration < 180:
                stage = "discovery"
            elif case_duration < 365:
                stage = "pre_trial"
            else:
                stage = "trial_prep"
                
            case_type = getattr(case, 'case_type', 'general')
            settlement_stages[case_type].append({
                'case_id': case.id,
                'stage': stage,
                'duration': case_duration
            })
            
        # Analyze patterns by case type
        for case_type, settlements in settlement_stages.items():
            if len(settlements) < 5:
                continue
                
            stage_counts = Counter(s['stage'] for s in settlements)
            total_settlements = len(settlements)
            
            # Calculate stage percentages
            stage_percentages = {
                stage: count / total_settlements 
                for stage, count in stage_counts.items()
            }
            
            # Check against expected patterns
            pre_discovery_threshold = rule.thresholds.get("pre_discovery_rate", 0.3)
            pre_trial_threshold = rule.thresholds.get("pre_trial_rate", 0.7)
            
            insights = []
            recommendations = []
            
            pre_discovery_rate = stage_percentages.get('pre_discovery', 0)
            pre_trial_rate = sum(stage_percentages.get(stage, 0) for stage in ['pre_discovery', 'discovery', 'pre_trial'])
            
            if pre_discovery_rate > pre_discovery_threshold:
                insights.append(f"High early settlement rate: {pre_discovery_rate:.1%}")
                recommendations.append("Cases settling early may indicate strong negotiation or weak claims")
                
            if pre_trial_rate < pre_trial_threshold:
                insights.append(f"Many cases going to trial: {1-pre_trial_rate:.1%}")
                recommendations.append("Consider earlier settlement negotiations")
                
            avg_duration = np.mean([s['duration'] for s in settlements])
            
            pattern = DetectedPattern(
                id=f"settlement_timing_{case_type}_{int(datetime.utcnow().timestamp())}",
                pattern_type=PatternType.SETTLEMENT_TIMING,
                severity=PatternSeverity.INFO,
                confidence=PatternConfidence.MEDIUM,
                title=f"Settlement Timing Pattern - {case_type.title()}",
                description=f"Settlement timing analysis for {total_settlements} {case_type} cases",
                frequency=total_settlements,
                insights=[
                    f"Average settlement duration: {avg_duration:.0f} days",
                    *insights,
                    f"Stage distribution: {dict(stage_counts)}"
                ],
                recommendations=[
                    *recommendations,
                    "Use timing patterns to inform case strategy",
                    "Adjust settlement negotiation timing based on patterns"
                ],
                detection_method="Settlement timing analysis",
                supporting_data={
                    "case_type": case_type,
                    "stage_percentages": stage_percentages,
                    "avg_duration": avg_duration,
                    "settlement_cases": [s['case_id'] for s in settlements]
                }
            )
            patterns.append(pattern)
            
        return patterns
        
    async def _detect_client_interaction_patterns(
        self,
        rule: PatternRule,
        historical_data: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """Detect patterns in client interaction."""
        patterns = []
        
        # This would analyze client communication patterns
        # For now, return empty list as we don't have client communication data
        # In production, this would analyze:
        # - Email frequency and response times
        # - Meeting frequency
        # - Client satisfaction scores
        # - Communication gaps
        
        return patterns
        
    def _calculate_severity(self, affected_count: int, total_count: int) -> PatternSeverity:
        """Calculate severity based on affected items."""
        ratio = affected_count / total_count if total_count > 0 else 0
        
        if ratio >= 0.5 or affected_count >= 10:
            return PatternSeverity.CRITICAL
        elif ratio >= 0.3 or affected_count >= 5:
            return PatternSeverity.HIGH
        elif ratio >= 0.15 or affected_count >= 3:
            return PatternSeverity.MEDIUM
        else:
            return PatternSeverity.LOW
            
    def _calculate_confidence(self, std_dev: float, mean_value: float) -> PatternConfidence:
        """Calculate confidence based on statistical metrics."""
        if mean_value == 0:
            return PatternConfidence.UNCERTAIN
            
        coefficient_of_variation = std_dev / abs(mean_value)
        
        if coefficient_of_variation < 0.1:
            return PatternConfidence.VERY_HIGH
        elif coefficient_of_variation < 0.2:
            return PatternConfidence.HIGH
        elif coefficient_of_variation < 0.4:
            return PatternConfidence.MEDIUM
        elif coefficient_of_variation < 0.6:
            return PatternConfidence.LOW
        else:
            return PatternConfidence.UNCERTAIN
            
    def _calculate_compliance_severity(self, compliance_rate: float) -> PatternSeverity:
        """Calculate severity for compliance issues."""
        if compliance_rate < 0.8:
            return PatternSeverity.CRITICAL
        elif compliance_rate < 0.9:
            return PatternSeverity.HIGH
        elif compliance_rate < 0.95:
            return PatternSeverity.MEDIUM
        else:
            return PatternSeverity.LOW
            
    async def _validate_patterns(self, patterns: List[DetectedPattern]) -> List[DetectedPattern]:
        """Validate and filter detected patterns."""
        validated = []
        
        for pattern in patterns:
            # Filter by confidence threshold
            confidence_scores = {
                PatternConfidence.VERY_HIGH: 0.95,
                PatternConfidence.HIGH: 0.85,
                PatternConfidence.MEDIUM: 0.75,
                PatternConfidence.LOW: 0.65,
                PatternConfidence.UNCERTAIN: 0.5
            }
            
            confidence_score = confidence_scores.get(pattern.confidence, 0.5)
            
            if confidence_score >= self.confidence_threshold:
                validated.append(pattern)
                
        return validated
        
    # Public API methods
    
    async def get_detected_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        severity: Optional[PatternSeverity] = None,
        limit: Optional[int] = None
    ) -> List[DetectedPattern]:
        """Get detected patterns with optional filtering."""
        patterns = list(self.detected_patterns.values())
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
            
        if severity:
            patterns = [p for p in patterns if p.severity == severity]
            
        # Sort by severity and confidence
        severity_order = {
            PatternSeverity.CRITICAL: 0,
            PatternSeverity.HIGH: 1,
            PatternSeverity.MEDIUM: 2,
            PatternSeverity.LOW: 3,
            PatternSeverity.INFO: 4
        }
        
        patterns.sort(key=lambda x: (severity_order.get(x.severity, 5), -x.statistical_significance))
        
        if limit:
            patterns = patterns[:limit]
            
        return patterns
        
    async def add_detection_rule(self, rule: PatternRule) -> bool:
        """Add a new pattern detection rule."""
        # Check for duplicate rule ID
        for existing_rule in self.detection_rules:
            if existing_rule.rule_id == rule.rule_id:
                return False
                
        self.detection_rules.append(rule)
        logger.info(f"Added pattern detection rule: {rule.name}")
        return True
        
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern detection statistics."""
        patterns = list(self.detected_patterns.values())
        
        # Count by type
        type_counts = Counter(p.pattern_type for p in patterns)
        
        # Count by severity
        severity_counts = Counter(p.severity for p in patterns)
        
        # Count by confidence
        confidence_counts = Counter(p.confidence for p in patterns)
        
        return {
            "total_patterns": len(patterns),
            "detection_rules": len(self.detection_rules),
            "active_rules": len([r for r in self.detection_rules if r.is_active]),
            "pattern_types": dict(type_counts),
            "severity_distribution": dict(severity_counts),
            "confidence_distribution": dict(confidence_counts),
            "last_analysis": max([p.created_at for p in patterns]) if patterns else None
        }