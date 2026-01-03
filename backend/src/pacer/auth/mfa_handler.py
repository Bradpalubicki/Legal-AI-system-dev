# -*- coding: utf-8 -*-
"""
PACER MFA/OTP Handler

Handles multi-factor authentication for PACER accounts including:
- OTP code collection
- TOTP generation (if configured)
- MFA retry logic
- User prompts for OTP codes
"""

import logging
from typing import Optional, Callable
import asyncio
from datetime import datetime, timedelta
import pyotp  # For TOTP support (optional dependency)

logger = logging.getLogger(__name__)


class MFAHandler:
    """
    Handles multi-factor authentication for PACER.

    Supports multiple MFA methods:
    - Manual OTP entry (user-provided codes)
    - TOTP from saved secrets
    - Callback functions for custom OTP retrieval
    """

    def __init__(self):
        """Initialize MFA handler"""
        self.totp_secrets: dict[str, str] = {}  # username -> TOTP secret
        self.otp_callback: Optional[Callable] = None

    def set_totp_secret(self, username: str, secret: str):
        """
        Configure TOTP secret for automatic code generation.

        Args:
            username: PACER username
            secret: TOTP secret key (base32 encoded)

        Warning:
            Storing TOTP secrets should be done securely with encryption
        """
        self.totp_secrets[username] = secret
        logger.info(f"TOTP secret configured for {username}")

    def set_otp_callback(self, callback: Callable[[str], str]):
        """
        Set callback function for OTP retrieval.

        Args:
            callback: Function that takes username and returns OTP code
        """
        self.otp_callback = callback
        logger.info("OTP callback configured")

    async def get_otp_code(self, username: str) -> Optional[str]:
        """
        Get OTP code for user authentication.

        Tries multiple methods in order:
        1. TOTP from saved secret
        2. Custom callback function
        3. User prompt (console input)

        Args:
            username: PACER username

        Returns:
            OTP code or None if unavailable
        """
        # Try TOTP first
        if username in self.totp_secrets:
            try:
                code = self._generate_totp(username)
                if code:
                    logger.info(f"Generated TOTP code for {username}")
                    return code
            except Exception as e:
                logger.warning(f"TOTP generation failed: {e}")

        # Try callback
        if self.otp_callback:
            try:
                code = self.otp_callback(username)
                if code:
                    logger.info(f"Retrieved OTP via callback for {username}")
                    return code
            except Exception as e:
                logger.warning(f"OTP callback failed: {e}")

        # Fall back to user prompt
        return await self._prompt_for_otp(username)

    def _generate_totp(self, username: str) -> Optional[str]:
        """
        Generate TOTP code from saved secret.

        Args:
            username: PACER username

        Returns:
            6-digit TOTP code
        """
        secret = self.totp_secrets.get(username)
        if not secret:
            return None

        try:
            totp = pyotp.TOTP(secret)
            code = totp.now()
            return code
        except Exception as e:
            logger.error(f"Error generating TOTP: {e}")
            return None

    async def _prompt_for_otp(self, username: str) -> Optional[str]:
        """
        Prompt user for OTP code via console input.

        Args:
            username: PACER username

        Returns:
            User-provided OTP code
        """
        try:
            print(f"\n🔐 Multi-factor authentication required for {username}")
            print("   Please enter your one-time password (OTP):")

            # Use asyncio to read from stdin
            loop = asyncio.get_event_loop()
            code = await loop.run_in_executor(None, input, "   OTP Code: ")

            code = code.strip()

            if code and len(code) >= 6:
                return code
            else:
                logger.warning("Invalid OTP code provided")
                return None

        except Exception as e:
            logger.error(f"Error prompting for OTP: {e}")
            return None

    async def authenticate_with_mfa(
        self,
        authenticator,
        username: str,
        password: str,
        max_attempts: int = 3,
        **kwargs
    ):
        """
        Authenticate with MFA, retrying if OTP is incorrect.

        Args:
            authenticator: PACERAuthenticator instance
            username: PACER username
            password: PACER password
            max_attempts: Maximum OTP attempts
            **kwargs: Additional args passed to authenticate()

        Returns:
            Authentication result

        Raises:
            PACERAuthenticationError: If authentication fails after max attempts
        """
        from .authenticator import PACERMFARequiredError, PACERAuthenticationError

        for attempt in range(max_attempts):
            try:
                # First attempt without OTP
                if attempt == 0:
                    try:
                        result = await authenticator.authenticate(
                            username=username,
                            password=password,
                            **kwargs
                        )
                        return result
                    except PACERMFARequiredError:
                        logger.info("MFA required, getting OTP code")

                # Get OTP code
                otp = await self.get_otp_code(username)

                if not otp:
                    logger.warning(f"No OTP code available, attempt {attempt + 1}/{max_attempts}")
                    continue

                # Attempt authentication with OTP
                result = await authenticator.authenticate(
                    username=username,
                    password=password,
                    otp=otp,
                    **kwargs
                )

                logger.info(f"MFA authentication successful for {username}")
                return result

            except PACERMFARequiredError:
                logger.warning(f"Incorrect OTP code, attempt {attempt + 1}/{max_attempts}")
                if attempt < max_attempts - 1:
                    print("   ❌ Incorrect code. Please try again.")
                    continue
                else:
                    raise PACERAuthenticationError("MFA failed after max attempts")

            except PACERAuthenticationError:
                # Other auth errors, don't retry
                raise

        raise PACERAuthenticationError("MFA authentication failed")

    def remove_totp_secret(self, username: str):
        """Remove saved TOTP secret for user"""
        if username in self.totp_secrets:
            del self.totp_secrets[username]
            logger.info(f"Removed TOTP secret for {username}")


# Example usage
async def main():
    """Test MFA handler"""
    handler = MFAHandler()

    # Example: Set a custom OTP callback
    def my_otp_callback(username: str) -> str:
        # In production, this might fetch from a secure vault
        print(f"Custom callback: Getting OTP for {username}")
        return "123456"  # Example code

    handler.set_otp_callback(my_otp_callback)

    # Test getting OTP
    code = await handler.get_otp_code("testuser")
    print(f"✅ Retrieved OTP code: {code}")


if __name__ == "__main__":
    asyncio.run(main())
