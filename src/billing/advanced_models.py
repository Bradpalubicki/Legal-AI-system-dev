"""
Advanced Billing System Models

SQLAlchemy models for comprehensive legal billing including time tracking,
expense management, invoicing, payments, and trust account management.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Numeric, Enum, JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from decimal import Decimal
from typing import Dict, List, Optional, Any
import uuid

Base = declarative_base()

# Enums
class TimeEntryStatus(PyEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    BILLED = "billed"
    REJECTED = "rejected"

class ExpenseType(PyEnum):
    TRAVEL = "travel"
    MEALS = "meals"
    FILING_FEES = "filing_fees"
    COURT_COSTS = "court_costs"
    EXPERT_FEES = "expert_fees"
    COPYING = "copying"
    RESEARCH = "research"
    TELECOMMUNICATIONS = "telecommunications"
    OTHER = "other"

class InvoiceStatus(PyEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    SENT = "sent"
    PARTIAL_PAYMENT = "partial_payment"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    WRITTEN_OFF = "written_off"

class PaymentStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class PaymentMethod(PyEnum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    ACH = "ach"
    WIRE_TRANSFER = "wire_transfer"
    TRUST_ACCOUNT = "trust_account"

class PaymentType(PyEnum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    RETAINER = "retainer"
    REFUND = "refund"
    TRUST_DEPOSIT = "trust_deposit"
    TRUST_WITHDRAWAL = "trust_withdrawal"

class TransactionType(PyEnum):
    PAYMENT = "payment"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    FEE = "fee"
    INTEREST = "interest"
    TRANSFER = "transfer"
    REVERSAL = "reversal"

class BillingFrequency(PyEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    PROJECT_BASED = "project_based"
    ON_DEMAND = "on_demand"

class RateType(PyEnum):
    HOURLY = "hourly"
    FIXED_FEE = "fixed_fee"
    CONTINGENCY = "contingency"
    BLENDED = "blended"
    ALTERNATIVE = "alternative"

class TrustAccountStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    CLOSED = "closed"

class BillingRuleType(PyEnum):
    DISCOUNT = "discount"
    SURCHARGE = "surcharge"
    WRITE_DOWN = "write_down"
    WRITE_OFF = "write_off"
    CAP = "cap"
    MINIMUM = "minimum"

class ActivityType(PyEnum):
    CORRESPONDENCE = "correspondence"
    RESEARCH = "research"
    DRAFTING = "drafting"
    REVIEW = "review"
    COURT_APPEARANCE = "court_appearance"
    MEETING = "meeting"
    TRAVEL = "travel"
    TELEPHONE = "telephone"
    ADMINISTRATIVE = "administrative"

# Core Models
class BillingClient(Base):
    """Enhanced client model for billing purposes."""
    __tablename__ = 'billing_clients'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Basic Information
    name = Column(String(255), nullable=False)
    company_name = Column(String(255))
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    
    # Billing Configuration
    default_billing_frequency = Column(Enum(BillingFrequency), default=BillingFrequency.MONTHLY)
    default_payment_terms = Column(Integer, default=30)  # Days
    currency = Column(String(3), default='USD')
    tax_rate = Column(Numeric(5, 4), default=0)
    
    # Status and Settings
    is_active = Column(Boolean, default=True)
    credit_limit = Column(Numeric(12, 2))
    current_balance = Column(Numeric(12, 2), default=0)
    
    # Preferences
    billing_preferences = Column(JSON, default={})
    notification_preferences = Column(JSON, default={})
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    matters = relationship("BillingMatter", back_populates="client", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="client", cascade="all, delete-orphan")
    trust_accounts = relationship("TrustAccount", back_populates="client", cascade="all, delete-orphan")
    billing_rates = relationship("BillingRate", back_populates="client", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_client_name', 'name'),
        Index('idx_billing_client_active', 'is_active'),
        Index('idx_billing_client_created', 'created_at'),
    )

class BillingMatter(Base):
    """Legal matter/case for billing purposes."""
    __tablename__ = 'billing_matters'
    
    id = Column(Integer, primary_key=True)
    matter_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('billing_clients.id'), nullable=False)
    
    # Matter Information
    name = Column(String(255), nullable=False)
    matter_number = Column(String(100), unique=True)
    description = Column(Text)
    practice_area = Column(String(100))
    
    # Billing Configuration
    rate_type = Column(Enum(RateType), default=RateType.HOURLY)
    billing_frequency = Column(Enum(BillingFrequency), default=BillingFrequency.MONTHLY)
    
    # Financial Settings
    budget_amount = Column(Numeric(12, 2))
    retainer_amount = Column(Numeric(12, 2))
    contingency_percentage = Column(Numeric(5, 2))
    
    # Status and Tracking
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, server_default=func.now())
    end_date = Column(DateTime)
    
    # Responsible Parties
    primary_attorney = Column(String(100))
    secondary_attorneys = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    client = relationship("BillingClient", back_populates="matters")
    time_entries = relationship("TimeEntry", back_populates="matter", cascade="all, delete-orphan")
    expense_entries = relationship("ExpenseEntry", back_populates="matter", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="matter", cascade="all, delete-orphan")
    billing_rates = relationship("BillingRate", back_populates="matter", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_matter_client', 'client_id'),
        Index('idx_billing_matter_number', 'matter_number'),
        Index('idx_billing_matter_active', 'is_active'),
        Index('idx_billing_matter_attorney', 'primary_attorney'),
    )

class TimeEntry(Base):
    """Individual time entry for billing."""
    __tablename__ = 'time_entries'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    matter_id = Column(Integer, ForeignKey('billing_matters.id'), nullable=False)
    
    # Time Information
    timekeeper = Column(String(100), nullable=False)  # Attorney/staff member
    entry_date = Column(DateTime, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer, nullable=False)
    
    # Activity Details
    activity_type = Column(Enum(ActivityType), nullable=False)
    description = Column(Text, nullable=False)
    task_code = Column(String(20))
    
    # Billing Information
    billable_minutes = Column(Integer)  # May differ from duration for adjustments
    hourly_rate = Column(Numeric(8, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Status and Workflow
    status = Column(Enum(TimeEntryStatus), default=TimeEntryStatus.DRAFT)
    is_billable = Column(Boolean, default=True)
    billed_date = Column(DateTime)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    
    # Review and Approval
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    matter = relationship("BillingMatter", back_populates="time_entries")
    invoice = relationship("Invoice", back_populates="time_entries")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('duration_minutes > 0', name='check_positive_duration'),
        CheckConstraint('billable_minutes >= 0', name='check_non_negative_billable'),
        CheckConstraint('hourly_rate > 0', name='check_positive_rate'),
        Index('idx_time_entry_matter', 'matter_id'),
        Index('idx_time_entry_timekeeper', 'timekeeper'),
        Index('idx_time_entry_date', 'entry_date'),
        Index('idx_time_entry_status', 'status'),
        Index('idx_time_entry_billable', 'is_billable'),
    )

class ExpenseEntry(Base):
    """Expense entries for billing."""
    __tablename__ = 'expense_entries'
    
    id = Column(Integer, primary_key=True)
    expense_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    matter_id = Column(Integer, ForeignKey('billing_matters.id'), nullable=False)
    
    # Expense Information
    expense_date = Column(DateTime, nullable=False)
    expense_type = Column(Enum(ExpenseType), nullable=False)
    vendor = Column(String(255))
    description = Column(Text, nullable=False)
    
    # Financial Details
    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    
    # Receipt and Documentation
    receipt_number = Column(String(100))
    receipt_url = Column(String(500))
    receipt_required = Column(Boolean, default=True)
    receipt_submitted = Column(Boolean, default=False)
    
    # Billing Information
    is_billable = Column(Boolean, default=True)
    markup_percentage = Column(Numeric(5, 2), default=0)
    billable_amount = Column(Numeric(10, 2))
    billed_date = Column(DateTime)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    
    # Status and Approval
    status = Column(Enum(TimeEntryStatus), default=TimeEntryStatus.DRAFT)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    matter = relationship("BillingMatter", back_populates="expense_entries")
    invoice = relationship("Invoice", back_populates="expense_entries")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_positive_amount'),
        CheckConstraint('tax_amount >= 0', name='check_non_negative_tax'),
        CheckConstraint('total_amount > 0', name='check_positive_total'),
        Index('idx_expense_entry_matter', 'matter_id'),
        Index('idx_expense_entry_date', 'expense_date'),
        Index('idx_expense_entry_type', 'expense_type'),
        Index('idx_expense_entry_status', 'status'),
        Index('idx_expense_entry_billable', 'is_billable'),
    )

class Invoice(Base):
    """Generated invoices."""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String(100), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey('billing_clients.id'), nullable=False)
    matter_id = Column(Integer, ForeignKey('billing_matters.id'))
    
    # Invoice Details
    invoice_date = Column(DateTime, nullable=False, server_default=func.now())
    due_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Financial Summary
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='USD')
    
    # Payment Tracking
    amount_paid = Column(Numeric(12, 2), default=0)
    amount_due = Column(Numeric(12, 2), nullable=False)
    
    # Status and Workflow
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    sent_date = Column(DateTime)
    payment_terms = Column(Integer, default=30)
    
    # Content and Presentation
    title = Column(String(255))
    description = Column(Text)
    notes = Column(Text)
    template_id = Column(String(50))
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    client = relationship("BillingClient", back_populates="invoices")
    matter = relationship("BillingMatter", back_populates="invoices")
    time_entries = relationship("TimeEntry", back_populates="invoice")
    expense_entries = relationship("ExpenseEntry", back_populates="invoice")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('total_amount >= 0', name='check_non_negative_total'),
        CheckConstraint('amount_paid >= 0', name='check_non_negative_paid'),
        CheckConstraint('amount_due >= 0', name='check_non_negative_due'),
        Index('idx_invoice_client', 'client_id'),
        Index('idx_invoice_matter', 'matter_id'),
        Index('idx_invoice_number', 'invoice_number'),
        Index('idx_invoice_status', 'status'),
        Index('idx_invoice_date', 'invoice_date'),
        Index('idx_invoice_due_date', 'due_date'),
    )

class InvoiceLineItem(Base):
    """Individual line items within an invoice."""
    __tablename__ = 'invoice_line_items'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    
    # Line Item Details
    line_number = Column(Integer, nullable=False)
    item_type = Column(String(50), nullable=False)  # time, expense, fee, adjustment
    description = Column(Text, nullable=False)
    
    # Quantity and Pricing
    quantity = Column(Numeric(10, 4), default=1)
    unit_rate = Column(Numeric(10, 2))
    amount = Column(Numeric(10, 2), nullable=False)
    
    # References
    time_entry_id = Column(Integer, ForeignKey('time_entries.id'))
    expense_entry_id = Column(Integer, ForeignKey('expense_entries.id'))
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    time_entry = relationship("TimeEntry")
    expense_entry = relationship("ExpenseEntry")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_positive_quantity'),
        Index('idx_line_item_invoice', 'invoice_id'),
        Index('idx_line_item_type', 'item_type'),
        UniqueConstraint('invoice_id', 'line_number', name='unique_line_number'),
    )

class Payment(Base):
    """Payment records."""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('billing_clients.id'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    
    # Payment Details
    payment_date = Column(DateTime, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='USD')
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Transaction Information
    reference_number = Column(String(100))
    transaction_id = Column(String(100))
    check_number = Column(String(50))
    
    # Status and Processing
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    processed_date = Column(DateTime)
    cleared_date = Column(DateTime)
    
    # Banking Information
    bank_account = Column(String(100))
    routing_number = Column(String(20))
    
    # Trust Account
    trust_account_id = Column(Integer, ForeignKey('trust_accounts.id'))
    
    # Notes and Description
    description = Column(Text)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    client = relationship("BillingClient", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
    trust_account = relationship("TrustAccount", back_populates="payments")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_positive_payment_amount'),
        Index('idx_payment_client', 'client_id'),
        Index('idx_payment_invoice', 'invoice_id'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_method', 'payment_method'),
    )

class TrustAccount(Base):
    """Client trust account management."""
    __tablename__ = 'trust_accounts'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('billing_clients.id'), nullable=False)
    
    # Account Information
    account_name = Column(String(255), nullable=False)
    account_number = Column(String(100), unique=True)
    account_type = Column(String(50), default='IOLTA')
    
    # Balance Information
    current_balance = Column(Numeric(12, 2), default=0)
    available_balance = Column(Numeric(12, 2), default=0)
    minimum_balance = Column(Numeric(12, 2), default=0)
    
    # Status and Configuration
    status = Column(Enum(TrustAccountStatus), default=TrustAccountStatus.ACTIVE)
    interest_bearing = Column(Boolean, default=True)
    
    # Banking Details
    bank_name = Column(String(255))
    bank_account_number = Column(String(100))
    bank_routing_number = Column(String(20))
    
    # Compliance and Monitoring
    last_reconciliation_date = Column(DateTime)
    next_reconciliation_date = Column(DateTime)
    reconciliation_frequency = Column(Integer, default=30)  # Days
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    client = relationship("BillingClient", back_populates="trust_accounts")
    payments = relationship("Payment", back_populates="trust_account")
    transactions = relationship("TrustTransaction", back_populates="trust_account", cascade="all, delete-orphan")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('current_balance >= 0', name='check_non_negative_balance'),
        CheckConstraint('available_balance >= 0', name='check_non_negative_available'),
        Index('idx_trust_account_client', 'client_id'),
        Index('idx_trust_account_status', 'status'),
        Index('idx_trust_account_number', 'account_number'),
    )

class TrustTransaction(Base):
    """Trust account transactions."""
    __tablename__ = 'trust_transactions'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    trust_account_id = Column(Integer, ForeignKey('trust_accounts.id'), nullable=False)
    
    # Transaction Details
    transaction_date = Column(DateTime, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # deposit, withdrawal, transfer, fee
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=False)
    
    # Description and Reference
    description = Column(Text, nullable=False)
    reference_number = Column(String(100))
    payment_id = Column(Integer, ForeignKey('payments.id'))
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(100))
    
    # Relationships
    trust_account = relationship("TrustAccount", back_populates="transactions")
    payment = relationship("Payment")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('amount != 0', name='check_non_zero_amount'),
        CheckConstraint('balance_after >= 0', name='check_non_negative_balance_after'),
        Index('idx_trust_transaction_account', 'trust_account_id'),
        Index('idx_trust_transaction_date', 'transaction_date'),
        Index('idx_trust_transaction_type', 'transaction_type'),
    )

# Configuration Models
class BillingRate(Base):
    """Billing rates for different timekeepers, clients, and matters."""
    __tablename__ = 'billing_rates'
    
    id = Column(Integer, primary_key=True)
    rate_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Rate Scope
    timekeeper = Column(String(100), nullable=False)
    client_id = Column(Integer, ForeignKey('billing_clients.id'))
    matter_id = Column(Integer, ForeignKey('billing_matters.id'))
    
    # Rate Information
    rate_type = Column(Enum(RateType), default=RateType.HOURLY)
    hourly_rate = Column(Numeric(8, 2))
    fixed_fee_amount = Column(Numeric(12, 2))
    contingency_percentage = Column(Numeric(5, 2))
    
    # Validity Period
    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime)
    
    # Activity-Specific Rates
    activity_type = Column(Enum(ActivityType))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    client = relationship("BillingClient", back_populates="billing_rates")
    matter = relationship("BillingMatter", back_populates="billing_rates")
    
    # Constraints and Indexes
    __table_args__ = (
        Index('idx_billing_rate_timekeeper', 'timekeeper'),
        Index('idx_billing_rate_client', 'client_id'),
        Index('idx_billing_rate_matter', 'matter_id'),
        Index('idx_billing_rate_effective', 'effective_date'),
        Index('idx_billing_rate_active', 'is_active'),
    )

class BillingRule(Base):
    """Billing rules for automatic adjustments and calculations."""
    __tablename__ = 'billing_rules'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Rule Configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    rule_type = Column(Enum(BillingRuleType), nullable=False)
    
    # Scope and Conditions
    client_id = Column(Integer, ForeignKey('billing_clients.id'))
    matter_id = Column(Integer, ForeignKey('billing_matters.id'))
    timekeeper = Column(String(100))
    activity_type = Column(Enum(ActivityType))
    
    # Rule Parameters
    rule_conditions = Column(JSON, default={})  # Flexible condition storage
    adjustment_type = Column(String(50))  # percentage, fixed_amount, hours
    adjustment_value = Column(Numeric(10, 4))
    
    # Execution Settings
    auto_apply = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    
    # Validity
    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime, server_default=func.now())
    expiration_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_rule_type', 'rule_type'),
        Index('idx_billing_rule_client', 'client_id'),
        Index('idx_billing_rule_matter', 'matter_id'),
        Index('idx_billing_rule_active', 'is_active'),
        Index('idx_billing_rule_priority', 'priority'),
    )

class BillingTemplate(Base):
    """Invoice templates for different clients and matter types."""
    __tablename__ = 'billing_templates'
    
    id = Column(Integer, primary_key=True)
    template_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Template Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), default='invoice')  # invoice, statement, report
    
    # Template Content
    header_template = Column(Text)
    footer_template = Column(Text)
    line_item_template = Column(Text)
    summary_template = Column(Text)
    
    # Styling and Layout
    css_styles = Column(Text)
    layout_settings = Column(JSON, default={})
    
    # Usage Scope
    client_id = Column(Integer, ForeignKey('billing_clients.id'))
    practice_area = Column(String(100))
    is_default = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_template_type', 'template_type'),
        Index('idx_billing_template_client', 'client_id'),
        Index('idx_billing_template_active', 'is_active'),
        Index('idx_billing_template_default', 'is_default'),
    )

# Audit and Tracking Models
class BillingAudit(Base):
    """Comprehensive audit trail for billing activities."""
    __tablename__ = 'billing_audits'
    
    id = Column(Integer, primary_key=True)
    audit_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Audit Information
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)  # time_entry, expense, invoice, payment
    entity_id = Column(String(50), nullable=False)
    
    # User Information
    user_id = Column(String(100), nullable=False)
    user_name = Column(String(255))
    ip_address = Column(String(45))
    
    # Change Information
    old_values = Column(JSON, default={})
    new_values = Column(JSON, default={})
    changes_made = Column(JSON, default={})
    
    # Context
    context_data = Column(JSON, default={})
    
    # Timestamp
    timestamp = Column(DateTime, server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_audit_action', 'action'),
        Index('idx_billing_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_billing_audit_user', 'user_id'),
        Index('idx_billing_audit_timestamp', 'timestamp'),
    )

class BillingAlert(Base):
    """Alerts and notifications for billing system."""
    __tablename__ = 'billing_alerts'
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Alert Information
    alert_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default='info')  # info, warning, error, critical
    
    # Related Entities
    client_id = Column(Integer, ForeignKey('billing_clients.id'))
    matter_id = Column(Integer, ForeignKey('billing_matters.id'))
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    
    # Status
    is_read = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_alert_type', 'alert_type'),
        Index('idx_billing_alert_severity', 'severity'),
        Index('idx_billing_alert_client', 'client_id'),
        Index('idx_billing_alert_unread', 'is_read'),
        Index('idx_billing_alert_created', 'created_at'),
    )