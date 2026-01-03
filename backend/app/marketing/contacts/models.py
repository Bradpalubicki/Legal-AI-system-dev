"""
Marketing Contact Models

SQLAlchemy models for marketing contacts extracted from CourtListener.
Includes contacts, their associated cases, and engagement tracking.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.src.core.database import Base


class ContactType(enum.Enum):
    """Types of marketing contacts"""
    ATTORNEY = "attorney"
    PARTY_INDIVIDUAL = "party_individual"
    PARTY_BUSINESS = "party_business"
    HR_PROFESSIONAL = "hr_professional"
    JOURNALIST = "journalist"
    OTHER = "other"


class ContactSource(enum.Enum):
    """Source of contact acquisition"""
    COURTLISTENER = "courtlistener"
    MANUAL = "manual"
    IMPORT = "import"
    WEBSITE = "website"
    REFERRAL = "referral"


class Contact(Base):
    """
    Marketing contact extracted from court filings.

    Stores attorney and party contact information along with
    engagement metrics and subscription status.
    """
    __tablename__ = "marketing_contacts"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(255))

    # Classification
    contact_type = Column(SQLEnum(ContactType), default=ContactType.OTHER)
    source = Column(SQLEnum(ContactSource), default=ContactSource.COURTLISTENER)

    # Professional Info
    firm_name = Column(String(255))
    title = Column(String(100))
    bar_number = Column(String(50))

    # Contact Details
    phone = Column(String(50))
    fax = Column(String(50))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))

    # CourtListener Reference
    courtlistener_attorney_id = Column(Integer, index=True)
    courtlistener_party_id = Column(Integer)

    # Engagement Status
    is_subscribed = Column(Boolean, default=True)
    opted_out_at = Column(DateTime)
    opt_out_reason = Column(String(255))

    # Scoring
    engagement_score = Column(Integer, default=0)
    value_score = Column(Integer, default=0)  # Based on case types

    # Metadata
    raw_contact_data = Column(JSON)  # Original CourtListener data
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contacted_at = Column(DateTime)
    last_engaged_at = Column(DateTime)  # Last open/click

    # Relationships
    cases = relationship("ContactCase", back_populates="contact", cascade="all, delete-orphan")
    emails_received = relationship("EmailSend", back_populates="contact")

    def __repr__(self):
        return f"<Contact(id={self.id}, email='{self.email}', type='{self.contact_type}')>"

    @property
    def display_name(self) -> str:
        """Get the best display name available"""
        if self.full_name:
            return self.full_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return self.email.split('@')[0]


class ContactCase(Base):
    """
    Links contacts to their court cases.

    Tracks which cases a contact is involved in and their role,
    enabling targeted marketing based on case characteristics.
    """
    __tablename__ = "marketing_contact_cases"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("marketing_contacts.id"), index=True)

    # Case Reference
    courtlistener_docket_id = Column(Integer, index=True)
    case_number = Column(String(100))
    case_name = Column(String(500))
    court = Column(String(100))

    # Role in Case
    role = Column(String(50))  # plaintiff, defendant, attorney_for_plaintiff, etc.
    party_type = Column(String(50))  # For attorneys: who they represent

    # Case Details (for targeting)
    nature_of_suit = Column(String(100))
    case_type = Column(String(100))
    date_filed = Column(DateTime)

    # AI Analysis
    case_value_estimate = Column(String(50))  # low, medium, high, very_high
    complexity_score = Column(Integer)
    ai_summary = Column(Text)  # AI-generated case summary for personalization

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contact = relationship("Contact", back_populates="cases")

    def __repr__(self):
        return f"<ContactCase(id={self.id}, case='{self.case_name[:50] if self.case_name else 'N/A'}')>"


class ContactTag(Base):
    """
    Tags for organizing and segmenting contacts.

    Allows flexible categorization beyond the built-in fields.
    """
    __tablename__ = "marketing_contact_tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    color = Column(String(7))  # Hex color code

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContactTag(name='{self.name}')>"


class ContactSuppressionList(Base):
    """
    Global suppression list for emails that should never be contacted.

    Includes hard bounces, spam complaints, and manual suppressions.
    Separate from opt-outs to ensure compliance.
    """
    __tablename__ = "marketing_suppression_list"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    reason = Column(String(50), nullable=False)  # hard_bounce, spam_complaint, manual, legal
    details = Column(Text)
    source = Column(String(100))  # Where the suppression came from

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SuppressionList(email='{self.email}', reason='{self.reason}')>"
