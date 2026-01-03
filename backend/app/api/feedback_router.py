from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from ..src.feedback.feedback_system import (
    FeedbackCollector, 
    CorrectionWorkflow, 
    QualityMetrics,
    AccuracyRating,
    UsefulnessRating, 
    CorrectionStatus,
    FeedbackType,
    MetricType,
    AccuracyFeedback,
    UsefulnessFeedback,
    ErrorReport,
    Suggestion,
    AttorneyCorrection,
    QualityReport
)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

feedback_collector = FeedbackCollector()
correction_workflow = CorrectionWorkflow() 
quality_metrics = QualityMetrics()

class AccuracyFeedbackRequest(BaseModel):
    user_id: str
    content_id: str
    rating: AccuracyRating
    comment: Optional[str] = None
    specific_issues: List[str] = Field(default_factory=list)

class AccuracyFeedbackResponse(BaseModel):
    feedback_id: str
    message: str
    flagged_for_review: bool

class UsefulnessFeedbackRequest(BaseModel):
    user_id: str
    content_id: str
    rating: UsefulnessRating
    comment: Optional[str] = None
    improvement_suggestions: List[str] = Field(default_factory=list)

class UsefulnessFeedbackResponse(BaseModel):
    feedback_id: str
    message: str

class ErrorReportRequest(BaseModel):
    user_id: str
    content_id: str
    error_type: str
    description: str
    severity: str = "medium"
    steps_to_reproduce: List[str] = Field(default_factory=list)
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None

class ErrorReportResponse(BaseModel):
    report_id: str
    message: str
    estimated_resolution_time: str

class SuggestionRequest(BaseModel):
    user_id: str
    title: str
    description: str
    category: str = "general"
    priority: str = "medium"

class SuggestionResponse(BaseModel):
    suggestion_id: str
    message: str

class CorrectionRequest(BaseModel):
    attorney_id: str
    content_id: str
    original_text: str
    corrected_text: str
    correction_type: str
    explanation: str
    severity: str = "medium"
    requires_model_update: bool = False

class CorrectionResponse(BaseModel):
    correction_id: str
    message: str
    status: CorrectionStatus

class MetricsResponse(BaseModel):
    accuracy_metrics: Dict[str, Any]
    usefulness_metrics: Dict[str, Any]
    error_metrics: Dict[str, Any]
    suggestion_metrics: Dict[str, Any]
    overall_quality_score: float
    generated_at: datetime

class AttorneyQueueResponse(BaseModel):
    pending_corrections: List[Dict[str, Any]]
    total_pending: int
    average_review_time: float
    overdue_corrections: int

@router.post("/accuracy", response_model=AccuracyFeedbackResponse)
async def submit_accuracy_feedback(
    request: AccuracyFeedbackRequest,
    background_tasks: BackgroundTasks
):
    """Submit accuracy feedback for AI-generated content."""
    try:
        feedback_id = feedback_collector.submit_accuracy_feedback(
            user_id=request.user_id,
            content_id=request.content_id,
            rating=request.rating,
            comment=request.comment,
            specific_issues=request.specific_issues
        )
        
        # Check if feedback should be flagged for attorney review
        flagged_for_review = request.rating in [AccuracyRating.POOR, AccuracyRating.VERY_POOR]
        
        if flagged_for_review:
            background_tasks.add_task(
                _flag_content_for_review,
                request.content_id,
                request.user_id,
                f"Low accuracy rating: {request.rating.value}"
            )
        
        return AccuracyFeedbackResponse(
            feedback_id=feedback_id,
            message="Accuracy feedback submitted successfully",
            flagged_for_review=flagged_for_review
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit accuracy feedback: {str(e)}")

@router.post("/usefulness", response_model=UsefulnessFeedbackResponse)
async def submit_usefulness_feedback(request: UsefulnessFeedbackRequest):
    """Submit usefulness feedback for AI-generated content."""
    try:
        feedback_id = feedback_collector.submit_usefulness_feedback(
            user_id=request.user_id,
            content_id=request.content_id,
            rating=request.rating,
            comment=request.comment,
            improvement_suggestions=request.improvement_suggestions
        )
        
        return UsefulnessFeedbackResponse(
            feedback_id=feedback_id,
            message="Usefulness feedback submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit usefulness feedback: {str(e)}")

@router.post("/report-error", response_model=ErrorReportResponse)
async def report_error(
    request: ErrorReportRequest,
    background_tasks: BackgroundTasks
):
    """Report an error or issue with AI-generated content."""
    try:
        report_id = feedback_collector.report_error(
            user_id=request.user_id,
            content_id=request.content_id,
            error_type=request.error_type,
            description=request.description,
            severity=request.severity,
            steps_to_reproduce=request.steps_to_reproduce,
            expected_behavior=request.expected_behavior,
            actual_behavior=request.actual_behavior
        )
        
        # Estimate resolution time based on severity
        resolution_times = {
            "low": "3-5 business days",
            "medium": "1-2 business days", 
            "high": "4-8 hours",
            "critical": "1-2 hours"
        }
        
        estimated_time = resolution_times.get(request.severity, "2-3 business days")
        
        # Schedule high/critical severity errors for immediate review
        if request.severity in ["high", "critical"]:
            background_tasks.add_task(
                _escalate_error_report,
                report_id,
                request.severity
            )
        
        return ErrorReportResponse(
            report_id=report_id,
            message="Error report submitted successfully",
            estimated_resolution_time=estimated_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit error report: {str(e)}")

@router.post("/suggestion", response_model=SuggestionResponse)
async def submit_suggestion(request: SuggestionRequest):
    """Submit a suggestion for system improvement."""
    try:
        suggestion_id = feedback_collector.submit_suggestion(
            user_id=request.user_id,
            title=request.title,
            description=request.description,
            category=request.category,
            priority=request.priority
        )
        
        return SuggestionResponse(
            suggestion_id=suggestion_id,
            message="Suggestion submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit suggestion: {str(e)}")

@router.post("/correction", response_model=CorrectionResponse)
async def submit_correction(
    request: CorrectionRequest,
    background_tasks: BackgroundTasks
):
    """Submit attorney correction for AI-generated content."""
    try:
        correction_id = correction_workflow.submit_correction(
            attorney_id=request.attorney_id,
            content_id=request.content_id,
            original_text=request.original_text,
            corrected_text=request.corrected_text,
            correction_type=request.correction_type,
            explanation=request.explanation,
            severity=request.severity,
            requires_model_update=request.requires_model_update
        )
        
        # Get current status
        status = correction_workflow.get_correction_status(correction_id)
        
        # Schedule for approval workflow if needed
        if request.requires_model_update:
            background_tasks.add_task(
                _initiate_approval_workflow,
                correction_id
            )
        
        return CorrectionResponse(
            correction_id=correction_id,
            message="Correction submitted successfully",
            status=status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit correction: {str(e)}")

@router.get("/metrics", response_model=MetricsResponse)
async def get_feedback_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    metric_types: List[str] = Query(default=["accuracy", "usefulness", "errors"])
):
    """Get comprehensive feedback metrics and analytics."""
    try:
        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        metrics = {}
        
        if "accuracy" in metric_types:
            metrics["accuracy_metrics"] = quality_metrics.get_accuracy_metrics(
                start_date=start_date,
                end_date=end_date
            )
        
        if "usefulness" in metric_types:
            metrics["usefulness_metrics"] = quality_metrics.get_usefulness_metrics(
                start_date=start_date,
                end_date=end_date
            )
        
        if "errors" in metric_types:
            metrics["error_metrics"] = quality_metrics.get_error_metrics(
                start_date=start_date,
                end_date=end_date
            )
        
        if "suggestions" in metric_types:
            metrics["suggestion_metrics"] = quality_metrics.get_suggestion_metrics(
                start_date=start_date,
                end_date=end_date
            )
        
        # Calculate overall quality score
        overall_score = quality_metrics.calculate_overall_quality_score(
            start_date=start_date,
            end_date=end_date
        )
        
        return MetricsResponse(
            accuracy_metrics=metrics.get("accuracy_metrics", {}),
            usefulness_metrics=metrics.get("usefulness_metrics", {}),
            error_metrics=metrics.get("error_metrics", {}),
            suggestion_metrics=metrics.get("suggestion_metrics", {}),
            overall_quality_score=overall_score,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback metrics: {str(e)}")

@router.get("/attorney-queue", response_model=AttorneyQueueResponse)
async def get_attorney_queue(attorney_id: Optional[str] = Query(None)):
    """Get attorney correction queue and statistics."""
    try:
        queue_data = correction_workflow.get_attorney_queue(attorney_id)
        
        # Calculate statistics
        pending_corrections = queue_data.get("pending_corrections", [])
        total_pending = len(pending_corrections)
        
        # Calculate average review time (mock calculation)
        avg_review_time = correction_workflow._calculate_average_review_time()
        
        # Count overdue corrections (corrections pending > 24 hours)
        overdue_threshold = datetime.utcnow() - timedelta(hours=24)
        overdue_corrections = len([
            correction for correction in pending_corrections
            if correction.get("created_at", datetime.utcnow()) < overdue_threshold
        ])
        
        return AttorneyQueueResponse(
            pending_corrections=pending_corrections,
            total_pending=total_pending,
            average_review_time=avg_review_time,
            overdue_corrections=overdue_corrections
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get attorney queue: {str(e)}")

@router.get("/reports/{report_type}")
async def generate_quality_report(
    report_type: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    format: str = Query("json", regex="^(json|csv|pdf)$")
):
    """Generate comprehensive quality reports."""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        report = quality_metrics.generate_quality_report(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            format=format
        )
        
        return {
            "report_type": report_type,
            "format": format,
            "generated_at": datetime.utcnow(),
            "data": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quality report: {str(e)}")

# Background task functions
async def _flag_content_for_review(content_id: str, user_id: str, reason: str):
    """Flag content for attorney review."""
    try:
        correction_workflow._flag_content_for_review(content_id, user_id, reason)
    except Exception as e:
        print(f"Failed to flag content for review: {e}")

async def _escalate_error_report(report_id: str, severity: str):
    """Escalate high/critical severity error reports."""
    try:
        feedback_collector._escalate_error_report(report_id, severity)
    except Exception as e:
        print(f"Failed to escalate error report: {e}")

async def _initiate_approval_workflow(correction_id: str):
    """Initiate approval workflow for corrections requiring model updates."""
    try:
        correction_workflow._initiate_approval_workflow(correction_id)
    except Exception as e:
        print(f"Failed to initiate approval workflow: {e}")