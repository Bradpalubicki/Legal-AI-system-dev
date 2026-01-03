#!/usr/bin/env python3
"""
Test script to verify environment variable reading and AI service configuration.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend to Python path
backend_path = Path(__file__).parent / "backend" / "app" / "src"
sys.path.insert(0, str(backend_path))

try:
    # Import directly from config.py to avoid circular import
    sys.path.insert(0, str(backend_path / "core"))
    from config import get_settings
    from ai_integration import get_ai_pipeline, get_openai_service, get_anthropic_service
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from the project root directory")
    sys.exit(1)


def test_environment_variables():
    """Test reading API keys from environment variables."""
    print("=== Environment Variables Test ===")
    
    # Check OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY present: {openai_key is not None}")
    if openai_key:
        print(f"OPENAI_API_KEY starts with: {openai_key[:10]}...")
        print(f"OPENAI_API_KEY length: {len(openai_key)}")
    
    # Check Anthropic key  
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"ANTHROPIC_API_KEY present: {anthropic_key is not None}")
    if anthropic_key:
        print(f"ANTHROPIC_API_KEY starts with: {anthropic_key[:15]}...")
        print(f"ANTHROPIC_API_KEY length: {len(anthropic_key)}")
    
    print()


def test_settings_config():
    """Test settings configuration."""
    print("=== Settings Configuration Test ===")
    
    try:
        settings = get_settings()
        print(f"Settings loaded successfully")
        print(f"App name: {settings.APP_NAME}")
        print(f"Environment: {settings.ENVIRONMENT}")
        print(f"OpenAI key configured: {settings.OPENAI_API_KEY is not None}")
        print(f"Anthropic key configured: {settings.ANTHROPIC_API_KEY is not None}")
        print(f"OpenAI model: {settings.OPENAI_DEFAULT_MODEL}")
        print(f"Anthropic model: {settings.ANTHROPIC_DEFAULT_MODEL}")
    except Exception as e:
        print(f"Settings error: {e}")
    
    print()


def test_service_detection():
    """Test AI service key detection."""
    print("=== AI Service Detection Test ===")
    
    try:
        # Test OpenAI service
        openai_service = get_openai_service()
        print(f"OpenAI service has real key: {openai_service.has_real_key}")
        
        # Test Anthropic service
        anthropic_service = get_anthropic_service()
        print(f"Anthropic service has real key: {anthropic_service.has_real_key}")
        
        # Test pipeline status
        pipeline = get_ai_pipeline()
        status = pipeline.service_status
        print(f"Pipeline mode: {status['pipeline_mode']}")
        print(f"OpenAI service type: {status['openai']['service_type']}")
        print(f"Anthropic service type: {status['anthropic']['service_type']}")
        
    except Exception as e:
        print(f"Service detection error: {e}")
    
    print()


async def test_mock_analysis():
    """Test mock analysis functionality."""
    print("=== Mock Analysis Test ===")
    
    try:
        pipeline = get_ai_pipeline()
        
        # Test document text
        test_document = """
        This is a sample legal document for testing purposes.
        It contains various clauses and legal language that would
        typically be found in a contract or agreement.
        
        Parties: Company A and Company B
        Effective Date: January 1, 2024
        Term: 12 months
        
        The parties agree to the following terms and conditions...
        """
        
        # Test analysis
        result = await pipeline.analyze_document(
            document_text=test_document,
            analysis_type="contract",
            use_cross_validation=True
        )
        
        print(f"Analysis completed successfully!")
        print(f"Pipeline mode: {result['pipeline_info']['mode']}")
        print(f"Duration: {result['pipeline_info']['duration_seconds']:.2f} seconds")
        print(f"Stage 1 provider: {result['stage_1']['provider']}")
        print(f"Stage 1 has real key: {result['stage_1']['result']['has_real_key']}")
        
        if 'stage_2' in result:
            print(f"Stage 2 provider: {result['stage_2']['provider']}")
            print(f"Stage 2 has real key: {result['stage_2']['result']['has_real_key']}")
        
        print(f"Total tokens used: {result['combined_token_usage']['total_tokens']}")
        
    except Exception as e:
        print(f"Mock analysis error: {e}")
    
    print()


async def test_real_analysis():
    """Test real analysis if API keys are available."""
    print("=== Real Analysis Test (if keys available) ===")
    
    try:
        pipeline = get_ai_pipeline()
        status = pipeline.service_status
        
        if status['pipeline_mode'] == 'mock_services':
            print("No real API keys detected - skipping real analysis test")
            return
        
        # Simple test document
        test_document = "This is a basic contract between Party A and Party B for testing purposes."
        
        # Test analysis with real services
        result = await pipeline.analyze_document(
            document_text=test_document,
            analysis_type="general",
            use_cross_validation=False  # Start simple
        )
        
        print(f"Real analysis completed successfully!")
        print(f"Pipeline mode: {result['pipeline_info']['mode']}")
        print(f"Stage 1 analysis preview: {result['stage_1']['result']['analysis'][:100]}...")
        
        if 'stage_2' in result and result['stage_2']['result']['has_real_key']:
            print(f"Stage 2 analysis preview: {result['stage_2']['result']['analysis'][:100]}...")
        
    except Exception as e:
        print(f"Real analysis error: {e}")
    
    print()


async def main():
    """Run all tests."""
    print("Starting AI Service Environment Variable Tests")
    print("=" * 50)
    
    test_environment_variables()
    test_settings_config()
    test_service_detection()
    await test_mock_analysis()
    await test_real_analysis()
    
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())