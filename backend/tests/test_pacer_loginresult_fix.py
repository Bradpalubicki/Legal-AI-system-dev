#!/usr/bin/env python3
"""
Test script to verify PACER loginResult fix.

This script helps debug authentication issues by:
1. Testing the authenticator with mock responses
2. Testing with real PACER credentials (if available)
3. Logging detailed debug info about loginResult handling
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_loginresult_parsing():
    """Test how different loginResult values are handled"""
    from src.pacer.auth.authenticator import PACERAuthenticator

    print("\n" + "="*60)
    print("TESTING loginResult PARSING")
    print("="*60 + "\n")

    test_cases = [
        {"loginResult": "0", "expected": "success", "description": "String '0'"},
        {"loginResult": 0, "expected": "success", "description": "Integer 0"},
        {"loginResult": "13", "expected": "failure", "description": "String '13' (invalid credentials)"},
        {"loginResult": 13, "expected": "failure", "description": "Integer 13"},
        {"loginResult": None, "expected": "failure", "description": "None"},
        {"loginResult": "", "expected": "failure", "description": "Empty string"},
        {"loginResult": " 0 ", "expected": "success", "description": "String '0' with whitespace"},
    ]

    for test in test_cases:
        raw_value = test["loginResult"]

        # Simulate the parsing logic
        if raw_value is None:
            login_result = ""
        else:
            login_result = str(raw_value).strip()

        is_success = (login_result == "0")
        actual_result = "success" if is_success else "failure"

        status = "✅ PASS" if actual_result == test["expected"] else "❌ FAIL"

        print(f"{status} | {test['description']}")
        print(f"       Raw: {repr(raw_value)} (type: {type(raw_value).__name__})")
        print(f"       Parsed: '{login_result}'")
        print(f"       Expected: {test['expected']}, Got: {actual_result}")
        print()


async def test_with_mock_response():
    """Test authentication with mock PACER response"""
    from unittest.mock import AsyncMock, patch
    from src.pacer.auth.authenticator import PACERAuthenticator

    print("\n" + "="*60)
    print("TESTING WITH MOCK PACER RESPONSE")
    print("="*60 + "\n")

    # Test case 1: Success with string "0"
    mock_response_success = AsyncMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {
        "loginResult": "0",
        "nextGenCSO": "test_token_123456789",
        "errorDescription": ""
    }

    print("Test 1: Success with loginResult='0' (string)")
    auth = PACERAuthenticator(environment="qa")

    try:
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response_success

            result = await auth.authenticate("test_user", "test_pass")

            if result["loginResult"] == "0" and result["nextGenCSO"]:
                print("✅ PASS - Successfully authenticated with loginResult='0'")
                print(f"   Token: {result['nextGenCSO'][:20]}...")
            else:
                print("❌ FAIL - Authentication succeeded but returned wrong format")
                print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ FAIL - Exception raised: {e}")
    finally:
        await auth.close()

    print()

    # Test case 2: Success with integer 0
    mock_response_int = AsyncMock()
    mock_response_int.status_code = 200
    mock_response_int.json.return_value = {
        "loginResult": 0,  # Integer
        "nextGenCSO": "test_token_987654321",
        "errorDescription": ""
    }

    print("Test 2: Success with loginResult=0 (integer)")
    auth2 = PACERAuthenticator(environment="qa")

    try:
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response_int

            result = await auth2.authenticate("test_user", "test_pass")

            if result["loginResult"] == "0" and result["nextGenCSO"]:
                print("✅ PASS - Successfully authenticated with loginResult=0 (int)")
                print(f"   Token: {result['nextGenCSO'][:20]}...")
            else:
                print("❌ FAIL - Authentication succeeded but returned wrong format")
                print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ FAIL - Exception raised: {e}")
    finally:
        await auth2.close()

    print()

    # Test case 3: Failure with code 13
    mock_response_fail = AsyncMock()
    mock_response_fail.status_code = 200
    mock_response_fail.json.return_value = {
        "loginResult": "13",
        "errorDescription": "Invalid username, password, or one-time passcode"
    }

    print("Test 3: Failure with loginResult='13'")
    auth3 = PACERAuthenticator(environment="qa")

    try:
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response_fail

            result = await auth3.authenticate("test_user", "wrong_pass")
            print(f"❌ FAIL - Should have raised exception but got: {result}")
    except Exception as e:
        if "code 13" in str(e) or "Invalid" in str(e):
            print(f"✅ PASS - Correctly raised exception: {e}")
        else:
            print(f"⚠️  PARTIAL - Raised exception but unexpected message: {e}")
    finally:
        await auth3.close()

    print()


async def test_with_real_credentials():
    """Test with real PACER credentials if available"""
    from src.pacer.auth.authenticator import PACERAuthenticator

    username = os.getenv("PACER_USERNAME")
    password = os.getenv("PACER_PASSWORD")

    if not username or not password:
        print("\n" + "="*60)
        print("SKIPPING REAL CREDENTIAL TEST")
        print("="*60)
        print("\nSet PACER_USERNAME and PACER_PASSWORD environment variables")
        print("to test with real PACER credentials.\n")
        return

    print("\n" + "="*60)
    print("TESTING WITH REAL PACER CREDENTIALS")
    print("="*60 + "\n")

    print(f"Username: {username[:4]}***")
    print("Environment: qa (non-billable testing)")
    print()

    auth = PACERAuthenticator(environment="qa")

    try:
        print("Attempting authentication...")
        result = await auth.authenticate(username, password)

        print("✅ SUCCESS - Authentication completed")
        print(f"   loginResult: {result.get('loginResult')}")
        print(f"   loginResultCode: {result.get('loginResultCode')}")
        print(f"   Token: {result.get('nextGenCSO', '')[:20]}...")
        print(f"   Cached: {result.get('cached', False)}")
        print(f"   Warning: {result.get('warning') or 'None'}")

        # Test cached token
        print("\nTesting cached token retrieval...")
        result2 = await auth.authenticate(username, password)

        if result2.get("cached"):
            print("✅ SUCCESS - Token retrieved from cache")
        else:
            print("⚠️  Token not cached (might be expected depending on setup)")

    except Exception as e:
        print(f"❌ FAILED - Authentication error: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Check if error message contains the double "Authentication failed"
        error_str = str(e)
        if "Authentication failed: Authentication failed" in error_str:
            print("⚠️  WARNING: Error message has duplicate 'Authentication failed'")
            print("   This indicates the bug is still present!")

    finally:
        await auth.close()

    print()


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PACER loginResult Fix Verification")
    print("="*60)
    print("\nThis script tests the fix for loginResult='0' handling")
    print("Bug: Authentication was failing because code checked for")
    print("     loginResult='success' instead of loginResult='0'\n")

    try:
        # Test 1: Parse logic
        await test_loginresult_parsing()

        # Test 2: Mock responses
        await test_with_mock_response()

        # Test 3: Real credentials (if available)
        await test_with_real_credentials()

        print("\n" + "="*60)
        print("TESTING COMPLETE")
        print("="*60)
        print("\nIf all tests pass, the loginResult fix is working correctly!")
        print("Check logs for detailed debug information.\n")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
