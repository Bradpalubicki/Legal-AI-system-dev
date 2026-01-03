#!/usr/bin/env python3
"""
Simple test script to verify security tools are working correctly
Fixed for Windows console compatibility
"""

import subprocess
import sys
import json

def test_security_tools():
    """Test that the security tools work correctly"""
    print("TESTING SECURITY TOOLS")
    print("=" * 40)

    # Test pip-audit
    print("Testing pip-audit...")
    try:
        result = subprocess.run(['pip-audit', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] pip-audit working: {result.stdout.strip()}")
        else:
            print(f"[ERROR] pip-audit error: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] pip-audit not available: {e}")

    # Test bandit
    print("Testing bandit...")
    try:
        result = subprocess.run(['bandit', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] bandit working: {result.stdout.strip()}")
        else:
            print(f"[ERROR] bandit error: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] bandit not available: {e}")

    print("=" * 40)

    # Test pip-audit dependency scan
    print("Testing pip-audit dependency scan...")
    try:
        result = subprocess.run(['pip-audit', '--format=json'], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("[OK] pip-audit scan completed - no vulnerabilities found")

            # Try to parse JSON output
            try:
                data = json.loads(result.stdout)
                dep_count = len(data.get('dependencies', []))
                vuln_count = sum(len(dep.get('vulns', [])) for dep in data.get('dependencies', []))
                print(f"[INFO] Scanned {dep_count} dependencies, found {vuln_count} vulnerabilities")
            except:
                print("[INFO] Could not parse scan results")

        else:
            if "found vulnerabilities" in result.stderr:
                print("[WARNING] pip-audit found vulnerabilities")
                print(result.stderr)
            else:
                print(f"[INFO] pip-audit completed with info: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("[ERROR] pip-audit scan timed out")
    except Exception as e:
        print(f"[ERROR] pip-audit scan failed: {e}")

    # Test bandit code scan
    print("Testing bandit code scan...")
    try:
        result = subprocess.run([
            'bandit', '-r', 'backend/app/src/', '-f', 'json'
        ], capture_output=True, text=True, timeout=60)

        try:
            data = json.loads(result.stdout)
            issue_count = len(data.get('results', []))
            if issue_count == 0:
                print("[OK] bandit scan completed - no security issues found")
            else:
                print(f"[WARNING] bandit found {issue_count} security issues")

                # Show severity breakdown
                severities = {}
                for issue in data.get('results', []):
                    sev = issue.get('issue_severity', 'UNKNOWN')
                    severities[sev] = severities.get(sev, 0) + 1

                for severity, count in severities.items():
                    print(f"  {severity}: {count}")

        except json.JSONDecodeError:
            print("[ERROR] Could not parse bandit output")

    except subprocess.TimeoutExpired:
        print("[ERROR] bandit scan timed out")
    except Exception as e:
        print(f"[INFO] bandit scan: {e}")

    print("=" * 40)
    print("TOOL TESTING COMPLETED")

if __name__ == "__main__":
    test_security_tools()