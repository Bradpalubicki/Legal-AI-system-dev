"""
Security Middleware

Comprehensive security middleware for FastAPI including:
- Security headers injection
- HTTPS enforcement
- Request validation
- Security logging
- IP filtering
"""

import time
import logging
from typing import Callable, Optional, Set
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.datastructures import Headers

from .tls_config import get_security_headers

logger = logging.getLogger(__name__)

# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all HTTP responses.

    Headers include:
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(self, app, custom_headers: Optional[dict] = None):
        super().__init__(app)
        self.security_headers = get_security_headers()

        # Merge custom headers
        if custom_headers:
            self.security_headers.update(custom_headers)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)

        # Add security headers
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value

        return response


# =============================================================================
# HTTPS ENFORCEMENT MIDDLEWARE
# =============================================================================

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Redirect all HTTP requests to HTTPS in production.

    Honors X-Forwarded-Proto header from load balancers/proxies.
    """

    def __init__(self, app, enforce: bool = True, exclude_paths: Optional[Set[str]] = None):
        super().__init__(app)
        self.enforce = enforce
        self.exclude_paths = exclude_paths or {'/health', '/health/liveness', '/metrics'}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enforce HTTPS"""

        # Skip enforcement if disabled or for excluded paths
        if not self.enforce or request.url.path in self.exclude_paths:
            return await call_next(request)

        # Check if request is HTTPS
        # Consider both direct HTTPS and X-Forwarded-Proto header
        forwarded_proto = request.headers.get('X-Forwarded-Proto', '').lower()
        is_secure = request.url.scheme == 'https' or forwarded_proto == 'https'

        if not is_secure:
            # Redirect to HTTPS
            https_url = request.url.replace(scheme='https')
            return Response(
                status_code=status.HTTP_308_PERMANENT_REDIRECT,
                headers={'Location': str(https_url)}
            )

        return await call_next(request)


# =============================================================================
# REQUEST VALIDATION MIDDLEWARE
# =============================================================================

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate incoming requests for security threats.

    Checks:
    - Request size limits
    - Suspicious headers
    - Path traversal attempts
    - SQL injection patterns
    """

    def __init__(
        self,
        app,
        max_request_size: int = 10 * 1024 * 1024,  # 10 MB
        max_header_size: int = 8192,  # 8 KB
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.max_header_size = max_header_size

        # Suspicious patterns to check for
        self.path_traversal_patterns = ['../', '..\\', '%2e%2e', '%252e%252e']
        self.sql_injection_patterns = [
            'union select',
            'drop table',
            'delete from',
            'insert into',
            '--',
            ';--',
            '/*',
            '*/',
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request"""

        # Check content length
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(
                        f"Request too large: {size} bytes from {request.client.host}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request size exceeds maximum of {self.max_request_size} bytes"
                    )
            except ValueError:
                pass

        # Check headers size
        headers_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if headers_size > self.max_header_size:
            logger.warning(
                f"Headers too large: {headers_size} bytes from {request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
                detail="Request headers too large"
            )

        # Check for path traversal
        path = request.url.path.lower()
        for pattern in self.path_traversal_patterns:
            if pattern in path:
                logger.warning(
                    f"Path traversal attempt detected: {path} from {request.client.host}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request path"
                )

        # Check for SQL injection in query parameters
        query_string = str(request.url.query).lower()
        for pattern in self.sql_injection_patterns:
            if pattern in query_string:
                logger.warning(
                    f"SQL injection attempt detected in query: {query_string} from {request.client.host}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request parameters"
                )

        return await call_next(request)


# =============================================================================
# IP FILTERING MIDDLEWARE
# =============================================================================

class IPFilterMiddleware(BaseHTTPMiddleware):
    """
    Filter requests by IP address.

    Supports:
    - Whitelist mode (only allowed IPs)
    - Blacklist mode (block specific IPs)
    """

    def __init__(
        self,
        app,
        whitelist: Optional[Set[str]] = None,
        blacklist: Optional[Set[str]] = None,
        exclude_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.whitelist = whitelist
        self.blacklist = blacklist or set()
        self.exclude_paths = exclude_paths or {'/health', '/metrics'}

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address, considering proxies.

        Checks X-Forwarded-For header from load balancers.
        """
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            # Get first IP (original client)
            return forwarded.split(',')[0].strip()

        return request.client.host if request.client else 'unknown'

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Filter by IP"""

        # Skip filtering for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # Check blacklist
        if client_ip in self.blacklist:
            logger.warning(f"Blocked blacklisted IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Check whitelist (if enabled)
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"Blocked non-whitelisted IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return await call_next(request)


# =============================================================================
# SECURITY LOGGING MIDDLEWARE
# =============================================================================

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log security-relevant events.

    Logs:
    - Authentication attempts
    - Authorization failures
    - Suspicious requests
    - High-risk operations
    """

    def __init__(self, app):
        super().__init__(app)

        # Paths to always log
        self.log_paths = {
            '/auth/login',
            '/auth/logout',
            '/auth/register',
            '/auth/reset-password',
            '/api/admin',
        }

        # Paths to log on failure
        self.log_on_failure_paths = {
            '/api/',  # All API endpoints
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log security events"""

        start_time = time.time()
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else 'unknown'

        # Get forwarded IP if behind proxy
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            client_ip = forwarded.split(',')[0].strip()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Determine if we should log
        should_log = False

        # Always log certain paths
        if any(path.startswith(log_path) for log_path in self.log_paths):
            should_log = True

        # Log failures on API endpoints
        if response.status_code >= 400:
            if any(path.startswith(log_path) for log_path in self.log_on_failure_paths):
                should_log = True

        # Log if needed
        if should_log:
            log_data = {
                'event': 'security_request',
                'method': method,
                'path': path,
                'status_code': response.status_code,
                'client_ip': client_ip,
                'duration_ms': int(duration * 1000),
                'user_agent': request.headers.get('user-agent', ''),
            }

            # Add user info if available
            if hasattr(request.state, 'user') and request.state.user:
                log_data['user_id'] = request.state.user.get('id')
                log_data['user_email'] = request.state.user.get('email')

            # Log at appropriate level
            if response.status_code >= 500:
                logger.error(f"Security log: {log_data}")
            elif response.status_code >= 400:
                logger.warning(f"Security log: {log_data}")
            else:
                logger.info(f"Security log: {log_data}")

        return response


# =============================================================================
# REQUEST ID MIDDLEWARE
# =============================================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.

    Adds:
    - X-Request-ID header to response
    - request.state.request_id for logging
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID"""
        import uuid

        # Check for existing request ID (from load balancer)
        request_id = request.headers.get('X-Request-ID')

        if not request_id:
            # Generate new request ID
            request_id = str(uuid.uuid4())

        # Store in request state for logging
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response
        response.headers['X-Request-ID'] = request_id

        return response


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

def configure_cors(
    allowed_origins: Optional[list] = None,
    allow_credentials: bool = True,
) -> dict:
    """
    Get CORS configuration for FastAPI.

    Args:
        allowed_origins: List of allowed origins (default: from env)
        allow_credentials: Whether to allow credentials

    Returns:
        Dictionary with CORS parameters
    """
    import os

    # Get allowed origins from environment if not provided
    if allowed_origins is None:
        origins_env = os.getenv('CORS_ORIGINS', '*')
        if origins_env == '*':
            allowed_origins = ['*']
        else:
            allowed_origins = [o.strip() for o in origins_env.split(',')]

    return {
        'allow_origins': allowed_origins,
        'allow_credentials': allow_credentials,
        'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
        'allow_headers': [
            'Accept',
            'Accept-Language',
            'Content-Type',
            'Authorization',
            'X-Request-ID',
            'X-API-Key',
        ],
        'expose_headers': [
            'X-Request-ID',
            'X-RateLimit-Limit',
            'X-RateLimit-Remaining',
            'X-RateLimit-Reset',
        ],
        'max_age': 600,  # Cache preflight requests for 10 minutes
    }


# =============================================================================
# MIDDLEWARE SETUP HELPER
# =============================================================================

def setup_security_middleware(app, config: Optional[dict] = None):
    """
    Set up all security middleware for FastAPI app.

    Args:
        app: FastAPI application
        config: Optional configuration dict

    Example:
        from fastapi import FastAPI
        from security_middleware import setup_security_middleware

        app = FastAPI()
        setup_security_middleware(app)
    """
    config = config or {}

    # Request ID (should be first)
    app.add_middleware(RequestIDMiddleware)

    # Security logging
    app.add_middleware(SecurityLoggingMiddleware)

    # Request validation
    app.add_middleware(
        RequestValidationMiddleware,
        max_request_size=config.get('max_request_size', 10 * 1024 * 1024),
        max_header_size=config.get('max_header_size', 8192),
    )

    # IP filtering (if configured)
    if config.get('ip_whitelist') or config.get('ip_blacklist'):
        app.add_middleware(
            IPFilterMiddleware,
            whitelist=config.get('ip_whitelist'),
            blacklist=config.get('ip_blacklist'),
        )

    # HTTPS redirect (in production)
    import os
    if os.getenv('ENVIRONMENT') == 'production':
        app.add_middleware(
            HTTPSRedirectMiddleware,
            enforce=config.get('enforce_https', True),
        )

    # Security headers
    app.add_middleware(
        SecurityHeadersMiddleware,
        custom_headers=config.get('custom_headers'),
    )

    # Trusted hosts (prevent host header injection)
    allowed_hosts = config.get('allowed_hosts') or os.getenv('ALLOWED_HOSTS', '*').split(',')
    if allowed_hosts != ['*']:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # CORS
    cors_config = configure_cors(
        allowed_origins=config.get('cors_origins'),
        allow_credentials=config.get('cors_allow_credentials', True),
    )
    app.add_middleware(CORSMiddleware, **cors_config)

    logger.info("Security middleware configured successfully")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'SecurityHeadersMiddleware',
    'HTTPSRedirectMiddleware',
    'RequestValidationMiddleware',
    'IPFilterMiddleware',
    'SecurityLoggingMiddleware',
    'RequestIDMiddleware',
    'configure_cors',
    'setup_security_middleware',
]
