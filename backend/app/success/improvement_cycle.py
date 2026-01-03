"""
Customer Success Improvement Cycle Integration

Orchestrates the complete feedback-to-improvement cycle:
1. Data collection from all success touchpoints
2. Analysis and insight generation
3. Prioritization of improvement opportunities
4. Action planning and execution
5. Impact measurement and iteration
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..core.database import get_db
from ..models.success_tracking import (
    SuccessMetric, ImprovementOpportunity, Feedback, FeatureRequest,
    UserHealthScore, ChurnPrediction, OutreachAction
)
from .metrics import SuccessMetricsCalculator, MetricsDashboard, User, Client
from .outreach import ProactiveOutreachEngine
from .feedback import FeedbackAnalyzer, FeedbackCollector
# Mock logger - replace with actual logger import
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

try:
    from ..utils.logger import logger
except ImportError:
    logger = MockLogger()

# Mock classes for missing services - these should be replaced with actual imports
class NotificationService:
    async def create_notification(self, data):
        return {"success": True, "notification_id": "mock_id"}

class EmailService:
    async def send_email(self, to_email, subject, body, template_name, context=None):
        return {"success": True, "message": "Email sent"}


class ImprovementPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


@dataclass
class ImprovementInsight:
    insight_id: str
    category: str  # metrics, feedback, behavior, competitive
    title: str
    description: str
    supporting_data: Dict
    confidence_score: float
    impact_estimate: str
    actionability_score: float


@dataclass
class ActionPlan:
    plan_id: str
    opportunity_id: str
    title: str
    description: str
    owner: str
    priority: ImprovementPriority
    estimated_effort_weeks: int
    success_criteria: List[str]
    dependencies: List[str]
    target_completion: datetime
    status: ActionStatus
    progress_percentage: float = 0.0


@dataclass
class CycleReport:
    cycle_id: str
    period_start: datetime
    period_end: datetime
    insights_generated: int
    opportunities_identified: int
    action_plans_created: int
    metrics_improved: int
    user_satisfaction_change: float
    business_impact_summary: Dict
    next_cycle_date: datetime


class DataCollector:
    """Collects data from all customer success touchpoints"""

    def __init__(self, db: Session):
        self.db = db
        self.metrics_calculator = SuccessMetricsCalculator(db)

    async def collect_comprehensive_data(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Collect data from all customer success sources"""
        try:
            data = {}

            # 1. Collect metrics data
            data["metrics"] = await self._collect_metrics_data(period_start, period_end)

            # 2. Collect feedback data
            data["feedback"] = await self._collect_feedback_data(period_start, period_end)

            # 3. Collect behavioral data
            data["behavior"] = await self._collect_behavioral_data(period_start, period_end)

            # 4. Collect support data
            data["support"] = await self._collect_support_data(period_start, period_end)

            # 5. Collect business outcome data
            data["business"] = await self._collect_business_data(period_start, period_end)

            logger.info(f"Comprehensive data collection completed for period {period_start} to {period_end}")
            return data

        except Exception as e:
            logger.error(f"Error collecting comprehensive data: {e}")
            return {}

    async def _collect_metrics_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect success metrics data"""
        try:
            # Get all success metrics for the period
            metrics = self.db.query(SuccessMetric).filter(
                and_(
                    SuccessMetric.period_start >= start_date,
                    SuccessMetric.period_end <= end_date
                )
            ).all()

            metrics_data = {
                "total_metrics": len(metrics),
                "by_type": {},
                "trends": {},
                "performance_vs_target": {}
            }

            for metric in metrics:
                metric_type = metric.metric_type
                if metric_type not in metrics_data["by_type"]:
                    metrics_data["by_type"][metric_type] = []

                metrics_data["by_type"][metric_type].append({
                    "name": metric.metric_name,
                    "value": metric.value,
                    "previous_value": metric.previous_value,
                    "change_percentage": metric.change_percentage,
                    "trend": metric.trend,
                    "vs_benchmark": metric.performance_vs_benchmark
                })

            return metrics_data

        except Exception as e:
            logger.error(f"Error collecting metrics data: {e}")
            return {}

    async def _collect_feedback_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect feedback and survey data"""
        try:
            # Get feedback for period
            feedback_items = self.db.query(Feedback).filter(
                Feedback.created_at.between(start_date, end_date)
            ).all()

            # Get feature requests
            feature_requests = self.db.query(FeatureRequest).filter(
                FeatureRequest.created_at.between(start_date, end_date)
            ).all()

            feedback_data = {
                "total_feedback": len(feedback_items),
                "feedback_by_type": {},
                "sentiment_distribution": {},
                "feature_requests": {
                    "total": len(feature_requests),
                    "by_priority": {},
                    "top_requested": []
                },
                "common_themes": await self._extract_feedback_themes(feedback_items)
            }

            # Analyze feedback by type
            for feedback in feedback_items:
                feedback_type = feedback.type.value
                if feedback_type not in feedback_data["feedback_by_type"]:
                    feedback_data["feedback_by_type"][feedback_type] = 0
                feedback_data["feedback_by_type"][feedback_type] += 1

            # Analyze feature requests by priority
            for request in feature_requests:
                priority = request.priority_score or 0
                priority_bucket = "high" if priority > 7 else "medium" if priority > 4 else "low"
                if priority_bucket not in feedback_data["feature_requests"]["by_priority"]:
                    feedback_data["feature_requests"]["by_priority"][priority_bucket] = 0
                feedback_data["feature_requests"]["by_priority"][priority_bucket] += 1

            return feedback_data

        except Exception as e:
            logger.error(f"Error collecting feedback data: {e}")
            return {}

    async def _collect_behavioral_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect user behavior and usage data"""
        try:
            # Get health score distributions
            health_scores = self.db.query(UserHealthScore).filter(
                UserHealthScore.calculation_date.between(start_date, end_date)
            ).all()

            # Get churn predictions
            churn_predictions = self.db.query(ChurnPrediction).filter(
                ChurnPrediction.prediction_date.between(start_date, end_date)
            ).all()

            behavior_data = {
                "health_score_distribution": {
                    "excellent": len([h for h in health_scores if h.status.value == "excellent"]),
                    "good": len([h for h in health_scores if h.status.value == "good"]),
                    "at_risk": len([h for h in health_scores if h.status.value == "at_risk"]),
                    "critical": len([h for h in health_scores if h.status.value == "critical"])
                },
                "churn_risk_analysis": {
                    "total_predictions": len(churn_predictions),
                    "high_risk": len([c for c in churn_predictions if c.churn_probability > 0.7]),
                    "medium_risk": len([c for c in churn_predictions if 0.4 <= c.churn_probability <= 0.7]),
                    "low_risk": len([c for c in churn_predictions if c.churn_probability < 0.4])
                },
                "common_risk_factors": await self._analyze_common_risk_factors(churn_predictions)
            }

            return behavior_data

        except Exception as e:
            logger.error(f"Error collecting behavioral data: {e}")
            return {}

    async def _collect_support_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect support and outreach data"""
        try:
            # Get outreach actions
            outreach_actions = self.db.query(OutreachAction).filter(
                OutreachAction.created_at.between(start_date, end_date)
            ).all()

            support_data = {
                "outreach_volume": len(outreach_actions),
                "outreach_by_type": {},
                "outreach_success_rate": 0,
                "response_patterns": {}
            }

            successful_actions = 0
            for action in outreach_actions:
                # Count by type
                action_type = action.outreach_type.value
                if action_type not in support_data["outreach_by_type"]:
                    support_data["outreach_by_type"][action_type] = 0
                support_data["outreach_by_type"][action_type] += 1

                # Count successful actions
                if action.success:
                    successful_actions += 1

            if outreach_actions:
                support_data["outreach_success_rate"] = successful_actions / len(outreach_actions)

            return support_data

        except Exception as e:
            logger.error(f"Error collecting support data: {e}")
            return {}

    async def _collect_business_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect business outcome data"""
        try:
            # Get user and client counts
            total_users = self.db.query(User).filter(
                User.created_at <= end_date
            ).count()

            new_users = self.db.query(User).filter(
                User.created_at.between(start_date, end_date)
            ).count()

            churned_users = self.db.query(User).filter(
                and_(
                    User.status == "inactive",
                    User.updated_at.between(start_date, end_date)
                )
            ).count()

            business_data = {
                "user_metrics": {
                    "total_users": total_users,
                    "new_users": new_users,
                    "churned_users": churned_users,
                    "net_user_growth": new_users - churned_users
                },
                "engagement_metrics": await self._calculate_engagement_metrics(start_date, end_date),
                "revenue_impact": await self._calculate_revenue_impact(start_date, end_date)
            }

            return business_data

        except Exception as e:
            logger.error(f"Error collecting business data: {e}")
            return {}

    async def _extract_feedback_themes(self, feedback_items: List[Feedback]) -> List[Dict]:
        """Extract common themes from feedback"""
        themes = {}

        for feedback in feedback_items:
            # Simple keyword-based theme extraction
            text = feedback.content.lower()

            # Define theme keywords
            theme_keywords = {
                "performance": ["slow", "fast", "speed", "loading", "response"],
                "usability": ["confusing", "difficult", "easy", "intuitive", "user-friendly"],
                "features": ["feature", "functionality", "capability", "tool"],
                "reliability": ["error", "bug", "broken", "crash", "issue"],
                "integration": ["connect", "integrate", "import", "export", "sync"]
            }

            for theme, keywords in theme_keywords.items():
                if any(keyword in text for keyword in keywords):
                    if theme not in themes:
                        themes[theme] = {"count": 0, "sentiment": "neutral"}
                    themes[theme]["count"] += 1

        return [{"theme": k, **v} for k, v in themes.items()]

    async def _analyze_common_risk_factors(self, predictions: List[ChurnPrediction]) -> List[Dict]:
        """Analyze most common churn risk factors"""
        risk_factor_counts = {}

        for prediction in predictions:
            if prediction.risk_factors:
                for factor in prediction.risk_factors:
                    if factor not in risk_factor_counts:
                        risk_factor_counts[factor] = 0
                    risk_factor_counts[factor] += 1

        # Sort by frequency
        sorted_factors = sorted(risk_factor_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"factor": factor, "count": count} for factor, count in sorted_factors[:10]]

    async def _calculate_engagement_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate user engagement metrics"""
        # Placeholder implementation
        return {
            "avg_session_duration": 0,
            "feature_adoption_rate": 0,
            "daily_active_users": 0
        }

    async def _calculate_revenue_impact(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate revenue impact metrics"""
        # Placeholder implementation
        return {
            "mrr_change": 0,
            "expansion_revenue": 0,
            "churn_impact": 0
        }


class InsightGenerator:
    """Generates actionable insights from collected data"""

    def __init__(self, db: Session):
        self.db = db

    async def generate_insights(self, data: Dict[str, Any]) -> List[ImprovementInsight]:
        """Generate insights from comprehensive data"""
        try:
            insights = []

            # 1. Generate metric-based insights
            metric_insights = await self._generate_metric_insights(data.get("metrics", {}))
            insights.extend(metric_insights)

            # 2. Generate feedback-based insights
            feedback_insights = await self._generate_feedback_insights(data.get("feedback", {}))
            insights.extend(feedback_insights)

            # 3. Generate behavioral insights
            behavior_insights = await self._generate_behavioral_insights(data.get("behavior", {}))
            insights.extend(behavior_insights)

            # 4. Generate cross-functional insights
            cross_insights = await self._generate_cross_functional_insights(data)
            insights.extend(cross_insights)

            # Sort insights by impact and confidence
            insights.sort(key=lambda x: (x.confidence_score * x.actionability_score), reverse=True)

            logger.info(f"Generated {len(insights)} improvement insights")
            return insights

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []

    async def _generate_metric_insights(self, metrics_data: Dict) -> List[ImprovementInsight]:
        """Generate insights from metrics data"""
        insights = []

        try:
            for metric_type, metrics in metrics_data.get("by_type", {}).items():
                for metric in metrics:
                    if metric["trend"] == "declining" and metric["change_percentage"] < -10:
                        insights.append(ImprovementInsight(
                            insight_id=f"metric_{metric_type}_{metric['name']}",
                            category="metrics",
                            title=f"Declining {metric['name']}",
                            description=f"{metric['name']} has declined by {abs(metric['change_percentage'])}% - requires attention",
                            supporting_data=metric,
                            confidence_score=0.9,
                            impact_estimate="high",
                            actionability_score=0.8
                        ))

        except Exception as e:
            logger.error(f"Error generating metric insights: {e}")

        return insights

    async def _generate_feedback_insights(self, feedback_data: Dict) -> List[ImprovementInsight]:
        """Generate insights from feedback data"""
        insights = []

        try:
            # Analyze common themes
            themes = feedback_data.get("common_themes", [])
            for theme in themes:
                if theme["count"] > 5:  # Threshold for significant themes
                    insights.append(ImprovementInsight(
                        insight_id=f"feedback_theme_{theme['theme']}",
                        category="feedback",
                        title=f"Recurring {theme['theme'].title()} Issues",
                        description=f"Users frequently mention {theme['theme']} issues ({theme['count']} instances)",
                        supporting_data=theme,
                        confidence_score=min(0.9, theme["count"] / 20),
                        impact_estimate="medium" if theme["count"] < 15 else "high",
                        actionability_score=0.7
                    ))

            # Analyze feature requests
            feature_requests = feedback_data.get("feature_requests", {})
            high_priority_requests = feature_requests.get("by_priority", {}).get("high", 0)

            if high_priority_requests > 10:
                insights.append(ImprovementInsight(
                    insight_id="high_priority_features",
                    category="feedback",
                    title="High Demand for New Features",
                    description=f"{high_priority_requests} high-priority feature requests indicate strong user demand",
                    supporting_data=feature_requests,
                    confidence_score=0.85,
                    impact_estimate="high",
                    actionability_score=0.6  # Requires product development
                ))

        except Exception as e:
            logger.error(f"Error generating feedback insights: {e}")

        return insights

    async def _generate_behavioral_insights(self, behavior_data: Dict) -> List[ImprovementInsight]:
        """Generate insights from behavioral data"""
        insights = []

        try:
            # Analyze health score distribution
            health_dist = behavior_data.get("health_score_distribution", {})
            at_risk_critical = health_dist.get("at_risk", 0) + health_dist.get("critical", 0)
            total_users = sum(health_dist.values())

            if total_users > 0 and (at_risk_critical / total_users) > 0.2:  # >20% at risk
                insights.append(ImprovementInsight(
                    insight_id="high_risk_user_concentration",
                    category="behavior",
                    title="High Concentration of At-Risk Users",
                    description=f"{(at_risk_critical/total_users)*100:.1f}% of users are at risk or critical",
                    supporting_data=health_dist,
                    confidence_score=0.95,
                    impact_estimate="critical",
                    actionability_score=0.9
                ))

            # Analyze common risk factors
            risk_factors = behavior_data.get("common_risk_factors", [])
            if risk_factors and risk_factors[0]["count"] > 10:
                top_risk = risk_factors[0]
                insights.append(ImprovementInsight(
                    insight_id=f"top_risk_factor_{top_risk['factor']}",
                    category="behavior",
                    title=f"Primary Risk Factor: {top_risk['factor']}",
                    description=f"Most common churn risk factor affects {top_risk['count']} users",
                    supporting_data=top_risk,
                    confidence_score=0.8,
                    impact_estimate="high",
                    actionability_score=0.8
                ))

        except Exception as e:
            logger.error(f"Error generating behavioral insights: {e}")

        return insights

    async def _generate_cross_functional_insights(self, data: Dict[str, Any]) -> List[ImprovementInsight]:
        """Generate insights that span multiple data sources"""
        insights = []

        try:
            # Example: Correlate low health scores with feedback themes
            behavior_data = data.get("behavior", {})
            feedback_data = data.get("feedback", {})

            at_risk_users = (
                behavior_data.get("health_score_distribution", {}).get("at_risk", 0) +
                behavior_data.get("health_score_distribution", {}).get("critical", 0)
            )

            performance_complaints = 0
            for theme in feedback_data.get("common_themes", []):
                if theme["theme"] == "performance":
                    performance_complaints = theme["count"]

            if at_risk_users > 10 and performance_complaints > 5:
                insights.append(ImprovementInsight(
                    insight_id="performance_health_correlation",
                    category="cross_functional",
                    title="Performance Issues Correlate with User Health",
                    description=f"{at_risk_users} at-risk users coincides with {performance_complaints} performance complaints",
                    supporting_data={
                        "at_risk_users": at_risk_users,
                        "performance_complaints": performance_complaints
                    },
                    confidence_score=0.75,
                    impact_estimate="high",
                    actionability_score=0.85
                ))

        except Exception as e:
            logger.error(f"Error generating cross-functional insights: {e}")

        return insights


class ActionPlanner:
    """Creates actionable improvement plans from insights"""

    def __init__(self, db: Session):
        self.db = db

    async def create_action_plans(
        self,
        insights: List[ImprovementInsight],
        opportunities: List[ImprovementOpportunity]
    ) -> List[ActionPlan]:
        """Create actionable improvement plans"""
        try:
            action_plans = []

            # Create plans from top insights
            top_insights = insights[:10]  # Top 10 insights
            for insight in top_insights:
                plan = await self._create_plan_from_insight(insight)
                if plan:
                    action_plans.append(plan)

            # Create plans from improvement opportunities
            for opportunity in opportunities[:5]:  # Top 5 opportunities
                plan = await self._create_plan_from_opportunity(opportunity)
                if plan:
                    action_plans.append(plan)

            # Prioritize and schedule plans
            prioritized_plans = await self._prioritize_action_plans(action_plans)

            logger.info(f"Created {len(prioritized_plans)} action plans")
            return prioritized_plans

        except Exception as e:
            logger.error(f"Error creating action plans: {e}")
            return []

    async def _create_plan_from_insight(self, insight: ImprovementInsight) -> Optional[ActionPlan]:
        """Create action plan from insight"""
        try:
            # Determine plan details based on insight category
            plan_details = await self._get_plan_template(insight)

            if not plan_details:
                return None

            plan = ActionPlan(
                plan_id=f"plan_{insight.insight_id}_{datetime.utcnow().strftime('%Y%m%d')}",
                opportunity_id=insight.insight_id,
                title=plan_details["title"],
                description=plan_details["description"],
                owner=plan_details["owner"],
                priority=plan_details["priority"],
                estimated_effort_weeks=plan_details["effort_weeks"],
                success_criteria=plan_details["success_criteria"],
                dependencies=plan_details["dependencies"],
                target_completion=datetime.utcnow() + timedelta(weeks=plan_details["effort_weeks"]),
                status=ActionStatus.PLANNED
            )

            return plan

        except Exception as e:
            logger.error(f"Error creating plan from insight: {e}")
            return None

    async def _create_plan_from_opportunity(self, opportunity: ImprovementOpportunity) -> Optional[ActionPlan]:
        """Create action plan from opportunity"""
        try:
            # Map effort estimate to weeks
            effort_weeks = {
                "Small (1-2 weeks)": 2,
                "Medium (3-5 weeks)": 4,
                "Large (6-12 weeks)": 8
            }.get(opportunity.effort_estimate, 4)

            # Determine priority
            if opportunity.impact_score > 15:
                priority = ImprovementPriority.CRITICAL
            elif opportunity.impact_score > 10:
                priority = ImprovementPriority.HIGH
            elif opportunity.impact_score > 5:
                priority = ImprovementPriority.MEDIUM
            else:
                priority = ImprovementPriority.LOW

            plan = ActionPlan(
                plan_id=f"opp_{opportunity.area}_{datetime.utcnow().strftime('%Y%m%d')}",
                opportunity_id=opportunity.area,
                title=f"Address {opportunity.area} Improvement",
                description=opportunity.description,
                owner=await self._assign_owner(opportunity.area),
                priority=priority,
                estimated_effort_weeks=effort_weeks,
                success_criteria=[
                    f"Reduce {opportunity.area} complaints by 50%",
                    f"Improve related metrics by 20%",
                    "Achieve user satisfaction score >4.0"
                ],
                dependencies=[],
                target_completion=datetime.utcnow() + timedelta(weeks=effort_weeks),
                status=ActionStatus.PLANNED
            )

            return plan

        except Exception as e:
            logger.error(f"Error creating plan from opportunity: {e}")
            return None

    async def _get_plan_template(self, insight: ImprovementInsight) -> Optional[Dict]:
        """Get plan template based on insight type"""
        templates = {
            "metrics": {
                "title": f"Improve {insight.title}",
                "description": f"Action plan to address declining metric: {insight.description}",
                "owner": "product_team",
                "priority": ImprovementPriority.HIGH,
                "effort_weeks": 3,
                "success_criteria": ["Metric trend reversal", "20% improvement in 30 days"],
                "dependencies": ["data_analysis", "stakeholder_alignment"]
            },
            "feedback": {
                "title": f"Address {insight.title}",
                "description": f"Resolve user feedback issues: {insight.description}",
                "owner": "customer_success",
                "priority": ImprovementPriority.MEDIUM,
                "effort_weeks": 2,
                "success_criteria": ["Reduce feedback volume by 40%", "Improve satisfaction"],
                "dependencies": ["root_cause_analysis"]
            },
            "behavior": {
                "title": f"Improve {insight.title}",
                "description": f"Address behavioral pattern: {insight.description}",
                "owner": "customer_success",
                "priority": ImprovementPriority.HIGH,
                "effort_weeks": 4,
                "success_criteria": ["Reduce at-risk users by 30%", "Improve health scores"],
                "dependencies": ["user_research", "outreach_strategy"]
            }
        }

        return templates.get(insight.category)

    async def _assign_owner(self, area: str) -> str:
        """Assign appropriate owner based on improvement area"""
        owner_mapping = {
            "Performance": "engineering_team",
            "User Experience": "product_team",
            "Features": "product_team",
            "Integration": "engineering_team",
            "Support": "customer_success",
            "Documentation": "customer_success"
        }

        return owner_mapping.get(area, "product_team")

    async def _prioritize_action_plans(self, plans: List[ActionPlan]) -> List[ActionPlan]:
        """Prioritize action plans based on multiple factors"""
        try:
            # Score plans based on priority, effort, and dependencies
            for plan in plans:
                priority_score = {
                    ImprovementPriority.CRITICAL: 10,
                    ImprovementPriority.HIGH: 8,
                    ImprovementPriority.MEDIUM: 5,
                    ImprovementPriority.LOW: 2
                }[plan.priority]

                effort_score = max(1, 10 - plan.estimated_effort_weeks)  # Lower effort = higher score
                dependency_score = max(1, 5 - len(plan.dependencies))  # Fewer deps = higher score

                plan.priority_score = (priority_score * 0.5) + (effort_score * 0.3) + (dependency_score * 0.2)

            # Sort by priority score
            plans.sort(key=lambda x: x.priority_score, reverse=True)

            return plans

        except Exception as e:
            logger.error(f"Error prioritizing action plans: {e}")
            return plans


class ImprovementCycleOrchestrator:
    """Orchestrates the complete improvement cycle"""

    def __init__(self, db: Session):
        self.db = db
        self.data_collector = DataCollector(db)
        self.insight_generator = InsightGenerator(db)
        self.action_planner = ActionPlanner(db)
        self.feedback_analyzer = FeedbackAnalyzer(db)
        self.notification_service = NotificationService()

    async def run_complete_cycle(
        self,
        cycle_period_days: int = 30
    ) -> CycleReport:
        """Run the complete improvement cycle"""
        try:
            cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=cycle_period_days)

            logger.info(f"Starting improvement cycle {cycle_id} for period {period_start} to {period_end}")

            # Step 1: Collect comprehensive data
            logger.info("Step 1: Collecting comprehensive data...")
            data = await self.data_collector.collect_comprehensive_data(period_start, period_end)

            # Step 2: Generate insights
            logger.info("Step 2: Generating insights...")
            insights = await self.insight_generator.generate_insights(data)

            # Step 3: Identify improvement opportunities
            logger.info("Step 3: Identifying improvement opportunities...")
            opportunities = await self.feedback_analyzer.identify_improvement_opportunities()

            # Step 4: Create action plans
            logger.info("Step 4: Creating action plans...")
            action_plans = await self.action_planner.create_action_plans(insights, opportunities)

            # Step 5: Store results and notify stakeholders
            logger.info("Step 5: Storing results and notifying stakeholders...")
            await self._store_cycle_results(cycle_id, insights, opportunities, action_plans)
            await self._notify_stakeholders(cycle_id, insights, action_plans)

            # Step 6: Schedule follow-up actions
            logger.info("Step 6: Scheduling follow-up actions...")
            await self._schedule_followup_actions(action_plans)

            # Step 7: Generate cycle report
            logger.info("Step 7: Generating cycle report...")
            report = await self._generate_cycle_report(
                cycle_id, period_start, period_end, insights, opportunities, action_plans, data
            )

            logger.info(f"Improvement cycle {cycle_id} completed successfully")
            return report

        except Exception as e:
            logger.error(f"Error running improvement cycle: {e}")
            raise

    async def _store_cycle_results(
        self,
        cycle_id: str,
        insights: List[ImprovementInsight],
        opportunities: List[ImprovementOpportunity],
        action_plans: List[ActionPlan]
    ):
        """Store cycle results in database"""
        try:
            # Store improvement opportunities
            for opportunity in opportunities:
                db_opportunity = ImprovementOpportunity(
                    title=opportunity.area,
                    description=opportunity.description,
                    area=opportunity.area,
                    type="enhancement",
                    impact_score=opportunity.impact_score,
                    affected_users=opportunity.affected_users,
                    effort_estimate=opportunity.effort_estimate,
                    supporting_feedback=opportunity.supporting_feedback,
                    business_priority="high" if opportunity.impact_score > 10 else "medium",
                    status="new",
                    identified_at=datetime.utcnow()
                )
                self.db.add(db_opportunity)

            # Store cycle metadata
            cycle_metadata = {
                "cycle_id": cycle_id,
                "insights_count": len(insights),
                "opportunities_count": len(opportunities),
                "action_plans_count": len(action_plans),
                "completed_at": datetime.utcnow()
            }

            # Create success metric for cycle completion
            cycle_metric = SuccessMetric(
                metric_name="improvement_cycle_completion",
                metric_type="operational",
                scope="global",
                period_start=datetime.utcnow() - timedelta(days=1),
                period_end=datetime.utcnow(),
                value=1.0,
                metadata=cycle_metadata
            )
            self.db.add(cycle_metric)

            self.db.commit()

        except Exception as e:
            logger.error(f"Error storing cycle results: {e}")
            self.db.rollback()

    async def _notify_stakeholders(
        self,
        cycle_id: str,
        insights: List[ImprovementInsight],
        action_plans: List[ActionPlan]
    ):
        """Notify stakeholders about cycle results"""
        try:
            # Notify product team
            await self.notification_service.create_notification({
                "user_id": "product_team",
                "type": "improvement_cycle_complete",
                "title": f"Improvement Cycle {cycle_id} Complete",
                "message": f"Generated {len(insights)} insights and {len(action_plans)} action plans",
                "priority": "medium",
                "metadata": {
                    "cycle_id": cycle_id,
                    "insights_count": len(insights),
                    "action_plans_count": len(action_plans)
                }
            })

            # Notify customer success team
            await self.notification_service.create_notification({
                "user_id": "customer_success",
                "type": "improvement_cycle_complete",
                "title": f"New Customer Success Insights Available",
                "message": f"Review {len(insights)} insights from latest improvement cycle",
                "priority": "medium",
                "metadata": {"cycle_id": cycle_id}
            })

            # Notify executives for critical insights
            critical_insights = [i for i in insights if i.impact_estimate == "critical"]
            if critical_insights:
                await self.notification_service.create_notification({
                    "user_id": "executives",
                    "type": "critical_insights",
                    "title": "Critical Customer Success Issues Identified",
                    "message": f"{len(critical_insights)} critical issues require immediate attention",
                    "priority": "urgent",
                    "metadata": {
                        "cycle_id": cycle_id,
                        "critical_count": len(critical_insights)
                    }
                })

        except Exception as e:
            logger.error(f"Error notifying stakeholders: {e}")

    async def _schedule_followup_actions(self, action_plans: List[ActionPlan]):
        """Schedule follow-up actions for high-priority plans"""
        try:
            high_priority_plans = [p for p in action_plans if p.priority in [ImprovementPriority.CRITICAL, ImprovementPriority.HIGH]]

            for plan in high_priority_plans[:5]:  # Top 5 high-priority plans
                # Schedule reminder notifications
                reminder_date = plan.target_completion - timedelta(weeks=1)

                await self.notification_service.create_notification({
                    "user_id": plan.owner,
                    "type": "action_plan_reminder",
                    "title": f"Action Plan Due Soon: {plan.title}",
                    "message": f"Target completion: {plan.target_completion.strftime('%Y-%m-%d')}",
                    "priority": "medium",
                    "scheduled_for": reminder_date,
                    "metadata": {"plan_id": plan.plan_id}
                })

        except Exception as e:
            logger.error(f"Error scheduling follow-up actions: {e}")

    async def _generate_cycle_report(
        self,
        cycle_id: str,
        period_start: datetime,
        period_end: datetime,
        insights: List[ImprovementInsight],
        opportunities: List[ImprovementOpportunity],
        action_plans: List[ActionPlan],
        data: Dict
    ) -> CycleReport:
        """Generate comprehensive cycle report"""
        try:
            # Calculate metrics improvements (simplified)
            metrics_improved = len([i for i in insights if i.category == "metrics"])

            # Calculate user satisfaction change
            satisfaction_change = await self._calculate_satisfaction_change(period_start, period_end)

            # Generate business impact summary
            business_impact = {
                "potential_churn_prevention": len([i for i in insights if "churn" in i.title.lower()]),
                "user_experience_improvements": len([i for i in insights if i.category == "feedback"]),
                "operational_efficiencies": len([p for p in action_plans if "efficiency" in p.description.lower()]),
                "revenue_impact_estimated": sum(o.potential_value or 0 for o in opportunities)
            }

            # Calculate next cycle date
            next_cycle_date = period_end + timedelta(days=30)

            report = CycleReport(
                cycle_id=cycle_id,
                period_start=period_start,
                period_end=period_end,
                insights_generated=len(insights),
                opportunities_identified=len(opportunities),
                action_plans_created=len(action_plans),
                metrics_improved=metrics_improved,
                user_satisfaction_change=satisfaction_change,
                business_impact_summary=business_impact,
                next_cycle_date=next_cycle_date
            )

            return report

        except Exception as e:
            logger.error(f"Error generating cycle report: {e}")
            return CycleReport(
                cycle_id=cycle_id,
                period_start=period_start,
                period_end=period_end,
                insights_generated=len(insights),
                opportunities_identified=len(opportunities),
                action_plans_created=len(action_plans),
                metrics_improved=0,
                user_satisfaction_change=0.0,
                business_impact_summary={},
                next_cycle_date=period_end + timedelta(days=30)
            )

    async def _calculate_satisfaction_change(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> float:
        """Calculate change in user satisfaction"""
        try:
            # Get satisfaction metrics for current period
            current_satisfaction = self.db.query(SuccessMetric).filter(
                and_(
                    SuccessMetric.metric_name == "user_satisfaction",
                    SuccessMetric.period_start >= period_start,
                    SuccessMetric.period_end <= period_end
                )
            ).first()

            # Get satisfaction metrics for previous period
            prev_period_start = period_start - timedelta(days=30)
            prev_period_end = period_start

            previous_satisfaction = self.db.query(SuccessMetric).filter(
                and_(
                    SuccessMetric.metric_name == "user_satisfaction",
                    SuccessMetric.period_start >= prev_period_start,
                    SuccessMetric.period_end <= prev_period_end
                )
            ).first()

            if current_satisfaction and previous_satisfaction:
                return current_satisfaction.value - previous_satisfaction.value
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating satisfaction change: {e}")
            return 0.0