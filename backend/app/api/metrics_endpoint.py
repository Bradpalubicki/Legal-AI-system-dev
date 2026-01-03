# =============================================================================
# Legal AI System - Metrics API Endpoint
# =============================================================================
# FastAPI endpoint for exposing Prometheus metrics
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import logging
from typing import Optional
import os

from app.monitoring import generate_metrics_response
from app.core.config import get_settings

router = APIRouter()
security = HTTPBasic()
settings = get_settings()

logger = logging.getLogger(__name__)

def authenticate_metrics_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate metrics endpoint access."""
    is_correct_username = secrets.compare_digest(
        credentials.username, 
        os.getenv("METRICS_USERNAME", "legal-ai-monitoring")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password,
        os.getenv("METRICS_PASSWORD", "changeme")
    )
    
    if not (is_correct_username and is_correct_password):
        logger.warning(f"Unauthorized metrics access attempt from username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

@router.get(
    "/metrics",
    response_class=Response,
    summary="Prometheus Metrics Endpoint",
    description="Expose Prometheus metrics for Legal AI System monitoring",
    tags=["monitoring"]
)
async def get_metrics(username: str = Depends(authenticate_metrics_user)):
    """
    Get Prometheus metrics for Legal AI System.
    
    This endpoint exposes all application metrics in Prometheus format,
    including legal-specific compliance and audit metrics.
    
    Authentication required with basic auth:
    - Username: legal-ai-monitoring
    - Password: configured via METRICS_PASSWORD environment variable
    
    Returns:
        Response: Prometheus metrics in text format
    """
    try:
        logger.debug(f"Metrics requested by user: {username}")
        content, content_type = generate_metrics_response()
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        logger.error(f"Error generating metrics response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate metrics"
        )

@router.get(
    "/health/metrics",
    summary="Metrics Endpoint Health Check",
    description="Health check for metrics collection system",
    tags=["monitoring", "health"]
)
async def metrics_health():
    """
    Health check for metrics collection system.
    
    Returns basic health status without requiring authentication.
    
    Returns:
        dict: Health status information
    """
    try:
        # Try to generate metrics to verify system is working
        content, content_type = generate_metrics_response()
        
        return {
            "status": "healthy",
            "metrics_available": True,
            "content_type": content_type,
            "metrics_size": len(content) if content else 0
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        return {
            "status": "unhealthy",
            "metrics_available": False,
            "error": str(e)
        }

# Example usage in main FastAPI app:
# from app.api.metrics_endpoint import router as metrics_router
# app.include_router(metrics_router, prefix="/api/v1")