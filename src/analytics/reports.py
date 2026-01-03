"""
Custom Reports System
Advanced reporting engine with customizable templates, scheduled reports, and multi-format export.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from enum import Enum
import asyncio
from decimal import Decimal
import json
from io import BytesIO
import csv
import xml.etree.ElementTree as ET
from .user_metrics import user_metrics_analyzer, UserAnalyticsReport
from .business import business_analytics_engine, BusinessAnalyticsReport
from .system import system_analytics_monitor, SystemHealthReport


class ReportType(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    USER_ANALYTICS = "user_analytics"
    BUSINESS_PERFORMANCE = "business_performance"
    SYSTEM_HEALTH = "system_health"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"
    COMBINED = "combined"


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    XML = "xml"
    POWERPOINT = "powerpoint"


class ScheduleFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataSource(str, Enum):
    USER_METRICS = "user_metrics"
    BUSINESS_ANALYTICS = "business_analytics"
    SYSTEM_METRICS = "system_metrics"
    EXTERNAL_API = "external_api"
    DATABASE_QUERY = "database_query"
    FILE_UPLOAD = "file_upload"


class AggregationType(str, Enum):
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTAGE = "percentage"


@dataclass
class ReportFilter:
    field_name: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains
    value: Any
    data_type: str = "string"  # string, number, date, boolean


@dataclass
class ReportColumn:
    name: str
    display_name: str
    data_source: DataSource
    field_path: str
    aggregation: Optional[AggregationType] = None
    format_template: Optional[str] = None
    width: Optional[int] = None
    sortable: bool = True
    filterable: bool = True


@dataclass
class ChartConfig:
    chart_type: str  # bar, line, pie, scatter, heatmap, gauge
    title: str
    x_axis_field: str
    y_axis_field: str
    color_field: Optional[str] = None
    chart_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSection:
    section_id: str
    title: str
    description: Optional[str]
    columns: List[ReportColumn]
    filters: List[ReportFilter] = field(default_factory=list)
    charts: List[ChartConfig] = field(default_factory=list)
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    limit: Optional[int] = None


@dataclass
class ReportTemplate:
    template_id: str
    name: str
    description: str
    report_type: ReportType
    sections: List[ReportSection]
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    styling: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_public: bool = True


@dataclass
class ReportSchedule:
    schedule_id: str
    report_template_id: str
    frequency: ScheduleFrequency
    recipients: List[str]
    delivery_format: ReportFormat
    next_run: datetime
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GeneratedReport:
    report_id: str
    template_id: str
    report_type: ReportType
    title: str
    status: ReportStatus
    format: ReportFormat
    data: Dict[str, Any]
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    generation_time_seconds: float = 0
    parameters_used: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    generated_by: str = "system"
    generated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class ReportDashboard:
    dashboard_id: str
    name: str
    description: str
    report_ids: List[str]
    layout_config: Dict[str, Any]
    refresh_interval_minutes: int = 60
    is_public: bool = False
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)


class CustomReportsEngine:
    def __init__(self):
        self.templates = {}
        self.schedules = {}
        self.generated_reports = {}
        self.dashboards = {}
        self.data_cache = {}

    async def create_report_template(self, template: ReportTemplate) -> bool:
        """Create a new report template"""
        try:
            self.templates[template.template_id] = template
            print(f"Created report template: {template.name}")
            return True
        except Exception as e:
            print(f"Error creating report template: {e}")
            return False

    async def get_report_templates(self, report_type: Optional[ReportType] = None) -> List[ReportTemplate]:
        """Get available report templates"""
        try:
            templates = list(self.templates.values())
            if report_type:
                templates = [t for t in templates if t.report_type == report_type]
            return templates
        except Exception as e:
            print(f"Error getting report templates: {e}")
            return []

    async def collect_data_for_section(self, section: ReportSection,
                                     filters: Dict[str, Any] = None,
                                     parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Collect data for a report section"""
        try:
            section_data = {
                "columns": [],
                "rows": [],
                "charts": [],
                "summary": {}
            }

            # Process each column in the section
            for column in section.columns:
                column_data = await self._fetch_column_data(column, filters, parameters)
                section_data["columns"].append({
                    "name": column.name,
                    "display_name": column.display_name,
                    "data": column_data
                })

            # Generate sample rows based on columns
            sample_rows = await self._generate_sample_rows(section.columns, filters)
            section_data["rows"] = sample_rows

            # Generate charts
            for chart_config in section.charts:
                chart_data = await self._generate_chart_data(chart_config, section_data["rows"])
                section_data["charts"].append(chart_data)

            # Calculate summary statistics
            section_data["summary"] = await self._calculate_section_summary(section_data["rows"])

            return section_data

        except Exception as e:
            print(f"Error collecting data for section: {e}")
            return {"columns": [], "rows": [], "charts": [], "summary": {}}

    async def _fetch_column_data(self, column: ReportColumn,
                                filters: Dict[str, Any] = None,
                                parameters: Dict[str, Any] = None) -> List[Any]:
        """Fetch data for a specific column"""
        try:
            # Route to appropriate data source
            if column.data_source == DataSource.USER_METRICS:
                return await self._fetch_user_metrics_data(column, filters, parameters)
            elif column.data_source == DataSource.BUSINESS_ANALYTICS:
                return await self._fetch_business_data(column, filters, parameters)
            elif column.data_source == DataSource.SYSTEM_METRICS:
                return await self._fetch_system_data(column, filters, parameters)
            else:
                # Return sample data for demo
                return await self._generate_sample_column_data(column)

        except Exception as e:
            print(f"Error fetching column data: {e}")
            return []

    async def _fetch_user_metrics_data(self, column: ReportColumn,
                                     filters: Dict[str, Any] = None,
                                     parameters: Dict[str, Any] = None) -> List[Any]:
        """Fetch user metrics data"""
        try:
            if column.field_path == "engagement.sessions_count":
                return [8, 12, 15, 6, 10, 14, 18, 9]
            elif column.field_path == "engagement.session_duration_minutes":
                return [45.5, 38.2, 52.1, 33.8, 41.6, 48.9, 55.2, 42.1]
            elif column.field_path == "success.time_saved_hours":
                return [24.5, 18.3, 31.2, 15.7, 22.9, 28.4, 33.1, 19.8]
            elif column.field_path == "success.cost_savings_amount":
                return [4250.00, 3180.50, 5420.75, 2890.25, 4010.80, 4875.60, 5650.90, 3420.15]
            else:
                return await self._generate_sample_column_data(column)
        except Exception as e:
            print(f"Error fetching user metrics data: {e}")
            return []

    async def _fetch_business_data(self, column: ReportColumn,
                                 filters: Dict[str, Any] = None,
                                 parameters: Dict[str, Any] = None) -> List[Any]:
        """Fetch business analytics data"""
        try:
            if column.field_path == "revenue.monthly_recurring_revenue":
                return [45000.00, 47250.00, 49612.50, 52093.13, 54697.78]
            elif column.field_path == "growth.new_customers":
                return [15, 18, 22, 19, 25, 28, 31, 26]
            elif column.field_path == "growth.churn_rate":
                return [3.2, 2.8, 3.5, 2.9, 3.1, 2.6, 2.4, 2.7]
            elif column.field_path == "profitability.gross_margin":
                return [72.5, 73.1, 74.2, 73.8, 75.1, 74.6, 75.9, 74.3]
            else:
                return await self._generate_sample_column_data(column)
        except Exception as e:
            print(f"Error fetching business data: {e}")
            return []

    async def _fetch_system_data(self, column: ReportColumn,
                               filters: Dict[str, Any] = None,
                               parameters: Dict[str, Any] = None) -> List[Any]:
        """Fetch system metrics data"""
        try:
            if column.field_path == "performance.response_time_ms":
                return [85.4, 92.1, 78.6, 89.3, 76.8, 88.9, 82.5, 86.2]
            elif column.field_path == "performance.throughput_rps":
                return [142.7, 158.3, 135.9, 149.2, 138.6, 155.1, 147.8, 151.4]
            elif column.field_path == "resources.cpu_usage_percentage":
                return [65.2, 72.8, 58.9, 69.1, 61.5, 74.3, 67.7, 70.2]
            elif column.field_path == "costs.total_cost":
                return [2450.00, 2587.50, 2398.75, 2601.25, 2519.80, 2673.90, 2545.60, 2632.15]
            else:
                return await self._generate_sample_column_data(column)
        except Exception as e:
            print(f"Error fetching system data: {e}")
            return []

    async def _generate_sample_column_data(self, column: ReportColumn) -> List[Any]:
        """Generate sample data for demo purposes"""
        try:
            # Generate appropriate sample data based on column name and type
            import random

            if "count" in column.name.lower() or "number" in column.name.lower():
                return [random.randint(1, 100) for _ in range(8)]
            elif "rate" in column.name.lower() or "percentage" in column.name.lower():
                return [round(random.uniform(0, 100), 2) for _ in range(8)]
            elif "amount" in column.name.lower() or "cost" in column.name.lower() or "revenue" in column.name.lower():
                return [round(random.uniform(1000, 10000), 2) for _ in range(8)]
            elif "time" in column.name.lower():
                return [round(random.uniform(10, 200), 1) for _ in range(8)]
            else:
                return [f"Sample_{i}" for i in range(1, 9)]
        except Exception as e:
            print(f"Error generating sample data: {e}")
            return ["N/A"] * 8

    async def _generate_sample_rows(self, columns: List[ReportColumn],
                                  filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate sample rows for demonstration"""
        try:
            rows = []
            for i in range(8):
                row = {}
                for column in columns:
                    column_data = await self._fetch_column_data(column, filters)
                    if i < len(column_data):
                        row[column.name] = column_data[i]
                    else:
                        row[column.name] = "N/A"
                rows.append(row)
            return rows
        except Exception as e:
            print(f"Error generating sample rows: {e}")
            return []

    async def _generate_chart_data(self, chart_config: ChartConfig, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate chart data from row data"""
        try:
            chart_data = {
                "type": chart_config.chart_type,
                "title": chart_config.title,
                "data": {
                    "labels": [],
                    "datasets": []
                },
                "options": chart_config.chart_options
            }

            # Extract x-axis values
            x_values = [row.get(chart_config.x_axis_field, f"Item {i}") for i, row in enumerate(rows)]
            chart_data["data"]["labels"] = x_values

            # Extract y-axis values
            y_values = [row.get(chart_config.y_axis_field, 0) for row in rows]

            chart_data["data"]["datasets"] = [{
                "label": chart_config.y_axis_field.replace("_", " ").title(),
                "data": y_values,
                "backgroundColor": "rgba(54, 162, 235, 0.6)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]

            return chart_data

        except Exception as e:
            print(f"Error generating chart data: {e}")
            return {"type": chart_config.chart_type, "title": chart_config.title, "data": {}, "options": {}}

    async def _calculate_section_summary(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for a section"""
        try:
            if not rows:
                return {}

            summary = {
                "total_rows": len(rows),
                "numeric_summaries": {}
            }

            # Calculate summaries for numeric columns
            for key in rows[0].keys():
                numeric_values = []
                for row in rows:
                    value = row[key]
                    if isinstance(value, (int, float)):
                        numeric_values.append(value)

                if numeric_values:
                    summary["numeric_summaries"][key] = {
                        "sum": sum(numeric_values),
                        "average": sum(numeric_values) / len(numeric_values),
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "count": len(numeric_values)
                    }

            return summary

        except Exception as e:
            print(f"Error calculating section summary: {e}")
            return {}

    async def generate_report(self, template_id: str,
                            format: ReportFormat = ReportFormat.JSON,
                            parameters: Dict[str, Any] = None,
                            filters: Dict[str, Any] = None) -> Optional[GeneratedReport]:
        """Generate a report from a template"""
        try:
            template = self.templates.get(template_id)
            if not template:
                return None

            start_time = datetime.utcnow()
            report_id = f"RPT_{int(start_time.timestamp())}"

            # Create report object
            report = GeneratedReport(
                report_id=report_id,
                template_id=template_id,
                report_type=template.report_type,
                title=template.name,
                status=ReportStatus.GENERATING,
                format=format,
                data={},
                parameters_used=parameters or {}
            )

            try:
                # Collect data for each section
                report_data = {
                    "template": {
                        "name": template.name,
                        "description": template.description,
                        "type": template.report_type.value
                    },
                    "sections": [],
                    "generation_info": {
                        "generated_at": start_time.isoformat(),
                        "parameters": parameters or {},
                        "filters": filters or {}
                    }
                }

                for section in template.sections:
                    section_data = await self.collect_data_for_section(section, filters, parameters)
                    report_data["sections"].append({
                        "id": section.section_id,
                        "title": section.title,
                        "description": section.description,
                        "data": section_data
                    })

                # Format the report based on requested format
                formatted_data = await self._format_report_data(report_data, format)

                # Update report with results
                end_time = datetime.utcnow()
                report.data = formatted_data
                report.status = ReportStatus.COMPLETED
                report.generation_time_seconds = (end_time - start_time).total_seconds()
                report.expires_at = end_time + timedelta(days=30)  # Reports expire in 30 days

                # Store the generated report
                self.generated_reports[report_id] = report

                return report

            except Exception as e:
                report.status = ReportStatus.FAILED
                report.error_message = str(e)
                self.generated_reports[report_id] = report
                return report

        except Exception as e:
            print(f"Error generating report: {e}")
            return None

    async def _format_report_data(self, data: Dict[str, Any], format: ReportFormat) -> Any:
        """Format report data according to the requested format"""
        try:
            if format == ReportFormat.JSON:
                return data

            elif format == ReportFormat.CSV:
                return await self._format_as_csv(data)

            elif format == ReportFormat.HTML:
                return await self._format_as_html(data)

            elif format == ReportFormat.XML:
                return await self._format_as_xml(data)

            else:
                # Default to JSON for unsupported formats
                return data

        except Exception as e:
            print(f"Error formatting report data: {e}")
            return data

    async def _format_as_csv(self, data: Dict[str, Any]) -> str:
        """Format report data as CSV"""
        try:
            csv_output = []

            # Add header
            csv_output.append(f"Report: {data['template']['name']}")
            csv_output.append(f"Generated: {data['generation_info']['generated_at']}")
            csv_output.append("")

            # Add sections
            for section in data["sections"]:
                csv_output.append(f"Section: {section['title']}")

                if section["data"]["rows"]:
                    # Get column headers
                    headers = list(section["data"]["rows"][0].keys())
                    csv_output.append(",".join(headers))

                    # Add data rows
                    for row in section["data"]["rows"]:
                        csv_row = ",".join(str(row.get(header, "")) for header in headers)
                        csv_output.append(csv_row)

                csv_output.append("")

            return "\n".join(csv_output)

        except Exception as e:
            print(f"Error formatting as CSV: {e}")
            return str(data)

    async def _format_as_html(self, data: Dict[str, Any]) -> str:
        """Format report data as HTML"""
        try:
            html_parts = [
                "<!DOCTYPE html>",
                "<html><head><title>{}</title>".format(data["template"]["name"]),
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                "table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
                "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
                "th { background-color: #f2f2f2; }",
                ".section { margin: 20px 0; }",
                "</style></head><body>",
                f"<h1>{data['template']['name']}</h1>",
                f"<p>Generated: {data['generation_info']['generated_at']}</p>"
            ]

            for section in data["sections"]:
                html_parts.append(f'<div class="section">')
                html_parts.append(f"<h2>{section['title']}</h2>")

                if section["description"]:
                    html_parts.append(f"<p>{section['description']}</p>")

                if section["data"]["rows"]:
                    html_parts.append("<table>")

                    # Headers
                    headers = list(section["data"]["rows"][0].keys())
                    html_parts.append("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")

                    # Rows
                    for row in section["data"]["rows"]:
                        html_parts.append("<tr>" + "".join(f"<td>{row.get(h, '')}</td>" for h in headers) + "</tr>")

                    html_parts.append("</table>")

                html_parts.append("</div>")

            html_parts.extend(["</body></html>"])

            return "\n".join(html_parts)

        except Exception as e:
            print(f"Error formatting as HTML: {e}")
            return f"<html><body><h1>Error formatting report</h1><p>{e}</p></body></html>"

    async def _format_as_xml(self, data: Dict[str, Any]) -> str:
        """Format report data as XML"""
        try:
            root = ET.Element("report")
            root.set("name", data["template"]["name"])
            root.set("generated", data["generation_info"]["generated_at"])

            for section in data["sections"]:
                section_elem = ET.SubElement(root, "section")
                section_elem.set("id", section["id"])
                section_elem.set("title", section["title"])

                if section["data"]["rows"]:
                    data_elem = ET.SubElement(section_elem, "data")

                    for i, row in enumerate(section["data"]["rows"]):
                        row_elem = ET.SubElement(data_elem, "row")
                        row_elem.set("index", str(i))

                        for key, value in row.items():
                            field_elem = ET.SubElement(row_elem, "field")
                            field_elem.set("name", key)
                            field_elem.text = str(value)

            return ET.tostring(root, encoding='unicode')

        except Exception as e:
            print(f"Error formatting as XML: {e}")
            return f"<error>Error formatting report: {e}</error>"

    async def schedule_report(self, schedule: ReportSchedule) -> bool:
        """Schedule a report for automatic generation"""
        try:
            self.schedules[schedule.schedule_id] = schedule
            print(f"Scheduled report: {schedule.schedule_id}")
            return True
        except Exception as e:
            print(f"Error scheduling report: {e}")
            return False

    async def get_scheduled_reports(self) -> List[ReportSchedule]:
        """Get all scheduled reports"""
        return list(self.schedules.values())

    async def get_generated_reports(self, status: Optional[ReportStatus] = None) -> List[GeneratedReport]:
        """Get generated reports, optionally filtered by status"""
        try:
            reports = list(self.generated_reports.values())
            if status:
                reports = [r for r in reports if r.status == status]
            return sorted(reports, key=lambda x: x.generated_at, reverse=True)
        except Exception as e:
            print(f"Error getting generated reports: {e}")
            return []

    async def create_dashboard(self, dashboard: ReportDashboard) -> bool:
        """Create a new dashboard"""
        try:
            self.dashboards[dashboard.dashboard_id] = dashboard
            print(f"Created dashboard: {dashboard.name}")
            return True
        except Exception as e:
            print(f"Error creating dashboard: {e}")
            return False

    async def get_dashboards(self) -> List[ReportDashboard]:
        """Get all dashboards"""
        return list(self.dashboards.values())

    async def initialize_default_templates(self) -> bool:
        """Initialize default report templates"""
        try:
            # Executive Summary Template
            exec_template = ReportTemplate(
                template_id="exec_summary_001",
                name="Executive Summary",
                description="High-level business metrics and KPIs for executive leadership",
                report_type=ReportType.EXECUTIVE_SUMMARY,
                sections=[
                    ReportSection(
                        section_id="business_overview",
                        title="Business Overview",
                        description="Key business metrics and performance indicators",
                        columns=[
                            ReportColumn("mrr", "Monthly Recurring Revenue", DataSource.BUSINESS_ANALYTICS, "revenue.monthly_recurring_revenue", AggregationType.SUM, "${:,.2f}"),
                            ReportColumn("new_customers", "New Customers", DataSource.BUSINESS_ANALYTICS, "growth.new_customers", AggregationType.COUNT),
                            ReportColumn("churn_rate", "Churn Rate", DataSource.BUSINESS_ANALYTICS, "growth.churn_rate", AggregationType.PERCENTAGE, "{:.1f}%"),
                            ReportColumn("health_score", "System Health", DataSource.SYSTEM_METRICS, "health.overall_score", AggregationType.AVERAGE, "{:.1f}/100")
                        ]
                    )
                ]
            )

            # User Analytics Template
            user_template = ReportTemplate(
                template_id="user_analytics_001",
                name="User Analytics Report",
                description="Detailed user engagement and success metrics",
                report_type=ReportType.USER_ANALYTICS,
                sections=[
                    ReportSection(
                        section_id="user_engagement",
                        title="User Engagement Metrics",
                        description="User activity and engagement patterns",
                        columns=[
                            ReportColumn("user_id", "User ID", DataSource.USER_METRICS, "user_id"),
                            ReportColumn("sessions", "Total Sessions", DataSource.USER_METRICS, "engagement.sessions_count", AggregationType.SUM),
                            ReportColumn("avg_duration", "Avg Session Duration", DataSource.USER_METRICS, "engagement.session_duration_minutes", AggregationType.AVERAGE, "{:.1f} min"),
                            ReportColumn("time_saved", "Time Saved", DataSource.USER_METRICS, "success.time_saved_hours", AggregationType.SUM, "{:.1f} hrs"),
                            ReportColumn("cost_savings", "Cost Savings", DataSource.USER_METRICS, "success.cost_savings_amount", AggregationType.SUM, "${:,.2f}")
                        ]
                    )
                ]
            )

            # System Health Template
            system_template = ReportTemplate(
                template_id="system_health_001",
                name="System Health Report",
                description="System performance, security, and operational metrics",
                report_type=ReportType.SYSTEM_HEALTH,
                sections=[
                    ReportSection(
                        section_id="performance_metrics",
                        title="Performance Metrics",
                        description="System performance and resource utilization",
                        columns=[
                            ReportColumn("service", "Service", DataSource.SYSTEM_METRICS, "service"),
                            ReportColumn("response_time", "Response Time", DataSource.SYSTEM_METRICS, "performance.response_time_ms", AggregationType.AVERAGE, "{:.1f}ms"),
                            ReportColumn("throughput", "Throughput", DataSource.SYSTEM_METRICS, "performance.throughput_rps", AggregationType.AVERAGE, "{:.1f} req/s"),
                            ReportColumn("cpu_usage", "CPU Usage", DataSource.SYSTEM_METRICS, "resources.cpu_usage_percentage", AggregationType.AVERAGE, "{:.1f}%"),
                            ReportColumn("cost", "Infrastructure Cost", DataSource.SYSTEM_METRICS, "costs.total_cost", AggregationType.SUM, "${:,.2f}")
                        ]
                    )
                ]
            )

            # Store templates
            await self.create_report_template(exec_template)
            await self.create_report_template(user_template)
            await self.create_report_template(system_template)

            return True

        except Exception as e:
            print(f"Error initializing default templates: {e}")
            return False


# Global instance
custom_reports_engine = CustomReportsEngine()


# FastAPI endpoints configuration
async def get_reports_endpoints():
    """Return FastAPI endpoint configurations for custom reports"""
    return [
        {
            "path": "/analytics/reports/templates",
            "method": "GET",
            "handler": "get_report_templates",
            "description": "Get available report templates"
        },
        {
            "path": "/analytics/reports/templates",
            "method": "POST",
            "handler": "create_report_template",
            "description": "Create new report template"
        },
        {
            "path": "/analytics/reports/generate",
            "method": "POST",
            "handler": "generate_custom_report",
            "description": "Generate report from template"
        },
        {
            "path": "/analytics/reports/generated",
            "method": "GET",
            "handler": "get_generated_reports",
            "description": "Get list of generated reports"
        },
        {
            "path": "/analytics/reports/schedules",
            "method": "GET",
            "handler": "get_scheduled_reports",
            "description": "Get scheduled reports"
        },
        {
            "path": "/analytics/reports/schedules",
            "method": "POST",
            "handler": "schedule_report",
            "description": "Schedule a report for automatic generation"
        },
        {
            "path": "/analytics/reports/dashboards",
            "method": "GET",
            "handler": "get_report_dashboards",
            "description": "Get available dashboards"
        },
        {
            "path": "/analytics/reports/dashboards",
            "method": "POST",
            "handler": "create_report_dashboard",
            "description": "Create new dashboard"
        },
        {
            "path": "/analytics/reports/{report_id}/download",
            "method": "GET",
            "handler": "download_report",
            "description": "Download generated report file"
        },
        {
            "path": "/analytics/reports/{report_id}/share",
            "method": "POST",
            "handler": "share_report",
            "description": "Share report with users"
        }
    ]


async def initialize_reports_system():
    """Initialize the custom reports system"""
    try:
        # Initialize default templates
        await custom_reports_engine.initialize_default_templates()

        print("Custom Reports System initialized successfully")
        print(f"Available endpoints: {len(await get_reports_endpoints())}")
        print(f"Default templates created: {len(custom_reports_engine.templates)}")
        return True
    except Exception as e:
        print(f"Error initializing reports system: {e}")
        return False