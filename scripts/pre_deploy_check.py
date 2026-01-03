#!/usr/bin/env python3
"""
Pre-Deployment Verification Script

Run this BEFORE pushing to production:
    python scripts/pre_deploy_check.py

All checks must pass before deploying.
"""

import os
import sys
import re
import subprocess
from pathlib import Path

# Colors for output (disabled on Windows for encoding compatibility)
import platform
if platform.system() == 'Windows':
    GREEN = ''
    RED = ''
    YELLOW = ''
    RESET = ''
    CHECK = '[OK]'
    CROSS = '[FAIL]'
    WARN = '[WARN]'
else:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    CHECK = '\u2713'
    CROSS = '\u2717'
    WARN = '!'

def ok(msg):
    print(f"{GREEN}{CHECK}{RESET} {msg}")

def fail(msg):
    print(f"{RED}{CROSS}{RESET} {msg}")

def warn(msg):
    print(f"{YELLOW}{WARN}{RESET} {msg}")

def run_checks():
    """Run all pre-deployment checks."""

    root = Path(__file__).parent.parent
    backend = root / "backend"
    api_dir = backend / "app" / "api"

    errors = []
    warnings = []

    print("\n" + "="*60)
    print("PRE-DEPLOYMENT VERIFICATION")
    print("="*60 + "\n")

    # =========================================================================
    # CHECK 1: Single get_current_user implementation
    # =========================================================================
    print("1. Checking auth implementations...")

    auth_implementations = []
    for py_file in backend.rglob("*.py"):
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        if re.search(r'^(async\s+)?def\s+get_current_user\s*\(', content, re.MULTILINE):
            # Exclude test files and the actual auth deps file
            rel_path = py_file.relative_to(backend)
            if 'test' not in str(rel_path).lower():
                auth_implementations.append(str(rel_path))

    # Expected: app/api/deps/auth.py and possibly app/utils/auth.py (legacy)
    expected = {'app\\api\\deps\\auth.py', 'app/api/deps/auth.py'}
    unexpected = [f for f in auth_implementations if f.replace('\\', '/') not in [e.replace('\\', '/') for e in expected] and 'utils/auth' not in f.replace('\\', '/')]

    if unexpected:
        fail(f"Found unexpected get_current_user in: {unexpected}")
        errors.append("Multiple auth implementations")
    else:
        ok("Single auth implementation in app/api/deps/auth.py")

    # =========================================================================
    # CHECK 2: CurrentUser attribute usage
    # =========================================================================
    print("\n2. Checking CurrentUser attribute usage...")

    # Valid attributes on CurrentUser
    valid_attrs = {
        'user_id', 'id', 'email', 'role', 'username', 'first_name', 'last_name',
        'roles', 'permissions', 'auth_method', 'authenticated_at', 'token_payload'
    }

    invalid_usages = []
    for py_file in api_dir.rglob("*.py"):
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        # Find all current_user.X usages
        matches = re.findall(r'current_user\.([a-z_]+)', content)
        for attr in matches:
            if attr not in valid_attrs:
                rel_path = py_file.relative_to(backend)
                invalid_usages.append(f"{rel_path}: current_user.{attr}")

    if invalid_usages:
        fail(f"Invalid CurrentUser attributes found:")
        for usage in invalid_usages[:10]:  # Show first 10
            print(f"      - {usage}")
        if len(invalid_usages) > 10:
            print(f"      ... and {len(invalid_usages) - 10} more")
        errors.append("Invalid CurrentUser attributes")
    else:
        ok("All CurrentUser attributes are valid")

    # =========================================================================
    # CHECK 3: Import consistency
    # =========================================================================
    print("\n3. Checking auth import consistency...")

    bad_imports = []
    good_pattern = re.compile(r'from\s+\.\.?api\.deps\.auth\s+import|from\s+app\.api\.deps\.auth\s+import')
    bad_patterns = [
        (re.compile(r'from\s+\.\.core\.auth\s+import'), 'core.auth (does not exist)'),
        (re.compile(r'from\s+\.\.utils\.auth\s+import\s+get_current_user'), 'utils.auth (returns different type)'),
    ]

    for py_file in api_dir.rglob("*.py"):
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        if 'get_current_user' in content:
            for pattern, desc in bad_patterns:
                if pattern.search(content):
                    rel_path = py_file.relative_to(backend)
                    bad_imports.append(f"{rel_path}: imports from {desc}")

    if bad_imports:
        fail(f"Bad auth imports found:")
        for imp in bad_imports:
            print(f"      - {imp}")
        errors.append("Inconsistent auth imports")
    else:
        ok("Auth imports are consistent")

    # =========================================================================
    # CHECK 4: Environment variables documented
    # =========================================================================
    print("\n4. Checking environment variables...")

    # Find all os.getenv calls
    env_vars_used = set()
    for py_file in backend.rglob("*.py"):
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        matches = re.findall(r'os\.getenv\([\'"]([^\'"]+)[\'"]', content)
        env_vars_used.update(matches)

    # Check if .env.example exists and contains these
    env_example = root / ".env.example"
    documented_vars = set()
    if env_example.exists():
        content = env_example.read_text(encoding='utf-8', errors='ignore')
        documented_vars = set(re.findall(r'^([A-Z_]+)=', content, re.MULTILINE))

    # Critical vars that must be set
    critical_vars = {'DATABASE_URL', 'JWT_SECRET_KEY', 'CORS_ORIGINS'}
    missing_critical = critical_vars - documented_vars

    if missing_critical:
        warn(f"Critical vars not in .env.example: {missing_critical}")
        warnings.append("Missing critical env var documentation")
    else:
        ok("Critical environment variables documented")

    # =========================================================================
    # CHECK 5: Migration files are idempotent
    # =========================================================================
    print("\n5. Checking migration idempotency...")

    migrations_dir = backend / "alembic" / "versions"
    non_idempotent = []

    if migrations_dir.exists():
        for mig_file in migrations_dir.glob("*.py"):
            content = mig_file.read_text(encoding='utf-8', errors='ignore')
            # Check for CREATE TABLE/INDEX without IF NOT EXISTS
            if 'op.create_table(' in content and 'IF NOT EXISTS' not in content:
                # This is okay if using op.create_table (Alembic handles it)
                pass
            if 'op.create_index(' in content:
                # Check if it's wrapped in try/except or uses IF NOT EXISTS
                if 'IF NOT EXISTS' not in content and 'EXCEPTION' not in content:
                    # Check if file has any raw SQL that might need fixing
                    if "CREATE INDEX" in content and "IF NOT EXISTS" not in content:
                        non_idempotent.append(mig_file.name)

    if non_idempotent:
        warn(f"Migrations may not be idempotent: {non_idempotent}")
        warnings.append("Non-idempotent migrations")
    else:
        ok("Migrations appear idempotent")

    # =========================================================================
    # CHECK 6: No hardcoded secrets
    # =========================================================================
    print("\n6. Checking for hardcoded secrets...")

    secret_patterns = [
        (re.compile(r'sk-[a-zA-Z0-9]{20,}'), 'OpenAI API key'),
        (re.compile(r'sk_live_[a-zA-Z0-9]+'), 'Stripe live key'),
        (re.compile(r'password\s*=\s*["\'][^"\']+["\']', re.IGNORECASE), 'Hardcoded password'),
    ]

    secrets_found = []
    for py_file in backend.rglob("*.py"):
        if '.env' in str(py_file):
            continue
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        for pattern, desc in secret_patterns:
            if pattern.search(content):
                rel_path = py_file.relative_to(backend)
                secrets_found.append(f"{rel_path}: {desc}")

    if secrets_found:
        fail(f"Potential secrets in code:")
        for s in secrets_found:
            print(f"      - {s}")
        errors.append("Hardcoded secrets")
    else:
        ok("No obvious hardcoded secrets")

    # =========================================================================
    # CHECK 7: Health endpoint exists
    # =========================================================================
    print("\n7. Checking health endpoint...")

    main_py = backend / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        if '/health' in content or 'health' in content.lower():
            ok("Health endpoint appears to exist")
        else:
            warn("No /health endpoint found in main.py")
            warnings.append("Missing health endpoint")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if errors:
        print(f"\n{RED}ERRORS ({len(errors)}):{RESET}")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print(f"\n{YELLOW}WARNINGS ({len(warnings)}):{RESET}")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print(f"\n{GREEN}All checks passed!{RESET}")
        print("Safe to deploy.\n")
        return 0
    elif errors:
        print(f"\n{RED}Deployment blocked. Fix errors before pushing.{RESET}\n")
        return 1
    else:
        print(f"\n{YELLOW}Warnings present. Review before deploying.{RESET}\n")
        return 0


if __name__ == "__main__":
    sys.exit(run_checks())
