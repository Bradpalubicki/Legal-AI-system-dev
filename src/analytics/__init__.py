"""
Analytics System
Comprehensive analytics platform with user metrics, business analytics, system monitoring, and custom reporting.
"""

from .user_metrics import (
    UserMetricsAnalyzer,
    EngagementMetrics,
    SuccessMetrics,
    UserBehaviorPattern,
    UserSegmentAnalysis,
    UserAnalyticsReport,
    MetricType,
    TimeRange,
    UserSegment,
    FeatureType,
    user_metrics_analyzer,
    get_user_analytics_endpoints,
    initialize_user_analytics_system
)

from .business import (
    BusinessAnalyticsEngine,
    RevenueMetrics,
    GrowthAnalytics,
    CustomerSegmentAnalysis,
    ProfitabilityAnalysis,
    MarketAnalysis,
    SalesMetrics,
    BusinessAnalyticsReport,
    RevenueType,
    GrowthMetric,
    BusinessSegment,
    PricingTier,
    PlanType,
    business_analytics_engine,
    get_business_analytics_endpoints,
    initialize_business_analytics_system
)

from .system import (
    SystemAnalyticsMonitor,
    PerformanceMetrics,
    ResourceUtilization,
    CostAnalytics,
    SecurityMetrics,
    ScalabilityAnalysis,
    SystemAlert,
    SystemHealthReport,
    SystemMetricType,
    ServiceType,
    AlertLevel,
    ResourceType,
    CostCategory,
    system_analytics_monitor,
    get_system_analytics_endpoints,
    initialize_system_analytics
)

from .reports import (
    CustomReportsEngine,
    ReportTemplate,
    ReportSection,
    ReportColumn,
    ChartConfig,
    ReportSchedule,
    GeneratedReport,
    ReportDashboard,
    ReportFilter,
    ReportType,
    ReportFormat,
    ScheduleFrequency,
    ReportStatus,
    DataSource,
    AggregationType,
    custom_reports_engine,
    get_reports_endpoints,
    initialize_reports_system
)

__all__ = [
    # User Analytics
    "UserMetricsAnalyzer",
    "EngagementMetrics",
    "SuccessMetrics",
    "UserBehaviorPattern",
    "UserSegmentAnalysis",
    "UserAnalyticsReport",
    "MetricType",
    "TimeRange",
    "UserSegment",
    "FeatureType",
    "user_metrics_analyzer",
    "get_user_analytics_endpoints",
    "initialize_user_analytics_system",

    # Business Analytics
    "BusinessAnalyticsEngine",
    "RevenueMetrics",
    "GrowthAnalytics",
    "CustomerSegmentAnalysis",
    "ProfitabilityAnalysis",
    "MarketAnalysis",
    "SalesMetrics",
    "BusinessAnalyticsReport",
    "RevenueType",
    "GrowthMetric",
    "BusinessSegment",
    "PricingTier",
    "PlanType",
    "business_analytics_engine",
    "get_business_analytics_endpoints",
    "initialize_business_analytics_system",

    # System Analytics
    "SystemAnalyticsMonitor",
    "PerformanceMetrics",
    "ResourceUtilization",
    "CostAnalytics",
    "SecurityMetrics",
    "ScalabilityAnalysis",
    "SystemAlert",
    "SystemHealthReport",
    "SystemMetricType",
    "ServiceType",
    "AlertLevel",
    "ResourceType",
    "CostCategory",
    "system_analytics_monitor",
    "get_system_analytics_endpoints",
    "initialize_system_analytics",

    # Custom Reports
    "CustomReportsEngine",
    "ReportTemplate",
    "ReportSection",
    "ReportColumn",
    "ChartConfig",
    "ReportSchedule",
    "GeneratedReport",
    "ReportDashboard",
    "ReportFilter",
    "ReportType",
    "ReportFormat",
    "ScheduleFrequency",
    "ReportStatus",
    "DataSource",
    "AggregationType",
    "custom_reports_engine",
    "get_reports_endpoints",
    "initialize_reports_system",

    # Unified functions
    "get_analytics_endpoints",
    "initialize_analytics_system"
]


async def get_analytics_endpoints():
    """Get all analytics endpoints from all modules"""
    endpoints = []

    # Collect endpoints from all modules
    user_endpoints = await get_user_analytics_endpoints()
    business_endpoints = await get_business_analytics_endpoints()
    system_endpoints = await get_system_analytics_endpoints()
    reports_endpoints = await get_reports_endpoints()

    endpoints.extend(user_endpoints)
    endpoints.extend(business_endpoints)
    endpoints.extend(system_endpoints)
    endpoints.extend(reports_endpoints)

    return endpoints


async def initialize_analytics_system():
    """Initialize the complete analytics system"""
    print("Initializing Analytics System...")

    results = []

    # Initialize all subsystems
    user_init = await initialize_user_analytics_system()
    results.append(("User Analytics", user_init))

    business_init = await initialize_business_analytics_system()
    results.append(("Business Analytics", business_init))

    system_init = await initialize_system_analytics()
    results.append(("System Analytics", system_init))

    reports_init = await initialize_reports_system()
    results.append(("Custom Reports", reports_init))

    # Check results
    failed_systems = [name for name, success in results if not success]
    successful_systems = [name for name, success in results if success]

    if failed_systems:
        print(f"WARNING: Failed to initialize: {', '.join(failed_systems)}")

    if successful_systems:
        print(f"SUCCESS: Successfully initialized: {', '.join(successful_systems)}")

    # Get total endpoint count
    all_endpoints = await get_analytics_endpoints()
    total_endpoints = len(all_endpoints)

    print(f"Analytics System initialized with {total_endpoints} endpoints")
    print("=" * 50)
    print("ANALYTICS SYSTEM READY")
    print("=" * 50)

    return len(failed_systems) == 0