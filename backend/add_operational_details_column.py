"""
Quick script to add operational_details column to documents table
Run this once to update your database schema
"""

from sqlalchemy import text
from app.src.core.database import engine

def add_operational_details_column():
    """Add operational_details JSON column to documents table"""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(documents)"))
            columns = [row[1] for row in result]

            if 'operational_details' in columns:
                print("✅ operational_details column already exists")
                return

            # Add the column
            conn.execute(text("ALTER TABLE documents ADD COLUMN operational_details JSON"))
            conn.commit()
            print("✅ Successfully added operational_details column to documents table")

    except Exception as e:
        print(f"❌ Error adding column: {e}")
        raise

if __name__ == "__main__":
    add_operational_details_column()
