"""
Role-Based Personalization System
Provides personalized user experiences based on roles, practice areas, and preferences.
"""

from .engine import (
    PersonalizationEngine,
    PersonalizationProfile,
    PersonalizedContent,
    UserRole,
    PracticeArea,
    ExperienceLevel,
    WorkflowPreference,
    CommunicationPreference,
    PersonalizationProfileModel,
    ProfileUpdateModel,
    InteractionModel,
    personalization_engine,
    get_personalization_endpoints,
    initialize_personalization_system
)

__all__ = [
    "PersonalizationEngine",
    "PersonalizationProfile",
    "PersonalizedContent",
    "UserRole",
    "PracticeArea",
    "ExperienceLevel",
    "WorkflowPreference",
    "CommunicationPreference",
    "PersonalizationProfileModel",
    "ProfileUpdateModel",
    "InteractionModel",
    "personalization_engine",
    "get_personalization_endpoints",
    "initialize_personalization_system"
]