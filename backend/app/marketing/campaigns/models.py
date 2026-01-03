"""
Marketing Campaign Models

SQLAlchemy models for email campaigns, sequences, and individual sends.
Supports drip campaigns, case alerts, newsletters, and cold outreach.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.src.core.database import Base


class CampaignStatus(enum.Enum):
    """Campaign lifecycle status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CampaignType(enum.Enum):
    """Types of marketing campaigns"""
    COLD_OUTREACH = "cold_outreach"
    CASE_ALERT = "case_alert"
    NEWSLETTER = "newsletter"
    DRIP_SEQUENCE = "drip_sequence"
    REENGAGEMENT = "reengagement"


class Campaign(Base):
    """
    Marketing campaign with targeting, scheduling, and metrics.

    Supports multiple email sequences for drip campaigns.
    """
    __tablename__ = "marketing_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    campaign_type = Column(SQLEnum(CampaignType), nullable=False)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)

    # Targeting
    target_contact_types = Column(JSON)  # List of ContactType values
    target_case_types = Column(JSON)     # Nature of suit filters
    target_courts = Column(JSON)         # Court filters
    target_tags = Column(JSON)           # Contact tag filters
    target_states = Column(JSON)         # Geographic targeting
    custom_query = Column(Text)          # SQL/filter for advanced targeting

    # Scheduling
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    send_window_start = Column(String(10), default="09:00")  # Business hours start
    send_window_end = Column(String(10), default="17:00")    # Business hours end
    timezone = Column(String(50), default="America/New_York")
    send_days = Column(JSON, default=["mon", "tue", "wed", "thu", "fri"])  # Days to send

    # Limits
    daily_send_limit = Column(Integer, default=100)
    total_send_limit = Column(Integer)
    min_days_between_emails = Column(Integer, default=3)  # Throttle per contact

    # From Address
    from_email = Column(String(255))
    from_name = Column(String(255))
    reply_to = Column(String(255))

    # Metrics (denormalized for quick access)
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    total_converted = Column(Integer, default=0)
    total_unsubscribed = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)
    total_spam_reports = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Created by
    created_by_user_id = Column(String(100))

    # Relationships
    sequences = relationship("EmailSequence", back_populates="campaign", cascade="all, delete-orphan")
    sends = relationship("EmailSend", back_populates="campaign")

    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"

    @property
    def open_rate(self) -> float:
        """Calculate open rate percentage"""
        if self.total_delivered == 0:
            return 0.0
        return (self.total_opened / self.total_delivered) * 100

    @property
    def click_rate(self) -> float:
        """Calculate click rate percentage"""
        if self.total_delivered == 0:
            return 0.0
        return (self.total_clicked / self.total_delivered) * 100

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate percentage"""
        if self.total_delivered == 0:
            return 0.0
        return (self.total_converted / self.total_delivered) * 100


class EmailSequence(Base):
    """
    Sequence of emails in a drip campaign.

    Each sequence represents one email in the drip flow
    with its content, timing, and conditions.
    """
    __tablename__ = "marketing_email_sequences"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), index=True)

    sequence_order = Column(Integer, nullable=False)  # 1, 2, 3...
    delay_days = Column(Integer, default=0)  # Days after previous email
    delay_hours = Column(Integer, default=0)

    # Email Content
    subject_line = Column(String(255), nullable=False)
    subject_line_b = Column(String(255))  # For A/B testing
    preview_text = Column(String(255))    # Email preview/preheader

    body_html = Column(Text, nullable=False)
    body_text = Column(Text)  # Plain text fallback

    # Personalization
    personalization_prompt = Column(Text)  # AI prompt for personalization
    use_ai_personalization = Column(Boolean, default=True)
    personalization_fields = Column(JSON, default=list)  # Fields to personalize

    # Conditions
    send_if_no_open = Column(Boolean, default=True)  # Only send if previous not opened
    send_if_no_click = Column(Boolean, default=True)
    send_if_no_reply = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)

    # A/B Testing
    ab_test_enabled = Column(Boolean, default=False)
    ab_test_split = Column(Integer, default=50)  # Percentage for variant A

    # Metrics for this sequence step
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="sequences")

    def __repr__(self):
        return f"<EmailSequence(id={self.id}, order={self.sequence_order}, subject='{self.subject_line[:30]}')>"


class EmailSend(Base):
    """
    Individual email send record.

    Tracks every email sent including delivery status,
    engagement metrics, and compliance events.
    """
    __tablename__ = "marketing_email_sends"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), index=True)
    sequence_id = Column(Integer, ForeignKey("marketing_email_sequences.id"))
    contact_id = Column(Integer, ForeignKey("marketing_contacts.id"), index=True)

    # Send Details
    to_email = Column(String(255), nullable=False, index=True)
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255))

    subject_line = Column(String(255))
    preview_text = Column(String(255))
    body_html = Column(Text)
    body_text = Column(Text)

    # AB Test variant
    ab_variant = Column(String(1))  # 'A' or 'B'

    # Case Context (for personalization and landing)
    related_case_id = Column(Integer, ForeignKey("marketing_contact_cases.id"))
    personalization_data = Column(JSON)  # Data used for personalization

    # Landing Token (for zero-friction landing)
    landing_token = Column(String(100), unique=True, index=True)
    landing_case_data = Column(JSON)  # Pre-loaded case data for landing page

    # Status
    status = Column(String(50), default="queued", index=True)
    # Statuses: queued, scheduled, sending, sent, delivered, bounced, failed, compliance_failed
    scheduled_for = Column(DateTime, index=True)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)

    # Engagement
    opened_at = Column(DateTime)
    open_count = Column(Integer, default=0)
    clicked_at = Column(DateTime)
    click_count = Column(Integer, default=0)
    clicked_links = Column(JSON, default=list)
    replied_at = Column(DateTime)
    converted_at = Column(DateTime)

    # Compliance
    unsubscribed_at = Column(DateTime)
    spam_reported_at = Column(DateTime)
    bounce_type = Column(String(50))  # hard, soft
    bounce_reason = Column(Text)
    compliance_notes = Column(Text)

    # External References
    email_provider_id = Column(String(255))  # SendGrid/SES message ID
    email_provider = Column(String(50))  # sendgrid, ses, smtp

    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="sends")
    contact = relationship("Contact", back_populates="emails_received")

    def __repr__(self):
        return f"<EmailSend(id={self.id}, to='{self.to_email}', status='{self.status}')>"


class EmailTemplate(Base):
    """
    Reusable email templates.

    Store common email designs that can be used across campaigns.
    """
    __tablename__ = "marketing_email_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # outreach, alert, newsletter, etc.

    subject_line = Column(String(255))
    preview_text = Column(String(255))
    body_html = Column(Text, nullable=False)
    body_text = Column(Text)

    # Personalization placeholders
    available_variables = Column(JSON, default=list)

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(String(100))

    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name='{self.name}')>"
