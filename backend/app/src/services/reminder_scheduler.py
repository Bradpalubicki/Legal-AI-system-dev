"""
Automated Task Reminder Scheduler
Runs background tasks to send reminder notifications for upcoming deadlines
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Background scheduler for automated reminders"""

    def __init__(self, check_interval_minutes: int = 60):
        """
        Initialize reminder scheduler

        Args:
            check_interval_minutes: How often to check for reminders (default: 60 minutes)
        """
        self.check_interval_minutes = check_interval_minutes
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, db_session_factory):
        """
        Start the reminder scheduler

        Args:
            db_session_factory: Function that returns a database session
        """
        if self.running:
            logger.warning("Reminder scheduler already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._run_scheduler(db_session_factory))
        logger.info(f"Reminder scheduler started (check interval: {self.check_interval_minutes} minutes)")

    async def stop(self):
        """Stop the reminder scheduler"""
        if not self.running:
            return

        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Reminder scheduler stopped")

    async def _run_scheduler(self, db_session_factory):
        """
        Main scheduler loop

        Args:
            db_session_factory: Function that returns a database session
        """
        while self.running:
            try:
                # Run reminder check
                await self._check_and_send_reminders(db_session_factory)

            except Exception as e:
                logger.error(f"Error in reminder scheduler: {str(e)}")

            # Wait until next check
            await asyncio.sleep(self.check_interval_minutes * 60)

    async def _check_and_send_reminders(self, db_session_factory):
        """
        Check for upcoming deadlines and send reminders

        Args:
            db_session_factory: Function that returns a database session
        """
        from ...models.case_management import CaseTimelineEvent as TimelineEvent, LegalCase as Case
        from .notification_service import get_notification_service

        db = db_session_factory()
        try:
            notification_service = get_notification_service()

            # Don't send reminders if email is not configured
            if not notification_service.enabled:
                logger.debug("Skipping reminder check - email not configured")
                return

            now = datetime.now()

            # Define reminder windows (days before event)
            reminder_windows = [
                1,   # 1 day before
                3,   # 3 days before
                7,   # 1 week before
                14,  # 2 weeks before
            ]

            reminders_sent = 0

            for days_before in reminder_windows:
                # Calculate target date range
                target_date_start = now + timedelta(days=days_before)
                target_date_end = target_date_start + timedelta(hours=1)  # 1-hour window

                # Find events in this window
                events = db.query(TimelineEvent).filter(
                    TimelineEvent.status == 'scheduled',
                    TimelineEvent.event_date >= target_date_start,
                    TimelineEvent.event_date < target_date_end
                ).all()

                for event in events:
                    # Get case
                    case = db.query(Case).filter(Case.id == event.case_id).first()
                    if not case:
                        continue

                    # TODO: Get attorney/user email from case
                    # For now, using environment variable for default email
                    import os
                    default_email = os.getenv('DEFAULT_REMINDER_EMAIL')

                    if not default_email:
                        logger.warning(f"No email configured for case {case.id} - skipping reminder")
                        continue

                    # Send reminder
                    success = notification_service.send_deadline_reminder(
                        to_email=default_email,
                        case_name=case.case_name,
                        case_id=case.id,
                        event_title=event.title,
                        event_date=event.event_date,
                        event_location=event.location,
                        days_until=days_before
                    )

                    if success:
                        reminders_sent += 1
                        logger.info(f"Sent automatic reminder for event {event.id} ({days_before} days before)")

            if reminders_sent > 0:
                logger.info(f"Sent {reminders_sent} automatic reminders")

        except Exception as e:
            logger.error(f"Error checking/sending reminders: {str(e)}")
        finally:
            db.close()

    def get_next_reminders(
        self,
        db: Session,
        days_ahead: int = 14,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get list of next scheduled reminders

        Args:
            db: Database session
            days_ahead: Number of days to look ahead
            limit: Maximum number of reminders to return

        Returns:
            List of upcoming reminder dictionaries
        """
        from ...models.case_management import CaseTimelineEvent as TimelineEvent, LegalCase as Case

        try:
            cutoff_date = datetime.now() + timedelta(days=days_ahead)

            events = db.query(TimelineEvent).join(Case).filter(
                TimelineEvent.status == 'scheduled',
                TimelineEvent.event_date >= datetime.now(),
                TimelineEvent.event_date <= cutoff_date
            ).order_by(TimelineEvent.event_date).limit(limit).all()

            reminders = []
            for event in events:
                case = db.query(Case).filter(Case.id == event.case_id).first()
                if case:
                    days_until = (event.event_date - datetime.now()).days

                    # Determine which reminder windows this falls into
                    reminder_types = []
                    if days_until <= 1:
                        reminder_types.append("1 day")
                    elif days_until <= 3:
                        reminder_types.append("3 days")
                    elif days_until <= 7:
                        reminder_types.append("1 week")
                    elif days_until <= 14:
                        reminder_types.append("2 weeks")

                    reminders.append({
                        'event_id': event.id,
                        'event_title': event.title,
                        'event_date': event.event_date.isoformat(),
                        'event_location': event.location,
                        'case_id': case.id,
                        'case_name': case.case_name,
                        'days_until': days_until,
                        'reminder_types': reminder_types
                    })

            return reminders

        except Exception as e:
            logger.error(f"Error getting next reminders: {str(e)}")
            return []


# Global scheduler instance
_scheduler: Optional[ReminderScheduler] = None


def get_reminder_scheduler() -> ReminderScheduler:
    """Get or create reminder scheduler instance"""
    global _scheduler

    if _scheduler is None:
        import os
        check_interval = int(os.getenv('REMINDER_CHECK_INTERVAL_MINUTES', '60'))
        _scheduler = ReminderScheduler(check_interval_minutes=check_interval)

    return _scheduler


async def start_reminder_scheduler(db_session_factory):
    """Start the global reminder scheduler"""
    scheduler = get_reminder_scheduler()
    await scheduler.start(db_session_factory)


async def stop_reminder_scheduler():
    """Stop the global reminder scheduler"""
    scheduler = get_reminder_scheduler()
    await scheduler.stop()
