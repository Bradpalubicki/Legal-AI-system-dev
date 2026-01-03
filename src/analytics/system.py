"""
System Analytics Module
Tracks system performance, infrastructure metrics, cost analytics, and operational insights.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import asyncio
from decimal import Decimal
import json
import psutil
import time


class SystemMetricType(str, Enum):
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    SCALABILITY = "scalability"
    SECURITY = "security"
    COST = "cost"
    RESOURCE_USAGE = "resource_usage"


class ServiceType(str, Enum):
    API_SERVER = "api_server"
    DATABASE = "database"
    CACHE = "cache"
    STORAGE = "storage"
    AI_PROCESSING = "ai_processing"
    BACKGROUND_JOBS = "background_jobs"
    FRONTEND = "frontend"
    CDN = "cdn"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE_CONNECTIONS = "database_connections"
    API_REQUESTS = "api_requests"


class CostCategory(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    AI_MODELS = "ai_models"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    THIRD_PARTY_APIS = "third_party_apis"
    PERSONNEL = "personnel"
    LICENSES = "licenses"


@dataclass
class PerformanceMetrics:
    service: ServiceType
    timestamp: datetime
    response_time_ms: float
    throughput_rps: float
    error_rate: float
    availability_percentage: float
    cpu_usage_percentage: float
    memory_usage_mb: float
    disk_io_mbps: float
    network_io_mbps: float
    database_query_time_ms: float
    cache_hit_rate: float
    concurrent_users: int
    queue_length: int
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ResourceUtilization:
    resource_type: ResourceType
    timestamp: datetime
    current_usage: float
    max_capacity: float
    utilization_percentage: float
    peak_usage: float
    avg_usage_24h: float
    trend_direction: str
    predicted_capacity_date: Optional[datetime]
    cost_per_unit: Decimal
    total_cost: Decimal
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class CostAnalytics:
    category: CostCategory
    period_start: datetime
    period_end: datetime
    total_cost: Decimal
    cost_per_user: Decimal
    cost_per_request: Decimal
    cost_breakdown: Dict[str, Decimal]
    cost_trend: float
    budget_variance: Decimal
    optimization_opportunities: List[str]
    projected_monthly_cost: Decimal
    roi_metrics: Dict[str, Any]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SecurityMetrics:
    timestamp: datetime
    failed_auth_attempts: int
    blocked_ip_addresses: int
    malicious_requests: int
    vulnerability_scans: int
    security_incidents: int
    compliance_score: float
    data_encryption_coverage: float
    access_control_violations: int
    audit_log_completeness: float
    threat_detection_alerts: int
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ScalabilityAnalysis:
    current_capacity: Dict[str, int]
    peak_load_handled: Dict[str, int]
    bottleneck_resources: List[str]
    scaling_recommendations: List[str]
    auto_scaling_events: int
    load_balancer_efficiency: float
    horizontal_scaling_potential: float
    vertical_scaling_cost: Decimal
    predicted_scaling_needs: Dict[str, Any]
    performance_under_load: Dict[str, float]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SystemAlert:
    alert_id: str
    service: ServiceType
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    duration_minutes: int
    impact_assessment: str
    recommended_action: str
    auto_resolved: bool
    acknowledged: bool
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SystemHealthReport:
    report_timestamp: datetime
    overall_health_score: float
    service_health: Dict[str, float]
    performance_metrics: List[PerformanceMetrics]
    resource_utilization: List[ResourceUtilization]
    cost_analytics: List[CostAnalytics]
    security_metrics: SecurityMetrics
    scalability_analysis: ScalabilityAnalysis
    active_alerts: List[SystemAlert]
    recommendations: List[str]
    key_insights: List[str]
    trend_analysis: Dict[str, Any]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class SystemAnalyticsMonitor:
    def __init__(self):
        self.metrics_history = {}
        self.cost_data = {}
        self.alerts = {}
        self.monitoring_enabled = True
        self.baseline_metrics = {}

    async def collect_performance_metrics(self, service: ServiceType) -> Optional[PerformanceMetrics]:
        """Collect real-time performance metrics for a service"""
        try:
            current_time = datetime.utcnow()

            # Collect system metrics using psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            # Service-specific metrics (simulated for demo)
            service_metrics = {
                ServiceType.API_SERVER: {
                    "response_time_ms": 85.4,
                    "throughput_rps": 142.7,
                    "error_rate": 0.02,
                    "concurrent_users": 45
                },
                ServiceType.DATABASE: {
                    "response_time_ms": 12.8,
                    "throughput_rps": 89.3,
                    "error_rate": 0.001,
                    "concurrent_users": 23
                },
                ServiceType.AI_PROCESSING: {
                    "response_time_ms": 2450.0,
                    "throughput_rps": 8.5,
                    "error_rate": 0.05,
                    "concurrent_users": 12
                }
            }

            metrics = service_metrics.get(service, service_metrics[ServiceType.API_SERVER])

            return PerformanceMetrics(
                service=service,
                timestamp=current_time,
                response_time_ms=metrics["response_time_ms"],
                throughput_rps=metrics["throughput_rps"],
                error_rate=metrics["error_rate"],
                availability_percentage=99.85,
                cpu_usage_percentage=cpu_percent,
                memory_usage_mb=memory.used / (1024 * 1024),
                disk_io_mbps=25.7,
                network_io_mbps=12.3,
                database_query_time_ms=15.4,
                cache_hit_rate=0.94,
                concurrent_users=metrics["concurrent_users"],
                queue_length=3
            )

        except Exception as e:
            print(f"Error collecting performance metrics: {e}")
            return None

    async def monitor_resource_utilization(self, resource_type: ResourceType) -> Optional[ResourceUtilization]:
        """Monitor resource utilization and capacity planning"""
        try:
            current_time = datetime.utcnow()

            # Get system resource data
            if resource_type == ResourceType.CPU:
                current_usage = psutil.cpu_percent(interval=1)
                max_capacity = 100.0
            elif resource_type == ResourceType.MEMORY:
                memory = psutil.virtual_memory()
                current_usage = memory.percent
                max_capacity = 100.0
            elif resource_type == ResourceType.DISK:
                disk = psutil.disk_usage('/')
                current_usage = disk.percent
                max_capacity = 100.0
            else:
                # Default metrics for other resource types
                current_usage = 65.5
                max_capacity = 100.0

            utilization_pct = (current_usage / max_capacity) * 100

            # Calculate trends and predictions
            peak_usage = current_usage * 1.2  # Simulate peak
            avg_24h = current_usage * 0.8    # Simulate 24h average

            trend = "increasing" if current_usage > avg_24h else "stable"

            # Predict capacity needs
            capacity_date = None
            if utilization_pct > 80:
                capacity_date = current_time + timedelta(days=30)

            # Cost calculations (example rates)
            cost_rates = {
                ResourceType.CPU: Decimal('0.05'),      # $0.05 per CPU hour
                ResourceType.MEMORY: Decimal('0.02'),   # $0.02 per GB hour
                ResourceType.DISK: Decimal('0.10'),     # $0.10 per GB hour
                ResourceType.NETWORK: Decimal('0.01'),  # $0.01 per GB
            }

            cost_per_unit = cost_rates.get(resource_type, Decimal('0.05'))
            total_cost = cost_per_unit * Decimal(str(current_usage))

            return ResourceUtilization(
                resource_type=resource_type,
                timestamp=current_time,
                current_usage=current_usage,
                max_capacity=max_capacity,
                utilization_percentage=utilization_pct,
                peak_usage=peak_usage,
                avg_usage_24h=avg_24h,
                trend_direction=trend,
                predicted_capacity_date=capacity_date,
                cost_per_unit=cost_per_unit,
                total_cost=total_cost
            )

        except Exception as e:
            print(f"Error monitoring resource utilization: {e}")
            return None

    async def analyze_costs(self, category: CostCategory, days_back: int = 30) -> Optional[CostAnalytics]:
        """Analyze system costs and optimization opportunities"""
        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=days_back)

            # Sample cost calculations based on category
            cost_data = {
                CostCategory.INFRASTRUCTURE: {
                    "total": Decimal('2450.00'),
                    "breakdown": {
                        "compute": Decimal('1200.00'),
                        "storage": Decimal('450.00'),
                        "networking": Decimal('300.00'),
                        "monitoring": Decimal('150.00'),
                        "backup": Decimal('350.00')
                    }
                },
                CostCategory.AI_MODELS: {
                    "total": Decimal('1875.00'),
                    "breakdown": {
                        "openai_gpt4": Decimal('850.00'),
                        "anthropic_claude": Decimal('625.00'),
                        "local_models": Decimal('400.00')
                    }
                },
                CostCategory.STORAGE: {
                    "total": Decimal('680.00'),
                    "breakdown": {
                        "document_storage": Decimal('450.00'),
                        "database_storage": Decimal('180.00'),
                        "backup_storage": Decimal('50.00')
                    }
                }
            }

            data = cost_data.get(category, cost_data[CostCategory.INFRASTRUCTURE])
            total_cost = data["total"]

            # Calculate per-user and per-request costs
            estimated_users = 150
            estimated_requests = 50000
            cost_per_user = total_cost / estimated_users
            cost_per_request = total_cost / estimated_requests

            # Calculate trends (simulated)
            cost_trend = 12.5  # 12.5% increase from last period
            budget = total_cost * Decimal('1.1')  # 10% over budget
            budget_variance = total_cost - budget

            # Generate optimization opportunities
            optimizations = [
                "Implement auto-scaling to reduce idle compute costs",
                "Optimize database queries to reduce processing time",
                "Use reserved instances for predictable workloads",
                "Implement intelligent caching to reduce API calls",
                "Archive old documents to cheaper storage tiers"
            ]

            # Project monthly costs
            daily_cost = total_cost / days_back
            projected_monthly = daily_cost * 30

            # ROI metrics
            roi_metrics = {
                "cost_savings_vs_manual": float(total_cost * Decimal('0.3')),
                "efficiency_improvement": 45.2,
                "time_saved_value": float(total_cost * Decimal('2.1')),
                "automation_roi": 312.5
            }

            return CostAnalytics(
                category=category,
                period_start=period_start,
                period_end=period_end,
                total_cost=total_cost,
                cost_per_user=cost_per_user,
                cost_per_request=cost_per_request,
                cost_breakdown=data["breakdown"],
                cost_trend=cost_trend,
                budget_variance=budget_variance,
                optimization_opportunities=optimizations,
                projected_monthly_cost=projected_monthly,
                roi_metrics=roi_metrics
            )

        except Exception as e:
            print(f"Error analyzing costs: {e}")
            return None

    async def collect_security_metrics(self) -> Optional[SecurityMetrics]:
        """Collect security and compliance metrics"""
        try:
            current_time = datetime.utcnow()

            # Simulated security metrics (in production, these would come from security tools)
            return SecurityMetrics(
                timestamp=current_time,
                failed_auth_attempts=23,
                blocked_ip_addresses=8,
                malicious_requests=15,
                vulnerability_scans=4,
                security_incidents=1,
                compliance_score=96.5,
                data_encryption_coverage=100.0,
                access_control_violations=2,
                audit_log_completeness=99.8,
                threat_detection_alerts=7
            )

        except Exception as e:
            print(f"Error collecting security metrics: {e}")
            return None

    async def analyze_scalability(self) -> Optional[ScalabilityAnalysis]:
        """Analyze system scalability and capacity"""
        try:
            # Current system capacity
            current_capacity = {
                "api_requests_per_second": 500,
                "concurrent_users": 1000,
                "document_processing_per_hour": 1200,
                "storage_gb": 2048,
                "database_connections": 200
            }

            # Peak loads handled successfully
            peak_load = {
                "api_requests_per_second": 750,
                "concurrent_users": 1500,
                "document_processing_per_hour": 1800,
                "storage_gb": 1850,
                "database_connections": 180
            }

            # Identify bottlenecks
            bottlenecks = []
            for resource, current in current_capacity.items():
                peak = peak_load.get(resource, current)
                utilization = peak / current
                if utilization > 0.8:
                    bottlenecks.append(resource)

            # Scaling recommendations
            recommendations = [
                "Add more API server instances during peak hours",
                "Implement database read replicas for query scaling",
                "Use CDN for static content delivery",
                "Optimize document processing pipeline for throughput",
                "Implement queue-based processing for heavy operations"
            ]

            # Performance under load metrics
            performance_under_load = {
                "response_time_degradation": 15.2,  # % increase under peak load
                "error_rate_increase": 0.5,         # % increase in errors
                "throughput_efficiency": 87.5,      # % of theoretical max
                "resource_utilization": 78.3        # % of resources used
            }

            return ScalabilityAnalysis(
                current_capacity=current_capacity,
                peak_load_handled=peak_load,
                bottleneck_resources=bottlenecks,
                scaling_recommendations=recommendations,
                auto_scaling_events=12,
                load_balancer_efficiency=94.2,
                horizontal_scaling_potential=85.0,
                vertical_scaling_cost=Decimal('450.00'),
                predicted_scaling_needs={
                    "next_quarter": "25% increase in capacity needed",
                    "next_year": "200% scaling recommended",
                    "critical_resources": ["database", "ai_processing"]
                },
                performance_under_load=performance_under_load
            )

        except Exception as e:
            print(f"Error analyzing scalability: {e}")
            return None

    async def check_system_alerts(self) -> List[SystemAlert]:
        """Check for system alerts and anomalies"""
        try:
            alerts = []

            # Sample alerts (in production, these would come from monitoring systems)
            sample_alerts = [
                {
                    "id": "ALT-001",
                    "service": ServiceType.DATABASE,
                    "level": AlertLevel.WARNING,
                    "message": "Database connection pool utilization high",
                    "metric": "connection_pool_usage",
                    "current": 85.5,
                    "threshold": 80.0,
                    "duration": 15
                },
                {
                    "id": "ALT-002",
                    "service": ServiceType.API_SERVER,
                    "level": AlertLevel.INFO,
                    "message": "Response time slightly elevated",
                    "metric": "avg_response_time",
                    "current": 120.0,
                    "threshold": 100.0,
                    "duration": 8
                }
            ]

            for alert_data in sample_alerts:
                alert = SystemAlert(
                    alert_id=alert_data["id"],
                    service=alert_data["service"],
                    level=alert_data["level"],
                    message=alert_data["message"],
                    metric_name=alert_data["metric"],
                    current_value=alert_data["current"],
                    threshold_value=alert_data["threshold"],
                    duration_minutes=alert_data["duration"],
                    impact_assessment="Moderate performance impact",
                    recommended_action="Monitor closely and scale if needed",
                    auto_resolved=False,
                    acknowledged=False
                )
                alerts.append(alert)

            return alerts

        except Exception as e:
            print(f"Error checking system alerts: {e}")
            return []

    async def calculate_health_score(self) -> float:
        """Calculate overall system health score"""
        try:
            # Collect metrics for health calculation
            api_metrics = await self.collect_performance_metrics(ServiceType.API_SERVER)
            db_metrics = await self.collect_performance_metrics(ServiceType.DATABASE)
            security_metrics = await self.collect_security_metrics()
            alerts = await self.check_system_alerts()

            # Calculate component scores
            performance_score = 100.0
            if api_metrics:
                if api_metrics.error_rate > 0.05:
                    performance_score -= 20
                if api_metrics.response_time_ms > 200:
                    performance_score -= 15
                if api_metrics.availability_percentage < 99.5:
                    performance_score -= 25

            security_score = security_metrics.compliance_score if security_metrics else 95.0

            # Alert penalty
            alert_penalty = len([a for a in alerts if a.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]]) * 10

            # Calculate weighted average
            overall_score = (
                performance_score * 0.4 +
                security_score * 0.3 +
                (100 - alert_penalty) * 0.3
            )

            return max(0.0, min(100.0, overall_score))

        except Exception as e:
            print(f"Error calculating health score: {e}")
            return 85.0  # Default score

    async def generate_system_report(self, include_detailed_metrics: bool = True) -> Optional[SystemHealthReport]:
        """Generate comprehensive system health report"""
        try:
            current_time = datetime.utcnow()

            # Collect all system metrics
            health_score = await self.calculate_health_score()

            performance_metrics = []
            for service in [ServiceType.API_SERVER, ServiceType.DATABASE, ServiceType.AI_PROCESSING]:
                metrics = await self.collect_performance_metrics(service)
                if metrics:
                    performance_metrics.append(metrics)

            resource_utilization = []
            for resource in [ResourceType.CPU, ResourceType.MEMORY, ResourceType.DISK]:
                utilization = await self.monitor_resource_utilization(resource)
                if utilization:
                    resource_utilization.append(utilization)

            cost_analytics = []
            for category in [CostCategory.INFRASTRUCTURE, CostCategory.AI_MODELS, CostCategory.STORAGE]:
                cost_analysis = await self.analyze_costs(category)
                if cost_analysis:
                    cost_analytics.append(cost_analysis)

            security_metrics = await self.collect_security_metrics()
            scalability_analysis = await self.analyze_scalability()
            active_alerts = await self.check_system_alerts()

            # Calculate service health scores
            service_health = {}
            for service in ServiceType:
                # Simplified health calculation per service
                base_score = 90.0
                service_alerts = [a for a in active_alerts if a.service == service]
                alert_penalty = len(service_alerts) * 5
                service_health[service.value] = max(0.0, base_score - alert_penalty)

            # Generate insights
            insights = [
                f"System operating at {health_score:.1f}% overall health",
                f"API response time averaging {performance_metrics[0].response_time_ms:.1f}ms" if performance_metrics else "API metrics unavailable",
                f"Database query performance at {performance_metrics[1].database_query_time_ms:.1f}ms" if len(performance_metrics) > 1 else "Database metrics unavailable",
                f"Security compliance score at {security_metrics.compliance_score:.1f}%" if security_metrics else "Security metrics unavailable",
                f"Total infrastructure cost: ${sum(c.total_cost for c in cost_analytics):,.2f}" if cost_analytics else "Cost data unavailable"
            ]

            # Generate recommendations
            recommendations = [
                "Monitor database connection pool utilization closely",
                "Implement automated scaling for peak traffic periods",
                "Review and optimize high-cost AI model usage",
                "Enhance security monitoring for threat detection",
                "Plan capacity upgrades for projected growth"
            ]

            # Trend analysis
            trend_analysis = {
                "performance_trend": "stable",
                "cost_trend": "increasing",
                "security_trend": "improving",
                "capacity_trend": "approaching_limits",
                "user_growth_impact": "moderate"
            }

            return SystemHealthReport(
                report_timestamp=current_time,
                overall_health_score=health_score,
                service_health=service_health,
                performance_metrics=performance_metrics if include_detailed_metrics else [],
                resource_utilization=resource_utilization if include_detailed_metrics else [],
                cost_analytics=cost_analytics,
                security_metrics=security_metrics,
                scalability_analysis=scalability_analysis,
                active_alerts=active_alerts,
                recommendations=recommendations,
                key_insights=insights,
                trend_analysis=trend_analysis
            )

        except Exception as e:
            print(f"Error generating system report: {e}")
            return None

    async def get_system_analytics_summary(self) -> Dict[str, Any]:
        """Get high-level system analytics summary"""
        try:
            health_score = await self.calculate_health_score()
            alerts = await self.check_system_alerts()
            cost_analysis = await self.analyze_costs(CostCategory.INFRASTRUCTURE)

            summary = {
                "health": {
                    "overall_score": health_score,
                    "status": "healthy" if health_score > 90 else "warning" if health_score > 70 else "critical",
                    "active_alerts": len(alerts),
                    "critical_alerts": len([a for a in alerts if a.level == AlertLevel.CRITICAL])
                },
                "performance": {
                    "avg_response_time": 85.4,
                    "availability": 99.85,
                    "error_rate": 0.02,
                    "throughput": 142.7
                },
                "resources": {
                    "cpu_utilization": psutil.cpu_percent(),
                    "memory_utilization": psutil.virtual_memory().percent,
                    "disk_utilization": psutil.disk_usage('/').percent
                },
                "costs": {
                    "monthly_infrastructure": float(cost_analysis.total_cost) if cost_analysis else 0,
                    "cost_per_user": float(cost_analysis.cost_per_user) if cost_analysis else 0,
                    "trend": cost_analysis.cost_trend if cost_analysis else 0
                }
            }

            return summary

        except Exception as e:
            print(f"Error generating system summary: {e}")
            return {}

    async def export_system_metrics(self, format_type: str = "json",
                                  include_historical: bool = False,
                                  days_back: int = 7) -> Optional[str]:
        """Export system analytics data"""
        try:
            # Generate comprehensive data export
            health_report = await self.generate_system_report(include_detailed_metrics=True)

            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "system_health": {
                    "overall_score": health_report.overall_health_score if health_report else 0,
                    "service_health": health_report.service_health if health_report else {},
                    "active_alerts": len(health_report.active_alerts) if health_report else 0
                },
                "performance_summary": {
                    "avg_response_time": 85.4,
                    "throughput": 142.7,
                    "error_rate": 0.02,
                    "availability": 99.85
                },
                "resource_utilization": {
                    "cpu": psutil.cpu_percent(),
                    "memory": psutil.virtual_memory().percent,
                    "disk": psutil.disk_usage('/').percent
                },
                "cost_summary": {
                    "total_monthly": 4500.00,
                    "infrastructure": 2450.00,
                    "ai_models": 1875.00,
                    "storage": 680.00
                }
            }

            if include_historical:
                export_data["historical_metrics"] = {
                    "period_days": days_back,
                    "trend_data": "Historical data would be included here"
                }

            if format_type.lower() == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif format_type.lower() == "csv":
                # Simple CSV format for key metrics
                csv_lines = [
                    "metric,value,timestamp",
                    f"health_score,{export_data['system_health']['overall_score']},{datetime.utcnow().isoformat()}",
                    f"response_time,{export_data['performance_summary']['avg_response_time']},{datetime.utcnow().isoformat()}",
                    f"cpu_usage,{export_data['resource_utilization']['cpu']},{datetime.utcnow().isoformat()}",
                    f"memory_usage,{export_data['resource_utilization']['memory']},{datetime.utcnow().isoformat()}"
                ]
                return "\n".join(csv_lines)

            return json.dumps(export_data, indent=2, default=str)

        except Exception as e:
            print(f"Error exporting system metrics: {e}")
            return None


# Global instance
system_analytics_monitor = SystemAnalyticsMonitor()


# FastAPI endpoints configuration
async def get_system_analytics_endpoints():
    """Return FastAPI endpoint configurations for system analytics"""
    return [
        {
            "path": "/analytics/system/health",
            "method": "GET",
            "handler": "get_system_health_score",
            "description": "Get overall system health score"
        },
        {
            "path": "/analytics/system/performance/{service}",
            "method": "GET",
            "handler": "get_performance_metrics",
            "description": "Get performance metrics for specific service"
        },
        {
            "path": "/analytics/system/resources/{resource_type}",
            "method": "GET",
            "handler": "get_resource_utilization",
            "description": "Get resource utilization metrics"
        },
        {
            "path": "/analytics/system/costs/{category}",
            "method": "GET",
            "handler": "get_cost_analysis",
            "description": "Get cost analysis for specific category"
        },
        {
            "path": "/analytics/system/security",
            "method": "GET",
            "handler": "get_security_metrics",
            "description": "Get security and compliance metrics"
        },
        {
            "path": "/analytics/system/scalability",
            "method": "GET",
            "handler": "get_scalability_analysis",
            "description": "Get system scalability analysis"
        },
        {
            "path": "/analytics/system/alerts",
            "method": "GET",
            "handler": "get_system_alerts",
            "description": "Get active system alerts"
        },
        {
            "path": "/analytics/system/report",
            "method": "GET",
            "handler": "generate_system_health_report",
            "description": "Generate comprehensive system health report"
        },
        {
            "path": "/analytics/system/summary",
            "method": "GET",
            "handler": "get_system_analytics_summary",
            "description": "Get high-level system analytics summary"
        },
        {
            "path": "/analytics/system/export",
            "method": "POST",
            "handler": "export_system_analytics",
            "description": "Export system analytics data"
        }
    ]


async def initialize_system_analytics():
    """Initialize the system analytics monitoring"""
    print("System Analytics Monitor initialized successfully")
    print(f"Available endpoints: {len(await get_system_analytics_endpoints())}")
    return True