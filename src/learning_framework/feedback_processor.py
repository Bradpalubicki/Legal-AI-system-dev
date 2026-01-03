"""
Feedback Processor Module

Advanced feedback processing system for capturing, analyzing, and integrating
user feedback to improve AI model performance and accuracy.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import asyncio
import json
import hashlib
from textblob import TextBlob
import re

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    ACCURACY_RATING = "accuracy_rating"
    RELEVANCE_RATING = "relevance_rating"
    COMPLETENESS_RATING = "completeness_rating"
    QUALITY_RATING = "quality_rating"
    USEFULNESS_RATING = "usefulness_rating"
    CORRECTNESS_FLAG = "correctness_flag"
    SUGGESTION_TEXT = "suggestion_text"
    ERROR_REPORT = "error_report"
    IMPROVEMENT_REQUEST = "improvement_request"
    PREFERENCE_UPDATE = "preference_update"
    ANNOTATION_CORRECTION = "annotation_correction"
    CLASSIFICATION_CORRECTION = "classification_correction"
    OUTCOME_VERIFICATION = "outcome_verification"
    USAGE_PATTERN = "usage_pattern"
    PERFORMANCE_ISSUE = "performance_issue"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"

class FeedbackSource(Enum):
    USER_EXPLICIT = "user_explicit"
    USER_IMPLICIT = "user_implicit"
    SYSTEM_MONITORING = "system_monitoring"
    OUTCOME_VERIFICATION = "outcome_verification"
    PEER_REVIEW = "peer_review"
    EXPERT_VALIDATION = "expert_validation"
    AUTOMATED_CHECK = "automated_check"

@dataclass
class QualityScore:
    overall_score: float = 0.0  # 0-1 scale
    accuracy_score: float = 0.0
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    usefulness_score: float = 0.0
    confidence_score: float = 0.0
    consistency_score: float = 0.0
    timeliness_score: float = 0.0
    explanation_quality: float = 0.0
    user_satisfaction: float = 0.0
    weighted_scores: Dict[str, float] = field(default_factory=dict)
    score_breakdown: Dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class FeedbackEntry:
    id: Optional[int] = None
    feedback_type: FeedbackType = FeedbackType.QUALITY_RATING
    source: FeedbackSource = FeedbackSource.USER_EXPLICIT
    user_id: Optional[int] = None
    case_id: Optional[int] = None
    model_id: Optional[str] = None
    prediction_id: Optional[str] = None
    task_type: Optional[str] = None
    feedback_value: Any = None  # Could be rating, text, boolean, etc.
    feedback_text: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    original_input: Optional[str] = None
    original_output: Optional[str] = None
    expected_output: Optional[str] = None
    corrected_output: Optional[str] = None
    confidence: float = 1.0
    priority: int = 1  # 1-5 scale
    severity: Optional[str] = None  # low, medium, high, critical
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    applied_to_training: bool = False
    validation_status: Optional[str] = None
    quality_score: Optional[QualityScore] = None
    sentiment_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class FeedbackProcessor:
    def __init__(self):
        self.feedback_buffer: List[FeedbackEntry] = []
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.quality_metrics: Dict[str, QualityScore] = {}
        self.feedback_patterns: Dict[str, Any] = {}
        self.user_preferences: Dict[int, Dict[str, Any]] = {}
        self.validation_rules = {
            'min_text_length': 5,
            'max_text_length': 5000,
            'rating_range': (1, 5),
            'confidence_threshold': 0.3,
            'spam_detection_enabled': True,
            'profanity_filter_enabled': True,
            'duplicate_detection_window_hours': 24
        }

    async def submit_feedback(
        self,
        feedback_type: FeedbackType,
        feedback_value: Any,
        user_id: Optional[int] = None,
        case_id: Optional[int] = None,
        model_id: Optional[str] = None,
        prediction_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        feedback_text: Optional[str] = None,
        source: FeedbackSource = FeedbackSource.USER_EXPLICIT,
        db: Optional[AsyncSession] = None
    ) -> Optional[FeedbackEntry]:
        """Submit feedback for processing."""
        try:
            # Create feedback entry
            feedback_entry = FeedbackEntry(
                feedback_type=feedback_type,
                source=source,
                user_id=user_id,
                case_id=case_id,
                model_id=model_id,
                prediction_id=prediction_id,
                feedback_value=feedback_value,
                feedback_text=feedback_text,
                context_data=context_data or {}
            )
            
            # Validate feedback
            validation_result = await self._validate_feedback(feedback_entry)
            if not validation_result['valid']:
                logger.warning(f"Invalid feedback rejected: {validation_result['reason']}")
                return None
            
            # Check for duplicates
            if await self._is_duplicate_feedback(feedback_entry):
                logger.info("Duplicate feedback detected, skipping")
                return None
            
            # Enrich feedback with additional data
            await self._enrich_feedback(feedback_entry, db)
            
            # Calculate quality scores
            feedback_entry.quality_score = await self._calculate_quality_scores(feedback_entry)
            
            # Analyze sentiment if text feedback
            if feedback_text:
                feedback_entry.sentiment_score = await self._analyze_sentiment(feedback_text)
            
            # Add to buffer and queue for processing
            self.feedback_buffer.append(feedback_entry)
            await self.processing_queue.put(feedback_entry)
            
            # Persist to database
            if db:
                await self._persist_feedback(feedback_entry, db)
            
            logger.info(f"Feedback submitted: {feedback_type.value} from user {user_id}")
            return feedback_entry
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return None

    async def process_feedback_batch(
        self,
        batch_size: int = 100,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Process a batch of feedback entries."""
        try:
            processed_count = 0
            processing_results = {
                'processed': [],
                'failed': [],
                'patterns_detected': [],
                'quality_updates': [],
                'training_data_created': []
            }
            
            # Process feedback entries from queue
            while processed_count < batch_size and not self.processing_queue.empty():
                try:
                    feedback_entry = await asyncio.wait_for(
                        self.processing_queue.get(), timeout=1.0
                    )
                    
                    # Process individual feedback
                    result = await self._process_single_feedback(feedback_entry, db)
                    
                    if result['success']:
                        processing_results['processed'].append(feedback_entry.id)
                        feedback_entry.processed = True
                        
                        # Extract insights
                        if result.get('patterns'):
                            processing_results['patterns_detected'].extend(result['patterns'])
                        
                        if result.get('quality_updates'):
                            processing_results['quality_updates'].extend(result['quality_updates'])
                        
                        if result.get('training_data'):
                            processing_results['training_data_created'].append(result['training_data'])
                    else:
                        processing_results['failed'].append({
                            'feedback_id': feedback_entry.id,
                            'error': result.get('error')
                        })
                    
                    processed_count += 1
                    
                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    logger.error(f"Error processing feedback entry: {e}")
                    processing_results['failed'].append({'error': str(e)})
            
            # Update feedback patterns
            if processing_results['patterns_detected']:
                await self._update_feedback_patterns(processing_results['patterns_detected'])
            
            # Update quality metrics
            if processing_results['quality_updates']:
                await self._update_quality_metrics(processing_results['quality_updates'])
            
            logger.info(f"Processed {processed_count} feedback entries")
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing feedback batch: {e}")
            return {'processed': [], 'failed': [], 'error': str(e)}

    async def analyze_feedback_trends(
        self,
        time_period_days: int = 30,
        group_by: Optional[str] = None,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze feedback trends and patterns."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_period_days)
            
            # Filter feedback entries
            relevant_feedback = []
            for feedback in self.feedback_buffer:
                if feedback.created_at >= start_date:
                    if not filter_criteria or self._matches_filter(feedback, filter_criteria):
                        relevant_feedback.append(feedback)
            
            if not relevant_feedback:
                return {'message': 'No feedback data available for analysis'}
            
            # Basic statistics
            total_feedback = len(relevant_feedback)
            feedback_by_type = Counter([f.feedback_type.value for f in relevant_feedback])
            feedback_by_source = Counter([f.source.value for f in relevant_feedback])
            
            # Quality trends
            quality_scores = [f.quality_score.overall_score for f in relevant_feedback if f.quality_score]
            avg_quality = np.mean(quality_scores) if quality_scores else 0
            
            # Sentiment trends (for text feedback)
            sentiment_scores = [f.sentiment_score for f in relevant_feedback if f.sentiment_score is not None]
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
            
            # Time-based analysis
            feedback_by_date = defaultdict(int)
            for feedback in relevant_feedback:
                date_key = feedback.created_at.date().isoformat()
                feedback_by_date[date_key] += 1
            
            # User engagement analysis
            active_users = len(set(f.user_id for f in relevant_feedback if f.user_id))
            feedback_per_user = total_feedback / active_users if active_users > 0 else 0
            
            # Model performance insights
            model_feedback = defaultdict(list)
            for feedback in relevant_feedback:
                if feedback.model_id:
                    model_feedback[feedback.model_id].append(feedback)
            
            model_quality_scores = {}
            for model_id, feedbacks in model_feedback.items():
                scores = [f.quality_score.overall_score for f in feedbacks if f.quality_score]
                if scores:
                    model_quality_scores[model_id] = {
                        'avg_quality': np.mean(scores),
                        'feedback_count': len(feedbacks),
                        'improvement_rate': self._calculate_improvement_rate(feedbacks)
                    }
            
            # Common issues and suggestions
            error_reports = [f for f in relevant_feedback if f.feedback_type == FeedbackType.ERROR_REPORT]
            improvement_requests = [f for f in relevant_feedback if f.feedback_type == FeedbackType.IMPROVEMENT_REQUEST]
            
            common_issues = await self._extract_common_themes(
                [f.feedback_text for f in error_reports if f.feedback_text]
            )
            
            common_requests = await self._extract_common_themes(
                [f.feedback_text for f in improvement_requests if f.feedback_text]
            )
            
            analysis_result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': time_period_days
                },
                'summary': {
                    'total_feedback': total_feedback,
                    'active_users': active_users,
                    'feedback_per_user': round(feedback_per_user, 2),
                    'avg_quality_score': round(avg_quality, 3),
                    'avg_sentiment_score': round(avg_sentiment, 3)
                },
                'distribution': {
                    'by_type': dict(feedback_by_type),
                    'by_source': dict(feedback_by_source),
                    'by_date': dict(feedback_by_date)
                },
                'model_performance': model_quality_scores,
                'insights': {
                    'common_issues': common_issues,
                    'improvement_requests': common_requests,
                    'quality_trend': self._calculate_quality_trend(relevant_feedback),
                    'engagement_trend': self._calculate_engagement_trend(relevant_feedback)
                },
                'recommendations': await self._generate_feedback_recommendations(relevant_feedback)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing feedback trends: {e}")
            return {'error': str(e)}

    async def get_user_feedback_profile(
        self,
        user_id: int,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """Get detailed feedback profile for a specific user."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)
            
            # Get user's feedback
            user_feedback = [
                f for f in self.feedback_buffer
                if f.user_id == user_id and f.created_at >= start_date
            ]
            
            if not user_feedback:
                return {'message': 'No feedback found for user'}
            
            # Calculate user statistics
            total_feedback = len(user_feedback)
            feedback_types = Counter([f.feedback_type.value for f in user_feedback])
            avg_quality_given = np.mean([
                f.quality_score.overall_score for f in user_feedback 
                if f.quality_score
            ])
            
            # Engagement patterns
            feedback_by_day = defaultdict(int)
            for feedback in user_feedback:
                day = feedback.created_at.strftime('%A')
                feedback_by_day[day] += 1
            
            feedback_by_hour = defaultdict(int)
            for feedback in user_feedback:
                hour = feedback.created_at.hour
                feedback_by_hour[hour] += 1
            
            # Sentiment analysis
            text_feedback = [f for f in user_feedback if f.feedback_text]
            sentiment_scores = [f.sentiment_score for f in text_feedback if f.sentiment_score is not None]
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
            
            # User preferences (inferred from feedback patterns)
            preferences = await self._infer_user_preferences(user_feedback)
            
            # Feedback quality assessment
            quality_assessment = await self._assess_feedback_quality(user_feedback)
            
            profile = {
                'user_id': user_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': lookback_days
                },
                'activity': {
                    'total_feedback': total_feedback,
                    'feedback_types': dict(feedback_types),
                    'avg_quality_score': round(avg_quality_given, 3),
                    'avg_sentiment': round(avg_sentiment, 3)
                },
                'patterns': {
                    'by_day_of_week': dict(feedback_by_day),
                    'by_hour_of_day': dict(feedback_by_hour),
                    'most_active_day': max(feedback_by_day.items(), key=lambda x: x[1])[0] if feedback_by_day else None,
                    'most_active_hour': max(feedback_by_hour.items(), key=lambda x: x[1])[0] if feedback_by_hour else None
                },
                'preferences': preferences,
                'quality_assessment': quality_assessment,
                'recommendations': await self._generate_user_recommendations(user_feedback)
            }
            
            # Cache user preferences
            self.user_preferences[user_id] = preferences
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user feedback profile: {e}")
            return {'error': str(e)}

    async def generate_training_data(
        self,
        feedback_types: Optional[List[FeedbackType]] = None,
        min_quality_threshold: float = 0.7,
        max_training_samples: int = 1000,
        balance_classes: bool = True
    ) -> List[Dict[str, Any]]:
        """Generate training data from processed feedback."""
        try:
            if not feedback_types:
                feedback_types = [
                    FeedbackType.CORRECTNESS_FLAG,
                    FeedbackType.CLASSIFICATION_CORRECTION,
                    FeedbackType.ANNOTATION_CORRECTION,
                    FeedbackType.OUTCOME_VERIFICATION
                ]
            
            training_samples = []
            
            # Filter relevant feedback
            relevant_feedback = [
                f for f in self.feedback_buffer
                if (f.feedback_type in feedback_types and
                    f.processed and
                    f.quality_score and
                    f.quality_score.overall_score >= min_quality_threshold)
            ]
            
            for feedback in relevant_feedback:
                # Create training sample based on feedback type
                training_sample = None
                
                if feedback.feedback_type == FeedbackType.CORRECTNESS_FLAG:
                    training_sample = {
                        'input': feedback.original_input,
                        'original_output': feedback.original_output,
                        'label': 'correct' if feedback.feedback_value else 'incorrect',
                        'confidence': feedback.confidence,
                        'context': feedback.context_data
                    }
                
                elif feedback.feedback_type == FeedbackType.CLASSIFICATION_CORRECTION:
                    training_sample = {
                        'input': feedback.original_input,
                        'original_prediction': feedback.original_output,
                        'corrected_label': feedback.corrected_output,
                        'confidence': feedback.confidence,
                        'context': feedback.context_data
                    }
                
                elif feedback.feedback_type == FeedbackType.ANNOTATION_CORRECTION:
                    training_sample = {
                        'input': feedback.original_input,
                        'original_annotations': feedback.original_output,
                        'corrected_annotations': feedback.corrected_output,
                        'confidence': feedback.confidence,
                        'context': feedback.context_data
                    }
                
                elif feedback.feedback_type == FeedbackType.OUTCOME_VERIFICATION:
                    training_sample = {
                        'input': feedback.original_input,
                        'predicted_outcome': feedback.original_output,
                        'actual_outcome': feedback.feedback_value,
                        'confidence': feedback.confidence,
                        'context': feedback.context_data
                    }
                
                if training_sample:
                    training_sample.update({
                        'feedback_id': feedback.id,
                        'user_id': feedback.user_id,
                        'quality_score': feedback.quality_score.overall_score,
                        'created_at': feedback.created_at.isoformat(),
                        'model_id': feedback.model_id,
                        'task_type': feedback.task_type
                    })
                    training_samples.append(training_sample)
            
            # Balance classes if requested
            if balance_classes and training_samples:
                training_samples = await self._balance_training_data(training_samples)
            
            # Limit sample size
            if len(training_samples) > max_training_samples:
                # Sort by quality score and take top samples
                training_samples.sort(key=lambda x: x['quality_score'], reverse=True)
                training_samples = training_samples[:max_training_samples]
            
            logger.info(f"Generated {len(training_samples)} training samples from feedback")
            return training_samples
            
        except Exception as e:
            logger.error(f"Error generating training data: {e}")
            return []

    async def validate_feedback_impact(
        self,
        feedback_ids: List[int],
        validation_period_days: int = 30
    ) -> Dict[str, Any]:
        """Validate the impact of applied feedback on model performance."""
        try:
            validation_results = {
                'feedback_count': len(feedback_ids),
                'validation_period_days': validation_period_days,
                'performance_changes': {},
                'quality_improvements': {},
                'user_satisfaction_changes': {},
                'overall_impact_score': 0.0
            }
            
            # Get feedback entries
            feedback_entries = [
                f for f in self.feedback_buffer
                if f.id in feedback_ids
            ]
            
            if not feedback_entries:
                return validation_results
            
            # Group by model and task type
            feedback_by_model = defaultdict(list)
            for feedback in feedback_entries:
                if feedback.model_id:
                    feedback_by_model[feedback.model_id].append(feedback)
            
            # Analyze performance changes for each model
            for model_id, feedbacks in feedback_by_model.items():
                # Get performance metrics before and after feedback application
                before_metrics = await self._get_model_performance_before_feedback(
                    model_id, feedbacks, validation_period_days
                )
                after_metrics = await self._get_model_performance_after_feedback(
                    model_id, feedbacks, validation_period_days
                )
                
                if before_metrics and after_metrics:
                    performance_change = {
                        'accuracy_change': after_metrics.get('accuracy', 0) - before_metrics.get('accuracy', 0),
                        'precision_change': after_metrics.get('precision', 0) - before_metrics.get('precision', 0),
                        'recall_change': after_metrics.get('recall', 0) - before_metrics.get('recall', 0),
                        'f1_change': after_metrics.get('f1', 0) - before_metrics.get('f1', 0),
                        'user_satisfaction_change': after_metrics.get('user_satisfaction', 0) - before_metrics.get('user_satisfaction', 0)
                    }
                    validation_results['performance_changes'][model_id] = performance_change
            
            # Calculate overall impact score
            all_changes = []
            for model_changes in validation_results['performance_changes'].values():
                all_changes.extend(model_changes.values())
            
            if all_changes:
                validation_results['overall_impact_score'] = np.mean(all_changes)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating feedback impact: {e}")
            return {'error': str(e)}

    # Private helper methods
    
    async def _validate_feedback(self, feedback: FeedbackEntry) -> Dict[str, Any]:
        """Validate feedback entry."""
        try:
            # Check required fields
            if not feedback.feedback_type or feedback.feedback_value is None:
                return {'valid': False, 'reason': 'Missing required fields'}
            
            # Validate rating values
            if feedback.feedback_type.value.endswith('_rating'):
                if not isinstance(feedback.feedback_value, (int, float)):
                    return {'valid': False, 'reason': 'Rating must be numeric'}
                
                min_rating, max_rating = self.validation_rules['rating_range']
                if not (min_rating <= feedback.feedback_value <= max_rating):
                    return {'valid': False, 'reason': f'Rating must be between {min_rating} and {max_rating}'}
            
            # Validate text length
            if feedback.feedback_text:
                text_length = len(feedback.feedback_text)
                if text_length < self.validation_rules['min_text_length']:
                    return {'valid': False, 'reason': 'Text too short'}
                if text_length > self.validation_rules['max_text_length']:
                    return {'valid': False, 'reason': 'Text too long'}
                
                # Check for spam/profanity if enabled
                if self.validation_rules['spam_detection_enabled']:
                    if await self._is_spam(feedback.feedback_text):
                        return {'valid': False, 'reason': 'Spam detected'}
                
                if self.validation_rules['profanity_filter_enabled']:
                    if await self._contains_profanity(feedback.feedback_text):
                        return {'valid': False, 'reason': 'Inappropriate content'}
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating feedback: {e}")
            return {'valid': False, 'reason': str(e)}

    async def _is_duplicate_feedback(self, feedback: FeedbackEntry) -> bool:
        """Check if feedback is a duplicate."""
        try:
            if not self.validation_rules.get('duplicate_detection_window_hours'):
                return False
            
            cutoff_time = datetime.utcnow() - timedelta(
                hours=self.validation_rules['duplicate_detection_window_hours']
            )
            
            # Create feedback signature for comparison
            signature = hashlib.md5(
                f"{feedback.user_id}_{feedback.feedback_type.value}_{feedback.model_id}_{feedback.prediction_id}_{feedback.feedback_value}".encode()
            ).hexdigest()
            
            # Check recent feedback for duplicates
            for existing_feedback in self.feedback_buffer:
                if existing_feedback.created_at >= cutoff_time:
                    existing_signature = hashlib.md5(
                        f"{existing_feedback.user_id}_{existing_feedback.feedback_type.value}_{existing_feedback.model_id}_{existing_feedback.prediction_id}_{existing_feedback.feedback_value}".encode()
                    ).hexdigest()
                    
                    if signature == existing_signature:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicate feedback: {e}")
            return False

    async def _enrich_feedback(self, feedback: FeedbackEntry, db: Optional[AsyncSession]) -> None:
        """Enrich feedback with additional context data."""
        try:
            # Add timestamp-based metadata
            feedback.metadata['submission_hour'] = feedback.created_at.hour
            feedback.metadata['submission_day'] = feedback.created_at.strftime('%A')
            
            # Add user context if available
            if feedback.user_id and feedback.user_id in self.user_preferences:
                feedback.metadata['user_preferences'] = self.user_preferences[feedback.user_id]
            
            # Add model context
            if feedback.model_id:
                feedback.metadata['model_version'] = feedback.model_id
            
            # Set expiration if not set
            if not feedback.expires_at:
                # Default expiration: 1 year for valuable feedback, 30 days for others
                if feedback.feedback_type in [FeedbackType.CORRECTNESS_FLAG, FeedbackType.CLASSIFICATION_CORRECTION]:
                    feedback.expires_at = feedback.created_at + timedelta(days=365)
                else:
                    feedback.expires_at = feedback.created_at + timedelta(days=30)
            
        except Exception as e:
            logger.error(f"Error enriching feedback: {e}")

    async def _calculate_quality_scores(self, feedback: FeedbackEntry) -> QualityScore:
        """Calculate quality scores for feedback."""
        try:
            quality_score = QualityScore()
            
            # Base quality on feedback type and completeness
            if feedback.feedback_type in [FeedbackType.CORRECTNESS_FLAG, FeedbackType.CLASSIFICATION_CORRECTION]:
                quality_score.accuracy_score = 0.9  # High accuracy for structured feedback
            else:
                quality_score.accuracy_score = 0.7
            
            # Text quality assessment
            if feedback.feedback_text:
                text_length = len(feedback.feedback_text)
                if text_length >= 50:  # Detailed feedback
                    quality_score.completeness_score = 0.9
                elif text_length >= 20:
                    quality_score.completeness_score = 0.7
                else:
                    quality_score.completeness_score = 0.5
                
                # Simple language quality check
                blob = TextBlob(feedback.feedback_text)
                if len(blob.sentences) > 0:
                    quality_score.explanation_quality = min(0.9, len(blob.sentences) * 0.2)
            else:
                quality_score.completeness_score = 0.6  # Still valuable without text
            
            # Relevance based on context
            if feedback.context_data:
                quality_score.relevance_score = 0.8
            else:
                quality_score.relevance_score = 0.6
            
            # Usefulness based on feedback type
            if feedback.feedback_type in [FeedbackType.ERROR_REPORT, FeedbackType.IMPROVEMENT_REQUEST]:
                quality_score.usefulness_score = 0.9
            else:
                quality_score.usefulness_score = 0.7
            
            # Confidence based on user history and feedback type
            base_confidence = feedback.confidence
            if feedback.source == FeedbackSource.EXPERT_VALIDATION:
                quality_score.confidence_score = min(1.0, base_confidence * 1.2)
            else:
                quality_score.confidence_score = base_confidence
            
            # Timeliness (fresher feedback is more valuable)
            hours_since_creation = (datetime.utcnow() - feedback.created_at).total_seconds() / 3600
            quality_score.timeliness_score = max(0.1, 1.0 - (hours_since_creation / 168))  # Decays over 1 week
            
            # Calculate overall score (weighted average)
            weights = {
                'accuracy': 0.25,
                'relevance': 0.20,
                'completeness': 0.15,
                'usefulness': 0.15,
                'confidence': 0.15,
                'timeliness': 0.10
            }
            
            quality_score.overall_score = (
                quality_score.accuracy_score * weights['accuracy'] +
                quality_score.relevance_score * weights['relevance'] +
                quality_score.completeness_score * weights['completeness'] +
                quality_score.usefulness_score * weights['usefulness'] +
                quality_score.confidence_score * weights['confidence'] +
                quality_score.timeliness_score * weights['timeliness']
            )
            
            quality_score.weighted_scores = weights
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating quality scores: {e}")
            return QualityScore()

    async def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of feedback text."""
        try:
            blob = TextBlob(text)
            # TextBlob returns polarity between -1 (negative) and 1 (positive)
            # We'll normalize to 0-1 scale where 0.5 is neutral
            sentiment = (blob.sentiment.polarity + 1) / 2
            return sentiment
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.5  # Neutral sentiment as default

    async def _process_single_feedback(
        self, 
        feedback: FeedbackEntry, 
        db: Optional[AsyncSession]
    ) -> Dict[str, Any]:
        """Process a single feedback entry."""
        try:
            result = {
                'success': True,
                'patterns': [],
                'quality_updates': [],
                'training_data': None
            }
            
            # Update feedback status
            feedback.processed = True
            feedback.updated_at = datetime.utcnow()
            
            # Extract patterns
            patterns = await self._extract_feedback_patterns(feedback)
            result['patterns'] = patterns
            
            # Update quality metrics
            if feedback.model_id:
                quality_update = {
                    'model_id': feedback.model_id,
                    'quality_score': feedback.quality_score.overall_score,
                    'feedback_type': feedback.feedback_type.value,
                    'timestamp': feedback.created_at
                }
                result['quality_updates'].append(quality_update)
            
            # Create training data if applicable
            if feedback.feedback_type in [FeedbackType.CORRECTNESS_FLAG, FeedbackType.CLASSIFICATION_CORRECTION]:
                training_data = {
                    'input': feedback.original_input,
                    'output': feedback.original_output,
                    'corrected_output': feedback.corrected_output,
                    'label': feedback.feedback_value,
                    'confidence': feedback.confidence
                }
                result['training_data'] = training_data
                feedback.applied_to_training = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing single feedback: {e}")
            return {'success': False, 'error': str(e)}

    async def _persist_feedback(self, feedback: FeedbackEntry, db: AsyncSession) -> None:
        """Persist feedback to database."""
        try:
            # This would typically involve database operations
            # For now, just log the persistence
            logger.info(f"Persisting feedback {feedback.id} to database")
        except Exception as e:
            logger.error(f"Error persisting feedback: {e}")

    # Additional helper methods would be implemented here...
    
    async def _extract_common_themes(self, texts: List[str]) -> List[str]:
        """Extract common themes from feedback texts."""
        if not texts:
            return []
        
        # Simple keyword extraction
        word_freq = Counter()
        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            word_freq.update(words)
        
        # Return most common meaningful words (excluding stop words)
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'cannot', 'this', 'that', 'these', 'those'}
        
        common_themes = []
        for word, freq in word_freq.most_common(10):
            if word not in stop_words and len(word) > 3 and freq > 1:
                common_themes.append(f"{word} ({freq} mentions)")
        
        return common_themes

    async def _is_spam(self, text: str) -> bool:
        """Simple spam detection."""
        spam_indicators = ['click here', 'free money', 'act now', 'limited time', 'urgent']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in spam_indicators)

    async def _contains_profanity(self, text: str) -> bool:
        """Simple profanity filter."""
        # This would typically use a more sophisticated profanity filter
        profanity_words = ['spam', 'scam']  # Simplified list
        text_lower = text.lower()
        return any(word in text_lower for word in profanity_words)

    def _matches_filter(self, feedback: FeedbackEntry, filter_criteria: Dict[str, Any]) -> bool:
        """Check if feedback matches filter criteria."""
        for key, value in filter_criteria.items():
            if hasattr(feedback, key):
                if getattr(feedback, key) != value:
                    return False
        return True

    def _calculate_improvement_rate(self, feedbacks: List[FeedbackEntry]) -> float:
        """Calculate improvement rate from feedback sequence."""
        if len(feedbacks) < 2:
            return 0.0
        
        # Sort by creation time
        sorted_feedbacks = sorted(feedbacks, key=lambda x: x.created_at)
        
        # Compare first half to second half
        mid_point = len(sorted_feedbacks) // 2
        first_half_scores = [f.quality_score.overall_score for f in sorted_feedbacks[:mid_point] if f.quality_score]
        second_half_scores = [f.quality_score.overall_score for f in sorted_feedbacks[mid_point:] if f.quality_score]
        
        if first_half_scores and second_half_scores:
            first_avg = np.mean(first_half_scores)
            second_avg = np.mean(second_half_scores)
            return second_avg - first_avg
        
        return 0.0