# -*- coding: utf-8 -*-
"""
PACER Integration - Complete Example

This example demonstrates the complete PACER integration workflow:
1. Authentication with token caching
2. Case searching
3. Party searching
4. Document downloading with cost tracking
5. MFA handling
6. Error handling and retries

Usage:
    python -m src.pacer.example_integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pacer.auth.authenticator import (
    PACERAuthenticator,
    PACERAuthenticationError,
    PACERMFARequiredError
)
from src.pacer.auth.token_manager import TokenManager
from src.pacer.auth.mfa_handler import MFAHandler
from src.pacer.api.pcl_client import PCLClient, PCLAuthenticationError
from src.pacer.downloads.cost_tracker import CostTracker, PACEROperation
from src.pacer.downloads.document_fetcher import DocumentFetcher
from src.pacer.models.pacer_models import CaseSearchCriteria


async def example_authentication():
    """Example 1: Authenticate with PACER"""
    print("\n" + "="*70)
    print("EXAMPLE 1: PACER Authentication")
    print("="*70)

    # Load credentials from environment
    username = os.getenv("PACER_USERNAME")
    password = os.getenv("PACER_PASSWORD")
    client_code = os.getenv("PACER_CLIENT_CODE")

    if not username or not password:
        print("❌ Please set PACER_USERNAME and PACER_PASSWORD in .env")
        return None

    # Initialize authenticator
    authenticator = PACERAuthenticator(environment="production")

    try:
        print(f"🔐 Authenticating as {username}...")

        result = await authenticator.authenticate(
            username=username,
            password=password,
            client_code=client_code
        )

        print("✅ Authentication successful!")
        print(f"   Token: {result['nextGenCSO'][:30]}...")
        print(f"   Cached: {result.get('cached', False)}")
        print(f"   Environment: {result.get('environment')}")

        return result['nextGenCSO']

    except PACERMFARequiredError:
        print("⚠️  MFA required - handling with MFAHandler...")
        return await example_mfa_authentication(authenticator, username, password, client_code)

    except PACERAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return None

    finally:
        await authenticator.close()


async def example_mfa_authentication(authenticator, username, password, client_code):
    """Example 2: Authentication with MFA"""
    print("\n" + "="*70)
    print("EXAMPLE 2: MFA Authentication")
    print("="*70)

    mfa_handler = MFAHandler()

    try:
        result = await mfa_handler.authenticate_with_mfa(
            authenticator=authenticator,
            username=username,
            password=password,
            client_code=client_code,
            max_attempts=3
        )

        print("✅ MFA authentication successful!")
        return result['nextGenCSO']

    except PACERAuthenticationError as e:
        print(f"❌ MFA authentication failed: {e}")
        return None


async def example_case_search(token: str):
    """Example 3: Search for cases"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Case Search")
    print("="*70)

    client = PCLClient(auth_token=token, environment="production")

    try:
        print("🔍 Searching for cases in NYSD filed in 2024...")

        results = await client.search_cases(
            court="nysd",
            filed_from="2024-01-01",
            page=1,
            page_size=5
        )

        print(f"✅ Found {results.total_count} total cases")
        print(f"   Showing page {results.page} ({len(results.results)} results)")

        for i, case in enumerate(results.results[:3], 1):
            print(f"\n   {i}. Case Number: {case.get('caseNumber', 'N/A')}")
            print(f"      Title: {case.get('caseTitle', 'N/A')}")
            print(f"      Filed: {case.get('dateFiled', 'N/A')}")
            print(f"      Judge: {case.get('judgeName', 'N/A')}")

        # Get client stats
        stats = client.get_stats()
        print(f"\n📊 PCL Client Statistics:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Success rate: {stats['success_rate']}%")

        return results.results[0] if results.results else None

    except PCLAuthenticationError:
        print("❌ Token expired or invalid")
        return None

    except Exception as e:
        print(f"❌ Search error: {e}")
        return None


async def example_party_search(token: str):
    """Example 4: Search for parties"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Party Search")
    print("="*70)

    client = PCLClient(auth_token=token, environment="production")

    try:
        print("🔍 Searching for parties named 'Smith'...")

        results = await client.search_parties(
            party_name="Smith",
            court="nysd",
            page_size=5
        )

        print(f"✅ Found {results.total_count} total parties")

        for i, party in enumerate(results.results[:3], 1):
            print(f"\n   {i}. Party: {party.get('partyName', 'N/A')}")
            print(f"      Role: {party.get('partyRole', 'N/A')}")
            print(f"      Case: {party.get('caseNumber', 'N/A')}")

    except Exception as e:
        print(f"❌ Party search error: {e}")


async def example_pagination(token: str):
    """Example 5: Automatic pagination"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Automatic Pagination")
    print("="*70)

    client = PCLClient(auth_token=token, environment="production")

    try:
        print("🔄 Fetching cases with auto-pagination (max 2 pages)...")

        case_count = 0
        async for case in client.search_cases_all_pages(
            court="nysd",
            filed_from="2024-01-01",
            page_size=10,
            max_pages=2
        ):
            case_count += 1
            if case_count <= 3:
                print(f"   {case_count}. {case.get('caseNumber')}: {case.get('caseTitle')}")

        print(f"✅ Fetched {case_count} cases across pages")

    except Exception as e:
        print(f"❌ Pagination error: {e}")


async def example_cost_tracking(token: str):
    """Example 6: Cost tracking"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Cost Tracking & Management")
    print("="*70)

    tracker = CostTracker(daily_limit=50.00, monthly_limit=500.00)

    # Estimate costs
    print("💰 Cost Estimates:")
    print(f"   Case search: ${tracker.estimate_cost(PACEROperation.CASE_SEARCH):.2f}")
    print(f"   10-page document: ${tracker.estimate_cost(PACEROperation.DOCUMENT_DOWNLOAD, 10):.2f}")
    print(f"   50-page document: ${tracker.estimate_cost(PACEROperation.DOCUMENT_DOWNLOAD, 50):.2f}")

    # Check affordability
    can_afford, cost, reason = await tracker.can_afford_operation(
        PACEROperation.DOCUMENT_DOWNLOAD,
        pages=20,
        user_id="example_user"
    )

    print(f"\n✅ Can afford 20-page document? {can_afford}")
    print(f"   Estimated cost: ${cost:.2f}")
    print(f"   Reason: {reason}")

    # Record some operations
    await tracker.record_cost(
        operation=PACEROperation.DOCUMENT_DOWNLOAD,
        user_id="example_user",
        pages=5,
        case_id="1:24-cv-00001",
        court="nysd",
        description="Downloaded complaint"
    )

    # Get usage report
    report = tracker.get_usage_report(user_id="example_user")
    print(f"\n📊 Usage Report:")
    print(f"   Total cost: ${report['total_cost']:.2f}")
    print(f"   Total pages: {report['total_pages']}")
    print(f"   Total operations: {report['total_operations']}")
    print(f"   Daily spending: ${report['daily_spending']:.2f} / ${report['daily_limit']:.2f}")
    print(f"   Daily remaining: ${report['daily_remaining']:.2f}")
    print(f"   Monthly spending: ${report['monthly_spending']:.2f} / ${report['monthly_limit']:.2f}")

    return tracker


async def example_document_download(token: str, tracker: CostTracker):
    """Example 7: Download documents with cost tracking"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Document Download (Simulated)")
    print("="*70)

    fetcher = DocumentFetcher(
        auth_token=token,
        cost_tracker=tracker,
        storage_path=Path("./storage/pacer_documents")
    )

    print("📥 Document Fetcher initialized")
    print(f"   Storage path: {fetcher.storage_path}")
    print(f"   Cost tracking: {'Enabled' if tracker else 'Disabled'}")

    # NOTE: This would require actual document URLs from PACER
    print("\n⚠️  Document download requires actual PACER document URLs")
    print("   This example shows the workflow only")

    # Show stats
    stats = fetcher.get_stats()
    print(f"\n📊 Fetcher Statistics:")
    print(f"   Total downloads: {stats['total_downloads']}")
    print(f"   Success rate: {stats['success_rate']}%")
    print(f"   Total cost: ${stats['total_cost']:.2f}")


async def example_token_management():
    """Example 8: Token lifecycle management"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Token Management")
    print("="*70)

    manager = TokenManager()

    # Store a token
    await manager.store_token(
        username="example_user",
        token="example_token_12345"
    )
    print("✅ Token stored for example_user")

    # Retrieve token
    token = await manager.get_token("example_user")
    print(f"✅ Retrieved token: {token[:20]}...")

    # Get token info
    info = manager.get_token_info("example_user")
    if info:
        print(f"\n📋 Token Info:")
        print(f"   Created: {info.created_at}")
        print(f"   Last used: {info.last_used}")
        print(f"   Use count: {info.use_count}")
        print(f"   Valid: {info.is_valid}")
        print(f"   Should refresh: {info.should_refresh()}")

    # Get stats
    stats = manager.get_stats()
    print(f"\n📊 Token Manager Stats:")
    print(f"   Total tokens: {stats['total_tokens']}")
    print(f"   Valid tokens: {stats['valid_tokens']}")
    print(f"   Expired tokens: {stats['expired_tokens']}")


async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("PACER INTEGRATION - COMPLETE EXAMPLE")
    print("="*70)
    print("\nThis example demonstrates the full PACER integration workflow.")
    print("Make sure you have set PACER credentials in .env file.")

    # Example 1: Authentication
    token = await example_authentication()

    if not token:
        print("\n❌ Authentication failed - cannot continue with other examples")
        print("   Please check your PACER credentials in .env")
        return

    # Example 3: Case search
    case = await example_case_search(token)

    # Example 4: Party search
    await example_party_search(token)

    # Example 5: Pagination
    await example_pagination(token)

    # Example 6: Cost tracking
    tracker = await example_cost_tracking(token)

    # Example 7: Document download
    await example_document_download(token, tracker)

    # Example 8: Token management
    await example_token_management()

    # Summary
    print("\n" + "="*70)
    print("EXAMPLES COMPLETE")
    print("="*70)
    print("\n✅ All examples executed successfully!")
    print("\nNext steps:")
    print("  1. Review the output above")
    print("  2. Check the source code in src/pacer/example_integration.py")
    print("  3. Integrate these patterns into your application")
    print("  4. Review individual module documentation:")
    print("     - src/pacer/auth/authenticator.py")
    print("     - src/pacer/api/pcl_client.py")
    print("     - src/pacer/downloads/cost_tracker.py")
    print("     - src/pacer/downloads/document_fetcher.py")
    print("     - src/pacer/models/pacer_models.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
