# GPS Courthouse Detection & Quick Brief Generation

Advanced location-aware legal services for mobile legal professionals, providing real-time courthouse detection, location-based legal assistance, and AI-powered brief generation.

## Features

### 🗺️ GPS Courthouse Detection
- **Real-time Detection**: Automatic courthouse identification using GPS coordinates
- **Geofencing**: Proximity alerts and arrival notifications  
- **Multi-level Accuracy**: High/medium/low GPS accuracy handling
- **Comprehensive Database**: 500+ US federal and state courthouses
- **Spatial Indexing**: Fast geographic search with grid-based optimization

### 🏛️ Courthouse Database
- **Federal Courts**: District, Appeals, Bankruptcy courts
- **State Courts**: Supreme, Superior, Municipal, Family courts  
- **Detailed Information**: Addresses, hours, judges, departments
- **Local Rules**: Filing requirements and procedures
- **Real-time Status**: Business hours and availability checking

### 📝 Quick Brief Generation
- **AI-Powered**: GPT-4 powered legal document generation
- **Court-Specific**: Formatting according to local court rules
- **Multiple Types**: Motions, responses, briefs, memos
- **Citation Integration**: Bluebook and ALWD citation styles
- **Voice Input**: Generate briefs directly from voice commands

### 📍 Location-Aware Services
- **Context Detection**: Understand legal environment from location
- **Smart Suggestions**: Location-based action recommendations
- **Emergency Contacts**: Court-specific emergency information
- **Filing Assistance**: Local filing requirements and deadlines

## API Endpoints

### Courthouse Detection
```http
POST /api/v1/mobile/location/detect-courthouse
Content-Type: application/x-www-form-urlencoded

latitude=40.7128&longitude=-74.0060&accuracy_meters=5
```

### Location Context
```http  
POST /api/v1/mobile/location/context
Content-Type: application/x-www-form-urlencoded

latitude=40.7128&longitude=-74.0060&include_cases=true&include_hearings=true
```

### Quick Brief Generation
```http
POST /api/v1/mobile/location/generate-brief
Content-Type: application/json

{
  "brief_type": "motion",
  "case_title": "Smith v. Johnson", 
  "case_type": "contract_dispute",
  "key_issues": ["Breach of contract", "Damages"],
  "facts_summary": "Plaintiff alleges breach of service contract...",
  "courthouse": {...}
}
```

### Geofencing
```http
POST /api/v1/mobile/location/setup-geofence
Content-Type: application/x-www-form-urlencoded

courthouse_id=12345678-1234-5678-9abc-123456789012&detection_radius_meters=100&notification_radius_meters=500
```

## Usage Examples

### Initialize Services
```python
import openai
from src.mobile_api.location_services import (
    CourthouseDatabase,
    CourthouseGPSDetector, 
    QuickBriefGenerator,
    LocationServicesIntegration
)

# Initialize OpenAI client
openai_client = openai.AsyncOpenAI(api_key="your-key")

# Create integration service
integration = LocationServicesIntegration(openai_client)

# Services are automatically initialized
courthouse_db = integration.courthouse_db
gps_detector = integration.gps_detector  
brief_generator = integration.brief_generator
```

### Detect Courthouse
```python
from src.mobile_api.location_services.location_models import LocationCoordinates, LocationAccuracy

# Create user location
user_location = LocationCoordinates(
    latitude=40.7128,
    longitude=-74.0060,
    accuracy=LocationAccuracy.HIGH,
    accuracy_meters=5.0
)

# Detect courthouse
detection = await gps_detector.detect_courthouse(user_location, user_id)

print(f"Status: {detection.status}")
print(f"Courthouse: {detection.courthouse.name if detection.courthouse else 'None'}")
print(f"Distance: {detection.distance_meters}m")
print(f"Confidence: {detection.confidence_score}")
```

### Generate Brief from Voice Input
```python
# Voice-to-brief generation
result = await integration.quick_courthouse_brief_from_voice(
    voice_input="Generate a motion for summary judgment in the Smith versus Johnson contract case",
    user_location=user_location,
    user_id=user_id,
    brief_type="motion"
)

print(f"Status: {result['status']}")
print(f"Brief ID: {result['brief']['id']}")
print(f"Word Count: {result['brief']['word_count']}")
```

### Search Nearby Courthouses
```python
# Find courthouses within 10km
nearby = courthouse_db.find_nearby_courthouses(
    latitude=40.7128,
    longitude=-74.0060,
    radius_km=10.0,
    max_results=5
)

for courthouse, distance_km in nearby:
    print(f"{courthouse.name} - {distance_km:.1f}km")
    print(f"  Type: {courthouse.court_type.value}")
    print(f"  Address: {courthouse.address}")
    print(f"  Open: {courthouse_db.is_courthouse_open(courthouse)}")
```

### Set Up Smart Geofencing
```python
# Configure intelligent geofencing
preferences = {
    "detection_radius": 100.0,
    "notification_radius": 500.0, 
    "arrival_alerts": True,
    "proximity_alerts": True,
    "auto_brief": False
}

result = await integration.setup_smart_geofencing(user_id, preferences)
print(f"Geofences created: {result['geofences_created']}")
```

## Location Models

### LocationCoordinates
```python
coordinates = LocationCoordinates(
    latitude=40.7128,
    longitude=-74.0060,
    altitude=10.0,  # Optional
    accuracy=LocationAccuracy.HIGH,
    accuracy_meters=5.0,
    timestamp=datetime.utcnow()
)
```

### CourthouseInfo
```python
courthouse = CourthouseInfo(
    name="United States District Court SDNY",
    court_type=CourthouseType.FEDERAL_DISTRICT,
    address="500 Pearl Street", 
    city="New York",
    state="NY",
    zip_code="10007",
    coordinates=coordinates,
    jurisdiction="Southern District of New York",
    judges=["Judge A", "Judge B"],
    departments=["Civil", "Criminal"],
    business_hours={
        "monday": "9:00 AM - 5:00 PM",
        "tuesday": "9:00 AM - 5:00 PM"
    },
    efiling_system="CM/ECF"
)
```

### BriefGenerationRequest
```python
brief_request = BriefGenerationRequest(
    case_title="Smith v. Johnson",
    case_type="contract_dispute",
    brief_type="motion",
    key_issues=["Breach of contract", "Damages calculation"],
    legal_standards=["Material breach standard", "Compensatory damages"],
    facts_summary="Plaintiff contracted for services...",
    courthouse=courthouse,
    length_preference="concise",
    citation_style="bluebook",
    include_citations=True,
    auto_research=True
)
```

## Configuration

### LocationServicesConfig
```python
from src.mobile_api.location_services.location_models import LocationServicesConfig

config = LocationServicesConfig(
    detection_accuracy_threshold=50.0,  # meters
    detection_confidence_threshold=0.7,
    cache_duration_minutes=15,
    max_nearby_courthouses=10,
    search_radius_km=50.0,
    store_location_history=False,  # Privacy setting
    anonymize_location_data=True
)
```

### GeofenceConfig  
```python
geofence_config = GeofenceConfig(
    courthouse_id=courthouse.id,
    detection_radius_meters=100.0,
    notification_radius_meters=500.0,
    enable_arrival_alerts=True,
    enable_departure_alerts=True,
    enable_proximity_alerts=True,
    business_days_only=True,
    auto_brief_generation=False
)
```

## Response Formats

### Courthouse Detection Response
```json
{
  "status": "detected",
  "courthouse": {
    "id": "uuid",
    "name": "US District Court SDNY",
    "court_type": "federal_district",
    "address": "500 Pearl Street",
    "coordinates": {...},
    "business_hours": {...}
  },
  "distance_meters": 45.2,
  "confidence_score": 0.95,
  "user_location": {...},
  "nearby_courthouses": [...]
}
```

### Brief Generation Response
```json
{
  "id": "uuid", 
  "title": "Motion for Summary Judgment in Smith v. Johnson",
  "brief_type": "motion",
  "case_info": {...},
  "courthouse_info": {...},
  "caption": "UNITED STATES DISTRICT COURT...",
  "introduction": "Plaintiff respectfully moves...",
  "statement_of_facts": "The undisputed facts are...",
  "legal_argument": "I. LEGAL STANDARD...",
  "conclusion": "For the foregoing reasons...",
  "signature_block": "Respectfully submitted...",
  "citations": [...],
  "word_count": 1250,
  "confidence_score": 0.88,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Location Context Response
```json
{
  "user_location": {...},
  "current_courthouse": {...},
  "nearby_courthouses": [...],
  "is_business_hours": true,
  "next_business_day": "Monday, January 15",
  "relevant_rules": [
    "Federal Rules of Civil Procedure",
    "Local Civil Rules SDNY"
  ],
  "filing_requirements": [
    "Electronic signature required",
    "Case number mandatory"
  ],
  "emergency_contacts": [...]
}
```

## Advanced Features

### Voice-Aware Brief Generation
```python
# Process voice command with location awareness  
result = await integration.process_location_aware_voice_command(
    voice_text="Generate a motion to dismiss for the Johnson case",
    user_location=coordinates,
    user_id=user_id
)

if result["status"] == "generated":
    brief = result["brief"]
    print(f"Generated: {brief['title']}")
```

### Comprehensive Context
```python
# Get full courthouse context
context = await integration.get_comprehensive_courthouse_context(
    user_location=coordinates,
    user_id=user_id,
    include_brief_templates=True
)

print(f"Courthouse: {context['detection']['courthouse']['name']}")
print(f"Services: {context['services_available']}")
print(f"Templates: {len(context['brief_templates'])}")
```

### Location Alerts
```python
# Get active location alerts
alerts = await gps_detector.get_location_alerts(user_id)

for alert in alerts:
    print(f"Alert: {alert.title}")
    print(f"Priority: {alert.priority}")
    print(f"Actions: {alert.suggested_actions}")
```

## Error Handling

### Common Error Scenarios
- **GPS_ACCURACY_LOW**: Location accuracy insufficient for courthouse detection
- **NO_COURTHOUSE_DETECTED**: No courthouses found within search radius
- **COURTHOUSE_CLOSED**: Courthouse detected but currently closed
- **BRIEF_GENERATION_FAILED**: AI brief generation encountered errors
- **INVALID_COORDINATES**: GPS coordinates out of valid range

### Error Response Format
```json
{
  "error_code": "GPS_ACCURACY_LOW",
  "error_message": "GPS accuracy too low for reliable courthouse detection",
  "details": {
    "required_accuracy": 50.0,
    "current_accuracy": 150.0,
    "suggestions": ["Wait for better GPS signal", "Move to open area"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Performance Optimization

### Caching Strategy
- **Detection Cache**: 15-minute cache for GPS detections
- **Rules Cache**: 24-hour cache for court rules and formatting
- **Spatial Index**: Grid-based indexing for fast courthouse search
- **Brief Templates**: Memory-cached templates for each court type

### Background Processing
- **Geofence Monitoring**: Continuous background location monitoring
- **Cache Cleanup**: Automatic cleanup of expired cache entries
- **Health Checks**: Regular service health monitoring

## Security & Privacy

### Location Privacy
- **Optional Storage**: Location history storage is opt-in
- **Data Anonymization**: GPS coordinates can be anonymized
- **Retention Policies**: Configurable data retention periods
- **Secure Transmission**: All location data encrypted in transit

### Authentication Integration
- **JWT Integration**: Seamless integration with mobile authentication
- **Session Validation**: Location services validate user sessions
- **Permission Checks**: Location access requires proper permissions

## Testing

### Unit Tests
```bash
pytest tests/unit/location_services/
```

### Integration Tests
```bash  
pytest tests/integration/location_services/
```

### Mock Data
```python
# Test with mock courthouse data
from tests.fixtures.courthouse_fixtures import mock_courthouse_data

courthouse_db = CourthouseDatabase()
for courthouse_data in mock_courthouse_data:
    courthouse_db.add_courthouse(courthouse_data)
```

## Deployment Considerations

### Production Requirements
- **OpenAI API**: Valid API key with sufficient quota
- **GPS Permissions**: Mobile app must request location permissions
- **Background Processing**: Consider battery usage for geofencing
- **Data Storage**: Courthouse database can be file-based or database-backed

### Monitoring
- **Detection Accuracy**: Monitor courthouse detection success rates
- **Brief Quality**: Track brief generation confidence scores  
- **Performance Metrics**: API response times and cache hit rates
- **Error Rates**: Monitor GPS accuracy issues and service failures

### Scalability
- **Spatial Indexing**: Grid-based indexing scales to 10,000+ courthouses
- **Caching Strategy**: Reduces AI API calls and improves response times
- **Async Processing**: All operations use async/await for scalability

## Future Enhancements

### Planned Features
- **Offline Mode**: Basic courthouse detection without internet
- **ML Improvements**: Custom models for legal document classification
- **Integration APIs**: Direct integration with legal research databases
- **Advanced Geofencing**: Time-based and case-specific geofences
- **Collaborative Features**: Shared courthouse information updates

### Research Integration  
- **Westlaw/LexisNexis**: Direct integration with legal research platforms
- **CourtListener**: Real-time court filing updates
- **PACER Integration**: Federal court document access
- **State Court APIs**: Integration with state-specific e-filing systems

## Support

For additional information:
- **API Documentation**: Available at `/docs` when services are running
- **Error Troubleshooting**: Check logs for detailed error information  
- **Performance Tuning**: Monitor cache hit rates and adjust timeouts
- **Feature Requests**: Submit issues for new courthouse data or features

## License

This module is part of the Legal AI System and follows the same licensing terms as the parent project.