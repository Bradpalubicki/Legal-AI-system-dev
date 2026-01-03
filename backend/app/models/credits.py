"""
Credit System Models

Manages user credits for PACER document purchases and other services.

Pricing Model:
- Document downloads: $0.25 per page (1 credit = 1 page)
- Credits can be purchased via credit packs or included in subscription tiers
- Free documents from RECAP/Internet Archive cost 0 credits
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..src.core.database import Base


class TransactionType(str, enum.Enum):
    """Types of credit transactions"""
    CREDIT_PURCHASE = "credit_purchase"  # User buys credit pack
    SUBSCRIPTION_CREDITS = "subscription_credits"  # Monthly credits from subscription
    DOCUMENT_PURCHASE = "document_purchase"  # User downloads document (costs credits)
    REFUND = "refund"  # Credit refund
    ADMIN_ADJUSTMENT = "admin_adjustment"  # Admin adds/removes credits
    BONUS = "bonus"  # Promotional bonus credits
    ROLLOVER = "rollover"  # Credits rolled over from previous period (if allowed)
    EXPIRED = "expired"  # Credits expired (subscription credits don't roll over)


class CreditPackType(str, enum.Enum):
    """Available credit pack types for pay-as-you-go purchases"""
    SINGLE_PAGE = "single_page"  # 1 credit @ $0.35
    STARTER = "starter"  # 25 credits @ $6.25 ($0.25/credit)
    STANDARD = "standard"  # 50 credits @ $11.00 ($0.22/credit)
    VALUE = "value"  # 100 credits @ $20.00 ($0.20/credit)
    PRO = "pro"  # 250 credits @ $45.00 ($0.18/credit)
    POWER = "power"  # 500 credits @ $80.00 ($0.16/credit)


class UserCredits(Base):
    """
    User credit balance tracking.

    Each user has a credit balance that can be used to purchase documents.
    1 credit = 1 page of document download
    Document price: $0.25 per page
    """
    __tablename__ = "user_credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    username = Column(String, nullable=False, index=True)

    # Credit balance (1 credit = 1 page)
    balance = Column(Integer, default=0, nullable=False)

    # Subscription credits (reset monthly, don't roll over by default)
    subscription_credits = Column(Integer, default=0)  # Credits from current subscription period
    subscription_credits_used = Column(Integer, default=0)  # How many subscription credits used this period

    # Purchased credits (these roll over indefinitely)
    purchased_credits = Column(Integer, default=0)  # Credits purchased via credit packs

    # Lifetime totals
    total_credits_purchased = Column(Integer, default=0)  # Total credits ever purchased
    total_credits_from_subscription = Column(Integer, default=0)  # Total credits from subscriptions
    total_credits_spent = Column(Integer, default=0)  # Total credits spent on documents
    total_pages_downloaded = Column(Integer, default=0)  # Total pages downloaded
    total_amount_spent = Column(Numeric(10, 2), default=0)  # Total $ spent on credit packs

    # Current subscription period
    subscription_period_start = Column(DateTime, nullable=True)
    subscription_period_end = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = relationship("CreditTransaction", back_populates="user_credits", cascade="all, delete-orphan")
    purchases = relationship("DocumentPurchase", back_populates="user_credits", cascade="all, delete-orphan")
    credit_pack_purchases = relationship("CreditPackPurchase", back_populates="user_credits", cascade="all, delete-orphan")


class CreditTransaction(Base):
    """
    Credit transaction history.

    Records all credit additions and deductions.
    """
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_credits_id = Column(Integer, ForeignKey("user_credits.id"), nullable=False, index=True)

    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Positive for additions, negative for deductions (in credits)
    balance_after = Column(Integer, nullable=False)  # Balance after transaction

    # For credit pack purchases
    credit_pack_type = Column(SQLEnum(CreditPackType), nullable=True)  # Which pack was purchased
    cash_amount = Column(Numeric(10, 2), nullable=True)  # Amount paid in USD

    # Description and metadata
    description = Column(String, nullable=True)
    extra_data = Column(String, nullable=True)  # JSON string for additional data

    # Payment information (for credit purchases)
    payment_method = Column(String, nullable=True)  # e.g., "stripe", "paypal", "admin"
    payment_id = Column(String, nullable=True)  # External payment reference

    # Related purchases (if applicable)
    document_purchase_id = Column(Integer, ForeignKey("document_purchases.id"), nullable=True)
    credit_pack_purchase_id = Column(Integer, ForeignKey("credit_pack_purchases.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user_credits = relationship("UserCredits", back_populates="transactions")
    document_purchase = relationship("DocumentPurchase", back_populates="transaction", foreign_keys=[document_purchase_id])
    credit_pack_purchase = relationship("CreditPackPurchase", back_populates="transaction", foreign_keys=[credit_pack_purchase_id])


class DocumentPurchase(Base):
    """
    Record of document downloads.

    Tracks documents downloaded through credits.
    Pricing: $0.25 per page (1 credit = 1 page)
    """
    __tablename__ = "document_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_credits_id = Column(Integer, ForeignKey("user_credits.id"), nullable=False, index=True)

    # Document identification
    document_id = Column(String, nullable=True)  # CourtListener/PACER document ID
    docket_id = Column(String, nullable=True)  # Docket ID
    court = Column(String, nullable=True)  # Court identifier
    case_number = Column(String, nullable=True)
    document_number = Column(Integer, nullable=True)

    # Page and credit details
    page_count = Column(Integer, nullable=False, default=0)  # Number of pages
    credits_used = Column(Integer, nullable=False, default=0)  # Credits consumed (= page_count for paid docs)
    price_per_page = Column(Numeric(10, 2), default=0.25)  # $0.25 per page
    total_price = Column(Numeric(10, 2), nullable=True)  # Total dollar value

    # Source tracking
    is_free = Column(Boolean, default=False)  # True if from RECAP/Internet Archive
    source = Column(String, nullable=True)  # "recap", "internet_archive", "pacer"
    our_cost = Column(Numeric(10, 2), nullable=True)  # Our actual cost (for margin tracking)

    # Purchase status
    status = Column(String, default="pending", index=True)  # pending, processing, completed, failed
    recap_fetch_id = Column(Integer, nullable=True)  # CourtListener RECAP Fetch request ID

    # Document storage
    file_path = Column(String, nullable=True)  # Local file path after download
    file_size = Column(Integer, nullable=True)  # File size in bytes

    # Metadata
    description = Column(String, nullable=True)  # Document description
    error_message = Column(String, nullable=True)  # Error if purchase failed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user_credits = relationship("UserCredits", back_populates="purchases")
    transaction = relationship("CreditTransaction", back_populates="document_purchase", foreign_keys="CreditTransaction.document_purchase_id")


class CreditPackPurchase(Base):
    """
    Record of credit pack purchases.

    Tracks when users buy credit packs.
    """
    __tablename__ = "credit_pack_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_credits_id = Column(Integer, ForeignKey("user_credits.id"), nullable=False, index=True)

    # Pack details
    pack_type = Column(SQLEnum(CreditPackType), nullable=False)
    pack_name = Column(String, nullable=False)
    credits_purchased = Column(Integer, nullable=False)
    price_paid = Column(Numeric(10, 2), nullable=False)
    price_per_credit = Column(Numeric(10, 4), nullable=False)

    # Payment details
    payment_method = Column(String, nullable=True)  # "stripe", "paypal"
    stripe_payment_intent_id = Column(String, nullable=True)
    stripe_charge_id = Column(String, nullable=True)

    # Status
    status = Column(String, default="pending", index=True)  # pending, completed, failed, refunded
    error_message = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user_credits = relationship("UserCredits", back_populates="credit_pack_purchases")
    transaction = relationship("CreditTransaction", back_populates="credit_pack_purchase", foreign_keys="CreditTransaction.credit_pack_purchase_id")
