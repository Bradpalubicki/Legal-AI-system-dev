"""
Comprehensive Audit Models for Legal AI System

These models provide complete audit coverage for:
- AI responses and analysis results
- Document access and lifecycle tracking
- Admin actions with justifications
- Hallucination detection with full context
- Search query analytics
- User session activity
- API usage tracking
- Error and exception logging
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean, Enum as SQLEnum,
    JSON, ForeignKey, Index, Numeric, BigInteger, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from datetime import datetime, timezone
import uuid
import enum
from typing import Dict, Any, Optional

# Import base
try:
    from app.src.core.database import Base
except ImportError:
    try:
        from backend.app.src.core.database import Base
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()


# =============================================================================
# ENUMS
# =============================================================================

class AIModelProvider(enum.Enum):
    """AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    HYBRID = "hybrid"


class AIAnalysisType(enum.Enum):
    """Types of AI analysis"""
    DOCUMENT_SUMMARY = "document_summary"
    DOCUMENT_EXTRACTION = "document_extraction"
    LEGAL_RESEARCH = "legal_research"
    CASE_ANALYSIS = "case_analysis"
    CITATION_VALIDATION = "citation_validation"
    RISK_ASSESSMENT = "risk_assessment"
    DEFENSE_GENERATION = "defense_generation"
    QA_RESPONSE = "qa_response"
    MULTI_LAYER_ANALYSIS = "multi_layer_analysis"


class HallucinationType(enum.Enum):
    """Types of hallucinations detected"""
    FABRICATED_PARTY = "fabricated_party"
    FABRICATED_DATE = "fabricated_date"
    FABRICATED_AMOUNT = "fabricated_amount"
    FABRICATED_CITATION = "fabricated_citation"
    FABRICATED_CASE_NUMBER = "fabricated_case_number"
    INCORRECT_FACT = "incorrect_fact"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    MISATTRIBUTION = "misattribution"
    CONTEXT_CONFUSION = "context_confusion"
    OTHER = "other"


class HallucinationSeverity(enum.Enum):
    """Severity of hallucination"""
    LOW = "low"  # Minor issue, doesn't affect core analysis
    MEDIUM = "medium"  # Noticeable error that should be corrected
    HIGH = "high"  # Significant error that affects analysis quality
    CRITICAL = "critical"  # Major fabrication that could cause legal issues


class CorrectionAction(enum.Enum):
    """Actions taken to correct hallucinations"""
    REMOVED = "removed"  # Item was removed entirely
    CORRECTED = "corrected"  # Item was corrected with accurate data
    FLAGGED = "flagged"  # Item was flagged for user review
    VERIFIED_ACCURATE = "verified_accurate"  # False positive - item is accurate


class DocumentAccessType(enum.Enum):
    """Types of document access"""
    VIEW = "view"
    DOWNLOAD = "download"
    PRINT = "print"
    SHARE = "share"
    EXPORT = "export"
    ANALYZE = "analyze"
    EDIT = "edit"
    DELETE = "delete"
    RESTORE = "restore"


class AdminActionType(enum.Enum):
    """Types of admin actions"""
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    USER_RESTORE = "user_restore"
    USER_IMPERSONATE = "user_impersonate"
    ROLE_ASSIGN = "role_assign"
    ROLE_REVOKE = "role_revoke"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    CONFIG_CHANGE = "config_change"
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    AUDIT_VIEW = "audit_view"
    SYSTEM_RESTART = "system_restart"
    CREDITS_ADJUST = "credits_adjust"
    REFUND_ISSUE = "refund_issue"
    LEGAL_HOLD = "legal_hold"
    API_KEY_GENERATE = "api_key_generate"
    API_KEY_REVOKE = "api_key_revoke"


# =============================================================================
# AI RESPONSE LOGGING
# =============================================================================

class AIResponseLog(Base):
    """
    Complete logging of all AI responses for audit and dispute resolution.

    Stores the full context of every AI interaction including:
    - The original input/prompt
    - The complete AI response
    - Model used and parameters
    - Processing time and costs
    - Any post-processing applied
    """
    __tablename__ = "ai_response_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Request identification
    request_id = Column(String(64), unique=True, nullable=False, index=True)
    correlation_id = Column(String(64), nullable=True, index=True)  # Links related requests

    # User and session context
    user_id = Column(Integer, nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    session_id = Column(String(128), nullable=True)
    source_ip = Column(INET, nullable=True)

    # Document context
    document_id = Column(Integer, nullable=True, index=True)
    document_name = Column(String(500), nullable=True)
    document_type = Column(String(100), nullable=True)
    document_hash = Column(String(64), nullable=True)  # SHA-256 of document

    # AI Analysis details
    analysis_type = Column(SQLEnum(AIAnalysisType), nullable=False, index=True)
    model_provider = Column(SQLEnum(AIModelProvider), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)  # e.g., "gpt-4", "claude-3-opus"
    model_version = Column(String(50), nullable=True)

    # Input data (what was sent to AI)
    prompt_template = Column(Text, nullable=True)  # Template used
    input_text = Column(Text, nullable=True)  # Document text or query
    input_tokens = Column(Integer, nullable=True)
    input_parameters = Column(JSONB, nullable=True)  # Temperature, max_tokens, etc.

    # Output data (what AI returned)
    raw_response = Column(Text, nullable=False)  # Unprocessed AI response
    processed_response = Column(JSONB, nullable=True)  # Structured/processed response
    output_tokens = Column(Integer, nullable=True)

    # Quality metrics
    confidence_score = Column(Float, nullable=True)  # Overall confidence 0-1
    quality_score = Column(Float, nullable=True)  # Quality assessment 0-1
    hallucination_count = Column(Integer, default=0)
    correction_count = Column(Integer, default=0)

    # Post-processing
    post_processing_applied = Column(JSONB, nullable=True)  # List of transformations
    final_output = Column(JSONB, nullable=True)  # Final user-facing result

    # Cost tracking
    estimated_cost = Column(Numeric(10, 6), nullable=True)  # In dollars
    actual_cost = Column(Numeric(10, 6), nullable=True)

    # Timing
    request_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    response_timestamp = Column(DateTime(timezone=True), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Status
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Metadata
    api_version = Column(String(20), nullable=True)
    request_headers = Column(JSONB, nullable=True)  # Sanitized headers

    __table_args__ = (
        Index('ix_ai_response_user_time', 'user_id', 'request_timestamp'),
        Index('ix_ai_response_doc_time', 'document_id', 'request_timestamp'),
        Index('ix_ai_response_type_time', 'analysis_type', 'request_timestamp'),
        Index('ix_ai_response_provider_time', 'model_provider', 'request_timestamp'),
    )


# =============================================================================
# HALLUCINATION AUDIT TRAIL
# =============================================================================

class HallucinationAudit(Base):
    """
    Detailed tracking of every hallucination detected and corrected.

    Provides complete transparency into:
    - Exactly what was hallucinated
    - Where in the document/analysis it occurred
    - How it was detected (which layer, what rule)
    - What correction was made
    - Before and after comparison
    """
    __tablename__ = "hallucination_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to parent AI response
    ai_response_id = Column(UUID(as_uuid=True), ForeignKey('ai_response_logs.id'), nullable=False, index=True)

    # Identification
    hallucination_id = Column(String(64), unique=True, nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)  # Order within the analysis

    # Classification
    hallucination_type = Column(SQLEnum(HallucinationType), nullable=False, index=True)
    severity = Column(SQLEnum(HallucinationSeverity), nullable=False, index=True)
    category = Column(String(100), nullable=True)  # More specific category

    # Location in output
    field_name = Column(String(255), nullable=False)  # e.g., "parties[0].name"
    field_path = Column(String(500), nullable=True)  # Full JSON path
    section = Column(String(255), nullable=True)  # Section of analysis
    line_number = Column(Integer, nullable=True)  # If applicable

    # The hallucinated content
    original_value = Column(JSONB, nullable=False)  # What AI originally said
    original_text = Column(Text, nullable=True)  # Text representation

    # Source context
    source_layer = Column(String(100), nullable=False)  # Which AI layer produced this
    source_prompt_excerpt = Column(Text, nullable=True)  # Relevant part of prompt
    source_document_excerpt = Column(Text, nullable=True)  # Relevant part of document

    # Detection details
    detection_method = Column(String(100), nullable=False)  # How it was detected
    detection_layer = Column(String(100), nullable=False)  # Which layer detected it
    detection_rule = Column(String(255), nullable=True)  # Specific rule that triggered
    detection_confidence = Column(Float, nullable=False)  # 0-1 confidence
    detection_reasoning = Column(Text, nullable=True)  # Why flagged as hallucination

    # Cross-validation details
    cross_validation_performed = Column(Boolean, default=False)
    cross_validation_sources = Column(JSONB, nullable=True)  # What was checked
    cross_validation_results = Column(JSONB, nullable=True)  # Results of checks

    # Correction action
    correction_action = Column(SQLEnum(CorrectionAction), nullable=False)
    corrected_value = Column(JSONB, nullable=True)  # What it was corrected to
    corrected_text = Column(Text, nullable=True)  # Text representation
    correction_source = Column(String(255), nullable=True)  # Where correct info came from
    correction_reasoning = Column(Text, nullable=True)  # Why this correction

    # Impact assessment
    impact_assessment = Column(Text, nullable=True)  # How this affected analysis
    affected_downstream = Column(JSONB, nullable=True)  # Other fields affected

    # Timing
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    corrected_at = Column(DateTime(timezone=True), nullable=True)

    # User visibility
    shown_to_user = Column(Boolean, default=False)
    user_notified = Column(Boolean, default=False)
    user_acknowledged = Column(Boolean, default=False)
    user_feedback = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_halluc_response_time', 'ai_response_id', 'detected_at'),
        Index('ix_halluc_type_severity', 'hallucination_type', 'severity'),
        Index('ix_halluc_field', 'field_name'),
        Index('ix_halluc_detection', 'detection_method', 'detection_layer'),
    )


# =============================================================================
# DOCUMENT ACCESS LOGGING
# =============================================================================

class DocumentAccessLog(Base):
    """
    Complete tracking of all document access for legal compliance.

    Records every time a document is:
    - Viewed, downloaded, or printed
    - Shared or exported
    - Analyzed by AI
    - Modified or deleted
    """
    __tablename__ = "document_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_id = Column(String(64), unique=True, nullable=False, index=True)

    # User context
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    user_role = Column(String(50), nullable=True)
    session_id = Column(String(128), nullable=True)

    # Document identification
    document_id = Column(Integer, nullable=False, index=True)
    document_name = Column(String(500), nullable=False)
    document_type = Column(String(100), nullable=True)
    document_hash = Column(String(64), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)

    # Access details
    access_type = Column(SQLEnum(DocumentAccessType), nullable=False, index=True)
    access_method = Column(String(100), nullable=True)  # API, UI, batch, etc.
    access_reason = Column(Text, nullable=True)  # Why accessed (if provided)

    # Context
    case_id = Column(Integer, nullable=True, index=True)
    case_name = Column(String(500), nullable=True)
    matter_id = Column(String(100), nullable=True)
    client_id = Column(Integer, nullable=True)

    # Source information
    source_ip = Column(INET, nullable=False)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(128), nullable=True)
    api_endpoint = Column(String(255), nullable=True)

    # For shares/exports
    shared_with = Column(JSONB, nullable=True)  # Recipients
    export_format = Column(String(50), nullable=True)

    # For modifications
    modification_type = Column(String(100), nullable=True)
    before_state = Column(JSONB, nullable=True)  # State before change
    after_state = Column(JSONB, nullable=True)  # State after change

    # Timing
    accessed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    duration_seconds = Column(Integer, nullable=True)  # Time spent viewing

    # Result
    success = Column(Boolean, nullable=False, default=True)
    bytes_transferred = Column(BigInteger, nullable=True)
    pages_viewed = Column(Integer, nullable=True)

    __table_args__ = (
        Index('ix_doc_access_user_time', 'user_id', 'accessed_at'),
        Index('ix_doc_access_doc_time', 'document_id', 'accessed_at'),
        Index('ix_doc_access_type_time', 'access_type', 'accessed_at'),
        Index('ix_doc_access_case', 'case_id', 'accessed_at'),
    )


# =============================================================================
# ADMIN ACTION LOGGING
# =============================================================================

class AdminActionLog(Base):
    """
    Complete audit trail of all administrative actions.

    Every admin action requires:
    - Clear identification of who did what
    - Justification/reason for the action
    - Before and after state
    - Approval chain if required
    """
    __tablename__ = "admin_action_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(String(64), unique=True, nullable=False, index=True)

    # Admin performing action
    admin_id = Column(Integer, nullable=False, index=True)
    admin_email = Column(String(255), nullable=False)
    admin_role = Column(String(50), nullable=False)

    # Action details
    action_type = Column(SQLEnum(AdminActionType), nullable=False, index=True)
    action_description = Column(Text, nullable=False)

    # Target of action
    target_type = Column(String(100), nullable=False)  # user, document, config, etc.
    target_id = Column(String(255), nullable=True, index=True)
    target_name = Column(String(500), nullable=True)

    # State tracking
    before_state = Column(JSONB, nullable=True)
    after_state = Column(JSONB, nullable=True)
    changes_made = Column(JSONB, nullable=True)  # Diff of changes

    # Justification (REQUIRED)
    reason = Column(Text, nullable=False)  # Why this action was taken
    ticket_number = Column(String(100), nullable=True)  # Support ticket if applicable
    authorization_reference = Column(String(255), nullable=True)  # Approval reference

    # Approval chain
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Source information
    source_ip = Column(INET, nullable=False)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(128), nullable=True)

    # Timing
    performed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Status
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    # Reversibility
    reversible = Column(Boolean, default=True)
    reversed = Column(Boolean, default=False)
    reversed_at = Column(DateTime(timezone=True), nullable=True)
    reversed_by = Column(Integer, nullable=True)
    reversal_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_admin_action_admin_time', 'admin_id', 'performed_at'),
        Index('ix_admin_action_target_time', 'target_type', 'target_id', 'performed_at'),
        Index('ix_admin_action_type_time', 'action_type', 'performed_at'),
    )


# =============================================================================
# SEARCH QUERY LOGGING
# =============================================================================

class SearchQueryLog(Base):
    """
    Track all search queries for analytics and audit.

    Helps identify:
    - What users are searching for
    - Zero-result searches (content gaps)
    - Search patterns and trends
    - Abuse detection
    """
    __tablename__ = "search_query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(String(64), unique=True, nullable=False, index=True)

    # User context
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(128), nullable=True)
    source_ip = Column(INET, nullable=True)

    # Query details
    query_text = Column(Text, nullable=False)
    query_type = Column(String(100), nullable=False)  # case_search, document_search, legal_research
    search_filters = Column(JSONB, nullable=True)  # Applied filters
    search_parameters = Column(JSONB, nullable=True)  # Other parameters

    # Results
    results_count = Column(Integer, nullable=False, default=0)
    results_returned = Column(Integer, nullable=True)  # Number shown to user
    top_result_ids = Column(JSONB, nullable=True)  # IDs of top results

    # User actions after search
    result_clicked = Column(Boolean, default=False)
    clicked_result_id = Column(String(255), nullable=True)
    clicked_position = Column(Integer, nullable=True)

    # Performance
    search_time_ms = Column(Integer, nullable=True)

    # Timing
    searched_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_search_user_time', 'user_id', 'searched_at'),
        Index('ix_search_type_time', 'query_type', 'searched_at'),
        Index('ix_search_results', 'results_count', 'searched_at'),
    )


# =============================================================================
# API USAGE LOGGING
# =============================================================================

class APIUsageLog(Base):
    """
    Comprehensive API usage tracking for billing and audit.
    """
    __tablename__ = "api_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(64), unique=True, nullable=False, index=True)

    # User context
    user_id = Column(Integer, nullable=True, index=True)
    api_key_id = Column(String(64), nullable=True, index=True)

    # Request details
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    path_params = Column(JSONB, nullable=True)
    query_params = Column(JSONB, nullable=True)
    request_size_bytes = Column(Integer, nullable=True)

    # Response details
    status_code = Column(Integer, nullable=False)
    response_size_bytes = Column(Integer, nullable=True)

    # Performance
    response_time_ms = Column(Integer, nullable=False)

    # Source
    source_ip = Column(INET, nullable=False)
    user_agent = Column(Text, nullable=True)

    # Cost attribution
    credits_used = Column(Numeric(10, 4), nullable=True)
    billing_category = Column(String(100), nullable=True)

    # Timing
    requested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_api_usage_user_time', 'user_id', 'requested_at'),
        Index('ix_api_usage_endpoint_time', 'endpoint', 'requested_at'),
        Index('ix_api_usage_status', 'status_code', 'requested_at'),
    )


# =============================================================================
# USER SESSION ACTIVITY
# =============================================================================

class UserSessionActivity(Base):
    """
    Track user session activity for security and usage analysis.
    """
    __tablename__ = "user_session_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Session identification
    session_id = Column(String(128), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Activity details
    activity_type = Column(String(100), nullable=False)  # page_view, action, api_call
    activity_name = Column(String(255), nullable=False)
    activity_details = Column(JSONB, nullable=True)

    # Page/route info
    page_path = Column(String(500), nullable=True)
    page_title = Column(String(255), nullable=True)
    referrer = Column(String(500), nullable=True)

    # Source
    source_ip = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet

    # Timing
    activity_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    duration_seconds = Column(Integer, nullable=True)

    __table_args__ = (
        Index('ix_session_activity_user_time', 'user_id', 'activity_at'),
        Index('ix_session_activity_session_time', 'session_id', 'activity_at'),
    )


# =============================================================================
# ERROR LOGGING
# =============================================================================

class ErrorLog(Base):
    """
    Comprehensive error logging for debugging and audit.
    """
    __tablename__ = "error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    error_id = Column(String(64), unique=True, nullable=False, index=True)

    # Context
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(128), nullable=True)
    request_id = Column(String(64), nullable=True, index=True)

    # Error details
    error_type = Column(String(255), nullable=False, index=True)
    error_code = Column(String(50), nullable=True, index=True)
    error_message = Column(Text, nullable=False)
    error_stack_trace = Column(Text, nullable=True)

    # Location
    component = Column(String(100), nullable=False)  # backend, frontend, worker
    module = Column(String(255), nullable=True)
    function_name = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)

    # Request context
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    request_data = Column(JSONB, nullable=True)  # Sanitized request data

    # Environment
    environment = Column(String(50), nullable=True)  # production, staging, development
    server_id = Column(String(100), nullable=True)
    version = Column(String(50), nullable=True)

    # Source
    source_ip = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Impact
    severity = Column(String(20), nullable=False, default='error')  # warning, error, critical
    affected_users = Column(Integer, nullable=True)

    # Resolution
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timing
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_error_type_time', 'error_type', 'occurred_at'),
        Index('ix_error_severity_time', 'severity', 'occurred_at'),
        Index('ix_error_resolved', 'resolved', 'occurred_at'),
    )


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    # Enums
    'AIModelProvider',
    'AIAnalysisType',
    'HallucinationType',
    'HallucinationSeverity',
    'CorrectionAction',
    'DocumentAccessType',
    'AdminActionType',
    # Models
    'AIResponseLog',
    'HallucinationAudit',
    'DocumentAccessLog',
    'AdminActionLog',
    'SearchQueryLog',
    'APIUsageLog',
    'UserSessionActivity',
    'ErrorLog',
]
