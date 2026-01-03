"""
AI Safety Monitoring API Router for Legal AI System

Provides endpoints for monitoring AI output safety, confidence scoring,
and hallucination detection with real-time dashboards and alerting.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from collections import Counter

# Import monitoring modules
from app.src.monitoring import (
    OutputValidator,
    ConfidenceScoring,
    HallucinationDetector,
    AIMonitoringDashboard,
    SafetyViolation,
    ConfidenceScore,
    HallucinationResult,
    ViolationType,
    SeverityLevel,
    ConfidenceLevel
)

# Import authentication dependencies
from app.api.deps.auth import get_current_user, get_admin_user, get_current_user_id, CurrentUser

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize monitoring services
output_validator = OutputValidator()
confidence_scorer = ConfidenceScoring()
hallucination_detector = HallucinationDetector()
monitoring_dashboard = AIMonitoringDashboard(output_validator, confidence_scorer, hallucination_detector)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class MonitoringRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    context: Dict[str, Any] = Field(default_factory=dict)
    source_documents: List[str] = Field(default_factory=list)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v


class SafetyViolationResponse(BaseModel):
    id: str
    violation_type: str
    severity: str
    description: str
    location: str
    confidence_score: float
    suggested_action: str
    flagged_portion: str
    timestamp: datetime
    resolved: bool = False


class ConfidenceScoreResponse(BaseModel):
    overall_confidence: float
    confidence_level: str
    needs_review: bool
    uncertainty_flags: List[str]
    statement_count: int
    factors: Dict[str, float]
    timestamp: datetime


class HallucinationResponse(BaseModel):
    is_hallucination: bool
    confidence: float
    evidence_found: bool
    source_citations: List[str]
    explanation: str
    verification_attempts: int
    timestamp: datetime


class MonitoringResultResponse(BaseModel):
    violations: List[SafetyViolationResponse]
    confidence: ConfidenceScoreResponse
    hallucination: HallucinationResponse
    processing_time_ms: float
    recommendations: List[str]
    safe_for_publication: bool


class DashboardMetricsResponse(BaseModel):
    period_hours: int
    total_outputs_monitored: int
    violations: Dict[str, Any]
    confidence: Dict[str, Any]
    hallucinations: Dict[str, Any]
    performance: Dict[str, Any]
    alerts: Dict[str, Any]
    timestamp: datetime


class RealTimeStatusResponse(BaseModel):
    status: str
    alert_level: str
    last_monitoring_time: datetime
    active_alerts: int
    critical_alerts: int
    latest_confidence: float
    latest_violations: int
    system_health: str


class AlertResponse(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None


# =============================================================================
# MAIN MONITORING ENDPOINTS
# =============================================================================

@router.post(
    "/monitor/analyze",
    response_model=MonitoringResultResponse,
    summary="Analyze AI Output Safety",
    description="Comprehensive safety analysis of AI-generated content including violation detection, confidence scoring, and hallucination checking"
)
async def analyze_ai_output(
    request: MonitoringRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Perform comprehensive safety analysis of AI output"""
    try:
        start_time = time.time()
        
        # Run all safety checks concurrently
        violation_task = asyncio.create_task(
            run_validation_async(request.text, request.context)
        )
        confidence_task = asyncio.create_task(
            run_confidence_async(request.text, request.context)
        )
        hallucination_task = asyncio.create_task(
            hallucination_detector.detect_hallucinations(request.text, request.source_documents)
        )
        
        # Wait for all tasks to complete
        violations, confidence, hallucination = await asyncio.gather(
            violation_task, confidence_task, hallucination_task
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Convert to response format
        violation_responses = []
        for violation in violations:
            violation_responses.append(SafetyViolationResponse(
                id=violation.id,
                violation_type=violation.violation_type.value,
                severity=violation.severity.value,
                description=violation.description,
                location=violation.location,
                confidence_score=violation.confidence_score,
                suggested_action=violation.suggested_action,
                flagged_portion=violation.flagged_portion,
                timestamp=violation.timestamp,
                resolved=violation.resolved
            ))
        
        confidence_response = ConfidenceScoreResponse(
            overall_confidence=confidence.overall_confidence,
            confidence_level=confidence_scorer.get_confidence_level(confidence.overall_confidence).value,
            needs_review=confidence.needs_review,
            uncertainty_flags=confidence.uncertainty_flags,
            statement_count=len(confidence.statement_confidences),
            factors=confidence.factors,
            timestamp=confidence.timestamp
        )
        
        hallucination_response = HallucinationResponse(
            is_hallucination=hallucination.is_hallucination,
            confidence=hallucination.confidence,
            evidence_found=hallucination.evidence_found,
            source_citations=hallucination.source_citations,
            explanation=hallucination.explanation,
            verification_attempts=len(hallucination.verification_attempts),
            timestamp=hallucination.timestamp
        )
        
        # Generate recommendations
        recommendations = generate_safety_recommendations(violations, confidence, hallucination)
        
        # Determine if safe for publication
        safe_for_publication = determine_publication_safety(violations, confidence, hallucination)
        
        # Create response
        response = MonitoringResultResponse(
            violations=violation_responses,
            confidence=confidence_response,
            hallucination=hallucination_response,
            processing_time_ms=processing_time_ms,
            recommendations=recommendations,
            safe_for_publication=safe_for_publication
        )
        
        # Add to monitoring dashboard (background task)
        background_tasks.add_task(
            add_to_dashboard, 
            request.text, 
            violations, 
            confidence, 
            hallucination, 
            processing_time_ms
        )
        
        logger.info(f"AI safety analysis completed: {len(violations)} violations, confidence {confidence.overall_confidence:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"Error in AI safety analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing AI safety analysis"
        )


@router.post(
    "/monitor/batch-analyze",
    summary="Batch Analyze Multiple Outputs",
    description="Analyze multiple AI outputs in batch for efficiency"
)
async def batch_analyze_outputs(
    requests: List[MonitoringRequest] = Body(..., max_items=50),
    current_user: CurrentUser = Depends(get_admin_user)  # Admin only for batch operations
):
    """Batch analyze multiple AI outputs for efficiency"""
    try:
        if len(requests) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 50 items"
            )
        
        results = []
        start_time = time.time()
        
        # Process requests concurrently
        tasks = []
        for request in requests:
            task = asyncio.create_task(process_single_request(request))
            tasks.append(task)
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = 0
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Error processing batch item {i}: {result}")
                results.append({
                    "index": i,
                    "error": str(result),
                    "status": "failed"
                })
            else:
                results.append({
                    "index": i,
                    "result": result,
                    "status": "success"
                })
                successful_results += 1
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return {
            "total_requests": len(requests),
            "successful_results": successful_results,
            "failed_results": len(requests) - successful_results,
            "processing_time_ms": processing_time_ms,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch AI safety analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing batch AI safety analysis"
        )


# =============================================================================
# DASHBOARD AND METRICS ENDPOINTS
# =============================================================================

@router.get(
    "/monitor/dashboard",
    response_model=DashboardMetricsResponse,
    summary="Get Dashboard Metrics",
    description="Retrieve monitoring dashboard metrics and trends"
)
async def get_dashboard_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to include (1-168)"),
    current_user: CurrentUser = Depends(get_admin_user)  # Admin only for dashboard access
):
    """Get dashboard metrics for the specified time period"""
    try:
        metrics = monitoring_dashboard.get_dashboard_metrics(hours)
        
        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=metrics["error"]
            )
        
        response = DashboardMetricsResponse(
            period_hours=metrics["period_hours"],
            total_outputs_monitored=metrics["total_outputs_monitored"],
            violations=metrics["violations"],
            confidence=metrics["confidence"],
            hallucinations=metrics["hallucinations"],
            performance=metrics["performance"],
            alerts=metrics["alerts"],
            timestamp=datetime.now()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving dashboard metrics"
        )


@router.get(
    "/monitor/status",
    response_model=RealTimeStatusResponse,
    summary="Get Real-Time Status",
    description="Get current real-time monitoring system status"
)
async def get_real_time_status():
    """Get current real-time monitoring status"""
    try:
        status_info = monitoring_dashboard.get_real_time_status()
        
        response = RealTimeStatusResponse(
            status=status_info["status"],
            alert_level=status_info["alert_level"],
            last_monitoring_time=status_info["last_monitoring_time"],
            active_alerts=status_info["active_alerts"],
            critical_alerts=status_info["critical_alerts"],
            latest_confidence=status_info["latest_confidence"],
            latest_violations=status_info["latest_violations"],
            system_health=status_info["system_health"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving real-time status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving real-time status"
        )


@router.get(
    "/monitor/alerts",
    response_model=List[AlertResponse],
    summary="Get Active Alerts",
    description="Retrieve current active safety alerts"
)
async def get_active_alerts(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of alerts to return"),
    current_user: CurrentUser = Depends(get_admin_user)  # Admin only for alerts
):
    """Get active safety alerts"""
    try:
        # Filter alerts
        alerts = monitoring_dashboard._alerts
        
        if resolved is not None:
            alerts = [a for a in alerts if a.get("resolved", False) == resolved]
        
        if severity:
            alerts = [a for a in alerts if a.get("severity", "").value.lower() == severity.lower()]
        
        # Sort by timestamp (most recent first) and limit
        alerts = sorted(alerts, key=lambda x: x["timestamp"], reverse=True)[:limit]
        
        # Convert to response format
        alert_responses = []
        for alert in alerts:
            alert_responses.append(AlertResponse(
                id=alert["id"],
                type=alert["type"],
                severity=alert["severity"].value,
                message=alert["message"],
                details=alert["details"],
                timestamp=alert["timestamp"],
                resolved=alert["resolved"],
                resolved_at=alert.get("resolved_at")
            ))
        
        return alert_responses
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving alerts"
        )


@router.post(
    "/monitor/alerts/{alert_id}/resolve",
    summary="Resolve Alert",
    description="Mark a safety alert as resolved"
)
async def resolve_alert(
    alert_id: str,
    current_user: CurrentUser = Depends(get_admin_user)  # Admin only for resolving alerts
):
    """Resolve a safety alert"""
    try:
        success = monitoring_dashboard.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert '{alert_id}' not found"
            )
        
        return {"message": f"Alert '{alert_id}' resolved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resolving alert"
        )


# =============================================================================
# CONFIDENCE TRACKING ENDPOINTS
# =============================================================================

@router.get(
    "/monitor/confidence/trends",
    summary="Get Confidence Trends",
    description="Retrieve confidence scoring trends over time"
)
async def get_confidence_trends(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    current_user: CurrentUser = Depends(get_admin_user)  # Admin only for trends
):
    """Get confidence scoring trends"""
    try:
        trends = confidence_scorer.track_confidence_over_time(days)
        return trends
        
    except Exception as e:
        logger.error(f"Error retrieving confidence trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving confidence trends"
        )


@router.get(
    "/monitor/violations/patterns",
    summary="Get Violation Patterns",
    description="Analyze patterns in safety violations"
)
async def get_violation_patterns(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to analyze"),
    current_user: CurrentUser = Depends(get_admin_user)  # Admin only for violation patterns
):
    """Analyze violation patterns over time"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get recent monitoring data
        recent_data = [
            entry for entry in monitoring_dashboard._monitoring_data
            if entry["timestamp"] >= cutoff_date
        ]
        
        if not recent_data:
            return {"error": "No violation data available for the specified period"}
        
        # Analyze patterns
        violation_patterns = analyze_violation_patterns(recent_data, days)
        
        return violation_patterns
        
    except Exception as e:
        logger.error(f"Error analyzing violation patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing violation patterns"
        )


# =============================================================================
# HEALTH AND DIAGNOSTICS ENDPOINTS
# =============================================================================

@router.get(
    "/monitor/health",
    summary="Monitoring System Health Check",
    description="Check the health of the AI safety monitoring system"
)
async def monitoring_health_check():
    """Health check for AI safety monitoring system"""
    try:
        # Test all components
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now()
        }
        
        # Test OutputValidator
        try:
            test_text = "This is a test sentence for validation."
            test_violations = output_validator.validate_output(test_text)
            health_status["components"]["output_validator"] = {
                "status": "healthy",
                "test_result": f"Processed test input, found {len(test_violations)} violations"
            }
        except Exception as e:
            health_status["components"]["output_validator"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Test ConfidenceScoring
        try:
            test_confidence = confidence_scorer.calculate_confidence(test_text)
            health_status["components"]["confidence_scorer"] = {
                "status": "healthy",
                "test_result": f"Generated confidence score: {test_confidence.overall_confidence:.2f}"
            }
        except Exception as e:
            health_status["components"]["confidence_scorer"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Test HallucinationDetector
        try:
            test_hallucination = await hallucination_detector.detect_hallucinations(test_text, [])
            health_status["components"]["hallucination_detector"] = {
                "status": "healthy",
                "test_result": f"Hallucination check completed, confidence: {test_hallucination.confidence:.2f}"
            }
        except Exception as e:
            health_status["components"]["hallucination_detector"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Test Dashboard
        try:
            dashboard_status = monitoring_dashboard.get_real_time_status()
            health_status["components"]["monitoring_dashboard"] = {
                "status": "healthy",
                "system_health": dashboard_status["system_health"],
                "active_alerts": dashboard_status["active_alerts"]
            }
        except Exception as e:
            health_status["components"]["monitoring_dashboard"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Determine overall status
        unhealthy_components = [
            comp for comp in health_status["components"].values() 
            if comp["status"] == "unhealthy"
        ]
        
        if unhealthy_components:
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }
        )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def run_validation_async(text: str, context: Dict[str, Any]) -> List[SafetyViolation]:
    """Run output validation asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, output_validator.validate_output, text, context)


async def run_confidence_async(text: str, context: Dict[str, Any]) -> ConfidenceScore:
    """Run confidence scoring asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, confidence_scorer.calculate_confidence, text, context)


async def process_single_request(request: MonitoringRequest) -> Dict[str, Any]:
    """Process a single monitoring request"""
    start_time = time.time()
    
    # Run all checks
    violations = await run_validation_async(request.text, request.context)
    confidence = await run_confidence_async(request.text, request.context)
    hallucination = await hallucination_detector.detect_hallucinations(request.text, request.source_documents)
    
    processing_time_ms = (time.time() - start_time) * 1000
    
    return {
        "violations_count": len(violations),
        "confidence_score": confidence.overall_confidence,
        "needs_review": confidence.needs_review,
        "is_hallucination": hallucination.is_hallucination,
        "processing_time_ms": processing_time_ms
    }


def add_to_dashboard(text: str, violations: List[SafetyViolation], confidence: ConfidenceScore, 
                    hallucination: HallucinationResult, processing_time_ms: float):
    """Add monitoring result to dashboard (background task)"""
    try:
        monitoring_dashboard.add_monitoring_result(
            text, violations, confidence, hallucination, processing_time_ms
        )
    except Exception as e:
        logger.error(f"Error adding to dashboard: {e}")


def generate_safety_recommendations(violations: List[SafetyViolation], confidence: ConfidenceScore, 
                                  hallucination: HallucinationResult) -> List[str]:
    """Generate safety recommendations based on analysis results"""
    recommendations = []
    
    # Violation-based recommendations
    if any(v.severity == SeverityLevel.CRITICAL for v in violations):
        recommendations.append("CRITICAL: Content contains serious safety violations and should not be published without review")
    
    if any(v.violation_type == ViolationType.LEGAL_ADVICE for v in violations):
        recommendations.append("Add clear disclaimers that content is informational only and not legal advice")
    
    if any(v.violation_type == ViolationType.DEADLINE_INACCURACY for v in violations):
        recommendations.append("Verify all deadline information with current legal rules and regulations")
    
    if any(v.violation_type == ViolationType.ETHICAL_VIOLATION for v in violations):
        recommendations.append("Remove content that inappropriately claims attorney-client relationships or privileges")
    
    # Confidence-based recommendations
    if confidence.overall_confidence < 0.3:
        recommendations.append("Very low confidence detected - require attorney review before publication")
    elif confidence.overall_confidence < 0.6:
        recommendations.append("Moderate confidence - consider adding uncertainty language and disclaimers")
    
    if confidence.needs_review:
        recommendations.append("System flagged for attorney review based on confidence analysis")
    
    # Hallucination-based recommendations
    if hallucination.is_hallucination and hallucination.confidence > 0.7:
        recommendations.append("High-confidence hallucination detected - verify all factual claims against reliable sources")
    
    if not hallucination.evidence_found and hallucination.source_citations:
        recommendations.append("Citations could not be verified - check all legal references for accuracy")
    
    # General recommendations
    if not recommendations:
        recommendations.append("Content passed safety checks but should still include appropriate legal disclaimers")
    
    return recommendations


def determine_publication_safety(violations: List[SafetyViolation], confidence: ConfidenceScore, 
                               hallucination: HallucinationResult) -> bool:
    """Determine if content is safe for publication"""
    
    # Block if critical violations
    if any(v.severity == SeverityLevel.CRITICAL for v in violations):
        return False
    
    # Block if very low confidence
    if confidence.overall_confidence < 0.2:
        return False
    
    # Block if high-confidence hallucination
    if hallucination.is_hallucination and hallucination.confidence > 0.8:
        return False
    
    # Block if too many high-severity violations
    high_severity_count = len([v for v in violations if v.severity == SeverityLevel.HIGH])
    if high_severity_count > 3:
        return False
    
    return True


def analyze_violation_patterns(monitoring_data: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
    """Analyze patterns in violations over time"""
    from collections import defaultdict
    import statistics
    
    # Group violations by type and day
    daily_violations = defaultdict(lambda: defaultdict(int))
    violation_severities = defaultdict(list)
    violation_locations = defaultdict(list)
    
    for entry in monitoring_data:
        day = entry["timestamp"].date()
        for violation in entry["violations"]:
            violation_type = violation.violation_type.value
            daily_violations[day][violation_type] += 1
            violation_severities[violation_type].append(violation.severity.value)
            violation_locations[violation_type].append(violation.location)
    
    # Calculate trends and patterns
    patterns = {
        "analysis_period_days": days,
        "total_violations": sum(len(entry["violations"]) for entry in monitoring_data),
        "violation_trends": {},
        "severity_distribution": {},
        "common_patterns": [],
        "recommendations": []
    }
    
    # Analyze trends for each violation type
    for violation_type in ViolationType:
        type_name = violation_type.value
        daily_counts = [daily_violations[day].get(type_name, 0) for day in sorted(daily_violations.keys())]
        
        if daily_counts:
            patterns["violation_trends"][type_name] = {
                "total_count": sum(daily_counts),
                "average_per_day": statistics.mean(daily_counts),
                "max_in_day": max(daily_counts),
                "trend": "stable"  # Could add trend calculation
            }
    
    # Severity distribution
    for violation_type, severities in violation_severities.items():
        severity_count = Counter(severities)
        patterns["severity_distribution"][violation_type] = dict(severity_count)
    
    # Generate recommendations based on patterns
    total_violations = patterns["total_violations"]
    if total_violations > 0:
        most_common_type = max(patterns["violation_trends"].items(), key=lambda x: x[1]["total_count"])
        patterns["recommendations"].append(f"Focus on reducing {most_common_type[0]} violations (most frequent)")
        
        if total_violations / days > 10:
            patterns["recommendations"].append("High violation rate detected - review AI model training")
    
    return patterns