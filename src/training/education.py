"""
Comprehensive Training and Education System
Provides video tutorials, interactive guides, progress tracking,
and personalized learning paths for legal AI system users.
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


class ContentType(Enum):
    VIDEO_TUTORIAL = "video_tutorial"
    INTERACTIVE_GUIDE = "interactive_guide"
    DOCUMENT = "document"
    QUIZ = "quiz"
    WEBINAR = "webinar"
    DEMO = "demo"


class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UserRole(Enum):
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    ADMIN = "admin"


class CompletionStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class LearningObjective(Enum):
    GETTING_STARTED = "getting_started"
    DOCUMENT_UPLOAD = "document_upload"
    ANALYSIS_UNDERSTANDING = "analysis_understanding"
    QA_SYSTEM_USAGE = "qa_system_usage"
    ATTORNEY_ACCOUNTABILITY = "attorney_accountability"
    ADVANCED_FEATURES = "advanced_features"
    COLLABORATION = "collaboration"
    SECURITY_COMPLIANCE = "security_compliance"
    INTEGRATION = "integration"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class LearningContent:
    """Individual learning content item"""
    content_id: str
    title: str
    description: str
    content_type: ContentType
    difficulty: DifficultyLevel
    duration_minutes: int
    objectives: List[LearningObjective]
    target_roles: List[UserRole] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # content_ids
    tags: List[str] = field(default_factory=list)
    video_url: Optional[str] = None
    transcript: Optional[str] = None
    interactive_elements: List[Dict[str, Any]] = field(default_factory=list)
    quiz_questions: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_available_for_role(self, role: UserRole) -> bool:
        """Check if content is available for the given role"""
        if not self.target_roles:
            return True
        return role in self.target_roles

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'content_id': self.content_id,
            'title': self.title,
            'description': self.description,
            'content_type': self.content_type.value,
            'difficulty': self.difficulty.value,
            'duration_minutes': self.duration_minutes,
            'objectives': [obj.value for obj in self.objectives],
            'target_roles': [role.value for role in self.target_roles],
            'prerequisites': self.prerequisites,
            'tags': self.tags,
            'video_url': self.video_url,
            'transcript': self.transcript,
            'interactive_elements': self.interactive_elements,
            'quiz_questions': self.quiz_questions,
            'resources': self.resources,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class LearningProgress:
    """User progress on a learning content item"""
    user_id: str
    content_id: str
    status: CompletionStatus = CompletionStatus.NOT_STARTED
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    time_spent_minutes: int = 0
    quiz_scores: List[float] = field(default_factory=list)
    bookmarks: List[int] = field(default_factory=list)  # Timestamp bookmarks
    notes: List[Dict[str, Any]] = field(default_factory=list)
    rating: Optional[int] = None
    feedback: Optional[str] = None

    def start(self):
        """Mark content as started"""
        if self.status == CompletionStatus.NOT_STARTED:
            self.status = CompletionStatus.IN_PROGRESS
            self.started_at = datetime.now()
        self.last_accessed = datetime.now()

    def update_progress(self, percentage: float):
        """Update progress percentage"""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        self.last_accessed = datetime.now()

    def complete(self, final_score: Optional[float] = None):
        """Mark content as completed"""
        self.status = CompletionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress_percentage = 100.0
        if final_score is not None:
            self.quiz_scores.append(final_score)

    def add_bookmark(self, timestamp: int):
        """Add timestamp bookmark"""
        if timestamp not in self.bookmarks:
            self.bookmarks.append(timestamp)
            self.bookmarks.sort()

    def add_note(self, timestamp: int, note: str):
        """Add a note at specific timestamp"""
        self.notes.append({
            'timestamp': timestamp,
            'note': note,
            'created_at': datetime.now().isoformat()
        })


@dataclass
class LearningPath:
    """Structured learning path with multiple content items"""
    path_id: str
    title: str
    description: str
    target_role: UserRole
    difficulty: DifficultyLevel
    estimated_hours: int
    content_sequence: List[str]  # content_ids in order
    objectives: List[LearningObjective]
    certificate_available: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def get_completion_percentage(self, user_progress: Dict[str, LearningProgress]) -> float:
        """Calculate path completion percentage"""
        if not self.content_sequence:
            return 0.0

        total_progress = 0.0
        for content_id in self.content_sequence:
            progress = user_progress.get(content_id)
            if progress:
                total_progress += progress.progress_percentage

        return total_progress / len(self.content_sequence)

    def is_completed(self, user_progress: Dict[str, LearningProgress]) -> bool:
        """Check if path is completed"""
        for content_id in self.content_sequence:
            progress = user_progress.get(content_id)
            if not progress or progress.status != CompletionStatus.COMPLETED:
                return False
        return True


@dataclass
class Certificate:
    """Training completion certificate"""
    certificate_id: str
    user_id: str
    path_id: Optional[str]
    content_id: Optional[str]
    title: str
    issued_at: datetime
    expires_at: Optional[datetime] = None
    verification_code: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_valid(self) -> bool:
        """Check if certificate is still valid"""
        if not self.expires_at:
            return True
        return datetime.now() < self.expires_at


class TrainingSystem:
    """Main training and education system"""

    def __init__(self):
        self.content_library: Dict[str, LearningContent] = {}
        self.learning_paths: Dict[str, LearningPath] = {}
        self.user_progress: Dict[str, Dict[str, LearningProgress]] = defaultdict(dict)
        self.certificates: Dict[str, Certificate] = {}

        # Initialize with default content
        self._initialize_default_content()

    def _initialize_default_content(self):
        """Initialize with default training content"""

        # Getting Started Video
        getting_started = LearningContent(
            content_id="getting-started-001",
            title="Getting Started with Legal AI System",
            description="Learn the basics of navigating and using the Legal AI System effectively.",
            content_type=ContentType.VIDEO_TUTORIAL,
            difficulty=DifficultyLevel.BEGINNER,
            duration_minutes=5,
            objectives=[LearningObjective.GETTING_STARTED],
            target_roles=[UserRole.ATTORNEY, UserRole.PARALEGAL, UserRole.CLIENT],
            video_url="/videos/getting-started.mp4",
            transcript="Welcome to the Legal AI System...",
            interactive_elements=[
                {
                    "type": "highlight",
                    "timestamp": 30,
                    "element": "#dashboard",
                    "text": "This is your main dashboard"
                },
                {
                    "type": "tooltip",
                    "timestamp": 60,
                    "element": "#upload-button",
                    "text": "Click here to upload documents"
                }
            ],
            quiz_questions=[
                {
                    "question": "What is the main purpose of the Legal AI System?",
                    "type": "multiple_choice",
                    "options": [
                        "Document analysis and legal research",
                        "Social media management",
                        "Email marketing",
                        "Project management"
                    ],
                    "correct": 0
                }
            ],
            resources=[
                {"title": "Quick Reference Guide", "url": "/docs/quick-reference.pdf"},
                {"title": "System Requirements", "url": "/docs/requirements.html"}
            ],
            tags=["basics", "navigation", "introduction"]
        )

        # Document Upload Tutorial
        document_upload = LearningContent(
            content_id="document-upload-001",
            title="Uploading and Managing Documents",
            description="Learn how to upload, organize, and manage your legal documents.",
            content_type=ContentType.VIDEO_TUTORIAL,
            difficulty=DifficultyLevel.BEGINNER,
            duration_minutes=3,
            objectives=[LearningObjective.DOCUMENT_UPLOAD],
            target_roles=[UserRole.ATTORNEY, UserRole.PARALEGAL],
            video_url="/videos/document-upload.mp4",
            interactive_elements=[
                {
                    "type": "step",
                    "timestamp": 15,
                    "action": "click",
                    "element": "#upload-button",
                    "text": "Click the upload button"
                },
                {
                    "type": "step",
                    "timestamp": 45,
                    "action": "drag_drop",
                    "element": "#upload-zone",
                    "text": "Drag and drop your files here"
                }
            ],
            quiz_questions=[
                {
                    "question": "What file formats are supported for upload?",
                    "type": "multiple_select",
                    "options": ["PDF", "DOCX", "TXT", "RTF", "JPG"],
                    "correct": [0, 1, 2, 3]
                }
            ]
        )

        # Understanding Analysis Tutorial
        analysis_understanding = LearningContent(
            content_id="analysis-understanding-001",
            title="Understanding AI Document Analysis",
            description="Learn how to interpret and use AI-generated document analysis results.",
            content_type=ContentType.VIDEO_TUTORIAL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_minutes=10,
            objectives=[LearningObjective.ANALYSIS_UNDERSTANDING],
            target_roles=[UserRole.ATTORNEY, UserRole.PARALEGAL],
            prerequisites=["document-upload-001"],
            video_url="/videos/analysis-understanding.mp4",
            interactive_elements=[
                {
                    "type": "guided_tour",
                    "steps": [
                        {
                            "element": "#analysis-summary",
                            "title": "Analysis Summary",
                            "description": "This section provides an overview of key findings"
                        },
                        {
                            "element": "#risk-assessment",
                            "title": "Risk Assessment",
                            "description": "Review potential legal risks identified in the document"
                        },
                        {
                            "element": "#key-clauses",
                            "title": "Key Clauses",
                            "description": "Important contractual terms are highlighted here"
                        }
                    ]
                }
            ]
        )

        # Q&A System Usage
        qa_system = LearningContent(
            content_id="qa-system-001",
            title="Using the Q&A System",
            description="Master the art of asking questions about your legal documents.",
            content_type=ContentType.VIDEO_TUTORIAL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_minutes=8,
            objectives=[LearningObjective.QA_SYSTEM_USAGE],
            target_roles=[UserRole.ATTORNEY, UserRole.PARALEGAL],
            prerequisites=["analysis-understanding-001"],
            video_url="/videos/qa-system.mp4",
            quiz_questions=[
                {
                    "question": "What makes a good question for the AI system?",
                    "type": "multiple_choice",
                    "options": [
                        "Specific and context-aware questions",
                        "Very general questions",
                        "Questions about unrelated topics",
                        "Single word queries"
                    ],
                    "correct": 0
                }
            ]
        )

        # Attorney Accountability
        attorney_accountability = LearningContent(
            content_id="attorney-accountability-001",
            title="Attorney Accountability and AI Assistance",
            description="Understanding professional responsibility when using AI legal tools.",
            content_type=ContentType.VIDEO_TUTORIAL,
            difficulty=DifficultyLevel.ADVANCED,
            duration_minutes=12,
            objectives=[LearningObjective.ATTORNEY_ACCOUNTABILITY],
            target_roles=[UserRole.ATTORNEY],
            video_url="/videos/attorney-accountability.mp4",
            resources=[
                {"title": "ABA Model Rules on Technology", "url": "/docs/aba-model-rules.pdf"},
                {"title": "State Bar Guidelines", "url": "/docs/state-bar-guidelines.pdf"}
            ]
        )

        # Interactive Security Guide
        security_guide = LearningContent(
            content_id="security-guide-001",
            title="Security and Confidentiality Best Practices",
            description="Interactive guide to maintaining client confidentiality and data security.",
            content_type=ContentType.INTERACTIVE_GUIDE,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_minutes=15,
            objectives=[LearningObjective.SECURITY_COMPLIANCE],
            target_roles=[UserRole.ATTORNEY, UserRole.PARALEGAL, UserRole.ADMIN],
            interactive_elements=[
                {
                    "type": "checklist",
                    "title": "Security Checklist",
                    "items": [
                        "Enable two-factor authentication",
                        "Use strong passwords",
                        "Regularly review access logs",
                        "Understand data encryption",
                        "Follow client consent procedures"
                    ]
                }
            ]
        )

        # Add content to library
        content_items = [
            getting_started,
            document_upload,
            analysis_understanding,
            qa_system,
            attorney_accountability,
            security_guide
        ]

        for content in content_items:
            self.content_library[content.content_id] = content

        # Create learning paths
        attorney_basics_path = LearningPath(
            path_id="attorney-basics-path",
            title="Attorney Essentials",
            description="Complete training path for attorneys new to the Legal AI System",
            target_role=UserRole.ATTORNEY,
            difficulty=DifficultyLevel.BEGINNER,
            estimated_hours=2,
            content_sequence=[
                "getting-started-001",
                "document-upload-001",
                "analysis-understanding-001",
                "qa-system-001",
                "attorney-accountability-001"
            ],
            objectives=[
                LearningObjective.GETTING_STARTED,
                LearningObjective.DOCUMENT_UPLOAD,
                LearningObjective.ANALYSIS_UNDERSTANDING,
                LearningObjective.QA_SYSTEM_USAGE,
                LearningObjective.ATTORNEY_ACCOUNTABILITY
            ]
        )

        paralegal_basics_path = LearningPath(
            path_id="paralegal-basics-path",
            title="Paralegal Essentials",
            description="Essential training for paralegals using the Legal AI System",
            target_role=UserRole.PARALEGAL,
            difficulty=DifficultyLevel.BEGINNER,
            estimated_hours=1.5,
            content_sequence=[
                "getting-started-001",
                "document-upload-001",
                "analysis-understanding-001",
                "qa-system-001",
                "security-guide-001"
            ],
            objectives=[
                LearningObjective.GETTING_STARTED,
                LearningObjective.DOCUMENT_UPLOAD,
                LearningObjective.ANALYSIS_UNDERSTANDING,
                LearningObjective.QA_SYSTEM_USAGE,
                LearningObjective.SECURITY_COMPLIANCE
            ]
        )

        self.learning_paths["attorney-basics-path"] = attorney_basics_path
        self.learning_paths["paralegal-basics-path"] = paralegal_basics_path

    async def get_content(self, content_id: str) -> Optional[LearningContent]:
        """Get learning content by ID"""
        return self.content_library.get(content_id)

    async def get_content_for_role(self, role: UserRole, difficulty: Optional[DifficultyLevel] = None) -> List[LearningContent]:
        """Get available content for specific role"""
        content_list = []
        for content in self.content_library.values():
            if content.is_available_for_role(role):
                if difficulty is None or content.difficulty == difficulty:
                    content_list.append(content)

        return sorted(content_list, key=lambda x: x.difficulty.value)

    async def start_content(self, user_id: str, content_id: str) -> bool:
        """Start learning content for user"""
        if content_id not in self.content_library:
            return False

        progress = self.user_progress[user_id].get(content_id)
        if not progress:
            progress = LearningProgress(user_id=user_id, content_id=content_id)
            self.user_progress[user_id][content_id] = progress

        progress.start()
        logger.info(f"User {user_id} started content {content_id}")
        return True

    async def update_progress(self, user_id: str, content_id: str, progress_percentage: float) -> bool:
        """Update user progress on content"""
        if content_id not in self.content_library:
            return False

        progress = self.user_progress[user_id].get(content_id)
        if not progress:
            progress = LearningProgress(user_id=user_id, content_id=content_id)
            self.user_progress[user_id][content_id] = progress

        progress.update_progress(progress_percentage)

        # Auto-complete if 100%
        if progress_percentage >= 100.0 and progress.status != CompletionStatus.COMPLETED:
            progress.complete()

        return True

    async def complete_content(self, user_id: str, content_id: str, quiz_score: Optional[float] = None) -> bool:
        """Mark content as completed"""
        if content_id not in self.content_library:
            return False

        progress = self.user_progress[user_id].get(content_id)
        if not progress:
            progress = LearningProgress(user_id=user_id, content_id=content_id)
            self.user_progress[user_id][content_id] = progress

        progress.complete(quiz_score)
        logger.info(f"User {user_id} completed content {content_id}")

        # Check if this completes any learning paths
        await self._check_path_completion(user_id)

        return True

    async def add_bookmark(self, user_id: str, content_id: str, timestamp: int) -> bool:
        """Add bookmark to content"""
        progress = self.user_progress[user_id].get(content_id)
        if not progress:
            return False

        progress.add_bookmark(timestamp)
        return True

    async def add_note(self, user_id: str, content_id: str, timestamp: int, note: str) -> bool:
        """Add note to content"""
        progress = self.user_progress[user_id].get(content_id)
        if not progress:
            return False

        progress.add_note(timestamp, note)
        return True

    async def get_user_progress(self, user_id: str, content_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user progress for content or all content"""
        if content_id:
            progress = self.user_progress[user_id].get(content_id)
            if not progress:
                return {}
            return {
                'content_id': content_id,
                'status': progress.status.value,
                'progress_percentage': progress.progress_percentage,
                'time_spent_minutes': progress.time_spent_minutes,
                'last_accessed': progress.last_accessed.isoformat() if progress.last_accessed else None,
                'quiz_scores': progress.quiz_scores,
                'bookmarks': progress.bookmarks,
                'notes': progress.notes
            }
        else:
            return {
                content_id: {
                    'status': progress.status.value,
                    'progress_percentage': progress.progress_percentage,
                    'completed_at': progress.completed_at.isoformat() if progress.completed_at else None
                }
                for content_id, progress in self.user_progress[user_id].items()
            }

    async def get_learning_paths(self, role: Optional[UserRole] = None) -> List[LearningPath]:
        """Get available learning paths"""
        paths = list(self.learning_paths.values())
        if role:
            paths = [path for path in paths if path.target_role == role]
        return paths

    async def get_path_progress(self, user_id: str, path_id: str) -> Optional[Dict[str, Any]]:
        """Get user progress on learning path"""
        path = self.learning_paths.get(path_id)
        if not path:
            return None

        user_progress = self.user_progress[user_id]
        completion_percentage = path.get_completion_percentage(user_progress)
        is_completed = path.is_completed(user_progress)

        content_progress = []
        for content_id in path.content_sequence:
            progress = user_progress.get(content_id)
            content = self.content_library.get(content_id)

            content_progress.append({
                'content_id': content_id,
                'title': content.title if content else 'Unknown',
                'status': progress.status.value if progress else CompletionStatus.NOT_STARTED.value,
                'progress_percentage': progress.progress_percentage if progress else 0.0
            })

        return {
            'path_id': path_id,
            'title': path.title,
            'completion_percentage': completion_percentage,
            'is_completed': is_completed,
            'content_progress': content_progress,
            'estimated_hours': path.estimated_hours,
            'certificate_available': path.certificate_available
        }

    async def _check_path_completion(self, user_id: str):
        """Check if user has completed any learning paths and issue certificates"""
        user_progress = self.user_progress[user_id]

        for path_id, path in self.learning_paths.items():
            if path.is_completed(user_progress):
                # Check if certificate already issued
                existing_cert = any(
                    cert.user_id == user_id and cert.path_id == path_id
                    for cert in self.certificates.values()
                )

                if not existing_cert and path.certificate_available:
                    await self._issue_certificate(user_id, path_id=path_id)

    async def _issue_certificate(self, user_id: str, path_id: Optional[str] = None, content_id: Optional[str] = None):
        """Issue completion certificate"""
        certificate_id = str(uuid.uuid4())

        if path_id:
            path = self.learning_paths.get(path_id)
            title = f"Certificate of Completion: {path.title}" if path else "Certificate of Completion"
        elif content_id:
            content = self.content_library.get(content_id)
            title = f"Certificate of Completion: {content.title}" if content else "Certificate of Completion"
        else:
            title = "Certificate of Completion"

        certificate = Certificate(
            certificate_id=certificate_id,
            user_id=user_id,
            path_id=path_id,
            content_id=content_id,
            title=title,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365*3)  # 3 years
        )

        self.certificates[certificate_id] = certificate
        logger.info(f"Issued certificate {certificate_id} to user {user_id}")

    async def get_user_certificates(self, user_id: str) -> List[Certificate]:
        """Get all certificates for user"""
        return [cert for cert in self.certificates.values() if cert.user_id == user_id]

    async def get_certificate(self, certificate_id: str) -> Optional[Certificate]:
        """Get certificate by ID"""
        return self.certificates.get(certificate_id)

    async def search_content(self, query: str, role: Optional[UserRole] = None) -> List[LearningContent]:
        """Search learning content"""
        results = []
        query_lower = query.lower()

        for content in self.content_library.values():
            if role and not content.is_available_for_role(role):
                continue

            # Search in title, description, tags
            if (query_lower in content.title.lower() or
                query_lower in content.description.lower() or
                any(query_lower in tag.lower() for tag in content.tags)):
                results.append(content)

        return results

    async def get_recommended_content(self, user_id: str, role: UserRole, limit: int = 5) -> List[LearningContent]:
        """Get personalized content recommendations"""
        user_progress = self.user_progress[user_id]
        completed_content = {
            content_id for content_id, progress in user_progress.items()
            if progress.status == CompletionStatus.COMPLETED
        }

        # Get uncompleted content for role
        available_content = []
        for content in self.content_library.values():
            if (content.is_available_for_role(role) and
                content.content_id not in completed_content):

                # Check prerequisites
                prereqs_met = all(
                    prereq in completed_content
                    for prereq in content.prerequisites
                )

                if prereqs_met:
                    available_content.append(content)

        # Sort by difficulty and relevance
        available_content.sort(key=lambda x: (x.difficulty.value, x.duration_minutes))

        return available_content[:limit]

    async def get_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get learning analytics for user"""
        user_progress = self.user_progress[user_id]

        if not user_progress:
            return {
                'total_content': 0,
                'completed_content': 0,
                'in_progress': 0,
                'total_time_minutes': 0,
                'completion_rate': 0.0,
                'average_quiz_score': 0.0,
                'certificates_earned': 0,
                'learning_streak_days': 0
            }

        completed = sum(1 for p in user_progress.values() if p.status == CompletionStatus.COMPLETED)
        in_progress = sum(1 for p in user_progress.values() if p.status == CompletionStatus.IN_PROGRESS)
        total_time = sum(p.time_spent_minutes for p in user_progress.values())

        all_scores = []
        for progress in user_progress.values():
            all_scores.extend(progress.quiz_scores)

        avg_quiz_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        certificates = len(await self.get_user_certificates(user_id))

        return {
            'total_content': len(user_progress),
            'completed_content': completed,
            'in_progress': in_progress,
            'total_time_minutes': total_time,
            'completion_rate': completed / len(user_progress) * 100 if user_progress else 0.0,
            'average_quiz_score': avg_quiz_score,
            'certificates_earned': certificates,
            'learning_streak_days': await self._calculate_learning_streak(user_id)
        }

    async def _calculate_learning_streak(self, user_id: str) -> int:
        """Calculate consecutive days of learning activity"""
        user_progress = self.user_progress[user_id]
        if not user_progress:
            return 0

        # Get all access dates
        access_dates = []
        for progress in user_progress.values():
            if progress.last_accessed:
                access_dates.append(progress.last_accessed.date())

        if not access_dates:
            return 0

        # Sort dates and count consecutive days
        unique_dates = sorted(set(access_dates), reverse=True)
        streak = 0
        current_date = datetime.now().date()

        for date in unique_dates:
            if (current_date - date).days == streak:
                streak += 1
            else:
                break

        return streak


# Global training system instance
training_system = TrainingSystem()


# FastAPI endpoints
def get_training_endpoints():
    """Returns FastAPI endpoints for training system"""
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel
    from typing import Optional, List

    router = APIRouter(prefix="/api/training", tags=["training"])

    class StartContentRequest(BaseModel):
        user_id: str
        content_id: str

    class UpdateProgressRequest(BaseModel):
        user_id: str
        content_id: str
        progress_percentage: float
        time_spent_minutes: Optional[int] = 0

    class CompleteContentRequest(BaseModel):
        user_id: str
        content_id: str
        quiz_score: Optional[float] = None

    class AddBookmarkRequest(BaseModel):
        user_id: str
        content_id: str
        timestamp: int

    class AddNoteRequest(BaseModel):
        user_id: str
        content_id: str
        timestamp: int
        note: str

    @router.get("/content")
    async def get_content_library(
        role: Optional[str] = None,
        difficulty: Optional[str] = None,
        content_type: Optional[str] = None
    ):
        """Get available learning content"""
        try:
            role_enum = UserRole(role) if role else None
            difficulty_enum = DifficultyLevel(difficulty) if difficulty else None
            type_enum = ContentType(content_type) if content_type else None

            content_list = await training_system.get_content_for_role(role_enum, difficulty_enum)

            if type_enum:
                content_list = [c for c in content_list if c.content_type == type_enum]

            return [content.to_dict() for content in content_list]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/content/{content_id}")
    async def get_content_detail(content_id: str):
        """Get detailed content information"""
        content = await training_system.get_content(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        return content.to_dict()

    @router.post("/content/start")
    async def start_content(request: StartContentRequest):
        """Start learning content"""
        success = await training_system.start_content(request.user_id, request.content_id)
        if not success:
            raise HTTPException(status_code=404, detail="Content not found")
        return {"success": True}

    @router.post("/content/progress")
    async def update_progress(request: UpdateProgressRequest):
        """Update learning progress"""
        success = await training_system.update_progress(
            request.user_id,
            request.content_id,
            request.progress_percentage
        )
        if not success:
            raise HTTPException(status_code=404, detail="Content not found")
        return {"success": True}

    @router.post("/content/complete")
    async def complete_content(request: CompleteContentRequest):
        """Complete learning content"""
        success = await training_system.complete_content(
            request.user_id,
            request.content_id,
            request.quiz_score
        )
        if not success:
            raise HTTPException(status_code=404, detail="Content not found")
        return {"success": True}

    @router.post("/content/bookmark")
    async def add_bookmark(request: AddBookmarkRequest):
        """Add bookmark to content"""
        success = await training_system.add_bookmark(
            request.user_id,
            request.content_id,
            request.timestamp
        )
        if not success:
            raise HTTPException(status_code=404, detail="Progress not found")
        return {"success": True}

    @router.post("/content/note")
    async def add_note(request: AddNoteRequest):
        """Add note to content"""
        success = await training_system.add_note(
            request.user_id,
            request.content_id,
            request.timestamp,
            request.note
        )
        if not success:
            raise HTTPException(status_code=404, detail="Progress not found")
        return {"success": True}

    @router.get("/user/{user_id}/progress")
    async def get_user_progress(user_id: str, content_id: Optional[str] = None):
        """Get user learning progress"""
        progress = await training_system.get_user_progress(user_id, content_id)
        return progress

    @router.get("/paths")
    async def get_learning_paths(role: Optional[str] = None):
        """Get available learning paths"""
        try:
            role_enum = UserRole(role) if role else None
            paths = await training_system.get_learning_paths(role_enum)
            return [
                {
                    'path_id': path.path_id,
                    'title': path.title,
                    'description': path.description,
                    'target_role': path.target_role.value,
                    'difficulty': path.difficulty.value,
                    'estimated_hours': path.estimated_hours,
                    'content_count': len(path.content_sequence),
                    'certificate_available': path.certificate_available
                }
                for path in paths
            ]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/user/{user_id}/path/{path_id}/progress")
    async def get_path_progress(user_id: str, path_id: str):
        """Get user progress on learning path"""
        progress = await training_system.get_path_progress(user_id, path_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Path not found")
        return progress

    @router.get("/user/{user_id}/certificates")
    async def get_user_certificates(user_id: str):
        """Get user certificates"""
        certificates = await training_system.get_user_certificates(user_id)
        return [
            {
                'certificate_id': cert.certificate_id,
                'title': cert.title,
                'issued_at': cert.issued_at.isoformat(),
                'expires_at': cert.expires_at.isoformat() if cert.expires_at else None,
                'is_valid': cert.is_valid(),
                'verification_code': cert.verification_code
            }
            for cert in certificates
        ]

    @router.get("/certificate/{certificate_id}")
    async def get_certificate(certificate_id: str):
        """Get certificate details"""
        certificate = await training_system.get_certificate(certificate_id)
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")

        return {
            'certificate_id': certificate.certificate_id,
            'title': certificate.title,
            'user_id': certificate.user_id,
            'issued_at': certificate.issued_at.isoformat(),
            'expires_at': certificate.expires_at.isoformat() if certificate.expires_at else None,
            'is_valid': certificate.is_valid(),
            'verification_code': certificate.verification_code
        }

    @router.get("/search")
    async def search_content(q: str = Query(..., description="Search query"), role: Optional[str] = None):
        """Search learning content"""
        try:
            role_enum = UserRole(role) if role else None
            results = await training_system.search_content(q, role_enum)
            return [content.to_dict() for content in results]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/user/{user_id}/recommendations")
    async def get_recommendations(user_id: str, role: str, limit: int = 5):
        """Get personalized content recommendations"""
        try:
            role_enum = UserRole(role)
            recommendations = await training_system.get_recommended_content(user_id, role_enum, limit)
            return [content.to_dict() for content in recommendations]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/user/{user_id}/analytics")
    async def get_learning_analytics(user_id: str):
        """Get learning analytics for user"""
        analytics = await training_system.get_learning_analytics(user_id)
        return analytics

    return router


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        system = TrainingSystem()

        # Start content
        await system.start_content("user123", "getting-started-001")

        # Update progress
        await system.update_progress("user123", "getting-started-001", 50.0)

        # Complete content
        await system.complete_content("user123", "getting-started-001", 85.0)

        # Get progress
        progress = await system.get_user_progress("user123")
        print(f"User progress: {progress}")

        # Get analytics
        analytics = await system.get_learning_analytics("user123")
        print(f"Learning analytics: {analytics}")

        print("Training system demo completed!")

    asyncio.run(demo())