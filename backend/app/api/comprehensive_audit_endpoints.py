"""
Comprehensive Audit API Endpoints

Provides admin access to:
- AI response logs with full context
- Hallucination audit trails
- Document access logs
- Admin action logs
- Search query analytics
- Error logs
- Usage statistics
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel

# Import dependencies - Railway compatible
try:
    from app.src.core.database import get_db
    from app.api.deps.auth import get_admin_user, CurrentUser
    from app.models.comprehensive_audit import (
        AIResponseLog, HallucinationAudit, DocumentAccessLog,
        AdminActionLog, SearchQueryLog, APIUsageLog, ErrorLog,
        AIAnalysisType, HallucinationType, HallucinationSeverity,
        DocumentAccessType, AdminActionType
    )
    from app.services.comprehensive_audit_service import ComprehensiveAuditService
except ImportError:
    from backend.app.src.core.database import get_db
    from backend.app.api.deps.auth import get_admin_user, CurrentUser
    from backend.app.models.comprehensive_audit import (
        AIResponseLog, HallucinationAudit, DocumentAccessLog,
        AdminActionLog, SearchQueryLog, APIUsageLog, ErrorLog,
        AIAnalysisType, HallucinationType, HallucinationSeverity,
        DocumentAccessType, AdminActionType
    )
    from backend.app.services.comprehensive_audit_service import ComprehensiveAuditService

router = APIRouter(prefix="/api/v1/audit", tags=["Comprehensive Audit"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class AuditSummary(BaseModel):
    """Summary of all audit activity."""
    total_ai_responses: int
    total_hallucinations: int
    total_document_accesses: int
    total_admin_actions: int
    total_errors: int
    period_start: datetime
    period_end: datetime


class HallucinationDetail(BaseModel):
    """Detailed hallucination information."""
    id: str
    hallucination_id: str
    hallucination_type: str
    severity: str
    field_name: str
    original_value: dict
    corrected_value: Optional[dict]
    detection_method: str
    detection_layer: str
    detection_reasoning: Optional[str]
    correction_action: str
    correction_reasoning: Optional[str]
    detected_at: datetime


class AIResponseWithHallucinations(BaseModel):
    """AI response with its hallucinations."""
    request_id: str
    user_id: Optional[int]
    document_id: Optional[int]
    document_name: Optional[str]
    analysis_type: str
    model_provider: str
    model_name: str
    raw_response: str
    processed_response: Optional[dict]
    confidence_score: Optional[float]
    hallucination_count: int
    correction_count: int
    success: bool
    request_timestamp: datetime
    hallucinations: List[dict]


# =============================================================================
# AI RESPONSE AUDIT ENDPOINTS
# =============================================================================

@router.get("/ai-responses")
def get_ai_responses(
    user_id: Optional[int] = None,
    document_id: Optional[int] = None,
    analysis_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    Get AI response audit logs.

    Provides complete visibility into what the AI was asked and what it returned.
    """
    try:
        query = select(AIResponseLog)

        conditions = []
        if user_id:
            conditions.append(AIResponseLog.user_id == user_id)
        if document_id:
            conditions.append(AIResponseLog.document_id == document_id)
        if analysis_type:
            try:
                at = AIAnalysisType(analysis_type)
                conditions.append(AIResponseLog.analysis_type == at)
            except ValueError:
                pass
        if start_date:
            conditions.append(AIResponseLog.request_timestamp >= start_date)
        if end_date:
            conditions.append(AIResponseLog.request_timestamp <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count(AIResponseLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get results
        query = query.order_by(desc(AIResponseLog.request_timestamp)).limit(limit).offset(offset)
        result = db.execute(query)
        rows = result.scalars().all()

        responses = []
        for row in rows:
            responses.append({
                "request_id": row.request_id,
                "user_id": row.user_id,
                "user_email": row.user_email,
                "document_id": row.document_id,
                "document_name": row.document_name,
                "document_type": row.document_type,
                "analysis_type": row.analysis_type.value if row.analysis_type else None,
                "model_provider": row.model_provider.value if row.model_provider else None,
                "model_name": row.model_name,
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
                "confidence_score": row.confidence_score,
                "quality_score": row.quality_score,
                "hallucination_count": row.hallucination_count,
                "correction_count": row.correction_count,
                "estimated_cost": float(row.estimated_cost) if row.estimated_cost else None,
                "processing_time_ms": row.processing_time_ms,
                "success": row.success,
                "error_message": row.error_message,
                "request_timestamp": row.request_timestamp.isoformat() if row.request_timestamp else None,
            })

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "responses": responses
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI responses: {str(e)}")


@router.get("/ai-responses/{request_id}")
def get_ai_response_detail(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    Get full details of a specific AI response including all hallucinations.

    This shows exactly:
    - What document was analyzed
    - What prompt was used
    - What the AI returned (raw and processed)
    - Every hallucination detected and how it was corrected
    """
    try:
        # Get the AI response
        result = db.execute(
            select(AIResponseLog).where(AIResponseLog.request_id == request_id)
        )
        response = result.scalar_one_or_none()

        if not response:
            raise HTTPException(status_code=404, detail="AI response not found")

        # Get associated hallucinations
        halluc_result = db.execute(
            select(HallucinationAudit)
            .where(HallucinationAudit.ai_response_id == response.id)
            .order_by(HallucinationAudit.sequence_number)
        )
        hallucinations = halluc_result.scalars().all()

        halluc_list = []
        for h in hallucinations:
            halluc_list.append({
                "hallucination_id": h.hallucination_id,
                "sequence_number": h.sequence_number,
                "hallucination_type": h.hallucination_type.value if h.hallucination_type else None,
                "severity": h.severity.value if h.severity else None,
                "field_name": h.field_name,
                "field_path": h.field_path,
                "section": h.section,
                "original_value": h.original_value,
                "original_text": h.original_text,
                "source_layer": h.source_layer,
                "source_document_excerpt": h.source_document_excerpt,
                "detection_method": h.detection_method,
                "detection_layer": h.detection_layer,
                "detection_rule": h.detection_rule,
                "detection_confidence": h.detection_confidence,
                "detection_reasoning": h.detection_reasoning,
                "cross_validation_performed": h.cross_validation_performed,
                "cross_validation_sources": h.cross_validation_sources,
                "cross_validation_results": h.cross_validation_results,
                "correction_action": h.correction_action.value if h.correction_action else None,
                "corrected_value": h.corrected_value,
                "corrected_text": h.corrected_text,
                "correction_source": h.correction_source,
                "correction_reasoning": h.correction_reasoning,
                "impact_assessment": h.impact_assessment,
                "detected_at": h.detected_at.isoformat() if h.detected_at else None,
                "corrected_at": h.corrected_at.isoformat() if h.corrected_at else None,
            })

        return {
            "request_id": response.request_id,
            "correlation_id": response.correlation_id,
            "user_id": response.user_id,
            "user_email": response.user_email,
            "session_id": response.session_id,
            "source_ip": str(response.source_ip) if response.source_ip else None,
            "document_id": response.document_id,
            "document_name": response.document_name,
            "document_type": response.document_type,
            "document_hash": response.document_hash,
            "analysis_type": response.analysis_type.value if response.analysis_type else None,
            "model_provider": response.model_provider.value if response.model_provider else None,
            "model_name": response.model_name,
            "model_version": response.model_version,
            "prompt_template": response.prompt_template,
            "input_text": response.input_text[:1000] + "..." if response.input_text and len(response.input_text) > 1000 else response.input_text,
            "input_tokens": response.input_tokens,
            "input_parameters": response.input_parameters,
            "raw_response": response.raw_response[:2000] + "..." if response.raw_response and len(response.raw_response) > 2000 else response.raw_response,
            "processed_response": response.processed_response,
            "output_tokens": response.output_tokens,
            "confidence_score": response.confidence_score,
            "quality_score": response.quality_score,
            "hallucination_count": response.hallucination_count,
            "correction_count": response.correction_count,
            "post_processing_applied": response.post_processing_applied,
            "final_output": response.final_output,
            "estimated_cost": float(response.estimated_cost) if response.estimated_cost else None,
            "actual_cost": float(response.actual_cost) if response.actual_cost else None,
            "processing_time_ms": response.processing_time_ms,
            "success": response.success,
            "error_message": response.error_message,
            "error_code": response.error_code,
            "request_timestamp": response.request_timestamp.isoformat() if response.request_timestamp else None,
            "response_timestamp": response.response_timestamp.isoformat() if response.response_timestamp else None,
            "hallucinations": halluc_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI response detail: {str(e)}")


# =============================================================================
# HALLUCINATION AUDIT ENDPOINTS
# =============================================================================

@router.get("/hallucinations")
def get_hallucinations(
    hallucination_type: Optional[str] = None,
    severity: Optional[str] = None,
    correction_action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    Get hallucination audit logs.

    Filter by type, severity, or correction action to find patterns.
    """
    try:
        query = select(HallucinationAudit)

        conditions = []
        if hallucination_type:
            try:
                ht = HallucinationType(hallucination_type)
                conditions.append(HallucinationAudit.hallucination_type == ht)
            except ValueError:
                pass
        if severity:
            try:
                sev = HallucinationSeverity(severity)
                conditions.append(HallucinationAudit.severity == sev)
            except ValueError:
                pass
        if correction_action:
            conditions.append(HallucinationAudit.correction_action == correction_action)
        if start_date:
            conditions.append(HallucinationAudit.detected_at >= start_date)
        if end_date:
            conditions.append(HallucinationAudit.detected_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count(HallucinationAudit.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get results
        query = query.order_by(desc(HallucinationAudit.detected_at)).limit(limit).offset(offset)
        result = db.execute(query)
        rows = result.scalars().all()

        hallucinations = []
        for h in rows:
            hallucinations.append({
                "hallucination_id": h.hallucination_id,
                "hallucination_type": h.hallucination_type.value if h.hallucination_type else None,
                "severity": h.severity.value if h.severity else None,
                "field_name": h.field_name,
                "original_value": h.original_value,
                "corrected_value": h.corrected_value,
                "detection_method": h.detection_method,
                "detection_layer": h.detection_layer,
                "detection_reasoning": h.detection_reasoning,
                "correction_action": h.correction_action.value if h.correction_action else None,
                "correction_reasoning": h.correction_reasoning,
                "detected_at": h.detected_at.isoformat() if h.detected_at else None,
            })

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "hallucinations": hallucinations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hallucinations: {str(e)}")


@router.get("/hallucinations/stats")
def get_hallucination_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    Get hallucination statistics for dashboard.

    Shows:
    - Total count
    - Breakdown by type
    - Breakdown by severity
    - Breakdown by correction action
    - Breakdown by detection method
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        conditions = [
            HallucinationAudit.detected_at >= start_date,
            HallucinationAudit.detected_at <= end_date
        ]

        # Get all hallucinations in period
        result = db.execute(
            select(HallucinationAudit).where(and_(*conditions))
        )
        rows = result.scalars().all()

        stats = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_count": len(rows),
            "by_type": {},
            "by_severity": {},
            "by_correction_action": {},
            "by_detection_method": {},
            "by_field": {},
        }

        for row in rows:
            # By type
            type_name = row.hallucination_type.value if row.hallucination_type else "unknown"
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1

            # By severity
            sev_name = row.severity.value if row.severity else "unknown"
            stats["by_severity"][sev_name] = stats["by_severity"].get(sev_name, 0) + 1

            # By correction action
            action_name = row.correction_action.value if row.correction_action else "unknown"
            stats["by_correction_action"][action_name] = stats["by_correction_action"].get(action_name, 0) + 1

            # By detection method
            method = row.detection_method or "unknown"
            stats["by_detection_method"][method] = stats["by_detection_method"].get(method, 0) + 1

            # By field (top 10)
            field = row.field_name or "unknown"
            stats["by_field"][field] = stats["by_field"].get(field, 0) + 1

        # Sort and limit by_field to top 10
        stats["by_field"] = dict(sorted(stats["by_field"].items(), key=lambda x: x[1], reverse=True)[:10])

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hallucination stats: {str(e)}")


@router.get("/hallucinations/{hallucination_id}")
def get_hallucination_detail(
    hallucination_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """Get full details of a specific hallucination."""
    try:
        result = db.execute(
            select(HallucinationAudit).where(HallucinationAudit.hallucination_id == hallucination_id)
        )
        h = result.scalar_one_or_none()

        if not h:
            raise HTTPException(status_code=404, detail="Hallucination not found")

        return {
            "hallucination_id": h.hallucination_id,
            "ai_response_id": str(h.ai_response_id) if h.ai_response_id else None,
            "sequence_number": h.sequence_number,
            "hallucination_type": h.hallucination_type.value if h.hallucination_type else None,
            "severity": h.severity.value if h.severity else None,
            "category": h.category,
            "field_name": h.field_name,
            "field_path": h.field_path,
            "section": h.section,
            "line_number": h.line_number,
            "original_value": h.original_value,
            "original_text": h.original_text,
            "source_layer": h.source_layer,
            "source_prompt_excerpt": h.source_prompt_excerpt,
            "source_document_excerpt": h.source_document_excerpt,
            "detection_method": h.detection_method,
            "detection_layer": h.detection_layer,
            "detection_rule": h.detection_rule,
            "detection_confidence": h.detection_confidence,
            "detection_reasoning": h.detection_reasoning,
            "cross_validation_performed": h.cross_validation_performed,
            "cross_validation_sources": h.cross_validation_sources,
            "cross_validation_results": h.cross_validation_results,
            "correction_action": h.correction_action.value if h.correction_action else None,
            "corrected_value": h.corrected_value,
            "corrected_text": h.corrected_text,
            "correction_source": h.correction_source,
            "correction_reasoning": h.correction_reasoning,
            "impact_assessment": h.impact_assessment,
            "affected_downstream": h.affected_downstream,
            "detected_at": h.detected_at.isoformat() if h.detected_at else None,
            "corrected_at": h.corrected_at.isoformat() if h.corrected_at else None,
            "shown_to_user": h.shown_to_user,
            "user_notified": h.user_notified,
            "user_acknowledged": h.user_acknowledged,
            "user_feedback": h.user_feedback,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hallucination detail: {str(e)}")


# =============================================================================
# DOCUMENT ACCESS ENDPOINTS
# =============================================================================

@router.get("/document-access")
def get_document_access_logs(
    user_id: Optional[int] = None,
    document_id: Optional[int] = None,
    access_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    Get document access logs.

    Shows who accessed what documents and when.
    """
    try:
        query = select(DocumentAccessLog)

        conditions = []
        if user_id:
            conditions.append(DocumentAccessLog.user_id == user_id)
        if document_id:
            conditions.append(DocumentAccessLog.document_id == document_id)
        if access_type:
            try:
                at = DocumentAccessType(access_type)
                conditions.append(DocumentAccessLog.access_type == at)
            except ValueError:
                pass
        if start_date:
            conditions.append(DocumentAccessLog.accessed_at >= start_date)
        if end_date:
            conditions.append(DocumentAccessLog.accessed_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count(DocumentAccessLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get results
        query = query.order_by(desc(DocumentAccessLog.accessed_at)).limit(limit).offset(offset)
        result = db.execute(query)
        rows = result.scalars().all()

        accesses = []
        for row in rows:
            accesses.append({
                "access_id": row.access_id,
                "user_id": row.user_id,
                "user_email": row.user_email,
                "user_role": row.user_role,
                "document_id": row.document_id,
                "document_name": row.document_name,
                "document_type": row.document_type,
                "access_type": row.access_type.value if row.access_type else None,
                "access_method": row.access_method,
                "case_name": row.case_name,
                "source_ip": str(row.source_ip) if row.source_ip else None,
                "success": row.success,
                "bytes_transferred": row.bytes_transferred,
                "accessed_at": row.accessed_at.isoformat() if row.accessed_at else None,
            })

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "accesses": accesses
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document access logs: {str(e)}")


# =============================================================================
# ADMIN ACTION ENDPOINTS
# =============================================================================

@router.get("/admin-actions")
def get_admin_action_logs(
    admin_id: Optional[int] = None,
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    Get admin action logs.

    Shows what admins have done, including their justifications.
    """
    try:
        query = select(AdminActionLog)

        conditions = []
        if admin_id:
            conditions.append(AdminActionLog.admin_id == admin_id)
        if action_type:
            try:
                at = AdminActionType(action_type)
                conditions.append(AdminActionLog.action_type == at)
            except ValueError:
                pass
        if target_type:
            conditions.append(AdminActionLog.target_type == target_type)
        if start_date:
            conditions.append(AdminActionLog.performed_at >= start_date)
        if end_date:
            conditions.append(AdminActionLog.performed_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count(AdminActionLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get results
        query = query.order_by(desc(AdminActionLog.performed_at)).limit(limit).offset(offset)
        result = db.execute(query)
        rows = result.scalars().all()

        actions = []
        for row in rows:
            actions.append({
                "action_id": row.action_id,
                "admin_id": row.admin_id,
                "admin_email": row.admin_email,
                "admin_role": row.admin_role,
                "action_type": row.action_type.value if row.action_type else None,
                "action_description": row.action_description,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "target_name": row.target_name,
                "reason": row.reason,
                "ticket_number": row.ticket_number,
                "success": row.success,
                "reversible": row.reversible,
                "reversed": row.reversed,
                "performed_at": row.performed_at.isoformat() if row.performed_at else None,
            })

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "actions": actions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch admin action logs: {str(e)}")


@router.get("/admin-actions/{action_id}")
def get_admin_action_detail(
    action_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """Get full details of a specific admin action including before/after state."""
    try:
        result = db.execute(
            select(AdminActionLog).where(AdminActionLog.action_id == action_id)
        )
        row = result.scalar_one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Admin action not found")

        return {
            "action_id": row.action_id,
            "admin_id": row.admin_id,
            "admin_email": row.admin_email,
            "admin_role": row.admin_role,
            "action_type": row.action_type.value if row.action_type else None,
            "action_description": row.action_description,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "target_name": row.target_name,
            "before_state": row.before_state,
            "after_state": row.after_state,
            "changes_made": row.changes_made,
            "reason": row.reason,
            "ticket_number": row.ticket_number,
            "authorization_reference": row.authorization_reference,
            "requires_approval": row.requires_approval,
            "approved_by": row.approved_by,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "approval_notes": row.approval_notes,
            "source_ip": str(row.source_ip) if row.source_ip else None,
            "session_id": row.session_id,
            "success": row.success,
            "error_message": row.error_message,
            "reversible": row.reversible,
            "reversed": row.reversed,
            "reversed_at": row.reversed_at.isoformat() if row.reversed_at else None,
            "reversed_by": row.reversed_by,
            "reversal_reason": row.reversal_reason,
            "performed_at": row.performed_at.isoformat() if row.performed_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch admin action detail: {str(e)}")


# =============================================================================
# SEARCH ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/search-queries")
def get_search_queries(
    user_id: Optional[int] = None,
    query_type: Optional[str] = None,
    zero_results_only: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """Get search query logs."""
    try:
        query = select(SearchQueryLog)

        conditions = []
        if user_id:
            conditions.append(SearchQueryLog.user_id == user_id)
        if query_type:
            conditions.append(SearchQueryLog.query_type == query_type)
        if zero_results_only:
            conditions.append(SearchQueryLog.results_count == 0)
        if start_date:
            conditions.append(SearchQueryLog.searched_at >= start_date)
        if end_date:
            conditions.append(SearchQueryLog.searched_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count(SearchQueryLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get results
        query = query.order_by(desc(SearchQueryLog.searched_at)).limit(limit).offset(offset)
        result = db.execute(query)
        rows = result.scalars().all()

        queries = []
        for row in rows:
            queries.append({
                "query_id": row.query_id,
                "user_id": row.user_id,
                "query_text": row.query_text,
                "query_type": row.query_type,
                "search_filters": row.search_filters,
                "results_count": row.results_count,
                "result_clicked": row.result_clicked,
                "clicked_position": row.clicked_position,
                "search_time_ms": row.search_time_ms,
                "searched_at": row.searched_at.isoformat() if row.searched_at else None,
            })

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "queries": queries
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch search queries: {str(e)}")


@router.get("/search-queries/top")
def get_top_search_queries(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """Get top search queries by frequency."""
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        conditions = [
            SearchQueryLog.searched_at >= start_date,
            SearchQueryLog.searched_at <= end_date
        ]

        result = db.execute(
            select(SearchQueryLog).where(and_(*conditions))
        )
        rows = result.scalars().all()

        # Aggregate by query text
        query_counts = {}
        for row in rows:
            qt = row.query_text.lower().strip()
            if qt not in query_counts:
                query_counts[qt] = {
                    "query_text": row.query_text,
                    "count": 0,
                    "avg_results": 0,
                    "click_rate": 0,
                    "total_results": 0,
                    "clicks": 0
                }
            query_counts[qt]["count"] += 1
            query_counts[qt]["total_results"] += row.results_count or 0
            if row.result_clicked:
                query_counts[qt]["clicks"] += 1

        # Calculate averages
        for qt, data in query_counts.items():
            if data["count"] > 0:
                data["avg_results"] = data["total_results"] / data["count"]
                data["click_rate"] = data["clicks"] / data["count"]

        # Sort by count and limit
        sorted_queries = sorted(query_counts.values(), key=lambda x: x["count"], reverse=True)[:limit]

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "top_queries": sorted_queries
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top search queries: {str(e)}")


# =============================================================================
# ERROR LOG ENDPOINTS
# =============================================================================

@router.get("/errors")
def get_error_logs(
    severity: Optional[str] = None,
    error_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """Get error logs."""
    try:
        query = select(ErrorLog)

        conditions = []
        if severity:
            conditions.append(ErrorLog.severity == severity)
        if error_type:
            conditions.append(ErrorLog.error_type == error_type)
        if resolved is not None:
            conditions.append(ErrorLog.resolved == resolved)
        if start_date:
            conditions.append(ErrorLog.occurred_at >= start_date)
        if end_date:
            conditions.append(ErrorLog.occurred_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count(ErrorLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get results
        query = query.order_by(desc(ErrorLog.occurred_at)).limit(limit).offset(offset)
        result = db.execute(query)
        rows = result.scalars().all()

        errors = []
        for row in rows:
            errors.append({
                "error_id": row.error_id,
                "user_id": row.user_id,
                "error_type": row.error_type,
                "error_code": row.error_code,
                "error_message": row.error_message,
                "component": row.component,
                "module": row.module,
                "endpoint": row.endpoint,
                "severity": row.severity,
                "acknowledged": row.acknowledged,
                "resolved": row.resolved,
                "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
            })

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch error logs: {str(e)}")


# =============================================================================
# SUMMARY ENDPOINTS
# =============================================================================

@router.get("/summary")
def get_audit_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    Get comprehensive audit summary.

    Provides quick overview of all audit activity.
    """
    try:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # Count AI responses
        ai_count = db.execute(
            select(func.count(AIResponseLog.id)).where(
                and_(
                    AIResponseLog.request_timestamp >= start_date,
                    AIResponseLog.request_timestamp <= end_date
                )
            )
        )
        total_ai_responses = ai_count.scalar() or 0

        # Count hallucinations
        halluc_count = db.execute(
            select(func.count(HallucinationAudit.id)).where(
                and_(
                    HallucinationAudit.detected_at >= start_date,
                    HallucinationAudit.detected_at <= end_date
                )
            )
        )
        total_hallucinations = halluc_count.scalar() or 0

        # Count document accesses
        doc_count = db.execute(
            select(func.count(DocumentAccessLog.id)).where(
                and_(
                    DocumentAccessLog.accessed_at >= start_date,
                    DocumentAccessLog.accessed_at <= end_date
                )
            )
        )
        total_document_accesses = doc_count.scalar() or 0

        # Count admin actions
        admin_count = db.execute(
            select(func.count(AdminActionLog.id)).where(
                and_(
                    AdminActionLog.performed_at >= start_date,
                    AdminActionLog.performed_at <= end_date
                )
            )
        )
        total_admin_actions = admin_count.scalar() or 0

        # Count errors
        error_count = db.execute(
            select(func.count(ErrorLog.id)).where(
                and_(
                    ErrorLog.occurred_at >= start_date,
                    ErrorLog.occurred_at <= end_date
                )
            )
        )
        total_errors = error_count.scalar() or 0

        # Count search queries
        search_count = db.execute(
            select(func.count(SearchQueryLog.id)).where(
                and_(
                    SearchQueryLog.searched_at >= start_date,
                    SearchQueryLog.searched_at <= end_date
                )
            )
        )
        total_searches = search_count.scalar() or 0

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_ai_responses": total_ai_responses,
            "total_hallucinations": total_hallucinations,
            "total_document_accesses": total_document_accesses,
            "total_admin_actions": total_admin_actions,
            "total_errors": total_errors,
            "total_searches": total_searches,
            "hallucination_rate": (total_hallucinations / total_ai_responses * 100) if total_ai_responses > 0 else 0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit summary: {str(e)}")
