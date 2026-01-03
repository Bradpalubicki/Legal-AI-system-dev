"""
Attorney Management Models - Track and manage attorney information for cases

This module provides models for:
- Attorney profiles and contact information
- Attorney-case relationships
- Attorney notes and communications
- Meeting preparation and scheduling
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from ..src.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class AttorneyRole(str, Enum):
    """Role of attorney in case"""
    LEAD_COUNSEL = "lead_counsel"
    CO_COUNSEL = "co_counsel"
    OPPOSING_COUNSEL = "opposing_counsel"
    TRUSTEE_COUNSEL = "trustee_counsel"
    GOVERNMENT_COUNSEL = "government_counsel"
    MEDIATOR = "mediator"
    GUARDIAN_AD_LITEM = "guardian_ad_litem"
    OTHER = "other"


class AttorneyStatus(str, Enum):
    """Status of attorney"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    WITHDRAWN = "withdrawn"
    SUSPENDED = "suspended"


class MeetingType(str, Enum):
    """Type of attorney meeting"""
    INITIAL_CONSULTATION = "initial_consultation"
    CASE_REVIEW = "case_review"
    STRATEGY_SESSION = "strategy_session"
    DEPOSITION_PREP = "deposition_prep"
    HEARING_PREP = "hearing_prep"
    SETTLEMENT_DISCUSSION = "settlement_discussion"
    COURT_APPEARANCE = "court_appearance"
    MEDIATION = "mediation"
    STATUS_UPDATE = "status_update"
    OTHER = "other"


class MeetingStatus(str, Enum):
    """Status of meeting"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


class CommunicationType(str, Enum):
    """Type of communication with attorney"""
    EMAIL = "email"
    PHONE = "phone"
    VIDEO_CALL = "video_call"
    IN_PERSON = "in_person"
    LETTER = "letter"
    PORTAL_MESSAGE = "portal_message"


# ============================================================================
# CORE MODELS
# ============================================================================

class Attorney(Base):
    """
    Attorney profile - represents a legal professional
    Can be opposing counsel, co-counsel, or own attorney
    """
    __tablename__ = "attorneys"

    id = Column(String(36), primary_key=True)  # UUID

    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(250), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    phone_secondary = Column(String(50))

    # Professional Information
    bar_number = Column(String(50), index=True)
    bar_state = Column(String(50))
    bar_status = Column(String(50))  # "Active", "Inactive", etc.
    license_date = Column(DateTime)

    # Firm Information
    firm_name = Column(String(300), index=True)
    firm_website = Column(String(500))
    title = Column(String(100))  # "Partner", "Associate", etc.

    # Address
    address_line1 = Column(String(300))
    address_line2 = Column(String(300))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(100), default="USA")

    # Practice Areas
    practice_areas = Column(JSON)  # ["Bankruptcy", "Civil Litigation", etc.]
    specializations = Column(Text)

    # Communication Preferences
    preferred_contact_method = Column(String(50), default="email")
    preferred_contact_time = Column(String(100))  # "Morning", "Afternoon", etc.
    timezone = Column(String(50), default="America/New_York")

    # Status and Metadata
    status = Column(SQLEnum(AttorneyStatus), default=AttorneyStatus.ACTIVE)
    notes = Column(Text)
    created_by_user_id = Column(String(36), ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Additional Data
    tags = Column(JSON)
    custom_fields = Column(JSON)

    # Relationships
    case_assignments = relationship("AttorneyCaseAssignment", back_populates="attorney", cascade="all, delete-orphan")
    meetings = relationship("AttorneyMeeting", back_populates="attorney", cascade="all, delete-orphan")
    communications = relationship("AttorneyCommunication", back_populates="attorney", cascade="all, delete-orphan")


class AttorneyCaseAssignment(Base):
    """
    Links attorneys to cases with specific roles
    Tracks attorney involvement and billing on each case
    """
    __tablename__ = "attorney_case_assignments"

    id = Column(String(36), primary_key=True)  # UUID

    # Foreign Keys
    attorney_id = Column(String(36), ForeignKey('attorneys.id'), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey('legal_cases.id'), index=True)
    case_number = Column(String(100), index=True)  # Alternative to case_id

    # Role and Status
    role = Column(SQLEnum(AttorneyRole), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_opposing = Column(Boolean, default=False)  # True if opposing counsel

    # Date Tracking
    assignment_date = Column(DateTime, default=datetime.utcnow)
    withdrawal_date = Column(DateTime)
    effective_date = Column(DateTime)

    # Billing Information
    hourly_rate = Column(String(50))
    billing_arrangement = Column(String(100))  # "Hourly", "Contingency", "Flat Fee"

    # Contact for this case (may differ from main contact)
    case_specific_email = Column(String(255))
    case_specific_phone = Column(String(50))

    # Notes
    notes = Column(Text)
    responsibilities = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(String(36))

    # Relationships
    attorney = relationship("Attorney", back_populates="case_assignments")


class AttorneyMeeting(Base):
    """
    Track meetings with attorneys
    Includes meeting prep materials and follow-up items
    """
    __tablename__ = "attorney_meetings"

    id = Column(String(36), primary_key=True)  # UUID

    # Foreign Keys
    attorney_id = Column(String(36), ForeignKey('attorneys.id'), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey('legal_cases.id'), index=True)
    user_id = Column(String(36), ForeignKey('users.id'))

    # Meeting Details
    meeting_type = Column(SQLEnum(MeetingType), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    location = Column(String(500))  # Physical address or video link
    is_virtual = Column(Boolean, default=True)

    # Scheduling
    scheduled_date = Column(DateTime, nullable=False, index=True)
    scheduled_end = Column(DateTime)
    duration_minutes = Column(Integer, default=60)
    status = Column(SQLEnum(MeetingStatus), default=MeetingStatus.SCHEDULED)

    # Preparation Materials (generated by AI)
    prep_document = Column(Text)  # Markdown/HTML meeting prep doc
    prep_questions = Column(JSON)  # Array of questions to ask
    prep_documents_to_bring = Column(JSON)  # Array of document references
    prep_talking_points = Column(JSON)  # Key points to cover
    prep_case_summary = Column(Text)  # Brief case summary for reference

    # Post-Meeting
    meeting_notes = Column(Text)
    action_items = Column(JSON)  # Array of action items with deadlines
    follow_up_date = Column(DateTime)
    outcome_summary = Column(Text)

    # Reminders
    reminder_sent = Column(Boolean, default=False)
    reminder_date = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(String(36))

    # Additional Data
    attachments = Column(JSON)  # Array of file references
    external_calendar_id = Column(String(200))  # Google/Outlook calendar ID

    # Relationships
    attorney = relationship("Attorney", back_populates="meetings")


class AttorneyCommunication(Base):
    """
    Log of all communications with attorneys
    Helps track correspondence and build case timeline
    """
    __tablename__ = "attorney_communications"

    id = Column(String(36), primary_key=True)  # UUID

    # Foreign Keys
    attorney_id = Column(String(36), ForeignKey('attorneys.id'), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey('legal_cases.id'), index=True)
    user_id = Column(String(36), ForeignKey('users.id'))

    # Communication Details
    communication_type = Column(SQLEnum(CommunicationType), nullable=False)
    direction = Column(String(20), default="outbound")  # "inbound" or "outbound"
    subject = Column(String(500))
    content = Column(Text)
    summary = Column(Text)  # AI-generated summary

    # Timing
    communication_date = Column(DateTime, default=datetime.utcnow, index=True)
    duration_minutes = Column(Integer)

    # Status
    requires_response = Column(Boolean, default=False)
    response_deadline = Column(DateTime)
    responded = Column(Boolean, default=False)
    response_date = Column(DateTime)

    # Attachments
    attachments = Column(JSON)  # Array of file references

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(String(36))

    # Additional Data
    tags = Column(JSON)
    importance = Column(String(20), default="normal")  # "low", "normal", "high", "urgent"

    # Relationships
    attorney = relationship("Attorney", back_populates="communications")


class MeetingPrepTemplate(Base):
    """
    Templates for generating meeting preparation documents
    Users can customize templates for different meeting types
    """
    __tablename__ = "meeting_prep_templates"

    id = Column(String(36), primary_key=True)  # UUID

    # Template Details
    name = Column(String(200), nullable=False)
    meeting_type = Column(SQLEnum(MeetingType), nullable=False)
    description = Column(Text)

    # Template Content
    template_content = Column(Text, nullable=False)  # Markdown template with placeholders
    default_questions = Column(JSON)  # Default questions for this meeting type
    default_sections = Column(JSON)  # Default sections to include

    # Settings
    is_system_template = Column(Boolean, default=False)  # Built-in vs user-created
    is_active = Column(Boolean, default=True)

    # Ownership
    created_by_user_id = Column(String(36), ForeignKey('users.id'))
    organization_id = Column(String(36))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_meeting_prep(case_info: Dict[str, Any], meeting_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate meeting preparation materials based on case and meeting information.

    Args:
        case_info: Dictionary containing case details, deadlines, documents, etc.
        meeting_info: Dictionary containing meeting type, attorney info, agenda

    Returns:
        Dictionary with prep materials:
        - summary: Case summary for quick reference
        - questions: List of questions to ask
        - talking_points: Key points to cover
        - documents_needed: List of documents to bring/review
        - timeline: Relevant upcoming deadlines
    """
    meeting_type = meeting_info.get("meeting_type", "general")

    # Base questions for all meeting types
    base_questions = [
        "What is the current status of the case?",
        "Are there any pending deadlines I should be aware of?",
        "What are the next steps we need to take?",
        "Are there any documents you need from me?",
    ]

    # Meeting-type-specific questions
    type_specific_questions = {
        "initial_consultation": [
            "What are my legal options?",
            "What is the likely timeline for this case?",
            "What are the potential outcomes?",
            "What are your fees and billing arrangements?",
            "What information or documents do you need from me?",
        ],
        "case_review": [
            "What progress has been made since our last meeting?",
            "Have there been any new developments in the case?",
            "Are we on track with the timeline?",
            "Should we adjust our strategy based on recent events?",
        ],
        "deposition_prep": [
            "What questions should I expect?",
            "What documents should I review beforehand?",
            "What topics should I avoid discussing?",
            "How should I handle difficult questions?",
            "What can I do to prepare mentally?",
        ],
        "hearing_prep": [
            "What is the purpose of this hearing?",
            "What outcome are we hoping for?",
            "Will I need to speak or testify?",
            "What should I wear and how early should I arrive?",
            "Who else will be present at the hearing?",
        ],
        "settlement_discussion": [
            "What is a realistic settlement range?",
            "What are the strengths and weaknesses of our position?",
            "What are the other side's likely demands?",
            "If we don't settle, what happens next?",
            "What are the tax implications of a settlement?",
        ],
    }

    # Get relevant questions
    questions = base_questions.copy()
    if meeting_type in type_specific_questions:
        questions.extend(type_specific_questions[meeting_type])

    # Generate case summary
    case_summary = f"""
**Case:** {case_info.get('case_number', 'Unknown')}
**Status:** {case_info.get('status', 'Unknown')}
**Type:** {case_info.get('case_type', 'Unknown')}

**Key Dates:**
"""
    deadlines = case_info.get('deadlines', [])
    for deadline in deadlines[:5]:
        if isinstance(deadline, dict):
            date = deadline.get('date', 'TBD')
            event = deadline.get('event', deadline.get('description', 'Event'))
            case_summary += f"- {date}: {event}\n"

    # Talking points based on meeting type
    talking_points = {
        "initial_consultation": [
            "Explain your situation clearly and completely",
            "Bring all relevant documents",
            "Discuss your goals and desired outcomes",
            "Ask about the attorney's experience with similar cases",
            "Understand the fee structure and payment options",
        ],
        "case_review": [
            "Review any correspondence received since last meeting",
            "Discuss any changes in your circumstances",
            "Confirm understanding of current case status",
            "Agree on action items and next steps",
        ],
        "hearing_prep": [
            "Understand exactly what will happen at the hearing",
            "Practice any testimony you may need to give",
            "Review all documents that may be discussed",
            "Know who will be present and their roles",
        ],
        "default": [
            "Review case materials before the meeting",
            "Prepare a list of your questions",
            "Take notes during the meeting",
            "Clarify any points you don't understand",
            "Confirm next steps before leaving",
        ],
    }

    return {
        "case_summary": case_summary.strip(),
        "questions": questions,
        "talking_points": talking_points.get(meeting_type, talking_points["default"]),
        "documents_needed": case_info.get('recent_documents', [])[:5],
        "upcoming_deadlines": deadlines[:5],
    }
