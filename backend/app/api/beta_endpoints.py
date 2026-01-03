# =============================================================================
# Legal AI System - Beta Management API Endpoints
# =============================================================================
# RESTful API endpoints for beta user management, onboarding, and monitoring
# =============================================================================

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from ..src.beta_management.service import beta_service
from ..src.beta_management.models import (
    BetaUserInvite, OnboardingStageUpdate, FeedbackSubmission, IssueReport,
    BetaUserStatus, OnboardingStage, FeedbackType, IssuePriority
)
from ..src.core.database import get_db_session
from ..src.audit.service import audit_api_call, AuditEventType, AuditSeverity

router = APIRouter(prefix="/api/v1/beta", tags=["Beta Management"])
security = HTTPBearer()

# =============================================================================
# RESPONSE MODELS
# =============================================================================

class BetaUserResponse(BaseModel):
    """Response model for beta user data."""
    id: uuid.UUID
    user_id: uuid.UUID
    beta_cohort: str
    status: BetaUserStatus
    current_stage: OnboardingStage
    invited_at: datetime
    onboarding_started_at: Optional[datetime]
    onboarding_completed_at: Optional[datetime]

    # Engagement metrics
    total_sessions: int
    documents_processed: int
    research_queries: int
    feedback_submissions: int
    bug_reports_submitted: int

    # Success indicators
    user_satisfaction_score: Optional[float]
    training_completed: bool

class OnboardingProgressResponse(BaseModel):
    """Response model for onboarding progress."""
    stage: OnboardingStage
    completed: bool
    started_at: datetime
    completed_at: Optional[datetime]
    time_spent_minutes: int
    help_requests: int
    errors_encountered: int

class BetaMetricsResponse(BaseModel):
    """Response model for beta metrics."""
    user_adoption: Dict[str, Any]
    engagement: Dict[str, Any]
    feedback_quality: Dict[str, Any]
    onboarding_performance: Dict[str, Any]
    issue_resolution: Dict[str, Any]
    generated_at: datetime

class BetaHealthResponse(BaseModel):
    """Response model for beta health monitoring."""
    overall_health: str
    alerts: List[Dict[str, Any]]
    recommendations: List[str]
    checked_at: datetime

# =============================================================================
# ADMIN ENDPOINTS - BETA PROGRAM MANAGEMENT
# =============================================================================

@router.post(
    "/users/invite",
    response_model=BetaUserResponse,
    summary="Invite user to beta program",
    description="Invite a new user to join the beta program with automated onboarding"
)
@audit_api_call(
    event_type=AuditEventType.USER_CREATED,
    action="invite_beta_user",
    resource_type="beta_user",
    severity=AuditSeverity.MEDIUM
)
async def invite_beta_user(
    invite_data: BetaUserInvite,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_admin_user),  # Admin only
    token: str = Depends(security)
):
    """
    Invite a new user to the beta program.

    - **email**: User's email address
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **organization**: User's organization (optional)
    - **practice_areas**: List of practice areas (optional)
    - **beta_cohort**: Beta cohort identifier

    Only admin users can invite beta users.
    """
    try:
        beta_user = await beta_service.invite_beta_user(
            db=db,
            invite_data=invite_data,
            invited_by_user_id=current_user.id
        )

        return BetaUserResponse.from_orm(beta_user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to invite beta user: {str(e)}"
        )

@router.get(
    "/users",
    response_model=List[BetaUserResponse],
    summary="List beta users",
    description="Get list of all beta users with filtering options"
)
async def list_beta_users(
    cohort: Optional[str] = Query(None, description="Filter by beta cohort"),
    status_filter: Optional[BetaUserStatus] = Query(None, description="Filter by user status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_admin_user),
    token: str = Depends(security)
):
    """
    Get list of beta users with optional filtering.

    Supports filtering by:
    - Beta cohort
    - User status
    - Pagination with limit/offset
    """
    try:
        users = await beta_service.list_beta_users(
            db=db,
            cohort=cohort,
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )

        return [BetaUserResponse.from_orm(user) for user in users]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list beta users: {str(e)}"
        )

@router.get(
    "/metrics",
    response_model=BetaMetricsResponse,
    summary="Get beta program metrics",
    description="Comprehensive metrics for beta program performance"
)
async def get_beta_metrics(
    cohort: Optional[str] = Query(None, description="Filter metrics by beta cohort"),
    start_date: Optional[datetime] = Query(None, description="Start date for metrics period"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics period"),
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_admin_user),
    token: str = Depends(security)
):
    """
    Get comprehensive beta program metrics including:

    - User adoption rates
    - Engagement metrics
    - Feedback quality
    - Onboarding performance
    - Issue resolution stats
    """
    try:
        metrics = await beta_service.calculate_beta_metrics(
            db=db,
            cohort=cohort,
            start_date=start_date,
            end_date=end_date
        )

        return BetaMetricsResponse(
            **metrics,
            generated_at=datetime.now(timezone.utc)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get beta metrics: {str(e)}"
        )

@router.get(
    "/health",
    response_model=BetaHealthResponse,
    summary="Monitor beta program health",
    description="Real-time health monitoring with alerts and recommendations"
)
async def monitor_beta_health(
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_admin_user),
    token: str = Depends(security)
):
    """
    Monitor beta program health and get alerts for issues requiring attention.

    Returns:
    - Overall health status
    - Critical alerts
    - Improvement recommendations
    """
    try:
        health_status = await beta_service.monitor_beta_health(db=db)

        return BetaHealthResponse(
            **health_status,
            checked_at=datetime.now(timezone.utc)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check beta health: {str(e)}"
        )

# =============================================================================
# BETA USER ENDPOINTS - ONBOARDING AND PARTICIPATION
# =============================================================================

@router.post(
    "/accept/{beta_user_id}",
    response_model=BetaUserResponse,
    summary="Accept beta invitation",
    description="Accept beta program invitation and start onboarding"
)
async def accept_beta_invitation(
    beta_user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
    token: str = Depends(security)
):
    """
    Accept beta program invitation and begin automated onboarding sequence.

    This endpoint:
    - Validates the invitation
    - Links the user account to beta program
    - Starts personalized onboarding flow
    - Sends welcome materials
    """
    try:
        beta_user = await beta_service.accept_beta_invitation(
            db=db,
            beta_user_id=beta_user_id,
            user_id=current_user.id,
            background_tasks=background_tasks
        )

        return BetaUserResponse.from_orm(beta_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept beta invitation: {str(e)}"
        )

@router.get(
    "/profile",
    response_model=BetaUserResponse,
    summary="Get beta user profile",
    description="Get current user's beta program profile and progress"
)
async def get_beta_profile(
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_beta_user),
    token: str = Depends(security)
):
    """Get the current user's beta program profile and engagement statistics."""
    try:
        beta_user = await beta_service.get_beta_user_by_user_id(
            db=db,
            user_id=current_user.id
        )

        if not beta_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beta user profile not found"
            )

        return BetaUserResponse.from_orm(beta_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get beta profile: {str(e)}"
        )

@router.get(
    "/onboarding/progress",
    response_model=List[OnboardingProgressResponse],
    summary="Get onboarding progress",
    description="Get detailed onboarding progress for current beta user"
)
async def get_onboarding_progress(
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_beta_user),
    token: str = Depends(security)
):
    """Get detailed onboarding progress for the current beta user."""
    try:
        beta_user = await beta_service.get_beta_user_by_user_id(
            db=db,
            user_id=current_user.id
        )

        if not beta_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beta user not found"
            )

        progress = await beta_service.get_onboarding_progress(
            db=db,
            beta_user_id=beta_user.id
        )

        return [OnboardingProgressResponse.from_orm(p) for p in progress]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding progress: {str(e)}"
        )

@router.post(
    "/onboarding/update",
    response_model=OnboardingProgressResponse,
    summary="Update onboarding progress",
    description="Update progress for a specific onboarding stage"
)
@audit_api_call(
    event_type=AuditEventType.USER_PROFILE_UPDATED,
    action="update_onboarding_progress",
    resource_type="onboarding_progress",
    severity=AuditSeverity.LOW
)
async def update_onboarding_progress(
    stage_update: OnboardingStageUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_beta_user),
    token: str = Depends(security)
):
    """
    Update onboarding progress for a specific stage.

    Automatically triggers:
    - Next stage guidance
    - Completion celebrations
    - Progress notifications
    """
    try:
        beta_user = await beta_service.get_beta_user_by_user_id(
            db=db,
            user_id=current_user.id
        )

        if not beta_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beta user not found"
            )

        progress = await beta_service.update_onboarding_progress(
            db=db,
            beta_user_id=beta_user.id,
            stage_update=stage_update
        )

        return OnboardingProgressResponse.from_orm(progress)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update onboarding progress: {str(e)}"
        )

# =============================================================================
# FEEDBACK AND ISSUE ENDPOINTS
# =============================================================================

@router.post(
    "/feedback",
    response_model=Dict[str, str],
    summary="Submit beta feedback",
    description="Submit feedback about the beta experience"
)
@audit_api_call(
    event_type=AuditEventType.FEEDBACK_SUBMITTED,
    action="submit_beta_feedback",
    resource_type="beta_feedback",
    severity=AuditSeverity.LOW
)
async def submit_feedback(
    feedback_data: FeedbackSubmission,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_beta_user),
    token: str = Depends(security)
):
    """
    Submit feedback about the beta experience.

    Feedback types:
    - Bug reports
    - Feature requests
    - Usability issues
    - Performance problems
    - Legal accuracy concerns
    - General feedback
    """
    try:
        beta_user = await beta_service.get_beta_user_by_user_id(
            db=db,
            user_id=current_user.id
        )

        if not beta_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beta user not found"
            )

        feedback = await beta_service.submit_feedback(
            db=db,
            beta_user_id=beta_user.id,
            feedback_data=feedback_data
        )

        return {
            "message": "Feedback submitted successfully",
            "feedback_id": str(feedback.id)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.post(
    "/issues/report",
    response_model=Dict[str, str],
    summary="Report beta issue",
    description="Report a bug or technical issue"
)
@audit_api_call(
    event_type=AuditEventType.ISSUE_REPORTED,
    action="report_beta_issue",
    resource_type="beta_issue",
    severity=AuditSeverity.MEDIUM
)
async def report_issue(
    issue_data: IssueReport,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_beta_user),
    token: str = Depends(security)
):
    """
    Report a bug or technical issue encountered during beta testing.

    Include:
    - Detailed description
    - Steps to reproduce
    - Expected vs actual behavior
    - Environment information
    - Error messages (if any)
    """
    try:
        beta_user = await beta_service.get_beta_user_by_user_id(
            db=db,
            user_id=current_user.id
        )

        if not beta_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beta user not found"
            )

        issue = await beta_service.report_issue(
            db=db,
            beta_user_id=beta_user.id,
            issue_data=issue_data
        )

        return {
            "message": "Issue reported successfully",
            "issue_number": issue.issue_number,
            "issue_id": str(issue.id)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report issue: {str(e)}"
        )

# =============================================================================
# REAL-TIME MONITORING ENDPOINTS
# =============================================================================

@router.get(
    "/monitoring/realtime",
    response_model=Dict[str, Any],
    summary="Real-time beta monitoring",
    description="Get real-time beta program monitoring data"
)
async def get_realtime_monitoring(
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_admin_user),
    token: str = Depends(security)
):
    """
    Get real-time monitoring data for beta program including:

    - Active users count
    - Current issues count
    - Recent feedback
    - System health indicators
    """
    try:
        monitoring_data = await beta_service.get_realtime_monitoring_data(db=db)

        return {
            "timestamp": datetime.now(timezone.utc),
            "data": monitoring_data
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring data: {str(e)}"
        )

# =============================================================================
# UTILITY FUNCTIONS (to be implemented in auth module)
# =============================================================================

async def get_current_user():
    """Get current authenticated user (to be implemented)."""
    # This should be implemented in the auth module
    pass

async def get_current_admin_user():
    """Get current admin user (to be implemented)."""
    # This should be implemented in the auth module
    pass

async def get_current_beta_user():
    """Get current beta user (to be implemented)."""
    # This should be implemented in the auth module
    pass