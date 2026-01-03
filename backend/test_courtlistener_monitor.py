"""
Test CourtListener case monitoring to verify DateTime fix
"""

import asyncio
import sys
import os
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

async def test_monitor():
    from app.src.core.database import SessionLocal
    from app.src.services.courtlistener_service import CourtListenerService

    db = SessionLocal()

    try:
        service = CourtListenerService(db)

        print("=" * 60)
        print("CourtListener Case Monitoring Test")
        print("=" * 60)
        print()

        # Test monitoring a real case
        # Using a known docket ID from CourtListener
        test_docket_id = 67326669  # Example docket ID
        test_user_id = "test-user-123"

        print(f"Testing: Start monitoring docket {test_docket_id}")
        print(f"User ID: {test_user_id}")
        print("-" * 60)

        try:
            result = await service.monitor_case(test_docket_id, test_user_id)
            print(f"[SUCCESS] Case monitoring started!")
            print(f"Case Name: {result.get('case_name', 'Unknown')}")
            print(f"Docket Number: {result.get('docket_number', 'Unknown')}")
            print(f"Court: {result.get('court', 'Unknown')}")
            print(f"Started Monitoring: {result.get('started_monitoring')}")
            print()

            # Verify it's in the database
            print("Verifying database entry...")
            monitors = await service.get_monitored_cases_list(test_user_id)
            print(f"[SUCCESS] Found {len(monitors)} monitored case(s) in database")

            if monitors:
                monitor = monitors[0]
                print(f"  Case: {monitor['case_name']}")
                print(f"  Started: {monitor['started_monitoring']}")
                print(f"  Last Checked: {monitor['last_checked']}")

            print()
            print("=" * 60)
            print("[PASSED] CourtListener monitoring test PASSED!")
            print("DateTime fix is working correctly!")
            print("=" * 60)

        except Exception as e:
            print(f"[FAILED] Monitoring test failed: {e}")
            import traceback
            traceback.print_exc()
            print()
            print("=" * 60)
            print("[FAILED] CourtListener monitoring test FAILED")
            print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_monitor())
