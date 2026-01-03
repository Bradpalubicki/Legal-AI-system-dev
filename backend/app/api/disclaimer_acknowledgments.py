"""
Disclaimer Acknowledgment API Endpoints

Tracks when users:
1. Confirm/acknowledge liability disclaimers
2. Disable/dismiss liability portions
3. View disclaimers multiple times

Critical for legal compliance and professional responsibility tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from ..src.core.database import get_db
from ..models.user import User
from ..models.disclaimer_acknowledgment import (
    DisclaimerAcknowledgment,
    DisclaimerTemplate,
    DisclaimerType,
    RiskLevel,
    AcknowledgmentAction
)
from ..api.deps.auth import get_current_user, get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/disclaimers", tags=["disclaimers"])


# =============================================================================
# REQUEST MODELS
# =============================================================================

class AcknowledgeDisclaimerRequest(BaseModel):
    """Request to acknowledge a disclaimer"""
    disclaimer_id: str
    disclaimer_type: str
    page_url: Optional[str] = None
    page_context: Optional[str] = None
    jurisdiction: Optional[str] = None
    time_to_acknowledge: Optional[float] = None  # seconds
    time_on_page: Optional[float] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DismissDisclaimerRequest(BaseModel):
    """Request to dismiss/disable a disclaimer"""
    disclaimer_id: str
    disclaimer_type: str
    reason: Optional[str] = None
    page_url: Optional[str] = None
    page_context: Optional[str] = None
    session_id: Optional[str] = None


class ViewDisclaimerRequest(BaseModel):
    """Request to record disclaimer view"""
    disclaimer_id: str
    disclaimer_type: str
    page_url: Optional[str] = None
    page_context: Optional[str] = None
    time_on_page: Optional[float] = None
    session_id: Optional[str] = None


class AcknowledgmentQueryParams(BaseModel):
    """Query parameters for acknowledgment history"""
    disclaimer_type: Optional[str] = None
    user_id: Optional[int] = None
    acknowledged: Optional[bool] = None
    risk_level: Optional[str] = None
    jurisdiction: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_risk_level(
    view_count: int,
    time_to_acknowledge: Optional[float],
    is_mandatory: bool,
    acknowledged: bool
) -> RiskLevel:
    """
    Calculate risk level based on user behavior.
    High risk = user repeatedly viewing without acknowledging mandatory disclaimers
    """
    if acknowledged:
        return RiskLevel.LOW

    if not is_mandatory:
        return RiskLevel.LOW

    # Critical risk: viewed 5+ times without acknowledgment on mandatory disclaimer
    if view_count >= 5:
        return RiskLevel.CRITICAL

    # High risk: viewed 3-4 times
    if view_count >= 3:
        return RiskLevel.HIGH

    # Medium risk: viewed 2 times
    if view_count >= 2:
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request"""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }


# =============================================================================
# ACKNOWLEDGMENT ENDPOINTS
# =============================================================================

@router.post("/acknowledge")
async def acknowledge_disclaimer(
    req: AcknowledgeDisclaimerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record when a user confirms/acknowledges a liability disclaimer.

    This is critical for legal compliance - tracks explicit user consent.
    """
    try:
        client_info = get_client_info(request)

        # Check if user has previously viewed this disclaimer
        existing = db.query(DisclaimerAcknowledgment).filter(
            and_(
                DisclaimerAcknowledgment.user_id == current_user.id,
                DisclaimerAcknowledgment.disclaimer_id == req.disclaimer_id,
                DisclaimerAcknowledgment.acknowledged == False
            )
        ).first()

        if existing:
            # Update existing record
            existing.acknowledged = True
            existing.acknowledged_at = datetime.utcnow()
            existing.action = AcknowledgmentAction.ACKNOWLEDGED
            existing.time_to_acknowledge = req.time_to_acknowledge or existing.time_to_acknowledge
            existing.time_on_page = req.time_on_page
            existing.risk_level = RiskLevel.LOW  # Acknowledged = low risk
            existing.updated_at = datetime.utcnow()

            if req.metadata:
                existing.extra_data = json.dumps(req.metadata)

            acknowledgment = existing
        else:
            # Create new acknowledgment record
            acknowledgment = DisclaimerAcknowledgment(
                user_id=current_user.id,
                user_type=current_user.role or "user",
                disclaimer_type=DisclaimerType(req.disclaimer_type),
                disclaimer_id=req.disclaimer_id,
                action=AcknowledgmentAction.ACKNOWLEDGED,
                acknowledged=True,
                acknowledged_at=datetime.utcnow(),
                view_count=1,
                time_to_acknowledge=req.time_to_acknowledge,
                time_on_page=req.time_on_page,
                page_url=req.page_url,
                page_context=req.page_context,
                jurisdiction=req.jurisdiction,
                session_id=req.session_id,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                risk_level=RiskLevel.LOW,
                is_mandatory=True,
                extra_data=json.dumps(req.metadata) if req.metadata else None
            )
            db.add(acknowledgment)

        db.commit()
        db.refresh(acknowledgment)

        logger.info(
            f"User {current_user.id} acknowledged disclaimer {req.disclaimer_id} "
            f"(type: {req.disclaimer_type})"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Disclaimer acknowledged successfully",
                "acknowledgment_id": str(acknowledgment.id),
                "acknowledged_at": acknowledgment.acknowledged_at.isoformat(),
                "risk_level": acknowledgment.risk_level.value
            }
        )

    except Exception as e:
        logger.error(f"Error acknowledging disclaimer: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record acknowledgment: {str(e)}"
        )


@router.post("/dismiss")
async def dismiss_disclaimer(
    req: DismissDisclaimerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record when a user dismisses or disables a liability disclaimer.

    This is tracked for compliance - indicates user chose not to acknowledge.
    May trigger follow-up or risk assessment.
    """
    try:
        client_info = get_client_info(request)

        # Check for existing record
        existing = db.query(DisclaimerAcknowledgment).filter(
            and_(
                DisclaimerAcknowledgment.user_id == current_user.id,
                DisclaimerAcknowledgment.disclaimer_id == req.disclaimer_id
            )
        ).order_by(desc(DisclaimerAcknowledgment.created_at)).first()

        if existing:
            # Increment view count and update
            existing.view_count += 1
            existing.action = AcknowledgmentAction.DISMISSED
            existing.dismissed_at = datetime.utcnow()
            existing.risk_level = calculate_risk_level(
                existing.view_count,
                existing.time_to_acknowledge,
                existing.is_mandatory,
                False
            )
            existing.updated_at = datetime.utcnow()

            # Flag for follow-up if high risk
            if existing.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                existing.follow_up_required = True
                existing.follow_up_reason = (
                    f"User dismissed mandatory disclaimer {existing.view_count} times. "
                    f"Reason: {req.reason or 'Not provided'}"
                )

            acknowledgment = existing
        else:
            # Create new record showing dismissal
            acknowledgment = DisclaimerAcknowledgment(
                user_id=current_user.id,
                user_type=current_user.role or "user",
                disclaimer_type=DisclaimerType(req.disclaimer_type),
                disclaimer_id=req.disclaimer_id,
                action=AcknowledgmentAction.DISMISSED,
                acknowledged=False,
                dismissed_at=datetime.utcnow(),
                view_count=1,
                page_url=req.page_url,
                page_context=req.page_context,
                session_id=req.session_id,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                risk_level=RiskLevel.MEDIUM,  # Dismissal = medium risk
                is_mandatory=True,
                follow_up_required=False,
                follow_up_reason=req.reason
            )
            db.add(acknowledgment)

        db.commit()
        db.refresh(acknowledgment)

        logger.warning(
            f"User {current_user.id} dismissed disclaimer {req.disclaimer_id} "
            f"(view count: {acknowledgment.view_count}, risk: {acknowledgment.risk_level.value})"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Disclaimer dismissal recorded",
                "acknowledgment_id": str(acknowledgment.id),
                "dismissed_at": acknowledgment.dismissed_at.isoformat(),
                "view_count": acknowledgment.view_count,
                "risk_level": acknowledgment.risk_level.value,
                "follow_up_required": acknowledgment.follow_up_required
            }
        )

    except Exception as e:
        logger.error(f"Error recording disclaimer dismissal: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record dismissal: {str(e)}"
        )


@router.post("/view")
async def record_disclaimer_view(
    req: ViewDisclaimerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record when a user views a disclaimer (without acknowledging yet).
    Tracks repeated views which may indicate confusion or avoidance.
    """
    try:
        client_info = get_client_info(request)

        # Check for existing unacknowledged record
        existing = db.query(DisclaimerAcknowledgment).filter(
            and_(
                DisclaimerAcknowledgment.user_id == current_user.id,
                DisclaimerAcknowledgment.disclaimer_id == req.disclaimer_id,
                DisclaimerAcknowledgment.acknowledged == False
            )
        ).first()

        if existing:
            # Increment view count
            existing.view_count += 1
            existing.time_on_page = req.time_on_page
            existing.risk_level = calculate_risk_level(
                existing.view_count,
                existing.time_to_acknowledge,
                existing.is_mandatory,
                False
            )
            existing.updated_at = datetime.utcnow()
            acknowledgment = existing
        else:
            # Create new view record
            acknowledgment = DisclaimerAcknowledgment(
                user_id=current_user.id,
                user_type=current_user.role or "user",
                disclaimer_type=DisclaimerType(req.disclaimer_type),
                disclaimer_id=req.disclaimer_id,
                action=AcknowledgmentAction.VIEWED,
                acknowledged=False,
                view_count=1,
                time_on_page=req.time_on_page,
                page_url=req.page_url,
                page_context=req.page_context,
                session_id=req.session_id,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                risk_level=RiskLevel.LOW,
                is_mandatory=True
            )
            db.add(acknowledgment)

        db.commit()
        db.refresh(acknowledgment)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "acknowledgment_id": str(acknowledgment.id),
                "view_count": acknowledgment.view_count,
                "risk_level": acknowledgment.risk_level.value
            }
        )

    except Exception as e:
        logger.error(f"Error recording disclaimer view: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record view: {str(e)}"
        )


@router.get("/status/{disclaimer_id}")
async def get_disclaimer_status(
    disclaimer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's acknowledgment status for a specific disclaimer.
    """
    try:
        acknowledgment = db.query(DisclaimerAcknowledgment).filter(
            and_(
                DisclaimerAcknowledgment.user_id == current_user.id,
                DisclaimerAcknowledgment.disclaimer_id == disclaimer_id
            )
        ).order_by(desc(DisclaimerAcknowledgment.updated_at)).first()

        if not acknowledgment:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "acknowledged": False,
                    "view_count": 0,
                    "risk_level": "low"
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "acknowledged": acknowledgment.acknowledged,
                "acknowledged_at": acknowledgment.acknowledged_at.isoformat() if acknowledgment.acknowledged_at else None,
                "view_count": acknowledgment.view_count,
                "risk_level": acknowledgment.risk_level.value,
                "follow_up_required": acknowledgment.follow_up_required,
                "needs_re_acknowledgment": acknowledgment.needs_re_acknowledgment
            }
        )

    except Exception as e:
        logger.error(f"Error getting disclaimer status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


# =============================================================================
# ADMIN ENDPOINTS - View All Acknowledgments
# =============================================================================

@router.get("/admin/acknowledgments")
async def get_all_acknowledgments(
    disclaimer_type: Optional[str] = None,
    user_id: Optional[int] = None,
    acknowledged: Optional[bool] = None,
    risk_level: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get all disclaimer acknowledgments (admin only).
    Supports filtering and pagination.
    """
    try:
        query = db.query(DisclaimerAcknowledgment)

        # Apply filters
        if disclaimer_type:
            query = query.filter(DisclaimerAcknowledgment.disclaimer_type == DisclaimerType(disclaimer_type))

        if user_id:
            query = query.filter(DisclaimerAcknowledgment.user_id == user_id)

        if acknowledged is not None:
            query = query.filter(DisclaimerAcknowledgment.acknowledged == acknowledged)

        if risk_level:
            query = query.filter(DisclaimerAcknowledgment.risk_level == RiskLevel(risk_level))

        if jurisdiction:
            query = query.filter(DisclaimerAcknowledgment.jurisdiction == jurisdiction)

        if start_date:
            query = query.filter(DisclaimerAcknowledgment.created_at >= datetime.fromisoformat(start_date))

        if end_date:
            query = query.filter(DisclaimerAcknowledgment.created_at <= datetime.fromisoformat(end_date))

        # Get total count
        total = query.count()

        # Get paginated results
        acknowledgments = query.order_by(
            desc(DisclaimerAcknowledgment.created_at)
        ).limit(limit).offset(offset).all()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "total": total,
                "limit": limit,
                "offset": offset,
                "acknowledgments": [ack.to_dict(include_pii=False) for ack in acknowledgments]
            }
        )

    except Exception as e:
        logger.error(f"Error fetching acknowledgments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch acknowledgments: {str(e)}"
        )


@router.get("/admin/analytics")
async def get_acknowledgment_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get analytics about disclaimer acknowledgments (admin only).
    Returns patterns, drop-off rates, and risk statistics.
    """
    try:
        # Get stats by disclaimer type
        patterns = []
        for dtype in DisclaimerType:
            total = db.query(DisclaimerAcknowledgment).filter(
                DisclaimerAcknowledgment.disclaimer_type == dtype
            ).count()

            if total == 0:
                continue

            acknowledged = db.query(DisclaimerAcknowledgment).filter(
                and_(
                    DisclaimerAcknowledgment.disclaimer_type == dtype,
                    DisclaimerAcknowledgment.acknowledged == True
                )
            ).count()

            avg_time = db.query(
                func.avg(DisclaimerAcknowledgment.time_to_acknowledge)
            ).filter(
                and_(
                    DisclaimerAcknowledgment.disclaimer_type == dtype,
                    DisclaimerAcknowledgment.time_to_acknowledge.isnot(None)
                )
            ).scalar() or 0

            drop_off_rate = ((total - acknowledged) / total * 100) if total > 0 else 0

            # Determine risk level for pattern
            if drop_off_rate > 20:
                pattern_risk = "critical"
            elif drop_off_rate > 15:
                pattern_risk = "high"
            elif drop_off_rate > 10:
                pattern_risk = "medium"
            else:
                pattern_risk = "low"

            patterns.append({
                "disclaimer_type": dtype.value,
                "total_shown": total,
                "acknowledged": acknowledged,
                "average_time_to_acknowledge": round(avg_time, 1),
                "drop_off_rate": round(drop_off_rate, 1),
                "risk_level": pattern_risk
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "patterns": patterns
            }
        )

    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )


@router.get("/admin/high-risk-users")
async def get_high_risk_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get users with high-risk disclaimer behavior (admin only).
    Identifies users who repeatedly dismiss mandatory disclaimers.
    """
    try:
        high_risk = db.query(DisclaimerAcknowledgment).filter(
            DisclaimerAcknowledgment.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        ).order_by(
            desc(DisclaimerAcknowledgment.updated_at)
        ).limit(100).all()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "count": len(high_risk),
                "high_risk_acknowledgments": [ack.to_dict(include_pii=False) for ack in high_risk]
            }
        )

    except Exception as e:
        logger.error(f"Error fetching high-risk users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch high-risk users: {str(e)}"
        )
