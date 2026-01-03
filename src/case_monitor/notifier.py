"""
Notification Manager for Case Monitoring

Handles multi-channel notifications for case changes including email, SMS,
webhooks, in-app notifications, and third-party integrations.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.config import settings
from .models import (
    NotificationEvent, NotificationChannel, ChangeDetection,
    MonitoringRule, AlertSeverity, MonitoredCase
)


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    """Configuration for notification delivery"""
    email_enabled: bool = True
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from_address: str = ""
    
    sms_enabled: bool = False
    sms_provider: str = "twilio"  # twilio, aws_sns, etc.
    sms_api_key: str = ""
    sms_api_secret: str = ""
    
    webhook_enabled: bool = True
    webhook_timeout_seconds: int = 30
    webhook_retry_attempts: int = 3
    
    slack_enabled: bool = False
    slack_bot_token: str = ""
    slack_default_channel: str = "#legal-alerts"
    
    teams_enabled: bool = False
    teams_webhook_url: str = ""
    
    push_enabled: bool = False
    push_service_key: str = ""
    
    max_notification_rate_per_hour: int = 100
    batch_notifications: bool = True
    batch_delay_seconds: int = 30


@dataclass
class NotificationTemplate:
    """Template for notification messages"""
    template_id: str
    name: str
    channel: NotificationChannel
    subject_template: str
    body_template: str
    html_template: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    severity_specific: bool = False
    change_type_specific: bool = False


class NotificationManager:
    """Manages notification delivery across multiple channels"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.pending_notifications: List[NotificationEvent] = []
        self.notification_history: List[NotificationEvent] = []
        self.rate_limiting: Dict[str, List[datetime]] = {}
        
        # Notification templates
        self.templates = self._load_notification_templates()
        
        # Batch processing
        self.batch_queue: Dict[NotificationChannel, List[NotificationEvent]] = {
            channel: [] for channel in NotificationChannel
        }
        
        # Start background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._is_running = False
        
        logger.info("Notification Manager initialized")
    
    async def start(self):
        """Start the notification manager"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # Start notification processing task
        self._background_tasks.append(
            asyncio.create_task(self._process_notification_queue())
        )
        
        # Start batch processing task
        self._background_tasks.append(
            asyncio.create_task(self._process_batch_notifications())
        )
        
        logger.info("Notification Manager started")
    
    async def stop(self):
        """Stop the notification manager"""
        self._is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
        logger.info("Notification Manager stopped")
    
    async def process_change(
        self,
        change_detection: ChangeDetection,
        monitoring_rule_ids: List[str]
    ):
        """Process a detected change and generate notifications"""
        
        try:
            # Get applicable monitoring rules
            rules = await self._get_monitoring_rules(monitoring_rule_ids)
            
            # Find matching rules
            matching_rules = []
            for rule in rules:
                if rule.matches_change(change_detection.change_type, change_detection.metadata):
                    matching_rules.append(rule)
            
            if not matching_rules:
                logger.debug(f"No matching rules for change {change_detection.change_id}")
                return
            
            # Generate notification events
            for rule in matching_rules:
                await self._generate_notification_event(change_detection, rule)
            
            logger.info(
                f"Generated notifications for change {change_detection.change_id} "
                f"using {len(matching_rules)} rules"
            )
            
        except Exception as e:
            logger.error(f"Change processing failed: {str(e)}")
    
    async def send_notification(
        self,
        channel: NotificationChannel,
        title: str,
        message: str,
        recipients: List[str],
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> NotificationEvent:
        """Send a notification directly"""
        
        try:
            # Create notification event
            event = NotificationEvent(
                event_id="",  # Will be auto-generated
                change_id="direct",
                rule_id="direct",
                monitor_id="direct",
                case_number="",
                court_id="",
                event_type=change_detection.change_type if 'change_detection' in locals() else None,
                severity=severity,
                title=title,
                message=message,
                channels=[channel],
                recipients=recipients,
                metadata=metadata or {}
            )
            
            # Add to queue
            await self._queue_notification(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Direct notification failed: {str(e)}")
            raise
    
    async def _generate_notification_event(
        self,
        change_detection: ChangeDetection,
        rule: MonitoringRule
    ):
        """Generate notification event from change and rule"""
        
        try:
            # Get recipients
            recipients = await self._get_notification_recipients(
                change_detection.monitor_id, rule
            )
            
            if not recipients:
                logger.warning(f"No recipients found for rule {rule.rule_id}")
                return
            
            # Generate message content
            title, message = await self._generate_message_content(
                change_detection, rule
            )
            
            # Create notification event
            event = NotificationEvent(
                event_id="",
                change_id=change_detection.change_id,
                rule_id=rule.rule_id,
                monitor_id=change_detection.monitor_id,
                case_number=change_detection.case_number,
                court_id=change_detection.court_id,
                event_type=change_detection.change_type,
                severity=change_detection.severity,
                title=title,
                message=message,
                channels=rule.notification_channels,
                recipients=recipients['external'],
                user_ids=recipients['internal'],
                metadata={
                    'rule_name': rule.name,
                    'change_metadata': change_detection.metadata
                }
            )
            
            # Queue for processing
            await self._queue_notification(event)
            
        except Exception as e:
            logger.error(f"Notification event generation failed: {str(e)}")
    
    async def _queue_notification(self, event: NotificationEvent):
        """Queue notification for processing"""
        
        # Check rate limiting
        if not await self._check_rate_limit(event):
            logger.warning(f"Rate limit exceeded for notification {event.event_id}")
            return
        
        # Add to appropriate queues
        if self.config.batch_notifications:
            for channel in event.channels:
                self.batch_queue[channel].append(event)
        else:
            self.pending_notifications.append(event)
        
        logger.debug(f"Queued notification {event.event_id}")
    
    async def _process_notification_queue(self):
        """Process pending notifications"""
        
        try:
            while self._is_running:
                if self.pending_notifications:
                    # Process notifications
                    current_batch = self.pending_notifications[:10]  # Process 10 at a time
                    self.pending_notifications = self.pending_notifications[10:]
                    
                    # Send notifications concurrently
                    tasks = []
                    for event in current_batch:
                        task = asyncio.create_task(self._deliver_notification(event))
                        tasks.append(task)
                    
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Notification queue processing failed: {str(e)}")
    
    async def _process_batch_notifications(self):
        """Process batched notifications"""
        
        try:
            while self._is_running:
                for channel, events in self.batch_queue.items():
                    if events and len(events) >= 5:  # Batch when 5+ notifications
                        # Process batch
                        batch = events[:20]  # Max 20 per batch
                        self.batch_queue[channel] = events[20:]
                        
                        await self._deliver_batch_notifications(channel, batch)
                
                await asyncio.sleep(self.config.batch_delay_seconds)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Batch notification processing failed: {str(e)}")
    
    async def _deliver_notification(self, event: NotificationEvent):
        """Deliver a single notification across all channels"""
        
        try:
            delivery_results = {}
            
            for channel in event.channels:
                try:
                    if channel == NotificationChannel.EMAIL and self.config.email_enabled:
                        result = await self._send_email(event)
                    elif channel == NotificationChannel.SMS and self.config.sms_enabled:
                        result = await self._send_sms(event)
                    elif channel == NotificationChannel.WEBHOOK and self.config.webhook_enabled:
                        result = await self._send_webhook(event)
                    elif channel == NotificationChannel.SLACK and self.config.slack_enabled:
                        result = await self._send_slack(event)
                    elif channel == NotificationChannel.TEAMS and self.config.teams_enabled:
                        result = await self._send_teams(event)
                    elif channel == NotificationChannel.IN_APP:
                        result = await self._send_in_app(event)
                    elif channel == NotificationChannel.PUSH and self.config.push_enabled:
                        result = await self._send_push(event)
                    else:
                        result = "skipped"
                    
                    delivery_results[channel.value] = result
                    
                except Exception as e:
                    logger.error(f"Delivery failed for channel {channel.value}: {str(e)}")
                    delivery_results[channel.value] = f"failed: {str(e)}"
            
            # Update event with delivery status
            event.delivery_status = delivery_results
            event.sent_at = datetime.now(timezone.utc)
            
            # Add to history
            self.notification_history.append(event)
            
            # Keep history limited
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-500:]
            
        except Exception as e:
            logger.error(f"Notification delivery failed: {str(e)}")
    
    async def _send_email(self, event: NotificationEvent) -> str:
        """Send email notification"""
        
        try:
            if not self.config.email_username or not event.recipients:
                return "skipped"
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from_address or self.config.email_username
            msg['To'] = ", ".join(event.recipients)
            msg['Subject'] = f"[{event.severity.value.upper()}] {event.title}"
            
            # Email body
            body = f"""
Case Monitoring Alert

Case: {event.case_number}
Court: {event.court_id}
Severity: {event.severity.value.upper()}
Time: {event.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

{event.message}

---
This is an automated message from Legal AI Case Monitor.
            """.strip()
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.email_smtp_host, self.config.email_smtp_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                text = msg.as_string()
                server.sendmail(msg['From'], event.recipients, text)
            
            logger.info(f"Email sent for event {event.event_id}")
            return "delivered"
            
        except Exception as e:
            logger.error(f"Email delivery failed: {str(e)}")
            return f"failed: {str(e)}"
    
    async def _send_sms(self, event: NotificationEvent) -> str:
        """Send SMS notification"""
        
        try:
            # SMS implementation depends on provider (Twilio, AWS SNS, etc.)
            # This is a placeholder implementation
            
            if not event.recipients:
                return "skipped"
            
            sms_message = f"LEGAL ALERT [{event.severity.value.upper()}]: {event.case_number} - {event.title[:100]}"
            
            # TODO: Implement actual SMS sending based on provider
            logger.info(f"SMS would be sent: {sms_message}")
            
            return "delivered"
            
        except Exception as e:
            logger.error(f"SMS delivery failed: {str(e)}")
            return f"failed: {str(e)}"
    
    async def _send_webhook(self, event: NotificationEvent) -> str:
        """Send webhook notification"""
        
        try:
            if not event.recipients:  # Webhook URLs in recipients
                return "skipped"
            
            # Prepare webhook payload
            payload = {
                "event_id": event.event_id,
                "case_number": event.case_number,
                "court_id": event.court_id,
                "change_type": event.event_type.value if event.event_type else None,
                "severity": event.severity.value,
                "title": event.title,
                "message": event.message,
                "timestamp": event.created_at.isoformat(),
                "metadata": event.metadata
            }
            
            # Send to all webhook URLs
            async with aiohttp.ClientSession() as session:
                for webhook_url in event.recipients:
                    try:
                        async with session.post(
                            webhook_url,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=self.config.webhook_timeout_seconds),
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status == 200:
                                logger.debug(f"Webhook delivered to {webhook_url}")
                            else:
                                logger.warning(f"Webhook failed: {response.status}")
                    
                    except Exception as e:
                        logger.error(f"Webhook delivery failed to {webhook_url}: {str(e)}")
            
            return "delivered"
            
        except Exception as e:
            logger.error(f"Webhook delivery failed: {str(e)}")
            return f"failed: {str(e)}"
    
    async def _send_slack(self, event: NotificationEvent) -> str:
        """Send Slack notification"""
        
        try:
            # Slack implementation using Bot API
            # This is a placeholder implementation
            
            slack_message = {
                "channel": self.config.slack_default_channel,
                "text": f"🚨 *{event.title}*",
                "attachments": [{
                    "color": self._get_severity_color(event.severity),
                    "fields": [
                        {"title": "Case", "value": event.case_number, "short": True},
                        {"title": "Court", "value": event.court_id, "short": True},
                        {"title": "Severity", "value": event.severity.value.upper(), "short": True},
                        {"title": "Time", "value": event.created_at.strftime('%Y-%m-%d %H:%M UTC'), "short": True}
                    ],
                    "text": event.message
                }]
            }
            
            # TODO: Implement actual Slack API call
            logger.info(f"Slack message would be sent: {slack_message}")
            
            return "delivered"
            
        except Exception as e:
            logger.error(f"Slack delivery failed: {str(e)}")
            return f"failed: {str(e)}"
    
    async def _send_teams(self, event: NotificationEvent) -> str:
        """Send Microsoft Teams notification"""
        
        try:
            if not self.config.teams_webhook_url:
                return "skipped"
            
            # Teams webhook payload
            teams_payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_severity_color(event.severity),
                "summary": event.title,
                "sections": [{
                    "activityTitle": f"🚨 {event.title}",
                    "activitySubtitle": f"Case {event.case_number} in {event.court_id}",
                    "facts": [
                        {"name": "Severity", "value": event.severity.value.upper()},
                        {"name": "Time", "value": event.created_at.strftime('%Y-%m-%d %H:%M UTC')},
                        {"name": "Details", "value": event.message}
                    ]
                }]
            }
            
            # Send to Teams
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.teams_webhook_url,
                    json=teams_payload,
                    timeout=aiohttp.ClientTimeout(total=self.config.webhook_timeout_seconds)
                ) as response:
                    if response.status == 200:
                        return "delivered"
                    else:
                        return f"failed: HTTP {response.status}"
                        
        except Exception as e:
            logger.error(f"Teams delivery failed: {str(e)}")
            return f"failed: {str(e)}"
    
    async def _send_in_app(self, event: NotificationEvent) -> str:
        """Send in-app notification"""
        
        try:
            # Store in-app notification for users
            from ..shared.utils.cache_manager import cache_manager
            
            for user_id in event.user_ids:
                notification_data = {
                    "event_id": event.event_id,
                    "title": event.title,
                    "message": event.message,
                    "severity": event.severity.value,
                    "case_number": event.case_number,
                    "court_id": event.court_id,
                    "created_at": event.created_at.isoformat(),
                    "read": False
                }
                
                # Store notification for user
                await cache_manager.set(
                    f"user_notification:{user_id}:{event.event_id}",
                    notification_data,
                    ttl=86400 * 30  # Keep for 30 days
                )
            
            return "delivered"
            
        except Exception as e:
            logger.error(f"In-app delivery failed: {str(e)}")
            return f"failed: {str(e)}"
    
    async def _send_push(self, event: NotificationEvent) -> str:
        """Send push notification"""
        
        try:
            # Push notification implementation (Firebase, APNs, etc.)
            # This is a placeholder implementation
            
            push_payload = {
                "title": event.title,
                "body": event.message[:100],
                "data": {
                    "case_number": event.case_number,
                    "court_id": event.court_id,
                    "severity": event.severity.value
                }
            }
            
            # TODO: Implement actual push notification sending
            logger.info(f"Push notification would be sent: {push_payload}")
            
            return "delivered"
            
        except Exception as e:
            logger.error(f"Push delivery failed: {str(e)}")
            return f"failed: {str(e)}"
    
    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get color code for severity level"""
        color_map = {
            AlertSeverity.LOW: "#36a64f",      # Green
            AlertSeverity.MEDIUM: "#ff9500",   # Orange  
            AlertSeverity.HIGH: "#ff6b35",     # Red-Orange
            AlertSeverity.CRITICAL: "#e01e5a", # Red
            AlertSeverity.URGENT: "#8b0000"    # Dark Red
        }
        return color_map.get(severity, "#36a64f")
    
    async def _generate_message_content(
        self,
        change_detection: ChangeDetection,
        rule: MonitoringRule
    ) -> Tuple[str, str]:
        """Generate notification title and message content"""
        
        try:
            # Title
            change_type_name = change_detection.change_type.value.replace('_', ' ').title()
            title = f"{change_type_name} in {change_detection.case_number}"
            
            # Message
            message_parts = [
                f"A {change_type_name.lower()} has been detected in case {change_detection.case_number}.",
                f"Court: {change_detection.court_id}",
                f"Time: {change_detection.detected_at.strftime('%Y-%m-%d %H:%M UTC')}",
                ""
            ]
            
            if change_detection.description:
                message_parts.append(f"Details: {change_detection.description}")
            
            if change_detection.affected_entry_number:
                message_parts.append(f"Docket Entry: {change_detection.affected_entry_number}")
            
            message = "\n".join(message_parts)
            
            return title, message
            
        except Exception as e:
            logger.error(f"Message generation failed: {str(e)}")
            return "Case Update", change_detection.description or "A change has been detected."
    
    async def _check_rate_limit(self, event: NotificationEvent) -> bool:
        """Check if notification is within rate limits"""
        
        try:
            current_time = datetime.now(timezone.utc)
            hour_key = current_time.strftime("%Y-%m-%d-%H")
            
            if hour_key not in self.rate_limiting:
                self.rate_limiting[hour_key] = []
            
            # Clean old entries
            cutoff_time = current_time - timedelta(hours=1)
            self.rate_limiting[hour_key] = [
                time for time in self.rate_limiting[hour_key]
                if time > cutoff_time
            ]
            
            # Check limit
            if len(self.rate_limiting[hour_key]) >= self.config.max_notification_rate_per_hour:
                return False
            
            # Add current notification
            self.rate_limiting[hour_key].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return True  # Allow if check fails
    
    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        
        templates = {}
        
        # Basic email template
        templates["email_basic"] = NotificationTemplate(
            template_id="email_basic",
            name="Basic Email Template",
            channel=NotificationChannel.EMAIL,
            subject_template="[{severity}] Case Update: {case_number}",
            body_template="""
Case Monitoring Alert

Case: {case_number}
Court: {court_id}
Change Type: {change_type}
Severity: {severity}
Time: {timestamp}

{description}

{additional_details}
            """.strip(),
            variables=["severity", "case_number", "court_id", "change_type", "timestamp", "description", "additional_details"]
        )
        
        return templates
    
    async def get_notification_history(
        self, 
        limit: int = 100,
        case_number: str = None,
        severity: AlertSeverity = None
    ) -> List[NotificationEvent]:
        """Get notification history with optional filtering"""
        
        filtered_history = self.notification_history
        
        if case_number:
            filtered_history = [
                event for event in filtered_history
                if event.case_number == case_number
            ]
        
        if severity:
            filtered_history = [
                event for event in filtered_history
                if event.severity == severity
            ]
        
        # Sort by timestamp (newest first)
        filtered_history.sort(key=lambda x: x.created_at, reverse=True)
        
        return filtered_history[:limit]
    
    # Placeholder methods for data access
    async def _get_monitoring_rules(self, rule_ids: List[str]) -> List[MonitoringRule]:
        """Get monitoring rules by IDs"""
        # TODO: Implement based on your storage
        from .models import get_default_rules
        default_rules = get_default_rules()
        return [rule for rule in default_rules if rule.rule_id in rule_ids]
    
    async def _get_notification_recipients(
        self, 
        monitor_id: str, 
        rule: MonitoringRule
    ) -> Dict[str, List]:
        """Get notification recipients for a monitor and rule"""
        # TODO: Implement based on your user management system
        return {
            "external": ["admin@legalai.com"],  # Email addresses, phone numbers, webhook URLs
            "internal": [1, 2]  # User IDs for in-app notifications
        }


# Global notification manager instance
notification_manager = NotificationManager()