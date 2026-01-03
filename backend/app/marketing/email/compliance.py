"""
CAN-SPAM Compliance

Ensures all marketing emails comply with CAN-SPAM Act requirements:
1. No false or misleading header information
2. No deceptive subject lines
3. Identify message as advertisement (less strict for B2B)
4. Include physical postal address
5. Tell recipients how to opt out
6. Honor opt-out requests within 10 business days
"""

import re
import os
import logging
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.marketing.contacts.models import Contact

logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheckResult:
    """Result of compliance check"""
    is_compliant: bool
    violations: List[str]
    warnings: List[str]


class CANSPAMCompliance:
    """
    Ensures all emails comply with CAN-SPAM Act requirements.

    The CAN-SPAM Act establishes requirements for commercial messages,
    gives recipients the right to opt out, and spells out penalties
    for violations.
    """

    # Patterns that indicate deceptive subjects
    DECEPTIVE_PATTERNS = [
        r'^re:\s',  # Fake reply
        r'^fwd:\s',  # Fake forward
        r'urgent action required',
        r'your account has been',
        r"you've won",
        r'claim your prize',
        r'act now',
        r'limited time',
        r'free money',
        r'winner',
        r'congratulations',
    ]

    # Required opt-out keywords
    OPT_OUT_KEYWORDS = [
        'unsubscribe',
        'opt-out',
        'opt out',
        'stop receiving',
        'remove me',
        'no longer wish to receive'
    ]

    def __init__(self):
        self.company_name = os.getenv('COMPANY_NAME', 'CourtCase-Search.com')
        self.company_address = os.getenv(
            'COMPANY_PHYSICAL_ADDRESS',
            '123 Main Street, Suite 100, Las Vegas, NV 89101'
        )
        self.from_email = os.getenv('DEFAULT_FROM_EMAIL', 'alerts@courtcase-search.com')
        self.from_name = os.getenv('DEFAULT_FROM_NAME', 'CourtCase-Search.com')
        self.tracking_domain = os.getenv(
            'EMAIL_TRACKING_DOMAIN',
            'https://courtcase-search.com'
        )

    def check_email(
        self,
        to_contact: Contact,
        subject: str,
        body_html: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> ComplianceCheckResult:
        """
        Check if email is CAN-SPAM compliant.

        Args:
            to_contact: Recipient contact
            subject: Email subject line
            body_html: HTML body content
            from_email: Sender email
            from_name: Sender name

        Returns:
            ComplianceCheckResult with violations and warnings
        """
        violations = []
        warnings = []

        # Check 1: Recipient hasn't opted out
        if not to_contact.is_subscribed:
            violations.append("Recipient has opted out of communications")

        if to_contact.opted_out_at:
            violations.append(f"Recipient opted out on {to_contact.opted_out_at}")

        # Check 2: Subject line
        if self._is_deceptive_subject(subject):
            violations.append("Subject line appears deceptive")

        if len(subject) > 200:
            warnings.append("Subject line is unusually long")

        if not subject.strip():
            violations.append("Subject line cannot be empty")

        # Check 3: Physical address present
        if not self._has_physical_address(body_html):
            violations.append("Email must include physical postal address")

        # Check 4: Opt-out mechanism present
        if not self._has_opt_out(body_html):
            violations.append("Email must include opt-out mechanism")

        # Check 5: From address is valid
        from_email = from_email or self.from_email
        if not self._is_valid_from(from_email):
            violations.append("From email address must be valid and monitored")

        # Check 6: Not sending too frequently
        if self._sent_recently(to_contact):
            warnings.append("Contact was emailed recently - consider spacing")

        # Check 7: Body content checks
        if not body_html or len(body_html.strip()) < 50:
            violations.append("Email body content is too short or empty")

        return ComplianceCheckResult(
            is_compliant=len(violations) == 0,
            violations=violations,
            warnings=warnings
        )

    def _is_deceptive_subject(self, subject: str) -> bool:
        """Check for obviously deceptive subject patterns."""
        if not subject:
            return False

        subject_lower = subject.lower().strip()

        for pattern in self.DECEPTIVE_PATTERNS:
            if re.search(pattern, subject_lower, re.IGNORECASE):
                return True

        return False

    def _has_physical_address(self, body_html: str) -> bool:
        """Check if email contains physical address."""
        if not body_html:
            return False

        # Check if our company address is in the email
        if self.company_address and self.company_address in body_html:
            return True

        # Check for common address patterns
        # Pattern: Number Street, City, ST ZIPCODE
        address_pattern = r'\d+\s+[\w\s]+,\s*[\w\s]+,\s*[A-Z]{2}\s+\d{5}'
        return bool(re.search(address_pattern, body_html))

    def _has_opt_out(self, body_html: str) -> bool:
        """Check if email has opt-out mechanism."""
        if not body_html:
            return False

        body_lower = body_html.lower()
        return any(keyword in body_lower for keyword in self.OPT_OUT_KEYWORDS)

    def _is_valid_from(self, from_email: str) -> bool:
        """Validate from email format."""
        if not from_email:
            return False

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(email_pattern, from_email))

    def _sent_recently(self, contact: Contact, hours: int = 24) -> bool:
        """Check if we've sent to this contact recently."""
        if not contact.last_contacted_at:
            return False

        return datetime.utcnow() - contact.last_contacted_at < timedelta(hours=hours)

    def add_compliance_footer(
        self,
        body_html: str,
        unsubscribe_url: Optional[str] = None
    ) -> str:
        """
        Add required compliance elements to email footer.

        Args:
            body_html: Original HTML body
            unsubscribe_url: URL for unsubscribe (will be templated if not provided)

        Returns:
            HTML body with compliance footer added
        """
        unsubscribe_link = unsubscribe_url or "{{unsubscribe_url}}"

        footer = f"""
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; font-family: Arial, sans-serif;">
            <p style="margin: 10px 0;">
                <strong>{self.company_name}</strong><br>
                {self.company_address}
            </p>

            <p style="margin: 10px 0;">
                You received this email because you are involved in litigation
                where public court records indicate our service may be relevant.
            </p>

            <p style="margin: 10px 0;">
                To stop receiving emails from us, reply with "STOP" or
                <a href="{unsubscribe_link}" style="color: #0066cc;">click here to unsubscribe</a>.
            </p>

            <p style="margin: 10px 0; font-size: 11px; color: #999;">
                This is informational content only and does not constitute legal advice.
                For legal advice, please consult with a licensed attorney.
            </p>
        </div>
        """

        # Insert before closing body tag or append
        if '</body>' in body_html.lower():
            # Find the position case-insensitively
            lower_body = body_html.lower()
            pos = lower_body.rfind('</body>')
            return body_html[:pos] + footer + body_html[pos:]

        return body_html + footer

    def generate_unsubscribe_url(
        self,
        email: str,
        email_send_id: Optional[int] = None,
        token: Optional[str] = None
    ) -> str:
        """
        Generate unsubscribe URL for an email.

        Args:
            email: Recipient email
            email_send_id: Optional email send ID for tracking
            token: Optional security token

        Returns:
            Unsubscribe URL
        """
        import urllib.parse

        base_url = f"{self.tracking_domain}/unsubscribe"
        params = {"email": email}

        if email_send_id:
            params["id"] = str(email_send_id)
        if token:
            params["token"] = token

        return f"{base_url}?{urllib.parse.urlencode(params)}"

    def validate_email_content(self, body_html: str) -> List[str]:
        """
        Additional content validation beyond CAN-SPAM.

        Args:
            body_html: Email HTML content

        Returns:
            List of issues found
        """
        issues = []

        if not body_html:
            issues.append("Email body is empty")
            return issues

        # Check for broken template variables
        template_pattern = r'\{\{[^}]*\}\}'
        if re.search(template_pattern, body_html):
            # This is fine if intentional, but warn
            pass

        # Check for excessive capitalization
        text_only = re.sub(r'<[^>]+>', '', body_html)
        if text_only:
            caps_ratio = sum(1 for c in text_only if c.isupper()) / len(text_only)
            if caps_ratio > 0.3:
                issues.append("Email has excessive capitalization (may trigger spam filters)")

        # Check for spam trigger words
        spam_triggers = [
            'free', 'winner', 'cash', 'prize', 'guarantee',
            'no obligation', 'risk free', 'act now', 'limited time'
        ]
        body_lower = body_html.lower()
        found_triggers = [t for t in spam_triggers if t in body_lower]
        if len(found_triggers) > 2:
            issues.append(f"Email contains multiple spam trigger words: {found_triggers[:3]}")

        return issues
