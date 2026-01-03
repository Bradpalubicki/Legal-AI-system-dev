"""
TLS/SSL Configuration

Secure configuration for HTTPS, database connections, and external services.
Ensures data is encrypted in transit.
"""

import os
import ssl
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# TLS/SSL CONSTANTS
# =============================================================================

# Minimum TLS version (TLS 1.2 or higher)
MIN_TLS_VERSION = ssl.TLSVersion.TLSv1_2

# Recommended cipher suites (secure, no weak ciphers)
RECOMMENDED_CIPHERS = [
    # TLS 1.3 ciphers (preferred)
    'TLS_AES_256_GCM_SHA384',
    'TLS_CHACHA20_POLY1305_SHA256',
    'TLS_AES_128_GCM_SHA256',

    # TLS 1.2 ciphers (fallback)
    'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-RSA-CHACHA20-POLY1305',
    'DHE-RSA-AES256-GCM-SHA384',
    'DHE-RSA-AES128-GCM-SHA256',
]

# OpenSSL cipher string
CIPHER_STRING = ':'.join(RECOMMENDED_CIPHERS)

# Excluded weak ciphers
EXCLUDED_CIPHERS = [
    'RC4',
    'MD5',
    'DES',
    '3DES',
    'NULL',
    'EXPORT',
    'anon',
]


# =============================================================================
# SSL CONTEXT CREATION
# =============================================================================

def create_ssl_context(
    purpose: ssl.Purpose = ssl.Purpose.CLIENT_AUTH,
    certfile: Optional[str] = None,
    keyfile: Optional[str] = None,
    cafile: Optional[str] = None,
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED,
    check_hostname: bool = True,
) -> ssl.SSLContext:
    """
    Create secure SSL context with strong security settings.

    Args:
        purpose: SSL purpose (CLIENT_AUTH for servers, SERVER_AUTH for clients)
        certfile: Path to SSL certificate file
        keyfile: Path to SSL private key file
        cafile: Path to CA certificate bundle
        verify_mode: Certificate verification mode
        check_hostname: Whether to verify hostname

    Returns:
        Configured SSL context
    """
    # Create context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    # Set minimum TLS version (TLS 1.2+)
    context.minimum_version = MIN_TLS_VERSION

    # Set strong cipher suites
    try:
        context.set_ciphers(CIPHER_STRING)
    except ssl.SSLError as e:
        logger.warning(f"Could not set custom ciphers: {e}. Using defaults.")

    # Load certificate and key for servers
    if certfile and keyfile:
        try:
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            logger.info(f"Loaded SSL certificate from {certfile}")
        except Exception as e:
            logger.error(f"Error loading SSL certificate: {e}")
            raise

    # Load CA certificates
    if cafile:
        try:
            context.load_verify_locations(cafile=cafile)
            logger.info(f"Loaded CA certificates from {cafile}")
        except Exception as e:
            logger.error(f"Error loading CA certificates: {e}")
            raise

    # Set verification mode
    context.verify_mode = verify_mode
    context.check_hostname = check_hostname

    # Additional security options
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    context.options |= ssl.OP_NO_COMPRESSION  # Prevent CRIME attack
    context.options |= ssl.OP_SINGLE_DH_USE
    context.options |= ssl.OP_SINGLE_ECDH_USE

    return context


def create_server_ssl_context(
    certfile: Optional[str] = None,
    keyfile: Optional[str] = None,
) -> ssl.SSLContext:
    """
    Create SSL context for HTTPS server (FastAPI/Uvicorn).

    Args:
        certfile: Path to SSL certificate
        keyfile: Path to SSL private key

    Returns:
        SSL context for server
    """
    # Get cert paths from environment if not provided
    certfile = certfile or os.getenv('SSL_CERTFILE')
    keyfile = keyfile or os.getenv('SSL_KEYFILE')

    if not certfile or not keyfile:
        logger.warning(
            "No SSL certificate provided. Server will run without HTTPS. "
            "Set SSL_CERTFILE and SSL_KEYFILE environment variables."
        )
        return None

    return create_ssl_context(
        purpose=ssl.Purpose.CLIENT_AUTH,
        certfile=certfile,
        keyfile=keyfile,
        verify_mode=ssl.CERT_NONE,  # Server doesn't verify clients
        check_hostname=False,
    )


def create_client_ssl_context(
    cafile: Optional[str] = None,
    verify: bool = True,
) -> ssl.SSLContext:
    """
    Create SSL context for HTTPS client (requests, httpx).

    Args:
        cafile: Path to CA certificate bundle
        verify: Whether to verify server certificates

    Returns:
        SSL context for client
    """
    if not verify:
        logger.warning("SSL verification disabled. This is insecure!")

    return create_ssl_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=cafile,
        verify_mode=ssl.CERT_REQUIRED if verify else ssl.CERT_NONE,
        check_hostname=verify,
    )


# =============================================================================
# DATABASE SSL CONFIGURATION
# =============================================================================

def get_database_ssl_config() -> Dict[str, Any]:
    """
    Get SSL configuration for database connections (PostgreSQL).

    Returns:
        Dictionary with SSL parameters for SQLAlchemy
    """
    ssl_mode = os.getenv('DATABASE_SSL_MODE', 'prefer')

    if ssl_mode == 'disable':
        logger.warning("Database SSL disabled. Connection is not encrypted!")
        return {}

    elif ssl_mode == 'require':
        # Require SSL but don't verify certificate
        return {
            'ssl': True,
            'ssl_require': True,
        }

    elif ssl_mode == 'verify-ca':
        # Require SSL and verify CA certificate
        ca_file = os.getenv('DATABASE_SSL_CA')
        if not ca_file:
            logger.error("DATABASE_SSL_CA not set for verify-ca mode")
            raise ValueError("DATABASE_SSL_CA required for verify-ca mode")

        return {
            'ssl': True,
            'ssl_require': True,
            'ssl_ca': ca_file,
        }

    elif ssl_mode == 'verify-full':
        # Require SSL, verify CA, and verify hostname
        ca_file = os.getenv('DATABASE_SSL_CA')
        if not ca_file:
            logger.error("DATABASE_SSL_CA not set for verify-full mode")
            raise ValueError("DATABASE_SSL_CA required for verify-full mode")

        return {
            'ssl': True,
            'ssl_require': True,
            'ssl_ca': ca_file,
            'ssl_check_hostname': True,
        }

    else:
        # prefer (default) - try SSL but allow fallback
        return {
            'ssl': True,
        }


# =============================================================================
# REDIS SSL CONFIGURATION
# =============================================================================

def get_redis_ssl_config() -> Dict[str, Any]:
    """
    Get SSL configuration for Redis connections.

    Returns:
        Dictionary with SSL parameters for Redis client
    """
    use_ssl = os.getenv('REDIS_SSL', 'false').lower() == 'true'

    if not use_ssl:
        return {}

    # Create SSL context for Redis
    ssl_context = create_client_ssl_context(
        cafile=os.getenv('REDIS_SSL_CA'),
        verify=os.getenv('REDIS_SSL_VERIFY', 'true').lower() == 'true',
    )

    return {
        'ssl': True,
        'ssl_context': ssl_context,
    }


# =============================================================================
# EXTERNAL API SSL CONFIGURATION
# =============================================================================

def get_httpx_ssl_config() -> Dict[str, Any]:
    """
    Get SSL configuration for HTTPX client (external API calls).

    Returns:
        Dictionary with SSL parameters for HTTPX
    """
    verify_ssl = os.getenv('VERIFY_SSL', 'true').lower() == 'true'

    if not verify_ssl:
        logger.warning("SSL verification disabled for external APIs!")
        return {'verify': False}

    ca_bundle = os.getenv('SSL_CA_BUNDLE')

    if ca_bundle:
        return {'verify': ca_bundle}
    else:
        # Use default CA bundle
        return {'verify': True}


# =============================================================================
# UVICORN SSL CONFIGURATION
# =============================================================================

def get_uvicorn_ssl_config() -> Dict[str, Any]:
    """
    Get SSL configuration for Uvicorn server.

    Returns:
        Dictionary with SSL parameters for Uvicorn
    """
    certfile = os.getenv('SSL_CERTFILE')
    keyfile = os.getenv('SSL_KEYFILE')

    if not certfile or not keyfile:
        logger.info("No SSL certificates configured. Running without HTTPS.")
        return {}

    config = {
        'ssl_certfile': certfile,
        'ssl_keyfile': keyfile,
        'ssl_version': ssl.PROTOCOL_TLS,
        'ssl_cert_reqs': ssl.CERT_NONE,
    }

    # Optional: SSL certificate chain
    ssl_ca = os.getenv('SSL_CA_BUNDLE')
    if ssl_ca:
        config['ssl_ca_certs'] = ssl_ca

    # Optional: Cipher configuration
    ciphers = os.getenv('SSL_CIPHERS', CIPHER_STRING)
    config['ssl_ciphers'] = ciphers

    return config


# =============================================================================
# SECURITY HEADERS
# =============================================================================

def get_security_headers() -> Dict[str, str]:
    """
    Get recommended security headers for HTTPS responses.

    Returns:
        Dictionary of security headers
    """
    return {
        # HTTPS enforcement
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

        # Content security
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',

        # Referrer policy
        'Referrer-Policy': 'strict-origin-when-cross-origin',

        # Permissions policy
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',

        # Content Security Policy (adjust based on your needs)
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        ),
    }


# =============================================================================
# SSL CERTIFICATE VALIDATION
# =============================================================================

def validate_ssl_certificate(
    certfile: str,
    keyfile: str,
    check_expiry: bool = True,
) -> tuple[bool, str]:
    """
    Validate SSL certificate and key files.

    Args:
        certfile: Path to certificate file
        keyfile: Path to private key file
        check_expiry: Whether to check certificate expiry

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Check files exist
        if not os.path.exists(certfile):
            return False, f"Certificate file not found: {certfile}"

        if not os.path.exists(keyfile):
            return False, f"Key file not found: {keyfile}"

        # Try to load certificate and key
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        # Check certificate expiry (if requested)
        if check_expiry:
            import datetime
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend

            with open(certfile, 'rb') as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            # Check if expired
            if cert.not_valid_after < datetime.datetime.utcnow():
                return False, f"Certificate expired on {cert.not_valid_after}"

            # Warn if expiring soon (30 days)
            days_until_expiry = (cert.not_valid_after - datetime.datetime.utcnow()).days
            if days_until_expiry < 30:
                return True, f"Certificate expires in {days_until_expiry} days"

        return True, "Certificate is valid"

    except Exception as e:
        return False, f"Certificate validation error: {e}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # SSL context creation
    'create_ssl_context',
    'create_server_ssl_context',
    'create_client_ssl_context',

    # Service-specific configs
    'get_database_ssl_config',
    'get_redis_ssl_config',
    'get_httpx_ssl_config',
    'get_uvicorn_ssl_config',

    # Security headers
    'get_security_headers',

    # Certificate validation
    'validate_ssl_certificate',

    # Constants
    'MIN_TLS_VERSION',
    'RECOMMENDED_CIPHERS',
    'CIPHER_STRING',
]
