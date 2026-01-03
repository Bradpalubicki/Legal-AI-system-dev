"""
Customer Success Feedback Loops Module

Handles comprehensive feedback collection and analysis:
- In-app surveys and feedback forms
- Feature requests tracking and prioritization
- Bug reports management
- Testimonials and case studies collection
- Reference program management
- Feedback-driven product improvement cycles
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..core.database import get_db
from .metrics import SuccessMetricsCalculator, User, Client, UserActivity, FeatureUsage
from ..models.success_tracking import (
    Feedback, FeatureRequest, BugReport, Testimonial,
    Survey, SurveyResponse
)
# Mock logger - replace with actual logger import
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

try:
    from ..utils.logger import logger
except ImportError:
    logger = MockLogger()

# Mock classes for missing services - these should be replaced with actual imports
class EmailService:
    async def send_email(self, to_email, subject, body, template_name, context=None):
        return {"success": True, "message": "Email sent"}

class NotificationService:
    async def create_notification(self, data):
        return {"success": True, "notification_id": "mock_id"}


class FeedbackType(Enum):
    GENERAL = "general"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    IMPROVEMENT = "improvement"
    TESTIMONIAL = "testimonial"
    COMPLAINT = "complaint"
    NPS_SURVEY = "nps_survey"
    SATISFACTION = "satisfaction"
    ONBOARDING = "onboarding"
    FEATURE_FEEDBACK = "feature_feedback"


class FeedbackPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class SurveyType(Enum):
    NPS = "nps"
    CSAT = "csat"
    CES = "ces"  # Customer Effort Score
    ONBOARDING = "onboarding"
    FEATURE_FEEDBACK = "feature_feedback"
    QUARTERLY_REVIEW = "quarterly_review"
    EXIT_INTERVIEW = "exit_interview"


@dataclass
class FeedbackSummary:
    total_feedback: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    avg_satisfaction_score: float
    sentiment_distribution: Dict[str, int]
    response_rate: float
    recent_trends: Dict[str, float]


@dataclass
class FeatureRequestAnalysis:
    request_id: str
    title: str
    description: str
    requester_count: int
    total_votes: int
    estimated_effort: Optional[str]
    business_impact: float
    technical_feasibility: float
    priority_score: float
    implementation_status: str
    related_requests: List[str]


@dataclass
class ImprovementOpportunity:
    area: str
    description: str
    impact_score: float
    effort_estimate: str
    supporting_feedback: List[str]
    affected_users: int
    recommended_action: str


class FeedbackCollector:
    """Manages feedback collection across different channels"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
        self.notification_service = NotificationService()
        self.metrics_calculator = SuccessMetricsCalculator(db)

    async def create_survey(
        self,
        survey_type: SurveyType,
        title: str,
        description: str,
        questions: List[Dict],
        target_users: Optional[List[str]] = None,
        target_segments: Optional[List[str]] = None
    ) -> str:
        """Create and deploy a new survey"""
        try:
            survey = Survey(
                type=survey_type.value,
                title=title,
                description=description,
                questions=questions,
                target_users=target_users or [],
                target_segments=target_segments or [],
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
                is_active=True
            )

            self.db.add(survey)
            self.db.commit()
            self.db.refresh(survey)

            # Send survey invitations
            await self._send_survey_invitations(survey)

            logger.info(f"Created survey: {survey.id} - {title}")
            return survey.id

        except Exception as e:
            logger.error(f"Error creating survey: {e}")
            raise

    async def _send_survey_invitations(self, survey: Survey):
        """Send survey invitations to target users"""
        try:
            # Determine target users
            if survey.target_users:
                target_users = self.db.query(User).filter(
                    User.id.in_(survey.target_users)
                ).all()
            else:
                # Default to active users
                target_users = self.db.query(User).filter(
                    and_(
                        User.status == 'active',
                        User.last_active >= datetime.utcnow() - timedelta(days=30)
                    )
                ).all()

            # Apply segment filters if specified
            if survey.target_segments:
                filtered_users = []
                for user in target_users:
                    user_segments = await self._get_user_segments(user)
                    if any(segment in survey.target_segments for segment in user_segments):
                        filtered_users.append(user)
                target_users = filtered_users

            # Send invitations
            for user in target_users:
                await self._send_survey_invitation(user, survey)

            logger.info(f"Sent {len(target_users)} survey invitations for survey {survey.id}")

        except Exception as e:
            logger.error(f"Error sending survey invitations: {e}")

    async def _get_user_segments(self, user: User) -> List[str]:
        """Get user segments for targeting"""
        segments = []

        # Basic segments
        if user.onboarding_completed:
            segments.append("onboarded")
        else:
            segments.append("not_onboarded")

        # Activity segments
        if user.last_active and user.last_active >= datetime.utcnow() - timedelta(days=7):
            segments.append("highly_active")
        elif user.last_active and user.last_active >= datetime.utcnow() - timedelta(days=30):
            segments.append("moderately_active")
        else:
            segments.append("low_activity")

        # Tenure segments
        if user.created_at:
            days_since_signup = (datetime.utcnow() - user.created_at).days
        else:
            days_since_signup = 0
        if days_since_signup <= 30:
            segments.append("new_user")
        elif days_since_signup <= 180:
            segments.append("growing_user")
        else:
            segments.append("mature_user")

        # Usage-based segments
        feature_usage_count = self.db.query(FeatureUsage).filter(
            and_(
                FeatureUsage.user_id == user.id,
                FeatureUsage.used_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).count()

        if feature_usage_count >= 50:
            segments.append("power_user")
        elif feature_usage_count >= 10:
            segments.append("regular_user")
        else:
            segments.append("light_user")

        return segments

    async def _send_survey_invitation(self, user: User, survey: Survey):
        """Send individual survey invitation"""
        try:
            # Create survey link
            survey_link = f"/surveys/{survey.id}?user={user.id}&token={self._generate_survey_token(user.id, survey.id)}"

            # Send email invitation
            await self.email_service.send_email(
                to_email=user.email,
                subject=f"Your feedback is important: {survey.title}",
                template_name="survey_invitation",
                context={
                    "user_name": user.full_name,
                    "survey_title": survey.title,
                    "survey_description": survey.description,
                    "survey_link": survey_link,
                    "estimated_time": len(survey.questions) * 30  # 30 seconds per question
                }
            )

            # Create in-app notification
            await self.notification_service.create_notification({
                "user_id": user.id,
                "type": "survey_invitation",
                "title": "New Survey Available",
                "message": f"Help us improve: {survey.title}",
                "action_url": survey_link,
                "priority": "medium"
            })

        except Exception as e:
            logger.error(f"Error sending survey invitation to {user.id}: {e}")

    def _generate_survey_token(self, user_id: str, survey_id: str) -> str:
        """Generate secure token for survey access"""
        # Simplified token generation - use proper JWT in production
        import hashlib
        token_string = f"{user_id}:{survey_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(token_string.encode()).hexdigest()[:16]

    async def submit_survey_response(
        self,
        survey_id: str,
        user_id: str,
        responses: Dict[str, Any]
    ) -> bool:
        """Submit survey response"""
        try:
            survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey or not survey.is_active:
                return False

            # Check if user already responded
            existing_response = self.db.query(SurveyResponse).filter(
                and_(
                    SurveyResponse.survey_id == survey_id,
                    SurveyResponse.user_id == user_id
                )
            ).first()

            if existing_response and not survey.allow_multiple_responses:
                return False

            # Validate responses
            if not self._validate_survey_responses(survey, responses):
                return False

            # Save response
            survey_response = SurveyResponse(
                survey_id=survey_id,
                user_id=user_id,
                responses=responses,
                submitted_at=datetime.utcnow()
            )

            self.db.add(survey_response)
            self.db.commit()

            # Process specific survey types
            await self._process_survey_response(survey, survey_response)

            logger.info(f"Survey response submitted: {survey_id} by {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error submitting survey response: {e}")
            return False

    def _validate_survey_responses(self, survey: Survey, responses: Dict[str, Any]) -> bool:
        """Validate survey responses against question requirements"""
        try:
            for question in survey.questions:
                question_id = question.get("id")
                if question.get("required", False) and question_id not in responses:
                    return False

                # Validate response type
                response_value = responses.get(question_id)
                if response_value is not None:
                    question_type = question.get("type", "text")

                    if question_type == "scale" and not isinstance(response_value, (int, float)):
                        return False
                    elif question_type == "multiple_choice" and question.get("options"):
                        if response_value not in [opt["value"] for opt in question["options"]]:
                            return False

            return True

        except Exception as e:
            logger.error(f"Error validating survey responses: {e}")
            return False

    async def _process_survey_response(self, survey: Survey, response: SurveyResponse):
        """Process survey response based on survey type"""
        try:
            if survey.type == SurveyType.NPS.value:
                await self._process_nps_response(response)
            elif survey.type == SurveyType.CSAT.value:
                await self._process_csat_response(response)
            elif survey.type == SurveyType.FEATURE_FEEDBACK.value:
                await self._process_feature_feedback_response(response)

        except Exception as e:
            logger.error(f"Error processing survey response: {e}")

    async def _process_nps_response(self, response: SurveyResponse):
        """Process NPS survey response"""
        try:
            nps_score = response.responses.get("nps_score")
            if nps_score is not None:
                # Create follow-up actions based on score
                if int(nps_score) <= 6:  # Detractor
                    await self._create_detractor_followup(response.user_id, response.responses)
                elif int(nps_score) >= 9:  # Promoter
                    await self._create_promoter_followup(response.user_id, response.responses)

        except Exception as e:
            logger.error(f"Error processing NPS response: {e}")

    async def _create_detractor_followup(self, user_id: str, responses: Dict):
        """Create follow-up actions for NPS detractors"""
        try:
            # Create high-priority feedback for review
            feedback = Feedback(
                user_id=user_id,
                type=FeedbackType.COMPLAINT.value,
                priority=FeedbackPriority.HIGH.value,
                content=responses.get("feedback_text", "NPS detractor - no specific feedback"),
                metadata={"nps_score": responses.get("nps_score"), "survey_response": True},
                created_at=datetime.utcnow(),
                status=FeedbackStatus.NEW.value
            )

            self.db.add(feedback)
            self.db.commit()

            # Schedule customer success manager outreach
            await self.notification_service.create_notification({
                "user_id": "csm_team",  # Notify CS team
                "type": "urgent_followup",
                "title": f"NPS Detractor Alert - User {user_id}",
                "message": f"User scored {responses.get('nps_score')} - immediate attention needed",
                "priority": "urgent",
                "metadata": {"user_id": user_id, "feedback_id": feedback.id}
            })

        except Exception as e:
            logger.error(f"Error creating detractor followup: {e}")

    async def _create_promoter_followup(self, user_id: str, responses: Dict):
        """Create follow-up actions for NPS promoters"""
        try:
            # Invite to reference program
            await self.notification_service.create_notification({
                "user_id": user_id,
                "type": "reference_invitation",
                "title": "Thanks for your great feedback!",
                "message": "Would you like to join our customer reference program?",
                "priority": "low",
                "action_url": "/programs/reference"
            })

            # Request testimonial
            await self._request_testimonial(user_id, responses.get("feedback_text", ""))

        except Exception as e:
            logger.error(f"Error creating promoter followup: {e}")

    async def collect_feature_request(
        self,
        user_id: str,
        title: str,
        description: str,
        use_case: str,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM
    ) -> str:
        """Collect and process feature request"""
        try:
            # Check for similar existing requests
            similar_requests = await self._find_similar_requests(title, description)

            feature_request = FeatureRequest(
                user_id=user_id,
                title=title,
                description=description,
                use_case=use_case,
                priority=priority.value,
                votes=1,  # User's initial vote
                created_at=datetime.utcnow(),
                status=FeedbackStatus.NEW.value,
                similar_requests=similar_requests
            )

            self.db.add(feature_request)
            self.db.commit()
            self.db.refresh(feature_request)

            # Notify product team
            await self.notification_service.create_notification({
                "user_id": "product_team",
                "type": "new_feature_request",
                "title": f"New Feature Request: {title}",
                "message": f"From user {user_id}",
                "metadata": {"request_id": feature_request.id}
            })

            logger.info(f"Feature request created: {feature_request.id}")
            return feature_request.id

        except Exception as e:
            logger.error(f"Error collecting feature request: {e}")
            raise

    async def _find_similar_requests(self, title: str, description: str) -> List[str]:
        """Find similar feature requests using basic text matching"""
        try:
            # Simple keyword-based similarity (enhance with ML/NLP in production)
            keywords = set(title.lower().split() + description.lower().split())
            keywords = {word for word in keywords if len(word) > 3}  # Filter short words

            if not keywords:
                return []

            existing_requests = self.db.query(FeatureRequest).filter(
                FeatureRequest.status.in_([FeedbackStatus.NEW.value, FeedbackStatus.REVIEWED.value])
            ).all()

            similar_requests = []
            for request in existing_requests:
                request_keywords = set(
                    request.title.lower().split() + request.description.lower().split()
                )
                request_keywords = {word for word in request_keywords if len(word) > 3}

                # Calculate simple similarity score
                intersection = keywords.intersection(request_keywords)
                union = keywords.union(request_keywords)
                similarity = len(intersection) / len(union) if union else 0

                if similarity > 0.3:  # 30% similarity threshold
                    similar_requests.append(request.id)

            return similar_requests

        except Exception as e:
            logger.error(f"Error finding similar requests: {e}")
            return []

    async def collect_bug_report(
        self,
        user_id: str,
        title: str,
        description: str,
        steps_to_reproduce: str,
        expected_behavior: str,
        actual_behavior: str,
        browser_info: Optional[str] = None,
        screenshots: Optional[List[str]] = None
    ) -> str:
        """Collect and process bug report"""
        try:
            bug_report = BugReport(
                user_id=user_id,
                title=title,
                description=description,
                steps_to_reproduce=steps_to_reproduce,
                expected_behavior=expected_behavior,
                actual_behavior=actual_behavior,
                browser_info=browser_info,
                screenshots=screenshots or [],
                severity=await self._determine_bug_severity(title, description),
                created_at=datetime.utcnow(),
                status=FeedbackStatus.NEW.value
            )

            self.db.add(bug_report)
            self.db.commit()
            self.db.refresh(bug_report)

            # Notify development team
            priority = "urgent" if bug_report.severity == "critical" else "high"
            await self.notification_service.create_notification({
                "user_id": "dev_team",
                "type": "new_bug_report",
                "title": f"Bug Report: {title}",
                "message": f"Severity: {bug_report.severity}",
                "priority": priority,
                "metadata": {"bug_id": bug_report.id}
            })

            logger.info(f"Bug report created: {bug_report.id}")
            return bug_report.id

        except Exception as e:
            logger.error(f"Error collecting bug report: {e}")
            raise

    async def _determine_bug_severity(self, title: str, description: str) -> str:
        """Determine bug severity based on title and description"""
        critical_keywords = ["crash", "down", "broken", "error", "failed", "not working"]
        high_keywords = ["slow", "incorrect", "missing", "problem"]

        text = (title + " " + description).lower()

        if any(keyword in text for keyword in critical_keywords):
            return "critical"
        elif any(keyword in text for keyword in high_keywords):
            return "high"
        else:
            return "medium"

    async def _request_testimonial(self, user_id: str, initial_feedback: str):
        """Request testimonial from satisfied user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return

            # Send personalized testimonial request
            await self.email_service.send_email(
                to_email=user.email,
                subject="Share your success story with Legal AI",
                template_name="testimonial_request",
                context={
                    "user_name": user.full_name,
                    "initial_feedback": initial_feedback,
                    "testimonial_link": f"/testimonials/create?user={user_id}"
                }
            )

        except Exception as e:
            logger.error(f"Error requesting testimonial: {e}")

    async def collect_testimonial(
        self,
        user_id: str,
        content: str,
        rating: int,
        use_case: str,
        results_achieved: str,
        permission_to_publish: bool = False
    ) -> str:
        """Collect user testimonial"""
        try:
            testimonial = Testimonial(
                user_id=user_id,
                content=content,
                rating=rating,
                use_case=use_case,
                results_achieved=results_achieved,
                permission_to_publish=permission_to_publish,
                created_at=datetime.utcnow(),
                status="pending_review"
            )

            self.db.add(testimonial)
            self.db.commit()
            self.db.refresh(testimonial)

            # Notify marketing team
            await self.notification_service.create_notification({
                "user_id": "marketing_team",
                "type": "new_testimonial",
                "title": f"New Testimonial from {user_id}",
                "message": f"Rating: {rating}/5 stars",
                "metadata": {"testimonial_id": testimonial.id}
            })

            logger.info(f"Testimonial collected: {testimonial.id}")
            return testimonial.id

        except Exception as e:
            logger.error(f"Error collecting testimonial: {e}")
            raise


class FeedbackAnalyzer:
    """Analyzes feedback patterns and generates insights"""

    def __init__(self, db: Session):
        self.db = db

    async def generate_feedback_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> FeedbackSummary:
        """Generate comprehensive feedback summary"""
        try:
            # Get all feedback in period
            feedback_query = self.db.query(Feedback).filter(
                Feedback.created_at.between(start_date, end_date)
            )

            total_feedback = feedback_query.count()
            feedback_items = feedback_query.all()

            # Analyze by type
            by_type = {}
            for feedback_type in FeedbackType:
                count = sum(1 for f in feedback_items if f.type == feedback_type.value)
                by_type[feedback_type.value] = count

            # Analyze by priority
            by_priority = {}
            for priority in FeedbackPriority:
                count = sum(1 for f in feedback_items if f.priority == priority.value)
                by_priority[priority.value] = count

            # Calculate average satisfaction
            satisfaction_scores = []
            for feedback in feedback_items:
                if feedback.metadata and "satisfaction_score" in feedback.metadata:
                    satisfaction_scores.append(feedback.metadata["satisfaction_score"])

            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

            # Sentiment analysis (simplified)
            sentiment_distribution = await self._analyze_sentiment_distribution(feedback_items)

            # Calculate response rate
            survey_invitations = self.db.query(UserActivity).filter(
                and_(
                    UserActivity.activity_type == "survey_invitation_sent",
                    UserActivity.created_at.between(start_date, end_date)
                )
            ).count()

            survey_responses = self.db.query(SurveyResponse).filter(
                SurveyResponse.submitted_at.between(start_date, end_date)
            ).count()

            response_rate = survey_responses / max(survey_invitations, 1)

            # Analyze trends
            recent_trends = await self._analyze_feedback_trends(start_date, end_date)

            return FeedbackSummary(
                total_feedback=total_feedback,
                by_type=by_type,
                by_priority=by_priority,
                avg_satisfaction_score=avg_satisfaction,
                sentiment_distribution=sentiment_distribution,
                response_rate=response_rate,
                recent_trends=recent_trends
            )

        except Exception as e:
            logger.error(f"Error generating feedback summary: {e}")
            return FeedbackSummary(0, {}, {}, 0, {}, 0, {})

    async def _analyze_sentiment_distribution(self, feedback_items: List[Feedback]) -> Dict[str, int]:
        """Analyze sentiment distribution (simplified version)"""
        try:
            # Simplified sentiment analysis using keyword matching
            positive_keywords = ["great", "excellent", "love", "amazing", "perfect", "helpful"]
            negative_keywords = ["bad", "terrible", "hate", "awful", "broken", "useless"]

            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

            for feedback in feedback_items:
                text = feedback.content.lower()
                positive_score = sum(1 for word in positive_keywords if word in text)
                negative_score = sum(1 for word in negative_keywords if word in text)

                if positive_score > negative_score:
                    sentiment_counts["positive"] += 1
                elif negative_score > positive_score:
                    sentiment_counts["negative"] += 1
                else:
                    sentiment_counts["neutral"] += 1

            return sentiment_counts

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"positive": 0, "negative": 0, "neutral": 0}

    async def _analyze_feedback_trends(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Analyze feedback trends over time"""
        try:
            # Compare with previous period
            period_length = end_date - start_date
            previous_start = start_date - period_length
            previous_end = start_date

            current_count = self.db.query(Feedback).filter(
                Feedback.created_at.between(start_date, end_date)
            ).count()

            previous_count = self.db.query(Feedback).filter(
                Feedback.created_at.between(previous_start, previous_end)
            ).count()

            volume_trend = ((current_count - previous_count) / max(previous_count, 1)) * 100

            # Analyze satisfaction trend
            current_satisfaction = self.db.query(SurveyResponse).filter(
                and_(
                    SurveyResponse.submitted_at.between(start_date, end_date),
                    SurveyResponse.responses.has_key("satisfaction_score")
                )
            ).all()

            previous_satisfaction = self.db.query(SurveyResponse).filter(
                and_(
                    SurveyResponse.submitted_at.between(previous_start, previous_end),
                    SurveyResponse.responses.has_key("satisfaction_score")
                )
            ).all()

            current_avg = sum(r.responses["satisfaction_score"] for r in current_satisfaction) / max(len(current_satisfaction), 1)
            previous_avg = sum(r.responses["satisfaction_score"] for r in previous_satisfaction) / max(len(previous_satisfaction), 1)

            satisfaction_trend = current_avg - previous_avg

            return {
                "volume_change_percent": volume_trend,
                "satisfaction_change": satisfaction_trend,
                "response_rate_change": 0  # Placeholder
            }

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"volume_change_percent": 0, "satisfaction_change": 0}

    async def analyze_feature_requests(self) -> List[FeatureRequestAnalysis]:
        """Analyze and prioritize feature requests"""
        try:
            requests = self.db.query(FeatureRequest).filter(
                FeatureRequest.status.in_([
                    FeedbackStatus.NEW.value,
                    FeedbackStatus.REVIEWED.value
                ])
            ).all()

            analyses = []

            for request in requests:
                # Count unique requesters (including similar requests)
                requester_count = 1  # Original requester
                if request.similar_requests:
                    similar = self.db.query(FeatureRequest).filter(
                        FeatureRequest.id.in_(request.similar_requests)
                    ).all()
                    requester_count += len(set(r.user_id for r in similar))

                # Calculate business impact score
                business_impact = await self._calculate_business_impact(request)

                # Estimate technical feasibility
                technical_feasibility = await self._estimate_technical_feasibility(request)

                # Calculate priority score
                priority_score = (
                    request.votes * 0.3 +
                    requester_count * 0.4 +
                    business_impact * 0.2 +
                    technical_feasibility * 0.1
                )

                analysis = FeatureRequestAnalysis(
                    request_id=request.id,
                    title=request.title,
                    description=request.description,
                    requester_count=requester_count,
                    total_votes=request.votes,
                    estimated_effort=await self._estimate_development_effort(request),
                    business_impact=business_impact,
                    technical_feasibility=technical_feasibility,
                    priority_score=priority_score,
                    implementation_status=request.status,
                    related_requests=request.similar_requests or []
                )

                analyses.append(analysis)

            # Sort by priority score
            analyses.sort(key=lambda x: x.priority_score, reverse=True)
            return analyses

        except Exception as e:
            logger.error(f"Error analyzing feature requests: {e}")
            return []

    async def _calculate_business_impact(self, request: FeatureRequest) -> float:
        """Calculate business impact score for feature request"""
        # Simplified scoring based on keywords and use case
        high_impact_keywords = ["revenue", "efficiency", "automation", "compliance", "integration"]
        medium_impact_keywords = ["workflow", "usability", "performance", "reporting"]

        text = (request.title + " " + request.description + " " + request.use_case).lower()

        high_matches = sum(1 for keyword in high_impact_keywords if keyword in text)
        medium_matches = sum(1 for keyword in medium_impact_keywords if keyword in text)

        return min(10, high_matches * 3 + medium_matches * 2)

    async def _estimate_technical_feasibility(self, request: FeatureRequest) -> float:
        """Estimate technical feasibility (1-10 scale)"""
        # Simplified estimation based on complexity indicators
        complex_keywords = ["integration", "machine learning", "real-time", "migration"]
        simple_keywords = ["ui", "display", "filter", "sort", "export"]

        text = (request.title + " " + request.description).lower()

        complex_matches = sum(1 for keyword in complex_keywords if keyword in text)
        simple_matches = sum(1 for keyword in simple_keywords if keyword in text)

        if complex_matches > simple_matches:
            return 3.0  # Low feasibility
        elif simple_matches > 0:
            return 8.0  # High feasibility
        else:
            return 5.0  # Medium feasibility

    async def _estimate_development_effort(self, request: FeatureRequest) -> str:
        """Estimate development effort"""
        text = (request.title + " " + request.description).lower()

        if any(word in text for word in ["integration", "migration", "architecture"]):
            return "Large (8-13 weeks)"
        elif any(word in text for word in ["workflow", "automation", "processing"]):
            return "Medium (3-5 weeks)"
        else:
            return "Small (1-2 weeks)"

    async def identify_improvement_opportunities(self) -> List[ImprovementOpportunity]:
        """Identify product improvement opportunities from feedback"""
        try:
            # Analyze recent feedback for common themes
            recent_feedback = self.db.query(Feedback).filter(
                Feedback.created_at >= datetime.utcnow() - timedelta(days=90)
            ).all()

            # Group feedback by common themes/areas
            themes = await self._extract_feedback_themes(recent_feedback)

            opportunities = []

            for theme, feedback_items in themes.items():
                impact_score = len(feedback_items) * 2  # Simple scoring
                affected_users = len(set(f.user_id for f in feedback_items))

                opportunity = ImprovementOpportunity(
                    area=theme,
                    description=f"Address {len(feedback_items)} related feedback items",
                    impact_score=impact_score,
                    effort_estimate=await self._estimate_improvement_effort(theme, feedback_items),
                    supporting_feedback=[f.id for f in feedback_items],
                    affected_users=affected_users,
                    recommended_action=await self._recommend_improvement_action(theme, feedback_items)
                )

                opportunities.append(opportunity)

            # Sort by impact score
            opportunities.sort(key=lambda x: x.impact_score, reverse=True)
            return opportunities[:10]  # Top 10 opportunities

        except Exception as e:
            logger.error(f"Error identifying improvement opportunities: {e}")
            return []

    async def _extract_feedback_themes(self, feedback_items: List[Feedback]) -> Dict[str, List[Feedback]]:
        """Extract common themes from feedback"""
        themes = {
            "Performance": [],
            "User Experience": [],
            "Features": [],
            "Integration": [],
            "Support": [],
            "Documentation": [],
            "Other": []
        }

        for feedback in feedback_items:
            text = feedback.content.lower()
            categorized = False

            if any(word in text for word in ["slow", "performance", "speed", "loading"]):
                themes["Performance"].append(feedback)
                categorized = True

            if any(word in text for word in ["confusing", "difficult", "ui", "interface"]):
                themes["User Experience"].append(feedback)
                categorized = True

            if any(word in text for word in ["feature", "functionality", "capability"]):
                themes["Features"].append(feedback)
                categorized = True

            if any(word in text for word in ["integration", "api", "connect"]):
                themes["Integration"].append(feedback)
                categorized = True

            if any(word in text for word in ["help", "support", "documentation"]):
                themes["Support"].append(feedback)
                categorized = True

            if not categorized:
                themes["Other"].append(feedback)

        # Remove empty themes
        return {k: v for k, v in themes.items() if v}

    async def _estimate_improvement_effort(self, theme: str, feedback_items: List[Feedback]) -> str:
        """Estimate effort required for improvement"""
        effort_mapping = {
            "Performance": "Medium (4-6 weeks)",
            "User Experience": "Small (2-3 weeks)",
            "Features": "Large (6-12 weeks)",
            "Integration": "Large (8-16 weeks)",
            "Support": "Small (1-2 weeks)",
            "Documentation": "Small (1 week)"
        }

        return effort_mapping.get(theme, "Medium (3-5 weeks)")

    async def _recommend_improvement_action(self, theme: str, feedback_items: List[Feedback]) -> str:
        """Recommend specific action for improvement"""
        action_mapping = {
            "Performance": "Conduct performance audit and optimization",
            "User Experience": "Redesign identified UI components",
            "Features": "Prioritize most requested feature enhancements",
            "Integration": "Develop improved API and integration capabilities",
            "Support": "Enhance help documentation and support resources",
            "Documentation": "Update and expand user documentation"
        }

        return action_mapping.get(theme, "Further investigation required")


class FeedbackImprovementCycle:
    """Manages the complete feedback-to-improvement cycle"""

    def __init__(self, db: Session):
        self.db = db
        self.collector = FeedbackCollector(db)
        self.analyzer = FeedbackAnalyzer(db)
        self.notification_service = NotificationService()

    async def run_improvement_cycle(self) -> Dict:
        """Execute complete improvement cycle"""
        try:
            # 1. Analyze feedback and identify opportunities
            opportunities = await self.analyzer.identify_improvement_opportunities()

            # 2. Prioritize feature requests
            feature_analyses = await self.analyzer.analyze_feature_requests()

            # 3. Generate improvement recommendations
            recommendations = await self._generate_improvement_recommendations(
                opportunities, feature_analyses
            )

            # 4. Create action items for product team
            action_items = await self._create_action_items(recommendations)

            # 5. Schedule follow-up feedback collection
            await self._schedule_followup_feedback()

            # 6. Generate improvement cycle report
            report = {
                "cycle_date": datetime.utcnow().isoformat(),
                "opportunities_identified": len(opportunities),
                "feature_requests_analyzed": len(feature_analyses),
                "recommendations_generated": len(recommendations),
                "action_items_created": len(action_items),
                "top_opportunities": [
                    {
                        "area": opp.area,
                        "impact_score": opp.impact_score,
                        "affected_users": opp.affected_users,
                        "recommended_action": opp.recommended_action
                    }
                    for opp in opportunities[:5]
                ],
                "priority_features": [
                    {
                        "title": feat.title,
                        "priority_score": feat.priority_score,
                        "requester_count": feat.requester_count,
                        "business_impact": feat.business_impact
                    }
                    for feat in feature_analyses[:5]
                ]
            }

            logger.info(f"Improvement cycle completed: {len(recommendations)} recommendations generated")
            return report

        except Exception as e:
            logger.error(f"Error running improvement cycle: {e}")
            return {"error": "Failed to run improvement cycle"}

    async def _generate_improvement_recommendations(
        self,
        opportunities: List[ImprovementOpportunity],
        feature_analyses: List[FeatureRequestAnalysis]
    ) -> List[Dict]:
        """Generate actionable improvement recommendations"""
        recommendations = []

        # Process top opportunities
        for opp in opportunities[:5]:
            recommendations.append({
                "type": "improvement",
                "priority": "high" if opp.impact_score > 10 else "medium",
                "title": f"Address {opp.area} concerns",
                "description": opp.description,
                "effort": opp.effort_estimate,
                "impact": opp.impact_score,
                "action": opp.recommended_action,
                "supporting_data": opp.supporting_feedback
            })

        # Process top feature requests
        for feat in feature_analyses[:5]:
            if feat.priority_score > 5:
                recommendations.append({
                    "type": "feature",
                    "priority": "high" if feat.priority_score > 8 else "medium",
                    "title": f"Implement: {feat.title}",
                    "description": feat.description,
                    "effort": feat.estimated_effort,
                    "impact": feat.business_impact,
                    "votes": feat.total_votes,
                    "requesters": feat.requester_count
                })

        return recommendations

    async def _create_action_items(self, recommendations: List[Dict]) -> List[str]:
        """Create actionable items for product team"""
        action_items = []

        for rec in recommendations:
            # Create notification for product team
            await self.notification_service.create_notification({
                "user_id": "product_team",
                "type": "improvement_recommendation",
                "title": rec["title"],
                "message": f"Priority: {rec['priority']} | Impact: {rec.get('impact', 'N/A')}",
                "priority": rec["priority"],
                "metadata": rec
            })

            action_items.append(rec["title"])

        return action_items

    async def _schedule_followup_feedback(self):
        """Schedule follow-up feedback collection"""
        try:
            # Create quarterly NPS survey
            await self.collector.create_survey(
                survey_type=SurveyType.NPS,
                title="How likely are you to recommend Legal AI to a colleague?",
                description="Your feedback helps us improve our platform",
                questions=[
                    {
                        "id": "nps_score",
                        "type": "scale",
                        "question": "How likely are you to recommend Legal AI to a colleague?",
                        "scale": {"min": 0, "max": 10},
                        "required": True
                    },
                    {
                        "id": "feedback_text",
                        "type": "text",
                        "question": "What's the main reason for your score?",
                        "required": False
                    }
                ],
                target_segments=["highly_active", "moderately_active"]
            )

            logger.info("Follow-up feedback surveys scheduled")

        except Exception as e:
            logger.error(f"Error scheduling follow-up feedback: {e}")