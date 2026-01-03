"""
Legal AI System - Billing Models
Comprehensive billing, subscription, and payment tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from ..src.core.database import Base

class BillingPlan(Base):
    """Subscription plans available to customers"""
    __tablename__ = "billing_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2))
    stripe_price_id = Column(String(100), nullable=False, unique=True)
    stripe_product_id = Column(String(100), nullable=False)

    # Feature limits
    features = Column(JSON, default={})  # {"documents_per_month": 100, "ai_queries": 500}
    is_active = Column(Boolean, default=True)
    trial_days = Column(Integer, default=14)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    """Customer subscriptions"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("billing_plans.id"), nullable=False)

    stripe_subscription_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(50), nullable=False, index=True)  # active, canceled, past_due, trialing

    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    canceled_at = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)

    # Billing
    collection_method = Column(String(20), default="charge_automatically")
    days_until_due = Column(Integer)

    # Usage tracking
    current_usage = Column(JSON, default={})  # {"documents": 25, "ai_queries": 150}
    usage_reset_date = Column(DateTime)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("BillingPlan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")
    usage_records = relationship("Usage", back_populates="subscription")

class PaymentMethod(Base):
    """Customer payment methods"""
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    stripe_payment_method_id = Column(String(100), nullable=False, unique=True)
    type = Column(String(20), nullable=False)  # card, bank_account, etc.

    # Card details (if applicable)
    card_brand = Column(String(20))
    card_last4 = Column(String(4))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="payment_methods")

class Invoice(Base):
    """Customer invoices"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    stripe_invoice_id = Column(String(100), nullable=False, unique=True)
    invoice_number = Column(String(50))

    # Amounts (in USD)
    subtotal = Column(Numeric(10, 2), default=0.00)
    tax = Column(Numeric(10, 2), default=0.00)
    total = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0.00)
    amount_due = Column(Numeric(10, 2), nullable=False)

    currency = Column(String(3), default="USD")
    status = Column(String(20), nullable=False, index=True)  # draft, open, paid, void

    # Dates
    created_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    paid_date = Column(DateTime)

    # URLs and PDFs
    hosted_invoice_url = Column(String(500))
    invoice_pdf = Column(String(500))

    # Billing details
    billing_reason = Column(String(50))  # subscription_create, subscription_cycle, manual
    description = Column(Text)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")

class Payment(Base):
    """Payment records"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    stripe_payment_id = Column(String(100), nullable=False, unique=True)
    stripe_payment_intent_id = Column(String(100))

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), nullable=False, index=True)  # succeeded, failed, pending, canceled

    # Payment method details
    payment_method_type = Column(String(20))  # card, bank_account
    payment_method_details = Column(JSON)  # {"card": {"brand": "visa", "last4": "4242"}}

    # Refund information
    refunded_amount = Column(Numeric(10, 2), default=0.00)
    refund_reason = Column(String(100))

    # Fees and charges
    stripe_fee = Column(Numeric(10, 2))
    net_amount = Column(Numeric(10, 2))

    # Timestamps
    processed_at = Column(DateTime)
    failed_at = Column(DateTime)
    failure_reason = Column(String(200))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
    refund_requests = relationship("RefundRequest", back_populates="payment")

class Usage(Base):
    """Feature usage tracking for billing"""
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    feature = Column(String(50), nullable=False, index=True)  # documents, ai_queries, storage
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 4))  # Price per unit if applicable

    # Metadata for detailed tracking
    usage_metadata = Column(JSON)  # {"document_id": 123, "query_type": "contract_analysis"}

    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)

    # Billing status
    billed = Column(Boolean, default=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="usage_records")
    subscription = relationship("Subscription", back_populates="usage_records")

class RefundRequest(Base):
    """Refund requests and processing"""
    __tablename__ = "refund_requests"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(100), nullable=False)
    description = Column(Text)

    status = Column(String(20), nullable=False, index=True)  # pending, approved, denied, processed

    # Stripe refund details
    stripe_refund_id = Column(String(100), unique=True)

    # Processing details
    requested_by = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    processed_by = Column(Integer, ForeignKey("users.id"))

    requested_at = Column(DateTime, default=func.now())
    reviewed_at = Column(DateTime)
    processed_at = Column(DateTime)

    # Review notes
    review_notes = Column(Text)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="refund_requests")

class BillingEvent(Base):
    """Billing events and audit trail"""
    __tablename__ = "billing_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    # subscription_created, payment_succeeded, invoice_generated, refund_processed

    event_data = Column(JSON)
    description = Column(Text)

    # Related objects
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_id = Column(Integer, ForeignKey("payments.id"))

    # Stripe event ID if from webhook
    stripe_event_id = Column(String(100), unique=True)

    created_at = Column(DateTime, default=func.now())

class PromoCode(Base):
    """Promotional codes and discounts"""
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100))

    # Discount details
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    discount_value = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Validity
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime)
    max_uses = Column(Integer)
    current_uses = Column(Integer, default=0)

    # Restrictions
    applicable_plans = Column(JSON)  # List of plan IDs
    first_time_customers_only = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TaxRate(Base):
    """Tax rates by jurisdiction"""
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True, index=True)

    # Geographic details
    country = Column(String(2), nullable=False)  # US, CA, etc.
    state = Column(String(20))  # Optional state/province
    jurisdiction = Column(String(100))

    # Tax details
    tax_type = Column(String(20), nullable=False)  # sales_tax, vat, gst
    rate = Column(Numeric(5, 4), nullable=False)  # 0.0875 for 8.75%

    # Stripe tax rate ID
    stripe_tax_rate_id = Column(String(100), unique=True)

    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())