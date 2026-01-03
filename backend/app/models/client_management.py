"""
Client Management Models

Models for managing legal clients, client portals, and document sharing.
Enables law firms to manage relationships with clients and share documents securely.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
import enum

from ..src.core.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class ClientStatus(enum.Enum):
    """Client account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ClientType(enum.Enum):
    """Type of client"""
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"


class CaseStatus(enum.Enum):
    """Case status"""
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"
    ARCHIVED = "archived"


class DocumentShareStatus(enum.Enum):
    """Status of shared documents"""
    PENDING = "pending"  # Shared but not yet viewed
    VIEWED = "viewed"  # Client has viewed
    DOWNLOADED = "downloaded"  # Client has downloaded
    ACKNOWLEDGED = "acknowledged"  # Client has acknowledged receipt
    EXPIRED = "expired"  # Share link expired


class AccessLevel(enum.Enum):
    """Access level for client portal"""
    READ_ONLY = "read_only"
    COMMENT = "comment"
    DOWNLOAD = "download"
    FULL = "full"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Client to User (lawyers/firm members)
client_user_association = Table(
    'client_user_association',
    Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(50)),  # "primary_attorney", "secondary_attorney", "paralegal", etc.
    Column('created_at', DateTime, default=func.now())
)


# =============================================================================
# MODELS
# =============================================================================

class Client(Base):
    """
    Legal client information and relationship management.

    Represents a client (individual or entity) of the law firm.
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Information
    client_number = Column(String(50), unique=True, nullable=False, index=True)  # Firm's client ID
    client_type = Column(SQLEnum(ClientType), nullable=False)
    status = Column(SQLEnum(ClientStatus), default=ClientStatus.ACTIVE, nullable=False, index=True)

    # Individual Client
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))
    date_of_birth = Column(DateTime)
    ssn_last_four = Column(String(4))  # Only store last 4 digits for security

    # Business Client
    company_name = Column(String(255))
    business_type = Column(String(100))  # "LLC", "Corporation", "Partnership", etc.
    ein = Column(String(50))  # Employer Identification Number
    industry = Column(String(100))

    # Contact Information
    email = Column(String(255), index=True)
    phone_primary = Column(String(50))
    phone_secondary = Column(String(50))
    fax = Column(String(50))

    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100), default="USA")

    # Billing Address (if different)
    billing_address_line1 = Column(String(255))
    billing_address_line2 = Column(String(255))
    billing_city = Column(String(100))
    billing_state = Column(String(50))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(100))

    # Portal Access
    portal_user_id = Column(Integer, ForeignKey('users.id'))  # If client has portal account
    portal_access_enabled = Column(Boolean, default=False)
    portal_access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.READ_ONLY)
    portal_last_login = Column(DateTime)

    # Financial
    billing_rate_hourly = Column(Integer)  # Cents
    retainer_amount = Column(Integer)  # Cents
    retainer_balance = Column(Integer)  # Cents
    payment_terms = Column(String(100))  # "Net 30", "Upon Receipt", etc.

    # Conflict Check
    conflict_check_date = Column(DateTime)
    conflict_check_status = Column(String(50))  # "clear", "potential", "conflict"
    conflict_notes = Column(Text)

    # Engagement
    engagement_letter_signed = Column(Boolean, default=False)
    engagement_date = Column(DateTime)
    termination_date = Column(DateTime)

    # Metadata
    notes = Column(Text)
    internal_notes = Column(Text)  # Not visible to client
    tags = Column(JSON)  # ["vip", "high-value", "referral"]
    custom_fields = Column(JSON)  # Flexible custom data

    # Source/Referral
    referral_source = Column(String(200))
    referred_by_client_id = Column(Integer, ForeignKey('clients.id'))

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    portal_user = relationship("User", foreign_keys=[portal_user_id])
    attorneys = relationship("User", secondary=client_user_association, backref="clients")
    cases = relationship("Case", back_populates="client", cascade="all, delete-orphan")
    shared_documents = relationship("SharedDocument", back_populates="client", cascade="all, delete-orphan")
    communications = relationship("ClientCommunication", back_populates="client", cascade="all, delete-orphan")
    # referred_by = relationship("Client", remote_side=[id], backref="referrals")  # Temporarily disabled - id reference issue

    def __repr__(self):
        return f"<Client {self.client_number}: {self.display_name}>"

    @property
    def display_name(self) -> str:
        """Get display name for client"""
        if self.client_type == ClientType.BUSINESS:
            return self.company_name or f"Client #{self.client_number}"
        else:
            if self.full_name:
                return self.full_name
            elif self.first_name and self.last_name:
                return f"{self.first_name} {self.last_name}"
            elif self.first_name:
                return self.first_name
            else:
                return f"Client #{self.client_number}"

    @property
    def is_active(self) -> bool:
        """Check if client is active"""
        return self.status == ClientStatus.ACTIVE

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert client to dictionary"""
        client_dict = {
            "id": self.id,
            "client_number": self.client_number,
            "client_type": self.client_type.value,
            "status": self.status.value,
            "display_name": self.display_name,
            "email": self.email,
            "phone": self.phone_primary,
            "portal_access_enabled": self.portal_access_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_sensitive:
            client_dict.update({
                "ssn_last_four": self.ssn_last_four,
                "ein": self.ein,
                "address": {
                    "line1": self.address_line1,
                    "line2": self.address_line2,
                    "city": self.city,
                    "state": self.state,
                    "postal_code": self.postal_code,
                    "country": self.country
                },
                "internal_notes": self.internal_notes,
                "retainer_balance": self.retainer_balance,
            })

        return client_dict


class Case(Base):
    """
    Legal case/matter associated with a client.
    """
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)

    # Case Identification
    case_number = Column(String(100), unique=True, nullable=False, index=True)
    case_name = Column(String(500), nullable=False)
    case_type = Column(String(100))  # "litigation", "transactional", "estate", etc.
    practice_area = Column(String(100))  # "family", "criminal", "corporate", etc.

    # Client Association
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)

    # Status
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.OPEN, nullable=False, index=True)
    priority = Column(String(20))  # "low", "medium", "high", "urgent"

    # Court Information
    court_name = Column(String(255))
    court_case_number = Column(String(100))
    judge_name = Column(String(200))
    opposing_party = Column(String(500))
    opposing_counsel = Column(String(500))

    # Important Dates
    opened_date = Column(DateTime, nullable=False, default=func.now())
    closed_date = Column(DateTime)
    statute_limitations_date = Column(DateTime)
    trial_date = Column(DateTime)

    # Financial
    estimated_value = Column(Integer)  # Cents
    billing_type = Column(String(50))  # "hourly", "flat_fee", "contingency"
    flat_fee_amount = Column(Integer)  # Cents
    contingency_percentage = Column(Integer)  # Percentage

    # Description
    description = Column(Text)
    legal_issues = Column(Text)
    case_summary = Column(Text)

    # Outcome
    outcome = Column(String(100))  # "won", "lost", "settled", "dismissed"
    outcome_details = Column(Text)
    settlement_amount = Column(Integer)  # Cents

    # Metadata
    tags = Column(JSON)
    custom_fields = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    client = relationship("Client", back_populates="cases")

    def __repr__(self):
        return f"<Case {self.case_number}: {self.case_name}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert case to dictionary"""
        return {
            "id": self.id,
            "case_number": self.case_number,
            "case_name": self.case_name,
            "case_type": self.case_type,
            "practice_area": self.practice_area,
            "status": self.status.value,
            "client_id": self.client_id,
            "opened_date": self.opened_date.isoformat() if self.opened_date else None,
            "trial_date": self.trial_date.isoformat() if self.trial_date else None,
        }


class SharedDocument(Base):
    """
    Documents shared with clients through the portal.

    Tracks document sharing, access, and expiration.
    """
    __tablename__ = "shared_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Document Reference
    document_id = Column(Integer, index=True)  # Reference to main documents table
    file_path = Column(String(500))
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)  # Bytes
    mime_type = Column(String(100))

    # Sharing
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey('cases.id', ondelete='SET NULL'))
    shared_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Access Control
    share_token = Column(String(255), unique=True, index=True)  # Secure token for access
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255))
    expires_at = Column(DateTime)  # Share expiration
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.DOWNLOAD)

    # Status Tracking
    status = Column(SQLEnum(DocumentShareStatus), default=DocumentShareStatus.PENDING, index=True)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    first_viewed_at = Column(DateTime)
    last_viewed_at = Column(DateTime)
    first_downloaded_at = Column(DateTime)
    last_downloaded_at = Column(DateTime)
    acknowledged_at = Column(DateTime)

    # Metadata
    title = Column(String(255))
    description = Column(Text)
    category = Column(String(100))  # "contract", "evidence", "correspondence", etc.
    tags = Column(JSON)

    # Notifications
    notify_on_view = Column(Boolean, default=True)
    notify_on_download = Column(Boolean, default=True)
    view_notification_sent = Column(Boolean, default=False)
    download_notification_sent = Column(Boolean, default=False)

    # Timestamps
    shared_at = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    client = relationship("Client", back_populates="shared_documents")
    case = relationship("Case")
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])

    def __repr__(self):
        return f"<SharedDocument {self.filename} with Client {self.client_id}>"

    @property
    def is_expired(self) -> bool:
        """Check if share has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_accessible(self) -> bool:
        """Check if document is currently accessible"""
        return (
            not self.is_expired and
            self.status != DocumentShareStatus.EXPIRED and
            not self.deleted_at
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert shared document to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "description": self.description,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status.value,
            "shared_at": self.shared_at.isoformat() if self.shared_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "access_level": self.access_level.value,
        }


class ClientCommunication(Base):
    """
    Track communications with clients (emails, calls, meetings).

    Maintains a complete audit trail of client interactions.
    """
    __tablename__ = "client_communications"

    id = Column(Integer, primary_key=True, index=True)

    # Association
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey('cases.id', ondelete='SET NULL'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Staff member

    # Communication Details
    communication_type = Column(String(50), nullable=False)  # "email", "phone", "meeting", "letter"
    direction = Column(String(20))  # "inbound", "outbound"
    subject = Column(String(500))
    content = Column(Text)
    summary = Column(Text)

    # Email Specific
    email_message_id = Column(String(255))
    email_from = Column(String(255))
    email_to = Column(String(255))
    email_cc = Column(String(500))

    # Meeting Specific
    meeting_location = Column(String(255))
    meeting_attendees = Column(JSON)

    # Tracking
    duration_minutes = Column(Integer)  # For calls/meetings
    billable = Column(Boolean, default=True)
    billable_time_minutes = Column(Integer)

    # Status
    is_privileged = Column(Boolean, default=True)  # Attorney-client privilege
    is_confidential = Column(Boolean, default=True)

    # Timestamps
    communication_date = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="communications")
    case = relationship("Case")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<ClientCommunication {self.communication_type} with Client {self.client_id}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert communication to dictionary"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "case_id": self.case_id,
            "communication_type": self.communication_type,
            "direction": self.direction,
            "subject": self.subject,
            "summary": self.summary,
            "communication_date": self.communication_date.isoformat() if self.communication_date else None,
            "duration_minutes": self.duration_minutes,
            "billable": self.billable,
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'ClientStatus',
    'ClientType',
    'CaseStatus',
    'DocumentShareStatus',
    'AccessLevel',

    # Models
    'Client',
    'Case',
    'SharedDocument',
    'ClientCommunication',

    # Association Tables
    'client_user_association',
]
