"""
Feature Access API Endpoints
Provides endpoints for checking feature access and getting tier information
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.deps.database import get_db
from app.api.deps.feature_gates import (
    get_user_from_db,
    get_feature_gate_service
)
from app.core.feature_access import Feature, FeatureTier
from app.services.feature_gate_service import FeatureGateService
from app.models.user import User
from pydantic import BaseModel


router = APIRouter()


class FeatureAccessResponse(BaseModel):
    """Response model for feature access check"""
    feature: str
    has_access: bool
    tier: str
    config: Dict[str, Any]
    reason: str
    is_override: bool = False
    is_promotional: bool = False
    upgrade_info: Dict[str, Any] | None = None


class UserTierResponse(BaseModel):
    """Response model for user tier information"""
    tier: str
    tier_name: str
    features: List[Dict[str, Any]]
    limits: Dict[str, Any]


class TierComparisonResponse(BaseModel):
    """Response model for tier comparison"""
    current_tier: str
    tiers: Dict[str, Any]


@router.get(
    "/access",
    response_model=Dict[str, FeatureAccessResponse],
    summary="Get all feature access for current user"
)
async def get_all_feature_access(
    user: User = Depends(get_user_from_db),
    feature_service: FeatureGateService = Depends(get_feature_gate_service)
):
    """
    Get access status for all features for the current user

    Returns a dictionary mapping feature names to access status
    """
    result = {}

    for feature in Feature:
        access_check = feature_service.check_feature_access(user, feature)
        result[feature.value] = access_check

    return result


@router.get(
    "/access/{feature}",
    response_model=FeatureAccessResponse,
    summary="Check access to specific feature"
)
async def check_feature_access(
    feature: str,
    user: User = Depends(get_user_from_db),
    feature_service: FeatureGateService = Depends(get_feature_gate_service)
):
    """
    Check if current user has access to a specific feature

    Args:
        feature: Feature name to check (e.g., "ai_analysis", "pacer_search")

    Returns:
        Feature access information including upgrade details if locked
    """
    try:
        feature_enum = Feature(feature)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feature: {feature}"
        )

    access_check = feature_service.check_feature_access(user, feature_enum)
    return access_check


@router.get(
    "/tier",
    response_model=UserTierResponse,
    summary="Get current user's tier information"
)
async def get_user_tier(
    user: User = Depends(get_user_from_db),
    feature_service: FeatureGateService = Depends(get_feature_gate_service)
):
    """
    Get detailed information about the current user's tier

    Returns tier name, available features, and usage limits
    """
    tier = feature_service.get_user_tier(user)

    # Get all enabled features for this tier
    features = []
    limits = {}

    for feature in Feature:
        access_check = feature_service.check_feature_access(user, feature)

        if access_check["has_access"]:
            feature_info = {
                "feature": feature.value,
                "description": access_check["config"].get("description", ""),
                "limit": access_check["config"].get("limit")
            }
            features.append(feature_info)

            # Track limits
            limit = access_check["config"].get("limit")
            if limit is not None:
                limits[feature.value] = limit

    tier_names = {
        FeatureTier.FREE: "Free",
        FeatureTier.CASE_MONITOR: "Case Monitor",
        FeatureTier.PRO: "Pro",
        FeatureTier.FIRM: "Firm"
    }

    return {
        "tier": tier.value,
        "tier_name": tier_names.get(tier, tier.value),
        "features": features,
        "limits": limits
    }


@router.get(
    "/tiers/compare",
    response_model=TierComparisonResponse,
    summary="Compare all available tiers"
)
async def compare_tiers(
    user: User = Depends(get_user_from_db),
    feature_service: FeatureGateService = Depends(get_feature_gate_service)
):
    """
    Get comparison of all available tiers for upgrade decision

    Returns detailed feature comparison across all tiers
    """
    current_tier = feature_service.get_user_tier(user)
    comparison = feature_service.get_tier_comparison(current_tier)

    return comparison


@router.get(
    "/features/list",
    response_model=List[Dict[str, str]],
    summary="List all available features"
)
async def list_all_features():
    """
    Get list of all features in the system

    Returns list of feature names and descriptions
    """
    features = []

    for feature in Feature:
        features.append({
            "feature": feature.value,
            "name": feature.name.replace("_", " ").title()
        })

    return features


@router.post(
    "/usage/{feature}/track",
    summary="Track feature usage"
)
async def track_feature_usage(
    feature: str,
    quantity: int = 1,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db),
    feature_service: FeatureGateService = Depends(get_feature_gate_service)
):
    """
    Track usage of a metered feature

    Args:
        feature: Feature name
        quantity: Usage quantity (default 1)

    Returns:
        Updated usage information
    """
    try:
        feature_enum = Feature(feature)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feature: {feature}"
        )

    # Check if user has access to this feature
    access_check = feature_service.check_feature_access(user, feature_enum)

    if not access_check["has_access"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=access_check
        )

    # Track usage in database
    from app.models.billing import Usage, Subscription
    from datetime import datetime

    # Get user's current subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(["active", "trialing"])
    ).first()

    if subscription:
        usage_record = Usage(
            user_id=user.id,
            subscription_id=subscription.id,
            feature=feature,
            quantity=quantity,
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end
        )

        db.add(usage_record)
        db.commit()

        # Get updated usage count
        total_usage = db.query(Usage).filter(
            Usage.user_id == user.id,
            Usage.feature == feature,
            Usage.billing_period_start == subscription.current_period_start
        ).count()

        # Check against limit
        limit_check = feature_service.check_feature_limit(user, feature_enum, total_usage)

        return {
            "feature": feature,
            "quantity": quantity,
            "total_usage": total_usage,
            "limit": limit_check.get("limit"),
            "remaining": limit_check.get("remaining"),
            "reset_date": limit_check.get("reset_date")
        }

    return {
        "feature": feature,
        "quantity": quantity,
        "message": "Usage tracked (no active subscription)"
    }


@router.get(
    "/usage/{feature}",
    summary="Get feature usage statistics"
)
async def get_feature_usage(
    feature: str,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db),
    feature_service: FeatureGateService = Depends(get_feature_gate_service)
):
    """
    Get usage statistics for a feature

    Returns current usage, limit, and remaining quota
    """
    try:
        feature_enum = Feature(feature)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feature: {feature}"
        )

    # Get current usage
    from app.models.billing import Usage, Subscription

    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(["active", "trialing"])
    ).first()

    current_usage = 0
    if subscription:
        usage_records = db.query(Usage).filter(
            Usage.user_id == user.id,
            Usage.feature == feature,
            Usage.billing_period_start == subscription.current_period_start
        ).all()

        current_usage = sum(u.quantity for u in usage_records)

    # Check limit
    limit_check = feature_service.check_feature_limit(user, feature_enum, current_usage)

    return limit_check
