"""
Data models for bulk document processing and categorization system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pathlib import Path


class DocumentCategory(Enum):
    """Document category classifications."""
    # Legal Documents
    COMPLAINT = "complaint"
    MOTION = "motion"
    BRIEF = "brief"
    DISCOVERY = "discovery"
    PLEADING = "pleading"
    JUDGMENT = "judgment"
    ORDER = "order"
    NOTICE = "notice"
    SUBPOENA = "subpoena"
    DEPOSITION = "deposition"

    # Bankruptcy Documents
    BANKRUPTCY_PETITION = "bankruptcy_petition"
    BANKRUPTCY_SCHEDULE = "bankruptcy_schedule"
    BANKRUPTCY_PLAN = "bankruptcy_plan"
    
    # Contracts and Agreements
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    LICENSE = "license"
    NDA = "nda"
    EMPLOYMENT_AGREEMENT = "employment_agreement"
    SERVICE_AGREEMENT = "service_agreement"
    
    # Corporate Documents
    INCORPORATION = "incorporation"
    BYLAWS = "bylaws"
    BOARD_RESOLUTION = "board_resolution"
    SHAREHOLDER_AGREEMENT = "shareholder_agreement"
    SEC_FILING = "sec_filing"
    
    # Regulatory and Compliance
    REGULATORY_FILING = "regulatory_filing"
    COMPLIANCE_REPORT = "compliance_report"
    AUDIT_REPORT = "audit_report"
    POLICY_DOCUMENT = "policy_document"
    
    # Intellectual Property
    PATENT = "patent"
    TRADEMARK = "trademark"
    COPYRIGHT = "copyright"
    IP_LICENSE = "ip_license"
    
    # Financial Documents
    FINANCIAL_STATEMENT = "financial_statement"
    TAX_DOCUMENT = "tax_document"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    
    # Correspondence
    EMAIL = "email"
    LETTER = "letter"
    MEMO = "memo"
    
    # Other
    RESEARCH_MEMO = "research_memo"
    EXPERT_REPORT = "expert_report"
    EXHIBIT = "exhibit"
    TRANSCRIPT = "transcript"
    OTHER = "other"
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """Status of document processing."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    CATEGORIZING = "categorizing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    DUPLICATE = "duplicate"


class DownloadSource(Enum):
    """Source systems for document downloads."""
    PACER = "pacer"
    WESTLAW = "westlaw"
    LEXIS_NEXIS = "lexis_nexis"
    GOOGLE_DRIVE = "google_drive"
    SHAREPOINT = "sharepoint"
    DROPBOX = "dropbox"
    FTP = "ftp"
    EMAIL = "email"
    LOCAL_FOLDER = "local_folder"
    WEB_SCRAPING = "web_scraping"
    API = "api"
    OTHER = "other"


class CategoryConfidence(Enum):
    """Confidence levels for document categorization."""
    VERY_HIGH = "very_high"  # 90%+
    HIGH = "high"            # 75-90%
    MEDIUM = "medium"        # 50-75%
    LOW = "low"              # 25-50%
    VERY_LOW = "very_low"    # <25%


@dataclass
class DocumentHash:
    """Document hash information for deduplication."""
    md5: str
    sha256: str
    content_hash: str  # Hash of text content only
    size: int
    created_at: datetime


@dataclass
class DocumentMetadata:
    """Comprehensive document metadata."""
    # Basic identification (required fields first)
    document_id: str
    filename: str
    file_size: int
    file_type: str
    mime_type: str
    category: DocumentCategory
    category_confidence: CategoryConfidence
    processing_status: ProcessingStatus
    download_source: DownloadSource

    # Optional fields
    original_path: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    language: Optional[str] = None
    subcategories: List[str] = field(default_factory=list)

    # Legal-specific metadata (optional)
    case_number: Optional[str] = None
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    filing_date: Optional[datetime] = None
    parties: List[str] = field(default_factory=list)
    attorneys: List[str] = field(default_factory=list)

    # Document relationships
    parent_document_id: Optional[str] = None
    related_documents: List[str] = field(default_factory=list)
    document_set: Optional[str] = None
    downloaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # Hash and deduplication
    document_hash: Optional[DocumentHash] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    
    # Storage information
    storage_path: Optional[str] = None
    compressed: bool = False
    encrypted: bool = False
    
    # Custom fields
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Audit trail
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "original_path": self.original_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "page_count": self.page_count,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "language": self.language,
            "category": self.category.value,
            "category_confidence": self.category_confidence.value,
            "subcategories": self.subcategories,
            "case_number": self.case_number,
            "court": self.court,
            "jurisdiction": self.jurisdiction,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "parties": self.parties,
            "attorneys": self.attorneys,
            "parent_document_id": self.parent_document_id,
            "related_documents": self.related_documents,
            "document_set": self.document_set,
            "processing_status": self.processing_status.value,
            "download_source": self.download_source.value,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "document_hash": {
                "md5": self.document_hash.md5,
                "sha256": self.document_hash.sha256,
                "content_hash": self.document_hash.content_hash,
                "size": self.document_hash.size,
                "created_at": self.document_hash.created_at.isoformat()
            } if self.document_hash else None,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "storage_path": self.storage_path,
            "compressed": self.compressed,
            "encrypted": self.encrypted,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by
        }


@dataclass
class ProcessingError:
    """Error information from document processing."""
    error_id: str
    error_type: str
    error_message: str
    error_details: Dict[str, Any]
    document_id: Optional[str]
    step: str
    retry_count: int
    max_retries: int
    is_retryable: bool
    occurred_at: datetime
    resolved_at: Optional[datetime] = None


@dataclass
class BatchResult:
    """Results from batch document processing."""
    # Required fields first
    batch_id: str
    total_documents: int
    successful: int
    failed: int
    duplicates: int
    skipped: int
    total_size_bytes: int
    processing_time_seconds: float
    download_time_seconds: float
    categorization_time_seconds: float
    started_at: datetime

    # Optional fields with defaults
    completed_at: Optional[datetime] = None
    category_counts: Dict[DocumentCategory, int] = field(default_factory=dict)
    errors: List[ProcessingError] = field(default_factory=list)
    error_summary: Dict[str, int] = field(default_factory=dict)
    successful_documents: List[str] = field(default_factory=list)
    failed_documents: List[str] = field(default_factory=list)
    duplicate_documents: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_documents == 0:
            return 0.0
        return (self.successful / self.total_documents) * 100
    
    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time per document."""
        if self.successful == 0:
            return 0.0
        return self.processing_time_seconds / self.successful
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary."""
        return {
            "batch_id": self.batch_id,
            "summary": {
                "total_documents": self.total_documents,
                "successful": self.successful,
                "failed": self.failed,
                "duplicates": self.duplicates,
                "skipped": self.skipped,
                "success_rate": round(self.success_rate, 2),
                "processing_time": round(self.processing_time_seconds, 2),
                "average_time_per_doc": round(self.average_processing_time, 2)
            },
            "category_breakdown": {
                category.value: count 
                for category, count in self.category_counts.items()
            },
            "error_summary": self.error_summary,
            "timestamps": {
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_minutes": (
                    (self.completed_at - self.started_at).total_seconds() / 60
                    if self.completed_at else None
                )
            }
        }


def get_category_from_filename(filename: str) -> DocumentCategory:
    """Attempt to determine category from filename patterns."""
    filename_lower = filename.lower()
    
    # Legal document patterns
    if any(word in filename_lower for word in ["complaint", "petition"]):
        return DocumentCategory.COMPLAINT
    elif any(word in filename_lower for word in ["motion", "mtd", "msj"]):
        return DocumentCategory.MOTION
    elif "brief" in filename_lower:
        return DocumentCategory.BRIEF
    elif any(word in filename_lower for word in ["discovery", "interrogator", "request"]):
        return DocumentCategory.DISCOVERY
    elif any(word in filename_lower for word in ["order", "judgment"]):
        return DocumentCategory.ORDER
    elif "notice" in filename_lower:
        return DocumentCategory.NOTICE
    
    # Contract patterns
    elif any(word in filename_lower for word in ["contract", "agreement", "agmt"]):
        return DocumentCategory.CONTRACT
    elif "nda" in filename_lower or "non-disclosure" in filename_lower:
        return DocumentCategory.NDA
    
    # Corporate patterns
    elif any(word in filename_lower for word in ["bylaw", "incorporation", "articles"]):
        return DocumentCategory.INCORPORATION
    elif "resolution" in filename_lower:
        return DocumentCategory.BOARD_RESOLUTION
    
    # IP patterns
    elif "patent" in filename_lower:
        return DocumentCategory.PATENT
    elif "trademark" in filename_lower:
        return DocumentCategory.TRADEMARK
    elif "copyright" in filename_lower:
        return DocumentCategory.COPYRIGHT
    
    # Financial patterns
    elif any(word in filename_lower for word in ["financial", "balance", "income"]):
        return DocumentCategory.FINANCIAL_STATEMENT
    elif any(word in filename_lower for word in ["tax", "1040", "w2", "w9"]):
        return DocumentCategory.TAX_DOCUMENT
    elif "invoice" in filename_lower:
        return DocumentCategory.INVOICE
    
    # Communication patterns
    elif any(word in filename_lower for word in ["email", "msg"]):
        return DocumentCategory.EMAIL
    elif "letter" in filename_lower:
        return DocumentCategory.LETTER
    elif "memo" in filename_lower:
        return DocumentCategory.MEMO
    
    # Other patterns
    elif "transcript" in filename_lower:
        return DocumentCategory.TRANSCRIPT
    elif "exhibit" in filename_lower:
        return DocumentCategory.EXHIBIT
    
    return DocumentCategory.UNKNOWN


def get_category_confidence_from_score(score: float) -> CategoryConfidence:
    """Convert numerical confidence score to confidence level."""
    if score >= 0.9:
        return CategoryConfidence.VERY_HIGH
    elif score >= 0.75:
        return CategoryConfidence.HIGH
    elif score >= 0.5:
        return CategoryConfidence.MEDIUM
    elif score >= 0.25:
        return CategoryConfidence.LOW
    else:
        return CategoryConfidence.VERY_LOW


def is_legal_document_type(file_type: str) -> bool:
    """Check if file type is commonly used for legal documents."""
    legal_types = {
        ".pdf", ".doc", ".docx", ".txt", ".rtf", 
        ".odt", ".pages", ".wpd", ".wps"
    }
    return file_type.lower() in legal_types


def get_mime_type_from_extension(filename: str) -> str:
    """Get MIME type from file extension."""
    extension = Path(filename).suffix.lower()
    
    mime_types = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".rtf": "application/rtf",
        ".html": "text/html",
        ".htm": "text/html",
        ".xml": "application/xml",
        ".json": "application/json",
        ".csv": "text/csv",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".odt": "application/vnd.oasis.opendocument.text",
        ".ods": "application/vnd.oasis.opendocument.spreadsheet",
        ".odp": "application/vnd.oasis.opendocument.presentation",
        ".pages": "application/vnd.apple.pages",
        ".numbers": "application/vnd.apple.numbers",
        ".keynote": "application/vnd.apple.keynote"
    }
    
    return mime_types.get(extension, "application/octet-stream")