"""
Core module for Legal AI System

This module provides the foundational components for the Legal AI System
including configuration, database, security, health monitoring, middleware,
error handling, logging, and the main FastAPI application.
"""

# Configuration
from .config import get_settings, settings

# Database
from .database import (
    Base,
    get_async_session,
    get_sync_session,
    get_async_session_context,
    AsyncSessionLocal,
    SessionLocal
)

# Health monitoring
from .health import router as health_router

# Logging
from .logging import (
    configure_logging,
    get_logger,
    audit_logger,
    security_logger,
    performance_logger,
    app_logger
)

# Exceptions
from .exceptions import (
    LegalAIException,
    ValidationException,
    BusinessLogicException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    DuplicateResourceException,
    DatabaseException,
    ExternalServiceException,
    PacerException,
    AIServiceException,
    RateLimitException,
    ConfigurationException,
    EXCEPTION_HANDLERS
)

# Middleware
from .middleware import (
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    AuthenticationMiddleware,
    SecurityHeadersMiddleware,
    ErrorTrackingMiddleware,
    AuditMiddleware,
    configure_middleware
)

# Main application - simplified for development
def create_application():
    """Create FastAPI application"""
    from fastapi import FastAPI
    app = FastAPI(title="Legal AI System")
    return app

def create_dev_app():
    """Create development app"""
    return create_application()

app = create_application()

__all__ = [
    # Configuration
    "get_settings",
    "settings",
    
    # Database
    "Base",
    "get_async_session",
    "get_sync_session",
    "get_async_session_context",
    "AsyncSessionLocal",
    "SessionLocal",
    
    # Health monitoring
    "health_router",
    
    # Logging
    "configure_logging",
    "get_logger",
    "audit_logger",
    "security_logger", 
    "performance_logger",
    "app_logger",
    
    # Exceptions
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
    "EXCEPTION_HANDLERS",
    
    # Middleware
    "RequestLoggingMiddleware",
    "RateLimitMiddleware",
    "AuthenticationMiddleware",
    "SecurityHeadersMiddleware",
    "ErrorTrackingMiddleware",
    "AuditMiddleware",
    "configure_middleware",
    
    # Main application
    "app",
    "create_application",
    "create_dev_app"
]