"""
Learning System Database Models

Tracks AI performance, user feedback, and builds knowledge base for continuous improvement.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from ..src.core.database import Base


class AIFeedback(Base):
    """
    User feedback on AI-generated responses.
    Used to improve model performance over time.
    """
    __tablename__ = "ai_feedback"

    id = Column(Integer, primary_key=True, index=True)

    # Reference to original request
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    session_id = Column(String(255), index=True)
    request_type = Column(String(100), index=True)  # analysis, classification, extraction, etc.

    # AI Response details
    model_used = Column(String(100))  # claude-3-5-sonnet, gpt-4, etc.
    prompt_version = Column(String(50))  # Track prompt versions
    response_text = Column(Text)
    confidence_score = Column(Float)  # AI's confidence in its response

    # User Feedback
    user_rating = Column(Integer)  # 1-5 star rating
    was_helpful = Column(Boolean, default=True)
    was_accurate = Column(Boolean, default=True)
    feedback_text = Column(Text, nullable=True)

    # Corrections provided by user
    corrected_response = Column(Text, nullable=True)  # User's correction if response was wrong
    correction_type = Column(String(100), nullable=True)  # classification, entity, reasoning, etc.

    # Metadata
    processing_time_ms = Column(Integer)
    token_count = Column(Integer)
    cost_usd = Column(Float)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="feedback_items")

    # Indexes for performance
    __table_args__ = (
        Index('idx_feedback_rating', 'user_rating'),
        Index('idx_feedback_type_model', 'request_type', 'model_used'),
        Index('idx_feedback_created', 'created_at'),
    )


class DocumentKnowledge(Base):
    """
    Knowledge base built from processed documents.
    Stores patterns, insights, and successful analyses for RAG.
    """
    __tablename__ = "document_knowledge"

    id = Column(Integer, primary_key=True, index=True)

    # Document reference
    source_document_id = Column(String(36), ForeignKey("documents.id"))
    document_type = Column(String(100), index=True)  # contract, brief, motion, etc.

    # Knowledge content
    knowledge_type = Column(String(100), index=True)  # pattern, precedent, clause, citation, etc.
    title = Column(String(500))  # Brief description
    content = Column(Text)  # Full knowledge content
    embedding = Column(JSON, nullable=True)  # Vector embedding for similarity search

    # Context and metadata
    jurisdiction = Column(String(100), nullable=True, index=True)
    practice_area = Column(String(100), nullable=True, index=True)
    tags = Column(JSON)  # Searchable tags

    # Quality metrics
    usage_count = Column(Integer, default=0)  # How many times this knowledge was used
    success_rate = Column(Float, default=1.0)  # How often it led to good results
    avg_user_rating = Column(Float, default=5.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="knowledge_items")

    # Indexes
    __table_args__ = (
        Index('idx_knowledge_type', 'knowledge_type', 'document_type'),
        Index('idx_knowledge_jurisdiction', 'jurisdiction'),
        Index('idx_knowledge_quality', 'success_rate', 'usage_count'),
    )


class PerformanceMetric(Base):
    """
    Track AI model performance metrics over time.
    Enables monitoring of improvement trends.
    """
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Metric identification
    metric_type = Column(String(100), index=True)  # accuracy, precision, recall, f1, etc.
    task_type = Column(String(100), index=True)  # classification, extraction, analysis, etc.
    model_name = Column(String(100), index=True)

    # Performance values
    value = Column(Float)  # The metric value
    sample_size = Column(Integer)  # Number of samples this metric is based on

    # Breakdown by category
    category = Column(String(100), nullable=True)  # e.g., contract_type, document_category
    subcategory = Column(String(100), nullable=True)

    # Time period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    measured_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Additional context
    metadata_info = Column(JSON)  # Flexible storage for additional info

    # Indexes
    __table_args__ = (
        Index('idx_metrics_type_task', 'metric_type', 'task_type'),
        Index('idx_metrics_model_time', 'model_name', 'measured_at'),
    )


class LearningTask(Base):
    """
    Tracks learning/improvement tasks and their status.
    Used for fine-tuning, prompt optimization, and model updates.
    """
    __tablename__ = "learning_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # Task details
    task_type = Column(String(100), index=True)  # fine_tune, prompt_optimization, knowledge_update
    status = Column(String(50), index=True, default="pending")  # pending, running, completed, failed

    # Configuration
    config = Column(JSON)  # Task-specific configuration

    # Input/Output
    input_data_path = Column(String(500), nullable=True)  # Path to training data
    output_model_path = Column(String(500), nullable=True)  # Path to improved model

    # Results
    improvement_percentage = Column(Float, nullable=True)
    baseline_score = Column(Float, nullable=True)
    new_score = Column(Float, nullable=True)

    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))  # User or system that initiated

    # Indexes
    __table_args__ = (
        Index('idx_learning_status', 'status', 'task_type'),
        Index('idx_learning_created', 'created_at'),
    )


class DocumentSimilarity(Base):
    """
    Pre-computed document similarities for fast retrieval.
    Enables finding similar documents for context and precedent.
    """
    __tablename__ = "document_similarities"

    id = Column(Integer, primary_key=True, index=True)

    # Document pair
    document_a_id = Column(String(36), ForeignKey("documents.id"), index=True)
    document_b_id = Column(String(36), ForeignKey("documents.id"), index=True)

    # Similarity metrics
    similarity_score = Column(Float, index=True)  # 0.0 to 1.0
    similarity_type = Column(String(50))  # semantic, structural, citation_based, etc.

    # Why they're similar
    common_features = Column(JSON)  # List of shared features

    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document_a = relationship("Document", foreign_keys=[document_a_id])
    document_b = relationship("Document", foreign_keys=[document_b_id])

    # Indexes
    __table_args__ = (
        Index('idx_similarity_score', 'similarity_score'),
        Index('idx_similarity_docs', 'document_a_id', 'document_b_id'),
    )


class UserPreference(Base):
    """
    Learn user and firm-specific preferences over time.
    Personalizes AI responses based on past interactions.
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)

    # User/Firm identification
    user_id = Column(String(255), nullable=True, index=True)
    firm_id = Column(String(255), nullable=True, index=True)

    # Preference details
    preference_type = Column(String(100), index=True)  # citation_style, analysis_depth, etc.
    preference_key = Column(String(255))
    preference_value = Column(JSON)  # Flexible value storage

    # Learning metadata
    confidence = Column(Float, default=0.5)  # How confident we are in this preference
    evidence_count = Column(Integer, default=1)  # How many examples support this

    # Timestamps
    first_observed = Column(DateTime(timezone=True), server_default=func.now())
    last_observed = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_prefs_user', 'user_id', 'preference_type'),
        Index('idx_prefs_firm', 'firm_id', 'preference_type'),
    )
