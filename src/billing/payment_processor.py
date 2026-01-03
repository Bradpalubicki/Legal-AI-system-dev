"""
Payment Processing Service

Comprehensive payment processing system with multiple payment methods,
fraud detection, and automated reconciliation for legal billing.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
import asyncio
import logging
import json
import uuid
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field, validator

from .advanced_models import (
    Payment, Invoice, TrustAccount, PaymentMethod, BillingMatter,
    PaymentStatus, PaymentType, TransactionType, AuditLog,
    PaymentGateway, RefundRequest, PaymentSchedule, RecurringPayment
)
from ..core.database import get_db_session
from ..core.security import get_current_user_id


logger = logging.getLogger(__name__)


class PaymentMethodType(str, Enum):
    """Supported payment method types."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    WIRE_TRANSFER = "wire_transfer"
    CHECK = "check"
    TRUST_ACCOUNT = "trust_account"
    CRYPTOCURRENCY = "cryptocurrency"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class PaymentRequest(BaseModel):
    """Request model for payment processing."""
    invoice_id: int
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    payment_method_type: PaymentMethodType
    payment_method_id: Optional[int] = None
    payment_source: Dict[str, Any] = Field(default_factory=dict)
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    process_immediately: bool = True
    scheduled_date: Optional[datetime] = None
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Payment amount must be positive')
        return v


class RefundRequest(BaseModel):
    """Request model for payment refunds."""
    payment_id: int
    refund_amount: Optional[Decimal] = None  # Full refund if not specified
    reason: str = Field(..., min_length=10, max_length=500)
    refund_method: Optional[str] = None  # Same as original if not specified
    notes: Optional[str] = None


class PaymentMethodRequest(BaseModel):
    """Request model for adding payment methods."""
    method_type: PaymentMethodType
    method_name: str = Field(..., min_length=3, max_length=100)
    is_default: bool = False
    billing_address: Dict[str, str] = Field(default_factory=dict)
    
    # Credit/Debit Card fields
    card_number: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    cvv: Optional[str] = None
    cardholder_name: Optional[str] = None
    
    # ACH fields
    routing_number: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None  # checking, savings
    bank_name: Optional[str] = None
    
    # Other payment method specific data
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class PaymentResult(BaseModel):
    """Result of payment processing."""
    success: bool
    payment_id: Optional[int] = None
    transaction_id: Optional[str] = None
    status: str
    message: str
    gateway_response: Dict[str, Any] = Field(default_factory=dict)
    fraud_score: Optional[float] = None
    requires_3ds: bool = False
    redirect_url: Optional[str] = None


class PaymentSummary(BaseModel):
    """Payment summary statistics."""
    total_payments: int
    total_amount: Decimal
    successful_payments: int
    failed_payments: int
    pending_payments: int
    refunded_amount: Decimal
    average_payment: Decimal
    payment_methods_breakdown: Dict[str, int]


class PaymentProcessor:
    """
    Advanced payment processing service with multiple gateway support and fraud detection.
    """
    
    def __init__(self):
        self.fraud_detection_enabled = True
        self.max_retry_attempts = 3
        self.supported_gateways = {
            'stripe': self._process_stripe_payment,
            'square': self._process_square_payment,
            'authorize_net': self._process_authorize_net_payment,
            'paypal': self._process_paypal_payment,
            'trust_account': self._process_trust_account_payment
        }
        
    async def process_payment(
        self,
        user_id: int,
        payment_request: PaymentRequest,
        db: Optional[AsyncSession] = None
    ) -> PaymentResult:
        """Process payment with fraud detection and multiple gateway support."""
        if not db:
            async with get_db_session() as db:
                return await self._process_payment_impl(user_id, payment_request, db)
        return await self._process_payment_impl(user_id, payment_request, db)
    
    async def _process_payment_impl(
        self,
        user_id: int,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> PaymentResult:
        """Implementation of payment processing."""
        # Validate invoice exists and is payable
        invoice_query = select(Invoice).options(
            joinedload(Invoice.matter)
        ).where(Invoice.id == payment_request.invoice_id)
        
        result = await db.execute(invoice_query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return PaymentResult(
                success=False,
                status="failed",
                message="Invoice not found"
            )
            
        if invoice.status not in ["finalized", "sent"]:
            return PaymentResult(
                success=False,
                status="failed",
                message="Invoice is not in a payable state"
            )
            
        # Validate payment amount
        outstanding_amount = invoice.total_amount - (invoice.paid_amount or Decimal('0'))
        if payment_request.amount > outstanding_amount:
            return PaymentResult(
                success=False,
                status="failed",
                message=f"Payment amount ${payment_request.amount} exceeds outstanding balance ${outstanding_amount}"
            )
            
        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Create payment record
        payment = Payment(
            invoice_id=payment_request.invoice_id,
            matter_id=invoice.matter_id,
            amount=payment_request.amount,
            payment_method=payment_request.payment_method_type,
            payment_method_id=payment_request.payment_method_id,
            transaction_id=transaction_id,
            reference_number=payment_request.reference_number or transaction_id[:12],
            payment_date=datetime.utcnow() if payment_request.process_immediately else payment_request.scheduled_date,
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.INVOICE_PAYMENT,
            notes=payment_request.notes,
            created_by=user_id,
            payment_source=payment_request.payment_source
        )
        
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        
        try:
            # Fraud detection
            if self.fraud_detection_enabled:
                fraud_result = await self._perform_fraud_check(payment, payment_request, db)
                if fraud_result['high_risk']:
                    payment.status = PaymentStatus.FLAGGED
                    payment.fraud_score = fraud_result['score']
                    await db.commit()
                    
                    return PaymentResult(
                        success=False,
                        status="flagged",
                        message="Payment flagged for manual review",
                        payment_id=payment.id,
                        fraud_score=fraud_result['score']
                    )
                    
            # Process payment based on method type
            if payment_request.process_immediately:
                gateway_result = await self._process_with_gateway(
                    payment, payment_request, db
                )
                
                if gateway_result['success']:
                    payment.status = PaymentStatus.COMPLETED
                    payment.gateway_transaction_id = gateway_result.get('gateway_transaction_id')
                    payment.gateway_response = gateway_result.get('response', {})
                    payment.processed_at = datetime.utcnow()
                    
                    # Update invoice paid amount
                    invoice.paid_amount = (invoice.paid_amount or Decimal('0')) + payment.amount
                    if invoice.paid_amount >= invoice.total_amount:
                        invoice.status = "paid"
                        invoice.paid_date = datetime.utcnow()
                        
                    await db.commit()
                    
                    # Create audit log
                    await self._create_audit_log(
                        user_id,
                        f"Payment processed successfully",
                        {
                            'payment_id': payment.id,
                            'amount': str(payment.amount),
                            'invoice_id': invoice.id,
                            'method': payment_request.payment_method_type
                        },
                        db
                    )
                    
                    return PaymentResult(
                        success=True,
                        payment_id=payment.id,
                        transaction_id=transaction_id,
                        status="completed",
                        message="Payment processed successfully",
                        gateway_response=gateway_result.get('response', {})
                    )
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.failure_reason = gateway_result.get('error', 'Payment processing failed')
                    payment.gateway_response = gateway_result.get('response', {})
                    await db.commit()
                    
                    return PaymentResult(
                        success=False,
                        payment_id=payment.id,
                        status="failed",
                        message=gateway_result.get('error', 'Payment processing failed'),
                        gateway_response=gateway_result.get('response', {})
                    )
            else:
                # Schedule payment for later
                payment.status = PaymentStatus.SCHEDULED
                await db.commit()
                
                return PaymentResult(
                    success=True,
                    payment_id=payment.id,
                    transaction_id=transaction_id,
                    status="scheduled",
                    message=f"Payment scheduled for {payment_request.scheduled_date}"
                )
                
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            await db.commit()
            
            return PaymentResult(
                success=False,
                payment_id=payment.id,
                status="failed",
                message=f"Payment processing error: {str(e)}"
            )
    
    async def _perform_fraud_check(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Perform fraud detection checks."""
        fraud_score = 0.0
        risk_factors = []
        
        # Check payment velocity (too many payments in short time)
        velocity_check = await self._check_payment_velocity(payment.created_by, db)
        if velocity_check['high_velocity']:
            fraud_score += 0.3
            risk_factors.append("High payment velocity")
            
        # Check unusual payment amount
        if payment.amount > Decimal('10000'):
            fraud_score += 0.2
            risk_factors.append("High payment amount")
            
        # Check payment method consistency
        method_check = await self._check_payment_method_consistency(
            payment.created_by, payment_request.payment_method_type, db
        )
        if method_check['new_method']:
            fraud_score += 0.1
            risk_factors.append("New payment method")
            
        # Check geolocation (would require IP geolocation service)
        # For now, mock this check
        geo_risk = 0.0  # Would be calculated from IP
        fraud_score += geo_risk
        
        # Machine learning model would provide better scoring in production
        
        return {
            'score': fraud_score,
            'high_risk': fraud_score > 0.5,
            'risk_factors': risk_factors
        }
    
    async def _check_payment_velocity(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check if user is making too many payments in a short time."""
        # Count payments in last hour
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        velocity_query = select(func.count(Payment.id)).where(
            and_(
                Payment.created_by == user_id,
                Payment.created_at >= hour_ago
            )
        )
        
        result = await db.execute(velocity_query)
        recent_payments = result.scalar() or 0
        
        return {
            'high_velocity': recent_payments > 5,
            'payment_count': recent_payments
        }
    
    async def _check_payment_method_consistency(
        self,
        user_id: int,
        method_type: PaymentMethodType,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check if payment method is consistent with user's history."""
        # Get user's payment method history
        history_query = select(Payment.payment_method).where(
            and_(
                Payment.created_by == user_id,
                Payment.status == PaymentStatus.COMPLETED
            )
        ).distinct()
        
        result = await db.execute(history_query)
        used_methods = [row[0] for row in result.fetchall()]
        
        return {
            'new_method': str(method_type) not in used_methods,
            'used_methods': used_methods
        }
    
    async def _process_with_gateway(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process payment with appropriate gateway."""
        method_type = payment_request.payment_method_type
        
        if method_type == PaymentMethodType.TRUST_ACCOUNT:
            return await self._process_trust_account_payment(payment, payment_request, db)
        elif method_type == PaymentMethodType.CHECK:
            return await self._process_check_payment(payment, payment_request, db)
        elif method_type in [PaymentMethodType.CREDIT_CARD, PaymentMethodType.DEBIT_CARD]:
            return await self._process_card_payment(payment, payment_request, db)
        elif method_type == PaymentMethodType.ACH:
            return await self._process_ach_payment(payment, payment_request, db)
        elif method_type == PaymentMethodType.WIRE_TRANSFER:
            return await self._process_wire_transfer(payment, payment_request, db)
        elif method_type == PaymentMethodType.PAYPAL:
            return await self._process_paypal_payment(payment, payment_request, db)
        elif method_type in [PaymentMethodType.APPLE_PAY, PaymentMethodType.GOOGLE_PAY]:
            return await self._process_digital_wallet(payment, payment_request, db)
        elif method_type == PaymentMethodType.CRYPTOCURRENCY:
            return await self._process_cryptocurrency_payment(payment, payment_request, db)
        else:
            return {
                'success': False,
                'error': f'Unsupported payment method: {method_type}'
            }
    
    async def _process_trust_account_payment(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process payment from client trust account."""
        # Get client's trust account
        trust_query = select(TrustAccount).where(
            and_(
                TrustAccount.matter_id == payment.matter_id,
                TrustAccount.is_active == True
            )
        )
        
        result = await db.execute(trust_query)
        trust_account = result.scalar_one_or_none()
        
        if not trust_account:
            return {
                'success': False,
                'error': 'Trust account not found for this matter'
            }
            
        if trust_account.available_balance < payment.amount:
            return {
                'success': False,
                'error': f'Insufficient trust account balance. Available: ${trust_account.available_balance}, Required: ${payment.amount}'
            }
            
        # Deduct from trust account
        trust_account.available_balance -= payment.amount
        
        # Create trust account transaction record
        trust_transaction = {
            'transaction_type': 'debit',
            'amount': payment.amount,
            'description': f'Payment for invoice {payment.invoice_id}',
            'balance_after': trust_account.available_balance
        }
        
        # Add to transaction history
        if not trust_account.transaction_history:
            trust_account.transaction_history = []
        trust_account.transaction_history.append(trust_transaction)
        
        await db.commit()
        
        return {
            'success': True,
            'gateway_transaction_id': f'TRUST-{payment.transaction_id}',
            'response': {
                'trust_account_id': trust_account.id,
                'remaining_balance': str(trust_account.available_balance)
            }
        }
    
    async def _process_card_payment(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process credit/debit card payment via Stripe."""
        # In production, this would integrate with Stripe API
        try:
            # Mock Stripe integration
            card_data = payment_request.payment_source
            
            # Validate card data
            if not all(k in card_data for k in ['number', 'exp_month', 'exp_year', 'cvc']):
                return {
                    'success': False,
                    'error': 'Missing required card information'
                }
                
            # Simulate card processing
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock successful response (90% success rate)
            import random
            if random.random() < 0.9:
                gateway_transaction_id = f'ch_{uuid.uuid4().hex[:24]}'
                return {
                    'success': True,
                    'gateway_transaction_id': gateway_transaction_id,
                    'response': {
                        'id': gateway_transaction_id,
                        'amount': int(payment.amount * 100),  # Stripe uses cents
                        'currency': 'usd',
                        'status': 'succeeded',
                        'last4': card_data.get('number', '0000')[-4:],
                        'brand': self._detect_card_brand(card_data.get('number', ''))
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Card declined',
                    'response': {
                        'decline_code': 'generic_decline',
                        'message': 'Your card was declined.'
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Card processing error: {str(e)}'
            }
    
    async def _process_ach_payment(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process ACH bank transfer."""
        # ACH payments typically take 1-3 business days
        try:
            ach_data = payment_request.payment_source
            
            # Validate ACH data
            required_fields = ['routing_number', 'account_number', 'account_type']
            if not all(k in ach_data for k in required_fields):
                return {
                    'success': False,
                    'error': 'Missing required ACH information'
                }
                
            # Mock ACH processing
            await asyncio.sleep(0.1)
            
            gateway_transaction_id = f'ach_{uuid.uuid4().hex[:24]}'
            return {
                'success': True,
                'gateway_transaction_id': gateway_transaction_id,
                'response': {
                    'id': gateway_transaction_id,
                    'amount': int(payment.amount * 100),
                    'status': 'pending',  # ACH starts as pending
                    'bank_name': ach_data.get('bank_name', 'Unknown Bank'),
                    'last4': ach_data.get('account_number', '0000')[-4:],
                    'expected_settlement': (datetime.utcnow() + timedelta(days=2)).isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'ACH processing error: {str(e)}'
            }
    
    async def _process_wire_transfer(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process wire transfer payment."""
        # Wire transfers are typically processed manually
        try:
            wire_data = payment_request.payment_source
            
            gateway_transaction_id = f'wire_{uuid.uuid4().hex[:24]}'
            return {
                'success': True,
                'gateway_transaction_id': gateway_transaction_id,
                'response': {
                    'id': gateway_transaction_id,
                    'amount': int(payment.amount * 100),
                    'status': 'pending_confirmation',
                    'wire_instructions': {
                        'routing_number': '021000021',  # Example routing number
                        'account_number': '1234567890',
                        'account_name': 'Legal Firm Trust Account',
                        'reference': payment.reference_number
                    }
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Wire transfer processing error: {str(e)}'
            }
    
    async def _process_check_payment(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process check payment."""
        # Check payments are recorded but require manual verification
        try:
            check_data = payment_request.payment_source
            
            gateway_transaction_id = f'check_{uuid.uuid4().hex[:24]}'
            return {
                'success': True,
                'gateway_transaction_id': gateway_transaction_id,
                'response': {
                    'id': gateway_transaction_id,
                    'amount': int(payment.amount * 100),
                    'status': 'pending_verification',
                    'check_number': check_data.get('check_number'),
                    'routing_number': check_data.get('routing_number'),
                    'account_number': check_data.get('account_number'),
                    'requires_manual_verification': True
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Check processing error: {str(e)}'
            }
    
    async def _process_paypal_payment(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process PayPal payment."""
        try:
            paypal_data = payment_request.payment_source
            
            # Mock PayPal integration
            await asyncio.sleep(0.1)
            
            import random
            if random.random() < 0.95:  # 95% success rate for PayPal
                gateway_transaction_id = f'PAY-{uuid.uuid4().hex[:17].upper()}'
                return {
                    'success': True,
                    'gateway_transaction_id': gateway_transaction_id,
                    'response': {
                        'id': gateway_transaction_id,
                        'amount': str(payment.amount),
                        'currency': 'USD',
                        'status': 'COMPLETED',
                        'payer_email': paypal_data.get('payer_email', 'hidden@paypal.com')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'PayPal payment failed',
                    'response': {
                        'error': 'PAYMENT_DENIED',
                        'message': 'Payment could not be processed at this time'
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'PayPal processing error: {str(e)}'
            }
    
    async def _process_digital_wallet(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process Apple Pay or Google Pay payment."""
        try:
            wallet_data = payment_request.payment_source
            wallet_type = payment_request.payment_method_type
            
            # Mock digital wallet processing
            await asyncio.sleep(0.1)
            
            gateway_transaction_id = f'{wallet_type.value}_{uuid.uuid4().hex[:20]}'
            return {
                'success': True,
                'gateway_transaction_id': gateway_transaction_id,
                'response': {
                    'id': gateway_transaction_id,
                    'amount': int(payment.amount * 100),
                    'currency': 'usd',
                    'status': 'succeeded',
                    'wallet_type': wallet_type.value,
                    'device_id': wallet_data.get('device_id', 'unknown')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Digital wallet processing error: {str(e)}'
            }
    
    async def _process_cryptocurrency_payment(
        self,
        payment: Payment,
        payment_request: PaymentRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process cryptocurrency payment."""
        try:
            crypto_data = payment_request.payment_source
            
            # Mock cryptocurrency processing
            gateway_transaction_id = f'crypto_{uuid.uuid4().hex[:32]}'
            return {
                'success': True,
                'gateway_transaction_id': gateway_transaction_id,
                'response': {
                    'id': gateway_transaction_id,
                    'amount': str(payment.amount),
                    'currency': 'USD',
                    'crypto_currency': crypto_data.get('currency', 'BTC'),
                    'crypto_amount': crypto_data.get('crypto_amount', '0.001'),
                    'wallet_address': crypto_data.get('wallet_address'),
                    'status': 'pending_confirmation',
                    'confirmations_required': 3
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Cryptocurrency processing error: {str(e)}'
            }
    
    def _detect_card_brand(self, card_number: str) -> str:
        """Detect credit card brand from card number."""
        card_number = card_number.replace(' ', '').replace('-', '')
        
        if card_number.startswith('4'):
            return 'visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'mastercard'
        elif card_number.startswith(('34', '37')):
            return 'amex'
        elif card_number.startswith('6'):
            return 'discover'
        else:
            return 'unknown'
    
    async def process_refund(
        self,
        user_id: int,
        refund_request: RefundRequest,
        db: Optional[AsyncSession] = None
    ) -> PaymentResult:
        """Process payment refund."""
        if not db:
            async with get_db_session() as db:
                return await self._process_refund_impl(user_id, refund_request, db)
        return await self._process_refund_impl(user_id, refund_request, db)
    
    async def _process_refund_impl(
        self,
        user_id: int,
        refund_request: RefundRequest,
        db: AsyncSession
    ) -> PaymentResult:
        """Implementation of refund processing."""
        # Get original payment
        payment_query = select(Payment).where(Payment.id == refund_request.payment_id)
        result = await db.execute(payment_query)
        original_payment = result.scalar_one_or_none()
        
        if not original_payment:
            return PaymentResult(
                success=False,
                status="failed",
                message="Original payment not found"
            )
            
        if original_payment.status != PaymentStatus.COMPLETED:
            return PaymentResult(
                success=False,
                status="failed",
                message="Can only refund completed payments"
            )
            
        # Calculate refund amount
        refund_amount = refund_request.refund_amount or original_payment.amount
        
        # Check refund limits
        total_refunded = original_payment.refunded_amount or Decimal('0')
        if total_refunded + refund_amount > original_payment.amount:
            return PaymentResult(
                success=False,
                status="failed",
                message=f"Refund amount exceeds remaining refundable amount"
            )
            
        # Create refund payment record
        refund_payment = Payment(
            invoice_id=original_payment.invoice_id,
            matter_id=original_payment.matter_id,
            amount=-refund_amount,  # Negative amount for refund
            payment_method=original_payment.payment_method,
            transaction_id=str(uuid.uuid4()),
            reference_number=f"REF-{original_payment.reference_number}",
            payment_date=datetime.utcnow(),
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.REFUND,
            notes=f"Refund: {refund_request.reason}",
            related_payment_id=original_payment.id,
            created_by=user_id
        )
        
        db.add(refund_payment)
        await db.commit()
        await db.refresh(refund_payment)
        
        try:
            # Process refund with gateway
            gateway_result = await self._process_gateway_refund(
                original_payment, refund_amount, refund_request.reason
            )
            
            if gateway_result['success']:
                refund_payment.status = PaymentStatus.COMPLETED
                refund_payment.gateway_transaction_id = gateway_result.get('refund_transaction_id')
                refund_payment.processed_at = datetime.utcnow()
                
                # Update original payment refund tracking
                original_payment.refunded_amount = total_refunded + refund_amount
                
                # Update invoice if necessary
                invoice_query = select(Invoice).where(Invoice.id == original_payment.invoice_id)
                invoice_result = await db.execute(invoice_query)
                invoice = invoice_result.scalar_one()
                
                invoice.paid_amount = (invoice.paid_amount or Decimal('0')) - refund_amount
                if invoice.status == "paid" and invoice.paid_amount < invoice.total_amount:
                    invoice.status = "partially_paid"
                    
                await db.commit()
                
                return PaymentResult(
                    success=True,
                    payment_id=refund_payment.id,
                    transaction_id=refund_payment.transaction_id,
                    status="completed",
                    message="Refund processed successfully"
                )
            else:
                refund_payment.status = PaymentStatus.FAILED
                refund_payment.failure_reason = gateway_result.get('error')
                await db.commit()
                
                return PaymentResult(
                    success=False,
                    status="failed",
                    message=gateway_result.get('error', 'Refund processing failed')
                )
                
        except Exception as e:
            refund_payment.status = PaymentStatus.FAILED
            refund_payment.failure_reason = str(e)
            await db.commit()
            
            return PaymentResult(
                success=False,
                status="failed",
                message=f"Refund processing error: {str(e)}"
            )
    
    async def _process_gateway_refund(
        self,
        original_payment: Payment,
        refund_amount: Decimal,
        reason: str
    ) -> Dict[str, Any]:
        """Process refund with payment gateway."""
        # Mock gateway refund processing
        try:
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Most refunds should succeed
            import random
            if random.random() < 0.95:
                return {
                    'success': True,
                    'refund_transaction_id': f'rf_{uuid.uuid4().hex[:24]}',
                    'amount': str(refund_amount),
                    'reason': reason
                }
            else:
                return {
                    'success': False,
                    'error': 'Gateway refund failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_payment_summary(
        self,
        matter_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Optional[AsyncSession] = None
    ) -> PaymentSummary:
        """Get payment summary statistics."""
        if not db:
            async with get_db_session() as db:
                return await self._get_payment_summary_impl(matter_id, start_date, end_date, db)
        return await self._get_payment_summary_impl(matter_id, start_date, end_date, db)
    
    async def _get_payment_summary_impl(
        self,
        matter_id: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: AsyncSession
    ) -> PaymentSummary:
        """Implementation of payment summary."""
        # Build query conditions
        conditions = []
        
        if matter_id:
            conditions.append(Payment.matter_id == matter_id)
        if start_date:
            conditions.append(Payment.payment_date >= start_date)
        if end_date:
            conditions.append(Payment.payment_date <= end_date)
            
        base_conditions = and_(*conditions) if conditions else None
        
        # Get summary statistics
        summary_query = select(
            func.count(Payment.id).label('total_payments'),
            func.sum(func.abs(Payment.amount)).label('total_amount'),
            func.count(func.case((Payment.status == PaymentStatus.COMPLETED, 1))).label('successful_payments'),
            func.count(func.case((Payment.status == PaymentStatus.FAILED, 1))).label('failed_payments'),
            func.count(func.case((Payment.status == PaymentStatus.PENDING, 1))).label('pending_payments'),
            func.sum(func.case((Payment.amount < 0, func.abs(Payment.amount)), else_=0)).label('refunded_amount'),
            func.avg(func.abs(Payment.amount)).label('avg_payment')
        )
        
        if base_conditions is not None:
            summary_query = summary_query.where(base_conditions)
            
        result = await db.execute(summary_query)
        row = result.first()
        
        # Get payment methods breakdown
        methods_query = select(
            Payment.payment_method,
            func.count(Payment.id).label('count')
        ).group_by(Payment.payment_method)
        
        if base_conditions is not None:
            methods_query = methods_query.where(base_conditions)
            
        methods_result = await db.execute(methods_query)
        methods_breakdown = {method: count for method, count in methods_result.fetchall()}
        
        return PaymentSummary(
            total_payments=row.total_payments or 0,
            total_amount=row.total_amount or Decimal('0'),
            successful_payments=row.successful_payments or 0,
            failed_payments=row.failed_payments or 0,
            pending_payments=row.pending_payments or 0,
            refunded_amount=row.refunded_amount or Decimal('0'),
            average_payment=row.avg_payment or Decimal('0'),
            payment_methods_breakdown=methods_breakdown
        )
    
    async def _create_audit_log(
        self,
        user_id: int,
        action: str,
        details: Dict[str, Any],
        db: AsyncSession
    ):
        """Create audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address="127.0.0.1",  # Should be passed from request
            user_agent="PaymentProcessor"  # Should be passed from request
        )
        db.add(audit_log)
        await db.commit()