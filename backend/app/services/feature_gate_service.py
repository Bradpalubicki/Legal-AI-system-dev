"""
Feature Gate Service
Integrates feature access configuration with existing feature flags and user subscriptions
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.feature_access import (
    Feature,
    FeatureTier,
    get_tier_for_role,
    has_feature_access,
    get_feature_config,
    get_feature_limit,
    get_upgrade_message
)
from app.models.user import User
from app.models.billing import Subscription
from app.models.feature_flags import UserFeatureOverride, PromotionalCampaign
from app.utils.feature_flags import FeatureFlagManager


class FeatureGateService:
    """Service for checking feature access across tiers, subscriptions, and overrides"""

    def __init__(self, db: Session):
        self.db = db
        self.flag_manager = FeatureFlagManager(db)

    def get_user_tier(self, user: User) -> FeatureTier:
        """
        Determine the user's effective feature tier

        Priority:
        1. Admin users ALWAYS get ADMIN tier (full access)
        2. Active subscription tier
        3. User role tier (fallback to FREE for non-admins)

        Args:
            user: The user to check

        Returns:
            The user's feature tier
        """
        from app.models.user import UserRole

        # CRITICAL: Admin users ALWAYS get full access, regardless of subscription
        if user.is_admin or user.role == UserRole.ADMIN:
            return FeatureTier.ADMIN

        # Check for active subscription
        # Wrapped in try-except in case subscriptions table doesn't exist
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status.in_(["active", "trialing"])
            ).first()
        except Exception:
            # Table might not exist yet - no subscription
            subscription = None

        if subscription and subscription.plan:
            plan_name = subscription.plan.name.lower()

            # Map subscription plan names to tiers (aligned with Stripe pricing.py)
            # Enterprise tier
            if "enterprise" in plan_name:
                return FeatureTier.ENTERPRISE
            # Premium tier ($199/month)
            elif "premium" in plan_name:
                return FeatureTier.PREMIUM
            # Professional tier ($99/month)
            elif "professional" in plan_name and "individual" not in plan_name:
                return FeatureTier.PROFESSIONAL
            # Individual Pro tier ($29.99/month)
            elif "individual" in plan_name or ("pro" in plan_name and "professional" not in plan_name):
                return FeatureTier.INDIVIDUAL_PRO
            # Basic tier ($9.99/month)
            elif "basic" in plan_name:
                return FeatureTier.BASIC
            # Legacy plan name fallbacks
            elif "firm" in plan_name:
                return FeatureTier.ENTERPRISE
            elif "case" in plan_name or "monitor" in plan_name:
                return FeatureTier.BASIC

        # Fall back to role-based tier (FREE for non-admins, ADMIN for admins)
        return get_tier_for_role(user.role)

    def check_feature_access(
        self,
        user: User,
        feature: Feature,
        check_overrides: bool = True
    ) -> Dict[str, Any]:
        """
        Check if user has access to a feature

        Args:
            user: The user to check
            feature: The feature to check access for
            check_overrides: Whether to check for user-specific overrides

        Returns:
            Dict with:
            - has_access: bool
            - tier: str
            - config: dict (feature configuration)
            - reason: str (why access was granted/denied)
            - upgrade_info: dict (if access denied, info about upgrading)
        """
        from app.models.user import UserRole

        # 0. CRITICAL: Admin users ALWAYS have full access to everything
        if user.is_admin or user.role == UserRole.ADMIN:
            return {
                "has_access": True,
                "tier": FeatureTier.ADMIN.value,
                "config": {"enabled": True, "limit": None},
                "reason": "Admin user - full access granted",
                "is_admin": True,
                "is_override": False,
                "is_promotional": False
            }

        # 1. Check user-specific feature overrides (highest priority)
        # Wrapped in try-except in case user_feature_overrides table doesn't exist
        if check_overrides:
            try:
                override = self.db.query(UserFeatureOverride).filter(
                    UserFeatureOverride.user_id == user.id,
                    UserFeatureOverride.flag_key == feature.value,
                    UserFeatureOverride.is_enabled == True
                ).first()

                if override:
                    # Check if override is still valid
                    if override.expires_at is None or override.expires_at > datetime.utcnow():
                        return {
                            "has_access": True,
                            "tier": "override",
                            "config": {"enabled": True, "limit": None},
                            "reason": f"User override: {override.reason}",
                            "is_override": True
                        }
            except Exception:
                # Table might not exist yet - skip override check
                pass

        # 2. Check promotional campaigns
        # Wrapped in try-except in case promotional_campaigns table doesn't exist
        try:
            active_campaigns = self._get_active_campaigns_for_user(user.id, feature)
            if active_campaigns:
                campaign = active_campaigns[0]
                return {
                    "has_access": True,
                    "tier": "promotional",
                    "config": {"enabled": True, "limit": None},
                    "reason": f"Promotional access: {campaign.name}",
                    "is_promotional": True,
                    "campaign_id": campaign.id
                }
        except Exception:
            # Table might not exist yet - skip campaign check
            pass

        # 3. Check tier-based access
        tier = self.get_user_tier(user)
        config = get_feature_config(tier, feature)
        has_access = config.get("enabled", False)

        result = {
            "has_access": has_access,
            "tier": tier.value,
            "config": config,
            "reason": config.get("description", ""),
            "is_override": False,
            "is_promotional": False
        }

        # If no access, add upgrade information
        if not has_access:
            result["upgrade_info"] = get_upgrade_message(feature, tier)

        return result

    def check_feature_limit(
        self,
        user: User,
        feature: Feature,
        current_usage: int = 0
    ) -> Dict[str, Any]:
        """
        Check if user has remaining usage for a limited feature

        Args:
            user: The user to check
            feature: The feature to check
            current_usage: User's current usage this billing period

        Returns:
            Dict with:
            - has_access: bool
            - limit: int or None (None = unlimited)
            - current_usage: int
            - remaining: int or None
            - reset_date: datetime (when usage resets)
        """
        access_check = self.check_feature_access(user, feature)

        if not access_check["has_access"]:
            return {
                "has_access": False,
                "limit": 0,
                "current_usage": current_usage,
                "remaining": 0,
                "reason": access_check.get("reason"),
                "upgrade_info": access_check.get("upgrade_info")
            }

        # Get the limit from config
        limit = access_check["config"].get("limit")

        # If limit is None, feature is unlimited
        if limit is None:
            return {
                "has_access": True,
                "limit": None,
                "current_usage": current_usage,
                "remaining": None,  # Unlimited
                "is_unlimited": True
            }

        # Check if user has remaining usage
        remaining = limit - current_usage
        has_remaining = remaining > 0

        result = {
            "has_access": has_remaining,
            "limit": limit,
            "current_usage": current_usage,
            "remaining": remaining,
            "is_unlimited": False
        }

        # Get reset date from subscription
        # Wrapped in try-except in case subscriptions table doesn't exist
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status.in_(["active", "trialing"])
            ).first()

            if subscription:
                result["reset_date"] = subscription.usage_reset_date
        except Exception:
            # Table might not exist yet - no subscription data
            pass

        # If no remaining, add upgrade info
        if not has_remaining:
            tier = self.get_user_tier(user)
            result["upgrade_info"] = get_upgrade_message(feature, tier)
            result["reason"] = "Usage limit exceeded for this billing period"

        return result

    def _get_active_campaigns_for_user(
        self,
        user_id: int,
        feature: Optional[Feature] = None
    ) -> list:
        """Get active promotional campaigns for a user"""
        now = datetime.utcnow()

        query = self.db.query(PromotionalCampaign).filter(
            PromotionalCampaign.is_active == True,
            PromotionalCampaign.starts_at <= now
        ).filter(
            (PromotionalCampaign.ends_at == None) |
            (PromotionalCampaign.ends_at > now)
        )

        # Filter by feature if specified
        if feature:
            # Check if campaign provides access to this feature
            # This would need to be expanded based on campaign structure
            pass

        campaigns = query.all()

        # Filter out campaigns user has already redeemed
        from app.models.feature_flags import UserCampaignRedemption
        redeemed_ids = [
            r.campaign_id for r in
            self.db.query(UserCampaignRedemption).filter(
                UserCampaignRedemption.user_id == user_id
            ).all()
        ]

        return [c for c in campaigns if c.id not in redeemed_ids]

    def get_tier_comparison(self, current_tier: FeatureTier) -> Dict[str, Any]:
        """
        Get comparison of features across all tiers for upgrade prompts
        Aligned with Stripe subscription tiers

        Args:
            current_tier: User's current tier

        Returns:
            Dict with tier comparison data
        """
        tiers_info = {
            FeatureTier.FREE: {
                "name": "Free",
                "price": "$0",
                "price_monthly": 0,
                "description": "Get started with basic search access",
                "features": []
            },
            FeatureTier.BASIC: {
                "name": "Basic",
                "price": "$9.99/month",
                "price_monthly": 9.99,
                "description": "Essential features for individuals",
                "features": []
            },
            FeatureTier.INDIVIDUAL_PRO: {
                "name": "Individual Pro",
                "price": "$29.99/month",
                "price_monthly": 29.99,
                "description": "Advanced features for power users",
                "features": [],
                "popular": True
            },
            FeatureTier.PROFESSIONAL: {
                "name": "Professional",
                "price": "$99/month",
                "price_monthly": 99,
                "description": "Complete toolkit for professionals",
                "features": []
            },
            FeatureTier.PREMIUM: {
                "name": "Premium",
                "price": "$199/month",
                "price_monthly": 199,
                "description": "Maximum power for heavy users",
                "features": []
            },
            FeatureTier.ENTERPRISE: {
                "name": "Enterprise",
                "price": "Custom pricing",
                "price_monthly": None,
                "description": "For teams and organizations",
                "features": []
            }
        }

        # Add featured capabilities for each tier
        important_features = [
            Feature.CASE_MONITORING,
            Feature.AI_ANALYSIS,
            Feature.DOCUMENT_DOWNLOAD,
            Feature.DOCUMENT_EXPORT,
            Feature.API_ACCESS,
            Feature.TEAM_COLLABORATION
        ]

        for tier, info in tiers_info.items():
            for feature in important_features:
                config = get_feature_config(tier, feature)
                if config.get("enabled"):
                    feature_info = {
                        "feature": feature.value,
                        "description": config.get("description"),
                        "limit": config.get("limit")
                    }
                    info["features"].append(feature_info)

        return {
            "current_tier": current_tier.value,
            "tiers": tiers_info
        }

    def grant_temporary_access(
        self,
        user_id: int,
        feature: Feature,
        duration_days: int = 30,
        reason: str = "Temporary access granted"
    ) -> UserFeatureOverride:
        """
        Grant temporary access to a feature (for trials, promos, etc.)

        Args:
            user_id: User to grant access to
            feature: Feature to grant access to
            duration_days: How many days the access lasts
            reason: Why access was granted

        Returns:
            UserFeatureOverride record
        """
        from datetime import timedelta

        expires_at = datetime.utcnow() + timedelta(days=duration_days)

        override = UserFeatureOverride(
            user_id=user_id,
            flag_key=feature.value,
            is_enabled=True,
            expires_at=expires_at,
            reason=reason
        )

        self.db.add(override)
        self.db.commit()
        self.db.refresh(override)

        return override
