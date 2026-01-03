"""
Audit Integration Module

This module bridges the in-memory AnalysisAuditTrail with the
database-backed ComprehensiveAuditService.

Usage:
    from app.services.audit_integration import persist_analysis_audit

    # After analysis completes:
    await persist_analysis_audit(
        db=session,
        audit_trail=analysis_audit_trail,
        user_id=user_id,
        document_id=doc_id,
        document_name=filename,
        model_provider="anthropic",
        model_name="claude-3-opus",
        raw_response=raw_ai_response,
        processed_response=final_result
    )
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Import models and services
try:
    from app.models.comprehensive_audit import (
        AIModelProvider, AIAnalysisType, HallucinationType,
        HallucinationSeverity, CorrectionAction, DocumentAccessType
    )
    from app.services.comprehensive_audit_service import ComprehensiveAuditService
    from app.src.services.analysis_audit_trail import AnalysisAuditTrail
except ImportError:
    from backend.app.models.comprehensive_audit import (
        AIModelProvider, AIAnalysisType, HallucinationType,
        HallucinationSeverity, CorrectionAction, DocumentAccessType
    )
    from backend.app.services.comprehensive_audit_service import ComprehensiveAuditService
    from backend.app.src.services.analysis_audit_trail import AnalysisAuditTrail

logger = logging.getLogger(__name__)


# Mapping from analysis audit item types to HallucinationType
ITEM_TYPE_TO_HALLUCINATION_TYPE = {
    "party": HallucinationType.FABRICATED_PARTY,
    "parties": HallucinationType.FABRICATED_PARTY,
    "date": HallucinationType.FABRICATED_DATE,
    "dates": HallucinationType.FABRICATED_DATE,
    "amount": HallucinationType.FABRICATED_AMOUNT,
    "monetary_amount": HallucinationType.FABRICATED_AMOUNT,
    "monetary_amounts": HallucinationType.FABRICATED_AMOUNT,
    "citation": HallucinationType.FABRICATED_CITATION,
    "citations": HallucinationType.FABRICATED_CITATION,
    "case_number": HallucinationType.FABRICATED_CASE_NUMBER,
    "fact": HallucinationType.INCORRECT_FACT,
    "claim": HallucinationType.UNSUPPORTED_CLAIM,
    "default": HallucinationType.OTHER,
}


def get_hallucination_type(item_type: str) -> HallucinationType:
    """Convert analysis audit item type to HallucinationType enum."""
    item_lower = item_type.lower()
    return ITEM_TYPE_TO_HALLUCINATION_TYPE.get(item_lower, HallucinationType.OTHER)


def get_hallucination_severity(action_taken: str, confidence_change: float = 0) -> HallucinationSeverity:
    """Determine severity based on action taken and impact."""
    if action_taken == "removed":
        return HallucinationSeverity.HIGH
    elif action_taken == "corrected":
        if abs(confidence_change) > 20:
            return HallucinationSeverity.HIGH
        elif abs(confidence_change) > 10:
            return HallucinationSeverity.MEDIUM
        else:
            return HallucinationSeverity.LOW
    return HallucinationSeverity.MEDIUM


def get_correction_action(action_taken: str) -> CorrectionAction:
    """Convert action taken string to CorrectionAction enum."""
    action_map = {
        "removed": CorrectionAction.REMOVED,
        "corrected": CorrectionAction.CORRECTED,
        "flagged": CorrectionAction.FLAGGED,
        "restored_as_false_positive": CorrectionAction.VERIFIED_ACCURATE,
    }
    return action_map.get(action_taken.lower(), CorrectionAction.FLAGGED)


def get_model_provider(model_name: str) -> AIModelProvider:
    """Determine model provider from model name."""
    model_lower = model_name.lower()
    if "claude" in model_lower or "opus" in model_lower or "sonnet" in model_lower or "anthropic" in model_lower:
        return AIModelProvider.ANTHROPIC
    elif "gpt" in model_lower or "openai" in model_lower:
        return AIModelProvider.OPENAI
    elif "local" in model_lower:
        return AIModelProvider.LOCAL
    return AIModelProvider.HYBRID


async def persist_analysis_audit(
    db: AsyncSession,
    audit_trail: AnalysisAuditTrail,
    user_id: Optional[int],
    document_id: Optional[int],
    document_name: str,
    model_provider: str,
    model_name: str,
    raw_response: str,
    processed_response: Optional[Dict] = None,
    document_content: Optional[str] = None,
    analysis_type: str = "multi_layer_analysis",
    user_email: Optional[str] = None,
    session_id: Optional[str] = None,
    source_ip: Optional[str] = None,
) -> Optional[str]:
    """
    Persist an AnalysisAuditTrail to the database.

    This function:
    1. Creates an AIResponseLog entry with full context
    2. Creates HallucinationAudit entries for each detected hallucination
    3. Returns the AI response request_id for reference

    Args:
        db: Database session
        audit_trail: The AnalysisAuditTrail from multi_layer_analyzer
        user_id: User who requested the analysis
        document_id: ID of the analyzed document
        document_name: Name of the document
        model_provider: AI provider (openai, anthropic)
        model_name: Specific model used
        raw_response: The raw AI response
        processed_response: The structured/processed response
        document_content: The document text (for hashing)
        analysis_type: Type of analysis performed
        user_email: User's email
        session_id: Session identifier
        source_ip: Client IP address

    Returns:
        The request_id of the AI response log entry, or None on failure
    """
    try:
        audit_service = ComprehensiveAuditService(db)

        # Determine processing time
        processing_time_ms = None
        if audit_trail.completed_at and audit_trail.started_at:
            processing_time_ms = int(
                (audit_trail.completed_at - audit_trail.started_at).total_seconds() * 1000
            )

        # Get confidence scores
        confidence_score = audit_trail.final_confidence / 100.0 if audit_trail.final_confidence else None

        # Determine analysis type enum
        analysis_type_enum = AIAnalysisType.MULTI_LAYER_ANALYSIS
        if "summary" in analysis_type.lower():
            analysis_type_enum = AIAnalysisType.DOCUMENT_SUMMARY
        elif "extraction" in analysis_type.lower():
            analysis_type_enum = AIAnalysisType.DOCUMENT_EXTRACTION

        # Log the AI response
        request_id = await audit_service.log_ai_response(
            user_id=user_id,
            user_email=user_email,
            session_id=session_id,
            source_ip=source_ip,
            document_id=document_id,
            document_name=document_name,
            document_content=document_content,
            analysis_type=analysis_type_enum,
            model_provider=get_model_provider(model_provider),
            model_name=model_name,
            raw_response=raw_response or "",
            processed_response=processed_response,
            confidence_score=confidence_score,
            hallucination_count=audit_trail.total_hallucinations_detected,
            correction_count=audit_trail.total_corrections_applied,
            processing_time_ms=processing_time_ms,
            success=True,
            post_processing_applied=[
                {"stage": s.stage_name, "model": s.model_used}
                for s in audit_trail.stage_snapshots
            ],
            final_output=processed_response,
        )

        if not request_id:
            logger.error("Failed to create AI response log entry")
            return None

        # Log each hallucination
        for i, hall in enumerate(audit_trail.hallucinations):
            hallucination_type = get_hallucination_type(hall.item_type)

            # Calculate confidence change if available
            confidence_change = 0
            if hall.confidence_before is not None and hall.confidence_after is not None:
                confidence_change = hall.confidence_after - hall.confidence_before

            severity = get_hallucination_severity(hall.action_taken, confidence_change)
            correction_action = get_correction_action(hall.action_taken)

            await audit_service.log_hallucination(
                ai_response_id=request_id,
                hallucination_type=hallucination_type,
                severity=severity,
                field_name=hall.item_type,
                original_value=hall.original_value,
                corrected_value=hall.corrected_value,
                detection_method=hall.detection_method,
                detection_layer=hall.detected_at_stage,
                detection_confidence=0.9,  # Default high confidence for our detectors
                detection_reasoning=hall.reason_flagged,
                correction_action=correction_action,
                correction_source=hall.correction_source,
                correction_reasoning=f"Detected via {hall.detection_method}: {hall.reason_flagged}",
                sequence_number=i + 1,
                cross_validation_performed=hall.verified_in_document,
            )

        logger.info(
            f"Persisted analysis audit: request_id={request_id}, "
            f"hallucinations={audit_trail.total_hallucinations_detected}, "
            f"corrections={audit_trail.total_corrections_applied}"
        )

        return request_id

    except Exception as e:
        logger.error(f"Failed to persist analysis audit: {e}")
        import traceback
        traceback.print_exc()
        return None


async def log_document_access_event(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    document_id: int,
    document_name: str,
    access_type: str,
    source_ip: str,
    user_role: Optional[str] = None,
    session_id: Optional[str] = None,
    document_type: Optional[str] = None,
    case_id: Optional[int] = None,
    case_name: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
) -> Optional[str]:
    """
    Log a document access event.

    Args:
        db: Database session
        user_id: ID of user accessing document
        user_email: Email of user
        document_id: ID of document being accessed
        document_name: Name of document
        access_type: Type of access (view, download, analyze, etc.)
        source_ip: Client IP address
        user_role: Role of the user
        session_id: Session identifier
        document_type: Type of document
        case_id: Related case ID
        case_name: Related case name
        user_agent: Browser/client user agent
        success: Whether access was successful

    Returns:
        The access_id or None on failure
    """
    try:
        audit_service = ComprehensiveAuditService(db)

        # Map access type string to enum
        access_type_map = {
            "view": DocumentAccessType.VIEW,
            "download": DocumentAccessType.DOWNLOAD,
            "print": DocumentAccessType.PRINT,
            "share": DocumentAccessType.SHARE,
            "export": DocumentAccessType.EXPORT,
            "analyze": DocumentAccessType.ANALYZE,
            "edit": DocumentAccessType.EDIT,
            "delete": DocumentAccessType.DELETE,
            "restore": DocumentAccessType.RESTORE,
        }
        access_type_enum = access_type_map.get(access_type.lower(), DocumentAccessType.VIEW)

        return await audit_service.log_document_access(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            session_id=session_id,
            document_id=document_id,
            document_name=document_name,
            document_type=document_type,
            access_type=access_type_enum,
            source_ip=source_ip,
            user_agent=user_agent,
            case_id=case_id,
            case_name=case_name,
            success=success,
        )

    except Exception as e:
        logger.error(f"Failed to log document access: {e}")
        return None


async def log_admin_action_event(
    db: AsyncSession,
    admin_id: int,
    admin_email: str,
    admin_role: str,
    action_type: str,
    action_description: str,
    reason: str,
    target_type: str,
    source_ip: str,
    target_id: Optional[str] = None,
    target_name: Optional[str] = None,
    before_state: Optional[Dict] = None,
    after_state: Optional[Dict] = None,
    success: bool = True,
) -> Optional[str]:
    """
    Log an admin action event.

    Args:
        db: Database session
        admin_id: ID of admin performing action
        admin_email: Email of admin
        admin_role: Role of admin
        action_type: Type of action (from AdminActionType)
        action_description: Description of what was done
        reason: REQUIRED - justification for the action
        target_type: Type of target (user, document, config, etc.)
        source_ip: Client IP address
        target_id: ID of target
        target_name: Name of target
        before_state: State before action
        after_state: State after action
        success: Whether action was successful

    Returns:
        The action_id or None on failure
    """
    try:
        from app.models.comprehensive_audit import AdminActionType

        audit_service = ComprehensiveAuditService(db)

        # Map action type string to enum
        action_type_map = {
            "user_create": AdminActionType.USER_CREATE,
            "user_update": AdminActionType.USER_UPDATE,
            "user_delete": AdminActionType.USER_DELETE,
            "user_suspend": AdminActionType.USER_SUSPEND,
            "user_restore": AdminActionType.USER_RESTORE,
            "user_impersonate": AdminActionType.USER_IMPERSONATE,
            "role_assign": AdminActionType.ROLE_ASSIGN,
            "role_revoke": AdminActionType.ROLE_REVOKE,
            "config_change": AdminActionType.CONFIG_CHANGE,
            "data_export": AdminActionType.DATA_EXPORT,
            "data_delete": AdminActionType.DATA_DELETE,
            "credits_adjust": AdminActionType.CREDITS_ADJUST,
            "refund_issue": AdminActionType.REFUND_ISSUE,
        }
        action_type_enum = action_type_map.get(
            action_type.lower(),
            AdminActionType.CONFIG_CHANGE
        )

        return await audit_service.log_admin_action(
            admin_id=admin_id,
            admin_email=admin_email,
            admin_role=admin_role,
            action_type=action_type_enum,
            action_description=action_description,
            reason=reason,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            before_state=before_state,
            after_state=after_state,
            source_ip=source_ip,
            success=success,
        )

    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")
        return None


async def log_search_event(
    db: AsyncSession,
    query_text: str,
    query_type: str,
    results_count: int,
    user_id: Optional[int] = None,
    source_ip: Optional[str] = None,
    search_filters: Optional[Dict] = None,
    search_time_ms: Optional[int] = None,
) -> Optional[str]:
    """
    Log a search query event.

    Args:
        db: Database session
        query_text: The search query
        query_type: Type of search (case_search, document_search, etc.)
        results_count: Number of results returned
        user_id: ID of user searching
        source_ip: Client IP address
        search_filters: Applied filters
        search_time_ms: Time taken to search

    Returns:
        The query_id or None on failure
    """
    try:
        audit_service = ComprehensiveAuditService(db)

        return await audit_service.log_search_query(
            query_text=query_text,
            query_type=query_type,
            results_count=results_count,
            user_id=user_id,
            source_ip=source_ip,
            search_filters=search_filters,
            search_time_ms=search_time_ms,
        )

    except Exception as e:
        logger.error(f"Failed to log search: {e}")
        return None


# Convenience class for use in request context
class AuditLogger:
    """
    Convenience class for logging audit events within a request context.

    Usage:
        audit = AuditLogger(db, user_id, user_email, source_ip)
        await audit.log_document_view(doc_id, doc_name)
        await audit.log_admin_action("user_update", "Updated user profile", "Fixing typo")
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        source_ip: Optional[str] = None,
        session_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ):
        self.db = db
        self.user_id = user_id
        self.user_email = user_email
        self.source_ip = source_ip or "0.0.0.0"
        self.session_id = session_id
        self.user_role = user_role
        self.service = ComprehensiveAuditService(db)

    async def log_document_view(
        self,
        document_id: int,
        document_name: str,
        **kwargs
    ) -> Optional[str]:
        return await log_document_access_event(
            db=self.db,
            user_id=self.user_id,
            user_email=self.user_email,
            document_id=document_id,
            document_name=document_name,
            access_type="view",
            source_ip=self.source_ip,
            user_role=self.user_role,
            session_id=self.session_id,
            **kwargs
        )

    async def log_document_download(
        self,
        document_id: int,
        document_name: str,
        **kwargs
    ) -> Optional[str]:
        return await log_document_access_event(
            db=self.db,
            user_id=self.user_id,
            user_email=self.user_email,
            document_id=document_id,
            document_name=document_name,
            access_type="download",
            source_ip=self.source_ip,
            user_role=self.user_role,
            session_id=self.session_id,
            **kwargs
        )

    async def log_document_analyze(
        self,
        document_id: int,
        document_name: str,
        **kwargs
    ) -> Optional[str]:
        return await log_document_access_event(
            db=self.db,
            user_id=self.user_id,
            user_email=self.user_email,
            document_id=document_id,
            document_name=document_name,
            access_type="analyze",
            source_ip=self.source_ip,
            user_role=self.user_role,
            session_id=self.session_id,
            **kwargs
        )

    async def log_admin_action(
        self,
        action_type: str,
        action_description: str,
        reason: str,
        target_type: str,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        return await log_admin_action_event(
            db=self.db,
            admin_id=self.user_id,
            admin_email=self.user_email,
            admin_role=self.user_role or "admin",
            action_type=action_type,
            action_description=action_description,
            reason=reason,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            source_ip=self.source_ip,
            **kwargs
        )

    async def log_search(
        self,
        query_text: str,
        query_type: str,
        results_count: int,
        **kwargs
    ) -> Optional[str]:
        return await log_search_event(
            db=self.db,
            query_text=query_text,
            query_type=query_type,
            results_count=results_count,
            user_id=self.user_id,
            source_ip=self.source_ip,
            **kwargs
        )
