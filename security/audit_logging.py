#!/usr/bin/env python3
"""
SOC 2 Type II Compliant Audit Logging System
Comprehensive audit trail for legal data access and changes
"""

import os
import json
import hashlib
import logging
import logging.handlers
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from threading import Lock
import sqlite3
import gzip
import csv

# Configure secure audit logger
audit_logger = logging.getLogger('legal_audit')
audit_logger.setLevel(logging.INFO)

# Create secure audit log handler with rotation
audit_handler = logging.handlers.RotatingFileHandler(
    'logs/legal_audit.log',
    maxBytes=50*1024*1024,  # 50MB per file
    backupCount=100,        # Keep 100 backup files
    encoding='utf-8'
)
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s|%(levelname)s|%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S.%f'
))
audit_logger.addHandler(audit_handler)

class AuditEventType(Enum):
    """Comprehensive audit event types for legal compliance"""
    
    # Authentication Events
    USER_LOGIN_SUCCESS = "user_login_success"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_LOGOUT = "user_logout"
    MFA_SETUP = "mfa_setup"
    MFA_VERIFICATION = "mfa_verification"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # Data Access Events
    DOCUMENT_VIEWED = "document_viewed"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    DOCUMENT_PRINTED = "document_printed"
    SEARCH_PERFORMED = "search_performed"
    CLIENT_DATA_ACCESSED = "client_data_accessed"
    PRIVILEGED_DATA_ACCESSED = "privileged_data_accessed"
    
    # Data Modification Events
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_MODIFIED = "document_modified"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_MOVED = "document_moved"
    METADATA_CHANGED = "metadata_changed"
    
    # Client Management Events
    CLIENT_CREATED = "client_created"
    CLIENT_MODIFIED = "client_modified"
    CLIENT_DELETED = "client_deleted"
    ATTORNEY_CLIENT_RELATIONSHIP_ESTABLISHED = "attorney_client_relationship_established"
    ATTORNEY_CLIENT_RELATIONSHIP_TERMINATED = "attorney_client_relationship_terminated"
    
    # System Events
    BACKUP_STARTED = "backup_started"
    BACKUP_COMPLETED = "backup_completed"
    BACKUP_FAILED = "backup_failed"
    RESTORE_STARTED = "restore_started"
    RESTORE_COMPLETED = "restore_completed"
    SYSTEM_CONFIGURATION_CHANGED = "system_configuration_changed"
    
    # Security Events
    SUSPICIOUS_ACTIVITY_DETECTED = "suspicious_activity_detected"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"
    DATA_BREACH_DETECTED = "data_breach_detected"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"
    
    # Compliance Events
    CONFLICTS_CHECK_PERFORMED = "conflicts_check_performed"
    ETHICAL_WALL_BREACH_ATTEMPT = "ethical_wall_breach_attempt"
    RETENTION_POLICY_APPLIED = "retention_policy_applied"
    DATA_PURGED = "data_purged"
    AUDIT_LOG_ACCESSED = "audit_log_accessed"

class RiskLevel(Enum):
    """Risk levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Comprehensive audit event structure"""
    
    event_id: str
    timestamp: str
    event_type: AuditEventType
    risk_level: RiskLevel
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    
    # Legal-specific fields
    client_id: Optional[str] = None
    document_id: Optional[str] = None
    attorney_bar_number: Optional[str] = None
    privilege_level: Optional[str] = None
    
    # Technical details
    resource_accessed: Optional[str] = None
    action_performed: Optional[str] = None
    result_status: str = "success"
    error_message: Optional[str] = None
    
    # Data changes
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    
    # Additional context
    additional_data: Optional[Dict[str, Any]] = None
    
    # Integrity and compliance
    event_hash: Optional[str] = None
    compliance_tags: List[str] = None
    
    def __post_init__(self):
        if self.compliance_tags is None:
            self.compliance_tags = []
        
        # Generate event hash for integrity verification
        if not self.event_hash:
            self.event_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate hash for event integrity verification"""
        # Create deterministic string from core event data
        hash_data = f"{self.event_id}|{self.timestamp}|{self.event_type.value}|{self.user_id}|{self.session_id}"
        
        if self.client_id:
            hash_data += f"|{self.client_id}"
        if self.document_id:
            hash_data += f"|{self.document_id}"
        if self.resource_accessed:
            hash_data += f"|{self.resource_accessed}"
        if self.action_performed:
            hash_data += f"|{self.action_performed}"
        
        return hashlib.sha256(hash_data.encode()).hexdigest()[:16]

class SOC2AuditLogger:
    """SOC 2 Type II compliant audit logging system"""
    
    def __init__(self, db_path: str = "audit/legal_audit.db"):
        self.db_path = db_path
        self.lock = Lock()
        
        # Ensure audit directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize audit database
        self._init_database()
        
        # Risk level mappings
        self.event_risk_mapping = self._setup_risk_mapping()
        
        # Compliance tag mappings
        self.compliance_mapping = self._setup_compliance_mapping()
    
    def _init_database(self):
        """Initialize SQLite database for audit logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    client_id TEXT,
                    document_id TEXT,
                    attorney_bar_number TEXT,
                    privilege_level TEXT,
                    resource_accessed TEXT,
                    action_performed TEXT,
                    result_status TEXT DEFAULT 'success',
                    error_message TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    additional_data TEXT,
                    event_hash TEXT NOT NULL,
                    compliance_tags TEXT,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_client_id ON audit_events(client_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_risk_level ON audit_events(risk_level)')
            
            # Create table for audit log integrity verification
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_integrity (
                    date TEXT PRIMARY KEY,
                    event_count INTEGER NOT NULL,
                    integrity_hash TEXT NOT NULL,
                    last_event_id TEXT NOT NULL
                )
            ''')
    
    def _setup_risk_mapping(self) -> Dict[AuditEventType, RiskLevel]:
        """Setup default risk levels for different event types"""
        return {
            # High-risk events
            AuditEventType.PRIVILEGED_DATA_ACCESSED: RiskLevel.HIGH,
            AuditEventType.DOCUMENT_DELETED: RiskLevel.HIGH,
            AuditEventType.ATTORNEY_CLIENT_RELATIONSHIP_TERMINATED: RiskLevel.HIGH,
            AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT: RiskLevel.CRITICAL,
            AuditEventType.PRIVILEGE_ESCALATION_ATTEMPT: RiskLevel.CRITICAL,
            AuditEventType.DATA_BREACH_DETECTED: RiskLevel.CRITICAL,
            AuditEventType.ETHICAL_WALL_BREACH_ATTEMPT: RiskLevel.CRITICAL,
            
            # Medium-risk events
            AuditEventType.CLIENT_DATA_ACCESSED: RiskLevel.MEDIUM,
            AuditEventType.DOCUMENT_DOWNLOADED: RiskLevel.MEDIUM,
            AuditEventType.DOCUMENT_MODIFIED: RiskLevel.MEDIUM,
            AuditEventType.PASSWORD_CHANGE: RiskLevel.MEDIUM,
            AuditEventType.ACCOUNT_LOCKED: RiskLevel.MEDIUM,
            AuditEventType.CONFLICTS_CHECK_PERFORMED: RiskLevel.MEDIUM,
            
            # Low-risk events (default)
        }
    
    def _setup_compliance_mapping(self) -> Dict[AuditEventType, List[str]]:
        """Setup compliance tags for different event types"""
        return {
            AuditEventType.PRIVILEGED_DATA_ACCESSED: ["attorney_client_privilege", "confidentiality"],
            AuditEventType.ATTORNEY_CLIENT_RELATIONSHIP_ESTABLISHED: ["ethical_rules", "conflicts"],
            AuditEventType.CONFLICTS_CHECK_PERFORMED: ["ethical_rules", "professional_responsibility"],
            AuditEventType.DATA_PURGED: ["data_retention", "legal_hold"],
            AuditEventType.BACKUP_COMPLETED: ["business_continuity", "data_protection"],
            AuditEventType.ENCRYPTION_KEY_ROTATED: ["data_security", "soc2_compliance"],
        }
    
    def log_event(self, event_type: AuditEventType, user_id: str, session_id: str = "",
                  ip_address: str = "", user_agent: str = "", **kwargs) -> str:
        """Log audit event with automatic risk assessment and compliance tagging"""
        
        # Generate unique event ID
        event_id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}|{user_id}|{event_type.value}".encode()
        ).hexdigest()[:16]
        
        # Determine risk level
        risk_level = self.event_risk_mapping.get(event_type, RiskLevel.LOW)
        
        # Get compliance tags
        compliance_tags = self.compliance_mapping.get(event_type, [])
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            risk_level=risk_level,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            compliance_tags=compliance_tags,
            **kwargs
        )
        
        # Log to structured database
        self._store_event_in_database(event)
        
        # Log to text file for external SIEM integration
        self._log_to_text_file(event)
        
        # Check for suspicious patterns
        self._analyze_for_suspicious_activity(event)
        
        return event_id
    
    def _store_event_in_database(self, event: AuditEvent):
        """Store audit event in SQLite database"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO audit_events (
                        event_id, timestamp, event_type, risk_level, user_id, session_id,
                        ip_address, user_agent, client_id, document_id, attorney_bar_number,
                        privilege_level, resource_accessed, action_performed, result_status,
                        error_message, old_values, new_values, additional_data, event_hash,
                        compliance_tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id, event.timestamp, event.event_type.value, event.risk_level.value,
                    event.user_id, event.session_id, event.ip_address, event.user_agent,
                    event.client_id, event.document_id, event.attorney_bar_number,
                    event.privilege_level, event.resource_accessed, event.action_performed,
                    event.result_status, event.error_message,
                    json.dumps(event.old_values) if event.old_values else None,
                    json.dumps(event.new_values) if event.new_values else None,
                    json.dumps(event.additional_data) if event.additional_data else None,
                    event.event_hash, json.dumps(event.compliance_tags)
                ))
    
    def _log_to_text_file(self, event: AuditEvent):
        """Log event to structured text file for SIEM integration"""
        log_entry = (
            f"EventID={event.event_id} "
            f"Timestamp={event.timestamp} "
            f"EventType={event.event_type.value} "
            f"RiskLevel={event.risk_level.value} "
            f"UserID={event.user_id} "
            f"SessionID={event.session_id} "
            f"IP={event.ip_address} "
            f"Status={event.result_status}"
        )
        
        if event.client_id:
            log_entry += f" ClientID={event.client_id}"
        if event.document_id:
            log_entry += f" DocumentID={event.document_id}"
        if event.privilege_level:
            log_entry += f" PrivilegeLevel={event.privilege_level}"
        if event.compliance_tags:
            log_entry += f" ComplianceTags={','.join(event.compliance_tags)}"
        
        audit_logger.info(log_entry)
    
    def _analyze_for_suspicious_activity(self, event: AuditEvent):
        """Analyze event for suspicious patterns and trigger alerts"""
        
        # Check for rapid successive access to privileged data
        if event.event_type == AuditEventType.PRIVILEGED_DATA_ACCESSED:
            recent_privileged_access = self.query_events(
                user_id=event.user_id,
                event_types=[AuditEventType.PRIVILEGED_DATA_ACCESSED],
                hours_back=1
            )
            
            if len(recent_privileged_access) > 10:  # More than 10 privileged accesses in 1 hour
                self.log_event(
                    AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    ip_address=event.ip_address,
                    additional_data={"reason": "rapid_privileged_access", "count": len(recent_privileged_access)}
                )
        
        # Check for access from unusual IP addresses
        if event.ip_address and not event.ip_address.startswith(('192.168.', '10.', '172.')):
            recent_logins = self.query_events(
                user_id=event.user_id,
                event_types=[AuditEventType.USER_LOGIN_SUCCESS],
                hours_back=24
            )
            
            # Check if this IP is new for this user
            recent_ips = {e.get('ip_address') for e in recent_logins}
            if event.ip_address not in recent_ips and len(recent_ips) > 0:
                self.log_event(
                    AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    ip_address=event.ip_address,
                    additional_data={"reason": "unusual_ip_address", "new_ip": event.ip_address}
                )
    
    def query_events(self, user_id: str = None, client_id: str = None, 
                    event_types: List[AuditEventType] = None, hours_back: int = 24,
                    risk_level: RiskLevel = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Query audit events with filtering"""
        
        query = "SELECT * FROM audit_events WHERE timestamp > ?"
        params = [datetime.utcnow() - timedelta(hours=hours_back)]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)
        
        if event_types:
            placeholders = ','.join(['?'] * len(event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend([et.value for et in event_types])
        
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level.value)
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def generate_compliance_report(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        with sqlite3.connect(self.db_path) as conn:
            # Total events
            total_events = conn.execute(
                "SELECT COUNT(*) FROM audit_events WHERE timestamp > ?",
                (start_date.isoformat(),)
            ).fetchone()[0]
            
            # Events by risk level
            risk_distribution = {}
            for risk in RiskLevel:
                count = conn.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE timestamp > ? AND risk_level = ?",
                    (start_date.isoformat(), risk.value)
                ).fetchone()[0]
                risk_distribution[risk.value] = count
            
            # Top users by activity
            top_users = conn.execute('''
                SELECT user_id, COUNT(*) as event_count
                FROM audit_events
                WHERE timestamp > ?
                GROUP BY user_id
                ORDER BY event_count DESC
                LIMIT 10
            ''', (start_date.isoformat(),)).fetchall()
            
            # Privileged data access
            privileged_access = conn.execute(
                "SELECT COUNT(*) FROM audit_events WHERE timestamp > ? AND event_type = ?",
                (start_date.isoformat(), AuditEventType.PRIVILEGED_DATA_ACCESSED.value)
            ).fetchone()[0]
            
            # Security incidents
            security_incidents = conn.execute('''
                SELECT COUNT(*) FROM audit_events
                WHERE timestamp > ? AND risk_level IN ('high', 'critical')
            ''', (start_date.isoformat(),)).fetchone()[0]
            
            # Compliance events
            compliance_events = conn.execute('''
                SELECT compliance_tags, COUNT(*) as count
                FROM audit_events
                WHERE timestamp > ? AND compliance_tags IS NOT NULL AND compliance_tags != '[]'
                GROUP BY compliance_tags
            ''', (start_date.isoformat(),)).fetchall()
        
        return {
            "report_period_days": days_back,
            "report_generated": datetime.utcnow().isoformat(),
            "total_events": total_events,
            "risk_distribution": risk_distribution,
            "top_users": [{"user_id": u[0], "event_count": u[1]} for u in top_users],
            "privileged_data_access_count": privileged_access,
            "security_incidents": security_incidents,
            "compliance_events": [{"tags": json.loads(c[0]), "count": c[1]} for c in compliance_events],
            "daily_average": total_events / days_back if days_back > 0 else 0
        }
    
    def export_audit_logs(self, start_date: datetime, end_date: datetime, 
                         format: str = "csv") -> str:
        """Export audit logs for external analysis or legal discovery"""
        
        events = self.query_events(hours_back=int((datetime.utcnow() - start_date).total_seconds() / 3600))
        
        # Filter by date range
        filtered_events = [
            e for e in events
            if start_date.isoformat() <= e['timestamp'] <= end_date.isoformat()
        ]
        
        if format.lower() == "csv":
            return self._export_to_csv(filtered_events)
        elif format.lower() == "json":
            return json.dumps(filtered_events, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_csv(self, events: List[Dict[str, Any]]) -> str:
        """Export events to CSV format"""
        if not events:
            return "No events to export"
        
        output_path = f"audit_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = events[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(events)
        
        return output_path
    
    def verify_audit_integrity(self, date: str = None) -> Dict[str, Any]:
        """Verify audit log integrity for SOC 2 compliance"""
        
        target_date = date or datetime.utcnow().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            # Get events for the date
            events = conn.execute('''
                SELECT event_id, event_hash FROM audit_events
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp
            ''', (target_date,)).fetchall()
            
            if not events:
                return {"date": target_date, "status": "no_events", "integrity": "N/A"}
            
            # Recalculate hash chain
            calculated_hash = hashlib.sha256("".join([e[1] for e in events]).encode()).hexdigest()
            
            # Check stored integrity hash
            stored_integrity = conn.execute(
                "SELECT integrity_hash FROM audit_integrity WHERE date = ?",
                (target_date,)
            ).fetchone()
            
            if stored_integrity and stored_integrity[0] == calculated_hash:
                status = "verified"
            else:
                status = "integrity_failure"
                # Store new integrity hash
                conn.execute('''
                    INSERT OR REPLACE INTO audit_integrity (date, event_count, integrity_hash, last_event_id)
                    VALUES (?, ?, ?, ?)
                ''', (target_date, len(events), calculated_hash, events[-1][0]))
        
        return {
            "date": target_date,
            "event_count": len(events),
            "status": status,
            "integrity_hash": calculated_hash,
            "verification_time": datetime.utcnow().isoformat()
        }

# Global audit logger instance
audit_system = SOC2AuditLogger()