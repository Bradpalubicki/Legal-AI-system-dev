"""
Client Portal Authentication Manager

Handles client authentication, session management, and security features
including 2FA, account lockout protection, and secure session handling.
"""

import hashlib
import secrets
import pyotp
import qrcode
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import jwt
import bcrypt
from io import BytesIO
import base64

from ..shared.security.jwt_manager import JWTManager
from ..shared.security.security_utils import SecurityUtils
from .models import ClientUser, ClientSession, ClientUserStatus, ClientAuditLog, AuditAction


class ClientAuthManager:
    """Manages client authentication and security."""
    
    def __init__(self, db_session: Session, jwt_secret: str, redis_client=None):
        self.db = db_session
        self.jwt_manager = JWTManager(jwt_secret)
        self.redis_client = redis_client
        self.security_utils = SecurityUtils()
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.session_duration = timedelta(hours=24)
        self.password_min_length = 8
        
    def register_client(
        self, 
        email: str, 
        password: str, 
        first_name: str, 
        last_name: str,
        phone_number: Optional[str] = None,
        company_name: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new client user."""
        try:
            # Validate input
            if not self._validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            if not self._validate_password(password):
                return {'success': False, 'error': 'Password does not meet requirements'}
            
            # Check if user already exists
            existing_user = self.db.query(ClientUser).filter(ClientUser.email == email.lower()).first()
            if existing_user:
                return {'success': False, 'error': 'Email already registered'}
            
            # Create new user
            password_hash = self._hash_password(password)
            verification_token = secrets.token_urlsafe(32)
            
            new_user = ClientUser(
                email=email.lower(),
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                company_name=company_name,
                email_verification_token=verification_token,
                status=ClientUserStatus.PENDING_VERIFICATION,
                created_by=created_by
            )
            
            self.db.add(new_user)
            self.db.commit()
            
            return {
                'success': True,
                'user_id': new_user.id,
                'client_id': new_user.client_id,
                'verification_token': verification_token
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Registration failed: {str(e)}'}
    
    def authenticate_client(
        self, 
        email: str, 
        password: str, 
        ip_address: str,
        user_agent: str,
        two_factor_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate client login."""
        try:
            # Find user by email
            user = self.db.query(ClientUser).filter(
                ClientUser.email == email.lower()
            ).first()
            
            if not user:
                self._log_audit(None, AuditAction.LOGIN, ip_address, user_agent, 
                              success=False, action_details={'email': email, 'reason': 'user_not_found'})
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Check account status
            if user.status == ClientUserStatus.SUSPENDED:
                return {'success': False, 'error': 'Account suspended'}
            
            if user.status == ClientUserStatus.PENDING_VERIFICATION:
                return {'success': False, 'error': 'Please verify your email first'}
            
            # Check if account is locked
            if self._is_account_locked(user):
                return {'success': False, 'error': 'Account temporarily locked due to failed attempts'}
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                self._handle_failed_login(user, ip_address, user_agent)
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Check 2FA if enabled
            if user.two_factor_enabled:
                if not two_factor_code:
                    return {'success': False, 'error': 'Two-factor code required', 'requires_2fa': True}
                
                if not self._verify_2fa_code(user, two_factor_code):
                    self._handle_failed_login(user, ip_address, user_agent)
                    return {'success': False, 'error': 'Invalid two-factor code'}
            
            # Successful authentication
            self._handle_successful_login(user, ip_address, user_agent)
            
            # Create session
            session_result = self._create_session(user, ip_address, user_agent)
            if not session_result['success']:
                return session_result
            
            return {
                'success': True,
                'user': user.to_dict(),
                'session_id': session_result['session_id'],
                'access_token': session_result['access_token'],
                'refresh_token': session_result['refresh_token']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Authentication failed: {str(e)}'}
    
    def verify_email(self, verification_token: str) -> Dict[str, Any]:
        """Verify client email address."""
        try:
            user = self.db.query(ClientUser).filter(
                ClientUser.email_verification_token == verification_token
            ).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid verification token'}
            
            user.is_verified = True
            user.status = ClientUserStatus.ACTIVE
            user.email_verification_token = None
            
            self.db.commit()
            
            return {'success': True, 'message': 'Email verified successfully'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Verification failed: {str(e)}'}
    
    def setup_2fa(self, user_id: int) -> Dict[str, Any]:
        """Setup two-factor authentication for user."""
        try:
            user = self.db.query(ClientUser).filter(ClientUser.id == user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Generate secret
            secret = pyotp.random_base32()
            user.two_factor_secret = secret
            
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name="Legal AI Portal"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.db.commit()
            
            return {
                'success': True,
                'secret': secret,
                'qr_code': qr_code_data,
                'backup_codes': self._generate_backup_codes()
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'2FA setup failed: {str(e)}'}
    
    def enable_2fa(self, user_id: int, verification_code: str) -> Dict[str, Any]:
        """Enable 2FA after verifying setup code."""
        try:
            user = self.db.query(ClientUser).filter(ClientUser.id == user_id).first()
            if not user or not user.two_factor_secret:
                return {'success': False, 'error': 'User not found or 2FA not set up'}
            
            if not self._verify_2fa_code(user, verification_code):
                return {'success': False, 'error': 'Invalid verification code'}
            
            user.two_factor_enabled = True
            self.db.commit()
            
            return {'success': True, 'message': '2FA enabled successfully'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'2FA enable failed: {str(e)}'}
    
    def disable_2fa(self, user_id: int, password: str) -> Dict[str, Any]:
        """Disable two-factor authentication."""
        try:
            user = self.db.query(ClientUser).filter(ClientUser.id == user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if not self._verify_password(password, user.password_hash):
                return {'success': False, 'error': 'Invalid password'}
            
            user.two_factor_enabled = False
            user.two_factor_secret = None
            
            self.db.commit()
            
            return {'success': True, 'message': '2FA disabled successfully'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'2FA disable failed: {str(e)}'}
    
    def validate_session(self, session_id: str, ip_address: str) -> Dict[str, Any]:
        """Validate client session."""
        try:
            session = self.db.query(ClientSession).filter(
                and_(
                    ClientSession.session_id == session_id,
                    ClientSession.is_active == True,
                    ClientSession.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not session:
                return {'success': False, 'error': 'Invalid or expired session'}
            
            # Check IP address for additional security (optional)
            if session.ip_address and session.ip_address != ip_address:
                # Log suspicious activity but don't immediately invalidate
                self._log_audit(
                    session.user_id, AuditAction.LOGIN, ip_address, None,
                    success=False, 
                    action_details={'reason': 'ip_mismatch', 'original_ip': session.ip_address}
                )
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            self.db.commit()
            
            return {
                'success': True,
                'user': session.user.to_dict(),
                'session': {
                    'id': session.session_id,
                    'expires_at': session.expires_at.isoformat(),
                    'last_activity': session.last_activity.isoformat()
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Session validation failed: {str(e)}'}
    
    def logout_client(self, session_id: str, ip_address: str) -> Dict[str, Any]:
        """Logout client and invalidate session."""
        try:
            session = self.db.query(ClientSession).filter(
                ClientSession.session_id == session_id
            ).first()
            
            if session:
                session.is_active = False
                session.invalidated_at = datetime.utcnow()
                session.invalidated_reason = 'logout'
                
                self._log_audit(
                    session.user_id, AuditAction.LOGOUT, ip_address, None,
                    action_details={'session_id': session_id}
                )
                
                self.db.commit()
            
            return {'success': True, 'message': 'Logged out successfully'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Logout failed: {str(e)}'}
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password."""
        try:
            user = self.db.query(ClientUser).filter(ClientUser.id == user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Verify current password
            if not self._verify_password(current_password, user.password_hash):
                return {'success': False, 'error': 'Current password is incorrect'}
            
            # Validate new password
            if not self._validate_password(new_password):
                return {'success': False, 'error': 'New password does not meet requirements'}
            
            # Update password
            user.password_hash = self._hash_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            
            # Invalidate all existing sessions except current one
            self.db.query(ClientSession).filter(
                and_(
                    ClientSession.user_id == user_id,
                    ClientSession.is_active == True
                )
            ).update({
                'is_active': False,
                'invalidated_at': datetime.utcnow(),
                'invalidated_reason': 'password_change'
            })
            
            self.db.commit()
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Password change failed: {str(e)}'}
    
    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Request password reset token."""
        try:
            user = self.db.query(ClientUser).filter(
                ClientUser.email == email.lower()
            ).first()
            
            if not user:
                # Don't reveal if email exists or not
                return {'success': True, 'message': 'If email exists, reset link will be sent'}
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            
            self.db.commit()
            
            return {
                'success': True,
                'message': 'Reset link sent to email',
                'reset_token': reset_token  # In production, send via email
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Password reset request failed: {str(e)}'}
    
    def reset_password(self, reset_token: str, new_password: str) -> Dict[str, Any]:
        """Reset password using token."""
        try:
            user = self.db.query(ClientUser).filter(
                and_(
                    ClientUser.password_reset_token == reset_token,
                    ClientUser.password_reset_expires > datetime.utcnow()
                )
            ).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid or expired reset token'}
            
            if not self._validate_password(new_password):
                return {'success': False, 'error': 'Password does not meet requirements'}
            
            # Update password
            user.password_hash = self._hash_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            user.failed_login_attempts = 0
            user.locked_until = None
            
            # Invalidate all sessions
            self.db.query(ClientSession).filter(
                and_(
                    ClientSession.user_id == user.id,
                    ClientSession.is_active == True
                )
            ).update({
                'is_active': False,
                'invalidated_at': datetime.utcnow(),
                'invalidated_reason': 'password_reset'
            })
            
            self.db.commit()
            
            return {'success': True, 'message': 'Password reset successfully'}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Password reset failed: {str(e)}'}
    
    def _create_session(self, user: ClientUser, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Create authenticated session for user."""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + self.session_duration
            
            # Create session record
            session = ClientSession(
                session_id=session_id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
                login_method='password' + ('_2fa' if user.two_factor_enabled else '')
            )
            
            self.db.add(session)
            
            # Generate JWT tokens
            access_token = self.jwt_manager.create_access_token({
                'user_id': user.id,
                'client_id': user.client_id,
                'session_id': session_id,
                'email': user.email
            })
            
            refresh_token = self.jwt_manager.create_refresh_token({
                'user_id': user.id,
                'session_id': session_id
            })
            
            self.db.commit()
            
            return {
                'success': True,
                'session_id': session_id,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Session creation failed: {str(e)}'}
    
    def _is_account_locked(self, user: ClientUser) -> bool:
        """Check if account is locked due to failed attempts."""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
    
    def _handle_failed_login(self, user: ClientUser, ip_address: str, user_agent: str):
        """Handle failed login attempt."""
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        if user.failed_login_attempts >= self.max_failed_attempts:
            user.locked_until = datetime.utcnow() + self.lockout_duration
        
        self._log_audit(
            user.id, AuditAction.LOGIN, ip_address, user_agent,
            success=False,
            action_details={
                'failed_attempts': user.failed_login_attempts,
                'locked': user.locked_until is not None
            }
        )
        
        self.db.commit()
    
    def _handle_successful_login(self, user: ClientUser, ip_address: str, user_agent: str):
        """Handle successful login."""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        
        self._log_audit(
            user.id, AuditAction.LOGIN, ip_address, user_agent,
            action_details={'login_method': 'password'}
        )
        
        self.db.commit()
    
    def _verify_2fa_code(self, user: ClientUser, code: str) -> bool:
        """Verify 2FA TOTP code."""
        if not user.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(user.two_factor_secret)
        return totp.verify(code, valid_window=1)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < self.password_min_length:
            return False
        
        # Check for at least one uppercase, lowercase, digit, and special char
        import re
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        
        return True
    
    def _generate_backup_codes(self) -> list:
        """Generate backup codes for 2FA."""
        return [secrets.token_hex(4).upper() for _ in range(10)]
    
    def _log_audit(
        self, 
        user_id: Optional[int], 
        action: AuditAction, 
        ip_address: str, 
        user_agent: Optional[str],
        success: bool = True,
        action_details: Optional[Dict] = None
    ):
        """Log audit event."""
        try:
            audit_log = ClientAuditLog(
                user_id=user_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                action_details=action_details or {}
            )
            
            self.db.add(audit_log)
            # Note: Commit handled by calling method
            
        except Exception as e:
            print(f"Audit logging failed: {str(e)}")  # Log to system logs