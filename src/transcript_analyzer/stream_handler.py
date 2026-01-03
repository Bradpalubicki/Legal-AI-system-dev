"""
Stream handler for processing real-time transcript data.

Handles incoming audio and text streams, manages buffering, and coordinates
with analysis engines for real-time processing and insights.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
import base64

from .models import (
    TranscriptMessage, MessageType, SpeakerType, StreamStatus, LegalEvent,
    generate_message_id, create_transcript_message, create_speaker_change_message,
    create_legal_event_message, create_status_message
)
from .websocket_server import TranscriptWebSocketServer


@dataclass
class StreamEvent:
    """Event in the transcript stream."""
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False


@dataclass
class StreamBuffer:
    """Buffer for managing stream data."""
    buffer_id: str
    max_size: int = 1000
    retention_time: int = 300  # seconds
    
    # Buffer storage
    text_buffer: deque = field(default_factory=deque)
    audio_buffer: deque = field(default_factory=deque)
    events_buffer: deque = field(default_factory=deque)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def add_text(self, text: str, speaker_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        """Add text to buffer."""
        entry = {
            "text": text,
            "speaker_id": speaker_id,
            "timestamp": timestamp or datetime.utcnow(),
            "sequence": len(self.text_buffer)
        }
        
        self.text_buffer.append(entry)
        
        # Maintain buffer size
        while len(self.text_buffer) > self.max_size:
            self.text_buffer.popleft()
        
        self.last_updated = datetime.utcnow()
    
    def add_audio(self, audio_data: bytes, format_info: Dict[str, Any]):
        """Add audio chunk to buffer."""
        entry = {
            "data": audio_data,
            "format": format_info,
            "timestamp": datetime.utcnow(),
            "size": len(audio_data)
        }
        
        self.audio_buffer.append(entry)
        
        # Maintain buffer size
        while len(self.audio_buffer) > self.max_size:
            self.audio_buffer.popleft()
        
        self.last_updated = datetime.utcnow()
    
    def add_event(self, event: StreamEvent):
        """Add event to buffer."""
        self.events_buffer.append(event)
        
        # Maintain buffer size
        while len(self.events_buffer) > self.max_size:
            self.events_buffer.popleft()
        
        self.last_updated = datetime.utcnow()
    
    def get_recent_text(self, seconds: int = 30) -> List[Dict[str, Any]]:
        """Get recent text entries."""
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        return [
            entry for entry in self.text_buffer
            if entry["timestamp"] >= cutoff
        ]
    
    def get_context_window(self, window_size: int = 10) -> List[Dict[str, Any]]:
        """Get recent context window of text entries."""
        return list(self.text_buffer)[-window_size:]
    
    def clear_old_entries(self):
        """Clear entries older than retention time."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.retention_time)
        
        # Clear old text entries
        while (self.text_buffer and 
               self.text_buffer[0]["timestamp"] < cutoff):
            self.text_buffer.popleft()
        
        # Clear old audio entries
        while (self.audio_buffer and 
               self.audio_buffer[0]["timestamp"] < cutoff):
            self.audio_buffer.popleft()
        
        # Clear old events
        while (self.events_buffer and 
               self.events_buffer[0].timestamp < cutoff):
            self.events_buffer.popleft()


@dataclass
class StreamSession:
    """Active streaming session."""
    session_id: str
    case_id: Optional[str]
    court_room: Optional[str]
    
    # Session state
    status: StreamStatus = StreamStatus.CONNECTING
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # Participants
    participants: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active_speaker: Optional[str] = None
    
    # Stream configuration
    audio_enabled: bool = True
    auto_analysis: bool = True
    recording_enabled: bool = False
    
    # Buffers and processing
    buffer: StreamBuffer = field(default_factory=lambda: StreamBuffer(buffer_id=generate_message_id()))
    
    # Statistics
    total_messages: int = 0
    total_audio_chunks: int = 0
    total_text_segments: int = 0
    total_events: int = 0
    
    # Quality metrics
    avg_confidence: float = 0.0
    speech_rate: float = 0.0  # words per minute
    audio_quality: str = "unknown"
    
    def update_speaker(self, speaker_id: str, speaker_type: Optional[SpeakerType] = None):
        """Update active speaker."""
        if self.active_speaker != speaker_id:
            self.active_speaker = speaker_id
            
            # Update participant info
            if speaker_id not in self.participants:
                self.participants[speaker_id] = {
                    "speaker_id": speaker_id,
                    "speaker_type": speaker_type.value if speaker_type else None,
                    "first_seen": datetime.utcnow(),
                    "message_count": 0,
                    "total_words": 0
                }
    
    def add_participant_message(self, speaker_id: str, word_count: int = 0):
        """Track participant messaging statistics."""
        if speaker_id in self.participants:
            self.participants[speaker_id]["message_count"] += 1
            self.participants[speaker_id]["total_words"] += word_count
    
    @property
    def duration(self) -> timedelta:
        """Get session duration."""
        end_time = self.ended_at or datetime.utcnow()
        return end_time - self.started_at
    
    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status in [StreamStatus.CONNECTED, StreamStatus.STREAMING, StreamStatus.RECORDING]


class TranscriptStreamHandler:
    """Handler for real-time transcript streaming."""
    
    def __init__(self, websocket_server: TranscriptWebSocketServer):
        self.websocket_server = websocket_server
        self.active_sessions: Dict[str, StreamSession] = {}
        
        # Processing components (to be injected)
        self.transcript_processor = None
        self.speech_analyzer = None
        self.legal_analyzer = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Configuration
        self.max_concurrent_sessions = 50
        self.buffer_cleanup_interval = 300  # seconds
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.is_running = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Register WebSocket handlers
        self._register_websocket_handlers()
    
    def _register_websocket_handlers(self):
        """Register handlers for WebSocket messages."""
        self.websocket_server.register_handler(MessageType.SESSION_START, self._handle_session_start)
        self.websocket_server.register_handler(MessageType.SESSION_END, self._handle_session_end)
        self.websocket_server.register_handler(MessageType.AUDIO_CHUNK, self._handle_audio_chunk)
        self.websocket_server.register_handler(MessageType.AUDIO_START, self._handle_audio_start)
        self.websocket_server.register_handler(MessageType.AUDIO_END, self._handle_audio_end)
        self.websocket_server.register_handler(MessageType.TRANSCRIPT_CHUNK, self._handle_transcript_chunk)
        self.websocket_server.register_handler(MessageType.START_RECORDING, self._handle_start_recording)
        self.websocket_server.register_handler(MessageType.STOP_RECORDING, self._handle_stop_recording)
        self.websocket_server.register_handler(MessageType.PAUSE_STREAM, self._handle_pause_stream)
        self.websocket_server.register_handler(MessageType.RESUME_STREAM, self._handle_resume_stream)
    
    async def start(self):
        """Start the stream handler."""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Stream handler started")
        
        # Start background tasks
        cleanup_task = asyncio.create_task(self._cleanup_task())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
    
    async def stop(self):
        """Stop the stream handler."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("Stopping stream handler")
        
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.end_session(session_id)
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
    
    async def create_session(self, 
                           session_id: str,
                           case_id: Optional[str] = None,
                           court_room: Optional[str] = None,
                           config: Optional[Dict[str, Any]] = None) -> StreamSession:
        """Create a new streaming session."""
        if len(self.active_sessions) >= self.max_concurrent_sessions:
            raise ValueError("Maximum concurrent sessions reached")
        
        if session_id in self.active_sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        config = config or {}
        
        session = StreamSession(
            session_id=session_id,
            case_id=case_id,
            court_room=court_room,
            audio_enabled=config.get("audio_enabled", True),
            auto_analysis=config.get("auto_analysis", True),
            recording_enabled=config.get("recording_enabled", False)
        )
        
        self.active_sessions[session_id] = session
        
        self.logger.info(f"Created streaming session {session_id}")
        
        # Notify session start
        await self._emit_event("session_created", session_id, {"session": session})
        
        return session
    
    async def end_session(self, session_id: str) -> bool:
        """End a streaming session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.status = StreamStatus.COMPLETED
        session.ended_at = datetime.utcnow()
        
        # Clean up session resources
        await self._cleanup_session(session_id)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        self.logger.info(f"Ended streaming session {session_id}")
        
        # Notify session end
        await self._emit_event("session_ended", session_id, {"session": session})
        
        return True
    
    async def process_audio_stream(self, 
                                 session_id: str,
                                 audio_data: bytes,
                                 format_info: Dict[str, Any]) -> Optional[str]:
        """Process incoming audio stream data."""
        session = self.active_sessions.get(session_id)
        if not session or not session.audio_enabled:
            return None
        
        # Add to buffer
        session.buffer.add_audio(audio_data, format_info)
        session.total_audio_chunks += 1
        
        # Process with speech analyzer if available
        if self.speech_analyzer:
            try:
                # Convert audio to text
                transcription_result = await self.speech_analyzer.transcribe_audio(
                    audio_data, format_info
                )
                
                if transcription_result and transcription_result.text:
                    # Process transcription
                    await self.process_transcript_chunk(
                        session_id,
                        transcription_result.text,
                        transcription_result.speaker_id,
                        transcription_result.speaker_type,
                        transcription_result.confidence,
                        transcription_result.is_final
                    )
                    
                    return transcription_result.text
                    
            except Exception as e:
                self.logger.error(f"Error processing audio for session {session_id}: {e}")
        
        return None
    
    async def process_transcript_chunk(self,
                                     session_id: str,
                                     text: str,
                                     speaker_id: Optional[str] = None,
                                     speaker_type: Optional[SpeakerType] = None,
                                     confidence: Optional[float] = None,
                                     is_final: bool = False) -> TranscriptMessage:
        """Process incoming transcript text."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update session state
        session.total_text_segments += 1
        if confidence:
            # Update running average confidence
            session.avg_confidence = (
                (session.avg_confidence * (session.total_text_segments - 1) + confidence) /
                session.total_text_segments
            )
        
        # Handle speaker changes
        if speaker_id and session.active_speaker != speaker_id:
            session.update_speaker(speaker_id, speaker_type)
            
            # Broadcast speaker change
            speaker_change_msg = create_speaker_change_message(
                speaker_id, speaker_type or SpeakerType.UNKNOWN, session_id, confidence
            )
            await self.websocket_server.broadcast_message(speaker_change_msg, session_id)
        
        # Add to buffer
        session.buffer.add_text(text, speaker_id)
        
        # Track participant activity
        if speaker_id:
            word_count = len(text.split())
            session.add_participant_message(speaker_id, word_count)
        
        # Create transcript message
        transcript_msg = create_transcript_message(
            text, speaker_id, speaker_type, is_final, confidence, session_id
        )
        
        # Broadcast to session subscribers
        await self.websocket_server.broadcast_message(transcript_msg, session_id)
        
        # Process with analyzers if final and auto-analysis enabled
        if is_final and session.auto_analysis:
            await self._analyze_transcript_segment(session_id, text, speaker_id, speaker_type)
        
        self.logger.debug(f"Processed transcript chunk for session {session_id}: {text[:50]}...")
        
        return transcript_msg
    
    async def _analyze_transcript_segment(self,
                                        session_id: str,
                                        text: str,
                                        speaker_id: Optional[str],
                                        speaker_type: Optional[SpeakerType]):
        """Analyze transcript segment for legal insights."""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        try:
            # Get context for analysis
            context = session.buffer.get_context_window(20)
            context_text = " ".join([entry["text"] for entry in context])
            
            # Legal analysis
            if self.legal_analyzer:
                insights = await self.legal_analyzer.analyze_segment(
                    text, context_text, speaker_id, speaker_type
                )
                
                # Process insights
                for insight in insights:
                    if isinstance(insight, LegalEvent):
                        # Add to session buffer
                        event = StreamEvent(
                            event_id=insight.event_id,
                            event_type=insight.event_type.value,
                            timestamp=insight.timestamp,
                            data=insight.to_dict()
                        )
                        session.buffer.add_event(event)
                        session.total_events += 1
                        
                        # Broadcast legal event
                        event_msg = create_legal_event_message(insight, session_id)
                        await self.websocket_server.broadcast_message(event_msg, session_id)
                        
                        # Emit internal event
                        await self._emit_event("legal_insight", session_id, {"insight": insight})
            
            # Additional processing with transcript processor
            if self.transcript_processor:
                processed_segment = await self.transcript_processor.process_segment(
                    text, context_text, session_id
                )
                
                if processed_segment and processed_segment.events:
                    for event in processed_segment.events:
                        session_event = StreamEvent(
                            event_id=generate_message_id(),
                            event_type=event.get("type", "unknown"),
                            timestamp=datetime.utcnow(),
                            data=event
                        )
                        session.buffer.add_event(session_event)
        
        except Exception as e:
            self.logger.error(f"Error analyzing transcript segment: {e}")
    
    def get_session(self, session_id: str) -> Optional[StreamSession]:
        """Get active session by ID."""
        return self.active_sessions.get(session_id)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "duration_seconds": session.duration.total_seconds(),
            "participants": len(session.participants),
            "active_speaker": session.active_speaker,
            "total_messages": session.total_messages,
            "total_audio_chunks": session.total_audio_chunks,
            "total_text_segments": session.total_text_segments,
            "total_events": session.total_events,
            "avg_confidence": session.avg_confidence,
            "audio_quality": session.audio_quality,
            "recording_enabled": session.recording_enabled,
            "buffer_size": {
                "text": len(session.buffer.text_buffer),
                "audio": len(session.buffer.audio_buffer),
                "events": len(session.buffer.events_buffer)
            }
        }
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register handler for internal events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, session_id: str, data: Dict[str, Any]):
        """Emit internal event to handlers."""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                await handler(session_id, data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    # WebSocket message handlers
    async def _handle_session_start(self, connection_id: str, message: TranscriptMessage):
        """Handle session start message."""
        data = message.data
        session_id = data.get("session_id", generate_message_id())
        
        try:
            session = await self.create_session(
                session_id,
                data.get("case_id"),
                data.get("court_room"),
                data.get("config", {})
            )
            
            # Subscribe connection to session
            await self.websocket_server.subscribe_to_session(connection_id, session_id)
            
            # Update session status
            session.status = StreamStatus.CONNECTED
            
            # Send confirmation
            response_msg = create_status_message(StreamStatus.CONNECTED, {
                "session_id": session_id,
                "message": "Session started successfully"
            })
            await self.websocket_server.send_message_to_connection(connection_id, response_msg)
            
        except Exception as e:
            error_msg = create_error_message("SESSION_START_FAILED", str(e))
            await self.websocket_server.send_message_to_connection(connection_id, error_msg)
    
    async def _handle_session_end(self, connection_id: str, message: TranscriptMessage):
        """Handle session end message."""
        session_id = message.session_id or message.data.get("session_id")
        
        if session_id:
            success = await self.end_session(session_id)
            
            if success:
                # Unsubscribe connection
                await self.websocket_server.unsubscribe_from_session(connection_id, session_id)
                
                response_msg = create_status_message(StreamStatus.COMPLETED, {
                    "session_id": session_id,
                    "message": "Session ended successfully"
                })
            else:
                response_msg = create_error_message("SESSION_NOT_FOUND", f"Session {session_id} not found")
            
            await self.websocket_server.send_message_to_connection(connection_id, response_msg)
    
    async def _handle_audio_chunk(self, connection_id: str, message: TranscriptMessage):
        """Handle audio chunk message."""
        session_id = message.session_id
        if not session_id:
            return
        
        data = message.data
        audio_data_b64 = data.get("audio_data")
        format_info = data.get("format", {})
        
        if audio_data_b64:
            try:
                audio_data = base64.b64decode(audio_data_b64)
                await self.process_audio_stream(session_id, audio_data, format_info)
            except Exception as e:
                self.logger.error(f"Error processing audio chunk: {e}")
    
    async def _handle_audio_start(self, connection_id: str, message: TranscriptMessage):
        """Handle audio stream start."""
        session_id = message.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = StreamStatus.STREAMING
            
            # Broadcast status update
            status_msg = create_status_message(StreamStatus.STREAMING, {
                "session_id": session_id,
                "audio_streaming": True
            })
            await self.websocket_server.broadcast_message(status_msg, session_id)
    
    async def _handle_audio_end(self, connection_id: str, message: TranscriptMessage):
        """Handle audio stream end."""
        session_id = message.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = StreamStatus.CONNECTED
            
            # Broadcast status update
            status_msg = create_status_message(StreamStatus.CONNECTED, {
                "session_id": session_id,
                "audio_streaming": False
            })
            await self.websocket_server.broadcast_message(status_msg, session_id)
    
    async def _handle_transcript_chunk(self, connection_id: str, message: TranscriptMessage):
        """Handle transcript chunk message."""
        session_id = message.session_id
        if not session_id:
            return
        
        data = message.data
        text = data.get("text", "")
        
        if text:
            await self.process_transcript_chunk(
                session_id,
                text,
                message.speaker_id,
                message.speaker_type,
                message.confidence,
                message.is_final
            )
    
    async def _handle_start_recording(self, connection_id: str, message: TranscriptMessage):
        """Handle start recording message."""
        session_id = message.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.recording_enabled = True
            session.status = StreamStatus.RECORDING
            
            # Broadcast recording started
            status_msg = create_status_message(StreamStatus.RECORDING, {
                "session_id": session_id,
                "recording": True
            })
            await self.websocket_server.broadcast_message(status_msg, session_id)
    
    async def _handle_stop_recording(self, connection_id: str, message: TranscriptMessage):
        """Handle stop recording message."""
        session_id = message.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.recording_enabled = False
            session.status = StreamStatus.STREAMING
            
            # Broadcast recording stopped
            status_msg = create_status_message(StreamStatus.STREAMING, {
                "session_id": session_id,
                "recording": False
            })
            await self.websocket_server.broadcast_message(status_msg, session_id)
    
    async def _handle_pause_stream(self, connection_id: str, message: TranscriptMessage):
        """Handle pause stream message."""
        session_id = message.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = StreamStatus.PAUSED
            
            status_msg = create_status_message(StreamStatus.PAUSED, {
                "session_id": session_id
            })
            await self.websocket_server.broadcast_message(status_msg, session_id)
    
    async def _handle_resume_stream(self, connection_id: str, message: TranscriptMessage):
        """Handle resume stream message."""
        session_id = message.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = StreamStatus.STREAMING
            
            status_msg = create_status_message(StreamStatus.STREAMING, {
                "session_id": session_id
            })
            await self.websocket_server.broadcast_message(status_msg, session_id)
    
    async def _cleanup_session(self, session_id: str):
        """Clean up session resources."""
        # This would handle cleanup of temporary files, database connections, etc.
        pass
    
    async def _cleanup_task(self):
        """Background task for cleaning up stale data."""
        while self.is_running:
            try:
                # Clean up session buffers
                for session in self.active_sessions.values():
                    session.buffer.clear_old_entries()
                
                # Remove inactive sessions
                inactive_sessions = []
                for session_id, session in self.active_sessions.items():
                    if not session.is_active and session.duration.total_seconds() > 3600:  # 1 hour
                        inactive_sessions.append(session_id)
                
                for session_id in inactive_sessions:
                    await self.end_session(session_id)
                    self.logger.info(f"Cleaned up inactive session {session_id}")
                
                await asyncio.sleep(self.buffer_cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(30)