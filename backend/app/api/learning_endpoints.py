"""
Learning System API Endpoints

Endpoints for feedback collection, knowledge retrieval, and performance tracking.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.src.core.database import get_db
from app.src.services.learning_service import get_learning_service, LearningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/learning", tags=["Learning & Improvement"])


# =========================================================================
# REQUEST/RESPONSE MODELS
# =========================================================================

class FeedbackRequest(BaseModel):
    """Request model for submitting feedback"""
    model_config = {"protected_namespaces": ()}  # Allow model_used field

    document_id: Optional[str] = None
    session_id: str
    request_type: str = Field(..., description="Type of request (analysis, classification, etc.)")
    model_used: str = Field(..., description="AI model that generated the response")
    response_text: str = Field(..., description="AI's response")
    user_rating: int = Field(..., ge=1, le=5, description="User rating 1-5")
    was_helpful: bool = True
    was_accurate: bool = True
    feedback_text: Optional[str] = None
    corrected_response: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    processing_time_ms: Optional[int] = None
    token_count: Optional[int] = None
    cost_usd: Optional[float] = None
    prompt_version: str = "1.0"


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    id: int
    message: str
    knowledge_extracted: bool


class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge search"""
    query: str
    knowledge_type: Optional[str] = None
    document_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    limit: int = Field(default=10, le=50)


class KnowledgeItem(BaseModel):
    """Knowledge item response"""
    id: int
    knowledge_type: str
    title: str
    content: str
    document_type: str
    jurisdiction: Optional[str]
    practice_area: Optional[str]
    usage_count: int
    success_rate: float
    avg_user_rating: float


class PerformanceTrendRequest(BaseModel):
    """Request model for performance trends"""
    model_config = {"protected_namespaces": ()}  # Allow model_name field

    metric_type: str
    task_type: str
    model_name: str
    days: int = Field(default=30, le=365)


class PerformanceDataPoint(BaseModel):
    """Single performance data point"""
    date: str
    value: float
    sample_size: int


class PerformanceImprovementResponse(BaseModel):
    """Performance improvement analysis"""
    baseline: Optional[float]
    current: Optional[float]
    improvement_pct: float
    trend: str
    data_points: int


class LearningStatsResponse(BaseModel):
    """Overall learning system statistics"""
    total_feedback_items: int
    average_user_rating: float
    total_knowledge_items: int
    total_performance_metrics: int
    rating_distribution: Dict[int, int]
    top_request_types: List[Dict[str, Any]]
    learning_status: str


class PreferenceRequest(BaseModel):
    """Request to learn a user preference"""
    user_id: Optional[str] = None
    firm_id: Optional[str] = None
    preference_type: str
    preference_key: str
    preference_value: Any
    confidence: float = Field(default=0.5, ge=0, le=1)


# =========================================================================
# FEEDBACK ENDPOINTS
# =========================================================================

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback on an AI response.

    This feedback is used to:
    - Track model performance
    - Identify areas for improvement
    - Extract successful patterns as knowledge
    - Build training data for fine-tuning

    Returns:
        Confirmation with feedback ID and whether knowledge was extracted
    """
    try:
        service = get_learning_service(db)

        feedback_obj = service.record_feedback(
            document_id=feedback.document_id,
            session_id=feedback.session_id,
            request_type=feedback.request_type,
            model_used=feedback.model_used,
            response_text=feedback.response_text,
            user_rating=feedback.user_rating,
            was_helpful=feedback.was_helpful,
            was_accurate=feedback.was_accurate,
            feedback_text=feedback.feedback_text,
            corrected_response=feedback.corrected_response,
            confidence_score=feedback.confidence_score,
            processing_time_ms=feedback.processing_time_ms,
            token_count=feedback.token_count,
            cost_usd=feedback.cost_usd,
            prompt_version=feedback.prompt_version
        )

        # Knowledge is extracted for ratings >= 4
        knowledge_extracted = feedback.user_rating >= 4 and feedback.was_accurate

        return FeedbackResponse(
            id=feedback_obj.id,
            message="Feedback recorded successfully",
            knowledge_extracted=knowledge_extracted
        )

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/feedback/stats", response_model=Dict[str, Any])
async def get_feedback_stats(
    request_type: Optional[str] = None,
    model: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics and aggregations.

    Args:
        request_type: Filter by request type
        model: Filter by model
        days: Number of days to analyze

    Returns:
        Aggregated feedback statistics
    """
    try:
        from app.models.learning import AIFeedback
        from sqlalchemy import func
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = db.query(AIFeedback).filter(AIFeedback.created_at >= cutoff_date)

        if request_type:
            query = query.filter(AIFeedback.request_type == request_type)
        if model:
            query = query.filter(AIFeedback.model_used == model)

        feedback_items = query.all()

        if not feedback_items:
            return {
                "total_feedback": 0,
                "average_rating": 0,
                "helpful_percentage": 0,
                "accurate_percentage": 0
            }

        total = len(feedback_items)
        avg_rating = sum(f.user_rating for f in feedback_items) / total
        helpful_count = sum(1 for f in feedback_items if f.was_helpful)
        accurate_count = sum(1 for f in feedback_items if f.was_accurate)

        return {
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "helpful_percentage": round((helpful_count / total) * 100, 1),
            "accurate_percentage": round((accurate_count / total) * 100, 1),
            "period_days": days
        }

    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback stats: {str(e)}"
        )


# =========================================================================
# KNOWLEDGE BASE ENDPOINTS
# =========================================================================

@router.post("/knowledge/search", response_model=List[KnowledgeItem])
async def search_knowledge(
    search_req: KnowledgeSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search the knowledge base for relevant information.

    This uses past successful analyses to inform current work.
    Implements a simple RAG (Retrieval-Augmented Generation) system.

    Returns:
        List of relevant knowledge items, ordered by quality
    """
    try:
        service = get_learning_service(db)

        knowledge_items = service.search_knowledge(
            query=search_req.query,
            knowledge_type=search_req.knowledge_type,
            document_type=search_req.document_type,
            jurisdiction=search_req.jurisdiction,
            practice_area=search_req.practice_area,
            limit=search_req.limit
        )

        return [
            KnowledgeItem(
                id=item.id,
                knowledge_type=item.knowledge_type,
                title=item.title,
                content=item.content,
                document_type=item.document_type,
                jurisdiction=item.jurisdiction,
                practice_area=item.practice_area,
                usage_count=item.usage_count,
                success_rate=item.success_rate,
                avg_user_rating=item.avg_user_rating
            )
            for item in knowledge_items
        ]

    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge: {str(e)}"
        )


@router.get("/knowledge/{document_id}/similar")
async def get_similar_documents(
    document_id: str,
    min_similarity: float = 0.7,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Find documents similar to the given document.

    Uses similarity metrics to find related precedents and examples.

    Returns:
        List of similar documents with similarity scores
    """
    try:
        service = get_learning_service(db)
        similar = service.get_similar_documents(document_id, min_similarity, limit)

        return [
            {
                "document_id": doc.id,
                "file_name": doc.file_name,
                "document_type": doc.document_type,
                "similarity_score": score,
                "summary": doc.summary
            }
            for doc, score in similar
        ]

    except Exception as e:
        logger.error(f"Error finding similar documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar documents: {str(e)}"
        )


# =========================================================================
# PERFORMANCE TRACKING ENDPOINTS
# =========================================================================

@router.post("/performance/trends", response_model=List[PerformanceDataPoint])
async def get_performance_trends(
    trend_req: PerformanceTrendRequest,
    db: Session = Depends(get_db)
):
    """
    Get performance trends over time for a specific metric.

    Tracks how the AI is improving on different tasks.

    Returns:
        Time series of performance measurements
    """
    try:
        service = get_learning_service(db)

        trends = service.get_performance_trends(
            metric_type=trend_req.metric_type,
            task_type=trend_req.task_type,
            model_name=trend_req.model_name,
            days=trend_req.days
        )

        return [
            PerformanceDataPoint(
                date=trend["date"],
                value=trend["value"],
                sample_size=trend["sample_size"]
            )
            for trend in trends
        ]

    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance trends: {str(e)}"
        )


@router.post("/performance/improvement", response_model=PerformanceImprovementResponse)
async def calculate_improvement(
    trend_req: PerformanceTrendRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate performance improvement over time.

    Compares baseline performance with current performance to show progress.

    Returns:
        Improvement analysis with percentage change
    """
    try:
        service = get_learning_service(db)

        improvement = service.calculate_improvement(
            metric_type=trend_req.metric_type,
            task_type=trend_req.task_type,
            model_name=trend_req.model_name,
            days=trend_req.days
        )

        return PerformanceImprovementResponse(**improvement)

    except Exception as e:
        logger.error(f"Error calculating improvement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate improvement: {str(e)}"
        )


# =========================================================================
# PREFERENCE LEARNING ENDPOINTS
# =========================================================================

@router.post("/preferences/learn")
async def learn_preference(
    pref_req: PreferenceRequest,
    db: Session = Depends(get_db)
):
    """
    Record a user or firm preference.

    The system learns from user interactions to personalize responses.

    Returns:
        Confirmation of learned preference
    """
    try:
        service = get_learning_service(db)

        pref = service.learn_preference(
            user_id=pref_req.user_id,
            firm_id=pref_req.firm_id,
            preference_type=pref_req.preference_type,
            preference_key=pref_req.preference_key,
            preference_value=pref_req.preference_value,
            confidence=pref_req.confidence
        )

        return {
            "id": pref.id,
            "message": "Preference learned",
            "confidence": pref.confidence,
            "evidence_count": pref.evidence_count
        }

    except Exception as e:
        logger.error(f"Error learning preference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to learn preference: {str(e)}"
        )


@router.get("/preferences")
async def get_preferences(
    user_id: Optional[str] = None,
    firm_id: Optional[str] = None,
    preference_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get learned preferences for a user or firm.

    Returns personalized settings based on past interactions.

    Returns:
        List of preferences ordered by confidence
    """
    try:
        service = get_learning_service(db)
        prefs = service.get_preferences(user_id, firm_id, preference_type)

        return [
            {
                "id": p.id,
                "preference_type": p.preference_type,
                "preference_key": p.preference_key,
                "preference_value": p.preference_value,
                "confidence": p.confidence,
                "evidence_count": p.evidence_count
            }
            for p in prefs
        ]

    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


# =========================================================================
# GENERAL STATISTICS
# =========================================================================

@router.get("/stats", response_model=LearningStatsResponse)
async def get_learning_statistics(db: Session = Depends(get_db)):
    """
    Get overall learning system statistics.

    Provides insights into how much the system has learned and
    how well it's performing.

    Returns:
        Comprehensive learning system statistics
    """
    try:
        service = get_learning_service(db)
        stats = service.get_learning_statistics()

        return LearningStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting learning statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning statistics: {str(e)}"
        )


@router.get("/health")
async def learning_system_health(db: Session = Depends(get_db)):
    """
    Check if the learning system is operational.

    Returns:
        Health status of the learning system
    """
    try:
        service = get_learning_service(db)
        stats = service.get_learning_statistics()

        return {
            "status": "healthy",
            "learning_active": stats["learning_status"] == "active",
            "total_data_points": (
                stats["total_feedback_items"] +
                stats["total_knowledge_items"] +
                stats["total_performance_metrics"]
            )
        }

    except Exception as e:
        logger.error(f"Learning system health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
