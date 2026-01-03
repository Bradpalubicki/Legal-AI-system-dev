"""
AI Integration Models for Legal AI System

Models for AI service integration, model management, analysis results,
and machine learning workflows specific to legal use cases.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, BigInteger,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Numeric, Table, Float
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import BaseModel, NamedModel, StatusModel, StatusEnum, PriorityEnum


# =============================================================================
# ENUMS
# =============================================================================

class AIProvider(enum.Enum):
    """AI service providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    AWS_BEDROCK = "aws_bedrock"
    HUGGINGFACE = "huggingface"
    LOCAL_MODEL = "local_model"
    CUSTOM = "custom"


class ModelType(enum.Enum):
    """Types of AI models"""
    LANGUAGE_MODEL = "language_model"
    CHAT_MODEL = "chat_model"
    EMBEDDING_MODEL = "embedding_model"
    CLASSIFICATION_MODEL = "classification_model"
    NAMED_ENTITY_RECOGNITION = "named_entity_recognition"
    SUMMARIZATION_MODEL = "summarization_model"
    TRANSLATION_MODEL = "translation_model"
    LEGAL_REASONING = "legal_reasoning"
    CONTRACT_ANALYSIS = "contract_analysis"
    CITATION_EXTRACTION = "citation_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    DOCUMENT_CLASSIFICATION = "document_classification"


class AnalysisType(enum.Enum):
    """Types of AI analysis"""
    DOCUMENT_SUMMARY = "document_summary"
    LEGAL_ANALYSIS = "legal_analysis"
    CONTRACT_REVIEW = "contract_review"
    RISK_ASSESSMENT = "risk_assessment"
    CITATION_EXTRACTION = "citation_extraction"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TOPIC_MODELING = "topic_modeling"
    SIMILARITY_ANALYSIS = "similarity_analysis"
    LEGAL_RESEARCH = "legal_research"
    COMPLIANCE_CHECK = "compliance_check"
    PRIVILEGE_REVIEW = "privilege_review"
    CASE_PREDICTION = "case_prediction"
    DOCUMENT_CLASSIFICATION = "document_classification"


class JobStatus(enum.Enum):
    """Status of AI processing jobs"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class ConfidenceLevel(enum.Enum):
    """Confidence levels for AI predictions"""
    VERY_LOW = "very_low"      # < 0.3
    LOW = "low"                # 0.3 - 0.5
    MEDIUM = "medium"          # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.9
    VERY_HIGH = "very_high"    # > 0.9


class ModelStatus(enum.Enum):
    """Status of AI models"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"
    MAINTENANCE = "maintenance"
    ERROR = "error"


# =============================================================================
# CORE AI MODELS
# =============================================================================

class AIModel(BaseModel):
    """AI model configuration and metadata"""
    
    __tablename__ = 'ai_models'
    
    # Model Identification
    name = Column(String(200), nullable=False, index=True)
    display_name = Column(String(200))
    description = Column(Text)
    version = Column(String(50), nullable=False)
    
    # Provider Information
    provider = Column(SQLEnum(AIProvider), nullable=False)
    model_type = Column(SQLEnum(ModelType), nullable=False)
    model_id = Column(String(200), nullable=False)  # Provider's model identifier
    api_endpoint = Column(String(500))
    
    # Model Capabilities
    max_tokens = Column(Integer)
    context_window = Column(Integer)
    supports_streaming = Column(Boolean, default=False)
    supports_function_calling = Column(Boolean, default=False)
    supports_json_mode = Column(Boolean, default=False)
    input_modalities = Column(JSON, default=list)  # text, image, audio, etc.
    output_modalities = Column(JSON, default=list)
    
    # Pricing Information (per 1K tokens)
    input_cost_per_1k_tokens = Column(Numeric(10, 6))  # Cost in USD
    output_cost_per_1k_tokens = Column(Numeric(10, 6))
    
    # Performance Metrics
    average_latency_ms = Column(Integer)
    throughput_requests_per_minute = Column(Integer)
    success_rate = Column(Numeric(5, 4))  # 0.0000 to 1.0000
    
    # Configuration
    default_parameters = Column(JSON, default=dict)  # Default model parameters
    rate_limits = Column(JSON, default=dict)  # Rate limiting configuration
    
    # Status and Usage
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.ACTIVE)
    is_available = Column(Boolean, default=True)
    usage_count = Column(BigInteger, default=0)
    total_tokens_processed = Column(BigInteger, default=0)
    
    # Legal-Specific Configuration
    legal_domains = Column(JSON, default=list)  # Areas of law this model handles
    jurisdiction_support = Column(JSON, default=list)  # Supported jurisdictions
    practice_areas = Column(JSON, default=list)  # Supported practice areas
    
    # Compliance and Security
    data_retention_policy = Column(String(100))
    supports_zero_data_retention = Column(Boolean, default=False)
    gdpr_compliant = Column(Boolean, default=False)
    hipaa_compliant = Column(Boolean, default=False)
    
    # Relationships
    analyses = relationship("AIAnalysis", back_populates="model")
    conversations = relationship("AIConversation", back_populates="model")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_ai_models_provider_type', 'provider', 'model_type'),
        Index('ix_ai_models_status_available', 'status', 'is_available'),
        UniqueConstraint('provider', 'model_id', 'version', name='uq_model_provider_version'),
    )
    
    @property
    def full_name(self) -> str:
        """Get full model name with provider"""
        return f"{self.provider.value}:{self.model_id}:{self.version}"
    
    def calculate_cost(self, input_tokens: int, output_tokens: int = 0) -> Decimal:
        """Calculate cost for token usage"""
        if not self.input_cost_per_1k_tokens:
            return Decimal('0')
        
        input_cost = (Decimal(input_tokens) / 1000) * self.input_cost_per_1k_tokens
        output_cost = Decimal('0')
        
        if output_tokens and self.output_cost_per_1k_tokens:
            output_cost = (Decimal(output_tokens) / 1000) * self.output_cost_per_1k_tokens
        
        return input_cost + output_cost
    
    def __repr__(self):
        return f"<AIModel(id={self.id}, name='{self.name}', provider='{self.provider.value}')>"


class AIAnalysis(BaseModel):
    """AI analysis results for documents and cases"""
    
    __tablename__ = 'ai_analyses'
    
    # Analysis Details
    analysis_type = Column(SQLEnum(AnalysisType), nullable=False)
    title = Column(String(300))
    description = Column(Text)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    
    # Target Objects
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    # AI Model and User
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False)
    requested_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Analysis Input
    input_text = Column(Text)
    input_parameters = Column(JSON, default=dict)
    prompt_template = Column(Text)
    context_data = Column(JSON, default=dict)
    
    # Processing Information
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    processing_time_ms = Column(Integer)
    
    # Token Usage and Cost
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    estimated_cost = Column(Numeric(10, 6))  # In USD
    
    # Results and Output
    result_text = Column(Text)
    result_data = Column(JSON, default=dict)  # Structured results
    confidence_score = Column(Numeric(5, 4))  # 0.0000 to 1.0000
    confidence_level = Column(SQLEnum(ConfidenceLevel))
    
    # Extracted Information
    entities = Column(JSON, default=list)  # Named entities
    key_points = Column(JSON, default=list)  # Important points
    legal_issues = Column(JSON, default=list)  # Identified legal issues
    citations = Column(JSON, default=list)  # Legal citations found
    recommendations = Column(JSON, default=list)  # AI recommendations
    
    # Legal-Specific Results
    legal_concepts = Column(JSON, default=list)
    jurisdiction_analysis = Column(JSON, default=dict)
    risk_factors = Column(JSON, default=list)
    compliance_issues = Column(JSON, default=list)
    
    # Quality and Validation
    human_reviewed = Column(Boolean, default=False)
    reviewed_by_id = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime(timezone=True))
    accuracy_rating = Column(Integer)  # 1-5 scale
    
    # Error Handling
    error_message = Column(Text)
    error_code = Column(String(50))
    retry_count = Column(Integer, default=0)
    
    # Usage and Feedback
    usefulness_rating = Column(Integer)  # 1-5 scale
    user_feedback = Column(Text)
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    document = relationship("Document", foreign_keys=[document_id])
    case = relationship("Case", foreign_keys=[case_id])
    model = relationship("AIModel", back_populates="analyses")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_ai_analyses_type_status', 'analysis_type', 'status'),
        Index('ix_ai_analyses_document_type', 'document_id', 'analysis_type'),
        Index('ix_ai_analyses_case_type', 'case_id', 'analysis_type'),
        Index('ix_ai_analyses_model_date', 'model_id', 'created_at'),
        Index('ix_ai_analyses_user_date', 'requested_by_id', 'created_at'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='ck_valid_confidence'),
        CheckConstraint('(document_id IS NOT NULL) OR (case_id IS NOT NULL)', name='ck_analysis_target_required'),
    )
    
    @property
    def processing_duration_seconds(self) -> Optional[float]:
        """Get processing duration in seconds"""
        if self.processing_time_ms:
            return self.processing_time_ms / 1000
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if analysis is completed"""
        return self.status == JobStatus.COMPLETED
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if analysis has high confidence"""
        return (self.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH] or
                (self.confidence_score and self.confidence_score > 0.7))
    
    def calculate_confidence_level(self):
        """Calculate confidence level from score"""
        if not self.confidence_score:
            return
        
        score = float(self.confidence_score)
        if score < 0.3:
            self.confidence_level = ConfidenceLevel.VERY_LOW
        elif score < 0.5:
            self.confidence_level = ConfidenceLevel.LOW
        elif score < 0.7:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif score < 0.9:
            self.confidence_level = ConfidenceLevel.HIGH
        else:
            self.confidence_level = ConfidenceLevel.VERY_HIGH
    
    def __repr__(self):
        return f"<AIAnalysis(id={self.id}, type='{self.analysis_type.value}', status='{self.status.value}')>"


class AIConversation(BaseModel):
    """AI conversation/chat sessions"""
    
    __tablename__ = 'ai_conversations'
    
    # Conversation Details
    title = Column(String(300))
    conversation_type = Column(String(50), default='general')  # general, legal_research, document_review
    
    # Context
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # AI Model and User
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Conversation State
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    total_tokens = Column(BigInteger, default=0)
    total_cost = Column(Numeric(10, 6), default=0)
    
    # System Settings
    system_prompt = Column(Text)
    model_parameters = Column(JSON, default=dict)
    context_data = Column(JSON, default=dict)
    
    # Privacy and Retention
    is_confidential = Column(Boolean, default=True)
    retention_date = Column(DateTime(timezone=True))
    auto_delete = Column(Boolean, default=True)
    
    # Relationships
    case = relationship("Case", foreign_keys=[case_id])
    document = relationship("Document", foreign_keys=[document_id])
    model = relationship("AIModel", back_populates="conversations")
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship("AIConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_ai_conversations_user_date', 'user_id', 'created_at'),
        Index('ix_ai_conversations_case_date', 'case_id', 'created_at'),
        Index('ix_ai_conversations_active', 'is_active', 'user_id'),
    )
    
    def add_message(self, role: str, content: str, tokens: int = 0, cost: Decimal = 0):
        """Add message to conversation"""
        self.message_count += 1
        self.total_tokens += tokens
        self.total_cost += cost
        
        message = AIConversationMessage(
            conversation_id=self.id,
            role=role,
            content=content,
            token_count=tokens,
            cost=cost,
            sequence_number=self.message_count
        )
        self.messages.append(message)
        return message
    
    def __repr__(self):
        return f"<AIConversation(id={self.id}, title='{self.title}', messages={self.message_count})>"


class AIConversationMessage(BaseModel):
    """Individual messages in AI conversations"""
    
    __tablename__ = 'ai_conversation_messages'
    
    # Message Details
    conversation_id = Column(Integer, ForeignKey('ai_conversations.id'), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Processing Information
    token_count = Column(Integer, default=0)
    cost = Column(Numeric(8, 6), default=0)
    response_time_ms = Column(Integer)
    
    # Function Calling (for advanced models)
    function_call = Column(JSON)  # Function call data
    function_response = Column(JSON)  # Function response data
    
    # Message Metadata
    model_parameters = Column(JSON, default=dict)
    finish_reason = Column(String(50))  # stop, length, function_call, etc.
    
    # Quality and Rating
    rating = Column(Integer)  # 1-5 user rating
    is_helpful = Column(Boolean)
    user_feedback = Column(Text)
    
    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_ai_messages_conversation_seq', 'conversation_id', 'sequence_number'),
        Index('ix_ai_messages_role_date', 'role', 'created_at'),
        UniqueConstraint('conversation_id', 'sequence_number', name='uq_message_sequence'),
    )
    
    def __repr__(self):
        return f"<AIConversationMessage(id={self.id}, role='{self.role}', seq={self.sequence_number})>"


class AIPromptTemplate(NamedModel):
    """Reusable prompt templates for AI models"""
    
    __tablename__ = 'ai_prompt_templates'
    
    # Template Details
    template_type = Column(String(100), nullable=False)  # analysis, generation, classification
    analysis_type = Column(SQLEnum(AnalysisType), nullable=True)
    
    # Content
    system_prompt = Column(Text)
    user_prompt_template = Column(Text, nullable=False)
    variables = Column(JSON, default=list)  # List of template variables
    
    # Model Configuration
    compatible_models = Column(JSON, default=list)  # List of compatible model IDs
    recommended_parameters = Column(JSON, default=dict)
    
    # Usage and Performance
    usage_count = Column(Integer, default=0)
    success_rate = Column(Numeric(5, 4))  # 0.0000 to 1.0000
    average_confidence = Column(Numeric(5, 4))
    
    # Access Control
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Version Control
    version = Column(String(20), default='1.0')
    parent_template_id = Column(Integer, ForeignKey('ai_prompt_templates.id'))
    
    # Legal Context
    practice_areas = Column(JSON, default=list)
    jurisdictions = Column(JSON, default=list)
    document_types = Column(JSON, default=list)
    
    # Relationships
    firm = relationship("LawFirm", foreign_keys=[firm_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    parent_template = relationship("AIPromptTemplate", remote_side=[BaseModel.id])
    
    def format_prompt(self, variables: Dict[str, Any]) -> str:
        """Format the prompt template with provided variables"""
        return self.user_prompt_template.format(**variables)
    
    def __repr__(self):
        return f"<AIPromptTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"


class AIModelUsage(BaseModel):
    """Track AI model usage for billing and monitoring"""
    
    __tablename__ = 'ai_model_usage'
    
    # Usage Details
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=True)
    
    # Request Information
    request_type = Column(String(50))  # completion, chat, embedding, analysis
    analysis_type = Column(SQLEnum(AnalysisType), nullable=True)
    
    # Usage Metrics
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    request_duration_ms = Column(Integer)
    
    # Cost Information
    cost_usd = Column(Numeric(10, 6))
    billing_category = Column(String(50))  # research, analysis, drafting, review
    
    # Context
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    analysis_id = Column(Integer, ForeignKey('ai_analyses.id'), nullable=True)
    
    # Status
    status = Column(String(20), default='success')  # success, error, timeout
    error_code = Column(String(50))
    
    # Aggregation Period (for reporting)
    usage_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    usage_hour = Column(Integer)  # Hour of day (0-23)
    usage_day_of_week = Column(Integer)  # Day of week (0-6)
    
    # Relationships
    model = relationship("AIModel", foreign_keys=[model_id])
    user = relationship("User", foreign_keys=[user_id])
    firm = relationship("LawFirm", foreign_keys=[firm_id])
    case = relationship("Case", foreign_keys=[case_id])
    document = relationship("Document", foreign_keys=[document_id])
    analysis = relationship("AIAnalysis", foreign_keys=[analysis_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_ai_usage_model_date', 'model_id', 'usage_date'),
        Index('ix_ai_usage_user_date', 'user_id', 'usage_date'),
        Index('ix_ai_usage_firm_date', 'firm_id', 'usage_date'),
        Index('ix_ai_usage_billing', 'billing_category', 'usage_date'),
        Index('ix_ai_usage_hourly', 'usage_date', 'usage_hour'),
    )
    
    @validates('input_tokens', 'output_tokens')
    def calculate_total_tokens(self, key, value):
        """Calculate total tokens when input or output changes"""
        if hasattr(self, 'input_tokens') and hasattr(self, 'output_tokens'):
            self.total_tokens = (self.input_tokens or 0) + (self.output_tokens or 0)
        return value
    
    def __repr__(self):
        return f"<AIModelUsage(id={self.id}, model_id={self.model_id}, tokens={self.total_tokens})>"


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    'AIModel',
    'AIAnalysis',
    'AIConversation',
    'AIConversationMessage',
    'AIPromptTemplate',
    'AIModelUsage',
    'AIProvider',
    'ModelType',
    'AnalysisType',
    'JobStatus',
    'ConfidenceLevel',
    'ModelStatus'
]