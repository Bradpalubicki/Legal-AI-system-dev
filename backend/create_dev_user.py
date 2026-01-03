"""Create development user for testing"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from backend.app.src.core.database import SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.utils.auth import hash_password

# Create database session
db = SessionLocal()

try:
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "dev@example.com").first()

    if existing_user:
        print("User already exists!")
        print(f"  Email: {existing_user.email}")
        print(f"  Role: {existing_user.role.value if existing_user.role else 'N/A'}")
    else:
        # Create new admin user
        new_user = User(
            email="dev@example.com",
            username="devuser",
            hashed_password=hash_password("DevPass123!"),
            full_name="Dev User",
            first_name="Dev",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            is_admin=True,
            created_at=datetime.now(timezone.utc)
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print("[SUCCESS] Development user created successfully!")
        print(f"  Email: {new_user.email}")
        print(f"  Username: {new_user.username}")
        print(f"  Password: DevPass123!")
        print(f"  Role: {new_user.role.value}")
        print(f"  ID: {new_user.id}")

except Exception as e:
    print(f"Error creating user: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
