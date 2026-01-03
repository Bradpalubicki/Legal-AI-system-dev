import time
import logging
import uuid
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse
import redis.asyncio as redis
from contextlib import asynccontextmanager
import json

from .config import settings
from .exceptions import RateLimitError, AuthenticationError


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("legal_ai.middleware")
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        start_time = time.time()
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            self.logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "client_ip": client_ip
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": round(process_time, 4),
                    "client_ip": client_ip,
                    "exception": str(exc)
                },
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        if settings.SECURE_HEADERS:
            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            
            # HSTS header for HTTPS
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # CSP header (allow resources for Swagger UI)
            # response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; frame-ancestors 'none'"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app):
        super().__init__(app)
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger("legal_ai.middleware.ratelimit")
    
    async def get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def is_rate_limited(self, key: str, limit: int, window: int = 60) -> tuple[bool, int, int]:
        """Check if request is rate limited."""
        try:
            client = await self.get_redis_client()
            
            # Use sliding window counter
            now = int(time.time())
            window_start = now - window
            
            # Pipeline for atomic operations
            pipe = client.pipeline()
            
            # Remove old entries and count current requests
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            # Calculate remaining requests and reset time
            remaining = max(0, limit - current_requests - 1)  # -1 for current request
            reset_time = now + window
            
            return current_requests >= limit, remaining, reset_time
            
        except Exception as exc:
            self.logger.error(f"Rate limit check failed: {exc}")
            # Fail open - allow request if Redis is unavailable
            return False, limit, int(time.time()) + window
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # Get client identifier (IP + user ID if available)
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        rate_limit_key = f"rate_limit:{client_ip}"
        if user_id:
            rate_limit_key = f"rate_limit:user:{user_id}"
        
        # Check rate limit
        is_limited, remaining, reset_time = await self.is_rate_limited(
            rate_limit_key, 
            settings.RATE_LIMIT_PER_MINUTE
        )
        
        if is_limited:
            retry_after = reset_time - int(time.time())
            self.logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "rate_limit_key": rate_limit_key
                }
            )
            raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.audit_logger = logging.getLogger("audit")
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip audit logging for non-sensitive endpoints
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Get request details
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        request_id = getattr(request.state, "request_id", None)
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log audit event
        audit_data = {
            "request_id": request_id,
            "timestamp": time.time(),
            "user_id": user_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Add additional context for sensitive operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            audit_data["operation_type"] = "write"
        else:
            audit_data["operation_type"] = "read"
        
        self.audit_logger.info("API access", extra=audit_data)
        
        return response


def setup_cors_middleware(app) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
    )


def setup_middleware(app) -> None:
    """Configure all middleware for the FastAPI app."""
    
    # Add middleware in reverse order (last added = first executed)
    
    # Compression (should be last to compress everything)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Audit logging
    app.add_middleware(AuditMiddleware)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware)
    
    # Request logging (should be early to log everything)
    app.add_middleware(RequestLoggingMiddleware)
    
    # CORS (should be first to handle preflight requests)
    setup_cors_middleware(app)