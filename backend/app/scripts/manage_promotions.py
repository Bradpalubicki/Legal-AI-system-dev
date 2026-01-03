"""
Promotion Management Scripts
Quick scripts for common promotional campaigns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta, timezone
from app.src.core.database import SessionLocal
from app.models.feature_flags import FeatureFlag, PromotionalCampaign, UserFeatureOverride
from app.models.user import User


def toggle_credits(enable: bool = True):
    """
    Enable or disable credit requirements globally.

    Usage:
        python manage_promotions.py enable-credits
        python manage_promotions.py disable-credits
    """
    db = SessionLocal()

    try:
        # Get or create credits flag
        flag = db.query(FeatureFlag).filter(
            FeatureFlag.flag_key == "credits_enabled"
        ).first()

        if not flag:
            flag = FeatureFlag(
                flag_name="Credits Enabled",
                flag_key="credits_enabled",
                description="Require users to pay credits for PACER/CourtListener operations",
                category="billing",
                is_enabled=enable
            )
            db.add(flag)
        else:
            flag.is_enabled = enable
            flag.updated_at = datetime.now(timezone.utc)

        db.commit()

        status = "ENABLED" if enable else "DISABLED"
        print(f"[OK] Credits {status} globally")
        print(f"   Users {'WILL' if enable else 'WILL NOT'} be charged for searches")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to toggle credits: {e}")
    finally:
        db.close()


def create_free_month_promo():
    """
    Create "Free for First Month" promotional campaign.

    All users get unlimited searches for 30 days.
    """
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        ends = now + timedelta(days=30)

        campaign = PromotionalCampaign(
            campaign_name="Launch Month - Free Unlimited Searches",
            campaign_code="FREEMONTH",
            campaign_type="unlimited_access",
            is_active=True,
            unlimited_searches=True,
            free_credits=0.0,  # Don't give credits, just unlimited access
            new_users_only=False,
            max_redemptions=None,  # No limit
            starts_at=now,
            ends_at=ends,
            description="Free unlimited PACER searches for our launch month!",
            terms="Valid for 30 days from launch. All users eligible.",
            created_by="admin"
        )

        db.add(campaign)
        db.commit()

        print(f"[OK] Created 'Free Month' promotion")
        print(f"   Code: FREEMONTH")
        print(f"   Benefits: Unlimited searches (no credits required)")
        print(f"   Valid: {now.date()} to {ends.date()}")
        print(f"   Duration: 30 days")
        print()
        print("To activate, users don't need to do anything!")
        print("Credits will be automatically disabled for all users.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create campaign: {e}")
    finally:
        db.close()


def create_signup_bonus():
    """
    Create "$20 Signup Bonus" campaign.

    New users get $20 free credits on signup.
    """
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        ends = now + timedelta(days=90)  # 3 month campaign

        campaign = PromotionalCampaign(
            campaign_name="$20 Signup Bonus",
            campaign_code="WELCOME20",
            campaign_type="free_credits",
            is_active=True,
            unlimited_searches=False,
            free_credits=20.00,
            discount_percentage=0.0,
            new_users_only=True,
            max_redemptions=1000,  # First 1000 users
            starts_at=now,
            ends_at=ends,
            description="Get $20 free credits when you sign up!",
            terms="New users only. First 1000 signups. Credits expire 90 days after signup.",
            created_by="admin"
        )

        db.add(campaign)
        db.commit()

        print(f"[OK] Created '$20 Signup Bonus' promotion")
        print(f"   Code: WELCOME20")
        print(f"   Benefits: $20 free credits")
        print(f"   Eligible: New users only")
        print(f"   Limit: First 1000 signups")
        print(f"   Valid: {now.date()} to {ends.date()}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create campaign: {e}")
    finally:
        db.close()


def grant_unlimited_access(user_email: str, duration_days: int = 30, reason: str = "VIP"):
    """
    Grant specific user unlimited access.

    Usage:
        python manage_promotions.py grant-unlimited attorney@example.com 30 "Beta tester"
    """
    db = SessionLocal()

    try:
        # Find user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"[ERROR] User not found: {user_email}")
            return

        # Set expiry
        expires = datetime.now(timezone.utc) + timedelta(days=duration_days)

        # Create or update override
        override = db.query(UserFeatureOverride).filter(
            UserFeatureOverride.user_id == user.id,
            UserFeatureOverride.flag_key == "unlimited_searches"
        ).first()

        if override:
            override.is_enabled = True
            override.expires_at = expires
            override.reason = reason
            override.updated_at = datetime.now(timezone.utc)
        else:
            override = UserFeatureOverride(
                user_id=user.id,
                flag_key="unlimited_searches",
                is_enabled=True,
                reason=reason,
                expires_at=expires
            )
            db.add(override)

        db.commit()

        print(f"[OK] Granted unlimited access to {user_email}")
        print(f"   User ID: {user.id}")
        print(f"   Duration: {duration_days} days")
        print(f"   Expires: {expires.date()}")
        print(f"   Reason: {reason}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to grant access: {e}")
    finally:
        db.close()


def list_active_campaigns():
    """List all active promotional campaigns"""
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        campaigns = db.query(PromotionalCampaign).filter(
            PromotionalCampaign.is_active == True
        ).all()

        if not campaigns:
            print("[INFO] No active campaigns")
            return

        print(f"\nActive Promotional Campaigns ({len(campaigns)}):\n")
        print("=" * 80)

        for campaign in campaigns:
            is_valid = campaign.is_valid()
            status = "ACTIVE" if is_valid else "INACTIVE"

            print(f"\n{campaign.campaign_name}")
            print(f"   Code: {campaign.campaign_code}")
            print(f"   Status: {status}")
            print(f"   Type: {campaign.campaign_type}")

            if campaign.unlimited_searches:
                print(f"   Benefits: Unlimited searches (no credits required)")
            if campaign.free_credits > 0:
                print(f"   Benefits: ${campaign.free_credits:.2f} free credits")
            if campaign.discount_percentage > 0:
                print(f"   Benefits: {campaign.discount_percentage}% discount")

            print(f"   Valid: {campaign.starts_at.date()} to {campaign.ends_at.date()}")

            if campaign.max_redemptions:
                remaining = campaign.max_redemptions - campaign.current_redemptions
                print(f"   Redemptions: {campaign.current_redemptions}/{campaign.max_redemptions} ({remaining} left)")

            print("-" * 80)

    finally:
        db.close()


def check_credits_status():
    """Check if credits are globally enabled"""
    db = SessionLocal()

    try:
        flag = db.query(FeatureFlag).filter(
            FeatureFlag.flag_key == "credits_enabled"
        ).first()

        if not flag:
            print("[INFO] Credits flag not set (defaults to DISABLED)")
            print("   Run: python manage_promotions.py enable-credits")
            return

        status = "ENABLED" if flag.is_enabled else "DISABLED"
        print(f"[OK] Credits are {status}")

        if flag.is_enabled:
            print("   Users WILL be charged for searches")
            print("   To disable: python manage_promotions.py disable-credits")
        else:
            print("   Users WILL NOT be charged (all searches free)")
            print("   To enable: python manage_promotions.py enable-credits")

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_promotions.py <command>")
        print()
        print("Commands:")
        print("  status                  - Check credits enabled/disabled status")
        print("  enable-credits          - Enable credit requirements globally")
        print("  disable-credits         - Disable credits (make everything free)")
        print("  free-month              - Create 'Free Month' promotion")
        print("  signup-bonus            - Create '$20 Signup Bonus' promotion")
        print("  list-campaigns          - List all active campaigns")
        print("  grant-unlimited <email> <days> <reason> - Grant user unlimited access")
        print()
        print("Examples:")
        print("  python manage_promotions.py status")
        print("  python manage_promotions.py disable-credits")
        print("  python manage_promotions.py free-month")
        print("  python manage_promotions.py grant-unlimited dev@example.com 30 'Beta tester'")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        check_credits_status()
    elif command == "enable-credits":
        toggle_credits(True)
    elif command == "disable-credits":
        toggle_credits(False)
    elif command == "free-month":
        create_free_month_promo()
    elif command == "signup-bonus":
        create_signup_bonus()
    elif command == "list-campaigns":
        list_active_campaigns()
    elif command == "grant-unlimited":
        if len(sys.argv) < 5:
            print("Usage: python manage_promotions.py grant-unlimited <email> <days> <reason>")
            sys.exit(1)
        email = sys.argv[2]
        days = int(sys.argv[3])
        reason = sys.argv[4]
        grant_unlimited_access(email, days, reason)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
