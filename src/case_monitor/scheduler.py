"""
Case Monitoring Scheduler

Manages the scheduling and execution of PACER monitoring checks.
Implements intelligent scheduling with priority queues, load balancing,
and cost optimization.
"""

import asyncio
import heapq
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import logging
import random

from ..shared.utils.cache_manager import cache_manager
from ..pacer_gateway.gateway import pacer_gateway
from .models import (
    MonitoredCase, MonitorStatus, MonitoringFrequency, 
    calculate_priority_score, MonitoringStatistics
)
from .detector import change_detector


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for the monitoring scheduler"""
    max_concurrent_checks: int = 5
    check_timeout_seconds: int = 120
    retry_failed_checks: bool = True
    max_retries: int = 3
    retry_delay_minutes: int = 5
    cost_limit_per_hour_cents: int = 5000  # $50/hour limit
    enable_intelligent_scheduling: bool = True
    priority_boost_hours: int = 24  # Hours after change to boost priority
    load_balancing_enabled: bool = True
    batch_size: int = 10


@dataclass 
class ScheduledCheck:
    """A scheduled monitoring check"""
    monitor_id: str
    case_number: str
    court_id: str
    scheduled_time: datetime
    priority_score: float
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __lt__(self, other):
        """Enable heap comparison based on priority and time"""
        if self.priority_score != other.priority_score:
            return self.priority_score < other.priority_score  # Lower score = higher priority
        return self.scheduled_time < other.scheduled_time


class MonitorScheduler:
    """Schedules and executes case monitoring checks"""
    
    def __init__(self, config: Optional[ScheduleConfig] = None):
        self.config = config or ScheduleConfig()
        
        # Priority queue for scheduled checks
        self.check_queue: List[ScheduledCheck] = []
        self.active_checks: Set[str] = set()  # Monitor IDs currently being checked
        
        # Statistics
        self.stats = MonitoringStatistics()
        self.hourly_cost_tracking: Dict[str, int] = {}  # Hour -> cost in cents
        
        # Semaphore for concurrent check limiting
        self.check_semaphore = asyncio.Semaphore(self.config.max_concurrent_checks)
        
        # Scheduler state
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        logger.info("Monitor Scheduler initialized")
    
    async def start(self):
        """Start the monitoring scheduler"""
        
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        
        # Start main scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_loop())
        
        logger.info("Monitor Scheduler started")
    
    async def stop(self):
        """Stop the monitoring scheduler"""
        
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Wait for active checks to complete
        while self.active_checks:
            await asyncio.sleep(1)
        
        logger.info("Monitor Scheduler stopped")
    
    async def schedule_check(self, monitored_case: MonitoredCase):
        """Schedule a monitoring check for a case"""
        
        try:
            if not monitored_case.is_active:
                return
            
            # Calculate priority score
            priority_score = calculate_priority_score(monitored_case)
            
            # Determine check time
            if monitored_case.should_check_now():
                scheduled_time = datetime.now(timezone.utc)
            else:
                scheduled_time = monitored_case.next_check_at or monitored_case.get_next_check_time()
            
            # Create scheduled check
            scheduled_check = ScheduledCheck(
                monitor_id=monitored_case.monitor_id,
                case_number=monitored_case.case_number,
                court_id=monitored_case.court_id,
                scheduled_time=scheduled_time,
                priority_score=priority_score
            )
            
            # Add to priority queue
            heapq.heappush(self.check_queue, scheduled_check)
            
            logger.debug(
                f"Scheduled check for case {monitored_case.case_number} at {scheduled_time} "
                f"(priority: {priority_score:.2f})"
            )
            
        except Exception as e:
            logger.error(f"Failed to schedule check: {str(e)}")
    
    async def schedule_bulk_checks(self, monitored_cases: List[MonitoredCase]):
        """Schedule multiple monitoring checks efficiently"""
        
        try:
            scheduled_count = 0
            
            for case in monitored_cases:
                if case.is_active:
                    await self.schedule_check(case)
                    scheduled_count += 1
            
            logger.info(f"Scheduled {scheduled_count} monitoring checks")
            
        except Exception as e:
            logger.error(f"Bulk scheduling failed: {str(e)}")
    
    async def get_next_due_checks(self, limit: int = None) -> List[ScheduledCheck]:
        """Get the next due monitoring checks"""
        
        limit = limit or self.config.batch_size
        now = datetime.now(timezone.utc)
        due_checks = []
        
        # Extract due checks from priority queue
        temp_queue = []
        
        while self.check_queue and len(due_checks) < limit:
            check = heapq.heappop(self.check_queue)
            
            if check.scheduled_time <= now and check.monitor_id not in self.active_checks:
                due_checks.append(check)
            else:
                temp_queue.append(check)
        
        # Put remaining checks back
        for check in temp_queue:
            heapq.heappush(self.check_queue, check)
        
        return due_checks
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        
        try:
            while self.is_running:
                try:
                    # Get due checks
                    due_checks = await self.get_next_due_checks()
                    
                    if due_checks:
                        # Execute checks concurrently
                        tasks = []
                        for check in due_checks:
                            if await self._can_execute_check(check):
                                task = asyncio.create_task(self._execute_check(check))
                                tasks.append(task)
                        
                        if tasks:
                            # Wait for checks to complete or timeout
                            await asyncio.wait_for(
                                asyncio.gather(*tasks, return_exceptions=True),
                                timeout=self.config.check_timeout_seconds * 2
                            )
                    
                    # Brief pause between scheduler cycles
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except asyncio.TimeoutError:
                    logger.warning("Scheduler cycle timed out")
                except Exception as e:
                    logger.error(f"Scheduler loop error: {str(e)}")
                    await asyncio.sleep(60)  # Wait longer on error
                    
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
        except Exception as e:
            logger.error(f"Scheduler loop failed: {str(e)}")
    
    async def _execute_check(self, scheduled_check: ScheduledCheck):
        """Execute a single monitoring check"""
        
        monitor_id = scheduled_check.monitor_id
        
        try:
            # Mark as active
            self.active_checks.add(monitor_id)
            
            # Get monitored case
            monitored_case = await self._get_monitored_case(monitor_id)
            if not monitored_case:
                logger.warning(f"Monitored case not found: {monitor_id}")
                return
            
            # Acquire semaphore
            async with self.check_semaphore:
                logger.info(f"Executing check for case {scheduled_check.case_number}")
                
                # Perform the actual check
                success, cost_cents, changes_detected = await self._perform_pacer_check(
                    monitored_case
                )
                
                # Update statistics
                await self._update_check_statistics(
                    success, cost_cents, changes_detected, scheduled_check
                )
                
                # Handle results
                if success:
                    await self._handle_successful_check(
                        monitored_case, changes_detected, cost_cents
                    )
                else:
                    await self._handle_failed_check(scheduled_check, monitored_case)
        
        except Exception as e:
            logger.error(f"Check execution failed for {monitor_id}: {str(e)}")
            await self._handle_failed_check(scheduled_check, None)
        
        finally:
            # Remove from active checks
            self.active_checks.discard(monitor_id)
    
    async def _perform_pacer_check(
        self, 
        monitored_case: MonitoredCase
    ) -> Tuple[bool, int, bool]:
        """Perform the actual PACER check"""
        
        try:
            # Get current docket report
            result = await pacer_gateway.get_docket_report(
                case_number=monitored_case.case_number,
                court_id=monitored_case.court_id,
                include_documents=True,
                user_id=monitored_case.created_by
            )
            
            if not result.get('success', False):
                logger.error(f"PACER check failed: {result.get('error', 'Unknown error')}")
                return False, 0, False
            
            # Extract data
            current_docket_entries = result.get('docket_entries', [])
            current_case_info = result.get('case_info', {})
            cost_cents = int(result.get('cost_dollars', 0) * 100)
            
            # Quick change detection
            has_changes = change_detector.quick_change_check(
                monitored_case, current_docket_entries
            )
            
            if has_changes:
                # Perform full change analysis
                delta_analysis = change_detector.analyze_changes(
                    monitored_case, 
                    {'docket_entries': current_docket_entries},
                    current_case_info
                )
                
                # Update cached data
                monitored_case.cached_docket_entries = current_docket_entries
                monitored_case.cached_case_info = current_case_info
                monitored_case.cached_docket_hash = change_detector.calculate_docket_hash(
                    current_docket_entries
                )
                
                # Process detected changes
                if delta_analysis.detected_changes:
                    await self._process_detected_changes(
                        monitored_case, delta_analysis.detected_changes
                    )
                
                logger.info(
                    f"Changes detected for case {monitored_case.case_number}: "
                    f"{len(delta_analysis.detected_changes)} changes"
                )
                
                return True, cost_cents, True
            else:
                logger.debug(f"No changes detected for case {monitored_case.case_number}")
                return True, cost_cents, False
            
        except Exception as e:
            logger.error(f"PACER check failed: {str(e)}")
            return False, 0, False
    
    async def _process_detected_changes(
        self,
        monitored_case: MonitoredCase,
        changes: List[Any]  # ChangeDetection objects
    ):
        """Process detected changes and trigger notifications"""
        
        try:
            from .notifier import notification_manager
            
            for change in changes:
                # Store change detection
                await self._store_change_detection(change)
                
                # Generate notifications
                await notification_manager.process_change(
                    change, monitored_case.monitoring_rules
                )
            
        except Exception as e:
            logger.error(f"Change processing failed: {str(e)}")
    
    async def _handle_successful_check(
        self,
        monitored_case: MonitoredCase,
        changes_detected: bool,
        cost_cents: int
    ):
        """Handle successful monitoring check"""
        
        try:
            # Update monitored case
            monitored_case.update_after_check(
                found_changes=changes_detected,
                cost_cents=cost_cents
            )
            
            # Schedule next check
            await self.schedule_check(monitored_case)
            
            # Update case in storage
            await self._update_monitored_case(monitored_case)
            
        except Exception as e:
            logger.error(f"Successful check handling failed: {str(e)}")
    
    async def _handle_failed_check(
        self,
        scheduled_check: ScheduledCheck,
        monitored_case: Optional[MonitoredCase]
    ):
        """Handle failed monitoring check"""
        
        try:
            if scheduled_check.retry_count < self.config.max_retries:
                # Schedule retry
                scheduled_check.retry_count += 1
                scheduled_check.scheduled_time = datetime.now(timezone.utc) + timedelta(
                    minutes=self.config.retry_delay_minutes * scheduled_check.retry_count
                )
                
                heapq.heappush(self.check_queue, scheduled_check)
                
                logger.info(
                    f"Scheduled retry {scheduled_check.retry_count} for case {scheduled_check.case_number}"
                )
            else:
                # Max retries reached
                if monitored_case:
                    monitored_case.status = MonitorStatus.ERROR
                    monitored_case.update_after_check(error="Max retries exceeded")
                    await self._update_monitored_case(monitored_case)
                
                logger.error(
                    f"Max retries exceeded for case {scheduled_check.case_number}"
                )
            
        except Exception as e:
            logger.error(f"Failed check handling failed: {str(e)}")
    
    async def _can_execute_check(self, scheduled_check: ScheduledCheck) -> bool:
        """Check if a monitoring check can be executed"""
        
        try:
            # Check cost limits
            current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
            hourly_cost = self.hourly_cost_tracking.get(current_hour, 0)
            
            if hourly_cost >= self.config.cost_limit_per_hour_cents:
                logger.warning(f"Hourly cost limit reached: ${hourly_cost/100:.2f}")
                return False
            
            # Check if already active
            if scheduled_check.monitor_id in self.active_checks:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Check execution validation failed: {str(e)}")
            return False
    
    async def _update_check_statistics(
        self,
        success: bool,
        cost_cents: int,
        changes_detected: bool,
        scheduled_check: ScheduledCheck
    ):
        """Update monitoring statistics"""
        
        try:
            self.stats.total_checks_today += 1
            self.stats.total_cost_today_cents += cost_cents
            
            if changes_detected:
                self.stats.total_changes_today += 1
            
            # Update hourly cost tracking
            current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
            if current_hour not in self.hourly_cost_tracking:
                self.hourly_cost_tracking[current_hour] = 0
            self.hourly_cost_tracking[current_hour] += cost_cents
            
            # Update statistics
            if self.stats.total_checks_today > 0:
                self.stats.change_detection_rate = (
                    self.stats.total_changes_today / self.stats.total_checks_today
                ) * 100
            
            if self.stats.total_changes_today > 0:
                self.stats.cost_per_change_cents = (
                    self.stats.total_cost_today_cents / self.stats.total_changes_today
                )
            
        except Exception as e:
            logger.error(f"Statistics update failed: {str(e)}")
    
    async def _cleanup_loop(self):
        """Cleanup loop for maintaining scheduler health"""
        
        try:
            while self.is_running:
                # Clean up old hourly cost tracking
                current_time = datetime.now(timezone.utc)
                cutoff_time = current_time - timedelta(hours=25)  # Keep 25 hours
                cutoff_hour = cutoff_time.strftime("%Y-%m-%d-%H")
                
                keys_to_remove = [
                    hour for hour in self.hourly_cost_tracking.keys()
                    if hour < cutoff_hour
                ]
                
                for hour in keys_to_remove:
                    del self.hourly_cost_tracking[hour]
                
                # Clean up completed checks from queue
                temp_queue = []
                now = datetime.now(timezone.utc)
                
                while self.check_queue:
                    check = heapq.heappop(self.check_queue)
                    # Keep checks that are recent or future
                    if (now - check.scheduled_time).total_seconds() < 3600:  # 1 hour
                        temp_queue.append(check)
                
                for check in temp_queue:
                    heapq.heappush(self.check_queue, check)
                
                # Sleep for 1 hour before next cleanup
                await asyncio.sleep(3600)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Cleanup loop failed: {str(e)}")
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        
        return {
            "is_running": self.is_running,
            "queued_checks": len(self.check_queue),
            "active_checks": len(self.active_checks),
            "hourly_cost_cents": sum(self.hourly_cost_tracking.values()),
            "statistics": {
                "total_checks_today": self.stats.total_checks_today,
                "total_changes_today": self.stats.total_changes_today,
                "total_cost_today_dollars": self.stats.total_cost_today_dollars,
                "change_detection_rate": self.stats.change_detection_rate,
                "cost_per_change_cents": self.stats.cost_per_change_cents
            },
            "config": {
                "max_concurrent_checks": self.config.max_concurrent_checks,
                "cost_limit_per_hour_cents": self.config.cost_limit_per_hour_cents,
                "batch_size": self.config.batch_size
            }
        }
    
    # Placeholder methods for data persistence (implement based on your storage)
    async def _get_monitored_case(self, monitor_id: str) -> Optional[MonitoredCase]:
        """Get monitored case from storage"""
        # TODO: Implement based on your storage backend
        cached_case = await cache_manager.get(f"monitor:case:{monitor_id}")
        if cached_case:
            return MonitoredCase(**cached_case)
        return None
    
    async def _update_monitored_case(self, monitored_case: MonitoredCase):
        """Update monitored case in storage"""
        # TODO: Implement based on your storage backend
        await cache_manager.set(
            f"monitor:case:{monitored_case.monitor_id}",
            monitored_case.__dict__,
            ttl=86400
        )
    
    async def _store_change_detection(self, change_detection: Any):
        """Store change detection in storage"""
        # TODO: Implement based on your storage backend
        await cache_manager.set(
            f"monitor:change:{change_detection.change_id}",
            change_detection.__dict__,
            ttl=86400 * 7  # Keep for a week
        )


# Global scheduler instance
monitor_scheduler = MonitorScheduler()