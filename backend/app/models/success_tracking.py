"""
Database models for Customer Success Tracking System

Models for tracking user engagement, feedback, surveys, feature requests,
testimonials, and success metrics for the legal AI platform.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    JSON, ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class HealthScoreStatusEnum(enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AT_RISK = "at_risk"
    CRITICAL = "critical"


class FeedbackTypeEnum(enum.Enum):
    GENERAL = "general"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    IMPROVEMENT = "improvement"
    TESTIMONIAL = "testimonial"
    COMPLAINT = "complaint"
    NPS_SURVEY = "nps_survey"
    SATISFACTION = "satisfaction"
    ONBOARDING = "onboarding"
    FEATURE_FEEDBACK = "feature_feedback"


class FeedbackPriorityEnum(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatusEnum(enum.Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class SurveyTypeEnum(enum.Enum):
    NPS = "nps"
    CSAT = "csat"
    CES = "ces"
    ONBOARDING = "onboarding"
    FEATURE_FEEDBACK = "feature_feedback"
    QUARTERLY_REVIEW = "quarterly_review"
    EXIT_INTERVIEW = "exit_interview"


class OutreachTypeEnum(enum.Enum):
    ONBOARDING = "onboarding"
    FEATURE_ADOPTION = "feature_adoption"
    HEALTH_CHECK = "health_check"
    CHURN_PREVENTION = "churn_prevention"
    SUCCESS_CELEBRATION = "success_celebration"
    RENEWAL_REMINDER = "renewal_reminder"
    UPSELL = "upsell"
    SUPPORT_FOLLOWUP = "support_followup"
    FEEDBACK_REQUEST = "feedback_request"


class OutreachPriorityEnum(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class OutreachChannelEnum(enum.Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    PHONE = "phone"
    SLACK = "slack"


class UserHealthScore(Base):
    """Track user health scores over time"""
    __tablename__ = "user_health_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    health_score = Column(Float, nullable=False)
    status = Column(SQLEnum(HealthScoreStatusEnum), nullable=False)

    # Component scores
    login_score = Column(Float, nullable=True)
    usage_score = Column(Float, nullable=True)
    support_score = Column(Float, nullable=True)
    onboarding_score = Column(Float, nullable=True)
    payment_score = Column(Float, nullable=True)

    # Metadata
    calculation_date = Column(DateTime, default=datetime.utcnow)
    factors_analyzed = Column(JSON, nullable=True)  # Store factors that influenced score
    risk_indicators = Column(JSON, nullable=True)  # Store risk indicators

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="health_scores")
    client = relationship("Client", backref="user_health_scores")

    # Indexes
    __table_args__ = (
        Index('idx_user_health_date', 'user_id', 'calculation_date'),
        Index('idx_health_status', 'status'),
        Index('idx_health_score', 'health_score'),
    )


class ChurnPrediction(Base):
    """Store churn predictions for users"""
    __tablename__ = "churn_predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    churn_probability = Column(Float, nullable=False)
    days_to_predicted_churn = Column(Integer, nullable=True)

    # Risk analysis
    risk_factors = Column(JSON, nullable=True)  # List of risk factors
    risk_score_breakdown = Column(JSON, nullable=True)  # Detailed scoring

    # Recommendations
    recommended_actions = Column(JSON, nullable=True)  # List of recommended interventions
    intervention_priority = Column(SQLEnum(OutreachPriorityEnum), nullable=True)

    # Prediction metadata
    model_version = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    prediction_date = Column(DateTime, default=datetime.utcnow)

    # Outcome tracking
    actual_churn_date = Column(DateTime, nullable=True)
    prediction_accuracy = Column(Float, nullable=True)
    intervention_applied = Column(Boolean, default=False)
    intervention_success = Column(Boolean, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="churn_predictions")
    client = relationship("Client", backref="churn_predictions")

    # Indexes
    __table_args__ = (
        Index('idx_churn_probability', 'churn_probability'),
        Index('idx_churn_prediction_date', 'prediction_date'),
        Index('idx_user_churn_latest', 'user_id', 'prediction_date'),
    )


class FeatureUsageMetrics(Base):
    """Track detailed feature usage metrics"""
    __tablename__ = "feature_usage_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    feature_name = Column(String, nullable=False)
    usage_count = Column(Integer, default=0)
    session_duration_seconds = Column(Integer, nullable=True)

    # Usage patterns
    first_used_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    usage_frequency_days = Column(Float, nullable=True)  # Average days between usage

    # Adoption metrics
    adoption_stage = Column(String, nullable=True)  # trial, regular, power_user, champion
    proficiency_level = Column(String, nullable=True)  # beginner, intermediate, advanced

    # Context data
    usage_context = Column(JSON, nullable=True)  # Additional context about usage
    performance_metrics = Column(JSON, nullable=True)  # Response times, error rates, etc.

    # Aggregation period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="feature_usage_metrics")
    client = relationship("Client", backref="feature_usage_metrics")

    # Indexes
    __table_args__ = (
        Index('idx_feature_usage_user_feature', 'user_id', 'feature_name'),
        Index('idx_feature_usage_period', 'period_start', 'period_end'),
        Index('idx_feature_usage_adoption', 'adoption_stage'),
        UniqueConstraint('user_id', 'feature_name', 'period_start', name='uq_user_feature_period'),
    )


class OnboardingProgress(Base):
    """Track detailed onboarding progress"""
    __tablename__ = "onboarding_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    # Progress tracking
    current_step = Column(String, nullable=True)
    completed_steps = Column(JSON, nullable=True)  # List of completed step IDs
    total_steps = Column(Integer, nullable=True)
    completion_percentage = Column(Float, nullable=True)

    # Timing metrics
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion_date = Column(DateTime, nullable=True)

    # Step timing
    step_durations = Column(JSON, nullable=True)  # Time spent on each step
    drop_off_points = Column(JSON, nullable=True)  # Steps where users commonly drop off

    # Assistance tracking
    help_requests = Column(JSON, nullable=True)  # Support requests during onboarding
    tutorial_completion = Column(JSON, nullable=True)  # Tutorial/guide completion status

    # Completion quality
    setup_quality_score = Column(Float, nullable=True)  # How well user completed setup
    feature_activation_count = Column(Integer, default=0)  # Features activated during onboarding

    # Outcome metrics
    time_to_first_value_days = Column(Integer, nullable=True)  # Days to first meaningful use
    onboarding_satisfaction = Column(Float, nullable=True)  # Post-onboarding survey score

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="onboarding_progress")
    client = relationship("Client", backref="onboarding_progress")

    # Indexes
    __table_args__ = (
        Index('idx_onboarding_user', 'user_id'),
        Index('idx_onboarding_completion', 'completion_percentage'),
        Index('idx_onboarding_current_step', 'current_step'),
    )


class Feedback(Base):
    """General feedback from users"""
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    # Feedback content
    type = Column(SQLEnum(FeedbackTypeEnum), nullable=False)
    priority = Column(SQLEnum(FeedbackPriorityEnum), default=FeedbackPriorityEnum.MEDIUM)
    status = Column(SQLEnum(FeedbackStatusEnum), default=FeedbackStatusEnum.NEW)

    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # UI, Performance, Feature, etc.

    # Context information
    page_url = Column(String, nullable=True)
    browser_info = Column(String, nullable=True)
    screen_resolution = Column(String, nullable=True)
    device_type = Column(String, nullable=True)

    # Sentiment analysis
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    sentiment_label = Column(String, nullable=True)  # positive, negative, neutral

    # Processing information
    assigned_to = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Metadata
    issue_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags for categorization

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="feedback")
    client = relationship("Client", backref="feedback")

    # Indexes
    __table_args__ = (
        Index('idx_feedback_type', 'type'),
        Index('idx_feedback_status', 'status'),
        Index('idx_feedback_priority', 'priority'),
        Index('idx_feedback_user_date', 'user_id', 'created_at'),
    )


class FeatureRequest(Base):
    """Feature requests from users"""
    __tablename__ = "feature_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    # Request details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    use_case = Column(Text, nullable=True)
    business_justification = Column(Text, nullable=True)

    # Prioritization
    votes = Column(Integer, default=1)
    requester_count = Column(Integer, default=1)
    business_impact_score = Column(Float, nullable=True)
    technical_complexity_score = Column(Float, nullable=True)
    priority_score = Column(Float, nullable=True)

    # Development information
    estimated_effort = Column(String, nullable=True)  # Small, Medium, Large
    estimated_dev_weeks = Column(Integer, nullable=True)
    technical_feasibility = Column(Float, nullable=True)  # 1-10 scale

    # Status tracking
    status = Column(SQLEnum(FeedbackStatusEnum), default=FeedbackStatusEnum.NEW)
    implementation_status = Column(String, nullable=True)  # backlog, planned, in_progress, completed
    target_release = Column(String, nullable=True)

    # Analysis
    similar_requests = Column(JSON, nullable=True)  # List of similar request IDs
    market_research = Column(JSON, nullable=True)
    competitive_analysis = Column(JSON, nullable=True)

    # Communication
    requester_updates = Column(JSON, nullable=True)  # Updates sent to requesters
    public_roadmap_item = Column(Boolean, default=False)

    # Outcome tracking
    implemented_at = Column(DateTime, nullable=True)
    adoption_rate_post_launch = Column(Float, nullable=True)
    satisfaction_post_launch = Column(Float, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="feature_requests")
    client = relationship("Client", backref="feature_requests")

    # Indexes
    __table_args__ = (
        Index('idx_feature_request_votes', 'votes'),
        Index('idx_feature_request_priority', 'priority_score'),
        Index('idx_feature_request_status', 'status'),
    )


class BugReport(Base):
    """Bug reports from users"""
    __tablename__ = "bug_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    # Bug details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    steps_to_reproduce = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)

    # Technical information
    browser_info = Column(String, nullable=True)
    operating_system = Column(String, nullable=True)
    screen_resolution = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Attachments
    screenshots = Column(JSON, nullable=True)  # List of screenshot URLs
    log_files = Column(JSON, nullable=True)  # List of log file URLs
    screen_recording = Column(String, nullable=True)

    # Classification
    severity = Column(String, nullable=True)  # critical, high, medium, low
    bug_type = Column(String, nullable=True)  # ui, functional, performance, security
    affected_feature = Column(String, nullable=True)

    # Resolution tracking
    status = Column(SQLEnum(FeedbackStatusEnum), default=FeedbackStatusEnum.NEW)
    assigned_developer = Column(String, nullable=True)
    root_cause = Column(Text, nullable=True)
    fix_description = Column(Text, nullable=True)

    # Timeline
    reported_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    fixed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Quality metrics
    reproduction_success_rate = Column(Float, nullable=True)
    fix_validation = Column(Boolean, nullable=True)
    regression_risk = Column(String, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="bug_reports")
    client = relationship("Client", backref="bug_reports")

    # Indexes
    __table_args__ = (
        Index('idx_bug_severity', 'severity'),
        Index('idx_bug_status', 'status'),
        Index('idx_bug_reported_date', 'reported_at'),
    )


class Survey(Base):
    """Survey definitions and configurations"""
    __tablename__ = "surveys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Survey metadata
    type = Column(SQLEnum(SurveyTypeEnum), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Survey configuration
    questions = Column(JSON, nullable=False)  # List of question objects
    target_users = Column(JSON, nullable=True)  # List of specific user IDs
    target_segments = Column(JSON, nullable=True)  # List of user segments

    # Distribution settings
    distribution_method = Column(String, nullable=True)  # email, in_app, both
    send_reminders = Column(Boolean, default=True)
    reminder_frequency_days = Column(Integer, default=7)
    max_reminders = Column(Integer, default=2)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    allow_multiple_responses = Column(Boolean, default=False)

    # Analytics
    total_sent = Column(Integer, default=0)
    total_responses = Column(Integer, default=0)
    response_rate = Column(Float, nullable=True)
    avg_completion_time_seconds = Column(Integer, nullable=True)

    # Settings
    survey_metadata = Column(JSON, nullable=True)

    # Audit fields
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_survey_type', 'type'),
        Index('idx_survey_active', 'is_active'),
        Index('idx_survey_expires', 'expires_at'),
    )


class SurveyResponse(Base):
    """Individual survey responses"""
    __tablename__ = "survey_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    # Response data
    responses = Column(JSON, nullable=False)  # Question ID -> Answer mapping
    completion_percentage = Column(Float, nullable=True)
    is_complete = Column(Boolean, default=False)

    # Timing
    started_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    completion_time_seconds = Column(Integer, nullable=True)

    # Context
    response_channel = Column(String, nullable=True)  # email, in_app, direct
    device_type = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    # Quality indicators
    response_quality_score = Column(Float, nullable=True)  # Based on completeness, consistency
    flagged_for_review = Column(Boolean, default=False)
    review_notes = Column(Text, nullable=True)

    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_completed = Column(Boolean, default=False)
    follow_up_notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    survey = relationship("Survey", backref="responses")
    user = relationship("User", backref="survey_responses")
    client = relationship("Client", backref="survey_responses")

    # Indexes
    __table_args__ = (
        Index('idx_survey_response_user', 'user_id', 'survey_id'),
        Index('idx_survey_response_submitted', 'submitted_at'),
        Index('idx_survey_response_complete', 'is_complete'),
        UniqueConstraint('survey_id', 'user_id', name='uq_survey_user_response'),
    )


class Testimonial(Base):
    """Customer testimonials and success stories"""
    __tablename__ = "testimonials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    # Testimonial content
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 stars

    # Context
    use_case = Column(String, nullable=True)
    results_achieved = Column(Text, nullable=True)
    metrics_improved = Column(JSON, nullable=True)  # Quantified improvements

    # Media
    photo_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    case_study_url = Column(String, nullable=True)

    # Permissions and usage
    permission_to_publish = Column(Boolean, default=False)
    permission_to_use_name = Column(Boolean, default=False)
    permission_to_use_company = Column(Boolean, default=False)
    permission_to_use_photo = Column(Boolean, default=False)

    # Publication status
    status = Column(String, default="pending_review")  # pending_review, approved, published, rejected
    published_at = Column(DateTime, nullable=True)
    published_channels = Column(JSON, nullable=True)  # website, social, sales_materials

    # Impact metrics
    views = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    leads_attributed = Column(Integer, default=0)

    # Review information
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="testimonials")
    client = relationship("Client", backref="testimonials")

    # Indexes
    __table_args__ = (
        Index('idx_testimonial_status', 'status'),
        Index('idx_testimonial_published', 'published_at'),
        Index('idx_testimonial_rating', 'rating'),
    )


class OutreachAction(Base):
    """Track proactive customer success outreach actions"""
    __tablename__ = "outreach_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    # Outreach details
    trigger_id = Column(String, nullable=False)
    outreach_type = Column(SQLEnum(OutreachTypeEnum), nullable=False)
    priority = Column(SQLEnum(OutreachPriorityEnum), nullable=False)
    channel = Column(SQLEnum(OutreachChannelEnum), nullable=False)

    # Content
    template_name = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    personalization_data = Column(JSON, nullable=True)

    # Context and triggers
    context_data = Column(JSON, nullable=True)  # Data that triggered the outreach
    trigger_conditions = Column(JSON, nullable=True)  # Conditions that were met

    # Scheduling
    scheduled_for = Column(DateTime, nullable=False)
    execution_window_start = Column(DateTime, nullable=True)
    execution_window_end = Column(DateTime, nullable=True)

    # Execution tracking
    executed_at = Column(DateTime, nullable=True)
    execution_status = Column(String, nullable=True)  # scheduled, sent, failed, cancelled
    delivery_status = Column(String, nullable=True)  # delivered, bounced, opened, clicked

    # Response tracking
    response_received = Column(Boolean, default=False)
    response_type = Column(String, nullable=True)  # positive, negative, neutral, unsubscribe
    response_data = Column(JSON, nullable=True)
    response_at = Column(DateTime, nullable=True)

    # Effectiveness
    success = Column(Boolean, nullable=True)
    success_metrics = Column(JSON, nullable=True)  # Custom success indicators
    follow_up_required = Column(Boolean, default=False)
    follow_up_completed = Column(Boolean, default=False)

    # Campaign association
    campaign_id = Column(String, nullable=True)
    sequence_position = Column(Integer, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="outreach_actions")
    client = relationship("Client", backref="outreach_actions")

    # Indexes
    __table_args__ = (
        Index('idx_outreach_scheduled', 'scheduled_for'),
        Index('idx_outreach_type', 'outreach_type'),
        Index('idx_outreach_priority', 'priority'),
        Index('idx_outreach_user_date', 'user_id', 'created_at'),
        Index('idx_outreach_trigger', 'trigger_id'),
    )


class SuccessMetric(Base):
    """Store calculated success metrics over time"""
    __tablename__ = "success_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Metric identification
    metric_name = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)  # onboarding, nps, support, adoption, etc.
    scope = Column(String, nullable=False)  # global, client, user, feature
    scope_id = Column(String, nullable=True)  # ID of the scope (client_id, user_id, etc.)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    calculation_date = Column(DateTime, default=datetime.utcnow)

    # Metric values
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)
    trend = Column(String, nullable=True)  # improving, declining, stable

    # Supporting data
    sample_size = Column(Integer, nullable=True)
    confidence_level = Column(Float, nullable=True)
    metric_metadata = Column(JSON, nullable=True)
    breakdown = Column(JSON, nullable=True)  # Detailed breakdown of the metric

    # Benchmarking
    industry_benchmark = Column(Float, nullable=True)
    company_target = Column(Float, nullable=True)
    performance_vs_benchmark = Column(String, nullable=True)  # above, below, at

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_success_metric_name_date', 'metric_name', 'calculation_date'),
        Index('idx_success_metric_scope', 'scope', 'scope_id'),
        Index('idx_success_metric_period', 'period_start', 'period_end'),
        UniqueConstraint('metric_name', 'scope', 'scope_id', 'period_start',
                        name='uq_metric_scope_period'),
    )


class ImprovementOpportunity(Base):
    """Track identified improvement opportunities"""
    __tablename__ = "improvement_opportunities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Opportunity details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    area = Column(String, nullable=False)  # performance, UX, features, etc.
    type = Column(String, nullable=False)  # bug_fix, enhancement, new_feature

    # Impact assessment
    impact_score = Column(Float, nullable=False)
    affected_users = Column(Integer, nullable=True)
    potential_value = Column(Float, nullable=True)
    risk_if_not_addressed = Column(String, nullable=True)

    # Effort estimation
    effort_estimate = Column(String, nullable=True)  # Small, Medium, Large
    estimated_hours = Column(Integer, nullable=True)
    required_skills = Column(JSON, nullable=True)
    dependencies = Column(JSON, nullable=True)

    # Prioritization
    priority_score = Column(Float, nullable=True)
    business_priority = Column(String, nullable=True)  # critical, high, medium, low
    technical_priority = Column(String, nullable=True)

    # Supporting evidence
    supporting_feedback = Column(JSON, nullable=True)  # List of feedback IDs
    supporting_data = Column(JSON, nullable=True)  # Metrics, analytics, etc.
    user_research = Column(JSON, nullable=True)

    # Implementation tracking
    status = Column(SQLEnum(FeedbackStatusEnum), default=FeedbackStatusEnum.NEW)
    assigned_to = Column(String, nullable=True)
    target_completion = Column(DateTime, nullable=True)

    # Outcome tracking
    implemented_at = Column(DateTime, nullable=True)
    actual_impact = Column(Float, nullable=True)
    success_metrics = Column(JSON, nullable=True)
    lessons_learned = Column(Text, nullable=True)

    # Audit fields
    identified_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_opportunity_impact', 'impact_score'),
        Index('idx_opportunity_priority', 'priority_score'),
        Index('idx_opportunity_status', 'status'),
        Index('idx_opportunity_area', 'area'),
    )