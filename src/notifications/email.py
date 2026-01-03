"""
Email Notification Engine

Comprehensive email system for transactional and marketing emails
with SendGrid/AWS SES integration, templates, and tracking.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import uuid
import aiofiles
import aiosmtplib
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)

class EmailProvider(Enum):
    """Email service providers"""
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    SMTP = "smtp"
    MAILGUN = "mailgun"

class EmailType(Enum):
    """Types of emails"""
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    SYSTEM = "system"
    LEGAL = "legal"

class EmailStatus(Enum):
    """Email delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    SPAM = "spam"
    UNSUBSCRIBED = "unsubscribed"

class EmailPriority(Enum):
    """Email priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

@dataclass
class EmailAttachment:
    """Email attachment"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"

@dataclass
class EmailTemplate:
    """Email template definition"""
    template_id: str
    name: str
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    category: str = "general"
    variables: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class EmailMessage:
    """Email message"""
    message_id: str
    to_emails: List[str]
    from_email: str
    from_name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Dict[str, Any] = field(default_factory=dict)
    attachments: List[EmailAttachment] = field(default_factory=list)
    reply_to: Optional[str] = None
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    email_type: EmailType = EmailType.TRANSACTIONAL
    priority: EmailPriority = EmailPriority.NORMAL
    send_at: Optional[datetime] = None
    status: EmailStatus = EmailStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class EmailEvent:
    """Email tracking event"""
    event_id: str
    message_id: str
    event_type: str
    timestamp: datetime
    email: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    url: Optional[str] = None  # For click events
    metadata: Dict[str, Any] = field(default_factory=dict)

class EmailTemplateManager:
    """Manage email templates"""

    def __init__(self, templates_dir: str = "templates/email"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, EmailTemplate] = {}
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default email templates"""
        default_templates = {
            "welcome": EmailTemplate(
                template_id="welcome",
                name="Welcome Email",
                subject_template="Welcome to Legal AI, {{user_name}}!",
                html_template="""
                <h1>Welcome to Legal AI!</h1>
                <p>Hello {{user_name}},</p>
                <p>Thank you for joining our legal AI platform. We're excited to help you streamline your legal work.</p>
                <p>Your account is now active and ready to use.</p>
                <a href="{{dashboard_url}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Get Started</a>
                <p>Best regards,<br>The Legal AI Team</p>
                """,
                variables=["user_name", "dashboard_url"]
            ),
            "password_reset": EmailTemplate(
                template_id="password_reset",
                name="Password Reset",
                subject_template="Reset your password",
                html_template="""
                <h1>Password Reset Request</h1>
                <p>Hello {{user_name}},</p>
                <p>You requested a password reset for your Legal AI account.</p>
                <p>Click the link below to reset your password:</p>
                <a href="{{reset_url}}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't request this reset, please ignore this email.</p>
                """,
                variables=["user_name", "reset_url"]
            ),
            "document_upload": EmailTemplate(
                template_id="document_upload",
                name="Document Upload Confirmation",
                subject_template="Document uploaded successfully",
                html_template="""
                <h1>Document Upload Confirmation</h1>
                <p>Hello {{user_name}},</p>
                <p>Your document "{{document_name}}" has been uploaded successfully.</p>
                <p><strong>Upload Details:</strong></p>
                <ul>
                    <li>File: {{document_name}}</li>
                    <li>Size: {{file_size}}</li>
                    <li>Type: {{document_type}}</li>
                    <li>Uploaded: {{upload_time}}</li>
                </ul>
                <p>Analysis will begin shortly and you'll receive another notification when complete.</p>
                <a href="{{document_url}}">View Document</a>
                """,
                variables=["user_name", "document_name", "file_size", "document_type", "upload_time", "document_url"]
            ),
            "analysis_complete": EmailTemplate(
                template_id="analysis_complete",
                name="Document Analysis Complete",
                subject_template="Analysis complete for {{document_name}}",
                html_template="""
                <h1>Document Analysis Complete</h1>
                <p>Hello {{user_name}},</p>
                <p>The analysis for "{{document_name}}" is now complete.</p>
                <p><strong>Analysis Results:</strong></p>
                <ul>
                    <li>Key Issues Found: {{key_issues_count}}</li>
                    <li>Risk Score: {{risk_score}}/10</li>
                    <li>Recommendations: {{recommendations_count}}</li>
                </ul>
                <a href="{{analysis_url}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Analysis</a>
                """,
                variables=["user_name", "document_name", "key_issues_count", "risk_score", "recommendations_count", "analysis_url"]
            ),
            "deadline_reminder": EmailTemplate(
                template_id="deadline_reminder",
                name="Deadline Reminder",
                subject_template="Reminder: {{case_name}} deadline approaching",
                html_template="""
                <h1>Deadline Reminder</h1>
                <p>Hello {{user_name}},</p>
                <p>This is a reminder that you have an upcoming deadline:</p>
                <p><strong>Case:</strong> {{case_name}}</p>
                <p><strong>Deadline:</strong> {{deadline_date}} ({{days_remaining}} days remaining)</p>
                <p><strong>Task:</strong> {{task_description}}</p>
                <a href="{{case_url}}">View Case Details</a>
                """,
                variables=["user_name", "case_name", "deadline_date", "days_remaining", "task_description", "case_url"]
            ),
            "payment_receipt": EmailTemplate(
                template_id="payment_receipt",
                name="Payment Receipt",
                subject_template="Payment receipt - {{invoice_number}}",
                html_template="""
                <h1>Payment Receipt</h1>
                <p>Hello {{user_name}},</p>
                <p>Thank you for your payment. Here are your receipt details:</p>
                <p><strong>Invoice:</strong> {{invoice_number}}</p>
                <p><strong>Amount:</strong> ${{amount}}</p>
                <p><strong>Payment Date:</strong> {{payment_date}}</p>
                <p><strong>Payment Method:</strong> {{payment_method}}</p>
                <a href="{{receipt_url}}">Download PDF Receipt</a>
                """,
                variables=["user_name", "invoice_number", "amount", "payment_date", "payment_method", "receipt_url"]
            ),
            "feature_announcement": EmailTemplate(
                template_id="feature_announcement",
                name="Feature Announcement",
                subject_template="New Feature: {{feature_name}}",
                html_template="""
                <h1>Exciting New Feature!</h1>
                <p>Hello {{user_name}},</p>
                <p>We're excited to announce a new feature: <strong>{{feature_name}}</strong></p>
                <p>{{feature_description}}</p>
                <p><strong>Key Benefits:</strong></p>
                <ul>
                    {{#benefits}}
                    <li>{{.}}</li>
                    {{/benefits}}
                </ul>
                <a href="{{feature_url}}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Try It Now</a>
                """,
                variables=["user_name", "feature_name", "feature_description", "benefits", "feature_url"]
            )
        }

        for template in default_templates.values():
            self.templates[template.template_id] = template

    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def render_template(self, template_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Render template with data"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Render subject
        subject_template = Template(template.subject_template)
        subject = subject_template.render(**data)

        # Render HTML content
        html_template = Template(template.html_template)
        html_content = html_template.render(**data)

        # Render text content if available
        text_content = None
        if template.text_template:
            text_template = Template(template.text_template)
            text_content = text_template.render(**data)

        return {
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content
        }

class SendGridProvider:
    """SendGrid email provider"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sendgrid.com/v3"

    async def send_email(self, message: EmailMessage) -> bool:
        """Send email via SendGrid"""
        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Build SendGrid message
            sg_message = {
                "personalizations": [{
                    "to": [{"email": email} for email in message.to_emails],
                    "subject": message.subject
                }],
                "from": {
                    "email": message.from_email,
                    "name": message.from_name
                },
                "content": [
                    {"type": "text/html", "value": message.html_content}
                ]
            }

            if message.text_content:
                sg_message["content"].append({
                    "type": "text/plain",
                    "value": message.text_content
                })

            if message.reply_to:
                sg_message["reply_to"] = {"email": message.reply_to}

            if message.tags:
                sg_message["categories"] = message.tags

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/mail/send",
                    headers=headers,
                    json=sg_message
                ) as response:
                    return response.status == 202

        except Exception as e:
            logger.error(f"SendGrid send error: {str(e)}")
            return False

class SMTPProvider:
    """SMTP email provider"""

    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send_email(self, message: EmailMessage) -> bool:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{message.from_name} <{message.from_email}>"
            msg["To"] = ", ".join(message.to_emails)

            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            # Add text content
            if message.text_content:
                text_part = MIMEText(message.text_content, "plain")
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(message.html_content, "html")
            msg.attach(html_part)

            # Add attachments
            for attachment in message.attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.content)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment.filename}"
                )
                msg.attach(part)

            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls
            )

            return True

        except Exception as e:
            logger.error(f"SMTP send error: {str(e)}")
            return False

class EmailNotificationEngine:
    """
    Comprehensive email notification system
    """

    def __init__(self, provider: EmailProvider = EmailProvider.SMTP):
        self.provider_type = provider
        self.provider = None
        self.template_manager = EmailTemplateManager()
        self.message_queue: List[EmailMessage] = []
        self.sent_messages: Dict[str, EmailMessage] = {}
        self.events: Dict[str, List[EmailEvent]] = {}
        self.unsubscribed_emails: set = set()

        # Email settings
        self.default_from_email = "noreply@legalai.com"
        self.default_from_name = "Legal AI"

    def configure_sendgrid(self, api_key: str):
        """Configure SendGrid provider"""
        self.provider = SendGridProvider(api_key)

    def configure_smtp(self, smtp_server: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        """Configure SMTP provider"""
        self.provider = SMTPProvider(smtp_server, smtp_port, username, password, use_tls)

    async def send_welcome_email(self, user_email: str, user_name: str, dashboard_url: str) -> str:
        """Send welcome email"""
        return await self.send_template_email(
            template_id="welcome",
            to_emails=[user_email],
            template_data={
                "user_name": user_name,
                "dashboard_url": dashboard_url
            },
            tags=["welcome", "onboarding"]
        )

    async def send_password_reset_email(self, user_email: str, user_name: str, reset_url: str) -> str:
        """Send password reset email"""
        return await self.send_template_email(
            template_id="password_reset",
            to_emails=[user_email],
            template_data={
                "user_name": user_name,
                "reset_url": reset_url
            },
            priority=EmailPriority.HIGH,
            tags=["password_reset", "security"]
        )

    async def send_document_upload_confirmation(self, user_email: str, user_name: str,
                                               document_name: str, file_size: str,
                                               document_type: str, document_url: str) -> str:
        """Send document upload confirmation"""
        return await self.send_template_email(
            template_id="document_upload",
            to_emails=[user_email],
            template_data={
                "user_name": user_name,
                "document_name": document_name,
                "file_size": file_size,
                "document_type": document_type,
                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "document_url": document_url
            },
            tags=["document", "upload", "confirmation"]
        )

    async def send_analysis_complete_email(self, user_email: str, user_name: str,
                                         document_name: str, key_issues_count: int,
                                         risk_score: float, recommendations_count: int,
                                         analysis_url: str) -> str:
        """Send analysis completion notification"""
        return await self.send_template_email(
            template_id="analysis_complete",
            to_emails=[user_email],
            template_data={
                "user_name": user_name,
                "document_name": document_name,
                "key_issues_count": key_issues_count,
                "risk_score": risk_score,
                "recommendations_count": recommendations_count,
                "analysis_url": analysis_url
            },
            priority=EmailPriority.HIGH,
            tags=["analysis", "complete", "results"]
        )

    async def send_deadline_reminder(self, user_email: str, user_name: str,
                                   case_name: str, deadline_date: str,
                                   days_remaining: int, task_description: str,
                                   case_url: str) -> str:
        """Send deadline reminder"""
        priority = EmailPriority.URGENT if days_remaining <= 1 else EmailPriority.HIGH

        return await self.send_template_email(
            template_id="deadline_reminder",
            to_emails=[user_email],
            template_data={
                "user_name": user_name,
                "case_name": case_name,
                "deadline_date": deadline_date,
                "days_remaining": days_remaining,
                "task_description": task_description,
                "case_url": case_url
            },
            priority=priority,
            tags=["deadline", "reminder", "urgent" if days_remaining <= 1 else "normal"]
        )

    async def send_payment_receipt(self, user_email: str, user_name: str,
                                 invoice_number: str, amount: float,
                                 payment_method: str, receipt_url: str) -> str:
        """Send payment receipt"""
        return await self.send_template_email(
            template_id="payment_receipt",
            to_emails=[user_email],
            template_data={
                "user_name": user_name,
                "invoice_number": invoice_number,
                "amount": f"{amount:.2f}",
                "payment_date": datetime.now().strftime("%Y-%m-%d"),
                "payment_method": payment_method,
                "receipt_url": receipt_url
            },
            tags=["payment", "receipt", "billing"]
        )

    async def send_feature_announcement(self, user_emails: List[str], user_name: str,
                                      feature_name: str, feature_description: str,
                                      benefits: List[str], feature_url: str) -> List[str]:
        """Send feature announcement (marketing email)"""
        message_ids = []

        for email in user_emails:
            if email not in self.unsubscribed_emails:
                message_id = await self.send_template_email(
                    template_id="feature_announcement",
                    to_emails=[email],
                    template_data={
                        "user_name": user_name,
                        "feature_name": feature_name,
                        "feature_description": feature_description,
                        "benefits": benefits,
                        "feature_url": feature_url
                    },
                    email_type=EmailType.MARKETING,
                    tags=["feature", "announcement", "marketing"]
                )
                message_ids.append(message_id)

        return message_ids

    async def send_template_email(self, template_id: str, to_emails: List[str],
                                template_data: Dict[str, Any],
                                from_email: Optional[str] = None,
                                from_name: Optional[str] = None,
                                reply_to: Optional[str] = None,
                                attachments: List[EmailAttachment] = None,
                                priority: EmailPriority = EmailPriority.NORMAL,
                                email_type: EmailType = EmailType.TRANSACTIONAL,
                                tags: List[str] = None,
                                send_at: Optional[datetime] = None) -> str:
        """Send templated email"""
        try:
            # Render template
            rendered = self.template_manager.render_template(template_id, template_data)

            # Create message
            message = EmailMessage(
                message_id=f"msg_{uuid.uuid4().hex[:12]}",
                to_emails=to_emails,
                from_email=from_email or self.default_from_email,
                from_name=from_name or self.default_from_name,
                subject=rendered["subject"],
                html_content=rendered["html_content"],
                text_content=rendered["text_content"],
                template_id=template_id,
                template_data=template_data,
                reply_to=reply_to,
                attachments=attachments or [],
                priority=priority,
                email_type=email_type,
                tags=tags or [],
                send_at=send_at
            )

            # Queue or send immediately
            if send_at and send_at > datetime.now():
                self.message_queue.append(message)
                message.status = EmailStatus.QUEUED
            else:
                success = await self._send_message(message)
                if success:
                    message.status = EmailStatus.SENT
                    self.sent_messages[message.message_id] = message
                else:
                    message.status = EmailStatus.FAILED

            logger.info(f"Email {message.message_id} status: {message.status.value}")
            return message.message_id

        except Exception as e:
            logger.error(f"Error sending template email: {str(e)}")
            raise

    async def send_custom_email(self, to_emails: List[str], subject: str,
                              html_content: str, text_content: Optional[str] = None,
                              from_email: Optional[str] = None,
                              from_name: Optional[str] = None,
                              attachments: List[EmailAttachment] = None,
                              priority: EmailPriority = EmailPriority.NORMAL) -> str:
        """Send custom email"""
        message = EmailMessage(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            to_emails=to_emails,
            from_email=from_email or self.default_from_email,
            from_name=from_name or self.default_from_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=attachments or [],
            priority=priority
        )

        success = await self._send_message(message)
        if success:
            message.status = EmailStatus.SENT
            self.sent_messages[message.message_id] = message
        else:
            message.status = EmailStatus.FAILED

        return message.message_id

    async def _send_message(self, message: EmailMessage) -> bool:
        """Send message using configured provider"""
        if not self.provider:
            logger.error("No email provider configured")
            return False

        try:
            # Filter out unsubscribed emails
            filtered_emails = [email for email in message.to_emails if email not in self.unsubscribed_emails]
            message.to_emails = filtered_emails

            if not filtered_emails:
                logger.info(f"All recipients unsubscribed for message {message.message_id}")
                return True

            success = await self.provider.send_email(message)
            return success

        except Exception as e:
            logger.error(f"Error sending message {message.message_id}: {str(e)}")
            return False

    async def process_scheduled_emails(self):
        """Process scheduled emails"""
        current_time = datetime.now()
        messages_to_send = []

        # Find messages ready to send
        for message in self.message_queue[:]:
            if message.send_at and message.send_at <= current_time:
                messages_to_send.append(message)
                self.message_queue.remove(message)

        # Send messages
        for message in messages_to_send:
            success = await self._send_message(message)
            if success:
                message.status = EmailStatus.SENT
                self.sent_messages[message.message_id] = message
            else:
                message.status = EmailStatus.FAILED

        return len(messages_to_send)

    def track_event(self, message_id: str, event_type: str, email: str,
                   user_agent: Optional[str] = None, ip_address: Optional[str] = None,
                   url: Optional[str] = None, metadata: Dict[str, Any] = None):
        """Track email event"""
        event = EmailEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            message_id=message_id,
            event_type=event_type,
            timestamp=datetime.now(),
            email=email,
            user_agent=user_agent,
            ip_address=ip_address,
            url=url,
            metadata=metadata or {}
        )

        if message_id not in self.events:
            self.events[message_id] = []
        self.events[message_id].append(event)

        # Update message status if needed
        if message_id in self.sent_messages:
            message = self.sent_messages[message_id]
            if event_type == "delivered":
                message.status = EmailStatus.DELIVERED
            elif event_type == "opened":
                message.status = EmailStatus.OPENED
            elif event_type == "clicked":
                message.status = EmailStatus.CLICKED
            elif event_type == "bounced":
                message.status = EmailStatus.BOUNCED
            elif event_type == "spam":
                message.status = EmailStatus.SPAM

    def unsubscribe_email(self, email: str):
        """Unsubscribe email address"""
        self.unsubscribed_emails.add(email)
        logger.info(f"Email {email} unsubscribed")

    def get_message_status(self, message_id: str) -> Optional[EmailStatus]:
        """Get message delivery status"""
        if message_id in self.sent_messages:
            return self.sent_messages[message_id].status

        # Check queue
        for message in self.message_queue:
            if message.message_id == message_id:
                return message.status

        return None

    def get_message_events(self, message_id: str) -> List[EmailEvent]:
        """Get events for a message"""
        return self.events.get(message_id, [])

    async def get_email_statistics(self) -> Dict[str, Any]:
        """Get email statistics"""
        total_sent = len(self.sent_messages)
        queued = len(self.message_queue)

        status_counts = {}
        for message in self.sent_messages.values():
            status = message.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_sent": total_sent,
            "queued": queued,
            "unsubscribed": len(self.unsubscribed_emails),
            "status_breakdown": status_counts,
            "delivery_rate": status_counts.get("delivered", 0) / max(total_sent, 1) * 100,
            "open_rate": status_counts.get("opened", 0) / max(total_sent, 1) * 100,
            "click_rate": status_counts.get("clicked", 0) / max(total_sent, 1) * 100
        }

class EmailAPI:
    """API interface for email notifications"""

    def __init__(self, email_engine: EmailNotificationEngine):
        self.email_engine = email_engine

    async def send_welcome_email_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for welcome emails"""
        try:
            message_id = await self.email_engine.send_welcome_email(
                user_email=request_data["user_email"],
                user_name=request_data["user_name"],
                dashboard_url=request_data["dashboard_url"]
            )
            return {"success": True, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_notification_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic notification endpoint"""
        try:
            message_id = await self.email_engine.send_template_email(
                template_id=request_data["template_id"],
                to_emails=request_data["to_emails"],
                template_data=request_data["template_data"],
                priority=EmailPriority(request_data.get("priority", EmailPriority.NORMAL.value)),
                tags=request_data.get("tags", [])
            )
            return {"success": True, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_message_status_endpoint(self, message_id: str) -> Dict[str, Any]:
        """API endpoint for message status"""
        try:
            status = self.email_engine.get_message_status(message_id)
            events = self.email_engine.get_message_events(message_id)

            return {
                "success": True,
                "message_id": message_id,
                "status": status.value if status else None,
                "events": [
                    {
                        "event_type": event.event_type,
                        "timestamp": event.timestamp.isoformat(),
                        "email": event.email
                    }
                    for event in events
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def unsubscribe_endpoint(self, email: str) -> Dict[str, Any]:
        """API endpoint for unsubscribe"""
        try:
            self.email_engine.unsubscribe_email(email)
            return {"success": True, "message": "Email unsubscribed successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_statistics_endpoint(self) -> Dict[str, Any]:
        """API endpoint for email statistics"""
        try:
            stats = await self.email_engine.get_email_statistics()
            return {"success": True, "statistics": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}