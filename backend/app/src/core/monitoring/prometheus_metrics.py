"""
Prometheus Metrics for Production Monitoring

Provides comprehensive application metrics for monitoring performance,
health, and business metrics in production.
"""

import time
import logging
from typing import Optional, Callable
from functools import wraps
from prometheus_client import (
    Counter, Gauge, Histogram, Summary, Info,
    generate_latest, CONTENT_TYPE_LATEST, REGISTRY
)
from prometheus_client.multiprocess import MultiProcessCollector
from prometheus_client.core import CollectorRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# HTTP METRICS
# =============================================================================

# HTTP request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# HTTP request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# HTTP request size
http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

# HTTP response size
http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Active HTTP requests
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint']
)


# =============================================================================
# DATABASE METRICS
# =============================================================================

# Database query counter
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

# Database query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Database connection pool
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Current database connection pool size'
)

db_connection_pool_overflow = Gauge(
    'db_connection_pool_overflow',
    'Current database connection pool overflow'
)

db_connection_pool_checked_out = Gauge(
    'db_connection_pool_checked_out',
    'Current number of checked out database connections'
)

# Database errors
db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['error_type']
)


# =============================================================================
# CACHE METRICS
# =============================================================================

# Cache operations
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']  # operation: get/set/delete, status: hit/miss/error
)

# Cache hit rate (calculated metric)
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Cache operation duration
cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation'],
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1)
)


# =============================================================================
# BUSINESS METRICS
# =============================================================================

# Document operations
documents_uploaded_total = Counter(
    'documents_uploaded_total',
    'Total documents uploaded',
    ['document_type']
)

documents_analyzed_total = Counter(
    'documents_analyzed_total',
    'Total documents analyzed',
    ['analysis_type']
)

# User operations
user_registrations_total = Counter(
    'user_registrations_total',
    'Total user registrations'
)

user_logins_total = Counter(
    'user_logins_total',
    'Total user logins',
    ['status']  # success/failure
)

# Search operations
searches_total = Counter(
    'searches_total',
    'Total search queries',
    ['search_type']
)

search_results_count = Histogram(
    'search_results_count',
    'Number of search results returned',
    ['search_type'],
    buckets=(0, 1, 5, 10, 25, 50, 100, 250, 500, 1000)
)

# Case operations
cases_created_total = Counter(
    'cases_created_total',
    'Total cases created',
    ['case_type']
)

cases_updated_total = Counter(
    'cases_updated_total',
    'Total cases updated'
)


# =============================================================================
# AI/ML METRICS
# =============================================================================

# AI API calls
ai_api_calls_total = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['provider', 'model', 'status']  # provider: openai/anthropic, status: success/error
)

# AI API duration
ai_api_duration_seconds = Histogram(
    'ai_api_duration_seconds',
    'AI API call duration in seconds',
    ['provider', 'model'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

# Token usage
ai_tokens_used_total = Counter(
    'ai_tokens_used_total',
    'Total AI tokens used',
    ['provider', 'model', 'token_type']  # token_type: prompt/completion
)

# AI costs
ai_cost_dollars = Counter(
    'ai_cost_dollars_total',
    'Total AI API costs in dollars',
    ['provider', 'model']
)


# =============================================================================
# BACKGROUND TASK METRICS
# =============================================================================

# Celery task metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']  # status: success/failure/retry
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600)
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Current Celery queue length',
    ['queue_name']
)


# =============================================================================
# SYSTEM METRICS
# =============================================================================

# Application info
app_info = Info(
    'app_info',
    'Application information'
)

# Uptime
app_uptime_seconds = Gauge(
    'app_uptime_seconds',
    'Application uptime in seconds'
)

# Active users
active_users = Gauge(
    'active_users_total',
    'Current number of active users'
)

# Memory usage
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Current memory usage in bytes'
)


# =============================================================================
# ERROR TRACKING
# =============================================================================

# Application errors
app_errors_total = Counter(
    'app_errors_total',
    'Total application errors',
    ['error_type', 'severity']  # severity: warning/error/critical
)

# Rate limit hits
rate_limit_hits_total = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint', 'user_tier']
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def track_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Track HTTP request metrics"""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_db_query(operation: str, table: str, duration: float):
    """Track database query metrics"""
    db_queries_total.labels(
        operation=operation,
        table=table
    ).inc()

    db_query_duration_seconds.labels(
        operation=operation,
        table=table
    ).observe(duration)


def track_cache_operation(operation: str, status: str, duration: float, cache_type: str = "redis"):
    """Track cache operation metrics"""
    cache_operations_total.labels(
        operation=operation,
        status=status
    ).inc()

    cache_operation_duration_seconds.labels(
        operation=operation
    ).observe(duration)

    if status == "hit":
        cache_hits.labels(cache_type=cache_type).inc()
    elif status == "miss":
        cache_misses.labels(cache_type=cache_type).inc()


def track_ai_api_call(provider: str, model: str, status: str, duration: float,
                      prompt_tokens: int = 0, completion_tokens: int = 0, cost: float = 0):
    """Track AI API call metrics"""
    ai_api_calls_total.labels(
        provider=provider,
        model=model,
        status=status
    ).inc()

    ai_api_duration_seconds.labels(
        provider=provider,
        model=model
    ).observe(duration)

    if prompt_tokens > 0:
        ai_tokens_used_total.labels(
            provider=provider,
            model=model,
            token_type="prompt"
        ).inc(prompt_tokens)

    if completion_tokens > 0:
        ai_tokens_used_total.labels(
            provider=provider,
            model=model,
            token_type="completion"
        ).inc(completion_tokens)

    if cost > 0:
        ai_cost_dollars.labels(
            provider=provider,
            model=model
        ).inc(cost)


def update_db_pool_metrics(pool):
    """Update database connection pool metrics"""
    try:
        db_connection_pool_size.set(pool.size())
        db_connection_pool_overflow.set(pool.overflow())
        db_connection_pool_checked_out.set(pool.checkedout())
    except Exception as e:
        logger.error(f"Error updating DB pool metrics: {e}")


def update_celery_queue_metrics(queue_name: str, length: int):
    """Update Celery queue length metrics"""
    celery_queue_length.labels(queue_name=queue_name).set(length)


# =============================================================================
# DECORATORS
# =============================================================================

def track_time(metric_name: str = None, labels: dict = None):
    """
    Decorator to track execution time of a function.

    Args:
        metric_name: Name of the metric histogram (defaults to function name)
        labels: Dictionary of labels for the metric

    Example:
        @track_time(metric_name="document_processing", labels={"type": "pdf"})
        def process_document(doc):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time

                # Use custom metric name or function name
                name = metric_name or f"{func.__module__}_{func.__name__}_duration_seconds"

                # Create or get histogram
                histogram = Histogram(
                    name,
                    f'Duration of {func.__name__} in seconds',
                    list(labels.keys()) if labels else []
                )

                # Observe duration
                if labels:
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)

        return wrapper
    return decorator


def count_calls(counter_name: str = None, labels: dict = None):
    """
    Decorator to count function calls.

    Args:
        counter_name: Name of the counter metric (defaults to function name)
        labels: Dictionary of labels for the metric

    Example:
        @count_calls(counter_name="user_actions", labels={"action": "login"})
        def user_login(username):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use custom counter name or function name
            name = counter_name or f"{func.__module__}_{func.__name__}_total"

            # Create or get counter
            counter = Counter(
                name,
                f'Total calls to {func.__name__}',
                list(labels.keys()) if labels else []
            )

            # Increment counter
            if labels:
                counter.labels(**labels).inc()
            else:
                counter.inc()

            return func(*args, **kwargs)

        return wrapper
    return decorator


# =============================================================================
# METRICS COLLECTION
# =============================================================================

def get_metrics():
    """Get all metrics in Prometheus format"""
    return generate_latest(REGISTRY)


def get_metrics_content_type():
    """Get content type for metrics endpoint"""
    return CONTENT_TYPE_LATEST


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_metrics(app_name: str, version: str, environment: str):
    """Initialize application metrics with metadata"""
    app_info.info({
        'app_name': app_name,
        'version': version,
        'environment': environment
    })

    logger.info(f"Prometheus metrics initialized for {app_name} v{version} ({environment})")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # HTTP metrics
    'http_requests_total',
    'http_request_duration_seconds',
    'http_requests_in_progress',
    'track_http_request',

    # Database metrics
    'db_queries_total',
    'db_query_duration_seconds',
    'update_db_pool_metrics',
    'track_db_query',

    # Cache metrics
    'cache_operations_total',
    'cache_hits',
    'cache_misses',
    'track_cache_operation',

    # Business metrics
    'documents_uploaded_total',
    'documents_analyzed_total',
    'user_registrations_total',
    'user_logins_total',
    'searches_total',
    'cases_created_total',

    # AI metrics
    'ai_api_calls_total',
    'ai_api_duration_seconds',
    'ai_tokens_used_total',
    'ai_cost_dollars',
    'track_ai_api_call',

    # Background task metrics
    'celery_tasks_total',
    'celery_task_duration_seconds',
    'celery_queue_length',
    'update_celery_queue_metrics',

    # System metrics
    'app_info',
    'app_uptime_seconds',
    'active_users',
    'memory_usage_bytes',

    # Error tracking
    'app_errors_total',
    'rate_limit_hits_total',

    # Decorators
    'track_time',
    'count_calls',

    # Collection
    'get_metrics',
    'get_metrics_content_type',
    'initialize_metrics',
]
