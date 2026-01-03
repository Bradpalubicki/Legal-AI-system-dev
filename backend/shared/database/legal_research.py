"""
Legal Research Models for Legal AI System

Models for legal research, case law, statutes, regulations, and external
legal database integration (Westlaw, LexisNexis, CourtListener, etc.).
"""

import enum
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, Date,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Numeric, Table, Float
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel, NamedModel, StatusModel, StatusEnum, PriorityEnum


# =============================================================================
# ENUMS
# =============================================================================

class ResearchDatabase(enum.Enum):
    """Legal research databases"""
    WESTLAW = "westlaw"
    LEXISNEXIS = "lexisnexis"
    COURTLISTENER = "courtlistener"
    JUSTIA = "justia"
    GOOGLE_SCHOLAR = "google_scholar"
    BLOOMBERG_LAW = "bloomberg_law"
    FASTCASE = "fastcase"
    CASETEXT = "casetext"
    VLEX = "vlex"
    HEINONLINE = "heinonline"
    INTERNAL = "internal"
    OTHER = "other"


class LegalSourceType(enum.Enum):
    """Types of legal sources"""
    CASE_LAW = "case_law"
    STATUTE = "statute"
    REGULATION = "regulation"
    CONSTITUTIONAL = "constitutional"
    ADMINISTRATIVE = "administrative"
    TREATY = "treaty"
    ORDINANCE = "ordinance"
    RULE = "rule"
    PRACTICE_GUIDE = "practice_guide"
    SECONDARY_AUTHORITY = "secondary_authority"
    LAW_REVIEW = "law_review"
    LEGAL_ENCYCLOPEDIA = "legal_encyclopedia"
    FORM = "form"
    BRIEF = "brief"
    OPINION = "opinion"


class CourtType(enum.Enum):
    """Types of courts"""
    SUPREME_COURT_US = "supreme_court_us"
    CIRCUIT_COURT = "circuit_court"
    DISTRICT_COURT = "district_court"
    STATE_SUPREME = "state_supreme"
    STATE_APPELLATE = "state_appellate"
    STATE_TRIAL = "state_trial"
    BANKRUPTCY = "bankruptcy"
    TAX_COURT = "tax_court"
    ADMINISTRATIVE = "administrative"
    ARBITRATION = "arbitration"
    INTERNATIONAL = "international"
    MILITARY = "military"
    OTHER = "other"


class ResearchStatus(enum.Enum):
    """Status of research projects"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class CitationRelevance(enum.Enum):
    """Relevance levels for legal citations"""
    HIGHLY_RELEVANT = "highly_relevant"
    RELEVANT = "relevant"
    SOMEWHAT_RELEVANT = "somewhat_relevant"
    TANGENTIALLY_RELEVANT = "tangentially_relevant"
    NOT_RELEVANT = "not_relevant"


class LegalAuthority(enum.Enum):
    """Authority levels of legal sources"""
    BINDING = "binding"
    PERSUASIVE = "persuasive"
    INFORMATIONAL = "informational"


# =============================================================================
# CORE RESEARCH MODELS
# =============================================================================

class ResearchProject(BaseModel):
    """Research projects and queries"""
    
    __tablename__ = 'research_projects'
    
    # Project Details
    title = Column(String(300), nullable=False)
    description = Column(Text)
    research_question = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)
    
    # Context
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=False)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    supervising_attorney_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Status and Progress
    status = Column(SQLEnum(ResearchStatus), default=ResearchStatus.ACTIVE)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    progress_percent = Column(Integer, default=0)  # 0-100
    
    # Scope and Parameters
    practice_areas = Column(JSON, default=list)
    jurisdictions = Column(JSON, default=list)
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    legal_issues = Column(JSON, default=list)
    
    # Deliverables
    due_date = Column(DateTime(timezone=True))
    estimated_hours = Column(Numeric(5, 2))
    actual_hours = Column(Numeric(5, 2))
    
    # Research Strategy
    research_databases = Column(JSON, default=list)  # List of databases to search
    search_terms = Column(JSON, default=list)
    boolean_queries = Column(JSON, default=list)
    
    # Results Summary
    total_sources_found = Column(Integer, default=0)
    relevant_sources = Column(Integer, default=0)
    key_findings = Column(Text)
    conclusions = Column(Text)
    recommendations = Column(Text)
    
    # Cost Tracking
    database_costs = Column(Numeric(10, 2), default=0)
    external_research_costs = Column(Numeric(10, 2), default=0)
    
    # Deliverable Files
    research_memo_path = Column(String(500))
    supporting_documents = Column(JSON, default=list)
    
    # Quality Control
    reviewed_by_id = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    approved = Column(Boolean, default=False)
    
    # Relationships
    case = relationship("Case", foreign_keys=[case_id])
    client = relationship("Client", foreign_keys=[client_id])
    firm = relationship("LawFirm", foreign_keys=[firm_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    supervising_attorney = relationship("User", foreign_keys=[supervising_attorney_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    searches = relationship("LegalSearch", back_populates="research_project", cascade="all, delete-orphan")
    sources = relationship("LegalSource", back_populates="research_project")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_research_projects_case_status', 'case_id', 'status'),
        Index('ix_research_projects_assigned_status', 'assigned_to_id', 'status'),
        Index('ix_research_projects_firm_date', 'firm_id', 'created_at'),
        Index('ix_research_projects_due_date', 'due_date'),
        CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='ck_valid_progress'),
    )
    
    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue"""
        return (self.due_date and 
                self.due_date < datetime.now(timezone.utc) and 
                self.status == ResearchStatus.ACTIVE)
    
    @property
    def relevance_rate(self) -> float:
        """Calculate relevance rate of found sources"""
        if self.total_sources_found == 0:
            return 0.0
        return self.relevant_sources / self.total_sources_found
    
    def __repr__(self):
        return f"<ResearchProject(id={self.id}, title='{self.title[:50]}...', status='{self.status.value}')>"


class LegalSearch(BaseModel):
    """Individual search queries and results"""
    
    __tablename__ = 'legal_searches'
    
    # Search Details
    query = Column(String(1000), nullable=False)
    search_type = Column(String(50), default='boolean')  # boolean, natural_language, citation
    database = Column(SQLEnum(ResearchDatabase), nullable=False)
    
    # Research Project
    research_project_id = Column(Integer, ForeignKey('research_projects.id'), nullable=False, index=True)
    
    # Search Parameters
    jurisdiction = Column(String(100))
    court_level = Column(String(50))
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    practice_area = Column(String(100))
    search_filters = Column(JSON, default=dict)
    
    # Execution Details
    executed_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    execution_time_ms = Column(Integer)
    
    # Results
    total_results = Column(Integer, default=0)
    results_retrieved = Column(Integer, default=0)
    results_relevant = Column(Integer, default=0)
    
    # Cost and Usage
    cost_usd = Column(Numeric(8, 2))
    documents_accessed = Column(Integer, default=0)
    pages_viewed = Column(Integer, default=0)
    
    # Search Strategy
    search_notes = Column(Text)
    search_refinements = Column(JSON, default=list)  # History of query refinements
    
    # API Response Data
    raw_response = Column(JSON)  # Store API response for analysis
    api_metadata = Column(JSON, default=dict)
    
    # Relationships
    research_project = relationship("ResearchProject", back_populates="searches")
    executed_by = relationship("User", foreign_keys=[executed_by_id])
    results = relationship("LegalSearchResult", back_populates="search", cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_legal_searches_project_date', 'research_project_id', 'executed_at'),
        Index('ix_legal_searches_database_date', 'database', 'executed_at'),
        Index('ix_legal_searches_user_date', 'executed_by_id', 'executed_at'),
    )
    
    @property
    def relevance_rate(self) -> float:
        """Calculate relevance rate of search results"""
        if self.results_retrieved == 0:
            return 0.0
        return self.results_relevant / self.results_retrieved
    
    def __repr__(self):
        return f"<LegalSearch(id={self.id}, database='{self.database.value}', results={self.total_results})>"


class LegalSearchResult(BaseModel):
    """Individual results from legal searches"""
    
    __tablename__ = 'legal_search_results'
    
    # Result Identification
    search_id = Column(Integer, ForeignKey('legal_searches.id'), nullable=False, index=True)
    result_rank = Column(Integer, nullable=False)  # Position in search results
    external_id = Column(String(200))  # ID in external database
    
    # Document Information
    title = Column(String(1000), nullable=False)
    citation = Column(String(300))
    court_name = Column(String(200))
    court_type = Column(SQLEnum(CourtType))
    date_decided = Column(Date)
    
    # Content
    summary = Column(Text)
    headnotes = Column(Text)
    full_text_available = Column(Boolean, default=False)
    
    # Metadata
    source_type = Column(SQLEnum(LegalSourceType))
    jurisdiction = Column(String(100))
    practice_areas = Column(JSON, default=list)
    legal_topics = Column(JSON, default=list)
    
    # Relevance and Review
    relevance = Column(SQLEnum(CitationRelevance))
    relevance_score = Column(Numeric(3, 2))  # 0.0 to 1.0
    reviewed_by_id = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    
    # Access Information
    database_url = Column(String(1000))
    pdf_url = Column(String(1000))
    access_cost = Column(Numeric(6, 2))
    accessed = Column(Boolean, default=False)
    accessed_at = Column(DateTime(timezone=True))
    
    # Document Analysis
    key_passages = Column(JSON, default=list)
    cited_cases = Column(JSON, default=list)
    citing_cases_count = Column(Integer, default=0)
    authority_level = Column(SQLEnum(LegalAuthority))
    
    # Integration with Case
    added_to_case = Column(Boolean, default=False)
    case_relevance_notes = Column(Text)
    
    # Relationships
    search = relationship("LegalSearch", back_populates="results")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    # Create legal source record if accessed
    legal_source = relationship("LegalSource", uselist=False, back_populates="search_result")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_search_results_search_rank', 'search_id', 'result_rank'),
        Index('ix_search_results_citation', 'citation'),
        Index('ix_search_results_court_date', 'court_name', 'date_decided'),
        Index('ix_search_results_relevance', 'relevance', 'relevance_score'),
        UniqueConstraint('search_id', 'result_rank', name='uq_search_result_rank'),
    )
    
    def __repr__(self):
        return f"<LegalSearchResult(id={self.id}, title='{self.title[:50]}...', rank={self.result_rank})>"


class LegalSource(BaseModel):
    """Legal authorities and source materials"""
    
    __tablename__ = 'legal_sources'
    
    # Source Identification
    title = Column(String(1000), nullable=False, index=True)
    citation = Column(String(300), index=True)
    alternate_citations = Column(JSON, default=list)
    external_id = Column(String(200))  # ID in external database
    database_source = Column(SQLEnum(ResearchDatabase))
    
    # Source Classification
    source_type = Column(SQLEnum(LegalSourceType), nullable=False)
    authority_level = Column(SQLEnum(LegalAuthority), default=LegalAuthority.PERSUASIVE)
    
    # Publication Information
    court_name = Column(String(200))
    court_type = Column(SQLEnum(CourtType))
    judge_names = Column(JSON, default=list)
    date_decided = Column(Date)
    date_published = Column(Date)
    
    # Jurisdiction and Topic
    jurisdiction = Column(String(100))
    federal_circuit = Column(String(20))  # For federal cases
    state = Column(String(50))
    practice_areas = Column(JSON, default=list)
    legal_topics = Column(JSON, default=list)
    subject_matter = Column(JSON, default=list)
    
    # Document Content
    summary = Column(Text)
    headnotes = Column(JSON, default=list)
    key_holdings = Column(JSON, default=list)
    procedural_posture = Column(Text)
    disposition = Column(Text)
    
    # Legal Analysis
    legal_issues = Column(JSON, default=list)
    legal_principles = Column(JSON, default=list)
    statutes_cited = Column(JSON, default=list)
    cases_cited = Column(JSON, default=list)
    regulations_cited = Column(JSON, default=list)
    
    # Citation Analysis
    times_cited = Column(Integer, default=0)
    citing_cases = Column(JSON, default=list)
    citation_treatment = Column(JSON, default=list)  # History of how case has been treated
    
    # Research Context
    research_project_id = Column(Integer, ForeignKey('research_projects.id'), nullable=True)
    search_result_id = Column(Integer, ForeignKey('legal_search_results.id'), nullable=True)
    
    # Access and Storage
    full_text_path = Column(String(500))  # Path to stored document
    pdf_path = Column(String(500))
    database_url = Column(String(1000))
    
    # Cost and Usage
    acquisition_cost = Column(Numeric(8, 2))
    access_date = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Review and Annotation
    reviewed_by_id = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime(timezone=True))
    relevance = Column(SQLEnum(CitationRelevance))
    relevance_score = Column(Numeric(3, 2))  # 0.0 to 1.0
    
    # Notes and Analysis
    research_notes = Column(Text)
    key_quotes = Column(JSON, default=list)
    practitioner_notes = Column(Text)
    
    # Case Association
    cases_used_in = Column(JSON, default=list)  # Case IDs where this source was used
    
    # Quality Metrics
    shepard_signals = Column(String(20))  # Westlaw/Lexis treatment signals
    last_verification_date = Column(DateTime(timezone=True))
    verification_status = Column(String(50))  # good_law, questioned, overruled, etc.
    
    # Relationships
    research_project = relationship("ResearchProject", back_populates="sources")
    search_result = relationship("LegalSearchResult", back_populates="legal_source")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    citations = relationship("LegalCitation", back_populates="source", cascade="all, delete-orphan")
    annotations = relationship("LegalSourceAnnotation", back_populates="source", cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_legal_sources_citation', 'citation'),
        Index('ix_legal_sources_court_date', 'court_name', 'date_decided'),
        Index('ix_legal_sources_jurisdiction', 'jurisdiction', 'source_type'),
        Index('ix_legal_sources_relevance', 'relevance', 'relevance_score'),
        Index('ix_legal_sources_project', 'research_project_id'),
    )
    
    @property
    def is_binding_authority(self) -> bool:
        """Check if source is binding authority"""
        return self.authority_level == LegalAuthority.BINDING
    
    @property
    def age_in_years(self) -> Optional[int]:
        """Calculate age of decision in years"""
        if self.date_decided:
            return (date.today() - self.date_decided).days // 365
        return None
    
    def __repr__(self):
        return f"<LegalSource(id={self.id}, citation='{self.citation}', type='{self.source_type.value if self.source_type else 'unknown'}')>"


class LegalCitation(BaseModel):
    """Structured legal citations with validation"""
    
    __tablename__ = 'legal_citations'
    
    # Citation Details
    full_citation = Column(String(500), nullable=False, index=True)
    short_citation = Column(String(200))
    neutral_citation = Column(String(200))
    
    # Citation Components
    case_name = Column(String(300))
    volume = Column(String(20))
    reporter = Column(String(100))
    page = Column(String(20))
    court = Column(String(200))
    year = Column(Integer)
    
    # Source Reference
    source_id = Column(Integer, ForeignKey('legal_sources.id'), nullable=False, index=True)
    
    # Citation Context
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    page_number = Column(Integer)
    paragraph = Column(String(50))
    
    # Citation Purpose
    citation_purpose = Column(String(100))  # support, distinguish, overrule, follow
    relevance_to_issue = Column(String(200))
    
    # Validation
    is_valid = Column(Boolean, default=True)
    validation_notes = Column(Text)
    verified_by_id = Column(Integer, ForeignKey('users.id'))
    verified_at = Column(DateTime(timezone=True))
    
    # Authority and Treatment
    authority_weight = Column(Integer, default=5)  # 1-10 scale
    current_status = Column(String(50))  # good_law, questioned, overruled
    
    # Relationships
    source = relationship("LegalSource", back_populates="citations")
    document = relationship("Document", foreign_keys=[document_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_citations_source_document', 'source_id', 'document_id'),
        Index('ix_citations_case_year', 'case_name', 'year'),
        Index('ix_citations_reporter', 'reporter', 'volume', 'page'),
    )
    
    def __repr__(self):
        return f"<LegalCitation(id={self.id}, citation='{self.full_citation}')>"


class LegalSourceAnnotation(BaseModel):
    """Annotations and notes on legal sources"""
    
    __tablename__ = 'legal_source_annotations'
    
    # Annotation Details
    source_id = Column(Integer, ForeignKey('legal_sources.id'), nullable=False, index=True)
    annotation_type = Column(String(50), nullable=False)  # note, highlight, bookmark, key_holding
    
    # Content
    title = Column(String(200))
    content = Column(Text)
    highlighted_text = Column(Text)
    
    # Location
    page_number = Column(Integer)
    paragraph_number = Column(Integer)
    start_position = Column(Integer)
    end_position = Column(Integer)
    
    # Context
    legal_issue = Column(String(200))
    practice_area = Column(String(100))
    relevance_to_case = Column(Text)
    
    # User and Access
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_private = Column(Boolean, default=True)
    shared_with_team = Column(Boolean, default=False)
    
    # Case Association
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    # Relationships
    source = relationship("LegalSource", back_populates="annotations")
    created_by = relationship("User", foreign_keys=[created_by_id])
    case = relationship("Case", foreign_keys=[case_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_annotations_source_user', 'source_id', 'created_by_id'),
        Index('ix_annotations_case_type', 'case_id', 'annotation_type'),
    )
    
    def __repr__(self):
        return f"<LegalSourceAnnotation(id={self.id}, type='{self.annotation_type}', source_id={self.source_id})>"


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    'ResearchProject',
    'LegalSearch',
    'LegalSearchResult',
    'LegalSource',
    'LegalCitation',
    'LegalSourceAnnotation',
    'ResearchDatabase',
    'LegalSourceType',
    'CourtType',
    'ResearchStatus',
    'CitationRelevance',
    'LegalAuthority'
]