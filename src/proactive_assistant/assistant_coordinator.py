"""
Proactive Assistant Coordinator

Central coordination service that orchestrates all proactive assistant components
and provides unified interface for 24/7 legal case monitoring and assistance.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

from .case_monitor import CaseMonitor, CaseAlert
from .deadline_tracker import DeadlineTracker, DeadlineAlert
from .document_watcher import DocumentWatcher, DocumentAlert
from .intelligent_alerts import (
    IntelligentAlertsEngine, IntelligentAlert, AlertSource,
    AlertClassification, RiskLevel
)
from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class AssistantStatus(str, Enum):
    """Status of the proactive assistant."""
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class SystemHealth(str, Enum):
    """Overall system health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class AssistantMetrics:
    """Comprehensive metrics for the assistant system."""
    status: AssistantStatus
    health: SystemHealth
    uptime_seconds: int
    total_alerts_processed: int
    active_alerts: int
    critical_alerts: int
    
    # Component status
    case_monitor_active: bool
    deadline_tracker_active: bool
    document_watcher_active: bool
    
    # Performance metrics
    alerts_last_hour: int
    avg_processing_time_ms: float
    error_rate: float
    
    # Resource utilization
    memory_usage_mb: float
    cpu_usage_percent: float
    
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AssistantSummary:
    """High-level summary for dashboard display."""
    total_cases_monitored: int
    upcoming_deadlines_7d: int
    overdue_deadlines: int
    critical_alerts: int
    documents_watched: int
    recent_activity: List[Dict[str, Any]] = field(default_factory=list)
    top_priorities: List[Dict[str, Any]] = field(default_factory=list)
    system_recommendations: List[str] = field(default_factory=list)


class ProactiveAssistantCoordinator:
    """
    Central coordinator for the proactive legal assistant system.
    """
    
    def __init__(self):
        # Core components
        self.case_monitor = CaseMonitor()
        self.deadline_tracker = DeadlineTracker()
        self.document_watcher = DocumentWatcher()
        self.intelligent_alerts = IntelligentAlertsEngine()
        
        # Coordinator state
        self.status = AssistantStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.error_count = 0
        self.processed_alerts_count = 0
        self.alert_processing_times: List[float] = []
        
        # Configuration
        self.coordination_interval = 60  # 1 minute
        self.health_check_interval = 300  # 5 minutes
        self.max_errors_before_pause = 5
        
        # Background tasks
        self.coordination_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
    async def start_assistant(self):
        """Start the complete proactive assistant system."""
        if self.status in [AssistantStatus.ACTIVE, AssistantStatus.STARTING]:
            logger.warning("Assistant already running or starting")
            return
            
        logger.info("Starting Proactive Legal Assistant")
        self.status = AssistantStatus.STARTING
        self.start_time = datetime.utcnow()
        self.error_count = 0
        
        try:
            # Start all monitoring components
            await self._start_components()
            
            # Start coordination loop
            self.coordination_task = asyncio.create_task(self._coordination_loop())
            
            # Start health monitoring
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.status = AssistantStatus.ACTIVE
            logger.info("Proactive Legal Assistant started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start assistant: {str(e)}")
            self.status = AssistantStatus.ERROR
            await self.stop_assistant()
            raise
            
    async def stop_assistant(self):
        """Stop the proactive assistant system."""
        if self.status == AssistantStatus.STOPPED:
            return
            
        logger.info("Stopping Proactive Legal Assistant")
        self.status = AssistantStatus.STOPPING
        
        try:
            # Cancel background tasks
            if self.coordination_task and not self.coordination_task.done():
                self.coordination_task.cancel()
                try:
                    await self.coordination_task
                except asyncio.CancelledError:
                    pass
                    
            if self.health_check_task and not self.health_check_task.done():
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
                    
            # Stop all components
            await self._stop_components()
            
            self.status = AssistantStatus.STOPPED
            logger.info("Proactive Legal Assistant stopped")
            
        except Exception as e:
            logger.error(f"Error stopping assistant: {str(e)}")
            self.status = AssistantStatus.ERROR
            
    async def pause_assistant(self):
        """Temporarily pause the assistant."""
        if self.status == AssistantStatus.ACTIVE:
            logger.info("Pausing Proactive Legal Assistant")
            self.status = AssistantStatus.PAUSED
            
    async def resume_assistant(self):
        """Resume the assistant from paused state."""
        if self.status == AssistantStatus.PAUSED:
            logger.info("Resuming Proactive Legal Assistant")
            self.status = AssistantStatus.ACTIVE
            
    async def _start_components(self):
        """Start all monitoring components."""
        logger.info("Starting monitoring components")
        
        # Start components in parallel for faster startup
        await asyncio.gather(
            self.case_monitor.start_monitoring(),
            self.deadline_tracker.start_tracking(),
            self.document_watcher.start_watching()
        )
        
        logger.info("All monitoring components started")
        
    async def _stop_components(self):
        """Stop all monitoring components."""
        logger.info("Stopping monitoring components")
        
        await asyncio.gather(
            self.case_monitor.stop_monitoring(),
            self.deadline_tracker.stop_tracking(),
            self.document_watcher.stop_watching(),
            return_exceptions=True  # Continue even if some components fail to stop
        )
        
        logger.info("All monitoring components stopped")
        
    async def _coordination_loop(self):
        """Main coordination loop that processes alerts and coordinates components."""
        logger.info("Starting coordination loop")
        
        while self.status in [AssistantStatus.ACTIVE, AssistantStatus.PAUSED]:
            try:
                if self.status == AssistantStatus.ACTIVE:
                    await self._coordination_cycle()
                    
                await asyncio.sleep(self.coordination_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in coordination loop: {str(e)}")
                self.error_count += 1
                
                if self.error_count >= self.max_errors_before_pause:
                    logger.critical("Too many errors, pausing assistant")
                    await self.pause_assistant()
                    
                await asyncio.sleep(60)  # Wait before retry
                
        logger.info("Coordination loop stopped")
        
    async def _coordination_cycle(self):
        """Execute one coordination cycle."""
        start_time = datetime.utcnow()
        
        # Collect alerts from all components
        alerts_processed = 0
        
        # Process case monitor alerts
        case_alerts = await self.case_monitor.get_case_alerts()
        for alert in case_alerts:
            if not getattr(alert, '_processed_by_coordinator', False):
                await self._process_component_alert(AlertSource.CASE_MONITOR, alert)
                alert._processed_by_coordinator = True
                alerts_processed += 1
                
        # Process deadline tracker alerts
        deadline_alerts = await self.deadline_tracker.get_deadline_alerts()
        for alert in deadline_alerts:
            if not getattr(alert, '_processed_by_coordinator', False):
                await self._process_component_alert(AlertSource.DEADLINE_TRACKER, alert)
                alert._processed_by_coordinator = True
                alerts_processed += 1
                
        # Process document watcher alerts
        document_alerts = await self.document_watcher.get_document_alerts()
        for alert in document_alerts:
            if not getattr(alert, '_processed_by_coordinator', False):
                await self._process_component_alert(AlertSource.DOCUMENT_WATCHER, alert)
                alert._processed_by_coordinator = True
                alerts_processed += 1
                
        # Update metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.alert_processing_times.append(processing_time)
        
        # Keep only recent processing times (last 100)
        if len(self.alert_processing_times) > 100:
            self.alert_processing_times = self.alert_processing_times[-100:]
            
        self.processed_alerts_count += alerts_processed
        
        if alerts_processed > 0:
            logger.debug(f"Coordination cycle processed {alerts_processed} alerts in {processing_time:.1f}ms")
            
    async def _process_component_alert(self, source: AlertSource, alert: Any):
        """Process an alert from a component through the intelligent alerts engine."""
        try:
            # Get context for the alert
            context = await self._get_alert_context(alert)
            
            # Process through intelligent alerts engine
            intelligent_alert = await self.intelligent_alerts.process_alert(
                source, alert, context
            )
            
            # Execute any needed actions based on priority
            await self._handle_high_priority_alert(intelligent_alert)
            
        except Exception as e:
            logger.error(f"Error processing {source} alert: {str(e)}")
            self.error_count += 1
            
    async def _get_alert_context(self, alert: Any) -> Dict[str, Any]:
        """Get context information for an alert."""
        context = {}
        
        # Add case context if available
        if hasattr(alert, 'case_id') and alert.case_id:
            case_context = await self._get_case_context(alert.case_id)
            context.update(case_context)
            
        # Add timing context
        context.update({
            "current_hour": datetime.utcnow().hour,
            "is_business_hours": 9 <= datetime.utcnow().hour < 18,
            "day_of_week": datetime.utcnow().weekday()
        })
        
        return context
        
    async def _get_case_context(self, case_id: int) -> Dict[str, Any]:
        """Get context information for a case."""
        # In production, this would query the database for case details
        return {
            "case_id": case_id,
            "case_type": "litigation",  # Would be fetched from DB
            "case_stage": "discovery",   # Would be fetched from DB
            "case_complexity": 0.7,     # Would be calculated
            "case_value": 500000,       # Would be fetched from DB
            "client_vip": False,        # Would be fetched from DB
            "attorney_workload": 0.6    # Would be calculated
        }
        
    async def _handle_high_priority_alert(self, intelligent_alert: IntelligentAlert):
        """Handle high-priority alerts that need immediate attention."""
        if intelligent_alert.risk_assessment.risk_level == RiskLevel.CRITICAL:
            logger.critical(f"CRITICAL ALERT: {intelligent_alert.classification} - Priority: {intelligent_alert.priority_score}")
            
            # Would send immediate notifications here
            # Would create urgent tasks here
            # Would escalate to appropriate personnel here
            
        elif intelligent_alert.priority_score >= 0.8:
            logger.warning(f"HIGH PRIORITY ALERT: {intelligent_alert.classification} - Priority: {intelligent_alert.priority_score}")
            
            # Would send high-priority notifications here
            
    async def _health_check_loop(self):
        """Monitor system health and component status."""
        logger.info("Starting health check loop")
        
        while self.status in [AssistantStatus.ACTIVE, AssistantStatus.PAUSED]:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check: {str(e)}")
                await asyncio.sleep(60)
                
        logger.info("Health check loop stopped")
        
    async def _perform_health_check(self):
        """Perform comprehensive health check."""
        health_issues = []
        
        # Check component status
        if not self.case_monitor.is_monitoring:
            health_issues.append("Case monitor not running")
            
        if not self.deadline_tracker.is_tracking:
            health_issues.append("Deadline tracker not running")
            
        if not self.document_watcher.is_watching:
            health_issues.append("Document watcher not running")
            
        # Check error rate
        if self.error_count > 10:
            health_issues.append("High error rate detected")
            
        # Check memory usage (simplified)
        # Would implement actual memory monitoring in production
        
        # Log health status
        if health_issues:
            logger.warning(f"Health issues detected: {', '.join(health_issues)}")
        else:
            logger.debug("System health check passed")
            
    # Public API methods
    
    async def get_assistant_status(self) -> AssistantStatus:
        """Get current assistant status."""
        return self.status
        
    async def get_assistant_metrics(self) -> AssistantMetrics:
        """Get comprehensive assistant metrics."""
        uptime_seconds = 0
        if self.start_time:
            uptime_seconds = int((datetime.utcnow() - self.start_time).total_seconds())
            
        # Get active alerts from intelligent alerts engine
        active_alerts = await self.intelligent_alerts.get_intelligent_alerts(unresolved_only=True)
        critical_alerts = [a for a in active_alerts if a.risk_assessment.risk_level == RiskLevel.CRITICAL]
        
        # Calculate average processing time
        avg_processing_time = 0.0
        if self.alert_processing_times:
            avg_processing_time = sum(self.alert_processing_times) / len(self.alert_processing_times)
            
        # Calculate error rate
        error_rate = 0.0
        if self.processed_alerts_count > 0:
            error_rate = self.error_count / max(self.processed_alerts_count, 1)
            
        # Determine overall health
        health = SystemHealth.HEALTHY
        if self.error_count > 5:
            health = SystemHealth.DEGRADED
        if self.status == AssistantStatus.ERROR or self.error_count > 20:
            health = SystemHealth.CRITICAL
        if self.status == AssistantStatus.STOPPED:
            health = SystemHealth.OFFLINE
            
        return AssistantMetrics(
            status=self.status,
            health=health,
            uptime_seconds=uptime_seconds,
            total_alerts_processed=self.processed_alerts_count,
            active_alerts=len(active_alerts),
            critical_alerts=len(critical_alerts),
            case_monitor_active=self.case_monitor.is_monitoring,
            deadline_tracker_active=self.deadline_tracker.is_tracking,
            document_watcher_active=self.document_watcher.is_watching,
            alerts_last_hour=0,  # Would calculate from recent alerts
            avg_processing_time_ms=avg_processing_time,
            error_rate=error_rate,
            memory_usage_mb=0.0,  # Would implement actual monitoring
            cpu_usage_percent=0.0  # Would implement actual monitoring
        )
        
    async def get_assistant_summary(self, db: Optional[AsyncSession] = None) -> AssistantSummary:
        """Get high-level assistant summary for dashboard."""
        if not db:
            async with get_db_session() as db:
                return await self._get_assistant_summary_impl(db)
        return await self._get_assistant_summary_impl(db)
        
    async def _get_assistant_summary_impl(self, db: AsyncSession) -> AssistantSummary:
        """Implementation of assistant summary."""
        # Get statistics from components
        deadline_stats = await self.deadline_tracker.get_deadline_statistics(db)
        case_dashboard = await self.case_monitor.get_dashboard_summary()
        document_stats = await self.document_watcher.get_monitoring_statistics()
        alert_stats = await self.intelligent_alerts.get_alert_statistics()
        
        # Get top priority alerts
        top_alerts = await self.intelligent_alerts.get_intelligent_alerts(
            unresolved_only=True, limit=5
        )
        
        top_priorities = []
        for alert in top_alerts:
            top_priorities.append({
                "id": alert.id,
                "classification": alert.classification,
                "priority_score": alert.priority_score,
                "risk_level": alert.risk_assessment.risk_level,
                "created_at": alert.created_at.isoformat()
            })
            
        # Generate recent activity
        recent_activity = []
        
        # Add recent alerts to activity
        recent_alerts = await self.intelligent_alerts.get_intelligent_alerts(
            unresolved_only=False, limit=10
        )
        
        for alert in recent_alerts[-5:]:  # Last 5 alerts
            recent_activity.append({
                "type": "alert",
                "description": f"New {alert.classification} alert processed",
                "timestamp": alert.created_at.isoformat(),
                "priority": alert.risk_assessment.risk_level
            })
            
        # Generate system recommendations
        recommendations = []
        
        if deadline_stats["overdue_deadlines"] > 0:
            recommendations.append(f"Review {deadline_stats['overdue_deadlines']} overdue deadlines immediately")
            
        if alert_stats["active_alerts"] > 20:
            recommendations.append("High alert volume - consider reviewing alert rules")
            
        if case_dashboard["alert_counts"]["critical"] > 5:
            recommendations.append("Multiple critical alerts require immediate attention")
            
        if not recommendations:
            recommendations.append("System operating normally - no immediate actions required")
            
        return AssistantSummary(
            total_cases_monitored=len(case_dashboard.get("monitored_cases", [])),
            upcoming_deadlines_7d=deadline_stats["upcoming_7_days"],
            overdue_deadlines=deadline_stats["overdue_deadlines"],
            critical_alerts=alert_stats["risk_level_breakdown"].get(RiskLevel.CRITICAL, 0),
            documents_watched=document_stats["monitored_documents"],
            recent_activity=recent_activity,
            top_priorities=top_priorities,
            system_recommendations=recommendations
        )
        
    async def acknowledge_alert(self, alert_id: str, user_id: int) -> bool:
        """Acknowledge an alert across all systems."""
        # Try intelligent alerts first
        if await self.intelligent_alerts.acknowledge_alert(alert_id, user_id):
            return True
            
        # Try component-specific acknowledgment
        if await self.case_monitor.acknowledge_alert(alert_id, user_id):
            return True
            
        if await self.deadline_tracker.acknowledge_alert(alert_id):
            return True
            
        if await self.document_watcher.acknowledge_alert(alert_id):
            return True
            
        return False
        
    async def resolve_alert(self, alert_id: str, user_id: int, notes: Optional[str] = None) -> bool:
        """Resolve an alert across all systems."""
        # Try intelligent alerts first
        if await self.intelligent_alerts.resolve_alert(alert_id, user_id, notes):
            return True
            
        # Try component-specific resolution
        if await self.case_monitor.resolve_alert(alert_id, user_id):
            return True
            
        return False
        
    async def get_all_active_alerts(self) -> Dict[str, List[Any]]:
        """Get all active alerts from all components."""
        return {
            "intelligent_alerts": await self.intelligent_alerts.get_intelligent_alerts(unresolved_only=True),
            "case_alerts": await self.case_monitor.get_case_alerts(),
            "deadline_alerts": await self.deadline_tracker.get_deadline_alerts(),
            "document_alerts": await self.document_watcher.get_document_alerts()
        }
        
    async def restart_component(self, component_name: str) -> bool:
        """Restart a specific component."""
        try:
            if component_name == "case_monitor":
                await self.case_monitor.stop_monitoring()
                await asyncio.sleep(1)
                await self.case_monitor.start_monitoring()
                
            elif component_name == "deadline_tracker":
                await self.deadline_tracker.stop_tracking()
                await asyncio.sleep(1)
                await self.deadline_tracker.start_tracking()
                
            elif component_name == "document_watcher":
                await self.document_watcher.stop_watching()
                await asyncio.sleep(1)
                await self.document_watcher.start_watching()
                
            else:
                return False
                
            logger.info(f"Successfully restarted component: {component_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart component {component_name}: {str(e)}")
            return False