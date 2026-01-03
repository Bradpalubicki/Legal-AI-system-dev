"""
Email Notification Service
Sends email notifications for case deadlines and reminders
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending email notifications"""

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        """
        Initialize notification service

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: From email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.enabled = bool(smtp_user and smtp_password)

        if not self.enabled:
            logger.warning("Email notifications disabled - SMTP credentials not configured")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Send an email notification

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body (fallback)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email notification skipped (disabled): {subject} to {to_email}")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Add text and HTML parts
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)

            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully: {subject} to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def send_deadline_reminder(
        self,
        to_email: str,
        case_name: str,
        case_id: str,
        event_title: str,
        event_date: datetime,
        event_location: Optional[str] = None,
        days_until: int = 0
    ) -> bool:
        """
        Send a deadline reminder email

        Args:
            to_email: Recipient email address
            case_name: Name of the case
            case_id: Case ID
            event_title: Event/deadline title
            event_date: Event date/time
            event_location: Event location (if any)
            days_until: Days until deadline

        Returns:
            True if sent successfully
        """
        # Format date
        formatted_date = event_date.strftime("%B %d, %Y at %I:%M %p")

        # Determine urgency
        if days_until == 0:
            urgency = "TODAY"
            urgency_color = "#dc2626"  # red
        elif days_until == 1:
            urgency = "TOMORROW"
            urgency_color = "#ea580c"  # orange
        elif days_until <= 7:
            urgency = f"in {days_until} days"
            urgency_color = "#f59e0b"  # amber
        else:
            urgency = f"in {days_until} days"
            urgency_color = "#3b82f6"  # blue

        subject = f"⚖️ Reminder: {event_title} {urgency}"

        # HTML email body
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 8px 8px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e5e7eb;
                    border-top: none;
                }}
                .urgency {{
                    display: inline-block;
                    background: {urgency_color};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 14px;
                    margin: 10px 0;
                }}
                .detail {{
                    margin: 15px 0;
                    padding: 15px;
                    background: #f9fafb;
                    border-left: 4px solid #667eea;
                    border-radius: 4px;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #6b7280;
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .detail-value {{
                    color: #1f2937;
                    font-size: 16px;
                    margin-top: 4px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 12px;
                }}
                .button {{
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 24px;">⚖️ Legal Case Reminder</h1>
                </div>
                <div class="content">
                    <div class="urgency">{urgency.upper()}</div>

                    <div class="detail">
                        <div class="detail-label">Event</div>
                        <div class="detail-value">{event_title}</div>
                    </div>

                    <div class="detail">
                        <div class="detail-label">Case</div>
                        <div class="detail-value">{case_name}</div>
                    </div>

                    <div class="detail">
                        <div class="detail-label">Date & Time</div>
                        <div class="detail-value">{formatted_date}</div>
                    </div>

                    {f'''
                    <div class="detail">
                        <div class="detail-label">Location</div>
                        <div class="detail-value">{event_location}</div>
                    </div>
                    ''' if event_location else ''}

                    <div style="text-align: center;">
                        <a href="http://localhost:3000/cases/{case_id}" class="button">
                            View Case Details
                        </a>
                    </div>

                    <div class="footer">
                        <p>This is an automated reminder from Legal AI System.</p>
                        <p>Manage your notification preferences in your account settings.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text fallback
        body_text = f"""
        Legal Case Reminder - {urgency.upper()}

        Event: {event_title}
        Case: {case_name}
        Date & Time: {formatted_date}
        {f"Location: {event_location}" if event_location else ""}

        View case details: http://localhost:3000/cases/{case_id}

        This is an automated reminder from Legal AI System.
        """

        return self.send_email(to_email, subject, body_html, body_text)

    def send_deadline_digest(
        self,
        to_email: str,
        upcoming_deadlines: List[Dict[str, Any]]
    ) -> bool:
        """
        Send a daily/weekly digest of upcoming deadlines

        Args:
            to_email: Recipient email address
            upcoming_deadlines: List of deadline dictionaries

        Returns:
            True if sent successfully
        """
        if not upcoming_deadlines:
            logger.info("No upcoming deadlines for digest")
            return False

        subject = f"📅 Legal Case Digest - {len(upcoming_deadlines)} Upcoming Deadlines"

        # Generate deadline rows HTML
        deadline_rows = ""
        for deadline in upcoming_deadlines:
            event_date = deadline['event_date']
            days_until = (event_date - datetime.now()).days

            if days_until <= 1:
                urgency_color = "#dc2626"
            elif days_until <= 7:
                urgency_color = "#f59e0b"
            else:
                urgency_color = "#3b82f6"

            deadline_rows += f"""
            <div style="padding: 15px; margin: 10px 0; background: #f9fafb; border-left: 4px solid {urgency_color}; border-radius: 4px;">
                <div style="font-weight: 600; font-size: 16px; color: #1f2937;">{deadline['event_title']}</div>
                <div style="color: #6b7280; font-size: 14px; margin-top: 4px;">{deadline['case_name']}</div>
                <div style="color: #6b7280; font-size: 14px;">{event_date.strftime("%B %d, %Y at %I:%M %p")} ({days_until} days)</div>
            </div>
            """

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 8px 8px 0 0;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 24px;">📅 Upcoming Deadlines Digest</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{len(upcoming_deadlines)} deadlines in the next 14 days</p>
                </div>
                <div style="background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
                    {deadline_rows}

                    <div style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:3000/dashboard" style="display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">
                            View Dashboard
                        </a>
                    </div>

                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px;">
                        <p>This is an automated digest from Legal AI System.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, body_html)

    def get_upcoming_deadlines(
        self,
        db: Session,
        days_ahead: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming deadlines from database

        Args:
            db: Database session
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming deadline dictionaries
        """
        from ...models.case_management import CaseTimelineEvent as TimelineEvent, LegalCase as Case

        try:
            cutoff_date = datetime.now() + timedelta(days=days_ahead)

            events = db.query(TimelineEvent).join(Case).filter(
                TimelineEvent.status == 'scheduled',
                TimelineEvent.event_date >= datetime.now(),
                TimelineEvent.event_date <= cutoff_date
            ).order_by(TimelineEvent.event_date).all()

            deadlines = []
            for event in events:
                case = db.query(Case).filter(Case.id == event.case_id).first()
                if case:
                    deadlines.append({
                        'event_id': event.id,
                        'event_title': event.title,
                        'event_date': event.event_date,
                        'event_location': event.location,
                        'case_id': case.id,
                        'case_name': case.case_name
                    })

            return deadlines

        except Exception as e:
            logger.error(f"Error fetching upcoming deadlines: {str(e)}")
            return []


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create notification service instance"""
    global _notification_service

    if _notification_service is None:
        import os
        _notification_service = NotificationService(
            smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_user=os.getenv('SMTP_USER'),
            smtp_password=os.getenv('SMTP_PASSWORD'),
            from_email=os.getenv('SMTP_FROM_EMAIL')
        )

    return _notification_service
