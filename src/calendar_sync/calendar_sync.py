"""
Calendar Synchronization Engine for CourtSync

Provides bidirectional synchronization between legal calendars and external
calendar systems with conflict detection and resolution capabilities.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set, Callable
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import logging
import json
from abc import ABC, abstractmethod

import aiohttp
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .hearing_detector import HearingEvent, HearingType, HearingStatus
from ..deadline_management.calendar_integration import CalendarProvider, CalendarEvent, CalendarConfig

logger = logging.getLogger(__name__)

Base = declarative_base()


class SyncDirection(Enum):
    """Synchronization direction."""
    BIDIRECTIONAL = "bidirectional"
    TO_EXTERNAL = "to_external"
    FROM_EXTERNAL = "from_external"
    DISABLED = "disabled"


class SyncStatus(Enum):
    """Synchronization status."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SCHEDULED = "scheduled"
    CONFLICT = "conflict"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    MANUAL = "manual"
    PREFER_EXTERNAL = "prefer_external" 
    PREFER_INTERNAL = "prefer_internal"
    MOST_RECENT = "most_recent"
    HIGHEST_PRIORITY = "highest_priority"


@dataclass
class SyncMapping:
    """Maps internal events to external calendar events."""
    internal_id: str
    external_id: str
    provider: CalendarProvider
    calendar_id: str
    last_sync: datetime
    sync_hash: str  # Hash of event data for change detection
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncConflict:
    """Represents a synchronization conflict."""
    conflict_id: str
    internal_event: Union[HearingEvent, CalendarEvent]
    external_event: CalendarEvent
    conflict_type: str
    description: str
    created_at: datetime
    resolved: bool = False
    resolution_strategy: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    status: SyncStatus
    events_synced: int = 0
    events_created: int = 0
    events_updated: int = 0
    events_deleted: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: Optional[timedelta] = None
    timestamp: datetime = field(default_factory=datetime.now)


class SyncMappingModel(Base):
    """Database model for sync mappings."""
    __tablename__ = 'calendar_sync_mappings'
    
    id = Column(Integer, primary_key=True)
    internal_id = Column(String(255), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)
    calendar_id = Column(String(255), nullable=False)
    last_sync = Column(DateTime, nullable=False)
    sync_hash = Column(String(64), nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SyncConflictModel(Base):
    """Database model for sync conflicts."""
    __tablename__ = 'calendar_sync_conflicts'
    
    id = Column(Integer, primary_key=True)
    conflict_id = Column(String(255), nullable=False, unique=True, index=True)
    internal_event_id = Column(String(255), nullable=False)
    external_event_id = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)
    conflict_type = Column(String(100), nullable=False)
    description = Column(Text)
    internal_event_data = Column(JSON)
    external_event_data = Column(JSON)
    resolved = Column(Boolean, default=False)
    resolution_strategy = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(255))


class EventTransformer:
    """Transforms events between internal and external formats."""
    
    @staticmethod
    def hearing_to_calendar_event(hearing: HearingEvent) -> CalendarEvent:
        """Convert HearingEvent to CalendarEvent."""
        # Map hearing type to event type
        event_type_mapping = {
            HearingType.HEARING: "court_date",
            HearingType.TRIAL: "court_date", 
            HearingType.MOTION_HEARING: "hearing",
            HearingType.STATUS_CONFERENCE: "meeting",
            HearingType.SETTLEMENT_CONFERENCE: "meeting",
            HearingType.PRETRIAL_CONFERENCE: "meeting",
            HearingType.DEPOSITION: "deposition",
            HearingType.ARBITRATION: "meeting",
            HearingType.MEDIATION: "meeting"
        }
        
        # Determine priority based on hearing type and status
        priority_mapping = {
            HearingType.TRIAL: "critical",
            HearingType.HEARING: "high",
            HearingType.MOTION_HEARING: "high",
            HearingType.DEPOSITION: "medium",
            HearingType.STATUS_CONFERENCE: "medium"
        }
        
        title = f"{hearing.hearing_type.value.replace('_', ' ').title()}"
        if hearing.case_title and hearing.case_title != "Unknown Case":
            title += f" - {hearing.case_title}"
        
        description_parts = []
        if hearing.case_number and hearing.case_number != "UNKNOWN":
            description_parts.append(f"Case: {hearing.case_number}")
        if hearing.judge:
            description_parts.append(f"Judge: {hearing.judge}")
        if hearing.location and hearing.location.courtroom:
            description_parts.append(f"Courtroom: {hearing.location.courtroom}")
        if hearing.description:
            description_parts.append(f"Description: {hearing.description}")
        if hearing.parties:
            description_parts.append(f"Parties: {', '.join(hearing.parties[:3])}")
        
        location_str = None
        if hearing.location:
            location_parts = [
                hearing.location.court_name,
                hearing.location.address,
                hearing.location.city
            ]
            location_str = ", ".join(filter(None, location_parts))
        
        return CalendarEvent(
            title=title,
            description="\n".join(description_parts),
            start_time=hearing.date_time,
            end_time=hearing.end_time or hearing.date_time + timedelta(hours=1),
            event_type=event_type_mapping.get(hearing.hearing_type, "meeting"),
            priority=priority_mapping.get(hearing.hearing_type, "medium"),
            case_id=hearing.case_number,
            location=location_str,
            attendees=hearing.attorneys if hearing.attorneys else None,
            reminders=EventTransformer._get_hearing_reminders(hearing.hearing_type),
            metadata={
                'hearing_id': hearing.hearing_id,
                'hearing_type': hearing.hearing_type.value,
                'confidence': hearing.confidence,
                'source': hearing.source,
                'original_event': hearing.to_dict()
            }
        )
    
    @staticmethod
    def calendar_event_to_hearing(calendar_event: CalendarEvent) -> HearingEvent:
        """Convert CalendarEvent back to HearingEvent."""
        # Extract hearing type from metadata or title
        hearing_type = HearingType.HEARING  # Default
        
        if calendar_event.metadata and 'hearing_type' in calendar_event.metadata:
            try:
                hearing_type = HearingType(calendar_event.metadata['hearing_type'])
            except ValueError:
                pass
        else:
            # Try to infer from title
            title_lower = calendar_event.title.lower()
            if 'trial' in title_lower:
                hearing_type = HearingType.TRIAL
            elif 'motion' in title_lower:
                hearing_type = HearingType.MOTION_HEARING
            elif 'deposition' in title_lower:
                hearing_type = HearingType.DEPOSITION
            elif 'status' in title_lower:
                hearing_type = HearingType.STATUS_CONFERENCE
        
        return HearingEvent(
            hearing_id=calendar_event.metadata.get('hearing_id', f"ext_{hash(calendar_event.title)}"),
            case_number=calendar_event.case_id or "EXTERNAL",
            case_title=calendar_event.title,
            hearing_type=hearing_type,
            date_time=calendar_event.start_time,
            end_time=calendar_event.end_time,
            judge=EventTransformer._extract_judge_from_description(calendar_event.description),
            status=HearingStatus.SCHEDULED,
            confidence=calendar_event.metadata.get('confidence', 1.0),
            source="external_calendar",
            description=calendar_event.description,
            metadata=calendar_event.metadata or {}
        )
    
    @staticmethod
    def _get_hearing_reminders(hearing_type: HearingType) -> List[int]:
        """Get reminder schedule for hearing type."""
        reminder_schedules = {
            HearingType.TRIAL: [10080, 2880, 1440, 240, 60],  # 1 week to 1 hour
            HearingType.HEARING: [2880, 1440, 240, 60],       # 2 days to 1 hour
            HearingType.MOTION_HEARING: [1440, 240, 60],      # 1 day to 1 hour
            HearingType.DEPOSITION: [1440, 240],              # 1 day to 4 hours
            HearingType.STATUS_CONFERENCE: [1440, 240],       # 1 day to 4 hours
        }
        return reminder_schedules.get(hearing_type, [1440, 240])  # Default
    
    @staticmethod
    def _extract_judge_from_description(description: str) -> Optional[str]:
        """Extract judge name from event description."""
        if not description:
            return None
        
        import re
        patterns = [
            r'Judge:\s*([^\n\r]+)',
            r'(?:Hon\.?|Honorable)\s+([^\n\r,]+)',
            r'Before\s+([^\n\r,]+),?\s+J\.?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None


class CalendarSyncEngine:
    """Main calendar synchronization engine."""
    
    def __init__(self, database_url: str, redis_url: Optional[str] = None):
        # Database setup
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Redis cache for performance
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        
        # Calendar providers
        self.providers: Dict[str, Any] = {}  # provider_name -> provider_instance
        self.sync_configs: Dict[str, Dict[str, Any]] = {}  # provider_name -> config
        
        # Event transformers and handlers
        self.transformer = EventTransformer()
        self.conflict_handlers: Dict[ConflictResolution, Callable] = {}
        
        # Sync state
        self.active_syncs: Set[str] = set()
        self.last_sync_times: Dict[str, datetime] = {}
        
        self._setup_conflict_handlers()
    
    def register_provider(self, name: str, provider: Any, config: Dict[str, Any]):
        """Register a calendar provider for synchronization."""
        self.providers[name] = provider
        self.sync_configs[name] = {
            'direction': config.get('direction', SyncDirection.BIDIRECTIONAL),
            'conflict_resolution': config.get('conflict_resolution', ConflictResolution.MANUAL),
            'sync_interval': config.get('sync_interval', 300),  # seconds
            'enabled': config.get('enabled', True),
            'calendar_filters': config.get('calendar_filters', {}),
            'event_filters': config.get('event_filters', {})
        }
        logger.info(f"Registered calendar provider: {name}")
    
    def _setup_conflict_handlers(self):
        """Setup conflict resolution handlers."""
        self.conflict_handlers = {
            ConflictResolution.PREFER_EXTERNAL: self._resolve_prefer_external,
            ConflictResolution.PREFER_INTERNAL: self._resolve_prefer_internal,
            ConflictResolution.MOST_RECENT: self._resolve_most_recent,
            ConflictResolution.HIGHEST_PRIORITY: self._resolve_highest_priority
        }
    
    async def sync_all_providers(self) -> Dict[str, SyncResult]:
        """Synchronize with all registered providers."""
        results = {}
        
        # Run syncs in parallel
        sync_tasks = []
        for provider_name in self.providers.keys():
            if self.sync_configs[provider_name]['enabled']:
                task = asyncio.create_task(self.sync_provider(provider_name))
                sync_tasks.append((provider_name, task))
        
        # Collect results
        for provider_name, task in sync_tasks:
            try:
                result = await task
                results[provider_name] = result
            except Exception as e:
                logger.error(f"Sync failed for provider {provider_name}: {str(e)}")
                results[provider_name] = SyncResult(
                    status=SyncStatus.FAILED,
                    errors=[str(e)]
                )
        
        return results
    
    async def sync_provider(self, provider_name: str) -> SyncResult:
        """Synchronize with a specific provider."""
        if provider_name in self.active_syncs:
            return SyncResult(
                status=SyncStatus.FAILED,
                errors=[f"Sync already in progress for {provider_name}"]
            )
        
        start_time = datetime.now()
        self.active_syncs.add(provider_name)
        
        try:
            provider = self.providers[provider_name]
            config = self.sync_configs[provider_name]
            direction = config['direction']
            
            result = SyncResult(status=SyncStatus.IN_PROGRESS)
            
            # Bidirectional or from external
            if direction in [SyncDirection.BIDIRECTIONAL, SyncDirection.FROM_EXTERNAL]:
                ext_result = await self._sync_from_external(provider_name, provider, config)
                result.events_synced += ext_result.events_synced
                result.events_created += ext_result.events_created
                result.events_updated += ext_result.events_updated
                result.conflicts_detected += ext_result.conflicts_detected
                result.errors.extend(ext_result.errors)
                result.warnings.extend(ext_result.warnings)
            
            # Bidirectional or to external
            if direction in [SyncDirection.BIDIRECTIONAL, SyncDirection.TO_EXTERNAL]:
                int_result = await self._sync_to_external(provider_name, provider, config)
                result.events_synced += int_result.events_synced
                result.events_created += int_result.events_created
                result.events_updated += int_result.events_updated
                result.conflicts_detected += int_result.conflicts_detected
                result.errors.extend(int_result.errors)
                result.warnings.extend(int_result.warnings)
            
            # Resolve conflicts if auto-resolution is enabled
            if config['conflict_resolution'] != ConflictResolution.MANUAL:
                conflicts_resolved = await self._auto_resolve_conflicts(
                    provider_name, config['conflict_resolution']
                )
                result.conflicts_resolved = conflicts_resolved
            
            # Determine final status
            if result.errors:
                result.status = SyncStatus.PARTIAL_SUCCESS if result.events_synced > 0 else SyncStatus.FAILED
            elif result.conflicts_detected > result.conflicts_resolved:
                result.status = SyncStatus.CONFLICT
            else:
                result.status = SyncStatus.SUCCESS
            
            result.duration = datetime.now() - start_time
            self.last_sync_times[provider_name] = datetime.now()
            
            logger.info(f"Sync completed for {provider_name}: {result.status.value}")
            return result
        
        except Exception as e:
            logger.error(f"Sync error for {provider_name}: {str(e)}")
            return SyncResult(
                status=SyncStatus.FAILED,
                errors=[str(e)],
                duration=datetime.now() - start_time
            )
        finally:
            self.active_syncs.discard(provider_name)
    
    async def _sync_from_external(self, provider_name: str, provider: Any,
                                config: Dict[str, Any]) -> SyncResult:
        """Sync events from external calendar to internal system."""
        result = SyncResult(status=SyncStatus.SUCCESS)
        
        try:
            # Get date range for sync (last sync + buffer)
            last_sync = self.last_sync_times.get(provider_name, datetime.now() - timedelta(days=30))
            start_date = last_sync - timedelta(hours=1)  # Small buffer
            end_date = datetime.now() + timedelta(days=90)  # Future events
            
            # Fetch external events
            external_events = await provider.get_events(start_date, end_date)
            logger.info(f"Fetched {len(external_events)} events from {provider_name}")
            
            # Process each external event
            with self.SessionLocal() as db_session:
                for ext_event in external_events:
                    try:
                        await self._process_external_event(
                            ext_event, provider_name, db_session, result
                        )
                    except Exception as e:
                        result.errors.append(f"Failed to process event {ext_event.external_event_id}: {str(e)}")
                        logger.error(f"Failed to process external event: {str(e)}")
                
                db_session.commit()
        
        except Exception as e:
            result.errors.append(f"Failed to fetch external events: {str(e)}")
            result.status = SyncStatus.FAILED
        
        return result
    
    async def _sync_to_external(self, provider_name: str, provider: Any,
                              config: Dict[str, Any]) -> SyncResult:
        """Sync internal events to external calendar."""
        result = SyncResult(status=SyncStatus.SUCCESS)
        
        try:
            # Get internal events that need syncing
            with self.SessionLocal() as db_session:
                # This would typically fetch from your internal hearing/event database
                # For now, we'll simulate with a method call
                internal_events = await self._get_internal_events_for_sync(
                    provider_name, db_session
                )
                
                logger.info(f"Found {len(internal_events)} internal events to sync to {provider_name}")
                
                for internal_event in internal_events:
                    try:
                        await self._process_internal_event(
                            internal_event, provider_name, provider, db_session, result
                        )
                    except Exception as e:
                        result.errors.append(f"Failed to sync internal event {internal_event.hearing_id}: {str(e)}")
                        logger.error(f"Failed to sync internal event: {str(e)}")
                
                db_session.commit()
        
        except Exception as e:
            result.errors.append(f"Failed to sync to external calendar: {str(e)}")
            result.status = SyncStatus.FAILED
        
        return result
    
    async def _process_external_event(self, ext_event: CalendarEvent, provider_name: str,
                                    db_session: Session, result: SyncResult):
        """Process a single external event."""
        # Check if we already have a mapping for this event
        existing_mapping = db_session.query(SyncMappingModel).filter_by(
            external_id=ext_event.external_event_id,
            provider=provider_name
        ).first()
        
        # Convert to internal format
        hearing_event = self.transformer.calendar_event_to_hearing(ext_event)
        event_hash = self._calculate_event_hash(ext_event)
        
        if existing_mapping:
            # Check if event has changed
            if existing_mapping.sync_hash != event_hash:
                # Event has been modified - check for conflicts
                conflict = await self._detect_conflict(
                    existing_mapping.internal_id, ext_event, db_session
                )
                
                if conflict:
                    await self._store_conflict(conflict, db_session)
                    result.conflicts_detected += 1
                else:
                    # Update internal event
                    await self._update_internal_event(existing_mapping.internal_id, hearing_event)
                    existing_mapping.sync_hash = event_hash
                    existing_mapping.last_sync = datetime.now()
                    result.events_updated += 1
        else:
            # New external event - create internal event
            internal_id = await self._create_internal_event(hearing_event)
            
            # Create mapping
            new_mapping = SyncMappingModel(
                internal_id=internal_id,
                external_id=ext_event.external_event_id,
                provider=provider_name,
                calendar_id=ext_event.metadata.get('calendar_id', 'default'),
                last_sync=datetime.now(),
                sync_hash=event_hash,
                metadata=ext_event.metadata or {}
            )
            db_session.add(new_mapping)
            result.events_created += 1
        
        result.events_synced += 1
    
    async def _process_internal_event(self, internal_event: HearingEvent, provider_name: str,
                                    provider: Any, db_session: Session, result: SyncResult):
        """Process a single internal event for external sync."""
        # Check if we already have a mapping
        existing_mapping = db_session.query(SyncMappingModel).filter_by(
            internal_id=internal_event.hearing_id,
            provider=provider_name
        ).first()
        
        # Convert to external format
        calendar_event = self.transformer.hearing_to_calendar_event(internal_event)
        event_hash = self._calculate_event_hash(calendar_event)
        
        if existing_mapping:
            # Check if event has changed
            if existing_mapping.sync_hash != event_hash:
                # Update external event
                success = await provider.update_event(existing_mapping.external_id, calendar_event)
                if success:
                    existing_mapping.sync_hash = event_hash
                    existing_mapping.last_sync = datetime.now()
                    result.events_updated += 1
                else:
                    result.errors.append(f"Failed to update external event {existing_mapping.external_id}")
        else:
            # Create new external event
            external_id = await provider.create_event(calendar_event)
            if external_id:
                # Create mapping
                new_mapping = SyncMappingModel(
                    internal_id=internal_event.hearing_id,
                    external_id=external_id,
                    provider=provider_name,
                    calendar_id='primary',  # Default calendar
                    last_sync=datetime.now(),
                    sync_hash=event_hash,
                    metadata={'created_by_sync': True}
                )
                db_session.add(new_mapping)
                result.events_created += 1
            else:
                result.errors.append(f"Failed to create external event for {internal_event.hearing_id}")
        
        result.events_synced += 1
    
    async def _detect_conflict(self, internal_id: str, external_event: CalendarEvent,
                             db_session: Session) -> Optional[SyncConflict]:
        """Detect synchronization conflicts."""
        # Get the current internal event (this would be from your event store)
        internal_event = await self._get_internal_event(internal_id)
        if not internal_event:
            return None
        
        conflicts = []
        
        # Check for datetime conflicts
        if abs((internal_event.date_time - external_event.start_time).total_seconds()) > 300:  # 5 min tolerance
            conflicts.append("DateTime mismatch")
        
        # Check for title/description conflicts
        if internal_event.case_title != external_event.title:
            conflicts.append("Title mismatch")
        
        # Check for location conflicts
        internal_location = internal_event.location.court_name if internal_event.location else None
        if internal_location and external_event.location and internal_location not in external_event.location:
            conflicts.append("Location mismatch")
        
        if conflicts:
            conflict_id = f"conflict_{datetime.now().timestamp()}_{hash(internal_id)}"
            return SyncConflict(
                conflict_id=conflict_id,
                internal_event=internal_event,
                external_event=external_event,
                conflict_type="sync_mismatch",
                description="; ".join(conflicts),
                created_at=datetime.now()
            )
        
        return None
    
    async def _store_conflict(self, conflict: SyncConflict, db_session: Session):
        """Store a sync conflict in the database."""
        conflict_model = SyncConflictModel(
            conflict_id=conflict.conflict_id,
            internal_event_id=conflict.internal_event.hearing_id,
            external_event_id=conflict.external_event.external_event_id,
            provider=conflict.external_event.provider.value if conflict.external_event.provider else "unknown",
            conflict_type=conflict.conflict_type,
            description=conflict.description,
            internal_event_data=conflict.internal_event.to_dict(),
            external_event_data=conflict.external_event.to_dict(),
            created_at=conflict.created_at
        )
        db_session.add(conflict_model)
        logger.warning(f"Conflict detected and stored: {conflict.conflict_id}")
    
    async def _auto_resolve_conflicts(self, provider_name: str,
                                    strategy: ConflictResolution) -> int:
        """Automatically resolve conflicts based on strategy."""
        resolved_count = 0
        
        with self.SessionLocal() as db_session:
            # Get unresolved conflicts for this provider
            conflicts = db_session.query(SyncConflictModel).filter_by(
                provider=provider_name,
                resolved=False
            ).all()
            
            for conflict_model in conflicts:
                try:
                    # Reconstruct conflict object
                    internal_event = HearingEvent.from_dict(conflict_model.internal_event_data)
                    external_event = CalendarEvent.from_dict(conflict_model.external_event_data)
                    
                    conflict = SyncConflict(
                        conflict_id=conflict_model.conflict_id,
                        internal_event=internal_event,
                        external_event=external_event,
                        conflict_type=conflict_model.conflict_type,
                        description=conflict_model.description,
                        created_at=conflict_model.created_at
                    )
                    
                    # Apply resolution strategy
                    handler = self.conflict_handlers.get(strategy)
                    if handler:
                        resolved = await handler(conflict, provider_name)
                        if resolved:
                            conflict_model.resolved = True
                            conflict_model.resolution_strategy = strategy.value
                            conflict_model.resolved_at = datetime.now()
                            conflict_model.resolved_by = "auto_resolver"
                            resolved_count += 1
                
                except Exception as e:
                    logger.error(f"Failed to resolve conflict {conflict_model.conflict_id}: {str(e)}")
            
            db_session.commit()
        
        logger.info(f"Auto-resolved {resolved_count} conflicts using {strategy.value} strategy")
        return resolved_count
    
    async def _resolve_prefer_external(self, conflict: SyncConflict, provider_name: str) -> bool:
        """Resolve conflict by preferring external event data."""
        try:
            # Update internal event with external event data
            hearing_event = self.transformer.calendar_event_to_hearing(conflict.external_event)
            await self._update_internal_event(conflict.internal_event.hearing_id, hearing_event)
            return True
        except Exception as e:
            logger.error(f"Failed to resolve conflict preferring external: {str(e)}")
            return False
    
    async def _resolve_prefer_internal(self, conflict: SyncConflict, provider_name: str) -> bool:
        """Resolve conflict by preferring internal event data."""
        try:
            # Update external event with internal event data
            provider = self.providers[provider_name]
            calendar_event = self.transformer.hearing_to_calendar_event(conflict.internal_event)
            
            # Get external event ID from mapping
            with self.SessionLocal() as db_session:
                mapping = db_session.query(SyncMappingModel).filter_by(
                    internal_id=conflict.internal_event.hearing_id,
                    provider=provider_name
                ).first()
                
                if mapping:
                    success = await provider.update_event(mapping.external_id, calendar_event)
                    return success
            
            return False
        except Exception as e:
            logger.error(f"Failed to resolve conflict preferring internal: {str(e)}")
            return False
    
    async def _resolve_most_recent(self, conflict: SyncConflict, provider_name: str) -> bool:
        """Resolve conflict by using the most recently modified event."""
        internal_updated = conflict.internal_event.updated_at
        external_updated = conflict.external_event.metadata.get('updated_at')
        
        if external_updated:
            external_updated = datetime.fromisoformat(external_updated)
            if external_updated > internal_updated:
                return await self._resolve_prefer_external(conflict, provider_name)
        
        return await self._resolve_prefer_internal(conflict, provider_name)
    
    async def _resolve_highest_priority(self, conflict: SyncConflict, provider_name: str) -> bool:
        """Resolve conflict by using the event with highest priority."""
        # Priority order: critical > high > medium > low
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        
        internal_priority = getattr(conflict.internal_event, 'priority', 'medium')
        external_priority = conflict.external_event.priority
        
        internal_score = priority_order.get(internal_priority, 2)
        external_score = priority_order.get(external_priority, 2)
        
        if external_score > internal_score:
            return await self._resolve_prefer_external(conflict, provider_name)
        else:
            return await self._resolve_prefer_internal(conflict, provider_name)
    
    def _calculate_event_hash(self, event: Union[CalendarEvent, HearingEvent]) -> str:
        """Calculate hash for event change detection."""
        import hashlib
        
        if isinstance(event, CalendarEvent):
            data = f"{event.title}|{event.start_time.isoformat()}|{event.end_time.isoformat()}|{event.description}"
        else:  # HearingEvent
            data = f"{event.case_title}|{event.date_time.isoformat()}|{event.description}|{event.judge}"
        
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def _get_internal_events_for_sync(self, provider_name: str,
                                          db_session: Session) -> List[HearingEvent]:
        """Get internal events that need syncing to external provider."""
        # This is a placeholder - in a real implementation, you'd query your hearing database
        # Filter by events modified since last sync, new events, etc.
        return []
    
    async def _get_internal_event(self, internal_id: str) -> Optional[HearingEvent]:
        """Get internal event by ID."""
        # This is a placeholder - in a real implementation, you'd query your hearing database
        return None
    
    async def _create_internal_event(self, hearing_event: HearingEvent) -> str:
        """Create new internal event and return its ID."""
        # This is a placeholder - in a real implementation, you'd store in your hearing database
        return hearing_event.hearing_id
    
    async def _update_internal_event(self, internal_id: str, hearing_event: HearingEvent) -> bool:
        """Update existing internal event."""
        # This is a placeholder - in a real implementation, you'd update your hearing database
        return True
    
    def get_sync_status(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Get synchronization status for providers."""
        if provider_name:
            return {
                'provider': provider_name,
                'enabled': self.sync_configs.get(provider_name, {}).get('enabled', False),
                'last_sync': self.last_sync_times.get(provider_name),
                'active': provider_name in self.active_syncs
            }
        else:
            return {
                provider: {
                    'enabled': config.get('enabled', False),
                    'last_sync': self.last_sync_times.get(provider),
                    'active': provider in self.active_syncs,
                    'direction': config.get('direction', SyncDirection.DISABLED).value
                }
                for provider, config in self.sync_configs.items()
            }
    
    def get_conflicts(self, provider_name: Optional[str] = None,
                     resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get synchronization conflicts."""
        with self.SessionLocal() as db_session:
            query = db_session.query(SyncConflictModel)
            
            if provider_name:
                query = query.filter_by(provider=provider_name)
            
            if resolved is not None:
                query = query.filter_by(resolved=resolved)
            
            conflicts = query.order_by(SyncConflictModel.created_at.desc()).all()
            
            return [
                {
                    'conflict_id': c.conflict_id,
                    'provider': c.provider,
                    'conflict_type': c.conflict_type,
                    'description': c.description,
                    'resolved': c.resolved,
                    'resolution_strategy': c.resolution_strategy,
                    'created_at': c.created_at.isoformat(),
                    'resolved_at': c.resolved_at.isoformat() if c.resolved_at else None
                }
                for c in conflicts
            ]
    
    async def resolve_conflict_manually(self, conflict_id: str,
                                      resolution: ConflictResolution,
                                      user_id: str) -> bool:
        """Manually resolve a specific conflict."""
        with self.SessionLocal() as db_session:
            conflict_model = db_session.query(SyncConflictModel).filter_by(
                conflict_id=conflict_id
            ).first()
            
            if not conflict_model or conflict_model.resolved:
                return False
            
            try:
                # Reconstruct conflict
                internal_event = HearingEvent.from_dict(conflict_model.internal_event_data)
                external_event = CalendarEvent.from_dict(conflict_model.external_event_data)
                
                conflict = SyncConflict(
                    conflict_id=conflict_model.conflict_id,
                    internal_event=internal_event,
                    external_event=external_event,
                    conflict_type=conflict_model.conflict_type,
                    description=conflict_model.description,
                    created_at=conflict_model.created_at
                )
                
                # Apply resolution
                handler = self.conflict_handlers.get(resolution)
                if handler:
                    resolved = await handler(conflict, conflict_model.provider)
                    if resolved:
                        conflict_model.resolved = True
                        conflict_model.resolution_strategy = resolution.value
                        conflict_model.resolved_at = datetime.now()
                        conflict_model.resolved_by = user_id
                        db_session.commit()
                        return True
                
                return False
            
            except Exception as e:
                logger.error(f"Failed to manually resolve conflict {conflict_id}: {str(e)}")
                return False


class SyncManager:
    """High-level sync manager with scheduling and monitoring."""
    
    def __init__(self, sync_engine: CalendarSyncEngine):
        self.sync_engine = sync_engine
        self.scheduler = AsyncIOScheduler()
        self.monitoring_callbacks: List[Callable] = []
    
    def start_scheduled_sync(self):
        """Start scheduled synchronization for all providers."""
        for provider_name, config in self.sync_engine.sync_configs.items():
            if config.get('enabled', False):
                interval = config.get('sync_interval', 300)  # seconds
                
                self.scheduler.add_job(
                    func=self._scheduled_sync_job,
                    trigger=IntervalTrigger(seconds=interval),
                    args=[provider_name],
                    id=f"sync_{provider_name}",
                    replace_existing=True
                )
        
        if not self.scheduler.running:
            self.scheduler.start()
        
        logger.info("Scheduled synchronization started")
    
    def stop_scheduled_sync(self):
        """Stop scheduled synchronization."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        logger.info("Scheduled synchronization stopped")
    
    async def _scheduled_sync_job(self, provider_name: str):
        """Execute scheduled sync job."""
        try:
            result = await self.sync_engine.sync_provider(provider_name)
            
            # Notify monitoring callbacks
            for callback in self.monitoring_callbacks:
                try:
                    await callback(provider_name, result)
                except Exception as e:
                    logger.error(f"Monitoring callback failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Scheduled sync job failed for {provider_name}: {str(e)}")
    
    def add_monitoring_callback(self, callback: Callable):
        """Add callback for sync result monitoring."""
        self.monitoring_callbacks.append(callback)
    
    def remove_monitoring_callback(self, callback: Callable):
        """Remove monitoring callback."""
        if callback in self.monitoring_callbacks:
            self.monitoring_callbacks.remove(callback)
    
    async def get_sync_health(self) -> Dict[str, Any]:
        """Get overall sync health status."""
        health = {
            'overall_status': 'healthy',
            'providers': {},
            'total_conflicts': 0,
            'last_sync_oldest': None,
            'scheduler_running': self.scheduler.running
        }
        
        now = datetime.now()
        
        for provider_name, config in self.sync_engine.sync_configs.items():
            provider_health = {
                'enabled': config.get('enabled', False),
                'last_sync': self.sync_engine.last_sync_times.get(provider_name),
                'active': provider_name in self.sync_engine.active_syncs,
                'sync_age_minutes': None,
                'status': 'unknown'
            }
            
            last_sync = provider_health['last_sync']
            if last_sync:
                age = now - last_sync
                provider_health['sync_age_minutes'] = age.total_seconds() / 60
                
                if health['last_sync_oldest'] is None or last_sync < health['last_sync_oldest']:
                    health['last_sync_oldest'] = last_sync
                
                # Determine status based on sync age
                sync_interval = config.get('sync_interval', 300) / 60  # Convert to minutes
                if age.total_seconds() / 60 > sync_interval * 2:
                    provider_health['status'] = 'stale'
                    health['overall_status'] = 'degraded'
                else:
                    provider_health['status'] = 'healthy'
            
            health['providers'][provider_name] = provider_health
        
        # Get conflict count
        conflicts = self.sync_engine.get_conflicts(resolved=False)
        health['total_conflicts'] = len(conflicts)
        
        if health['total_conflicts'] > 10:
            health['overall_status'] = 'degraded'
        elif health['total_conflicts'] > 50:
            health['overall_status'] = 'unhealthy'
        
        return health


# Example monitoring callback
async def sync_monitoring_callback(provider_name: str, result: SyncResult):
    """Example monitoring callback for sync results."""
    if result.status == SyncStatus.FAILED:
        logger.error(f"Sync failed for {provider_name}: {result.errors}")
        # Could send alert notifications here
    elif result.conflicts_detected > 0:
        logger.warning(f"Sync conflicts detected for {provider_name}: {result.conflicts_detected}")
        # Could escalate conflicts for manual review
    else:
        logger.info(f"Sync successful for {provider_name}: {result.events_synced} events synced")


# Example usage
async def example_usage():
    """Example usage of the calendar sync engine."""
    
    # Initialize sync engine
    sync_engine = CalendarSyncEngine(
        database_url="sqlite:///calendar_sync.db",
        redis_url="redis://localhost:6379"
    )
    
    # Example provider registration (you would use real providers)
    class MockGoogleProvider:
        async def get_events(self, start_date, end_date):
            return []
        
        async def create_event(self, event):
            return "mock_event_id"
        
        async def update_event(self, event_id, event):
            return True
    
    google_provider = MockGoogleProvider()
    sync_engine.register_provider("google", google_provider, {
        'direction': SyncDirection.BIDIRECTIONAL,
        'conflict_resolution': ConflictResolution.MOST_RECENT,
        'sync_interval': 300,
        'enabled': True
    })
    
    # Create sync manager
    sync_manager = SyncManager(sync_engine)
    sync_manager.add_monitoring_callback(sync_monitoring_callback)
    
    # Start scheduled sync
    sync_manager.start_scheduled_sync()
    
    # Perform manual sync
    results = await sync_engine.sync_all_providers()
    print(f"Sync results: {results}")
    
    # Get sync health
    health = await sync_manager.get_sync_health()
    print(f"Sync health: {health}")
    
    # Cleanup
    sync_manager.stop_scheduled_sync()


if __name__ == "__main__":
    asyncio.run(example_usage())