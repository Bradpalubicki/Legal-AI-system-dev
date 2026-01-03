"""
Contact Management Service

CRUD operations and business logic for marketing contacts.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.marketing.contacts.models import (
    Contact, ContactCase, ContactType, ContactSource,
    ContactSuppressionList
)

logger = logging.getLogger(__name__)


class ContactService:
    """Service for managing marketing contacts."""

    def __init__(self, db: Session):
        self.db = db

    # ============ CRUD Operations ============

    def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
        contact_type: ContactType = ContactType.OTHER,
        source: ContactSource = ContactSource.MANUAL,
        firm_name: Optional[str] = None,
        phone: Optional[str] = None,
        fax: Optional[str] = None,
        address_line1: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        courtlistener_attorney_id: Optional[int] = None,
        raw_contact_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Contact:
        """
        Create a new contact.

        Args:
            email: Contact email (required, unique)
            Various optional fields

        Returns:
            Created Contact object

        Raises:
            ValueError: If email already exists or is suppressed
        """
        email = email.lower().strip()

        # Check if suppressed
        if self.is_suppressed(email):
            raise ValueError(f"Email {email} is on suppression list")

        # Check for existing
        existing = self.get_by_email(email)
        if existing:
            raise ValueError(f"Contact with email {email} already exists")

        contact = Contact(
            email=email,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name or f"{first_name or ''} {last_name or ''}".strip(),
            contact_type=contact_type,
            source=source,
            firm_name=firm_name,
            phone=phone,
            fax=fax,
            address_line1=address_line1,
            city=city,
            state=state,
            zip_code=zip_code,
            courtlistener_attorney_id=courtlistener_attorney_id,
            raw_contact_data=raw_contact_data,
            tags=tags or [],
            is_subscribed=True
        )

        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)

        logger.info(f"Created contact: {email}")
        return contact

    def get_by_id(self, contact_id: int) -> Optional[Contact]:
        """Get contact by ID."""
        return self.db.query(Contact).filter(Contact.id == contact_id).first()

    def get_by_email(self, email: str) -> Optional[Contact]:
        """Get contact by email."""
        return self.db.query(Contact).filter(
            Contact.email == email.lower().strip()
        ).first()

    def get_contact_with_cases(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get contact with all associated cases."""
        contact = self.get_by_id(contact_id)
        if not contact:
            return None

        cases = self.db.query(ContactCase).filter(
            ContactCase.contact_id == contact_id
        ).all()

        return {
            "contact": contact,
            "cases": cases,
            "case_count": len(cases)
        }

    def update_contact(
        self,
        contact_id: int,
        **updates
    ) -> Optional[Contact]:
        """
        Update contact fields.

        Args:
            contact_id: Contact to update
            **updates: Fields to update

        Returns:
            Updated contact or None if not found
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return None

        # Apply updates
        for field, value in updates.items():
            if hasattr(contact, field):
                setattr(contact, field, value)

        contact.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(contact)

        return contact

    def delete_contact(self, contact_id: int) -> bool:
        """
        Delete a contact and all associated data.

        Args:
            contact_id: Contact to delete

        Returns:
            True if deleted, False if not found
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return False

        self.db.delete(contact)
        self.db.commit()

        logger.info(f"Deleted contact: {contact.email}")
        return True

    # ============ List & Search ============

    def list_contacts(
        self,
        skip: int = 0,
        limit: int = 100,
        contact_type: Optional[str] = None,
        has_email: bool = True,
        is_subscribed: Optional[bool] = None,
        source: Optional[str] = None,
        state: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        order_by: str = "-created_at"
    ) -> List[Contact]:
        """
        List contacts with filters.

        Args:
            skip: Offset for pagination
            limit: Max results
            contact_type: Filter by type
            has_email: Only contacts with email
            is_subscribed: Filter by subscription status
            source: Filter by source
            state: Filter by state
            tags: Filter by tags (any match)
            search: Search in name/email
            order_by: Sort field (prefix with - for desc)

        Returns:
            List of matching contacts
        """
        query = self.db.query(Contact)

        # Apply filters
        if has_email:
            query = query.filter(Contact.email.isnot(None))

        if contact_type:
            try:
                ct = ContactType(contact_type)
                query = query.filter(Contact.contact_type == ct)
            except ValueError:
                pass

        if is_subscribed is not None:
            query = query.filter(Contact.is_subscribed == is_subscribed)

        if source:
            try:
                src = ContactSource(source)
                query = query.filter(Contact.source == src)
            except ValueError:
                pass

        if state:
            query = query.filter(Contact.state == state.upper())

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Contact.email.ilike(search_term),
                    Contact.full_name.ilike(search_term),
                    Contact.firm_name.ilike(search_term)
                )
            )

        # Apply ordering
        if order_by.startswith("-"):
            field = getattr(Contact, order_by[1:], Contact.created_at)
            query = query.order_by(field.desc())
        else:
            field = getattr(Contact, order_by, Contact.created_at)
            query = query.order_by(field.asc())

        return query.offset(skip).limit(limit).all()

    def count_contacts(
        self,
        is_subscribed: Optional[bool] = None,
        contact_type: Optional[str] = None
    ) -> int:
        """Count contacts with optional filters."""
        query = self.db.query(func.count(Contact.id))

        if is_subscribed is not None:
            query = query.filter(Contact.is_subscribed == is_subscribed)

        if contact_type:
            try:
                ct = ContactType(contact_type)
                query = query.filter(Contact.contact_type == ct)
            except ValueError:
                pass

        return query.scalar() or 0

    # ============ Opt-out & Compliance ============

    def opt_out(
        self,
        contact_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Opt out a contact from marketing emails.

        Args:
            contact_id: Contact to opt out
            reason: Optional reason for opt-out

        Returns:
            True if successful
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return False

        contact.is_subscribed = False
        contact.opted_out_at = datetime.utcnow()
        contact.opt_out_reason = reason
        contact.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Contact opted out: {contact.email}")
        return True

    def opt_out_by_email(
        self,
        email: str,
        reason: Optional[str] = None
    ) -> bool:
        """Opt out a contact by email address."""
        contact = self.get_by_email(email)
        if contact:
            return self.opt_out(contact.id, reason)
        return False

    def resubscribe(self, contact_id: int) -> bool:
        """Resubscribe an opted-out contact."""
        contact = self.get_by_id(contact_id)
        if not contact:
            return False

        contact.is_subscribed = True
        contact.opted_out_at = None
        contact.opt_out_reason = None
        contact.updated_at = datetime.utcnow()

        self.db.commit()
        return True

    def process_pending_opt_outs(self) -> int:
        """
        Process any pending opt-out requests.

        CAN-SPAM requires honoring opt-outs within 10 business days.
        This processes them immediately.

        Returns:
            Count of processed opt-outs
        """
        # In this implementation, opt-outs are processed immediately
        # This method exists for any batch processing needs
        return 0

    # ============ Suppression List ============

    def is_suppressed(self, email: str) -> bool:
        """Check if email is on suppression list."""
        return self.db.query(ContactSuppressionList).filter(
            ContactSuppressionList.email == email.lower().strip()
        ).first() is not None

    def add_to_suppression_list(
        self,
        email: str,
        reason: str,
        details: Optional[str] = None,
        source: Optional[str] = None
    ) -> ContactSuppressionList:
        """
        Add email to global suppression list.

        Args:
            email: Email to suppress
            reason: Reason code (hard_bounce, spam_complaint, manual, legal)
            details: Additional details
            source: Source of suppression

        Returns:
            Created suppression record
        """
        email = email.lower().strip()

        # Check if already suppressed
        existing = self.db.query(ContactSuppressionList).filter(
            ContactSuppressionList.email == email
        ).first()

        if existing:
            return existing

        suppression = ContactSuppressionList(
            email=email,
            reason=reason,
            details=details,
            source=source
        )

        self.db.add(suppression)

        # Also opt out any matching contact
        contact = self.get_by_email(email)
        if contact:
            contact.is_subscribed = False
            contact.opted_out_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Added to suppression list: {email} ({reason})")
        return suppression

    def remove_from_suppression_list(self, email: str) -> bool:
        """Remove email from suppression list."""
        suppression = self.db.query(ContactSuppressionList).filter(
            ContactSuppressionList.email == email.lower().strip()
        ).first()

        if suppression:
            self.db.delete(suppression)
            self.db.commit()
            return True

        return False

    # ============ Engagement & Scoring ============

    def update_engagement(
        self,
        contact_id: int,
        event_type: str
    ) -> None:
        """
        Update contact engagement based on an event.

        Args:
            contact_id: Contact to update
            event_type: Type of engagement (open, click, reply, convert)
        """
        contact = self.get_by_id(contact_id)
        if not contact:
            return

        contact.last_engaged_at = datetime.utcnow()

        # Update engagement score
        score_increment = {
            "open": 1,
            "click": 3,
            "reply": 5,
            "convert": 10
        }.get(event_type, 1)

        contact.engagement_score = (contact.engagement_score or 0) + score_increment
        contact.updated_at = datetime.utcnow()

        self.db.commit()

    def get_top_engaged_contacts(
        self,
        limit: int = 100,
        contact_type: Optional[str] = None
    ) -> List[Contact]:
        """Get contacts sorted by engagement score."""
        query = self.db.query(Contact).filter(
            Contact.is_subscribed == True,
            Contact.engagement_score > 0
        )

        if contact_type:
            try:
                ct = ContactType(contact_type)
                query = query.filter(Contact.contact_type == ct)
            except ValueError:
                pass

        return query.order_by(
            Contact.engagement_score.desc()
        ).limit(limit).all()

    # ============ Statistics ============

    def get_statistics(self) -> Dict[str, Any]:
        """Get contact statistics."""
        total = self.count_contacts()
        subscribed = self.count_contacts(is_subscribed=True)
        unsubscribed = self.count_contacts(is_subscribed=False)

        by_type = {}
        for ct in ContactType:
            by_type[ct.value] = self.count_contacts(contact_type=ct.value)

        by_source = self.db.query(
            Contact.source, func.count(Contact.id)
        ).group_by(Contact.source).all()

        suppressed = self.db.query(
            func.count(ContactSuppressionList.id)
        ).scalar() or 0

        return {
            "total": total,
            "subscribed": subscribed,
            "unsubscribed": unsubscribed,
            "subscription_rate": (subscribed / total * 100) if total > 0 else 0,
            "by_type": by_type,
            "by_source": {str(src): count for src, count in by_source},
            "suppressed": suppressed
        }
