from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime


class LegalAIException(Exception):
    """Base exception class for Legal AI System."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "LEGAL_AI_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(LegalAIException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(LegalAIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(LegalAIException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class DocumentProcessingError(LegalAIException):
    """Raised when document processing fails."""
    
    def __init__(self, message: str, document_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.document_id = document_id
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", details)


class AIServiceError(LegalAIException):
    """Raised when AI service integration fails."""
    
    def __init__(self, message: str, service: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.service = service
        super().__init__(message, "AI_SERVICE_ERROR", details)


class DatabaseError(LegalAIException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        super().__init__(message, "DATABASE_ERROR", details)


class StorageError(LegalAIException):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.file_path = file_path
        super().__init__(message, "STORAGE_ERROR", details)


class RateLimitError(LegalAIException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", {"retry_after": retry_after})


class ConfigurationError(LegalAIException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.config_key = config_key
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ExternalServiceError(LegalAIException):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service: Optional[str] = None, status_code: Optional[int] = None):
        self.service = service
        self.status_code = status_code
        details = {"service": service, "status_code": status_code}
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


async def legal_ai_exception_handler(request: Request, exc: LegalAIException) -> JSONResponse:
    """Handle custom LegalAI exceptions."""
    
    logger = logging.getLogger("legal_ai.exceptions")
    
    # Log the exception with context
    logger.error(
        f"LegalAI Exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "request_url": str(request.url),
            "request_method": request.method,
            "client_ip": request.client.host if request.client else None
        },
        exc_info=True
    )
    
    # Determine HTTP status code based on exception type
    status_code_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "RATE_LIMIT_ERROR": status.HTTP_429_TOO_MANY_REQUESTS,
        "DOCUMENT_PROCESSING_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "AI_SERVICE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "STORAGE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
    }
    
    status_code = status_code_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Prepare response
    response_data = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat(),
            "details": exc.details
        }
    }
    
    # Add retry_after header for rate limit errors
    headers = {}
    if isinstance(exc, RateLimitError) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=status_code,
        content=response_data,
        headers=headers
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    
    logger = logging.getLogger("legal_ai.exceptions")
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "request_url": str(request.url),
            "request_method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    response_data = {
        "error": {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    
    logger = logging.getLogger("legal_ai.exceptions")
    
    logger.error(
        f"Unexpected exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "request_url": str(request.url),
            "request_method": request.method,
            "client_ip": request.client.host if request.client else None
        },
        exc_info=True
    )
    
    response_data = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )