"""
Email Notification Service
Sends email notifications for case updates
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""

    def __init__(self):
        self._config_loaded = False
        self.smtp_host = ''
        self.smtp_port = 587
        self.smtp_user = ''
        self.smtp_password = ''
        self.from_email = ''
        self.from_name = ''
        self.email_enabled = False
        self.app_base_url = ''  # Base URL for links in emails

    def _ensure_config_loaded(self):
        """Load email configuration from environment variables (lazy loading)"""
        if self._config_loaded:
            return

        # Reload environment variables from root .env to ensure we have the latest
        from pathlib import Path
        from dotenv import load_dotenv
        root_env = Path(__file__).parent.parent.parent.parent / '.env'
        if root_env.exists():
            load_dotenv(dotenv_path=root_env, override=True)

        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'Legal AI System')
        self.email_enabled = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        # Base URL for links in emails - defaults to localhost for dev, should be set in production
        self.app_base_url = os.getenv('APP_BASE_URL', os.getenv('NEXT_PUBLIC_APP_URL', 'http://localhost:3000')).rstrip('/')
        self._config_loaded = True

        logger.info(f"[EMAIL] Config loaded: enabled={self.email_enabled}, smtp_user={self.smtp_user[:20] if self.smtp_user else 'empty'}, base_url={self.app_base_url}")

    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        self._ensure_config_loaded()
        return bool(self.smtp_user and self.smtp_password and self.email_enabled)

    def send_new_documents_notification(
        self,
        to_email: str,
        docket_id: int,
        case_name: str,
        document_count: int,
        documents: List[Dict[str, Any]],
        court: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email notification for new documents

        Args:
            to_email: Recipient email address
            docket_id: Case docket ID
            case_name: Case name
            document_count: Number of new documents
            documents: List of new documents
            court: Court identifier

        Returns:
            Dictionary with success status and any errors
        """
        if not self.is_configured():
            logger.warning("Email notifications not configured - skipping email")
            return {
                "success": False,
                "sent": False,
                "error": "Email notifications not configured"
            }

        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = f"New Document{'s' if document_count > 1 else ''} Filed - {case_name}"

            # Create email body
            text_body = self._create_text_body(
                docket_id, case_name, document_count, documents, court
            )
            html_body = self._create_html_body(
                docket_id, case_name, document_count, documents, court
            )

            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email} for docket {docket_id}")

            return {
                "success": True,
                "sent": True,
                "to_email": to_email,
                "sent_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {
                "success": False,
                "sent": False,
                "error": str(e),
                "to_email": to_email
            }

    def _create_text_body(
        self,
        docket_id: int,
        case_name: str,
        document_count: int,
        documents: List[Dict[str, Any]],
        court: Optional[str]
    ) -> str:
        """Create plain text email body"""
        lines = [
            f"New Document{'s' if document_count > 1 else ''} Filed",
            "=" * 50,
            "",
            f"Case: {case_name}",
            f"Docket ID: {docket_id}",
        ]

        if court:
            lines.append(f"Court: {court}")

        lines.extend([
            "",
            f"{document_count} new document{'s' if document_count > 1 else ''} {'have' if document_count > 1 else 'has'} been filed:",
            ""
        ])

        # List documents (limit to first 10)
        for i, doc in enumerate(documents[:10], 1):
            doc_num = doc.get('document_number', 'N/A')
            description = doc.get('short_description') or doc.get('description', 'No description')
            is_free = doc.get('is_available', False)

            lines.append(f"{i}. Doc #{doc_num}: {description}")
            if is_free:
                lines.append("   [FREE - Available to download]")

        if len(documents) > 10:
            lines.append(f"\n... and {len(documents) - 10} more documents")

        lines.extend([
            "",
            "View all documents in your Legal AI System dashboard:",
            f"{self.app_base_url}/pacer?docket={docket_id}",
            "",
            "---",
            "This is an automated notification from Legal AI System",
        ])

        return "\n".join(lines)

    def _create_html_body(
        self,
        docket_id: int,
        case_name: str,
        document_count: int,
        documents: List[Dict[str, Any]],
        court: Optional[str]
    ) -> str:
        """Create HTML email body"""
        court_html = f"<p><strong>Court:</strong> {court}</p>" if court else ""

        docs_html = []
        for i, doc in enumerate(documents[:10], 1):
            doc_num = doc.get('document_number', 'N/A')
            description = doc.get('short_description') or doc.get('description', 'No description')
            is_free = doc.get('is_available', False)
            free_badge = '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px;">FREE</span>' if is_free else ''

            docs_html.append(f"""
                <li style="margin-bottom: 12px;">
                    <strong>Doc #{doc_num}:</strong> {description} {free_badge}
                </li>
            """)

        if len(documents) > 10:
            docs_html.append(f"""
                <li style="color: #6b7280; margin-top: 8px;">
                    ... and {len(documents) - 10} more documents
                </li>
            """)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">New Document{'s' if document_count > 1 else ''} Filed</h1>
            </div>

            <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #e5e7eb;">
                <div style="background: white; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                    <h2 style="margin-top: 0; color: #1f2937; font-size: 20px;">{case_name}</h2>
                    <p><strong>Docket ID:</strong> {docket_id}</p>
                    {court_html}
                    <div style="background: #dbeafe; border-left: 4px solid #3b82f6; padding: 12px; margin: 16px 0;">
                        <p style="margin: 0; color: #1e40af;">
                            <strong>{document_count}</strong> new document{'s' if document_count > 1 else ''} {'have' if document_count > 1 else 'has'} been filed
                        </p>
                    </div>
                </div>

                <div style="background: white; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #1f2937;">New Documents:</h3>
                    <ul style="padding-left: 20px;">
                        {''.join(docs_html)}
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.app_base_url}/pacer?docket={docket_id}"
                       style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        View All Documents
                    </a>
                </div>

                <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">
                    <p>This is an automated notification from <strong>Legal AI System</strong></p>
                    <p style="margin: 0;">To manage your notification preferences, visit your dashboard</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    async def send_case_update_email(
        self,
        user_id: int,
        docket_id: int,
        new_documents: List[Dict[str, Any]],
        case_name: Optional[str] = None,
        court: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send case update email (wrapper for compatibility with case_monitor_service)

        Args:
            user_id: User ID to send notification to
            docket_id: Case docket ID
            new_documents: List of new documents
            case_name: Name of the case (from monitor)
            court: Court name (from monitor)

        Returns:
            Dictionary with success status
        """
        # Get user email from database
        try:
            from app.src.core.database import SessionLocal
            from app.models.user import User

            db = SessionLocal()
            user = db.query(User).filter(User.id == user_id).first()
            db.close()

            if not user or not user.email:
                logger.warning(f"User {user_id} not found or has no email")
                return {"success": False, "error": "User not found or no email"}

            # Use provided case_name/court or try to extract from documents
            if not case_name:
                case_name = new_documents[0].get('case_name', 'Unknown Case') if new_documents else 'Unknown Case'
            if not court:
                court = new_documents[0].get('court', None) if new_documents else None

            logger.info(f"[EMAIL] Sending notification to {user.email} for case: {case_name}, court: {court}")

            return self.send_new_documents_notification(
                to_email=user.email,
                docket_id=docket_id,
                case_name=case_name,
                document_count=len(new_documents),
                documents=new_documents,
                court=court
            )

        except Exception as e:
            logger.error(f"Error sending case update email: {e}")
            return {"success": False, "error": str(e)}


    def send_account_lockout_notification(
        self,
        to_email: str,
        user_name: str,
        lockout_duration_minutes: int,
        lockout_until: datetime,
        failed_attempts: int
    ) -> Dict[str, Any]:
        """
        Send email notification when an account is locked due to failed login attempts.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            lockout_duration_minutes: Duration of lockout in minutes
            lockout_until: Datetime when account will be unlocked
            failed_attempts: Number of failed login attempts

        Returns:
            Dictionary with success status and any errors
        """
        if not self.is_configured():
            logger.warning("Email notifications not configured - skipping lockout email")
            return {
                "success": False,
                "sent": False,
                "error": "Email notifications not configured"
            }

        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = "Security Alert: Account Temporarily Locked"

            # Create email body
            text_body = self._create_lockout_text_body(
                user_name, lockout_duration_minutes, lockout_until, failed_attempts
            )
            html_body = self._create_lockout_html_body(
                user_name, lockout_duration_minutes, lockout_until, failed_attempts
            )

            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Account lockout email sent successfully to {to_email}")

            return {
                "success": True,
                "sent": True,
                "to_email": to_email,
                "sent_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send lockout email to {to_email}: {str(e)}")
            return {
                "success": False,
                "sent": False,
                "error": str(e),
                "to_email": to_email
            }

    def _create_lockout_text_body(
        self,
        user_name: str,
        lockout_duration_minutes: int,
        lockout_until: datetime,
        failed_attempts: int
    ) -> str:
        """Create plain text email body for account lockout"""
        unlock_time = lockout_until.strftime("%I:%M %p on %B %d, %Y")

        return f"""
Security Alert: Account Temporarily Locked
{'=' * 50}

Hello {user_name},

Your Legal AI System account has been temporarily locked due to {failed_attempts} failed login attempts.

Your account will be automatically unlocked at:
{unlock_time} (UTC)

Lockout duration: {lockout_duration_minutes} minutes

If this was you:
- Wait {lockout_duration_minutes} minutes and try again
- Make sure you're using the correct password
- Use the "Forgot Password" feature if needed

If this wasn't you:
- Someone may be trying to access your account
- Consider changing your password once the lockout expires
- Enable two-factor authentication if available

For security questions, contact our support team.

---
This is an automated security notification from Legal AI System.
"""

    def _create_lockout_html_body(
        self,
        user_name: str,
        lockout_duration_minutes: int,
        lockout_until: datetime,
        failed_attempts: int
    ) -> str:
        """Create HTML email body for account lockout"""
        unlock_time = lockout_until.strftime("%I:%M %p on %B %d, %Y")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🔒 Security Alert</h1>
            </div>

            <div style="background: #fef2f2; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #fecaca;">
                <h2 style="color: #991b1b; margin-top: 0;">Account Temporarily Locked</h2>

                <p>Hello <strong>{user_name}</strong>,</p>

                <p>Your Legal AI System account has been temporarily locked due to <strong>{failed_attempts} failed login attempts</strong>.</p>

                <div style="background: white; border-left: 4px solid #dc2626; padding: 16px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0;"><strong>Your account will be automatically unlocked at:</strong></p>
                    <p style="margin: 8px 0 0 0; font-size: 18px; color: #1f2937;">{unlock_time} (UTC)</p>
                    <p style="margin: 8px 0 0 0; color: #6b7280;">Lockout duration: {lockout_duration_minutes} minutes</p>
                </div>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1f2937;">If this was you:</h3>
                    <ul style="color: #4b5563;">
                        <li>Wait {lockout_duration_minutes} minutes and try again</li>
                        <li>Make sure you're using the correct password</li>
                        <li>Use the "Forgot Password" feature if needed</li>
                    </ul>
                </div>

                <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #fcd34d;">
                    <h3 style="margin-top: 0; color: #92400e;">⚠️ If this wasn't you:</h3>
                    <ul style="color: #78350f;">
                        <li>Someone may be trying to access your account</li>
                        <li>Consider changing your password once the lockout expires</li>
                        <li>Enable two-factor authentication if available</li>
                    </ul>
                </div>

                <div style="text-align: center; padding-top: 20px; border-top: 1px solid #fecaca; color: #6b7280; font-size: 14px;">
                    <p>This is an automated security notification from <strong>Legal AI System</strong></p>
                    <p style="margin: 0;">For security questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """


    def send_case_access_welcome_email(
        self,
        to_email: str,
        user_name: str,
        case_name: str,
        case_number: str,
        access_type: str,
        amount_paid: float,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Send welcome email after purchasing case access.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            case_name: Name of the case
            case_number: Docket number
            access_type: Type of access (one_time or monthly)
            amount_paid: Amount paid for access
            expires_at: When access expires (None for one-time until case closes)

        Returns:
            Dictionary with success status and any errors
        """
        if not self.is_configured():
            logger.warning("Email notifications not configured - skipping welcome email")
            return {
                "success": False,
                "sent": False,
                "error": "Email notifications not configured"
            }

        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = f"Welcome! Case Monitoring Activated - {case_number}"

            # Create email body
            text_body = self._create_case_access_welcome_text(
                user_name, case_name, case_number, access_type, amount_paid, expires_at
            )
            html_body = self._create_case_access_welcome_html(
                user_name, case_name, case_number, access_type, amount_paid, expires_at
            )

            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Case access welcome email sent successfully to {to_email}")

            return {
                "success": True,
                "sent": True,
                "to_email": to_email,
                "sent_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send case access welcome email to {to_email}: {str(e)}")
            return {
                "success": False,
                "sent": False,
                "error": str(e),
                "to_email": to_email
            }

    def _create_case_access_welcome_text(
        self,
        user_name: str,
        case_name: str,
        case_number: str,
        access_type: str,
        amount_paid: float,
        expires_at: Optional[datetime]
    ) -> str:
        """Create plain text welcome email body"""
        access_desc = "Monthly Unlimited" if access_type == "monthly" else "One-Time Access"
        expiry_text = expires_at.strftime("%B %d, %Y") if expires_at else "Until case closes"

        return f"""
Welcome to Case Monitoring!
{'=' * 50}

Hello {user_name},

Thank you for your purchase! Your case monitoring is now active.

CASE DETAILS
------------
Case: {case_name}
Docket Number: {case_number}

ACCESS INFORMATION
------------------
Access Type: {access_desc}
Amount Paid: ${amount_paid:.2f}
Valid Until: {expiry_text}

WHAT YOU CAN DO NOW
-------------------
✓ Monitor case updates in real-time
✓ Receive email notifications for new documents
✓ Download court documents as they're filed
✓ Access AI-powered case analysis

Get started by viewing your case in the dashboard:
{self.app_base_url}/my-cases

NEED HELP?
----------
- Visit our Help Center: {self.app_base_url}/help
- Contact Support: support@legal-ai-system.com

---
This is an automated notification from Legal AI System.
"""

    def _create_case_access_welcome_html(
        self,
        user_name: str,
        case_name: str,
        case_number: str,
        access_type: str,
        amount_paid: float,
        expires_at: Optional[datetime]
    ) -> str:
        """Create HTML welcome email body"""
        access_desc = "Monthly Unlimited" if access_type == "monthly" else "One-Time Access"
        expiry_text = expires_at.strftime("%B %d, %Y") if expires_at else "Until case closes"
        badge_color = "#8b5cf6" if access_type == "monthly" else "#10b981"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🎉 Welcome!</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Your case monitoring is now active</p>
            </div>

            <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #e5e7eb;">
                <p style="font-size: 18px;">Hello <strong>{user_name}</strong>,</p>
                <p>Thank you for your purchase! You now have full access to monitor your case.</p>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb;">
                    <h3 style="margin-top: 0; color: #1f2937; border-bottom: 2px solid #10b981; padding-bottom: 10px;">Case Details</h3>
                    <p><strong>Case:</strong> {case_name}</p>
                    <p><strong>Docket Number:</strong> <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{case_number}</code></p>
                </div>

                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb;">
                    <h3 style="margin-top: 0; color: #1f2937; border-bottom: 2px solid #8b5cf6; padding-bottom: 10px;">Access Information</h3>
                    <p>
                        <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 600;">
                            {access_desc}
                        </span>
                    </p>
                    <p><strong>Amount Paid:</strong> ${amount_paid:.2f}</p>
                    <p><strong>Valid Until:</strong> {expiry_text}</p>
                </div>

                <div style="background: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #a7f3d0;">
                    <h3 style="margin-top: 0; color: #065f46;">What You Can Do Now</h3>
                    <ul style="color: #047857; margin: 0; padding-left: 20px;">
                        <li style="margin-bottom: 8px;">✓ Monitor case updates in real-time</li>
                        <li style="margin-bottom: 8px;">✓ Receive email notifications for new documents</li>
                        <li style="margin-bottom: 8px;">✓ Download court documents as they're filed</li>
                        <li style="margin-bottom: 8px;">✓ Access AI-powered case analysis</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.app_base_url}/my-cases"
                       style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        View Your Case Dashboard
                    </a>
                </div>

                <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">
                    <p>Questions? Visit our <a href="{self.app_base_url}/help" style="color: #10b981;">Help Center</a></p>
                    <p style="margin: 0;">This is an automated notification from <strong>Legal AI System</strong></p>
                </div>
            </div>
        </body>
        </html>
        """


# Global instance
email_notification_service = EmailNotificationService()
