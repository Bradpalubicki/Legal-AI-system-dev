"""
Billing API Endpoints

FastAPI endpoints for the comprehensive legal billing system with
financial analytics, payment processing, and reporting capabilities.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from . import (
    # Core Services
    TimeTracker, TimesheetManager, ExpenseManager, InvoiceGenerator,
    PaymentProcessor, PaymentMethodManager, RecurringPaymentManager,
    
    # Analytics & Reporting
    FinancialAnalytics, DashboardGenerator, ReportingEngine,
    
    # Models
    TimeEntryRequest, ExpenseRequest, InvoiceRequest, PaymentRequest,
    PaymentMethodCreate, RecurringPaymentCreate, DateRange, ReportPeriod,
    DashboardFilter, ReportRequest, ReportFormat, ReportType,
    
    # Response Models
    TimesheetSummary, ExpenseSummary, InvoicePreview, PaymentResult,
    FinancialReport, DashboardLayout, GeneratedReport
)
from ..core.database import get_db_session
from ..core.security import get_current_user_id, require_permissions


logger = logging.getLogger(__name__)

# Create router
billing_router = APIRouter(prefix="/api/billing", tags=["billing"])

# Initialize services
time_tracker = TimeTracker()
timesheet_manager = TimesheetManager()
expense_manager = ExpenseManager()
invoice_generator = InvoiceGenerator()
payment_processor = PaymentProcessor()
payment_method_manager = PaymentMethodManager()
recurring_payment_manager = RecurringPaymentManager()
financial_analytics = FinancialAnalytics()
dashboard_generator = DashboardGenerator()
reporting_engine = ReportingEngine()


# ============================================================================
# TIME TRACKING ENDPOINTS
# ============================================================================

@billing_router.post("/time/start-timer")
async def start_timer(
    matter_id: int,
    activity_description: str,
    activity_code: Optional[str] = None,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Start a new timer for time tracking."""
    try:
        result = await time_tracker.start_timer(
            current_user, matter_id, activity_description, activity_code, db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/time/stop-timer")
async def stop_timer(
    create_entry: bool = True,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Stop active timer and optionally create time entry."""
    try:
        result = await time_tracker.stop_timer(current_user, create_entry, db)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/time/active-timer")
async def get_active_timer(
    current_user: int = Depends(get_current_user_id)
):
    """Get active timer for current user."""
    timer_data = await time_tracker.get_active_timer(current_user)
    return {"success": True, "data": timer_data}


@billing_router.post("/time/entries")
async def create_time_entry(
    entry_request: TimeEntryRequest,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new time entry."""
    try:
        time_entry = await time_tracker.create_time_entry(current_user, entry_request, db)
        return {"success": True, "data": {"id": time_entry.id, "entry_id": time_entry.entry_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/time/summary")
async def get_timesheet_summary(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> TimesheetSummary:
    """Get timesheet summary for date range."""
    try:
        summary = await time_tracker.get_timesheet_summary(
            current_user, start_date, end_date, db
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# EXPENSE MANAGEMENT ENDPOINTS
# ============================================================================

@billing_router.post("/expenses")
async def create_expense(
    expense_request: ExpenseRequest,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new expense entry."""
    try:
        expense = await expense_manager.create_expense(current_user, expense_request, db=db)
        return {"success": True, "data": {"id": expense.id, "expense_id": expense.expense_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/expenses/{expense_id}/submit")
async def submit_expense(
    expense_id: int,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Submit expense for approval."""
    try:
        expense = await expense_manager.submit_expense(expense_id, current_user, db)
        return {"success": True, "data": {"status": expense.expense_status}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/expenses/{expense_id}/approve")
@require_permissions(["approve_expenses"])
async def approve_expense(
    expense_id: int,
    approved_amount: Optional[Decimal] = None,
    notes: Optional[str] = None,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve expense entry."""
    try:
        expense = await expense_manager.approve_expense(
            expense_id, current_user, approved_amount, notes, db
        )
        return {"success": True, "data": {"status": expense.approval_status}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/expenses/summary")
async def get_expense_summary(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    matter_id: Optional[int] = Query(None),
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> ExpenseSummary:
    """Get expense summary for date range."""
    try:
        summary = await expense_manager.get_expense_summary(
            current_user, start_date, end_date, matter_id, db
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# INVOICE MANAGEMENT ENDPOINTS
# ============================================================================

@billing_router.post("/invoices/preview")
async def preview_invoice(
    invoice_request: InvoiceRequest,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> InvoicePreview:
    """Preview invoice before generation."""
    try:
        preview = await invoice_generator.preview_invoice(invoice_request, db)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/invoices")
async def generate_invoice(
    invoice_request: InvoiceRequest,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a new invoice."""
    try:
        invoice = await invoice_generator.generate_invoice(current_user, invoice_request, db)
        return {"success": True, "data": {"id": invoice.id, "invoice_number": invoice.invoice_number}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/invoices/{invoice_id}/finalize")
async def finalize_invoice(
    invoice_id: int,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Finalize invoice for sending."""
    try:
        invoice = await invoice_generator.finalize_invoice(invoice_id, current_user, db)
        return {"success": True, "data": {"status": invoice.status}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/invoices/summary")
async def get_invoice_summary(
    matter_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get invoice summary statistics."""
    try:
        summary = await invoice_generator.get_invoice_summary(matter_id, start_date, end_date, db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PAYMENT PROCESSING ENDPOINTS
# ============================================================================

@billing_router.post("/payments/process")
async def process_payment(
    payment_request: PaymentRequest,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> PaymentResult:
    """Process a payment."""
    try:
        result = await payment_processor.process_payment(current_user, payment_request, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/payments/{payment_id}/refund")
async def process_refund(
    payment_id: int,
    refund_amount: Optional[Decimal] = None,
    reason: str = "Refund requested",
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Process payment refund."""
    try:
        from .payment_processor import RefundRequest
        refund_request = RefundRequest(
            payment_id=payment_id,
            refund_amount=refund_amount,
            reason=reason
        )
        result = await payment_processor.process_refund(current_user, refund_request, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PAYMENT METHODS ENDPOINTS
# ============================================================================

@billing_router.post("/payment-methods")
async def create_payment_method(
    matter_id: int,
    method_data: PaymentMethodCreate,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Create new payment method."""
    try:
        payment_method = await payment_method_manager.create_payment_method(
            current_user, matter_id, method_data, db
        )
        return {"success": True, "data": payment_method}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/payment-methods")
async def get_payment_methods(
    matter_id: Optional[int] = Query(None),
    include_inactive: bool = Query(False),
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's payment methods."""
    try:
        payment_methods = await payment_method_manager.get_payment_methods(
            current_user, matter_id, include_inactive, db
        )
        return {"success": True, "data": payment_methods}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: int,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete payment method."""
    try:
        success = await payment_method_manager.delete_payment_method(
            payment_method_id, current_user, db
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RECURRING PAYMENTS ENDPOINTS
# ============================================================================

@billing_router.post("/recurring-payments")
async def create_recurring_payment(
    recurring_data: RecurringPaymentCreate,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Create new recurring payment schedule."""
    try:
        recurring_payment = await recurring_payment_manager.create_recurring_payment(
            current_user, recurring_data, db
        )
        return {"success": True, "data": recurring_payment}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/recurring-payments/{recurring_payment_id}")
async def get_recurring_payment(
    recurring_payment_id: int,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get recurring payment details."""
    try:
        recurring_payment = await recurring_payment_manager.get_recurring_payment(
            recurring_payment_id, current_user, db
        )
        return {"success": True, "data": recurring_payment}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/recurring-payments/{recurring_payment_id}/cancel")
async def cancel_recurring_payment(
    recurring_payment_id: int,
    reason: str = "Cancelled by user",
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Cancel recurring payment."""
    try:
        success = await recurring_payment_manager.cancel_recurring_payment(
            recurring_payment_id, current_user, reason, db
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# FINANCIAL ANALYTICS ENDPOINTS
# ============================================================================

@billing_router.post("/analytics/financial-report")
async def generate_financial_report(
    date_range: DateRange,
    matter_ids: Optional[List[int]] = None,
    attorney_ids: Optional[List[int]] = None,
    db: AsyncSession = Depends(get_db_session)
) -> FinancialReport:
    """Generate comprehensive financial report."""
    try:
        report = await financial_analytics.generate_financial_report(
            date_range, matter_ids, attorney_ids, db
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/analytics/revenue-metrics")
async def get_revenue_metrics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    period: ReportPeriod = Query(ReportPeriod.MONTHLY),
    matter_ids: Optional[List[int]] = Query(None),
    attorney_ids: Optional[List[int]] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get revenue metrics for specified period."""
    try:
        date_range = DateRange(start_date=start_date, end_date=end_date, period=period)
        filters = {
            'date_start': start_date,
            'date_end': end_date,
            'matter_ids': matter_ids,
            'attorney_ids': attorney_ids
        }
        
        revenue_metrics = await financial_analytics.get_revenue_metrics(date_range, filters, db)
        return {"success": True, "data": revenue_metrics}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/analytics/collection-metrics")
async def get_collection_metrics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    period: ReportPeriod = Query(ReportPeriod.MONTHLY),
    matter_ids: Optional[List[int]] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get collection performance metrics."""
    try:
        date_range = DateRange(start_date=start_date, end_date=end_date, period=period)
        filters = {
            'date_start': start_date,
            'date_end': end_date,
            'matter_ids': matter_ids
        }
        
        collection_metrics = await financial_analytics.get_collection_metrics(date_range, filters, db)
        return {"success": True, "data": collection_metrics}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@billing_router.post("/dashboard/executive")
async def generate_executive_dashboard(
    filters: DashboardFilter,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> DashboardLayout:
    """Generate executive dashboard."""
    try:
        dashboard = await dashboard_generator.generate_executive_dashboard(
            current_user, filters, db
        )
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.post("/dashboard/operational")
async def generate_operational_dashboard(
    filters: DashboardFilter,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> DashboardLayout:
    """Generate operational dashboard."""
    try:
        dashboard = await dashboard_generator.generate_operational_dashboard(
            current_user, filters, db
        )
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# REPORTING ENDPOINTS
# ============================================================================

@billing_router.post("/reports/generate")
async def generate_report(
    request: ReportRequest,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
) -> GeneratedReport:
    """Generate custom report."""
    try:
        report = await reporting_engine.generate_report(current_user, request, db)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@billing_router.get("/reports/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: int = Depends(get_current_user_id)
):
    """Download generated report file."""
    try:
        # In a real implementation, you'd verify user access to the report
        # and retrieve the file path from database
        report_path = f"reports/generated/{report_id}"
        
        return FileResponse(
            path=report_path,
            filename=f"report_{report_id}.pdf",
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Report not found")


@billing_router.get("/reports/templates")
async def get_report_templates(
    report_type: Optional[ReportType] = Query(None)
):
    """Get available report templates."""
    # In a real implementation, this would query the database
    templates = [
        {
            "id": "financial_summary",
            "name": "Financial Summary",
            "description": "Comprehensive financial overview with key metrics",
            "report_type": "financial_summary"
        },
        {
            "id": "revenue_analysis", 
            "name": "Revenue Analysis",
            "description": "Detailed revenue breakdown and trend analysis",
            "report_type": "revenue_analysis"
        },
        {
            "id": "collection_report",
            "name": "Collection Report", 
            "description": "Accounts receivable and collection performance",
            "report_type": "collection_report"
        }
    ]
    
    if report_type:
        templates = [t for t in templates if t["report_type"] == report_type]
        
    return {"success": True, "data": templates}


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@billing_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }


@billing_router.get("/metrics")
@require_permissions(["view_system_metrics"])
async def get_system_metrics(
    db: AsyncSession = Depends(get_db_session)
):
    """Get system performance metrics."""
    try:
        # Basic system metrics
        current_date = datetime.utcnow()
        thirty_days_ago = current_date - timedelta(days=30)
        
        date_range = DateRange(
            start_date=thirty_days_ago,
            end_date=current_date,
            period=ReportPeriod.MONTHLY
        )
        
        # Get summary metrics
        filters = {
            'date_start': thirty_days_ago,
            'date_end': current_date
        }
        
        revenue_metrics = await financial_analytics.get_revenue_metrics(date_range, filters, db)
        payment_summary = await payment_processor.get_payment_summary(db=db)
        
        metrics = {
            "billing_metrics": {
                "total_revenue_30d": revenue_metrics.total_revenue,
                "collection_rate": revenue_metrics.realization_rate,
                "billable_hours_30d": revenue_metrics.billable_hours,
                "utilization_rate": revenue_metrics.utilization_rate
            },
            "payment_metrics": {
                "total_payments": payment_summary.total_payments,
                "successful_payments": payment_summary.successful_payments,
                "failed_payments": payment_summary.failed_payments,
                "total_amount": payment_summary.total_amount
            },
            "system_info": {
                "uptime": "99.9%",  # Would be calculated from actual uptime
                "version": "1.0.0",
                "last_updated": current_date
            }
        }
        
        return {"success": True, "data": metrics}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))