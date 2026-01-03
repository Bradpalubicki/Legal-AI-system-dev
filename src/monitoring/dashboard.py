"""
Performance Monitoring Dashboard
Real-time monitoring and visualization of AI system performance, feedback quality, and learning progress.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sqlite3
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetricSnapshot:
    """Real-time metric snapshot"""
    timestamp: datetime
    metric_name: str
    value: float
    threshold: Optional[float]
    status: str  # 'good', 'warning', 'critical'
    trend: str   # 'up', 'down', 'stable'

@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    system_overview: Dict[str, Any]
    performance_metrics: Dict[str, List[MetricSnapshot]]
    learning_progress: Dict[str, Any]
    feedback_analytics: Dict[str, Any]
    model_status: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    timestamp: datetime

class PerformanceMonitoringDashboard:
    """
    Real-time performance monitoring dashboard for the AI improvement system
    """

    def __init__(self, config_path: str = "dashboard_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

        # Database connections
        self.feedback_db = "feedback_collector.db"
        self.training_db = "training_pipeline.db"
        self.versions_db = "model_versions/model_versions.db"
        self.metrics_db = "dashboard_metrics.db"

        # Real-time data
        self.active_connections: List[WebSocket] = []
        self.current_metrics: Dict[str, List[MetricSnapshot]] = {}
        self.alert_history: List[Dict[str, Any]] = []

        # Monitoring state
        self.monitoring_active = False
        self.last_update = datetime.now()

        self._init_metrics_database()

        # FastAPI app for dashboard
        self.app = FastAPI(title="AI Performance Dashboard")
        self._setup_routes()

    def _load_config(self) -> Dict[str, Any]:
        """Load dashboard configuration"""
        default_config = {
            "refresh_interval_seconds": 30,
            "metric_retention_hours": 168,  # 1 week
            "alert_thresholds": {
                "accuracy": {"warning": 0.80, "critical": 0.75},
                "response_time": {"warning": 3000, "critical": 5000},
                "error_rate": {"warning": 0.05, "critical": 0.10},
                "user_satisfaction": {"warning": 3.5, "critical": 3.0},
                "training_success_rate": {"warning": 0.80, "critical": 0.70}
            },
            "dashboard_settings": {
                "theme": "dark",
                "auto_refresh": True,
                "show_detailed_metrics": True,
                "enable_alerts": True,
                "enable_sounds": False
            },
            "visualization": {
                "chart_types": ["line", "gauge", "bar"],
                "time_ranges": ["1h", "6h", "24h", "7d", "30d"],
                "default_time_range": "24h"
            }
        }

        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.warning(f"Could not load dashboard config: {e}, using defaults")

        return default_config

    def _init_metrics_database(self):
        """Initialize metrics storage database"""
        with sqlite3.connect(self.metrics_db) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS metric_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL,
                    status TEXT NOT NULL,
                    trend TEXT NOT NULL,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS system_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metric_name TEXT,
                    current_value REAL,
                    threshold_value REAL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS dashboard_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    user_agent TEXT,
                    ip_address TEXT,
                    active BOOLEAN DEFAULT TRUE
                );

                CREATE INDEX IF NOT EXISTS idx_metric_timestamp ON metric_snapshots(timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_timestamp ON system_alerts(timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_severity ON system_alerts(severity);
            """)

    async def start_monitoring(self):
        """Start the real-time monitoring system"""
        logger.info("Starting performance monitoring dashboard")

        self.monitoring_active = True

        # Start monitoring tasks
        asyncio.create_task(self._collect_metrics_loop())
        asyncio.create_task(self._check_alerts_loop())
        asyncio.create_task(self._broadcast_updates_loop())

        logger.info("Performance monitoring dashboard started")

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        logger.info("Stopping performance monitoring dashboard")

        self.monitoring_active = False

        # Close all WebSocket connections
        for connection in self.active_connections:
            await connection.close()

        self.active_connections.clear()

        logger.info("Performance monitoring dashboard stopped")

    async def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while self.monitoring_active:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self.config["refresh_interval_seconds"])
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _collect_all_metrics(self):
        """Collect all performance metrics"""
        current_time = datetime.now()

        # Collect feedback metrics
        feedback_metrics = await self._collect_feedback_metrics()

        # Collect training metrics
        training_metrics = await self._collect_training_metrics()

        # Collect model performance metrics
        model_metrics = await self._collect_model_metrics()

        # Collect system metrics
        system_metrics = await self._collect_system_metrics()

        # Store all metrics
        all_metrics = {**feedback_metrics, **training_metrics, **model_metrics, **system_metrics}

        for metric_name, value in all_metrics.items():
            snapshot = self._create_metric_snapshot(metric_name, value, current_time)
            await self._store_metric_snapshot(snapshot)

            # Update current metrics for real-time display
            if metric_name not in self.current_metrics:
                self.current_metrics[metric_name] = []

            self.current_metrics[metric_name].append(snapshot)

            # Keep only recent metrics
            cutoff_time = current_time - timedelta(hours=self.config["metric_retention_hours"])
            self.current_metrics[metric_name] = [
                m for m in self.current_metrics[metric_name]
                if m.timestamp > cutoff_time
            ]

        self.last_update = current_time

    async def _collect_feedback_metrics(self) -> Dict[str, float]:
        """Collect feedback-related metrics"""
        metrics = {}

        try:
            with sqlite3.connect(self.feedback_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Total feedback count (last 24h)
                cursor.execute("""
                    SELECT COUNT(*) as count FROM feedback_entries
                    WHERE created_at >= datetime('now', '-24 hours')
                """)
                metrics['feedback_volume_24h'] = cursor.fetchone()['count']

                # Average accuracy rating
                cursor.execute("""
                    SELECT AVG(
                        CASE
                            WHEN accuracy_rating = 'excellent' THEN 5
                            WHEN accuracy_rating = 'good' THEN 4
                            WHEN accuracy_rating = 'fair' THEN 3
                            WHEN accuracy_rating = 'poor' THEN 2
                            ELSE 1
                        END
                    ) as avg_rating
                    FROM feedback_entries
                    WHERE accuracy_rating IS NOT NULL
                    AND created_at >= datetime('now', '-24 hours')
                """)
                result = cursor.fetchone()
                metrics['avg_accuracy_rating'] = result['avg_rating'] or 0

                # Attorney verification rate
                cursor.execute("""
                    SELECT
                        SUM(CASE WHEN attorney_verified = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as rate
                    FROM feedback_entries
                    WHERE created_at >= datetime('now', '-24 hours')
                """)
                result = cursor.fetchone()
                metrics['attorney_verification_rate'] = result['rate'] or 0

                # Training queue size
                cursor.execute("""
                    SELECT COUNT(*) as count FROM feedback_entries
                    WHERE queued_for_training = 1 AND processed_for_training = 0
                """)
                metrics['training_queue_size'] = cursor.fetchone()['count']

        except Exception as e:
            logger.error(f"Error collecting feedback metrics: {e}")

        return metrics

    async def _collect_training_metrics(self) -> Dict[str, float]:
        """Collect training-related metrics"""
        metrics = {}

        try:
            with sqlite3.connect(self.training_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Training success rate (last 7 days)
                cursor.execute("""
                    SELECT
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as rate
                    FROM training_runs
                    WHERE start_time >= datetime('now', '-7 days')
                """)
                result = cursor.fetchone()
                metrics['training_success_rate'] = result['rate'] or 0

                # Average training duration
                cursor.execute("""
                    SELECT AVG(
                        (julianday(end_time) - julianday(start_time)) * 24 * 60
                    ) as avg_duration_minutes
                    FROM training_runs
                    WHERE status = 'completed'
                    AND start_time >= datetime('now', '-7 days')
                """)
                result = cursor.fetchone()
                metrics['avg_training_duration_minutes'] = result['avg_duration_minutes'] or 0

                # Active A/B tests
                cursor.execute("""
                    SELECT COUNT(*) as count FROM ab_tests
                    WHERE status = 'running'
                """)
                metrics['active_ab_tests'] = cursor.fetchone()['count']

                # Recent model accuracy improvements
                cursor.execute("""
                    SELECT AVG(JSON_EXTRACT(performance_metrics, '$.accuracy')) as avg_accuracy
                    FROM model_versions
                    WHERE created_at >= datetime('now', '-7 days')
                """)
                result = cursor.fetchone()
                metrics['recent_model_accuracy'] = result['avg_accuracy'] or 0

        except Exception as e:
            logger.error(f"Error collecting training metrics: {e}")

        return metrics

    async def _collect_model_metrics(self) -> Dict[str, float]:
        """Collect model performance metrics"""
        metrics = {}

        try:
            with sqlite3.connect(self.versions_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Production models count
                cursor.execute("""
                    SELECT COUNT(*) as count FROM model_metadata
                    WHERE status = 'production'
                """)
                metrics['production_models_count'] = cursor.fetchone()['count']

                # Average response time (from latest metrics)
                cursor.execute("""
                    SELECT AVG(avg_response_time_ms) as avg_response_time
                    FROM performance_metrics
                    WHERE evaluation_date >= datetime('now', '-1 day')
                """)
                result = cursor.fetchone()
                metrics['avg_response_time_ms'] = result['avg_response_time'] or 0

                # Current error rate
                cursor.execute("""
                    SELECT AVG(error_rate) as avg_error_rate
                    FROM performance_metrics
                    WHERE evaluation_date >= datetime('now', '-1 day')
                """)
                result = cursor.fetchone()
                metrics['current_error_rate'] = result['avg_error_rate'] or 0

                # User satisfaction score
                cursor.execute("""
                    SELECT AVG(user_satisfaction_score) as avg_satisfaction
                    FROM performance_metrics
                    WHERE evaluation_date >= datetime('now', '-1 day')
                """)
                result = cursor.fetchone()
                metrics['user_satisfaction_score'] = result['avg_satisfaction'] or 0

                # Safety score
                cursor.execute("""
                    SELECT AVG(safety_score) as avg_safety
                    FROM performance_metrics
                    WHERE evaluation_date >= datetime('now', '-1 day')
                """)
                result = cursor.fetchone()
                metrics['safety_score'] = result['avg_safety'] or 0

        except Exception as e:
            logger.error(f"Error collecting model metrics: {e}")

        return metrics

    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics"""
        metrics = {}

        try:
            # Simulated system metrics (in real implementation, would collect actual system stats)
            metrics['cpu_usage_percent'] = np.random.normal(45, 10)  # Simulated CPU usage
            metrics['memory_usage_percent'] = np.random.normal(60, 15)  # Simulated memory usage
            metrics['disk_usage_percent'] = np.random.normal(75, 5)  # Simulated disk usage
            metrics['network_throughput_mbps'] = np.random.normal(150, 25)  # Simulated network

            # Database sizes
            for db_path in [self.feedback_db, self.training_db, self.versions_db, self.metrics_db]:
                if Path(db_path).exists():
                    size_mb = Path(db_path).stat().st_size / (1024 * 1024)
                    db_name = Path(db_path).stem
                    metrics[f'{db_name}_size_mb'] = size_mb

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

        return metrics

    def _create_metric_snapshot(self, metric_name: str, value: float, timestamp: datetime) -> MetricSnapshot:
        """Create a metric snapshot with status and trend analysis"""
        # Get threshold for this metric
        threshold = None
        status = "good"

        thresholds = self.config.get("alert_thresholds", {}).get(metric_name)
        if thresholds:
            if metric_name in ["error_rate"]:  # Lower is better
                if value >= thresholds.get("critical", float('inf')):
                    status = "critical"
                    threshold = thresholds["critical"]
                elif value >= thresholds.get("warning", float('inf')):
                    status = "warning"
                    threshold = thresholds["warning"]
            else:  # Higher is better
                if value <= thresholds.get("critical", 0):
                    status = "critical"
                    threshold = thresholds["critical"]
                elif value <= thresholds.get("warning", 0):
                    status = "warning"
                    threshold = thresholds["warning"]

        # Calculate trend
        trend = "stable"
        if metric_name in self.current_metrics and len(self.current_metrics[metric_name]) > 1:
            recent_values = [m.value for m in self.current_metrics[metric_name][-5:]]
            if len(recent_values) >= 2:
                if recent_values[-1] > recent_values[-2] * 1.05:  # 5% increase
                    trend = "up"
                elif recent_values[-1] < recent_values[-2] * 0.95:  # 5% decrease
                    trend = "down"

        return MetricSnapshot(
            timestamp=timestamp,
            metric_name=metric_name,
            value=value,
            threshold=threshold,
            status=status,
            trend=trend
        )

    async def _store_metric_snapshot(self, snapshot: MetricSnapshot):
        """Store metric snapshot in database"""
        try:
            with sqlite3.connect(self.metrics_db) as conn:
                conn.execute("""
                    INSERT INTO metric_snapshots
                    (timestamp, metric_name, value, threshold, status, trend)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.timestamp.isoformat(),
                    snapshot.metric_name,
                    snapshot.value,
                    snapshot.threshold,
                    snapshot.status,
                    snapshot.trend
                ))
        except Exception as e:
            logger.error(f"Error storing metric snapshot: {e}")

    async def _check_alerts_loop(self):
        """Check for alert conditions"""
        while self.monitoring_active:
            try:
                await self._check_alerts()
                await asyncio.sleep(60)  # Check alerts every minute
            except Exception as e:
                logger.error(f"Error in alert checking: {e}")
                await asyncio.sleep(5)

    async def _check_alerts(self):
        """Check current metrics against alert thresholds"""
        current_time = datetime.now()

        for metric_name, snapshots in self.current_metrics.items():
            if not snapshots:
                continue

            latest_snapshot = snapshots[-1]

            if latest_snapshot.status in ["warning", "critical"]:
                # Check if we already have a recent alert for this metric
                recent_alert = await self._get_recent_alert(metric_name, hours=1)

                if not recent_alert:
                    alert = {
                        "timestamp": current_time,
                        "alert_type": "threshold_violation",
                        "severity": latest_snapshot.status,
                        "message": f"{metric_name} is {latest_snapshot.status}: {latest_snapshot.value:.2f}",
                        "metric_name": metric_name,
                        "current_value": latest_snapshot.value,
                        "threshold_value": latest_snapshot.threshold,
                        "acknowledged": False,
                        "resolved": False
                    }

                    await self._store_alert(alert)
                    self.alert_history.append(alert)

                    logger.warning(f"Alert generated: {alert['message']}")

    async def _get_recent_alert(self, metric_name: str, hours: int = 1) -> Optional[Dict[str, Any]]:
        """Check for recent alerts for a metric"""
        try:
            with sqlite3.connect(self.metrics_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM system_alerts
                    WHERE metric_name = ?
                    AND timestamp >= datetime('now', '-{} hours')
                    AND resolved = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 1
                """.format(hours), (metric_name,))

                row = cursor.fetchone()
                return dict(row) if row else None

        except Exception as e:
            logger.error(f"Error checking recent alerts: {e}")
            return None

    async def _store_alert(self, alert: Dict[str, Any]):
        """Store alert in database"""
        try:
            with sqlite3.connect(self.metrics_db) as conn:
                conn.execute("""
                    INSERT INTO system_alerts
                    (alert_type, severity, message, metric_name, current_value, threshold_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    alert["alert_type"],
                    alert["severity"],
                    alert["message"],
                    alert["metric_name"],
                    alert["current_value"],
                    alert["threshold_value"]
                ))
        except Exception as e:
            logger.error(f"Error storing alert: {e}")

    async def _broadcast_updates_loop(self):
        """Broadcast updates to connected WebSocket clients"""
        while self.monitoring_active:
            try:
                if self.active_connections:
                    dashboard_data = await self._generate_dashboard_data()
                    await self._broadcast_to_all_connections(dashboard_data)

                await asyncio.sleep(self.config["refresh_interval_seconds"])

            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(5)

    async def _generate_dashboard_data(self) -> DashboardData:
        """Generate complete dashboard data"""
        current_time = datetime.now()

        # System overview
        system_overview = {
            "status": "operational" if self.monitoring_active else "stopped",
            "last_update": self.last_update.isoformat(),
            "uptime_hours": (current_time - self.last_update).total_seconds() / 3600,
            "total_metrics": len(self.current_metrics),
            "active_alerts": len([a for a in self.alert_history if not a.get("resolved", False)])
        }

        # Performance metrics summary
        performance_summary = {}
        for metric_name, snapshots in self.current_metrics.items():
            if snapshots:
                latest = snapshots[-1]
                performance_summary[metric_name] = {
                    "current_value": latest.value,
                    "status": latest.status,
                    "trend": latest.trend,
                    "threshold": latest.threshold
                }

        # Learning progress
        learning_progress = await self._get_learning_progress()

        # Feedback analytics
        feedback_analytics = await self._get_feedback_analytics()

        # Model status
        model_status = await self._get_model_status()

        # Recent alerts
        recent_alerts = self.alert_history[-10:]  # Last 10 alerts

        return DashboardData(
            system_overview=system_overview,
            performance_metrics=self.current_metrics,
            learning_progress=learning_progress,
            feedback_analytics=feedback_analytics,
            model_status=model_status,
            alerts=recent_alerts,
            timestamp=current_time
        )

    async def _get_learning_progress(self) -> Dict[str, Any]:
        """Get learning progress metrics"""
        try:
            with sqlite3.connect(self.training_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Training cycles completed
                cursor.execute("""
                    SELECT COUNT(*) as count FROM training_runs
                    WHERE status = 'completed'
                    AND start_time >= datetime('now', '-30 days')
                """)
                completed_cycles = cursor.fetchone()['count']

                # Models deployed
                cursor.execute("""
                    SELECT COUNT(*) as count FROM deployments
                    WHERE deployment_time >= datetime('now', '-30 days')
                """)
                models_deployed = cursor.fetchone()['count']

                return {
                    "training_cycles_30d": completed_cycles,
                    "models_deployed_30d": models_deployed,
                    "learning_velocity": completed_cycles / 30,  # Cycles per day
                    "deployment_rate": models_deployed / 30  # Deployments per day
                }

        except Exception as e:
            logger.error(f"Error getting learning progress: {e}")
            return {}

    async def _get_feedback_analytics(self) -> Dict[str, Any]:
        """Get feedback analytics"""
        try:
            with sqlite3.connect(self.feedback_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Feedback volume trend
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM feedback_entries
                    WHERE created_at >= datetime('now', '-7 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """)
                volume_trend = [dict(row) for row in cursor.fetchall()]

                # Quality distribution
                cursor.execute("""
                    SELECT accuracy_rating, COUNT(*) as count
                    FROM feedback_entries
                    WHERE accuracy_rating IS NOT NULL
                    AND created_at >= datetime('now', '-7 days')
                    GROUP BY accuracy_rating
                """)
                quality_distribution = {row['accuracy_rating']: row['count'] for row in cursor.fetchall()}

                return {
                    "volume_trend": volume_trend,
                    "quality_distribution": quality_distribution,
                    "total_feedback_7d": sum(quality_distribution.values())
                }

        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {}

    async def _get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        try:
            with sqlite3.connect(self.versions_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Models by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM model_metadata
                    GROUP BY status
                """)
                status_distribution = {row['status']: row['count'] for row in cursor.fetchall()}

                # Recent deployments
                cursor.execute("""
                    SELECT model_id, deployment_time, status
                    FROM deployments
                    WHERE deployment_time >= datetime('now', '-7 days')
                    ORDER BY deployment_time DESC
                    LIMIT 5
                """)
                recent_deployments = [dict(row) for row in cursor.fetchall()]

                return {
                    "status_distribution": status_distribution,
                    "recent_deployments": recent_deployments,
                    "total_models": sum(status_distribution.values())
                }

        except Exception as e:
            logger.error(f"Error getting model status: {e}")
            return {}

    async def _broadcast_to_all_connections(self, data: DashboardData):
        """Broadcast data to all connected WebSocket clients"""
        if not self.active_connections:
            return

        message = json.dumps(asdict(data), default=str)

        # Send to all connections, removing any that are closed
        active_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                active_connections.append(connection)
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")

        self.active_connections = active_connections

    def _setup_routes(self):
        """Setup FastAPI routes for the dashboard"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            return self._generate_dashboard_html()

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

        @self.app.get("/api/metrics")
        async def get_current_metrics():
            return {
                "metrics": {name: [asdict(m) for m in snapshots[-50:]]
                           for name, snapshots in self.current_metrics.items()},
                "last_update": self.last_update.isoformat()
            }

        @self.app.get("/api/alerts")
        async def get_alerts():
            return {
                "alerts": self.alert_history[-50:],  # Last 50 alerts
                "active_count": len([a for a in self.alert_history if not a.get("resolved", False)])
            }

        @self.app.post("/api/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: int):
            # Mark alert as acknowledged
            return {"status": "acknowledged"}

    def _generate_dashboard_html(self) -> str:
        """Generate the dashboard HTML page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Performance Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: white; }
                .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .metric-card { background: #2a2a2a; padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50; }
                .metric-card.warning { border-left-color: #FF9800; }
                .metric-card.critical { border-left-color: #F44336; }
                .metric-value { font-size: 2em; font-weight: bold; margin: 10px 0; }
                .metric-label { color: #888; }
                .chart-container { height: 300px; margin-top: 20px; }
                .alerts-panel { background: #2a2a2a; padding: 20px; border-radius: 8px; margin-top: 20px; }
                .alert-item { padding: 10px; margin: 5px 0; border-radius: 4px; }
                .alert-warning { background: #FF9800; }
                .alert-critical { background: #F44336; }
                .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
                .status-good { background: #4CAF50; }
                .status-warning { background: #FF9800; }
                .status-critical { background: #F44336; }
                h1, h2 { color: #fff; }
            </style>
        </head>
        <body>
            <h1>🤖 AI Performance Dashboard</h1>

            <div class="dashboard-grid" id="metricsGrid">
                <!-- Metrics will be populated here -->
            </div>

            <div class="alerts-panel">
                <h2>🚨 System Alerts</h2>
                <div id="alertsList">
                    <!-- Alerts will be populated here -->
                </div>
            </div>

            <script>
                const socket = new WebSocket('ws://localhost:8005/ws');

                socket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };

                function updateDashboard(data) {
                    updateMetrics(data.performance_metrics);
                    updateAlerts(data.alerts);
                }

                function updateMetrics(metrics) {
                    const grid = document.getElementById('metricsGrid');
                    grid.innerHTML = '';

                    for (const [name, snapshots] of Object.entries(metrics)) {
                        if (snapshots.length === 0) continue;

                        const latest = snapshots[snapshots.length - 1];
                        const card = document.createElement('div');
                        card.className = `metric-card ${latest.status}`;

                        card.innerHTML = `
                            <div class="metric-label">${name.replace(/_/g, ' ').toUpperCase()}</div>
                            <div class="metric-value">
                                <span class="status-indicator status-${latest.status}"></span>
                                ${formatValue(latest.value, name)}
                                <span style="font-size: 0.5em; color: #888;">
                                    ${latest.trend === 'up' ? '↗️' : latest.trend === 'down' ? '↘️' : '➡️'}
                                </span>
                            </div>
                            ${latest.threshold ? `<div style="color: #888;">Threshold: ${latest.threshold}</div>` : ''}
                        `;

                        grid.appendChild(card);
                    }
                }

                function updateAlerts(alerts) {
                    const alertsList = document.getElementById('alertsList');
                    alertsList.innerHTML = '';

                    if (alerts.length === 0) {
                        alertsList.innerHTML = '<div style="color: #4CAF50;">✅ No active alerts</div>';
                        return;
                    }

                    alerts.slice(-5).reverse().forEach(alert => {
                        const alertItem = document.createElement('div');
                        alertItem.className = `alert-item alert-${alert.severity}`;
                        alertItem.innerHTML = `
                            <strong>${alert.severity.toUpperCase()}</strong>: ${alert.message}
                            <div style="font-size: 0.8em; opacity: 0.8;">${new Date(alert.timestamp).toLocaleString()}</div>
                        `;
                        alertsList.appendChild(alertItem);
                    });
                }

                function formatValue(value, metricName) {
                    if (metricName.includes('rate') || metricName.includes('accuracy')) {
                        return (value * 100).toFixed(1) + '%';
                    } else if (metricName.includes('time')) {
                        return value.toFixed(0) + 'ms';
                    } else if (metricName.includes('size_mb')) {
                        return value.toFixed(1) + 'MB';
                    } else if (metricName.includes('percent')) {
                        return value.toFixed(1) + '%';
                    } else {
                        return value.toFixed(2);
                    }
                }

                // Refresh connection every 30 seconds
                setInterval(() => {
                    if (socket.readyState === WebSocket.CLOSED) {
                        location.reload();
                    }
                }, 30000);
            </script>
        </body>
        </html>
        """

    async def run_server(self, host: str = "localhost", port: int = 8005):
        """Run the dashboard server"""
        logger.info(f"Starting dashboard server on {host}:{port}")

        await self.start_monitoring()

        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)

        try:
            await server.serve()
        finally:
            await self.stop_monitoring()

# Example usage
async def main():
    """Example usage of the dashboard"""
    dashboard = PerformanceMonitoringDashboard()

    # Run the dashboard server
    await dashboard.run_server()

if __name__ == "__main__":
    asyncio.run(main())