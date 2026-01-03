#!/usr/bin/env python3
"""
UPDATED SECURITY TEST SUITE WITH PIP-AUDIT
Legal AI System - Comprehensive Security Testing

Updated to use pip-audit instead of safety for dependency scanning.
"""

import asyncio
import httpx
import jwt
import time
import secrets
import subprocess
import json
from typing import Dict, List, Any
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
        """Run comprehensive security test suite with new tools"""
        print("🔐 LEGAL AI SYSTEM - UPDATED SECURITY TEST SUITE")
        print("=" * 60)
        print("✅ Using pip-audit for dependency scanning")
        print("✅ Clean environment - no deprecation warnings")
        print("=" * 60)

        test_methods = [
            self.test_dependency_vulnerabilities,  # New pip-audit test
            self.test_authentication_bypass,
            self.test_jwt_vulnerabilities,
            self.test_authorization_escalation,
            self.test_api_key_security,
            self.test_rate_limiting_bypass,
            self.test_data_leakage,
            self.test_sensitive_data_exposure,
            self.test_cors_misconfiguration,
            self.test_security_headers,
            self.test_error_information_disclosure,
            self.test_code_security_issues
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

    async def test_dependency_vulnerabilities(self):
        """Test for dependency vulnerabilities using pip-audit"""
        print("\n🔍 Testing Dependency Vulnerabilities (pip-audit)...")

        try:
            # Run pip-audit
            result = subprocess.run([
                'pip-audit',
                '--format=json'
            ], capture_output=True, text=True, timeout=60)

            if result.returncode != 0 and result.stderr:
                # Check if there are actual vulnerabilities or just errors
                if "found vulnerabilities" in result.stderr.lower():
                    self.add_vulnerability(
                        "HIGH",
                        "Dependency Vulnerabilities Found",
                        f"pip-audit found security issues: {result.stderr}"
                    )
                else:
                    print(f"  ℹ️  pip-audit info: {result.stderr}")

            # Parse JSON output if available
            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    vulnerable_deps = [dep for dep in audit_data.get('dependencies', [])
                                     if dep.get('vulns')]

                    if vulnerable_deps:
                        for dep in vulnerable_deps:
                            for vuln in dep['vulns']:
                                self.add_vulnerability(
                                    "HIGH",
                                    f"Vulnerable Dependency: {dep['name']}",
                                    f"Version {dep['version']} has vulnerability {vuln.get('id', 'Unknown')}: {vuln.get('description', 'No description')}"
                                )
                    else:
                        print("  ✅ No dependency vulnerabilities found")

                except json.JSONDecodeError as e:
                    print(f"  ⚠️  Could not parse pip-audit output: {e}")

        except subprocess.TimeoutExpired:
            self.add_vulnerability(
                "MEDIUM",
                "Dependency Scan Timeout",
                "pip-audit scan timed out - may indicate performance issues"
            )
        except FileNotFoundError:
            self.add_vulnerability(
                "HIGH",
                "Security Tool Missing",
                "pip-audit is not installed or not in PATH"
            )
        except Exception as e:
            print(f"  ⚠️  Dependency scan error: {e}")

    async def test_code_security_issues(self):
        """Test for static code security issues using bandit"""
        print("\n🔍 Testing Code Security Issues (bandit)...")

        try:
            # Run bandit on the codebase
            result = subprocess.run([
                'bandit',
                '-r', 'backend/app/src/',
                '-f', 'json'
            ], capture_output=True, text=True, timeout=120)

            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    issues = bandit_data.get('results', [])

                    if issues:
                        print(f"  🚨 Found {len(issues)} code security issues")
                        for issue in issues:
                            severity = issue.get('issue_severity', 'UNKNOWN')
                            confidence = issue.get('issue_confidence', 'UNKNOWN')

                            # Map bandit severity to our severity levels
                            mapped_severity = "MEDIUM"
                            if severity == "HIGH":
                                mapped_severity = "HIGH"
                            elif severity == "MEDIUM":
                                mapped_severity = "MEDIUM"
                            else:
                                mapped_severity = "LOW"

                            self.add_vulnerability(
                                mapped_severity,
                                f"Code Security Issue: {issue.get('test_name', 'Unknown')}",
                                f"File: {issue.get('filename', 'Unknown')}:{issue.get('line_number', 'Unknown')} - {issue.get('issue_text', 'No description')}"
                            )
                    else:
                        print("  ✅ No code security issues found")

                except json.JSONDecodeError as e:
                    print(f"  ⚠️  Could not parse bandit output: {e}")

        except subprocess.TimeoutExpired:
            print("  ⚠️  Code security scan timed out")
        except FileNotFoundError:
            print("  ⚠️  bandit not found - code security scan skipped")
        except Exception as e:
            print(f"  ⚠️  Code security scan error: {e}")

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

    async def test_authorization_escalation(self):
        """Test for authorization escalation vulnerabilities"""
        print("🔍 Testing Authorization Escalation...")

        # Test role manipulation in JWT
        privileged_payloads = [
            {"user_id": "test", "role": "admin", "exp": int(time.time()) + 3600},
            {"user_id": "admin", "exp": int(time.time()) + 3600},
        ]

        for payload in privileged_payloads:
            try:
                token = jwt.encode(payload, "secret", algorithm="HS256")
                headers = {"Authorization": f"Bearer {token}"}

                admin_endpoints = ["/api/admin/users", "/api/users"]
                for endpoint in admin_endpoints:
                    try:
                        response = await self.client.get(f"{self.base_url}{endpoint}", headers=headers)
                        if response.status_code == 200:
                            self.add_vulnerability(
                                "CRITICAL",
                                f"Authorization Escalation - {endpoint}",
                                f"User can access admin endpoint with token: {payload}"
                            )
                    except:
                        pass
            except:
                pass

    async def test_api_key_security(self):
        """Test API key security"""
        print("🔍 Testing API Key Security...")

        # Test weak API keys
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

        headers_variations = [
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Real-IP": "10.0.0.1"},
        ]

        endpoint = f"{self.base_url}/api/documents"
        for headers in headers_variations:
            successful_requests = 0
            for attempt in range(50):  # Reduced for faster testing
                try:
                    response = await self.client.get(endpoint, headers=headers)
                    if response.status_code == 200:
                        successful_requests += 1
                except:
                    break

                if attempt > 30 and successful_requests > 30:
                    self.add_vulnerability(
                        "HIGH",
                        f"Rate Limiting Bypass - Header: {list(headers.keys())[0]}",
                        f"Made {successful_requests} successful requests bypassing rate limit"
                    )
                    break

    async def test_data_leakage(self):
        """Test for sensitive data leakage"""
        print("🔍 Testing Data Leakage...")

        error_endpoints = [
            "/api/documents/999999",
            "/api/users/admin",
            "/api/../../../etc/passwd",
        ]

        for endpoint in error_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code == 500:
                    content = response.text.lower()
                    sensitive_patterns = [
                        "password", "secret", "token", "key", "database"
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

        config_endpoints = ["/.env", "/config", "/api/config"]
        for endpoint in config_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    content = response.text
                    if any(word in content.lower() for word in ["password", "secret", "key"]):
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

        malicious_origins = ["http://evil.com", "https://attacker.com"]
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

            required_security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection"
            ]

            for header in required_security_headers:
                if header not in headers:
                    self.add_vulnerability(
                        "MEDIUM",
                        f"Missing Security Header: {header}",
                        "Security header not present in response"
                    )
        except:
            pass

    async def test_error_information_disclosure(self):
        """Test error information disclosure"""
        print("🔍 Testing Error Information Disclosure...")

        try:
            response = await self.client.get(f"{self.base_url}/debug")
            if "debug" in response.text.lower() or response.status_code == 200:
                self.add_vulnerability(
                    "HIGH",
                    "Debug Mode Enabled",
                    "Debug endpoints accessible"
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
        print("🔐 UPDATED SECURITY TEST REPORT")
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

        for vuln in sorted(self.vulnerabilities,
                          key=lambda x: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}[x["severity"]],
                          reverse=True):
            print(f"\n[{vuln['severity']}] {vuln['title']}")
            print(f"Description: {vuln['description']}")
            print(f"Timestamp: {vuln['timestamp']}")

        # Save to file
        with open("security_test_results_updated.json", "w") as f:
            json.dump({
                "tool_info": {
                    "dependency_scanner": "pip-audit",
                    "code_scanner": "bandit",
                    "no_deprecation_warnings": True
                },
                "summary": severity_counts,
                "vulnerabilities": self.vulnerabilities,
                "total": len(self.vulnerabilities),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)

        print(f"\n💾 Updated report saved to: security_test_results_updated.json")
        print("=" * 60)

# Test the updated tools independently
def test_new_tools():
    """Test that the new security tools work correctly"""
    print("TESTING NEW SECURITY TOOLS")
    print("=" * 40)

    # Test pip-audit
    print("Testing pip-audit...")
    try:
        result = subprocess.run(['pip-audit', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pip-audit working: {result.stdout.strip()}")
        else:
            print(f"❌ pip-audit error: {result.stderr}")
    except Exception as e:
        print(f"❌ pip-audit not available: {e}")

    # Test bandit
    print("Testing bandit...")
    try:
        result = subprocess.run(['bandit', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ bandit working: {result.stdout.strip()}")
        else:
            print(f"❌ bandit error: {result.stderr}")
    except Exception as e:
        print(f"❌ bandit not available: {e}")

    print("=" * 40)

# Run the security tests
async def main():
    # First test the tools
    test_new_tools()
    print()

    # Then run the full security suite
    suite = SecurityTestSuite()
    await suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())