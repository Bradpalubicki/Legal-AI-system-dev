"""
Request Monitoring Middleware
Automatically tracks all API requests for metrics collection
"""

import time
import logging
from typing import Callable, Optional
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import traceback
import jwt
import os

from ..src.monitoring.metrics_collector import metrics_collector
from ..src.core.database import SessionLocal
from ..models.user import User

logger = logging.getLogger(__name__)

# JWT secret for token decoding
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "your-secret-key"))

# Track when each user was last updated to avoid excessive DB writes
_last_activity_updates: dict = {}
_activity_update_interval = 60  # Only update DB once per minute per user


def decode_user_id_from_token(token: str) -> Optional[int]:
    """Decode user ID from JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id") or payload.get("sub")
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.debug(f"Token decode error: {e}")
        return None


def update_user_last_activity(user_id: int):
    """
    Update user's last_active_at timestamp in the database.
    Uses rate limiting to avoid excessive DB writes.
    """
    global _last_activity_updates

    now = time.time()
    last_update = _last_activity_updates.get(user_id, 0)

    # Only update if enough time has passed since last update
    if now - last_update < _activity_update_interval:
        return

    try:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_active_at = datetime.utcnow()
                db.commit()
                _last_activity_updates[user_id] = now
                logger.debug(f"Updated last_active_at for user {user_id}")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to update user activity: {e}")


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor all API requests and collect metrics
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip monitoring for:
        # - monitoring endpoints themselves (avoid recursive tracking)
        # - static files
        # - health checks
        skip_paths = [
            '/api/v1/monitoring',
            '/api/v1/credits',  # Skip credits - called frequently on page loads
            '/api/v1/pacer',    # Skip pacer - has many sub-endpoints
            '/api/v1/courtlistener',  # Skip courtlistener - has many sub-endpoints
            '/docs',
            '/openapi.json',
            '/redoc',
            '/favicon.ico',
            '/metrics',
            '/health'
        ]

        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Get user ID from request if available
        user_id = None
        user_id_int = None
        try:
            # Extract token from authorization header
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                user_id_int = decode_user_id_from_token(token)
                if user_id_int:
                    user_id = str(user_id_int)
        except Exception as e:
            logger.debug(f"Error extracting user from token: {e}")

        # Process request
        response = None
        error = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Update user's last_active_at if authenticated
            if user_id_int:
                update_user_last_activity(user_id_int)
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            error = str(e)
            stack_trace = traceback.format_exc()

            # Record error
            metrics_collector.record_error(
                error_type=type(e).__name__,
                endpoint=request.url.path,
                message=str(e),
                stack_trace=stack_trace,
                user_id=user_id,
                request_data={
                    'method': request.method,
                    'query_params': dict(request.query_params),
                    'headers': dict(request.headers)
                }
            )
            raise

        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record API call
            metrics_collector.record_api_call(
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                error=error,
                metadata={
                    'query_params': dict(request.query_params),
                    'content_length': request.headers.get('content-length', 0)
                }
            )

        return response
