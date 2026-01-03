"""
Marketing Analytics Service

Calculates metrics, generates reports, and tracks funnel performance.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.marketing.analytics.models import (
    MarketingEvent, DailyMetrics, CampaignMetricsSnapshot, Conversion
)
from app.marketing.contacts.models import Contact, ContactCase
from app.marketing.campaigns.models import Campaign, EmailSend, CampaignStatus
from app.marketing.newsletter.models import NewsletterSubscriber

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for marketing analytics and reporting."""

    def __init__(self, db: Session):
        self.db = db

    # ============ Dashboard Metrics ============

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics.

        Returns overview of contacts, campaigns, emails, and conversions.
        """
        # Contact metrics
        total_contacts = self.db.query(func.count(Contact.id)).scalar() or 0
        contacts_with_email = self.db.query(func.count(Contact.id)).filter(
            Contact.email.isnot(None)
        ).scalar() or 0
        subscribed_contacts = self.db.query(func.count(Contact.id)).filter(
            Contact.is_subscribed == True
        ).scalar() or 0

        # New contacts this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_contacts_week = self.db.query(func.count(Contact.id)).filter(
            Contact.created_at >= week_ago
        ).scalar() or 0

        # Campaign metrics
        active_campaigns = self.db.query(func.count(Campaign.id)).filter(
            Campaign.status == CampaignStatus.ACTIVE
        ).scalar() or 0

        # Email metrics
        total_sent = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.sent_at.isnot(None)
        ).scalar() or 0
        total_opened = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.opened_at.isnot(None)
        ).scalar() or 0
        total_clicked = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.clicked_at.isnot(None)
        ).scalar() or 0

        # Calculate rates
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0

        # Newsletter metrics
        newsletter_subscribers = self.db.query(func.count(NewsletterSubscriber.id)).filter(
            NewsletterSubscriber.is_active == True,
            NewsletterSubscriber.is_confirmed == True
        ).scalar() or 0

        # Conversion metrics
        total_conversions = self.db.query(func.count(Conversion.id)).scalar() or 0
        conversions_week = self.db.query(func.count(Conversion.id)).filter(
            Conversion.converted_at >= week_ago
        ).scalar() or 0

        return {
            "contacts": {
                "total": total_contacts,
                "with_email": contacts_with_email,
                "subscribed": subscribed_contacts,
                "new_this_week": new_contacts_week
            },
            "campaigns": {
                "active": active_campaigns
            },
            "emails": {
                "total_sent": total_sent,
                "total_opened": total_opened,
                "total_clicked": total_clicked,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2)
            },
            "newsletter": {
                "subscribers": newsletter_subscribers
            },
            "conversions": {
                "total": total_conversions,
                "this_week": conversions_week
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_funnel_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get conversion funnel metrics.

        Tracks: Contacts -> Emails Sent -> Opened -> Clicked -> Converted
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Funnel stages
        contacts_created = self.db.query(func.count(Contact.id)).filter(
            Contact.created_at >= start_date
        ).scalar() or 0

        emails_sent = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.sent_at >= start_date
        ).scalar() or 0

        emails_delivered = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.delivered_at >= start_date
        ).scalar() or 0

        emails_opened = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.opened_at >= start_date
        ).scalar() or 0

        emails_clicked = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.clicked_at >= start_date
        ).scalar() or 0

        conversions = self.db.query(func.count(Conversion.id)).filter(
            Conversion.converted_at >= start_date
        ).scalar() or 0

        # Calculate conversion rates between stages
        delivery_rate = (emails_delivered / emails_sent * 100) if emails_sent > 0 else 0
        open_rate = (emails_opened / emails_delivered * 100) if emails_delivered > 0 else 0
        click_rate = (emails_clicked / emails_opened * 100) if emails_opened > 0 else 0
        conversion_rate = (conversions / emails_clicked * 100) if emails_clicked > 0 else 0

        return {
            "period_days": days,
            "funnel": {
                "contacts_created": contacts_created,
                "emails_sent": emails_sent,
                "emails_delivered": emails_delivered,
                "emails_opened": emails_opened,
                "emails_clicked": emails_clicked,
                "conversions": conversions
            },
            "rates": {
                "delivery_rate": round(delivery_rate, 2),
                "open_rate": round(open_rate, 2),
                "click_to_open_rate": round(click_rate, 2),
                "conversion_rate": round(conversion_rate, 2),
                "overall_conversion": round(
                    (conversions / contacts_created * 100) if contacts_created > 0 else 0, 2
                )
            }
        }

    # ============ Daily Metrics ============

    def calculate_daily_metrics(self, for_date: Optional[date] = None) -> DailyMetrics:
        """
        Calculate and store daily metrics.

        Args:
            for_date: Date to calculate for (defaults to yesterday)

        Returns:
            DailyMetrics record
        """
        if for_date is None:
            for_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info(f"Calculating daily metrics for {for_date}")

        start = datetime.combine(for_date, datetime.min.time())
        end = datetime.combine(for_date, datetime.max.time())

        # Check if already calculated
        existing = self.db.query(DailyMetrics).filter(
            DailyMetrics.date == for_date
        ).first()

        if existing:
            metrics = existing
        else:
            metrics = DailyMetrics(date=for_date)
            self.db.add(metrics)

        # Contact metrics
        metrics.new_contacts = self.db.query(func.count(Contact.id)).filter(
            Contact.created_at.between(start, end)
        ).scalar() or 0

        metrics.total_contacts = self.db.query(func.count(Contact.id)).filter(
            Contact.created_at <= end
        ).scalar() or 0

        metrics.contacts_with_email = self.db.query(func.count(Contact.id)).filter(
            Contact.created_at <= end,
            Contact.email.isnot(None)
        ).scalar() or 0

        # Email metrics
        metrics.emails_sent = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.sent_at.between(start, end)
        ).scalar() or 0

        metrics.emails_delivered = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.delivered_at.between(start, end)
        ).scalar() or 0

        metrics.emails_opened = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.opened_at.between(start, end)
        ).scalar() or 0

        metrics.emails_clicked = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.clicked_at.between(start, end)
        ).scalar() or 0

        metrics.emails_bounced = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.bounce_type.isnot(None),
            EmailSend.created_at.between(start, end)
        ).scalar() or 0

        metrics.emails_unsubscribed = self.db.query(func.count(EmailSend.id)).filter(
            EmailSend.unsubscribed_at.between(start, end)
        ).scalar() or 0

        # Calculate rates
        if metrics.emails_sent > 0:
            metrics.delivery_rate = (metrics.emails_delivered / metrics.emails_sent) * 100
            metrics.bounce_rate = (metrics.emails_bounced / metrics.emails_sent) * 100

        if metrics.emails_delivered > 0:
            metrics.open_rate = (metrics.emails_opened / metrics.emails_delivered) * 100
            metrics.click_rate = (metrics.emails_clicked / metrics.emails_delivered) * 100
            metrics.unsubscribe_rate = (metrics.emails_unsubscribed / metrics.emails_delivered) * 100

        # Newsletter metrics
        metrics.newsletter_subscribers = self.db.query(func.count(NewsletterSubscriber.id)).filter(
            NewsletterSubscriber.created_at <= end,
            NewsletterSubscriber.is_active == True
        ).scalar() or 0

        # CourtListener metrics
        metrics.dockets_processed = self.db.query(func.count(ContactCase.id)).filter(
            ContactCase.created_at.between(start, end)
        ).scalar() or 0

        # Conversion metrics
        metrics.conversions = self.db.query(func.count(Conversion.id)).filter(
            Conversion.converted_at.between(start, end)
        ).scalar() or 0

        metrics.conversion_revenue = self.db.query(
            func.sum(Conversion.revenue)
        ).filter(
            Conversion.converted_at.between(start, end)
        ).scalar() or 0.0

        # Active campaigns
        metrics.active_campaigns = self.db.query(func.count(Campaign.id)).filter(
            Campaign.status == CampaignStatus.ACTIVE
        ).scalar() or 0

        metrics.calculated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Daily metrics calculated: {metrics.emails_sent} emails, {metrics.new_contacts} new contacts")
        return metrics

    def get_metrics_history(
        self,
        days: int = 30
    ) -> List[DailyMetrics]:
        """Get daily metrics history."""
        start_date = (datetime.utcnow() - timedelta(days=days)).date()

        return self.db.query(DailyMetrics).filter(
            DailyMetrics.date >= start_date
        ).order_by(DailyMetrics.date.desc()).all()

    # ============ Campaign Analytics ============

    def get_campaign_performance(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """Get detailed campaign performance analytics."""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()

        if not campaign:
            return {}

        # Get sends
        sends = self.db.query(EmailSend).filter(
            EmailSend.campaign_id == campaign_id
        )

        total_sends = sends.count()
        delivered = sends.filter(EmailSend.delivered_at.isnot(None)).count()
        opened = sends.filter(EmailSend.opened_at.isnot(None)).count()
        clicked = sends.filter(EmailSend.clicked_at.isnot(None)).count()

        # Daily breakdown
        daily_sends = self.db.query(
            func.date(EmailSend.sent_at).label('date'),
            func.count(EmailSend.id).label('count')
        ).filter(
            EmailSend.campaign_id == campaign_id,
            EmailSend.sent_at.isnot(None)
        ).group_by(func.date(EmailSend.sent_at)).all()

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status.value,
            "totals": {
                "sent": total_sends,
                "delivered": delivered,
                "opened": opened,
                "clicked": clicked
            },
            "rates": {
                "delivery_rate": round((delivered / total_sends * 100) if total_sends > 0 else 0, 2),
                "open_rate": round((opened / delivered * 100) if delivered > 0 else 0, 2),
                "click_rate": round((clicked / delivered * 100) if delivered > 0 else 0, 2)
            },
            "daily_sends": [
                {"date": str(d.date), "count": d.count}
                for d in daily_sends
            ]
        }

    # ============ Event Tracking ============

    def log_event(
        self,
        event_type: str,
        email: Optional[str] = None,
        contact_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> MarketingEvent:
        """Log a marketing event."""
        event = MarketingEvent(
            event_type=event_type,
            email=email,
            contact_id=contact_id,
            campaign_id=campaign_id,
            event_metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(event)
        self.db.commit()

        return event

    def get_recent_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[MarketingEvent]:
        """Get recent marketing events."""
        query = self.db.query(MarketingEvent)

        if event_type:
            query = query.filter(MarketingEvent.event_type == event_type)

        return query.order_by(
            MarketingEvent.event_timestamp.desc()
        ).limit(limit).all()

    # ============ Conversion Tracking ============

    def track_conversion(
        self,
        email: str,
        conversion_type: str,
        revenue: float = 0.0,
        campaign_id: Optional[int] = None,
        email_send_id: Optional[int] = None,
        landing_token: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversion:
        """Track a conversion event."""
        # Find contact
        contact = self.db.query(Contact).filter(
            Contact.email == email.lower()
        ).first()

        conversion = Conversion(
            contact_id=contact.id if contact else None,
            email=email.lower(),
            user_id=user_id,
            conversion_type=conversion_type,
            revenue=revenue,
            attributed_campaign_id=campaign_id,
            attributed_email_send_id=email_send_id,
            landing_token=landing_token,
            conversion_data=metadata,
            converted_at=datetime.utcnow()
        )

        # Calculate days to convert
        if contact:
            conversion.first_touch_at = contact.created_at
            conversion.days_to_convert = (datetime.utcnow() - contact.created_at).days

        self.db.add(conversion)
        self.db.commit()
        self.db.refresh(conversion)

        # Update campaign metrics if attributed
        if campaign_id:
            campaign = self.db.query(Campaign).filter(
                Campaign.id == campaign_id
            ).first()
            if campaign:
                campaign.total_converted = (campaign.total_converted or 0) + 1
                self.db.commit()

        logger.info(f"Tracked conversion: {email} - {conversion_type}")
        return conversion
