#!/usr/bin/env python3
"""
Attorney Session Management System
Enterprise-grade secure session management for legal professionals
"""

import os
import json
import sqlite3
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
import ipaddress
from pathlib import Path
import jwt
import threading
import time

class SessionStatus(Enum):
    """Attorney session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    LOCKED = "locked"

class SessionTerminationReason(Enum):
    """Reasons for session termination"""
    USER_LOGOUT = "user_logout"
    TIMEOUT_IDLE = "timeout_idle"
    TIMEOUT_ABSOLUTE = "timeout_absolute"
    SECURITY_VIOLATION = "security_violation"
    ADMINISTRATIVE = "administrative"
    CONCURRENT_LIMIT = "concurrent_limit"
    IP_CHANGE = "ip_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class RiskLevel(Enum):
    """Session risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AttorneySession:
    """Attorney session with security tracking"""
    session_id: str
    attorney_id: str
    attorney_email: str
    attorney_role: str
    bar_number: Optional[str]
    
    # Session timing
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    idle_timeout_minutes: int
    absolute_timeout_minutes: int
    
    # Security information
    ip_address: str
    user_agent: str
    device_fingerprint: str
    geolocation: Optional[Dict[str, Any]]
    
    # Session state
    status: SessionStatus
    is_privileged_session: bool  # For accessing privileged documents
    risk_level: RiskLevel
    security_flags: List[str]
    
    # Activity tracking
    page_views: int
    document_accesses: int
    privileged_document_accesses: int
    client_data_accesses: int
    api_calls: int
    
    # Termination info
    terminated_at: Optional[datetime]
    termination_reason: Optional[SessionTerminationReason]
    terminated_by: Optional[str]
    
    # Compliance tracking
    privilege_access_log: List[Dict[str, Any]]
    compliance_notes: List[str]

class AttorneySessionManager:
    """Enterprise attorney session management system"""
    
    def __init__(self, db_path: str = "attorney_sessions.db"):
        self.db_path = db_path
        self.secret_key = self._load_or_create_secret()
        self.logger = self._setup_logger()
        self._init_database()
        
        # Session configuration
        self.config = {
            # Timeout settings by role
            "role_timeouts": {
                "receptionist": {"idle": 240, "absolute": 480},      # 4/8 hours
                "legal_assistant": {"idle": 480, "absolute": 720},   # 8/12 hours  
                "paralegal": {"idle": 480, "absolute": 720},         # 8/12 hours
                "associate": {"idle": 720, "absolute": 1440},        # 12/24 hours
                "partner": {"idle": 720, "absolute": 1440},          # 12/24 hours
                "managing_partner": {"idle": 480, "absolute": 720},  # 8/12 hours (security)
            },
            
            # Security settings
            "max_concurrent_sessions": 3,
            "privileged_session_timeout": 120,  # 2 hours for privileged access
            "ip_change_tolerance": False,  # Strict IP checking
            "require_device_fingerprinting": True,
            "session_encryption": True,
            
            # Risk assessment thresholds
            "risk_thresholds": {
                "high_privilege_accesses": 50,
                "rapid_api_calls": 100,
                "unusual_hours_access": True,
                "multiple_ip_addresses": 2
            }
        }
        
        # Start background session monitor
        self._start_session_monitor()
    
    def _load_or_create_secret(self) -> bytes:
        """Load or create JWT secret key"""
        secret_file = "attorney_session_secret.key"
        if os.path.exists(secret_file):
            with open(secret_file, 'rb') as f:
                return f.read()
        else:
            secret = secrets.token_bytes(64)
            with open(secret_file, 'wb') as f:
                f.write(secret)
            os.chmod(secret_file, 0o600)
            return secret
    
    def _setup_logger(self) -> logging.Logger:
        """Setup session management logger"""
        logger = logging.getLogger('attorney_sessions')
        logger.setLevel(logging.INFO)
        
        Path('logs').mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/attorney_sessions.log',
            maxBytes=50*1024*1024,
            backupCount=100,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - SESSION - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize session management database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Attorney sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attorney_sessions (
                session_id TEXT PRIMARY KEY,
                attorney_id TEXT NOT NULL,
                attorney_email TEXT NOT NULL,
                attorney_role TEXT NOT NULL,
                bar_number TEXT,
                created_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                idle_timeout_minutes INTEGER NOT NULL,
                absolute_timeout_minutes INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                device_fingerprint TEXT NOT NULL,
                geolocation TEXT,
                status TEXT NOT NULL,
                is_privileged_session BOOLEAN NOT NULL,
                risk_level TEXT NOT NULL,
                security_flags TEXT NOT NULL,
                page_views INTEGER DEFAULT 0,
                document_accesses INTEGER DEFAULT 0,
                privileged_document_accesses INTEGER DEFAULT 0,
                client_data_accesses INTEGER DEFAULT 0,
                api_calls INTEGER DEFAULT 0,
                terminated_at TIMESTAMP,
                termination_reason TEXT,
                terminated_by TEXT,
                privilege_access_log TEXT NOT NULL,
                compliance_notes TEXT NOT NULL
            )
        ''')
        
        # Session activity log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_activity (
                activity_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                activity_description TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                risk_score REAL DEFAULT 0.0,
                requires_review BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (session_id) REFERENCES attorney_sessions (session_id)
            )
        ''')
        
        # Session security events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_security_events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                handled BOOLEAN DEFAULT FALSE,
                handler_notes TEXT,
                FOREIGN KEY (session_id) REFERENCES attorney_sessions (session_id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_attorney ON attorney_sessions (attorney_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON attorney_sessions (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON attorney_sessions (expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_session ON session_activity (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_session ON session_security_events (session_id)')
        
        conn.commit()
        conn.close()
    
    def create_attorney_session(
        self,
        attorney_id: str,
        attorney_email: str,
        attorney_role: str,
        ip_address: str,
        user_agent: str,
        bar_number: Optional[str] = None,
        is_privileged_session: bool = False
    ) -> Tuple[str, str]:  # Returns (session_id, jwt_token)
        """Create new attorney session with security validation"""
        
        # Check for existing active sessions
        active_sessions = self._get_active_sessions(attorney_id)
        if len(active_sessions) >= self.config["max_concurrent_sessions"]:
            # Terminate oldest session
            oldest_session = min(active_sessions, key=lambda x: x.created_at)
            self.terminate_session(
                oldest_session.session_id,
                SessionTerminationReason.CONCURRENT_LIMIT,
                "system"
            )
        
        # Generate session ID
        session_id = secrets.token_urlsafe(32)
        
        # Get timeout settings for role
        role_config = self.config["role_timeouts"].get(
            attorney_role, 
            self.config["role_timeouts"]["associate"]
        )
        
        idle_timeout = role_config["idle"]
        absolute_timeout = role_config["absolute"]
        
        # Adjust for privileged sessions
        if is_privileged_session:
            idle_timeout = min(idle_timeout, self.config["privileged_session_timeout"])
            absolute_timeout = min(absolute_timeout, self.config["privileged_session_timeout"])
        
        # Create timestamps
        now = datetime.now()
        expires_at = now + timedelta(minutes=absolute_timeout)
        
        # Generate device fingerprint
        device_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
        
        # Assess initial risk level
        risk_level = self._assess_session_risk(
            attorney_id, ip_address, user_agent, is_privileged_session
        )
        
        # Create session object
        session = AttorneySession(
            session_id=session_id,
            attorney_id=attorney_id,
            attorney_email=attorney_email,
            attorney_role=attorney_role,
            bar_number=bar_number,
            created_at=now,
            last_activity=now,
            expires_at=expires_at,
            idle_timeout_minutes=idle_timeout,
            absolute_timeout_minutes=absolute_timeout,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            geolocation=self._get_ip_geolocation(ip_address),
            status=SessionStatus.ACTIVE,
            is_privileged_session=is_privileged_session,
            risk_level=risk_level,
            security_flags=[],
            page_views=0,
            document_accesses=0,
            privileged_document_accesses=0,
            client_data_accesses=0,
            api_calls=0,
            terminated_at=None,
            termination_reason=None,
            terminated_by=None,
            privilege_access_log=[],
            compliance_notes=[]
        )
        
        # Store session in database
        self._store_session(session)
        
        # Generate JWT token
        jwt_token = self._generate_jwt_token(session)
        
        # Log session creation
        self.logger.info(
            f"Attorney session created: {session_id[:8]}... - "
            f"Attorney: {attorney_email} - Role: {attorney_role} - "
            f"Privileged: {is_privileged_session} - Risk: {risk_level.value}"
        )
        
        return session_id, jwt_token
    
    def _generate_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Generate device fingerprint for session tracking"""
        fingerprint_data = f"{user_agent}:{ip_address}:{datetime.now().date()}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def _assess_session_risk(
        self,
        attorney_id: str,
        ip_address: str,
        user_agent: str,
        is_privileged: bool
    ) -> RiskLevel:
        """Assess initial session risk level"""
        risk_score = 0
        
        # Check for unusual IP address
        if not self._is_known_ip(attorney_id, ip_address):
            risk_score += 2
        
        # Check for unusual user agent
        if not self._is_known_user_agent(attorney_id, user_agent):
            risk_score += 1
        
        # Privileged session increases risk
        if is_privileged:
            risk_score += 1
        
        # Check time of access
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Outside business hours
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _get_ip_geolocation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get IP geolocation (placeholder for real implementation)"""
        try:
            # In production, use a real geolocation service
            if ipaddress.ip_address(ip_address).is_private:
                return {"country": "Local", "city": "Private Network", "is_private": True}
            else:
                return {"country": "Unknown", "city": "Unknown", "is_private": False}
        except:
            return None
    
    def _is_known_ip(self, attorney_id: str, ip_address: str) -> bool:
        """Check if IP address is known for this attorney"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check last 30 days of sessions
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        cursor.execute('''
            SELECT COUNT(*) FROM attorney_sessions
            WHERE attorney_id = ? AND ip_address = ? AND created_at >= ?
        ''', (attorney_id, ip_address, thirty_days_ago.isoformat()))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def _is_known_user_agent(self, attorney_id: str, user_agent: str) -> bool:
        """Check if user agent is known for this attorney"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check last 30 days of sessions
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        cursor.execute('''
            SELECT COUNT(*) FROM attorney_sessions
            WHERE attorney_id = ? AND user_agent = ? AND created_at >= ?
        ''', (attorney_id, user_agent, thirty_days_ago.isoformat()))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def _generate_jwt_token(self, session: AttorneySession) -> str:
        """Generate JWT token for session"""
        payload = {
            "session_id": session.session_id,
            "attorney_id": session.attorney_id,
            "attorney_email": session.attorney_email,
            "attorney_role": session.attorney_role,
            "bar_number": session.bar_number,
            "is_privileged": session.is_privileged_session,
            "iat": int(session.created_at.timestamp()),
            "exp": int(session.expires_at.timestamp()),
            "device_fingerprint": session.device_fingerprint
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_session_token(self, token: str, ip_address: str) -> Optional[AttorneySession]:
        """Validate JWT session token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            session_id = payload['session_id']
            
            # Get session from database
            session = self._get_session_by_id(session_id)
            if not session:
                return None
            
            # Check session status
            if session.status != SessionStatus.ACTIVE:
                return None
            
            # Check IP address consistency (if required)
            if not self.config["ip_change_tolerance"] and session.ip_address != ip_address:
                self._log_security_event(
                    session_id, 
                    "IP_ADDRESS_CHANGE",
                    "HIGH",
                    f"IP changed from {session.ip_address} to {ip_address}"
                )
                # Terminate session for security
                self.terminate_session(
                    session_id,
                    SessionTerminationReason.IP_CHANGE,
                    "system"
                )
                return None
            
            # Check for expiration
            now = datetime.now()
            if now > session.expires_at:
                self.terminate_session(
                    session_id,
                    SessionTerminationReason.TIMEOUT_ABSOLUTE,
                    "system"
                )
                return None
            
            # Check idle timeout
            idle_limit = session.last_activity + timedelta(minutes=session.idle_timeout_minutes)
            if now > idle_limit:
                self.terminate_session(
                    session_id,
                    SessionTerminationReason.TIMEOUT_IDLE,
                    "system"
                )
                return None
            
            # Update last activity
            self._update_session_activity(session_id, now)
            session.last_activity = now
            
            return session
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _store_session(self, session: AttorneySession):
        """Store session in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO attorney_sessions (
                    session_id, attorney_id, attorney_email, attorney_role, bar_number,
                    created_at, last_activity, expires_at, idle_timeout_minutes,
                    absolute_timeout_minutes, ip_address, user_agent, device_fingerprint,
                    geolocation, status, is_privileged_session, risk_level, security_flags,
                    page_views, document_accesses, privileged_document_accesses,
                    client_data_accesses, api_calls, terminated_at, termination_reason,
                    terminated_by, privilege_access_log, compliance_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id, session.attorney_id, session.attorney_email,
                session.attorney_role, session.bar_number, session.created_at.isoformat(),
                session.last_activity.isoformat(), session.expires_at.isoformat(),
                session.idle_timeout_minutes, session.absolute_timeout_minutes,
                session.ip_address, session.user_agent, session.device_fingerprint,
                json.dumps(session.geolocation) if session.geolocation else None,
                session.status.value, session.is_privileged_session, session.risk_level.value,
                json.dumps(session.security_flags), session.page_views, session.document_accesses,
                session.privileged_document_accesses, session.client_data_accesses,
                session.api_calls, session.terminated_at.isoformat() if session.terminated_at else None,
                session.termination_reason.value if session.termination_reason else None,
                session.terminated_by, json.dumps(session.privilege_access_log),
                json.dumps(session.compliance_notes)
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def _get_active_sessions(self, attorney_id: str) -> List[AttorneySession]:
        """Get all active sessions for attorney"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM attorney_sessions
            WHERE attorney_id = ? AND status = ?
            ORDER BY created_at DESC
        ''', (attorney_id, SessionStatus.ACTIVE.value))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        sessions = []
        for row in rows:
            session_data = dict(zip(columns, row))
            session = self._row_to_session(session_data)
            sessions.append(session)
        
        conn.close()
        return sessions
    
    def terminate_session(
        self,
        session_id: str,
        reason: SessionTerminationReason,
        terminated_by: str
    ) -> bool:
        """Terminate attorney session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE attorney_sessions
                SET status = ?, terminated_at = ?, termination_reason = ?, terminated_by = ?
                WHERE session_id = ? AND status = ?
            ''', (
                SessionStatus.TERMINATED.value,
                datetime.now().isoformat(),
                reason.value,
                terminated_by,
                session_id,
                SessionStatus.ACTIVE.value
            ))
            
            success = cursor.rowcount > 0
            conn.commit()
            
            if success:
                self.logger.info(
                    f"Session terminated: {session_id[:8]}... - "
                    f"Reason: {reason.value} - By: {terminated_by}"
                )
            
            return success
            
        finally:
            conn.close()
    
    def _start_session_monitor(self):
        """Start background session monitoring thread"""
        def monitor_sessions():
            while True:
                try:
                    self._cleanup_expired_sessions()
                    self._check_suspicious_activity()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    self.logger.error(f"Session monitor error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        monitor_thread = threading.Thread(target=monitor_sessions, daemon=True)
        monitor_thread.start()
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Find expired sessions
        cursor.execute('''
            SELECT session_id FROM attorney_sessions
            WHERE status = ? AND expires_at < ?
        ''', (SessionStatus.ACTIVE.value, now.isoformat()))
        
        expired_sessions = [row[0] for row in cursor.fetchall()]
        
        # Terminate expired sessions
        for session_id in expired_sessions:
            self.terminate_session(
                session_id,
                SessionTerminationReason.TIMEOUT_ABSOLUTE,
                "system"
            )
        
        conn.close()
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global attorney session manager instance
attorney_session_manager = AttorneySessionManager()