"""
Mobile API Module

This module provides mobile-specific APIs including voice command processing,
mobile authentication, and mobile-optimized endpoints for the legal AI system.
"""

from .voice_processor import VoiceProcessor
from .mobile_auth import MobileAuthManager
from .api_endpoints import mobile_router
from .models import VoiceCommand, MobileSession
from .location_services import (
    CourthouseGPSDetector,
    CourthouseDatabase,
    QuickBriefGenerator,
    LocationCoordinates,
    CourthouseInfo,
    LocationContext
)
from .location_services.location_endpoints import location_router
from .location_services.integration_service import LocationServicesIntegration

__all__ = [
    "VoiceProcessor",
    "MobileAuthManager", 
    "mobile_router",
    "location_router",
    "VoiceCommand",
    "MobileSession",
    "CourthouseGPSDetector",
    "CourthouseDatabase",
    "QuickBriefGenerator",
    "LocationCoordinates",
    "CourthouseInfo",
    "LocationContext",
    "LocationServicesIntegration"
]