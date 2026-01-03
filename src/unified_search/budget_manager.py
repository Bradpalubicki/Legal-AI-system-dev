"""
Comprehensive budget management system for legal research costs.
Provides budget planning, monitoring, alerts, and enforcement capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import calendar
import uuid

from ..types.unified_types import UnifiedDocument, ContentType
from .cost_tracker import CostTracker, CostEvent, ResourceType, CostCategory


class BudgetPeriod(Enum):
    """Budget period types."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    CUSTOM = "custom"


class BudgetType(Enum):
    """Types of budgets."""
    TOTAL_RESEARCH = "total_research"
    USER_SPECIFIC = "user_specific"
    MATTER_SPECIFIC = "matter_specific"
    CLIENT_SPECIFIC = "client_specific"
    RESOURCE_SPECIFIC = "resource_specific"
    CATEGORY_SPECIFIC = "category_specific"
    DEPARTMENT_SPECIFIC = "department_specific"


class AlertType(Enum):
    """Types of budget alerts."""
    THRESHOLD_WARNING = "threshold_warning"    # 75%, 90% thresholds
    BUDGET_EXCEEDED = "budget_exceeded"       # Over budget
    OVERSPEND_PROJECTION = "overspend_projection"  # Projected to exceed
    UNUSUAL_SPENDING = "unusual_spending"     # Spike in spending
    BUDGET_UNDERUTILIZATION = "budget_underutilization"  # Too little spending


class BudgetStatus(Enum):
    """Budget status indicators."""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OVER_BUDGET = "over_budget"
    SIGNIFICANTLY_OVER = "significantly_over"
    UNDER_UTILIZED = "under_utilized"


@dataclass
class BudgetAllocation:
    """Individual budget allocation."""
    allocation_id: str
    name: str
    budget_type: BudgetType
    
    # Budget details
    allocated_amount: Decimal
    period_start: datetime
    period_end: datetime
    budget_period: BudgetPeriod
    
    # Scope
    user_ids: Set[str] = field(default_factory=set)
    matter_ids: Set[str] = field(default_factory=set)
    client_ids: Set[str] = field(default_factory=set)
    resource_types: Set[ResourceType] = field(default_factory=set)
    cost_categories: Set[CostCategory] = field(default_factory=set)
    
    # Current status
    spent_amount: Decimal = Decimal('0.00')
    committed_amount: Decimal = Decimal('0.00')  # Pending/reserved amounts
    remaining_amount: Decimal = field(init=False)
    
    # Performance tracking
    utilization_rate: float = 0.0  # 0-1 scale
    burn_rate: Decimal = Decimal('0.00')  # Spending per day
    projected_total: Decimal = Decimal('0.00')
    
    # Configuration
    alert_thresholds: List[float] = field(default_factory=lambda: [0.75, 0.90])
    enforce_hard_limit: bool = False
    allow_overrun_percentage: float = 0.1  # 10% default
    
    # Status
    status: BudgetStatus = BudgetStatus.ON_TRACK
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.remaining_amount = self.allocated_amount - self.spent_amount - self.committed_amount


@dataclass
class BudgetAlert:
    """Budget alert notification."""
    alert_id: str
    allocation_id: str
    alert_type: AlertType
    severity: str  # "low", "medium", "high", "critical"
    
    # Alert details
    title: str
    message: str
    current_amount: Decimal
    threshold_amount: Optional[Decimal] = None
    projected_amount: Optional[Decimal] = None
    
    # Timing
    alert_date: datetime = field(default_factory=datetime.now)
    period_remaining_days: int = 0
    
    # Actions
    recommended_actions: List[str] = field(default_factory=list)
    requires_approval: bool = False
    
    # Status
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_date: Optional[datetime] = None


@dataclass
class SpendingForecast:
    """Spending forecast for budget planning."""
    allocation_id: str
    forecast_date: datetime
    
    # Forecast data
    projected_total: Decimal
    confidence_level: float  # 0-1 scale
    projection_method: str  # "linear", "seasonal", "ml"
    
    # Trend analysis
    spending_trend: str  # "increasing", "decreasing", "stable", "volatile"
    trend_strength: float  # 0-1 scale
    
    # Risk factors
    risk_factors: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0-1 scale
    
    # Scenario analysis
    best_case_scenario: Decimal = Decimal('0.00')
    worst_case_scenario: Decimal = Decimal('0.00')
    most_likely_scenario: Decimal = Decimal('0.00')


@dataclass
class BudgetReport:
    """Comprehensive budget performance report."""
    report_id: str
    report_date: datetime
    period_start: datetime
    period_end: datetime
    
    # Overall performance
    total_allocated: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_utilization: float
    
    # Budget breakdowns
    allocations_summary: List[Dict[str, Any]] = field(default_factory=list)
    spending_by_category: Dict[CostCategory, Decimal] = field(default_factory=dict)
    spending_by_resource: Dict[ResourceType, Decimal] = field(default_factory=dict)
    spending_by_user: Dict[str, Decimal] = field(default_factory=dict)
    
    # Performance metrics
    budgets_on_track: int = 0
    budgets_at_risk: int = 0
    budgets_over: int = 0
    average_utilization: float = 0.0
    
    # Alerts and issues
    active_alerts: List[BudgetAlert] = field(default_factory=list)
    total_overruns: Decimal = Decimal('0.00')
    
    # Trends and insights
    spending_trends: Dict[str, str] = field(default_factory=dict)
    cost_efficiency_metrics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class BudgetManager:
    """
    Comprehensive budget management system for legal research costs.
    
    Provides budget allocation, monitoring, forecasting, and enforcement
    capabilities with real-time alerts and detailed reporting.
    """
    
    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        self.logger = logging.getLogger(__name__)
        
        # Budget storage
        self.budget_allocations: Dict[str, BudgetAllocation] = {}
        self.budget_alerts: Dict[str, List[BudgetAlert]] = defaultdict(list)
        
        # Configuration
        self.default_alert_thresholds = [0.75, 0.90]  # 75% and 90%
        self.forecast_horizon_days = 90
        self.alert_cooldown_hours = 24  # Prevent spam alerts
        
        # Historical data for forecasting
        self.spending_history: Dict[str, List[Tuple[datetime, Decimal]]] = defaultdict(list)
    
    async def create_budget_allocation(self, 
                                     name: str,
                                     budget_type: BudgetType,
                                     allocated_amount: Decimal,
                                     period_start: datetime,
                                     period_end: datetime,
                                     **kwargs) -> BudgetAllocation:
        """
        Create a new budget allocation.
        
        Args:
            name: Budget allocation name
            budget_type: Type of budget
            allocated_amount: Budget amount
            period_start: Budget period start
            period_end: Budget period end
            **kwargs: Additional configuration options
            
        Returns:
            Created BudgetAllocation
        """
        
        allocation_id = str(uuid.uuid4())
        
        # Determine budget period
        period_duration = (period_end - period_start).days
        if period_duration <= 35:  # ~1 month
            budget_period = BudgetPeriod.MONTHLY
        elif period_duration <= 100:  # ~3 months
            budget_period = BudgetPeriod.QUARTERLY
        elif period_duration <= 370:  # ~1 year
            budget_period = BudgetPeriod.ANNUALLY
        else:
            budget_period = BudgetPeriod.CUSTOM
        
        allocation = BudgetAllocation(
            allocation_id=allocation_id,
            name=name,
            budget_type=budget_type,
            allocated_amount=allocated_amount,
            period_start=period_start,
            period_end=period_end,
            budget_period=budget_period,
            user_ids=set(kwargs.get('user_ids', [])),
            matter_ids=set(kwargs.get('matter_ids', [])),
            client_ids=set(kwargs.get('client_ids', [])),
            resource_types=set(kwargs.get('resource_types', [])),
            cost_categories=set(kwargs.get('cost_categories', [])),
            alert_thresholds=kwargs.get('alert_thresholds', self.default_alert_thresholds.copy()),
            enforce_hard_limit=kwargs.get('enforce_hard_limit', False),
            allow_overrun_percentage=kwargs.get('allow_overrun_percentage', 0.1)
        )
        
        self.budget_allocations[allocation_id] = allocation
        
        self.logger.info(f"Created budget allocation '{name}' with ${allocated_amount}")
        
        return allocation
    
    async def update_budget_spending(self, cost_event: CostEvent):
        """Update budget spending based on a cost event."""
        
        # Find applicable budget allocations
        applicable_allocations = await self._find_applicable_allocations(cost_event)
        
        for allocation in applicable_allocations:
            # Update spent amount
            allocation.spent_amount += cost_event.total_cost
            allocation.remaining_amount = allocation.allocated_amount - allocation.spent_amount - allocation.committed_amount
            
            # Update performance metrics
            await self._update_allocation_metrics(allocation)
            
            # Check for alerts
            await self._check_budget_alerts(allocation)
            
            # Record spending history
            self.spending_history[allocation.allocation_id].append(
                (cost_event.timestamp, cost_event.total_cost)
            )
            
            allocation.last_updated = datetime.now()
    
    async def _find_applicable_allocations(self, cost_event: CostEvent) -> List[BudgetAllocation]:
        """Find budget allocations that apply to a cost event."""
        
        applicable = []
        
        for allocation in self.budget_allocations.values():
            # Check if event is within budget period
            if not (allocation.period_start <= cost_event.timestamp <= allocation.period_end):
                continue
            
            # Check scope criteria
            is_applicable = True
            
            # User scope
            if allocation.user_ids and cost_event.user_id not in allocation.user_ids:
                is_applicable = False
            
            # Matter scope
            if allocation.matter_ids and cost_event.matter_id not in allocation.matter_ids:
                is_applicable = False
            
            # Client scope
            if allocation.client_ids and cost_event.client_id not in allocation.client_ids:
                is_applicable = False
            
            # Resource scope
            if allocation.resource_types and cost_event.resource_type not in allocation.resource_types:
                is_applicable = False
            
            # Category scope
            if allocation.cost_categories and cost_event.cost_category not in allocation.cost_categories:
                is_applicable = False
            
            if is_applicable:
                applicable.append(allocation)
        
        return applicable
    
    async def _update_allocation_metrics(self, allocation: BudgetAllocation):
        """Update performance metrics for a budget allocation."""
        
        # Calculate utilization rate
        if allocation.allocated_amount > 0:
            allocation.utilization_rate = float(allocation.spent_amount / allocation.allocated_amount)
        
        # Calculate burn rate (spending per day)
        period_elapsed = (datetime.now() - allocation.period_start).days
        if period_elapsed > 0:
            allocation.burn_rate = allocation.spent_amount / Decimal(str(period_elapsed))
        
        # Calculate projection
        period_total = (allocation.period_end - allocation.period_start).days
        if period_elapsed > 0 and period_total > period_elapsed:
            remaining_days = period_total - period_elapsed
            allocation.projected_total = allocation.spent_amount + (allocation.burn_rate * Decimal(str(remaining_days)))
        else:
            allocation.projected_total = allocation.spent_amount
        
        # Update status
        allocation.status = await self._calculate_budget_status(allocation)
    
    async def _calculate_budget_status(self, allocation: BudgetAllocation) -> BudgetStatus:
        """Calculate the current status of a budget allocation."""
        
        utilization = allocation.utilization_rate
        
        # Check for over-budget conditions
        if utilization >= 1.2:  # 20% over budget
            return BudgetStatus.SIGNIFICANTLY_OVER
        elif utilization >= 1.0:
            return BudgetStatus.OVER_BUDGET
        elif utilization >= 0.9:  # 90% utilized
            return BudgetStatus.AT_RISK
        elif utilization < 0.3:  # Less than 30% utilized
            # Check if we're near end of period
            period_total = (allocation.period_end - allocation.period_start).days
            period_elapsed = (datetime.now() - allocation.period_start).days
            period_progress = period_elapsed / period_total if period_total > 0 else 1
            
            if period_progress > 0.75 and utilization < 0.5:  # 75% through period, <50% spent
                return BudgetStatus.UNDER_UTILIZED
        
        return BudgetStatus.ON_TRACK
    
    async def _check_budget_alerts(self, allocation: BudgetAllocation):
        """Check if budget alerts should be generated."""
        
        current_time = datetime.now()
        
        # Check recent alerts to avoid spam
        recent_alerts = [
            alert for alert in self.budget_alerts[allocation.allocation_id]
            if (current_time - alert.alert_date).total_seconds() < self.alert_cooldown_hours * 3600
        ]
        
        # Threshold alerts
        for threshold in allocation.alert_thresholds:
            if (allocation.utilization_rate >= threshold and 
                not any(alert.alert_type == AlertType.THRESHOLD_WARNING and 
                       abs(float(alert.threshold_amount or 0) / float(allocation.allocated_amount) - threshold) < 0.05
                       for alert in recent_alerts)):
                
                await self._generate_threshold_alert(allocation, threshold)
        
        # Over-budget alert
        if (allocation.utilization_rate >= 1.0 and
            not any(alert.alert_type == AlertType.BUDGET_EXCEEDED for alert in recent_alerts)):
            
            await self._generate_over_budget_alert(allocation)
        
        # Projection alert
        projected_overrun = allocation.projected_total - allocation.allocated_amount
        if (projected_overrun > 0 and
            not any(alert.alert_type == AlertType.OVERSPEND_PROJECTION for alert in recent_alerts)):
            
            await self._generate_projection_alert(allocation, projected_overrun)
        
        # Under-utilization alert
        if (allocation.status == BudgetStatus.UNDER_UTILIZED and
            not any(alert.alert_type == AlertType.BUDGET_UNDERUTILIZATION for alert in recent_alerts)):
            
            await self._generate_underutilization_alert(allocation)
    
    async def _generate_threshold_alert(self, allocation: BudgetAllocation, threshold: float):
        """Generate threshold warning alert."""
        
        threshold_amount = allocation.allocated_amount * Decimal(str(threshold))
        
        alert = BudgetAlert(
            alert_id=str(uuid.uuid4()),
            allocation_id=allocation.allocation_id,
            alert_type=AlertType.THRESHOLD_WARNING,
            severity="medium" if threshold < 0.9 else "high",
            title=f"Budget Alert: {threshold*100:.0f}% Threshold Reached",
            message=f"Budget '{allocation.name}' has reached {threshold*100:.0f}% utilization (${allocation.spent_amount} of ${allocation.allocated_amount})",
            current_amount=allocation.spent_amount,
            threshold_amount=threshold_amount,
            period_remaining_days=(allocation.period_end - datetime.now()).days,
            recommended_actions=[
                "Review recent spending patterns",
                "Consider reducing non-essential research",
                "Monitor daily spending more closely"
            ]
        )
        
        self.budget_alerts[allocation.allocation_id].append(alert)
        self.logger.warning(f"Generated threshold alert for budget {allocation.name}")
    
    async def _generate_over_budget_alert(self, allocation: BudgetAllocation):
        """Generate over-budget alert."""
        
        overrun_amount = allocation.spent_amount - allocation.allocated_amount
        
        alert = BudgetAlert(
            alert_id=str(uuid.uuid4()),
            allocation_id=allocation.allocation_id,
            alert_type=AlertType.BUDGET_EXCEEDED,
            severity="high",
            title=f"Budget Exceeded: {allocation.name}",
            message=f"Budget '{allocation.name}' has been exceeded by ${overrun_amount} (${allocation.spent_amount} vs ${allocation.allocated_amount})",
            current_amount=allocation.spent_amount,
            threshold_amount=allocation.allocated_amount,
            period_remaining_days=(allocation.period_end - datetime.now()).days,
            recommended_actions=[
                "Stop non-essential spending immediately",
                "Review and approve all future expenses",
                "Analyze overspend causes",
                "Consider budget reallocation if justified"
            ],
            requires_approval=True
        )
        
        self.budget_alerts[allocation.allocation_id].append(alert)
        self.logger.error(f"Generated over-budget alert for {allocation.name}")
    
    async def _generate_projection_alert(self, allocation: BudgetAllocation, projected_overrun: Decimal):
        """Generate projection alert for anticipated overspend."""
        
        alert = BudgetAlert(
            alert_id=str(uuid.uuid4()),
            allocation_id=allocation.allocation_id,
            alert_type=AlertType.OVERSPEND_PROJECTION,
            severity="high",
            title=f"Projected Overspend: {allocation.name}",
            message=f"Budget '{allocation.name}' is projected to exceed by ${projected_overrun} (projected total: ${allocation.projected_total})",
            current_amount=allocation.spent_amount,
            projected_amount=allocation.projected_total,
            period_remaining_days=(allocation.period_end - datetime.now()).days,
            recommended_actions=[
                "Reduce spending rate to stay within budget",
                "Prioritize essential research only",
                "Consider requesting budget increase",
                "Review spending patterns for optimization"
            ]
        )
        
        self.budget_alerts[allocation.allocation_id].append(alert)
        self.logger.warning(f"Generated projection alert for {allocation.name}")
    
    async def _generate_underutilization_alert(self, allocation: BudgetAllocation):
        """Generate under-utilization alert."""
        
        alert = BudgetAlert(
            alert_id=str(uuid.uuid4()),
            allocation_id=allocation.allocation_id,
            alert_type=AlertType.BUDGET_UNDERUTILIZATION,
            severity="low",
            title=f"Budget Under-Utilized: {allocation.name}",
            message=f"Budget '{allocation.name}' is under-utilized at {allocation.utilization_rate*100:.1f}% (${allocation.spent_amount} of ${allocation.allocated_amount})",
            current_amount=allocation.spent_amount,
            period_remaining_days=(allocation.period_end - datetime.now()).days,
            recommended_actions=[
                "Consider reallocating unused budget",
                "Evaluate if budget was over-estimated",
                "Increase research activities if needed",
                "Plan for remaining budget utilization"
            ]
        )
        
        self.budget_alerts[allocation.allocation_id].append(alert)
        self.logger.info(f"Generated under-utilization alert for {allocation.name}")
    
    async def check_spending_authorization(self, 
                                         cost_event: CostEvent) -> Tuple[bool, List[str]]:
        """
        Check if a spending request is authorized within budget limits.
        
        Args:
            cost_event: Proposed cost event
            
        Returns:
            Tuple of (authorized, reasons)
        """
        
        applicable_allocations = await self._find_applicable_allocations(cost_event)
        
        if not applicable_allocations:
            return True, ["No specific budget constraints apply"]
        
        reasons = []
        all_authorized = True
        
        for allocation in applicable_allocations:
            # Check hard limits
            if allocation.enforce_hard_limit:
                remaining = allocation.remaining_amount
                if cost_event.total_cost > remaining:
                    all_authorized = False
                    reasons.append(f"Exceeds remaining budget for '{allocation.name}': ${remaining} remaining")
                    continue
            
            # Check soft limits (overrun percentage)
            max_allowed_spend = allocation.allocated_amount * Decimal(str(1 + allocation.allow_overrun_percentage))
            potential_total = allocation.spent_amount + cost_event.total_cost
            
            if potential_total > max_allowed_spend:
                all_authorized = False
                reasons.append(f"Would exceed allowed overrun for '{allocation.name}': {allocation.allow_overrun_percentage*100}%")
        
        if all_authorized:
            reasons.append("Authorized within all applicable budget limits")
        
        return all_authorized, reasons
    
    async def reserve_budget(self, 
                           allocation_id: str, 
                           amount: Decimal,
                           description: str = "") -> bool:
        """
        Reserve budget amount for planned spending.
        
        Args:
            allocation_id: Budget allocation ID
            amount: Amount to reserve
            description: Description of reservation
            
        Returns:
            True if reservation successful
        """
        
        if allocation_id not in self.budget_allocations:
            return False
        
        allocation = self.budget_allocations[allocation_id]
        
        # Check if reservation is possible
        if allocation.remaining_amount >= amount:
            allocation.committed_amount += amount
            allocation.remaining_amount -= amount
            
            self.logger.info(f"Reserved ${amount} from budget '{allocation.name}': {description}")
            return True
        
        return False
    
    async def release_budget_reservation(self, 
                                       allocation_id: str, 
                                       amount: Decimal) -> bool:
        """Release a budget reservation."""
        
        if allocation_id not in self.budget_allocations:
            return False
        
        allocation = self.budget_allocations[allocation_id]
        
        # Release reservation
        release_amount = min(amount, allocation.committed_amount)
        allocation.committed_amount -= release_amount
        allocation.remaining_amount += release_amount
        
        self.logger.info(f"Released ${release_amount} reservation from budget '{allocation.name}'")
        return True
    
    async def generate_spending_forecast(self, 
                                       allocation_id: str,
                                       method: str = "linear") -> SpendingForecast:
        """Generate spending forecast for a budget allocation."""
        
        allocation = self.budget_allocations[allocation_id]
        spending_data = self.spending_history[allocation_id]
        
        if len(spending_data) < 7:  # Need at least a week of data
            # Simple linear projection based on current burn rate
            projected_total = allocation.projected_total
            confidence = 0.3  # Low confidence with little data
        else:
            if method == "linear":
                projected_total, confidence = await self._linear_forecast(allocation, spending_data)
            elif method == "seasonal":
                projected_total, confidence = await self._seasonal_forecast(allocation, spending_data)
            else:  # ml method would go here
                projected_total, confidence = await self._linear_forecast(allocation, spending_data)
        
        # Analyze trend
        trend, trend_strength = await self._analyze_spending_trend(spending_data)
        
        # Identify risk factors
        risk_factors = await self._identify_forecast_risks(allocation, spending_data)
        risk_score = len(risk_factors) * 0.2  # Simple risk scoring
        
        # Scenario analysis
        best_case = projected_total * Decimal('0.85')  # 15% under projection
        worst_case = projected_total * Decimal('1.25')  # 25% over projection
        
        forecast = SpendingForecast(
            allocation_id=allocation_id,
            forecast_date=datetime.now(),
            projected_total=projected_total,
            confidence_level=confidence,
            projection_method=method,
            spending_trend=trend,
            trend_strength=trend_strength,
            risk_factors=risk_factors,
            risk_score=min(1.0, risk_score),
            best_case_scenario=best_case,
            worst_case_scenario=worst_case,
            most_likely_scenario=projected_total
        )
        
        return forecast
    
    async def _linear_forecast(self, 
                             allocation: BudgetAllocation,
                             spending_data: List[Tuple[datetime, Decimal]]) -> Tuple[Decimal, float]:
        """Generate linear forecast based on historical spending."""
        
        if not spending_data:
            return allocation.projected_total, 0.3
        
        # Calculate daily spending rates
        daily_spending = defaultdict(Decimal)
        for timestamp, amount in spending_data:
            date_key = timestamp.date()
            daily_spending[date_key] += amount
        
        # Calculate average daily spending (last 30 days)
        recent_data = [
            (date_key, amount) for date_key, amount in daily_spending.items()
            if (datetime.now().date() - date_key).days <= 30
        ]
        
        if not recent_data:
            return allocation.projected_total, 0.3
        
        avg_daily_spend = sum(amount for _, amount in recent_data) / len(recent_data)
        
        # Project to end of period
        remaining_days = (allocation.period_end - datetime.now()).days
        projected_additional = avg_daily_spend * remaining_days
        projected_total = allocation.spent_amount + projected_additional
        
        # Calculate confidence based on data consistency
        if len(recent_data) >= 14:  # At least 2 weeks of data
            daily_amounts = [amount for _, amount in recent_data]
            avg_amount = sum(daily_amounts) / len(daily_amounts)
            variance = sum((amount - avg_amount) ** 2 for amount in daily_amounts) / len(daily_amounts)
            coefficient_of_variation = float(variance ** 0.5 / avg_amount) if avg_amount > 0 else 1.0
            
            confidence = max(0.3, min(0.9, 1.0 - coefficient_of_variation))
        else:
            confidence = 0.5
        
        return projected_total, confidence
    
    async def _seasonal_forecast(self, 
                               allocation: BudgetAllocation,
                               spending_data: List[Tuple[datetime, Decimal]]) -> Tuple[Decimal, float]:
        """Generate seasonal forecast (simplified implementation)."""
        
        # For now, just apply seasonal adjustment to linear forecast
        projected_total, base_confidence = await self._linear_forecast(allocation, spending_data)
        
        # Simple seasonal adjustments (would be more sophisticated in practice)
        current_month = datetime.now().month
        
        seasonal_multipliers = {
            1: 0.9,   # January - post-holiday reduction
            2: 1.0,   # February - normal
            3: 1.1,   # March - quarter end push
            4: 0.95,  # April - start of Q2
            5: 1.0,   # May - normal
            6: 1.1,   # June - quarter end
            7: 0.9,   # July - summer slowdown
            8: 0.9,   # August - vacation season
            9: 1.1,   # September - back to work
            10: 1.0,  # October - normal
            11: 1.0,  # November - normal
            12: 1.2   # December - year-end push
        }
        
        seasonal_adjustment = seasonal_multipliers.get(current_month, 1.0)
        seasonal_projection = projected_total * Decimal(str(seasonal_adjustment))
        
        # Confidence is slightly lower for seasonal forecasts
        confidence = base_confidence * 0.9
        
        return seasonal_projection, confidence
    
    async def _analyze_spending_trend(self, spending_data: List[Tuple[datetime, Decimal]]) -> Tuple[str, float]:
        """Analyze spending trend from historical data."""
        
        if len(spending_data) < 14:  # Need at least 2 weeks
            return "stable", 0.0
        
        # Group by week and calculate trend
        weekly_spending = defaultdict(Decimal)
        for timestamp, amount in spending_data:
            week_start = timestamp.date() - timedelta(days=timestamp.weekday())
            weekly_spending[week_start] += amount
        
        if len(weekly_spending) < 3:
            return "stable", 0.0
        
        # Simple linear regression on weekly amounts
        weeks = sorted(weekly_spending.keys())
        amounts = [float(weekly_spending[week]) for week in weeks]
        
        n = len(amounts)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = sum(amounts) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, amounts))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return "stable", 0.0
        
        slope = numerator / denominator
        
        # Classify trend
        if slope > y_mean * 0.1:  # More than 10% of average weekly spending
            return "increasing", min(1.0, abs(slope) / y_mean)
        elif slope < -y_mean * 0.1:
            return "decreasing", min(1.0, abs(slope) / y_mean)
        else:
            # Check for volatility
            variance = sum((amount - y_mean) ** 2 for amount in amounts) / n
            std_dev = variance ** 0.5
            
            if std_dev > y_mean * 0.3:  # High variance
                return "volatile", min(1.0, std_dev / y_mean)
            else:
                return "stable", 0.0
    
    async def _identify_forecast_risks(self, 
                                     allocation: BudgetAllocation,
                                     spending_data: List[Tuple[datetime, Decimal]]) -> List[str]:
        """Identify risk factors that could affect forecast accuracy."""
        
        risks = []
        
        # High volatility risk
        if len(spending_data) >= 7:
            amounts = [float(amount) for _, amount in spending_data[-7:]]  # Last week
            avg_amount = sum(amounts) / len(amounts)
            variance = sum((amount - avg_amount) ** 2 for amount in amounts) / len(amounts)
            coefficient_of_variation = (variance ** 0.5) / avg_amount if avg_amount > 0 else 0
            
            if coefficient_of_variation > 0.5:
                risks.append("High spending volatility detected")
        
        # Accelerating spending risk
        trend, strength = await self._analyze_spending_trend(spending_data)
        if trend == "increasing" and strength > 0.3:
            risks.append("Accelerating spending trend")
        
        # Late period risk
        period_total = (allocation.period_end - allocation.period_start).days
        period_elapsed = (datetime.now() - allocation.period_start).days
        period_progress = period_elapsed / period_total if period_total > 0 else 1
        
        if period_progress > 0.75 and allocation.utilization_rate < 0.5:
            risks.append("Low utilization late in period may trigger catch-up spending")
        
        # Approaching limits risk
        if allocation.utilization_rate > 0.8:
            risks.append("Approaching budget limits may affect spending patterns")
        
        return risks
    
    async def generate_budget_report(self, 
                                   period_start: Optional[datetime] = None,
                                   period_end: Optional[datetime] = None) -> BudgetReport:
        """Generate comprehensive budget performance report."""
        
        if not period_start:
            period_start = datetime.now().replace(day=1)  # Start of current month
        if not period_end:
            period_end = datetime.now()
        
        report = BudgetReport(
            report_id=str(uuid.uuid4()),
            report_date=datetime.now(),
            period_start=period_start,
            period_end=period_end
        )
        
        # Analyze allocations within period
        relevant_allocations = [
            allocation for allocation in self.budget_allocations.values()
            if (allocation.period_start <= period_end and allocation.period_end >= period_start)
        ]
        
        # Calculate overall metrics
        report.total_allocated = sum(alloc.allocated_amount for alloc in relevant_allocations)
        report.total_spent = sum(alloc.spent_amount for alloc in relevant_allocations)
        report.total_remaining = sum(alloc.remaining_amount for alloc in relevant_allocations)
        
        if report.total_allocated > 0:
            report.overall_utilization = float(report.total_spent / report.total_allocated)
        
        # Status breakdown
        status_counts = defaultdict(int)
        utilization_rates = []
        
        for allocation in relevant_allocations:
            status_counts[allocation.status] += 1
            utilization_rates.append(allocation.utilization_rate)
            
            # Add to allocation summary
            report.allocations_summary.append({
                'name': allocation.name,
                'type': allocation.budget_type.value,
                'allocated': float(allocation.allocated_amount),
                'spent': float(allocation.spent_amount),
                'remaining': float(allocation.remaining_amount),
                'utilization': allocation.utilization_rate,
                'status': allocation.status.value
            })
        
        report.budgets_on_track = status_counts[BudgetStatus.ON_TRACK]
        report.budgets_at_risk = status_counts[BudgetStatus.AT_RISK]
        report.budgets_over = status_counts[BudgetStatus.OVER_BUDGET] + status_counts[BudgetStatus.SIGNIFICANTLY_OVER]
        
        if utilization_rates:
            report.average_utilization = sum(utilization_rates) / len(utilization_rates)
        
        # Get spending breakdowns from cost tracker
        cost_summary = await self.cost_tracker.get_cost_summary(period_start, period_end)
        report.spending_by_category = cost_summary.costs_by_category
        report.spending_by_resource = cost_summary.costs_by_resource
        report.spending_by_user = cost_summary.costs_by_user
        
        # Collect active alerts
        for allocation_alerts in self.budget_alerts.values():
            for alert in allocation_alerts:
                if not alert.acknowledged and alert.alert_date >= period_start:
                    report.active_alerts.append(alert)
        
        # Calculate overruns
        for allocation in relevant_allocations:
            if allocation.spent_amount > allocation.allocated_amount:
                overrun = allocation.spent_amount - allocation.allocated_amount
                report.total_overruns += overrun
        
        # Generate trends and recommendations
        report.spending_trends = await self._analyze_system_spending_trends(relevant_allocations)
        report.recommendations = await self._generate_budget_recommendations(relevant_allocations, report)
        
        return report
    
    async def _analyze_system_spending_trends(self, allocations: List[BudgetAllocation]) -> Dict[str, str]:
        """Analyze system-wide spending trends."""
        
        trends = {}
        
        # Overall spending trend
        increasing_count = 0
        decreasing_count = 0
        stable_count = 0
        
        for allocation in allocations:
            spending_data = self.spending_history[allocation.allocation_id]
            trend, _ = await self._analyze_spending_trend(spending_data)
            
            if trend == "increasing":
                increasing_count += 1
            elif trend == "decreasing":
                decreasing_count += 1
            else:
                stable_count += 1
        
        total_allocations = len(allocations)
        if total_allocations > 0:
            if increasing_count / total_allocations > 0.6:
                trends['overall'] = "increasing"
            elif decreasing_count / total_allocations > 0.6:
                trends['overall'] = "decreasing"
            else:
                trends['overall'] = "stable"
        
        # Budget utilization trend
        high_util_count = len([a for a in allocations if a.utilization_rate > 0.8])
        low_util_count = len([a for a in allocations if a.utilization_rate < 0.3])
        
        if high_util_count > low_util_count:
            trends['utilization'] = "high"
        elif low_util_count > high_util_count:
            trends['utilization'] = "low"
        else:
            trends['utilization'] = "balanced"
        
        return trends
    
    async def _generate_budget_recommendations(self, 
                                             allocations: List[BudgetAllocation],
                                             report: BudgetReport) -> List[str]:
        """Generate budget management recommendations."""
        
        recommendations = []
        
        # High-level recommendations based on overall performance
        if report.overall_utilization < 0.5:
            recommendations.append("Overall budget utilization is low - consider reallocating unused funds")
        elif report.overall_utilization > 1.1:
            recommendations.append("System-wide overspending detected - review all budget controls")
        
        if report.budgets_over > 0:
            recommendations.append(f"{report.budgets_over} budgets are over limit - implement stricter controls")
        
        # Alert-based recommendations
        critical_alerts = [a for a in report.active_alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append(f"{len(critical_alerts)} critical budget alerts require immediate attention")
        
        # Specific allocation recommendations
        overallocated = [a for a in allocations if a.utilization_rate > 1.2]
        if overallocated:
            recommendations.append(f"Review {len(overallocated)} significantly over-allocated budgets")
        
        underallocated = [a for a in allocations if a.utilization_rate < 0.3]
        if len(underallocated) > 2:
            recommendations.append(f"{len(underallocated)} budgets are under-utilized - consider reallocation")
        
        # Seasonal recommendations
        current_month = datetime.now().month
        if current_month in [3, 6, 9, 12]:  # Quarter ends
            recommendations.append("Quarter-end period - monitor for spending spikes")
        
        return recommendations
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a budget alert."""
        
        for alerts in self.budget_alerts.values():
            for alert in alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_by = acknowledged_by
                    alert.acknowledged_date = datetime.now()
                    
                    self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                    return True
        
        return False
    
    async def get_budget_summary(self, allocation_id: str) -> Dict[str, Any]:
        """Get summary information for a specific budget allocation."""
        
        if allocation_id not in self.budget_allocations:
            return {}
        
        allocation = self.budget_allocations[allocation_id]
        
        # Generate forecast
        forecast = await self.generate_spending_forecast(allocation_id)
        
        # Get recent alerts
        recent_alerts = [
            alert for alert in self.budget_alerts[allocation_id]
            if (datetime.now() - alert.alert_date).total_seconds() < 7 * 24 * 3600  # Last 7 days
        ]
        
        summary = {
            'allocation_id': allocation_id,
            'name': allocation.name,
            'type': allocation.budget_type.value,
            'period': {
                'start': allocation.period_start.isoformat(),
                'end': allocation.period_end.isoformat(),
                'days_remaining': (allocation.period_end - datetime.now()).days
            },
            'budget': {
                'allocated': float(allocation.allocated_amount),
                'spent': float(allocation.spent_amount),
                'committed': float(allocation.committed_amount),
                'remaining': float(allocation.remaining_amount),
                'utilization_rate': allocation.utilization_rate
            },
            'performance': {
                'status': allocation.status.value,
                'burn_rate': float(allocation.burn_rate),
                'projected_total': float(forecast.projected_total),
                'forecast_confidence': forecast.confidence_level
            },
            'alerts': {
                'total_active': len([a for a in recent_alerts if not a.acknowledged]),
                'recent_count': len(recent_alerts),
                'highest_severity': max([a.severity for a in recent_alerts], default="none")
            }
        }
        
        return summary


# Helper functions
async def create_monthly_budget(name: str, amount: Decimal, **kwargs) -> BudgetAllocation:
    """Helper function to create monthly budget."""
    cost_tracker = CostTracker()
    budget_manager = BudgetManager(cost_tracker)
    
    now = datetime.now()
    period_start = datetime(now.year, now.month, 1)
    
    # Calculate last day of month
    last_day = calendar.monthrange(now.year, now.month)[1]
    period_end = datetime(now.year, now.month, last_day, 23, 59, 59)
    
    return await budget_manager.create_budget_allocation(
        name, BudgetType.TOTAL_RESEARCH, amount, period_start, period_end, **kwargs
    )

async def check_budget_status() -> Dict[str, Any]:
    """Helper function to check overall budget status."""
    cost_tracker = CostTracker()
    budget_manager = BudgetManager(cost_tracker)
    
    report = await budget_manager.generate_budget_report()
    
    return {
        'total_allocated': float(report.total_allocated),
        'total_spent': float(report.total_spent),
        'overall_utilization': report.overall_utilization,
        'budgets_over': report.budgets_over,
        'active_alerts': len(report.active_alerts)
    }