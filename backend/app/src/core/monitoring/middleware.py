"""
Monitoring Middleware

Automatically tracks HTTP requests, response times, and errors.
Integrates with Prometheus metrics for production monitoring.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .prometheus_metrics import (
    track_http_request,
    http_requests_in_progress,
    http_request_size_bytes,
    http_response_size_bytes,
    app_errors_total,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PROMETHEUS MONITORING MIDDLEWARE
# =============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP metrics for Prometheus.

    Automatically tracks:
    - Request count by method, endpoint, and status code
    - Request duration
    - Requests in progress
    - Request/response sizes
    - Error rates
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with monitoring"""

        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Get endpoint pattern (remove path params for cleaner metrics)
        endpoint = self._get_endpoint_pattern(request)
        method = request.method

        # Track request size
        if request.headers.get("content-length"):
            try:
                size = int(request.headers["content-length"])
                http_request_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(size)
            except (ValueError, TypeError):
                pass

        # Track requests in progress
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).inc()

        # Start timing
        start_time = time.time()
        status_code = 500  # Default to error if something goes wrong

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Track response size
            if hasattr(response, "headers") and response.headers.get("content-length"):
                try:
                    size = int(response.headers["content-length"])
                    http_response_size_bytes.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(size)
                except (ValueError, TypeError):
                    pass

            return response

        except Exception as e:
            # Track errors
            app_errors_total.labels(
                error_type=type(e).__name__,
                severity="error"
            ).inc()

            logger.error(f"Error processing request {method} {endpoint}: {e}")
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Track metrics
            track_http_request(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration
            )

            # Decrement in-progress counter
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()

            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {method} {endpoint} took {duration:.2f}s (status: {status_code})"
                )

    def _get_endpoint_pattern(self, request: Request) -> str:
        """
        Get endpoint pattern without specific IDs.

        Converts:
            /api/documents/123 -> /api/documents/{id}
            /api/users/abc-def -> /api/users/{id}
        """
        path = request.url.path

        # Use route path if available (from FastAPI routing)
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope.get("route")
            if route and hasattr(route, "path"):
                return route.path

        # Fallback: simple pattern matching
        # Replace UUIDs and numeric IDs with {id}
        import re

        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )

        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)

        # Replace long alphanumeric strings (likely IDs)
        path = re.sub(r'/[a-zA-Z0-9_-]{20,}', '/{id}', path)

        return path


# =============================================================================
# PERFORMANCE MONITORING MIDDLEWARE
# =============================================================================

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detailed performance monitoring.

    Adds performance headers to responses:
    - X-Process-Time: Server processing time
    - X-Request-ID: Unique request identifier
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring"""

        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())

        # Add request ID to request state
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add headers
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Request-ID"] = request_id

        return response


# =============================================================================
# DATABASE MONITORING MIDDLEWARE
# =============================================================================

class DatabaseMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track database connection pool metrics.

    Updates pool metrics on every request to monitor:
    - Pool size
    - Connections in use
    - Pool overflow
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with DB monitoring"""

        # Update DB pool metrics before processing
        try:
            from ...database import engine
            from .prometheus_metrics import update_db_pool_metrics

            if hasattr(engine, 'pool'):
                update_db_pool_metrics(engine.pool)

        except Exception as e:
            logger.debug(f"Could not update DB pool metrics: {e}")

        # Process request
        response = await call_next(request)

        return response


# =============================================================================
# HEALTH CHECK HELPERS
# =============================================================================

def get_system_health() -> dict:
    """
    Get comprehensive system health information.

    Returns:
        Dictionary with health status of all components
    """
    import psutil
    import sys

    health = {
        "status": "healthy",
        "components": {},
        "system": {}
    }

    # Check database
    try:
        from ...database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health["status"] = "degraded"

    # Check Redis cache
    try:
        from ...cache import cache
        if cache.is_available():
            health["components"]["cache"] = {"status": "healthy"}
        else:
            health["components"]["cache"] = {"status": "unavailable"}
            # Cache is optional, so don't mark as unhealthy
    except Exception as e:
        health["components"]["cache"] = {
            "status": "error",
            "error": str(e)
        }

    # Check rate limiter
    try:
        from ..middleware.rate_limiter import rate_limiter
        if rate_limiter.is_available():
            health["components"]["rate_limiter"] = {"status": "healthy"}
        else:
            health["components"]["rate_limiter"] = {"status": "unavailable"}
    except Exception as e:
        health["components"]["rate_limiter"] = {
            "status": "error",
            "error": str(e)
        }

    # System metrics
    try:
        health["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "python_version": sys.version,
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")

    return health


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'PrometheusMiddleware',
    'PerformanceMonitoringMiddleware',
    'DatabaseMonitoringMiddleware',
    'get_system_health',
]
