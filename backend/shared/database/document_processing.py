"""
Document Processing Models for Legal AI System

Models for document storage, processing, analysis, and version control.
Supports various document types, OCR, AI analysis, and secure document management.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, BigInteger,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Numeric, Table, LargeBinary
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import BaseModel, NamedModel, StatusModel, StatusEnum, PriorityEnum, ConfidentialityLevel


# =============================================================================
# ENUMS
# =============================================================================

class DocumentType(enum.Enum):
    """Types of legal documents"""
    PLEADING = "pleading"
    MOTION = "motion"
    ORDER = "order"
    JUDGMENT = "judgment"
    BRIEF = "brief"
    MEMORANDUM = "memorandum"
    LETTER = "letter"
    EMAIL = "email"
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    COMPLAINT = "complaint"
    ANSWER = "answer"
    DISCOVERY = "discovery"
    DEPOSITION = "deposition"
    TRANSCRIPT = "transcript"
    EXHIBIT = "exhibit"
    EVIDENCE = "evidence"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    REPORT = "report"
    FORM = "form"
    CERTIFICATE = "certificate"
    LICENSE = "license"
    PERMIT = "permit"
    OTHER = "other"


class DocumentStatus(enum.Enum):
    """Processing status of documents"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    OCR_PENDING = "ocr_pending"
    OCR_COMPLETE = "ocr_complete"
    ANALYSIS_PENDING = "analysis_pending"
    ANALYSIS_COMPLETE = "analysis_complete"
    ERROR = "error"
    ARCHIVED = "archived"


class DocumentFormat(enum.Enum):
    """Supported document formats"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    RTF = "rtf"
    TXT = "txt"
    HTML = "html"
    XML = "xml"
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    PPT = "ppt"
    PPTX = "pptx"
    MSG = "msg"  # Outlook email
    EML = "eml"  # Email
    TIFF = "tiff"
    JPEG = "jpeg"
    PNG = "png"
    OTHER = "other"


class ProcessingType(enum.Enum):
    """Types of document processing"""
    OCR = "ocr"
    TEXT_EXTRACTION = "text_extraction"
    METADATA_EXTRACTION = "metadata_extraction"
    AI_ANALYSIS = "ai_analysis"
    CLASSIFICATION = "classification"
    REDACTION = "redaction"
    CONVERSION = "conversion"
    INDEXING = "indexing"
    VIRUS_SCAN = "virus_scan"
    HASH_CALCULATION = "hash_calculation"


class VersionType(enum.Enum):
    """Types of document versions"""
    ORIGINAL = "original"
    DRAFT = "draft"
    REVISION = "revision"
    FINAL = "final"
    REDACTED = "redacted"
    CONVERTED = "converted"
    PROCESSED = "processed"


class AccessLevel(enum.Enum):
    """Document access levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    TEAM = "team"
    CASE_ONLY = "case_only"
    ATTORNEY_ONLY = "attorney_only"
    PRIVILEGED = "privileged"
    RESTRICTED = "restricted"


class ReviewStatus(enum.Enum):
    """Document review status"""
    NOT_REVIEWED = "not_reviewed"
    IN_REVIEW = "in_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    PRIVILEGED = "privileged"
    CONFIDENTIAL = "confidential"
    RESPONSIVE = "responsive"
    NON_RESPONSIVE = "non_responsive"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many relationship between documents and cases
document_cases = Table(
    'document_cases',
    BaseModel.metadata,
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    Column('case_id', Integer, ForeignKey('cases.id', ondelete='CASCADE'), primary_key=True),
    Column('relationship_type', String(50), default='evidence'),  # evidence, exhibit, reference
    Column('relevance_score', Numeric(3, 2)),  # 0.0 to 1.0
    Column('added_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column('added_by_id', Integer, ForeignKey('users.id')),
    Index('ix_document_cases_document_id', 'document_id'),
    Index('ix_document_cases_case_id', 'case_id')
)

# Many-to-many relationship between documents (for relationships like attachments)
document_relationships = Table(
    'document_relationships',
    BaseModel.metadata,
    Column('parent_document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    Column('child_document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    Column('relationship_type', String(50)),  # attachment, exhibit, reference, version
    Column('sequence_number', Integer),
    Index('ix_document_relationships_parent', 'parent_document_id'),
    Index('ix_document_relationships_child', 'child_document_id')
)


# =============================================================================
# CORE DOCUMENT MODELS
# =============================================================================

class Document(BaseModel):
    """Core document model with metadata and processing information"""
    
    __tablename__ = 'documents'
    
    # Document Identification
    title = Column(String(500), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    document_number = Column(String(100))  # Internal document numbering
    
    # Document Classification
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.OTHER)
    document_subtype = Column(String(100))  # More specific classification
    category = Column(String(100))  # User-defined category
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    
    # File Information
    file_format = Column(SQLEnum(DocumentFormat), nullable=False)
    mime_type = Column(String(100))
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    file_hash_md5 = Column(String(32), index=True)
    file_hash_sha256 = Column(String(64), unique=True, index=True)
    
    # Storage Information
    storage_path = Column(String(1000))  # Path in storage system
    storage_bucket = Column(String(100))  # Cloud storage bucket
    storage_provider = Column(String(50), default='minio')  # minio, s3, azure, etc.
    is_encrypted = Column(Boolean, default=True, nullable=False)
    encryption_key_id = Column(String(100))
    
    # Content Information
    page_count = Column(Integer)
    word_count = Column(Integer)
    character_count = Column(Integer)
    language = Column(String(10), default='en')
    
    # Processing Status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)
    
    # OCR and Text Extraction
    ocr_performed = Column(Boolean, default=False)
    ocr_confidence = Column(Numeric(5, 2))  # 0-100%
    ocr_language = Column(String(10))
    text_extracted = Column(Boolean, default=False)
    searchable = Column(Boolean, default=False)
    
    # AI Analysis
    ai_analyzed = Column(Boolean, default=False)
    ai_confidence = Column(Numeric(5, 2))  # 0-100%
    ai_summary = Column(Text)
    ai_key_points = Column(JSON, default=list)
    ai_entities = Column(JSON, default=list)  # Named entities
    ai_topics = Column(JSON, default=list)
    sentiment_score = Column(Numeric(3, 2))  # -1.0 to 1.0
    
    # Legal Analysis
    legal_issues = Column(JSON, default=list)
    cited_cases = Column(JSON, default=list)
    cited_statutes = Column(JSON, default=list)
    legal_concepts = Column(JSON, default=list)
    contract_terms = Column(JSON, default=list)  # For contracts
    
    # Document Dates
    document_date = Column(DateTime(timezone=True))  # Date on the document
    received_date = Column(DateTime(timezone=True))  # Date received
    effective_date = Column(DateTime(timezone=True))  # Date document becomes effective
    expiration_date = Column(DateTime(timezone=True))  # Date document expires
    
    # Author and Source Information
    author_name = Column(String(200))
    author_title = Column(String(100))
    author_organization = Column(String(300))
    author_email = Column(String(255))
    source = Column(String(200))  # Where document came from
    source_reference = Column(String(200))  # Reference in source system
    
    # Security and Access
    confidentiality_level = Column(SQLEnum(ConfidentialityLevel), default=ConfidentialityLevel.CONFIDENTIAL)
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.CASE_ONLY)
    is_privileged = Column(Boolean, default=False)
    privilege_log_entry = Column(Text)
    attorney_work_product = Column(Boolean, default=False)
    
    # Review and Approval
    review_status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.NOT_REVIEWED)
    reviewed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    approval_required = Column(Boolean, default=False)
    
    # Version Control
    version_number = Column(String(20), default='1.0')
    version_type = Column(SQLEnum(VersionType), default=VersionType.ORIGINAL)
    parent_version_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    is_current_version = Column(Boolean, default=True)
    
    # Associations
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # External References
    pacer_document_id = Column(String(50))
    court_docket_number = Column(String(100))
    exhibit_number = Column(String(20))
    bates_number_start = Column(String(50))
    bates_number_end = Column(String(50))
    
    # Custom Fields and Metadata
    custom_fields = Column(JSON, default=dict)
    additional_metadata = Column(JSON, default=dict)
    processing_metadata = Column(JSON, default=dict)
    
    # Notes and Comments
    description = Column(Text)
    notes = Column(Text)
    keywords = Column(JSON, default=list)
    
    # Retention and Compliance
    retention_date = Column(DateTime(timezone=True))
    legal_hold = Column(Boolean, default=False)
    destruction_date = Column(DateTime(timezone=True))
    is_record = Column(Boolean, default=False)  # Legal record status
    
    # Relationships
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    firm = relationship("LawFirm", foreign_keys=[firm_id])
    client = relationship("Client", foreign_keys=[client_id])
    parent_version = relationship("Document", remote_side=[BaseModel.id], backref="child_versions")
    
    # Related cases through association table
    cases = relationship("Case", secondary=document_cases, backref="documents")
    
    # Document processing records
    processing_jobs = relationship("DocumentProcessingJob", back_populates="document", cascade="all, delete-orphan")
    annotations = relationship("DocumentAnnotation", back_populates="document", cascade="all, delete-orphan")
    reviews = relationship("DocumentReview", back_populates="document", cascade="all, delete-orphan")
    
    # Full text content (stored separately for large documents)
    content = relationship("DocumentContent", back_populates="document", uselist=False, cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_documents_title_type', 'title', 'document_type'),
        Index('ix_documents_status_priority', 'status', 'priority'),
        Index('ix_documents_client_type', 'client_id', 'document_type'),
        Index('ix_documents_date_uploaded', 'created_at', 'uploaded_by_id'),
        Index('ix_documents_hash', 'file_hash_sha256'),
        Index('ix_documents_searchable', 'searchable', 'status'),
        Index('ix_documents_review_status', 'review_status'),
        CheckConstraint('file_size > 0', name='ck_positive_file_size'),
        CheckConstraint('page_count >= 0', name='ck_non_negative_pages'),
        CheckConstraint('ocr_confidence >= 0 AND ocr_confidence <= 100', name='ck_valid_ocr_confidence'),
    )
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024) if self.file_size else 0
    
    @property
    def is_processed(self) -> bool:
        """Check if document is fully processed"""
        return self.status == DocumentStatus.PROCESSED
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Calculate processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return None
    
    def generate_document_number(self) -> str:
        """Generate unique document number"""
        if self.firm_id:
            year = self.created_at.year
            doc_id = str(self.id).zfill(6)
            self.document_number = f"DOC-{self.firm_id:04d}-{year}-{doc_id}"
        return self.document_number
    
    @validates('file_hash_sha256')
    def validate_hash(self, key, hash_value):
        """Validate hash format"""
        if hash_value and len(hash_value) != 64:
            raise ValueError("SHA256 hash must be 64 characters")
        return hash_value
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title[:50]}...', type='{self.document_type.value if self.document_type else 'unknown'}')>"


class DocumentContent(BaseModel):
    """Extracted text content from documents"""
    
    __tablename__ = 'document_content'
    
    # Document Reference
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, unique=True, index=True)
    
    # Content
    raw_text = Column(Text)  # Raw extracted text
    processed_text = Column(Text)  # Cleaned and processed text
    structured_content = Column(JSON)  # Structured content (headings, tables, etc.)
    
    # OCR Results
    ocr_text = Column(Text)  # OCR-extracted text
    ocr_blocks = Column(JSON)  # OCR text blocks with coordinates
    ocr_confidence_by_page = Column(JSON)  # Per-page confidence scores
    
    # Text Analysis
    word_frequency = Column(JSON)  # Word frequency analysis
    readability_score = Column(Numeric(5, 2))
    complexity_score = Column(Numeric(5, 2))
    
    # Search Vector (PostgreSQL full-text search)
    # search_vector = Column(TSVectorType())  # Would need sqlalchemy-searchable
    
    # Relationships
    document = relationship("Document", back_populates="content")
    
    def __repr__(self):
        return f"<DocumentContent(id={self.id}, document_id={self.document_id})>"


class DocumentProcessingJob(BaseModel):
    """Track document processing jobs and their status"""
    
    __tablename__ = 'document_processing_jobs'
    
    # Job Details
    job_type = Column(SQLEnum(ProcessingType), nullable=False)
    job_name = Column(String(200), nullable=False)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    
    # Document and User
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)
    initiated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Job Status
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    progress_percent = Column(Integer, default=0)  # 0-100
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    estimated_duration = Column(Integer)  # Estimated seconds
    
    # Configuration
    job_parameters = Column(JSON, default=dict)
    processor_settings = Column(JSON, default=dict)
    
    # Results
    result_data = Column(JSON)  # Job output data
    output_files = Column(JSON)  # Generated files
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # System Information
    worker_id = Column(String(100))
    queue_name = Column(String(100))
    celery_task_id = Column(String(155), unique=True)
    
    # Relationships
    document = relationship("Document", back_populates="processing_jobs")
    initiated_by = relationship("User", foreign_keys=[initiated_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_processing_jobs_document_type', 'document_id', 'job_type'),
        Index('ix_processing_jobs_status_priority', 'status', 'priority'),
        Index('ix_processing_jobs_created', 'created_at'),
        CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='ck_valid_progress'),
    )
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate job duration in seconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds())
        return None
    
    def __repr__(self):
        return f"<DocumentProcessingJob(id={self.id}, type='{self.job_type.value}', status='{self.status}')>"


class DocumentAnnotation(BaseModel):
    """Annotations and highlights on documents"""
    
    __tablename__ = 'document_annotations'
    
    # Annotation Details
    annotation_type = Column(String(50), nullable=False)  # highlight, note, redaction, bookmark
    title = Column(String(200))
    content = Column(Text)
    
    # Location in Document
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)
    page_number = Column(Integer)
    x_coordinate = Column(Integer)  # Pixel coordinates
    y_coordinate = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    
    # Text Selection
    selected_text = Column(Text)
    text_start_index = Column(Integer)
    text_end_index = Column(Integer)
    
    # Visual Properties
    color = Column(String(7), default='#FFFF00')  # Hex color
    opacity = Column(Numeric(3, 2), default=0.5)
    
    # User and Context
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    # Status
    is_public = Column(Boolean, default=False)  # Visible to other users
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    document = relationship("Document", back_populates="annotations")
    created_by = relationship("User", foreign_keys=[created_by_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_annotations_document_page', 'document_id', 'page_number'),
        Index('ix_annotations_user_type', 'created_by_id', 'annotation_type'),
        Index('ix_annotations_case', 'case_id'),
    )
    
    def __repr__(self):
        return f"<DocumentAnnotation(id={self.id}, type='{self.annotation_type}', page={self.page_number})>"


class DocumentReview(BaseModel):
    """Document review records for e-discovery and compliance"""
    
    __tablename__ = 'document_reviews'
    
    # Review Details
    review_round = Column(Integer, default=1)
    review_type = Column(String(50), nullable=False)  # first_pass, second_pass, quality_control
    review_status = Column(SQLEnum(ReviewStatus), nullable=False)
    
    # Document and Reviewer
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    supervising_attorney_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Review Results
    is_responsive = Column(Boolean, default=False)
    is_privileged = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=False)
    needs_redaction = Column(Boolean, default=False)
    
    # Coding and Tags
    issue_codes = Column(JSON, default=list)  # Legal issue codes
    topic_tags = Column(JSON, default=list)  # Topic tags
    privilege_tags = Column(JSON, default=list)  # Privilege assertions
    
    # Time Tracking
    review_started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    review_completed_at = Column(DateTime(timezone=True))
    time_spent_minutes = Column(Integer)
    
    # Comments and Notes
    reviewer_notes = Column(Text)
    internal_notes = Column(Text)
    privilege_assertion = Column(Text)
    
    # Quality Control
    qc_required = Column(Boolean, default=False)
    qc_completed = Column(Boolean, default=False)
    qc_reviewer_id = Column(Integer, ForeignKey('users.id'))
    qc_approved = Column(Boolean)
    qc_notes = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    supervising_attorney = relationship("User", foreign_keys=[supervising_attorney_id])
    qc_reviewer = relationship("User", foreign_keys=[qc_reviewer_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_reviews_document_status', 'document_id', 'review_status'),
        Index('ix_reviews_reviewer_date', 'reviewer_id', 'review_completed_at'),
        Index('ix_reviews_responsive', 'is_responsive'),
        Index('ix_reviews_privileged', 'is_privileged'),
        UniqueConstraint('document_id', 'review_round', 'review_type', name='uq_document_review_round_type'),
    )
    
    @property
    def review_duration_minutes(self) -> Optional[int]:
        """Calculate review duration in minutes"""
        if self.review_started_at and self.review_completed_at:
            delta = self.review_completed_at - self.review_started_at
            return int(delta.total_seconds() / 60)
        return None
    
    def __repr__(self):
        return f"<DocumentReview(id={self.id}, document_id={self.document_id}, status='{self.review_status.value}')>"


class DocumentTemplate(NamedModel):
    """Templates for generating standard legal documents"""
    
    __tablename__ = 'document_templates'
    
    # Template Details
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    category = Column(String(100))
    practice_area = Column(String(100))
    
    # Template Content
    template_content = Column(Text, nullable=False)
    template_format = Column(String(20), default='docx')  # docx, pdf, html
    template_variables = Column(JSON, default=list)  # List of variable placeholders
    
    # Usage and Status
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default='1.0')
    usage_count = Column(Integer, default=0)
    
    # Access Control
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_public = Column(Boolean, default=False)
    
    # Approval Workflow
    approval_required = Column(Boolean, default=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    firm = relationship("LawFirm", foreign_keys=[firm_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f"<DocumentTemplate(id={self.id}, name='{self.name}', type='{self.document_type.value}')>"


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    'Document',
    'DocumentContent',
    'DocumentProcessingJob',
    'DocumentAnnotation',
    'DocumentReview',
    'DocumentTemplate',
    'DocumentType',
    'DocumentStatus',
    'DocumentFormat',
    'ProcessingType',
    'VersionType',
    'AccessLevel',
    'ReviewStatus',
    'document_cases',
    'document_relationships'
]