"""
Data Encryption Utilities

Provides encryption/decryption for sensitive data including:
- Field-level encryption for PII data
- Document encryption at rest
- Secure key management
- Encryption helpers for SQLAlchemy models
"""

import os
import base64
import hashlib
import secrets
from typing import Optional, Union, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# ENCRYPTION KEY MANAGEMENT
# =============================================================================

class EncryptionKeyManager:
    """
    Manages encryption keys with key rotation support.

    Keys are derived from a master key using PBKDF2 key derivation.
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption key manager.

        Args:
            master_key: Master encryption key (from environment or secrets)
        """
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')

        if not self.master_key:
            logger.warning(
                "No ENCRYPTION_MASTER_KEY found. Generating temporary key. "
                "THIS IS NOT SUITABLE FOR PRODUCTION!"
            )
            self.master_key = Fernet.generate_key().decode()

        # Primary encryption key (Fernet)
        self._primary_key = self._derive_fernet_key(self.master_key.encode())

        # Key rotation support (store old keys for decryption)
        self._rotation_keys = []

    def _derive_fernet_key(self, password: bytes, salt: Optional[bytes] = None) -> Fernet:
        """
        Derive a Fernet encryption key from password using PBKDF2.

        Args:
            password: Password/master key
            salt: Salt for key derivation (uses fixed salt for deterministic key)

        Returns:
            Fernet encryption object
        """
        # Use fixed salt for deterministic key derivation
        # In production, consider using per-environment salts
        salt = salt or b'legal_ai_system_salt_v1'

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)

    def get_primary_key(self) -> Fernet:
        """Get primary encryption key"""
        return self._primary_key

    def rotate_key(self, new_master_key: str):
        """
        Rotate encryption key.

        Args:
            new_master_key: New master key
        """
        # Store old key for decryption
        self._rotation_keys.append(self._primary_key)

        # Generate new primary key
        self._primary_key = self._derive_fernet_key(new_master_key.encode())

        logger.info("Encryption key rotated successfully")

    def get_all_keys(self) -> list:
        """Get all keys (primary + rotation keys) for decryption attempts"""
        return [self._primary_key] + self._rotation_keys


# Global key manager instance
_key_manager = None

def get_key_manager() -> EncryptionKeyManager:
    """Get global encryption key manager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = EncryptionKeyManager()
    return _key_manager


# =============================================================================
# FIELD-LEVEL ENCRYPTION
# =============================================================================

def encrypt_field(plaintext: Union[str, bytes], key_id: Optional[str] = None) -> str:
    """
    Encrypt a field value (PII, sensitive data).

    Args:
        plaintext: Data to encrypt
        key_id: Optional key identifier for key rotation

    Returns:
        Base64-encoded encrypted data with format: {version}:{ciphertext}
    """
    if plaintext is None:
        return None

    # Convert to bytes if string
    if isinstance(plaintext, str):
        plaintext = plaintext.encode('utf-8')

    # Get encryption key
    key_manager = get_key_manager()
    fernet = key_manager.get_primary_key()

    # Encrypt
    encrypted = fernet.encrypt(plaintext)

    # Add version prefix for future key rotation
    # Format: v1:{base64_ciphertext}
    versioned = f"v1:{encrypted.decode('utf-8')}"

    return versioned


def decrypt_field(ciphertext: str) -> Optional[str]:
    """
    Decrypt a field value.

    Args:
        ciphertext: Encrypted data (with version prefix)

    Returns:
        Decrypted plaintext string, or None if decryption fails
    """
    if not ciphertext:
        return None

    try:
        # Parse version
        if ':' in ciphertext:
            version, encrypted_data = ciphertext.split(':', 1)
        else:
            # Legacy format without version
            version = 'v1'
            encrypted_data = ciphertext

        # Get encryption keys
        key_manager = get_key_manager()
        keys = key_manager.get_all_keys()

        # Try decryption with all available keys (supports key rotation)
        for fernet in keys:
            try:
                decrypted = fernet.decrypt(encrypted_data.encode('utf-8'))
                return decrypted.decode('utf-8')
            except Exception:
                continue

        # If all keys failed
        logger.error("Failed to decrypt field with any available key")
        return None

    except Exception as e:
        logger.error(f"Error decrypting field: {e}")
        return None


# =============================================================================
# DOCUMENT ENCRYPTION
# =============================================================================

def encrypt_document(
    content: bytes,
    document_id: str
) -> tuple[bytes, dict]:
    """
    Encrypt document content with AES-256-GCM.

    Args:
        content: Document content (bytes)
        document_id: Document identifier (used in AAD)

    Returns:
        Tuple of (encrypted_content, metadata)
        metadata contains: iv, tag, algorithm, version
    """
    # Generate random IV
    iv = secrets.token_bytes(12)  # 96 bits for GCM

    # Get encryption key (derive from master key)
    key_manager = get_key_manager()
    master_key = key_manager.master_key.encode()

    # Derive document encryption key
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits for AES-256
        salt=b'document_encryption_salt',
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(master_key)

    # Create cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()

    # Add document ID as Additional Authenticated Data (AAD)
    # This ensures ciphertext is tied to specific document
    encryptor.authenticate_additional_data(document_id.encode('utf-8'))

    # Encrypt content
    ciphertext = encryptor.update(content) + encryptor.finalize()

    # Get authentication tag
    tag = encryptor.tag

    # Return encrypted content and metadata
    metadata = {
        'iv': base64.b64encode(iv).decode('utf-8'),
        'tag': base64.b64encode(tag).decode('utf-8'),
        'algorithm': 'AES-256-GCM',
        'version': 'v1',
    }

    return ciphertext, metadata


def decrypt_document(
    ciphertext: bytes,
    document_id: str,
    metadata: dict
) -> Optional[bytes]:
    """
    Decrypt document content.

    Args:
        ciphertext: Encrypted content
        document_id: Document identifier
        metadata: Encryption metadata (iv, tag, algorithm, version)

    Returns:
        Decrypted content bytes, or None if decryption fails
    """
    try:
        # Parse metadata
        iv = base64.b64decode(metadata['iv'])
        tag = base64.b64decode(metadata['tag'])

        # Get decryption key
        key_manager = get_key_manager()
        master_key = key_manager.master_key.encode()

        # Derive document encryption key (same as encryption)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'document_encryption_salt',
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(master_key)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # Add document ID as AAD (must match encryption)
        decryptor.authenticate_additional_data(document_id.encode('utf-8'))

        # Decrypt
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext

    except Exception as e:
        logger.error(f"Error decrypting document {document_id}: {e}")
        return None


# =============================================================================
# HASHING UTILITIES
# =============================================================================

def hash_data(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """
    Hash data (one-way, for comparison not encryption).

    Args:
        data: Data to hash
        algorithm: Hash algorithm (sha256, sha512)

    Returns:
        Hex-encoded hash
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    if algorithm == 'sha256':
        h = hashlib.sha256(data)
    elif algorithm == 'sha512':
        h = hashlib.sha512(data)
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    return h.hexdigest()


def hash_pii(pii_data: str) -> str:
    """
    Hash PII data for indexing/comparison without storing plaintext.

    Uses SHA-256 with application-specific salt.

    Args:
        pii_data: PII data (email, SSN, etc.)

    Returns:
        Hex-encoded hash
    """
    salt = os.getenv('PII_HASH_SALT', 'legal_ai_pii_salt')
    salted = f"{salt}:{pii_data}"
    return hash_data(salted, algorithm='sha256')


# =============================================================================
# SECURE TOKEN GENERATION
# =============================================================================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.

    Args:
        length: Token length in bytes

    Returns:
        URL-safe base64-encoded token
    """
    token_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(token_bytes).decode('utf-8')


def generate_api_key() -> str:
    """
    Generate secure API key.

    Returns:
        API key in format: lai_xxxxxxxxxxxxxxxxxxxx
    """
    token = generate_secure_token(24)
    return f"lai_{token[:32]}"


# =============================================================================
# SQLALCHEMY ENCRYPTED FIELD TYPE
# =============================================================================

from sqlalchemy.types import TypeDecorator, String, Text

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy column type for encrypted strings.

    Automatically encrypts on write, decrypts on read.

    Usage:
        class User(Base):
            ssn = Column(EncryptedString(255))
            email = Column(EncryptedString(255))
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt value before storing in database"""
        if value is not None:
            return encrypt_field(value)
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt value when reading from database"""
        if value is not None:
            return decrypt_field(value)
        return value


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy column type for encrypted text (larger content).

    Usage:
        class Document(Base):
            sensitive_content = Column(EncryptedText)
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt value before storing in database"""
        if value is not None:
            return encrypt_field(value)
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt value when reading from database"""
        if value is not None:
            return decrypt_field(value)
        return value


# =============================================================================
# DATA MASKING
# =============================================================================

def mask_email(email: str) -> str:
    """
    Mask email address for display.

    Example: john.doe@example.com -> j***@example.com

    Args:
        email: Email address

    Returns:
        Masked email
    """
    if not email or '@' not in email:
        return email

    local, domain = email.split('@', 1)

    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 1)

    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for display.

    Example: +1-555-123-4567 -> +1-***-***-4567

    Args:
        phone: Phone number

    Returns:
        Masked phone
    """
    if not phone:
        return phone

    # Keep last 4 digits
    if len(phone) > 4:
        return '*' * (len(phone) - 4) + phone[-4:]
    else:
        return '*' * len(phone)


def mask_ssn(ssn: str) -> str:
    """
    Mask SSN for display.

    Example: 123-45-6789 -> ***-**-6789

    Args:
        ssn: SSN

    Returns:
        Masked SSN
    """
    if not ssn:
        return ssn

    # Keep last 4 digits
    if len(ssn) > 4:
        return '*' * (len(ssn) - 4) + ssn[-4:]
    else:
        return '*' * len(ssn)


def mask_credit_card(card: str) -> str:
    """
    Mask credit card number for display.

    Example: 4532-1234-5678-9010 -> ****-****-****-9010

    Args:
        card: Credit card number

    Returns:
        Masked card number
    """
    if not card:
        return card

    # Remove spaces/dashes
    digits = ''.join(c for c in card if c.isdigit())

    if len(digits) > 4:
        masked = '*' * (len(digits) - 4) + digits[-4:]
    else:
        masked = '*' * len(digits)

    # Restore original formatting
    result = []
    digit_index = 0
    for c in card:
        if c.isdigit():
            result.append(masked[digit_index])
            digit_index += 1
        else:
            result.append(c)

    return ''.join(result)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Key management
    'EncryptionKeyManager',
    'get_key_manager',

    # Field encryption
    'encrypt_field',
    'decrypt_field',

    # Document encryption
    'encrypt_document',
    'decrypt_document',

    # Hashing
    'hash_data',
    'hash_pii',

    # Token generation
    'generate_secure_token',
    'generate_api_key',

    # SQLAlchemy types
    'EncryptedString',
    'EncryptedText',

    # Data masking
    'mask_email',
    'mask_phone',
    'mask_ssn',
    'mask_credit_card',
]
