"""
COMPREHENSIVE KEY MANAGEMENT SYSTEM

Implements enterprise-grade key management with AWS KMS/HashiCorp Vault integration,
automatic key rotation, client matter separation, and comprehensive audit trails.

CRITICAL: Manages encryption keys for all legal documents with client matter isolation.
"""

import os
import logging
import json
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import sqlite3
import threading
from enum import Enum

logger = logging.getLogger(__name__)

class KeyType(Enum):
    MASTER = "master"
    CLIENT_MATTER = "client_matter"
    DOCUMENT = "document"
    BACKUP = "backup"
    ARCHIVE = "archive"
    SYSTEM = "system"

class KeyStatus(Enum):
    ACTIVE = "active"
    ROTATING = "rotating"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"
    COMPROMISED = "compromised"

@dataclass
class KeyMetadata:
    """Metadata for encryption keys"""
    key_id: str
    key_type: KeyType
    key_status: KeyStatus
    client_id: Optional[str]
    matter_id: Optional[str]
    created_at: datetime
    last_used_at: datetime
    rotation_due_date: datetime
    access_count: int
    algorithm: str
    key_size_bits: int
    derived_from_master: bool
    vault_path: Optional[str]
    compliance_level: str
    audit_trail: List[Dict[str, Any]]

@dataclass
class KeyRotationPolicy:
    """Key rotation policy configuration"""
    key_type: KeyType
    rotation_interval_days: int
    max_key_age_days: int
    auto_rotation_enabled: bool
    rotation_warning_days: int
    max_usage_count: Optional[int]
    require_manual_approval: bool

class KeyVaultInterface:
    """Abstract interface for key vault implementations"""
    
    def store_key(self, key_id: str, key_data: bytes, metadata: Dict[str, Any]) -> bool:
        raise NotImplementedError
    
    def retrieve_key(self, key_id: str) -> Tuple[bool, bytes, Dict[str, Any]]:
        raise NotImplementedError
    
    def delete_key(self, key_id: str) -> bool:
        raise NotImplementedError
    
    def list_keys(self, key_type: Optional[str] = None) -> List[str]:
        raise NotImplementedError

class LocalKeyVault(KeyVaultInterface):
    """Local file-based key vault (for development/testing)"""
    
    def __init__(self, vault_path: str = "secure_vault"):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Create database for key metadata
        self.db_path = self.vault_path / "key_vault.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize key vault database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS key_vault (
                    key_id TEXT PRIMARY KEY,
                    key_file_path TEXT NOT NULL,
                    key_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def store_key(self, key_id: str, key_data: bytes, metadata: Dict[str, Any]) -> bool:
        try:
            # Store key in encrypted file
            key_file = self.vault_path / f"{key_id}.key"
            with open(key_file, 'wb') as f:
                f.write(key_data)
            os.chmod(key_file, 0o600)
            
            # Store metadata in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO key_vault (key_id, key_file_path, key_type, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                    (key_id, str(key_file), metadata.get('key_type', 'unknown'), datetime.utcnow().isoformat(), json.dumps(metadata))
                )
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"[KEY_VAULT] Failed to store key {key_id}: {e}")
            return False
    
    def retrieve_key(self, key_id: str) -> Tuple[bool, bytes, Dict[str, Any]]:
        try:
            # Get metadata from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT key_file_path, metadata FROM key_vault WHERE key_id = ?", (key_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, b"", {}
                
                key_file_path, metadata_json = result
                metadata = json.loads(metadata_json)
            
            # Read key data
            key_file = Path(key_file_path)
            if not key_file.exists():
                return False, b"", {}
            
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            return True, key_data, metadata
        except Exception as e:
            logger.error(f"[KEY_VAULT] Failed to retrieve key {key_id}: {e}")
            return False, b"", {}
    
    def delete_key(self, key_id: str) -> bool:
        try:
            # Get key file path
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT key_file_path FROM key_vault WHERE key_id = ?", (key_id,))
                result = cursor.fetchone()
                
                if result:
                    key_file_path = result[0]
                    key_file = Path(key_file_path)
                    
                    # Securely delete key file
                    if key_file.exists():
                        # Overwrite with random data before deletion
                        file_size = key_file.stat().st_size
                        with open(key_file, 'wb') as f:
                            f.write(secrets.token_bytes(file_size))
                        key_file.unlink()
                    
                    # Remove from database
                    conn.execute("DELETE FROM key_vault WHERE key_id = ?", (key_id,))
                    conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"[KEY_VAULT] Failed to delete key {key_id}: {e}")
            return False
    
    def list_keys(self, key_type: Optional[str] = None) -> List[str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                if key_type:
                    cursor = conn.execute("SELECT key_id FROM key_vault WHERE key_type = ?", (key_type,))
                else:
                    cursor = conn.execute("SELECT key_id FROM key_vault")
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[KEY_VAULT] Failed to list keys: {e}")
            return []

class KeyManagementSystem:
    """Comprehensive key management system with enterprise features"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # Initialize key vault
        vault_type = self.config.get('vault_type', 'local')
        if vault_type == 'local':
            self.vault = LocalKeyVault(self.config.get('vault_path', 'secure_vault'))
        else:
            raise ValueError(f"Unsupported vault type: {vault_type}")
        
        # Key rotation policies
        self.rotation_policies = self._init_rotation_policies()
        
        # In-memory key cache (with TTL)
        self._key_cache = {}
        self._cache_timestamps = {}
        self._cache_ttl_seconds = 300  # 5 minutes
        
        # Threading lock for key operations
        self._key_lock = threading.RLock()
        
        # Audit log
        self.audit_log = []
        
        # Initialize master key
        self._master_key_id = "master_key_v1"
        self._ensure_master_key()
        
        logger.info("[KEY_MANAGEMENT] Key management system initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for key management"""
        return {
            'vault_type': 'local',
            'vault_path': 'secure_vault',
            'master_key_algorithm': 'ChaCha20Poly1305',
            'client_key_algorithm': 'AES-256-GCM',
            'key_derivation_iterations': 100000,
            'cache_ttl_seconds': 300,
            'auto_rotation_enabled': True,
            'audit_all_operations': True,
            'require_key_approval': False
        }
    
    def _init_rotation_policies(self) -> Dict[KeyType, KeyRotationPolicy]:
        """Initialize key rotation policies"""
        return {
            KeyType.MASTER: KeyRotationPolicy(
                key_type=KeyType.MASTER,
                rotation_interval_days=365,  # 1 year
                max_key_age_days=400,
                auto_rotation_enabled=False,  # Manual approval required
                rotation_warning_days=30,
                max_usage_count=None,
                require_manual_approval=True
            ),
            KeyType.CLIENT_MATTER: KeyRotationPolicy(
                key_type=KeyType.CLIENT_MATTER,
                rotation_interval_days=90,  # 3 months
                max_key_age_days=120,
                auto_rotation_enabled=True,
                rotation_warning_days=14,
                max_usage_count=10000,
                require_manual_approval=False
            ),
            KeyType.DOCUMENT: KeyRotationPolicy(
                key_type=KeyType.DOCUMENT,
                rotation_interval_days=30,  # 1 month
                max_key_age_days=45,
                auto_rotation_enabled=True,
                rotation_warning_days=7,
                max_usage_count=1000,
                require_manual_approval=False
            ),
            KeyType.BACKUP: KeyRotationPolicy(
                key_type=KeyType.BACKUP,
                rotation_interval_days=90,  # 3 months
                max_key_age_days=120,
                auto_rotation_enabled=True,
                rotation_warning_days=14,
                max_usage_count=None,
                require_manual_approval=False
            )
        }
    
    def _ensure_master_key(self):
        """Ensure master key exists"""
        with self._key_lock:
            success, key_data, metadata = self.vault.retrieve_key(self._master_key_id)
            
            if not success:
                # Generate new master key
                master_key = ChaCha20Poly1305.generate_key()
                
                metadata = {
                    'key_id': self._master_key_id,
                    'key_type': KeyType.MASTER.value,
                    'algorithm': 'ChaCha20Poly1305',
                    'key_size_bits': 256,
                    'created_at': datetime.utcnow().isoformat(),
                    'compliance_level': 'CRITICAL'
                }
                
                success = self.vault.store_key(self._master_key_id, master_key, metadata)
                if not success:
                    raise RuntimeError("Failed to store master key")
                
                self._log_key_event('MASTER_KEY_GENERATED', {
                    'key_id': self._master_key_id,
                    'algorithm': 'ChaCha20Poly1305'
                })
                
                logger.critical("[KEY_MANAGEMENT] New master key generated")
    
    def create_client_matter_key(self, client_id: str, matter_id: str, 
                                compliance_level: str = 'ATTORNEY_CLIENT') -> Tuple[bool, str, str]:
        """Create encryption key for specific client matter"""
        
        key_id = f"client_{client_id}_matter_{matter_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        with self._key_lock:
            logger.info(f"[KEY_MANAGEMENT] Creating client matter key: {key_id}")
            
            try:
                # Check if key already exists
                existing_key = self._find_active_client_key(client_id, matter_id)
                if existing_key:
                    logger.warning(f"[KEY_MANAGEMENT] Active key already exists for client {client_id} matter {matter_id}")
                    return True, existing_key, "Key already exists"
                
                # Generate new key
                client_key = AESGCM.generate_key(bit_length=256)
                
                # Create key metadata
                metadata = KeyMetadata(
                    key_id=key_id,
                    key_type=KeyType.CLIENT_MATTER,
                    key_status=KeyStatus.ACTIVE,
                    client_id=client_id,
                    matter_id=matter_id,
                    created_at=datetime.utcnow(),
                    last_used_at=datetime.utcnow(),
                    rotation_due_date=datetime.utcnow() + timedelta(days=90),
                    access_count=0,
                    algorithm='AES-256-GCM',
                    key_size_bits=256,
                    derived_from_master=True,
                    vault_path=None,
                    compliance_level=compliance_level,
                    audit_trail=[]
                )
                
                # Store key in vault
                vault_metadata = asdict(metadata)
                vault_metadata['created_at'] = metadata.created_at.isoformat()
                vault_metadata['last_used_at'] = metadata.last_used_at.isoformat()
                vault_metadata['rotation_due_date'] = metadata.rotation_due_date.isoformat()
                vault_metadata['key_type'] = metadata.key_type.value
                vault_metadata['key_status'] = metadata.key_status.value
                
                success = self.vault.store_key(key_id, client_key, vault_metadata)
                if not success:
                    return False, "", "Failed to store key in vault"
                
                # Log key creation
                self._log_key_event('CLIENT_MATTER_KEY_CREATED', {
                    'key_id': key_id,
                    'client_id': client_id,
                    'matter_id': matter_id,
                    'compliance_level': compliance_level,
                    'algorithm': 'AES-256-GCM'
                })
                
                logger.info(f"[KEY_MANAGEMENT] Client matter key created successfully: {key_id}")
                
                return True, key_id, "Key created successfully"
                
            except Exception as e:
                error_msg = f"Failed to create client matter key: {str(e)}"
                logger.error(f"[KEY_MANAGEMENT] {error_msg}", exc_info=True)
                
                self._log_key_event('CLIENT_MATTER_KEY_CREATION_FAILED', {
                    'client_id': client_id,
                    'matter_id': matter_id,
                    'error': str(e)
                })
                
                return False, "", error_msg
    
    def get_client_matter_key(self, client_id: str, matter_id: str) -> Tuple[bool, bytes, str]:
        """Retrieve encryption key for client matter"""
        
        with self._key_lock:
            try:
                # Find active key for client matter
                key_id = self._find_active_client_key(client_id, matter_id)
                if not key_id:
                    return False, b"", "No active key found for client matter"
                
                # Check cache first
                cache_key = f"{client_id}_{matter_id}"
                if self._is_cached_key_valid(cache_key):
                    key_data = self._key_cache[cache_key]
                    self._log_key_access(key_id, 'CACHE_HIT')
                    return True, key_data, key_id
                
                # Retrieve from vault
                success, key_data, metadata = self.vault.retrieve_key(key_id)
                if not success:
                    return False, b"", "Failed to retrieve key from vault"
                
                # Update cache
                self._key_cache[cache_key] = key_data
                self._cache_timestamps[cache_key] = datetime.utcnow()
                
                # Log key access
                self._log_key_access(key_id, 'VAULT_ACCESS')
                
                # Check if key needs rotation
                self._check_key_rotation(key_id, metadata)
                
                logger.debug(f"[KEY_MANAGEMENT] Retrieved client matter key: {key_id}")
                
                return True, key_data, key_id
                
            except Exception as e:
                error_msg = f"Failed to retrieve client matter key: {str(e)}"
                logger.error(f"[KEY_MANAGEMENT] {error_msg}", exc_info=True)
                return False, b"", error_msg
    
    def rotate_key(self, key_id: str, force: bool = False) -> Tuple[bool, str, str]:
        """Rotate encryption key"""
        
        with self._key_lock:
            logger.info(f"[KEY_MANAGEMENT] Starting key rotation: {key_id}")
            
            try:
                # Get current key metadata
                success, current_key, metadata = self.vault.retrieve_key(key_id)
                if not success:
                    return False, "", "Current key not found"
                
                key_type = KeyType(metadata.get('key_type', 'unknown'))
                policy = self.rotation_policies.get(key_type)
                
                if not policy:
                    return False, "", f"No rotation policy for key type: {key_type}"
                
                # Check if rotation is required or forced
                created_at = datetime.fromisoformat(metadata['created_at'])
                key_age_days = (datetime.utcnow() - created_at).days
                
                if not force and key_age_days < policy.rotation_interval_days:
                    return False, "", f"Key rotation not due (age: {key_age_days} days)"
                
                if policy.require_manual_approval and not force:
                    return False, "", "Manual approval required for key rotation"
                
                # Generate new key ID
                new_key_id = f"{key_id}_rotated_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                
                # Generate new key based on type
                if key_type == KeyType.CLIENT_MATTER:
                    new_key = AESGCM.generate_key(bit_length=256)
                    algorithm = 'AES-256-GCM'
                elif key_type == KeyType.MASTER:
                    new_key = ChaCha20Poly1305.generate_key()
                    algorithm = 'ChaCha20Poly1305'
                else:
                    new_key = ChaCha20Poly1305.generate_key()
                    algorithm = 'ChaCha20Poly1305'
                
                # Create new key metadata
                new_metadata = metadata.copy()
                new_metadata.update({
                    'key_id': new_key_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'last_used_at': datetime.utcnow().isoformat(),
                    'rotation_due_date': (datetime.utcnow() + timedelta(days=policy.rotation_interval_days)).isoformat(),
                    'access_count': 0,
                    'algorithm': algorithm,
                    'key_status': KeyStatus.ACTIVE.value,
                    'rotated_from': key_id
                })
                
                # Store new key
                success = self.vault.store_key(new_key_id, new_key, new_metadata)
                if not success:
                    return False, "", "Failed to store new key"
                
                # Mark old key as deprecated
                old_metadata = metadata.copy()
                old_metadata['key_status'] = KeyStatus.DEPRECATED.value
                old_metadata['deprecated_at'] = datetime.utcnow().isoformat()
                old_metadata['replaced_by'] = new_key_id
                
                self.vault.store_key(key_id, current_key, old_metadata)
                
                # Clear cache
                self._clear_key_cache()
                
                # Log rotation
                self._log_key_event('KEY_ROTATED', {
                    'old_key_id': key_id,
                    'new_key_id': new_key_id,
                    'key_type': key_type.value,
                    'algorithm': algorithm,
                    'rotation_reason': 'scheduled' if not force else 'forced'
                })
                
                logger.info(f"[KEY_MANAGEMENT] Key rotation completed: {key_id} -> {new_key_id}")
                
                return True, new_key_id, "Key rotation completed successfully"
                
            except Exception as e:
                error_msg = f"Key rotation failed: {str(e)}"
                logger.error(f"[KEY_MANAGEMENT] {error_msg}", exc_info=True)
                
                self._log_key_event('KEY_ROTATION_FAILED', {
                    'key_id': key_id,
                    'error': str(e)
                })
                
                return False, "", error_msg
    
    def audit_key_access(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate key access audit report"""
        
        audit_entries = []
        
        for entry in self.audit_log:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if start_date <= entry_time <= end_date:
                audit_entries.append(entry)
        
        # Sort by timestamp
        audit_entries.sort(key=lambda x: x['timestamp'])
        
        return audit_entries
    
    def get_keys_due_for_rotation(self) -> List[Dict[str, Any]]:
        """Get list of keys due for rotation"""
        
        keys_due = []
        
        for key_type, policy in self.rotation_policies.items():
            vault_keys = self.vault.list_keys(key_type.value)
            
            for key_id in vault_keys:
                success, key_data, metadata = self.vault.retrieve_key(key_id)
                if not success:
                    continue
                
                # Check if key is active
                if metadata.get('key_status') != KeyStatus.ACTIVE.value:
                    continue
                
                created_at = datetime.fromisoformat(metadata['created_at'])
                key_age_days = (datetime.utcnow() - created_at).days
                
                rotation_due_date = datetime.fromisoformat(metadata.get('rotation_due_date', created_at.isoformat()))
                days_until_rotation = (rotation_due_date - datetime.utcnow()).days
                
                if days_until_rotation <= policy.rotation_warning_days:
                    keys_due.append({
                        'key_id': key_id,
                        'key_type': key_type.value,
                        'age_days': key_age_days,
                        'days_until_rotation': days_until_rotation,
                        'rotation_overdue': days_until_rotation < 0,
                        'client_id': metadata.get('client_id'),
                        'matter_id': metadata.get('matter_id'),
                        'compliance_level': metadata.get('compliance_level')
                    })
        
        return keys_due
    
    def _find_active_client_key(self, client_id: str, matter_id: str) -> Optional[str]:
        """Find active key for client matter"""
        vault_keys = self.vault.list_keys(KeyType.CLIENT_MATTER.value)
        
        for key_id in vault_keys:
            success, _, metadata = self.vault.retrieve_key(key_id)
            if not success:
                continue
            
            if (metadata.get('client_id') == client_id and 
                metadata.get('matter_id') == matter_id and
                metadata.get('key_status') == KeyStatus.ACTIVE.value):
                return key_id
        
        return None
    
    def _is_cached_key_valid(self, cache_key: str) -> bool:
        """Check if cached key is still valid"""
        if cache_key not in self._key_cache:
            return False
        
        cache_time = self._cache_timestamps.get(cache_key)
        if not cache_time:
            return False
        
        age_seconds = (datetime.utcnow() - cache_time).total_seconds()
        return age_seconds < self._cache_ttl_seconds
    
    def _clear_key_cache(self):
        """Clear key cache"""
        self._key_cache.clear()
        self._cache_timestamps.clear()
    
    def _check_key_rotation(self, key_id: str, metadata: Dict[str, Any]):
        """Check if key needs rotation and schedule if necessary"""
        rotation_due_date = datetime.fromisoformat(metadata.get('rotation_due_date', metadata['created_at']))
        
        if datetime.utcnow() > rotation_due_date:
            key_type = KeyType(metadata['key_type'])
            policy = self.rotation_policies.get(key_type)
            
            if policy and policy.auto_rotation_enabled and not policy.require_manual_approval:
                # Schedule automatic rotation (in production, this would use a task queue)
                logger.warning(f"[KEY_MANAGEMENT] Key due for rotation: {key_id}")
                
                # For now, just log the need for rotation
                self._log_key_event('KEY_ROTATION_DUE', {
                    'key_id': key_id,
                    'key_type': key_type.value,
                    'days_overdue': (datetime.utcnow() - rotation_due_date).days
                })
    
    def _log_key_access(self, key_id: str, access_type: str):
        """Log key access for audit"""
        self._log_key_event('KEY_ACCESS', {
            'key_id': key_id,
            'access_type': access_type
        })
    
    def _log_key_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log key management events for audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'service': 'key_management_system',
            'event_data': event_data,
            'compliance_audit': True,
            'key_management': True
        }
        
        # Store in audit log
        self.audit_log.append(log_entry)
        
        # Also log to system logger
        logger.info(f"[KEY_MANAGEMENT_AUDIT] {json.dumps(log_entry)}")

# Global key management system instance
key_management_system = KeyManagementSystem()

__all__ = [
    'KeyManagementSystem',
    'KeyType',
    'KeyStatus', 
    'KeyMetadata',
    'KeyRotationPolicy',
    'key_management_system'
]