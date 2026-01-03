"""
E-Filing Data Models

Comprehensive data models for electronic court filing system supporting
Federal (PACER/CM/ECF) and state court systems.
"""

from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, EmailStr


class CourtType(str, Enum):
    """Types of court systems"""
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_APPEALS = "federal_appeals"
    FEDERAL_BANKRUPTCY = "federal_bankruptcy"
    FEDERAL_TAX = "federal_tax"
    STATE_SUPREME = "state_supreme"
    STATE_APPELLATE = "state_appellate"
    STATE_SUPERIOR = "state_superior"
    STATE_MUNICIPAL = "state_municipal"
    STATE_FAMILY = "state_family"
    STATE_PROBATE = "state_probate"
    ADMINISTRATIVE = "administrative"


class FilingStatus(str, Enum):
    """Status of filing submission"""
    DRAFT = "draft"
    PENDING_VALIDATION = "pending_validation"
    VALIDATION_FAILED = "validation_failed"
    PENDING_SUBMISSION = "pending_submission"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SERVED = "served"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """Types of court documents"""
    COMPLAINT = "complaint"
    MOTION = "motion"
    RESPONSE = "response"
    BRIEF = "brief"
    MEMORANDUM = "memorandum"
    ORDER = "order"
    JUDGMENT = "judgment"
    NOTICE = "notice"
    EXHIBIT = "exhibit"
    AFFIDAVIT = "affidavit"
    DECLARATION = "declaration"
    CERTIFICATE = "certificate"
    STIPULATION = "stipulation"
    DISCOVERY = "discovery"
    SUBPOENA = "subpoena"
    OTHER = "other"


class ServiceType(str, Enum):
    """Methods of service"""
    ELECTRONIC = "electronic"
    MAIL = "mail"
    HAND_DELIVERY = "hand_delivery"
    CERTIFIED_MAIL = "certified_mail"
    PUBLICATION = "publication"
    OTHER = "other"


class PartyType(str, Enum):
    """Types of parties in a case"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    APPELLANT = "appellant"
    APPELLEE = "appellee"
    INTERVENOR = "intervenor"
    AMICUS = "amicus"
    GOVERNMENT = "government"
    OTHER = "other"


class AttorneyRole(str, Enum):
    """Attorney roles in representation"""
    LEAD_COUNSEL = "lead_counsel"
    CO_COUNSEL = "co_counsel"
    LOCAL_COUNSEL = "local_counsel"
    PRO_HAC_VICE = "pro_hac_vice"
    PRO_SE = "pro_se"
    GOVERNMENT_COUNSEL = "government_counsel"


class FilingFeeType(str, Enum):
    """Types of filing fees"""
    CASE_OPENING = "case_opening"
    MOTION = "motion"
    APPEAL = "appeal"
    COPY = "copy"
    SEARCH = "search"
    MISCELLANEOUS = "miscellaneous"
    WAIVED = "waived"


# Base Models

class BaseEntity(BaseModel):
    """Base entity with common fields"""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None


class ContactInfo(BaseModel):
    """Contact information structure"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "United States"


class Attorney(BaseModel):
    """Attorney information"""
    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    bar_number: str
    state_bar: str
    federal_bar_id: Optional[str] = None
    
    # Contact information
    contact_info: ContactInfo
    
    # Professional details
    law_firm: Optional[str] = None
    role: AttorneyRole = AttorneyRole.LEAD_COUNSEL
    admission_date: Optional[date] = None
    is_active: bool = True
    
    # Electronic filing credentials
    ecf_login: Optional[str] = None
    pacer_id: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name}{middle} {self.last_name}"


class Party(BaseModel):
    """Party to legal proceeding"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    party_type: PartyType
    
    # Entity details
    is_individual: bool = True
    business_type: Optional[str] = None  # Corporation, LLC, etc.
    
    # Contact information
    contact_info: Optional[ContactInfo] = None
    
    # Representation
    attorneys: List[Attorney] = Field(default_factory=list)
    is_pro_se: bool = False
    
    # Case-specific details
    case_role: Optional[str] = None
    served_date: Optional[datetime] = None
    
    @validator('attorneys')
    def validate_representation(cls, v, values):
        is_pro_se = values.get('is_pro_se', False)
        if is_pro_se and v:
            raise ValueError('Pro se party cannot have attorneys')
        if not is_pro_se and not v:
            raise ValueError('Represented party must have at least one attorney')
        return v


class CourtInfo(BaseModel):
    """Court information"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    court_type: CourtType
    jurisdiction: str
    
    # Location
    address: str
    city: str
    state: str
    zip_code: str
    
    # System information
    cm_ecf_url: Optional[str] = None
    pacer_site: Optional[str] = None
    efiling_system: Optional[str] = None
    
    # Filing requirements
    local_rules_url: Optional[str] = None
    filing_fee_schedule: Dict[str, Decimal] = Field(default_factory=dict)
    accepted_formats: List[str] = Field(default_factory=lambda: ["PDF"])
    max_file_size_mb: int = 50
    
    # Business hours
    business_hours: Dict[str, str] = Field(default_factory=dict)
    
    @validator('cm_ecf_url', 'pacer_site')
    def validate_urls(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class CaseInfo(BaseModel):
    """Case information"""
    id: UUID = Field(default_factory=uuid4)
    case_number: Optional[str] = None
    case_title: str
    case_type: str
    
    # Court assignment
    court: CourtInfo
    judge: Optional[str] = None
    magistrate: Optional[str] = None
    
    # Case status
    status: str = "active"
    filed_date: Optional[date] = None
    closed_date: Optional[date] = None
    
    # Parties
    parties: List[Party] = Field(default_factory=list)
    
    # Case details
    nature_of_suit: Optional[str] = None
    cause_of_action: Optional[str] = None
    jury_demand: bool = False
    class_action: bool = False
    
    # Financial
    amount_in_controversy: Optional[Decimal] = None
    filing_fee: Optional[Decimal] = None
    fee_status: str = "pending"  # paid, waived, pending
    
    @validator('case_number')
    def validate_case_number_format(cls, v, values):
        if v:
            court = values.get('court')
            if court and court.court_type == CourtType.FEDERAL_DISTRICT:
                # Federal format: X:YY-cv-NNNNN
                import re
                if not re.match(r'\d:\d{2}-[a-z]{2}-\d{5}', v):
                    raise ValueError('Federal case number format invalid')
        return v


class DocumentMetadata(BaseModel):
    """Document metadata"""
    title: str
    document_type: DocumentType
    description: Optional[str] = None
    
    # Filing details
    security_level: str = "public"  # public, sealed, restricted
    redacted: bool = False
    exhibits_attached: bool = False
    
    # Technical details
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None
    
    # Timestamps
    created_date: Optional[datetime] = None
    signed_date: Optional[datetime] = None
    
    @validator('page_count', 'word_count', 'file_size_bytes')
    def validate_positive_numbers(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value must be non-negative')
        return v


class CourtDocument(BaseModel):
    """Court document with content and metadata"""
    id: UUID = Field(default_factory=uuid4)
    
    # Document content
    file_name: str
    file_content: Optional[bytes] = None  # Binary content
    file_url: Optional[str] = None  # URL to document storage
    mime_type: str = "application/pdf"
    
    # Metadata
    metadata: DocumentMetadata
    
    # Filing context
    case_id: UUID
    attorney_id: UUID
    
    # Document relationships
    parent_document_id: Optional[UUID] = None  # For amended documents
    related_documents: List[UUID] = Field(default_factory=list)
    
    # Status tracking
    status: str = "draft"
    validation_errors: List[str] = Field(default_factory=list)
    
    @validator('file_name')
    def validate_file_name(cls, v):
        if not v.endswith(('.pdf', '.PDF')):
            raise ValueError('File must be PDF format')
        return v
    
    @validator('mime_type')
    def validate_mime_type(cls, v):
        allowed_types = ['application/pdf', 'text/plain', 'application/msword']
        if v not in allowed_types:
            raise ValueError(f'MIME type must be one of: {allowed_types}')
        return v


class ServiceInfo(BaseModel):
    """Service of process information"""
    service_type: ServiceType
    service_date: Optional[datetime] = None
    served_parties: List[UUID] = Field(default_factory=list)  # Party IDs
    
    # Service details
    process_server: Optional[str] = None
    service_address: Optional[str] = None
    service_method_details: Optional[str] = None
    
    # Electronic service
    email_addresses: List[EmailStr] = Field(default_factory=list)
    delivery_receipt: Optional[str] = None
    
    # Certificate of service
    certificate_required: bool = False
    certificate_filed: bool = False
    certificate_date: Optional[datetime] = None


class FilingFee(BaseModel):
    """Filing fee information"""
    fee_type: FilingFeeType
    amount: Decimal
    currency: str = "USD"
    
    # Payment details
    payment_method: Optional[str] = None  # credit_card, check, etc.
    payment_reference: Optional[str] = None
    paid_date: Optional[datetime] = None
    
    # Fee waiver
    waiver_requested: bool = False
    waiver_approved: bool = False
    waiver_reason: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError('Fee amount cannot be negative')
        return v


class FilingRequest(BaseEntity):
    """Electronic filing request"""
    
    # Case context
    case_info: CaseInfo
    
    # Documents to file
    documents: List[CourtDocument]
    primary_document: UUID  # ID of main document
    
    # Filing details
    filing_type: str  # initial, response, motion, etc.
    filing_description: str
    hearing_date: Optional[datetime] = None
    
    # Service information
    service_info: ServiceInfo
    
    # Fees
    filing_fees: List[FilingFee] = Field(default_factory=list)
    total_fee: Decimal = Field(default=Decimal('0'))
    
    # Attorney information
    filing_attorney: Attorney
    
    # Status and tracking
    status: FilingStatus = FilingStatus.DRAFT
    submission_date: Optional[datetime] = None
    confirmation_number: Optional[str] = None
    
    # System tracking
    court_system: str  # cm_ecf, state_system, etc.
    external_id: Optional[str] = None  # Court system's ID
    
    # Validation and processing
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    processing_errors: List[str] = Field(default_factory=list)
    
    @validator('documents')
    def validate_documents_not_empty(cls, v):
        if not v:
            raise ValueError('Filing must include at least one document')
        return v
    
    @validator('primary_document')
    def validate_primary_document_exists(cls, v, values):
        documents = values.get('documents', [])
        if documents and v not in [doc.id for doc in documents]:
            raise ValueError('Primary document must be in documents list')
        return v
    
    @validator('total_fee')
    def calculate_total_fee(cls, v, values):
        fees = values.get('filing_fees', [])
        calculated_total = sum(fee.amount for fee in fees)
        return calculated_total


class FilingResponse(BaseModel):
    """Response from court filing system"""
    filing_id: UUID
    
    # Response status
    success: bool
    status: FilingStatus
    message: str
    
    # Court system response
    confirmation_number: Optional[str] = None
    transaction_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Document processing results
    accepted_documents: List[UUID] = Field(default_factory=list)
    rejected_documents: List[UUID] = Field(default_factory=list)
    
    # Errors and warnings
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Next steps
    next_actions: List[str] = Field(default_factory=list)
    deadlines: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Fee processing
    fees_processed: List[UUID] = Field(default_factory=list)
    total_fees_charged: Decimal = Field(default=Decimal('0'))
    
    # Service tracking
    service_complete: bool = False
    service_failures: List[str] = Field(default_factory=list)


class EFilingCredentials(BaseModel):
    """Credentials for court e-filing systems"""
    attorney_id: UUID
    court_system: str  # cm_ecf, state_system, etc.
    
    # Login credentials
    username: str
    password_hash: str  # Encrypted/hashed password
    
    # System-specific IDs
    bar_number: str
    pacer_id: Optional[str] = None
    ecf_id: Optional[str] = None
    
    # Security
    two_factor_enabled: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    account_locked: bool = False
    
    # Permissions
    filing_permissions: List[str] = Field(default_factory=list)
    court_access: List[str] = Field(default_factory=list)
    
    # Expiration
    expires_at: Optional[datetime] = None
    needs_renewal: bool = False


class FilingConfiguration(BaseModel):
    """Configuration for court filing system"""
    court_id: UUID
    
    # System endpoints
    filing_endpoint: str
    query_endpoint: str
    authentication_endpoint: str
    
    # Document requirements
    required_formats: List[str] = Field(default_factory=lambda: ["PDF"])
    max_file_size_mb: int = 50
    max_documents_per_filing: int = 99
    
    # Validation rules
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    required_fields: List[str] = Field(default_factory=list)
    
    # Scheduling
    business_hours: Dict[str, str] = Field(default_factory=dict)
    maintenance_windows: List[Dict[str, str]] = Field(default_factory=list)
    
    # Features
    supports_electronic_service: bool = True
    supports_fee_waiver: bool = True
    supports_sealed_documents: bool = True
    requires_certificate_of_service: bool = True
    
    # System limits
    daily_filing_limit: Optional[int] = None
    hourly_rate_limit: Optional[int] = None


class AuditLog(BaseEntity):
    """Audit log for filing activities"""
    
    # Action details
    action: str  # filed, served, validated, etc.
    entity_type: str  # filing, document, case, etc.
    entity_id: UUID
    
    # User context
    user_id: Optional[UUID] = None
    attorney_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Action details
    description: str
    old_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    
    # System context
    system: str  # web, mobile, api, etc.
    court_system: Optional[str] = None
    
    # Result
    success: bool = True
    error_message: Optional[str] = None