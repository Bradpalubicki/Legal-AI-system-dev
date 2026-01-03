"""
SQLAlchemy Models for Legal AI System

Database models for tracking legal dockets and RECAP tasks.
Includes models for PACER docket tracking, document processing,
and background task management.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON,
    ForeignKey, Numeric, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Import base from backend core if available, otherwise create new base
try:
    # Try the path when running from backend/ directory
    from app.src.core.database import Base
except ImportError:
    try:
        # Try alternative path when running from project root
        from backend.app.src.core.database import Base
    except ImportError:
        # Fallback base classes
        Base = declarative_base()

# Define mixins that are used by multiple models
class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""
    created_at = Column(DateTime(), default=lambda: datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime(), default=lambda: datetime.utcnow(),
                      onupdate=lambda: datetime.utcnow(), nullable=False)

class BaseModelMixin(TimestampMixin):
    """Base mixin with common fields for all models"""
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


# =============================================================================
# ENUMS FOR STATUS AND TYPES
# =============================================================================

class DocketTrackingStatus(enum.Enum):
    """Status of docket tracking"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"


class CourtType(enum.Enum):
    """Types of courts"""
    DISTRICT = "district"
    CIRCUIT = "circuit"
    SUPREME = "supreme"
    BANKRUPTCY = "bankruptcy"
    TAX = "tax"
    APPEALS = "appeals"
    STATE = "state"
    INTERNATIONAL = "international"


class DocumentType(enum.Enum):
    """Types of legal documents"""
    MOTION = "motion"
    ORDER = "order"
    COMPLAINT = "complaint"
    ANSWER = "answer"
    BRIEF = "brief"
    OPINION = "opinion"
    JUDGMENT = "judgment"
    TRANSCRIPT = "transcript"
    EXHIBIT = "exhibit"
    NOTICE = "notice"
    PLEADING = "pleading"
    OTHER = "other"


class RecapTaskStatus(enum.Enum):
    """Status of RECAP background tasks"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class RecapTaskType(enum.Enum):
    """Types of RECAP tasks"""
    DOCKET_FETCH = "docket_fetch"
    DOCUMENT_DOWNLOAD = "document_download"
    PDF_EXTRACTION = "pdf_extraction"
    OCR_PROCESSING = "ocr_processing"
    CITATION_ANALYSIS = "citation_analysis"
    METADATA_EXTRACTION = "metadata_extraction"
    COURT_CALENDAR_SYNC = "court_calendar_sync"
    NOTIFICATION_SEND = "notification_send"


class Priority(enum.Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class DocumentDownloadSource(enum.Enum):
    """Source of document download"""
    FREE = "free"           # Internet Archive / RECAP
    PACER = "pacer"         # Direct PACER download (costs money)
    MANUAL = "manual"       # Manually uploaded


class DocumentDownloadStatus(enum.Enum):
    """Status of document download"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# TRACKED DOCKETS MODEL
# =============================================================================

class TrackedDocket(Base, BaseModelMixin):
    """
    Model for tracking legal dockets from various court systems.
    
    This model stores information about legal cases being monitored,
    including PACER integration, document tracking, and automated updates.
    """
    
    __tablename__ = "tracked_dockets"
    
    # Core docket identification
    docket_number = Column(String(100), nullable=False, index=True)
    court_id = Column(String(50), nullable=False, index=True)
    court_name = Column(String(200), nullable=False)
    court_type = Column(SQLEnum(CourtType), nullable=False, default=CourtType.DISTRICT)
    
    # Case information
    case_name = Column(String(500), nullable=False)
    case_title = Column(Text)  # Full case title
    nature_of_suit = Column(String(100))
    cause_of_action = Column(String(200))
    jurisdiction = Column(String(100))
    
    # Parties involved
    plaintiff = Column(String(300))
    defendant = Column(String(300))
    judge_assigned = Column(String(200))
    magistrate_judge = Column(String(200))
    
    # PACER integration
    pacer_case_id = Column(String(50), unique=True, index=True)
    pacer_case_guid = Column(UUID(as_uuid=True), unique=True, index=True)
    pacer_court_id = Column(String(20))  # PACER court identifier
    pacer_last_fetch = Column(DateTime())
    pacer_fetch_count = Column(Integer, default=0)

    # CourtListener integration (free alternative to PACER)
    courtlistener_docket_id = Column(Integer, index=True, nullable=True)  # CourtListener docket ID
    courtlistener_last_fetch = Column(DateTime())
    
    # Case dates and status
    date_filed = Column(DateTime())
    date_terminated = Column(DateTime())
    date_last_filing = Column(DateTime())
    case_status = Column(String(50))
    case_flags = Column(String(200))  # Comma-separated flags
    
    # Tracking configuration
    tracking_status = Column(SQLEnum(DocketTrackingStatus), default=DocketTrackingStatus.ACTIVE, nullable=False)
    auto_fetch_enabled = Column(Boolean, default=True, nullable=False)
    fetch_interval_hours = Column(Integer, default=24)  # How often to check for updates
    notification_enabled = Column(Boolean, default=True, nullable=False)
    
    # Financial information
    filing_fee = Column(Numeric(10, 2))
    total_fees = Column(Numeric(10, 2))
    pacer_cost_estimate = Column(Numeric(8, 2))  # Estimated PACER costs
    pacer_cost_actual = Column(Numeric(8, 2))    # Actual PACER costs incurred
    
    # Document tracking
    total_documents = Column(Integer, default=0)
    documents_downloaded = Column(Integer, default=0)
    last_document_number = Column(Integer, default=0)
    
    # Metadata and custom fields
    tags = Column(JSON)  # Array of tags for organization
    custom_fields = Column(JSON)  # Custom user-defined fields
    notes = Column(Text)
    
    # Client and matter association
    client_id = Column(Integer, nullable=True)  # Removed foreign key - backend tables in separate metadata
    matter_id = Column(Integer, nullable=True)  # Removed foreign key - matters table doesn't exist
    assigned_attorney_id = Column(Integer, nullable=True)  # Removed foreign key - backend tables in separate metadata
    
    # Analysis and AI processing
    ai_summary = Column(Text)
    key_events = Column(JSON)  # Important events extracted by AI
    risk_assessment = Column(JSON)  # AI-generated risk assessment
    similar_cases = Column(JSON)  # References to similar cases
    
    # Archive and retention
    archived = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime())
    retention_date = Column(DateTime())
    
    # Relationships
    recap_tasks = relationship("RecapTask", back_populates="tracked_docket", cascade="all, delete-orphan")
    documents = relationship("DocketDocument", back_populates="tracked_docket", cascade="all, delete-orphan")
    # user_monitors = relationship("UserDocketMonitor", back_populates="tracked_docket", cascade="all, delete-orphan")  # Temporarily disabled
    # access_grants = relationship("CaseAccess", back_populates="case")  # Commented out - CaseAccess not in shared models
    
    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint('docket_number', 'court_id', name='uq_docket_court'),
        Index('ix_tracked_dockets_status_court', 'tracking_status', 'court_type'),
        Index('ix_tracked_dockets_dates', 'date_filed', 'date_last_filing'),
        Index('ix_tracked_dockets_pacer', 'pacer_case_id', 'pacer_last_fetch'),
        Index('ix_tracked_dockets_client_matter', 'client_id', 'matter_id'),
        CheckConstraint('fetch_interval_hours > 0', name='ck_positive_fetch_interval'),
        CheckConstraint('total_documents >= 0', name='ck_non_negative_documents'),
        CheckConstraint('documents_downloaded >= 0', name='ck_non_negative_downloaded'),
        CheckConstraint('documents_downloaded <= total_documents', name='ck_downloaded_not_exceed_total'),
    )
    
    @validates('docket_number')
    def validate_docket_number(self, key, docket_number):
        """Validate docket number format"""
        if not docket_number or len(docket_number.strip()) == 0:
            raise ValueError("Docket number cannot be empty")
        return docket_number.strip().upper()
    
    @validates('court_id')
    def validate_court_id(self, key, court_id):
        """Validate court ID format"""
        if not court_id or len(court_id.strip()) == 0:
            raise ValueError("Court ID cannot be empty")
        return court_id.strip().lower()
    
    def __repr__(self):
        return f"<TrackedDocket(id={self.id}, docket='{self.docket_number}', court='{self.court_id}', status='{self.tracking_status.value}')>"


# =============================================================================
# RECAP TASKS MODEL  
# =============================================================================

class RecapTask(Base, BaseModelMixin):
    """
    Model for managing RECAP background tasks.
    
    Handles asynchronous processing of legal documents, docket updates,
    PACER integration, and other background operations.
    """
    
    __tablename__ = "recap_tasks"
    
    # Task identification
    task_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    task_type = Column(SQLEnum(RecapTaskType), nullable=False, index=True)
    task_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Task status and progress
    status = Column(SQLEnum(RecapTaskStatus), default=RecapTaskStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(Priority), default=Priority.NORMAL, nullable=False, index=True)
    progress_percent = Column(Integer, default=0)  # 0-100
    
    # Timing information
    scheduled_at = Column(DateTime(), default=lambda: datetime.utcnow())
    started_at = Column(DateTime())
    completed_at = Column(DateTime())
    estimated_duration_seconds = Column(Integer)
    actual_duration_seconds = Column(Integer)
    
    # Retry logic
    max_retries = Column(Integer, default=3, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    retry_delay_seconds = Column(Integer, default=300)  # 5 minutes default
    last_retry_at = Column(DateTime())
    
    # Task configuration and parameters
    task_params = Column(JSON)  # Input parameters for the task
    task_config = Column(JSON)  # Configuration options
    environment_vars = Column(JSON)  # Environment-specific variables
    
    # Results and output
    result_data = Column(JSON)  # Task output data
    result_metadata = Column(JSON)  # Metadata about results
    output_files = Column(JSON)  # References to generated files
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)  # Detailed error information
    error_stack_trace = Column(Text)
    error_code = Column(String(50))
    
    # Resource usage and monitoring
    memory_usage_mb = Column(Integer)
    cpu_usage_percent = Column(Numeric(5, 2))
    disk_usage_mb = Column(Integer)
    network_usage_mb = Column(Integer)
    
    # Dependencies and relationships
    parent_task_id = Column(Integer, ForeignKey('recap_tasks.id'), nullable=True)
    tracked_docket_id = Column(Integer, ForeignKey('tracked_dockets.id'), nullable=True, index=True)
    user_id = Column(Integer, nullable=True)  # User who initiated the task - removed foreign key (backend tables in separate metadata)

    # PACER-specific fields
    pacer_session_id = Column(String(100))
    pacer_cost_estimate = Column(Numeric(8, 2))
    pacer_cost_actual = Column(Numeric(8, 2))
    pacer_pages_accessed = Column(Integer)

    # Document processing fields
    source_document_id = Column(Integer, nullable=True)  # Removed foreign key - backend tables in separate metadata
    processed_document_ids = Column(JSON)  # Array of resulting document IDs
    
    # Queue and worker information
    queue_name = Column(String(100), default='default', nullable=False)
    worker_id = Column(String(100))
    worker_hostname = Column(String(200))
    celery_task_id = Column(String(155), unique=True, index=True)  # Celery UUID
    
    # Notifications and alerts
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_recipients = Column(JSON)  # Email addresses or user IDs
    alert_on_failure = Column(Boolean, default=True, nullable=False)
    alert_on_completion = Column(Boolean, default=False, nullable=False)
    
    # Archival and cleanup
    archived = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime())
    cleanup_after_days = Column(Integer, default=30)
    
    # Relationships
    tracked_docket = relationship("TrackedDocket", back_populates="recap_tasks")
    # parent_task = relationship("RecapTask", remote_side=[id], backref="child_tasks")  # Temporarily disabled - id reference issue
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_recap_tasks_status_priority', 'status', 'priority'),
        Index('ix_recap_tasks_type_status', 'task_type', 'status'),
        Index('ix_recap_tasks_scheduled', 'scheduled_at', 'status'),
        Index('ix_recap_tasks_docket_type', 'tracked_docket_id', 'task_type'),
        Index('ix_recap_tasks_celery', 'celery_task_id'),
        Index('ix_recap_tasks_worker', 'worker_id', 'status'),
        CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='ck_valid_progress'),
        CheckConstraint('retry_count >= 0', name='ck_non_negative_retries'),
        CheckConstraint('retry_count <= max_retries', name='ck_retries_not_exceed_max'),
        CheckConstraint('max_retries >= 0', name='ck_non_negative_max_retries'),
    )
    
    @validates('progress_percent')
    def validate_progress(self, key, progress):
        """Validate progress percentage"""
        if progress is not None and (progress < 0 or progress > 100):
            raise ValueError("Progress must be between 0 and 100")
        return progress
    
    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate task priority"""
        if priority not in Priority:
            raise ValueError(f"Invalid priority: {priority}")
        return priority
    
    def __repr__(self):
        return f"<RecapTask(id={self.id}, type='{self.task_type.value}', status='{self.status.value}', docket_id={self.tracked_docket_id})>"
    
    def is_completed(self) -> bool:
        """Check if task is in a completed state"""
        return self.status in [RecapTaskStatus.COMPLETED, RecapTaskStatus.FAILED, RecapTaskStatus.CANCELLED]
    
    def is_running(self) -> bool:
        """Check if task is currently running"""
        return self.status == RecapTaskStatus.PROCESSING
    
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return (self.status == RecapTaskStatus.FAILED and 
                self.retry_count < self.max_retries)
    
    def calculate_duration(self) -> Optional[int]:
        """Calculate actual task duration in seconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    def update_progress(self, percent: int, message: str = None):
        """Update task progress"""
        self.progress_percent = max(0, min(100, percent))
        if message:
            if not self.result_metadata:
                self.result_metadata = {}
            self.result_metadata['progress_message'] = message
            self.result_metadata['last_update'] = datetime.now(timezone.utc).isoformat()


# =============================================================================
# SUPPORTING MODELS
# =============================================================================

class DocketDocument(Base, BaseModelMixin):
    """
    Model for individual documents within a tracked docket.
    """
    
    __tablename__ = "docket_documents"
    
    # Document identification
    document_number = Column(Integer, nullable=False)
    attachment_number = Column(Integer, default=0)  # 0 for main document, >0 for attachments
    pacer_doc_id = Column(String(50), unique=True, index=True)
    pacer_seq_number = Column(Integer)
    
    # Document metadata
    description = Column(Text, nullable=False)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.OTHER)
    file_size_bytes = Column(BigInteger)
    page_count = Column(Integer)
    
    # Filing information
    date_filed = Column(DateTime(), nullable=False)
    filed_by = Column(String(300))  # Party or attorney who filed
    docket_text = Column(Text)  # Full docket entry text
    
    # Document access and costs
    is_available = Column(Boolean, default=True, nullable=False)
    cost_cents = Column(Integer)  # PACER cost in cents
    is_free = Column(Boolean, default=False, nullable=False)
    
    # Processing status
    downloaded = Column(Boolean, default=False, nullable=False)
    downloaded_at = Column(DateTime())
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime())
    
    # File storage
    file_path = Column(String(500))
    file_hash = Column(String(64))  # SHA-256 hash
    mime_type = Column(String(100))
    
    # Relationships
    tracked_docket_id = Column(Integer, ForeignKey('tracked_dockets.id'), nullable=False, index=True)
    tracked_docket = relationship("TrackedDocket", back_populates="documents")
    
    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint('tracked_docket_id', 'document_number', 'attachment_number', 
                        name='uq_docket_doc_attachment'),
        Index('ix_docket_docs_filing_date', 'date_filed'),
        Index('ix_docket_docs_type', 'document_type'),
        Index('ix_docket_docs_status', 'downloaded', 'processed'),
        CheckConstraint('document_number > 0', name='ck_positive_doc_number'),
        CheckConstraint('attachment_number >= 0', name='ck_non_negative_attachment'),
        CheckConstraint('page_count >= 0', name='ck_non_negative_pages'),
        CheckConstraint('file_size_bytes >= 0', name='ck_non_negative_file_size'),
    )
    
    def __repr__(self):
        return f"<DocketDocument(id={self.id}, doc_num={self.document_number}, attachment={self.attachment_number}, docket_id={self.tracked_docket_id})>"


class UserDocketMonitor(Base):
    """
    Model for tracking which users are monitoring which dockets.

    This replaces the in-memory storage in CourtListenerService to persist
    monitored cases across server restarts.
    """

    __tablename__ = "user_docket_monitors"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User and docket relationship
    user_id = Column(Integer, nullable=False, index=True)  # References users.id
    tracked_docket_id = Column(Integer, ForeignKey('tracked_dockets.id'), nullable=False, index=True)

    # Monitoring metadata
    started_monitoring_at = Column(DateTime(), default=lambda: datetime.utcnow(), nullable=False)
    last_checked_at = Column(DateTime(), default=lambda: datetime.utcnow(), nullable=False)
    last_known_entry_number = Column(Integer, default=0, nullable=False)  # Track last seen document entry number

    # Case details cache (for quick display without fetching from API)
    case_name = Column(String(500))
    docket_number = Column(String(100))
    court_name = Column(String(200))
    date_filed = Column(DateTime(), nullable=True)  # Case filing date from CourtListener
    courtlistener_docket_id = Column(Integer)  # CourtListener docket ID
    courtlistener_absolute_url = Column(String(500))  # Direct link to case

    # Notification preferences
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    notification_frequency = Column(String(50), default="immediate")  # immediate, daily, weekly

    # Auto-download preferences
    auto_download_enabled = Column(Boolean, default=True, nullable=False)  # ON by default
    auto_download_free_only = Column(Boolean, default=False, nullable=False)  # Default: download all docs within budget
    pacer_download_budget = Column(Numeric(10, 2), default=10.00)  # Monthly budget limit
    pacer_spent_this_month = Column(Numeric(10, 2), default=0.00)  # Track spending
    budget_reset_date = Column(DateTime(), default=lambda: datetime.utcnow())  # When to reset monthly budget

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    stopped_monitoring_at = Column(DateTime(), nullable=True)

    # Relationships
    # tracked_docket = relationship("TrackedDocket", back_populates="user_monitors")  # Temporarily disabled

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'tracked_docket_id', name='uq_user_docket_monitor'),
        Index('ix_user_monitors_active', 'user_id', 'is_active'),
        Index('ix_user_monitors_last_check', 'last_checked_at'),
    )

    def __repr__(self):
        return f"<UserDocketMonitor(user_id={self.user_id}, docket_id={self.tracked_docket_id}, active={self.is_active})>"


# =============================================================================
# DOCUMENT DOWNLOAD TRACKING MODEL
# =============================================================================

class DocumentDownload(Base):
    """
    Model for tracking document downloads.

    Stores information about documents downloaded from free sources (RECAP/IA)
    or paid sources (PACER), including cost tracking for budget management.
    """

    __tablename__ = "document_downloads"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User and case relationship
    user_id = Column(Integer, nullable=False, index=True)
    docket_id = Column(Integer, nullable=False, index=True)  # CourtListener docket ID
    document_id = Column(Integer, nullable=False)  # CourtListener document ID

    # Document metadata
    document_number = Column(Integer)
    description = Column(String(500))
    entry_date = Column(DateTime())

    # Download details
    source = Column(SQLEnum(DocumentDownloadSource), default=DocumentDownloadSource.FREE, nullable=False)
    status = Column(SQLEnum(DocumentDownloadStatus), default=DocumentDownloadStatus.PENDING, nullable=False)

    # Cost tracking (for PACER downloads)
    page_count = Column(Integer, default=0)
    cost = Column(Numeric(10, 2), default=0.00)  # $0.10/page for PACER

    # File storage
    file_path = Column(String(500))  # Path in MinIO/storage
    file_size = Column(BigInteger, default=0)  # Size in bytes
    file_name = Column(String(255))
    mime_type = Column(String(100), default="application/pdf")

    # Timestamps
    created_at = Column(DateTime(), default=lambda: datetime.utcnow(), nullable=False)
    downloaded_at = Column(DateTime())

    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Table constraints and indexes
    __table_args__ = (
        Index('ix_downloads_user_status', 'user_id', 'status'),
        Index('ix_downloads_docket', 'docket_id'),
        Index('ix_downloads_created', 'created_at'),
    )

    def __repr__(self):
        return f"<DocumentDownload(id={self.id}, doc_id={self.document_id}, status={self.status}, source={self.source})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "docket_id": self.docket_id,
            "document_id": self.document_id,
            "document_number": self.document_number,
            "description": self.description,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "source": self.source.value if self.source else None,
            "status": self.status.value if self.status else None,
            "page_count": self.page_count,
            "cost": float(self.cost) if self.cost else 0.0,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }


# =============================================================================
# MODEL REGISTRY AND RELATIONSHIPS
# =============================================================================

# Export all models for easy importing
__all__ = [
    'TrackedDocket',
    'RecapTask',
    'DocketDocument',
    'UserDocketMonitor',
    'DocumentDownload',
    'DocumentDownloadSource',
    'DocumentDownloadStatus',
    'DocketTrackingStatus',
    'CourtType',
    'DocumentType',
    'RecapTaskStatus',
    'RecapTaskType',
    'Priority'
]