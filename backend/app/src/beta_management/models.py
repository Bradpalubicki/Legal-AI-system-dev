# =============================================================================
# Legal AI System - Beta Management Models
# =============================================================================
# Database models for managing beta users, onboarding, and launch metrics
# =============================================================================

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text,
    ForeignKey, Float, JSON, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, EmailStr

Base = declarative_base()

# =============================================================================
# ENUMS
# =============================================================================

class BetaUserStatus(str, Enum):
    """Beta user status enum."""
    INVITED = "invited"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    FEEDBACK_PENDING = "feedback_pending"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CHURNED = "churned"

class OnboardingStage(str, Enum):
    """Beta user onboarding stages."""
    WELCOME = "welcome"
    TRAINING = "training"
    FIRST_DOCUMENT = "first_document"
    LEGAL_RESEARCH = "legal_research"
    COMPLIANCE_SETUP = "compliance_setup"
    CASE_MANAGEMENT = "case_management"
    FEEDBACK_COLLECTION = "feedback_collection"
    COMPLETED = "completed"

class BetaIssueStatus(str, Enum):
    """Beta issue tracking status."""
    REPORTED = "reported"
    TRIAGING = "triaging"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"

class IssuePriority(str, Enum):
    """Issue priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FeedbackType(str, Enum):
    """Types of beta feedback."""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY = "usability"
    PERFORMANCE = "performance"
    LEGAL_ACCURACY = "legal_accuracy"
    COMPLIANCE = "compliance"
    GENERAL = "general"

# =============================================================================
# BETA USER MODELS
# =============================================================================

class BetaUser(Base):
    """Beta user model with onboarding tracking."""
    __tablename__ = "beta_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    # Beta program details
    beta_cohort = Column(String(50), nullable=False)
    invited_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    invited_by = Column(UUID(as_uuid=True), nullable=True)
    status = Column(SQLEnum(BetaUserStatus), default=BetaUserStatus.INVITED)

    # Onboarding tracking
    current_stage = Column(SQLEnum(OnboardingStage), default=OnboardingStage.WELCOME)
    onboarding_started_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)

    # User profile for beta
    organization = Column(String(200), nullable=True)
    practice_areas = Column(JSON, nullable=True)  # List of practice areas
    firm_size = Column(String(50), nullable=True)
    experience_level = Column(String(50), nullable=True)

    # Engagement metrics
    first_login_at = Column(DateTime(timezone=True), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    total_sessions = Column(Integer, default=0)
    total_session_duration_minutes = Column(Integer, default=0)

    # Feature adoption tracking
    documents_processed = Column(Integer, default=0)
    research_queries = Column(Integer, default=0)
    cases_created = Column(Integer, default=0)
    ai_interactions = Column(Integer, default=0)

    # Support and feedback
    support_tickets_created = Column(Integer, default=0)
    feedback_submissions = Column(Integer, default=0)
    bug_reports_submitted = Column(Integer, default=0)
    feature_requests_submitted = Column(Integer, default=0)

    # Success metrics
    successful_workflows = Column(Integer, default=0)
    user_satisfaction_score = Column(Float, nullable=True)  # 1-10 scale
    net_promoter_score = Column(Integer, nullable=True)  # -100 to 100

    # Training and certification
    training_completed = Column(Boolean, default=False)
    training_completed_at = Column(DateTime(timezone=True), nullable=True)
    certification_achieved = Column(Boolean, default=False)

    # Exit tracking
    churn_risk_score = Column(Float, default=0.0)  # 0-1 scale
    churned_at = Column(DateTime(timezone=True), nullable=True)
    churn_reason = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # Relationships
    onboarding_progress = relationship("OnboardingProgress", back_populates="beta_user")
    feedback_entries = relationship("BetaFeedback", back_populates="beta_user")
    issues = relationship("BetaIssue", back_populates="beta_user")

class OnboardingProgress(Base):
    """Detailed onboarding progress tracking."""
    __tablename__ = "onboarding_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beta_user_id = Column(UUID(as_uuid=True), ForeignKey("beta_users.id"), nullable=False)

    stage = Column(SQLEnum(OnboardingStage), nullable=False)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Stage-specific metrics
    attempts = Column(Integer, default=1)
    time_spent_minutes = Column(Integer, default=0)
    help_requests = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)

    # Progress data
    progress_data = Column(JSON, nullable=True)  # Stage-specific completion data
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    beta_user = relationship("BetaUser", back_populates="onboarding_progress")

    __table_args__ = (
        UniqueConstraint('beta_user_id', 'stage', name='unique_user_stage'),
    )

# =============================================================================
# FEEDBACK AND ISSUE TRACKING
# =============================================================================

class BetaFeedback(Base):
    """Beta user feedback collection."""
    __tablename__ = "beta_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beta_user_id = Column(UUID(as_uuid=True), ForeignKey("beta_users.id"), nullable=False)

    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Context information
    feature_area = Column(String(100), nullable=True)
    page_url = Column(String(500), nullable=True)
    user_action = Column(String(200), nullable=True)
    browser_info = Column(JSON, nullable=True)

    # Ratings and sentiment
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    ease_of_use_rating = Column(Integer, nullable=True)  # 1-5 scale
    feature_importance = Column(Integer, nullable=True)  # 1-5 scale

    # Processing status
    reviewed = Column(Boolean, default=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)

    # Response tracking
    response_provided = Column(Boolean, default=False)
    response_content = Column(Text, nullable=True)
    response_at = Column(DateTime(timezone=True), nullable=True)

    # Implementation tracking
    implemented = Column(Boolean, default=False)
    implementation_notes = Column(Text, nullable=True)

    # Metadata
    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    priority_score = Column(Float, default=0.0)  # Calculated priority
    tags = Column(JSON, nullable=True)  # List of tags

    # Relationships
    beta_user = relationship("BetaUser", back_populates="feedback_entries")

class BetaIssue(Base):
    """Beta issue and bug tracking."""
    __tablename__ = "beta_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_number = Column(String(20), unique=True, nullable=False)
    beta_user_id = Column(UUID(as_uuid=True), ForeignKey("beta_users.id"), nullable=False)

    # Issue details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    steps_to_reproduce = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)

    # Classification
    priority = Column(SQLEnum(IssuePriority), default=IssuePriority.MEDIUM)
    status = Column(SQLEnum(BetaIssueStatus), default=BetaIssueStatus.REPORTED)
    category = Column(String(100), nullable=True)
    component = Column(String(100), nullable=True)

    # Environment information
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    screen_resolution = Column(String(20), nullable=True)

    # Error details
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Assignment and resolution
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # Timeline tracking
    reported_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolution_started_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Resolution details
    resolution_description = Column(Text, nullable=True)
    fix_version = Column(String(20), nullable=True)
    workaround = Column(Text, nullable=True)

    # Impact assessment
    users_affected = Column(Integer, default=1)
    severity_score = Column(Float, default=0.0)
    business_impact = Column(String(50), nullable=True)

    # Communication
    user_notified = Column(Boolean, default=False)
    user_notification_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    tags = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)  # File references

    # Relationships
    beta_user = relationship("BetaUser", back_populates="issues")

# =============================================================================
# LAUNCH METRICS AND MONITORING
# =============================================================================

class BetaMetric(Base):
    """Beta program metrics and KPIs."""
    __tablename__ = "beta_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Metric identification
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50), nullable=False)  # user_adoption, performance, satisfaction, etc.
    cohort = Column(String(50), nullable=True)

    # Metric values
    value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=True)
    threshold_min = Column(Float, nullable=True)
    threshold_max = Column(Float, nullable=True)

    # Time period
    measured_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    unit = Column(String(20), nullable=True)  # percentage, count, seconds, etc.
    calculation_method = Column(String(100), nullable=True)
    data_source = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Success indicators
    meets_target = Column(Boolean, nullable=True)
    trend_direction = Column(String(20), nullable=True)  # improving, declining, stable

    __table_args__ = (
        UniqueConstraint('metric_name', 'cohort', 'measured_at', name='unique_metric_measurement'),
    )

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class BetaUserInvite(BaseModel):
    """Schema for inviting beta users."""
    email: EmailStr
    first_name: str
    last_name: str
    organization: Optional[str] = None
    practice_areas: Optional[List[str]] = None
    firm_size: Optional[str] = None
    experience_level: Optional[str] = None
    beta_cohort: str
    invited_by: uuid.UUID
    notes: Optional[str] = None

class OnboardingStageUpdate(BaseModel):
    """Schema for updating onboarding progress."""
    stage: OnboardingStage
    completed: bool = False
    time_spent_minutes: Optional[int] = None
    help_requests: Optional[int] = None
    errors_encountered: Optional[int] = None
    progress_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class FeedbackSubmission(BaseModel):
    """Schema for submitting beta feedback."""
    feedback_type: FeedbackType
    title: str
    description: str
    feature_area: Optional[str] = None
    page_url: Optional[str] = None
    user_action: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    ease_of_use_rating: Optional[int] = Field(None, ge=1, le=5)
    feature_importance: Optional[int] = Field(None, ge=1, le=5)
    browser_info: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None

class IssueReport(BaseModel):
    """Schema for reporting beta issues."""
    title: str
    description: str
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    priority: IssuePriority = IssuePriority.MEDIUM
    category: Optional[str] = None
    component: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    device_type: Optional[str] = None
    screen_resolution: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    attachments: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class BetaUserStats(BaseModel):
    """Schema for beta user statistics."""
    total_invited: int
    total_active: int
    total_completed_onboarding: int
    average_onboarding_time_days: float
    retention_rate_30_days: float
    average_satisfaction_score: float
    total_feedback_submissions: int
    total_issues_reported: int
    issues_resolved_percentage: float
    feature_adoption_rates: Dict[str, float]