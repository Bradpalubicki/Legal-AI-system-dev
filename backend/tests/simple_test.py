#!/usr/bin/env python3
"""
Simple test script to verify environment variable reading.
"""

import os


def test_environment_variables():
    """Test reading API keys from environment variables."""
    print("=== Environment Variables Test ===")
    
    # Check OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY present: {openai_key is not None}")
    if openai_key:
        print(f"OPENAI_API_KEY starts with: {openai_key[:10]}...")
        print(f"OPENAI_API_KEY length: {len(openai_key)}")
        print(f"Is real key (starts with sk-): {openai_key.startswith('sk-')}")
    
    # Check Anthropic key  
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"ANTHROPIC_API_KEY present: {anthropic_key is not None}")
    if anthropic_key:
        print(f"ANTHROPIC_API_KEY starts with: {anthropic_key[:15]}...")
        print(f"ANTHROPIC_API_KEY length: {len(anthropic_key)}")
        print(f"Is real key (starts with sk-ant-): {anthropic_key.startswith('sk-ant-')}")
    
    print()


def test_key_detection():
    """Test key detection logic."""
    print("=== Key Detection Logic Test ===")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # OpenAI key validation
    openai_is_real = (
        openai_key is not None 
        and openai_key.startswith("sk-") 
        and len(openai_key) > 20
        and not openai_key.startswith("sk-mock")
    )
    print(f"OpenAI key is real: {openai_is_real}")
    
    # Anthropic key validation
    anthropic_is_real = (
        anthropic_key is not None 
        and anthropic_key.startswith("sk-ant-") 
        and len(anthropic_key) > 30
        and not anthropic_key.startswith("sk-ant-mock")
    )
    print(f"Anthropic key is real: {anthropic_is_real}")
    
    # Determine service mode
    if openai_is_real and anthropic_is_real:
        service_mode = "full_pipeline"
    elif openai_is_real and not anthropic_is_real:
        service_mode = "openai_only"
    elif not openai_is_real and anthropic_is_real:
        service_mode = "anthropic_only"
    else:
        service_mode = "mock_services"
    
    print(f"Service mode: {service_mode}")
    print()


def main():
    """Run all tests."""
    print("AI Service Environment Variable Detection Test")
    print("=" * 50)
    
    test_environment_variables()
    test_key_detection()
    
    print("Environment variable tests completed!")


if __name__ == "__main__":
    main()