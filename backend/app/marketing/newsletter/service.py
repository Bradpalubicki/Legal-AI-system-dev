"""
Newsletter Service

Manages newsletter subscribers and editions.
Generates weekly digest content using AI.
"""

import os
import logging
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.marketing.newsletter.models import (
    NewsletterSubscriber, NewsletterEdition, NewsletterSend
)
from app.marketing.contacts.models import Contact, ContactCase
from app.marketing.email.sender import EmailSender
from app.marketing.email.compliance import CANSPAMCompliance

logger = logging.getLogger(__name__)


class NewsletterService:
    """Service for managing newsletters."""

    def __init__(self, db: Session):
        self.db = db
        self.sender = EmailSender()
        self.compliance = CANSPAMCompliance()

    # ============ Subscriber Management ============

    def subscribe(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        source: str = "website",
        interests: Optional[List[str]] = None,
        jurisdictions: Optional[List[str]] = None
    ) -> NewsletterSubscriber:
        """
        Subscribe a new email to the newsletter.

        Uses double opt-in - sends confirmation email.
        """
        email = email.lower().strip()

        # Check existing
        existing = self.get_subscriber_by_email(email)
        if existing:
            if existing.is_active and existing.is_confirmed:
                return existing
            # Reactivate if unsubscribed
            existing.is_active = True
            existing.unsubscribed_at = None
            self.db.commit()
            return existing

        # Create new subscriber
        subscriber = NewsletterSubscriber(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
            source=source,
            interests=interests or [],
            jurisdictions=jurisdictions or [],
            is_confirmed=False,
            confirmation_token=secrets.token_urlsafe(32)
        )

        self.db.add(subscriber)
        self.db.commit()
        self.db.refresh(subscriber)

        # Send confirmation email (double opt-in)
        self._send_confirmation_email(subscriber)

        logger.info(f"New newsletter subscriber: {email}")
        return subscriber

    def confirm_subscription(self, token: str) -> bool:
        """Confirm a subscription via token."""
        subscriber = self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.confirmation_token == token
        ).first()

        if not subscriber:
            return False

        subscriber.is_confirmed = True
        subscriber.confirmed_at = datetime.utcnow()
        subscriber.confirmation_token = None
        self.db.commit()

        logger.info(f"Subscription confirmed: {subscriber.email}")
        return True

    def unsubscribe(
        self,
        email: str,
        reason: Optional[str] = None
    ) -> bool:
        """Unsubscribe from newsletter."""
        subscriber = self.get_subscriber_by_email(email)
        if not subscriber:
            return False

        subscriber.is_active = False
        subscriber.unsubscribed_at = datetime.utcnow()
        subscriber.unsubscribe_reason = reason
        self.db.commit()

        logger.info(f"Newsletter unsubscribed: {email}")
        return True

    def get_subscriber_by_email(self, email: str) -> Optional[NewsletterSubscriber]:
        """Get subscriber by email."""
        return self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email.lower().strip()
        ).first()

    def list_subscribers(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_confirmed: Optional[bool] = None
    ) -> List[NewsletterSubscriber]:
        """List newsletter subscribers."""
        query = self.db.query(NewsletterSubscriber)

        if is_active is not None:
            query = query.filter(NewsletterSubscriber.is_active == is_active)

        if is_confirmed is not None:
            query = query.filter(NewsletterSubscriber.is_confirmed == is_confirmed)

        return query.order_by(
            NewsletterSubscriber.created_at.desc()
        ).offset(skip).limit(limit).all()

    def get_active_subscribers(self) -> List[NewsletterSubscriber]:
        """Get all active, confirmed subscribers."""
        return self.db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.is_active == True,
            NewsletterSubscriber.is_confirmed == True
        ).all()

    # ============ Newsletter Editions ============

    def generate_weekly_digest(self) -> Optional[NewsletterEdition]:
        """
        Generate weekly newsletter content.

        Pulls recent cases, analyzes trends, and creates
        AI-generated insights.
        """
        logger.info("Generating weekly newsletter digest")

        # Get next edition number
        last_edition = self.db.query(NewsletterEdition).order_by(
            NewsletterEdition.edition_number.desc()
        ).first()
        edition_number = (last_edition.edition_number or 0) + 1 if last_edition else 1

        # Get recent cases from last week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        recent_cases = self.db.query(ContactCase).filter(
            ContactCase.created_at >= one_week_ago
        ).order_by(ContactCase.date_filed.desc()).limit(20).all()

        # Build featured cases list
        featured_cases = []
        for case in recent_cases[:5]:
            featured_cases.append({
                "case_name": case.case_name,
                "case_number": case.case_number,
                "court": case.court,
                "nature_of_suit": case.nature_of_suit,
                "date_filed": case.date_filed.isoformat() if case.date_filed else None
            })

        # Create edition
        edition = NewsletterEdition(
            edition_number=edition_number,
            edition_date=datetime.utcnow(),
            subject_line=f"CourtCase-Search Weekly: {len(recent_cases)} New Cases This Week",
            featured_cases=featured_cases,
            notable_filings=featured_cases,  # Same for now
            cases_analyzed=len(recent_cases),
            status="draft",
            target_frequency="weekly"
        )

        # Generate body HTML
        edition.body_html = self._generate_newsletter_html(edition, recent_cases)
        edition.body_text = self._generate_newsletter_text(edition, recent_cases)

        # Generate AI insights if available
        try:
            insights = asyncio.run(self._generate_ai_insights(recent_cases))
            edition.insights = insights
        except Exception as e:
            logger.warning(f"Could not generate AI insights: {e}")
            edition.insights = ""

        edition.generation_completed_at = datetime.utcnow()
        edition.status = "scheduled"
        edition.scheduled_for = datetime.utcnow() + timedelta(hours=12)

        self.db.add(edition)
        self.db.commit()
        self.db.refresh(edition)

        logger.info(f"Generated newsletter edition {edition_number}")
        return edition

    async def send_latest_edition(self) -> Dict[str, int]:
        """Send the latest scheduled newsletter edition."""
        stats = {"sent": 0, "failed": 0, "skipped": 0}

        # Get latest scheduled edition
        edition = self.db.query(NewsletterEdition).filter(
            NewsletterEdition.status == "scheduled"
        ).order_by(NewsletterEdition.edition_date.desc()).first()

        if not edition:
            logger.info("No scheduled newsletter edition to send")
            return stats

        # Get active subscribers
        subscribers = self.get_active_subscribers()

        if not subscribers:
            logger.info("No active subscribers for newsletter")
            return stats

        edition.status = "sending"
        self.db.commit()

        for subscriber in subscribers:
            try:
                success = await self._send_newsletter_to_subscriber(edition, subscriber)
                if success:
                    stats["sent"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"Error sending newsletter to {subscriber.email}: {e}")
                stats["failed"] += 1

        # Update edition stats
        edition.status = "sent"
        edition.sent_at = datetime.utcnow()
        edition.total_sent = stats["sent"]

        self.db.commit()

        logger.info(f"Newsletter edition {edition.id} sent: {stats}")
        return stats

    async def _send_newsletter_to_subscriber(
        self,
        edition: NewsletterEdition,
        subscriber: NewsletterSubscriber
    ) -> bool:
        """Send newsletter to a single subscriber."""
        # Create send record
        send = NewsletterSend(
            edition_id=edition.id,
            subscriber_id=subscriber.id,
            to_email=subscriber.email,
            status="queued"
        )
        self.db.add(send)
        self.db.commit()

        # Generate unsubscribe URL
        unsubscribe_url = self.compliance.generate_unsubscribe_url(
            email=subscriber.email
        )

        # Add compliance footer
        body_html = self.compliance.add_compliance_footer(
            edition.body_html,
            unsubscribe_url=unsubscribe_url
        )

        # Send via email sender
        try:
            result = await self.sender.send_test_email(
                to_email=subscriber.email,
                subject=edition.subject_line,
                body=body_html
            )

            send.status = "sent"
            send.sent_at = datetime.utcnow()
            send.email_provider_id = result.get("message_id")

            subscriber.emails_received = (subscriber.emails_received or 0) + 1
            subscriber.updated_at = datetime.utcnow()

            self.db.commit()
            return True

        except Exception as e:
            send.status = "failed"
            self.db.commit()
            raise

    def list_editions(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> List[NewsletterEdition]:
        """List newsletter editions."""
        return self.db.query(NewsletterEdition).order_by(
            NewsletterEdition.edition_date.desc()
        ).offset(skip).limit(limit).all()

    # ============ Helper Methods ============

    def _send_confirmation_email(self, subscriber: NewsletterSubscriber) -> None:
        """Send double opt-in confirmation email."""
        # This would send a confirmation email
        # For now, auto-confirm in development
        if os.getenv('ENVIRONMENT') == 'development':
            subscriber.is_confirmed = True
            subscriber.confirmed_at = datetime.utcnow()
            self.db.commit()

    def _generate_newsletter_html(
        self,
        edition: NewsletterEdition,
        cases: List[ContactCase]
    ) -> str:
        """Generate newsletter HTML content."""
        cases_html = ""
        for case in cases[:10]:
            cases_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <strong>{case.case_name or 'Unnamed Case'}</strong><br>
                    <span style="color: #666; font-size: 12px;">
                        {case.court or 'Unknown Court'} |
                        {case.nature_of_suit or 'Unknown Type'} |
                        Filed: {case.date_filed.strftime('%Y-%m-%d') if case.date_filed else 'Unknown'}
                    </span>
                </td>
            </tr>
            """

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #333; margin: 0;">CourtCase-Search</h1>
        <p style="color: #666;">Weekly Legal Filing Digest</p>
    </div>

    <div style="background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
        <h2 style="color: #333; margin-top: 0;">This Week's Highlights</h2>
        <p>We tracked <strong>{len(cases)}</strong> new court filings this week.</p>
        {edition.insights or ''}
    </div>

    <h3 style="color: #333;">Recent Filings</h3>
    <table style="width: 100%; border-collapse: collapse;">
        {cases_html}
    </table>

    <div style="margin-top: 30px; padding: 20px; background: #0066cc; color: white; text-align: center; border-radius: 5px;">
        <h3 style="margin: 0 0 10px 0;">Want Real-Time Alerts?</h3>
        <p style="margin: 0 0 15px 0;">Get instant notifications when cases matching your criteria are filed.</p>
        <a href="https://courtcase-search.com/signup" style="display: inline-block; background: white; color: #0066cc; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
            Start Free Trial
        </a>
    </div>
</body>
</html>
        """

    def _generate_newsletter_text(
        self,
        edition: NewsletterEdition,
        cases: List[ContactCase]
    ) -> str:
        """Generate plain text newsletter content."""
        cases_text = "\n".join([
            f"- {c.case_name or 'Unnamed'} | {c.court or 'Unknown Court'}"
            for c in cases[:10]
        ])

        return f"""
CourtCase-Search Weekly Digest
===============================

This Week's Highlights
----------------------
We tracked {len(cases)} new court filings this week.

{edition.insights or ''}

Recent Filings
--------------
{cases_text}

---
Want real-time alerts? Visit https://courtcase-search.com/signup

To unsubscribe, visit: {{{{unsubscribe_url}}}}
        """

    async def _generate_ai_insights(
        self,
        cases: List[ContactCase]
    ) -> str:
        """Generate AI-powered insights about this week's filings."""
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_key:
            return ""

        # Summarize case types
        case_types = {}
        for case in cases:
            nos = case.nature_of_suit or "Other"
            case_types[nos] = case_types.get(nos, 0) + 1

        case_summary = "\n".join([f"- {k}: {v} cases" for k, v in case_types.items()])

        prompt = f"""Based on this week's court filings, write 2-3 sentences of insights for legal professionals.

Filing Summary:
{case_summary}

Total: {len(cases)} cases

Be factual, concise, and professional. Focus on trends or notable patterns."""

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            response = await client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()

        except Exception as e:
            logger.warning(f"Error generating AI insights: {e}")
            return ""
