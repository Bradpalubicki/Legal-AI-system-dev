"""
Authentication Service

Secure authentication and credential management for e-filing system
supporting multiple court systems and security standards.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..models import EFilingCredentials, AuditLog

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Secure authentication service for e-filing system with support
    for multiple court systems, credential encryption, and audit logging.
    """
    
    def __init__(self, secret_key: str, encryption_key: Optional[bytes] = None):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Initialize encryption for sensitive data
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Credential storage (in production, would use secure database)
        self.stored_credentials: Dict[str, EFilingCredentials] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.session_timeout_hours = 8
        self.password_expiry_days = 90
        
        logger.info("Authentication service initialized")
    
    async def register_credentials(
        self,
        attorney_id: UUID,
        court_system: str,
        username: str,
        password: str,
        additional_data: Dict
    ) -> Dict[str, any]:
        """
        Register new e-filing credentials for an attorney and court system
        """
        try:
            # Validate password strength
            password_validation = self._validate_password_strength(password)
            if not password_validation["valid"]:
                return {
                    "success": False,
                    "error": "Password does not meet security requirements",
                    "requirements": password_validation["requirements"]
                }
            
            # Check if credentials already exist
            cred_key = f"{attorney_id}:{court_system}"
            if cred_key in self.stored_credentials:
                return {
                    "success": False,
                    "error": "Credentials already exist for this attorney and court system"
                }
            
            # Hash password
            password_hash = self.pwd_context.hash(password)
            
            # Create credentials object
            credentials = EFilingCredentials(
                attorney_id=attorney_id,
                court_system=court_system,
                username=username,
                password_hash=password_hash,
                bar_number=additional_data.get("bar_number", ""),
                pacer_id=additional_data.get("pacer_id"),
                ecf_id=additional_data.get("ecf_id"),
                two_factor_enabled=additional_data.get("two_factor_enabled", False),
                expires_at=datetime.utcnow() + timedelta(days=self.password_expiry_days)
            )
            
            # Encrypt sensitive fields
            credentials = await self._encrypt_credentials(credentials)
            
            # Store credentials
            self.stored_credentials[cred_key] = credentials
            
            # Log registration
            await self._log_auth_event(
                "credential_registration",
                attorney_id,
                court_system,
                True,
                f"Credentials registered for {court_system}"
            )
            
            return {
                "success": True,
                "message": "Credentials registered successfully",
                "credential_id": cred_key,
                "expires_at": credentials.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Credential registration failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def authenticate_user(
        self,
        attorney_id: UUID,
        court_system: str,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Authenticate user credentials for e-filing access
        """
        try:
            cred_key = f"{attorney_id}:{court_system}"
            
            # Check for account lockout
            if await self._is_account_locked(cred_key):
                await self._log_auth_event(
                    "authentication_blocked",
                    attorney_id,
                    court_system,
                    False,
                    "Account locked due to failed attempts",
                    ip_address
                )
                return {
                    "success": False,
                    "error": "Account is temporarily locked",
                    "lockout_expires": await self._get_lockout_expiry(cred_key)
                }
            
            # Get stored credentials
            stored_creds = self.stored_credentials.get(cred_key)
            if not stored_creds:
                await self._record_failed_attempt(cred_key)
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
            
            # Decrypt credentials
            decrypted_creds = await self._decrypt_credentials(stored_creds)
            
            # Verify username and password
            if (decrypted_creds.username != username or
                not self.pwd_context.verify(password, decrypted_creds.password_hash)):
                await self._record_failed_attempt(cred_key)
                await self._log_auth_event(
                    "authentication_failed",
                    attorney_id,
                    court_system,
                    False,
                    "Invalid username or password",
                    ip_address
                )
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
            
            # Check if credentials are expired
            if decrypted_creds.expires_at and decrypted_creds.expires_at < datetime.utcnow():
                return {
                    "success": False,
                    "error": "Credentials have expired",
                    "needs_renewal": True
                }
            
            # Clear failed attempts on successful auth
            self.failed_attempts.pop(cred_key, None)
            
            # Create session token
            session_token = await self._create_session_token(decrypted_creds, ip_address)
            
            # Update last login
            stored_creds.last_login = datetime.utcnow()
            
            # Log successful authentication
            await self._log_auth_event(
                "authentication_success",
                attorney_id,
                court_system,
                True,
                f"Successful login from {ip_address or 'unknown'}",
                ip_address
            )
            
            return {
                "success": True,
                "session_token": session_token,
                "expires_at": (datetime.utcnow() + timedelta(hours=self.session_timeout_hours)).isoformat(),
                "two_factor_required": decrypted_creds.two_factor_enabled,
                "credentials": decrypted_creds.dict(exclude={"password_hash"})
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return {
                "success": False,
                "error": "Authentication service error"
            }
    
    async def validate_session_token(
        self,
        session_token: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Validate session token and return user information
        """
        try:
            # Decode JWT token
            payload = jwt.decode(session_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check expiration
            if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                return {
                    "valid": False,
                    "error": "Session token expired"
                }
            
            # Get session information
            session_id = payload.get("session_id")
            if not session_id or session_id not in self.active_sessions:
                return {
                    "valid": False,
                    "error": "Invalid session"
                }
            
            session_info = self.active_sessions[session_id]
            
            # Check IP address if provided (optional security check)
            if ip_address and session_info.get("ip_address") != ip_address:
                logger.warning(f"IP address mismatch for session {session_id}")
            
            # Update last activity
            session_info["last_activity"] = datetime.utcnow()
            
            return {
                "valid": True,
                "attorney_id": payload["attorney_id"],
                "court_system": payload["court_system"],
                "username": payload["username"],
                "session_id": session_id,
                "expires_at": datetime.utcfromtimestamp(payload["exp"]).isoformat()
            }
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return {
                "valid": False,
                "error": "Invalid session token"
            }
        except Exception as e:
            logger.error(f"Session validation failed: {str(e)}")
            return {
                "valid": False,
                "error": "Session validation error"
            }
    
    async def logout_session(
        self,
        session_token: str,
        attorney_id: UUID,
        court_system: str
    ) -> Dict[str, any]:
        """
        Logout and invalidate session
        """
        try:
            # Validate token first
            validation_result = await self.validate_session_token(session_token)
            
            if validation_result.get("valid"):
                session_id = validation_result.get("session_id")
                
                # Remove session
                if session_id and session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                
                # Log logout
                await self._log_auth_event(
                    "logout",
                    attorney_id,
                    court_system,
                    True,
                    "User logged out"
                )
                
                return {
                    "success": True,
                    "message": "Logged out successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid session token"
                }
                
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return {
                "success": False,
                "error": "Logout failed"
            }
    
    async def refresh_credentials(
        self,
        attorney_id: UUID,
        court_system: str,
        new_password: str
    ) -> Dict[str, any]:
        """
        Refresh expired credentials with new password
        """
        try:
            cred_key = f"{attorney_id}:{court_system}"
            stored_creds = self.stored_credentials.get(cred_key)
            
            if not stored_creds:
                return {
                    "success": False,
                    "error": "Credentials not found"
                }
            
            # Validate new password
            password_validation = self._validate_password_strength(new_password)
            if not password_validation["valid"]:
                return {
                    "success": False,
                    "error": "Password does not meet security requirements",
                    "requirements": password_validation["requirements"]
                }
            
            # Update password and expiration
            stored_creds.password_hash = self.pwd_context.hash(new_password)
            stored_creds.expires_at = datetime.utcnow() + timedelta(days=self.password_expiry_days)
            stored_creds.needs_renewal = False
            
            # Re-encrypt credentials
            stored_creds = await self._encrypt_credentials(stored_creds)
            self.stored_credentials[cred_key] = stored_creds
            
            # Log credential refresh
            await self._log_auth_event(
                "credential_refresh",
                attorney_id,
                court_system,
                True,
                "Credentials refreshed successfully"
            )
            
            return {
                "success": True,
                "message": "Credentials refreshed successfully",
                "expires_at": stored_creds.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Credential refresh failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def enable_two_factor(
        self,
        attorney_id: UUID,
        court_system: str
    ) -> Dict[str, any]:
        """
        Enable two-factor authentication for credentials
        """
        try:
            cred_key = f"{attorney_id}:{court_system}"
            stored_creds = self.stored_credentials.get(cred_key)
            
            if not stored_creds:
                return {
                    "success": False,
                    "error": "Credentials not found"
                }
            
            # Enable 2FA
            stored_creds.two_factor_enabled = True
            
            # Generate backup codes (in production, would be more sophisticated)
            backup_codes = [secrets.token_hex(8) for _ in range(10)]
            
            # Log 2FA enablement
            await self._log_auth_event(
                "two_factor_enabled",
                attorney_id,
                court_system,
                True,
                "Two-factor authentication enabled"
            )
            
            return {
                "success": True,
                "message": "Two-factor authentication enabled",
                "backup_codes": backup_codes,
                "setup_instructions": "Use an authenticator app to scan the QR code"
            }
            
        except Exception as e:
            logger.error(f"2FA enablement failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_password_strength(self, password: str) -> Dict[str, any]:
        """
        Validate password meets security requirements
        """
        requirements = []
        issues = []
        
        # Length check
        if len(password) < 12:
            issues.append("Password must be at least 12 characters long")
        requirements.append("Minimum 12 characters")
        
        # Character variety checks
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not has_upper:
            issues.append("Password must contain uppercase letters")
        if not has_lower:
            issues.append("Password must contain lowercase letters")
        if not has_digit:
            issues.append("Password must contain numbers")
        if not has_special:
            issues.append("Password must contain special characters")
        
        requirements.extend([
            "Uppercase and lowercase letters",
            "Numbers",
            "Special characters"
        ])
        
        # Common password check (simplified)
        common_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
        if password.lower() in common_passwords:
            issues.append("Password is too common")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "requirements": requirements
        }
    
    async def _encrypt_credentials(self, credentials: EFilingCredentials) -> EFilingCredentials:
        """
        Encrypt sensitive credential fields
        """
        # In production, would encrypt more fields
        if credentials.password_hash:
            credentials.password_hash = self.cipher_suite.encrypt(
                credentials.password_hash.encode()
            ).decode()
        
        return credentials
    
    async def _decrypt_credentials(self, credentials: EFilingCredentials) -> EFilingCredentials:
        """
        Decrypt sensitive credential fields
        """
        decrypted_creds = credentials.copy()
        
        try:
            if credentials.password_hash:
                decrypted_creds.password_hash = self.cipher_suite.decrypt(
                    credentials.password_hash.encode()
                ).decode()
        except Exception as e:
            logger.error(f"Credential decryption failed: {str(e)}")
            
        return decrypted_creds
    
    async def _create_session_token(
        self,
        credentials: EFilingCredentials,
        ip_address: Optional[str]
    ) -> str:
        """
        Create JWT session token
        """
        session_id = secrets.token_urlsafe(32)
        
        payload = {
            "session_id": session_id,
            "attorney_id": str(credentials.attorney_id),
            "court_system": credentials.court_system,
            "username": credentials.username,
            "bar_number": credentials.bar_number,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.session_timeout_hours)
        }
        
        # Store session info
        self.active_sessions[session_id] = {
            "attorney_id": str(credentials.attorney_id),
            "court_system": credentials.court_system,
            "username": credentials.username,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def _record_failed_attempt(self, credential_key: str):
        """
        Record failed authentication attempt
        """
        if credential_key not in self.failed_attempts:
            self.failed_attempts[credential_key] = []
        
        self.failed_attempts[credential_key].append(datetime.utcnow())
        
        # Clean old attempts (older than lockout duration)
        cutoff = datetime.utcnow() - timedelta(minutes=self.lockout_duration_minutes)
        self.failed_attempts[credential_key] = [
            attempt for attempt in self.failed_attempts[credential_key]
            if attempt > cutoff
        ]
    
    async def _is_account_locked(self, credential_key: str) -> bool:
        """
        Check if account is locked due to failed attempts
        """
        if credential_key not in self.failed_attempts:
            return False
        
        recent_attempts = self.failed_attempts[credential_key]
        return len(recent_attempts) >= self.max_failed_attempts
    
    async def _get_lockout_expiry(self, credential_key: str) -> Optional[str]:
        """
        Get when account lockout expires
        """
        if credential_key not in self.failed_attempts:
            return None
        
        recent_attempts = self.failed_attempts[credential_key]
        if not recent_attempts:
            return None
        
        earliest_attempt = min(recent_attempts)
        expiry = earliest_attempt + timedelta(minutes=self.lockout_duration_minutes)
        return expiry.isoformat()
    
    async def _log_auth_event(
        self,
        action: str,
        attorney_id: UUID,
        court_system: str,
        success: bool,
        description: str,
        ip_address: Optional[str] = None
    ):
        """
        Log authentication event for audit purposes
        """
        try:
            audit_log = AuditLog(
                action=action,
                entity_type="authentication",
                entity_id=attorney_id,
                attorney_id=attorney_id,
                ip_address=ip_address,
                description=description,
                system="authentication_service",
                court_system=court_system,
                success=success
            )
            
            # In production, would save to database
            logger.info(f"Auth audit: {action} - {description} - Success: {success}")
            
        except Exception as e:
            logger.error(f"Auth logging failed: {str(e)}")
    
    async def cleanup_expired_sessions(self):
        """
        Clean up expired sessions
        """
        try:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session_info in self.active_sessions.items():
                last_activity = session_info.get("last_activity", session_info["created_at"])
                if current_time - last_activity > timedelta(hours=self.session_timeout_hours):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {str(e)}")
    
    def get_security_metrics(self) -> Dict[str, any]:
        """
        Get security metrics for monitoring
        """
        try:
            active_sessions_count = len(self.active_sessions)
            locked_accounts = sum(
                1 for attempts in self.failed_attempts.values()
                if len(attempts) >= self.max_failed_attempts
            )
            
            return {
                "active_sessions": active_sessions_count,
                "locked_accounts": locked_accounts,
                "total_credentials": len(self.stored_credentials),
                "failed_attempt_records": len(self.failed_attempts),
                "session_timeout_hours": self.session_timeout_hours,
                "max_failed_attempts": self.max_failed_attempts,
                "last_cleanup": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Security metrics failed: {str(e)}")
            return {"error": str(e)}