"""
Analysis Progress Tracker

Tracks the progress of document analysis jobs and provides
real-time status updates for the frontend.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class AnalysisStage(Enum):
    """Stages of the multi-layer analysis pipeline"""
    QUEUED = "queued"
    EXTRACTING_TEXT = "extracting_text"
    LAYER1_EXTRACTION = "layer1_extraction"
    LAYER1_INSPECTION = "layer1_inspection"
    LAYER2_VERIFICATION = "layer2_verification"
    LAYER2_INSPECTION = "layer2_inspection"
    LAYER3_HALLUCINATION = "layer3_hallucination"
    LAYER3_INSPECTION = "layer3_inspection"
    LAYER4_VALIDATION = "layer4_validation"
    EXPERT_REVIEW = "expert_review"
    FINAL_INSPECTION = "final_inspection"
    COMPLETED = "completed"
    FAILED = "failed"


# Stage descriptions for UI display
STAGE_DESCRIPTIONS = {
    AnalysisStage.QUEUED: {
        "title": "Queued",
        "description": "Document queued for analysis",
        "progress": 0
    },
    AnalysisStage.EXTRACTING_TEXT: {
        "title": "Extracting Text",
        "description": "Extracting text content from document",
        "progress": 5
    },
    AnalysisStage.LAYER1_EXTRACTION: {
        "title": "Deep Extraction",
        "description": "Claude Opus analyzing document for comprehensive extraction",
        "progress": 15
    },
    AnalysisStage.LAYER1_INSPECTION: {
        "title": "Extraction Review",
        "description": "Reviewing extraction quality and completeness",
        "progress": 25
    },
    AnalysisStage.LAYER2_VERIFICATION: {
        "title": "Cross-Verification",
        "description": "GPT-4o independently verifying extracted information",
        "progress": 40
    },
    AnalysisStage.LAYER2_INSPECTION: {
        "title": "Verification Review",
        "description": "Comparing results between AI models",
        "progress": 50
    },
    AnalysisStage.LAYER3_HALLUCINATION: {
        "title": "Accuracy Check",
        "description": "Detecting and removing hallucinated information",
        "progress": 60
    },
    AnalysisStage.LAYER3_INSPECTION: {
        "title": "Accuracy Review",
        "description": "Verifying all information against source document",
        "progress": 70
    },
    AnalysisStage.LAYER4_VALIDATION: {
        "title": "Final Validation",
        "description": "Merging verified data and calculating confidence scores",
        "progress": 80
    },
    AnalysisStage.EXPERT_REVIEW: {
        "title": "Expert Analysis",
        "description": "Document-type specific expert review",
        "progress": 90
    },
    AnalysisStage.FINAL_INSPECTION: {
        "title": "Quality Assurance",
        "description": "Final quality check before delivery",
        "progress": 95
    },
    AnalysisStage.COMPLETED: {
        "title": "Complete",
        "description": "Analysis completed successfully",
        "progress": 100
    },
    AnalysisStage.FAILED: {
        "title": "Failed",
        "description": "Analysis encountered an error",
        "progress": 0
    }
}


@dataclass
class HallucinationReport:
    """Details about a detected hallucination and its correction"""
    field_name: str  # Which field had the hallucination (e.g., "parties", "dates", "amounts")
    original_value: Any  # What the AI originally extracted
    corrected_value: Any  # What it was corrected to (or None if removed)
    reason: str  # Why it was flagged as a hallucination
    source_layer: str  # Which layer detected it (e.g., "layer3_hallucination")
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "reason": self.reason,
            "source_layer": self.source_layer,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class AnalysisJob:
    """Represents a document analysis job with progress tracking"""
    job_id: str
    document_id: str
    filename: str
    stage: AnalysisStage = AnalysisStage.QUEUED
    progress: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    # User info
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    # Detailed stage tracking
    stages_completed: List[str] = field(default_factory=list)
    current_stage_detail: str = ""

    # Results
    items_extracted: int = 0
    hallucinations_detected: int = 0
    corrections_made: int = 0
    confidence_score: float = 0.0

    # Detailed hallucination reports
    hallucination_reports: List[HallucinationReport] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        stage_info = STAGE_DESCRIPTIONS.get(self.stage, {})
        elapsed = (datetime.now() - self.started_at).total_seconds()

        # Calculate estimated time remaining based on progress
        estimated_remaining = None
        estimated_total = None
        if self.progress > 0 and self.progress < 100:
            # Estimate total time based on current progress rate
            estimated_total = (elapsed / self.progress) * 100
            estimated_remaining = estimated_total - elapsed
        elif self.stage == AnalysisStage.COMPLETED:
            estimated_remaining = 0
            estimated_total = elapsed

        return {
            "job_id": self.job_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "stage": self.stage.value,
            "stage_title": stage_info.get("title", self.stage.value),
            "stage_description": stage_info.get("description", ""),
            "progress": self.progress,
            "current_stage_detail": self.current_stage_detail,
            "stages_completed": self.stages_completed,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_seconds": round(elapsed, 1),
            "estimated_remaining_seconds": round(estimated_remaining, 1) if estimated_remaining is not None else None,
            "estimated_total_seconds": round(estimated_total, 1) if estimated_total is not None else None,
            "error": self.error,
            "items_extracted": self.items_extracted,
            "hallucinations_detected": self.hallucinations_detected,
            "corrections_made": self.corrections_made,
            "confidence_score": self.confidence_score,
            "is_complete": self.stage == AnalysisStage.COMPLETED,
            "is_failed": self.stage == AnalysisStage.FAILED,
            # User info
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_name": self.user_name,
            # Hallucination details
            "hallucination_reports": [r.to_dict() for r in self.hallucination_reports]
        }


class AnalysisProgressTracker:
    """
    Singleton tracker for all active analysis jobs.
    Thread-safe for concurrent access.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._jobs: Dict[str, AnalysisJob] = {}
                    cls._instance._job_lock = threading.Lock()
        return cls._instance

    def create_job(
        self,
        job_id: str,
        document_id: str,
        filename: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> AnalysisJob:
        """Create a new analysis job"""
        with self._job_lock:
            job = AnalysisJob(
                job_id=job_id,
                document_id=document_id,
                filename=filename,
                user_id=user_id,
                user_email=user_email,
                user_name=user_name
            )
            self._jobs[job_id] = job
            logger.info(f"Created analysis job: {job_id} for {filename} (user: {user_email})")
            return job

    def update_stage(
        self,
        job_id: str,
        stage: AnalysisStage,
        detail: str = "",
        items_extracted: int = None,
        hallucinations: int = None,
        corrections: int = None,
        confidence: float = None
    ) -> Optional[AnalysisJob]:
        """Update the stage of an analysis job"""
        with self._job_lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return None

            # Mark previous stage as completed
            if job.stage != stage and job.stage != AnalysisStage.QUEUED:
                job.stages_completed.append(job.stage.value)

            job.stage = stage
            job.progress = STAGE_DESCRIPTIONS.get(stage, {}).get("progress", 0)
            job.current_stage_detail = detail
            job.updated_at = datetime.now()

            if items_extracted is not None:
                job.items_extracted = items_extracted
            if hallucinations is not None:
                job.hallucinations_detected = hallucinations
            if corrections is not None:
                job.corrections_made = corrections
            if confidence is not None:
                job.confidence_score = confidence

            if stage == AnalysisStage.COMPLETED:
                job.completed_at = datetime.now()
                job.progress = 100

            logger.info(f"Job {job_id} updated: {stage.value} ({job.progress}%)")
            return job

    def fail_job(self, job_id: str, error: str) -> Optional[AnalysisJob]:
        """Mark a job as failed"""
        with self._job_lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            job.stage = AnalysisStage.FAILED
            job.error = error
            job.updated_at = datetime.now()
            job.completed_at = datetime.now()

            logger.error(f"Job {job_id} failed: {error}")
            return job

    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """Get a job by ID"""
        with self._job_lock:
            return self._jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status as dictionary"""
        job = self.get_job(job_id)
        if job:
            return job.to_dict()
        return None

    def cleanup_old_jobs(self, max_age_seconds: int = 3600):
        """Remove jobs older than max_age_seconds"""
        with self._job_lock:
            now = datetime.now()
            expired = [
                job_id for job_id, job in self._jobs.items()
                if (now - job.started_at).total_seconds() > max_age_seconds
            ]
            for job_id in expired:
                del self._jobs[job_id]

            if expired:
                logger.info(f"Cleaned up {len(expired)} old analysis jobs")

    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active (non-completed, non-failed) jobs"""
        with self._job_lock:
            return [
                job.to_dict() for job in self._jobs.values()
                if job.stage not in [AnalysisStage.COMPLETED, AnalysisStage.FAILED]
            ]

    def add_hallucination_report(
        self,
        job_id: str,
        field_name: str,
        original_value: Any,
        corrected_value: Any,
        reason: str,
        source_layer: str
    ) -> bool:
        """Add a hallucination report to a job"""
        with self._job_lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job not found for hallucination report: {job_id}")
                return False

            report = HallucinationReport(
                field_name=field_name,
                original_value=original_value,
                corrected_value=corrected_value,
                reason=reason,
                source_layer=source_layer
            )
            job.hallucination_reports.append(report)
            job.hallucinations_detected = len(job.hallucination_reports)
            logger.info(f"Added hallucination report to job {job_id}: {field_name}")
            return True

    def set_user_info(
        self,
        job_id: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> bool:
        """Set user info for an existing job"""
        with self._job_lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if user_id is not None:
                job.user_id = user_id
            if user_email is not None:
                job.user_email = user_email
            if user_name is not None:
                job.user_name = user_name
            return True


# Singleton instance
progress_tracker = AnalysisProgressTracker()
