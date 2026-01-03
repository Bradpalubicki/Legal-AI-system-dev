"""
Test DateTime fix for CourtListener monitoring
Tests that we can create monitored cases without DateTime errors
"""

import asyncio
import sys
import os
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

async def test_datetime_fix():
    from app.src.core.database import SessionLocal
    from app.src.services.courtlistener_service import CourtListenerService, parse_date_to_naive_datetime
    from shared.database.models import TrackedDocket, UserDocketMonitor
    from datetime import datetime

    db = SessionLocal()
    all_passed = True

    try:
        service = CourtListenerService(db)

        print("=" * 70)
        print("DATETIME FIX VERIFICATION TEST")
        print("=" * 70)
        print()

        # Test: Create TrackedDocket with date string (like CourtListener API returns)
        print("TEST 1: Create TrackedDocket with simulated CourtListener data")
        print("-" * 70)
        try:
            # Simulate CourtListener API response with date strings
            # Use parse_date_to_naive_datetime to convert string to datetime (like the service does)
            test_docket_data = {
                "docket_number": "TEST-DATETIME-2025",
                "court_id": "cacd",
                "court_name": "Central District of California",
                "case_name": "Test v. DateTime Fix Verification",
                "courtlistener_docket_id": 88888888,
                "date_filed": parse_date_to_naive_datetime("2023-05-04"),  # Parse string to datetime
                "courtlistener_last_fetch": datetime.utcnow(),
            }

            # Try to create the docket
            test_docket = TrackedDocket(**test_docket_data)
            db.add(test_docket)
            db.flush()

            print(f"[OK] TrackedDocket created successfully!")
            print(f"  - Docket Number: {test_docket.docket_number}")
            print(f"  - Case Name: {test_docket.case_name}")
            print(f"  - Date Filed: {test_docket.date_filed}")
            print(f"  - Created At: {test_docket.created_at}")
            print()

        except Exception as e:
            print(f"[FAIL] TrackedDocket creation failed: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            print()

        # Test 2: Create UserDocketMonitor
        print("TEST 2: Create UserDocketMonitor with DateTime fields")
        print("-" * 70)
        try:
            test_monitor = UserDocketMonitor(
                user_id="test-datetime-user",
                tracked_docket_id=test_docket.id,
                case_name=test_docket.case_name,
                docket_number=test_docket.docket_number,
                court_name=test_docket.court_name,
                courtlistener_docket_id=test_docket.courtlistener_docket_id,
                started_monitoring_at=datetime.utcnow(),
                last_checked_at=datetime.utcnow()
            )
            db.add(test_monitor)
            db.commit()

            print(f"[OK] UserDocketMonitor created successfully!")
            print(f"  - User ID: {test_monitor.user_id}")
            print(f"  - Started Monitoring: {test_monitor.started_monitoring_at}")
            print(f"  - Last Checked: {test_monitor.last_checked_at}")
            print()

        except Exception as e:
            print(f"[FAIL] UserDocketMonitor creation failed: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            print()

        # Test 3: Query back the data
        print("TEST 3: Query monitored cases")
        print("-" * 70)
        try:
            monitors = await service.get_monitored_cases_list("test-datetime-user")
            print(f"[OK] Query successful - found {len(monitors)} case(s)")
            if monitors:
                m = monitors[0]
                print(f"  - Case: {m['case_name']}")
                print(f"  - Started: {m['started_monitoring']}")
                print(f"  - Last Checked: {m['last_checked']}")
            print()

        except Exception as e:
            print(f"[FAIL] Query failed: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            print()

        # Cleanup
        print("TEST 4: Cleanup")
        print("-" * 70)
        try:
            db.query(UserDocketMonitor).filter(
                UserDocketMonitor.user_id == "test-datetime-user"
            ).delete()
            db.query(TrackedDocket).filter(
                TrackedDocket.courtlistener_docket_id == 88888888
            ).delete()
            db.commit()
            print(f"[OK] Cleanup successful")
            print()

        except Exception as e:
            print(f"[FAIL] Cleanup failed: {e}")
            all_passed = False
            print()

        # Final summary
        print("=" * 70)
        if all_passed:
            print("[SUCCESS] DateTime fix is working correctly!")
            print()
            print("Key findings:")
            print("  - TrackedDocket can be created with DateTime fields")
            print("  - UserDocketMonitor can be created with DateTime fields")
            print("  - No timezone-aware DateTime errors")
            print("  - All database operations successful")
        else:
            print("[FAILED] Some tests failed - review errors above")
        print("=" * 70)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_datetime_fix())
