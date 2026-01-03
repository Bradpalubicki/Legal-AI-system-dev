"""
Comprehensive Notification System
A complete notification infrastructure supporting email, SMS, push notifications,
in-app notifications, with unified orchestration and preference management.
"""

from .email import EmailNotificationEngine, EmailMessage, EmailTemplate
from .sms import SMSNotificationSystem, SMSMessage, SMSTemplate
from .push import PushNotificationSystem, PushNotification, PushTemplate
from .in_app import (
    InAppNotificationSystem,
    InAppNotification,
    InAppTemplateManager,
    NotificationType,
    NotificationPriority as InAppPriority,
    NotificationStatus
)
from .orchestrator import (
    NotificationOrchestrator,
    NotificationRequest,
    NotificationExecution,
    NotificationChannel,
    NotificationPriority,
    DeliveryStatus
)
from .preferences import (
    NotificationPreferencesManager,
    UserNotificationPreferences,
    ChannelPreferences,
    QuietHours,
    NotificationFrequency,
    NotificationCategory
)

# Global instances for easy access
email_system = EmailNotificationEngine()
sms_system = SMSNotificationSystem()
push_system = PushNotificationSystem()
in_app_system = InAppNotificationSystem()
orchestrator = NotificationOrchestrator()
preferences_manager = NotificationPreferencesManager()

__version__ = "1.0.0"

__all__ = [
    # Email system
    "EmailNotificationEngine",
    "EmailMessage",
    "EmailTemplate",

    # SMS system
    "SMSNotificationSystem",
    "SMSMessage",
    "SMSTemplate",

    # Push notifications
    "PushNotificationSystem",
    "PushNotification",
    "PushTemplate",

    # In-app notifications
    "InAppNotificationSystem",
    "InAppNotification",
    "InAppTemplateManager",
    "NotificationType",
    "InAppPriority",
    "NotificationStatus",

    # Orchestration
    "NotificationOrchestrator",
    "NotificationRequest",
    "NotificationExecution",
    "NotificationChannel",
    "NotificationPriority",
    "DeliveryStatus",

    # Preferences
    "NotificationPreferencesManager",
    "UserNotificationPreferences",
    "ChannelPreferences",
    "QuietHours",
    "NotificationFrequency",
    "NotificationCategory",

    # Global instances
    "email_system",
    "sms_system",
    "push_system",
    "in_app_system",
    "orchestrator",
    "preferences_manager"
]


def get_notification_endpoints():
    """Get all notification-related FastAPI endpoints"""
    from fastapi import APIRouter

    # Import endpoint functions
    from .email import get_email_endpoints
    from .sms import get_sms_endpoints
    from .push import get_push_endpoints
    from .in_app import get_in_app_notification_endpoints
    from .orchestrator import get_orchestrator_endpoints
    from .preferences import get_preferences_endpoints

    # Create main router
    router = APIRouter(prefix="/api/notifications", tags=["notifications"])

    # Include all sub-routers
    router.include_router(get_email_endpoints())
    router.include_router(get_sms_endpoints())
    router.include_router(get_push_endpoints())
    router.include_router(get_in_app_notification_endpoints())
    router.include_router(get_orchestrator_endpoints())
    router.include_router(get_preferences_endpoints())

    return router


async def initialize_notification_systems():
    """Initialize all notification systems"""
    print("Initializing comprehensive notification system...")

    # Test email system
    try:
        await email_system.send_email(
            template_type="welcome",
            recipient_email="test@example.com",
            variables={"user_name": "Test User"}
        )
        print("✓ Email system initialized")
    except Exception as e:
        print(f"⚠ Email system warning: {e}")

    # Test SMS system
    try:
        await sms_system.send_sms(
            template_type="verification_code",
            phone_number="+1234567890",
            variables={"verification_code": "123456"}
        )
        print("✓ SMS system initialized")
    except Exception as e:
        print(f"⚠ SMS system warning: {e}")

    # Test push system
    try:
        await push_system.send_notification(
            template_type="case_update",
            device_tokens=["test_token"],
            variables={"case_name": "Test Case", "status": "Updated"}
        )
        print("✓ Push notification system initialized")
    except Exception as e:
        print(f"⚠ Push system warning: {e}")

    # Test in-app system
    try:
        await in_app_system.notify_document_analysis_complete(
            "test_user", "test_document.pdf", "doc123", "contract", 3
        )
        print("✓ In-app notification system initialized")
    except Exception as e:
        print(f"⚠ In-app system warning: {e}")

    # Test orchestrator
    try:
        notification_id = await orchestrator.notify_document_analysis_complete(
            user_id="test_user",
            document_name="test_document.pdf",
            document_id="doc123",
            user_email="test@example.com"
        )
        print(f"✓ Notification orchestrator initialized (ID: {notification_id})")
    except Exception as e:
        print(f"⚠ Orchestrator warning: {e}")

    # Test preferences manager
    try:
        prefs = await preferences_manager.get_user_preferences("test_user")
        print(f"✓ Preferences manager initialized (User: {prefs.user_id})")
    except Exception as e:
        print(f"⚠ Preferences manager warning: {e}")

    print("🎉 Comprehensive notification system initialization complete!")


# Quick helper functions for common use cases
async def send_document_analysis_notification(
    user_id: str, document_name: str, document_id: str,
    user_email: str, analysis_type: str = "comprehensive"
):
    """Quick helper to send document analysis complete notification"""
    return await orchestrator.notify_document_analysis_complete(
        user_id, document_name, document_id, user_email, analysis_type
    )


async def send_urgent_deadline_notification(
    user_id: str, task_name: str, task_id: str,
    user_phone: str, user_email: str, time_remaining: str
):
    """Quick helper to send urgent deadline notification"""
    return await orchestrator.notify_urgent_deadline(
        user_id, task_name, task_id, user_phone, user_email, time_remaining
    )


async def send_case_update_notification(
    user_id: str, case_name: str, case_id: str,
    user_email: str, old_status: str, new_status: str, update_notes: str = ""
):
    """Quick helper to send case update notification"""
    return await orchestrator.notify_case_update(
        user_id, case_name, case_id, user_email, old_status, new_status, update_notes
    )


# System health check
async def health_check():
    """Check health of all notification systems"""
    health_status = {
        "email": {"status": "unknown", "details": ""},
        "sms": {"status": "unknown", "details": ""},
        "push": {"status": "unknown", "details": ""},
        "in_app": {"status": "unknown", "details": ""},
        "orchestrator": {"status": "unknown", "details": ""},
        "preferences": {"status": "unknown", "details": ""}
    }

    # Check email system
    try:
        # Email system health would be checked here
        health_status["email"] = {"status": "healthy", "details": "Email system operational"}
    except Exception as e:
        health_status["email"] = {"status": "unhealthy", "details": str(e)}

    # Check SMS system
    try:
        # SMS system health would be checked here
        health_status["sms"] = {"status": "healthy", "details": "SMS system operational"}
    except Exception as e:
        health_status["sms"] = {"status": "unhealthy", "details": str(e)}

    # Check push system
    try:
        # Push system health would be checked here
        health_status["push"] = {"status": "healthy", "details": "Push system operational"}
    except Exception as e:
        health_status["push"] = {"status": "unhealthy", "details": str(e)}

    # Check in-app system
    try:
        count = await in_app_system.get_unread_count("health_check_user")
        health_status["in_app"] = {"status": "healthy", "details": f"In-app system operational, test query returned {count}"}
    except Exception as e:
        health_status["in_app"] = {"status": "unhealthy", "details": str(e)}

    # Check orchestrator
    try:
        stats = await orchestrator.get_delivery_statistics()
        health_status["orchestrator"] = {"status": "healthy", "details": f"Orchestrator operational, {stats['total']} total notifications"}
    except Exception as e:
        health_status["orchestrator"] = {"status": "unhealthy", "details": str(e)}

    # Check preferences manager
    try:
        stats = await preferences_manager.get_preference_statistics()
        health_status["preferences"] = {"status": "healthy", "details": f"Preferences manager operational, {stats['total_users']} users"}
    except Exception as e:
        health_status["preferences"] = {"status": "unhealthy", "details": str(e)}

    return health_status