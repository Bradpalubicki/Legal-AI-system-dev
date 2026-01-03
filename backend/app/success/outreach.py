"""
Proactive Customer Success Outreach Module

Handles automated and triggered outreach based on:
- Usage monitoring
- Health scores
- Risk detection
- Success milestones
- Check-in automation
- Renewal management
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db
from .metrics import SuccessMetricsCalculator, HealthScoreStatus, ChurnPrediction, User, Client, UserActivity, FeatureUsage
from ..models.success_tracking import OutreachAction as OutreachActionModel
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
class EmailService:
    async def send_email(self, to_email, subject, body, template_name):
        return {"success": True, "message": "Email sent"}

class NotificationService:
    async def create_notification(self, data):
        return {"success": True, "notification_id": "mock_id"}

class EmailTemplate:
    def __init__(self):
        self.name = None
        self.subject = None
        self.body = None

class OutreachCampaign:
    def __init__(self):
        self.id = None

class UserMessage:
    def __init__(self):
        self.id = None


class OutreachType(Enum):
    ONBOARDING = "onboarding"
    FEATURE_ADOPTION = "feature_adoption"
    HEALTH_CHECK = "health_check"
    CHURN_PREVENTION = "churn_prevention"
    SUCCESS_CELEBRATION = "success_celebration"
    RENEWAL_REMINDER = "renewal_reminder"
    UPSELL = "upsell"
    SUPPORT_FOLLOWUP = "support_followup"
    FEEDBACK_REQUEST = "feedback_request"


class OutreachPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class OutreachChannel(Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    PHONE = "phone"
    SLACK = "slack"


@dataclass
class OutreachTrigger:
    trigger_id: str
    name: str
    description: str
    conditions: Dict
    outreach_type: OutreachType
    priority: OutreachPriority
    delay_minutes: int = 0
    max_frequency_days: int = 7
    enabled: bool = True


@dataclass
class OutreachActionDataData:
    user_id: str
    client_id: str
    trigger_id: str
    outreach_type: OutreachType
    priority: OutreachPriority
    channel: OutreachChannel
    template_name: str
    context_data: Dict
    scheduled_for: datetime
    created_at: datetime
    executed_at: Optional[datetime] = None
    success: Optional[bool] = None
    response_data: Optional[Dict] = None


@dataclass
class SuccessMilestone:
    milestone_id: str
    name: str
    description: str
    conditions: Dict
    celebration_template: str
    next_milestone: Optional[str] = None


class ProactiveOutreachEngine:
    """Main engine for proactive customer success outreach"""

    def __init__(self, db: Session):
        self.db = db
        self.metrics_calculator = SuccessMetricsCalculator(db)
        self.email_service = EmailService()
        self.notification_service = NotificationService()
        self.triggers = self._initialize_triggers()
        self.milestones = self._initialize_milestones()

    def _initialize_triggers(self) -> List[OutreachTrigger]:
        """Initialize standard outreach triggers"""
        return [
            # Onboarding triggers
            OutreachTrigger(
                trigger_id="onboarding_day3_incomplete",
                name="Onboarding Incomplete - Day 3",
                description="User hasn't completed onboarding after 3 days",
                conditions={
                    "days_since_signup": 3,
                    "onboarding_completed": False,
                    "onboarding_progress": "<50%"
                },
                outreach_type=OutreachType.ONBOARDING,
                priority=OutreachPriority.HIGH,
                delay_minutes=0,
                max_frequency_days=7
            ),

            OutreachTrigger(
                trigger_id="first_document_upload_reminder",
                name="First Document Upload Reminder",
                description="Encourage first document upload after profile setup",
                conditions={
                    "profile_setup": True,
                    "documents_uploaded": 0,
                    "days_since_signup": 1
                },
                outreach_type=OutreachType.ONBOARDING,
                priority=OutreachPriority.MEDIUM,
                delay_minutes=1440  # 24 hours
            ),

            # Usage monitoring triggers
            OutreachTrigger(
                trigger_id="inactive_user_7days",
                name="Inactive User - 7 Days",
                description="User hasn't logged in for 7 days",
                conditions={
                    "days_since_last_login": 7,
                    "lifetime_value": ">$100"
                },
                outreach_type=OutreachType.HEALTH_CHECK,
                priority=OutreachPriority.MEDIUM,
                delay_minutes=0
            ),

            OutreachTrigger(
                trigger_id="feature_usage_decline",
                name="Feature Usage Decline",
                description="50% decline in feature usage over 30 days",
                conditions={
                    "usage_decline_percentage": ">=50",
                    "time_period": "30_days"
                },
                outreach_type=OutreachType.CHURN_PREVENTION,
                priority=OutreachPriority.HIGH,
                delay_minutes=0
            ),

            # Health score triggers
            OutreachTrigger(
                trigger_id="health_score_critical",
                name="Critical Health Score",
                description="Health score dropped below 40",
                conditions={
                    "health_score": "<40",
                    "health_score_trend": "declining"
                },
                outreach_type=OutreachType.CHURN_PREVENTION,
                priority=OutreachPriority.URGENT,
                delay_minutes=0,
                max_frequency_days=3
            ),

            OutreachTrigger(
                trigger_id="health_score_at_risk",
                name="At Risk Health Score",
                description="Health score between 40-60",
                conditions={
                    "health_score": "40-60"
                },
                outreach_type=OutreachType.HEALTH_CHECK,
                priority=OutreachPriority.HIGH,
                delay_minutes=60
            ),

            # Success celebration triggers
            OutreachTrigger(
                trigger_id="first_successful_analysis",
                name="First Successful Document Analysis",
                description="Celebrate user's first document analysis",
                conditions={
                    "successful_analyses": 1,
                    "first_analysis": True
                },
                outreach_type=OutreachType.SUCCESS_CELEBRATION,
                priority=OutreachPriority.LOW,
                delay_minutes=30
            ),

            OutreachTrigger(
                trigger_id="heavy_user_milestone",
                name="Heavy User Milestone",
                description="User reached 100+ document analyses",
                conditions={
                    "successful_analyses": ">=100",
                    "milestone_100_celebrated": False
                },
                outreach_type=OutreachType.SUCCESS_CELEBRATION,
                priority=OutreachPriority.MEDIUM,
                delay_minutes=0
            ),

            # Renewal triggers
            OutreachTrigger(
                trigger_id="renewal_30days",
                name="Renewal Reminder - 30 Days",
                description="Contract renewal in 30 days",
                conditions={
                    "days_to_renewal": 30,
                    "subscription_status": "active"
                },
                outreach_type=OutreachType.RENEWAL_REMINDER,
                priority=OutreachPriority.MEDIUM,
                delay_minutes=0
            ),

            OutreachTrigger(
                trigger_id="renewal_7days_high_value",
                name="Renewal Urgent - High Value Client",
                description="High-value client renewal in 7 days",
                conditions={
                    "days_to_renewal": 7,
                    "monthly_value": ">$1000",
                    "health_score": ">70"
                },
                outreach_type=OutreachType.RENEWAL_REMINDER,
                priority=OutreachPriority.HIGH,
                delay_minutes=0
            ),

            # Support follow-up triggers
            OutreachTrigger(
                trigger_id="support_ticket_resolved_satisfaction",
                name="Support Satisfaction Follow-up",
                description="Follow up on resolved tickets for satisfaction",
                conditions={
                    "ticket_resolved": True,
                    "resolution_age_hours": 24,
                    "satisfaction_collected": False
                },
                outreach_type=OutreachType.SUPPORT_FOLLOWUP,
                priority=OutreachPriority.LOW,
                delay_minutes=1440
            )
        ]

    def _initialize_milestones(self) -> List[SuccessMilestone]:
        """Initialize success milestones for celebration"""
        return [
            SuccessMilestone(
                milestone_id="onboarding_complete",
                name="Onboarding Complete",
                description="User completed full onboarding process",
                conditions={"onboarding_completed": True},
                celebration_template="onboarding_celebration",
                next_milestone="first_month_active"
            ),

            SuccessMilestone(
                milestone_id="first_month_active",
                name="First Month Active",
                description="Active usage for 30 days",
                conditions={
                    "days_since_signup": 30,
                    "active_days_last_month": ">=20",
                    "documents_analyzed": ">=10"
                },
                celebration_template="first_month_celebration",
                next_milestone="power_user"
            ),

            SuccessMilestone(
                milestone_id="power_user",
                name="Power User",
                description="Heavy feature usage indicating expertise",
                conditions={
                    "documents_analyzed": ">=100",
                    "features_used": ">=5",
                    "avg_session_duration": ">=30min"
                },
                celebration_template="power_user_celebration",
                next_milestone="advocate"
            ),

            SuccessMilestone(
                milestone_id="advocate",
                name="Customer Advocate",
                description="Potential reference customer",
                conditions={
                    "nps_score": ">=9",
                    "tenure_months": ">=6",
                    "health_score": ">=80",
                    "feature_adoption_rate": ">=80%"
                },
                celebration_template="advocate_celebration"
            )
        ]

    async def monitor_and_trigger_outreach(self) -> List[OutreachActionDataData]:
        """Main monitoring function to identify and trigger outreach actions"""
        try:
            all_actions = []

            # Get all active users and clients
            active_users = self.db.query(User).filter(
                User.status == 'active',
                User.last_active >= datetime.utcnow() - timedelta(days=90)
            ).all()

            for user in active_users:
                user_actions = await self._evaluate_user_triggers(user)
                all_actions.extend(user_actions)

                # Check for milestone achievements
                milestone_actions = await self._check_milestone_achievements(user)
                all_actions.extend(milestone_actions)

            # Schedule all identified actions
            for action in all_actions:
                await self._schedule_outreach_action(action)

            logger.info(f"Generated {len(all_actions)} outreach actions")
            return all_actions

        except Exception as e:
            logger.error(f"Error in monitoring and triggering outreach: {e}")
            return []

    async def _evaluate_user_triggers(self, user: User) -> List[OutreachActionDataData]:
        """Evaluate all triggers for a specific user"""
        actions = []

        try:
            # Get user context data
            context = await self._build_user_context(user)

            for trigger in self.triggers:
                if not trigger.enabled:
                    continue

                # Check if trigger conditions are met
                if await self._evaluate_trigger_conditions(trigger, context):
                    # Check frequency limits
                    if await self._check_frequency_limits(user.id, trigger.trigger_id, trigger.max_frequency_days):
                        continue

                    # Determine appropriate channel
                    channel = await self._select_outreach_channel(user, trigger)

                    # Create outreach action
                    action = OutreachActionDataData(
                        user_id=user.id,
                        client_id=user.client_id,
                        trigger_id=trigger.trigger_id,
                        outreach_type=trigger.outreach_type,
                        priority=trigger.priority,
                        channel=channel,
                        template_name=await self._get_template_name(trigger, context),
                        context_data=context,
                        scheduled_for=datetime.utcnow() + timedelta(minutes=trigger.delay_minutes),
                        created_at=datetime.utcnow()
                    )

                    actions.append(action)

        except Exception as e:
            logger.error(f"Error evaluating triggers for user {user.id}: {e}")

        return actions

    async def _build_user_context(self, user: User) -> Dict:
        """Build comprehensive context data for a user"""
        try:
            # Calculate health score
            health_score, health_status = await self.metrics_calculator.calculate_health_score(user.id)

            # Get churn prediction
            churn_prediction = await self.metrics_calculator.predict_churn(user.id)

            # Calculate key metrics
            days_since_signup = (datetime.utcnow() - user.created_at).days
            days_since_last_login = (datetime.utcnow() - user.last_active).days if user.last_active else 999

            # Get usage statistics
            recent_activity = self.db.query(UserActivity).filter(
                and_(
                    UserActivity.user_id == user.id,
                    UserActivity.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()

            # Get document analysis count
            documents_analyzed = self.db.query(UserActivity).filter(
                and_(
                    UserActivity.user_id == user.id,
                    UserActivity.activity_type == 'document_analyzed'
                )
            ).count()

            # Get feature usage diversity
            unique_features = self.db.query(FeatureUsage.feature_name).filter(
                FeatureUsage.user_id == user.id
            ).distinct().count()

            # Get client information
            client = self.db.query(Client).filter(Client.id == user.client_id).first()
            days_to_renewal = 0
            if client and client.contract_end_date:
                days_to_renewal = (client.contract_end_date - datetime.utcnow().date()).days

            return {
                "user_id": user.id,
                "user_name": user.full_name,
                "user_email": user.email,
                "client_id": user.client_id,
                "client_name": client.name if client else "Unknown",
                "days_since_signup": days_since_signup,
                "days_since_last_login": days_since_last_login,
                "onboarding_completed": user.onboarding_completed,
                "onboarding_progress": user.onboarding_progress or {},
                "health_score": health_score,
                "health_status": health_status.value,
                "churn_probability": churn_prediction.churn_probability,
                "churn_risk_factors": churn_prediction.risk_factors,
                "recent_activity_count": recent_activity,
                "documents_analyzed": documents_analyzed,
                "unique_features_used": unique_features,
                "subscription_status": user.subscription_status,
                "payment_status": user.payment_status,
                "days_to_renewal": days_to_renewal,
                "monthly_value": client.monthly_value if client else 0,
                "lifetime_value": user.lifetime_value or 0
            }

        except Exception as e:
            logger.error(f"Error building context for user {user.id}: {e}")
            return {"user_id": user.id}

    async def _evaluate_trigger_conditions(self, trigger: OutreachTrigger, context: Dict) -> bool:
        """Evaluate if trigger conditions are met for the given context"""
        try:
            conditions = trigger.conditions

            for condition_key, condition_value in conditions.items():
                context_value = context.get(condition_key)

                if context_value is None:
                    return False

                # Handle different condition types
                if isinstance(condition_value, str):
                    if condition_value.startswith(">="):
                        threshold = float(condition_value[2:])
                        if float(context_value) < threshold:
                            return False
                    elif condition_value.startswith("<="):
                        threshold = float(condition_value[2:])
                        if float(context_value) > threshold:
                            return False
                    elif condition_value.startswith(">"):
                        # Handle monetary values like ">$100"
                        if condition_value.startswith(">$"):
                            threshold = float(condition_value[2:])
                            if float(context_value) <= threshold:
                                return False
                        else:
                            threshold = float(condition_value[1:])
                            if float(context_value) <= threshold:
                                return False
                    elif condition_value.startswith("<"):
                        threshold = float(condition_value[1:])
                        if float(context_value) >= threshold:
                            return False
                    elif "-" in condition_value:
                        # Range condition like "40-60"
                        min_val, max_val = map(float, condition_value.split("-"))
                        if not (min_val <= float(context_value) <= max_val):
                            return False
                    elif condition_value.endswith("%"):
                        # Percentage condition like "<50%"
                        if condition_key == "onboarding_progress":
                            progress_percentage = len([v for v in context_value.values() if v]) / len(context_value) * 100
                            threshold = float(condition_value[1:-1])
                            if progress_percentage >= threshold:
                                return False
                    else:
                        # Direct string comparison
                        if str(context_value) != condition_value:
                            return False
                else:
                    # Direct value comparison
                    if context_value != condition_value:
                        return False

            return True

        except Exception as e:
            logger.error(f"Error evaluating trigger conditions: {e}")
            return False

    async def _check_frequency_limits(self, user_id: str, trigger_id: str, max_frequency_days: int) -> bool:
        """Check if outreach frequency limits are exceeded"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_frequency_days)

            recent_outreach = self.db.query(OutreachActionData).filter(
                and_(
                    OutreachActionData.user_id == user_id,
                    OutreachActionData.trigger_id == trigger_id,
                    OutreachActionData.created_at >= cutoff_date
                )
            ).first()

            return recent_outreach is not None

        except Exception as e:
            logger.error(f"Error checking frequency limits: {e}")
            return False

    async def _select_outreach_channel(self, user: User, trigger: OutreachTrigger) -> OutreachChannel:
        """Select the most appropriate outreach channel"""
        try:
            # Priority-based channel selection
            if trigger.priority == OutreachPriority.URGENT:
                if user.phone and user.phone_verified:
                    return OutreachChannel.PHONE
                elif user.slack_user_id:
                    return OutreachChannel.SLACK
                else:
                    return OutreachChannel.EMAIL

            elif trigger.outreach_type in [OutreachType.SUCCESS_CELEBRATION, OutreachType.FEATURE_ADOPTION]:
                return OutreachChannel.IN_APP

            elif trigger.outreach_type == OutreachType.SUPPORT_FOLLOWUP:
                return OutreachChannel.EMAIL

            else:
                # Default to email for most cases
                return OutreachChannel.EMAIL

        except Exception as e:
            logger.error(f"Error selecting outreach channel: {e}")
            return OutreachChannel.EMAIL

    async def _get_template_name(self, trigger: OutreachTrigger, context: Dict) -> str:
        """Get the appropriate email template name for the trigger"""
        template_mapping = {
            "onboarding_day3_incomplete": "onboarding_reminder_day3",
            "first_document_upload_reminder": "first_document_upload",
            "inactive_user_7days": "inactive_user_reengagement",
            "feature_usage_decline": "usage_decline_concern",
            "health_score_critical": "urgent_health_check",
            "health_score_at_risk": "proactive_check_in",
            "first_successful_analysis": "first_analysis_celebration",
            "heavy_user_milestone": "milestone_100_analyses",
            "renewal_30days": "renewal_reminder_30d",
            "renewal_7days_high_value": "renewal_urgent_high_value",
            "support_ticket_resolved_satisfaction": "support_satisfaction_survey"
        }

        return template_mapping.get(trigger.trigger_id, "default_outreach")

    async def _check_milestone_achievements(self, user: User) -> List[OutreachActionData]:
        """Check if user has achieved any success milestones"""
        actions = []

        try:
            context = await self._build_user_context(user)

            for milestone in self.milestones:
                if await self._evaluate_trigger_conditions(
                    OutreachTrigger(
                        trigger_id=milestone.milestone_id,
                        name=milestone.name,
                        description=milestone.description,
                        conditions=milestone.conditions,
                        outreach_type=OutreachType.SUCCESS_CELEBRATION,
                        priority=OutreachPriority.MEDIUM
                    ),
                    context
                ):
                    # Check if milestone was already celebrated
                    existing_celebration = self.db.query(OutreachActionData).filter(
                        and_(
                            OutreachActionData.user_id == user.id,
                            OutreachActionData.template_name == milestone.celebration_template,
                            OutreachActionData.success == True
                        )
                    ).first()

                    if not existing_celebration:
                        action = OutreachActionDataData(
                            user_id=user.id,
                            client_id=user.client_id,
                            trigger_id=milestone.milestone_id,
                            outreach_type=OutreachType.SUCCESS_CELEBRATION,
                            priority=OutreachPriority.MEDIUM,
                            channel=OutreachChannel.IN_APP,
                            template_name=milestone.celebration_template,
                            context_data=context,
                            scheduled_for=datetime.utcnow(),
                            created_at=datetime.utcnow()
                        )
                        actions.append(action)

        except Exception as e:
            logger.error(f"Error checking milestone achievements for user {user.id}: {e}")

        return actions

    async def _schedule_outreach_action(self, action: OutreachActionData):
        """Schedule an outreach action for execution"""
        try:
            # Save action to database
            db_action = OutreachActionData(**asdict(action))
            self.db.add(db_action)
            self.db.commit()

            # If scheduled for immediate execution, execute now
            if action.scheduled_for <= datetime.utcnow():
                await self._execute_outreach_action(action)

        except Exception as e:
            logger.error(f"Error scheduling outreach action: {e}")

    async def _execute_outreach_action(self, action: OutreachActionData):
        """Execute a scheduled outreach action"""
        try:
            success = False
            response_data = {}

            if action.channel == OutreachChannel.EMAIL:
                success, response_data = await self._send_email_outreach(action)
            elif action.channel == OutreachChannel.IN_APP:
                success, response_data = await self._send_in_app_notification(action)
            elif action.channel == OutreachChannel.SMS:
                success, response_data = await self._send_sms_outreach(action)
            elif action.channel == OutreachChannel.SLACK:
                success, response_data = await self._send_slack_message(action)

            # Update action with execution results
            action.executed_at = datetime.utcnow()
            action.success = success
            action.response_data = response_data

            # Update in database
            db_action = self.db.query(OutreachActionData).filter(
                OutreachActionData.user_id == action.user_id,
                OutreachActionData.trigger_id == action.trigger_id,
                OutreachActionData.created_at == action.created_at
            ).first()

            if db_action:
                db_action.executed_at = action.executed_at
                db_action.success = action.success
                db_action.response_data = action.response_data
                self.db.commit()

            logger.info(f"Executed outreach action: {action.trigger_id} for user {action.user_id}, success: {success}")

        except Exception as e:
            logger.error(f"Error executing outreach action: {e}")

    async def _send_email_outreach(self, action: OutreachActionData) -> Tuple[bool, Dict]:
        """Send email-based outreach"""
        try:
            user = self.db.query(User).filter(User.id == action.user_id).first()
            if not user:
                return False, {"error": "User not found"}

            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.name == action.template_name
            ).first()

            if not template:
                return False, {"error": f"Template {action.template_name} not found"}

            # Personalize template content
            subject = template.subject.format(**action.context_data)
            body = template.body.format(**action.context_data)

            # Send email
            result = await self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                body=body,
                template_name=action.template_name
            )

            return result.get("success", False), result

        except Exception as e:
            logger.error(f"Error sending email outreach: {e}")
            return False, {"error": str(e)}

    async def _send_in_app_notification(self, action: OutreachActionData) -> Tuple[bool, Dict]:
        """Send in-app notification"""
        try:
            notification_data = {
                "user_id": action.user_id,
                "type": action.outreach_type.value,
                "priority": action.priority.value,
                "title": self._get_notification_title(action),
                "message": self._get_notification_message(action),
                "context": action.context_data
            }

            result = await self.notification_service.create_notification(notification_data)
            return result.get("success", False), result

        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
            return False, {"error": str(e)}

    async def _send_sms_outreach(self, action: OutreachActionData) -> Tuple[bool, Dict]:
        """Send SMS outreach"""
        # Placeholder for SMS implementation
        return False, {"error": "SMS outreach not implemented"}

    async def _send_slack_message(self, action: OutreachActionData) -> Tuple[bool, Dict]:
        """Send Slack message"""
        # Placeholder for Slack implementation
        return False, {"error": "Slack outreach not implemented"}

    def _get_notification_title(self, action: OutreachActionData) -> str:
        """Generate notification title based on action type"""
        titles = {
            OutreachType.ONBOARDING: "Complete Your Setup",
            OutreachType.FEATURE_ADOPTION: "Discover New Features",
            OutreachType.SUCCESS_CELEBRATION: "Congratulations!",
            OutreachType.HEALTH_CHECK: "How are things going?",
            OutreachType.RENEWAL_REMINDER: "Subscription Renewal",
            OutreachType.SUPPORT_FOLLOWUP: "How did we do?"
        }
        return titles.get(action.outreach_type, "Update from Legal AI")

    def _get_notification_message(self, action: OutreachActionData) -> str:
        """Generate notification message based on action context"""
        messages = {
            OutreachType.ONBOARDING: f"Hi {action.context_data.get('user_name', '')}, let's finish setting up your account!",
            OutreachType.SUCCESS_CELEBRATION: f"Great work! You've analyzed {action.context_data.get('documents_analyzed', 0)} documents.",
            OutreachType.HEALTH_CHECK: "We noticed you haven't been active lately. Need any help?",
            OutreachType.RENEWAL_REMINDER: f"Your subscription renews in {action.context_data.get('days_to_renewal', 0)} days."
        }
        return messages.get(action.outreach_type, "We have an update for you.")


class RenewalManager:
    """Specialized manager for subscription renewals"""

    def __init__(self, db: Session):
        self.db = db
        self.outreach_engine = ProactiveOutreachEngine(db)

    async def manage_renewals(self) -> Dict:
        """Comprehensive renewal management"""
        try:
            # Get clients with upcoming renewals
            upcoming_renewals = self.db.query(Client).filter(
                and_(
                    Client.contract_end_date.between(
                        datetime.utcnow().date(),
                        datetime.utcnow().date() + timedelta(days=90)
                    ),
                    Client.status == 'active'
                )
            ).all()

            renewal_actions = []
            at_risk_renewals = []
            healthy_renewals = []

            for client in upcoming_renewals:
                days_to_renewal = (client.contract_end_date - datetime.utcnow().date()).days

                # Calculate client health
                client_users = self.db.query(User).filter(User.client_id == client.id).all()
                health_scores = []

                for user in client_users:
                    health_score, _ = await self.outreach_engine.metrics_calculator.calculate_health_score(user.id)
                    health_scores.append(health_score)

                avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 0

                renewal_data = {
                    "client_id": client.id,
                    "client_name": client.name,
                    "days_to_renewal": days_to_renewal,
                    "monthly_value": client.monthly_value,
                    "health_score": avg_health_score,
                    "user_count": len(client_users),
                    "renewal_probability": self._calculate_renewal_probability(client, avg_health_score)
                }

                if avg_health_score < 60 or days_to_renewal <= 30:
                    at_risk_renewals.append(renewal_data)
                else:
                    healthy_renewals.append(renewal_data)

                # Generate renewal outreach actions
                for user in client_users:
                    if user.role in ['admin', 'owner']:  # Target decision makers
                        context = await self.outreach_engine._build_user_context(user)
                        context.update(renewal_data)

                        action = OutreachActionDataData(
                            user_id=user.id,
                            client_id=client.id,
                            trigger_id="renewal_management",
                            outreach_type=OutreachType.RENEWAL_REMINDER,
                            priority=OutreachPriority.HIGH if avg_health_score < 60 else OutreachPriority.MEDIUM,
                            channel=OutreachChannel.EMAIL,
                            template_name="renewal_reminder_personalized",
                            context_data=context,
                            scheduled_for=datetime.utcnow(),
                            created_at=datetime.utcnow()
                        )

                        renewal_actions.append(action)

            # Schedule all renewal actions
            for action in renewal_actions:
                await self.outreach_engine._schedule_outreach_action(action)

            return {
                "total_renewals": len(upcoming_renewals),
                "at_risk_renewals": at_risk_renewals,
                "healthy_renewals": healthy_renewals,
                "actions_scheduled": len(renewal_actions),
                "total_renewal_value": sum(c.monthly_value * 12 for c in upcoming_renewals)
            }

        except Exception as e:
            logger.error(f"Error managing renewals: {e}")
            return {"error": "Failed to manage renewals"}

    def _calculate_renewal_probability(self, client: Client, health_score: float) -> float:
        """Calculate probability of successful renewal"""
        # Base probability on health score
        base_prob = health_score / 100

        # Adjust for tenure
        months_active = (datetime.utcnow().date() - client.created_at.date()).days / 30
        tenure_bonus = min(0.2, months_active * 0.02)

        # Adjust for contract value
        value_factor = 1.0 if client.monthly_value < 1000 else 1.1

        # Adjust for payment history
        payment_penalty = 0.1 if client.payment_issues_count > 0 else 0

        renewal_probability = (base_prob + tenure_bonus) * value_factor - payment_penalty
        return max(0, min(1, renewal_probability))