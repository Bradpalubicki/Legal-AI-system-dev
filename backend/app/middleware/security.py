"""
Security Middleware - Production-ready authentication and security headers

Provides JWT authentication, security headers, and request validation.
Can run in development mode (lenient) or production mode (strict).
"""

import os
import logging
from typing import Callable, Optional, List
from datetime import datetime, timezone
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt

logger = logging.getLogger(__name__)

# Get environment settings
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
JWT_SECRET = os.getenv('JWT_SECRET_KEY') or os.getenv('JWT_SECRET', 'development-jwt-secret')
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

# CORS origins for error responses (middleware returns before CORS middleware can add headers)
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]
if not CORS_ORIGINS:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]


def _get_cors_headers(origin: str) -> dict:
    """Generate CORS headers for error responses when middleware returns early"""
    # Check if origin is allowed
    if origin in CORS_ORIGINS or '*' in CORS_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    # Even for disallowed origins, we should return the error without CORS
    # (browser will block it anyway)
    return {}


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware that adds:
    - JWT authentication (optional in dev, required in production)
    - Security headers
    - Request validation
    """

    def __init__(
        self,
        app,
        exclude_paths: Optional[List[str]] = None,
        require_auth: bool = None
    ):
        super().__init__(app)

        # Default exclude paths (ONLY truly public endpoints)
        # SECURITY: Removed document/qa/defense paths - they now REQUIRE authentication
        self.exclude_paths = exclude_paths or [
            '/health',
            '/health/system',
            '/metrics',
            '/docs',
            '/openapi.json',
            '/redoc',
            '/favicon.ico',
            '/api/v1/auth/register',  # Registration is public
            '/api/v1/auth/login',     # Login is public
            '/api/v1/auth/refresh',   # Token refresh is public
            # All other endpoints (documents, qa, defense, etc.) REQUIRE authentication
        ]

        # In development mode, add additional paths that have their own auth fallbacks
        if ENVIRONMENT == 'development':
            self.exclude_paths.extend([
                '/api/v1/pacer',         # PACER has get_current_user_or_test fallback
                '/api/v1/credits',       # Credits - needed for PACER integration
                # CourtListener - specific public paths only (monitor/* requires auth)
                '/api/v1/courtlistener/search',   # Public search endpoints
                '/api/v1/courtlistener/docket',   # Public docket lookup
                '/api/v1/courtlistener/status',   # Public status check
                '/api/v1/courtlistener/recap',    # Public RECAP documents
                # NOTE: /api/v1/documents removed - endpoints require proper auth
            ])

            logger.info(f"Development mode: Added dev-only excluded paths")

        # Always allow monitoring endpoints for testing
        self.exclude_paths.extend([
            '/api/v1/notifications/check-now',   # Manual monitor check trigger
            '/api/v1/notifications/status',      # Monitor status
            '/api/v1/state-courts',              # State court info - public reference data
        ])

        # Determine if auth is required based on environment
        if require_auth is None:
            # Production requires auth, development is optional
            self.require_auth = (ENVIRONMENT == 'production')
        else:
            self.require_auth = require_auth

        logger.info(f"SecurityMiddleware initialized - Environment: {ENVIRONMENT}, Require Auth: {self.require_auth}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks"""

        # ALWAYS allow OPTIONS requests (CORS preflight) - never block these
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response

        print(f"[SECURITY MIDDLEWARE] Processing: {request.url.path}")
        print(f"[SECURITY MIDDLEWARE] require_auth: {self.require_auth}")
        logger.info(f"SecurityMiddleware processing: {request.url.path}")

        # Skip security for excluded paths
        if self._is_excluded_path(request.url.path):
            print(f"[SECURITY MIDDLEWARE] Path is excluded: {request.url.path}")
            response = await call_next(request)
            response = self._add_security_headers(response)
            logger.info(f"Added security headers for excluded path: {request.url.path}")
            return response

        # Get origin for CORS headers on error responses
        origin = request.headers.get('origin', '')
        cors_headers = _get_cors_headers(origin) if origin else {}

        # Perform authentication if required
        if self.require_auth:
            print(f"[SECURITY MIDDLEWARE] Authentication REQUIRED (production mode)")
            try:
                await self._authenticate_request(request)
            except HTTPException as e:
                # Merge CORS headers with any error headers
                error_headers = {**(e.headers or {}), **cors_headers}
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                    headers=error_headers
                )
        else:
            # Development mode - STILL require authentication (no automatic mock users)
            # SECURITY FIX: Dev mode no longer bypasses auth
            print(f"[SECURITY MIDDLEWARE] Development mode - authentication STILL required")
            try:
                await self._authenticate_request(request)
            except HTTPException as e:
                # In dev mode, return a helpful error message
                print(f"[SECURITY MIDDLEWARE] Authentication failed: {e.detail}")
                # Merge CORS headers with any error headers
                error_headers = {**(e.headers or {}), **cors_headers}
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "detail": e.detail,
                        "hint": "Please login first via /api/v1/auth/login to get an access token"
                    },
                    headers=error_headers
                )

        # Process request
        response = await call_next(request)

        # Add security headers to response
        return self._add_security_headers(response)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from authentication"""
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                print(f"[SECURITY] Path '{path}' MATCHED pattern '{excluded}'")
                print(f"[SECURITY] Full exclude list: {self.exclude_paths}")
                return True
        return False

    async def _authenticate_request(self, request: Request):
        """Authenticate the request using JWT"""

        # Get authorization header
        authorization = request.headers.get('Authorization')

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Validate Bearer scheme
        if not authorization.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme. Use 'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Extract token
        token = authorization[7:]  # Remove 'Bearer '

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Verify JWT token
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=['HS256'],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'require': ['user_id', 'exp']
                }
            )

            # Set user context in request state
            request.state.user_id = payload['user_id']
            request.state.auth_method = 'jwt'
            request.state.authenticated_at = datetime.now(timezone.utc)
            request.state.token_payload = payload

            logger.debug(f"Authenticated user: {payload['user_id']}")

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"}
            )

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy (basic)
        if ENVIRONMENT == 'production':
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )

        # Strict-Transport-Security (HSTS) - only in production with HTTPS
        if ENVIRONMENT == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Permissions Policy (formerly Feature-Policy)
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=()'
        )

        return response


def setup_security_middleware(app, **kwargs):
    """
    Convenience function to add security middleware to FastAPI app

    Usage:
        setup_security_middleware(app)
        # or with custom settings:
        setup_security_middleware(app, require_auth=True, exclude_paths=['/public'])
    """
    app.add_middleware(SecurityMiddleware, **kwargs)
    logger.info("Security middleware configured")
