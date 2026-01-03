"""
Test Email Notification
Sends a test email to verify SMTP configuration
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from root .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.services.email_notification_service import email_notification_service


async def test_email():
    """Send a test email notification"""
    print("=" * 80)
    print("EMAIL NOTIFICATION TEST")
    print("=" * 80)

    # Check configuration
    print(f"\nSMTP Configuration:")
    print(f"  Host: {email_notification_service.smtp_host}")
    print(f"  Port: {email_notification_service.smtp_port}")
    print(f"  User: {email_notification_service.smtp_user}")
    print(f"  From: {email_notification_service.from_email}")
    print(f"  Enabled: {email_notification_service.email_enabled}")
    print(f"  Configured: {email_notification_service.is_configured()}")

    if not email_notification_service.is_configured():
        print("\nERROR: Email not configured!")
        print("Please check your .env file")
        return

    # Test email data
    test_documents = [
        {
            "document_number": 123,
            "short_description": "Motion to Dismiss",
            "description": "Defendant's Motion to Dismiss Case",
            "is_available": True,
            "case_name": "NUMALE CORPORATION",
            "court": "Nevada Bankruptcy Court"
        },
        {
            "document_number": 124,
            "short_description": "Response to Motion",
            "description": "Plaintiff's Response to Motion to Dismiss",
            "is_available": False,
        }
    ]

    print("\n" + "=" * 80)
    print("SENDING TEST EMAIL...")
    print("=" * 80)

    result = email_notification_service.send_new_documents_notification(
        to_email="kobrielmaier@gmail.com",
        docket_id=69566281,
        case_name="NUMALE CORPORATION (TEST)",
        document_count=2,
        documents=test_documents,
        court="Nevada Bankruptcy Court"
    )

    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)
    print(f"Success: {result.get('success')}")
    print(f"Sent: {result.get('sent')}")

    if result.get('error'):
        print(f"ERROR: {result.get('error')}")
    else:
        print(f"Email sent to: {result.get('to_email')}")
        print(f"Sent at: {result.get('sent_at')}")
        print("\nCheck your inbox at kobrielmaier@gmail.com!")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_email())
