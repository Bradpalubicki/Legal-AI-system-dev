"""
Newsletter Models

SQLAlchemy models for newsletter subscribers and editions.
Supports weekly digests of court filings and legal news.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.src.core.database import Base


class NewsletterSubscriber(Base):
    """
    Newsletter subscriber record.

    Tracks subscription preferences and engagement metrics.
    Separate from marketing contacts for double opt-in compliance.
    """
    __tablename__ = "marketing_newsletter_subscribers"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Optional profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    title = Column(String(100))

    # Preferences
    frequency = Column(String(20), default="weekly")  # daily, weekly, monthly
    interests = Column(JSON, default=list)  # case types interested in
    jurisdictions = Column(JSON, default=list)  # courts interested in
    preferred_send_time = Column(String(10))  # HH:MM format

    # Status
    is_confirmed = Column(Boolean, default=False)  # Double opt-in
    confirmation_token = Column(String(100), unique=True)
    confirmed_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    unsubscribed_at = Column(DateTime)
    unsubscribe_reason = Column(String(255))

    # Source
    source = Column(String(100))  # website, outreach_conversion, import
    source_campaign_id = Column(Integer)
    source_url = Column(String(500))  # Referrer URL

    # Engagement
    emails_received = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    last_opened_at = Column(DateTime)
    last_clicked_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NewsletterSubscriber(id={self.id}, email='{self.email}', active={self.is_active})>"

    @property
    def open_rate(self) -> float:
        """Calculate subscriber's open rate"""
        if self.emails_received == 0:
            return 0.0
        return (self.emails_opened / self.emails_received) * 100


class NewsletterEdition(Base):
    """
    Newsletter edition/issue.

    Represents a single newsletter send with its content and metrics.
    """
    __tablename__ = "marketing_newsletter_editions"

    id = Column(Integer, primary_key=True)

    # Edition info
    edition_number = Column(Integer)  # Issue number
    edition_date = Column(DateTime, nullable=False)
    subject_line = Column(String(255))
    preview_text = Column(String(255))

    # Content
    intro_text = Column(Text)
    featured_cases = Column(JSON)  # List of case summaries
    notable_filings = Column(JSON)  # Recent notable filings
    legal_news = Column(JSON)  # Curated news items
    insights = Column(Text)  # AI-generated insights
    call_to_action = Column(Text)  # CTA section

    body_html = Column(Text)
    body_text = Column(Text)

    # Status
    status = Column(String(50), default="draft")  # draft, scheduled, sending, sent
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    generation_started_at = Column(DateTime)
    generation_completed_at = Column(DateTime)

    # Targeting
    target_frequency = Column(String(20))  # daily, weekly, monthly
    target_interests = Column(JSON)

    # Metrics
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_unsubscribed = Column(Integer, default=0)

    # Generation metadata
    ai_model_used = Column(String(100))
    generation_prompt = Column(Text)
    cases_analyzed = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(String(100))

    def __repr__(self):
        return f"<NewsletterEdition(id={self.id}, date={self.edition_date}, status='{self.status}')>"

    @property
    def open_rate(self) -> float:
        """Calculate open rate for this edition"""
        if self.total_delivered == 0:
            return 0.0
        return (self.total_opened / self.total_delivered) * 100


class NewsletterSend(Base):
    """
    Individual newsletter send record.

    Tracks each subscriber's receipt and engagement with an edition.
    """
    __tablename__ = "marketing_newsletter_sends"

    id = Column(Integer, primary_key=True, index=True)
    edition_id = Column(Integer, ForeignKey("marketing_newsletter_editions.id"), index=True)
    subscriber_id = Column(Integer, ForeignKey("marketing_newsletter_subscribers.id"), index=True)

    # Send details
    to_email = Column(String(255), nullable=False, index=True)
    email_provider_id = Column(String(255))

    # Status
    status = Column(String(50), default="queued")  # queued, sent, delivered, bounced, failed
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)

    # Engagement
    opened_at = Column(DateTime)
    open_count = Column(Integer, default=0)
    clicked_at = Column(DateTime)
    clicked_links = Column(JSON, default=list)

    # Compliance
    unsubscribed_at = Column(DateTime)
    bounce_type = Column(String(50))
    bounce_reason = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NewsletterSend(id={self.id}, to='{self.to_email}', status='{self.status}')>"
