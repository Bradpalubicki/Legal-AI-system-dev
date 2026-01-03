"""
Anthropic Claude Integration Service for Legal AI System

Provides integration with Anthropic's Claude models for legal document analysis.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import anthropic
from anthropic import AsyncAnthropic

from ...core.config import get_settings

logger = logging.getLogger(__name__)


class AnthropicService:
    """Anthropic Claude service for legal document analysis and AI operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[AsyncAnthropic] = None
        self._has_real_key: Optional[bool] = None
    
    @property
    def has_real_key(self) -> bool:
        """Check if we have a real API key (not mock)."""
        if self._has_real_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY") or self.settings.ANTHROPIC_API_KEY
            # Check if it's a real key (starts with sk-ant- and has reasonable length)
            self._has_real_key = (
                api_key is not None 
                and api_key.startswith("sk-ant-") 
                and len(api_key) > 30
                and not api_key.startswith("sk-ant-mock")
            )
        return self._has_real_key
    
    @property
    def client(self) -> AsyncAnthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY") or self.settings.ANTHROPIC_API_KEY
            
            if not api_key:
                raise ValueError("Anthropic API key not configured")
            
            self._client = AsyncAnthropic(api_key=api_key)
            
            logger.info(f"Anthropic client initialized with real key: {self.has_real_key}")
        
        return self._client
    
    async def analyze_document(
        self, 
        document_text: str, 
        analysis_type: str = "general",
        openai_analysis: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze legal document using Anthropic Claude.
        
        Args:
            document_text: The document content to analyze
            analysis_type: Type of analysis (general, contract, brief, etc.)
            openai_analysis: Previous OpenAI analysis to build upon
            **kwargs: Additional parameters
            
        Returns:
            Analysis results dictionary
        """
        if not self.has_real_key:
            logger.warning("Using mock Anthropic service - no real API key detected")
            return await self._mock_analyze_document(document_text, analysis_type, openai_analysis, **kwargs)
        
        try:
            prompt = self._build_analysis_prompt(document_text, analysis_type, openai_analysis, **kwargs)
            
            response = await self.client.messages.create(
                model=self.settings.ANTHROPIC_DEFAULT_MODEL,
                max_tokens=self.settings.ANTHROPIC_MAX_TOKENS,
                temperature=self.settings.ANTHROPIC_TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis = response.content[0].text
            
            return {
                "provider": "anthropic",
                "model": self.settings.ANTHROPIC_DEFAULT_MODEL,
                "analysis": analysis,
                "analysis_type": analysis_type,
                "builds_on_openai": openai_analysis is not None,
                "token_usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "timestamp": datetime.utcnow().isoformat(),
                "has_real_key": True
            }
            
        except Exception as e:
            logger.error(f"Anthropic analysis failed: {str(e)}")
            raise
    
    async def cross_validate_analysis(
        self, 
        document_text: str, 
        openai_analysis: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cross-validate OpenAI analysis using Claude.
        
        Args:
            document_text: The original document content
            openai_analysis: The OpenAI analysis to validate
            **kwargs: Additional parameters
            
        Returns:
            Cross-validation results
        """
        if not self.has_real_key:
            logger.warning("Using mock Anthropic service - no real API key detected")
            return await self._mock_cross_validate_analysis(document_text, openai_analysis, **kwargs)
        
        try:
            prompt = f"""
            Please review and cross-validate the following AI analysis of a legal document.

            ORIGINAL DOCUMENT:
            {document_text[:6000]}

            PREVIOUS AI ANALYSIS (from OpenAI):
            {openai_analysis.get('analysis', 'No analysis provided')}

            Please provide:
            1. Points of agreement with the previous analysis
            2. Points of disagreement or alternative interpretations
            3. Additional insights not covered in the previous analysis
            4. Overall assessment of the analysis quality and accuracy
            5. Any corrections or clarifications needed

            Focus on providing a thorough, independent legal perspective that enhances the overall analysis.
            """
            
            response = await self.client.messages.create(
                model=self.settings.ANTHROPIC_DEFAULT_MODEL,
                max_tokens=self.settings.ANTHROPIC_MAX_TOKENS,
                temperature=0.2,  # Lower temperature for validation tasks
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            validation = response.content[0].text
            
            return {
                "provider": "anthropic",
                "model": self.settings.ANTHROPIC_DEFAULT_MODEL,
                "validation": validation,
                "original_provider": openai_analysis.get('provider', 'unknown'),
                "original_model": openai_analysis.get('model', 'unknown'),
                "token_usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "timestamp": datetime.utcnow().isoformat(),
                "has_real_key": True
            }
            
        except Exception as e:
            logger.error(f"Anthropic cross-validation failed: {str(e)}")
            raise
    
    async def summarize_document(
        self, 
        document_text: str, 
        max_length: int = 500,
        openai_summary: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Summarize legal document using Anthropic Claude.
        
        Args:
            document_text: The document content to summarize
            max_length: Maximum length of summary
            openai_summary: Previous OpenAI summary to build upon
            **kwargs: Additional parameters
            
        Returns:
            Summary results dictionary
        """
        if not self.has_real_key:
            logger.warning("Using mock Anthropic service - no real API key detected")
            return await self._mock_summarize_document(document_text, max_length, openai_summary, **kwargs)
        
        try:
            if openai_summary:
                prompt = f"""
                Please provide an enhanced legal summary building upon the previous AI summary.

                ORIGINAL DOCUMENT:
                {document_text[:6000]}

                PREVIOUS SUMMARY (from OpenAI):
                {openai_summary.get('summary', 'No summary provided')}

                Please provide a comprehensive summary (approximately {max_length} characters) that:
                1. Builds upon the previous summary
                2. Adds any missing critical information
                3. Provides alternative perspectives where relevant
                4. Ensures accuracy and completeness
                """
            else:
                prompt = f"""
                Please provide a concise legal summary of the following document in approximately {max_length} characters:
                
                {document_text[:8000]}
                
                Focus on:
                1. Document type and purpose
                2. Key parties involved
                3. Main terms and conditions
                4. Important dates and deadlines
                5. Potential risks or issues
                6. Critical legal implications
                """
            
            response = await self.client.messages.create(
                model=self.settings.ANTHROPIC_DEFAULT_MODEL,
                max_tokens=min(self.settings.ANTHROPIC_MAX_TOKENS, max_length // 2),
                temperature=0.1,  # Lower temperature for summaries
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            summary = response.content[0].text
            
            return {
                "provider": "anthropic",
                "model": self.settings.ANTHROPIC_DEFAULT_MODEL,
                "summary": summary,
                "max_length": max_length,
                "builds_on_openai": openai_summary is not None,
                "token_usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "timestamp": datetime.utcnow().isoformat(),
                "has_real_key": True
            }
            
        except Exception as e:
            logger.error(f"Anthropic summarization failed: {str(e)}")
            raise
    
    def _build_analysis_prompt(
        self, 
        document_text: str, 
        analysis_type: str, 
        openai_analysis: Optional[Dict[str, Any]], 
        **kwargs
    ) -> str:
        """Build analysis prompt based on type and previous analysis."""
        
        if openai_analysis:
            base_prompt = f"""
            Please provide an enhanced legal analysis building upon a previous AI analysis.

            ORIGINAL DOCUMENT:
            {document_text[:6000]}

            PREVIOUS ANALYSIS (from OpenAI):
            {openai_analysis.get('analysis', 'No analysis provided')}

            Please provide a comprehensive analysis that builds upon and enhances the previous analysis with additional insights and perspectives.
            """
        else:
            base_prompt = f"Please analyze the following legal document:\n\n{document_text[:8000]}\n\n"
        
        if analysis_type == "contract":
            return base_prompt + """
            Provide a detailed contract analysis focusing on:
            1. Contract type, structure, and parties
            2. Key terms, obligations, and performance requirements
            3. Payment terms, pricing, and financial implications
            4. Termination, renewal, and exit clauses
            5. Risk assessment and potential legal issues
            6. Compliance requirements and regulatory considerations
            7. Dispute resolution mechanisms
            """
        elif analysis_type == "brief":
            return base_prompt + """
            Provide a legal brief analysis focusing on:
            1. Legal issues and questions presented
            2. Arguments, counterarguments, and legal theories
            3. Relevant case law, precedents, and statutory authority
            4. Strength of legal position and likelihood of success
            5. Potential outcomes and strategic considerations
            6. Procedural requirements and deadlines
            """
        elif analysis_type == "compliance":
            return base_prompt + """
            Provide a compliance analysis focusing on:
            1. Applicable regulatory frameworks and requirements
            2. Compliance gaps, violations, or areas of concern
            3. Risk assessment and potential consequences
            4. Recommended corrective actions and timelines
            5. Monitoring and ongoing compliance strategies
            """
        else:
            return base_prompt + """
            Provide a comprehensive legal document analysis focusing on:
            1. Document type, purpose, and legal context
            2. Key legal concepts and implications
            3. Important clauses, terms, and conditions
            4. Potential legal risks and opportunities
            5. Recommended review points and next steps
            6. Strategic considerations and alternatives
            """
    
    async def _mock_analyze_document(
        self, 
        document_text: str, 
        analysis_type: str, 
        openai_analysis: Optional[Dict[str, Any]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Mock analysis for when no real API key is available."""
        build_text = " (building on OpenAI analysis)" if openai_analysis else ""
        return {
            "provider": "anthropic",
            "model": "mock",
            "analysis": f"Mock Anthropic analysis of {analysis_type} document{build_text}. This is a placeholder response generated without using the Anthropic API. The document appears to be approximately {len(document_text)} characters long.",
            "analysis_type": analysis_type,
            "builds_on_openai": openai_analysis is not None,
            "token_usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            },
            "timestamp": datetime.utcnow().isoformat(),
            "has_real_key": False
        }
    
    async def _mock_cross_validate_analysis(
        self, 
        document_text: str, 
        openai_analysis: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """Mock cross-validation for when no real API key is available."""
        return {
            "provider": "anthropic",
            "model": "mock",
            "validation": "Mock cross-validation response. This is a placeholder generated without using the Anthropic API.",
            "original_provider": openai_analysis.get('provider', 'unknown'),
            "original_model": openai_analysis.get('model', 'unknown'),
            "token_usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            },
            "timestamp": datetime.utcnow().isoformat(),
            "has_real_key": False
        }
    
    async def _mock_summarize_document(
        self, 
        document_text: str, 
        max_length: int, 
        openai_summary: Optional[Dict[str, Any]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Mock summary for when no real API key is available."""
        build_text = " (enhancing OpenAI summary)" if openai_summary else ""
        return {
            "provider": "anthropic",
            "model": "mock",
            "summary": f"Mock Anthropic summary of document{build_text} ({len(document_text)} characters). This is a placeholder response generated without using the Anthropic API.",
            "max_length": max_length,
            "builds_on_openai": openai_summary is not None,
            "token_usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            },
            "timestamp": datetime.utcnow().isoformat(),
            "has_real_key": False
        }


# Global service instance
_anthropic_service: Optional[AnthropicService] = None


def get_anthropic_service() -> AnthropicService:
    """Get or create Anthropic service instance."""
    global _anthropic_service
    if _anthropic_service is None:
        _anthropic_service = AnthropicService()
    return _anthropic_service