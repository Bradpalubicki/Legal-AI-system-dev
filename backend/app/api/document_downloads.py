"""
Document Downloads API Endpoints

Endpoints for managing document downloads, including:
- Download history
- Budget status
- Manual download triggers
- Auto-download settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
import logging

from ..src.core.database import get_db
from ..api.deps import get_current_user, CurrentUser
from ..services.document_download_service import DocumentDownloadService
from shared.database.models import (
    DocumentDownload,
    DocumentDownloadStatus,
    UserDocketMonitor
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/downloads", tags=["Document Downloads"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DownloadResponse(BaseModel):
    """Response for a single download"""
    id: int
    document_id: int
    docket_id: int
    description: Optional[str]
    document_number: Optional[int]
    source: str
    status: str
    page_count: Optional[int]
    cost: float
    file_name: Optional[str]
    file_size: Optional[int]
    created_at: str
    downloaded_at: Optional[str]
    error_message: Optional[str]


class BudgetStatusResponse(BaseModel):
    """Response for budget status"""
    budget: float
    spent: float
    remaining: float
    auto_download_enabled: bool
    auto_download_free_only: bool
    budget_reset_date: Optional[str]


class UpdateAutoDownloadRequest(BaseModel):
    """Request to update auto-download settings"""
    auto_download_enabled: Optional[bool] = None
    auto_download_free_only: Optional[bool] = None
    pacer_download_budget: Optional[float] = Field(None, ge=0, le=1000)


class ManualDownloadRequest(BaseModel):
    """Request to manually trigger a download"""
    docket_id: int
    document_id: int
    use_pacer: bool = False  # If true, use PACER even if free copy exists


# ============================================================================
# Helper Functions
# ============================================================================

def get_download_service(db: Session = Depends(get_db)) -> DocumentDownloadService:
    """Get document download service instance"""
    return DocumentDownloadService(db)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/history", response_model=List[DownloadResponse])
async def get_download_history(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentDownloadService = Depends(get_download_service)
):
    """
    Get user's document download history.

    Returns a list of downloads sorted by most recent first.
    """
    try:
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = DocumentDownloadStatus(status_filter)
            except ValueError:
                pass

        downloads = service.get_user_downloads(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset,
            status=status_enum
        )

        return [
            DownloadResponse(
                id=d.id,
                document_id=d.document_id,
                docket_id=d.docket_id,
                description=d.description,
                document_number=d.document_number,
                source=d.source.value if d.source else "unknown",
                status=d.status.value if d.status else "unknown",
                page_count=d.page_count,
                cost=float(d.cost) if d.cost else 0.0,
                file_name=d.file_name,
                file_size=d.file_size,
                created_at=d.created_at.isoformat() if d.created_at else "",
                downloaded_at=d.downloaded_at.isoformat() if d.downloaded_at else None,
                error_message=d.error_message
            )
            for d in downloads
        ]

    except Exception as e:
        logger.error(f"Error getting download history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download history: {str(e)}"
        )


@router.get("/budget/{docket_id}", response_model=BudgetStatusResponse)
async def get_budget_status(
    docket_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentDownloadService = Depends(get_download_service)
):
    """
    Get PACER budget status for a specific monitored case.

    Shows current budget, amount spent, and remaining balance.
    """
    try:
        budget_info = service.get_user_budget_status(
            user_id=current_user.user_id,
            docket_id=docket_id
        )

        return BudgetStatusResponse(**budget_info)

    except Exception as e:
        logger.error(f"Error getting budget status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget status: {str(e)}"
        )


@router.get("/{download_id}", response_model=DownloadResponse)
async def get_download(
    download_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific download by ID.
    """
    download = db.query(DocumentDownload).filter(
        DocumentDownload.id == download_id,
        DocumentDownload.user_id == current_user.user_id
    ).first()

    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found"
        )

    return DownloadResponse(
        id=download.id,
        document_id=download.document_id,
        docket_id=download.docket_id,
        description=download.description,
        document_number=download.document_number,
        source=download.source.value if download.source else "unknown",
        status=download.status.value if download.status else "unknown",
        page_count=download.page_count,
        cost=float(download.cost) if download.cost else 0.0,
        file_name=download.file_name,
        file_size=download.file_size,
        created_at=download.created_at.isoformat() if download.created_at else "",
        downloaded_at=download.downloaded_at.isoformat() if download.downloaded_at else None,
        error_message=download.error_message
    )


@router.post("/manual")
async def manual_download(
    request: ManualDownloadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentDownloadService = Depends(get_download_service)
):
    """
    Manually trigger a document download.

    By default, downloads from free sources if available.
    Set use_pacer=true to force PACER download (costs tokens).
    """
    try:
        # Check availability
        availability = await service.check_document_availability(request.document_id)

        if not availability.get("available"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not available for download"
            )

        is_free = availability.get("free", False)

        if is_free and not request.use_pacer:
            # Download from free source
            download = await service.download_free_document(
                user_id=current_user.user_id,
                docket_id=request.docket_id,
                document_id=request.document_id
            )
        else:
            # Download from PACER
            try:
                download = await service.download_pacer_document(
                    user_id=current_user.user_id,
                    docket_id=request.docket_id,
                    document_id=request.document_id
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        return {
            "success": download.status == DocumentDownloadStatus.COMPLETED,
            "download_id": download.id,
            "status": download.status.value if download.status else "unknown",
            "source": download.source.value if download.source else "unknown",
            "cost": float(download.cost) if download.cost else 0.0,
            "error": download.error_message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


@router.put("/monitor/{docket_id}/auto-download")
async def update_auto_download_settings(
    docket_id: int,
    request: UpdateAutoDownloadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update auto-download settings for a monitored case.

    Allows enabling/disabling auto-download and setting PACER budget.
    """
    try:
        # Find the user's monitor for this docket
        monitor = db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == current_user.user_id,
            UserDocketMonitor.courtlistener_docket_id == docket_id,
            UserDocketMonitor.is_active == True
        ).first()

        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not monitoring this case"
            )

        # Update settings
        if request.auto_download_enabled is not None:
            monitor.auto_download_enabled = request.auto_download_enabled

        if request.auto_download_free_only is not None:
            monitor.auto_download_free_only = request.auto_download_free_only

        if request.pacer_download_budget is not None:
            monitor.pacer_download_budget = Decimal(str(request.pacer_download_budget))

        db.commit()

        return {
            "success": True,
            "docket_id": docket_id,
            "auto_download_enabled": monitor.auto_download_enabled,
            "auto_download_free_only": monitor.auto_download_free_only,
            "pacer_download_budget": float(monitor.pacer_download_budget),
            "pacer_spent_this_month": float(monitor.pacer_spent_this_month)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating auto-download settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.get("/check-availability/{document_id}")
async def check_document_availability(
    document_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentDownloadService = Depends(get_download_service)
):
    """
    Check if a document is available for download and its cost.

    Returns availability info including whether it's free or requires PACER.
    """
    try:
        availability = await service.check_document_availability(document_id)

        return {
            "document_id": document_id,
            **availability
        }

    except Exception as e:
        logger.error(f"Error checking document availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check availability: {str(e)}"
        )
