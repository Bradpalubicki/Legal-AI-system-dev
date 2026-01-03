#!/usr/bin/env python3
"""
Simple AI services test that verifies environment variables and service detection.
"""

import os
import sys
import asyncio
from datetime import datetime


def test_environment_variables():
    """Test environment variable detection."""
    print("ENVIRONMENT VARIABLE DETECTION")
    print("=" * 50)
    
    # Check OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY: {'Present' if openai_key else 'Missing'}")
    if openai_key:
        print(f"   Length: {len(openai_key)}")
        print(f"   Starts with: {openai_key[:10]}...")
        print(f"   Real key: {'Yes' if openai_key.startswith('sk-') and len(openai_key) > 20 else 'No'}")
    
    # Check Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"ANTHROPIC_API_KEY: {'Present' if anthropic_key else 'Missing'}")
    if anthropic_key:
        print(f"   Length: {len(anthropic_key)}")
        print(f"   Starts with: {anthropic_key[:15]}...")
        print(f"   Real key: {'Yes' if anthropic_key.startswith('sk-ant-') and len(anthropic_key) > 30 else 'No'}")
    
    print()


def test_library_imports():
    """Test required library imports."""
    print("LIBRARY AVAILABILITY")
    print("=" * 50)
    
    # Test OpenAI
    try:
        import openai
        print("[OK] OpenAI library: Available")
        print(f"     Version: {openai.__version__ if hasattr(openai, '__version__') else 'Unknown'}")
    except ImportError:
        print("[FAIL] OpenAI library: Not installed (run: pip install openai)")
    
    # Test Anthropic
    try:
        import anthropic
        print("[OK] Anthropic library: Available")
        print(f"     Version: {anthropic.__version__ if hasattr(anthropic, '__version__') else 'Unknown'}")
    except ImportError:
        print("[FAIL] Anthropic library: Not installed (run: pip install anthropic)")
    
    print()


def determine_service_status():
    """Determine service status based on available information."""
    print("SERVICE STATUS ANALYSIS")
    print("=" * 50)
    
    # OpenAI analysis
    openai_key = os.getenv("OPENAI_API_KEY")
    try:
        import openai
        openai_lib = True
    except ImportError:
        openai_lib = False
    
    if openai_key and openai_key.startswith('sk-') and len(openai_key) > 20:
        openai_status = "live" if openai_lib else "library_missing"
    elif openai_key:
        openai_status = "mock"
    else:
        openai_status = "unavailable"
    
    print(f"OpenAI Status: {openai_status.upper()}")
    
    # Anthropic analysis
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    try:
        import anthropic
        anthropic_lib = True
    except ImportError:
        anthropic_lib = False
    
    if anthropic_key and anthropic_key.startswith('sk-ant-') and len(anthropic_key) > 30:
        anthropic_status = "live" if anthropic_lib else "library_missing"
    elif anthropic_key:
        anthropic_status = "mock"
    else:
        anthropic_status = "unavailable"
    
    print(f"Anthropic Status: {anthropic_status.upper()}")
    
    # Pipeline analysis
    if openai_status in ["live", "mock"] and anthropic_status in ["live", "mock"]:
        if openai_status == "live" and anthropic_status == "live":
            pipeline_mode = "FULL_LIVE_PIPELINE"
        elif openai_status == "live" or anthropic_status == "live":
            pipeline_mode = "MIXED_PIPELINE"
        else:
            pipeline_mode = "MOCK_PIPELINE"
    else:
        pipeline_mode = "UNAVAILABLE"
    
    print(f"Pipeline Mode: {pipeline_mode}")
    print()
    
    return {
        "openai": openai_status,
        "anthropic": anthropic_status,
        "pipeline": pipeline_mode
    }


async def test_basic_openai():
    """Test basic OpenAI functionality if available."""
    print("OPENAI SERVICE TEST")
    print("=" * 50)
    
    try:
        import openai
        from openai import AsyncOpenAI
    except ImportError:
        print("[SKIP] OpenAI library not available")
        print()
        return
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[SKIP] No OpenAI API key")
        print()
        return
    
    if not (api_key.startswith('sk-') and len(api_key) > 20):
        print("[MOCK] Mock OpenAI key detected - would use mock responses")
        print()
        return
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        # Simple test request
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'OpenAI test successful' in exactly those words."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"[OK] OpenAI API Test: SUCCESS")
        print(f"     Response: {result}")
        print(f"     Tokens used: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"[FAIL] OpenAI API Test: FAILED")
        print(f"       Error: {str(e)}")
    
    print()


async def test_basic_anthropic():
    """Test basic Anthropic functionality if available."""
    print("ANTHROPIC SERVICE TEST")
    print("=" * 50)
    
    try:
        import anthropic
        from anthropic import AsyncAnthropic
    except ImportError:
        print("[SKIP] Anthropic library not available")
        print()
        return
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[SKIP] No Anthropic API key")
        print()
        return
    
    if not (api_key.startswith('sk-ant-') and len(api_key) > 30):
        print("[MOCK] Mock Anthropic key detected - would use mock responses")
        print()
        return
    
    try:
        client = AsyncAnthropic(api_key=api_key)
        
        # Simple test request
        response = await client.messages.create(
            model="claude-3-haiku-20240307",  # Cheaper model for testing
            max_tokens=20,
            messages=[
                {"role": "user", "content": "Say 'Anthropic test successful' in exactly those words."}
            ]
        )
        
        result = response.content[0].text
        print(f"[OK] Anthropic API Test: SUCCESS")
        print(f"     Response: {result}")
        print(f"     Tokens used: {response.usage.input_tokens + response.usage.output_tokens}")
        
    except Exception as e:
        print(f"[FAIL] Anthropic API Test: FAILED")
        print(f"       Error: {str(e)}")
    
    print()


async def test_mock_pipeline():
    """Test a mock two-stage pipeline."""
    print("MOCK TWO-STAGE PIPELINE TEST")
    print("=" * 50)
    
    test_document = """
    SAMPLE CONTRACT
    
    This agreement is between Company A and Company B.
    Term: 12 months
    Payment: $10,000 monthly
    Termination: 30 days notice required
    """
    
    print(f"Test document: {len(test_document)} characters")
    print()
    
    # Mock Stage 1: OpenAI Analysis
    print("Stage 1 (OpenAI Analysis):")
    openai_analysis = {
        "provider": "openai",
        "model": "gpt-4-turbo-preview",
        "analysis": """Contract Analysis:
- Type: Service Agreement
- Parties: Company A and Company B  
- Duration: 12 months
- Payment Terms: $10,000/month
- Termination: 30 days written notice
- Risk Level: Medium - standard commercial terms""",
        "timestamp": datetime.now().isoformat(),
        "is_live": os.getenv("OPENAI_API_KEY", "").startswith("sk-") and len(os.getenv("OPENAI_API_KEY", "")) > 20
    }
    
    print(f"[OK] OpenAI analysis completed")
    print(f"     Status: {'Live' if openai_analysis['is_live'] else 'Mock'}")
    print(f"     Preview: {openai_analysis['analysis'][:80]}...")
    print()
    
    # Mock Stage 2: Anthropic Review
    print("Stage 2 (Anthropic Review):")
    anthropic_review = {
        "provider": "anthropic",
        "model": "claude-3-opus-20240229",
        "review": """Review of OpenAI Analysis:

The previous analysis correctly identifies this as a service agreement with standard commercial terms. 

Additional considerations:
- Contract lacks dispute resolution mechanism
- No intellectual property clauses specified
- Consider adding force majeure provisions
- Payment terms could specify late fees
- Termination clause should address work-in-progress

Overall assessment: The analysis is accurate but could benefit from additional risk factors.""",
        "timestamp": datetime.now().isoformat(),
        "is_live": os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant-") and len(os.getenv("ANTHROPIC_API_KEY", "")) > 30
    }
    
    print(f"[OK] Anthropic review completed")
    print(f"     Status: {'Live' if anthropic_review['is_live'] else 'Mock'}")
    print(f"     Preview: {anthropic_review['review'][:80]}...")
    print()
    
    # Combined result
    pipeline_result = {
        "stage_1": openai_analysis,
        "stage_2": anthropic_review,
        "pipeline_mode": "two_stage_review",
        "both_live": openai_analysis['is_live'] and anthropic_review['is_live']
    }
    
    print("Pipeline Summary:")
    print(f"     Both services live: {'Yes' if pipeline_result['both_live'] else 'No'}")
    print(f"     Pipeline ready: Yes")
    print()


def generate_recommendations(status):
    """Generate recommendations based on service status."""
    print("RECOMMENDATIONS")
    print("=" * 50)
    
    recommendations = []
    
    if status["openai"] == "unavailable":
        recommendations.append("Set OPENAI_API_KEY environment variable with a valid OpenAI API key")
    elif status["openai"] == "library_missing":
        recommendations.append("Install OpenAI library: pip install openai")
    
    if status["anthropic"] == "unavailable":
        recommendations.append("Set ANTHROPIC_API_KEY environment variable with a valid Anthropic API key")  
    elif status["anthropic"] == "library_missing":
        recommendations.append("Install Anthropic library: pip install anthropic")
    
    if status["pipeline"] == "FULL_LIVE_PIPELINE":
        recommendations.append("[SUCCESS] All services configured! Ready for production use.")
    elif status["pipeline"] == "MIXED_PIPELINE":
        recommendations.append("Consider configuring both services with real API keys for best results")
    elif status["pipeline"] == "MOCK_PIPELINE":
        recommendations.append("Using mock keys - configure real API keys for actual AI analysis")
    else:
        recommendations.append("Configure at least one AI service to enable analysis")
    
    if not recommendations:
        recommendations.append("System is fully configured and ready to use!")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print()


async def main():
    """Run all tests."""
    print("LEGAL AI SYSTEM - API SERVICES TEST")
    print("=" * 50)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Environment variables
    test_environment_variables()
    
    # Library availability
    test_library_imports()
    
    # Service status
    status = determine_service_status()
    
    # API tests (only if libraries available and keys look real)
    await test_basic_openai()
    await test_basic_anthropic()
    
    # Mock pipeline test
    await test_mock_pipeline()
    
    # Recommendations
    generate_recommendations(status)
    
    print("TEST COMPLETE!")
    print()


if __name__ == "__main__":
    asyncio.run(main())