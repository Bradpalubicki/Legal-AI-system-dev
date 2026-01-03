# =============================================================================
# Legal AI System - Application Metrics Instrumentation
# =============================================================================
# Comprehensive metrics collection for monitoring legal document processing,
# AI services, compliance, and system performance
# =============================================================================

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    Enum,
    generate_latest,
    CONTENT_TYPE_LATEST,
    multiprocess,
    CollectorRegistry
)
from typing import Dict, List, Optional, Any
import time
import functools
import logging
from contextlib import contextmanager

# =============================================================================
# CORE METRICS
# =============================================================================

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# =============================================================================
# LEGAL AI SPECIFIC METRICS
# =============================================================================

# Document Processing Metrics
document_processing_total = Counter(
    'document_processing_total',
    'Total documents processed',
    ['document_type', 'status']
)

document_processing_errors_total = Counter(
    'document_processing_errors_total',
    'Total document processing errors',
    ['document_type', 'error_type']
)

document_processing_duration_seconds = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['document_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
)

# AI Service Metrics
ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'AI service request duration in seconds',
    ['provider', 'model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

ai_api_rate_limit_errors_total = Counter(
    'ai_api_rate_limit_errors_total',
    'AI API rate limit errors',
    ['provider']
)

ai_token_usage_total = Counter(
    'ai_token_usage_total',
    'Total AI tokens consumed',
    ['provider', 'model', 'type']  # type: prompt, completion
)

# Citation Processing Metrics
citation_validation_errors_total = Counter(
    'citation_validation_errors_total',
    'Citation validation errors',
    ['citation_type', 'error_reason']
)

citation_processing_total = Counter(
    'citation_processing_total',
    'Total citations processed',
    ['citation_type', 'status']
)

# =============================================================================
# COMPLIANCE AND AUDIT METRICS
# =============================================================================

# Audit Logging Metrics
audit_log_entries_total = Counter(
    'audit_log_entries_total',
    'Total audit log entries',
    ['action', 'user_role', 'resource_type']
)

audit_log_errors_total = Counter(
    'audit_log_errors_total',
    'Audit logging errors',
    ['error_type']
)

# Data Retention Metrics
data_retention_overdue_records = Gauge(
    'data_retention_overdue_records',
    'Number of records overdue for retention policy',
    ['data_type']
)

data_retention_compliant_records = Gauge(
    'data_retention_compliant_records',
    'Number of records compliant with retention policy',
    ['data_type']
)

# Authentication and Security Metrics
auth_failures_total = Counter(
    'auth_failures_total',
    'Authentication failures',
    ['failure_reason', 'client_ip']
)

privileged_operations_total = Counter(
    'privileged_operations_total',
    'Privileged operations performed',
    ['operation_type', 'user_id']
)

# Client Data Access Metrics
client_data_access_total = Counter(
    'client_data_access_total',
    'Client data access events',
    ['access_type', 'data_classification']
)

client_data_export_total = Counter(
    'client_data_export_total',
    'Client data export events',
    ['export_format', 'user_role']
)

# =============================================================================
# EXTERNAL SERVICE METRICS
# =============================================================================

# Legal Research API Metrics
legal_research_api_errors_total = Counter(
    'legal_research_api_errors_total',
    'Legal research API errors',
    ['provider', 'error_type']
)

legal_research_requests_total = Counter(
    'legal_research_requests_total',
    'Legal research API requests',
    ['provider', 'query_type']
)

# Email Service Metrics
email_send_errors_total = Counter(
    'email_send_errors_total',
    'Email sending errors',
    ['smtp_server', 'error_type']
)

email_sent_total = Counter(
    'email_sent_total',
    'Total emails sent',
    ['email_type', 'recipient_type']
)

# =============================================================================
# BACKGROUND TASK METRICS (CELERY)
# =============================================================================

celery_task_total = Counter(
    'celery_task_total',
    'Total Celery tasks processed',
    ['task_name', 'status']
)

celery_task_failure_total = Counter(
    'celery_task_failure_total',
    'Celery task failures',
    ['task_name', 'failure_reason']
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue',
    ['queue_name']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task execution duration',
    ['task_name'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
)

# =============================================================================
# BUSINESS METRICS
# =============================================================================

# Legal Workflow Metrics
legal_workflow_total = Counter(
    'legal_workflow_total',
    'Legal workflows processed',
    ['workflow_type', 'client_type']
)

legal_workflow_compliant_total = Counter(
    'legal_workflow_compliant_total',
    'Compliant legal workflows',
    ['workflow_type', 'compliance_standard']
)

# Active Users and Sessions
active_users_gauge = Gauge(
    'active_users_current',
    'Currently active users',
    ['user_type']
)

active_sessions_gauge = Gauge(
    'active_sessions_current',
    'Currently active sessions'
)

# System Health Metrics
system_health_status = Enum(
    'system_health_status',
    'Overall system health status',
    states=['healthy', 'degraded', 'unhealthy']
)

# =============================================================================
# INSTRUMENTATION DECORATORS
# =============================================================================

def track_request_metrics(endpoint: str = None, method: str = None):
    """Decorator to track HTTP request metrics."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "200"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "500"
                logging.error(f"Request failed: {e}")
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method or "GET",
                    endpoint=endpoint or func.__name__,
                    status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method or "GET",
                    endpoint=endpoint or func.__name__
                ).observe(duration)
        return wrapper
    return decorator

def track_document_processing(document_type: str = "unknown"):
    """Decorator to track document processing metrics."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                document_processing_errors_total.labels(
                    document_type=document_type,
                    error_type=type(e).__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                document_processing_total.labels(
                    document_type=document_type,
                    status=status
                ).inc()
                document_processing_duration_seconds.labels(
                    document_type=document_type
                ).observe(duration)
        return wrapper
    return decorator

def track_ai_request(provider: str, model: str = "unknown"):
    """Decorator to track AI service request metrics."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                ai_request_duration_seconds.labels(
                    provider=provider,
                    model=model
                ).observe(duration)
        return wrapper
    return decorator

# =============================================================================
# CONTEXT MANAGERS FOR METRICS
# =============================================================================

@contextmanager
def track_audit_log(action: str, user_role: str, resource_type: str):
    """Context manager to track audit log entries."""
    try:
        yield
        audit_log_entries_total.labels(
            action=action,
            user_role=user_role,
            resource_type=resource_type
        ).inc()
    except Exception as e:
        audit_log_errors_total.labels(
            error_type=type(e).__name__
        ).inc()
        raise

@contextmanager
def track_celery_task(task_name: str, queue_name: str = "default"):
    """Context manager to track Celery task metrics."""
    start_time = time.time()
    status = "success"
    
    try:
        yield
    except Exception as e:
        status = "failure"
        celery_task_failure_total.labels(
            task_name=task_name,
            failure_reason=type(e).__name__
        ).inc()
        raise
    finally:
        duration = time.time() - start_time
        celery_task_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        celery_task_duration_seconds.labels(
            task_name=task_name
        ).observe(duration)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def increment_counter(counter, labels: Dict[str, str] = None, value: float = 1):
    """Helper function to increment a counter with labels."""
    if labels:
        counter.labels(**labels).inc(value)
    else:
        counter.inc(value)

def set_gauge(gauge, value: float, labels: Dict[str, str] = None):
    """Helper function to set a gauge value with labels."""
    if labels:
        gauge.labels(**labels).set(value)
    else:
        gauge.set(value)

def observe_histogram(histogram, value: float, labels: Dict[str, str] = None):
    """Helper function to observe a histogram value with labels."""
    if labels:
        histogram.labels(**labels).observe(value)
    else:
        histogram.observe(value)

# =============================================================================
# METRICS COLLECTION AND EXPORT
# =============================================================================

def get_metrics_registry() -> CollectorRegistry:
    """Get the metrics registry for multi-process environments."""
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry
    else:
        return None

def generate_metrics_response():
    """Generate Prometheus metrics response."""
    registry = get_metrics_registry()
    if registry:
        return generate_latest(registry), CONTENT_TYPE_LATEST
    else:
        return generate_latest(), CONTENT_TYPE_LATEST

# =============================================================================
# COMPLIANCE HELPERS
# =============================================================================

def record_client_data_access(access_type: str, data_classification: str, user_id: str):
    """Record client data access for compliance tracking."""
    client_data_access_total.labels(
        access_type=access_type,
        data_classification=data_classification
    ).inc()
    
    # Also create audit log entry
    audit_log_entries_total.labels(
        action="data_access",
        user_role="user",  # This should be determined from user context
        resource_type="client_data"
    ).inc()

def record_privileged_operation(operation_type: str, user_id: str):
    """Record privileged operations for security monitoring."""
    privileged_operations_total.labels(
        operation_type=operation_type,
        user_id=user_id
    ).inc()
    
    # Also create audit log entry
    audit_log_entries_total.labels(
        action="privileged_operation",
        user_role="admin",  # This should be determined from user context
        resource_type="system"
    ).inc()

def update_data_retention_metrics(data_type: str, compliant_count: int, overdue_count: int):
    """Update data retention compliance metrics."""
    data_retention_compliant_records.labels(data_type=data_type).set(compliant_count)
    data_retention_overdue_records.labels(data_type=data_type).set(overdue_count)

def record_ai_token_usage(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    """Record AI token usage for cost tracking and monitoring."""
    ai_token_usage_total.labels(
        provider=provider,
        model=model,
        type="prompt"
    ).inc(prompt_tokens)
    
    ai_token_usage_total.labels(
        provider=provider,
        model=model,
        type="completion"
    ).inc(completion_tokens)

# =============================================================================
# INITIALIZATION
# =============================================================================

import os

def init_metrics():
    """Initialize metrics collection."""
    logging.info("Initializing Legal AI System metrics collection")
    
    # Set initial system health status
    system_health_status.state('healthy')
    
    # Initialize some baseline gauges
    active_users_gauge.labels(user_type="client").set(0)
    active_users_gauge.labels(user_type="attorney").set(0)
    active_users_gauge.labels(user_type="admin").set(0)
    active_sessions_gauge.set(0)
    
    logging.info("Legal AI System metrics collection initialized")

# Initialize metrics on import
init_metrics()