"""
Backend Monitoring Dashboard
Admin-only interface for real-time system monitoring
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(prefix="/admin", tags=["Backend Monitor"])


# Simple admin check (in production, use proper authentication)
async def verify_admin(request: Request):
    """
    Verify admin access
    In development: No authentication required
    In production: Requires admin JWT token
    """
    environment = os.getenv('ENVIRONMENT', 'development')

    if environment == 'production':
        # Check for admin token in Authorization header
        auth_header = request.headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Admin access only."
            )

        # In production, validate JWT token here
        # For now, just check if token exists
        token = auth_header.replace('Bearer ', '')
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

    # In development, allow access
    return True


@router.get("/backend-monitor", response_class=HTMLResponse)
async def backend_monitor(
    request: Request,
    _admin: bool = Depends(verify_admin)
):
    """
    Backend Monitoring Dashboard

    Provides real-time monitoring interface for system administrators.
    This is NOT a user-facing interface - admin access only.

    Features:
    - Live system health status
    - Endpoint performance metrics
    - Document processing monitor
    - Error analytics
    - Cost tracking
    - Real-time logs feed

    Access: Admin only
    Updates: WebSocket (every 2 seconds)
    """
    return templates.TemplateResponse(
        "backend_monitor.html",
        {"request": request}
    )


@router.get("/backend-monitor/report")
async def download_report(
    _admin: bool = Depends(verify_admin)
):
    """Download monitoring report"""
    from ..src.monitoring.metrics_collector import metrics_collector

    report = {
        "timestamp": "2025-10-23T00:00:00Z",
        "system_health": metrics_collector.get_health(),
        "endpoints": [],
        "costs": metrics_collector.get_costs(),
        "errors": metrics_collector.get_recent_errors(limit=100)
    }

    return report
