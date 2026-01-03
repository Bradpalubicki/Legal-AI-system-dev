"""
Unified Notification Orchestration System
Coordinates all notification channels (email, SMS, push, in-app) with intelligent routing,
deduplication, delivery optimization, and comprehensive tracking.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib

# Import our notification systems
from .email import EmailNotificationEngine
from .sms import SMSNotificationSystem
from .push import PushNotificationSystem
from .in_app import InAppNotificationSystem, NotificationType as InAppNotificationType

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"


@dataclass
class NotificationRequest:
    """Unified notification request across all channels"""
    id: str
    user_id: str
    template_type: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    variables: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    deduplication_key: Optional[str] = None
    retry_config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def generate_dedup_key(self) -> str:
        """Generate deduplication key if not provided"""
        if self.deduplication_key:
            return self.deduplication_key

        # Create hash based on user, template, and key variables
        key_vars = {k: v for k, v in self.variables.items() if k in [
            'document_id', 'case_id', 'task_id', 'message_id', 'alert_id'
        ]}

        content = f"{self.user_id}:{self.template_type}:{json.dumps(key_vars, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class ChannelDelivery:
    """Represents delivery attempt for a specific channel"""
    channel: NotificationChannel
    status: DeliveryStatus
    message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationExecution:
    """Tracks execution of a notification request"""
    request: NotificationRequest
    status: DeliveryStatus
    channel_deliveries: Dict[NotificationChannel, ChannelDelivery] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_channel_delivery(self, channel: NotificationChannel, delivery: ChannelDelivery):
        """Update delivery status for a channel"""
        self.channel_deliveries[channel] = delivery
        self.updated_at = datetime.now()

        # Update overall status based on channel statuses
        statuses = [d.status for d in self.channel_deliveries.values()]

        if all(s == DeliveryStatus.DELIVERED for s in statuses):
            self.status = DeliveryStatus.DELIVERED
        elif all(s in [DeliveryStatus.FAILED, DeliveryStatus.BOUNCED, DeliveryStatus.CANCELLED] for s in statuses):
            self.status = DeliveryStatus.FAILED
        elif any(s == DeliveryStatus.SENT for s in statuses):
            self.status = DeliveryStatus.SENT
        else:
            self.status = DeliveryStatus.PENDING


class UserPreferences:
    """User notification preferences"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences = {
            'email': {
                'enabled': True,
                'types': ['document_analysis', 'deadline_reminder', 'case_update'],
                'frequency': 'immediate',  # immediate, daily, weekly
                'quiet_hours': {'start': '22:00', 'end': '08:00'}
            },
            'sms': {
                'enabled': True,
                'types': ['deadline_reminder', 'urgent_alert'],
                'quiet_hours': {'start': '22:00', 'end': '08:00'}
            },
            'push': {
                'enabled': True,
                'types': ['document_analysis', 'qa_response', 'case_update'],
                'quiet_hours': {'start': '22:00', 'end': '08:00'}
            },
            'in_app': {
                'enabled': True,
                'types': ['all'],
                'retention_days': 30
            }
        }

    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if channel is enabled"""
        return self.preferences.get(channel.value, {}).get('enabled', False)

    def is_type_enabled_for_channel(self, channel: NotificationChannel, notification_type: str) -> bool:
        """Check if notification type is enabled for channel"""
        channel_prefs = self.preferences.get(channel.value, {})
        enabled_types = channel_prefs.get('types', [])
        return 'all' in enabled_types or notification_type in enabled_types

    def is_in_quiet_hours(self, channel: NotificationChannel) -> bool:
        """Check if current time is in quiet hours for channel"""
        channel_prefs = self.preferences.get(channel.value, {})
        quiet_hours = channel_prefs.get('quiet_hours')

        if not quiet_hours:
            return False

        now = datetime.now().time()
        start = datetime.strptime(quiet_hours['start'], '%H:%M').time()
        end = datetime.strptime(quiet_hours['end'], '%H:%M').time()

        if start <= end:
            return start <= now <= end
        else:  # Quiet hours span midnight
            return now >= start or now <= end


class NotificationOrchestrator:
    """Central orchestration system for all notification channels"""

    def __init__(self):
        # Initialize notification systems
        self.email_system = EmailNotificationEngine()
        self.sms_system = SMSNotificationSystem()
        self.push_system = PushNotificationSystem()
        self.in_app_system = InAppNotificationSystem()

        # Tracking and state
        self.executions: Dict[str, NotificationExecution] = {}
        self.user_preferences: Dict[str, UserPreferences] = {}
        self.deduplication_cache: Dict[str, datetime] = {}
        self.rate_limit_counters: Dict[str, deque] = defaultdict(lambda: deque())

        # Configuration
        self.dedup_window_minutes = 60
        self.rate_limits = {
            NotificationChannel.EMAIL: {'per_hour': 100, 'per_day': 500},
            NotificationChannel.SMS: {'per_hour': 10, 'per_day': 50},
            NotificationChannel.PUSH: {'per_hour': 200, 'per_day': 1000},
            NotificationChannel.IN_APP: {'per_hour': 1000, 'per_day': 10000}
        }

        self._notification_counter = 0

    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        self._notification_counter += 1
        return f"notif_{int(datetime.now().timestamp())}_{self._notification_counter}"

    async def send_notification(
        self,
        user_id: str,
        template_type: str,
        variables: Dict[str, Any],
        channels: Optional[List[NotificationChannel]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        scheduled_at: Optional[datetime] = None,
        deduplication_key: Optional[str] = None
    ) -> str:
        """Send notification through specified channels"""

        notification_id = self._generate_notification_id()

        # Default to all channels if none specified
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP]

        # Create notification request
        request = NotificationRequest(
            id=notification_id,
            user_id=user_id,
            template_type=template_type,
            priority=priority,
            channels=channels,
            variables=variables,
            scheduled_at=scheduled_at,
            deduplication_key=deduplication_key
        )

        # Check for deduplication
        dedup_key = request.generate_dedup_key()
        if await self._is_duplicate(dedup_key):
            logger.info(f"Notification {notification_id} skipped due to deduplication")
            return notification_id

        # Store deduplication key
        self.deduplication_cache[dedup_key] = datetime.now()

        # Create execution tracker
        execution = NotificationExecution(request=request, status=DeliveryStatus.PENDING)
        self.executions[notification_id] = execution

        # Process immediately or schedule
        if scheduled_at and scheduled_at > datetime.now():
            await self._schedule_notification(execution)
        else:
            await self._process_notification(execution)

        logger.info(f"Notification {notification_id} initiated for user {user_id}")
        return notification_id

    async def _process_notification(self, execution: NotificationExecution):
        """Process notification across all specified channels"""
        request = execution.request
        user_prefs = await self._get_user_preferences(request.user_id)

        # Filter channels based on user preferences
        enabled_channels = []
        for channel in request.channels:
            if (user_prefs.is_channel_enabled(channel) and
                user_prefs.is_type_enabled_for_channel(channel, request.template_type)):
                enabled_channels.append(channel)

        if not enabled_channels:
            logger.warning(f"No enabled channels for notification {request.id}")
            execution.status = DeliveryStatus.CANCELLED
            return

        # Check rate limits
        enabled_channels = await self._check_rate_limits(request.user_id, enabled_channels)

        if not enabled_channels:
            logger.warning(f"Rate limits exceeded for notification {request.id}")
            execution.status = DeliveryStatus.FAILED
            return

        # Process each channel
        tasks = []
        for channel in enabled_channels:
            # Check quiet hours for non-urgent notifications
            if (request.priority != NotificationPriority.URGENT and
                user_prefs.is_in_quiet_hours(channel)):
                continue

            tasks.append(self._send_via_channel(execution, channel))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Notification {request.id} processed across {len(tasks)} channels")

    async def _send_via_channel(self, execution: NotificationExecution, channel: NotificationChannel):
        """Send notification via specific channel"""
        request = execution.request
        delivery = ChannelDelivery(channel=channel, status=DeliveryStatus.PENDING)

        try:
            if channel == NotificationChannel.EMAIL:
                result = await self._send_email(request)
            elif channel == NotificationChannel.SMS:
                result = await self._send_sms(request)
            elif channel == NotificationChannel.PUSH:
                result = await self._send_push(request)
            elif channel == NotificationChannel.IN_APP:
                result = await self._send_in_app(request)
            else:
                raise ValueError(f"Unknown channel: {channel}")

            delivery.status = DeliveryStatus.SENT
            delivery.message_id = result.get('message_id')
            delivery.sent_at = datetime.now()
            delivery.metadata = result

        except Exception as e:
            logger.error(f"Failed to send notification {request.id} via {channel.value}: {e}")
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = str(e)

        execution.update_channel_delivery(channel, delivery)

    async def _send_email(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send email notification"""
        template_mapping = {
            'document_analysis_complete': 'document_upload_confirmation',
            'deadline_reminder': 'deadline_reminder',
            'case_update': 'feature_announcement',
            'payment_receipt': 'payment_receipt',
            'welcome': 'welcome'
        }

        template = template_mapping.get(request.template_type, 'feature_announcement')

        result = await self.email_system.send_email(
            template_type=template,
            recipient_email=request.variables.get('email', f'user_{request.user_id}@example.com'),
            variables=request.variables
        )

        return {'message_id': result.get('message_id'), 'provider': 'email'}

    async def _send_sms(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send SMS notification"""
        template_mapping = {
            'deadline_reminder': 'urgent_deadline',
            'case_update': 'document_request',
            'payment_failure': 'payment_failure',
            'security_alert': 'security_alert'
        }

        template = template_mapping.get(request.template_type, 'urgent_deadline')
        phone_number = request.variables.get('phone', '+1234567890')

        result = await self.sms_system.send_sms(
            template_type=template,
            phone_number=phone_number,
            variables=request.variables
        )

        return {'message_id': result.get('message_id'), 'provider': 'sms'}

    async def _send_push(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send push notification"""
        template_mapping = {
            'document_analysis_complete': 'document_analysis',
            'qa_response': 'qa_response',
            'case_update': 'case_update',
            'deadline_reminder': 'deadline_reminder'
        }

        template = template_mapping.get(request.template_type, 'case_update')
        device_tokens = request.variables.get('device_tokens', [f'device_{request.user_id}'])

        result = await self.push_system.send_notification(
            template_type=template,
            device_tokens=device_tokens,
            variables=request.variables
        )

        return {'message_id': result.get('message_id'), 'provider': 'push'}

    async def _send_in_app(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send in-app notification"""
        type_mapping = {
            'document_analysis_complete': InAppNotificationType.DOCUMENT_ANALYSIS,
            'qa_response': InAppNotificationType.QA_RESPONSE,
            'case_update': InAppNotificationType.CASE_UPDATE,
            'deadline_reminder': InAppNotificationType.DEADLINE_REMINDER,
            'attorney_action': InAppNotificationType.ATTORNEY_ACTION,
            'system_alert': InAppNotificationType.SYSTEM_ALERT,
            'payment_receipt': InAppNotificationType.PAYMENT,
            'security_alert': InAppNotificationType.SECURITY
        }

        notification_type = type_mapping.get(request.template_type, InAppNotificationType.SYSTEM_ALERT)

        notification = await self.in_app_system.create_notification(
            user_id=request.user_id,
            notification_type=notification_type,
            variables=request.variables
        )

        return {'message_id': notification.id if notification else None, 'provider': 'in_app'}

    async def _is_duplicate(self, dedup_key: str) -> bool:
        """Check if notification is duplicate within deduplication window"""
        if dedup_key not in self.deduplication_cache:
            return False

        cached_time = self.deduplication_cache[dedup_key]
        return (datetime.now() - cached_time).total_seconds() < (self.dedup_window_minutes * 60)

    async def _check_rate_limits(self, user_id: str, channels: List[NotificationChannel]) -> List[NotificationChannel]:
        """Check rate limits for user and channels"""
        allowed_channels = []
        now = datetime.now()

        for channel in channels:
            limits = self.rate_limits[channel]
            counter_key = f"{user_id}:{channel.value}"
            counter = self.rate_limit_counters[counter_key]

            # Clean old entries
            cutoff_hour = now - timedelta(hours=1)
            cutoff_day = now - timedelta(days=1)

            while counter and counter[0] < cutoff_day:
                counter.popleft()

            # Count recent sends
            hour_count = sum(1 for timestamp in counter if timestamp >= cutoff_hour)
            day_count = len(counter)

            if hour_count < limits['per_hour'] and day_count < limits['per_day']:
                allowed_channels.append(channel)
                counter.append(now)
            else:
                logger.warning(f"Rate limit exceeded for user {user_id} on channel {channel.value}")

        return allowed_channels

    async def _get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get or create user preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(user_id)
        return self.user_preferences[user_id]

    async def _schedule_notification(self, execution: NotificationExecution):
        """Schedule notification for future delivery"""
        # In a production system, this would integrate with a job scheduler like Celery
        logger.info(f"Notification {execution.request.id} scheduled for {execution.request.scheduled_at}")
        # For now, we'll just mark it as pending
        execution.status = DeliveryStatus.PENDING

    async def get_notification_status(self, notification_id: str) -> Optional[NotificationExecution]:
        """Get status of notification execution"""
        return self.executions.get(notification_id)

    async def get_user_notifications(self, user_id: str, limit: int = 50) -> List[NotificationExecution]:
        """Get notifications for user"""
        user_notifications = [
            execution for execution in self.executions.values()
            if execution.request.user_id == user_id
        ]
        return sorted(user_notifications, key=lambda x: x.created_at, reverse=True)[:limit]

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user notification preferences"""
        user_prefs = await self._get_user_preferences(user_id)

        for channel, settings in preferences.items():
            if channel in user_prefs.preferences:
                user_prefs.preferences[channel].update(settings)

        logger.info(f"Updated preferences for user {user_id}")

    async def retry_failed_notification(self, notification_id: str) -> bool:
        """Retry failed notification"""
        execution = self.executions.get(notification_id)
        if not execution:
            return False

        # Only retry failed deliveries
        failed_channels = [
            channel for channel, delivery in execution.channel_deliveries.items()
            if delivery.status == DeliveryStatus.FAILED and delivery.retry_count < 3
        ]

        if not failed_channels:
            return False

        # Retry failed channels
        for channel in failed_channels:
            delivery = execution.channel_deliveries[channel]
            delivery.retry_count += 1
            delivery.status = DeliveryStatus.PENDING

            await self._send_via_channel(execution, channel)

        logger.info(f"Retried notification {notification_id} for {len(failed_channels)} channels")
        return True

    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel pending notification"""
        execution = self.executions.get(notification_id)
        if not execution or execution.status not in [DeliveryStatus.PENDING]:
            return False

        execution.status = DeliveryStatus.CANCELLED
        logger.info(f"Cancelled notification {notification_id}")
        return True

    async def get_delivery_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get delivery statistics"""
        executions = self.executions.values()
        if user_id:
            executions = [e for e in executions if e.request.user_id == user_id]

        stats = {
            'total': len(executions),
            'by_status': defaultdict(int),
            'by_channel': defaultdict(lambda: defaultdict(int)),
            'by_priority': defaultdict(int),
            'success_rate': 0
        }

        for execution in executions:
            stats['by_status'][execution.status.value] += 1
            stats['by_priority'][execution.request.priority.value] += 1

            for channel, delivery in execution.channel_deliveries.items():
                stats['by_channel'][channel.value][delivery.status.value] += 1

        # Calculate success rate
        successful = stats['by_status'][DeliveryStatus.DELIVERED.value] + stats['by_status'][DeliveryStatus.SENT.value]
        if stats['total'] > 0:
            stats['success_rate'] = (successful / stats['total']) * 100

        return stats

    # Quick notification sending methods
    async def notify_document_analysis_complete(
        self, user_id: str, document_name: str, document_id: str,
        user_email: str, analysis_type: str = "comprehensive", key_findings_count: int = 0
    ) -> str:
        """Quick method to notify document analysis completion across all channels"""
        return await self.send_notification(
            user_id=user_id,
            template_type='document_analysis_complete',
            variables={
                'document_name': document_name,
                'document_id': document_id,
                'email': user_email,
                'analysis_type': analysis_type,
                'key_findings_count': key_findings_count
            },
            channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP],
            priority=NotificationPriority.MEDIUM
        )

    async def notify_urgent_deadline(
        self, user_id: str, task_name: str, task_id: str, user_phone: str,
        user_email: str, time_remaining: str
    ) -> str:
        """Quick method to send urgent deadline reminder across all channels"""
        return await self.send_notification(
            user_id=user_id,
            template_type='deadline_reminder',
            variables={
                'task_name': task_name,
                'task_id': task_id,
                'phone': user_phone,
                'email': user_email,
                'time_remaining': time_remaining
            },
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS,
                     NotificationChannel.PUSH, NotificationChannel.IN_APP],
            priority=NotificationPriority.URGENT
        )

    async def notify_case_update(
        self, user_id: str, case_name: str, case_id: str, user_email: str,
        old_status: str, new_status: str, update_notes: str = ""
    ) -> str:
        """Quick method to notify case status update"""
        return await self.send_notification(
            user_id=user_id,
            template_type='case_update',
            variables={
                'case_name': case_name,
                'case_id': case_id,
                'email': user_email,
                'old_status': old_status,
                'new_status': new_status,
                'update_notes': update_notes
            },
            channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.IN_APP],
            priority=NotificationPriority.MEDIUM
        )


# Global orchestrator instance
notification_orchestrator = NotificationOrchestrator()


# FastAPI endpoints
def get_orchestrator_endpoints():
    """Returns FastAPI endpoints for notification orchestration"""
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    from typing import Optional, List

    router = APIRouter(prefix="/api/notifications/orchestrator", tags=["notification-orchestration"])

    class SendNotificationRequest(BaseModel):
        user_id: str
        template_type: str
        variables: Dict[str, Any]
        channels: Optional[List[str]] = None
        priority: str = "medium"
        scheduled_at: Optional[str] = None

    class UpdatePreferencesRequest(BaseModel):
        user_id: str
        preferences: Dict[str, Any]

    @router.post("/send")
    async def send_notification(request: SendNotificationRequest):
        """Send unified notification"""
        try:
            channels = None
            if request.channels:
                channels = [NotificationChannel(ch) for ch in request.channels]

            priority = NotificationPriority(request.priority)

            scheduled_at = None
            if request.scheduled_at:
                scheduled_at = datetime.fromisoformat(request.scheduled_at)

            notification_id = await notification_orchestrator.send_notification(
                user_id=request.user_id,
                template_type=request.template_type,
                variables=request.variables,
                channels=channels,
                priority=priority,
                scheduled_at=scheduled_at
            )

            return {"notification_id": notification_id, "status": "sent"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/status/{notification_id}")
    async def get_status(notification_id: str):
        """Get notification status"""
        execution = await notification_orchestrator.get_notification_status(notification_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {
            "id": execution.request.id,
            "status": execution.status.value,
            "created_at": execution.created_at.isoformat(),
            "updated_at": execution.updated_at.isoformat(),
            "channels": {
                channel.value: {
                    "status": delivery.status.value,
                    "message_id": delivery.message_id,
                    "sent_at": delivery.sent_at.isoformat() if delivery.sent_at else None,
                    "error": delivery.error_message
                }
                for channel, delivery in execution.channel_deliveries.items()
            }
        }

    @router.get("/user/{user_id}/notifications")
    async def get_user_notifications(user_id: str, limit: int = 50):
        """Get user notifications"""
        executions = await notification_orchestrator.get_user_notifications(user_id, limit)
        return [
            {
                "id": exec.request.id,
                "template_type": exec.request.template_type,
                "priority": exec.request.priority.value,
                "status": exec.status.value,
                "created_at": exec.created_at.isoformat(),
                "channels": list(exec.channel_deliveries.keys())
            }
            for exec in executions
        ]

    @router.post("/preferences")
    async def update_preferences(request: UpdatePreferencesRequest):
        """Update user notification preferences"""
        try:
            await notification_orchestrator.update_user_preferences(
                request.user_id, request.preferences
            )
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/retry/{notification_id}")
    async def retry_notification(notification_id: str):
        """Retry failed notification"""
        success = await notification_orchestrator.retry_failed_notification(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found or not retryable")
        return {"success": True}

    @router.post("/cancel/{notification_id}")
    async def cancel_notification(notification_id: str):
        """Cancel pending notification"""
        success = await notification_orchestrator.cancel_notification(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found or not cancellable")
        return {"success": True}

    @router.get("/stats")
    async def get_statistics(user_id: Optional[str] = None):
        """Get delivery statistics"""
        return await notification_orchestrator.get_delivery_statistics(user_id)

    # Quick notification endpoints
    @router.post("/quick/document-analysis")
    async def quick_document_analysis(
        user_id: str, document_name: str, document_id: str,
        user_email: str, analysis_type: str = "comprehensive", key_findings_count: int = 0
    ):
        """Quick document analysis notification"""
        notification_id = await notification_orchestrator.notify_document_analysis_complete(
            user_id, document_name, document_id, user_email, analysis_type, key_findings_count
        )
        return {"notification_id": notification_id}

    @router.post("/quick/urgent-deadline")
    async def quick_urgent_deadline(
        user_id: str, task_name: str, task_id: str, user_phone: str,
        user_email: str, time_remaining: str
    ):
        """Quick urgent deadline notification"""
        notification_id = await notification_orchestrator.notify_urgent_deadline(
            user_id, task_name, task_id, user_phone, user_email, time_remaining
        )
        return {"notification_id": notification_id}

    @router.post("/quick/case-update")
    async def quick_case_update(
        user_id: str, case_name: str, case_id: str, user_email: str,
        old_status: str, new_status: str, update_notes: str = ""
    ):
        """Quick case update notification"""
        notification_id = await notification_orchestrator.notify_case_update(
            user_id, case_name, case_id, user_email, old_status, new_status, update_notes
        )
        return {"notification_id": notification_id}

    return router


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        orchestrator = NotificationOrchestrator()

        # Send comprehensive notification
        notification_id = await orchestrator.notify_document_analysis_complete(
            user_id="user123",
            document_name="Contract_Review.pdf",
            document_id="doc456",
            user_email="user@example.com",
            analysis_type="contract",
            key_findings_count=5
        )

        print(f"Sent notification: {notification_id}")

        # Check status
        execution = await orchestrator.get_notification_status(notification_id)
        if execution:
            print(f"Status: {execution.status.value}")
            print(f"Channels: {list(execution.channel_deliveries.keys())}")

        # Get statistics
        stats = await orchestrator.get_delivery_statistics()
        print(f"Total notifications: {stats['total']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")

        print("Notification orchestration demo completed!")

    asyncio.run(demo())