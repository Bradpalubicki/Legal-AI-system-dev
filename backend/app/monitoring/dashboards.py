# =============================================================================
# Legal AI System - Performance Dashboards and Visualization
# =============================================================================
# Comprehensive dashboard system for monitoring legal document processing,
# AI services, compliance, and system performance with real-time updates
# =============================================================================

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from ..database import get_db
from .models import (
    MetricDefinition, MetricSample, AggregatedMetric,
    AlertRule, Alert, SLADefinition, SLAMeasurement
)
from .analytics import PerformanceAnalytics, TrendAnalysis
from .sla import SLAEngine

logger = logging.getLogger(__name__)

# =============================================================================
# DASHBOARD TYPES AND ENUMS
# =============================================================================

class DashboardType(str, Enum):
    SYSTEM_OVERVIEW = "system_overview"
    DOCUMENT_PROCESSING = "document_processing"
    AI_SERVICES = "ai_services"
    COMPLIANCE = "compliance"
    SLA_MONITORING = "sla_monitoring"
    SECURITY = "security"
    LEGAL_METRICS = "legal_metrics"

class WidgetType(str, Enum):
    METRIC_CARD = "metric_card"
    TIME_SERIES = "time_series"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    HEAT_MAP = "heat_map"
    ALERT_FEED = "alert_feed"
    SLA_STATUS = "sla_status"
    TREND_INDICATOR = "trend_indicator"
    GAUGE = "gauge"
    TABLE = "table"

class TimeRange(str, Enum):
    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"

@dataclass
class WidgetData:
    """Data structure for dashboard widgets."""
    widget_id: str
    widget_type: WidgetType
    title: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None

@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    dashboard_id: str
    dashboard_type: DashboardType
    title: str
    description: str
    widgets: List[Dict[str, Any]]
    refresh_interval: int = 30  # seconds
    auto_refresh: bool = True

# =============================================================================
# DASHBOARD DATA PROVIDERS
# =============================================================================

class MetricDataProvider:
    """Provides metric data for dashboard widgets."""
    
    def __init__(self, analytics: PerformanceAnalytics):
        self.analytics = analytics
    
    async def get_current_metrics(self, db: AsyncSession, metric_names: List[str]) -> Dict[str, float]:
        """Get current values for specified metrics."""
        current_metrics = {}
        
        for metric_name in metric_names:
            query = select(MetricSample).where(
                MetricSample.metric_name == metric_name
            ).order_by(desc(MetricSample.timestamp)).limit(1)
            
            result = await db.execute(query)
            sample = result.scalar_one_or_none()
            
            if sample:
                current_metrics[metric_name] = sample.value
            else:
                current_metrics[metric_name] = 0.0
        
        return current_metrics
    
    async def get_time_series_data(
        self, 
        db: AsyncSession, 
        metric_names: List[str], 
        time_range: TimeRange
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """Get time series data for specified metrics."""
        end_time = datetime.utcnow()
        
        # Calculate start time based on range
        range_mapping = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(days=1),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
            TimeRange.LAST_30_DAYS: timedelta(days=30),
            TimeRange.LAST_90_DAYS: timedelta(days=90)
        }
        
        start_time = end_time - range_mapping[time_range]
        
        time_series_data = {}
        
        for metric_name in metric_names:
            query = select(MetricSample).where(
                and_(
                    MetricSample.metric_name == metric_name,
                    MetricSample.timestamp >= start_time,
                    MetricSample.timestamp <= end_time
                )
            ).order_by(MetricSample.timestamp)
            
            result = await db.execute(query)
            samples = result.scalars().all()
            
            time_series_data[metric_name] = [
                (sample.timestamp, sample.value) for sample in samples
            ]
        
        return time_series_data
    
    async def get_aggregated_metrics(
        self, 
        db: AsyncSession, 
        metric_names: List[str], 
        aggregation_type: str,
        time_range: TimeRange
    ) -> Dict[str, float]:
        """Get aggregated metrics (avg, sum, min, max)."""
        end_time = datetime.utcnow()
        range_mapping = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(days=1),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
            TimeRange.LAST_30_DAYS: timedelta(days=30),
            TimeRange.LAST_90_DAYS: timedelta(days=90)
        }
        start_time = end_time - range_mapping[time_range]
        
        aggregated_data = {}
        
        for metric_name in metric_names:
            if aggregation_type == "avg":
                query = select(func.avg(MetricSample.value)).where(
                    and_(
                        MetricSample.metric_name == metric_name,
                        MetricSample.timestamp >= start_time,
                        MetricSample.timestamp <= end_time
                    )
                )
            elif aggregation_type == "sum":
                query = select(func.sum(MetricSample.value)).where(
                    and_(
                        MetricSample.metric_name == metric_name,
                        MetricSample.timestamp >= start_time,
                        MetricSample.timestamp <= end_time
                    )
                )
            elif aggregation_type == "min":
                query = select(func.min(MetricSample.value)).where(
                    and_(
                        MetricSample.metric_name == metric_name,
                        MetricSample.timestamp >= start_time,
                        MetricSample.timestamp <= end_time
                    )
                )
            elif aggregation_type == "max":
                query = select(func.max(MetricSample.value)).where(
                    and_(
                        MetricSample.metric_name == metric_name,
                        MetricSample.timestamp >= start_time,
                        MetricSample.timestamp <= end_time
                    )
                )
            else:
                continue
                
            result = await db.execute(query)
            value = result.scalar()
            aggregated_data[metric_name] = float(value) if value else 0.0
        
        return aggregated_data

class AlertDataProvider:
    """Provides alert data for dashboard widgets."""
    
    async def get_active_alerts(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        query = select(Alert).where(
            Alert.status.in_(["triggered", "escalated"])
        ).order_by(desc(Alert.triggered_at))
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        return [
            {
                "id": str(alert.id),
                "severity": alert.severity,
                "message": alert.message,
                "triggered_at": alert.triggered_at.isoformat(),
                "metric_name": alert.metric_name,
                "status": alert.status
            }
            for alert in alerts
        ]
    
    async def get_alert_statistics(self, db: AsyncSession, time_range: TimeRange) -> Dict[str, int]:
        """Get alert statistics for the specified time range."""
        end_time = datetime.utcnow()
        range_mapping = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(days=1),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
            TimeRange.LAST_30_DAYS: timedelta(days=30),
            TimeRange.LAST_90_DAYS: timedelta(days=90)
        }
        start_time = end_time - range_mapping[time_range]
        
        # Count alerts by severity
        query = select(
            Alert.severity,
            func.count(Alert.id).label('count')
        ).where(
            Alert.triggered_at >= start_time
        ).group_by(Alert.severity)
        
        result = await db.execute(query)
        severity_counts = {row.severity: row.count for row in result}
        
        # Total alerts
        total_query = select(func.count(Alert.id)).where(
            Alert.triggered_at >= start_time
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        
        return {
            "total": total_count or 0,
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
            "medium": severity_counts.get("medium", 0),
            "low": severity_counts.get("low", 0)
        }

class SLADataProvider:
    """Provides SLA data for dashboard widgets."""
    
    def __init__(self, sla_engine: SLAEngine):
        self.sla_engine = sla_engine
    
    async def get_sla_status(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get current SLA status for all defined SLAs."""
        query = select(SLADefinition)
        result = await db.execute(query)
        sla_definitions = result.scalars().all()
        
        sla_status_list = []
        
        for sla_def in sla_definitions:
            # Get latest measurement
            measurement_query = select(SLAMeasurement).where(
                SLAMeasurement.sla_definition_id == sla_def.id
            ).order_by(desc(SLAMeasurement.measurement_end)).limit(1)
            
            measurement_result = await db.execute(measurement_query)
            latest_measurement = measurement_result.scalar_one_or_none()
            
            if latest_measurement:
                sla_status_list.append({
                    "sla_id": str(sla_def.id),
                    "name": sla_def.name,
                    "target": sla_def.target_value,
                    "actual": latest_measurement.actual_value,
                    "compliance": latest_measurement.compliance_percentage,
                    "status": "compliant" if latest_measurement.compliance_percentage >= 100 else "breach",
                    "measurement_time": latest_measurement.measurement_end.isoformat()
                })
        
        return sla_status_list
    
    async def get_sla_trends(self, db: AsyncSession, sla_id: str, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Get SLA trend data over time."""
        end_time = datetime.utcnow()
        range_mapping = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(days=1),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
            TimeRange.LAST_30_DAYS: timedelta(days=30),
            TimeRange.LAST_90_DAYS: timedelta(days=90)
        }
        start_time = end_time - range_mapping[time_range]
        
        query = select(SLAMeasurement).where(
            and_(
                SLAMeasurement.sla_definition_id == sla_id,
                SLAMeasurement.measurement_end >= start_time
            )
        ).order_by(SLAMeasurement.measurement_end)
        
        result = await db.execute(query)
        measurements = result.scalars().all()
        
        return [
            {
                "timestamp": measurement.measurement_end.isoformat(),
                "actual_value": measurement.actual_value,
                "compliance_percentage": measurement.compliance_percentage,
                "is_breach": measurement.is_breach
            }
            for measurement in measurements
        ]

# =============================================================================
# DASHBOARD WIDGET BUILDERS
# =============================================================================

class WidgetBuilder:
    """Builds dashboard widgets with data."""
    
    def __init__(
        self, 
        metric_provider: MetricDataProvider,
        alert_provider: AlertDataProvider,
        sla_provider: SLADataProvider
    ):
        self.metric_provider = metric_provider
        self.alert_provider = alert_provider
        self.sla_provider = sla_provider
    
    async def build_metric_card_widget(
        self, 
        db: AsyncSession,
        widget_id: str,
        title: str,
        metric_name: str,
        format_type: str = "number"
    ) -> WidgetData:
        """Build a metric card widget."""
        current_metrics = await self.metric_provider.get_current_metrics(db, [metric_name])
        value = current_metrics.get(metric_name, 0.0)
        
        return WidgetData(
            widget_id=widget_id,
            widget_type=WidgetType.METRIC_CARD,
            title=title,
            data={
                "value": value,
                "format": format_type,
                "metric_name": metric_name
            },
            last_updated=datetime.utcnow()
        )
    
    async def build_time_series_widget(
        self,
        db: AsyncSession,
        widget_id: str,
        title: str,
        metric_names: List[str],
        time_range: TimeRange
    ) -> WidgetData:
        """Build a time series chart widget."""
        time_series_data = await self.metric_provider.get_time_series_data(
            db, metric_names, time_range
        )
        
        # Format data for charting
        chart_data = []
        for metric_name, data_points in time_series_data.items():
            chart_data.append({
                "name": metric_name,
                "data": [
                    {"x": timestamp.isoformat(), "y": value}
                    for timestamp, value in data_points
                ]
            })
        
        return WidgetData(
            widget_id=widget_id,
            widget_type=WidgetType.TIME_SERIES,
            title=title,
            data={
                "series": chart_data,
                "time_range": time_range
            },
            last_updated=datetime.utcnow()
        )
    
    async def build_alert_feed_widget(
        self,
        db: AsyncSession,
        widget_id: str,
        title: str = "Active Alerts"
    ) -> WidgetData:
        """Build an alert feed widget."""
        active_alerts = await self.alert_provider.get_active_alerts(db)
        
        return WidgetData(
            widget_id=widget_id,
            widget_type=WidgetType.ALERT_FEED,
            title=title,
            data={
                "alerts": active_alerts,
                "total_count": len(active_alerts)
            },
            last_updated=datetime.utcnow()
        )
    
    async def build_sla_status_widget(
        self,
        db: AsyncSession,
        widget_id: str,
        title: str = "SLA Status"
    ) -> WidgetData:
        """Build an SLA status widget."""
        sla_status = await self.sla_provider.get_sla_status(db)
        
        # Calculate overall SLA health
        total_slas = len(sla_status)
        compliant_slas = len([sla for sla in sla_status if sla["status"] == "compliant"])
        health_percentage = (compliant_slas / total_slas * 100) if total_slas > 0 else 100
        
        return WidgetData(
            widget_id=widget_id,
            widget_type=WidgetType.SLA_STATUS,
            title=title,
            data={
                "slas": sla_status,
                "total_slas": total_slas,
                "compliant_slas": compliant_slas,
                "health_percentage": health_percentage
            },
            last_updated=datetime.utcnow()
        )
    
    async def build_gauge_widget(
        self,
        db: AsyncSession,
        widget_id: str,
        title: str,
        metric_name: str,
        min_value: float = 0,
        max_value: float = 100,
        thresholds: Optional[Dict[str, float]] = None
    ) -> WidgetData:
        """Build a gauge widget."""
        current_metrics = await self.metric_provider.get_current_metrics(db, [metric_name])
        value = current_metrics.get(metric_name, 0.0)
        
        if thresholds is None:
            thresholds = {"warning": max_value * 0.7, "critical": max_value * 0.9}
        
        return WidgetData(
            widget_id=widget_id,
            widget_type=WidgetType.GAUGE,
            title=title,
            data={
                "value": value,
                "min": min_value,
                "max": max_value,
                "thresholds": thresholds,
                "metric_name": metric_name
            },
            last_updated=datetime.utcnow()
        )

# =============================================================================
# PREDEFINED DASHBOARD CONFIGURATIONS
# =============================================================================

class DashboardTemplates:
    """Predefined dashboard templates for different use cases."""
    
    @staticmethod
    def get_system_overview_dashboard() -> DashboardConfig:
        """System overview dashboard configuration."""
        return DashboardConfig(
            dashboard_id="system_overview",
            dashboard_type=DashboardType.SYSTEM_OVERVIEW,
            title="System Overview",
            description="High-level system health and performance metrics",
            widgets=[
                {
                    "id": "system_health",
                    "type": "metric_card",
                    "title": "System Health",
                    "config": {"metric_name": "system_health_status", "format": "status"}
                },
                {
                    "id": "active_users",
                    "type": "gauge",
                    "title": "Active Users",
                    "config": {"metric_name": "active_users_current", "max_value": 1000}
                },
                {
                    "id": "request_rate",
                    "type": "time_series",
                    "title": "Request Rate (24h)",
                    "config": {
                        "metric_names": ["http_requests_total"],
                        "time_range": "24h"
                    }
                },
                {
                    "id": "active_alerts",
                    "type": "alert_feed",
                    "title": "Active Alerts",
                    "config": {}
                },
                {
                    "id": "sla_overview",
                    "type": "sla_status",
                    "title": "SLA Status",
                    "config": {}
                }
            ]
        )
    
    @staticmethod
    def get_document_processing_dashboard() -> DashboardConfig:
        """Document processing dashboard configuration."""
        return DashboardConfig(
            dashboard_id="document_processing",
            dashboard_type=DashboardType.DOCUMENT_PROCESSING,
            title="Document Processing",
            description="Document processing performance and metrics",
            widgets=[
                {
                    "id": "docs_processed",
                    "type": "metric_card",
                    "title": "Documents Processed (24h)",
                    "config": {"metric_name": "document_processing_total", "format": "number"}
                },
                {
                    "id": "processing_time",
                    "type": "gauge",
                    "title": "Avg Processing Time",
                    "config": {
                        "metric_name": "document_processing_duration_seconds", 
                        "max_value": 300,
                        "thresholds": {"warning": 180, "critical": 240}
                    }
                },
                {
                    "id": "processing_errors",
                    "type": "metric_card",
                    "title": "Processing Errors (24h)",
                    "config": {"metric_name": "document_processing_errors_total", "format": "number"}
                },
                {
                    "id": "processing_trend",
                    "type": "time_series",
                    "title": "Processing Volume Trend (7d)",
                    "config": {
                        "metric_names": ["document_processing_total"],
                        "time_range": "7d"
                    }
                }
            ]
        )
    
    @staticmethod
    def get_ai_services_dashboard() -> DashboardConfig:
        """AI services dashboard configuration."""
        return DashboardConfig(
            dashboard_id="ai_services",
            dashboard_type=DashboardType.AI_SERVICES,
            title="AI Services",
            description="AI service performance and usage metrics",
            widgets=[
                {
                    "id": "ai_requests",
                    "type": "metric_card",
                    "title": "AI Requests (24h)",
                    "config": {"metric_name": "ai_request_duration_seconds", "format": "number"}
                },
                {
                    "id": "token_usage",
                    "type": "metric_card",
                    "title": "Token Usage (24h)",
                    "config": {"metric_name": "ai_token_usage_total", "format": "number"}
                },
                {
                    "id": "rate_limits",
                    "type": "metric_card",
                    "title": "Rate Limit Errors (24h)",
                    "config": {"metric_name": "ai_api_rate_limit_errors_total", "format": "number"}
                },
                {
                    "id": "ai_response_time",
                    "type": "gauge",
                    "title": "Avg Response Time",
                    "config": {
                        "metric_name": "ai_request_duration_seconds",
                        "max_value": 60,
                        "thresholds": {"warning": 30, "critical": 45}
                    }
                }
            ]
        )
    
    @staticmethod
    def get_compliance_dashboard() -> DashboardConfig:
        """Compliance monitoring dashboard configuration."""
        return DashboardConfig(
            dashboard_id="compliance",
            dashboard_type=DashboardType.COMPLIANCE,
            title="Compliance Monitoring",
            description="Legal and regulatory compliance metrics",
            widgets=[
                {
                    "id": "audit_entries",
                    "type": "metric_card",
                    "title": "Audit Entries (24h)",
                    "config": {"metric_name": "audit_log_entries_total", "format": "number"}
                },
                {
                    "id": "data_retention_compliance",
                    "type": "gauge",
                    "title": "Data Retention Compliance",
                    "config": {
                        "metric_name": "data_retention_compliant_records",
                        "max_value": 100,
                        "thresholds": {"warning": 85, "critical": 75}
                    }
                },
                {
                    "id": "privileged_ops",
                    "type": "metric_card",
                    "title": "Privileged Operations (24h)",
                    "config": {"metric_name": "privileged_operations_total", "format": "number"}
                },
                {
                    "id": "client_data_access",
                    "type": "time_series",
                    "title": "Client Data Access Trend (7d)",
                    "config": {
                        "metric_names": ["client_data_access_total"],
                        "time_range": "7d"
                    }
                }
            ]
        )

# =============================================================================
# DASHBOARD ENGINE
# =============================================================================

class DashboardEngine:
    """Main dashboard engine that orchestrates data collection and rendering."""
    
    def __init__(self, analytics: PerformanceAnalytics, sla_engine: SLAEngine):
        self.analytics = analytics
        self.sla_engine = sla_engine
        self.metric_provider = MetricDataProvider(analytics)
        self.alert_provider = AlertDataProvider()
        self.sla_provider = SLADataProvider(sla_engine)
        self.widget_builder = WidgetBuilder(
            self.metric_provider,
            self.alert_provider,
            self.sla_provider
        )
        self.templates = DashboardTemplates()
    
    async def get_dashboard_data(
        self, 
        db: AsyncSession, 
        dashboard_type: DashboardType,
        time_range: TimeRange = TimeRange.LAST_24_HOURS
    ) -> Dict[str, Any]:
        """Get complete dashboard data for the specified type."""
        try:
            # Get dashboard configuration
            dashboard_config = self._get_dashboard_config(dashboard_type)
            
            # Build widgets
            widgets_data = []
            for widget_config in dashboard_config.widgets:
                widget_data = await self._build_widget(
                    db, widget_config, time_range
                )
                widgets_data.append(asdict(widget_data))
            
            return {
                "dashboard_id": dashboard_config.dashboard_id,
                "title": dashboard_config.title,
                "description": dashboard_config.description,
                "widgets": widgets_data,
                "last_updated": datetime.utcnow().isoformat(),
                "refresh_interval": dashboard_config.refresh_interval
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")
    
    def _get_dashboard_config(self, dashboard_type: DashboardType) -> DashboardConfig:
        """Get dashboard configuration for the specified type."""
        config_mapping = {
            DashboardType.SYSTEM_OVERVIEW: self.templates.get_system_overview_dashboard,
            DashboardType.DOCUMENT_PROCESSING: self.templates.get_document_processing_dashboard,
            DashboardType.AI_SERVICES: self.templates.get_ai_services_dashboard,
            DashboardType.COMPLIANCE: self.templates.get_compliance_dashboard
        }
        
        config_func = config_mapping.get(dashboard_type)
        if not config_func:
            raise ValueError(f"Unknown dashboard type: {dashboard_type}")
        
        return config_func()
    
    async def _build_widget(
        self, 
        db: AsyncSession, 
        widget_config: Dict[str, Any],
        time_range: TimeRange
    ) -> WidgetData:
        """Build a single widget based on configuration."""
        widget_type = widget_config["type"]
        widget_id = widget_config["id"]
        title = widget_config["title"]
        config = widget_config["config"]
        
        if widget_type == "metric_card":
            return await self.widget_builder.build_metric_card_widget(
                db, widget_id, title, config["metric_name"], config.get("format", "number")
            )
        elif widget_type == "time_series":
            return await self.widget_builder.build_time_series_widget(
                db, widget_id, title, config["metric_names"], 
                TimeRange(config.get("time_range", time_range))
            )
        elif widget_type == "alert_feed":
            return await self.widget_builder.build_alert_feed_widget(db, widget_id, title)
        elif widget_type == "sla_status":
            return await self.widget_builder.build_sla_status_widget(db, widget_id, title)
        elif widget_type == "gauge":
            return await self.widget_builder.build_gauge_widget(
                db, widget_id, title, config["metric_name"],
                config.get("min_value", 0), config["max_value"],
                config.get("thresholds")
            )
        else:
            raise ValueError(f"Unknown widget type: {widget_type}")

# =============================================================================
# WEBSOCKET CONNECTION MANAGER
# =============================================================================

class DashboardWebSocketManager:
    """Manages WebSocket connections for real-time dashboard updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.dashboard_engine: Optional[DashboardEngine] = None
    
    def set_dashboard_engine(self, dashboard_engine: DashboardEngine):
        """Set the dashboard engine for data updates."""
        self.dashboard_engine = dashboard_engine
    
    async def connect(self, websocket: WebSocket, dashboard_id: str):
        """Connect a WebSocket to a specific dashboard."""
        await websocket.accept()
        
        if dashboard_id not in self.active_connections:
            self.active_connections[dashboard_id] = []
        
        self.active_connections[dashboard_id].append(websocket)
        logger.info(f"WebSocket connected to dashboard {dashboard_id}")
    
    def disconnect(self, websocket: WebSocket, dashboard_id: str):
        """Disconnect a WebSocket from a dashboard."""
        if dashboard_id in self.active_connections:
            if websocket in self.active_connections[dashboard_id]:
                self.active_connections[dashboard_id].remove(websocket)
                
            if not self.active_connections[dashboard_id]:
                del self.active_connections[dashboard_id]
        
        logger.info(f"WebSocket disconnected from dashboard {dashboard_id}")
    
    async def broadcast_dashboard_update(
        self, 
        db: AsyncSession,
        dashboard_type: DashboardType,
        time_range: TimeRange = TimeRange.LAST_24_HOURS
    ):
        """Broadcast dashboard updates to all connected clients."""
        if not self.dashboard_engine:
            return
        
        dashboard_id = dashboard_type.value
        
        if dashboard_id not in self.active_connections:
            return
        
        try:
            # Get updated dashboard data
            dashboard_data = await self.dashboard_engine.get_dashboard_data(
                db, dashboard_type, time_range
            )
            
            message = {
                "type": "dashboard_update",
                "data": dashboard_data
            }
            
            # Broadcast to all connected clients
            disconnected = []
            for websocket in self.active_connections[dashboard_id]:
                try:
                    await websocket.send_json(message)
                except WebSocketDisconnect:
                    disconnected.append(websocket)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected clients
            for websocket in disconnected:
                self.disconnect(websocket, dashboard_id)
                
        except Exception as e:
            logger.error(f"Error broadcasting dashboard update: {e}")

# Global WebSocket manager instance
websocket_manager = DashboardWebSocketManager()

# =============================================================================
# API ENDPOINTS
# =============================================================================

router = APIRouter(prefix="/api/monitoring/dashboards", tags=["dashboards"])

@router.get("/{dashboard_type}")
async def get_dashboard(
    dashboard_type: DashboardType,
    time_range: TimeRange = TimeRange.LAST_24_HOURS,
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard data for the specified type."""
    analytics = PerformanceAnalytics()
    sla_engine = SLAEngine()
    dashboard_engine = DashboardEngine(analytics, sla_engine)
    
    return await dashboard_engine.get_dashboard_data(db, dashboard_type, time_range)

@router.websocket("/ws/{dashboard_type}")
async def dashboard_websocket(
    websocket: WebSocket,
    dashboard_type: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time dashboard updates."""
    dashboard_id = dashboard_type
    await websocket_manager.connect(websocket, dashboard_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, dashboard_id)

@router.get("/")
async def list_available_dashboards():
    """List all available dashboard types."""
    return {
        "dashboards": [
            {
                "id": dashboard_type.value,
                "name": dashboard_type.value.replace("_", " ").title(),
                "type": dashboard_type.value
            }
            for dashboard_type in DashboardType
        ]
    }

# =============================================================================
# DASHBOARD UPDATE SCHEDULER
# =============================================================================

class DashboardUpdateScheduler:
    """Schedules periodic dashboard updates for WebSocket clients."""
    
    def __init__(self, dashboard_engine: DashboardEngine, websocket_manager: DashboardWebSocketManager):
        self.dashboard_engine = dashboard_engine
        self.websocket_manager = websocket_manager
        self.websocket_manager.set_dashboard_engine(dashboard_engine)
        self.update_interval = 30  # seconds
        self._running = False
    
    async def start_periodic_updates(self, db: AsyncSession):
        """Start periodic dashboard updates."""
        self._running = True
        
        while self._running:
            try:
                # Update all dashboard types that have active connections
                for dashboard_type in DashboardType:
                    if dashboard_type.value in self.websocket_manager.active_connections:
                        await self.websocket_manager.broadcast_dashboard_update(
                            db, dashboard_type
                        )
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in periodic dashboard updates: {e}")
                await asyncio.sleep(self.update_interval)
    
    def stop(self):
        """Stop periodic updates."""
        self._running = False