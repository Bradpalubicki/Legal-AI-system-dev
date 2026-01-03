"""
Exception Classes and Error Handling for Legal AI System

Custom exception classes and error handlers for consistent
error responses across the application.
"""

import os
import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

logger = logging.getLogger(__name__)


def _get_cors_headers(request: Request) -> Dict[str, str]:
    """Get CORS headers based on request origin"""
    origin = request.headers.get("origin", "")

    # Get allowed origins from environment
    cors_origins = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    cors_origins = [o.strip() for o in cors_origins if o.strip()]

    # Default origins for development
    if not cors_origins:
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
        ]

    # Check if origin is allowed
    if origin and (origin in cors_origins or '*' in cors_origins):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }

    # If origin not in list but we have an origin, still return headers for better error visibility
    if origin:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }

    return {}


# =============================================================================
# CUSTOM EXCEPTION CLASSES
# =============================================================================

class LegalAIException(Exception):
    """Base exception class for Legal AI System"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(LegalAIException):
    """Exception for validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details or {"field": field} if field else {},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class BusinessLogicException(LegalAIException):
    """Exception for business logic violations"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class AuthenticationException(LegalAIException):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(LegalAIException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundException(LegalAIException):
    """Exception for resource not found errors"""
    
    def __init__(self, resource: str, identifier: Union[str, int], details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=details or {"resource": resource, "identifier": str(identifier)},
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicateResourceException(LegalAIException):
    """Exception for duplicate resource errors"""
    
    def __init__(self, resource: str, field: str, value: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(
            message=message,
            error_code="DUPLICATE_RESOURCE",
            details=details or {"resource": resource, "field": field, "value": value},
            status_code=status.HTTP_409_CONFLICT
        )


class DatabaseException(LegalAIException):
    """Exception for database-related errors"""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details or {"operation": operation} if operation else {},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ExternalServiceException(LegalAIException):
    """Exception for external service errors (PACER, AI APIs, etc.)"""
    
    def __init__(
        self,
        service: str,
        message: str,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details or {"service": service},
            status_code=status_code
        )


class PacerException(ExternalServiceException):
    """Exception for PACER-specific errors"""
    
    def __init__(self, message: str, pacer_error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if pacer_error_code:
            details["pacer_error_code"] = pacer_error_code
        
        super().__init__(
            service="PACER",
            message=message,
            details=details
        )


class AIServiceException(ExternalServiceException):
    """Exception for AI service errors"""
    
    def __init__(
        self,
        service: str,
        message: str,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if model:
            details["model"] = model
        
        super().__init__(
            service=f"AI Service ({service})",
            message=message,
            details=details
        )


class RateLimitException(LegalAIException):
    """Exception for rate limiting errors"""
    
    def __init__(
        self,
        resource: str,
        limit: int,
        window: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Rate limit exceeded for {resource}: {limit} requests per {window}"
        details = details or {
            "resource": resource,
            "limit": limit,
            "window": window,
            "retry_after": retry_after
        }
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class ConfigurationException(LegalAIException):
    """Exception for configuration errors"""
    
    def __init__(self, parameter: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Configuration error for '{parameter}': {message}",
            error_code="CONFIGURATION_ERROR",
            details=details or {"parameter": parameter},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# ERROR RESPONSE UTILITIES
# =============================================================================

def create_error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized error response"""
    
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    return error_response


def log_error(
    error: Exception,
    request: Optional[Request] = None,
    user_id: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Log error with context information"""
    
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if request:
        context.update({
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        })
    
    if user_id:
        context["user_id"] = user_id
    
    if additional_context:
        context.update(additional_context)
    
    if isinstance(error, LegalAIException):
        context["error_code"] = error.error_code
        context["details"] = error.details
    
    # Log stack trace for unhandled exceptions
    if not isinstance(error, (LegalAIException, HTTPException, RequestValidationError)):
        context["stack_trace"] = traceback.format_exc()
        logger.error("Unhandled exception occurred", extra=context, exc_info=True)
    else:
        logger.error("Application exception occurred", extra=context)


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

async def legal_ai_exception_handler(request: Request, exc: LegalAIException) -> JSONResponse:
    """Handler for custom LegalAI exceptions"""

    # Extract request ID from headers if available
    request_id = request.headers.get("X-Request-ID")

    # Log the error
    log_error(exc, request, request_id=request_id)

    # Create error response
    error_response = create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=_get_cors_headers(request)
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for HTTP exceptions"""

    request_id = request.headers.get("X-Request-ID")

    # Log the error
    log_error(exc, request, request_id=request_id)

    # Create error response
    error_response = create_error_response(
        error_code="HTTP_ERROR",
        message=exc.detail if hasattr(exc, 'detail') else "HTTP error occurred",
        status_code=exc.status_code,
        request_id=request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=_get_cors_headers(request)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for request validation errors"""

    request_id = request.headers.get("X-Request-ID")

    # Extract validation error details
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]) if error["loc"] else None,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })

    # Log the error
    log_error(exc, request, request_id=request_id, additional_context={
        "validation_errors": validation_errors
    })

    # Create error response
    error_response = create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": validation_errors},
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
        headers=_get_cors_headers(request)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions"""

    request_id = request.headers.get("X-Request-ID")

    # Log the error with full stack trace
    log_error(exc, request, request_id=request_id)

    # Create generic error response (don't expose internal details)
    error_response = create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
        headers=_get_cors_headers(request)
    )


# =============================================================================
# EXCEPTION HANDLER REGISTRY
# =============================================================================

EXCEPTION_HANDLERS = {
    LegalAIException: legal_ai_exception_handler,
    StarletteHTTPException: http_exception_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    Exception: general_exception_handler,
}


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    # Exception classes
    "LegalAIException",
    "ValidationException",
    "BusinessLogicException",
    "AuthenticationException",
    "AuthorizationException",
    "ResourceNotFoundException",
    "DuplicateResourceException",
    "DatabaseException",
    "ExternalServiceException",
    "PacerException",
    "AIServiceException",
    "RateLimitException",
    "ConfigurationException",
    
    # Utilities
    "create_error_response",
    "log_error",
    
    # Exception handlers
    "legal_ai_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
    "EXCEPTION_HANDLERS",
]