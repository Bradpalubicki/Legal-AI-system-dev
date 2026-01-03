"""
CourtSync Manager - Main orchestrator for calendar synchronization system

Integrates all components: hearing detection, calendar sync, court data integration,
and conflict resolution to provide a complete calendar management solution.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import json

from .hearing_detector import HearingDetector, HearingEvent, HearingType, HearingStatus
from .calendar_sync import CalendarSyncEngine, SyncManager, SyncResult, SyncStatus
from .court_data_integration import CourtDataIntegrationManager, CourtInfo, DataSourceConfig
from .conflict_resolver import ConflictDetector, ConflictResolver, ScheduleConflict, ConflictType
from ..deadline_management.calendar_integration import LegalCalendarManager, CalendarConfig, CalendarProvider

logger = logging.getLogger(__name__)


class CourtSyncStatus(Enum):
    """Overall system status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    INITIALIZING = "initializing"


class SyncMode(Enum):
    """Synchronization modes."""
    AUTOMATIC = "automatic"         # Fully automated sync
    SEMI_AUTOMATIC = "semi_automatic"  # Auto sync with manual conflict resolution
    MANUAL = "manual"              # Manual sync only
    MONITORING_ONLY = "monitoring_only"  # Monitor but don't sync


@dataclass
class CourtSyncConfig:
    """Configuration for CourtSync system."""
    # System settings
    sync_mode: SyncMode = SyncMode.SEMI_AUTOMATIC
    sync_interval_minutes: int = 15
    conflict_resolution_enabled: bool = True
    auto_reschedule_enabled: bool = True
    
    # Detection settings
    min_confidence_threshold: float = 0.6
    enable_ml_detection: bool = True
    ml_model_path: Optional[str] = None
    
    # Integration settings
    court_data_sources: List[str] = field(default_factory=list)
    calendar_providers: List[str] = field(default_factory=list)
    enable_pacer_integration: bool = True
    enable_ecf_integration: bool = True
    enable_state_courts: bool = True
    
    # Notification settings
    notify_on_conflicts: bool = True
    notify_on_sync_failures: bool = True
    notification_channels: List[str] = field(default_factory=list)
    
    # Business rules
    business_hours_start: time = field(default_factory=lambda: time(9, 0))
    business_hours_end: time = field(default_factory=lambda: time(17, 0))
    min_travel_buffer_minutes: int = 30
    max_daily_hearings: int = 10
    
    # Data retention
    retain_conflicts_days: int = 90
    retain_sync_logs_days: int = 30
    archive_old_hearings: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'sync_mode': self.sync_mode.value,
            'sync_interval_minutes': self.sync_interval_minutes,
            'conflict_resolution_enabled': self.conflict_resolution_enabled,
            'auto_reschedule_enabled': self.auto_reschedule_enabled,
            'min_confidence_threshold': self.min_confidence_threshold,
            'enable_ml_detection': self.enable_ml_detection,
            'ml_model_path': self.ml_model_path,
            'court_data_sources': self.court_data_sources,
            'calendar_providers': self.calendar_providers,
            'enable_pacer_integration': self.enable_pacer_integration,
            'enable_ecf_integration': self.enable_ecf_integration,
            'enable_state_courts': self.enable_state_courts,
            'notify_on_conflicts': self.notify_on_conflicts,
            'notify_on_sync_failures': self.notify_on_sync_failures,
            'notification_channels': self.notification_channels,
            'business_hours_start': self.business_hours_start.isoformat(),
            'business_hours_end': self.business_hours_end.isoformat(),
            'min_travel_buffer_minutes': self.min_travel_buffer_minutes,
            'max_daily_hearings': self.max_daily_hearings,
            'retain_conflicts_days': self.retain_conflicts_days,
            'retain_sync_logs_days': self.retain_sync_logs_days,
            'archive_old_hearings': self.archive_old_hearings
        }


@dataclass
class SystemMetrics:
    """System performance and health metrics."""
    # Sync metrics
    total_syncs_today: int = 0
    successful_syncs_today: int = 0
    failed_syncs_today: int = 0
    avg_sync_duration_seconds: float = 0.0
    last_successful_sync: Optional[datetime] = None
    
    # Detection metrics
    hearings_detected_today: int = 0
    detection_accuracy_rate: float = 0.0
    avg_detection_confidence: float = 0.0
    
    # Conflict metrics
    conflicts_detected_today: int = 0
    conflicts_resolved_today: int = 0
    pending_conflicts: int = 0
    critical_conflicts: int = 0
    
    # Data source metrics
    active_data_sources: int = 0
    pacer_queries_today: int = 0
    ecf_queries_today: int = 0
    calendar_events_synced_today: int = 0
    
    # Error metrics
    errors_today: int = 0
    warnings_today: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'sync': {
                'total_syncs_today': self.total_syncs_today,
                'successful_syncs_today': self.successful_syncs_today,
                'failed_syncs_today': self.failed_syncs_today,
                'success_rate': self.successful_syncs_today / max(self.total_syncs_today, 1) * 100,
                'avg_sync_duration_seconds': self.avg_sync_duration_seconds,
                'last_successful_sync': self.last_successful_sync.isoformat() if self.last_successful_sync else None
            },
            'detection': {
                'hearings_detected_today': self.hearings_detected_today,
                'detection_accuracy_rate': self.detection_accuracy_rate,
                'avg_detection_confidence': self.avg_detection_confidence
            },
            'conflicts': {
                'conflicts_detected_today': self.conflicts_detected_today,
                'conflicts_resolved_today': self.conflicts_resolved_today,
                'pending_conflicts': self.pending_conflicts,
                'critical_conflicts': self.critical_conflicts,
                'resolution_rate': self.conflicts_resolved_today / max(self.conflicts_detected_today, 1) * 100
            },
            'data_sources': {
                'active_data_sources': self.active_data_sources,
                'pacer_queries_today': self.pacer_queries_today,
                'ecf_queries_today': self.ecf_queries_today,
                'calendar_events_synced_today': self.calendar_events_synced_today
            },
            'errors': {
                'errors_today': self.errors_today,
                'warnings_today': self.warnings_today
            }
        }


class CourtSyncManager:
    """Main manager for the CourtSync calendar system."""
    
    def __init__(self, config: CourtSyncConfig, database_url: str, redis_url: Optional[str] = None):
        self.config = config
        self.status = CourtSyncStatus.INITIALIZING
        self.metrics = SystemMetrics()
        
        # Initialize core components
        self.hearing_detector = HearingDetector()
        self.calendar_sync_engine = CalendarSyncEngine(database_url, redis_url)
        self.sync_manager = SyncManager(self.calendar_sync_engine)
        self.court_data_manager = CourtDataIntegrationManager(self.hearing_detector)
        self.conflict_detector = ConflictDetector()
        self.conflict_resolver = ConflictResolver()
        self.legal_calendar_manager = LegalCalendarManager()
        
        # State tracking
        self.active_sync_tasks: Set[str] = set()
        self.last_sync_results: Dict[str, SyncResult] = {}
        self.event_cache: Dict[str, HearingEvent] = {}
        self.initialization_complete = False
        
        # Set up monitoring callbacks
        self.sync_manager.add_monitoring_callback(self._sync_monitoring_callback)
    
    async def initialize(self, 
                        court_configs: List[Tuple[CourtInfo, List[DataSourceConfig]]] = None,
                        calendar_configs: List[Tuple[str, CalendarConfig]] = None) -> bool:
        """Initialize the CourtSync system."""
        try:
            logger.info("Initializing CourtSync system...")
            
            # Load ML model if enabled
            if self.config.enable_ml_detection and self.config.ml_model_path:
                success = self.hearing_detector.load_ml_model(self.config.ml_model_path)
                if not success:
                    logger.warning("Failed to load ML model, continuing with rule-based detection")
            
            # Initialize court data sources
            if court_configs:
                await self._initialize_court_data_sources(court_configs)
            
            # Initialize calendar providers
            if calendar_configs:
                await self._initialize_calendar_providers(calendar_configs)
            
            # Set up business rules
            self._setup_business_rules()
            
            # Start scheduled sync if in automatic mode
            if self.config.sync_mode in [SyncMode.AUTOMATIC, SyncMode.SEMI_AUTOMATIC]:
                self._start_scheduled_sync()
            
            self.initialization_complete = True
            self.status = CourtSyncStatus.HEALTHY
            logger.info("CourtSync system initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize CourtSync system: {str(e)}")
            self.status = CourtSyncStatus.ERROR
            return False
    
    async def _initialize_court_data_sources(self, court_configs: List[Tuple[CourtInfo, List[DataSourceConfig]]]):
        """Initialize court data sources."""
        for court_info, data_source_configs in court_configs:
            # Register court
            self.court_data_manager.register_court(court_info)
            
            # Register data source providers
            for source_config in data_source_configs:
                if source_config.source_id not in self.config.court_data_sources:
                    continue  # Skip if not enabled in config
                
                # Create appropriate provider based on source type
                provider = await self._create_court_data_provider(source_config)
                if provider:
                    self.court_data_manager.register_provider(source_config.source_id, provider)
        
        # Initialize providers
        auth_results = await self.court_data_manager.initialize_providers()
        self.metrics.active_data_sources = sum(1 for success in auth_results.values() if success)
        logger.info(f"Initialized {self.metrics.active_data_sources} court data sources")
    
    async def _initialize_calendar_providers(self, calendar_configs: List[Tuple[str, CalendarConfig]]):
        """Initialize calendar providers."""
        auth_results = await self.legal_calendar_manager.initialize(calendar_configs)
        
        # Also register with sync engine
        for provider_name, config in calendar_configs:
            if auth_results.get(provider_name, False):
                # Create sync configuration
                sync_config = {
                    'direction': 'bidirectional',
                    'conflict_resolution': 'most_recent',
                    'sync_interval': self.config.sync_interval_minutes * 60,
                    'enabled': provider_name in self.config.calendar_providers
                }
                
                # Get the actual provider instance from legal calendar manager
                provider_info = self.legal_calendar_manager.sync_manager.providers.get(provider_name)
                if provider_info:
                    self.calendar_sync_engine.register_provider(
                        provider_name, 
                        provider_info['provider'], 
                        sync_config
                    )
        
        logger.info(f"Initialized {len([r for r in auth_results.values() if r])} calendar providers")
    
    async def _create_court_data_provider(self, config: DataSourceConfig):
        """Create appropriate court data provider based on configuration."""
        from .court_data_integration import PACERProvider, ECFProvider, StateCourtProvider
        
        try:
            if config.source_type.value == "pacer" and self.config.enable_pacer_integration:
                return PACERProvider(config)
            elif config.source_type.value == "ecf" and self.config.enable_ecf_integration:
                return ECFProvider(config)
            elif config.source_type.value == "state_ecf" and self.config.enable_state_courts:
                return StateCourtProvider(config)
            else:
                logger.warning(f"Unsupported or disabled data source type: {config.source_type.value}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to create provider for {config.source_id}: {str(e)}")
            return None
    
    def _setup_business_rules(self):
        """Set up business rules and constraints."""
        # Set court business hours
        self.conflict_detector.set_court_hours(
            "default", 
            self.config.business_hours_start, 
            self.config.business_hours_end
        )
        
        # Set travel buffer requirements
        # This would be expanded based on specific business requirements
        
        logger.info("Business rules configured")
    
    def _start_scheduled_sync(self):
        """Start scheduled synchronization."""
        self.sync_manager.start_scheduled_sync()
        logger.info(f"Scheduled sync started (interval: {self.config.sync_interval_minutes} minutes)")
    
    async def run_manual_sync(self) -> Dict[str, SyncResult]:
        """Run manual synchronization across all sources."""
        if not self.initialization_complete:
            logger.error("System not initialized, cannot run sync")
            return {}
        
        sync_start = datetime.now()
        logger.info("Starting manual sync...")
        
        try:
            # Sync calendar providers
            calendar_results = await self.calendar_sync_engine.sync_all_providers()
            
            # Update metrics
            self.metrics.total_syncs_today += len(calendar_results)
            successful_syncs = sum(1 for result in calendar_results.values() 
                                 if result.status == SyncStatus.SUCCESS)
            self.metrics.successful_syncs_today += successful_syncs
            self.metrics.failed_syncs_today += len(calendar_results) - successful_syncs
            
            if successful_syncs > 0:
                self.metrics.last_successful_sync = datetime.now()
            
            # Calculate average sync duration
            total_duration = sum(result.duration.total_seconds() 
                               for result in calendar_results.values() 
                               if result.duration)
            if calendar_results:
                self.metrics.avg_sync_duration_seconds = total_duration / len(calendar_results)
            
            logger.info(f"Manual sync completed in {(datetime.now() - sync_start).total_seconds():.1f} seconds")
            return calendar_results
        
        except Exception as e:
            logger.error(f"Manual sync failed: {str(e)}")
            self.metrics.failed_syncs_today += 1
            return {}
    
    async def detect_hearings_from_sources(self, 
                                         start_date: Optional[datetime] = None,
                                         end_date: Optional[datetime] = None) -> List[HearingEvent]:
        """Detect hearings from all configured court data sources."""
        if not self.initialization_complete:
            logger.error("System not initialized, cannot detect hearings")
            return []
        
        # Default date range: next 30 days
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=30)
        
        try:
            detected_hearings = await self.court_data_manager.detect_hearings_from_sources(
                start_date, end_date
            )
            
            # Filter by confidence threshold
            high_confidence_hearings = [
                h for h in detected_hearings 
                if h.confidence >= self.config.min_confidence_threshold
            ]
            
            # Update metrics
            self.metrics.hearings_detected_today += len(high_confidence_hearings)
            if high_confidence_hearings:
                avg_confidence = sum(h.confidence for h in high_confidence_hearings) / len(high_confidence_hearings)
                self.metrics.avg_detection_confidence = avg_confidence
            
            # Cache detected hearings
            for hearing in high_confidence_hearings:
                self.event_cache[hearing.hearing_id] = hearing
            
            logger.info(f"Detected {len(high_confidence_hearings)} high-confidence hearings")
            return high_confidence_hearings
        
        except Exception as e:
            logger.error(f"Failed to detect hearings: {str(e)}")
            self.metrics.errors_today += 1
            return []
    
    async def detect_and_resolve_conflicts(self, 
                                         events: Optional[List[Union[HearingEvent, Any]]] = None) -> Dict[str, Any]:
        """Detect and resolve calendar conflicts."""
        if not self.initialization_complete:
            logger.error("System not initialized, cannot detect conflicts")
            return {}
        
        try:
            # Use provided events or get from cache
            if events is None:
                events = list(self.event_cache.values())
            
            if not events:
                logger.warning("No events provided for conflict detection")
                return {'conflicts': [], 'resolutions': {}}
            
            # Detect conflicts
            conflicts = await self.conflict_detector.detect_conflicts(events)
            
            # Update metrics
            self.metrics.conflicts_detected_today += len(conflicts)
            critical_conflicts = sum(1 for c in conflicts if c.severity.value == 'critical')
            self.metrics.critical_conflicts += critical_conflicts
            
            resolution_results = {}
            
            # Resolve conflicts if enabled
            if self.config.conflict_resolution_enabled and conflicts:
                if self.config.sync_mode == SyncMode.AUTOMATIC:
                    # Automatically resolve all conflicts
                    resolution_results = await self.conflict_resolver.resolve_conflicts(conflicts)
                    resolved_count = sum(1 for status in resolution_results.values() 
                                       if status.value == 'resolved')
                    self.metrics.conflicts_resolved_today += resolved_count
                
                elif self.config.sync_mode == SyncMode.SEMI_AUTOMATIC:
                    # Auto-resolve non-critical conflicts, flag critical ones for manual review
                    auto_resolve_conflicts = [c for c in conflicts if c.severity.value != 'critical']
                    manual_conflicts = [c for c in conflicts if c.severity.value == 'critical']
                    
                    if auto_resolve_conflicts:
                        auto_results = await self.conflict_resolver.resolve_conflicts(auto_resolve_conflicts)
                        resolution_results.update(auto_results)
                        resolved_count = sum(1 for status in auto_results.values() 
                                           if status.value == 'resolved')
                        self.metrics.conflicts_resolved_today += resolved_count
                    
                    # Log manual conflicts for review
                    for conflict in manual_conflicts:
                        logger.warning(f"Critical conflict requires manual review: {conflict.conflict_id}")
                        resolution_results[conflict.conflict_id] = "manual_review_required"
            
            # Update pending conflicts metric
            self.metrics.pending_conflicts = len(self.conflict_resolver.get_pending_conflicts())
            
            logger.info(f"Detected {len(conflicts)} conflicts, resolved {len([r for r in resolution_results.values() if r == 'resolved'])}")
            
            return {
                'conflicts': [c.to_dict() for c in conflicts],
                'resolutions': resolution_results,
                'stats': self.conflict_resolver.get_conflict_stats()
            }
        
        except Exception as e:
            logger.error(f"Failed to detect/resolve conflicts: {str(e)}")
            self.metrics.errors_today += 1
            return {}
    
    async def create_calendar_events(self, hearings: List[HearingEvent]) -> Dict[str, str]:
        """Create calendar events for detected hearings."""
        if not self.initialization_complete:
            logger.error("System not initialized, cannot create calendar events")
            return {}
        
        try:
            created_events = {}
            
            for hearing in hearings:
                # Create deadline event if it's a deadline-related hearing
                if hearing.hearing_type in [HearingEvent.HearingType.MOTION_HEARING, HearingEvent.HearingType.HEARING]:
                    # Convert hearing to deadline data format
                    deadline_data = {
                        'deadline_id': hearing.hearing_id,
                        'title': f"{hearing.hearing_type.value.replace('_', ' ').title()}",
                        'due_date': hearing.date_time.isoformat(),
                        'case_name': hearing.case_title,
                        'case_id': hearing.case_number,
                        'priority': self._map_hearing_to_priority(hearing),
                        'description': hearing.description or f"Court hearing for {hearing.case_title}",
                        'consequences': f"Failure to appear may result in adverse ruling"
                    }
                    
                    # Create calendar event
                    event_id = await self.legal_calendar_manager.create_deadline_event(deadline_data)
                    created_events[hearing.hearing_id] = event_id
                
                # Create court event
                hearing_data = {
                    'hearing_id': hearing.hearing_id,
                    'title': hearing.case_title,
                    'start_time': hearing.date_time.isoformat(),
                    'end_time': (hearing.end_time or hearing.date_time + timedelta(hours=1)).isoformat(),
                    'case_name': hearing.case_title,
                    'judge': hearing.judge,
                    'courtroom': hearing.location.courtroom if hearing.location else None,
                    'location': hearing.location.court_name if hearing.location else None,
                    'hearing_type': hearing.hearing_type.value
                }
                
                court_event_id = await self.legal_calendar_manager.create_court_event(hearing_data)
                created_events[f"{hearing.hearing_id}_court"] = court_event_id
            
            self.metrics.calendar_events_synced_today += len(created_events)
            logger.info(f"Created {len(created_events)} calendar events")
            return created_events
        
        except Exception as e:
            logger.error(f"Failed to create calendar events: {str(e)}")
            self.metrics.errors_today += 1
            return {}
    
    def _map_hearing_to_priority(self, hearing: HearingEvent) -> str:
        """Map hearing type to priority level."""
        priority_map = {
            HearingType.TRIAL: 'critical',
            HearingType.MOTION_HEARING: 'high',
            HearingType.HEARING: 'high',
            HearingType.ORAL_ARGUMENT: 'high',
            HearingType.PRETRIAL_CONFERENCE: 'medium',
            HearingType.STATUS_CONFERENCE: 'medium',
            HearingType.SETTLEMENT_CONFERENCE: 'medium',
            HearingType.DEPOSITION: 'medium',
            HearingType.CASE_MANAGEMENT: 'low'
        }
        
        return priority_map.get(hearing.hearing_type, 'medium')
    
    async def _sync_monitoring_callback(self, provider_name: str, result: SyncResult):
        """Callback for monitoring sync results."""
        self.last_sync_results[provider_name] = result
        
        if result.status == SyncStatus.FAILED:
            self.metrics.errors_today += 1
            if self.config.notify_on_sync_failures:
                await self._notify_sync_failure(provider_name, result)
        
        if result.conflicts_detected > 0 and self.config.notify_on_conflicts:
            await self._notify_conflicts_detected(provider_name, result)
    
    async def _notify_sync_failure(self, provider_name: str, result: SyncResult):
        """Send notification about sync failure."""
        # This would integrate with notification systems
        logger.error(f"Sync failure notification for {provider_name}: {result.errors}")
    
    async def _notify_conflicts_detected(self, provider_name: str, result: SyncResult):
        """Send notification about detected conflicts."""
        # This would integrate with notification systems
        logger.warning(f"Conflicts detected in {provider_name}: {result.conflicts_detected}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'overall_status': self.status.value,
            'initialization_complete': self.initialization_complete,
            'config': self.config.to_dict(),
            'metrics': self.metrics.to_dict(),
            'components': {
                'hearing_detector': {
                    'ml_enabled': self.config.enable_ml_detection,
                    'ml_trained': self.hearing_detector.ml_classifier.is_trained,
                    'cached_events': len(self.event_cache)
                },
                'calendar_sync': {
                    'active_providers': len(self.calendar_sync_engine.providers),
                    'sync_manager_running': self.sync_manager.scheduler.running,
                    'last_sync_results': {
                        provider: result.status.value 
                        for provider, result in self.last_sync_results.items()
                    }
                },
                'court_data_integration': {
                    'active_sources': len(self.court_data_manager.providers),
                    'registered_courts': len(self.court_data_manager.courts)
                },
                'conflict_resolution': {
                    'pending_conflicts': len(self.conflict_resolver.get_pending_conflicts()),
                    'resolved_conflicts': len(self.conflict_resolver.get_resolved_conflicts()),
                    'resolution_rules': len(self.conflict_resolver.resolution_rules)
                }
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def get_health_check(self) -> Dict[str, Any]:
        """Get simple health check status."""
        health_status = "healthy"
        issues = []
        
        # Check component health
        if not self.initialization_complete:
            health_status = "initializing"
            issues.append("System initialization in progress")
        
        if self.status == CourtSyncStatus.ERROR:
            health_status = "unhealthy"
            issues.append("System in error state")
        
        if self.metrics.errors_today > 10:
            health_status = "degraded"
            issues.append(f"High error count today: {self.metrics.errors_today}")
        
        if self.metrics.critical_conflicts > 5:
            health_status = "degraded"
            issues.append(f"Multiple critical conflicts: {self.metrics.critical_conflicts}")
        
        # Check last sync time
        if (self.metrics.last_successful_sync and 
            datetime.now() - self.metrics.last_successful_sync > timedelta(hours=1)):
            health_status = "degraded"
            issues.append("No successful sync in over 1 hour")
        
        return {
            'status': health_status,
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'uptime_hours': (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)).total_seconds() / 3600,
            'metrics_summary': {
                'sync_success_rate': self.metrics.successful_syncs_today / max(self.metrics.total_syncs_today, 1) * 100,
                'conflict_resolution_rate': self.metrics.conflicts_resolved_today / max(self.metrics.conflicts_detected_today, 1) * 100,
                'active_data_sources': self.metrics.active_data_sources,
                'hearings_detected_today': self.metrics.hearings_detected_today
            }
        }
    
    async def run_comprehensive_sync(self) -> Dict[str, Any]:
        """Run comprehensive sync: detect hearings, sync calendars, resolve conflicts."""
        logger.info("Starting comprehensive sync...")
        sync_start = datetime.now()
        
        try:
            results = {
                'sync_started': sync_start.isoformat(),
                'steps_completed': [],
                'errors': [],
                'warnings': []
            }
            
            # Step 1: Detect hearings from court sources
            logger.info("Step 1: Detecting hearings from court sources")
            hearings = await self.detect_hearings_from_sources()
            results['hearings_detected'] = len(hearings)
            results['steps_completed'].append('hearing_detection')
            
            # Step 2: Sync with calendar providers
            logger.info("Step 2: Syncing with calendar providers")
            sync_results = await self.run_manual_sync()
            results['calendar_sync_results'] = {
                provider: result.status.value for provider, result in sync_results.items()
            }
            results['steps_completed'].append('calendar_sync')
            
            # Step 3: Detect and resolve conflicts
            logger.info("Step 3: Detecting and resolving conflicts")
            conflict_results = await self.detect_and_resolve_conflicts(hearings)
            results['conflicts'] = conflict_results
            results['steps_completed'].append('conflict_resolution')
            
            # Step 4: Create calendar events for new hearings
            logger.info("Step 4: Creating calendar events")
            new_hearings = [h for h in hearings if h.hearing_id not in self.event_cache]
            if new_hearings:
                created_events = await self.create_calendar_events(new_hearings)
                results['calendar_events_created'] = len(created_events)
                results['steps_completed'].append('event_creation')
            
            # Calculate total duration
            results['sync_completed'] = datetime.now().isoformat()
            results['total_duration_seconds'] = (datetime.now() - sync_start).total_seconds()
            
            logger.info(f"Comprehensive sync completed in {results['total_duration_seconds']:.1f} seconds")
            return results
        
        except Exception as e:
            logger.error(f"Comprehensive sync failed: {str(e)}")
            return {
                'sync_started': sync_start.isoformat(),
                'sync_failed': datetime.now().isoformat(),
                'error': str(e),
                'steps_completed': results.get('steps_completed', [])
            }
    
    async def shutdown(self):
        """Graceful shutdown of the CourtSync system."""
        logger.info("Shutting down CourtSync system...")
        
        # Stop scheduled sync
        self.sync_manager.stop_scheduled_sync()
        
        # Cleanup court data integration
        await self.court_data_manager.cleanup()
        
        # Cleanup legal calendar manager
        await self.legal_calendar_manager.shutdown()
        
        self.status = CourtSyncStatus.MAINTENANCE
        logger.info("CourtSync system shutdown complete")


# Example usage and configuration
async def example_usage():
    """Example usage of the CourtSync system."""
    
    # Create configuration
    config = CourtSyncConfig(
        sync_mode=SyncMode.SEMI_AUTOMATIC,
        sync_interval_minutes=15,
        enable_ml_detection=True,
        court_data_sources=['pacer_cacd', 'ecf_cacd'],
        calendar_providers=['google', 'outlook'],
        notify_on_conflicts=True,
        min_travel_buffer_minutes=30
    )
    
    # Initialize CourtSync manager
    manager = CourtSyncManager(
        config=config,
        database_url="sqlite:///courtsync.db",
        redis_url="redis://localhost:6379"
    )
    
    # Example court and calendar configurations
    from .court_data_integration import CourtInfo, DataSourceConfig, CourtSystem, DataSource
    from ..deadline_management.calendar_integration import CalendarConfig, CalendarProvider
    
    # Court configuration
    court_info = CourtInfo(
        court_id="cacd",
        name="US District Court for the Central District of California",
        system_type=CourtSystem.FEDERAL_DISTRICT,
        jurisdiction="California Central District",
        website="https://www.cacd.uscourts.gov",
        timezone="America/Los_Angeles"
    )
    
    pacer_config = DataSourceConfig(
        source_id="pacer_cacd",
        court_id="cacd",
        source_type=DataSource.PACER,
        url="https://pcl.uscourts.gov",
        credentials={
            'username': 'your_username',
            'password': 'your_password'
        }
    )
    
    court_configs = [(court_info, [pacer_config])]
    
    # Calendar configuration
    google_config = CalendarConfig(
        provider=CalendarProvider.GOOGLE,
        credentials={
            'client_id': 'your_client_id',
            'client_secret': 'your_client_secret'
        },
        timezone='America/Los_Angeles'
    )
    
    calendar_configs = [('google', google_config)]
    
    # Initialize system
    success = await manager.initialize(court_configs, calendar_configs)
    if not success:
        print("Failed to initialize CourtSync system")
        return
    
    # Get system status
    status = manager.get_system_status()
    print("System Status:")
    print(json.dumps(status, indent=2))
    
    # Run comprehensive sync
    sync_results = await manager.run_comprehensive_sync()
    print("\nSync Results:")
    print(json.dumps(sync_results, indent=2))
    
    # Get health check
    health = manager.get_health_check()
    print("\nHealth Check:")
    print(json.dumps(health, indent=2))
    
    # Cleanup
    await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(example_usage())