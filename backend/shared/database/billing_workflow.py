"""
Billing and Workflow Models for Legal AI System

Models for billing, invoicing, payments, workflow automation,
and business process management.
"""

import enum
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, Date,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Numeric, Table
)
from sqlalchemy.orm import relationship, validates

from .base import BaseModel, NamedModel, StatusModel, StatusEnum, PriorityEnum


# =============================================================================
# ENUMS
# =============================================================================

class BillingType(enum.Enum):
    """Types of billing arrangements"""
    HOURLY = "hourly"
    FLAT_FEE = "flat_fee"
    CONTINGENCY = "contingency"
    RETAINER = "retainer"
    MIXED = "mixed"
    BLENDED_RATE = "blended_rate"
    ALTERNATIVE_FEE = "alternative_fee"
    PRO_BONO = "pro_bono"


class InvoiceStatus(enum.Enum):
    """Invoice status values"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    WRITTEN_OFF = "written_off"


class PaymentMethod(enum.Enum):
    """Payment methods"""
    CHECK = "check"
    WIRE_TRANSFER = "wire_transfer"
    CREDIT_CARD = "credit_card"
    ACH = "ach"
    CASH = "cash"
    OFFSET = "offset"
    OTHER = "other"


class ExpenseType(enum.Enum):
    """Types of expenses"""
    TRAVEL = "travel"
    LODGING = "lodging"
    MEALS = "meals"
    FILING_FEES = "filing_fees"
    COURT_COSTS = "court_costs"
    COPYING = "copying"
    POSTAGE = "postage"
    TELEPHONE = "telephone"
    RESEARCH_DATABASES = "research_databases"
    EXPERT_FEES = "expert_fees"
    DEPOSITION_COSTS = "deposition_costs"
    OTHER = "other"


class WorkflowStatus(enum.Enum):
    """Workflow execution status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class WorkflowTriggerType(enum.Enum):
    """Types of workflow triggers"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    API_CALL = "api_call"
    EMAIL_RECEIVED = "email_received"
    DOCUMENT_UPLOADED = "document_uploaded"
    CASE_STATUS_CHANGE = "case_status_change"
    DEADLINE_APPROACHING = "deadline_approaching"


class TaskAutomationType(enum.Enum):
    """Types of automated tasks"""
    EMAIL_NOTIFICATION = "email_notification"
    DOCUMENT_GENERATION = "document_generation"
    CALENDAR_EVENT = "calendar_event"
    TASK_CREATION = "task_creation"
    STATUS_UPDATE = "status_update"
    DATA_SYNCHRONIZATION = "data_synchronization"
    REPORT_GENERATION = "report_generation"
    BACKUP_CREATION = "backup_creation"


# =============================================================================
# BILLING MODELS
# =============================================================================

class BillingArrangement(BaseModel):
    """Billing arrangements and fee structures"""
    
    __tablename__ = 'billing_arrangements'
    
    # Basic Information
    name = Column(String(200), nullable=False)
    billing_type = Column(SQLEnum(BillingType), nullable=False)
    description = Column(Text)
    
    # Client and Case Association
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True, index=True)
    
    # Rate Structure
    hourly_rate = Column(Integer)  # In cents
    flat_fee_amount = Column(Integer)  # In cents
    contingency_percentage = Column(Numeric(5, 2))  # 0.00 to 100.00
    blended_rate = Column(Integer)  # In cents
    
    # Retainer Information
    retainer_amount = Column(Integer)  # In cents
    retainer_balance = Column(Integer)  # In cents
    retainer_replenishment_threshold = Column(Integer)  # In cents
    
    # Rate Cards (for different attorney levels)
    rate_card = Column(JSON, default=dict)  # {"partner": 50000, "associate": 30000, "paralegal": 15000}
    
    # Terms and Conditions
    payment_terms = Column(String(50), default='net_30')  # net_30, net_15, due_on_receipt
    late_fee_percentage = Column(Numeric(5, 2))
    discount_percentage = Column(Numeric(5, 2))
    
    # Budget and Limits
    estimated_budget = Column(Integer)  # In cents
    budget_alert_threshold = Column(Numeric(5, 2), default=90)  # Alert at 90% of budget
    spending_cap = Column(Integer)  # In cents - hard limit
    
    # Billing Schedule
    billing_frequency = Column(String(20), default='monthly')  # weekly, bi-weekly, monthly, quarterly
    billing_day = Column(Integer)  # Day of month/week for recurring billing
    next_billing_date = Column(Date)
    
    # Status and Dates
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, default=date.today)
    end_date = Column(Date)
    
    # Approval
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_date = Column(Date)
    
    # Relationships
    client = relationship("Client", foreign_keys=[client_id])
    case = relationship("Case", foreign_keys=[case_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    invoices = relationship("Invoice", back_populates="billing_arrangement")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_billing_arrangements_client_active', 'client_id', 'is_active'),
        Index('ix_billing_arrangements_case_active', 'case_id', 'is_active'),
        Index('ix_billing_arrangements_next_billing', 'next_billing_date'),
    )
    
    @property
    def current_spend(self) -> Decimal:
        """Calculate current spend against budget"""
        # This would sum up related time entries and expenses
        # Implementation depends on time tracking integration
        return Decimal('0')
    
    @property
    def budget_utilization_percentage(self) -> Optional[Decimal]:
        """Calculate budget utilization percentage"""
        if self.estimated_budget:
            return (self.current_spend / (self.estimated_budget / 100)) * 100
        return None
    
    def __repr__(self):
        return f"<BillingArrangement(id={self.id}, client_id={self.client_id}, type='{self.billing_type.value}')>"


class Invoice(BaseModel):
    """Client invoices"""
    
    __tablename__ = 'invoices'
    
    # Invoice Identification
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Client and Billing
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    billing_arrangement_id = Column(Integer, ForeignKey('billing_arrangements.id'), nullable=False)
    
    # Period Covered
    period_start = Column(Date)
    period_end = Column(Date)
    
    # Amounts (in cents)
    subtotal = Column(Integer, default=0, nullable=False)
    tax_amount = Column(Integer, default=0)
    discount_amount = Column(Integer, default=0)
    total_amount = Column(Integer, nullable=False)
    
    # Status
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    
    # Payment Tracking
    amount_paid = Column(Integer, default=0)
    amount_outstanding = Column(Integer)  # Calculated field
    
    # Narrative and Notes
    narrative = Column(Text)
    internal_notes = Column(Text)
    client_notes = Column(Text)
    
    # Delivery
    sent_date = Column(Date)
    sent_method = Column(String(50))  # email, mail, portal
    sent_to_email = Column(String(255))
    
    # Aging
    days_outstanding = Column(Integer, default=0)
    is_overdue = Column(Boolean, default=False)
    
    # File References
    invoice_pdf_path = Column(String(500))
    supporting_documents = Column(JSON, default=list)
    
    # Review and Approval
    reviewed_by_id = Column(Integer, ForeignKey('users.id'))
    reviewed_date = Column(Date)
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_date = Column(Date)
    
    # Write-off Information
    write_off_amount = Column(Integer, default=0)
    write_off_reason = Column(String(200))
    write_off_date = Column(Date)
    write_off_approved_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    client = relationship("Client", foreign_keys=[client_id])
    billing_arrangement = relationship("BillingArrangement", back_populates="invoices")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    write_off_approved_by = relationship("User", foreign_keys=[write_off_approved_by_id])
    
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_invoices_client_status', 'client_id', 'status'),
        Index('ix_invoices_due_date', 'due_date', 'status'),
        Index('ix_invoices_period', 'period_start', 'period_end'),
        Index('ix_invoices_overdue', 'is_overdue'),
        CheckConstraint('total_amount >= 0', name='ck_positive_total'),
        CheckConstraint('amount_paid >= 0', name='ck_positive_paid'),
    )
    
    def generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        if self.client_id and self.invoice_date:
            year = self.invoice_date.year
            month = self.invoice_date.month
            # This would typically include a sequence number
            sequence = 1  # This would be calculated based on existing invoices
            self.invoice_number = f"INV-{self.client_id:06d}-{year}{month:02d}-{sequence:04d}"
        return self.invoice_number
    
    def calculate_outstanding_amount(self):
        """Calculate outstanding amount"""
        self.amount_outstanding = self.total_amount - self.amount_paid - self.write_off_amount
    
    def update_aging(self):
        """Update aging information"""
        if self.due_date:
            self.days_outstanding = (date.today() - self.due_date).days
            self.is_overdue = self.days_outstanding > 0 and self.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total_amount/100:.2f})>"


class InvoiceLineItem(BaseModel):
    """Individual line items on invoices"""
    
    __tablename__ = 'invoice_line_items'
    
    # Line Item Details
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    
    # Item Information
    item_type = Column(String(50), nullable=False)  # time, expense, flat_fee, adjustment
    description = Column(Text, nullable=False)
    
    # Time Entry Information (for time items)
    time_entry_id = Column(Integer, ForeignKey('time_entries.id'), nullable=True)
    attorney_name = Column(String(200))
    hours = Column(Numeric(5, 2))
    rate = Column(Integer)  # In cents per hour
    
    # Expense Information (for expense items)
    expense_id = Column(Integer, ForeignKey('expenses.id'), nullable=True)
    expense_type = Column(SQLEnum(ExpenseType))
    expense_date = Column(Date)
    
    # Amounts (in cents)
    unit_price = Column(Integer)
    quantity = Column(Numeric(10, 3), default=1)
    discount_percentage = Column(Numeric(5, 2), default=0)
    line_total = Column(Integer, nullable=False)
    
    # Flags
    is_billable = Column(Boolean, default=True)
    is_taxable = Column(Boolean, default=True)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    time_entry = relationship("TimeEntry", foreign_keys=[time_entry_id])
    expense = relationship("Expense", foreign_keys=[expense_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_line_items_invoice_line', 'invoice_id', 'line_number'),
        Index('ix_line_items_time_entry', 'time_entry_id'),
        Index('ix_line_items_expense', 'expense_id'),
        UniqueConstraint('invoice_id', 'line_number', name='uq_invoice_line_number'),
        CheckConstraint('line_total >= 0', name='ck_positive_line_total'),
    )
    
    def calculate_line_total(self):
        """Calculate line total with discount"""
        if self.unit_price and self.quantity:
            subtotal = int(self.unit_price * float(self.quantity))
            discount = int(subtotal * float(self.discount_percentage or 0) / 100)
            self.line_total = subtotal - discount
    
    def __repr__(self):
        return f"<InvoiceLineItem(id={self.id}, invoice_id={self.invoice_id}, line={self.line_number})>"


class Payment(BaseModel):
    """Payment records"""
    
    __tablename__ = 'payments'
    
    # Payment Details
    payment_date = Column(Date, default=date.today, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    amount = Column(Integer, nullable=False)  # In cents
    
    # Invoice Association
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    
    # Payment Details
    reference_number = Column(String(100))  # Check number, transaction ID, etc.
    payment_note = Column(Text)
    
    # Bank Information (for checks/wires)
    bank_name = Column(String(200))
    account_number_last_four = Column(String(4))
    
    # Credit Card Information (if applicable)
    card_last_four = Column(String(4))
    card_type = Column(String(20))  # Visa, MasterCard, Amex
    authorization_code = Column(String(50))
    
    # Processing
    processed_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    processing_fee = Column(Integer, default=0)  # In cents
    net_amount = Column(Integer)  # Amount after processing fees
    
    # Status
    is_cleared = Column(Boolean, default=False)
    cleared_date = Column(Date)
    
    # Reconciliation
    deposit_date = Column(Date)
    bank_statement_date = Column(Date)
    reconciled = Column(Boolean, default=False)
    reconciled_by_id = Column(Integer, ForeignKey('users.id'))
    reconciled_date = Column(Date)
    
    # Refund Information
    is_refunded = Column(Boolean, default=False)
    refund_amount = Column(Integer, default=0)
    refund_date = Column(Date)
    refund_reason = Column(Text)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    client = relationship("Client", foreign_keys=[client_id])
    processed_by = relationship("User", foreign_keys=[processed_by_id])
    reconciled_by = relationship("User", foreign_keys=[reconciled_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_payments_invoice_date', 'invoice_id', 'payment_date'),
        Index('ix_payments_client_date', 'client_id', 'payment_date'),
        Index('ix_payments_method_date', 'payment_method', 'payment_date'),
        Index('ix_payments_cleared', 'is_cleared', 'cleared_date'),
        CheckConstraint('amount > 0', name='ck_positive_amount'),
    )
    
    def calculate_net_amount(self):
        """Calculate net amount after processing fees"""
        self.net_amount = self.amount - self.processing_fee
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount/100:.2f}, date='{self.payment_date}')>"


class Expense(BaseModel):
    """Expense records"""
    
    __tablename__ = 'expenses'
    
    # Expense Details
    expense_date = Column(Date, default=date.today, nullable=False)
    expense_type = Column(SQLEnum(ExpenseType), nullable=False)
    description = Column(String(500), nullable=False)
    
    # Amount
    amount = Column(Integer, nullable=False)  # In cents
    
    # Case and Client
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    
    # User
    incurred_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Billing
    is_billable = Column(Boolean, default=True)
    billing_rate = Column(Integer)  # Markup rate in cents
    billed_amount = Column(Integer)  # Amount to bill client
    
    # Status
    status = Column(String(20), default='submitted')  # submitted, approved, rejected, billed
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_date = Column(Date)
    
    # Receipt Information
    receipt_required = Column(Boolean, default=True)
    receipt_attached = Column(Boolean, default=False)
    receipt_path = Column(String(500))
    
    # Vendor Information
    vendor_name = Column(String(200))
    vendor_contact = Column(String(500))
    
    # Categories and Coding
    expense_category = Column(String(100))
    billing_code = Column(String(50))
    
    # Reimbursement
    is_reimbursable = Column(Boolean, default=False)
    reimbursed = Column(Boolean, default=False)
    reimbursement_date = Column(Date)
    
    # Notes
    notes = Column(Text)
    rejection_reason = Column(Text)
    
    # Relationships
    case = relationship("Case", foreign_keys=[case_id])
    client = relationship("Client", foreign_keys=[client_id])
    incurred_by = relationship("User", foreign_keys=[incurred_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_expenses_case_date', 'case_id', 'expense_date'),
        Index('ix_expenses_client_date', 'client_id', 'expense_date'),
        Index('ix_expenses_user_status', 'incurred_by_id', 'status'),
        Index('ix_expenses_type_date', 'expense_type', 'expense_date'),
        CheckConstraint('amount > 0', name='ck_positive_expense_amount'),
    )
    
    def calculate_billed_amount(self):
        """Calculate amount to bill client including markup"""
        if self.billing_rate:
            markup = int(self.amount * (self.billing_rate / 10000))  # billing_rate in basis points
            self.billed_amount = self.amount + markup
        else:
            self.billed_amount = self.amount
    
    def __repr__(self):
        return f"<Expense(id={self.id}, type='{self.expense_type.value}', amount={self.amount/100:.2f})>"


# =============================================================================
# WORKFLOW MODELS
# =============================================================================

class WorkflowDefinition(NamedModel):
    """Workflow process definitions"""
    
    __tablename__ = 'workflow_definitions'
    
    # Workflow Details
    version = Column(String(20), default='1.0')
    category = Column(String(100))  # case_management, billing, document_review
    
    # Configuration
    trigger_type = Column(SQLEnum(WorkflowTriggerType), nullable=False)
    trigger_config = Column(JSON, default=dict)  # Trigger-specific configuration
    
    # Workflow Steps
    steps = Column(JSON, nullable=False)  # Ordered list of workflow steps
    
    # Conditions and Rules
    conditions = Column(JSON, default=list)  # Execution conditions
    rules = Column(JSON, default=list)  # Business rules
    
    # Settings
    is_active = Column(Boolean, default=True)
    max_concurrent_executions = Column(Integer, default=10)
    timeout_minutes = Column(Integer, default=60)
    
    # Usage Statistics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Access Control
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    firm = relationship("LawFirm", foreign_keys=[firm_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    executions = relationship("WorkflowExecution", back_populates="definition")
    
    def __repr__(self):
        return f"<WorkflowDefinition(id={self.id}, name='{self.name}', trigger='{self.trigger_type.value}')>"


class WorkflowExecution(BaseModel):
    """Individual workflow execution instances"""
    
    __tablename__ = 'workflow_executions'
    
    # Execution Details
    definition_id = Column(Integer, ForeignKey('workflow_definitions.id'), nullable=False, index=True)
    execution_name = Column(String(200))
    
    # Trigger Information
    triggered_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    trigger_event = Column(String(100))
    trigger_data = Column(JSON, default=dict)
    
    # Status
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.ACTIVE, nullable=False)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer)
    
    # Timing
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Context Data
    context_data = Column(JSON, default=dict)  # Data passed between steps
    input_data = Column(JSON, default=dict)    # Original input data
    output_data = Column(JSON, default=dict)   # Final output data
    
    # Error Information
    error_message = Column(Text)
    error_step = Column(Integer)
    retry_count = Column(Integer, default=0)
    
    # Resources
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Relationships
    definition = relationship("WorkflowDefinition", back_populates="executions")
    triggered_by = relationship("User", foreign_keys=[triggered_by_id])
    case = relationship("Case", foreign_keys=[case_id])
    client = relationship("Client", foreign_keys=[client_id])
    document = relationship("Document", foreign_keys=[document_id])
    
    step_logs = relationship("WorkflowStepLog", back_populates="execution", cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_workflow_executions_definition_status', 'definition_id', 'status'),
        Index('ix_workflow_executions_status_started', 'status', 'started_at'),
        Index('ix_workflow_executions_case', 'case_id'),
        Index('ix_workflow_executions_triggered_by', 'triggered_by_id', 'started_at'),
    )
    
    def calculate_duration(self):
        """Calculate execution duration"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_steps > 0:
            return (self.current_step / self.total_steps) * 100
        return 0
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, definition_id={self.definition_id}, status='{self.status.value}')>"


class WorkflowStepLog(BaseModel):
    """Log entries for individual workflow steps"""
    
    __tablename__ = 'workflow_step_logs'
    
    # Step Information
    execution_id = Column(Integer, ForeignKey('workflow_executions.id'), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(200), nullable=False)
    step_type = Column(SQLEnum(TaskAutomationType), nullable=False)
    
    # Execution
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    
    # Status
    status = Column(String(20), default='running')  # running, completed, failed, skipped
    
    # Input/Output
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    
    # Results
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Logs
    log_messages = Column(JSON, default=list)  # Step execution logs
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="step_logs")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_step_logs_execution_step', 'execution_id', 'step_number'),
        Index('ix_step_logs_status', 'status'),
        UniqueConstraint('execution_id', 'step_number', name='uq_execution_step'),
    )
    
    def calculate_duration(self):
        """Calculate step duration in milliseconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def __repr__(self):
        return f"<WorkflowStepLog(id={self.id}, step='{self.step_name}', status='{self.status}')>"


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    'BillingArrangement',
    'Invoice',
    'InvoiceLineItem',
    'Payment',
    'Expense',
    'WorkflowDefinition',
    'WorkflowExecution',
    'WorkflowStepLog',
    'BillingType',
    'InvoiceStatus',
    'PaymentMethod',
    'ExpenseType',
    'WorkflowStatus',
    'WorkflowTriggerType',
    'TaskAutomationType'
]