"""
Quick test to verify PACER authentication with test credentials
"""

import asyncio
import sys
sys.path.insert(0, ".")

async def test_pacer_auth():
    from app.src.core.database import SessionLocal
    from app.src.services.pacer_service import PACERService

    db = SessionLocal()

    try:
        service = PACERService(db)

        print("Testing PACER authentication with test credentials...")
        print("Expected behavior: Should auto-enable test mode for @example credentials")

        # This should trigger test mode automatically
        result = await service.authenticate_user(
            user_id=1,  # User created earlier with dev script
            test_mode=True,  # Explicitly enable test mode
            force_refresh=True
        )

        print(f"[OK] Authentication successful!")
        print(f"Token: {result[:50]}..." if result else "No token")

    except Exception as e:
        print(f"[FAIL] Authentication failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_pacer_auth())
