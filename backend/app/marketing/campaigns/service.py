"""
Campaign Management Service

CRUD operations and business logic for marketing campaigns.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.marketing.campaigns.models import (
    Campaign, EmailSequence, EmailSend, EmailTemplate,
    CampaignStatus, CampaignType
)
from app.marketing.contacts.models import Contact, ContactType
from app.marketing.contacts.service import ContactService

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing marketing campaigns."""

    def __init__(self, db: Session):
        self.db = db
        self.contact_service = ContactService(db)

    # ============ Campaign CRUD ============

    def create_campaign(
        self,
        name: str,
        campaign_type: CampaignType,
        description: Optional[str] = None,
        target_contact_types: Optional[List[str]] = None,
        target_case_types: Optional[List[str]] = None,
        target_courts: Optional[List[str]] = None,
        target_states: Optional[List[str]] = None,
        daily_send_limit: int = 100,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        created_by_user_id: Optional[str] = None
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            campaign_type: Type of campaign
            Various targeting and configuration options

        Returns:
            Created Campaign object
        """
        campaign = Campaign(
            name=name,
            description=description,
            campaign_type=campaign_type,
            status=CampaignStatus.DRAFT,
            target_contact_types=target_contact_types,
            target_case_types=target_case_types,
            target_courts=target_courts,
            target_states=target_states,
            daily_send_limit=daily_send_limit,
            from_email=from_email,
            from_name=from_name,
            created_by_user_id=created_by_user_id
        )

        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Created campaign: {name} (ID: {campaign.id})")
        return campaign

    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Get campaign by ID."""
        return self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

    def list_campaigns(
        self,
        status: Optional[str] = None,
        campaign_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Campaign]:
        """List campaigns with optional filters."""
        query = self.db.query(Campaign)

        if status:
            try:
                st = CampaignStatus(status)
                query = query.filter(Campaign.status == st)
            except ValueError:
                pass

        if campaign_type:
            try:
                ct = CampaignType(campaign_type)
                query = query.filter(Campaign.campaign_type == ct)
            except ValueError:
                pass

        return query.order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()

    def update_campaign(
        self,
        campaign_id: int,
        **updates
    ) -> Optional[Campaign]:
        """Update campaign fields."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return None

        # Don't allow updates to active campaigns (except pause/resume)
        if campaign.status == CampaignStatus.ACTIVE and 'status' not in updates:
            raise ValueError("Cannot modify active campaign. Pause it first.")

        for field, value in updates.items():
            if hasattr(campaign, field):
                setattr(campaign, field, value)

        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(campaign)

        return campaign

    def delete_campaign(self, campaign_id: int) -> bool:
        """Delete a campaign (only if draft or completed)."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return False

        if campaign.status == CampaignStatus.ACTIVE:
            raise ValueError("Cannot delete active campaign. Pause or complete it first.")

        self.db.delete(campaign)
        self.db.commit()

        logger.info(f"Deleted campaign: {campaign.name}")
        return True

    # ============ Campaign Lifecycle ============

    def activate_campaign(self, campaign_id: int) -> Campaign:
        """
        Activate a campaign and start sending.

        Args:
            campaign_id: Campaign to activate

        Returns:
            Activated campaign

        Raises:
            ValueError: If campaign can't be activated
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
            raise ValueError(f"Cannot activate campaign in {campaign.status} status")

        # Verify campaign has at least one sequence
        sequences = self.db.query(EmailSequence).filter(
            EmailSequence.campaign_id == campaign_id,
            EmailSequence.is_active == True
        ).count()

        if sequences == 0:
            raise ValueError("Campaign must have at least one email sequence")

        campaign.status = CampaignStatus.ACTIVE
        campaign.activated_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Activated campaign: {campaign.name}")
        return campaign

    def pause_campaign(self, campaign_id: int) -> Campaign:
        """Pause a running campaign."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.status != CampaignStatus.ACTIVE:
            raise ValueError("Campaign is not active")

        campaign.status = CampaignStatus.PAUSED
        campaign.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Paused campaign: {campaign.name}")
        return campaign

    def complete_campaign(self, campaign_id: int) -> Campaign:
        """Mark a campaign as completed."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Completed campaign: {campaign.name}")
        return campaign

    # ============ Email Sequences ============

    def add_sequence(
        self,
        campaign_id: int,
        subject_line: str,
        body_html: str,
        sequence_order: Optional[int] = None,
        delay_days: int = 0,
        delay_hours: int = 0,
        body_text: Optional[str] = None,
        personalization_prompt: Optional[str] = None,
        use_ai_personalization: bool = True
    ) -> EmailSequence:
        """
        Add an email sequence to a campaign.

        Args:
            campaign_id: Campaign to add to
            subject_line: Email subject
            body_html: HTML body content
            sequence_order: Order in sequence (auto-calculated if not provided)
            delay_days/hours: Delay from previous email
            Various content options

        Returns:
            Created EmailSequence
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.status == CampaignStatus.ACTIVE:
            raise ValueError("Cannot modify active campaign")

        # Auto-calculate sequence order
        if sequence_order is None:
            max_order = self.db.query(func.max(EmailSequence.sequence_order)).filter(
                EmailSequence.campaign_id == campaign_id
            ).scalar() or 0
            sequence_order = max_order + 1

        sequence = EmailSequence(
            campaign_id=campaign_id,
            sequence_order=sequence_order,
            delay_days=delay_days,
            delay_hours=delay_hours,
            subject_line=subject_line,
            body_html=body_html,
            body_text=body_text,
            personalization_prompt=personalization_prompt,
            use_ai_personalization=use_ai_personalization
        )

        self.db.add(sequence)
        self.db.commit()
        self.db.refresh(sequence)

        return sequence

    def get_sequences(self, campaign_id: int) -> List[EmailSequence]:
        """Get all sequences for a campaign in order."""
        return self.db.query(EmailSequence).filter(
            EmailSequence.campaign_id == campaign_id
        ).order_by(EmailSequence.sequence_order).all()

    # ============ Email Queue Management ============

    def queue_campaign_emails(self, campaign_id: int) -> int:
        """
        Queue initial emails for campaign targets.

        Args:
            campaign_id: Campaign to queue emails for

        Returns:
            Number of emails queued
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign or campaign.status != CampaignStatus.ACTIVE:
            return 0

        # Get first sequence
        first_sequence = self.db.query(EmailSequence).filter(
            EmailSequence.campaign_id == campaign_id,
            EmailSequence.is_active == True
        ).order_by(EmailSequence.sequence_order).first()

        if not first_sequence:
            return 0

        # Get target contacts
        contacts = self._get_target_contacts(campaign)

        queued = 0
        for contact in contacts:
            # Check if already in this campaign
            existing = self.db.query(EmailSend).filter(
                EmailSend.campaign_id == campaign_id,
                EmailSend.contact_id == contact.id
            ).first()

            if existing:
                continue

            # Create email send record
            email_send = self._create_email_send(
                campaign, first_sequence, contact
            )
            if email_send:
                queued += 1

        self.db.commit()

        logger.info(f"Queued {queued} emails for campaign {campaign_id}")
        return queued

    def get_queued_emails(
        self,
        limit: int = 50,
        campaign_id: Optional[int] = None
    ) -> List[EmailSend]:
        """
        Get emails ready to send.

        Args:
            limit: Max emails to return
            campaign_id: Optional filter by campaign

        Returns:
            List of EmailSend records ready to send
        """
        query = self.db.query(EmailSend).filter(
            EmailSend.status == "queued",
            or_(
                EmailSend.scheduled_for.is_(None),
                EmailSend.scheduled_for <= datetime.utcnow()
            )
        )

        if campaign_id:
            query = query.filter(EmailSend.campaign_id == campaign_id)

        # Join with campaign to check status
        query = query.join(Campaign).filter(
            Campaign.status == CampaignStatus.ACTIVE
        )

        return query.order_by(EmailSend.created_at).limit(limit).all()

    def _get_target_contacts(
        self,
        campaign: Campaign,
        limit: int = 1000
    ) -> List[Contact]:
        """Get contacts matching campaign targeting criteria."""
        query = self.db.query(Contact).filter(
            Contact.is_subscribed == True,
            Contact.email.isnot(None)
        )

        # Filter by contact types
        if campaign.target_contact_types:
            types = [ContactType(t) for t in campaign.target_contact_types if t]
            if types:
                query = query.filter(Contact.contact_type.in_(types))

        # Filter by states
        if campaign.target_states:
            query = query.filter(Contact.state.in_(campaign.target_states))

        # Respect daily limit
        daily_limit = campaign.daily_send_limit or 100

        # Check how many already sent today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.campaign_id == campaign.id,
            EmailSend.sent_at >= today_start
        ).scalar() or 0

        remaining_limit = max(0, daily_limit - sent_today)

        return query.limit(min(limit, remaining_limit)).all()

    def _create_email_send(
        self,
        campaign: Campaign,
        sequence: EmailSequence,
        contact: Contact
    ) -> Optional[EmailSend]:
        """Create an email send record."""
        # Generate landing token for zero-friction landing
        landing_token = secrets.token_urlsafe(32)

        # Get the latest case for this contact (for personalization)
        latest_case = None
        if contact.cases:
            latest_case = max(contact.cases, key=lambda c: c.created_at, default=None)

        email_send = EmailSend(
            campaign_id=campaign.id,
            sequence_id=sequence.id,
            contact_id=contact.id,
            to_email=contact.email,
            from_email=campaign.from_email or "alerts@courtcase-search.com",
            from_name=campaign.from_name or "CourtCase-Search",
            subject_line=sequence.subject_line,
            body_html=sequence.body_html,
            body_text=sequence.body_text,
            status="queued",
            landing_token=landing_token,
            related_case_id=latest_case.id if latest_case else None,
            personalization_data={
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "full_name": contact.full_name or contact.display_name,
                "firm_name": contact.firm_name,
                "case_name": latest_case.case_name if latest_case else None,
                "case_number": latest_case.case_number if latest_case else None,
                "court": latest_case.court if latest_case else None
            }
        )

        self.db.add(email_send)
        return email_send

    # ============ Campaign Statistics ============

    def get_campaign_stats(self, campaign_id: int) -> Dict[str, Any]:
        """Get comprehensive campaign statistics."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return {}

        # Calculate rates
        delivery_rate = (
            (campaign.total_delivered / campaign.total_sent * 100)
            if campaign.total_sent > 0 else 0
        )

        open_rate = (
            (campaign.total_opened / campaign.total_delivered * 100)
            if campaign.total_delivered > 0 else 0
        )

        click_rate = (
            (campaign.total_clicked / campaign.total_delivered * 100)
            if campaign.total_delivered > 0 else 0
        )

        conversion_rate = (
            (campaign.total_converted / campaign.total_delivered * 100)
            if campaign.total_delivered > 0 else 0
        )

        # Get sequence stats
        sequences = self.get_sequences(campaign_id)
        sequence_stats = []
        for seq in sequences:
            seq_open_rate = (seq.total_opened / seq.total_sent * 100) if seq.total_sent > 0 else 0
            sequence_stats.append({
                "sequence_order": seq.sequence_order,
                "subject": seq.subject_line,
                "sent": seq.total_sent,
                "opened": seq.total_opened,
                "clicked": seq.total_clicked,
                "open_rate": seq_open_rate
            })

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status.value,
            "metrics": {
                "total_sent": campaign.total_sent,
                "total_delivered": campaign.total_delivered,
                "total_opened": campaign.total_opened,
                "total_clicked": campaign.total_clicked,
                "total_replied": campaign.total_replied,
                "total_converted": campaign.total_converted,
                "total_unsubscribed": campaign.total_unsubscribed,
                "total_bounced": campaign.total_bounced
            },
            "rates": {
                "delivery_rate": round(delivery_rate, 2),
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "conversion_rate": round(conversion_rate, 2)
            },
            "sequences": sequence_stats,
            "created_at": campaign.created_at.isoformat(),
            "activated_at": campaign.activated_at.isoformat() if campaign.activated_at else None
        }

    def update_campaign_metrics(self, campaign_id: int) -> None:
        """Recalculate and update campaign metrics from email sends."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return

        sends = self.db.query(EmailSend).filter(
            EmailSend.campaign_id == campaign_id
        )

        campaign.total_sent = sends.filter(EmailSend.sent_at.isnot(None)).count()
        campaign.total_delivered = sends.filter(EmailSend.delivered_at.isnot(None)).count()
        campaign.total_opened = sends.filter(EmailSend.opened_at.isnot(None)).count()
        campaign.total_clicked = sends.filter(EmailSend.clicked_at.isnot(None)).count()
        campaign.total_replied = sends.filter(EmailSend.replied_at.isnot(None)).count()
        campaign.total_converted = sends.filter(EmailSend.converted_at.isnot(None)).count()
        campaign.total_unsubscribed = sends.filter(EmailSend.unsubscribed_at.isnot(None)).count()
        campaign.total_bounced = sends.filter(EmailSend.bounce_type.isnot(None)).count()

        campaign.updated_at = datetime.utcnow()
        self.db.commit()
