"""
SMS Notification System

Critical alert system for urgent legal notifications including
court dates, deadlines, attorney messages, and payment failures
with Twilio integration.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class SMSProvider(Enum):
    """SMS service providers"""
    TWILIO = "twilio"
    AWS_SNS = "aws_sns"
    VONAGE = "vonage"
    MOCK = "mock"

class SMSStatus(Enum):
    """SMS delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"

class SMSPriority(Enum):
    """SMS priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class SMSType(Enum):
    """Types of SMS messages"""
    DEADLINE = "deadline"
    COURT_DATE = "court_date"
    DOCUMENT_REQUEST = "document_request"
    ATTORNEY_MESSAGE = "attorney_message"
    PAYMENT_FAILURE = "payment_failure"
    SECURITY_ALERT = "security_alert"
    SYSTEM_ALERT = "system_alert"
    VERIFICATION = "verification"

@dataclass
class SMSMessage:
    """SMS message"""
    message_id: str
    to_number: str
    from_number: str
    message: str
    sms_type: SMSType
    priority: SMSPriority = SMSPriority.NORMAL
    status: SMSStatus = SMSStatus.PENDING
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    case_id: Optional[str] = None

@dataclass
class SMSTemplate:
    """SMS message template"""
    template_id: str
    name: str
    message_template: str
    sms_type: SMSType
    priority: SMSPriority
    variables: List[str] = field(default_factory=list)
    max_length: int = 160

class TwilioProvider:
    """Twilio SMS provider"""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"

    async def send_sms(self, message: SMSMessage) -> bool:
        """Send SMS via Twilio"""
        try:
            import aiohttp
            import base64

            # Create basic auth header
            credentials = f"{self.account_sid}:{self.auth_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "To": message.to_number,
                "From": self.from_number,
                "Body": message.message
            }

            # Convert to URL-encoded format
            encoded_data = "&".join([f"{k}={quote(str(v))}" for k, v in data.items()])

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/Messages.json",
                    headers=headers,
                    data=encoded_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        message.metadata["twilio_sid"] = result.get("sid")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Twilio error: {error_text}")
                        return False

        except Exception as e:
            logger.error(f"Twilio send error: {str(e)}")
            return False

class MockSMSProvider:
    """Mock SMS provider for testing"""

    def __init__(self):
        self.sent_messages: List[SMSMessage] = []

    async def send_sms(self, message: SMSMessage) -> bool:
        """Mock send SMS"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)

            self.sent_messages.append(message)
            message.metadata["mock_sent"] = True

            logger.info(f"Mock SMS sent to {message.to_number}: {message.message[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Mock SMS error: {str(e)}")
            return False

class SMSTemplateManager:
    """Manage SMS templates"""

    def __init__(self):
        self.templates: Dict[str, SMSTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default SMS templates"""
        templates = {
            "urgent_deadline": SMSTemplate(
                template_id="urgent_deadline",
                name="Urgent Deadline Alert",
                message_template="URGENT: {case_name} deadline in {hours} hours. Task: {task}. Act now! View: {url}",
                sms_type=SMSType.DEADLINE,
                priority=SMSPriority.URGENT,
                variables=["case_name", "hours", "task", "url"]
            ),
            "court_date_reminder": SMSTemplate(
                template_id="court_date_reminder",
                name="Court Date Reminder",
                message_template="Court appearance for {case_name} on {date} at {time}. Location: {court}. Prepare: {prep_items}",
                sms_type=SMSType.COURT_DATE,
                priority=SMSPriority.CRITICAL,
                variables=["case_name", "date", "time", "court", "prep_items"]
            ),
            "document_request": SMSTemplate(
                template_id="document_request",
                name="Document Request",
                message_template="Attorney {attorney} requests: {documents} for {case_name}. Due: {due_date}. Upload: {url}",
                sms_type=SMSType.DOCUMENT_REQUEST,
                priority=SMSPriority.HIGH,
                variables=["attorney", "documents", "case_name", "due_date", "url"]
            ),
            "attorney_message": SMSTemplate(
                template_id="attorney_message",
                name="Attorney Message",
                message_template="Message from {attorney}: {message}. Case: {case_name}. Reply: {reply_url}",
                sms_type=SMSType.ATTORNEY_MESSAGE,
                priority=SMSPriority.HIGH,
                variables=["attorney", "message", "case_name", "reply_url"]
            ),
            "payment_failure": SMSTemplate(
                template_id="payment_failure",
                name="Payment Failure Alert",
                message_template="Payment failed for invoice #{invoice}. Amount: ${amount}. Update payment: {url} or call {phone}",
                sms_type=SMSType.PAYMENT_FAILURE,
                priority=SMSPriority.URGENT,
                variables=["invoice", "amount", "url", "phone"]
            ),
            "security_alert": SMSTemplate(
                template_id="security_alert",
                name="Security Alert",
                message_template="Security alert: {alert_type} detected on your account at {time}. If not you, secure account: {url}",
                sms_type=SMSType.SECURITY_ALERT,
                priority=SMSPriority.CRITICAL,
                variables=["alert_type", "time", "url"]
            ),
            "verification_code": SMSTemplate(
                template_id="verification_code",
                name="Verification Code",
                message_template="Your Legal AI verification code is: {code}. Valid for {minutes} minutes. Do not share.",
                sms_type=SMSType.VERIFICATION,
                priority=SMSPriority.HIGH,
                variables=["code", "minutes"]
            )
        }

        self.templates.update(templates)

    def get_template(self, template_id: str) -> Optional[SMSTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def render_template(self, template_id: str, data: Dict[str, Any]) -> str:
        """Render template with data"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        message = template.message_template
        for var in template.variables:
            if var in data:
                message = message.replace(f"{{{var}}}", str(data[var]))

        # Ensure message doesn't exceed max length
        if len(message) > template.max_length:
            message = message[:template.max_length - 3] + "..."

        return message

class SMSNotificationSystem:
    """
    Comprehensive SMS notification system for critical legal alerts
    """

    def __init__(self, provider: SMSProvider = SMSProvider.MOCK):
        self.provider_type = provider
        self.provider = None
        self.template_manager = SMSTemplateManager()
        self.message_queue: List[SMSMessage] = []
        self.sent_messages: Dict[str, SMSMessage] = {}
        self.blocked_numbers: set = set()

        # Default settings
        self.default_from_number = "+1234567890"  # Replace with actual number

        # Phone number validation
        self.phone_pattern = re.compile(r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$')

    def configure_twilio(self, account_sid: str, auth_token: str, from_number: str):
        """Configure Twilio provider"""
        self.provider = TwilioProvider(account_sid, auth_token, from_number)
        self.default_from_number = from_number

    def configure_mock(self):
        """Configure mock provider for testing"""
        self.provider = MockSMSProvider()

    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)

        # Add +1 if not present and number is 10 digits
        if not cleaned.startswith('+'):
            if len(cleaned) == 10:
                cleaned = f"+1{cleaned}"
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                cleaned = f"+{cleaned}"
            else:
                cleaned = f"+1{cleaned}"

        return cleaned

    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        normalized = self._normalize_phone_number(phone)
        return bool(self.phone_pattern.match(normalized.replace('+', '')))

    async def send_urgent_deadline_alert(self, to_number: str, user_id: str,
                                       case_name: str, hours_remaining: int,
                                       task_description: str, case_url: str,
                                       case_id: Optional[str] = None) -> str:
        """Send urgent deadline alert"""
        if hours_remaining <= 24:  # Only send if within 24 hours
            return await self.send_template_sms(
                template_id="urgent_deadline",
                to_number=to_number,
                template_data={
                    "case_name": case_name,
                    "hours": hours_remaining,
                    "task": task_description[:50],  # Truncate for SMS
                    "url": case_url
                },
                priority=SMSPriority.URGENT,
                user_id=user_id,
                case_id=case_id
            )
        return ""

    async def send_court_date_reminder(self, to_number: str, user_id: str,
                                     case_name: str, court_date: str,
                                     court_time: str, court_location: str,
                                     prep_items: str, case_id: Optional[str] = None) -> str:
        """Send court date reminder"""
        return await self.send_template_sms(
            template_id="court_date_reminder",
            to_number=to_number,
            template_data={
                "case_name": case_name,
                "date": court_date,
                "time": court_time,
                "court": court_location[:30],  # Truncate for SMS
                "prep_items": prep_items[:40]
            },
            priority=SMSPriority.CRITICAL,
            user_id=user_id,
            case_id=case_id
        )

    async def send_document_request(self, to_number: str, user_id: str,
                                  attorney_name: str, requested_documents: str,
                                  case_name: str, due_date: str,
                                  upload_url: str, case_id: Optional[str] = None) -> str:
        """Send document request alert"""
        return await self.send_template_sms(
            template_id="document_request",
            to_number=to_number,
            template_data={
                "attorney": attorney_name,
                "documents": requested_documents[:30],
                "case_name": case_name,
                "due_date": due_date,
                "url": upload_url
            },
            priority=SMSPriority.HIGH,
            user_id=user_id,
            case_id=case_id
        )

    async def send_attorney_message(self, to_number: str, user_id: str,
                                  attorney_name: str, message_content: str,
                                  case_name: str, reply_url: str,
                                  case_id: Optional[str] = None) -> str:
        """Send attorney message notification"""
        return await self.send_template_sms(
            template_id="attorney_message",
            to_number=to_number,
            template_data={
                "attorney": attorney_name,
                "message": message_content[:50],  # Truncate for SMS
                "case_name": case_name,
                "reply_url": reply_url
            },
            priority=SMSPriority.HIGH,
            user_id=user_id,
            case_id=case_id
        )

    async def send_payment_failure_alert(self, to_number: str, user_id: str,
                                        invoice_number: str, amount: float,
                                        payment_url: str, support_phone: str) -> str:
        """Send payment failure alert"""
        return await self.send_template_sms(
            template_id="payment_failure",
            to_number=to_number,
            template_data={
                "invoice": invoice_number,
                "amount": f"{amount:.2f}",
                "url": payment_url,
                "phone": support_phone
            },
            priority=SMSPriority.URGENT,
            user_id=user_id
        )

    async def send_security_alert(self, to_number: str, user_id: str,
                                alert_type: str, alert_time: str,
                                secure_url: str) -> str:
        """Send security alert"""
        return await self.send_template_sms(
            template_id="security_alert",
            to_number=to_number,
            template_data={
                "alert_type": alert_type,
                "time": alert_time,
                "url": secure_url
            },
            priority=SMSPriority.CRITICAL,
            user_id=user_id
        )

    async def send_verification_code(self, to_number: str, user_id: str,
                                   verification_code: str, expiry_minutes: int = 10) -> str:
        """Send verification code"""
        return await self.send_template_sms(
            template_id="verification_code",
            to_number=to_number,
            template_data={
                "code": verification_code,
                "minutes": str(expiry_minutes)
            },
            priority=SMSPriority.HIGH,
            user_id=user_id
        )

    async def send_template_sms(self, template_id: str, to_number: str,
                              template_data: Dict[str, Any],
                              priority: SMSPriority = SMSPriority.NORMAL,
                              user_id: Optional[str] = None,
                              case_id: Optional[str] = None,
                              scheduled_at: Optional[datetime] = None) -> str:
        """Send templated SMS"""
        try:
            # Validate and normalize phone number
            normalized_number = self._normalize_phone_number(to_number)
            if not self._validate_phone_number(normalized_number):
                raise ValueError(f"Invalid phone number: {to_number}")

            # Check if number is blocked
            if normalized_number in self.blocked_numbers:
                logger.info(f"SMS not sent to blocked number: {normalized_number}")
                return ""

            # Render template
            message_text = self.template_manager.render_template(template_id, template_data)

            # Get template for SMS type
            template = self.template_manager.get_template(template_id)
            sms_type = template.sms_type if template else SMSType.SYSTEM_ALERT

            # Create message
            message = SMSMessage(
                message_id=f"sms_{uuid.uuid4().hex[:12]}",
                to_number=normalized_number,
                from_number=self.default_from_number,
                message=message_text,
                sms_type=sms_type,
                priority=priority,
                scheduled_at=scheduled_at,
                user_id=user_id,
                case_id=case_id,
                metadata={"template_id": template_id, "template_data": template_data}
            )

            # Queue or send immediately
            if scheduled_at and scheduled_at > datetime.now():
                self.message_queue.append(message)
                message.status = SMSStatus.QUEUED
            else:
                success = await self._send_message(message)
                if success:
                    message.status = SMSStatus.SENT
                    message.sent_at = datetime.now()
                    self.sent_messages[message.message_id] = message
                else:
                    message.status = SMSStatus.FAILED

            logger.info(f"SMS {message.message_id} status: {message.status.value}")
            return message.message_id

        except Exception as e:
            logger.error(f"Error sending template SMS: {str(e)}")
            raise

    async def send_custom_sms(self, to_number: str, message: str,
                            priority: SMSPriority = SMSPriority.NORMAL,
                            user_id: Optional[str] = None,
                            case_id: Optional[str] = None) -> str:
        """Send custom SMS message"""
        try:
            # Validate and normalize phone number
            normalized_number = self._normalize_phone_number(to_number)
            if not self._validate_phone_number(normalized_number):
                raise ValueError(f"Invalid phone number: {to_number}")

            # Check if number is blocked
            if normalized_number in self.blocked_numbers:
                logger.info(f"SMS not sent to blocked number: {normalized_number}")
                return ""

            # Truncate message if too long
            if len(message) > 160:
                message = message[:157] + "..."

            sms_message = SMSMessage(
                message_id=f"sms_{uuid.uuid4().hex[:12]}",
                to_number=normalized_number,
                from_number=self.default_from_number,
                message=message,
                sms_type=SMSType.SYSTEM_ALERT,
                priority=priority,
                user_id=user_id,
                case_id=case_id
            )

            success = await self._send_message(sms_message)
            if success:
                sms_message.status = SMSStatus.SENT
                sms_message.sent_at = datetime.now()
                self.sent_messages[sms_message.message_id] = sms_message
            else:
                sms_message.status = SMSStatus.FAILED

            return sms_message.message_id

        except Exception as e:
            logger.error(f"Error sending custom SMS: {str(e)}")
            raise

    async def _send_message(self, message: SMSMessage) -> bool:
        """Send message using configured provider"""
        if not self.provider:
            logger.error("No SMS provider configured")
            return False

        try:
            success = await self.provider.send_sms(message)
            return success

        except Exception as e:
            logger.error(f"Error sending SMS {message.message_id}: {str(e)}")
            return False

    async def process_scheduled_messages(self) -> int:
        """Process scheduled SMS messages"""
        current_time = datetime.now()
        messages_to_send = []

        # Find messages ready to send
        for message in self.message_queue[:]:
            if message.scheduled_at and message.scheduled_at <= current_time:
                messages_to_send.append(message)
                self.message_queue.remove(message)

        # Send messages
        for message in messages_to_send:
            success = await self._send_message(message)
            if success:
                message.status = SMSStatus.SENT
                message.sent_at = datetime.now()
                self.sent_messages[message.message_id] = message
            else:
                message.status = SMSStatus.FAILED

        return len(messages_to_send)

    def block_number(self, phone_number: str):
        """Block phone number from receiving SMS"""
        normalized = self._normalize_phone_number(phone_number)
        self.blocked_numbers.add(normalized)
        logger.info(f"Phone number {normalized} blocked from SMS")

    def unblock_number(self, phone_number: str):
        """Unblock phone number"""
        normalized = self._normalize_phone_number(phone_number)
        self.blocked_numbers.discard(normalized)
        logger.info(f"Phone number {normalized} unblocked")

    def get_message_status(self, message_id: str) -> Optional[SMSStatus]:
        """Get message delivery status"""
        if message_id in self.sent_messages:
            return self.sent_messages[message_id].status

        # Check queue
        for message in self.message_queue:
            if message.message_id == message_id:
                return message.status

        return None

    def update_delivery_status(self, message_id: str, status: SMSStatus, delivered_at: Optional[datetime] = None):
        """Update message delivery status (called by webhook)"""
        if message_id in self.sent_messages:
            message = self.sent_messages[message_id]
            message.status = status
            if delivered_at:
                message.delivered_at = delivered_at
            logger.info(f"Updated SMS {message_id} status to {status.value}")

    async def get_sms_statistics(self) -> Dict[str, Any]:
        """Get SMS statistics"""
        total_sent = len(self.sent_messages)
        queued = len(self.message_queue)

        status_counts = {}
        priority_counts = {}
        type_counts = {}

        for message in self.sent_messages.values():
            # Status counts
            status = message.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Priority counts
            priority = message.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

            # Type counts
            sms_type = message.sms_type.value
            type_counts[sms_type] = type_counts.get(sms_type, 0) + 1

        return {
            "total_sent": total_sent,
            "queued": queued,
            "blocked_numbers": len(self.blocked_numbers),
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "type_breakdown": type_counts,
            "delivery_rate": status_counts.get("delivered", 0) / max(total_sent, 1) * 100
        }

class SMSAPI:
    """API interface for SMS notifications"""

    def __init__(self, sms_system: SMSNotificationSystem):
        self.sms_system = sms_system

    async def send_urgent_deadline_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for urgent deadline alerts"""
        try:
            message_id = await self.sms_system.send_urgent_deadline_alert(
                to_number=request_data["to_number"],
                user_id=request_data["user_id"],
                case_name=request_data["case_name"],
                hours_remaining=request_data["hours_remaining"],
                task_description=request_data["task_description"],
                case_url=request_data["case_url"],
                case_id=request_data.get("case_id")
            )
            return {"success": True, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_court_reminder_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for court date reminders"""
        try:
            message_id = await self.sms_system.send_court_date_reminder(
                to_number=request_data["to_number"],
                user_id=request_data["user_id"],
                case_name=request_data["case_name"],
                court_date=request_data["court_date"],
                court_time=request_data["court_time"],
                court_location=request_data["court_location"],
                prep_items=request_data["prep_items"],
                case_id=request_data.get("case_id")
            )
            return {"success": True, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_verification_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for verification codes"""
        try:
            message_id = await self.sms_system.send_verification_code(
                to_number=request_data["to_number"],
                user_id=request_data["user_id"],
                verification_code=request_data["verification_code"],
                expiry_minutes=request_data.get("expiry_minutes", 10)
            )
            return {"success": True, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_message_status_endpoint(self, message_id: str) -> Dict[str, Any]:
        """API endpoint for message status"""
        try:
            status = self.sms_system.get_message_status(message_id)
            return {
                "success": True,
                "message_id": message_id,
                "status": status.value if status else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def block_number_endpoint(self, phone_number: str) -> Dict[str, Any]:
        """API endpoint for blocking numbers"""
        try:
            self.sms_system.block_number(phone_number)
            return {"success": True, "message": "Phone number blocked"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_statistics_endpoint(self) -> Dict[str, Any]:
        """API endpoint for SMS statistics"""
        try:
            stats = await self.sms_system.get_sms_statistics()
            return {"success": True, "statistics": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}