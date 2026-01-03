"""
Client Portal Database Models

SQLAlchemy models for client portal functionality including user management,
document sharing, communications, notifications, and audit logging.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, 
    Enum, JSON, LargeBinary, Numeric, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any
import uuid

Base = declarative_base()

class ClientUserStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class DocumentStatus(PyEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ARCHIVED = "archived"
    DELETED = "deleted"

class DocumentType(PyEnum):
    CASE_FILE = "case_file"
    CORRESPONDENCE = "correspondence"
    INVOICE = "invoice"
    CONTRACT = "contract"
    EVIDENCE = "evidence"
    COURT_FILING = "court_filing"
    OTHER = "other"

class MessageStatus(PyEnum):
    SENT = "sent"
    DELIVERED = "delivered" 
    READ = "read"
    ARCHIVED = "archived"

class NotificationType(PyEnum):
    CASE_UPDATE = "case_update"
    DOCUMENT_SHARED = "document_shared"
    MESSAGE_RECEIVED = "message_received"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    INVOICE_GENERATED = "invoice_generated"
    DEADLINE_REMINDER = "deadline_reminder"
    SYSTEM_ALERT = "system_alert"

class NotificationPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CaseStatus(PyEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    ON_HOLD = "on_hold"
    PENDING = "pending"

class InvoiceStatus(PyEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class AppointmentStatus(PyEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class AuditAction(PyEnum):
    LOGIN = "login"
    LOGOUT = "logout"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"
    MESSAGE_SENT = "message_sent"
    MESSAGE_READ = "message_read"
    CASE_VIEWED = "case_viewed"
    PROFILE_UPDATED = "profile_updated"
    INVOICE_VIEWED = "invoice_viewed"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"

class ClientUser(Base):
    """Client user accounts with authentication and profile information."""
    __tablename__ = 'client_users'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    company_name = Column(String(255))
    
    # Authentication & Security
    is_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    last_login = Column(DateTime)
    
    # Profile Information
    status = Column(Enum(ClientUserStatus), default=ClientUserStatus.PENDING_VERIFICATION)
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    notification_preferences = Column(JSON, default={})
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    sessions = relationship("ClientSession", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("ClientDocument", back_populates="client", cascade="all, delete-orphan")
    sent_messages = relationship("ClientMessage", foreign_keys="ClientMessage.sender_id", back_populates="sender")
    received_messages = relationship("ClientMessage", foreign_keys="ClientMessage.recipient_id", back_populates="recipient")
    notifications = relationship("ClientNotification", back_populates="client", cascade="all, delete-orphan")
    cases = relationship("ClientCase", back_populates="client", cascade="all, delete-orphan")
    invoices = relationship("ClientInvoice", back_populates="client", cascade="all, delete-orphan")
    appointments = relationship("ClientAppointment", back_populates="client", cascade="all, delete-orphan")
    audit_logs = relationship("ClientAuditLog", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_client_email', 'email'),
        Index('idx_client_status', 'status'),
        Index('idx_client_created', 'created_at'),
    )
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'company_name': self.company_name,
            'is_verified': self.is_verified,
            'status': self.status.value if self.status else None,
            'timezone': self.timezone,
            'language': self.language,
            'notification_preferences': self.notification_preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'two_factor_enabled': self.two_factor_enabled,
                'failed_login_attempts': self.failed_login_attempts,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None
            })
        
        return data

class ClientSession(Base):
    """Client authentication sessions with security tracking."""
    __tablename__ = 'client_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('client_users.id'), nullable=False)
    
    # Session Information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_fingerprint = Column(String(255))
    location_country = Column(String(100))
    location_city = Column(String(100))
    
    # Security & Tracking
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, server_default=func.now())
    login_method = Column(String(50))  # password, 2fa, sso
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    invalidated_at = Column(DateTime)
    invalidated_reason = Column(String(100))
    
    # Relationships
    user = relationship("ClientUser", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_session_user', 'user_id'),
        Index('idx_session_active', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
    )

class ClientDocument(Base):
    """Client-accessible documents with security and sharing controls."""
    __tablename__ = 'client_documents'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('client_users.id'), nullable=False)
    
    # Document Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    
    # Content & Metadata
    title = Column(String(255))
    description = Column(Text)
    tags = Column(JSON, default=[])
    document_metadata = Column(JSON, default={})
    
    # Security & Access
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    is_confidential = Column(Boolean, default=False)
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255))
    access_permissions = Column(JSON, default={})
    download_allowed = Column(Boolean, default=True)
    print_allowed = Column(Boolean, default=True)
    
    # Tracking
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    last_viewed = Column(DateTime)
    last_downloaded = Column(DateTime)
    
    # Legal Context
    case_id = Column(Integer, ForeignKey('client_cases.id'))
    matter_number = Column(String(100))
    retention_until = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    uploaded_by = Column(String(100))
    
    # Relationships
    client = relationship("ClientUser", back_populates="documents")
    case = relationship("ClientCase", back_populates="documents")
    
    # Indexes
    __table_args__ = (
        Index('idx_document_client', 'client_id'),
        Index('idx_document_type', 'document_type'),
        Index('idx_document_status', 'status'),
        Index('idx_document_created', 'created_at'),
        Index('idx_document_case', 'case_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'document_type': self.document_type.value if self.document_type else None,
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'status': self.status.value if self.status else None,
            'is_confidential': self.is_confidential,
            'download_allowed': self.download_allowed,
            'print_allowed': self.print_allowed,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'last_viewed': self.last_viewed.isoformat() if self.last_viewed else None,
            'last_downloaded': self.last_downloaded.isoformat() if self.last_downloaded else None,
            'matter_number': self.matter_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ClientMessage(Base):
    """Secure messaging between clients and legal team."""
    __tablename__ = 'client_messages'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Message Participants
    sender_id = Column(Integer, ForeignKey('client_users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('client_users.id'))
    recipient_type = Column(String(50))  # client, attorney, staff
    
    # Message Content
    subject = Column(String(255))
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='text')  # text, html, encrypted
    
    # Message Status & Tracking
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    is_encrypted = Column(Boolean, default=True)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Threading
    thread_id = Column(String(50))
    parent_message_id = Column(Integer, ForeignKey('client_messages.id'))
    
    # Legal Context
    case_id = Column(Integer, ForeignKey('client_cases.id'))
    matter_number = Column(String(100))
    is_privileged = Column(Boolean, default=True)
    
    # Timestamps
    sent_at = Column(DateTime, server_default=func.now())
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    sender = relationship("ClientUser", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("ClientUser", foreign_keys=[recipient_id], back_populates="received_messages")
    parent_message = relationship("ClientMessage", remote_side=[id], backref="replies")
    case = relationship("ClientCase", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_message_sender', 'sender_id'),
        Index('idx_message_recipient', 'recipient_id'),
        Index('idx_message_thread', 'thread_id'),
        Index('idx_message_case', 'case_id'),
        Index('idx_message_created', 'created_at'),
    )

class ClientNotification(Base):
    """Real-time notifications for client portal events."""
    __tablename__ = 'client_notifications'
    
    id = Column(Integer, primary_key=True)
    notification_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('client_users.id'), nullable=False)
    
    # Notification Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Delivery & Status
    is_read = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    delivery_method = Column(JSON, default=['portal'])  # portal, email, sms, push
    
    # Context & Actions
    related_entity_type = Column(String(50))  # case, document, message, appointment
    related_entity_id = Column(String(50))
    action_url = Column(String(500))
    action_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    scheduled_for = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Relationships
    client = relationship("ClientUser", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_client', 'client_id'),
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_priority', 'priority'),
        Index('idx_notification_read', 'is_read'),
        Index('idx_notification_created', 'created_at'),
    )

class ClientCase(Base):
    """Client case information and status tracking."""
    __tablename__ = 'client_cases'
    
    id = Column(Integer, primary_key=True)
    case_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('client_users.id'), nullable=False)
    
    # Case Information
    case_number = Column(String(100), unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    case_type = Column(String(100))
    practice_area = Column(String(100))
    
    # Status & Progress
    status = Column(Enum(CaseStatus), default=CaseStatus.ACTIVE)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    progress_percentage = Column(Integer, default=0)
    
    # Legal Team
    assigned_attorney = Column(String(100))
    assigned_paralegal = Column(String(100))
    team_members = Column(JSON, default=[])
    
    # Important Dates
    opened_date = Column(DateTime, server_default=func.now())
    closed_date = Column(DateTime)
    statute_limitations = Column(DateTime)
    next_hearing = Column(DateTime)
    
    # Court Information
    court_name = Column(String(255))
    judge_name = Column(String(100))
    opposing_counsel = Column(String(255))
    
    # Billing & Financials
    billing_rate = Column(Numeric(10, 2))
    estimated_budget = Column(Numeric(10, 2))
    total_billed = Column(Numeric(10, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    client = relationship("ClientUser", back_populates="cases")
    documents = relationship("ClientDocument", back_populates="case")
    messages = relationship("ClientMessage", back_populates="case")
    invoices = relationship("ClientInvoice", back_populates="case")
    appointments = relationship("ClientAppointment", back_populates="case")
    
    # Indexes
    __table_args__ = (
        Index('idx_case_client', 'client_id'),
        Index('idx_case_number', 'case_number'),
        Index('idx_case_status', 'status'),
        Index('idx_case_type', 'case_type'),
        Index('idx_case_created', 'created_at'),
    )

class ClientInvoice(Base):
    """Client billing and invoice information."""
    __tablename__ = 'client_invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('client_users.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('client_cases.id'))
    
    # Invoice Details
    invoice_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(255))
    description = Column(Text)
    
    # Financial Information
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    
    # Status & Dates
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    issued_date = Column(DateTime)
    due_date = Column(DateTime)
    paid_date = Column(DateTime)
    
    # Line Items & Details
    line_items = Column(JSON, default=[])
    payment_terms = Column(String(255))
    payment_methods = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    client = relationship("ClientUser", back_populates="invoices")
    case = relationship("ClientCase", back_populates="invoices")
    
    # Indexes
    __table_args__ = (
        Index('idx_invoice_client', 'client_id'),
        Index('idx_invoice_case', 'case_id'),
        Index('idx_invoice_number', 'invoice_number'),
        Index('idx_invoice_status', 'status'),
        Index('idx_invoice_due_date', 'due_date'),
    )

class ClientAppointment(Base):
    """Client appointment scheduling and management."""
    __tablename__ = 'client_appointments'
    
    id = Column(Integer, primary_key=True)
    appointment_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = Column(Integer, ForeignKey('client_users.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('client_cases.id'))
    
    # Appointment Details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    appointment_type = Column(String(100))  # consultation, deposition, hearing, meeting
    
    # Scheduling
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    timezone = Column(String(50), default='UTC')
    
    # Location & Method
    location_type = Column(String(50))  # office, phone, video, court
    location_address = Column(Text)
    meeting_url = Column(String(500))
    meeting_credentials = Column(JSON, default={})
    
    # Status & Tracking
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reminder_sent = Column(Boolean, default=False)
    confirmation_required = Column(Boolean, default=True)
    confirmed_at = Column(DateTime)
    
    # Participants
    attorney_name = Column(String(100))
    participants = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    client = relationship("ClientUser", back_populates="appointments")
    case = relationship("ClientCase", back_populates="appointments")
    
    # Indexes
    __table_args__ = (
        Index('idx_appointment_client', 'client_id'),
        Index('idx_appointment_case', 'case_id'),
        Index('idx_appointment_start', 'scheduled_start'),
        Index('idx_appointment_status', 'status'),
    )

class ClientAuditLog(Base):
    """Comprehensive audit logging for client portal activities."""
    __tablename__ = 'client_audit_logs'
    
    id = Column(Integer, primary_key=True)
    log_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('client_users.id'))
    
    # Action Information
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(50))
    
    # Context & Details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # Action Details
    action_details = Column(JSON, default={})
    old_values = Column(JSON, default={})
    new_values = Column(JSON, default={})
    
    # Status & Results
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Metadata
    timestamp = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("ClientUser", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_ip', 'ip_address'),
    )