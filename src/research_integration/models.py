"""
Research Integration Models

Core data models for legal research integration including search results,
citations, documents, and research analytics.
"""

import logging
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Set, Union, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class ResearchProvider(str, Enum):
    WESTLAW = "westlaw"
    LEXISNEXIS = "lexisnexis"
    BOTH = "both"


class DocumentType(str, Enum):
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"
    SECONDARY = "secondary"
    BRIEF = "brief"
    PLEADING = "pleading"
    FORM = "form"
    NEWS = "news"
    JOURNAL = "journal"
    TREATISE = "treatise"


class JurisdictionLevel(str, Enum):
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"
    INTERNATIONAL = "international"


class CourtLevel(str, Enum):
    SUPREME = "supreme"
    APPELLATE = "appellate"
    TRIAL = "trial"
    ADMINISTRATIVE = "administrative"
    SPECIALTY = "specialty"


class SearchType(str, Enum):
    BOOLEAN = "boolean"
    NATURAL_LANGUAGE = "natural_language"
    CITATION = "citation"
    HEADNOTE = "headnote"
    KEYCITE = "keycite"
    SHEPARDIZE = "shepardize"


class ResearchQuery(BaseModel):
    """Legal research query with filtering options"""
    query_id: UUID = Field(default_factory=uuid4)
    query_text: str
    search_type: SearchType = SearchType.NATURAL_LANGUAGE
    providers: List[ResearchProvider] = [ResearchProvider.BOTH]
    
    # Content Filters
    document_types: List[DocumentType] = []
    jurisdictions: List[str] = []  # State codes, federal, etc.
    jurisdiction_levels: List[JurisdictionLevel] = []
    court_levels: List[CourtLevel] = []
    
    # Date Filters
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    
    # Result Filters
    max_results: int = 50
    sort_by: str = "relevance"  # relevance, date, jurisdiction
    include_unpublished: bool = False
    include_secondary: bool = True
    
    # Advanced Options
    terms_and_connectors: bool = False
    proximity_search: bool = False
    field_restrictions: Dict[str, str] = {}  # field -> value
    
    # Context
    practice_area: Optional[str] = None
    client_matter: Optional[UUID] = None
    researcher_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('max_results')
    def validate_max_results(cls, v):
        return min(max(v, 1), 1000)  # Between 1 and 1000


class Citation(BaseModel):
    """Legal citation with standardized format"""
    citation_id: UUID = Field(default_factory=uuid4)
    raw_citation: str
    normalized_citation: str
    
    # Citation Components
    case_name: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    court: Optional[str] = None
    year: Optional[int] = None
    
    # Document Information
    document_type: DocumentType
    jurisdiction: Optional[str] = None
    jurisdiction_level: JurisdictionLevel
    
    # Validation Status
    is_valid: bool = True
    validation_errors: List[str] = []
    parallel_citations: List[str] = []
    
    # Treatment
    treatment_status: Optional[str] = None  # Good law, warning, etc.
    citing_references_count: int = 0
    
    # Provider Information
    provider: ResearchProvider
    provider_document_id: Optional[str] = None
    westlaw_key: Optional[str] = None
    lexis_shepards: Optional[str] = None


class LegalDocument(BaseModel):
    """Comprehensive legal document model"""
    document_id: UUID = Field(default_factory=uuid4)
    provider_id: str  # Provider's internal ID
    provider: ResearchProvider
    
    # Basic Information
    title: str
    document_type: DocumentType
    citation: Citation
    
    # Content
    full_text: Optional[str] = None
    summary: Optional[str] = None
    headnotes: List[str] = []
    key_points: List[str] = []
    
    # Metadata
    authors: List[str] = []
    court: Optional[str] = None
    judges: List[str] = []
    decision_date: Optional[date] = None
    filing_date: Optional[date] = None
    
    # Jurisdictional Information
    jurisdiction: str
    jurisdiction_level: JurisdictionLevel
    court_level: CourtLevel
    
    # Topics and Classification
    topics: List[str] = []
    key_numbers: List[str] = []  # West Key Numbers
    practice_areas: List[str] = []
    legal_issues: List[str] = []
    
    # Treatment and Citations
    citing_documents: List[Citation] = []
    cited_documents: List[Citation] = []
    treatment_analysis: Optional[str] = None
    shepard_treatment: Optional[str] = None
    keycite_treatment: Optional[str] = None
    
    # Access Information
    is_published: bool = True
    is_precedential: bool = True
    access_level: str = "full"  # full, limited, citation_only
    
    # Provider-Specific Data
    provider_metadata: Dict[str, Any] = {}
    
    # System Metadata
    indexed_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    relevance_score: Optional[float] = None


class SearchResult(BaseModel):
    """Search result containing documents and metadata"""
    result_id: UUID = Field(default_factory=uuid4)
    query: ResearchQuery
    
    # Results
    documents: List[LegalDocument] = []
    total_results: int = 0
    results_returned: int = 0
    
    # Provider Breakdown
    westlaw_results: int = 0
    lexisnexis_results: int = 0
    
    # Search Metadata
    search_time_ms: int = 0
    providers_searched: List[ResearchProvider] = []
    search_strategy: str = ""
    
    # Faceting/Filtering
    jurisdiction_facets: Dict[str, int] = {}
    court_facets: Dict[str, int] = {}
    date_facets: Dict[str, int] = {}
    document_type_facets: Dict[str, int] = {}
    
    # Quality Metrics
    precision_estimate: Optional[float] = None
    recall_estimate: Optional[float] = None
    result_confidence: Optional[float] = None
    
    # Pagination
    page: int = 1
    page_size: int = 50
    has_more_results: bool = False
    next_page_token: Optional[str] = None
    
    # Execution Details
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time: float = 0.0
    cached: bool = False
    cache_hit_ratio: Optional[float] = None


class ResearchProject(BaseModel):
    """Research project for organizing related searches"""
    project_id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    
    # Organization
    client_matter: Optional[UUID] = None
    practice_area: str
    tags: List[str] = []
    
    # Research Data
    queries: List[UUID] = []  # Query IDs
    saved_documents: List[UUID] = []  # Document IDs
    citations: List[UUID] = []  # Citation IDs
    notes: List[str] = []
    
    # Collaboration
    owner_id: UUID
    shared_with: List[UUID] = []
    permissions: Dict[str, List[str]] = {}  # user_id -> permissions
    
    # Status
    status: str = "active"  # active, archived, completed
    priority: str = "medium"  # low, medium, high, urgent
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[date] = None
    completed_date: Optional[date] = None


class ResearchSession(BaseModel):
    """Research session for tracking user activity"""
    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    project_id: Optional[UUID] = None
    
    # Session Data
    queries_executed: List[UUID] = []
    documents_viewed: List[UUID] = []
    citations_validated: List[UUID] = []
    
    # Activity Metrics
    session_start: datetime = Field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = None
    total_search_time: float = 0.0
    total_reading_time: float = 0.0
    
    # Research Effectiveness
    relevant_documents_found: int = 0
    irrelevant_documents_viewed: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    
    # Provider Usage
    westlaw_usage_time: float = 0.0
    lexisnexis_usage_time: float = 0.0
    provider_preferences: Dict[str, int] = {}
    
    # Cost Tracking
    estimated_cost: float = 0.0
    westlaw_charges: float = 0.0
    lexisnexis_charges: float = 0.0


class CitationValidationResult(BaseModel):
    """Result of citation validation process"""
    validation_id: UUID = Field(default_factory=uuid4)
    original_citation: str
    
    # Validation Status
    is_valid: bool
    confidence_score: float  # 0.0 to 1.0
    validation_method: str
    
    # Standardized Citation
    normalized_citation: Optional[str] = None
    bluebook_citation: Optional[str] = None
    alwd_citation: Optional[str] = None
    
    # Document Information
    document: Optional[LegalDocument] = None
    parallel_citations: List[str] = []
    
    # Validation Issues
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    
    # Treatment Information
    current_treatment: Optional[str] = None
    shepards_signals: List[str] = []
    keycite_flags: List[str] = []
    
    # Provider Data
    provider_validations: Dict[ResearchProvider, Dict[str, Any]] = {}
    
    # Metadata
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validation_source: ResearchProvider


class ResearchAlert(BaseModel):
    """Research alert for monitoring legal developments"""
    alert_id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    
    # Alert Configuration
    query: ResearchQuery
    frequency: str  # daily, weekly, monthly
    active: bool = True
    
    # Delivery Settings
    user_id: UUID
    email_notifications: bool = True
    in_app_notifications: bool = True
    notification_preferences: Dict[str, Any] = {}
    
    # Content Filters
    min_relevance_score: float = 0.7
    max_results_per_alert: int = 10
    exclude_known_documents: bool = True
    
    # Tracking
    last_executed: Optional[datetime] = None
    total_results_sent: int = 0
    documents_found: List[UUID] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APIUsageMetrics(BaseModel):
    """API usage metrics for cost and performance tracking"""
    metric_id: UUID = Field(default_factory=uuid4)
    provider: ResearchProvider
    user_id: UUID
    
    # Usage Counts
    api_calls: int = 0
    documents_retrieved: int = 0
    searches_performed: int = 0
    citations_validated: int = 0
    
    # Performance Metrics
    average_response_time: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Cost Information
    total_cost: float = 0.0
    cost_per_search: float = 0.0
    cost_per_document: float = 0.0
    
    # Time Period
    period_start: datetime
    period_end: datetime
    
    # Provider-Specific Metrics
    westlaw_ku_usage: int = 0  # KeyCite Units
    lexis_transactional_charges: float = 0.0
    
    # Quality Metrics
    user_satisfaction_score: Optional[float] = None
    research_effectiveness: Optional[float] = None
    
    recorded_at: datetime = Field(default_factory=datetime.utcnow)