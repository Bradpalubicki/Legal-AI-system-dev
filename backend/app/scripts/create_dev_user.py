"""
Create development/test user accounts
Run once to create dev users for testing
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.utils.auth import hash_password
from app.src.core.database import SessionLocal
from datetime import datetime, timezone


def create_dev_user():
    """Create main development admin user"""
    db = SessionLocal()

    try:
        # Check if exists
        existing = db.query(User).filter(User.email == "dev@example.com").first()

        if existing:
            print("[OK] Dev admin user already exists")
            print(f"   Email: {existing.email}")
            print(f"   Password: DevPass123!")
            print(f"   Role: {existing.role.value}")
            return existing

        # Create new dev user
        dev_user = User(
            email="dev@example.com",
            username="developer",
            first_name="Developer",
            last_name="Account",
            full_name="Developer Account",
            hashed_password=hash_password("DevPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            email_verified_at=datetime.now(timezone.utc),
            is_admin=True,
            is_premium=True,  # Full access for testing
        )

        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)

        print("[OK] Dev admin user created successfully!")
        print(f"   Email: {dev_user.email}")
        print(f"   Password: DevPass123!")
        print(f"   Role: {dev_user.role.value}")
        print(f"   Admin: {dev_user.is_admin}")
        print(f"   Premium: {dev_user.is_premium}")

        return dev_user

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error creating dev user: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def create_test_users():
    """Create test users for different roles"""
    db = SessionLocal()

    test_users = [
        {
            "email": "attorney@example.com",
            "username": "test_attorney",
            "first_name": "Test",
            "last_name": "Attorney",
            "role": UserRole.ATTORNEY,
            "password": "Attorney123!",
            "is_premium": True
        },
        {
            "email": "client@example.com",
            "username": "test_client",
            "first_name": "Test",
            "last_name": "Client",
            "role": UserRole.CLIENT,
            "password": "Client123!",
            "is_premium": False
        },
        {
            "email": "user@example.com",
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.USER,
            "password": "User123!",
            "is_premium": False
        }
    ]

    created = []
    try:
        for user_data in test_users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                print(f"   [INFO] {user_data['email']} - already exists")
                continue

            user = User(
                email=user_data["email"],
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                full_name=f"{user_data['first_name']} {user_data['last_name']}",
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True,
                is_verified=True,
                email_verified_at=datetime.now(timezone.utc),
                is_premium=user_data["is_premium"]
            )

            db.add(user)
            created.append(user_data)

        if created:
            db.commit()
            print(f"\n[OK] Created {len(created)} test users:")
            for user_data in created:
                print(f"   Email: {user_data['email']}")
                print(f"   Password: {user_data['password']}")
                print(f"   Role: {user_data['role'].value}")
                print(f"   Premium: {user_data['is_premium']}")
                print()
        else:
            print("\n   [INFO] All test users already exist")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error creating test users: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def list_dev_users():
    """List all dev/test users"""
    db = SessionLocal()

    try:
        dev_emails = [
            "dev@example.com",
            "attorney@example.com",
            "client@example.com",
            "user@example.com"
        ]

        users = db.query(User).filter(User.email.in_(dev_emails)).all()

        if users:
            print("\nCurrent dev/test users:")
            for user in users:
                print(f"\n   Email: {user.email}")
                print(f"   Username: {user.username}")
                print(f"   Role: {user.role.value}")
                print(f"   Active: {user.is_active}")
                print(f"   Verified: {user.is_verified}")
                print(f"   Premium: {user.is_premium}")
                print(f"   Admin: {user.is_admin}")
        else:
            print("\n   [INFO] No dev users found")

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Legal AI System - Development User Setup")
    print("=" * 60)
    print()

    # Create dev admin user
    print("Creating development admin user...")
    create_dev_user()
    print()

    # Create test users for different roles
    print("Creating test users for different roles...")
    create_test_users()

    # List all dev users
    list_dev_users()

    print("\n" + "=" * 60)
    print("[OK] Setup complete!")
    print("=" * 60)
    print("\nYou can now login with:")
    print("  - dev@example.com / DevPass123! (Admin)")
    print("  - attorney@example.com / Attorney123! (Attorney)")
    print("  - client@example.com / Client123! (Client)")
    print("  - user@example.com / User123! (User)")
    print()
