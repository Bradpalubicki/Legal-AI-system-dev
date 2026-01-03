"""
Analysis Audit Trail - Comprehensive documentation of document analysis

This module provides:
1. Full audit trail of every analysis stage
2. Hallucination detection and correction tracking
3. Before/after snapshots of corrections
4. Queryable audit data for compliance and debugging
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""
    STAGE_START = "stage_start"
    STAGE_COMPLETE = "stage_complete"
    STAGE_ERROR = "stage_error"
    HALLUCINATION_DETECTED = "hallucination_detected"
    HALLUCINATION_CORRECTED = "hallucination_corrected"
    HALLUCINATION_REMOVED = "hallucination_removed"
    FALSE_POSITIVE_RESTORED = "false_positive_restored"
    CORRECTION_APPLIED = "correction_applied"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    EXPERT_CORRECTION = "expert_correction"
    CROSS_VALIDATION_ISSUE = "cross_validation_issue"
    DATA_MERGED = "data_merged"
    CONFIDENCE_ADJUSTED = "confidence_adjusted"


@dataclass
class AuditEvent:
    """Single audit event with full context"""
    event_type: AuditEventType
    stage: str
    timestamp: datetime
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    before_value: Optional[Any] = None
    after_value: Optional[Any] = None
    model_used: Optional[str] = None
    confidence_impact: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type.value,
            "stage": self.stage,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "details": self.details,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "model_used": self.model_used,
            "confidence_impact": self.confidence_impact
        }


@dataclass
class HallucinationRecord:
    """Detailed record of a detected hallucination"""
    hallucination_id: str
    detected_at_stage: str
    item_type: str  # party, date, amount, etc.
    original_value: Any
    reason_flagged: str
    detection_method: str  # rule_based, ai_verification, cross_validation
    action_taken: str  # removed, corrected, restored_as_false_positive
    corrected_value: Optional[Any] = None
    correction_source: Optional[str] = None  # layer2, expert_review, etc.
    verified_in_document: bool = False
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "hallucination_id": self.hallucination_id,
            "detected_at_stage": self.detected_at_stage,
            "item_type": self.item_type,
            "original_value": self.original_value,
            "reason_flagged": self.reason_flagged,
            "detection_method": self.detection_method,
            "action_taken": self.action_taken,
            "corrected_value": self.corrected_value,
            "correction_source": self.correction_source,
            "verified_in_document": self.verified_in_document,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CorrectionRecord:
    """Record of a correction applied during analysis"""
    correction_id: str
    stage: str
    field_path: str  # e.g., "monetary_amounts[0].amount"
    original_value: Any
    corrected_value: Any
    correction_reason: str
    correction_source: str  # layer2_verification, expert_review, cross_validation
    verified_against_document: bool
    document_evidence: Optional[str] = None  # excerpt from document proving correction
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "correction_id": self.correction_id,
            "stage": self.stage,
            "field_path": self.field_path,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "correction_reason": self.correction_reason,
            "correction_source": self.correction_source,
            "verified_against_document": self.verified_against_document,
            "document_evidence": self.document_evidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class StageSnapshot:
    """Snapshot of data at a specific stage"""
    stage_name: str
    stage_number: int
    model_used: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: float = 0.0
    status: str = "in_progress"
    input_summary: Dict[str, Any] = field(default_factory=dict)
    output_summary: Dict[str, Any] = field(default_factory=dict)
    items_extracted: int = 0
    items_verified: int = 0
    items_flagged: int = 0
    items_corrected: int = 0
    items_removed: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "stage_name": self.stage_name,
            "stage_number": self.stage_number,
            "model_used": self.model_used,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time_seconds": self.processing_time_seconds,
            "status": self.status,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "items_extracted": self.items_extracted,
            "items_verified": self.items_verified,
            "items_flagged": self.items_flagged,
            "items_corrected": self.items_corrected,
            "items_removed": self.items_removed,
            "warnings": self.warnings,
            "errors": self.errors
        }


class AnalysisAuditTrail:
    """
    Complete audit trail for a document analysis.
    Tracks every stage, hallucination, correction, and validation.
    """

    def __init__(self, document_id: str, filename: str):
        self.document_id = document_id
        self.filename = filename
        self.analysis_id = f"audit_{document_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

        # Audit data
        self.events: List[AuditEvent] = []
        self.hallucinations: List[HallucinationRecord] = []
        self.corrections: List[CorrectionRecord] = []
        self.stage_snapshots: List[StageSnapshot] = []

        # Tracking
        self.current_stage: Optional[StageSnapshot] = None
        self._hallucination_counter = 0
        self._correction_counter = 0

        # Summary stats
        self.total_hallucinations_detected = 0
        self.total_hallucinations_corrected = 0
        self.total_hallucinations_removed = 0
        self.total_false_positives = 0
        self.total_corrections_applied = 0
        self.initial_confidence: Optional[float] = None
        self.final_confidence: Optional[float] = None

    def start_stage(self, stage_name: str, stage_number: int, model: str,
                   input_data: Optional[Dict] = None) -> StageSnapshot:
        """Start tracking a new analysis stage"""
        snapshot = StageSnapshot(
            stage_name=stage_name,
            stage_number=stage_number,
            model_used=model,
            started_at=datetime.utcnow(),
            input_summary=self._summarize_data(input_data) if input_data else {}
        )
        self.current_stage = snapshot
        self.stage_snapshots.append(snapshot)

        self._log_event(
            AuditEventType.STAGE_START,
            stage_name,
            f"Started {stage_name} using {model}",
            {"stage_number": stage_number}
        )

        return snapshot

    def complete_stage(self, output_data: Optional[Dict] = None,
                      items_extracted: int = 0, items_verified: int = 0,
                      items_flagged: int = 0, items_corrected: int = 0,
                      items_removed: int = 0, warnings: List[str] = None):
        """Complete the current stage with results"""
        if not self.current_stage:
            return

        self.current_stage.completed_at = datetime.utcnow()
        self.current_stage.processing_time_seconds = (
            self.current_stage.completed_at - self.current_stage.started_at
        ).total_seconds()
        self.current_stage.status = "completed"
        self.current_stage.output_summary = self._summarize_data(output_data) if output_data else {}
        self.current_stage.items_extracted = items_extracted
        self.current_stage.items_verified = items_verified
        self.current_stage.items_flagged = items_flagged
        self.current_stage.items_corrected = items_corrected
        self.current_stage.items_removed = items_removed
        self.current_stage.warnings = warnings or []

        self._log_event(
            AuditEventType.STAGE_COMPLETE,
            self.current_stage.stage_name,
            f"Completed {self.current_stage.stage_name} in {self.current_stage.processing_time_seconds:.1f}s",
            {
                "items_extracted": items_extracted,
                "items_verified": items_verified,
                "items_flagged": items_flagged,
                "items_corrected": items_corrected,
                "items_removed": items_removed
            },
            model_used=self.current_stage.model_used
        )

    def record_hallucination(
        self,
        stage: str,
        item_type: str,
        original_value: Any,
        reason: str,
        detection_method: str = "rule_based",
        corrected_value: Any = None,
        correction_source: str = None,
        document_text: str = None
    ) -> HallucinationRecord:
        """Record a detected hallucination with full details"""
        self._hallucination_counter += 1
        hall_id = f"hall_{self.document_id}_{self._hallucination_counter}"

        # Determine action taken
        if corrected_value is not None:
            action = "corrected"
            self.total_hallucinations_corrected += 1
        else:
            action = "removed"
            self.total_hallucinations_removed += 1

        self.total_hallucinations_detected += 1

        # Check if value exists in document
        verified = False
        if document_text and original_value:
            verified = str(original_value) in document_text

        record = HallucinationRecord(
            hallucination_id=hall_id,
            detected_at_stage=stage,
            item_type=item_type,
            original_value=original_value,
            reason_flagged=reason,
            detection_method=detection_method,
            action_taken=action,
            corrected_value=corrected_value,
            correction_source=correction_source,
            verified_in_document=verified
        )
        self.hallucinations.append(record)

        # Log event
        event_type = (AuditEventType.HALLUCINATION_CORRECTED if corrected_value
                     else AuditEventType.HALLUCINATION_REMOVED)
        self._log_event(
            event_type,
            stage,
            f"Hallucination {action}: {item_type} '{original_value}' - {reason}",
            {
                "item_type": item_type,
                "detection_method": detection_method,
                "correction_source": correction_source
            },
            before_value=original_value,
            after_value=corrected_value
        )

        return record

    def record_false_positive(self, stage: str, item_type: str, value: Any,
                             reason_restored: str):
        """Record when a flagged item is restored as a false positive"""
        self.total_false_positives += 1

        self._log_event(
            AuditEventType.FALSE_POSITIVE_RESTORED,
            stage,
            f"False positive restored: {item_type} '{value}'",
            {
                "item_type": item_type,
                "reason_restored": reason_restored
            }
        )

    def record_correction(
        self,
        stage: str,
        field_path: str,
        original_value: Any,
        corrected_value: Any,
        reason: str,
        source: str,
        document_text: str = None
    ) -> CorrectionRecord:
        """Record a correction applied during analysis"""
        self._correction_counter += 1
        corr_id = f"corr_{self.document_id}_{self._correction_counter}"

        # Find document evidence if possible
        evidence = None
        if document_text and corrected_value:
            # Try to find the corrected value in the document
            corrected_str = str(corrected_value)
            if corrected_str in document_text:
                idx = document_text.find(corrected_str)
                start = max(0, idx - 50)
                end = min(len(document_text), idx + len(corrected_str) + 50)
                evidence = f"...{document_text[start:end]}..."

        record = CorrectionRecord(
            correction_id=corr_id,
            stage=stage,
            field_path=field_path,
            original_value=original_value,
            corrected_value=corrected_value,
            correction_reason=reason,
            correction_source=source,
            verified_against_document=evidence is not None,
            document_evidence=evidence
        )
        self.corrections.append(record)
        self.total_corrections_applied += 1

        self._log_event(
            AuditEventType.CORRECTION_APPLIED,
            stage,
            f"Correction: {field_path} changed from '{original_value}' to '{corrected_value}'",
            {
                "field_path": field_path,
                "reason": reason,
                "source": source,
                "verified": evidence is not None
            },
            before_value=original_value,
            after_value=corrected_value
        )

        return record

    def record_confidence_change(self, stage: str, before: float, after: float,
                                reason: str):
        """Record a confidence score adjustment"""
        impact = after - before

        self._log_event(
            AuditEventType.CONFIDENCE_ADJUSTED,
            stage,
            f"Confidence adjusted: {before:.1f}% → {after:.1f}% ({impact:+.1f}%)",
            {"reason": reason},
            before_value=before,
            after_value=after,
            confidence_impact=impact
        )

    def record_cross_validation_issue(self, stage: str, issue_type: str,
                                      details: Dict[str, Any]):
        """Record a cross-validation issue found"""
        self._log_event(
            AuditEventType.CROSS_VALIDATION_ISSUE,
            stage,
            f"Cross-validation issue: {issue_type}",
            details
        )

    def complete_analysis(self, final_confidence: float):
        """Mark analysis as complete and finalize audit"""
        self.completed_at = datetime.utcnow()
        self.final_confidence = final_confidence

        logger.info(
            f"Analysis audit complete for {self.document_id}: "
            f"{self.total_hallucinations_detected} hallucinations detected, "
            f"{self.total_corrections_applied} corrections applied, "
            f"confidence: {self.initial_confidence}% → {final_confidence}%"
        )

    def _log_event(self, event_type: AuditEventType, stage: str,
                  description: str, details: Dict = None,
                  before_value: Any = None, after_value: Any = None,
                  model_used: str = None, confidence_impact: float = None):
        """Log an audit event"""
        event = AuditEvent(
            event_type=event_type,
            stage=stage,
            timestamp=datetime.utcnow(),
            description=description,
            details=details or {},
            before_value=before_value,
            after_value=after_value,
            model_used=model_used,
            confidence_impact=confidence_impact
        )
        self.events.append(event)

    def _summarize_data(self, data: Dict) -> Dict:
        """Create a summary of data for audit (avoid storing full content)"""
        if not data:
            return {}

        summary = {}
        for key, value in data.items():
            if isinstance(value, list):
                summary[key] = f"{len(value)} items"
            elif isinstance(value, dict):
                summary[key] = f"{len(value)} fields"
            elif isinstance(value, str) and len(value) > 100:
                summary[key] = f"{len(value)} chars"
            else:
                summary[key] = value

        return summary

    def to_dict(self) -> Dict:
        """Convert full audit trail to dictionary"""
        return {
            "analysis_id": self.analysis_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_processing_time_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at else None
            ),

            # Summary statistics
            "summary": {
                "total_stages": len(self.stage_snapshots),
                "total_events": len(self.events),
                "hallucinations_detected": self.total_hallucinations_detected,
                "hallucinations_corrected": self.total_hallucinations_corrected,
                "hallucinations_removed": self.total_hallucinations_removed,
                "false_positives": self.total_false_positives,
                "corrections_applied": self.total_corrections_applied,
                "initial_confidence": self.initial_confidence,
                "final_confidence": self.final_confidence
            },

            # Detailed records
            "stages": [s.to_dict() for s in self.stage_snapshots],
            "hallucinations": [h.to_dict() for h in self.hallucinations],
            "corrections": [c.to_dict() for c in self.corrections],
            "events": [e.to_dict() for e in self.events]
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert audit trail to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def get_hallucination_summary(self) -> Dict:
        """Get a summary of all hallucinations for quick review"""
        return {
            "total_detected": self.total_hallucinations_detected,
            "corrected": self.total_hallucinations_corrected,
            "removed": self.total_hallucinations_removed,
            "false_positives": self.total_false_positives,
            "by_type": self._group_hallucinations_by_type(),
            "by_stage": self._group_hallucinations_by_stage(),
            "details": [h.to_dict() for h in self.hallucinations]
        }

    def get_correction_summary(self) -> Dict:
        """Get a summary of all corrections for quick review"""
        return {
            "total_corrections": self.total_corrections_applied,
            "by_source": self._group_corrections_by_source(),
            "by_field": self._group_corrections_by_field(),
            "verified_count": sum(1 for c in self.corrections if c.verified_against_document),
            "details": [c.to_dict() for c in self.corrections]
        }

    def _group_hallucinations_by_type(self) -> Dict[str, int]:
        counts = {}
        for h in self.hallucinations:
            counts[h.item_type] = counts.get(h.item_type, 0) + 1
        return counts

    def _group_hallucinations_by_stage(self) -> Dict[str, int]:
        counts = {}
        for h in self.hallucinations:
            counts[h.detected_at_stage] = counts.get(h.detected_at_stage, 0) + 1
        return counts

    def _group_corrections_by_source(self) -> Dict[str, int]:
        counts = {}
        for c in self.corrections:
            counts[c.correction_source] = counts.get(c.correction_source, 0) + 1
        return counts

    def _group_corrections_by_field(self) -> Dict[str, int]:
        counts = {}
        for c in self.corrections:
            # Extract base field name (e.g., "monetary_amounts" from "monetary_amounts[0].amount")
            base_field = c.field_path.split('[')[0].split('.')[0]
            counts[base_field] = counts.get(base_field, 0) + 1
        return counts
