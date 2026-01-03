"""
Session management for court transcript streaming.

Manages court sessions, participants, and coordination between different
components of the transcript streaming system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .models import (
    SpeakerType, CourtRole, StreamStatus, generate_session_id,
    create_session_message, MessageType
)


class SessionType(Enum):
    """Types of court sessions."""
    HEARING = "hearing"
    TRIAL = "trial"
    DEPOSITION = "deposition"
    MEDIATION = "mediation"
    ARBITRATION = "arbitration"
    CONFERENCE = "conference"
    MOTION_HEARING = "motion_hearing"
    SETTLEMENT_CONFERENCE = "settlement_conference"
    STATUS_CONFERENCE = "status_conference"
    OTHER = "other"


class ParticipantStatus(Enum):
    """Status of session participants."""
    INVITED = "invited"
    CONNECTED = "connected"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONNECTED = "disconnected"
    REMOVED = "removed"


@dataclass
class Participant:
    """Session participant information."""
    participant_id: str
    user_id: Optional[str]
    name: str
    role: CourtRole
    speaker_type: SpeakerType
    
    # Connection info
    connection_id: Optional[str] = None
    status: ParticipantStatus = ParticipantStatus.INVITED
    joined_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Permissions
    can_speak: bool = True
    can_record: bool = False
    can_moderate: bool = False
    
    # Activity tracking
    messages_sent: int = 0
    words_spoken: int = 0
    speaking_time: float = 0.0  # seconds
    
    # Contact info
    email: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        if self.status == ParticipantStatus.CONNECTED:
            self.status = ParticipantStatus.ACTIVE
    
    def add_speaking_activity(self, words: int, duration: float):
        """Add speaking activity metrics."""
        self.messages_sent += 1
        self.words_spoken += words
        self.speaking_time += duration
        self.update_activity()
    
    @property
    def is_active(self) -> bool:
        """Check if participant is currently active."""
        if not self.last_activity:
            return False
        
        # Consider active if activity within last 5 minutes
        return (datetime.utcnow() - self.last_activity) < timedelta(minutes=5)


@dataclass
class CourtSession:
    """Court session information and state."""
    session_id: str
    case_id: Optional[str]
    case_number: Optional[str]
    session_type: SessionType
    
    # Session details
    title: str
    description: str = ""
    court_room: Optional[str] = None
    judge_id: Optional[str] = None
    
    # Scheduling
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    
    # Status
    status: StreamStatus = StreamStatus.CONNECTING
    is_recording: bool = False
    is_public: bool = False
    
    # Participants
    participants: Dict[str, Participant] = field(default_factory=dict)
    moderators: Set[str] = field(default_factory=set)
    
    # Session configuration
    max_participants: int = 50
    require_approval: bool = True
    allow_recording: bool = True
    auto_transcription: bool = True
    
    # Quality and monitoring
    connection_quality: Dict[str, float] = field(default_factory=dict)
    audio_quality: Dict[str, float] = field(default_factory=dict)
    
    # Statistics
    total_messages: int = 0
    total_participants: int = 0
    peak_participants: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_participant(self, participant: Participant) -> bool:
        """Add participant to session."""
        if len(self.participants) >= self.max_participants:
            return False
        
        self.participants[participant.participant_id] = participant
        self.total_participants += 1
        self.peak_participants = max(self.peak_participants, len(self.participants))
        
        return True
    
    def remove_participant(self, participant_id: str) -> bool:
        """Remove participant from session."""
        if participant_id in self.participants:
            participant = self.participants[participant_id]
            participant.status = ParticipantStatus.REMOVED
            del self.participants[participant_id]
            return True
        return False
    
    def get_active_participants(self) -> List[Participant]:
        """Get list of currently active participants."""
        return [
            p for p in self.participants.values()
            if p.status in [ParticipantStatus.ACTIVE, ParticipantStatus.CONNECTED]
        ]
    
    def get_participants_by_role(self, role: CourtRole) -> List[Participant]:
        """Get participants by their court role."""
        return [p for p in self.participants.values() if p.role == role]
    
    def get_speaking_participants(self) -> List[Participant]:
        """Get participants who can speak."""
        return [p for p in self.participants.values() if p.can_speak]
    
    def update_connection_quality(self, connection_id: str, quality: float):
        """Update connection quality for participant."""
        self.connection_quality[connection_id] = quality
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get session duration."""
        if self.actual_start:
            end_time = self.actual_end or datetime.utcnow()
            return end_time - self.actual_start
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status in [
            StreamStatus.CONNECTED,
            StreamStatus.STREAMING,
            StreamStatus.RECORDING
        ]
    
    @property
    def active_participant_count(self) -> int:
        """Get count of active participants."""
        return len(self.get_active_participants())


class SessionManager:
    """Manager for court transcript streaming sessions."""
    
    def __init__(self):
        self.active_sessions: Dict[str, CourtSession] = {}
        self.participant_sessions: Dict[str, str] = {}  # participant_id -> session_id
        self.connection_participants: Dict[str, str] = {}  # connection_id -> participant_id
        
        # Event handlers
        self.event_handlers: Dict[str, List[callable]] = {}
        
        # Configuration
        self.max_sessions = 100
        self.session_timeout = timedelta(hours=8)
        self.cleanup_interval = 300  # seconds
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.is_running = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the session manager."""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Session manager started")
        
        # Start background tasks
        cleanup_task = asyncio.create_task(self._cleanup_task())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
    
    async def stop(self):
        """Stop the session manager."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("Stopping session manager")
        
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
                           case_id: Optional[str] = None,
                           case_number: Optional[str] = None,
                           session_type: SessionType = SessionType.HEARING,
                           title: str = "Court Session",
                           description: str = "",
                           judge_id: Optional[str] = None,
                           court_room: Optional[str] = None,
                           created_by: Optional[str] = None,
                           config: Optional[Dict[str, Any]] = None) -> CourtSession:
        """Create a new court session."""
        if len(self.active_sessions) >= self.max_sessions:
            raise ValueError("Maximum number of sessions reached")
        
        config = config or {}
        session_id = generate_session_id()
        
        session = CourtSession(
            session_id=session_id,
            case_id=case_id,
            case_number=case_number,
            session_type=session_type,
            title=title,
            description=description,
            judge_id=judge_id,
            court_room=court_room,
            created_by=created_by,
            max_participants=config.get("max_participants", 50),
            require_approval=config.get("require_approval", True),
            allow_recording=config.get("allow_recording", True),
            auto_transcription=config.get("auto_transcription", True),
            is_public=config.get("is_public", False)
        )
        
        # Add creator as moderator if specified
        if created_by:
            session.moderators.add(created_by)
        
        self.active_sessions[session_id] = session
        
        self.logger.info(f"Created session {session_id}: {title}")
        
        # Emit event
        await self._emit_event("session_created", session_id, {"session": session})
        
        return session
    
    async def end_session(self, session_id: str) -> bool:
        """End a court session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        # Update session status
        session.status = StreamStatus.COMPLETED
        session.actual_end = datetime.utcnow()
        
        # Disconnect all participants
        for participant in list(session.participants.values()):
            await self.remove_participant(session_id, participant.participant_id)
        
        # Clean up mappings
        participants_to_remove = [
            pid for pid, sid in self.participant_sessions.items()
            if sid == session_id
        ]
        for pid in participants_to_remove:
            del self.participant_sessions[pid]
        
        connections_to_remove = [
            cid for cid, pid in self.connection_participants.items()
            if pid in participants_to_remove
        ]
        for cid in connections_to_remove:
            del self.connection_participants[cid]
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        self.logger.info(f"Ended session {session_id}")
        
        # Emit event
        await self._emit_event("session_ended", session_id, {"session": session})
        
        return True
    
    async def add_participant(self,
                            session_id: str,
                            user_id: Optional[str],
                            name: str,
                            role: CourtRole,
                            speaker_type: SpeakerType = SpeakerType.UNKNOWN,
                            connection_id: Optional[str] = None,
                            permissions: Optional[Dict[str, bool]] = None) -> Optional[Participant]:
        """Add participant to session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        participant_id = f"participant_{len(session.participants) + 1}"
        permissions = permissions or {}
        
        participant = Participant(
            participant_id=participant_id,
            user_id=user_id,
            name=name,
            role=role,
            speaker_type=speaker_type,
            connection_id=connection_id,
            can_speak=permissions.get("can_speak", True),
            can_record=permissions.get("can_record", False),
            can_moderate=permissions.get("can_moderate", False),
            joined_at=datetime.utcnow()
        )
        
        if not session.add_participant(participant):
            return None
        
        # Update mappings
        self.participant_sessions[participant_id] = session_id
        if connection_id:
            self.connection_participants[connection_id] = participant_id
            participant.status = ParticipantStatus.CONNECTED
        
        self.logger.info(f"Added participant {name} ({role.value}) to session {session_id}")
        
        # Emit event
        await self._emit_event("participant_joined", session_id, {
            "participant": participant,
            "session": session
        })
        
        return participant
    
    async def remove_participant(self, session_id: str, participant_id: str) -> bool:
        """Remove participant from session."""
        session = self.active_sessions.get(session_id)
        if not session or participant_id not in session.participants:
            return False
        
        participant = session.participants[participant_id]
        
        # Update status and remove
        participant.status = ParticipantStatus.DISCONNECTED
        session.remove_participant(participant_id)
        
        # Clean up mappings
        if participant_id in self.participant_sessions:
            del self.participant_sessions[participant_id]
        
        if participant.connection_id and participant.connection_id in self.connection_participants:
            del self.connection_participants[participant.connection_id]
        
        self.logger.info(f"Removed participant {participant.name} from session {session_id}")
        
        # Emit event
        await self._emit_event("participant_left", session_id, {
            "participant": participant,
            "session": session
        })
        
        return True
    
    async def update_participant_connection(self,
                                          session_id: str,
                                          participant_id: str,
                                          connection_id: Optional[str]) -> bool:
        """Update participant connection information."""
        session = self.active_sessions.get(session_id)
        if not session or participant_id not in session.participants:
            return False
        
        participant = session.participants[participant_id]
        old_connection = participant.connection_id
        
        # Update connection mapping
        if old_connection and old_connection in self.connection_participants:
            del self.connection_participants[old_connection]
        
        participant.connection_id = connection_id
        if connection_id:
            self.connection_participants[connection_id] = participant_id
            participant.status = ParticipantStatus.CONNECTED
        else:
            participant.status = ParticipantStatus.DISCONNECTED
        
        return True
    
    async def update_participant_activity(self,
                                        session_id: str,
                                        participant_id: str,
                                        activity_data: Dict[str, Any]):
        """Update participant activity metrics."""
        session = self.active_sessions.get(session_id)
        if not session or participant_id not in session.participants:
            return
        
        participant = session.participants[participant_id]
        
        # Update activity metrics
        if "words" in activity_data and "duration" in activity_data:
            participant.add_speaking_activity(
                activity_data["words"],
                activity_data["duration"]
            )
        else:
            participant.update_activity()
        
        # Update session statistics
        session.total_messages += activity_data.get("messages", 0)
    
    def get_session(self, session_id: str) -> Optional[CourtSession]:
        """Get session by ID."""
        return self.active_sessions.get(session_id)
    
    def get_participant(self, participant_id: str) -> Optional[Participant]:
        """Get participant by ID."""
        session_id = self.participant_sessions.get(participant_id)
        if session_id:
            session = self.active_sessions.get(session_id)
            if session:
                return session.participants.get(participant_id)
        return None
    
    def get_participant_by_connection(self, connection_id: str) -> Optional[Participant]:
        """Get participant by connection ID."""
        participant_id = self.connection_participants.get(connection_id)
        if participant_id:
            return self.get_participant(participant_id)
        return None
    
    def get_session_by_connection(self, connection_id: str) -> Optional[CourtSession]:
        """Get session by connection ID."""
        participant = self.get_participant_by_connection(connection_id)
        if participant:
            session_id = self.participant_sessions.get(participant.participant_id)
            if session_id:
                return self.active_sessions.get(session_id)
        return None
    
    def get_sessions_by_case(self, case_id: str) -> List[CourtSession]:
        """Get all sessions for a case."""
        return [
            session for session in self.active_sessions.values()
            if session.case_id == case_id
        ]
    
    def get_sessions_by_user(self, user_id: str) -> List[CourtSession]:
        """Get all sessions where user is a participant."""
        user_sessions = []
        for session in self.active_sessions.values():
            for participant in session.participants.values():
                if participant.user_id == user_id:
                    user_sessions.append(session)
                    break
        return user_sessions
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics."""
        total_participants = sum(
            len(session.participants) for session in self.active_sessions.values()
        )
        
        active_sessions = [
            session for session in self.active_sessions.values()
            if session.is_active
        ]
        
        session_types = {}
        for session in self.active_sessions.values():
            session_type = session.session_type.value
            session_types[session_type] = session_types.get(session_type, 0) + 1
        
        return {
            "total_sessions": len(self.active_sessions),
            "active_sessions": len(active_sessions),
            "total_participants": total_participants,
            "session_types": session_types,
            "recording_sessions": sum(
                1 for session in self.active_sessions.values()
                if session.is_recording
            )
        }
    
    def register_event_handler(self, event_type: str, handler: callable):
        """Register handler for session events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, session_id: str, data: Dict[str, Any]):
        """Emit session event to handlers."""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                await handler(session_id, data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def _cleanup_task(self):
        """Background task for cleaning up stale sessions and participants."""
        while self.is_running:
            try:
                now = datetime.utcnow()
                stale_sessions = []
                
                # Find stale sessions
                for session_id, session in self.active_sessions.items():
                    # Check if session is too old
                    if (now - session.created_at) > self.session_timeout:
                        stale_sessions.append(session_id)
                        continue
                    
                    # Check for inactive participants
                    inactive_participants = []
                    for participant_id, participant in session.participants.items():
                        if (participant.last_activity and 
                            (now - participant.last_activity) > timedelta(minutes=30)):
                            inactive_participants.append(participant_id)
                    
                    # Remove inactive participants
                    for participant_id in inactive_participants:
                        await self.remove_participant(session_id, participant_id)
                        self.logger.info(f"Removed inactive participant {participant_id}")
                
                # End stale sessions
                for session_id in stale_sessions:
                    await self.end_session(session_id)
                    self.logger.info(f"Cleaned up stale session {session_id}")
                
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait before retrying