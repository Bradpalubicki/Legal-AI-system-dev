"""
Legal AI System Database Models

Complete database schema for the Legal AI System including:
- User management and authentication
- Case and matter management  
- Document processing and analysis
- AI integration and analysis
- Legal research and citations
- Compliance and audit trails
- Billing and workflow automation

All models use SQLAlchemy ORM with PostgreSQL-specific features.
"""

# Import base classes and utilities
from .base import (
    Base, 
    StatusEnum, 
    PriorityEnum, 
    ConfidentialityLevel,
    TimestampMixin,
    UUIDMixin,
    SoftDeleteMixin,
    AuditMixin,
    MetadataMixin,
    BaseModelMixin,
    BaseModel,
    NamedModel,
    StatusModel,
    create_database_url,
    generate_table_name,
    DatabaseUtils
)

# Import user management models
from .user_management import (
    User,
    LawFirm,
    Client, 
    Role,
    Permission,
    UserType,
    UserStatus,
    PermissionType,
    AuthenticationMethod,
    FirmSize,
    PracticeArea,
    user_roles,
    role_permissions,
    user_firms
)

# Import case management models
from .case_management import (
    Case,
    Task,
    CalendarEvent,
    Deadline,
    CaseParty,
    TimeEntry,
    CaseStatus,
    CaseType,
    TaskStatus,
    TaskType,
    EventType,
    DeadlineType,
    PartyRole,
    CourtLevel,
    case_attorneys
)

# Import document processing models
from .document_processing import (
    Document,
    DocumentContent,
    DocumentProcessingJob,
    DocumentAnnotation,
    DocumentReview,
    DocumentTemplate,
    DocumentType,
    DocumentStatus,
    DocumentFormat,
    ProcessingType,
    VersionType,
    AccessLevel,
    ReviewStatus,
    document_cases,
    document_relationships
)

# Import AI integration models
from .ai_integration import (
    AIModel,
    AIAnalysis,
    AIConversation,
    AIConversationMessage,
    AIPromptTemplate,
    AIModelUsage,
    AIProvider,
    ModelType,
    AnalysisType,
    JobStatus,
    ConfidenceLevel,
    ModelStatus
)

# Import legal research models
from .legal_research import (
    ResearchProject,
    LegalSearch,
    LegalSearchResult,
    LegalSource,
    LegalCitation,
    LegalSourceAnnotation,
    ResearchDatabase,
    LegalSourceType,
    CourtType as ResearchCourtType,
    ResearchStatus,
    CitationRelevance,
    LegalAuthority
)

# Import compliance and audit models
from .compliance_audit import (
    AuditLog,
    ComplianceFramework,
    ComplianceAssessment,
    ComplianceFinding,
    RemediationPlan,
    RemediationTask,
    DataRetentionPolicy,
    DataRetentionRecord,
    PrivacyRequest,
    AuditEventType,
    ComplianceRegulation,
    DataCategory,
    RetentionStatus,
    PrivacyRequestType,
    ComplianceStatus
)

# Import billing and workflow models
from .billing_workflow import (
    BillingArrangement,
    Invoice,
    InvoiceLineItem,
    Payment,
    Expense,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStepLog,
    BillingType,
    InvoiceStatus,
    PaymentMethod,
    ExpenseType,
    WorkflowStatus,
    WorkflowTriggerType,
    TaskAutomationType
)

# Import original PACER-specific models for backward compatibility
from .models import (
    TrackedDocket,
    RecapTask,
    DocketDocument,
    DocketTrackingStatus,
    RecapTaskStatus,
    RecapTaskType,
    Priority
)


# Collect all model classes for easy reference
MODEL_CLASSES = [
    # Base models
    User, LawFirm, Client, Role, Permission,
    
    # Case management
    Case, Task, CalendarEvent, Deadline, CaseParty, TimeEntry,
    
    # Document processing
    Document, DocumentContent, DocumentProcessingJob, 
    DocumentAnnotation, DocumentReview, DocumentTemplate,
    
    # AI integration
    AIModel, AIAnalysis, AIConversation, AIConversationMessage,
    AIPromptTemplate, AIModelUsage,
    
    # Legal research
    ResearchProject, LegalSearch, LegalSearchResult, 
    LegalSource, LegalCitation, LegalSourceAnnotation,
    
    # Compliance and audit
    AuditLog, ComplianceFramework, ComplianceAssessment,
    ComplianceFinding, RemediationPlan, RemediationTask,
    DataRetentionPolicy, DataRetentionRecord, PrivacyRequest,
    
    # Billing and workflow
    BillingArrangement, Invoice, InvoiceLineItem, Payment, Expense,
    WorkflowDefinition, WorkflowExecution, WorkflowStepLog,
    
    # PACER/RECAP models
    TrackedDocket, RecapTask, DocketDocument
]

# Association tables
ASSOCIATION_TABLES = [
    user_roles,
    role_permissions, 
    user_firms,
    case_attorneys,
    document_cases,
    document_relationships
]


def get_all_models():
    """Get all SQLAlchemy model classes"""
    return MODEL_CLASSES


def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """Drop all database tables - USE WITH CAUTION"""
    Base.metadata.drop_all(bind=engine)


# Database schema version for migrations
SCHEMA_VERSION = "1.0.0"

# Export everything for convenient imports
__all__ = [
    # Base classes
    'Base', 'BaseModel', 'NamedModel', 'StatusModel',
    'TimestampMixin', 'UUIDMixin', 'SoftDeleteMixin', 'AuditMixin', 'MetadataMixin',
    
    # Core models
    'User', 'LawFirm', 'Client', 'Role', 'Permission',
    'Case', 'Task', 'CalendarEvent', 'Deadline', 'CaseParty', 'TimeEntry',
    'Document', 'DocumentContent', 'DocumentProcessingJob', 'DocumentAnnotation', 'DocumentReview', 'DocumentTemplate',
    'AIModel', 'AIAnalysis', 'AIConversation', 'AIConversationMessage', 'AIPromptTemplate', 'AIModelUsage',
    'ResearchProject', 'LegalSearch', 'LegalSearchResult', 'LegalSource', 'LegalCitation', 'LegalSourceAnnotation',
    'AuditLog', 'ComplianceFramework', 'ComplianceAssessment', 'ComplianceFinding', 'RemediationPlan', 'RemediationTask',
    'DataRetentionPolicy', 'DataRetentionRecord', 'PrivacyRequest',
    'BillingArrangement', 'Invoice', 'InvoiceLineItem', 'Payment', 'Expense',
    'WorkflowDefinition', 'WorkflowExecution', 'WorkflowStepLog',
    'TrackedDocket', 'RecapTask', 'DocketDocument',
    
    # Enums
    'StatusEnum', 'PriorityEnum', 'ConfidentialityLevel',
    'UserType', 'UserStatus', 'PermissionType', 'AuthenticationMethod', 'FirmSize', 'PracticeArea',
    'CaseStatus', 'CaseType', 'TaskStatus', 'TaskType', 'EventType', 'DeadlineType', 'PartyRole', 'CourtLevel',
    'DocumentType', 'DocumentStatus', 'DocumentFormat', 'ProcessingType', 'VersionType', 'AccessLevel', 'ReviewStatus',
    'AIProvider', 'ModelType', 'AnalysisType', 'JobStatus', 'ConfidenceLevel', 'ModelStatus',
    'ResearchDatabase', 'LegalSourceType', 'ResearchCourtType', 'ResearchStatus', 'CitationRelevance', 'LegalAuthority',
    'AuditEventType', 'ComplianceRegulation', 'DataCategory', 'RetentionStatus', 'PrivacyRequestType', 'ComplianceStatus',
    'BillingType', 'InvoiceStatus', 'PaymentMethod', 'ExpenseType', 'WorkflowStatus', 'WorkflowTriggerType', 'TaskAutomationType',
    'DocketTrackingStatus', 'RecapTaskStatus', 'RecapTaskType', 'Priority',
    
    # Association tables
    'user_roles', 'role_permissions', 'user_firms', 'case_attorneys', 'document_cases', 'document_relationships',
    
    # Utilities
    'create_database_url', 'generate_table_name', 'DatabaseUtils',
    'get_all_models', 'create_all_tables', 'drop_all_tables',
    'MODEL_CLASSES', 'ASSOCIATION_TABLES', 'SCHEMA_VERSION'
]