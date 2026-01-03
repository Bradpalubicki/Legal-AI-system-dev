"""
Clear old Q&A responses from database
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'legal_ai.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing Q&A data
print("\n=== EXISTING Q&A DATA ===")
cursor.execute("""
    SELECT id, question, substr(answer, 1, 100) as answer_preview,
           length(answer) as answer_length, timestamp
    FROM qa_conversations
    ORDER BY id DESC LIMIT 10
""")

for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"Question: {row[1]}")
    print(f"Answer Preview: {row[2]}...")
    print(f"Answer Length: {row[3]} chars")
    print(f"Timestamp: {row[4]}")

# Delete all old Q&A data
print("\n=== CLEARING ALL Q&A DATA ===")
cursor.execute("DELETE FROM qa_conversations")
deleted_count = cursor.rowcount
conn.commit()

print(f"Deleted {deleted_count} old Q&A conversations")

# Verify deletion
cursor.execute("SELECT COUNT(*) FROM qa_conversations")
remaining = cursor.fetchone()[0]
print(f"Remaining Q&A conversations: {remaining}")

conn.close()
print("\n✅ Database cleared successfully!")
