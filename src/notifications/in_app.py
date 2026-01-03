"""
In-App Notification System
Provides real-time in-app notifications with UI components for bell icon,
notification center, and read/unread state management.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import json
import asyncio
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(Enum):
    DOCUMENT_ANALYSIS = "document_analysis"
    QA_RESPONSE = "qa_response"
    ATTORNEY_ACTION = "attorney_action"
    CASE_UPDATE = "case_update"
    SYSTEM_ALERT = "system_alert"
    DEADLINE_REMINDER = "deadline_reminder"
    MESSAGE = "message"
    PAYMENT = "payment"
    SECURITY = "security"


class NotificationStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


@dataclass
class InAppNotification:
    """Represents an in-app notification"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    status: NotificationStatus = NotificationStatus.UNREAD
    created_at: datetime = field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    expires_at: Optional[datetime] = None

    def mark_as_read(self):
        """Mark notification as read"""
        if self.status == NotificationStatus.UNREAD:
            self.status = NotificationStatus.READ
            self.read_at = datetime.now()

    def mark_as_archived(self):
        """Mark notification as archived"""
        self.status = NotificationStatus.ARCHIVED
        self.archived_at = datetime.now()

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        return self.expires_at is not None and datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "metadata": self.metadata,
            "action_url": self.action_url,
            "action_text": self.action_text,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired()
        }


@dataclass
class NotificationTemplate:
    """Template for generating in-app notifications"""
    type: NotificationType
    title_template: str
    message_template: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    action_text: Optional[str] = None
    action_url_template: Optional[str] = None
    expires_hours: Optional[int] = None

    def generate_notification(
        self,
        notification_id: str,
        user_id: str,
        variables: Dict[str, Any]
    ) -> InAppNotification:
        """Generate notification from template"""
        title = self.title_template.format(**variables)
        message = self.message_template.format(**variables)

        action_url = None
        if self.action_url_template:
            action_url = self.action_url_template.format(**variables)

        expires_at = None
        if self.expires_hours:
            expires_at = datetime.now() + timedelta(hours=self.expires_hours)

        return InAppNotification(
            id=notification_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=self.type,
            priority=self.priority,
            action_url=action_url,
            action_text=self.action_text,
            expires_at=expires_at,
            metadata=variables
        )


class InAppTemplateManager:
    """Manages in-app notification templates"""

    def __init__(self):
        self.templates = {
            NotificationType.DOCUMENT_ANALYSIS: NotificationTemplate(
                type=NotificationType.DOCUMENT_ANALYSIS,
                title_template="Document Analysis Complete",
                message_template="Analysis of '{document_name}' is complete. {analysis_type} analysis found {key_findings_count} key findings.",
                priority=NotificationPriority.MEDIUM,
                action_text="View Analysis",
                action_url_template="/documents/{document_id}/analysis",
                expires_hours=72
            ),
            NotificationType.QA_RESPONSE: NotificationTemplate(
                type=NotificationType.QA_RESPONSE,
                title_template="Question Answered",
                message_template="Your question about '{question_topic}' has been answered by {responder_name}.",
                priority=NotificationPriority.HIGH,
                action_text="View Answer",
                action_url_template="/qa/{question_id}",
                expires_hours=48
            ),
            NotificationType.ATTORNEY_ACTION: NotificationTemplate(
                type=NotificationType.ATTORNEY_ACTION,
                title_template="Attorney Update",
                message_template="{attorney_name} has {action_type} on case '{case_name}': {action_description}",
                priority=NotificationPriority.HIGH,
                action_text="View Case",
                action_url_template="/cases/{case_id}",
                expires_hours=48
            ),
            NotificationType.CASE_UPDATE: NotificationTemplate(
                type=NotificationType.CASE_UPDATE,
                title_template="Case Status Update",
                message_template="Case '{case_name}' status changed from {old_status} to {new_status}. {update_notes}",
                priority=NotificationPriority.MEDIUM,
                action_text="View Case",
                action_url_template="/cases/{case_id}",
                expires_hours=96
            ),
            NotificationType.SYSTEM_ALERT: NotificationTemplate(
                type=NotificationType.SYSTEM_ALERT,
                title_template="System Alert",
                message_template="{alert_message}",
                priority=NotificationPriority.HIGH,
                action_text="Learn More",
                action_url_template="/system/alerts/{alert_id}",
                expires_hours=24
            ),
            NotificationType.DEADLINE_REMINDER: NotificationTemplate(
                type=NotificationType.DEADLINE_REMINDER,
                title_template="Deadline Reminder",
                message_template="'{task_name}' is due {time_remaining}. Don't miss this important deadline!",
                priority=NotificationPriority.URGENT,
                action_text="View Task",
                action_url_template="/tasks/{task_id}",
                expires_hours=1
            ),
            NotificationType.MESSAGE: NotificationTemplate(
                type=NotificationType.MESSAGE,
                title_template="New Message",
                message_template="You have a new message from {sender_name}: '{message_preview}'",
                priority=NotificationPriority.MEDIUM,
                action_text="Read Message",
                action_url_template="/messages/{message_id}",
                expires_hours=168
            ),
            NotificationType.PAYMENT: NotificationTemplate(
                type=NotificationType.PAYMENT,
                title_template="Payment {payment_status}",
                message_template="Payment of ${amount} for {service_description} has been {payment_status}.",
                priority=NotificationPriority.HIGH,
                action_text="View Receipt",
                action_url_template="/billing/invoices/{invoice_id}",
                expires_hours=720
            ),
            NotificationType.SECURITY: NotificationTemplate(
                type=NotificationType.SECURITY,
                title_template="Security Alert",
                message_template="{security_event}: {security_details}. Please review your account activity.",
                priority=NotificationPriority.URGENT,
                action_text="Review Security",
                action_url_template="/account/security",
                expires_hours=12
            )
        }

    def get_template(self, notification_type: NotificationType) -> Optional[NotificationTemplate]:
        """Get template by type"""
        return self.templates.get(notification_type)

    def create_notification(
        self,
        notification_type: NotificationType,
        notification_id: str,
        user_id: str,
        variables: Dict[str, Any]
    ) -> Optional[InAppNotification]:
        """Create notification from template"""
        template = self.get_template(notification_type)
        if not template:
            logger.error(f"Template not found for type: {notification_type}")
            return None

        try:
            return template.generate_notification(notification_id, user_id, variables)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return None


@dataclass
class NotificationStats:
    """Statistics for user notifications"""
    total_notifications: int = 0
    unread_notifications: int = 0
    read_notifications: int = 0
    archived_notifications: int = 0
    notifications_by_type: Dict[str, int] = field(default_factory=dict)
    notifications_by_priority: Dict[str, int] = field(default_factory=dict)
    recent_notifications: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total_notifications,
            "unread": self.unread_notifications,
            "read": self.read_notifications,
            "archived": self.archived_notifications,
            "by_type": self.notifications_by_type,
            "by_priority": self.notifications_by_priority,
            "recent": self.recent_notifications
        }


class InAppNotificationSystem:
    """Comprehensive in-app notification system"""

    def __init__(self):
        self.notifications: Dict[str, Dict[str, InAppNotification]] = defaultdict(dict)
        self.template_manager = InAppTemplateManager()
        self.websocket_connections: Dict[str, List] = defaultdict(list)
        self._notification_counter = 0

    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        self._notification_counter += 1
        return f"inapp_{int(datetime.now().timestamp())}_{self._notification_counter}"

    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        variables: Dict[str, Any]
    ) -> Optional[InAppNotification]:
        """Create and store new notification"""
        notification_id = self._generate_notification_id()

        notification = self.template_manager.create_notification(
            notification_type, notification_id, user_id, variables
        )

        if notification:
            self.notifications[user_id][notification_id] = notification
            await self._broadcast_to_user(user_id, {
                "type": "new_notification",
                "notification": notification.to_dict()
            })
            logger.info(f"Created in-app notification {notification_id} for user {user_id}")
            return notification

        return None

    async def get_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[InAppNotification]:
        """Get user notifications with filtering"""
        user_notifications = list(self.notifications.get(user_id, {}).values())

        # Filter by status
        if status:
            user_notifications = [n for n in user_notifications if n.status == status]

        # Filter by type
        if notification_type:
            user_notifications = [n for n in user_notifications if n.notification_type == notification_type]

        # Remove expired notifications
        user_notifications = [n for n in user_notifications if not n.is_expired()]

        # Sort by creation time (newest first)
        user_notifications.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        return user_notifications[offset:offset + limit]

    async def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read"""
        if user_id in self.notifications and notification_id in self.notifications[user_id]:
            notification = self.notifications[user_id][notification_id]
            old_status = notification.status
            notification.mark_as_read()

            if old_status != notification.status:
                await self._broadcast_to_user(user_id, {
                    "type": "notification_updated",
                    "notification": notification.to_dict()
                })

            logger.info(f"Marked notification {notification_id} as read for user {user_id}")
            return True

        return False

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for user"""
        count = 0
        if user_id in self.notifications:
            for notification in self.notifications[user_id].values():
                if notification.status == NotificationStatus.UNREAD:
                    notification.mark_as_read()
                    count += 1

            if count > 0:
                await self._broadcast_to_user(user_id, {
                    "type": "all_notifications_read",
                    "count": count
                })

            logger.info(f"Marked {count} notifications as read for user {user_id}")

        return count

    async def archive_notification(self, user_id: str, notification_id: str) -> bool:
        """Archive notification"""
        if user_id in self.notifications and notification_id in self.notifications[user_id]:
            notification = self.notifications[user_id][notification_id]
            notification.mark_as_archived()

            await self._broadcast_to_user(user_id, {
                "type": "notification_archived",
                "notification_id": notification_id
            })

            logger.info(f"Archived notification {notification_id} for user {user_id}")
            return True

        return False

    async def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """Delete notification permanently"""
        if user_id in self.notifications and notification_id in self.notifications[user_id]:
            del self.notifications[user_id][notification_id]

            await self._broadcast_to_user(user_id, {
                "type": "notification_deleted",
                "notification_id": notification_id
            })

            logger.info(f"Deleted notification {notification_id} for user {user_id}")
            return True

        return False

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        if user_id not in self.notifications:
            return 0

        count = 0
        for notification in self.notifications[user_id].values():
            if notification.status == NotificationStatus.UNREAD and not notification.is_expired():
                count += 1

        return count

    async def get_notification_stats(self, user_id: str) -> NotificationStats:
        """Get comprehensive notification statistics"""
        stats = NotificationStats()

        if user_id not in self.notifications:
            return stats

        notifications = [n for n in self.notifications[user_id].values() if not n.is_expired()]

        stats.total_notifications = len(notifications)

        # Count by status
        for notification in notifications:
            if notification.status == NotificationStatus.UNREAD:
                stats.unread_notifications += 1
            elif notification.status == NotificationStatus.READ:
                stats.read_notifications += 1
            elif notification.status == NotificationStatus.ARCHIVED:
                stats.archived_notifications += 1

        # Count by type
        stats.notifications_by_type = defaultdict(int)
        for notification in notifications:
            stats.notifications_by_type[notification.notification_type.value] += 1

        # Count by priority
        stats.notifications_by_priority = defaultdict(int)
        for notification in notifications:
            stats.notifications_by_priority[notification.priority.value] += 1

        # Recent notifications (last 10)
        recent = sorted(notifications, key=lambda x: x.created_at, reverse=True)[:10]
        stats.recent_notifications = [n.to_dict() for n in recent]

        return stats

    async def cleanup_expired_notifications(self) -> int:
        """Remove expired notifications"""
        removed_count = 0

        for user_id in list(self.notifications.keys()):
            expired_ids = []
            for notification_id, notification in self.notifications[user_id].items():
                if notification.is_expired():
                    expired_ids.append(notification_id)

            for notification_id in expired_ids:
                del self.notifications[user_id][notification_id]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired notifications")

        return removed_count

    async def add_websocket_connection(self, user_id: str, websocket):
        """Add WebSocket connection for real-time notifications"""
        self.websocket_connections[user_id].append(websocket)
        logger.info(f"Added WebSocket connection for user {user_id}")

    async def remove_websocket_connection(self, user_id: str, websocket):
        """Remove WebSocket connection"""
        if user_id in self.websocket_connections:
            try:
                self.websocket_connections[user_id].remove(websocket)
                if not self.websocket_connections[user_id]:
                    del self.websocket_connections[user_id]
                logger.info(f"Removed WebSocket connection for user {user_id}")
            except ValueError:
                pass

    async def _broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast message to all user's WebSocket connections"""
        if user_id in self.websocket_connections:
            disconnected = []
            for websocket in self.websocket_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.append(websocket)

            # Remove disconnected WebSockets
            for ws in disconnected:
                try:
                    self.websocket_connections[user_id].remove(ws)
                except ValueError:
                    pass

    # Quick notification creation methods
    async def notify_document_analysis_complete(
        self, user_id: str, document_name: str, document_id: str,
        analysis_type: str = "comprehensive", key_findings_count: int = 0
    ):
        """Quick method to notify about document analysis completion"""
        await self.create_notification(user_id, NotificationType.DOCUMENT_ANALYSIS, {
            "document_name": document_name,
            "document_id": document_id,
            "analysis_type": analysis_type,
            "key_findings_count": key_findings_count
        })

    async def notify_qa_response(
        self, user_id: str, question_topic: str, question_id: str, responder_name: str
    ):
        """Quick method to notify about Q&A response"""
        await self.create_notification(user_id, NotificationType.QA_RESPONSE, {
            "question_topic": question_topic,
            "question_id": question_id,
            "responder_name": responder_name
        })

    async def notify_deadline_reminder(
        self, user_id: str, task_name: str, task_id: str, time_remaining: str
    ):
        """Quick method to notify about deadline reminder"""
        await self.create_notification(user_id, NotificationType.DEADLINE_REMINDER, {
            "task_name": task_name,
            "task_id": task_id,
            "time_remaining": time_remaining
        })


# Global in-app notification system instance
in_app_notification_system = InAppNotificationSystem()


# FastAPI endpoints would be added to main router
def get_in_app_notification_endpoints():
    """Returns FastAPI endpoints for in-app notifications"""
    from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse

    router = APIRouter(prefix="/api/notifications/in-app", tags=["in-app-notifications"])

    @router.get("/")
    async def get_notifications(
        user_id: str,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ):
        """Get user notifications"""
        try:
            status_enum = NotificationStatus(status) if status else None
            type_enum = NotificationType(notification_type) if notification_type else None

            notifications = await in_app_notification_system.get_notifications(
                user_id, status_enum, type_enum, limit, offset
            )

            return {
                "notifications": [n.to_dict() for n in notifications],
                "total": len(notifications)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/unread-count")
    async def get_unread_count(user_id: str):
        """Get unread notification count"""
        count = await in_app_notification_system.get_unread_count(user_id)
        return {"unread_count": count}

    @router.get("/stats")
    async def get_stats(user_id: str):
        """Get notification statistics"""
        stats = await in_app_notification_system.get_notification_stats(user_id)
        return stats.to_dict()

    @router.post("/{notification_id}/read")
    async def mark_as_read(user_id: str, notification_id: str):
        """Mark notification as read"""
        success = await in_app_notification_system.mark_as_read(user_id, notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"success": True}

    @router.post("/mark-all-read")
    async def mark_all_as_read(user_id: str):
        """Mark all notifications as read"""
        count = await in_app_notification_system.mark_all_as_read(user_id)
        return {"marked_read": count}

    @router.post("/{notification_id}/archive")
    async def archive_notification(user_id: str, notification_id: str):
        """Archive notification"""
        success = await in_app_notification_system.archive_notification(user_id, notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"success": True}

    @router.delete("/{notification_id}")
    async def delete_notification(user_id: str, notification_id: str):
        """Delete notification"""
        success = await in_app_notification_system.delete_notification(user_id, notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"success": True}

    @router.post("/create")
    async def create_notification(
        user_id: str,
        notification_type: str,
        variables: Dict[str, Any]
    ):
        """Create new notification"""
        try:
            type_enum = NotificationType(notification_type)
            notification = await in_app_notification_system.create_notification(
                user_id, type_enum, variables
            )

            if not notification:
                raise HTTPException(status_code=400, detail="Failed to create notification")

            return notification.to_dict()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification type")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for real-time notifications"""
        await websocket.accept()
        await in_app_notification_system.add_websocket_connection(user_id, websocket)

        try:
            while True:
                # Keep connection alive and handle ping/pong
                await websocket.receive_text()
        except WebSocketDisconnect:
            await in_app_notification_system.remove_websocket_connection(user_id, websocket)

    @router.post("/cleanup-expired")
    async def cleanup_expired():
        """Cleanup expired notifications"""
        count = await in_app_notification_system.cleanup_expired_notifications()
        return {"removed": count}

    return router


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        system = InAppNotificationSystem()

        # Create notifications
        await system.notify_document_analysis_complete(
            "user123", "Contract_Review.pdf", "doc456", "contract", 5
        )

        await system.notify_deadline_reminder(
            "user123", "File Motion Response", "task789", "in 2 hours"
        )

        # Get notifications
        notifications = await system.get_notifications("user123")
        print(f"User has {len(notifications)} notifications")

        # Get stats
        stats = await system.get_notification_stats("user123")
        print(f"Unread: {stats.unread_notifications}")

        # Mark as read
        if notifications:
            await system.mark_as_read("user123", notifications[0].id)

        print("In-app notification system demo completed!")

    asyncio.run(demo())