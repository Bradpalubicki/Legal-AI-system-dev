#!/usr/bin/env python
"""
Direct test of Anthropic API functionality
"""

import asyncio
import sys
import os
sys.path.append('src')

from src.shared.ai.anthropic_service import AnthropicService

async def test_anthropic():
    """Test Anthropic service directly."""
    print("Testing Anthropic service...")

    try:
        # Initialize service
        service = AnthropicService()

        print(f"Service available: {service.is_available}")
        print(f"Service live: {service.is_live}")

        if not service.is_available:
            print("ERROR: Anthropic service is not available")
            return

        if service.is_live:
            print("Testing live Anthropic API...")
            try:
                client = service.client
                response = await client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=50,
                    messages=[
                        {
                            "role": "user",
                            "content": "Hello! Please respond with just 'Anthropic API is working'"
                        }
                    ]
                )

                print(f"SUCCESS! Response: {response.content[0].text}")
                return True

            except Exception as e:
                print(f"Error calling Anthropic API: {e}")
                return False
        else:
            print("Anthropic service available but in mock mode")
            return True

    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_anthropic())
    sys.exit(0 if result else 1)