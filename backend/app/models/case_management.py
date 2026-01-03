"""
Case Management Models - Comprehensive Legal Case Tracking System
Designed for complex litigation, bankruptcy, and multi-party cases
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from ..src.core.database import Base


# ============================================================================
# ENUMS - Define valid values for status fields
# ============================================================================

class CaseStatus(str, Enum):
    """Case lifecycle status"""
    INTAKE = "intake"
    ACTIVE = "active"
    PENDING = "pending"
    STAYED = "stayed"
    CLOSED = "closed"
    DISMISSED = "dismissed"
    SETTLED = "settled"
    APPEALED = "appealed"


class CaseType(str, Enum):
    """Type of legal case"""
    BANKRUPTCY_CH7 = "bankruptcy_ch7"
    BANKRUPTCY_CH11 = "bankruptcy_ch11"
    BANKRUPTCY_CH13 = "bankruptcy_ch13"
    CIVIL_LITIGATION = "civil_litigation"
    DEBT_COLLECTION = "debt_collection"
    FORECLOSURE = "foreclosure"
    EVICTION = "eviction"
    CRIMINAL = "criminal"
    EMPLOYMENT = "employment"
    CONTRACT_DISPUTE = "contract_dispute"
    OTHER = "other"


class PartyRole(str, Enum):
    """Role of party in case"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    DEBTOR = "debtor"
    CREDITOR = "creditor"
    TRUSTEE = "trustee"
    ATTORNEY = "attorney"
    JUDGE = "judge"
    WITNESS = "witness"
    EXPERT = "expert"
    MEDIATOR = "mediator"
    BIDDER = "bidder"
    OTHER = "other"


class EventType(str, Enum):
    """Type of timeline event"""
    FILING = "filing"
    HEARING = "hearing"
    DEADLINE = "deadline"
    MEETING = "meeting"
    OBJECTION = "objection"
    MOTION = "motion"
    ORDER = "order"
    PAYMENT = "payment"
    AUCTION = "auction"
    CONFIRMATION = "confirmation"
    DISCHARGE = "discharge"
    OTHER = "other"


class EventStatus(str, Enum):
    """Status of timeline event"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    MISSED = "missed"


class TransactionType(str, Enum):
    """Type of financial transaction"""
    PAYMENT = "payment"
    DISTRIBUTION = "distribution"
    FEE = "fee"
    DEPOSIT = "deposit"
    REFUND = "refund"
    BID = "bid"
    TRANSFER = "transfer"
    ESCROW = "escrow"


class AssetStatus(str, Enum):
    """Status of asset in case"""
    INCLUDED = "included"
    EXCLUDED = "excluded"
    PENDING = "pending"
    SOLD = "sold"
    ABANDONED = "abandoned"
    EXEMPT = "exempt"


class ObjectionStatus(str, Enum):
    """Status of objection"""
    FILED = "filed"
    PENDING = "pending"
    OVERRULED = "overruled"
    SUSTAINED = "sustained"
    WITHDRAWN = "withdrawn"
    RESOLVED = "resolved"


# ============================================================================
# CORE MODELS
# ============================================================================

class LegalCase(Base):
    """
    Main case entity - represents a legal case/matter
    Central hub for all case-related information
    Comprehensive case management for complex litigation/bankruptcy
    """
    __tablename__ = "legal_cases"

    id = Column(String(36), primary_key=True)  # UUID

    # Basic Case Information
    case_number = Column(String(100), unique=True, nullable=False, index=True)
    case_name = Column(String(500), nullable=False)
    case_type = Column(SQLEnum(CaseType), nullable=False, index=True)
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.ACTIVE, nullable=False, index=True)

    # Court Information
    court_name = Column(String(300))
    jurisdiction = Column(String(200))
    judge_name = Column(String(200))
    court_division = Column(String(100))

    # Important Dates
    filing_date = Column(DateTime, index=True)
    status_date = Column(DateTime)  # Date of last status change
    close_date = Column(DateTime)

    # Case Details
    description = Column(Text)
    current_phase = Column(String(100))  # e.g., "Discovery", "Trial", "Post-Judgment"
    estimated_completion_date = Column(DateTime)

    # Related/Consolidated Cases
    parent_case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=True)
    related_case_ids = Column(JSON)  # Array of case IDs

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36))  # User ID
    is_deleted = Column(Boolean, default=False)

    # Additional Data
    notes = Column(Text)
    tags = Column(JSON)  # Array of tags for filtering
    custom_fields = Column(JSON)  # Flexible custom data

    # Relationships
    parties = relationship("CaseParty", back_populates="legal_case", cascade="all, delete-orphan")
    documents = relationship("LegalCaseDocument", back_populates="legal_case", cascade="all, delete-orphan")
    timeline_events = relationship("CaseTimelineEvent", back_populates="legal_case", cascade="all, delete-orphan")
    financial_transactions = relationship("CaseFinancialTransaction", back_populates="legal_case", cascade="all, delete-orphan")
    assets = relationship("CaseAsset", back_populates="legal_case", cascade="all, delete-orphan")
    bidding_processes = relationship("CaseBiddingProcess", back_populates="legal_case", cascade="all, delete-orphan")
    objections = relationship("CaseObjection", back_populates="legal_case", cascade="all, delete-orphan")
    # parent_case = relationship("LegalCase", remote_side=[id], backref="child_cases")  # Temporarily disabled - id reference issue


class CaseParty(Base):
    """
    Parties involved in a case - plaintiffs, defendants, creditors, attorneys, etc.
    Tracks roles, contact information, and authorization levels
    """
    __tablename__ = "case_parties"

    id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=False, index=True)

    # Party Information
    party_type = Column(String(50))  # "individual", "corporation", "government", etc.
    role = Column(SQLEnum(PartyRole), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    legal_name = Column(String(500))  # Full legal name if different

    # Contact Information
    email = Column(String(300))
    phone = Column(String(50))
    address = Column(Text)

    # Representation
    represented_by = Column(String(36))  # Attorney party ID
    attorney_firm = Column(String(300))
    bar_number = Column(String(100))

    # Claims and Interests
    claims_held = Column(JSON)  # Array of claim objects
    interest_amount = Column(Numeric(15, 2))
    interest_description = Column(Text)
    priority_level = Column(Integer)  # For creditor priority

    # Authorization and Access
    authorization_level = Column(String(50))  # "full", "limited", "view_only"
    can_receive_notices = Column(Boolean, default=True)
    can_file_documents = Column(Boolean, default=False)
    can_bid = Column(Boolean, default=False)

    # Communication Preferences
    preferred_contact_method = Column(String(50))  # "email", "phone", "mail"
    language_preference = Column(String(50))
    communication_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    custom_fields = Column(JSON)

    # Relationships
    legal_case = relationship("LegalCase", back_populates="parties")
    timeline_events = relationship("CaseTimelineEvent", secondary="case_event_parties", back_populates="responsible_parties")
    financial_transactions = relationship("CaseFinancialTransaction", foreign_keys="CaseFinancialTransaction.party_id", back_populates="party")


class LegalCaseDocument(Base):
    """
    Junction table linking Documents to Cases with additional metadata
    Tracks document role in case, deadlines triggered, and dependencies
    """
    __tablename__ = "legal_case_documents"

    id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey('documents.id'), nullable=False, index=True)

    # Document Role in Case
    document_role = Column(String(100))  # "complaint", "motion", "evidence", "order", etc.
    filing_date = Column(DateTime, index=True)
    filed_by_party_id = Column(String(36), ForeignKey('case_parties.id'))

    # Version Control
    version = Column(Integer, default=1)
    is_current_version = Column(Boolean, default=True)
    supersedes_document_id = Column(String(36))  # Previous version

    # Deadlines and Actions
    response_deadline = Column(DateTime)
    deadlines_triggered = Column(JSON)  # Array of deadline objects
    required_actions = Column(JSON)  # Array of action items

    # Dependencies
    depends_on_document_ids = Column(JSON)  # Must be filed after these
    prerequisite_for_document_ids = Column(JSON)  # Must be filed before these

    # Status
    status = Column(String(50))  # "filed", "pending", "served", "objected", etc.
    is_confidential = Column(Boolean, default=False)
    is_sealed = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)
    custom_fields = Column(JSON)

    # Relationships
    legal_case = relationship("LegalCase", back_populates="documents")
    filed_by = relationship("CaseParty", foreign_keys=[filed_by_party_id])


class CaseTimelineEvent(Base):
    """
    Timeline events - hearings, deadlines, filings, meetings
    Tracks dependencies, required actions, and completion status
    """
    __tablename__ = "case_timeline_events"

    id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=False, index=True)

    # Event Information
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Date and Time
    event_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime)  # For multi-day events
    is_all_day = Column(Boolean, default=False)
    timezone = Column(String(50), default="UTC")

    # Location
    location = Column(String(500))
    courtroom = Column(String(100))
    virtual_meeting_link = Column(String(1000))

    # Status and Progress
    status = Column(SQLEnum(EventStatus), default=EventStatus.SCHEDULED, nullable=False, index=True)
    completion_percentage = Column(Integer, default=0)
    completed_at = Column(DateTime)

    # Dependencies
    blocks_event_ids = Column(JSON)  # This event blocks these events
    blocked_by_event_ids = Column(JSON)  # This event is blocked by these events
    related_event_ids = Column(JSON)  # Related but not blocking

    # Required Actions
    required_actions = Column(JSON)  # Array of action items
    required_documents = Column(JSON)  # Array of document types needed
    required_parties = Column(JSON)  # Array of party IDs who must attend/act

    # Completion Criteria
    completion_criteria = Column(JSON)  # What defines completion
    deliverables = Column(JSON)  # Expected outputs

    # Notifications and Reminders
    reminder_dates = Column(JSON)  # Array of dates for reminders
    notification_sent = Column(Boolean, default=False)
    attendees_notified = Column(Boolean, default=False)

    # Result and Outcome
    outcome = Column(Text)
    minutes_notes = Column(Text)
    orders_issued = Column(JSON)  # Array of order details

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36))
    is_critical_path = Column(Boolean, default=False)  # Is this on critical path?
    priority_level = Column(Integer, default=3)  # 1=highest, 5=lowest
    custom_fields = Column(JSON)

    # Relationships
    legal_case = relationship("LegalCase", back_populates="timeline_events")
    responsible_parties = relationship("CaseParty", secondary="case_event_parties", back_populates="timeline_events")


class CaseFinancialTransaction(Base):
    """
    Financial transactions - payments, distributions, fees, deposits
    Tracks amounts, approval requirements, and distribution calculations
    """
    __tablename__ = "case_financial_transactions"

    id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=False, index=True)

    # Transaction Details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    effective_date = Column(DateTime)

    # Financial Information
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    check_number = Column(String(50))
    reference_number = Column(String(100))

    # Parties Involved
    party_id = Column(String(36), ForeignKey('case_parties.id'), index=True)  # Payer or payee
    from_party_id = Column(String(36), ForeignKey('case_parties.id'))
    to_party_id = Column(String(36), ForeignKey('case_parties.id'))

    # Description and Category
    description = Column(Text)
    category = Column(String(100))  # "administrative", "secured", "unsecured", etc.
    subcategory = Column(String(100))

    # Approval and Authorization
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String(36))  # User or party ID
    approval_date = Column(DateTime)
    approval_status = Column(String(50))  # "pending", "approved", "denied"

    # Distribution Calculations
    distribution_priority = Column(Integer)
    distribution_percentage = Column(Numeric(5, 2))
    calculated_amount = Column(Numeric(15, 2))
    calculation_method = Column(Text)

    # Payment Status
    payment_status = Column(String(50))  # "pending", "processed", "cleared", "failed"
    payment_method = Column(String(50))  # "check", "wire", "ach", "cash"
    cleared_date = Column(DateTime)

    # Related Items
    related_asset_id = Column(String(36), ForeignKey('case_assets.id'))
    related_event_id = Column(String(36), ForeignKey('case_timeline_events.id'))
    related_document_id = Column(String(36))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36))
    notes = Column(Text)
    custom_fields = Column(JSON)

    # Relationships
    legal_case = relationship("LegalCase", back_populates="financial_transactions")
    party = relationship("CaseParty", foreign_keys=[party_id], back_populates="financial_transactions")
    from_party = relationship("CaseParty", foreign_keys=[from_party_id])
    to_party = relationship("CaseParty", foreign_keys=[to_party_id])
    related_asset = relationship("CaseAsset", foreign_keys=[related_asset_id])


class CaseAsset(Base):
    """
    Assets in the case - property, accounts, contracts, intellectual property
    Tracks categories, inclusion/exclusion status, and valuations
    """
    __tablename__ = "case_assets"

    id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=False, index=True)

    # Asset Information
    asset_type = Column(String(100), nullable=False)  # "real_estate", "vehicle", "account", etc.
    category = Column(String(100))  # "secured", "unsecured", "exempt", etc.
    name = Column(String(500), nullable=False)
    description = Column(Text)

    # Location and Identification
    location = Column(String(500))
    identification_number = Column(String(200))  # VIN, account number, parcel ID, etc.

    # Status
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.PENDING, nullable=False, index=True)
    inclusion_reason = Column(Text)
    exclusion_reason = Column(Text)

    # Valuation
    estimated_value = Column(Numeric(15, 2))
    appraised_value = Column(Numeric(15, 2))
    market_value = Column(Numeric(15, 2))
    valuation_date = Column(DateTime)
    valuation_method = Column(String(100))

    # Liens and Encumbrances
    has_liens = Column(Boolean, default=False)
    lien_amount = Column(Numeric(15, 2))
    lien_holders = Column(JSON)  # Array of lien holder info
    encumbrances = Column(JSON)  # Array of encumbrance details

    # Associated Contracts
    has_contracts = Column(Boolean, default=False)
    contract_details = Column(JSON)  # Array of contract info
    ongoing_obligations = Column(JSON)

    # Disposition
    disposition_method = Column(String(100))  # "sale", "abandonment", "retention", etc.
    disposition_date = Column(DateTime)
    disposition_amount = Column(Numeric(15, 2))
    buyer_party_id = Column(String(36), ForeignKey('case_parties.id'))

    # Bidding Information
    minimum_bid = Column(Numeric(15, 2))
    current_high_bid = Column(Numeric(15, 2))
    reserve_price = Column(Numeric(15, 2))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36))
    notes = Column(Text)
    custom_fields = Column(JSON)
    attachments = Column(JSON)  # Array of document/image references

    # Relationships
    legal_case = relationship("LegalCase", back_populates="assets")
    buyer = relationship("CaseParty", foreign_keys=[buyer_party_id])
    bidding_processes = relationship("CaseBiddingProcess", back_populates="asset")


class CaseBiddingProcess(Base):
    """
    Bidding/auction process for asset sales
    Tracks qualified bidders, deposits, bids, and auction rules
    """
    __tablename__ = "case_bidding_processes"

    id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey('case_assets.id'), nullable=False, index=True)

    # Process Information
    process_name = Column(String(500))
    process_type = Column(String(50))  # "auction", "sealed_bid", "negotiated", etc.
    status = Column(String(50), default="open")  # "open", "closed", "cancelled"

    # Timeline
    announcement_date = Column(DateTime)
    bidding_start_date = Column(DateTime, index=True)
    bidding_end_date = Column(DateTime, index=True)
    sale_hearing_date = Column(DateTime)

    # Qualification Criteria
    qualified_bidder_criteria = Column(JSON)  # Requirements to bid
    requires_approval = Column(Boolean, default=True)
    approved_bidders = Column(JSON)  # Array of approved party IDs

    # Deposit Requirements
    deposit_required = Column(Boolean, default=True)
    deposit_amount = Column(Numeric(15, 2))
    deposit_percentage = Column(Numeric(5, 2))
    deposit_deadline = Column(DateTime)
    deposits_received = Column(JSON)  # Array of deposit records

    # Bidding Rules
    minimum_bid = Column(Numeric(15, 2))
    bid_increment = Column(Numeric(15, 2))
    reserve_price = Column(Numeric(15, 2))
    allows_credit_bid = Column(Boolean, default=False)
    credit_bid_rules = Column(JSON)

    # Protections and Contingencies
    breakup_fee = Column(Numeric(15, 2))
    expense_reimbursement = Column(Numeric(15, 2))
    stalking_horse_bidder_id = Column(String(36), ForeignKey('case_parties.id'))
    stalking_horse_protections = Column(JSON)

    # Bids Received
    bids = Column(JSON)  # Array of bid objects with timestamp, amount, bidder
    highest_bid_amount = Column(Numeric(15, 2))
    highest_bidder_id = Column(String(36), ForeignKey('case_parties.id'))

    # Evaluation and Selection
    evaluation_criteria = Column(JSON)
    evaluation_scores = Column(JSON)
    winning_bid_id = Column(String(36))
    winner_selected_date = Column(DateTime)

    # Results
    sale_approved = Column(Boolean)
    sale_approval_date = Column(DateTime)
    sale_closing_date = Column(DateTime)
    final_sale_price = Column(Numeric(15, 2))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36))
    notes = Column(Text)
    custom_fields = Column(JSON)

    # Relationships
    legal_case = relationship("LegalCase", back_populates="bidding_processes")
    asset = relationship("CaseAsset", back_populates="bidding_processes")
    stalking_horse_bidder = relationship("CaseParty", foreign_keys=[stalking_horse_bidder_id])
    highest_bidder = relationship("CaseParty", foreign_keys=[highest_bidder_id])


class CaseObjection(Base):
    """
    Objections filed in the case
    Tracks filing party, grounds, deadline, responses, and resolution
    """
    __tablename__ = "case_objections"

    id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(String(36), ForeignKey('legal_cases.id'), nullable=False, index=True)

    # Objection Details
    objection_type = Column(String(100))  # "claim", "plan", "sale", "disclosure", etc.
    title = Column(String(500), nullable=False)
    description = Column(Text)
    grounds = Column(Text)  # Legal basis for objection

    # Parties
    filed_by_party_id = Column(String(36), ForeignKey('case_parties.id'), nullable=False)
    objection_to_party_id = Column(String(36), ForeignKey('case_parties.id'))
    affected_parties = Column(JSON)  # Array of party IDs

    # Timeline
    filing_date = Column(DateTime, nullable=False, index=True)
    response_deadline = Column(DateTime, index=True)
    hearing_date = Column(DateTime)
    resolution_date = Column(DateTime)

    # Status and Resolution
    status = Column(SQLEnum(ObjectionStatus), default=ObjectionStatus.FILED, nullable=False, index=True)
    resolution = Column(Text)
    resolution_type = Column(String(50))  # "sustained", "overruled", "withdrawn", "settled"

    # Impact Assessment
    impact_on_timeline = Column(Text)  # How this affects case timeline
    blocks_event_ids = Column(JSON)  # Events blocked by this objection
    delays_days = Column(Integer)  # Estimated delay in days

    # Responses
    responses_required_from = Column(JSON)  # Array of party IDs
    responses_received = Column(JSON)  # Array of response records
    response_status = Column(String(50))  # "pending", "complete", "partial"

    # Related Items
    related_document_id = Column(String(36))
    related_event_id = Column(String(36), ForeignKey('case_timeline_events.id'))
    related_asset_id = Column(String(36), ForeignKey('case_assets.id'))

    # Legal Citations
    legal_authority = Column(Text)  # Cited laws, rules, cases
    precedent_cases = Column(JSON)  # Array of relevant case citations

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36))
    notes = Column(Text)
    custom_fields = Column(JSON)

    # Relationships
    legal_case = relationship("LegalCase", back_populates="objections")
    filed_by = relationship("CaseParty", foreign_keys=[filed_by_party_id])
    objection_to = relationship("CaseParty", foreign_keys=[objection_to_party_id])
    related_event = relationship("CaseTimelineEvent", foreign_keys=[related_event_id])
    related_asset = relationship("CaseAsset", foreign_keys=[related_asset_id])


# ============================================================================
# ASSOCIATION TABLES - Many-to-Many Relationships
# ============================================================================

class CaseEventParty(Base):
    """Association table for CaseTimelineEvent <-> CaseParty many-to-many relationship"""
    __tablename__ = "case_event_parties"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(36), ForeignKey('case_timeline_events.id'), nullable=False)
    party_id = Column(String(36), ForeignKey('case_parties.id'), nullable=False)
    role = Column(String(100))  # "organizer", "required_attendee", "optional_attendee", "responsible"
    attendance_status = Column(String(50))  # "attending", "declined", "maybe", "no_response"

    created_at = Column(DateTime, default=datetime.utcnow)
