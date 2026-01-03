"""
Contextual Help and Tooltips System
Provides smart, contextual help that adapts to user roles, experience levels, and current tasks.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import json
import re
from collections import defaultdict


class HelpTriggerType(Enum):
    HOVER = "hover"              # On element hover
    CLICK = "click"              # On element click
    FOCUS = "focus"              # On input focus
    ERROR = "error"              # On error occurrence
    FIRST_TIME = "first_time"    # First time visiting element
    CONTEXT_CHANGE = "context_change"  # When context changes
    IDLE = "idle"                # After period of inactivity
    REQUEST = "request"          # User explicitly requests help


class HelpContentType(Enum):
    TOOLTIP = "tooltip"          # Brief hover text
    POPOVER = "popover"          # Expandable popup
    MODAL = "modal"              # Full modal dialog
    SPOTLIGHT = "spotlight"      # Highlight with overlay
    TOUR_STEP = "tour_step"      # Guided tour step
    INLINE = "inline"            # Inline text/instructions
    VIDEO = "video"              # Video help
    INTERACTIVE = "interactive"  # Interactive tutorial


class HelpPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HelpContent:
    content_id: str
    title: str
    content: str
    content_type: HelpContentType
    trigger_type: HelpTriggerType
    priority: HelpPriority = HelpPriority.MEDIUM
    target_roles: List[str] = field(default_factory=list)
    target_experience_levels: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    media_url: Optional[str] = None
    duration_estimate: Optional[int] = None  # seconds
    interaction_required: bool = False
    auto_dismiss_timeout: Optional[int] = None  # seconds
    show_count_limit: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContextualElement:
    element_id: str
    selector: str  # CSS selector for targeting
    page_url: str
    section: str
    element_type: str  # button, input, link, etc.
    help_contents: List[str] = field(default_factory=list)  # content_ids
    fallback_help: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    tracking_enabled: bool = True


@dataclass
class UserHelpInteraction:
    user_id: str
    content_id: str
    element_id: Optional[str]
    interaction_type: str  # viewed, dismissed, completed, clicked_link, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    helpful_rating: Optional[int] = None  # 1-5 rating


@dataclass
class HelpAnalytics:
    content_id: str
    total_views: int = 0
    unique_users: int = 0
    average_view_duration: float = 0.0
    completion_rate: float = 0.0
    helpfulness_score: float = 0.0
    dismissal_rate: float = 0.0
    common_next_actions: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)


class ContextualHelpSystem:
    """Smart contextual help system with adaptive content"""

    def __init__(self):
        self.help_contents: Dict[str, HelpContent] = {}
        self.contextual_elements: Dict[str, ContextualElement] = {}
        self.user_interactions: Dict[str, List[UserHelpInteraction]] = defaultdict(list)
        self.help_analytics: Dict[str, HelpAnalytics] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_help_content()
        self._initialize_contextual_elements()

    def _initialize_default_help_content(self):
        """Initialize default help content library"""

        help_contents = [
            HelpContent(
                content_id="document_upload_tooltip",
                title="Upload Document",
                content="Click here to upload legal documents for AI analysis. Supported formats: PDF, DOCX, TXT.",
                content_type=HelpContentType.TOOLTIP,
                trigger_type=HelpTriggerType.HOVER,
                target_roles=["attorney", "paralegal", "client"],
                target_experience_levels=["beginner", "intermediate"],
                auto_dismiss_timeout=5
            ),
            HelpContent(
                content_id="document_upload_first_time",
                title="Welcome to Document Analysis",
                content="""
                <div class="help-popover">
                    <h3>Upload Your First Document</h3>
                    <p>To get started with AI-powered legal analysis:</p>
                    <ol>
                        <li>Click the upload button or drag files here</li>
                        <li>Select a legal document (PDF, DOCX, or TXT)</li>
                        <li>Choose the document type for better analysis</li>
                        <li>Click 'Analyze' to begin processing</li>
                    </ol>
                    <p><strong>Tip:</strong> Contracts and briefs work best with our AI models.</p>
                </div>
                """,
                content_type=HelpContentType.POPOVER,
                trigger_type=HelpTriggerType.FIRST_TIME,
                target_experience_levels=["beginner"],
                duration_estimate=45,
                show_count_limit=3
            ),
            HelpContent(
                content_id="analysis_progress_help",
                title="Document Analysis in Progress",
                content="Your document is being analyzed by our AI. This typically takes 30-60 seconds depending on document length.",
                content_type=HelpContentType.INLINE,
                trigger_type=HelpTriggerType.CONTEXT_CHANGE,
                auto_dismiss_timeout=10
            ),
            HelpContent(
                content_id="search_filters_tutorial",
                title="Advanced Search Filters",
                content="""
                <div class="help-tour">
                    <h3>Filter Your Search Results</h3>
                    <p>Use these filters to narrow down your legal research:</p>
                    <ul>
                        <li><strong>Jurisdiction:</strong> Select federal, state, or local courts</li>
                        <li><strong>Date Range:</strong> Focus on recent or historical cases</li>
                        <li><strong>Case Type:</strong> Filter by civil, criminal, appellate, etc.</li>
                        <li><strong>Citation:</strong> Find specific cases by citation format</li>
                    </ul>
                </div>
                """,
                content_type=HelpContentType.TOUR_STEP,
                trigger_type=HelpTriggerType.CLICK,
                target_roles=["attorney", "paralegal"],
                target_experience_levels=["intermediate", "advanced"],
                duration_estimate=60
            ),
            HelpContent(
                content_id="client_portal_intro",
                title="Client Portal Overview",
                content="""
                Welcome to your secure client portal! Here you can:
                • View your case status and timeline
                • Access shared documents securely
                • Communicate with your legal team
                • Schedule appointments
                • Review and approve legal actions

                All information is encrypted and HIPAA-compliant.
                """,
                content_type=HelpContentType.MODAL,
                trigger_type=HelpTriggerType.FIRST_TIME,
                target_roles=["client"],
                duration_estimate=90,
                show_count_limit=1
            ),
            HelpContent(
                content_id="billing_integration_help",
                title="Time Tracking Integration",
                content="This feature automatically tracks time spent on document analysis for billing purposes. Time starts when analysis begins and stops when you finish reviewing results.",
                content_type=HelpContentType.TOOLTIP,
                trigger_type=HelpTriggerType.HOVER,
                target_roles=["attorney"],
                auto_dismiss_timeout=7
            ),
            HelpContent(
                content_id="error_document_format",
                title="Unsupported Document Format",
                content="""
                <div class="error-help">
                    <h3>File Format Not Supported</h3>
                    <p>The document you uploaded is not in a supported format.</p>
                    <h4>Supported formats:</h4>
                    <ul>
                        <li>PDF (.pdf)</li>
                        <li>Word Document (.docx, .doc)</li>
                        <li>Plain Text (.txt)</li>
                        <li>Rich Text Format (.rtf)</li>
                    </ul>
                    <h4>Solutions:</h4>
                    <ol>
                        <li>Convert your document to a supported format</li>
                        <li>For images: Use OCR software to extract text first</li>
                        <li>For other formats: Copy text and save as .txt file</li>
                    </ol>
                </div>
                """,
                content_type=HelpContentType.MODAL,
                trigger_type=HelpTriggerType.ERROR,
                priority=HelpPriority.HIGH,
                duration_estimate=30
            ),
            HelpContent(
                content_id="keyboard_shortcuts",
                title="Keyboard Shortcuts",
                content="""
                <div class="shortcuts-help">
                    <h3>Keyboard Shortcuts</h3>
                    <div class="shortcut-group">
                        <h4>Navigation:</h4>
                        <ul>
                            <li><kbd>Ctrl</kbd> + <kbd>U</kbd> - Upload document</li>
                            <li><kbd>Ctrl</kbd> + <kbd>S</kbd> - Save analysis</li>
                            <li><kbd>Ctrl</kbd> + <kbd>F</kbd> - Search in document</li>
                            <li><kbd>Ctrl</kbd> + <kbd>H</kbd> - Show help</li>
                        </ul>
                    </div>
                    <div class="shortcut-group">
                        <h4>Analysis:</h4>
                        <ul>
                            <li><kbd>Ctrl</kbd> + <kbd>Enter</kbd> - Start analysis</li>
                            <li><kbd>Esc</kbd> - Cancel current action</li>
                            <li><kbd>Tab</kbd> - Navigate between sections</li>
                        </ul>
                    </div>
                </div>
                """,
                content_type=HelpContentType.MODAL,
                trigger_type=HelpTriggerType.REQUEST,
                target_experience_levels=["intermediate", "advanced"],
                tags=["shortcuts", "efficiency"]
            ),
            HelpContent(
                content_id="idle_help_suggestion",
                title="Need help getting started?",
                content="It looks like you might be looking for something. Try uploading a document to analyze, or browse our help center for tutorials and guides.",
                content_type=HelpContentType.POPOVER,
                trigger_type=HelpTriggerType.IDLE,
                target_experience_levels=["beginner"],
                auto_dismiss_timeout=10,
                show_count_limit=2
            )
        ]

        for content in help_contents:
            self.help_contents[content.content_id] = content

    def _initialize_contextual_elements(self):
        """Initialize contextual elements mapping"""

        elements = [
            ContextualElement(
                element_id="document_upload_button",
                selector="[data-testid='upload-button'], #upload-btn, .upload-button",
                page_url="/dashboard",
                section="document_management",
                element_type="button",
                help_contents=["document_upload_tooltip", "document_upload_first_time"]
            ),
            ContextualElement(
                element_id="search_filters_panel",
                selector=".search-filters, [data-testid='search-filters']",
                page_url="/research",
                section="legal_research",
                element_type="panel",
                help_contents=["search_filters_tutorial"]
            ),
            ContextualElement(
                element_id="client_portal_dashboard",
                selector=".client-dashboard, [data-testid='client-dashboard']",
                page_url="/client",
                section="client_portal",
                element_type="dashboard",
                help_contents=["client_portal_intro"]
            ),
            ContextualElement(
                element_id="billing_timer",
                selector=".billing-timer, [data-testid='time-tracker']",
                page_url="/dashboard",
                section="billing",
                element_type="widget",
                help_contents=["billing_integration_help"],
                conditions={"user_role": ["attorney"]}
            )
        ]

        for element in elements:
            self.contextual_elements[element.element_id] = element

    async def get_contextual_help(
        self,
        user_id: str,
        element_id: Optional[str] = None,
        page_url: Optional[str] = None,
        trigger_type: HelpTriggerType = HelpTriggerType.HOVER,
        context: Dict[str, Any] = None
    ) -> List[HelpContent]:
        """Get contextual help based on element and user context"""

        if context is None:
            context = {}

        # Get user profile for filtering
        user_role = context.get("user_role", "attorney")
        experience_level = context.get("experience_level", "intermediate")

        # Get user preferences
        user_prefs = self.user_preferences.get(user_id, {})
        help_enabled = user_prefs.get("help_enabled", True)

        if not help_enabled:
            return []

        relevant_help = []

        # If specific element requested
        if element_id and element_id in self.contextual_elements:
            element = self.contextual_elements[element_id]

            # Check element conditions
            if element.conditions:
                if "user_role" in element.conditions:
                    if user_role not in element.conditions["user_role"]:
                        return []

            # Get help contents for this element
            for content_id in element.help_contents:
                if content_id in self.help_contents:
                    content = self.help_contents[content_id]
                    if await self._should_show_help(user_id, content, trigger_type, context):
                        relevant_help.append(content)

        # If no element-specific help, search by page/context
        elif page_url:
            for element in self.contextual_elements.values():
                if element.page_url == page_url:
                    for content_id in element.help_contents:
                        if content_id in self.help_contents:
                            content = self.help_contents[content_id]
                            if await self._should_show_help(user_id, content, trigger_type, context):
                                relevant_help.append(content)

        # Sort by priority and relevance
        relevant_help.sort(key=lambda x: (
            x.priority.value,
            -len([r for r in x.target_roles if r == user_role]),
            -len([e for e in x.target_experience_levels if e == experience_level])
        ), reverse=True)

        return relevant_help[:3]  # Limit to top 3 most relevant

    async def _should_show_help(
        self,
        user_id: str,
        content: HelpContent,
        trigger_type: HelpTriggerType,
        context: Dict[str, Any]
    ) -> bool:
        """Determine if help content should be shown to user"""

        # Check trigger type match
        if content.trigger_type != trigger_type:
            return False

        # Check role targeting
        if content.target_roles:
            user_role = context.get("user_role", "attorney")
            if user_role not in content.target_roles:
                return False

        # Check experience level targeting
        if content.target_experience_levels:
            experience_level = context.get("experience_level", "intermediate")
            if experience_level not in content.target_experience_levels:
                return False

        # Check show count limits
        if content.show_count_limit:
            user_interactions = self.user_interactions.get(user_id, [])
            view_count = len([
                i for i in user_interactions
                if i.content_id == content.content_id and i.interaction_type == "viewed"
            ])
            if view_count >= content.show_count_limit:
                return False

        # Check prerequisites
        if content.prerequisites:
            user_interactions = self.user_interactions.get(user_id, [])
            for prereq in content.prerequisites:
                prereq_completed = any(
                    i.content_id == prereq and i.interaction_type == "completed"
                    for i in user_interactions
                )
                if not prereq_completed:
                    return False

        return True

    async def record_help_interaction(
        self,
        user_id: str,
        content_id: str,
        interaction_type: str,
        element_id: Optional[str] = None,
        context: Dict[str, Any] = None,
        session_id: Optional[str] = None,
        helpful_rating: Optional[int] = None
    ):
        """Record user interaction with help content"""

        interaction = UserHelpInteraction(
            user_id=user_id,
            content_id=content_id,
            element_id=element_id,
            interaction_type=interaction_type,
            context=context or {},
            session_id=session_id,
            helpful_rating=helpful_rating
        )

        self.user_interactions[user_id].append(interaction)
        await self._update_help_analytics(content_id, interaction)

    async def _update_help_analytics(self, content_id: str, interaction: UserHelpInteraction):
        """Update analytics for help content"""

        if content_id not in self.help_analytics:
            self.help_analytics[content_id] = HelpAnalytics(content_id=content_id)

        analytics = self.help_analytics[content_id]

        if interaction.interaction_type == "viewed":
            analytics.total_views += 1
            # Update unique users count
            unique_users = len(set(
                i.user_id for i in self.user_interactions.values()
                for i in i if i.content_id == content_id and i.interaction_type == "viewed"
            ))
            analytics.unique_users = unique_users

        elif interaction.interaction_type == "completed":
            # Update completion rate
            total_views = analytics.total_views
            completed_views = len([
                i for interactions in self.user_interactions.values()
                for i in interactions
                if i.content_id == content_id and i.interaction_type == "completed"
            ])
            analytics.completion_rate = (completed_views / total_views * 100) if total_views > 0 else 0

        elif interaction.interaction_type == "dismissed":
            # Update dismissal rate
            total_views = analytics.total_views
            dismissed_views = len([
                i for interactions in self.user_interactions.values()
                for i in interactions
                if i.content_id == content_id and i.interaction_type == "dismissed"
            ])
            analytics.dismissal_rate = (dismissed_views / total_views * 100) if total_views > 0 else 0

        if interaction.helpful_rating:
            # Update helpfulness score
            all_ratings = [
                i.helpful_rating for interactions in self.user_interactions.values()
                for i in interactions
                if i.content_id == content_id and i.helpful_rating is not None
            ]
            analytics.helpfulness_score = sum(all_ratings) / len(all_ratings) if all_ratings else 0

        analytics.updated_at = datetime.now()

    async def get_help_suggestions(
        self,
        user_id: str,
        current_page: str,
        user_actions: List[str],
        context: Dict[str, Any] = None
    ) -> List[HelpContent]:
        """Get proactive help suggestions based on user behavior"""

        suggestions = []

        # Analyze user behavior patterns
        user_interactions = self.user_interactions.get(user_id, [])
        recent_interactions = [
            i for i in user_interactions
            if i.timestamp > datetime.now() - timedelta(minutes=30)
        ]

        # Check for error patterns
        error_interactions = [i for i in recent_interactions if "error" in i.interaction_type]
        if error_interactions:
            # Suggest error-related help
            error_helps = [
                content for content in self.help_contents.values()
                if content.trigger_type == HelpTriggerType.ERROR
            ]
            suggestions.extend(error_helps[:2])

        # Check for idle behavior
        if len(recent_interactions) == 0:
            idle_helps = [
                content for content in self.help_contents.values()
                if content.trigger_type == HelpTriggerType.IDLE
            ]
            suggestions.extend(idle_helps[:1])

        # Check for first-time user patterns
        total_interactions = len(user_interactions)
        if total_interactions < 5:
            first_time_helps = [
                content for content in self.help_contents.values()
                if content.trigger_type == HelpTriggerType.FIRST_TIME
            ]
            suggestions.extend(first_time_helps[:2])

        return suggestions

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ):
        """Update user help preferences"""

        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id].update(preferences)

    async def get_help_analytics_summary(self) -> Dict[str, Any]:
        """Get overall help system analytics"""

        total_contents = len(self.help_contents)
        total_interactions = sum(len(interactions) for interactions in self.user_interactions.values())

        # Most helpful content
        most_helpful = sorted(
            self.help_analytics.values(),
            key=lambda x: x.helpfulness_score,
            reverse=True
        )[:5]

        # Most viewed content
        most_viewed = sorted(
            self.help_analytics.values(),
            key=lambda x: x.total_views,
            reverse=True
        )[:5]

        # Content with high dismissal rates (needs improvement)
        high_dismissal = [
            analytics for analytics in self.help_analytics.values()
            if analytics.dismissal_rate > 50 and analytics.total_views > 10
        ]

        return {
            "total_help_contents": total_contents,
            "total_user_interactions": total_interactions,
            "unique_users_helped": len(self.user_interactions),
            "most_helpful_content": [
                {
                    "content_id": analytics.content_id,
                    "helpfulness_score": round(analytics.helpfulness_score, 2),
                    "total_views": analytics.total_views
                }
                for analytics in most_helpful
            ],
            "most_viewed_content": [
                {
                    "content_id": analytics.content_id,
                    "total_views": analytics.total_views,
                    "completion_rate": round(analytics.completion_rate, 1)
                }
                for analytics in most_viewed
            ],
            "content_needing_improvement": [
                {
                    "content_id": analytics.content_id,
                    "dismissal_rate": round(analytics.dismissal_rate, 1),
                    "total_views": analytics.total_views
                }
                for analytics in high_dismissal
            ]
        }

    async def add_help_content(self, content: HelpContent) -> str:
        """Add new help content"""
        self.help_contents[content.content_id] = content
        return content.content_id

    async def update_help_content(self, content_id: str, updates: Dict[str, Any]) -> HelpContent:
        """Update existing help content"""
        if content_id not in self.help_contents:
            raise ValueError(f"Help content '{content_id}' not found")

        content = self.help_contents[content_id]
        for key, value in updates.items():
            if hasattr(content, key):
                setattr(content, key, value)

        content.updated_at = datetime.now()
        return content

    async def search_help_content(
        self,
        query: str,
        user_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> List[HelpContent]:
        """Search help content by query"""

        query_lower = query.lower()
        matching_content = []

        for content in self.help_contents.values():
            score = 0

            # Title match (highest weight)
            if query_lower in content.title.lower():
                score += 10

            # Content match
            if query_lower in content.content.lower():
                score += 5

            # Tag match
            if any(query_lower in tag.lower() for tag in content.tags):
                score += 3

            if score > 0:
                matching_content.append((content, score))

        # Sort by score
        matching_content.sort(key=lambda x: x[1], reverse=True)

        return [content for content, score in matching_content]


# Pydantic models for API
class HelpContentModel(BaseModel):
    content_id: str
    title: str
    content: str
    content_type: HelpContentType
    trigger_type: HelpTriggerType
    priority: HelpPriority
    target_roles: List[str]
    target_experience_levels: List[str]
    prerequisites: List[str]
    tags: List[str]
    media_url: Optional[str] = None
    duration_estimate: Optional[int] = None
    interaction_required: bool
    auto_dismiss_timeout: Optional[int] = None
    show_count_limit: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HelpInteractionModel(BaseModel):
    content_id: str
    interaction_type: str
    element_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    helpful_rating: Optional[int] = Field(None, ge=1, le=5)


class HelpRequestModel(BaseModel):
    element_id: Optional[str] = None
    page_url: Optional[str] = None
    trigger_type: HelpTriggerType = HelpTriggerType.HOVER
    context: Optional[Dict[str, Any]] = None


class UserPreferencesModel(BaseModel):
    help_enabled: bool = True
    tooltip_delay: int = 1000  # milliseconds
    auto_dismiss: bool = True
    show_keyboard_shortcuts: bool = True
    proactive_suggestions: bool = True
    content_types_enabled: List[HelpContentType] = Field(default_factory=lambda: list(HelpContentType))


# Global instance
contextual_help_system = ContextualHelpSystem()


def get_contextual_help_endpoints() -> APIRouter:
    """Get contextual help system FastAPI endpoints"""
    router = APIRouter(prefix="/contextual-help", tags=["contextual_help"])

    @router.post("/get-help/{user_id}", response_model=List[HelpContentModel])
    async def get_contextual_help(user_id: str, request: HelpRequestModel):
        """Get contextual help for user"""
        help_contents = await contextual_help_system.get_contextual_help(
            user_id,
            request.element_id,
            request.page_url,
            request.trigger_type,
            request.context
        )
        return [HelpContentModel(**content.__dict__) for content in help_contents]

    @router.post("/interaction/{user_id}")
    async def record_help_interaction(user_id: str, interaction: HelpInteractionModel):
        """Record user interaction with help content"""
        await contextual_help_system.record_help_interaction(
            user_id,
            interaction.content_id,
            interaction.interaction_type,
            interaction.element_id,
            interaction.context,
            interaction.session_id,
            interaction.helpful_rating
        )
        return {"status": "recorded"}

    @router.get("/suggestions/{user_id}", response_model=List[HelpContentModel])
    async def get_help_suggestions(
        user_id: str,
        current_page: str = Query(...),
        user_actions: List[str] = Query([]),
        context: Optional[str] = Query(None)
    ):
        """Get proactive help suggestions"""
        context_dict = json.loads(context) if context else {}
        suggestions = await contextual_help_system.get_help_suggestions(
            user_id, current_page, user_actions, context_dict
        )
        return [HelpContentModel(**content.__dict__) for content in suggestions]

    @router.put("/preferences/{user_id}")
    async def update_user_help_preferences(user_id: str, preferences: UserPreferencesModel):
        """Update user help preferences"""
        await contextual_help_system.update_user_preferences(
            user_id, preferences.dict()
        )
        return {"status": "updated"}

    @router.get("/search")
    async def search_help_content(
        query: str = Query(...),
        user_id: Optional[str] = Query(None),
        context: Optional[str] = Query(None)
    ):
        """Search help content"""
        context_dict = json.loads(context) if context else {}
        results = await contextual_help_system.search_help_content(
            query, user_id, context_dict
        )
        return [HelpContentModel(**content.__dict__) for content in results]

    @router.get("/analytics")
    async def get_help_analytics():
        """Get help system analytics"""
        return await contextual_help_system.get_help_analytics_summary()

    @router.post("/content", response_model=str)
    async def add_help_content(content: HelpContentModel):
        """Add new help content"""
        help_content = HelpContent(**content.dict())
        return await contextual_help_system.add_help_content(help_content)

    @router.put("/content/{content_id}", response_model=HelpContentModel)
    async def update_help_content(content_id: str, updates: Dict[str, Any]):
        """Update existing help content"""
        try:
            updated_content = await contextual_help_system.update_help_content(content_id, updates)
            return HelpContentModel(**updated_content.__dict__)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/content", response_model=List[HelpContentModel])
    async def list_help_content(
        content_type: Optional[HelpContentType] = Query(None),
        trigger_type: Optional[HelpTriggerType] = Query(None),
        target_role: Optional[str] = Query(None)
    ):
        """List help content with optional filters"""
        contents = list(contextual_help_system.help_contents.values())

        if content_type:
            contents = [c for c in contents if c.content_type == content_type]
        if trigger_type:
            contents = [c for c in contents if c.trigger_type == trigger_type]
        if target_role:
            contents = [c for c in contents if target_role in c.target_roles]

        return [HelpContentModel(**content.__dict__) for content in contents]

    return router


async def initialize_contextual_help_system():
    """Initialize the contextual help system"""
    print("Initializing contextual help and tooltips system...")

    # Test the system with sample interactions
    sample_user_id = "demo_user"

    # Simulate getting help
    help_contents = await contextual_help_system.get_contextual_help(
        sample_user_id,
        element_id="document_upload_button",
        trigger_type=HelpTriggerType.HOVER,
        context={"user_role": "attorney", "experience_level": "beginner"}
    )

    if help_contents:
        await contextual_help_system.record_help_interaction(
            sample_user_id,
            help_contents[0].content_id,
            "viewed"
        )

    print("✓ Contextual help system initialized")
    print("✓ Default help content library loaded")
    print("✓ Element mapping configured")
    print("✓ Analytics tracking enabled")
    print("💡 Contextual help and tooltips system ready!")