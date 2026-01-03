"""
Simple test to verify user isolation in database queries
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database.models import UserDocketMonitor, TrackedDocket

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), 'legal_ai.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)
Session = sessionmaker(bind=engine)
db = Session()

print("="*80)
print("DATABASE USER ISOLATION TEST")
print("="*80)

# Check all monitors
all_monitors = db.query(UserDocketMonitor).all()
print(f"\nTotal monitors in database: {len(all_monitors)}")

if len(all_monitors) > 0:
    print("\nAll monitors:")
    for m in all_monitors:
        print(f"  - Monitor ID: {m.id}")
        print(f"    User ID: {m.user_id} (type: {type(m.user_id).__name__})")
        print(f"    Case: {m.case_name}")
        print(f"    Is Active: {m.is_active}")
        print()

# Test query for user 1
print("\nQuery test for User 1 (should use integer comparison):")
user1_monitors = db.query(UserDocketMonitor).filter(
    UserDocketMonitor.user_id == 1,  # Integer comparison
    UserDocketMonitor.is_active == True
).all()
print(f"  Found {len(user1_monitors)} monitors for user_id=1 (integer)")

# Test query for user 2
print("\nQuery test for User 2:")
user2_monitors = db.query(UserDocketMonitor).filter(
    UserDocketMonitor.user_id == 2,  # Integer comparison
    UserDocketMonitor.is_active == True
).all()
print(f"  Found {len(user2_monitors)} monitors for user_id=2 (integer)")

# Test with string (should still work after conversion)
print("\nQuery test for User 1 using STRING '1' (simulating JWT token):")
user1_monitors_str = db.query(UserDocketMonitor).filter(
    UserDocketMonitor.user_id == int("1"),  # Convert string to int first
    UserDocketMonitor.is_active == True
).all()
print(f"  Found {len(user1_monitors_str)} monitors for user_id='1' (converted to int)")

# Verify type safety
print("\n" + "="*80)
print("TYPE SAFETY VERIFICATION")
print("="*80)

# Check if there are any non-integer user_ids
invalid_monitors = []
for m in all_monitors:
    if not isinstance(m.user_id, int):
        invalid_monitors.append(m)
        print(f"WARNING: Monitor {m.id} has non-integer user_id: {m.user_id} (type: {type(m.user_id).__name__})")

if len(invalid_monitors) == 0:
    print("OK: All user_id values are integers")
    print("\nISOLATION VERDICT:")
    print("------------------")
    print(f"User 1 monitors: {len(user1_monitors)}")
    print(f"User 2 monitors: {len(user2_monitors)}")

    if len(all_monitors) > 0:
        # Check if each user sees different data
        user1_cases = set(m.case_name for m in user1_monitors)
        user2_cases = set(m.case_name for m in user2_monitors)
        overlap = user1_cases.intersection(user2_cases)

        if len(overlap) == 0:
            print("\nPASS: No case overlap between users - isolation is working!")
        else:
            print(f"\nFAIL: Users share {len(overlap)} case(s) - isolation broken!")
            print(f"  Shared cases: {overlap}")
    else:
        print("\nINFO: No monitors in database yet - isolation cannot be fully tested")
        print("  Add monitors via the frontend to test isolation")
else:
    print(f"\nFAIL: Found {len(invalid_monitors)} monitors with non-integer user_ids!")
    print("  These will break user isolation!")

db.close()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
