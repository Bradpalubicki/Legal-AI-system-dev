"""
Firm Administration Portal
Comprehensive administration system for law firms with user management, analytics, and billing.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta, date
from enum import Enum
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator, EmailStr
import json
import uuid
import hashlib
from collections import defaultdict
import statistics
import asyncio


class UserRole(Enum):
    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    STAFF = "staff"
    GUEST = "guest"


class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    ARCHIVED = "archived"


class BillingStatus(Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    OVERDUE = "overdue"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_RESPONSE = "waiting_response"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class SecurityEvent(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    DATA_EXPORT = "data_export"
    API_ACCESS = "api_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class FirmUser:
    user_id: str
    firm_id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    permissions: List[str] = field(default_factory=list)
    department: Optional[str] = None
    hire_date: Optional[date] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_login_attempts: int = 0
    two_factor_enabled: bool = False
    profile_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FirmBilling:
    firm_id: str
    plan_type: str
    billing_status: BillingStatus
    monthly_cost: float
    users_included: int
    additional_users: int = 0
    storage_gb: int = 100
    additional_storage_gb: int = 0
    api_calls_included: int = 10000
    api_calls_used: int = 0
    billing_email: str = ""
    billing_address: Dict[str, str] = field(default_factory=dict)
    payment_method: Dict[str, str] = field(default_factory=dict)
    next_billing_date: date = field(default_factory=lambda: date.today() + timedelta(days=30))
    trial_ends: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class UsageMetrics:
    firm_id: str
    date: date
    active_users: int = 0
    documents_processed: int = 0
    api_calls: int = 0
    storage_used_gb: float = 0.0
    workflows_executed: int = 0
    emails_sent: int = 0
    reports_generated: int = 0
    login_events: int = 0
    feature_usage: Dict[str, int] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class SecurityAuditLog:
    log_id: str
    firm_id: str
    user_id: Optional[str]
    event_type: SecurityEvent
    event_description: str
    ip_address: str
    user_agent: str
    success: bool = True
    risk_level: str = "low"  # low, medium, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SupportTicket:
    ticket_id: str
    firm_id: str
    submitted_by: str
    subject: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = "general"
    assigned_to: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    resolution_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


@dataclass
class ComplianceReport:
    report_id: str
    firm_id: str
    report_type: str  # gdpr, hipaa, sox, custom
    generated_by: str
    date_range: Dict[str, date]
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_score: float = 0.0
    status: str = "generated"
    file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class FirmAdminPortal:
    """Comprehensive firm administration portal"""

    def __init__(self):
        self.firms: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, FirmUser] = {}
        self.billing: Dict[str, FirmBilling] = {}
        self.usage_metrics: Dict[str, List[UsageMetrics]] = defaultdict(list)
        self.security_logs: Dict[str, List[SecurityAuditLog]] = defaultdict(list)
        self.support_tickets: Dict[str, SupportTicket] = {}
        self.compliance_reports: Dict[str, ComplianceReport] = {}
        self.system_settings: Dict[str, Dict[str, Any]] = {}

    async def create_firm(
        self,
        firm_name: str,
        admin_email: str,
        admin_name: str,
        plan_type: str = "trial"
    ) -> Dict[str, Any]:
        """Create a new firm with admin user"""

        firm_id = str(uuid.uuid4())
        admin_user_id = str(uuid.uuid4())

        # Create firm record
        firm_data = {
            "firm_id": firm_id,
            "name": firm_name,
            "status": "active",
            "created_at": datetime.now(),
            "settings": {
                "timezone": "America/New_York",
                "business_hours": {
                    "start": "09:00",
                    "end": "17:00",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "security": {
                    "require_2fa": False,
                    "password_policy": {
                        "min_length": 8,
                        "require_uppercase": True,
                        "require_numbers": True,
                        "require_symbols": True
                    },
                    "session_timeout": 60  # minutes
                }
            }
        }

        # Create admin user
        admin_user = FirmUser(
            user_id=admin_user_id,
            firm_id=firm_id,
            email=admin_email,
            first_name=admin_name.split()[0],
            last_name=" ".join(admin_name.split()[1:]) if len(admin_name.split()) > 1 else "",
            role=UserRole.ADMIN,
            permissions=[
                "admin.full_access",
                "users.manage",
                "billing.view",
                "analytics.view",
                "security.manage",
                "settings.manage"
            ]
        )

        # Create billing record
        billing = FirmBilling(
            firm_id=firm_id,
            plan_type=plan_type,
            billing_status=BillingStatus.TRIAL if plan_type == "trial" else BillingStatus.ACTIVE,
            monthly_cost=0.0 if plan_type == "trial" else 99.0,
            users_included=5 if plan_type == "trial" else 25,
            billing_email=admin_email,
            trial_ends=date.today() + timedelta(days=30) if plan_type == "trial" else None
        )

        # Store records
        self.firms[firm_id] = firm_data
        self.users[admin_user_id] = admin_user
        self.billing[firm_id] = billing

        # Initialize usage tracking
        self.usage_metrics[firm_id] = []
        self.security_logs[firm_id] = []

        # Log security event
        await self._log_security_event(
            firm_id, admin_user_id, SecurityEvent.LOGIN_SUCCESS,
            f"Firm created and admin user {admin_email} registered", "system", "system"
        )

        return {
            "firm_id": firm_id,
            "admin_user_id": admin_user_id,
            "status": "created"
        }

    async def manage_user(
        self,
        firm_id: str,
        action: str,  # create, update, suspend, delete, activate
        user_data: Dict[str, Any],
        admin_user_id: str
    ) -> FirmUser:
        """Manage firm users"""

        if not await self._check_permission(admin_user_id, "users.manage"):
            raise ValueError("Insufficient permissions")

        if action == "create":
            user_id = str(uuid.uuid4())
            user = FirmUser(
                user_id=user_id,
                firm_id=firm_id,
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=UserRole(user_data["role"]),
                permissions=user_data.get("permissions", []),
                department=user_data.get("department")
            )

            self.users[user_id] = user

            await self._log_security_event(
                firm_id, admin_user_id, SecurityEvent.PERMISSION_CHANGE,
                f"User {user.email} created with role {user.role.value}", "", ""
            )

            return user

        elif action == "update":
            user_id = user_data["user_id"]
            if user_id not in self.users:
                raise ValueError("User not found")

            user = self.users[user_id]
            for key, value in user_data.items():
                if hasattr(user, key) and key != "user_id":
                    setattr(user, key, value)

            user.updated_at = datetime.now()

            await self._log_security_event(
                firm_id, admin_user_id, SecurityEvent.PERMISSION_CHANGE,
                f"User {user.email} updated", "", ""
            )

            return user

        elif action == "suspend":
            user_id = user_data["user_id"]
            if user_id not in self.users:
                raise ValueError("User not found")

            user = self.users[user_id]
            user.status = UserStatus.SUSPENDED
            user.updated_at = datetime.now()

            await self._log_security_event(
                firm_id, admin_user_id, SecurityEvent.PERMISSION_CHANGE,
                f"User {user.email} suspended", "", ""
            )

            return user

        elif action == "activate":
            user_id = user_data["user_id"]
            if user_id not in self.users:
                raise ValueError("User not found")

            user = self.users[user_id]
            user.status = UserStatus.ACTIVE
            user.updated_at = datetime.now()

            return user

        else:
            raise ValueError(f"Invalid action: {action}")

    async def get_usage_analytics(
        self,
        firm_id: str,
        start_date: date,
        end_date: date,
        admin_user_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""

        if not await self._check_permission(admin_user_id, "analytics.view"):
            raise ValueError("Insufficient permissions")

        firm_metrics = self.usage_metrics.get(firm_id, [])
        date_range_metrics = [
            m for m in firm_metrics
            if start_date <= m.date <= end_date
        ]

        if not date_range_metrics:
            # Generate sample data if no metrics exist
            sample_metrics = await self._generate_sample_metrics(firm_id, start_date, end_date)
            date_range_metrics = sample_metrics

        # Calculate aggregated statistics
        total_users = len([u for u in self.users.values() if u.firm_id == firm_id and u.status == UserStatus.ACTIVE])
        total_documents = sum(m.documents_processed for m in date_range_metrics)
        total_api_calls = sum(m.api_calls for m in date_range_metrics)
        total_workflows = sum(m.workflows_executed for m in date_range_metrics)

        # Calculate averages
        avg_daily_users = statistics.mean([m.active_users for m in date_range_metrics]) if date_range_metrics else 0
        avg_daily_documents = statistics.mean([m.documents_processed for m in date_range_metrics]) if date_range_metrics else 0

        # Feature usage analysis
        feature_usage = defaultdict(int)
        for metrics in date_range_metrics:
            for feature, usage in metrics.feature_usage.items():
                feature_usage[feature] += usage

        # Performance metrics
        performance_data = defaultdict(list)
        for metrics in date_range_metrics:
            for metric, value in metrics.performance_metrics.items():
                performance_data[metric].append(value)

        avg_performance = {
            metric: statistics.mean(values) if values else 0
            for metric, values in performance_data.items()
        }

        # Growth analysis
        growth_data = []
        for i, metrics in enumerate(sorted(date_range_metrics, key=lambda x: x.date)):
            if i > 0:
                prev_metrics = sorted(date_range_metrics, key=lambda x: x.date)[i-1]
                growth = {
                    "date": metrics.date.isoformat(),
                    "users_growth": metrics.active_users - prev_metrics.active_users,
                    "documents_growth": metrics.documents_processed - prev_metrics.documents_processed,
                    "api_calls_growth": metrics.api_calls - prev_metrics.api_calls
                }
                growth_data.append(growth)

        return {
            "firm_id": firm_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "overview": {
                "total_users": total_users,
                "total_documents_processed": total_documents,
                "total_api_calls": total_api_calls,
                "total_workflows_executed": total_workflows,
                "avg_daily_active_users": round(avg_daily_users, 1),
                "avg_daily_documents": round(avg_daily_documents, 1)
            },
            "feature_usage": dict(feature_usage),
            "performance_metrics": avg_performance,
            "growth_analysis": growth_data,
            "daily_metrics": [
                {
                    "date": m.date.isoformat(),
                    "active_users": m.active_users,
                    "documents_processed": m.documents_processed,
                    "api_calls": m.api_calls,
                    "workflows_executed": m.workflows_executed,
                    "storage_used_gb": m.storage_used_gb
                }
                for m in sorted(date_range_metrics, key=lambda x: x.date)
            ]
        }

    async def get_billing_overview(self, firm_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Get billing overview and usage"""

        if not await self._check_permission(admin_user_id, "billing.view"):
            raise ValueError("Insufficient permissions")

        billing = self.billing.get(firm_id)
        if not billing:
            raise ValueError("Billing information not found")

        # Calculate usage overages
        firm_users = [u for u in self.users.values() if u.firm_id == firm_id and u.status == UserStatus.ACTIVE]
        user_overage = max(0, len(firm_users) - billing.users_included)
        storage_overage = max(0, billing.additional_storage_gb)
        api_overage = max(0, billing.api_calls_used - billing.api_calls_included)

        # Calculate additional costs
        user_cost = user_overage * 10.0  # $10 per additional user
        storage_cost = storage_overage * 0.50  # $0.50 per GB
        api_cost = max(0, (api_overage / 1000) * 0.01)  # $0.01 per 1K additional API calls

        total_additional_cost = user_cost + storage_cost + api_cost
        total_monthly_cost = billing.monthly_cost + total_additional_cost

        # Payment history (simulated)
        payment_history = [
            {
                "date": (datetime.now() - timedelta(days=30*i)).date().isoformat(),
                "amount": billing.monthly_cost,
                "status": "paid",
                "invoice_id": f"INV-{firm_id[-8:]}-{i:03d}"
            }
            for i in range(1, 6)  # Last 5 payments
        ]

        return {
            "firm_id": firm_id,
            "plan_type": billing.plan_type,
            "billing_status": billing.billing_status.value,
            "current_period": {
                "base_cost": billing.monthly_cost,
                "additional_costs": {
                    "users": user_cost,
                    "storage": storage_cost,
                    "api_calls": api_cost
                },
                "total_cost": total_monthly_cost,
                "next_billing_date": billing.next_billing_date.isoformat()
            },
            "usage": {
                "users": {
                    "included": billing.users_included,
                    "current": len(firm_users),
                    "overage": user_overage
                },
                "storage": {
                    "included_gb": billing.storage_gb,
                    "additional_gb": billing.additional_storage_gb,
                    "total_gb": billing.storage_gb + billing.additional_storage_gb
                },
                "api_calls": {
                    "included": billing.api_calls_included,
                    "used": billing.api_calls_used,
                    "remaining": max(0, billing.api_calls_included - billing.api_calls_used)
                }
            },
            "payment_history": payment_history,
            "trial_info": {
                "is_trial": billing.billing_status == BillingStatus.TRIAL,
                "trial_ends": billing.trial_ends.isoformat() if billing.trial_ends else None,
                "days_remaining": (billing.trial_ends - date.today()).days if billing.trial_ends else None
            }
        }

    async def get_security_overview(self, firm_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Get security overview and audit logs"""

        if not await self._check_permission(admin_user_id, "security.manage"):
            raise ValueError("Insufficient permissions")

        logs = self.security_logs.get(firm_id, [])
        recent_logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:100]

        # Analyze security events
        event_counts = defaultdict(int)
        risk_counts = defaultdict(int)
        failed_logins = 0

        for log in recent_logs:
            event_counts[log.event_type.value] += 1
            risk_counts[log.risk_level] += 1
            if log.event_type == SecurityEvent.LOGIN_FAILURE:
                failed_logins += 1

        # User security status
        firm_users = [u for u in self.users.values() if u.firm_id == firm_id]
        users_with_2fa = len([u for u in firm_users if u.two_factor_enabled])
        users_with_failed_logins = len([u for u in firm_users if u.failed_login_attempts > 0])

        # Security recommendations
        recommendations = []
        if users_with_2fa / len(firm_users) < 0.5 if firm_users else 0:
            recommendations.append("Enable two-factor authentication for more users")
        if failed_logins > 10:
            recommendations.append("Review failed login attempts - potential security threat")
        if any(log.risk_level in ["high", "critical"] for log in recent_logs[-20:]):
            recommendations.append("High-risk security events detected - review immediately")

        return {
            "firm_id": firm_id,
            "security_score": self._calculate_security_score(firm_id),
            "overview": {
                "total_users": len(firm_users),
                "users_with_2fa": users_with_2fa,
                "users_with_failed_logins": users_with_failed_logins,
                "recent_events": len(recent_logs),
                "high_risk_events": len([l for l in recent_logs if l.risk_level in ["high", "critical"]])
            },
            "event_summary": dict(event_counts),
            "risk_distribution": dict(risk_counts),
            "recent_events": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type.value,
                    "description": log.event_description,
                    "user_id": log.user_id,
                    "ip_address": log.ip_address,
                    "risk_level": log.risk_level,
                    "success": log.success
                }
                for log in recent_logs[:20]
            ],
            "recommendations": recommendations
        }

    async def create_support_ticket(
        self,
        firm_id: str,
        submitted_by: str,
        subject: str,
        description: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        category: str = "general"
    ) -> SupportTicket:
        """Create a support ticket"""

        ticket_id = str(uuid.uuid4())
        ticket = SupportTicket(
            ticket_id=ticket_id,
            firm_id=firm_id,
            submitted_by=submitted_by,
            subject=subject,
            description=description,
            priority=priority,
            category=category
        )

        self.support_tickets[ticket_id] = ticket

        # Auto-assign based on category
        if category == "billing":
            ticket.assigned_to = "billing_team"
        elif category == "technical":
            ticket.assigned_to = "tech_team"
        else:
            ticket.assigned_to = "support_team"

        return ticket

    async def generate_compliance_report(
        self,
        firm_id: str,
        report_type: str,
        date_range: Dict[str, date],
        admin_user_id: str
    ) -> ComplianceReport:
        """Generate compliance report"""

        if not await self._check_permission(admin_user_id, "analytics.view"):
            raise ValueError("Insufficient permissions")

        report_id = str(uuid.uuid4())

        # Generate findings based on report type
        findings = []
        recommendations = []
        compliance_score = 85.0  # Base score

        if report_type == "gdpr":
            findings = await self._generate_gdpr_findings(firm_id, date_range)
            recommendations = [
                "Implement regular data retention policy reviews",
                "Enhance user consent tracking mechanisms",
                "Strengthen data subject request processing"
            ]
        elif report_type == "hipaa":
            findings = await self._generate_hipaa_findings(firm_id, date_range)
            recommendations = [
                "Review access controls for medical records",
                "Implement additional audit logging",
                "Enhance encryption for data at rest"
            ]
        elif report_type == "sox":
            findings = await self._generate_sox_findings(firm_id, date_range)
            recommendations = [
                "Strengthen financial data access controls",
                "Implement quarterly security reviews",
                "Enhance change management processes"
            ]

        # Adjust compliance score based on findings
        critical_findings = len([f for f in findings if f.get("severity") == "critical"])
        compliance_score -= critical_findings * 10

        report = ComplianceReport(
            report_id=report_id,
            firm_id=firm_id,
            report_type=report_type,
            generated_by=admin_user_id,
            date_range=date_range,
            findings=findings,
            recommendations=recommendations,
            compliance_score=max(0, compliance_score)
        )

        self.compliance_reports[report_id] = report
        return report

    async def _check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has required permission"""
        user = self.users.get(user_id)
        if not user:
            return False

        # Admin users have all permissions
        if user.role == UserRole.ADMIN:
            return True

        return permission in user.permissions

    async def _log_security_event(
        self,
        firm_id: str,
        user_id: Optional[str],
        event_type: SecurityEvent,
        description: str,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        risk_level: str = "low"
    ):
        """Log security event"""

        log_id = str(uuid.uuid4())
        log = SecurityAuditLog(
            log_id=log_id,
            firm_id=firm_id,
            user_id=user_id,
            event_type=event_type,
            event_description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            risk_level=risk_level
        )

        self.security_logs[firm_id].append(log)

    def _calculate_security_score(self, firm_id: str) -> float:
        """Calculate security score for firm"""
        score = 100.0
        firm_users = [u for u in self.users.values() if u.firm_id == firm_id]

        if not firm_users:
            return 0.0

        # Factors that reduce security score
        users_without_2fa = len([u for u in firm_users if not u.two_factor_enabled])
        users_with_failed_logins = len([u for u in firm_users if u.failed_login_attempts > 3])

        # Reduce score based on security issues
        score -= (users_without_2fa / len(firm_users)) * 20  # Up to -20 for no 2FA
        score -= (users_with_failed_logins / len(firm_users)) * 15  # Up to -15 for failed logins

        # Check recent high-risk events
        recent_logs = self.security_logs.get(firm_id, [])
        recent_high_risk = len([
            l for l in recent_logs[-100:]  # Last 100 events
            if l.risk_level in ["high", "critical"] and l.timestamp > datetime.now() - timedelta(days=7)
        ])

        score -= min(recent_high_risk * 5, 25)  # Up to -25 for high-risk events

        return max(0, score)

    async def _generate_sample_metrics(
        self,
        firm_id: str,
        start_date: date,
        end_date: date
    ) -> List[UsageMetrics]:
        """Generate sample usage metrics for demonstration"""

        metrics = []
        current_date = start_date

        while current_date <= end_date:
            # Generate realistic sample data
            base_users = 15
            daily_variation = hash(f"{firm_id}{current_date}") % 10 - 5

            metric = UsageMetrics(
                firm_id=firm_id,
                date=current_date,
                active_users=max(1, base_users + daily_variation),
                documents_processed=max(0, 25 + (hash(f"docs{firm_id}{current_date}") % 30)),
                api_calls=max(0, 150 + (hash(f"api{firm_id}{current_date}") % 200)),
                storage_used_gb=45.5 + (hash(f"storage{firm_id}{current_date}") % 100) / 10,
                workflows_executed=max(0, 8 + (hash(f"workflows{firm_id}{current_date}") % 15)),
                emails_sent=max(0, 12 + (hash(f"emails{firm_id}{current_date}") % 20)),
                reports_generated=max(0, 3 + (hash(f"reports{firm_id}{current_date}") % 8)),
                feature_usage={
                    "document_analysis": max(0, 20 + (hash(f"da{firm_id}{current_date}") % 15)),
                    "legal_research": max(0, 15 + (hash(f"lr{firm_id}{current_date}") % 12)),
                    "case_management": max(0, 18 + (hash(f"cm{firm_id}{current_date}") % 10)),
                    "client_portal": max(0, 12 + (hash(f"cp{firm_id}{current_date}") % 8)),
                },
                performance_metrics={
                    "avg_response_time": 0.25 + (hash(f"rt{firm_id}{current_date}") % 100) / 1000,
                    "uptime_percentage": 99.5 + (hash(f"up{firm_id}{current_date}") % 50) / 100,
                    "error_rate": max(0, 0.1 + (hash(f"er{firm_id}{current_date}") % 20) / 1000)
                }
            )

            metrics.append(metric)
            current_date += timedelta(days=1)

        return metrics

    async def _generate_gdpr_findings(
        self,
        firm_id: str,
        date_range: Dict[str, date]
    ) -> List[Dict[str, Any]]:
        """Generate GDPR compliance findings"""
        return [
            {
                "category": "Data Retention",
                "severity": "medium",
                "description": "Some user data exceeds maximum retention period",
                "affected_records": 23,
                "recommendation": "Implement automated data purging"
            },
            {
                "category": "Consent Management",
                "severity": "low",
                "description": "Cookie consent tracking could be improved",
                "affected_records": 156,
                "recommendation": "Update consent management system"
            }
        ]

    async def _generate_hipaa_findings(
        self,
        firm_id: str,
        date_range: Dict[str, date]
    ) -> List[Dict[str, Any]]:
        """Generate HIPAA compliance findings"""
        return [
            {
                "category": "Access Controls",
                "severity": "low",
                "description": "Some users have broader access than required",
                "affected_records": 8,
                "recommendation": "Review and restrict user access permissions"
            }
        ]

    async def _generate_sox_findings(
        self,
        firm_id: str,
        date_range: Dict[str, date]
    ) -> List[Dict[str, Any]]:
        """Generate SOX compliance findings"""
        return [
            {
                "category": "Change Management",
                "severity": "medium",
                "description": "Some system changes lack proper approval documentation",
                "affected_records": 5,
                "recommendation": "Strengthen change approval workflow"
            }
        ]


# Pydantic models for API
class UserCreateModel(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    department: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class UserUpdateModel(BaseModel):
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    permissions: Optional[List[str]] = None
    status: Optional[UserStatus] = None


class SupportTicketModel(BaseModel):
    subject: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = "general"


class ComplianceReportModel(BaseModel):
    report_type: str
    start_date: date
    end_date: date


# Global instance
firm_admin_portal = FirmAdminPortal()


def get_admin_endpoints() -> APIRouter:
    """Get firm administration FastAPI endpoints"""
    router = APIRouter(prefix="/admin", tags=["administration"])

    @router.post("/firm/create")
    async def create_firm(
        firm_name: str,
        admin_email: EmailStr,
        admin_name: str,
        plan_type: str = "trial"
    ):
        """Create new firm"""
        try:
            result = await firm_admin_portal.create_firm(
                firm_name, admin_email, admin_name, plan_type
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/users/{firm_id}")
    async def create_user(
        firm_id: str,
        user_data: UserCreateModel,
        admin_user_id: str = "system"
    ):
        """Create new user"""
        try:
            user = await firm_admin_portal.manage_user(
                firm_id, "create", user_data.dict(), admin_user_id
            )
            return {"user_id": user.user_id, "status": "created"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/users/{firm_id}")
    async def update_user(
        firm_id: str,
        user_data: UserUpdateModel,
        admin_user_id: str = "system"
    ):
        """Update user"""
        try:
            user = await firm_admin_portal.manage_user(
                firm_id, "update", user_data.dict(), admin_user_id
            )
            return {"user_id": user.user_id, "status": "updated"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/analytics/{firm_id}")
    async def get_usage_analytics(
        firm_id: str,
        start_date: date = Query(...),
        end_date: date = Query(...),
        admin_user_id: str = "system"
    ):
        """Get usage analytics"""
        try:
            return await firm_admin_portal.get_usage_analytics(
                firm_id, start_date, end_date, admin_user_id
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/billing/{firm_id}")
    async def get_billing_overview(firm_id: str, admin_user_id: str = "system"):
        """Get billing overview"""
        try:
            return await firm_admin_portal.get_billing_overview(firm_id, admin_user_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/security/{firm_id}")
    async def get_security_overview(firm_id: str, admin_user_id: str = "system"):
        """Get security overview"""
        try:
            return await firm_admin_portal.get_security_overview(firm_id, admin_user_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/support/{firm_id}")
    async def create_support_ticket(
        firm_id: str,
        ticket_data: SupportTicketModel,
        submitted_by: str = "system"
    ):
        """Create support ticket"""
        try:
            ticket = await firm_admin_portal.create_support_ticket(
                firm_id, submitted_by, ticket_data.subject, ticket_data.description,
                ticket_data.priority, ticket_data.category
            )
            return {"ticket_id": ticket.ticket_id, "status": "created"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/support/{firm_id}")
    async def get_support_tickets(firm_id: str):
        """Get support tickets for firm"""
        tickets = [
            {
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "created_at": ticket.created_at,
                "assigned_to": ticket.assigned_to
            }
            for ticket in firm_admin_portal.support_tickets.values()
            if ticket.firm_id == firm_id
        ]
        return {"tickets": tickets}

    @router.post("/compliance/{firm_id}")
    async def generate_compliance_report(
        firm_id: str,
        report_data: ComplianceReportModel,
        admin_user_id: str = "system"
    ):
        """Generate compliance report"""
        try:
            report = await firm_admin_portal.generate_compliance_report(
                firm_id, report_data.report_type,
                {"start": report_data.start_date, "end": report_data.end_date},
                admin_user_id
            )
            return {
                "report_id": report.report_id,
                "compliance_score": report.compliance_score,
                "findings": len(report.findings),
                "status": "generated"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/users/{firm_id}")
    async def get_firm_users(firm_id: str):
        """Get all users for firm"""
        users = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "status": user.status.value,
                "department": user.department,
                "last_login": user.last_login,
                "two_factor_enabled": user.two_factor_enabled
            }
            for user in firm_admin_portal.users.values()
            if user.firm_id == firm_id
        ]
        return {"users": users}

    @router.get("/dashboard/{firm_id}")
    async def get_admin_dashboard(firm_id: str, admin_user_id: str = "system"):
        """Get admin dashboard overview"""
        try:
            # Get basic firm info
            firm_data = firm_admin_portal.firms.get(firm_id, {})
            billing = firm_admin_portal.billing.get(firm_id)

            # Count active users
            active_users = len([
                u for u in firm_admin_portal.users.values()
                if u.firm_id == firm_id and u.status == UserStatus.ACTIVE
            ])

            # Count open tickets
            open_tickets = len([
                t for t in firm_admin_portal.support_tickets.values()
                if t.firm_id == firm_id and t.status == TicketStatus.OPEN
            ])

            # Get recent security events
            recent_security_events = len([
                l for l in firm_admin_portal.security_logs.get(firm_id, [])
                if l.timestamp > datetime.now() - timedelta(days=7)
            ])

            return {
                "firm_name": firm_data.get("name"),
                "status": firm_data.get("status"),
                "plan_type": billing.plan_type if billing else "unknown",
                "billing_status": billing.billing_status.value if billing else "unknown",
                "active_users": active_users,
                "open_support_tickets": open_tickets,
                "recent_security_events": recent_security_events,
                "security_score": firm_admin_portal._calculate_security_score(firm_id)
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router


async def initialize_admin_system():
    """Initialize the firm administration system"""
    print("Initializing firm administration portal...")

    # Create sample firm for demonstration
    sample_firm = await firm_admin_portal.create_firm(
        "Demo Law Firm", "admin@demolaw.com", "John Admin", "trial"
    )

    print("✓ Firm administration portal initialized")
    print("✓ User management system ready")
    print("✓ Billing and analytics systems active")
    print("✓ Security monitoring configured")
    print("✓ Support ticket system ready")
    print(f"✓ Sample firm created: {sample_firm['firm_id']}")
    print("🏢 Firm administration portal ready!")