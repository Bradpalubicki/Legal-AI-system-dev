"""
PACER API Endpoints

Provides access to PACER case search, document downloads, and cost tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date
import logging

from ..src.core.database import get_db
from ..src.services.pacer_service import PACERService, PACERServiceError
from ..models.user import User
from ..api.auth import get_current_user

logger = logging.getLogger(__name__)


# ============================================================================
# Local Dev Helper - Get or Create Test User
# ============================================================================
async def get_current_user_or_test(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user, or create a test user for local dev.

    This allows PACER to work without login during development.
    """
    # Check if user is authenticated via request.state.user_id
    user_id = getattr(request.state, 'user_id', None)

    if user_id:
        # User is authenticated, get their user object
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user

    # For local dev: use any existing user or create a simple one
    # Try to get any existing user first
    test_user = db.query(User).first()

    if test_user:
        return test_user

    # If no users exist, create a minimal test user
    # Use raw SQL to avoid model validation issues
    try:
        from sqlalchemy import text
        result = db.execute(text("""
            INSERT INTO users (email, username, hashed_password)
            VALUES ('test@local.dev', 'test_user', 'not_used')
        """))
        db.commit()

        # Now fetch the created user
        test_user = db.query(User).filter(User.email == 'test@local.dev').first()
        return test_user
    except:
        # If even that fails, just return a fake user object with minimal fields
        class FakeUser:
            id = "test-user-id"
            email = "test@local.dev"
            username = "test_user"

        return FakeUser()

router = APIRouter(prefix="/api/v1/pacer", tags=["PACER Integration"])


# ============================================================================
# PACER Service Status (SaaS Model)
# ============================================================================
@router.get("/status")
async def get_pacer_service_status(
    db: Session = Depends(get_db)
):
    """
    Get PACER service status.

    SaaS Model: Users don't need their own PACER credentials.
    The platform manages PACER access - users just need subscription credits.
    """
    service = PACERService(db)
    status = service.get_pacer_status()

    return {
        "success": True,
        **status,
        "info": {
            "requires_user_credentials": False,
            "access_method": "subscription_credits",
            "description": "PACER document access is included with your subscription. Use your credits to download documents."
        }
    }


# ============================================================================
# Test Endpoint (Development only)
# ============================================================================
@router.get("/test-auth")
async def test_auth_bypass(
    request: Request,
    db: Session = Depends(get_db)
):
    """Test if auth bypass works"""
    try:
        user = await get_current_user_or_test(request, db)
        return {
            "success": True,
            "message": "Auth bypass working",
            "user_id": user.id,
            "user_email": user.email
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# Request/Response Models
# ============================================================================

class PACERCredentialsCreate(BaseModel):
    """Request model for creating/updating PACER credentials"""
    pacer_username: str = Field(..., min_length=1, description="PACER username")
    pacer_password: str = Field(..., min_length=1, description="PACER password")
    client_code: Optional[str] = Field(None, description="PACER client code")
    environment: str = Field("production", description="Environment (production or qa)")
    daily_limit: float = Field(100.0, ge=0, description="Daily spending limit ($)")
    monthly_limit: float = Field(1000.0, ge=0, description="Monthly spending limit ($)")


class CaseSearchRequest(BaseModel):
    """Request model for case search"""
    case_number: Optional[str] = None
    case_title: Optional[str] = None
    court: Optional[str] = None
    filed_from: Optional[date] = None
    filed_to: Optional[date] = None
    closed_from: Optional[date] = None
    closed_to: Optional[date] = None
    nature_of_suit: Optional[str] = None
    case_status: Optional[str] = None
    judge_name: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PartySearchRequest(BaseModel):
    """Request model for party search"""
    party_name: str = Field(..., min_length=2)
    court: Optional[str] = None
    party_role: Optional[str] = None
    case_filed_from: Optional[date] = None
    case_filed_to: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# ============================================================================
# Credentials Status (SaaS Model - No user credentials needed)
# ============================================================================

@router.get("/credentials/status")
async def get_credentials_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_test)
):
    """
    Get PACER access status for user.

    SaaS Model: Users don't need their own PACER credentials.
    Access is controlled via subscription tier and credits.
    """
    service = PACERService(db)

    # Check if app-level credentials are configured
    if service.has_app_credentials():
        return {
            "success": True,
            "has_credentials": True,  # App has credentials, user doesn't need their own
            "is_verified": True,
            "mode": "platform_managed",
            "message": "PACER access is included with your subscription. No additional setup required.",
            "access_method": "subscription_credits"
        }
    else:
        return {
            "success": True,
            "has_credentials": False,
            "is_verified": False,
            "mode": "not_configured",
            "message": "PACER service is not currently available. Please contact support."
        }


@router.post("/credentials", status_code=status.HTTP_200_OK)
async def save_pacer_credentials(
    credentials: PACERCredentialsCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_test)
):
    """
    [DEPRECATED] User credentials are no longer required.

    SaaS Model: The platform manages PACER access.
    Users access PACER through their subscription credits.
    """
    return {
        "success": True,
        "message": "PACER credentials are no longer required. Your subscription includes PACER access.",
        "deprecated": True,
        "info": "Use your subscription credits to download PACER documents. No additional setup needed."
    }


@router.delete("/credentials")
async def delete_pacer_credentials(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_test)
):
    """
    [DEPRECATED] User credentials are no longer required.
    """
    # Clean up any legacy user credentials if they exist
    from ..models.pacer_credentials import UserPACERCredentials

    credentials = db.query(UserPACERCredentials).filter(
        UserPACERCredentials.user_id == current_user.id
    ).first()

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PACER credentials found"
        )

    db.delete(credentials)
    db.commit()

    return {
        "success": True,
        "message": "PACER credentials deleted successfully"
    }


# ============================================================================
# Authentication Endpoint
# ============================================================================

class AuthenticateRequest(BaseModel):
    """Request model for authentication"""
    otp: Optional[str] = Field(None, description="One-time password for MFA")
    force_refresh: bool = Field(False, description="Force re-authentication")
    test_mode: bool = Field(False, description="Enable test mode (bypass real PACER)")


@router.post("/authenticate")
async def authenticate_pacer(
    auth_request: Optional[AuthenticateRequest] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_test)
):
    """
    Authenticate with PACER and verify credentials.

    Supports MFA via optional OTP parameter.
    Supports test_mode to bypass real PACER authentication.
    Returns success status and caches authentication token.
    """
    logger.info(f"[PACER ENDPOINT] Starting authentication for user {current_user.id if current_user else 'None'}")

    service = PACERService(db)

    # Import model at top
    from app.models.pacer_credentials import UserPACERCredentials

    try:
        # Extract parameters from auth_request if provided
        otp = auth_request.otp if auth_request else None
        force_refresh = auth_request.force_refresh if auth_request else False
        test_mode = auth_request.test_mode if auth_request else False

        # Auto-enable test mode for test credentials
        if not test_mode:
            creds = db.query(UserPACERCredentials).filter(
                UserPACERCredentials.user_id == current_user.id,
                UserPACERCredentials.is_active == True
            ).first()
            if creds:
                username_lower = creds.pacer_username.lower()
                # Enable test mode for test/example credentials
                if 'test' in username_lower or 'example' in username_lower or '@example.' in username_lower:
                    test_mode = True
                    logger.info(f"Auto-enabling test mode for user {current_user.id} with test credentials")

        logger.info(f"[PACER ENDPOINT] Calling service.authenticate_user")

        try:
            token = await service.authenticate_user(
                user_id=current_user.id,
                otp=otp,
                force_refresh=force_refresh,
                test_mode=test_mode
            )
            logger.info(f"[PACER ENDPOINT] Authentication succeeded")
        except Exception as svc_err:
            logger.error(f"[PACER ENDPOINT] Service error: {type(svc_err).__name__}: {str(svc_err)}")
            raise

        return {
            "success": True,
            "message": "Successfully authenticated with PACER" + (" (TEST MODE)" if test_mode else ""),
            "token_cached": True,
            "test_mode": test_mode
        }

    except PACERServiceError as e:
        logger.error(f"[PACER ENDPOINT] PACERServiceError: {str(e)}")
        # Determine appropriate HTTP status code based on error message
        if "rate limit" in str(e).lower():
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif "invalid" in str(e).lower() or "credentials" in str(e).lower():
            status_code = status.HTTP_401_UNAUTHORIZED
        elif "mfa" in str(e).lower() or "one-time" in str(e).lower():
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )


# ============================================================================
# Search Endpoints
# ============================================================================

@router.post("/search/cases")
async def search_cases(
    search_request: CaseSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_test)
):
    """
    Search PACER for cases.

    Supports filtering by court, case number, title, filing dates, etc.
    Case searches are FREE (no PACER charges).
    """
    # Fixed authentication to work in dev mode
    service = PACERService(db)

    try:
        results = await service.search_cases(
            user_id=current_user.id,
            **search_request.dict(exclude_none=True)
        )

        return results

    except PACERServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/search/parties")
async def search_parties(
    search_request: PartySearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_test)
):
    """
    Search PACER for parties by name.

    Party searches are FREE (no PACER charges).
    """
    service = PACERService(db)

    try:
        results = await service.search_parties(
            user_id=current_user.id,
            **search_request.dict(exclude_none=True)
        )

        return results

    except PACERServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Statistics & Usage Endpoints
# ============================================================================

@router.get("/stats")
async def get_pacer_stats(
    request: Request,
    current_user: User = Depends(get_current_user_or_test),
    db: Session = Depends(get_db)
):
    """
    Get user's PACER usage statistics.

    Includes:
    - Total searches and downloads
    - Cost tracking (daily/monthly spending)
    - Recent search history
    - Cost limits and remaining budget
    """
    service = PACERService(db)

    try:
        stats = service.get_user_stats(current_user.id)
        return {
            "success": True,
            **stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/history/searches")
async def get_search_history(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user_or_test),
    db: Session = Depends(get_db)
):
    """
    Get user's PACER search history.
    """
    from ..models.pacer_credentials import PACERSearchHistory

    searches = db.query(PACERSearchHistory).filter(
        PACERSearchHistory.user_id == current_user.id
    ).order_by(
        PACERSearchHistory.timestamp.desc()
    ).offset(offset).limit(limit).all()

    total = db.query(PACERSearchHistory).filter(
        PACERSearchHistory.user_id == current_user.id
    ).count()

    return {
        "success": True,
        "searches": [{
            "id": s.id,
            "type": s.search_type,
            "criteria": s.search_criteria,
            "results_count": s.results_count,
            "court": s.court,
            "cost": s.search_cost,
            "timestamp": s.timestamp.isoformat()
        } for s in searches],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/history/documents")
async def get_document_history(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user_or_test),
    db: Session = Depends(get_db)
):
    """
    Get user's downloaded PACER documents.
    """
    from ..models.pacer_credentials import PACERDocument

    documents = db.query(PACERDocument).filter(
        PACERDocument.user_id == current_user.id
    ).order_by(
        PACERDocument.downloaded_at.desc()
    ).offset(offset).limit(limit).all()

    total = db.query(PACERDocument).filter(
        PACERDocument.user_id == current_user.id
    ).count()

    return {
        "success": True,
        "documents": [{
            "id": d.id,
            "document_id": d.document_id,
            "case_id": d.case_id,
            "title": d.title,
            "document_type": d.document_type,
            "court": d.court,
            "page_count": d.page_count,
            "download_cost": d.download_cost,
            "downloaded_at": d.downloaded_at.isoformat()
        } for d in documents],
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ============================================================================
# Cost Tracking Endpoints
# ============================================================================

@router.get("/costs/summary")
async def get_cost_summary(
    request: Request,
    days: int = 30,
    current_user: User = Depends(get_current_user_or_test),
    db: Session = Depends(get_db)
):
    """
    Get detailed cost summary for specified period.
    """
    from ..models.pacer_credentials import PACERCostTracking
    from datetime import datetime, timedelta
    from sqlalchemy import func

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get costs for period
    costs = db.query(PACERCostTracking).filter(
        PACERCostTracking.user_id == current_user.id,
        PACERCostTracking.timestamp >= cutoff_date
    ).all()

    # Calculate totals
    total_cost = sum(c.cost for c in costs)
    total_operations = len(costs)

    # Group by operation type
    by_operation = {}
    for cost in costs:
        op_type = cost.operation_type
        if op_type not in by_operation:
            by_operation[op_type] = {"count": 0, "total_cost": 0.0}
        by_operation[op_type]["count"] += 1
        by_operation[op_type]["total_cost"] += cost.cost

    # Group by court
    by_court = {}
    for cost in costs:
        if cost.court:
            if cost.court not in by_court:
                by_court[cost.court] = {"count": 0, "total_cost": 0.0}
            by_court[cost.court]["count"] += 1
            by_court[cost.court]["total_cost"] += cost.cost

    return {
        "success": True,
        "period_days": days,
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_operations": total_operations,
            "average_per_operation": round(total_cost / total_operations, 2) if total_operations > 0 else 0
        },
        "by_operation": by_operation,
        "by_court": by_court
    }


# ============================================================================
# Monitoring & Security Endpoints
# ============================================================================

@router.get("/monitoring/rate-limit")
async def get_rate_limit_status(
    request: Request,
    current_user: User = Depends(get_current_user_or_test),
    db: Session = Depends(get_db)
):
    """
    Get rate limit status for current user.

    Returns:
        Rate limit information including attempts, remaining, and reset time
    """
    service = PACERService(db)

    try:
        status_info = await service.get_rate_limit_status(current_user.id)
        return {
            "success": True,
            **status_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )


@router.post("/monitoring/rate-limit/clear")
async def clear_rate_limit(
    request: Request,
    current_user: User = Depends(get_current_user_or_test),
    db: Session = Depends(get_db)
):
    """
    Clear rate limit for current user.

    This is useful if a user was temporarily rate-limited and wants to reset.
    Note: Should be used carefully and possibly restricted to admins in production.
    """
    service = PACERService(db)

    try:
        result = await service.clear_rate_limit(current_user.id)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to clear rate limit")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear rate limit: {str(e)}"
        )


# ============================================================================
# Document Download Endpoint
# ============================================================================

class DownloadDocumentRequest(BaseModel):
    """Request model for document download"""
    document_url: str = Field(..., description="PACER document URL")
    case_id: str = Field(..., description="Case identifier")
    document_id: str = Field(..., description="Document identifier")
    court: Optional[str] = Field(None, description="Court identifier (e.g., 'canb')")
    estimated_pages: int = Field(1, description="Estimated number of pages", ge=1)
    save_to_disk: bool = Field(True, description="Whether to save document to disk")


@router.post("/documents/download")
async def download_document(
    request: DownloadDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_test)
):
    """
    Download a document from PACER.

    This endpoint:
    - Authenticates with PACER using cached token
    - Downloads the specified document
    - Tracks costs and updates limits
    - Optionally saves to disk
    - Records download in database

    Cost: $0.10 per page, capped at $3.00 per document
    """
    service = PACERService(db)

    try:
        result = await service.download_document(
            user_id=current_user.id,
            document_url=request.document_url,
            case_id=request.case_id,
            document_id=request.document_id,
            court=request.court,
            estimated_pages=request.estimated_pages,
            save_to_disk=request.save_to_disk
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Document download failed")
            )

        return result

    except PACERServiceError as e:
        error_str = str(e).lower()
        if "cost limit" in error_str or "exceeded" in error_str:
            status_code = status.HTTP_402_PAYMENT_REQUIRED
        elif "not found" in error_str:
            status_code = status.HTTP_404_NOT_FOUND
        elif "unauthorized" in error_str or "credentials" in error_str:
            status_code = status.HTTP_401_UNAUTHORIZED
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(status_code=status_code, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download document: {str(e)}"
        )


@router.post("/logout")
async def logout_pacer(
    request: Request,
    current_user: User = Depends(get_current_user_or_test),
    db: Session = Depends(get_db)
):
    """
    Logout from PACER by invalidating cached authentication token.

    This forces a new authentication on the next request.
    Useful when:
    - Switching PACER accounts
    - Security concerns about cached token
    - Testing authentication flow
    """
    service = PACERService(db)

    try:
        result = await service.logout_user(current_user.id)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Logout failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to logout: {str(e)}"
        )
