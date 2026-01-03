"""
Recurring Payments Service

Automated recurring payment processing for legal billing including
subscription-based services and installment plans.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import asyncio
import logging
import json
from enum import Enum
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field, validator

from .advanced_models import (
    RecurringPayment, PaymentSchedule, Payment, Invoice, BillingMatter,
    PaymentMethod, PaymentStatus, PaymentType, RecurringStatus, AuditLog
)
from .payment_processor import PaymentProcessor, PaymentRequest, PaymentMethodType
from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class RecurringFrequency(str, Enum):
    """Supported recurring payment frequencies."""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUALLY = "semiannually"
    ANNUALLY = "annually"


class RecurringPaymentCreate(BaseModel):
    """Request model for creating recurring payments."""
    matter_id: int
    payment_method_id: int
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    frequency: RecurringFrequency
    start_date: datetime
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    description: str = Field(..., min_length=10, max_length=500)
    reference_prefix: Optional[str] = None
    
    # Retry configuration
    retry_failed_payments: bool = True
    max_retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_interval_days: int = Field(default=3, ge=1, le=30)
    
    # Notification settings
    notify_before_charge: bool = True
    notification_days: int = Field(default=3, ge=0, le=30)
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('end_date')
    def end_date_after_start(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class RecurringPaymentUpdate(BaseModel):
    """Request model for updating recurring payments."""
    amount: Optional[Decimal] = None
    frequency: Optional[RecurringFrequency] = None
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RecurringPaymentResponse(BaseModel):
    """Response model for recurring payments."""
    id: int
    matter_id: int
    amount: Decimal
    frequency: str
    start_date: datetime
    end_date: Optional[datetime]
    next_payment_date: Optional[datetime]
    status: str
    description: str
    total_payments: int
    successful_payments: int
    failed_payments: int
    total_amount_processed: Decimal
    created_at: datetime
    is_active: bool


class PaymentScheduleResponse(BaseModel):
    """Response model for payment schedules."""
    id: int
    scheduled_date: datetime
    amount: Decimal
    status: str
    payment_id: Optional[int]
    attempt_count: int
    last_attempt_date: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime


class RecurringPaymentManager:
    """
    Advanced recurring payment management with flexible scheduling and retry logic.
    """
    
    def __init__(self):
        self.payment_processor = PaymentProcessor()
        self.frequency_deltas = {
            RecurringFrequency.WEEKLY: timedelta(weeks=1),
            RecurringFrequency.BIWEEKLY: timedelta(weeks=2),
            RecurringFrequency.MONTHLY: relativedelta(months=1),
            RecurringFrequency.QUARTERLY: relativedelta(months=3),
            RecurringFrequency.SEMIANNUALLY: relativedelta(months=6),
            RecurringFrequency.ANNUALLY: relativedelta(years=1)
        }
        
    async def create_recurring_payment(
        self,
        user_id: int,
        recurring_data: RecurringPaymentCreate,
        db: Optional[AsyncSession] = None
    ) -> RecurringPaymentResponse:
        """Create new recurring payment schedule."""
        if not db:
            async with get_db_session() as db:
                return await self._create_recurring_payment_impl(user_id, recurring_data, db)
        return await self._create_recurring_payment_impl(user_id, recurring_data, db)
    
    async def _create_recurring_payment_impl(
        self,
        user_id: int,
        recurring_data: RecurringPaymentCreate,
        db: AsyncSession
    ) -> RecurringPaymentResponse:
        """Implementation of recurring payment creation."""
        # Validate matter access
        matter_query = select(BillingMatter).where(
            and_(
                BillingMatter.id == recurring_data.matter_id,
                BillingMatter.responsible_attorney == user_id
            )
        )
        result = await db.execute(matter_query)
        matter = result.scalar_one_or_none()
        
        if not matter:
            raise ValueError("Matter not found or access denied")
            
        # Validate payment method
        payment_method_query = select(PaymentMethod).where(
            and_(
                PaymentMethod.id == recurring_data.payment_method_id,
                PaymentMethod.user_id == user_id,
                PaymentMethod.is_active == True
            )
        )
        pm_result = await db.execute(payment_method_query)
        payment_method = pm_result.scalar_one_or_none()
        
        if not payment_method:
            raise ValueError("Payment method not found or access denied")
            
        # Create recurring payment
        recurring_payment = RecurringPayment(
            matter_id=recurring_data.matter_id,
            payment_method_id=recurring_data.payment_method_id,
            amount=recurring_data.amount,
            frequency=recurring_data.frequency,
            start_date=recurring_data.start_date,
            end_date=recurring_data.end_date,
            max_occurrences=recurring_data.max_occurrences,
            description=recurring_data.description,
            reference_prefix=recurring_data.reference_prefix or f"REC-{matter.matter_number or matter.id}",
            retry_failed_payments=recurring_data.retry_failed_payments,
            max_retry_attempts=recurring_data.max_retry_attempts,
            retry_interval_days=recurring_data.retry_interval_days,
            notify_before_charge=recurring_data.notify_before_charge,
            notification_days=recurring_data.notification_days,
            status=RecurringStatus.ACTIVE,
            created_by=user_id
        )
        
        db.add(recurring_payment)
        await db.commit()
        await db.refresh(recurring_payment)
        
        # Calculate next payment date
        next_payment_date = await self._calculate_next_payment_date(
            recurring_payment.start_date, recurring_payment.frequency
        )
        recurring_payment.next_payment_date = next_payment_date
        
        # Generate initial payment schedules
        await self._generate_payment_schedules(recurring_payment, db)
        
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Created recurring payment schedule",
            {
                'recurring_payment_id': recurring_payment.id,
                'amount': str(recurring_data.amount),
                'frequency': str(recurring_data.frequency),
                'matter_id': recurring_data.matter_id
            },
            db
        )
        
        logger.info(f"Recurring payment created: {recurring_payment.id} for matter {matter.matter_name}")
        
        return await self._build_recurring_payment_response(recurring_payment, db)
    
    async def _calculate_next_payment_date(
        self,
        current_date: datetime,
        frequency: RecurringFrequency
    ) -> datetime:
        """Calculate next payment date based on frequency."""
        delta = self.frequency_deltas[frequency]
        
        if isinstance(delta, timedelta):
            return current_date + delta
        else:  # relativedelta
            return current_date + delta
    
    async def _generate_payment_schedules(
        self,
        recurring_payment: RecurringPayment,
        db: AsyncSession,
        num_schedules: int = 12  # Generate 12 future schedules
    ):
        """Generate payment schedules for recurring payment."""
        current_date = recurring_payment.start_date
        schedules_created = 0
        
        while schedules_created < num_schedules:
            # Check if we've reached end date or max occurrences
            if recurring_payment.end_date and current_date > recurring_payment.end_date:
                break
                
            if (recurring_payment.max_occurrences and 
                schedules_created >= recurring_payment.max_occurrences):
                break
                
            # Create payment schedule
            schedule = PaymentSchedule(
                recurring_payment_id=recurring_payment.id,
                scheduled_date=current_date,
                amount=recurring_payment.amount,
                status='pending',
                attempt_count=0,
                created_by=recurring_payment.created_by
            )
            
            db.add(schedule)
            schedules_created += 1
            
            # Calculate next date
            current_date = await self._calculate_next_payment_date(
                current_date, recurring_payment.frequency
            )
            
        await db.commit()
        logger.info(f"Generated {schedules_created} payment schedules for recurring payment {recurring_payment.id}")
    
    async def process_due_payments(
        self,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Process all due recurring payments."""
        if not db:
            async with get_db_session() as db:
                return await self._process_due_payments_impl(db)
        return await self._process_due_payments_impl(db)
    
    async def _process_due_payments_impl(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of due payments processing."""
        # Get due payment schedules
        due_date = datetime.utcnow()
        
        due_schedules_query = select(PaymentSchedule).options(
            joinedload(PaymentSchedule.recurring_payment)
        ).where(
            and_(
                PaymentSchedule.scheduled_date <= due_date,
                PaymentSchedule.status == 'pending'
            )
        ).order_by(PaymentSchedule.scheduled_date)
        
        result = await db.execute(due_schedules_query)
        due_schedules = result.scalars().all()
        
        processed = 0
        successful = 0
        failed = 0
        total_amount = Decimal('0')
        
        for schedule in due_schedules:
            try:
                payment_result = await self._process_scheduled_payment(schedule, db)
                processed += 1
                
                if payment_result['success']:
                    successful += 1
                    total_amount += schedule.amount
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error processing scheduled payment {schedule.id}: {str(e)}")
                failed += 1
                
        return {
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'total_amount': total_amount
        }
    
    async def _process_scheduled_payment(
        self,
        schedule: PaymentSchedule,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process individual scheduled payment."""
        recurring_payment = schedule.recurring_payment
        
        # Update attempt count
        schedule.attempt_count += 1
        schedule.last_attempt_date = datetime.utcnow()
        
        try:
            # Create payment request
            payment_request = PaymentRequest(
                invoice_id=0,  # Recurring payments might not be tied to specific invoices
                amount=schedule.amount,
                payment_method_type=PaymentMethodType.CREDIT_CARD,  # Will be determined from payment method
                payment_method_id=recurring_payment.payment_method_id,
                reference_number=f"{recurring_payment.reference_prefix}-{schedule.id}",
                notes=f"Recurring payment: {recurring_payment.description}",
                process_immediately=True
            )
            
            # Process payment
            payment_result = await self.payment_processor.process_payment(
                recurring_payment.created_by, payment_request, db
            )
            
            if payment_result.success:
                # Update schedule status
                schedule.status = 'completed'
                schedule.payment_id = payment_result.payment_id
                
                # Update recurring payment statistics
                recurring_payment.successful_payments += 1
                recurring_payment.total_amount_processed += schedule.amount
                recurring_payment.last_payment_date = datetime.utcnow()
                
                # Update next payment date
                recurring_payment.next_payment_date = await self._calculate_next_payment_date(
                    schedule.scheduled_date, recurring_payment.frequency
                )
                
                await db.commit()
                
                logger.info(f"Processed recurring payment {schedule.id} successfully")
                return {'success': True, 'payment_id': payment_result.payment_id}
                
            else:
                # Handle failure
                schedule.failure_reason = payment_result.message
                recurring_payment.failed_payments += 1
                
                # Check if we should retry
                if (recurring_payment.retry_failed_payments and 
                    schedule.attempt_count < recurring_payment.max_retry_attempts):
                    
                    # Schedule retry
                    retry_date = datetime.utcnow() + timedelta(days=recurring_payment.retry_interval_days)
                    schedule.scheduled_date = retry_date
                    schedule.status = 'retry_pending'
                    
                else:
                    # Max retries reached or retries disabled
                    schedule.status = 'failed'
                    
                    # Check if we should pause the recurring payment
                    recent_failures = await self._count_recent_failures(recurring_payment.id, db)
                    if recent_failures >= 3:
                        recurring_payment.status = RecurringStatus.PAUSED
                        recurring_payment.pause_reason = "Multiple consecutive payment failures"
                        
                await db.commit()
                
                logger.warning(f"Recurring payment {schedule.id} failed: {payment_result.message}")
                return {'success': False, 'error': payment_result.message}
                
        except Exception as e:
            # Handle processing error
            schedule.status = 'error'
            schedule.failure_reason = str(e)
            recurring_payment.failed_payments += 1
            
            await db.commit()
            
            logger.error(f"Error processing recurring payment {schedule.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _count_recent_failures(
        self,
        recurring_payment_id: int,
        db: AsyncSession
    ) -> int:
        """Count recent payment failures for recurring payment."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        query = select(func.count(PaymentSchedule.id)).where(
            and_(
                PaymentSchedule.recurring_payment_id == recurring_payment_id,
                PaymentSchedule.status == 'failed',
                PaymentSchedule.last_attempt_date >= thirty_days_ago
            )
        )
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def update_recurring_payment(
        self,
        recurring_payment_id: int,
        user_id: int,
        updates: RecurringPaymentUpdate,
        db: Optional[AsyncSession] = None
    ) -> RecurringPaymentResponse:
        """Update recurring payment configuration."""
        if not db:
            async with get_db_session() as db:
                return await self._update_recurring_payment_impl(recurring_payment_id, user_id, updates, db)
        return await self._update_recurring_payment_impl(recurring_payment_id, user_id, updates, db)
    
    async def _update_recurring_payment_impl(
        self,
        recurring_payment_id: int,
        user_id: int,
        updates: RecurringPaymentUpdate,
        db: AsyncSession
    ) -> RecurringPaymentResponse:
        """Implementation of recurring payment update."""
        # Get recurring payment
        query = select(RecurringPayment).where(
            and_(
                RecurringPayment.id == recurring_payment_id,
                RecurringPayment.created_by == user_id
            )
        )
        result = await db.execute(query)
        recurring_payment = result.scalar_one_or_none()
        
        if not recurring_payment:
            raise ValueError("Recurring payment not found or access denied")
            
        # Apply updates
        update_dict = updates.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == 'is_active':
                # Handle status change
                if value:
                    recurring_payment.status = RecurringStatus.ACTIVE
                    recurring_payment.pause_reason = None
                else:
                    recurring_payment.status = RecurringStatus.PAUSED
                    recurring_payment.pause_reason = "Manually paused by user"
            else:
                setattr(recurring_payment, field, value)
                
        recurring_payment.updated_at = datetime.utcnow()
        
        # If frequency changed, regenerate schedules
        if 'frequency' in update_dict:
            await self._regenerate_future_schedules(recurring_payment, db)
            
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Updated recurring payment {recurring_payment.id}",
            {
                'recurring_payment_id': recurring_payment.id,
                'updated_fields': list(update_dict.keys())
            },
            db
        )
        
        return await self._build_recurring_payment_response(recurring_payment, db)
    
    async def _regenerate_future_schedules(
        self,
        recurring_payment: RecurringPayment,
        db: AsyncSession
    ):
        """Regenerate future payment schedules after frequency change."""
        # Delete future pending schedules
        future_date = datetime.utcnow()
        
        delete_query = select(PaymentSchedule).where(
            and_(
                PaymentSchedule.recurring_payment_id == recurring_payment.id,
                PaymentSchedule.scheduled_date > future_date,
                PaymentSchedule.status == 'pending'
            )
        )
        
        result = await db.execute(delete_query)
        future_schedules = result.scalars().all()
        
        for schedule in future_schedules:
            await db.delete(schedule)
            
        # Generate new schedules
        await self._generate_payment_schedules(recurring_payment, db)
        
        logger.info(f"Regenerated schedules for recurring payment {recurring_payment.id}")
    
    async def cancel_recurring_payment(
        self,
        recurring_payment_id: int,
        user_id: int,
        reason: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Cancel recurring payment."""
        if not db:
            async with get_db_session() as db:
                return await self._cancel_recurring_payment_impl(recurring_payment_id, user_id, reason, db)
        return await self._cancel_recurring_payment_impl(recurring_payment_id, user_id, reason, db)
    
    async def _cancel_recurring_payment_impl(
        self,
        recurring_payment_id: int,
        user_id: int,
        reason: str,
        db: AsyncSession
    ) -> bool:
        """Implementation of recurring payment cancellation."""
        # Get recurring payment
        query = select(RecurringPayment).where(
            and_(
                RecurringPayment.id == recurring_payment_id,
                RecurringPayment.created_by == user_id
            )
        )
        result = await db.execute(query)
        recurring_payment = result.scalar_one_or_none()
        
        if not recurring_payment:
            raise ValueError("Recurring payment not found or access denied")
            
        # Update status
        recurring_payment.status = RecurringStatus.CANCELLED
        recurring_payment.cancelled_at = datetime.utcnow()
        recurring_payment.cancel_reason = reason
        
        # Cancel all pending schedules
        pending_schedules_query = select(PaymentSchedule).where(
            and_(
                PaymentSchedule.recurring_payment_id == recurring_payment_id,
                PaymentSchedule.status.in_(['pending', 'retry_pending'])
            )
        )
        
        pending_result = await db.execute(pending_schedules_query)
        pending_schedules = pending_result.scalars().all()
        
        for schedule in pending_schedules:
            schedule.status = 'cancelled'
            
        await db.commit()
        
        # Create audit log
        await self._create_audit_log(
            user_id,
            f"Cancelled recurring payment {recurring_payment.id}",
            {
                'recurring_payment_id': recurring_payment.id,
                'reason': reason,
                'cancelled_schedules': len(pending_schedules)
            },
            db
        )
        
        logger.info(f"Recurring payment {recurring_payment_id} cancelled by user {user_id}")
        return True
    
    async def get_recurring_payment(
        self,
        recurring_payment_id: int,
        user_id: int,
        db: Optional[AsyncSession] = None
    ) -> RecurringPaymentResponse:
        """Get recurring payment details."""
        if not db:
            async with get_db_session() as db:
                return await self._get_recurring_payment_impl(recurring_payment_id, user_id, db)
        return await self._get_recurring_payment_impl(recurring_payment_id, user_id, db)
    
    async def _get_recurring_payment_impl(
        self,
        recurring_payment_id: int,
        user_id: int,
        db: AsyncSession
    ) -> RecurringPaymentResponse:
        """Implementation of recurring payment retrieval."""
        query = select(RecurringPayment).where(
            and_(
                RecurringPayment.id == recurring_payment_id,
                RecurringPayment.created_by == user_id
            )
        )
        result = await db.execute(query)
        recurring_payment = result.scalar_one_or_none()
        
        if not recurring_payment:
            raise ValueError("Recurring payment not found or access denied")
            
        return await self._build_recurring_payment_response(recurring_payment, db)
    
    async def _build_recurring_payment_response(
        self,
        recurring_payment: RecurringPayment,
        db: AsyncSession
    ) -> RecurringPaymentResponse:
        """Build recurring payment response."""
        return RecurringPaymentResponse(
            id=recurring_payment.id,
            matter_id=recurring_payment.matter_id,
            amount=recurring_payment.amount,
            frequency=str(recurring_payment.frequency),
            start_date=recurring_payment.start_date,
            end_date=recurring_payment.end_date,
            next_payment_date=recurring_payment.next_payment_date,
            status=str(recurring_payment.status),
            description=recurring_payment.description,
            total_payments=recurring_payment.successful_payments + recurring_payment.failed_payments,
            successful_payments=recurring_payment.successful_payments,
            failed_payments=recurring_payment.failed_payments,
            total_amount_processed=recurring_payment.total_amount_processed or Decimal('0'),
            created_at=recurring_payment.created_at,
            is_active=recurring_payment.status == RecurringStatus.ACTIVE
        )
    
    async def get_payment_schedules(
        self,
        recurring_payment_id: int,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> List[PaymentScheduleResponse]:
        """Get payment schedules for recurring payment."""
        if not db:
            async with get_db_session() as db:
                return await self._get_payment_schedules_impl(recurring_payment_id, user_id, limit, offset, db)
        return await self._get_payment_schedules_impl(recurring_payment_id, user_id, limit, offset, db)
    
    async def _get_payment_schedules_impl(
        self,
        recurring_payment_id: int,
        user_id: int,
        limit: int,
        offset: int,
        db: AsyncSession
    ) -> List[PaymentScheduleResponse]:
        """Implementation of payment schedules retrieval."""
        # Verify access to recurring payment
        recurring_query = select(RecurringPayment).where(
            and_(
                RecurringPayment.id == recurring_payment_id,
                RecurringPayment.created_by == user_id
            )
        )
        recurring_result = await db.execute(recurring_query)
        recurring_payment = recurring_result.scalar_one_or_none()
        
        if not recurring_payment:
            raise ValueError("Recurring payment not found or access denied")
            
        # Get payment schedules
        schedules_query = select(PaymentSchedule).where(
            PaymentSchedule.recurring_payment_id == recurring_payment_id
        ).order_by(desc(PaymentSchedule.scheduled_date)).limit(limit).offset(offset)
        
        result = await db.execute(schedules_query)
        schedules = result.scalars().all()
        
        responses = []
        for schedule in schedules:
            responses.append(PaymentScheduleResponse(
                id=schedule.id,
                scheduled_date=schedule.scheduled_date,
                amount=schedule.amount,
                status=schedule.status,
                payment_id=schedule.payment_id,
                attempt_count=schedule.attempt_count,
                last_attempt_date=schedule.last_attempt_date,
                failure_reason=schedule.failure_reason,
                created_at=schedule.created_at
            ))
            
        return responses
    
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
            user_agent="RecurringPaymentManager"  # Should be passed from request
        )
        db.add(audit_log)
        await db.commit()