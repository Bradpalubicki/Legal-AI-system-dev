"""
Feature Gate Dependencies for FastAPI Routes

Provides dependency functions to protect routes with feature access control
"""

from typing import Callable
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.feature_access import Feature
from app.services.feature_gate_service import FeatureGateService
from app.api.deps.database import get_db
from app.models.user import User


def get_feature_gate_service(db: Session = Depends(get_db)) -> FeatureGateService:
    """Get feature gate service instance"""
    return FeatureGateService(db)


async def get_user_from_db(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Get full User object from database using authenticated user ID

    This extends the basic authentication to fetch the complete user record
    """
    # Get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, 'user_id', None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Fetch user from database
    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def require_feature(feature: Feature) -> Callable:
    """
    Dependency factory for feature-based access control

    Usage:
        @router.post("/documents/analyze")
        async def analyze_document(
            user: User = Depends(require_feature(Feature.AI_ANALYSIS))
        ):
            # Only users with AI_ANALYSIS feature can access this
            return {"status": "analyzing"}

    Args:
        feature: The feature required to access the endpoint

    Returns:
        Dependency function that checks feature access

    Raises:
        HTTPException: 402 Payment Required if user doesn't have access
        HTTPException: 403 Forbidden if feature is disabled globally
    """
    async def feature_checker(
        user: User = Depends(get_user_from_db),
        feature_service: FeatureGateService = Depends(get_feature_gate_service)
    ) -> User:
        # Check if user has access to this feature
        access_check = feature_service.check_feature_access(user, feature)

        if not access_check["has_access"]:
            # Prepare error response with upgrade information
            error_detail = {
                "error": "feature_access_denied",
                "feature": feature.value,
                "message": access_check.get("reason", "You don't have access to this feature"),
                "current_tier": access_check.get("tier"),
            }

            # Add upgrade information if available
            if "upgrade_info" in access_check:
                error_detail["upgrade"] = access_check["upgrade_info"]

            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=error_detail
            )

        return user

    return feature_checker


def check_feature_limit(feature: Feature, usage_field: str = None) -> Callable:
    """
    Dependency factory to check feature usage limits

    Usage:
        @router.post("/ai/analyze")
        async def ai_analyze(
            user: User = Depends(check_feature_limit(Feature.AI_ANALYSIS, "ai_analyses_this_month"))
        ):
            # Only proceeds if user hasn't exceeded their AI analysis limit
            return {"status": "analyzing"}

    Args:
        feature: The feature to check limits for
        usage_field: Optional field name to track usage (for custom tracking)

    Returns:
        Dependency function that checks usage limits
    """
    async def limit_checker(
        user: User = Depends(get_user_from_db),
        feature_service: FeatureGateService = Depends(get_feature_gate_service),
        db: Session = Depends(get_db)
    ) -> User:
        # First check if feature is accessible at all
        access_check = feature_service.check_feature_access(user, feature)

        if not access_check["has_access"]:
            error_detail = {
                "error": "feature_access_denied",
                "feature": feature.value,
                "message": access_check.get("reason"),
            }

            if "upgrade_info" in access_check:
                error_detail["upgrade"] = access_check["upgrade_info"]

            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=error_detail
            )

        # Check usage limits
        # Get current usage from Usage table or user object
        from app.models.billing import Usage, Subscription
        from datetime import datetime

        # Get user's current billing period
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(["active", "trialing"])
        ).first()

        current_usage = 0
        if subscription:
            # Count usage in current billing period
            usage_records = db.query(Usage).filter(
                Usage.user_id == user.id,
                Usage.feature == feature.value,
                Usage.billing_period_start == subscription.current_period_start
            ).all()

            current_usage = sum(u.quantity for u in usage_records)

        # Check if limit exceeded
        limit_check = feature_service.check_feature_limit(user, feature, current_usage)

        if not limit_check["has_access"]:
            error_detail = {
                "error": "feature_limit_exceeded",
                "feature": feature.value,
                "message": limit_check.get("reason", "You've exceeded your usage limit for this feature"),
                "limit": limit_check.get("limit"),
                "current_usage": limit_check.get("current_usage"),
                "remaining": limit_check.get("remaining"),
                "reset_date": limit_check.get("reset_date").isoformat() if limit_check.get("reset_date") else None
            }

            if "upgrade_info" in limit_check:
                error_detail["upgrade"] = limit_check["upgrade_info"]

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_detail
            )

        return user

    return limit_checker


async def check_optional_feature(
    feature: Feature,
    user: User = Depends(get_user_from_db),
    feature_service: FeatureGateService = Depends(get_feature_gate_service)
) -> dict:
    """
    Check feature access without blocking (for UI feature flags)

    Usage:
        @router.get("/dashboard")
        async def dashboard(
            user: User = Depends(get_user_from_db),
            ai_access: dict = Depends(lambda: check_optional_feature(Feature.AI_ANALYSIS))
        ):
            return {
                "ai_enabled": ai_access["has_access"],
                "features": {...}
            }

    Returns:
        Feature access dict (doesn't raise exception)
    """
    return feature_service.check_feature_access(user, feature)


def require_any_feature(*features: Feature) -> Callable:
    """
    Require user to have access to at least ONE of the specified features

    Usage:
        @router.get("/research")
        async def research(
            user: User = Depends(require_any_feature(
                Feature.PACER_SEARCH,
                Feature.COURTLISTENER_SEARCH
            ))
        ):
            return {"status": "ok"}

    Args:
        *features: Features (user needs access to at least one)

    Returns:
        Dependency function
    """
    async def any_feature_checker(
        user: User = Depends(get_user_from_db),
        feature_service: FeatureGateService = Depends(get_feature_gate_service)
    ) -> User:
        has_any_access = False

        for feature in features:
            access_check = feature_service.check_feature_access(user, feature)
            if access_check["has_access"]:
                has_any_access = True
                break

        if not has_any_access:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "no_feature_access",
                    "message": "You don't have access to any of the required features",
                    "required_features": [f.value for f in features]
                }
            )

        return user

    return any_feature_checker


def require_all_features(*features: Feature) -> Callable:
    """
    Require user to have access to ALL specified features

    Usage:
        @router.post("/advanced-analysis")
        async def advanced_analysis(
            user: User = Depends(require_all_features(
                Feature.AI_ANALYSIS,
                Feature.DOCUMENT_COMPARISON
            ))
        ):
            return {"status": "analyzing"}

    Args:
        *features: Features (user needs access to all)

    Returns:
        Dependency function
    """
    async def all_features_checker(
        user: User = Depends(get_user_from_db),
        feature_service: FeatureGateService = Depends(get_feature_gate_service)
    ) -> User:
        missing_features = []

        for feature in features:
            access_check = feature_service.check_feature_access(user, feature)
            if not access_check["has_access"]:
                missing_features.append({
                    "feature": feature.value,
                    "upgrade_info": access_check.get("upgrade_info")
                })

        if missing_features:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "missing_features",
                    "message": "You don't have access to all required features",
                    "missing": missing_features
                }
            )

        return user

    return all_features_checker
