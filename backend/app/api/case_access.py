"""
Case Access API
Handles pay-per-case purchases and access management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import stripe
import os

from app.api.deps.database import get_db
from app.api.deps.feature_gates import get_user_from_db
from app.models.user import User
from app.models.case_access import (
    CaseAccess,
    CaseAccessPurchase,
    CaseAccessType,
    CaseAccessStatus,
    CaseMonitoringEvent
)
from app.models.billing import Subscription
from shared.database.models import TrackedDocket


router = APIRouter(prefix="/api/v1/case-access", tags=["case-access"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_CASE_ACCESS")


# ============================================================================
# Request/Response Models
# ============================================================================

class PurchaseCaseAccessRequest(BaseModel):
    """Request to purchase access to a case"""
    case_id: int
    access_type: str = "one_time"  # one_time ($5) or monthly ($19)
    notification_email: Optional[EmailStr] = None
    success_url: str
    cancel_url: str


class CaseAccessResponse(BaseModel):
    """Response for case access"""
    id: int
    case_id: int
    case_number: str
    case_name: str
    access_type: str
    status: str
    amount_paid: Optional[float]
    granted_at: Optional[datetime]
    expires_at: Optional[datetime]
    days_remaining: Optional[int]
    notifications_enabled: bool
    is_active: bool


class CheckoutSessionResponse(BaseModel):
    """Response for Stripe checkout session"""
    checkout_url: str
    session_id: str


# ============================================================================
# Case Access Purchase
# ============================================================================

@router.post("/purchase", response_model=CheckoutSessionResponse)
async def purchase_case_access(
    request: PurchaseCaseAccessRequest,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db)
):
    """
    Purchase access to a specific case

    Creates a Stripe checkout session for:
    - One-time access: $5 (access until case closes)
    - Monthly unlimited: $19/month
    """
    # Verify case exists
    case = db.query(TrackedDocket).filter(TrackedDocket.id == request.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Check if user already has active access
    existing_access = db.query(CaseAccess).filter(
        CaseAccess.user_id == user.id,
        CaseAccess.case_id == request.case_id,
        CaseAccess.status == CaseAccessStatus.ACTIVE
    ).first()

    if existing_access and existing_access.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "already_has_access",
                "message": "You already have access to this case",
                "case_access_id": existing_access.id,
                "expires_at": existing_access.expires_at.isoformat() if existing_access.expires_at else None
            }
        )

    # Determine pricing and access duration
    if request.access_type == "one_time":
        amount = 500  # $5.00 in cents
        access_duration = None  # Until case closes
        description = f"Case Monitoring: {case.case_name} ({case.docket_number})"
    elif request.access_type == "monthly":
        amount = 1900  # $19.00 in cents
        access_duration = 30  # 30 days
        description = f"Monthly Case Monitoring: {case.case_name}"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid access_type. Must be 'one_time' or 'monthly'"
        )

    # Create pending case access record
    case_access = CaseAccess(
        user_id=user.id,
        case_id=request.case_id,
        access_type=CaseAccessType(request.access_type),
        status=CaseAccessStatus.PENDING,
        amount_paid=amount / 100,  # Store in dollars
        notification_email=request.notification_email or user.email,
        notifications_enabled=True
    )

    db.add(case_access)
    db.commit()
    db.refresh(case_access)

    # Create Stripe checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id if user.stripe_customer_id else None,
            customer_email=user.email if not user.stripe_customer_id else None,
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount,
                        "product_data": {
                            "name": description,
                            "description": f"Monitor case updates and download documents",
                            "metadata": {
                                "case_id": str(case.id),
                                "case_number": case.docket_number,
                                "access_type": request.access_type
                            }
                        }
                    },
                    "quantity": 1
                }
            ],
            metadata={
                "user_id": str(user.id),
                "case_id": str(request.case_id),
                "case_access_id": str(case_access.id),
                "access_type": request.access_type,
                "product_type": "case_access"
            },
            success_url=request.success_url + f"?session_id={{CHECKOUT_SESSION_ID}}&case_id={request.case_id}",
            cancel_url=request.cancel_url,
            expires_at=int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        )

        # Update case access with session ID
        case_access.stripe_checkout_session_id = checkout_session.id
        db.commit()

        return CheckoutSessionResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )

    except stripe.error.StripeError as e:
        # Rollback case access creation
        db.delete(case_access)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}"
        )


# ============================================================================
# Webhook Handler
# ============================================================================

@router.post("/webhook")
async def handle_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks for case access payments

    Processes:
    - checkout.session.completed - Grant case access
    - charge.refunded - Revoke case access
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle different event types
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await _handle_successful_payment(session, db)

    elif event["type"] == "charge.refunded":
        charge = event["data"]["object"]
        await _handle_refund(charge, db)

    return {"status": "success"}


async def _handle_successful_payment(session: dict, db: Session):
    """Grant case access after successful payment"""
    case_access_id = session["metadata"].get("case_access_id")
    access_type = session["metadata"].get("access_type")

    if not case_access_id:
        print(f"No case_access_id in webhook metadata: {session['id']}")
        return

    case_access = db.query(CaseAccess).filter(CaseAccess.id == int(case_access_id)).first()

    if not case_access:
        print(f"Case access not found: {case_access_id}")
        return

    # Grant access
    case_access.status = CaseAccessStatus.ACTIVE
    case_access.granted_at = datetime.utcnow()
    case_access.stripe_payment_intent_id = session.get("payment_intent")

    # Set expiration for monthly subscriptions
    if access_type == "monthly":
        case_access.expires_at = datetime.utcnow() + timedelta(days=30)
    # One-time purchases don't expire (access until case closes)

    # Create purchase record
    payment_intent = stripe.PaymentIntent.retrieve(session["payment_intent"])
    charge = payment_intent.charges.data[0] if payment_intent.charges.data else None

    purchase = CaseAccessPurchase(
        user_id=case_access.user_id,
        case_access_id=case_access.id,
        amount=session["amount_total"] / 100,  # Convert cents to dollars
        currency=session["currency"].upper(),
        stripe_payment_intent_id=session["payment_intent"],
        stripe_charge_id=charge.id if charge else None,
        stripe_receipt_url=charge.receipt_url if charge else None,
        payment_method_type=session.get("payment_method_types", ["card"])[0] if charge else None,
        card_brand=charge.payment_method_details.card.brand if charge and charge.payment_method_details else None,
        card_last4=charge.payment_method_details.card.last4 if charge and charge.payment_method_details else None
    )

    db.add(purchase)

    # Create welcome event
    event = CaseMonitoringEvent(
        case_access_id=case_access.id,
        case_id=case_access.case_id,
        user_id=case_access.user_id,
        event_type="access_granted",
        event_title="Case monitoring activated",
        event_description="You now have access to monitor this case and receive notifications"
    )
    db.add(event)

    db.commit()

    # Start monitoring the case automatically
    try:
        from app.services.case_monitoring_bridge import get_monitoring_bridge

        # Check if case has CourtListener ID
        case = case_access.case
        if hasattr(case, 'courtlistener_docket_id') and case.courtlistener_docket_id:
            bridge = get_monitoring_bridge(db)
            await bridge.ensure_case_monitored(case.id, case.courtlistener_docket_id)
            print(f"✓ Started monitoring case {case.id} (docket {case.courtlistener_docket_id})")
        else:
            print(f"⚠️ Case {case.id} doesn't have CourtListener ID - manual monitoring required")

    except Exception as e:
        print(f"⚠️ Failed to auto-start monitoring: {e}")
        # Don't fail the webhook - access is already granted

    # Send welcome email with case monitoring info
    try:
        from app.services.email_notification_service import email_notification_service
        from app.models.user import User

        user = db.query(User).filter(User.id == case_access.user_id).first()
        case = case_access.case

        if user and case:
            email_notification_service.send_case_access_welcome_email(
                to_email=case_access.notification_email or user.email,
                user_name=user.display_name,
                case_name=case.case_name,
                case_number=case.docket_number,
                access_type=access_type,
                amount_paid=float(case_access.amount_paid) if case_access.amount_paid else 0.0,
                expires_at=case_access.expires_at
            )
            print(f"✓ Welcome email sent for case access {case_access.id}")
    except Exception as e:
        print(f"⚠️ Failed to send welcome email: {e}")
        # Don't fail the webhook - access is already granted


async def _handle_refund(charge: dict, db: Session):
    """Handle refunded case access payment"""
    payment_intent_id = charge["payment_intent"]

    purchase = db.query(CaseAccessPurchase).filter(
        CaseAccessPurchase.stripe_payment_intent_id == payment_intent_id
    ).first()

    if not purchase:
        print(f"Purchase not found for refund: {payment_intent_id}")
        return

    # Mark purchase as refunded
    purchase.refunded = True
    purchase.refund_amount = charge["amount_refunded"] / 100
    purchase.refunded_at = datetime.utcnow()

    # Cancel case access
    case_access = purchase.case_access
    if case_access:
        case_access.cancel(reason="Payment refunded")

    db.commit()


# ============================================================================
# Case Access Management
# ============================================================================

@router.get("/my-cases", response_model=List[CaseAccessResponse])
async def get_my_case_access(
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db)
):
    """Get all cases the current user has access to"""
    case_accesses = db.query(CaseAccess).filter(
        CaseAccess.user_id == user.id,
        CaseAccess.status.in_([CaseAccessStatus.ACTIVE, CaseAccessStatus.PENDING])
    ).all()

    results = []
    for access in case_accesses:
        case = access.case
        if not case:
            continue

        results.append(CaseAccessResponse(
            id=access.id,
            case_id=access.case_id,
            case_number=case.docket_number,
            case_name=case.case_name,
            access_type=access.access_type.value,
            status=access.status.value,
            amount_paid=float(access.amount_paid) if access.amount_paid else None,
            granted_at=access.granted_at,
            expires_at=access.expires_at,
            days_remaining=access.days_remaining(),
            notifications_enabled=access.notifications_enabled,
            is_active=access.is_active()
        ))

    return results


@router.get("/{case_id}/check")
async def check_case_access(
    case_id: int,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db)
):
    """Check if user has access to a specific case"""
    # Check direct case access
    case_access = db.query(CaseAccess).filter(
        CaseAccess.user_id == user.id,
        CaseAccess.case_id == case_id,
        CaseAccess.status == CaseAccessStatus.ACTIVE
    ).first()

    if case_access and case_access.is_active():
        return {
            "has_access": True,
            "access_type": case_access.access_type.value,
            "expires_at": case_access.expires_at.isoformat() if case_access.expires_at else None,
            "days_remaining": case_access.days_remaining()
        }

    # Check if user has Pro/Firm subscription (unlimited access)
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(["active", "trialing"])
    ).first()

    if subscription and subscription.plan:
        plan_name = subscription.plan.name.lower()
        if "pro" in plan_name or "firm" in plan_name or "enterprise" in plan_name:
            return {
                "has_access": True,
                "access_type": "subscription",
                "subscription_tier": plan_name
            }

    return {
        "has_access": False,
        "message": "No access to this case",
        "purchase_options": [
            {
                "type": "one_time",
                "price": 5.00,
                "description": "Monitor this case until it closes"
            },
            {
                "type": "monthly",
                "price": 19.00,
                "description": "Monitor unlimited cases for 30 days"
            },
            {
                "type": "subscription_pro",
                "price": 49.00,
                "description": "Pro plan with unlimited case monitoring + AI features"
            }
        ]
    }


@router.post("/{case_access_id}/cancel")
async def cancel_case_access(
    case_access_id: int,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db)
):
    """Cancel case access"""
    case_access = db.query(CaseAccess).filter(
        CaseAccess.id == case_access_id,
        CaseAccess.user_id == user.id
    ).first()

    if not case_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case access not found"
        )

    case_access.cancel(reason="Cancelled by user")
    db.commit()

    return {"message": "Case access cancelled successfully"}


@router.put("/{case_access_id}/notifications")
async def update_notification_settings(
    case_access_id: int,
    enabled: bool,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db)
):
    """Update notification settings for a case"""
    case_access = db.query(CaseAccess).filter(
        CaseAccess.id == case_access_id,
        CaseAccess.user_id == user.id
    ).first()

    if not case_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case access not found"
        )

    case_access.notifications_enabled = enabled
    db.commit()

    return {"message": f"Notifications {'enabled' if enabled else 'disabled'}"}
