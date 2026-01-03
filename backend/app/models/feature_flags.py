"""
Feature Flags Model
Control feature availability, pricing, and promotional campaigns
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import Optional

from ..src.core.database import Base


class FeatureFlag(Base):
    """
    Global feature flags for controlling app behavior.

    Use cases:
    - Enable/disable credit requirements
    - Run promotional campaigns
    - A/B testing
    - Gradual feature rollouts
    """
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)

    # Flag identification
    flag_name = Column(String(100), unique=True, nullable=False, index=True)
    flag_key = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "credits_enabled"

    # Status
    is_enabled = Column(Boolean, default=False, nullable=False)

    # Description
    description = Column(Text)
    category = Column(String(50))  # 'billing', 'features', 'promotional', 'experimental'

    # Value (for flags that aren't just boolean)
    value_string = Column(String(500))
    value_number = Column(Float)
    value_json = Column(JSON)

    # Scheduling
    enabled_at = Column(DateTime)
    disabled_at = Column(DateTime)

    # Metadata
    created_by = Column(String(100))  # Admin who created it
    last_modified_by = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FeatureFlag(key={self.flag_key}, enabled={self.is_enabled})>"


class UserFeatureOverride(Base):
    """
    Per-user feature flag overrides.

    Use cases:
    - VIP users get unlimited searches
    - Beta testers get early access
    - Free tier for specific users
    """
    __tablename__ = "user_feature_overrides"

    id = Column(Integer, primary_key=True, index=True)

    # User and flag
    user_id = Column(Integer, nullable=False, index=True)
    flag_key = Column(String(100), nullable=False, index=True)

    # Override value
    is_enabled = Column(Boolean, nullable=False)
    override_value = Column(JSON)  # Additional override data

    # Reason and expiry
    reason = Column(String(500))  # "VIP user", "Beta tester", "Promotional campaign"
    expires_at = Column(DateTime)  # Auto-expire on specific date

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserFeatureOverride(user_id={self.user_id}, flag={self.flag_key}, enabled={self.is_enabled})>"


class PromotionalCampaign(Base):
    """
    Time-limited promotional campaigns.

    Examples:
    - "Free searches for first month"
    - "50% off credit purchases"
    - "$20 signup bonus"
    """
    __tablename__ = "promotional_campaigns"

    id = Column(Integer, primary_key=True, index=True)

    # Campaign details
    campaign_name = Column(String(200), nullable=False)
    campaign_code = Column(String(50), unique=True, index=True)  # "LAUNCH2025", "FREEMONTH"

    # Type
    campaign_type = Column(String(50), nullable=False)  # 'free_credits', 'discount', 'unlimited_access'

    # Status
    is_active = Column(Boolean, default=True)

    # Benefits
    free_credits = Column(Float, default=0.0)  # Give users $X free credits
    discount_percentage = Column(Float, default=0.0)  # X% off purchases
    unlimited_searches = Column(Boolean, default=False)  # No credit requirements

    # Eligibility
    new_users_only = Column(Boolean, default=False)
    max_redemptions = Column(Integer)  # Max users who can redeem
    current_redemptions = Column(Integer, default=0)

    # Timing
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)

    # Terms
    description = Column(Text)
    terms = Column(Text)

    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def is_valid(self) -> bool:
        """Check if campaign is currently valid"""
        now = datetime.now(timezone.utc)

        if not self.is_active:
            return False

        if self.starts_at and now < self.starts_at.replace(tzinfo=timezone.utc):
            return False

        if self.ends_at and now > self.ends_at.replace(tzinfo=timezone.utc):
            return False

        if self.max_redemptions and self.current_redemptions >= self.max_redemptions:
            return False

        return True

    def __repr__(self):
        return f"<PromotionalCampaign(code={self.campaign_code}, active={self.is_active})>"


class UserCampaignRedemption(Base):
    """
    Track which users have redeemed which campaigns.
    Prevents multiple redemptions.
    """
    __tablename__ = "user_campaign_redemptions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False, index=True)
    campaign_id = Column(Integer, nullable=False, index=True)
    campaign_code = Column(String(50), nullable=False)

    # What they got
    credits_awarded = Column(Float, default=0.0)
    discount_applied = Column(Float, default=0.0)

    # When
    redeemed_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<UserCampaignRedemption(user_id={self.user_id}, campaign={self.campaign_code})>"
