"""
Case Monitoring Data Models

Defines data structures for case monitoring, change detection,
notifications, and monitoring rules.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from enum import Enum
from dataclasses import dataclass, field
import uuid

from ..pacer_gateway.models import CaseInfo, DocketEntry, DocumentInfo


class MonitorStatus(Enum):
    """Case monitoring status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    COST_LIMITED = "cost_limited"


class ChangeType(Enum):
    """Types of case changes that can be detected"""
    NEW_DOCKET_ENTRY = "new_docket_entry"
    NEW_DOCUMENT = "new_document"
    CASE_STATUS_CHANGE = "case_status_change"
    PARTY_CHANGE = "party_change"
    JUDGE_CHANGE = "judge_change"
    HEARING_SCHEDULED = "hearing_scheduled"
    DEADLINE_CHANGE = "deadline_change"
    MOTION_FILED = "motion_filed"
    ORDER_ENTERED = "order_entered"
    JUDGMENT_ENTERED = "judgment_entered"
    CASE_CLOSED = "case_closed"
    CASE_REOPENED = "case_reopened"
    OTHER = "other"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SLACK = "slack"
    TEAMS = "teams"
    PUSH = "push"


class MonitoringFrequency(Enum):
    """Monitoring check frequencies"""
    EVERY_5_MIN = "5min"
    EVERY_15_MIN = "15min"
    EVERY_30_MIN = "30min"
    HOURLY = "hourly"
    EVERY_2_HOURS = "2hours"
    EVERY_4_HOURS = "4hours"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class MonitoringRule:
    """Rule defining what changes to monitor and how to respond"""
    rule_id: str
    name: str
    description: str
    change_types: List[ChangeType]
    severity: AlertSeverity = AlertSeverity.MEDIUM
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)  # Additional filtering conditions
    actions: List[str] = field(default_factory=list)  # Actions to take when triggered
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[int] = None  # User ID
    
    def matches_change(self, change_type: ChangeType, change_data: Dict[str, Any]) -> bool:
        """Check if this rule matches a detected change"""
        if not self.is_active:
            return False
        
        if change_type not in self.change_types:
            return False
        
        # Check additional conditions
        for condition_key, condition_value in self.conditions.items():
            if condition_key in change_data:
                if change_data[condition_key] != condition_value:
                    return False
        
        return True


@dataclass
class MonitoredCase:
    """A case being monitored for changes"""
    monitor_id: str
    case_number: str
    court_id: str
    case_title: str = ""
    monitoring_rules: List[str] = field(default_factory=list)  # Rule IDs
    status: MonitorStatus = MonitorStatus.ACTIVE
    frequency: MonitoringFrequency = MonitoringFrequency.EVERY_15_MIN
    priority: int = 1  # 1=highest, 5=lowest
    cost_limit_cents: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_checked_at: Optional[datetime] = None
    last_change_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    check_count: int = 0
    change_count: int = 0
    error_count: int = 0
    total_cost_cents: int = 0
    created_by: Optional[int] = None  # User ID
    assigned_to: List[int] = field(default_factory=list)  # User IDs to notify
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Cached case data
    cached_case_info: Optional[Dict[str, Any]] = None
    cached_docket_entries: List[Dict[str, Any]] = field(default_factory=list)
    cached_docket_hash: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Check if monitoring is active"""
        return self.status == MonitorStatus.ACTIVE
    
    @property
    def total_cost_dollars(self) -> float:
        """Get total cost in dollars"""
        return self.total_cost_cents / 100.0
    
    def get_next_check_time(self) -> datetime:
        """Calculate next check time based on frequency"""
        now = datetime.now(timezone.utc)
        
        frequency_minutes = {
            MonitoringFrequency.EVERY_5_MIN: 5,
            MonitoringFrequency.EVERY_15_MIN: 15,
            MonitoringFrequency.EVERY_30_MIN: 30,
            MonitoringFrequency.HOURLY: 60,
            MonitoringFrequency.EVERY_2_HOURS: 120,
            MonitoringFrequency.EVERY_4_HOURS: 240,
            MonitoringFrequency.DAILY: 1440,
            MonitoringFrequency.WEEKLY: 10080
        }
        
        minutes = frequency_minutes.get(self.frequency, 15)
        
        # Add some jitter to distribute load
        import random
        jitter_minutes = random.randint(-2, 2)
        
        return now + timedelta(minutes=minutes + jitter_minutes)
    
    def should_check_now(self) -> bool:
        """Check if case should be monitored now"""
        if not self.is_active:
            return False
        
        if not self.next_check_at:
            return True
        
        return datetime.now(timezone.utc) >= self.next_check_at
    
    def update_after_check(self, found_changes: bool = False, cost_cents: int = 0, error: str = None):
        """Update case after a monitoring check"""
        now = datetime.now(timezone.utc)
        
        self.last_checked_at = now
        self.check_count += 1
        self.total_cost_cents += cost_cents
        
        if found_changes:
            self.last_change_at = now
            self.change_count += 1
        
        if error:
            self.error_count += 1
            if self.error_count >= 5:  # Too many errors
                self.status = MonitorStatus.ERROR
        else:
            self.error_count = 0  # Reset error count on success
        
        self.next_check_at = self.get_next_check_time()


@dataclass
class ChangeDetection:
    """A detected change in a monitored case"""
    change_id: str
    monitor_id: str
    case_number: str
    court_id: str
    change_type: ChangeType
    severity: AlertSeverity
    detected_at: datetime
    description: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    affected_entry_number: Optional[str] = None
    affected_document_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_processed: bool = False
    
    def __post_init__(self):
        if not self.change_id:
            self.change_id = str(uuid.uuid4())
        if not self.detected_at:
            self.detected_at = datetime.now(timezone.utc)


@dataclass
class NotificationEvent:
    """A notification event triggered by a change"""
    event_id: str
    change_id: str
    rule_id: str
    monitor_id: str
    case_number: str
    court_id: str
    event_type: ChangeType
    severity: AlertSeverity
    title: str
    message: str
    channels: List[NotificationChannel]
    recipients: List[str] = field(default_factory=list)  # Email addresses, phone numbers, etc.
    user_ids: List[int] = field(default_factory=list)  # User IDs for in-app notifications
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    delivery_status: Dict[NotificationChannel, str] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
    
    @property
    def is_sent(self) -> bool:
        """Check if notification has been successfully sent"""
        return bool(self.sent_at and any(
            status == "delivered" for status in self.delivery_status.values()
        ))
    
    def can_retry(self) -> bool:
        """Check if notification can be retried"""
        return self.retry_count < self.max_retries and not self.is_sent


@dataclass
class DeltaAnalysis:
    """Analysis of changes between two docket states"""
    case_number: str
    court_id: str
    analysis_time: datetime
    old_entry_count: int
    new_entry_count: int
    added_entries: List[Dict[str, Any]] = field(default_factory=list)
    modified_entries: List[Dict[str, Any]] = field(default_factory=list)
    removed_entries: List[Dict[str, Any]] = field(default_factory=list)
    new_documents: List[Dict[str, Any]] = field(default_factory=list)
    status_changes: List[Dict[str, Any]] = field(default_factory=list)
    detected_changes: List[ChangeDetection] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected"""
        return bool(
            self.added_entries or 
            self.modified_entries or 
            self.removed_entries or 
            self.new_documents or 
            self.status_changes
        )
    
    @property
    def total_changes(self) -> int:
        """Get total number of changes"""
        return (
            len(self.added_entries) + 
            len(self.modified_entries) + 
            len(self.removed_entries) +
            len(self.new_documents) + 
            len(self.status_changes)
        )


@dataclass
class MonitoringStatistics:
    """Statistics for case monitoring"""
    total_monitored_cases: int = 0
    active_monitors: int = 0
    paused_monitors: int = 0
    error_monitors: int = 0
    total_checks_today: int = 0
    total_changes_today: int = 0
    total_notifications_today: int = 0
    total_cost_today_cents: int = 0
    average_check_time_ms: float = 0.0
    change_detection_rate: float = 0.0  # Percentage of checks that find changes
    cost_per_change_cents: float = 0.0
    most_active_court: Optional[str] = None
    most_changed_case: Optional[str] = None
    
    @property
    def total_cost_today_dollars(self) -> float:
        """Get total cost today in dollars"""
        return self.total_cost_today_cents / 100.0


@dataclass
class MonitoringAlert:
    """High-priority monitoring alert"""
    alert_id: str
    alert_type: str  # "cost_limit", "error_threshold", "high_activity", etc.
    severity: AlertSeverity
    title: str
    description: str
    affected_monitors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None  # User ID
    resolved_at: Optional[datetime] = None
    actions_taken: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = str(uuid.uuid4())
    
    @property
    def is_acknowledged(self) -> bool:
        """Check if alert has been acknowledged"""
        return bool(self.acknowledged_at)
    
    @property
    def is_resolved(self) -> bool:
        """Check if alert has been resolved"""
        return bool(self.resolved_at)


# Predefined monitoring rules for common legal scenarios
DEFAULT_MONITORING_RULES = [
    MonitoringRule(
        rule_id="new_filing",
        name="New Filing Alert",
        description="Alert when any new document is filed in the case",
        change_types=[ChangeType.NEW_DOCKET_ENTRY, ChangeType.NEW_DOCUMENT],
        severity=AlertSeverity.MEDIUM,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
    ),
    
    MonitoringRule(
        rule_id="motion_filed",
        name="Motion Filed Alert",
        description="High-priority alert when a motion is filed",
        change_types=[ChangeType.MOTION_FILED],
        severity=AlertSeverity.HIGH,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.IN_APP],
        conditions={"description_contains": ["motion", "Motion"]}
    ),
    
    MonitoringRule(
        rule_id="order_entered",
        name="Court Order Alert",
        description="Critical alert when a court order is entered",
        change_types=[ChangeType.ORDER_ENTERED],
        severity=AlertSeverity.CRITICAL,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.IN_APP, NotificationChannel.PUSH],
        conditions={"description_contains": ["order", "Order", "ORDER"]}
    ),
    
    MonitoringRule(
        rule_id="judgment_entered",
        name="Judgment Alert",
        description="Urgent alert when a judgment is entered",
        change_types=[ChangeType.JUDGMENT_ENTERED],
        severity=AlertSeverity.URGENT,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.IN_APP, NotificationChannel.PUSH],
        conditions={"description_contains": ["judgment", "Judgment", "JUDGMENT"]}
    ),
    
    MonitoringRule(
        rule_id="hearing_scheduled",
        name="Hearing Scheduled Alert",
        description="Alert when a hearing or conference is scheduled",
        change_types=[ChangeType.HEARING_SCHEDULED],
        severity=AlertSeverity.HIGH,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        conditions={"description_contains": ["hearing", "conference", "oral argument"]}
    ),
    
    MonitoringRule(
        rule_id="case_status_change",
        name="Case Status Change",
        description="Alert when case status changes (closed, reopened, etc.)",
        change_types=[ChangeType.CASE_STATUS_CHANGE, ChangeType.CASE_CLOSED, ChangeType.CASE_REOPENED],
        severity=AlertSeverity.HIGH,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
    ),
    
    MonitoringRule(
        rule_id="judge_change",
        name="Judge Assignment Change",
        description="Alert when the assigned judge changes",
        change_types=[ChangeType.JUDGE_CHANGE],
        severity=AlertSeverity.MEDIUM,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
    ),
    
    MonitoringRule(
        rule_id="deadline_change",
        name="Deadline Change Alert",
        description="Alert when important deadlines are modified",
        change_types=[ChangeType.DEADLINE_CHANGE],
        severity=AlertSeverity.HIGH,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        conditions={"description_contains": ["deadline", "due date", "time limit"]}
    )
]


def get_default_rules() -> List[MonitoringRule]:
    """Get default monitoring rules"""
    return DEFAULT_MONITORING_RULES.copy()


def create_custom_rule(
    name: str,
    change_types: List[ChangeType],
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    channels: List[NotificationChannel] = None,
    conditions: Dict[str, Any] = None
) -> MonitoringRule:
    """Create a custom monitoring rule"""
    
    if channels is None:
        channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
    
    return MonitoringRule(
        rule_id=str(uuid.uuid4()),
        name=name,
        description=f"Custom rule: {name}",
        change_types=change_types,
        severity=severity,
        notification_channels=channels,
        conditions=conditions or {}
    )


def categorize_docket_entry(entry_description: str) -> List[ChangeType]:
    """Categorize a docket entry based on its description"""
    
    description_lower = entry_description.lower()
    categories = []
    
    # Motion-related
    if any(word in description_lower for word in ["motion", "application", "petition"]):
        categories.append(ChangeType.MOTION_FILED)
    
    # Order-related
    if any(word in description_lower for word in ["order", "ruling", "decision"]):
        categories.append(ChangeType.ORDER_ENTERED)
    
    # Judgment-related
    if any(word in description_lower for word in ["judgment", "verdict", "award"]):
        categories.append(ChangeType.JUDGMENT_ENTERED)
    
    # Hearing-related
    if any(word in description_lower for word in ["hearing", "conference", "oral argument", "trial"]):
        categories.append(ChangeType.HEARING_SCHEDULED)
    
    # Case closure
    if any(word in description_lower for word in ["closed", "dismissed", "terminated"]):
        categories.append(ChangeType.CASE_CLOSED)
    
    # Case reopened
    if any(word in description_lower for word in ["reopened", "reinstated"]):
        categories.append(ChangeType.CASE_REOPENED)
    
    # Default to new docket entry if no specific category
    if not categories:
        categories.append(ChangeType.NEW_DOCKET_ENTRY)
    
    return categories


def calculate_priority_score(monitored_case: MonitoredCase) -> float:
    """Calculate priority score for scheduling monitoring checks"""
    
    base_score = monitored_case.priority  # 1-5 scale (1 = highest)
    
    # Adjust based on recent activity
    if monitored_case.last_change_at:
        hours_since_change = (datetime.now(timezone.utc) - monitored_case.last_change_at).total_seconds() / 3600
        if hours_since_change < 24:
            base_score -= 1  # Higher priority for recently active cases
    
    # Adjust based on case type (could be enhanced with ML)
    case_title_lower = monitored_case.case_title.lower()
    if any(word in case_title_lower for word in ["urgent", "emergency", "tro", "preliminary injunction"]):
        base_score -= 2
    
    # Adjust based on monitoring rules
    if len(monitored_case.monitoring_rules) > 3:  # Many rules = important case
        base_score -= 0.5
    
    return max(1.0, base_score)  # Ensure minimum priority of 1