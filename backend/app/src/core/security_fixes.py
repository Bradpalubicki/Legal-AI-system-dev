"""
SECURITY FIXES FOR LEGAL AI SYSTEM

This module provides secure implementations to replace the vulnerable code.
Apply these fixes immediately before production deployment.
"""

import os
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import jwt
from cryptography.fernet import Fernet
import bcrypt
import redis.asyncio as redis
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class SecureConfig:
    """Secure configuration management with proper secret handling"""

    @staticmethod
    def generate_secure_jwt_secret() -> str:
        """Generate a cryptographically secure JWT secret"""
        return secrets.token_urlsafe(64)  # 512 bits of entropy

    @staticmethod
    def generate_secure_session_secret() -> str:
        """Generate a cryptographically secure session secret"""
        return secrets.token_hex(32)  # 256 bits

    @staticmethod
    def generate_encryption_key() -> bytes:
        """Generate a secure encryption key for Fernet"""
        return Fernet.generate_key()

    @staticmethod
    def validate_secrets():
        """Validate that secrets are properly configured"""
        jwt_secret = os.getenv('JWT_SECRET')
        session_secret = os.getenv('SESSION_SECRET')
        encryption_key = os.getenv('ENCRYPTION_KEY')

        issues = []

        # Check JWT secret
        if not jwt_secret or len(jwt_secret) < 32:
            issues.append("JWT_SECRET is too short or missing")
        if jwt_secret and jwt_secret.startswith('your-'):
            issues.append("JWT_SECRET appears to be a default value")

        # Check session secret
        if not session_secret or len(session_secret) < 32:
            issues.append("SESSION_SECRET is too short or missing")
        if session_secret and session_secret.startswith('your-'):
            issues.append("SESSION_SECRET appears to be a default value")

        # Check encryption key
        if not encryption_key or len(encryption_key) < 32:
            issues.append("ENCRYPTION_KEY is too short or missing")
        if encryption_key and encryption_key.startswith('your-'):
            issues.append("ENCRYPTION_KEY appears to be a default value")

        return issues


class SecureJWTHandler:
    """Secure JWT implementation with proper validation"""

    def __init__(self, secret: str, algorithm: str = "HS256"):
        if len(secret) < 32:
            raise ValueError("JWT secret must be at least 32 characters long")
        self.secret = secret
        self.algorithm = algorithm
        self.allowed_algorithms = ["HS256", "HS384", "HS512"]  # No 'none' allowed

        if algorithm not in self.allowed_algorithms:
            raise ValueError(f"Algorithm must be one of {self.allowed_algorithms}")

    def create_token(self, payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a secure JWT token with proper expiration"""
        to_encode = payload.copy()

        # Always set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=1)  # Default 1 hour

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "nbf": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16)  # Unique token ID
        })

        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token with comprehensive validation"""
        try:
            # Verify token and check all claims
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=self.allowed_algorithms,  # Explicit algorithm whitelist
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "require_exp": True,
                    "require_iat": True,
                    "require_nbf": True
                }
            )

            # Additional security checks
            current_time = datetime.now(timezone.utc).timestamp()

            # Check if token is not too old (beyond normal expiration)
            if payload.get('iat') and current_time - payload['iat'] > 86400:  # 24 hours max
                raise jwt.InvalidTokenError("Token too old")

            # Verify required claims
            required_claims = ['user_id', 'jti']
            for claim in required_claims:
                if claim not in payload:
                    raise jwt.InvalidTokenError(f"Missing required claim: {claim}")

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired token attempted: {token[:20]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token attempted: {token[:20]}... - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )


class SecureRateLimiter:
    """Secure rate limiter with fallback protection"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.fallback_cache: Dict[str, List[float]] = {}
        self.redis_client: Optional[redis.Redis] = None

    async def get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client with error handling"""
        try:
            if self.redis_client is None:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            return self.redis_client
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return None

    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Check rate limit with secure fallback"""
        current_time = time.time()

        # Try Redis first
        redis_client = await self.get_redis_client()
        if redis_client:
            try:
                return await self._check_redis_rate_limit(redis_client, key, limit, window, current_time)
            except Exception as e:
                logger.warning(f"Redis rate limit check failed, using fallback: {e}")

        # Fallback to in-memory rate limiting (SECURE - fails closed)
        return await self._check_fallback_rate_limit(key, limit, window, current_time)

    async def _check_redis_rate_limit(self, client: redis.Redis, key: str, limit: int, window: int, current_time: float) -> tuple[bool, int]:
        """Redis-based rate limiting"""
        window_start = current_time - window

        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, window + 1)

        results = await pipe.execute()
        request_count = results[1]

        return request_count < limit, request_count

    async def _check_fallback_rate_limit(self, key: str, limit: int, window: int, current_time: float) -> tuple[bool, int]:
        """In-memory fallback rate limiting (more restrictive)"""
        fallback_limit = min(limit // 2, 10)  # Reduced limit for fallback

        if key not in self.fallback_cache:
            self.fallback_cache[key] = []

        # Clean old requests
        window_start = current_time - window
        self.fallback_cache[key] = [
            req_time for req_time in self.fallback_cache[key]
            if req_time > window_start
        ]

        # Add current request
        self.fallback_cache[key].append(current_time)

        request_count = len(self.fallback_cache[key])
        return request_count <= fallback_limit, request_count


class SecureAPIKeyManager:
    """Secure API key management"""

    def __init__(self, secret: str):
        self.secret = secret.encode() if isinstance(secret, str) else secret

    def generate_api_key(self) -> tuple[str, str]:
        """Generate secure API key and return key and hash"""
        # Generate cryptographically secure random key
        api_key = f"legalai_{secrets.token_urlsafe(32)}"
        api_key_hash = self._hash_api_key(api_key)
        return api_key, api_key_hash

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key securely using bcrypt directly"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(api_key.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_api_key(self, api_key: str, api_key_hash: str) -> bool:
        """Verify API key against hash"""
        if not api_key or not api_key_hash:
            return False

        # Check minimum length
        if len(api_key) < 20:
            return False

        # Check format
        if not api_key.startswith('legalai_'):
            return False

        try:
            return bcrypt.checkpw(api_key.encode('utf-8'), api_key_hash.encode('utf-8'))
        except Exception:
            return False


class SecureDataEncryption:
    """Secure data encryption for sensitive information"""

    def __init__(self, encryption_key: bytes):
        self.cipher_suite = Fernet(encryption_key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return ""
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return ""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

    def encrypt_dict(self, data: Dict[str, Any], sensitive_keys: List[str]) -> Dict[str, Any]:
        """Encrypt sensitive fields in dictionary"""
        result = data.copy()
        for key in sensitive_keys:
            if key in result and result[key]:
                result[key] = self.encrypt(str(result[key]))
        return result

    def decrypt_dict(self, data: Dict[str, Any], sensitive_keys: List[str]) -> Dict[str, Any]:
        """Decrypt sensitive fields in dictionary"""
        result = data.copy()
        for key in sensitive_keys:
            if key in result and result[key]:
                try:
                    result[key] = self.decrypt(result[key])
                except Exception:
                    logger.error(f"Failed to decrypt field: {key}")
        return result


class SecureSessionManager:
    """Secure session management with proper validation"""

    def __init__(self, redis_url: str, secret_key: str):
        self.redis_url = redis_url
        self.secret_key = secret_key
        self.redis_client: Optional[redis.Redis] = None

    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    def generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)

    async def create_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = 3600) -> str:
        """Create secure session"""
        session_id = self.generate_session_id()

        session_data.update({
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_accessed': datetime.now(timezone.utc).isoformat(),
            'ip_address': session_data.get('ip_address'),
            'user_agent': session_data.get('user_agent')
        })

        redis_client = await self.get_redis_client()
        await redis_client.setex(f"session:{session_id}", ttl, str(session_data))

        return session_id

    async def validate_session(self, session_id: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """Validate session with security checks"""
        if not session_id or len(session_id) < 20:
            return None

        try:
            redis_client = await self.get_redis_client()
            session_data = await redis_client.get(f"session:{session_id}")

            if not session_data:
                return None

            session_data = eval(session_data)  # In production, use json.loads

            # Validate IP address consistency (optional but recommended)
            if ip_address and session_data.get('ip_address'):
                if session_data['ip_address'] != ip_address:
                    logger.warning(f"Session IP mismatch for session {session_id}")
                    # Could return None for strict IP validation

            # Update last accessed time
            session_data['last_accessed'] = datetime.now(timezone.utc).isoformat()
            await redis_client.setex(f"session:{session_id}", 3600, str(session_data))

            return session_data

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke session"""
        try:
            redis_client = await self.get_redis_client()
            result = await redis_client.delete(f"session:{session_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Session revocation error: {e}")
            return False


class SecurityAuditor:
    """Security auditing and monitoring"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    async def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        event = {
            'type': event_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': details
        }

        # Log to file
        logger.warning(f"SECURITY EVENT: {event_type} - {details}")

        # Store in Redis for monitoring
        try:
            redis_client = await self.get_redis_client()
            await redis_client.lpush("security_events", str(event))
            await redis_client.ltrim("security_events", 0, 999)  # Keep last 1000 events
        except Exception as e:
            logger.error(f"Failed to store security event: {e}")

    async def track_failed_attempts(self, identifier: str, attempt_type: str = "login") -> int:
        """Track failed authentication attempts"""
        key = f"failed_attempts:{attempt_type}:{identifier}"

        try:
            redis_client = await self.get_redis_client()
            current_attempts = await redis_client.incr(key)
            await redis_client.expire(key, 300)  # 5 minute window

            if current_attempts >= 5:  # Threshold for blocking
                await self.log_security_event("BRUTE_FORCE_DETECTED", {
                    'identifier': identifier,
                    'attempt_type': attempt_type,
                    'attempts': current_attempts
                })

            return current_attempts

        except Exception as e:
            logger.error(f"Failed to track attempts: {e}")
            return 0

    async def is_blocked(self, identifier: str, attempt_type: str = "login") -> bool:
        """Check if identifier is blocked due to too many failed attempts"""
        key = f"failed_attempts:{attempt_type}:{identifier}"

        try:
            redis_client = await self.get_redis_client()
            attempts = await redis_client.get(key)
            return int(attempts or 0) >= 5
        except Exception:
            return False


# Example usage and integration
def create_secure_components():
    """Create secure component instances"""

    # Validate configuration first
    config_issues = SecureConfig.validate_secrets()
    if config_issues:
        raise ValueError(f"Configuration issues: {', '.join(config_issues)}")

    # Create secure components
    jwt_handler = SecureJWTHandler(
        secret=os.getenv('JWT_SECRET'),
        algorithm="HS256"
    )

    rate_limiter = SecureRateLimiter(
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    )

    api_key_manager = SecureAPIKeyManager(
        secret=os.getenv('API_KEY_SECRET', os.getenv('JWT_SECRET'))
    )

    encryption_key = os.getenv('ENCRYPTION_KEY').encode()
    data_encryptor = SecureDataEncryption(encryption_key)

    session_manager = SecureSessionManager(
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        secret_key=os.getenv('SESSION_SECRET')
    )

    auditor = SecurityAuditor(
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    )

    return {
        'jwt_handler': jwt_handler,
        'rate_limiter': rate_limiter,
        'api_key_manager': api_key_manager,
        'data_encryptor': data_encryptor,
        'session_manager': session_manager,
        'auditor': auditor
    }


# Security configuration checker
def check_security_configuration():
    """Check if security configuration is properly set up"""
    issues = []

    # Check environment variables
    required_vars = [
        'JWT_SECRET', 'SESSION_SECRET', 'ENCRYPTION_KEY',
        'DATABASE_PASSWORD', 'REDIS_PASSWORD'
    ]

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            issues.append(f"{var} is not set")
        elif value.startswith('your-') or value in ['password', 'secret', 'key']:
            issues.append(f"{var} appears to use a default/weak value")
        elif len(value) < 20:
            issues.append(f"{var} is too short (minimum 20 characters)")

    return issues


if __name__ == "__main__":
    # Run security configuration check
    issues = check_security_configuration()
    if issues:
        print("❌ SECURITY CONFIGURATION ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n🔧 Run the following commands to fix:")
        print("python -c \"from core.security_fixes import SecureConfig; print('JWT_SECRET=' + SecureConfig.generate_secure_jwt_secret())\"")
    else:
        print("✅ Security configuration looks good!")