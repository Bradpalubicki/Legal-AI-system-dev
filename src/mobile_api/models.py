"""
Mobile API Data Models

Pydantic models for mobile API requests, responses, and voice command processing.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class VoiceCommandType(str, Enum):
    """Types of voice commands supported by the system"""
    SEARCH_DOCUMENTS = "search_documents"
    CREATE_CASE = "create_case"
    DICTATE_NOTES = "dictate_notes"
    SCHEDULE_MEETING = "schedule_meeting"
    GET_CALENDAR = "get_calendar"
    SUMMARIZE_DOCUMENT = "summarize_document"
    LEGAL_RESEARCH = "legal_research"
    CHECK_DEADLINES = "check_deadlines"
    CLIENT_UPDATE = "client_update"
    GENERAL_QUERY = "general_query"


class VoiceCommandStatus(str, Enum):
    """Status of voice command processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VoiceCommand(BaseModel):
    """Voice command data model"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    session_id: UUID
    command_type: VoiceCommandType
    original_text: str = Field(..., min_length=1)
    processed_text: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    status: VoiceCommandStatus = VoiceCommandStatus.PENDING
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v < 0.3:
            raise ValueError('Confidence score too low for processing')
        return v


class VoiceCommandRequest(BaseModel):
    """Request model for voice command processing"""
    audio_data: Optional[str] = None  # Base64 encoded audio
    text_input: Optional[str] = None  # Direct text input
    session_id: Optional[UUID] = None
    language: str = Field(default="en-US")
    audio_format: str = Field(default="wav")
    
    @validator('audio_data', 'text_input')
    def validate_input(cls, v, values):
        if not values.get('audio_data') and not values.get('text_input'):
            raise ValueError('Either audio_data or text_input must be provided')
        return v


class VoiceCommandResponse(BaseModel):
    """Response model for voice command processing"""
    command_id: UUID
    status: VoiceCommandStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    suggested_actions: List[str] = Field(default_factory=list)
    processing_time_ms: int


class MobileSession(BaseModel):
    """Mobile session data model"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    device_id: str
    device_type: str  # iOS, Android, etc.
    app_version: str
    is_active: bool = True
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    voice_settings: Dict[str, Any] = Field(default_factory=dict)


class DocumentSummaryRequest(BaseModel):
    """Request for document summarization via voice"""
    document_id: UUID
    summary_type: str = Field(default="brief")  # brief, detailed, key_points
    focus_areas: List[str] = Field(default_factory=list)


class LegalResearchRequest(BaseModel):
    """Request for legal research via voice"""
    query: str = Field(..., min_length=3)
    jurisdiction: Optional[str] = None
    document_types: List[str] = Field(default_factory=list)
    date_range: Optional[Dict[str, str]] = None


class CalendarRequest(BaseModel):
    """Request for calendar operations via voice"""
    action: str  # get_events, create_event, update_event
    date_range: Optional[Dict[str, str]] = None
    event_details: Optional[Dict[str, Any]] = None


class ClientUpdateRequest(BaseModel):
    """Request for client updates via voice"""
    client_id: UUID
    update_type: str  # status, notes, contact_info
    update_data: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response model"""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VoiceSettings(BaseModel):
    """User voice preferences and settings"""
    language: str = "en-US"
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    wake_word_enabled: bool = True
    auto_transcription: bool = True
    noise_cancellation: bool = True
    preferred_commands: List[str] = Field(default_factory=list)