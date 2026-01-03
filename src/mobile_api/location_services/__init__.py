"""
Location Services Module

GPS-based courthouse detection and location-aware legal services
for mobile legal professionals.
"""

from .gps_detector import CourthouseGPSDetector
from .courthouse_database import CourthouseDatabase
from .location_models import *
from .brief_generator import QuickBriefGenerator

__all__ = [
    "CourthouseGPSDetector",
    "CourthouseDatabase", 
    "QuickBriefGenerator",
    "LocationCoordinates",
    "CourthouseInfo",
    "LocationContext"
]