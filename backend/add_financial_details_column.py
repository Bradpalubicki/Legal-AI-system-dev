"""
Quick script to add financial_details column to documents table
"""

from sqlalchemy import text
from app.src.core.database import engine

def add_financial_details_column():
    """Add financial_details JSON column to documents table"""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(documents)"))
            columns = [row[1] for row in result]

            if 'financial_details' in columns:
                print("financial_details column already exists")
                return

            # Add the column
            conn.execute(text("ALTER TABLE documents ADD COLUMN financial_details JSON"))
            conn.commit()
            print("Successfully added financial_details column to documents table")

    except Exception as e:
        print(f"Error adding column: {e}")
        raise

if __name__ == "__main__":
    add_financial_details_column()
