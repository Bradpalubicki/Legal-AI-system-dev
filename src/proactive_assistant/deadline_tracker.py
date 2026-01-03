"""
Deadline Tracker

Intelligent deadline tracking system with automated reminders,
escalation workflows, and predictive deadline analysis.
"""

from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field
import asyncio
import logging

from ..core.database import get_db_session
from ..trial_prep.models import Case, Deadline as TrialDeadline


logger = logging.getLogger(__name__)


class DeadlineType(str, Enum):
    """Types of legal deadlines."""
    COURT_FILING = "court_filing"
    DISCOVERY = "discovery"
    MOTION = "motion"
    HEARING = "hearing"
    TRIAL = "trial"
    APPEAL = "appeal"
    STATUTE_OF_LIMITATIONS = "statute_of_limitations"
    CONTRACT = "contract"
    REGULATORY = "regulatory"
    INTERNAL = "internal"
    CLIENT_DELIVERABLE = "client_deliverable"
    PAYMENT = "payment"
    RENEWAL = "renewal"


class DeadlineStatus(str, Enum):
    """Deadline status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    EXTENDED = "extended"


class ReminderFrequency(str, Enum):
    """Reminder frequency options."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    BUSINESS_DAYS = "business_days"


@dataclass
class DeadlineAlert:
    """Deadline alert information."""
    id: str
    deadline_id: int
    case_id: int
    case_name: str
    deadline_title: str
    deadline_type: DeadlineType
    due_date: datetime
    days_until_due: int
    priority_level: str
    message: str
    suggested_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False


@dataclass
class TaskReminder:
    """Task reminder for deadline preparation."""
    id: str
    deadline_id: int
    task_title: str
    task_description: str
    due_date: datetime
    assigned_to: Optional[int] = None
    estimated_hours: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class DeadlineRule(BaseModel):
    """Rule for deadline tracking and reminders."""
    id: str
    name: str
    deadline_types: List[DeadlineType]
    reminder_schedule: List[int]  # Days before deadline to send reminders
    auto_generate_tasks: bool = False
    task_templates: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class DeadlineTracker:
    """
    Intelligent deadline tracking with automated reminders and task generation.
    """
    
    def __init__(self):
        self.tracking_rules: List[DeadlineRule] = []
        self.pending_alerts: Dict[str, DeadlineAlert] = {}
        self.active_reminders: Dict[str, TaskReminder] = {}
        self.is_tracking = False
        self.check_interval = 3600  # 1 hour
        
        # Load default tracking rules
        self._load_default_rules()
        
    def _load_default_rules(self):
        """Load default deadline tracking rules."""
        default_rules = [
            DeadlineRule(
                id="court_filing_standard",
                name="Court Filing Standard",
                deadline_types=[DeadlineType.COURT_FILING, DeadlineType.MOTION],
                reminder_schedule=[30, 14, 7, 3, 1],
                auto_generate_tasks=True,
                task_templates=[
                    {
                        "title": "Draft {deadline_title}",
                        "days_before": 14,
                        "estimated_hours": 4.0,
                        "description": "Prepare initial draft of {deadline_title}"
                    },
                    {
                        "title": "Review and finalize {deadline_title}",
                        "days_before": 3,
                        "estimated_hours": 2.0,
                        "description": "Final review and preparation for filing"
                    },
                    {
                        "title": "File {deadline_title}",
                        "days_before": 1,
                        "estimated_hours": 1.0,
                        "description": "Submit filing to court"
                    }
                ],
                escalation_rules=[
                    {"days_before": 1, "escalate_to": "supervisor"},
                    {"days_overdue": 0, "escalate_to": "partner"}
                ]
            ),
            DeadlineRule(
                id="discovery_standard",
                name="Discovery Standard",
                deadline_types=[DeadlineType.DISCOVERY],
                reminder_schedule=[60, 30, 14, 7, 3],
                auto_generate_tasks=True,
                task_templates=[
                    {
                        "title": "Prepare discovery requests",
                        "days_before": 30,
                        "estimated_hours": 6.0
                    },
                    {
                        "title": "Review and serve discovery",
                        "days_before": 7,
                        "estimated_hours": 2.0
                    }
                ]
            ),
            DeadlineRule(
                id="statute_of_limitations",
                name="Statute of Limitations",
                deadline_types=[DeadlineType.STATUTE_OF_LIMITATIONS],
                reminder_schedule=[365, 180, 90, 30, 14, 7, 3, 1],
                auto_generate_tasks=True,
                task_templates=[
                    {
                        "title": "Investigate potential claims",
                        "days_before": 180,
                        "estimated_hours": 8.0
                    },
                    {
                        "title": "Prepare and file complaint",
                        "days_before": 30,
                        "estimated_hours": 12.0
                    }
                ],
                escalation_rules=[
                    {"days_before": 30, "escalate_to": "partner"},
                    {"days_before": 7, "escalate_to": "managing_partner"}
                ]
            )
        ]
        
        self.tracking_rules.extend(default_rules)
        
    async def start_tracking(self):
        """Start the deadline tracking service."""
        if self.is_tracking:
            return
            
        self.is_tracking = True
        logger.info("Starting deadline tracking service")
        
        while self.is_tracking:
            try:
                await self._tracking_cycle()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in deadline tracking cycle: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
                
    async def stop_tracking(self):
        """Stop the deadline tracking service."""
        self.is_tracking = False
        logger.info("Stopping deadline tracking service")
        
    async def _tracking_cycle(self):
        """Execute one deadline tracking cycle."""
        async with get_db_session() as db:
            # Get all pending deadlines
            deadlines = await self._get_pending_deadlines(db)
            
            # Process each deadline
            for deadline in deadlines:
                try:
                    await self._process_deadline(deadline, db)
                except Exception as e:
                    logger.error(f"Error processing deadline {deadline.id}: {str(e)}")
                    
            # Process task reminders
            await self._process_task_reminders()
            
            # Clean up old alerts and reminders
            await self._cleanup_old_items()
            
        logger.debug(f"Deadline tracking cycle completed for {len(deadlines)} deadlines")
        
    async def _get_pending_deadlines(self, db: AsyncSession) -> List[TrialDeadline]:
        """Get all pending deadlines that need tracking."""
        query = select(TrialDeadline).options(
            joinedload(TrialDeadline.case)
        ).where(
            and_(
                TrialDeadline.is_completed == False,
                TrialDeadline.due_date >= datetime.utcnow() - timedelta(days=1),  # Include slightly overdue
                TrialDeadline.due_date <= datetime.utcnow() + timedelta(days=365)   # Don't track too far out
            )
        ).order_by(TrialDeadline.due_date)
        
        result = await db.execute(query)
        return result.scalars().all()
        
    async def _process_deadline(self, deadline: TrialDeadline, db: AsyncSession):
        """Process a single deadline for alerts and tasks."""
        current_time = datetime.utcnow()
        days_until_due = (deadline.due_date - current_time).days
        
        # Find applicable tracking rule
        tracking_rule = await self._find_tracking_rule(deadline)
        if not tracking_rule:
            return
            
        # Check if we need to send reminders
        if days_until_due in tracking_rule.reminder_schedule:
            await self._generate_deadline_alert(deadline, days_until_due, tracking_rule, db)
            
        # Generate tasks if enabled and not already generated
        if tracking_rule.auto_generate_tasks:
            await self._generate_deadline_tasks(deadline, tracking_rule, db)
            
        # Check for escalation conditions
        await self._check_escalation_rules(deadline, days_until_due, tracking_rule, db)
        
    async def _find_tracking_rule(self, deadline: TrialDeadline) -> Optional[DeadlineRule]:
        """Find the applicable tracking rule for a deadline."""
        # Map deadline description to type (this would be more sophisticated in practice)
        deadline_type = self._infer_deadline_type(deadline)
        
        for rule in self.tracking_rules:
            if rule.is_active and deadline_type in rule.deadline_types:
                return rule
                
        return None
        
    def _infer_deadline_type(self, deadline: TrialDeadline) -> DeadlineType:
        """Infer deadline type from deadline information."""
        title_lower = deadline.title.lower()
        description_lower = deadline.description.lower() if deadline.description else ""
        
        # Simple keyword matching - would use ML in production
        if any(word in title_lower for word in ["filing", "file", "serve"]):
            return DeadlineType.COURT_FILING
        elif any(word in title_lower for word in ["discovery", "interrogator", "deposition"]):
            return DeadlineType.DISCOVERY
        elif any(word in title_lower for word in ["motion", "brief"]):
            return DeadlineType.MOTION
        elif any(word in title_lower for word in ["hearing", "court date"]):
            return DeadlineType.HEARING
        elif any(word in title_lower for word in ["trial", "jury"]):
            return DeadlineType.TRIAL
        elif any(word in title_lower for word in ["appeal", "appellate"]):
            return DeadlineType.APPEAL
        elif any(word in title_lower for word in ["statute", "limitation"]):
            return DeadlineType.STATUTE_OF_LIMITATIONS
        else:
            return DeadlineType.INTERNAL
            
    async def _generate_deadline_alert(
        self,
        deadline: TrialDeadline,
        days_until_due: int,
        rule: DeadlineRule,
        db: AsyncSession
    ):
        """Generate an alert for an approaching deadline."""
        alert_id = f"deadline_{deadline.id}_{days_until_due}d"
        
        # Check if alert already exists
        if alert_id in self.pending_alerts:
            return
            
        # Determine priority based on days until due
        if days_until_due <= 1:
            priority = "critical"
        elif days_until_due <= 3:
            priority = "high"
        elif days_until_due <= 7:
            priority = "medium"
        else:
            priority = "low"
            
        # Generate message
        if days_until_due > 0:
            message = f"Deadline '{deadline.title}' is due in {days_until_due} day{'s' if days_until_due != 1 else ''}."
        elif days_until_due == 0:
            message = f"Deadline '{deadline.title}' is due TODAY."
        else:
            message = f"Deadline '{deadline.title}' is {abs(days_until_due)} day{'s' if abs(days_until_due) != 1 else ''} OVERDUE."
            priority = "critical"
            
        # Generate suggested actions
        suggested_actions = await self._generate_suggested_actions(deadline, days_until_due, rule)
        
        # Create alert
        alert = DeadlineAlert(
            id=alert_id,
            deadline_id=deadline.id,
            case_id=deadline.case_id,
            case_name=deadline.case.case_name if deadline.case else "Unknown Case",
            deadline_title=deadline.title,
            deadline_type=self._infer_deadline_type(deadline),
            due_date=deadline.due_date,
            days_until_due=days_until_due,
            priority_level=priority,
            message=message,
            suggested_actions=suggested_actions
        )
        
        self.pending_alerts[alert_id] = alert
        logger.info(f"Generated {priority} deadline alert: {deadline.title} ({days_until_due} days)")
        
    async def _generate_suggested_actions(
        self,
        deadline: TrialDeadline,
        days_until_due: int,
        rule: DeadlineRule
    ) -> List[str]:
        """Generate suggested actions based on deadline and timeline."""
        actions = []
        
        deadline_type = self._infer_deadline_type(deadline)
        
        if deadline_type == DeadlineType.COURT_FILING:
            if days_until_due > 7:
                actions.append("Begin drafting the required filing")
                actions.append("Research applicable laws and precedents")
            elif days_until_due > 3:
                actions.append("Complete draft and begin internal review")
                actions.append("Gather all supporting documents")
            elif days_until_due > 0:
                actions.append("Finalize document and prepare for filing")
                actions.append("Verify court filing requirements and fees")
            else:
                actions.append("FILE IMMEDIATELY - Deadline is today/overdue")
                
        elif deadline_type == DeadlineType.DISCOVERY:
            if days_until_due > 14:
                actions.append("Plan discovery strategy")
                actions.append("Draft initial discovery requests")
            elif days_until_due > 7:
                actions.append("Finalize discovery documents")
                actions.append("Prepare service arrangements")
            else:
                actions.append("Serve discovery documents immediately")
                
        elif deadline_type == DeadlineType.STATUTE_OF_LIMITATIONS:
            if days_until_due > 30:
                actions.append("Investigate and document all potential claims")
                actions.append("Research applicable statutes and exceptions")
            elif days_until_due > 7:
                actions.append("Draft complaint or protective filing")
                actions.append("Prepare for immediate filing if needed")
            else:
                actions.append("FILE COMPLAINT IMMEDIATELY to preserve claims")
                
        # Add general actions
        if days_until_due <= 3:
            actions.append("Notify supervising attorney")
            actions.append("Update case timeline and dependencies")
            
        return actions
        
    async def _generate_deadline_tasks(
        self,
        deadline: TrialDeadline,
        rule: DeadlineRule,
        db: AsyncSession
    ):
        """Generate preparation tasks for a deadline."""
        current_time = datetime.utcnow()
        
        for task_template in rule.task_templates:
            days_before = task_template.get("days_before", 7)
            task_due_date = deadline.due_date - timedelta(days=days_before)
            
            # Only create tasks for future dates
            if task_due_date <= current_time:
                continue
                
            # Check if task already exists
            task_id = f"task_{deadline.id}_{days_before}d"
            if task_id in self.active_reminders:
                continue
                
            # Create task
            task_title = task_template["title"].format(deadline_title=deadline.title)
            task_description = task_template.get("description", "").format(deadline_title=deadline.title)
            
            task = TaskReminder(
                id=task_id,
                deadline_id=deadline.id,
                task_title=task_title,
                task_description=task_description,
                due_date=task_due_date,
                estimated_hours=task_template.get("estimated_hours"),
                dependencies=task_template.get("dependencies", [])
            )
            
            self.active_reminders[task_id] = task
            logger.info(f"Generated task: {task_title} (due {task_due_date.strftime('%Y-%m-%d')})")
            
    async def _check_escalation_rules(
        self,
        deadline: TrialDeadline,
        days_until_due: int,
        rule: DeadlineRule,
        db: AsyncSession
    ):
        """Check and apply escalation rules."""
        for escalation_rule in rule.escalation_rules:
            should_escalate = False
            
            # Check days_before condition
            if "days_before" in escalation_rule:
                if days_until_due <= escalation_rule["days_before"]:
                    should_escalate = True
                    
            # Check days_overdue condition
            if "days_overdue" in escalation_rule:
                if days_until_due < -escalation_rule["days_overdue"]:
                    should_escalate = True
                    
            if should_escalate:
                escalate_to = escalation_rule.get("escalate_to")
                logger.warning(f"Escalating deadline '{deadline.title}' to {escalate_to}")
                # Implementation would send notification to specified role/person
                
    async def _process_task_reminders(self):
        """Process and send task reminders."""
        current_time = datetime.utcnow()
        
        for task in self.active_reminders.values():
            if task.is_completed:
                continue
                
            # Check if task is due soon
            time_until_due = task.due_date - current_time
            
            if time_until_due <= timedelta(hours=24) and time_until_due > timedelta(hours=0):
                # Task is due within 24 hours
                logger.info(f"Task reminder: '{task.task_title}' is due in {time_until_due}")
                # Would send notification here
                
            elif time_until_due <= timedelta(hours=0):
                # Task is overdue
                logger.warning(f"Task overdue: '{task.task_title}' was due {abs(time_until_due)} ago")
                # Would send overdue notification here
                
    async def _cleanup_old_items(self):
        """Clean up old alerts and reminders."""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Clean up old alerts
        old_alert_ids = []
        for alert_id, alert in self.pending_alerts.items():
            if alert.created_at < cutoff_date or alert.due_date < cutoff_date:
                old_alert_ids.append(alert_id)
                
        for alert_id in old_alert_ids:
            del self.pending_alerts[alert_id]
            
        # Clean up completed or old tasks
        old_task_ids = []
        for task_id, task in self.active_reminders.items():
            if task.is_completed or task.created_at < cutoff_date:
                old_task_ids.append(task_id)
                
        for task_id in old_task_ids:
            del self.active_reminders[task_id]
            
        if old_alert_ids or old_task_ids:
            logger.info(f"Cleaned up {len(old_alert_ids)} old alerts and {len(old_task_ids)} old tasks")
            
    # Public API methods
    
    async def get_deadline_alerts(
        self,
        case_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> List[DeadlineAlert]:
        """Get deadline alerts, optionally filtered."""
        alerts = []
        
        for alert in self.pending_alerts.values():
            if case_id is not None and alert.case_id != case_id:
                continue
            if priority is not None and alert.priority_level != priority:
                continue
            alerts.append(alert)
            
        # Sort by due date and priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: (x.due_date, priority_order.get(x.priority_level, 4)))
        
        return alerts
        
    async def get_upcoming_deadlines(
        self,
        days_ahead: int = 30,
        case_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> List[TrialDeadline]:
        """Get upcoming deadlines within specified days."""
        if not db:
            async with get_db_session() as db:
                return await self._get_upcoming_deadlines_impl(days_ahead, case_id, db)
        return await self._get_upcoming_deadlines_impl(days_ahead, case_id, db)
        
    async def _get_upcoming_deadlines_impl(
        self,
        days_ahead: int,
        case_id: Optional[int],
        db: AsyncSession
    ) -> List[TrialDeadline]:
        """Implementation of upcoming deadlines retrieval."""
        current_time = datetime.utcnow()
        future_date = current_time + timedelta(days=days_ahead)
        
        conditions = [
            TrialDeadline.due_date >= current_time,
            TrialDeadline.due_date <= future_date,
            TrialDeadline.is_completed == False
        ]
        
        if case_id:
            conditions.append(TrialDeadline.case_id == case_id)
            
        query = select(TrialDeadline).options(
            joinedload(TrialDeadline.case)
        ).where(and_(*conditions)).order_by(TrialDeadline.due_date)
        
        result = await db.execute(query)
        return result.scalars().all()
        
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a deadline alert."""
        if alert_id in self.pending_alerts:
            self.pending_alerts[alert_id].acknowledged = True
            logger.info(f"Acknowledged deadline alert: {alert_id}")
            return True
        return False
        
    async def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        if task_id in self.active_reminders:
            self.active_reminders[task_id].is_completed = True
            logger.info(f"Completed task: {task_id}")
            return True
        return False
        
    async def get_task_reminders(
        self,
        case_id: Optional[int] = None,
        overdue_only: bool = False
    ) -> List[TaskReminder]:
        """Get task reminders."""
        tasks = []
        current_time = datetime.utcnow()
        
        for task in self.active_reminders.values():
            if task.is_completed:
                continue
                
            # Get case_id from deadline (would need to look up)
            # For now, skip case filtering
            
            if overdue_only and task.due_date > current_time:
                continue
                
            tasks.append(task)
            
        # Sort by due date
        tasks.sort(key=lambda x: x.due_date)
        return tasks
        
    async def add_tracking_rule(self, rule: DeadlineRule) -> bool:
        """Add a new deadline tracking rule."""
        # Check for existing rule with same ID
        for existing_rule in self.tracking_rules:
            if existing_rule.id == rule.id:
                return False
                
        self.tracking_rules.append(rule)
        logger.info(f"Added deadline tracking rule: {rule.name}")
        return True
        
    async def get_deadline_statistics(self, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """Get deadline statistics for dashboard."""
        if not db:
            async with get_db_session() as db:
                return await self._get_deadline_statistics_impl(db)
        return await self._get_deadline_statistics_impl(db)
        
    async def _get_deadline_statistics_impl(self, db: AsyncSession) -> Dict[str, Any]:
        """Implementation of deadline statistics."""
        current_time = datetime.utcnow()
        
        # Count upcoming deadlines by time period
        upcoming_7d = await db.execute(
            select(func.count(TrialDeadline.id)).where(
                and_(
                    TrialDeadline.due_date >= current_time,
                    TrialDeadline.due_date <= current_time + timedelta(days=7),
                    TrialDeadline.is_completed == False
                )
            )
        )
        
        upcoming_30d = await db.execute(
            select(func.count(TrialDeadline.id)).where(
                and_(
                    TrialDeadline.due_date >= current_time,
                    TrialDeadline.due_date <= current_time + timedelta(days=30),
                    TrialDeadline.is_completed == False
                )
            )
        )
        
        overdue = await db.execute(
            select(func.count(TrialDeadline.id)).where(
                and_(
                    TrialDeadline.due_date < current_time,
                    TrialDeadline.is_completed == False
                )
            )
        )
        
        # Get active alerts count
        active_alerts = len([a for a in self.pending_alerts.values() if not a.acknowledged])
        active_tasks = len([t for t in self.active_reminders.values() if not t.is_completed])
        
        return {
            "tracking_status": "active" if self.is_tracking else "inactive",
            "upcoming_7_days": upcoming_7d.scalar() or 0,
            "upcoming_30_days": upcoming_30d.scalar() or 0,
            "overdue_deadlines": overdue.scalar() or 0,
            "active_alerts": active_alerts,
            "active_tasks": active_tasks,
            "tracking_rules": len([r for r in self.tracking_rules if r.is_active])
        }