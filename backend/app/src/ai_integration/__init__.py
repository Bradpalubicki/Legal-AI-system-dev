"""
AI Integration Module for Legal AI System

Provides unified access to AI services including OpenAI, Anthropic Claude,
and the two-stage analysis pipeline.
"""

from .openai.service import get_openai_service, OpenAIService
from .anthropic.service import get_anthropic_service, AnthropicService
from .pipeline_service import get_ai_pipeline, AIAnalysisPipeline

__all__ = [
    "get_openai_service",
    "OpenAIService",
    "get_anthropic_service", 
    "AnthropicService",
    "get_ai_pipeline",
    "AIAnalysisPipeline"
]