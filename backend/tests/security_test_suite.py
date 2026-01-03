#!/usr/bin/env python3
"""
CRITICAL SECURITY TEST SUITE
Legal AI System - Comprehensive Security Testing

This suite tests for the security vulnerabilities identified in the system.
Run this to validate security fixes before deployment.
"""

import asyncio
import httpx
import jwt
import time
import secrets
from typing import Dict, List, Any
import json
from concurrent.futures import ThreadPoolExecutor
import warnings

# Suppress SSL warnings for testing
warnings.filterwarnings("ignore", category=UserWarning, module='httpx')

class SecurityTestSuite:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(verify=False, timeout=10.0)
        self.vulnerabilities = []

    async def run_all_tests(self):
        """Run comprehensive security test suite"""
        print("🔐 LEGAL AI SYSTEM - SECURITY TEST SUITE")
        print("=" * 60)

        test_methods = [
            self.test_authentication_bypass,
            self.test_jwt_vulnerabilities,
            self.test_authorization_escalation,
            self.test_api_key_security,
            self.test_rate_limiting_bypass,
            self.test_data_leakage,
            self.test_sensitive_data_exposure,
            self.test_cors_misconfiguration,
            self.test_security_headers,
            self.test_error_information_disclosure
        ]

        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.add_vulnerability(
                    "CRITICAL",
                    f"Test execution failed: {test_method.__name__}",
                    str(e)
                )

        await self.generate_report()
        await self.client.aclose()

    async def test_authentication_bypass(self):
        """Test authentication bypass vulnerabilities"""
        print("\n🔍 Testing Authentication Bypass...")

        # Test 1: No token access
        try:
            response = await self.client.get(f"{self.base_url}/api/documents")
            if response.status_code != 401:
                self.add_vulnerability(
                    "CRITICAL",
                    "Authentication Bypass - No Token",
                    f"Protected endpoint accessible without token. Status: {response.status_code}"
                )
        except:
            pass

        # Test 2: Invalid token formats
        invalid_tokens = [
            "invalid_token",
            "Bearer ",
            "Bearer invalid",
            "Basic dXNlcjpwYXNz",  # Base64: user:pass
            "JWT invalid.token.here"
        ]

        for token in invalid_tokens:
            try:
                headers = {"Authorization": token}
                response = await self.client.get(f"{self.base_url}/api/documents", headers=headers)
                if response.status_code not in [401, 403]:
                    self.add_vulnerability(
                        "CRITICAL",
                        f"Authentication Bypass - Invalid Token: {token}",
                        f"Accepted invalid token format. Status: {response.status_code}"
                    )
            except:
                pass

    async def test_jwt_vulnerabilities(self):
        """Test JWT implementation vulnerabilities"""
        print("🔍 Testing JWT Vulnerabilities...")

        # Test 1: Algorithm confusion attack
        payload = {"user_id": "admin", "exp": int(time.time()) + 3600}

        # Try "none" algorithm
        try:
            none_token = jwt.encode(payload, "", algorithm="none")
            headers = {"Authorization": f"Bearer {none_token}"}
            response = await self.client.get(f"{self.base_url}/api/documents", headers=headers)
            if response.status_code == 200:
                self.add_vulnerability(
                    "CRITICAL",
                    "JWT None Algorithm Attack",
                    "Server accepts JWT tokens with 'none' algorithm"
                )
        except:
            pass

        # Test 2: Weak secrets
        weak_secrets = ["secret", "123456", "password", "key"]
        for secret in weak_secrets:
            try:
                token = jwt.encode(payload, secret, algorithm="HS256")
                headers = {"Authorization": f"Bearer {token}"}
                response = await self.client.get(f"{self.base_url}/api/documents", headers=headers)
                if response.status_code == 200:
                    self.add_vulnerability(
                        "CRITICAL",
                        f"JWT Weak Secret: {secret}",
                        "JWT signed with weak/predictable secret"
                    )
            except:
                pass

        # Test 3: No expiration check
        expired_payload = {"user_id": "test", "exp": int(time.time()) - 3600}  # Expired 1 hour ago
        try:
            expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
            headers = {"Authorization": f"Bearer {expired_token}"}
            response = await self.client.get(f"{self.base_url}/api/documents", headers=headers)
            if response.status_code == 200:
                self.add_vulnerability(
                    "HIGH",
                    "JWT Expiration Not Validated",
                    "Server accepts expired JWT tokens"
                )
        except:
            pass

    async def test_authorization_escalation(self):
        """Test for authorization escalation vulnerabilities"""
        print("🔍 Testing Authorization Escalation...")

        # Test 1: Role manipulation in JWT
        privileged_payloads = [
            {"user_id": "test", "role": "admin", "exp": int(time.time()) + 3600},
            {"user_id": "test", "permissions": ["read", "write", "delete"], "exp": int(time.time()) + 3600},
            {"user_id": "admin", "exp": int(time.time()) + 3600},
            {"user_id": "test", "is_admin": True, "exp": int(time.time()) + 3600}
        ]

        for payload in privileged_payloads:
            try:
                token = jwt.encode(payload, "secret", algorithm="HS256")
                headers = {"Authorization": f"Bearer {token}"}

                # Try admin endpoints
                admin_endpoints = [
                    "/api/admin/users",
                    "/api/admin/system",
                    "/api/users",
                    "/api/config"
                ]

                for endpoint in admin_endpoints:
                    try:
                        response = await self.client.get(f"{self.base_url}{endpoint}", headers=headers)
                        if response.status_code == 200:
                            self.add_vulnerability(
                                "CRITICAL",
                                f"Authorization Escalation - {endpoint}",
                                f"User can access admin endpoint with manipulated token: {payload}"
                            )
                    except:
                        pass
            except:
                pass

    async def test_api_key_security(self):
        """Test API key security"""
        print("🔍 Testing API Key Security...")

        # Test 1: API key in URL parameters
        try:
            response = await self.client.get(f"{self.base_url}/api/documents?api_key=test123")
            if response.status_code == 200:
                self.add_vulnerability(
                    "HIGH",
                    "API Key in URL Parameters",
                    "API key accepted in URL parameters (logged in access logs)"
                )
        except:
            pass

        # Test 2: Weak API keys
        weak_keys = ["123456", "apikey", "test", "key", "admin"]
        for key in weak_keys:
            try:
                headers = {"X-API-Key": key}
                response = await self.client.get(f"{self.base_url}/api/documents", headers=headers)
                if response.status_code == 200:
                    self.add_vulnerability(
                        "HIGH",
                        f"Weak API Key Accepted: {key}",
                        "Server accepts weak/predictable API keys"
                    )
            except:
                pass

    async def test_rate_limiting_bypass(self):
        """Test rate limiting bypass techniques"""
        print("🔍 Testing Rate Limiting Bypass...")

        # Test 1: IP rotation bypass
        headers_variations = [
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Real-IP": "10.0.0.1"},
            {"X-Client-IP": "172.16.0.1"},
            {"CF-Connecting-IP": "203.0.113.1"},
            {"True-Client-IP": "198.51.100.1"}
        ]

        endpoint = f"{self.base_url}/api/documents"

        for i, headers in enumerate(headers_variations):
            successful_requests = 0
            for attempt in range(150):  # Try to exceed rate limit
                try:
                    response = await self.client.get(endpoint, headers=headers)
                    if response.status_code == 200:
                        successful_requests += 1
                except:
                    break

                if attempt > 100 and successful_requests > 100:
                    self.add_vulnerability(
                        "HIGH",
                        f"Rate Limiting Bypass - Header: {list(headers.keys())[0]}",
                        f"Made {successful_requests} successful requests bypassing rate limit"
                    )
                    break

    async def test_data_leakage(self):
        """Test for sensitive data leakage"""
        print("🔍 Testing Data Leakage...")

        # Test 1: Error messages with sensitive info
        error_endpoints = [
            "/api/documents/999999",
            "/api/users/admin",
            "/api/config/database",
            "/api/../../../etc/passwd",
            "/api/documents?sql=' OR 1=1--"
        ]

        for endpoint in error_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code == 500:
                    content = response.text.lower()
                    sensitive_patterns = [
                        "password", "secret", "token", "key", "database",
                        "connection", "server", "path", "file", "directory"
                    ]
                    for pattern in sensitive_patterns:
                        if pattern in content:
                            self.add_vulnerability(
                                "MEDIUM",
                                f"Sensitive Data in Error Response: {endpoint}",
                                f"Error response contains sensitive information: {pattern}"
                            )
                            break
            except:
                pass

    async def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure"""
        print("🔍 Testing Sensitive Data Exposure...")

        # Test configuration endpoints
        config_endpoints = [
            "/.env",
            "/config",
            "/api/config",
            "/settings",
            "/debug",
            "/admin",
            "/swagger.json",
            "/openapi.json"
        ]

        for endpoint in config_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    content = response.text
                    if any(word in content.lower() for word in ["password", "secret", "key", "token"]):
                        self.add_vulnerability(
                            "CRITICAL",
                            f"Configuration Data Exposure: {endpoint}",
                            "Endpoint exposes sensitive configuration data"
                        )
            except:
                pass

    async def test_cors_misconfiguration(self):
        """Test CORS misconfiguration"""
        print("🔍 Testing CORS Misconfiguration...")

        malicious_origins = [
            "http://evil.com",
            "https://attacker.com",
            "http://localhost:3001",  # If not in allowed origins
            "null"
        ]

        for origin in malicious_origins:
            try:
                headers = {"Origin": origin}
                response = await self.client.get(f"{self.base_url}/api/documents", headers=headers)

                cors_header = response.headers.get("Access-Control-Allow-Origin")
                if cors_header == "*" or cors_header == origin:
                    self.add_vulnerability(
                        "MEDIUM",
                        f"CORS Misconfiguration: {origin}",
                        f"Server allows requests from untrusted origin: {cors_header}"
                    )
            except:
                pass

    async def test_security_headers(self):
        """Test missing security headers"""
        print("🔍 Testing Security Headers...")

        try:
            response = await self.client.get(f"{self.base_url}/")
            headers = response.headers

            required_security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,
                "Content-Security-Policy": None,
                "Referrer-Policy": None
            }

            for header, expected in required_security_headers.items():
                if header not in headers:
                    self.add_vulnerability(
                        "MEDIUM",
                        f"Missing Security Header: {header}",
                        "Security header not present in response"
                    )
                elif expected and headers[header] not in expected:
                    if isinstance(expected, list):
                        if headers[header] not in expected:
                            self.add_vulnerability(
                                "LOW",
                                f"Weak Security Header: {header}",
                                f"Header value '{headers[header]}' may be insufficient"
                            )
                    elif headers[header] != expected:
                        self.add_vulnerability(
                            "LOW",
                            f"Weak Security Header: {header}",
                            f"Header value '{headers[header]}' may be insufficient"
                        )
        except:
            pass

    async def test_error_information_disclosure(self):
        """Test error information disclosure"""
        print("🔍 Testing Error Information Disclosure...")

        # Test debug mode detection
        try:
            response = await self.client.get(f"{self.base_url}/debug")
            if "debug" in response.text.lower() or response.status_code == 200:
                self.add_vulnerability(
                    "HIGH",
                    "Debug Mode Enabled",
                    "Debug endpoints accessible in production"
                )
        except:
            pass

    def add_vulnerability(self, severity: str, title: str, description: str):
        """Add vulnerability to findings"""
        self.vulnerabilities.append({
            "severity": severity,
            "title": title,
            "description": description,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        print(f"  🚨 {severity}: {title}")

    async def generate_report(self):
        """Generate security test report"""
        print("\n" + "=" * 60)
        print("🔐 SECURITY TEST REPORT")
        print("=" * 60)

        if not self.vulnerabilities:
            print("✅ No vulnerabilities detected!")
            return

        # Count by severity
        severity_counts = {}
        for vuln in self.vulnerabilities:
            severity = vuln["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        print(f"\n📊 VULNERABILITY SUMMARY:")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[severity]
                print(f"  {emoji} {severity}: {count}")

        print(f"\n🚨 DETAILED FINDINGS:")
        print("-" * 60)

        for vuln in sorted(self.vulnerabilities, key=lambda x: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}[x["severity"]], reverse=True):
            print(f"\n[{vuln['severity']}] {vuln['title']}")
            print(f"Description: {vuln['description']}")
            print(f"Timestamp: {vuln['timestamp']}")

        # Save to file
        with open("security_test_results.json", "w") as f:
            json.dump({
                "summary": severity_counts,
                "vulnerabilities": self.vulnerabilities,
                "total": len(self.vulnerabilities),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)

        print(f"\n💾 Report saved to: security_test_results.json")
        print("=" * 60)

# Run the security tests
async def main():
    suite = SecurityTestSuite()
    await suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())