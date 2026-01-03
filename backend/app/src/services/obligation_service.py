"""
Obligation Service - Centralized obligation management with plugin architecture
Aggregates obligations from multiple sources with confidence tracking and audit trail
"""

from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ObligationSource(Enum):
    """Source of obligation extraction"""
    AI = "ai"
    MANUAL = "manual"
    TEMPLATE = "template"
    REGEX = "regex"
    HYBRID = "hybrid"  # Combination of sources


class VerificationStatus(Enum):
    """Verification status of obligation"""
    UNVERIFIED = "unverified"
    ATTORNEY_REVIEWED = "attorney_reviewed"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    CORRECTED = "corrected"


class ObligationPriority(Enum):
    """Priority level"""
    CRITICAL = "critical"
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ObligationStatus(Enum):
    """Current status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ObligationMetadata:
    """Metadata for obligation tracking"""
    confidence_score: float  # 0-100
    source: ObligationSource
    extraction_method: str  # Specific method used
    source_text: Optional[str] = None  # Original text if extracted
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: Optional[str] = None  # User ID if manual
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ObligationAuditEntry:
    """Audit trail entry"""
    timestamp: str
    action: str  # created, modified, verified, completed, etc.
    user_id: Optional[str]
    field_changed: Optional[str]
    old_value: Optional[Any]
    new_value: Optional[Any]
    notes: Optional[str] = None


@dataclass
class Obligation:
    """Core obligation model"""
    id: str
    case_id: str
    description: str
    due_date: str  # ISO format or 'TBD'
    priority: ObligationPriority
    status: ObligationStatus
    verification_status: VerificationStatus
    metadata: ObligationMetadata

    # Optional fields
    category: Optional[str] = None
    type: Optional[str] = None
    assigned_to: Optional[str] = None
    evidence_required: List[str] = field(default_factory=list)
    consequences: Optional[str] = None
    completion_date: Optional[str] = None
    completion_notes: Optional[str] = None

    # Audit trail
    audit_trail: List[ObligationAuditEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to values
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['verification_status'] = self.verification_status.value
        data['metadata']['source'] = self.metadata.source.value
        return data

    def add_audit_entry(self, action: str, user_id: Optional[str] = None, **kwargs):
        """Add audit trail entry"""
        entry = ObligationAuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            user_id=user_id,
            **kwargs
        )
        self.audit_trail.append(entry)


# ============================================================================
# EXTRACTOR PROTOCOL
# ============================================================================

class ObligationExtractor(Protocol):
    """Protocol for obligation extractors"""

    @property
    def source_type(self) -> ObligationSource:
        """Return the source type for this extractor"""
        ...

    def extract(self, document_text: str, context: Dict[str, Any]) -> List[Obligation]:
        """Extract obligations from document"""
        ...


# ============================================================================
# EXTRACTOR IMPLEMENTATIONS
# ============================================================================

class AIExtractor:
    """AI-based obligation extraction"""

    @property
    def source_type(self) -> ObligationSource:
        return ObligationSource.AI

    def extract(self, document_text: str, context: Dict[str, Any]) -> List[Obligation]:
        """Extract using AI analysis"""
        obligations = []
        ai_analysis = context.get('ai_analysis', {})
        case_id = context.get('case_id', 'unknown')

        # Extract from AI deadlines
        for deadline in ai_analysis.get('deadlines', []):
            obligation = Obligation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                description=deadline.get('description', 'AI-extracted deadline'),
                due_date=deadline.get('date', 'TBD'),
                priority=ObligationPriority.HIGH,
                status=ObligationStatus.PENDING,
                verification_status=VerificationStatus.UNVERIFIED,
                metadata=ObligationMetadata(
                    confidence_score=85.0,
                    source=ObligationSource.AI,
                    extraction_method="ai_deadline_analysis",
                    source_text=deadline.get('description', '')[:200]
                ),
                category="procedural",
                type="deadline_compliance"
            )
            obligation.add_audit_entry("created", notes="AI extraction")
            obligations.append(obligation)

        # Extract from key dates
        for key_date in ai_analysis.get('key_dates', []):
            obligation = Obligation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                description=key_date.get('description', 'Important date'),
                due_date=key_date.get('date', 'TBD'),
                priority=ObligationPriority.HIGH,
                status=ObligationStatus.PENDING,
                verification_status=VerificationStatus.UNVERIFIED,
                metadata=ObligationMetadata(
                    confidence_score=80.0,
                    source=ObligationSource.AI,
                    extraction_method="ai_key_date_analysis",
                    source_text=key_date.get('description', '')[:200]
                ),
                category="court_appearance",
                type="hearing_or_trial"
            )
            obligation.add_audit_entry("created", notes="AI extraction")
            obligations.append(obligation)

        return obligations


class RegexExtractor:
    """Regex-based obligation extraction"""

    @property
    def source_type(self) -> ObligationSource:
        return ObligationSource.REGEX

    def extract(self, document_text: str, context: Dict[str, Any]) -> List[Obligation]:
        """Extract using regex patterns"""
        import re
        from datetime import timedelta

        obligations = []
        case_id = context.get('case_id', 'unknown')

        # Pattern: "within X days"
        pattern = r'within (\d+) (?:calendar )?days?'
        matches = re.finditer(pattern, document_text, re.IGNORECASE)

        for match in matches:
            days = int(match.group(1))
            due_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

            obligation = Obligation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                description=f"Deadline: Respond within {days} days",
                due_date=due_date,
                priority=ObligationPriority.HIGH if days <= 30 else ObligationPriority.MEDIUM,
                status=ObligationStatus.PENDING,
                verification_status=VerificationStatus.UNVERIFIED,
                metadata=ObligationMetadata(
                    confidence_score=70.0,
                    source=ObligationSource.REGEX,
                    extraction_method="regex_days_pattern",
                    source_text=match.group(0)
                ),
                category="procedural",
                type="deadline_compliance"
            )
            obligation.add_audit_entry("created", notes="Regex extraction")
            obligations.append(obligation)

        return obligations


class TemplateExtractor:
    """Template-based obligation extraction for common case types"""

    @property
    def source_type(self) -> ObligationSource:
        return ObligationSource.TEMPLATE

    def __init__(self):
        self.templates = {
            'complaint': self._complaint_template,
            'motion': self._motion_template,
            'discovery': self._discovery_template
        }

    def extract(self, document_text: str, context: Dict[str, Any]) -> List[Obligation]:
        """Extract using case type templates"""
        from datetime import timedelta

        obligations = []
        case_id = context.get('case_id', 'unknown')
        doc_type = context.get('document_type', '').lower()

        # Find matching template
        template_func = None
        for key, func in self.templates.items():
            if key in doc_type:
                template_func = func
                break

        if template_func:
            template_obligations = template_func(case_id)
            obligations.extend(template_obligations)

        return obligations

    def _complaint_template(self, case_id: str) -> List[Obligation]:
        """Standard obligations for complaint/summons"""
        from datetime import timedelta

        return [
            Obligation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                description="File responsive pleading (Answer or Motion to Dismiss)",
                due_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                priority=ObligationPriority.URGENT,
                status=ObligationStatus.PENDING,
                verification_status=VerificationStatus.UNVERIFIED,
                metadata=ObligationMetadata(
                    confidence_score=90.0,
                    source=ObligationSource.TEMPLATE,
                    extraction_method="complaint_standard_template"
                ),
                category="procedural",
                type="responsive_pleading",
                evidence_required=["Responsive pleading filed", "Proof of service"],
                consequences="Default judgment may be entered"
            ),
            Obligation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                description="Initial client consultation and case assessment",
                due_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                priority=ObligationPriority.HIGH,
                status=ObligationStatus.PENDING,
                verification_status=VerificationStatus.UNVERIFIED,
                metadata=ObligationMetadata(
                    confidence_score=95.0,
                    source=ObligationSource.TEMPLATE,
                    extraction_method="complaint_standard_template"
                ),
                category="client_communication",
                type="consultation"
            )
        ]

    def _motion_template(self, case_id: str) -> List[Obligation]:
        """Standard obligations for motions"""
        from datetime import timedelta

        return [
            Obligation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                description="File opposition to motion (if appropriate)",
                due_date=(datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d"),
                priority=ObligationPriority.HIGH,
                status=ObligationStatus.PENDING,
                verification_status=VerificationStatus.UNVERIFIED,
                metadata=ObligationMetadata(
                    confidence_score=85.0,
                    source=ObligationSource.TEMPLATE,
                    extraction_method="motion_standard_template"
                ),
                category="procedural",
                type="motion_response"
            )
        ]

    def _discovery_template(self, case_id: str) -> List[Obligation]:
        """Standard obligations for discovery"""
        from datetime import timedelta

        return [
            Obligation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                description="Respond to discovery requests",
                due_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                priority=ObligationPriority.HIGH,
                status=ObligationStatus.PENDING,
                verification_status=VerificationStatus.UNVERIFIED,
                metadata=ObligationMetadata(
                    confidence_score=90.0,
                    source=ObligationSource.TEMPLATE,
                    extraction_method="discovery_standard_template"
                ),
                category="discovery",
                type="discovery_response"
            )
        ]


class ManualExtractor:
    """Manual obligation entry"""

    @property
    def source_type(self) -> ObligationSource:
        return ObligationSource.MANUAL

    def create_manual_obligation(self, case_id: str, data: Dict[str, Any], user_id: str) -> Obligation:
        """Create manually entered obligation"""

        obligation = Obligation(
            id=str(uuid.uuid4()),
            case_id=case_id,
            description=data.get('description', 'Manual obligation'),
            due_date=data.get('due_date', 'TBD'),
            priority=ObligationPriority(data.get('priority', 'medium')),
            status=ObligationStatus.PENDING,
            verification_status=VerificationStatus.CONFIRMED,  # Manual is pre-confirmed
            metadata=ObligationMetadata(
                confidence_score=100.0,
                source=ObligationSource.MANUAL,
                extraction_method="manual_user_entry",
                created_by=user_id,
                notes=data.get('notes')
            ),
            category=data.get('category'),
            type=data.get('type'),
            evidence_required=data.get('evidence_required', []),
            consequences=data.get('consequences')
        )
        obligation.add_audit_entry("created", user_id=user_id, notes="Manual entry")
        return obligation


# ============================================================================
# OBLIGATION SERVICE
# ============================================================================

class ObligationService:
    """Central service for obligation management"""

    def __init__(self):
        self.extractors: List[ObligationExtractor] = [
            AIExtractor(),
            RegexExtractor(),
            TemplateExtractor()
        ]
        self.manual_extractor = ManualExtractor()

        # In-memory storage (replace with database in production)
        self.obligations: Dict[str, Obligation] = {}
        self.case_obligations: Dict[str, List[str]] = {}  # case_id -> [obligation_ids]

    def extract_all(self, document_text: str, context: Dict[str, Any]) -> List[Obligation]:
        """Extract obligations from all sources"""
        all_obligations = []

        for extractor in self.extractors:
            try:
                obligations = extractor.extract(document_text, context)
                logger.info(f"{extractor.source_type.value} extracted {len(obligations)} obligations")
                all_obligations.extend(obligations)
            except Exception as e:
                logger.error(f"Error in {extractor.source_type.value} extraction: {e}")

        # Deduplicate based on description and due date
        unique_obligations = self._deduplicate(all_obligations)

        # Store obligations
        for obligation in unique_obligations:
            self.obligations[obligation.id] = obligation
            case_id = obligation.case_id
            if case_id not in self.case_obligations:
                self.case_obligations[case_id] = []
            self.case_obligations[case_id].append(obligation.id)

        return unique_obligations

    def _deduplicate(self, obligations: List[Obligation]) -> List[Obligation]:
        """Deduplicate obligations, keeping highest confidence"""
        seen = {}

        for obligation in obligations:
            key = (obligation.description.lower(), obligation.due_date)

            if key not in seen:
                seen[key] = obligation
            else:
                # Keep higher confidence
                if obligation.metadata.confidence_score > seen[key].metadata.confidence_score:
                    # Create hybrid
                    seen[key].metadata.source = ObligationSource.HYBRID
                    seen[key].metadata.confidence_score = max(
                        seen[key].metadata.confidence_score,
                        obligation.metadata.confidence_score
                    )
                    seen[key].add_audit_entry(
                        "merged",
                        notes=f"Merged with {obligation.metadata.source.value} source"
                    )

        return list(seen.values())

    def add_manual_obligation(self, case_id: str, data: Dict[str, Any], user_id: str) -> Obligation:
        """Add manually created obligation"""
        obligation = self.manual_extractor.create_manual_obligation(case_id, data, user_id)

        self.obligations[obligation.id] = obligation
        if case_id not in self.case_obligations:
            self.case_obligations[case_id] = []
        self.case_obligations[case_id].append(obligation.id)

        return obligation

    def get_case_obligations(self, case_id: str) -> List[Obligation]:
        """Get all obligations for a case"""
        obligation_ids = self.case_obligations.get(case_id, [])
        return [self.obligations[oid] for oid in obligation_ids if oid in self.obligations]

    def update_obligation(self, obligation_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Obligation:
        """Update obligation with audit trail"""
        if obligation_id not in self.obligations:
            raise ValueError(f"Obligation {obligation_id} not found")

        obligation = self.obligations[obligation_id]

        for field, new_value in updates.items():
            old_value = getattr(obligation, field, None)
            setattr(obligation, field, new_value)
            obligation.add_audit_entry(
                "modified",
                user_id=user_id,
                field_changed=field,
                old_value=old_value,
                new_value=new_value
            )

        return obligation

    def verify_obligation(self, obligation_id: str, user_id: str, status: VerificationStatus) -> Obligation:
        """Verify an obligation"""
        obligation = self.obligations[obligation_id]
        obligation.verification_status = status
        obligation.metadata.verified_at = datetime.now().isoformat()
        obligation.metadata.verified_by = user_id
        obligation.add_audit_entry(
            "verified",
            user_id=user_id,
            field_changed="verification_status",
            new_value=status.value
        )
        return obligation

    def complete_obligation(self, obligation_id: str, user_id: str, notes: Optional[str] = None) -> Obligation:
        """Mark obligation as completed"""
        obligation = self.obligations[obligation_id]
        obligation.status = ObligationStatus.COMPLETED
        obligation.completion_date = datetime.now().isoformat()
        obligation.completion_notes = notes
        obligation.add_audit_entry(
            "completed",
            user_id=user_id,
            notes=notes
        )
        return obligation

    def get_audit_trail(self, obligation_id: str) -> List[ObligationAuditEntry]:
        """Get audit trail for obligation"""
        if obligation_id not in self.obligations:
            return []
        return self.obligations[obligation_id].audit_trail


# Global service instance
obligation_service = ObligationService()
