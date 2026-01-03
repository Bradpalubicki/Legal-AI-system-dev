"""
Authentication middleware for WebSocket connections.

Handles authentication, authorization, and security for real-time transcript
streaming with support for JWT tokens, API keys, and role-based access control.
"""

import asyncio
import jwt
import hashlib
import hmac
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..shared.utils import BaseAPIClient


class AuthMethod(Enum):
    """Authentication methods supported."""
    JWT_TOKEN = "jwt_token"
    API_KEY = "api_key"
    SESSION_TOKEN = "session_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


class Permission(Enum):
    """WebSocket permissions."""
    # Session management
    CREATE_SESSION = "create_session"
    JOIN_SESSION = "join_session"
    END_SESSION = "end_session"
    
    # Streaming
    STREAM_AUDIO = "stream_audio"
    STREAM_TEXT = "stream_text"
    RECEIVE_TRANSCRIPTS = "receive_transcripts"
    
    # Analysis and insights
    RECEIVE_ANALYSIS = "receive_analysis"
    RECEIVE_LEGAL_INSIGHTS = "receive_legal_insights"
    RECEIVE_OBJECTIONS = "receive_objections"
    RECEIVE_EVIDENCE = "receive_evidence"
    
    # Recording
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    ACCESS_RECORDINGS = "access_recordings"
    
    # Administration
    VIEW_ALL_SESSIONS = "view_all_sessions"
    MODERATE_SESSIONS = "moderate_sessions"
    MANAGE_USERS = "manage_users"
    
    # Data access
    EXPORT_TRANSCRIPTS = "export_transcripts"
    ACCESS_HISTORICAL = "access_historical"
    DOWNLOAD_AUDIO = "download_audio"


@dataclass
class AuthResult:
    """Result of authentication attempt."""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    session_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    # Rate limiting
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    
    # Additional context
    client_id: Optional[str] = None
    organization_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)


@dataclass
class AuthConfig:
    """Configuration for authentication middleware."""
    # JWT Configuration
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_issuer: Optional[str] = None
    jwt_audience: Optional[str] = None
    
    # API Key Configuration
    api_key_header: str = "X-API-Key"
    api_key_validation_url: Optional[str] = None
    
    # Rate limiting
    enable_rate_limiting: bool = True
    requests_per_minute: int = 100
    burst_limit: int = 20
    
    # Session management
    session_timeout: int = 3600  # seconds
    max_concurrent_sessions: int = 5
    
    # Security
    require_https: bool = True
    allowed_origins: Optional[List[str]] = None
    ip_whitelist: Optional[List[str]] = None
    ip_blacklist: Optional[List[str]] = None
    
    # Permissions
    default_permissions: List[str] = field(default_factory=list)
    role_permissions: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class RateLimitState:
    """Rate limiting state for a user/IP."""
    requests: List[datetime] = field(default_factory=list)
    blocked_until: Optional[datetime] = None
    total_requests: int = 0
    
    def is_blocked(self) -> bool:
        """Check if currently blocked."""
        if self.blocked_until and datetime.utcnow() < self.blocked_until:
            return True
        
        # Clean up old request timestamps
        cutoff = datetime.utcnow() - timedelta(minutes=1)
        self.requests = [req_time for req_time in self.requests if req_time > cutoff]
        
        return False
    
    def add_request(self) -> bool:
        """Add request and check if rate limit exceeded."""
        now = datetime.utcnow()
        self.requests.append(now)
        self.total_requests += 1
        
        # Check if over limit
        if len(self.requests) > 100:  # Default limit
            self.blocked_until = now + timedelta(minutes=5)
            return False
        
        return True


class WebSocketAuthMiddleware:
    """Authentication and authorization middleware for WebSocket connections."""
    
    def __init__(self, 
                 config: AuthConfig,
                 api_client: Optional[BaseAPIClient] = None):
        self.config = config
        self.api_client = api_client
        
        # Rate limiting
        self.rate_limits: Dict[str, RateLimitState] = {}
        
        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Permission cache
        self.permission_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=15)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize role permissions
        self._initialize_default_roles()
    
    def _initialize_default_roles(self):
        """Initialize default role-based permissions."""
        if not self.config.role_permissions:
            self.config.role_permissions = {
                "judge": [
                    Permission.CREATE_SESSION.value,
                    Permission.JOIN_SESSION.value,
                    Permission.END_SESSION.value,
                    Permission.RECEIVE_TRANSCRIPTS.value,
                    Permission.RECEIVE_ANALYSIS.value,
                    Permission.RECEIVE_LEGAL_INSIGHTS.value,
                    Permission.START_RECORDING.value,
                    Permission.STOP_RECORDING.value,
                    Permission.ACCESS_RECORDINGS.value,
                    Permission.MODERATE_SESSIONS.value,
                    Permission.EXPORT_TRANSCRIPTS.value
                ],
                "attorney": [
                    Permission.CREATE_SESSION.value,
                    Permission.JOIN_SESSION.value,
                    Permission.STREAM_AUDIO.value,
                    Permission.STREAM_TEXT.value,
                    Permission.RECEIVE_TRANSCRIPTS.value,
                    Permission.RECEIVE_ANALYSIS.value,
                    Permission.RECEIVE_LEGAL_INSIGHTS.value,
                    Permission.RECEIVE_OBJECTIONS.value,
                    Permission.RECEIVE_EVIDENCE.value,
                    Permission.ACCESS_RECORDINGS.value,
                    Permission.EXPORT_TRANSCRIPTS.value
                ],
                "court_reporter": [
                    Permission.JOIN_SESSION.value,
                    Permission.STREAM_AUDIO.value,
                    Permission.STREAM_TEXT.value,
                    Permission.RECEIVE_TRANSCRIPTS.value,
                    Permission.START_RECORDING.value,
                    Permission.STOP_RECORDING.value,
                    Permission.ACCESS_RECORDINGS.value,
                    Permission.EXPORT_TRANSCRIPTS.value
                ],
                "observer": [
                    Permission.JOIN_SESSION.value,
                    Permission.RECEIVE_TRANSCRIPTS.value,
                    Permission.RECEIVE_ANALYSIS.value
                ],
                "admin": [perm.value for perm in Permission]  # All permissions
            }
        
        if not self.config.default_permissions:
            self.config.default_permissions = [
                Permission.JOIN_SESSION.value,
                Permission.RECEIVE_TRANSCRIPTS.value
            ]
    
    async def authenticate(self, 
                         auth_data: Dict[str, Any], 
                         connection_id: str,
                         ip_address: Optional[str] = None) -> AuthResult:
        """
        Authenticate WebSocket connection.
        
        Args:
            auth_data: Authentication data from client
            connection_id: WebSocket connection ID
            ip_address: Client IP address
            
        Returns:
            AuthResult with authentication outcome
        """
        try:
            # Check rate limiting
            if not await self._check_rate_limit(connection_id, ip_address):
                return AuthResult(
                    success=False,
                    error_message="Rate limit exceeded",
                    rate_limit_remaining=0
                )
            
            # Check IP restrictions
            if not self._check_ip_restrictions(ip_address):
                return AuthResult(
                    success=False,
                    error_message="IP address not allowed"
                )
            
            # Determine authentication method
            auth_method = self._determine_auth_method(auth_data)
            
            # Perform authentication
            if auth_method == AuthMethod.JWT_TOKEN:
                result = await self._authenticate_jwt(auth_data)
            elif auth_method == AuthMethod.API_KEY:
                result = await self._authenticate_api_key(auth_data)
            elif auth_method == AuthMethod.SESSION_TOKEN:
                result = await self._authenticate_session_token(auth_data)
            elif auth_method == AuthMethod.BASIC_AUTH:
                result = await self._authenticate_basic_auth(auth_data)
            elif auth_method == AuthMethod.OAUTH2:
                result = await self._authenticate_oauth2(auth_data)
            else:
                return AuthResult(
                    success=False,
                    error_message="Unsupported authentication method"
                )
            
            # If authentication successful, setup session
            if result.success:
                await self._setup_session(connection_id, result)
                
                # Update rate limit info
                rate_limit_state = self.rate_limits.get(connection_id)
                if rate_limit_state:
                    result.rate_limit_remaining = max(0, 100 - len(rate_limit_state.requests))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Authentication error for connection {connection_id}: {e}")
            return AuthResult(
                success=False,
                error_message="Authentication failed"
            )
    
    async def authorize(self, 
                       connection_id: str, 
                       required_permission: str,
                       resource_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if connection has required permission.
        
        Args:
            connection_id: WebSocket connection ID
            required_permission: Required permission
            resource_context: Optional context for resource-specific authorization
            
        Returns:
            True if authorized
        """
        session = self.active_sessions.get(connection_id)
        if not session:
            return False
        
        # Check if session is expired
        if session.get("expires_at") and datetime.utcnow() > session["expires_at"]:
            await self._cleanup_session(connection_id)
            return False
        
        # Check basic permission
        user_permissions = session.get("permissions", [])
        if required_permission not in user_permissions:
            return False
        
        # Check resource-specific authorization if context provided
        if resource_context:
            return await self._check_resource_authorization(
                session, required_permission, resource_context
            )
        
        return True
    
    async def get_user_context(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get user context for connection."""
        session = self.active_sessions.get(connection_id)
        if not session:
            return None
        
        return {
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "permissions": session.get("permissions", []),
            "roles": session.get("roles", []),
            "organization_id": session.get("organization_id"),
            "client_id": session.get("client_id")
        }
    
    async def cleanup_connection(self, connection_id: str):
        """Clean up authentication state for connection."""
        await self._cleanup_session(connection_id)
        
        # Clean up rate limiting (optional - might want to keep for IP tracking)
        if connection_id in self.rate_limits:
            del self.rate_limits[connection_id]
    
    def _determine_auth_method(self, auth_data: Dict[str, Any]) -> AuthMethod:
        """Determine authentication method from auth data."""
        data = auth_data.get("data", {})
        
        if "token" in data:
            # Try to decode as JWT
            try:
                jwt.decode(data["token"], options={"verify_signature": False})
                return AuthMethod.JWT_TOKEN
            except:
                return AuthMethod.SESSION_TOKEN
        elif "api_key" in data:
            return AuthMethod.API_KEY
        elif "username" in data and "password" in data:
            return AuthMethod.BASIC_AUTH
        elif "access_token" in data:
            return AuthMethod.OAUTH2
        
        return AuthMethod.JWT_TOKEN  # Default
    
    async def _authenticate_jwt(self, auth_data: Dict[str, Any]) -> AuthResult:
        """Authenticate using JWT token."""
        data = auth_data.get("data", {})
        token = data.get("token")
        
        if not token:
            return AuthResult(success=False, error_message="No token provided")
        
        if not self.config.jwt_secret:
            return AuthResult(success=False, error_message="JWT authentication not configured")
        
        try:
            # Decode JWT
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                issuer=self.config.jwt_issuer,
                audience=self.config.jwt_audience
            )
            
            # Extract user information
            user_id = payload.get("sub")
            username = payload.get("username") or payload.get("preferred_username")
            roles = payload.get("roles", [])
            permissions = payload.get("permissions", [])
            
            # Add role-based permissions
            for role in roles:
                role_perms = self.config.role_permissions.get(role, [])
                permissions.extend(role_perms)
            
            # Add default permissions
            permissions.extend(self.config.default_permissions)
            
            # Remove duplicates
            permissions = list(set(permissions))
            
            return AuthResult(
                success=True,
                user_id=user_id,
                username=username,
                permissions=permissions,
                roles=roles,
                expires_at=datetime.fromtimestamp(payload.get("exp", 0)) if payload.get("exp") else None,
                organization_id=payload.get("org_id"),
                client_id=payload.get("client_id")
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(success=False, error_message="Token expired")
        except jwt.InvalidTokenError as e:
            return AuthResult(success=False, error_message=f"Invalid token: {str(e)}")
        except Exception as e:
            self.logger.error(f"JWT authentication error: {e}")
            return AuthResult(success=False, error_message="Authentication failed")
    
    async def _authenticate_api_key(self, auth_data: Dict[str, Any]) -> AuthResult:
        """Authenticate using API key."""
        data = auth_data.get("data", {})
        api_key = data.get("api_key")
        
        if not api_key:
            return AuthResult(success=False, error_message="No API key provided")
        
        try:
            # Validate API key with external service
            if self.api_client and self.config.api_key_validation_url:
                response = await self.api_client.post(
                    self.config.api_key_validation_url,
                    json={"api_key": api_key},
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.get("valid"):
                    user_data = response.get("user", {})
                    permissions = user_data.get("permissions", [])
                    roles = user_data.get("roles", [])
                    
                    # Add role-based permissions
                    for role in roles:
                        role_perms = self.config.role_permissions.get(role, [])
                        permissions.extend(role_perms)
                    
                    permissions.extend(self.config.default_permissions)
                    permissions = list(set(permissions))
                    
                    return AuthResult(
                        success=True,
                        user_id=user_data.get("id"),
                        username=user_data.get("username"),
                        permissions=permissions,
                        roles=roles,
                        organization_id=user_data.get("organization_id"),
                        client_id=user_data.get("client_id")
                    )
                else:
                    return AuthResult(success=False, error_message="Invalid API key")
            else:
                # Simple validation (for development)
                if self._validate_api_key_format(api_key):
                    return AuthResult(
                        success=True,
                        user_id=f"api_user_{api_key[:8]}",
                        permissions=self.config.default_permissions
                    )
                else:
                    return AuthResult(success=False, error_message="Invalid API key format")
                    
        except Exception as e:
            self.logger.error(f"API key authentication error: {e}")
            return AuthResult(success=False, error_message="Authentication failed")
    
    async def _authenticate_session_token(self, auth_data: Dict[str, Any]) -> AuthResult:
        """Authenticate using session token."""
        data = auth_data.get("data", {})
        token = data.get("token")
        
        if not token:
            return AuthResult(success=False, error_message="No session token provided")
        
        try:
            # Validate session token with API
            if self.api_client:
                response = await self.api_client.get(
                    "/auth/validate-session",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.get("valid"):
                    user_data = response.get("user", {})
                    permissions = user_data.get("permissions", [])
                    permissions.extend(self.config.default_permissions)
                    
                    return AuthResult(
                        success=True,
                        user_id=user_data.get("id"),
                        username=user_data.get("username"),
                        permissions=list(set(permissions)),
                        roles=user_data.get("roles", []),
                        organization_id=user_data.get("organization_id")
                    )
                else:
                    return AuthResult(success=False, error_message="Invalid session token")
            else:
                return AuthResult(success=False, error_message="Session authentication not available")
                
        except Exception as e:
            self.logger.error(f"Session token authentication error: {e}")
            return AuthResult(success=False, error_message="Authentication failed")
    
    async def _authenticate_basic_auth(self, auth_data: Dict[str, Any]) -> AuthResult:
        """Authenticate using username/password."""
        data = auth_data.get("data", {})
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return AuthResult(success=False, error_message="Username and password required")
        
        try:
            # Authenticate with API
            if self.api_client:
                response = await self.api_client.post(
                    "/auth/login",
                    json={"username": username, "password": password}
                )
                
                if response.get("success"):
                    user_data = response.get("user", {})
                    permissions = user_data.get("permissions", [])
                    permissions.extend(self.config.default_permissions)
                    
                    return AuthResult(
                        success=True,
                        user_id=user_data.get("id"),
                        username=username,
                        permissions=list(set(permissions)),
                        roles=user_data.get("roles", []),
                        organization_id=user_data.get("organization_id")
                    )
                else:
                    return AuthResult(success=False, error_message="Invalid credentials")
            else:
                return AuthResult(success=False, error_message="Basic authentication not available")
                
        except Exception as e:
            self.logger.error(f"Basic authentication error: {e}")
            return AuthResult(success=False, error_message="Authentication failed")
    
    async def _authenticate_oauth2(self, auth_data: Dict[str, Any]) -> AuthResult:
        """Authenticate using OAuth2 access token."""
        data = auth_data.get("data", {})
        access_token = data.get("access_token")
        
        if not access_token:
            return AuthResult(success=False, error_message="No access token provided")
        
        try:
            # Validate OAuth2 token with provider
            if self.api_client:
                response = await self.api_client.get(
                    "/auth/oauth2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.get("sub"):  # Standard OAuth2 user ID field
                    permissions = self.config.default_permissions.copy()
                    
                    return AuthResult(
                        success=True,
                        user_id=response.get("sub"),
                        username=response.get("preferred_username") or response.get("email"),
                        permissions=permissions,
                        organization_id=response.get("org_id")
                    )
                else:
                    return AuthResult(success=False, error_message="Invalid access token")
            else:
                return AuthResult(success=False, error_message="OAuth2 authentication not available")
                
        except Exception as e:
            self.logger.error(f"OAuth2 authentication error: {e}")
            return AuthResult(success=False, error_message="Authentication failed")
    
    async def _check_rate_limit(self, connection_id: str, ip_address: Optional[str]) -> bool:
        """Check rate limiting for connection/IP."""
        if not self.config.enable_rate_limiting:
            return True
        
        # Use IP address if available, otherwise connection ID
        rate_key = ip_address or connection_id
        
        if rate_key not in self.rate_limits:
            self.rate_limits[rate_key] = RateLimitState()
        
        rate_limit_state = self.rate_limits[rate_key]
        
        if rate_limit_state.is_blocked():
            return False
        
        return rate_limit_state.add_request()
    
    def _check_ip_restrictions(self, ip_address: Optional[str]) -> bool:
        """Check IP whitelist/blacklist restrictions."""
        if not ip_address:
            return True
        
        # Check blacklist first
        if self.config.ip_blacklist and ip_address in self.config.ip_blacklist:
            return False
        
        # Check whitelist if configured
        if self.config.ip_whitelist and ip_address not in self.config.ip_whitelist:
            return False
        
        return True
    
    async def _setup_session(self, connection_id: str, auth_result: AuthResult):
        """Setup session state for authenticated connection."""
        session_data = {
            "user_id": auth_result.user_id,
            "username": auth_result.username,
            "permissions": auth_result.permissions,
            "roles": auth_result.roles,
            "organization_id": auth_result.organization_id,
            "client_id": auth_result.client_id,
            "authenticated_at": datetime.utcnow(),
            "expires_at": auth_result.expires_at,
            "session_data": auth_result.session_data
        }
        
        self.active_sessions[connection_id] = session_data
        
        self.logger.info(f"Session established for user {auth_result.user_id} on connection {connection_id}")
    
    async def _cleanup_session(self, connection_id: str):
        """Clean up session state."""
        if connection_id in self.active_sessions:
            user_id = self.active_sessions[connection_id].get("user_id")
            del self.active_sessions[connection_id]
            self.logger.info(f"Session cleaned up for user {user_id} on connection {connection_id}")
    
    async def _check_resource_authorization(self, 
                                          session: Dict[str, Any],
                                          permission: str,
                                          resource_context: Dict[str, Any]) -> bool:
        """Check resource-specific authorization."""
        # Example: Check if user can access specific session
        if "session_id" in resource_context:
            session_id = resource_context["session_id"]
            
            # Admin can access all sessions
            if "admin" in session.get("roles", []):
                return True
            
            # Check if user has permission for this specific session
            # This would typically involve checking database/cache
            # For now, allow if user has the basic permission
            return True
        
        # Default: allow if user has the permission
        return True
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format."""
        # Simple validation - in production use more sophisticated validation
        return (len(api_key) >= 32 and 
                all(c.isalnum() or c in '-_' for c in api_key))
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        return {
            "active_sessions": len(self.active_sessions),
            "rate_limited_connections": len(self.rate_limits),
            "blocked_connections": sum(
                1 for state in self.rate_limits.values() 
                if state.is_blocked()
            ),
            "authentication_methods": {
                "jwt_enabled": bool(self.config.jwt_secret),
                "api_key_enabled": bool(self.config.api_key_validation_url),
                "rate_limiting_enabled": self.config.enable_rate_limiting
            }
        }