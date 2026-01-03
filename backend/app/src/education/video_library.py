from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class VideoCategory(str, Enum):
    CASE_TYPES = "case_types"
    COURT_PROCESS = "court_process"
    ATTORNEY_RELATIONS = "attorney_relations"
    DOCUMENT_TYPES = "document_types"
    LEGAL_CONCEPTS = "legal_concepts"
    PRACTICAL_SKILLS = "practical_skills"


class VideoLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class VideoChapter:
    id: str
    title: str
    start_time: int  # seconds
    duration: int  # seconds
    description: str
    key_points: List[str]


@dataclass
class VideoResource:
    id: str
    title: str
    description: str
    resource_type: str  # "transcript", "slides", "worksheet", "checklist"
    url: str
    downloadable: bool = True


@dataclass
class Quiz:
    id: str
    question: str
    question_type: str  # "multiple_choice", "true_false", "short_answer"
    options: List[str]  # For multiple choice
    correct_answer: str
    explanation: str
    points: int = 1


@dataclass
class EducationalVideo:
    id: str
    title: str
    description: str
    category: VideoCategory
    level: VideoLevel
    duration: int  # seconds
    video_url: str
    thumbnail_url: str
    transcript_url: Optional[str] = None
    chapters: List[VideoChapter] = None
    resources: List[VideoResource] = None
    quiz: List[Quiz] = None
    tags: List[str] = None
    prerequisites: List[str] = None
    learning_objectives: List[str] = None
    created_date: datetime = None
    last_updated: datetime = None
    view_count: int = 0
    rating: float = 0.0
    instructor: str = ""
    closed_captions_available: bool = True

    def __post_init__(self):
        if self.chapters is None:
            self.chapters = []
        if self.resources is None:
            self.resources = []
        if self.quiz is None:
            self.quiz = []
        if self.tags is None:
            self.tags = []
        if self.prerequisites is None:
            self.prerequisites = []
        if self.learning_objectives is None:
            self.learning_objectives = []
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class VideoSeries:
    id: str
    title: str
    description: str
    category: VideoCategory
    videos: List[str]  # Video IDs in order
    total_duration: int  # seconds
    difficulty_progression: bool  # True if videos get progressively harder
    completion_certificate: bool
    prerequisites: List[str] = None
    learning_path: str = ""

    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []


@dataclass
class UserProgress:
    user_id: str
    video_id: str
    watched_duration: int  # seconds
    completed: bool
    last_position: int  # seconds
    quiz_score: Optional[float] = None
    bookmarks: List[int] = None  # timestamp bookmarks
    notes: str = ""
    last_watched: datetime = None

    def __post_init__(self):
        if self.bookmarks is None:
            self.bookmarks = []
        if self.last_watched is None:
            self.last_watched = datetime.now()


class VideoLibrary:
    def __init__(self):
        self._videos = self._initialize_videos()
        self._series = self._initialize_series()
        self._user_progress = {}  # user_id -> {video_id -> UserProgress}
    
    def _initialize_videos(self) -> Dict[str, EducationalVideo]:
        videos = {}
        
        # Understanding Your Case Type Series
        videos["understanding_civil_cases"] = EducationalVideo(
            id="understanding_civil_cases",
            title="Understanding Civil Cases: When to Sue and When Not To",
            description="Learn the basics of civil litigation, when you have a valid claim, and alternatives to filing a lawsuit.",
            category=VideoCategory.CASE_TYPES,
            level=VideoLevel.BEGINNER,
            duration=1200,  # 20 minutes
            video_url="/videos/understanding-civil-cases.mp4",
            thumbnail_url="/thumbnails/civil-cases.jpg",
            transcript_url="/transcripts/understanding-civil-cases.txt",
            instructor="Sarah Johnson, Esq.",
            chapters=[
                VideoChapter(
                    id="what_is_civil_case",
                    title="What is a Civil Case?",
                    start_time=0,
                    duration=300,
                    description="Introduction to civil litigation and how it differs from criminal cases",
                    key_points=[
                        "Civil vs. criminal law distinction",
                        "Burden of proof differences",
                        "Types of remedies available"
                    ]
                ),
                VideoChapter(
                    id="elements_valid_claim",
                    title="Elements of a Valid Claim",
                    start_time=300,
                    duration=450,
                    description="Understanding what makes a legally viable civil claim",
                    key_points=[
                        "Duty, breach, causation, and damages",
                        "Statute of limitations considerations",
                        "Standing to sue requirements"
                    ]
                ),
                VideoChapter(
                    id="alternatives_litigation",
                    title="Alternatives to Litigation",
                    start_time=750,
                    duration=300,
                    description="Explore mediation, arbitration, and settlement options",
                    key_points=[
                        "Mediation benefits and process",
                        "Arbitration vs. court trial",
                        "Settlement negotiation strategies"
                    ]
                ),
                VideoChapter(
                    id="cost_benefit_analysis",
                    title="Cost-Benefit Analysis",
                    start_time=1050,
                    duration=150,
                    description="How to evaluate whether litigation is worth pursuing",
                    key_points=[
                        "Attorney fees and costs",
                        "Time investment required",
                        "Likelihood of recovery"
                    ]
                )
            ],
            resources=[
                VideoResource(
                    id="civil_case_checklist",
                    title="Civil Case Evaluation Checklist",
                    description="Worksheet to help evaluate the strength of your potential case",
                    resource_type="worksheet",
                    url="/resources/civil-case-checklist.pdf"
                ),
                VideoResource(
                    id="litigation_alternatives_guide",
                    title="Guide to Litigation Alternatives",
                    description="Comprehensive guide to mediation, arbitration, and settlement",
                    resource_type="guide",
                    url="/resources/litigation-alternatives.pdf"
                )
            ],
            quiz=[
                Quiz(
                    id="civil_vs_criminal",
                    question="What is the primary difference between civil and criminal cases?",
                    question_type="multiple_choice",
                    options=[
                        "Civil cases involve money damages, criminal cases involve jail time",
                        "Civil cases are tried by judges, criminal cases by juries",
                        "Civil cases have lower burden of proof than criminal cases",
                        "There is no significant difference"
                    ],
                    correct_answer="Civil cases involve money damages, criminal cases involve jail time",
                    explanation="While both may have other remedies, the key distinction is that civil cases primarily seek monetary or equitable relief, while criminal cases can result in imprisonment."
                ),
                Quiz(
                    id="burden_of_proof_civil",
                    question="What is the burden of proof in most civil cases?",
                    question_type="multiple_choice",
                    options=[
                        "Beyond a reasonable doubt",
                        "Clear and convincing evidence", 
                        "Preponderance of the evidence",
                        "Probable cause"
                    ],
                    correct_answer="Preponderance of the evidence",
                    explanation="Most civil cases require proof by a preponderance of the evidence, meaning more likely than not (51%)."
                )
            ],
            tags=["civil litigation", "case evaluation", "beginner", "overview"],
            learning_objectives=[
                "Distinguish between civil and criminal cases",
                "Identify elements of a valid civil claim",
                "Evaluate alternatives to litigation",
                "Understand cost-benefit considerations"
            ]
        )
        
        videos["criminal_case_basics"] = EducationalVideo(
            id="criminal_case_basics",
            title="Criminal Cases: Rights and Procedures",
            description="Essential information about criminal procedure and defendant rights",
            category=VideoCategory.CASE_TYPES,
            level=VideoLevel.BEGINNER,
            duration=1500,  # 25 minutes
            video_url="/videos/criminal-case-basics.mp4",
            thumbnail_url="/thumbnails/criminal-cases.jpg",
            instructor="Michael Rodriguez, Esq.",
            chapters=[
                VideoChapter(
                    id="constitutional_rights",
                    title="Constitutional Rights in Criminal Cases",
                    start_time=0,
                    duration=600,
                    description="Overview of key constitutional protections for criminal defendants",
                    key_points=[
                        "Fourth Amendment search and seizure protections",
                        "Fifth Amendment right against self-incrimination",
                        "Sixth Amendment right to counsel and fair trial",
                        "Miranda rights and when they apply"
                    ]
                ),
                VideoChapter(
                    id="criminal_process_overview",
                    title="The Criminal Justice Process",
                    start_time=600,
                    duration=600,
                    description="Step-by-step walkthrough of criminal proceedings",
                    key_points=[
                        "Investigation and arrest",
                        "Booking and initial appearance",
                        "Preliminary hearing or grand jury",
                        "Arraignment and plea bargaining",
                        "Trial and sentencing"
                    ]
                ),
                VideoChapter(
                    id="working_with_attorney",
                    title="Working with a Criminal Defense Attorney",
                    start_time=1200,
                    duration=300,
                    description="How to effectively work with your defense lawyer",
                    key_points=[
                        "Attorney-client privilege",
                        "Providing complete and honest information",
                        "Understanding plea bargain decisions",
                        "Trial preparation expectations"
                    ]
                )
            ],
            tags=["criminal law", "defendant rights", "procedure"],
            learning_objectives=[
                "Understand key constitutional protections",
                "Navigate the criminal justice process",
                "Work effectively with defense counsel"
            ]
        )
        
        videos["family_court_process"] = EducationalVideo(
            id="family_court_process",
            title="Navigating Family Court: Divorce and Custody Cases",
            description="Guide to family court procedures, divorce process, and custody determinations",
            category=VideoCategory.COURT_PROCESS,
            level=VideoLevel.INTERMEDIATE,
            duration=1800,  # 30 minutes
            video_url="/videos/family-court-process.mp4",
            thumbnail_url="/thumbnails/family-court.jpg",
            instructor="Lisa Chen, Esq.",
            chapters=[
                VideoChapter(
                    id="divorce_overview",
                    title="Divorce Process Overview",
                    start_time=0,
                    duration=450,
                    description="Understanding no-fault vs. fault divorce and procedural steps",
                    key_points=[
                        "Residency requirements",
                        "Grounds for divorce",
                        "Property division principles",
                        "Spousal support considerations"
                    ]
                ),
                VideoChapter(
                    id="child_custody_basics",
                    title="Child Custody Fundamentals",
                    start_time=450,
                    duration=600,
                    description="Types of custody and best interest standards",
                    key_points=[
                        "Legal vs. physical custody",
                        "Best interest of the child standard",
                        "Parenting plan development",
                        "Modification procedures"
                    ]
                ),
                VideoChapter(
                    id="family_court_procedures",
                    title="Family Court Procedures",
                    start_time=1050,
                    duration=450,
                    description="What to expect in family court hearings",
                    key_points=[
                        "Temporary orders hearings",
                        "Mediation requirements",
                        "Discovery in family cases",
                        "Trial procedures"
                    ]
                ),
                VideoChapter(
                    id="financial_disclosures",
                    title="Financial Disclosure Requirements",
                    start_time=1500,
                    duration=300,
                    description="Required financial documentation and disclosure rules",
                    key_points=[
                        "Asset and debt inventory",
                        "Income documentation",
                        "Valuation of property",
                        "Hidden asset discovery"
                    ]
                )
            ],
            tags=["family law", "divorce", "custody", "court process"],
            prerequisites=["understanding_civil_cases"],
            learning_objectives=[
                "Understand divorce procedure variations",
                "Navigate child custody determinations",
                "Prepare required financial disclosures"
            ]
        )
        
        videos["working_with_attorney"] = EducationalVideo(
            id="working_with_attorney",
            title="How to Work Effectively with Your Attorney",
            description="Best practices for attorney-client relationships and communication",
            category=VideoCategory.ATTORNEY_RELATIONS,
            level=VideoLevel.BEGINNER,
            duration=900,  # 15 minutes
            video_url="/videos/working-with-attorney.mp4",
            thumbnail_url="/thumbnails/attorney-relations.jpg",
            instructor="David Park, Esq.",
            chapters=[
                VideoChapter(
                    id="choosing_attorney",
                    title="Choosing the Right Attorney",
                    start_time=0,
                    duration=300,
                    description="Factors to consider when selecting legal representation",
                    key_points=[
                        "Practice area specialization",
                        "Experience level requirements",
                        "Fee structures and costs",
                        "Communication style preferences"
                    ]
                ),
                VideoChapter(
                    id="attorney_client_privilege",
                    title="Understanding Attorney-Client Privilege",
                    start_time=300,
                    duration=200,
                    description="What communications are protected and why honesty matters",
                    key_points=[
                        "Scope of privilege protection",
                        "Exceptions to privilege",
                        "Importance of complete honesty",
                        "Third party presence effects"
                    ]
                ),
                VideoChapter(
                    id="effective_communication",
                    title="Communicating Effectively",
                    start_time=500,
                    duration=250,
                    description="How to communicate efficiently with your attorney",
                    key_points=[
                        "Organizing documents and information",
                        "Asking the right questions",
                        "Understanding billing and time management",
                        "When to call vs. email"
                    ]
                ),
                VideoChapter(
                    id="managing_expectations",
                    title="Managing Expectations and Outcomes",
                    start_time=750,
                    duration=150,
                    description="Realistic expectations about legal processes and outcomes",
                    key_points=[
                        "Timeline realities",
                        "Cost considerations",
                        "Success probability discussions",
                        "Settlement vs. trial decisions"
                    ]
                )
            ],
            tags=["attorney relations", "communication", "legal representation"],
            learning_objectives=[
                "Select appropriate legal counsel",
                "Communicate effectively with attorneys",
                "Maintain realistic expectations"
            ]
        )
        
        videos["legal_documents_explained"] = EducationalVideo(
            id="legal_documents_explained",
            title="Common Legal Documents Explained",
            description="Understanding different types of legal documents and their purposes",
            category=VideoCategory.DOCUMENT_TYPES,
            level=VideoLevel.BEGINNER,
            duration=1350,  # 22.5 minutes
            video_url="/videos/legal-documents-explained.mp4",
            thumbnail_url="/thumbnails/legal-documents.jpg",
            instructor="Amanda Foster, Esq.",
            chapters=[
                VideoChapter(
                    id="pleadings_overview",
                    title="Pleadings: Complaints and Answers",
                    start_time=0,
                    duration=400,
                    description="Understanding the documents that start and respond to lawsuits",
                    key_points=[
                        "Components of a complaint",
                        "Types of answers and responses",
                        "Counterclaims and cross-claims",
                        "Amendment procedures"
                    ]
                ),
                VideoChapter(
                    id="discovery_documents",
                    title="Discovery Documents",
                    start_time=400,
                    duration=450,
                    description="Documents used to gather information during litigation",
                    key_points=[
                        "Interrogatories structure and limits",
                        "Document production requests",
                        "Admission requests strategy",
                        "Subpoenas and third-party discovery"
                    ]
                ),
                VideoChapter(
                    id="motions_briefs",
                    title="Motions and Legal Briefs",
                    start_time=850,
                    duration=350,
                    description="How attorneys make legal arguments to the court",
                    key_points=[
                        "Common types of motions",
                        "Brief structure and components",
                        "Evidence and exhibit requirements",
                        "Oral argument procedures"
                    ]
                ),
                VideoChapter(
                    id="settlement_documents",
                    title="Settlement and Resolution Documents",
                    start_time=1200,
                    duration=150,
                    description="Documents that resolve cases without trial",
                    key_points=[
                        "Settlement agreement essentials",
                        "Release language importance",
                        "Enforcement provisions",
                        "Confidentiality considerations"
                    ]
                )
            ],
            resources=[
                VideoResource(
                    id="document_templates",
                    title="Legal Document Templates",
                    description="Sample templates for common legal documents",
                    resource_type="templates",
                    url="/resources/document-templates.zip"
                )
            ],
            tags=["legal documents", "pleadings", "discovery", "motions"],
            learning_objectives=[
                "Identify different types of legal documents",
                "Understand document purposes and requirements",
                "Recognize key document components"
            ]
        )
        
        return videos
    
    def _initialize_series(self) -> Dict[str, VideoSeries]:
        series = {}
        
        series["case_types_fundamentals"] = VideoSeries(
            id="case_types_fundamentals",
            title="Understanding Your Case Type",
            description="Comprehensive series covering different types of legal cases and their unique characteristics",
            category=VideoCategory.CASE_TYPES,
            videos=[
                "understanding_civil_cases",
                "criminal_case_basics",
                "family_court_process"
            ],
            total_duration=4500,  # 75 minutes total
            difficulty_progression=True,
            completion_certificate=True,
            learning_path="Provides foundation for understanding different areas of law and court procedures"
        )
        
        series["court_process_explained"] = VideoSeries(
            id="court_process_explained",
            title="Court Process Explained",
            description="Step-by-step guide through various court procedures and what to expect",
            category=VideoCategory.COURT_PROCESS,
            videos=[
                "family_court_process"
                # Additional court process videos would be added here
            ],
            total_duration=1800,
            difficulty_progression=False,
            completion_certificate=True,
            prerequisites=["case_types_fundamentals"]
        )
        
        series["working_with_attorneys"] = VideoSeries(
            id="working_with_attorneys",
            title="Working with Your Attorney",
            description="Best practices for attorney-client relationships and effective legal representation",
            category=VideoCategory.ATTORNEY_RELATIONS,
            videos=[
                "working_with_attorney"
                # Additional attorney relations videos would be added here
            ],
            total_duration=900,
            difficulty_progression=False,
            completion_certificate=False
        )
        
        return series
    
    # Video retrieval methods
    def get_all_videos(self) -> List[EducationalVideo]:
        return list(self._videos.values())
    
    def get_video(self, video_id: str) -> Optional[EducationalVideo]:
        return self._videos.get(video_id)
    
    def get_videos_by_category(self, category: VideoCategory) -> List[EducationalVideo]:
        return [video for video in self._videos.values() if video.category == category]
    
    def get_videos_by_level(self, level: VideoLevel) -> List[EducationalVideo]:
        return [video for video in self._videos.values() if video.level == level]
    
    def search_videos(self, query: str) -> List[EducationalVideo]:
        query_lower = query.lower()
        matching_videos = []
        
        for video in self._videos.values():
            if (query_lower in video.title.lower() or 
                query_lower in video.description.lower() or
                any(query_lower in tag.lower() for tag in video.tags) or
                query_lower in video.instructor.lower()):
                matching_videos.append(video)
        
        return matching_videos
    
    def get_recommended_videos(self, user_id: str, limit: int = 5) -> List[EducationalVideo]:
        # Simple recommendation based on user's viewing history and level
        user_progress = self._user_progress.get(user_id, {})
        
        # Get videos user hasn't completed
        incomplete_videos = []
        for video in self._videos.values():
            progress = user_progress.get(video.id)
            if not progress or not progress.completed:
                incomplete_videos.append(video)
        
        # Sort by beginner level first, then by rating
        recommended = sorted(
            incomplete_videos,
            key=lambda v: (v.level != VideoLevel.BEGINNER, -v.rating)
        )
        
        return recommended[:limit]
    
    # Series methods
    def get_all_series(self) -> List[VideoSeries]:
        return list(self._series.values())
    
    def get_series(self, series_id: str) -> Optional[VideoSeries]:
        return self._series.get(series_id)
    
    def get_series_videos(self, series_id: str) -> List[EducationalVideo]:
        series = self.get_series(series_id)
        if not series:
            return []
        
        videos = []
        for video_id in series.videos:
            video = self.get_video(video_id)
            if video:
                videos.append(video)
        
        return videos
    
    # Progress tracking methods
    def update_progress(self, user_id: str, video_id: str, watched_duration: int, 
                       current_position: int, completed: bool = False) -> UserProgress:
        if user_id not in self._user_progress:
            self._user_progress[user_id] = {}
        
        if video_id not in self._user_progress[user_id]:
            self._user_progress[user_id][video_id] = UserProgress(
                user_id=user_id,
                video_id=video_id,
                watched_duration=0,
                completed=False,
                last_position=0
            )
        
        progress = self._user_progress[user_id][video_id]
        progress.watched_duration = max(progress.watched_duration, watched_duration)
        progress.last_position = current_position
        progress.completed = completed
        progress.last_watched = datetime.now()
        
        return progress
    
    def get_user_progress(self, user_id: str, video_id: str = None) -> Union[Optional[UserProgress], Dict[str, UserProgress]]:
        if user_id not in self._user_progress:
            return None if video_id else {}
        
        if video_id:
            return self._user_progress[user_id].get(video_id)
        
        return self._user_progress[user_id]
    
    def add_bookmark(self, user_id: str, video_id: str, timestamp: int) -> bool:
        progress = self.get_user_progress(user_id, video_id)
        if progress:
            if timestamp not in progress.bookmarks:
                progress.bookmarks.append(timestamp)
                progress.bookmarks.sort()
            return True
        return False
    
    def remove_bookmark(self, user_id: str, video_id: str, timestamp: int) -> bool:
        progress = self.get_user_progress(user_id, video_id)
        if progress and timestamp in progress.bookmarks:
            progress.bookmarks.remove(timestamp)
            return True
        return False
    
    def update_quiz_score(self, user_id: str, video_id: str, score: float):
        progress = self.get_user_progress(user_id, video_id)
        if progress:
            progress.quiz_score = score
    
    def get_completion_percentage(self, user_id: str, series_id: str = None) -> float:
        if series_id:
            series = self.get_series(series_id)
            if not series:
                return 0.0
            
            completed_videos = 0
            for video_id in series.videos:
                progress = self.get_user_progress(user_id, video_id)
                if progress and progress.completed:
                    completed_videos += 1
            
            return (completed_videos / len(series.videos)) * 100.0 if series.videos else 0.0
        
        else:
            # Overall completion across all videos
            user_progress = self.get_user_progress(user_id)
            if not user_progress:
                return 0.0
            
            completed = sum(1 for p in user_progress.values() if p.completed)
            total = len(self._videos)
            
            return (completed / total) * 100.0 if total > 0 else 0.0