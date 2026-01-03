"""
Case Notification Service
Sends notifications to users monitoring cases
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from app.models.case_access import CaseAccess, CaseMonitoringEvent, CaseAccessStatus
from shared.database.models import TrackedDocket


class CaseNotificationService:
    """Service for sending case monitoring notifications"""

    def __init__(self, db: Session):
        self.db = db
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "notifications@legalai.com")

    def notify_case_update(
        self,
        case_id: int,
        event_type: str,
        event_title: str,
        event_description: str,
        event_data: Optional[dict] = None
    ):
        """
        Send notification to all users monitoring a case

        Args:
            case_id: Case that was updated
            event_type: Type of update (new_filing, status_change, etc.)
            event_title: Short title for the event
            event_description: Detailed description
            event_data: Additional data (JSON)
        """
        # Get all active case accesses for this case
        case_accesses = self.db.query(CaseAccess).filter(
            CaseAccess.case_id == case_id,
            CaseAccess.status == CaseAccessStatus.ACTIVE,
            CaseAccess.notifications_enabled == True
        ).all()

        if not case_accesses:
            return 0  # No one to notify

        # Get case details
        case = self.db.query(TrackedDocket).filter(TrackedDocket.id == case_id).first()
        if not case:
            return 0

        notifications_sent = 0

        for access in case_accesses:
            # Only notify if access is still active
            if not access.is_active():
                continue

            # Create event record
            event = CaseMonitoringEvent(
                case_access_id=access.id,
                case_id=case_id,
                user_id=access.user_id,
                event_type=event_type,
                event_title=event_title,
                event_description=event_description,
                event_data=str(event_data) if event_data else None,
                event_date=datetime.utcnow()
            )
            self.db.add(event)

            # Send email notification
            if self._send_email_notification(
                access=access,
                case=case,
                event=event
            ):
                event.notified = True
                event.notified_at = datetime.utcnow()
                event.notification_sent_to = access.notification_email
                notifications_sent += 1

        self.db.commit()
        return notifications_sent

    def _send_email_notification(
        self,
        access: CaseAccess,
        case: TrackedDocket,
        event: CaseMonitoringEvent
    ) -> bool:
        """Send email notification for a case event"""
        try:
            # Prepare email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Case Update: {case.case_name}"
            msg['From'] = self.from_email
            msg['To'] = access.notification_email

            # Create email body
            html = self._create_email_html(access, case, event)
            text = self._create_email_text(access, case, event)

            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))

            # Send email
            if self.smtp_username and self.smtp_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                return True
            else:
                print(f"[DEV MODE] Would send email to {access.notification_email}")
                print(f"Subject: {msg['Subject']}")
                print(f"Body: {text}")
                return True  # Consider sent in dev mode

        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False

    def _create_email_html(
        self,
        access: CaseAccess,
        case: TrackedDocket,
        event: CaseMonitoringEvent
    ) -> str:
        """Create HTML email body"""
        case_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/cases/{case.id}"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .event {{ background: white; padding: 20px; border-radius: 8px;
                         border-left: 4px solid #667eea; margin: 20px 0; }}
                .button {{ background: #667eea; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Case Update Notification</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">
                        {case.case_name}
                    </p>
                </div>

                <div class="content">
                    <div class="event">
                        <h2 style="margin-top: 0; color: #667eea;">{event.event_title}</h2>
                        <p>{event.event_description}</p>
                        <p style="color: #666; font-size: 14px;">
                            <strong>Case Number:</strong> {case.docket_number}<br>
                            <strong>Court:</strong> {case.court_id}<br>
                            <strong>Event Time:</strong> {event.event_date.strftime('%B %d, %Y at %I:%M %p')}
                        </p>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{case_url}" class="button">
                            View Case Details →
                        </a>
                    </div>

                    <div style="background: #fff; padding: 15px; border-radius: 6px; margin-top: 20px;">
                        <p style="margin: 0; font-size: 14px; color: #666;">
                            <strong>💡 Tip:</strong> You can manage your notification preferences
                            and access all case documents in your dashboard.
                        </p>
                    </div>
                </div>

                <div class="footer">
                    <p>
                        You're receiving this because you're monitoring this case.<br>
                        <a href="{case_url}/settings" style="color: #667eea;">
                            Manage notification settings
                        </a>
                    </p>
                    <p style="margin-top: 20px;">
                        © 2025 Legal AI System. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_email_text(
        self,
        access: CaseAccess,
        case: TrackedDocket,
        event: CaseMonitoringEvent
    ) -> str:
        """Create plain text email body"""
        case_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/cases/{case.id}"

        return f"""
Case Update Notification
{'=' * 50}

{event.event_title}

{event.event_description}

Case Details:
- Case Name: {case.case_name}
- Case Number: {case.docket_number}
- Court: {case.court_id}
- Event Time: {event.event_date.strftime('%B %d, %Y at %I:%M %p')}

View full case details: {case_url}

---
You're receiving this because you're monitoring this case.
Manage notification settings: {case_url}/settings

© 2025 Legal AI System
        """

    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[CaseMonitoringEvent]:
        """Get notification history for a user"""
        query = self.db.query(CaseMonitoringEvent).filter(
            CaseMonitoringEvent.user_id == user_id
        )

        if unread_only:
            query = query.filter(CaseMonitoringEvent.notified == False)

        return query.order_by(
            CaseMonitoringEvent.event_date.desc()
        ).limit(limit).all()

    def mark_notifications_read(self, event_ids: List[int], user_id: int):
        """Mark notifications as read"""
        self.db.query(CaseMonitoringEvent).filter(
            CaseMonitoringEvent.id.in_(event_ids),
            CaseMonitoringEvent.user_id == user_id
        ).update(
            {"notified": True, "notified_at": datetime.utcnow()},
            synchronize_session=False
        )
        self.db.commit()


# Example usage:
# service = CaseNotificationService(db)
# service.notify_case_update(
#     case_id=123,
#     event_type="new_filing",
#     event_title="New Motion Filed",
#     event_description="Defendant filed Motion to Dismiss",
#     event_data={"document_id": 456}
# )
