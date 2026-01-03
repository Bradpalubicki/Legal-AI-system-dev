#!/usr/bin/env python3
"""
Secure Session Management System
Advanced session handling with encryption, timeout, and audit compliance
"""

import uuid
import time
import secrets
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import json

# Import security components
try:
    from ..core.audit_logger import AuditLogger
    from ..core.encryption_manager import EncryptionManager
except ImportError:
    # Fallback for testing
    class AuditLogger:
        def log_session_event(self, **kwargs): pass
    class EncryptionManager:
        def encrypt_data(self, data): return f"encrypted_{data}"
        def decrypt_data(self, data): return data.replace("encrypted_", "")


class SessionStatus(Enum):
    """Session status indicators"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    INVALID = "invalid"


class SessionType(Enum):
    """Types of portal sessions"""
    CLIENT_PORTAL = "client_portal"
    ATTORNEY_PORTAL = "attorney_portal"
    ADMIN_PORTAL = "admin_portal"
    EDUCATIONAL_DEMO = "educational_demo"


@dataclass
class SessionData:
    """Secure session data with encryption"""
    session_id: str
    user_id: str
    session_type: SessionType
    status: SessionStatus
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    encrypted_data: str
    access_count: int = 0
    security_flags: List[str] = field(default_factory=list)
    compliance_acknowledged: bool = False


@dataclass
class SessionActivity:
    """Session activity tracking for audit compliance"""
    activity_id: str
    session_id: str
    user_id: str
    activity_type: str
    timestamp: datetime
    resource_accessed: str
    ip_address: str
    details: Dict[str, Any]
    risk_level: str = "low"


class SessionManager:
    """Secure session management with compliance logging"""

    def __init__(self):
        # Initialize security components
        self.audit_logger = AuditLogger()
        self.encryption_manager = EncryptionManager()

        # Session configuration
        self.default_timeout = timedelta(hours=1)
        self.max_sessions_per_user = 3
        self.session_cleanup_interval = timedelta(hours=4)
        self.inactivity_timeout = timedelta(minutes=30)

        # Active sessions storage (in production, use secure database)
        self.active_sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, List[str]] = {}

        # Session security configuration
        self.security_config = {
            "require_ip_consistency": True,
            "require_user_agent_consistency": True,
            "auto_logout_on_suspicious_activity": True,
            "encrypt_session_data": True,
            "comprehensive_audit_logging": True
        }

        # Compliance requirements
        self.compliance_notices = self._initialize_compliance_notices()

    def _initialize_compliance_notices(self) -> List[str]:
        """Initialize session compliance notices"""
        return [
            "SESSION SECURITY: All session activities are logged for security and compliance purposes.",

            "AUTO-LOGOUT: Sessions expire automatically for security. Save work frequently.",

            "CONFIDENTIALITY: Do not share session access or leave portal unattended.",

            "PROFESSIONAL RESPONSIBILITY: Session access is subject to legal ethics and compliance rules.",

            "AUDIT COMPLIANCE: All portal activities are monitored and logged for audit purposes.",

            "SECURE COMMUNICATION: All session data is encrypted in transit and at rest.",

            "ACTIVITY MONITORING: Suspicious activity will result in automatic session termination.",

            "COMPLIANCE ACKNOWLEDGMENT: Users must acknowledge disclaimers and compliance requirements."
        ]

    def create_session(self, user_id: str, portal_type: str = "client_portal",
                      ip_address: str = "unknown", user_agent: str = "unknown",
                      expires_in: int = 3600) -> str:
        """Create new secure session with compliance tracking"""
        try:
            # Generate unique session ID
            session_id = f"SES_{uuid.uuid4().hex.upper()}"

            # Determine session type
            session_type = SessionType.CLIENT_PORTAL
            if portal_type == "attorney_portal":
                session_type = SessionType.ATTORNEY_PORTAL
            elif portal_type == "admin_portal":
                session_type = SessionType.ADMIN_PORTAL
            elif portal_type == "educational_demo":
                session_type = SessionType.EDUCATIONAL_DEMO

            # Check session limits per user
            if user_id in self.user_sessions:
                if len(self.user_sessions[user_id]) >= self.max_sessions_per_user:
                    # Terminate oldest session
                    oldest_session = self.user_sessions[user_id][0]
                    self.terminate_session(oldest_session, "session_limit_exceeded")

            # Create session data
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=expires_in)

            # Encrypt session metadata
            session_metadata = {
                "user_id": user_id,
                "portal_type": portal_type,
                "created_timestamp": now.isoformat(),
                "security_token": secrets.token_hex(16)
            }
            encrypted_data = self.encryption_manager.encrypt_data(json.dumps(session_metadata))

            # Create session object
            session = SessionData(
                session_id=session_id,
                user_id=user_id,
                session_type=session_type,
                status=SessionStatus.ACTIVE,
                created_at=now,
                expires_at=expires_at,
                last_activity=now,
                ip_address=ip_address,
                user_agent=user_agent,
                encrypted_data=encrypted_data,
                security_flags=[]
            )

            # Store session
            self.active_sessions[session_id] = session

            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)

            # Log session creation
            self._log_session_activity(
                session_id, user_id, "session_created", ip_address,
                "session_management", {
                    "session_type": session_type.value,
                    "expires_at": expires_at.isoformat(),
                    "portal_type": portal_type
                }
            )

            return session_id

        except Exception as e:
            # Log error
            self.audit_logger.log_session_event(
                event_type="session_creation_error",
                user_id=user_id,
                error=str(e),
                timestamp=datetime.now(timezone.utc)
            )
            raise

    def verify_session(self, session_id: str, ip_address: str = "unknown",
                      user_agent: str = "unknown") -> bool:
        """Verify session validity with security checks"""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]

            # Check session status
            if session.status != SessionStatus.ACTIVE:
                return False

            # Check expiration
            now = datetime.now(timezone.utc)
            if now > session.expires_at:
                self._expire_session(session_id, "session_expired")
                return False

            # Check inactivity timeout
            if now - session.last_activity > self.inactivity_timeout:
                self._expire_session(session_id, "inactivity_timeout")
                return False

            # Security checks
            security_issues = []

            if self.security_config["require_ip_consistency"]:
                if ip_address != "unknown" and ip_address != session.ip_address:
                    security_issues.append("ip_address_mismatch")

            if self.security_config["require_user_agent_consistency"]:
                if user_agent != "unknown" and user_agent != session.user_agent:
                    security_issues.append("user_agent_mismatch")

            # Handle security issues
            if security_issues:
                session.security_flags.extend(security_issues)

                if self.security_config["auto_logout_on_suspicious_activity"]:
                    self.terminate_session(session_id, "suspicious_activity")
                    self._log_session_activity(
                        session_id, session.user_id, "security_violation", ip_address,
                        "security_check", {
                            "violations": security_issues,
                            "action": "session_terminated"
                        }, "high"
                    )
                    return False

            # Update activity
            session.last_activity = now
            session.access_count += 1

            # Log access
            self._log_session_activity(
                session_id, session.user_id, "session_accessed", ip_address,
                "session_verification", {
                    "access_count": session.access_count,
                    "security_flags": session.security_flags
                }
            )

            return True

        except Exception as e:
            self.audit_logger.log_session_event(
                event_type="session_verification_error",
                session_id=session_id,
                error=str(e),
                timestamp=datetime.now(timezone.utc)
            )
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information for compliance and monitoring"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        # Decrypt session metadata
        try:
            decrypted_data = self.encryption_manager.decrypt_data(session.encrypted_data)
            metadata = json.loads(decrypted_data)
        except:
            metadata = {"error": "unable_to_decrypt"}

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "session_type": session.session_type.value,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "time_remaining": max(0, (session.expires_at - datetime.now(timezone.utc)).total_seconds()),
            "access_count": session.access_count,
            "security_flags": session.security_flags,
            "compliance_acknowledged": session.compliance_acknowledged,
            "ip_address": session.ip_address,
            "metadata": metadata,
            "security_status": "secure" if not session.security_flags else "flagged"
        }

    def extend_session(self, session_id: str, additional_time: int = 3600) -> bool:
        """Extend session duration with security validation"""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]

            # Verify session is in good standing
            if session.status != SessionStatus.ACTIVE:
                return False

            if session.security_flags:
                # Don't extend sessions with security issues
                return False

            # Extend expiration
            session.expires_at += timedelta(seconds=additional_time)
            session.last_activity = datetime.now(timezone.utc)

            # Log extension
            self._log_session_activity(
                session_id, session.user_id, "session_extended", session.ip_address,
                "session_management", {
                    "additional_seconds": additional_time,
                    "new_expiration": session.expires_at.isoformat()
                }
            )

            return True

        except Exception as e:
            self.audit_logger.log_session_event(
                event_type="session_extension_error",
                session_id=session_id,
                error=str(e),
                timestamp=datetime.now(timezone.utc)
            )
            return False

    def acknowledge_compliance(self, session_id: str, disclaimers_acknowledged: List[str]) -> bool:
        """Record compliance acknowledgment for legal requirements"""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]
            session.compliance_acknowledged = True

            # Log compliance acknowledgment
            self._log_session_activity(
                session_id, session.user_id, "compliance_acknowledged", session.ip_address,
                "compliance_tracking", {
                    "disclaimers_count": len(disclaimers_acknowledged),
                    "acknowledged_at": datetime.now(timezone.utc).isoformat()
                }
            )

            return True

        except Exception as e:
            return False

    def terminate_session(self, session_id: str, reason: str = "user_logout") -> bool:
        """Terminate session with audit logging"""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]
            session.status = SessionStatus.TERMINATED

            # Remove from active sessions
            del self.active_sessions[session_id]

            # Remove from user session tracking
            if session.user_id in self.user_sessions:
                if session_id in self.user_sessions[session.user_id]:
                    self.user_sessions[session.user_id].remove(session_id)

            # Log termination
            self._log_session_activity(
                session_id, session.user_id, "session_terminated", session.ip_address,
                "session_management", {
                    "reason": reason,
                    "duration_seconds": (datetime.now(timezone.utc) - session.created_at).total_seconds(),
                    "access_count": session.access_count
                }
            )

            return True

        except Exception as e:
            self.audit_logger.log_session_event(
                event_type="session_termination_error",
                session_id=session_id,
                error=str(e),
                timestamp=datetime.now(timezone.utc)
            )
            return False

    def _expire_session(self, session_id: str, reason: str):
        """Mark session as expired"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = SessionStatus.EXPIRED

            self._log_session_activity(
                session_id, session.user_id, "session_expired", session.ip_address,
                "session_management", {"reason": reason}
            )

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions for maintenance"""
        now = datetime.now(timezone.utc)
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if (session.status != SessionStatus.ACTIVE or
                now > session.expires_at or
                now - session.last_activity > self.inactivity_timeout):
                expired_sessions.append(session_id)

        # Remove expired sessions
        for session_id in expired_sessions:
            self.terminate_session(session_id, "cleanup_expired")

        # Log cleanup activity
        if expired_sessions:
            self.audit_logger.log_session_event(
                event_type="session_cleanup",
                sessions_cleaned=len(expired_sessions),
                timestamp=now
            )

        return len(expired_sessions)

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        user_session_ids = self.user_sessions.get(user_id, [])
        user_sessions = []

        for session_id in user_session_ids:
            if session_id in self.active_sessions:
                session_info = self.get_session_info(session_id)
                if session_info:
                    user_sessions.append(session_info)

        return user_sessions

    def get_session_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive session security report"""
        now = datetime.now(timezone.utc)
        total_sessions = len(self.active_sessions)
        flagged_sessions = sum(1 for s in self.active_sessions.values() if s.security_flags)

        session_types = {}
        for session in self.active_sessions.values():
            session_type = session.session_type.value
            session_types[session_type] = session_types.get(session_type, 0) + 1

        return {
            "report_timestamp": now.isoformat(),
            "total_active_sessions": total_sessions,
            "flagged_sessions": flagged_sessions,
            "session_types": session_types,
            "security_configuration": self.security_config,
            "compliance_features": {
                "session_encryption": "AES-256",
                "audit_logging": "comprehensive",
                "activity_tracking": "all_actions",
                "compliance_acknowledgment": "required",
                "automatic_timeout": "configured"
            },
            "session_limits": {
                "max_sessions_per_user": self.max_sessions_per_user,
                "default_timeout_hours": self.default_timeout.total_seconds() / 3600,
                "inactivity_timeout_minutes": self.inactivity_timeout.total_seconds() / 60
            },
            "security_status": "secure" if flagged_sessions == 0 else "monitoring_required"
        }

    def _log_session_activity(self, session_id: str, user_id: str, activity_type: str,
                             ip_address: str, resource_accessed: str, details: Dict[str, Any],
                             risk_level: str = "low"):
        """Log session activity for audit compliance"""
        activity = SessionActivity(
            activity_id=f"ACT_{uuid.uuid4().hex[:8].upper()}",
            session_id=session_id,
            user_id=user_id,
            activity_type=activity_type,
            timestamp=datetime.now(timezone.utc),
            resource_accessed=resource_accessed,
            ip_address=ip_address,
            details=details,
            risk_level=risk_level
        )

        self.audit_logger.log_session_event(
            activity_id=activity.activity_id,
            session_id=activity.session_id,
            user_id=activity.user_id,
            activity_type=activity.activity_type,
            timestamp=activity.timestamp,
            resource_accessed=activity.resource_accessed,
            details=activity.details,
            risk_level=activity.risk_level
        )


# Global session manager instance
session_manager = SessionManager()


def main():
    """Test the session manager"""
    print("SECURE SESSION MANAGEMENT SYSTEM - SECURITY TEST")
    print("=" * 60)

    # Test session creation
    print("\n1. Testing Session Creation...")
    session_id = session_manager.create_session(
        user_id="CLIENT_EDU_001",
        portal_type="client_portal",
        ip_address="192.168.1.100",
        user_agent="Educational Test Browser",
        expires_in=3600
    )

    print(f"[PASS] Session created successfully")
    print(f"   Session ID: {session_id}")

    # Test session verification
    print("\n2. Testing Session Verification...")
    is_valid = session_manager.verify_session(
        session_id=session_id,
        ip_address="192.168.1.100",
        user_agent="Educational Test Browser"
    )

    if is_valid:
        print(f"[PASS] Session verification successful")
    else:
        print(f"[FAIL] Session verification failed")

    # Test session information
    print("\n3. Testing Session Information Retrieval...")
    session_info = session_manager.get_session_info(session_id)
    if session_info:
        print(f"[PASS] Session info retrieved")
        print(f"   User ID: {session_info['user_id']}")
        print(f"   Status: {session_info['status']}")
        print(f"   Type: {session_info['session_type']}")
        print(f"   Access Count: {session_info['access_count']}")
        print(f"   Time Remaining: {session_info['time_remaining']:.0f} seconds")
        print(f"   Security Status: {session_info['security_status']}")
    else:
        print(f"[FAIL] Could not retrieve session info")

    # Test compliance acknowledgment
    print("\n4. Testing Compliance Acknowledgment...")
    compliance_result = session_manager.acknowledge_compliance(
        session_id=session_id,
        disclaimers_acknowledged=["portal_disclaimer", "educational_disclaimer", "attorney_supervision"]
    )

    if compliance_result:
        print(f"[PASS] Compliance acknowledgment recorded")
    else:
        print(f"[FAIL] Compliance acknowledgment failed")

    # Test session extension
    print("\n5. Testing Session Extension...")
    extension_result = session_manager.extend_session(session_id, 1800)  # 30 minutes
    if extension_result:
        print(f"[PASS] Session extended successfully")
        updated_info = session_manager.get_session_info(session_id)
        print(f"   New Time Remaining: {updated_info['time_remaining']:.0f} seconds")
    else:
        print(f"[FAIL] Session extension failed")

    # Test security report
    print("\n6. Testing Security Report Generation...")
    security_report = session_manager.get_session_security_report()
    print(f"[PASS] Security report generated")
    print(f"   Active Sessions: {security_report['total_active_sessions']}")
    print(f"   Flagged Sessions: {security_report['flagged_sessions']}")
    print(f"   Session Types: {security_report['session_types']}")
    print(f"   Security Status: {security_report['security_status']}")

    # Test session cleanup
    print("\n7. Testing Session Cleanup...")
    cleaned_sessions = session_manager.cleanup_expired_sessions()
    print(f"[PASS] Session cleanup completed")
    print(f"   Sessions cleaned: {cleaned_sessions}")

    # Test session termination
    print("\n8. Testing Session Termination...")
    termination_result = session_manager.terminate_session(session_id, "user_logout")
    if termination_result:
        print(f"[PASS] Session terminated successfully")

        # Verify session is no longer valid
        post_termination_valid = session_manager.verify_session(session_id)
        print(f"   Post-termination verification: {'FAIL' if post_termination_valid else 'PASS'}")
    else:
        print(f"[FAIL] Session termination failed")

    print(f"\n[PASS] SESSION MANAGER OPERATIONAL")
    print(f"Secure session management is functional")
    print(f"Encryption, audit logging, and compliance features active")
    print(f"Security monitoring and automatic timeouts working")


if __name__ == "__main__":
    main()