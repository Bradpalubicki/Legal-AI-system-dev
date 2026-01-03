"""
Centralized alert management system that coordinates real-time monitoring, alert generation, and delivery.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import json
from sqlalchemy.orm import Session

from ..shared.database.models import Case, User, TranscriptSegment, CourtSession
from ..shared.database.connection import get_db
from .alert_system import AlertSystem, Alert, AlertType, AlertSeverity, AlertRule, AlertRecipient
from .alert_dispatcher import AlertDispatcher, DeliveryConfig
from .comprehensive_analyzer import ComprehensiveAnalyzer
from .statement_analyzer import StatementAnalyzer, IdentifiedStatement
from .legal_analyzer import LegalAnalyzer, LegalEvent
from .key_moment_detector import KeyMomentDetector, KeyMoment


@dataclass
class AlertConfiguration:
    """Configuration for the alert management system."""
    enable_real_time_alerts: bool = True
    enable_batch_processing: bool = True
    max_alerts_per_minute: int = 10
    alert_cooldown_minutes: int = 5
    auto_escalation_enabled: bool = True
    emergency_contacts: List[str] = None
    business_hours_only: bool = False
    weekend_alerts: bool = True
    
    def __post_init__(self):
        if self.emergency_contacts is None:
            self.emergency_contacts = []


class AlertManager:
    """Centralized alert management system for real-time courtroom monitoring."""
    
    def __init__(self, config: AlertConfiguration, delivery_config: DeliveryConfig):
        self.config = config
        self.alert_system = AlertSystem()
        self.alert_dispatcher = AlertDispatcher(delivery_config)
        self.comprehensive_analyzer = ComprehensiveAnalyzer()
        
        # Processing components
        self.statement_analyzer = StatementAnalyzer()
        self.legal_analyzer = LegalAnalyzer()
        self.moment_detector = KeyMomentDetector()
        
        # Alert management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.alert_buffer: Dict[str, List[Alert]] = {}
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.alert_rate_limiter: Dict[str, List[datetime]] = {}
        
        # Monitoring and stats
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        self.alert_metrics: Dict[str, int] = {
            "total_alerts": 0,
            "critical_alerts": 0,
            "alerts_sent": 0,
            "alerts_acknowledged": 0,
            "false_positives": 0
        }
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

    async def start_alert_manager(self):
        """Start the alert management system."""
        try:
            print("Starting alert management system...")
            
            # Start dispatcher
            await self.alert_dispatcher.start_dispatcher()
            
            # Start processing worker
            asyncio.create_task(self._alert_processing_worker())
            
            # Start monitoring tasks
            asyncio.create_task(self._rate_limit_cleaner())
            asyncio.create_task(self._session_monitor())
            
            print("Alert management system started successfully")
            
        except Exception as e:
            print(f"Error starting alert manager: {e}")
            raise

    async def register_court_session(
        self, 
        session_id: str, 
        case: Case, 
        participants: List[User],
        alert_rules: Optional[List[AlertRule]] = None
    ):
        """Register a new court session for real-time monitoring."""
        try:
            print(f"Registering court session {session_id} for case {case.id}")
            
            # Initialize session tracking
            self.active_sessions[session_id] = {
                "case": case,
                "participants": participants,
                "start_time": datetime.now(),
                "last_activity": datetime.now(),
                "segment_count": 0,
                "alert_count": 0,
                "status": "active"
            }
            
            # Initialize session stats
            self.session_stats[session_id] = {
                "total_segments": 0,
                "alerts_generated": 0,
                "critical_alerts": 0,
                "avg_response_time": 0.0,
                "last_alert": None
            }
            
            # Setup alert rules for session
            if alert_rules:
                for rule in alert_rules:
                    self.alert_system.add_alert_rule(rule)
            
            # Setup recipients for case participants
            await self._setup_session_recipients(session_id, participants)
            
            print(f"Court session {session_id} registered successfully")
            
        except Exception as e:
            print(f"Error registering court session: {e}")
            raise

    async def process_real_time_segment(
        self, 
        session_id: str, 
        segment: TranscriptSegment
    ) -> Dict[str, Any]:
        """Process a real-time transcript segment and generate alerts."""
        try:
            if session_id not in self.active_sessions:
                print(f"Session {session_id} not registered")
                return {"alerts": [], "requires_attention": False}
            
            session_info = self.active_sessions[session_id]
            case = session_info["case"]
            
            # Update session activity
            session_info["last_activity"] = datetime.now()
            session_info["segment_count"] += 1
            self.session_stats[session_id]["total_segments"] += 1
            
            # Check rate limiting
            if not self._check_rate_limit(session_id):
                print(f"Rate limit exceeded for session {session_id}")
                return {"alerts": [], "rate_limited": True}
            
            # Perform comprehensive analysis
            analysis_results = await self._analyze_segment_comprehensive(segment, case)
            
            # Generate alerts based on analysis
            alerts = await self._generate_alerts_from_analysis(
                segment, case, analysis_results, session_id
            )
            
            # Process and send alerts
            processed_alerts = []
            for alert in alerts:
                # Add to processing queue
                await self.processing_queue.put((alert, session_id))
                processed_alerts.append({
                    "alert_id": alert.alert_id,
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "requires_response": alert.requires_response
                })
            
            # Update session stats
            session_info["alert_count"] += len(alerts)
            self.session_stats[session_id]["alerts_generated"] += len(alerts)
            self.session_stats[session_id]["critical_alerts"] += len([
                a for a in alerts if a.severity == AlertSeverity.CRITICAL
            ])
            
            if alerts:
                self.session_stats[session_id]["last_alert"] = datetime.now().isoformat()
            
            # Check if session requires immediate attention
            requires_attention = any(
                alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH] 
                for alert in alerts
            )
            
            # Trigger event handlers
            await self._trigger_event_handlers("segment_processed", {
                "session_id": session_id,
                "segment": segment,
                "alerts": alerts,
                "analysis": analysis_results
            })
            
            return {
                "alerts": processed_alerts,
                "requires_attention": requires_attention,
                "analysis_summary": self._create_analysis_summary(analysis_results),
                "session_stats": self.session_stats[session_id]
            }
            
        except Exception as e:
            print(f"Error processing real-time segment: {e}")
            return {"alerts": [], "error": str(e)}

    async def _analyze_segment_comprehensive(
        self, 
        segment: TranscriptSegment, 
        case: Case
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis of the segment."""
        try:
            # Parallel analysis
            analysis_tasks = [
                self.legal_analyzer.analyze_transcript_segment(segment, case),
                self.statement_analyzer.analyze_transcript_segment(segment, case),
                self.moment_detector.analyze_segment_for_moments(segment, case)
            ]
            
            legal_events, statements, moments = await asyncio.gather(
                *analysis_tasks, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(legal_events, Exception):
                print(f"Legal analysis error: {legal_events}")
                legal_events = []
            
            if isinstance(statements, Exception):
                print(f"Statement analysis error: {statements}")
                statements = []
                
            if isinstance(moments, Exception):
                print(f"Moment detection error: {moments}")
                moments = []
            
            return {
                "legal_events": legal_events,
                "statements": statements,
                "moments": moments,
                "segment_quality": segment.confidence,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in comprehensive analysis: {e}")
            return {"legal_events": [], "statements": [], "moments": []}

    async def _generate_alerts_from_analysis(
        self, 
        segment: TranscriptSegment, 
        case: Case, 
        analysis: Dict[str, Any],
        session_id: str
    ) -> List[Alert]:
        """Generate alerts based on analysis results."""
        try:
            alerts = []
            
            # Process through alert system
            system_alerts = await self.alert_system.process_transcript_segment(
                segment, case, 
                analysis.get("legal_events", []),
                analysis.get("statements", []),
                analysis.get("moments", [])
            )
            
            alerts.extend(system_alerts)
            
            # Additional custom alert logic
            custom_alerts = await self._generate_custom_alerts(
                segment, case, analysis, session_id
            )
            alerts.extend(custom_alerts)
            
            return alerts
            
        except Exception as e:
            print(f"Error generating alerts from analysis: {e}")
            return []

    async def _generate_custom_alerts(
        self, 
        segment: TranscriptSegment, 
        case: Case, 
        analysis: Dict[str, Any],
        session_id: str
    ) -> List[Alert]:
        """Generate custom alerts based on specific patterns or conditions."""
        try:
            alerts = []
            
            # Check for multiple critical events in short timespan
            session_info = self.active_sessions[session_id]
            recent_segments_window = 5  # Last 5 segments
            
            if session_info["segment_count"] > recent_segments_window:
                # Logic for detecting patterns across multiple segments
                pass
            
            # Check for unusual speaker patterns
            if self._detect_unusual_speaker_pattern(segment, session_info):
                alert = await self._create_custom_alert(
                    AlertType.PROCEDURAL_VIOLATION,
                    "Unusual Speaker Pattern Detected",
                    f"Irregular speaking pattern detected from {segment.speaker}",
                    segment, case, AlertSeverity.MEDIUM
                )
                alerts.append(alert)
            
            # Check for audio quality issues
            if segment.confidence < 0.5:
                alert = await self._create_custom_alert(
                    AlertType.PROCEDURAL_VIOLATION,
                    "Audio Quality Issues",
                    f"Low audio quality detected (confidence: {segment.confidence:.2f})",
                    segment, case, AlertSeverity.LOW
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            print(f"Error generating custom alerts: {e}")
            return []

    def _detect_unusual_speaker_pattern(
        self, 
        segment: TranscriptSegment, 
        session_info: Dict[str, Any]
    ) -> bool:
        """Detect unusual speaking patterns that might indicate issues."""
        try:
            # Example: Detect if someone is speaking out of turn
            # This would require more sophisticated logic based on court procedures
            return False
            
        except Exception as e:
            print(f"Error detecting speaker pattern: {e}")
            return False

    async def _create_custom_alert(
        self, 
        alert_type: AlertType, 
        title: str, 
        message: str,
        segment: TranscriptSegment, 
        case: Case, 
        severity: AlertSeverity
    ) -> Alert:
        """Create a custom alert."""
        import uuid
        
        return Alert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details={
                "segment_text": segment.text,
                "speaker": segment.speaker,
                "timestamp": segment.timestamp
            },
            case_id=case.id,
            session_id=getattr(segment, 'session_id', None),
            timestamp=datetime.now(),
            source_segment=segment,
            recipients=[],  # Will be populated by alert system
            channels=[],    # Will be populated by alert system
            status=self.alert_system.AlertStatus.PENDING
        )

    async def _alert_processing_worker(self):
        """Background worker for processing and sending alerts."""
        while True:
            try:
                # Get alert from queue
                alert, session_id = await self.processing_queue.get()
                
                # Send alert via dispatcher
                delivery_results = await self.alert_dispatcher.dispatch_alert(alert)
                
                # Update alert metrics
                self.alert_metrics["total_alerts"] += 1
                if alert.severity == AlertSeverity.CRITICAL:
                    self.alert_metrics["critical_alerts"] += 1
                
                if any(delivery_results.values()):
                    self.alert_metrics["alerts_sent"] += 1
                
                # Log delivery results
                successful_channels = [ch for ch, success in delivery_results.items() if success]
                failed_channels = [ch for ch, success in delivery_results.items() if not success]
                
                if successful_channels:
                    print(f"Alert {alert.alert_id} delivered via: {', '.join(successful_channels)}")
                
                if failed_channels:
                    print(f"Alert {alert.alert_id} failed to deliver via: {', '.join(failed_channels)}")
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except Exception as e:
                print(f"Error in alert processing worker: {e}")
                await asyncio.sleep(1)

    def _check_rate_limit(self, session_id: str) -> bool:
        """Check if session is within rate limits."""
        try:
            if not self.config.enable_real_time_alerts:
                return False
            
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(minutes=1)
            
            # Initialize if not exists
            if session_id not in self.alert_rate_limiter:
                self.alert_rate_limiter[session_id] = []
            
            # Remove old entries
            self.alert_rate_limiter[session_id] = [
                timestamp for timestamp in self.alert_rate_limiter[session_id]
                if timestamp > cutoff_time
            ]
            
            # Check limit
            if len(self.alert_rate_limiter[session_id]) >= self.config.max_alerts_per_minute:
                return False
            
            # Add current timestamp
            self.alert_rate_limiter[session_id].append(current_time)
            return True
            
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return True  # Allow on error

    async def _rate_limit_cleaner(self):
        """Clean up old rate limit entries."""
        while True:
            try:
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(minutes=5)
                
                for session_id in list(self.alert_rate_limiter.keys()):
                    self.alert_rate_limiter[session_id] = [
                        timestamp for timestamp in self.alert_rate_limiter[session_id]
                        if timestamp > cutoff_time
                    ]
                    
                    # Remove empty entries
                    if not self.alert_rate_limiter[session_id]:
                        del self.alert_rate_limiter[session_id]
                
                await asyncio.sleep(60)  # Clean every minute
                
            except Exception as e:
                print(f"Error in rate limit cleaner: {e}")
                await asyncio.sleep(60)

    async def _session_monitor(self):
        """Monitor session health and activity."""
        while True:
            try:
                current_time = datetime.now()
                inactive_threshold = timedelta(minutes=30)
                
                for session_id, session_info in list(self.active_sessions.items()):
                    last_activity = session_info["last_activity"]
                    
                    if current_time - last_activity > inactive_threshold:
                        print(f"Session {session_id} appears inactive, marking for cleanup")
                        session_info["status"] = "inactive"
                        
                        # Could implement automatic cleanup here
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Error in session monitor: {e}")
                await asyncio.sleep(300)

    async def _setup_session_recipients(self, session_id: str, participants: List[User]):
        """Setup alert recipients for a session."""
        try:
            for user in participants:
                recipient = AlertRecipient(
                    user_id=str(user.id),
                    name=f"{user.first_name} {user.last_name}",
                    role=user.role,
                    channels=[
                        self.alert_dispatcher.AlertChannel.PUSH_NOTIFICATION,
                        self.alert_dispatcher.AlertChannel.EMAIL,
                        self.alert_dispatcher.AlertChannel.WEBSOCKET
                    ],
                    alert_types=list(AlertType),
                    severity_threshold=AlertSeverity.MEDIUM,
                    contact_info={
                        "email": user.email,
                        "phone": getattr(user, 'phone', None)
                    }
                )
                
                self.alert_system.add_recipient(recipient)
                
        except Exception as e:
            print(f"Error setting up session recipients: {e}")

    def _create_analysis_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of analysis results."""
        return {
            "legal_events_count": len(analysis.get("legal_events", [])),
            "statements_count": len(analysis.get("statements", [])),
            "key_moments_count": len(analysis.get("moments", [])),
            "segment_quality": analysis.get("segment_quality", 0.0),
            "high_impact_items": len([
                item for items in [
                    analysis.get("moments", []), 
                    analysis.get("statements", [])
                ] for item in items
                if hasattr(item, 'impact_level') and item.impact_level.value in ['case_changing', 'highly_significant']
            ])
        }

    async def _trigger_event_handlers(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger registered event handlers."""
        try:
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event_data)
                        else:
                            handler(event_data)
                    except Exception as e:
                        print(f"Error in event handler: {e}")
                        
        except Exception as e:
            print(f"Error triggering event handlers: {e}")

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def acknowledge_alert(self, alert_id: str, user_id: str, response: Optional[str] = None) -> bool:
        """Acknowledge an alert."""
        success = self.alert_system.acknowledge_alert(alert_id, user_id, response)
        if success:
            self.alert_metrics["alerts_acknowledged"] += 1
        return success

    async def resolve_alert(self, alert_id: str, user_id: str, resolution_notes: Optional[str] = None) -> bool:
        """Resolve an alert."""
        return self.alert_system.resolve_alert(alert_id, user_id, resolution_notes)

    def mark_false_positive(self, alert_id: str, user_id: str, reason: str):
        """Mark an alert as a false positive for ML training."""
        self.alert_metrics["false_positives"] += 1
        # Would implement ML feedback loop here

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific session."""
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id]
            stats = self.session_stats.get(session_id, {})
            
            return {
                "session_id": session_id,
                "case_id": session_info["case"].id,
                "status": session_info["status"],
                "start_time": session_info["start_time"].isoformat(),
                "last_activity": session_info["last_activity"].isoformat(),
                "duration_minutes": (datetime.now() - session_info["start_time"]).total_seconds() / 60,
                "segment_count": session_info["segment_count"],
                "alert_count": session_info["alert_count"],
                "stats": stats
            }
        return None

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide alert metrics."""
        return {
            "alert_metrics": self.alert_metrics,
            "active_sessions": len(self.active_sessions),
            "processing_queue_size": self.processing_queue.qsize(),
            "delivery_stats": self.alert_dispatcher.get_delivery_statistics(),
            "alert_system_stats": self.alert_system.get_alert_statistics()
        }

    async def shutdown(self):
        """Shutdown the alert management system gracefully."""
        try:
            print("Shutting down alert management system...")
            
            # Mark all sessions as inactive
            for session_info in self.active_sessions.values():
                session_info["status"] = "shutdown"
            
            # Wait for processing queue to empty
            await self.processing_queue.join()
            
            # Shutdown dispatcher
            await self.alert_dispatcher.shutdown()
            
            print("Alert management system shut down successfully")
            
        except Exception as e:
            print(f"Error shutting down alert manager: {e}")

    async def export_session_report(self, session_id: str) -> Optional[str]:
        """Export a comprehensive session report including all alerts."""
        try:
            if session_id not in self.active_sessions:
                return None
            
            session_info = self.active_sessions[session_id]
            stats = self.session_stats.get(session_id, {})
            
            # Get session alerts
            session_alerts = [
                alert for alert in self.alert_system.alert_history
                if alert.session_id == session_id
            ]
            
            report = f"""
# Court Session Alert Report

**Session ID:** {session_id}
**Case:** {session_info['case'].title} ({session_info['case'].case_type})
**Date:** {session_info['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {(datetime.now() - session_info['start_time']).total_seconds() / 3600:.1f} hours

## Session Statistics

- **Total Segments:** {stats.get('total_segments', 0)}
- **Alerts Generated:** {stats.get('alerts_generated', 0)}
- **Critical Alerts:** {stats.get('critical_alerts', 0)}
- **Last Alert:** {stats.get('last_alert', 'None')}

## Alert Summary

**By Type:**
{chr(10).join([f"- {alert.alert_type.value}: {len([a for a in session_alerts if a.alert_type == alert.alert_type])}" for alert in session_alerts])}

**By Severity:**
{chr(10).join([f"- {severity.value}: {len([a for a in session_alerts if a.severity == severity])}" for severity in AlertSeverity])}

## Critical Alerts

{chr(10).join([f"- {alert.timestamp.strftime('%H:%M:%S')} - {alert.title}" for alert in session_alerts if alert.severity == AlertSeverity.CRITICAL])}

---
*Report generated by Legal AI Alert Management System*
"""
            
            return report
            
        except Exception as e:
            print(f"Error exporting session report: {e}")
            return None