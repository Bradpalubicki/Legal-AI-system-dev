"""
Feature Flag Utilities
Helper functions for checking feature flags and handling promotions
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

from ..models.feature_flags import (
    FeatureFlag,
    UserFeatureOverride,
    PromotionalCampaign,
    UserCampaignRedemption
)
from ..models.credits import UserCredits, CreditTransaction, TransactionType

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """Service for managing feature flags and promotions"""

    def __init__(self, db: Session):
        self.db = db

    def is_enabled(self, flag_key: str, user_id: Optional[int] = None) -> bool:
        """
        Check if a feature flag is enabled.

        Priority:
        1. User-specific override
        2. Global flag setting
        3. Default to False
        """
        # Check user override first
        if user_id:
            override = self.db.query(UserFeatureOverride).filter(
                UserFeatureOverride.user_id == user_id,
                UserFeatureOverride.flag_key == flag_key
            ).first()

            if override:
                # Check if override has expired
                if override.expires_at:
                    now = datetime.now(timezone.utc)
                    if now > override.expires_at.replace(tzinfo=timezone.utc):
                        # Expired - remove it
                        self.db.delete(override)
                        self.db.commit()
                    else:
                        return override.is_enabled
                else:
                    return override.is_enabled

        # Check global flag
        flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.flag_key == flag_key
        ).first()

        if flag:
            # Check if flag has scheduled enable/disable
            now = datetime.now(timezone.utc)

            if flag.enabled_at and now < flag.enabled_at.replace(tzinfo=timezone.utc):
                return False

            if flag.disabled_at and now > flag.disabled_at.replace(tzinfo=timezone.utc):
                return False

            return flag.is_enabled

        return False

    def get_value(self, flag_key: str, default: Any = None) -> Any:
        """Get feature flag value (for non-boolean flags)"""
        flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.flag_key == flag_key
        ).first()

        if not flag or not flag.is_enabled:
            return default

        # Return value based on type
        if flag.value_json is not None:
            return flag.value_json
        elif flag.value_number is not None:
            return flag.value_number
        elif flag.value_string is not None:
            return flag.value_string
        else:
            return default

    def credits_required(self, user_id: int) -> bool:
        """
        Check if user needs to pay credits for operations.

        Returns False if:
        - Global credits disabled
        - User has unlimited access override
        - User in active promotional campaign
        """
        # Check global credits flag
        if not self.is_enabled("credits_enabled"):
            logger.info(f"Credits globally disabled")
            return False

        # Check user override
        if self.is_enabled("unlimited_searches", user_id):
            logger.info(f"User {user_id} has unlimited searches override")
            return False

        # Check active promotional campaigns
        active_campaigns = self.get_active_campaigns_for_user(user_id)
        for campaign in active_campaigns:
            if campaign.unlimited_searches:
                logger.info(f"User {user_id} has unlimited searches from campaign: {campaign.campaign_code}")
                return False

        return True

    def get_active_campaigns_for_user(self, user_id: int) -> list:
        """Get all active promotional campaigns user is eligible for"""
        now = datetime.now(timezone.utc)

        # Get all active campaigns
        campaigns = self.db.query(PromotionalCampaign).filter(
            PromotionalCampaign.is_active == True,
            PromotionalCampaign.starts_at <= now,
            PromotionalCampaign.ends_at >= now
        ).all()

        eligible = []
        for campaign in campaigns:
            # Check if user already redeemed
            redemption = self.db.query(UserCampaignRedemption).filter(
                UserCampaignRedemption.user_id == user_id,
                UserCampaignRedemption.campaign_id == campaign.id
            ).first()

            if redemption:
                # Already redeemed - but still gets benefits until campaign ends
                eligible.append(campaign)
            elif campaign.is_valid():
                eligible.append(campaign)

        return eligible

    def redeem_campaign(self, user_id: int, campaign_code: str) -> Dict[str, Any]:
        """
        Redeem a promotional campaign for a user.

        Returns dict with redemption details.
        """
        # Get campaign
        campaign = self.db.query(PromotionalCampaign).filter(
            PromotionalCampaign.campaign_code == campaign_code
        ).first()

        if not campaign:
            raise ValueError(f"Campaign code '{campaign_code}' not found")

        if not campaign.is_valid():
            raise ValueError(f"Campaign '{campaign_code}' is not currently active")

        # Check if already redeemed
        existing = self.db.query(UserCampaignRedemption).filter(
            UserCampaignRedemption.user_id == user_id,
            UserCampaignRedemption.campaign_id == campaign.id
        ).first()

        if existing:
            raise ValueError(f"You have already redeemed campaign '{campaign_code}'")

        # Apply benefits
        credits_awarded = 0.0

        if campaign.free_credits > 0:
            # Award free credits
            user_credits = self.db.query(UserCredits).filter(
                UserCredits.user_id == user_id
            ).first()

            if not user_credits:
                user_credits = UserCredits(
                    user_id=user_id,
                    username=f"user_{user_id}",
                    balance=0,
                    total_credits_purchased=0,
                    total_credits_spent=0
                )
                self.db.add(user_credits)

            user_credits.balance += int(campaign.free_credits)
            user_credits.total_credits_purchased += int(campaign.free_credits)
            credits_awarded = campaign.free_credits

            # Record transaction
            transaction = CreditTransaction(
                user_id=user_id,
                transaction_type=TransactionType.GRANT,
                amount=campaign.free_credits,
                balance_after=user_credits.balance,
                description=f"Promotional campaign: {campaign.campaign_name}",
                reference_id=campaign.campaign_code
            )
            self.db.add(transaction)

        # Create redemption record
        redemption = UserCampaignRedemption(
            user_id=user_id,
            campaign_id=campaign.id,
            campaign_code=campaign.campaign_code,
            credits_awarded=credits_awarded,
            discount_applied=campaign.discount_percentage
        )
        self.db.add(redemption)

        # Increment redemption count
        campaign.current_redemptions += 1

        self.db.commit()

        logger.info(f"User {user_id} redeemed campaign '{campaign_code}': ${credits_awarded} credits")

        return {
            "success": True,
            "campaign": campaign.campaign_name,
            "credits_awarded": credits_awarded,
            "discount_percentage": campaign.discount_percentage,
            "unlimited_searches": campaign.unlimited_searches,
            "valid_until": campaign.ends_at.isoformat()
        }


# Convenience functions
def is_feature_enabled(db: Session, flag_key: str, user_id: Optional[int] = None) -> bool:
    """Quick check if feature is enabled"""
    service = FeatureFlagService(db)
    return service.is_enabled(flag_key, user_id)


def credits_required_for_user(db: Session, user_id: int) -> bool:
    """Check if user must pay credits"""
    service = FeatureFlagService(db)
    return service.credits_required(user_id)


# Alias for backward compatibility
FeatureFlagManager = FeatureFlagService
