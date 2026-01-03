"""
Customer Success API Endpoints

FastAPI endpoints for customer success tracking, metrics, feedback,
surveys, outreach management, and improvement cycle operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..models.success_tracking import (
    UserHealthScore, ChurnPrediction, FeatureUsageMetrics,
    Feedback, FeatureRequest, BugReport, Survey, SurveyResponse,
    Testimonial, OutreachAction, SuccessMetric
)
from ..success.metrics import SuccessMetricsCalculator, MetricsDashboard, User
from ..success.outreach import ProactiveOutreachEngine, RenewalManager
from ..success.feedback import FeedbackCollector, FeedbackAnalyzer, FeedbackImprovementCycle
# Mock logger - replace with actual logger import
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

try:
    from ..utils.logger import logger
except ImportError:
    logger = MockLogger()

# Mock classes for missing security - these should be replaced with actual imports
async def get_current_user():
    return User()

def require_permissions(permissions):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator


router = APIRouter(prefix="/api/success", tags=["Customer Success"])
security = HTTPBearer()


# Pydantic models for API requests/responses
class HealthScoreResponse(BaseModel):
    user_id: str
    health_score: float
    status: str
    component_scores: Dict[str, float]
    risk_factors: List[str]
    last_calculated: datetime


class MetricsSummaryResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    onboarding_completion_rate: float
    nps_score: float
    support_satisfaction: float
    feature_adoption_rates: Dict[str, float]
    churn_risk_users: int
    total_feedback: int


class FeedbackCreateRequest(BaseModel):
    type: str
    content: str
    priority: Optional[str] = "medium"
    category: Optional[str] = None
    page_url: Optional[str] = None
    browser_info: Optional[str] = None
    metadata: Optional[Dict] = None


class FeatureRequestCreateRequest(BaseModel):
    title: str
    description: str
    use_case: str
    business_justification: Optional[str] = None
    priority: Optional[str] = "medium"


class BugReportCreateRequest(BaseModel):
    title: str
    description: str
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    browser_info: Optional[str] = None
    screenshots: Optional[List[str]] = None


class SurveyCreateRequest(BaseModel):
    type: str
    title: str
    description: str
    questions: List[Dict]
    target_segments: Optional[List[str]] = None
    expires_in_days: Optional[int] = 30


class SurveyResponseRequest(BaseModel):
    survey_id: str
    responses: Dict[str, Any]


class TestimonialCreateRequest(BaseModel):
    content: str
    rating: int = Field(..., ge=1, le=5)
    use_case: Optional[str] = None
    results_achieved: Optional[str] = None
    permission_to_publish: Optional[bool] = False


# Health Score Endpoints
@router.get("/health-score/{user_id}")
async def get_user_health_score(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> HealthScoreResponse:
    """Get current health score for a user"""
    try:
        # Check permissions
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        calculator = SuccessMetricsCalculator(db)
        health_score, status = await calculator.calculate_health_score(user_id)

        # Get latest health score record
        latest_score = db.query(UserHealthScore).filter(
            UserHealthScore.user_id == user_id
        ).order_by(UserHealthScore.calculation_date.desc()).first()

        component_scores = {}
        risk_factors = []

        if latest_score:
            component_scores = {
                "login": latest_score.login_score or 0,
                "usage": latest_score.usage_score or 0,
                "support": latest_score.support_score or 0,
                "onboarding": latest_score.onboarding_score or 0,
                "payment": latest_score.payment_score or 0
            }
            risk_factors = latest_score.risk_indicators or []

        return HealthScoreResponse(
            user_id=user_id,
            health_score=health_score,
            status=status.value,
            component_scores=component_scores,
            risk_factors=risk_factors,
            last_calculated=latest_score.calculation_date if latest_score else datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error getting health score for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health score")


@router.get("/health-scores/at-risk")
async def get_at_risk_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> List[HealthScoreResponse]:
    """Get users with at-risk or critical health scores"""
    try:
        at_risk_scores = db.query(UserHealthScore).filter(
            UserHealthScore.status.in_(["at_risk", "critical"])
        ).order_by(UserHealthScore.health_score).all()

        results = []
        for score in at_risk_scores:
            results.append(HealthScoreResponse(
                user_id=score.user_id,
                health_score=score.health_score,
                status=score.status.value,
                component_scores={
                    "login": score.login_score or 0,
                    "usage": score.usage_score or 0,
                    "support": score.support_score or 0,
                    "onboarding": score.onboarding_score or 0,
                    "payment": score.payment_score or 0
                },
                risk_factors=score.risk_indicators or [],
                last_calculated=score.calculation_date
            ))

        return results

    except Exception as e:
        logger.error(f"Error getting at-risk users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get at-risk users")


# Metrics Dashboard Endpoints
@router.get("/metrics/dashboard")
async def get_metrics_dashboard(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> Dict:
    """Get comprehensive metrics dashboard data"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        dashboard = MetricsDashboard(db)
        data = await dashboard.generate_dashboard_data(start_date, end_date)

        return data

    except Exception as e:
        logger.error(f"Error generating metrics dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard")


@router.get("/metrics/summary")
async def get_metrics_summary(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> MetricsSummaryResponse:
    """Get high-level metrics summary"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        calculator = SuccessMetricsCalculator(db)

        # Get key metrics concurrently
        onboarding_metrics = await calculator.calculate_onboarding_metrics(start_date, end_date)
        nps_metrics = await calculator.calculate_nps_metrics(start_date, end_date)
        support_metrics = await calculator.calculate_support_metrics(start_date, end_date)

        # Get feature adoption rates
        key_features = ["document_analysis", "legal_research", "citation_processing"]
        feature_adoption = {}
        for feature in key_features:
            adoption = await calculator.calculate_feature_adoption(feature, start_date, end_date)
            feature_adoption[feature] = adoption.adoption_rate

        # Count at-risk users
        at_risk_count = db.query(UserHealthScore).filter(
            UserHealthScore.status.in_(["at_risk", "critical"])
        ).count()

        # Total feedback in period
        total_feedback = db.query(Feedback).filter(
            Feedback.created_at.between(start_date, end_date)
        ).count()

        return MetricsSummaryResponse(
            period_start=start_date,
            period_end=end_date,
            onboarding_completion_rate=onboarding_metrics.completion_rate,
            nps_score=nps_metrics.nps_score,
            support_satisfaction=support_metrics.satisfaction_score,
            feature_adoption_rates=feature_adoption,
            churn_risk_users=at_risk_count,
            total_feedback=total_feedback
        )

    except Exception as e:
        logger.error(f"Error generating metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


# Feedback Collection Endpoints
@router.post("/feedback")
async def submit_feedback(
    feedback_data: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Submit user feedback"""
    try:
        feedback = Feedback(
            user_id=current_user.id,
            client_id=current_user.client_id,
            type=feedback_data.type,
            content=feedback_data.content,
            priority=feedback_data.priority,
            category=feedback_data.category,
            page_url=feedback_data.page_url,
            browser_info=feedback_data.browser_info,
            metadata=feedback_data.metadata,
            created_at=datetime.utcnow()
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"Feedback submitted by user {current_user.id}: {feedback.id}")

        return {
            "feedback_id": feedback.id,
            "status": "submitted",
            "message": "Thank you for your feedback!"
        }

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.post("/feature-requests")
async def submit_feature_request(
    request_data: FeatureRequestCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Submit feature request"""
    try:
        collector = FeedbackCollector(db)
        request_id = await collector.collect_feature_request(
            user_id=current_user.id,
            title=request_data.title,
            description=request_data.description,
            use_case=request_data.use_case,
            priority=request_data.priority
        )

        return {
            "request_id": request_id,
            "status": "submitted",
            "message": "Feature request submitted successfully!"
        }

    except Exception as e:
        logger.error(f"Error submitting feature request: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feature request")


@router.post("/bug-reports")
async def submit_bug_report(
    bug_data: BugReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Submit bug report"""
    try:
        collector = FeedbackCollector(db)
        bug_id = await collector.collect_bug_report(
            user_id=current_user.id,
            title=bug_data.title,
            description=bug_data.description,
            steps_to_reproduce=bug_data.steps_to_reproduce or "",
            expected_behavior=bug_data.expected_behavior or "",
            actual_behavior=bug_data.actual_behavior or "",
            browser_info=bug_data.browser_info,
            screenshots=bug_data.screenshots
        )

        return {
            "bug_id": bug_id,
            "status": "submitted",
            "message": "Bug report submitted successfully!"
        }

    except Exception as e:
        logger.error(f"Error submitting bug report: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit bug report")


# Survey Management Endpoints
@router.post("/surveys")
async def create_survey(
    survey_data: SurveyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> Dict:
    """Create and deploy a new survey"""
    try:
        collector = FeedbackCollector(db)
        survey_id = await collector.create_survey(
            survey_type=survey_data.type,
            title=survey_data.title,
            description=survey_data.description,
            questions=survey_data.questions,
            target_segments=survey_data.target_segments
        )

        return {
            "survey_id": survey_id,
            "status": "created",
            "message": "Survey created and deployed successfully!"
        }

    except Exception as e:
        logger.error(f"Error creating survey: {e}")
        raise HTTPException(status_code=500, detail="Failed to create survey")


@router.get("/surveys/{survey_id}")
async def get_survey(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get survey details for user response"""
    try:
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        if not survey.is_active:
            raise HTTPException(status_code=400, detail="Survey is not active")

        # Check if user already responded
        existing_response = db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == current_user.id
        ).first()

        if existing_response and not survey.allow_multiple_responses:
            raise HTTPException(status_code=400, detail="Already responded to this survey")

        return {
            "survey_id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "questions": survey.questions,
            "expires_at": survey.expires_at,
            "already_responded": bool(existing_response)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting survey {survey_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get survey")


@router.post("/surveys/{survey_id}/responses")
async def submit_survey_response(
    survey_id: str,
    response_data: SurveyResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Submit survey response"""
    try:
        collector = FeedbackCollector(db)
        success = await collector.submit_survey_response(
            survey_id=survey_id,
            user_id=current_user.id,
            responses=response_data.responses
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to submit response")

        return {
            "status": "submitted",
            "message": "Thank you for your response!"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting survey response: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit response")


@router.post("/testimonials")
async def submit_testimonial(
    testimonial_data: TestimonialCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Submit customer testimonial"""
    try:
        collector = FeedbackCollector(db)
        testimonial_id = await collector.collect_testimonial(
            user_id=current_user.id,
            content=testimonial_data.content,
            rating=testimonial_data.rating,
            use_case=testimonial_data.use_case or "",
            results_achieved=testimonial_data.results_achieved or "",
            permission_to_publish=testimonial_data.permission_to_publish
        )

        return {
            "testimonial_id": testimonial_id,
            "status": "submitted",
            "message": "Thank you for sharing your success story!"
        }

    except Exception as e:
        logger.error(f"Error submitting testimonial: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit testimonial")


# Outreach Management Endpoints
@router.post("/outreach/trigger")
async def trigger_outreach_monitoring(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> Dict:
    """Manually trigger outreach monitoring cycle"""
    try:
        def run_outreach():
            outreach_engine = ProactiveOutreachEngine(db)
            return outreach_engine.monitor_and_trigger_outreach()

        background_tasks.add_task(run_outreach)

        return {
            "status": "triggered",
            "message": "Outreach monitoring cycle started"
        }

    except Exception as e:
        logger.error(f"Error triggering outreach: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger outreach")


@router.get("/outreach/actions")
async def get_outreach_actions(
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> List[Dict]:
    """Get recent outreach actions"""
    try:
        query = db.query(OutreachAction).order_by(OutreachAction.created_at.desc())

        if user_id:
            query = query.filter(OutreachAction.user_id == user_id)

        actions = query.limit(limit).all()

        return [
            {
                "id": action.id,
                "user_id": action.user_id,
                "type": action.outreach_type.value,
                "priority": action.priority.value,
                "channel": action.channel.value,
                "scheduled_for": action.scheduled_for,
                "executed_at": action.executed_at,
                "success": action.success,
                "trigger_id": action.trigger_id
            }
            for action in actions
        ]

    except Exception as e:
        logger.error(f"Error getting outreach actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get outreach actions")


# Renewal Management Endpoints
@router.get("/renewals")
async def get_renewal_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> Dict:
    """Get renewal management insights"""
    try:
        renewal_manager = RenewalManager(db)
        insights = await renewal_manager.manage_renewals()
        return insights

    except Exception as e:
        logger.error(f"Error getting renewal insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get renewal insights")


# Analytics and Reporting Endpoints
@router.get("/analytics/feedback")
async def get_feedback_analytics(
    days: int = Query(90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> Dict:
    """Get feedback analytics summary"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        analyzer = FeedbackAnalyzer(db)
        summary = await analyzer.generate_feedback_summary(start_date, end_date)

        return {
            "period": {"start": start_date, "end": end_date},
            "total_feedback": summary.total_feedback,
            "by_type": summary.by_type,
            "by_priority": summary.by_priority,
            "avg_satisfaction": summary.avg_satisfaction_score,
            "sentiment_distribution": summary.sentiment_distribution,
            "response_rate": summary.response_rate,
            "trends": summary.recent_trends
        }

    except Exception as e:
        logger.error(f"Error getting feedback analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback analytics")


@router.get("/analytics/feature-requests")
async def get_feature_request_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "product"]))
) -> List[Dict]:
    """Get feature request analysis and prioritization"""
    try:
        analyzer = FeedbackAnalyzer(db)
        analyses = await analyzer.analyze_feature_requests()

        return [
            {
                "request_id": analysis.request_id,
                "title": analysis.title,
                "description": analysis.description,
                "requester_count": analysis.requester_count,
                "votes": analysis.total_votes,
                "business_impact": analysis.business_impact,
                "technical_feasibility": analysis.technical_feasibility,
                "priority_score": analysis.priority_score,
                "estimated_effort": analysis.estimated_effort,
                "status": analysis.implementation_status
            }
            for analysis in analyses
        ]

    except Exception as e:
        logger.error(f"Error analyzing feature requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze feature requests")


@router.get("/improvement-opportunities")
async def get_improvement_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "product"]))
) -> List[Dict]:
    """Get identified improvement opportunities"""
    try:
        analyzer = FeedbackAnalyzer(db)
        opportunities = await analyzer.identify_improvement_opportunities()

        return [
            {
                "area": opp.area,
                "description": opp.description,
                "impact_score": opp.impact_score,
                "effort_estimate": opp.effort_estimate,
                "affected_users": opp.affected_users,
                "recommended_action": opp.recommended_action,
                "supporting_feedback_count": len(opp.supporting_feedback)
            }
            for opp in opportunities
        ]

    except Exception as e:
        logger.error(f"Error getting improvement opportunities: {e}")
        raise HTTPException(status_code=500, detail="Failed to get improvement opportunities")


@router.post("/improvement-cycle/run")
async def run_improvement_cycle(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "product"]))
) -> Dict:
    """Run the complete feedback-to-improvement cycle"""
    try:
        def run_cycle():
            cycle = FeedbackImprovementCycle(db)
            return cycle.run_improvement_cycle()

        background_tasks.add_task(run_cycle)

        return {
            "status": "started",
            "message": "Improvement cycle initiated successfully"
        }

    except Exception as e:
        logger.error(f"Error running improvement cycle: {e}")
        raise HTTPException(status_code=500, detail="Failed to run improvement cycle")


# Churn Prevention Endpoints
@router.get("/churn/predictions")
async def get_churn_predictions(
    high_risk_only: bool = Query(False),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> List[Dict]:
    """Get churn predictions for users"""
    try:
        query = db.query(ChurnPrediction).order_by(ChurnPrediction.churn_probability.desc())

        if high_risk_only:
            query = query.filter(ChurnPrediction.churn_probability >= 0.7)

        predictions = query.limit(limit).all()

        return [
            {
                "user_id": pred.user_id,
                "churn_probability": pred.churn_probability,
                "days_to_churn": pred.days_to_predicted_churn,
                "risk_factors": pred.risk_factors,
                "recommended_actions": pred.recommended_actions,
                "prediction_date": pred.prediction_date,
                "intervention_applied": pred.intervention_applied
            }
            for pred in predictions
        ]

    except Exception as e:
        logger.error(f"Error getting churn predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get churn predictions")


@router.post("/churn/predict/{user_id}")
async def predict_user_churn(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "customer_success"]))
) -> Dict:
    """Generate churn prediction for specific user"""
    try:
        calculator = SuccessMetricsCalculator(db)
        prediction = await calculator.predict_churn(user_id)

        # Save prediction to database
        churn_prediction = ChurnPrediction(
            user_id=user_id,
            client_id=db.query(User).filter(User.id == user_id).first().client_id,
            churn_probability=prediction.churn_probability,
            days_to_predicted_churn=prediction.days_to_predicted_churn,
            risk_factors=prediction.risk_factors,
            recommended_actions=prediction.recommended_actions,
            prediction_date=datetime.utcnow(),
            confidence_score=0.85  # Default confidence
        )

        db.add(churn_prediction)
        db.commit()

        return {
            "user_id": user_id,
            "churn_probability": prediction.churn_probability,
            "risk_factors": prediction.risk_factors,
            "recommended_actions": prediction.recommended_actions,
            "days_to_predicted_churn": prediction.days_to_predicted_churn
        }

    except Exception as e:
        logger.error(f"Error predicting churn for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict churn")


# Health monitoring endpoint for system status
@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict:
    """Health check endpoint for customer success system"""
    try:
        # Basic database connectivity test
        db.execute("SELECT 1")

        # Count recent activities
        recent_feedback = db.query(Feedback).filter(
            Feedback.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()

        recent_outreach = db.query(OutreachAction).filter(
            OutreachAction.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "metrics": {
                "recent_feedback_24h": recent_feedback,
                "recent_outreach_24h": recent_outreach,
                "database_connected": True
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }