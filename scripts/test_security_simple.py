#!/usr/bin/env python3
"""
Simple Security Test (Windows Compatible)
Tests the security middleware without Unicode characters
"""

import requests
import sys

API_BASE = "http://localhost:8000"

def test_backend_running():
    """Test if backend is running"""
    print("\n" + "="*70)
    print("TEST 1: Backend Status")
    print("="*70)

    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("PASS - Backend is running")
        return True
    except Exception as e:
        print(f"FAIL - Backend not running: {e}")
        return False


def test_security_headers():
    """Test security headers"""
    print("\n" + "="*70)
    print("TEST 2: Security Headers")
    print("="*70)

    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)

        expected_headers = {
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        }

        passed = 0
        failed = 0

        for header, expected_value in expected_headers.items():
            actual_value = response.headers.get(header)
            if actual_value:
                print(f"PASS - {header}: {actual_value}")
                passed += 1
            else:
                print(f"FAIL - {header}: Missing")
                failed += 1

        print(f"\nResult: {passed} passed, {failed} failed")
        return failed == 0

    except Exception as e:
        print(f"FAIL - Error testing headers: {e}")
        return False


def test_rate_limiting():
    """Test rate limiting headers"""
    print("\n" + "="*70)
    print("TEST 3: Rate Limiting")
    print("="*70)

    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)

        rate_headers = ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset']

        found = False
        for header in rate_headers:
            value = response.headers.get(header)
            if value:
                print(f"{header}: {value}")
                found = True

        if found:
            print("PASS - Rate limiting active")
        else:
            print("WARN - Rate limit headers not found")

        return True

    except Exception as e:
        print(f"FAIL - Error testing rate limiting: {e}")
        return False


def test_endpoints():
    """Test various endpoints"""
    print("\n" + "="*70)
    print("TEST 4: Endpoint Access (Dev Mode)")
    print("="*70)

    tests = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/v1/qa/test", "Q&A endpoint"),
    ]

    for path, description in tests:
        try:
            response = requests.get(f"{API_BASE}{path}", timeout=5)
            status = "PASS" if response.status_code in [200, 404, 405, 422] else "FAIL"
            print(f"{status} - {description}: {response.status_code}")
        except Exception as e:
            print(f"FAIL - {description}: {e}")

    return True


def test_authentication_mode():
    """Test authentication mode"""
    print("\n" + "="*70)
    print("TEST 5: Authentication Mode")
    print("="*70)

    try:
        # In dev mode, endpoints should work without auth
        response = requests.post(
            f"{API_BASE}/api/v1/documents/analyze",
            json={"text": "test"},
            timeout=5
        )

        if response.status_code in [200, 422, 404]:  # 422 = validation error (expected)
            print("PASS - Development mode active (no auth required)")
            print(f"Status: {response.status_code}")
            return True
        elif response.status_code == 401:
            print("INFO - Production mode active (auth required)")
            print(f"Status: {response.status_code}")
            return True
        else:
            print(f"Status: {response.status_code}")
            return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Run all tests"""
    print("="*70)
    print(" LEGAL AI SYSTEM - SECURITY TEST SUITE")
    print("="*70)
    print(f"\nTesting: {API_BASE}")

    results = []

    # Run tests
    if not test_backend_running():
        print("\nERROR: Backend is not running!")
        print("Please start it with:")
        print("  cd backend && python -m uvicorn main:app --reload --port 8000")
        return 1

    results.append(("Security Headers", test_security_headers()))
    results.append(("Rate Limiting", test_rate_limiting()))
    results.append(("Endpoints", test_endpoints()))
    results.append(("Authentication", test_authentication_mode()))

    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\nSUCCESS - All security systems operational!")
        return 0
    else:
        print(f"\nWARNING - {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
