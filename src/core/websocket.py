"""
WebSocket endpoints for real-time dashboard updates
"""

import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import logging

logger = logging.getLogger(__name__)

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.client_data: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_data[websocket] = {
            "client_id": client_id or f"client_{int(time.time())}",
            "connected_at": datetime.utcnow().isoformat(),
            "subscriptions": ["dashboard", "timeline", "notifications"]
        }
        logger.info(f"WebSocket client connected: {self.client_data[websocket]['client_id']}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.discard(websocket)
            client_info = self.client_data.pop(websocket, {})
            logger.info(f"WebSocket client disconnected: {client_info.get('client_id', 'unknown')}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client"""
        if websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to client: {e}")
                self.disconnect(websocket)

    async def broadcast(self, message: str, subscription_filter: str = None):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections.copy():
            try:
                # Check subscription filter if provided
                if subscription_filter:
                    client_subscriptions = self.client_data.get(connection, {}).get("subscriptions", [])
                    if subscription_filter not in client_subscriptions:
                        continue

                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager instance
manager = ConnectionManager()

# Create router for WebSocket endpoints
websocket_router = APIRouter()

@websocket_router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates"""
    client_id = websocket.query_params.get("client_id")

    await manager.connect(websocket, client_id)

    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "client_id": manager.client_data[websocket]["client_id"],
                "timestamp": datetime.utcnow().isoformat(),
                "subscriptions": manager.client_data[websocket]["subscriptions"]
            }),
            websocket
        )

        # Send initial dashboard data
        initial_data = generate_dashboard_update()
        await manager.send_personal_message(
            json.dumps(initial_data),
            websocket
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (with timeout)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle client messages
                try:
                    data = json.loads(message)
                    await handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client: {message}")

            except asyncio.TimeoutError:
                # Send periodic heartbeat/data updates
                heartbeat = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(json.dumps(heartbeat), websocket)

                # Send data updates every 30 seconds
                update_data = generate_dashboard_update()
                await manager.send_personal_message(json.dumps(update_data), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_client_message(websocket: WebSocket, data: Dict):
    """Handle messages received from WebSocket clients"""
    message_type = data.get("type")
    client_id = manager.client_data.get(websocket, {}).get("client_id")

    logger.info(f"Received message from {client_id}: {message_type}")

    if message_type == "subscribe":
        # Handle subscription updates
        subscriptions = data.get("subscriptions", [])
        if websocket in manager.client_data:
            manager.client_data[websocket]["subscriptions"] = subscriptions

        response = {
            "type": "subscription_updated",
            "subscriptions": subscriptions,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_personal_message(json.dumps(response), websocket)

    elif message_type == "request_data":
        # Handle data requests
        data_type = data.get("data_type", "dashboard")
        update_data = generate_dashboard_update() if data_type == "dashboard" else {}
        await manager.send_personal_message(json.dumps(update_data), websocket)

    elif message_type == "ping":
        # Handle ping/pong
        pong = {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_personal_message(json.dumps(pong), websocket)

def generate_dashboard_update() -> Dict:
    """Generate real-time dashboard data"""
    import random

    return {
        "type": "dashboard_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "documents": {
                "processing": random.randint(1, 8),
                "completed": random.randint(20, 60),
                "failed": random.randint(0, 3),
                "recent_completion": {
                    "document_name": f"Contract_Analysis_{random.randint(1, 100)}.pdf",
                    "processing_time": random.randint(30, 300)
                } if random.random() > 0.7 else None
            },
            "analysis": {
                "in_progress": random.randint(1, 5),
                "completed": random.randint(10, 40),
                "confidence": random.randint(75, 95),
                "latest_insight": {
                    "type": "risk_assessment",
                    "confidence": round(random.uniform(0.7, 0.95), 2),
                    "summary": "New risk factor identified in contract terms"
                } if random.random() > 0.8 else None
            },
            "qa": {
                "pending_responses": random.randint(1, 10),
                "total_sessions": random.randint(15, 35),
                "active_users": random.randint(1, 8),
                "new_question": {
                    "question": "What are the implications of the new regulation?",
                    "priority": random.choice(["high", "medium", "low"])
                } if random.random() > 0.6 else None
            },
            "notifications": {
                "unread": random.randint(1, 15),
                "new_notification": {
                    "title": "Analysis Complete",
                    "message": f"Document analysis finished for Case #{random.randint(1000, 9999)}",
                    "type": random.choice(["info", "success", "warning"]),
                    "timestamp": datetime.utcnow().isoformat()
                } if random.random() > 0.5 else None
            },
            "system": {
                "uptime": round(random.uniform(98.5, 99.9), 1),
                "performance": random.randint(85, 98),
                "errors": random.randint(0, 2),
                "last_update": datetime.utcnow().isoformat()
            }
        }
    }

# Background task for periodic updates
async def periodic_dashboard_updates():
    """Send periodic updates to all connected clients"""
    while True:
        try:
            await asyncio.sleep(10)  # Send updates every 10 seconds

            if manager.active_connections:
                update_data = generate_dashboard_update()
                await manager.broadcast(
                    json.dumps(update_data),
                    subscription_filter="dashboard"
                )

        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")

# Notification broadcasting functions
async def broadcast_notification(notification: Dict):
    """Broadcast a notification to all connected clients"""
    message = {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.broadcast(
        json.dumps(message),
        subscription_filter="notifications"
    )

async def broadcast_document_update(document_id: str, status: str, metadata: Dict = None):
    """Broadcast document processing updates"""
    message = {
        "type": "document_update",
        "data": {
            "document_id": document_id,
            "status": status,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    await manager.broadcast(json.dumps(message))

async def broadcast_analysis_update(analysis_id: str, results: Dict):
    """Broadcast AI analysis completion"""
    message = {
        "type": "analysis_complete",
        "data": {
            "analysis_id": analysis_id,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    await manager.broadcast(json.dumps(message))

async def broadcast_qa_update(session_id: str, question: str, answer: str):
    """Broadcast Q&A session updates"""
    message = {
        "type": "qa_answered",
        "data": {
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    await manager.broadcast(json.dumps(message))

# Export the router and utility functions
__all__ = [
    "websocket_router",
    "manager",
    "broadcast_notification",
    "broadcast_document_update",
    "broadcast_analysis_update",
    "broadcast_qa_update",
    "periodic_dashboard_updates"
]