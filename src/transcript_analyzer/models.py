"""
Data models for real-time transcript streaming and analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid


class MessageType(Enum):
    """Types of WebSocket messages."""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    AUTH = "auth"
    
    # Transcript streaming
    TRANSCRIPT_CHUNK = "transcript_chunk"
    TRANSCRIPT_SEGMENT = "transcript_segment"
    TRANSCRIPT_FINAL = "transcript_final"
    
    # Audio streaming
    AUDIO_CHUNK = "audio_chunk"
    AUDIO_START = "audio_start"
    AUDIO_END = "audio_end"
    
    # Analysis results
    SPEAKER_CHANGE = "speaker_change"
    LEGAL_INSIGHT = "legal_insight"
    KEY_MOMENT = "key_moment"
    OBJECTION = "objection"
    RULING = "ruling"
    EVIDENCE = "evidence"
    
    # Session management
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_UPDATE = "session_update"
    PARTICIPANT_JOIN = "participant_join"
    PARTICIPANT_LEAVE = "participant_leave"
    
    # Control messages
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    PAUSE_STREAM = "pause_stream"
    RESUME_STREAM = "resume_stream"
    
    # Error handling
    ERROR = "error"
    WARNING = "warning"
    STATUS = "status"


class SpeakerType(Enum):
    """Types of speakers in court proceedings."""
    JUDGE = "judge"
    PLAINTIFF_ATTORNEY = "plaintiff_attorney"
    DEFENDANT_ATTORNEY = "defendant_attorney"
    WITNESS = "witness"
    COURT_REPORTER = "court_reporter"
    BAILIFF = "bailiff"
    JURY_FOREPERSON = "jury_foreperson"
    INTERPRETER = "interpreter"
    EXPERT_WITNESS = "expert_witness"
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    UNKNOWN = "unknown"
    SYSTEM = "system"


class CourtRole(Enum):
    """Roles in court proceedings."""
    JUDGE = "judge"
    ATTORNEY = "attorney"
    WITNESS = "witness"
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    COURT_STAFF = "court_staff"
    JURY = "jury"
    OBSERVER = "observer"
    SYSTEM = "system"


class StreamStatus(Enum):
    """Status of transcript stream."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    PAUSED = "paused"
    RECORDING = "recording"
    BUFFERING = "buffering"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    COMPLETED = "completed"


class StreamQuality(Enum):
    """Quality levels for audio streams."""
    LOW = "low"          # 8kHz, mono
    STANDARD = "standard" # 16kHz, mono
    HIGH = "high"        # 44kHz, mono
    PREMIUM = "premium"  # 48kHz, stereo


class EventType(Enum):
    """Types of legal events detected."""
    OBJECTION = "objection"
    RULING = "ruling"
    EVIDENCE_INTRODUCTION = "evidence_introduction"
    WITNESS_SWORN = "witness_sworn"
    RECESS = "recess"
    SIDEBAR = "sidebar"
    JURY_INSTRUCTION = "jury_instruction"
    OPENING_STATEMENT = "opening_statement"
    CLOSING_ARGUMENT = "closing_argument"
    CROSS_EXAMINATION = "cross_examination"
    REDIRECT = "redirect"
    MOTION = "motion"
    SETTLEMENT_DISCUSSION = "settlement_discussion"
    CONTEMPT = "contempt"
    KEY_TESTIMONY = "key_testimony"


@dataclass
class ConnectionInfo:
    """Information about WebSocket connection."""
    connection_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    
    # Connection timing
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    
    # Connection properties
    is_authenticated: bool = False
    permissions: List[str] = field(default_factory=list)
    subscription_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Quality settings
    stream_quality: StreamQuality = StreamQuality.STANDARD
    buffer_size: int = 1024
    
    # Statistics
    messages_sent: int = 0
    messages_received: int = 0
    bytes_transferred: int = 0
    
    @property
    def connection_duration(self) -> timedelta:
        """Get connection duration."""
        return datetime.utcnow() - self.connected_at
    
    @property
    def is_active(self) -> bool:
        """Check if connection is considered active."""
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() < 30


@dataclass
class TranscriptMessage:
    """WebSocket message for transcript data."""
    message_id: str
    message_type: MessageType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Message payload
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Message metadata
    session_id: Optional[str] = None
    speaker_id: Optional[str] = None
    speaker_type: Optional[SpeakerType] = None
    confidence: Optional[float] = None
    
    # Streaming metadata
    sequence_number: Optional[int] = None
    is_final: bool = False
    
    # Processing flags
    requires_analysis: bool = False
    priority: int = 0  # Higher number = higher priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "session_id": self.session_id,
            "speaker_id": self.speaker_id,
            "speaker_type": self.speaker_type.value if self.speaker_type else None,
            "confidence": self.confidence,
            "sequence_number": self.sequence_number,
            "is_final": self.is_final,
            "requires_analysis": self.requires_analysis,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptMessage':
        """Create message from dictionary."""
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["message_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
            session_id=data.get("session_id"),
            speaker_id=data.get("speaker_id"),
            speaker_type=SpeakerType(data["speaker_type"]) if data.get("speaker_type") else None,
            confidence=data.get("confidence"),
            sequence_number=data.get("sequence_number"),
            is_final=data.get("is_final", False),
            requires_analysis=data.get("requires_analysis", False),
            priority=data.get("priority", 0)
        )


@dataclass
class LegalEvent:
    """Legal event detected in transcript."""
    event_id: str
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Event details
    description: str = ""
    speaker_id: Optional[str] = None
    speaker_type: Optional[SpeakerType] = None
    
    # Event content
    transcript_excerpt: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Analysis results
    confidence: float = 0.0
    significance: int = 1  # 1-10 scale
    legal_implications: List[str] = field(default_factory=list)
    
    # Related data
    related_events: List[str] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)
    case_law_citations: List[str] = field(default_factory=list)
    
    # Metadata
    detected_by: str = "system"
    reviewed: bool = False
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "speaker_id": self.speaker_id,
            "speaker_type": self.speaker_type.value if self.speaker_type else None,
            "transcript_excerpt": self.transcript_excerpt,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "confidence": self.confidence,
            "significance": self.significance,
            "legal_implications": self.legal_implications,
            "related_events": self.related_events,
            "evidence_references": self.evidence_references,
            "case_law_citations": self.case_law_citations,
            "detected_by": self.detected_by,
            "reviewed": self.reviewed,
            "tags": self.tags,
            "notes": self.notes
        }


def generate_message_id() -> str:
    """Generate unique message ID."""
    return f"msg_{uuid.uuid4().hex[:12]}"


def generate_connection_id() -> str:
    """Generate unique connection ID."""
    return f"conn_{uuid.uuid4().hex[:8]}"


def generate_session_id() -> str:
    """Generate unique session ID."""
    return f"session_{uuid.uuid4().hex[:8]}"


def generate_event_id() -> str:
    """Generate unique event ID."""
    return f"event_{uuid.uuid4().hex[:8]}"


def create_heartbeat_message(connection_id: str) -> TranscriptMessage:
    """Create heartbeat message."""
    return TranscriptMessage(
        message_id=generate_message_id(),
        message_type=MessageType.HEARTBEAT,
        data={"connection_id": connection_id, "status": "alive"}
    )


def create_error_message(error_code: str, error_message: str, details: Optional[Dict] = None) -> TranscriptMessage:
    """Create error message."""
    return TranscriptMessage(
        message_id=generate_message_id(),
        message_type=MessageType.ERROR,
        data={
            "error_code": error_code,
            "error_message": error_message,
            "details": details or {}
        },
        priority=10  # High priority for errors
    )


def create_status_message(status: StreamStatus, details: Optional[Dict] = None) -> TranscriptMessage:
    """Create status update message."""
    return TranscriptMessage(
        message_id=generate_message_id(),
        message_type=MessageType.STATUS,
        data={
            "status": status.value,
            "details": details or {}
        }
    )


def create_transcript_message(text: str,
                            speaker_id: Optional[str] = None,
                            speaker_type: Optional[SpeakerType] = None,
                            is_final: bool = False,
                            confidence: Optional[float] = None,
                            session_id: Optional[str] = None) -> TranscriptMessage:
    """Create transcript chunk message."""
    return TranscriptMessage(
        message_id=generate_message_id(),
        message_type=MessageType.TRANSCRIPT_CHUNK if not is_final else MessageType.TRANSCRIPT_FINAL,
        data={"text": text},
        speaker_id=speaker_id,
        speaker_type=speaker_type,
        confidence=confidence,
        session_id=session_id,
        is_final=is_final,
        requires_analysis=is_final
    )


def create_legal_event_message(event: LegalEvent, session_id: Optional[str] = None) -> TranscriptMessage:
    """Create legal event message."""
    message_type = MessageType.LEGAL_INSIGHT
    
    # Map specific event types to message types
    if event.event_type == EventType.OBJECTION:
        message_type = MessageType.OBJECTION
    elif event.event_type == EventType.RULING:
        message_type = MessageType.RULING
    elif event.event_type == EventType.EVIDENCE_INTRODUCTION:
        message_type = MessageType.EVIDENCE
    elif event.event_type in [EventType.KEY_TESTIMONY, EventType.OPENING_STATEMENT, EventType.CLOSING_ARGUMENT]:
        message_type = MessageType.KEY_MOMENT
    
    return TranscriptMessage(
        message_id=generate_message_id(),
        message_type=message_type,
        data=event.to_dict(),
        session_id=session_id,
        speaker_id=event.speaker_id,
        speaker_type=event.speaker_type,
        confidence=event.confidence,
        priority=event.significance
    )


def create_speaker_change_message(new_speaker_id: str,
                                speaker_type: SpeakerType,
                                session_id: Optional[str] = None,
                                confidence: Optional[float] = None) -> TranscriptMessage:
    """Create speaker change notification message."""
    return TranscriptMessage(
        message_id=generate_message_id(),
        message_type=MessageType.SPEAKER_CHANGE,
        data={
            "new_speaker_id": new_speaker_id,
            "speaker_type": speaker_type.value
        },
        session_id=session_id,
        speaker_id=new_speaker_id,
        speaker_type=speaker_type,
        confidence=confidence
    )


def create_session_message(message_type: MessageType,
                         session_id: str,
                         session_data: Dict[str, Any]) -> TranscriptMessage:
    """Create session management message."""
    return TranscriptMessage(
        message_id=generate_message_id(),
        message_type=message_type,
        data=session_data,
        session_id=session_id,
        priority=5  # Medium priority for session messages
    )


class MessageValidator:
    """Validator for WebSocket messages."""
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate WebSocket message structure.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Required fields
        if "message_type" not in message:
            errors.append("Missing required field: message_type")
        elif message["message_type"] not in [mt.value for mt in MessageType]:
            errors.append(f"Invalid message_type: {message['message_type']}")
        
        if "message_id" not in message:
            errors.append("Missing required field: message_id")
        
        if "timestamp" not in message:
            errors.append("Missing required field: timestamp")
        else:
            try:
                datetime.fromisoformat(message["timestamp"])
            except ValueError:
                errors.append("Invalid timestamp format")
        
        # Validate data field
        if "data" in message and not isinstance(message["data"], dict):
            errors.append("Data field must be a dictionary")
        
        # Validate speaker_type if present
        if "speaker_type" in message and message["speaker_type"]:
            if message["speaker_type"] not in [st.value for st in SpeakerType]:
                errors.append(f"Invalid speaker_type: {message['speaker_type']}")
        
        # Validate confidence if present
        if "confidence" in message and message["confidence"] is not None:
            try:
                confidence = float(message["confidence"])
                if not 0.0 <= confidence <= 1.0:
                    errors.append("Confidence must be between 0.0 and 1.0")
            except (ValueError, TypeError):
                errors.append("Confidence must be a number")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_auth_message(message: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate authentication message."""
        errors = []
        
        if message.get("message_type") != MessageType.AUTH.value:
            errors.append("Message type must be 'auth' for authentication")
        
        data = message.get("data", {})
        if "token" not in data and "credentials" not in data:
            errors.append("Authentication data must contain 'token' or 'credentials'")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_audio_message(message: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate audio chunk message."""
        errors = []
        
        if message.get("message_type") not in [MessageType.AUDIO_CHUNK.value, 
                                              MessageType.AUDIO_START.value,
                                              MessageType.AUDIO_END.value]:
            errors.append("Invalid message type for audio message")
        
        data = message.get("data", {})
        
        if message.get("message_type") == MessageType.AUDIO_CHUNK.value:
            if "audio_data" not in data:
                errors.append("Audio chunk must contain 'audio_data'")
            if "format" not in data:
                errors.append("Audio chunk must contain 'format' specification")
        
        return len(errors) == 0, errors


def get_message_priority(message_type: MessageType) -> int:
    """Get default priority for message type."""
    priority_map = {
        MessageType.ERROR: 10,
        MessageType.AUTH: 9,
        MessageType.SESSION_START: 8,
        MessageType.SESSION_END: 8,
        MessageType.OBJECTION: 7,
        MessageType.RULING: 7,
        MessageType.KEY_MOMENT: 6,
        MessageType.LEGAL_INSIGHT: 5,
        MessageType.EVIDENCE: 5,
        MessageType.SPEAKER_CHANGE: 4,
        MessageType.TRANSCRIPT_FINAL: 3,
        MessageType.TRANSCRIPT_CHUNK: 2,
        MessageType.STATUS: 2,
        MessageType.HEARTBEAT: 1
    }
    
    return priority_map.get(message_type, 2)


def is_control_message(message_type: MessageType) -> bool:
    """Check if message type is a control message."""
    control_types = {
        MessageType.CONNECT,
        MessageType.DISCONNECT,
        MessageType.AUTH,
        MessageType.START_RECORDING,
        MessageType.STOP_RECORDING,
        MessageType.PAUSE_STREAM,
        MessageType.RESUME_STREAM,
        MessageType.HEARTBEAT
    }
    
    return message_type in control_types


def is_analysis_message(message_type: MessageType) -> bool:
    """Check if message type contains analysis results."""
    analysis_types = {
        MessageType.LEGAL_INSIGHT,
        MessageType.KEY_MOMENT,
        MessageType.OBJECTION,
        MessageType.RULING,
        MessageType.EVIDENCE,
        MessageType.SPEAKER_CHANGE
    }
    
    return message_type in analysis_types