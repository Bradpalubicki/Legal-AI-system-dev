"""
Credit Management API Endpoints

Provides API for managing user credits and document purchases.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from ..src.core.database import get_db
from ..models.credits import UserCredits, CreditTransaction, DocumentPurchase, TransactionType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/credits", tags=["Credits"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreditBalanceResponse(BaseModel):
    """User credit balance information"""
    user_id: int
    username: str
    balance: float
    total_purchased: float
    total_spent: float


class AddCreditsRequest(BaseModel):
    """Request to add credits to user account"""
    user_id: int
    username: str
    amount: float = Field(..., gt=0, description="Amount of credits to add")
    payment_method: str = Field(..., description="Payment method (e.g., stripe, paypal)")
    payment_id: Optional[str] = Field(None, description="External payment reference")
    description: Optional[str] = None


class PurchaseDocumentRequest(BaseModel):
    """Request to purchase a PACER document with credits"""
    document_id: Optional[str] = None
    docket_id: Optional[str] = None
    court: str = Field(..., description="Court identifier (e.g., nvd, cand)")
    case_number: Optional[str] = None
    document_number: int = Field(..., description="Document number on docket")
    attachment_number: Optional[int] = None
    estimated_cost: float = Field(..., description="Estimated cost in credits/dollars")
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    """Credit transaction information"""
    id: int
    transaction_type: str
    amount: float
    balance_after: float
    description: Optional[str]
    created_at: datetime


class PurchaseResponse(BaseModel):
    """Document purchase information"""
    id: int
    document_id: Optional[str]
    court: Optional[str]
    case_number: Optional[str]
    document_number: Optional[int]
    cost_credits: float
    status: str
    description: Optional[str]
    file_path: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


# ============================================================================
# Credit Balance Endpoints
# ============================================================================

@router.get("/balance/{user_id}")
async def get_credit_balance(
    user_id: int,
    db: Session = Depends(get_db)
) -> CreditBalanceResponse:
    """
    Get user's credit balance.

    Returns current balance and lifetime totals.
    """
    try:
        user_credits = db.query(UserCredits).filter(UserCredits.user_id == user_id).first()

        if not user_credits:
            # Create new credits account with $0 balance
            user_credits = UserCredits(
                user_id=user_id,
                username=f"user_{user_id}",
                balance=0,
                total_credits_purchased=0,
                total_credits_spent=0
            )
            db.add(user_credits)
            db.commit()
            db.refresh(user_credits)

        return CreditBalanceResponse(
            user_id=user_credits.user_id,
            username=user_credits.username,
            balance=float(user_credits.balance),
            total_purchased=float(user_credits.total_credits_purchased),
            total_spent=float(user_credits.total_credits_spent)
        )

    except Exception as e:
        logger.error(f"Error getting credit balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credit balance: {str(e)}"
        )


@router.post("/add")
async def add_credits(
    request: AddCreditsRequest,
    db: Session = Depends(get_db)
):
    """
    Add credits to user account.

    This endpoint should be called after successful payment processing.
    In production, verify payment with payment provider before adding credits.
    """
    try:
        # Get or create user credits account
        user_credits = db.query(UserCredits).filter(UserCredits.user_id == request.user_id).first()

        if not user_credits:
            user_credits = UserCredits(
                user_id=request.user_id,
                username=request.username,
                balance=0,
                total_credits_purchased=0,
                total_credits_spent=0
            )
            db.add(user_credits)
            db.flush()

        # Update balance
        user_credits.balance += int(request.amount)
        user_credits.total_credits_purchased += int(request.amount)
        user_credits.updated_at = datetime.utcnow()

        # Create transaction record
        transaction = CreditTransaction(
            user_credits_id=user_credits.id,
            transaction_type=TransactionType.CREDIT_PURCHASE,
            amount=request.amount,
            balance_after=user_credits.balance,
            description=request.description or f"Credits purchased: ${request.amount:.2f}",
            payment_method=request.payment_method,
            payment_id=request.payment_id
        )
        db.add(transaction)

        db.commit()
        db.refresh(user_credits)

        logger.info(f"Added {request.amount} credits to user {request.user_id}. New balance: {user_credits.balance}")

        return {
            "success": True,
            "message": f"Successfully added {request.amount} credits",
            "new_balance": user_credits.balance,
            "transaction_id": transaction.id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding credits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add credits: {str(e)}"
        )


# ============================================================================
# Transaction History
# ============================================================================

@router.get("/transactions/{user_id}")
async def get_transactions(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[TransactionResponse]:
    """
    Get user's credit transaction history.

    Returns recent transactions ordered by date (newest first).
    """
    try:
        user_credits = db.query(UserCredits).filter(UserCredits.user_id == user_id).first()

        if not user_credits:
            return []

        transactions = (
            db.query(CreditTransaction)
            .filter(CreditTransaction.user_credits_id == user_credits.id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            TransactionResponse(
                id=t.id,
                transaction_type=t.transaction_type.value,
                amount=t.amount,
                balance_after=t.balance_after,
                description=t.description,
                created_at=t.created_at
            )
            for t in transactions
        ]

    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transactions: {str(e)}"
        )


# ============================================================================
# Purchase History
# ============================================================================

@router.get("/purchases/{user_id}")
async def get_purchases(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[PurchaseResponse]:
    """
    Get user's document purchase history.

    Returns recent purchases ordered by date (newest first).
    """
    try:
        user_credits = db.query(UserCredits).filter(UserCredits.user_id == user_id).first()

        if not user_credits:
            return []

        purchases = (
            db.query(DocumentPurchase)
            .filter(DocumentPurchase.user_credits_id == user_credits.id)
            .order_by(DocumentPurchase.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            PurchaseResponse(
                id=p.id,
                document_id=p.document_id,
                court=p.court,
                case_number=p.case_number,
                document_number=p.document_number,
                cost_credits=p.cost_credits,
                status=p.status,
                description=p.description,
                file_path=p.file_path,
                created_at=p.created_at,
                completed_at=p.completed_at
            )
            for p in purchases
        ]

    except Exception as e:
        logger.error(f"Error getting purchases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get purchases: {str(e)}"
        )


# ============================================================================
# Document Purchase with Credits
# ============================================================================

@router.post("/purchase-document")
async def purchase_document_with_credits(
    request: PurchaseDocumentRequest,
    user_id: int,
    username: str,
    pacer_username: str,
    pacer_password: str,
    db: Session = Depends(get_db)
):
    """
    Purchase a PACER document using credits.

    Process:
    1. Check user has sufficient credits
    2. Deduct credits from balance
    3. Submit PACER purchase request via CourtListener
    4. Track purchase status
    5. Download document when ready
    """
    try:
        # Get user credits account
        user_credits = db.query(UserCredits).filter(UserCredits.user_id == user_id).first()

        if not user_credits:
            user_credits = UserCredits(
                user_id=user_id,
                username=username,
                balance=0.0
            )
            db.add(user_credits)
            db.flush()

        # Check sufficient balance
        if user_credits.balance < request.estimated_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Balance: ${user_credits.balance:.2f}, Required: ${request.estimated_cost:.2f}"
            )

        # IMPORTANT: Check if document is already free in RECAP Archive before charging
        # This saves users money if the document has become freely available
        from ..src.services.courtlistener_service import CourtListenerService
        import os

        cl_service = CourtListenerService(db, api_key=os.getenv("COURTLISTENER_API_KEY"))

        logger.info(f"Checking if document {request.document_id} is already free in RECAP Archive...")

        try:
            availability_check = await cl_service.check_document_availability(
                court=request.court,
                pacer_doc_ids=[request.document_id]
            )

            if availability_check.get("success"):
                doc_info = availability_check["results"].get(request.document_id, {})

                if doc_info.get("is_available") and doc_info.get("filepath_local"):
                    # Document is FREE! Don't charge the user
                    logger.info(f"Document {request.document_id} is FREE in RECAP! Not charging user.")

                    return {
                        "success": True,
                        "free_download": True,
                        "message": "Great news! This document is available for FREE in the RECAP Archive. No credits charged.",
                        "filepath_local": doc_info["filepath_local"],
                        "download_url": f"https://www.courtlistener.com{doc_info['filepath_local']}",
                        "recap_document_id": doc_info["recap_document_id"],
                        "cost_credits": 0.0,
                        "balance_unchanged": user_credits.balance
                    }
                else:
                    logger.info(f"Document {request.document_id} not available in RECAP. Proceeding with purchase.")
            else:
                logger.warning(f"RECAP availability check failed: {availability_check.get('error')}. Proceeding with purchase anyway.")

        except Exception as e:
            # If availability check fails, don't block the purchase - just log and continue
            logger.error(f"Error checking RECAP availability: {e}. Proceeding with purchase.")

        # Create purchase record
        purchase = DocumentPurchase(
            user_credits_id=user_credits.id,
            document_id=request.document_id,
            docket_id=request.docket_id,
            court=request.court,
            case_number=request.case_number,
            document_number=request.document_number,
            cost_credits=request.estimated_cost,
            status="pending",
            description=request.description
        )
        db.add(purchase)
        db.flush()

        # Deduct credits
        user_credits.balance -= request.estimated_cost
        user_credits.total_spent += request.estimated_cost
        user_credits.updated_at = datetime.utcnow()

        # Create transaction record
        transaction = CreditTransaction(
            user_credits_id=user_credits.id,
            transaction_type=TransactionType.DOCUMENT_PURCHASE,
            amount=-request.estimated_cost,
            balance_after=user_credits.balance,
            description=f"PACER document purchase: {request.court} {request.case_number or ''} Doc #{request.document_number}",
            document_purchase_id=purchase.id
        )
        db.add(transaction)

        db.commit()
        db.refresh(purchase)

        logger.info(f"User {user_id} purchased document. Cost: ${request.estimated_cost:.2f}, New balance: ${user_credits.balance:.2f}")

        # Submit to CourtListener RECAP Fetch API
        from ..src.services.courtlistener_service import CourtListenerService

        cl_service = CourtListenerService(db)

        try:
            # Update purchase status
            purchase.status = "processing"
            db.commit()

            # Submit PACER purchase request
            fetch_result = await cl_service.purchase_pacer_document(
                court=request.court,
                document_number=request.document_number,
                attachment_number=request.attachment_number,
                request_type=2,  # PDF download
                pacer_username=pacer_username,
                pacer_password=pacer_password,
                docket_number=request.case_number
            )

            # Store RECAP fetch request ID
            if fetch_result.get("success"):
                purchase.recap_fetch_id = fetch_result.get("request_id")
                db.commit()

                return {
                    "success": True,
                    "purchase_id": purchase.id,
                    "recap_fetch_id": purchase.recap_fetch_id,
                    "status": "processing",
                    "message": "Document purchase submitted. Check status for completion.",
                    "new_balance": user_credits.balance
                }
            else:
                # Purchase failed - refund credits
                purchase.status = "failed"
                purchase.error_message = fetch_result.get("error", "Unknown error")

                # Refund
                user_credits.balance += request.estimated_cost
                user_credits.total_spent -= request.estimated_cost

                refund_transaction = CreditTransaction(
                    user_credits_id=user_credits.id,
                    transaction_type=TransactionType.REFUND,
                    amount=request.estimated_cost,
                    balance_after=user_credits.balance,
                    description=f"Refund for failed purchase #{purchase.id}",
                    document_purchase_id=purchase.id
                )
                db.add(refund_transaction)
                db.commit()

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Purchase failed: {purchase.error_message}"
                )

        except Exception as e:
            # Refund on error
            purchase.status = "failed"
            purchase.error_message = str(e)

            user_credits.balance += request.estimated_cost
            user_credits.total_spent -= request.estimated_cost

            refund_transaction = CreditTransaction(
                user_credits_id=user_credits.id,
                transaction_type=TransactionType.REFUND,
                amount=request.estimated_cost,
                balance_after=user_credits.balance,
                description=f"Refund for failed purchase #{purchase.id}",
                document_purchase_id=purchase.id
            )
            db.add(refund_transaction)
            db.commit()

            logger.error(f"Error submitting PACER purchase: {e}")
            raise

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error purchasing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purchase document: {str(e)}"
        )


@router.get("/purchase-status/{purchase_id}")
async def get_purchase_status(
    purchase_id: int,
    db: Session = Depends(get_db)
):
    """
    Check status of a document purchase.

    Polls CourtListener for completion and downloads document when ready.
    """
    try:
        purchase = db.query(DocumentPurchase).filter(DocumentPurchase.id == purchase_id).first()

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )

        # If already completed or failed, return current status
        if purchase.status in ["completed", "failed"]:
            return {
                "purchase_id": purchase.id,
                "status": purchase.status,
                "file_path": purchase.file_path,
                "error_message": purchase.error_message,
                "completed_at": purchase.completed_at
            }

        # Check RECAP Fetch status
        if purchase.recap_fetch_id:
            from ..src.services.courtlistener_service import CourtListenerService

            cl_service = CourtListenerService(db)

            try:
                fetch_status = await cl_service.check_fetch_status(purchase.recap_fetch_id)

                if fetch_status.get("completed") and not fetch_status.get("failed"):
                    # Download completed document
                    import os
                    import uuid

                    filename = f"pacer_{purchase.court}_{purchase.document_number}_{uuid.uuid4().hex[:8]}.pdf"
                    save_dir = os.path.join(os.getcwd(), "storage", "purchased_documents")
                    save_path = os.path.join(save_dir, filename)

                    download_result = await cl_service.download_purchased_document(
                        filepath_local=fetch_status.get("document_url"),
                        save_path=save_path
                    )

                    if download_result.get("success"):
                        purchase.status = "completed"
                        purchase.file_path = save_path
                        purchase.file_size = download_result.get("file_size")
                        purchase.pacer_cost = fetch_status.get("cost")
                        purchase.completed_at = datetime.utcnow()
                        db.commit()

                        logger.info(f"Purchase {purchase_id} completed. Document saved to {save_path}")

                elif fetch_status.get("failed"):
                    purchase.status = "failed"
                    purchase.error_message = fetch_status.get("error", "Purchase failed")
                    db.commit()

            except Exception as e:
                logger.error(f"Error checking fetch status: {e}")
                # Don't fail - just return current status

        return {
            "purchase_id": purchase.id,
            "status": purchase.status,
            "file_path": purchase.file_path,
            "error_message": purchase.error_message,
            "completed_at": purchase.completed_at,
            "recap_fetch_id": purchase.recap_fetch_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting purchase status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get purchase status: {str(e)}"
        )


# ============================================================================
# Stats Endpoint
# ============================================================================

@router.get("/stats/{user_id}")
async def get_credit_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive credit statistics for user.
    """
    try:
        user_credits = db.query(UserCredits).filter(UserCredits.user_id == user_id).first()

        if not user_credits:
            return {
                "balance": 0.0,
                "total_purchased": 0.0,
                "total_spent": 0.0,
                "documents_purchased": 0,
                "pending_purchases": 0
            }

        # Count purchases
        total_purchases = db.query(DocumentPurchase).filter(
            DocumentPurchase.user_credits_id == user_credits.id
        ).count()

        pending_purchases = db.query(DocumentPurchase).filter(
            DocumentPurchase.user_credits_id == user_credits.id,
            DocumentPurchase.status.in_(["pending", "processing"])
        ).count()

        return {
            "balance": user_credits.balance,
            "total_purchased": user_credits.total_credits_purchased,
            "total_spent": user_credits.total_credits_spent,
            "documents_purchased": total_purchases,
            "pending_purchases": pending_purchases,
            "created_at": user_credits.created_at,
            "updated_at": user_credits.updated_at
        }

    except Exception as e:
        logger.error(f"Error getting credit stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credit stats: {str(e)}"
        )
