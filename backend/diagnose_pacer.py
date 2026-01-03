"""
Diagnose PACER authentication issue
"""
import asyncio
import sys
import os
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

async def diagnose():
    from app.src.core.database import SessionLocal
    from app.models.pacer_credentials import UserPACERCredentials
    from src.pacer.auth.authenticator import PACERAuthenticator

    db = SessionLocal()

    try:
        # Get stored credentials
        creds = db.query(UserPACERCredentials).filter(UserPACERCredentials.user_id == 1).first()

        if not creds:
            print("[ERROR] No PACER credentials found for user 1")
            return

        print("="*60)
        print("PACER Credentials Diagnostic")
        print("="*60)
        print(f"Username: {creds.pacer_username}")
        print(f"Password: {'*' * len(creds.pacer_password) if creds.pacer_password else '[NONE]'}")
        print(f"Environment: {creds.environment}")
        print(f"Is Active: {creds.is_active}")
        print()

        # Check what will be sent
        authenticator = PACERAuthenticator(env=creds.environment)
        base_url = authenticator.base_url
        auth_url = f"{base_url}/services/cso-auth"

        print("Authentication Details:")
        print(f"PACER API URL: {auth_url}")
        print(f"Request will include:")
        print(f"  - loginId: {creds.pacer_username}")
        print(f"  - password: [REDACTED - {len(creds.pacer_password)} characters]")
        print()

        # Try authentication
        print("Attempting authentication...")
        try:
            result = await authenticator.authenticate(
                username=creds.pacer_username,
                password=creds.pacer_password
            )
            print(f"[SUCCESS] Authentication worked!")
            print(f"Token received: {result['nextGenCSO'][:50]}...")
        except Exception as e:
            print(f"[FAILED] {type(e).__name__}: {e}")
            print()
            print("Common causes:")
            print("1. Incorrect password - verify at https://pacer.uscourts.gov/")
            print("2. Account locked/disabled - check PACER account status")
            print("3. Username format - PACER might expect email or different format")
            print("4. Special characters in password need escaping")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
