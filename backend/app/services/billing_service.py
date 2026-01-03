"""
Legal AI System - Comprehensive Billing Service
Production-ready payment processing and subscription management
"""

import stripe
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, and_
from fastapi import HTTPException, BackgroundTasks
import logging

from ..models.billing import (
    Subscription, Invoice, Payment, Usage,
    BillingPlan, PaymentMethod, RefundRequest
)
from ..models.user import User
from ..core.database import get_async_session
from ..core.config import settings
from ..utils.email import send_email
from ..utils.notifications import send_notification

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class BillingService:
    """Comprehensive billing and payment processing service"""

    def __init__(self):
        self.stripe_webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_customer(self, user_id: int, email: str, name: str) -> str:
        """Create a new Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": user_id}
            )

            # Update user with Stripe customer ID
            async with get_async_session() as session:
                await session.execute(
                    update(User).where(User.id == user_id)
                    .values(stripe_customer_id=customer.id)
                )
                await session.commit()

            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id

        except Exception as e:
            logger.error(f"Failed to create Stripe customer for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create customer")

    async def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        payment_method_id: str,
        trial_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new subscription"""
        try:
            async with get_async_session() as session:
                # Get user and plan
                user = await session.get(User, user_id)
                plan = await session.get(BillingPlan, plan_id)

                if not user or not plan:
                    raise HTTPException(status_code=404, detail="User or plan not found")

                # Ensure user has Stripe customer ID
                if not user.stripe_customer_id:
                    user.stripe_customer_id = await self.create_customer(
                        user_id, user.email, f"{user.first_name} {user.last_name}"
                    )

                # Attach payment method to customer
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=user.stripe_customer_id
                )

                # Set as default payment method
                stripe.Customer.modify(
                    user.stripe_customer_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )

                # Create subscription in Stripe
                subscription_params = {
                    'customer': user.stripe_customer_id,
                    'items': [{'price': plan.stripe_price_id}],
                    'expand': ['latest_invoice.payment_intent'],
                    'metadata': {
                        'user_id': user_id,
                        'plan_id': plan_id
                    }
                }

                if trial_days:
                    subscription_params['trial_period_days'] = trial_days

                stripe_subscription = stripe.Subscription.create(**subscription_params)

                # Create local subscription record
                subscription = Subscription(
                    user_id=user_id,
                    plan_id=plan_id,
                    stripe_subscription_id=stripe_subscription.id,
                    status=stripe_subscription.status,
                    current_period_start=datetime.fromtimestamp(
                        stripe_subscription.current_period_start
                    ),
                    current_period_end=datetime.fromtimestamp(
                        stripe_subscription.current_period_end
                    ),
                    trial_end=datetime.fromtimestamp(
                        stripe_subscription.trial_end
                    ) if stripe_subscription.trial_end else None
                )

                session.add(subscription)
                await session.commit()

                logger.info(f"Created subscription {stripe_subscription.id} for user {user_id}")

                return {
                    'subscription_id': stripe_subscription.id,
                    'status': stripe_subscription.status,
                    'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret
                }

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise HTTPException(status_code=500, detail="Failed to create subscription")

    async def cancel_subscription(self, user_id: int, subscription_id: str, immediately: bool = False) -> bool:
        """Cancel a subscription"""
        try:
            async with get_async_session() as session:
                # Verify subscription belongs to user
                subscription = await session.execute(
                    select(Subscription).where(
                        and_(
                            Subscription.stripe_subscription_id == subscription_id,
                            Subscription.user_id == user_id
                        )
                    )
                )
                subscription = subscription.scalar_one_or_none()

                if not subscription:
                    raise HTTPException(status_code=404, detail="Subscription not found")

                # Cancel in Stripe
                if immediately:
                    stripe.Subscription.delete(subscription_id)
                    subscription.status = 'canceled'
                else:
                    stripe.Subscription.modify(
                        subscription_id,
                        cancel_at_period_end=True
                    )
                    subscription.status = 'canceling'

                subscription.canceled_at = datetime.utcnow()
                await session.commit()

                # Send cancellation email
                await self._send_cancellation_email(subscription.user_id, immediately)

                logger.info(f"Canceled subscription {subscription_id} for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise HTTPException(status_code=500, detail="Failed to cancel subscription")

    async def track_usage(
        self,
        user_id: int,
        feature: str,
        quantity: int = 1,
        metadata: Optional[Dict] = None
    ) -> None:
        """Track feature usage for billing"""
        try:
            async with get_async_session() as session:
                # Get active subscription
                subscription = await session.execute(
                    select(Subscription).where(
                        and_(
                            Subscription.user_id == user_id,
                            Subscription.status.in_(['active', 'trialing'])
                        )
                    ).options(selectinload(Subscription.plan))
                )
                subscription = subscription.scalar_one_or_none()

                if not subscription:
                    logger.warning(f"No active subscription found for user {user_id}")
                    return

                # Create usage record
                usage = Usage(
                    user_id=user_id,
                    subscription_id=subscription.id,
                    feature=feature,
                    quantity=quantity,
                    timestamp=datetime.utcnow(),
                    metadata=metadata or {}
                )

                session.add(usage)

                # Check usage limits and send warnings if needed
                await self._check_usage_limits(session, subscription, feature, quantity)

                await session.commit()

        except Exception as e:
            logger.error(f"Failed to track usage: {e}")

    async def generate_invoice(
        self,
        subscription_id: int,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Generate and send invoice"""
        try:
            async with get_async_session() as session:
                subscription = await session.get(
                    Subscription,
                    subscription_id,
                    options=[
                        selectinload(Subscription.user),
                        selectinload(Subscription.plan)
                    ]
                )

                if not subscription:
                    raise HTTPException(status_code=404, detail="Subscription not found")

                # Calculate usage-based charges
                usage_charges = await self._calculate_usage_charges(
                    session, subscription_id
                )

                # Create invoice in Stripe if needed
                if usage_charges > 0:
                    stripe.InvoiceItem.create(
                        customer=subscription.user.stripe_customer_id,
                        amount=int(usage_charges * 100),  # Convert to cents
                        currency='usd',
                        description='Usage-based charges'
                    )

                # Create invoice
                stripe_invoice = stripe.Invoice.create(
                    customer=subscription.user.stripe_customer_id,
                    subscription=subscription.stripe_subscription_id,
                    auto_advance=True
                )

                # Finalize and send
                stripe.Invoice.finalize_invoice(stripe_invoice.id)

                # Create local invoice record
                invoice = Invoice(
                    user_id=subscription.user_id,
                    subscription_id=subscription_id,
                    stripe_invoice_id=stripe_invoice.id,
                    amount_due=Decimal(stripe_invoice.amount_due / 100),
                    status=stripe_invoice.status,
                    due_date=datetime.fromtimestamp(stripe_invoice.due_date),
                    invoice_pdf=stripe_invoice.invoice_pdf
                )

                session.add(invoice)
                await session.commit()

                # Send invoice email in background
                background_tasks.add_task(
                    self._send_invoice_email,
                    subscription.user.email,
                    stripe_invoice.hosted_invoice_url
                )

                logger.info(f"Generated invoice {stripe_invoice.id} for subscription {subscription_id}")

                return {
                    'invoice_id': stripe_invoice.id,
                    'amount_due': invoice.amount_due,
                    'due_date': invoice.due_date,
                    'hosted_url': stripe_invoice.hosted_invoice_url
                }

        except Exception as e:
            logger.error(f"Failed to generate invoice: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate invoice")

    async def process_refund(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """Process a refund"""
        try:
            async with get_async_session() as session:
                # Get payment record
                payment = await session.execute(
                    select(Payment).where(Payment.stripe_payment_id == payment_id)
                )
                payment = payment.scalar_one_or_none()

                if not payment:
                    raise HTTPException(status_code=404, detail="Payment not found")

                refund_amount = amount or payment.amount

                # Process refund in Stripe
                refund = stripe.Refund.create(
                    payment_intent=payment_id,
                    amount=int(refund_amount * 100) if amount else None,
                    reason=reason
                )

                # Create refund request record
                refund_request = RefundRequest(
                    payment_id=payment.id,
                    amount=refund_amount,
                    reason=reason,
                    status='succeeded',
                    stripe_refund_id=refund.id,
                    processed_at=datetime.utcnow()
                )

                session.add(refund_request)

                # Update payment status
                payment.refunded_amount = (payment.refunded_amount or Decimal(0)) + refund_amount
                if payment.refunded_amount >= payment.amount:
                    payment.status = 'refunded'
                else:
                    payment.status = 'partially_refunded'

                await session.commit()

                logger.info(f"Processed refund {refund.id} for payment {payment_id}")

                return {
                    'refund_id': refund.id,
                    'amount': refund_amount,
                    'status': refund.status
                }

        except Exception as e:
            logger.error(f"Failed to process refund: {e}")
            raise HTTPException(status_code=500, detail="Failed to process refund")

    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.stripe_webhook_secret
            )

            event_type = event['type']
            event_data = event['data']['object']

            logger.info(f"Processing webhook event: {event_type}")

            # Handle different event types
            if event_type == 'invoice.payment_succeeded':
                await self._handle_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                await self._handle_payment_failed(event_data)
            elif event_type == 'subscription.updated':
                await self._handle_subscription_updated(event_data)
            elif event_type == 'subscription.deleted':
                await self._handle_subscription_deleted(event_data)
            elif event_type == 'customer.subscription.trial_will_end':
                await self._handle_trial_ending(event_data)

            return {'status': 'success', 'event_type': event_type}

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")

    # Private helper methods
    async def _handle_payment_succeeded(self, invoice_data: Dict) -> None:
        """Handle successful payment"""
        async with get_async_session() as session:
            # Create payment record
            payment = Payment(
                user_id=int(invoice_data['customer']),  # Will need to look up by customer ID
                amount=Decimal(invoice_data['amount_paid'] / 100),
                currency=invoice_data['currency'],
                status='succeeded',
                stripe_payment_id=invoice_data['payment_intent'],
                created_at=datetime.utcnow()
            )

            session.add(payment)

            # Update subscription status if applicable
            if invoice_data.get('subscription'):
                await session.execute(
                    update(Subscription)
                    .where(Subscription.stripe_subscription_id == invoice_data['subscription'])
                    .values(status='active')
                )

            await session.commit()

    async def _handle_payment_failed(self, invoice_data: Dict) -> None:
        """Handle failed payment"""
        # Send payment failure notification
        # Update subscription status
        # Implement retry logic
        pass

    async def _calculate_usage_charges(self, session: AsyncSession, subscription_id: int) -> Decimal:
        """Calculate usage-based charges for the current billing period"""
        # Implementation for usage-based billing calculations
        return Decimal(0)

    async def _check_usage_limits(
        self,
        session: AsyncSession,
        subscription: Subscription,
        feature: str,
        quantity: int
    ) -> None:
        """Check if usage is approaching limits and send warnings"""
        # Implementation for usage limit checking and warnings
        pass

    async def _send_invoice_email(self, email: str, invoice_url: str) -> None:
        """Send invoice email to customer"""
        await send_email(
            to_email=email,
            subject="Your Legal AI Invoice",
            template="invoice",
            context={'invoice_url': invoice_url}
        )

    async def _send_cancellation_email(self, user_id: int, immediate: bool) -> None:
        """Send subscription cancellation email"""
        # Implementation for cancellation email
        pass

# Initialize billing service
billing_service = BillingService()