"""
Push Notification System

Real-time push notifications for browser and mobile devices with
Firebase/OneSignal integration for immediate legal updates.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import base64

logger = logging.getLogger(__name__)

class PushProvider(Enum):
    """Push notification providers"""
    FIREBASE = "firebase"
    ONESIGNAL = "onesignal"
    WEB_PUSH = "web_push"
    MOCK = "mock"

class PushStatus(Enum):
    """Push notification status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    CLICKED = "clicked"
    DISMISSED = "dismissed"
    FAILED = "failed"

class PushPriority(Enum):
    """Push notification priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class PushType(Enum):
    """Types of push notifications"""
    DOCUMENT_ANALYSIS = "document_analysis"
    QA_RESPONSE = "qa_response"
    ATTORNEY_ACTION = "attorney_action"
    CASE_UPDATE = "case_update"
    SYSTEM_ALERT = "system_alert"
    REMINDER = "reminder"
    MARKETING = "marketing"

@dataclass
class PushDevice:
    """User device for push notifications"""
    device_id: str
    user_id: str
    device_type: str  # web, ios, android
    device_token: str
    push_endpoint: Optional[str] = None
    public_key: Optional[str] = None
    auth_secret: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)

@dataclass
class PushNotification:
    """Push notification message"""
    notification_id: str
    user_id: str
    device_ids: List[str]
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    sound: Optional[str] = None
    click_action: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    push_type: PushType = PushType.SYSTEM_ALERT
    priority: PushPriority = PushPriority.NORMAL
    ttl: int = 3600  # Time to live in seconds
    status: PushStatus = PushStatus.PENDING
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PushTemplate:
    """Push notification template"""
    template_id: str
    name: str
    title_template: str
    body_template: str
    push_type: PushType
    priority: PushPriority = PushPriority.NORMAL
    icon: Optional[str] = None
    click_action_template: Optional[str] = None
    variables: List[str] = field(default_factory=list)

class FirebaseProvider:
    """Firebase Cloud Messaging provider"""

    def __init__(self, server_key: str, sender_id: str):
        self.server_key = server_key
        self.sender_id = sender_id
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"

    async def send_push(self, notification: PushNotification, devices: List[PushDevice]) -> Dict[str, bool]:
        """Send push notification via Firebase"""
        try:
            import aiohttp

            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json"
            }

            results = {}

            for device in devices:
                # Build Firebase message
                message = {
                    "to": device.device_token,
                    "notification": {
                        "title": notification.title,
                        "body": notification.body,
                        "icon": notification.icon or "/icons/default.png",
                        "click_action": notification.click_action
                    },
                    "data": notification.data,
                    "priority": "high" if notification.priority == PushPriority.HIGH else "normal",
                    "time_to_live": notification.ttl
                }

                if notification.image:
                    message["notification"]["image"] = notification.image

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.fcm_url,
                        headers=headers,
                        json=message
                    ) as response:
                        if response.status == 200:
                            result_data = await response.json()
                            results[device.device_id] = result_data.get("success", 0) > 0
                        else:
                            results[device.device_id] = False

            return results

        except Exception as e:
            logger.error(f"Firebase send error: {str(e)}")
            return {device.device_id: False for device in devices}

class WebPushProvider:
    """Web Push API provider"""

    def __init__(self, vapid_private_key: str, vapid_public_key: str, vapid_subject: str):
        self.vapid_private_key = vapid_private_key
        self.vapid_public_key = vapid_public_key
        self.vapid_subject = vapid_subject

    async def send_push(self, notification: PushNotification, devices: List[PushDevice]) -> Dict[str, bool]:
        """Send push notification via Web Push API"""
        try:
            # This would integrate with pywebpush library
            # For now, return mock success
            results = {}

            for device in devices:
                if device.push_endpoint and device.public_key and device.auth_secret:
                    # Mock successful send
                    results[device.device_id] = True
                    logger.info(f"Mock web push sent to {device.device_id}")
                else:
                    results[device.device_id] = False

            return results

        except Exception as e:
            logger.error(f"Web Push send error: {str(e)}")
            return {device.device_id: False for device in devices}

class MockPushProvider:
    """Mock push provider for testing"""

    def __init__(self):
        self.sent_notifications: List[Dict[str, Any]] = []

    async def send_push(self, notification: PushNotification, devices: List[PushDevice]) -> Dict[str, bool]:
        """Mock send push notification"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)

            results = {}
            for device in devices:
                # Mock successful delivery
                results[device.device_id] = True

                self.sent_notifications.append({
                    "notification_id": notification.notification_id,
                    "device_id": device.device_id,
                    "user_id": notification.user_id,
                    "title": notification.title,
                    "body": notification.body,
                    "sent_at": datetime.now().isoformat()
                })

            logger.info(f"Mock push sent to {len(devices)} devices: {notification.title}")
            return results

        except Exception as e:
            logger.error(f"Mock push error: {str(e)}")
            return {device.device_id: False for device in devices}

class PushTemplateManager:
    """Manage push notification templates"""

    def __init__(self):
        self.templates: Dict[str, PushTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default push templates"""
        templates = {
            "document_analysis_complete": PushTemplate(
                template_id="document_analysis_complete",
                name="Document Analysis Complete",
                title_template="Analysis Complete",
                body_template="Your document '{document_name}' analysis is ready with {issues_count} issues found.",
                push_type=PushType.DOCUMENT_ANALYSIS,
                priority=PushPriority.HIGH,
                icon="/icons/document.png",
                click_action_template="/documents/{document_id}/analysis",
                variables=["document_name", "issues_count", "document_id"]
            ),
            "qa_response_ready": PushTemplate(
                template_id="qa_response_ready",
                name="Q&A Response Ready",
                title_template="Question Answered",
                body_template="Your question about '{topic}' has been answered by our AI.",
                push_type=PushType.QA_RESPONSE,
                priority=PushPriority.HIGH,
                icon="/icons/qa.png",
                click_action_template="/qa/{question_id}",
                variables=["topic", "question_id"]
            ),
            "attorney_action": PushTemplate(
                template_id="attorney_action",
                name="Attorney Action Required",
                title_template="Attorney Action",
                body_template="{attorney_name} has {action_type} for case '{case_name}'.",
                push_type=PushType.ATTORNEY_ACTION,
                priority=PushPriority.HIGH,
                icon="/icons/attorney.png",
                click_action_template="/cases/{case_id}",
                variables=["attorney_name", "action_type", "case_name", "case_id"]
            ),
            "case_update": PushTemplate(
                template_id="case_update",
                name="Case Update",
                title_template="Case Update",
                body_template="New update for '{case_name}': {update_summary}",
                push_type=PushType.CASE_UPDATE,
                priority=PushPriority.NORMAL,
                icon="/icons/case.png",
                click_action_template="/cases/{case_id}",
                variables=["case_name", "update_summary", "case_id"]
            ),
            "system_alert": PushTemplate(
                template_id="system_alert",
                name="System Alert",
                title_template="System Alert",
                body_template="{alert_message}",
                push_type=PushType.SYSTEM_ALERT,
                priority=PushPriority.HIGH,
                icon="/icons/alert.png",
                click_action_template="/dashboard",
                variables=["alert_message"]
            ),
            "deadline_reminder": PushTemplate(
                template_id="deadline_reminder",
                name="Deadline Reminder",
                title_template="Deadline Reminder",
                body_template="'{case_name}' deadline is {time_remaining}. Don't forget: {task_description}",
                push_type=PushType.REMINDER,
                priority=PushPriority.HIGH,
                icon="/icons/deadline.png",
                click_action_template="/cases/{case_id}",
                variables=["case_name", "time_remaining", "task_description", "case_id"]
            )
        }

        self.templates.update(templates)

    def get_template(self, template_id: str) -> Optional[PushTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def render_template(self, template_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Render template with data"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Render title
        title = template.title_template
        for var in template.variables:
            if var in data:
                title = title.replace(f"{{{var}}}", str(data[var]))

        # Render body
        body = template.body_template
        for var in template.variables:
            if var in data:
                body = body.replace(f"{{{var}}}", str(data[var]))

        # Render click action
        click_action = None
        if template.click_action_template:
            click_action = template.click_action_template
            for var in template.variables:
                if var in data:
                    click_action = click_action.replace(f"{{{var}}}", str(data[var]))

        return {
            "title": title,
            "body": body,
            "click_action": click_action,
            "icon": template.icon,
            "priority": template.priority
        }

class PushNotificationSystem:
    """
    Comprehensive push notification system for real-time legal updates
    """

    def __init__(self, provider: PushProvider = PushProvider.MOCK):
        self.provider_type = provider
        self.provider = None
        self.template_manager = PushTemplateManager()
        self.devices: Dict[str, List[PushDevice]] = {}  # user_id -> devices
        self.notifications: Dict[str, PushNotification] = {}
        self.notification_queue: List[PushNotification] = []

    def configure_firebase(self, server_key: str, sender_id: str):
        """Configure Firebase provider"""
        self.provider = FirebaseProvider(server_key, sender_id)

    def configure_webpush(self, vapid_private_key: str, vapid_public_key: str, vapid_subject: str):
        """Configure Web Push provider"""
        self.provider = WebPushProvider(vapid_private_key, vapid_public_key, vapid_subject)

    def configure_mock(self):
        """Configure mock provider for testing"""
        self.provider = MockPushProvider()

    def register_device(self, user_id: str, device_token: str, device_type: str,
                       push_endpoint: Optional[str] = None, public_key: Optional[str] = None,
                       auth_secret: Optional[str] = None, user_agent: Optional[str] = None) -> str:
        """Register user device for push notifications"""
        device_id = f"device_{uuid.uuid4().hex[:12]}"

        device = PushDevice(
            device_id=device_id,
            user_id=user_id,
            device_type=device_type,
            device_token=device_token,
            push_endpoint=push_endpoint,
            public_key=public_key,
            auth_secret=auth_secret,
            user_agent=user_agent
        )

        if user_id not in self.devices:
            self.devices[user_id] = []
        self.devices[user_id].append(device)

        logger.info(f"Registered device {device_id} for user {user_id}")
        return device_id

    def unregister_device(self, user_id: str, device_id: str) -> bool:
        """Unregister device"""
        if user_id in self.devices:
            self.devices[user_id] = [
                device for device in self.devices[user_id]
                if device.device_id != device_id
            ]
            logger.info(f"Unregistered device {device_id} for user {user_id}")
            return True
        return False

    def get_user_devices(self, user_id: str) -> List[PushDevice]:
        """Get active devices for user"""
        return [
            device for device in self.devices.get(user_id, [])
            if device.is_active
        ]

    async def send_document_analysis_complete(self, user_id: str, document_name: str,
                                            issues_count: int, document_id: str) -> str:
        """Send document analysis completion notification"""
        return await self.send_template_push(
            template_id="document_analysis_complete",
            user_ids=[user_id],
            template_data={
                "document_name": document_name,
                "issues_count": issues_count,
                "document_id": document_id
            },
            priority=PushPriority.HIGH
        )

    async def send_qa_response_ready(self, user_id: str, topic: str, question_id: str) -> str:
        """Send Q&A response notification"""
        return await self.send_template_push(
            template_id="qa_response_ready",
            user_ids=[user_id],
            template_data={
                "topic": topic[:50],  # Truncate for notification
                "question_id": question_id
            },
            priority=PushPriority.HIGH
        )

    async def send_attorney_action_notification(self, user_id: str, attorney_name: str,
                                              action_type: str, case_name: str,
                                              case_id: str) -> str:
        """Send attorney action notification"""
        return await self.send_template_push(
            template_id="attorney_action",
            user_ids=[user_id],
            template_data={
                "attorney_name": attorney_name,
                "action_type": action_type,
                "case_name": case_name,
                "case_id": case_id
            },
            priority=PushPriority.HIGH
        )

    async def send_case_update(self, user_ids: List[str], case_name: str,
                              update_summary: str, case_id: str) -> str:
        """Send case update notification"""
        return await self.send_template_push(
            template_id="case_update",
            user_ids=user_ids,
            template_data={
                "case_name": case_name,
                "update_summary": update_summary[:100],  # Truncate
                "case_id": case_id
            },
            priority=PushPriority.NORMAL
        )

    async def send_system_alert(self, user_ids: List[str], alert_message: str) -> str:
        """Send system alert notification"""
        return await self.send_template_push(
            template_id="system_alert",
            user_ids=user_ids,
            template_data={
                "alert_message": alert_message
            },
            priority=PushPriority.HIGH
        )

    async def send_deadline_reminder(self, user_id: str, case_name: str,
                                   time_remaining: str, task_description: str,
                                   case_id: str) -> str:
        """Send deadline reminder notification"""
        return await self.send_template_push(
            template_id="deadline_reminder",
            user_ids=[user_id],
            template_data={
                "case_name": case_name,
                "time_remaining": time_remaining,
                "task_description": task_description[:50],  # Truncate
                "case_id": case_id
            },
            priority=PushPriority.HIGH
        )

    async def send_template_push(self, template_id: str, user_ids: List[str],
                               template_data: Dict[str, Any],
                               priority: Optional[PushPriority] = None,
                               ttl: int = 3600,
                               scheduled_at: Optional[datetime] = None) -> str:
        """Send templated push notification"""
        try:
            # Render template
            rendered = self.template_manager.render_template(template_id, template_data)
            template = self.template_manager.get_template(template_id)

            # Collect all devices for users
            all_device_ids = []
            for user_id in user_ids:
                user_devices = self.get_user_devices(user_id)
                all_device_ids.extend([device.device_id for device in user_devices])

            if not all_device_ids:
                logger.warning(f"No active devices found for users: {user_ids}")
                return ""

            # Create notification
            notification = PushNotification(
                notification_id=f"push_{uuid.uuid4().hex[:12]}",
                user_id=user_ids[0] if len(user_ids) == 1 else "multiple",
                device_ids=all_device_ids,
                title=rendered["title"],
                body=rendered["body"],
                icon=rendered["icon"],
                click_action=rendered["click_action"],
                data={"template_id": template_id, **template_data},
                push_type=template.push_type,
                priority=priority or rendered["priority"],
                ttl=ttl,
                scheduled_at=scheduled_at,
                metadata={"template_data": template_data, "user_ids": user_ids}
            )

            # Queue or send immediately
            if scheduled_at and scheduled_at > datetime.now():
                self.notification_queue.append(notification)
                notification.status = PushStatus.PENDING
            else:
                success = await self._send_notification(notification)
                if success:
                    notification.status = PushStatus.SENT
                    notification.sent_at = datetime.now()

            self.notifications[notification.notification_id] = notification

            logger.info(f"Push notification {notification.notification_id} status: {notification.status.value}")
            return notification.notification_id

        except Exception as e:
            logger.error(f"Error sending template push: {str(e)}")
            raise

    async def send_custom_push(self, user_ids: List[str], title: str, body: str,
                             icon: Optional[str] = None, click_action: Optional[str] = None,
                             data: Dict[str, Any] = None, priority: PushPriority = PushPriority.NORMAL,
                             ttl: int = 3600) -> str:
        """Send custom push notification"""
        try:
            # Collect all devices for users
            all_device_ids = []
            for user_id in user_ids:
                user_devices = self.get_user_devices(user_id)
                all_device_ids.extend([device.device_id for device in user_devices])

            if not all_device_ids:
                logger.warning(f"No active devices found for users: {user_ids}")
                return ""

            notification = PushNotification(
                notification_id=f"push_{uuid.uuid4().hex[:12]}",
                user_id=user_ids[0] if len(user_ids) == 1 else "multiple",
                device_ids=all_device_ids,
                title=title,
                body=body,
                icon=icon,
                click_action=click_action,
                data=data or {},
                push_type=PushType.SYSTEM_ALERT,
                priority=priority,
                ttl=ttl
            )

            success = await self._send_notification(notification)
            if success:
                notification.status = PushStatus.SENT
                notification.sent_at = datetime.now()

            self.notifications[notification.notification_id] = notification
            return notification.notification_id

        except Exception as e:
            logger.error(f"Error sending custom push: {str(e)}")
            raise

    async def _send_notification(self, notification: PushNotification) -> bool:
        """Send notification using configured provider"""
        if not self.provider:
            logger.error("No push provider configured")
            return False

        try:
            # Get devices for notification
            devices = []
            for device_id in notification.device_ids:
                for user_devices in self.devices.values():
                    for device in user_devices:
                        if device.device_id == device_id and device.is_active:
                            devices.append(device)

            if not devices:
                logger.warning(f"No active devices found for notification {notification.notification_id}")
                return False

            # Send to devices
            results = await self.provider.send_push(notification, devices)

            # Update device last used time for successful sends
            for device_id, success in results.items():
                if success:
                    for user_devices in self.devices.values():
                        for device in user_devices:
                            if device.device_id == device_id:
                                device.last_used = datetime.now()

            # Check if any sends were successful
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            logger.info(f"Push notification {notification.notification_id}: {success_count}/{total_count} successful")
            return success_count > 0

        except Exception as e:
            logger.error(f"Error sending notification {notification.notification_id}: {str(e)}")
            return False

    async def process_scheduled_notifications(self) -> int:
        """Process scheduled push notifications"""
        current_time = datetime.now()
        notifications_to_send = []

        # Find notifications ready to send
        for notification in self.notification_queue[:]:
            if notification.scheduled_at and notification.scheduled_at <= current_time:
                notifications_to_send.append(notification)
                self.notification_queue.remove(notification)

        # Send notifications
        for notification in notifications_to_send:
            success = await self._send_notification(notification)
            if success:
                notification.status = PushStatus.SENT
                notification.sent_at = datetime.now()
            else:
                notification.status = PushStatus.FAILED

        return len(notifications_to_send)

    def track_interaction(self, notification_id: str, action: str, device_id: str):
        """Track notification interaction (click, dismiss)"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]

            if action == "clicked":
                notification.status = PushStatus.CLICKED
            elif action == "dismissed":
                notification.status = PushStatus.DISMISSED

            # Update device last used time
            for user_devices in self.devices.values():
                for device in user_devices:
                    if device.device_id == device_id:
                        device.last_used = datetime.now()

            logger.info(f"Tracked {action} for notification {notification_id}")

    def get_notification_status(self, notification_id: str) -> Optional[PushStatus]:
        """Get notification status"""
        if notification_id in self.notifications:
            return self.notifications[notification_id].status

        # Check queue
        for notification in self.notification_queue:
            if notification.notification_id == notification_id:
                return notification.status

        return None

    async def get_push_statistics(self) -> Dict[str, Any]:
        """Get push notification statistics"""
        total_sent = len([n for n in self.notifications.values() if n.status != PushStatus.PENDING])
        queued = len(self.notification_queue)
        total_devices = sum(len(devices) for devices in self.devices.values())
        active_devices = sum(len([d for d in devices if d.is_active]) for devices in self.devices.values())

        status_counts = {}
        type_counts = {}
        priority_counts = {}

        for notification in self.notifications.values():
            # Status counts
            status = notification.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Type counts
            push_type = notification.push_type.value
            type_counts[push_type] = type_counts.get(push_type, 0) + 1

            # Priority counts
            priority = notification.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        return {
            "total_sent": total_sent,
            "queued": queued,
            "total_devices": total_devices,
            "active_devices": active_devices,
            "status_breakdown": status_counts,
            "type_breakdown": type_counts,
            "priority_breakdown": priority_counts,
            "delivery_rate": status_counts.get("delivered", 0) / max(total_sent, 1) * 100,
            "click_rate": status_counts.get("clicked", 0) / max(total_sent, 1) * 100
        }

class PushAPI:
    """API interface for push notifications"""

    def __init__(self, push_system: PushNotificationSystem):
        self.push_system = push_system

    async def register_device_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for device registration"""
        try:
            device_id = self.push_system.register_device(
                user_id=request_data["user_id"],
                device_token=request_data["device_token"],
                device_type=request_data["device_type"],
                push_endpoint=request_data.get("push_endpoint"),
                public_key=request_data.get("public_key"),
                auth_secret=request_data.get("auth_secret"),
                user_agent=request_data.get("user_agent")
            )
            return {"success": True, "device_id": device_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_analysis_complete_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for analysis complete notifications"""
        try:
            notification_id = await self.push_system.send_document_analysis_complete(
                user_id=request_data["user_id"],
                document_name=request_data["document_name"],
                issues_count=request_data["issues_count"],
                document_id=request_data["document_id"]
            )
            return {"success": True, "notification_id": notification_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_custom_notification_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for custom notifications"""
        try:
            notification_id = await self.push_system.send_custom_push(
                user_ids=request_data["user_ids"],
                title=request_data["title"],
                body=request_data["body"],
                icon=request_data.get("icon"),
                click_action=request_data.get("click_action"),
                data=request_data.get("data", {}),
                priority=PushPriority(request_data.get("priority", "normal"))
            )
            return {"success": True, "notification_id": notification_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def track_interaction_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for tracking interactions"""
        try:
            self.push_system.track_interaction(
                notification_id=request_data["notification_id"],
                action=request_data["action"],
                device_id=request_data["device_id"]
            )
            return {"success": True, "message": "Interaction tracked"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_statistics_endpoint(self) -> Dict[str, Any]:
        """API endpoint for push statistics"""
        try:
            stats = await self.push_system.get_push_statistics()
            return {"success": True, "statistics": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}