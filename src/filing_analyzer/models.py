"""
Filing Analysis Data Models

Defines comprehensive data structures for intelligent filing analysis
including document types, analysis results, impact assessments, and notifications.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid


class FilingType(Enum):
    """Types of legal filings"""
    # Motions
    MOTION_TO_DISMISS = "motion_to_dismiss"
    MOTION_FOR_SUMMARY_JUDGMENT = "motion_for_summary_judgment" 
    MOTION_FOR_PRELIMINARY_INJUNCTION = "motion_for_preliminary_injunction"
    MOTION_FOR_TEMPORARY_RESTRAINING_ORDER = "motion_for_tro"
    MOTION_TO_COMPEL = "motion_to_compel"
    MOTION_FOR_SANCTIONS = "motion_for_sanctions"
    MOTION_IN_LIMINE = "motion_in_limine"
    MOTION_FOR_PROTECTIVE_ORDER = "motion_for_protective_order"
    MOTION_TO_AMEND = "motion_to_amend"
    MOTION_FOR_EXTENSION = "motion_for_extension"
    
    # Pleadings
    COMPLAINT = "complaint"
    ANSWER = "answer"
    COUNTERCLAIM = "counterclaim"
    CROSS_CLAIM = "cross_claim"
    THIRD_PARTY_COMPLAINT = "third_party_complaint"
    AMENDED_PLEADING = "amended_pleading"
    
    # Discovery
    DISCOVERY_REQUEST = "discovery_request"
    DISCOVERY_RESPONSE = "discovery_response"
    DEPOSITION_NOTICE = "deposition_notice"
    EXPERT_REPORT = "expert_report"
    
    # Orders and Judgments
    ORDER = "order"
    JUDGMENT = "judgment"
    RULING = "ruling"
    MINUTE_ORDER = "minute_order"
    
    # Briefs and Memoranda
    BRIEF = "brief"
    MEMORANDUM = "memorandum"
    REPLY_BRIEF = "reply_brief"
    
    # Administrative
    NOTICE = "notice"
    STIPULATION = "stipulation"
    SETTLEMENT_AGREEMENT = "settlement_agreement"
    EXHIBIT = "exhibit"
    CERTIFICATE_OF_SERVICE = "certificate_of_service"
    
    # Appeals
    NOTICE_OF_APPEAL = "notice_of_appeal"
    APPELLATE_BRIEF = "appellate_brief"
    
    # Specialized
    BANKRUPTCY_FILING = "bankruptcy_filing"
    PATENT_FILING = "patent_filing"
    SEC_FILING = "sec_filing"
    
    # Other
    OTHER = "other"
    UNKNOWN = "unknown"


class ImpactLevel(Enum):
    """Impact level of a filing on the case"""
    MINIMAL = "minimal"          # Routine administrative filing
    LOW = "low"                  # Standard procedural filing
    MEDIUM = "medium"            # Important substantive filing
    HIGH = "high"                # Significant case development
    CRITICAL = "critical"        # Case-changing development
    EMERGENCY = "emergency"      # Requires immediate attention


class UrgencyLevel(Enum):
    """Urgency level for response or action"""
    LOW = "low"                  # No immediate action required
    MEDIUM = "medium"            # Action needed within days/weeks
    HIGH = "high"                # Action needed within days
    URGENT = "urgent"            # Action needed within 24-48 hours
    EMERGENCY = "emergency"      # Immediate action required


class AnalysisStatus(Enum):
    """Status of filing analysis"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


class NotificationType(Enum):
    """Types of notifications"""
    NEW_FILING = "new_filing"
    DEADLINE_ALERT = "deadline_alert"
    ACTION_REQUIRED = "action_required"
    COMPLIANCE_WARNING = "compliance_warning"
    IMPACT_ASSESSMENT = "impact_assessment"
    SUMMARY_REPORT = "summary_report"


@dataclass
class ActionItem:
    """Required action identified from filing analysis"""
    action_id: str
    description: str
    action_type: str  # "response_due", "deadline", "compliance", "strategic"
    urgency: UrgencyLevel
    due_date: Optional[datetime] = None
    estimated_effort_hours: Optional[float] = None
    assigned_to: List[int] = field(default_factory=list)  # User IDs
    dependencies: List[str] = field(default_factory=list)  # Other action IDs
    status: str = "pending"  # pending, in_progress, completed, cancelled
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.action_id:
            self.action_id = str(uuid.uuid4())
    
    @property
    def is_overdue(self) -> bool:
        """Check if action item is overdue"""
        if not self.due_date:
            return False
        return datetime.now(timezone.utc) > self.due_date
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Get days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.now(timezone.utc)
        return delta.days


@dataclass
class LegalCitation:
    """Legal citation found in filing"""
    citation_id: str
    citation_text: str
    citation_type: str  # "case", "statute", "regulation", "rule"
    case_name: Optional[str] = None
    court: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    jurisdiction: Optional[str] = None
    relevance_score: float = 0.0  # 0.0 to 1.0
    context: str = ""  # Surrounding text
    is_controlling: bool = False
    is_binding: bool = False
    
    def __post_init__(self):
        if not self.citation_id:
            self.citation_id = str(uuid.uuid4())


@dataclass
class ExtractedContent:
    """Content extracted from filing"""
    content_type: str  # "summary", "key_points", "arguments", "facts", "procedural_history"
    content: str
    confidence_score: float = 0.0  # AI confidence in extraction
    page_numbers: List[int] = field(default_factory=list)
    section_title: Optional[str] = None
    extracted_entities: List[str] = field(default_factory=list)  # People, organizations, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceRequirement:
    """Compliance requirement identified in filing"""
    requirement_id: str
    description: str
    regulation_source: str  # Which regulation/rule requires this
    due_date: Optional[datetime] = None
    responsible_party: str = ""
    compliance_status: str = "pending"  # pending, compliant, non_compliant, under_review
    risk_level: str = "medium"  # low, medium, high, critical
    penalties: str = ""  # Description of potential penalties
    remediation_steps: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.requirement_id:
            self.requirement_id = str(uuid.uuid4())


@dataclass
class ImpactAnalysis:
    """Analysis of filing's impact on the case"""
    overall_impact: ImpactLevel
    case_trajectory_change: str  # "positive", "negative", "neutral", "mixed"
    likelihood_of_success_change: float = 0.0  # -1.0 to 1.0 (change in probability)
    estimated_cost_impact: Optional[float] = None  # Dollar impact
    timeline_impact_days: Optional[int] = None  # Impact on case timeline
    strategic_implications: List[str] = field(default_factory=list)
    risks_identified: List[str] = field(default_factory=list)
    opportunities_identified: List[str] = field(default_factory=list)
    recommended_responses: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class FilingAnalysis:
    """Complete analysis of a legal filing"""
    analysis_id: str
    filing_id: str
    case_number: str
    court_id: str
    document_title: str
    filing_type: FilingType
    filing_date: datetime
    filed_by: str = ""
    
    # Analysis results
    status: AnalysisStatus = AnalysisStatus.PENDING
    impact_level: ImpactLevel = ImpactLevel.LOW
    urgency_level: UrgencyLevel = UrgencyLevel.LOW
    
    # Extracted content
    extracted_content: List[ExtractedContent] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    legal_arguments: List[str] = field(default_factory=list)
    factual_claims: List[str] = field(default_factory=list)
    procedural_requests: List[str] = field(default_factory=list)
    
    # Citations and references
    citations: List[LegalCitation] = field(default_factory=list)
    referenced_documents: List[str] = field(default_factory=list)
    
    # Action items and deadlines
    action_items: List[ActionItem] = field(default_factory=list)
    deadlines: List[Dict[str, Any]] = field(default_factory=list)
    
    # Impact and compliance
    impact_analysis: Optional[ImpactAnalysis] = None
    compliance_requirements: List[ComplianceRequirement] = field(default_factory=list)
    
    # AI analysis metadata
    analysis_confidence: float = 0.0  # Overall confidence in analysis
    processing_time_seconds: float = 0.0
    ai_model_version: str = ""
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Flags and alerts
    requires_immediate_attention: bool = False
    contains_sanctions_risk: bool = False
    contains_deadline: bool = False
    contains_motion: bool = False
    contains_settlement_discussion: bool = False
    potentially_dispositive: bool = False  # Could end/significantly change case
    
    # Review and approval
    reviewed_by: Optional[int] = None  # User ID
    reviewed_at: Optional[datetime] = None
    review_notes: str = ""
    approved: bool = False
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.analysis_id:
            self.analysis_id = str(uuid.uuid4())
    
    @property
    def is_high_priority(self) -> bool:
        """Check if filing requires high priority attention"""
        return (
            self.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL, ImpactLevel.EMERGENCY] or
            self.urgency_level in [UrgencyLevel.URGENT, UrgencyLevel.EMERGENCY] or
            self.requires_immediate_attention or
            self.potentially_dispositive
        )
    
    @property
    def summary_text(self) -> str:
        """Get summary text for notifications"""
        content_summaries = [
            content.content for content in self.extracted_content
            if content.content_type == "summary"
        ]
        if content_summaries:
            return content_summaries[0][:500]  # First 500 characters
        
        # Fallback to key points
        if self.key_points:
            return "; ".join(self.key_points[:3])  # First 3 key points
        
        return f"{self.filing_type.value.replace('_', ' ').title()} filed by {self.filed_by}"


@dataclass
class NotificationRule:
    """Rule for determining notification routing and content"""
    rule_id: str
    name: str
    description: str
    
    # Conditions
    filing_types: List[FilingType] = field(default_factory=list)
    impact_levels: List[ImpactLevel] = field(default_factory=list)
    urgency_levels: List[UrgencyLevel] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    filed_by_patterns: List[str] = field(default_factory=list)  # Regex patterns
    case_types: List[str] = field(default_factory=list)
    courts: List[str] = field(default_factory=list)
    
    # Actions
    notification_channels: List[str] = field(default_factory=list)  # email, sms, slack, etc.
    recipients: List[str] = field(default_factory=list)  # Email addresses, user IDs
    escalation_delay_hours: int = 24
    custom_message_template: Optional[str] = None
    attach_full_analysis: bool = True
    create_task: bool = False
    
    # Metadata
    priority: int = 1  # 1 = highest
    is_active: bool = True
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if not self.rule_id:
            self.rule_id = str(uuid.uuid4())
    
    def matches_filing(self, analysis: FilingAnalysis) -> bool:
        """Check if this rule matches a filing analysis"""
        if not self.is_active:
            return False
        
        # Check filing type
        if self.filing_types and analysis.filing_type not in self.filing_types:
            return False
        
        # Check impact level
        if self.impact_levels and analysis.impact_level not in self.impact_levels:
            return False
        
        # Check urgency level
        if self.urgency_levels and analysis.urgency_level not in self.urgency_levels:
            return False
        
        # Check keywords in document title and content
        if self.keywords:
            text_to_search = f"{analysis.document_title} {' '.join(analysis.key_points)}".lower()
            if not any(keyword.lower() in text_to_search for keyword in self.keywords):
                return False
        
        # Check filed by patterns
        if self.filed_by_patterns:
            import re
            if not any(re.search(pattern, analysis.filed_by, re.IGNORECASE) 
                      for pattern in self.filed_by_patterns):
                return False
        
        # Check courts
        if self.courts and analysis.court_id not in self.courts:
            return False
        
        return True


@dataclass
class NotificationEvent:
    """Notification event for a filing analysis"""
    event_id: str
    analysis_id: str
    rule_id: str
    notification_type: NotificationType
    case_number: str
    court_id: str
    
    # Content
    title: str
    message: str
    summary: str
    urgency: UrgencyLevel
    
    # Delivery
    channels: List[str] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    delivery_status: Dict[str, str] = field(default_factory=dict)  # channel -> status
    
    # Attachments and links
    analysis_attachment: bool = False
    document_link: Optional[str] = None
    action_items: List[str] = field(default_factory=list)  # Action item IDs
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
    
    @property
    def is_sent(self) -> bool:
        """Check if notification has been sent"""
        return bool(self.sent_at)
    
    @property
    def is_delivered(self) -> bool:
        """Check if notification has been delivered successfully"""
        return any(status == "delivered" for status in self.delivery_status.values())


# Predefined filing type classifications with keywords
FILING_TYPE_KEYWORDS = {
    FilingType.MOTION_TO_DISMISS: [
        "motion to dismiss", "dismiss", "rule 12(b)", "failure to state a claim",
        "lack of jurisdiction", "improper venue", "failure to join"
    ],
    FilingType.MOTION_FOR_SUMMARY_JUDGMENT: [
        "motion for summary judgment", "summary judgment", "rule 56",
        "no genuine issue", "matter of law"
    ],
    FilingType.MOTION_FOR_PRELIMINARY_INJUNCTION: [
        "preliminary injunction", "preliminary relief", "enjoin", "restrain",
        "irreparable harm", "likelihood of success"
    ],
    FilingType.MOTION_FOR_TEMPORARY_RESTRAINING_ORDER: [
        "temporary restraining order", "tro", "emergency relief", "immediate harm",
        "ex parte", "without notice"
    ],
    FilingType.MOTION_TO_COMPEL: [
        "motion to compel", "compel discovery", "failure to respond", "inadequate response"
    ],
    FilingType.MOTION_FOR_SANCTIONS: [
        "motion for sanctions", "sanctions", "rule 11", "frivolous", "bad faith",
        "attorney fees"
    ],
    FilingType.COMPLAINT: [
        "complaint", "petition", "plaintiff", "alleges", "cause of action"
    ],
    FilingType.ANSWER: [
        "answer", "response to complaint", "defendant", "denies", "affirmative defense"
    ],
    FilingType.ORDER: [
        "order", "ordered", "it is hereby ordered", "the court orders", "granted", "denied"
    ],
    FilingType.JUDGMENT: [
        "judgment", "final judgment", "enters judgment", "judgment is entered"
    ]
}

# Default notification rules
DEFAULT_NOTIFICATION_RULES = [
    NotificationRule(
        rule_id="emergency_filings",
        name="Emergency Filings",
        description="Immediate notification for emergency filings",
        filing_types=[FilingType.MOTION_FOR_TEMPORARY_RESTRAINING_ORDER],
        impact_levels=[ImpactLevel.EMERGENCY, ImpactLevel.CRITICAL],
        urgency_levels=[UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT],
        notification_channels=["email", "sms", "push"],
        escalation_delay_hours=1,
        priority=1
    ),
    NotificationRule(
        rule_id="dispositive_motions",
        name="Dispositive Motions",
        description="High priority notification for potentially case-ending motions",
        filing_types=[FilingType.MOTION_TO_DISMISS, FilingType.MOTION_FOR_SUMMARY_JUDGMENT],
        impact_levels=[ImpactLevel.HIGH, ImpactLevel.CRITICAL],
        notification_channels=["email", "slack"],
        escalation_delay_hours=4,
        priority=2
    ),
    NotificationRule(
        rule_id="court_orders",
        name="Court Orders",
        description="Notification for all court orders",
        filing_types=[FilingType.ORDER, FilingType.RULING],
        notification_channels=["email"],
        escalation_delay_hours=12,
        priority=3
    ),
    NotificationRule(
        rule_id="judgments",
        name="Judgments",
        description="Critical notification for judgments",
        filing_types=[FilingType.JUDGMENT],
        impact_levels=[ImpactLevel.CRITICAL, ImpactLevel.HIGH],
        notification_channels=["email", "sms"],
        escalation_delay_hours=2,
        priority=1
    ),
    NotificationRule(
        rule_id="sanctions_motions",
        name="Sanctions Motions",
        description="High priority notification for sanctions motions",
        filing_types=[FilingType.MOTION_FOR_SANCTIONS],
        keywords=["sanctions", "rule 11", "frivolous", "bad faith"],
        impact_levels=[ImpactLevel.HIGH, ImpactLevel.CRITICAL],
        notification_channels=["email", "sms"],
        escalation_delay_hours=6,
        priority=2
    )
]


def classify_filing_type(document_title: str, content_preview: str = "") -> FilingType:
    """Classify filing type based on title and content"""
    
    text_to_analyze = f"{document_title} {content_preview}".lower()
    
    # Score each filing type
    type_scores = {}
    
    for filing_type, keywords in FILING_TYPE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_to_analyze:
                # Give higher score for exact matches in title
                if keyword.lower() in document_title.lower():
                    score += 2
                else:
                    score += 1
        
        if score > 0:
            type_scores[filing_type] = score
    
    # Return the highest scoring type, or UNKNOWN if no matches
    if type_scores:
        return max(type_scores.items(), key=lambda x: x[1])[0]
    
    return FilingType.UNKNOWN


def extract_urgency_indicators(text: str) -> UrgencyLevel:
    """Extract urgency level from text content"""
    
    text_lower = text.lower()
    
    # Emergency indicators
    emergency_keywords = [
        "emergency", "immediate", "ex parte", "without notice", "tro",
        "temporary restraining order", "irreparable harm", "imminent"
    ]
    
    # Urgent indicators
    urgent_keywords = [
        "urgent", "expedited", "forthwith", "as soon as possible", "asap",
        "time sensitive", "deadline approaching"
    ]
    
    # High priority indicators
    high_keywords = [
        "sanctions", "contempt", "default", "dismiss", "summary judgment",
        "preliminary injunction", "dispositive"
    ]
    
    if any(keyword in text_lower for keyword in emergency_keywords):
        return UrgencyLevel.EMERGENCY
    elif any(keyword in text_lower for keyword in urgent_keywords):
        return UrgencyLevel.URGENT
    elif any(keyword in text_lower for keyword in high_keywords):
        return UrgencyLevel.HIGH
    else:
        return UrgencyLevel.MEDIUM


def assess_impact_level(filing_type: FilingType, content_indicators: List[str]) -> ImpactLevel:
    """Assess impact level based on filing type and content"""
    
    # High impact filing types
    high_impact_types = {
        FilingType.MOTION_FOR_TEMPORARY_RESTRAINING_ORDER: ImpactLevel.EMERGENCY,
        FilingType.JUDGMENT: ImpactLevel.CRITICAL,
        FilingType.MOTION_FOR_SUMMARY_JUDGMENT: ImpactLevel.HIGH,
        FilingType.MOTION_TO_DISMISS: ImpactLevel.HIGH,
        FilingType.MOTION_FOR_PRELIMINARY_INJUNCTION: ImpactLevel.HIGH,
        FilingType.ORDER: ImpactLevel.HIGH,
        FilingType.MOTION_FOR_SANCTIONS: ImpactLevel.HIGH
    }
    
    # Check filing type impact
    base_impact = high_impact_types.get(filing_type, ImpactLevel.MEDIUM)
    
    # Adjust based on content indicators
    critical_indicators = ["granted", "denied", "dismissed with prejudice", "final judgment"]
    emergency_indicators = ["tro granted", "emergency relief", "immediate harm"]
    
    content_text = " ".join(content_indicators).lower()
    
    if any(indicator in content_text for indicator in emergency_indicators):
        return ImpactLevel.EMERGENCY
    elif any(indicator in content_text for indicator in critical_indicators):
        return max(base_impact, ImpactLevel.CRITICAL)
    
    return base_impact