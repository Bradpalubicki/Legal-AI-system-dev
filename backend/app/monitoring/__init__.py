# =============================================================================
# Legal AI System - Monitoring Module
# =============================================================================
# Comprehensive monitoring system for legal document processing with
# metrics collection, alerting, analytics, SLA monitoring, dashboards,
# distributed tracing, and capacity planning
# =============================================================================

from .metrics import (
    # Core metrics
    http_requests_total,
    http_request_duration_seconds,
    
    # Document processing metrics
    document_processing_total,
    document_processing_errors_total,
    document_processing_duration_seconds,
    
    # AI service metrics
    ai_request_duration_seconds,
    ai_api_rate_limit_errors_total,
    ai_token_usage_total,
    
    # Compliance metrics
    audit_log_entries_total,
    audit_log_errors_total,
    data_retention_overdue_records,
    data_retention_compliant_records,
    
    # Security metrics
    auth_failures_total,
    privileged_operations_total,
    client_data_access_total,
    client_data_export_total,
    
    # Decorators and utilities
    track_request_metrics,
    track_document_processing,
    track_ai_request,
    track_audit_log,
    track_celery_task,
    
    # Helper functions
    increment_counter,
    set_gauge,
    observe_histogram,
    generate_metrics_response,
    
    # Compliance helpers
    record_client_data_access,
    record_privileged_operation,
    update_data_retention_metrics,
    record_ai_token_usage,
    
    # Initialization
    init_metrics
)

# Import monitoring system components
from .models import *
# from .analytics import PerformanceAnalytics, TrendAnalysis, AnomalyDetectionResult
# from .alerting import AlertingEngine, EscalationEngine, AlertCorrelationEngine
from .sla import SLAEngine, LegalComplianceSLATracker
from .dashboards import DashboardEngine, DashboardType, WidgetType, websocket_manager
from .tracing import (
    get_tracer, trace_operation, async_trace_operation, trace_function,
    document_tracer, ai_tracer, compliance_tracer, TraceAnalyzer
)
from .capacity import (
    CapacityPlanningEngine, LegalWorkloadAnalyzer, ResourceType, 
    CapacityRecommendation, ForecastResult
)

__all__ = [
    # Core Metrics
    'http_requests_total',
    'http_request_duration_seconds',
    'document_processing_total',
    'document_processing_errors_total',
    'document_processing_duration_seconds',
    'ai_request_duration_seconds',
    'ai_api_rate_limit_errors_total',
    'ai_token_usage_total',
    'audit_log_entries_total',
    'audit_log_errors_total',
    'data_retention_overdue_records',
    'data_retention_compliant_records',
    'auth_failures_total',
    'privileged_operations_total',
    'client_data_access_total',
    'client_data_export_total',
    
    # Metric Decorators and Utilities
    'track_request_metrics',
    'track_document_processing',
    'track_ai_request',
    'track_audit_log',
    'track_celery_task',
    'increment_counter',
    'set_gauge',
    'observe_histogram',
    'generate_metrics_response',
    'record_client_data_access',
    'record_privileged_operation',
    'update_data_retention_metrics',
    'record_ai_token_usage',
    'init_metrics',
    
    # Analytics
    'PerformanceAnalytics',
    'TrendAnalysis',
    'AnomalyDetectionResult',
    
    # Alerting
    'AlertingEngine',
    'EscalationEngine',
    'AlertCorrelationEngine',
    
    # SLA Monitoring
    'SLAEngine',
    'LegalComplianceSLATracker',
    
    # Dashboards
    'DashboardEngine',
    'DashboardType',
    'WidgetType',
    'websocket_manager',
    
    # Tracing
    'get_tracer',
    'trace_operation',
    'async_trace_operation',
    'trace_function',
    'document_tracer',
    'ai_tracer',
    'compliance_tracer',
    'TraceAnalyzer',
    
    # Capacity Planning
    'CapacityPlanningEngine',
    'LegalWorkloadAnalyzer',
    'ResourceType',
    'CapacityRecommendation',
    'ForecastResult'
]