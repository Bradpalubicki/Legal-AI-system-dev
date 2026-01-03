from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import statistics
import logging
from collections import defaultdict, Counter
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    ACCURACY = "accuracy"
    USEFULNESS = "usefulness"
    ERROR_REPORT = "error_report"
    SUGGESTION = "suggestion"
    CORRECTION = "correction"
    GENERAL = "general"


class AccuracyRating(str, Enum):
    COMPLETELY_ACCURATE = "completely_accurate"
    MOSTLY_ACCURATE = "mostly_accurate"
    PARTIALLY_ACCURATE = "partially_accurate"
    MOSTLY_INACCURATE = "mostly_inaccurate"
    COMPLETELY_INACCURATE = "completely_inaccurate"


class UsefulnessRating(str, Enum):
    VERY_USEFUL = "very_useful"
    SOMEWHAT_USEFUL = "somewhat_useful"
    NEUTRAL = "neutral"
    NOT_VERY_USEFUL = "not_very_useful"
    NOT_USEFUL = "not_useful"


class ErrorSeverity(str, Enum):
    CRITICAL = "critical"  # Wrong legal advice, major factual errors
    HIGH = "high"        # Significant inaccuracies, misleading information
    MEDIUM = "medium"    # Minor inaccuracies, unclear explanations
    LOW = "low"         # Formatting issues, minor typos


class CorrectionStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class DocumentType(str, Enum):
    CONTRACT_ANALYSIS = "contract_analysis"
    LEGAL_RESEARCH = "legal_research"
    CASE_SUMMARY = "case_summary"
    LEGAL_MEMO = "legal_memo"
    DOCUMENT_REVIEW = "document_review"
    CITATION_ANALYSIS = "citation_analysis"
    DEADLINE_CALCULATION = "deadline_calculation"
    GENERAL_GUIDANCE = "general_guidance"


@dataclass
class UserFeedback:
    id: str
    user_id: str
    session_id: str
    content_id: str  # ID of the AI output being reviewed
    feedback_type: FeedbackType
    rating: Optional[Union[AccuracyRating, UsefulnessRating]] = None
    comment: Optional[str] = None
    specific_issues: List[str] = field(default_factory=list)
    suggestions: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    document_type: Optional[DocumentType] = None
    attorney_reviewed: bool = False
    resolved: bool = False


@dataclass
class ErrorReport:
    id: str
    user_id: str
    content_id: str
    error_type: str
    severity: ErrorSeverity
    description: str
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    browser_info: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    status: str = "open"
    resolution: Optional[str] = None


@dataclass
class Correction:
    id: str
    user_id: str
    attorney_id: str
    content_id: str
    original_content: str
    corrected_content: str
    correction_reason: str
    correction_type: str  # factual, legal_accuracy, clarity, etc.
    document_type: DocumentType
    status: CorrectionStatus
    reviewer_notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    user_notified: bool = False


@dataclass
class QualityMetric:
    metric_name: str
    value: float
    period_start: datetime
    period_end: datetime
    document_type: Optional[DocumentType] = None
    sample_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeedbackCollector:
    """
    Collects and manages user feedback on AI outputs including
    accuracy ratings, usefulness scores, and error reports.
    """
    
    def __init__(self):
        self._feedback_storage = {}  # feedback_id -> UserFeedback
        self._error_reports = {}     # error_id -> ErrorReport
        self._feedback_by_content = defaultdict(list)  # content_id -> [feedback_ids]
        self._feedback_by_user = defaultdict(list)     # user_id -> [feedback_ids]
        self._notification_queue = []
        
    def submit_accuracy_feedback(
        self, 
        user_id: str, 
        content_id: str, 
        rating: AccuracyRating,
        comment: Optional[str] = None,
        specific_issues: List[str] = None,
        document_type: Optional[DocumentType] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Submit accuracy feedback for AI-generated content"""
        
        feedback_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        feedback = UserFeedback(
            id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            content_id=content_id,
            feedback_type=FeedbackType.ACCURACY,
            rating=rating,
            comment=comment,
            specific_issues=specific_issues or [],
            document_type=document_type,
            context={
                "rating_scale": "5_point_accuracy",
                "submission_method": "user_interface"
            }
        )
        
        # Store feedback
        self._feedback_storage[feedback_id] = feedback
        self._feedback_by_content[content_id].append(feedback_id)
        self._feedback_by_user[user_id].append(feedback_id)
        
        # Log critical accuracy issues
        if rating in [AccuracyRating.MOSTLY_INACCURATE, AccuracyRating.COMPLETELY_INACCURATE]:
            logger.warning(f"Critical accuracy feedback received for content {content_id}: {rating}")
            self._queue_for_attorney_review(feedback_id)
        
        logger.info(f"Accuracy feedback submitted: {feedback_id} by user {user_id}")
        return feedback_id
    
    def submit_usefulness_feedback(
        self,
        user_id: str,
        content_id: str,
        rating: UsefulnessRating,
        comment: Optional[str] = None,
        suggestions: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Submit usefulness feedback for AI-generated content"""
        
        feedback_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        feedback = UserFeedback(
            id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            content_id=content_id,
            feedback_type=FeedbackType.USEFULNESS,
            rating=rating,
            comment=comment,
            suggestions=suggestions,
            document_type=document_type,
            context={
                "rating_scale": "5_point_usefulness",
                "submission_method": "user_interface"
            }
        )
        
        # Store feedback
        self._feedback_storage[feedback_id] = feedback
        self._feedback_by_content[content_id].append(feedback_id)
        self._feedback_by_user[user_id].append(feedback_id)
        
        logger.info(f"Usefulness feedback submitted: {feedback_id} by user {user_id}")
        return feedback_id
    
    def report_error(
        self,
        user_id: str,
        content_id: str,
        error_type: str,
        severity: ErrorSeverity,
        description: str,
        steps_to_reproduce: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        actual_behavior: Optional[str] = None,
        browser_info: Optional[str] = None
    ) -> str:
        """Submit an error report"""
        
        error_id = str(uuid.uuid4())
        
        error_report = ErrorReport(
            id=error_id,
            user_id=user_id,
            content_id=content_id,
            error_type=error_type,
            severity=severity,
            description=description,
            steps_to_reproduce=steps_to_reproduce,
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior,
            browser_info=browser_info
        )
        
        # Store error report
        self._error_reports[error_id] = error_report
        
        # Auto-assign critical errors
        if severity == ErrorSeverity.CRITICAL:
            error_report.assigned_to = "legal_team_lead"
            logger.critical(f"Critical error reported: {error_id} - {description}")
        
        logger.info(f"Error report submitted: {error_id} by user {user_id}")
        return error_id
    
    def submit_general_suggestion(
        self,
        user_id: str,
        suggestion: str,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Submit a general suggestion for system improvement"""
        
        feedback_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        feedback = UserFeedback(
            id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            content_id="general_system",
            feedback_type=FeedbackType.SUGGESTION,
            suggestions=suggestion,
            context={
                "category": category,
                "priority": priority,
                "submission_method": "suggestion_form"
            }
        )
        
        # Store feedback
        self._feedback_storage[feedback_id] = feedback
        self._feedback_by_user[user_id].append(feedback_id)
        
        logger.info(f"General suggestion submitted: {feedback_id} by user {user_id}")
        return feedback_id
    
    def get_content_feedback_summary(self, content_id: str) -> Dict[str, Any]:
        """Get feedback summary for specific content"""
        
        feedback_ids = self._feedback_by_content.get(content_id, [])
        if not feedback_ids:
            return {"error": "No feedback found for this content"}
        
        feedbacks = [self._feedback_storage[fid] for fid in feedback_ids]
        
        # Analyze accuracy feedback
        accuracy_feedbacks = [f for f in feedbacks if f.feedback_type == FeedbackType.ACCURACY]
        accuracy_summary = {}
        if accuracy_feedbacks:
            accuracy_ratings = [f.rating.value for f in accuracy_feedbacks if f.rating]
            accuracy_summary = {
                "total_responses": len(accuracy_feedbacks),
                "rating_distribution": dict(Counter(accuracy_ratings)),
                "average_score": self._calculate_accuracy_score(accuracy_ratings),
                "common_issues": self._extract_common_issues(accuracy_feedbacks)
            }
        
        # Analyze usefulness feedback
        usefulness_feedbacks = [f for f in feedbacks if f.feedback_type == FeedbackType.USEFULNESS]
        usefulness_summary = {}
        if usefulness_feedbacks:
            usefulness_ratings = [f.rating.value for f in usefulness_feedbacks if f.rating]
            usefulness_summary = {
                "total_responses": len(usefulness_feedbacks),
                "rating_distribution": dict(Counter(usefulness_ratings)),
                "average_score": self._calculate_usefulness_score(usefulness_ratings),
                "suggestions": [f.suggestions for f in usefulness_feedbacks if f.suggestions]
            }
        
        return {
            "content_id": content_id,
            "total_feedback_items": len(feedbacks),
            "accuracy": accuracy_summary,
            "usefulness": usefulness_summary,
            "last_updated": max(f.timestamp for f in feedbacks) if feedbacks else None
        }
    
    def get_user_feedback_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's feedback history"""
        
        feedback_ids = self._feedback_by_user.get(user_id, [])
        feedbacks = [self._feedback_storage[fid] for fid in feedback_ids[-limit:]]
        
        return [
            {
                "id": f.id,
                "content_id": f.content_id,
                "feedback_type": f.feedback_type.value,
                "rating": f.rating.value if f.rating else None,
                "comment": f.comment,
                "timestamp": f.timestamp,
                "resolved": f.resolved
            }
            for f in sorted(feedbacks, key=lambda x: x.timestamp, reverse=True)
        ]
    
    def _queue_for_attorney_review(self, feedback_id: str):
        """Queue feedback for attorney review"""
        feedback = self._feedback_storage.get(feedback_id)
        if feedback:
            feedback.attorney_reviewed = False
            self._notification_queue.append({
                "type": "attorney_review_needed",
                "feedback_id": feedback_id,
                "priority": "high",
                "timestamp": datetime.now()
            })
    
    def _calculate_accuracy_score(self, ratings: List[str]) -> float:
        """Convert accuracy ratings to numerical scores (1-5)"""
        score_map = {
            "completely_accurate": 5,
            "mostly_accurate": 4,
            "partially_accurate": 3,
            "mostly_inaccurate": 2,
            "completely_inaccurate": 1
        }
        scores = [score_map.get(rating, 3) for rating in ratings]
        return statistics.mean(scores) if scores else 0.0
    
    def _calculate_usefulness_score(self, ratings: List[str]) -> float:
        """Convert usefulness ratings to numerical scores (1-5)"""
        score_map = {
            "very_useful": 5,
            "somewhat_useful": 4,
            "neutral": 3,
            "not_very_useful": 2,
            "not_useful": 1
        }
        scores = [score_map.get(rating, 3) for rating in ratings]
        return statistics.mean(scores) if scores else 0.0
    
    def _extract_common_issues(self, feedbacks: List[UserFeedback]) -> List[str]:
        """Extract common issues from feedback comments"""
        all_issues = []
        for feedback in feedbacks:
            all_issues.extend(feedback.specific_issues)
        
        issue_counts = Counter(all_issues)
        return [issue for issue, count in issue_counts.most_common(5)]


class CorrectionWorkflow:
    """
    Manages the attorney correction workflow including review queues,
    approval processes, and model retraining data collection.
    """
    
    def __init__(self, feedback_collector: FeedbackCollector):
        self.feedback_collector = feedback_collector
        self._corrections = {}  # correction_id -> Correction
        self._review_queue = []  # List of correction_ids awaiting review
        self._correction_by_content = defaultdict(list)  # content_id -> [correction_ids]
        self._correction_by_attorney = defaultdict(list)  # attorney_id -> [correction_ids]
        self._retraining_data = []  # Approved corrections for model retraining
        
    def submit_correction(
        self,
        user_id: str,
        attorney_id: str,
        content_id: str,
        original_content: str,
        corrected_content: str,
        correction_reason: str,
        correction_type: str,
        document_type: DocumentType
    ) -> str:
        """Submit a correction from an attorney"""
        
        correction_id = str(uuid.uuid4())
        
        correction = Correction(
            id=correction_id,
            user_id=user_id,
            attorney_id=attorney_id,
            content_id=content_id,
            original_content=original_content,
            corrected_content=corrected_content,
            correction_reason=correction_reason,
            correction_type=correction_type,
            document_type=document_type,
            status=CorrectionStatus.SUBMITTED
        )
        
        # Store correction
        self._corrections[correction_id] = correction
        self._correction_by_content[content_id].append(correction_id)
        self._correction_by_attorney[attorney_id].append(correction_id)
        
        # Add to review queue
        self._review_queue.append(correction_id)
        
        # Update status
        correction.status = CorrectionStatus.UNDER_REVIEW
        
        logger.info(f"Correction submitted: {correction_id} by attorney {attorney_id}")
        return correction_id
    
    def get_review_queue(self, attorney_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get corrections awaiting review"""
        
        # Filter by attorney if specified
        if attorney_id:
            queue_items = [
                cid for cid in self._review_queue 
                if self._corrections[cid].attorney_id == attorney_id
            ]
        else:
            queue_items = self._review_queue
        
        # Get correction details
        corrections = []
        for correction_id in queue_items[:limit]:
            correction = self._corrections.get(correction_id)
            if correction and correction.status == CorrectionStatus.UNDER_REVIEW:
                corrections.append({
                    "id": correction.id,
                    "content_id": correction.content_id,
                    "attorney_id": correction.attorney_id,
                    "correction_type": correction.correction_type,
                    "correction_reason": correction.correction_reason,
                    "document_type": correction.document_type.value,
                    "timestamp": correction.timestamp,
                    "status": correction.status.value,
                    "original_length": len(correction.original_content),
                    "corrected_length": len(correction.corrected_content)
                })
        
        return sorted(corrections, key=lambda x: x["timestamp"])
    
    def approve_correction(
        self,
        correction_id: str,
        approver_id: str,
        reviewer_notes: Optional[str] = None
    ) -> bool:
        """Approve a correction for implementation"""
        
        correction = self._corrections.get(correction_id)
        if not correction:
            return False
        
        correction.status = CorrectionStatus.APPROVED
        correction.approved_by = approver_id
        correction.approved_at = datetime.now()
        correction.reviewer_notes = reviewer_notes
        
        # Remove from review queue
        if correction_id in self._review_queue:
            self._review_queue.remove(correction_id)
        
        # Add to retraining data
        self._add_to_retraining_data(correction)
        
        # Queue for user notification
        self._queue_user_notification(correction)
        
        logger.info(f"Correction approved: {correction_id} by {approver_id}")
        return True
    
    def reject_correction(
        self,
        correction_id: str,
        approver_id: str,
        rejection_reason: str
    ) -> bool:
        """Reject a correction"""
        
        correction = self._corrections.get(correction_id)
        if not correction:
            return False
        
        correction.status = CorrectionStatus.REJECTED
        correction.approved_by = approver_id
        correction.approved_at = datetime.now()
        correction.reviewer_notes = rejection_reason
        
        # Remove from review queue
        if correction_id in self._review_queue:
            self._review_queue.remove(correction_id)
        
        # Queue for user notification
        self._queue_user_notification(correction)
        
        logger.info(f"Correction rejected: {correction_id} by {approver_id}")
        return True
    
    def implement_correction(self, correction_id: str) -> bool:
        """Mark correction as implemented in the system"""
        
        correction = self._corrections.get(correction_id)
        if not correction or correction.status != CorrectionStatus.APPROVED:
            return False
        
        correction.status = CorrectionStatus.IMPLEMENTED
        correction.implemented_at = datetime.now()
        
        logger.info(f"Correction implemented: {correction_id}")
        return True
    
    def get_retraining_data(self, document_type: Optional[DocumentType] = None) -> List[Dict[str, Any]]:
        """Get approved corrections for model retraining"""
        
        if document_type:
            filtered_data = [
                data for data in self._retraining_data
                if data.get("document_type") == document_type.value
            ]
        else:
            filtered_data = self._retraining_data
        
        return filtered_data
    
    def get_correction_statistics(self) -> Dict[str, Any]:
        """Get statistics about the correction workflow"""
        
        total_corrections = len(self._corrections)
        if total_corrections == 0:
            return {"total_corrections": 0}
        
        status_counts = Counter(c.status.value for c in self._corrections.values())
        correction_type_counts = Counter(c.correction_type for c in self._corrections.values())
        document_type_counts = Counter(c.document_type.value for c in self._corrections.values())
        
        # Calculate average time to approval
        approved_corrections = [
            c for c in self._corrections.values() 
            if c.status == CorrectionStatus.APPROVED and c.approved_at
        ]
        
        avg_approval_time = None
        if approved_corrections:
            approval_times = [
                (c.approved_at - c.timestamp).total_seconds() / 3600  # Convert to hours
                for c in approved_corrections
            ]
            avg_approval_time = statistics.mean(approval_times)
        
        return {
            "total_corrections": total_corrections,
            "status_distribution": dict(status_counts),
            "correction_type_distribution": dict(correction_type_counts),
            "document_type_distribution": dict(document_type_counts),
            "pending_review": len(self._review_queue),
            "average_approval_time_hours": avg_approval_time,
            "retraining_data_points": len(self._retraining_data)
        }
    
    def _add_to_retraining_data(self, correction: Correction):
        """Add approved correction to retraining dataset"""
        
        retraining_entry = {
            "correction_id": correction.id,
            "original_content": correction.original_content,
            "corrected_content": correction.corrected_content,
            "correction_type": correction.correction_type,
            "correction_reason": correction.correction_reason,
            "document_type": correction.document_type.value,
            "attorney_id": correction.attorney_id,
            "approved_by": correction.approved_by,
            "timestamp": correction.timestamp.isoformat(),
            "approved_at": correction.approved_at.isoformat() if correction.approved_at else None
        }
        
        self._retraining_data.append(retraining_entry)
        
        # Keep only recent retraining data (last 1000 entries)
        if len(self._retraining_data) > 1000:
            self._retraining_data = self._retraining_data[-1000:]
    
    def _queue_user_notification(self, correction: Correction):
        """Queue notification for user about correction status"""
        
        notification = {
            "type": "correction_status_update",
            "user_id": correction.user_id,
            "correction_id": correction.id,
            "status": correction.status.value,
            "timestamp": datetime.now(),
            "message": self._generate_notification_message(correction)
        }
        
        # Add to feedback collector's notification queue
        self.feedback_collector._notification_queue.append(notification)
    
    def _generate_notification_message(self, correction: Correction) -> str:
        """Generate user-friendly notification message"""
        
        if correction.status == CorrectionStatus.APPROVED:
            return f"Your correction for {correction.document_type.value} has been approved and will be implemented."
        elif correction.status == CorrectionStatus.REJECTED:
            return f"Your correction for {correction.document_type.value} was not approved. See reviewer notes for details."
        elif correction.status == CorrectionStatus.IMPLEMENTED:
            return f"Your correction for {correction.document_type.value} has been successfully implemented."
        
        return f"Status update for your correction: {correction.status.value}"


class QualityMetrics:
    """
    Tracks and analyzes quality metrics including accuracy rates,
    user satisfaction, error rates, and attorney override frequency.
    """
    
    def __init__(self, feedback_collector: FeedbackCollector, correction_workflow: CorrectionWorkflow):
        self.feedback_collector = feedback_collector
        self.correction_workflow = correction_workflow
        self._cached_metrics = {}  # Cache for expensive calculations
        self._cache_expiry = {}    # Cache expiration times
    
    def calculate_accuracy_rates_by_document_type(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """Calculate accuracy rates grouped by document type"""
        
        cache_key = f"accuracy_by_doc_type_{days}"
        if self._is_cache_valid(cache_key):
            return self._cached_metrics[cache_key]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all accuracy feedback
        accuracy_feedbacks = [
            feedback for feedback in self.feedback_collector._feedback_storage.values()
            if (feedback.feedback_type == FeedbackType.ACCURACY and 
                feedback.timestamp >= cutoff_date and
                feedback.rating is not None)
        ]
        
        # Group by document type
        by_doc_type = defaultdict(list)
        for feedback in accuracy_feedbacks:
            doc_type = feedback.document_type.value if feedback.document_type else "unknown"
            by_doc_type[doc_type].append(feedback)
        
        # Calculate metrics for each document type
        results = {}
        for doc_type, feedbacks in by_doc_type.items():
            ratings = [feedback.rating.value for feedback in feedbacks]
            scores = [self.feedback_collector._calculate_accuracy_score([rating]) for rating in ratings]
            
            # Calculate accuracy buckets
            accurate_count = len([s for s in scores if s >= 4.0])  # Mostly/completely accurate
            inaccurate_count = len([s for s in scores if s <= 2.0])  # Mostly/completely inaccurate
            
            results[doc_type] = {
                "total_responses": len(feedbacks),
                "average_accuracy_score": statistics.mean(scores) if scores else 0,
                "accuracy_rate": accurate_count / len(scores) if scores else 0,
                "inaccuracy_rate": inaccurate_count / len(scores) if scores else 0,
                "rating_distribution": dict(Counter(ratings)),
                "common_issues": self.feedback_collector._extract_common_issues(feedbacks)
            }
        
        # Cache results
        self._cached_metrics[cache_key] = results
        self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)
        
        return results
    
    def calculate_user_satisfaction_scores(self, days: int = 30) -> Dict[str, Any]:
        """Calculate overall user satisfaction metrics"""
        
        cache_key = f"satisfaction_scores_{days}"
        if self._is_cache_valid(cache_key):
            return self._cached_metrics[cache_key]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get usefulness feedback
        usefulness_feedbacks = [
            feedback for feedback in self.feedback_collector._feedback_storage.values()
            if (feedback.feedback_type == FeedbackType.USEFULNESS and 
                feedback.timestamp >= cutoff_date and
                feedback.rating is not None)
        ]
        
        if not usefulness_feedbacks:
            return {"error": "No usefulness feedback available for the specified period"}
        
        # Calculate satisfaction metrics
        ratings = [feedback.rating.value for feedback in usefulness_feedbacks]
        scores = [self.feedback_collector._calculate_usefulness_score([rating]) for rating in ratings]
        
        satisfied_count = len([s for s in scores if s >= 4.0])  # Very/somewhat useful
        dissatisfied_count = len([s for s in scores if s <= 2.0])  # Not very/not useful
        
        # Group by document type
        by_doc_type = defaultdict(list)
        for feedback in usefulness_feedbacks:
            doc_type = feedback.document_type.value if feedback.document_type else "unknown"
            by_doc_type[doc_type].append(feedback.rating.value)
        
        doc_type_satisfaction = {}
        for doc_type, type_ratings in by_doc_type.items():
            type_scores = [self.feedback_collector._calculate_usefulness_score([rating]) for rating in type_ratings]
            doc_type_satisfaction[doc_type] = statistics.mean(type_scores) if type_scores else 0
        
        results = {
            "period_days": days,
            "total_responses": len(usefulness_feedbacks),
            "average_satisfaction_score": statistics.mean(scores),
            "satisfaction_rate": satisfied_count / len(scores),
            "dissatisfaction_rate": dissatisfied_count / len(scores),
            "rating_distribution": dict(Counter(ratings)),
            "satisfaction_by_document_type": doc_type_satisfaction,
            "trend": self._calculate_satisfaction_trend(days)
        }
        
        # Cache results
        self._cached_metrics[cache_key] = results
        self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)
        
        return results
    
    def calculate_error_rates_by_feature(self, days: int = 30) -> Dict[str, Any]:
        """Calculate error rates grouped by system features"""
        
        cache_key = f"error_rates_{days}"
        if self._is_cache_valid(cache_key):
            return self._cached_metrics[cache_key]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get error reports
        error_reports = [
            error for error in self.feedback_collector._error_reports.values()
            if error.timestamp >= cutoff_date
        ]
        
        if not error_reports:
            return {"error": "No error reports available for the specified period"}
        
        # Group by error type and severity
        by_error_type = defaultdict(list)
        by_severity = defaultdict(int)
        
        for error in error_reports:
            by_error_type[error.error_type].append(error)
            by_severity[error.severity.value] += 1
        
        # Calculate error rates by type
        error_type_stats = {}
        for error_type, type_errors in by_error_type.items():
            severity_distribution = Counter(error.severity.value for error in type_errors)
            
            error_type_stats[error_type] = {
                "total_errors": len(type_errors),
                "severity_distribution": dict(severity_distribution),
                "critical_errors": severity_distribution.get("critical", 0),
                "resolution_rate": len([e for e in type_errors if e.status == "resolved"]) / len(type_errors)
            }
        
        results = {
            "period_days": days,
            "total_errors": len(error_reports),
            "error_rate_per_day": len(error_reports) / days,
            "severity_distribution": dict(by_severity),
            "error_types": error_type_stats,
            "critical_error_rate": by_severity.get("critical", 0) / len(error_reports)
        }
        
        # Cache results
        self._cached_metrics[cache_key] = results
        self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)
        
        return results
    
    def calculate_attorney_override_frequency(self, days: int = 30) -> Dict[str, Any]:
        """Calculate frequency of attorney corrections and overrides"""
        
        cache_key = f"attorney_overrides_{days}"
        if self._is_cache_valid(cache_key):
            return self._cached_metrics[cache_key]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get corrections
        corrections = [
            correction for correction in self.correction_workflow._corrections.values()
            if correction.timestamp >= cutoff_date
        ]
        
        if not corrections:
            return {"error": "No corrections available for the specified period"}
        
        # Analyze correction patterns
        by_correction_type = defaultdict(int)
        by_document_type = defaultdict(int)
        by_attorney = defaultdict(int)
        
        for correction in corrections:
            by_correction_type[correction.correction_type] += 1
            by_document_type[correction.document_type.value] += 1
            by_attorney[correction.attorney_id] += 1
        
        # Calculate approval rates
        total_corrections = len(corrections)
        approved_corrections = len([c for c in corrections if c.status == CorrectionStatus.APPROVED])
        rejected_corrections = len([c for c in corrections if c.status == CorrectionStatus.REJECTED])
        
        results = {
            "period_days": days,
            "total_corrections": total_corrections,
            "corrections_per_day": total_corrections / days,
            "approval_rate": approved_corrections / total_corrections if total_corrections > 0 else 0,
            "rejection_rate": rejected_corrections / total_corrections if total_corrections > 0 else 0,
            "correction_types": dict(by_correction_type),
            "document_types": dict(by_document_type),
            "top_correcting_attorneys": dict(Counter(by_attorney).most_common(10)),
            "average_time_to_correction": self._calculate_avg_correction_time(corrections)
        }
        
        # Cache results
        self._cached_metrics[cache_key] = results
        self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)
        
        return results
    
    def get_time_to_correction_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Calculate time-to-correction metrics"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get implemented corrections
        implemented_corrections = [
            correction for correction in self.correction_workflow._corrections.values()
            if (correction.timestamp >= cutoff_date and 
                correction.status == CorrectionStatus.IMPLEMENTED and
                correction.implemented_at is not None)
        ]
        
        if not implemented_corrections:
            return {"error": "No implemented corrections available for the specified period"}
        
        # Calculate time metrics
        correction_times = []
        approval_times = []
        implementation_times = []
        
        for correction in implemented_corrections:
            # Total time from submission to implementation
            total_time = (correction.implemented_at - correction.timestamp).total_seconds() / 3600
            correction_times.append(total_time)
            
            # Time from submission to approval
            if correction.approved_at:
                approval_time = (correction.approved_at - correction.timestamp).total_seconds() / 3600
                approval_times.append(approval_time)
                
                # Time from approval to implementation
                impl_time = (correction.implemented_at - correction.approved_at).total_seconds() / 3600
                implementation_times.append(impl_time)
        
        return {
            "period_days": days,
            "total_implemented_corrections": len(implemented_corrections),
            "average_total_time_hours": statistics.mean(correction_times),
            "median_total_time_hours": statistics.median(correction_times),
            "average_approval_time_hours": statistics.mean(approval_times) if approval_times else None,
            "average_implementation_time_hours": statistics.mean(implementation_times) if implementation_times else None,
            "time_percentiles": {
                "p50": statistics.median(correction_times),
                "p75": self._percentile(correction_times, 75),
                "p90": self._percentile(correction_times, 90),
                "p95": self._percentile(correction_times, 95)
            }
        }
    
    def generate_quality_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        
        report = {
            "report_period_days": days,
            "generated_at": datetime.now(),
            "accuracy_metrics": self.calculate_accuracy_rates_by_document_type(days),
            "satisfaction_metrics": self.calculate_user_satisfaction_scores(days),
            "error_metrics": self.calculate_error_rates_by_feature(days),
            "correction_metrics": self.calculate_attorney_override_frequency(days),
            "timing_metrics": self.get_time_to_correction_metrics(days)
        }
        
        # Add executive summary
        report["executive_summary"] = self._generate_executive_summary(report)
        
        return report
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached metric is still valid"""
        return (cache_key in self._cached_metrics and 
                cache_key in self._cache_expiry and
                datetime.now() < self._cache_expiry[cache_key])
    
    def _calculate_satisfaction_trend(self, days: int) -> str:
        """Calculate satisfaction trend over time"""
        # Simplified trend calculation - could be enhanced with more sophisticated analysis
        current_period = self.calculate_user_satisfaction_scores(days)
        previous_period = self.calculate_user_satisfaction_scores(days * 2)
        
        if "average_satisfaction_score" not in current_period or "average_satisfaction_score" not in previous_period:
            return "insufficient_data"
        
        current_score = current_period["average_satisfaction_score"]
        # Get the previous period score (roughly)
        previous_score = previous_period["average_satisfaction_score"]
        
        if current_score > previous_score + 0.1:
            return "improving"
        elif current_score < previous_score - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _calculate_avg_correction_time(self, corrections: List[Correction]) -> float:
        """Calculate average time for corrections to be processed"""
        processed_corrections = [
            c for c in corrections 
            if c.status in [CorrectionStatus.APPROVED, CorrectionStatus.REJECTED] and c.approved_at
        ]
        
        if not processed_corrections:
            return 0.0
        
        times = [
            (c.approved_at - c.timestamp).total_seconds() / 3600
            for c in processed_corrections
        ]
        
        return statistics.mean(times)
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index == int(index):
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (index - int(index)) * (upper - lower)
    
    def _generate_executive_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from quality report"""
        
        summary = {}
        
        # Accuracy summary
        accuracy_data = report.get("accuracy_metrics", {})
        if accuracy_data and not isinstance(accuracy_data, dict) or "error" not in accuracy_data:
            avg_accuracy = statistics.mean([
                data["average_accuracy_score"] 
                for data in accuracy_data.values() 
                if isinstance(data, dict) and "average_accuracy_score" in data
            ]) if accuracy_data else 0
            summary["overall_accuracy"] = f"{avg_accuracy:.2f}/5.0"
        
        # Satisfaction summary
        satisfaction_data = report.get("satisfaction_metrics", {})
        if satisfaction_data and "average_satisfaction_score" in satisfaction_data:
            summary["user_satisfaction"] = f"{satisfaction_data['average_satisfaction_score']:.2f}/5.0"
            summary["satisfaction_trend"] = satisfaction_data.get("trend", "unknown")
        
        # Error summary
        error_data = report.get("error_metrics", {})
        if error_data and "total_errors" in error_data:
            summary["daily_error_rate"] = f"{error_data['error_rate_per_day']:.1f}"
            summary["critical_error_percentage"] = f"{error_data.get('critical_error_rate', 0)*100:.1f}%"
        
        # Correction summary
        correction_data = report.get("correction_metrics", {})
        if correction_data and "total_corrections" in correction_data:
            summary["daily_correction_rate"] = f"{correction_data['corrections_per_day']:.1f}"
            summary["correction_approval_rate"] = f"{correction_data.get('approval_rate', 0)*100:.1f}%"
        
        return summary