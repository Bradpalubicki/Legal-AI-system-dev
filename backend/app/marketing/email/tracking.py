"""
Email Tracking

Handles open and click tracking for marketing emails.
Provides endpoints and services for tracking pixel and link redirects.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import unquote

from sqlalchemy.orm import Session

from app.marketing.campaigns.models import EmailSend, Campaign
from app.marketing.contacts.models import Contact
from app.marketing.contacts.service import ContactService
from app.marketing.analytics.models import MarketingEvent

logger = logging.getLogger(__name__)


class EmailTracker:
    """
    Service for tracking email engagement.

    Handles open tracking (via pixel), click tracking (via redirects),
    and event logging.
    """

    def __init__(self, db: Session):
        self.db = db
        self.contact_service = ContactService(db)

    def track_open(
        self,
        email_send_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Track email open event.

        Args:
            email_send_id: EmailSend ID from tracking pixel URL
            ip_address: Requester IP address
            user_agent: Browser user agent

        Returns:
            True if tracked successfully
        """
        email_send = self.db.query(EmailSend).filter(
            EmailSend.id == email_send_id
        ).first()

        if not email_send:
            logger.warning(f"Email send {email_send_id} not found for open tracking")
            return False

        # Update email send
        email_send.open_count = (email_send.open_count or 0) + 1

        if not email_send.opened_at:
            # First open
            email_send.opened_at = datetime.utcnow()

            # Update campaign metrics
            if email_send.campaign_id:
                campaign = self.db.query(Campaign).filter(
                    Campaign.id == email_send.campaign_id
                ).first()
                if campaign:
                    campaign.total_opened = (campaign.total_opened or 0) + 1

            # Update contact engagement
            if email_send.contact_id:
                self.contact_service.update_engagement(
                    email_send.contact_id, "open"
                )

        # Log event
        self._log_event(
            event_type="email_opened",
            email_send_id=email_send_id,
            contact_id=email_send.contact_id,
            campaign_id=email_send.campaign_id,
            email=email_send.to_email,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.commit()

        logger.debug(f"Tracked open for email {email_send_id}")
        return True

    def track_click(
        self,
        email_send_id: int,
        url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """
        Track email link click and return redirect URL.

        Args:
            email_send_id: EmailSend ID from tracking link
            url: Original URL (may be URL encoded)
            ip_address: Requester IP address
            user_agent: Browser user agent

        Returns:
            URL to redirect to, or None if invalid
        """
        email_send = self.db.query(EmailSend).filter(
            EmailSend.id == email_send_id
        ).first()

        if not email_send:
            logger.warning(f"Email send {email_send_id} not found for click tracking")
            return None

        # Decode URL if needed
        redirect_url = unquote(url)

        # Update email send
        email_send.click_count = (email_send.click_count or 0) + 1

        if not email_send.clicked_at:
            # First click
            email_send.clicked_at = datetime.utcnow()

            # Update campaign metrics
            if email_send.campaign_id:
                campaign = self.db.query(Campaign).filter(
                    Campaign.id == email_send.campaign_id
                ).first()
                if campaign:
                    campaign.total_clicked = (campaign.total_clicked or 0) + 1

            # Update contact engagement
            if email_send.contact_id:
                self.contact_service.update_engagement(
                    email_send.contact_id, "click"
                )

        # Track clicked links
        clicked_links = email_send.clicked_links or []
        if redirect_url not in clicked_links:
            clicked_links.append(redirect_url)
            email_send.clicked_links = clicked_links

        # Log event
        self._log_event(
            event_type="email_clicked",
            email_send_id=email_send_id,
            contact_id=email_send.contact_id,
            campaign_id=email_send.campaign_id,
            email=email_send.to_email,
            link_url=redirect_url,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.commit()

        logger.debug(f"Tracked click for email {email_send_id}: {redirect_url}")
        return redirect_url

    def track_unsubscribe(
        self,
        email_send_id: Optional[int] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Track unsubscribe event and opt out contact.

        Args:
            email_send_id: EmailSend ID if from tracked email
            email: Email address to unsubscribe
            ip_address: Requester IP address
            user_agent: Browser user agent

        Returns:
            True if unsubscribed successfully
        """
        contact_id = None
        campaign_id = None

        if email_send_id:
            email_send = self.db.query(EmailSend).filter(
                EmailSend.id == email_send_id
            ).first()

            if email_send:
                email_send.unsubscribed_at = datetime.utcnow()
                contact_id = email_send.contact_id
                campaign_id = email_send.campaign_id
                email = email_send.to_email

                # Update campaign metrics
                if campaign_id:
                    campaign = self.db.query(Campaign).filter(
                        Campaign.id == campaign_id
                    ).first()
                    if campaign:
                        campaign.total_unsubscribed = (campaign.total_unsubscribed or 0) + 1

        # Opt out the contact
        if email:
            self.contact_service.opt_out_by_email(
                email,
                reason="Unsubscribed via email link"
            )

            # Log event
            self._log_event(
                event_type="unsubscribe",
                email_send_id=email_send_id,
                contact_id=contact_id,
                campaign_id=campaign_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent
            )

            self.db.commit()

            logger.info(f"Unsubscribed: {email}")
            return True

        return False

    def track_bounce(
        self,
        email_send_id: int,
        bounce_type: str,
        bounce_reason: Optional[str] = None
    ) -> bool:
        """
        Track email bounce.

        Args:
            email_send_id: EmailSend ID
            bounce_type: 'hard' or 'soft'
            bounce_reason: Reason from email provider

        Returns:
            True if tracked successfully
        """
        email_send = self.db.query(EmailSend).filter(
            EmailSend.id == email_send_id
        ).first()

        if not email_send:
            return False

        email_send.bounce_type = bounce_type
        email_send.bounce_reason = bounce_reason
        email_send.status = "bounced"

        # Update campaign metrics
        if email_send.campaign_id:
            campaign = self.db.query(Campaign).filter(
                Campaign.id == email_send.campaign_id
            ).first()
            if campaign:
                campaign.total_bounced = (campaign.total_bounced or 0) + 1

        # For hard bounces, add to suppression list
        if bounce_type == "hard":
            self.contact_service.add_to_suppression_list(
                email=email_send.to_email,
                reason="hard_bounce",
                details=bounce_reason,
                source="email_tracking"
            )

        # Log event
        self._log_event(
            event_type="email_bounced",
            email_send_id=email_send_id,
            contact_id=email_send.contact_id,
            campaign_id=email_send.campaign_id,
            email=email_send.to_email,
            metadata={"bounce_type": bounce_type, "reason": bounce_reason}
        )

        self.db.commit()

        logger.info(f"Tracked {bounce_type} bounce for {email_send.to_email}")
        return True

    def track_spam_report(
        self,
        email_send_id: int
    ) -> bool:
        """
        Track spam report.

        Args:
            email_send_id: EmailSend ID

        Returns:
            True if tracked successfully
        """
        email_send = self.db.query(EmailSend).filter(
            EmailSend.id == email_send_id
        ).first()

        if not email_send:
            return False

        email_send.spam_reported_at = datetime.utcnow()

        # Update campaign metrics
        if email_send.campaign_id:
            campaign = self.db.query(Campaign).filter(
                Campaign.id == email_send.campaign_id
            ).first()
            if campaign:
                campaign.total_spam_reports = (campaign.total_spam_reports or 0) + 1

        # Add to suppression list
        self.contact_service.add_to_suppression_list(
            email=email_send.to_email,
            reason="spam_complaint",
            source="email_tracking"
        )

        # Log event
        self._log_event(
            event_type="spam_report",
            email_send_id=email_send_id,
            contact_id=email_send.contact_id,
            campaign_id=email_send.campaign_id,
            email=email_send.to_email
        )

        self.db.commit()

        logger.warning(f"Spam report for {email_send.to_email}")
        return True

    def track_conversion(
        self,
        email_send_id: int,
        conversion_type: str = "signup",
        revenue: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track conversion event.

        Args:
            email_send_id: EmailSend ID
            conversion_type: Type of conversion
            revenue: Revenue amount if applicable
            metadata: Additional conversion data

        Returns:
            True if tracked successfully
        """
        email_send = self.db.query(EmailSend).filter(
            EmailSend.id == email_send_id
        ).first()

        if not email_send:
            return False

        email_send.converted_at = datetime.utcnow()

        # Update campaign metrics
        if email_send.campaign_id:
            campaign = self.db.query(Campaign).filter(
                Campaign.id == email_send.campaign_id
            ).first()
            if campaign:
                campaign.total_converted = (campaign.total_converted or 0) + 1

        # Update contact engagement
        if email_send.contact_id:
            self.contact_service.update_engagement(
                email_send.contact_id, "convert"
            )

        # Log event
        self._log_event(
            event_type="conversion",
            email_send_id=email_send_id,
            contact_id=email_send.contact_id,
            campaign_id=email_send.campaign_id,
            email=email_send.to_email,
            metadata={
                "conversion_type": conversion_type,
                "revenue": revenue,
                **(metadata or {})
            }
        )

        self.db.commit()

        logger.info(f"Tracked conversion for {email_send.to_email}: {conversion_type}")
        return True

    def _log_event(
        self,
        event_type: str,
        email_send_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        email: Optional[str] = None,
        link_url: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MarketingEvent:
        """Log a marketing event."""
        event = MarketingEvent(
            event_type=event_type,
            email_send_id=email_send_id,
            contact_id=contact_id,
            campaign_id=campaign_id,
            email=email,
            link_url=link_url,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=metadata
        )

        self.db.add(event)
        return event

    def get_email_send_by_token(self, token: str) -> Optional[EmailSend]:
        """Get email send by landing token."""
        return self.db.query(EmailSend).filter(
            EmailSend.landing_token == token
        ).first()
