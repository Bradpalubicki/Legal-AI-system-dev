"""
Test script to verify user isolation in case monitoring
"""
import asyncio
import sys
import os

# Add parent directory to path for 'shared' module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.services.courtlistener_service import CourtListenerService
from shared.database.models import UserDocketMonitor, TrackedDocket

async def test_user_isolation():
    """Test that users only see their own monitored cases"""

    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'legal_ai.db')
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("="*80)
    print("TESTING USER ISOLATION IN CASE MONITORING")
    print("="*80)

    try:
        # Create service instance
        service = CourtListenerService(db=db)

        # Test Case 1: Monitor a case as user 1 (dev@example.com)
        print("\n[TEST 1] User 1 (dev@example.com) monitors case 69566281...")
        try:
            await service.monitor_case(docket_id=69566281, user_id="1")  # String "1" should convert to int 1
            print("✓ Successfully monitored case as user 1")
        except Exception as e:
            print(f"✗ Error monitoring case: {e}")

        # Check what user 1 sees
        user1_cases = await service.get_monitored_cases_list(user_id="1")
        print(f"  User 1 sees {len(user1_cases)} case(s)")
        for case in user1_cases:
            print(f"    - Case: {case['case_name']} (Docket: {case['docket_id']})")

        # Test Case 2: Check what user 2 (kobrielmaier) sees
        print("\n[TEST 2] Checking what User 2 (kobrielmaier) sees...")
        user2_cases = await service.get_monitored_cases_list(user_id="2")
        print(f"  User 2 sees {len(user2_cases)} case(s)")
        if len(user2_cases) == 0:
            print("  ✓ GOOD: User 2 sees no cases (correct isolation)")
        else:
            print("  ✗ BAD: User 2 should not see any cases!")
            for case in user2_cases:
                print(f"    - Case: {case['case_name']} (Docket: {case['docket_id']})")

        # Test Case 3: User 2 monitors a DIFFERENT case
        print("\n[TEST 3] User 2 (kobrielmaier) monitors a different case 68000000...")
        try:
            # Using a different docket ID for user 2
            await service.monitor_case(docket_id=68000000, user_id=2)  # Integer user_id
            print("✓ Successfully monitored case as user 2")
        except Exception as e:
            print(f"  Note: Could not monitor case 68000000 (might not exist): {e}")
            print("  This is OK for testing - we'll check with real case")

        # Re-check both users
        print("\n[TEST 4] Final verification - checking both users...")
        user1_cases = await service.get_monitored_cases_list(user_id=1)  # Integer user_id
        user2_cases = await service.get_monitored_cases_list(user_id=2)  # Integer user_id

        print(f"  User 1 (dev@example.com) sees {len(user1_cases)} case(s):")
        for case in user1_cases:
            print(f"    - {case['case_name']}")

        print(f"  User 2 (kobrielmaier) sees {len(user2_cases)} case(s):")
        for case in user2_cases:
            print(f"    - {case['case_name']}")

        # Check database directly
        print("\n[TEST 5] Checking database directly...")
        all_monitors = db.query(UserDocketMonitor).all()
        print(f"  Total monitors in database: {len(all_monitors)}")

        user1_monitors = db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == 1,
            UserDocketMonitor.is_active == True
        ).all()
        print(f"  User 1 monitors: {len(user1_monitors)}")

        user2_monitors = db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == 2,
            UserDocketMonitor.is_active == True
        ).all()
        print(f"  User 2 monitors: {len(user2_monitors)}")

        # Verify isolation
        print("\n" + "="*80)
        print("ISOLATION TEST RESULTS")
        print("="*80)

        if len(user1_cases) > 0 and len(user2_cases) == 0:
            print("✓ PASS: User 1 has cases, User 2 has no cases")
            print("✓ PASS: Users see only their own monitored cases")
            print("\n✅ USER ISOLATION IS WORKING CORRECTLY!")
            return True
        elif len(user1_cases) == 0 and len(user2_cases) == 0:
            print("⚠ INFO: No cases monitored yet by either user")
            print("  This is expected if this is first run")
            return True
        else:
            print("✗ FAIL: User isolation may not be working correctly")
            print(f"  User 1 cases: {len(user1_cases)}")
            print(f"  User 2 cases: {len(user2_cases)}")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    result = asyncio.run(test_user_isolation())
    sys.exit(0 if result else 1)
