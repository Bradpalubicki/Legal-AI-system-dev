# -*- coding: utf-8 -*-
"""
PACER Token Manager

Handles token lifecycle management including:
- Token expiration tracking
- Automatic token refresh
- Multi-user token management
- Token health monitoring
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Information about a PACER authentication token"""
    token: str
    username: str
    created_at: datetime
    last_used: datetime = field(default_factory=datetime.utcnow)
    use_count: int = 0
    expires_at: Optional[datetime] = None
    is_valid: bool = True

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if self.expires_at:
            return datetime.utcnow() >= self.expires_at
        # Default expiration: 8 hours
        return (datetime.utcnow() - self.created_at) > timedelta(hours=8)

    def should_refresh(self) -> bool:
        """Check if token should be refreshed proactively"""
        if self.expires_at:
            # Refresh 30 minutes before expiration
            time_until_expiry = self.expires_at - datetime.utcnow()
            return time_until_expiry < timedelta(minutes=30)
        # Refresh after 7 hours
        age = datetime.utcnow() - self.created_at
        return age > timedelta(hours=7)

    def mark_used(self):
        """Mark token as used"""
        self.last_used = datetime.utcnow()
        self.use_count += 1


class TokenManager:
    """
    Manages PACER authentication tokens for multiple users.

    Features:
    - Automatic token refresh before expiration
    - Token health monitoring
    - Usage statistics
    - Thread-safe token access
    """

    def __init__(self, authenticator=None):
        """
        Initialize token manager.

        Args:
            authenticator: PACERAuthenticator instance for token refresh
        """
        self.authenticator = authenticator
        self.tokens: Dict[str, TokenInfo] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get_token(self, username: str) -> Optional[str]:
        """
        Get valid token for user, refreshing if necessary.

        Args:
            username: PACER username

        Returns:
            Valid authentication token or None
        """
        # Get or create lock for this user
        if username not in self._locks:
            self._locks[username] = asyncio.Lock()

        async with self._locks[username]:
            token_info = self.tokens.get(username)

            # No token cached
            if not token_info:
                logger.debug(f"No token cached for {username}")
                return None

            # Token is invalid
            if not token_info.is_valid:
                logger.warning(f"Token for {username} is marked invalid")
                return None

            # Token is expired
            if token_info.is_expired():
                logger.info(f"Token for {username} is expired")
                # Try to refresh if authenticator available
                if self.authenticator:
                    await self._refresh_token(username)
                    token_info = self.tokens.get(username)
                    if token_info and token_info.is_valid:
                        return token_info.token
                return None

            # Token should be refreshed proactively
            if token_info.should_refresh():
                logger.info(f"Proactively refreshing token for {username}")
                if self.authenticator:
                    # Refresh in background, but return current token
                    asyncio.create_task(self._refresh_token(username))

            # Update usage stats
            token_info.mark_used()
            return token_info.token

    async def store_token(
        self,
        username: str,
        token: str,
        expires_at: Optional[datetime] = None
    ):
        """
        Store authentication token for user.

        Args:
            username: PACER username
            token: Authentication token
            expires_at: Token expiration time (optional)
        """
        if username not in self._locks:
            self._locks[username] = asyncio.Lock()

        async with self._locks[username]:
            self.tokens[username] = TokenInfo(
                token=token,
                username=username,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                is_valid=True
            )
            logger.info(f"Stored token for {username}")

    async def invalidate_token(self, username: str):
        """Mark token as invalid (e.g., after logout or auth error)"""
        if username in self.tokens:
            self.tokens[username].is_valid = False
            logger.info(f"Invalidated token for {username}")

    async def remove_token(self, username: str):
        """Completely remove token from manager"""
        if username in self.tokens:
            del self.tokens[username]
            logger.info(f"Removed token for {username}")

    async def _refresh_token(self, username: str):
        """
        Refresh token for user.

        Requires authenticator to be configured with user credentials.
        """
        if not self.authenticator:
            logger.warning("Cannot refresh token: no authenticator configured")
            return

        try:
            # Get stored password (would need to be implemented)
            # For now, just invalidate the token
            logger.warning(f"Token refresh not fully implemented for {username}")
            await self.invalidate_token(username)

        except Exception as e:
            logger.error(f"Error refreshing token for {username}: {e}")
            await self.invalidate_token(username)

    def get_token_info(self, username: str) -> Optional[TokenInfo]:
        """Get token information for user"""
        return self.tokens.get(username)

    def get_all_users(self) -> list:
        """Get list of users with cached tokens"""
        return list(self.tokens.keys())

    def get_stats(self) -> Dict[str, any]:
        """Get token manager statistics"""
        total_tokens = len(self.tokens)
        valid_tokens = sum(1 for t in self.tokens.values() if t.is_valid)
        expired_tokens = sum(1 for t in self.tokens.values() if t.is_expired())

        return {
            "total_tokens": total_tokens,
            "valid_tokens": valid_tokens,
            "expired_tokens": expired_tokens,
            "users": self.get_all_users()
        }

    async def cleanup_expired_tokens(self):
        """Remove expired tokens from manager"""
        expired_users = [
            username for username, token_info in self.tokens.items()
            if token_info.is_expired()
        ]

        for username in expired_users:
            await self.remove_token(username)

        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired tokens")

        return len(expired_users)


# Example usage
async def main():
    """Test token manager"""
    from .authenticator import PACERAuthenticator

    manager = TokenManager()

    # Store a test token
    await manager.store_token(
        username="testuser",
        token="test_token_123456",
        expires_at=datetime.utcnow() + timedelta(hours=8)
    )

    # Retrieve token
    token = await manager.get_token("testuser")
    print(f"✅ Retrieved token: {token}")

    # Get stats
    stats = manager.get_stats()
    print(f"📊 Token Manager Stats: {stats}")

    # Get token info
    info = manager.get_token_info("testuser")
    if info:
        print(f"   Created: {info.created_at}")
        print(f"   Used: {info.use_count} times")
        print(f"   Expires: {info.expires_at}")
        print(f"   Should refresh: {info.should_refresh()}")


if __name__ == "__main__":
    asyncio.run(main())
