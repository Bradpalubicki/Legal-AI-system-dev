"""
CourtListener API Endpoints

Free federal court records access integrated into the unified PACER interface.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import logging

from ..src.core.database import get_db
from ..src.services.courtlistener_service import CourtListenerService, CourtListenerServiceError
from ..api.deps.auth import get_current_user, get_optional_user, CurrentUser
from ..api.deps.feature_gates import require_feature
from ..core.feature_access import Feature
from ..models.user import User
from ..models.case_notification_history import CaseNotification
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/courtlistener", tags=["CourtListener"])

# Global service instance for case monitoring
_courtlistener_service: Optional[CourtListenerService] = None


def get_courtlistener_service(db: Session = Depends(get_db)) -> CourtListenerService:
    """Get or create CourtListener service instance"""
    global _courtlistener_service
    if _courtlistener_service is None:
        # API key can be set in environment variable COURTLISTENER_API_KEY
        import os
        api_key = os.getenv("COURTLISTENER_API_KEY")
        _courtlistener_service = CourtListenerService(db, api_key=api_key)
    return _courtlistener_service


# ============================================================================
# Request/Response Models
# ============================================================================

class DocketSearchRequest(BaseModel):
    """Request model for docket search"""
    query: Optional[str] = Field(None, description="General search query")
    court_id: Optional[str] = Field(None, description="Court identifier (e.g., 'ca9', 'nysd')")
    court_type: Optional[str] = Field(None, description="Court type filter ('bankruptcy', 'district', 'circuit')")
    case_number: Optional[str] = Field(None, description="Case number")
    party_name: Optional[str] = Field(None, description="Party name")
    filed_after: Optional[str] = Field(None, description="Filed after date (YYYY-MM-DD)")
    filed_before: Optional[str] = Field(None, description="Filed before date (YYYY-MM-DD)")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Results per page")


class OpinionSearchRequest(BaseModel):
    """Request model for opinion search"""
    query: str = Field(..., min_length=2, description="Search query")
    court_id: Optional[str] = Field(None, description="Court identifier")
    filed_after: Optional[str] = Field(None, description="Filed after date")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class MonitorCaseRequest(BaseModel):
    """Request model to start monitoring a case"""
    docket_id: int = Field(..., description="CourtListener docket ID to monitor")
    # Optional: case metadata from PACER (bypasses CourtListener API fetch)
    case_name: Optional[str] = Field(None, description="Case name")
    docket_number: Optional[str] = Field(None, description="Docket number")
    court: Optional[str] = Field(None, description="Court name")
    court_id: Optional[str] = Field(None, description="Court ID")
    date_filed: Optional[str] = Field(None, description="Date filed")


# ============================================================================
# Search Endpoints
# ============================================================================

@router.post("/search/dockets")
async def search_dockets(
    search_request: DocketSearchRequest,
    service: CourtListenerService = Depends(get_courtlistener_service)
):
    """
    Search for federal court dockets.

    FREE alternative to PACER - no account required.
    Returns dockets with case information.
    """
    try:
        logger.info(f"[ENDPOINT] CourtListener docket search called")
        logger.info(f"[ENDPOINT] Request data: {search_request.dict(exclude_none=True)}")
        results = await service.search_dockets(
            **search_request.dict(exclude_none=True)
        )

        return results

    except CourtListenerServiceError as e:
        logger.error(f"CourtListener service error: {e}")
        error_message = str(e)

        # Provide helpful message for timeout errors
        if "timed out" in error_message.lower():
            error_message = (
                "CourtListener API is currently unavailable or very slow. "
                "This is a temporary service issue. Please try again in a few minutes. "
                "Alternative: You can use PACER integration for federal case access."
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,  # Changed from 400 to 503
            detail=error_message
        )
    except Exception as e:
        logger.error(f"Docket search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/search/opinions")
async def search_opinions(
    search_request: OpinionSearchRequest,
    service: CourtListenerService = Depends(get_courtlistener_service)
):
    """
    Search for court opinions and case law.

    FREE case law database.
    """
    try:
        results = await service.search_opinions(
            **search_request.dict(exclude_none=True)
        )

        return results

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/docket/{docket_id}")
async def get_docket_details(
    docket_id: int,
    service: CourtListenerService = Depends(get_courtlistener_service)
):
    """
    Get detailed information about a specific docket.

    Includes docket entries and associated documents.
    """
    try:
        result = await service.get_docket_details(docket_id)
        return result

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# Case Monitoring Endpoints (Auto-Update Functionality)
# ============================================================================

@router.post("/monitor/start")
async def start_monitoring_case(
    request: MonitorCaseRequest,
    service: CourtListenerService = Depends(get_courtlistener_service),
    user: User = Depends(require_feature(Feature.CASE_MONITORING))  # Feature gate: requires paid tier
):
    """
    Start monitoring a case for new documents.

    Once monitoring starts, the UI will auto-update when new files are added.
    Requires authentication AND case monitoring feature (paid tier).

    Optional case metadata can be provided to bypass CourtListener API fetch.

    Feature Gate: Requires CASE_MONITORING feature
    - FREE tier: Blocked (returns 402 Payment Required)
    - CASE_MONITOR tier ($5/case or $19/month): Allowed
    - PRO/FIRM tiers: Allowed
    """
    try:
        logger.info(f"User {user.id} starting to monitor docket {request.docket_id}")

        # Prepare case metadata if provided (allows monitoring without CourtListener API)
        case_metadata = None
        if request.case_name or request.docket_number:
            case_metadata = {
                "case_name": request.case_name,
                "docket_number": request.docket_number,
                "court": request.court,
                "court_id": request.court_id,
                "date_filed": request.date_filed
            }
            logger.info(f"Using provided case metadata (bypassing CourtListener API fetch)")

        await service.monitor_case(
            request.docket_id,
            user.id,
            case_metadata=case_metadata
        )

        return {
            "success": True,
            "message": f"Started monitoring docket {request.docket_id}",
            "docket_id": request.docket_id
        }

    except Exception as e:
        logger.error(f"Error starting case monitoring for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/monitor/stop/{docket_id}")
async def stop_monitoring_case(
    docket_id: int,
    service: CourtListenerService = Depends(get_courtlistener_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Stop monitoring a case for the current user.
    Requires authentication - users can only stop monitoring their own cases.
    """
    try:
        logger.info(f"User {current_user.user_id} stopping monitoring for docket {docket_id}")
        stopped = service.stop_monitoring(docket_id, current_user.user_id)

        if not stopped:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Docket {docket_id} is not being monitored by you"
            )

        return {
            "success": True,
            "message": f"Stopped monitoring docket {docket_id}",
            "docket_id": docket_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping case monitoring for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.get("/monitor/list")
async def list_monitored_cases(
    service: CourtListenerService = Depends(get_courtlistener_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of currently monitored cases for the authenticated user.

    Each user only sees their own monitored cases.
    Requires authentication.

    Monitored cases are stored in the database (TrackedDocket + UserDocketMonitor tables)
    for persistence across server restarts.
    """
    try:
        print(f"\n{'='*80}")
        print(f"MONITOR/LIST ENDPOINT CALLED - User ID: {current_user.user_id}")
        print(f"{'='*80}\n")
        logger.info(f"=== ENDPOINT: list_monitored_cases called by user: {current_user.user_id} ===")

        # Get monitored cases for this specific user
        monitored = await service.get_monitored_cases_list(current_user.user_id)
        print(f"\nReturning {len(monitored)} monitored cases for user {current_user.user_id}")
        if monitored:
            print(f"First case: {monitored[0]}")
        print(f"{'='*80}\n")

        logger.info(f"=== ENDPOINT: User {current_user.user_id} - Received {len(monitored)} cases from service ===")
        if monitored:
            logger.info(f"=== ENDPOINT: First case sample: {monitored[0]} ===")

        return {
            "success": True,
            "monitored_cases": monitored,
            "count": len(monitored)
        }

    except Exception as e:
        logger.error(f"Error listing monitored cases for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitored cases: {str(e)}"
        )


@router.get("/monitor/updates")
async def check_for_updates(
    service: CourtListenerService = Depends(get_courtlistener_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Check all monitored cases for new documents for the current user.

    Frontend polls this endpoint to auto-update the UI.
    Returns list of cases with new documents.
    Requires authentication - users only see updates for their own monitored cases.
    """
    try:
        logger.info(f"Checking for updates for user {current_user.user_id}")
        updates = await service.get_monitored_cases_updates(current_user.user_id)

        return {
            "success": True,
            "updates": updates,
            "count": len(updates),
            "has_updates": len(updates) > 0
        }

    except Exception as e:
        logger.error(f"Error checking for updates for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check updates: {str(e)}"
        )


@router.get("/monitor/updates/{docket_id}")
async def check_case_updates(
    docket_id: int,
    service: CourtListenerService = Depends(get_courtlistener_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Check a specific case for new documents for the current user.
    Requires authentication - users can only check updates for cases they are monitoring.
    """
    try:
        logger.info(f"User {current_user.user_id} checking updates for docket {docket_id}")
        result = await service.check_for_updates(docket_id, current_user.user_id)

        return {
            "success": True,
            "docket_id": docket_id,
            **result
        }

    except Exception as e:
        logger.error(f"Error checking updates for docket {docket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check updates: {str(e)}"
        )


# ============================================================================
# New Filings Since Last Login Endpoint
# ============================================================================

@router.get("/monitor/new-since-login")
async def get_new_filings_since_login(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get new filings in monitored cases since the user's last login.

    Used to show a notification popup when user logs in.
    Returns summary of new filings grouped by case.
    """
    try:
        # Get user's last login time
        user = db.query(User).filter(User.id == current_user.user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get PREVIOUS login time (not current login) for accurate comparison
        # This is set by authenticate_user before updating last_login_at
        print(f'[NEW-SINCE-LOGIN] previous_login_at={user.previous_login_at}, last_login_at={user.last_login_at}', flush=True)
        last_login = user.previous_login_at or user.last_login_at
        print(f'[NEW-SINCE-LOGIN] Using last_login={last_login}', flush=True)
        logger.info(f'[NEW-SINCE-LOGIN] User {current_user.user_id}: previous_login_at={user.previous_login_at}, last_login_at={user.last_login_at}')
        logger.info(f'[NEW-SINCE-LOGIN] Using last_login={last_login}')
        if not last_login:
            last_login = datetime.utcnow() - timedelta(hours=24)

        # Query notifications for this user since last login
        # CaseNotification stores user_id in extra_data JSON
        notifications = db.query(CaseNotification).filter(
            CaseNotification.sent_at > last_login,
            CaseNotification.notification_type == "new_documents"
        ).order_by(CaseNotification.sent_at.desc()).all()

        logger.info(f'[NEW-SINCE-LOGIN] Found {len(notifications)} total notifications after {last_login}')
        
        # Filter to only this user's notifications (stored in extra_data)
        user_notifications = []
        for notification in notifications:
            extra = notification.extra_data or {}
            logger.info(f'[NEW-SINCE-LOGIN] Notification {notification.id}: user_id={extra.get("user_id")}, comparing to {current_user.user_id}')
            if str(extra.get("user_id")) == str(current_user.user_id):
                user_notifications.append(notification)
                logger.info(f'[NEW-SINCE-LOGIN] MATCHED!')

        # Group by case
        cases_with_new_filings = {}
        total_new_documents = 0

        for notification in user_notifications:
            docket_id = notification.docket_id
            if docket_id not in cases_with_new_filings:
                cases_with_new_filings[docket_id] = {
                    "docket_id": docket_id,
                    "case_name": notification.case_name,
                    "court": notification.court,
                    "new_documents": [],
                    "document_count": 0,
                    "latest_notification": notification.sent_at.isoformat() if notification.sent_at else None,
                    "_seen_entries": set()  # Track seen entry numbers for deduplication
                }

            # Add documents from this notification (deduplicated by entry_number)
            if notification.documents:
                for doc in notification.documents:
                    entry_num = doc.get('entry_number') or doc.get('entry_num')
                    if entry_num and entry_num not in cases_with_new_filings[docket_id]["_seen_entries"]:
                        cases_with_new_filings[docket_id]["_seen_entries"].add(entry_num)
                        cases_with_new_filings[docket_id]["new_documents"].append(doc)
                    elif not entry_num:
                        cases_with_new_filings[docket_id]["new_documents"].append(doc)

        # Clean up internal tracking and update counts
        for case_data in cases_with_new_filings.values():
            del case_data["_seen_entries"]
            case_data["document_count"] = len(case_data["new_documents"])
            total_new_documents += case_data["document_count"]

        # Convert to list
        cases_list = list(cases_with_new_filings.values())

        return {
            "success": True,
            "has_new_filings": len(cases_list) > 0,
            "total_new_documents": total_new_documents,
            "cases_count": len(cases_list),
            "cases": cases_list,
            "since": last_login.isoformat() if last_login else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting new filings since login for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get new filings: {str(e)}"
        )


# ============================================================================
# Status Endpoint
# ============================================================================

@router.get("/status")
async def get_status(
    service: CourtListenerService = Depends(get_courtlistener_service)
):
    """
    Get CourtListener service status.
    Public endpoint - does not require authentication.
    """
    try:
        return {
            "success": True,
            "service": "CourtListener",
            "status": "active",
            "authenticated": service.api_key is not None,
            "rate_limit": "5000/hour" if service.api_key else "100/hour",
            "base_url": service.base_url
        }

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "success": False,
            "service": "CourtListener",
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# RECAP Fetch API - Purchase Documents from PACER
# ============================================================================

class PurchaseDocumentRequest(BaseModel):
    """Request model for purchasing documents from PACER"""
    pacer_case_id: Optional[str] = Field(None, description="PACER case ID")
    pacer_doc_id: Optional[str] = Field(None, description="PACER document ID")
    docket_number: Optional[str] = Field(None, description="Docket number")
    court: Optional[str] = Field(None, description="Court identifier (e.g., 'cand')")
    document_number: Optional[int] = Field(None, description="Document number on docket")
    attachment_number: Optional[int] = Field(None, description="Attachment number")
    request_type: int = Field(2, description="1=docket, 2=PDF, 3=attachment_page")
    pacer_username: str = Field(..., description="PACER account username")
    pacer_password: str = Field(..., description="PACER account password")


@router.post("/purchase-document")
async def purchase_document(
    request: PurchaseDocumentRequest,
    service: CourtListenerService = Depends(get_courtlistener_service),
    user: User = Depends(require_feature(Feature.DOCUMENT_DOWNLOAD))
):
    """
    Purchase a document from PACER using CourtListener's RECAP Fetch API.

    This endpoint:
    1. Submits a purchase request to CourtListener
    2. CourtListener uses your PACER credentials to buy the document
    3. Returns a request_id for checking status

    The process is asynchronous - use /fetch-status/{request_id} to check when complete.

    Feature Gate: Requires DOCUMENT_DOWNLOAD feature
    - FREE tier: Blocked (returns 402 Payment Required)
    - CASE_MONITOR tier and above: Allowed
    """
    try:
        result = await service.purchase_pacer_document(
            pacer_case_id=request.pacer_case_id,
            pacer_doc_id=request.pacer_doc_id,
            docket_number=request.docket_number,
            court=request.court,
            document_number=request.document_number,
            attachment_number=request.attachment_number,
            request_type=request.request_type,
            pacer_username=request.pacer_username,
            pacer_password=request.pacer_password
        )

        return result

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error purchasing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Purchase failed: {str(e)}"
        )


@router.get("/fetch-status/{request_id}")
async def check_fetch_status(
    request_id: int,
    service: CourtListenerService = Depends(get_courtlistener_service)
):
    """
    Check the status of a RECAP Fetch purchase request.

    Returns:
    - Status: queued (4), processing (1), success (2), or failed (3)
    - Document URL if completed successfully
    - Cost and document metadata
    """
    try:
        result = await service.check_fetch_status(request_id)
        return result

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error checking fetch status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )


class DownloadPurchasedDocumentRequest(BaseModel):
    """Request model for downloading a purchased document"""
    filepath_local: str = Field(..., description="The filepath_local from fetch status")
    filename: Optional[str] = Field(None, description="Custom filename (optional)")


@router.post("/download-purchased")
async def download_purchased_document(
    request: DownloadPurchasedDocumentRequest,
    service: CourtListenerService = Depends(get_courtlistener_service),
    user: User = Depends(require_feature(Feature.DOCUMENT_DOWNLOAD))
):
    """
    Download a purchased document to the app's storage.

    After a purchase request completes (status=2), use the filepath_local
    to download the actual PDF file to the app for analysis.

    Feature Gate: Requires DOCUMENT_DOWNLOAD feature
    - FREE tier: Blocked (returns 402 Payment Required)
    - CASE_MONITOR tier and above: Allowed
    """
    try:
        import os
        import uuid

        # Generate save path
        filename = request.filename or f"pacer_doc_{uuid.uuid4().hex[:8]}.pdf"
        save_dir = os.path.join(os.getcwd(), "storage", "pacer_documents")
        save_path = os.path.join(save_dir, filename)

        result = await service.download_purchased_document(
            filepath_local=request.filepath_local,
            save_path=save_path
        )

        return result

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error downloading purchased document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


# ============================================================================
# RECAP Document Endpoints (FREE Document Access)
# ============================================================================

@router.get("/docket/{docket_id}/documents")
async def get_docket_documents(
    docket_id: int,
    service: CourtListenerService = Depends(get_courtlistener_service)
):
    """
    Get all RECAP documents for a docket.

    This endpoint fetches the docket AND all associated documents from RECAP,
    showing which documents are available for FREE download.

    FREE documents can be downloaded without PACER costs!
    """
    try:
        result = await service.get_docket_with_documents(docket_id)
        return result

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting docket documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.get("/recap/document/{document_id}")
async def get_recap_document(
    document_id: int,
    service: CourtListenerService = Depends(get_courtlistener_service)
):
    """
    Get RECAP document download information.

    Returns download URL for FREE documents, or cost estimate for unavailable ones.
    """
    try:
        result = await service.download_recap_document(document_id)
        return result

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting RECAP document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


class DownloadRecapToAppRequest(BaseModel):
    """Request model for downloading FREE RECAP documents to app storage"""
    document_id: int = Field(..., description="RECAP document ID from CourtListener")
    filename: Optional[str] = Field(None, description="Custom filename (optional)")


@router.post("/download-recap-to-app")
async def download_recap_to_app(
    request: DownloadRecapToAppRequest,
    service: CourtListenerService = Depends(get_courtlistener_service),
    user: User = Depends(require_feature(Feature.DOCUMENT_DOWNLOAD))
):
    """
    Download a FREE RECAP document directly to app storage for analysis.

    This is the BRIDGE endpoint that connects CourtListener to your app:
    - Fetches the document from CourtListener's RECAP archive
    - Downloads the PDF directly to app storage (not browser downloads)
    - Makes it immediately available for AI analysis
    - Returns file path and metadata

    Use this instead of external CourtListener links to keep documents in the app!

    Feature Gate: Requires DOCUMENT_DOWNLOAD feature
    - FREE tier: Blocked (returns 402 Payment Required)
    - CASE_MONITOR tier ($5/case or $19/month): Allowed
    - PRO/FIRM tiers: Allowed

    This ensures only paying users can download documents to the app for analysis.
    """
    # Endpoint for direct document download to app storage
    try:
        import os
        import uuid

        logger.info(f"[DOWNLOAD-RECAP] Received request: document_id={request.document_id}, filename={request.filename}")

        # Generate save path in RECAP documents folder
        filename = request.filename or f"recap_doc_{request.document_id}_{uuid.uuid4().hex[:8]}.pdf"
        save_dir = os.path.join(os.getcwd(), "storage", "recap_documents")
        save_path = os.path.join(save_dir, filename)

        logger.info(f"Download-to-app request for RECAP document {request.document_id}")

        result = await service.download_recap_to_storage(
            document_id=request.document_id,
            save_path=save_path
        )

        return result

    except CourtListenerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error downloading RECAP document to app: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )
