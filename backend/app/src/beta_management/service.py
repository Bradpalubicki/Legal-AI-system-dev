# =============================================================================
# Legal AI System - Beta Management Service
# =============================================================================
# Comprehensive beta user management, onboarding automation, and success tracking
# =============================================================================

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
import uuid
import asyncio
import logging
from statistics import mean

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_, desc, update
from fastapi import BackgroundTasks

from .models import (
    BetaUser, OnboardingProgress, BetaFeedback, BetaIssue, BetaMetric,
    BetaUserStatus, OnboardingStage, BetaIssueStatus, FeedbackType,
    BetaUserInvite, OnboardingStageUpdate, FeedbackSubmission, IssueReport
)
from ..audit.service import AuditLoggingService, AuditEventCreate, AuditEventType, AuditSeverity, AuditStatus
from ...monitoring.metrics import (
    increment_counter, set_gauge, observe_histogram,
    active_users_gauge, privileged_operations_total
)
from ..notification_service.service import NotificationService
from ..core.config import get_settings

logger = logging.getLogger(__name__)

# =============================================================================
# BETA USER MANAGEMENT SERVICE
# =============================================================================

class BetaManagementService:
    """
    Comprehensive beta user management service with automated onboarding,
    monitoring, and success tracking.
    """

    def __init__(self):
        self.audit_service = AuditLoggingService()
        self.notification_service = NotificationService()
        self.settings = get_settings()

    # =============================================================================
    # BETA USER INVITATION AND SETUP
    # =============================================================================

    async def invite_beta_user(
        self,
        db: AsyncSession,
        invite_data: BetaUserInvite,
        invited_by_user_id: uuid.UUID
    ) -> BetaUser:
        """
        Invite a new user to the beta program with comprehensive tracking.
        """
        try:
            # Create beta user record
            beta_user = BetaUser(
                user_id=uuid.uuid4(),  # Will be assigned when user accepts
                beta_cohort=invite_data.beta_cohort,
                invited_by=invited_by_user_id,
                organization=invite_data.organization,
                practice_areas=invite_data.practice_areas,
                firm_size=invite_data.firm_size,
                experience_level=invite_data.experience_level,
                notes=invite_data.notes
            )

            db.add(beta_user)
            await db.commit()
            await db.refresh(beta_user)

            # Initialize onboarding stages
            await self._initialize_onboarding_stages(db, beta_user.id)

            # Send invitation email
            await self._send_beta_invitation_email(
                email=invite_data.email,
                first_name=invite_data.first_name,
                last_name=invite_data.last_name,
                beta_user_id=beta_user.id
            )

            # Log audit event
            await self.audit_service.log_audit_event(
                db=db,
                event_data=AuditEventCreate(
                    event_type=AuditEventType.USER_CREATED,
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.SUCCESS,
                    action="beta_user_invited",
                    description=f"Beta user invited: {invite_data.email}",
                    user_id=invited_by_user_id,
                    resource_type="beta_user",
                    resource_id=str(beta_user.id),
                    details={
                        "email": invite_data.email,
                        "cohort": invite_data.beta_cohort,
                        "organization": invite_data.organization
                    }
                )
            )

            # Update metrics
            increment_counter(
                privileged_operations_total,
                {"operation_type": "beta_invite", "user_id": str(invited_by_user_id)}
            )

            logger.info(f"Beta user invited successfully: {beta_user.id}")
            return beta_user

        except Exception as e:
            logger.error(f"Failed to invite beta user: {e}")
            await db.rollback()
            raise

    async def _initialize_onboarding_stages(
        self,
        db: AsyncSession,
        beta_user_id: uuid.UUID
    ) -> None:
        """Initialize all onboarding stages for a new beta user."""
        stages = [
            OnboardingStage.WELCOME,
            OnboardingStage.TRAINING,
            OnboardingStage.FIRST_DOCUMENT,
            OnboardingStage.LEGAL_RESEARCH,
            OnboardingStage.COMPLIANCE_SETUP,
            OnboardingStage.CASE_MANAGEMENT,
            OnboardingStage.FEEDBACK_COLLECTION
        ]

        for stage in stages:
            progress = OnboardingProgress(
                beta_user_id=beta_user_id,
                stage=stage,
                completed=False
            )
            db.add(progress)

        await db.commit()

    async def _send_beta_invitation_email(
        self,
        email: str,
        first_name: str,
        last_name: str,
        beta_user_id: uuid.UUID
    ) -> None:
        """Send beta program invitation email."""
        invitation_link = f"{self.settings.FRONTEND_URL}/beta/accept/{beta_user_id}"

        email_content = f"""
        Welcome to the Legal AI System Beta Program!

        Dear {first_name} {last_name},

        You've been selected to participate in our exclusive beta program for the Legal AI System.
        This cutting-edge platform will revolutionize how legal professionals work with AI-powered
        document analysis, legal research, and case management.

        🎯 What You'll Get:
        - Early access to advanced AI legal tools
        - Personalized onboarding and training
        - Direct line to our engineering team
        - Opportunity to shape the future of legal AI

        ⚠️ IMPORTANT DISCLAIMER:
        This system is for educational and informational purposes only. All content provided
        is for learning about legal processes and does not constitute legal advice.

        🚀 Get Started:
        Click here to accept your invitation and begin your journey: {invitation_link}

        Our team will guide you through every step of the onboarding process.

        Questions? Reply to this email or contact our beta support team.

        Welcome aboard!
        The Legal AI Team
        """

        await self.notification_service.send_email(
            to_email=email,
            subject="Welcome to Legal AI System Beta Program 🚀",
            content=email_content,
            email_type="beta_invitation"
        )

    # =============================================================================
    # ONBOARDING MANAGEMENT
    # =============================================================================

    async def accept_beta_invitation(
        self,
        db: AsyncSession,
        beta_user_id: uuid.UUID,
        user_id: uuid.UUID,
        background_tasks: BackgroundTasks
    ) -> BetaUser:
        """Process beta invitation acceptance and start onboarding."""
        try:
            # Get beta user record
            result = await db.execute(
                select(BetaUser).where(BetaUser.id == beta_user_id)
            )
            beta_user = result.scalar_one_or_none()

            if not beta_user:
                raise ValueError("Beta invitation not found")

            if beta_user.status != BetaUserStatus.INVITED:
                raise ValueError("Beta invitation already processed")

            # Update beta user
            beta_user.user_id = user_id
            beta_user.status = BetaUserStatus.ONBOARDING
            beta_user.onboarding_started_at = datetime.now(timezone.utc)
            beta_user.first_login_at = datetime.now(timezone.utc)

            await db.commit()

            # Start automated onboarding sequence
            background_tasks.add_task(
                self._start_onboarding_sequence,
                beta_user_id,
                user_id
            )

            # Log audit event
            await self.audit_service.log_audit_event(
                db=db,
                event_data=AuditEventCreate(
                    event_type=AuditEventType.LOGIN_SUCCESS,
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.SUCCESS,
                    action="beta_invitation_accepted",
                    description="Beta invitation accepted and onboarding started",
                    user_id=user_id,
                    resource_type="beta_user",
                    resource_id=str(beta_user_id),
                    details={"cohort": beta_user.beta_cohort}
                )
            )

            logger.info(f"Beta invitation accepted: {beta_user_id}")
            return beta_user

        except Exception as e:
            logger.error(f"Failed to accept beta invitation: {e}")
            await db.rollback()
            raise

    async def _start_onboarding_sequence(
        self,
        beta_user_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """Start automated onboarding sequence with personalized content."""
        try:
            # Send welcome email with training materials
            await self._send_welcome_email(beta_user_id, user_id)

            # Schedule training completion check
            await asyncio.sleep(24 * 3600)  # Wait 24 hours
            await self._check_training_progress(beta_user_id)

            # Schedule follow-up communications
            await self._schedule_onboarding_followups(beta_user_id)

        except Exception as e:
            logger.error(f"Failed to start onboarding sequence: {e}")

    async def _send_welcome_email(
        self,
        beta_user_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """Send personalized welcome email with training materials."""
        training_portal_url = f"{self.settings.FRONTEND_URL}/beta/training"

        welcome_content = f"""
        🎉 Welcome to Legal AI System Beta!

        Congratulations on joining our exclusive beta program! You're now part of a select group
        shaping the future of legal AI technology.

        📚 Your Beta Journey Starts Here:

        1. TRAINING PORTAL (Start Now!)
           Complete our interactive training modules: {training_portal_url}
           - Platform Overview (10 minutes)
           - Document Analysis Basics (15 minutes)
           - Legal Research Tools (20 minutes)
           - Compliance & Security (10 minutes)

        2. FIRST TASK: Process Your First Document
           We'll guide you through uploading and analyzing your first legal document

        3. EXPLORE FEATURES
           - AI-powered legal research
           - Case management tools
           - Compliance checking

        4. PROVIDE FEEDBACK
           Your insights directly influence our development roadmap

        💬 DEDICATED SUPPORT:
        - Beta Support Channel: Available 24/7
        - Weekly Office Hours: Tuesdays 2-3 PM EST
        - Direct Line to Engineering Team

        ⚠️ BETA DISCLAIMER:
        As a beta participant, you may encounter bugs or incomplete features.
        Your feedback helps us perfect the system before public launch.

        🎯 SUCCESS METRICS:
        We'll track your progress and ensure you're getting maximum value from the platform.

        Ready to revolutionize your legal practice? Start with the training portal!

        Questions? Hit reply or use our in-app chat.

        Best regards,
        The Legal AI Beta Team
        """

        await self.notification_service.send_email(
            to_user_id=user_id,
            subject="🎉 Your Legal AI Beta Journey Begins Now!",
            content=welcome_content,
            email_type="beta_welcome"
        )

    async def update_onboarding_progress(
        self,
        db: AsyncSession,
        beta_user_id: uuid.UUID,
        stage_update: OnboardingStageUpdate
    ) -> OnboardingProgress:
        """Update onboarding progress for a specific stage."""
        try:
            # Get or create progress record
            result = await db.execute(
                select(OnboardingProgress).where(
                    and_(
                        OnboardingProgress.beta_user_id == beta_user_id,
                        OnboardingProgress.stage == stage_update.stage
                    )
                )
            )
            progress = result.scalar_one_or_none()

            if not progress:
                progress = OnboardingProgress(
                    beta_user_id=beta_user_id,
                    stage=stage_update.stage
                )
                db.add(progress)

            # Update progress
            if stage_update.completed and not progress.completed:
                progress.completed = True
                progress.completed_at = datetime.now(timezone.utc)

            if stage_update.time_spent_minutes:
                progress.time_spent_minutes += stage_update.time_spent_minutes

            if stage_update.help_requests:
                progress.help_requests += stage_update.help_requests

            if stage_update.errors_encountered:
                progress.errors_encountered += stage_update.errors_encountered

            if stage_update.progress_data:
                progress.progress_data = stage_update.progress_data

            if stage_update.notes:
                progress.notes = stage_update.notes

            progress.updated_at = datetime.now(timezone.utc)

            await db.commit()

            # Check if this completes overall onboarding
            await self._check_onboarding_completion(db, beta_user_id)

            # Trigger next stage guidance
            if stage_update.completed:
                await self._trigger_next_stage_guidance(beta_user_id, stage_update.stage)

            return progress

        except Exception as e:
            logger.error(f"Failed to update onboarding progress: {e}")
            await db.rollback()
            raise

    async def _check_onboarding_completion(
        self,
        db: AsyncSession,
        beta_user_id: uuid.UUID
    ) -> None:
        """Check if user has completed all onboarding stages."""
        try:
            # Count completed stages
            result = await db.execute(
                select(func.count(OnboardingProgress.id)).where(
                    and_(
                        OnboardingProgress.beta_user_id == beta_user_id,
                        OnboardingProgress.completed == True
                    )
                )
            )
            completed_stages = result.scalar()

            # Check total required stages (excluding COMPLETED)
            required_stages = len([s for s in OnboardingStage if s != OnboardingStage.COMPLETED])

            if completed_stages >= required_stages:
                # Mark onboarding as completed
                await db.execute(
                    update(BetaUser)
                    .where(BetaUser.id == beta_user_id)
                    .values(
                        status=BetaUserStatus.ACTIVE,
                        current_stage=OnboardingStage.COMPLETED,
                        onboarding_completed_at=datetime.now(timezone.utc)
                    )
                )
                await db.commit()

                # Send completion celebration email
                await self._send_onboarding_completion_email(beta_user_id)

                logger.info(f"Beta user completed onboarding: {beta_user_id}")

        except Exception as e:
            logger.error(f"Failed to check onboarding completion: {e}")

    # =============================================================================
    # FEEDBACK AND ISSUE MANAGEMENT
    # =============================================================================

    async def submit_feedback(
        self,
        db: AsyncSession,
        beta_user_id: uuid.UUID,
        feedback_data: FeedbackSubmission
    ) -> BetaFeedback:
        """Submit beta feedback with automated prioritization."""
        try:
            # Calculate priority score
            priority_score = self._calculate_feedback_priority(feedback_data)

            feedback = BetaFeedback(
                beta_user_id=beta_user_id,
                feedback_type=feedback_data.feedback_type,
                title=feedback_data.title,
                description=feedback_data.description,
                feature_area=feedback_data.feature_area,
                page_url=feedback_data.page_url,
                user_action=feedback_data.user_action,
                satisfaction_rating=feedback_data.satisfaction_rating,
                ease_of_use_rating=feedback_data.ease_of_use_rating,
                feature_importance=feedback_data.feature_importance,
                browser_info=feedback_data.browser_info,
                priority_score=priority_score,
                tags=feedback_data.tags
            )

            db.add(feedback)
            await db.commit()
            await db.refresh(feedback)

            # Update beta user feedback count
            await db.execute(
                update(BetaUser)
                .where(BetaUser.id == beta_user_id)
                .values(feedback_submissions=BetaUser.feedback_submissions + 1)
            )
            await db.commit()

            # Auto-notify team for high priority feedback
            if priority_score > 0.8:
                await self._notify_team_high_priority_feedback(feedback)

            logger.info(f"Beta feedback submitted: {feedback.id}")
            return feedback

        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            await db.rollback()
            raise

    def _calculate_feedback_priority(self, feedback: FeedbackSubmission) -> float:
        """Calculate priority score for feedback (0-1 scale)."""
        score = 0.0

        # Type-based scoring
        type_weights = {
            FeedbackType.BUG_REPORT: 0.8,
            FeedbackType.LEGAL_ACCURACY: 0.9,
            FeedbackType.COMPLIANCE: 0.9,
            FeedbackType.PERFORMANCE: 0.6,
            FeedbackType.USABILITY: 0.5,
            FeedbackType.FEATURE_REQUEST: 0.4,
            FeedbackType.GENERAL: 0.2
        }
        score += type_weights.get(feedback.feedback_type, 0.5)

        # Satisfaction impact
        if feedback.satisfaction_rating:
            if feedback.satisfaction_rating <= 2:
                score += 0.3  # Low satisfaction = high priority
            elif feedback.satisfaction_rating >= 4:
                score += 0.1  # High satisfaction = lower priority

        # Feature importance
        if feedback.feature_importance:
            score += (feedback.feature_importance / 5) * 0.2

        # Normalize to 0-1 scale
        return min(score, 1.0)

    async def report_issue(
        self,
        db: AsyncSession,
        beta_user_id: uuid.UUID,
        issue_data: IssueReport
    ) -> BetaIssue:
        """Report a beta issue with automated triage."""
        try:
            # Generate issue number
            issue_count = await db.execute(
                select(func.count(BetaIssue.id))
            )
            issue_number = f"BETA-{datetime.now().year}-{issue_count.scalar() + 1:04d}"

            # Calculate severity score
            severity_score = self._calculate_issue_severity(issue_data)

            issue = BetaIssue(
                issue_number=issue_number,
                beta_user_id=beta_user_id,
                title=issue_data.title,
                description=issue_data.description,
                steps_to_reproduce=issue_data.steps_to_reproduce,
                expected_behavior=issue_data.expected_behavior,
                actual_behavior=issue_data.actual_behavior,
                priority=issue_data.priority,
                category=issue_data.category,
                component=issue_data.component,
                browser=issue_data.browser,
                os=issue_data.os,
                device_type=issue_data.device_type,
                screen_resolution=issue_data.screen_resolution,
                error_message=issue_data.error_message,
                error_code=issue_data.error_code,
                severity_score=severity_score,
                tags=issue_data.tags,
                attachments=issue_data.attachments
            )

            db.add(issue)
            await db.commit()
            await db.refresh(issue)

            # Update beta user bug report count
            await db.execute(
                update(BetaUser)
                .where(BetaUser.id == beta_user_id)
                .values(bug_reports_submitted=BetaUser.bug_reports_submitted + 1)
            )
            await db.commit()

            # Auto-assign critical issues
            if severity_score > 0.8:
                await self._auto_assign_critical_issue(issue)

            # Notify engineering team
            await self._notify_engineering_team(issue)

            logger.info(f"Beta issue reported: {issue_number}")
            return issue

        except Exception as e:
            logger.error(f"Failed to report issue: {e}")
            await db.rollback()
            raise

    def _calculate_issue_severity(self, issue: IssueReport) -> float:
        """Calculate issue severity score (0-1 scale)."""
        score = 0.0

        # Priority-based scoring
        priority_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }
        score += priority_weights.get(issue.priority.value, 0.5)

        # Error indicators
        if issue.error_message or issue.error_code:
            score += 0.2

        # Category impact
        critical_categories = ["authentication", "data_loss", "security", "compliance"]
        if issue.category and issue.category.lower() in critical_categories:
            score += 0.3

        return min(score, 1.0)

    # =============================================================================
    # METRICS AND MONITORING
    # =============================================================================

    async def calculate_beta_metrics(
        self,
        db: AsyncSession,
        cohort: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive beta program metrics."""
        try:
            # Base query for cohort filtering
            base_query = select(BetaUser)
            if cohort:
                base_query = base_query.where(BetaUser.beta_cohort == cohort)

            # User adoption metrics
            total_invited = await db.execute(base_query)
            total_invited_count = len(total_invited.scalars().all())

            active_users = await db.execute(
                base_query.where(BetaUser.status == BetaUserStatus.ACTIVE)
            )
            active_count = len(active_users.scalars().all())

            completed_onboarding = await db.execute(
                base_query.where(BetaUser.onboarding_completed_at.isnot(None))
            )
            completed_count = len(completed_onboarding.scalars().all())

            # Engagement metrics
            result = await db.execute(
                select(
                    func.avg(BetaUser.total_sessions),
                    func.avg(BetaUser.total_session_duration_minutes),
                    func.avg(BetaUser.user_satisfaction_score),
                    func.sum(BetaUser.documents_processed),
                    func.sum(BetaUser.research_queries),
                    func.sum(BetaUser.feedback_submissions),
                    func.sum(BetaUser.bug_reports_submitted)
                ).select_from(base_query.subquery())
            )
            engagement_stats = result.first()

            # Onboarding performance
            onboarding_times = await db.execute(
                select(
                    func.extract('epoch',
                        BetaUser.onboarding_completed_at - BetaUser.onboarding_started_at
                    ) / 86400  # Convert to days
                ).where(
                    and_(
                        BetaUser.onboarding_started_at.isnot(None),
                        BetaUser.onboarding_completed_at.isnot(None)
                    )
                )
            )
            avg_onboarding_days = mean([t[0] for t in onboarding_times.all()]) if onboarding_times.rowcount > 0 else 0

            # Issue resolution metrics
            total_issues = await db.execute(
                select(func.count(BetaIssue.id)).where(
                    BetaIssue.beta_user_id.in_(
                        select(BetaUser.id).where(base_query.whereclause)
                    )
                )
            )
            total_issues_count = total_issues.scalar()

            resolved_issues = await db.execute(
                select(func.count(BetaIssue.id)).where(
                    and_(
                        BetaIssue.beta_user_id.in_(
                            select(BetaUser.id).where(base_query.whereclause)
                        ),
                        BetaIssue.status == BetaIssueStatus.RESOLVED
                    )
                )
            )
            resolved_count = resolved_issues.scalar()

            metrics = {
                "user_adoption": {
                    "total_invited": total_invited_count,
                    "total_active": active_count,
                    "activation_rate": active_count / max(total_invited_count, 1),
                    "completed_onboarding": completed_count,
                    "onboarding_completion_rate": completed_count / max(total_invited_count, 1)
                },
                "engagement": {
                    "avg_sessions_per_user": engagement_stats[0] or 0,
                    "avg_session_duration_minutes": engagement_stats[1] or 0,
                    "avg_satisfaction_score": engagement_stats[2] or 0,
                    "total_documents_processed": engagement_stats[3] or 0,
                    "total_research_queries": engagement_stats[4] or 0
                },
                "feedback_quality": {
                    "total_feedback_submissions": engagement_stats[5] or 0,
                    "total_bug_reports": engagement_stats[6] or 0,
                    "feedback_per_user": (engagement_stats[5] or 0) / max(active_count, 1)
                },
                "onboarding_performance": {
                    "avg_onboarding_time_days": avg_onboarding_days,
                    "onboarding_completion_rate": completed_count / max(total_invited_count, 1)
                },
                "issue_resolution": {
                    "total_issues": total_issues_count,
                    "resolved_issues": resolved_count,
                    "resolution_rate": resolved_count / max(total_issues_count, 1)
                }
            }

            # Store metrics in database
            await self._store_metrics_snapshot(db, metrics, cohort)

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate beta metrics: {e}")
            raise

    async def _store_metrics_snapshot(
        self,
        db: AsyncSession,
        metrics: Dict[str, Any],
        cohort: Optional[str]
    ) -> None:
        """Store metrics snapshot for historical tracking."""
        timestamp = datetime.now(timezone.utc)

        for category, category_metrics in metrics.items():
            for metric_name, value in category_metrics.items():
                if isinstance(value, (int, float)):
                    metric = BetaMetric(
                        metric_name=f"{category}_{metric_name}",
                        metric_category=category,
                        cohort=cohort,
                        value=float(value),
                        measured_at=timestamp
                    )
                    db.add(metric)

        await db.commit()

    async def monitor_beta_health(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Monitor beta program health and alert on issues."""
        try:
            metrics = await self.calculate_beta_metrics(db)

            health_status = {
                "overall_health": "healthy",
                "alerts": [],
                "recommendations": []
            }

            # Check critical thresholds
            activation_rate = metrics["user_adoption"]["activation_rate"]
            if activation_rate < 0.5:  # Less than 50% activation
                health_status["alerts"].append({
                    "type": "low_activation",
                    "message": f"Low activation rate: {activation_rate:.1%}",
                    "severity": "high"
                })
                health_status["overall_health"] = "warning"

            avg_satisfaction = metrics["engagement"]["avg_satisfaction_score"]
            if avg_satisfaction < 7.0:  # Less than 7/10 satisfaction
                health_status["alerts"].append({
                    "type": "low_satisfaction",
                    "message": f"Low satisfaction score: {avg_satisfaction:.1f}/10",
                    "severity": "medium"
                })

            resolution_rate = metrics["issue_resolution"]["resolution_rate"]
            if resolution_rate < 0.8:  # Less than 80% resolution
                health_status["alerts"].append({
                    "type": "low_resolution",
                    "message": f"Low issue resolution rate: {resolution_rate:.1%}",
                    "severity": "high"
                })
                health_status["overall_health"] = "critical"

            # Generate recommendations
            if activation_rate < 0.7:
                health_status["recommendations"].append(
                    "Improve onboarding flow and user communication"
                )

            if avg_satisfaction < 8.0:
                health_status["recommendations"].append(
                    "Focus on user experience improvements and feature polish"
                )

            return health_status

        except Exception as e:
            logger.error(f"Failed to monitor beta health: {e}")
            return {
                "overall_health": "error",
                "alerts": [{"type": "monitoring_error", "message": str(e)}],
                "recommendations": []
            }

# =============================================================================
# SINGLETON SERVICE INSTANCE
# =============================================================================

beta_service = BetaManagementService()