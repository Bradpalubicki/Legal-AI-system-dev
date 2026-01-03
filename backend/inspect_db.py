"""
Inspect database structure
"""
import sqlite3
import os
import glob

backend_dir = os.path.dirname(__file__)

# Find all .db files
print("=== FINDING ALL DATABASE FILES ===")
db_files = glob.glob(os.path.join(backend_dir, "*.db"))
for db_file in db_files:
    print(f"Found: {os.path.basename(db_file)}")

# Check legal_ai.db
db_path = os.path.join(backend_dir, 'legal_ai.db')
if os.path.exists(db_path):
    print(f"\n=== INSPECTING legal_ai.db ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"Tables in legal_ai.db:")
    for table in tables:
        print(f"  - {table[0]}")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"    Rows: {count}")

    conn.close()
else:
    print(f"\nlegal_ai.db not found at {db_path}")
