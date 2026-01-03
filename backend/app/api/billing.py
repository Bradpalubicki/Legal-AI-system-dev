"""
Legal AI System - Billing API Endpoints
Production-ready subscription and payment management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from ..core.database import get_async_session
from ..core.auth import get_current_user
from ..models.user import User
from ..models.billing import (
    Subscription, BillingPlan, Invoice, Payment,
    Usage, PaymentMethod, RefundRequest
)
from ..services.billing_service import billing_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
security = HTTPBearer()

# Pydantic models for request/response
class SubscriptionCreate(BaseModel):
    plan_id: int
    payment_method_id: str
    trial_days: Optional[int] = None

class SubscriptionResponse(BaseModel):
    id: int
    plan_id: int
    plan_name: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime]
    cancel_at_period_end: bool
    current_usage: Dict[str, Any]

class PlanResponse(BaseModel):
    id: int
    name: str
    description: str
    price_monthly: float
    price_yearly: Optional[float]
    features: Dict[str, Any]
    trial_days: int

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    total: float
    amount_due: float
    status: str
    due_date: Optional[datetime]
    hosted_invoice_url: Optional[str]

class PaymentResponse(BaseModel):
    id: int
    amount: float
    status: str
    processed_at: Optional[datetime]
    payment_method_type: str

class UsageResponse(BaseModel):
    feature: str
    current_usage: int
    limit: Optional[int]
    percentage_used: Optional[float]

class RefundCreate(BaseModel):
    payment_id: str
    amount: Optional[float] = None
    reason: str = "requested_by_customer"

class CheckoutSessionCreate(BaseModel):
    plan: str  # 'basic', 'individual_pro', 'professional', 'premium'
    billing_period: str = "monthly"  # 'monthly' or 'annual'
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

@router.get("/plans", response_model=List[PlanResponse])
async def get_billing_plans(
    session: AsyncSession = Depends(get_async_session)
):
    """Get all available billing plans"""
    try:
        plans = await session.execute(
            select(BillingPlan).where(BillingPlan.is_active == True)
        )
        plans = plans.scalars().all()

        return [
            PlanResponse(
                id=plan.id,
                name=plan.name,
                description=plan.description or "",
                price_monthly=float(plan.price_monthly),
                price_yearly=float(plan.price_yearly) if plan.price_yearly else None,
                features=plan.features,
                trial_days=plan.trial_days
            )
            for plan in plans
        ]

    except Exception as e:
        logger.error(f"Failed to get billing plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve plans")

@router.post("/create-checkout-session", response_model=Dict[str, Any])
async def create_checkout_session(
    checkout_data: CheckoutSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a Stripe Checkout session for subscription"""
    import stripe
    import os
    from ..core.pricing import SUBSCRIPTION_TIERS, SubscriptionTier

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    try:
        # Map plan name to tier
        plan_mapping = {
            'basic': SubscriptionTier.BASIC,
            'individual_pro': SubscriptionTier.INDIVIDUAL_PRO,
            'professional': SubscriptionTier.PROFESSIONAL,
            'premium': SubscriptionTier.PREMIUM,
        }

        tier = plan_mapping.get(checkout_data.plan.lower())
        if not tier:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {checkout_data.plan}")

        tier_config = SUBSCRIPTION_TIERS.get(tier)
        if not tier_config:
            raise HTTPException(status_code=400, detail="Plan configuration not found")

        # Get the correct Stripe price ID based on billing period
        if checkout_data.billing_period == 'annual':
            price_id = tier_config.stripe_price_id_annual
        else:
            price_id = tier_config.stripe_price_id_monthly

        if not price_id:
            raise HTTPException(status_code=400, detail="Stripe price not configured for this plan")

        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            # Update user with Stripe customer ID
            async with get_async_session() as session:
                from sqlalchemy import update
                await session.execute(
                    update(User).where(User.id == current_user.id)
                    .values(stripe_customer_id=customer.id)
                )
                await session.commit()
            customer_id = customer.id
        else:
            customer_id = current_user.stripe_customer_id

        # Build success and cancel URLs
        app_base_url = os.getenv("APP_BASE_URL", "http://localhost:3000")
        success_url = checkout_data.success_url or f"{app_base_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = checkout_data.cancel_url or f"{app_base_url}/subscription/cancel"

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={
                'trial_period_days': tier_config.trial_days if tier_config.trial_days > 0 else None,
                'metadata': {
                    'user_id': str(current_user.id),
                    'plan': checkout_data.plan,
                    'billing_period': checkout_data.billing_period,
                }
            },
            metadata={
                'user_id': str(current_user.id),
                'plan': checkout_data.plan,
            },
            allow_promotion_codes=True,
        )

        logger.info(f"Created checkout session {checkout_session.id} for user {current_user.id}, plan {checkout_data.plan}")

        return {
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/subscribe", response_model=Dict[str, Any])
async def create_subscription(
    subscription_data: SubscriptionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription"""
    try:
        result = await billing_service.create_subscription(
            user_id=current_user.id,
            plan_id=subscription_data.plan_id,
            payment_method_id=subscription_data.payment_method_id,
            trial_days=subscription_data.trial_days
        )

        logger.info(f"Created subscription for user {current_user.id}")
        return result

    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's current subscription"""
    try:
        subscription = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == current_user.id,
                    Subscription.status.in_(['active', 'trialing', 'past_due'])
                )
            ).options(selectinload(Subscription.plan))
        )
        subscription = subscription.scalar_one_or_none()

        if not subscription:
            return None

        return SubscriptionResponse(
            id=subscription.id,
            plan_id=subscription.plan_id,
            plan_name=subscription.plan.name,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            trial_end=subscription.trial_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            current_usage=subscription.current_usage or {}
        )

    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")

@router.post("/subscription/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    immediately: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Cancel a subscription"""
    try:
        success = await billing_service.cancel_subscription(
            user_id=current_user.id,
            subscription_id=subscription_id,
            immediately=immediately
        )

        if success:
            return {"message": "Subscription canceled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel subscription")

    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's invoices"""
    try:
        invoices = await session.execute(
            select(Invoice)
            .where(Invoice.user_id == current_user.id)
            .order_by(Invoice.created_date.desc())
            .limit(limit)
            .offset(offset)
        )
        invoices = invoices.scalars().all()

        return [
            InvoiceResponse(
                id=invoice.id,
                invoice_number=invoice.invoice_number or f"INV-{invoice.id}",
                total=float(invoice.total),
                amount_due=float(invoice.amount_due),
                status=invoice.status,
                due_date=invoice.due_date,
                hosted_invoice_url=invoice.hosted_invoice_url
            )
            for invoice in invoices
        ]

    except Exception as e:
        logger.error(f"Failed to get invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve invoices")

@router.get("/payments", response_model=List[PaymentResponse])
async def get_payments(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's payment history"""
    try:
        payments = await session.execute(
            select(Payment)
            .where(Payment.user_id == current_user.id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        payments = payments.scalars().all()

        return [
            PaymentResponse(
                id=payment.id,
                amount=float(payment.amount),
                status=payment.status,
                processed_at=payment.processed_at,
                payment_method_type=payment.payment_method_type or "card"
            )
            for payment in payments
        ]

    except Exception as e:
        logger.error(f"Failed to get payments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payments")

@router.get("/usage", response_model=List[UsageResponse])
async def get_current_usage(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current billing period usage"""
    try:
        # Get active subscription with plan
        subscription = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == current_user.id,
                    Subscription.status.in_(['active', 'trialing'])
                )
            ).options(selectinload(Subscription.plan))
        )
        subscription = subscription.scalar_one_or_none()

        if not subscription:
            return []

        current_usage = subscription.current_usage or {}
        plan_features = subscription.plan.features or {}

        usage_data = []
        for feature, usage_count in current_usage.items():
            limit = plan_features.get(feature)
            percentage = (usage_count / limit * 100) if limit else None

            usage_data.append(UsageResponse(
                feature=feature,
                current_usage=usage_count,
                limit=limit,
                percentage_used=percentage
            ))

        return usage_data

    except Exception as e:
        logger.error(f"Failed to get usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage")

@router.post("/usage/track")
async def track_usage(
    feature: str,
    quantity: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """Track feature usage (internal API)"""
    try:
        await billing_service.track_usage(
            user_id=current_user.id,
            feature=feature,
            quantity=quantity,
            metadata=metadata
        )

        return {"message": "Usage tracked successfully"}

    except Exception as e:
        logger.error(f"Failed to track usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to track usage")

@router.post("/refund", response_model=Dict[str, Any])
async def request_refund(
    refund_data: RefundCreate,
    current_user: User = Depends(get_current_user)
):
    """Request a refund"""
    try:
        result = await billing_service.process_refund(
            payment_id=refund_data.payment_id,
            amount=refund_data.amount,
            reason=refund_data.reason
        )

        return result

    except Exception as e:
        logger.error(f"Failed to process refund: {e}")
        raise HTTPException(status_code=500, detail="Failed to process refund")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")

        result = await billing_service.handle_webhook(payload, signature)
        return result

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

@router.get("/portal-session")
async def create_customer_portal_session(
    current_user: User = Depends(get_current_user)
):
    """Create Stripe customer portal session"""
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No customer found")

        import stripe
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url="https://legal-ai.production.com/billing"
        )

        return {"url": session.url}

    except Exception as e:
        logger.error(f"Failed to create portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

# Admin endpoints (require admin role)
@router.get("/admin/subscriptions", response_model=List[Dict[str, Any]])
async def get_all_subscriptions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all subscriptions (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        subscriptions = await session.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.user),
                selectinload(Subscription.plan)
            )
            .order_by(Subscription.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        subscriptions = subscriptions.scalars().all()

        return [
            {
                "id": sub.id,
                "user_email": sub.user.email,
                "plan_name": sub.plan.name,
                "status": sub.status,
                "created_at": sub.created_at,
                "current_period_end": sub.current_period_end
            }
            for sub in subscriptions
        ]

    except Exception as e:
        logger.error(f"Failed to get all subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscriptions")

@router.get("/admin/revenue-stats", response_model=Dict[str, Any])
async def get_revenue_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get revenue statistics (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # This would include comprehensive revenue analytics
        # For now, return basic stats
        return {
            "total_active_subscriptions": 0,
            "monthly_recurring_revenue": 0.0,
            "churn_rate": 0.0,
            "average_revenue_per_user": 0.0
        }

    except Exception as e:
        logger.error(f"Failed to get revenue stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stats")