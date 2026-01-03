"""
Case Notification WebSocket API
Real-time notifications for monitored case updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import logging

from app.src.core.database import get_db
from app.services.case_monitor_service import case_monitor_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.websocket("/ws")
async def case_notifications_websocket(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time case notification updates

    Sends notifications when:
    - New documents are filed in monitored cases
    - Document processing is complete
    - Auto-download finishes

    Message format:
    {
        "type": "new_documents",
        "timestamp": "2025-11-12T19:00:00",
        "docket_id": 69566447,
        "case_name": "Case Name",
        "document_count": 5,
        "documents": [...],  # Preview of new documents
        "total_new": 5
    }
    """
    await websocket.accept()
    case_monitor_service.register_websocket(websocket)

    logger.info("Case notification WebSocket client connected")

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to case notification service",
            "poll_interval": case_monitor_service.poll_interval
        })

        # Keep connection alive and listen for client messages
        while True:
            # Receive messages from client (e.g., ping/pong, manual refresh requests)
            data = await websocket.receive_json()

            # Handle client requests
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            elif data.get("type") == "check_now":
                # Manual check request from client
                logger.info("Manual check requested by client")
                await case_monitor_service.check_monitored_cases(db)
                await websocket.send_json({
                    "type": "check_complete",
                    "message": "Manual check completed"
                })

    except WebSocketDisconnect:
        logger.info("Case notification WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        case_monitor_service.unregister_websocket(websocket)


@router.post("/check-now")
async def trigger_manual_check(db: Session = Depends(get_db)):
    """
    Manually trigger a check for new documents in monitored cases
    """
    try:
        await case_monitor_service.check_monitored_cases(db)
        return {
            "success": True,
            "message": "Check initiated successfully"
        }
    except Exception as e:
        logger.error(f"Error triggering manual check: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/status")
async def get_monitor_status():
    """
    Get status of the monitoring service
    """
    return {
        "running": case_monitor_service.running,
        "poll_interval": case_monitor_service.poll_interval,
        "connected_clients": len(case_monitor_service.websocket_clients)
    }


@router.post("/poll-interval")
async def set_poll_interval(interval_seconds: int):
    """
    Set how often the service checks for updates (minimum 60 seconds)
    """
    case_monitor_service.set_poll_interval(interval_seconds)
    return {
        "success": True,
        "poll_interval": case_monitor_service.poll_interval
    }
