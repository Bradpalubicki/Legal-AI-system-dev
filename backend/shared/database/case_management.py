"""
Case Management Models for Legal AI System

Models for legal cases, matters, tasks, calendar events, and deadline tracking.
Supports case lifecycle management, task assignment, and court calendar integration.
"""

import enum
from datetime import datetime, timezone, date, time
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, Date, Time,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint, 
    CheckConstraint, Numeric, Table
)
from sqlalchemy.orm import relationship, validates

from .base import BaseModel, NamedModel, StatusModel, StatusEnum, PriorityEnum, ConfidentialityLevel


# =============================================================================
# ENUMS
# =============================================================================

class CaseStatus(enum.Enum):
    """Case status in legal proceedings"""
    OPEN = "open"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    PENDING = "pending"
    SETTLED = "settled"
    DISMISSED = "dismissed"
    CLOSED = "closed"
    APPEALED = "appealed"
    ARCHIVED = "archived"


class CaseType(enum.Enum):
    """Types of legal cases"""
    CIVIL = "civil"
    CRIMINAL = "criminal"
    FAMILY = "family"
    PROBATE = "probate"
    BANKRUPTCY = "bankruptcy"
    ADMINISTRATIVE = "administrative"
    APPELLATE = "appellate"
    ARBITRATION = "arbitration"
    MEDIATION = "mediation"
    TRANSACTIONAL = "transactional"


class TaskStatus(enum.Enum):
    """Status of case tasks"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class TaskType(enum.Enum):
    """Types of legal tasks"""
    RESEARCH = "research"
    DRAFTING = "drafting"
    REVIEW = "review"
    FILING = "filing"
    COURT_APPEARANCE = "court_appearance"
    CLIENT_MEETING = "client_meeting"
    DISCOVERY = "discovery"
    DEPOSITION = "deposition"
    NEGOTIATION = "negotiation"
    INVESTIGATION = "investigation"
    CORRESPONDENCE = "correspondence"
    ADMINISTRATIVE = "administrative"


class EventType(enum.Enum):
    """Types of calendar events"""
    HEARING = "hearing"
    TRIAL = "trial"
    DEPOSITION = "deposition"
    MEETING = "meeting"
    DEADLINE = "deadline"
    FILING_DEADLINE = "filing_deadline"
    COURT_DATE = "court_date"
    CONFERENCE = "conference"
    MEDIATION = "mediation"
    ARBITRATION = "arbitration"


class DeadlineType(enum.Enum):
    """Types of legal deadlines"""
    STATUTE_OF_LIMITATIONS = "statute_of_limitations"
    FILING_DEADLINE = "filing_deadline"
    DISCOVERY_DEADLINE = "discovery_deadline"
    MOTION_DEADLINE = "motion_deadline"
    RESPONSE_DEADLINE = "response_deadline"
    APPEAL_DEADLINE = "appeal_deadline"
    PAYMENT_DEADLINE = "payment_deadline"
    CUSTOM = "custom"


class PartyRole(enum.Enum):
    """Roles of parties in a case"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    APPELLANT = "appellant"
    APPELLEE = "appellee"
    INTERVENOR = "intervenor"
    THIRD_PARTY = "third_party"
    WITNESS = "witness"
    EXPERT = "expert"


class CourtLevel(enum.Enum):
    """Levels of court jurisdiction"""
    TRIAL = "trial"
    APPELLATE = "appellate"
    SUPREME = "supreme"
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_APPELLATE = "federal_appellate"
    FEDERAL_SUPREME = "federal_supreme"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many relationship between cases and attorneys
case_attorneys = Table(
    'case_attorneys',
    BaseModel.metadata,
    Column('case_id', Integer, ForeignKey('cases.id', ondelete='CASCADE'), primary_key=True),
    Column('attorney_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(50), default='attorney'),  # lead_attorney, co_counsel, local_counsel
    Column('assigned_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column('assigned_by_id', Integer, ForeignKey('users.id')),
    Index('ix_case_attorneys_case_id', 'case_id'),
    Index('ix_case_attorneys_attorney_id', 'attorney_id')
)


# =============================================================================
# CORE CASE MODELS
# =============================================================================

class Case(BaseModel):
    """Core case/matter model"""
    
    __tablename__ = 'cases'
    
    # Case Identification
    case_number = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    short_title = Column(String(200))
    client_matter_number = Column(String(100))  # Client's internal case number
    
    # Case Classification
    case_type = Column(SQLEnum(CaseType), nullable=False)
    practice_area = Column(String(100))  # From PracticeArea enum in user_management
    case_category = Column(String(100))  # Subcategory within practice area
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    confidentiality_level = Column(SQLEnum(ConfidentialityLevel), default=ConfidentialityLevel.CONFIDENTIAL)
    
    # Status and Lifecycle
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.OPEN, nullable=False)
    status_changed_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Parties and Relationships
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    firm_id = Column(Integer, ForeignKey('law_firms.id'), nullable=False, index=True)
    assigned_attorney_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    originating_attorney_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    responsible_attorney_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Court Information
    court_name = Column(String(200))
    court_id = Column(String(50))  # PACER or state court ID
    judge_name = Column(String(200))
    magistrate_judge = Column(String(200))
    court_level = Column(SQLEnum(CourtLevel))
    jurisdiction = Column(String(100))
    venue = Column(String(200))
    
    # Case Details
    description = Column(Text)
    summary = Column(Text)  # Brief case summary
    key_facts = Column(Text)
    legal_issues = Column(JSON, default=list)  # List of legal issues
    causes_of_action = Column(JSON, default=list)  # List of legal claims
    
    # Important Dates
    date_opened = Column(Date, default=date.today, nullable=False)
    date_closed = Column(Date)
    statute_of_limitations = Column(Date)
    trial_date = Column(Date)
    settlement_date = Column(Date)
    
    # Financial Information
    estimated_value = Column(Numeric(12, 2))  # Estimated case value
    settlement_amount = Column(Numeric(12, 2))
    judgment_amount = Column(Numeric(12, 2))
    costs_incurred = Column(Numeric(10, 2), default=0)
    fees_billed = Column(Numeric(10, 2), default=0)
    
    # Billing Configuration
    hourly_rate = Column(Integer)  # In cents, overrides client/firm default
    billing_type = Column(String(50), default='hourly')  # hourly, flat_fee, contingency, hybrid
    contingency_percentage = Column(Numeric(5, 2))  # For contingency cases
    flat_fee_amount = Column(Numeric(10, 2))
    
    # Case Outcome
    outcome = Column(String(200))
    outcome_details = Column(Text)
    outcome_date = Column(Date)
    appeal_filed = Column(Boolean, default=False)
    appeal_outcome = Column(String(200))
    
    # Risk Assessment
    risk_level = Column(String(20), default='medium')  # low, medium, high, critical
    risk_factors = Column(JSON, default=list)
    malpractice_risk = Column(String(20), default='low')
    
    # Document Management
    total_documents = Column(Integer, default=0)
    key_documents = Column(JSON, default=list)  # References to important docs
    
    # Communication and Notes
    notes = Column(Text)
    internal_notes = Column(Text)  # Not visible to client
    client_instructions = Column(Text)
    
    # Conflicts and Compliance
    conflicts_checked = Column(Boolean, default=False)
    conflicts_cleared = Column(Boolean, default=False)
    ethical_walls = Column(JSON, default=list)  # List of ethical wall requirements
    
    # Integration with External Systems
    pacer_case_id = Column(String(50))
    court_listener_id = Column(Integer)
    westlaw_key_number = Column(String(100))
    external_references = Column(JSON, default=dict)
    
    # AI Analysis
    ai_summary = Column(Text)
    predicted_outcome = Column(String(200))
    outcome_probability = Column(Numeric(5, 2))  # 0-100%
    similar_cases = Column(JSON, default=list)
    
    # Relationships
    client = relationship("Client", back_populates="cases")
    firm = relationship("LawFirm", back_populates="cases") 
    assigned_attorney = relationship("User", foreign_keys=[assigned_attorney_id])
    originating_attorney = relationship("User", foreign_keys=[originating_attorney_id])
    responsible_attorney = relationship("User", foreign_keys=[responsible_attorney_id])
    attorneys = relationship("User", secondary=case_attorneys, backref="assigned_cases")
    
    tasks = relationship("Task", back_populates="case", cascade="all, delete-orphan")
    events = relationship("CalendarEvent", back_populates="case", cascade="all, delete-orphan")
    deadlines = relationship("Deadline", back_populates="case", cascade="all, delete-orphan")
    parties = relationship("CaseParty", back_populates="case", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="case", cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_cases_client_status', 'client_id', 'status'),
        Index('ix_cases_firm_type', 'firm_id', 'case_type'),
        Index('ix_cases_attorney_status', 'assigned_attorney_id', 'status'),
        Index('ix_cases_dates', 'date_opened', 'date_closed'),
        Index('ix_cases_court', 'court_id', 'judge_name'),
        Index('ix_cases_priority_status', 'priority', 'status'),
        UniqueConstraint('firm_id', 'case_number', name='uq_case_number_per_firm'),
        CheckConstraint('date_closed >= date_opened', name='ck_close_after_open'),
        CheckConstraint('estimated_value >= 0', name='ck_positive_estimated_value'),
    )
    
    @property
    def display_name(self) -> str:
        """Get display name for case"""
        return f"{self.case_number}: {self.short_title or self.title}"
    
    @property
    def is_open(self) -> bool:
        """Check if case is open/active"""
        return self.status in [CaseStatus.OPEN, CaseStatus.ACTIVE, CaseStatus.PENDING]
    
    @property
    def days_open(self) -> int:
        """Calculate days case has been open"""
        end_date = self.date_closed or date.today()
        return (end_date - self.date_opened).days
    
    def add_attorney(self, attorney_id: int, role: str = 'attorney'):
        """Add attorney to case team"""
        # This would be implemented with the association table
        pass
    
    def generate_case_number(self) -> str:
        """Generate unique case number"""
        import random
        
        if self.firm_id and self.client_id:
            year = self.date_opened.year
            random_num = random.randint(1000, 9999)
            self.case_number = f"{self.firm_id:04d}-{self.client_id:06d}-{year}-{random_num}"
        
        return self.case_number
    
    @validates('status')
    def validate_status_change(self, key, new_status):
        """Validate status transitions"""
        if hasattr(self, 'status') and self.status:
            # Add business logic for valid status transitions
            pass
        self.status_changed_at = datetime.now(timezone.utc)
        return new_status
    
    def __repr__(self):
        return f"<Case(id={self.id}, number='{self.case_number}', title='{self.short_title}')>"


class Task(BaseModel):
    """Case-related tasks and assignments"""
    
    __tablename__ = 'tasks'
    
    # Task Identification
    title = Column(String(300), nullable=False)
    description = Column(Text)
    task_type = Column(SQLEnum(TaskType), nullable=False)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    
    # Status and Progress
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.NOT_STARTED, nullable=False)
    progress_percent = Column(Integer, default=0)  # 0-100
    
    # Assignment
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False, index=True)
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Timing
    due_date = Column(DateTime(timezone=True))
    estimated_hours = Column(Numeric(5, 2))
    actual_hours = Column(Numeric(5, 2))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Dependencies
    parent_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    depends_on_tasks = Column(JSON, default=list)  # List of task IDs
    
    # Additional Information
    notes = Column(Text)
    completion_notes = Column(Text)
    billable = Column(Boolean, default=True)
    hourly_rate = Column(Integer)  # In cents, overrides defaults
    
    # Reminders and Notifications
    reminder_date = Column(DateTime(timezone=True))
    reminder_sent = Column(Boolean, default=False)
    
    # Relationships
    case = relationship("Case", back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    parent_task = relationship("Task", remote_side=[BaseModel.id], backref="subtasks")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_tasks_case_status', 'case_id', 'status'),
        Index('ix_tasks_assigned_to', 'assigned_to_id', 'status'),
        Index('ix_tasks_due_date', 'due_date'),
        Index('ix_tasks_priority_status', 'priority', 'status'),
        CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='ck_valid_progress'),
        CheckConstraint('estimated_hours >= 0', name='ck_positive_estimated_hours'),
        CheckConstraint('actual_hours >= 0', name='ck_positive_actual_hours'),
    )
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        return (self.due_date and 
                self.due_date < datetime.now(timezone.utc) and 
                self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED])
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date.date() - date.today()
        return delta.days
    
    def mark_completed(self, completion_notes: str = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.progress_percent = 100
        if completion_notes:
            self.completion_notes = completion_notes
    
    def calculate_actual_duration(self) -> Optional[float]:
        """Calculate actual task duration in hours"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 3600
        return None
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title[:30]}...', status='{self.status.value}')>"


class CalendarEvent(BaseModel):
    """Calendar events related to cases"""
    
    __tablename__ = 'calendar_events'
    
    # Event Details
    title = Column(String(300), nullable=False)
    description = Column(Text)
    event_type = Column(SQLEnum(EventType), nullable=False)
    
    # Timing
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    all_day = Column(Boolean, default=False)
    timezone_name = Column(String(50), default='UTC')
    
    # Location
    location = Column(String(300))
    room = Column(String(100))
    address = Column(Text)
    virtual_meeting_url = Column(String(500))
    dial_in_info = Column(Text)
    
    # Case Association
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True, index=True)
    
    # Participants
    organizer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    required_attendees = Column(JSON, default=list)  # User IDs
    optional_attendees = Column(JSON, default=list)  # User IDs
    external_attendees = Column(JSON, default=list)  # Email addresses
    
    # Status and Visibility
    status = Column(String(20), default='scheduled')  # scheduled, confirmed, cancelled, completed
    is_private = Column(Boolean, default=False)
    is_billable = Column(Boolean, default=True)
    
    # Court-Specific Information
    court_name = Column(String(200))
    judge_name = Column(String(200))
    courtroom = Column(String(50))
    docket_number = Column(String(100))
    hearing_type = Column(String(100))
    
    # Reminders and Notifications
    reminder_minutes = Column(Integer, default=30)  # Minutes before event
    reminder_sent = Column(Boolean, default=False)
    calendar_sent = Column(Boolean, default=False)
    
    # Preparation and Follow-up
    preparation_notes = Column(Text)
    preparation_time_minutes = Column(Integer)
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    
    # Results
    outcome = Column(String(200))
    notes = Column(Text)
    next_steps = Column(Text)
    
    # Relationships
    case = relationship("Case", back_populates="events")
    organizer = relationship("User", foreign_keys=[organizer_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_calendar_events_case_date', 'case_id', 'start_datetime'),
        Index('ix_calendar_events_organizer', 'organizer_id', 'start_datetime'),
        Index('ix_calendar_events_type_date', 'event_type', 'start_datetime'),
        CheckConstraint('end_datetime > start_datetime', name='ck_end_after_start'),
    )
    
    @property
    def duration_minutes(self) -> int:
        """Calculate event duration in minutes"""
        delta = self.end_datetime - self.start_datetime
        return int(delta.total_seconds() / 60)
    
    @property
    def is_upcoming(self) -> bool:
        """Check if event is in the future"""
        return self.start_datetime > datetime.now(timezone.utc)
    
    @property
    def is_today(self) -> bool:
        """Check if event is today"""
        return self.start_datetime.date() == date.today()
    
    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}', date='{self.start_datetime.date()}')>"


class Deadline(BaseModel):
    """Legal deadlines and important dates"""
    
    __tablename__ = 'deadlines'
    
    # Deadline Details
    title = Column(String(300), nullable=False)
    description = Column(Text)
    deadline_type = Column(SQLEnum(DeadlineType), nullable=False)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.NORMAL)
    
    # Timing
    deadline_date = Column(DateTime(timezone=True), nullable=False)
    warning_date = Column(DateTime(timezone=True))  # Earlier warning date
    time_sensitive = Column(Boolean, default=True)
    
    # Case Association
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False, index=True)
    
    # Responsibility
    responsible_attorney_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    backup_attorney_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Status
    status = Column(String(20), default='active')  # active, completed, extended, waived
    completed_at = Column(DateTime(timezone=True))
    extension_requested = Column(Boolean, default=False)
    extension_granted = Column(Boolean, default=False)
    extended_deadline = Column(DateTime(timezone=True))
    
    # Legal Authority
    rule_citation = Column(String(200))  # Legal rule creating the deadline
    statute_citation = Column(String(200))
    court_order_reference = Column(String(200))
    
    # Consequences
    consequence_description = Column(Text)
    is_jurisdictional = Column(Boolean, default=False)  # Cannot be waived/extended
    malpractice_risk = Column(String(20), default='medium')
    
    # Calculation
    trigger_event = Column(String(200))  # Event that triggered the deadline
    trigger_date = Column(Date)
    days_from_trigger = Column(Integer)  # Number of days from trigger event
    
    # Tracking
    calendar_days = Column(Boolean, default=True)  # vs business days
    exclude_weekends = Column(Boolean, default=False)
    exclude_holidays = Column(Boolean, default=False)
    
    # Reminders
    reminder_schedule = Column(JSON, default=list)  # List of days before deadline
    reminders_sent = Column(JSON, default=list)  # Track sent reminders
    
    # Notes
    notes = Column(Text)
    completion_notes = Column(Text)
    
    # Relationships
    case = relationship("Case", back_populates="deadlines")
    responsible_attorney = relationship("User", foreign_keys=[responsible_attorney_id])
    backup_attorney = relationship("User", foreign_keys=[backup_attorney_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_deadlines_case_date', 'case_id', 'deadline_date'),
        Index('ix_deadlines_attorney_date', 'responsible_attorney_id', 'deadline_date'),
        Index('ix_deadlines_type_priority', 'deadline_type', 'priority'),
        Index('ix_deadlines_status', 'status', 'deadline_date'),
    )
    
    @property
    def days_until_deadline(self) -> int:
        """Calculate days until deadline"""
        today = date.today()
        deadline_date = self.deadline_date.date() if isinstance(self.deadline_date, datetime) else self.deadline_date
        return (deadline_date - today).days
    
    @property
    def is_overdue(self) -> bool:
        """Check if deadline has passed"""
        return (self.deadline_date < datetime.now(timezone.utc) and 
                self.status not in ['completed', 'waived'])
    
    @property
    def is_critical(self) -> bool:
        """Check if deadline is within critical timeframe"""
        days_left = self.days_until_deadline
        return days_left <= 3 and days_left >= 0 and self.status == 'active'
    
    def mark_completed(self, completion_notes: str = None):
        """Mark deadline as completed"""
        self.status = 'completed'
        self.completed_at = datetime.now(timezone.utc)
        if completion_notes:
            self.completion_notes = completion_notes
    
    def __repr__(self):
        return f"<Deadline(id={self.id}, title='{self.title}', date='{self.deadline_date.date()}')>"


class CaseParty(BaseModel):
    """Parties involved in a case"""
    
    __tablename__ = 'case_parties'
    
    # Party Information
    name = Column(String(300), nullable=False)
    party_type = Column(String(50))  # individual, corporation, government, etc.
    role = Column(SQLEnum(PartyRole), nullable=False)
    
    # Contact Information
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    
    # Legal Representation
    attorney_name = Column(String(200))
    law_firm_name = Column(String(200))
    attorney_phone = Column(String(20))
    attorney_email = Column(String(255))
    attorney_address = Column(Text)
    
    # Case Association
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    date_added = Column(Date, default=date.today)
    date_removed = Column(Date)
    
    # Additional Information
    notes = Column(Text)
    is_pro_se = Column(Boolean, default=False)  # Representing themselves
    service_address = Column(Text)  # Address for service of process
    
    # Relationships
    case = relationship("Case", back_populates="parties")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_case_parties_case_role', 'case_id', 'role'),
        Index('ix_case_parties_name', 'name'),
    )
    
    def __repr__(self):
        return f"<CaseParty(id={self.id}, name='{self.name}', role='{self.role.value}')>"


class TimeEntry(BaseModel):
    """Time tracking for case work"""
    
    __tablename__ = 'time_entries'
    
    # Time Entry Details
    description = Column(String(500), nullable=False)
    hours = Column(Numeric(5, 2), nullable=False)
    date_worked = Column(Date, nullable=False, default=date.today)
    
    # Case and User
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    
    # Billing Information
    hourly_rate = Column(Integer, nullable=False)  # In cents
    total_amount = Column(Integer, nullable=False)  # In cents
    is_billable = Column(Boolean, default=True)
    billing_code = Column(String(50))
    
    # Status
    status = Column(String(20), default='draft')  # draft, submitted, approved, billed
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime(timezone=True))
    billed_at = Column(DateTime(timezone=True))
    
    # Relationships
    case = relationship("Case", back_populates="time_entries")
    user = relationship("User", foreign_keys=[user_id])
    task = relationship("Task", foreign_keys=[task_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    # Table constraints and indexes
    __table_args__ = (
        Index('ix_time_entries_case_date', 'case_id', 'date_worked'),
        Index('ix_time_entries_user_date', 'user_id', 'date_worked'),
        Index('ix_time_entries_status', 'status'),
        CheckConstraint('hours > 0', name='ck_positive_hours'),
        CheckConstraint('hourly_rate > 0', name='ck_positive_rate'),
        CheckConstraint('total_amount > 0', name='ck_positive_amount'),
    )
    
    @validates('hours', 'hourly_rate')
    def calculate_total_amount(self, key, value):
        """Calculate total amount when hours or rate changes"""
        if hasattr(self, 'hours') and hasattr(self, 'hourly_rate'):
            if self.hours and self.hourly_rate:
                self.total_amount = int(float(self.hours) * self.hourly_rate)
        return value
    
    def __repr__(self):
        return f"<TimeEntry(id={self.id}, case_id={self.case_id}, hours={self.hours}, date='{self.date_worked}')>"


# =============================================================================
# EXPORT ALL MODELS
# =============================================================================

__all__ = [
    'Case',
    'Task',
    'CalendarEvent',
    'Deadline',
    'CaseParty',
    'TimeEntry',
    'CaseStatus',
    'CaseType',
    'TaskStatus',
    'TaskType',
    'EventType',
    'DeadlineType',
    'PartyRole',
    'CourtLevel',
    'case_attorneys'
]