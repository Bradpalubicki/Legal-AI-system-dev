"""
Main Case Monitor Controller

Orchestrates the entire case monitoring system including scheduler,
detector, notifier, and analytics components. Provides the main API
for managing case monitoring operations.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import uuid

from ..shared.utils.cache_manager import cache_manager
from ..pacer_gateway.gateway import pacer_gateway
from .models import (
    MonitoredCase, MonitoringRule, MonitorStatus, MonitoringFrequency,
    AlertSeverity, ChangeType, NotificationChannel, MonitoringStatistics,
    MonitoringAlert, get_default_rules, create_custom_rule
)
from .scheduler import monitor_scheduler, ScheduleConfig
from .detector import change_detector
from .notifier import notification_manager, NotificationConfig
from .analytics import MonitoringAnalytics


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """Configuration for the case monitor"""
    scheduler_config: ScheduleConfig = None
    notification_config: NotificationConfig = None
    enable_analytics: bool = True
    enable_cost_optimization: bool = True
    auto_adjust_frequency: bool = True
    max_monitored_cases: int = 1000
    default_monitoring_frequency: MonitoringFrequency = MonitoringFrequency.EVERY_15_MIN
    default_cost_limit_cents: int = 10000  # $100 per case
    enable_smart_notifications: bool = True
    duplicate_detection_window_hours: int = 24


class CaseMonitor:
    """Main case monitoring controller"""
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        
        # Initialize components
        self.scheduler = monitor_scheduler
        self.detector = change_detector
        self.notifier = notification_manager
        self.analytics = MonitoringAnalytics()
        
        # Storage
        self.monitored_cases: Dict[str, MonitoredCase] = {}
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        self.active_alerts: List[MonitoringAlert] = []
        
        # Load default rules
        self._load_default_rules()
        
        # Statistics
        self.statistics = MonitoringStatistics()
        
        # Service state
        self.is_running = False
        
        logger.info("Case Monitor initialized")
    
    async def start(self):
        """Start the case monitoring system"""
        
        if self.is_running:
            logger.warning("Case Monitor is already running")
            return
        
        try:
            # Start components
            await self.scheduler.start()
            await self.notifier.start()
            
            # Load existing monitored cases
            await self._load_monitored_cases()
            
            # Schedule initial checks
            await self._schedule_initial_checks()
            
            # Start maintenance tasks
            asyncio.create_task(self._maintenance_loop())
            asyncio.create_task(self._statistics_update_loop())
            
            self.is_running = True
            
            logger.info(
                f"Case Monitor started - monitoring {len(self.monitored_cases)} cases"
            )
            
        except Exception as e:
            logger.error(f"Failed to start Case Monitor: {str(e)}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the case monitoring system"""
        
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            
            # Stop components
            await self.scheduler.stop()
            await self.notifier.stop()
            
            # Save state
            await self._save_monitored_cases()
            
            logger.info("Case Monitor stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop Case Monitor: {str(e)}")
    
    async def add_monitored_case(
        self,
        case_number: str,
        court_id: str,
        case_title: str = "",
        monitoring_rules: List[str] = None,
        frequency: MonitoringFrequency = None,
        priority: int = 1,
        cost_limit_cents: int = None,
        created_by: int = None,
        assigned_to: List[int] = None,
        tags: List[str] = None
    ) -> MonitoredCase:
        """Add a case to monitoring"""
        
        try:
            # Validate inputs
            if not case_number or not court_id:
                raise ValueError("Case number and court ID are required")
            
            # Check if already monitored
            existing_monitor = await self._find_existing_monitor(case_number, court_id)
            if existing_monitor:
                logger.warning(f"Case {case_number} is already being monitored")
                return existing_monitor
            
            # Check limits
            if len(self.monitored_cases) >= self.config.max_monitored_cases:
                raise ValueError(f"Maximum number of monitored cases ({self.config.max_monitored_cases}) reached")
            
            # Create monitored case
            monitor_id = str(uuid.uuid4())
            
            monitored_case = MonitoredCase(
                monitor_id=monitor_id,
                case_number=case_number,
                court_id=court_id,
                case_title=case_title,
                monitoring_rules=monitoring_rules or ["new_filing", "motion_filed", "order_entered"],
                frequency=frequency or self.config.default_monitoring_frequency,
                priority=priority,
                cost_limit_cents=cost_limit_cents or self.config.default_cost_limit_cents,
                created_by=created_by,
                assigned_to=assigned_to or [],
                tags=tags or []
            )
            
            # Get initial case data
            await self._initialize_case_data(monitored_case)
            
            # Store monitored case
            self.monitored_cases[monitor_id] = monitored_case
            await self._save_monitored_case(monitored_case)
            
            # Schedule monitoring
            await self.scheduler.schedule_check(monitored_case)
            
            # Update statistics
            self.statistics.total_monitored_cases += 1
            self.statistics.active_monitors += 1
            
            logger.info(
                f"Added case {case_number} to monitoring with {len(monitored_case.monitoring_rules)} rules"
            )
            
            return monitored_case
            
        except Exception as e:
            logger.error(f"Failed to add monitored case: {str(e)}")
            raise
    
    async def remove_monitored_case(self, monitor_id: str) -> bool:
        """Remove a case from monitoring"""
        
        try:
            if monitor_id not in self.monitored_cases:
                logger.warning(f"Monitor {monitor_id} not found")
                return False
            
            monitored_case = self.monitored_cases[monitor_id]
            
            # Update status
            monitored_case.status = MonitorStatus.STOPPED
            
            # Remove from active monitoring
            del self.monitored_cases[monitor_id]
            
            # Clean up storage
            await self._delete_monitored_case(monitor_id)
            
            # Update statistics
            self.statistics.total_monitored_cases -= 1
            self.statistics.active_monitors -= 1
            
            logger.info(f"Removed case {monitored_case.case_number} from monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove monitored case: {str(e)}")
            return False
    
    async def update_monitoring_rules(
        self,
        monitor_id: str,
        rule_ids: List[str]
    ) -> bool:
        """Update monitoring rules for a case"""
        
        try:
            if monitor_id not in self.monitored_cases:
                return False
            
            monitored_case = self.monitored_cases[monitor_id]
            
            # Validate rules exist
            valid_rules = []
            for rule_id in rule_ids:
                if rule_id in self.monitoring_rules:
                    valid_rules.append(rule_id)
                else:
                    logger.warning(f"Monitoring rule not found: {rule_id}")
            
            # Update rules
            monitored_case.monitoring_rules = valid_rules
            
            # Save changes
            await self._save_monitored_case(monitored_case)
            
            logger.info(
                f"Updated monitoring rules for case {monitored_case.case_number}: "
                f"{len(valid_rules)} rules"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update monitoring rules: {str(e)}")
            return False
    
    async def pause_monitoring(self, monitor_id: str) -> bool:
        """Pause monitoring for a case"""
        
        try:
            if monitor_id not in self.monitored_cases:
                return False
            
            monitored_case = self.monitored_cases[monitor_id]
            monitored_case.status = MonitorStatus.PAUSED
            
            await self._save_monitored_case(monitored_case)
            
            # Update statistics
            self.statistics.active_monitors -= 1
            self.statistics.paused_monitors += 1
            
            logger.info(f"Paused monitoring for case {monitored_case.case_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause monitoring: {str(e)}")
            return False
    
    async def resume_monitoring(self, monitor_id: str) -> bool:
        """Resume monitoring for a case"""
        
        try:
            if monitor_id not in self.monitored_cases:
                return False
            
            monitored_case = self.monitored_cases[monitor_id]
            monitored_case.status = MonitorStatus.ACTIVE
            
            # Schedule next check
            await self.scheduler.schedule_check(monitored_case)
            
            await self._save_monitored_case(monitored_case)
            
            # Update statistics
            self.statistics.active_monitors += 1
            self.statistics.paused_monitors -= 1
            
            logger.info(f"Resumed monitoring for case {monitored_case.case_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume monitoring: {str(e)}")
            return False
    
    async def add_monitoring_rule(self, rule: MonitoringRule) -> bool:
        """Add a custom monitoring rule"""
        
        try:
            if rule.rule_id in self.monitoring_rules:
                logger.warning(f"Rule {rule.rule_id} already exists")
                return False
            
            self.monitoring_rules[rule.rule_id] = rule
            await self._save_monitoring_rule(rule)
            
            logger.info(f"Added monitoring rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add monitoring rule: {str(e)}")
            return False
    
    async def get_monitored_case(self, monitor_id: str) -> Optional[MonitoredCase]:
        """Get monitored case by ID"""
        
        try:
            if monitor_id in self.monitored_cases:
                return self.monitored_cases[monitor_id]
            
            # Try loading from storage
            return await self._load_monitored_case(monitor_id)
            
        except Exception as e:
            logger.error(f"Failed to get monitored case: {str(e)}")
            return None
    
    async def search_monitored_cases(
        self,
        court_id: str = None,
        case_number: str = None,
        status: MonitorStatus = None,
        created_by: int = None,
        tags: List[str] = None
    ) -> List[MonitoredCase]:
        """Search monitored cases with filters"""
        
        try:
            filtered_cases = []
            
            for case in self.monitored_cases.values():
                # Apply filters
                if court_id and case.court_id != court_id:
                    continue
                if case_number and case_number not in case.case_number:
                    continue
                if status and case.status != status:
                    continue
                if created_by and case.created_by != created_by:
                    continue
                if tags and not any(tag in case.tags for tag in tags):
                    continue
                
                filtered_cases.append(case)
            
            return filtered_cases
            
        except Exception as e:
            logger.error(f"Failed to search monitored cases: {str(e)}")
            return []
    
    async def get_monitoring_statistics(self) -> MonitoringStatistics:
        """Get current monitoring statistics"""
        
        try:
            # Update real-time statistics
            active_count = sum(1 for case in self.monitored_cases.values() if case.is_active)
            paused_count = sum(1 for case in self.monitored_cases.values() if case.status == MonitorStatus.PAUSED)
            error_count = sum(1 for case in self.monitored_cases.values() if case.status == MonitorStatus.ERROR)
            
            self.statistics.total_monitored_cases = len(self.monitored_cases)
            self.statistics.active_monitors = active_count
            self.statistics.paused_monitors = paused_count
            self.statistics.error_monitors = error_count
            
            # Get scheduler statistics
            scheduler_status = await self.scheduler.get_scheduler_status()
            scheduler_stats = scheduler_status.get('statistics', {})
            
            self.statistics.total_checks_today = scheduler_stats.get('total_checks_today', 0)
            self.statistics.total_changes_today = scheduler_stats.get('total_changes_today', 0)
            self.statistics.total_cost_today_cents = scheduler_stats.get('total_cost_today_dollars', 0) * 100
            self.statistics.change_detection_rate = scheduler_stats.get('change_detection_rate', 0)
            
            return self.statistics
            
        except Exception as e:
            logger.error(f"Failed to get monitoring statistics: {str(e)}")
            return self.statistics
    
    async def generate_monitoring_report(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        include_analytics: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=7)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            report = {
                "report_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "statistics": await self.get_monitoring_statistics(),
                "monitored_cases_summary": await self._get_cases_summary(),
                "recent_changes": await self._get_recent_changes(start_date, end_date),
                "cost_analysis": await self._get_cost_analysis(start_date, end_date),
                "alert_summary": await self._get_alert_summary(start_date, end_date)
            }
            
            if include_analytics and self.config.enable_analytics:
                report["analytics"] = await self.analytics.generate_report(start_date, end_date)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate monitoring report: {str(e)}")
            return {"error": str(e)}
    
    async def _initialize_case_data(self, monitored_case: MonitoredCase):
        """Initialize case data for monitoring"""
        
        try:
            # Get initial docket data
            result = await pacer_gateway.get_docket_report(
                case_number=monitored_case.case_number,
                court_id=monitored_case.court_id,
                include_documents=False,  # Don't get documents initially
                user_id=monitored_case.created_by
            )
            
            if result.get('success', False):
                # Store initial data
                monitored_case.cached_docket_entries = result.get('docket_entries', [])
                monitored_case.cached_case_info = result.get('case_info', {})
                monitored_case.cached_docket_hash = self.detector.calculate_docket_hash(
                    monitored_case.cached_docket_entries
                )
                
                # Update case title if not provided
                if not monitored_case.case_title and result.get('case_info', {}).get('case_title'):
                    monitored_case.case_title = result['case_info']['case_title']
                
                # Track initial cost
                initial_cost = int(result.get('cost_dollars', 0) * 100)
                monitored_case.total_cost_cents += initial_cost
                
                logger.info(f"Initialized case data for {monitored_case.case_number}")
            else:
                logger.warning(f"Failed to initialize case data: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Case data initialization failed: {str(e)}")
    
    def _load_default_rules(self):
        """Load default monitoring rules"""
        
        try:
            default_rules = get_default_rules()
            
            for rule in default_rules:
                self.monitoring_rules[rule.rule_id] = rule
            
            logger.info(f"Loaded {len(default_rules)} default monitoring rules")
            
        except Exception as e:
            logger.error(f"Failed to load default rules: {str(e)}")
    
    async def _schedule_initial_checks(self):
        """Schedule initial monitoring checks for all active cases"""
        
        try:
            active_cases = [case for case in self.monitored_cases.values() if case.is_active]
            
            if active_cases:
                await self.scheduler.schedule_bulk_checks(active_cases)
                logger.info(f"Scheduled initial checks for {len(active_cases)} cases")
            
        except Exception as e:
            logger.error(f"Failed to schedule initial checks: {str(e)}")
    
    async def _maintenance_loop(self):
        """Maintenance loop for system health"""
        
        try:
            while self.is_running:
                # Clean up old alerts
                await self._cleanup_old_alerts()
                
                # Check for stuck monitors
                await self._check_stuck_monitors()
                
                # Optimize monitoring frequencies
                if self.config.auto_adjust_frequency:
                    await self._optimize_monitoring_frequencies()
                
                # Generate system alerts
                await self._check_system_health()
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Maintenance loop failed: {str(e)}")
    
    async def _statistics_update_loop(self):
        """Update statistics periodically"""
        
        try:
            while self.is_running:
                await self.get_monitoring_statistics()
                await asyncio.sleep(300)  # Update every 5 minutes
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Statistics update loop failed: {str(e)}")
    
    # Placeholder methods for data persistence
    async def _load_monitored_cases(self):
        """Load monitored cases from storage"""
        # TODO: Implement based on your storage backend
        pass
    
    async def _save_monitored_cases(self):
        """Save all monitored cases to storage"""
        # TODO: Implement based on your storage backend
        pass
    
    async def _save_monitored_case(self, monitored_case: MonitoredCase):
        """Save single monitored case to storage"""
        await cache_manager.set(
            f"monitor:case:{monitored_case.monitor_id}",
            monitored_case.__dict__,
            ttl=86400 * 7  # Keep for a week
        )
    
    async def _load_monitored_case(self, monitor_id: str) -> Optional[MonitoredCase]:
        """Load single monitored case from storage"""
        cached_case = await cache_manager.get(f"monitor:case:{monitor_id}")
        if cached_case:
            return MonitoredCase(**cached_case)
        return None
    
    async def _delete_monitored_case(self, monitor_id: str):
        """Delete monitored case from storage"""
        await cache_manager.delete(f"monitor:case:{monitor_id}")
    
    async def _save_monitoring_rule(self, rule: MonitoringRule):
        """Save monitoring rule to storage"""
        await cache_manager.set(
            f"monitor:rule:{rule.rule_id}",
            rule.__dict__,
            ttl=86400 * 30  # Keep for a month
        )
    
    async def _find_existing_monitor(self, case_number: str, court_id: str) -> Optional[MonitoredCase]:
        """Find existing monitor for case"""
        for case in self.monitored_cases.values():
            if case.case_number == case_number and case.court_id == court_id:
                return case
        return None
    
    async def _get_cases_summary(self) -> Dict[str, Any]:
        """Get summary of monitored cases"""
        return {
            "total_cases": len(self.monitored_cases),
            "by_status": {
                status.value: sum(1 for case in self.monitored_cases.values() if case.status == status)
                for status in MonitorStatus
            },
            "by_court": {},  # TODO: Implement
            "by_priority": {}  # TODO: Implement
        }
    
    async def _get_recent_changes(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get recent changes in the date range"""
        # TODO: Implement based on your change detection storage
        return []
    
    async def _get_cost_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get cost analysis for the period"""
        total_cost = sum(case.total_cost_cents for case in self.monitored_cases.values())
        return {
            "total_cost_dollars": total_cost / 100.0,
            "average_cost_per_case": total_cost / max(1, len(self.monitored_cases)) / 100.0,
            "cost_by_court": {}  # TODO: Implement
        }
    
    async def _get_alert_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get alert summary for the period"""
        return {
            "total_alerts": len(self.active_alerts),
            "by_severity": {},  # TODO: Implement
            "acknowledged_alerts": sum(1 for alert in self.active_alerts if alert.is_acknowledged)
        }
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.created_at > cutoff
        ]
    
    async def _check_stuck_monitors(self):
        """Check for monitors that might be stuck"""
        now = datetime.now(timezone.utc)
        
        for case in self.monitored_cases.values():
            if case.is_active and case.last_checked_at:
                hours_since_check = (now - case.last_checked_at).total_seconds() / 3600
                expected_interval_hours = 0.25  # 15 minutes
                
                # Convert frequency to hours
                if case.frequency == MonitoringFrequency.EVERY_15_MIN:
                    expected_interval_hours = 0.25
                elif case.frequency == MonitoringFrequency.EVERY_30_MIN:
                    expected_interval_hours = 0.5
                elif case.frequency == MonitoringFrequency.HOURLY:
                    expected_interval_hours = 1.0
                
                # Check if stuck (3x expected interval)
                if hours_since_check > expected_interval_hours * 3:
                    logger.warning(f"Monitor may be stuck: {case.case_number} (last check: {hours_since_check:.1f}h ago)")
    
    async def _optimize_monitoring_frequencies(self):
        """Optimize monitoring frequencies based on activity"""
        # TODO: Implement intelligent frequency optimization
        pass
    
    async def _check_system_health(self):
        """Check overall system health and generate alerts"""
        # TODO: Implement system health monitoring
        pass


# Global case monitor instance
case_monitor = CaseMonitor()