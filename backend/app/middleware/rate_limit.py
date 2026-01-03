"""
Rate Limiting Middleware

Provides basic rate limiting protection against abuse.
Uses in-memory storage for development, Redis for production.
"""

import os
import time
import logging
from typing import Callable, Dict, Tuple
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')


class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development"""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_id: str, limit: int, window: int) -> Tuple[bool, int]:
        """
        Check if request is allowed within rate limit

        Args:
            client_id: Unique identifier for client (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (allowed: bool, current_count: int)
        """
        now = time.time()
        cutoff = now - window

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]

        current_count = len(self.requests[client_id])

        if current_count >= limit:
            return False, current_count

        # Add current request
        self.requests[client_id].append(now)
        return True, current_count + 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware

    Default limits:
    - General API: 100 requests per minute
    - High-traffic endpoints: 300 requests per minute
    - Authentication: 10 requests per minute
    """

    def __init__(
        self,
        app,
        default_limit: int = 100,
        default_window: int = 60,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.limiter = InMemoryRateLimiter()
        self.default_limit = default_limit
        self.default_window = default_window
        self.exclude_paths = exclude_paths or [
            '/health',
            '/metrics',
            '/favicon.ico',
            '/api/v1/monitoring/',  # Exclude monitoring endpoints (internal use)
            '/admin/backend-monitor',  # Exclude admin dashboard
            '/docs',  # Exclude API docs
            '/openapi.json',
            '/redoc'
        ]

        # Endpoint-specific limits
        self.endpoint_limits = {
            '/api/v1/documents/': (300, 60),  # 300 per minute for document uploads (increased)
            '/api/v1/qa/': (200, 60),  # 200 per minute for Q&A
            '/api/v1/defense/': (100, 60),  # 100 per minute for defense
            '/api/v1/batch/': (50, 60),  # 50 per minute for batch operations
            '/auth/': (10, 60),  # 10 per minute for auth endpoints
        }

        logger.info(f"RateLimitMiddleware initialized - Default: {default_limit}/{default_window}s")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to request"""

        # ALWAYS allow OPTIONS requests (CORS preflight) - never rate limit these
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get client identifier (IP address or user ID if authenticated)
        client_id = self._get_client_identifier(request)

        # Get rate limits for this endpoint
        limit, window = self._get_rate_limits(request.url.path)

        # Check rate limit
        allowed, current_count = self.limiter.is_allowed(client_id, limit, window)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path}: "
                f"{current_count}/{limit} in {window}s"
            )

            # Return 429 Too Many Requests
            return Response(
                content=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(time.time()) + window),
                    'Retry-After': str(window)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(max(0, limit - current_count))
        response.headers['X-RateLimit-Reset'] = str(int(time.time()) + window)

        return response

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for client"""

        # Use user ID if authenticated
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"

        # Default fallback
        return "unknown"

    def _get_rate_limits(self, path: str) -> Tuple[int, int]:
        """Get rate limit and window for specific path"""

        # Check for endpoint-specific limits
        for endpoint, (limit, window) in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limit, window

        # Return default limits
        return self.default_limit, self.default_window
