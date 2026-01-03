"""
GDPR/CCPA Compliance API Endpoints

Provides endpoints for data subject rights requests and consent management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from datetime import datetime

from ..src.core.database import get_db
from ..src.core.compliance.gdpr_ccpa import (
    ConsentType,
    DataSubjectRightType,
    RequestStatus,
    ConsentManager,
    DataSubjectRightsManager,
    DataRetentionManager,
)

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])

# =============================================================================
# REQUEST MODELS
# =============================================================================

class ConsentRequest(BaseModel):
    """Request to record user consent"""
    consent_type: ConsentType
    consent_given: bool
    purpose: Optional[str] = None


class DataSubjectRightRequest(BaseModel):
    """Request for data subject rights"""
    request_type: DataSubjectRightType
    additional_info: Optional[Dict] = None


class ConsentWithdrawalRequest(BaseModel):
    """Request to withdraw consent"""
    consent_type: ConsentType


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class ConsentResponse(BaseModel):
    """Response for consent operations"""
    success: bool
    consent_type: str
    consent_given: bool
    consent_date: datetime
    message: str


class DataRequestResponse(BaseModel):
    """Response for data subject rights requests"""
    success: bool
    request_id: int
    request_type: str
    status: str
    deadline: datetime
    message: str


# =============================================================================
# COMPLIANCE STATUS ENDPOINT
# =============================================================================

@router.get("/status")
async def get_compliance_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get current compliance status for the user
    Returns information about terms acceptance, privacy policy, etc.
    """
    try:
        # For now, return a simple status indicating compliance is not required
        # This can be expanded later to track actual user compliance
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "hasAcceptedTerms": True,
                    "hasAcceptedPrivacy": True,
                    "hasCompletedOnboarding": True,
                    "requiredActions": []
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve compliance status"
            }
        )


# =============================================================================
# CONSENT MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    request: Request,
    consent_req: ConsentRequest,
    db: Session = Depends(get_db),
):
    """
    Record user consent for data processing.

    Required for GDPR Article 6 compliance.

    Args:
        consent_req: Consent request details
        db: Database session

    Returns:
        ConsentResponse with confirmation
    """
    # Get user from request (assumes authentication middleware)
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = request.state.user['id']

    # Get IP and user agent for audit trail
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get('user-agent')

    # Record consent
    consent = ConsentManager.record_consent(
        db=db,
        user_id=user_id,
        consent_type=consent_req.consent_type,
        consent_given=consent_req.consent_given,
        purpose=consent_req.purpose or f"User consent for {consent_req.consent_type.value}",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return ConsentResponse(
        success=True,
        consent_type=consent.consent_type,
        consent_given=consent.consent_given,
        consent_date=consent.consent_date,
        message=f"Consent {'given' if consent.consent_given else 'withdrawn'} successfully"
    )


@router.get("/consent")
async def get_user_consents(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get all current consents for authenticated user.

    Returns:
        Dictionary of consent types and their status
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = request.state.user['id']

    consents = ConsentManager.get_user_consents(db=db, user_id=user_id)

    return {
        "success": True,
        "consents": consents,
        "message": "Consents retrieved successfully"
    }


@router.post("/consent/withdraw")
async def withdraw_consent(
    request: Request,
    withdrawal: ConsentWithdrawalRequest,
    db: Session = Depends(get_db),
):
    """
    Withdraw consent for data processing.

    GDPR Article 7(3): Right to withdraw consent at any time.

    Args:
        withdrawal: Consent withdrawal request
        db: Database session

    Returns:
        Confirmation of withdrawal
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = request.state.user['id']

    success = ConsentManager.withdraw_consent(
        db=db,
        user_id=user_id,
        consent_type=withdrawal.consent_type,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active consent found for {withdrawal.consent_type.value}"
        )

    return {
        "success": True,
        "consent_type": withdrawal.consent_type.value,
        "message": "Consent withdrawn successfully"
    }


# =============================================================================
# DATA SUBJECT RIGHTS ENDPOINTS
# =============================================================================

@router.post("/data-request", response_model=DataRequestResponse)
async def create_data_request(
    request: Request,
    data_req: DataSubjectRightRequest,
    db: Session = Depends(get_db),
):
    """
    Create a data subject rights request.

    Supports:
    - Right to access (GDPR Art. 15)
    - Right to erasure (GDPR Art. 17, "right to be forgotten")
    - Right to data portability (GDPR Art. 20)
    - Right to rectification (GDPR Art. 16)
    - Right to restrict processing (GDPR Art. 18)
    - Right to object (GDPR Art. 21)

    Args:
        data_req: Data subject rights request
        db: Database session

    Returns:
        DataRequestResponse with request details
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = request.state.user['id']
    ip_address = request.client.host if request.client else None

    # Create request
    dsr = DataSubjectRightsManager.create_request(
        db=db,
        user_id=user_id,
        request_type=data_req.request_type,
        request_data=data_req.additional_info,
        ip_address=ip_address,
    )

    # Get appropriate message
    messages = {
        DataSubjectRightType.ACCESS: "Data access request created. We will provide your data within 30 days.",
        DataSubjectRightType.ERASURE: "Data erasure request created. We will process your request within 30 days.",
        DataSubjectRightType.PORTABILITY: "Data portability request created. We will provide your data in a machine-readable format within 30 days.",
        DataSubjectRightType.RECTIFICATION: "Rectification request created. We will correct your data within 30 days.",
        DataSubjectRightType.RESTRICT: "Processing restriction request created. We will restrict processing within 30 days.",
        DataSubjectRightType.OBJECT: "Objection request created. We will stop processing your data within 30 days.",
        DataSubjectRightType.OPT_OUT: "Opt-out request created. We will stop sharing your data within 30 days.",
    }

    return DataRequestResponse(
        success=True,
        request_id=dsr.id,
        request_type=dsr.request_type,
        status=dsr.status,
        deadline=dsr.deadline,
        message=messages.get(data_req.request_type, "Request created successfully")
    )


@router.get("/data-request/{request_id}")
async def get_data_request_status(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db),
):
    """
    Get status of a data subject rights request.

    Args:
        request_id: Request ID
        db: Database session

    Returns:
        Request status and details
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = request.state.user['id']

    from ..src.core.compliance.gdpr_ccpa import DataSubjectRequest
    dsr = db.query(DataSubjectRequest).filter(
        DataSubjectRequest.id == request_id,
        DataSubjectRequest.user_id == user_id,
    ).first()

    if not dsr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    return {
        "success": True,
        "request": {
            "id": dsr.id,
            "type": dsr.request_type,
            "status": dsr.status,
            "requested_at": dsr.requested_at.isoformat(),
            "deadline": dsr.deadline.isoformat(),
            "processed_at": dsr.processed_at.isoformat() if dsr.processed_at else None,
            "completed_at": dsr.completed_at.isoformat() if dsr.completed_at else None,
            "denial_reason": dsr.denial_reason,
        }
    }


@router.get("/data-request")
async def list_user_data_requests(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    List all data subject rights requests for authenticated user.

    Returns:
        List of user's data requests
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = request.state.user['id']

    from ..src.core.compliance.gdpr_ccpa import DataSubjectRequest
    requests = db.query(DataSubjectRequest).filter(
        DataSubjectRequest.user_id == user_id
    ).order_by(DataSubjectRequest.requested_at.desc()).all()

    return {
        "success": True,
        "requests": [
            {
                "id": req.id,
                "type": req.request_type,
                "status": req.status,
                "requested_at": req.requested_at.isoformat(),
                "deadline": req.deadline.isoformat(),
                "completed_at": req.completed_at.isoformat() if req.completed_at else None,
            }
            for req in requests
        ]
    }


@router.get("/data-export")
async def export_user_data(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Export all user data (GDPR Article 20: Right to data portability).

    This is a direct export endpoint that provides data immediately
    without creating a formal request.

    Returns:
        JSON with all user data
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = request.state.user['id']

    # Create a temporary access request
    dsr = DataSubjectRightsManager.create_request(
        db=db,
        user_id=user_id,
        request_type=DataSubjectRightType.ACCESS,
        ip_address=request.client.host if request.client else None,
    )

    # Process immediately
    try:
        user_data = DataSubjectRightsManager.process_access_request(
            db=db,
            request_id=dsr.id,
            processor_id=user_id,  # Self-service export
        )

        return {
            "success": True,
            "export_date": datetime.utcnow().isoformat(),
            "data": user_data,
            "format": "JSON",
            "message": "Data exported successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting data: {str(e)}"
        )


# =============================================================================
# ADMIN ENDPOINTS (for processing requests)
# =============================================================================

@router.post("/admin/process-request/{request_id}")
async def process_data_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db),
):
    """
    Process a data subject rights request (admin only).

    Args:
        request_id: Request ID
        db: Database session

    Returns:
        Processing result
    """
    # Check if user is admin
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if not request.state.user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    processor_id = request.state.user['id']

    from ..src.core.compliance.gdpr_ccpa import DataSubjectRequest
    dsr = db.query(DataSubjectRequest).filter(
        DataSubjectRequest.id == request_id
    ).first()

    if not dsr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    try:
        if dsr.request_type == DataSubjectRightType.ACCESS.value:
            user_data = DataSubjectRightsManager.process_access_request(
                db=db,
                request_id=request_id,
                processor_id=processor_id,
            )
            return {
                "success": True,
                "message": "Access request processed",
                "data": user_data
            }

        elif dsr.request_type == DataSubjectRightType.ERASURE.value:
            DataSubjectRightsManager.process_erasure_request(
                db=db,
                request_id=request_id,
                processor_id=processor_id,
            )
            return {
                "success": True,
                "message": "Erasure request processed"
            }

        else:
            return {
                "success": False,
                "message": f"Request type {dsr.request_type} not yet implemented"
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


# =============================================================================
# INFORMATION ENDPOINTS
# =============================================================================

@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    Get privacy policy information.

    Returns:
        Privacy policy details and data processing information
    """
    return {
        "success": True,
        "policy": {
            "last_updated": "2024-01-15",
            "version": "1.0",
            "data_controller": {
                "name": "Legal AI System",
                "email": "privacy@legal-ai.example.com",
                "address": "123 Legal Street, City, Country",
            },
            "data_protection_officer": {
                "email": "dpo@legal-ai.example.com",
            },
            "data_collected": [
                "Personal information (name, email, phone)",
                "Account information (username, password hash)",
                "Document data (uploaded files, analysis results)",
                "Usage data (activity logs, interactions)",
                "Technical data (IP address, browser, device)",
            ],
            "legal_basis": [
                "Consent (GDPR Article 6(1)(a))",
                "Contract performance (GDPR Article 6(1)(b))",
                "Legal obligation (GDPR Article 6(1)(c))",
                "Legitimate interests (GDPR Article 6(1)(f))",
            ],
            "retention_periods": {
                "account_data": "Until account deletion",
                "documents": "90 days after upload",
                "audit_logs": "1 year",
                "analytics": "2 years",
            },
            "user_rights": [
                "Right to access your data (GDPR Art. 15)",
                "Right to rectification (GDPR Art. 16)",
                "Right to erasure (GDPR Art. 17)",
                "Right to restrict processing (GDPR Art. 18)",
                "Right to data portability (GDPR Art. 20)",
                "Right to object (GDPR Art. 21)",
                "Right to withdraw consent (GDPR Art. 7(3))",
            ],
        }
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['router']
