"""
Dashboard Generator Service

Dynamic dashboard generation with customizable widgets and real-time
financial metrics for legal practice management.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
import asyncio
import logging
import json
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from .financial_analytics import FinancialAnalytics, DateRange, ReportPeriod
from .advanced_models import BillingMatter, TimeEntry, Invoice, Payment
from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class WidgetType(str, Enum):
    """Types of dashboard widgets."""
    KPI_CARD = "kpi_card"
    CHART = "chart"
    TABLE = "table"
    GAUGE = "gauge"
    PROGRESS_BAR = "progress_bar"
    HEATMAP = "heatmap"
    CALENDAR = "calendar"
    LIST = "list"


class ChartType(str, Enum):
    """Types of charts."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    CANDLESTICK = "candlestick"


class DashboardTheme(str, Enum):
    """Dashboard themes."""
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"


class WidgetSize(str, Enum):
    """Widget sizes."""
    SMALL = "small"      # 1x1
    MEDIUM = "medium"    # 2x1
    LARGE = "large"      # 2x2
    WIDE = "wide"        # 3x1
    TALL = "tall"        # 1x3
    EXTRA_LARGE = "xl"   # 3x2


@dataclass
class WidgetPosition:
    """Widget position on dashboard grid."""
    row: int
    column: int
    width: int = 2
    height: int = 2


class KPIWidget(BaseModel):
    """Key Performance Indicator widget."""
    id: str
    title: str
    value: Union[Decimal, float, int, str]
    previous_value: Optional[Union[Decimal, float, int, str]] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "flat"
    format_type: str = "currency"  # "currency", "percentage", "number", "duration"
    color: Optional[str] = None
    icon: Optional[str] = None
    subtitle: Optional[str] = None


class ChartWidget(BaseModel):
    """Chart widget for visualizations."""
    id: str
    title: str
    chart_type: ChartType
    data: Dict[str, Any]
    options: Dict[str, Any] = Field(default_factory=dict)
    subtitle: Optional[str] = None


class TableWidget(BaseModel):
    """Table widget for tabular data."""
    id: str
    title: str
    headers: List[str]
    rows: List[List[Any]]
    sortable: bool = True
    searchable: bool = True
    pagination: bool = True
    row_limit: int = 10


class GaugeWidget(BaseModel):
    """Gauge widget for progress indicators."""
    id: str
    title: str
    value: float
    min_value: float = 0
    max_value: float = 100
    target_value: Optional[float] = None
    color_ranges: List[Dict[str, Any]] = Field(default_factory=list)
    unit: str = "%"


class DashboardWidget(BaseModel):
    """Generic dashboard widget container."""
    id: str
    type: WidgetType
    title: str
    size: WidgetSize
    position: WidgetPosition
    data: Union[KPIWidget, ChartWidget, TableWidget, GaugeWidget, Dict[str, Any]]
    refresh_interval: Optional[int] = None  # seconds
    permissions: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class DashboardLayout(BaseModel):
    """Dashboard layout configuration."""
    id: str
    name: str
    description: Optional[str] = None
    theme: DashboardTheme = DashboardTheme.LIGHT
    widgets: List[DashboardWidget]
    grid_columns: int = 12
    grid_rows: int = 20
    auto_refresh: bool = True
    refresh_interval: int = 300  # seconds
    created_by: int
    is_default: bool = False
    is_public: bool = False


class DashboardFilter(BaseModel):
    """Dashboard-level filters."""
    date_range: DateRange
    matter_ids: Optional[List[int]] = None
    attorney_ids: Optional[List[int]] = None
    client_ids: Optional[List[int]] = None
    practice_areas: Optional[List[str]] = None


class DashboardGenerator:
    """
    Advanced dashboard generator with customizable widgets and real-time metrics.
    """
    
    def __init__(self):
        self.analytics = FinancialAnalytics()
        self.default_colors = {
            'primary': '#3B82F6',
            'success': '#10B981', 
            'warning': '#F59E0B',
            'danger': '#EF4444',
            'info': '#06B6D4'
        }
        
    async def generate_executive_dashboard(
        self,
        user_id: int,
        filters: DashboardFilter,
        db: Optional[AsyncSession] = None
    ) -> DashboardLayout:
        """Generate executive summary dashboard."""
        if not db:
            async with get_db_session() as db:
                return await self._generate_executive_dashboard_impl(user_id, filters, db)
        return await self._generate_executive_dashboard_impl(user_id, filters, db)
    
    async def _generate_executive_dashboard_impl(
        self,
        user_id: int,
        filters: DashboardFilter,
        db: AsyncSession
    ) -> DashboardLayout:
        """Implementation of executive dashboard generation."""
        widgets = []
        
        # Get financial metrics
        filter_dict = {
            'date_start': filters.date_range.start_date,
            'date_end': filters.date_range.end_date,
            'matter_ids': filters.matter_ids,
            'attorney_ids': filters.attorney_ids
        }
        
        # Generate widgets concurrently
        kpi_widgets_task = self._generate_kpi_widgets(filters, filter_dict, db)
        revenue_chart_task = self._generate_revenue_chart(filters, filter_dict, db)
        collection_chart_task = self._generate_collection_chart(filters, filter_dict, db)
        top_matters_task = self._generate_top_matters_table(filters, filter_dict, db)
        attorney_performance_task = self._generate_attorney_performance_chart(filters, filter_dict, db)
        ar_aging_task = self._generate_ar_aging_chart(filters, filter_dict, db)
        
        kpi_widgets, revenue_chart, collection_chart, top_matters_table, \
        attorney_chart, ar_aging_chart = await asyncio.gather(
            kpi_widgets_task, revenue_chart_task, collection_chart_task,
            top_matters_task, attorney_performance_task, ar_aging_task
        )
        
        # Add widgets to layout
        widgets.extend(kpi_widgets)
        widgets.extend([
            revenue_chart, collection_chart, top_matters_table,
            attorney_chart, ar_aging_chart
        ])
        
        return DashboardLayout(
            id=f"executive_dashboard_{user_id}",
            name="Executive Dashboard",
            description="High-level financial metrics and performance indicators",
            theme=DashboardTheme.LIGHT,
            widgets=widgets,
            created_by=user_id,
            is_default=True
        )
    
    async def _generate_kpi_widgets(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> List[DashboardWidget]:
        """Generate KPI widgets."""
        # Get current period metrics
        revenue_metrics = await self.analytics.get_revenue_metrics(filters.date_range, filter_dict, db)
        collection_metrics = await self.analytics.get_collection_metrics(filters.date_range, filter_dict, db)
        profitability_metrics = await self.analytics.get_profitability_metrics(filters.date_range, filter_dict, db)
        
        # Get previous period for comparison
        period_delta = filters.date_range.end_date - filters.date_range.start_date
        previous_range = DateRange(
            start_date=filters.date_range.start_date - period_delta,
            end_date=filters.date_range.start_date,
            period=filters.date_range.period
        )
        
        previous_revenue = await self.analytics.get_revenue_metrics(previous_range, filter_dict, db)
        
        widgets = []
        
        # Total Revenue KPI
        revenue_change = 0.0
        if previous_revenue.total_revenue > 0:
            revenue_change = float((revenue_metrics.total_revenue - previous_revenue.total_revenue) / previous_revenue.total_revenue * 100)
            
        widgets.append(DashboardWidget(
            id="total_revenue_kpi",
            type=WidgetType.KPI_CARD,
            title="Total Revenue",
            size=WidgetSize.MEDIUM,
            position=WidgetPosition(row=0, column=0, width=3, height=2),
            data=KPIWidget(
                id="total_revenue",
                title="Total Revenue",
                value=revenue_metrics.total_revenue,
                previous_value=previous_revenue.total_revenue,
                change_percentage=revenue_change,
                trend="up" if revenue_change > 0 else "down" if revenue_change < 0 else "flat",
                format_type="currency",
                color=self.default_colors['success'] if revenue_change > 0 else self.default_colors['danger'],
                icon="trending-up" if revenue_change > 0 else "trending-down"
            )
        ))
        
        # Collection Rate KPI
        widgets.append(DashboardWidget(
            id="collection_rate_kpi",
            type=WidgetType.KPI_CARD,
            title="Collection Rate",
            size=WidgetSize.MEDIUM,
            position=WidgetPosition(row=0, column=3, width=3, height=2),
            data=KPIWidget(
                id="collection_rate",
                title="Collection Rate",
                value=collection_metrics.collection_rate,
                format_type="percentage",
                color=self.default_colors['success'] if collection_metrics.collection_rate > 90 else self.default_colors['warning'],
                icon="dollar-sign"
            )
        ))
        
        # Outstanding AR KPI
        widgets.append(DashboardWidget(
            id="outstanding_ar_kpi",
            type=WidgetType.KPI_CARD,
            title="Outstanding A/R",
            size=WidgetSize.MEDIUM,
            position=WidgetPosition(row=0, column=6, width=3, height=2),
            data=KPIWidget(
                id="outstanding_ar",
                title="Outstanding A/R",
                value=collection_metrics.outstanding_ar,
                format_type="currency",
                color=self.default_colors['warning'] if collection_metrics.outstanding_ar > 50000 else self.default_colors['info'],
                icon="clock"
            )
        ))
        
        # Profit Margin KPI
        widgets.append(DashboardWidget(
            id="profit_margin_kpi",
            type=WidgetType.KPI_CARD,
            title="Profit Margin",
            size=WidgetSize.MEDIUM,
            position=WidgetPosition(row=0, column=9, width=3, height=2),
            data=KPIWidget(
                id="profit_margin",
                title="Profit Margin",
                value=profitability_metrics.gross_profit_margin,
                format_type="percentage",
                color=self.default_colors['success'] if profitability_metrics.gross_profit_margin > 30 else self.default_colors['warning'],
                icon="percent"
            )
        ))
        
        return widgets
    
    async def _generate_revenue_chart(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate revenue trend chart."""
        # Get financial trends
        trends = await self.analytics.get_financial_trends(filters.date_range, filter_dict, db)
        revenue_trend = trends.get('revenue', [])
        
        # Prepare chart data
        labels = [trend.period for trend in revenue_trend]
        data = [float(trend.value) for trend in revenue_trend]
        
        chart_data = {
            'labels': labels,
            'datasets': [{
                'label': 'Revenue',
                'data': data,
                'backgroundColor': self.default_colors['primary'],
                'borderColor': self.default_colors['primary'],
                'borderWidth': 2,
                'fill': True,
                'tension': 0.4
            }]
        }
        
        chart_options = {
            'responsive': True,
            'plugins': {
                'legend': {
                    'display': False
                }
            },
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'ticks': {
                        'callback': 'function(value) { return "$" + value.toLocaleString(); }'
                    }
                }
            }
        }
        
        return DashboardWidget(
            id="revenue_trend_chart",
            type=WidgetType.CHART,
            title="Revenue Trend",
            size=WidgetSize.LARGE,
            position=WidgetPosition(row=2, column=0, width=6, height=4),
            data=ChartWidget(
                id="revenue_trend",
                title="Revenue Trend",
                chart_type=ChartType.LINE,
                data=chart_data,
                options=chart_options
            )
        )
    
    async def _generate_collection_chart(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate collection performance chart."""
        # Get collection trends
        trends = await self.analytics.get_financial_trends(filters.date_range, filter_dict, db)
        collection_trend = trends.get('collection', [])
        
        # Prepare chart data
        labels = [trend.period for trend in collection_trend]
        data = [float(trend.value) for trend in collection_trend]
        
        chart_data = {
            'labels': labels,
            'datasets': [{
                'label': 'Collections',
                'data': data,
                'backgroundColor': self.default_colors['success'],
                'borderColor': self.default_colors['success'],
                'borderWidth': 2
            }]
        }
        
        chart_options = {
            'responsive': True,
            'plugins': {
                'legend': {
                    'display': False
                }
            },
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'ticks': {
                        'callback': 'function(value) { return "$" + value.toLocaleString(); }'
                    }
                }
            }
        }
        
        return DashboardWidget(
            id="collection_chart",
            type=WidgetType.CHART,
            title="Collections",
            size=WidgetSize.LARGE,
            position=WidgetPosition(row=2, column=6, width=6, height=4),
            data=ChartWidget(
                id="collection_trend",
                title="Collections",
                chart_type=ChartType.BAR,
                data=chart_data,
                options=chart_options
            )
        )
    
    async def _generate_top_matters_table(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate top matters performance table."""
        top_matters = await self.analytics.get_top_matters_performance(
            filters.date_range, filter_dict, 10, db
        )
        
        headers = [
            "Matter", "Client", "Revenue", "Hours", "Avg Rate", "Collection %"
        ]
        
        rows = []
        for matter in top_matters:
            rows.append([
                matter.matter_name,
                matter.client_name,
                f"${matter.total_revenue:,.2f}",
                f"{matter.billable_hours:.1f}",
                f"${matter.average_rate:.0f}",
                f"{matter.collection_rate:.1f}%"
            ])
        
        return DashboardWidget(
            id="top_matters_table",
            type=WidgetType.TABLE,
            title="Top Matters by Revenue",
            size=WidgetSize.WIDE,
            position=WidgetPosition(row=6, column=0, width=8, height=4),
            data=TableWidget(
                id="top_matters",
                title="Top Matters by Revenue",
                headers=headers,
                rows=rows,
                sortable=True,
                searchable=True,
                row_limit=10
            )
        )
    
    async def _generate_attorney_performance_chart(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate attorney performance chart."""
        attorney_performance = await self.analytics.get_attorney_performance(
            filters.date_range, filter_dict, db
        )
        
        # Take top 10 attorneys
        top_attorneys = attorney_performance[:10]
        
        labels = [f"Attorney {perf.attorney_id}" for perf in top_attorneys]
        revenue_data = [float(perf.billable_revenue) for perf in top_attorneys]
        hours_data = [float(perf.billable_hours) for perf in top_attorneys]
        
        chart_data = {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Revenue',
                    'data': revenue_data,
                    'backgroundColor': self.default_colors['primary'],
                    'yAxisID': 'y'
                },
                {
                    'label': 'Hours',
                    'data': hours_data,
                    'backgroundColor': self.default_colors['success'],
                    'type': 'line',
                    'yAxisID': 'y1'
                }
            ]
        }
        
        chart_options = {
            'responsive': True,
            'scales': {
                'y': {
                    'type': 'linear',
                    'display': True,
                    'position': 'left'
                },
                'y1': {
                    'type': 'linear',
                    'display': True,
                    'position': 'right',
                    'grid': {
                        'drawOnChartArea': False
                    }
                }
            }
        }
        
        return DashboardWidget(
            id="attorney_performance_chart",
            type=WidgetType.CHART,
            title="Attorney Performance",
            size=WidgetSize.LARGE,
            position=WidgetPosition(row=6, column=8, width=4, height=4),
            data=ChartWidget(
                id="attorney_performance",
                title="Attorney Performance",
                chart_type=ChartType.BAR,
                data=chart_data,
                options=chart_options
            )
        )
    
    async def _generate_ar_aging_chart(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate accounts receivable aging chart."""
        collection_metrics = await self.analytics.get_collection_metrics(
            filters.date_range, filter_dict, db
        )
        
        aged_ar = collection_metrics.aged_ar_breakdown
        
        labels = list(aged_ar.keys())
        data = [float(value) for value in aged_ar.values()]
        
        # Color coding for aging buckets
        colors = [
            self.default_colors['success'],  # 0-30 days
            self.default_colors['info'],     # 31-60 days  
            self.default_colors['warning'],  # 61-90 days
            self.default_colors['danger'],   # 91-120 days
            '#DC2626'                        # Over 120 days
        ]
        
        chart_data = {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors[:len(labels)],
                'borderWidth': 0
            }]
        }
        
        chart_options = {
            'responsive': True,
            'plugins': {
                'legend': {
                    'position': 'bottom'
                }
            }
        }
        
        return DashboardWidget(
            id="ar_aging_chart",
            type=WidgetType.CHART,
            title="A/R Aging",
            size=WidgetSize.MEDIUM,
            position=WidgetPosition(row=10, column=0, width=4, height=3),
            data=ChartWidget(
                id="ar_aging",
                title="A/R Aging",
                chart_type=ChartType.DOUGHNUT,
                data=chart_data,
                options=chart_options
            )
        )
    
    async def generate_operational_dashboard(
        self,
        user_id: int,
        filters: DashboardFilter,
        db: Optional[AsyncSession] = None
    ) -> DashboardLayout:
        """Generate operational metrics dashboard."""
        if not db:
            async with get_db_session() as db:
                return await self._generate_operational_dashboard_impl(user_id, filters, db)
        return await self._generate_operational_dashboard_impl(user_id, filters, db)
    
    async def _generate_operational_dashboard_impl(
        self,
        user_id: int,
        filters: DashboardFilter,
        db: AsyncSession
    ) -> DashboardLayout:
        """Implementation of operational dashboard generation."""
        widgets = []
        
        # Add utilization gauge
        utilization_widget = await self._generate_utilization_gauge(filters, db)
        widgets.append(utilization_widget)
        
        # Add time entry trends
        time_entry_chart = await self._generate_time_entry_chart(filters, db)
        widgets.append(time_entry_chart)
        
        # Add recent activity list
        recent_activity = await self._generate_recent_activity_list(filters, db)
        widgets.append(recent_activity)
        
        return DashboardLayout(
            id=f"operational_dashboard_{user_id}",
            name="Operational Dashboard",
            description="Day-to-day operational metrics and activity",
            theme=DashboardTheme.LIGHT,
            widgets=widgets,
            created_by=user_id
        )
    
    async def _generate_utilization_gauge(
        self,
        filters: DashboardFilter,
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate utilization rate gauge."""
        filter_dict = {
            'date_start': filters.date_range.start_date,
            'date_end': filters.date_range.end_date,
            'attorney_ids': filters.attorney_ids
        }
        
        revenue_metrics = await self.analytics.get_revenue_metrics(
            filters.date_range, filter_dict, db
        )
        
        color_ranges = [
            {'from': 0, 'to': 60, 'color': self.default_colors['danger']},
            {'from': 60, 'to': 80, 'color': self.default_colors['warning']},
            {'from': 80, 'to': 100, 'color': self.default_colors['success']}
        ]
        
        return DashboardWidget(
            id="utilization_gauge",
            type=WidgetType.GAUGE,
            title="Utilization Rate",
            size=WidgetSize.MEDIUM,
            position=WidgetPosition(row=0, column=0, width=4, height=3),
            data=GaugeWidget(
                id="utilization",
                title="Utilization Rate",
                value=revenue_metrics.utilization_rate,
                min_value=0,
                max_value=100,
                target_value=80.0,
                color_ranges=color_ranges,
                unit="%"
            )
        )
    
    async def _generate_time_entry_chart(
        self,
        filters: DashboardFilter,
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate time entry trend chart."""
        # This would require time entry trend analysis
        # For now, return a placeholder
        
        chart_data = {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'datasets': [{
                'label': 'Hours Logged',
                'data': [8.5, 7.2, 9.1, 6.8, 8.3],
                'backgroundColor': self.default_colors['primary']
            }]
        }
        
        return DashboardWidget(
            id="time_entry_chart",
            type=WidgetType.CHART,
            title="Daily Time Entries",
            size=WidgetSize.LARGE,
            position=WidgetPosition(row=0, column=4, width=8, height=3),
            data=ChartWidget(
                id="time_entries",
                title="Daily Time Entries",
                chart_type=ChartType.BAR,
                data=chart_data
            )
        )
    
    async def _generate_recent_activity_list(
        self,
        filters: DashboardFilter,
        db: AsyncSession
    ) -> DashboardWidget:
        """Generate recent activity list."""
        # This would query recent time entries, payments, etc.
        # For now, return a placeholder
        
        activities = [
            "New payment received: $5,000 from ABC Corp",
            "Time entry submitted: 2.5 hours on Contract Review",
            "Invoice generated: INV-2024-001 for $12,500",
            "Expense approved: $150 for Legal Research",
            "New matter opened: Litigation Support"
        ]
        
        return DashboardWidget(
            id="recent_activity",
            type=WidgetType.LIST,
            title="Recent Activity",
            size=WidgetSize.MEDIUM,
            position=WidgetPosition(row=3, column=0, width=6, height=4),
            data={
                'items': activities,
                'show_timestamps': True,
                'max_items': 10
            }
        )
    
    def customize_dashboard(
        self,
        layout: DashboardLayout,
        customizations: Dict[str, Any]
    ) -> DashboardLayout:
        """Apply customizations to dashboard layout."""
        if 'theme' in customizations:
            layout.theme = DashboardTheme(customizations['theme'])
            
        if 'widgets' in customizations:
            for widget_custom in customizations['widgets']:
                widget_id = widget_custom.get('id')
                widget = next((w for w in layout.widgets if w.id == widget_id), None)
                
                if widget:
                    if 'position' in widget_custom:
                        pos = widget_custom['position']
                        widget.position = WidgetPosition(**pos)
                        
                    if 'size' in widget_custom:
                        widget.size = WidgetSize(widget_custom['size'])
                        
                    if 'title' in widget_custom:
                        widget.title = widget_custom['title']
                        
        return layout
    
    def export_dashboard_config(self, layout: DashboardLayout) -> Dict[str, Any]:
        """Export dashboard configuration as JSON."""
        return layout.dict()
    
    def import_dashboard_config(self, config: Dict[str, Any]) -> DashboardLayout:
        """Import dashboard configuration from JSON."""
        return DashboardLayout(**config)