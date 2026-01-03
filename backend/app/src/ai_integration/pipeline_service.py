"""
Two-Stage AI Analysis Pipeline Service

Orchestrates analysis using OpenAI first, then Anthropic Claude for enhanced results.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .openai.service import get_openai_service
from .anthropic.service import get_anthropic_service

logger = logging.getLogger(__name__)


class AIAnalysisPipeline:
    """Two-stage AI analysis pipeline using OpenAI followed by Anthropic Claude."""
    
    def __init__(self):
        self.openai_service = get_openai_service()
        self.anthropic_service = get_anthropic_service()
    
    @property
    def service_status(self) -> Dict[str, Any]:
        """Get status of all AI services."""
        return {
            "openai": {
                "available": True,
                "has_real_key": self.openai_service.has_real_key,
                "service_type": "real" if self.openai_service.has_real_key else "mock"
            },
            "anthropic": {
                "available": True,
                "has_real_key": self.anthropic_service.has_real_key,
                "service_type": "real" if self.anthropic_service.has_real_key else "mock"
            },
            "pipeline_mode": self._get_pipeline_mode()
        }
    
    def _get_pipeline_mode(self) -> str:
        """Determine the pipeline mode based on available services."""
        openai_real = self.openai_service.has_real_key
        anthropic_real = self.anthropic_service.has_real_key
        
        if openai_real and anthropic_real:
            return "full_pipeline"
        elif openai_real and not anthropic_real:
            return "openai_only"
        elif not openai_real and anthropic_real:
            return "anthropic_only"
        else:
            return "mock_services"
    
    async def analyze_document(
        self, 
        document_text: str, 
        analysis_type: str = "general",
        use_cross_validation: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run complete two-stage analysis pipeline.
        
        Args:
            document_text: The document content to analyze
            analysis_type: Type of analysis (general, contract, brief, etc.)
            use_cross_validation: Whether to use Claude for cross-validation
            **kwargs: Additional parameters
            
        Returns:
            Complete analysis results from both stages
        """
        pipeline_start = datetime.utcnow()
        
        try:
            # Stage 1: OpenAI Analysis
            logger.info(f"Starting Stage 1: OpenAI analysis for {analysis_type}")
            openai_result = await self.openai_service.analyze_document(
                document_text=document_text,
                analysis_type=analysis_type,
                **kwargs
            )
            
            # Stage 2: Anthropic Enhancement/Cross-validation
            logger.info(f"Starting Stage 2: Anthropic enhancement for {analysis_type}")
            
            if use_cross_validation:
                # Use cross-validation mode
                anthropic_result = await self.anthropic_service.cross_validate_analysis(
                    document_text=document_text,
                    openai_analysis=openai_result,
                    **kwargs
                )
            else:
                # Use enhancement mode
                anthropic_result = await self.anthropic_service.analyze_document(
                    document_text=document_text,
                    analysis_type=analysis_type,
                    openai_analysis=openai_result,
                    **kwargs
                )
            
            # Combine results
            pipeline_end = datetime.utcnow()
            pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
            
            combined_result = {
                "pipeline_info": {
                    "version": "2.0",
                    "mode": "two_stage_analysis",
                    "cross_validation": use_cross_validation,
                    "duration_seconds": pipeline_duration,
                    "timestamp": pipeline_end.isoformat(),
                    "service_status": self.service_status
                },
                "document_info": {
                    "length": len(document_text),
                    "analysis_type": analysis_type
                },
                "stage_1": {
                    "provider": "openai",
                    "result": openai_result
                },
                "stage_2": {
                    "provider": "anthropic",
                    "result": anthropic_result
                },
                "combined_token_usage": self._calculate_combined_token_usage(openai_result, anthropic_result)
            }
            
            logger.info(f"Two-stage analysis completed in {pipeline_duration:.2f} seconds")
            return combined_result
            
        except Exception as e:
            logger.error(f"Two-stage analysis pipeline failed: {str(e)}")
            # Return partial results if available
            error_result = {
                "pipeline_info": {
                    "version": "2.0",
                    "mode": "two_stage_analysis_failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "service_status": self.service_status
                },
                "document_info": {
                    "length": len(document_text),
                    "analysis_type": analysis_type
                }
            }
            
            # Try to include any partial results
            try:
                if 'openai_result' in locals():
                    error_result["stage_1"] = {"provider": "openai", "result": openai_result}
            except:
                pass
            
            try:
                if 'anthropic_result' in locals():
                    error_result["stage_2"] = {"provider": "anthropic", "result": anthropic_result}
            except:
                pass
            
            return error_result
    
    async def summarize_document(
        self, 
        document_text: str, 
        max_length: int = 500,
        use_enhancement: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run complete two-stage summarization pipeline.
        
        Args:
            document_text: The document content to summarize
            max_length: Maximum length of summary
            use_enhancement: Whether to use Claude for enhancement
            **kwargs: Additional parameters
            
        Returns:
            Complete summarization results from both stages
        """
        pipeline_start = datetime.utcnow()
        
        try:
            # Stage 1: OpenAI Summarization
            logger.info("Starting Stage 1: OpenAI summarization")
            openai_result = await self.openai_service.summarize_document(
                document_text=document_text,
                max_length=max_length,
                **kwargs
            )
            
            # Stage 2: Anthropic Enhancement (if enabled)
            anthropic_result = None
            if use_enhancement:
                logger.info("Starting Stage 2: Anthropic enhancement")
                anthropic_result = await self.anthropic_service.summarize_document(
                    document_text=document_text,
                    max_length=max_length,
                    openai_summary=openai_result,
                    **kwargs
                )
            
            # Combine results
            pipeline_end = datetime.utcnow()
            pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
            
            combined_result = {
                "pipeline_info": {
                    "version": "2.0",
                    "mode": "two_stage_summarization",
                    "enhancement_enabled": use_enhancement,
                    "duration_seconds": pipeline_duration,
                    "timestamp": pipeline_end.isoformat(),
                    "service_status": self.service_status
                },
                "document_info": {
                    "length": len(document_text),
                    "max_summary_length": max_length
                },
                "stage_1": {
                    "provider": "openai",
                    "result": openai_result
                },
                "combined_token_usage": self._calculate_combined_token_usage(openai_result, anthropic_result)
            }
            
            if anthropic_result:
                combined_result["stage_2"] = {
                    "provider": "anthropic",
                    "result": anthropic_result
                }
            
            logger.info(f"Two-stage summarization completed in {pipeline_duration:.2f} seconds")
            return combined_result
            
        except Exception as e:
            logger.error(f"Two-stage summarization pipeline failed: {str(e)}")
            raise
    
    async def analyze_document_single_stage(
        self, 
        document_text: str, 
        provider: str,
        analysis_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run single-stage analysis using specified provider.
        
        Args:
            document_text: The document content to analyze
            provider: AI provider to use ("openai" or "anthropic")
            analysis_type: Type of analysis
            **kwargs: Additional parameters
            
        Returns:
            Single-stage analysis results
        """
        if provider.lower() == "openai":
            service = self.openai_service
        elif provider.lower() == "anthropic":
            service = self.anthropic_service
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        result = await service.analyze_document(
            document_text=document_text,
            analysis_type=analysis_type,
            **kwargs
        )
        
        return {
            "pipeline_info": {
                "version": "2.0",
                "mode": "single_stage_analysis",
                "provider": provider.lower(),
                "timestamp": datetime.utcnow().isoformat(),
                "service_status": self.service_status
            },
            "document_info": {
                "length": len(document_text),
                "analysis_type": analysis_type
            },
            "result": result
        }
    
    def _calculate_combined_token_usage(
        self, 
        openai_result: Optional[Dict[str, Any]], 
        anthropic_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate combined token usage from both services."""
        combined = {
            "total_tokens": 0,
            "openai_tokens": 0,
            "anthropic_tokens": 0,
            "breakdown": {}
        }
        
        if openai_result and "token_usage" in openai_result:
            openai_tokens = openai_result["token_usage"].get("total_tokens", 0)
            combined["openai_tokens"] = openai_tokens
            combined["total_tokens"] += openai_tokens
            combined["breakdown"]["openai"] = openai_result["token_usage"]
        
        if anthropic_result and "token_usage" in anthropic_result:
            anthropic_tokens = anthropic_result["token_usage"].get("total_tokens", 0)
            combined["anthropic_tokens"] = anthropic_tokens
            combined["total_tokens"] += anthropic_tokens
            combined["breakdown"]["anthropic"] = anthropic_result["token_usage"]
        
        return combined


# Global pipeline instance
_ai_pipeline: Optional[AIAnalysisPipeline] = None


def get_ai_pipeline() -> AIAnalysisPipeline:
    """Get or create AI analysis pipeline instance."""
    global _ai_pipeline
    if _ai_pipeline is None:
        _ai_pipeline = AIAnalysisPipeline()
    return _ai_pipeline