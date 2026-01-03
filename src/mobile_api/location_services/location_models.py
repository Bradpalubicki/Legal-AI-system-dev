"""
Location Services Data Models

Pydantic models for GPS coordinates, courthouse information,
and location-based legal services.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class LocationAccuracy(str, Enum):
    """GPS location accuracy levels"""
    HIGH = "high"          # <5m accuracy
    MEDIUM = "medium"      # 5-50m accuracy  
    LOW = "low"           # >50m accuracy
    UNKNOWN = "unknown"    # Accuracy not available


class CourthouseType(str, Enum):
    """Types of court facilities"""
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_APPEALS = "federal_appeals"
    FEDERAL_BANKRUPTCY = "federal_bankruptcy"
    STATE_SUPREME = "state_supreme"
    STATE_APPELLATE = "state_appellate"
    STATE_SUPERIOR = "state_superior"
    STATE_MUNICIPAL = "state_municipal"
    STATE_FAMILY = "state_family"
    STATE_PROBATE = "state_probate"
    STATE_TRAFFIC = "state_traffic"
    ADMINISTRATIVE = "administrative"


class DetectionStatus(str, Enum):
    """Courthouse detection status"""
    DETECTED = "detected"
    NEARBY = "nearby"
    UNCERTAIN = "uncertain"
    NOT_DETECTED = "not_detected"


class LocationCoordinates(BaseModel):
    """GPS coordinates with accuracy information"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy: LocationAccuracy = LocationAccuracy.UNKNOWN
    accuracy_meters: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('accuracy_meters')
    def validate_accuracy_meters(cls, v):
        if v is not None and v < 0:
            raise ValueError('Accuracy must be non-negative')
        return v


class CourthouseInfo(BaseModel):
    """Comprehensive courthouse information"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    court_type: CourthouseType
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "United States"
    coordinates: LocationCoordinates
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Court-specific information
    jurisdiction: str
    judges: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    case_types: List[str] = Field(default_factory=list)
    
    # Operating information
    business_hours: Dict[str, str] = Field(default_factory=dict)
    filing_deadlines: Dict[str, str] = Field(default_factory=dict)
    local_rules_url: Optional[str] = None
    efiling_system: Optional[str] = None
    
    # Security and access
    security_requirements: List[str] = Field(default_factory=list)
    parking_info: Optional[str] = None
    accessibility_info: Optional[str] = None
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = "manual"
    verified: bool = False


class CourthouseDetection(BaseModel):
    """Result of courthouse detection"""
    status: DetectionStatus
    courthouse: Optional[CourthouseInfo] = None
    distance_meters: Optional[float] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    detection_time: datetime = Field(default_factory=datetime.utcnow)
    user_location: LocationCoordinates
    nearby_courthouses: List[CourthouseInfo] = Field(default_factory=list)
    
    @validator('distance_meters')
    def validate_distance(cls, v):
        if v is not None and v < 0:
            raise ValueError('Distance must be non-negative')
        return v


class LocationContext(BaseModel):
    """Context information for location-based services"""
    user_location: LocationCoordinates
    current_courthouse: Optional[CourthouseInfo] = None
    nearby_courthouses: List[CourthouseInfo] = Field(default_factory=list)
    
    # Time-based context
    current_time: datetime = Field(default_factory=datetime.utcnow)
    is_business_hours: bool = False
    next_business_day: Optional[str] = None
    
    # User context
    user_id: UUID
    active_cases: List[Dict[str, Any]] = Field(default_factory=list)
    upcoming_hearings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Legal context
    relevant_rules: List[str] = Field(default_factory=list)
    filing_requirements: List[str] = Field(default_factory=list)
    emergency_contacts: List[Dict[str, str]] = Field(default_factory=list)


class BriefGenerationRequest(BaseModel):
    """Request for quick brief generation"""
    case_id: Optional[UUID] = None
    case_title: Optional[str] = None
    case_type: str = "general"
    
    # Location context
    courthouse: Optional[CourthouseInfo] = None
    hearing_date: Optional[datetime] = None
    hearing_type: Optional[str] = None
    
    # Brief parameters
    brief_type: str = "motion"  # motion, response, brief, memo
    key_issues: List[str] = Field(default_factory=list)
    legal_standards: List[str] = Field(default_factory=list)
    facts_summary: Optional[str] = None
    
    # Document preferences
    length_preference: str = "concise"  # concise, standard, detailed
    citation_style: str = "bluebook"
    include_signature_block: bool = True
    
    # Automation level
    auto_research: bool = True
    include_citations: bool = True
    include_precedents: bool = True


class QuickBrief(BaseModel):
    """Generated quick brief document"""
    id: UUID = Field(default_factory=uuid4)
    title: str
    brief_type: str
    case_info: Dict[str, Any]
    courthouse_info: Optional[CourthouseInfo] = None
    
    # Brief content
    caption: str
    introduction: str
    statement_of_facts: str
    legal_argument: str
    conclusion: str
    signature_block: str
    
    # Supporting information
    citations: List[Dict[str, str]] = Field(default_factory=list)
    precedents: List[Dict[str, Any]] = Field(default_factory=list)
    local_rules_cited: List[str] = Field(default_factory=list)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = 0
    estimated_filing_fee: Optional[float] = None
    filing_deadline: Optional[datetime] = None
    
    # Quality metrics
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    completeness_score: float = Field(ge=0.0, le=1.0, default=0.8)
    citations_verified: bool = False


class LocationAlert(BaseModel):
    """Location-based alert for legal professionals"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    alert_type: str  # courthouse_arrival, filing_deadline, hearing_reminder
    priority: str = "medium"  # low, medium, high, urgent
    
    title: str
    message: str
    location_context: Optional[LocationContext] = None
    
    # Action items
    suggested_actions: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    deadlines: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    acknowledged: bool = False
    dismissed: bool = False


class GeofenceConfig(BaseModel):
    """Configuration for courthouse geofencing"""
    courthouse_id: UUID
    detection_radius_meters: float = Field(default=100.0, ge=10.0, le=1000.0)
    notification_radius_meters: float = Field(default=500.0, ge=50.0, le=5000.0)
    
    # Trigger conditions
    enable_arrival_alerts: bool = True
    enable_departure_alerts: bool = True
    enable_proximity_alerts: bool = True
    
    # Time-based rules
    active_hours: Dict[str, str] = Field(default_factory=dict)
    business_days_only: bool = True
    
    # User preferences
    notification_types: List[str] = Field(default_factory=list)
    auto_brief_generation: bool = False
    auto_case_context: bool = True


class LocationServicesConfig(BaseModel):
    """Configuration for location services"""
    # Detection settings
    detection_accuracy_threshold: float = 50.0  # meters
    detection_confidence_threshold: float = 0.7
    cache_duration_minutes: int = 15
    
    # Database settings
    courthouse_database_url: Optional[str] = None
    update_frequency_hours: int = 24
    enable_crowd_sourcing: bool = False
    
    # Privacy settings
    store_location_history: bool = False
    anonymize_location_data: bool = True
    location_retention_days: int = 30
    
    # Performance settings
    max_nearby_courthouses: int = 10
    search_radius_km: float = 50.0
    enable_background_updates: bool = True