"""
SECURE MIDDLEWARE IMPLEMENTATION
Replaces vulnerable middleware with secure implementations
"""

import time
import uuid
import json
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any, List
import asyncio

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from .config import get_settings
from .logging import get_logger, audit_logger, security_logger
from .security_fixes import (
    SecureJWTHandler, SecureRateLimiter, SecureAPIKeyManager,
    SecurityAuditor, SecureSessionManager
)

settings = get_settings()
logger = get_logger('secure_middleware')

# Initialize secure components
try:
    security_components = {
        'jwt_handler': SecureJWTHandler(settings.JWT_SECRET),
        'rate_limiter': SecureRateLimiter(settings.REDIS_URL),
        'api_key_manager': SecureAPIKeyManager(settings.JWT_SECRET),
        'auditor': SecurityAuditor(settings.REDIS_URL),
        'session_manager': SecureSessionManager(settings.REDIS_URL, settings.SESSION_SECRET)
    }
except Exception as e:
    logger.error(f"Failed to initialize security components: {e}")
    security_components = None


class SecureAuthenticationMiddleware(BaseHTTPMiddleware):
    """Secure JWT Authentication Middleware with proper validation"""

    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            '/health', '/metrics', '/docs', '/openapi.json', '/redoc',
            '/auth/login', '/auth/register', '/auth/refresh', '/favicon.ico', '/'
        ]
        self.jwt_handler = security_components['jwt_handler'] if security_components else None
        self.auditor = security_components['auditor'] if security_components else None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        if not self.jwt_handler:
            logger.error("JWT handler not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication system unavailable"
            )

        # Get authorization header
        authorization = request.headers.get('Authorization')
        api_key = request.headers.get('X-API-Key')

        if not authorization and not api_key:
            await self._log_auth_failure(request, "missing_credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        try:
            user_id = None
            auth_method = None

            # Try JWT authentication first
            if authorization:
                if not authorization.startswith('Bearer '):
                    await self._log_auth_failure(request, "invalid_auth_scheme")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authorization scheme",
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                token = authorization[7:]  # Remove 'Bearer '
                if not token:
                    await self._log_auth_failure(request, "empty_token")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token required",
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # Verify JWT token
                payload = self.jwt_handler.verify_token(token)
                user_id = payload['user_id']
                auth_method = 'jwt'
                request.state.token_payload = payload

            # Try API key authentication if JWT failed
            elif api_key:
                # In production, verify API key against database
                if not self._verify_api_key(api_key):
                    await self._log_auth_failure(request, "invalid_api_key")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key"
                    )

                user_id = self._get_user_from_api_key(api_key)
                auth_method = 'api_key'

            # Set request context
            request.state.user_id = user_id
            request.state.auth_method = auth_method
            request.state.authenticated_at = datetime.now(timezone.utc)

            # Check for suspicious activity
            await self._check_suspicious_activity(request, user_id)

            # Log successful authentication
            if self.auditor:
                await self.auditor.log_security_event("AUTH_SUCCESS", {
                    'user_id': user_id,
                    'method': auth_method,
                    'ip': request.client.host if request.client else None,
                    'path': request.url.path
                })

            return await call_next(request)

        except HTTPException:
            raise
        except Exception as exc:
            await self._log_auth_failure(request, f"system_error: {str(exc)}")
            logger.error(f"Authentication error: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

    def _verify_api_key(self, api_key: str) -> bool:
        """Verify API key (implement proper database lookup)"""
        # Placeholder - implement proper API key verification
        if not api_key or len(api_key) < 20:
            return False
        return api_key.startswith('legalai_')

    def _get_user_from_api_key(self, api_key: str) -> str:
        """Get user ID from API key (implement proper database lookup)"""
        # Placeholder - implement proper user lookup
        return "api_user"

    async def _log_auth_failure(self, request: Request, reason: str):
        """Log authentication failure"""
        client_ip = request.client.host if request.client else "unknown"

        if self.auditor:
            await self.auditor.log_security_event("AUTH_FAILURE", {
                'reason': reason,
                'ip': client_ip,
                'path': request.url.path,
                'user_agent': request.headers.get('user-agent'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

            # Track failed attempts for brute force protection
            await self.auditor.track_failed_attempts(client_ip, "auth")

    async def _check_suspicious_activity(self, request: Request, user_id: str):
        """Check for suspicious authentication patterns"""
        if not self.auditor:
            return

        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')

        # Check if IP is blocked due to too many failures
        if client_ip and await self.auditor.is_blocked(client_ip, "auth"):
            await self.auditor.log_security_event("BLOCKED_IP_ACCESS", {
                'ip': client_ip,
                'user_id': user_id
            })
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )


class SecureRateLimitMiddleware(BaseHTTPMiddleware):
    """Secure Rate Limiting Middleware with fail-closed behavior"""

    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/health', '/metrics', '/favicon.ico']
        self.rate_limiter = security_components['rate_limiter'] if security_components else None
        self.auditor = security_components['auditor'] if security_components else None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        if not self.rate_limiter:
            logger.error("Rate limiter not initialized")
            # Fail closed - reject request if rate limiter unavailable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service unavailable"
            )

        # Get client identifier
        client_id = await self._get_client_identifier(request)

        # Determine rate limits based on endpoint and user
        limit, window = self._get_rate_limits(request)

        # Check rate limit
        try:
            allowed, current_count = await self.rate_limiter.is_allowed(client_id, limit, window)
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail closed - reject request if rate limiting fails
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service error"
            )

        if not allowed:
            # Log rate limit violation
            if self.auditor:
                await self.auditor.log_security_event("RATE_LIMIT_EXCEEDED", {
                    'client_id': client_id,
                    'limit': limit,
                    'current_count': current_count,
                    'path': request.url.path,
                    'method': request.method
                })

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Limit: {limit} requests per {window} seconds",
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + window)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers.update({
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - current_count - 1)),
            "X-RateLimit-Window": str(window)
        })

        return response

    async def _get_client_identifier(self, request: Request) -> str:
        """Get secure client identifier for rate limiting"""
        # Prefer authenticated user ID
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address with additional context
        client_ip = request.client.host if request.client else 'unknown'
        user_agent_hash = hash(request.headers.get('user-agent', ''))

        return f"ip:{client_ip}:ua:{abs(user_agent_hash) % 10000}"

    def _get_rate_limits(self, request: Request) -> tuple[int, int]:
        """Get rate limits based on endpoint and authentication status"""
        # Base limits
        limit = 60  # requests per minute
        window = 60  # seconds

        # More restrictive limits for unauthenticated users
        if not getattr(request.state, 'user_id', None):
            limit = 20

        # Endpoint-specific limits
        path = request.url.path
        if path.startswith('/api/v1/ai/'):
            limit = 5  # AI endpoints are expensive
            window = 60
        elif path.startswith('/api/v1/documents/upload'):
            limit = 10  # Document uploads
            window = 300  # 5 minutes
        elif path.startswith('/auth/'):
            limit = 10  # Authentication endpoints
            window = 300

        return limit, window


class SecureDataProtectionMiddleware(BaseHTTPMiddleware):
    """Data protection and sanitization middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process request
        response = await call_next(request)

        # Sanitize response headers
        sensitive_headers = [
            'server', 'x-powered-by', 'x-aspnet-version',
            'x-aspnetmvc-version', 'x-frame-options'
        ]

        for header in sensitive_headers:
            if header in response.headers:
                del response.headers[header]

        # Add security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
            'Pragma': 'no-cache'
        }

        if settings.ENVIRONMENT == 'production':
            security_headers.update({
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-ancestors 'none'"
            })

        response.headers.update(security_headers)

        # Check for information leakage in error responses
        if response.status_code >= 400:
            await self._sanitize_error_response(response)

        return response

    async def _sanitize_error_response(self, response: Response):
        """Sanitize error responses to prevent information disclosure"""
        if hasattr(response, 'body'):
            try:
                body = response.body
                if isinstance(body, bytes):
                    content = body.decode('utf-8')
                else:
                    content = str(body)

                # Remove sensitive patterns
                sensitive_patterns = [
                    r'/[a-zA-Z]:/[\w/\\.-]+',  # File paths
                    r'password[\'"\s]*[:=][\'"\s]*\w+',  # Passwords
                    r'secret[\'"\s]*[:=][\'"\s]*\w+',  # Secrets
                    r'token[\'"\s]*[:=][\'"\s]*[\w.-]+',  # Tokens
                    r'key[\'"\s]*[:=][\'"\s]*[\w.-]+',  # API keys
                ]

                import re
                for pattern in sensitive_patterns:
                    content = re.sub(pattern, '[REDACTED]', content, flags=re.IGNORECASE)

                response.body = content.encode('utf-8')
            except Exception as e:
                logger.error(f"Error sanitizing response: {e}")


class SecureAuditMiddleware(BaseHTTPMiddleware):
    """Enhanced audit logging middleware"""

    def __init__(self, app, audit_sensitive_endpoints: bool = True):
        super().__init__(app)
        self.audit_sensitive_endpoints = audit_sensitive_endpoints
        self.auditor = security_components['auditor'] if security_components else None

        self.sensitive_endpoints = [
            '/api/v1/documents', '/api/v1/users', '/api/v1/clients',
            '/api/v1/cases', '/auth/', '/admin/'
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Determine if this request should be audited
        should_audit = self._should_audit_request(request)

        if not should_audit or not self.auditor:
            return await call_next(request)

        # Capture request details
        request_details = await self._capture_request_details(request)

        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log audit event for successful operations
        if 200 <= response.status_code < 400:
            await self._log_audit_event(request, response, request_details, duration)

        return response

    def _should_audit_request(self, request: Request) -> bool:
        """Determine if request should be audited"""
        # Always audit sensitive endpoints
        if any(request.url.path.startswith(endpoint) for endpoint in self.sensitive_endpoints):
            return True

        # Audit all non-GET requests to API endpoints
        if request.method != 'GET' and request.url.path.startswith('/api/'):
            return True

        return False

    async def _capture_request_details(self, request: Request) -> Dict[str, Any]:
        """Capture request details for audit logging"""
        user_id = getattr(request.state, 'user_id', 'anonymous')
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

        return {
            'request_id': request_id,
            'user_id': user_id,
            'method': request.method,
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'client_ip': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'auth_method': getattr(request.state, 'auth_method', None)
        }

    async def _log_audit_event(self, request: Request, response: Response,
                             request_details: Dict[str, Any], duration: float):
        """Log comprehensive audit event"""
        action = self._determine_action(request.method, request.url.path)
        resource = self._extract_resource(request.url.path)

        audit_event = {
            'action': action,
            'resource': resource,
            'status': 'SUCCESS',
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            **request_details
        }

        await self.auditor.log_security_event("AUDIT_LOG", audit_event)

        # Additional logging for sensitive operations
        if action in ['DELETE', 'UPDATE'] and resource in ['DOCUMENTS', 'USERS', 'CASES']:
            await self.auditor.log_security_event("SENSITIVE_OPERATION", {
                'operation': f"{action} {resource}",
                'user_id': request_details['user_id'],
                'ip': request_details['client_ip'],
                'path': request_details['path']
            })

    def _determine_action(self, method: str, path: str) -> str:
        """Determine action from HTTP method and path"""
        action_map = {
            'GET': 'READ',
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE'
        }
        return action_map.get(method, 'UNKNOWN')

    def _extract_resource(self, path: str) -> str:
        """Extract resource name from path"""
        parts = [p for p in path.strip('/').split('/') if p]
        if len(parts) >= 2 and parts[0] == 'api':
            if len(parts) >= 3:
                return parts[2].upper()
            return parts[1].upper()
        return 'UNKNOWN'


def configure_secure_middleware(app):
    """Configure secure middleware stack"""
    logger.info("Configuring secure middleware stack...")

    if not security_components:
        logger.error("Security components not initialized - using basic middleware only")
        return

    # Security middleware (outermost)
    app.add_middleware(SecureDataProtectionMiddleware)

    # Trusted host middleware
    trusted_hosts = ['*'] if settings.ENVIRONMENT == 'development' else [
        'localhost', '127.0.0.1', settings.API_BASE_URL.split('://')[-1].split(':')[0]
    ]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # CORS middleware with strict configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["http://localhost:3000"],
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        expose_headers=['X-Request-ID', 'X-Response-Time', 'X-RateLimit-Limit', 'X-RateLimit-Remaining']
    )

    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Session middleware with secure configuration
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET,
        max_age=3600,  # 1 hour
        same_site='strict' if settings.ENVIRONMENT == 'production' else 'lax',
        https_only=settings.ENVIRONMENT == 'production',
        domain=None  # Let browser determine
    )

    # Custom secure middleware (order matters)
    app.add_middleware(SecureAuditMiddleware)
    app.add_middleware(SecureRateLimitMiddleware)
    app.add_middleware(SecureAuthenticationMiddleware)

    logger.info("Secure middleware configuration completed")


__all__ = [
    'SecureAuthenticationMiddleware',
    'SecureRateLimitMiddleware',
    'SecureDataProtectionMiddleware',
    'SecureAuditMiddleware',
    'configure_secure_middleware'
]