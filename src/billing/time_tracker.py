"""
Time Tracking Service

Comprehensive time tracking system for legal billing with automatic time capture,
timesheet management, and billing integration.
"""

from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field

from .advanced_models import (
    TimeEntry, TimeSheet, AutoTimeCapture, BillingMatter, BillingRate,
    TimesheetTemplate, BillingRule, AuditLog, TimesheetStatus, TimeEntryStatus,
    BillableStatus, CaptureMethod
)
from ..core.database import get_db_session
from ..core.security import get_current_user_id


logger = logging.getLogger(__name__)


class TimeEntryRequest(BaseModel):
    """Request model for creating time entries."""
    matter_id: int
    entry_date: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    activity_description: str = Field(..., min_length=10, max_length=2000)
    activity_code: Optional[str] = None
    billable: bool = True
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TimesheetSummary(BaseModel):
    """Summary statistics for timesheet."""
    total_hours: Decimal
    billable_hours: Decimal
    non_billable_hours: Decimal
    total_value: Decimal
    entries_count: int
    matters_count: int
    avg_hourly_rate: Decimal


class TimeTracker:
    """
    Advanced time tracking service with automatic capture and billing integration.
    """
    
    def __init__(self):
        self.active_timers: Dict[int, Dict[str, Any]] = {}
        self.auto_capture_enabled = True
        
    async def start_timer(
        self,
        user_id: int,
        matter_id: int,
        activity_description: str,
        activity_code: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Start a new timer for time tracking."""
        if not db:
            async with get_db_session() as db:
                return await self._start_timer_impl(
                    user_id, matter_id, activity_description, activity_code, db
                )
        return await self._start_timer_impl(
            user_id, matter_id, activity_description, activity_code, db
        )
    
    async def _start_timer_impl(
        self,
        user_id: int,
        matter_id: int,
        activity_description: str,
        activity_code: Optional[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of timer start."""
        # Stop any existing timer for this user
        if user_id in self.active_timers:
            await self.stop_timer(user_id, db=db)
            
        # Verify matter exists and user has access
        matter_query = select(BillingMatter).where(
            and_(
                BillingMatter.id == matter_id,
                BillingMatter.responsible_attorney == user_id
            )
        )
        result = await db.execute(matter_query)
        matter = result.scalar_one_or_none()
        
        if not matter:
            raise ValueError(f"Matter {matter_id} not found or access denied")
            
        # Start timer
        start_time = datetime.utcnow()
        self.active_timers[user_id] = {
            'matter_id': matter_id,
            'start_time': start_time,
            'activity_description': activity_description,
            'activity_code': activity_code,
            'matter_name': matter.matter_name
        }
        
        # Create auto capture record if enabled
        if self.auto_capture_enabled:
            auto_capture = AutoTimeCapture(
                user_id=user_id,
                matter_id=matter_id,
                start_time=start_time,
                capture_method=CaptureMethod.MANUAL_START,
                activity_data={
                    'description': activity_description,
                    'code': activity_code
                }
            )
            db.add(auto_capture)
            await db.commit()
            
        logger.info(f"Timer started for user {user_id} on matter {matter_id}")
        
        return {
            'status': 'started',
            'start_time': start_time,
            'matter_id': matter_id,
            'matter_name': matter.matter_name,
            'activity_description': activity_description
        }
    
    async def stop_timer(
        self,
        user_id: int,
        create_entry: bool = True,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Stop active timer and optionally create time entry."""
        if not db:
            async with get_db_session() as db:
                return await self._stop_timer_impl(user_id, create_entry, db)
        return await self._stop_timer_impl(user_id, create_entry, db)
    
    async def _stop_timer_impl(
        self,
        user_id: int,
        create_entry: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of timer stop."""
        if user_id not in self.active_timers:
            raise ValueError("No active timer found for user")
            
        timer_data = self.active_timers[user_id]
        end_time = datetime.utcnow()
        duration = end_time - timer_data['start_time']
        duration_minutes = int(duration.total_seconds() / 60)
        
        result = {
            'status': 'stopped',
            'start_time': timer_data['start_time'],
            'end_time': end_time,
            'duration_minutes': duration_minutes,
            'matter_id': timer_data['matter_id'],
            'activity_description': timer_data['activity_description']
        }
        
        if create_entry and duration_minutes > 0:
            # Create time entry
            entry_request = TimeEntryRequest(
                matter_id=timer_data['matter_id'],
                entry_date=timer_data['start_time'],
                start_time=timer_data['start_time'],
                end_time=end_time,
                duration_minutes=duration_minutes,
                activity_description=timer_data['activity_description'],
                activity_code=timer_data.get('activity_code'),
                billable=True
            )
            
            time_entry = await self.create_time_entry(user_id, entry_request, db=db)
            result['time_entry_id'] = time_entry.id
            
        # Update auto capture record
        auto_capture_query = select(AutoTimeCapture).where(
            and_(
                AutoTimeCapture.user_id == user_id,
                AutoTimeCapture.matter_id == timer_data['matter_id'],
                AutoTimeCapture.start_time == timer_data['start_time']
            )
        )
        auto_result = await db.execute(auto_capture_query)
        auto_capture = auto_result.scalar_one_or_none()
        
        if auto_capture:
            auto_capture.end_time = end_time
            auto_capture.duration_minutes = duration_minutes
            await db.commit()
            
        # Remove from active timers
        del self.active_timers[user_id]
        
        logger.info(f"Timer stopped for user {user_id}, duration: {duration_minutes} minutes")
        return result
    
    async def create_time_entry(
        self,
        user_id: int,
        entry_request: TimeEntryRequest,
        db: Optional[AsyncSession] = None
    ) -> TimeEntry:
        """Create a new time entry with automatic rate calculation."""
        if not db:
            async with get_db_session() as db:
                return await self._create_time_entry_impl(user_id, entry_request, db)
        return await self._create_time_entry_impl(user_id, entry_request, db)
    
    async def _create_time_entry_impl(
        self,
        user_id: int,
        entry_request: TimeEntryRequest,
        db: AsyncSession
    ) -> TimeEntry:
        """Implementation of time entry creation."""
        # Calculate duration if not provided
        duration_minutes = entry_request.duration_minutes
        if not duration_minutes and entry_request.start_time and entry_request.end_time:
            duration = entry_request.end_time - entry_request.start_time
            duration_minutes = int(duration.total_seconds() / 60)
            
        if not duration_minutes or duration_minutes <= 0:
            raise ValueError("Duration must be positive")
            
        # Get billing rate for user and matter
        rate_query = select(BillingRate).where(
            and_(
                BillingRate.user_id == user_id,
                BillingRate.matter_id == entry_request.matter_id,
                BillingRate.effective_date <= entry_request.entry_date,
                or_(
                    BillingRate.end_date.is_(None),
                    BillingRate.end_date > entry_request.entry_date
                )
            )
        ).order_by(desc(BillingRate.effective_date))
        
        rate_result = await db.execute(rate_query)
        billing_rate = rate_result.scalar_one_or_none()
        
        if not billing_rate:
            # Try to get default rate
            default_rate_query = select(BillingRate).where(
                and_(
                    BillingRate.user_id == user_id,
                    BillingRate.matter_id.is_(None),
                    BillingRate.is_default == True
                )
            )
            default_result = await db.execute(default_rate_query)
            billing_rate = default_result.scalar_one_or_none()
            
        if not billing_rate:
            raise ValueError("No billing rate found for user and matter")
            
        # Apply billing rules
        billable_minutes = await self._apply_billing_rules(
            duration_minutes, entry_request.matter_id, user_id, db
        )
        
        # Calculate amounts
        hourly_rate = billing_rate.standard_rate
        hours = Decimal(str(billable_minutes)) / Decimal('60')
        total_amount = hours * hourly_rate
        
        # Create time entry
        time_entry = TimeEntry(
            matter_id=entry_request.matter_id,
            timekeeper=user_id,
            entry_date=entry_request.entry_date,
            start_time=entry_request.start_time,
            end_time=entry_request.end_time,
            duration_minutes=duration_minutes,
            billable_minutes=billable_minutes if entry_request.billable else 0,
            activity_description=entry_request.activity_description,
            activity_code=entry_request.activity_code,
            hourly_rate=hourly_rate,
            total_amount=total_amount if entry_request.billable else Decimal('0'),
            billable_status=BillableStatus.BILLABLE if entry_request.billable else BillableStatus.NON_BILLABLE,
            entry_status=TimeEntryStatus.DRAFT,
            notes=entry_request.notes,
            tags=entry_request.tags,
            created_by=user_id
        )
        
        db.add(time_entry)
        await db.commit()
        await db.refresh(time_entry)
        
        # Create audit log
        await self._create_audit_log(
            user_id, f"Created time entry {time_entry.entry_id}", 
            {'entry_id': time_entry.id, 'duration': duration_minutes}, db
        )
        
        logger.info(f"Time entry created: {time_entry.entry_id} for {duration_minutes} minutes")
        return time_entry
    
    async def _apply_billing_rules(
        self,
        duration_minutes: int,
        matter_id: int,
        user_id: int,
        db: AsyncSession
    ) -> int:
        """Apply billing rules to determine billable minutes."""
        # Get applicable billing rules
        rules_query = select(BillingRule).where(
            and_(
                BillingRule.matter_id == matter_id,
                BillingRule.is_active == True
            )
        ).order_by(BillingRule.priority)
        
        result = await db.execute(rules_query)
        rules = result.scalars().all()
        
        billable_minutes = duration_minutes
        
        for rule in rules:
            if rule.rule_type == 'minimum_increment':
                # Round up to minimum increment
                increment = rule.rule_parameters.get('increment_minutes', 15)
                billable_minutes = ((billable_minutes + increment - 1) // increment) * increment
                
            elif rule.rule_type == 'daily_maximum':
                # Apply daily maximum (would need additional logic to check daily total)
                max_daily = rule.rule_parameters.get('max_daily_hours', 24) * 60
                billable_minutes = min(billable_minutes, max_daily)
                
            elif rule.rule_type == 'activity_multiplier':
                # Apply activity-based multiplier
                multiplier = rule.rule_parameters.get('multiplier', 1.0)
                billable_minutes = int(billable_minutes * multiplier)
                
        return billable_minutes
    
    async def get_timesheet_summary(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        db: Optional[AsyncSession] = None
    ) -> TimesheetSummary:
        """Get timesheet summary for date range."""
        if not db:
            async with get_db_session() as db:
                return await self._get_timesheet_summary_impl(
                    user_id, start_date, end_date, db
                )
        return await self._get_timesheet_summary_impl(
            user_id, start_date, end_date, db
        )
    
    async def _get_timesheet_summary_impl(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession
    ) -> TimesheetSummary:
        """Implementation of timesheet summary."""
        query = select(
            func.sum(TimeEntry.billable_minutes).label('total_billable'),
            func.sum(TimeEntry.duration_minutes - TimeEntry.billable_minutes).label('total_non_billable'),
            func.sum(TimeEntry.total_amount).label('total_value'),
            func.count(TimeEntry.id).label('entries_count'),
            func.count(func.distinct(TimeEntry.matter_id)).label('matters_count'),
            func.avg(TimeEntry.hourly_rate).label('avg_rate')
        ).where(
            and_(
                TimeEntry.timekeeper == user_id,
                TimeEntry.entry_date >= start_date,
                TimeEntry.entry_date <= end_date
            )
        )
        
        result = await db.execute(query)
        row = result.first()
        
        total_billable = row.total_billable or 0
        total_non_billable = row.total_non_billable or 0
        total_hours = Decimal(str(total_billable + total_non_billable)) / Decimal('60')
        billable_hours = Decimal(str(total_billable)) / Decimal('60')
        non_billable_hours = Decimal(str(total_non_billable)) / Decimal('60')
        
        return TimesheetSummary(
            total_hours=total_hours,
            billable_hours=billable_hours,
            non_billable_hours=non_billable_hours,
            total_value=row.total_value or Decimal('0'),
            entries_count=row.entries_count or 0,
            matters_count=row.matters_count or 0,
            avg_hourly_rate=row.avg_rate or Decimal('0')
        )
    
    async def get_active_timer(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get active timer for user."""
        if user_id in self.active_timers:
            timer_data = self.active_timers[user_id].copy()
            # Add elapsed time
            elapsed = datetime.utcnow() - timer_data['start_time']
            timer_data['elapsed_minutes'] = int(elapsed.total_seconds() / 60)
            return timer_data
        return None
    
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
            user_agent="TimeTracker"  # Should be passed from request
        )
        db.add(audit_log)
        await db.commit()


class TimesheetManager:
    """
    Timesheet management service for organizing and approving time entries.
    """
    
    async def create_timesheet(
        self,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        template_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> TimeSheet:
        """Create a new timesheet for the specified period."""
        if not db:
            async with get_db_session() as db:
                return await self._create_timesheet_impl(
                    user_id, period_start, period_end, template_id, db
                )
        return await self._create_timesheet_impl(
            user_id, period_start, period_end, template_id, db
        )
    
    async def _create_timesheet_impl(
        self,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        template_id: Optional[int],
        db: AsyncSession
    ) -> TimeSheet:
        """Implementation of timesheet creation."""
        # Check for existing timesheet in period
        existing_query = select(TimeSheet).where(
            and_(
                TimeSheet.user_id == user_id,
                TimeSheet.period_start <= period_end,
                TimeSheet.period_end >= period_start
            )
        )
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError("Timesheet already exists for overlapping period")
            
        # Get template if specified
        template = None
        if template_id:
            template_query = select(TimesheetTemplate).where(
                TimesheetTemplate.id == template_id
            )
            template_result = await db.execute(template_query)
            template = template_result.scalar_one_or_none()
            
        # Create timesheet
        timesheet = TimeSheet(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            template_id=template_id,
            status=TimesheetStatus.DRAFT,
            created_by=user_id
        )
        
        db.add(timesheet)
        await db.commit()
        await db.refresh(timesheet)
        
        # Auto-populate with existing time entries
        await self._populate_timesheet_entries(timesheet.id, db)
        
        logger.info(f"Timesheet created: {timesheet.id} for user {user_id}")
        return timesheet
    
    async def _populate_timesheet_entries(
        self,
        timesheet_id: int,
        db: AsyncSession
    ):
        """Populate timesheet with existing time entries."""
        # Get timesheet details
        timesheet_query = select(TimeSheet).where(TimeSheet.id == timesheet_id)
        result = await db.execute(timesheet_query)
        timesheet = result.scalar_one()
        
        # Get time entries in period
        entries_query = select(TimeEntry).where(
            and_(
                TimeEntry.timekeeper == timesheet.user_id,
                TimeEntry.entry_date >= timesheet.period_start,
                TimeEntry.entry_date <= timesheet.period_end,
                TimeEntry.timesheet_id.is_(None)
            )
        )
        
        entries_result = await db.execute(entries_query)
        entries = entries_result.scalars().all()
        
        # Associate entries with timesheet
        for entry in entries:
            entry.timesheet_id = timesheet_id
            
        await db.commit()
        logger.info(f"Associated {len(entries)} time entries with timesheet {timesheet_id}")
    
    async def submit_timesheet(
        self,
        timesheet_id: int,
        user_id: int,
        db: Optional[AsyncSession] = None
    ) -> TimeSheet:
        """Submit timesheet for approval."""
        if not db:
            async with get_db_session() as db:
                return await self._submit_timesheet_impl(timesheet_id, user_id, db)
        return await self._submit_timesheet_impl(timesheet_id, user_id, db)
    
    async def _submit_timesheet_impl(
        self,
        timesheet_id: int,
        user_id: int,
        db: AsyncSession
    ) -> TimeSheet:
        """Implementation of timesheet submission."""
        # Get timesheet
        query = select(TimeSheet).where(
            and_(
                TimeSheet.id == timesheet_id,
                TimeSheet.user_id == user_id
            )
        )
        result = await db.execute(query)
        timesheet = result.scalar_one_or_none()
        
        if not timesheet:
            raise ValueError("Timesheet not found or access denied")
            
        if timesheet.status != TimesheetStatus.DRAFT:
            raise ValueError("Can only submit draft timesheets")
            
        # Validate all time entries
        entries_query = select(TimeEntry).where(
            TimeEntry.timesheet_id == timesheet_id
        )
        entries_result = await db.execute(entries_query)
        entries = entries_result.scalars().all()
        
        # Update entry statuses
        for entry in entries:
            if entry.entry_status == TimeEntryStatus.DRAFT:
                entry.entry_status = TimeEntryStatus.SUBMITTED
                
        # Update timesheet status
        timesheet.status = TimesheetStatus.SUBMITTED
        timesheet.submitted_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Timesheet {timesheet_id} submitted for approval")
        return timesheet