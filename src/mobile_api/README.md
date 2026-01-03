# Mobile API Module

This module provides comprehensive mobile API functionality for the Legal AI System, including voice command processing, mobile authentication, and mobile-optimized endpoints.

## Features

### 🎤 Voice Command Processing
- **Speech-to-Text**: Convert audio input to text using OpenAI Whisper
- **Intent Recognition**: Classify voice commands into actionable categories
- **Natural Language Understanding**: Parse commands and extract relevant parameters
- **Multi-language Support**: Support for various languages (default: en-US)

### 🔐 Mobile Authentication
- **Device Registration**: Secure device registration and management
- **JWT Token Management**: Access and refresh token generation
- **Session Management**: Mobile session tracking and validation
- **Biometric Support**: Framework for biometric authentication integration

### 📱 Mobile-Optimized Endpoints
- **Document Operations**: Search, summarize, and manage documents
- **Case Management**: Create and manage legal cases
- **Calendar Integration**: Schedule meetings and check calendar
- **Legal Research**: Mobile-friendly legal research functionality
- **Note Taking**: Voice dictation and note management

## API Endpoints

### Authentication
```
POST /api/v1/mobile/auth/register-device
POST /api/v1/mobile/auth/refresh
POST /api/v1/mobile/auth/logout
```

### Voice Commands
```
POST /api/v1/mobile/voice/process
POST /api/v1/mobile/voice/upload-audio
GET  /api/v1/mobile/voice/settings
PUT  /api/v1/mobile/voice/settings
```

### Mobile Services
```
POST /api/v1/mobile/documents/summarize
POST /api/v1/mobile/research/legal
GET  /api/v1/mobile/calendar
POST /api/v1/mobile/calendar/event
GET  /api/v1/mobile/deadlines
POST /api/v1/mobile/clients/update
GET  /api/v1/mobile/session/info
GET  /api/v1/mobile/health
```

## Voice Command Types

### Supported Commands
- **Document Search**: "Search for contracts with XYZ Corp"
- **Case Creation**: "Create a new case for Johnson vs Smith"
- **Note Dictation**: "Take a note: Follow up with client"
- **Meeting Scheduling**: "Schedule a meeting with John Smith"
- **Calendar Queries**: "What's on my calendar today?"
- **Document Summarization**: "Summarize the contract document"
- **Legal Research**: "Research case law on contract disputes"
- **Deadline Checking**: "What deadlines do I have coming up?"
- **Client Updates**: "Update client status for case 123"
- **General Queries**: "Explain the discovery process"

### Command Processing Flow
1. **Audio Input**: Receive audio data or text input
2. **Speech-to-Text**: Convert audio to text using Whisper API
3. **Intent Classification**: Determine command type and intent
4. **Parameter Extraction**: Extract relevant parameters from command
5. **Handler Routing**: Route to appropriate command handler
6. **Action Execution**: Execute the requested action
7. **Response Generation**: Generate mobile-friendly response

## Usage Examples

### Initialize Mobile API
```python
from src.mobile_api import VoiceProcessor, MobileAuthManager
from src.mobile_api.api_endpoints import init_mobile_api
import openai

# Initialize services
voice_processor = VoiceProcessor(openai.AsyncOpenAI(api_key="your-key"))
auth_manager = MobileAuthManager(secret_key="your-secret")

# Initialize API
init_mobile_api(voice_processor, auth_manager)
```

### Process Voice Command
```python
from src.mobile_api.models import VoiceCommandRequest

# Text input
request = VoiceCommandRequest(
    text_input="Search for contracts with ABC Corp",
    language="en-US"
)

response = await voice_processor.process_voice_command(
    request, user_id, session_id
)
```

### Audio Input
```python
# Audio input (base64 encoded)
request = VoiceCommandRequest(
    audio_data=base64_audio_data,
    audio_format="wav",
    language="en-US"
)

response = await voice_processor.process_voice_command(
    request, user_id, session_id
)
```

### Register Mobile Device
```python
session = await auth_manager.register_mobile_device(
    user_id=user_id,
    device_id="device-123",
    device_type="iOS",
    app_version="1.0.0"
)

access_token = await auth_manager.create_mobile_access_token(
    user_id, session.id, "device-123"
)
```

## Configuration

### Voice Settings
```python
voice_settings = {
    "language": "en-US",
    "voice_speed": 1.0,
    "wake_word_enabled": True,
    "auto_transcription": True,
    "noise_cancellation": True,
    "preferred_commands": ["search", "create case", "take note"]
}
```

### Authentication Settings
```python
auth_config = {
    "access_token_expire": 24 * 60 * 60,  # 24 hours
    "refresh_token_expire": 30 * 24 * 60 * 60,  # 30 days
    "session_timeout": 7 * 24 * 60 * 60,  # 7 days
    "max_sessions_per_user": 5
}
```

## Response Format

### Successful Voice Command Response
```json
{
  "command_id": "uuid",
  "status": "completed",
  "message": "Document search completed",
  "data": {
    "action": "document_search",
    "results": [...],
    "query": "contracts with ABC Corp"
  },
  "suggested_actions": ["Open document", "Refine search"],
  "processing_time_ms": 1500
}
```

### Error Response
```json
{
  "command_id": "uuid",
  "status": "failed",
  "message": "Failed to process command: Invalid audio format",
  "processing_time_ms": 500
}
```

## Security Features

### Token-Based Authentication
- JWT access tokens with 24-hour expiry
- Refresh tokens with 30-day expiry
- Device-specific token binding
- Automatic token rotation

### Session Security
- Device ID validation
- Session timeout management
- Activity tracking
- Automatic cleanup of expired sessions

### Data Protection
- Audio data is processed and not stored
- Encrypted token payload
- Secure session management
- Audit logging for all operations

## Integration Points

### Legal AI System Integration
- Document processing services
- Case management system
- Calendar and scheduling
- Legal research APIs
- Client portal integration

### External Services
- OpenAI Whisper for speech-to-text
- OpenAI GPT for natural language understanding
- Calendar services (Google, Outlook)
- Legal research databases

## Error Handling

### Common Error Scenarios
- **Invalid Audio Format**: Unsupported audio file format
- **Low Confidence Score**: Speech recognition confidence below threshold
- **Session Expired**: Mobile session has expired
- **Invalid Token**: JWT token validation failed
- **Service Unavailable**: Backend service not available

### Error Response Codes
- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Authentication failed
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `500`: Internal Server Error - Server error

## Performance Considerations

### Audio Processing
- Limit audio file size to 10MB
- Support common audio formats (WAV, MP3, M4A)
- Implement audio compression for network efficiency
- Cache speech-to-text results

### Response Optimization
- Limit search results to top 10 items for mobile
- Implement pagination for large result sets
- Compress response data when possible
- Use appropriate timeout values

## Testing

### Unit Tests
```bash
pytest tests/unit/mobile_api/
```

### Integration Tests
```bash
pytest tests/integration/mobile_api/
```

### Voice Command Testing
```python
# Test voice command processing
async def test_voice_command():
    request = VoiceCommandRequest(text_input="search documents")
    response = await voice_processor.process_voice_command(request, user_id, session_id)
    assert response.status == "completed"
```

## Future Enhancements

### Planned Features
- **Offline Mode**: Basic functionality when offline
- **Voice Shortcuts**: Custom voice shortcuts for frequent actions
- **Multi-language Support**: Expanded language support
- **Advanced NLP**: Better intent recognition and entity extraction
- **Voice Biometrics**: Voice-based user authentication
- **Real-time Streaming**: Real-time audio processing

### Integration Enhancements
- **Smart Calendar**: AI-powered scheduling suggestions
- **Document Intelligence**: Advanced document analysis
- **Predictive Commands**: Suggest commands based on context
- **Workflow Automation**: Voice-triggered workflow automation

## Support and Documentation

For additional information:
- API documentation: `/docs` endpoint when running
- Integration examples: `examples/` directory
- Troubleshooting: See error handling section
- Performance tuning: See performance considerations

## License

This module is part of the Legal AI System and follows the same licensing terms.