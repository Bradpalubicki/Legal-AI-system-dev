"""
API Rate Limiting Middleware

Implements rate limiting to protect against abuse and ensure fair resource usage.
Uses Redis for distributed rate limiting across multiple instances.
"""

import time
import logging
from typing import Optional, Callable, Dict, Any
from functools import wraps
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..cache.redis_cache import get_redis_client

logger = logging.getLogger(__name__)


# =============================================================================
# RATE LIMIT CONFIGURATIONS
# =============================================================================

class RateLimitConfig:
    """Rate limit configurations for different tiers"""

    # Anonymous/public API (no authentication)
    ANONYMOUS = {
        "requests": 60,      # Max requests
        "window": 60,        # Time window in seconds (1 minute)
        "message": "Rate limit exceeded. Please try again later."
    }

    # Authenticated users
    AUTHENTICATED = {
        "requests": 300,     # 300 requests
        "window": 60,        # per minute
        "message": "Rate limit exceeded. Please wait before making more requests."
    }

    # Premium/paid users
    PREMIUM = {
        "requests": 1000,    # 1000 requests
        "window": 60,        # per minute
        "message": "Rate limit exceeded. Contact support for higher limits."
    }

    # Admin users (very high limit)
    ADMIN = {
        "requests": 10000,   # 10000 requests
        "window": 60,        # per minute
        "message": "Admin rate limit exceeded."
    }

    # Specific endpoint limits
    EXPENSIVE_OPERATIONS = {
        "requests": 10,      # 10 requests
        "window": 60,        # per minute
        "message": "This operation is rate limited. Please wait before retrying."
    }

    # Document upload limits
    UPLOAD = {
        "requests": 20,      # 20 uploads
        "window": 3600,      # per hour
        "message": "Upload limit exceeded. Please wait before uploading more files."
    }

    # Search API limits
    SEARCH = {
        "requests": 100,     # 100 searches
        "window": 60,        # per minute
        "message": "Search rate limit exceeded. Please wait before searching again."
    }


# =============================================================================
# RATE LIMITER SERVICE
# =============================================================================

class RateLimiter:
    """
    Redis-based rate limiter using token bucket algorithm.

    Features:
    - Distributed rate limiting across multiple instances
    - Configurable per-user, per-IP, or per-endpoint
    - Graceful fallback if Redis is unavailable
    """

    def __init__(self):
        self.redis = get_redis_client()

    def is_available(self) -> bool:
        """Check if rate limiting is available (Redis must be working)"""
        if not self.redis:
            return False

        try:
            self.redis.ping()
            return True
        except Exception:
            return False

    def _make_key(self, identifier: str, endpoint: Optional[str] = None) -> str:
        """Generate rate limit key"""
        if endpoint:
            return f"ratelimit:{identifier}:{endpoint}"
        return f"ratelimit:{identifier}"

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        endpoint: Optional[str] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit.

        Args:
            identifier: User ID, IP address, or other identifier
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            endpoint: Optional endpoint-specific limiting

        Returns:
            Tuple of (is_allowed: bool, info: dict)
            info contains: remaining, reset_time, total
        """
        if not self.is_available():
            # Fallback: allow request if Redis is down
            logger.warning("Rate limiter unavailable - allowing request")
            return True, {
                "remaining": max_requests,
                "reset_time": int(time.time()) + window_seconds,
                "total": max_requests
            }

        try:
            key = self._make_key(identifier, endpoint)
            current_time = int(time.time())

            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Get current count
            pipe.get(key)

            # Execute pipeline
            results = pipe.execute()
            current_count = int(results[0]) if results[0] else 0

            # Check if limit exceeded
            if current_count >= max_requests:
                # Get TTL to know when limit resets
                ttl = self.redis.ttl(key)
                reset_time = current_time + ttl if ttl > 0 else current_time + window_seconds

                return False, {
                    "remaining": 0,
                    "reset_time": reset_time,
                    "total": max_requests
                }

            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(key)

            # Set expiry on first request
            if current_count == 0:
                pipe.expire(key, window_seconds)

            pipe.execute()

            # Calculate remaining
            remaining = max_requests - current_count - 1

            # Get accurate reset time
            ttl = self.redis.ttl(key)
            reset_time = current_time + ttl if ttl > 0 else current_time + window_seconds

            return True, {
                "remaining": remaining,
                "reset_time": reset_time,
                "total": max_requests
            }

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fallback: allow request on error
            return True, {
                "remaining": max_requests,
                "reset_time": int(time.time()) + window_seconds,
                "total": max_requests
            }

    def reset_limit(self, identifier: str, endpoint: Optional[str] = None) -> bool:
        """Reset rate limit for identifier"""
        if not self.is_available():
            return False

        try:
            key = self._make_key(identifier, endpoint)
            self.redis.delete(key)
            return True

        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")
            return False

    def get_remaining(
        self,
        identifier: str,
        max_requests: int,
        endpoint: Optional[str] = None
    ) -> int:
        """Get remaining requests for identifier"""
        if not self.is_available():
            return max_requests

        try:
            key = self._make_key(identifier, endpoint)
            current_count = int(self.redis.get(key) or 0)
            return max(0, max_requests - current_count)

        except Exception as e:
            logger.error(f"Get remaining error: {e}")
            return max_requests


# Global rate limiter instance
rate_limiter = RateLimiter()


# =============================================================================
# MIDDLEWARE
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for API-wide rate limiting.

    Applies rate limits based on:
    1. User authentication status and role
    2. IP address for anonymous requests
    3. Specific endpoint configurations
    """

    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get identifier (user ID or IP)
        identifier = self._get_identifier(request)

        # Get rate limit config based on user
        config = self._get_rate_limit_config(request)

        # Check rate limit
        is_allowed, info = self.rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=config["requests"],
            window_seconds=config["window"],
            endpoint=self._get_endpoint_key(request)
        )

        # Add rate limit headers to response
        async def add_rate_limit_headers(response):
            response.headers["X-RateLimit-Limit"] = str(info["total"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset_time"])
            return response

        # If rate limit exceeded
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} on {request.url.path}"
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": config["message"],
                    "rate_limit": {
                        "limit": info["total"],
                        "remaining": 0,
                        "reset": info["reset_time"]
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(info["total"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset_time"]),
                    "Retry-After": str(info["reset_time"] - int(time.time()))
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response = await add_rate_limit_headers(response)

        return response

    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""

        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id', 'unknown')}"

        # Fallback to IP address
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _get_rate_limit_config(self, request: Request) -> Dict[str, Any]:
        """Get rate limit configuration based on user role"""

        # Check if user is authenticated
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user

            # Admin users get highest limits
            if user.get("role") == "admin" or user.get("is_admin"):
                return RateLimitConfig.ADMIN

            # Premium users get higher limits
            if user.get("is_premium"):
                return RateLimitConfig.PREMIUM

            # Regular authenticated users
            return RateLimitConfig.AUTHENTICATED

        # Anonymous/unauthenticated users get lowest limits
        return RateLimitConfig.ANONYMOUS

    def _get_endpoint_key(self, request: Request) -> Optional[str]:
        """Get endpoint-specific rate limit key"""

        path = request.url.path

        # Expensive operations
        if "/analyze" in path or "/process" in path:
            return "expensive"

        # Upload endpoints
        if "/upload" in path or path.endswith("/documents"):
            return "upload"

        # Search endpoints
        if "/search" in path:
            return "search"

        # Default: no endpoint-specific limiting
        return None


# =============================================================================
# DECORATOR FOR ENDPOINT-SPECIFIC RATE LIMITING
# =============================================================================

def rate_limit(requests: int, window: int, message: Optional[str] = None):
    """
    Decorator for endpoint-specific rate limiting.

    Args:
        requests: Maximum requests allowed
        window: Time window in seconds
        message: Custom error message

    Example:
        @router.post("/expensive-operation")
        @rate_limit(requests=10, window=60)
        async def expensive_operation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # If no request found, execute function without rate limiting
                logger.warning("No request found in rate_limit decorator")
                return await func(*args, **kwargs)

            # Get identifier
            identifier = _get_request_identifier(request)

            # Check rate limit
            is_allowed, info = rate_limiter.check_rate_limit(
                identifier=identifier,
                max_requests=requests,
                window_seconds=window,
                endpoint=func.__name__
            )

            if not is_allowed:
                error_message = message or "Rate limit exceeded for this operation."

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=error_message,
                    headers={
                        "X-RateLimit-Limit": str(info["total"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(info["reset_time"]),
                        "Retry-After": str(info["reset_time"] - int(time.time()))
                    }
                )

            # Execute function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def _get_request_identifier(request: Request) -> str:
    """Helper to get identifier from request"""
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.get('id', 'unknown')}"

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"ip:{ip}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'RateLimiter',
    'RateLimitMiddleware',
    'RateLimitConfig',
    'rate_limiter',
    'rate_limit',
]
