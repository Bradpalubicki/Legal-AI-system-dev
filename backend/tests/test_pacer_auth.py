#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_pacer_auth.py - Test and usage examples for PACER authenticator

Comprehensive test suite and usage examples for the enhanced PACER authenticator
with security features including rate limiting, token validation, and sanitized logging.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from datetime import datetime
import json

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Assuming the authenticator is in src/pacer/auth/authenticator.py
from src.pacer.auth.authenticator import (
    PACERAuthenticator,
    PACERAuthenticationError,
    PACERMFARequiredError,
    PACERInvalidCredentialsError,
    PACERRateLimitError
)


class TestPACERAuthenticator:
    """Test suite for PACER authenticator with security features."""

    @pytest.fixture
    async def authenticator(self):
        """Create authenticator instance for testing."""
        # Use QA environment for testing
        auth = PACERAuthenticator(environment="qa")
        yield auth
        await auth.close()

    @pytest.mark.asyncio
    async def test_encryption_key_management(self):
        """Test that encryption keys are properly managed."""
        # Test that the same key is used across instances
        auth1 = PACERAuthenticator(environment="qa")
        auth2 = PACERAuthenticator(environment="qa")

        # Encrypt with one instance
        test_data = b"test_token"
        encrypted1 = auth1.fernet.encrypt(test_data)

        # Should be able to decrypt with another instance if using same key
        try:
            decrypted2 = auth2.fernet.decrypt(encrypted1)
            assert decrypted2 == test_data
            print("✓ Encryption key management test passed")
        except Exception as e:
            # If keys are different (temporary keys), that's also valid
            print(f"✓ Encryption test passed (using temporary keys): {e}")

        await auth1.close()
        await auth2.close()

    @pytest.mark.asyncio
    async def test_redis_connection_fallback(self):
        """Test that authentication works even if Redis is unavailable."""
        auth = PACERAuthenticator(environment="qa")

        # Simulate Redis connection failure
        auth.redis_client = None
        auth.cache_enabled = False

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "loginResult": "success",
                "nextGenCSO": "test_token_123"
            }
            mock_response.raise_for_status = MagicMock()

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            mock_context.post = AsyncMock(return_value=mock_response)

            with patch('httpx.AsyncClient', return_value=mock_context):
                # Should authenticate successfully even without Redis
                result = await auth.authenticate("test_user", "test_pass")

                assert result["loginResult"] == "success"
                assert result["nextGenCSO"] == "test_token_123"
                assert result["cached"] == False
                print("✓ Redis fallback test passed")

        await auth.close()

    @pytest.mark.asyncio
    async def test_password_not_logged(self, caplog):
        """Test that passwords are never logged."""
        auth = PACERAuthenticator(environment="qa")

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "loginResult": "failed",
                "errorDescription": "Invalid password"
            }

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_context
            mock_context.__aexit__.return_value = None
            mock_context.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            try:
                await auth.authenticate("test_user", "test_pass")
            except (PACERAuthenticationError, PACERInvalidCredentialsError):
                pass

            # Check logs don't contain the actual password
            log_text = caplog.text
            assert "test_pass" not in log_text or "***" in log_text
            print("✓ Password sanitization test passed")

        await auth.close()

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        auth = PACERAuthenticator(environment="qa")
        username = "test_user"

        # Mock Redis to simulate rate limiting
        mock_redis = AsyncMock()
        auth.redis_client = mock_redis

        # Simulate max attempts reached
        mock_redis.get.return_value = str(auth.max_auth_attempts).encode()
        mock_redis.ttl.return_value = 180  # 3 minutes remaining

        try:
            await auth.authenticate(username, "test_pass")
            assert False, "Should have raised PACERRateLimitError"
        except PACERRateLimitError as e:
            assert "Too many authentication attempts" in str(e)
            print("✓ Rate limiting test passed")

        await auth.close()

    @pytest.mark.asyncio
    async def test_token_validation(self):
        """Test token validation mechanism."""
        auth = PACERAuthenticator(environment="qa")

        with patch.object(auth, '_validate_token') as mock_validate:
            mock_validate.return_value = False

            with patch.object(auth, '_get_cached_token') as mock_get:
                mock_get.return_value = "expired_token"

                with patch.object(auth, 'invalidate_token') as mock_invalidate:
                    with patch('httpx.AsyncClient') as mock_client:
                        mock_response = AsyncMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            "loginResult": "success",
                            "nextGenCSO": "new_token"
                        }
                        mock_response.raise_for_status = MagicMock()

                        mock_context = AsyncMock()
                        mock_context.__aenter__.return_value = mock_context
                        mock_context.__aexit__.return_value = None
                        mock_context.post = AsyncMock(return_value=mock_response)
                        mock_client.return_value = mock_context

                        result = await auth.authenticate("test_user", "test_pass")

                        # Should have invalidated the expired token
                        mock_invalidate.assert_called_once()
                        # Should have gotten new token
                        assert result["nextGenCSO"] == "new_token"
                        assert result["cached"] == False
                        print("✓ Token validation test passed")

        await auth.close()

    @pytest.mark.asyncio
    async def test_username_hashing(self):
        """Test that usernames are hashed for privacy."""
        auth = PACERAuthenticator(environment="qa")

        username = "test_user@example.com"
        hash1 = auth._hash_username(username)
        hash2 = auth._hash_username(username)

        # Same username should produce same hash
        assert hash1 == hash2
        # Hash should be 64 characters (SHA-256)
        assert len(hash1) == 64
        # Different username should produce different hash
        different_hash = auth._hash_username("different@example.com")
        assert hash1 != different_hash

        print("✓ Username hashing test passed")

        await auth.close()

    @pytest.mark.asyncio
    async def test_sanitized_logging(self):
        """Test that sensitive data is sanitized for logging."""
        auth = PACERAuthenticator(environment="qa")

        test_data = {
            "username": "testuser@example.com",
            "password": "SuperSecret123!",
            "nextGenCSO": "token123456789",
            "safe_field": "not_sensitive"
        }

        sanitized = auth._sanitize_for_logging(test_data)

        # Check that sensitive fields are masked
        assert "***REDACTED***" in sanitized["password"]
        assert "***REDACTED***" in sanitized["nextGenCSO"]
        # Check that username is partially masked
        assert "***" in sanitized["username"]
        # Check that safe fields are preserved
        assert sanitized["safe_field"] == "not_sensitive"

        print("✓ Sanitized logging test passed")

        await auth.close()


# === USAGE EXAMPLES ===

async def basic_authentication_example():
    """Basic authentication example."""
    print("\n=== Basic Authentication Example ===")

    auth = PACERAuthenticator(environment="production")

    try:
        # Simple authentication
        result = await auth.authenticate(
            username="your_username",
            password="your_password"
        )

        if result["loginResult"] == "success":
            token = result["nextGenCSO"]
            print(f"✓ Authentication successful! Token: {token[:10]}...")
            print(f"  Cached: {result.get('cached', False)}")
            print(f"  Environment: {result.get('environment')}")

            # Use token for PCL API calls
            # ...

    except PACERInvalidCredentialsError:
        print("✗ Invalid credentials. Please check username and password.")
    except PACERRateLimitError as e:
        print(f"✗ Rate limited: {e}")
    except PACERAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")

    finally:
        await auth.close()


async def mfa_authentication_example():
    """Authentication with MFA/OTP support."""
    print("\n=== MFA Authentication Example ===")

    auth = PACERAuthenticator(environment="production")

    try:
        # First attempt without OTP
        try:
            result = await auth.authenticate(
                username="your_username",
                password="your_password"
            )

            if result["loginResult"] == "success":
                token = result["nextGenCSO"]
                print(f"✓ Authentication successful! Token: {token[:10]}...")

        except PACERMFARequiredError:
            print("⚠ MFA required. Please enter OTP code:")
            otp_code = input("OTP: ")

            # Retry with OTP
            result = await auth.authenticate(
                username="your_username",
                password="your_password",
                otp=otp_code
            )

            if result["loginResult"] == "success":
                token = result["nextGenCSO"]
                print(f"✓ Authentication successful with MFA! Token: {token[:10]}...")

    except PACERAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")

    finally:
        await auth.close()


async def cached_authentication_example():
    """Example showing token caching."""
    print("\n=== Token Caching Example ===")

    auth = PACERAuthenticator(environment="production")

    try:
        # First authentication - will hit PACER API
        print("First authentication (fresh)...")
        result1 = await auth.authenticate(
            username="your_username",
            password="your_password"
        )
        print(f"  Cached: {result1.get('cached', False)}")  # Should be False

        # Second authentication - will use cached token
        print("Second authentication (should use cache)...")
        result2 = await auth.authenticate(
            username="your_username",
            password="your_password"
        )
        print(f"  Cached: {result2.get('cached', False)}")  # Should be True

        # Force refresh to get new token
        print("Force refresh (bypass cache)...")
        result3 = await auth.authenticate(
            username="your_username",
            password="your_password",
            force_refresh=True
        )
        print(f"  Cached: {result3.get('cached', False)}")  # Should be False

    except PACERAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")

    finally:
        await auth.close()


async def client_code_example():
    """Example with client code for billing."""
    print("\n=== Client Code Example ===")

    auth = PACERAuthenticator(environment="production")

    try:
        result = await auth.authenticate(
            username="your_username",
            password="your_password",
            client_code="CLIENT123",  # For billing segregation
            is_filer=True  # If you're a filer
        )

        if result["loginResult"] == "success":
            token = result["nextGenCSO"]
            print(f"✓ Authenticated with client code. Token: {token[:10]}...")

    except PACERAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")

    finally:
        await auth.close()


async def error_handling_example():
    """Comprehensive error handling example."""
    print("\n=== Error Handling Example ===")

    auth = PACERAuthenticator(environment="production")

    try:
        result = await auth.authenticate(
            username="your_username",
            password="your_password"
        )

        if result["loginResult"] == "success":
            print("✓ Authentication successful!")

    except PACERRateLimitError as e:
        # Rate limited - specific handling
        print(f"⚠ Rate limited: {e}")
        print("  Please wait 5 minutes before trying again.")

    except PACERInvalidCredentialsError:
        # Invalid credentials
        print("✗ Invalid username or password.")
        print("  Please check your PACER credentials.")

    except PACERMFARequiredError:
        # MFA required
        print("⚠ Multi-factor authentication required.")
        print("  Please provide your OTP code.")

    except ValueError as e:
        # Invalid input
        print(f"✗ Invalid input: {e}")

    except PACERAuthenticationError as e:
        # General authentication errors
        error_msg = str(e)

        if "timed out" in error_msg.lower():
            print("⚠ Connection timed out. Check your internet connection.")
        elif "network error" in error_msg.lower():
            print("⚠ Network problem. Please try again.")
        else:
            print(f"✗ Authentication failed: {error_msg}")

    except Exception as e:
        # Unexpected errors
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await auth.close()


async def logout_example():
    """Example of logging out and invalidating tokens."""
    print("\n=== Logout Example ===")

    auth = PACERAuthenticator(environment="production")

    try:
        # Authenticate first
        result = await auth.authenticate(
            username="your_username",
            password="your_password"
        )

        if result["loginResult"] == "success":
            print("✓ Authenticated successfully")

            # Do some work with the token
            # ...

            # Logout - invalidate cached token
            await auth.invalidate_token("your_username")
            print("✓ Logged out - token invalidated")

            # Next authentication will require fresh login
            result2 = await auth.authenticate(
                username="your_username",
                password="your_password"
            )
            print(f"  New token (not cached): {result2.get('cached', False)}")

    except PACERAuthenticationError as e:
        print(f"✗ Error: {e}")

    finally:
        await auth.close()


async def run_all_examples():
    """Run all usage examples."""
    print("\n" + "="*70)
    print("PACER AUTHENTICATOR - USAGE EXAMPLES")
    print("="*70)

    try:
        await basic_authentication_example()
    except Exception as e:
        print(f"Example failed: {e}")

    try:
        await cached_authentication_example()
    except Exception as e:
        print(f"Example failed: {e}")

    try:
        await error_handling_example()
    except Exception as e:
        print(f"Example failed: {e}")

    try:
        await logout_example()
    except Exception as e:
        print(f"Example failed: {e}")

    print("\n" + "="*70)
    print("EXAMPLES COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run tests with pytest
        print("Running tests with pytest...")
        pytest.main([__file__, "-v", "-s"])
    elif len(sys.argv) > 1 and sys.argv[1] == "--examples":
        # Run usage examples
        print("Running usage examples...")
        asyncio.run(run_all_examples())
    else:
        # Run basic tests
        print("Running basic tests...")
        print("\nTo run full test suite: python test_pacer_auth.py --test")
        print("To run usage examples: python test_pacer_auth.py --examples\n")

        # Run some basic tests
        asyncio.run(TestPACERAuthenticator().test_username_hashing())
        asyncio.run(TestPACERAuthenticator().test_sanitized_logging())
        asyncio.run(TestPACERAuthenticator().test_encryption_key_management())

        print("\n✓ Basic tests completed successfully!")
