"""
Legal AI System - Document and Session Models
Data persistence for documents, Q&A sessions, and defense strategies
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..src.core.database import Base


class Document(Base):
    """Uploaded legal documents"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), index=True, nullable=True)  # Owner user ID - Required for new docs, may be null for legacy data
    session_id = Column(String(36), index=True)  # Session identifier (for grouping)

    # File metadata
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Document content
    text_content = Column(Text, nullable=False)  # Extracted text

    # AI Analysis results
    summary = Column(Text)
    document_type = Column(String(200))
    parties = Column(JSON)  # Array of strings
    important_dates = Column(JSON)  # Array of {date, description}
    key_figures = Column(JSON)  # Array of {label, value}
    keywords = Column(JSON)  # Array of strings
    analysis_data = Column(JSON)  # Full analysis response

    # Enhanced operational details extraction
    operational_details = Column(JSON)  # Action items, obligations, contacts, jurisdiction, etc.

    # Enhanced financial details extraction
    financial_details = Column(JSON)  # Detailed financial transactions, insurance, claims, precedents

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    qa_sessions = relationship("QASession", back_populates="document", cascade="all, delete-orphan")
    defense_sessions = relationship("DefenseSession", back_populates="document", cascade="all, delete-orphan")
    feedback_items = relationship("AIFeedback", back_populates="document", cascade="all, delete-orphan")
    knowledge_items = relationship("DocumentKnowledge", back_populates="document", cascade="all, delete-orphan")


class QASession(Base):
    """Q&A conversation sessions"""
    __tablename__ = "qa_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), index=True, nullable=True)  # Owner user ID - Required for new sessions, may be null for legacy data
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)  # Allow NULL for general education sessions
    session_id = Column(String(36), nullable=False, index=True)  # Frontend session ID

    # Session metadata
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Conversation state
    question_count = Column(Integer, default=0)
    case_type = Column(String(100))  # Case type for interview flow
    last_question = Column(Text)  # Last question asked to user
    using_document_aware = Column(Boolean, default=False)  # Using document-aware interviewer

    # Cached data for performance
    document_text = Column(Text)  # Cached document text excerpt
    document_analysis = Column(JSON)  # Cached document analysis
    collected_info = Column(JSON, default=dict)  # Interview answers collected

    # Relationships
    document = relationship("Document", back_populates="qa_sessions")
    messages = relationship("QAMessage", back_populates="session", cascade="all, delete-orphan", order_by="QAMessage.timestamp")


class QAMessage(Base):
    """Individual Q&A messages"""
    __tablename__ = "qa_messages"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("qa_sessions.id"), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)  # 'ai' or 'user'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # AI-specific fields
    follow_up_question = Column(Text)  # AI's follow-up question
    confidence = Column(JSON)  # Confidence scores
    sources = Column(JSON)  # Source references

    # Relationships
    session = relationship("QASession", back_populates="messages")


class DefenseSession(Base):
    """Defense strategy interview sessions"""
    __tablename__ = "defense_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), index=True, nullable=True)  # Owner user ID - Required for new sessions, may be null for legacy data
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)  # Optional: can work without documents
    session_id = Column(String(36), nullable=False, index=True)  # Frontend session ID

    # Session metadata
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Conversation state
    phase = Column(String(50), default='intro')  # intro, questions, analysis, complete
    collected_answers = Column(JSON, default=dict)  # Dict of interview responses (answers dict from ChatContext)
    is_interview_active = Column(Boolean, default=True)  # Whether interview is ongoing
    current_question_key = Column(String(200))  # Current question being asked
    message_count = Column(Integer, default=0)  # Number of messages exchanged

    # Analysis results
    case_type = Column(String(100))
    situation_summary = Column(Text)
    defenses = Column(JSON)  # Array of defense strategies
    actions = Column(JSON)  # Array of recommended actions
    evidence_needed = Column(JSON)  # Array of evidence items
    analysis_data = Column(JSON)  # Full defense analysis

    # Relationships
    document = relationship("Document", back_populates="defense_sessions")
    messages = relationship("DefenseMessage", back_populates="session", cascade="all, delete-orphan", order_by="DefenseMessage.timestamp")


class DefenseMessage(Base):
    """Defense strategy conversation messages"""
    __tablename__ = "defense_messages"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("defense_sessions.id"), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)  # 'ai' or 'user'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("DefenseSession", back_populates="messages")


class BatchJob(Base):
    """Batch document processing jobs"""
    __tablename__ = "batch_jobs"

    id = Column(String(36), primary_key=True)  # UUID (job_id)
    user_id = Column(String(36), index=True, nullable=True)  # Owner user ID - Required for new jobs, may be null for legacy data
    session_id = Column(String(36), nullable=False, index=True)

    # Job status
    status = Column(String(20), default='pending')  # pending, processing, completed, failed, cancelled

    # Counts
    total_documents = Column(Integer, default=0)
    processed_documents = Column(Integer, default=0)
    successful_documents = Column(Integer, default=0)
    failed_documents = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Error tracking and results
    errors = Column(JSON, default=list)  # Array of error objects
    documents = Column(JSON, default=list)  # Array of processed document results

    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CaseTracking(Base):
    """Case tracking for obligations and attorney accountability"""
    __tablename__ = "case_tracking"

    case_id = Column(String(100), primary_key=True)  # Case identifier

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Tracking data (stored as JSON for flexibility)
    documents_processed = Column(JSON, default=list)  # Array of document processing records
    obligations = Column(JSON, default=list)  # Array of obligation objects
    actions_taken = Column(JSON, default=list)  # Array of attorney action records
    missed_deadlines = Column(JSON, default=list)  # Array of missed deadlines
    performance_metrics = Column(JSON, default=dict)  # Performance calculation results
