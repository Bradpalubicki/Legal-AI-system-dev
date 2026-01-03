"""Check if users exist in enhanced_auth.db"""
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from backend.app.models.user import User

# Check enhanced_auth.db
engine = create_engine('sqlite:///./enhanced_auth.db')
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"Tables in enhanced_auth.db: {len(tables)}")
print(tables)

if 'users' in tables:
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        users = db.query(User).all()
        print(f"\nUsers in enhanced_auth.db: {len(users)}")
        for u in users:
            print(f"  - {u.email} (role: {u.role.value if u.role else None})")
    except Exception as e:
        print(f"Error querying users: {e}")
    finally:
        db.close()
else:
    print("\n'users' table not found in enhanced_auth.db")
