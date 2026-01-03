"""
Learning Service - Continuous Improvement for AI Agents

Handles feedback collection, knowledge base building, and performance tracking
to make AI agents smarter over time.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.learning import (
    AIFeedback,
    DocumentKnowledge,
    PerformanceMetric,
    LearningTask,
    DocumentSimilarity,
    UserPreference
)
from app.models.legal_documents import Document

logger = logging.getLogger(__name__)


class LearningService:
    """
    Service for continuous learning and improvement of AI agents.

    Features:
    - Collect and store user feedback
    - Build knowledge base from successful analyses
    - Track performance metrics over time
    - Provide similar document recommendations
    - Learn user preferences
    - Support fine-tuning and prompt optimization
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # FEEDBACK COLLECTION
    # =========================================================================

    def record_feedback(
        self,
        document_id: Optional[str],
        session_id: str,
        request_type: str,
        model_used: str,
        response_text: str,
        user_rating: int,
        was_helpful: bool = True,
        was_accurate: bool = True,
        feedback_text: Optional[str] = None,
        corrected_response: Optional[str] = None,
        confidence_score: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        token_count: Optional[int] = None,
        cost_usd: Optional[float] = None,
        prompt_version: str = "1.0"
    ) -> AIFeedback:
        """
        Record user feedback on an AI response.

        Args:
            document_id: Document being analyzed
            session_id: Session identifier
            request_type: Type of request (analysis, classification, etc.)
            model_used: AI model name
            response_text: AI's response
            user_rating: 1-5 star rating
            was_helpful: Whether response was helpful
            was_accurate: Whether response was accurate
            feedback_text: Optional feedback comments
            corrected_response: User's correction if response was wrong
            confidence_score: AI's confidence
            processing_time_ms: Processing time
            token_count: Tokens used
            cost_usd: Cost in USD
            prompt_version: Version of prompt used

        Returns:
            Created AIFeedback object
        """
        feedback = AIFeedback(
            document_id=document_id,
            session_id=session_id,
            request_type=request_type,
            model_used=model_used,
            response_text=response_text,
            user_rating=user_rating,
            was_helpful=was_helpful,
            was_accurate=was_accurate,
            feedback_text=feedback_text,
            corrected_response=corrected_response,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            token_count=token_count,
            cost_usd=cost_usd,
            prompt_version=prompt_version
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        logger.info(f"Recorded feedback: {request_type} - Rating: {user_rating}/5")

        # If highly rated, extract as knowledge
        if user_rating >= 4 and was_accurate:
            self._extract_knowledge_from_feedback(feedback)

        return feedback

    def _extract_knowledge_from_feedback(self, feedback: AIFeedback):
        """Extract reusable knowledge from highly-rated feedback"""
        try:
            # Extract key patterns or insights from the response
            knowledge = DocumentKnowledge(
                source_document_id=feedback.document_id,
                document_type=feedback.request_type,
                knowledge_type="successful_response",
                title=f"{feedback.request_type} - {feedback.model_used}",
                content=feedback.response_text,
                tags={"model": feedback.model_used, "rating": feedback.user_rating},
                usage_count=0,
                success_rate=1.0,
                avg_user_rating=float(feedback.user_rating)
            )

            self.db.add(knowledge)
            self.db.commit()
            logger.info(f"Extracted knowledge from highly-rated feedback (ID: {feedback.id})")

        except Exception as e:
            logger.error(f"Error extracting knowledge from feedback: {e}")

    # =========================================================================
    # KNOWLEDGE BASE (RAG)
    # =========================================================================

    def add_knowledge(
        self,
        document_id: str,
        knowledge_type: str,
        title: str,
        content: str,
        document_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        practice_area: Optional[str] = None,
        tags: Optional[Dict] = None
    ) -> DocumentKnowledge:
        """
        Add new knowledge to the knowledge base.

        Args:
            document_id: Source document ID
            knowledge_type: Type of knowledge (pattern, precedent, clause, etc.)
            title: Brief description
            content: Full knowledge content
            document_type: Type of document
            jurisdiction: Legal jurisdiction
            practice_area: Practice area
            tags: Searchable tags

        Returns:
            Created DocumentKnowledge object
        """
        knowledge = DocumentKnowledge(
            source_document_id=document_id,
            document_type=document_type or "general",
            knowledge_type=knowledge_type,
            title=title,
            content=content,
            jurisdiction=jurisdiction,
            practice_area=practice_area,
            tags=tags or {},
            usage_count=0,
            success_rate=1.0,
            avg_user_rating=5.0
        )

        self.db.add(knowledge)
        self.db.commit()
        self.db.refresh(knowledge)

        logger.info(f"Added knowledge: {knowledge_type} - {title}")
        return knowledge

    def search_knowledge(
        self,
        query: str,
        knowledge_type: Optional[str] = None,
        document_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        practice_area: Optional[str] = None,
        limit: int = 10
    ) -> List[DocumentKnowledge]:
        """
        Search the knowledge base (simple text-based for now).

        In production, this would use vector embeddings and similarity search.

        Args:
            query: Search query
            knowledge_type: Filter by knowledge type
            document_type: Filter by document type
            jurisdiction: Filter by jurisdiction
            practice_area: Filter by practice area
            limit: Maximum results

        Returns:
            List of matching knowledge items, ordered by quality
        """
        filters = []

        if knowledge_type:
            filters.append(DocumentKnowledge.knowledge_type == knowledge_type)
        if document_type:
            filters.append(DocumentKnowledge.document_type == document_type)
        if jurisdiction:
            filters.append(DocumentKnowledge.jurisdiction == jurisdiction)
        if practice_area:
            filters.append(DocumentKnowledge.practice_area == practice_area)

        # Simple text search (in production, use vector similarity)
        query_filter = DocumentKnowledge.content.contains(query) | \
                      DocumentKnowledge.title.contains(query)

        results = self.db.query(DocumentKnowledge).filter(
            and_(*filters) if filters else True,
            query_filter
        ).order_by(
            desc(DocumentKnowledge.success_rate),
            desc(DocumentKnowledge.usage_count)
        ).limit(limit).all()

        # Update usage count for retrieved knowledge
        for item in results:
            item.usage_count += 1
            item.last_used_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Knowledge search: '{query}' - Found {len(results)} items")
        return results

    def get_similar_documents(
        self,
        document_id: str,
        min_similarity: float = 0.7,
        limit: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Find documents similar to the given document.

        Args:
            document_id: Document to find similarities for
            min_similarity: Minimum similarity score (0-1)
            limit: Maximum results

        Returns:
            List of (Document, similarity_score) tuples
        """
        similarities = self.db.query(DocumentSimilarity).filter(
            and_(
                DocumentSimilarity.document_a_id == document_id,
                DocumentSimilarity.similarity_score >= min_similarity
            )
        ).order_by(desc(DocumentSimilarity.similarity_score)).limit(limit).all()

        results = [(sim.document_b, sim.similarity_score) for sim in similarities]

        logger.info(f"Found {len(results)} similar documents for {document_id}")
        return results

    # =========================================================================
    # PERFORMANCE TRACKING
    # =========================================================================

    def track_performance(
        self,
        metric_type: str,
        task_type: str,
        model_name: str,
        value: float,
        sample_size: int,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> PerformanceMetric:
        """
        Track a performance metric.

        Args:
            metric_type: Type of metric (accuracy, precision, recall, etc.)
            task_type: Type of task (classification, extraction, etc.)
            model_name: Model being measured
            value: Metric value
            sample_size: Number of samples
            category: Optional category
            subcategory: Optional subcategory
            metadata: Additional metadata

        Returns:
            Created PerformanceMetric object
        """
        now = datetime.utcnow()
        metric = PerformanceMetric(
            metric_type=metric_type,
            task_type=task_type,
            model_name=model_name,
            value=value,
            sample_size=sample_size,
            category=category,
            subcategory=subcategory,
            period_start=now - timedelta(days=1),
            period_end=now,
            measured_at=now,
            metadata_info=metadata or {}
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)

        logger.info(f"Tracked metric: {metric_type} for {task_type} = {value:.3f}")
        return metric

    def get_performance_trends(
        self,
        metric_type: str,
        task_type: str,
        model_name: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get performance trends over time.

        Args:
            metric_type: Metric type to track
            task_type: Task type
            model_name: Model name
            days: Number of days to look back

        Returns:
            List of metric data points with timestamps
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        metrics = self.db.query(PerformanceMetric).filter(
            and_(
                PerformanceMetric.metric_type == metric_type,
                PerformanceMetric.task_type == task_type,
                PerformanceMetric.model_name == model_name,
                PerformanceMetric.measured_at >= cutoff_date
            )
        ).order_by(PerformanceMetric.measured_at).all()

        trends = [
            {
                "date": m.measured_at.isoformat(),
                "value": m.value,
                "sample_size": m.sample_size
            }
            for m in metrics
        ]

        logger.info(f"Retrieved {len(trends)} performance data points for {model_name}")
        return trends

    def calculate_improvement(
        self,
        metric_type: str,
        task_type: str,
        model_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate improvement percentage over time.

        Args:
            metric_type: Metric type
            task_type: Task type
            model_name: Model name
            days: Period to analyze

        Returns:
            Dict with baseline, current, and improvement percentage
        """
        trends = self.get_performance_trends(metric_type, task_type, model_name, days)

        if len(trends) < 2:
            return {
                "baseline": None,
                "current": None,
                "improvement_pct": 0.0,
                "trend": "insufficient_data"
            }

        baseline = trends[0]["value"]
        current = trends[-1]["value"]
        improvement_pct = ((current - baseline) / baseline) * 100 if baseline > 0 else 0

        return {
            "baseline": baseline,
            "current": current,
            "improvement_pct": improvement_pct,
            "trend": "improving" if improvement_pct > 0 else "declining",
            "data_points": len(trends)
        }

    # =========================================================================
    # USER PREFERENCE LEARNING
    # =========================================================================

    def learn_preference(
        self,
        user_id: Optional[str],
        firm_id: Optional[str],
        preference_type: str,
        preference_key: str,
        preference_value: Any,
        confidence: float = 0.5
    ) -> UserPreference:
        """
        Learn a user or firm preference.

        Args:
            user_id: User identifier
            firm_id: Firm identifier
            preference_type: Type of preference
            preference_key: Preference key
            preference_value: Preference value
            confidence: Confidence in this preference (0-1)

        Returns:
            Created or updated UserPreference object
        """
        # Check if preference already exists
        existing = self.db.query(UserPreference).filter(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.firm_id == firm_id,
                UserPreference.preference_type == preference_type,
                UserPreference.preference_key == preference_key
            )
        ).first()

        if existing:
            # Update existing preference
            existing.preference_value = preference_value
            existing.confidence = min(1.0, existing.confidence + 0.1)  # Increase confidence
            existing.evidence_count += 1
            existing.last_observed = datetime.utcnow()
            self.db.commit()
            logger.info(f"Updated preference: {preference_key} (confidence: {existing.confidence:.2f})")
            return existing
        else:
            # Create new preference
            pref = UserPreference(
                user_id=user_id,
                firm_id=firm_id,
                preference_type=preference_type,
                preference_key=preference_key,
                preference_value=preference_value,
                confidence=confidence,
                evidence_count=1
            )
            self.db.add(pref)
            self.db.commit()
            self.db.refresh(pref)
            logger.info(f"Learned new preference: {preference_key}")
            return pref

    def get_preferences(
        self,
        user_id: Optional[str] = None,
        firm_id: Optional[str] = None,
        preference_type: Optional[str] = None
    ) -> List[UserPreference]:
        """
        Get learned preferences for a user or firm.

        Args:
            user_id: User identifier
            firm_id: Firm identifier
            preference_type: Filter by preference type

        Returns:
            List of preferences, ordered by confidence
        """
        filters = []

        if user_id:
            filters.append(UserPreference.user_id == user_id)
        if firm_id:
            filters.append(UserPreference.firm_id == firm_id)
        if preference_type:
            filters.append(UserPreference.preference_type == preference_type)

        prefs = self.db.query(UserPreference).filter(
            and_(*filters) if filters else True
        ).order_by(desc(UserPreference.confidence)).all()

        logger.info(f"Retrieved {len(prefs)} preferences")
        return prefs

    # =========================================================================
    # LEARNING TASKS
    # =========================================================================

    def create_learning_task(
        self,
        task_type: str,
        config: Dict[str, Any],
        created_by: str = "system"
    ) -> LearningTask:
        """
        Create a new learning task (e.g., fine-tuning, prompt optimization).

        Args:
            task_type: Type of learning task
            config: Task configuration
            created_by: Who created the task

        Returns:
            Created LearningTask object
        """
        task = LearningTask(
            task_type=task_type,
            status="pending",
            config=config,
            created_by=created_by
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        logger.info(f"Created learning task: {task_type} (ID: {task.id})")
        return task

    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        Get overall learning system statistics.

        Returns:
            Dict with various statistics about the learning system
        """
        total_feedback = self.db.query(func.count(AIFeedback.id)).scalar()
        avg_rating = self.db.query(func.avg(AIFeedback.user_rating)).scalar() or 0
        total_knowledge = self.db.query(func.count(DocumentKnowledge.id)).scalar()
        total_metrics = self.db.query(func.count(PerformanceMetric.id)).scalar()

        # Get feedback distribution by rating
        feedback_dist = self.db.query(
            AIFeedback.user_rating,
            func.count(AIFeedback.id)
        ).group_by(AIFeedback.user_rating).all()

        rating_distribution = {rating: count for rating, count in feedback_dist}

        # Get most common request types
        request_types = self.db.query(
            AIFeedback.request_type,
            func.count(AIFeedback.id).label('count')
        ).group_by(AIFeedback.request_type).order_by(desc('count')).limit(10).all()

        stats = {
            "total_feedback_items": total_feedback,
            "average_user_rating": round(float(avg_rating), 2),
            "total_knowledge_items": total_knowledge,
            "total_performance_metrics": total_metrics,
            "rating_distribution": rating_distribution,
            "top_request_types": [{"type": rt, "count": cnt} for rt, cnt in request_types],
            "learning_status": "active" if total_feedback > 0 else "initializing"
        }

        logger.info(f"Learning statistics: {total_feedback} feedback, {total_knowledge} knowledge items")
        return stats


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_learning_service(db: Session) -> LearningService:
    """Get LearningService instance"""
    return LearningService(db)
