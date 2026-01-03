"""
Case Monitoring Analytics

Provides analytics and insights for case monitoring including
trend analysis, cost optimization, performance metrics, and
predictive monitoring recommendations.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import statistics
from collections import defaultdict

from ..shared.utils.cache_manager import cache_manager
from .models import (
    MonitoredCase, ChangeDetection, NotificationEvent,
    ChangeType, AlertSeverity, MonitorStatus, MonitoringFrequency
)


# Configure logging
logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction for analytics"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class MonitoringTrend:
    """Monitoring trend analysis"""
    metric_name: str
    time_period: str
    direction: TrendDirection
    change_percentage: float
    current_value: float
    previous_value: float
    confidence: float  # 0.0 to 1.0
    data_points: List[Tuple[datetime, float]] = field(default_factory=list)


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation"""
    recommendation_id: str
    title: str
    description: str
    potential_savings_dollars: float
    implementation_effort: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    affected_monitors: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)


@dataclass
class MonitoringInsight:
    """Monitoring insight or finding"""
    insight_id: str
    category: str  # "performance", "cost", "activity", "anomaly"
    title: str
    description: str
    severity: AlertSeverity
    actionable: bool
    recommendations: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringReport:
    """Comprehensive monitoring analytics report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    trends: List[MonitoringTrend] = field(default_factory=list)
    cost_analysis: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    insights: List[MonitoringInsight] = field(default_factory=list)
    recommendations: List[CostOptimizationRecommendation] = field(default_factory=list)
    top_active_cases: List[Dict[str, Any]] = field(default_factory=list)
    change_patterns: Dict[str, Any] = field(default_factory=dict)


class MonitoringAnalytics:
    """Analytics engine for case monitoring"""
    
    def __init__(self):
        # Historical data storage (in production, use proper database)
        self.historical_metrics: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.change_history: List[ChangeDetection] = []
        self.notification_history: List[NotificationEvent] = []
        
        # Analysis cache
        self.cached_insights: Dict[str, Any] = {}
        self.last_analysis_time: Optional[datetime] = None
        
        logger.info("Monitoring Analytics initialized")
    
    async def record_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """Record a metric for analytics"""
        
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            self.historical_metrics[metric_name].append((timestamp, value))
            
            # Keep only last 90 days of data
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            self.historical_metrics[metric_name] = [
                (ts, val) for ts, val in self.historical_metrics[metric_name]
                if ts > cutoff_date
            ]
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {str(e)}")
    
    async def analyze_trends(
        self,
        metric_name: str,
        days_back: int = 30
    ) -> Optional[MonitoringTrend]:
        """Analyze trends for a specific metric"""
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Get relevant data points
            metric_data = [
                (ts, val) for ts, val in self.historical_metrics.get(metric_name, [])
                if ts > cutoff_date
            ]
            
            if len(metric_data) < 5:  # Need minimum data points
                return None
            
            # Sort by timestamp
            metric_data.sort(key=lambda x: x[0])
            
            # Calculate trend
            values = [val for _, val in metric_data]
            
            # Simple linear trend calculation
            n = len(values)
            if n < 2:
                return None
            
            # Split into two halves for comparison
            half_point = n // 2
            first_half_avg = statistics.mean(values[:half_point]) if half_point > 0 else 0
            second_half_avg = statistics.mean(values[half_point:]) if half_point < n else 0
            
            # Calculate change percentage
            if first_half_avg > 0:
                change_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            else:
                change_pct = 0
            
            # Determine trend direction
            if abs(change_pct) < 5:
                direction = TrendDirection.STABLE
            elif change_pct > 0:
                direction = TrendDirection.INCREASING
            else:
                direction = TrendDirection.DECREASING
            
            # Calculate volatility (standard deviation)
            volatility = statistics.stdev(values) if len(values) > 1 else 0
            avg_value = statistics.mean(values)
            
            if avg_value > 0 and (volatility / avg_value) > 0.5:  # High relative volatility
                direction = TrendDirection.VOLATILE
            
            # Calculate confidence based on data points and consistency
            confidence = min(1.0, len(metric_data) / 30)  # More data = higher confidence
            
            return MonitoringTrend(
                metric_name=metric_name,
                time_period=f"{days_back} days",
                direction=direction,
                change_percentage=change_pct,
                current_value=values[-1],
                previous_value=values[0],
                confidence=confidence,
                data_points=metric_data
            )
            
        except Exception as e:
            logger.error(f"Trend analysis failed for {metric_name}: {str(e)}")
            return None
    
    async def analyze_cost_optimization(
        self,
        monitored_cases: Dict[str, MonitoredCase]
    ) -> List[CostOptimizationRecommendation]:
        """Generate cost optimization recommendations"""
        
        try:
            recommendations = []
            
            # Analyze monitoring frequencies
            freq_optimization = await self._analyze_frequency_optimization(monitored_cases)
            if freq_optimization:
                recommendations.append(freq_optimization)
            
            # Analyze inactive cases
            inactive_optimization = await self._analyze_inactive_cases(monitored_cases)
            if inactive_optimization:
                recommendations.append(inactive_optimization)
            
            # Analyze high-cost low-activity cases
            activity_optimization = await self._analyze_activity_cost_ratio(monitored_cases)
            if activity_optimization:
                recommendations.append(activity_optimization)
            
            # Analyze redundant monitoring
            redundancy_optimization = await self._analyze_monitoring_redundancy(monitored_cases)
            if redundancy_optimization:
                recommendations.append(redundancy_optimization)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Cost optimization analysis failed: {str(e)}")
            return []
    
    async def generate_insights(
        self,
        monitored_cases: Dict[str, MonitoredCase],
        period_days: int = 30
    ) -> List[MonitoringInsight]:
        """Generate monitoring insights"""
        
        try:
            insights = []
            
            # Performance insights
            performance_insights = await self._analyze_performance_insights(monitored_cases)
            insights.extend(performance_insights)
            
            # Cost insights
            cost_insights = await self._analyze_cost_insights(monitored_cases)
            insights.extend(cost_insights)
            
            # Activity insights
            activity_insights = await self._analyze_activity_insights(monitored_cases, period_days)
            insights.extend(activity_insights)
            
            # Anomaly detection
            anomaly_insights = await self._detect_anomalies(monitored_cases)
            insights.extend(anomaly_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight generation failed: {str(e)}")
            return []
    
    async def generate_report(
        self,
        start_date: datetime,
        end_date: datetime,
        monitored_cases: Dict[str, MonitoredCase] = None
    ) -> MonitoringReport:
        """Generate comprehensive monitoring analytics report"""
        
        try:
            report = MonitoringReport(
                report_id=f"analytics_{int(datetime.now().timestamp())}",
                generated_at=datetime.now(timezone.utc),
                period_start=start_date,
                period_end=end_date
            )
            
            if not monitored_cases:
                # Load from cache or storage
                monitored_cases = await self._load_monitored_cases_for_analysis()
            
            # Generate summary statistics
            report.summary_stats = await self._generate_summary_stats(
                monitored_cases, start_date, end_date
            )
            
            # Analyze trends
            key_metrics = [
                "total_checks", "total_changes", "total_cost", "change_rate",
                "average_response_time", "error_rate"
            ]
            
            for metric in key_metrics:
                trend = await self.analyze_trends(metric, days_back=30)
                if trend:
                    report.trends.append(trend)
            
            # Cost analysis
            report.cost_analysis = await self._generate_cost_analysis(
                monitored_cases, start_date, end_date
            )
            
            # Performance metrics
            report.performance_metrics = await self._generate_performance_metrics(
                monitored_cases, start_date, end_date
            )
            
            # Generate insights
            report.insights = await self.generate_insights(monitored_cases)
            
            # Generate recommendations
            report.recommendations = await self.analyze_cost_optimization(monitored_cases)
            
            # Top active cases
            report.top_active_cases = await self._get_top_active_cases(monitored_cases)
            
            # Change patterns
            report.change_patterns = await self._analyze_change_patterns(start_date, end_date)
            
            logger.info(f"Generated analytics report with {len(report.insights)} insights")
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return MonitoringReport(
                report_id="error",
                generated_at=datetime.now(timezone.utc),
                period_start=start_date,
                period_end=end_date
            )
    
    async def _analyze_frequency_optimization(
        self,
        monitored_cases: Dict[str, MonitoredCase]
    ) -> Optional[CostOptimizationRecommendation]:
        """Analyze monitoring frequency optimization opportunities"""
        
        try:
            over_monitored = []
            under_monitored = []
            
            for case in monitored_cases.values():
                if case.check_count < 10:  # Not enough data
                    continue
                
                # Calculate activity rate
                if case.check_count > 0:
                    activity_rate = case.change_count / case.check_count
                else:
                    activity_rate = 0
                
                # Check if over-monitored (high frequency, low activity)
                if (case.frequency in [MonitoringFrequency.EVERY_5_MIN, MonitoringFrequency.EVERY_15_MIN] 
                    and activity_rate < 0.05):  # Less than 5% hit rate
                    over_monitored.append(case)
                
                # Check if under-monitored (low frequency, high activity)
                if (case.frequency in [MonitoringFrequency.HOURLY, MonitoringFrequency.EVERY_2_HOURS]
                    and activity_rate > 0.3):  # More than 30% hit rate
                    under_monitored.append(case)
            
            if over_monitored:
                # Calculate potential savings
                potential_savings = 0
                for case in over_monitored:
                    # Estimate cost reduction by reducing frequency
                    current_checks_per_day = self._get_checks_per_day(case.frequency)
                    reduced_checks_per_day = current_checks_per_day / 2  # Half the frequency
                    
                    cost_per_check = case.total_cost_cents / max(1, case.check_count)
                    daily_savings = (current_checks_per_day - reduced_checks_per_day) * cost_per_check
                    potential_savings += daily_savings * 30  # Monthly savings
                
                return CostOptimizationRecommendation(
                    recommendation_id="frequency_optimization",
                    title="Optimize Monitoring Frequencies",
                    description=f"Reduce monitoring frequency for {len(over_monitored)} low-activity cases",
                    potential_savings_dollars=potential_savings / 100.0,
                    implementation_effort="low",
                    impact="medium",
                    affected_monitors=[case.monitor_id for case in over_monitored],
                    implementation_steps=[
                        "Review low-activity cases",
                        "Reduce monitoring frequency to 30-60 minutes",
                        "Monitor for 2 weeks to ensure no missed critical changes",
                        "Adjust further if needed"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Frequency optimization analysis failed: {str(e)}")
            return None
    
    async def _analyze_inactive_cases(
        self,
        monitored_cases: Dict[str, MonitoredCase]
    ) -> Optional[CostOptimizationRecommendation]:
        """Analyze inactive cases that might be stopped"""
        
        try:
            inactive_threshold = datetime.now(timezone.utc) - timedelta(days=60)
            inactive_cases = []
            
            for case in monitored_cases.values():
                # Case hasn't had changes in 60+ days
                if (case.last_change_at and case.last_change_at < inactive_threshold) or \
                   (not case.last_change_at and case.created_at < inactive_threshold):
                    inactive_cases.append(case)
            
            if inactive_cases:
                # Calculate savings
                total_monthly_cost = sum(
                    (case.total_cost_cents / max(1, case.check_count)) * 
                    self._get_checks_per_day(case.frequency) * 30
                    for case in inactive_cases
                )
                
                return CostOptimizationRecommendation(
                    recommendation_id="inactive_cases",
                    title="Review Inactive Cases",
                    description=f"Consider pausing or stopping monitoring for {len(inactive_cases)} inactive cases",
                    potential_savings_dollars=total_monthly_cost / 100.0,
                    implementation_effort="low",
                    impact="high",
                    affected_monitors=[case.monitor_id for case in inactive_cases],
                    implementation_steps=[
                        "Review cases with no changes in 60+ days",
                        "Confirm cases are truly inactive (closed, settled, etc.)",
                        "Pause monitoring for confirmed inactive cases",
                        "Set up alerts for any unexpected activity"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Inactive cases analysis failed: {str(e)}")
            return None
    
    async def _analyze_activity_cost_ratio(
        self,
        monitored_cases: Dict[str, MonitoredCase]
    ) -> Optional[CostOptimizationRecommendation]:
        """Analyze cases with poor activity-to-cost ratios"""
        
        try:
            poor_ratio_cases = []
            
            for case in monitored_cases.values():
                if case.total_cost_cents < 100 or case.check_count < 10:  # Minimum thresholds
                    continue
                
                cost_per_change = case.total_cost_cents / max(1, case.change_count) if case.change_count > 0 else float('inf')
                
                # High cost per change (over $10)
                if cost_per_change > 1000:  # 1000 cents = $10
                    poor_ratio_cases.append((case, cost_per_change))
            
            if poor_ratio_cases:
                # Sort by worst ratio
                poor_ratio_cases.sort(key=lambda x: x[1], reverse=True)
                
                return CostOptimizationRecommendation(
                    recommendation_id="activity_cost_ratio",
                    title="Optimize High-Cost Low-Activity Cases",
                    description=f"Review {len(poor_ratio_cases)} cases with high cost per change",
                    potential_savings_dollars=0,  # Hard to estimate without changes
                    implementation_effort="medium",
                    impact="medium",
                    affected_monitors=[case.monitor_id for case, _ in poor_ratio_cases],
                    implementation_steps=[
                        "Review cases with cost per change > $10",
                        "Consider reducing monitoring frequency",
                        "Evaluate if monitoring is still necessary",
                        "Implement smarter change detection rules"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Activity-cost ratio analysis failed: {str(e)}")
            return None
    
    async def _analyze_monitoring_redundancy(
        self,
        monitored_cases: Dict[str, MonitoredCase]
    ) -> Optional[CostOptimizationRecommendation]:
        """Analyze redundant monitoring (same case multiple times)"""
        
        try:
            # Group by case number and court
            case_groups = defaultdict(list)
            
            for case in monitored_cases.values():
                key = f"{case.court_id}:{case.case_number}"
                case_groups[key].append(case)
            
            # Find duplicates
            redundant_cases = []
            for cases in case_groups.values():
                if len(cases) > 1:
                    # Sort by creation date, keep the oldest
                    cases.sort(key=lambda x: x.created_at)
                    redundant_cases.extend(cases[1:])  # All but the first
            
            if redundant_cases:
                total_redundant_cost = sum(case.total_cost_cents for case in redundant_cases)
                
                return CostOptimizationRecommendation(
                    recommendation_id="redundant_monitoring",
                    title="Remove Duplicate Case Monitoring",
                    description=f"Found {len(redundant_cases)} duplicate case monitors",
                    potential_savings_dollars=total_redundant_cost / 100.0,
                    implementation_effort="low",
                    impact="high",
                    affected_monitors=[case.monitor_id for case in redundant_cases],
                    implementation_steps=[
                        "Identify duplicate case monitors",
                        "Consolidate monitoring rules from duplicates",
                        "Remove redundant monitors",
                        "Verify monitoring continuity"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Redundancy analysis failed: {str(e)}")
            return None
    
    def _get_checks_per_day(self, frequency: MonitoringFrequency) -> float:
        """Get estimated checks per day for a frequency"""
        
        frequency_map = {
            MonitoringFrequency.EVERY_5_MIN: 288,    # 24*60/5
            MonitoringFrequency.EVERY_15_MIN: 96,    # 24*60/15
            MonitoringFrequency.EVERY_30_MIN: 48,    # 24*60/30
            MonitoringFrequency.HOURLY: 24,          # 24
            MonitoringFrequency.EVERY_2_HOURS: 12,   # 24/2
            MonitoringFrequency.EVERY_4_HOURS: 6,    # 24/4
            MonitoringFrequency.DAILY: 1,            # 1
            MonitoringFrequency.WEEKLY: 1/7          # 1/7
        }
        
        return frequency_map.get(frequency, 96)  # Default to 15 min
    
    # Additional analysis methods would go here...
    async def _analyze_performance_insights(self, monitored_cases: Dict[str, MonitoredCase]) -> List[MonitoringInsight]:
        """Analyze performance insights"""
        return []  # Placeholder
    
    async def _analyze_cost_insights(self, monitored_cases: Dict[str, MonitoredCase]) -> List[MonitoringInsight]:
        """Analyze cost insights"""
        return []  # Placeholder
    
    async def _analyze_activity_insights(self, monitored_cases: Dict[str, MonitoredCase], period_days: int) -> List[MonitoringInsight]:
        """Analyze activity insights"""
        return []  # Placeholder
    
    async def _detect_anomalies(self, monitored_cases: Dict[str, MonitoredCase]) -> List[MonitoringInsight]:
        """Detect anomalies in monitoring data"""
        return []  # Placeholder
    
    async def _load_monitored_cases_for_analysis(self) -> Dict[str, MonitoredCase]:
        """Load monitored cases for analysis"""
        return {}  # Placeholder
    
    async def _generate_summary_stats(self, monitored_cases: Dict[str, MonitoredCase], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {}  # Placeholder
    
    async def _generate_cost_analysis(self, monitored_cases: Dict[str, MonitoredCase], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate cost analysis"""
        return {}  # Placeholder
    
    async def _generate_performance_metrics(self, monitored_cases: Dict[str, MonitoredCase], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate performance metrics"""
        return {}  # Placeholder
    
    async def _get_top_active_cases(self, monitored_cases: Dict[str, MonitoredCase]) -> List[Dict[str, Any]]:
        """Get top active cases"""
        return []  # Placeholder
    
    async def _analyze_change_patterns(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze change patterns"""
        return {}  # Placeholder