"""
Marketing Analytics Models

SQLAlchemy models for tracking marketing events, metrics, and conversions.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey, JSON, Float, Date
)
from datetime import datetime

from app.src.core.database import Base


class MarketingEvent(Base):
    """
    Generic marketing event tracking.

    Tracks all marketing-related events for analytics and attribution.
    """
    __tablename__ = "marketing_events"

    id = Column(Integer, primary_key=True, index=True)

    # Event identification
    event_type = Column(String(50), nullable=False, index=True)
    # Types: email_sent, email_opened, email_clicked, email_bounced,
    #        unsubscribe, subscribe, page_view, conversion, signup

    event_timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Related entities
    contact_id = Column(Integer, ForeignKey("marketing_contacts.id"), index=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), index=True)
    email_send_id = Column(Integer, ForeignKey("marketing_email_sends.id"))
    subscriber_id = Column(Integer, ForeignKey("marketing_newsletter_subscribers.id"))

    # Event data
    email = Column(String(255), index=True)
    link_url = Column(String(500))
    page_url = Column(String(500))
    referrer_url = Column(String(500))

    # Attribution
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    utm_content = Column(String(100))
    utm_term = Column(String(100))

    # Client info
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    device_type = Column(String(50))  # desktop, mobile, tablet
    browser = Column(String(100))
    os = Column(String(100))
    country = Column(String(100))
    city = Column(String(100))

    # Additional data
    event_metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketingEvent(id={self.id}, type='{self.event_type}')>"


class DailyMetrics(Base):
    """
    Daily aggregated marketing metrics.

    Pre-calculated daily statistics for dashboard and reporting.
    """
    __tablename__ = "marketing_daily_metrics"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True, index=True)

    # Contact metrics
    new_contacts = Column(Integer, default=0)
    total_contacts = Column(Integer, default=0)
    contacts_with_email = Column(Integer, default=0)

    # Email metrics
    emails_sent = Column(Integer, default=0)
    emails_delivered = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    emails_unsubscribed = Column(Integer, default=0)
    emails_spam_reported = Column(Integer, default=0)

    # Rates
    delivery_rate = Column(Float, default=0.0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    unsubscribe_rate = Column(Float, default=0.0)

    # Newsletter metrics
    newsletter_subscribers = Column(Integer, default=0)
    newsletter_sent = Column(Integer, default=0)
    newsletter_opened = Column(Integer, default=0)

    # CourtListener metrics
    dockets_processed = Column(Integer, default=0)
    attorneys_extracted = Column(Integer, default=0)
    parties_extracted = Column(Integer, default=0)

    # Conversion metrics
    signups = Column(Integer, default=0)
    trial_starts = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    conversion_revenue = Column(Float, default=0.0)

    # Campaign metrics (aggregate)
    active_campaigns = Column(Integer, default=0)

    calculated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DailyMetrics(date={self.date})>"


class CampaignMetricsSnapshot(Base):
    """
    Point-in-time campaign metrics snapshot.

    Captures campaign performance at regular intervals for trend analysis.
    """
    __tablename__ = "marketing_campaign_snapshots"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), index=True)
    snapshot_date = Column(Date, nullable=False, index=True)

    # Metrics at snapshot time
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    total_converted = Column(Integer, default=0)
    total_unsubscribed = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)

    # Calculated rates
    delivery_rate = Column(Float, default=0.0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CampaignSnapshot(campaign_id={self.campaign_id}, date={self.snapshot_date})>"


class Conversion(Base):
    """
    Marketing conversion record.

    Tracks when a contact converts to a paying customer or takes
    a valuable action, with full attribution.
    """
    __tablename__ = "marketing_conversions"

    id = Column(Integer, primary_key=True, index=True)

    # Who converted
    contact_id = Column(Integer, ForeignKey("marketing_contacts.id"), index=True)
    email = Column(String(255), index=True)
    user_id = Column(String(100))  # App user ID after signup

    # Conversion type
    conversion_type = Column(String(50), nullable=False)
    # Types: signup, trial_start, subscription, document_purchase

    # Attribution
    attributed_campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"))
    attributed_email_send_id = Column(Integer, ForeignKey("marketing_email_sends.id"))
    landing_token = Column(String(100))  # From email link

    # Value
    revenue = Column(Float, default=0.0)
    subscription_tier = Column(String(50))

    # Timing
    first_touch_at = Column(DateTime)  # First marketing contact
    converted_at = Column(DateTime, default=datetime.utcnow)
    days_to_convert = Column(Integer)

    # Additional data
    conversion_data = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Conversion(id={self.id}, type='{self.conversion_type}', email='{self.email}')>"


class MonitorStatus(Base):
    """
    CourtListener monitor status and health tracking.

    Tracks the filing monitor service status and statistics.
    """
    __tablename__ = "marketing_monitor_status"

    id = Column(Integer, primary_key=True)

    # Last run info
    last_poll_started_at = Column(DateTime)
    last_poll_completed_at = Column(DateTime)
    last_poll_status = Column(String(50))  # success, error, partial
    last_poll_error = Column(Text)

    # Statistics from last run
    dockets_found = Column(Integer, default=0)
    dockets_processed = Column(Integer, default=0)
    contacts_created = Column(Integer, default=0)
    contacts_updated = Column(Integer, default=0)
    cases_linked = Column(Integer, default=0)

    # Rate limit tracking
    api_calls_made = Column(Integer, default=0)
    rate_limit_remaining = Column(Integer)
    rate_limit_reset_at = Column(DateTime)

    # Configuration snapshot
    lookback_hours = Column(Integer)
    target_courts = Column(JSON)
    target_nature_of_suits = Column(JSON)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MonitorStatus(last_poll={self.last_poll_completed_at})>"
