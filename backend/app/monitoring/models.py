# =============================================================================
# Legal AI System - Performance Monitoring Models
# =============================================================================
# Database models for performance metrics, alerts, SLA tracking, and
# monitoring configuration with legal compliance and audit focus
# =============================================================================

from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, Numeric, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

Base = declarative_base()

# =============================================================================
# MONITORING ENUMS
# =============================================================================

class MetricType(Enum):
    """Types of performance metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"

class MetricCategory(Enum):
    """Performance metric categories."""
    SYSTEM = "system"
    APPLICATION = "application"
    DATABASE = "database"
    API = "api"
    AI_PROCESSING = "ai_processing"
    LEGAL_ANALYSIS = "legal_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    USER_EXPERIENCE = "user_experience"
    SECURITY = "security"
    COMPLIANCE = "compliance"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"

class SLAStatus(Enum):
    """SLA compliance status."""
    MEETING = "meeting"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    UNKNOWN = "unknown"

class ThresholdOperator(Enum):
    """Threshold comparison operators."""
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal

# =============================================================================
# METRICS MODELS
# =============================================================================

class MetricDefinition(Base):
    """Metric definition and configuration."""
    __tablename__ = "metric_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(500))
    description = Column(Text)
    
    # Metric configuration
    metric_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    unit = Column(String(50))  # bytes, seconds, requests, etc.
    
    # Collection settings
    collection_interval_seconds = Column(Integer, default=60)
    retention_days = Column(Integer, default=90)
    aggregation_functions = Column(JSONB)  # avg, sum, min, max, p95, p99
    
    # Legal and compliance
    contains_sensitive_data = Column(Boolean, default=False)
    compliance_tags = Column(JSONB)
    data_classification = Column(String(50))
    
    # Metadata
    tags = Column(JSONB)
    enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    metric_samples = relationship("MetricSample", back_populates="metric_definition", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="metric_definition")

class MetricSample(Base):
    """Individual metric sample/data point."""
    __tablename__ = "metric_samples"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_definition_id = Column(UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=False)
    
    # Sample data
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Numeric(precision=20, scale=6), nullable=False)
    
    # Context and labels
    labels = Column(JSONB)  # service, instance, user_id, etc.
    source_instance = Column(String(255))
    source_component = Column(String(255))
    
    # Additional metadata
    sample_metadata = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    metric_definition = relationship("MetricDefinition", back_populates="metric_samples")
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('ix_metric_samples_timestamp_metric', 'timestamp', 'metric_definition_id'),
        Index('ix_metric_samples_labels', 'labels'),
    )

class AggregatedMetric(Base):
    """Pre-aggregated metric data for faster queries."""
    __tablename__ = "aggregated_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_definition_id = Column(UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=False)
    
    # Time window
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    window_size_seconds = Column(Integer, nullable=False)  # 300, 3600, 86400
    
    # Aggregated values
    sample_count = Column(Integer, nullable=False)
    avg_value = Column(Numeric(precision=20, scale=6))
    min_value = Column(Numeric(precision=20, scale=6))
    max_value = Column(Numeric(precision=20, scale=6))
    sum_value = Column(Numeric(precision=20, scale=6))
    percentile_50 = Column(Numeric(precision=20, scale=6))
    percentile_95 = Column(Numeric(precision=20, scale=6))
    percentile_99 = Column(Numeric(precision=20, scale=6))
    
    # Labels for filtering
    labels = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('ix_aggregated_metrics_window', 'window_start', 'window_end', 'metric_definition_id'),
        Index('ix_aggregated_metrics_window_size', 'window_size_seconds', 'metric_definition_id'),
    )

# =============================================================================
# ALERTING MODELS
# =============================================================================

class AlertRule(Base):
    """Alert rule definition."""
    __tablename__ = "alert_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_definition_id = Column(UUID(as_uuid=True), ForeignKey("metric_definitions.id"), nullable=False)
    
    # Rule identification
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    severity = Column(String(50), nullable=False)
    
    # Threshold configuration
    threshold_value = Column(Numeric(precision=20, scale=6), nullable=False)
    threshold_operator = Column(String(10), nullable=False)  # gt, gte, lt, lte, eq, ne
    evaluation_window_seconds = Column(Integer, default=300)  # 5 minutes
    
    # Trigger conditions
    consecutive_breaches = Column(Integer, default=1)
    breach_percentage = Column(Numeric(precision=5, scale=2), default=100.0)  # % of samples that must breach
    
    # Alert behavior
    suppress_duration_seconds = Column(Integer, default=3600)  # 1 hour
    auto_resolve = Column(Boolean, default=True)
    resolution_timeout_seconds = Column(Integer, default=86400)  # 24 hours
    
    # Notification configuration
    notification_channels = Column(JSONB)  # email, slack, pagerduty, etc.
    escalation_policy = Column(JSONB)
    
    # Filtering
    label_filters = Column(JSONB)
    
    # Legal and compliance
    business_critical = Column(Boolean, default=False)
    compliance_related = Column(Boolean, default=False)
    client_impacting = Column(Boolean, default=False)
    
    # Status
    enabled = Column(Boolean, default=True)
    last_evaluation_at = Column(DateTime(timezone=True))
    next_evaluation_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    metric_definition = relationship("MetricDefinition", back_populates="alert_rules")
    alerts = relationship("Alert", back_populates="alert_rule", cascade="all, delete-orphan")

class Alert(Base):
    """Alert instance."""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False)
    
    # Alert details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=AlertStatus.OPEN.value, index=True)
    
    # Timing
    triggered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Values and context
    trigger_value = Column(Numeric(precision=20, scale=6))
    threshold_value = Column(Numeric(precision=20, scale=6))
    evaluation_data = Column(JSONB)  # Sample data that triggered alert
    
    # Assignment and escalation
    assigned_to = Column(String(255))
    escalation_level = Column(Integer, default=0)
    escalation_history = Column(JSONB)
    
    # Actions and resolution
    acknowledged_by = Column(String(255))
    resolved_by = Column(String(255))
    resolution_notes = Column(Text)
    
    # Legal and business context
    client_impact = Column(Boolean, default=False)
    business_impact_level = Column(String(50))  # low, medium, high, critical
    compliance_impact = Column(Boolean, default=False)
    
    # Notification tracking
    notifications_sent = Column(JSONB)
    last_notification_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    alert_rule = relationship("AlertRule", back_populates="alerts")
    alert_annotations = relationship("AlertAnnotation", back_populates="alert", cascade="all, delete-orphan")

class AlertAnnotation(Base):
    """Alert annotations and comments."""
    __tablename__ = "alert_annotations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False)
    
    # Annotation details
    annotation_type = Column(String(50), nullable=False)  # comment, action, escalation
    content = Column(Text, nullable=False)
    
    # Author
    created_by = Column(String(255))
    visibility = Column(String(50), default="internal")  # internal, client, public
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    alert = relationship("Alert", back_populates="alert_annotations")

# =============================================================================
# SLA MONITORING MODELS
# =============================================================================

class SLADefinition(Base):
    """Service Level Agreement definition."""
    __tablename__ = "sla_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # SLA identification
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    service_name = Column(String(255), nullable=False)
    
    # SLA targets
    availability_target = Column(Numeric(precision=5, scale=2))  # 99.95%
    response_time_target_ms = Column(Integer)  # 500ms
    throughput_target_rps = Column(Integer)  # requests per second
    error_rate_target = Column(Numeric(precision=5, scale=2))  # 0.1%
    
    # Measurement configuration
    measurement_window_hours = Column(Integer, default=24)
    measurement_interval_seconds = Column(Integer, default=300)
    
    # Legal and business context
    client_tier = Column(String(50))  # premium, standard, basic
    contract_reference = Column(String(255))
    business_criticality = Column(String(50))  # critical, high, medium, low
    
    # Compliance requirements
    regulatory_requirements = Column(JSONB)
    data_residency_requirements = Column(JSONB)
    
    # Status
    enabled = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True))
    effective_until = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sla_measurements = relationship("SLAMeasurement", back_populates="sla_definition", cascade="all, delete-orphan")

class SLAMeasurement(Base):
    """SLA measurement data."""
    __tablename__ = "sla_measurements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_definition_id = Column(UUID(as_uuid=True), ForeignKey("sla_definitions.id"), nullable=False)
    
    # Measurement period
    measurement_start = Column(DateTime(timezone=True), nullable=False)
    measurement_end = Column(DateTime(timezone=True), nullable=False)
    
    # Measured values
    availability_percentage = Column(Numeric(precision=5, scale=2))
    avg_response_time_ms = Column(Numeric(precision=10, scale=3))
    p95_response_time_ms = Column(Numeric(precision=10, scale=3))
    p99_response_time_ms = Column(Numeric(precision=10, scale=3))
    throughput_rps = Column(Numeric(precision=10, scale=3))
    error_rate_percentage = Column(Numeric(precision=5, scale=2))
    
    # Compliance status
    availability_status = Column(String(50))
    response_time_status = Column(String(50))
    throughput_status = Column(String(50))
    error_rate_status = Column(String(50))
    overall_status = Column(String(50))
    
    # Data quality
    sample_count = Column(Integer)
    data_completeness_percentage = Column(Numeric(precision=5, scale=2))
    measurement_confidence = Column(String(50))  # high, medium, low
    
    # Context
    incidents_during_period = Column(Integer, default=0)
    maintenance_windows = Column(JSONB)
    exclusions_applied = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sla_definition = relationship("SLADefinition", back_populates="sla_measurements")
    
    # Indexes
    __table_args__ = (
        Index('ix_sla_measurements_period', 'measurement_start', 'measurement_end', 'sla_definition_id'),
    )

# =============================================================================
# PERFORMANCE INSIGHTS MODELS
# =============================================================================

class PerformanceInsight(Base):
    """Performance insights and recommendations."""
    __tablename__ = "performance_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Insight details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    insight_type = Column(String(50), nullable=False)  # bottleneck, optimization, anomaly
    category = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False)
    
    # Analysis results
    affected_services = Column(JSONB)
    affected_metrics = Column(JSONB)
    impact_assessment = Column(JSONB)
    
    # Recommendations
    recommendations = Column(JSONB)
    estimated_improvement = Column(JSONB)
    implementation_effort = Column(String(50))  # low, medium, high
    
    # Detection
    detection_method = Column(String(50))  # rule_based, ml_based, manual
    confidence_score = Column(Numeric(precision=3, scale=2))  # 0.0 - 1.0
    detection_data = Column(JSONB)
    
    # Status tracking
    status = Column(String(50), default="open")  # open, acknowledged, in_progress, resolved, dismissed
    assigned_to = Column(String(255))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Legal and compliance impact
    client_impact_potential = Column(Boolean, default=False)
    compliance_risk = Column(String(50))  # none, low, medium, high
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class MetricDefinitionCreate(BaseModel):
    """Create metric definition request."""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    metric_type: MetricType
    category: MetricCategory
    unit: Optional[str] = Field(None, max_length=50)
    collection_interval_seconds: int = Field(default=60, ge=1, le=86400)
    retention_days: int = Field(default=90, ge=1, le=2555)
    aggregation_functions: Optional[List[str]] = None
    contains_sensitive_data: bool = False
    compliance_tags: Optional[Dict[str, Any]] = None
    data_classification: Optional[str] = None
    tags: Optional[Dict[str, str]] = None

class AlertRuleCreate(BaseModel):
    """Create alert rule request."""
    metric_definition_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: AlertSeverity
    threshold_value: float
    threshold_operator: ThresholdOperator
    evaluation_window_seconds: int = Field(default=300, ge=60, le=86400)
    consecutive_breaches: int = Field(default=1, ge=1, le=100)
    breach_percentage: float = Field(default=100.0, ge=0.0, le=100.0)
    suppress_duration_seconds: int = Field(default=3600, ge=0, le=86400)
    auto_resolve: bool = True
    resolution_timeout_seconds: int = Field(default=86400, ge=300, le=604800)
    notification_channels: Optional[List[str]] = None
    escalation_policy: Optional[Dict[str, Any]] = None
    label_filters: Optional[Dict[str, str]] = None
    business_critical: bool = False
    compliance_related: bool = False
    client_impacting: bool = False

class SLADefinitionCreate(BaseModel):
    """Create SLA definition request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    service_name: str = Field(..., min_length=1, max_length=255)
    availability_target: Optional[float] = Field(None, ge=0.0, le=100.0)
    response_time_target_ms: Optional[int] = Field(None, ge=1)
    throughput_target_rps: Optional[int] = Field(None, ge=1)
    error_rate_target: Optional[float] = Field(None, ge=0.0, le=100.0)
    measurement_window_hours: int = Field(default=24, ge=1, le=168)
    measurement_interval_seconds: int = Field(default=300, ge=60, le=3600)
    client_tier: Optional[str] = None
    contract_reference: Optional[str] = None
    business_criticality: Optional[str] = None
    regulatory_requirements: Optional[List[str]] = None
    data_residency_requirements: Optional[Dict[str, Any]] = None

class MetricSampleCreate(BaseModel):
    """Create metric sample request."""
    metric_name: str
    value: float
    timestamp: Optional[datetime] = None
    labels: Optional[Dict[str, str]] = None
    source_instance: Optional[str] = None
    source_component: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AlertUpdate(BaseModel):
    """Update alert request."""
    status: Optional[AlertStatus] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    business_impact_level: Optional[str] = None
    client_impact: Optional[bool] = None
    compliance_impact: Optional[bool] = None

# =============================================================================
# CONFIGURATION MODELS
# =============================================================================

@dataclass
class MonitoringConfiguration:
    """Monitoring system configuration."""
    metrics_retention_days: int = 90
    aggregation_intervals: List[int] = None  # [300, 3600, 86400]  # 5min, 1hr, 1day
    alert_evaluation_interval_seconds: int = 60
    max_metrics_per_request: int = 1000
    enable_distributed_tracing: bool = True
    enable_profiling: bool = False
    
    def __post_init__(self):
        if self.aggregation_intervals is None:
            self.aggregation_intervals = [300, 3600, 86400]