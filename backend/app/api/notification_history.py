"""
Notification History API Endpoints
View and manage notification history for monitored cases
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.src.core.database import get_db
from app.models.case_notification_history import CaseNotification
from app.api.deps import get_optional_user

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/history")
async def get_notification_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    docket_id: Optional[int] = Query(None, description="Filter by docket ID"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    days: Optional[int] = Query(None, ge=1, le=90, description="Filter by last N days"),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """
    Get notification history with pagination and filtering

    Query parameters:
    - skip: Number of records to skip for pagination
    - limit: Maximum number of records to return (1-100)
    - docket_id: Filter by specific case
    - notification_type: Filter by type (e.g., 'new_documents')
    - days: Filter by notifications sent in last N days (1-90)
    """
    query = db.query(CaseNotification)

    # Apply filters
    if docket_id:
        query = query.filter(CaseNotification.docket_id == docket_id)

    if notification_type:
        query = query.filter(CaseNotification.notification_type == notification_type)

    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(CaseNotification.sent_at >= cutoff_date)

    # Get all matching notifications ordered by sent_at
    all_notifications = query.order_by(desc(CaseNotification.sent_at)).all()

    # Filter by current user if authenticated (prevents seeing other users' notifications)
    if current_user:
        user_id = str(current_user.user_id)
        all_notifications = [
            n for n in all_notifications
            if n.extra_data and str(n.extra_data.get('user_id')) == user_id
        ]

    # Get total count after user filtering
    total = len(all_notifications)

    # Apply pagination
    notifications = all_notifications[skip:skip + limit]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "notifications": [n.to_dict() for n in notifications]
    }


@router.get("/history/{notification_id}")
async def get_notification_by_id(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific notification by ID"""
    notification = db.query(CaseNotification).filter(CaseNotification.id == notification_id).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification.to_dict()


@router.get("/history/case/{docket_id}")
async def get_notifications_by_case(
    docket_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get all notifications for a specific case"""
    query = db.query(CaseNotification).filter(CaseNotification.docket_id == docket_id)
    all_notifications = query.order_by(desc(CaseNotification.sent_at)).all()

    # Filter by current user if authenticated
    if current_user:
        user_id = str(current_user.user_id)
        all_notifications = [
            n for n in all_notifications
            if n.extra_data and str(n.extra_data.get('user_id')) == user_id
        ]

    total = len(all_notifications)
    notifications = all_notifications[skip:skip + limit]

    return {
        "docket_id": docket_id,
        "total": total,
        "skip": skip,
        "limit": limit,
        "notifications": [n.to_dict() for n in notifications]
    }


@router.get("/stats")
async def get_notification_stats(
    days: int = Query(7, ge=1, le=90, description="Statistics for last N days"),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """
    Get notification statistics for the current user.

    Returns:
    - Total notifications sent
    - WebSocket success rate
    - Email success rate
    - Notifications by type
    - Recent activity
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get all notifications in the time period
    all_notifications = db.query(CaseNotification).filter(
        CaseNotification.sent_at >= cutoff_date
    ).all()

    # Filter by current user if authenticated
    if current_user:
        user_id = str(current_user.user_id)
        notifications = [
            n for n in all_notifications
            if n.extra_data and str(n.extra_data.get('user_id')) == user_id
        ]
    else:
        notifications = all_notifications

    total_count = len(notifications)

    if total_count == 0:
        return {
            "days": days,
            "total_notifications": 0,
            "websocket_success_rate": 0,
            "email_success_rate": 0,
            "total_documents_notified": 0,
            "by_type": {},
            "recent_cases": []
        }

    websocket_sent = sum(1 for n in notifications if n.websocket_sent)
    email_sent = sum(1 for n in notifications if n.email_sent)
    total_documents = sum(n.document_count for n in notifications)

    # Group by type
    by_type = {}
    for n in notifications:
        type_key = n.notification_type or "unknown"
        by_type[type_key] = by_type.get(type_key, 0) + 1

    # Get recent unique cases
    case_dict = {}
    for n in notifications:
        if n.docket_id not in case_dict:
            case_dict[n.docket_id] = {
                "docket_id": n.docket_id,
                "case_name": n.case_name,
                "last_notification": n.sent_at.isoformat() if n.sent_at else None,
                "notification_count": 0
            }
        case_dict[n.docket_id]["notification_count"] += 1

    recent_cases = sorted(
        case_dict.values(),
        key=lambda x: x["last_notification"],
        reverse=True
    )[:10]

    return {
        "days": days,
        "total_notifications": total_count,
        "websocket_success_rate": round(websocket_sent / total_count * 100, 1) if total_count > 0 else 0,
        "email_success_rate": round(email_sent / total_count * 100, 1) if total_count > 0 else 0,
        "total_documents_notified": total_documents,
        "by_type": by_type,
        "recent_cases": recent_cases
    }


@router.delete("/history/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific notification from history"""
    notification = db.query(CaseNotification).filter(CaseNotification.id == notification_id).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()

    return {"success": True, "message": "Notification deleted"}


@router.delete("/history/case/{docket_id}")
async def delete_case_notifications(
    docket_id: int,
    db: Session = Depends(get_db)
):
    """Delete all notifications for a specific case"""
    count = db.query(CaseNotification).filter(CaseNotification.docket_id == docket_id).count()

    if count == 0:
        raise HTTPException(status_code=404, detail="No notifications found for this case")

    db.query(CaseNotification).filter(CaseNotification.docket_id == docket_id).delete()
    db.commit()

    return {"success": True, "message": f"Deleted {count} notifications"}
