"""
Document Download Service

Handles downloading documents from free sources (Internet Archive/RECAP)
and paid sources (PACER). Integrates with the credit system for PACER downloads.

Pricing Model:
- Document downloads: $0.25 per page (1 credit = 1 page)
- Our blended cost: ~$0.11 per page (56% gross margin)
- Free sources (RECAP/Internet Archive): 0 credits
"""

import os
import asyncio
import logging
import httpx
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from shared.database.models import (
    DocumentDownload,
    DocumentDownloadSource,
    DocumentDownloadStatus,
    UserDocketMonitor
)
from ..models.credits import UserCredits, CreditTransaction, TransactionType

logger = logging.getLogger(__name__)

# Pricing constants
DOCUMENT_PRICE_PER_PAGE = Decimal("0.25")  # Our price to customers
OUR_COST_PER_PAGE = Decimal("0.11")  # Our blended cost (PACER + CourtListener + AI + infra)
PACER_COST_PER_PAGE = Decimal("0.10")  # PACER's actual cost
GROSS_MARGIN = Decimal("0.56")  # 56% margin

# CourtListener API base URL
COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v3"

# RECAP Fetch polling configuration
RECAP_POLL_INTERVAL = 3  # seconds between status checks
RECAP_MAX_WAIT_TIME = 120  # maximum seconds to wait for document


class DocumentDownloadService:
    """
    Service for downloading court documents from various sources.

    Supports:
    - Free downloads from Internet Archive / RECAP (0 credits)
    - Paid downloads from PACER (1 credit per page = $0.25)

    Pricing:
    - 1 credit = 1 page = $0.25
    - Our cost: ~$0.11/page (56% gross margin)
    """

    def __init__(self, db: Session, api_key: Optional[str] = None):
        self.db = db
        self.api_key = api_key or os.getenv("COURTLISTENER_API_KEY")
        self.storage_path = os.getenv("DOCUMENT_STORAGE_PATH", "storage/downloads")
        self.price_per_page = DOCUMENT_PRICE_PER_PAGE
        self.cost_per_page = OUR_COST_PER_PAGE

        # PACER credentials from environment
        self.pacer_username = os.getenv("PACER_USERNAME")
        self.pacer_password = os.getenv("PACER_PASSWORD")

        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers for CourtListener requests"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Token {self.api_key}"
        return headers

    async def check_document_availability(self, document_id: int) -> Dict[str, Any]:
        """
        Check if a document is available for free download.

        Returns availability info including:
        - Whether it's free (RECAP/Internet Archive)
        - Page count
        - Credits needed (1 credit = 1 page)
        - Price ($0.25 per page for paid documents)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{COURTLISTENER_API_BASE}/recap-documents/{document_id}/",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code != 200:
                    return {
                        "available": False,
                        "free": False,
                        "error": f"Document not found: {response.status_code}"
                    }

                doc_data = response.json()

                # Check if free copy exists (RECAP or Internet Archive)
                is_free = bool(
                    doc_data.get("filepath_local") or
                    doc_data.get("ia_upload_failure_count") == 0
                )

                page_count = doc_data.get("page_count", 0) or 0

                # Calculate pricing
                if is_free:
                    credits_needed = 0
                    price_usd = Decimal("0")
                    our_cost = Decimal("0")
                else:
                    credits_needed = page_count  # 1 credit = 1 page
                    price_usd = Decimal(str(page_count)) * DOCUMENT_PRICE_PER_PAGE  # $0.25/page
                    our_cost = Decimal(str(page_count)) * OUR_COST_PER_PAGE  # $0.11/page

                return {
                    "available": True,
                    "free": is_free,
                    "source": "recap" if is_free else "pacer",
                    "page_count": page_count,
                    "credits_needed": credits_needed,
                    "price_per_page": float(DOCUMENT_PRICE_PER_PAGE),
                    "price_usd": float(price_usd),
                    "our_cost": float(our_cost),
                    # Legacy field for backwards compatibility
                    "estimated_cost": float(price_usd),
                    "filepath_local": doc_data.get("filepath_local"),
                    "description": doc_data.get("description", ""),
                    "document_number": doc_data.get("document_number"),
                    "pacer_doc_id": doc_data.get("pacer_doc_id"),
                    "court": doc_data.get("court")
                }

        except Exception as e:
            logger.error(f"Error checking document availability: {e}")
            return {
                "available": False,
                "free": False,
                "error": str(e)
            }

    async def download_free_document(
        self,
        user_id: int,
        docket_id: int,
        document_id: int,
        document_info: Optional[Dict] = None
    ) -> DocumentDownload:
        """
        Download a free document from Internet Archive/RECAP.

        This doesn't cost any tokens/credits.
        """
        # Create download record
        download = DocumentDownload(
            user_id=user_id,
            docket_id=docket_id,
            document_id=document_id,
            source=DocumentDownloadSource.FREE,
            status=DocumentDownloadStatus.PENDING,
            description=document_info.get("description") if document_info else None,
            document_number=document_info.get("document_number") if document_info else None
        )
        self.db.add(download)
        self.db.commit()

        try:
            download.status = DocumentDownloadStatus.DOWNLOADING
            self.db.commit()

            # Check availability first
            availability = await self.check_document_availability(document_id)

            if not availability.get("available") or not availability.get("free"):
                download.status = DocumentDownloadStatus.FAILED
                download.error_message = "Document not available for free download"
                self.db.commit()
                return download

            # Download from CourtListener/IA
            filepath_local = availability.get("filepath_local")
            if not filepath_local:
                download.status = DocumentDownloadStatus.FAILED
                download.error_message = "No file path available"
                self.db.commit()
                return download

            # Construct download URL
            download_url = f"https://storage.courtlistener.com/{filepath_local}"

            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, timeout=120.0)

                if response.status_code != 200:
                    download.status = DocumentDownloadStatus.FAILED
                    download.error_message = f"Download failed: HTTP {response.status_code}"
                    self.db.commit()
                    return download

                # Save file
                file_name = f"doc_{document_id}_{user_id}.pdf"
                file_path = os.path.join(self.storage_path, str(user_id), str(docket_id))
                os.makedirs(file_path, exist_ok=True)

                full_path = os.path.join(file_path, file_name)
                with open(full_path, "wb") as f:
                    f.write(response.content)

                # Update download record
                download.status = DocumentDownloadStatus.COMPLETED
                download.file_path = full_path
                download.file_name = file_name
                download.file_size = len(response.content)
                download.page_count = availability.get("page_count", 0)
                download.downloaded_at = datetime.utcnow()
                download.cost = Decimal("0")
                self.db.commit()

                logger.info(f"Successfully downloaded free document {document_id} for user {user_id}")
                return download

        except Exception as e:
            logger.error(f"Error downloading free document {document_id}: {e}")
            download.status = DocumentDownloadStatus.FAILED
            download.error_message = str(e)
            download.retry_count += 1
            self.db.commit()
            return download


    async def _submit_recap_fetch(
        self,
        pacer_doc_id: str,
        court: str,
        document_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Submit a RECAP Fetch request to CourtListener to purchase a document from PACER."""
        if not self.pacer_username or not self.pacer_password:
            raise ValueError("PACER credentials not configured. Set PACER_USERNAME and PACER_PASSWORD.")

        payload = {
            "request_type": 2,
            "pacer_username": self.pacer_username,
            "pacer_password": self.pacer_password,
            "pacer_doc_id": pacer_doc_id,
            "court": court
        }
        if document_number:
            payload["document_number"] = document_number

        logger.info(f"Submitting RECAP Fetch request: court={court}, pacer_doc_id={pacer_doc_id}")

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(
                f"{COURTLISTENER_API_BASE}/recap-fetch/",
                json=payload,
                headers=self._get_headers()
            )
            if response.status_code not in [200, 201]:
                logger.error(f"RECAP Fetch failed: {response.status_code} - {response.text}")
                raise ValueError(f"RECAP Fetch failed: {response.status_code}")
            data = response.json()
            logger.info(f"RECAP Fetch submitted: request_id={data.get('id')}")
            return {"success": True, "request_id": data.get("id"), "status": data.get("status")}

    async def _poll_recap_status(self, request_id: int) -> Dict[str, Any]:
        """Poll the RECAP Fetch status until completion or timeout."""
        start_time = datetime.utcnow()

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            while True:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > RECAP_MAX_WAIT_TIME:
                    raise TimeoutError(f"RECAP Fetch timed out after {RECAP_MAX_WAIT_TIME} seconds")

                response = await client.get(
                    f"{COURTLISTENER_API_BASE}/recap-fetch/{request_id}/",
                    headers=self._get_headers()
                )
                if response.status_code != 200:
                    raise ValueError(f"Failed to check RECAP status: {response.status_code}")

                data = response.json()
                status = data.get("status")
                logger.debug(f"RECAP Fetch {request_id} status: {status}")

                if status == 2:  # Success
                    return {"success": True, "completed": True, "filepath_local": data.get("filepath_local")}
                elif status == 3:  # Failed
                    raise ValueError(f"RECAP Fetch failed: {data.get('message', 'Unknown error')}")
                await asyncio.sleep(RECAP_POLL_INTERVAL)

    async def download_pacer_document(
        self,
        user_id: int,
        docket_id: int,
        document_id: int,
        document_info: Optional[Dict] = None
    ) -> DocumentDownload:
        """
        Download a document from PACER (paid).

        This uses the token system - user must have sufficient credits.
        Cost is $0.10 per page.
        """
        availability = await self.check_document_availability(document_id)
        if not availability.get("available"):
            raise ValueError("Document not available")

        page_count = availability.get("page_count", 0) or 1
        credits_needed = page_count
        cost_usd = Decimal(str(page_count)) * DOCUMENT_PRICE_PER_PAGE
        pacer_doc_id = availability.get("pacer_doc_id")
        court = availability.get("court")

        if not pacer_doc_id:
            raise ValueError("Document does not have PACER document ID - may be available free")

        monitor = self.db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == user_id,
            UserDocketMonitor.courtlistener_docket_id == docket_id,
            UserDocketMonitor.is_active == True
        ).first()

        if monitor:
            remaining_budget = monitor.pacer_download_budget - monitor.pacer_spent_this_month
            if cost_usd > remaining_budget:
                raise ValueError(f"Insufficient budget. Need ${cost_usd}, have ${remaining_budget}")

        user_credits = self.db.query(UserCredits).filter(UserCredits.user_id == user_id).first()
        if not user_credits or user_credits.balance < credits_needed:
            available = user_credits.balance if user_credits else 0
            raise ValueError(f"Insufficient credits. Need {credits_needed}, have {available}")

        download = DocumentDownload(
            user_id=user_id, docket_id=docket_id, document_id=document_id,
            source=DocumentDownloadSource.PACER, status=DocumentDownloadStatus.PENDING,
            description=document_info.get("description") if document_info else availability.get("description"),
            document_number=document_info.get("document_number") if document_info else availability.get("document_number"),
            page_count=page_count, cost=cost_usd
        )
        self.db.add(download)

        # Deduct credits before purchase
        user_credits.balance -= credits_needed
        user_credits.total_credits_spent += credits_needed
        user_credits.total_pages_downloaded += page_count
        credit_tx = CreditTransaction(
            user_credits_id=user_credits.id, transaction_type=TransactionType.DOCUMENT_PURCHASE,
            amount=-credits_needed, balance_after=user_credits.balance,
            description=f"PACER document: Doc #{document_id}, {page_count} pages"
        )
        self.db.add(credit_tx)
        self.db.commit()

        try:
            download.status = DocumentDownloadStatus.DOWNLOADING
            self.db.commit()

            fetch_result = await self._submit_recap_fetch(pacer_doc_id, court, availability.get("document_number"))
            if not fetch_result.get("success"):
                raise ValueError("Failed to submit RECAP Fetch request")

            poll_result = await self._poll_recap_status(fetch_result.get("request_id"))
            if not poll_result.get("completed"):
                raise ValueError("RECAP Fetch did not complete")

            filepath_local = poll_result.get("filepath_local")
            if not filepath_local:
                raise ValueError("No file path returned from RECAP Fetch")

            download_url = f"https://storage.courtlistener.com/{filepath_local}"
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, timeout=120.0)
                if response.status_code != 200:
                    raise ValueError(f"Download failed: HTTP {response.status_code}")

                file_name = f"doc_{document_id}_{user_id}.pdf"
                file_path = os.path.join(self.storage_path, str(user_id), str(docket_id))
                os.makedirs(file_path, exist_ok=True)
                full_path = os.path.join(file_path, file_name)
                with open(full_path, "wb") as f:
                    f.write(response.content)

                download.status = DocumentDownloadStatus.COMPLETED
                download.file_path = full_path
                download.file_name = file_name
                download.file_size = len(response.content)
                download.downloaded_at = datetime.utcnow()
                if monitor:
                    monitor.pacer_spent_this_month += cost_usd
                self.db.commit()
                logger.info(f"Downloaded PACER doc {document_id} for user {user_id}. Cost: {credits_needed} credits")
                return download

        except Exception as e:
            logger.error(f"Error downloading PACER document {document_id}: {e}")
            # Refund credits on failure
            user_credits.balance += credits_needed
            user_credits.total_credits_spent -= credits_needed
            user_credits.total_pages_downloaded -= page_count
            refund_tx = CreditTransaction(
                user_credits_id=user_credits.id, transaction_type=TransactionType.REFUND,
                amount=credits_needed, balance_after=user_credits.balance,
                description=f"Refund for failed PACER download: Doc #{document_id}"
            )
            self.db.add(refund_tx)
            download.status = DocumentDownloadStatus.FAILED
            download.error_message = str(e)
            download.retry_count += 1
            self.db.commit()
            return download

    async def auto_download_new_documents(
        self,
        user_id: int,
        docket_id: int,
        documents: List[Dict]
    ) -> List[DocumentDownload]:
        """
        Auto-download new documents based on user's preferences.

        Checks user's auto-download settings and budget before downloading.
        """
        # Get user's monitor settings
        monitor = self.db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == user_id,
            UserDocketMonitor.courtlistener_docket_id == docket_id,
            UserDocketMonitor.is_active == True
        ).first()

        if not monitor or not monitor.auto_download_enabled:
            logger.debug(f"Auto-download disabled for user {user_id} on docket {docket_id}")
            return []

        downloads = []

        for doc in documents:
            doc_id = doc.get("id") or doc.get("document_id")
            if not doc_id:
                continue

            # Check if already downloaded
            existing = self.db.query(DocumentDownload).filter(
                DocumentDownload.user_id == user_id,
                DocumentDownload.document_id == doc_id,
                DocumentDownload.status == DocumentDownloadStatus.COMPLETED
            ).first()

            if existing:
                logger.debug(f"Document {doc_id} already downloaded for user {user_id}")
                continue

            # Check availability
            availability = await self.check_document_availability(doc_id)

            if not availability.get("available"):
                continue

            is_free = availability.get("free", False)

            if is_free:
                # Download free document
                download = await self.download_free_document(
                    user_id=user_id,
                    docket_id=docket_id,
                    document_id=doc_id,
                    document_info=doc
                )
                downloads.append(download)

            elif not monitor.auto_download_free_only:
                # Check budget for PACER download
                estimated_cost = Decimal(str(availability.get("estimated_cost", 0)))
                remaining_budget = monitor.pacer_download_budget - monitor.pacer_spent_this_month

                if estimated_cost <= remaining_budget:
                    try:
                        download = await self.download_pacer_document(
                            user_id=user_id,
                            docket_id=docket_id,
                            document_id=doc_id,
                            document_info=doc
                        )

                        # Update spent amount
                        if download.status == DocumentDownloadStatus.COMPLETED:
                            monitor.pacer_spent_this_month += download.cost
                            self.db.commit()

                        downloads.append(download)

                    except ValueError as e:
                        logger.warning(f"PACER download skipped for doc {doc_id}: {e}")
                else:
                    logger.info(f"Skipping PACER download for doc {doc_id}: budget exceeded")

        return downloads

    def get_user_downloads(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[DocumentDownloadStatus] = None
    ) -> List[DocumentDownload]:
        """Get download history for a user"""
        query = self.db.query(DocumentDownload).filter(
            DocumentDownload.user_id == user_id
        )

        if status:
            query = query.filter(DocumentDownload.status == status)

        return query.order_by(
            DocumentDownload.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_user_budget_status(self, user_id: int, docket_id: int) -> Dict[str, Any]:
        """Get user's PACER budget status for a specific docket"""
        monitor = self.db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == user_id,
            UserDocketMonitor.courtlistener_docket_id == docket_id,
            UserDocketMonitor.is_active == True
        ).first()

        if not monitor:
            return {
                "budget": 0,
                "spent": 0,
                "remaining": 0,
                "auto_download_enabled": False
            }

        return {
            "budget": float(monitor.pacer_download_budget),
            "spent": float(monitor.pacer_spent_this_month),
            "remaining": float(monitor.pacer_download_budget - monitor.pacer_spent_this_month),
            "auto_download_enabled": monitor.auto_download_enabled,
            "auto_download_free_only": monitor.auto_download_free_only,
            "budget_reset_date": monitor.budget_reset_date.isoformat() if monitor.budget_reset_date else None
        }

    def reset_monthly_budgets(self):
        """Reset monthly PACER budgets for all users (run on 1st of month)"""
        from datetime import timedelta

        now = datetime.utcnow()
        one_month_ago = now - timedelta(days=30)

        monitors = self.db.query(UserDocketMonitor).filter(
            UserDocketMonitor.is_active == True,
            UserDocketMonitor.budget_reset_date < one_month_ago
        ).all()

        for monitor in monitors:
            monitor.pacer_spent_this_month = Decimal("0")
            monitor.budget_reset_date = now

        self.db.commit()
        logger.info(f"Reset monthly budgets for {len(monitors)} monitors")
