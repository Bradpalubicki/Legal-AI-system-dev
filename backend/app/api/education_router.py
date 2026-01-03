"""
Education API Router for Legal AI System

Provides endpoints for educational content, interactive guides, and video library
for legal education and client empowerment.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

# Import education modules
from src.education import (
    EducationContent,
    InteractiveGuides,
    VideoLibrary,
    LegalTopicCategory,
    GuideCategory,
    VideoCategory,
    VideoLevel
)

# Import authentication dependencies
from app.api.deps.auth import get_current_user, get_current_user_id, get_optional_user, CurrentUser

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize education services
education_content = EducationContent()
interactive_guides = InteractiveGuides()
video_library = VideoLibrary()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class TopicSummaryResponse(BaseModel):
    id: str
    title: str
    category: str
    description: str
    difficulty_level: int
    section_count: int
    estimated_read_time: int
    keywords: List[str]
    last_updated: datetime

class ContentSectionResponse(BaseModel):
    title: str
    content: str
    level: int
    estimated_read_time: int
    prerequisites: List[str]
    related_topics: List[str]

class TopicDetailResponse(BaseModel):
    id: str
    title: str
    category: str
    description: str
    difficulty_level: int
    sections: List[ContentSectionResponse]
    keywords: List[str]
    last_updated: datetime

class GuideStepResponse(BaseModel):
    id: str
    title: str
    description: str
    step_type: str
    estimated_time: Optional[int]
    required_documents: List[str]
    tips: List[str]
    warnings: List[str]
    next_steps: List[str]
    deadline_info: Optional[Dict[str, Any]]

class InteractiveGuideResponse(BaseModel):
    id: str
    title: str
    category: str
    description: str
    difficulty_level: int
    estimated_completion_time: int
    prerequisites: List[str]
    steps: List[GuideStepResponse]
    resources: List[Dict[str, str]]
    tags: List[str]
    last_updated: datetime

class ChecklistItemResponse(BaseModel):
    id: str
    task: str
    description: str
    required: bool
    deadline_days: Optional[int]
    dependencies: List[str]
    documents_needed: List[str]
    completed: bool

class DocumentChecklistResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    items: List[ChecklistItemResponse]
    applicable_jurisdictions: List[str]
    last_updated: datetime

class VideoChapterResponse(BaseModel):
    id: str
    title: str
    start_time: int
    duration: int
    description: str
    key_points: List[str]

class VideoResourceResponse(BaseModel):
    id: str
    title: str
    description: str
    resource_type: str
    url: str
    downloadable: bool

class QuizResponse(BaseModel):
    id: str
    question: str
    question_type: str
    options: List[str]
    points: int

class VideoResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    level: str
    duration: int
    video_url: str
    thumbnail_url: str
    transcript_url: Optional[str]
    chapters: List[VideoChapterResponse]
    resources: List[VideoResourceResponse]
    quiz: List[QuizResponse]
    tags: List[str]
    prerequisites: List[str]
    learning_objectives: List[str]
    instructor: str
    view_count: int
    rating: float
    created_date: datetime

class VideoSeriesResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    videos: List[str]
    total_duration: int
    difficulty_progression: bool
    completion_certificate: bool
    prerequisites: List[str]
    learning_path: str

class ProgressUpdateRequest(BaseModel):
    watched_duration: int = Field(..., ge=0)
    current_position: int = Field(..., ge=0)
    completed: bool = False

class ProgressResponse(BaseModel):
    user_id: str
    video_id: str
    watched_duration: int
    completed: bool
    last_position: int
    quiz_score: Optional[float]
    bookmarks: List[int]
    last_watched: datetime

class GlossaryTermResponse(BaseModel):
    id: str
    term: str
    definition: str
    pronunciation: Optional[str]
    etymology: Optional[str]
    related_terms: List[str]
    examples: List[str]
    categories: List[str]

class DeadlineCalculationRequest(BaseModel):
    rule_id: str
    start_date: datetime

class DeadlineCalculationResponse(BaseModel):
    rule_id: str
    start_date: datetime
    calculated_deadline: Optional[datetime]
    rule_description: str
    calculation_method: str


# =============================================================================
# EDUCATION CONTENT ENDPOINTS
# =============================================================================

@router.get(
    "/topics",
    response_model=List[TopicSummaryResponse],
    summary="Get All Educational Topics",
    description="Retrieve a list of all available legal education topics with summary information"
)
async def get_all_topics(
    category: Optional[LegalTopicCategory] = Query(None, description="Filter by topic category"),
    difficulty_level: Optional[int] = Query(None, ge=1, le=3, description="Filter by difficulty level (1-3)"),
    search: Optional[str] = Query(None, description="Search topics by keyword")
):
    """Get all educational topics with optional filtering"""
    try:
        if search:
            topics = education_content.search_topics(search)
        elif category:
            topics = education_content.get_topics_by_category(category)
        else:
            topics = education_content.get_all_topics()
        
        # Apply difficulty filter if specified
        if difficulty_level:
            topics = [t for t in topics if t.difficulty_level == difficulty_level]
        
        # Convert to response format
        response_data = []
        for topic in topics:
            total_read_time = sum(section.estimated_read_time for section in topic.sections)
            response_data.append(TopicSummaryResponse(
                id=topic.id,
                title=topic.title,
                category=topic.category.value,
                description=topic.description,
                difficulty_level=topic.difficulty_level,
                section_count=len(topic.sections),
                estimated_read_time=total_read_time,
                keywords=topic.keywords,
                last_updated=topic.last_updated
            ))
        
        logger.info(f"Retrieved {len(response_data)} topics")
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving educational topics"
        )


@router.get(
    "/content/{topic_id}",
    response_model=TopicDetailResponse,
    summary="Get Educational Content",
    description="Retrieve detailed content for a specific educational topic"
)
async def get_topic_content(
    topic_id: str = Path(..., description="Unique identifier for the educational topic")
):
    """Get detailed content for a specific topic"""
    try:
        topic = education_content.get_topic(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found"
            )
        
        # Convert sections to response format
        sections_response = []
        for section in topic.sections:
            sections_response.append(ContentSectionResponse(
                title=section.title,
                content=section.content,
                level=section.level,
                estimated_read_time=section.estimated_read_time,
                prerequisites=section.prerequisites,
                related_topics=section.related_topics
            ))
        
        response = TopicDetailResponse(
            id=topic.id,
            title=topic.title,
            category=topic.category.value,
            description=topic.description,
            difficulty_level=topic.difficulty_level,
            sections=sections_response,
            keywords=topic.keywords,
            last_updated=topic.last_updated
        )
        
        logger.info(f"Retrieved content for topic: {topic_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving topic content {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving topic content"
        )


# =============================================================================
# INTERACTIVE GUIDES ENDPOINTS
# =============================================================================

@router.get(
    "/guides",
    response_model=List[InteractiveGuideResponse],
    summary="Get Interactive Guides",
    description="Retrieve list of interactive step-by-step guides"
)
async def get_interactive_guides(
    category: Optional[GuideCategory] = Query(None, description="Filter by guide category"),
    difficulty_level: Optional[int] = Query(None, ge=1, le=3, description="Filter by difficulty level"),
    search: Optional[str] = Query(None, description="Search guides by keyword")
):
    """Get interactive guides with optional filtering"""
    try:
        if search:
            guides = interactive_guides.search_guides(search)
        elif category:
            guides = interactive_guides.get_guides_by_category(category)
        else:
            guides = interactive_guides.get_all_guides()
        
        # Apply difficulty filter
        if difficulty_level:
            guides = [g for g in guides if g.difficulty_level == difficulty_level]
        
        # Convert to response format
        response_data = []
        for guide in guides:
            steps_response = []
            for step in guide.steps:
                steps_response.append(GuideStepResponse(
                    id=step.id,
                    title=step.title,
                    description=step.description,
                    step_type=step.step_type.value,
                    estimated_time=step.estimated_time,
                    required_documents=step.required_documents,
                    tips=step.tips,
                    warnings=step.warnings,
                    next_steps=step.next_steps,
                    deadline_info=step.deadline_info
                ))
            
            response_data.append(InteractiveGuideResponse(
                id=guide.id,
                title=guide.title,
                category=guide.category.value,
                description=guide.description,
                difficulty_level=guide.difficulty_level,
                estimated_completion_time=guide.estimated_completion_time,
                prerequisites=guide.prerequisites,
                steps=steps_response,
                resources=guide.resources,
                tags=guide.tags,
                last_updated=guide.last_updated
            ))
        
        logger.info(f"Retrieved {len(response_data)} interactive guides")
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving interactive guides: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving interactive guides"
        )


@router.get(
    "/checklists",
    response_model=List[DocumentChecklistResponse],
    summary="Get Document Checklists",
    description="Retrieve document preparation checklists"
)
async def get_document_checklists(
    category: Optional[str] = Query(None, description="Filter by checklist category"),
    jurisdiction: Optional[str] = Query(None, description="Filter by applicable jurisdiction")
):
    """Get document preparation checklists"""
    try:
        if category:
            checklists = interactive_guides.get_checklists_by_category(category)
        else:
            checklists = interactive_guides.get_all_checklists()
        
        # Apply jurisdiction filter
        if jurisdiction:
            checklists = [c for c in checklists 
                         if jurisdiction in c.applicable_jurisdictions or 
                            "all_states" in c.applicable_jurisdictions]
        
        # Convert to response format
        response_data = []
        for checklist in checklists:
            items_response = []
            for item in checklist.items:
                items_response.append(ChecklistItemResponse(
                    id=item.id,
                    task=item.task,
                    description=item.description,
                    required=item.required,
                    deadline_days=item.deadline_days,
                    dependencies=item.dependencies,
                    documents_needed=item.documents_needed,
                    completed=item.completed
                ))
            
            response_data.append(DocumentChecklistResponse(
                id=checklist.id,
                title=checklist.title,
                description=checklist.description,
                category=checklist.category,
                items=items_response,
                applicable_jurisdictions=checklist.applicable_jurisdictions,
                last_updated=checklist.last_updated
            ))
        
        logger.info(f"Retrieved {len(response_data)} document checklists")
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving document checklists: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving document checklists"
        )


@router.post(
    "/deadlines/calculate",
    response_model=DeadlineCalculationResponse,
    summary="Calculate Legal Deadline",
    description="Calculate legal deadline based on specific rules and start date"
)
async def calculate_deadline(
    request: DeadlineCalculationRequest
):
    """Calculate legal deadline using specified rule"""
    try:
        rule = interactive_guides.get_deadline_rule(request.rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deadline rule '{request.rule_id}' not found"
            )
        
        calculated_deadline = interactive_guides.calculate_deadline(
            request.rule_id, 
            request.start_date
        )
        
        response = DeadlineCalculationResponse(
            rule_id=request.rule_id,
            start_date=request.start_date,
            calculated_deadline=calculated_deadline,
            rule_description=rule.description,
            calculation_method=rule.calculation_method
        )
        
        logger.info(f"Calculated deadline for rule {request.rule_id}: {calculated_deadline}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating deadline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating deadline"
        )


@router.get(
    "/etiquette",
    summary="Get Court Etiquette Rules",
    description="Retrieve court etiquette and behavior guidelines"
)
async def get_court_etiquette(
    court_type: Optional[str] = Query(None, description="Filter by court type (trial, appellate, administrative)")
):
    """Get court etiquette rules"""
    try:
        rules = interactive_guides.get_etiquette_rules(court_type)
        
        logger.info(f"Retrieved {len(rules)} etiquette rules")
        return rules
        
    except Exception as e:
        logger.error(f"Error retrieving etiquette rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving etiquette rules"
        )


# =============================================================================
# GLOSSARY ENDPOINTS
# =============================================================================

@router.get(
    "/glossary/{term_id}",
    response_model=GlossaryTermResponse,
    summary="Get Glossary Term",
    description="Retrieve definition and details for a specific legal term"
)
async def get_glossary_term(
    term_id: str = Path(..., description="Unique identifier for the legal term")
):
    """Get specific glossary term definition"""
    try:
        term = interactive_guides.get_glossary_term(term_id)
        if not term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Term '{term_id}' not found in glossary"
            )
        
        response = GlossaryTermResponse(
            id=term.id,
            term=term.term,
            definition=term.definition,
            pronunciation=term.pronunciation,
            etymology=term.etymology,
            related_terms=term.related_terms,
            examples=term.examples,
            categories=term.categories
        )
        
        logger.info(f"Retrieved glossary term: {term_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving glossary term {term_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving glossary term"
        )


@router.get(
    "/glossary",
    response_model=List[GlossaryTermResponse],
    summary="Search Glossary",
    description="Search legal terminology glossary"
)
async def search_glossary(
    search: str = Query(..., description="Search term or phrase"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """Search glossary terms"""
    try:
        terms = interactive_guides.search_glossary(search)
        
        # Limit results
        terms = terms[:limit]
        
        # Convert to response format
        response_data = []
        for term in terms:
            response_data.append(GlossaryTermResponse(
                id=term.id,
                term=term.term,
                definition=term.definition,
                pronunciation=term.pronunciation,
                etymology=term.etymology,
                related_terms=term.related_terms,
                examples=term.examples,
                categories=term.categories
            ))
        
        logger.info(f"Found {len(response_data)} matching glossary terms for: {search}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error searching glossary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching glossary"
        )


# =============================================================================
# VIDEO LIBRARY ENDPOINTS
# =============================================================================

@router.get(
    "/videos/{category}",
    response_model=List[VideoResponse],
    summary="Get Videos by Category",
    description="Retrieve educational videos filtered by category"
)
async def get_videos_by_category(
    category: VideoCategory = Path(..., description="Video category filter"),
    level: Optional[VideoLevel] = Query(None, description="Filter by difficulty level"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of videos")
):
    """Get videos filtered by category and optionally by level"""
    try:
        if level:
            videos = video_library.get_videos_by_level(level)
            videos = [v for v in videos if v.category == category]
        else:
            videos = video_library.get_videos_by_category(category)
        
        # Limit results
        videos = videos[:limit]
        
        # Convert to response format
        response_data = []
        for video in videos:
            chapters_response = [
                VideoChapterResponse(
                    id=ch.id,
                    title=ch.title,
                    start_time=ch.start_time,
                    duration=ch.duration,
                    description=ch.description,
                    key_points=ch.key_points
                ) for ch in video.chapters
            ]
            
            resources_response = [
                VideoResourceResponse(
                    id=res.id,
                    title=res.title,
                    description=res.description,
                    resource_type=res.resource_type,
                    url=res.url,
                    downloadable=res.downloadable
                ) for res in video.resources
            ]
            
            quiz_response = [
                QuizResponse(
                    id=q.id,
                    question=q.question,
                    question_type=q.question_type,
                    options=q.options,
                    points=q.points
                ) for q in video.quiz
            ]
            
            response_data.append(VideoResponse(
                id=video.id,
                title=video.title,
                description=video.description,
                category=video.category.value,
                level=video.level.value,
                duration=video.duration,
                video_url=video.video_url,
                thumbnail_url=video.thumbnail_url,
                transcript_url=video.transcript_url,
                chapters=chapters_response,
                resources=resources_response,
                quiz=quiz_response,
                tags=video.tags,
                prerequisites=video.prerequisites,
                learning_objectives=video.learning_objectives,
                instructor=video.instructor,
                view_count=video.view_count,
                rating=video.rating,
                created_date=video.created_date
            ))
        
        logger.info(f"Retrieved {len(response_data)} videos for category: {category}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving videos by category {category}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving videos"
        )


@router.get(
    "/videos",
    response_model=List[VideoResponse],
    summary="Search Videos",
    description="Search educational videos by keyword or get recommended videos"
)
async def search_videos(
    search: Optional[str] = Query(None, description="Search term for videos"),
    recommended: bool = Query(False, description="Get recommended videos for user"),
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of videos")
):
    """Search videos or get recommendations"""
    try:
        if search:
            videos = video_library.search_videos(search)
        elif recommended:
            # Use actual user_id from auth, or demo_user for unauthenticated requests
            user_id = current_user.user_id if current_user else "demo_user"
            videos = video_library.get_recommended_videos(user_id, limit)
        else:
            videos = video_library.get_all_videos()
        
        # Limit results
        videos = videos[:limit]
        
        # Convert to response format (same as above)
        response_data = []
        for video in videos:
            response_data.append(VideoResponse(
                id=video.id,
                title=video.title,
                description=video.description,
                category=video.category.value,
                level=video.level.value,
                duration=video.duration,
                video_url=video.video_url,
                thumbnail_url=video.thumbnail_url,
                transcript_url=video.transcript_url,
                chapters=[],  # Simplified for search results
                resources=[],
                quiz=[],
                tags=video.tags,
                prerequisites=video.prerequisites,
                learning_objectives=video.learning_objectives,
                instructor=video.instructor,
                view_count=video.view_count,
                rating=video.rating,
                created_date=video.created_date
            ))
        
        logger.info(f"Retrieved {len(response_data)} videos")
        return response_data
        
    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching videos"
        )


@router.post(
    "/videos/{video_id}/progress",
    response_model=ProgressResponse,
    summary="Track Video Progress",
    description="Update user's progress for a specific video"
)
async def track_video_progress(
    video_id: str = Path(..., description="Video identifier"),
    progress: ProgressUpdateRequest = ...,
    current_user: CurrentUser = Depends(get_current_user)  # Requires authentication
):
    """Track user's video viewing progress"""
    try:
        # Use actual user_id from authentication
        user_id = current_user.user_id
        
        # Verify video exists
        video = video_library.get_video(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video '{video_id}' not found"
            )
        
        # Update progress
        user_progress = video_library.update_progress(
            user_id=user_id,
            video_id=video_id,
            watched_duration=progress.watched_duration,
            current_position=progress.current_position,
            completed=progress.completed
        )
        
        response = ProgressResponse(
            user_id=user_progress.user_id,
            video_id=user_progress.video_id,
            watched_duration=user_progress.watched_duration,
            completed=user_progress.completed,
            last_position=user_progress.last_position,
            quiz_score=user_progress.quiz_score,
            bookmarks=user_progress.bookmarks,
            last_watched=user_progress.last_watched
        )
        
        logger.info(f"Updated progress for user {user_id}, video {video_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking video progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error tracking video progress"
        )


@router.get(
    "/series",
    response_model=List[VideoSeriesResponse],
    summary="Get Video Series",
    description="Retrieve available video series for structured learning"
)
async def get_video_series():
    """Get all available video series"""
    try:
        series_list = video_library.get_all_series()
        
        # Convert to response format
        response_data = []
        for series in series_list:
            response_data.append(VideoSeriesResponse(
                id=series.id,
                title=series.title,
                description=series.description,
                category=series.category.value,
                videos=series.videos,
                total_duration=series.total_duration,
                difficulty_progression=series.difficulty_progression,
                completion_certificate=series.completion_certificate,
                prerequisites=series.prerequisites,
                learning_path=series.learning_path
            ))
        
        logger.info(f"Retrieved {len(response_data)} video series")
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving video series: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving video series"
        )


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get(
    "/health",
    summary="Education System Health Check",
    description="Check the health and availability of education services"
)
async def education_health_check():
    """Health check for education services"""
    try:
        # Test each service
        topics_count = len(education_content.get_all_topics())
        guides_count = len(interactive_guides.get_all_guides())
        videos_count = len(video_library.get_all_videos())
        
        return {
            "status": "healthy",
            "services": {
                "education_content": {
                    "status": "online",
                    "topics_available": topics_count
                },
                "interactive_guides": {
                    "status": "online", 
                    "guides_available": guides_count
                },
                "video_library": {
                    "status": "online",
                    "videos_available": videos_count
                }
            },
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Education health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }
        )