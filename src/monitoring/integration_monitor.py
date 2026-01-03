"""
Integration Monitoring System
Comprehensive monitoring for webhooks, external APIs, and integration health with alerting and analytics.
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import statistics
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationMetrics:
    """Integration performance metrics"""
    provider: str
    endpoint: str
    timestamp: datetime

    # Performance metrics
    response_time_ms: float
    success_rate: float
    error_rate: float
    throughput_per_minute: float

    # HTTP metrics
    status_codes: Dict[int, int]

    # Rate limiting metrics
    rate_limit_hits: int
    rate_limit_remaining: int

    # Availability metrics
    uptime_percentage: float
    downtime_minutes: float

    # Business metrics
    total_requests: int
    successful_requests: int
    failed_requests: int
    retried_requests: int

@dataclass
class IntegrationAlert:
    """Integration alert configuration and state"""
    alert_id: str
    provider: str
    alert_type: str  # availability, performance, error_rate, rate_limit
    severity: str    # low, medium, high, critical
    threshold: float
    current_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime]
    status: str      # active, resolved, acknowledged
    message: str
    notification_sent: bool = False

@dataclass
class WebhookDeliveryMetrics:
    """Webhook delivery tracking metrics"""
    provider: str
    endpoint: str
    timestamp: datetime

    # Delivery metrics
    total_webhooks: int
    successful_deliveries: int
    failed_deliveries: int
    retry_attempts: int

    # Timing metrics
    average_delivery_time_ms: float
    max_delivery_time_ms: float
    min_delivery_time_ms: float

    # Error analysis
    error_types: Dict[str, int]
    http_errors: Dict[int, int]

    # Dead letter queue metrics
    dlq_size: int
    dlq_oldest_age_hours: float

class IntegrationHealthChecker:
    """Health check system for external integrations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_endpoints = config.get('health_endpoints', {})
        self.check_interval = config.get('check_interval_seconds', 300)
        self.timeout = config.get('timeout_seconds', 30)

    async def check_integration_health(self, provider: str) -> Dict[str, Any]:
        """Check health of a specific integration"""
        endpoint_config = self.health_endpoints.get(provider)

        if not endpoint_config:
            return {
                'provider': provider,
                'status': 'unknown',
                'message': 'No health endpoint configured',
                'timestamp': datetime.now().isoformat()
            }

        try:
            start_time = time.time()

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(endpoint_config['url'], headers=endpoint_config.get('headers', {})) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json() if 'json' in response.content_type else {}
                        return {
                            'provider': provider,
                            'status': 'healthy',
                            'response_time_ms': response_time,
                            'timestamp': datetime.now().isoformat(),
                            'details': data
                        }
                    else:
                        return {
                            'provider': provider,
                            'status': 'unhealthy',
                            'response_time_ms': response_time,
                            'status_code': response.status,
                            'timestamp': datetime.now().isoformat(),
                            'message': f"HTTP {response.status}"
                        }

        except asyncio.TimeoutError:
            return {
                'provider': provider,
                'status': 'timeout',
                'timestamp': datetime.now().isoformat(),
                'message': f"Health check timeout after {self.timeout}s"
            }
        except Exception as e:
            return {
                'provider': provider,
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'message': str(e)
            }

    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run health checks for all configured integrations"""
        results = {}

        check_tasks = []
        for provider in self.health_endpoints.keys():
            task = asyncio.create_task(self.check_integration_health(provider))
            check_tasks.append((provider, task))

        for provider, task in check_tasks:
            try:
                results[provider] = await task
            except Exception as e:
                results[provider] = {
                    'provider': provider,
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'message': f"Health check failed: {str(e)}"
                }

        return results

class PerformanceAnalyzer:
    """Analyze integration performance and detect issues"""

    def __init__(self, db_path: str = "integration_metrics.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS integration_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time_ms REAL,
                    success_rate REAL,
                    error_rate REAL,
                    throughput_per_minute REAL,
                    status_codes TEXT,
                    rate_limit_hits INTEGER,
                    rate_limit_remaining INTEGER,
                    uptime_percentage REAL,
                    total_requests INTEGER,
                    successful_requests INTEGER,
                    failed_requests INTEGER,
                    retried_requests INTEGER
                );

                CREATE TABLE IF NOT EXISTS webhook_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_webhooks INTEGER,
                    successful_deliveries INTEGER,
                    failed_deliveries INTEGER,
                    retry_attempts INTEGER,
                    average_delivery_time_ms REAL,
                    max_delivery_time_ms REAL,
                    min_delivery_time_ms REAL,
                    error_types TEXT,
                    http_errors TEXT,
                    dlq_size INTEGER,
                    dlq_oldest_age_hours REAL
                );

                CREATE TABLE IF NOT EXISTS integration_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    provider TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    threshold REAL,
                    current_value REAL,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    message TEXT,
                    notification_sent BOOLEAN DEFAULT FALSE
                );

                CREATE INDEX IF NOT EXISTS idx_integration_metrics_provider_time
                ON integration_metrics(provider, timestamp);
                CREATE INDEX IF NOT EXISTS idx_webhook_metrics_provider_time
                ON webhook_metrics(provider, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_status ON integration_alerts(status);
            """)

    async def record_integration_metrics(self, metrics: IntegrationMetrics):
        """Record integration performance metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO integration_metrics
                (provider, endpoint, response_time_ms, success_rate, error_rate,
                 throughput_per_minute, status_codes, rate_limit_hits, rate_limit_remaining,
                 uptime_percentage, total_requests, successful_requests, failed_requests, retried_requests)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.provider, metrics.endpoint, metrics.response_time_ms,
                metrics.success_rate, metrics.error_rate, metrics.throughput_per_minute,
                json.dumps(metrics.status_codes), metrics.rate_limit_hits,
                metrics.rate_limit_remaining, metrics.uptime_percentage,
                metrics.total_requests, metrics.successful_requests,
                metrics.failed_requests, metrics.retried_requests
            ))

    async def record_webhook_metrics(self, metrics: WebhookDeliveryMetrics):
        """Record webhook delivery metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO webhook_metrics
                (provider, endpoint, total_webhooks, successful_deliveries, failed_deliveries,
                 retry_attempts, average_delivery_time_ms, max_delivery_time_ms, min_delivery_time_ms,
                 error_types, http_errors, dlq_size, dlq_oldest_age_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.provider, metrics.endpoint, metrics.total_webhooks,
                metrics.successful_deliveries, metrics.failed_deliveries,
                metrics.retry_attempts, metrics.average_delivery_time_ms,
                metrics.max_delivery_time_ms, metrics.min_delivery_time_ms,
                json.dumps(metrics.error_types), json.dumps(metrics.http_errors),
                metrics.dlq_size, metrics.dlq_oldest_age_hours
            ))

    async def analyze_performance_trends(self, provider: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze performance trends for a provider"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get recent metrics
            cursor.execute("""
                SELECT * FROM integration_metrics
                WHERE provider = ? AND timestamp >= ?
                ORDER BY timestamp
            """, (provider, cutoff_time.isoformat()))

            metrics = [dict(row) for row in cursor.fetchall()]

            if not metrics:
                return {'provider': provider, 'status': 'no_data'}

            # Calculate trends
            response_times = [m['response_time_ms'] for m in metrics if m['response_time_ms']]
            success_rates = [m['success_rate'] for m in metrics if m['success_rate'] is not None]
            error_rates = [m['error_rate'] for m in metrics if m['error_rate'] is not None]

            analysis = {
                'provider': provider,
                'time_period_hours': hours,
                'total_data_points': len(metrics),
                'performance_summary': {
                    'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                    'p95_response_time_ms': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 10 else 0,
                    'avg_success_rate': statistics.mean(success_rates) if success_rates else 0,
                    'avg_error_rate': statistics.mean(error_rates) if error_rates else 0
                },
                'trends': {
                    'response_time_trend': self._calculate_trend(response_times),
                    'success_rate_trend': self._calculate_trend(success_rates),
                    'error_rate_trend': self._calculate_trend(error_rates)
                }
            }

            # Detect anomalies
            analysis['anomalies'] = await self._detect_anomalies(provider, metrics)

            return analysis

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        if len(values) < 2:
            return 'insufficient_data'

        # Simple trend calculation - compare first and last quarters
        quarter_size = len(values) // 4
        if quarter_size < 1:
            return 'insufficient_data'

        first_quarter_avg = statistics.mean(values[:quarter_size])
        last_quarter_avg = statistics.mean(values[-quarter_size:])

        change_percent = ((last_quarter_avg - first_quarter_avg) / first_quarter_avg) * 100

        if change_percent > 10:
            return 'increasing'
        elif change_percent < -10:
            return 'decreasing'
        else:
            return 'stable'

    async def _detect_anomalies(self, provider: str, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect performance anomalies"""
        anomalies = []

        response_times = [m['response_time_ms'] for m in metrics if m['response_time_ms']]
        if len(response_times) > 10:
            mean_rt = statistics.mean(response_times)
            stdev_rt = statistics.stdev(response_times)
            threshold = mean_rt + (2 * stdev_rt)  # 2 standard deviations

            outliers = [rt for rt in response_times if rt > threshold]
            if outliers:
                anomalies.append({
                    'type': 'response_time_spike',
                    'count': len(outliers),
                    'max_value': max(outliers),
                    'threshold': threshold
                })

        # Check for error rate spikes
        error_rates = [m['error_rate'] for m in metrics if m['error_rate'] is not None]
        if error_rates:
            max_error_rate = max(error_rates)
            if max_error_rate > 0.1:  # 10% error rate
                anomalies.append({
                    'type': 'high_error_rate',
                    'max_error_rate': max_error_rate,
                    'threshold': 0.1
                })

        return anomalies

class AlertManager:
    """Manage integration alerts and notifications"""

    def __init__(self, config: Dict[str, Any], performance_analyzer: PerformanceAnalyzer):
        self.config = config
        self.analyzer = performance_analyzer
        self.alert_rules = config.get('alert_rules', {})
        self.notification_config = config.get('notifications', {})

    async def check_alert_conditions(self, provider: str, metrics: IntegrationMetrics) -> List[IntegrationAlert]:
        """Check if any alert conditions are met"""
        alerts = []

        provider_rules = self.alert_rules.get(provider, self.alert_rules.get('default', {}))

        # Response time alerts
        if 'response_time_ms' in provider_rules:
            threshold = provider_rules['response_time_ms']['threshold']
            if metrics.response_time_ms > threshold:
                alert = IntegrationAlert(
                    alert_id=f"{provider}_response_time_{int(time.time())}",
                    provider=provider,
                    alert_type='performance',
                    severity=provider_rules['response_time_ms'].get('severity', 'medium'),
                    threshold=threshold,
                    current_value=metrics.response_time_ms,
                    triggered_at=datetime.now(),
                    resolved_at=None,
                    status='active',
                    message=f"Response time ({metrics.response_time_ms:.2f}ms) exceeds threshold ({threshold}ms)"
                )
                alerts.append(alert)

        # Error rate alerts
        if 'error_rate' in provider_rules:
            threshold = provider_rules['error_rate']['threshold']
            if metrics.error_rate > threshold:
                alert = IntegrationAlert(
                    alert_id=f"{provider}_error_rate_{int(time.time())}",
                    provider=provider,
                    alert_type='error_rate',
                    severity=provider_rules['error_rate'].get('severity', 'high'),
                    threshold=threshold,
                    current_value=metrics.error_rate,
                    triggered_at=datetime.now(),
                    resolved_at=None,
                    status='active',
                    message=f"Error rate ({metrics.error_rate:.2%}) exceeds threshold ({threshold:.2%})"
                )
                alerts.append(alert)

        # Availability alerts
        if 'uptime_percentage' in provider_rules:
            threshold = provider_rules['uptime_percentage']['threshold']
            if metrics.uptime_percentage < threshold:
                alert = IntegrationAlert(
                    alert_id=f"{provider}_availability_{int(time.time())}",
                    provider=provider,
                    alert_type='availability',
                    severity=provider_rules['uptime_percentage'].get('severity', 'critical'),
                    threshold=threshold,
                    current_value=metrics.uptime_percentage,
                    triggered_at=datetime.now(),
                    resolved_at=None,
                    status='active',
                    message=f"Availability ({metrics.uptime_percentage:.1%}) below threshold ({threshold:.1%})"
                )
                alerts.append(alert)

        # Rate limit alerts
        if 'rate_limit_remaining' in provider_rules:
            threshold = provider_rules['rate_limit_remaining']['threshold']
            if metrics.rate_limit_remaining < threshold:
                alert = IntegrationAlert(
                    alert_id=f"{provider}_rate_limit_{int(time.time())}",
                    provider=provider,
                    alert_type='rate_limit',
                    severity=provider_rules['rate_limit_remaining'].get('severity', 'medium'),
                    threshold=threshold,
                    current_value=metrics.rate_limit_remaining,
                    triggered_at=datetime.now(),
                    resolved_at=None,
                    status='active',
                    message=f"Rate limit remaining ({metrics.rate_limit_remaining}) below threshold ({threshold})"
                )
                alerts.append(alert)

        return alerts

    async def process_alerts(self, alerts: List[IntegrationAlert]):
        """Process and store alerts"""
        for alert in alerts:
            # Check if similar alert already exists
            existing_alert = await self._get_existing_alert(alert.provider, alert.alert_type)

            if existing_alert:
                # Update existing alert
                await self._update_alert(existing_alert['alert_id'], alert.current_value)
            else:
                # Create new alert
                await self._store_alert(alert)

                # Send notification
                if self.notification_config.get('enabled', True):
                    await self._send_alert_notification(alert)

    async def _get_existing_alert(self, provider: str, alert_type: str) -> Optional[Dict[str, Any]]:
        """Check for existing active alert of the same type"""
        with sqlite3.connect(self.analyzer.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM integration_alerts
                WHERE provider = ? AND alert_type = ? AND status = 'active'
                ORDER BY triggered_at DESC
                LIMIT 1
            """, (provider, alert_type))

            row = cursor.fetchone()
            return dict(row) if row else None

    async def _store_alert(self, alert: IntegrationAlert):
        """Store alert in database"""
        with sqlite3.connect(self.analyzer.db_path) as conn:
            conn.execute("""
                INSERT INTO integration_alerts
                (alert_id, provider, alert_type, severity, threshold, current_value,
                 status, message, notification_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id, alert.provider, alert.alert_type, alert.severity,
                alert.threshold, alert.current_value, alert.status, alert.message,
                alert.notification_sent
            ))

    async def _update_alert(self, alert_id: str, current_value: float):
        """Update existing alert with new value"""
        with sqlite3.connect(self.analyzer.db_path) as conn:
            conn.execute("""
                UPDATE integration_alerts
                SET current_value = ?, triggered_at = CURRENT_TIMESTAMP
                WHERE alert_id = ?
            """, (current_value, alert_id))

    async def _send_alert_notification(self, alert: IntegrationAlert):
        """Send alert notification"""
        try:
            # Send Slack notification if configured
            if self.notification_config.get('slack', {}).get('enabled'):
                await self._send_slack_notification(alert)

            # Send email notification if configured
            if self.notification_config.get('email', {}).get('enabled'):
                await self._send_email_notification(alert)

            # Update notification status
            with sqlite3.connect(self.analyzer.db_path) as conn:
                conn.execute("""
                    UPDATE integration_alerts
                    SET notification_sent = TRUE
                    WHERE alert_id = ?
                """, (alert.alert_id,))

        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")

    async def _send_slack_notification(self, alert: IntegrationAlert):
        """Send Slack notification"""
        webhook_url = self.notification_config['slack']['webhook_url']

        color_map = {
            'low': '#36a64f',      # Green
            'medium': '#ff9500',   # Orange
            'high': '#ff0000',     # Red
            'critical': '#8B0000'  # Dark Red
        }

        payload = {
            'attachments': [{
                'color': color_map.get(alert.severity, '#ff9500'),
                'title': f'Integration Alert: {alert.provider}',
                'text': alert.message,
                'fields': [
                    {'title': 'Severity', 'value': alert.severity.upper(), 'short': True},
                    {'title': 'Alert Type', 'value': alert.alert_type.replace('_', ' ').title(), 'short': True},
                    {'title': 'Current Value', 'value': str(alert.current_value), 'short': True},
                    {'title': 'Threshold', 'value': str(alert.threshold), 'short': True}
                ],
                'footer': 'Legal AI Integration Monitor',
                'ts': int(alert.triggered_at.timestamp())
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Slack notification failed: {response.status}")

    async def _send_email_notification(self, alert: IntegrationAlert):
        """Send email notification"""
        email_config = self.notification_config['email']

        msg = MimeMultipart()
        msg['From'] = email_config['from_address']
        msg['To'] = ', '.join(email_config['to_addresses'])
        msg['Subject'] = f'Integration Alert: {alert.provider} - {alert.severity.upper()}'

        body = f"""
        Integration Alert Triggered

        Provider: {alert.provider}
        Alert Type: {alert.alert_type.replace('_', ' ').title()}
        Severity: {alert.severity.upper()}

        Message: {alert.message}

        Current Value: {alert.current_value}
        Threshold: {alert.threshold}

        Triggered At: {alert.triggered_at}

        Please check the integration monitoring dashboard for more details.
        """

        msg.attach(MimeText(body, 'plain'))

        # Send email
        server = smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port'])
        if email_config.get('use_tls'):
            server.starttls()
        if email_config.get('username'):
            server.login(email_config['username'], email_config['password'])

        text = msg.as_string()
        server.sendmail(email_config['from_address'], email_config['to_addresses'], text)
        server.quit()

class IntegrationMonitor:
    """Main integration monitoring system"""

    def __init__(self, config_path: str = "integration_monitor_config.json"):
        self.config = self._load_config(config_path)

        # Initialize components
        self.health_checker = IntegrationHealthChecker(self.config.get('health_checks', {}))
        self.performance_analyzer = PerformanceAnalyzer(self.config.get('db_path', 'integration_metrics.db'))
        self.alert_manager = AlertManager(self.config.get('alerting', {}), self.performance_analyzer)

        # Monitoring state
        self.monitoring_active = False
        self.monitoring_stats = {
            'checks_performed': 0,
            'alerts_triggered': 0,
            'uptime_start': datetime.now()
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            'health_checks': {
                'check_interval_seconds': 300,
                'timeout_seconds': 30,
                'health_endpoints': {}
            },
            'alerting': {
                'enabled': True,
                'alert_rules': {},
                'notifications': {
                    'enabled': True,
                    'slack': {'enabled': False},
                    'email': {'enabled': False}
                }
            },
            'performance_analysis': {
                'enabled': True,
                'analysis_interval_minutes': 60,
                'retention_days': 30
            },
            'db_path': 'integration_metrics.db'
        }

        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.warning(f"Could not load monitoring config: {e}, using defaults")

        return default_config

    async def start_monitoring(self):
        """Start the integration monitoring system"""
        logger.info("Starting integration monitoring system")

        self.monitoring_active = True
        self.monitoring_stats['uptime_start'] = datetime.now()

        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._performance_analysis_loop()),
            asyncio.create_task(self._webhook_monitoring_loop())
        ]

        await asyncio.gather(*monitoring_tasks, return_exceptions=True)

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        logger.info("Stopping integration monitoring system")
        self.monitoring_active = False

    async def _health_check_loop(self):
        """Main health checking loop"""
        while self.monitoring_active:
            try:
                # Run health checks
                health_results = await self.health_checker.run_all_health_checks()

                # Process results and generate metrics
                for provider, result in health_results.items():
                    await self._process_health_check_result(provider, result)

                self.monitoring_stats['checks_performed'] += len(health_results)

                # Wait for next check
                await asyncio.sleep(self.config['health_checks']['check_interval_seconds'])

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _performance_analysis_loop(self):
        """Performance analysis loop"""
        while self.monitoring_active:
            try:
                # Get list of providers to analyze
                providers = self.config.get('providers', [])

                for provider in providers:
                    # Analyze performance trends
                    analysis = await self.performance_analyzer.analyze_performance_trends(provider)

                    # Log significant findings
                    if analysis.get('anomalies'):
                        logger.warning(f"Performance anomalies detected for {provider}: {analysis['anomalies']}")

                # Wait for next analysis
                analysis_interval = self.config['performance_analysis']['analysis_interval_minutes'] * 60
                await asyncio.sleep(analysis_interval)

            except Exception as e:
                logger.error(f"Error in performance analysis loop: {e}")
                await asyncio.sleep(300)  # Wait before retrying

    async def _webhook_monitoring_loop(self):
        """Webhook delivery monitoring loop"""
        while self.monitoring_active:
            try:
                # Monitor webhook delivery metrics
                webhook_metrics = await self._collect_webhook_metrics()

                for metrics in webhook_metrics:
                    await self.performance_analyzer.record_webhook_metrics(metrics)

                # Wait for next collection
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Error in webhook monitoring loop: {e}")
                await asyncio.sleep(300)

    async def _process_health_check_result(self, provider: str, result: Dict[str, Any]):
        """Process health check result and generate metrics"""
        # Create metrics from health check result
        metrics = IntegrationMetrics(
            provider=provider,
            endpoint='health_check',
            timestamp=datetime.now(),
            response_time_ms=result.get('response_time_ms', 0),
            success_rate=1.0 if result['status'] == 'healthy' else 0.0,
            error_rate=0.0 if result['status'] == 'healthy' else 1.0,
            throughput_per_minute=0,  # Not applicable for health checks
            status_codes={result.get('status_code', 200): 1},
            rate_limit_hits=0,
            rate_limit_remaining=1000,  # Default
            uptime_percentage=100.0 if result['status'] == 'healthy' else 0.0,
            downtime_minutes=0,
            total_requests=1,
            successful_requests=1 if result['status'] == 'healthy' else 0,
            failed_requests=0 if result['status'] == 'healthy' else 1,
            retried_requests=0
        )

        # Record metrics
        await self.performance_analyzer.record_integration_metrics(metrics)

        # Check for alerts
        alerts = await self.alert_manager.check_alert_conditions(provider, metrics)
        if alerts:
            await self.alert_manager.process_alerts(alerts)
            self.monitoring_stats['alerts_triggered'] += len(alerts)

    async def _collect_webhook_metrics(self) -> List[WebhookDeliveryMetrics]:
        """Collect webhook delivery metrics"""
        # This would integrate with the webhook receiver system
        # For now, return empty list
        return []

    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        # Get recent health status
        health_status = await self.health_checker.run_all_health_checks()

        # Get performance summaries
        performance_summaries = {}
        providers = self.config.get('providers', [])
        for provider in providers:
            performance_summaries[provider] = await self.performance_analyzer.analyze_performance_trends(provider, hours=24)

        # Get active alerts
        with sqlite3.connect(self.performance_analyzer.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM integration_alerts
                WHERE status = 'active'
                ORDER BY triggered_at DESC
                LIMIT 20
            """)
            active_alerts = [dict(row) for row in cursor.fetchall()]

        # Get monitoring stats
        uptime_hours = (datetime.now() - self.monitoring_stats['uptime_start']).total_seconds() / 3600

        return {
            'health_status': health_status,
            'performance_summaries': performance_summaries,
            'active_alerts': active_alerts,
            'monitoring_stats': {
                **self.monitoring_stats,
                'uptime_hours': uptime_hours,
                'monitoring_active': self.monitoring_active
            },
            'last_updated': datetime.now().isoformat()
        }

# Example usage
async def main():
    """Example usage of the integration monitor"""
    monitor = IntegrationMonitor()

    # Get dashboard data
    dashboard_data = await monitor.get_monitoring_dashboard_data()
    print(f"Monitoring dashboard: {json.dumps(dashboard_data, indent=2, default=str)}")

    # Start monitoring (would run continuously)
    # await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())