"""
Legal Analysis Integration Module
Bridges the legal filing analysis system with existing services

This module provides:
- Integration with document processing pipeline
- Integration with case tracking system
- Integration with AI services (Claude/OpenAI)
- Integration with notification system
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import date, datetime

from . import (
    LegalFilingAnalyzer,
    create_analyzer,
    FilingAnalysisResult,
    JurisdictionType,
    ServiceMethod,
    DeadlineCalculator,
    TemplateContext,
    SummaryRenderer,
    OutputFormat,
)

logger = logging.getLogger(__name__)


class LegalAnalysisIntegration:
    """
    Integration layer for legal analysis services

    Connects the legal filing analysis module with:
    - Document processing pipeline
    - Case management system
    - Notification services
    - AI services
    """

    def __init__(
        self,
        ai_service: Optional[Any] = None,
        db_session: Optional[Any] = None,
        notification_service: Optional[Any] = None
    ):
        """
        Initialize integration layer

        Args:
            ai_service: AI service for enhanced analysis (DualAIService)
            db_session: Database session for persistence
            notification_service: Email notification service
        """
        self.ai_service = ai_service
        self.db = db_session
        self.notification_service = notification_service
        self._analyzer = None

    def get_analyzer(
        self,
        jurisdiction: str = "federal",
        enable_ai: bool = True
    ) -> LegalFilingAnalyzer:
        """Get or create analyzer instance"""
        if not self._analyzer:
            self._analyzer = create_analyzer(
                ai_service=self.ai_service,
                jurisdiction=jurisdiction,
                enable_ai=enable_ai and self.ai_service is not None
            )
        return self._analyzer

    async def analyze_document(
        self,
        document_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        case_id: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a legal document and return structured results

        Args:
            document_text: Document text content
            metadata: Document metadata (filing_date, case_number, etc.)
            user_id: User ID for tracking
            case_id: Case ID if associated with a case
            options: Analysis options

        Returns:
            Dictionary with analysis results
        """
        options = options or {}
        metadata = metadata or {}

        try:
            analyzer = self.get_analyzer(
                jurisdiction=options.get('jurisdiction', 'federal'),
                enable_ai=options.get('enable_ai', True)
            )

            # Perform analysis
            result = await analyzer.analyze(
                document_text=document_text,
                metadata=metadata,
                options=options
            )

            # Optionally persist results
            if self.db and user_id:
                await self._persist_analysis(result, user_id, case_id)

            # Send notifications for urgent filings
            if self.notification_service and result.risk.urgency_level.value in ['high', 'critical']:
                await self._send_urgency_notification(result, user_id)

            return {
                'success': True,
                'analysis': result.to_dict(),
                'analysis_id': result.analysis_id
            }

        except Exception as e:
            logger.error(f"Document analysis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    async def analyze_for_defense_flow(
        self,
        document_text: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Analyze document for defense flow integration

        This provides enhanced document analysis for the interview/defense
        building flow by pre-classifying the document and extracting
        relevant information.

        Args:
            document_text: Document text content
            session_id: Session ID for tracking

        Returns:
            Dictionary with classification and key information
        """
        try:
            analyzer = self.get_analyzer(enable_ai=False)  # Fast analysis

            # Get classification
            classification = analyzer.classify_only(document_text)

            # Get extraction
            extraction = analyzer.extract_only(document_text)

            # Determine case type based on classification
            case_type = self._determine_case_type(classification, extraction)

            return {
                'success': True,
                'filing_type': classification.filing_type_name,
                'category': classification.category_name,
                'case_type': case_type,
                'parties': extraction.parties,
                'has_deadline': len(extraction.dates) > 0,
                'confidence': classification.confidence,
                'practice_areas': classification.practice_areas
            }

        except Exception as e:
            logger.error(f"Defense flow analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'case_type': 'unknown'
            }

    def _determine_case_type(
        self,
        classification: Any,
        extraction: Any
    ) -> str:
        """Determine case type from classification and extraction"""
        # Map practice areas to case types
        practice_area_mapping = {
            'civil_litigation': 'civil',
            'contract': 'contract',
            'employment': 'employment',
            'personal_injury': 'personal_injury',
            'debt_collection': 'debt_collection',
            'landlord_tenant': 'landlord_tenant',
            'family_law': 'family',
            'criminal': 'criminal',
            'bankruptcy': 'bankruptcy',
        }

        for area in classification.practice_areas:
            if area.lower() in practice_area_mapping:
                return practice_area_mapping[area.lower()]

        # Default based on category
        category_mapping = {
            'A': 'civil',
            'B': 'civil',
            'C': 'civil',
            'D': 'civil',
            'E': 'civil',
            'M': 'bankruptcy',
            'P': 'appeal',
        }

        return category_mapping.get(classification.category, 'civil')

    async def get_deadlines_for_case(
        self,
        case_id: int,
        filing_type: str,
        filing_date: date,
        jurisdiction: str = "federal"
    ) -> List[Dict[str, Any]]:
        """
        Calculate deadlines for a case based on filing type

        Args:
            case_id: Case ID
            filing_type: Filing type code
            filing_date: Date of filing
            jurisdiction: Jurisdiction string

        Returns:
            List of calculated deadlines
        """
        try:
            analyzer = self.get_analyzer(jurisdiction=jurisdiction)
            deadline_result = analyzer.calculate_deadlines_only(
                filing_type=filing_type,
                filing_date=filing_date,
                jurisdiction=self._map_jurisdiction(jurisdiction)
            )

            return deadline_result.deadlines

        except Exception as e:
            logger.error(f"Deadline calculation error: {e}")
            return []

    def _map_jurisdiction(self, jurisdiction: str) -> JurisdictionType:
        """Map jurisdiction string to enum"""
        mapping = {
            'federal': JurisdictionType.FEDERAL,
            'california': JurisdictionType.STATE_CA,
            'ca': JurisdictionType.STATE_CA,
            'new_york': JurisdictionType.STATE_NY,
            'ny': JurisdictionType.STATE_NY,
            'texas': JurisdictionType.STATE_TX,
            'tx': JurisdictionType.STATE_TX,
            'florida': JurisdictionType.STATE_FL,
            'fl': JurisdictionType.STATE_FL,
            'illinois': JurisdictionType.STATE_IL,
            'il': JurisdictionType.STATE_IL,
        }
        return mapping.get(jurisdiction.lower(), JurisdictionType.FEDERAL)

    async def _persist_analysis(
        self,
        result: FilingAnalysisResult,
        user_id: int,
        case_id: Optional[int] = None
    ):
        """Persist analysis results to database"""
        # This would save to a document_analyses table
        # Implementation depends on your database schema
        pass

    async def _send_urgency_notification(
        self,
        result: FilingAnalysisResult,
        user_id: int
    ):
        """Send notification for urgent filings"""
        if not self.notification_service:
            return

        try:
            # Create template context
            context = TemplateContext.from_analysis_result(result)

            # Get email content
            email_content = SummaryRenderer.render_email(context)

            # Send via notification service
            # Implementation depends on your notification service
            logger.info(f"Would send urgent notification to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to send urgency notification: {e}")

    async def generate_report(
        self,
        result: FilingAnalysisResult,
        output_format: str = "html"
    ) -> str:
        """
        Generate formatted report from analysis result

        Args:
            result: FilingAnalysisResult
            output_format: html, markdown, plain_text, pdf_ready

        Returns:
            Formatted report string
        """
        format_map = {
            'html': OutputFormat.HTML,
            'markdown': OutputFormat.MARKDOWN,
            'plain_text': OutputFormat.PLAIN_TEXT,
            'pdf_ready': OutputFormat.PDF_READY,
            'json': OutputFormat.JSON,
        }

        context = TemplateContext.from_analysis_result(result)
        return SummaryRenderer.render(
            context,
            format_map.get(output_format, OutputFormat.HTML)
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def quick_analyze(
    document_text: str,
    jurisdiction: str = "federal"
) -> Dict[str, Any]:
    """
    Quick analysis without full integration

    Args:
        document_text: Document text
        jurisdiction: Jurisdiction string

    Returns:
        Analysis results dictionary
    """
    integration = LegalAnalysisIntegration()
    return await integration.analyze_document(
        document_text=document_text,
        options={'jurisdiction': jurisdiction, 'enable_ai': False}
    )


async def get_filing_deadlines(
    filing_type: str,
    trigger_date: date,
    jurisdiction: str = "federal",
    service_method: str = "electronic"
) -> List[Dict[str, Any]]:
    """
    Quick deadline calculation

    Args:
        filing_type: Filing type code
        trigger_date: Trigger date
        jurisdiction: Jurisdiction string
        service_method: Service method string

    Returns:
        List of deadline dictionaries
    """
    from . import ResponseDeadlineCalculator

    jurisdiction_map = {
        'federal': JurisdictionType.FEDERAL,
        'california': JurisdictionType.STATE_CA,
        'new_york': JurisdictionType.STATE_NY,
        'texas': JurisdictionType.STATE_TX,
    }

    service_map = {
        'electronic': ServiceMethod.ELECTRONIC,
        'personal': ServiceMethod.PERSONAL,
        'mail': ServiceMethod.MAIL,
    }

    jurisdiction_type = jurisdiction_map.get(jurisdiction.lower(), JurisdictionType.FEDERAL)
    service_type = service_map.get(service_method.lower(), ServiceMethod.ELECTRONIC)

    deadlines = []

    if filing_type.upper().startswith('A'):
        deadline = ResponseDeadlineCalculator.calculate_answer_deadline(
            trigger_date, jurisdiction_type, waiver=False, service_method=service_type
        )
        if deadline:
            deadlines.append({
                'description': 'Answer Due',
                'date': deadline.adjusted_deadline.isoformat(),
                'rule': deadline.rule_applied
            })

    return deadlines


# =============================================================================
# AI SERVICE ADAPTER
# =============================================================================

class AIServiceAdapter:
    """
    Adapter to connect DualAIService with legal analysis module

    The legal analysis module expects an AI service with a specific interface.
    This adapter wraps the existing DualAIService to provide that interface.
    """

    def __init__(self, dual_ai_service: Any):
        """
        Initialize adapter

        Args:
            dual_ai_service: Instance of DualAIService
        """
        self.service = dual_ai_service

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate AI response using DualAIService

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Maximum tokens
            temperature: Temperature setting

        Returns:
            Response dictionary with 'content' key
        """
        try:
            # Use DualAIService's analyze_document method
            # This will use Claude or OpenAI based on availability
            response = await self.service.analyze_document(
                document_text=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )

            return {
                'content': response.get('analysis', response.get('content', '')),
                'model': response.get('model', 'unknown'),
                'usage': response.get('usage', {})
            }

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return {
                'content': '',
                'error': str(e)
            }


def create_integrated_analyzer(
    dual_ai_service: Optional[Any] = None,
    db_session: Optional[Any] = None,
    notification_service: Optional[Any] = None
) -> LegalAnalysisIntegration:
    """
    Factory function to create fully integrated analyzer

    Args:
        dual_ai_service: DualAIService instance
        db_session: Database session
        notification_service: Email notification service

    Returns:
        Configured LegalAnalysisIntegration instance
    """
    ai_adapter = AIServiceAdapter(dual_ai_service) if dual_ai_service else None

    return LegalAnalysisIntegration(
        ai_service=ai_adapter,
        db_session=db_session,
        notification_service=notification_service
    )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "LegalAnalysisIntegration",
    "AIServiceAdapter",
    "quick_analyze",
    "get_filing_deadlines",
    "create_integrated_analyzer",
]
