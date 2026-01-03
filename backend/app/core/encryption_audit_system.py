"""
COMPREHENSIVE ENCRYPTION AUDIT SYSTEM

Enterprise-grade audit system for all encryption operations, key usage tracking,
compliance reporting, and security event monitoring.

CRITICAL: Provides complete audit trail for legal compliance and security monitoring.
"""

import os
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    # Encryption operations
    DOCUMENT_ENCRYPTED = "document_encrypted"
    DOCUMENT_DECRYPTED = "document_decrypted"
    ENCRYPTION_FAILED = "encryption_failed"
    DECRYPTION_FAILED = "decryption_failed"
    
    # Key management
    KEY_CREATED = "key_created"
    KEY_ACCESSED = "key_accessed"
    KEY_ROTATED = "key_rotated"
    KEY_DEPRECATED = "key_deprecated"
    KEY_REVOKED = "key_revoked"
    
    # Backup operations
    BACKUP_ENCRYPTED = "backup_encrypted"
    BACKUP_DECRYPTED = "backup_decrypted"
    BACKUP_VERIFIED = "backup_verified"
    
    # Security events
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    KEY_COMPROMISE_SUSPECTED = "key_compromise_suspected"
    VERIFICATION_FAILURE = "verification_failure"
    SECURITY_ALERT = "security_alert"
    
    # Compliance events
    COMPLIANCE_CHECK = "compliance_check"
    RETENTION_POLICY_APPLIED = "retention_policy_applied"
    DATA_EXPORT_REQUEST = "data_export_request"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGE = "configuration_change"

class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"

@dataclass
class AuditEvent:
    """Individual audit event record"""
    event_id: str
    event_type: AuditEventType
    event_level: AuditLevel
    timestamp: datetime
    user_id: Optional[str]
    client_id: Optional[str]
    matter_id: Optional[str]
    document_id: Optional[str]
    key_id: Optional[str]
    source_service: str
    source_function: str
    event_details: Dict[str, Any]
    security_context: Dict[str, Any]
    compliance_flags: List[str]
    retention_until: datetime

@dataclass
class ComplianceReport:
    """Compliance audit report"""
    report_id: str
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_events: int
    encryption_operations: int
    key_operations: int
    security_events: int
    compliance_violations: int
    recommendations: List[str]
    detailed_findings: Dict[str, Any]

class EncryptionAuditSystem:
    """Comprehensive audit system for encryption operations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # Initialize audit database
        self.db_path = Path(self.config['audit_db_path'])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_audit_database()
        
        # Event buffer for high-performance logging
        self._event_buffer = []
        self._buffer_lock = threading.RLock()
        self._max_buffer_size = 1000
        
        # Statistics tracking
        self.event_stats = defaultdict(int)
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        
        # Compliance tracking
        self.compliance_violations = []
        self.retention_policies = self._load_retention_policies()
        
        # Auto-flush buffer periodically
        self._start_buffer_flush_thread()
        
        logger.info("[AUDIT_SYSTEM] Encryption audit system initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default audit configuration"""
        return {
            'audit_db_path': 'audit/encryption_audit.db',
            'retention_days_default': 2555,  # 7 years for legal compliance
            'retention_days_security': 3650,  # 10 years for security events
            'buffer_flush_interval_seconds': 60,
            'enable_real_time_monitoring': True,
            'compliance_checks_enabled': True,
            'export_format': 'json',
            'encryption_at_rest': True
        }
    
    def _init_audit_database(self):
        """Initialize audit database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    event_level TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    client_id TEXT,
                    matter_id TEXT,
                    document_id TEXT,
                    key_id TEXT,
                    source_service TEXT NOT NULL,
                    source_function TEXT NOT NULL,
                    event_details TEXT NOT NULL,
                    security_context TEXT,
                    compliance_flags TEXT,
                    retention_until TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS compliance_reports (
                    report_id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    report_data TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS key_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_id TEXT NOT NULL,
                    access_type TEXT NOT NULL,
                    accessed_by TEXT,
                    accessed_at TEXT NOT NULL,
                    client_id TEXT,
                    matter_id TEXT,
                    access_granted BOOLEAN NOT NULL,
                    failure_reason TEXT
                );
                
                CREATE TABLE IF NOT EXISTS failed_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    document_id TEXT,
                    key_id TEXT,
                    failure_reason TEXT NOT NULL,
                    failed_at TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    resolved BOOLEAN DEFAULT FALSE
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_audit_client_matter ON audit_events(client_id, matter_id);
                CREATE INDEX IF NOT EXISTS idx_audit_document_id ON audit_events(document_id);
                CREATE INDEX IF NOT EXISTS idx_audit_key_id ON audit_events(key_id);
                CREATE INDEX IF NOT EXISTS idx_key_access_key_id ON key_access_log(key_id);
                CREATE INDEX IF NOT EXISTS idx_key_access_time ON key_access_log(accessed_at);
            """)
            conn.commit()
    
    def log_event(self, event_type: AuditEventType, event_details: Dict[str, Any],
                  event_level: AuditLevel = AuditLevel.INFO,
                  user_id: Optional[str] = None,
                  client_id: Optional[str] = None,
                  matter_id: Optional[str] = None,
                  document_id: Optional[str] = None,
                  key_id: Optional[str] = None,
                  source_service: str = "encryption_service",
                  source_function: str = "unknown") -> str:
        """Log audit event with comprehensive details"""
        
        # Generate unique event ID
        event_id = f"{event_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Determine retention period
        retention_days = self.retention_policies.get(
            event_type.value, 
            self.config['retention_days_security' if event_level == AuditLevel.SECURITY else 'retention_days_default']
        )
        retention_until = datetime.utcnow() + timedelta(days=retention_days)
        
        # Gather security context
        security_context = {
            'process_id': os.getpid(),
            'thread_id': threading.get_ident(),
            'timestamp_utc': datetime.utcnow().isoformat(),
            'hostname': os.environ.get('COMPUTERNAME', 'unknown')
        }
        
        # Determine compliance flags
        compliance_flags = self._determine_compliance_flags(event_type, event_details)
        
        # Create audit event
        audit_event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            event_level=event_level,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_id=client_id,
            matter_id=matter_id,
            document_id=document_id,
            key_id=key_id,
            source_service=source_service,
            source_function=source_function,
            event_details=event_details,
            security_context=security_context,
            compliance_flags=compliance_flags,
            retention_until=retention_until
        )
        
        # Add to buffer for batch processing
        with self._buffer_lock:
            self._event_buffer.append(audit_event)
            
            # Flush buffer if it's getting full
            if len(self._event_buffer) >= self._max_buffer_size:
                self._flush_event_buffer()
        
        # Update statistics
        self.event_stats[event_type.value] += 1
        today = datetime.utcnow().date().isoformat()
        self.daily_stats[today][event_type.value] += 1
        
        # Log to system logger for real-time monitoring
        if self.config['enable_real_time_monitoring']:
            logger.log(
                getattr(logging, event_level.value.upper()),
                f"[AUDIT] {event_type.value}: {json.dumps(event_details)}"
            )
        
        return event_id
    
    def log_key_access(self, key_id: str, access_type: str, accessed_by: str = None,
                       client_id: str = None, matter_id: str = None,
                       access_granted: bool = True, failure_reason: str = None):
        """Log key access attempt"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO key_access_log 
                   (key_id, access_type, accessed_by, accessed_at, client_id, matter_id, 
                    access_granted, failure_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (key_id, access_type, accessed_by, datetime.utcnow().isoformat(),
                 client_id, matter_id, access_granted, failure_reason)
            )
            conn.commit()
        
        # Also log as audit event
        self.log_event(
            AuditEventType.KEY_ACCESSED,
            {
                'key_id': key_id,
                'access_type': access_type,
                'accessed_by': accessed_by,
                'access_granted': access_granted,
                'failure_reason': failure_reason
            },
            event_level=AuditLevel.SECURITY if not access_granted else AuditLevel.INFO,
            client_id=client_id,
            matter_id=matter_id,
            key_id=key_id
        )
    
    def log_failed_operation(self, operation_type: str, document_id: str = None,
                           key_id: str = None, failure_reason: str = None) -> int:
        """Log failed encryption/decryption operation"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO failed_operations 
                   (operation_type, document_id, key_id, failure_reason, failed_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (operation_type, document_id, key_id, failure_reason, datetime.utcnow().isoformat())
            )
            failure_id = cursor.lastrowid
            conn.commit()
        
        # Log as audit event
        self.log_event(
            AuditEventType.ENCRYPTION_FAILED if 'encrypt' in operation_type.lower() else AuditEventType.DECRYPTION_FAILED,
            {
                'operation_type': operation_type,
                'document_id': document_id,
                'key_id': key_id,
                'failure_reason': failure_reason,
                'failure_id': failure_id
            },
            event_level=AuditLevel.ERROR,
            document_id=document_id,
            key_id=key_id
        )
        
        return failure_id
    
    def track_decryption_attempts(self, document_id: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Track decryption attempts for suspicious activity detection"""
        
        start_time = (datetime.utcnow() - timedelta(minutes=time_window_minutes)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Count total decryption attempts
            cursor = conn.execute(
                """SELECT COUNT(*) FROM audit_events 
                   WHERE document_id = ? AND event_type = ? AND timestamp > ?""",
                (document_id, AuditEventType.DOCUMENT_DECRYPTED.value, start_time)
            )
            total_attempts = cursor.fetchone()[0]
            
            # Count failed attempts
            cursor = conn.execute(
                """SELECT COUNT(*) FROM failed_operations 
                   WHERE document_id = ? AND operation_type LIKE '%decrypt%' AND failed_at > ?""",
                (document_id, start_time)
            )
            failed_attempts = cursor.fetchone()[0]
            
            # Get unique users/sources
            cursor = conn.execute(
                """SELECT DISTINCT user_id, source_service FROM audit_events 
                   WHERE document_id = ? AND event_type = ? AND timestamp > ?""",
                (document_id, AuditEventType.DOCUMENT_DECRYPTED.value, start_time)
            )
            unique_sources = cursor.fetchall()
        
        analysis = {
            'document_id': document_id,
            'time_window_minutes': time_window_minutes,
            'total_attempts': total_attempts,
            'failed_attempts': failed_attempts,
            'success_rate': (total_attempts - failed_attempts) / max(total_attempts, 1),
            'unique_sources': len(unique_sources),
            'sources': unique_sources
        }
        
        # Check for suspicious patterns
        if failed_attempts > 10:  # More than 10 failures in time window
            self.log_event(
                AuditEventType.SECURITY_ALERT,
                {
                    'alert_type': 'HIGH_DECRYPTION_FAILURE_RATE',
                    'document_id': document_id,
                    'failed_attempts': failed_attempts,
                    'time_window_minutes': time_window_minutes
                },
                event_level=AuditLevel.SECURITY,
                document_id=document_id
            )
            analysis['security_alert'] = True
        
        if len(unique_sources) > 5:  # Many different sources accessing same document
            self.log_event(
                AuditEventType.SECURITY_ALERT,
                {
                    'alert_type': 'MULTIPLE_ACCESS_SOURCES',
                    'document_id': document_id,
                    'unique_sources': len(unique_sources),
                    'time_window_minutes': time_window_minutes
                },
                event_level=AuditLevel.SECURITY,
                document_id=document_id
            )
            analysis['security_alert'] = True
        
        return analysis
    
    def generate_compliance_report(self, report_type: str, start_date: datetime, 
                                  end_date: datetime, client_id: str = None,
                                  matter_id: str = None) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        
        report_id = f"{report_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        with sqlite3.connect(self.db_path) as conn:
            # Base query conditions
            conditions = ["timestamp BETWEEN ? AND ?"]
            params = [start_date.isoformat(), end_date.isoformat()]
            
            if client_id:
                conditions.append("client_id = ?")
                params.append(client_id)
            
            if matter_id:
                conditions.append("matter_id = ?")
                params.append(matter_id)
            
            where_clause = " AND ".join(conditions)
            
            # Total events
            cursor = conn.execute(f"SELECT COUNT(*) FROM audit_events WHERE {where_clause}", params)
            total_events = cursor.fetchone()[0]
            
            # Encryption operations
            cursor = conn.execute(
                f"""SELECT COUNT(*) FROM audit_events 
                    WHERE {where_clause} AND event_type IN (?, ?)""",
                params + [AuditEventType.DOCUMENT_ENCRYPTED.value, AuditEventType.DOCUMENT_DECRYPTED.value]
            )
            encryption_operations = cursor.fetchone()[0]
            
            # Key operations
            cursor = conn.execute(
                f"""SELECT COUNT(*) FROM audit_events 
                    WHERE {where_clause} AND event_type LIKE 'key_%'""",
                params
            )
            key_operations = cursor.fetchone()[0]
            
            # Security events
            cursor = conn.execute(
                f"""SELECT COUNT(*) FROM audit_events 
                    WHERE {where_clause} AND event_level = ?""",
                params + [AuditLevel.SECURITY.value]
            )
            security_events = cursor.fetchone()[0]
            
            # Compliance violations (events with compliance flags)
            cursor = conn.execute(
                f"""SELECT COUNT(*) FROM audit_events 
                    WHERE {where_clause} AND compliance_flags IS NOT NULL AND compliance_flags != '[]'""",
                params
            )
            compliance_violations = cursor.fetchone()[0]
            
            # Detailed findings
            cursor = conn.execute(
                f"""SELECT event_type, COUNT(*) as count FROM audit_events 
                    WHERE {where_clause} GROUP BY event_type ORDER BY count DESC""",
                params
            )
            event_breakdown = dict(cursor.fetchall())
            
            # Failed operations
            cursor = conn.execute(
                f"""SELECT operation_type, COUNT(*) as count FROM failed_operations 
                    WHERE failed_at BETWEEN ? AND ? GROUP BY operation_type""",
                [start_date.isoformat(), end_date.isoformat()]
            )
            failure_breakdown = dict(cursor.fetchall())
        
        # Generate recommendations
        recommendations = []
        
        if compliance_violations > 0:
            recommendations.append(f"Review and address {compliance_violations} compliance violations")
        
        if security_events > total_events * 0.1:  # More than 10% security events
            recommendations.append("High number of security events detected - review security posture")
        
        if sum(failure_breakdown.values()) > encryption_operations * 0.05:  # More than 5% failure rate
            recommendations.append("Encryption failure rate is high - investigate system reliability")
        
        # Detailed findings
        detailed_findings = {
            'event_breakdown': event_breakdown,
            'failure_breakdown': failure_breakdown,
            'time_period_days': (end_date - start_date).days,
            'average_daily_events': total_events / max((end_date - start_date).days, 1),
            'client_scope': client_id,
            'matter_scope': matter_id
        }
        
        # Create compliance report
        report = ComplianceReport(
            report_id=report_id,
            report_type=report_type,
            generated_at=datetime.utcnow(),
            period_start=start_date,
            period_end=end_date,
            total_events=total_events,
            encryption_operations=encryption_operations,
            key_operations=key_operations,
            security_events=security_events,
            compliance_violations=compliance_violations,
            recommendations=recommendations,
            detailed_findings=detailed_findings
        )
        
        # Store report in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO compliance_reports 
                   (report_id, report_type, generated_at, period_start, period_end, report_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (report_id, report_type, report.generated_at.isoformat(),
                 start_date.isoformat(), end_date.isoformat(),
                 json.dumps(asdict(report), default=str))
            )
            conn.commit()
        
        # Log report generation
        self.log_event(
            AuditEventType.COMPLIANCE_CHECK,
            {
                'report_id': report_id,
                'report_type': report_type,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'total_events': total_events,
                'compliance_violations': compliance_violations
            },
            event_level=AuditLevel.INFO
        )
        
        return report
    
    def search_audit_events(self, criteria: Dict[str, Any], limit: int = 1000) -> List[Dict[str, Any]]:
        """Search audit events with flexible criteria"""
        
        conditions = []
        params = []
        
        # Build dynamic query based on criteria
        if 'event_type' in criteria:
            conditions.append("event_type = ?")
            params.append(criteria['event_type'])
        
        if 'event_level' in criteria:
            conditions.append("event_level = ?")
            params.append(criteria['event_level'])
        
        if 'start_date' in criteria:
            conditions.append("timestamp >= ?")
            params.append(criteria['start_date'])
        
        if 'end_date' in criteria:
            conditions.append("timestamp <= ?")
            params.append(criteria['end_date'])
        
        if 'client_id' in criteria:
            conditions.append("client_id = ?")
            params.append(criteria['client_id'])
        
        if 'matter_id' in criteria:
            conditions.append("matter_id = ?")
            params.append(criteria['matter_id'])
        
        if 'document_id' in criteria:
            conditions.append("document_id = ?")
            params.append(criteria['document_id'])
        
        if 'key_id' in criteria:
            conditions.append("key_id = ?")
            params.append(criteria['key_id'])
        
        if 'source_service' in criteria:
            conditions.append("source_service = ?")
            params.append(criteria['source_service'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT event_id, event_type, event_level, timestamp, user_id, client_id, matter_id,
                   document_id, key_id, source_service, source_function, event_details,
                   security_context, compliance_flags
            FROM audit_events 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params + [limit])
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                event = dict(zip(columns, row))
                # Parse JSON fields
                if event['event_details']:
                    event['event_details'] = json.loads(event['event_details'])
                if event['security_context']:
                    event['security_context'] = json.loads(event['security_context'])
                if event['compliance_flags']:
                    event['compliance_flags'] = json.loads(event['compliance_flags'])
                
                results.append(event)
        
        return results
    
    def _determine_compliance_flags(self, event_type: AuditEventType, event_details: Dict[str, Any]) -> List[str]:
        """Determine compliance flags for event"""
        flags = []
        
        # Attorney-client privilege
        if event_details.get('compliance_level') == 'ATTORNEY_CLIENT':
            flags.append('ATTORNEY_CLIENT_PRIVILEGE')
        
        # GDPR/Privacy
        if 'personal_data' in str(event_details).lower():
            flags.append('PERSONAL_DATA')
        
        # Retention requirements
        if event_type in [AuditEventType.DOCUMENT_ENCRYPTED, AuditEventType.DOCUMENT_DECRYPTED]:
            flags.append('DOCUMENT_RETENTION')
        
        # Security events
        if event_type in [AuditEventType.KEY_COMPROMISE_SUSPECTED, AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT]:
            flags.append('SECURITY_INCIDENT')
        
        return flags
    
    def _load_retention_policies(self) -> Dict[str, int]:
        """Load retention policies for different event types"""
        return {
            # Critical security events - 10 years
            AuditEventType.KEY_COMPROMISE_SUSPECTED.value: 3650,
            AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT.value: 3650,
            AuditEventType.SECURITY_ALERT.value: 3650,
            
            # Key management - 7 years
            AuditEventType.KEY_CREATED.value: 2555,
            AuditEventType.KEY_ROTATED.value: 2555,
            AuditEventType.KEY_REVOKED.value: 2555,
            
            # Document operations - 7 years (legal requirement)
            AuditEventType.DOCUMENT_ENCRYPTED.value: 2555,
            AuditEventType.DOCUMENT_DECRYPTED.value: 2555,
            
            # Compliance events - 10 years
            AuditEventType.COMPLIANCE_CHECK.value: 3650,
            AuditEventType.DATA_EXPORT_REQUEST.value: 3650,
            
            # Default for other events - 3 years
            'default': 1095
        }
    
    def _flush_event_buffer(self):
        """Flush event buffer to database"""
        if not self._event_buffer:
            return
        
        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()
        
        # Batch insert events
        with sqlite3.connect(self.db_path) as conn:
            for event in events_to_flush:
                conn.execute(
                    """INSERT INTO audit_events 
                       (event_id, event_type, event_level, timestamp, user_id, client_id, matter_id,
                        document_id, key_id, source_service, source_function, event_details,
                        security_context, compliance_flags, retention_until)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event.event_id, event.event_type.value, event.event_level.value,
                        event.timestamp.isoformat(), event.user_id, event.client_id, event.matter_id,
                        event.document_id, event.key_id, event.source_service, event.source_function,
                        json.dumps(event.event_details), json.dumps(event.security_context),
                        json.dumps(event.compliance_flags), event.retention_until.isoformat()
                    )
                )
            conn.commit()
    
    def _start_buffer_flush_thread(self):
        """Start background thread to flush event buffer"""
        def flush_periodically():
            while True:
                try:
                    time.sleep(self.config['buffer_flush_interval_seconds'])
                    with self._buffer_lock:
                        if self._event_buffer:
                            self._flush_event_buffer()
                except Exception as e:
                    logger.error(f"[AUDIT_SYSTEM] Error flushing buffer: {e}")
        
        import time
        flush_thread = threading.Thread(target=flush_periodically, name="AuditBufferFlush", daemon=True)
        flush_thread.start()
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get comprehensive audit statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Total events
            cursor = conn.execute("SELECT COUNT(*) FROM audit_events")
            total_events = cursor.fetchone()[0]
            
            # Events by type (last 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            cursor = conn.execute(
                """SELECT event_type, COUNT(*) FROM audit_events 
                   WHERE timestamp > ? GROUP BY event_type ORDER BY COUNT(*) DESC""",
                (thirty_days_ago,)
            )
            recent_events_by_type = dict(cursor.fetchall())
            
            # Security events (last 7 days)
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            cursor = conn.execute(
                """SELECT COUNT(*) FROM audit_events 
                   WHERE timestamp > ? AND event_level = ?""",
                (seven_days_ago, AuditLevel.SECURITY.value)
            )
            recent_security_events = cursor.fetchone()[0]
            
            # Key access stats
            cursor = conn.execute(
                """SELECT access_granted, COUNT(*) FROM key_access_log 
                   WHERE accessed_at > ? GROUP BY access_granted""",
                (seven_days_ago,)
            )
            key_access_stats = dict(cursor.fetchall())
            
            # Failed operations
            cursor = conn.execute(
                """SELECT COUNT(*) FROM failed_operations WHERE failed_at > ?""",
                (seven_days_ago,)
            )
            recent_failures = cursor.fetchone()[0]
        
        return {
            'total_events': total_events,
            'events_last_30_days': sum(recent_events_by_type.values()),
            'events_by_type': recent_events_by_type,
            'security_events_last_7_days': recent_security_events,
            'key_access_stats': key_access_stats,
            'failed_operations_last_7_days': recent_failures,
            'buffer_size': len(self._event_buffer),
            'daily_stats_current': dict(self.daily_stats.get(datetime.utcnow().date().isoformat(), {}))
        }

# Global encryption audit system instance
encryption_audit_system = EncryptionAuditSystem()

__all__ = [
    'EncryptionAuditSystem',
    'AuditEvent',
    'AuditEventType',
    'AuditLevel',
    'ComplianceReport',
    'encryption_audit_system'
]