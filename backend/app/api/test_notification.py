"""
Test endpoint for notification system
"""
from fastapi import APIRouter
from datetime import datetime

from app.services.case_monitor_service import case_monitor_service

router = APIRouter(prefix="/api/v1/test", tags=["test"])


@router.post("/send-test-notification")
async def send_test_notification():
    """
    Send a test notification through WebSocket to demonstrate the notification system.
    """
    # Create a test notification
    test_notification = {
        "type": "new_documents",
        "timestamp": datetime.utcnow().isoformat(),
        "docket_id": 69566281,
        "case_name": "NUMALE CORPORATION",
        "document_count": 1,
        "documents": [{
            "document_number": 17,
            "short_description": "Test Document - Filed 11/12/2025",
            "description": "This is a test notification to demonstrate the real-time notification system",
            "is_available": True
        }],
        "total_new": 1
    }

    # Broadcast to all connected WebSocket clients
    await case_monitor_service.broadcast_notification(test_notification)

    return {
        "success": True,
        "message": "Test notification sent to all connected clients",
        "notification": test_notification
    }
