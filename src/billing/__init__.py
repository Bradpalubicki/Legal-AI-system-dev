"""
Legal Billing and Cost Tracking System

Advanced billing system for tracking PACER fees, document costs, and client
billing allocation with detailed cost analysis and automated billing generation.

Features:
- PACER fee tracking and allocation
- Client-based cost allocation
- Automated billing generation
- Cost optimization and analysis
- Budget monitoring and alerts
- Integration with time tracking
- Multi-currency support
- Detailed cost reporting
"""

# Temporarily commented out to fix import issues
# from .advanced_models import (
#     TimeEntry, TimeSheet, ExpenseEntry, Invoice, InvoiceLineItem,
#     Payment, TrustAccount, BillingMatter, BillingRate, PaymentMethod,
#     RecurringPayment, PaymentSchedule, AuditLog
# )
# from .time_tracker import TimeTracker, TimesheetManager, TimeEntryRequest, TimesheetSummary
# from .expense_manager import ExpenseManager, ExpenseRequest, ExpenseSummary, ReceiptUpload
# from .invoice_generator import InvoiceGenerator, InvoiceRequest, InvoicePreview, InvoiceSummary
from .payment_processor import PaymentProcessor, PaymentRequest, PaymentResult, PaymentSummary
from .payment_methods import PaymentMethodManager, PaymentMethodCreate, PaymentMethodResponse
from .recurring_payments import RecurringPaymentManager, RecurringPaymentCreate, RecurringPaymentResponse
from .financial_analytics import (
    FinancialAnalytics, RevenueMetrics, ProfitabilityMetrics, CollectionMetrics,
    CashFlowMetrics, MatterPerformance, AttorneyPerformance, FinancialReport,
    DateRange, ReportPeriod
)
from .dashboard_generator import (
    DashboardGenerator, DashboardLayout, DashboardWidget, DashboardFilter,
    KPIWidget, ChartWidget, TableWidget, GaugeWidget, WidgetType, ChartType
)
from .reporting_engine import (
    ReportingEngine, ReportRequest, ReportTemplate, GeneratedReport,
    ReportFormat, ReportType, ScheduleFrequency
)

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    # Advanced Models
    "TimeEntry",
    "TimeSheet", 
    "ExpenseEntry",
    "Invoice",
    "InvoiceLineItem",
    "Payment",
    "TrustAccount",
    "BillingMatter",
    "BillingRate",
    "PaymentMethod",
    "RecurringPayment",
    "PaymentSchedule",
    "AuditLog",
    
    # Service Classes
    "TimeTracker",
    "TimesheetManager",
    "ExpenseManager", 
    "InvoiceGenerator",
    "PaymentProcessor",
    "PaymentMethodManager",
    "RecurringPaymentManager",
    
    # Request/Response Models
    "TimeEntryRequest",
    "TimesheetSummary",
    "ExpenseRequest",
    "ExpenseSummary",
    "ReceiptUpload",
    "InvoiceRequest",
    "InvoicePreview",
    "InvoiceSummary",
    "PaymentRequest",
    "PaymentResult",
    "PaymentSummary",
    "PaymentMethodCreate",
    "PaymentMethodResponse",
    "RecurringPaymentCreate",
    "RecurringPaymentResponse",
    
    # Analytics & Reporting
    "FinancialAnalytics",
    "RevenueMetrics",
    "ProfitabilityMetrics", 
    "CollectionMetrics",
    "CashFlowMetrics",
    "MatterPerformance",
    "AttorneyPerformance",
    "FinancialReport",
    "DateRange",
    "ReportPeriod",
    
    # Dashboard
    "DashboardGenerator",
    "DashboardLayout",
    "DashboardWidget",
    "DashboardFilter",
    "KPIWidget",
    "ChartWidget",
    "TableWidget",
    "GaugeWidget",
    "WidgetType",
    "ChartType",
    
    # Reporting
    "ReportingEngine",
    "ReportRequest",
    "ReportTemplate",
    "GeneratedReport",
    "ReportFormat",
    "ReportType",
    "ScheduleFrequency"
]