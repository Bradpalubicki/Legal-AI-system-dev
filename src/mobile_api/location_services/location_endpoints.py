"""
Location-Aware API Endpoints

GPS-enabled endpoints for courthouse detection, location-based legal services,
and quick brief generation for mobile legal professionals.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .location_models import (
    LocationCoordinates,
    CourthouseDetection,
    LocationContext,
    BriefGenerationRequest,
    QuickBrief,
    LocationAlert,
    GeofenceConfig,
    CourthouseInfo,
    LocationAccuracy
)
from .gps_detector import CourthouseGPSDetector
from .courthouse_database import CourthouseDatabase
from .brief_generator import QuickBriefGenerator

logger = logging.getLogger(__name__)

# Create router
location_router = APIRouter(prefix="/api/v1/mobile/location", tags=["location"])
security = HTTPBearer()


class LocationServicesHandler:
    """
    Handler for location-based services that manages GPS detection,
    courthouse database, and brief generation services.
    """
    
    def __init__(self):
        self.gps_detector: Optional[CourthouseGPSDetector] = None
        self.courthouse_db: Optional[CourthouseDatabase] = None
        self.brief_generator: Optional[QuickBriefGenerator] = None
    
    def set_services(
        self,
        gps_detector: CourthouseGPSDetector,
        courthouse_db: CourthouseDatabase,
        brief_generator: QuickBriefGenerator
    ):
        self.gps_detector = gps_detector
        self.courthouse_db = courthouse_db
        self.brief_generator = brief_generator


# Global handler instance
location_handler = LocationServicesHandler()


async def get_current_mobile_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependency to get current mobile user from JWT token
    (Reused from main mobile API)
    """
    # In production, this would verify the JWT token
    # For now, returning mock user data
    return {
        "sub": "12345678-1234-5678-9abc-123456789012",
        "session_id": "session-123",
        "device_id": "device-456"
    }


@location_router.post("/detect-courthouse", response_model=CourthouseDetection)
async def detect_courthouse(
    latitude: float = Form(...),
    longitude: float = Form(...),
    accuracy_meters: Optional[float] = Form(None),
    altitude: Optional[float] = Form(None),
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Detect nearby courthouse based on GPS coordinates
    """
    if not location_handler.gps_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPS detection service not available"
        )
    
    try:
        # Create location coordinates
        user_location = LocationCoordinates(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            accuracy=LocationAccuracy.HIGH if accuracy_meters and accuracy_meters <= 10 
                     else LocationAccuracy.MEDIUM if accuracy_meters and accuracy_meters <= 50
                     else LocationAccuracy.LOW,
            accuracy_meters=accuracy_meters
        )
        
        user_id = UUID(current_user["sub"])
        
        # Perform courthouse detection
        detection = await location_handler.gps_detector.detect_courthouse(
            user_location, user_id
        )
        
        logger.info(f"Courthouse detection for user {user_id}: {detection.status}")
        return detection
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid coordinates: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Courthouse detection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection failed: {str(e)}"
        )


@location_router.post("/context", response_model=LocationContext)
async def get_location_context(
    latitude: float = Form(...),
    longitude: float = Form(...),
    accuracy_meters: Optional[float] = Form(None),
    include_cases: bool = Form(default=True),
    include_hearings: bool = Form(default=True),
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get comprehensive location context including courthouse info,
    relevant rules, and case information
    """
    if not location_handler.gps_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPS detection service not available"
        )
    
    try:
        user_location = LocationCoordinates(
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            accuracy=LocationAccuracy.HIGH if accuracy_meters and accuracy_meters <= 10 
                     else LocationAccuracy.MEDIUM if accuracy_meters and accuracy_meters <= 50
                     else LocationAccuracy.LOW
        )
        
        user_id = UUID(current_user["sub"])
        
        # Get active cases and hearings (mock data for now)
        active_cases = []
        upcoming_hearings = []
        
        if include_cases:
            # In production, fetch from case management system
            active_cases = [
                {
                    "case_id": "case-123",
                    "title": "Smith v. Johnson",
                    "type": "civil",
                    "status": "active"
                }
            ]
        
        if include_hearings:
            # In production, fetch from calendar system
            upcoming_hearings = [
                {
                    "hearing_id": "hearing-456",
                    "case_id": "case-123",
                    "date": "2024-02-15T14:00:00Z",
                    "type": "motion_hearing",
                    "location": "Courtroom 4A"
                }
            ]
        
        # Create location context
        context = await location_handler.gps_detector.create_location_context(
            user_id=user_id,
            user_location=user_location,
            active_cases=active_cases,
            upcoming_hearings=upcoming_hearings
        )
        
        return context
        
    except Exception as e:
        logger.error(f"Location context creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context creation failed: {str(e)}"
        )


@location_router.get("/nearby-courthouses", response_model=List[Dict])
async def get_nearby_courthouses(
    latitude: float,
    longitude: float,
    radius_km: float = 10.0,
    max_results: int = 10,
    court_type: Optional[str] = None,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get list of courthouses within specified radius
    """
    if not location_handler.courthouse_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Courthouse database service not available"
        )
    
    try:
        # Find nearby courthouses
        nearby_courthouses = location_handler.courthouse_db.find_nearby_courthouses(
            latitude=latitude,
            longitude=longitude,
            radius_km=min(radius_km, 50.0),  # Limit search radius
            max_results=min(max_results, 25)  # Limit results
        )
        
        # Filter by court type if specified
        if court_type:
            filtered_courthouses = []
            for courthouse, distance in nearby_courthouses:
                if court_type.lower() in courthouse.court_type.value.lower():
                    filtered_courthouses.append((courthouse, distance))
            nearby_courthouses = filtered_courthouses
        
        # Format response
        results = []
        for courthouse, distance_km in nearby_courthouses:
            courthouse_dict = courthouse.dict()
            courthouse_dict["distance_km"] = round(distance_km, 2)
            courthouse_dict["distance_meters"] = round(distance_km * 1000, 0)
            courthouse_dict["is_open"] = location_handler.courthouse_db.is_courthouse_open(courthouse)
            results.append(courthouse_dict)
        
        return results
        
    except Exception as e:
        logger.error(f"Nearby courthouses search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@location_router.post("/generate-brief", response_model=QuickBrief)
async def generate_quick_brief(
    brief_request: BriefGenerationRequest,
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Generate a quick legal brief with courthouse-specific formatting
    """
    if not location_handler.brief_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Brief generation service not available"
        )
    
    try:
        location_context = None
        
        # Create location context if coordinates provided
        if latitude is not None and longitude is not None:
            user_location = LocationCoordinates(
                latitude=latitude,
                longitude=longitude,
                accuracy=LocationAccuracy.MEDIUM
            )
            
            user_id = UUID(current_user["sub"])
            
            location_context = await location_handler.gps_detector.create_location_context(
                user_id=user_id,
                user_location=user_location
            )
            
            # Use detected courthouse if not specified in request
            if not brief_request.courthouse and location_context.current_courthouse:
                brief_request.courthouse = location_context.current_courthouse
        
        # Generate the brief
        brief = await location_handler.brief_generator.generate_quick_brief(
            brief_request, location_context
        )
        
        logger.info(f"Generated {brief_request.brief_type} brief for user {current_user['sub']}")
        return brief
        
    except Exception as e:
        logger.error(f"Brief generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Brief generation failed: {str(e)}"
        )


@location_router.post("/setup-geofence", response_model=Dict)
async def setup_geofence(
    courthouse_id: str = Form(...),
    detection_radius_meters: float = Form(default=100.0),
    notification_radius_meters: float = Form(default=500.0),
    enable_arrival_alerts: bool = Form(default=True),
    enable_proximity_alerts: bool = Form(default=True),
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Set up geofence monitoring for a courthouse
    """
    if not location_handler.gps_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPS detection service not available"
        )
    
    try:
        user_id = UUID(current_user["sub"])
        courthouse_uuid = UUID(courthouse_id)
        
        # Validate courthouse exists
        courthouse = location_handler.courthouse_db.get_courthouse(courthouse_id)
        if not courthouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Courthouse not found"
            )
        
        # Create geofence configuration
        geofence_config = GeofenceConfig(
            courthouse_id=courthouse_uuid,
            detection_radius_meters=min(detection_radius_meters, 1000.0),
            notification_radius_meters=min(notification_radius_meters, 5000.0),
            enable_arrival_alerts=enable_arrival_alerts,
            enable_proximity_alerts=enable_proximity_alerts
        )
        
        # Set up geofence
        geofence_id = await location_handler.gps_detector.setup_geofence(
            user_id, courthouse_uuid, geofence_config
        )
        
        return {
            "geofence_id": geofence_id,
            "courthouse_name": courthouse.name,
            "detection_radius_meters": geofence_config.detection_radius_meters,
            "notification_radius_meters": geofence_config.notification_radius_meters,
            "status": "active",
            "message": "Geofence monitoring activated"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid geofence parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Geofence setup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geofence setup failed: {str(e)}"
        )


@location_router.delete("/geofence/{geofence_id}", response_model=Dict)
async def remove_geofence(
    geofence_id: str,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Remove geofence monitoring
    """
    if not location_handler.gps_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPS detection service not available"
        )
    
    try:
        success = await location_handler.gps_detector.remove_geofence(geofence_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Geofence not found"
            )
        
        return {
            "geofence_id": geofence_id,
            "status": "removed",
            "message": "Geofence monitoring deactivated"
        }
        
    except Exception as e:
        logger.error(f"Geofence removal failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geofence removal failed: {str(e)}"
        )


@location_router.get("/alerts", response_model=List[LocationAlert])
async def get_location_alerts(
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get active location-based alerts for user
    """
    if not location_handler.gps_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPS detection service not available"
        )
    
    try:
        user_id = UUID(current_user["sub"])
        alerts = await location_handler.gps_detector.get_location_alerts(user_id)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Location alerts retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert retrieval failed: {str(e)}"
        )


@location_router.post("/alerts/{alert_id}/dismiss", response_model=Dict)
async def dismiss_location_alert(
    alert_id: str,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Dismiss a location alert
    """
    if not location_handler.gps_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPS detection service not available"
        )
    
    try:
        user_id = UUID(current_user["sub"])
        alert_uuid = UUID(alert_id)
        
        success = await location_handler.gps_detector.dismiss_alert(user_id, alert_uuid)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {
            "alert_id": alert_id,
            "status": "dismissed",
            "message": "Alert dismissed successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid alert ID: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Alert dismissal failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert dismissal failed: {str(e)}"
        )


@location_router.get("/courthouse/{courthouse_id}", response_model=CourthouseInfo)
async def get_courthouse_details(
    courthouse_id: str,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get detailed information about a specific courthouse
    """
    if not location_handler.courthouse_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Courthouse database service not available"
        )
    
    try:
        courthouse = location_handler.courthouse_db.get_courthouse(courthouse_id)
        
        if not courthouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Courthouse not found"
            )
        
        return courthouse
        
    except Exception as e:
        logger.error(f"Courthouse details retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Courthouse details retrieval failed: {str(e)}"
        )


@location_router.get("/courthouse/{courthouse_id}/hours", response_model=Dict)
async def get_courthouse_hours(
    courthouse_id: str,
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get courthouse business hours and current status
    """
    if not location_handler.courthouse_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Courthouse database service not available"
        )
    
    try:
        courthouse = location_handler.courthouse_db.get_courthouse(courthouse_id)
        
        if not courthouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Courthouse not found"
            )
        
        is_open = location_handler.courthouse_db.is_courthouse_open(courthouse)
        next_business_day = location_handler.courthouse_db.get_next_business_day(courthouse)
        
        return {
            "courthouse_id": courthouse_id,
            "courthouse_name": courthouse.name,
            "business_hours": courthouse.business_hours,
            "is_currently_open": is_open,
            "next_business_day": next_business_day,
            "current_time": datetime.now().isoformat(),
            "timezone": "Local"  # Would be determined by courthouse location
        }
        
    except Exception as e:
        logger.error(f"Courthouse hours retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hours retrieval failed: {str(e)}"
        )


@location_router.get("/stats", response_model=Dict)
async def get_location_services_stats(
    current_user: Dict = Depends(get_current_mobile_user)
):
    """
    Get location services statistics and health information
    """
    try:
        stats = {
            "services_available": {
                "gps_detector": location_handler.gps_detector is not None,
                "courthouse_db": location_handler.courthouse_db is not None,
                "brief_generator": location_handler.brief_generator is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add GPS detector stats
        if location_handler.gps_detector:
            detector_stats = location_handler.gps_detector.get_detector_stats()
            stats["gps_detection"] = detector_stats
        
        # Add courthouse database stats
        if location_handler.courthouse_db:
            db_stats = location_handler.courthouse_db.get_statistics()
            stats["courthouse_database"] = db_stats
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats retrieval failed: {str(e)}"
        )


# Dependency injection function for initialization
def init_location_services(
    gps_detector: CourthouseGPSDetector,
    courthouse_db: CourthouseDatabase,
    brief_generator: QuickBriefGenerator
):
    """
    Initialize location services with required dependencies
    """
    location_handler.set_services(gps_detector, courthouse_db, brief_generator)
    logger.info("Location services initialized successfully")