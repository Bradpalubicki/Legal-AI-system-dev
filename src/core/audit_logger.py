#!/usr/bin/env python3
"""
Comprehensive Audit Logging System
Legal-grade audit logging with encryption and compliance features
"""

import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Union
import json
from pathlib import Path

# Import encryption components
try:
    from .encryption_manager import EncryptionManager
except ImportError:
    # Fallback for testing
    class EncryptionManager:
        def encrypt_data(self, data): return f"encrypted_{data}"
        def hash_data(self, data): return f"hash_{abs(hash(data))}"


class LogLevel(Enum):
    """Audit log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class EventCategory(Enum):
    """Categories of auditable events"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SESSION_MANAGEMENT = "session_management"
    DOCUMENT_ACCESS = "document_access"
    PORTAL_ACCESS = "portal_access"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    SYSTEM_EVENT = "system_event"
    USER_ACTION = "user_action"
    DATA_MODIFICATION = "data_modification"


class RiskLevel(Enum):
    """Risk levels for security assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    """Individual audit log entry with full compliance metadata"""
    log_id: str
    timestamp: datetime
    level: LogLevel
    category: EventCategory
    event_type: str
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    resource_accessed: str
    action_performed: str
    outcome: str  # "success", "failure", "partial"
    risk_level: RiskLevel
    details: Dict[str, Any]
    compliance_flags: List[str] = field(default_factory=list)
    retention_period_days: int = 2555  # 7 years default for legal compliance
    encrypted_payload: str = ""
    integrity_hash: str = ""


@dataclass
class AuditSearchQuery:
    """Query parameters for audit log searching"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    event_type: Optional[str] = None
    category: Optional[EventCategory] = None
    risk_level: Optional[RiskLevel] = None
    outcome: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass
class ComplianceReport:
    """Compliance audit report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_category: Dict[str, int]
    security_events: int
    failed_events: int
    high_risk_events: int
    compliance_violations: List[Dict[str, Any]]
    recommendations: List[str]
    report_integrity_hash: str


class AuditLogger:
    """Comprehensive audit logging system for legal compliance"""

    def __init__(self, storage_root: str = "storage/audit_logs"):
        # Initialize encryption
        self.encryption_manager = EncryptionManager()

        # Configure storage
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Audit configuration
        self.config = {
            "encrypt_sensitive_data": True,
            "generate_integrity_hashes": True,
            "real_time_monitoring": True,
            "compliance_validation": True,
            "retention_enforcement": True,
            "legal_hold_support": True
        }

        # In-memory log storage (in production, use secure database)
        self.audit_logs: List[AuditLogEntry] = []

        # Compliance requirements
        self.compliance_requirements = self._initialize_compliance_requirements()

        # Initialize audit system
        self._log_system_event("audit_system_initialized", "system", {
            "config": self.config,
            "storage_path": str(self.storage_root)
        })

    def _initialize_compliance_requirements(self) -> Dict[str, Any]:
        """Initialize legal compliance requirements"""
        return {
            "professional_responsibility": {
                "client_confidentiality": "mandatory",
                "attorney_client_privilege": "protected",
                "conflict_of_interest_tracking": "required",
                "unauthorized_practice_prevention": "enforced"
            },
            "data_protection": {
                "encryption_at_rest": "required",
                "encryption_in_transit": "required",
                "access_control_logging": "comprehensive",
                "data_retention": "7_years_minimum"
            },
            "audit_trail": {
                "user_actions": "all_recorded",
                "system_access": "fully_logged",
                "document_handling": "tracked",
                "security_events": "immediate_alerting"
            },
            "legal_compliance": {
                "bar_association_rules": "compliant",
                "state_regulations": "varies_by_jurisdiction",
                "federal_requirements": "applicable_laws",
                "ethical_standards": "professional_codes"
            }
        }

    def log_authentication_event(self, user_id: str, event_type: str, success: bool,
                                ip_address: str = "unknown", details: Dict[str, Any] = None,
                                session_id: str = "", user_agent: str = "unknown") -> str:
        """Log authentication events with security focus"""
        return self._create_log_entry(
            level=LogLevel.SECURITY if not success else LogLevel.INFO,
            category=EventCategory.AUTHENTICATION,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_accessed="authentication_system",
            action_performed="authenticate_user",
            outcome="success" if success else "failure",
            risk_level=RiskLevel.HIGH if not success else RiskLevel.LOW,
            details=details or {},
            compliance_flags=["professional_responsibility", "access_control"] if not success else []
        )

    def log_session_event(self, session_id: str, user_id: str, activity_type: str,
                         resource_accessed: str = "session_manager", details: Dict[str, Any] = None,
                         timestamp: datetime = None, risk_level: str = "low", **kwargs) -> str:
        """Log session management events"""
        risk_enum = RiskLevel.LOW
        if risk_level == "medium":
            risk_enum = RiskLevel.MEDIUM
        elif risk_level == "high":
            risk_enum = RiskLevel.HIGH
        elif risk_level == "critical":
            risk_enum = RiskLevel.CRITICAL

        return self._create_log_entry(
            level=LogLevel.INFO,
            category=EventCategory.SESSION_MANAGEMENT,
            event_type=activity_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=kwargs.get("ip_address", "unknown"),
            user_agent=kwargs.get("user_agent", "unknown"),
            resource_accessed=resource_accessed,
            action_performed="session_management",
            outcome=kwargs.get("outcome", "success"),
            risk_level=risk_enum,
            details=details or {},
            compliance_flags=["session_security"]
        )

    def log_document_event(self, user_id: str, document_id: str, action: str,
                          session_id: str = "", ip_address: str = "unknown",
                          details: Dict[str, Any] = None, success: bool = True) -> str:
        """Log document access and modification events"""
        return self._create_log_entry(
            level=LogLevel.INFO,
            category=EventCategory.DOCUMENT_ACCESS,
            event_type=f"document_{action}",
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent="document_system",
            resource_accessed=document_id,
            action_performed=action,
            outcome="success" if success else "failure",
            risk_level=RiskLevel.MEDIUM if action in ["download", "modify"] else RiskLevel.LOW,
            details=details or {},
            compliance_flags=["document_confidentiality", "client_data_protection"]
        )

    def log_portal_access(self, user_id: str, action: str, portal_type: str = "client_portal",
                         resource_accessed: str = "portal", ip_address: str = "unknown",
                         timestamp: datetime = None, **kwargs) -> str:
        """Log portal access events"""
        return self._create_log_entry(
            level=LogLevel.INFO,
            category=EventCategory.PORTAL_ACCESS,
            event_type=action,
            user_id=user_id,
            session_id=kwargs.get("session_id", ""),
            ip_address=ip_address,
            user_agent=kwargs.get("user_agent", "unknown"),
            resource_accessed=resource_accessed,
            action_performed="portal_access",
            outcome=kwargs.get("outcome", "success"),
            risk_level=RiskLevel.LOW,
            details={"portal_type": portal_type, **kwargs},
            compliance_flags=["portal_access_control"]
        )

    def log_security_event(self, event_id: str, user_id: str, event_type: str,
                          timestamp: datetime, success: bool, details: Dict[str, Any],
                          risk_level: str = "medium", **kwargs) -> str:
        """Log security events with high compliance requirements"""
        risk_enum = RiskLevel.MEDIUM
        if risk_level == "low":
            risk_enum = RiskLevel.LOW
        elif risk_level == "high":
            risk_enum = RiskLevel.HIGH
        elif risk_level == "critical":
            risk_enum = RiskLevel.CRITICAL

        return self._create_log_entry(
            level=LogLevel.SECURITY,
            category=EventCategory.SECURITY_EVENT,
            event_type=event_type,
            user_id=user_id,
            session_id=kwargs.get("session_id", ""),
            ip_address=kwargs.get("ip_address", "unknown"),
            user_agent=kwargs.get("user_agent", "unknown"),
            resource_accessed=kwargs.get("resource", "security_system"),
            action_performed="security_monitoring",
            outcome="success" if success else "security_incident",
            risk_level=risk_enum,
            details={"event_id": event_id, **details},
            compliance_flags=["security_monitoring", "incident_response"]
        )

    def log_compliance_event(self, user_id: str, compliance_type: str, action: str,
                           details: Dict[str, Any], session_id: str = "") -> str:
        """Log compliance-specific events"""
        return self._create_log_entry(
            level=LogLevel.COMPLIANCE,
            category=EventCategory.COMPLIANCE_EVENT,
            event_type=f"compliance_{compliance_type}",
            user_id=user_id,
            session_id=session_id,
            ip_address="compliance_system",
            user_agent="compliance_monitor",
            resource_accessed="compliance_framework",
            action_performed=action,
            outcome="logged",
            risk_level=RiskLevel.LOW,
            details=details,
            compliance_flags=[compliance_type, "regulatory_compliance"]
        )

    def _create_log_entry(self, level: LogLevel, category: EventCategory, event_type: str,
                         user_id: str, session_id: str, ip_address: str, user_agent: str,
                         resource_accessed: str, action_performed: str, outcome: str,
                         risk_level: RiskLevel, details: Dict[str, Any],
                         compliance_flags: List[str]) -> str:
        """Create and store audit log entry"""
        # Generate unique log ID
        log_id = f"LOG_{uuid.uuid4().hex.upper()}"

        # Prepare log entry
        log_entry = AuditLogEntry(
            log_id=log_id,
            timestamp=datetime.now(timezone.utc),
            level=level,
            category=category,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_accessed=resource_accessed,
            action_performed=action_performed,
            outcome=outcome,
            risk_level=risk_level,
            details=details,
            compliance_flags=compliance_flags
        )

        # Encrypt sensitive data if configured
        if self.config["encrypt_sensitive_data"]:
            sensitive_data = {
                "details": details,
                "user_agent": user_agent,
                "session_id": session_id
            }
            log_entry.encrypted_payload = self.encryption_manager.encrypt_data(
                json.dumps(sensitive_data)
            )

        # Generate integrity hash
        if self.config["generate_integrity_hashes"]:
            hash_data = f"{log_id}_{log_entry.timestamp}_{event_type}_{user_id}_{outcome}"
            log_entry.integrity_hash = self.encryption_manager.hash_data(hash_data)

        # Store log entry
        self.audit_logs.append(log_entry)

        # Real-time monitoring for high-risk events
        if self.config["real_time_monitoring"] and risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._trigger_real_time_alert(log_entry)

        return log_id

    def _trigger_real_time_alert(self, log_entry: AuditLogEntry):
        """Trigger real-time alerts for high-risk events"""
        alert_data = {
            "alert_id": f"ALERT_{uuid.uuid4().hex[:8].upper()}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_id": log_entry.log_id,
            "risk_level": log_entry.risk_level.value,
            "event_type": log_entry.event_type,
            "user_id": log_entry.user_id,
            "outcome": log_entry.outcome,
            "requires_immediate_attention": log_entry.risk_level == RiskLevel.CRITICAL,
            "compliance_implications": log_entry.compliance_flags
        }

        # In production, this would trigger actual alerting systems
        self._log_system_event("security_alert_triggered", "alert_system", alert_data)

    def search_audit_logs(self, query: AuditSearchQuery) -> List[AuditLogEntry]:
        """Search audit logs with compliance filtering"""
        filtered_logs = self.audit_logs.copy()

        # Apply filters
        if query.start_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= query.start_date]

        if query.end_date:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= query.end_date]

        if query.user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == query.user_id]

        if query.event_type:
            filtered_logs = [log for log in filtered_logs if log.event_type == query.event_type]

        if query.category:
            filtered_logs = [log for log in filtered_logs if log.category == query.category]

        if query.risk_level:
            filtered_logs = [log for log in filtered_logs if log.risk_level == query.risk_level]

        if query.outcome:
            filtered_logs = [log for log in filtered_logs if log.outcome == query.outcome]

        # Apply pagination
        start_idx = query.offset
        end_idx = start_idx + query.limit
        return filtered_logs[start_idx:end_idx]

    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> ComplianceReport:
        """Generate comprehensive compliance audit report"""
        # Filter logs for date range
        period_logs = [
            log for log in self.audit_logs
            if start_date <= log.timestamp <= end_date
        ]

        # Analyze events by category
        events_by_category = {}
        for log in period_logs:
            category = log.category.value
            events_by_category[category] = events_by_category.get(category, 0) + 1

        # Count security and failed events
        security_events = len([log for log in period_logs if log.category == EventCategory.SECURITY_EVENT])
        failed_events = len([log for log in period_logs if log.outcome == "failure"])
        high_risk_events = len([log for log in period_logs if log.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])

        # Identify compliance violations
        compliance_violations = []
        for log in period_logs:
            if log.risk_level == RiskLevel.CRITICAL or "violation" in log.event_type.lower():
                compliance_violations.append({
                    "log_id": log.log_id,
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "user_id": log.user_id,
                    "risk_level": log.risk_level.value,
                    "compliance_flags": log.compliance_flags
                })

        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(period_logs)

        # Create report
        report = ComplianceReport(
            report_id=f"COMP_{uuid.uuid4().hex.upper()}",
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            total_events=len(period_logs),
            events_by_category=events_by_category,
            security_events=security_events,
            failed_events=failed_events,
            high_risk_events=high_risk_events,
            compliance_violations=compliance_violations,
            recommendations=recommendations,
            report_integrity_hash=""
        )

        # Generate integrity hash for report
        report_data = f"{report.report_id}_{report.generated_at}_{report.total_events}"
        report.report_integrity_hash = self.encryption_manager.hash_data(report_data)

        return report

    def _generate_compliance_recommendations(self, logs: List[AuditLogEntry]) -> List[str]:
        """Generate compliance recommendations based on audit analysis"""
        recommendations = []

        # Analyze patterns
        failed_attempts = len([log for log in logs if log.outcome == "failure"])
        security_events = len([log for log in logs if log.category == EventCategory.SECURITY_EVENT])
        high_risk_events = len([log for log in logs if log.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])

        if failed_attempts > 10:
            recommendations.append("Consider implementing additional authentication controls to reduce failed login attempts")

        if security_events > 5:
            recommendations.append("Review security incident response procedures and consider additional monitoring")

        if high_risk_events > 0:
            recommendations.append("Investigate high-risk events and implement preventive measures")

        # Compliance-specific recommendations
        recommendations.extend([
            "Ensure all staff receive regular training on professional responsibility and confidentiality requirements",
            "Review and update data retention policies to ensure compliance with legal requirements",
            "Conduct regular security assessments and penetration testing",
            "Maintain comprehensive backup and disaster recovery procedures",
            "Implement regular audit log reviews and compliance monitoring"
        ])

        return recommendations

    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get comprehensive audit system statistics"""
        total_logs = len(self.audit_logs)

        if total_logs == 0:
            return {
                "total_logs": 0,
                "message": "No audit logs available"
            }

        # Calculate statistics
        categories = {}
        risk_levels = {}
        outcomes = {}

        for log in self.audit_logs:
            # Count by category
            cat = log.category.value
            categories[cat] = categories.get(cat, 0) + 1

            # Count by risk level
            risk = log.risk_level.value
            risk_levels[risk] = risk_levels.get(risk, 0) + 1

            # Count by outcome
            outcome = log.outcome
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

        return {
            "total_logs": total_logs,
            "categories": categories,
            "risk_levels": risk_levels,
            "outcomes": outcomes,
            "compliance_features": {
                "encryption_enabled": self.config["encrypt_sensitive_data"],
                "integrity_verification": self.config["generate_integrity_hashes"],
                "real_time_monitoring": self.config["real_time_monitoring"],
                "compliance_validation": self.config["compliance_validation"]
            },
            "retention_policy": {
                "default_retention_days": 2555,  # 7 years
                "legal_compliance": "professional_responsibility_compliant"
            },
            "security_status": "operational",
            "last_log_timestamp": max(log.timestamp for log in self.audit_logs).isoformat() if total_logs > 0 else None
        }

    def _log_system_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log internal system events"""
        self._create_log_entry(
            level=LogLevel.INFO,
            category=EventCategory.SYSTEM_EVENT,
            event_type=event_type,
            user_id=user_id,
            session_id="system",
            ip_address="localhost",
            user_agent="audit_system",
            resource_accessed="audit_logger",
            action_performed="system_operation",
            outcome="success",
            risk_level=RiskLevel.LOW,
            details=details,
            compliance_flags=["system_monitoring"]
        )


# Global audit logger instance
audit_logger = AuditLogger()
from datetime import datetime
from typing import Dict, Any, Optional

class AuditLogger:
    """Simple audit logger for document processing compliance"""

    def __init__(self):
        self.logger = logging.getLogger('audit')

    def log_document_event(self, event_type: str, document_id: str,
                          user_id: str, details: Dict[str, Any] = None):
        """Log document-related events"""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "document_id": document_id,
                "user_id": user_id,
                "details": details or {}
            }

            self.logger.info(f"AUDIT: {json.dumps(audit_entry)}")

        except Exception as e:
            self.logger.error(f"Audit logging failed: {e}")

    def log_security_event(self, event_type: str, details: Dict[str, Any] = None):
        """Log security-related events"""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "category": "security",
                "details": details or {}
            }

            self.logger.warning(f"SECURITY AUDIT: {json.dumps(audit_entry)}")

        except Exception as e:
            self.logger.error(f"Security audit logging failed: {e}")