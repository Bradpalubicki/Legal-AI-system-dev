"""
Middleware Components for Legal AI System

Comprehensive middleware stack including request logging, authentication,
rate limiting, CORS, security headers, and performance monitoring.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any, List
import asyncio

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
import redis.asyncio as redis

from .config import get_settings
from .logging import get_logger, audit_logger, security_logger, performance_logger
from .exceptions import RateLimitException, AuthenticationException

settings = get_settings()
logger = get_logger('middleware')


# =============================================================================
# REQUEST LOGGING MIDDLEWARE
# =============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and responses"""
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/health', '/metrics', '/favicon.ico']
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Log request start
        start_time = time.time()
        request_size = int(request.headers.get('content-length', 0))
        
        logger.set_context(request_id=request_id)
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'http_method': request.method,
                'http_path': request.url.path,
                'http_query': str(request.url.query) if request.url.query else None,
                'client_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
                'content_type': request.headers.get('content-type'),
                'request_size_bytes': request_size,
                'referer': request.headers.get('referer')
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            response_size = int(response.headers.get('content-length', 0))
            
            # Add response headers
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    'http_status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'response_size_bytes': response_size
                }
            )
            
            # Log performance metrics
            user_id = getattr(request.state, 'user_id', None)
            performance_logger.log_request_metrics(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_size=request_size,
                response_size=response_size,
                user_id=user_id
            )
            
            return response
            
        except Exception as exc:
            # Log request error
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {type(exc).__name__} ({duration_ms:.2f}ms)",
                extra={
                    'error_type': type(exc).__name__,
                    'error_message': str(exc),
                    'duration_ms': duration_ms
                },
                exc_info=True
            )
            raise


# =============================================================================
# RATE LIMITING MIDDLEWARE
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    def __init__(
        self,
        app,
        redis_url: str = None,
        default_limit: int = 100,
        window_seconds: int = 60,
        exclude_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or ['/health', '/metrics']
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client with lazy initialization"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client
    
    async def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get authenticated user ID first
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else 'unknown'
        return f"ip:{client_ip}"
    
    async def check_rate_limit(self, client_id: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Check rate limit for client"""
        try:
            redis_client = await self.get_redis_client()
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use sliding window rate limiting
            pipe = redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(client_id, 0, window_start)
            
            # Count current requests
            pipe.zcard(client_id)
            
            # Add current request
            pipe.zadd(client_id, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(client_id, window + 1)
            
            results = await pipe.execute()
            current_requests = results[1]  # Count result
            
            # Check if limit exceeded
            if current_requests >= limit:
                return False, current_requests, window
            
            return True, current_requests, window
            
        except Exception as exc:
            logger.error(f"Rate limit check failed: {exc}", exc_info=True)
            # Fail open - allow request if Redis is unavailable
            return True, 0, window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get rate limit configuration
        limit = self.default_limit
        window = self.window_seconds
        
        # Custom limits based on endpoint
        if request.url.path.startswith('/api/v1/documents'):
            limit = 20  # Lower limit for document endpoints
        elif request.url.path.startswith('/api/v1/ai'):
            limit = 10  # Very low limit for AI endpoints
        
        # Check rate limit
        client_id = await self.get_client_identifier(request)
        allowed, current_requests, window_time = await self.check_rate_limit(client_id, limit, window)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id}",
                extra={
                    'client_id': client_id,
                    'current_requests': current_requests,
                    'limit': limit,
                    'window_seconds': window_time
                }
            )
            
            raise RateLimitException(
                resource=request.url.path,
                limit=limit,
                window=f"{window_time} seconds",
                retry_after=window_time
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(limit - current_requests)
        response.headers['X-RateLimit-Window'] = str(window_time)
        
        return response


# =============================================================================
# AUTHENTICATION MIDDLEWARE
# =============================================================================

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT Authentication middleware"""
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            '/health', '/metrics', '/docs', '/openapi.json', '/redoc',
            '/auth/login', '/auth/register', '/auth/refresh'
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get authorization header
        authorization = request.headers.get('Authorization')
        if not authorization:
            raise AuthenticationException("Authorization header missing")
        
        scheme, token = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != 'bearer':
            raise AuthenticationException("Invalid authorization scheme")
        
        if not token:
            raise AuthenticationException("Token missing")
        
        try:
            # Validate JWT token (simplified - implement proper JWT validation)
            user_id = await self.validate_token(token)
            
            # Set user context
            request.state.user_id = user_id
            request.state.token = token
            
            # Log authentication success
            security_logger.log_auth_attempt(
                username=user_id,
                success=True,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent')
            )
            
            return await call_next(request)
            
        except AuthenticationException:
            # Log authentication failure
            security_logger.log_auth_attempt(
                username='unknown',
                success=False,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
                details={'reason': 'invalid_token'}
            )
            raise
    
    async def validate_token(self, token: str) -> str:
        """Validate JWT token and return user ID"""
        # TODO: Implement proper JWT validation
        # This is a placeholder implementation
        if token == 'invalid':
            raise AuthenticationException("Invalid token")
        
        # Return mock user ID
        return 'user123'


# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy
        # csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
        # response.headers['Content-Security-Policy'] = csp
        
        return response


# =============================================================================
# ERROR TRACKING MIDDLEWARE
# =============================================================================

class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Track and report application errors"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # Track error with context
            error_id = str(uuid.uuid4())
            request_id = getattr(request.state, 'request_id', 'unknown')
            user_id = getattr(request.state, 'user_id', None)
            
            error_context = {
                'error_id': error_id,
                'request_id': request_id,
                'user_id': user_id,
                'method': request.method,
                'url': str(request.url),
                'client_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
                'error_type': type(exc).__name__,
                'error_message': str(exc)
            }
            
            logger.error(f"Unhandled error [{error_id}]: {exc}", extra=error_context, exc_info=True)
            
            # TODO: Send to external error tracking service (Sentry, etc.)
            
            raise


# =============================================================================
# AUDIT LOGGING MIDDLEWARE
# =============================================================================

class AuditMiddleware(BaseHTTPMiddleware):
    """Log audit events for sensitive operations"""
    
    def __init__(self, app, audit_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.audit_paths = audit_paths or ['/api/v1/dockets', '/api/v1/documents', '/api/v1/users']
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is an auditable operation
        should_audit = any(request.url.path.startswith(path) for path in self.audit_paths)
        
        if not should_audit or request.method == 'GET':
            return await call_next(request)
        
        # Process request
        response = await call_next(request)
        
        # Log audit event for successful operations
        if 200 <= response.status_code < 300:
            user_id = getattr(request.state, 'user_id', None)
            request_id = getattr(request.state, 'request_id', None)
            
            # Determine action and resource from path and method
            action = self.get_action_from_method(request.method)
            resource = self.get_resource_from_path(request.url.path)
            
            audit_logger.log_action(
                action=action,
                resource=resource,
                user_id=user_id,
                request_id=request_id,
                details={
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code
                }
            )
        
        return response
    
    def get_action_from_method(self, method: str) -> str:
        """Map HTTP method to audit action"""
        action_map = {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE'
        }
        return action_map.get(method, 'UNKNOWN')
    
    def get_resource_from_path(self, path: str) -> str:
        """Extract resource name from path"""
        parts = path.strip('/').split('/')
        if len(parts) >= 3:  # /api/v1/resource
            return parts[2].upper()
        return 'UNKNOWN'


# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

def configure_middleware(app):
    """Configure all middleware for the FastAPI application"""
    
    # Security middleware (outermost)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=['*'] if settings.ENVIRONMENT == 'development' else ['localhost', '127.0.0.1']
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
        expose_headers=['X-Request-ID', 'X-Response-Time', 'X-RateLimit-Limit', 'X-RateLimit-Remaining']
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET,
        max_age=3600,  # 1 hour
        same_site='lax',
        https_only=settings.ENVIRONMENT == 'production'
    )
    
    # Custom middleware (order matters - innermost first)
    app.add_middleware(ErrorTrackingMiddleware)
    app.add_middleware(AuditMiddleware)
    
    # Authentication middleware (if enabled)
    if hasattr(settings, 'AUTHENTICATION_REQUIRED') and settings.AUTHENTICATION_REQUIRED:
        app.add_middleware(AuthenticationMiddleware)
    
    # Rate limiting middleware (if enabled)
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(
            RateLimitMiddleware,
            default_limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            window_seconds=60
        )
    
    # Request logging middleware (innermost)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("Middleware configuration completed")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'RequestLoggingMiddleware',
    'RateLimitMiddleware',
    'AuthenticationMiddleware',
    'SecurityHeadersMiddleware',
    'ErrorTrackingMiddleware',
    'AuditMiddleware',
    'configure_middleware'
]