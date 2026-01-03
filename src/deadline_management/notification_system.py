"""
Comprehensive Notification and Alert System for Legal AI System

Provides multi-channel notification capabilities for legal deadlines,
court dates, and critical events with escalation and acknowledgment tracking.
"""

from typing import List, Dict, Any, Optional, Union, Callable, Set
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from urllib.parse import urlencode
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import ssl

import aiohttp
import websockets
from twilio.rest import Client as TwilioClient
from slack_sdk.web.async_client import AsyncWebClient as SlackClient
import requests

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    PUSH = "push"
    VOICE = "voice"
    IN_APP = "in_app"


class NotificationPriority(Enum):
    """Notification priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class NotificationType(Enum):
    """Types of notifications."""
    DEADLINE_REMINDER = "deadline_reminder"
    DEADLINE_OVERDUE = "deadline_overdue"
    COURT_REMINDER = "court_reminder"
    FILING_CONFIRMATION = "filing_confirmation"
    CASE_UPDATE = "case_update"
    SYSTEM_ALERT = "system_alert"
    ERROR_ALERT = "error_alert"
    CLIENT_MESSAGE = "client_message"
    TASK_ASSIGNMENT = "task_assignment"
    APPROVAL_REQUEST = "approval_request"


class NotificationStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"


@dataclass
class NotificationTemplate:
    """Template for notification content."""
    name: str
    subject_template: str
    body_template: str
    html_template: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Render template with context variables."""
        try:
            subject = self.subject_template.format(**context)
            body = self.body_template.format(**context)
            html = self.html_template.format(**context) if self.html_template else None
            
            return {
                'subject': subject,
                'body': body,
                'html': html
            }
        except KeyError as e:
            logger.error(f"Template rendering failed, missing variable: {e}")
            raise ValueError(f"Missing template variable: {e}")


@dataclass
class NotificationRecipient:
    """Notification recipient information."""
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_user_id: Optional[str] = None
    teams_user_id: Optional[str] = None
    timezone: str = "UTC"
    preferences: Dict[NotificationChannel, bool] = field(default_factory=dict)
    escalation_contacts: List[str] = field(default_factory=list)
    
    def get_contact_info(self, channel: NotificationChannel) -> Optional[str]:
        """Get contact information for specific channel."""
        contact_map = {
            NotificationChannel.EMAIL: self.email,
            NotificationChannel.SMS: self.phone,
            NotificationChannel.VOICE: self.phone,
            NotificationChannel.SLACK: self.slack_user_id,
            NotificationChannel.TEAMS: self.teams_user_id
        }
        return contact_map.get(channel)
    
    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if notification channel is enabled for recipient."""
        return self.preferences.get(channel, True)  # Default to enabled


@dataclass
class NotificationRequest:
    """Request to send a notification."""
    notification_type: NotificationType
    priority: NotificationPriority
    recipients: List[NotificationRecipient]
    template_name: str
    context: Dict[str, Any]
    channels: List[NotificationChannel] = field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    require_acknowledgment: bool = False
    escalation_enabled: bool = False
    escalation_delay: timedelta = field(default_factory=lambda: timedelta(hours=1))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        data['notification_type'] = self.notification_type.value
        data['priority'] = self.priority.value
        data['channels'] = [c.value for c in self.channels]
        if self.scheduled_time:
            data['scheduled_time'] = self.scheduled_time.isoformat()
        if self.expiry_time:
            data['expiry_time'] = self.expiry_time.isoformat()
        data['escalation_delay'] = self.escalation_delay.total_seconds()
        return data


@dataclass
class NotificationRecord:
    """Record of a sent notification."""
    notification_id: str
    request: NotificationRequest
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    failed_channels: List[NotificationChannel] = field(default_factory=list)
    retry_count: int = 0
    error_message: Optional[str] = None
    delivery_details: Dict[NotificationChannel, Dict[str, Any]] = field(default_factory=dict)


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""
    
    @abstractmethod
    async def send(self, recipient: NotificationRecipient, content: Dict[str, str], 
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send notification through this provider."""
        pass
    
    @abstractmethod
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """Check if provider supports the given channel."""
        pass


class EmailProvider(NotificationProvider):
    """Email notification provider."""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_host = smtp_config.get('host', 'localhost')
        self.smtp_port = smtp_config.get('port', 587)
        self.username = smtp_config.get('username')
        self.password = smtp_config.get('password')
        self.use_tls = smtp_config.get('use_tls', True)
        self.from_address = smtp_config.get('from_address', 'noreply@example.com')
        self.from_name = smtp_config.get('from_name', 'Legal AI System')
    
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """Check if provider supports email channel."""
        return channel == NotificationChannel.EMAIL
    
    async def send(self, recipient: NotificationRecipient, content: Dict[str, str],
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send email notification."""
        try:
            if not recipient.email:
                return {'success': False, 'error': 'No email address provided'}
            
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = content['subject']
            msg['From'] = f"{self.from_name} <{self.from_address}>"
            msg['To'] = recipient.email
            
            # Add plain text part
            text_part = MimeText(content['body'], 'plain')
            msg.attach(text_part)
            
            # Add HTML part if available
            if content.get('html'):
                html_part = MimeText(content['html'], 'html')
                msg.attach(html_part)
            
            # Send email
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp, msg
            )
            
            return {
                'success': True,
                'provider': 'email',
                'recipient': recipient.email,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'email'
            }
    
    def _send_smtp(self, msg: MimeMultipart):
        """Send email via SMTP (synchronous)."""
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls(context=context)
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            server.send_message(msg)


class SMSProvider(NotificationProvider):
    """SMS notification provider using Twilio."""
    
    def __init__(self, twilio_config: Dict[str, Any]):
        self.account_sid = twilio_config['account_sid']
        self.auth_token = twilio_config['auth_token']
        self.from_phone = twilio_config['from_phone']
        self.client = TwilioClient(self.account_sid, self.auth_token)
    
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """Check if provider supports SMS/Voice channels."""
        return channel in [NotificationChannel.SMS, NotificationChannel.VOICE]
    
    async def send(self, recipient: NotificationRecipient, content: Dict[str, str],
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send SMS notification."""
        try:
            if not recipient.phone:
                return {'success': False, 'error': 'No phone number provided'}
            
            # Send SMS
            message = await asyncio.get_event_loop().run_in_executor(
                None, self._send_sms, recipient.phone, content['body']
            )
            
            return {
                'success': True,
                'provider': 'sms',
                'recipient': recipient.phone,
                'message_sid': message.sid,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'sms'
            }
    
    def _send_sms(self, to_phone: str, body: str):
        """Send SMS via Twilio (synchronous)."""
        return self.client.messages.create(
            body=body,
            from_=self.from_phone,
            to=to_phone
        )


class SlackProvider(NotificationProvider):
    """Slack notification provider."""
    
    def __init__(self, slack_config: Dict[str, Any]):
        self.bot_token = slack_config['bot_token']
        self.client = SlackClient(token=self.bot_token)
    
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """Check if provider supports Slack channel."""
        return channel == NotificationChannel.SLACK
    
    async def send(self, recipient: NotificationRecipient, content: Dict[str, str],
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send Slack notification."""
        try:
            if not recipient.slack_user_id:
                return {'success': False, 'error': 'No Slack user ID provided'}
            
            # Format message for Slack
            slack_message = {
                'channel': recipient.slack_user_id,
                'text': content['subject'],
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f"*{content['subject']}*\n{content['body']}"
                        }
                    }
                ]
            }
            
            # Add action buttons for acknowledgment if required
            if metadata and metadata.get('require_acknowledgment'):
                slack_message['blocks'].append({
                    'type': 'actions',
                    'elements': [
                        {
                            'type': 'button',
                            'text': {'type': 'plain_text', 'text': 'Acknowledge'},
                            'action_id': f"ack_{metadata.get('notification_id')}",
                            'style': 'primary'
                        }
                    ]
                })
            
            response = await self.client.chat_postMessage(**slack_message)
            
            return {
                'success': response['ok'],
                'provider': 'slack',
                'recipient': recipient.slack_user_id,
                'message_ts': response.get('ts'),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Slack sending failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'slack'
            }


class WebhookProvider(NotificationProvider):
    """Webhook notification provider."""
    
    def __init__(self, webhook_config: Dict[str, Any]):
        self.webhooks = webhook_config.get('webhooks', {})
        self.default_url = webhook_config.get('default_url')
        self.headers = webhook_config.get('headers', {})
        self.timeout = webhook_config.get('timeout', 30)
    
    def supports_channel(self, channel: NotificationChannel) -> bool:
        """Check if provider supports webhook channel."""
        return channel == NotificationChannel.WEBHOOK
    
    async def send(self, recipient: NotificationRecipient, content: Dict[str, str],
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send webhook notification."""
        try:
            # Get webhook URL for recipient or use default
            webhook_url = self.webhooks.get(recipient.user_id, self.default_url)
            if not webhook_url:
                return {'success': False, 'error': 'No webhook URL configured'}
            
            # Prepare payload
            payload = {
                'recipient': {
                    'user_id': recipient.user_id,
                    'name': recipient.name
                },
                'notification': content,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Send webhook
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    success = response.status < 400
                    response_text = await response.text()
                    
                    return {
                        'success': success,
                        'provider': 'webhook',
                        'webhook_url': webhook_url,
                        'status_code': response.status,
                        'response': response_text[:500],  # Limit response length
                        'timestamp': datetime.now().isoformat()
                    }
        
        except Exception as e:
            logger.error(f"Webhook sending failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'webhook'
            }


class NotificationScheduler:
    """Handles scheduled notifications and reminders."""
    
    def __init__(self):
        self.scheduled_notifications: Dict[str, asyncio.Task] = {}
        self.recurring_tasks: Dict[str, asyncio.Task] = {}
    
    def schedule_notification(self, notification_id: str, 
                            send_time: datetime,
                            send_callback: Callable) -> bool:
        """Schedule a notification to be sent at a specific time."""
        try:
            delay = (send_time - datetime.now()).total_seconds()
            if delay <= 0:
                # Send immediately if scheduled time has passed
                asyncio.create_task(send_callback())
                return True
            
            # Cancel existing task if any
            if notification_id in self.scheduled_notifications:
                self.scheduled_notifications[notification_id].cancel()
            
            # Schedule new task
            async def delayed_send():
                await asyncio.sleep(delay)
                await send_callback()
                # Clean up task reference
                if notification_id in self.scheduled_notifications:
                    del self.scheduled_notifications[notification_id]
            
            self.scheduled_notifications[notification_id] = asyncio.create_task(delayed_send())
            return True
        
        except Exception as e:
            logger.error(f"Failed to schedule notification: {str(e)}")
            return False
    
    def cancel_notification(self, notification_id: str) -> bool:
        """Cancel a scheduled notification."""
        if notification_id in self.scheduled_notifications:
            self.scheduled_notifications[notification_id].cancel()
            del self.scheduled_notifications[notification_id]
            return True
        return False
    
    def schedule_recurring_reminders(self, deadline_id: str,
                                   deadline_time: datetime,
                                   reminder_intervals: List[timedelta],
                                   reminder_callback: Callable):
        """Schedule recurring reminders for a deadline."""
        async def reminder_loop():
            for interval in sorted(reminder_intervals, reverse=True):
                reminder_time = deadline_time - interval
                delay = (reminder_time - datetime.now()).total_seconds()
                
                if delay > 0:
                    await asyncio.sleep(delay)
                    await reminder_callback(interval)
        
        if deadline_id in self.recurring_tasks:
            self.recurring_tasks[deadline_id].cancel()
        
        self.recurring_tasks[deadline_id] = asyncio.create_task(reminder_loop())
    
    def cancel_recurring_reminders(self, deadline_id: str) -> bool:
        """Cancel recurring reminders for a deadline."""
        if deadline_id in self.recurring_tasks:
            self.recurring_tasks[deadline_id].cancel()
            del self.recurring_tasks[deadline_id]
            return True
        return False


class NotificationSystem:
    """Main notification system manager."""
    
    def __init__(self):
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.scheduler = NotificationScheduler()
        self.notification_records: Dict[str, NotificationRecord] = {}
        self.escalation_tasks: Dict[str, asyncio.Task] = {}
        
        # Load default templates
        self._load_default_templates()
    
    def register_provider(self, channel: NotificationChannel, provider: NotificationProvider):
        """Register a notification provider for a channel."""
        self.providers[channel] = provider
        logger.info(f"Registered provider for {channel.value}")
    
    def add_template(self, template: NotificationTemplate):
        """Add a notification template."""
        self.templates[template.name] = template
        logger.info(f"Added template: {template.name}")
    
    async def send_notification(self, request: NotificationRequest) -> str:
        """Send a notification based on the request."""
        notification_id = f"notif_{datetime.now().timestamp()}_{hash(str(request))}"
        
        # Create notification record
        record = NotificationRecord(
            notification_id=notification_id,
            request=request,
            status=NotificationStatus.PENDING,
            created_at=datetime.now()
        )
        self.notification_records[notification_id] = record
        
        # Schedule notification if needed
        if request.scheduled_time:
            self.scheduler.schedule_notification(
                notification_id,
                request.scheduled_time,
                lambda: self._send_immediate(notification_id)
            )
            logger.info(f"Scheduled notification {notification_id} for {request.scheduled_time}")
            return notification_id
        
        # Send immediately
        await self._send_immediate(notification_id)
        return notification_id
    
    async def _send_immediate(self, notification_id: str):
        """Send notification immediately."""
        try:
            record = self.notification_records[notification_id]
            request = record.request
            
            # Get template
            template = self.templates.get(request.template_name)
            if not template:
                logger.error(f"Template {request.template_name} not found")
                record.status = NotificationStatus.FAILED
                record.error_message = f"Template {request.template_name} not found"
                return
            
            # Render content
            content = template.render(request.context)
            
            # Determine channels
            channels = request.channels if request.channels else list(self.providers.keys())
            
            # Send to all recipients
            all_success = True
            failed_channels = []
            
            for recipient in request.recipients:
                for channel in channels:
                    if not recipient.is_channel_enabled(channel):
                        continue
                    
                    provider = self.providers.get(channel)
                    if not provider or not provider.supports_channel(channel):
                        continue
                    
                    # Send notification
                    result = await provider.send(
                        recipient, 
                        content, 
                        {
                            'notification_id': notification_id,
                            'require_acknowledgment': request.require_acknowledgment,
                            'notification_type': request.notification_type.value,
                            'priority': request.priority.value
                        }
                    )
                    
                    # Record delivery details
                    if channel not in record.delivery_details:
                        record.delivery_details[channel] = {}
                    record.delivery_details[channel][recipient.user_id] = result
                    
                    if not result.get('success'):
                        all_success = False
                        failed_channels.append(channel)
                        logger.error(f"Failed to send via {channel.value}: {result.get('error')}")
            
            # Update record
            record.sent_at = datetime.now()
            record.status = NotificationStatus.SENT if all_success else NotificationStatus.FAILED
            record.failed_channels = list(set(failed_channels))
            
            if all_success:
                record.status = NotificationStatus.DELIVERED
                record.delivered_at = datetime.now()
            
            # Set up escalation if enabled and required
            if (request.escalation_enabled and 
                request.require_acknowledgment and 
                request.priority in [NotificationPriority.CRITICAL, NotificationPriority.HIGH]):
                
                self._setup_escalation(notification_id)
            
            logger.info(f"Notification {notification_id} sent with status: {record.status.value}")
        
        except Exception as e:
            logger.error(f"Failed to send notification {notification_id}: {str(e)}")
            record.status = NotificationStatus.FAILED
            record.error_message = str(e)
    
    def _setup_escalation(self, notification_id: str):
        """Set up escalation for unacknowledged notifications."""
        record = self.notification_records[notification_id]
        
        async def escalate():
            await asyncio.sleep(record.request.escalation_delay.total_seconds())
            
            # Check if still not acknowledged
            if record.status != NotificationStatus.ACKNOWLEDGED:
                logger.warning(f"Escalating unacknowledged notification: {notification_id}")
                
                # Send escalation notifications
                for recipient in record.request.recipients:
                    for escalation_contact in recipient.escalation_contacts:
                        # Create escalation notification
                        escalation_request = NotificationRequest(
                            notification_type=NotificationType.SYSTEM_ALERT,
                            priority=NotificationPriority.CRITICAL,
                            recipients=[
                                NotificationRecipient(
                                    user_id=escalation_contact,
                                    name=f"Escalation Contact for {recipient.name}",
                                    email=escalation_contact  # Assuming email format
                                )
                            ],
                            template_name='escalation_alert',
                            context={
                                'original_recipient': recipient.name,
                                'original_subject': record.request.context.get('subject', 'Unknown'),
                                'notification_time': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                                'escalation_reason': 'Notification not acknowledged within required timeframe'
                            },
                            require_acknowledgment=True
                        )
                        
                        await self.send_notification(escalation_request)
        
        self.escalation_tasks[notification_id] = asyncio.create_task(escalate())
    
    async def acknowledge_notification(self, notification_id: str, user_id: str) -> bool:
        """Acknowledge a notification."""
        if notification_id not in self.notification_records:
            return False
        
        record = self.notification_records[notification_id]
        record.status = NotificationStatus.ACKNOWLEDGED
        record.acknowledged_at = datetime.now()
        record.acknowledged_by = user_id
        
        # Cancel escalation if active
        if notification_id in self.escalation_tasks:
            self.escalation_tasks[notification_id].cancel()
            del self.escalation_tasks[notification_id]
        
        logger.info(f"Notification {notification_id} acknowledged by {user_id}")
        return True
    
    def get_notification_status(self, notification_id: str) -> Optional[NotificationRecord]:
        """Get notification status and details."""
        return self.notification_records.get(notification_id)
    
    def _load_default_templates(self):
        """Load default notification templates."""
        templates = [
            NotificationTemplate(
                name='deadline_reminder',
                subject_template='URGENT: Legal Deadline Approaching - {deadline_title}',
                body_template='''
Legal Deadline Reminder

Deadline: {deadline_title}
Case: {case_name}
Due Date: {due_date}
Time Remaining: {time_remaining}

Description: {deadline_description}

Priority: {priority}
Consequences if missed: {consequences}

Please ensure this deadline is met on time.
                ''',
                html_template='''
<h2>⚠️ Legal Deadline Reminder</h2>
<p><strong>Deadline:</strong> {deadline_title}</p>
<p><strong>Case:</strong> {case_name}</p>
<p><strong>Due Date:</strong> {due_date}</p>
<p><strong>Time Remaining:</strong> <span style="color: red; font-weight: bold;">{time_remaining}</span></p>
<p><strong>Description:</strong> {deadline_description}</p>
<p><strong>Priority:</strong> <span style="color: orange;">{priority}</span></p>
<p><strong>Consequences if missed:</strong> {consequences}</p>
<p style="margin-top: 20px; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeeba;">
<strong>⚠️ Please ensure this deadline is met on time.</strong>
</p>
                '''
            ),
            NotificationTemplate(
                name='court_hearing_reminder',
                subject_template='Court Hearing Tomorrow - {hearing_title}',
                body_template='''
Court Hearing Reminder

Hearing: {hearing_title}
Case: {case_name}
Date & Time: {hearing_date} at {hearing_time}
Location: {court_location}
Courtroom: {courtroom}
Judge: {judge}

Please be prepared and arrive 15 minutes early.
                ''',
                html_template='''
<h2>⚖️ Court Hearing Reminder</h2>
<p><strong>Hearing:</strong> {hearing_title}</p>
<p><strong>Case:</strong> {case_name}</p>
<p><strong>Date & Time:</strong> {hearing_date} at {hearing_time}</p>
<p><strong>Location:</strong> {court_location}</p>
<p><strong>Courtroom:</strong> {courtroom}</p>
<p><strong>Judge:</strong> {judge}</p>
<p style="margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb;">
<strong>📍 Please be prepared and arrive 15 minutes early.</strong>
</p>
                '''
            ),
            NotificationTemplate(
                name='deadline_overdue',
                subject_template='CRITICAL: Deadline OVERDUE - {deadline_title}',
                body_template='''
CRITICAL ALERT: Legal Deadline Overdue

Deadline: {deadline_title}
Case: {case_name}
Original Due Date: {due_date}
Days Overdue: {days_overdue}

IMMEDIATE ACTION REQUIRED

Please contact the legal team immediately to address this overdue deadline.
                ''',
                html_template='''
<h2 style="color: red;">🚨 CRITICAL ALERT: Legal Deadline Overdue</h2>
<p><strong>Deadline:</strong> {deadline_title}</p>
<p><strong>Case:</strong> {case_name}</p>
<p><strong>Original Due Date:</strong> {due_date}</p>
<p><strong>Days Overdue:</strong> <span style="color: red; font-weight: bold;">{days_overdue}</span></p>
<div style="margin-top: 20px; padding: 15px; background-color: #f8d7da; border: 2px solid #f5c6cb; border-radius: 5px;">
<h3 style="color: red;">⚠️ IMMEDIATE ACTION REQUIRED</h3>
<p>Please contact the legal team immediately to address this overdue deadline.</p>
</div>
                '''
            ),
            NotificationTemplate(
                name='escalation_alert',
                subject_template='ESCALATION: Unacknowledged Notification - {original_subject}',
                body_template='''
Escalation Alert

An important notification sent to {original_recipient} has not been acknowledged.

Original Subject: {original_subject}
Notification Time: {notification_time}
Escalation Reason: {escalation_reason}

Please follow up immediately.
                '''
            )
        ]
        
        for template in templates:
            self.templates[template.name] = template


# Integration with deadline management system
class DeadlineNotificationManager:
    """Manages notifications specifically for legal deadlines."""
    
    def __init__(self, notification_system: NotificationSystem):
        self.notification_system = notification_system
        self.active_deadline_reminders: Dict[str, List[str]] = {}  # deadline_id -> notification_ids
    
    async def setup_deadline_notifications(self, 
                                         deadline_data: Dict[str, Any],
                                         recipients: List[NotificationRecipient]) -> List[str]:
        """Set up all notifications for a deadline."""
        deadline_id = deadline_data['deadline_id']
        due_date = datetime.fromisoformat(deadline_data['due_date'])
        priority = deadline_data.get('priority', 'medium')
        
        # Determine reminder schedule based on priority
        reminder_intervals = self._get_reminder_schedule(priority)
        
        notification_ids = []
        
        # Schedule reminders
        for interval in reminder_intervals:
            reminder_time = due_date - interval
            
            if reminder_time > datetime.now():  # Only schedule future reminders
                request = NotificationRequest(
                    notification_type=NotificationType.DEADLINE_REMINDER,
                    priority=NotificationPriority(priority),
                    recipients=recipients,
                    template_name='deadline_reminder',
                    context={
                        'deadline_title': deadline_data.get('title', 'Legal Deadline'),
                        'case_name': deadline_data.get('case_name', 'Unknown Case'),
                        'due_date': due_date.strftime('%Y-%m-%d %H:%M'),
                        'time_remaining': self._format_time_remaining(interval),
                        'deadline_description': deadline_data.get('description', 'No description'),
                        'priority': priority.upper(),
                        'consequences': deadline_data.get('consequences', 'Unknown consequences')
                    },
                    scheduled_time=reminder_time,
                    require_acknowledgment=priority in ['critical', 'high'],
                    escalation_enabled=priority == 'critical'
                )
                
                notification_id = await self.notification_system.send_notification(request)
                notification_ids.append(notification_id)
        
        # Schedule overdue check
        overdue_check_time = due_date + timedelta(hours=1)
        overdue_request = NotificationRequest(
            notification_type=NotificationType.DEADLINE_OVERDUE,
            priority=NotificationPriority.CRITICAL,
            recipients=recipients,
            template_name='deadline_overdue',
            context={
                'deadline_title': deadline_data.get('title', 'Legal Deadline'),
                'case_name': deadline_data.get('case_name', 'Unknown Case'),
                'due_date': due_date.strftime('%Y-%m-%d %H:%M'),
                'days_overdue': '1'  # Will be updated when sent
            },
            scheduled_time=overdue_check_time,
            require_acknowledgment=True,
            escalation_enabled=True
        )
        
        overdue_notification_id = await self.notification_system.send_notification(overdue_request)
        notification_ids.append(overdue_notification_id)
        
        self.active_deadline_reminders[deadline_id] = notification_ids
        return notification_ids
    
    def _get_reminder_schedule(self, priority: str) -> List[timedelta]:
        """Get reminder schedule based on deadline priority."""
        schedules = {
            'critical': [
                timedelta(days=7),
                timedelta(days=3),
                timedelta(days=1),
                timedelta(hours=4),
                timedelta(hours=1),
                timedelta(minutes=15)
            ],
            'high': [
                timedelta(days=7),
                timedelta(days=2),
                timedelta(hours=8),
                timedelta(hours=2)
            ],
            'medium': [
                timedelta(days=3),
                timedelta(days=1),
                timedelta(hours=4)
            ],
            'low': [
                timedelta(days=2),
                timedelta(hours=8)
            ]
        }
        
        return schedules.get(priority, schedules['medium'])
    
    def _format_time_remaining(self, interval: timedelta) -> str:
        """Format time remaining for display."""
        total_seconds = interval.total_seconds()
        
        if total_seconds >= 86400:  # Days
            days = int(total_seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''}"
        elif total_seconds >= 3600:  # Hours
            hours = int(total_seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:  # Minutes
            minutes = int(total_seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    async def cancel_deadline_notifications(self, deadline_id: str) -> bool:
        """Cancel all notifications for a deadline."""
        if deadline_id not in self.active_deadline_reminders:
            return False
        
        notification_ids = self.active_deadline_reminders[deadline_id]
        
        # Cancel scheduled notifications
        for notification_id in notification_ids:
            self.notification_system.scheduler.cancel_notification(notification_id)
        
        del self.active_deadline_reminders[deadline_id]
        return True


# Example usage
async def example_usage():
    """Example usage of the notification system."""
    
    # Initialize notification system
    notification_system = NotificationSystem()
    
    # Configure providers
    email_config = {
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'use_tls': True,
        'from_address': 'legal-ai@example.com',
        'from_name': 'Legal AI System'
    }
    
    slack_config = {
        'bot_token': 'xoxb-your-slack-bot-token'
    }
    
    # Register providers
    notification_system.register_provider(NotificationChannel.EMAIL, EmailProvider(email_config))
    notification_system.register_provider(NotificationChannel.SLACK, SlackProvider(slack_config))
    
    # Create recipients
    recipients = [
        NotificationRecipient(
            user_id='user_123',
            name='John Doe',
            email='john.doe@lawfirm.com',
            slack_user_id='U1234567890',
            preferences={
                NotificationChannel.EMAIL: True,
                NotificationChannel.SLACK: True
            },
            escalation_contacts=['supervisor@lawfirm.com']
        )
    ]
    
    # Send deadline reminder
    deadline_request = NotificationRequest(
        notification_type=NotificationType.DEADLINE_REMINDER,
        priority=NotificationPriority.HIGH,
        recipients=recipients,
        template_name='deadline_reminder',
        context={
            'deadline_title': 'File Motion to Dismiss',
            'case_name': 'Smith v. Jones',
            'due_date': '2024-01-15 17:00',
            'time_remaining': '2 days',
            'deadline_description': 'File motion to dismiss with prejudice',
            'priority': 'HIGH',
            'consequences': 'Case proceeds to discovery if not filed'
        },
        require_acknowledgment=True,
        escalation_enabled=True
    )
    
    notification_id = await notification_system.send_notification(deadline_request)
    print(f"Sent notification: {notification_id}")
    
    # Set up deadline notifications
    deadline_manager = DeadlineNotificationManager(notification_system)
    
    deadline_data = {
        'deadline_id': 'deadline_123',
        'title': 'File Appeal Brief',
        'due_date': '2024-01-20T17:00:00',
        'case_name': 'Johnson v. State',
        'priority': 'critical',
        'description': 'File appellant brief with court of appeals',
        'consequences': 'Appeal will be dismissed if not filed timely'
    }
    
    notification_ids = await deadline_manager.setup_deadline_notifications(deadline_data, recipients)
    print(f"Set up deadline notifications: {notification_ids}")


if __name__ == "__main__":
    asyncio.run(example_usage())