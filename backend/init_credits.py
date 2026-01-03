"""
Initialize Credits System

This script:
1. Creates credit database tables
2. Optionally adds test credits to your account

Run: python init_credits.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.src.core.database import engine, SessionLocal
from app.models.credits import Base as CreditsBase, UserCredits, CreditTransaction, TransactionType

def init_database():
    """Create all credit system tables"""
    print("="*60)
    print("INITIALIZING CREDITS SYSTEM DATABASE")
    print("="*60)

    try:
        # Create tables
        CreditsBase.metadata.create_all(bind=engine)
        print("[OK] Credit system tables created successfully")
        print()
        print("Tables created:")
        print("  - user_credits")
        print("  - credit_transactions")
        print("  - document_purchases")
        print()
        return True
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        return False


def add_test_credits(user_id: int = 1, username: str = "test_user", amount: float = 100.0):
    """Add test credits to a user account"""
    print("="*60)
    print("ADDING TEST CREDITS")
    print("="*60)

    db = SessionLocal()
    try:
        # Get or create user credits
        user_credits = db.query(UserCredits).filter(UserCredits.user_id == user_id).first()

        if not user_credits:
            user_credits = UserCredits(
                user_id=user_id,
                username=username,
                balance=0,
                total_credits_purchased=0,
                total_credits_spent=0
            )
            db.add(user_credits)
            db.flush()
            print(f"[OK] Created new credit account for user {user_id} ({username})")
        else:
            print(f"[OK] Found existing account for user {user_id} ({username})")

        # Add credits
        user_credits.balance += int(amount)
        user_credits.total_credits_purchased += int(amount)

        # Create transaction
        transaction = CreditTransaction(
            user_credits_id=user_credits.id,
            transaction_type=TransactionType.ADMIN_ADJUSTMENT,
            amount=amount,
            balance_after=user_credits.balance,
            description=f"Test credits added: ${amount:.2f}",
            payment_method="admin"
        )
        db.add(transaction)

        db.commit()

        print(f"[OK] Added ${amount:.2f} credits")
        print(f"[OK] New balance: ${user_credits.balance:.2f}")
        print()
        print("="*60)
        print("SUCCESS! Credits added successfully")
        print("="*60)
        print()
        print(f"User ID: {user_id}")
        print(f"Username: {username}")
        print(f"Balance: {user_credits.balance}")
        print(f"Total Purchased: {user_credits.total_credits_purchased}")
        print(f"Total Spent: {user_credits.total_credits_spent}")
        print("="*60)

        return True

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error adding credits: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print()
    print("CREDIT SYSTEM INITIALIZATION")
    print()

    # Initialize database
    if not init_database():
        sys.exit(1)

    # Ask if user wants to add test credits
    print()
    add_credits = input("Would you like to add test credits to an account? (y/n): ").lower().strip()

    if add_credits == 'y':
        print()
        user_id_input = input("Enter user ID (default: 1): ").strip()
        user_id = int(user_id_input) if user_id_input else 1

        username_input = input("Enter username (default: test_user): ").strip()
        username = username_input if username_input else "test_user"

        amount_input = input("Enter credit amount (default: 100.00): ").strip()
        amount = float(amount_input) if amount_input else 100.0

        print()
        if not add_test_credits(user_id, username, amount):
            sys.exit(1)
    else:
        print()
        print("Skipping test credit addition")

    print()
    print("[OK] Initialization complete!")
    print()
    print("You can now:")
    print("1. Start the backend: uvicorn main:app --reload")
    print("2. Access credits API: http://localhost:8000/api/v1/credits/")
    print("3. View API docs: http://localhost:8000/docs")
    print()
