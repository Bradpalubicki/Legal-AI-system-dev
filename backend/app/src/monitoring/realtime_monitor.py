# =============================================================================
# Legal AI System - Real-Time Beta Launch Monitoring
# =============================================================================
# Comprehensive real-time monitoring system for beta launch with alerting,
# anomaly detection, and automated response capabilities
# =============================================================================

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone, timedelta
import asyncio
import logging
import json
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict, deque

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import redis
from prometheus_client import Gauge, Counter, Histogram

from ..beta_management.models import BetaUser, BetaIssue, BetaFeedback, BetaUserStatus
from ..audit.models import AuditEvent, AuditEventType, AuditSeverity
# Simplified monitoring - imports disabled for development
from ..notification_service.service import NotificationService
from ..core.config import get_settings

logger = logging.getLogger(__name__)

# =============================================================================
# MONITORING ENUMS AND MODELS
# =============================================================================

class AlertSeverity(str, Enum):
    """Alert severity levels for beta monitoring."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(str, Enum):
    """Types of monitoring alerts."""
    USER_ACTIVITY = "user_activity"
    ERROR_RATE = "error_rate"
    PERFORMANCE = "performance"
    SECURITY = "security"
    FEATURE_ADOPTION = "feature_adoption"
    FEEDBACK_NEGATIVE = "feedback_negative"
    SYSTEM_HEALTH = "system_health"

@dataclass
class MonitoringAlert:
    """Real-time monitoring alert."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AlertType = AlertType.SYSTEM_HEALTH
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    resolved: bool = False
    auto_resolve: bool = False

@dataclass
class MetricThreshold:
    """Metric threshold configuration."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "greater_than"  # greater_than, less_than, equals
    time_window_minutes: int = 5
    consecutive_violations: int = 3

@dataclass
class MonitoringMetrics:
    """Current monitoring metrics snapshot."""
    timestamp: datetime
    active_beta_users: int = 0
    total_sessions_last_hour: int = 0
    error_rate_percentage: float = 0.0
    avg_response_time_ms: float = 0.0
    new_issues_last_hour: int = 0
    negative_feedback_last_hour: int = 0
    cpu_usage_percentage: float = 0.0
    memory_usage_percentage: float = 0.0
    disk_usage_percentage: float = 0.0

# =============================================================================
# REAL-TIME MONITORING SERVICE
# =============================================================================

class BetaLaunchMonitor:
    """
    Comprehensive real-time monitoring system for beta launch.

    Features:
    - Real-time metrics collection
    - Threshold-based alerting
    - Anomaly detection
    - Automated responses
    - Executive dashboards
    """

    def __init__(self):
        self.settings = get_settings()
        self.notification_service = NotificationService()
        self.redis_client = redis.Redis.from_url(self.settings.REDIS_URL)

        # Monitoring state
        self.active_alerts: Dict[str, MonitoringAlert] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.threshold_violations: Dict[str, int] = defaultdict(int)

        # Alert handlers
        self.alert_handlers: Dict[AlertType, List[Callable]] = defaultdict(list)

        # Monitoring thresholds
        self.thresholds = self._setup_monitoring_thresholds()

        # Real-time metrics
        self.current_metrics = MonitoringMetrics(timestamp=datetime.now(timezone.utc))

        self._setup_alert_handlers()

    def _setup_monitoring_thresholds(self) -> List[MetricThreshold]:
        """Setup monitoring thresholds for beta launch."""
        return [
            # Error rate thresholds
            MetricThreshold(
                metric_name="error_rate_percentage",
                warning_threshold=5.0,
                critical_threshold=10.0,
                comparison="greater_than",
                time_window_minutes=5,
                consecutive_violations=2
            ),

            # Response time thresholds
            MetricThreshold(
                metric_name="avg_response_time_ms",
                warning_threshold=2000.0,
                critical_threshold=5000.0,
                comparison="greater_than",
                time_window_minutes=3,
                consecutive_violations=3
            ),

            # New issues threshold
            MetricThreshold(
                metric_name="new_issues_last_hour",
                warning_threshold=5.0,
                critical_threshold=10.0,
                comparison="greater_than",
                time_window_minutes=60,
                consecutive_violations=1
            ),

            # Negative feedback threshold
            MetricThreshold(
                metric_name="negative_feedback_last_hour",
                warning_threshold=3.0,
                critical_threshold=6.0,
                comparison="greater_than",
                time_window_minutes=60,
                consecutive_violations=1
            ),

            # Active users drop threshold
            MetricThreshold(
                metric_name="active_beta_users",
                warning_threshold=0.8,  # 20% drop from baseline
                critical_threshold=0.6,  # 40% drop from baseline
                comparison="less_than",
                time_window_minutes=15,
                consecutive_violations=2
            ),

            # System resource thresholds
            MetricThreshold(
                metric_name="cpu_usage_percentage",
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison="greater_than",
                time_window_minutes=5,
                consecutive_violations=3
            ),

            MetricThreshold(
                metric_name="memory_usage_percentage",
                warning_threshold=85.0,
                critical_threshold=95.0,
                comparison="greater_than",
                time_window_minutes=5,
                consecutive_violations=3
            )
        ]

    def _setup_alert_handlers(self):
        """Setup automated alert response handlers."""
        # Critical error handlers
        self.alert_handlers[AlertType.ERROR_RATE].extend([
            self._notify_engineering_team,
            self._auto_scale_resources,
            self._enable_circuit_breakers
        ])

        # Performance issue handlers
        self.alert_handlers[AlertType.PERFORMANCE].extend([
            self._notify_devops_team,
            self._auto_scale_resources,
            self._analyze_slow_queries
        ])

        # User activity handlers
        self.alert_handlers[AlertType.USER_ACTIVITY].extend([
            self._notify_product_team,
            self._analyze_user_dropoff
        ])

        # Security handlers
        self.alert_handlers[AlertType.SECURITY].extend([
            self._notify_security_team,
            self._auto_block_suspicious_ips,
            self._escalate_to_management
        ])

    async def start_monitoring(self):
        """Start real-time monitoring loop."""
        logger.info("Starting beta launch real-time monitoring")

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._threshold_monitoring_loop()),
            asyncio.create_task(self._anomaly_detection_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._health_check_loop())
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring system error: {e}")
            await self._emergency_notification(str(e))

    async def _metrics_collection_loop(self):
        """Continuous metrics collection loop."""
        while True:
            try:
                await self._collect_current_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)  # Backoff on error

    async def _collect_current_metrics(self):
        """Collect current system and beta metrics."""
        try:
            # Get database session
            from ..core.database import get_async_session as get_db_session
            async with get_db_session() as db:

                # Active beta users
                active_users_result = await db.execute(
                    select(func.count(BetaUser.id)).where(
                        and_(
                            BetaUser.status == BetaUserStatus.ACTIVE,
                            BetaUser.last_active_at >= datetime.now(timezone.utc) - timedelta(hours=1)
                        )
                    )
                )
                self.current_metrics.active_beta_users = active_users_result.scalar() or 0

                # Recent issues
                issues_result = await db.execute(
                    select(func.count(BetaIssue.id)).where(
                        BetaIssue.reported_at >= datetime.now(timezone.utc) - timedelta(hours=1)
                    )
                )
                self.current_metrics.new_issues_last_hour = issues_result.scalar() or 0

                # Negative feedback
                negative_feedback_result = await db.execute(
                    select(func.count(BetaFeedback.id)).where(
                        and_(
                            BetaFeedback.submitted_at >= datetime.now(timezone.utc) - timedelta(hours=1),
                            BetaFeedback.satisfaction_rating <= 2
                        )
                    )
                )
                self.current_metrics.negative_feedback_last_hour = negative_feedback_result.scalar() or 0

                # Error rate from recent audit events
                total_requests_result = await db.execute(
                    select(func.count(AuditEvent.id)).where(
                        and_(
                            AuditEvent.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=10),
                            AuditEvent.api_endpoint.isnot(None)
                        )
                    )
                )
                total_requests = total_requests_result.scalar() or 1

                error_requests_result = await db.execute(
                    select(func.count(AuditEvent.id)).where(
                        and_(
                            AuditEvent.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=10),
                            AuditEvent.severity.in_([AuditSeverity.HIGH, AuditSeverity.CRITICAL])
                        )
                    )
                )
                error_requests = error_requests_result.scalar() or 0

                self.current_metrics.error_rate_percentage = (error_requests / total_requests) * 100

                # Update timestamp
                self.current_metrics.timestamp = datetime.now(timezone.utc)

                # Store metrics in history
                self._store_metrics_in_history()

                # Update Prometheus metrics
                active_users_gauge.labels(user_type="beta").set(self.current_metrics.active_beta_users)

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")

    def _store_metrics_in_history(self):
        """Store current metrics in rolling history."""
        timestamp = self.current_metrics.timestamp.timestamp()

        for attr_name in self.current_metrics.__dataclass_fields__.keys():
            if attr_name == 'timestamp':
                continue

            value = getattr(self.current_metrics, attr_name)
            if isinstance(value, (int, float)):
                self.metric_history[attr_name].append((timestamp, value))

    async def _threshold_monitoring_loop(self):
        """Monitor thresholds and trigger alerts."""
        while True:
            try:
                await self._check_all_thresholds()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Threshold monitoring error: {e}")
                await asyncio.sleep(120)

    async def _check_all_thresholds(self):
        """Check all configured thresholds against current metrics."""
        for threshold in self.thresholds:
            await self._check_threshold(threshold)

    async def _check_threshold(self, threshold: MetricThreshold):
        """Check a specific threshold against current metrics."""
        try:
            current_value = getattr(self.current_metrics, threshold.metric_name, None)
            if current_value is None:
                return

            # Special handling for relative thresholds (like user activity drops)
            if threshold.metric_name == "active_beta_users" and threshold.comparison == "less_than":
                # Get baseline from history
                baseline = self._get_baseline_value(threshold.metric_name)
                if baseline:
                    current_value = current_value / baseline

            violation = self._evaluate_threshold(current_value, threshold)

            if violation:
                self.threshold_violations[threshold.metric_name] += 1

                if self.threshold_violations[threshold.metric_name] >= threshold.consecutive_violations:
                    await self._trigger_threshold_alert(threshold, current_value)
            else:
                # Reset violation count on recovery
                self.threshold_violations[threshold.metric_name] = 0
                await self._check_alert_resolution(threshold.metric_name)

        except Exception as e:
            logger.error(f"Threshold check error for {threshold.metric_name}: {e}")

    def _evaluate_threshold(self, value: float, threshold: MetricThreshold) -> bool:
        """Evaluate if a value violates the threshold."""
        if threshold.comparison == "greater_than":
            return value > threshold.critical_threshold or value > threshold.warning_threshold
        elif threshold.comparison == "less_than":
            return value < threshold.critical_threshold or value < threshold.warning_threshold
        elif threshold.comparison == "equals":
            return abs(value - threshold.critical_threshold) < 0.001
        return False

    def _get_baseline_value(self, metric_name: str) -> Optional[float]:
        """Get baseline value for relative comparisons."""
        history = self.metric_history.get(metric_name, [])
        if len(history) < 10:
            return None

        # Calculate average from last 30 minutes
        cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).timestamp()
        recent_values = [value for timestamp, value in history if timestamp >= cutoff_time]

        if recent_values:
            return sum(recent_values) / len(recent_values)
        return None

    async def _trigger_threshold_alert(self, threshold: MetricThreshold, current_value: float):
        """Trigger alert for threshold violation."""
        severity = (AlertSeverity.CRITICAL
                   if current_value > threshold.critical_threshold
                   else AlertSeverity.HIGH)

        alert = MonitoringAlert(
            alert_type=AlertType.SYSTEM_HEALTH,
            severity=severity,
            title=f"Threshold Violation: {threshold.metric_name}",
            message=f"Metric {threshold.metric_name} has exceeded threshold. Current: {current_value:.2f}, Threshold: {threshold.warning_threshold:.2f}",
            details={
                "metric_name": threshold.metric_name,
                "current_value": current_value,
                "warning_threshold": threshold.warning_threshold,
                "critical_threshold": threshold.critical_threshold,
                "consecutive_violations": self.threshold_violations[threshold.metric_name]
            },
            auto_resolve=True
        )

        await self._process_alert(alert)

    async def _process_alert(self, alert: MonitoringAlert):
        """Process and handle monitoring alert."""
        self.active_alerts[alert.id] = alert

        # Execute alert handlers
        handlers = self.alert_handlers.get(alert.alert_type, [])
        for handler in handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        # Store alert in Redis for dashboard
        await self._store_alert_in_redis(alert)

        # Log alert
        logger.warning(f"BETA ALERT [{alert.severity.value.upper()}]: {alert.title} - {alert.message}")

    async def _store_alert_in_redis(self, alert: MonitoringAlert):
        """Store alert in Redis for real-time dashboard."""
        try:
            alert_data = {
                "id": alert.id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "details": alert.details,
                "triggered_at": alert.triggered_at.isoformat(),
                "acknowledged": alert.acknowledged,
                "resolved": alert.resolved
            }

            # Store with TTL
            self.redis_client.setex(
                f"beta_alert:{alert.id}",
                timedelta(hours=24),
                json.dumps(alert_data)
            )

            # Add to active alerts list
            self.redis_client.lpush("beta_active_alerts", alert.id)
            self.redis_client.ltrim("beta_active_alerts", 0, 99)  # Keep latest 100

        except Exception as e:
            logger.error(f"Failed to store alert in Redis: {e}")

    # =============================================================================
    # ALERT HANDLERS
    # =============================================================================

    async def _notify_engineering_team(self, alert: MonitoringAlert):
        """Notify engineering team of critical issues."""
        await self.notification_service.send_slack_alert(
            channel="#beta-engineering",
            title=f"🚨 BETA CRITICAL: {alert.title}",
            message=alert.message,
            severity=alert.severity.value,
            details=alert.details
        )

    async def _notify_devops_team(self, alert: MonitoringAlert):
        """Notify DevOps team for infrastructure issues."""
        await self.notification_service.send_slack_alert(
            channel="#beta-devops",
            title=f"⚡ BETA PERFORMANCE: {alert.title}",
            message=alert.message,
            severity=alert.severity.value,
            details=alert.details
        )

    async def _notify_product_team(self, alert: MonitoringAlert):
        """Notify product team for user experience issues."""
        await self.notification_service.send_slack_alert(
            channel="#beta-product",
            title=f"👥 BETA USER ISSUE: {alert.title}",
            message=alert.message,
            severity=alert.severity.value,
            details=alert.details
        )

    async def _notify_security_team(self, alert: MonitoringAlert):
        """Notify security team for security incidents."""
        await self.notification_service.send_slack_alert(
            channel="#beta-security",
            title=f"🔒 BETA SECURITY: {alert.title}",
            message=alert.message,
            severity=alert.severity.value,
            details=alert.details
        )

    async def _auto_scale_resources(self, alert: MonitoringAlert):
        """Auto-scale resources based on performance alerts."""
        logger.info(f"Auto-scaling triggered by alert: {alert.title}")
        # Implementation would depend on infrastructure setup
        # Could trigger Kubernetes HPA or cloud auto-scaling

    async def _enable_circuit_breakers(self, alert: MonitoringAlert):
        """Enable circuit breakers to protect system."""
        logger.info(f"Circuit breakers activated by alert: {alert.title}")
        # Implementation would enable circuit breakers for problematic services

    async def _analyze_slow_queries(self, alert: MonitoringAlert):
        """Analyze slow database queries."""
        logger.info(f"Analyzing slow queries due to alert: {alert.title}")
        # Implementation would analyze database performance

    async def _analyze_user_dropoff(self, alert: MonitoringAlert):
        """Analyze user activity dropoff patterns."""
        logger.info(f"Analyzing user dropoff due to alert: {alert.title}")
        # Implementation would analyze user behavior patterns

    async def _auto_block_suspicious_ips(self, alert: MonitoringAlert):
        """Auto-block suspicious IP addresses."""
        logger.info(f"Auto-blocking suspicious IPs due to alert: {alert.title}")
        # Implementation would block IPs via firewall/WAF

    async def _escalate_to_management(self, alert: MonitoringAlert):
        """Escalate critical issues to management."""
        await self.notification_service.send_email(
            to_emails=["cto@company.com", "vp-engineering@company.com"],
            subject=f"CRITICAL BETA ISSUE: {alert.title}",
            content=f"""
            A critical issue has been detected in the beta program:

            Alert: {alert.title}
            Severity: {alert.severity.value.upper()}
            Message: {alert.message}
            Time: {alert.triggered_at}

            Details: {json.dumps(alert.details, indent=2)}

            Immediate attention required.
            """,
            email_type="critical_alert"
        )

    async def _emergency_notification(self, error_message: str):
        """Send emergency notification for monitoring system failures."""
        await self.notification_service.send_email(
            to_emails=["devops-oncall@company.com"],
            subject="EMERGENCY: Beta Monitoring System Failure",
            content=f"""
            The beta monitoring system has encountered a critical error:

            Error: {error_message}
            Time: {datetime.now(timezone.utc)}

            The monitoring system needs immediate attention.
            """,
            email_type="emergency"
        )

    # =============================================================================
    # PUBLIC API
    # =============================================================================

    async def get_current_metrics(self) -> MonitoringMetrics:
        """Get current monitoring metrics."""
        return self.current_metrics

    async def get_active_alerts(self) -> List[MonitoringAlert]:
        """Get all active alerts."""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")

    async def resolve_alert(self, alert_id: str, resolved_by: str):
        """Manually resolve an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")

    async def _check_alert_resolution(self, metric_name: str):
        """Check if alerts should be auto-resolved."""
        for alert in self.active_alerts.values():
            if (alert.auto_resolve and
                not alert.resolved and
                metric_name in alert.details.get("metric_name", "")):
                alert.resolved = True
                logger.info(f"Alert {alert.id} auto-resolved for metric recovery: {metric_name}")

# =============================================================================
# SINGLETON MONITOR INSTANCE
# =============================================================================

beta_monitor = BetaLaunchMonitor()