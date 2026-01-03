"""
OpenAI Integration Service for Legal AI System

Provides integration with OpenAI's GPT models for legal document analysis.
"""

import os
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime

import openai
from openai import AsyncOpenAI

from ...core.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI service for legal document analysis and AI operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[AsyncOpenAI] = None
        self._has_real_key: Optional[bool] = None
    
    @property
    def has_real_key(self) -> bool:
        """Check if we have a real API key (not mock)."""
        if self._has_real_key is None:
            api_key = os.getenv("OPENAI_API_KEY") or self.settings.OPENAI_API_KEY
            # Check if it's a real key (starts with sk- and has reasonable length)
            self._has_real_key = (
                api_key is not None 
                and api_key.startswith("sk-") 
                and len(api_key) > 20
                and not api_key.startswith("sk-mock")
            )
        return self._has_real_key
    
    @property
    def client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY") or self.settings.OPENAI_API_KEY
            
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            org_id = os.getenv("OPENAI_ORG_ID") or self.settings.OPENAI_ORG_ID
            
            self._client = AsyncOpenAI(
                api_key=api_key,
                organization=org_id
            )
            
            logger.info(f"OpenAI client initialized with real key: {self.has_real_key}")
        
        return self._client
    
    async def analyze_document(
        self, 
        document_text: str, 
        analysis_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze legal document using OpenAI.
        
        Args:
            document_text: The document content to analyze
            analysis_type: Type of analysis (general, contract, brief, etc.)
            **kwargs: Additional parameters
            
        Returns:
            Analysis results dictionary
        """
        if not self.has_real_key:
            logger.warning("Using mock OpenAI service - no real API key detected")
            return await self._mock_analyze_document(document_text, analysis_type, **kwargs)
        
        try:
            prompt = self._build_analysis_prompt(document_text, analysis_type, **kwargs)
            
            response = await self.client.chat.completions.create(
                model=self.settings.OPENAI_DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a legal AI assistant specialized in document analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.settings.OPENAI_MAX_TOKENS,
                temperature=self.settings.OPENAI_TEMPERATURE
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "provider": "openai",
                "model": self.settings.OPENAI_DEFAULT_MODEL,
                "analysis": analysis,
                "analysis_type": analysis_type,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "timestamp": datetime.utcnow().isoformat(),
                "has_real_key": True
            }
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            raise
    
    async def summarize_document(
        self, 
        document_text: str, 
        max_length: int = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Summarize legal document using OpenAI.
        
        Args:
            document_text: The document content to summarize
            max_length: Maximum length of summary
            **kwargs: Additional parameters
            
        Returns:
            Summary results dictionary
        """
        if not self.has_real_key:
            logger.warning("Using mock OpenAI service - no real API key detected")
            return await self._mock_summarize_document(document_text, max_length, **kwargs)
        
        try:
            prompt = f"""
            Please provide a concise legal summary of the following document in approximately {max_length} characters:
            
            {document_text[:8000]}  # Limit input to avoid token limits
            
            Focus on:
            1. Document type and purpose
            2. Key parties involved
            3. Main terms and conditions
            4. Important dates and deadlines
            5. Potential risks or issues
            """
            
            response = await self.client.chat.completions.create(
                model=self.settings.OPENAI_DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a legal AI assistant specialized in document summarization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=min(self.settings.OPENAI_MAX_TOKENS, max_length // 3),  # Rough token estimation
                temperature=0.1  # Lower temperature for summaries
            )
            
            summary = response.choices[0].message.content
            
            return {
                "provider": "openai",
                "model": self.settings.OPENAI_DEFAULT_MODEL,
                "summary": summary,
                "max_length": max_length,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "timestamp": datetime.utcnow().isoformat(),
                "has_real_key": True
            }
            
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {str(e)}")
            raise
    
    def _build_analysis_prompt(self, document_text: str, analysis_type: str, **kwargs) -> str:
        """Build analysis prompt based on type."""
        base_prompt = f"Please analyze the following legal document:\n\n{document_text[:8000]}\n\n"
        
        if analysis_type == "contract":
            return base_prompt + """
            Provide a detailed contract analysis focusing on:
            1. Contract type and parties
            2. Key terms and obligations
            3. Payment terms and conditions
            4. Termination clauses
            5. Risk assessment and potential issues
            6. Compliance requirements
            """
        elif analysis_type == "brief":
            return base_prompt + """
            Provide a legal brief analysis focusing on:
            1. Legal issues presented
            2. Arguments and counterarguments
            3. Relevant case law and precedents
            4. Strength of legal position
            5. Potential outcomes
            """
        elif analysis_type == "compliance":
            return base_prompt + """
            Provide a compliance analysis focusing on:
            1. Regulatory requirements
            2. Compliance gaps or issues
            3. Risk assessment
            4. Recommended actions
            """
        else:
            return base_prompt + """
            Provide a general legal document analysis focusing on:
            1. Document type and purpose
            2. Key legal concepts
            3. Important clauses or sections
            4. Potential legal implications
            5. Recommended review points
            """
    
    async def _mock_analyze_document(self, document_text: str, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Mock analysis for when no real API key is available."""
        return {
            "provider": "openai",
            "model": "mock",
            "analysis": f"Mock analysis of {analysis_type} document. This is a placeholder response generated without using the OpenAI API. The document appears to be approximately {len(document_text)} characters long.",
            "analysis_type": analysis_type,
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "timestamp": datetime.utcnow().isoformat(),
            "has_real_key": False
        }
    
    async def _mock_summarize_document(self, document_text: str, max_length: int, **kwargs) -> Dict[str, Any]:
        """Mock summary for when no real API key is available."""
        return {
            "provider": "openai",
            "model": "mock",
            "summary": f"Mock summary of document ({len(document_text)} characters). This is a placeholder response generated without using the OpenAI API.",
            "max_length": max_length,
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "timestamp": datetime.utcnow().isoformat(),
            "has_real_key": False
        }


# Global service instance
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """Get or create OpenAI service instance."""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service