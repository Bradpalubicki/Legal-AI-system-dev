"""
Interactive Onboarding Wizard System
Provides step-by-step setup and personalization for new users
with role-based paths and progress tracking.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class UserRole(Enum):
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    ADMIN = "admin"


class PracticeArea(Enum):
    CORPORATE = "corporate"
    LITIGATION = "litigation"
    FAMILY = "family"
    CRIMINAL = "criminal"
    REAL_ESTATE = "real_estate"
    IMMIGRATION = "immigration"
    BANKRUPTCY = "bankruptcy"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    EMPLOYMENT = "employment"
    PERSONAL_INJURY = "personal_injury"


class OnboardingStep(Enum):
    WELCOME = "welcome"
    ACCOUNT_SETUP = "account_setup"
    ROLE_SELECTION = "role_selection"
    FIRM_PROFILE = "firm_profile"
    PRACTICE_AREAS = "practice_areas"
    STATE_SELECTION = "state_selection"
    COMMUNICATION_PREFERENCES = "communication_preferences"
    FIRST_DOCUMENT = "first_document"
    SAMPLE_ANALYSIS = "sample_analysis"
    FEATURE_TOUR = "feature_tour"
    COMPLETION = "completion"


class OnboardingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class OnboardingStepData:
    """Data for a single onboarding step"""
    step: OnboardingStep
    title: str
    description: str
    content: Dict[str, Any]
    estimated_time: int  # in minutes
    required: bool = True
    role_specific: List[UserRole] = field(default_factory=list)
    prerequisites: List[OnboardingStep] = field(default_factory=list)

    def is_available_for_role(self, role: UserRole) -> bool:
        """Check if step is available for the given role"""
        if not self.role_specific:
            return True
        return role in self.role_specific


@dataclass
class StepProgress:
    """Progress tracking for a single step"""
    step: OnboardingStep
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    attempts: int = 0

    def start(self):
        """Mark step as started"""
        if self.status == OnboardingStatus.NOT_STARTED:
            self.status = OnboardingStatus.IN_PROGRESS
            self.started_at = datetime.now()
            self.attempts += 1

    def complete(self, data: Optional[Dict[str, Any]] = None):
        """Mark step as completed"""
        self.status = OnboardingStatus.COMPLETED
        self.completed_at = datetime.now()
        if data:
            self.data.update(data)

    def skip(self, reason: str = ""):
        """Mark step as skipped"""
        self.status = OnboardingStatus.SKIPPED
        self.skipped_at = datetime.now()
        self.data['skip_reason'] = reason


@dataclass
class OnboardingProfile:
    """Complete onboarding profile for a user"""
    user_id: str
    role: Optional[UserRole] = None
    practice_areas: List[PracticeArea] = field(default_factory=list)
    state: Optional[str] = None
    firm_name: Optional[str] = None
    firm_size: Optional[str] = None
    experience_level: Optional[str] = None
    communication_preferences: Dict[str, Any] = field(default_factory=dict)
    workflow_preferences: Dict[str, Any] = field(default_factory=dict)
    feature_interests: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(self, **kwargs):
        """Update profile data"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'role': self.role.value if self.role else None,
            'practice_areas': [pa.value for pa in self.practice_areas],
            'state': self.state,
            'firm_name': self.firm_name,
            'firm_size': self.firm_size,
            'experience_level': self.experience_level,
            'communication_preferences': self.communication_preferences,
            'workflow_preferences': self.workflow_preferences,
            'feature_interests': self.feature_interests,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class OnboardingSession:
    """Complete onboarding session for a user"""
    user_id: str
    session_id: str
    profile: OnboardingProfile
    step_progress: Dict[OnboardingStep, StepProgress] = field(default_factory=dict)
    current_step: Optional[OnboardingStep] = OnboardingStep.WELCOME
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    completion_percentage: float = 0.0

    def get_next_step(self) -> Optional[OnboardingStep]:
        """Get the next available step"""
        steps = list(OnboardingStep)
        if not self.current_step:
            return steps[0]

        current_index = steps.index(self.current_step)
        for i in range(current_index + 1, len(steps)):
            next_step = steps[i]
            step_data = OnboardingWizard.get_step_data(next_step)

            if step_data and step_data.is_available_for_role(self.profile.role or UserRole.ATTORNEY):
                # Check prerequisites
                prereqs_met = all(
                    self.step_progress.get(prereq, StepProgress(prereq)).status == OnboardingStatus.COMPLETED
                    for prereq in step_data.prerequisites
                )
                if prereqs_met:
                    return next_step

        return None

    def calculate_completion(self):
        """Calculate completion percentage"""
        role = self.profile.role or UserRole.ATTORNEY
        total_steps = 0
        completed_steps = 0

        for step in OnboardingStep:
            step_data = OnboardingWizard.get_step_data(step)
            if step_data and step_data.is_available_for_role(role):
                total_steps += 1
                progress = self.step_progress.get(step)
                if progress and progress.status == OnboardingStatus.COMPLETED:
                    completed_steps += 1

        self.completion_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        if self.completion_percentage >= 100:
            self.completed_at = datetime.now()


class OnboardingWizard:
    """Main onboarding wizard system"""

    # Step definitions
    STEP_DEFINITIONS = {
        OnboardingStep.WELCOME: OnboardingStepData(
            step=OnboardingStep.WELCOME,
            title="Welcome to Legal AI System",
            description="Welcome! Let's get you set up with your personalized legal AI assistant.",
            content={
                "welcome_message": "Welcome to the future of legal practice! Our AI-powered system will help you analyze documents, research cases, and streamline your workflow.",
                "benefits": [
                    "Analyze legal documents in seconds",
                    "Get instant answers to legal questions",
                    "Maintain full attorney accountability",
                    "Secure, confidential document handling"
                ],
                "video_url": "/videos/welcome-intro.mp4"
            },
            estimated_time=2,
            required=True
        ),

        OnboardingStep.ACCOUNT_SETUP: OnboardingStepData(
            step=OnboardingStep.ACCOUNT_SETUP,
            title="Account Setup",
            description="Set up your account with basic information.",
            content={
                "fields": [
                    {"name": "first_name", "type": "text", "required": True},
                    {"name": "last_name", "type": "text", "required": True},
                    {"name": "email", "type": "email", "required": True},
                    {"name": "phone", "type": "tel", "required": False},
                    {"name": "password", "type": "password", "required": True},
                    {"name": "confirm_password", "type": "password", "required": True}
                ]
            },
            estimated_time=3,
            required=True
        ),

        OnboardingStep.ROLE_SELECTION: OnboardingStepData(
            step=OnboardingStep.ROLE_SELECTION,
            title="Select Your Role",
            description="Help us personalize your experience by selecting your role.",
            content={
                "roles": [
                    {
                        "value": "attorney",
                        "label": "Attorney",
                        "description": "Licensed attorney practicing law",
                        "features": ["Full document analysis", "Case research", "Client management", "Billing integration"]
                    },
                    {
                        "value": "paralegal",
                        "label": "Paralegal",
                        "description": "Legal assistant supporting attorneys",
                        "features": ["Document preparation", "Research assistance", "Case organization", "Administrative tools"]
                    },
                    {
                        "value": "client",
                        "label": "Client",
                        "description": "Client of a law firm",
                        "features": ["Document upload", "Case status", "Communication", "Basic Q&A"]
                    },
                    {
                        "value": "admin",
                        "label": "Administrator",
                        "description": "Firm administrator or manager",
                        "features": ["User management", "Firm settings", "Reporting", "Billing oversight"]
                    }
                ]
            },
            estimated_time=2,
            required=True
        ),

        OnboardingStep.FIRM_PROFILE: OnboardingStepData(
            step=OnboardingStep.FIRM_PROFILE,
            title="Firm Information",
            description="Tell us about your law firm or organization.",
            content={
                "fields": [
                    {"name": "firm_name", "type": "text", "required": True, "label": "Firm Name"},
                    {"name": "firm_size", "type": "select", "required": True, "label": "Firm Size",
                     "options": ["Solo practitioner", "2-5 attorneys", "6-25 attorneys", "26-100 attorneys", "100+ attorneys"]},
                    {"name": "years_in_practice", "type": "select", "required": False, "label": "Years in Practice",
                     "options": ["Less than 1 year", "1-5 years", "6-15 years", "16-25 years", "25+ years"]},
                    {"name": "firm_website", "type": "url", "required": False, "label": "Firm Website"}
                ]
            },
            estimated_time=3,
            required=False,
            role_specific=[UserRole.ATTORNEY, UserRole.PARALEGAL, UserRole.ADMIN]
        ),

        OnboardingStep.PRACTICE_AREAS: OnboardingStepData(
            step=OnboardingStep.PRACTICE_AREAS,
            title="Practice Areas",
            description="Select your primary areas of legal practice.",
            content={
                "areas": [
                    {"value": "corporate", "label": "Corporate Law", "description": "Business formation, contracts, M&A"},
                    {"value": "litigation", "label": "Litigation", "description": "Civil litigation, trial practice"},
                    {"value": "family", "label": "Family Law", "description": "Divorce, custody, adoption"},
                    {"value": "criminal", "label": "Criminal Law", "description": "Criminal defense, DUI"},
                    {"value": "real_estate", "label": "Real Estate", "description": "Property transactions, zoning"},
                    {"value": "immigration", "label": "Immigration", "description": "Visas, citizenship, deportation"},
                    {"value": "bankruptcy", "label": "Bankruptcy", "description": "Chapter 7, Chapter 11, debt relief"},
                    {"value": "intellectual_property", "label": "Intellectual Property", "description": "Patents, trademarks, copyright"},
                    {"value": "employment", "label": "Employment Law", "description": "Workplace issues, discrimination"},
                    {"value": "personal_injury", "label": "Personal Injury", "description": "Accidents, medical malpractice"}
                ],
                "multiple_selection": True,
                "max_selections": 5
            },
            estimated_time=2,
            required=True,
            role_specific=[UserRole.ATTORNEY, UserRole.PARALEGAL]
        ),

        OnboardingStep.STATE_SELECTION: OnboardingStepData(
            step=OnboardingStep.STATE_SELECTION,
            title="Jurisdiction Selection",
            description="Select your primary practice jurisdiction.",
            content={
                "field_type": "select",
                "label": "Primary State/Jurisdiction",
                "options": [
                    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
                    "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
                    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
                    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
                    "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
                    "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
                    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
                    "Federal", "International"
                ],
                "searchable": True
            },
            estimated_time=1,
            required=True
        ),

        OnboardingStep.COMMUNICATION_PREFERENCES: OnboardingStepData(
            step=OnboardingStep.COMMUNICATION_PREFERENCES,
            title="Communication Preferences",
            description="Set up how you'd like to receive notifications and updates.",
            content={
                "preferences": [
                    {
                        "category": "Document Analysis",
                        "options": [
                            {"key": "email_analysis_complete", "label": "Email when analysis is complete", "default": True},
                            {"key": "push_analysis_complete", "label": "Push notification when analysis is complete", "default": True},
                            {"key": "sms_urgent_findings", "label": "SMS for urgent findings", "default": False}
                        ]
                    },
                    {
                        "category": "Case Updates",
                        "options": [
                            {"key": "email_case_updates", "label": "Email for case status changes", "default": True},
                            {"key": "push_case_updates", "label": "Push notifications for case updates", "default": False},
                            {"key": "daily_summary", "label": "Daily summary email", "default": False}
                        ]
                    },
                    {
                        "category": "Deadlines",
                        "options": [
                            {"key": "email_deadline_reminders", "label": "Email deadline reminders", "default": True},
                            {"key": "sms_deadline_reminders", "label": "SMS deadline reminders", "default": True},
                            {"key": "push_deadline_reminders", "label": "Push deadline reminders", "default": True}
                        ]
                    }
                ]
            },
            estimated_time=3,
            required=False
        ),

        OnboardingStep.FIRST_DOCUMENT: OnboardingStepData(
            step=OnboardingStep.FIRST_DOCUMENT,
            title="Upload Your First Document",
            description="Let's analyze your first legal document to show you how the system works.",
            content={
                "instructions": [
                    "Choose a document to upload (PDF, DOCX, or TXT)",
                    "The system will automatically analyze the document",
                    "You'll see key findings, summaries, and insights",
                    "Try asking questions about the document"
                ],
                "sample_documents": [
                    {
                        "name": "Sample Employment Contract",
                        "description": "A standard employment agreement with common clauses",
                        "file": "/samples/employment-contract.pdf"
                    },
                    {
                        "name": "Sample NDA",
                        "description": "A mutual non-disclosure agreement",
                        "file": "/samples/mutual-nda.pdf"
                    },
                    {
                        "name": "Sample Lease Agreement",
                        "description": "A residential lease agreement",
                        "file": "/samples/lease-agreement.pdf"
                    }
                ],
                "upload_types": [".pdf", ".docx", ".txt", ".rtf"],
                "max_size": "10MB"
            },
            estimated_time=5,
            required=False,
            prerequisites=[OnboardingStep.ROLE_SELECTION]
        ),

        OnboardingStep.SAMPLE_ANALYSIS: OnboardingStepData(
            step=OnboardingStep.SAMPLE_ANALYSIS,
            title="Understanding Document Analysis",
            description="Learn how to interpret AI analysis results and use key features.",
            content={
                "tutorial_sections": [
                    {
                        "title": "Analysis Overview",
                        "description": "Understanding the summary and key findings",
                        "duration": "2 min"
                    },
                    {
                        "title": "Risk Assessment",
                        "description": "How to interpret risk scores and recommendations",
                        "duration": "3 min"
                    },
                    {
                        "title": "Key Clauses",
                        "description": "Identifying important terms and provisions",
                        "duration": "2 min"
                    },
                    {
                        "title": "Q&A System",
                        "description": "Asking questions about your documents",
                        "duration": "3 min"
                    }
                ],
                "interactive_elements": [
                    "Click on highlighted text to see explanations",
                    "Try asking sample questions",
                    "Explore the risk assessment panel",
                    "Review the clause analysis section"
                ]
            },
            estimated_time=10,
            required=False,
            prerequisites=[OnboardingStep.FIRST_DOCUMENT]
        ),

        OnboardingStep.FEATURE_TOUR: OnboardingStepData(
            step=OnboardingStep.FEATURE_TOUR,
            title="Platform Tour",
            description="Explore key features and learn navigation shortcuts.",
            content={
                "tour_stops": [
                    {
                        "element": "#dashboard",
                        "title": "Dashboard",
                        "description": "Your central hub for all activities and recent documents",
                        "tips": ["Customize widgets", "View recent activity", "Access quick actions"]
                    },
                    {
                        "element": "#document-library",
                        "title": "Document Library",
                        "description": "Organize and manage all your legal documents",
                        "tips": ["Use folders and tags", "Search across all documents", "Share with team members"]
                    },
                    {
                        "element": "#analysis-workspace",
                        "title": "Analysis Workspace",
                        "description": "Where AI analysis results are displayed and explored",
                        "tips": ["Use split view", "Save analysis notes", "Export reports"]
                    },
                    {
                        "element": "#qa-panel",
                        "title": "Q&A Panel",
                        "description": "Ask questions about your documents and get instant answers",
                        "tips": ["Use natural language", "Reference specific sections", "Save important Q&As"]
                    }
                ],
                "keyboard_shortcuts": [
                    {"key": "Ctrl+U", "action": "Upload document"},
                    {"key": "Ctrl+S", "action": "Save current analysis"},
                    {"key": "Ctrl+F", "action": "Search documents"},
                    {"key": "Ctrl+?", "action": "Show help"}
                ]
            },
            estimated_time=8,
            required=False
        ),

        OnboardingStep.COMPLETION: OnboardingStepData(
            step=OnboardingStep.COMPLETION,
            title="Setup Complete!",
            description="Congratulations! Your Legal AI System is ready to use.",
            content={
                "completion_message": "You've successfully set up your Legal AI System! You're now ready to streamline your legal workflow with AI-powered document analysis and research.",
                "next_steps": [
                    "Upload and analyze your first real document",
                    "Explore the Q&A system with your documents",
                    "Set up your document organization system",
                    "Invite team members to collaborate",
                    "Schedule a follow-up training session"
                ],
                "resources": [
                    {"title": "User Guide", "url": "/help/user-guide", "description": "Comprehensive documentation"},
                    {"title": "Video Tutorials", "url": "/help/videos", "description": "Step-by-step video guides"},
                    {"title": "Support Center", "url": "/support", "description": "Get help when you need it"},
                    {"title": "Community Forum", "url": "/community", "description": "Connect with other users"}
                ],
                "certificate": {
                    "title": "Legal AI System Certified User",
                    "description": "You have completed the onboarding process and are ready to use the Legal AI System effectively.",
                    "downloadable": True
                }
            },
            estimated_time=2,
            required=True
        )
    }

    def __init__(self):
        self.sessions: Dict[str, OnboardingSession] = {}
        self.user_profiles: Dict[str, OnboardingProfile] = {}

    @classmethod
    def get_step_data(cls, step: OnboardingStep) -> Optional[OnboardingStepData]:
        """Get step data by step enum"""
        return cls.STEP_DEFINITIONS.get(step)

    async def start_onboarding(self, user_id: str) -> OnboardingSession:
        """Start a new onboarding session"""
        session_id = str(uuid.uuid4())
        profile = OnboardingProfile(user_id=user_id)

        session = OnboardingSession(
            user_id=user_id,
            session_id=session_id,
            profile=profile,
            current_step=OnboardingStep.WELCOME
        )

        # Initialize progress for all steps
        for step in OnboardingStep:
            session.step_progress[step] = StepProgress(step=step)

        self.sessions[session_id] = session
        self.user_profiles[user_id] = profile

        logger.info(f"Started onboarding session {session_id} for user {user_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Get onboarding session by ID"""
        return self.sessions.get(session_id)

    async def get_user_session(self, user_id: str) -> Optional[OnboardingSession]:
        """Get active onboarding session for user"""
        for session in self.sessions.values():
            if session.user_id == user_id and not session.completed_at:
                return session
        return None

    async def complete_step(
        self,
        session_id: str,
        step: OnboardingStep,
        data: Dict[str, Any]
    ) -> bool:
        """Complete a step in the onboarding process"""
        session = await self.get_session(session_id)
        if not session:
            return False

        # Validate step data
        step_data = self.get_step_data(step)
        if not step_data:
            return False

        # Update step progress
        progress = session.step_progress.get(step)
        if not progress:
            progress = StepProgress(step=step)
            session.step_progress[step] = progress

        progress.complete(data)

        # Update profile based on step data
        await self._update_profile_from_step(session.profile, step, data)

        # Move to next step
        next_step = session.get_next_step()
        session.current_step = next_step

        # Update completion percentage
        session.calculate_completion()

        logger.info(f"Completed step {step.value} in session {session_id}")
        return True

    async def skip_step(self, session_id: str, step: OnboardingStep, reason: str = "") -> bool:
        """Skip a step in the onboarding process"""
        session = await self.get_session(session_id)
        if not session:
            return False

        progress = session.step_progress.get(step)
        if not progress:
            progress = StepProgress(step=step)
            session.step_progress[step] = progress

        progress.skip(reason)

        # Move to next step
        next_step = session.get_next_step()
        session.current_step = next_step

        # Update completion percentage
        session.calculate_completion()

        logger.info(f"Skipped step {step.value} in session {session_id}: {reason}")
        return True

    async def get_step_content(self, step: OnboardingStep, user_role: Optional[UserRole] = None) -> Optional[Dict[str, Any]]:
        """Get content for a specific step"""
        step_data = self.get_step_data(step)
        if not step_data:
            return None

        if user_role and not step_data.is_available_for_role(user_role):
            return None

        return {
            "step": step.value,
            "title": step_data.title,
            "description": step_data.description,
            "content": step_data.content,
            "estimated_time": step_data.estimated_time,
            "required": step_data.required,
            "role_specific": [role.value for role in step_data.role_specific],
            "prerequisites": [prereq.value for prereq in step_data.prerequisites]
        }

    async def get_progress_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get progress summary for a session"""
        session = await self.get_session(session_id)
        if not session:
            return None

        completed_steps = []
        pending_steps = []
        skipped_steps = []

        role = session.profile.role or UserRole.ATTORNEY

        for step in OnboardingStep:
            step_data = self.get_step_data(step)
            if not step_data or not step_data.is_available_for_role(role):
                continue

            progress = session.step_progress.get(step)
            if not progress:
                continue

            step_info = {
                "step": step.value,
                "title": step_data.title,
                "status": progress.status.value,
                "estimated_time": step_data.estimated_time
            }

            if progress.status == OnboardingStatus.COMPLETED:
                step_info["completed_at"] = progress.completed_at.isoformat() if progress.completed_at else None
                completed_steps.append(step_info)
            elif progress.status == OnboardingStatus.SKIPPED:
                step_info["skipped_at"] = progress.skipped_at.isoformat() if progress.skipped_at else None
                skipped_steps.append(step_info)
            else:
                pending_steps.append(step_info)

        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "current_step": session.current_step.value if session.current_step else None,
            "completion_percentage": session.completion_percentage,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "completed_steps": completed_steps,
            "pending_steps": pending_steps,
            "skipped_steps": skipped_steps,
            "total_estimated_time": sum(step["estimated_time"] for step in pending_steps)
        }

    async def _update_profile_from_step(self, profile: OnboardingProfile, step: OnboardingStep, data: Dict[str, Any]):
        """Update user profile based on completed step data"""
        if step == OnboardingStep.ROLE_SELECTION:
            if "role" in data:
                profile.role = UserRole(data["role"])

        elif step == OnboardingStep.FIRM_PROFILE:
            profile.firm_name = data.get("firm_name")
            profile.firm_size = data.get("firm_size")
            profile.experience_level = data.get("years_in_practice")

        elif step == OnboardingStep.PRACTICE_AREAS:
            if "practice_areas" in data:
                profile.practice_areas = [PracticeArea(area) for area in data["practice_areas"]]

        elif step == OnboardingStep.STATE_SELECTION:
            profile.state = data.get("state")

        elif step == OnboardingStep.COMMUNICATION_PREFERENCES:
            profile.communication_preferences = data.get("preferences", {})

        profile.update()

    async def get_role_based_recommendations(self, session_id: str) -> Dict[str, Any]:
        """Get personalized recommendations based on user role and profile"""
        session = await self.get_session(session_id)
        if not session:
            return {}

        role = session.profile.role
        practice_areas = session.profile.practice_areas

        recommendations = {
            "templates": [],
            "workflows": [],
            "integrations": [],
            "training": []
        }

        if role == UserRole.ATTORNEY:
            recommendations["templates"] = [
                "Client intake forms",
                "Retainer agreements",
                "Case status updates",
                "Billing templates"
            ]
            recommendations["workflows"] = [
                "Document review process",
                "Client communication flow",
                "Deadline management",
                "Time tracking setup"
            ]
            recommendations["integrations"] = [
                "Calendar integration",
                "CRM connection",
                "Billing software",
                "Court filing systems"
            ]

        elif role == UserRole.PARALEGAL:
            recommendations["templates"] = [
                "Research memo templates",
                "Discovery documents",
                "Filing checklists",
                "Client correspondence"
            ]
            recommendations["workflows"] = [
                "Research methodology",
                "Document organization",
                "Case preparation",
                "Administrative tasks"
            ]

        elif role == UserRole.CLIENT:
            recommendations["workflows"] = [
                "Document submission",
                "Status checking",
                "Communication with attorney",
                "Payment processing"
            ]

        # Practice area specific recommendations
        if PracticeArea.CORPORATE in practice_areas:
            recommendations["templates"].extend([
                "Contract templates",
                "Board resolutions",
                "Securities filings"
            ])

        if PracticeArea.LITIGATION in practice_areas:
            recommendations["templates"].extend([
                "Motion templates",
                "Discovery requests",
                "Brief formats"
            ])

        return recommendations

    async def export_onboarding_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export complete onboarding data for analysis or transfer"""
        session = await self.get_session(session_id)
        if not session:
            return None

        return {
            "session": {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "completion_percentage": session.completion_percentage,
                "current_step": session.current_step.value if session.current_step else None
            },
            "profile": session.profile.to_dict(),
            "step_progress": {
                step.value: {
                    "status": progress.status.value,
                    "started_at": progress.started_at.isoformat() if progress.started_at else None,
                    "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                    "skipped_at": progress.skipped_at.isoformat() if progress.skipped_at else None,
                    "data": progress.data,
                    "attempts": progress.attempts
                }
                for step, progress in session.step_progress.items()
            }
        }


# Global onboarding wizard instance
onboarding_wizard = OnboardingWizard()


# FastAPI endpoints
def get_onboarding_endpoints():
    """Returns FastAPI endpoints for onboarding wizard"""
    from fastapi import APIRouter, HTTPException, Depends
    from pydantic import BaseModel
    from typing import Optional, List, Dict, Any

    router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

    class StartOnboardingRequest(BaseModel):
        user_id: str

    class CompleteStepRequest(BaseModel):
        step: str
        data: Dict[str, Any]

    class SkipStepRequest(BaseModel):
        step: str
        reason: Optional[str] = ""

    @router.post("/start")
    async def start_onboarding(request: StartOnboardingRequest):
        """Start new onboarding session"""
        try:
            session = await onboarding_wizard.start_onboarding(request.user_id)
            return {
                "session_id": session.session_id,
                "current_step": session.current_step.value if session.current_step else None,
                "profile": session.profile.to_dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/session/{session_id}")
    async def get_session(session_id: str):
        """Get onboarding session"""
        session = await onboarding_wizard.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "current_step": session.current_step.value if session.current_step else None,
            "completion_percentage": session.completion_percentage,
            "profile": session.profile.to_dict()
        }

    @router.get("/user/{user_id}/session")
    async def get_user_session(user_id: str):
        """Get active session for user"""
        session = await onboarding_wizard.get_user_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="No active session found")

        return {
            "session_id": session.session_id,
            "current_step": session.current_step.value if session.current_step else None,
            "completion_percentage": session.completion_percentage
        }

    @router.get("/step/{step}")
    async def get_step_content(step: str, role: Optional[str] = None):
        """Get content for specific step"""
        try:
            step_enum = OnboardingStep(step)
            role_enum = UserRole(role) if role else None

            content = await onboarding_wizard.get_step_content(step_enum, role_enum)
            if not content:
                raise HTTPException(status_code=404, detail="Step not found or not available for role")

            return content
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid step or role")

    @router.post("/session/{session_id}/complete-step")
    async def complete_step(session_id: str, request: CompleteStepRequest):
        """Complete onboarding step"""
        try:
            step_enum = OnboardingStep(request.step)
            success = await onboarding_wizard.complete_step(session_id, step_enum, request.data)

            if not success:
                raise HTTPException(status_code=400, detail="Failed to complete step")

            session = await onboarding_wizard.get_session(session_id)
            return {
                "success": True,
                "current_step": session.current_step.value if session.current_step else None,
                "completion_percentage": session.completion_percentage
            }
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid step")

    @router.post("/session/{session_id}/skip-step")
    async def skip_step(session_id: str, request: SkipStepRequest):
        """Skip onboarding step"""
        try:
            step_enum = OnboardingStep(request.step)
            success = await onboarding_wizard.skip_step(session_id, step_enum, request.reason)

            if not success:
                raise HTTPException(status_code=400, detail="Failed to skip step")

            session = await onboarding_wizard.get_session(session_id)
            return {
                "success": True,
                "current_step": session.current_step.value if session.current_step else None,
                "completion_percentage": session.completion_percentage
            }
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid step")

    @router.get("/session/{session_id}/progress")
    async def get_progress(session_id: str):
        """Get session progress summary"""
        progress = await onboarding_wizard.get_progress_summary(session_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Session not found")
        return progress

    @router.get("/session/{session_id}/recommendations")
    async def get_recommendations(session_id: str):
        """Get role-based recommendations"""
        recommendations = await onboarding_wizard.get_role_based_recommendations(session_id)
        return recommendations

    @router.get("/session/{session_id}/export")
    async def export_data(session_id: str):
        """Export onboarding data"""
        data = await onboarding_wizard.export_onboarding_data(session_id)
        if not data:
            raise HTTPException(status_code=404, detail="Session not found")
        return data

    @router.get("/steps")
    async def get_all_steps():
        """Get all available onboarding steps"""
        steps = []
        for step, step_data in OnboardingWizard.STEP_DEFINITIONS.items():
            steps.append({
                "step": step.value,
                "title": step_data.title,
                "description": step_data.description,
                "estimated_time": step_data.estimated_time,
                "required": step_data.required,
                "role_specific": [role.value for role in step_data.role_specific]
            })
        return steps

    return router


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        wizard = OnboardingWizard()

        # Start onboarding
        session = await wizard.start_onboarding("user123")
        print(f"Started session: {session.session_id}")

        # Complete role selection
        await wizard.complete_step(session.session_id, OnboardingStep.ROLE_SELECTION, {
            "role": "attorney"
        })

        # Complete practice areas
        await wizard.complete_step(session.session_id, OnboardingStep.PRACTICE_AREAS, {
            "practice_areas": ["corporate", "litigation"]
        })

        # Get progress
        progress = await wizard.get_progress_summary(session.session_id)
        print(f"Progress: {progress['completion_percentage']:.1f}%")

        # Get recommendations
        recommendations = await wizard.get_role_based_recommendations(session.session_id)
        print(f"Templates: {recommendations['templates']}")

        print("Onboarding wizard demo completed!")

    asyncio.run(demo())