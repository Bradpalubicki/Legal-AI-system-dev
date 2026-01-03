"""
GPS Courthouse Detection Module

Real-time courthouse detection using GPS coordinates with geofencing,
proximity alerts, and location-based legal services activation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from .location_models import (
    LocationCoordinates,
    CourthouseDetection,
    DetectionStatus,
    LocationContext,
    LocationAlert,
    GeofenceConfig,
    LocationServicesConfig
)
from .courthouse_database import CourthouseDatabase

logger = logging.getLogger(__name__)


class CourthouseGPSDetector:
    """
    GPS-based courthouse detection system with geofencing and proximity alerts
    """
    
    def __init__(
        self,
        courthouse_db: CourthouseDatabase,
        config: Optional[LocationServicesConfig] = None
    ):
        self.courthouse_db = courthouse_db
        self.config = config or LocationServicesConfig()
        
        # Active geofences and detection cache
        self.active_geofences: Dict[str, GeofenceConfig] = {}
        self.detection_cache: Dict[str, CourthouseDetection] = {}
        self.user_locations: Dict[UUID, LocationCoordinates] = {}
        self.location_alerts: Dict[UUID, List[LocationAlert]] = {}
        
        # Performance tracking
        self.detection_count = 0
        self.cache_hits = 0
        
        logger.info("GPS Courthouse Detector initialized")
    
    async def detect_courthouse(
        self,
        user_location: LocationCoordinates,
        user_id: Optional[UUID] = None
    ) -> CourthouseDetection:
        """
        Detect if user is at or near a courthouse
        """
        start_time = datetime.utcnow()
        
        # Check cache first
        cache_key = self._get_cache_key(user_location)
        if cache_key in self.detection_cache:
            cached_detection = self.detection_cache[cache_key]
            
            # Check if cache is still valid
            cache_age = (datetime.utcnow() - cached_detection.detection_time).total_seconds()
            if cache_age < (self.config.cache_duration_minutes * 60):
                self.cache_hits += 1
                logger.debug("Using cached courthouse detection")
                return cached_detection
        
        # Perform detection
        detection = await self._perform_detection(user_location, user_id)
        
        # Cache result
        self.detection_cache[cache_key] = detection
        
        # Update user location if provided
        if user_id:
            self.user_locations[user_id] = user_location
        
        # Process geofence events
        if user_id:
            await self._process_geofence_events(user_id, user_location, detection)
        
        self.detection_count += 1
        processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        logger.debug(f"Courthouse detection completed in {processing_time_ms}ms")
        return detection
    
    async def _perform_detection(
        self,
        user_location: LocationCoordinates,
        user_id: Optional[UUID] = None
    ) -> CourthouseDetection:
        """
        Perform actual courthouse detection logic
        """
        # Find nearby courthouses
        nearby_courthouses = self.courthouse_db.find_nearby_courthouses(
            user_location.latitude,
            user_location.longitude,
            radius_km=self.config.search_radius_km,
            max_results=self.config.max_nearby_courthouses
        )
        
        if not nearby_courthouses:
            return CourthouseDetection(
                status=DetectionStatus.NOT_DETECTED,
                confidence_score=1.0,
                user_location=user_location,
                nearby_courthouses=[]
            )
        
        # Find closest courthouse
        closest_courthouse, closest_distance_km = nearby_courthouses[0]
        closest_distance_meters = closest_distance_km * 1000
        
        # Determine detection status based on distance and accuracy
        status = self._determine_detection_status(
            closest_distance_meters,
            user_location.accuracy_meters or float('inf')
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            closest_distance_meters,
            user_location.accuracy_meters or float('inf'),
            status
        )
        
        # Prepare nearby courthouses list
        nearby_list = [courthouse for courthouse, _ in nearby_courthouses[1:]]
        
        return CourthouseDetection(
            status=status,
            courthouse=closest_courthouse if status in [DetectionStatus.DETECTED, DetectionStatus.NEARBY] else None,
            distance_meters=closest_distance_meters,
            confidence_score=confidence_score,
            user_location=user_location,
            nearby_courthouses=nearby_list
        )
    
    def _determine_detection_status(
        self,
        distance_meters: float,
        location_accuracy_meters: float
    ) -> DetectionStatus:
        """
        Determine detection status based on distance and GPS accuracy
        """
        # Account for GPS accuracy in detection
        effective_distance = distance_meters - location_accuracy_meters
        
        if effective_distance <= 50:  # Within 50 meters (likely inside or very close)
            return DetectionStatus.DETECTED
        elif distance_meters <= 200:  # Within 200 meters (nearby)
            return DetectionStatus.NEARBY
        elif distance_meters <= 500 and location_accuracy_meters > 100:  # Uncertain due to poor GPS
            return DetectionStatus.UNCERTAIN
        else:
            return DetectionStatus.NOT_DETECTED
    
    def _calculate_confidence_score(
        self,
        distance_meters: float,
        location_accuracy_meters: float,
        status: DetectionStatus
    ) -> float:
        """
        Calculate confidence score for detection
        """
        if status == DetectionStatus.NOT_DETECTED:
            return 1.0  # High confidence in non-detection
        
        # Base confidence on distance and accuracy
        max_distance = 500.0  # meters
        distance_factor = max(0, (max_distance - distance_meters) / max_distance)
        
        # Account for GPS accuracy
        accuracy_factor = 1.0
        if location_accuracy_meters <= 10:
            accuracy_factor = 1.0
        elif location_accuracy_meters <= 50:
            accuracy_factor = 0.8
        elif location_accuracy_meters <= 100:
            accuracy_factor = 0.6
        else:
            accuracy_factor = 0.4
        
        # Status-based adjustment
        status_multiplier = {
            DetectionStatus.DETECTED: 1.0,
            DetectionStatus.NEARBY: 0.8,
            DetectionStatus.UNCERTAIN: 0.5
        }.get(status, 0.3)
        
        confidence = distance_factor * accuracy_factor * status_multiplier
        return max(0.1, min(1.0, confidence))  # Clamp between 0.1 and 1.0
    
    async def create_location_context(
        self,
        user_id: UUID,
        user_location: LocationCoordinates,
        active_cases: Optional[List[Dict]] = None,
        upcoming_hearings: Optional[List[Dict]] = None
    ) -> LocationContext:
        """
        Create comprehensive location context for user
        """
        # Detect courthouse
        detection = await self.detect_courthouse(user_location, user_id)
        
        # Find nearby courthouses
        nearby_courthouses = [
            courthouse for courthouse, _ in self.courthouse_db.find_nearby_courthouses(
                user_location.latitude,
                user_location.longitude,
                radius_km=5.0,  # 5km radius for context
                max_results=5
            )
        ]
        
        # Determine current courthouse
        current_courthouse = None
        if detection.status == DetectionStatus.DETECTED:
            current_courthouse = detection.courthouse
        
        # Check if current time is business hours
        is_business_hours = False
        next_business_day = None
        
        if current_courthouse:
            is_business_hours = self.courthouse_db.is_courthouse_open(current_courthouse)
            if not is_business_hours:
                next_business_day = self.courthouse_db.get_next_business_day(current_courthouse)
        
        # Gather relevant rules and requirements
        relevant_rules = []
        filing_requirements = []
        emergency_contacts = []
        
        if current_courthouse:
            relevant_rules = await self._get_relevant_local_rules(current_courthouse)
            filing_requirements = await self._get_filing_requirements(current_courthouse)
            emergency_contacts = await self._get_emergency_contacts(current_courthouse)
        
        return LocationContext(
            user_location=user_location,
            current_courthouse=current_courthouse,
            nearby_courthouses=nearby_courthouses,
            is_business_hours=is_business_hours,
            next_business_day=next_business_day,
            user_id=user_id,
            active_cases=active_cases or [],
            upcoming_hearings=upcoming_hearings or [],
            relevant_rules=relevant_rules,
            filing_requirements=filing_requirements,
            emergency_contacts=emergency_contacts
        )
    
    async def setup_geofence(
        self,
        user_id: UUID,
        courthouse_id: UUID,
        config: GeofenceConfig
    ) -> str:
        """
        Set up geofence monitoring for a courthouse
        """
        geofence_id = f"{user_id}_{courthouse_id}"
        self.active_geofences[geofence_id] = config
        
        logger.info(f"Geofence setup for user {user_id} at courthouse {courthouse_id}")
        return geofence_id
    
    async def remove_geofence(self, geofence_id: str) -> bool:
        """
        Remove geofence monitoring
        """
        if geofence_id in self.active_geofences:
            del self.active_geofences[geofence_id]
            logger.info(f"Removed geofence {geofence_id}")
            return True
        return False
    
    async def _process_geofence_events(
        self,
        user_id: UUID,
        current_location: LocationCoordinates,
        detection: CourthouseDetection
    ):
        """
        Process geofence entry/exit events
        """
        # Find relevant geofences for this user
        user_geofences = {
            gf_id: config for gf_id, config in self.active_geofences.items()
            if gf_id.startswith(str(user_id))
        }
        
        for geofence_id, config in user_geofences.items():
            courthouse = self.courthouse_db.get_courthouse(str(config.courthouse_id))
            if not courthouse:
                continue
            
            # Calculate distance to courthouse
            distance_km = self.courthouse_db._haversine_distance(
                current_location.latitude,
                current_location.longitude,
                courthouse.coordinates.latitude,
                courthouse.coordinates.longitude
            )
            distance_meters = distance_km * 1000
            
            # Check for geofence events
            if distance_meters <= config.detection_radius_meters:
                await self._trigger_arrival_event(user_id, courthouse, distance_meters, config)
            elif distance_meters <= config.notification_radius_meters:
                await self._trigger_proximity_event(user_id, courthouse, distance_meters, config)
    
    async def _trigger_arrival_event(
        self,
        user_id: UUID,
        courthouse,
        distance_meters: float,
        config: GeofenceConfig
    ):
        """
        Trigger courthouse arrival event
        """
        if not config.enable_arrival_alerts:
            return
        
        alert = LocationAlert(
            user_id=user_id,
            alert_type="courthouse_arrival",
            priority="high",
            title=f"Arrived at {courthouse.name}",
            message=f"You have arrived at {courthouse.name}. Distance: {int(distance_meters)}m",
            suggested_actions=[
                "Check in for hearing",
                "Review case documents",
                "Find courtroom location",
                "Check local rules"
            ]
        )
        
        await self._add_location_alert(user_id, alert)
        logger.info(f"Triggered arrival event for user {user_id} at {courthouse.name}")
    
    async def _trigger_proximity_event(
        self,
        user_id: UUID,
        courthouse,
        distance_meters: float,
        config: GeofenceConfig
    ):
        """
        Trigger courthouse proximity event
        """
        if not config.enable_proximity_alerts:
            return
        
        alert = LocationAlert(
            user_id=user_id,
            alert_type="courthouse_proximity",
            priority="medium",
            title=f"Approaching {courthouse.name}",
            message=f"You are {int(distance_meters)}m from {courthouse.name}",
            suggested_actions=[
                "Review hearing schedule",
                "Prepare documents",
                "Check parking information",
                "Allow extra time for security"
            ]
        )
        
        await self._add_location_alert(user_id, alert)
    
    async def _add_location_alert(self, user_id: UUID, alert: LocationAlert):
        """
        Add location alert for user
        """
        if user_id not in self.location_alerts:
            self.location_alerts[user_id] = []
        
        # Check for duplicate alerts (within last 30 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        existing_alerts = [
            a for a in self.location_alerts[user_id]
            if a.alert_type == alert.alert_type and a.created_at > cutoff_time
        ]
        
        if not existing_alerts:
            self.location_alerts[user_id].append(alert)
            logger.debug(f"Added location alert for user {user_id}: {alert.title}")
    
    async def get_location_alerts(self, user_id: UUID) -> List[LocationAlert]:
        """
        Get active location alerts for user
        """
        if user_id not in self.location_alerts:
            return []
        
        # Filter out expired alerts
        current_time = datetime.utcnow()
        active_alerts = [
            alert for alert in self.location_alerts[user_id]
            if not alert.expires_at or alert.expires_at > current_time
        ]
        
        # Update alerts list
        self.location_alerts[user_id] = active_alerts
        
        return [alert for alert in active_alerts if not alert.dismissed]
    
    async def dismiss_alert(self, user_id: UUID, alert_id: UUID) -> bool:
        """
        Dismiss a location alert
        """
        if user_id not in self.location_alerts:
            return False
        
        for alert in self.location_alerts[user_id]:
            if alert.id == alert_id:
                alert.dismissed = True
                return True
        
        return False
    
    async def _get_relevant_local_rules(self, courthouse) -> List[str]:
        """
        Get relevant local rules for the courthouse
        """
        # This would integrate with local rules database
        rules = []
        
        if courthouse.court_type.value.startswith("federal"):
            rules.extend([
                "Federal Rules of Civil Procedure",
                "Local Civil Rules",
                "Electronic Filing Requirements"
            ])
        else:
            rules.extend([
                "State Civil Procedure Rules",
                "Local Court Rules",
                "Filing Requirements"
            ])
        
        if courthouse.efiling_system:
            rules.append(f"E-Filing System: {courthouse.efiling_system}")
        
        return rules
    
    async def _get_filing_requirements(self, courthouse) -> List[str]:
        """
        Get filing requirements for the courthouse
        """
        requirements = [
            "Valid government-issued photo ID",
            "Case number for all filings"
        ]
        
        if courthouse.security_requirements:
            requirements.extend(courthouse.security_requirements)
        
        if courthouse.efiling_system:
            requirements.append("Electronic signature required for e-filings")
        
        return requirements
    
    async def _get_emergency_contacts(self, courthouse) -> List[Dict[str, str]]:
        """
        Get emergency contacts for the courthouse
        """
        contacts = []
        
        if courthouse.phone:
            contacts.append({
                "name": "Court Clerk",
                "phone": courthouse.phone,
                "type": "main"
            })
        
        # Add standard emergency contacts
        contacts.extend([
            {
                "name": "Emergency Services",
                "phone": "911",
                "type": "emergency"
            },
            {
                "name": "Court Security",
                "phone": courthouse.phone or "N/A",
                "type": "security"
            }
        ])
        
        return contacts
    
    def _get_cache_key(self, location: LocationCoordinates) -> str:
        """
        Generate cache key for location
        """
        # Round to reasonable precision for caching
        lat_rounded = round(location.latitude, 4)  # ~11m precision
        lon_rounded = round(location.longitude, 4)
        return f"{lat_rounded}_{lon_rounded}"
    
    async def cleanup_cache(self, max_age_minutes: int = 60):
        """
        Clean up expired cache entries
        """
        current_time = datetime.utcnow()
        expired_keys = []
        
        for cache_key, detection in self.detection_cache.items():
            age_minutes = (current_time - detection.detection_time).total_seconds() / 60
            if age_minutes > max_age_minutes:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.detection_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_detector_stats(self) -> Dict[str, any]:
        """
        Get detector performance statistics
        """
        cache_hit_rate = (self.cache_hits / self.detection_count) if self.detection_count > 0 else 0
        
        return {
            "detection_count": self.detection_count,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "active_geofences": len(self.active_geofences),
            "cached_detections": len(self.detection_cache),
            "tracked_users": len(self.user_locations),
            "active_alerts": sum(len(alerts) for alerts in self.location_alerts.values())
        }