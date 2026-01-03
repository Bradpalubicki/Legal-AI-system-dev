"""
Mobile API Endpoints

FastAPI router with mobile-specific endpoints including voice command processing,
mobile authentication, session management, and mobile-optimized data retrieval.
"""

import logging
from datetime import timedelta
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import (
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceSettings,
    MobileSession,
    ErrorResponse,
    DocumentSummaryRequest,
    LegalResearchRequest,
    CalendarRequest,
    ClientUpdateRequest
)
from .voice_processor import VoiceProcessor
from .mobile_auth import MobileAuthManager

logger = logging.getLogger(__name__)

# Create router
mobile_router = APIRouter(prefix="/api/v1/mobile", tags=["mobile"])
security = HTTPBearer()


class MobileAPIHandler:
    """
    Mobile API handler that manages dependencies and coordinates between
    voice processing and authentication services.
    """
    
    def __init__(self):
        self.voice_processor: Optional[VoiceProcessor] = None
        self.auth_manager: Optional[MobileAuthManager] = None
    
    def set_voice_processor(self, processor: VoiceProcessor):
        self.voice_processor = processor
    
    def set_auth_manager(self, manager: MobileAuthManager):
        self.auth_manager = manager


# Global handler instance
mobile_handler = MobileAPIHandler()


async def get_current_mobile_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependency to get current mobile user from JWT token
    """
    if not mobile_handler.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    token = credentials.credentials
    is_valid, payload = await mobile_handler.auth_manager.verify_mobile_token(token)
    
    if not is_valid or not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload


@mobile_router.post("/auth/register-device", response_model=Dict)
async def register_mobile_device(
    device_id: str = Form(...),
    device_type: str = Form(...),
    app_version: str = Form(...),
    user_credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Register a mobile device for a user
    """
    if not mobile_handler.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    # Verify user token (should be web token)
    # In production, this would verify against the main auth system
    user_id = UUID("12345678-1234-5678-9abc-123456789012")  # Placeholder
    
    try:
        session = await mobile_handler.auth_manager.register_mobile_device(
            user_id=user_id,
            device_id=device_id,
            device_type=device_type,
            app_version=app_version
        )
        
        # Create mobile tokens
        access_token = await mobile_handler.auth_manager.create_mobile_access_token(
            user_id, session.id, device_id
        )
        refresh_token = await mobile_handler.auth_manager.create_refresh_token(
            user_id, session.id, device_id
        )
        
        return {
            "session_id": str(session.id),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400  # 24 hours
        }
        
    except Exception as e:
        logger.error(f"Device registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device registration failed: {str(e)}"
        )


@mobile_router.post("/auth/refresh", response_model=Dict)
async def refresh_mobile_token(
    refresh_token: str = Form(...)
):
    """
    Refresh mobile access token
    """
    if not mobile_handler.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    try:
        new_access_token, new_refresh_token = await mobile_handler.auth_manager.refresh_mobile_token(
            refresh_token
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 86400
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@mobile_router.post("/auth/logout", response_model=Dict)
async def logout_mobile_session(
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Logout mobile session
    """
    if not mobile_handler.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    session_id = UUID(current_user["session_id"])
    device_id = current_user["device_id"]
    
    success = await mobile_handler.auth_manager.logout_mobile_session(
        session_id, device_id
    )
    
    return {
        "message": "Logged out successfully" if success else "Logout failed",
        "success": success
    }


@mobile_router.post("/voice/process", response_model=VoiceCommandResponse)
async def process_voice_command(
    request: VoiceCommandRequest,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Process voice command (text or audio input)
    """
    if not mobile_handler.voice_processor:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice processing service not available"
        )
    
    user_id = UUID(current_user["sub"])
    session_id = UUID(current_user["session_id"])
    
    try:
        response = await mobile_handler.voice_processor.process_voice_command(
            request, user_id, session_id
        )
        return response
        
    except Exception as e:
        logger.error(f"Voice command processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice processing failed: {str(e)}"
        )


@mobile_router.post("/voice/upload-audio", response_model=VoiceCommandResponse)
async def upload_audio_command(
    audio_file: UploadFile = File(...),
    language: str = Form(default="en-US"),
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Upload audio file for voice command processing
    """
    if not mobile_handler.voice_processor:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice processing service not available"
        )
    
    # Validate audio file
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file format"
        )
    
    try:
        # Read and encode audio data
        import base64
        audio_data = await audio_file.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Determine audio format
        audio_format = audio_file.content_type.split("/")[-1]
        if audio_format == "mpeg":
            audio_format = "mp3"
        
        # Create request
        request = VoiceCommandRequest(
            audio_data=audio_base64,
            language=language,
            audio_format=audio_format
        )
        
        user_id = UUID(current_user["sub"])
        session_id = UUID(current_user["session_id"])
        
        response = await mobile_handler.voice_processor.process_voice_command(
            request, user_id, session_id
        )
        return response
        
    except Exception as e:
        logger.error(f"Audio upload processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio processing failed: {str(e)}"
        )


@mobile_router.get("/voice/settings", response_model=VoiceSettings)
async def get_voice_settings(
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get current voice settings for mobile session
    """
    if not mobile_handler.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    session_id = current_user["session_id"]
    session = mobile_handler.auth_manager.active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return VoiceSettings(**session.voice_settings)


@mobile_router.put("/voice/settings", response_model=Dict)
async def update_voice_settings(
    settings: VoiceSettings,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Update voice settings for mobile session
    """
    if not mobile_handler.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    session_id = UUID(current_user["session_id"])
    
    success = await mobile_handler.auth_manager.update_voice_settings(
        session_id, settings.dict()
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update voice settings"
        )
    
    return {
        "message": "Voice settings updated successfully",
        "success": True
    }


@mobile_router.post("/documents/summarize", response_model=Dict)
async def summarize_document_mobile(
    request: DocumentSummaryRequest,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Summarize document for mobile viewing
    """
    # Placeholder for document summarization
    # In production, this would integrate with the document processor
    
    return {
        "document_id": str(request.document_id),
        "summary_type": request.summary_type,
        "summary": "Document summary would be generated here...",
        "key_points": [
            "Key point 1",
            "Key point 2",
            "Key point 3"
        ],
        "focus_areas": request.focus_areas,
        "word_count": 150,
        "confidence_score": 0.85
    }


@mobile_router.post("/research/legal", response_model=Dict)
async def legal_research_mobile(
    request: LegalResearchRequest,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Perform legal research optimized for mobile display
    """
    # Placeholder for legal research
    # In production, this would integrate with legal research APIs
    
    return {
        "query": request.query,
        "jurisdiction": request.jurisdiction,
        "results_count": 0,
        "results": [],
        "research_summary": "No results found for the given query.",
        "suggested_queries": [
            f"Similar cases to {request.query}",
            f"Statutes related to {request.query}",
            f"Recent decisions on {request.query}"
        ]
    }


@mobile_router.get("/calendar", response_model=Dict)
async def get_mobile_calendar(
    days: int = 7,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get calendar events for mobile display
    """
    # Placeholder for calendar integration
    # In production, this would integrate with calendar services
    
    return {
        "days_requested": days,
        "events": [],
        "upcoming_deadlines": [],
        "conflicts": [],
        "summary": f"No events found for the next {days} days"
    }


@mobile_router.post("/calendar/event", response_model=Dict)
async def create_calendar_event_mobile(
    request: CalendarRequest,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Create calendar event from mobile
    """
    # Placeholder for calendar event creation
    # In production, this would integrate with calendar services
    
    return {
        "action": request.action,
        "event_created": False,
        "message": "Calendar integration not yet implemented",
        "event_details": request.event_details
    }


@mobile_router.get("/deadlines", response_model=Dict)
async def get_mobile_deadlines(
    days_ahead: int = 30,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get upcoming deadlines for mobile display
    """
    # Placeholder for deadline checking
    # In production, this would integrate with case management system
    
    return {
        "days_ahead": days_ahead,
        "deadlines": [],
        "overdue": [],
        "critical": [],
        "summary": f"No deadlines found for the next {days_ahead} days"
    }


@mobile_router.post("/clients/update", response_model=Dict)
async def update_client_mobile(
    request: ClientUpdateRequest,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Update client information from mobile
    """
    # Placeholder for client updates
    # In production, this would integrate with client management system
    
    return {
        "client_id": str(request.client_id),
        "update_type": request.update_type,
        "success": True,
        "message": "Client update processed successfully",
        "updated_fields": list(request.update_data.keys())
    }


@mobile_router.get("/session/info", response_model=Dict)
async def get_session_info(
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get current mobile session information
    """
    if not mobile_handler.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    session_id = current_user["session_id"]
    session = mobile_handler.auth_manager.active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "session_id": str(session.id),
        "user_id": str(session.user_id),
        "device_id": session.device_id,
        "device_type": session.device_type,
        "app_version": session.app_version,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "voice_settings": session.voice_settings
    }


@mobile_router.get("/health", response_model=Dict)
async def mobile_api_health():
    """
    Health check endpoint for mobile API
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "voice_processor": mobile_handler.voice_processor is not None,
            "auth_manager": mobile_handler.auth_manager is not None
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


# GPS Location Integration
@mobile_router.post("/location/voice-command", response_model=VoiceCommandResponse)
async def process_location_aware_voice_command(
    request: VoiceCommandRequest,
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    accuracy_meters: Optional[float] = Form(None),
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Process voice command with location context for courthouse-aware responses
    """
    if not mobile_handler.voice_processor:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice processing service not available"
        )
    
    user_id = UUID(current_user["sub"])
    session_id = UUID(current_user["session_id"])
    
    try:
        # Add location context to voice command if coordinates provided
        location_context = None
        if latitude is not None and longitude is not None:
            from .location_services.location_models import LocationCoordinates, LocationAccuracy
            
            user_location = LocationCoordinates(
                latitude=latitude,
                longitude=longitude,
                accuracy_meters=accuracy_meters,
                accuracy=LocationAccuracy.HIGH if accuracy_meters and accuracy_meters <= 10 
                         else LocationAccuracy.MEDIUM if accuracy_meters and accuracy_meters <= 50
                         else LocationAccuracy.LOW
            )
            
            # Enhanced voice processing with location awareness
            # This would integrate with the GPS detector to provide courthouse context
            request.location_context = {
                "coordinates": user_location.dict(),
                "has_location": True
            }
        
        response = await mobile_handler.voice_processor.process_voice_command(
            request, user_id, session_id
        )
        
        # Enhance response with location-specific suggestions if courthouse detected
        if location_context:
            response.suggested_actions.extend([
                "Generate courthouse brief",
                "Check local filing rules",
                "View courthouse hours",
                "Set geofence alerts"
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Location-aware voice command processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice processing with location failed: {str(e)}"
        )


@mobile_router.post("/quick-courthouse-brief", response_model=Dict)
async def generate_courthouse_brief_voice(
    voice_input: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    brief_type: str = Form(default="motion"),
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Generate quick brief using voice input and current courthouse location
    """
    try:
        # This would integrate with both voice processing and brief generation
        # For now, return a structured response indicating the feature
        
        return {
            "status": "processed",
            "voice_input": voice_input,
            "detected_location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "brief_type": brief_type,
            "message": "Voice-to-brief generation would process here",
            "next_steps": [
                "Transcribe voice input",
                "Detect courthouse",
                "Extract legal requirements",
                "Generate formatted brief",
                "Apply local court rules"
            ],
            "estimated_completion_time": "2-3 minutes"
        }
        
    except Exception as e:
        logger.error(f"Voice-to-brief generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Brief generation failed: {str(e)}"
        )


# Dependency injection functions for initialization
def init_mobile_api(voice_processor: VoiceProcessor, auth_manager: MobileAuthManager):
    """
    Initialize mobile API with required services
    """
    mobile_handler.set_voice_processor(voice_processor)
    mobile_handler.set_auth_manager(auth_manager)
    logger.info("Mobile API initialized successfully")