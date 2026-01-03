"""
Filing Monitor Service

Monitors CourtListener for new filings and extracts contacts.
Runs as a scheduled background task via Celery.
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.marketing.courtlistener.client import CourtListenerClient
from app.marketing.courtlistener.extractors import ContactExtractor, ExtractedContact
from app.marketing.contacts.models import Contact, ContactCase, ContactSource
from app.marketing.analytics.models import MonitorStatus

logger = logging.getLogger(__name__)


class FilingMonitor:
    """
    Monitors CourtListener for new filings and extracts contacts.

    Designed to run as a scheduled background task. Polls CourtListener
    for recent dockets, extracts attorney/party contacts, and stores
    them in the database for marketing campaigns.
    """

    # Default nature of suit codes to target
    DEFAULT_NATURE_OF_SUITS = [
        "440",  # Other Civil Rights
        "442",  # Employment
        "445",  # Americans with Disabilities
        "710",  # Fair Labor Standards Act
        "720",  # Labor/Management Relations
        "790",  # Other Labor Litigation
        "830",  # Patent
        "840",  # Trademark
        "850",  # Securities/Commodities
        "890",  # Other Statutory Actions
    ]

    def __init__(self, db: Session):
        """
        Initialize the filing monitor.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.client = CourtListenerClient()
        self.extractor = ContactExtractor()

        # Configuration from environment
        self.poll_interval_minutes = int(os.getenv('FILING_MONITOR_POLL_INTERVAL', '30'))
        self.lookback_hours = int(os.getenv('FILING_MONITOR_LOOKBACK_HOURS', '24'))

        # Target filters
        nos_env = os.getenv('TARGET_NATURE_OF_SUITS', '')
        self.target_nature_of_suits = (
            [n.strip() for n in nos_env.split(',') if n.strip()]
            or self.DEFAULT_NATURE_OF_SUITS
        )

        courts_env = os.getenv('TARGET_COURTS', '')
        self.target_courts = (
            [c.strip() for c in courts_env.split(',') if c.strip()]
            or None  # None = all courts
        )

    async def poll_for_new_filings(self) -> Dict[str, int]:
        """
        Poll CourtListener for new filings and process them.

        Returns:
            Statistics dict with counts of processed items
        """
        stats = {
            "dockets_found": 0,
            "dockets_processed": 0,
            "contacts_created": 0,
            "contacts_updated": 0,
            "cases_linked": 0,
            "errors": 0
        }

        logger.info(f"Polling for filings in last {self.lookback_hours} hours")

        # Update monitor status
        status = self._get_or_create_monitor_status()
        status.last_poll_started_at = datetime.utcnow()
        status.lookback_hours = self.lookback_hours
        status.target_courts = self.target_courts
        status.target_nature_of_suits = self.target_nature_of_suits
        self.db.commit()

        try:
            # Get recent dockets
            dockets = await self.client.get_recent_dockets(
                hours_back=self.lookback_hours,
                courts=self.target_courts,
                nature_of_suits=self.target_nature_of_suits,
                max_results=500  # Reasonable limit per poll
            )

            stats["dockets_found"] = len(dockets)
            logger.info(f"Found {len(dockets)} recent dockets")

            # Process each docket
            for docket in dockets:
                try:
                    result = await self._process_docket(docket)
                    stats["dockets_processed"] += 1
                    stats["contacts_created"] += result.get("contacts_created", 0)
                    stats["contacts_updated"] += result.get("contacts_updated", 0)
                    stats["cases_linked"] += result.get("cases_linked", 0)
                except Exception as e:
                    logger.error(f"Error processing docket {docket.get('id')}: {e}")
                    stats["errors"] += 1

            # Update monitor status with success
            status.last_poll_completed_at = datetime.utcnow()
            status.last_poll_status = "success" if stats["errors"] == 0 else "partial"
            status.dockets_found = stats["dockets_found"]
            status.dockets_processed = stats["dockets_processed"]
            status.contacts_created = stats["contacts_created"]
            status.contacts_updated = stats["contacts_updated"]
            status.cases_linked = stats["cases_linked"]

            # Track rate limit status
            rate_status = self.client.get_rate_limit_status()
            status.rate_limit_remaining = rate_status.get("remaining")

        except Exception as e:
            logger.error(f"Error in filing monitor: {e}", exc_info=True)
            status.last_poll_completed_at = datetime.utcnow()
            status.last_poll_status = "error"
            status.last_poll_error = str(e)
            raise

        finally:
            self.db.commit()

        logger.info(
            f"Polling complete: {stats['dockets_processed']} dockets, "
            f"{stats['contacts_created']} new contacts"
        )

        return stats

    async def _process_docket(self, docket: Dict[str, Any]) -> Dict[str, int]:
        """
        Process a single docket and extract contacts.

        Args:
            docket: Docket record from CourtListener

        Returns:
            Statistics dict for this docket
        """
        result = {
            "contacts_created": 0,
            "contacts_updated": 0,
            "cases_linked": 0
        }

        docket_id = docket.get("id")

        # Get attorneys for this docket
        try:
            attorneys = await self.client.get_attorneys_for_docket(docket_id)
        except Exception as e:
            logger.warning(f"Could not get attorneys for docket {docket_id}: {e}")
            attorneys = []

        # Get parties (may require special access)
        try:
            parties = await self.client.get_parties_for_docket(docket_id)
        except Exception as e:
            logger.debug(f"Could not get parties for docket {docket_id}: {e}")
            parties = []

        # Extract all contacts
        extracted_contacts = self.extractor.extract_all_from_docket(
            docket, attorneys, parties
        )

        # Save contacts
        for extracted in extracted_contacts:
            if extracted.email:  # Only save contacts with email
                saved, is_new = self._save_contact(extracted, docket)
                if saved:
                    if is_new:
                        result["contacts_created"] += 1
                    else:
                        result["contacts_updated"] += 1

                    # Link to case
                    if self._link_contact_to_case(saved, docket, extracted.role):
                        result["cases_linked"] += 1

        return result

    def _save_contact(
        self,
        extracted: ExtractedContact,
        docket: Dict[str, Any]
    ) -> tuple[Optional[Contact], bool]:
        """
        Save or update a contact in the database.

        Args:
            extracted: Extracted contact data
            docket: Source docket data

        Returns:
            Tuple of (Contact, is_new)
        """
        if not extracted.email:
            return None, False

        # Check for existing contact
        existing = self.db.query(Contact).filter(
            Contact.email == extracted.email.lower()
        ).first()

        if existing:
            # Update existing contact with any new information
            if not existing.phone and extracted.phone:
                existing.phone = extracted.phone
            if not existing.firm_name and extracted.firm_name:
                existing.firm_name = extracted.firm_name
            if not existing.address_line1 and extracted.address_line1:
                existing.address_line1 = extracted.address_line1
            if not existing.city and extracted.city:
                existing.city = extracted.city
            if not existing.state and extracted.state:
                existing.state = extracted.state
            if not existing.zip_code and extracted.zip_code:
                existing.zip_code = extracted.zip_code

            existing.updated_at = datetime.utcnow()
            self.db.commit()

            logger.debug(f"Updated existing contact: {extracted.email}")
            return existing, False

        # Create new contact
        contact = Contact(
            email=extracted.email.lower(),
            first_name=extracted.first_name,
            last_name=extracted.last_name,
            full_name=extracted.full_name,
            contact_type=extracted.contact_type,
            source=ContactSource.COURTLISTENER,
            firm_name=extracted.firm_name,
            phone=extracted.phone,
            fax=extracted.fax,
            address_line1=extracted.address_line1,
            address_line2=extracted.address_line2,
            city=extracted.city,
            state=extracted.state,
            zip_code=extracted.zip_code,
            courtlistener_attorney_id=extracted.courtlistener_attorney_id,
            courtlistener_party_id=extracted.courtlistener_party_id,
            raw_contact_data=extracted.raw_data,
            is_subscribed=True
        )

        self.db.add(contact)
        self.db.commit()

        logger.info(f"Created new contact: {extracted.email}")
        return contact, True

    def _link_contact_to_case(
        self,
        contact: Contact,
        docket: Dict[str, Any],
        role: str
    ) -> bool:
        """
        Link a contact to a case.

        Args:
            contact: Contact to link
            docket: Docket data
            role: Contact's role in the case

        Returns:
            True if new link created, False if already existed
        """
        docket_id = docket.get("id")

        # Check if already linked
        existing = self.db.query(ContactCase).filter(
            ContactCase.contact_id == contact.id,
            ContactCase.courtlistener_docket_id == docket_id
        ).first()

        if existing:
            return False

        # Parse date_filed
        date_filed = None
        if docket.get("date_filed"):
            try:
                date_filed = datetime.fromisoformat(
                    docket["date_filed"].replace('Z', '+00:00')
                )
            except (ValueError, TypeError):
                pass

        # Create new link
        case_link = ContactCase(
            contact_id=contact.id,
            courtlistener_docket_id=docket_id,
            case_number=docket.get("docket_number"),
            case_name=docket.get("case_name"),
            court=docket.get("court_id") or docket.get("court"),
            role=role,
            nature_of_suit=docket.get("nature_of_suit"),
            date_filed=date_filed
        )

        self.db.add(case_link)
        self.db.commit()

        return True

    def _get_or_create_monitor_status(self) -> MonitorStatus:
        """Get or create the monitor status record."""
        status = self.db.query(MonitorStatus).first()
        if not status:
            status = MonitorStatus()
            self.db.add(status)
            self.db.commit()
        return status

    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitor status.

        Returns:
            Status information dict
        """
        status = self.db.query(MonitorStatus).first()
        if not status:
            return {"status": "never_run"}

        return {
            "last_poll_started": status.last_poll_started_at.isoformat() if status.last_poll_started_at else None,
            "last_poll_completed": status.last_poll_completed_at.isoformat() if status.last_poll_completed_at else None,
            "last_status": status.last_poll_status,
            "last_error": status.last_poll_error,
            "dockets_found": status.dockets_found,
            "dockets_processed": status.dockets_processed,
            "contacts_created": status.contacts_created,
            "rate_limit_remaining": status.rate_limit_remaining,
            "config": {
                "lookback_hours": self.lookback_hours,
                "poll_interval_minutes": self.poll_interval_minutes,
                "target_courts": self.target_courts,
                "target_nature_of_suits": self.target_nature_of_suits
            }
        }
