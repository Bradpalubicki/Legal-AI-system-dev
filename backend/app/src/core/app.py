"""
Core FastAPI Application Factory for Legal AI System

Creates and configures the FastAPI application with all middleware,
error handlers, routers, and lifecycle events.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .config import get_settings
from .database import init_database, close_database
from .exceptions import EXCEPTION_HANDLERS
from .middleware import configure_middleware
from .health import router as health_router
from .logging import configure_logging, app_logger

# Import document processing router
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../src'))
from api.document_processing import router as document_processing_router
from api.bankruptcy import router as bankruptcy_router

settings = get_settings()


# =============================================================================
# APPLICATION LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup events
    app_logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    app_logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Initialize database
        app_logger.info("Initializing database...")
        await init_database()
        app_logger.info("Database initialized successfully")
        
        # Initialize other services
        await initialize_services()
        app_logger.info("All services initialized successfully")
        
        # Set application state
        app.state.startup_time = datetime.now(timezone.utc)
        app.state.health_status = "healthy"
        
        app_logger.info(f"{settings.APP_NAME} startup completed successfully")
        
    except Exception as exc:
        app_logger.critical(f"Startup failed: {exc}", exc_info=True)
        raise
    
    yield
    
    # Shutdown events
    app_logger.info(f"Shutting down {settings.APP_NAME}...")
    
    try:
        # Close database connections
        app_logger.info("Closing database connections...")
        await close_database()
        app_logger.info("Database connections closed")
        
        # Cleanup other services
        await cleanup_services()
        app_logger.info("Services cleanup completed")
        
        app_logger.info(f"{settings.APP_NAME} shutdown completed successfully")
        
    except Exception as exc:
        app_logger.error(f"Shutdown error: {exc}", exc_info=True)


async def initialize_services():
    """Initialize additional services during startup"""
    
    # Initialize Redis connections
    app_logger.info("Initializing Redis connections...")
    # TODO: Add Redis initialization
    
    # Initialize external service clients
    app_logger.info("Initializing external service clients...")
    # TODO: Add PACER, AI service clients initialization
    
    # Initialize background task workers
    app_logger.info("Initializing background task workers...")
    # TODO: Add Celery worker initialization
    
    # Load ML models if needed
    if settings.ENVIRONMENT != 'testing':
        app_logger.info("Loading ML models...")
        # TODO: Add ML model loading


async def cleanup_services():
    """Cleanup services during shutdown"""
    
    # Close Redis connections
    app_logger.info("Closing Redis connections...")
    # TODO: Add Redis cleanup
    
    # Close external service clients
    app_logger.info("Closing external service clients...")
    # TODO: Add external service cleanup
    
    # Stop background task workers
    app_logger.info("Stopping background task workers...")
    # TODO: Add Celery worker cleanup


# =============================================================================
# SENTRY INTEGRATION
# =============================================================================

def configure_sentry():
    """Configure Sentry error tracking"""
    if settings.SENTRY_ENABLED and settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=True),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            attach_stacktrace=True,
            send_default_pii=False,  # Important for legal data privacy
            before_send=filter_sensitive_data,
            release=settings.APP_VERSION
        )
        app_logger.info("Sentry error tracking configured")


def filter_sensitive_data(event, hint):
    """Filter sensitive data from Sentry events"""
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            event['request']['headers'].pop(header.lower(), None)
    
    # Remove sensitive form data
    if 'request' in event and 'data' in event['request']:
        sensitive_fields = ['password', 'token', 'secret', 'key']
        if isinstance(event['request']['data'], dict):
            for field in sensitive_fields:
                if field in event['request']['data']:
                    event['request']['data'][field] = '[Filtered]'
    
    return event


# =============================================================================
# CUSTOM OPENAPI SCHEMA
# =============================================================================

def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with additional metadata"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        routes=app.routes,
        servers=[
            {"url": settings.API_BASE_URL, "description": "Main API server"}
        ]
    )
    
    # Add custom information
    openapi_schema["info"].update({
        "contact": {
            "name": "Legal AI System Support",
            "email": "support@legalai.com",
            "url": "https://legalai.com/support"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        "termsOfService": "https://legalai.com/terms"
    })
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "apiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"bearerAuth": []},
        {"apiKey": []}
    ]
    
    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "auth",
            "description": "Authentication and authorization endpoints"
        },
        {
            "name": "dockets",
            "description": "Legal docket tracking and management"
        },
        {
            "name": "documents",
            "description": "Document processing and analysis"
        },
        {
            "name": "tasks",
            "description": "Background task management"
        },
        {
            "name": "ai",
            "description": "AI-powered legal analysis endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Configure logging first
    configure_logging()
    
    # Configure Sentry if enabled
    configure_sentry()
    
    # Create FastAPI application
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None
    )
    
    # Configure middleware
    configure_middleware(app)
    
    # Add exception handlers
    for exception_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_class, handler)
    
    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(document_processing_router, prefix="/api/document-processing", tags=["documents"])
    app.include_router(bankruptcy_router, prefix="/api/bankruptcy", tags=["bankruptcy"])

    # TODO: Add other routers
    # app.include_router(auth_router, prefix="/auth", tags=["auth"])
    # app.include_router(dockets_router, prefix="/api/v1/dockets", tags=["dockets"])
    # app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
    # app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])
    
    # Mount static files in development
    if settings.ENVIRONMENT == "development":
        try:
            app.mount("/static", StaticFiles(directory="static"), name="static")
        except RuntimeError:
            # Static directory doesn't exist, skip mounting
            pass
    
    # Set custom OpenAPI schema
    app.openapi = lambda: custom_openapi_schema(app)
    
    # Add root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint with API information"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION,
            "environment": settings.ENVIRONMENT,
            "status": "online",
            "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
            "health_check": "/health"
        }
    
    # Add favicon endpoint to prevent 404s
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Favicon endpoint"""
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})
    
    app_logger.info("FastAPI application created and configured")
    return app


# =============================================================================
# DEVELOPMENT SERVER
# =============================================================================

def create_dev_app() -> FastAPI:
    """Create application with development-specific configurations"""
    import os
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DEBUG", "true")
    
    return create_application()


# =============================================================================
# APPLICATION INSTANCE
# =============================================================================

# Create the application instance
app = create_application()

# Add development-specific configurations
if settings.ENVIRONMENT == "development":
    
    @app.middleware("http")
    async def add_dev_headers(request: Request, call_next):
        """Add development-specific headers"""
        response = await call_next(request)
        response.headers["X-Dev-Mode"] = "true"
        response.headers["X-Debug"] = str(settings.DEBUG)
        return response
    
    app_logger.info("Development mode configurations applied")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "app",
    "create_application",
    "create_dev_app",
    "lifespan"
]


# Import datetime for lifespan function
from datetime import datetime, timezone