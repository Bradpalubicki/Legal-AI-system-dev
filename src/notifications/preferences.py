"""
Notification Preferences and Settings Management
Comprehensive system for managing user notification preferences across all channels
with granular controls, scheduling, and user-friendly management interfaces.
"""

import json
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationFrequency(Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


class NotificationCategory(Enum):
    DOCUMENT_ANALYSIS = "document_analysis"
    DEADLINE_REMINDERS = "deadline_reminders"
    CASE_UPDATES = "case_updates"
    QA_RESPONSES = "qa_responses"
    ATTORNEY_ACTIONS = "attorney_actions"
    SYSTEM_ALERTS = "system_alerts"
    PAYMENTS = "payments"
    SECURITY = "security"
    MARKETING = "marketing"
    COLLABORATION = "collaboration"


@dataclass
class QuietHours:
    """Represents quiet hours for a user"""
    enabled: bool = False
    start_time: str = "22:00"  # 24-hour format
    end_time: str = "08:00"    # 24-hour format
    timezone: str = "UTC"
    exceptions: List[NotificationCategory] = field(default_factory=list)  # Categories that bypass quiet hours

    def is_in_quiet_hours(self, check_time: Optional[datetime] = None) -> bool:
        """Check if given time is within quiet hours"""
        if not self.enabled:
            return False

        if check_time is None:
            check_time = datetime.now()

        current_time = check_time.time()
        start = datetime.strptime(self.start_time, "%H:%M").time()
        end = datetime.strptime(self.end_time, "%H:%M").time()

        if start <= end:
            return start <= current_time <= end
        else:  # Quiet hours span midnight
            return current_time >= start or current_time <= end


@dataclass
class ChannelPreferences:
    """Preferences for a specific notification channel"""
    enabled: bool = True
    categories: Dict[NotificationCategory, bool] = field(default_factory=dict)
    frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    quiet_hours: QuietHours = field(default_factory=QuietHours)
    daily_limit: Optional[int] = None  # Max notifications per day
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default category preferences"""
        if not self.categories:
            # Default to all categories enabled
            for category in NotificationCategory:
                self.categories[category] = True

    def is_category_enabled(self, category: NotificationCategory) -> bool:
        """Check if a category is enabled for this channel"""
        return self.enabled and self.categories.get(category, False)

    def can_send_now(self, category: NotificationCategory, check_time: Optional[datetime] = None) -> bool:
        """Check if notification can be sent now considering quiet hours and exceptions"""
        if not self.is_category_enabled(category):
            return False

        if category in self.quiet_hours.exceptions:
            return True

        return not self.quiet_hours.is_in_quiet_hours(check_time)


@dataclass
class UserNotificationPreferences:
    """Complete notification preferences for a user"""
    user_id: str
    channels: Dict[NotificationChannel, ChannelPreferences] = field(default_factory=dict)
    global_enabled: bool = True
    language: str = "en"
    timezone: str = "UTC"
    contact_info: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    def __post_init__(self):
        """Initialize default channel preferences"""
        if not self.channels:
            # Email preferences - comprehensive notifications
            self.channels[NotificationChannel.EMAIL] = ChannelPreferences(
                enabled=True,
                frequency=NotificationFrequency.IMMEDIATE,
                quiet_hours=QuietHours(
                    enabled=True,
                    start_time="22:00",
                    end_time="08:00",
                    exceptions=[NotificationCategory.SECURITY, NotificationCategory.DEADLINE_REMINDERS]
                ),
                daily_limit=50,
                categories={
                    NotificationCategory.DOCUMENT_ANALYSIS: True,
                    NotificationCategory.DEADLINE_REMINDERS: True,
                    NotificationCategory.CASE_UPDATES: True,
                    NotificationCategory.QA_RESPONSES: True,
                    NotificationCategory.ATTORNEY_ACTIONS: True,
                    NotificationCategory.SYSTEM_ALERTS: True,
                    NotificationCategory.PAYMENTS: True,
                    NotificationCategory.SECURITY: True,
                    NotificationCategory.MARKETING: False,
                    NotificationCategory.COLLABORATION: True
                }
            )

            # SMS preferences - critical only
            self.channels[NotificationChannel.SMS] = ChannelPreferences(
                enabled=True,
                frequency=NotificationFrequency.IMMEDIATE,
                quiet_hours=QuietHours(
                    enabled=True,
                    start_time="22:00",
                    end_time="08:00",
                    exceptions=[NotificationCategory.SECURITY, NotificationCategory.DEADLINE_REMINDERS]
                ),
                daily_limit=10,
                categories={
                    NotificationCategory.DOCUMENT_ANALYSIS: False,
                    NotificationCategory.DEADLINE_REMINDERS: True,
                    NotificationCategory.CASE_UPDATES: False,
                    NotificationCategory.QA_RESPONSES: False,
                    NotificationCategory.ATTORNEY_ACTIONS: True,
                    NotificationCategory.SYSTEM_ALERTS: True,
                    NotificationCategory.PAYMENTS: False,
                    NotificationCategory.SECURITY: True,
                    NotificationCategory.MARKETING: False,
                    NotificationCategory.COLLABORATION: False
                }
            )

            # Push preferences - real-time updates
            self.channels[NotificationChannel.PUSH] = ChannelPreferences(
                enabled=True,
                frequency=NotificationFrequency.IMMEDIATE,
                quiet_hours=QuietHours(
                    enabled=True,
                    start_time="22:00",
                    end_time="08:00",
                    exceptions=[NotificationCategory.SECURITY]
                ),
                daily_limit=100,
                categories={
                    NotificationCategory.DOCUMENT_ANALYSIS: True,
                    NotificationCategory.DEADLINE_REMINDERS: True,
                    NotificationCategory.CASE_UPDATES: True,
                    NotificationCategory.QA_RESPONSES: True,
                    NotificationCategory.ATTORNEY_ACTIONS: True,
                    NotificationCategory.SYSTEM_ALERTS: True,
                    NotificationCategory.PAYMENTS: True,
                    NotificationCategory.SECURITY: True,
                    NotificationCategory.MARKETING: False,
                    NotificationCategory.COLLABORATION: True
                }
            )

            # In-app preferences - everything enabled
            self.channels[NotificationChannel.IN_APP] = ChannelPreferences(
                enabled=True,
                frequency=NotificationFrequency.IMMEDIATE,
                quiet_hours=QuietHours(enabled=False),  # No quiet hours for in-app
                daily_limit=1000,
                categories={category: True for category in NotificationCategory}
            )

    def get_channel_preferences(self, channel: NotificationChannel) -> Optional[ChannelPreferences]:
        """Get preferences for a specific channel"""
        return self.channels.get(channel)

    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if a channel is globally enabled"""
        if not self.global_enabled:
            return False

        channel_prefs = self.get_channel_preferences(channel)
        return channel_prefs.enabled if channel_prefs else False

    def can_send_notification(
        self,
        channel: NotificationChannel,
        category: NotificationCategory,
        check_time: Optional[datetime] = None
    ) -> bool:
        """Check if notification can be sent for given channel and category"""
        if not self.is_channel_enabled(channel):
            return False

        channel_prefs = self.get_channel_preferences(channel)
        if not channel_prefs:
            return False

        return channel_prefs.can_send_now(category, check_time)

    def update_channel_preferences(self, channel: NotificationChannel, preferences: Dict[str, Any]):
        """Update preferences for a specific channel"""
        if channel not in self.channels:
            self.channels[channel] = ChannelPreferences()

        channel_prefs = self.channels[channel]

        # Update basic settings
        if 'enabled' in preferences:
            channel_prefs.enabled = preferences['enabled']

        if 'frequency' in preferences:
            channel_prefs.frequency = NotificationFrequency(preferences['frequency'])

        if 'daily_limit' in preferences:
            channel_prefs.daily_limit = preferences['daily_limit']

        # Update categories
        if 'categories' in preferences:
            for category_name, enabled in preferences['categories'].items():
                try:
                    category = NotificationCategory(category_name)
                    channel_prefs.categories[category] = enabled
                except ValueError:
                    logger.warning(f"Unknown category: {category_name}")

        # Update quiet hours
        if 'quiet_hours' in preferences:
            quiet_hours_data = preferences['quiet_hours']
            if isinstance(quiet_hours_data, dict):
                channel_prefs.quiet_hours.enabled = quiet_hours_data.get('enabled', False)
                channel_prefs.quiet_hours.start_time = quiet_hours_data.get('start_time', '22:00')
                channel_prefs.quiet_hours.end_time = quiet_hours_data.get('end_time', '08:00')
                channel_prefs.quiet_hours.timezone = quiet_hours_data.get('timezone', 'UTC')

                if 'exceptions' in quiet_hours_data:
                    exceptions = []
                    for exc in quiet_hours_data['exceptions']:
                        try:
                            exceptions.append(NotificationCategory(exc))
                        except ValueError:
                            logger.warning(f"Unknown exception category: {exc}")
                    channel_prefs.quiet_hours.exceptions = exceptions

        self.updated_at = datetime.now()
        self.version += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary"""
        return {
            'user_id': self.user_id,
            'global_enabled': self.global_enabled,
            'language': self.language,
            'timezone': self.timezone,
            'contact_info': self.contact_info,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
            'channels': {
                channel.value: {
                    'enabled': prefs.enabled,
                    'frequency': prefs.frequency.value,
                    'daily_limit': prefs.daily_limit,
                    'categories': {cat.value: enabled for cat, enabled in prefs.categories.items()},
                    'quiet_hours': {
                        'enabled': prefs.quiet_hours.enabled,
                        'start_time': prefs.quiet_hours.start_time,
                        'end_time': prefs.quiet_hours.end_time,
                        'timezone': prefs.quiet_hours.timezone,
                        'exceptions': [exc.value for exc in prefs.quiet_hours.exceptions]
                    },
                    'metadata': prefs.metadata
                }
                for channel, prefs in self.channels.items()
            }
        }


class NotificationPreferencesManager:
    """Manages notification preferences for all users"""

    def __init__(self):
        self.user_preferences: Dict[str, UserNotificationPreferences] = {}
        self.default_templates: Dict[str, Dict[str, Any]] = {}
        self._setup_default_templates()

    def _setup_default_templates(self):
        """Setup default preference templates"""
        self.default_templates = {
            "legal_professional": {
                "description": "Optimized for legal professionals with comprehensive notifications",
                "channels": {
                    "email": {
                        "enabled": True,
                        "categories": {
                            "document_analysis": True,
                            "deadline_reminders": True,
                            "case_updates": True,
                            "attorney_actions": True,
                            "system_alerts": True,
                            "payments": True,
                            "security": True,
                            "marketing": False,
                            "collaboration": True
                        },
                        "frequency": "immediate",
                        "daily_limit": 50
                    },
                    "sms": {
                        "enabled": True,
                        "categories": {
                            "deadline_reminders": True,
                            "attorney_actions": True,
                            "system_alerts": True,
                            "security": True
                        },
                        "daily_limit": 10
                    },
                    "push": {
                        "enabled": True,
                        "categories": {
                            "document_analysis": True,
                            "deadline_reminders": True,
                            "case_updates": True,
                            "qa_responses": True,
                            "collaboration": True
                        },
                        "daily_limit": 100
                    }
                }
            },
            "client": {
                "description": "Simplified notifications for clients",
                "channels": {
                    "email": {
                        "enabled": True,
                        "categories": {
                            "case_updates": True,
                            "attorney_actions": True,
                            "payments": True,
                            "security": True
                        },
                        "frequency": "daily",
                        "daily_limit": 5
                    },
                    "sms": {
                        "enabled": False,
                        "categories": {
                            "security": True
                        }
                    },
                    "push": {
                        "enabled": True,
                        "categories": {
                            "case_updates": True,
                            "attorney_actions": True
                        },
                        "daily_limit": 10
                    }
                }
            },
            "minimal": {
                "description": "Minimal notifications - only critical updates",
                "channels": {
                    "email": {
                        "enabled": True,
                        "categories": {
                            "deadline_reminders": True,
                            "security": True
                        },
                        "frequency": "weekly",
                        "daily_limit": 2
                    },
                    "sms": {
                        "enabled": False
                    },
                    "push": {
                        "enabled": True,
                        "categories": {
                            "security": True
                        },
                        "daily_limit": 5
                    }
                }
            }
        }

    async def get_user_preferences(self, user_id: str) -> UserNotificationPreferences:
        """Get or create user preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserNotificationPreferences(user_id=user_id)
        return self.user_preferences[user_id]

    async def update_user_preferences(
        self,
        user_id: str,
        preferences_update: Dict[str, Any]
    ) -> UserNotificationPreferences:
        """Update user preferences"""
        user_prefs = await self.get_user_preferences(user_id)

        # Update global settings
        if 'global_enabled' in preferences_update:
            user_prefs.global_enabled = preferences_update['global_enabled']

        if 'language' in preferences_update:
            user_prefs.language = preferences_update['language']

        if 'timezone' in preferences_update:
            user_prefs.timezone = preferences_update['timezone']

        if 'contact_info' in preferences_update:
            user_prefs.contact_info.update(preferences_update['contact_info'])

        # Update channel preferences
        if 'channels' in preferences_update:
            for channel_name, channel_prefs in preferences_update['channels'].items():
                try:
                    channel = NotificationChannel(channel_name)
                    user_prefs.update_channel_preferences(channel, channel_prefs)
                except ValueError:
                    logger.warning(f"Unknown channel: {channel_name}")

        user_prefs.updated_at = datetime.now()
        user_prefs.version += 1

        logger.info(f"Updated preferences for user {user_id} to version {user_prefs.version}")
        return user_prefs

    async def apply_template(self, user_id: str, template_name: str) -> UserNotificationPreferences:
        """Apply a preference template to user"""
        if template_name not in self.default_templates:
            raise ValueError(f"Unknown template: {template_name}")

        template = self.default_templates[template_name]
        return await self.update_user_preferences(user_id, template)

    async def bulk_update_preferences(
        self,
        user_preferences: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Bulk update preferences for multiple users"""
        results = {}

        for user_pref_data in user_preferences:
            user_id = user_pref_data.get('user_id')
            if not user_id:
                continue

            try:
                preferences = {k: v for k, v in user_pref_data.items() if k != 'user_id'}
                await self.update_user_preferences(user_id, preferences)
                results[user_id] = True
            except Exception as e:
                logger.error(f"Failed to update preferences for user {user_id}: {e}")
                results[user_id] = False

        return results

    async def get_channel_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's notification settings"""
        user_prefs = await self.get_user_preferences(user_id)

        summary = {
            'global_enabled': user_prefs.global_enabled,
            'channels': {},
            'total_categories': len(NotificationCategory),
            'enabled_categories_by_channel': {}
        }

        for channel, prefs in user_prefs.channels.items():
            enabled_categories = [cat.value for cat, enabled in prefs.categories.items() if enabled]

            summary['channels'][channel.value] = {
                'enabled': prefs.enabled,
                'frequency': prefs.frequency.value,
                'daily_limit': prefs.daily_limit,
                'quiet_hours_enabled': prefs.quiet_hours.enabled,
                'enabled_categories_count': len(enabled_categories)
            }

            summary['enabled_categories_by_channel'][channel.value] = enabled_categories

        return summary

    async def export_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Export user preferences for backup or transfer"""
        user_prefs = await self.get_user_preferences(user_id)
        return user_prefs.to_dict()

    async def import_user_preferences(self, preferences_data: Dict[str, Any]) -> str:
        """Import user preferences from backup"""
        user_id = preferences_data['user_id']

        # Create new preferences object
        user_prefs = UserNotificationPreferences(user_id=user_id)

        # Import basic settings
        user_prefs.global_enabled = preferences_data.get('global_enabled', True)
        user_prefs.language = preferences_data.get('language', 'en')
        user_prefs.timezone = preferences_data.get('timezone', 'UTC')
        user_prefs.contact_info = preferences_data.get('contact_info', {})

        # Import channel preferences
        channels_data = preferences_data.get('channels', {})
        for channel_name, channel_data in channels_data.items():
            try:
                channel = NotificationChannel(channel_name)
                user_prefs.update_channel_preferences(channel, channel_data)
            except ValueError:
                logger.warning(f"Skipping unknown channel: {channel_name}")

        self.user_preferences[user_id] = user_prefs
        logger.info(f"Imported preferences for user {user_id}")
        return user_id

    async def get_users_for_notification(
        self,
        channel: NotificationChannel,
        category: NotificationCategory,
        check_time: Optional[datetime] = None
    ) -> List[str]:
        """Get list of users who can receive notifications for given channel and category"""
        eligible_users = []

        for user_id, prefs in self.user_preferences.items():
            if prefs.can_send_notification(channel, category, check_time):
                eligible_users.append(user_id)

        return eligible_users

    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available preference templates"""
        return self.default_templates.copy()

    async def reset_user_preferences(self, user_id: str) -> UserNotificationPreferences:
        """Reset user preferences to defaults"""
        self.user_preferences[user_id] = UserNotificationPreferences(user_id=user_id)
        logger.info(f"Reset preferences for user {user_id}")
        return self.user_preferences[user_id]

    async def get_preference_statistics(self) -> Dict[str, Any]:
        """Get statistics about user preferences"""
        stats = {
            'total_users': len(self.user_preferences),
            'global_enabled_users': 0,
            'channel_adoption': defaultdict(int),
            'category_popularity': defaultdict(int),
            'quiet_hours_users': defaultdict(int),
            'frequency_distribution': defaultdict(int)
        }

        for prefs in self.user_preferences.values():
            if prefs.global_enabled:
                stats['global_enabled_users'] += 1

            for channel, channel_prefs in prefs.channels.items():
                if channel_prefs.enabled:
                    stats['channel_adoption'][channel.value] += 1

                stats['frequency_distribution'][channel_prefs.frequency.value] += 1

                if channel_prefs.quiet_hours.enabled:
                    stats['quiet_hours_users'][channel.value] += 1

                for category, enabled in channel_prefs.categories.items():
                    if enabled:
                        stats['category_popularity'][category.value] += 1

        return dict(stats)


# Global preferences manager instance
preferences_manager = NotificationPreferencesManager()


# FastAPI endpoints
def get_preferences_endpoints():
    """Returns FastAPI endpoints for notification preferences"""
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    from typing import Optional, List

    router = APIRouter(prefix="/api/notifications/preferences", tags=["notification-preferences"])

    class PreferencesUpdateRequest(BaseModel):
        channels: Optional[Dict[str, Any]] = None
        global_enabled: Optional[bool] = None
        language: Optional[str] = None
        timezone: Optional[str] = None
        contact_info: Optional[Dict[str, str]] = None

    class BulkPreferencesRequest(BaseModel):
        user_preferences: List[Dict[str, Any]]

    @router.get("/{user_id}")
    async def get_preferences(user_id: str):
        """Get user notification preferences"""
        try:
            prefs = await preferences_manager.get_user_preferences(user_id)
            return prefs.to_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/{user_id}")
    async def update_preferences(user_id: str, request: PreferencesUpdateRequest):
        """Update user notification preferences"""
        try:
            update_data = request.dict(exclude_unset=True)
            prefs = await preferences_manager.update_user_preferences(user_id, update_data)
            return prefs.to_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{user_id}/summary")
    async def get_preferences_summary(user_id: str):
        """Get summary of user notification preferences"""
        try:
            return await preferences_manager.get_channel_summary(user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{user_id}/template/{template_name}")
    async def apply_template(user_id: str, template_name: str):
        """Apply preference template to user"""
        try:
            prefs = await preferences_manager.apply_template(user_id, template_name)
            return prefs.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/templates/available")
    async def get_templates():
        """Get available preference templates"""
        return preferences_manager.get_available_templates()

    @router.post("/{user_id}/reset")
    async def reset_preferences(user_id: str):
        """Reset user preferences to defaults"""
        try:
            prefs = await preferences_manager.reset_user_preferences(user_id)
            return prefs.to_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/bulk-update")
    async def bulk_update_preferences(request: BulkPreferencesRequest):
        """Bulk update preferences for multiple users"""
        try:
            results = await preferences_manager.bulk_update_preferences(request.user_preferences)
            return {"results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{user_id}/export")
    async def export_preferences(user_id: str):
        """Export user preferences"""
        try:
            return await preferences_manager.export_user_preferences(user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/import")
    async def import_preferences(preferences_data: Dict[str, Any]):
        """Import user preferences"""
        try:
            user_id = await preferences_manager.import_user_preferences(preferences_data)
            return {"user_id": user_id, "success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats/overview")
    async def get_statistics():
        """Get preference statistics"""
        try:
            return await preferences_manager.get_preference_statistics()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/eligible-users/{channel}/{category}")
    async def get_eligible_users(channel: str, category: str):
        """Get users eligible for notification"""
        try:
            channel_enum = NotificationChannel(channel)
            category_enum = NotificationCategory(category)
            users = await preferences_manager.get_users_for_notification(channel_enum, category_enum)
            return {"eligible_users": users}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        manager = NotificationPreferencesManager()

        # Create user preferences
        user_id = "user123"
        prefs = await manager.get_user_preferences(user_id)
        print(f"Created preferences for {user_id}")

        # Update some preferences
        updates = {
            "channels": {
                "email": {
                    "enabled": True,
                    "categories": {
                        "marketing": True
                    },
                    "quiet_hours": {
                        "enabled": True,
                        "start_time": "20:00",
                        "end_time": "09:00"
                    }
                }
            }
        }

        updated_prefs = await manager.update_user_preferences(user_id, updates)
        print(f"Updated preferences to version {updated_prefs.version}")

        # Apply a template
        await manager.apply_template("client456", "client")
        print("Applied client template")

        # Get summary
        summary = await manager.get_channel_summary(user_id)
        print(f"Email enabled: {summary['channels']['email']['enabled']}")

        # Get statistics
        stats = await manager.get_preference_statistics()
        print(f"Total users with preferences: {stats['total_users']}")

        print("Notification preferences demo completed!")

    asyncio.run(demo())