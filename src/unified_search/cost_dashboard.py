"""
Comprehensive cost reporting and dashboard system for legal research platforms.
Provides real-time dashboards, detailed reports, and interactive cost analytics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from decimal import Decimal
import statistics
from collections import defaultdict

from ..types.unified_types import UnifiedDocument, ContentType
from .cost_tracker import CostTracker, CostSummary, ResourceType, CostCategory
from .usage_monitor import UsageMonitor, UsageAnalytics, UserProfile
from .cost_analyzer import CostAnalyzer, CostAnalysisReport
from .budget_manager import BudgetManager, BudgetReport, BudgetAllocation


class DashboardView(Enum):
    """Types of dashboard views."""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYTICS = "detailed_analytics"
    USER_PERFORMANCE = "user_performance"
    RESOURCE_UTILIZATION = "resource_utilization"
    BUDGET_MONITORING = "budget_monitoring"
    COST_OPTIMIZATION = "cost_optimization"
    TREND_ANALYSIS = "trend_analysis"
    REAL_TIME = "real_time"


class ReportType(Enum):
    """Types of generated reports."""
    MONTHLY_SUMMARY = "monthly_summary"
    QUARTERLY_REVIEW = "quarterly_review"
    ANNUAL_REPORT = "annual_report"
    USER_EFFICIENCY = "user_efficiency"
    RESOURCE_ANALYSIS = "resource_analysis"
    BUDGET_PERFORMANCE = "budget_performance"
    COST_OPTIMIZATION_PLAN = "cost_optimization_plan"
    CUSTOM_ANALYSIS = "custom_analysis"


class ChartType(Enum):
    """Types of charts for visualization."""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    STACKED_BAR = "stacked_bar"
    AREA_CHART = "area_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TABLE = "table"


@dataclass
class ChartData:
    """Data structure for charts."""
    chart_id: str
    chart_type: ChartType
    title: str
    
    # Data
    labels: List[str]
    datasets: List[Dict[str, Any]]
    
    # Configuration
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    show_legend: bool = True
    
    # Metadata
    data_source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Interactive features
    clickable: bool = False
    drill_down_available: bool = False


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    widget_id: str
    title: str
    widget_type: str  # "chart", "metric", "table", "alert"
    
    # Content
    chart_data: Optional[ChartData] = None
    metric_value: Optional[str] = None
    metric_trend: Optional[str] = None  # "up", "down", "stable"
    table_data: Optional[List[Dict[str, Any]]] = None
    alert_data: Optional[List[Dict[str, Any]]] = None
    
    # Layout
    position: Tuple[int, int] = (0, 0)  # (row, column)
    size: Tuple[int, int] = (1, 1)      # (height, width)
    
    # Configuration
    refresh_interval: int = 300  # seconds
    auto_refresh: bool = True
    
    # Status
    last_updated: datetime = field(default_factory=datetime.now)
    loading: bool = False
    error_message: Optional[str] = None


@dataclass
class DashboardLayout:
    """Complete dashboard layout."""
    dashboard_id: str
    name: str
    view_type: DashboardView
    
    # Widgets
    widgets: List[DashboardWidget] = field(default_factory=list)
    
    # Configuration
    refresh_interval: int = 300
    auto_refresh: bool = True
    
    # Access control
    user_permissions: Dict[str, List[str]] = field(default_factory=dict)
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None


@dataclass
class GeneratedReport:
    """Generated report structure."""
    report_id: str
    report_type: ReportType
    title: str
    
    # Content
    executive_summary: str
    detailed_sections: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[ChartData] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    period_start: datetime
    period_end: datetime
    generated_date: datetime = field(default_factory=datetime.now)
    generated_by: Optional[str] = None
    
    # Export options
    export_formats: List[str] = field(default_factory=lambda: ["pdf", "excel", "csv"])


class CostDashboard:
    """
    Comprehensive cost reporting and dashboard system.
    
    Provides real-time dashboards, detailed analytics, automated reporting,
    and interactive cost management interfaces for legal research platforms.
    """
    
    def __init__(self, 
                 cost_tracker: CostTracker,
                 usage_monitor: UsageMonitor,
                 cost_analyzer: CostAnalyzer,
                 budget_manager: BudgetManager):
        self.cost_tracker = cost_tracker
        self.usage_monitor = usage_monitor
        self.cost_analyzer = cost_analyzer
        self.budget_manager = budget_manager
        self.logger = logging.getLogger(__name__)
        
        # Dashboard storage
        self.dashboards: Dict[str, DashboardLayout] = {}
        self.generated_reports: Dict[str, GeneratedReport] = {}
        
        # Real-time data cache
        self.realtime_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=5)
        
        # Initialize default dashboards
        asyncio.create_task(self._initialize_default_dashboards())
    
    async def _initialize_default_dashboards(self):
        """Initialize default dashboard layouts."""
        
        # Executive Summary Dashboard
        exec_dashboard = await self.create_dashboard(
            "executive_summary",
            "Executive Summary",
            DashboardView.EXECUTIVE_SUMMARY
        )
        
        await self.add_widget_to_dashboard(
            exec_dashboard.dashboard_id,
            "total_costs_metric",
            "Total Research Costs",
            "metric",
            position=(0, 0),
            size=(1, 2)
        )
        
        await self.add_widget_to_dashboard(
            exec_dashboard.dashboard_id,
            "monthly_trend_chart",
            "Monthly Cost Trend",
            "chart",
            position=(0, 2),
            size=(1, 4)
        )
        
        await self.add_widget_to_dashboard(
            exec_dashboard.dashboard_id,
            "budget_alerts",
            "Budget Alerts",
            "alert",
            position=(1, 0),
            size=(1, 3)
        )
        
        await self.add_widget_to_dashboard(
            exec_dashboard.dashboard_id,
            "resource_breakdown",
            "Cost by Resource",
            "chart",
            position=(1, 3),
            size=(1, 3)
        )
        
        # Detailed Analytics Dashboard
        analytics_dashboard = await self.create_dashboard(
            "detailed_analytics",
            "Detailed Analytics",
            DashboardView.DETAILED_ANALYTICS
        )
        
        await self.add_widget_to_dashboard(
            analytics_dashboard.dashboard_id,
            "efficiency_metrics",
            "Efficiency Metrics",
            "table",
            position=(0, 0),
            size=(2, 3)
        )
        
        await self.add_widget_to_dashboard(
            analytics_dashboard.dashboard_id,
            "user_performance_chart",
            "User Performance Analysis",
            "chart",
            position=(0, 3),
            size=(2, 3)
        )
        
        # Budget Monitoring Dashboard
        budget_dashboard = await self.create_dashboard(
            "budget_monitoring",
            "Budget Monitoring",
            DashboardView.BUDGET_MONITORING
        )
        
        self.logger.info("Initialized default dashboards")
    
    async def create_dashboard(self, 
                             dashboard_id: str,
                             name: str,
                             view_type: DashboardView,
                             created_by: Optional[str] = None) -> DashboardLayout:
        """Create a new dashboard layout."""
        
        dashboard = DashboardLayout(
            dashboard_id=dashboard_id,
            name=name,
            view_type=view_type,
            created_by=created_by
        )
        
        self.dashboards[dashboard_id] = dashboard
        
        self.logger.info(f"Created dashboard: {name}")
        
        return dashboard
    
    async def add_widget_to_dashboard(self,
                                    dashboard_id: str,
                                    widget_id: str,
                                    title: str,
                                    widget_type: str,
                                    position: Tuple[int, int] = (0, 0),
                                    size: Tuple[int, int] = (1, 1),
                                    **kwargs) -> bool:
        """Add a widget to a dashboard."""
        
        if dashboard_id not in self.dashboards:
            return False
        
        widget = DashboardWidget(
            widget_id=widget_id,
            title=title,
            widget_type=widget_type,
            position=position,
            size=size,
            refresh_interval=kwargs.get('refresh_interval', 300),
            auto_refresh=kwargs.get('auto_refresh', True)
        )
        
        self.dashboards[dashboard_id].widgets.append(widget)
        self.dashboards[dashboard_id].last_modified = datetime.now()
        
        return True
    
    async def get_dashboard_data(self, 
                               dashboard_id: str,
                               force_refresh: bool = False) -> Optional[DashboardLayout]:
        """Get dashboard data with populated widgets."""
        
        if dashboard_id not in self.dashboards:
            return None
        
        dashboard = self.dashboards[dashboard_id]
        
        # Update widget data
        for widget in dashboard.widgets:
            if force_refresh or self._should_refresh_widget(widget):
                await self._populate_widget_data(widget, dashboard.view_type)
        
        return dashboard
    
    def _should_refresh_widget(self, widget: DashboardWidget) -> bool:
        """Check if widget data should be refreshed."""
        
        if not widget.auto_refresh:
            return False
        
        time_since_update = (datetime.now() - widget.last_updated).total_seconds()
        return time_since_update >= widget.refresh_interval
    
    async def _populate_widget_data(self, widget: DashboardWidget, view_type: DashboardView):
        """Populate widget with current data."""
        
        widget.loading = True
        widget.error_message = None
        
        try:
            if widget.widget_type == "metric":
                await self._populate_metric_widget(widget, view_type)
            elif widget.widget_type == "chart":
                await self._populate_chart_widget(widget, view_type)
            elif widget.widget_type == "table":
                await self._populate_table_widget(widget, view_type)
            elif widget.widget_type == "alert":
                await self._populate_alert_widget(widget, view_type)
            
            widget.last_updated = datetime.now()
            
        except Exception as e:
            widget.error_message = str(e)
            self.logger.error(f"Error populating widget {widget.widget_id}: {e}")
        
        finally:
            widget.loading = False
    
    async def _populate_metric_widget(self, widget: DashboardWidget, view_type: DashboardView):
        """Populate metric widget with data."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
        
        if widget.widget_id == "total_costs_metric":
            cost_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
            widget.metric_value = f"${cost_summary.total_cost:,.2f}"
            widget.metric_trend = cost_summary.cost_trend
        
        elif widget.widget_id == "efficiency_metric":
            analytics = await self.usage_monitor.generate_system_analytics(start_date, end_date)
            widget.metric_value = f"{analytics.average_relevance_rate:.1%}"
            widget.metric_trend = "up" if analytics.average_relevance_rate > 0.6 else "down"
        
        elif widget.widget_id == "budget_utilization_metric":
            budget_report = await self.budget_manager.generate_budget_report(start_date, end_date)
            widget.metric_value = f"{budget_report.overall_utilization:.1%}"
            widget.metric_trend = "up" if budget_report.overall_utilization > 0.8 else "stable"
    
    async def _populate_chart_widget(self, widget: DashboardWidget, view_type: DashboardView):
        """Populate chart widget with data."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        if widget.widget_id == "monthly_trend_chart":
            chart_data = await self._generate_monthly_trend_chart(start_date, end_date)
            widget.chart_data = chart_data
        
        elif widget.widget_id == "resource_breakdown":
            chart_data = await self._generate_resource_breakdown_chart(start_date, end_date)
            widget.chart_data = chart_data
        
        elif widget.widget_id == "user_performance_chart":
            chart_data = await self._generate_user_performance_chart(start_date, end_date)
            widget.chart_data = chart_data
        
        elif widget.widget_id == "budget_status_chart":
            chart_data = await self._generate_budget_status_chart()
            widget.chart_data = chart_data
    
    async def _populate_table_widget(self, widget: DashboardWidget, view_type: DashboardView):
        """Populate table widget with data."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        if widget.widget_id == "efficiency_metrics":
            table_data = await self._generate_efficiency_metrics_table(start_date, end_date)
            widget.table_data = table_data
        
        elif widget.widget_id == "top_users_table":
            table_data = await self._generate_top_users_table(start_date, end_date)
            widget.table_data = table_data
        
        elif widget.widget_id == "resource_performance_table":
            table_data = await self._generate_resource_performance_table(start_date, end_date)
            widget.table_data = table_data
    
    async def _populate_alert_widget(self, widget: DashboardWidget, view_type: DashboardView):
        """Populate alert widget with data."""
        
        if widget.widget_id == "budget_alerts":
            alerts = await self.budget_manager.get_pending_alerts()
            
            alert_data = []
            for alert in alerts[:10]:  # Limit to 10 most recent
                alert_data.append({
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message[:100] + "..." if len(alert.message) > 100 else alert.message,
                    'date': alert.alert_date.strftime('%Y-%m-%d %H:%M'),
                    'acknowledged': alert.acknowledged
                })
            
            widget.alert_data = alert_data
        
        elif widget.widget_id == "cost_optimization_alerts":
            # Generate cost optimization alerts
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            analysis_report = await self.cost_analyzer.analyze_costs(start_date, end_date)
            
            alert_data = []
            for recommendation in analysis_report.top_optimization_opportunities[:5]:
                alert_data.append({
                    'severity': recommendation.priority,
                    'title': recommendation.title,
                    'message': recommendation.description,
                    'savings': f"${recommendation.estimated_monthly_savings:,.2f}",
                    'acknowledged': False
                })
            
            widget.alert_data = alert_data
    
    async def _generate_monthly_trend_chart(self, start_date: datetime, end_date: datetime) -> ChartData:
        """Generate monthly cost trend chart."""
        
        # Get daily costs
        cost_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
        daily_costs = cost_summary.daily_costs
        
        # Sort by date
        sorted_dates = sorted(daily_costs.keys())
        labels = [date for date in sorted_dates]
        values = [float(daily_costs[date]) for date in sorted_dates]
        
        chart_data = ChartData(
            chart_id="monthly_trend",
            chart_type=ChartType.LINE_CHART,
            title="Daily Cost Trend",
            labels=labels,
            datasets=[{
                'label': 'Daily Costs',
                'data': values,
                'borderColor': '#2E86AB',
                'backgroundColor': '#2E86AB20',
                'fill': True
            }],
            x_axis_label="Date",
            y_axis_label="Cost ($)",
            data_source="Cost Tracker"
        )
        
        return chart_data
    
    async def _generate_resource_breakdown_chart(self, start_date: datetime, end_date: datetime) -> ChartData:
        """Generate resource cost breakdown pie chart."""
        
        cost_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
        resource_costs = cost_summary.costs_by_resource
        
        labels = [resource.value for resource in resource_costs.keys()]
        values = [float(cost) for cost in resource_costs.values()]
        
        # Color scheme for resources
        colors = [
            '#2E86AB', '#A23B72', '#F18F01', '#C73E1D', 
            '#6A994E', '#BC4749', '#8E9AAF', '#7B68EE'
        ]
        
        chart_data = ChartData(
            chart_id="resource_breakdown",
            chart_type=ChartType.PIE_CHART,
            title="Cost by Resource",
            labels=labels,
            datasets=[{
                'label': 'Resource Costs',
                'data': values,
                'backgroundColor': colors[:len(labels)],
                'borderWidth': 2
            }],
            data_source="Cost Tracker"
        )
        
        return chart_data
    
    async def _generate_user_performance_chart(self, start_date: datetime, end_date: datetime) -> ChartData:
        """Generate user performance analysis chart."""
        
        # Get top 10 users by cost
        cost_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
        user_costs = cost_summary.costs_by_user
        
        # Sort users by cost and take top 10
        sorted_users = sorted(user_costs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get efficiency data for these users
        efficiency_data = []
        cost_data = []
        labels = []
        
        for user_id, cost in sorted_users:
            user_profile = await self.usage_monitor.analyze_user_patterns(user_id)
            efficiency_data.append(user_profile.overall_relevance_rate * 100)  # Convert to percentage
            cost_data.append(float(cost))
            labels.append(user_id[:10])  # Truncate user ID
        
        chart_data = ChartData(
            chart_id="user_performance",
            chart_type=ChartType.SCATTER_PLOT,
            title="User Cost vs Efficiency",
            labels=labels,
            datasets=[{
                'label': 'Users',
                'data': [{'x': cost, 'y': eff} for cost, eff in zip(cost_data, efficiency_data)],
                'backgroundColor': '#2E86AB',
                'borderColor': '#2E86AB',
                'pointRadius': 8
            }],
            x_axis_label="Total Cost ($)",
            y_axis_label="Efficiency (%)",
            data_source="Usage Monitor"
        )
        
        return chart_data
    
    async def _generate_budget_status_chart(self) -> ChartData:
        """Generate budget status overview chart."""
        
        budget_report = await self.budget_manager.generate_budget_report()
        
        # Count budgets by status
        status_counts = {
            'On Track': budget_report.budgets_on_track,
            'At Risk': budget_report.budgets_at_risk,
            'Over Budget': budget_report.budgets_over
        }
        
        labels = list(status_counts.keys())
        values = list(status_counts.values())
        colors = ['#6A994E', '#F18F01', '#C73E1D']  # Green, Orange, Red
        
        chart_data = ChartData(
            chart_id="budget_status",
            chart_type=ChartType.BAR_CHART,
            title="Budget Status Overview",
            labels=labels,
            datasets=[{
                'label': 'Number of Budgets',
                'data': values,
                'backgroundColor': colors,
                'borderWidth': 2
            }],
            y_axis_label="Number of Budgets",
            data_source="Budget Manager"
        )
        
        return chart_data
    
    async def _generate_efficiency_metrics_table(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate efficiency metrics table."""
        
        analysis_report = await self.cost_analyzer.analyze_costs(start_date, end_date)
        metrics = analysis_report.efficiency_metrics
        
        table_data = [
            {
                'metric': 'Cost per Search',
                'value': f"${metrics.cost_per_search:.2f}",
                'benchmark': '$10.00',
                'status': 'Good' if metrics.cost_per_search <= 10 else 'Needs Improvement'
            },
            {
                'metric': 'Cost per Document',
                'value': f"${metrics.cost_per_document:.2f}",
                'benchmark': '$15.00',
                'status': 'Good' if metrics.cost_per_document <= 15 else 'Needs Improvement'
            },
            {
                'metric': 'Cost per User',
                'value': f"${metrics.cost_per_user:.2f}",
                'benchmark': '$800.00',
                'status': 'Good' if metrics.cost_per_user <= 800 else 'Needs Improvement'
            },
            {
                'metric': 'System Efficiency',
                'value': f"{metrics.efficiency_trend}",
                'benchmark': 'Improving',
                'status': 'Good' if metrics.efficiency_trend in ['improving', 'stable'] else 'Needs Attention'
            }
        ]
        
        return table_data
    
    async def _generate_top_users_table(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate top users by cost table."""
        
        cost_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
        user_costs = cost_summary.costs_by_user
        
        # Sort users by cost and take top 10
        sorted_users = sorted(user_costs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        table_data = []
        for rank, (user_id, cost) in enumerate(sorted_users, 1):
            user_profile = await self.usage_monitor.analyze_user_patterns(user_id)
            
            table_data.append({
                'rank': rank,
                'user_id': user_id,
                'total_cost': f"${cost:.2f}",
                'efficiency': f"{user_profile.overall_relevance_rate:.1%}",
                'searches': user_profile.total_activities,
                'pattern': user_profile.primary_pattern.value if user_profile.primary_pattern else 'N/A'
            })
        
        return table_data
    
    async def _generate_resource_performance_table(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate resource performance table."""
        
        cost_summary = await self.cost_tracker.get_cost_summary(start_date, end_date)
        
        table_data = []
        for resource, cost in cost_summary.costs_by_resource.items():
            # Get usage metrics for this resource
            usage_metrics = await self.usage_monitor.get_usage_metrics(resource, start_date, end_date)
            
            roi = 0.0
            if cost > 0 and usage_metrics.total_searches > 0:
                roi = usage_metrics.total_searches / float(cost)  # Simple ROI calculation
            
            table_data.append({
                'resource': resource.value,
                'total_cost': f"${cost:.2f}",
                'usage_count': usage_metrics.total_searches + usage_metrics.total_documents,
                'success_rate': f"{usage_metrics.success_rate:.1%}",
                'roi': f"{roi:.2f}",
                'avg_cost_per_use': f"${usage_metrics.average_cost_per_search:.2f}" if usage_metrics.average_cost_per_search > 0 else "N/A"
            })
        
        # Sort by total cost descending
        table_data.sort(key=lambda x: float(x['total_cost'].replace('$', '').replace(',', '')), reverse=True)
        
        return table_data
    
    async def generate_report(self, 
                            report_type: ReportType,
                            period_start: datetime,
                            period_end: datetime,
                            generated_by: Optional[str] = None,
                            custom_params: Optional[Dict[str, Any]] = None) -> GeneratedReport:
        """Generate a comprehensive report."""
        
        report_id = f"report_{int(datetime.now().timestamp())}"
        
        if report_type == ReportType.MONTHLY_SUMMARY:
            return await self._generate_monthly_summary_report(
                report_id, period_start, period_end, generated_by
            )
        elif report_type == ReportType.QUARTERLY_REVIEW:
            return await self._generate_quarterly_review_report(
                report_id, period_start, period_end, generated_by
            )
        elif report_type == ReportType.USER_EFFICIENCY:
            return await self._generate_user_efficiency_report(
                report_id, period_start, period_end, generated_by
            )
        elif report_type == ReportType.RESOURCE_ANALYSIS:
            return await self._generate_resource_analysis_report(
                report_id, period_start, period_end, generated_by
            )
        elif report_type == ReportType.BUDGET_PERFORMANCE:
            return await self._generate_budget_performance_report(
                report_id, period_start, period_end, generated_by
            )
        elif report_type == ReportType.COST_OPTIMIZATION_PLAN:
            return await self._generate_cost_optimization_report(
                report_id, period_start, period_end, generated_by
            )
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
    
    async def _generate_monthly_summary_report(self,
                                             report_id: str,
                                             period_start: datetime,
                                             period_end: datetime,
                                             generated_by: Optional[str]) -> GeneratedReport:
        """Generate monthly summary report."""
        
        # Get all necessary data
        cost_summary = await self.cost_tracker.get_cost_summary(period_start, period_end)
        usage_analytics = await self.usage_monitor.generate_system_analytics(period_start, period_end)
        analysis_report = await self.cost_analyzer.analyze_costs(period_start, period_end)
        budget_report = await self.budget_manager.generate_budget_report(period_start, period_end)
        
        # Generate executive summary
        executive_summary = f"""
MONTHLY RESEARCH COST SUMMARY
{period_start.strftime('%B %Y')}

FINANCIAL OVERVIEW:
• Total Research Costs: ${cost_summary.total_cost:,.2f}
• Cost Trend: {cost_summary.cost_trend}
• Budget Utilization: {budget_report.overall_utilization:.1%}

EFFICIENCY METRICS:
• System Efficiency: {usage_analytics.average_relevance_rate:.1%}
• Total Users: {usage_analytics.total_users:,}
• Total Activities: {usage_analytics.total_activities:,}

KEY INSIGHTS:
• Primary cost driver: {analysis_report.primary_cost_drivers[0].description if analysis_report.primary_cost_drivers else 'N/A'}
• Top optimization opportunity: {analysis_report.top_optimization_opportunities[0].title if analysis_report.top_optimization_opportunities else 'N/A'}
• Potential monthly savings: ${analysis_report.total_potential_savings:,.2f}

ALERT STATUS:
• Active budget alerts: {len(budget_report.active_alerts)}
• Budgets over limit: {budget_report.budgets_over}
        """.strip()
        
        # Create report
        report = GeneratedReport(
            report_id=report_id,
            report_type=ReportType.MONTHLY_SUMMARY,
            title=f"Monthly Research Cost Summary - {period_start.strftime('%B %Y')}",
            executive_summary=executive_summary,
            period_start=period_start,
            period_end=period_end,
            generated_by=generated_by
        )
        
        # Add detailed sections
        report.detailed_sections = [
            {
                'title': 'Cost Analysis',
                'content': self._format_cost_analysis_section(cost_summary, analysis_report)
            },
            {
                'title': 'Usage Analytics',
                'content': self._format_usage_analytics_section(usage_analytics)
            },
            {
                'title': 'Budget Performance',
                'content': self._format_budget_performance_section(budget_report)
            }
        ]
        
        # Add charts
        report.charts = [
            await self._generate_monthly_trend_chart(period_start, period_end),
            await self._generate_resource_breakdown_chart(period_start, period_end),
            await self._generate_budget_status_chart()
        ]
        
        # Add recommendations
        report.recommendations = analysis_report.immediate_actions[:5]
        
        # Store report
        self.generated_reports[report_id] = report
        
        return report
    
    async def _generate_cost_optimization_report(self,
                                               report_id: str,
                                               period_start: datetime,
                                               period_end: datetime,
                                               generated_by: Optional[str]) -> GeneratedReport:
        """Generate cost optimization plan report."""
        
        analysis_report = await self.cost_analyzer.analyze_costs(period_start, period_end)
        
        executive_summary = f"""
COST OPTIMIZATION PLAN
Analysis Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}

OPTIMIZATION SUMMARY:
• Total Potential Savings: ${analysis_report.total_potential_savings:,.2f}/month
• Quick Win Savings: ${analysis_report.quick_win_savings:,.2f}/month
• Strategic Initiative Savings: ${analysis_report.strategic_savings:,.2f}/month

TOP OPPORTUNITIES:
        """.strip()
        
        for i, opportunity in enumerate(analysis_report.top_optimization_opportunities[:3], 1):
            executive_summary += f"\n{i}. {opportunity.title} - ${opportunity.estimated_monthly_savings:,.2f}/month"
        
        report = GeneratedReport(
            report_id=report_id,
            report_type=ReportType.COST_OPTIMIZATION_PLAN,
            title="Cost Optimization Plan",
            executive_summary=executive_summary,
            period_start=period_start,
            period_end=period_end,
            generated_by=generated_by
        )
        
        # Add detailed optimization sections
        report.detailed_sections = [
            {
                'title': 'Cost Driver Analysis',
                'content': self._format_cost_drivers_section(analysis_report.cost_drivers)
            },
            {
                'title': 'Optimization Opportunities',
                'content': self._format_optimization_opportunities_section(analysis_report.optimization_recommendations)
            },
            {
                'title': 'Implementation Roadmap',
                'content': self._format_implementation_roadmap_section(analysis_report)
            }
        ]
        
        # Add recommendations
        report.recommendations = analysis_report.immediate_actions + analysis_report.short_term_goals
        
        self.generated_reports[report_id] = report
        
        return report
    
    def _format_cost_analysis_section(self, cost_summary: CostSummary, analysis_report: CostAnalysisReport) -> str:
        """Format cost analysis section."""
        
        content = f"""
COST BREAKDOWN:
• Total Costs: ${cost_summary.total_cost:,.2f}
• Average Cost per Event: ${cost_summary.average_cost_per_event:.2f}
• Cost Trend: {cost_summary.cost_trend}

BY CATEGORY:
        """
        
        for category, cost in cost_summary.costs_by_category.items():
            percentage = (cost / cost_summary.total_cost) * 100 if cost_summary.total_cost > 0 else 0
            content += f"• {category.value}: ${cost:,.2f} ({percentage:.1f}%)\n"
        
        content += "\nBY RESOURCE:\n"
        for resource, cost in cost_summary.costs_by_resource.items():
            percentage = (cost / cost_summary.total_cost) * 100 if cost_summary.total_cost > 0 else 0
            content += f"• {resource.value}: ${cost:,.2f} ({percentage:.1f}%)\n"
        
        return content.strip()
    
    def _format_usage_analytics_section(self, analytics: UsageAnalytics) -> str:
        """Format usage analytics section."""
        
        content = f"""
USAGE OVERVIEW:
• Total Users: {analytics.total_users:,}
• Total Sessions: {analytics.total_sessions:,}
• Total Activities: {analytics.total_activities:,}
• Average Relevance Rate: {analytics.average_relevance_rate:.1%}

RESOURCE UTILIZATION:
        """
        
        for resource, usage in analytics.resource_usage.items():
            content += f"• {resource.value}: {usage:,} uses\n"
        
        content += "\nUSAGE PATTERNS:\n"
        for pattern, count in analytics.pattern_distribution.items():
            content += f"• {pattern.value}: {count} users\n"
        
        return content.strip()
    
    def _format_budget_performance_section(self, budget_report: BudgetReport) -> str:
        """Format budget performance section."""
        
        content = f"""
BUDGET OVERVIEW:
• Total Allocated: ${budget_report.total_allocated:,.2f}
• Total Spent: ${budget_report.total_spent:,.2f}
• Total Remaining: ${budget_report.total_remaining:,.2f}
• Overall Utilization: {budget_report.overall_utilization:.1%}

BUDGET STATUS:
• Budgets On Track: {budget_report.budgets_on_track}
• Budgets At Risk: {budget_report.budgets_at_risk}
• Budgets Over Limit: {budget_report.budgets_over}

ACTIVE ALERTS: {len(budget_report.active_alerts)}
        """
        
        return content.strip()
    
    def _format_cost_drivers_section(self, cost_drivers: List[Any]) -> str:
        """Format cost drivers section."""
        
        content = "PRIMARY COST DRIVERS:\n\n"
        
        for i, driver in enumerate(cost_drivers[:5], 1):
            content += f"{i}. {driver.description}\n"
            content += f"   Impact: ${driver.impact_amount:,.2f} ({driver.impact_percentage:.1f}%)\n"
            content += f"   Severity: {driver.severity}\n"
            content += f"   Potential Savings: ${driver.estimated_savings:,.2f}\n\n"
        
        return content.strip()
    
    def _format_optimization_opportunities_section(self, recommendations: List[Any]) -> str:
        """Format optimization opportunities section."""
        
        content = "OPTIMIZATION OPPORTUNITIES:\n\n"
        
        for i, rec in enumerate(recommendations[:10], 1):
            content += f"{i}. {rec.title}\n"
            content += f"   Description: {rec.description}\n"
            content += f"   Monthly Savings: ${rec.estimated_monthly_savings:,.2f}\n"
            content += f"   Priority: {rec.priority}\n"
            content += f"   Effort: {rec.effort_level}\n"
            content += f"   Timeline: {rec.timeline}\n\n"
        
        return content.strip()
    
    def _format_implementation_roadmap_section(self, analysis_report: CostAnalysisReport) -> str:
        """Format implementation roadmap section."""
        
        content = "IMPLEMENTATION ROADMAP:\n\n"
        
        content += "IMMEDIATE ACTIONS (0-30 days):\n"
        for action in analysis_report.immediate_actions:
            content += f"• {action}\n"
        
        content += "\nSHORT-TERM GOALS (1-3 months):\n"
        for goal in analysis_report.short_term_goals:
            content += f"• {goal}\n"
        
        content += "\nLONG-TERM STRATEGY (6-12 months):\n"
        for strategy in analysis_report.long_term_strategy:
            content += f"• {strategy}\n"
        
        return content.strip()
    
    async def export_dashboard_data(self, dashboard_id: str, format: str = "json") -> str:
        """Export dashboard data for external use."""
        
        dashboard = await self.get_dashboard_data(dashboard_id, force_refresh=True)
        
        if not dashboard:
            return ""
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            export_data = {
                'dashboard_id': dashboard.dashboard_id,
                'name': dashboard.name,
                'view_type': dashboard.view_type.value,
                'last_updated': dashboard.last_modified.isoformat(),
                'widgets': []
            }
            
            for widget in dashboard.widgets:
                widget_data = {
                    'widget_id': widget.widget_id,
                    'title': widget.title,
                    'type': widget.widget_type,
                    'last_updated': widget.last_updated.isoformat()
                }
                
                if widget.metric_value:
                    widget_data['metric_value'] = widget.metric_value
                    widget_data['metric_trend'] = widget.metric_trend
                
                if widget.chart_data:
                    widget_data['chart_data'] = {
                        'type': widget.chart_data.chart_type.value,
                        'labels': widget.chart_data.labels,
                        'datasets': widget.chart_data.datasets
                    }
                
                if widget.table_data:
                    widget_data['table_data'] = widget.table_data
                
                if widget.alert_data:
                    widget_data['alert_data'] = widget.alert_data
                
                export_data['widgets'].append(widget_data)
            
            return json.dumps(export_data, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time cost and usage metrics."""
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check cache
        cache_key = "real_time_metrics"
        if (cache_key in self.realtime_cache and 
            cache_key in self.cache_timestamps and
            now - self.cache_timestamps[cache_key] < self.cache_ttl):
            return self.realtime_cache[cache_key]
        
        # Calculate real-time metrics
        today_summary = await self.cost_tracker.get_cost_summary(today_start, now)
        
        metrics = {
            'current_timestamp': now.isoformat(),
            'today_costs': float(today_summary.total_cost),
            'today_events': today_summary.total_events,
            'hourly_rate': float(today_summary.total_cost) / max(1, (now - today_start).seconds / 3600),
            'active_sessions': len(self.usage_monitor.active_sessions),
            'pending_budget_alerts': len([
                alert for alerts in self.budget_manager.pending_alerts.values() 
                for alert in alerts if not alert.acknowledged
            ])
        }
        
        # Cache results
        self.realtime_cache[cache_key] = metrics
        self.cache_timestamps[cache_key] = now
        
        return metrics
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old dashboard and report data."""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Clean up old generated reports
        old_reports = [
            report_id for report_id, report in self.generated_reports.items()
            if report.generated_date < cutoff_date
        ]
        
        for report_id in old_reports:
            del self.generated_reports[report_id]
        
        # Clear old cache entries
        old_cache_keys = [
            key for key, timestamp in self.cache_timestamps.items()
            if timestamp < cutoff_date
        ]
        
        for key in old_cache_keys:
            self.realtime_cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
        
        self.logger.info(f"Cleaned up {len(old_reports)} old reports and {len(old_cache_keys)} cache entries")


# Helper functions
async def get_executive_dashboard() -> Optional[DashboardLayout]:
    """Helper function to get executive dashboard."""
    cost_tracker = CostTracker()
    usage_monitor = UsageMonitor()
    cost_analyzer = CostAnalyzer(cost_tracker, usage_monitor)
    budget_manager = BudgetManager(cost_tracker)
    
    dashboard = CostDashboard(cost_tracker, usage_monitor, cost_analyzer, budget_manager)
    return await dashboard.get_dashboard_data("executive_summary")

async def generate_monthly_cost_report(month: int, year: int) -> GeneratedReport:
    """Helper function to generate monthly cost report."""
    cost_tracker = CostTracker()
    usage_monitor = UsageMonitor()
    cost_analyzer = CostAnalyzer(cost_tracker, usage_monitor)
    budget_manager = BudgetManager(cost_tracker)
    
    dashboard = CostDashboard(cost_tracker, usage_monitor, cost_analyzer, budget_manager)
    
    period_start = datetime(year, month, 1)
    if month == 12:
        period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    return await dashboard.generate_report(
        ReportType.MONTHLY_SUMMARY,
        period_start,
        period_end
    )