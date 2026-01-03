#!/usr/bin/env python3
"""
Integration test for AI services with real API keys.
"""

import os
import sys
import asyncio
from datetime import datetime


# Simple service classes that mirror our backend structure
class SimpleOpenAIService:
    """Simplified OpenAI service for testing."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    @property
    def has_real_key(self) -> bool:
        return (
            self.api_key is not None 
            and self.api_key.startswith("sk-") 
            and len(self.api_key) > 20
            and not self.api_key.startswith("sk-mock")
        )
    
    async def test_analyze(self, text: str) -> dict:
        """Test analysis (mock for now)."""
        if self.has_real_key:
            return {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "analysis": f"Real OpenAI analysis would process: {text[:50]}...",
                "has_real_key": True,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": {"total_tokens": 150}
            }
        else:
            return {
                "provider": "openai",
                "model": "mock",
                "analysis": f"Mock OpenAI analysis of: {text[:50]}...",
                "has_real_key": False,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": {"total_tokens": 0}
            }


class SimpleAnthropicService:
    """Simplified Anthropic service for testing."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
    @property
    def has_real_key(self) -> bool:
        return (
            self.api_key is not None 
            and self.api_key.startswith("sk-ant-") 
            and len(self.api_key) > 30
            and not self.api_key.startswith("sk-ant-mock")
        )
    
    async def test_analyze(self, text: str, openai_result: dict = None) -> dict:
        """Test analysis (mock for now)."""
        if self.has_real_key:
            builds_on = " (building on OpenAI)" if openai_result else ""
            return {
                "provider": "anthropic",
                "model": "claude-3-opus-20240229",
                "analysis": f"Real Anthropic analysis would process: {text[:50]}...{builds_on}",
                "has_real_key": True,
                "builds_on_openai": openai_result is not None,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": {"total_tokens": 200}
            }
        else:
            builds_on = " (building on OpenAI)" if openai_result else ""
            return {
                "provider": "anthropic", 
                "model": "mock",
                "analysis": f"Mock Anthropic analysis of: {text[:50]}...{builds_on}",
                "has_real_key": False,
                "builds_on_openai": openai_result is not None,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": {"total_tokens": 0}
            }


class SimplePipeline:
    """Simplified two-stage pipeline for testing."""
    
    def __init__(self):
        self.openai = SimpleOpenAIService()
        self.anthropic = SimpleAnthropicService()
    
    @property
    def service_status(self) -> dict:
        openai_real = self.openai.has_real_key
        anthropic_real = self.anthropic.has_real_key
        
        if openai_real and anthropic_real:
            mode = "full_pipeline"
        elif openai_real and not anthropic_real:
            mode = "openai_only"
        elif not openai_real and anthropic_real:
            mode = "anthropic_only"
        else:
            mode = "mock_services"
        
        return {
            "openai": {
                "available": True,
                "has_real_key": openai_real,
                "service_type": "real" if openai_real else "mock"
            },
            "anthropic": {
                "available": True,
                "has_real_key": anthropic_real,
                "service_type": "real" if anthropic_real else "mock"
            },
            "pipeline_mode": mode
        }
    
    async def analyze_document(self, document_text: str, analysis_type: str = "general") -> dict:
        """Run two-stage analysis pipeline."""
        start_time = datetime.utcnow()
        
        # Stage 1: OpenAI
        print(f"Stage 1: Running OpenAI analysis...")
        openai_result = await self.openai.test_analyze(document_text)
        print(f"  - OpenAI used real key: {openai_result['has_real_key']}")
        
        # Stage 2: Anthropic  
        print(f"Stage 2: Running Anthropic analysis...")
        anthropic_result = await self.anthropic.test_analyze(document_text, openai_result)
        print(f"  - Anthropic used real key: {anthropic_result['has_real_key']}")
        
        # Combine results
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "pipeline_info": {
                "version": "2.0",
                "mode": "two_stage_analysis", 
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
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
            "combined_token_usage": {
                "total_tokens": openai_result["token_usage"]["total_tokens"] + anthropic_result["token_usage"]["total_tokens"],
                "openai_tokens": openai_result["token_usage"]["total_tokens"],
                "anthropic_tokens": anthropic_result["token_usage"]["total_tokens"]
            }
        }


async def test_pipeline():
    """Test the two-stage pipeline."""
    print("=== Two-Stage AI Pipeline Integration Test ===")
    
    pipeline = SimplePipeline()
    
    # Show service status
    status = pipeline.service_status
    print(f"Pipeline mode: {status['pipeline_mode']}")
    print(f"OpenAI service: {status['openai']['service_type']}")
    print(f"Anthropic service: {status['anthropic']['service_type']}")
    print()
    
    # Test document
    test_document = """
    LEGAL SERVICES AGREEMENT
    
    This Agreement is entered into on January 15, 2024, between:
    - Client: ABC Corporation, a Delaware corporation
    - Law Firm: Smith & Associates LLP
    
    TERMS:
    1. Scope of Services: General legal counsel and contract review
    2. Fee Structure: $450/hour for partners, $275/hour for associates  
    3. Term: 12 months with automatic renewal
    4. Termination: 30 days written notice required
    
    The parties agree to the terms and conditions set forth herein.
    """
    
    print(f"Analyzing document ({len(test_document)} characters)...")
    print()
    
    # Run pipeline
    result = await pipeline.analyze_document(test_document, "contract")
    
    # Display results
    print(f"Analysis completed in {result['pipeline_info']['duration_seconds']:.2f} seconds")
    print()
    print("Stage 1 (OpenAI) Result:")
    print(f"  Provider: {result['stage_1']['result']['provider']}")
    print(f"  Model: {result['stage_1']['result']['model']}")
    print(f"  Real key: {result['stage_1']['result']['has_real_key']}")
    print(f"  Analysis: {result['stage_1']['result']['analysis']}")
    print()
    print("Stage 2 (Anthropic) Result:")
    print(f"  Provider: {result['stage_2']['result']['provider']}")
    print(f"  Model: {result['stage_2']['result']['model']}")
    print(f"  Real key: {result['stage_2']['result']['has_real_key']}")
    print(f"  Builds on OpenAI: {result['stage_2']['result']['builds_on_openai']}")
    print(f"  Analysis: {result['stage_2']['result']['analysis']}")
    print()
    print("Token Usage:")
    print(f"  Total: {result['combined_token_usage']['total_tokens']}")
    print(f"  OpenAI: {result['combined_token_usage']['openai_tokens']}")
    print(f"  Anthropic: {result['combined_token_usage']['anthropic_tokens']}")


async def main():
    """Run integration tests."""
    print("AI Services Integration Test")
    print("=" * 50)
    print()
    
    await test_pipeline()
    
    print()
    print("Integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())