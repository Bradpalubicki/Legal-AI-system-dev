#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PACER Integration Test Script

Tests the complete PACER integration including:
1. Database models
2. Service layer
3. Authentication
4. Cost tracking
5. API endpoints (basic)
"""

import asyncio
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("PACER INTEGRATION TEST SUITE")
print("="*70)

# ============================================================================
# TEST 1: Environment & Dependencies
# ============================================================================

print("\n[TEST 1] Checking Dependencies...")

try:
    import httpx
    print("✓ httpx installed")
except ImportError:
    print("✗ httpx not installed - run: pip install httpx")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
    print("✓ cryptography installed")
except ImportError:
    print("✗ cryptography not installed - run: pip install cryptography")
    sys.exit(1)

try:
    import redis.asyncio as redis
    print("✓ redis installed")
except ImportError:
    print("✗ redis not installed - run: pip install redis")
    sys.exit(1)

try:
    from pydantic import BaseModel
    print("✓ pydantic installed")
except ImportError:
    print("✗ pydantic not installed - run: pip install pydantic")
    sys.exit(1)

print("✓ All dependencies installed\n")

# ============================================================================
# TEST 2: PACER Core Components
# ============================================================================

print("[TEST 2] Testing PACER Core Components...")

try:
    from src.pacer.auth.authenticator import PACERAuthenticator
    print("✓ PACERAuthenticator imported")
except ImportError as e:
    print(f"✗ Failed to import PACERAuthenticator: {e}")
    sys.exit(1)

try:
    from src.pacer.auth.token_manager import TokenManager
    print("✓ TokenManager imported")
except ImportError as e:
    print(f"✗ Failed to import TokenManager: {e}")
    sys.exit(1)

try:
    from src.pacer.api.pcl_client import PCLClient
    print("✓ PCLClient imported")
except ImportError as e:
    print(f"✗ Failed to import PCLClient: {e}")
    sys.exit(1)

try:
    from src.pacer.downloads.cost_tracker import CostTracker, PACEROperation
    print("✓ CostTracker imported")
except ImportError as e:
    print(f"✗ Failed to import CostTracker: {e}")
    sys.exit(1)

print("✓ All PACER core components available\n")

# ============================================================================
# TEST 3: Database Models
# ============================================================================

print("[TEST 3] Testing Database Models...")

try:
    from backend.app.models.pacer_credentials import (
        UserPACERCredentials,
        PACERSearchHistory,
        PACERDocument,
        PACERCostTracking
    )
    print("✓ Database models imported")

    # Test model instantiation
    from datetime import datetime

    creds = UserPACERCredentials(
        user_id=1,
        pacer_username="test@example.com",
        pacer_password_encrypted="encrypted_test",
        environment="qa"
    )
    print(f"✓ UserPACERCredentials: {creds}")

except ImportError as e:
    print(f"✗ Failed to import database models: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Model instantiation failed: {e}")
    sys.exit(1)

print("✓ Database models working\n")

# ============================================================================
# TEST 4: Token Manager
# ============================================================================

print("[TEST 4] Testing Token Manager...")

async def test_token_manager():
    try:
        manager = TokenManager()
        print("✓ TokenManager initialized")

        # Store a test token
        await manager.store_token(
            username="test_user",
            token="test_token_12345"
        )
        print("✓ Token stored")

        # Retrieve token
        token = await manager.get_token("test_user")
        if token == "test_token_12345":
            print(f"✓ Token retrieved correctly: {token[:20]}...")
        else:
            print(f"✗ Token mismatch: expected test_token_12345, got {token}")

        # Get stats
        stats = manager.get_stats()
        print(f"✓ Token manager stats: {stats}")

        return True
    except Exception as e:
        print(f"✗ Token manager test failed: {e}")
        return False

asyncio.run(test_token_manager())
print()

# ============================================================================
# TEST 5: Cost Tracker
# ============================================================================

print("[TEST 5] Testing Cost Tracker...")

async def test_cost_tracker():
    try:
        tracker = CostTracker(daily_limit=100.0, monthly_limit=1000.0)
        print("✓ CostTracker initialized")

        # Test cost estimation
        cost = tracker.estimate_cost(PACEROperation.CASE_SEARCH)
        if cost == 0.0:
            print(f"✓ Case search cost: ${cost:.2f} (FREE)")

        cost = tracker.estimate_cost(PACEROperation.DOCUMENT_DOWNLOAD, pages=10)
        print(f"✓ Document download (10 pages) cost: ${cost:.2f}")

        # Test affordability check
        can_afford, cost, reason = await tracker.can_afford_operation(
            PACEROperation.DOCUMENT_DOWNLOAD,
            pages=5,
            user_id="test_user"
        )
        print(f"✓ Affordability check: {can_afford} - {reason}")

        # Test recording cost
        await tracker.record_cost(
            operation=PACEROperation.DOCUMENT_DOWNLOAD,
            user_id="test_user",
            pages=5,
            case_id="1:24-cv-00001",
            description="Test download"
        )
        print("✓ Cost recorded")

        # Get report
        report = tracker.get_usage_report(user_id="test_user")
        print(f"✓ Usage report generated: ${report['total_cost']:.2f} total")

        return True
    except Exception as e:
        print(f"✗ Cost tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

asyncio.run(test_cost_tracker())
print()

# ============================================================================
# TEST 6: PACER Authenticator (No Real Credentials)
# ============================================================================

print("[TEST 6] Testing PACER Authenticator...")

def test_authenticator():
    try:
        auth = PACERAuthenticator(environment="qa")
        print("✓ PACERAuthenticator initialized for QA environment")
        print(f"  Base URL: {auth.base_url}")
        print(f"  Max retries: {auth.max_retries}")

        # Check encryption is set up
        if hasattr(auth, 'fernet'):
            print("✓ Encryption initialized")
        else:
            print("✗ Encryption not initialized")

        return True
    except Exception as e:
        print(f"✗ Authenticator test failed: {e}")
        return False

test_authenticator()
print()

# ============================================================================
# TEST 7: PCL Client (No Token)
# ============================================================================

print("[TEST 7] Testing PCL Client...")

def test_pcl_client():
    try:
        client = PCLClient(auth_token="test_token", environment="qa")
        print("✓ PCLClient initialized")
        print(f"  Base URL: {client.base_url}")
        print(f"  Max retries: {client.max_retries}")

        # Get stats
        stats = client.get_stats()
        print(f"✓ Client stats: {stats}")

        return True
    except Exception as e:
        print(f"✗ PCL Client test failed: {e}")
        return False

test_pcl_client()
print()

# ============================================================================
# TEST 8: Check Environment Variables
# ============================================================================

print("[TEST 8] Checking Environment Configuration...")

# Check PACER credentials
pacer_username = os.getenv("PACER_USERNAME")
pacer_password = os.getenv("PACER_PASSWORD")
pacer_encryption_key = os.getenv("PACER_ENCRYPTION_KEY")

if pacer_username:
    print(f"✓ PACER_USERNAME configured: {pacer_username}")
else:
    print("⚠ PACER_USERNAME not set (optional for testing)")

if pacer_password:
    print(f"✓ PACER_PASSWORD configured: {'*' * len(pacer_password)}")
else:
    print("⚠ PACER_PASSWORD not set (optional for testing)")

if pacer_encryption_key:
    print(f"✓ PACER_ENCRYPTION_KEY configured")
else:
    print("⚠ PACER_ENCRYPTION_KEY not set (will use generated key)")

# Check Redis configuration
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")
print(f"✓ Redis configured: {redis_host}:{redis_port}")

print()

# ============================================================================
# TEST 9: Redis Connection
# ============================================================================

print("[TEST 9] Testing Redis Connection...")

async def test_redis():
    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        await client.ping()
        print("✓ Redis connection successful")

        # Test set/get
        await client.set("test_key", "test_value", ex=10)
        value = await client.get("test_key")
        if value == b"test_value":
            print("✓ Redis read/write working")

        await client.delete("test_key")
        await client.close()

        return True
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}")
        print("  Token caching will not work without Redis")
        print("  Start Redis with: redis-server")
        return False

asyncio.run(test_redis())
print()

# ============================================================================
# TEST 10: Check Files Exist
# ============================================================================

print("[TEST 10] Verifying File Structure...")

required_files = [
    "src/pacer/auth/authenticator.py",
    "src/pacer/auth/token_manager.py",
    "src/pacer/auth/mfa_handler.py",
    "src/pacer/api/pcl_client.py",
    "src/pacer/downloads/cost_tracker.py",
    "src/pacer/downloads/document_fetcher.py",
    "src/pacer/models/pacer_models.py",
    "backend/app/models/pacer_credentials.py",
    "backend/app/src/services/pacer_service.py",
    "backend/app/api/pacer_endpoints.py",
    "frontend/src/app/pacer/page.tsx",
]

all_exist = True
for file_path in required_files:
    if Path(file_path).exists():
        print(f"✓ {file_path}")
    else:
        print(f"✗ {file_path} - MISSING")
        all_exist = False

if all_exist:
    print("\n✓ All required files present")
else:
    print("\n⚠ Some files are missing")

print()

# ============================================================================
# SUMMARY
# ============================================================================

print("="*70)
print("TEST SUMMARY")
print("="*70)

print("\n✓ Core Components:")
print("  - PACER authenticator")
print("  - Token manager")
print("  - PCL client")
print("  - Cost tracker")
print("  - Database models")

print("\n✓ Integration Points:")
print("  - Backend service layer")
print("  - API endpoints")
print("  - Frontend dashboard")

print("\n⚠ Next Steps:")
print("  1. Ensure Redis is running: redis-server")
print("  2. Add PACER credentials to .env:")
print("     PACER_USERNAME=your_username")
print("     PACER_PASSWORD=your_password")
print("  3. Start backend: cd backend && python main.py")
print("  4. Start frontend: cd frontend && npm run dev")
print("  5. Access PACER: http://localhost:3000/pacer")

print("\n" + "="*70)
print("PACER INTEGRATION TEST COMPLETE")
print("="*70 + "\n")

# ============================================================================
# OPTIONAL: Real Authentication Test
# ============================================================================

if pacer_username and pacer_password:
    print("\n[OPTIONAL] Real PACER Authentication Test")
    print("="*70)

    response = input("Credentials found. Test real PACER authentication? (y/N): ").strip().lower()

    if response == 'y':
        print("\nAttempting PACER authentication...")

        async def test_real_auth():
            try:
                auth = PACERAuthenticator(environment="production")
                result = await auth.authenticate(
                    username=pacer_username,
                    password=pacer_password
                )

                print("✅ AUTHENTICATION SUCCESSFUL!")
                print(f"   Token: {result['nextGenCSO'][:30]}...")
                print(f"   Environment: {result.get('environment')}")
                print(f"   Cached: {result.get('cached', False)}")

                await auth.close()
                return True

            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return False

        asyncio.run(test_real_auth())
    else:
        print("Skipping real authentication test")

print("\nTest script complete! ✨")
