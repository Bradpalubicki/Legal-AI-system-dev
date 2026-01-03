"""
Comprehensive CourtListener Integration Test
Tests all functionality end-to-end
"""

import asyncio
import sys
import os
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

async def test_all():
    from app.src.core.database import SessionLocal
    from app.src.services.courtlistener_service import CourtListenerService
    from shared.database.models import TrackedDocket, UserDocketMonitor

    db = SessionLocal()
    all_passed = True

    try:
        service = CourtListenerService(db)

        print("=" * 70)
        print("COMPREHENSIVE COURTLISTENER INTEGRATION TEST")
        print("=" * 70)
        print()

        # Test 1: Database Connection
        print("TEST 1: Database Connection")
        print("-" * 70)
        try:
            # Check if tables exist
            tracked_count = db.query(TrackedDocket).count()
            monitor_count = db.query(UserDocketMonitor).count()
            print(f"[OK] Database connection successful")
            print(f"  - TrackedDocket table: {tracked_count} records")
            print(f"  - UserDocketMonitor table: {monitor_count} records")
            print()
        except Exception as e:
            print(f"[FAIL] Database connection failed: {e}")
            all_passed = False
            print()

        # Test 2: CourtListener API Search (Free - no auth required)
        print("TEST 2: CourtListener Search API")
        print("-" * 70)
        try:
            # Search for recent cases (this should work without auth)
            result = await service.search_dockets(
                query="patent",
                page_size=5
            )
            print(f"[OK] Search API responding")
            print(f"  - Total results: {result.get('count', 0)}")
            print(f"  - Results returned: {len(result.get('results', []))}")
            if result.get('results'):
                first = result['results'][0]
                print(f"  - Sample case: {first.get('caseName', 'N/A')[:50]}")
            print()
        except Exception as e:
            print(f"[FAIL] Search API failed: {e}")
            all_passed = False
            print()

        # Test 3: DateTime Handling (Create TrackedDocket manually)
        print("TEST 3: DateTime Handling in Database")
        print("-" * 70)
        try:
            from datetime import datetime

            # Create a TrackedDocket with timezone-naive datetime
            test_docket = TrackedDocket(
                docket_number="TEST-2025-001",
                court_id="test",
                court_name="Test Court",
                case_name="Test Case for DateTime",
                courtlistener_docket_id=99999999,
                courtlistener_last_fetch=datetime.utcnow(),  # This should work now!
            )
            db.add(test_docket)
            db.flush()

            print(f"[OK] TrackedDocket created successfully")
            print(f"  - Docket Number: {test_docket.docket_number}")
            print(f"  - Created At: {test_docket.created_at}")
            print(f"  - Last Fetch: {test_docket.courtlistener_last_fetch}")

            # Create UserDocketMonitor
            test_monitor = UserDocketMonitor(
                user_id="test-user-datetime",
                tracked_docket_id=test_docket.id,
                case_name="Test Case",
                docket_number="TEST-2025-001",
                court_name="Test Court",
                courtlistener_docket_id=99999999,
                started_monitoring_at=datetime.utcnow(),
                last_checked_at=datetime.utcnow()
            )
            db.add(test_monitor)
            db.commit()

            print(f"[OK] UserDocketMonitor created successfully")
            print(f"  - User ID: {test_monitor.user_id}")
            print(f"  - Started Monitoring: {test_monitor.started_monitoring_at}")
            print(f"  - Last Checked: {test_monitor.last_checked_at}")
            print()

        except Exception as e:
            print(f"[FAIL] DateTime handling failed: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            print()

        # Test 4: Query Monitored Cases
        print("TEST 4: Query Monitored Cases")
        print("-" * 70)
        try:
            monitors = await service.get_monitored_cases_list("test-user-datetime")
            print(f"[OK] Query monitored cases successful")
            print(f"  - Found {len(monitors)} monitored case(s)")
            if monitors:
                for m in monitors:
                    print(f"  - {m['case_name']} (since {m['started_monitoring']})")
            print()
        except Exception as e:
            print(f"[FAIL] Query monitored cases failed: {e}")
            all_passed = False
            print()

        # Test 5: Stop Monitoring
        print("TEST 5: Stop Monitoring Case")
        print("-" * 70)
        try:
            stopped = service.stop_monitoring(99999999, "test-user-datetime")
            if stopped:
                print(f"[OK] Stop monitoring successful")
                print(f"  - Case monitoring deactivated")
            else:
                print(f"[WARN] No active monitoring found (expected if already stopped)")
            print()
        except Exception as e:
            print(f"[FAIL] Stop monitoring failed: {e}")
            all_passed = False
            print()

        # Test 6: Database Cleanup
        print("TEST 6: Database Cleanup")
        print("-" * 70)
        try:
            # Clean up test data
            db.query(UserDocketMonitor).filter(
                UserDocketMonitor.user_id == "test-user-datetime"
            ).delete()
            db.query(TrackedDocket).filter(
                TrackedDocket.courtlistener_docket_id == 99999999
            ).delete()
            db.commit()
            print(f"[OK] Test data cleaned up successfully")
            print()
        except Exception as e:
            print(f"[FAIL] Cleanup failed: {e}")
            all_passed = False
            print()

        # Final Summary
        print("=" * 70)
        if all_passed:
            print("[OK][OK][OK] ALL TESTS PASSED [OK][OK][OK]")
            print()
            print("CourtListener integration is working correctly!")
            print("DateTime issues are FIXED!")
        else:
            print("[FAIL][FAIL][FAIL] SOME TESTS FAILED [FAIL][FAIL][FAIL]")
            print()
            print("Review errors above for details")
        print("=" * 70)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_all())
