"""
Database Models

Unified data models for legal database integration supporting multiple
providers, document types, and search result formats.
"""

import logging
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Set, Union, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DatabaseProvider(str, Enum):
    """Legal database providers"""
    # Commercial Providers
    WESTLAW = "westlaw"
    LEXISNEXIS = "lexisnexis"
    BLOOMBERG_LAW = "bloomberg_law"
    HEINONLINE = "heinonline"
    
    # Free/Open Providers
    COURTLISTENER = "courtlistener"
    GOOGLE_SCHOLAR = "google_scholar"
    JUSTIA = "justia"
    FINDLAW = "findlaw"
    CASELAW_ACCESS_PROJECT = "caselaw_access_project"
    
    # Government Sources
    GOVINFO = "govinfo"
    CONGRESS_GOV = "congress_gov"
    SUPREMECOURT_GOV = "supremecourt_gov"
    USCOURTS_GOV = "uscourts_gov"
    
    # Specialized Sources
    SSRN = "ssrn"
    BEPRESS = "bepress"
    ARXIV = "arxiv"
    JSTOR = "jstor"
    
    # International
    WORLDLII = "worldlii"
    BAILII = "bailii"
    CANLII = "canlii"
    AUSTLII = "austlii"


class DatabaseCapability(str, Enum):
    """Database search and access capabilities"""
    FULL_TEXT_SEARCH = "full_text_search"
    CITATION_SEARCH = "citation_search"
    BOOLEAN_SEARCH = "boolean_search"
    NATURAL_LANGUAGE = "natural_language"
    FIELD_SEARCH = "field_search"
    DATE_FILTERING = "date_filtering"
    JURISDICTION_FILTERING = "jurisdiction_filtering"
    COURT_FILTERING = "court_filtering"
    DOCUMENT_TYPE_FILTERING = "document_type_filtering"
    FULL_DOCUMENT_ACCESS = "full_document_access"
    CITATION_ANALYSIS = "citation_analysis"
    SHEPARDIZING = "shepardizing"
    KEYCITING = "keyciting"
    API_ACCESS = "api_access"
    BULK_DOWNLOAD = "bulk_download"
    REAL_TIME_ALERTS = "real_time_alerts"


class AccessType(str, Enum):
    """Database access types"""
    FREE = "free"
    SUBSCRIPTION = "subscription" 
    PAY_PER_USE = "pay_per_use"
    INSTITUTIONAL = "institutional"
    LIMITED_FREE = "limited_free"
    API_KEY_REQUIRED = "api_key_required"


class ContentType(str, Enum):
    """Content types available in databases"""
    CASES = "cases"
    STATUTES = "statutes"
    REGULATIONS = "regulations"
    CONSTITUTIONS = "constitutions"
    COURT_RULES = "court_rules"
    LAW_REVIEWS = "law_reviews"
    JOURNALS = "journals"
    TREATISES = "treatises"
    PRACTICE_MATERIALS = "practice_materials"
    FORMS = "forms"
    BRIEFS = "briefs"
    PLEADINGS = "pleadings"
    DOCKETS = "dockets"
    ORAL_ARGUMENTS = "oral_arguments"
    NEWS = "news"
    BLOGS = "blogs"
    CLE_MATERIALS = "cle_materials"
    LEGISLATIVE_HISTORY = "legislative_history"
    CONGRESSIONAL_MATERIALS = "congressional_materials"


class GeographicCoverage(str, Enum):
    """Geographic coverage of databases"""
    GLOBAL = "global"
    US_FEDERAL = "us_federal"
    US_STATE = "us_state"
    US_LOCAL = "us_local"
    CANADA = "canada"
    UK = "uk"
    AUSTRALIA = "australia"
    EU = "eu"
    INTERNATIONAL_TREATIES = "international_treaties"
    MULTI_JURISDICTIONAL = "multi_jurisdictional"


class DatabaseConfiguration(BaseModel):
    """Configuration for a legal database"""
    provider: DatabaseProvider
    name: str
    description: str
    
    # Access Information
    base_url: str
    api_endpoint: Optional[str] = None
    access_type: AccessType
    requires_credentials: bool = True
    
    # Capabilities
    capabilities: List[DatabaseCapability] = []
    supported_content: List[ContentType] = []
    geographic_coverage: List[GeographicCoverage] = []
    
    # Search Configuration
    max_results_per_query: int = 100
    supports_pagination: bool = True
    rate_limit_per_minute: int = 60
    
    # Cost Information
    cost_per_query: Optional[float] = None
    cost_per_document: Optional[float] = None
    monthly_subscription_cost: Optional[float] = None
    
    # Quality Metrics
    content_freshness_days: int = 1
    reliability_score: float = 1.0  # 0.0 to 1.0
    completeness_score: float = 1.0  # 0.0 to 1.0
    
    # Technical Details
    response_format: str = "json"
    authentication_method: str = "oauth2"
    sdk_available: bool = False
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class UnifiedQuery(BaseModel):
    """Unified query model for cross-database search"""
    query_id: UUID = Field(default_factory=uuid4)
    
    # Core Query
    query_text: str
    query_type: str = "natural_language"  # natural_language, boolean, citation, field
    
    # Content Filters
    content_types: List[ContentType] = []
    jurisdictions: List[str] = []
    courts: List[str] = []
    
    # Date Filters
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    decision_date_from: Optional[date] = None
    decision_date_to: Optional[date] = None
    
    # Advanced Filters
    case_law_only: bool = False
    primary_law_only: bool = False
    secondary_sources_only: bool = False
    unpublished_opinions: bool = True
    
    # Search Configuration
    max_results: int = 100
    sort_by: str = "relevance"  # relevance, date, jurisdiction, court
    include_cited_cases: bool = False
    include_citing_cases: bool = False
    
    # Provider Preferences
    preferred_providers: List[DatabaseProvider] = []
    exclude_providers: List[DatabaseProvider] = []
    free_sources_only: bool = False
    
    # Quality Requirements
    min_reliability_score: float = 0.0
    require_full_text: bool = False
    
    # User Context
    user_id: Optional[UUID] = None
    practice_area: Optional[str] = None
    research_purpose: Optional[str] = None
    
    # Execution Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timeout_seconds: int = 30


class UnifiedDocument(BaseModel):
    """Unified document model across all databases"""
    document_id: UUID = Field(default_factory=uuid4)
    
    # Source Information
    source_provider: DatabaseProvider
    source_document_id: str
    source_url: Optional[str] = None
    
    # Document Identification
    title: str
    document_type: ContentType
    citation: Optional[str] = None
    docket_number: Optional[str] = None
    
    # Content
    full_text: Optional[str] = None
    summary: Optional[str] = None
    headnotes: List[str] = []
    key_passages: List[str] = []
    
    # Legal Information
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    judges: List[str] = []
    attorneys: List[str] = []
    parties: List[str] = []
    
    # Dates
    decision_date: Optional[date] = None
    filing_date: Optional[date] = None
    publication_date: Optional[date] = None
    
    # Classification
    legal_topics: List[str] = []
    practice_areas: List[str] = []
    key_numbers: List[str] = []  # West Key Numbers if available
    subject_headings: List[str] = []
    
    # Citation Analysis
    cited_cases: List[str] = []
    citing_cases: List[str] = []
    statutes_cited: List[str] = []
    treatment_status: Optional[str] = None
    
    # Quality Metrics
    relevance_score: float = 0.0
    authority_score: float = 0.0  # Based on court level, citations, etc.
    recency_score: float = 0.0
    
    # Access Information
    is_free_access: bool = True
    full_text_available: bool = True
    citation_only: bool = False
    
    # Provider-Specific Metadata
    provider_metadata: Dict[str, Any] = {}
    
    # System Metadata
    indexed_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class UnifiedSearchResult(BaseModel):
    """Unified search result across multiple databases"""
    search_id: UUID = Field(default_factory=uuid4)
    query: UnifiedQuery
    
    # Results Summary
    total_results: int = 0
    results_returned: int = 0
    documents: List[UnifiedDocument] = []
    
    # Provider Breakdown
    provider_results: Dict[str, int] = {}  # provider -> result_count
    provider_response_times: Dict[str, float] = {}  # provider -> response_time_ms
    
    # Search Execution
    search_time_ms: float = 0.0
    providers_searched: List[DatabaseProvider] = []
    providers_failed: List[DatabaseProvider] = []
    
    # Result Quality
    average_relevance: float = 0.0
    coverage_completeness: float = 0.0  # Estimated % of relevant docs found
    result_diversity: float = 0.0  # Diversity across sources/jurisdictions
    
    # Faceting Information
    jurisdiction_facets: Dict[str, int] = {}
    court_facets: Dict[str, int] = {}
    date_facets: Dict[str, int] = {}
    content_type_facets: Dict[str, int] = {}
    topic_facets: Dict[str, int] = {}
    
    # Cost Information
    total_cost: float = 0.0
    cost_by_provider: Dict[str, float] = {}
    
    # Pagination
    page: int = 1
    page_size: int = 100
    has_next_page: bool = False
    next_page_token: Optional[str] = None
    
    # Recommendations
    suggested_refinements: List[str] = []
    related_queries: List[str] = []
    missing_coverage_areas: List[str] = []
    
    # Execution Metadata
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    cache_used: bool = False
    cached_providers: List[DatabaseProvider] = []


class DatabaseMetrics(BaseModel):
    """Performance and usage metrics for a database"""
    provider: DatabaseProvider
    
    # Performance Metrics
    average_response_time_ms: float = 0.0
    success_rate: float = 1.0
    uptime_percentage: float = 100.0
    
    # Usage Metrics
    queries_today: int = 0
    queries_this_month: int = 0
    documents_retrieved: int = 0
    
    # Cost Metrics
    cost_today: float = 0.0
    cost_this_month: float = 0.0
    
    # Quality Metrics
    user_satisfaction_score: float = 0.0
    result_relevance_score: float = 0.0
    
    # Content Metrics
    total_documents: Optional[int] = None
    recent_additions: int = 0
    last_content_update: Optional[datetime] = None
    
    # Error Tracking
    error_count_today: int = 0
    common_errors: List[str] = []
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SearchStrategy(BaseModel):
    """Strategy configuration for unified search execution"""
    strategy_id: str
    name: str
    description: str
    
    # Provider Selection
    provider_priorities: Dict[DatabaseProvider, int] = {}  # Higher number = higher priority
    max_providers: int = 10
    parallel_execution: bool = True
    
    # Result Fusion
    fusion_method: str = "weighted_score"  # round_robin, interleave, weighted_score
    deduplication_threshold: float = 0.85
    max_total_results: int = 100
    
    # Quality Thresholds
    min_relevance_score: float = 0.0
    min_authority_score: float = 0.0
    diversity_weight: float = 0.1
    
    # Cost Management
    max_total_cost: Optional[float] = None
    cost_per_result_threshold: Optional[float] = None
    prefer_free_sources: bool = False
    
    # Timeout Management
    per_provider_timeout_ms: int = 5000
    total_timeout_ms: int = 15000
    
    # Fallback Strategy
    enable_fallback: bool = True
    fallback_providers: List[DatabaseProvider] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class FederatedIndex(BaseModel):
    """Federated index entry for cross-database document linking"""
    index_id: UUID = Field(default_factory=uuid4)
    
    # Document Identity
    normalized_citation: str
    document_hash: str  # Content-based hash for duplicate detection
    
    # Cross-References
    provider_mappings: Dict[DatabaseProvider, str] = {}  # provider -> document_id
    canonical_url: Optional[str] = None
    
    # Consolidated Metadata
    title: str
    court: Optional[str] = None
    decision_date: Optional[date] = None
    jurisdiction: str
    
    # Quality Information
    best_source_provider: DatabaseProvider
    full_text_providers: List[DatabaseProvider] = []
    citation_only_providers: List[DatabaseProvider] = []
    
    # Usage Statistics
    search_frequency: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)