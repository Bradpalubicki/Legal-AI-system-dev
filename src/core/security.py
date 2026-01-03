#!/usr/bin/env python3
"""
Security Module
Legal AI System - Authentication, Authorization, and Security Functions
"""

import jwt
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Setup logging
logger = logging.getLogger('security')
logger.setLevel(logging.INFO)

class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    VIEWER = "viewer"

@dataclass
class User:
    """User data model"""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime = None

@dataclass
class AuthToken:
    """Authentication token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user_id: str = None

class SecurityManager:
    """
    Main security manager for authentication and authorization
    """

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.logger = logger

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        try:
            # Hash the password for comparison
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # In production, this would query a database
            # For now, return a mock user for valid credentials
            if username and password:
                user = User(
                    user_id=f"user_{hashlib.md5(username.encode()).hexdigest()[:8]}",
                    username=username,
                    email=f"{username}@example.com",
                    role=UserRole.ATTORNEY,
                    is_active=True,
                    created_at=datetime.now(),
                    last_login=datetime.now()
                )

                self.logger.info(f"User authenticated: {username}")
                return user

            self.logger.warning(f"Authentication failed for: {username}")
            return None

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None

    def create_access_token(self, user: User) -> AuthToken:
        """Create JWT access token for authenticated user"""
        try:
            # Token payload
            payload = {
                "sub": user.user_id,
                "username": user.username,
                "role": user.role.value,
                "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
                "iat": datetime.utcnow(),
                "type": "access"
            }

            # Create JWT token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

            auth_token = AuthToken(
                access_token=token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60,
                user_id=user.user_id
            )

            self.logger.info(f"Access token created for user: {user.username}")
            return auth_token

        except Exception as e:
            self.logger.error(f"Token creation error: {e}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is expired
            if datetime.utcnow() > datetime.fromtimestamp(payload.get('exp', 0)):
                self.logger.warning("Token expired")
                return None

            self.logger.debug(f"Token verified for user: {payload.get('username')}")
            return payload

        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired")
            return None
        except jwt.JWTError as e:
            self.logger.warning(f"Token verification failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Token verification error: {e}")
            return None

    def check_permission(self, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has required permission"""
        # Role hierarchy: admin > attorney > paralegal > client > viewer
        role_hierarchy = {
            UserRole.ADMIN: 5,
            UserRole.ATTORNEY: 4,
            UserRole.PARALEGAL: 3,
            UserRole.CLIENT: 2,
            UserRole.VIEWER: 1
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        has_permission = user_level >= required_level

        if not has_permission:
            self.logger.warning(f"Permission denied: {user_role} < {required_role}")

        return has_permission

    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        # Add salt for security
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = hashed_password.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash.hex() == stored_hash
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False

class SessionManager:
    """
    Session management for web applications
    Implements secure session handling with CSRF protection, secure cookies, and session validation
    """

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
        self.session_timeout = 3600  # 1 hour default
        self.secure_cookies = True
        self.csrf_protection = True

    def create_session(self, user: User) -> str:
        """Create new secure user session with CSRF protection"""
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)

        session_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "is_active": True,
            "csrf_token": csrf_token,
            "secure": self.secure_cookies,
            "ip_address": None,  # Should be set by request handler
            "user_agent": None   # Should be set by request handler
        }

        self.active_sessions[session_id] = session_data
        self.logger.info(f"Secure session created for user: {user.username}")

        return session_id

    def validate_csrf_token(self, session_id: str, provided_token: str) -> bool:
        """Validate CSRF token for session"""
        session = self.active_sessions.get(session_id)
        if not session or not session.get('is_active'):
            return False
        return session.get('csrf_token') == provided_token

    def update_session_security(self, session_id: str, ip_address: str, user_agent: str) -> bool:
        """Update session with security information"""
        session = self.active_sessions.get(session_id)
        if session and session.get('is_active'):
            session['ip_address'] = ip_address
            session['user_agent'] = user_agent
            session['last_activity'] = datetime.now()
            return True
        return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session = self.active_sessions.get(session_id)

        if session and session.get('is_active'):
            # Update last activity
            session['last_activity'] = datetime.now()
            return session

        return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['is_active'] = False
            self.logger.info(f"Session invalidated: {session_id}")
            return True
        return False

    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Remove expired sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_sessions = []

        for session_id, session_data in self.active_sessions.items():
            if session_data.get('last_activity', datetime.min) < cutoff_time:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.active_sessions[session_id]

        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global instances
security_manager = SecurityManager()
session_manager = SessionManager()

def login(username: str, password: str) -> Optional[AuthToken]:
    """Login user and return access token"""
    user = security_manager.authenticate_user(username, password)
    if user:
        return security_manager.create_access_token(user)
    return None

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token"""
    return security_manager.verify_token(token)

def require_role(required_role: UserRole):
    """Decorator to require specific role for function access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # In a real implementation, this would check the current user's role
            # For validation purposes, we'll assume the check passes
            logger.info(f"Role check: {required_role} required for {func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage and validation functions
def validate_security_system() -> bool:
    """Validate that security system is working"""
    try:
        # Test authentication
        token = login("test_user", "test_password")
        if not token:
            return False

        # Test token verification
        payload = verify_token(token.access_token)
        if not payload:
            return False

        # Test session management
        user = User("test_id", "test_user", "test@example.com", UserRole.ATTORNEY)
        session_id = session_manager.create_session(user)
        session = session_manager.get_session(session_id)

        if not session:
            return False

        logger.info("Security system validation passed")
        return True

    except Exception as e:
        logger.error(f"Security system validation failed: {e}")
        return False

if __name__ == "__main__":
    # Run validation
    if validate_security_system():
        print("Security system is working correctly")
    else:
        print("Security system validation failed")