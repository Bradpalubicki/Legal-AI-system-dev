"""
Audit Logging API Endpoints

Provides endpoints for querying audit logs and security alerts.
Admin-only access for security monitoring and compliance reporting.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from ..src.core.database import get_db
from ..src.core.security.audit_logging import (
    AuditLog,
    SecurityAlert,
    AuditEventType,
    AuditSeverity,
    AuditQuery,
    SecurityAlertManager,
)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

# =============================================================================
# RESPONSE MODELS
# =============================================================================

class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    id: int
    event_type: str
    severity: str
    user_id: Optional[int]
    username: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    description: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityAlertResponse(BaseModel):
    """Security alert response"""
    id: int
    alert_type: str
    severity: str
    title: str
    description: Optional[str]
    user_id: Optional[int]
    ip_address: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AlertUpdateRequest(BaseModel):
    """Request to update alert status"""
    status: str
    resolution: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def require_admin(request):
    """Check if user is admin"""
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if not request.state.user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return request.state.user


# =============================================================================
# AUDIT LOG ENDPOINTS
# =============================================================================

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    request,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get audit logs with filtering.

    Admin only. Returns filtered audit log entries.

    Args:
        event_type: Filter by event type
        user_id: Filter by user ID
        resource_type: Filter by resource type
        severity: Filter by severity
        start_date: Start date filter
        end_date: End date filter
        limit: Maximum results (max 1000)
        offset: Pagination offset

    Returns:
        List of audit log entries
    """
    require_admin(request)

    # Build query
    query = db.query(AuditLog)

    if event_type:
        query = query.filter(AuditLog.event_type == event_type)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    if severity:
        query = query.filter(AuditLog.severity == severity)

    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    # Order by most recent first
    query = query.order_by(AuditLog.created_at.desc())

    # Paginate
    logs = query.offset(offset).limit(limit).all()

    return logs


@router.get("/logs/{log_id}")
async def get_audit_log(
    request,
    log_id: int,
    db: Session = Depends(get_db),
):
    """
    Get specific audit log entry with full details.

    Args:
        log_id: Audit log ID

    Returns:
        Full audit log entry including metadata
    """
    require_admin(request)

    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    return {
        "id": log.id,
        "event_type": log.event_type,
        "severity": log.severity,
        "user_id": log.user_id,
        "username": log.username,
        "user_email": log.user_email,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "action": log.action,
        "description": log.description,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "request_id": log.request_id,
        "session_id": log.session_id,
        "metadata": log.metadata,
        "old_values": log.old_values,
        "new_values": log.new_values,
        "created_at": log.created_at.isoformat(),
        "is_compliance_event": bool(log.is_compliance_event),
        "retention_until": log.retention_until.isoformat() if log.retention_until else None,
    }


@router.get("/user/{user_id}/activity")
async def get_user_activity(
    request,
    user_id: int,
    days: int = Query(30, le=365),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get user activity history.

    Args:
        user_id: User ID
        days: Number of days to look back
        limit: Maximum results

    Returns:
        User's recent activity
    """
    require_admin(request)

    start_date = datetime.utcnow() - timedelta(days=days)

    logs = AuditQuery.get_user_activity(
        db=db,
        user_id=user_id,
        start_date=start_date,
        limit=limit,
    )

    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/resource/{resource_type}/{resource_id}/history")
async def get_resource_history(
    request,
    resource_type: str,
    resource_id: str,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get full history of a resource.

    Tracks all changes and access to a specific resource.

    Args:
        resource_type: Type of resource (document, user, etc.)
        resource_id: Resource identifier
        limit: Maximum results

    Returns:
        Resource modification history
    """
    require_admin(request)

    logs = AuditQuery.get_resource_history(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
    )

    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "action": log.action,
            "user_id": log.user_id,
            "username": log.username,
            "description": log.description,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/compliance")
async def get_compliance_logs(
    request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """
    Get compliance-related audit logs.

    For compliance reporting and audits.

    Args:
        start_date: Start date filter
        end_date: End date filter

    Returns:
        Compliance event logs
    """
    require_admin(request)

    logs = AuditQuery.get_compliance_events(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )

    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "user_id": log.user_id,
            "username": log.username,
            "description": log.description,
            "metadata": log.metadata,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


# =============================================================================
# SECURITY ALERT ENDPOINTS
# =============================================================================

@router.get("/alerts", response_model=List[SecurityAlertResponse])
async def get_security_alerts(
    request,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get security alerts.

    Args:
        status: Filter by status (new, investigating, resolved, false_positive)
        severity: Filter by severity
        limit: Maximum results

    Returns:
        List of security alerts
    """
    require_admin(request)

    query = db.query(SecurityAlert)

    if status:
        query = query.filter(SecurityAlert.status == status)

    if severity:
        query = query.filter(SecurityAlert.severity == severity)

    alerts = query.order_by(
        SecurityAlert.created_at.desc()
    ).limit(limit).all()

    return alerts


@router.get("/alerts/{alert_id}")
async def get_security_alert(
    request,
    alert_id: int,
    db: Session = Depends(get_db),
):
    """
    Get specific security alert with full details.

    Args:
        alert_id: Alert ID

    Returns:
        Full alert details
    """
    require_admin(request)

    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "user_id": alert.user_id,
        "ip_address": alert.ip_address,
        "audit_log_id": alert.audit_log_id,
        "metadata": alert.metadata,
        "status": alert.status,
        "assigned_to": alert.assigned_to,
        "investigated_at": alert.investigated_at.isoformat() if alert.investigated_at else None,
        "resolution": alert.resolution,
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat(),
    }


@router.patch("/alerts/{alert_id}")
async def update_alert(
    request,
    alert_id: int,
    update: AlertUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update security alert status.

    Args:
        alert_id: Alert ID
        update: Status update

    Returns:
        Updated alert
    """
    admin = require_admin(request)

    alert = SecurityAlertManager.update_alert_status(
        db=db,
        alert_id=alert_id,
        status=update.status,
        assigned_to=admin['id'],
        resolution=update.resolution,
    )

    return {
        "success": True,
        "alert_id": alert.id,
        "status": alert.status,
        "message": f"Alert status updated to: {alert.status}"
    }


# =============================================================================
# SECURITY STATISTICS
# =============================================================================

@router.get("/stats/failed-logins")
async def get_failed_login_stats(
    request,
    hours: int = Query(24, le=168),
    threshold: int = Query(5, le=100),
    db: Session = Depends(get_db),
):
    """
    Get IPs with excessive failed login attempts.

    Args:
        hours: Time window in hours
        threshold: Minimum failed attempts to report

    Returns:
        IP addresses with failed login counts
    """
    require_admin(request)

    failed_logins = AuditQuery.get_failed_logins(
        db=db,
        hours=hours,
        threshold=threshold,
    )

    return {
        "time_window_hours": hours,
        "threshold": threshold,
        "suspicious_ips": [
            {"ip_address": ip, "failed_attempts": count}
            for ip, count in failed_logins.items()
        ]
    }


@router.get("/stats/summary")
async def get_audit_summary(
    request,
    days: int = Query(7, le=90),
    db: Session = Depends(get_db),
):
    """
    Get audit log summary statistics.

    Args:
        days: Number of days to analyze

    Returns:
        Summary statistics
    """
    require_admin(request)

    from sqlalchemy import func

    start_date = datetime.utcnow() - timedelta(days=days)

    # Total events
    total_events = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= start_date
    ).scalar()

    # Events by type
    events_by_type = db.query(
        AuditLog.event_type,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.event_type).all()

    # Events by severity
    events_by_severity = db.query(
        AuditLog.severity,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.severity).all()

    # Active alerts
    active_alerts = db.query(func.count(SecurityAlert.id)).filter(
        SecurityAlert.status.in_(['new', 'investigating'])
    ).scalar()

    return {
        "period_days": days,
        "total_events": total_events,
        "events_by_type": {et: count for et, count in events_by_type},
        "events_by_severity": {sev: count for sev, count in events_by_severity},
        "active_security_alerts": active_alerts,
    }


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@router.get("/export")
async def export_audit_logs(
    request,
    start_date: datetime,
    end_date: datetime,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
):
    """
    Export audit logs for compliance reporting.

    Args:
        start_date: Start date
        end_date: End date
        format: Export format (json or csv)

    Returns:
        Exported audit logs
    """
    require_admin(request)

    logs = db.query(AuditLog).filter(
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date,
    ).order_by(AuditLog.created_at).all()

    if format == "json":
        return {
            "export_date": datetime.utcnow().isoformat(),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_records": len(logs),
            "logs": [
                {
                    "id": log.id,
                    "timestamp": log.created_at.isoformat(),
                    "event_type": log.event_type,
                    "severity": log.severity,
                    "user_id": log.user_id,
                    "username": log.username,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "action": log.action,
                    "description": log.description,
                    "ip_address": log.ip_address,
                }
                for log in logs
            ]
        }
    else:  # CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Timestamp', 'Event Type', 'Severity', 'User ID',
            'Username', 'Resource Type', 'Resource ID', 'Action',
            'Description', 'IP Address'
        ])

        # Write data
        for log in logs:
            writer.writerow([
                log.id,
                log.created_at.isoformat(),
                log.event_type,
                log.severity,
                log.user_id or '',
                log.username or '',
                log.resource_type or '',
                log.resource_id or '',
                log.action,
                log.description or '',
                log.ip_address or '',
            ])

        from fastapi.responses import StreamingResponse

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{start_date.date()}_{end_date.date()}.csv"
            }
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['router']
