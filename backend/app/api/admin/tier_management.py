"""
Tier Management Admin API
Admin endpoints for managing pricing tiers, feature flags, and promotions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from app.api.deps.database import get_db
from app.api.deps.auth import get_admin_user
from app.models.user import User, UserRole
from app.models.feature_flags import FeatureFlag, UserFeatureOverride, PromotionalCampaign
from app.models.billing import Subscription
from app.core.feature_access import Feature, FeatureTier
from app.services.feature_gate_service import FeatureGateService


router = APIRouter(prefix="/api/v1/admin/tiers", tags=["admin-tiers"])


# ============================================================================
# Request/Response Models
# ============================================================================

class FeatureFlagUpdate(BaseModel):
    """Update feature flag"""
    is_enabled: bool
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    enabled_at: Optional[datetime] = None
    disabled_at: Optional[datetime] = None


class UserOverrideCreate(BaseModel):
    """Create user feature override"""
    user_id: int
    flag_key: str
    is_enabled: bool
    expires_at: Optional[datetime] = None
    reason: str


class PromotionalCampaignCreate(BaseModel):
    """Create promotional campaign"""
    name: str
    description: str
    campaign_type: str  # free_credits, discount, unlimited_access
    discount_percentage: Optional[float] = None
    free_credits: Optional[int] = None
    unlimited_searches: Optional[bool] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    max_redemptions: Optional[int] = None
    new_users_only: bool = False


class TierChangeRequest(BaseModel):
    """Change user's tier"""
    user_id: int
    new_tier: str  # free, case_monitor, pro, firm
    reason: str


# ============================================================================
# Feature Flag Management
# ============================================================================

@router.get("/feature-flags")
async def list_feature_flags(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all feature flags"""
    flags = db.query(FeatureFlag).all()

    return [{
        "id": flag.id,
        "flag_key": flag.flag_key,
        "description": flag.description,
        "is_enabled": flag.is_enabled,
        "value_string": flag.value_string,
        "value_number": flag.value_number,
        "enabled_at": flag.enabled_at,
        "disabled_at": flag.disabled_at,
        "created_at": flag.created_at
    } for flag in flags]


@router.post("/feature-flags/{flag_key}")
async def update_feature_flag(
    flag_key: str,
    update: FeatureFlagUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update or create feature flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.flag_key == flag_key).first()

    if not flag:
        # Create new flag
        flag = FeatureFlag(
            flag_key=flag_key,
            is_enabled=update.is_enabled,
            value_string=update.value_string,
            value_number=update.value_number,
            enabled_at=update.enabled_at,
            disabled_at=update.disabled_at
        )
        db.add(flag)
    else:
        # Update existing
        flag.is_enabled = update.is_enabled
        if update.value_string is not None:
            flag.value_string = update.value_string
        if update.value_number is not None:
            flag.value_number = update.value_number
        if update.enabled_at is not None:
            flag.enabled_at = update.enabled_at
        if update.disabled_at is not None:
            flag.disabled_at = update.disabled_at

    db.commit()
    db.refresh(flag)

    return {"message": f"Feature flag '{flag_key}' updated", "flag": flag}


# ============================================================================
# User Overrides
# ============================================================================

@router.post("/user-overrides")
async def create_user_override(
    override: UserOverrideCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create feature override for specific user"""
    # Verify user exists
    user = db.query(User).filter(User.id == override.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create override
    user_override = UserFeatureOverride(
        user_id=override.user_id,
        flag_key=override.flag_key,
        is_enabled=override.is_enabled,
        expires_at=override.expires_at,
        reason=override.reason
    )

    db.add(user_override)
    db.commit()
    db.refresh(user_override)

    return {
        "message": f"Override created for user {user.email}",
        "override": user_override
    }


@router.get("/user-overrides/{user_id}")
async def list_user_overrides(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all overrides for a user"""
    overrides = db.query(UserFeatureOverride).filter(
        UserFeatureOverride.user_id == user_id
    ).all()

    return overrides


# ============================================================================
# Promotional Campaigns
# ============================================================================

@router.post("/campaigns")
async def create_campaign(
    campaign: PromotionalCampaignCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create promotional campaign"""
    new_campaign = PromotionalCampaign(
        name=campaign.name,
        description=campaign.description,
        campaign_type=campaign.campaign_type,
        discount_percentage=campaign.discount_percentage,
        free_credits=campaign.free_credits,
        unlimited_searches=campaign.unlimited_searches,
        starts_at=campaign.starts_at,
        ends_at=campaign.ends_at,
        max_redemptions=campaign.max_redemptions,
        new_users_only=campaign.new_users_only,
        is_active=True
    )

    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    return {
        "message": f"Campaign '{campaign.name}' created",
        "campaign": new_campaign
    }


@router.get("/campaigns")
async def list_campaigns(
    active_only: bool = False,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all promotional campaigns"""
    query = db.query(PromotionalCampaign)

    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            PromotionalCampaign.is_active == True,
            PromotionalCampaign.starts_at <= now
        ).filter(
            (PromotionalCampaign.ends_at == None) |
            (PromotionalCampaign.ends_at > now)
        )

    campaigns = query.all()
    return campaigns


@router.post("/campaigns/{campaign_id}/deactivate")
async def deactivate_campaign(
    campaign_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate a campaign"""
    campaign = db.query(PromotionalCampaign).filter(
        PromotionalCampaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.is_active = False
    db.commit()

    return {"message": f"Campaign '{campaign.name}' deactivated"}


# ============================================================================
# Tier Management
# ============================================================================

@router.post("/change-tier")
async def change_user_tier(
    request: TierChangeRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Manually change user's tier (for testing, migrations, etc.)"""
    user = db.query(User).filter(User.id == request.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Map tier names to roles
    tier_role_map = {
        "free": UserRole.GUEST,
        "case_monitor": UserRole.CLIENT,
        "pro": UserRole.USER,
        "firm": UserRole.ATTORNEY
    }

    if request.new_tier not in tier_role_map:
        raise HTTPException(status_code=400, detail="Invalid tier")

    # Update user role
    old_role = user.role
    user.role = tier_role_map[request.new_tier]

    db.commit()

    return {
        "message": f"User tier changed from {old_role.value} to {request.new_tier}",
        "user_id": user.id,
        "email": user.email,
        "old_tier": old_role.value,
        "new_tier": request.new_tier,
        "reason": request.reason
    }


@router.get("/tier-stats")
async def get_tier_statistics(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get statistics on tier distribution"""
    from sqlalchemy import func

    # Count users by role
    role_counts = db.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()

    # Count active subscriptions by tier
    subscription_counts = db.query(
        func.count(Subscription.id).label('count')
    ).filter(
        Subscription.status.in_(["active", "trialing"])
    ).scalar()

    return {
        "users_by_role": [{
            "role": role.value,
            "count": count
        } for role, count in role_counts],
        "active_subscriptions": subscription_counts,
        "total_users": sum(count for _, count in role_counts)
    }


# ============================================================================
# Launch Presets
# ============================================================================

@router.post("/presets/beta-launch")
async def apply_beta_launch_preset(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Apply beta launch configuration:
    - Disable credit requirements
    - Enable all features for all users
    - Create welcome campaign
    """
    # Disable credit requirements
    credits_flag = db.query(FeatureFlag).filter(
        FeatureFlag.flag_key == "credits_enabled"
    ).first()

    if not credits_flag:
        credits_flag = FeatureFlag(
            flag_key="credits_enabled",
            is_enabled=False,
            description="Beta launch - credits disabled"
        )
        db.add(credits_flag)

    credits_flag.is_enabled = False

    # Create welcome campaign
    welcome_campaign = PromotionalCampaign(
        name="Beta Launch - Free Access",
        description="Free access to all features during beta",
        campaign_type="unlimited_access",
        unlimited_searches=True,
        starts_at=datetime.utcnow(),
        ends_at=datetime.utcnow() + timedelta(days=30),
        is_active=True,
        new_users_only=False
    )

    db.add(welcome_campaign)
    db.commit()

    return {
        "message": "Beta launch preset applied",
        "changes": [
            "Credits disabled",
            "30-day free access campaign created",
            "All features unlocked for testing"
        ]
    }


@router.post("/presets/production-launch")
async def apply_production_launch_preset(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Apply production launch configuration:
    - Enable credit requirements
    - Enable tier-based access
    - Create launch promotion
    """
    # Enable credits
    credits_flag = db.query(FeatureFlag).filter(
        FeatureFlag.flag_key == "credits_enabled"
    ).first()

    if not credits_flag:
        credits_flag = FeatureFlag(
            flag_key="credits_enabled",
            is_enabled=True,
            description="Production - credits enabled"
        )
        db.add(credits_flag)

    credits_flag.is_enabled = True

    # Create launch promotion
    launch_promo = PromotionalCampaign(
        name="Launch Special - 20% Off",
        description="20% off Pro and Firm plans for first 3 months",
        campaign_type="discount",
        discount_percentage=20.0,
        starts_at=datetime.utcnow(),
        ends_at=datetime.utcnow() + timedelta(days=90),
        max_redemptions=1000,
        is_active=True,
        new_users_only=True
    )

    db.add(launch_promo)
    db.commit()

    return {
        "message": "Production launch preset applied",
        "changes": [
            "Credits enabled",
            "Tier-based access enforced",
            "20% launch discount for new users (90 days)"
        ]
    }
