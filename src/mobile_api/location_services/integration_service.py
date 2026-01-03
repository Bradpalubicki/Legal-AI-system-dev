"""
Location Services Integration

Central integration service that coordinates GPS detection, courthouse database,
brief generation, and mobile API services for seamless location-aware functionality.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import openai
from fastapi import HTTPException

from .gps_detector import CourthouseGPSDetector
from .courthouse_database import CourthouseDatabase
from .brief_generator import QuickBriefGenerator
from .location_models import (
    LocationCoordinates,
    LocationServicesConfig,
    BriefGenerationRequest,
    VoiceCommandType
)

logger = logging.getLogger(__name__)


class LocationServicesIntegration:
    """
    Central integration service that coordinates all location-based services
    for the mobile legal AI system.
    """
    
    def __init__(
        self,
        openai_client: openai.AsyncOpenAI,
        config: Optional[LocationServicesConfig] = None
    ):
        self.config = config or LocationServicesConfig()
        
        # Initialize core services
        self.courthouse_db = CourthouseDatabase()
        self.gps_detector = CourthouseGPSDetector(self.courthouse_db, self.config)
        self.brief_generator = QuickBriefGenerator(openai_client)
        
        # Service status tracking
        self.services_initialized = True
        self.last_health_check = datetime.utcnow()
        
        logger.info("Location services integration initialized")
    
    async def process_location_aware_voice_command(
        self,
        voice_text: str,
        user_location: LocationCoordinates,
        user_id: UUID,
        command_type: Optional[VoiceCommandType] = None
    ) -> Dict:
        """
        Process voice command with full location awareness and courthouse context
        """
        try:
            # 1. Detect courthouse context
            detection = await self.gps_detector.detect_courthouse(user_location, user_id)
            
            # 2. Create comprehensive location context
            location_context = await self.gps_detector.create_location_context(
                user_id=user_id,
                user_location=user_location
            )
            
            # 3. Determine if this is a brief generation request
            is_brief_request = await self._is_brief_generation_request(voice_text)
            
            # 4. Process based on command type and context
            if is_brief_request and detection.courthouse:
                return await self._handle_brief_generation_voice_command(
                    voice_text, detection.courthouse, location_context, user_id
                )
            elif detection.status.value in ["detected", "nearby"]:
                return await self._handle_courthouse_aware_voice_command(
                    voice_text, detection, location_context, command_type
                )
            else:
                return await self._handle_standard_voice_command(
                    voice_text, location_context, command_type
                )
                
        except Exception as e:
            logger.error(f"Location-aware voice processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def quick_courthouse_brief_from_voice(
        self,
        voice_input: str,
        user_location: LocationCoordinates,
        user_id: UUID,
        brief_type: str = "motion"
    ) -> Dict:
        """
        Generate a quick brief directly from voice input and courthouse location
        """
        try:
            # 1. Detect courthouse
            detection = await self.gps_detector.detect_courthouse(user_location, user_id)
            
            if not detection.courthouse:
                return {
                    "status": "no_courthouse_detected",
                    "message": "No courthouse detected. Please get closer to a courthouse or specify one manually.",
                    "suggested_actions": ["Find nearby courthouses", "Specify courthouse manually"]
                }
            
            # 2. Extract brief requirements from voice input
            brief_requirements = await self._extract_brief_requirements_from_voice(
                voice_input, brief_type
            )
            
            # 3. Create brief generation request
            brief_request = BriefGenerationRequest(
                brief_type=brief_type,
                courthouse=detection.courthouse,
                **brief_requirements
            )
            
            # 4. Create location context
            location_context = await self.gps_detector.create_location_context(
                user_id=user_id,
                user_location=user_location
            )
            
            # 5. Generate the brief
            brief = await self.brief_generator.generate_quick_brief(
                brief_request, location_context
            )
            
            return {
                "status": "generated",
                "brief": brief.dict(),
                "courthouse": detection.courthouse.dict(),
                "generation_time": brief.generated_at.isoformat(),
                "confidence_score": brief.confidence_score,
                "suggested_actions": [
                    "Review and edit brief",
                    "Check local filing requirements", 
                    "Export to PDF",
                    "File electronically"
                ]
            }
            
        except Exception as e:
            logger.error(f"Voice-to-brief generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_comprehensive_courthouse_context(
        self,
        user_location: LocationCoordinates,
        user_id: UUID,
        include_brief_templates: bool = False
    ) -> Dict:
        """
        Get comprehensive courthouse context including detection, rules, and services
        """
        try:
            # Get courthouse detection
            detection = await self.gps_detector.detect_courthouse(user_location, user_id)
            
            # Get location context
            location_context = await self.gps_detector.create_location_context(
                user_id=user_id,
                user_location=user_location
            )
            
            # Get nearby courthouses for comparison
            nearby_courthouses = self.courthouse_db.find_nearby_courthouses(
                user_location.latitude,
                user_location.longitude,
                radius_km=5.0,
                max_results=5
            )
            
            context = {
                "detection": detection.dict(),
                "location_context": location_context.dict(),
                "nearby_courthouses": [
                    {"courthouse": ch.dict(), "distance_km": dist}
                    for ch, dist in nearby_courthouses
                ],
                "services_available": {
                    "brief_generation": True,
                    "geofence_monitoring": True,
                    "local_rules_lookup": True,
                    "filing_assistance": True
                }
            }
            
            # Add brief templates if requested
            if include_brief_templates and detection.courthouse:
                templates = await self._get_courthouse_brief_templates(detection.courthouse)
                context["brief_templates"] = templates
            
            return context
            
        except Exception as e:
            logger.error(f"Comprehensive context creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def setup_smart_geofencing(
        self,
        user_id: UUID,
        preferences: Dict
    ) -> Dict:
        """
        Set up intelligent geofencing based on user's active cases and preferences
        """
        try:
            # Get user's location history and active cases (mock for now)
            active_cases = await self._get_user_active_cases(user_id)
            frequent_courthouses = await self._get_frequent_courthouses(user_id)
            
            geofences_created = []
            
            # Set up geofences for frequent courthouses
            for courthouse_info in frequent_courthouses:
                from .location_models import GeofenceConfig
                
                config = GeofenceConfig(
                    courthouse_id=courthouse_info["courthouse_id"],
                    detection_radius_meters=preferences.get("detection_radius", 100.0),
                    notification_radius_meters=preferences.get("notification_radius", 500.0),
                    enable_arrival_alerts=preferences.get("arrival_alerts", True),
                    enable_proximity_alerts=preferences.get("proximity_alerts", True),
                    auto_brief_generation=preferences.get("auto_brief", False)
                )
                
                geofence_id = await self.gps_detector.setup_geofence(
                    user_id, courthouse_info["courthouse_id"], config
                )
                
                geofences_created.append({
                    "geofence_id": geofence_id,
                    "courthouse_name": courthouse_info["courthouse_name"],
                    "config": config.dict()
                })
            
            return {
                "status": "configured",
                "geofences_created": len(geofences_created),
                "geofences": geofences_created,
                "message": f"Smart geofencing activated for {len(geofences_created)} courthouses"
            }
            
        except Exception as e:
            logger.error(f"Smart geofencing setup failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _is_brief_generation_request(self, voice_text: str) -> bool:
        """Determine if voice input is requesting brief generation"""
        brief_keywords = [
            "generate brief", "create brief", "write brief", "draft brief",
            "motion", "response", "memo", "memorandum", "filing",
            "brief for", "document for", "legal document"
        ]
        
        voice_lower = voice_text.lower()
        return any(keyword in voice_lower for keyword in brief_keywords)
    
    async def _extract_brief_requirements_from_voice(
        self,
        voice_input: str,
        brief_type: str
    ) -> Dict:
        """Extract brief generation requirements from voice input using AI"""
        try:
            # Use OpenAI to extract structured requirements from voice input
            prompt = f"""
            Extract legal brief requirements from this voice input: "{voice_input}"
            
            Brief type: {brief_type}
            
            Extract and return in JSON format:
            - case_title: string (if mentioned)
            - case_type: string (personal_injury, contract, family, etc.)
            - key_issues: array of strings
            - legal_standards: array of strings  
            - facts_summary: string (if provided)
            - length_preference: "concise", "standard", or "detailed"
            
            Return only valid JSON.
            """
            
            response = await self.brief_generator.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            import json
            requirements = json.loads(response.choices[0].message.content)
            
            # Set defaults for missing values
            requirements.setdefault("case_type", "general")
            requirements.setdefault("key_issues", [])
            requirements.setdefault("legal_standards", [])
            requirements.setdefault("length_preference", "concise")
            
            return requirements
            
        except Exception as e:
            logger.warning(f"Failed to extract requirements from voice: {str(e)}")
            return {
                "case_type": "general",
                "key_issues": [],
                "legal_standards": [],
                "length_preference": "concise",
                "facts_summary": voice_input
            }
    
    async def _handle_brief_generation_voice_command(
        self,
        voice_text: str,
        courthouse,
        location_context,
        user_id: UUID
    ) -> Dict:
        """Handle voice command that requests brief generation"""
        
        # Extract brief type from voice input
        brief_type = "motion"  # Default
        if "response" in voice_text.lower():
            brief_type = "response"
        elif "memo" in voice_text.lower() or "memorandum" in voice_text.lower():
            brief_type = "memo"
        elif "brief" in voice_text.lower():
            brief_type = "brief"
        
        return await self.quick_courthouse_brief_from_voice(
            voice_text, location_context.user_location, user_id, brief_type
        )
    
    async def _handle_courthouse_aware_voice_command(
        self,
        voice_text: str,
        detection,
        location_context,
        command_type: Optional[VoiceCommandType]
    ) -> Dict:
        """Handle voice command with courthouse context"""
        
        courthouse_suggestions = []
        if detection.courthouse:
            courthouse_suggestions = [
                f"File documents at {detection.courthouse.name}",
                "Check courthouse hours",
                "View local filing rules",
                "Generate courthouse-specific brief"
            ]
        
        return {
            "status": "processed_with_courthouse_context",
            "voice_input": voice_text,
            "courthouse_detected": detection.courthouse.dict() if detection.courthouse else None,
            "distance_meters": detection.distance_meters,
            "confidence_score": detection.confidence_score,
            "location_context": {
                "is_business_hours": location_context.is_business_hours,
                "relevant_rules": location_context.relevant_rules,
                "filing_requirements": location_context.filing_requirements
            },
            "suggested_actions": courthouse_suggestions,
            "message": f"Processed with courthouse context: {detection.courthouse.name if detection.courthouse else 'None detected'}"
        }
    
    async def _handle_standard_voice_command(
        self,
        voice_text: str,
        location_context,
        command_type: Optional[VoiceCommandType]
    ) -> Dict:
        """Handle standard voice command without specific courthouse context"""
        
        return {
            "status": "processed_standard",
            "voice_input": voice_text,
            "location_provided": True,
            "nearby_courthouses": len(location_context.nearby_courthouses),
            "suggested_actions": [
                "Find nearby courthouses",
                "Get location-based legal assistance",
                "Set up courthouse alerts"
            ],
            "message": "Processed voice command with location context"
        }
    
    async def _get_courthouse_brief_templates(self, courthouse) -> List[Dict]:
        """Get available brief templates for courthouse"""
        templates = [
            {
                "type": "motion",
                "name": "Motion for Summary Judgment",
                "court_specific": True,
                "estimated_pages": 8
            },
            {
                "type": "response", 
                "name": "Response to Motion",
                "court_specific": True,
                "estimated_pages": 6
            },
            {
                "type": "brief",
                "name": "Appellate Brief",
                "court_specific": False,
                "estimated_pages": 20
            }
        ]
        
        return templates
    
    async def _get_user_active_cases(self, user_id: UUID) -> List[Dict]:
        """Get user's active cases (mock implementation)"""
        return [
            {
                "case_id": "case-123",
                "title": "Smith v. Johnson", 
                "court": "Superior Court",
                "status": "active"
            }
        ]
    
    async def _get_frequent_courthouses(self, user_id: UUID) -> List[Dict]:
        """Get user's frequently visited courthouses (mock implementation)"""
        return [
            {
                "courthouse_id": UUID("12345678-1234-5678-9abc-123456789012"),
                "courthouse_name": "Los Angeles Superior Court",
                "visit_frequency": 5
            }
        ]
    
    def get_service_health(self) -> Dict:
        """Get health status of all location services"""
        return {
            "services_initialized": self.services_initialized,
            "last_health_check": self.last_health_check.isoformat(),
            "courthouse_database": {
                "total_courthouses": len(self.courthouse_db.courthouses),
                "status": "healthy"
            },
            "gps_detector": {
                "active_geofences": len(self.gps_detector.active_geofences),
                "cache_size": len(self.gps_detector.detection_cache),
                "status": "healthy"
            },
            "brief_generator": {
                "templates_loaded": len(self.brief_generator.brief_templates),
                "status": "healthy"
            }
        }
    
    async def cleanup_services(self):
        """Clean up services and cached data"""
        try:
            await self.gps_detector.cleanup_cache()
            logger.info("Location services cleanup completed")
        except Exception as e:
            logger.error(f"Service cleanup failed: {str(e)}")