"""
Pricing API Endpoints

Public and authenticated endpoints for:
- Viewing subscription tiers
- Viewing credit pack options
- Calculating document costs
- Purchasing credit packs
- Managing subscriptions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging

from ..src.core.database import get_db
from ..api.deps import get_current_user, CurrentUser, get_optional_user
from ..core.pricing import (
    DOCUMENT_PRICE_PER_PAGE,
    SubscriptionTier,
    CreditPackType,
    SUBSCRIPTION_TIERS,
    CREDIT_PACKS,
    get_tier_config,
    get_credit_pack_config,
    calculate_document_cost,
    get_best_credit_pack,
    get_all_tiers_comparison,
    get_all_credit_packs,
)
from ..models.credits import (
    UserCredits,
    CreditTransaction,
    CreditPackPurchase,
    TransactionType,
    CreditPackType as CreditPackTypeEnum,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pricing", tags=["Pricing"])


# =============================================================================
# Request/Response Models
# =============================================================================

class TierResponse(BaseModel):
    """Response for a subscription tier"""
    tier: str
    name: str
    description: str
    price_monthly: float
    price_annual: float
    effective_monthly_annual: float
    annual_savings: float
    included_credits: int
    credit_value: float
    features: Dict[str, Any]
    trial_days: int
    is_enterprise: bool


class CreditPackResponse(BaseModel):
    """Response for a credit pack"""
    pack_type: str
    name: str
    credits: int
    price: float
    price_per_credit: float
    savings_percent: float
    is_active: bool


class DocumentCostRequest(BaseModel):
    """Request to calculate document cost"""
    page_count: int = Field(..., ge=0)


class DocumentCostResponse(BaseModel):
    """Response with document cost breakdown"""
    page_count: int
    total_credits_needed: int
    price_per_page: float
    total_price: float
    credits_available: int
    credits_to_use: int
    credits_remaining_needed: int
    cash_needed: float
    is_free: bool
    recommended_pack: Optional[CreditPackResponse] = None


class PurchaseCreditsRequest(BaseModel):
    """Request to purchase credits"""
    pack_type: str = Field(..., description="Credit pack type to purchase")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")


class PurchaseCreditsResponse(BaseModel):
    """Response after purchasing credits"""
    success: bool
    credits_added: int
    new_balance: int
    amount_charged: float
    transaction_id: int
    message: str


class UserCreditsResponse(BaseModel):
    """Response with user's credit information"""
    balance: int
    subscription_credits: int
    subscription_credits_used: int
    purchased_credits: int
    subscription_tier: Optional[str]
    subscription_period_end: Optional[str]
    total_credits_spent: int
    total_pages_downloaded: int


# =============================================================================
# Public Endpoints (No Auth Required)
# =============================================================================

@router.get("/tiers", response_model=List[TierResponse])
async def get_subscription_tiers():
    """
    Get all available subscription tiers.

    Returns pricing, features, and included credits for each tier.
    """
    return get_all_tiers_comparison()


@router.get("/tiers/{tier}", response_model=TierResponse)
async def get_tier_details(tier: str):
    """
    Get details for a specific subscription tier.
    """
    try:
        tier_enum = SubscriptionTier(tier)
        config = get_tier_config(tier_enum)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tier '{tier}' not found"
            )

        return {
            "tier": config.tier.value,
            "name": config.name,
            "description": config.description,
            "price_monthly": float(config.price_monthly),
            "price_annual": float(config.price_annual),
            "effective_monthly_annual": float(config.effective_monthly_annual),
            "annual_savings": float(config.annual_savings),
            "included_credits": config.included_credits,
            "credit_value": float(config.credit_value),
            "features": config.features,
            "trial_days": config.trial_days,
            "is_enterprise": config.tier == SubscriptionTier.ENTERPRISE,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {tier}"
        )


@router.get("/credit-packs", response_model=List[CreditPackResponse])
async def get_credit_packs():
    """
    Get all available credit packs for pay-as-you-go purchases.

    Returns pricing and savings information for each pack.
    """
    return get_all_credit_packs()


@router.get("/credit-packs/{pack_type}", response_model=CreditPackResponse)
async def get_credit_pack_details(pack_type: str):
    """
    Get details for a specific credit pack.
    """
    try:
        pack_enum = CreditPackType(pack_type)
        config = get_credit_pack_config(pack_enum)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credit pack '{pack_type}' not found"
            )

        return {
            "pack_type": config.pack_type.value,
            "name": config.name,
            "credits": config.credits,
            "price": float(config.price),
            "price_per_credit": float(config.price_per_credit),
            "savings_percent": float(config.savings_vs_single) if config.pack_type != CreditPackType.SINGLE_PAGE else 0,
            "is_active": config.is_active,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pack type: {pack_type}"
        )


@router.get("/document-price")
async def get_document_price():
    """
    Get the base document download price.
    """
    return {
        "price_per_page": float(DOCUMENT_PRICE_PER_PAGE),
        "currency": "USD",
        "description": "Price per page for document downloads",
        "free_sources": ["recap", "internet_archive"],
        "paid_sources": ["pacer"],
    }


# =============================================================================
# Authenticated Endpoints
# =============================================================================

@router.post("/calculate-cost", response_model=DocumentCostResponse)
async def calculate_document_download_cost(
    request: DocumentCostRequest,
    current_user: CurrentUser = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Calculate the cost to download a document.

    Returns cost breakdown including how many credits would be used
    and how much cash (if any) would be needed.
    """
    # Get user's available credits
    credits_available = 0
    if current_user:
        user_credits = db.query(UserCredits).filter(
            UserCredits.user_id == current_user.user_id
        ).first()
        if user_credits:
            credits_available = user_credits.balance

    # Calculate cost
    cost_info = calculate_document_cost(request.page_count, credits_available)

    # Get recommended pack if user needs more credits
    recommended_pack = None
    if cost_info["credits_remaining_needed"] > 0:
        best_pack = get_best_credit_pack(cost_info["credits_remaining_needed"])
        if best_pack:
            recommended_pack = {
                "pack_type": best_pack.pack_type.value,
                "name": best_pack.name,
                "credits": best_pack.credits,
                "price": float(best_pack.price),
                "price_per_credit": float(best_pack.price_per_credit),
                "savings_percent": float(best_pack.savings_vs_single) if best_pack.pack_type != CreditPackType.SINGLE_PAGE else 0,
                "is_active": best_pack.is_active,
            }

    return DocumentCostResponse(
        **cost_info,
        recommended_pack=recommended_pack
    )


@router.get("/my-credits", response_model=UserCreditsResponse)
async def get_my_credits(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's credit balance and usage information.
    """
    user_credits = db.query(UserCredits).filter(
        UserCredits.user_id == current_user.user_id
    ).first()

    if not user_credits:
        # Create credit record if doesn't exist
        user_credits = UserCredits(
            user_id=current_user.user_id,
            username=current_user.username or f"user_{current_user.user_id}",
            balance=0,
            subscription_credits=0,
            subscription_credits_used=0,
            purchased_credits=0,
        )
        db.add(user_credits)
        db.commit()
        db.refresh(user_credits)

    # TODO: Get subscription tier from user's subscription
    subscription_tier = None
    subscription_period_end = None

    return UserCreditsResponse(
        balance=user_credits.balance,
        subscription_credits=user_credits.subscription_credits,
        subscription_credits_used=user_credits.subscription_credits_used,
        purchased_credits=user_credits.purchased_credits,
        subscription_tier=subscription_tier,
        subscription_period_end=subscription_period_end,
        total_credits_spent=user_credits.total_credits_spent,
        total_pages_downloaded=user_credits.total_pages_downloaded,
    )


@router.post("/purchase-credits", response_model=PurchaseCreditsResponse)
async def purchase_credits(
    request: PurchaseCreditsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Purchase a credit pack.

    This endpoint creates the purchase record. Payment processing
    should be handled separately via Stripe.
    """
    try:
        # Validate pack type
        pack_enum = CreditPackTypeEnum(request.pack_type)
        pack_config = get_credit_pack_config(CreditPackType(request.pack_type))

        if not pack_config or not pack_config.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Credit pack '{request.pack_type}' is not available"
            )

        # Get or create user credits
        user_credits = db.query(UserCredits).filter(
            UserCredits.user_id == current_user.user_id
        ).first()

        if not user_credits:
            user_credits = UserCredits(
                user_id=current_user.user_id,
                username=current_user.username or f"user_{current_user.user_id}",
                balance=0,
            )
            db.add(user_credits)
            db.commit()
            db.refresh(user_credits)

        # Create credit pack purchase record
        purchase = CreditPackPurchase(
            user_credits_id=user_credits.id,
            pack_type=pack_enum,
            pack_name=pack_config.name,
            credits_purchased=pack_config.credits,
            price_paid=pack_config.price,
            price_per_credit=pack_config.price_per_credit,
            payment_method="stripe" if request.payment_method_id else "pending",
            status="pending",
        )
        db.add(purchase)
        db.commit()
        db.refresh(purchase)

        # TODO: Process payment via Stripe
        # For now, mark as completed (in production, this would wait for payment confirmation)

        # Add credits to user's balance
        old_balance = user_credits.balance
        user_credits.balance += pack_config.credits
        user_credits.purchased_credits += pack_config.credits
        user_credits.total_credits_purchased += pack_config.credits
        user_credits.total_amount_spent = (user_credits.total_amount_spent or Decimal("0")) + pack_config.price

        # Create transaction record
        transaction = CreditTransaction(
            user_credits_id=user_credits.id,
            transaction_type=TransactionType.CREDIT_PURCHASE,
            amount=pack_config.credits,
            balance_after=user_credits.balance,
            credit_pack_type=pack_enum,
            cash_amount=pack_config.price,
            description=f"Purchased {pack_config.name} ({pack_config.credits} credits)",
            payment_method="stripe" if request.payment_method_id else "pending",
            credit_pack_purchase_id=purchase.id,
        )
        db.add(transaction)

        # Update purchase status
        purchase.status = "completed"
        purchase.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(transaction)

        logger.info(f"User {current_user.user_id} purchased {pack_config.credits} credits for ${pack_config.price}")

        return PurchaseCreditsResponse(
            success=True,
            credits_added=pack_config.credits,
            new_balance=user_credits.balance,
            amount_charged=float(pack_config.price),
            transaction_id=transaction.id,
            message=f"Successfully purchased {pack_config.credits} credits!",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pack type: {request.pack_type}"
        )
    except Exception as e:
        logger.error(f"Error purchasing credits: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purchase credits: {str(e)}"
        )


@router.get("/purchase-history")
async def get_purchase_history(
    limit: int = 20,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's credit pack purchase history.
    """
    user_credits = db.query(UserCredits).filter(
        UserCredits.user_id == current_user.user_id
    ).first()

    if not user_credits:
        return {"purchases": [], "total": 0}

    purchases = db.query(CreditPackPurchase).filter(
        CreditPackPurchase.user_credits_id == user_credits.id
    ).order_by(
        CreditPackPurchase.created_at.desc()
    ).offset(offset).limit(limit).all()

    total = db.query(CreditPackPurchase).filter(
        CreditPackPurchase.user_credits_id == user_credits.id
    ).count()

    return {
        "purchases": [
            {
                "id": p.id,
                "pack_type": p.pack_type.value if p.pack_type else None,
                "pack_name": p.pack_name,
                "credits_purchased": p.credits_purchased,
                "price_paid": float(p.price_paid),
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in purchases
        ],
        "total": total,
    }


@router.get("/transactions")
async def get_credit_transactions(
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's credit transaction history.
    """
    user_credits = db.query(UserCredits).filter(
        UserCredits.user_id == current_user.user_id
    ).first()

    if not user_credits:
        return {"transactions": [], "total": 0}

    query = db.query(CreditTransaction).filter(
        CreditTransaction.user_credits_id == user_credits.id
    )

    if transaction_type:
        try:
            type_enum = TransactionType(transaction_type)
            query = query.filter(CreditTransaction.transaction_type == type_enum)
        except ValueError:
            pass

    transactions = query.order_by(
        CreditTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()

    total = query.count()

    return {
        "transactions": [
            {
                "id": t.id,
                "type": t.transaction_type.value if t.transaction_type else None,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "cash_amount": float(t.cash_amount) if t.cash_amount else None,
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in transactions
        ],
        "total": total,
    }
