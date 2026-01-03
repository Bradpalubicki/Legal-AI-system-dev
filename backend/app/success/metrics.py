"""
Customer Success Metrics Module

Tracks key success indicators for the legal AI platform including:
- Onboarding completion rate
- Feature adoption tracking
- User satisfaction (NPS)
- Support ticket resolution
- Churn prediction
- Upsell opportunities
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
import pandas as pd

from ..core.database import get_db
from ..models.success_tracking import FeatureUsageMetrics as FeatureUsage
# Mock logger - replace with actual logger import
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

try:
    from ..utils.logger import logger
except ImportError:
    logger = MockLogger()

# Mock classes for missing models - these should be replaced with actual imports
class User:
    def __init__(self):
        self.id = "mock_user_id"
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.onboarding_completed = False
        self.onboarding_progress = {}
        self.onboarding_completed_at = None
        self.client_id = "mock_client_id"
        self.full_name = "Mock User"
        self.email = "user@example.com"
        self.role = "user"
        self.payment_status = "active"
        self.subscription_status = "active"
        self.lifetime_value = 0
        self.phone = None
        self.phone_verified = False
        self.slack_user_id = None
        self.status = "active"
        self.is_admin = False

class Client:
    def __init__(self):
        self.id = None
        self.name = None
        self.contract_end_date = None
        self.created_at = None
        self.monthly_value = None
        self.storage_used_gb = None
        self.storage_limit_gb = None
        self.plan_tier = None
        self.user_limit = None
        self.per_user_cost = None
        self.api_limit = None
        self.payment_issues_count = None
        self.status = None

class UserActivity:
    def __init__(self):
        self.id = None
        self.user_id = None
        self.client_id = None
        self.activity_type = None
        self.created_at = None
        self.metadata = None

class SupportTicket:
    def __init__(self):
        self.id = None
        self.user_id = None
        self.created_at = None
        self.resolved_at = None
        self.first_response_at = None
        self.status = None
        self.escalated = None
        self.satisfaction_score = None


class HealthScoreStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AT_RISK = "at_risk"
    CRITICAL = "critical"


@dataclass
class OnboardingMetrics:
    completion_rate: float
    avg_completion_time: float
    drop_off_points: List[str]
    completed_users: int
    total_users: int


@dataclass
class FeatureAdoptionMetrics:
    feature_name: str
    adoption_rate: float
    active_users: int
    total_users: int
    avg_usage_per_user: float
    power_users: int


@dataclass
class NPSMetrics:
    nps_score: float
    promoters: int
    detractors: int
    passives: int
    total_responses: int
    response_rate: float


@dataclass
class SupportMetrics:
    avg_resolution_time: float
    first_response_time: float
    satisfaction_score: float
    ticket_volume: int
    escalation_rate: float
    resolution_rate: float


@dataclass
class ChurnPrediction:
    user_id: str
    churn_probability: float
    risk_factors: List[str]
    recommended_actions: List[str]
    days_to_predicted_churn: int


@dataclass
class UpsellOpportunity:
    client_id: str
    opportunity_type: str
    confidence_score: float
    potential_value: float
    recommended_timing: datetime
    key_indicators: List[str]


class SuccessMetricsCalculator:
    def __init__(self, db: Session):
        self.db = db

    async def calculate_onboarding_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> OnboardingMetrics:
        """Calculate onboarding completion metrics"""
        try:
            # Define onboarding steps
            onboarding_steps = [
                'profile_setup',
                'document_upload',
                'first_analysis',
                'team_invitation',
                'billing_setup'
            ]

            # Get users who started onboarding in the period
            users_query = self.db.query(User).filter(
                User.created_at.between(start_date, end_date)
            )
            total_users = users_query.count()

            if total_users == 0:
                return OnboardingMetrics(0, 0, [], 0, 0)

            # Calculate completion rates for each step
            completed_steps = {}
            drop_off_points = []

            for step in onboarding_steps:
                # Note: This query assumes onboarding_progress is a JSON field
                # For mock implementation, this will need to be handled differently
                try:
                    completed = users_query.filter(
                        User.onboarding_progress.contains({step: True})
                    ).count()
                except AttributeError:
                    # Fallback for mock implementation
                    completed = 0
                completed_steps[step] = completed / total_users

                if completed_steps[step] < 0.7:  # Less than 70% completion
                    drop_off_points.append(step)

            # Full onboarding completion
            completed_users = users_query.filter(
                User.onboarding_completed == True
            ).count()

            completion_rate = completed_users / total_users

            # Calculate average completion time
            completed_users_data = users_query.filter(
                User.onboarding_completed == True,
                User.onboarding_completed_at.isnot(None)
            ).all()

            if completed_users_data:
                completion_times = [
                    (user.onboarding_completed_at - user.created_at).total_seconds() / 3600
                    for user in completed_users_data
                ]
                avg_completion_time = sum(completion_times) / len(completion_times)
            else:
                avg_completion_time = 0

            return OnboardingMetrics(
                completion_rate=completion_rate,
                avg_completion_time=avg_completion_time,
                drop_off_points=drop_off_points,
                completed_users=completed_users,
                total_users=total_users
            )

        except Exception as e:
            logger.error(f"Error calculating onboarding metrics: {e}")
            return OnboardingMetrics(0, 0, [], 0, 0)

    async def calculate_feature_adoption(
        self,
        feature_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> FeatureAdoptionMetrics:
        """Calculate feature adoption metrics"""
        try:
            # Get total active users in period
            total_users = self.db.query(User).filter(
                User.last_active.between(start_date, end_date)
            ).count()

            if total_users == 0:
                return FeatureAdoptionMetrics(feature_name, 0, 0, 0, 0, 0)

            # Get feature usage data
            feature_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.feature_name == feature_name,
                    FeatureUsage.used_at.between(start_date, end_date)
                )
            )

            # Calculate active users for this feature
            active_users = feature_usage.distinct(FeatureUsage.user_id).count()
            adoption_rate = active_users / total_users

            # Calculate average usage per user
            usage_counts = feature_usage.with_entities(
                FeatureUsage.user_id,
                func.count(FeatureUsage.id).label('usage_count')
            ).group_by(FeatureUsage.user_id).all()

            if usage_counts:
                avg_usage_per_user = sum(count for _, count in usage_counts) / len(usage_counts)

                # Define power users (top 20% of users by usage)
                usage_values = [count for _, count in usage_counts]
                power_user_threshold = np.percentile(usage_values, 80)
                power_users = sum(1 for count in usage_values if count >= power_user_threshold)
            else:
                avg_usage_per_user = 0
                power_users = 0

            return FeatureAdoptionMetrics(
                feature_name=feature_name,
                adoption_rate=adoption_rate,
                active_users=active_users,
                total_users=total_users,
                avg_usage_per_user=avg_usage_per_user,
                power_users=power_users
            )

        except Exception as e:
            logger.error(f"Error calculating feature adoption for {feature_name}: {e}")
            return FeatureAdoptionMetrics(feature_name, 0, 0, 0, 0, 0)

    async def calculate_nps_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> NPSMetrics:
        """Calculate Net Promoter Score metrics"""
        try:
            # Get NPS survey responses
            nps_responses = self.db.query(UserActivity).filter(
                and_(
                    UserActivity.activity_type == 'nps_survey',
                    UserActivity.created_at.between(start_date, end_date),
                    UserActivity.metadata.has_key('nps_score')
                )
            ).all()

            if not nps_responses:
                return NPSMetrics(0, 0, 0, 0, 0, 0)

            scores = [int(response.metadata.get('nps_score', 0)) for response in nps_responses if response.metadata and 'nps_score' in response.metadata]

            if not scores:
                return NPSMetrics(0, 0, 0, 0, 0, 0)

            promoters = sum(1 for score in scores if score >= 9)
            detractors = sum(1 for score in scores if score <= 6)
            passives = sum(1 for score in scores if 7 <= score <= 8)
            total_responses = len(scores)

            nps_score = ((promoters - detractors) / total_responses) * 100

            # Calculate response rate (assuming we track survey sends)
            total_surveys_sent = self.db.query(UserActivity).filter(
                and_(
                    UserActivity.activity_type == 'nps_survey_sent',
                    UserActivity.created_at.between(start_date, end_date)
                )
            ).count()

            response_rate = total_responses / max(total_surveys_sent, 1)

            return NPSMetrics(
                nps_score=nps_score,
                promoters=promoters,
                detractors=detractors,
                passives=passives,
                total_responses=total_responses,
                response_rate=response_rate
            )

        except Exception as e:
            logger.error(f"Error calculating NPS metrics: {e}")
            return NPSMetrics(0, 0, 0, 0, 0, 0)

    async def calculate_support_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> SupportMetrics:
        """Calculate support ticket metrics"""
        try:
            tickets = self.db.query(SupportTicket).filter(
                SupportTicket.created_at.between(start_date, end_date)
            ).all()

            if not tickets:
                return SupportMetrics(0, 0, 0, 0, 0, 0)

            total_tickets = len(tickets)
            resolved_tickets = [t for t in tickets if t.status == 'resolved']

            # Average resolution time
            resolution_times = []
            for ticket in resolved_tickets:
                if ticket.resolved_at:
                    resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                    resolution_times.append(resolution_time)

            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

            # First response time
            first_response_times = []
            for ticket in tickets:
                if ticket.first_response_at:
                    response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
                    first_response_times.append(response_time)

            avg_first_response_time = sum(first_response_times) / len(first_response_times) if first_response_times else 0

            # Satisfaction score
            satisfaction_scores = [t.satisfaction_score for t in resolved_tickets if t.satisfaction_score]
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

            # Escalation and resolution rates
            escalated_tickets = sum(1 for t in tickets if t.escalated)
            escalation_rate = escalated_tickets / total_tickets
            resolution_rate = len(resolved_tickets) / total_tickets

            return SupportMetrics(
                avg_resolution_time=avg_resolution_time,
                first_response_time=avg_first_response_time,
                satisfaction_score=avg_satisfaction,
                ticket_volume=total_tickets,
                escalation_rate=escalation_rate,
                resolution_rate=resolution_rate
            )

        except Exception as e:
            logger.error(f"Error calculating support metrics: {e}")
            return SupportMetrics(0, 0, 0, 0, 0, 0)

    async def predict_churn(self, user_id: str) -> ChurnPrediction:
        """Predict churn probability for a specific user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ChurnPrediction(user_id, 0, [], [], 0)

            risk_factors = []
            risk_score = 0

            # Factor 1: Login frequency (30% weight)
            days_since_login = (datetime.utcnow() - user.last_active).days if user.last_active else 999
            if days_since_login > 14:
                risk_factors.append("Inactive for 14+ days")
                risk_score += 0.3
            elif days_since_login > 7:
                risk_factors.append("Low login frequency")
                risk_score += 0.15

            # Factor 2: Feature usage decline (25% weight)
            recent_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.user_id == user_id,
                    FeatureUsage.used_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()

            historical_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.user_id == user_id,
                    FeatureUsage.used_at.between(
                        datetime.utcnow() - timedelta(days=60),
                        datetime.utcnow() - timedelta(days=30)
                    )
                )
            ).count()

            if historical_usage > 0 and recent_usage < historical_usage * 0.5:
                risk_factors.append("50% decline in feature usage")
                risk_score += 0.25
            elif historical_usage > 0 and recent_usage < historical_usage * 0.7:
                risk_factors.append("Usage decline detected")
                risk_score += 0.15

            # Factor 3: Support ticket volume (20% weight)
            recent_tickets = self.db.query(SupportTicket).filter(
                and_(
                    SupportTicket.user_id == user_id,
                    SupportTicket.created_at >= datetime.utcnow() - timedelta(days=30),
                    SupportTicket.status.in_(['open', 'escalated'])
                )
            ).count()

            if recent_tickets > 3:
                risk_factors.append("Multiple unresolved support issues")
                risk_score += 0.20
            elif recent_tickets > 1:
                risk_factors.append("Recent support issues")
                risk_score += 0.10

            # Factor 4: Onboarding completion (15% weight)
            if not user.onboarding_completed:
                risk_factors.append("Incomplete onboarding")
                risk_score += 0.15

            # Factor 5: Billing issues (10% weight)
            if user.payment_status == 'failed' or user.subscription_status == 'past_due':
                risk_factors.append("Payment issues")
                risk_score += 0.10

            # Generate recommendations
            recommended_actions = []
            if "Inactive" in str(risk_factors):
                recommended_actions.append("Send re-engagement email campaign")
            if "usage decline" in str(risk_factors).lower():
                recommended_actions.append("Provide feature adoption training")
            if "support issues" in str(risk_factors).lower():
                recommended_actions.append("Priority support outreach")
            if "Incomplete onboarding" in risk_factors:
                recommended_actions.append("Complete onboarding assistance")
            if "Payment issues" in risk_factors:
                recommended_actions.append("Billing support contact")

            # Estimate days to churn based on risk score
            if risk_score >= 0.7:
                days_to_churn = 30
            elif risk_score >= 0.5:
                days_to_churn = 60
            elif risk_score >= 0.3:
                days_to_churn = 90
            else:
                days_to_churn = 180

            return ChurnPrediction(
                user_id=user_id,
                churn_probability=min(risk_score, 1.0),
                risk_factors=risk_factors,
                recommended_actions=recommended_actions,
                days_to_predicted_churn=days_to_churn
            )

        except Exception as e:
            logger.error(f"Error predicting churn for user {user_id}: {e}")
            return ChurnPrediction(user_id, 0, [], [], 0)

    async def identify_upsell_opportunities(self, client_id: str) -> List[UpsellOpportunity]:
        """Identify upsell opportunities for a client"""
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return []

            opportunities = []

            # Opportunity 1: Storage upgrade
            if client.storage_used_gb / client.storage_limit_gb > 0.8:
                opportunities.append(UpsellOpportunity(
                    client_id=client_id,
                    opportunity_type="storage_upgrade",
                    confidence_score=0.9,
                    potential_value=client.monthly_value * 0.3,
                    recommended_timing=datetime.utcnow() + timedelta(days=7),
                    key_indicators=["Storage usage > 80%"]
                ))

            # Opportunity 2: Advanced features based on usage patterns
            advanced_feature_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.client_id == client_id,
                    FeatureUsage.feature_name.in_(['advanced_analytics', 'bulk_processing', 'api_access']),
                    FeatureUsage.used_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()

            if advanced_feature_usage > 10 and client.plan_tier == 'basic':
                opportunities.append(UpsellOpportunity(
                    client_id=client_id,
                    opportunity_type="plan_upgrade",
                    confidence_score=0.75,
                    potential_value=client.monthly_value * 1.5,
                    recommended_timing=datetime.utcnow() + timedelta(days=14),
                    key_indicators=["High advanced feature usage", "Basic plan limitation"]
                ))

            # Opportunity 3: Team expansion
            active_users = self.db.query(User).filter(
                and_(
                    User.client_id == client_id,
                    User.last_active >= datetime.utcnow() - timedelta(days=7)
                )
            ).count()

            if active_users >= client.user_limit * 0.9:
                opportunities.append(UpsellOpportunity(
                    client_id=client_id,
                    opportunity_type="user_seats",
                    confidence_score=0.8,
                    potential_value=active_users * client.per_user_cost * 0.2,
                    recommended_timing=datetime.utcnow() + timedelta(days=5),
                    key_indicators=["Near user limit", "High team activity"]
                ))

            # Opportunity 4: API usage growth
            api_usage = self.db.query(UserActivity).filter(
                and_(
                    UserActivity.client_id == client_id,
                    UserActivity.activity_type == 'api_call',
                    UserActivity.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()

            if api_usage > client.api_limit * 0.8:
                opportunities.append(UpsellOpportunity(
                    client_id=client_id,
                    opportunity_type="api_upgrade",
                    confidence_score=0.85,
                    potential_value=client.monthly_value * 0.4,
                    recommended_timing=datetime.utcnow() + timedelta(days=10),
                    key_indicators=["High API usage", "Approaching limit"]
                ))

            return opportunities

        except Exception as e:
            logger.error(f"Error identifying upsell opportunities for client {client_id}: {e}")
            return []

    async def calculate_health_score(self, user_id: str) -> Tuple[float, HealthScoreStatus]:
        """Calculate overall health score for a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return 0.0, HealthScoreStatus.CRITICAL

            score_components = []

            # Login recency (25% weight)
            days_since_login = (datetime.utcnow() - user.last_active).days if user.last_active else 999
            login_score = max(0, 100 - (days_since_login * 5))
            score_components.append(login_score * 0.25)

            # Feature usage (30% weight)
            recent_usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.user_id == user_id,
                    FeatureUsage.used_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()

            usage_score = min(100, recent_usage * 5)
            score_components.append(usage_score * 0.30)

            # Support satisfaction (20% weight)
            recent_tickets = self.db.query(SupportTicket).filter(
                and_(
                    SupportTicket.user_id == user_id,
                    SupportTicket.resolved_at >= datetime.utcnow() - timedelta(days=90),
                    SupportTicket.satisfaction_score.isnot(None)
                )
            ).all()

            if recent_tickets:
                avg_satisfaction = sum(t.satisfaction_score for t in recent_tickets) / len(recent_tickets)
                support_score = avg_satisfaction * 20
            else:
                support_score = 80  # Neutral score if no recent tickets

            score_components.append(support_score * 0.20)

            # Onboarding completion (15% weight)
            onboarding_score = 100 if user.onboarding_completed else 20
            score_components.append(onboarding_score * 0.15)

            # Payment status (10% weight)
            payment_score = 100 if user.payment_status == 'active' else 0
            score_components.append(payment_score * 0.10)

            # Calculate final score
            health_score = sum(score_components)

            # Determine status
            if health_score >= 80:
                status = HealthScoreStatus.EXCELLENT
            elif health_score >= 60:
                status = HealthScoreStatus.GOOD
            elif health_score >= 40:
                status = HealthScoreStatus.AT_RISK
            else:
                status = HealthScoreStatus.CRITICAL

            return health_score, status

        except Exception as e:
            logger.error(f"Error calculating health score for user {user_id}: {e}")
            return 0.0, HealthScoreStatus.CRITICAL


class MetricsDashboard:
    """Generate comprehensive metrics dashboard data"""

    def __init__(self, db: Session):
        self.calculator = SuccessMetricsCalculator(db)

    async def generate_dashboard_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Generate complete dashboard metrics"""
        try:
            # Run all metric calculations concurrently
            tasks = [
                self.calculator.calculate_onboarding_metrics(start_date, end_date),
                self.calculator.calculate_nps_metrics(start_date, end_date),
                self.calculator.calculate_support_metrics(start_date, end_date)
            ]

            # Feature adoption for key features
            key_features = [
                'document_analysis',
                'legal_research',
                'citation_processing',
                'contract_review'
            ]

            for feature in key_features:
                tasks.append(
                    self.calculator.calculate_feature_adoption(feature, start_date, end_date)
                )

            results = await asyncio.gather(*tasks)

            onboarding_metrics = results[0]
            nps_metrics = results[1]
            support_metrics = results[2]
            feature_metrics = results[3:]

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "onboarding": {
                    "completion_rate": onboarding_metrics.completion_rate,
                    "avg_completion_time_hours": onboarding_metrics.avg_completion_time,
                    "drop_off_points": onboarding_metrics.drop_off_points,
                    "completed_users": onboarding_metrics.completed_users,
                    "total_users": onboarding_metrics.total_users
                },
                "satisfaction": {
                    "nps_score": nps_metrics.nps_score,
                    "promoters": nps_metrics.promoters,
                    "detractors": nps_metrics.detractors,
                    "response_rate": nps_metrics.response_rate
                },
                "support": {
                    "avg_resolution_hours": support_metrics.avg_resolution_time,
                    "first_response_hours": support_metrics.first_response_time,
                    "satisfaction_score": support_metrics.satisfaction_score,
                    "ticket_volume": support_metrics.ticket_volume,
                    "resolution_rate": support_metrics.resolution_rate
                },
                "feature_adoption": {
                    feature.feature_name: {
                        "adoption_rate": feature.adoption_rate,
                        "active_users": feature.active_users,
                        "avg_usage": feature.avg_usage_per_user,
                        "power_users": feature.power_users
                    }
                    for feature in feature_metrics
                }
            }

        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {"error": "Failed to generate metrics"}