"""
Financial Analytics Service

Advanced financial analytics and reporting for legal billing with
revenue analysis, profitability metrics, and predictive insights.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, Tuple
from decimal import Decimal
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc, asc, case, extract
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from .advanced_models import (
    TimeEntry, ExpenseEntry, Invoice, Payment, BillingMatter,
    BillingRate, TrustAccount, RecurringPayment, PaymentSchedule,
    PaymentStatus, InvoiceStatus, AuditLog
)
from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class ReportPeriod(str, Enum):
    """Supported reporting periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class MetricType(str, Enum):
    """Types of financial metrics."""
    REVENUE = "revenue"
    PROFIT = "profit"
    UTILIZATION = "utilization"
    COLLECTION = "collection"
    EXPENSE = "expense"
    CASH_FLOW = "cash_flow"


@dataclass
class DateRange:
    """Date range for analytics queries."""
    start_date: datetime
    end_date: datetime
    period: ReportPeriod = ReportPeriod.MONTHLY


class RevenueMetrics(BaseModel):
    """Revenue analytics metrics."""
    total_revenue: Decimal
    billable_revenue: Decimal
    non_billable_revenue: Decimal
    collected_revenue: Decimal
    outstanding_revenue: Decimal
    revenue_growth_rate: float
    average_hourly_rate: Decimal
    billable_hours: Decimal
    utilization_rate: float
    realization_rate: float


class ProfitabilityMetrics(BaseModel):
    """Profitability analytics metrics."""
    gross_profit: Decimal
    gross_profit_margin: float
    net_profit: Decimal
    net_profit_margin: float
    total_expenses: Decimal
    billable_expense_recovery: Decimal
    expense_recovery_rate: float
    profit_per_attorney: Decimal
    profit_per_matter: Decimal


class CollectionMetrics(BaseModel):
    """Collection performance metrics."""
    total_invoiced: Decimal
    total_collected: Decimal
    collection_rate: float
    average_collection_days: float
    outstanding_ar: Decimal
    overdue_ar: Decimal
    aged_ar_breakdown: Dict[str, Decimal]
    write_offs: Decimal
    bad_debt_rate: float


class CashFlowMetrics(BaseModel):
    """Cash flow analytics metrics."""
    cash_receipts: Decimal
    cash_disbursements: Decimal
    net_cash_flow: Decimal
    trust_account_balance: Decimal
    operating_account_balance: Decimal
    projected_cash_flow: List[Dict[str, Any]]
    cash_conversion_cycle: float


class MatterPerformance(BaseModel):
    """Individual matter performance metrics."""
    matter_id: int
    matter_name: str
    client_name: str
    total_revenue: Decimal
    total_expenses: Decimal
    profit_margin: float
    billable_hours: Decimal
    average_rate: Decimal
    collection_rate: float
    days_outstanding: float
    status: str


class AttorneyPerformance(BaseModel):
    """Individual attorney performance metrics."""
    attorney_id: int
    attorney_name: str
    billable_hours: Decimal
    billable_revenue: Decimal
    average_hourly_rate: Decimal
    utilization_rate: float
    collection_rate: float
    matters_count: int
    profit_contribution: Decimal


class TrendData(BaseModel):
    """Time series trend data."""
    period: str
    value: Decimal
    change_from_previous: Optional[float] = None
    change_from_previous_year: Optional[float] = None


class FinancialReport(BaseModel):
    """Comprehensive financial report."""
    report_date: datetime
    date_range: Dict[str, datetime]
    revenue_metrics: RevenueMetrics
    profitability_metrics: ProfitabilityMetrics
    collection_metrics: CollectionMetrics
    cash_flow_metrics: CashFlowMetrics
    top_matters: List[MatterPerformance]
    attorney_performance: List[AttorneyPerformance]
    trends: Dict[str, List[TrendData]]


class FinancialAnalytics:
    """
    Advanced financial analytics service with comprehensive reporting and insights.
    """
    
    def __init__(self):
        self.standard_billable_target = Decimal('1800')  # Annual billable hours target
        self.working_days_per_year = 250
        
    async def generate_financial_report(
        self,
        date_range: DateRange,
        matter_ids: Optional[List[int]] = None,
        attorney_ids: Optional[List[int]] = None,
        db: Optional[AsyncSession] = None
    ) -> FinancialReport:
        """Generate comprehensive financial report."""
        if not db:
            async with get_db_session() as db:
                return await self._generate_financial_report_impl(date_range, matter_ids, attorney_ids, db)
        return await self._generate_financial_report_impl(date_range, matter_ids, attorney_ids, db)
    
    async def _generate_financial_report_impl(
        self,
        date_range: DateRange,
        matter_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: AsyncSession
    ) -> FinancialReport:
        """Implementation of financial report generation."""
        # Build base filters
        filters = self._build_base_filters(date_range, matter_ids, attorney_ids)
        
        # Generate all metrics concurrently for performance
        revenue_task = self.get_revenue_metrics(date_range, filters, db)
        profitability_task = self.get_profitability_metrics(date_range, filters, db)
        collection_task = self.get_collection_metrics(date_range, filters, db)
        cash_flow_task = self.get_cash_flow_metrics(date_range, filters, db)
        matters_task = self.get_top_matters_performance(date_range, filters, 20, db)
        attorneys_task = self.get_attorney_performance(date_range, filters, db)
        trends_task = self.get_financial_trends(date_range, filters, db)
        
        # Await all results
        revenue_metrics, profitability_metrics, collection_metrics, cash_flow_metrics, \
        top_matters, attorney_performance, trends = await asyncio.gather(
            revenue_task, profitability_task, collection_task, cash_flow_task,
            matters_task, attorneys_task, trends_task
        )
        
        return FinancialReport(
            report_date=datetime.utcnow(),
            date_range={
                'start_date': date_range.start_date,
                'end_date': date_range.end_date
            },
            revenue_metrics=revenue_metrics,
            profitability_metrics=profitability_metrics,
            collection_metrics=collection_metrics,
            cash_flow_metrics=cash_flow_metrics,
            top_matters=top_matters,
            attorney_performance=attorney_performance,
            trends=trends
        )
    
    def _build_base_filters(
        self,
        date_range: DateRange,
        matter_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]]
    ) -> Dict[str, Any]:
        """Build base filters for queries."""
        filters = {
            'date_start': date_range.start_date,
            'date_end': date_range.end_date
        }
        
        if matter_ids:
            filters['matter_ids'] = matter_ids
        if attorney_ids:
            filters['attorney_ids'] = attorney_ids
            
        return filters
    
    async def get_revenue_metrics(
        self,
        date_range: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> RevenueMetrics:
        """Calculate comprehensive revenue metrics."""
        # Build time entry query conditions
        time_conditions = [
            TimeEntry.entry_date >= filters['date_start'],
            TimeEntry.entry_date <= filters['date_end']
        ]
        
        if filters.get('matter_ids'):
            time_conditions.append(TimeEntry.matter_id.in_(filters['matter_ids']))
        if filters.get('attorney_ids'):
            time_conditions.append(TimeEntry.timekeeper.in_(filters['attorney_ids']))
            
        # Revenue from time entries
        time_revenue_query = select(
            func.sum(TimeEntry.total_amount).label('total_revenue'),
            func.sum(case((TimeEntry.billable_minutes > 0, TimeEntry.total_amount), else_=0)).label('billable_revenue'),
            func.sum(case((TimeEntry.billable_minutes == 0, TimeEntry.total_amount), else_=0)).label('non_billable_revenue'),
            func.sum(TimeEntry.billable_minutes).label('total_billable_minutes'),
            func.avg(TimeEntry.hourly_rate).label('avg_hourly_rate'),
            func.count(TimeEntry.id).label('time_entries_count')
        ).where(and_(*time_conditions))
        
        time_result = await db.execute(time_revenue_query)
        time_row = time_result.first()
        
        # Revenue from expenses
        expense_conditions = [
            ExpenseEntry.expense_date >= filters['date_start'],
            ExpenseEntry.expense_date <= filters['date_end']
        ]
        
        if filters.get('matter_ids'):
            expense_conditions.append(ExpenseEntry.matter_id.in_(filters['matter_ids']))
            
        expense_revenue_query = select(
            func.sum(ExpenseEntry.billable_amount).label('expense_revenue')
        ).where(and_(*expense_conditions))
        
        expense_result = await db.execute(expense_revenue_query)
        expense_row = expense_result.first()
        
        # Collection metrics
        invoice_conditions = [
            Invoice.invoice_date >= filters['date_start'],
            Invoice.invoice_date <= filters['date_end']
        ]
        
        if filters.get('matter_ids'):
            invoice_conditions.append(Invoice.matter_id.in_(filters['matter_ids']))
            
        collection_query = select(
            func.sum(Invoice.total_amount).label('total_invoiced'),
            func.sum(Invoice.paid_amount).label('total_collected')
        ).where(and_(*invoice_conditions))
        
        collection_result = await db.execute(collection_query)
        collection_row = collection_result.first()
        
        # Calculate metrics
        total_time_revenue = time_row.total_revenue or Decimal('0')
        expense_revenue = expense_row.expense_revenue or Decimal('0')
        total_revenue = total_time_revenue + expense_revenue
        
        billable_revenue = time_row.billable_revenue or Decimal('0')
        non_billable_revenue = time_row.non_billable_revenue or Decimal('0')
        
        collected_revenue = collection_row.total_collected or Decimal('0')
        outstanding_revenue = (collection_row.total_invoiced or Decimal('0')) - collected_revenue
        
        # Calculate growth rate (compare with previous period)
        previous_period = DateRange(
            start_date=date_range.start_date - (date_range.end_date - date_range.start_date),
            end_date=date_range.start_date,
            period=date_range.period
        )
        previous_metrics = await self._get_previous_period_revenue(previous_period, filters, db)
        
        revenue_growth_rate = 0.0
        if previous_metrics > 0:
            revenue_growth_rate = float((total_revenue - previous_metrics) / previous_metrics * 100)
            
        # Utilization and realization rates
        billable_hours = Decimal(str((time_row.total_billable_minutes or 0) / 60))
        
        # Get total working hours for utilization calculation
        total_possible_hours = self._calculate_possible_hours(date_range, filters.get('attorney_ids'))
        utilization_rate = float(billable_hours / total_possible_hours * 100) if total_possible_hours > 0 else 0.0
        
        # Realization rate (collected vs billed)
        realization_rate = float(collected_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
        
        return RevenueMetrics(
            total_revenue=total_revenue,
            billable_revenue=billable_revenue,
            non_billable_revenue=non_billable_revenue,
            collected_revenue=collected_revenue,
            outstanding_revenue=outstanding_revenue,
            revenue_growth_rate=revenue_growth_rate,
            average_hourly_rate=time_row.avg_hourly_rate or Decimal('0'),
            billable_hours=billable_hours,
            utilization_rate=utilization_rate,
            realization_rate=realization_rate
        )
    
    async def get_profitability_metrics(
        self,
        date_range: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> ProfitabilityMetrics:
        """Calculate profitability metrics."""
        # Get revenue (reuse from revenue metrics)
        revenue_metrics = await self.get_revenue_metrics(date_range, filters, db)
        
        # Calculate expenses
        expense_conditions = [
            ExpenseEntry.expense_date >= filters['date_start'],
            ExpenseEntry.expense_date <= filters['date_end']
        ]
        
        if filters.get('matter_ids'):
            expense_conditions.append(ExpenseEntry.matter_id.in_(filters['matter_ids']))
            
        expense_query = select(
            func.sum(ExpenseEntry.amount).label('total_expenses'),
            func.sum(ExpenseEntry.billable_amount).label('billable_expenses'),
            func.sum(case(
                (ExpenseEntry.reimbursable == True, ExpenseEntry.amount),
                else_=0
            )).label('reimbursable_expenses')
        ).where(and_(*expense_conditions))
        
        expense_result = await db.execute(expense_query)
        expense_row = expense_result.first()
        
        total_expenses = expense_row.total_expenses or Decimal('0')
        billable_expense_recovery = expense_row.billable_expenses or Decimal('0')
        
        # Calculate profit metrics
        gross_profit = revenue_metrics.total_revenue - total_expenses
        gross_profit_margin = float(gross_profit / revenue_metrics.total_revenue * 100) if revenue_metrics.total_revenue > 0 else 0.0
        
        # For net profit, we'd need to account for overhead costs
        # For now, using gross profit as net profit
        net_profit = gross_profit
        net_profit_margin = gross_profit_margin
        
        # Expense recovery rate
        expense_recovery_rate = float(billable_expense_recovery / total_expenses * 100) if total_expenses > 0 else 0.0
        
        # Per attorney and per matter metrics
        attorney_count = await self._get_attorney_count(filters, db)
        matter_count = await self._get_matter_count(filters, db)
        
        profit_per_attorney = gross_profit / Decimal(str(attorney_count)) if attorney_count > 0 else Decimal('0')
        profit_per_matter = gross_profit / Decimal(str(matter_count)) if matter_count > 0 else Decimal('0')
        
        return ProfitabilityMetrics(
            gross_profit=gross_profit,
            gross_profit_margin=gross_profit_margin,
            net_profit=net_profit,
            net_profit_margin=net_profit_margin,
            total_expenses=total_expenses,
            billable_expense_recovery=billable_expense_recovery,
            expense_recovery_rate=expense_recovery_rate,
            profit_per_attorney=profit_per_attorney,
            profit_per_matter=profit_per_matter
        )
    
    async def get_collection_metrics(
        self,
        date_range: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> CollectionMetrics:
        """Calculate collection performance metrics."""
        # Base invoice conditions
        invoice_conditions = [
            Invoice.invoice_date >= filters['date_start'],
            Invoice.invoice_date <= filters['date_end']
        ]
        
        if filters.get('matter_ids'):
            invoice_conditions.append(Invoice.matter_id.in_(filters['matter_ids']))
            
        # Collection metrics query
        collection_query = select(
            func.sum(Invoice.total_amount).label('total_invoiced'),
            func.sum(Invoice.paid_amount).label('total_collected'),
            func.avg(
                func.extract('days', Invoice.paid_date - Invoice.invoice_date)
            ).label('avg_collection_days'),
            func.sum(
                case((Invoice.paid_amount < Invoice.total_amount, Invoice.total_amount - Invoice.paid_amount),
                     else_=0)
            ).label('outstanding_ar'),
            func.sum(
                case((and_(Invoice.due_date < datetime.utcnow(), Invoice.paid_amount < Invoice.total_amount),
                          Invoice.total_amount - Invoice.paid_amount),
                     else_=0)
            ).label('overdue_ar')
        ).where(and_(*invoice_conditions))
        
        result = await db.execute(collection_query)
        row = result.first()
        
        total_invoiced = row.total_invoiced or Decimal('0')
        total_collected = row.total_collected or Decimal('0')
        outstanding_ar = row.outstanding_ar or Decimal('0')
        overdue_ar = row.overdue_ar or Decimal('0')
        
        # Collection rate
        collection_rate = float(total_collected / total_invoiced * 100) if total_invoiced > 0 else 0.0
        
        # Average collection days
        avg_collection_days = float(row.avg_collection_days or 0)
        
        # Aged AR breakdown
        aged_ar_breakdown = await self._get_aged_ar_breakdown(filters, db)
        
        # Write-offs and bad debt (would need additional tracking)
        write_offs = Decimal('0')  # Placeholder - would need write-off tracking
        bad_debt_rate = 0.0  # Placeholder
        
        return CollectionMetrics(
            total_invoiced=total_invoiced,
            total_collected=total_collected,
            collection_rate=collection_rate,
            average_collection_days=avg_collection_days,
            outstanding_ar=outstanding_ar,
            overdue_ar=overdue_ar,
            aged_ar_breakdown=aged_ar_breakdown,
            write_offs=write_offs,
            bad_debt_rate=bad_debt_rate
        )
    
    async def get_cash_flow_metrics(
        self,
        date_range: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> CashFlowMetrics:
        """Calculate cash flow metrics."""
        # Cash receipts (payments received)
        payment_conditions = [
            Payment.payment_date >= filters['date_start'],
            Payment.payment_date <= filters['date_end'],
            Payment.status == PaymentStatus.COMPLETED
        ]
        
        if filters.get('matter_ids'):
            payment_conditions.append(Payment.matter_id.in_(filters['matter_ids']))
            
        receipts_query = select(
            func.sum(case((Payment.amount > 0, Payment.amount), else_=0)).label('cash_receipts'),
            func.sum(case((Payment.amount < 0, func.abs(Payment.amount)), else_=0)).label('refunds')
        ).where(and_(*payment_conditions))
        
        receipts_result = await db.execute(receipts_query)
        receipts_row = receipts_result.first()
        
        cash_receipts = receipts_row.cash_receipts or Decimal('0')
        refunds = receipts_row.refunds or Decimal('0')
        net_receipts = cash_receipts - refunds
        
        # Cash disbursements (expenses paid)
        disbursements_query = select(
            func.sum(ExpenseEntry.amount).label('cash_disbursements')
        ).where(
            and_(
                ExpenseEntry.expense_date >= filters['date_start'],
                ExpenseEntry.expense_date <= filters['date_end']
            )
        )
        
        if filters.get('matter_ids'):
            disbursements_query = disbursements_query.where(
                ExpenseEntry.matter_id.in_(filters['matter_ids'])
            )
            
        disbursements_result = await db.execute(disbursements_query)
        cash_disbursements = disbursements_result.scalar() or Decimal('0')
        
        # Net cash flow
        net_cash_flow = net_receipts - cash_disbursements
        
        # Account balances
        trust_balance = await self._get_trust_account_balance(filters, db)
        operating_balance = Decimal('0')  # Would need operating account tracking
        
        # Projected cash flow
        projected_cash_flow = await self._get_projected_cash_flow(filters, db)
        
        # Cash conversion cycle (placeholder - needs detailed implementation)
        cash_conversion_cycle = 45.0  # Days - placeholder
        
        return CashFlowMetrics(
            cash_receipts=net_receipts,
            cash_disbursements=cash_disbursements,
            net_cash_flow=net_cash_flow,
            trust_account_balance=trust_balance,
            operating_account_balance=operating_balance,
            projected_cash_flow=projected_cash_flow,
            cash_conversion_cycle=cash_conversion_cycle
        )
    
    async def get_top_matters_performance(
        self,
        date_range: DateRange,
        filters: Dict[str, Any],
        limit: int,
        db: AsyncSession
    ) -> List[MatterPerformance]:
        """Get top performing matters by revenue."""
        # Build matter performance query
        matter_conditions = []
        
        if filters.get('matter_ids'):
            matter_conditions.append(BillingMatter.id.in_(filters['matter_ids']))
            
        # Subquery for time entry revenue
        time_revenue_subquery = select(
            TimeEntry.matter_id,
            func.sum(TimeEntry.total_amount).label('time_revenue'),
            func.sum(TimeEntry.billable_minutes).label('billable_minutes'),
            func.avg(TimeEntry.hourly_rate).label('avg_rate')
        ).where(
            and_(
                TimeEntry.entry_date >= filters['date_start'],
                TimeEntry.entry_date <= filters['date_end']
            )
        ).group_by(TimeEntry.matter_id).subquery()
        
        # Subquery for expense revenue
        expense_subquery = select(
            ExpenseEntry.matter_id,
            func.sum(ExpenseEntry.billable_amount).label('expense_revenue')
        ).where(
            and_(
                ExpenseEntry.expense_date >= filters['date_start'],
                ExpenseEntry.expense_date <= filters['date_end']
            )
        ).group_by(ExpenseEntry.matter_id).subquery()
        
        # Subquery for collections
        collection_subquery = select(
            Invoice.matter_id,
            func.sum(Invoice.total_amount).label('total_invoiced'),
            func.sum(Invoice.paid_amount).label('total_collected'),
            func.avg(
                func.extract('days', func.coalesce(Invoice.paid_date, datetime.utcnow()) - Invoice.invoice_date)
            ).label('avg_days_outstanding')
        ).where(
            and_(
                Invoice.invoice_date >= filters['date_start'],
                Invoice.invoice_date <= filters['date_end']
            )
        ).group_by(Invoice.matter_id).subquery()
        
        # Main query
        query = select(
            BillingMatter.id,
            BillingMatter.matter_name,
            BillingMatter.client_name,
            BillingMatter.status,
            func.coalesce(time_revenue_subquery.c.time_revenue, 0).label('time_revenue'),
            func.coalesce(expense_subquery.c.expense_revenue, 0).label('expense_revenue'),
            func.coalesce(time_revenue_subquery.c.billable_minutes, 0).label('billable_minutes'),
            func.coalesce(time_revenue_subquery.c.avg_rate, 0).label('avg_rate'),
            func.coalesce(collection_subquery.c.total_invoiced, 0).label('total_invoiced'),
            func.coalesce(collection_subquery.c.total_collected, 0).label('total_collected'),
            func.coalesce(collection_subquery.c.avg_days_outstanding, 0).label('avg_days_outstanding')
        ).select_from(
            BillingMatter
            .outerjoin(time_revenue_subquery, BillingMatter.id == time_revenue_subquery.c.matter_id)
            .outerjoin(expense_subquery, BillingMatter.id == expense_subquery.c.matter_id)
            .outerjoin(collection_subquery, BillingMatter.id == collection_subquery.c.matter_id)
        )
        
        if matter_conditions:
            query = query.where(and_(*matter_conditions))
            
        query = query.order_by(
            desc(func.coalesce(time_revenue_subquery.c.time_revenue, 0) + 
                 func.coalesce(expense_subquery.c.expense_revenue, 0))
        ).limit(limit)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        performances = []
        for row in rows:
            total_revenue = Decimal(str(row.time_revenue)) + Decimal(str(row.expense_revenue))
            total_expenses = Decimal('0')  # Would need expense tracking by matter
            
            # Calculate collection rate
            collection_rate = float(row.total_collected / row.total_invoiced * 100) if row.total_invoiced > 0 else 0.0
            
            # Calculate profit margin (simplified)
            profit_margin = 100.0 if total_revenue > 0 else 0.0  # Placeholder without expense tracking
            
            performances.append(MatterPerformance(
                matter_id=row.id,
                matter_name=row.matter_name,
                client_name=row.client_name,
                total_revenue=total_revenue,
                total_expenses=total_expenses,
                profit_margin=profit_margin,
                billable_hours=Decimal(str(row.billable_minutes / 60)),
                average_rate=Decimal(str(row.avg_rate or 0)),
                collection_rate=collection_rate,
                days_outstanding=float(row.avg_days_outstanding or 0),
                status=row.status
            ))
            
        return performances
    
    async def get_attorney_performance(
        self,
        date_range: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> List[AttorneyPerformance]:
        """Get attorney performance metrics."""
        # Attorney performance query
        attorney_conditions = [
            TimeEntry.entry_date >= filters['date_start'],
            TimeEntry.entry_date <= filters['date_end']
        ]
        
        if filters.get('attorney_ids'):
            attorney_conditions.append(TimeEntry.timekeeper.in_(filters['attorney_ids']))
        if filters.get('matter_ids'):
            attorney_conditions.append(TimeEntry.matter_id.in_(filters['matter_ids']))
            
        query = select(
            TimeEntry.timekeeper,
            func.sum(TimeEntry.billable_minutes).label('billable_minutes'),
            func.sum(TimeEntry.total_amount).label('billable_revenue'),
            func.avg(TimeEntry.hourly_rate).label('avg_hourly_rate'),
            func.count(func.distinct(TimeEntry.matter_id)).label('matters_count')
        ).where(and_(*attorney_conditions)).group_by(TimeEntry.timekeeper)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        performances = []
        for row in rows:
            billable_hours = Decimal(str(row.billable_minutes / 60))
            
            # Calculate utilization rate
            possible_hours = self._calculate_possible_hours(date_range, [row.timekeeper])
            utilization_rate = float(billable_hours / possible_hours * 100) if possible_hours > 0 else 0.0
            
            # Get collection rate for this attorney
            collection_rate = await self._get_attorney_collection_rate(
                row.timekeeper, date_range, filters, db
            )
            
            # Profit contribution (simplified)
            profit_contribution = Decimal(str(row.billable_revenue))  # Placeholder
            
            performances.append(AttorneyPerformance(
                attorney_id=row.timekeeper,
                attorney_name=f"Attorney {row.timekeeper}",  # Would need user name lookup
                billable_hours=billable_hours,
                billable_revenue=Decimal(str(row.billable_revenue)),
                average_hourly_rate=Decimal(str(row.avg_hourly_rate or 0)),
                utilization_rate=utilization_rate,
                collection_rate=collection_rate,
                matters_count=row.matters_count,
                profit_contribution=profit_contribution
            ))
            
        return sorted(performances, key=lambda x: x.billable_revenue, reverse=True)
    
    async def get_financial_trends(
        self,
        date_range: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, List[TrendData]]:
        """Get financial trends over time."""
        trends = {}
        
        # Generate period breakdowns
        periods = self._generate_periods(date_range)
        
        # Revenue trend
        revenue_trend = []
        previous_revenue = None
        
        for period_start, period_end, period_label in periods:
            period_range = DateRange(period_start, period_end, date_range.period)
            revenue_metrics = await self.get_revenue_metrics(period_range, filters, db)
            
            change_from_previous = None
            if previous_revenue is not None and previous_revenue > 0:
                change_from_previous = float((revenue_metrics.total_revenue - previous_revenue) / previous_revenue * 100)
                
            revenue_trend.append(TrendData(
                period=period_label,
                value=revenue_metrics.total_revenue,
                change_from_previous=change_from_previous
            ))
            
            previous_revenue = revenue_metrics.total_revenue
            
        trends['revenue'] = revenue_trend
        
        # Collection trend
        collection_trend = []
        previous_collection = None
        
        for period_start, period_end, period_label in periods:
            period_range = DateRange(period_start, period_end, date_range.period)
            collection_metrics = await self.get_collection_metrics(period_range, filters, db)
            
            change_from_previous = None
            if previous_collection is not None and previous_collection > 0:
                change_from_previous = float((collection_metrics.total_collected - previous_collection) / previous_collection * 100)
                
            collection_trend.append(TrendData(
                period=period_label,
                value=collection_metrics.total_collected,
                change_from_previous=change_from_previous
            ))
            
            previous_collection = collection_metrics.total_collected
            
        trends['collection'] = collection_trend
        
        return trends
    
    # Helper methods
    
    async def _get_previous_period_revenue(
        self,
        previous_period: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> Decimal:
        """Get revenue for previous period for growth calculation."""
        try:
            metrics = await self.get_revenue_metrics(previous_period, filters, db)
            return metrics.total_revenue
        except:
            return Decimal('0')
    
    def _calculate_possible_hours(
        self,
        date_range: DateRange,
        attorney_ids: Optional[List[int]] = None
    ) -> Decimal:
        """Calculate possible billable hours for the period."""
        days_in_period = (date_range.end_date - date_range.start_date).days + 1
        working_days = min(days_in_period, days_in_period * 5 / 7)  # Assume 5-day work week
        
        hours_per_day = 8  # Standard work day
        attorney_count = len(attorney_ids) if attorney_ids else 1
        
        total_possible_hours = working_days * hours_per_day * attorney_count
        return Decimal(str(total_possible_hours))
    
    async def _get_attorney_count(
        self,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> int:
        """Get count of attorneys in the analysis."""
        if filters.get('attorney_ids'):
            return len(filters['attorney_ids'])
            
        # Get unique attorneys who worked in the period
        query = select(func.count(func.distinct(TimeEntry.timekeeper))).where(
            and_(
                TimeEntry.entry_date >= filters['date_start'],
                TimeEntry.entry_date <= filters['date_end']
            )
        )
        
        result = await db.execute(query)
        return result.scalar() or 1
    
    async def _get_matter_count(
        self,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> int:
        """Get count of matters in the analysis."""
        if filters.get('matter_ids'):
            return len(filters['matter_ids'])
            
        # Get unique matters with activity in the period
        query = select(func.count(func.distinct(TimeEntry.matter_id))).where(
            and_(
                TimeEntry.entry_date >= filters['date_start'],
                TimeEntry.entry_date <= filters['date_end']
            )
        )
        
        result = await db.execute(query)
        return result.scalar() or 1
    
    async def _get_aged_ar_breakdown(
        self,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Decimal]:
        """Get aged accounts receivable breakdown."""
        current_date = datetime.utcnow()
        
        # Define aging buckets
        buckets = {
            '0-30 days': (0, 30),
            '31-60 days': (31, 60),
            '61-90 days': (61, 90),
            '91-120 days': (91, 120),
            'Over 120 days': (121, 9999)
        }
        
        breakdown = {}
        
        for bucket_name, (min_days, max_days) in buckets.items():
            query = select(
                func.sum(Invoice.total_amount - Invoice.paid_amount).label('outstanding')
            ).where(
                and_(
                    Invoice.paid_amount < Invoice.total_amount,
                    func.extract('days', current_date - Invoice.invoice_date) >= min_days,
                    func.extract('days', current_date - Invoice.invoice_date) <= max_days
                )
            )
            
            if filters.get('matter_ids'):
                query = query.where(Invoice.matter_id.in_(filters['matter_ids']))
                
            result = await db.execute(query)
            breakdown[bucket_name] = result.scalar() or Decimal('0')
            
        return breakdown
    
    async def _get_trust_account_balance(
        self,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> Decimal:
        """Get total trust account balance."""
        query = select(
            func.sum(TrustAccount.available_balance).label('total_balance')
        ).where(TrustAccount.is_active == True)
        
        if filters.get('matter_ids'):
            query = query.where(TrustAccount.matter_id.in_(filters['matter_ids']))
            
        result = await db.execute(query)
        return result.scalar() or Decimal('0')
    
    async def _get_projected_cash_flow(
        self,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get projected cash flow for next periods."""
        # Simple projection based on recurring payments
        projections = []
        
        # Get active recurring payments
        query = select(RecurringPayment).where(
            and_(
                RecurringPayment.status == 'active',
                RecurringPayment.next_payment_date.isnot(None)
            )
        )
        
        if filters.get('matter_ids'):
            query = query.where(RecurringPayment.matter_id.in_(filters['matter_ids']))
            
        result = await db.execute(query)
        recurring_payments = result.scalars().all()
        
        # Project next 12 months
        current_date = datetime.utcnow()
        for month in range(12):
            month_start = current_date.replace(day=1) + relativedelta(months=month)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)
            
            projected_amount = Decimal('0')
            
            for payment in recurring_payments:
                # Simple projection - would need more sophisticated logic
                if payment.next_payment_date and month_start <= payment.next_payment_date <= month_end:
                    projected_amount += payment.amount
                    
            projections.append({
                'period': month_start.strftime('%Y-%m'),
                'projected_inflow': projected_amount,
                'projected_outflow': Decimal('0'),  # Would need expense projections
                'net_projection': projected_amount
            })
            
        return projections
    
    async def _get_attorney_collection_rate(
        self,
        attorney_id: int,
        date_range: DateRange,
        filters: Dict[str, Any],
        db: AsyncSession
    ) -> float:
        """Get collection rate for specific attorney."""
        # Get invoices for matters where this attorney worked
        attorney_matters_query = select(func.distinct(TimeEntry.matter_id)).where(
            and_(
                TimeEntry.timekeeper == attorney_id,
                TimeEntry.entry_date >= date_range.start_date,
                TimeEntry.entry_date <= date_range.end_date
            )
        )
        
        attorney_matters_result = await db.execute(attorney_matters_query)
        matter_ids = [row[0] for row in attorney_matters_result.fetchall()]
        
        if not matter_ids:
            return 0.0
            
        # Get collection rate for these matters
        collection_query = select(
            func.sum(Invoice.total_amount).label('total_invoiced'),
            func.sum(Invoice.paid_amount).label('total_collected')
        ).where(
            and_(
                Invoice.matter_id.in_(matter_ids),
                Invoice.invoice_date >= date_range.start_date,
                Invoice.invoice_date <= date_range.end_date
            )
        )
        
        result = await db.execute(collection_query)
        row = result.first()
        
        if row.total_invoiced and row.total_invoiced > 0:
            return float((row.total_collected or 0) / row.total_invoiced * 100)
        return 0.0
    
    def _generate_periods(
        self,
        date_range: DateRange
    ) -> List[Tuple[datetime, datetime, str]]:
        """Generate period breakdowns for trend analysis."""
        periods = []
        
        if date_range.period == ReportPeriod.MONTHLY:
            current = date_range.start_date.replace(day=1)
            while current <= date_range.end_date:
                period_end = current + relativedelta(months=1) - timedelta(days=1)
                period_end = min(period_end, date_range.end_date)
                
                periods.append((
                    current,
                    period_end,
                    current.strftime('%Y-%m')
                ))
                
                current = current + relativedelta(months=1)
                
        elif date_range.period == ReportPeriod.QUARTERLY:
            current = date_range.start_date.replace(month=((date_range.start_date.month-1)//3)*3+1, day=1)
            while current <= date_range.end_date:
                period_end = current + relativedelta(months=3) - timedelta(days=1)
                period_end = min(period_end, date_range.end_date)
                
                quarters = ['Q1', 'Q2', 'Q3', 'Q4']
                quarter = quarters[(current.month-1)//3]
                
                periods.append((
                    current,
                    period_end,
                    f"{current.year}-{quarter}"
                ))
                
                current = current + relativedelta(months=3)
                
        else:  # Default to monthly
            return self._generate_periods(
                DateRange(date_range.start_date, date_range.end_date, ReportPeriod.MONTHLY)
            )
            
        return periods