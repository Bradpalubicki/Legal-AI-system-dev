"""
Role-Based Personalization Engine
Provides personalized experiences based on user roles, practice areas, and preferences.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import json


class UserRole(Enum):
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    ADMIN = "admin"


class PracticeArea(Enum):
    CORPORATE = "corporate"
    LITIGATION = "litigation"
    REAL_ESTATE = "real_estate"
    FAMILY_LAW = "family_law"
    CRIMINAL_LAW = "criminal_law"
    IMMIGRATION = "immigration"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    TAX_LAW = "tax_law"
    EMPLOYMENT = "employment"
    PERSONAL_INJURY = "personal_injury"


class ExperienceLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class WorkflowPreference(Enum):
    STRUCTURED = "structured"  # Step-by-step guided workflows
    FLEXIBLE = "flexible"      # Open-ended with options
    EFFICIENT = "efficient"    # Minimal steps, maximum speed
    COMPREHENSIVE = "comprehensive"  # Detailed analysis and options


class CommunicationPreference(Enum):
    EMAIL_ONLY = "email_only"
    SMS_ALERTS = "sms_alerts"
    IN_APP_ONLY = "in_app_only"
    ALL_CHANNELS = "all_channels"
    URGENT_ONLY = "urgent_only"


@dataclass
class PersonalizationProfile:
    user_id: str
    role: UserRole
    practice_areas: List[PracticeArea] = field(default_factory=list)
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    workflow_preference: WorkflowPreference = WorkflowPreference.STRUCTURED
    communication_preference: CommunicationPreference = CommunicationPreference.EMAIL_ONLY
    preferred_features: List[str] = field(default_factory=list)
    hidden_features: List[str] = field(default_factory=list)
    dashboard_layout: Dict[str, Any] = field(default_factory=dict)
    quick_actions: List[str] = field(default_factory=list)
    content_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PersonalizedContent:
    content_type: str
    title: str
    description: str
    content: Dict[str, Any]
    target_roles: List[UserRole]
    target_practice_areas: List[PracticeArea]
    experience_levels: List[ExperienceLevel]
    priority: int = 5  # 1-10, higher is more important
    is_featured: bool = False


class PersonalizationEngine:
    """Advanced personalization engine for role-based user experiences"""

    def __init__(self):
        self.profiles: Dict[str, PersonalizationProfile] = {}
        self.content_library: Dict[str, PersonalizedContent] = {}
        self.role_templates = self._initialize_role_templates()
        self.feature_matrix = self._initialize_feature_matrix()

    def _initialize_role_templates(self) -> Dict[UserRole, Dict]:
        """Initialize default templates for each role"""
        return {
            UserRole.ATTORNEY: {
                "dashboard_widgets": [
                    "case_summary", "document_analysis", "deadline_tracker",
                    "client_communications", "billing_summary", "legal_research"
                ],
                "quick_actions": [
                    "upload_document", "create_case", "schedule_meeting",
                    "generate_report", "search_cases", "contact_client"
                ],
                "default_features": [
                    "advanced_analysis", "multi_client_view", "billing_integration",
                    "calendar_sync", "email_templates", "signature_tools"
                ],
                "workflow_steps": [
                    "client_intake", "document_review", "legal_analysis",
                    "strategy_development", "client_communication", "case_closure"
                ]
            },
            UserRole.PARALEGAL: {
                "dashboard_widgets": [
                    "task_list", "document_queue", "deadline_alerts",
                    "research_tools", "template_library", "case_notes"
                ],
                "quick_actions": [
                    "process_documents", "update_case", "schedule_tasks",
                    "generate_forms", "research_citations", "update_calendar"
                ],
                "default_features": [
                    "document_processing", "template_management", "task_tracking",
                    "research_tools", "form_generation", "calendar_management"
                ],
                "workflow_steps": [
                    "document_intake", "initial_review", "fact_gathering",
                    "research_support", "document_preparation", "filing_support"
                ]
            },
            UserRole.CLIENT: {
                "dashboard_widgets": [
                    "case_status", "document_viewer", "communication_center",
                    "appointment_scheduler", "billing_overview", "progress_tracker"
                ],
                "quick_actions": [
                    "view_documents", "message_attorney", "upload_files",
                    "schedule_appointment", "pay_invoice", "download_reports"
                ],
                "default_features": [
                    "document_viewing", "secure_messaging", "appointment_booking",
                    "payment_portal", "progress_tracking", "mobile_access"
                ],
                "workflow_steps": [
                    "case_overview", "document_review", "provide_feedback",
                    "approve_actions", "payment_processing", "case_completion"
                ]
            },
            UserRole.ADMIN: {
                "dashboard_widgets": [
                    "system_overview", "user_management", "analytics_dashboard",
                    "security_monitoring", "backup_status", "performance_metrics"
                ],
                "quick_actions": [
                    "manage_users", "system_settings", "view_analytics",
                    "security_audit", "backup_data", "update_system"
                ],
                "default_features": [
                    "user_management", "system_administration", "security_controls",
                    "analytics_reporting", "backup_management", "audit_logging"
                ],
                "workflow_steps": [
                    "system_monitoring", "user_support", "security_review",
                    "performance_optimization", "data_management", "compliance_check"
                ]
            }
        }

    def _initialize_feature_matrix(self) -> Dict[str, Dict[UserRole, bool]]:
        """Define which features are available to which roles"""
        return {
            "advanced_analysis": {
                UserRole.ATTORNEY: True,
                UserRole.PARALEGAL: True,
                UserRole.CLIENT: False,
                UserRole.ADMIN: True
            },
            "multi_client_view": {
                UserRole.ATTORNEY: True,
                UserRole.PARALEGAL: True,
                UserRole.CLIENT: False,
                UserRole.ADMIN: True
            },
            "billing_integration": {
                UserRole.ATTORNEY: True,
                UserRole.PARALEGAL: False,
                UserRole.CLIENT: True,
                UserRole.ADMIN: True
            },
            "user_management": {
                UserRole.ATTORNEY: False,
                UserRole.PARALEGAL: False,
                UserRole.CLIENT: False,
                UserRole.ADMIN: True
            },
            "system_administration": {
                UserRole.ATTORNEY: False,
                UserRole.PARALEGAL: False,
                UserRole.CLIENT: False,
                UserRole.ADMIN: True
            },
            "document_processing": {
                UserRole.ATTORNEY: True,
                UserRole.PARALEGAL: True,
                UserRole.CLIENT: True,
                UserRole.ADMIN: True
            },
            "secure_messaging": {
                UserRole.ATTORNEY: True,
                UserRole.PARALEGAL: True,
                UserRole.CLIENT: True,
                UserRole.ADMIN: False
            }
        }

    async def create_profile(
        self,
        user_id: str,
        role: UserRole,
        practice_areas: List[PracticeArea] = None,
        experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    ) -> PersonalizationProfile:
        """Create a new personalization profile"""

        # Get role template
        template = self.role_templates.get(role, {})

        profile = PersonalizationProfile(
            user_id=user_id,
            role=role,
            practice_areas=practice_areas or [],
            experience_level=experience_level,
            preferred_features=template.get("default_features", []),
            dashboard_layout={
                "widgets": template.get("dashboard_widgets", []),
                "layout": "default"
            },
            quick_actions=template.get("quick_actions", []),
            content_preferences={
                "workflow_steps": template.get("workflow_steps", []),
                "show_tooltips": experience_level in [ExperienceLevel.BEGINNER, ExperienceLevel.INTERMEDIATE],
                "detailed_explanations": experience_level == ExperienceLevel.BEGINNER
            }
        )

        self.profiles[user_id] = profile
        return profile

    async def get_profile(self, user_id: str) -> Optional[PersonalizationProfile]:
        """Get user's personalization profile"""
        return self.profiles.get(user_id)

    async def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> PersonalizationProfile:
        """Update user's personalization profile"""

        if user_id not in self.profiles:
            raise ValueError(f"Profile not found for user {user_id}")

        profile = self.profiles[user_id]

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.now()
        return profile

    async def get_personalized_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get personalized dashboard configuration"""

        profile = await self.get_profile(user_id)
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")

        # Base dashboard from profile
        dashboard = profile.dashboard_layout.copy()

        # Add role-specific enhancements
        if profile.role == UserRole.ATTORNEY:
            dashboard["priority_widgets"] = [
                "urgent_deadlines", "high_priority_cases", "client_messages"
            ]
        elif profile.role == UserRole.PARALEGAL:
            dashboard["priority_widgets"] = [
                "task_deadlines", "document_queue", "attorney_requests"
            ]
        elif profile.role == UserRole.CLIENT:
            dashboard["priority_widgets"] = [
                "case_updates", "new_messages", "upcoming_appointments"
            ]

        # Add practice area specific widgets
        practice_widgets = []
        for area in profile.practice_areas:
            if area == PracticeArea.LITIGATION:
                practice_widgets.extend(["court_calendar", "discovery_tracker"])
            elif area == PracticeArea.CORPORATE:
                practice_widgets.extend(["contract_pipeline", "compliance_alerts"])
            elif area == PracticeArea.REAL_ESTATE:
                practice_widgets.extend(["closing_calendar", "title_alerts"])

        dashboard["practice_widgets"] = practice_widgets

        return dashboard

    async def get_personalized_content(
        self,
        user_id: str,
        content_type: str = None
    ) -> List[PersonalizedContent]:
        """Get personalized content recommendations"""

        profile = await self.get_profile(user_id)
        if not profile:
            return []

        relevant_content = []

        for content_id, content in self.content_library.items():
            # Filter by content type if specified
            if content_type and content.content_type != content_type:
                continue

            # Check role matching
            if profile.role not in content.target_roles:
                continue

            # Check practice area overlap
            if content.target_practice_areas:
                if not any(area in profile.practice_areas for area in content.target_practice_areas):
                    continue

            # Check experience level
            if profile.experience_level not in content.experience_levels:
                continue

            relevant_content.append(content)

        # Sort by priority and featured status
        relevant_content.sort(key=lambda x: (-x.priority, -x.is_featured))

        return relevant_content

    async def get_available_features(self, user_id: str) -> List[str]:
        """Get list of features available to user based on role"""

        profile = await self.get_profile(user_id)
        if not profile:
            return []

        available_features = []

        for feature, role_access in self.feature_matrix.items():
            if role_access.get(profile.role, False):
                # Check if user has explicitly hidden this feature
                if feature not in profile.hidden_features:
                    available_features.append(feature)

        return available_features

    async def get_workflow_recommendations(self, user_id: str, task_type: str) -> Dict[str, Any]:
        """Get personalized workflow recommendations"""

        profile = await self.get_profile(user_id)
        if not profile:
            return {}

        workflow = {
            "steps": [],
            "quick_actions": profile.quick_actions,
            "recommended_templates": [],
            "suggested_automations": []
        }

        # Get base workflow steps from profile
        base_steps = profile.content_preferences.get("workflow_steps", [])

        # Customize based on workflow preference
        if profile.workflow_preference == WorkflowPreference.STRUCTURED:
            workflow["steps"] = base_steps
            workflow["guidance_level"] = "detailed"
        elif profile.workflow_preference == WorkflowPreference.EFFICIENT:
            # Reduce steps to essentials
            workflow["steps"] = base_steps[:3]
            workflow["guidance_level"] = "minimal"
        elif profile.workflow_preference == WorkflowPreference.FLEXIBLE:
            workflow["steps"] = base_steps
            workflow["guidance_level"] = "optional"
            workflow["allow_skipping"] = True

        # Add role-specific recommendations
        if profile.role == UserRole.ATTORNEY:
            workflow["suggested_automations"] = [
                "auto_time_tracking", "client_update_templates", "deadline_reminders"
            ]
        elif profile.role == UserRole.PARALEGAL:
            workflow["suggested_automations"] = [
                "document_routing", "task_notifications", "form_prefilling"
            ]

        return workflow

    async def record_user_interaction(
        self,
        user_id: str,
        feature: str,
        action: str,
        context: Dict[str, Any] = None
    ):
        """Record user interaction for learning and personalization"""

        profile = await self.get_profile(user_id)
        if not profile:
            return

        # Update feature usage frequency
        usage_stats = profile.content_preferences.get("feature_usage", {})
        usage_stats[feature] = usage_stats.get(feature, 0) + 1
        profile.content_preferences["feature_usage"] = usage_stats

        # Learn from user behavior
        if action == "hide":
            if feature not in profile.hidden_features:
                profile.hidden_features.append(feature)
        elif action == "favorite":
            if feature not in profile.preferred_features:
                profile.preferred_features.append(feature)
        elif action == "quick_access":
            if feature not in profile.quick_actions:
                profile.quick_actions.append(feature)

    async def add_content(self, content: PersonalizedContent):
        """Add personalized content to the library"""
        content_id = f"{content.content_type}_{len(self.content_library)}"
        self.content_library[content_id] = content
        return content_id

    async def get_onboarding_customization(self, user_id: str) -> Dict[str, Any]:
        """Get customized onboarding flow based on user profile"""

        profile = await self.get_profile(user_id)
        if not profile:
            return {}

        customization = {
            "skip_basic_steps": profile.experience_level in [ExperienceLevel.ADVANCED, ExperienceLevel.EXPERT],
            "focus_areas": [area.value for area in profile.practice_areas],
            "recommended_features": profile.preferred_features[:5],  # Top 5
            "workflow_style": profile.workflow_preference.value,
            "communication_setup": profile.communication_preference.value
        }

        # Role-specific customizations
        if profile.role == UserRole.CLIENT:
            customization["simplified_interface"] = True
            customization["hide_advanced_features"] = True
        elif profile.role == UserRole.ATTORNEY:
            customization["show_all_features"] = True
            customization["enable_shortcuts"] = True

        return customization


# Pydantic models for API
class PersonalizationProfileModel(BaseModel):
    user_id: str
    role: UserRole
    practice_areas: List[PracticeArea] = Field(default_factory=list)
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    workflow_preference: WorkflowPreference = WorkflowPreference.STRUCTURED
    communication_preference: CommunicationPreference = CommunicationPreference.EMAIL_ONLY
    preferred_features: List[str] = Field(default_factory=list)
    hidden_features: List[str] = Field(default_factory=list)
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict)
    quick_actions: List[str] = Field(default_factory=list)
    content_preferences: Dict[str, Any] = Field(default_factory=dict)


class ProfileUpdateModel(BaseModel):
    practice_areas: Optional[List[PracticeArea]] = None
    experience_level: Optional[ExperienceLevel] = None
    workflow_preference: Optional[WorkflowPreference] = None
    communication_preference: Optional[CommunicationPreference] = None
    preferred_features: Optional[List[str]] = None
    hidden_features: Optional[List[str]] = None
    dashboard_layout: Optional[Dict[str, Any]] = None
    quick_actions: Optional[List[str]] = None


class InteractionModel(BaseModel):
    feature: str
    action: str
    context: Optional[Dict[str, Any]] = None


# Global instance
personalization_engine = PersonalizationEngine()


def get_personalization_endpoints() -> APIRouter:
    """Get personalization-related FastAPI endpoints"""
    router = APIRouter(prefix="/personalization", tags=["personalization"])

    @router.post("/profile/{user_id}", response_model=PersonalizationProfileModel)
    async def create_personalization_profile(
        user_id: str,
        role: UserRole,
        practice_areas: List[PracticeArea] = None,
        experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    ):
        """Create a new personalization profile"""
        profile = await personalization_engine.create_profile(
            user_id, role, practice_areas, experience_level
        )
        return PersonalizationProfileModel(**profile.__dict__)

    @router.get("/profile/{user_id}", response_model=PersonalizationProfileModel)
    async def get_personalization_profile(user_id: str):
        """Get user's personalization profile"""
        profile = await personalization_engine.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return PersonalizationProfileModel(**profile.__dict__)

    @router.put("/profile/{user_id}", response_model=PersonalizationProfileModel)
    async def update_personalization_profile(
        user_id: str,
        updates: ProfileUpdateModel
    ):
        """Update user's personalization profile"""
        try:
            profile = await personalization_engine.update_profile(
                user_id, updates.dict(exclude_unset=True)
            )
            return PersonalizationProfileModel(**profile.__dict__)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/dashboard/{user_id}")
    async def get_personalized_dashboard(user_id: str):
        """Get personalized dashboard configuration"""
        try:
            dashboard = await personalization_engine.get_personalized_dashboard(user_id)
            return dashboard
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/content/{user_id}")
    async def get_personalized_content(
        user_id: str,
        content_type: Optional[str] = None
    ):
        """Get personalized content recommendations"""
        content = await personalization_engine.get_personalized_content(
            user_id, content_type
        )
        return [
            {
                "content_type": c.content_type,
                "title": c.title,
                "description": c.description,
                "content": c.content,
                "priority": c.priority,
                "is_featured": c.is_featured
            }
            for c in content
        ]

    @router.get("/features/{user_id}")
    async def get_available_features(user_id: str):
        """Get list of features available to user"""
        features = await personalization_engine.get_available_features(user_id)
        return {"available_features": features}

    @router.get("/workflow/{user_id}/{task_type}")
    async def get_workflow_recommendations(user_id: str, task_type: str):
        """Get personalized workflow recommendations"""
        workflow = await personalization_engine.get_workflow_recommendations(
            user_id, task_type
        )
        return workflow

    @router.post("/interaction/{user_id}")
    async def record_user_interaction(user_id: str, interaction: InteractionModel):
        """Record user interaction for learning"""
        await personalization_engine.record_user_interaction(
            user_id, interaction.feature, interaction.action, interaction.context
        )
        return {"status": "recorded"}

    @router.get("/onboarding/{user_id}")
    async def get_onboarding_customization(user_id: str):
        """Get customized onboarding flow"""
        customization = await personalization_engine.get_onboarding_customization(user_id)
        return customization

    return router


async def initialize_personalization_system():
    """Initialize the personalization system"""
    print("Initializing role-based personalization system...")

    # Add some sample personalized content
    content_samples = [
        PersonalizedContent(
            content_type="tutorial",
            title="Contract Analysis for Attorneys",
            description="Advanced techniques for analyzing complex contracts",
            content={
                "video_url": "/videos/contract-analysis-advanced.mp4",
                "transcript": "Advanced contract analysis techniques...",
                "duration": "15 minutes"
            },
            target_roles=[UserRole.ATTORNEY],
            target_practice_areas=[PracticeArea.CORPORATE, PracticeArea.REAL_ESTATE],
            experience_levels=[ExperienceLevel.INTERMEDIATE, ExperienceLevel.ADVANCED],
            priority=8,
            is_featured=True
        ),
        PersonalizedContent(
            content_type="guide",
            title="Document Processing Workflow",
            description="Efficient document processing for paralegals",
            content={
                "steps": [
                    "Receive and categorize documents",
                    "Initial quality review",
                    "Extract key information",
                    "Route to appropriate attorney",
                    "Update case files"
                ],
                "templates": ["processing_checklist.pdf", "routing_form.pdf"]
            },
            target_roles=[UserRole.PARALEGAL],
            target_practice_areas=[],  # Applies to all practice areas
            experience_levels=[ExperienceLevel.BEGINNER, ExperienceLevel.INTERMEDIATE],
            priority=7
        ),
        PersonalizedContent(
            content_type="overview",
            title="Understanding Your Case Progress",
            description="How to track and understand your legal case",
            content={
                "sections": [
                    "Case status indicators",
                    "Document review process",
                    "Timeline and milestones",
                    "Communication preferences"
                ],
                "interactive_demo": True
            },
            target_roles=[UserRole.CLIENT],
            target_practice_areas=[],
            experience_levels=[ExperienceLevel.BEGINNER],
            priority=9,
            is_featured=True
        )
    ]

    for content in content_samples:
        await personalization_engine.add_content(content)

    print("✓ Personalization system initialized with sample content")
    print("✓ Role-based templates configured")
    print("✓ Feature matrix established")
    print("🎯 Role-based personalization system ready!")