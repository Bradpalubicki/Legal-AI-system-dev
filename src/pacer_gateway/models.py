"""
PACER Gateway Data Models

Defines data structures for PACER operations including accounts, documents,
cases, dockets, and billing information.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, field
import uuid


class CourtType(Enum):
    """Federal court types"""
    DISTRICT = "district"
    BANKRUPTCY = "bankruptcy"
    APPELLATE = "appellate"
    SUPREME = "supreme"


class DocumentType(Enum):
    """PACER document types"""
    DOCKET_ENTRY = "docket_entry"
    COMPLAINT = "complaint"
    MOTION = "motion"
    ORDER = "order"
    JUDGMENT = "judgment"
    BRIEF = "brief"
    TRANSCRIPT = "transcript"
    EXHIBIT = "exhibit"
    OTHER = "other"


class CaseStatus(Enum):
    """Case status in PACER"""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    DISMISSED = "dismissed"
    TERMINATED = "terminated"


class PartyType(Enum):
    """Party types in legal cases"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    APPELLANT = "appellant"
    APPELLEE = "appellee"
    INTERVENOR = "intervenor"
    AMICUS = "amicus"
    THIRD_PARTY = "third_party"


class AccountStatus(Enum):
    """PACER account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    EXPIRED = "expired"


class RequestStatus(Enum):
    """Request processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RATE_LIMITED = "rate_limited"


@dataclass
class CourtInfo:
    """Federal court information"""
    court_id: str
    court_name: str
    court_type: CourtType
    district: str
    state: str
    pacer_url: str
    cm_ecf_url: Optional[str] = None
    timezone: str = "UTC"
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PacerAccount:
    """PACER account credentials and configuration"""
    account_id: str
    username: str
    password: str  # Should be encrypted in storage
    client_code: str
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
    daily_limit_dollars: float = 100.0
    monthly_limit_dollars: float = 3000.0
    auto_renew: bool = True
    allowed_courts: List[str] = field(default_factory=list)  # Empty = all courts
    rate_limit_per_hour: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if account is active and usable"""
        return self.status == AccountStatus.ACTIVE
    
    def can_access_court(self, court_id: str) -> bool:
        """Check if account can access specific court"""
        if not self.allowed_courts:
            return True  # No restrictions
        return court_id in self.allowed_courts


@dataclass
class Party:
    """Case party information"""
    party_id: Optional[str] = None
    name: str = ""
    party_type: Optional[PartyType] = None
    attorney_name: Optional[str] = None
    attorney_firm: Optional[str] = None
    attorney_phone: Optional[str] = None
    attorney_email: Optional[str] = None
    is_pro_se: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseInfo:
    """Federal case information"""
    case_number: str
    case_title: str
    court_id: str
    court_name: str
    court_type: CourtType
    judge_name: Optional[str] = None
    filing_date: Optional[datetime] = None
    case_status: Optional[CaseStatus] = None
    nature_of_suit: Optional[str] = None
    cause_of_action: Optional[str] = None
    parties: List[Party] = field(default_factory=list)
    docket_entries_count: int = 0
    last_filing_date: Optional[datetime] = None
    pacer_case_id: Optional[str] = None
    cm_ecf_case_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocketEntry:
    """PACER docket entry"""
    entry_number: str
    date_filed: datetime
    description: str
    case_number: str
    court_id: str
    document_count: int = 0
    page_count: Optional[int] = None
    cost_cents: int = 0  # Cost in cents
    pacer_doc_id: Optional[str] = None
    pacer_seq_no: Optional[str] = None
    is_available: bool = True
    is_restricted: bool = False
    document_type: Optional[DocumentType] = None
    filing_party: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentInfo:
    """PACER document information"""
    document_id: str
    case_number: str
    court_id: str
    entry_number: str
    document_number: str
    attachment_number: Optional[str] = None
    description: str = ""
    date_filed: Optional[datetime] = None
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    cost_cents: int = 0
    pacer_doc_id: Optional[str] = None
    pacer_de_seq_num: Optional[str] = None
    document_type: Optional[DocumentType] = None
    is_available: bool = True
    is_free: bool = False
    filename: Optional[str] = None
    content_type: str = "application/pdf"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchCriteria:
    """Search criteria for PACER searches"""
    case_number: Optional[str] = None
    case_title: Optional[str] = None
    party_name: Optional[str] = None
    attorney_name: Optional[str] = None
    judge_name: Optional[str] = None
    nature_of_suit: Optional[str] = None
    cause_of_action: Optional[str] = None
    date_filed_from: Optional[datetime] = None
    date_filed_to: Optional[datetime] = None
    date_terminated_from: Optional[datetime] = None
    date_terminated_to: Optional[datetime] = None
    case_status: Optional[CaseStatus] = None
    court_ids: List[str] = field(default_factory=list)
    max_results: int = 100
    include_closed_cases: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BillingRecord:
    """PACER billing record"""
    billing_id: str
    account_id: str
    transaction_date: datetime
    court_id: str
    case_number: Optional[str] = None
    description: str = ""
    cost_cents: int = 0
    page_count: Optional[int] = None
    document_count: int = 0
    request_id: Optional[str] = None
    pacer_transaction_id: Optional[str] = None
    billable_pages: int = 0  # Pages that actually cost money
    free_pages: int = 0     # Free pages (first 30 per document)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def cost_dollars(self) -> float:
        """Get cost in dollars"""
        return self.cost_cents / 100.0


@dataclass
class UsageStatistics:
    """PACER usage statistics"""
    account_id: str
    date: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost_cents: int = 0
    total_pages: int = 0
    total_documents: int = 0
    unique_cases_accessed: int = 0
    courts_accessed: List[str] = field(default_factory=list)
    peak_requests_per_hour: int = 0
    average_response_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_cost_dollars(self) -> float:
        """Get total cost in dollars"""
        return self.total_cost_cents / 100.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0


@dataclass
class RequestLog:
    """PACER request log entry"""
    request_id: str
    account_id: str
    timestamp: datetime
    court_id: str
    request_type: str  # search, docket, document, etc.
    case_number: Optional[str] = None
    status: RequestStatus = RequestStatus.PENDING
    response_time_ms: Optional[float] = None
    cost_cents: int = 0
    page_count: Optional[int] = None
    document_count: int = 0
    error_message: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())


@dataclass
class CostAlert:
    """Cost alert configuration and tracking"""
    alert_id: str
    account_id: str
    alert_type: str  # daily, monthly, per_request, per_case
    threshold_cents: int
    current_amount_cents: int = 0
    is_active: bool = True
    is_triggered: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered_at: Optional[datetime] = None
    notification_email: Optional[str] = None
    auto_suspend: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def threshold_dollars(self) -> float:
        """Get threshold in dollars"""
        return self.threshold_cents / 100.0
    
    @property
    def current_amount_dollars(self) -> float:
        """Get current amount in dollars"""
        return self.current_amount_cents / 100.0
    
    def check_threshold(self) -> bool:
        """Check if threshold has been exceeded"""
        return self.current_amount_cents >= self.threshold_cents


@dataclass
class QueuedRequest:
    """Queued PACER request for batch processing"""
    request_id: str
    account_id: str
    priority: int  # Higher number = higher priority
    request_type: str
    request_data: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: RequestStatus = RequestStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
    
    def can_retry(self) -> bool:
        """Check if request can be retried"""
        return self.retry_count < self.max_retries and self.status == RequestStatus.FAILED


# Court data - major federal courts
FEDERAL_COURTS = {
    # District Courts (examples)
    "nysd": CourtInfo(
        court_id="nysd",
        court_name="Southern District of New York",
        court_type=CourtType.DISTRICT,
        district="Southern District",
        state="New York",
        pacer_url="https://ecf.nysd.uscourts.gov",
        cm_ecf_url="https://ecf.nysd.uscourts.gov"
    ),
    "cacd": CourtInfo(
        court_id="cacd",
        court_name="Central District of California",
        court_type=CourtType.DISTRICT,
        district="Central District",
        state="California",
        pacer_url="https://ecf.cacd.uscourts.gov",
        cm_ecf_url="https://ecf.cacd.uscourts.gov"
    ),
    "dcd": CourtInfo(
        court_id="dcd",
        court_name="District of Columbia",
        court_type=CourtType.DISTRICT,
        district="District of Columbia",
        state="District of Columbia",
        pacer_url="https://ecf.dcd.uscourts.gov",
        cm_ecf_url="https://ecf.dcd.uscourts.gov"
    ),
    
    # Bankruptcy Courts (examples)  
    "nysb": CourtInfo(
        court_id="nysb",
        court_name="Southern District of New York Bankruptcy",
        court_type=CourtType.BANKRUPTCY,
        district="Southern District",
        state="New York",
        pacer_url="https://ecf.nysb.uscourts.gov",
        cm_ecf_url="https://ecf.nysb.uscourts.gov"
    ),
    "cacb": CourtInfo(
        court_id="cacb",
        court_name="Central District of California Bankruptcy",
        court_type=CourtType.BANKRUPTCY,
        district="Central District", 
        state="California",
        pacer_url="https://ecf.cacb.uscourts.gov",
        cm_ecf_url="https://ecf.cacb.uscourts.gov"
    ),
    
    # Appellate Courts
    "ca2": CourtInfo(
        court_id="ca2",
        court_name="Second Circuit Court of Appeals",
        court_type=CourtType.APPELLATE,
        district="Second Circuit",
        state="Multi-state",
        pacer_url="https://ecf.ca2.uscourts.gov",
        cm_ecf_url="https://ecf.ca2.uscourts.gov"
    ),
    "ca9": CourtInfo(
        court_id="ca9", 
        court_name="Ninth Circuit Court of Appeals",
        court_type=CourtType.APPELLATE,
        district="Ninth Circuit",
        state="Multi-state",
        pacer_url="https://ecf.ca9.uscourts.gov",
        cm_ecf_url="https://ecf.ca9.uscourts.gov"
    )
}


# PACER pricing (as of 2024)
PACER_PRICING = {
    "per_page_cents": 10,  # 10 cents per page
    "free_pages_per_document": 30,  # First 30 pages free
    "search_fee_cents": 30,  # 30 cents per search
    "docket_sheet_fee_cents": 0,  # Docket sheets are free
    "quarterly_spending_cap_cents": 3000,  # $30 quarterly cap per user
}


def get_court_info(court_id: str) -> Optional[CourtInfo]:
    """Get court information by court ID"""
    return FEDERAL_COURTS.get(court_id.lower())


def get_courts_by_type(court_type: CourtType) -> List[CourtInfo]:
    """Get all courts of a specific type"""
    return [court for court in FEDERAL_COURTS.values() if court.court_type == court_type]


def get_courts_by_state(state: str) -> List[CourtInfo]:
    """Get all courts in a specific state"""
    return [court for court in FEDERAL_COURTS.values() if court.state.lower() == state.lower()]


def calculate_document_cost(page_count: int) -> int:
    """Calculate cost for a document in cents"""
    if page_count <= PACER_PRICING["free_pages_per_document"]:
        return 0
    
    billable_pages = page_count - PACER_PRICING["free_pages_per_document"]
    return billable_pages * PACER_PRICING["per_page_cents"]


def format_case_number(case_number: str, court_type: CourtType) -> str:
    """Format case number according to court conventions"""
    # This is a simplified version - real implementation would be more complex
    case_number = case_number.strip().upper()
    
    if court_type == CourtType.BANKRUPTCY:
        # Bankruptcy case numbers typically have format: YY-NNNNN-SSS
        if not case_number.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
            return case_number
    
    return case_number