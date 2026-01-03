"""
Security Audit Logging

Comprehensive audit trail for security events, user actions, and data access.
Compliant with SOC 2, ISO 27001, and regulatory requirements.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ...database import Base

logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS
# =============================================================================

class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"

    # Authorization
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    ROLE_CHANGED = "role_changed"

    # Data Access
    DATA_READ = "data_read"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"

    # Document Operations
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    DOCUMENT_SHARED = "document_shared"
    DOCUMENT_DELETED = "document_deleted"

    # Administrative
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_SUSPENDED = "user_suspended"
    CONFIG_CHANGED = "config_changed"

    # Security Events
    SECURITY_ALERT = "security_alert"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"

    # Compliance
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    GDPR_REQUEST = "gdpr_request"
    DATA_RETENTION_APPLIED = "data_retention_applied"

    # System Events
    SYSTEM_ERROR = "system_error"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# DATABASE MODELS
# =============================================================================

class AuditLog(Base):
    """
    Comprehensive audit log for security and compliance.

    Stores all security-relevant events with full context.
    Immutable after creation (no updates or deletes).
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default=AuditSeverity.INFO.value)

    # User information
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    username = Column(String(100))
    user_email = Column(String(255))

    # Resource information
    resource_type = Column(String(100), index=True)  # e.g., "document", "user", "config"
    resource_id = Column(String(100), index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g., "create", "read", "update", "delete"
    description = Column(Text)

    # Request context
    ip_address = Column(String(45), index=True)  # IPv4 or IPv6
    user_agent = Column(Text)
    request_id = Column(String(100), index=True)
    session_id = Column(String(100))

    # Additional context
    event_metadata = Column(JSON)  # Flexible storage for event-specific data

    # Changes (for data modification events)
    old_values = Column(JSON)
    new_values = Column(JSON)

    # Timestamp (immutable)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Compliance tracking
    is_compliance_event = Column(Integer, default=0)  # Boolean for compliance-related events
    retention_until = Column(DateTime)  # When this log can be deleted

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.event_type} by {self.username} at {self.created_at}>"

    __table_args__ = (
        # Composite indexes for common queries
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_event_created', 'event_type', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id', 'created_at'),
        Index('idx_audit_compliance', 'is_compliance_event', 'created_at'),
        Index('idx_audit_ip_created', 'ip_address', 'created_at'),
    )


class SecurityAlert(Base):
    """
    High-priority security alerts requiring investigation.

    Separate from audit logs for immediate visibility.
    """
    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Alert details
    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default=AuditSeverity.WARNING.value)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Related audit log
    audit_log_id = Column(Integer, ForeignKey("audit_logs.id"))

    # User/IP information
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    ip_address = Column(String(45), index=True)

    # Alert data
    alert_metadata = Column(JSON)

    # Investigation
    status = Column(String(50), default="new", index=True)  # new, investigating, resolved, false_positive
    assigned_to = Column(Integer, ForeignKey("users.id"))
    investigated_at = Column(DateTime)
    resolution = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SecurityAlert {self.id}: {self.alert_type} - {self.status}>"


# =============================================================================
# AUDIT LOGGER
# =============================================================================

class AuditLogger:
    """
    Main audit logging service.

    Provides methods to log various security and compliance events.
    """

    @staticmethod
    def log_event(
        db: Session,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        is_compliance: bool = False,
        retention_days: int = 365,
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            db: Database session
            event_type: Type of event
            action: Action performed (create, read, update, delete)
            user_id: User ID (if applicable)
            username: Username
            user_email: User email
            resource_type: Type of resource (document, user, etc.)
            resource_id: Resource identifier
            description: Human-readable description
            ip_address: Client IP address
            user_agent: User agent string
            request_id: Request ID for tracing
            session_id: Session ID
            metadata: Additional event data
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            severity: Event severity
            is_compliance: Whether this is a compliance event
            retention_days: How long to retain this log

        Returns:
            Created AuditLog record
        """
        from datetime import timedelta

        # Calculate retention deadline
        retention_until = datetime.utcnow() + timedelta(days=retention_days)

        # Create audit log entry
        audit_log = AuditLog(
            event_type=event_type.value,
            severity=severity.value,
            user_id=user_id,
            username=username,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            session_id=session_id,
            event_metadata=metadata or {},
            old_values=old_values,
            new_values=new_values,
            is_compliance_event=1 if is_compliance else 0,
            retention_until=retention_until,
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        # Log to application logger as well
        log_level = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }.get(severity, logging.INFO)

        logger.log(
            log_level,
            f"Audit: {event_type.value} - {action} - User: {username or user_id} - Resource: {resource_type}/{resource_id}",
            extra={
                'audit_log_id': audit_log.id,
                'event_type': event_type.value,
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
            }
        )

        return audit_log

    @staticmethod
    def log_authentication(
        db: Session,
        event_type: AuditEventType,
        user_id: Optional[int],
        username: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log authentication event"""
        return AuditLogger.log_event(
            db=db,
            event_type=event_type,
            action="authenticate",
            user_id=user_id,
            username=username,
            description=f"Authentication {'successful' if success else 'failed'}: {reason or ''}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
        )

    @staticmethod
    def log_data_access(
        db: Session,
        user_id: int,
        username: str,
        action: str,
        resource_type: str,
        resource_id: str,
        ip_address: str,
        description: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
    ) -> AuditLog:
        """Log data access event"""
        event_type_map = {
            'read': AuditEventType.DATA_READ,
            'create': AuditEventType.DATA_CREATED,
            'update': AuditEventType.DATA_UPDATED,
            'delete': AuditEventType.DATA_DELETED,
            'export': AuditEventType.DATA_EXPORTED,
        }

        return AuditLogger.log_event(
            db=db,
            event_type=event_type_map.get(action, AuditEventType.DATA_READ),
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            old_values=old_values,
            new_values=new_values,
        )

    @staticmethod
    def log_document_operation(
        db: Session,
        operation: str,
        user_id: int,
        username: str,
        document_id: str,
        document_name: str,
        ip_address: str,
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """Log document operation"""
        event_type_map = {
            'upload': AuditEventType.DOCUMENT_UPLOADED,
            'download': AuditEventType.DOCUMENT_DOWNLOADED,
            'share': AuditEventType.DOCUMENT_SHARED,
            'delete': AuditEventType.DOCUMENT_DELETED,
        }

        return AuditLogger.log_event(
            db=db,
            event_type=event_type_map.get(operation, AuditEventType.DATA_READ),
            action=operation,
            user_id=user_id,
            username=username,
            resource_type='document',
            resource_id=document_id,
            description=f"Document {operation}: {document_name}",
            ip_address=ip_address,
            metadata=metadata,
        )

    @staticmethod
    def log_compliance_event(
        db: Session,
        event_type: AuditEventType,
        user_id: int,
        username: str,
        description: str,
        ip_address: str,
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """Log compliance event (GDPR/CCPA)"""
        return AuditLogger.log_event(
            db=db,
            event_type=event_type,
            action="compliance",
            user_id=user_id,
            username=username,
            description=description,
            ip_address=ip_address,
            metadata=metadata,
            is_compliance=True,
            retention_days=2555,  # 7 years for compliance
            severity=AuditSeverity.INFO,
        )

    @staticmethod
    def log_security_event(
        db: Session,
        event_type: AuditEventType,
        description: str,
        ip_address: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        metadata: Optional[Dict] = None,
        severity: AuditSeverity = AuditSeverity.WARNING,
    ) -> AuditLog:
        """Log security event"""
        return AuditLogger.log_event(
            db=db,
            event_type=event_type,
            action="security",
            user_id=user_id,
            username=username,
            description=description,
            ip_address=ip_address,
            metadata=metadata,
            severity=severity,
        )


# =============================================================================
# SECURITY ALERT MANAGER
# =============================================================================

class SecurityAlertManager:
    """
    Manages security alerts and investigations.
    """

    @staticmethod
    def create_alert(
        db: Session,
        alert_type: str,
        title: str,
        description: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        audit_log_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        severity: AuditSeverity = AuditSeverity.WARNING,
    ) -> SecurityAlert:
        """
        Create a security alert.

        Args:
            db: Database session
            alert_type: Type of alert
            title: Alert title
            description: Detailed description
            user_id: Related user ID
            ip_address: Source IP
            audit_log_id: Related audit log entry
            metadata: Additional data
            severity: Alert severity

        Returns:
            Created SecurityAlert
        """
        alert = SecurityAlert(
            alert_type=alert_type,
            title=title,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            audit_log_id=audit_log_id,
            alert_metadata=metadata or {},
            severity=severity.value,
            status='new',
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Log critical alerts
        if severity == AuditSeverity.CRITICAL:
            logger.critical(f"Security Alert: {title} - {description}")
        else:
            logger.warning(f"Security Alert: {title}")

        return alert

    @staticmethod
    def get_active_alerts(
        db: Session,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
    ) -> List[SecurityAlert]:
        """Get active security alerts"""
        query = db.query(SecurityAlert).filter(
            SecurityAlert.status.in_(['new', 'investigating'])
        )

        if severity:
            query = query.filter(SecurityAlert.severity == severity.value)

        return query.order_by(
            SecurityAlert.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def update_alert_status(
        db: Session,
        alert_id: int,
        status: str,
        assigned_to: Optional[int] = None,
        resolution: Optional[str] = None,
    ) -> SecurityAlert:
        """Update alert investigation status"""
        alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = status
        if assigned_to:
            alert.assigned_to = assigned_to
        if resolution:
            alert.resolution = resolution

        if status in ['resolved', 'false_positive']:
            alert.investigated_at = datetime.utcnow()

        db.commit()
        db.refresh(alert)

        return alert


# =============================================================================
# AUDIT QUERY HELPERS
# =============================================================================

class AuditQuery:
    """Helper class for querying audit logs"""

    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get user activity within date range"""
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_resource_history(
        db: Session,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get full history of a resource"""
        return db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_failed_logins(
        db: Session,
        hours: int = 24,
        threshold: int = 5,
    ) -> Dict[str, int]:
        """Get IPs with excessive failed login attempts"""
        from datetime import timedelta
        from sqlalchemy import func as sql_func

        since = datetime.utcnow() - timedelta(hours=hours)

        results = db.query(
            AuditLog.ip_address,
            sql_func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.event_type == AuditEventType.LOGIN_FAILURE.value,
            AuditLog.created_at >= since,
        ).group_by(AuditLog.ip_address).having(
            sql_func.count(AuditLog.id) >= threshold
        ).all()

        return {ip: count for ip, count in results}

    @staticmethod
    def get_compliance_events(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """Get all compliance-related events"""
        query = db.query(AuditLog).filter(AuditLog.is_compliance_event == 1)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return query.order_by(AuditLog.created_at.desc()).all()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'AuditEventType',
    'AuditSeverity',

    # Models
    'AuditLog',
    'SecurityAlert',

    # Services
    'AuditLogger',
    'SecurityAlertManager',
    'AuditQuery',
]
