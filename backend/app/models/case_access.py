"""
Case Access Models
Handles pay-per-case purchases and access control
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum

from ..src.core.database import Base
# TrackedDocket is defined in shared.database.models


class CaseAccessType(enum.Enum):
    """Type of case access"""
    ONE_TIME = "one_time"  # $5 pay-per-case
    MONTHLY = "monthly"  # $19/month unlimited
    SUBSCRIPTION = "subscription"  # From Pro/Firm tier


class CaseAccessStatus(enum.Enum):
    """Status of case access"""
    PENDING = "pending"  # Payment pending
    ACTIVE = "active"  # Access granted
    EXPIRED = "expired"  # Access expired
    CANCELLED = "cancelled"  # User cancelled


class CaseAccess(Base):
    """
    Tracks user access to specific cases
    Can be purchased individually ($5) or included in subscription
    """
    __tablename__ = "case_access"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("tracked_dockets.id"), nullable=False, index=True)

    # Access type and status
    access_type = Column(Enum(CaseAccessType), nullable=False)
    status = Column(Enum(CaseAccessStatus), default=CaseAccessStatus.PENDING, index=True)

    # Payment information
    amount_paid = Column(Numeric(10, 2))  # Amount user paid
    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_checkout_session_id = Column(String(255), unique=True, index=True)

    # Subscription reference (if from subscription)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    # Access period
    granted_at = Column(DateTime, nullable=True)  # When access was granted
    expires_at = Column(DateTime, nullable=True)  # When access expires (null = unlimited)

    # Case monitoring preferences
    notifications_enabled = Column(Boolean, default=True)
    notification_email = Column(String(255), nullable=True)  # Custom email for this case
    notification_frequency = Column(String(50), default="immediate")  # immediate, daily, weekly

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="case_accesses")
    # case = relationship("TrackedDocket", back_populates="access_grants")  # Temporarily disabled - relationship issue
    # subscription = relationship("Subscription", back_populates="case_accesses")  # Temporarily disabled - Subscription model import issue

    def is_active(self) -> bool:
        """Check if access is currently active"""
        if self.status != CaseAccessStatus.ACTIVE:
            return False

        # Check expiration
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False

        return True

    def days_remaining(self) -> int | None:
        """Get number of days remaining (None if unlimited)"""
        if not self.expires_at:
            return None

        if self.expires_at < datetime.utcnow():
            return 0

        delta = self.expires_at - datetime.utcnow()
        return delta.days

    def extend_access(self, days: int = 30):
        """Extend access by specified number of days"""
        if self.expires_at:
            self.expires_at = self.expires_at + timedelta(days=days)
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=days)

    def cancel(self, reason: str = None):
        """Cancel case access"""
        self.status = CaseAccessStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.cancellation_reason = reason

    def __repr__(self):
        return f"<CaseAccess(user_id={self.user_id}, case_id={self.case_id}, type={self.access_type.value}, status={self.status.value})>"


class CaseAccessPurchase(Base):
    """
    Records individual case access purchases
    Separate from CaseAccess to track payment history
    """
    __tablename__ = "case_access_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    case_access_id = Column(Integer, ForeignKey("case_access.id"), nullable=False)

    # Purchase details
    amount = Column(Numeric(10, 2), nullable=False)  # Amount charged
    currency = Column(String(3), default="USD")

    # Stripe details
    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_charge_id = Column(String(255))
    stripe_receipt_url = Column(String(500))
    stripe_invoice_id = Column(String(255), nullable=True)

    # Payment method
    payment_method_type = Column(String(50))  # card, apple_pay, google_pay
    card_brand = Column(String(50), nullable=True)  # visa, mastercard, amex
    card_last4 = Column(String(4), nullable=True)

    # Refund tracking
    refunded = Column(Boolean, default=False)
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    refund_reason = Column(String(500), nullable=True)

    # Metadata
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    purchase_metadata = Column(String(1000), nullable=True)  # JSON string for additional data

    # Relationships
    user = relationship("User")
    case_access = relationship("CaseAccess", backref="purchases")

    def __repr__(self):
        return f"<CaseAccessPurchase(id={self.id}, user_id={self.user_id}, amount={self.amount})>"


class CaseMonitoringEvent(Base):
    """
    Track events for monitored cases
    Used for notifications and activity feed
    """
    __tablename__ = "case_monitoring_events"

    id = Column(Integer, primary_key=True, index=True)
    case_access_id = Column(Integer, ForeignKey("case_access.id"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("tracked_dockets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Event details
    event_type = Column(String(100), nullable=False)  # new_filing, status_change, deadline, etc.
    event_title = Column(String(255), nullable=False)
    event_description = Column(String(1000), nullable=True)
    event_data = Column(String(2000), nullable=True)  # JSON string

    # Notification tracking
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)
    notification_sent_to = Column(String(255), nullable=True)  # Email address

    # Event metadata
    event_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case_access = relationship("CaseAccess", backref="events")
    # case = relationship("TrackedDocket")  # Temporarily disabled - relationship issue
    user = relationship("User")

    def __repr__(self):
        return f"<CaseMonitoringEvent(id={self.id}, type={self.event_type}, case_id={self.case_id})>"
