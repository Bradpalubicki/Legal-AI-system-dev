"""
Reporting Engine

Advanced report generation with customizable templates, export formats,
and automated scheduling for legal billing analytics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, IO
from decimal import Decimal
import asyncio
import logging
import json
import io
import csv
from enum import Enum
from pathlib import Path
import jinja2
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from .financial_analytics import FinancialAnalytics, DateRange, ReportPeriod, FinancialReport
from .dashboard_generator import DashboardGenerator, DashboardFilter
from .advanced_models import BillingMatter, TimeEntry, Invoice, Payment
from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """Supported report export formats."""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportType(str, Enum):
    """Types of reports."""
    FINANCIAL_SUMMARY = "financial_summary"
    REVENUE_ANALYSIS = "revenue_analysis"
    COLLECTION_REPORT = "collection_report"
    TIME_UTILIZATION = "time_utilization"
    MATTER_PROFITABILITY = "matter_profitability"
    ATTORNEY_PERFORMANCE = "attorney_performance"
    AGING_REPORT = "aging_report"
    CASH_FLOW = "cash_flow"
    BUDGET_VARIANCE = "budget_variance"
    CUSTOM = "custom"


class ScheduleFrequency(str, Enum):
    """Report scheduling frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ReportTemplate(BaseModel):
    """Report template configuration."""
    id: str
    name: str
    description: Optional[str] = None
    report_type: ReportType
    template_path: str
    default_format: ReportFormat = ReportFormat.PDF
    parameters: Dict[str, Any] = Field(default_factory=dict)
    sections: List[str] = Field(default_factory=list)
    created_by: int
    is_public: bool = False


class ReportRequest(BaseModel):
    """Report generation request."""
    template_id: str
    title: str
    filters: DashboardFilter
    format: ReportFormat = ReportFormat.PDF
    parameters: Dict[str, Any] = Field(default_factory=dict)
    include_charts: bool = True
    include_raw_data: bool = False
    custom_sections: Optional[List[str]] = None


class ReportSchedule(BaseModel):
    """Automated report schedule."""
    id: str
    name: str
    template_id: str
    frequency: ScheduleFrequency
    filters: DashboardFilter
    format: ReportFormat
    recipients: List[str]
    next_run: datetime
    is_active: bool = True
    created_by: int


class GeneratedReport(BaseModel):
    """Generated report metadata."""
    id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    file_path: str
    file_size: int
    generation_time: float
    parameters: Dict[str, Any]
    created_at: datetime
    created_by: int


class ReportingEngine:
    """
    Advanced reporting engine with template support and automated scheduling.
    """
    
    def __init__(self):
        self.analytics = FinancialAnalytics()
        self.dashboard_generator = DashboardGenerator()
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates/reports'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        self.reports_directory = Path("reports/generated")
        self.reports_directory.mkdir(parents=True, exist_ok=True)
        
    async def generate_report(
        self,
        user_id: int,
        request: ReportRequest,
        db: Optional[AsyncSession] = None
    ) -> GeneratedReport:
        """Generate report based on request."""
        if not db:
            async with get_db_session() as db:
                return await self._generate_report_impl(user_id, request, db)
        return await self._generate_report_impl(user_id, request, db)
    
    async def _generate_report_impl(
        self,
        user_id: int,
        request: ReportRequest,
        db: AsyncSession
    ) -> GeneratedReport:
        """Implementation of report generation."""
        start_time = datetime.utcnow()
        
        # Get template
        template = await self._get_report_template(request.template_id)
        
        # Generate report data based on type
        report_data = await self._generate_report_data(
            template.report_type, request, db
        )
        
        # Render report content
        content = await self._render_report_content(
            template, report_data, request
        )
        
        # Export in requested format
        file_path, file_size = await self._export_report(
            content, request.format, request.title
        )
        
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create report record
        report = GeneratedReport(
            id=f"report_{user_id}_{int(start_time.timestamp())}",
            title=request.title,
            report_type=template.report_type,
            format=request.format,
            file_path=str(file_path),
            file_size=file_size,
            generation_time=generation_time,
            parameters=request.parameters,
            created_at=start_time,
            created_by=user_id
        )
        
        logger.info(f"Generated report: {report.title} in {generation_time:.2f}s")
        return report
    
    async def _generate_report_data(
        self,
        report_type: ReportType,
        request: ReportRequest,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate data for specific report type."""
        filter_dict = {
            'date_start': request.filters.date_range.start_date,
            'date_end': request.filters.date_range.end_date,
            'matter_ids': request.filters.matter_ids,
            'attorney_ids': request.filters.attorney_ids
        }
        
        if report_type == ReportType.FINANCIAL_SUMMARY:
            return await self._generate_financial_summary_data(request.filters, filter_dict, db)
        elif report_type == ReportType.REVENUE_ANALYSIS:
            return await self._generate_revenue_analysis_data(request.filters, filter_dict, db)
        elif report_type == ReportType.COLLECTION_REPORT:
            return await self._generate_collection_report_data(request.filters, filter_dict, db)
        elif report_type == ReportType.TIME_UTILIZATION:
            return await self._generate_time_utilization_data(request.filters, filter_dict, db)
        elif report_type == ReportType.MATTER_PROFITABILITY:
            return await self._generate_matter_profitability_data(request.filters, filter_dict, db)
        elif report_type == ReportType.ATTORNEY_PERFORMANCE:
            return await self._generate_attorney_performance_data(request.filters, filter_dict, db)
        elif report_type == ReportType.AGING_REPORT:
            return await self._generate_aging_report_data(request.filters, filter_dict, db)
        else:
            return await self._generate_financial_summary_data(request.filters, filter_dict, db)
    
    async def _generate_financial_summary_data(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate comprehensive financial summary data."""
        # Generate full financial report
        financial_report = await self.analytics.generate_financial_report(
            filters.date_range, filters.matter_ids, filters.attorney_ids, db
        )
        
        # Additional calculations for summary
        data = {
            'report_title': 'Financial Summary Report',
            'period': f"{filters.date_range.start_date.strftime('%B %d, %Y')} - {filters.date_range.end_date.strftime('%B %d, %Y')}",
            'generated_at': datetime.utcnow(),
            'financial_report': financial_report,
            
            # Key highlights
            'highlights': {
                'total_revenue': financial_report.revenue_metrics.total_revenue,
                'collection_rate': financial_report.collection_metrics.collection_rate,
                'profit_margin': financial_report.profitability_metrics.gross_profit_margin,
                'outstanding_ar': financial_report.collection_metrics.outstanding_ar,
                'billable_hours': financial_report.revenue_metrics.billable_hours,
                'utilization_rate': financial_report.revenue_metrics.utilization_rate
            },
            
            # Executive summary metrics
            'executive_summary': {
                'revenue_growth': financial_report.revenue_metrics.revenue_growth_rate,
                'top_performing_matter': financial_report.top_matters[0] if financial_report.top_matters else None,
                'total_matters': len(financial_report.top_matters),
                'total_attorneys': len(financial_report.attorney_performance),
                'cash_position': financial_report.cash_flow_metrics.trust_account_balance
            }
        }
        
        return data
    
    async def _generate_revenue_analysis_data(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate detailed revenue analysis data."""
        revenue_metrics = await self.analytics.get_revenue_metrics(filters.date_range, filter_dict, db)
        trends = await self.analytics.get_financial_trends(filters.date_range, filter_dict, db)
        
        # Revenue breakdown by source
        revenue_breakdown = {
            'time_entries': revenue_metrics.billable_revenue,
            'expenses': revenue_metrics.total_revenue - revenue_metrics.billable_revenue,
            'other': Decimal('0')  # Placeholder for other revenue sources
        }
        
        return {
            'report_title': 'Revenue Analysis Report',
            'period': f"{filters.date_range.start_date.strftime('%B %d, %Y')} - {filters.date_range.end_date.strftime('%B %d, %Y')}",
            'generated_at': datetime.utcnow(),
            'revenue_metrics': revenue_metrics,
            'revenue_trends': trends.get('revenue', []),
            'revenue_breakdown': revenue_breakdown,
            'realization_analysis': {
                'target_realization_rate': 90.0,
                'actual_realization_rate': revenue_metrics.realization_rate,
                'variance': revenue_metrics.realization_rate - 90.0
            }
        }
    
    async def _generate_collection_report_data(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate collection performance report data."""
        collection_metrics = await self.analytics.get_collection_metrics(filters.date_range, filter_dict, db)
        
        # Additional collection analysis
        return {
            'report_title': 'Collection Performance Report',
            'period': f"{filters.date_range.start_date.strftime('%B %d, %Y')} - {filters.date_range.end_date.strftime('%B %d, %Y')}",
            'generated_at': datetime.utcnow(),
            'collection_metrics': collection_metrics,
            'aged_ar_analysis': collection_metrics.aged_ar_breakdown,
            'collection_recommendations': await self._generate_collection_recommendations(collection_metrics)
        }
    
    async def _generate_time_utilization_data(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate time utilization report data."""
        revenue_metrics = await self.analytics.get_revenue_metrics(filters.date_range, filter_dict, db)
        attorney_performance = await self.analytics.get_attorney_performance(filters.date_range, filter_dict, db)
        
        # Calculate utilization statistics
        utilization_stats = {
            'average_utilization': revenue_metrics.utilization_rate,
            'target_utilization': 80.0,
            'attorneys_above_target': len([a for a in attorney_performance if a.utilization_rate > 80]),
            'attorneys_below_target': len([a for a in attorney_performance if a.utilization_rate <= 80]),
            'highest_utilization': max([a.utilization_rate for a in attorney_performance]) if attorney_performance else 0,
            'lowest_utilization': min([a.utilization_rate for a in attorney_performance]) if attorney_performance else 0
        }
        
        return {
            'report_title': 'Time Utilization Report',
            'period': f"{filters.date_range.start_date.strftime('%B %d, %Y')} - {filters.date_range.end_date.strftime('%B %d, %Y')}",
            'generated_at': datetime.utcnow(),
            'revenue_metrics': revenue_metrics,
            'attorney_performance': attorney_performance,
            'utilization_stats': utilization_stats,
            'recommendations': await self._generate_utilization_recommendations(utilization_stats, attorney_performance)
        }
    
    async def _generate_matter_profitability_data(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate matter profitability report data."""
        top_matters = await self.analytics.get_top_matters_performance(
            filters.date_range, filter_dict, 50, db
        )
        
        # Profitability analysis
        profitable_matters = [m for m in top_matters if m.profit_margin > 0]
        unprofitable_matters = [m for m in top_matters if m.profit_margin <= 0]
        
        profitability_summary = {
            'total_matters': len(top_matters),
            'profitable_matters': len(profitable_matters),
            'unprofitable_matters': len(unprofitable_matters),
            'average_margin': sum(m.profit_margin for m in top_matters) / len(top_matters) if top_matters else 0,
            'total_profit': sum(m.total_revenue - m.total_expenses for m in top_matters)
        }
        
        return {
            'report_title': 'Matter Profitability Report',
            'period': f"{filters.date_range.start_date.strftime('%B %d, %Y')} - {filters.date_range.end_date.strftime('%B %d, %Y')}",
            'generated_at': datetime.utcnow(),
            'matter_performance': top_matters,
            'profitability_summary': profitability_summary,
            'top_profitable': top_matters[:10],
            'least_profitable': sorted(top_matters, key=lambda x: x.profit_margin)[:10]
        }
    
    async def _generate_attorney_performance_data(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate attorney performance report data."""
        attorney_performance = await self.analytics.get_attorney_performance(filters.date_range, filter_dict, db)
        
        # Performance statistics
        performance_stats = {
            'total_attorneys': len(attorney_performance),
            'total_billable_hours': sum(a.billable_hours for a in attorney_performance),
            'total_revenue': sum(a.billable_revenue for a in attorney_performance),
            'average_rate': sum(a.average_hourly_rate for a in attorney_performance) / len(attorney_performance) if attorney_performance else 0,
            'top_performer': max(attorney_performance, key=lambda x: x.billable_revenue) if attorney_performance else None,
            'most_utilized': max(attorney_performance, key=lambda x: x.utilization_rate) if attorney_performance else None
        }
        
        return {
            'report_title': 'Attorney Performance Report',
            'period': f"{filters.date_range.start_date.strftime('%B %d, %Y')} - {filters.date_range.end_date.strftime('%B %d, %Y')}",
            'generated_at': datetime.utcnow(),
            'attorney_performance': attorney_performance,
            'performance_stats': performance_stats,
            'recommendations': await self._generate_attorney_recommendations(attorney_performance)
        }
    
    async def _generate_aging_report_data(
        self,
        filters: DashboardFilter,
        filter_dict: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate accounts receivable aging report data."""
        collection_metrics = await self.analytics.get_collection_metrics(filters.date_range, filter_dict, db)
        
        # Detailed aging analysis
        aging_analysis = {
            'total_ar': collection_metrics.outstanding_ar,
            'overdue_ar': collection_metrics.overdue_ar,
            'overdue_percentage': float(collection_metrics.overdue_ar / collection_metrics.outstanding_ar * 100) if collection_metrics.outstanding_ar > 0 else 0,
            'aged_breakdown': collection_metrics.aged_ar_breakdown,
            'collection_priority': []  # Would include specific invoices to prioritize
        }
        
        return {
            'report_title': 'Accounts Receivable Aging Report',
            'period': f"{filters.date_range.start_date.strftime('%B %d, %Y')} - {filters.date_range.end_date.strftime('%B %d, %Y')}",
            'generated_at': datetime.utcnow(),
            'collection_metrics': collection_metrics,
            'aging_analysis': aging_analysis,
            'action_items': await self._generate_collection_action_items(aging_analysis)
        }
    
    async def _render_report_content(
        self,
        template: ReportTemplate,
        data: Dict[str, Any],
        request: ReportRequest
    ) -> str:
        """Render report content using template."""
        try:
            template_obj = self.template_env.get_template(template.template_path)
            
            # Add common template variables
            template_data = {
                **data,
                'request': request,
                'template': template,
                'format_currency': self._format_currency,
                'format_percentage': self._format_percentage,
                'format_hours': self._format_hours
            }
            
            return template_obj.render(**template_data)
            
        except Exception as e:
            logger.error(f"Error rendering report template: {str(e)}")
            # Fallback to basic HTML
            return self._generate_fallback_html(data)
    
    async def _export_report(
        self,
        content: str,
        format: ReportFormat,
        title: str
    ) -> tuple[Path, int]:
        """Export report content in specified format."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}_{timestamp}"
        
        if format == ReportFormat.HTML:
            file_path = self.reports_directory / f"{filename}.html"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        elif format == ReportFormat.PDF:
            file_path = self.reports_directory / f"{filename}.pdf"
            # Would use library like weasyprint or reportlab
            # For now, save as HTML
            with open(file_path.with_suffix('.html'), 'w', encoding='utf-8') as f:
                f.write(content)
            file_path = file_path.with_suffix('.html')
            
        elif format == ReportFormat.CSV:
            file_path = self.reports_directory / f"{filename}.csv"
            await self._export_to_csv(content, file_path)
            
        elif format == ReportFormat.JSON:
            file_path = self.reports_directory / f"{filename}.json"
            # Extract data from content (would need proper data structure)
            with open(file_path, 'w') as f:
                json.dump({'content': content}, f, indent=2, default=str)
                
        else:  # Default to HTML
            file_path = self.reports_directory / f"{filename}.html"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        file_size = file_path.stat().st_size
        return file_path, file_size
    
    async def _export_to_csv(self, content: str, file_path: Path):
        """Export report data to CSV format."""
        # This would parse the HTML/data and convert to CSV
        # For now, create a simple placeholder
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Report Content'])
            writer.writerow([content[:100] + '...' if len(content) > 100 else content])
    
    def _generate_fallback_html(self, data: Dict[str, Any]) -> str:
        """Generate basic HTML fallback when template fails."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{data.get('report_title', 'Report')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
                .section {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{data.get('report_title', 'Report')}</h1>
                <p>Generated: {data.get('generated_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Period: {data.get('period', 'N/A')}</p>
            </div>
            
            <div class="section">
                <h2>Report Data</h2>
                <pre>{json.dumps(data, indent=2, default=str)}</pre>
            </div>
        </body>
        </html>
        """
        return html
    
    # Helper methods for report generation
    
    async def _generate_collection_recommendations(
        self,
        collection_metrics
    ) -> List[str]:
        """Generate collection improvement recommendations."""
        recommendations = []
        
        if collection_metrics.collection_rate < 85:
            recommendations.append("Collection rate is below industry average. Consider implementing automated payment reminders.")
            
        if collection_metrics.average_collection_days > 45:
            recommendations.append("Average collection time exceeds 45 days. Review payment terms and follow-up procedures.")
            
        if collection_metrics.overdue_ar > collection_metrics.total_invoiced * Decimal('0.15'):
            recommendations.append("Overdue accounts receivable is high. Prioritize collection efforts on aged accounts.")
            
        return recommendations
    
    async def _generate_utilization_recommendations(
        self,
        utilization_stats: Dict[str, Any],
        attorney_performance: List
    ) -> List[str]:
        """Generate utilization improvement recommendations."""
        recommendations = []
        
        if utilization_stats['average_utilization'] < 75:
            recommendations.append("Overall utilization is below target. Consider workload redistribution or additional business development.")
            
        low_utilization_count = len([a for a in attorney_performance if a.utilization_rate < 60])
        if low_utilization_count > 0:
            recommendations.append(f"{low_utilization_count} attorneys have utilization below 60%. Consider additional training or support.")
            
        return recommendations
    
    async def _generate_attorney_recommendations(
        self,
        attorney_performance: List
    ) -> List[str]:
        """Generate attorney performance recommendations."""
        recommendations = []
        
        # Identify top and bottom performers
        if attorney_performance:
            top_performer = max(attorney_performance, key=lambda x: x.billable_revenue)
            recommendations.append(f"Top performer: {top_performer.attorney_name} with ${top_performer.billable_revenue:,.2f} in revenue.")
            
            low_performers = [a for a in attorney_performance if a.utilization_rate < 60]
            if low_performers:
                recommendations.append(f"{len(low_performers)} attorneys need utilization improvement.")
                
        return recommendations
    
    async def _generate_collection_action_items(
        self,
        aging_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate specific collection action items."""
        action_items = []
        
        aged_ar = aging_analysis['aged_breakdown']
        
        if aged_ar.get('31-60 days', 0) > 0:
            action_items.append(f"Follow up on ${aged_ar['31-60 days']:,.2f} in 31-60 day receivables.")
            
        if aged_ar.get('Over 120 days', 0) > 0:
            action_items.append(f"Urgent collection required for ${aged_ar['Over 120 days']:,.2f} in 120+ day receivables.")
            
        return action_items
    
    async def _get_report_template(self, template_id: str) -> ReportTemplate:
        """Get report template by ID."""
        # This would typically query from database
        # For now, return default templates
        
        default_templates = {
            'financial_summary': ReportTemplate(
                id='financial_summary',
                name='Financial Summary',
                report_type=ReportType.FINANCIAL_SUMMARY,
                template_path='financial_summary.html',
                created_by=1
            ),
            'revenue_analysis': ReportTemplate(
                id='revenue_analysis',
                name='Revenue Analysis',
                report_type=ReportType.REVENUE_ANALYSIS,
                template_path='revenue_analysis.html',
                created_by=1
            )
        }
        
        return default_templates.get(template_id, default_templates['financial_summary'])
    
    # Template helper functions
    
    def _format_currency(self, value: Union[Decimal, float, int]) -> str:
        """Format currency values."""
        return f"${value:,.2f}"
    
    def _format_percentage(self, value: Union[Decimal, float, int]) -> str:
        """Format percentage values."""
        return f"{value:.1f}%"
    
    def _format_hours(self, value: Union[Decimal, float, int]) -> str:
        """Format hour values."""
        return f"{value:.1f} hrs"
    
    # Scheduling methods (would be implemented with background task system)
    
    async def schedule_report(
        self,
        user_id: int,
        schedule: ReportSchedule
    ) -> str:
        """Schedule automated report generation."""
        # This would integrate with task scheduler (Celery, etc.)
        logger.info(f"Scheduled report: {schedule.name} for user {user_id}")
        return schedule.id
    
    async def cancel_scheduled_report(self, schedule_id: str) -> bool:
        """Cancel scheduled report."""
        # This would cancel the scheduled task
        logger.info(f"Cancelled scheduled report: {schedule_id}")
        return True