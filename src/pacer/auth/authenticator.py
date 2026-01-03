# -*- coding: utf-8 -*-
"""
PACER Authentication Module

Handles PACER authentication with:
- Secure token caching in Redis
- Encryption at rest
- MFA/OTP support
- Token lifecycle management
- Comprehensive error handling
"""

import httpx
import json
import logging
import hashlib
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from functools import wraps

from cryptography.fernet import Fernet
import redis.asyncio as redis

# Try to import from backend config, fallback to environment variables
try:
    from backend.app.src.core.config import get_settings
    settings = get_settings()
except ImportError:
    import os
    class Settings:
        PACER_ENVIRONMENT = os.getenv("PACER_ENVIRONMENT", "production")
        PACER_ENCRYPTION_KEY = os.getenv("PACER_ENCRYPTION_KEY")
        REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        REDIS_DB = int(os.getenv("REDIS_DB", "0"))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        # PACER sessions timeout after 15 minutes, cache for 12 minutes
        PACER_TOKEN_CACHE_TTL = int(os.getenv("PACER_TOKEN_CACHE_TTL", "720"))
        PACER_TOKEN_CACHE_ENABLED = os.getenv("PACER_TOKEN_CACHE_ENABLED", "true").lower() == "true"
    settings = Settings()


logger = logging.getLogger(__name__)


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for exponential delay
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), retrying in {current_delay}s")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                except Exception as e:
                    # Don't retry on other exceptions
                    raise

            raise last_exception
        return wrapper
    return decorator


class PACERAuthenticationError(Exception):
    """Base exception for PACER authentication errors"""
    pass


class PACERMFARequiredError(PACERAuthenticationError):
    """Raised when MFA/OTP is required but not provided"""
    pass


class PACERInvalidCredentialsError(PACERAuthenticationError):
    """Raised when credentials are invalid"""
    pass


class PACERRateLimitError(PACERAuthenticationError):
    """Raised when rate limit is exceeded"""
    pass


class PACERAuthenticator:
    """
    Handles PACER authentication with token management.

    Features:
    - Secure token caching with encryption
    - MFA/OTP support
    - Automatic token refresh
    - Comprehensive error handling
    - Connection pooling
    """

    def __init__(self, environment: str = None):
        """
        Initialize PACER authenticator.

        Args:
            environment: PACER environment ('production' or 'qa')
        """
        self.env = environment or getattr(settings, 'PACER_ENVIRONMENT', 'production')
        self.base_url = self._get_base_url()

        # Initialize encryption
        self._init_encryption()

        # Initialize Redis connection
        self.redis_client = None
        self.cache_enabled = getattr(settings, 'PACER_TOKEN_CACHE_ENABLED', True)
        # PACER sessions timeout after 15 minutes, cache for 12 minutes to provide buffer
        self.cache_ttl = getattr(settings, 'PACER_TOKEN_CACHE_TTL', 720)

        # HTTP client configuration
        self.http_timeout = httpx.Timeout(30.0, connect=10.0)
        self.max_retries = 3

        # Rate limiting configuration
        self.max_auth_attempts = 5  # Max authentication attempts
        self.rate_limit_window = 300  # 5 minutes in seconds

        # Connection pool for Redis (will be created lazily)
        self._redis_pool = None

        logger.info(f"PACERAuthenticator initialized for {self.env} environment")

    def _init_encryption(self):
        """Initialize encryption key for token storage"""
        try:
            # Try to load from config file
            config_path = Path(".pacer_config/keys.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    key_path = Path(config.get("encryption_key_path"))
                    if key_path.exists():
                        with open(key_path, 'rb') as kf:
                            encryption_key = kf.read()
                        self.fernet = Fernet(encryption_key)
                        logger.info("Loaded encryption key from config")
                        return

            # Fallback to environment variable
            encryption_key = getattr(settings, 'PACER_ENCRYPTION_KEY', None)
            if encryption_key:
                # Ensure it's bytes
                if isinstance(encryption_key, str):
                    encryption_key = encryption_key.encode()
                self.fernet = Fernet(encryption_key)
                logger.info("Loaded encryption key from environment")
            else:
                # Generate temporary key (WARNING: tokens won't persist across restarts)
                logger.warning("No encryption key found, generating temporary key")
                self.fernet = Fernet(Fernet.generate_key())

        except Exception as e:
            logger.error(f"Error initializing encryption: {e}")
            # Use temporary key as fallback
            self.fernet = Fernet(Fernet.generate_key())

    async def _init_redis(self):
        """Initialize Redis connection lazily"""
        if not self.cache_enabled:
            return None

        if self.redis_client is not None:
            return self.redis_client

        try:
            redis_config = {
                'host': getattr(settings, 'REDIS_HOST', 'localhost'),
                'port': getattr(settings, 'REDIS_PORT', 6379),
                'db': getattr(settings, 'REDIS_DB', 0),
                'decode_responses': False,  # We handle encoding ourselves
                'socket_timeout': 5,
                'socket_connect_timeout': 5
            }

            # Add password if configured
            redis_password = getattr(settings, 'REDIS_PASSWORD', None)
            if redis_password:
                redis_config['password'] = redis_password

            self.redis_client = redis.Redis(**redis_config)

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established")
            return self.redis_client

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Token caching disabled.")
            self.cache_enabled = False
            return None

    def _get_base_url(self) -> str:
        """Get appropriate base URL for environment."""
        if self.env.lower() == "qa":
            return "https://qa-login.uscourts.gov"
        return "https://pacer.login.uscourts.gov"

    @staticmethod
    def _hash_username(username: str) -> str:
        """
        Hash username with SHA-256 for privacy in Redis keys.

        Args:
            username: PACER username to hash

        Returns:
            Hexadecimal SHA-256 hash of username
        """
        return hashlib.sha256(username.encode()).hexdigest()

    @staticmethod
    def _sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive data before logging.

        Args:
            data: Dictionary that may contain sensitive information

        Returns:
            Sanitized dictionary safe for logging
        """
        sensitive_fields = [
            'password', 'loginId', 'twoFactorCode', 'nextGenCSO',
            'token', 'clientCode', 'otp', 'pacer_password'
        ]

        sanitized = data.copy()
        for field in sensitive_fields:
            if field in sanitized:
                if isinstance(sanitized[field], str) and len(sanitized[field]) > 0:
                    # Show first 2 chars for debugging, mask rest
                    sanitized[field] = sanitized[field][:2] + "***REDACTED***"
                else:
                    sanitized[field] = "***REDACTED***"

        # Partially mask usernames for privacy
        if 'username' in sanitized and isinstance(sanitized['username'], str):
            username = sanitized['username']
            if len(username) > 4:
                sanitized['username'] = username[:2] + "***" + username[-2:]
            else:
                sanitized['username'] = "***"

        return sanitized

    async def _check_rate_limit(self, username: str) -> bool:
        """
        Check if user has exceeded authentication rate limit.

        Args:
            username: PACER username to check

        Returns:
            True if within rate limit, False if exceeded

        Raises:
            PACERRateLimitError: If rate limit is exceeded
        """
        try:
            redis_client = await self._init_redis()
            if redis_client is None:
                # If Redis unavailable, allow the request (fail open)
                return True

            username_hash = self._hash_username(username)
            key = f"pacer:ratelimit:{username_hash}"

            # Get current attempt count
            attempts = await redis_client.get(key)

            if attempts:
                attempts = int(attempts)
                if attempts >= self.max_auth_attempts:
                    # Get TTL to inform user when they can retry
                    ttl = await redis_client.ttl(key)
                    logger.warning(f"Rate limit exceeded for user (attempts: {attempts})")
                    raise PACERRateLimitError(
                        f"Too many authentication attempts. Please try again in {ttl} seconds."
                    )

            return True

        except PACERRateLimitError:
            raise
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}. Allowing request.")
            return True

    async def _record_auth_attempt(self, username: str, success: bool = False):
        """
        Record authentication attempt for rate limiting.

        Args:
            username: PACER username
            success: Whether authentication was successful
        """
        try:
            redis_client = await self._init_redis()
            if redis_client is None:
                return

            username_hash = self._hash_username(username)
            key = f"pacer:ratelimit:{username_hash}"

            if success:
                # Reset counter on successful authentication
                await redis_client.delete(key)
                logger.debug(f"Reset rate limit counter for user after successful auth")
            else:
                # Increment failed attempt counter
                current = await redis_client.incr(key)
                if current == 1:
                    # Set expiry on first failed attempt
                    await redis_client.expire(key, self.rate_limit_window)
                logger.debug(f"Recorded failed auth attempt (total: {current})")

        except Exception as e:
            logger.warning(f"Failed to record auth attempt: {e}")

    async def _validate_token(self, token: str) -> bool:
        """
        Validate that a cached token is still valid with PACER.

        This makes a lightweight request to PACER to verify token validity.

        Args:
            token: PACER authentication token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Make a lightweight request to validate token
            # Using the PCL API status endpoint or similar
            validate_url = f"{self.base_url}/pcl/pages/status"
            headers = {
                "Cookie": f"nextGenCSO={token}",
                "User-Agent": "PACER-Legal-AI-System/1.0"
            }

            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(validate_url, headers=headers)

                # If we get 401, token is invalid
                if response.status_code == 401:
                    logger.debug("Token validation failed: 401 Unauthorized")
                    return False

                # If we get 200 or 302, token is likely valid
                if response.status_code in (200, 302):
                    logger.debug("Token validation succeeded")
                    return True

                # For other status codes, assume token is valid to avoid false negatives
                logger.debug(f"Token validation returned {response.status_code}, assuming valid")
                return True

        except Exception as e:
            logger.warning(f"Token validation error: {e}. Assuming token is valid.")
            # On error, assume token is valid to avoid unnecessary re-authentication
            return True

    async def authenticate(
        self,
        username: str,
        password: str,
        client_code: Optional[str] = None,
        otp: Optional[str] = None,
        is_filer: bool = False,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Authenticate with PACER and get nextGenCSO token.

        Args:
            username: PACER username
            password: PACER password
            client_code: Optional client code for billing
            otp: Optional one-time password for MFA
            is_filer: Whether user is a filer (requires redaction flag)
            force_refresh: Force new authentication even if cached token exists

        Returns:
            Authentication response with nextGenCSO token

        Raises:
            PACERAuthenticationError: Base exception for auth errors
            PACERMFARequiredError: When MFA is required
            PACERInvalidCredentialsError: When credentials are invalid
            PACERRateLimitError: When rate limit is exceeded
        """
        # Check rate limit first
        await self._check_rate_limit(username)

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_token = await self._get_cached_token(username)
            if cached_token:
                # Validate cached token
                is_valid = await self._validate_token(cached_token)
                if is_valid:
                    sanitized = self._sanitize_for_logging({"username": username})
                    logger.info(f"Using cached token for user: {sanitized['username']}")
                    return {
                        "nextGenCSO": cached_token,
                        "loginResult": "0",  # Consistent with PACER API success code
                        "loginResultCode": "0",
                        "cached": True,
                        "expires_at": None  # Could be enhanced to track expiry
                    }
                else:
                    # Token invalid, remove from cache and continue to re-auth
                    logger.info("Cached token is invalid, re-authenticating")
                    await self.invalidate_token(username)

        # Prepare authentication request
        auth_url = f"{self.base_url}/services/cso-auth"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PACER-Legal-AI-System/1.0"
        }

        payload = {
            "loginId": username,
            "password": password
        }

        if client_code:
            payload["clientCode"] = client_code

        if otp:
            payload["twoFactorCode"] = otp

        if is_filer:
            payload["redactFlag"] = "1"

        # Attempt authentication with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                    response = await client.post(auth_url, json=payload, headers=headers)

                    # Handle specific HTTP errors
                    if response.status_code == 401:
                        # Record failed attempt for invalid credentials
                        await self._record_auth_attempt(username, success=False)
                        raise PACERInvalidCredentialsError("Invalid PACER credentials")
                    elif response.status_code == 429:
                        # Rate limited, wait and retry
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status_code >= 500:
                        # Server error, retry
                        logger.warning(f"Server error (HTTP {response.status_code}), attempt {attempt + 1}/{self.max_retries}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        raise PACERAuthenticationError(f"PACER server error: HTTP {response.status_code}")

                    # Parse JSON response first (before raise_for_status)
                    # so we can extract PACER's error message even on 4xx responses
                    try:
                        data = response.json()
                    except Exception as json_error:
                        # If JSON parsing fails, log the raw response
                        logger.error(f"Failed to parse JSON response. Status: {response.status_code}, Body: {response.text[:500]}")
                        # Let raise_for_status handle it
                        response.raise_for_status()
                        raise PACERAuthenticationError(f"Authentication response not in JSON format: {json_error}")

                    # Log response for debugging
                    logger.info(f"PACER authentication response status: {response.status_code}")
                    logger.debug(f"PACER response data: {self._sanitize_for_logging(data)}")

                    # Handle non-200 responses that still have JSON
                    if response.status_code != 200:
                        error_msg = data.get("errorDescription") or data.get("message") or f"HTTP {response.status_code}"
                        logger.warning(f"Non-200 response from PACER: {response.status_code} - {error_msg}")
                        # Continue to parse loginResult anyway - PACER might still include it

                    # Check login result
                    # IMPORTANT: PACER API returns "0" for success, not "success"
                    # Handle both string "0", integer 0, and None
                    raw_login_result = data.get("loginResult")
                    if raw_login_result is None:
                        login_result = ""
                    else:
                        login_result = str(raw_login_result).strip()

                    error_desc = data.get("errorDescription", "")
                    if error_desc:
                        error_desc = str(error_desc).strip()
                    else:
                        error_desc = ""

                    # Log the raw response for debugging
                    logger.debug(f"PACER response: HTTP {response.status_code}, loginResult='{login_result}' (type: {type(raw_login_result).__name__}), errorDescription='{error_desc}', has_token={bool(data.get('nextGenCSO'))}")

                    # SUCCESS: loginResult == "0"
                    if login_result == "0":
                        token = data.get("nextGenCSO")
                        if not token:
                            raise PACERAuthenticationError("Authentication succeeded but no token received")

                        # Check for warnings (e.g., missing client code)
                        if error_desc:
                            sanitized = self._sanitize_for_logging({"username": username})
                            logger.warning(
                                f"Authentication succeeded with warning for {sanitized['username']}: {error_desc}"
                            )
                            # Common warning: "Client code required for search privileges"
                            # User is authenticated but may have limited functionality

                        # Cache token for reuse
                        await self._cache_token(username, token)

                        # Record successful authentication
                        await self._record_auth_attempt(username, success=True)

                        sanitized = self._sanitize_for_logging({"username": username})
                        logger.info(f"Successfully authenticated user: {sanitized['username']}")

                        return {
                            "nextGenCSO": token,
                            "loginResult": "0",
                            "loginResultCode": login_result,
                            "warning": error_desc if error_desc else None,
                            "cached": False,
                            "username": username,
                            "environment": self.env,
                            "timestamp": datetime.utcnow().isoformat()
                        }

                    # MFA Required (special case - could be specific code or keyword)
                    elif "twoFactor" in data or "MFA" in error_desc or "one-time" in error_desc:
                        # Don't record as failed attempt - MFA is a normal part of flow
                        raise PACERMFARequiredError("Multi-factor authentication required")

                    # FAILURE: Any non-zero loginResult (or missing loginResult)
                    else:
                        # Record failed attempt
                        await self._record_auth_attempt(username, success=False)

                        # Extract error message from PACER response
                        if not error_desc:
                            error_desc = (
                                data.get("message") or
                                data.get("error") or
                                "Unknown authentication error"
                            )

                        # Handle special cases
                        if not login_result:
                            # Missing loginResult entirely
                            error_message = f"PACER API error: No loginResult in response. {error_desc}"
                        elif login_result == "0":
                            # This should never happen (we check for "0" above)
                            # but just in case there's a type issue
                            error_message = f"PACER API returned success code but failed. Token missing? Error: {error_desc}"
                        else:
                            # Non-zero failure code
                            # Common failure codes:
                            # "13" = Invalid username/password/OTP
                            # Non-zero with redaction error = Registered filer missing redactFlag
                            # Non-zero with Service Center message = Disabled account
                            error_message = f"PACER authentication failed (code {login_result}): {error_desc}"

                        logger.error(f"PACER authentication failed: loginResult='{login_result}', error='{error_desc}'")
                        raise PACERAuthenticationError(error_message)

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Authentication timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            except httpx.NetworkError as e:
                last_error = e
                logger.warning(f"Network error during authentication, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            except (PACERAuthenticationError, PACERMFARequiredError, PACERInvalidCredentialsError, PACERRateLimitError):
                # Don't retry on these specific errors
                raise

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during authentication: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

        # All retries failed
        raise PACERAuthenticationError(f"Authentication failed after {self.max_retries} attempts: {last_error}")

    async def _cache_token(self, username: str, token: str):
        """Cache authentication token securely in Redis"""
        if not self.cache_enabled:
            return

        try:
            redis_client = await self._init_redis()
            if redis_client is None:
                return

            # Hash username for privacy
            username_hash = self._hash_username(username)

            # Encrypt token before caching
            encrypted_token = self.fernet.encrypt(token.encode())
            key = f"pacer:token:{username_hash}"

            # Cache with TTL
            await redis_client.setex(key, self.cache_ttl, encrypted_token)
            sanitized = self._sanitize_for_logging({"username": username})
            logger.debug(f"Cached token for {sanitized['username']} (TTL: {self.cache_ttl}s)")

        except Exception as e:
            logger.warning(f"Failed to cache token: {e}")
            # Don't fail authentication if caching fails

    async def _get_cached_token(self, username: str) -> Optional[str]:
        """Retrieve cached token if available"""
        if not self.cache_enabled:
            return None

        try:
            redis_client = await self._init_redis()
            if redis_client is None:
                return None

            # Hash username for privacy
            username_hash = self._hash_username(username)
            key = f"pacer:token:{username_hash}"
            encrypted_token = await redis_client.get(key)

            if encrypted_token:
                try:
                    # Decrypt token
                    token = self.fernet.decrypt(encrypted_token).decode()
                    sanitized = self._sanitize_for_logging({"username": username})
                    logger.debug(f"Retrieved cached token for {sanitized['username']}")
                    return token
                except Exception as e:
                    # Invalid/corrupted token, remove from cache
                    logger.warning(f"Failed to decrypt cached token: {e}")
                    await redis_client.delete(key)

        except Exception as e:
            logger.warning(f"Failed to retrieve cached token: {e}")

        return None

    async def invalidate_token(self, username: str):
        """Invalidate (remove) cached token for a user"""
        if not self.cache_enabled:
            return

        try:
            redis_client = await self._init_redis()
            if redis_client is None:
                return

            # Hash username for privacy
            username_hash = self._hash_username(username)
            key = f"pacer:token:{username_hash}"
            await redis_client.delete(key)

            sanitized = self._sanitize_for_logging({"username": username})
            logger.info(f"Invalidated token for {sanitized['username']}")

        except Exception as e:
            logger.warning(f"Failed to invalidate token: {e}")

    async def refresh_token(self, username: str, password: str, **kwargs):
        """Force token refresh (invalidate cache and re-authenticate)"""
        await self.invalidate_token(username)
        return await self.authenticate(username, password, force_refresh=True, **kwargs)

    async def close(self):
        """Close Redis connection and cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")


# Example usage and testing
async def main():
    """Test PACER authentication"""
    import os

    # Load credentials from environment
    username = os.getenv("PACER_USERNAME")
    password = os.getenv("PACER_PASSWORD")

    if not username or not password:
        print("❌ PACER_USERNAME and PACER_PASSWORD must be set in environment")
        print("   Set them in .env file")
        return

    authenticator = PACERAuthenticator(environment="production")

    try:
        print(f"🔐 Authenticating with PACER as {username}...")
        result = await authenticator.authenticate(username, password)

        print("✅ Authentication successful!")
        print(f"   Token: {result['nextGenCSO'][:20]}...")
        print(f"   Cached: {result.get('cached', False)}")
        print(f"   Environment: {result.get('environment')}")

        # Test cached token
        print("\n🔄 Testing cached token retrieval...")
        cached_result = await authenticator.authenticate(username, password)
        print(f"✅ Token retrieved from cache: {cached_result.get('cached', False)}")

    except PACERMFARequiredError:
        print("⚠️  MFA/OTP required - Please provide one-time password")
    except PACERInvalidCredentialsError:
        print("❌ Invalid credentials")
    except PACERAuthenticationError as e:
        print(f"❌ Authentication error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        await authenticator.close()


if __name__ == "__main__":
    asyncio.run(main())
# Force reload
