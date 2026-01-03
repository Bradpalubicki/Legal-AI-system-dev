"""
Compliance and Audit Models for Legal AI System

Models for audit trails, compliance tracking, data retention, privacy controls,
and regulatory compliance (GDPR, CCPA, HIPAA, SOX, etc.).
"""

import enum
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, Date,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Numeric, BigInteger
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, INET

from .base import BaseModel, StatusEnum, PriorityEnum


# =============================================================================
# ENUMS
# =============================================================================

class AuditEventType(enum.Enum):
    """Types of audit events"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    PRINT = "print"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SHARE = "share"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_SENT = "email_sent"
    DOCUMENT_VIEWED = "document_viewed"
    SEARCH_PERFORMED = "search_performed"
    REPORT_GENERATED = "report_generated"
    BACKUP_CREATED = "backup_created"
    DATA_EXPORTED = "data_exported"
    CONFIGURATION_CHANGED = "configuration_changed"
    INTEGRATION_ACCESS = "integration_access"


class ComplianceRegulation(enum.Enum):
    """Regulatory compliance frameworks"""
    GDPR = "gdpr"              # General Data Protection Regulation
    CCPA = "ccpa"              # California Consumer Privacy Act
    HIPAA = "hipaa"            # Health Insurance Portability and Accountability Act
    SOX = "sox"                # Sarbanes-Oxley Act
    GLBA = "glba"              # Gramm-Leach-Bliley Act
    FERPA = "ferpa"            # Family Educational Rights and Privacy Act
    PCI_DSS = "pci_dss"        # Payment Card Industry Data Security Standard
    FISMA = "fisma"            # Federal Information Security Management Act
    ISO_27001 = "iso_27001"    # ISO/IEC 27001
    NIST = "nist"              # NIST Cybersecurity Framework
    ABA_MODEL_RULES = "aba_model_rules"  # ABA Model Rules of Professional Conduct
    STATE_BAR_RULES = "state_bar_rules"
    ATTORNEY_CLIENT_PRIVILEGE = "attorney_client_privilege"


class DataCategory(enum.Enum):
    """Categories of data for compliance"""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_PERSONAL_DATA = "sensitive_personal_data"
    PROTECTED_HEALTH_INFO = "protected_health_info"
    FINANCIAL_DATA = "financial_data"
    BIOMETRIC_DATA = "biometric_data"
    PRIVILEGED_COMMUNICATION = "privileged_communication"
    ATTORNEY_WORK_PRODUCT = "attorney_work_product"
    TRADE_SECRET = "trade_secret"
    CONFIDENTIAL_INFO = "confidential_info"
    PUBLIC_DATA = "public_data"


class RetentionStatus(enum.Enum):
    """Data retention statuses"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    LEGAL_HOLD = "legal_hold"
    PENDING_DESTRUCTION = "pending_destruction"
    DESTROYED = "destroyed"
    PERMANENT = "permanent"


class PrivacyRequestType(enum.Enum):
    """Types of privacy requests"""
    ACCESS_REQUEST = "access_request"          # Right to access data
    RECTIFICATION_REQUEST = "rectification_request"  # Right to correct data
    ERASURE_REQUEST = "erasure_request"        # Right to be forgotten
    PORTABILITY_REQUEST = "portability_request"  # Right to data portability
    OBJECTION_REQUEST = "objection_request"    # Right to object to processing
    RESTRICTION_REQUEST = "restriction_request"  # Right to restrict processing
    WITHDRAWAL_CONSENT = "withdrawal_consent"   # Withdraw consent
    DO_NOT_SELL = "do_not_sell"               # CCPA - Do not sell


class ComplianceStatus(enum.Enum):
    """Compliance check statuses"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    REMEDIATION_REQUIRED = "remediation_required"
    NOT_APPLICABLE = "not_applicable"


# =============================================================================
# AUDIT TRAIL MODELS
# =============================================================================

class AuditLog(BaseModel):
    """Comprehensive audit trail for all system activities"""
    
    __tablename__ = 'audit_logs'
    
    # Event Details
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    event_name = Column(String(200), nullable=False)
    event_description = Column(Text)
    
    # User and Session
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    session_id = Column(String(100), index=True)
    impersonated_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Technical Details
    ip_address = Column(INET)
    user_agent = Column(String(500))
    device_id = Column(String(100))
    geolocation = Column(JSON)  # {"country", "state", "city", "lat", "lng"}
    
    # Resource Information
    resource_type = Column(String(100))  # table name or resource type
    resource_id = Column(String(100))    # primary key or identifier
    resource_name = Column(String(300))  # human-readable resource name
    
    # Change Details
    old_values = Column(JSON)  # Previous values for update operations
    new_values = Column(JSON)  # New values for create/update operations
    changed_fields = Column(JSON)  # List of fields that changed
    
    # Context
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=True)
    
    # Request Information
    request_id = Column(String(100), index=True)
    http_method = Column(String(10))
    endpoint_path = Column(String(500))
    query_parameters = Column(JSON)
    request_body = Column(JSON)
    
    # Response Information
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # Compliance and Legal
    requires_legal_review = Column(Boolean, default=False)
    legal_hold_relevant = Column(Boolean, default=False)
    compliance_flags = Column(JSON, default=list)
    retention_category = Column(String(100))
    
    # Risk Assessment
    risk_level = Column(String(20), default='low')  # low, medium, high, critical
    sensitive_data_accessed = Column(Boolean, default=False)
    privileged_data_accessed = Column(Boolean, default=False)
    
    # Additional Metadata
    additional_data = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    impersonated_user = relationship("User", foreign_keys=[impersonated_user_id])
    case = relationship("Case", foreign_keys=[case_id])
    client = relationship("Client", foreign_keys=[client_id])
    firm = relationship("LawFirm", foreign_keys=[firm_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_audit_logs_event_time', 'event_type', 'created_at'),
        Index('ix_audit_logs_user_time', 'user_id', 'created_at'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('ix_audit_logs_session', 'session_id', 'created_at'),
        Index('ix_audit_logs_ip_time', 'ip_address', 'created_at'),
        Index('ix_audit_logs_case_time', 'case_id', 'created_at'),
        Index('ix_audit_logs_compliance', 'compliance_flags'),
        Index('ix_audit_logs_risk', 'risk_level', 'sensitive_data_accessed'),
    )
    
    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event"""
        security_events = [
            AuditEventType.LOGIN_FAILED,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.PERMISSION_CHANGED,
            AuditEventType.PASSWORD_CHANGED
        ]
        return self.event_type in security_events
    
    @property
    def is_data_access_event(self) -> bool:
        """Check if this involves data access"""
        data_events = [
            AuditEventType.READ,
            AuditEventType.DOWNLOAD,
            AuditEventType.EXPORT,
            AuditEventType.DOCUMENT_VIEWED,
            AuditEventType.SEARCH_PERFORMED
        ]
        return self.event_type in data_events
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event='{self.event_type.value}', user_id={self.user_id})>"


# =============================================================================
# COMPLIANCE MANAGEMENT MODELS
# =============================================================================

class ComplianceFramework(BaseModel):
    """Regulatory compliance frameworks and requirements"""
    
    __tablename__ = 'compliance_frameworks'
    
    # Framework Details
    name = Column(String(200), nullable=False)
    regulation = Column(SQLEnum(ComplianceRegulation), nullable=False, index=True)
    version = Column(String(50))
    description = Column(Text)
    
    # Applicability
    applies_to_firm = Column(Boolean, default=True)
    jurisdiction = Column(String(100))
    industry_specific = Column(Boolean, default=False)
    industries = Column(JSON, default=list)
    
    # Requirements
    requirements = Column(JSON, default=list)  # List of specific requirements
    controls = Column(JSON, default=list)     # Required controls
    policies_required = Column(JSON, default=list)
    
    # Implementation
    is_active = Column(Boolean, default=True)
    implementation_date = Column(Date)
    next_review_date = Column(Date)
    responsible_person_id = Column(Integer, ForeignKey('users.id'))
    
    # Documentation
    policy_documents = Column(JSON, default=list)
    training_materials = Column(JSON, default=list)
    reference_links = Column(JSON, default=list)
    
    # Relationships
    responsible_person = relationship("User", foreign_keys=[responsible_person_id])
    assessments = relationship("ComplianceAssessment", back_populates="framework")
    
    def __repr__(self):
        return f"<ComplianceFramework(id={self.id}, name='{self.name}', regulation='{self.regulation.value}')>"


class ComplianceAssessment(BaseModel):
    """Compliance assessments and audits"""
    
    __tablename__ = 'compliance_assessments'
    
    # Assessment Details
    title = Column(String(300), nullable=False)
    framework_id = Column(Integer, ForeignKey('compliance_frameworks.id'), nullable=False)
    assessment_type = Column(String(50), default='internal')  # internal, external, self
    
    # Scope
    scope_description = Column(Text)
    departments = Column(JSON, default=list)
    systems = Column(JSON, default=list)
    data_types = Column(JSON, default=list)
    
    # Timeline
    start_date = Column(Date)
    end_date = Column(Date)
    due_date = Column(Date)
    
    # Personnel
    assessor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reviewers = Column(JSON, default=list)  # List of user IDs
    
    # Results
    overall_status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.UNDER_REVIEW)
    compliance_percentage = Column(Numeric(5, 2))  # 0.00 to 100.00
    
    # Findings
    compliant_controls = Column(Integer, default=0)
    non_compliant_controls = Column(Integer, default=0)
    partially_compliant_controls = Column(Integer, default=0)
    
    # Risk Assessment
    risk_level = Column(String(20), default='medium')
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    
    # Deliverables
    executive_summary = Column(Text)
    detailed_findings = Column(Text)
    recommendations = Column(Text)
    report_path = Column(String(500))
    
    # Follow-up
    remediation_plan_id = Column(Integer, ForeignKey('remediation_plans.id'))
    next_assessment_date = Column(Date)
    
    # Relationships
    framework = relationship("ComplianceFramework", back_populates="assessments")
    assessor = relationship("User", foreign_keys=[assessor_id])
    findings = relationship("ComplianceFinding", back_populates="assessment")
    remediation_plan = relationship("RemediationPlan", back_populates="assessment")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_assessments_framework_date', 'framework_id', 'start_date'),
        Index('ix_assessments_status', 'overall_status'),
        Index('ix_assessments_due_date', 'due_date'),
    )
    
    @property
    def is_overdue(self) -> bool:
        """Check if assessment is overdue"""
        return self.due_date and self.due_date < date.today() and self.overall_status == ComplianceStatus.UNDER_REVIEW
    
    @property
    def total_findings(self) -> int:
        """Get total number of findings"""
        return (self.critical_findings + self.high_findings + 
                self.medium_findings + self.low_findings)
    
    def __repr__(self):
        return f"<ComplianceAssessment(id={self.id}, title='{self.title}', status='{self.overall_status.value}')>"


class ComplianceFinding(BaseModel):
    """Individual compliance findings and issues"""
    
    __tablename__ = 'compliance_findings'
    
    # Finding Details
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    assessment_id = Column(Integer, ForeignKey('compliance_assessments.id'), nullable=False)
    
    # Classification
    finding_type = Column(String(50))  # control_deficiency, policy_gap, procedural_issue
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    risk_rating = Column(String(20))
    
    # Control Information
    control_id = Column(String(100))
    control_name = Column(String(200))
    requirement_reference = Column(String(200))
    
    # Status
    status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.NON_COMPLIANT)
    resolution_status = Column(String(50), default='open')  # open, in_progress, resolved, accepted_risk
    
    # Impact Assessment
    business_impact = Column(Text)
    legal_risk = Column(String(20))
    financial_impact = Column(Numeric(12, 2))
    
    # Resolution
    recommendation = Column(Text)
    remediation_effort = Column(String(20))  # low, medium, high
    estimated_cost = Column(Numeric(10, 2))
    target_resolution_date = Column(Date)
    actual_resolution_date = Column(Date)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey('users.id'))
    assigned_date = Column(Date)
    
    # Evidence
    evidence = Column(JSON, default=list)  # Supporting evidence/documentation
    screenshots = Column(JSON, default=list)
    
    # Follow-up
    follow_up_required = Column(Boolean, default=True)
    next_review_date = Column(Date)
    resolution_notes = Column(Text)
    
    # Relationships
    assessment = relationship("ComplianceAssessment", back_populates="findings")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_findings_assessment_severity', 'assessment_id', 'severity'),
        Index('ix_findings_status', 'status', 'resolution_status'),
        Index('ix_findings_assigned', 'assigned_to_id', 'status'),
        Index('ix_findings_due_date', 'target_resolution_date'),
    )
    
    @property
    def is_overdue(self) -> bool:
        """Check if finding resolution is overdue"""
        return (self.target_resolution_date and 
                self.target_resolution_date < date.today() and 
                self.resolution_status not in ['resolved', 'accepted_risk'])
    
    def __repr__(self):
        return f"<ComplianceFinding(id={self.id}, severity='{self.severity}', status='{self.status.value}')>"


class RemediationPlan(BaseModel):
    """Plans for addressing compliance findings"""
    
    __tablename__ = 'remediation_plans'
    
    # Plan Details
    title = Column(String(300), nullable=False)
    description = Column(Text)
    assessment_id = Column(Integer, ForeignKey('compliance_assessments.id'), nullable=False)
    
    # Planning
    plan_owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    stakeholders = Column(JSON, default=list)  # List of user IDs
    
    # Timeline
    start_date = Column(Date)
    target_completion_date = Column(Date)
    actual_completion_date = Column(Date)
    
    # Status
    status = Column(String(50), default='draft')  # draft, approved, in_progress, completed, cancelled
    progress_percentage = Column(Numeric(5, 2), default=0)  # 0.00 to 100.00
    
    # Resources
    estimated_budget = Column(Numeric(12, 2))
    actual_cost = Column(Numeric(12, 2))
    resources_required = Column(Text)
    
    # Implementation
    approach = Column(Text)
    success_criteria = Column(Text)
    risk_mitigation = Column(Text)
    
    # Approval
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_date = Column(Date)
    approval_notes = Column(Text)
    
    # Monitoring
    last_review_date = Column(Date)
    next_review_date = Column(Date)
    
    # Relationships
    assessment = relationship("ComplianceAssessment", back_populates="remediation_plan")
    plan_owner = relationship("User", foreign_keys=[plan_owner_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    tasks = relationship("RemediationTask", back_populates="plan")
    
    def __repr__(self):
        return f"<RemediationPlan(id={self.id}, title='{self.title}', status='{self.status}')>"


class RemediationTask(BaseModel):
    """Individual tasks within a remediation plan"""
    
    __tablename__ = 'remediation_tasks'
    
    # Task Details
    title = Column(String(300), nullable=False)
    description = Column(Text)
    plan_id = Column(Integer, ForeignKey('remediation_plans.id'), nullable=False)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    
    # Timeline
    due_date = Column(Date)
    estimated_hours = Column(Numeric(5, 2))
    actual_hours = Column(Numeric(5, 2))
    
    # Status
    status = Column(String(50), default='not_started')  # not_started, in_progress, completed, blocked
    progress_percentage = Column(Numeric(5, 2), default=0)
    
    # Completion
    completion_date = Column(Date)
    completion_notes = Column(Text)
    deliverables = Column(JSON, default=list)
    
    # Dependencies
    depends_on_tasks = Column(JSON, default=list)  # List of task IDs
    
    # Relationships
    plan = relationship("RemediationPlan", back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    
    def __repr__(self):
        return f"<RemediationTask(id={self.id}, title='{self.title}', status='{self.status}')>"


# =============================================================================
# DATA RETENTION MODELS
# =============================================================================

class DataRetentionPolicy(BaseModel):
    """Data retention policies and schedules"""
    
    __tablename__ = 'data_retention_policies'
    
    # Policy Details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    version = Column(String(20), default='1.0')
    
    # Scope
    data_category = Column(SQLEnum(DataCategory), nullable=False)
    applies_to_tables = Column(JSON, default=list)  # Database tables
    applies_to_file_types = Column(JSON, default=list)
    
    # Retention Rules
    retention_period_years = Column(Integer)
    retention_period_months = Column(Integer)
    retention_period_days = Column(Integer)
    retention_trigger = Column(String(100))  # event that starts retention clock
    
    # Legal Requirements
    legal_basis = Column(String(200))  # Legal requirement for retention
    regulatory_citations = Column(JSON, default=list)
    jurisdiction = Column(String(100))
    
    # Disposal
    disposal_method = Column(String(100))  # secure_delete, archive, anonymize
    disposal_approval_required = Column(Boolean, default=True)
    disposal_documentation_required = Column(Boolean, default=True)
    
    # Exceptions
    litigation_hold_applies = Column(Boolean, default=True)
    client_request_override = Column(Boolean, default=False)
    business_need_extension = Column(Boolean, default=False)
    
    # Implementation
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date)
    next_review_date = Column(Date)
    
    # Relationships
    retention_records = relationship("DataRetentionRecord", back_populates="policy")
    
    def calculate_retention_date(self, trigger_date: date) -> date:
        """Calculate retention date based on trigger date"""
        from dateutil.relativedelta import relativedelta
        
        retention_date = trigger_date
        if self.retention_period_years:
            retention_date = retention_date + relativedelta(years=self.retention_period_years)
        if self.retention_period_months:
            retention_date = retention_date + relativedelta(months=self.retention_period_months)
        if self.retention_period_days:
            retention_date = retention_date + relativedelta(days=self.retention_period_days)
        
        return retention_date
    
    def __repr__(self):
        return f"<DataRetentionPolicy(id={self.id}, name='{self.name}', category='{self.data_category.value}')>"


class DataRetentionRecord(BaseModel):
    """Individual records subject to data retention"""
    
    __tablename__ = 'data_retention_records'
    
    # Record Identification
    record_type = Column(String(100), nullable=False)  # table name or record type
    record_id = Column(String(100), nullable=False)    # primary key
    record_description = Column(String(300))
    
    # Policy
    policy_id = Column(Integer, ForeignKey('data_retention_policies.id'), nullable=False)
    data_category = Column(SQLEnum(DataCategory), nullable=False)
    
    # Retention Dates
    trigger_date = Column(Date, nullable=False)
    retention_date = Column(Date, nullable=False)
    destruction_date = Column(Date)
    
    # Status
    status = Column(SQLEnum(RetentionStatus), default=RetentionStatus.ACTIVE)
    
    # Legal Hold
    legal_hold_active = Column(Boolean, default=False)
    legal_hold_case = Column(String(200))
    legal_hold_start_date = Column(Date)
    legal_hold_end_date = Column(Date)
    
    # Context
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    matter_id = Column(String(100))
    
    # Disposal
    disposal_method = Column(String(100))
    disposal_date = Column(Date)
    disposal_approved_by_id = Column(Integer, ForeignKey('users.id'))
    disposal_certificate_path = Column(String(500))
    
    # Audit
    last_reviewed_date = Column(Date)
    reviewed_by_id = Column(Integer, ForeignKey('users.id'))
    review_notes = Column(Text)
    
    # Relationships
    policy = relationship("DataRetentionPolicy", back_populates="retention_records")
    case = relationship("Case", foreign_keys=[case_id])
    client = relationship("Client", foreign_keys=[client_id])
    disposal_approved_by = relationship("User", foreign_keys=[disposal_approved_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_retention_records_retention_date', 'retention_date', 'status'),
        Index('ix_retention_records_policy', 'policy_id', 'status'),
        Index('ix_retention_records_case', 'case_id'),
        Index('ix_retention_records_legal_hold', 'legal_hold_active'),
        UniqueConstraint('record_type', 'record_id', name='uq_retention_record'),
    )
    
    @property
    def is_due_for_destruction(self) -> bool:
        """Check if record is due for destruction"""
        return (self.retention_date <= date.today() and 
                not self.legal_hold_active and 
                self.status == RetentionStatus.ACTIVE)
    
    @property
    def days_until_destruction(self) -> int:
        """Calculate days until destruction"""
        if self.legal_hold_active:
            return -1  # Cannot be destroyed while on legal hold
        return (self.retention_date - date.today()).days
    
    def __repr__(self):
        return f"<DataRetentionRecord(id={self.id}, record_type='{self.record_type}', status='{self.status.value}')>"


class PrivacyRequest(BaseModel):
    """Data subject privacy requests (GDPR, CCPA, etc.)"""
    
    __tablename__ = 'privacy_requests'
    
    # Request Details
    request_type = Column(SQLEnum(PrivacyRequestType), nullable=False)
    request_source = Column(String(50), default='email')  # email, phone, portal, letter
    
    # Data Subject
    data_subject_name = Column(String(200), nullable=False)
    data_subject_email = Column(String(255))
    data_subject_phone = Column(String(20))
    identity_verified = Column(Boolean, default=False)
    verification_method = Column(String(100))
    
    # Request Content
    request_description = Column(Text, nullable=False)
    specific_data_requested = Column(Text)
    date_range_requested = Column(Text)
    preferred_format = Column(String(50))  # pdf, csv, json
    
    # Processing
    received_date = Column(Date, default=date.today)
    acknowledgment_sent = Column(Boolean, default=False)
    acknowledgment_date = Column(Date)
    due_date = Column(Date, nullable=False)  # Legal deadline
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_date = Column(Date)
    
    # Status
    status = Column(String(50), default='received')  # received, in_progress, completed, rejected, extended
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    
    # Legal Basis
    legal_basis_for_processing = Column(Text)
    exemptions_claimed = Column(JSON, default=list)
    rejection_reason = Column(Text)
    
    # Response
    response_date = Column(Date)
    response_method = Column(String(50))  # email, mail, portal
    response_path = Column(String(500))  # Path to response file
    
    # Data Search Results
    data_sources_searched = Column(JSON, default=list)
    records_found_count = Column(Integer, default=0)
    data_provided = Column(Boolean, default=False)
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    appeal_filed = Column(Boolean, default=False)
    appeal_date = Column(Date)
    
    # Compliance
    regulatory_framework = Column(SQLEnum(ComplianceRegulation))
    deadline_met = Column(Boolean)
    extension_requested = Column(Boolean, default=False)
    extension_granted = Column(Boolean, default=False)
    
    # Notes
    processing_notes = Column(Text)
    internal_notes = Column(Text)
    
    # Relationships
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_privacy_requests_type_status', 'request_type', 'status'),
        Index('ix_privacy_requests_due_date', 'due_date'),
        Index('ix_privacy_requests_assigned', 'assigned_to_id', 'status'),
        Index('ix_privacy_requests_subject', 'data_subject_email'),
    )
    
    @property
    def is_overdue(self) -> bool:
        """Check if request is overdue"""
        return self.due_date < date.today() and self.status not in ['completed', 'rejected']
    
    @property
    def days_until_due(self) -> int:
        """Calculate days until due date"""
        return (self.due_date - date.today()).days
    
    def __repr__(self):
        return f"<PrivacyRequest(id={self.id}, type='{self.request_type.value}', status='{self.status}')>"


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    'AuditLog',
    'ComplianceFramework',
    'ComplianceAssessment',
    'ComplianceFinding',
    'RemediationPlan',
    'RemediationTask',
    'DataRetentionPolicy',
    'DataRetentionRecord',
    'PrivacyRequest',
    'AuditEventType',
    'ComplianceRegulation',
    'DataCategory',
    'RetentionStatus',
    'PrivacyRequestType',
    'ComplianceStatus'
]