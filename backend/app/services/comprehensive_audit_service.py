"""
Comprehensive Audit Service for Legal AI System

This service provides centralized audit logging for:
- AI responses and analysis
- Hallucination detection and correction
- Document access tracking
- Admin actions
- Search queries
- API usage
- Error logging

All audit methods are designed to:
1. Never throw exceptions (logging failures shouldn't break the app)
2. Be async-friendly for performance
3. Include full context for dispute resolution
4. Support legal compliance requirements
"""

import asyncio
import enum
import hashlib
import json
import logging
import traceback
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

# Import models
try:
    from app.models.comprehensive_audit import (
        AIResponseLog, HallucinationAudit, DocumentAccessLog,
        AdminActionLog, SearchQueryLog, APIUsageLog,
        UserSessionActivity, ErrorLog,
        AIModelProvider, AIAnalysisType, HallucinationType,
        HallucinationSeverity, CorrectionAction, DocumentAccessType,
        AdminActionType
    )
except ImportError:
    from backend.app.models.comprehensive_audit import (
        AIResponseLog, HallucinationAudit, DocumentAccessLog,
        AdminActionLog, SearchQueryLog, APIUsageLog,
        UserSessionActivity, ErrorLog,
        AIModelProvider, AIAnalysisType, HallucinationType,
        HallucinationSeverity, CorrectionAction, DocumentAccessType,
        AdminActionType
    )

logger = logging.getLogger(__name__)


class ComprehensiveAuditService:
    """
    Centralized service for all audit logging operations.

    Usage:
        audit_service = ComprehensiveAuditService(db_session)

        # Log an AI response
        await audit_service.log_ai_response(
            user_id=123,
            document_id=456,
            analysis_type=AIAnalysisType.DOCUMENT_SUMMARY,
            model_provider=AIModelProvider.OPENAI,
            model_name="gpt-4",
            input_text="Document content...",
            raw_response="AI response...",
            processed_response={"summary": "..."}
        )

        # Log a hallucination
        await audit_service.log_hallucination(
            ai_response_id=response_id,
            hallucination_type=HallucinationType.FABRICATED_PARTY,
            severity=HallucinationSeverity.HIGH,
            field_name="parties[0].name",
            original_value="John Doe",
            corrected_value="Jane Smith",
            detection_method="cross_validation",
            detection_layer="verification_layer",
            correction_action=CorrectionAction.CORRECTED
        )
    """

    def __init__(self, db: Union[Session, AsyncSession]):
        self.db = db
        self._is_async = hasattr(db, 'execute') and asyncio.iscoroutinefunction(getattr(db, 'execute', None))

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique ID for audit records."""
        return str(uuid.uuid4()).replace('-', '')[:32]

    @staticmethod
    def _safe_json(data: Any) -> Any:
        """Safely convert data to JSON-serializable format."""
        if data is None:
            return None

        def convert(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, bytes):
                return obj.decode('utf-8', errors='replace')
            elif hasattr(obj, '__dict__'):
                return {k: convert(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert(v) for v in obj]
            return obj

        try:
            return convert(data)
        except Exception:
            return str(data)

    @staticmethod
    def _truncate_text(text: Optional[str], max_length: int = 50000) -> Optional[str]:
        """Truncate text to avoid database limits."""
        if text is None:
            return None
        if len(text) > max_length:
            return text[:max_length] + f"\n... [TRUNCATED - {len(text) - max_length} chars remaining]"
        return text

    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    # =========================================================================
    # AI RESPONSE LOGGING
    # =========================================================================

    async def log_ai_response(
        self,
        user_id: Optional[int],
        analysis_type: AIAnalysisType,
        model_provider: AIModelProvider,
        model_name: str,
        raw_response: str,
        document_id: Optional[int] = None,
        document_name: Optional[str] = None,
        document_type: Optional[str] = None,
        document_content: Optional[str] = None,
        input_text: Optional[str] = None,
        prompt_template: Optional[str] = None,
        input_parameters: Optional[Dict] = None,
        processed_response: Optional[Dict] = None,
        final_output: Optional[Dict] = None,
        post_processing_applied: Optional[List] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        confidence_score: Optional[float] = None,
        quality_score: Optional[float] = None,
        hallucination_count: int = 0,
        correction_count: int = 0,
        estimated_cost: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        user_email: Optional[str] = None,
        session_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log an AI response with full context.

        Returns the request_id for linking hallucination audits.
        """
        try:
            request_id = self._generate_id()

            log_entry = AIResponseLog(
                request_id=request_id,
                correlation_id=correlation_id,
                user_id=user_id,
                user_email=user_email,
                session_id=session_id,
                source_ip=source_ip,
                document_id=document_id,
                document_name=document_name,
                document_type=document_type,
                document_hash=self._hash_content(document_content) if document_content else None,
                analysis_type=analysis_type,
                model_provider=model_provider,
                model_name=model_name,
                prompt_template=self._truncate_text(prompt_template, 10000),
                input_text=self._truncate_text(input_text),
                input_tokens=input_tokens,
                input_parameters=self._safe_json(input_parameters),
                raw_response=self._truncate_text(raw_response),
                processed_response=self._safe_json(processed_response),
                output_tokens=output_tokens,
                confidence_score=confidence_score,
                quality_score=quality_score,
                hallucination_count=hallucination_count,
                correction_count=correction_count,
                post_processing_applied=self._safe_json(post_processing_applied),
                final_output=self._safe_json(final_output),
                estimated_cost=Decimal(str(estimated_cost)) if estimated_cost else None,
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message,
                request_timestamp=datetime.now(timezone.utc),
                response_timestamp=datetime.now(timezone.utc) if success else None,
            )

            self.db.add(log_entry)
            await self._commit()

            logger.debug(f"Logged AI response: {request_id}")
            return request_id

        except Exception as e:
            logger.error(f"Failed to log AI response: {e}")
            await self._rollback()
            return None

    # =========================================================================
    # HALLUCINATION LOGGING
    # =========================================================================

    async def log_hallucination(
        self,
        ai_response_id: str,
        hallucination_type: HallucinationType,
        severity: HallucinationSeverity,
        field_name: str,
        original_value: Any,
        detection_method: str,
        detection_layer: str,
        correction_action: CorrectionAction,
        corrected_value: Any = None,
        field_path: Optional[str] = None,
        section: Optional[str] = None,
        source_layer: Optional[str] = None,
        source_prompt_excerpt: Optional[str] = None,
        source_document_excerpt: Optional[str] = None,
        detection_rule: Optional[str] = None,
        detection_confidence: float = 1.0,
        detection_reasoning: Optional[str] = None,
        cross_validation_performed: bool = False,
        cross_validation_sources: Optional[List] = None,
        cross_validation_results: Optional[Dict] = None,
        correction_source: Optional[str] = None,
        correction_reasoning: Optional[str] = None,
        impact_assessment: Optional[str] = None,
        affected_downstream: Optional[List] = None,
        sequence_number: int = 1,
    ) -> Optional[str]:
        """
        Log a hallucination with complete before/after context.

        This provides the detailed audit trail showing:
        - What was wrong (original_value)
        - Where it was wrong (field_name, field_path)
        - How we detected it (detection_method, detection_layer, detection_reasoning)
        - What we did about it (correction_action, corrected_value)
        - Why we made that correction (correction_reasoning)
        """
        try:
            hallucination_id = self._generate_id()

            # Look up the AI response to get its UUID
            ai_response = None
            if ai_response_id:
                try:
                    result = await self._execute_query(
                        select(AIResponseLog).where(AIResponseLog.request_id == ai_response_id)
                    )
                    ai_response = result.scalar_one_or_none() if result else None
                except Exception:
                    pass

            log_entry = HallucinationAudit(
                hallucination_id=hallucination_id,
                ai_response_id=ai_response.id if ai_response else None,
                sequence_number=sequence_number,
                hallucination_type=hallucination_type,
                severity=severity,
                field_name=field_name,
                field_path=field_path,
                section=section,
                original_value=self._safe_json(original_value),
                original_text=str(original_value) if original_value else None,
                source_layer=source_layer or detection_layer,
                source_prompt_excerpt=self._truncate_text(source_prompt_excerpt, 2000),
                source_document_excerpt=self._truncate_text(source_document_excerpt, 2000),
                detection_method=detection_method,
                detection_layer=detection_layer,
                detection_rule=detection_rule,
                detection_confidence=detection_confidence,
                detection_reasoning=detection_reasoning,
                cross_validation_performed=cross_validation_performed,
                cross_validation_sources=self._safe_json(cross_validation_sources),
                cross_validation_results=self._safe_json(cross_validation_results),
                correction_action=correction_action,
                corrected_value=self._safe_json(corrected_value),
                corrected_text=str(corrected_value) if corrected_value else None,
                correction_source=correction_source,
                correction_reasoning=correction_reasoning,
                impact_assessment=impact_assessment,
                affected_downstream=self._safe_json(affected_downstream),
                detected_at=datetime.now(timezone.utc),
                corrected_at=datetime.now(timezone.utc) if correction_action != CorrectionAction.FLAGGED else None,
            )

            self.db.add(log_entry)
            await self._commit()

            logger.debug(f"Logged hallucination: {hallucination_id} - {field_name}")
            return hallucination_id

        except Exception as e:
            logger.error(f"Failed to log hallucination: {e}")
            await self._rollback()
            return None

    async def log_hallucination_batch(
        self,
        ai_response_id: str,
        hallucinations: List[Dict]
    ) -> List[Optional[str]]:
        """
        Log multiple hallucinations for a single AI response.

        Each hallucination dict should contain the same parameters as log_hallucination.
        """
        results = []
        for i, h in enumerate(hallucinations):
            h['sequence_number'] = i + 1
            result = await self.log_hallucination(ai_response_id=ai_response_id, **h)
            results.append(result)
        return results

    # =========================================================================
    # DOCUMENT ACCESS LOGGING
    # =========================================================================

    async def log_document_access(
        self,
        user_id: int,
        user_email: str,
        document_id: int,
        document_name: str,
        access_type: DocumentAccessType,
        source_ip: str,
        user_role: Optional[str] = None,
        session_id: Optional[str] = None,
        document_type: Optional[str] = None,
        document_hash: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        access_method: Optional[str] = None,
        access_reason: Optional[str] = None,
        case_id: Optional[int] = None,
        case_name: Optional[str] = None,
        matter_id: Optional[str] = None,
        client_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        shared_with: Optional[List] = None,
        export_format: Optional[str] = None,
        modification_type: Optional[str] = None,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None,
        duration_seconds: Optional[int] = None,
        success: bool = True,
        bytes_transferred: Optional[int] = None,
        pages_viewed: Optional[int] = None,
    ) -> Optional[str]:
        """Log document access for compliance tracking."""
        try:
            access_id = self._generate_id()

            log_entry = DocumentAccessLog(
                access_id=access_id,
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                session_id=session_id,
                document_id=document_id,
                document_name=document_name,
                document_type=document_type,
                document_hash=document_hash,
                file_size_bytes=file_size_bytes,
                access_type=access_type,
                access_method=access_method,
                access_reason=access_reason,
                case_id=case_id,
                case_name=case_name,
                matter_id=matter_id,
                client_id=client_id,
                source_ip=source_ip,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                api_endpoint=api_endpoint,
                shared_with=self._safe_json(shared_with),
                export_format=export_format,
                modification_type=modification_type,
                before_state=self._safe_json(before_state),
                after_state=self._safe_json(after_state),
                duration_seconds=duration_seconds,
                success=success,
                bytes_transferred=bytes_transferred,
                pages_viewed=pages_viewed,
                accessed_at=datetime.now(timezone.utc),
            )

            self.db.add(log_entry)
            await self._commit()

            logger.debug(f"Logged document access: {access_id}")
            return access_id

        except Exception as e:
            logger.error(f"Failed to log document access: {e}")
            await self._rollback()
            return None

    # =========================================================================
    # ADMIN ACTION LOGGING
    # =========================================================================

    async def log_admin_action(
        self,
        admin_id: int,
        admin_email: str,
        admin_role: str,
        action_type: AdminActionType,
        action_description: str,
        reason: str,
        target_type: str,
        source_ip: str,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None,
        changes_made: Optional[Dict] = None,
        ticket_number: Optional[str] = None,
        authorization_reference: Optional[str] = None,
        requires_approval: bool = False,
        approved_by: Optional[int] = None,
        approval_notes: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        reversible: bool = True,
    ) -> Optional[str]:
        """
        Log an admin action with full justification.

        IMPORTANT: The 'reason' field is REQUIRED and must explain why the action was taken.
        """
        try:
            action_id = self._generate_id()

            log_entry = AdminActionLog(
                action_id=action_id,
                admin_id=admin_id,
                admin_email=admin_email,
                admin_role=admin_role,
                action_type=action_type,
                action_description=action_description,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                before_state=self._safe_json(before_state),
                after_state=self._safe_json(after_state),
                changes_made=self._safe_json(changes_made),
                reason=reason,
                ticket_number=ticket_number,
                authorization_reference=authorization_reference,
                requires_approval=requires_approval,
                approved_by=approved_by,
                approved_at=datetime.now(timezone.utc) if approved_by else None,
                approval_notes=approval_notes,
                source_ip=source_ip,
                user_agent=user_agent,
                session_id=session_id,
                success=success,
                error_message=error_message,
                reversible=reversible,
                performed_at=datetime.now(timezone.utc),
            )

            self.db.add(log_entry)
            await self._commit()

            logger.info(f"Admin action logged: {action_type.value} by {admin_email} - {reason}")
            return action_id

        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
            await self._rollback()
            return None

    # =========================================================================
    # SEARCH QUERY LOGGING
    # =========================================================================

    async def log_search_query(
        self,
        query_text: str,
        query_type: str,
        results_count: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        search_filters: Optional[Dict] = None,
        search_parameters: Optional[Dict] = None,
        results_returned: Optional[int] = None,
        top_result_ids: Optional[List] = None,
        search_time_ms: Optional[int] = None,
    ) -> Optional[str]:
        """Log a search query for analytics."""
        try:
            query_id = self._generate_id()

            log_entry = SearchQueryLog(
                query_id=query_id,
                user_id=user_id,
                session_id=session_id,
                source_ip=source_ip,
                query_text=self._truncate_text(query_text, 2000),
                query_type=query_type,
                search_filters=self._safe_json(search_filters),
                search_parameters=self._safe_json(search_parameters),
                results_count=results_count,
                results_returned=results_returned,
                top_result_ids=self._safe_json(top_result_ids),
                search_time_ms=search_time_ms,
                searched_at=datetime.now(timezone.utc),
            )

            self.db.add(log_entry)
            await self._commit()

            return query_id

        except Exception as e:
            logger.error(f"Failed to log search query: {e}")
            await self._rollback()
            return None

    async def log_search_click(
        self,
        query_id: str,
        clicked_result_id: str,
        clicked_position: int
    ) -> bool:
        """Update a search query with the result that was clicked."""
        try:
            result = await self._execute_query(
                select(SearchQueryLog).where(SearchQueryLog.query_id == query_id)
            )
            log_entry = result.scalar_one_or_none() if result else None

            if log_entry:
                log_entry.result_clicked = True
                log_entry.clicked_result_id = clicked_result_id
                log_entry.clicked_position = clicked_position
                await self._commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to log search click: {e}")
            await self._rollback()
            return False

    # =========================================================================
    # API USAGE LOGGING
    # =========================================================================

    async def log_api_usage(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        source_ip: str,
        user_id: Optional[int] = None,
        api_key_id: Optional[str] = None,
        path_params: Optional[Dict] = None,
        query_params: Optional[Dict] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        user_agent: Optional[str] = None,
        credits_used: Optional[float] = None,
        billing_category: Optional[str] = None,
    ) -> Optional[str]:
        """Log API usage for billing and analytics."""
        try:
            request_id = self._generate_id()

            log_entry = APIUsageLog(
                request_id=request_id,
                user_id=user_id,
                api_key_id=api_key_id,
                endpoint=endpoint,
                method=method,
                path_params=self._safe_json(path_params),
                query_params=self._safe_json(query_params),
                request_size_bytes=request_size_bytes,
                status_code=status_code,
                response_size_bytes=response_size_bytes,
                response_time_ms=response_time_ms,
                source_ip=source_ip,
                user_agent=user_agent,
                credits_used=Decimal(str(credits_used)) if credits_used else None,
                billing_category=billing_category,
                requested_at=datetime.now(timezone.utc),
            )

            self.db.add(log_entry)
            await self._commit()

            return request_id

        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
            await self._rollback()
            return None

    # =========================================================================
    # ERROR LOGGING
    # =========================================================================

    async def log_error(
        self,
        error_type: str,
        error_message: str,
        component: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_stack_trace: Optional[str] = None,
        module: Optional[str] = None,
        function_name: Optional[str] = None,
        line_number: Optional[int] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        request_data: Optional[Dict] = None,
        environment: Optional[str] = None,
        server_id: Optional[str] = None,
        version: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = 'error',
        affected_users: Optional[int] = None,
    ) -> Optional[str]:
        """Log an error with full context."""
        try:
            error_id = self._generate_id()

            log_entry = ErrorLog(
                error_id=error_id,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                error_type=error_type,
                error_code=error_code,
                error_message=self._truncate_text(error_message, 5000),
                error_stack_trace=self._truncate_text(error_stack_trace, 10000),
                component=component,
                module=module,
                function_name=function_name,
                line_number=line_number,
                endpoint=endpoint,
                method=method,
                request_data=self._safe_json(request_data),
                environment=environment,
                server_id=server_id,
                version=version,
                source_ip=source_ip,
                user_agent=user_agent,
                severity=severity,
                affected_users=affected_users,
                occurred_at=datetime.now(timezone.utc),
            )

            self.db.add(log_entry)
            await self._commit()

            return error_id

        except Exception as e:
            logger.error(f"Failed to log error: {e}")
            await self._rollback()
            return None

    async def log_exception(
        self,
        exception: Exception,
        component: str,
        **kwargs
    ) -> Optional[str]:
        """Convenience method to log an exception with automatic stack trace extraction."""
        return await self.log_error(
            error_type=type(exception).__name__,
            error_message=str(exception),
            error_stack_trace=traceback.format_exc(),
            component=component,
            **kwargs
        )

    # =========================================================================
    # SESSION ACTIVITY LOGGING
    # =========================================================================

    async def log_session_activity(
        self,
        session_id: str,
        user_id: int,
        activity_type: str,
        activity_name: str,
        activity_details: Optional[Dict] = None,
        page_path: Optional[str] = None,
        page_title: Optional[str] = None,
        referrer: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_type: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> bool:
        """Log user session activity."""
        try:
            log_entry = UserSessionActivity(
                session_id=session_id,
                user_id=user_id,
                activity_type=activity_type,
                activity_name=activity_name,
                activity_details=self._safe_json(activity_details),
                page_path=page_path,
                page_title=page_title,
                referrer=referrer,
                source_ip=source_ip,
                user_agent=user_agent,
                device_type=device_type,
                duration_seconds=duration_seconds,
                activity_at=datetime.now(timezone.utc),
            )

            self.db.add(log_entry)
            await self._commit()

            return True

        except Exception as e:
            logger.error(f"Failed to log session activity: {e}")
            await self._rollback()
            return False

    # =========================================================================
    # QUERY METHODS FOR ADMIN DASHBOARD
    # =========================================================================

    async def get_ai_responses(
        self,
        user_id: Optional[int] = None,
        document_id: Optional[int] = None,
        analysis_type: Optional[AIAnalysisType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """Get AI response logs with filtering."""
        try:
            query = select(AIResponseLog)

            conditions = []
            if user_id:
                conditions.append(AIResponseLog.user_id == user_id)
            if document_id:
                conditions.append(AIResponseLog.document_id == document_id)
            if analysis_type:
                conditions.append(AIResponseLog.analysis_type == analysis_type)
            if start_date:
                conditions.append(AIResponseLog.request_timestamp >= start_date)
            if end_date:
                conditions.append(AIResponseLog.request_timestamp <= end_date)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(AIResponseLog.request_timestamp)).limit(limit).offset(offset)

            result = await self._execute_query(query)
            rows = result.scalars().all() if result else []

            return [self._row_to_dict(r) for r in rows]

        except Exception as e:
            logger.error(f"Failed to get AI responses: {e}")
            return []

    async def get_hallucinations_for_response(self, ai_response_id: str) -> List[Dict]:
        """Get all hallucinations for a specific AI response."""
        try:
            # First get the AI response
            response_result = await self._execute_query(
                select(AIResponseLog).where(AIResponseLog.request_id == ai_response_id)
            )
            ai_response = response_result.scalar_one_or_none() if response_result else None

            if not ai_response:
                return []

            # Get hallucinations
            query = select(HallucinationAudit).where(
                HallucinationAudit.ai_response_id == ai_response.id
            ).order_by(HallucinationAudit.sequence_number)

            result = await self._execute_query(query)
            rows = result.scalars().all() if result else []

            return [self._row_to_dict(r) for r in rows]

        except Exception as e:
            logger.error(f"Failed to get hallucinations: {e}")
            return []

    async def get_hallucination_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """Get hallucination statistics for dashboard."""
        try:
            conditions = []
            if start_date:
                conditions.append(HallucinationAudit.detected_at >= start_date)
            if end_date:
                conditions.append(HallucinationAudit.detected_at <= end_date)

            base_query = select(HallucinationAudit)
            if conditions:
                base_query = base_query.where(and_(*conditions))

            result = await self._execute_query(base_query)
            rows = result.scalars().all() if result else []

            # Calculate stats
            stats = {
                'total_count': len(rows),
                'by_type': {},
                'by_severity': {},
                'by_action': {},
                'by_detection_method': {},
            }

            for row in rows:
                # By type
                type_name = row.hallucination_type.value if row.hallucination_type else 'unknown'
                stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1

                # By severity
                sev_name = row.severity.value if row.severity else 'unknown'
                stats['by_severity'][sev_name] = stats['by_severity'].get(sev_name, 0) + 1

                # By action
                action_name = row.correction_action.value if row.correction_action else 'unknown'
                stats['by_action'][action_name] = stats['by_action'].get(action_name, 0) + 1

                # By detection method
                method = row.detection_method or 'unknown'
                stats['by_detection_method'][method] = stats['by_detection_method'].get(method, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"Failed to get hallucination stats: {e}")
            return {'total_count': 0, 'by_type': {}, 'by_severity': {}, 'by_action': {}, 'by_detection_method': {}}

    async def get_document_access_log(
        self,
        user_id: Optional[int] = None,
        document_id: Optional[int] = None,
        access_type: Optional[DocumentAccessType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """Get document access logs."""
        try:
            query = select(DocumentAccessLog)

            conditions = []
            if user_id:
                conditions.append(DocumentAccessLog.user_id == user_id)
            if document_id:
                conditions.append(DocumentAccessLog.document_id == document_id)
            if access_type:
                conditions.append(DocumentAccessLog.access_type == access_type)
            if start_date:
                conditions.append(DocumentAccessLog.accessed_at >= start_date)
            if end_date:
                conditions.append(DocumentAccessLog.accessed_at <= end_date)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(DocumentAccessLog.accessed_at)).limit(limit).offset(offset)

            result = await self._execute_query(query)
            rows = result.scalars().all() if result else []

            return [self._row_to_dict(r) for r in rows]

        except Exception as e:
            logger.error(f"Failed to get document access log: {e}")
            return []

    async def get_admin_actions(
        self,
        admin_id: Optional[int] = None,
        action_type: Optional[AdminActionType] = None,
        target_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """Get admin action logs."""
        try:
            query = select(AdminActionLog)

            conditions = []
            if admin_id:
                conditions.append(AdminActionLog.admin_id == admin_id)
            if action_type:
                conditions.append(AdminActionLog.action_type == action_type)
            if target_type:
                conditions.append(AdminActionLog.target_type == target_type)
            if start_date:
                conditions.append(AdminActionLog.performed_at >= start_date)
            if end_date:
                conditions.append(AdminActionLog.performed_at <= end_date)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(AdminActionLog.performed_at)).limit(limit).offset(offset)

            result = await self._execute_query(query)
            rows = result.scalars().all() if result else []

            return [self._row_to_dict(r) for r in rows]

        except Exception as e:
            logger.error(f"Failed to get admin actions: {e}")
            return []

    async def get_recent_errors(
        self,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get recent error logs."""
        try:
            query = select(ErrorLog)

            conditions = []
            if severity:
                conditions.append(ErrorLog.severity == severity)
            if resolved is not None:
                conditions.append(ErrorLog.resolved == resolved)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(ErrorLog.occurred_at)).limit(limit)

            result = await self._execute_query(query)
            rows = result.scalars().all() if result else []

            return [self._row_to_dict(r) for r in rows]

        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _commit(self):
        """Commit the transaction, handling both sync and async sessions."""
        try:
            if self._is_async:
                await self.db.commit()
            else:
                self.db.commit()
        except Exception:
            await self._rollback()
            raise

    async def _rollback(self):
        """Rollback the transaction, handling both sync and async sessions."""
        try:
            if self._is_async:
                await self.db.rollback()
            else:
                self.db.rollback()
        except Exception:
            pass

    async def _execute_query(self, query):
        """Execute a query, handling both sync and async sessions."""
        try:
            if self._is_async:
                return await self.db.execute(query)
            else:
                return self.db.execute(query)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None

    def _row_to_dict(self, row) -> Dict:
        """Convert a SQLAlchemy row to a dictionary."""
        if row is None:
            return {}

        result = {}
        for column in row.__table__.columns:
            value = getattr(row, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, enum.Enum):
                value = value.value
            result[column.name] = value

        return result


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_audit_service(db: Union[Session, AsyncSession]) -> ComprehensiveAuditService:
    """Get an instance of the audit service."""
    return ComprehensiveAuditService(db)


# Singleton for sync operations (use with caution in async contexts)
_sync_audit_service: Optional[ComprehensiveAuditService] = None


def init_sync_audit_service(db: Session) -> ComprehensiveAuditService:
    """Initialize the global sync audit service."""
    global _sync_audit_service
    _sync_audit_service = ComprehensiveAuditService(db)
    return _sync_audit_service


def get_sync_audit_service() -> Optional[ComprehensiveAuditService]:
    """Get the global sync audit service."""
    return _sync_audit_service
