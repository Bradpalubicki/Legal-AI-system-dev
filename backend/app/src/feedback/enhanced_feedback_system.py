"""
Enhanced Feedback System for Legal AI

Improved feedback system with proper database management, connection pooling,
real-time processing, and comprehensive analytics.
"""

import sqlite3
import asyncio
import aiofiles
import logging
import statistics
import threading
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from contextlib import asynccontextmanager
import json
import uuid
import os

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    ACCURACY = "accuracy"
    USEFULNESS = "usefulness"
    ERROR_REPORT = "error_report"
    SUGGESTION = "suggestion"
    CORRECTION = "correction"
    GENERAL = "general"
    COMPLIANCE_ISSUE = "compliance_issue"


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
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class EnhancedFeedback:
    id: str
    user_id: str
    session_id: str
    content_id: str
    feedback_type: FeedbackType
    rating: Optional[Union[AccuracyRating, UsefulnessRating]] = None
    comment: Optional[str] = None
    specific_issues: List[str] = field(default_factory=list)
    suggestions: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    attorney_flagged: bool = False
    compliance_impact: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None
    escalated_at: Optional[datetime] = None


@dataclass
class FeedbackMetrics:
    total_feedback_count: int
    accuracy_distribution: Dict[str, int]
    usefulness_distribution: Dict[str, int]
    average_accuracy_score: float
    average_usefulness_score: float
    critical_issues_count: int
    resolution_rate: float
    response_time_hours: float
    user_satisfaction_score: float
    period_start: datetime
    period_end: datetime


class DatabaseManager:
    """Enhanced database manager with connection pooling and async support"""

    def __init__(self, db_path: str = "data/enhanced_feedback.db"):
        self.db_path = db_path
        self.connection_pool = []
        self.pool_size = 5
        self._lock = threading.Lock()
        self._initialized = False

    def initialize_database(self):
        """Initialize database with proper schema"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create feedback table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            content_id TEXT NOT NULL,
            feedback_type TEXT NOT NULL,
            rating TEXT,
            comment TEXT,
            specific_issues TEXT,
            suggestions TEXT,
            metadata TEXT,
            timestamp TEXT NOT NULL,
            processing_status TEXT DEFAULT 'pending',
            attorney_flagged BOOLEAN DEFAULT FALSE,
            compliance_impact BOOLEAN DEFAULT FALSE,
            resolved BOOLEAN DEFAULT FALSE,
            resolution_notes TEXT,
            escalated_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_content_id ON feedback(content_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(processing_status)")

        # Create feedback analytics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_analytics (
            id TEXT PRIMARY KEY,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create user acknowledgments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_acknowledgments (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            acknowledgment_type TEXT NOT NULL,
            content TEXT NOT NULL,
            acknowledged_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ack_user_id ON user_acknowledgments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ack_type ON user_acknowledgments(acknowledgment_type)")

        conn.commit()
        conn.close()

        # Initialize connection pool
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
            self.connection_pool.append(conn)

        self._initialized = True
        logger.info(f"Database initialized with {self.pool_size} connections")

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self._initialized:
            self.initialize_database()

        conn = None
        try:
            with self._lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()

            if conn is None:
                # Create temporary connection if pool is exhausted
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")

            yield conn

        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                with self._lock:
                    if len(self.connection_pool) < self.pool_size:
                        self.connection_pool.append(conn)
                    else:
                        conn.close()

    async def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return results"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    async def execute_insert(self, query: str, params: tuple = ()) -> str:
        """Execute insert query and return last row id"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return str(cursor.lastrowid)


class EnhancedFeedbackSystem:
    """Enhanced feedback system with improved database management and analytics"""

    def __init__(self, db_path: str = "data/enhanced_feedback.db"):
        self.db_manager = DatabaseManager(db_path)
        self.processing_queue = asyncio.Queue()
        self.metrics_cache = {}
        self.cache_expiry = {}
        self._processing_task = None
        self._running = False

    async def initialize(self):
        """Initialize the feedback system"""
        self.db_manager.initialize_database()
        self._running = True
        self._processing_task = asyncio.create_task(self._process_feedback_queue())
        logger.info("Enhanced feedback system initialized")

    async def shutdown(self):
        """Shutdown the feedback system"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Enhanced feedback system shut down")

    async def submit_feedback(
        self,
        user_id: str,
        content_id: str,
        feedback_type: FeedbackType,
        rating: Optional[Union[AccuracyRating, UsefulnessRating]] = None,
        comment: Optional[str] = None,
        specific_issues: List[str] = None,
        suggestions: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Submit comprehensive feedback"""

        feedback_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())

        # Determine if this is a critical issue
        attorney_flagged = self._should_flag_for_attorney_review(rating, comment, specific_issues)
        compliance_impact = self._has_compliance_impact(feedback_type, rating, specific_issues)

        feedback = EnhancedFeedback(
            id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            content_id=content_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            specific_issues=specific_issues or [],
            suggestions=suggestions,
            metadata=metadata or {},
            attorney_flagged=attorney_flagged,
            compliance_impact=compliance_impact
        )

        # Store in database
        await self._store_feedback(feedback)

        # Add to processing queue
        await self.processing_queue.put(feedback)

        logger.info(f"Feedback submitted: {feedback_id} (attorney_flagged: {attorney_flagged})")
        return feedback_id

    async def _store_feedback(self, feedback: EnhancedFeedback):
        """Store feedback in database"""
        query = """
        INSERT INTO feedback (
            id, user_id, session_id, content_id, feedback_type, rating, comment,
            specific_issues, suggestions, metadata, timestamp, processing_status,
            attorney_flagged, compliance_impact, resolved, escalated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            feedback.id,
            feedback.user_id,
            feedback.session_id,
            feedback.content_id,
            feedback.feedback_type.value,
            feedback.rating.value if feedback.rating else None,
            feedback.comment,
            json.dumps(feedback.specific_issues),
            feedback.suggestions,
            json.dumps(feedback.metadata),
            feedback.timestamp.isoformat(),
            feedback.processing_status.value,
            feedback.attorney_flagged,
            feedback.compliance_impact,
            feedback.resolved,
            feedback.escalated_at.isoformat() if feedback.escalated_at else None
        )

        await self.db_manager.execute_insert(query, params)

    def _should_flag_for_attorney_review(
        self,
        rating: Optional[Union[AccuracyRating, UsefulnessRating]],
        comment: Optional[str],
        specific_issues: Optional[List[str]]
    ) -> bool:
        """Determine if feedback should be flagged for attorney review"""

        # Flag critical accuracy issues
        if isinstance(rating, AccuracyRating):
            if rating in [AccuracyRating.MOSTLY_INACCURATE, AccuracyRating.COMPLETELY_INACCURATE]:
                return True

        # Flag critical keywords in comments
        if comment:
            critical_keywords = [
                "legal advice", "wrong", "incorrect", "dangerous", "lawsuit",
                "sue", "attorney malpractice", "ethical violation", "misleading",
                "unauthorized practice", "upl"
            ]
            comment_lower = comment.lower()
            if any(keyword in comment_lower for keyword in critical_keywords):
                return True

        # Flag specific critical issues
        if specific_issues:
            critical_issues = [
                "factual_error", "legal_inaccuracy", "ethical_concern",
                "unauthorized_practice", "misleading_advice"
            ]
            if any(issue in specific_issues for issue in critical_issues):
                return True

        return False

    def _has_compliance_impact(
        self,
        feedback_type: FeedbackType,
        rating: Optional[Union[AccuracyRating, UsefulnessRating]],
        specific_issues: Optional[List[str]]
    ) -> bool:
        """Determine if feedback has compliance implications"""

        # Compliance-related feedback types
        if feedback_type == FeedbackType.COMPLIANCE_ISSUE:
            return True

        # Critical accuracy issues affect compliance
        if isinstance(rating, AccuracyRating):
            if rating == AccuracyRating.COMPLETELY_INACCURATE:
                return True

        # Specific compliance-related issues
        if specific_issues:
            compliance_issues = [
                "unauthorized_practice", "legal_advice", "ethical_violation",
                "disclaimer_missing", "attorney_client_confusion"
            ]
            if any(issue in specific_issues for issue in compliance_issues):
                return True

        return False

    async def _process_feedback_queue(self):
        """Process feedback queue for real-time analytics and escalation"""
        while self._running:
            try:
                # Process feedback with timeout
                feedback = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)

                # Update processing status
                await self._update_feedback_status(feedback.id, ProcessingStatus.PROCESSING)

                # Process the feedback
                await self._process_individual_feedback(feedback)

                # Mark as completed
                await self._update_feedback_status(feedback.id, ProcessingStatus.COMPLETED)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing feedback: {e}")

    async def _process_individual_feedback(self, feedback: EnhancedFeedback):
        """Process individual feedback item"""

        # Escalate if needed
        if feedback.attorney_flagged or feedback.compliance_impact:
            await self._escalate_feedback(feedback)

        # Update analytics
        await self._update_real_time_analytics(feedback)

        # Notify if critical
        if feedback.attorney_flagged:
            await self._send_critical_feedback_notification(feedback)

    async def _update_feedback_status(self, feedback_id: str, status: ProcessingStatus):
        """Update feedback processing status"""
        query = """
        UPDATE feedback
        SET processing_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        async with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (status.value, feedback_id))
            conn.commit()

    async def _escalate_feedback(self, feedback: EnhancedFeedback):
        """Escalate critical feedback to attorney review"""

        escalated_at = datetime.now()

        query = """
        UPDATE feedback
        SET escalated_at = ?, processing_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        async with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (escalated_at.isoformat(), ProcessingStatus.ESCALATED.value, feedback.id))
            conn.commit()

        logger.warning(f"Feedback escalated to attorney review: {feedback.id}")

    async def _update_real_time_analytics(self, feedback: EnhancedFeedback):
        """Update real-time analytics"""
        # Cache key for hourly metrics
        hour_key = feedback.timestamp.strftime("%Y-%m-%d-%H")

        if hour_key not in self.metrics_cache:
            self.metrics_cache[hour_key] = {
                "total_count": 0,
                "accuracy_ratings": [],
                "usefulness_ratings": [],
                "critical_issues": 0,
                "escalations": 0
            }

        # Update cached metrics
        metrics = self.metrics_cache[hour_key]
        metrics["total_count"] += 1

        if isinstance(feedback.rating, AccuracyRating):
            metrics["accuracy_ratings"].append(feedback.rating.value)
        elif isinstance(feedback.rating, UsefulnessRating):
            metrics["usefulness_ratings"].append(feedback.rating.value)

        if feedback.attorney_flagged:
            metrics["critical_issues"] += 1

        if feedback.compliance_impact:
            metrics["escalations"] += 1

    async def _send_critical_feedback_notification(self, feedback: EnhancedFeedback):
        """Send notification for critical feedback"""
        # In a real implementation, this would send notifications via email, Slack, etc.
        logger.critical(f"CRITICAL FEEDBACK ALERT: {feedback.id} - {feedback.feedback_type.value}")

        notification = {
            "type": "critical_feedback",
            "feedback_id": feedback.id,
            "user_id": feedback.user_id,
            "content_id": feedback.content_id,
            "rating": feedback.rating.value if feedback.rating else None,
            "comment": feedback.comment,
            "attorney_flagged": feedback.attorney_flagged,
            "compliance_impact": feedback.compliance_impact,
            "timestamp": feedback.timestamp.isoformat()
        }

        # Store notification for later processing
        await self._store_notification(notification)

    async def _store_notification(self, notification: Dict[str, Any]):
        """Store notification in database"""
        # Implementation would store notifications for external systems
        pass

    async def get_feedback_metrics(self, hours: int = 24) -> FeedbackMetrics:
        """Get comprehensive feedback metrics"""

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # Check cache first
        cache_key = f"metrics_{hours}_{end_time.strftime('%Y%m%d%H')}"
        if cache_key in self.metrics_cache and cache_key in self.cache_expiry:
            if datetime.now() < self.cache_expiry[cache_key]:
                return self.metrics_cache[cache_key]

        # Query database for metrics
        query = """
        SELECT
            feedback_type,
            rating,
            processing_status,
            attorney_flagged,
            compliance_impact,
            resolved,
            timestamp
        FROM feedback
        WHERE timestamp >= ? AND timestamp <= ?
        """

        results = await self.db_manager.execute_query(
            query,
            (start_time.isoformat(), end_time.isoformat())
        )

        # Calculate metrics
        total_count = len(results)
        accuracy_ratings = []
        usefulness_ratings = []
        critical_issues = 0
        resolved_count = 0

        for row in results:
            if row['rating']:
                if 'accurate' in row['rating']:
                    accuracy_ratings.append(row['rating'])
                elif 'useful' in row['rating']:
                    usefulness_ratings.append(row['rating'])

            if row['attorney_flagged']:
                critical_issues += 1

            if row['resolved']:
                resolved_count += 1

        # Calculate scores
        accuracy_score = self._calculate_rating_score(accuracy_ratings, AccuracyRating)
        usefulness_score = self._calculate_rating_score(usefulness_ratings, UsefulnessRating)
        resolution_rate = resolved_count / total_count if total_count > 0 else 0

        metrics = FeedbackMetrics(
            total_feedback_count=total_count,
            accuracy_distribution=Counter(accuracy_ratings),
            usefulness_distribution=Counter(usefulness_ratings),
            average_accuracy_score=accuracy_score,
            average_usefulness_score=usefulness_score,
            critical_issues_count=critical_issues,
            resolution_rate=resolution_rate,
            response_time_hours=self._calculate_average_response_time(results),
            user_satisfaction_score=(accuracy_score + usefulness_score) / 2,
            period_start=start_time,
            period_end=end_time
        )

        # Cache results
        self.metrics_cache[cache_key] = metrics
        self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=15)

        return metrics

    def _calculate_rating_score(self, ratings: List[str], rating_enum) -> float:
        """Calculate average score for ratings"""
        if not ratings:
            return 0.0

        # Map ratings to numeric scores
        if rating_enum == AccuracyRating:
            score_map = {
                "completely_accurate": 5.0,
                "mostly_accurate": 4.0,
                "partially_accurate": 3.0,
                "mostly_inaccurate": 2.0,
                "completely_inaccurate": 1.0
            }
        else:  # UsefulnessRating
            score_map = {
                "very_useful": 5.0,
                "somewhat_useful": 4.0,
                "neutral": 3.0,
                "not_very_useful": 2.0,
                "not_useful": 1.0
            }

        scores = [score_map.get(rating, 3.0) for rating in ratings]
        return statistics.mean(scores)

    def _calculate_average_response_time(self, results: List[Dict]) -> float:
        """Calculate average response time for resolved issues"""
        # Implementation would calculate time from submission to resolution
        return 24.0  # Placeholder

    async def track_user_acknowledgment(
        self,
        user_id: str,
        acknowledgment_type: str,
        content: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Track user acknowledgment for compliance purposes"""

        acknowledgment_id = str(uuid.uuid4())
        acknowledged_at = datetime.now()

        query = """
        INSERT INTO user_acknowledgments (
            id, user_id, acknowledgment_type, content, acknowledged_at,
            ip_address, user_agent, session_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            acknowledgment_id,
            user_id,
            acknowledgment_type,
            content,
            acknowledged_at.isoformat(),
            ip_address,
            user_agent,
            session_id
        )

        await self.db_manager.execute_insert(query, params)

        logger.info(f"User acknowledgment tracked: {acknowledgment_id}")
        return acknowledgment_id

    async def get_system_health(self) -> Dict[str, Any]:
        """Get feedback system health metrics"""

        # Check database connectivity
        try:
            await self.db_manager.execute_query("SELECT 1", ())
            db_health = "healthy"
        except Exception as e:
            db_health = f"unhealthy: {e}"

        # Check processing queue
        queue_size = self.processing_queue.qsize()
        queue_health = "healthy" if queue_size < 100 else "overloaded"

        # Check recent metrics
        recent_metrics = await self.get_feedback_metrics(hours=1)

        return {
            "status": "healthy" if db_health == "healthy" and queue_health == "healthy" else "degraded",
            "database": db_health,
            "processing_queue": {
                "status": queue_health,
                "size": queue_size
            },
            "recent_activity": {
                "feedback_count_1h": recent_metrics.total_feedback_count,
                "critical_issues_1h": recent_metrics.critical_issues_count,
                "resolution_rate": recent_metrics.resolution_rate
            },
            "cache_size": len(self.metrics_cache),
            "system_running": self._running
        }

    async def resolve_feedback(self, feedback_id: str, resolution_notes: str) -> bool:
        """Mark feedback as resolved"""

        query = """
        UPDATE feedback
        SET resolved = TRUE, resolution_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        try:
            async with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (resolution_notes, feedback_id))
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Feedback resolved: {feedback_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error resolving feedback {feedback_id}: {e}")
            return False