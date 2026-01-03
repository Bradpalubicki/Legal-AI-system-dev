"""
Advanced cost analysis engine for legal research optimization.
Analyzes spending patterns, identifies inefficiencies, and provides cost optimization recommendations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from decimal import Decimal, ROUND_HALF_UP
import statistics
from collections import defaultdict
import numpy as np

from ..types.unified_types import UnifiedDocument, ContentType
from .cost_tracker import CostTracker, CostEvent, ResourceType, CostCategory, CostSummary
from .usage_monitor import UsageMonitor, UserProfile, EfficiencyLevel


class CostDriverType(Enum):
    """Types of cost drivers."""
    HIGH_VOLUME_USER = "high_volume_user"
    INEFFICIENT_SEARCHES = "inefficient_searches"
    PREMIUM_RESOURCE_OVERUSE = "premium_resource_overuse"
    LOW_RELEVANCE_RESULTS = "low_relevance_results"
    SUBSCRIPTION_UNDERUTILIZATION = "subscription_underutilization"
    PEAK_HOUR_CONCENTRATION = "peak_hour_concentration"
    DUPLICATE_RESEARCH = "duplicate_research"
    OVERAGE_FEES = "overage_fees"


class OptimizationOpportunity(Enum):
    """Types of optimization opportunities."""
    RESOURCE_SUBSTITUTION = "resource_substitution"
    USER_TRAINING = "user_training"
    SEARCH_REFINEMENT = "search_refinement"
    SUBSCRIPTION_ADJUSTMENT = "subscription_adjustment"
    WORKFLOW_IMPROVEMENT = "workflow_improvement"
    TIMING_OPTIMIZATION = "timing_optimization"
    BULK_PRICING = "bulk_pricing"
    ALTERNATIVE_PROVIDERS = "alternative_providers"


@dataclass
class CostDriver:
    """Individual cost driver analysis."""
    driver_type: CostDriverType
    description: str
    impact_amount: Decimal
    impact_percentage: float
    
    # Contributing factors
    users_involved: List[str] = field(default_factory=list)
    resources_involved: List[ResourceType] = field(default_factory=list)
    time_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics
    frequency: int = 0
    severity: str = "medium"  # "low", "medium", "high", "critical"
    
    # Resolution details
    estimated_savings: Decimal = Decimal('0.00')
    implementation_effort: str = "medium"  # "low", "medium", "high"
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""
    opportunity_type: OptimizationOpportunity
    title: str
    description: str
    
    # Financial impact
    estimated_monthly_savings: Decimal
    implementation_cost: Decimal = Decimal('0.00')
    payback_period_months: float = 0.0
    
    # Implementation details
    priority: str = "medium"  # "low", "medium", "high", "critical"
    effort_level: str = "medium"  # "low", "medium", "high"
    timeline: str = "1-3 months"
    
    # Affected entities
    affected_users: List[str] = field(default_factory=list)
    affected_resources: List[ResourceType] = field(default_factory=list)
    
    # Action items
    action_steps: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    
    # Risk assessment
    implementation_risks: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)


@dataclass
class CostEfficiencyMetrics:
    """Cost efficiency metrics for analysis."""
    period_start: datetime
    period_end: datetime
    
    # Overall efficiency
    cost_per_search: Decimal = Decimal('0.00')
    cost_per_document: Decimal = Decimal('0.00')
    cost_per_relevant_result: Decimal = Decimal('0.00')
    cost_per_user: Decimal = Decimal('0.00')
    
    # Resource efficiency
    resource_roi: Dict[ResourceType, float] = field(default_factory=dict)
    resource_utilization: Dict[ResourceType, float] = field(default_factory=dict)
    
    # User efficiency
    user_cost_efficiency: Dict[str, Decimal] = field(default_factory=dict)
    efficiency_quartiles: Dict[str, Decimal] = field(default_factory=dict)
    
    # Benchmarks
    industry_benchmarks: Dict[str, float] = field(default_factory=dict)
    internal_benchmarks: Dict[str, float] = field(default_factory=dict)
    
    # Trends
    efficiency_trend: str = "stable"  # "improving", "declining", "stable", "volatile"
    trend_percentage: float = 0.0


@dataclass
class CostAnalysisReport:
    """Comprehensive cost analysis report."""
    report_id: str
    analysis_date: datetime
    period_start: datetime
    period_end: datetime
    
    # Executive summary
    total_cost: Decimal
    cost_change_percentage: float
    primary_cost_drivers: List[CostDriver]
    top_optimization_opportunities: List[OptimizationRecommendation]
    
    # Detailed metrics
    efficiency_metrics: CostEfficiencyMetrics
    
    # Analysis findings
    cost_drivers: List[CostDriver]
    optimization_recommendations: List[OptimizationRecommendation]
    
    # Savings potential
    total_potential_savings: Decimal
    quick_win_savings: Decimal  # Savings from low-effort initiatives
    strategic_savings: Decimal  # Savings from high-effort initiatives
    
    # Implementation roadmap
    immediate_actions: List[str] = field(default_factory=list)
    short_term_goals: List[str] = field(default_factory=list)
    long_term_strategy: List[str] = field(default_factory=list)


class CostAnalyzer:
    """
    Advanced cost analysis engine for legal research optimization.
    
    Analyzes spending patterns, identifies cost drivers, calculates efficiency metrics,
    and provides actionable recommendations for cost optimization.
    """
    
    def __init__(self, cost_tracker: CostTracker, usage_monitor: UsageMonitor):
        self.cost_tracker = cost_tracker
        self.usage_monitor = usage_monitor
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.analysis_window_days = 90  # Default analysis period
        self.efficiency_benchmarks = {
            'cost_per_search': Decimal('10.00'),
            'cost_per_document': Decimal('15.00'),
            'cost_per_relevant_result': Decimal('25.00'),
            'relevance_rate_threshold': 0.6
        }
        
        # Industry benchmarks (example values)
        self.industry_benchmarks = {
            'cost_per_attorney_per_month': 800.0,
            'research_cost_percentage_of_revenue': 0.03,
            'average_relevance_rate': 0.65,
            'premium_resource_utilization': 0.75
        }
    
    async def analyze_costs(self, 
                          start_date: datetime,
                          end_date: datetime,
                          include_detailed_breakdown: bool = True) -> CostAnalysisReport:
        """
        Perform comprehensive cost analysis for a given period.
        
        Args:
            start_date: Analysis period start
            end_date: Analysis period end
            include_detailed_breakdown: Include detailed breakdowns
            
        Returns:
            CostAnalysisReport with findings and recommendations
        """
        
        self.logger.info(f"Starting cost analysis for period {start_date} to {end_date}")
        
        # Get cost summary
        cost_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
        
        # Calculate efficiency metrics
        efficiency_metrics = await self._calculate_efficiency_metrics(start_date, end_date, cost_summary)
        
        # Identify cost drivers
        cost_drivers = await self._identify_cost_drivers(start_date, end_date, cost_summary)
        
        # Generate optimization recommendations
        optimization_recommendations = await self._generate_optimization_recommendations(
            cost_drivers, efficiency_metrics, cost_summary
        )
        
        # Calculate savings potential
        total_potential_savings = sum(rec.estimated_monthly_savings for rec in optimization_recommendations)
        quick_win_savings = sum(
            rec.estimated_monthly_savings for rec in optimization_recommendations
            if rec.effort_level == "low"
        )
        strategic_savings = total_potential_savings - quick_win_savings
        
        # Create analysis report
        report = CostAnalysisReport(
            report_id=f"cost_analysis_{int(datetime.now().timestamp())}",
            analysis_date=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            total_cost=cost_summary.total_cost,
            cost_change_percentage=await self._calculate_cost_change_percentage(start_date, end_date),
            primary_cost_drivers=cost_drivers[:5],  # Top 5 drivers
            top_optimization_opportunities=optimization_recommendations[:5],  # Top 5 opportunities
            efficiency_metrics=efficiency_metrics,
            cost_drivers=cost_drivers,
            optimization_recommendations=optimization_recommendations,
            total_potential_savings=total_potential_savings,
            quick_win_savings=quick_win_savings,
            strategic_savings=strategic_savings
        )
        
        # Generate implementation roadmap
        report.immediate_actions = await self._generate_immediate_actions(optimization_recommendations)
        report.short_term_goals = await self._generate_short_term_goals(optimization_recommendations)
        report.long_term_strategy = await self._generate_long_term_strategy(optimization_recommendations)
        
        self.logger.info(f"Cost analysis completed. Total potential savings: ${total_potential_savings}")
        
        return report
    
    async def _calculate_efficiency_metrics(self, 
                                          start_date: datetime,
                                          end_date: datetime,
                                          cost_summary: CostSummary) -> CostEfficiencyMetrics:
        """Calculate detailed efficiency metrics."""
        
        metrics = CostEfficiencyMetrics(
            period_start=start_date,
            period_end=end_date
        )
        
        # Get usage data for efficiency calculations
        system_analytics = await self.usage_monitor.generate_system_analytics(start_date, end_date)
        
        # Calculate per-unit costs
        if system_analytics.total_activities > 0:
            total_searches = len([e for e in self.cost_tracker.cost_events 
                                if e.timestamp >= start_date and e.timestamp <= end_date
                                and e.cost_category == CostCategory.SEARCH_QUERIES])
            
            total_documents = len([e for e in self.cost_tracker.cost_events 
                                 if e.timestamp >= start_date and e.timestamp <= end_date
                                 and e.cost_category == CostCategory.DOCUMENT_RETRIEVAL])
            
            if total_searches > 0:
                search_costs = sum(e.total_cost for e in self.cost_tracker.cost_events 
                                 if e.timestamp >= start_date and e.timestamp <= end_date
                                 and e.cost_category == CostCategory.SEARCH_QUERIES)
                metrics.cost_per_search = search_costs / Decimal(str(total_searches))
            
            if total_documents > 0:
                document_costs = sum(e.total_cost for e in self.cost_tracker.cost_events 
                                   if e.timestamp >= start_date and e.timestamp <= end_date
                                   and e.cost_category == CostCategory.DOCUMENT_RETRIEVAL)
                metrics.cost_per_document = document_costs / Decimal(str(total_documents))
            
            # Calculate cost per relevant result
            total_relevant_results = sum(e.relevant_results for e in self.cost_tracker.cost_events 
                                       if e.timestamp >= start_date and e.timestamp <= end_date)
            
            if total_relevant_results > 0:
                metrics.cost_per_relevant_result = cost_summary.total_cost / Decimal(str(total_relevant_results))
            
            # Cost per user
            if system_analytics.total_users > 0:
                metrics.cost_per_user = cost_summary.total_cost / Decimal(str(system_analytics.total_users))
        
        # Calculate resource efficiency
        for resource, cost in cost_summary.costs_by_resource.items():
            if resource in system_analytics.resource_usage:
                usage_count = system_analytics.resource_usage[resource]
                if usage_count > 0:
                    # ROI calculation (simplified)
                    total_results = sum(e.relevant_results for e in self.cost_tracker.cost_events 
                                      if e.timestamp >= start_date and e.timestamp <= end_date
                                      and e.resource_type == resource)
                    
                    if total_results > 0 and cost > 0:
                        metrics.resource_roi[resource] = float(total_results) / float(cost)
                    
                    # Utilization (usage vs potential)
                    # This is simplified - in practice would calculate against subscription limits
                    metrics.resource_utilization[resource] = min(1.0, usage_count / 100.0)
        
        # Calculate user efficiency
        for user_id, user_cost in cost_summary.costs_by_user.items():
            user_profile = await self.usage_monitor.analyze_user_patterns(user_id)
            if user_profile.overall_relevance_rate > 0:
                efficiency = user_cost / Decimal(str(user_profile.overall_relevance_rate))
                metrics.user_cost_efficiency[user_id] = efficiency
        
        # Calculate efficiency quartiles
        if metrics.user_cost_efficiency:
            efficiency_values = list(metrics.user_cost_efficiency.values())
            efficiency_values.sort()
            n = len(efficiency_values)
            if n > 0:
                metrics.efficiency_quartiles = {
                    'q1': efficiency_values[int(n * 0.25)],
                    'q2': efficiency_values[int(n * 0.5)],
                    'q3': efficiency_values[int(n * 0.75)],
                    'min': efficiency_values[0],
                    'max': efficiency_values[-1]
                }
        
        # Set benchmarks
        metrics.industry_benchmarks = self.industry_benchmarks.copy()
        
        # Calculate trend
        metrics.efficiency_trend, metrics.trend_percentage = await self._calculate_efficiency_trend(
            start_date, end_date
        )
        
        return metrics
    
    async def _identify_cost_drivers(self, 
                                   start_date: datetime,
                                   end_date: datetime,
                                   cost_summary: CostSummary) -> List[CostDriver]:
        """Identify primary cost drivers."""
        
        cost_drivers = []
        
        # Analyze high-cost users
        await self._analyze_high_cost_users(start_date, end_date, cost_summary, cost_drivers)
        
        # Analyze inefficient searches
        await self._analyze_inefficient_searches(start_date, end_date, cost_drivers)
        
        # Analyze premium resource usage
        await self._analyze_premium_resource_usage(start_date, end_date, cost_summary, cost_drivers)
        
        # Analyze subscription utilization
        await self._analyze_subscription_utilization(start_date, end_date, cost_summary, cost_drivers)
        
        # Analyze overage fees
        await self._analyze_overage_fees(start_date, end_date, cost_drivers)
        
        # Sort by impact
        cost_drivers.sort(key=lambda x: x.impact_amount, reverse=True)
        
        return cost_drivers
    
    async def _analyze_high_cost_users(self, 
                                     start_date: datetime,
                                     end_date: datetime,
                                     cost_summary: CostSummary,
                                     cost_drivers: List[CostDriver]):
        """Analyze high-cost users as potential cost drivers."""
        
        if not cost_summary.costs_by_user:
            return
        
        # Find users with costs above 75th percentile
        user_costs = list(cost_summary.costs_by_user.values())
        if len(user_costs) < 4:  # Need at least 4 users for meaningful quartiles
            return
        
        user_costs.sort()
        q3_threshold = user_costs[int(len(user_costs) * 0.75)]
        
        high_cost_users = []
        total_high_cost = Decimal('0.00')
        
        for user_id, cost in cost_summary.costs_by_user.items():
            if cost >= q3_threshold:
                high_cost_users.append(user_id)
                total_high_cost += cost
        
        if high_cost_users:
            impact_percentage = float(total_high_cost / cost_summary.total_cost) * 100
            
            # Analyze if these users are inefficient
            inefficient_users = []
            for user_id in high_cost_users:
                profile = await self.usage_monitor.analyze_user_patterns(user_id)
                if profile.efficiency_level in [EfficiencyLevel.INEFFICIENT, EfficiencyLevel.HIGHLY_INEFFICIENT]:
                    inefficient_users.append(user_id)
            
            if inefficient_users:
                # Calculate potential savings from improving efficiency
                estimated_savings = total_high_cost * Decimal('0.3')  # 30% savings potential
                
                cost_driver = CostDriver(
                    driver_type=CostDriverType.HIGH_VOLUME_USER,
                    description=f"{len(high_cost_users)} high-cost users account for {impact_percentage:.1f}% of total costs",
                    impact_amount=total_high_cost,
                    impact_percentage=impact_percentage,
                    users_involved=high_cost_users,
                    frequency=len(high_cost_users),
                    severity="high" if impact_percentage > 50 else "medium",
                    estimated_savings=estimated_savings,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Provide efficiency training for high-cost users",
                        "Analyze usage patterns of high-cost users",
                        "Set cost monitoring alerts for top users",
                        "Review research workflows for optimization"
                    ]
                )
                
                cost_drivers.append(cost_driver)
    
    async def _analyze_inefficient_searches(self, 
                                          start_date: datetime,
                                          end_date: datetime,
                                          cost_drivers: List[CostDriver]):
        """Analyze inefficient searches as cost drivers."""
        
        # Get search events
        search_events = [
            e for e in self.cost_tracker.cost_events
            if e.timestamp >= start_date and e.timestamp <= end_date
            and e.cost_category == CostCategory.SEARCH_QUERIES
        ]
        
        if not search_events:
            return
        
        # Calculate relevance rates
        inefficient_searches = []
        total_inefficient_cost = Decimal('0.00')
        
        for event in search_events:
            if event.results_found > 0:
                relevance_rate = event.relevant_results / event.results_found
                if relevance_rate < 0.3:  # Less than 30% relevance
                    inefficient_searches.append(event)
                    total_inefficient_cost += event.total_cost
        
        if inefficient_searches:
            impact_percentage = float(total_inefficient_cost / sum(e.total_cost for e in search_events)) * 100
            
            # Estimate savings from improving search efficiency
            estimated_savings = total_inefficient_cost * Decimal('0.5')  # 50% savings potential
            
            # Get unique users involved
            users_involved = list(set(e.user_id for e in inefficient_searches))
            
            cost_driver = CostDriver(
                driver_type=CostDriverType.INEFFICIENT_SEARCHES,
                description=f"{len(inefficient_searches)} inefficient searches with low relevance rates",
                impact_amount=total_inefficient_cost,
                impact_percentage=impact_percentage,
                users_involved=users_involved,
                frequency=len(inefficient_searches),
                severity="high" if impact_percentage > 25 else "medium",
                estimated_savings=estimated_savings,
                implementation_effort="low",
                recommended_actions=[
                    "Provide search technique training",
                    "Implement search query suggestions",
                    "Add relevance feedback mechanisms",
                    "Create search best practices guide"
                ]
            )
            
            cost_drivers.append(cost_driver)
    
    async def _analyze_premium_resource_usage(self, 
                                            start_date: datetime,
                                            end_date: datetime,
                                            cost_summary: CostSummary,
                                            cost_drivers: List[CostDriver]):
        """Analyze premium resource usage patterns."""
        
        premium_resources = [ResourceType.WESTLAW, ResourceType.LEXIS, ResourceType.BLOOMBERG_LAW]
        free_resources = [ResourceType.GOOGLE_SCHOLAR, ResourceType.JUSTIA]
        
        premium_cost = Decimal('0.00')
        premium_usage = 0
        
        for resource in premium_resources:
            if resource in cost_summary.costs_by_resource:
                premium_cost += cost_summary.costs_by_resource[resource]
            
            # Count usage
            premium_usage += len([
                e for e in self.cost_tracker.cost_events
                if e.timestamp >= start_date and e.timestamp <= end_date
                and e.resource_type == resource
            ])
        
        # Check for potential over-reliance on premium resources
        total_usage = len([
            e for e in self.cost_tracker.cost_events
            if e.timestamp >= start_date and e.timestamp <= end_date
            and e.resource_type is not None
        ])
        
        if total_usage > 0:
            premium_usage_percentage = (premium_usage / total_usage) * 100
            
            # If premium usage is very high, it might be a cost driver
            if premium_usage_percentage > 80:  # More than 80% premium usage
                impact_percentage = float(premium_cost / cost_summary.total_cost) * 100
                
                # Estimate savings from partial substitution with free resources
                estimated_savings = premium_cost * Decimal('0.15')  # 15% savings potential
                
                cost_driver = CostDriver(
                    driver_type=CostDriverType.PREMIUM_RESOURCE_OVERUSE,
                    description=f"Heavy reliance on premium resources ({premium_usage_percentage:.1f}% of usage)",
                    impact_amount=premium_cost,
                    impact_percentage=impact_percentage,
                    resources_involved=premium_resources,
                    frequency=premium_usage,
                    severity="medium",
                    estimated_savings=estimated_savings,
                    implementation_effort="medium",
                    recommended_actions=[
                        "Evaluate free alternatives for initial research",
                        "Create research workflow using tiered resources",
                        "Train users on cost-effective research strategies",
                        "Implement resource recommendation system"
                    ]
                )
                
                cost_drivers.append(cost_driver)
    
    async def _analyze_subscription_utilization(self, 
                                              start_date: datetime,
                                              end_date: datetime,
                                              cost_summary: CostSummary,
                                              cost_drivers: List[CostDriver]):
        """Analyze subscription utilization rates."""
        
        # Get subscription costs
        subscription_events = [
            e for e in self.cost_tracker.cost_events
            if e.timestamp >= start_date and e.timestamp <= end_date
            and e.cost_category == CostCategory.SUBSCRIPTION
        ]
        
        if not subscription_events:
            return
        
        total_subscription_cost = sum(e.total_cost for e in subscription_events)
        
        # Analyze utilization for each subscribed resource
        for resource_type, pricing in self.cost_tracker.pricing_configs.items():
            if pricing.monthly_fee > 0 or pricing.annual_fee > 0:
                # Calculate actual usage vs included limits
                monthly_searches = await self.cost_tracker._get_monthly_usage_count(resource_type, "searches")
                monthly_documents = await self.cost_tracker._get_monthly_usage_count(resource_type, "documents")
                
                # Check utilization rates
                search_utilization = 0.0
                document_utilization = 0.0
                
                if pricing.included_searches > 0:
                    search_utilization = monthly_searches / pricing.included_searches
                
                if pricing.included_documents > 0:
                    document_utilization = monthly_documents / pricing.included_documents
                
                # Flag underutilized subscriptions
                avg_utilization = (search_utilization + document_utilization) / 2
                if avg_utilization < 0.5:  # Less than 50% utilization
                    
                    underutilized_cost = pricing.monthly_fee * Decimal('0.5')  # Potential savings
                    
                    cost_driver = CostDriver(
                        driver_type=CostDriverType.SUBSCRIPTION_UNDERUTILIZATION,
                        description=f"{resource_type.value} subscription underutilized ({avg_utilization*100:.1f}%)",
                        impact_amount=underutilized_cost,
                        impact_percentage=float(underutilized_cost / total_subscription_cost) * 100,
                        resources_involved=[resource_type],
                        severity="medium" if avg_utilization < 0.3 else "low",
                        estimated_savings=underutilized_cost,
                        implementation_effort="low",
                        recommended_actions=[
                            "Review subscription necessity",
                            "Downgrade to lower tier if available",
                            "Increase usage through training",
                            "Consider usage-based pricing model"
                        ]
                    )
                    
                    cost_drivers.append(cost_driver)
    
    async def _analyze_overage_fees(self, 
                                  start_date: datetime,
                                  end_date: datetime,
                                  cost_drivers: List[CostDriver]):
        """Analyze overage fees as cost drivers."""
        
        overage_events = []
        total_overage_cost = Decimal('0.00')
        
        for event in self.cost_tracker.cost_events:
            if (event.timestamp >= start_date and event.timestamp <= end_date and
                event.additional_fees > 0):
                
                # Check if additional fees are likely overage charges
                pricing = self.cost_tracker.pricing_configs.get(event.resource_type)
                if pricing and pricing.overage_multiplier > 1.0:
                    overage_events.append(event)
                    total_overage_cost += event.additional_fees
        
        if overage_events:
            total_period_cost = sum(
                e.total_cost for e in self.cost_tracker.cost_events
                if start_date <= e.timestamp <= end_date
            )
            
            impact_percentage = float(total_overage_cost / total_period_cost) * 100
            
            # Get users generating overages
            users_involved = list(set(e.user_id for e in overage_events))
            resources_involved = list(set(e.resource_type for e in overage_events if e.resource_type))
            
            cost_driver = CostDriver(
                driver_type=CostDriverType.OVERAGE_FEES,
                description=f"{len(overage_events)} overage incidents generating extra fees",
                impact_amount=total_overage_cost,
                impact_percentage=impact_percentage,
                users_involved=users_involved,
                resources_involved=resources_involved,
                frequency=len(overage_events),
                severity="high" if impact_percentage > 15 else "medium",
                estimated_savings=total_overage_cost * Decimal('0.8'),  # 80% savings potential
                implementation_effort="medium",
                recommended_actions=[
                    "Implement usage monitoring and alerts",
                    "Negotiate higher usage limits",
                    "Redistribute usage across subscription periods",
                    "Consider alternative pricing models"
                ]
            )
            
            cost_drivers.append(cost_driver)
    
    async def _generate_optimization_recommendations(self,
                                                   cost_drivers: List[CostDriver],
                                                   efficiency_metrics: CostEfficiencyMetrics,
                                                   cost_summary: CostSummary) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis."""
        
        recommendations = []
        
        # Generate recommendations for each cost driver
        for driver in cost_drivers:
            recommendations.extend(await self._generate_driver_recommendations(driver, cost_summary))
        
        # Generate efficiency-based recommendations
        recommendations.extend(await self._generate_efficiency_recommendations(efficiency_metrics, cost_summary))
        
        # Generate resource optimization recommendations
        recommendations.extend(await self._generate_resource_recommendations(cost_summary))
        
        # Sort by potential savings
        recommendations.sort(key=lambda x: x.estimated_monthly_savings, reverse=True)
        
        return recommendations
    
    async def _generate_driver_recommendations(self,
                                             driver: CostDriver,
                                             cost_summary: CostSummary) -> List[OptimizationRecommendation]:
        """Generate recommendations for specific cost drivers."""
        
        recommendations = []
        
        if driver.driver_type == CostDriverType.HIGH_VOLUME_USER:
            rec = OptimizationRecommendation(
                opportunity_type=OptimizationOpportunity.USER_TRAINING,
                title="High-Cost User Training Program",
                description="Implement targeted training for users generating high costs",
                estimated_monthly_savings=driver.estimated_savings,
                priority="high",
                effort_level="medium",
                timeline="1-2 months",
                affected_users=driver.users_involved,
                action_steps=[
                    "Identify specific inefficiencies for each high-cost user",
                    "Develop personalized training programs",
                    "Implement usage monitoring dashboards",
                    "Set up regular review meetings"
                ],
                success_metrics=[
                    "Reduction in cost per user",
                    "Improvement in search relevance rates",
                    "Decrease in premium resource usage"
                ]
            )
            recommendations.append(rec)
        
        elif driver.driver_type == CostDriverType.INEFFICIENT_SEARCHES:
            rec = OptimizationRecommendation(
                opportunity_type=OptimizationOpportunity.SEARCH_REFINEMENT,
                title="Search Efficiency Improvement",
                description="Improve search techniques and tools to increase relevance rates",
                estimated_monthly_savings=driver.estimated_savings,
                priority="high",
                effort_level="low",
                timeline="2-4 weeks",
                affected_users=driver.users_involved,
                action_steps=[
                    "Implement search query assistance tools",
                    "Provide search technique training",
                    "Add relevance feedback mechanisms",
                    "Create search templates for common queries"
                ],
                success_metrics=[
                    "Increase in average relevance rate",
                    "Reduction in searches per research task",
                    "User satisfaction with search results"
                ]
            )
            recommendations.append(rec)
        
        elif driver.driver_type == CostDriverType.PREMIUM_RESOURCE_OVERUSE:
            rec = OptimizationRecommendation(
                opportunity_type=OptimizationOpportunity.RESOURCE_SUBSTITUTION,
                title="Resource Mix Optimization",
                description="Optimize use of free and premium resources",
                estimated_monthly_savings=driver.estimated_savings,
                priority="medium",
                effort_level="medium",
                timeline="1-3 months",
                affected_resources=driver.resources_involved,
                action_steps=[
                    "Develop tiered research workflow",
                    "Train users on free resource capabilities",
                    "Implement intelligent resource routing",
                    "Create resource selection guidelines"
                ],
                success_metrics=[
                    "Reduction in premium resource usage percentage",
                    "Maintained research quality",
                    "Cost per research task reduction"
                ]
            )
            recommendations.append(rec)
        
        elif driver.driver_type == CostDriverType.SUBSCRIPTION_UNDERUTILIZATION:
            rec = OptimizationRecommendation(
                opportunity_type=OptimizationOpportunity.SUBSCRIPTION_ADJUSTMENT,
                title="Subscription Right-Sizing",
                description="Adjust subscriptions to match actual usage patterns",
                estimated_monthly_savings=driver.estimated_savings,
                priority="medium",
                effort_level="low",
                timeline="1 month",
                affected_resources=driver.resources_involved,
                action_steps=[
                    "Analyze usage patterns vs subscription limits",
                    "Negotiate with vendors for better pricing tiers",
                    "Consider usage-based pricing models",
                    "Redistribute subscriptions among users"
                ],
                success_metrics=[
                    "Improved subscription utilization rates",
                    "Cost reduction per subscription",
                    "Better alignment of costs with usage"
                ]
            )
            recommendations.append(rec)
        
        elif driver.driver_type == CostDriverType.OVERAGE_FEES:
            rec = OptimizationRecommendation(
                opportunity_type=OptimizationOpportunity.WORKFLOW_IMPROVEMENT,
                title="Usage Monitoring and Control",
                description="Implement systems to prevent overage fees",
                estimated_monthly_savings=driver.estimated_savings,
                priority="high",
                effort_level="medium",
                timeline="1-2 months",
                affected_users=driver.users_involved,
                action_steps=[
                    "Implement real-time usage monitoring",
                    "Set up automated alerts for usage thresholds",
                    "Create usage budgets for users/matters",
                    "Negotiate better overage terms with vendors"
                ],
                success_metrics=[
                    "Reduction in overage incidents",
                    "Better usage distribution across periods",
                    "Improved cost predictability"
                ]
            )
            recommendations.append(rec)
        
        return recommendations
    
    async def _generate_efficiency_recommendations(self,
                                                 efficiency_metrics: CostEfficiencyMetrics,
                                                 cost_summary: CostSummary) -> List[OptimizationRecommendation]:
        """Generate recommendations based on efficiency metrics."""
        
        recommendations = []
        
        # Cost per search optimization
        if efficiency_metrics.cost_per_search > self.efficiency_benchmarks['cost_per_search']:
            excess_cost = efficiency_metrics.cost_per_search - self.efficiency_benchmarks['cost_per_search']
            
            # Estimate monthly searches
            search_events = len([e for e in self.cost_tracker.cost_events 
                               if e.cost_category == CostCategory.SEARCH_QUERIES])
            monthly_searches = search_events * 30 / max(1, (efficiency_metrics.period_end - efficiency_metrics.period_start).days)
            
            potential_savings = excess_cost * Decimal(str(monthly_searches))
            
            rec = OptimizationRecommendation(
                opportunity_type=OptimizationOpportunity.SEARCH_REFINEMENT,
                title="Search Cost Optimization",
                description=f"Reduce cost per search from ${efficiency_metrics.cost_per_search} to target ${self.efficiency_benchmarks['cost_per_search']}",
                estimated_monthly_savings=potential_savings,
                priority="medium",
                effort_level="medium",
                action_steps=[
                    "Analyze high-cost search patterns",
                    "Implement search optimization tools",
                    "Provide targeted user training",
                    "Optimize resource selection algorithms"
                ]
            )
            recommendations.append(rec)
        
        # Low ROI resources
        for resource, roi in efficiency_metrics.resource_roi.items():
            if roi < 1.0:  # Less than 1 relevant result per dollar
                resource_cost = cost_summary.costs_by_resource.get(resource, Decimal('0.00'))
                potential_savings = resource_cost * Decimal('0.3')  # 30% improvement potential
                
                rec = OptimizationRecommendation(
                    opportunity_type=OptimizationOpportunity.RESOURCE_SUBSTITUTION,
                    title=f"Improve {resource.value} ROI",
                    description=f"Low ROI ({roi:.2f}) for {resource.value} - consider alternatives",
                    estimated_monthly_savings=potential_savings,
                    priority="low",
                    effort_level="medium",
                    affected_resources=[resource],
                    action_steps=[
                        f"Evaluate {resource.value} usage patterns",
                        "Identify alternative resources",
                        "Test resource substitution",
                        "Monitor quality impact"
                    ]
                )
                recommendations.append(rec)
        
        return recommendations
    
    async def _generate_resource_recommendations(self, cost_summary: CostSummary) -> List[OptimizationRecommendation]:
        """Generate resource-specific recommendations."""
        
        recommendations = []
        
        # Vendor consolidation opportunity
        premium_resources = [ResourceType.WESTLAW, ResourceType.LEXIS, ResourceType.BLOOMBERG_LAW]
        used_premium = [r for r in premium_resources if r in cost_summary.costs_by_resource]
        
        if len(used_premium) > 1:
            total_premium_cost = sum(cost_summary.costs_by_resource[r] for r in used_premium)
            potential_savings = total_premium_cost * Decimal('0.15')  # 15% volume discount
            
            rec = OptimizationRecommendation(
                opportunity_type=OptimizationOpportunity.BULK_PRICING,
                title="Vendor Consolidation",
                description="Consolidate premium subscriptions for volume discounts",
                estimated_monthly_savings=potential_savings,
                priority="low",
                effort_level="high",
                timeline="6-12 months",
                affected_resources=used_premium,
                action_steps=[
                    "Analyze feature overlap between resources",
                    "Negotiate volume pricing with preferred vendor",
                    "Plan migration strategy",
                    "Train users on consolidated platform"
                ],
                implementation_risks=[
                    "User resistance to platform change",
                    "Potential feature gaps",
                    "Migration complexity"
                ],
                mitigation_strategies=[
                    "Comprehensive user training program",
                    "Phased migration approach",
                    "Maintain backup access during transition"
                ]
            )
            recommendations.append(rec)
        
        return recommendations
    
    async def _calculate_cost_change_percentage(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate cost change percentage compared to previous period."""
        
        period_duration = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_duration)
        previous_end = start_date
        
        current_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
        previous_summary = await self.cost_tracker.get_cost_summary(previous_start, previous_end)
        
        if previous_summary.total_cost > 0:
            change = ((current_summary.total_cost - previous_summary.total_cost) / 
                     previous_summary.total_cost) * 100
            return float(change)
        
        return 0.0
    
    async def _calculate_efficiency_trend(self, start_date: datetime, end_date: datetime) -> Tuple[str, float]:
        """Calculate efficiency trend over the analysis period."""
        
        # Split period into segments for trend analysis
        period_duration = (end_date - start_date).days
        segment_days = max(7, period_duration // 4)  # At least weekly segments
        
        segment_efficiencies = []
        current_date = start_date
        
        while current_date < end_date:
            segment_end = min(current_date + timedelta(days=segment_days), end_date)
            
            # Calculate efficiency for segment
            segment_events = [
                e for e in self.cost_tracker.cost_events
                if current_date <= e.timestamp < segment_end
            ]
            
            if segment_events:
                total_results = sum(e.results_found for e in segment_events)
                total_relevant = sum(e.relevant_results for e in segment_events)
                
                if total_results > 0:
                    efficiency = total_relevant / total_results
                    segment_efficiencies.append(efficiency)
            
            current_date = segment_end
        
        if len(segment_efficiencies) < 2:
            return "stable", 0.0
        
        # Calculate trend
        first_half_avg = statistics.mean(segment_efficiencies[:len(segment_efficiencies)//2])
        second_half_avg = statistics.mean(segment_efficiencies[len(segment_efficiencies)//2:])
        
        change_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        if change_percentage > 5:
            return "improving", change_percentage
        elif change_percentage < -5:
            return "declining", change_percentage
        else:
            # Check for volatility
            if len(segment_efficiencies) > 2:
                std_dev = statistics.stdev(segment_efficiencies)
                mean_efficiency = statistics.mean(segment_efficiencies)
                
                if std_dev / mean_efficiency > 0.2:  # High coefficient of variation
                    return "volatile", change_percentage
            
            return "stable", change_percentage
    
    async def _generate_immediate_actions(self, recommendations: List[OptimizationRecommendation]) -> List[str]:
        """Generate immediate actions from recommendations."""
        
        immediate_actions = []
        
        for rec in recommendations:
            if rec.effort_level == "low" and rec.priority in ["critical", "high"]:
                immediate_actions.extend(rec.action_steps[:2])  # First 2 action steps
        
        return immediate_actions[:5]  # Top 5 immediate actions
    
    async def _generate_short_term_goals(self, recommendations: List[OptimizationRecommendation]) -> List[str]:
        """Generate short-term goals (1-3 months)."""
        
        short_term_goals = []
        
        for rec in recommendations:
            if "month" in rec.timeline and rec.priority in ["high", "medium"]:
                short_term_goals.append(f"Implement {rec.title}")
        
        return short_term_goals[:5]
    
    async def _generate_long_term_strategy(self, recommendations: List[OptimizationRecommendation]) -> List[str]:
        """Generate long-term strategic goals."""
        
        long_term_strategy = [
            "Establish ongoing cost monitoring and optimization processes",
            "Develop internal legal research expertise and training programs",
            "Negotiate strategic partnerships with research vendors",
            "Implement advanced analytics and AI for research optimization",
            "Create cost-aware research culture and best practices"
        ]
        
        # Add high-impact, high-effort recommendations
        for rec in recommendations:
            if rec.effort_level == "high" and rec.estimated_monthly_savings > Decimal('1000.00'):
                long_term_strategy.append(f"Execute {rec.title} for significant cost reduction")
        
        return long_term_strategy[:7]
    
    async def benchmark_against_industry(self, metrics: CostEfficiencyMetrics) -> Dict[str, Any]:
        """Benchmark metrics against industry standards."""
        
        benchmark_comparison = {
            'cost_per_user_vs_industry': {
                'current': float(metrics.cost_per_user),
                'industry_average': self.industry_benchmarks.get('cost_per_attorney_per_month', 800.0),
                'performance': 'above' if float(metrics.cost_per_user) > 800.0 else 'below'
            },
            'relevance_rate_vs_industry': {
                'current': metrics.efficiency_trend,  # This would be the actual relevance rate
                'industry_average': self.industry_benchmarks.get('average_relevance_rate', 0.65),
                'performance': 'above'  # Would calculate based on actual data
            }
        }
        
        return benchmark_comparison
    
    async def generate_executive_summary(self, report: CostAnalysisReport) -> str:
        """Generate executive summary of the cost analysis."""
        
        summary_parts = []
        
        # Key findings
        summary_parts.append("EXECUTIVE SUMMARY")
        summary_parts.append("==================")
        summary_parts.append("")
        
        summary_parts.append(f"Analysis Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}")
        summary_parts.append(f"Total Research Costs: ${report.total_cost:,.2f}")
        summary_parts.append(f"Cost Change: {report.cost_change_percentage:+.1f}% vs previous period")
        summary_parts.append("")
        
        # Top cost drivers
        summary_parts.append("PRIMARY COST DRIVERS:")
        for i, driver in enumerate(report.primary_cost_drivers[:3], 1):
            summary_parts.append(f"{i}. {driver.description} (${driver.impact_amount:,.2f})")
        summary_parts.append("")
        
        # Optimization opportunities
        summary_parts.append("TOP OPTIMIZATION OPPORTUNITIES:")
        for i, rec in enumerate(report.top_optimization_opportunities[:3], 1):
            summary_parts.append(f"{i}. {rec.title} (${rec.estimated_monthly_savings:,.2f}/month savings)")
        summary_parts.append("")
        
        # Financial impact
        summary_parts.append(f"Total Potential Monthly Savings: ${report.total_potential_savings:,.2f}")
        summary_parts.append(f"Quick Wins (Low Effort): ${report.quick_win_savings:,.2f}")
        summary_parts.append(f"Strategic Initiatives: ${report.strategic_savings:,.2f}")
        summary_parts.append("")
        
        # Key recommendations
        summary_parts.append("IMMEDIATE ACTIONS REQUIRED:")
        for i, action in enumerate(report.immediate_actions[:3], 1):
            summary_parts.append(f"{i}. {action}")
        
        return "\n".join(summary_parts)


# Helper functions
async def analyze_research_costs(start_date: datetime, end_date: datetime) -> CostAnalysisReport:
    """Helper function to perform cost analysis."""
    cost_tracker = CostTracker()
    usage_monitor = UsageMonitor()
    analyzer = CostAnalyzer(cost_tracker, usage_monitor)
    
    return await analyzer.analyze_costs(start_date, end_date)

async def get_cost_optimization_recommendations(period_days: int = 30) -> List[OptimizationRecommendation]:
    """Helper function to get optimization recommendations."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    report = await analyze_research_costs(start_date, end_date)
    return report.optimization_recommendations