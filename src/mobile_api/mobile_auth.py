"""
Mobile Authentication Manager

Handles mobile-specific authentication including device registration,
session management, and biometric authentication support.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt

from .models import MobileSession

logger = logging.getLogger(__name__)


class MobileAuthManager:
    """
    Mobile authentication manager that handles:
    - Device registration and verification
    - Mobile session management
    - JWT token generation for mobile clients
    - Biometric authentication support
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.active_sessions: Dict[str, MobileSession] = {}
        
    async def register_mobile_device(
        self,
        user_id: UUID,
        device_id: str,
        device_type: str,
        app_version: str,
        device_info: Optional[Dict] = None
    ) -> MobileSession:
        """
        Register a new mobile device for a user
        """
        try:
            # Check if device is already registered
            existing_session = self._find_session_by_device(device_id, user_id)
            if existing_session:
                # Update existing session
                existing_session.app_version = app_version
                existing_session.last_activity = datetime.utcnow()
                existing_session.is_active = True
                return existing_session
            
            # Create new mobile session
            session = MobileSession(
                user_id=user_id,
                device_id=device_id,
                device_type=device_type,
                app_version=app_version,
                voice_settings={
                    "language": "en-US",
                    "voice_speed": 1.0,
                    "wake_word_enabled": True,
                    "auto_transcription": True,
                    "noise_cancellation": True
                }
            )
            
            # Store session
            self.active_sessions[str(session.id)] = session
            
            logger.info(f"Registered mobile device {device_id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to register mobile device: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Device registration failed: {str(e)}"
            )

    async def authenticate_mobile_session(
        self,
        session_id: UUID,
        device_id: str,
        biometric_data: Optional[str] = None
    ) -> Tuple[bool, Optional[MobileSession]]:
        """
        Authenticate a mobile session
        """
        try:
            session = self.active_sessions.get(str(session_id))
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False, None
            
            if not session.is_active:
                logger.warning(f"Session {session_id} is inactive")
                return False, None
                
            if session.device_id != device_id:
                logger.warning(f"Device ID mismatch for session {session_id}")
                return False, None
            
            # Check session expiry (30 days)
            if datetime.utcnow() - session.created_at > timedelta(days=30):
                session.is_active = False
                logger.warning(f"Session {session_id} expired")
                return False, None
            
            # Verify biometric data if provided
            if biometric_data and not await self._verify_biometric(session, biometric_data):
                logger.warning(f"Biometric verification failed for session {session_id}")
                return False, None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            
            return True, session
            
        except Exception as e:
            logger.error(f"Mobile session authentication failed: {str(e)}")
            return False, None

    async def create_mobile_access_token(
        self,
        user_id: UUID,
        session_id: UUID,
        device_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token for mobile client
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)  # 24 hour default
        
        to_encode = {
            "sub": str(user_id),
            "session_id": str(session_id),
            "device_id": device_id,
            "token_type": "mobile_access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create mobile access token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token creation failed"
            )

    async def create_refresh_token(
        self,
        user_id: UUID,
        session_id: UUID,
        device_id: str
    ) -> str:
        """
        Create JWT refresh token for mobile client
        """
        expire = datetime.utcnow() + timedelta(days=30)  # 30 day refresh token
        
        to_encode = {
            "sub": str(user_id),
            "session_id": str(session_id),
            "device_id": device_id,
            "token_type": "mobile_refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Refresh token creation failed"
            )

    async def verify_mobile_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verify JWT token and return payload
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            token_type = payload.get("token_type")
            if token_type not in ["mobile_access", "mobile_refresh"]:
                return False, None
            
            # Verify session is still active
            session_id = payload.get("session_id")
            if session_id:
                session = self.active_sessions.get(session_id)
                if not session or not session.is_active:
                    return False, None
            
            return True, payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return False, None

    async def refresh_mobile_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh mobile access token using refresh token
        """
        is_valid, payload = await self.verify_mobile_token(refresh_token)
        
        if not is_valid or not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        if payload.get("token_type") != "mobile_refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = UUID(payload["sub"])
        session_id = UUID(payload["session_id"])
        device_id = payload["device_id"]
        
        # Create new tokens
        new_access_token = await self.create_mobile_access_token(
            user_id, session_id, device_id
        )
        new_refresh_token = await self.create_refresh_token(
            user_id, session_id, device_id
        )
        
        return new_access_token, new_refresh_token

    async def logout_mobile_session(
        self,
        session_id: UUID,
        device_id: str
    ) -> bool:
        """
        Logout mobile session
        """
        try:
            session = self.active_sessions.get(str(session_id))
            
            if session and session.device_id == device_id:
                session.is_active = False
                logger.info(f"Mobile session {session_id} logged out")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to logout mobile session: {str(e)}")
            return False

    async def update_voice_settings(
        self,
        session_id: UUID,
        voice_settings: Dict
    ) -> bool:
        """
        Update voice settings for mobile session
        """
        try:
            session = self.active_sessions.get(str(session_id))
            
            if not session:
                return False
            
            # Validate and update voice settings
            valid_settings = {
                "language": voice_settings.get("language", session.voice_settings.get("language", "en-US")),
                "voice_speed": max(0.5, min(2.0, voice_settings.get("voice_speed", 1.0))),
                "wake_word_enabled": voice_settings.get("wake_word_enabled", True),
                "auto_transcription": voice_settings.get("auto_transcription", True),
                "noise_cancellation": voice_settings.get("noise_cancellation", True),
                "preferred_commands": voice_settings.get("preferred_commands", [])
            }
            
            session.voice_settings.update(valid_settings)
            session.last_activity = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update voice settings: {str(e)}")
            return False

    async def get_active_sessions_for_user(self, user_id: UUID) -> List[MobileSession]:
        """
        Get all active mobile sessions for a user
        """
        return [
            session for session in self.active_sessions.values()
            if session.user_id == user_id and session.is_active
        ]

    def _find_session_by_device(
        self,
        device_id: str,
        user_id: UUID
    ) -> Optional[MobileSession]:
        """
        Find existing session by device ID and user ID
        """
        for session in self.active_sessions.values():
            if (session.device_id == device_id and 
                session.user_id == user_id and 
                session.is_active):
                return session
        return None

    async def _verify_biometric(
        self,
        session: MobileSession,
        biometric_data: str
    ) -> bool:
        """
        Verify biometric authentication data
        In a real implementation, this would validate biometric signatures
        """
        try:
            # Placeholder for biometric verification
            # In production, this would:
            # 1. Decrypt biometric data
            # 2. Compare with stored biometric template
            # 3. Return verification result
            
            # For now, we'll do basic validation
            if not biometric_data or len(biometric_data) < 10:
                return False
            
            # Mock verification - in production this would be more sophisticated
            return True
            
        except Exception as e:
            logger.error(f"Biometric verification error: {str(e)}")
            return False

    async def cleanup_expired_sessions(self):
        """
        Clean up expired mobile sessions
        """
        try:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                # Mark sessions as inactive if they haven't been used in 7 days
                if current_time - session.last_activity > timedelta(days=7):
                    session.is_active = False
                    expired_sessions.append(session_id)
                # Remove sessions older than 30 days
                elif current_time - session.created_at > timedelta(days=30):
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired mobile sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {str(e)}")