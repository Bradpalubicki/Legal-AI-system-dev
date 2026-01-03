"""
Alert dispatcher for real-time delivery of critical courtroom alerts across multiple channels.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

from .alert_system import Alert, AlertChannel, AlertSeverity, AlertStatus


@dataclass
class DeliveryConfig:
    """Configuration for alert delivery channels."""
    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    
    # SMS settings (Twilio)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # Push notification settings
    firebase_server_key: str = ""
    
    # Slack settings
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    
    # Teams settings
    teams_webhook_url: str = ""
    
    # Phone call settings
    voice_api_key: str = ""
    voice_api_url: str = ""


class AlertDispatcher:
    """Handles real-time delivery of alerts across multiple channels."""
    
    def __init__(self, config: DeliveryConfig):
        self.config = config
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.active_deliveries: Dict[str, asyncio.Task] = {}
        self.delivery_stats: Dict[str, Dict[str, int]] = {}
        self.failed_deliveries: List[Dict[str, Any]] = []
        
        # Initialize delivery stats
        for channel in AlertChannel:
            self.delivery_stats[channel.value] = {
                "sent": 0,
                "delivered": 0,
                "failed": 0
            }

    async def start_dispatcher(self):
        """Start the alert dispatcher service."""
        try:
            print("Starting alert dispatcher...")
            
            # Start delivery worker
            asyncio.create_task(self._delivery_worker())
            
            print("Alert dispatcher started successfully")
            
        except Exception as e:
            print(f"Error starting alert dispatcher: {e}")
            raise

    async def dispatch_alert(self, alert: Alert) -> Dict[str, bool]:
        """Dispatch alert through all configured channels."""
        try:
            delivery_results = {}
            
            # Create delivery tasks for each channel
            delivery_tasks = []
            for channel in alert.channels:
                task = asyncio.create_task(
                    self._deliver_alert(alert, channel)
                )
                delivery_tasks.append((channel, task))
            
            # Wait for all deliveries
            for channel, task in delivery_tasks:
                try:
                    success = await task
                    delivery_results[channel.value] = success
                    
                    if success:
                        self.delivery_stats[channel.value]["delivered"] += 1
                    else:
                        self.delivery_stats[channel.value]["failed"] += 1
                        
                except Exception as e:
                    print(f"Error delivering alert via {channel.value}: {e}")
                    delivery_results[channel.value] = False
                    self.delivery_stats[channel.value]["failed"] += 1
            
            return delivery_results
            
        except Exception as e:
            print(f"Error dispatching alert: {e}")
            return {}

    async def _delivery_worker(self):
        """Background worker for processing delivery queue."""
        while True:
            try:
                # Get next alert from queue
                alert, channel = await self.delivery_queue.get()
                
                # Process delivery
                success = await self._deliver_alert(alert, channel)
                
                if success:
                    self.delivery_stats[channel.value]["sent"] += 1
                else:
                    self.delivery_stats[channel.value]["failed"] += 1
                    self._log_failed_delivery(alert, channel)
                
                # Mark task as done
                self.delivery_queue.task_done()
                
            except Exception as e:
                print(f"Error in delivery worker: {e}")
                await asyncio.sleep(1)

    async def _deliver_alert(self, alert: Alert, channel: AlertChannel) -> bool:
        """Deliver alert via specific channel."""
        try:
            if channel == AlertChannel.EMAIL:
                return await self._send_email(alert)
            elif channel == AlertChannel.SMS:
                return await self._send_sms(alert)
            elif channel == AlertChannel.PUSH_NOTIFICATION:
                return await self._send_push_notification(alert)
            elif channel == AlertChannel.SLACK:
                return await self._send_slack_message(alert)
            elif channel == AlertChannel.TEAMS:
                return await self._send_teams_message(alert)
            elif channel == AlertChannel.PHONE_CALL:
                return await self._make_phone_call(alert)
            elif channel == AlertChannel.WEBSOCKET:
                return await self._send_websocket_message(alert)
            elif channel == AlertChannel.IN_APP:
                return await self._send_in_app_notification(alert)
            else:
                print(f"Unsupported channel: {channel.value}")
                return False
                
        except Exception as e:
            print(f"Error delivering alert via {channel.value}: {e}")
            return False

    async def _send_email(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            if not self.config.email_username or not self.config.email_password:
                print("Email configuration missing")
                return False
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            message["From"] = self.config.email_username
            message["To"] = ", ".join(alert.recipients)
            
            # Create email body
            text_body = self._create_email_text_body(alert)
            html_body = self._create_email_html_body(alert)
            
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.email_username, self.config.email_password)
                server.sendmail(
                    self.config.email_username,
                    alert.recipients,
                    message.as_string()
                )
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    async def _send_sms(self, alert: Alert) -> bool:
        """Send alert via SMS using Twilio."""
        try:
            if not self.config.twilio_account_sid or not self.config.twilio_auth_token:
                print("Twilio configuration missing")
                return False
            
            # Create SMS message
            message_body = f"[{alert.severity.value.upper()}] {alert.title}\n\n{alert.message}"
            
            # Truncate if too long
            if len(message_body) > 1600:
                message_body = message_body[:1597] + "..."
            
            # Send SMS via Twilio API
            auth = aiohttp.BasicAuth(
                self.config.twilio_account_sid,
                self.config.twilio_auth_token
            )
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.twilio_account_sid}/Messages.json"
            
            async with aiohttp.ClientSession(auth=auth) as session:
                for recipient in alert.recipients:
                    data = {
                        'From': self.config.twilio_phone_number,
                        'To': recipient,  # Should be phone number
                        'Body': message_body
                    }
                    
                    async with session.post(url, data=data) as response:
                        if response.status != 201:
                            print(f"Failed to send SMS to {recipient}: {response.status}")
                            return False
            
            return True
            
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False

    async def _send_push_notification(self, alert: Alert) -> bool:
        """Send push notification via Firebase."""
        try:
            if not self.config.firebase_server_key:
                print("Firebase configuration missing")
                return False
            
            headers = {
                'Authorization': f'key={self.config.firebase_server_key}',
                'Content-Type': 'application/json'
            }
            
            # Create notification payload
            notification_data = {
                "notification": {
                    "title": alert.title,
                    "body": alert.message,
                    "icon": "legal-alert-icon",
                    "click_action": f"/case/{alert.case_id}/alerts/{alert.alert_id}"
                },
                "data": {
                    "alert_id": alert.alert_id,
                    "case_id": alert.case_id,
                    "severity": alert.severity.value,
                    "timestamp": alert.timestamp.isoformat()
                },
                "registration_ids": alert.recipients  # Should be FCM tokens
            }
            
            url = "https://fcm.googleapis.com/fcm/send"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=notification_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("success", 0) > 0
                    else:
                        print(f"Failed to send push notification: {response.status}")
                        return False
            
        except Exception as e:
            print(f"Error sending push notification: {e}")
            return False

    async def _send_slack_message(self, alert: Alert) -> bool:
        """Send alert to Slack channel."""
        try:
            if not self.config.slack_webhook_url:
                print("Slack webhook URL not configured")
                return False
            
            # Create Slack message
            color = self._get_slack_color(alert.severity)
            
            slack_message = {
                "text": f"🚨 Legal Alert: {alert.title}",
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.title(),
                                "short": True
                            },
                            {
                                "title": "Case",
                                "value": alert.case_id,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            },
                            {
                                "title": "Speaker",
                                "value": alert.source_segment.speaker if alert.source_segment else "Unknown",
                                "short": True
                            }
                        ],
                        "footer": "Legal AI Alert System",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            if alert.requires_response:
                slack_message["attachments"][0]["actions"] = [
                    {
                        "type": "button",
                        "text": "Acknowledge",
                        "style": "primary",
                        "value": f"ack_{alert.alert_id}"
                    },
                    {
                        "type": "button",
                        "text": "Resolve",
                        "style": "danger",
                        "value": f"resolve_{alert.alert_id}"
                    }
                ]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.slack_webhook_url, json=slack_message) as response:
                    return response.status == 200
            
        except Exception as e:
            print(f"Error sending Slack message: {e}")
            return False

    async def _send_teams_message(self, alert: Alert) -> bool:
        """Send alert to Microsoft Teams."""
        try:
            if not self.config.teams_webhook_url:
                print("Teams webhook URL not configured")
                return False
            
            # Create Teams message card
            color = self._get_teams_color(alert.severity)
            
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "summary": alert.title,
                "sections": [
                    {
                        "activityTitle": f"🚨 Legal Alert: {alert.title}",
                        "activitySubtitle": f"Severity: {alert.severity.value.title()}",
                        "activityImage": "https://legal-ai-system.com/icons/alert.png",
                        "text": alert.message,
                        "facts": [
                            {
                                "name": "Case ID",
                                "value": alert.case_id
                            },
                            {
                                "name": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            },
                            {
                                "name": "Speaker",
                                "value": alert.source_segment.speaker if alert.source_segment else "Unknown"
                            }
                        ]
                    }
                ]
            }
            
            if alert.requires_response:
                teams_message["potentialAction"] = [
                    {
                        "@type": "ActionCard",
                        "name": "Quick Actions",
                        "inputs": [
                            {
                                "@type": "TextInput",
                                "id": "response",
                                "title": "Response",
                                "isMultiline": True
                            }
                        ],
                        "actions": [
                            {
                                "@type": "HttpPOST",
                                "name": "Acknowledge",
                                "target": f"https://legal-ai-system.com/api/alerts/{alert.alert_id}/acknowledge"
                            }
                        ]
                    }
                ]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.teams_webhook_url, json=teams_message) as response:
                    return response.status == 200
            
        except Exception as e:
            print(f"Error sending Teams message: {e}")
            return False

    async def _make_phone_call(self, alert: Alert) -> bool:
        """Make phone call for critical alerts."""
        try:
            if not self.config.voice_api_key or not self.config.voice_api_url:
                print("Voice API configuration missing")
                return False
            
            # Create voice message
            voice_message = f"""
            This is an urgent legal alert from the AI system.
            
            Alert: {alert.title}
            
            Severity: {alert.severity.value}
            
            Message: {alert.message}
            
            Case ID: {alert.case_id}
            
            Time: {alert.timestamp.strftime("%H:%M on %B %d")}
            
            Please acknowledge this alert immediately.
            
            Press 1 to acknowledge, or press 2 to escalate.
            """
            
            headers = {
                'Authorization': f'Bearer {self.config.voice_api_key}',
                'Content-Type': 'application/json'
            }
            
            for recipient in alert.recipients:
                call_data = {
                    'to': recipient,  # Should be phone number
                    'message': voice_message,
                    'voice': 'female',
                    'callback_url': f"https://legal-ai-system.com/api/alerts/{alert.alert_id}/voice-response"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.config.voice_api_url}/calls",
                        headers=headers,
                        json=call_data
                    ) as response:
                        if response.status != 200:
                            print(f"Failed to make call to {recipient}: {response.status}")
                            return False
            
            return True
            
        except Exception as e:
            print(f"Error making phone call: {e}")
            return False

    async def _send_websocket_message(self, alert: Alert) -> bool:
        """Send alert via WebSocket to connected clients."""
        try:
            # This would integrate with the WebSocket manager
            websocket_message = {
                "type": "alert",
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "case_id": alert.case_id,
                "requires_response": alert.requires_response,
                "response_deadline": alert.response_deadline.isoformat() if alert.response_deadline else None
            }
            
            # Send to WebSocket manager (implementation would depend on WebSocket system)
            print(f"WebSocket Alert: {json.dumps(websocket_message, indent=2)}")
            
            return True
            
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")
            return False

    async def _send_in_app_notification(self, alert: Alert) -> bool:
        """Send in-app notification."""
        try:
            # Store notification in database for in-app display
            notification_data = {
                "alert_id": alert.alert_id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp.isoformat(),
                "case_id": alert.case_id,
                "read": False,
                "recipients": alert.recipients
            }
            
            print(f"In-App Notification: {json.dumps(notification_data, indent=2)}")
            
            return True
            
        except Exception as e:
            print(f"Error sending in-app notification: {e}")
            return False

    def _create_email_text_body(self, alert: Alert) -> str:
        """Create text version of email body."""
        return f"""
LEGAL ALERT - {alert.severity.value.upper()}

{alert.title}

{alert.message}

Details:
- Case ID: {alert.case_id}
- Alert Type: {alert.alert_type.value}
- Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- Speaker: {alert.source_segment.speaker if alert.source_segment else 'Unknown'}

{f"RESPONSE REQUIRED BY: {alert.response_deadline.strftime('%Y-%m-%d %H:%M:%S')}" if alert.requires_response else ""}

This alert was generated by the Legal AI System.
"""

    def _create_email_html_body(self, alert: Alert) -> str:
        """Create HTML version of email body."""
        severity_color = {
            AlertSeverity.CRITICAL: "#dc3545",
            AlertSeverity.HIGH: "#fd7e14", 
            AlertSeverity.MEDIUM: "#ffc107",
            AlertSeverity.LOW: "#17a2b8",
            AlertSeverity.INFORMATIONAL: "#6c757d"
        }.get(alert.severity, "#6c757d")
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background-color: {severity_color}; color: white; padding: 15px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0;">🚨 LEGAL ALERT - {alert.severity.value.upper()}</h2>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 5px 5px;">
                    <h3 style="color: {severity_color}; margin-top: 0;">{alert.title}</h3>
                    <p style="font-size: 16px; line-height: 1.5;">{alert.message}</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Case ID:</td>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{alert.case_id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Alert Type:</td>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{alert.alert_type.value.replace('_', ' ').title()}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Time:</td>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Speaker:</td>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{alert.source_segment.speaker if alert.source_segment else 'Unknown'}</td>
                        </tr>
                    </table>
                    
                    {f'<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;"><strong>RESPONSE REQUIRED BY: {alert.response_deadline.strftime("%Y-%m-%d %H:%M:%S")}</strong></div>' if alert.requires_response else ''}
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 14px; color: #6c757d;">
                        This alert was generated by the Legal AI System.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_slack_color(self, severity: AlertSeverity) -> str:
        """Get Slack color for severity level."""
        return {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.HIGH: "warning",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "good",
            AlertSeverity.INFORMATIONAL: "#36a64f"
        }.get(severity, "good")

    def _get_teams_color(self, severity: AlertSeverity) -> str:
        """Get Teams color for severity level."""
        return {
            AlertSeverity.CRITICAL: "FF0000",
            AlertSeverity.HIGH: "FF8C00",
            AlertSeverity.MEDIUM: "FFD700",
            AlertSeverity.LOW: "1E90FF",
            AlertSeverity.INFORMATIONAL: "808080"
        }.get(severity, "808080")

    def _log_failed_delivery(self, alert: Alert, channel: AlertChannel):
        """Log failed delivery attempt."""
        failure_record = {
            "alert_id": alert.alert_id,
            "channel": channel.value,
            "timestamp": datetime.now().isoformat(),
            "severity": alert.severity.value,
            "title": alert.title
        }
        self.failed_deliveries.append(failure_record)

    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get delivery statistics."""
        return {
            "delivery_stats": self.delivery_stats,
            "failed_deliveries": len(self.failed_deliveries),
            "active_deliveries": len(self.active_deliveries),
            "recent_failures": self.failed_deliveries[-10:]  # Last 10 failures
        }

    async def retry_failed_deliveries(self) -> int:
        """Retry recent failed deliveries."""
        retry_count = 0
        
        # Get failures from last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_failures = [
            f for f in self.failed_deliveries 
            if datetime.fromisoformat(f["timestamp"]) > cutoff_time
        ]
        
        for failure in recent_failures:
            try:
                # Would need to reconstruct alert and retry
                print(f"Retrying delivery for alert {failure['alert_id']} via {failure['channel']}")
                retry_count += 1
            except Exception as e:
                print(f"Error retrying delivery: {e}")
        
        return retry_count

    async def shutdown(self):
        """Shutdown the dispatcher gracefully."""
        try:
            print("Shutting down alert dispatcher...")
            
            # Wait for queue to be empty
            await self.delivery_queue.join()
            
            # Cancel active delivery tasks
            for task_id, task in self.active_deliveries.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            print("Alert dispatcher shut down successfully")
            
        except Exception as e:
            print(f"Error shutting down dispatcher: {e}")