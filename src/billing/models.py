"""
Data models for billing and cost tracking system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import uuid


class CostType(Enum):
    """Types of costs that can be tracked."""
    PACER_SEARCH = "pacer_search"
    PACER_DOCUMENT = "pacer_document"
    PACER_DOCKET = "pacer_docket"
    PACER_REPORT = "pacer_report"
    WESTLAW_SEARCH = "westlaw_search"
    WESTLAW_DOCUMENT = "westlaw_document"
    LEXIS_SEARCH = "lexis_search"
    LEXIS_DOCUMENT = "lexis_document"
    COURT_FILING_FEE = "court_filing_fee"
    SERVICE_FEE = "service_fee"
    EXPERT_WITNESS = "expert_witness"
    TRAVEL_EXPENSE = "travel_expense"
    PRINTING_COPYING = "printing_copying"
    POSTAGE_DELIVERY = "postage_delivery"
    TRANSLATION = "translation"
    COURT_REPORTER = "court_reporter"
    PROCESS_SERVER = "process_server"
    INVESTIGATION = "investigation"
    OTHER = "other"


class AllocationMethod(Enum):
    """Methods for allocating costs to clients."""
    DIRECT = "direct"                    # Direct assignment to specific client
    PROPORTIONAL = "proportional"        # Based on case value or time
    EQUAL_SPLIT = "equal_split"          # Split equally among clients
    TIME_BASED = "time_based"            # Based on attorney time allocation
    CUSTOM = "custom"                    # Custom allocation rules
    OVERHEAD = "overhead"                # Firm overhead, not billable


class BillingStatus(Enum):
    """Status of billing items and invoices."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    WRITTEN_OFF = "written_off"


class PaymentMethod(Enum):
    """Payment methods for invoices."""
    CHECK = "check"
    WIRE_TRANSFER = "wire_transfer"
    CREDIT_CARD = "credit_card"
    ACH = "ach"
    CASH = "cash"
    ESCROW = "escrow"
    RETAINER = "retainer"
    OTHER = "other"


@dataclass
class BillingAccount:
    """Client billing account information."""
    account_id: str
    client_id: str
    client_name: str
    matter_number: Optional[str]
    matter_description: Optional[str]
    
    # Billing configuration
    billing_contact: str
    billing_email: str
    billing_address: Dict[str, str]
    payment_terms: int  # days
    preferred_payment_method: PaymentMethod
    
    # Rate information
    hourly_rates: Dict[str, Decimal] = field(default_factory=dict)  # role -> rate
    markup_percentage: Decimal = Decimal('0.0')
    discount_percentage: Decimal = Decimal('0.0')
    
    # Budget and limits
    budget_limit: Optional[Decimal] = None
    cost_limit: Optional[Decimal] = None
    approval_required_threshold: Optional[Decimal] = None
    
    # Account status
    is_active: bool = True
    credit_limit: Optional[Decimal] = None
    current_balance: Decimal = Decimal('0.0')
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class TaxRate:
    """Tax rate configuration."""
    tax_id: str
    name: str
    rate: Decimal
    jurisdiction: str
    tax_type: str  # sales, vat, service, etc.
    applicable_services: List[str] = field(default_factory=list)
    effective_from: date = field(default_factory=date.today)
    effective_to: Optional[date] = None
    is_active: bool = True


@dataclass
class DiscountRule:
    """Discount rule configuration."""
    rule_id: str
    name: str
    description: str
    discount_type: str  # percentage, fixed_amount, bulk_discount
    discount_value: Decimal
    
    # Conditions
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    applicable_cost_types: List[CostType] = field(default_factory=list)
    applicable_clients: List[str] = field(default_factory=list)
    
    # Time constraints
    effective_from: date = field(default_factory=date.today)
    effective_to: Optional[date] = None
    
    # Usage limits
    max_uses: Optional[int] = None
    current_uses: int = 0
    
    is_active: bool = True


@dataclass
class BillingMetrics:
    """Billing performance metrics."""
    period_start: date
    period_end: date
    
    # Revenue metrics
    total_revenue: Decimal
    billable_costs: Decimal
    non_billable_costs: Decimal
    markup_revenue: Decimal
    
    # Cost breakdown
    pacer_costs: Decimal
    research_costs: Decimal
    court_costs: Decimal
    other_costs: Decimal
    
    # Client metrics
    total_clients: int
    active_clients: int
    new_clients: int
    
    # Invoice metrics
    invoices_sent: int
    invoices_paid: int
    average_payment_days: float
    overdue_amount: Decimal
    
    # Efficiency metrics
    cost_recovery_rate: float  # percentage of costs recovered
    markup_rate: float         # average markup applied
    discount_rate: float       # average discount given
    
    # PACER specific metrics
    pacer_searches: int
    pacer_documents: int
    pacer_cost_per_search: Decimal
    pacer_cost_per_document: Decimal
    
    calculated_at: datetime = field(default_factory=datetime.utcnow)


def generate_billing_id() -> str:
    """Generate unique billing ID."""
    return f"BILL-{uuid.uuid4().hex[:8].upper()}"


def generate_invoice_number(prefix: str = "INV") -> str:
    """Generate invoice number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"


def calculate_tax_amount(base_amount: Decimal, tax_rate: TaxRate) -> Decimal:
    """Calculate tax amount for given base amount."""
    return base_amount * (tax_rate.rate / Decimal('100'))


def apply_discount(amount: Decimal, discount_rule: DiscountRule) -> Decimal:
    """Apply discount rule to amount."""
    if not discount_rule.is_active:
        return Decimal('0.0')
    
    if discount_rule.min_amount and amount < discount_rule.min_amount:
        return Decimal('0.0')
    
    if discount_rule.max_amount and amount > discount_rule.max_amount:
        return Decimal('0.0')
    
    if discount_rule.discount_type == "percentage":
        return amount * (discount_rule.discount_value / Decimal('100'))
    elif discount_rule.discount_type == "fixed_amount":
        return min(discount_rule.discount_value, amount)
    else:
        return Decimal('0.0')


def calculate_markup(base_amount: Decimal, markup_percentage: Decimal) -> Decimal:
    """Calculate markup amount."""
    return base_amount * (markup_percentage / Decimal('100'))


class PACERCostType(Enum):
    """Specific PACER cost types."""
    SEARCH = "search"              # $0.10 per search
    DOCUMENT_VIEW = "document_view" # $0.10 per page
    DOCKET_REPORT = "docket_report" # $0.10 per page
    CASE_SUMMARY = "case_summary"   # $0.10 per page
    PARTY_SEARCH = "party_search"   # $0.10 per search
    DOWNLOAD_FEE = "download_fee"   # Additional fees
    QUARTERLY_EXEMPTION = "quarterly_exemption"  # First $30 free


@dataclass 
class PACERRates:
    """Current PACER fee rates."""
    search_fee: Decimal = Decimal('0.10')
    page_fee: Decimal = Decimal('0.10')
    quarterly_exemption: Decimal = Decimal('30.00')
    max_document_fee: Decimal = Decimal('3.00')  # Max fee per document
    
    # Updated rates (PACER changes rates periodically)
    effective_date: date = field(default_factory=date.today)
    
    @classmethod
    def get_current_rates(cls) -> 'PACERRates':
        """Get current PACER rates."""
        # In production, this would fetch from a configuration service
        return cls()
    
    def calculate_search_cost(self, search_count: int) -> Decimal:
        """Calculate cost for PACER searches."""
        return Decimal(str(search_count)) * self.search_fee
    
    def calculate_document_cost(self, page_count: int) -> Decimal:
        """Calculate cost for PACER document viewing."""
        base_cost = Decimal(str(page_count)) * self.page_fee
        return min(base_cost, self.max_document_fee)
    
    def calculate_docket_cost(self, page_count: int) -> Decimal:
        """Calculate cost for PACER docket reports."""
        return Decimal(str(page_count)) * self.page_fee
    
    def apply_quarterly_exemption(self, total_cost: Decimal, used_exemption: Decimal) -> Tuple[Decimal, Decimal]:
        """Apply quarterly exemption and return (final_cost, exemption_used)."""
        available_exemption = self.quarterly_exemption - used_exemption
        
        if available_exemption <= 0:
            return total_cost, Decimal('0.0')
        
        exemption_applied = min(total_cost, available_exemption)
        final_cost = total_cost - exemption_applied
        
        return final_cost, exemption_applied


def get_cost_type_display_name(cost_type: CostType) -> str:
    """Get human-readable display name for cost type."""
    display_names = {
        CostType.PACER_SEARCH: "PACER Search",
        CostType.PACER_DOCUMENT: "PACER Document", 
        CostType.PACER_DOCKET: "PACER Docket Report",
        CostType.PACER_REPORT: "PACER Report",
        CostType.WESTLAW_SEARCH: "Westlaw Search",
        CostType.WESTLAW_DOCUMENT: "Westlaw Document",
        CostType.LEXIS_SEARCH: "Lexis Search", 
        CostType.LEXIS_DOCUMENT: "Lexis Document",
        CostType.COURT_FILING_FEE: "Court Filing Fee",
        CostType.SERVICE_FEE: "Service Fee",
        CostType.EXPERT_WITNESS: "Expert Witness",
        CostType.TRAVEL_EXPENSE: "Travel Expense",
        CostType.PRINTING_COPYING: "Printing & Copying",
        CostType.POSTAGE_DELIVERY: "Postage & Delivery",
        CostType.TRANSLATION: "Translation Services",
        CostType.COURT_REPORTER: "Court Reporter",
        CostType.PROCESS_SERVER: "Process Server",
        CostType.INVESTIGATION: "Investigation",
        CostType.OTHER: "Other"
    }
    
    return display_names.get(cost_type, cost_type.value.replace('_', ' ').title())


def is_pacer_cost_type(cost_type: CostType) -> bool:
    """Check if cost type is PACER-related."""
    pacer_types = {
        CostType.PACER_SEARCH,
        CostType.PACER_DOCUMENT,
        CostType.PACER_DOCKET,
        CostType.PACER_REPORT
    }
    return cost_type in pacer_types


def get_default_allocation_method(cost_type: CostType) -> AllocationMethod:
    """Get default allocation method for cost type."""
    if is_pacer_cost_type(cost_type):
        return AllocationMethod.DIRECT  # PACER costs are usually direct
    elif cost_type in [CostType.COURT_FILING_FEE, CostType.SERVICE_FEE]:
        return AllocationMethod.DIRECT
    elif cost_type in [CostType.EXPERT_WITNESS, CostType.COURT_REPORTER]:
        return AllocationMethod.DIRECT
    else:
        return AllocationMethod.TIME_BASED  # Default to time-based allocation