#!/usr/bin/env python3
"""
Simple test script to verify all AI services are working.

This script tests:
1. Environment variable detection
2. API key validation
3. Service detection
4. Two-stage AI pipeline functionality
"""

import sys
import asyncio
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Add shared to path
shared_path = Path(__file__).parent / "src" / "shared"
sys.path.insert(0, str(shared_path))

try:
    from config.api_keys import get_api_key_config, get_service_status
    from utils.service_detector import get_service_detector
    from ai.pipeline import get_pipeline
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from the project root directory")
    print("Required libraries: pip install openai anthropic")
    sys.exit(1)


def test_environment_detection():
    """Test environment variable detection."""
    print("🔍 Testing Environment Variable Detection")
    print("=" * 50)
    
    config = get_api_key_config()
    status = get_service_status()
    
    print(f"OpenAI Key Status: {status['openai']['status']}")
    print(f"OpenAI Available: {status['openai']['available']}")
    print(f"OpenAI Live: {status['openai']['live']}")
    print()
    
    print(f"Anthropic Key Status: {status['anthropic']['status']}")
    print(f"Anthropic Available: {status['anthropic']['available']}")
    print(f"Anthropic Live: {status['anthropic']['live']}")
    print()
    
    print(f"Pipeline Mode: {status['pipeline_mode']}")
    print()


def test_service_detection():
    """Test comprehensive service detection."""
    print("🔧 Testing Service Detection")
    print("=" * 50)
    
    detector = get_service_detector()
    detector.print_status_report()


async def test_individual_services():
    """Test individual AI services."""
    print("🤖 Testing Individual AI Services")
    print("=" * 50)
    
    pipeline = get_pipeline()
    
    test_document = """
    SAMPLE LEGAL AGREEMENT
    
    This Agreement is entered into on January 1, 2024, between:
    - Party A: Technology Corp
    - Party B: Legal Services LLC
    
    Terms:
    1. Services: Legal consultation and contract review
    2. Duration: 6 months
    3. Payment: $5,000 per month
    4. Termination: 30 days written notice
    
    The parties agree to these terms and conditions.
    """
    
    print("Testing OpenAI service...")
    try:
        openai_result = await pipeline.analyze_single_stage(
            document_text=test_document,
            provider="openai",
            analysis_type="contract"
        )
        
        print(f"✅ OpenAI Result:")
        print(f"   Success: {openai_result['pipeline_success']}")
        print(f"   Provider: {openai_result['result']['provider']}")
        print(f"   Model: {openai_result['result']['model']}")
        print(f"   Live: {openai_result['result'].get('is_live', False)}")
        print(f"   Analysis preview: {openai_result['result']['analysis'][:100]}...")
        print()
        
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        print()
    
    print("Testing Anthropic service...")
    try:
        anthropic_result = await pipeline.analyze_single_stage(
            document_text=test_document,
            provider="anthropic",
            analysis_type="contract"
        )
        
        print(f"✅ Anthropic Result:")
        print(f"   Success: {anthropic_result['pipeline_success']}")
        print(f"   Provider: {anthropic_result['result']['provider']}")
        print(f"   Model: {anthropic_result['result']['model']}")
        print(f"   Live: {anthropic_result['result'].get('is_live', False)}")
        print(f"   Analysis preview: {anthropic_result['result']['analysis'][:100]}...")
        print()
        
    except Exception as e:
        print(f"❌ Anthropic Error: {e}")
        print()


async def test_two_stage_pipeline():
    """Test the two-stage AI pipeline."""
    print("🔄 Testing Two-Stage AI Pipeline")
    print("=" * 50)
    
    pipeline = get_pipeline()
    
    if not pipeline.is_pipeline_available:
        print("❌ Pipeline not available - missing required services")
        requirements = pipeline.config.get_pipeline_requirements()
        if requirements:
            print("Requirements:")
            for service, req in requirements.items():
                print(f"   {service}: {req}")
        print()
        return
    
    test_document = """
    CONFIDENTIALITY AGREEMENT
    
    This Confidentiality Agreement ("Agreement") is made on March 1, 2024, between:
    
    Disclosing Party: InnovTech Solutions Inc., a Delaware corporation
    Receiving Party: Digital Marketing Agency LLC, a California limited liability company
    
    WHEREAS, Disclosing Party desires to share certain confidential information;
    WHEREAS, Receiving Party agrees to maintain confidentiality;
    
    NOW THEREFORE, the parties agree:
    
    1. CONFIDENTIAL INFORMATION
    Confidential Information includes all technical data, trade secrets, know-how, 
    research, product plans, software, customers, customer lists, markets, marketing
    plans, finances, or other business information.
    
    2. OBLIGATIONS
    Receiving Party agrees to:
    a) Hold all Confidential Information in strict confidence
    b) Not disclose to any third parties
    c) Use information solely for evaluation purposes
    d) Return all materials upon request
    
    3. TERM
    This Agreement shall remain in effect for 3 years from the date signed.
    
    4. REMEDIES
    Breach may result in irreparable harm warranting injunctive relief.
    
    IN WITNESS WHEREOF, the parties have executed this Agreement.
    """
    
    print(f"Document length: {len(test_document)} characters")
    print(f"Pipeline available: {pipeline.is_pipeline_available}")
    print(f"Pipeline live: {pipeline.is_pipeline_live}")
    print()
    
    try:
        print("🚀 Running two-stage analysis pipeline...")
        result = await pipeline.analyze_document(
            document_text=test_document,
            analysis_type="contract",
            use_review_mode=True
        )
        
        print(f"✅ Pipeline completed successfully: {result['pipeline_success']}")
        print(f"   Duration: {result['pipeline_info']['duration_seconds']:.2f} seconds")
        print(f"   Mode: {result['pipeline_info']['mode']}")
        print()
        
        # Stage 1 results
        if 'stage_1' in result:
            stage1 = result['stage_1']
            print("📊 Stage 1 (OpenAI) Results:")
            print(f"   Success: {stage1['success']}")
            print(f"   Provider: {stage1['result']['provider']}")
            print(f"   Model: {stage1['result']['model']}")
            print(f"   Live: {stage1['result'].get('is_live', False)}")
            print(f"   Analysis preview: {stage1['result']['analysis'][:150]}...")
            print()
        
        # Stage 2 results
        if 'stage_2' in result:
            stage2 = result['stage_2']
            print("📊 Stage 2 (Anthropic) Results:")
            print(f"   Success: {stage2['success']}")
            print(f"   Provider: {stage2['result']['provider']}")
            print(f"   Model: {stage2['result']['model']}")
            print(f"   Live: {stage2['result'].get('is_live', False)}")
            print(f"   Mode: {stage2['mode']}")
            
            if stage2['mode'] == 'review':
                print(f"   Review preview: {stage2['result'].get('review', 'No review')[:150]}...")
            else:
                print(f"   Analysis preview: {stage2['result']['analysis'][:150]}...")
            print()
        
        # Combined metrics
        if 'combined_metrics' in result:
            metrics = result['combined_metrics']
            print("📈 Combined Metrics:")
            print(f"   Total tokens: {metrics['total_tokens']}")
            print(f"   OpenAI tokens: {metrics['openai_tokens']}")
            print(f"   Anthropic tokens: {metrics['anthropic_tokens']}")
            print(f"   Both live: {metrics['both_live']}")
            if 'cost_estimate' in metrics:
                print(f"   Estimated cost: ${metrics['cost_estimate']['total_cost_estimate']:.4f}")
            print()
        
    except Exception as e:
        print(f"❌ Pipeline Error: {e}")
        print()


async def test_pipeline_modes():
    """Test different pipeline modes."""
    print("⚙️ Testing Different Pipeline Modes")
    print("=" * 50)
    
    pipeline = get_pipeline()
    
    if not pipeline.is_pipeline_available:
        print("❌ Pipeline not available - skipping mode tests")
        return
    
    test_doc = "This is a short test contract between two parties for testing purposes."
    
    print("Testing review mode (Claude reviews OpenAI)...")
    try:
        review_result = await pipeline.analyze_document(
            document_text=test_doc,
            analysis_type="general",
            use_review_mode=True
        )
        print(f"✅ Review mode: {review_result['pipeline_success']}")
        print(f"   Mode: {review_result['pipeline_info'].get('review_mode', 'Unknown')}")
        print()
    except Exception as e:
        print(f"❌ Review mode error: {e}")
        print()
    
    print("Testing independent mode (both analyze independently)...")
    try:
        independent_result = await pipeline.analyze_document(
            document_text=test_doc,
            analysis_type="general",
            use_review_mode=False
        )
        print(f"✅ Independent mode: {independent_result['pipeline_success']}")
        print(f"   Mode: {independent_result['pipeline_info'].get('review_mode', 'Unknown')}")
        print()
    except Exception as e:
        print(f"❌ Independent mode error: {e}")
        print()


async def main():
    """Run all tests."""
    print("🧪 AI SERVICES COMPREHENSIVE TEST")
    print("🧪" * 30)
    print()
    
    # Test 1: Environment detection
    test_environment_detection()
    
    # Test 2: Service detection
    test_service_detection()
    
    # Test 3: Individual services
    await test_individual_services()
    
    # Test 4: Two-stage pipeline
    await test_two_stage_pipeline()
    
    # Test 5: Different pipeline modes
    await test_pipeline_modes()
    
    print("🎉 All tests completed!")
    print()
    
    # Final summary
    print("📋 FINAL SUMMARY")
    print("=" * 50)
    pipeline = get_pipeline()
    status = pipeline.pipeline_status
    
    print(f"Pipeline Available: {status['pipeline_available']}")
    print(f"Pipeline Mode: {status['pipeline_mode']}")
    print(f"OpenAI Status: {status['services']['openai']['status']}")
    print(f"Anthropic Status: {status['services']['anthropic']['status']}")
    
    if status['pipeline_available']:
        print("✅ AI services are configured and ready to use!")
    else:
        print("⚠️  Some services need configuration.")
        requirements = pipeline.config.get_pipeline_requirements()
        if requirements:
            print("Next steps:")
            for service, req in requirements.items():
                print(f"   • {req}")


if __name__ == "__main__":
    asyncio.run(main())