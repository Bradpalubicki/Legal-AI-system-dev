"""
Email Sender

Handles email sending via SMTP (Gmail) or SendGrid.
Includes tracking pixel and link tracking.

For Railway deployment, uses Gmail SMTP which is already configured.
"""

import os
import re
import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime

import httpx

from app.marketing.campaigns.models import EmailSend
from app.marketing.contacts.models import Contact
from app.marketing.email.compliance import CANSPAMCompliance

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Handles email sending with tracking and compliance.

    Supports both SMTP (Gmail) and SendGrid API.
    Gmail SMTP is used by default for Railway deployments.
    """

    def __init__(self):
        # SendGrid config
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')

        # SMTP config (Gmail)
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

        # Default sender
        self.default_from_email = os.getenv('FROM_EMAIL', 'alerts@courtcase-search.com')
        self.default_from_name = os.getenv('FROM_NAME', 'CourtCase-Search')

        # Tracking
        self.tracking_domain = os.getenv(
            'EMAIL_TRACKING_DOMAIN',
            os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')
        )

        # Compliance checker
        self.compliance = CANSPAMCompliance()

        # Determine which provider to use
        self._use_sendgrid = bool(
            self.sendgrid_api_key and
            not self.sendgrid_api_key.startswith('SG.test')
        )

    async def send_email(
        self,
        email_send: EmailSend,
        contact: Contact
    ) -> bool:
        """
        Send a single email with tracking.

        Args:
            email_send: EmailSend record with content
            contact: Recipient contact

        Returns:
            True if sent successfully
        """
        # Compliance check
        check = self.compliance.check_email(
            to_contact=contact,
            subject=email_send.subject_line,
            body_html=email_send.body_html,
            from_email=email_send.from_email
        )

        if not check.is_compliant:
            logger.error(f"Email failed compliance: {check.violations}")
            email_send.status = "compliance_failed"
            email_send.compliance_notes = "; ".join(check.violations)
            return False

        if check.warnings:
            logger.warning(f"Email compliance warnings: {check.warnings}")

        # Add tracking
        body_with_tracking = self._add_tracking(
            email_send.body_html,
            email_send.id
        )

        # Generate unsubscribe URL
        unsubscribe_url = self.compliance.generate_unsubscribe_url(
            email=email_send.to_email,
            email_send_id=email_send.id,
            token=email_send.landing_token
        )

        # Add compliance footer
        body_final = self.compliance.add_compliance_footer(
            body_with_tracking,
            unsubscribe_url=unsubscribe_url
        )

        # Replace template variables
        body_final = self._replace_template_vars(
            body_final,
            email_send,
            contact,
            unsubscribe_url
        )

        subject = self._replace_template_vars(
            email_send.subject_line,
            email_send,
            contact,
            unsubscribe_url
        )

        # Send via appropriate provider
        try:
            if self._use_sendgrid:
                result = await self._send_via_sendgrid(
                    to_email=email_send.to_email,
                    from_email=email_send.from_email or self.default_from_email,
                    from_name=email_send.from_name or self.default_from_name,
                    subject=subject,
                    body_html=body_final,
                    body_text=email_send.body_text
                )
            else:
                result = await self._send_via_smtp(
                    to_email=email_send.to_email,
                    from_email=email_send.from_email or self.default_from_email,
                    from_name=email_send.from_name or self.default_from_name,
                    subject=subject,
                    body_html=body_final,
                    body_text=email_send.body_text
                )

            email_send.status = "sent"
            email_send.sent_at = datetime.utcnow()
            email_send.email_provider_id = result.get("message_id")
            email_send.email_provider = result.get("provider")

            # Update contact last contacted
            contact.last_contacted_at = datetime.utcnow()

            logger.info(f"Email sent to {email_send.to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {email_send.to_email}: {e}")
            email_send.status = "failed"
            email_send.error_message = str(e)
            email_send.retry_count = (email_send.retry_count or 0) + 1
            return False

    async def _send_via_sendgrid(
        self,
        to_email: str,
        from_email: str,
        from_name: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid API."""
        content = [{"type": "text/html", "value": body_html}]
        if body_text:
            content.insert(0, {"type": "text/plain", "value": body_text})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self.sendgrid_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{
                        "to": [{"email": to_email}]
                    }],
                    "from": {
                        "email": from_email,
                        "name": from_name
                    },
                    "subject": subject,
                    "content": content,
                    "tracking_settings": {
                        "click_tracking": {"enable": True},
                        "open_tracking": {"enable": True}
                    }
                },
                timeout=30.0
            )

            response.raise_for_status()

            return {
                "message_id": response.headers.get("X-Message-Id"),
                "provider": "sendgrid",
                "status": "sent"
            }

    async def _send_via_smtp(
        self,
        to_email: str,
        from_email: str,
        from_name: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP (Gmail)."""
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email

        # Add plain text part
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)

        # Add HTML part
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)

        # Send via SMTP (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, msg, to_email)

        return {
            "message_id": msg['Message-ID'] or f"smtp-{datetime.utcnow().timestamp()}",
            "provider": "smtp",
            "status": "sent"
        }

    def _smtp_send(self, msg: MIMEMultipart, to_email: str) -> None:
        """Synchronous SMTP send."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.smtp_use_tls:
                server.starttls()

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.send_message(msg)

    def _add_tracking(self, body_html: str, email_send_id: int) -> str:
        """
        Add open tracking pixel and wrap links for click tracking.

        Args:
            body_html: Original HTML content
            email_send_id: Email send ID for tracking

        Returns:
            HTML with tracking added
        """
        # Add tracking pixel for open tracking
        tracking_pixel = (
            f'<img src="{self.tracking_domain}/api/v1/admin/marketing/track/open/{email_send_id}" '
            f'width="1" height="1" style="display:none;" alt="" />'
        )

        if '</body>' in body_html.lower():
            lower_body = body_html.lower()
            pos = lower_body.rfind('</body>')
            body_html = body_html[:pos] + tracking_pixel + body_html[pos:]
        else:
            body_html += tracking_pixel

        # Wrap links for click tracking
        def replace_link(match):
            original_url = match.group(1)
            # Don't track unsubscribe or mailto links
            if 'unsubscribe' in original_url.lower() or original_url.startswith('mailto:'):
                return match.group(0)

            import urllib.parse
            tracked_url = (
                f"{self.tracking_domain}/api/v1/admin/marketing/track/click/{email_send_id}"
                f"?url={urllib.parse.quote(original_url)}"
            )
            return f'href="{tracked_url}"'

        body_html = re.sub(r'href="([^"]+)"', replace_link, body_html)

        return body_html

    def _replace_template_vars(
        self,
        content: str,
        email_send: EmailSend,
        contact: Contact,
        unsubscribe_url: str
    ) -> str:
        """
        Replace template variables in content.

        Supported variables:
        - {{first_name}}, {{last_name}}, {{full_name}}
        - {{firm_name}}, {{email}}
        - {{case_name}}, {{case_number}}, {{court}}
        - {{unsubscribe_url}}, {{landing_url}}
        """
        if not content:
            return content

        personalization = email_send.personalization_data or {}

        replacements = {
            '{{first_name}}': contact.first_name or personalization.get('first_name', ''),
            '{{last_name}}': contact.last_name or personalization.get('last_name', ''),
            '{{full_name}}': contact.full_name or contact.display_name,
            '{{firm_name}}': contact.firm_name or personalization.get('firm_name', ''),
            '{{email}}': contact.email,
            '{{case_name}}': personalization.get('case_name', ''),
            '{{case_number}}': personalization.get('case_number', ''),
            '{{court}}': personalization.get('court', ''),
            '{{unsubscribe_url}}': unsubscribe_url,
            '{{landing_url}}': f"{self.tracking_domain}/case/{email_send.landing_token}" if email_send.landing_token else '',
        }

        for var, value in replacements.items():
            content = content.replace(var, str(value) if value else '')

        return content

    async def send_test_email(
        self,
        to_email: str,
        subject: str = "Test Email from CourtCase-Search",
        body: str = "This is a test email."
    ) -> Dict[str, Any]:
        """Send a simple test email."""
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Test Email</h2>
            <p>{body}</p>
            <p>Sent at: {datetime.utcnow().isoformat()}</p>
        </body>
        </html>
        """

        if self._use_sendgrid:
            return await self._send_via_sendgrid(
                to_email=to_email,
                from_email=self.default_from_email,
                from_name=self.default_from_name,
                subject=subject,
                body_html=body_html
            )
        else:
            return await self._send_via_smtp(
                to_email=to_email,
                from_email=self.default_from_email,
                from_name=self.default_from_name,
                subject=subject,
                body_html=body_html
            )
