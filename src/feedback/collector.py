"""
AI Improvement Feedback System

Comprehensive feedback collection and analysis system for continuous AI improvement
including user corrections, attorney verification, outcome tracking, accuracy ratings,
false positive/negative tracking, and automated training data generation.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import uuid
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import pickle
import base64

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback that can be collected"""
    USER_CORRECTION = "user_correction"
    ATTORNEY_VERIFICATION = "attorney_verification"
    ACCURACY_RATING = "accuracy_rating"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    OUTCOME_TRACKING = "outcome_tracking"
    PERFORMANCE_RATING = "performance_rating"
    ENHANCEMENT_REQUEST = "enhancement_request"
    BUG_REPORT = "bug_report"
    QUALITY_ASSESSMENT = "quality_assessment"


class FeedbackSeverity(Enum):
    """Severity levels for feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackSource(Enum):
    """Source of the feedback"""
    USER_INTERFACE = "user_interface"
    ATTORNEY_REVIEW = "attorney_review"
    AUTOMATED_ANALYSIS = "automated_analysis"
    CASE_OUTCOME = "case_outcome"
    PEER_REVIEW = "peer_review"
    BATCH_PROCESSING = "batch_processing"


class AIModelType(Enum):
    """Types of AI models in the system"""
    DOCUMENT_ANALYZER = "document_analyzer"
    LEGAL_RESEARCH = "legal_research"
    CITATION_PARSER = "citation_parser"
    RISK_ASSESSOR = "risk_assessor"
    COMPLIANCE_CHECKER = "compliance_checker"
    CONTRACT_ANALYZER = "contract_analyzer"
    CASE_PREDICTOR = "case_predictor"
    QUESTION_GENERATOR = "question_generator"
    DEFENSE_IDENTIFIER = "defense_identifier"
    PRECEDENT_FINDER = "precedent_finder"
    SUMMARY_GENERATOR = "summary_generator"


class CaseOutcome(Enum):
    """Possible case outcomes"""
    WON = "won"
    LOST = "lost"
    SETTLED = "settled"
    DISMISSED = "dismissed"
    WITHDRAWN = "withdrawn"
    ONGOING = "ongoing"
    PENDING = "pending"


@dataclass
class UserCorrection:
    """User correction to AI output"""
    correction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    model_type: AIModelType = AIModelType.DOCUMENT_ANALYZER
    model_version: str = ""
    original_input: str = ""
    original_output: str = ""
    corrected_output: str = ""
    correction_reason: str = ""
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified_by_attorney: bool = False
    attorney_notes: str = ""


@dataclass
class AttorneyVerification:
    """Attorney verification of AI analysis"""
    verification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attorney_id: str = ""
    attorney_name: str = ""
    bar_number: str = ""
    years_experience: Optional[int] = None
    specialization: List[str] = field(default_factory=list)
    analysis_id: str = ""
    model_type: AIModelType = AIModelType.DOCUMENT_ANALYZER
    model_version: str = ""
    verification_status: str = "pending"  # pending, approved, rejected, needs_revision
    accuracy_score: float = 0.0  # 0.0 to 1.0
    completeness_score: float = 0.0  # 0.0 to 1.0
    relevance_score: float = 0.0  # 0.0 to 1.0
    overall_quality: float = 0.0  # 0.0 to 1.0
    detailed_feedback: str = ""
    improvement_suggestions: List[str] = field(default_factory=list)
    time_saved_estimate: Optional[int] = None  # minutes
    would_use_again: bool = False
    recommend_to_colleagues: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class OutcomeTracking:
    """Track actual case outcomes for prediction validation"""
    outcome_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str = ""
    prediction_id: str = ""
    model_type: AIModelType = AIModelType.CASE_PREDICTOR
    model_version: str = ""
    predicted_outcome: str = ""
    predicted_confidence: float = 0.0
    predicted_factors: List[str] = field(default_factory=list)
    actual_outcome: CaseOutcome = CaseOutcome.PENDING
    outcome_date: Optional[datetime] = None
    outcome_factors: List[str] = field(default_factory=list)
    accuracy_score: Optional[float] = None
    prediction_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    follow_up_analysis: str = ""
    lessons_learned: str = ""


@dataclass
class AccuracyRating:
    """Accuracy rating from users"""
    rating_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    user_type: str = "attorney"  # attorney, paralegal, student, etc.
    model_type: AIModelType = AIModelType.DOCUMENT_ANALYZER
    model_version: str = ""
    analysis_id: str = ""
    accuracy_score: float = 0.0  # 0.0 to 1.0
    usefulness_score: float = 0.0  # 0.0 to 1.0
    clarity_score: float = 0.0  # 0.0 to 1.0
    completeness_score: float = 0.0  # 0.0 to 1.0
    overall_satisfaction: float = 0.0  # 0.0 to 1.0
    specific_feedback: str = ""
    areas_for_improvement: List[str] = field(default_factory=list)
    most_helpful_features: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FalsePositiveNegative:
    """False positive/negative tracking"""
    fp_fn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    model_type: AIModelType = AIModelType.DOCUMENT_ANALYZER
    model_version: str = ""
    analysis_id: str = ""
    fp_fn_type: str = "false_positive"  # false_positive, false_negative
    description: str = ""
    expected_result: str = ""
    actual_result: str = ""
    impact_assessment: FeedbackSeverity = FeedbackSeverity.MEDIUM
    context_information: Dict[str, Any] = field(default_factory=dict)
    reproduction_steps: str = ""
    suggested_fix: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FeedbackAnalytics:
    """Analytics derived from feedback data"""
    analytics_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    period_start: datetime
    period_end: datetime
    model_type: AIModelType
    model_version: str
    total_feedback_count: int = 0
    correction_count: int = 0
    verification_count: int = 0
    average_accuracy: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    attorney_approval_rate: float = 0.0
    user_satisfaction: float = 0.0
    improvement_trends: Dict[str, List[float]] = field(default_factory=dict)
    common_issues: List[Dict[str, Any]] = field(default_factory=list)
    suggested_improvements: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class FeedbackCollector:
    """
    Comprehensive AI improvement feedback collection system

    Features:
    - User corrections and attorney verification
    - Outcome tracking for prediction validation
    - Accuracy ratings and performance metrics
    - False positive/negative detection and analysis
    - Automated training data generation
    - Real-time feedback analytics
    - Continuous learning integration
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.feedback_db_path = config.get('feedback_db_path', 'data/ai_feedback.db')
        self.min_quality_threshold = config.get('min_quality_threshold', 0.7)
        self.auto_training_enabled = config.get('auto_training_enabled', True)

        # Initialize database
        self._init_feedback_database()

        # Analytics cache
        self._analytics_cache = {}
        self._cache_duration = timedelta(minutes=15)

        # Feedback processors
        self._feedback_processors = {
            FeedbackType.USER_CORRECTION: self._process_user_correction,
            FeedbackType.ATTORNEY_VERIFICATION: self._process_attorney_verification,
            FeedbackType.OUTCOME_TRACKING: self._process_outcome_tracking,
            FeedbackType.ACCURACY_RATING: self._process_accuracy_rating,
            FeedbackType.FALSE_POSITIVE: self._process_false_positive,
            FeedbackType.FALSE_NEGATIVE: self._process_false_negative
        }

    def _init_feedback_database(self):
        """Initialize comprehensive feedback database"""
        logger.info("Initializing AI feedback database...")

        Path(self.feedback_db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.feedback_db_path)
        try:
            # User corrections table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_corrections (
                    correction_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    original_input TEXT NOT NULL,
                    original_output TEXT NOT NULL,
                    corrected_output TEXT NOT NULL,
                    correction_reason TEXT,
                    confidence_before REAL,
                    confidence_after REAL,
                    severity TEXT NOT NULL,
                    context TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    verified_by_attorney BOOLEAN DEFAULT FALSE,
                    attorney_notes TEXT,
                    used_for_training BOOLEAN DEFAULT FALSE,
                    training_batch_id TEXT
                )
            """)

            # Attorney verifications table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attorney_verifications (
                    verification_id TEXT PRIMARY KEY,
                    attorney_id TEXT NOT NULL,
                    attorney_name TEXT NOT NULL,
                    bar_number TEXT,
                    years_experience INTEGER,
                    specialization TEXT,
                    analysis_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    accuracy_score REAL NOT NULL,
                    completeness_score REAL NOT NULL,
                    relevance_score REAL NOT NULL,
                    overall_quality REAL NOT NULL,
                    detailed_feedback TEXT,
                    improvement_suggestions TEXT,
                    time_saved_estimate INTEGER,
                    would_use_again BOOLEAN,
                    recommend_to_colleagues BOOLEAN,
                    timestamp TIMESTAMP NOT NULL
                )
            """)

            # Outcome tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outcome_tracking (
                    outcome_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    prediction_id TEXT,
                    model_type TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    predicted_outcome TEXT,
                    predicted_confidence REAL,
                    predicted_factors TEXT,
                    actual_outcome TEXT NOT NULL,
                    outcome_date TIMESTAMP,
                    outcome_factors TEXT,
                    accuracy_score REAL,
                    prediction_date TIMESTAMP NOT NULL,
                    follow_up_analysis TEXT,
                    lessons_learned TEXT
                )
            """)

            # Accuracy ratings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accuracy_ratings (
                    rating_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_type TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    accuracy_score REAL NOT NULL,
                    usefulness_score REAL NOT NULL,
                    clarity_score REAL NOT NULL,
                    completeness_score REAL NOT NULL,
                    overall_satisfaction REAL NOT NULL,
                    specific_feedback TEXT,
                    areas_for_improvement TEXT,
                    most_helpful_features TEXT,
                    timestamp TIMESTAMP NOT NULL
                )
            """)

            # False positive/negative tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS false_positive_negative (
                    fp_fn_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    fp_fn_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expected_result TEXT,
                    actual_result TEXT,
                    impact_assessment TEXT NOT NULL,
                    context_information TEXT,
                    reproduction_steps TEXT,
                    suggested_fix TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT
                )
            """)

            # Training data queue table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_data_queue (
                    queue_id TEXT PRIMARY KEY,
                    source_feedback_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    input_data TEXT NOT NULL,
                    expected_output TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    priority INTEGER NOT NULL,
                    created_timestamp TIMESTAMP NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_timestamp TIMESTAMP,
                    batch_id TEXT
                )
            """)

            # Feedback analytics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_analytics (
                    analytics_id TEXT PRIMARY KEY,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    model_type TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    total_feedback_count INTEGER NOT NULL,
                    correction_count INTEGER NOT NULL,
                    verification_count INTEGER NOT NULL,
                    average_accuracy REAL NOT NULL,
                    false_positive_rate REAL NOT NULL,
                    false_negative_rate REAL NOT NULL,
                    attorney_approval_rate REAL NOT NULL,
                    user_satisfaction REAL NOT NULL,
                    improvement_trends TEXT,
                    common_issues TEXT,
                    suggested_improvements TEXT,
                    performance_metrics TEXT,
                    created_timestamp TIMESTAMP NOT NULL
                )
            """)

            # Model performance tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    performance_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    date DATE NOT NULL,
                    total_uses INTEGER DEFAULT 0,
                    positive_feedback INTEGER DEFAULT 0,
                    negative_feedback INTEGER DEFAULT 0,
                    average_accuracy REAL DEFAULT 0.0,
                    false_positive_count INTEGER DEFAULT 0,
                    false_negative_count INTEGER DEFAULT 0,
                    attorney_verifications INTEGER DEFAULT 0,
                    attorney_approvals INTEGER DEFAULT 0,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(model_type, model_version, date)
                )
            """)

            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_corrections_model ON user_corrections(model_type, model_version)",
                "CREATE INDEX IF NOT EXISTS idx_corrections_timestamp ON user_corrections(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_verifications_attorney ON attorney_verifications(attorney_id)",
                "CREATE INDEX IF NOT EXISTS idx_verifications_model ON attorney_verifications(model_type, model_version)",
                "CREATE INDEX IF NOT EXISTS idx_outcomes_case ON outcome_tracking(case_id)",
                "CREATE INDEX IF NOT EXISTS idx_outcomes_model ON outcome_tracking(model_type, model_version)",
                "CREATE INDEX IF NOT EXISTS idx_ratings_model ON accuracy_ratings(model_type, model_version)",
                "CREATE INDEX IF NOT EXISTS idx_fp_fn_model ON false_positive_negative(model_type, model_version)",
                "CREATE INDEX IF NOT EXISTS idx_training_queue_processed ON training_data_queue(processed)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_model ON feedback_analytics(model_type, model_version)",
                "CREATE INDEX IF NOT EXISTS idx_performance_model_date ON model_performance(model_type, model_version, date)"
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

            conn.commit()
            logger.info("✓ AI feedback database initialized")

        finally:
            conn.close()

    async def collect_user_correction(self, correction: UserCorrection) -> str:
        """Collect user correction feedback"""
        try:
            conn = sqlite3.connect(self.feedback_db_path)
            try:
                conn.execute("""
                    INSERT INTO user_corrections (
                        correction_id, user_id, model_type, model_version,
                        original_input, original_output, corrected_output,
                        correction_reason, confidence_before, confidence_after,
                        severity, context, timestamp, verified_by_attorney, attorney_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    correction.correction_id, correction.user_id, correction.model_type.value,
                    correction.model_version, correction.original_input, correction.original_output,
                    correction.corrected_output, correction.correction_reason,
                    correction.confidence_before, correction.confidence_after,
                    correction.severity.value, json.dumps(correction.context),
                    correction.timestamp.isoformat(), correction.verified_by_attorney,
                    correction.attorney_notes
                ))
                conn.commit()

                # Process for training data
                await self._evaluate_correction_for_training(correction)

                # Update performance metrics
                await self._update_performance_metrics(correction.model_type, correction.model_version, 'correction')

                logger.info(f"User correction collected: {correction.correction_id}")
                return correction.correction_id

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error collecting user correction: {str(e)}")
            raise

    async def collect_attorney_verification(self, verification: AttorneyVerification) -> str:
        """Collect attorney verification feedback"""
        try:
            conn = sqlite3.connect(self.feedback_db_path)
            try:
                conn.execute("""
                    INSERT INTO attorney_verifications (
                        verification_id, attorney_id, attorney_name, bar_number,
                        years_experience, specialization, analysis_id, model_type,
                        model_version, verification_status, accuracy_score,
                        completeness_score, relevance_score, overall_quality,
                        detailed_feedback, improvement_suggestions, time_saved_estimate,
                        would_use_again, recommend_to_colleagues, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    verification.verification_id, verification.attorney_id,
                    verification.attorney_name, verification.bar_number,
                    verification.years_experience, json.dumps(verification.specialization),
                    verification.analysis_id, verification.model_type.value,
                    verification.model_version, verification.verification_status,
                    verification.accuracy_score, verification.completeness_score,
                    verification.relevance_score, verification.overall_quality,
                    verification.detailed_feedback, json.dumps(verification.improvement_suggestions),
                    verification.time_saved_estimate, verification.would_use_again,
                    verification.recommend_to_colleagues, verification.timestamp.isoformat()
                ))
                conn.commit()

                # Update performance metrics
                await self._update_performance_metrics(
                    verification.model_type, verification.model_version,
                    'verification', verification.verification_status == 'approved'
                )

                logger.info(f"Attorney verification collected: {verification.verification_id}")
                return verification.verification_id

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error collecting attorney verification: {str(e)}")
            raise

    async def collect_outcome_tracking(self, outcome: OutcomeTracking) -> str:
        """Collect case outcome tracking data"""
        try:
            # Calculate accuracy score if we have both predicted and actual outcomes
            if outcome.actual_outcome != CaseOutcome.PENDING:
                outcome.accuracy_score = self._calculate_prediction_accuracy(
                    outcome.predicted_outcome, outcome.actual_outcome.value
                )

            conn = sqlite3.connect(self.feedback_db_path)
            try:
                conn.execute("""
                    INSERT INTO outcome_tracking (
                        outcome_id, case_id, prediction_id, model_type, model_version,
                        predicted_outcome, predicted_confidence, predicted_factors,
                        actual_outcome, outcome_date, outcome_factors, accuracy_score,
                        prediction_date, follow_up_analysis, lessons_learned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    outcome.outcome_id, outcome.case_id, outcome.prediction_id,
                    outcome.model_type.value, outcome.model_version,
                    outcome.predicted_outcome, outcome.predicted_confidence,
                    json.dumps(outcome.predicted_factors), outcome.actual_outcome.value,
                    outcome.outcome_date.isoformat() if outcome.outcome_date else None,
                    json.dumps(outcome.outcome_factors), outcome.accuracy_score,
                    outcome.prediction_date.isoformat(), outcome.follow_up_analysis,
                    outcome.lessons_learned
                ))
                conn.commit()

                logger.info(f"Outcome tracking collected: {outcome.outcome_id}")
                return outcome.outcome_id

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error collecting outcome tracking: {str(e)}")
            raise

    async def collect_accuracy_rating(self, rating: AccuracyRating) -> str:
        """Collect accuracy rating feedback"""
        try:
            conn = sqlite3.connect(self.feedback_db_path)
            try:
                conn.execute("""
                    INSERT INTO accuracy_ratings (
                        rating_id, user_id, user_type, model_type, model_version,
                        analysis_id, accuracy_score, usefulness_score, clarity_score,
                        completeness_score, overall_satisfaction, specific_feedback,
                        areas_for_improvement, most_helpful_features, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rating.rating_id, rating.user_id, rating.user_type,
                    rating.model_type.value, rating.model_version, rating.analysis_id,
                    rating.accuracy_score, rating.usefulness_score, rating.clarity_score,
                    rating.completeness_score, rating.overall_satisfaction,
                    rating.specific_feedback, json.dumps(rating.areas_for_improvement),
                    json.dumps(rating.most_helpful_features), rating.timestamp.isoformat()
                ))
                conn.commit()

                # Update performance metrics
                await self._update_performance_metrics(
                    rating.model_type, rating.model_version, 'rating',
                    rating.overall_satisfaction >= 0.7
                )

                logger.info(f"Accuracy rating collected: {rating.rating_id}")
                return rating.rating_id

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error collecting accuracy rating: {str(e)}")
            raise

    async def collect_false_positive_negative(self, fp_fn: FalsePositiveNegative) -> str:
        """Collect false positive/negative feedback"""
        try:
            conn = sqlite3.connect(self.feedback_db_path)
            try:
                conn.execute("""
                    INSERT INTO false_positive_negative (
                        fp_fn_id, user_id, model_type, model_version, analysis_id,
                        fp_fn_type, description, expected_result, actual_result,
                        impact_assessment, context_information, reproduction_steps,
                        suggested_fix, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fp_fn.fp_fn_id, fp_fn.user_id, fp_fn.model_type.value,
                    fp_fn.model_version, fp_fn.analysis_id, fp_fn.fp_fn_type,
                    fp_fn.description, fp_fn.expected_result, fp_fn.actual_result,
                    fp_fn.impact_assessment.value, json.dumps(fp_fn.context_information),
                    fp_fn.reproduction_steps, fp_fn.suggested_fix,
                    fp_fn.timestamp.isoformat()
                ))
                conn.commit()

                # Process for training data (high priority)
                await self._evaluate_fp_fn_for_training(fp_fn)

                # Update performance metrics
                await self._update_performance_metrics(
                    fp_fn.model_type, fp_fn.model_version, fp_fn.fp_fn_type
                )

                logger.info(f"False positive/negative collected: {fp_fn.fp_fn_id}")
                return fp_fn.fp_fn_id

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error collecting false positive/negative: {str(e)}")
            raise

    def _calculate_prediction_accuracy(self, predicted: str, actual: str) -> float:
        """Calculate accuracy score for prediction vs actual outcome"""
        if predicted.lower() == actual.lower():
            return 1.0
        elif predicted.lower() in ['won', 'favorable'] and actual.lower() in ['won', 'settled']:
            return 0.8
        elif predicted.lower() in ['lost', 'unfavorable'] and actual.lower() in ['lost', 'dismissed']:
            return 0.8
        else:
            return 0.0

    async def _evaluate_correction_for_training(self, correction: UserCorrection):
        """Evaluate user correction for training data"""
        quality_score = 0.7  # Base quality for corrections

        # Increase quality if attorney verified
        if correction.verified_by_attorney:
            quality_score += 0.2

        # Increase quality for detailed corrections
        if len(correction.corrected_output) > 50:
            quality_score += 0.1

        if quality_score >= self.min_quality_threshold:
            await self._add_to_training_queue(
                correction.correction_id, FeedbackType.USER_CORRECTION,
                correction.model_type, correction.original_input,
                correction.corrected_output, quality_score, 3
            )

    async def _evaluate_fp_fn_for_training(self, fp_fn: FalsePositiveNegative):
        """Evaluate false positive/negative for training data"""
        quality_score = 0.8  # High quality for FP/FN

        # Increase quality for detailed descriptions
        if len(fp_fn.description) > 100:
            quality_score += 0.1

        # Higher priority for high impact issues
        priority = 4 if fp_fn.impact_assessment in [FeedbackSeverity.HIGH, FeedbackSeverity.CRITICAL] else 3

        expected_output = fp_fn.expected_result if fp_fn.expected_result else "No issue detected"

        await self._add_to_training_queue(
            fp_fn.fp_fn_id, FeedbackType.FALSE_POSITIVE if fp_fn.fp_fn_type == "false_positive" else FeedbackType.FALSE_NEGATIVE,
            fp_fn.model_type, f"Analysis ID: {fp_fn.analysis_id}\nDescription: {fp_fn.description}",
            expected_output, quality_score, priority
        )

    async def _add_to_training_queue(self, source_id: str, feedback_type: FeedbackType,
                                   model_type: AIModelType, input_data: str,
                                   expected_output: str, quality_score: float, priority: int):
        """Add feedback to training data queue"""
        if not self.auto_training_enabled:
            return

        queue_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.feedback_db_path)
        try:
            conn.execute("""
                INSERT INTO training_data_queue (
                    queue_id, source_feedback_id, feedback_type, model_type,
                    input_data, expected_output, quality_score, priority, created_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                queue_id, source_id, feedback_type.value, model_type.value,
                input_data, expected_output, quality_score, priority,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

            logger.info(f"Added to training queue: {queue_id} (quality: {quality_score:.2f}, priority: {priority})")

        finally:
            conn.close()

    async def _update_performance_metrics(self, model_type: AIModelType, model_version: str,
                                        metric_type: str, is_positive: bool = None):
        """Update daily performance metrics"""
        today = datetime.now(timezone.utc).date()

        conn = sqlite3.connect(self.feedback_db_path)
        try:
            # Insert or update performance record
            conn.execute("""
                INSERT INTO model_performance (
                    performance_id, model_type, model_version, date, total_uses,
                    positive_feedback, negative_feedback, false_positive_count,
                    false_negative_count, attorney_verifications, attorney_approvals
                ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_type, model_version, date) DO UPDATE SET
                    total_uses = total_uses + 1,
                    positive_feedback = positive_feedback + ?,
                    negative_feedback = negative_feedback + ?,
                    false_positive_count = false_positive_count + ?,
                    false_negative_count = false_negative_count + ?,
                    attorney_verifications = attorney_verifications + ?,
                    attorney_approvals = attorney_approvals + ?
            """, (
                str(uuid.uuid4()), model_type.value, model_version, today.isoformat(),
                1 if is_positive else 0,
                1 if is_positive is False else 0,
                1 if metric_type == "false_positive" else 0,
                1 if metric_type == "false_negative" else 0,
                1 if metric_type == "verification" else 0,
                1 if metric_type == "verification" and is_positive else 0,
                1 if is_positive else 0,
                1 if is_positive is False else 0,
                1 if metric_type == "false_positive" else 0,
                1 if metric_type == "false_negative" else 0,
                1 if metric_type == "verification" else 0,
                1 if metric_type == "verification" and is_positive else 0
            ))
            conn.commit()

        finally:
            conn.close()

    async def get_feedback_analytics(self, model_type: AIModelType = None,
                                   model_version: str = None,
                                   days: int = 30) -> FeedbackAnalytics:
        """Generate comprehensive feedback analytics"""
        cache_key = f"{model_type}_{model_version}_{days}"
        if cache_key in self._analytics_cache:
            cached_data, timestamp = self._analytics_cache[cache_key]
            if datetime.now(timezone.utc) - timestamp < self._cache_duration:
                return cached_data

        period_start = datetime.now(timezone.utc) - timedelta(days=days)
        period_end = datetime.now(timezone.utc)

        conn = sqlite3.connect(self.feedback_db_path)
        try:
            # Get feedback counts
            where_clause = "WHERE timestamp >= ?"
            params = [period_start.isoformat()]

            if model_type:
                where_clause += " AND model_type = ?"
                params.append(model_type.value)

            if model_version:
                where_clause += " AND model_version = ?"
                params.append(model_version)

            # User corrections
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM user_corrections {where_clause}
            """, params)
            correction_count = cursor.fetchone()[0]

            # Attorney verifications
            cursor = conn.execute(f"""
                SELECT COUNT(*),
                       AVG(overall_quality),
                       SUM(CASE WHEN verification_status = 'approved' THEN 1 ELSE 0 END)
                FROM attorney_verifications {where_clause}
            """, params)
            verification_data = cursor.fetchone()
            verification_count = verification_data[0]
            avg_quality = verification_data[1] or 0.0
            approved_count = verification_data[2]

            # Accuracy ratings
            cursor = conn.execute(f"""
                SELECT COUNT(*), AVG(overall_satisfaction), AVG(accuracy_score)
                FROM accuracy_ratings {where_clause}
            """, params)
            rating_data = cursor.fetchone()
            rating_count = rating_data[0]
            avg_satisfaction = rating_data[1] or 0.0
            avg_accuracy = rating_data[2] or 0.0

            # False positives/negatives
            cursor = conn.execute(f"""
                SELECT
                    SUM(CASE WHEN fp_fn_type = 'false_positive' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN fp_fn_type = 'false_negative' THEN 1 ELSE 0 END)
                FROM false_positive_negative {where_clause}
            """, params)
            fp_fn_data = cursor.fetchone()
            false_positives = fp_fn_data[0] or 0
            false_negatives = fp_fn_data[1] or 0

            total_feedback = correction_count + verification_count + rating_count + false_positives + false_negatives

            # Calculate rates
            false_positive_rate = false_positives / total_feedback if total_feedback > 0 else 0.0
            false_negative_rate = false_negatives / total_feedback if total_feedback > 0 else 0.0
            attorney_approval_rate = approved_count / verification_count if verification_count > 0 else 0.0

            # Get common issues
            cursor = conn.execute(f"""
                SELECT description, COUNT(*) as count
                FROM false_positive_negative {where_clause}
                GROUP BY description
                ORDER BY count DESC
                LIMIT 10
            """, params)
            common_issues = [{"description": row[0], "count": row[1]} for row in cursor.fetchall()]

            # Create analytics object
            analytics = FeedbackAnalytics(
                period_start=period_start,
                period_end=period_end,
                model_type=model_type or AIModelType.DOCUMENT_ANALYZER,
                model_version=model_version or "all",
                total_feedback_count=total_feedback,
                correction_count=correction_count,
                verification_count=verification_count,
                average_accuracy=avg_accuracy,
                false_positive_rate=false_positive_rate,
                false_negative_rate=false_negative_rate,
                attorney_approval_rate=attorney_approval_rate,
                user_satisfaction=avg_satisfaction,
                common_issues=common_issues,
                performance_metrics={
                    "overall_quality": avg_quality,
                    "total_interactions": total_feedback,
                    "improvement_needed": false_positive_rate + false_negative_rate > 0.1
                }
            )

            # Cache the results
            self._analytics_cache[cache_key] = (analytics, datetime.now(timezone.utc))

            return analytics

        finally:
            conn.close()

    async def get_training_data(self, processed: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        """Get training data from queue"""
        conn = sqlite3.connect(self.feedback_db_path)
        try:
            cursor = conn.execute("""
                SELECT * FROM training_data_queue
                WHERE processed = ?
                ORDER BY priority DESC, created_timestamp ASC
                LIMIT ?
            """, (processed, limit))

            columns = ['queue_id', 'source_feedback_id', 'feedback_type', 'model_type',
                      'input_data', 'expected_output', 'quality_score', 'priority',
                      'created_timestamp', 'processed', 'processing_timestamp', 'batch_id']

            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        finally:
            conn.close()

    async def mark_training_data_processed(self, queue_ids: List[str], batch_id: str):
        """Mark training data as processed"""
        conn = sqlite3.connect(self.feedback_db_path)
        try:
            placeholders = ','.join(['?' for _ in queue_ids])
            conn.execute(f"""
                UPDATE training_data_queue
                SET processed = TRUE, processing_timestamp = ?, batch_id = ?
                WHERE queue_id IN ({placeholders})
            """, [datetime.now(timezone.utc).isoformat(), batch_id] + queue_ids)

            conn.commit()
            logger.info(f"Marked {len(queue_ids)} training data items as processed for batch {batch_id}")

        finally:
            conn.close()

    async def get_improvement_suggestions(self, model_type: AIModelType,
                                        model_version: str = None) -> List[str]:
        """Get AI improvement suggestions based on feedback"""
        suggestions = []

        analytics = await self.get_feedback_analytics(model_type, model_version)

        if analytics.false_positive_rate > 0.1:
            suggestions.append(f"High false positive rate ({analytics.false_positive_rate:.1%}) - review detection thresholds")

        if analytics.false_negative_rate > 0.1:
            suggestions.append(f"High false negative rate ({analytics.false_negative_rate:.1%}) - improve detection sensitivity")

        if analytics.attorney_approval_rate < 0.8:
            suggestions.append(f"Low attorney approval rate ({analytics.attorney_approval_rate:.1%}) - review output quality")

        if analytics.user_satisfaction < 0.7:
            suggestions.append(f"Low user satisfaction ({analytics.user_satisfaction:.1%}) - improve user experience")

        # Add specific suggestions based on common issues
        for issue in analytics.common_issues[:3]:
            suggestions.append(f"Address common issue: {issue['description']} ({issue['count']} reports)")

        return suggestions

    async def export_feedback_data(self, format: str = "json", **filters) -> str:
        """Export feedback data for analysis"""
        conn = sqlite3.connect(self.feedback_db_path)
        try:
            # Build queries based on filters
            tables = {
                'corrections': 'user_corrections',
                'verifications': 'attorney_verifications',
                'outcomes': 'outcome_tracking',
                'ratings': 'accuracy_ratings',
                'fp_fn': 'false_positive_negative'
            }

            export_data = {}

            for table_name, table in tables.items():
                cursor = conn.execute(f"SELECT * FROM {table}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                export_data[table_name] = [dict(zip(columns, row)) for row in rows]

            if format.lower() == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif format.lower() == "csv":
                # For CSV, export each table separately
                csv_data = {}
                for table_name, data in export_data.items():
                    if data:
                        df = pd.DataFrame(data)
                        csv_data[table_name] = df.to_csv(index=False)
                return json.dumps(csv_data)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        finally:
            conn.close()


# Configuration for feedback system
FEEDBACK_CONFIG = {
    "feedback_db_path": "data/ai_feedback.db",
    "min_quality_threshold": 0.7,
    "auto_training_enabled": True,
    "analytics_cache_duration_minutes": 15,
    "notification_settings": {
        "critical_feedback_alerts": True,
        "daily_analytics_reports": True,
        "weekly_improvement_reports": True
    },
    "training_integration": {
        "batch_size": 100,
        "quality_threshold": 0.8,
        "priority_weights": {
            "false_positive": 0.9,
            "false_negative": 0.9,
            "attorney_verified": 0.8,
            "user_correction": 0.7
        }
    }
}


# Export main classes
__all__ = [
    'FeedbackCollector',
    'UserCorrection',
    'AttorneyVerification',
    'OutcomeTracking',
    'AccuracyRating',
    'FalsePositiveNegative',
    'FeedbackAnalytics',
    'FeedbackType',
    'FeedbackSeverity',
    'AIModelType',
    'CaseOutcome'
]