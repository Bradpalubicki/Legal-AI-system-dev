"""
Searchable transcript database with full-text search capabilities for legal transcripts.
"""
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid
import re
import json
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Integer, Boolean, JSON, Index, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy import text

from ..shared.database.models import Case, User, CourtSession
from ..shared.database.connection import get_db


Base = declarative_base()


class SearchScope(Enum):
    """Search scope options."""
    ALL_TRANSCRIPTS = "all_transcripts"
    CASE_SPECIFIC = "case_specific"
    DATE_RANGE = "date_range"
    SPEAKER_SPECIFIC = "speaker_specific"
    SESSION_SPECIFIC = "session_specific"


class SearchType(Enum):
    """Types of search queries."""
    FULL_TEXT = "full_text"
    PHRASE_EXACT = "phrase_exact"
    BOOLEAN = "boolean"
    PROXIMITY = "proximity"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    LEGAL_CITATION = "legal_citation"
    SPEAKER_CONTEXT = "speaker_context"


class TranscriptDocument(Base):
    """Main transcript document storage with full-text search."""
    __tablename__ = "transcript_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    case_id = Column(String, nullable=False, index=True)
    
    # Document metadata
    title = Column(String, nullable=False)
    document_type = Column(String, default="court_transcript")
    proceeding_type = Column(String)  # hearing, trial, deposition, etc.
    date_created = Column(DateTime, default=datetime.utcnow)
    date_proceeding = Column(DateTime)
    
    # Content
    full_text = Column(Text, nullable=False)
    enhanced_text = Column(Text)  # AI-enhanced version
    word_count = Column(Integer)
    page_count = Column(Integer)
    
    # Participants
    judge_name = Column(String)
    court_reporter = Column(String)
    participants = Column(JSON)  # List of all speakers/participants
    
    # Quality and processing
    confidence_score = Column(Float, default=0.0)
    processing_status = Column(String, default="pending")
    ai_analysis_complete = Column(Boolean, default=False)
    
    # Full-text search vector
    search_vector = Column(TSVECTOR)
    
    # Relationships
    segments = relationship("TranscriptSegmentDB", back_populates="document")
    annotations = relationship("TranscriptAnnotation", back_populates="document")
    search_results = relationship("SearchResult", back_populates="document")
    
    __table_args__ = (
        Index('idx_transcript_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_transcript_case_date', 'case_id', 'date_proceeding'),
        Index('idx_transcript_session', 'session_id'),
    )


class TranscriptSegmentDB(Base):
    """Individual transcript segments with speaker information."""
    __tablename__ = "transcript_segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('transcript_documents.id'), nullable=False)
    
    # Segment identification
    segment_number = Column(Integer, nullable=False)
    page_number = Column(Integer)
    line_number = Column(Integer)
    
    # Speaker information
    speaker = Column(String, nullable=False, index=True)
    speaker_role = Column(String)  # attorney, witness, judge, etc.
    speaker_party = Column(String)  # plaintiff, defendant, court, etc.
    
    # Content
    text = Column(Text, nullable=False)
    cleaned_text = Column(Text)
    word_count = Column(Integer)
    
    # Timing
    start_time = Column(Float)  # Seconds from start
    end_time = Column(Float)
    duration = Column(Float)
    
    # Audio quality
    confidence = Column(Float, default=0.0)
    audio_quality = Column(String)
    
    # Context
    preceding_context = Column(Text)  # Previous segments for context
    following_context = Column(Text)  # Following segments for context
    
    # Legal analysis
    contains_objection = Column(Boolean, default=False)
    contains_ruling = Column(Boolean, default=False)
    contains_evidence = Column(Boolean, default=False)
    legal_significance = Column(String)
    
    # Search vector
    search_vector = Column(TSVECTOR)
    
    # Relationships
    document = relationship("TranscriptDocument", back_populates="segments")
    annotations = relationship("SegmentAnnotation", back_populates="segment")
    
    __table_args__ = (
        Index('idx_segment_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_segment_speaker', 'speaker'),
        Index('idx_segment_time', 'start_time', 'end_time'),
        Index('idx_segment_legal', 'contains_objection', 'contains_ruling', 'contains_evidence'),
    )


class TranscriptAnnotation(Base):
    """Annotations and metadata for transcript documents."""
    __tablename__ = "transcript_annotations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('transcript_documents.id'), nullable=False)
    
    # Annotation details
    annotation_type = Column(String, nullable=False)  # legal_event, key_moment, etc.
    category = Column(String)
    subcategory = Column(String)
    
    # Content
    title = Column(String, nullable=False)
    description = Column(Text)
    content = Column(JSON)  # Flexible content storage
    
    # Location in transcript
    start_segment_id = Column(UUID(as_uuid=True))
    end_segment_id = Column(UUID(as_uuid=True))
    start_position = Column(Integer)  # Character position
    end_position = Column(Integer)
    
    # Metadata
    confidence = Column(Float, default=0.0)
    importance = Column(String, default="medium")
    tags = Column(JSON)  # List of tags
    
    # Creation info
    created_by = Column(String)  # user_id or "ai_system"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("TranscriptDocument", back_populates="annotations")
    
    __table_args__ = (
        Index('idx_annotation_type', 'annotation_type', 'category'),
        Index('idx_annotation_importance', 'importance'),
        Index('idx_annotation_created', 'created_at'),
    )


class SegmentAnnotation(Base):
    """Specific annotations for individual segments."""
    __tablename__ = "segment_annotations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey('transcript_segments.id'), nullable=False)
    
    annotation_type = Column(String, nullable=False)
    label = Column(String)
    value = Column(String)
    confidence = Column(Float, default=0.0)
    metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    
    # Relationships
    segment = relationship("TranscriptSegmentDB", back_populates="annotations")
    
    __table_args__ = (
        Index('idx_segment_annotation_type', 'annotation_type'),
    )


class SearchResult(Base):
    """Stored search results for caching and analytics."""
    __tablename__ = "search_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('transcript_documents.id'), nullable=False)
    
    # Search details
    query_text = Column(Text, nullable=False)
    search_type = Column(String, nullable=False)
    search_scope = Column(String)
    filters = Column(JSON)
    
    # Result details
    relevance_score = Column(Float)
    match_count = Column(Integer)
    matched_segments = Column(JSON)  # List of segment IDs
    highlighted_text = Column(Text)
    
    # Metadata
    search_timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String)
    session_info = Column(JSON)
    
    # Relationships
    document = relationship("TranscriptDocument", back_populates="search_results")
    
    __table_args__ = (
        Index('idx_search_query', 'query_text'),
        Index('idx_search_timestamp', 'search_timestamp'),
        Index('idx_search_user', 'user_id'),
    )


@dataclass
class SearchQuery:
    """Search query specification."""
    query_text: str
    search_type: SearchType = SearchType.FULL_TEXT
    search_scope: SearchScope = SearchScope.ALL_TRANSCRIPTS
    
    # Filters
    case_ids: List[str] = field(default_factory=list)
    session_ids: List[str] = field(default_factory=list)
    speakers: List[str] = field(default_factory=list)
    date_range: Optional[Tuple[datetime, datetime]] = None
    
    # Search options
    include_annotations: bool = True
    include_context: bool = True
    max_results: int = 100
    offset: int = 0
    
    # Advanced options
    fuzzy_threshold: float = 0.8
    proximity_distance: int = 10
    minimum_score: float = 0.1
    highlight_matches: bool = True


@dataclass
class SearchMatch:
    """Individual search match result."""
    segment_id: str
    document_id: str
    relevance_score: float
    matched_text: str
    highlighted_text: str
    context_before: str
    context_after: str
    speaker: str
    timestamp: Optional[float]
    page_number: Optional[int]
    line_number: Optional[int]
    annotations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SearchResults:
    """Complete search results."""
    query: SearchQuery
    total_matches: int
    execution_time: float
    matches: List[SearchMatch]
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    related_queries: List[str] = field(default_factory=list)


class TranscriptDatabase:
    """Searchable transcript database with full-text search capabilities."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        # Legal term patterns for enhanced search
        self.legal_patterns = {
            'objections': [
                'objection', 'sustained', 'overruled', 'sidebar', 'approach',
                'leading', 'hearsay', 'relevance', 'foundation', 'speculation'
            ],
            'evidence': [
                'exhibit', 'marked', 'admitted', 'excluded', 'foundation',
                'authentication', 'best evidence', 'original document'
            ],
            'procedure': [
                'motion', 'ruling', 'order', 'directed verdict', 'mistrial',
                'recess', 'adjourn', 'continuance', 'stipulation'
            ],
            'testimony': [
                'sworn', 'oath', 'perjury', 'cross-examine', 'redirect',
                'recross', 'impeach', 'refresh recollection'
            ]
        }

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    async def store_transcript(
        self, 
        session_id: str, 
        case_id: str, 
        transcript_content: str,
        segments: List[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a complete transcript with full-text indexing."""
        try:
            db = self.get_session()
            
            # Create document
            document = TranscriptDocument(
                session_id=session_id,
                case_id=case_id,
                title=metadata.get('title', f'Transcript {session_id}') if metadata else f'Transcript {session_id}',
                proceeding_type=metadata.get('proceeding_type', 'hearing') if metadata else 'hearing',
                date_proceeding=metadata.get('date_proceeding', datetime.utcnow()) if metadata else datetime.utcnow(),
                full_text=transcript_content,
                word_count=len(transcript_content.split()),
                judge_name=metadata.get('judge_name') if metadata else None,
                court_reporter=metadata.get('court_reporter') if metadata else None,
                participants=metadata.get('participants', []) if metadata else []
            )
            
            db.add(document)
            db.flush()  # Get document ID
            
            # Store segments if provided
            if segments:
                for i, segment_data in enumerate(segments):
                    segment = TranscriptSegmentDB(
                        document_id=document.id,
                        segment_number=i + 1,
                        speaker=segment_data.get('speaker', 'Unknown'),
                        speaker_role=segment_data.get('speaker_role'),
                        speaker_party=segment_data.get('speaker_party'),
                        text=segment_data.get('text', ''),
                        word_count=len(segment_data.get('text', '').split()),
                        start_time=segment_data.get('start_time'),
                        end_time=segment_data.get('end_time'),
                        duration=segment_data.get('duration'),
                        confidence=segment_data.get('confidence', 0.0),
                        page_number=segment_data.get('page_number'),
                        line_number=segment_data.get('line_number')
                    )
                    
                    db.add(segment)
            
            # Update search vectors
            await self._update_search_vectors(db, document.id)
            
            db.commit()
            return str(document.id)
            
        except Exception as e:
            db.rollback()
            print(f"Error storing transcript: {e}")
            raise
        finally:
            db.close()

    async def _update_search_vectors(self, db: Session, document_id: str):
        """Update full-text search vectors for document and segments."""
        try:
            # Update document search vector
            db.execute(text("""
                UPDATE transcript_documents 
                SET search_vector = to_tsvector('english', 
                    coalesce(title, '') || ' ' || 
                    coalesce(full_text, '') || ' ' ||
                    coalesce(judge_name, '') || ' ' ||
                    coalesce(proceeding_type, '')
                )
                WHERE id = :document_id
            """), {"document_id": document_id})
            
            # Update segment search vectors
            db.execute(text("""
                UPDATE transcript_segments 
                SET search_vector = to_tsvector('english',
                    coalesce(speaker, '') || ' ' ||
                    coalesce(text, '') || ' ' ||
                    coalesce(speaker_role, '') || ' ' ||
                    coalesce(legal_significance, '')
                )
                WHERE document_id = :document_id
            """), {"document_id": document_id})
            
        except Exception as e:
            print(f"Error updating search vectors: {e}")
            raise

    async def search_transcripts(self, query: SearchQuery) -> SearchResults:
        """Perform full-text search across transcripts."""
        try:
            start_time = datetime.now()
            db = self.get_session()
            
            # Build base query based on search type
            base_query = self._build_search_query(db, query)
            
            # Apply filters
            filtered_query = self._apply_filters(base_query, query)
            
            # Execute search
            results = filtered_query.offset(query.offset).limit(query.max_results).all()
            
            # Get total count
            total_count = filtered_query.count()
            
            # Process results
            matches = []
            for result in results:
                match = await self._process_search_result(db, result, query)
                if match and match.relevance_score >= query.minimum_score:
                    matches.append(match)
            
            # Calculate facets
            facets = await self._calculate_facets(db, query, filtered_query)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(db, query)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return SearchResults(
                query=query,
                total_matches=total_count,
                execution_time=execution_time,
                matches=matches,
                facets=facets,
                suggestions=suggestions
            )
            
        except Exception as e:
            print(f"Error in search: {e}")
            return SearchResults(
                query=query,
                total_matches=0,
                execution_time=0.0,
                matches=[]
            )
        finally:
            db.close()

    def _build_search_query(self, db: Session, query: SearchQuery):
        """Build the appropriate search query based on search type."""
        if query.search_type == SearchType.FULL_TEXT:
            return self._build_full_text_query(db, query)
        elif query.search_type == SearchType.PHRASE_EXACT:
            return self._build_phrase_query(db, query)
        elif query.search_type == SearchType.BOOLEAN:
            return self._build_boolean_query(db, query)
        elif query.search_type == SearchType.PROXIMITY:
            return self._build_proximity_query(db, query)
        elif query.search_type == SearchType.FUZZY:
            return self._build_fuzzy_query(db, query)
        elif query.search_type == SearchType.SPEAKER_CONTEXT:
            return self._build_speaker_context_query(db, query)
        else:
            return self._build_full_text_query(db, query)  # Default

    def _build_full_text_query(self, db: Session, query: SearchQuery):
        """Build full-text search query."""
        # Clean and prepare search terms
        search_terms = self._prepare_search_terms(query.query_text)
        
        return db.query(
            TranscriptSegmentDB,
            func.ts_rank(TranscriptSegmentDB.search_vector, func.plainto_tsquery('english', search_terms)).label('rank')
        ).filter(
            TranscriptSegmentDB.search_vector.op('@@')(func.plainto_tsquery('english', search_terms))
        ).order_by(text('rank DESC'))

    def _build_phrase_query(self, db: Session, query: SearchQuery):
        """Build exact phrase search query."""
        phrase = f'"{query.query_text}"'
        
        return db.query(
            TranscriptSegmentDB,
            func.ts_rank(TranscriptSegmentDB.search_vector, func.phraseto_tsquery('english', query.query_text)).label('rank')
        ).filter(
            TranscriptSegmentDB.search_vector.op('@@')(func.phraseto_tsquery('english', query.query_text))
        ).order_by(text('rank DESC'))

    def _build_boolean_query(self, db: Session, query: SearchQuery):
        """Build boolean search query (AND, OR, NOT)."""
        # Convert natural language to tsquery format
        boolean_query = self._convert_to_tsquery(query.query_text)
        
        return db.query(
            TranscriptSegmentDB,
            func.ts_rank(TranscriptSegmentDB.search_vector, func.to_tsquery('english', boolean_query)).label('rank')
        ).filter(
            TranscriptSegmentDB.search_vector.op('@@')(func.to_tsquery('english', boolean_query))
        ).order_by(text('rank DESC'))

    def _build_proximity_query(self, db: Session, query: SearchQuery):
        """Build proximity search query."""
        terms = query.query_text.split()
        if len(terms) < 2:
            return self._build_full_text_query(db, query)
        
        # Build proximity query (terms within N words of each other)
        proximity_query = f"{terms[0]} <{query.proximity_distance}> {terms[1]}"
        for term in terms[2:]:
            proximity_query = f"({proximity_query}) <{query.proximity_distance}> {term}"
        
        return db.query(
            TranscriptSegmentDB,
            func.ts_rank(TranscriptSegmentDB.search_vector, func.to_tsquery('english', proximity_query)).label('rank')
        ).filter(
            TranscriptSegmentDB.search_vector.op('@@')(func.to_tsquery('english', proximity_query))
        ).order_by(text('rank DESC'))

    def _build_fuzzy_query(self, db: Session, query: SearchQuery):
        """Build fuzzy search query using similarity."""
        return db.query(
            TranscriptSegmentDB,
            func.similarity(TranscriptSegmentDB.text, query.query_text).label('similarity')
        ).filter(
            func.similarity(TranscriptSegmentDB.text, query.query_text) > query.fuzzy_threshold
        ).order_by(text('similarity DESC'))

    def _build_speaker_context_query(self, db: Session, query: SearchQuery):
        """Build speaker-specific context search."""
        base_query = self._build_full_text_query(db, query)
        
        if query.speakers:
            base_query = base_query.filter(
                TranscriptSegmentDB.speaker.in_(query.speakers)
            )
        
        return base_query

    def _apply_filters(self, base_query, query: SearchQuery):
        """Apply filters to the search query."""
        filtered_query = base_query
        
        # Case filter
        if query.case_ids:
            filtered_query = filtered_query.join(TranscriptDocument).filter(
                TranscriptDocument.case_id.in_(query.case_ids)
            )
        
        # Session filter
        if query.session_ids:
            if not hasattr(filtered_query.column_descriptions[0]['type'], 'session_id'):
                filtered_query = filtered_query.join(TranscriptDocument)
            filtered_query = filtered_query.filter(
                TranscriptDocument.session_id.in_(query.session_ids)
            )
        
        # Speaker filter
        if query.speakers:
            filtered_query = filtered_query.filter(
                TranscriptSegmentDB.speaker.in_(query.speakers)
            )
        
        # Date range filter
        if query.date_range:
            start_date, end_date = query.date_range
            if not hasattr(filtered_query.column_descriptions[0]['type'], 'date_proceeding'):
                filtered_query = filtered_query.join(TranscriptDocument)
            filtered_query = filtered_query.filter(
                TranscriptDocument.date_proceeding.between(start_date, end_date)
            )
        
        return filtered_query

    async def _process_search_result(
        self, 
        db: Session, 
        result, 
        query: SearchQuery
    ) -> Optional[SearchMatch]:
        """Process individual search result."""
        try:
            if hasattr(result, 'TranscriptSegmentDB'):
                segment = result.TranscriptSegmentDB
                score = getattr(result, 'rank', 0.0) or getattr(result, 'similarity', 0.0)
            else:
                segment = result[0] if isinstance(result, tuple) else result
                score = result[1] if isinstance(result, tuple) and len(result) > 1 else 0.0
            
            # Get document info
            document = db.query(TranscriptDocument).filter(
                TranscriptDocument.id == segment.document_id
            ).first()
            
            if not document:
                return None
            
            # Generate highlighted text
            highlighted_text = self._highlight_matches(segment.text, query.query_text) if query.highlight_matches else segment.text
            
            # Get context
            context_before, context_after = "", ""
            if query.include_context:
                context_before, context_after = await self._get_segment_context(db, segment)
            
            # Get annotations
            annotations = []
            if query.include_annotations:
                annotations = await self._get_segment_annotations(db, segment.id)
            
            return SearchMatch(
                segment_id=str(segment.id),
                document_id=str(document.id),
                relevance_score=float(score),
                matched_text=segment.text,
                highlighted_text=highlighted_text,
                context_before=context_before,
                context_after=context_after,
                speaker=segment.speaker,
                timestamp=segment.start_time,
                page_number=segment.page_number,
                line_number=segment.line_number,
                annotations=annotations
            )
            
        except Exception as e:
            print(f"Error processing search result: {e}")
            return None

    def _highlight_matches(self, text: str, query: str) -> str:
        """Highlight search terms in text."""
        try:
            terms = self._prepare_search_terms(query).split()
            highlighted = text
            
            for term in terms:
                # Case-insensitive highlighting
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted = pattern.sub(f'<mark>\\g<0></mark>', highlighted)
            
            return highlighted
            
        except Exception as e:
            print(f"Error highlighting matches: {e}")
            return text

    async def _get_segment_context(
        self, 
        db: Session, 
        segment: TranscriptSegmentDB, 
        context_size: int = 2
    ) -> Tuple[str, str]:
        """Get surrounding context for a segment."""
        try:
            # Get preceding segments
            preceding = db.query(TranscriptSegmentDB).filter(
                TranscriptSegmentDB.document_id == segment.document_id,
                TranscriptSegmentDB.segment_number < segment.segment_number
            ).order_by(TranscriptSegmentDB.segment_number.desc()).limit(context_size).all()
            
            # Get following segments
            following = db.query(TranscriptSegmentDB).filter(
                TranscriptSegmentDB.document_id == segment.document_id,
                TranscriptSegmentDB.segment_number > segment.segment_number
            ).order_by(TranscriptSegmentDB.segment_number.asc()).limit(context_size).all()
            
            context_before = " ".join([f"{s.speaker}: {s.text}" for s in reversed(preceding)])
            context_after = " ".join([f"{s.speaker}: {s.text}" for s in following])
            
            return context_before, context_after
            
        except Exception as e:
            print(f"Error getting segment context: {e}")
            return "", ""

    async def _get_segment_annotations(self, db: Session, segment_id: str) -> List[Dict[str, Any]]:
        """Get annotations for a segment."""
        try:
            annotations = db.query(SegmentAnnotation).filter(
                SegmentAnnotation.segment_id == segment_id
            ).all()
            
            return [
                {
                    "type": ann.annotation_type,
                    "label": ann.label,
                    "value": ann.value,
                    "confidence": ann.confidence,
                    "metadata": ann.metadata
                }
                for ann in annotations
            ]
            
        except Exception as e:
            print(f"Error getting segment annotations: {e}")
            return []

    async def _calculate_facets(
        self, 
        db: Session, 
        query: SearchQuery, 
        filtered_query
    ) -> Dict[str, Dict[str, int]]:
        """Calculate search facets for filtering."""
        try:
            facets = {}
            
            # Speaker facets
            speaker_facets = db.query(
                TranscriptSegmentDB.speaker,
                func.count(TranscriptSegmentDB.id).label('count')
            ).filter(
                TranscriptSegmentDB.id.in_(filtered_query.subquery().select())
            ).group_by(TranscriptSegmentDB.speaker).all()
            
            facets['speakers'] = {speaker: count for speaker, count in speaker_facets}
            
            # Case facets
            case_facets = db.query(
                TranscriptDocument.case_id,
                func.count(TranscriptSegmentDB.id).label('count')
            ).join(TranscriptSegmentDB).filter(
                TranscriptSegmentDB.id.in_(filtered_query.subquery().select())
            ).group_by(TranscriptDocument.case_id).all()
            
            facets['cases'] = {case_id: count for case_id, count in case_facets}
            
            # Legal significance facets
            legal_facets = db.query(
                TranscriptSegmentDB.legal_significance,
                func.count(TranscriptSegmentDB.id).label('count')
            ).filter(
                TranscriptSegmentDB.id.in_(filtered_query.subquery().select()),
                TranscriptSegmentDB.legal_significance.isnot(None)
            ).group_by(TranscriptSegmentDB.legal_significance).all()
            
            facets['legal_significance'] = {sig: count for sig, count in legal_facets if sig}
            
            return facets
            
        except Exception as e:
            print(f"Error calculating facets: {e}")
            return {}

    async def _generate_suggestions(self, db: Session, query: SearchQuery) -> List[str]:
        """Generate search suggestions and corrections."""
        try:
            suggestions = []
            
            # Find similar queries from search history
            similar_queries = db.query(SearchResult.query_text).filter(
                func.similarity(SearchResult.query_text, query.query_text) > 0.6
            ).distinct().limit(5).all()
            
            suggestions.extend([q[0] for q in similar_queries if q[0] != query.query_text])
            
            # Add legal term suggestions
            query_terms = query.query_text.lower().split()
            for category, terms in self.legal_patterns.items():
                for term in terms:
                    if any(qt in term or term in qt for qt in query_terms):
                        suggestions.append(f"{query.query_text} {term}")
            
            return suggestions[:5]
            
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []

    def _prepare_search_terms(self, query_text: str) -> str:
        """Prepare and clean search terms."""
        # Remove special characters that might interfere with search
        cleaned = re.sub(r'[^\w\s\-\.]', ' ', query_text)
        
        # Handle legal abbreviations and expand them
        legal_expansions = {
            'def': 'defendant',
            'pl': 'plaintiff',
            'att': 'attorney',
            'obj': 'objection',
            'sust': 'sustained',
            'overr': 'overruled',
            'ct': 'court'
        }
        
        terms = cleaned.lower().split()
        expanded_terms = []
        
        for term in terms:
            if term in legal_expansions:
                expanded_terms.append(legal_expansions[term])
            else:
                expanded_terms.append(term)
        
        return ' '.join(expanded_terms)

    def _convert_to_tsquery(self, query_text: str) -> str:
        """Convert natural language boolean query to PostgreSQL tsquery format."""
        # Simple conversion - would need more sophisticated parsing for full boolean logic
        query = query_text.replace(' AND ', ' & ')
        query = query.replace(' OR ', ' | ')
        query = query.replace(' NOT ', ' ! ')
        
        # Handle parentheses and quotes
        return query

    async def add_annotation(
        self, 
        document_id: str, 
        annotation_type: str,
        title: str,
        description: str,
        start_segment_id: Optional[str] = None,
        end_segment_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> str:
        """Add annotation to a transcript."""
        try:
            db = self.get_session()
            
            annotation = TranscriptAnnotation(
                document_id=document_id,
                annotation_type=annotation_type,
                title=title,
                description=description,
                start_segment_id=start_segment_id,
                end_segment_id=end_segment_id,
                content=metadata or {},
                created_by=created_by
            )
            
            db.add(annotation)
            db.commit()
            
            return str(annotation.id)
            
        except Exception as e:
            db.rollback()
            print(f"Error adding annotation: {e}")
            raise
        finally:
            db.close()

    async def get_document_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript document by session ID."""
        try:
            db = self.get_session()
            
            document = db.query(TranscriptDocument).filter(
                TranscriptDocument.session_id == session_id
            ).first()
            
            if not document:
                return None
            
            return {
                "id": str(document.id),
                "session_id": document.session_id,
                "case_id": document.case_id,
                "title": document.title,
                "proceeding_type": document.proceeding_type,
                "date_created": document.date_created.isoformat(),
                "date_proceeding": document.date_proceeding.isoformat() if document.date_proceeding else None,
                "word_count": document.word_count,
                "confidence_score": document.confidence_score,
                "judge_name": document.judge_name,
                "participants": document.participants
            }
            
        except Exception as e:
            print(f"Error getting document by session: {e}")
            return None
        finally:
            db.close()

    async def get_transcript_statistics(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Get transcript database statistics."""
        try:
            db = self.get_session()
            
            # Base query
            base_query = db.query(TranscriptDocument)
            if case_id:
                base_query = base_query.filter(TranscriptDocument.case_id == case_id)
            
            # Count statistics
            total_documents = base_query.count()
            total_word_count = base_query.with_entities(func.sum(TranscriptDocument.word_count)).scalar() or 0
            
            # Segment statistics
            segment_base = db.query(TranscriptSegmentDB).join(TranscriptDocument)
            if case_id:
                segment_base = segment_base.filter(TranscriptDocument.case_id == case_id)
            
            total_segments = segment_base.count()
            
            # Speaker statistics
            speaker_stats = segment_base.with_entities(
                TranscriptSegmentDB.speaker,
                func.count(TranscriptSegmentDB.id).label('segment_count'),
                func.sum(TranscriptSegmentDB.word_count).label('word_count')
            ).group_by(TranscriptSegmentDB.speaker).all()
            
            # Recent activity
            recent_docs = base_query.filter(
                TranscriptDocument.date_created >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            return {
                "total_documents": total_documents,
                "total_word_count": total_word_count,
                "total_segments": total_segments,
                "recent_documents": recent_docs,
                "speaker_statistics": [
                    {
                        "speaker": speaker,
                        "segment_count": segment_count,
                        "word_count": word_count
                    }
                    for speaker, segment_count, word_count in speaker_stats
                ],
                "average_words_per_document": total_word_count / total_documents if total_documents > 0 else 0
            }
            
        except Exception as e:
            print(f"Error getting transcript statistics: {e}")
            return {}
        finally:
            db.close()

    async def export_search_results(self, results: SearchResults, format: str = "json") -> str:
        """Export search results in specified format."""
        try:
            if format.lower() == "json":
                return json.dumps({
                    "query": {
                        "text": results.query.query_text,
                        "type": results.query.search_type.value,
                        "scope": results.query.search_scope.value
                    },
                    "total_matches": results.total_matches,
                    "execution_time": results.execution_time,
                    "matches": [
                        {
                            "segment_id": match.segment_id,
                            "relevance_score": match.relevance_score,
                            "speaker": match.speaker,
                            "text": match.matched_text,
                            "timestamp": match.timestamp,
                            "page_number": match.page_number,
                            "annotations": match.annotations
                        }
                        for match in results.matches
                    ],
                    "facets": results.facets
                }, indent=2)
            
            elif format.lower() == "csv":
                # CSV format implementation
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Header
                writer.writerow([
                    'Segment ID', 'Speaker', 'Text', 'Relevance Score', 
                    'Timestamp', 'Page', 'Line'
                ])
                
                # Data
                for match in results.matches:
                    writer.writerow([
                        match.segment_id,
                        match.speaker,
                        match.matched_text,
                        match.relevance_score,
                        match.timestamp,
                        match.page_number,
                        match.line_number
                    ])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            print(f"Error exporting search results: {e}")
            return ""