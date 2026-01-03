#!/usr/bin/env python3
"""
SOC 2 Type II Compliant Role-Based Access Control with Multi-Factor Authentication
Implements legal industry specific roles and compliance controls
"""

import os
import secrets
import hashlib
import pyotp
import qrcode
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from enum import Enum
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

class LegalRole(Enum):
    """Legal industry specific roles with hierarchical permissions"""
    PARALEGAL = "paralegal"
    ASSOCIATE_ATTORNEY = "associate_attorney"
    SENIOR_ATTORNEY = "senior_attorney"
    PARTNER = "partner"
    MANAGING_PARTNER = "managing_partner"
    COMPLIANCE_OFFICER = "compliance_officer"
    IT_ADMIN = "it_admin"
    CLIENT_READ_ONLY = "client_read_only"

class Permission(Enum):
    """Granular permissions for legal operations"""
    READ_PUBLIC_DOCS = "read_public_docs"
    READ_CONFIDENTIAL_DOCS = "read_confidential_docs"
    READ_ATTORNEY_CLIENT_PRIVILEGED = "read_attorney_client_privileged"
    CREATE_DOCUMENTS = "create_documents"
    EDIT_DOCUMENTS = "edit_documents"
    DELETE_DOCUMENTS = "delete_documents"
    MANAGE_CLIENTS = "manage_clients"
    VIEW_BILLING = "view_billing"
    MANAGE_BILLING = "manage_billing"
    RUN_CONFLICTS_CHECK = "run_conflicts_check"
    ACCESS_AUDIT_LOGS = "access_audit_logs"
    MANAGE_USERS = "manage_users"
    SYSTEM_ADMIN = "system_admin"
    BACKUP_RESTORE = "backup_restore"

@dataclass
class SecurityContext:
    """Security context for audit and compliance tracking"""
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    login_time: datetime
    last_activity: datetime
    mfa_verified: bool = False
    risk_score: int = 0
    session_timeout: timedelta = field(default_factory=lambda: timedelta(hours=4))

class RolePermissionMatrix:
    """Defines role-based permissions matrix for legal industry compliance"""
    
    ROLE_PERMISSIONS = {
        LegalRole.PARALEGAL: [
            Permission.READ_PUBLIC_DOCS,
            Permission.READ_CONFIDENTIAL_DOCS,
            Permission.CREATE_DOCUMENTS,
            Permission.EDIT_DOCUMENTS,
            Permission.VIEW_BILLING
        ],
        LegalRole.ASSOCIATE_ATTORNEY: [
            Permission.READ_PUBLIC_DOCS,
            Permission.READ_CONFIDENTIAL_DOCS,
            Permission.READ_ATTORNEY_CLIENT_PRIVILEGED,
            Permission.CREATE_DOCUMENTS,
            Permission.EDIT_DOCUMENTS,
            Permission.MANAGE_CLIENTS,
            Permission.VIEW_BILLING,
            Permission.RUN_CONFLICTS_CHECK
        ],
        LegalRole.SENIOR_ATTORNEY: [
            Permission.READ_PUBLIC_DOCS,
            Permission.READ_CONFIDENTIAL_DOCS,
            Permission.READ_ATTORNEY_CLIENT_PRIVILEGED,
            Permission.CREATE_DOCUMENTS,
            Permission.EDIT_DOCUMENTS,
            Permission.DELETE_DOCUMENTS,
            Permission.MANAGE_CLIENTS,
            Permission.VIEW_BILLING,
            Permission.MANAGE_BILLING,
            Permission.RUN_CONFLICTS_CHECK,
            Permission.ACCESS_AUDIT_LOGS
        ],
        LegalRole.PARTNER: [
            Permission.READ_PUBLIC_DOCS,
            Permission.READ_CONFIDENTIAL_DOCS,
            Permission.READ_ATTORNEY_CLIENT_PRIVILEGED,
            Permission.CREATE_DOCUMENTS,
            Permission.EDIT_DOCUMENTS,
            Permission.DELETE_DOCUMENTS,
            Permission.MANAGE_CLIENTS,
            Permission.VIEW_BILLING,
            Permission.MANAGE_BILLING,
            Permission.RUN_CONFLICTS_CHECK,
            Permission.ACCESS_AUDIT_LOGS,
            Permission.MANAGE_USERS
        ],
        LegalRole.MANAGING_PARTNER: [perm for perm in Permission],  # All permissions
        LegalRole.COMPLIANCE_OFFICER: [
            Permission.READ_PUBLIC_DOCS,
            Permission.READ_CONFIDENTIAL_DOCS,
            Permission.ACCESS_AUDIT_LOGS,
            Permission.VIEW_BILLING,
            Permission.RUN_CONFLICTS_CHECK,
            Permission.MANAGE_USERS
        ],
        LegalRole.IT_ADMIN: [
            Permission.ACCESS_AUDIT_LOGS,
            Permission.MANAGE_USERS,
            Permission.SYSTEM_ADMIN,
            Permission.BACKUP_RESTORE
        ],
        LegalRole.CLIENT_READ_ONLY: [
            Permission.READ_PUBLIC_DOCS
        ]
    }
    
    @classmethod
    def has_permission(cls, role: LegalRole, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def get_role_permissions(cls, role: LegalRole) -> List[Permission]:
        """Get all permissions for a role"""
        return cls.ROLE_PERMISSIONS.get(role, [])

class LegalUser(UserMixin):
    """SOC 2 compliant user model with legal industry requirements"""
    
    def __init__(self, user_id: str, email: str, role: LegalRole, 
                 bar_number: str = None, firm_id: str = None):
        self.id = user_id
        self.email = email
        self.role = role
        self.bar_number = bar_number  # Attorney bar admission number
        self.firm_id = firm_id
        self.password_hash = None
        self.mfa_secret = None
        self.backup_codes = []
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.last_password_change = datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.last_login = None
        self.security_context = None
        
        # Legal-specific fields
        self.practicing_attorney = role in [LegalRole.ASSOCIATE_ATTORNEY, 
                                          LegalRole.SENIOR_ATTORNEY, 
                                          LegalRole.PARTNER, 
                                          LegalRole.MANAGING_PARTNER]
        self.authorized_clients = []  # List of client IDs this user can access
        self.conflicts_cleared = []   # List of conflict checks passed
        
    def set_password(self, password: str) -> None:
        """Set password with SOC 2 complexity requirements"""
        if not self._validate_password_complexity(password):
            raise ValueError("Password does not meet complexity requirements")
        
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:100000')
        self.last_password_change = datetime.utcnow()
        
    def check_password(self, password: str) -> bool:
        """Verify password with timing attack protection"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def _validate_password_complexity(self, password: str) -> bool:
        """Enforce SOC 2 password complexity requirements"""
        if len(password) < 12:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return all([has_upper, has_lower, has_digit, has_special])
    
    def setup_mfa(self) -> Tuple[str, str]:
        """Setup TOTP-based MFA with QR code"""
        self.mfa_secret = pyotp.random_base32()
        
        # Generate QR code for easy mobile app setup
        totp = pyotp.TOTP(self.mfa_secret)
        provisioning_uri = totp.provisioning_uri(
            name=self.email,
            issuer_name="Legal AI System"
        )
        
        # Generate backup codes
        self.backup_codes = [secrets.token_hex(8) for _ in range(10)]
        
        return self.mfa_secret, provisioning_uri
    
    def verify_mfa_token(self, token: str) -> bool:
        """Verify TOTP token or backup code"""
        if not self.mfa_secret:
            return False
        
        # Check backup codes first
        if token in self.backup_codes:
            self.backup_codes.remove(token)  # One-time use
            logger.info(f"User {self.id} used backup code for MFA")
            return True
        
        # Verify TOTP token
        totp = pyotp.TOTP(self.mfa_secret)
        if totp.verify(token, valid_window=1):  # Allow 30s window
            return True
        
        return False
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return RolePermissionMatrix.has_permission(self.role, permission)
    
    def can_access_client(self, client_id: str) -> bool:
        """Check if user can access specific client data"""
        # Managing partners and compliance officers can access all clients
        if self.role in [LegalRole.MANAGING_PARTNER, LegalRole.COMPLIANCE_OFFICER]:
            return True
        
        return client_id in self.authorized_clients
    
    def is_account_locked(self) -> bool:
        """Check if account is locked due to failed login attempts"""
        if not self.account_locked_until:
            return False
        return datetime.utcnow() < self.account_locked_until
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock account for specified duration"""
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        logger.warning(f"Account {self.id} locked until {self.account_locked_until}")

class SOC2AuthenticationManager:
    """SOC 2 Type II compliant authentication manager"""
    
    def __init__(self):
        self.users: Dict[str, LegalUser] = {}
        self.active_sessions: Dict[str, SecurityContext] = {}
        self.max_failed_attempts = 5
        self.session_timeout_hours = 4
        self.password_expiry_days = 90
        
    def create_user(self, email: str, role: LegalRole, password: str,
                   bar_number: str = None, firm_id: str = None) -> LegalUser:
        """Create new user with SOC 2 compliance checks"""
        
        # Check if user already exists
        user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
        if user_id in self.users:
            raise ValueError(f"User with email {email} already exists")
        
        # Create user
        user = LegalUser(user_id, email, role, bar_number, firm_id)
        user.set_password(password)
        
        # Setup MFA for attorneys and privileged users
        if user.practicing_attorney or role in [LegalRole.IT_ADMIN, LegalRole.COMPLIANCE_OFFICER]:
            user.setup_mfa()
        
        self.users[user_id] = user
        logger.info(f"Created user {user_id} with role {role.value}")
        
        return user
    
    def authenticate_user(self, email: str, password: str, mfa_token: str = None,
                         ip_address: str = "", user_agent: str = "") -> Tuple[bool, Optional[SecurityContext]]:
        """Authenticate user with MFA support"""
        
        user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
        user = self.users.get(user_id)
        
        if not user:
            logger.warning(f"Authentication attempt for non-existent user: {email}")
            return False, None
        
        # Check if account is locked
        if user.is_account_locked():
            logger.warning(f"Authentication attempt for locked account: {user_id}")
            return False, None
        
        # Verify password
        if not user.check_password(password):
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.lock_account()
                
            logger.warning(f"Failed password attempt for user {user_id} ({user.failed_login_attempts}/{self.max_failed_attempts})")
            return False, None
        
        # Reset failed attempts on successful password
        user.failed_login_attempts = 0
        
        # Check MFA if required
        if user.mfa_secret:
            if not mfa_token or not user.verify_mfa_token(mfa_token):
                logger.warning(f"MFA verification failed for user {user_id}")
                return False, None
        
        # Create security context
        session_id = secrets.token_urlsafe(32)
        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            login_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            mfa_verified=bool(user.mfa_secret)
        )
        
        # Calculate risk score
        context.risk_score = self._calculate_risk_score(user, context)
        
        # Store session
        self.active_sessions[session_id] = context
        user.security_context = context
        user.last_login = datetime.utcnow()
        
        logger.info(f"User {user_id} authenticated successfully (risk score: {context.risk_score})")
        return True, context
    
    def _calculate_risk_score(self, user: LegalUser, context: SecurityContext) -> int:
        """Calculate session risk score for adaptive security"""
        score = 0
        
        # Base score for role privilege level
        role_scores = {
            LegalRole.CLIENT_READ_ONLY: 0,
            LegalRole.PARALEGAL: 10,
            LegalRole.ASSOCIATE_ATTORNEY: 20,
            LegalRole.SENIOR_ATTORNEY: 30,
            LegalRole.PARTNER: 40,
            LegalRole.MANAGING_PARTNER: 50,
            LegalRole.COMPLIANCE_OFFICER: 60,
            LegalRole.IT_ADMIN: 80
        }
        score += role_scores.get(user.role, 50)
        
        # IP address risk (in production, would check against threat intelligence)
        if context.ip_address.startswith("192.168.") or context.ip_address.startswith("10."):
            score -= 10  # Internal network, lower risk
        else:
            score += 20  # External network, higher risk
        
        # Time-based risk
        hour = datetime.utcnow().hour
        if hour < 6 or hour > 22:  # After hours access
            score += 15
        
        # MFA reduces risk
        if context.mfa_verified:
            score -= 20
        
        return max(0, min(100, score))  # Keep between 0-100
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[LegalUser]]:
        """Validate active session with timeout checks"""
        
        context = self.active_sessions.get(session_id)
        if not context:
            return False, None
        
        # Check session timeout
        if datetime.utcnow() - context.last_activity > context.session_timeout:
            self.logout_user(session_id)
            logger.info(f"Session {session_id} expired due to timeout")
            return False, None
        
        # Update last activity
        context.last_activity = datetime.utcnow()
        
        # Get user
        user = self.users.get(context.user_id)
        if not user:
            self.logout_user(session_id)
            return False, None
        
        return True, user
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user and cleanup session"""
        context = self.active_sessions.get(session_id)
        if not context:
            return False
        
        user = self.users.get(context.user_id)
        if user:
            user.security_context = None
        
        del self.active_sessions[session_id]
        logger.info(f"User logged out: {context.user_id}")
        return True
    
    def get_user_by_id(self, user_id: str) -> Optional[LegalUser]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def update_user_permissions(self, user_id: str, new_role: LegalRole, 
                              authorized_clients: List[str] = None) -> bool:
        """Update user role and permissions"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        old_role = user.role
        user.role = new_role
        
        if authorized_clients is not None:
            user.authorized_clients = authorized_clients
        
        logger.info(f"Updated user {user_id} role from {old_role.value} to {new_role.value}")
        return True
    
    def audit_active_sessions(self) -> Dict[str, Any]:
        """Generate session audit report for SOC 2 compliance"""
        
        active_count = len(self.active_sessions)
        high_risk_sessions = sum(1 for ctx in self.active_sessions.values() if ctx.risk_score >= 70)
        
        sessions_by_role = {}
        for context in self.active_sessions.values():
            user = self.users.get(context.user_id)
            if user:
                role = user.role.value
                sessions_by_role[role] = sessions_by_role.get(role, 0) + 1
        
        return {
            "total_active_sessions": active_count,
            "high_risk_sessions": high_risk_sessions,
            "sessions_by_role": sessions_by_role,
            "session_timeout_hours": self.session_timeout_hours,
            "mfa_enabled_users": sum(1 for user in self.users.values() if user.mfa_secret),
            "locked_accounts": sum(1 for user in self.users.values() if user.is_account_locked()),
            "audit_timestamp": datetime.utcnow().isoformat()
        }

# Global authentication manager instance
auth_manager = SOC2AuthenticationManager()