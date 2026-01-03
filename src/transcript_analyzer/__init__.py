"""
Real-Time Court Transcript Streaming and Analysis System

Advanced WebSocket-based system for streaming, processing, and analyzing 
court transcripts in real-time with AI-powered insights and legal analysis.

Features:
- Real-time transcript streaming via WebSocket
- Live speech-to-text transcription
- AI-powered legal analysis and insights
- Speaker identification and diarization
- Key moment detection and highlighting
- Real-time objection and ruling tracking
- Evidence and exhibit tracking
- Automatic summarization and note-taking
- Multi-client streaming support
- Secure authentication and authorization
- Recording and playback capabilities
"""

from .websocket_server import TranscriptWebSocketServer, WebSocketConfig
from .stream_handler import TranscriptStreamHandler, StreamSession, StreamEvent
from .transcript_processor import TranscriptProcessor, ProcessingConfig, TranscriptSegment
from .speech_analyzer import SpeechAnalyzer, SpeakerProfile, AnalysisResult
from .legal_analyzer import LegalAnalyzer, LegalInsight, ObjectionTracker, EvidenceTracker
from .session_manager import SessionManager, CourtSession, Participant
from .auth_middleware import WebSocketAuthMiddleware, AuthConfig
from .models import (
    TranscriptMessage, MessageType, SpeakerType, StreamStatus,
    LegalEvent, EventType, CourtRole, StreamQuality, ConnectionInfo
)

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    "TranscriptWebSocketServer",
    "WebSocketConfig",
    "TranscriptStreamHandler",
    "StreamSession",
    "StreamEvent",
    "TranscriptProcessor",
    "ProcessingConfig",
    "TranscriptSegment",
    "SpeechAnalyzer",
    "SpeakerProfile",
    "AnalysisResult",
    "LegalAnalyzer",
    "LegalInsight",
    "ObjectionTracker",
    "EvidenceTracker",
    "SessionManager",
    "CourtSession",
    "Participant",
    "WebSocketAuthMiddleware",
    "AuthConfig",
    "TranscriptMessage",
    "MessageType",
    "SpeakerType",
    "StreamStatus",
    "LegalEvent",
    "EventType",
    "CourtRole",
    "StreamQuality",
    "ConnectionInfo"
]