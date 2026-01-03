"""
Monitoring Module

Provides Prometheus metrics, health checks, and monitoring middleware
for production deployments.
"""

from .prometheus_metrics import (
    # HTTP metrics
    http_requests_total,
    http_request_duration_seconds,
    track_http_request,

    # Database metrics
    db_queries_total,
    db_query_duration_seconds,
    track_db_query,
    update_db_pool_metrics,

    # Cache metrics
    cache_operations_total,
    cache_hits,
    cache_misses,
    track_cache_operation,

    # Business metrics
    documents_uploaded_total,
    documents_analyzed_total,
    user_registrations_total,
    user_logins_total,
    searches_total,
    cases_created_total,

    # AI metrics
    ai_api_calls_total,
    ai_api_duration_seconds,
    ai_tokens_used_total,
    ai_cost_dollars,
    track_ai_api_call,

    # Background task metrics
    celery_tasks_total,
    celery_task_duration_seconds,
    update_celery_queue_metrics,

    # System metrics
    app_info,
    app_uptime_seconds,
    active_users,
    app_errors_total,
    rate_limit_hits_total,

    # Decorators
    track_time,
    count_calls,

    # Collection
    get_metrics,
    get_metrics_content_type,
    initialize_metrics,
)

from .middleware import (
    PrometheusMiddleware,
    PerformanceMonitoringMiddleware,
    DatabaseMonitoringMiddleware,
    get_system_health,
)

__all__ = [
    # Middleware
    'PrometheusMiddleware',
    'PerformanceMonitoringMiddleware',
    'DatabaseMonitoringMiddleware',

    # Tracking functions
    'track_http_request',
    'track_db_query',
    'track_cache_operation',
    'track_ai_api_call',
    'update_db_pool_metrics',
    'update_celery_queue_metrics',

    # Business metrics
    'documents_uploaded_total',
    'documents_analyzed_total',
    'user_registrations_total',
    'user_logins_total',
    'searches_total',
    'cases_created_total',

    # AI metrics
    'ai_api_calls_total',
    'ai_tokens_used_total',
    'ai_cost_dollars',

    # System
    'app_errors_total',
    'rate_limit_hits_total',
    'active_users',

    # Decorators
    'track_time',
    'count_calls',

    # Utilities
    'get_metrics',
    'get_metrics_content_type',
    'initialize_metrics',
    'get_system_health',
]
