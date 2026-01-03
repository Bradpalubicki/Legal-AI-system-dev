"""
Case Access Dependencies
FastAPI dependencies for validating case access
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.database import get_db
from app.api.deps.feature_gates import get_user_from_db
from app.models.user import User
from app.services.case_access_service import CaseAccessService


def get_case_access_service(db: Session = Depends(get_db)) -> CaseAccessService:
    """Get case access service instance"""
    return CaseAccessService(db)


def require_case_access(case_id: int):
    """
    Dependency factory to require case access

    Usage:
        @router.get("/cases/{case_id}")
        async def get_case(
            case_id: int,
            user: User = Depends(require_case_access(case_id))
        ):
            # User is guaranteed to have access to case_id
            return case_data

    Args:
        case_id: ID of the case to check access for

    Returns:
        Dependency function that validates access
    """
    async def access_checker(
        user: User = Depends(get_user_from_db),
        case_service: CaseAccessService = Depends(get_case_access_service)
    ) -> User:
        # Check if user has access
        access_check = case_service.check_user_access(user, case_id)

        if not access_check["has_access"]:
            # Prepare detailed error response
            error_detail = {
                "error": "case_access_denied",
                "message": access_check.get("reason", "You don't have access to this case"),
                "case_id": case_id,
                "purchase_options": access_check.get("purchase_options", [])
            }

            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=error_detail
            )

        return user

    return access_checker


async def get_accessible_cases(
    user: User = Depends(get_user_from_db),
    case_service: CaseAccessService = Depends(get_case_access_service)
) -> list:
    """
    Get all cases the current user has access to

    Usage:
        @router.get("/cases")
        async def list_cases(
            accessible_cases: list = Depends(get_accessible_cases)
        ):
            return accessible_cases
    """
    return case_service.get_user_cases(user)


async def check_case_access_optional(
    case_id: int,
    user: User = Depends(get_user_from_db),
    case_service: CaseAccessService = Depends(get_case_access_service)
) -> dict:
    """
    Check case access without raising error (for UI flags)

    Returns access information that can be used to show/hide features

    Usage:
        @router.get("/cases/{case_id}/info")
        async def case_info(
            case_id: int,
            access_info: dict = Depends(check_case_access_optional)
        ):
            return {
                "case": case_data,
                "user_access": access_info
            }
    """
    return case_service.check_user_access(user, case_id)
