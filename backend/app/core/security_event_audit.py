"""
COMPREHENSIVE SECURITY EVENT AUDIT SYSTEM

Implements comprehensive security event logging including:
- Failed login attempts and authentication events
- Permission changes and privilege escalations
- Data exports and access anomalies
- Session monitoring and anomaly detection

CRITICAL: Provides complete security audit trail for legal and compliance requirements.
"""

import os
import logging
import json
import hashlib
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
from collections import defaultdict
import ipaddress
import re

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_BLOCKED = "login_blocked"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILED = "mfa_failed"
    TOKEN_ISSUED = "token_issued"
    TOKEN_REVOKED = "token_revoked"
    
    # Authorization Events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_CHANGED = "permission_changed"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PRIVILEGE_REVOCATION = "privilege_revocation"
    
    # Session Events
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"
    SESSION_EXPIRED = "session_expired"
    SESSION_HIJACK_ATTEMPT = "session_hijack_attempt"
    CONCURRENT_SESSION_LIMIT = "concurrent_session_limit"
    SESSION_ANOMALY = "session_anomaly"
    UNUSUAL_LOCATION = "unusual_location"
    DEVICE_FINGERPRINT_MISMATCH = "device_fingerprint_mismatch"
    
    # Data Access Events
    DATA_EXPORT = "data_export"
    BULK_DOWNLOAD = "bulk_download"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    
    # System Events
    SYSTEM_BREACH_ATTEMPT = "system_breach_attempt"
    MALWARE_DETECTED = "malware_detected"
    VULNERABILITY_EXPLOIT = "vulnerability_exploit"
    SECURITY_SCAN_DETECTED = "security_scan_detected"
    
    # Anomaly Detection
    BEHAVIOR_ANOMALY = "behavior_anomaly"
    USAGE_PATTERN_ANOMALY = "usage_pattern_anomaly"
    TIME_BASED_ANOMALY = "time_based_anomaly"
    FREQUENCY_ANOMALY = "frequency_anomaly"

class SecurityEventSeverity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Individual security event record"""
    event_id: str
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    geo_location: Optional[Dict[str, str]]
    device_fingerprint: Optional[str]
    event_details: Dict[str, Any]
    risk_score: int  # 0-100
    automated_response: Optional[str]
    investigation_required: bool
    legal_hold: bool = False

@dataclass
class SessionProfile:
    """User session profile for anomaly detection"""
    user_id: str
    typical_locations: List[str]
    typical_devices: List[str]
    typical_hours: List[int]  # Hours of day (0-23)
    typical_ip_ranges: List[str]
    average_session_duration: float
    typical_actions: List[str]
    last_updated: datetime

class SecurityEventAuditSystem:
    """Comprehensive security event audit system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # Initialize security audit database
        self.db_path = Path(self.config['security_audit_db_path'])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_security_audit_database()
        
        # Session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_profiles: Dict[str, SessionProfile] = {}
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = self._load_anomaly_thresholds()
        
        # Failed login tracking
        self.failed_logins: Dict[str, List[datetime]] = defaultdict(list)
        
        # Event buffer for performance
        self._event_buffer = []
        self._buffer_lock = threading.RLock()
        
        # Statistics
        self.event_stats = defaultdict(int)
        
        # Start background processing
        self._start_background_processors()
        
        logger.info("[SECURITY_AUDIT] Security event audit system initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for security audit"""
        return {
            'security_audit_db_path': 'audit/security_events.db',
            'max_failed_logins': 5,
            'login_lockout_duration_minutes': 30,
            'session_timeout_minutes': 480,  # 8 hours
            'anomaly_detection_enabled': True,
            'auto_response_enabled': True,
            'geo_location_tracking': True,
            'device_fingerprinting': True,
            'legal_hold_enabled': True,
            'buffer_flush_interval_seconds': 30
        }
    
    def _init_security_audit_database(self):
        """Initialize security audit database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    geo_location TEXT,
                    device_fingerprint TEXT,
                    event_details TEXT NOT NULL,
                    risk_score INTEGER,
                    automated_response TEXT,
                    investigation_required BOOLEAN,
                    legal_hold BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    device_fingerprint TEXT,
                    geo_location TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    terminated_reason TEXT,
                    terminated_at TEXT
                );
                
                CREATE TABLE IF NOT EXISTS failed_login_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    ip_address TEXT,
                    attempt_time TEXT NOT NULL,
                    failure_reason TEXT,
                    user_agent TEXT,
                    geo_location TEXT,
                    blocked BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    baseline_established BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS security_alerts (
                    alert_id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    user_id TEXT,
                    triggered_at TEXT NOT NULL,
                    alert_data TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    resolution_notes TEXT
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_security_events_user ON security_events(user_id);
                CREATE INDEX IF NOT EXISTS idx_security_events_session ON security_events(session_id);
                CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);
                CREATE INDEX IF NOT EXISTS idx_failed_logins_user ON failed_login_tracking(user_id);
                CREATE INDEX IF NOT EXISTS idx_failed_logins_ip ON failed_login_tracking(ip_address);
            """)
            conn.commit()
    
    def log_authentication_event(self, event_type: SecurityEventType, user_id: str = None,
                                ip_address: str = None, user_agent: str = None,
                                success: bool = True, failure_reason: str = None,
                                session_id: str = None, **additional_details) -> str:
        """Log authentication-related security event"""
        
        # Calculate risk score
        risk_score = self._calculate_auth_risk_score(event_type, user_id, ip_address, success)
        
        # Determine severity
        severity = self._determine_auth_severity(event_type, risk_score, success)
        
        # Gather additional context
        geo_location = self._get_geo_location(ip_address) if ip_address else None
        device_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
        
        # Event details
        event_details = {
            'success': success,
            'failure_reason': failure_reason,
            'authentication_method': additional_details.get('auth_method', 'password'),
            'mfa_used': additional_details.get('mfa_used', False),
            **additional_details
        }
        
        # Handle failed login tracking
        if not success and event_type == SecurityEventType.LOGIN_FAILED:
            self._track_failed_login(user_id, ip_address, failure_reason, user_agent, geo_location)
        
        # Create security event
        event = SecurityEvent(
            event_id=f"auth_{event_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            geo_location=geo_location,
            device_fingerprint=device_fingerprint,
            event_details=event_details,
            risk_score=risk_score,
            automated_response=self._determine_automated_response(event_type, risk_score, success),
            investigation_required=risk_score >= 70 or not success
        )
        
        # Store event
        self._store_security_event(event)
        
        # Trigger automated responses if enabled
        if self.config['auto_response_enabled'] and event.automated_response:
            self._execute_automated_response(event)
        
        return event.event_id
    
    def log_permission_event(self, event_type: SecurityEventType, user_id: str,
                           target_user_id: str = None, permission: str = None,
                           resource: str = None, granted: bool = True,
                           changed_by: str = None, **additional_details) -> str:
        """Log permission and authorization events"""
        
        risk_score = self._calculate_permission_risk_score(event_type, user_id, permission, granted)
        severity = self._determine_permission_severity(event_type, risk_score, granted)
        
        event_details = {
            'target_user_id': target_user_id,
            'permission': permission,
            'resource': resource,
            'granted': granted,
            'changed_by': changed_by,
            'privilege_level': additional_details.get('privilege_level'),
            'previous_permissions': additional_details.get('previous_permissions'),
            'new_permissions': additional_details.get('new_permissions'),
            **additional_details
        }
        
        event = SecurityEvent(
            event_id=f"perm_{event_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=additional_details.get('session_id'),
            ip_address=additional_details.get('ip_address'),
            user_agent=additional_details.get('user_agent'),
            geo_location=None,
            device_fingerprint=None,
            event_details=event_details,
            risk_score=risk_score,
            automated_response=None,
            investigation_required=risk_score >= 60 or event_type == SecurityEventType.PRIVILEGE_ESCALATION
        )
        
        self._store_security_event(event)
        return event.event_id
    
    def log_session_event(self, event_type: SecurityEventType, session_id: str,
                         user_id: str = None, ip_address: str = None,
                         user_agent: str = None, **additional_details) -> str:
        """Log session-related security events"""
        
        # Check for session anomalies
        anomaly_detected = self._detect_session_anomaly(session_id, user_id, ip_address, event_type)
        
        risk_score = self._calculate_session_risk_score(event_type, user_id, ip_address, anomaly_detected)
        severity = self._determine_session_severity(event_type, risk_score, anomaly_detected)
        
        geo_location = self._get_geo_location(ip_address) if ip_address else None
        device_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
        
        event_details = {
            'session_duration': additional_details.get('session_duration'),
            'previous_ip': additional_details.get('previous_ip'),
            'location_change': additional_details.get('location_change', False),
            'device_change': additional_details.get('device_change', False),
            'concurrent_sessions': additional_details.get('concurrent_sessions', 1),
            'anomaly_detected': anomaly_detected,
            **additional_details
        }
        
        # Update session tracking
        if event_type == SecurityEventType.SESSION_CREATED:
            self._track_session_start(session_id, user_id, ip_address, user_agent, geo_location)
        elif event_type in [SecurityEventType.SESSION_TERMINATED, SecurityEventType.SESSION_EXPIRED]:
            self._track_session_end(session_id, event_type.value)
        
        event = SecurityEvent(
            event_id=f"sess_{event_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            geo_location=geo_location,
            device_fingerprint=device_fingerprint,
            event_details=event_details,
            risk_score=risk_score,
            automated_response=self._determine_automated_response(event_type, risk_score, True),
            investigation_required=anomaly_detected or risk_score >= 70
        )
        
        self._store_security_event(event)
        return event.event_id
    
    def log_data_access_event(self, event_type: SecurityEventType, user_id: str,
                            resource: str = None, action: str = None, success: bool = True,
                            session_id: str = None, ip_address: str = None,
                            data_type: str = None, data_id: str = None, access_method: str = None,
                            **additional_details) -> str:
        """Log data access and export events"""
        
        # Handle legacy parameter names for compatibility
        if resource is None and data_type is not None:
            resource = data_type
        if action is None and access_method is not None:
            action = access_method
        if data_id is not None:
            additional_details['data_id'] = data_id
        
        # Ensure required parameters are provided
        if resource is None:
            resource = "unknown_resource"
        if action is None:
            action = "unknown_action"
        
        # Determine if this involves sensitive data
        is_sensitive = self._is_sensitive_resource(resource)
        
        risk_score = self._calculate_data_access_risk_score(event_type, resource, action, is_sensitive, success)
        severity = self._determine_data_access_severity(event_type, risk_score, is_sensitive, success)
        
        event_details = {
            'resource': resource,
            'action': action,
            'success': success,
            'is_sensitive_data': is_sensitive,
            'data_classification': additional_details.get('data_classification', 'unknown'),
            'export_format': additional_details.get('export_format'),
            'record_count': additional_details.get('record_count'),
            'file_size_bytes': additional_details.get('file_size_bytes'),
            'client_matter_ids': additional_details.get('client_matter_ids', []),
            **additional_details
        }
        
        # Flag for legal hold if sensitive data export
        legal_hold = (event_type == SecurityEventType.DATA_EXPORT and is_sensitive)
        
        event = SecurityEvent(
            event_id=f"data_{event_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=additional_details.get('user_agent'),
            geo_location=self._get_geo_location(ip_address) if ip_address else None,
            device_fingerprint=None,
            event_details=event_details,
            risk_score=risk_score,
            automated_response=None,
            investigation_required=risk_score >= 60 or not success,
            legal_hold=legal_hold
        )
        
        self._store_security_event(event)
        
        # Create alert for high-risk data access
        if risk_score >= 80:
            self._create_security_alert('HIGH_RISK_DATA_ACCESS', event)
        
        return event.event_id
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect security anomalies across all event types"""
        
        anomalies = []
        
        # Time-based anomalies (unusual hours)
        anomalies.extend(self._detect_time_based_anomalies())
        
        # Location-based anomalies
        anomalies.extend(self._detect_location_anomalies())
        
        # Frequency-based anomalies
        anomalies.extend(self._detect_frequency_anomalies())
        
        # Behavior pattern anomalies
        anomalies.extend(self._detect_behavior_anomalies())
        
        # Log detected anomalies
        for anomaly in anomalies:
            self.log_security_anomaly(anomaly)
        
        return anomalies
    
    def log_security_anomaly(self, anomaly_data: Dict[str, Any]) -> str:
        """Log detected security anomaly"""
        
        event_type = SecurityEventType.BEHAVIOR_ANOMALY
        if 'time' in anomaly_data.get('anomaly_type', '').lower():
            event_type = SecurityEventType.TIME_BASED_ANOMALY
        elif 'frequency' in anomaly_data.get('anomaly_type', '').lower():
            event_type = SecurityEventType.FREQUENCY_ANOMALY
        
        risk_score = anomaly_data.get('risk_score', 70)
        severity = SecurityEventSeverity.HIGH if risk_score >= 80 else SecurityEventSeverity.MEDIUM
        
        event = SecurityEvent(
            event_id=f"anomaly_{event_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=anomaly_data.get('user_id'),
            session_id=anomaly_data.get('session_id'),
            ip_address=anomaly_data.get('ip_address'),
            user_agent=None,
            geo_location=None,
            device_fingerprint=None,
            event_details=anomaly_data,
            risk_score=risk_score,
            automated_response=None,
            investigation_required=True
        )
        
        self._store_security_event(event)
        
        # Create high-priority alert
        self._create_security_alert('SECURITY_ANOMALY_DETECTED', event)
        
        return event.event_id
    
    def _track_failed_login(self, user_id: str, ip_address: str, failure_reason: str,
                           user_agent: str, geo_location: Dict[str, str]):
        """Track failed login attempts for brute force detection"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO failed_login_tracking 
                   (user_id, ip_address, attempt_time, failure_reason, user_agent, geo_location)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, ip_address, datetime.utcnow().isoformat(), failure_reason,
                 user_agent, json.dumps(geo_location) if geo_location else None)
            )
            conn.commit()
        
        # Check for brute force patterns
        self._check_brute_force_attack(user_id, ip_address)
    
    def _check_brute_force_attack(self, user_id: str, ip_address: str):
        """Check for brute force attack patterns"""
        
        # Check recent failed attempts
        cutoff_time = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Check by user
            cursor = conn.execute(
                "SELECT COUNT(*) FROM failed_login_tracking WHERE user_id = ? AND attempt_time > ?",
                (user_id, cutoff_time)
            )
            user_failures = cursor.fetchone()[0]
            
            # Check by IP
            cursor = conn.execute(
                "SELECT COUNT(*) FROM failed_login_tracking WHERE ip_address = ? AND attempt_time > ?",
                (ip_address, cutoff_time)
            )
            ip_failures = cursor.fetchone()[0]
        
        # Trigger alerts if thresholds exceeded
        if user_failures >= self.config['max_failed_logins']:
            self._create_security_alert('BRUTE_FORCE_USER', {
                'user_id': user_id,
                'failed_attempts': user_failures,
                'time_window': 30,
                'recommended_action': 'LOCK_ACCOUNT'
            })
        
        if ip_failures >= self.config['max_failed_logins'] * 2:
            self._create_security_alert('BRUTE_FORCE_IP', {
                'ip_address': ip_address,
                'failed_attempts': ip_failures,
                'time_window': 30,
                'recommended_action': 'BLOCK_IP'
            })
    
    def _calculate_auth_risk_score(self, event_type: SecurityEventType, user_id: str,
                                  ip_address: str, success: bool) -> int:
        """Calculate risk score for authentication events"""
        
        base_score = 0
        
        if not success:
            base_score += 30
        
        if event_type == SecurityEventType.LOGIN_FAILED:
            base_score += 20
        elif event_type == SecurityEventType.LOGIN_BLOCKED:
            base_score += 50
        elif event_type == SecurityEventType.ACCOUNT_LOCKED:
            base_score += 60
        
        # Check for unusual location/IP
        if ip_address and self._is_unusual_location(user_id, ip_address):
            base_score += 25
        
        # Check time of day
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Outside business hours
            base_score += 15
        
        return min(base_score, 100)
    
    def _determine_auth_severity(self, event_type: SecurityEventType, risk_score: int, success: bool) -> SecurityEventSeverity:
        """Determine severity for authentication events"""
        
        if not success and risk_score >= 80:
            return SecurityEventSeverity.CRITICAL
        elif not success and risk_score >= 60:
            return SecurityEventSeverity.HIGH
        elif not success:
            return SecurityEventSeverity.MEDIUM
        elif success and risk_score >= 40:
            return SecurityEventSeverity.MEDIUM
        else:
            return SecurityEventSeverity.LOW
    
    def _store_security_event(self, event: SecurityEvent):
        """Store security event in database"""
        
        with self._buffer_lock:
            self._event_buffer.append(event)
            
            # Flush buffer if getting full
            if len(self._event_buffer) >= 100:
                self._flush_event_buffer()
        
        # Update statistics
        self.event_stats[event.event_type.value] += 1
        self.event_stats[f"severity_{event.severity.value}"] += 1
    
    def _flush_event_buffer(self):
        """Flush event buffer to database"""
        
        if not self._event_buffer:
            return
        
        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()
        
        with sqlite3.connect(self.db_path) as conn:
            for event in events_to_flush:
                conn.execute(
                    """INSERT INTO security_events 
                       (event_id, event_type, severity, timestamp, user_id, session_id,
                        ip_address, user_agent, geo_location, device_fingerprint,
                        event_details, risk_score, automated_response, investigation_required,
                        legal_hold)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event.event_id, event.event_type.value, event.severity.value,
                        event.timestamp.isoformat(), event.user_id, event.session_id,
                        event.ip_address, event.user_agent,
                        json.dumps(event.geo_location) if event.geo_location else None,
                        event.device_fingerprint, json.dumps(event.event_details),
                        event.risk_score, event.automated_response,
                        event.investigation_required, event.legal_hold
                    )
                )
            conn.commit()
    
    def _start_background_processors(self):
        """Start background processing threads"""
        
        def flush_periodically():
            import time
            while True:
                try:
                    time.sleep(self.config['buffer_flush_interval_seconds'])
                    with self._buffer_lock:
                        if self._event_buffer:
                            self._flush_event_buffer()
                except Exception as e:
                    logger.error(f"[SECURITY_AUDIT] Error flushing buffer: {e}")
        
        def anomaly_detection_loop():
            import time
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes
                    if self.config['anomaly_detection_enabled']:
                        self.detect_anomalies()
                except Exception as e:
                    logger.error(f"[SECURITY_AUDIT] Error in anomaly detection: {e}")
        
        # Start background threads
        flush_thread = threading.Thread(target=flush_periodically, name="SecurityAuditFlush", daemon=True)
        flush_thread.start()
        
        anomaly_thread = threading.Thread(target=anomaly_detection_loop, name="AnomalyDetection", daemon=True)
        anomaly_thread.start()
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Total events
            cursor = conn.execute("SELECT COUNT(*) FROM security_events")
            total_events = cursor.fetchone()[0]
            
            # Events by severity (last 24 hours)
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
            cursor = conn.execute(
                """SELECT severity, COUNT(*) FROM security_events 
                   WHERE timestamp > ? GROUP BY severity""",
                (yesterday,)
            )
            severity_stats = dict(cursor.fetchall())
            
            # Failed login attempts (last 24 hours)
            cursor = conn.execute(
                "SELECT COUNT(*) FROM failed_login_tracking WHERE attempt_time > ?",
                (yesterday,)
            )
            failed_logins_24h = cursor.fetchone()[0]
            
            # Active sessions
            cursor = conn.execute("SELECT COUNT(*) FROM user_sessions WHERE is_active = 1")
            active_sessions = cursor.fetchone()[0]
        
        return {
            'total_security_events': total_events,
            'events_last_24h': sum(severity_stats.values()),
            'severity_distribution': severity_stats,
            'failed_logins_24h': failed_logins_24h,
            'active_sessions': active_sessions,
            'buffer_size': len(self._event_buffer),
            'event_type_stats': dict(self.event_stats),
            'system_health': 'healthy'
        }
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Alias for get_security_statistics for compatibility"""
        return self.get_security_statistics()
    
    def log_authorization_event(self, event_type: SecurityEventType, user_id: str,
                               permission: str, granted: bool = True, 
                               resource: str = None, ip_address: str = None,
                               session_id: str = None, additional_data: Dict[str, Any] = None,
                               resource_type: str = None, **kwargs) -> str:
        """Log authorization and permission events"""
        # Handle extra parameters for compatibility
        if additional_data is None:
            additional_data = {}
        if resource_type:
            additional_data['resource_type'] = resource_type
        additional_data.update(kwargs)
        
        return self.log_permission_event(
            event_type=event_type,
            user_id=user_id,
            permission=permission,
            granted=granted,
            resource=resource,
            ip_address=ip_address,
            session_id=session_id,
            additional_data=additional_data
        )
    
    # Placeholder methods for additional functionality
    def _get_geo_location(self, ip_address: str) -> Optional[Dict[str, str]]:
        """Get geographic location from IP address"""
        # In production, this would use a geo-location service
        return None
    
    def _generate_device_fingerprint(self, user_agent: str, ip_address: str) -> Optional[str]:
        """Generate device fingerprint"""
        if user_agent and ip_address:
            return hashlib.sha256(f"{user_agent}:{ip_address}".encode()).hexdigest()[:16]
        return None
    
    def _is_unusual_location(self, user_id: str, ip_address: str) -> bool:
        """Check if location is unusual for user"""
        # Placeholder - would check against user's typical locations
        return False
    
    def _detect_session_anomaly(self, session_id: str, user_id: str, ip_address: str, event_type: SecurityEventType) -> bool:
        """Detect session anomalies"""
        # Placeholder for session anomaly detection
        return False
    
    def _is_sensitive_resource(self, resource: str) -> bool:
        """Determine if resource contains sensitive data"""
        sensitive_indicators = ['client', 'matter', 'document', 'confidential', 'privileged']
        return any(indicator in resource.lower() for indicator in sensitive_indicators)
    
    def _calculate_permission_risk_score(self, event_type: SecurityEventType, user_id: str, permission: str, granted: bool) -> int:
        """Calculate risk score for permission events"""
        base_score = 20 if granted else 40
        
        if event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            base_score += 50
        
        if permission and 'admin' in permission.lower():
            base_score += 30
        
        return min(base_score, 100)
    
    def _determine_permission_severity(self, event_type: SecurityEventType, risk_score: int, granted: bool) -> SecurityEventSeverity:
        """Determine severity for permission events"""
        if risk_score >= 80:
            return SecurityEventSeverity.HIGH
        elif risk_score >= 60:
            return SecurityEventSeverity.MEDIUM
        else:
            return SecurityEventSeverity.LOW
    
    def _calculate_session_risk_score(self, event_type: SecurityEventType, user_id: str, ip_address: str, anomaly_detected: bool) -> int:
        """Calculate risk score for session events"""
        base_score = 10
        
        if anomaly_detected:
            base_score += 50
        
        if event_type == SecurityEventType.SESSION_HIJACK_ATTEMPT:
            base_score += 70
        
        return min(base_score, 100)
    
    def _determine_session_severity(self, event_type: SecurityEventType, risk_score: int, anomaly_detected: bool) -> SecurityEventSeverity:
        """Determine severity for session events"""
        if anomaly_detected or risk_score >= 80:
            return SecurityEventSeverity.HIGH
        elif risk_score >= 60:
            return SecurityEventSeverity.MEDIUM
        else:
            return SecurityEventSeverity.LOW
    
    def _calculate_data_access_risk_score(self, event_type: SecurityEventType, resource: str, action: str, is_sensitive: bool, success: bool) -> int:
        """Calculate risk score for data access events"""
        base_score = 20 if success else 40
        
        if is_sensitive:
            base_score += 30
        
        if event_type == SecurityEventType.DATA_EXPORT:
            base_score += 25
        elif event_type == SecurityEventType.BULK_DOWNLOAD:
            base_score += 35
        
        return min(base_score, 100)
    
    def _determine_data_access_severity(self, event_type: SecurityEventType, risk_score: int, is_sensitive: bool, success: bool) -> SecurityEventSeverity:
        """Determine severity for data access events"""
        if not success and is_sensitive:
            return SecurityEventSeverity.CRITICAL
        elif risk_score >= 80:
            return SecurityEventSeverity.HIGH
        elif risk_score >= 60 or is_sensitive:
            return SecurityEventSeverity.MEDIUM
        else:
            return SecurityEventSeverity.LOW
    
    def _determine_automated_response(self, event_type: SecurityEventType, risk_score: int, success: bool) -> Optional[str]:
        """Determine automated response for security event"""
        if risk_score >= 90:
            return "IMMEDIATE_INVESTIGATION"
        elif risk_score >= 80:
            return "ALERT_SECURITY_TEAM"
        elif not success and event_type == SecurityEventType.LOGIN_FAILED and risk_score >= 60:
            return "TEMPORARY_ACCOUNT_LOCK"
        return None
    
    def _execute_automated_response(self, event: SecurityEvent):
        """Execute automated response for security event"""
        # Placeholder for automated response execution
        logger.info(f"[SECURITY_AUDIT] Automated response triggered: {event.automated_response} for event {event.event_id}")
    
    def _create_security_alert(self, alert_type: str, event_or_data):
        """Create security alert"""
        if isinstance(event_or_data, SecurityEvent):
            alert_data = {
                'event_id': event_or_data.event_id,
                'event_type': event_or_data.event_type.value,
                'severity': event_or_data.severity.value,
                'user_id': event_or_data.user_id,
                'risk_score': event_or_data.risk_score
            }
        else:
            alert_data = event_or_data
        
        alert_id = f"alert_{alert_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO security_alerts 
                   (alert_id, alert_type, severity, user_id, triggered_at, alert_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (alert_id, alert_type, 'HIGH', alert_data.get('user_id'),
                 datetime.utcnow().isoformat(), json.dumps(alert_data))
            )
            conn.commit()
        
        logger.warning(f"[SECURITY_ALERT] {alert_type}: {alert_data}")
    
    def _track_session_start(self, session_id: str, user_id: str, ip_address: str, user_agent: str, geo_location: Dict):
        """Track session start"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO user_sessions 
                   (session_id, user_id, created_at, last_activity, ip_address, user_agent, geo_location)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, user_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(),
                 ip_address, user_agent, json.dumps(geo_location) if geo_location else None)
            )
            conn.commit()
    
    def _track_session_end(self, session_id: str, reason: str):
        """Track session end"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE user_sessions SET is_active = FALSE, terminated_reason = ?, terminated_at = ?
                   WHERE session_id = ?""",
                (reason, datetime.utcnow().isoformat(), session_id)
            )
            conn.commit()
    
    def _load_anomaly_thresholds(self) -> Dict[str, Any]:
        """Load anomaly detection thresholds"""
        return {
            'max_failed_logins_per_hour': 10,
            'max_sessions_per_user': 3,
            'unusual_hour_threshold': 0.1,
            'location_change_threshold': 100,  # km
            'frequency_multiplier_threshold': 5.0
        }
    
    def _detect_time_based_anomalies(self) -> List[Dict[str, Any]]:
        """Detect time-based anomalies"""
        # Placeholder for time-based anomaly detection
        return []
    
    def _detect_location_anomalies(self) -> List[Dict[str, Any]]:
        """Detect location-based anomalies"""
        # Placeholder for location-based anomaly detection
        return []
    
    def _detect_frequency_anomalies(self) -> List[Dict[str, Any]]:
        """Detect frequency-based anomalies"""
        # Placeholder for frequency-based anomaly detection
        return []
    
    def _detect_behavior_anomalies(self) -> List[Dict[str, Any]]:
        """Detect behavior pattern anomalies"""
        # Placeholder for behavior pattern anomaly detection
        return []

# Global security event audit system
security_event_audit = SecurityEventAuditSystem()

__all__ = [
    'SecurityEventAuditSystem',
    'SecurityEvent',
    'SecurityEventType',
    'SecurityEventSeverity',
    'SessionProfile',
    'security_event_audit'
]