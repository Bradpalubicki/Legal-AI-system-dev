"""
Legal AI System - Main FastAPI Application

Main FastAPI application entry point that initializes the app with all routers,
middleware, exception handlers, and startup/shutdown events.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import configuration and core modules
from src.core.config import settings
from src.core.exceptions import (
    LegalAIException,
    legal_ai_exception_handler,
    http_exception_handler,
    general_exception_handler
)
# Try to import health checker, fall back to basic implementation if dependencies missing
try:
    from src.core.health import health_checker
    HEALTH_CHECKER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Health checker not available due to missing dependencies: {e}")
    HEALTH_CHECKER_AVAILABLE = False

    # Simple fallback health checker
    class SimpleHealthChecker:
        async def check_all_services(self):
            from datetime import datetime
            class SimpleHealth:
                def __init__(self):
                    self.status = "healthy"
                    self.timestamp = datetime.utcnow()
                    self.uptime_seconds = time.time() - app_state.get("start_time", time.time())
                    self.services = []
            return SimpleHealth()

    health_checker = SimpleHealthChecker()
# Try to import logging setup, fall back to basic logging if not available
try:
    from src.core.logging import setup_logging
except ImportError:
    print("Warning: Custom logging setup not available, using basic logging")
    def setup_logging():
        logging.basicConfig(level=logging.INFO)

# Import routers - with error handling for missing modules
# Import the new API routers
from src.api.document_processing import router as doc_processing_router
from src.api.bankruptcy import router as bankruptcy_router

# Start with just the working PACER router for initial testing
routers_to_import = [
    ("src.pacer_gateway.router", "router", "pacer_router", "PACER Gateway"),
    # ("src.document_processor.processing_api", "router", "document_processing_router", "Document Processing"),
    # ("src.transcript_analyzer.search_api", "router", "transcript_search_router", "Transcript Analysis"),
    # ("src.unified_search.unified_search_api", "router", "unified_search_router", "Unified Search"),
    # ("src.research_integration.research_api", "router", "research_router", "Legal Research"),
    # ("src.billing.api_endpoints", "router", "billing_router", "Billing"),
    # ("src.e_filing.api_endpoints", "router", "e_filing_router", "E-Filing"),
    # ("src.e_filing.compliance.compliance_api", "router", "compliance_router", "Compliance"),
    # ("src.mobile_api.api_endpoints", "router", "mobile_router", "Mobile API"),
]

loaded_routers = []
for module_path, attr_name, var_name, display_name in routers_to_import:
    try:
        import importlib
        module = importlib.import_module(module_path)
        router = getattr(module, attr_name)
        loaded_routers.append((router, var_name, display_name))
    except ImportError as e:
        print(f"Warning: Could not import {display_name} router from {module_path}: {e}")
    except AttributeError as e:
        print(f"Warning: {display_name} router not found in {module_path}: {e}")
    except Exception as e:
        print(f"Warning: Error loading {display_name} router: {e}")


# Application state
app_state = {
    "start_time": None,
    "logger": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""

    # Startup
    app_state["start_time"] = time.time()

    # Setup logging
    setup_logging()
    logger = logging.getLogger("legal_ai.main")
    app_state["logger"] = logger

    logger.info(f"Starting Legal AI System v{settings.APP_VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"API prefix: {settings.API_V1_STR}")

    # Initialize health checker
    try:
        health_status = await health_checker.check_all_services()
        if HEALTH_CHECKER_AVAILABLE:
            logger.info(f"Health check complete - Status: {health_status.status}")
            # Log service statuses
            for service in health_status.services:
                logger.info(f"Service {service.name}: {service.status}")
        else:
            logger.info(f"Basic health check complete - Status: {health_status.status}")

    except Exception as exc:
        logger.error(f"Health check failed during startup: {exc}")

    logger.info("Legal AI System startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Legal AI System")

    # Cleanup tasks could go here
    # e.g., close database connections, cleanup temp files, etc.

    uptime = time.time() - app_state["start_time"]
    logger.info(f"Legal AI System shutdown complete. Uptime: {uptime:.2f} seconds")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive AI-powered legal document analysis and research system",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.legal-ai.com"]
    )

# Exception handlers
app.add_exception_handler(LegalAIException, legal_ai_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Health check endpoint (mounted at root level)
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Application health check endpoint.

    Returns the overall health status of the application and all its dependencies.
    """
    try:
        health_status = await health_checker.check_all_services()

        if HEALTH_CHECKER_AVAILABLE:
            return {
                "status": health_status.status.value,
                "timestamp": health_status.timestamp.isoformat(),
                "uptime_seconds": health_status.uptime_seconds,
                "services": [
                    {
                        "name": service.name,
                        "status": service.status.value,
                        "response_time_ms": service.response_time_ms,
                        "last_check": service.last_check.isoformat(),
                        "details": service.details
                    }
                    for service in health_status.services
                ],
                "version": settings.APP_VERSION,
                "environment": "development" if settings.DEBUG else "production"
            }
        else:
            return {
                "status": health_status.status,
                "timestamp": health_status.timestamp.isoformat(),
                "uptime_seconds": health_status.uptime_seconds,
                "services": health_status.services,
                "version": settings.APP_VERSION,
                "environment": "development" if settings.DEBUG else "production",
                "note": "Running with simplified health checker"
            }

    except Exception as exc:
        logger = app_state.get("logger") or logging.getLogger("legal_ai.main")
        logger.error(f"Health check failed: {exc}")

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check failed",
                "version": settings.APP_VERSION
            }
        )


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint with basic application information.
    """
    uptime = time.time() - app_state["start_time"] if app_state["start_time"] else 0

    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "uptime_seconds": uptime,
        "api_docs": "/docs",
        "health_check": "/health",
        "api_prefix": settings.API_V1_STR,
        "timestamp": datetime.utcnow().isoformat()
    }


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests for monitoring and debugging."""
    start_time = time.time()

    # Log request
    logger = app_state.get("logger") or logging.getLogger("legal_ai.requests")
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    )

    # Process request
    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} - {process_time:.4f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time,
            "method": request.method,
            "path": request.url.path
        }
    )

    return response


# Mount API routers
api_prefix = settings.API_V1_STR

# Router path mapping
router_paths = {
    "pacer_router": "/pacer",
    "document_processing_router": "/documents",
    "transcript_search_router": "/transcripts",
    "unified_search_router": "/search",
    "research_router": "/research",
    "billing_router": "/billing",
    "e_filing_router": "/e-filing",
    "compliance_router": "/compliance",
    "mobile_router": "/mobile"
}

# Mount all successfully loaded routers
for router, var_name, display_name in loaded_routers:
    path_suffix = router_paths.get(var_name, f"/{var_name.replace('_router', '')}")
    try:
        app.include_router(
            router,
            prefix=f"{api_prefix}{path_suffix}",
            tags=[display_name]
        )
        print(f"[OK] Mounted {display_name} router at {api_prefix}{path_suffix}")
    except Exception as e:
        print(f"[ERROR] Failed to mount {display_name} router: {e}")

# Mount the new API routers with consistent API prefix
app.include_router(doc_processing_router, prefix=f'{api_prefix}/document-processing', tags=['Document Processing'])
print(f"[OK] Mounted Document Processing router at {api_prefix}/document-processing")
app.include_router(bankruptcy_router, prefix=f'{api_prefix}/bankruptcy', tags=['Bankruptcy'])
print(f"[OK] Mounted Bankruptcy router at {api_prefix}/bankruptcy")


if __name__ == "__main__":
    """
    Development server entry point.

    Run with: python -m uvicorn src.core.main:app --reload --port 8001
    """
    uvicorn.run(
        "src.core.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD or settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )