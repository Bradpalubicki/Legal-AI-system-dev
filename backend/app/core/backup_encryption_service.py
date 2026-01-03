"""
BACKUP ENCRYPTION SERVICE

Implements secure backup encryption with separate keys from main encryption system.
Provides database backup encryption, key vault integration, and restoration testing.

CRITICAL: Backup encryption uses separate keys and different algorithms for security isolation.
"""

import os
import logging
import json
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import sqlite3
import subprocess

logger = logging.getLogger(__name__)

@dataclass
class BackupEncryptionConfig:
    """Configuration for backup encryption system"""
    backup_key_path: str = "backup/keys"
    encrypted_backup_path: str = "backup/encrypted"
    database_backup_path: str = "backup/database"
    key_rotation_days: int = 90
    encryption_algorithm: str = "ChaCha20Poly1305"
    key_derivation_iterations: int = 150000
    backup_retention_days: int = 365
    compression_enabled: bool = True
    backup_verification: bool = True

@dataclass
class BackupMetadata:
    """Metadata for encrypted backups"""
    backup_id: str
    backup_type: str  # DATABASE, DOCUMENTS, FULL_SYSTEM
    created_at: datetime
    encrypted_at: datetime
    original_size_bytes: int
    compressed_size_bytes: int
    encrypted_size_bytes: int
    backup_hash_sha256: str
    encryption_key_id: str
    encryption_algorithm: str
    compression_algorithm: str
    verification_status: str  # VERIFIED, PENDING, FAILED
    retention_until: datetime

class BackupEncryptionService:
    """Secure backup encryption service with separate key management"""
    
    def __init__(self, config: BackupEncryptionConfig = None):
        self.config = config or BackupEncryptionConfig()
        
        # Initialize backup directories
        self._setup_backup_directories()
        
        # Load or create backup keys (separate from main encryption)
        self._backup_keys = self._initialize_backup_keys()
        
        # Key rotation tracking
        self._key_rotation_log = []
        
        logger.info("[BACKUP_ENCRYPTION] Backup encryption service initialized")
    
    def _setup_backup_directories(self):
        """Create necessary backup directories with secure permissions"""
        directories = [
            self.config.backup_key_path,
            self.config.encrypted_backup_path,
            self.config.database_backup_path,
            "backup/metadata",
            "backup/restore_tests"
        ]
        
        for dir_path in directories:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            
            # Set restrictive permissions (owner only)
            if os.name != 'nt':  # Unix-like systems
                os.chmod(path, 0o700)
    
    def _initialize_backup_keys(self) -> Dict[str, bytes]:
        """Initialize backup encryption keys (separate from main keys)"""
        keys = {}
        key_types = ['database', 'documents', 'system', 'archive']
        
        for key_type in key_types:
            key_file = Path(self.config.backup_key_path) / f"backup_{key_type}.key"
            
            if key_file.exists():
                # Load existing key
                with open(key_file, 'rb') as f:
                    keys[key_type] = f.read()
                logger.info(f"[BACKUP_ENCRYPTION] Loaded existing backup key: {key_type}")
            else:
                # Generate new key using ChaCha20Poly1305 (different from main encryption)
                key = ChaCha20Poly1305.generate_key()
                keys[key_type] = key
                
                # Save key with secure permissions
                with open(key_file, 'wb') as f:
                    f.write(key)
                os.chmod(key_file, 0o600)
                
                logger.critical(f"[BACKUP_ENCRYPTION] Generated new backup key: {key_type}")
        
        # Create master backup key for key encryption
        master_key_file = Path(self.config.backup_key_path) / "backup_master.key"
        if not master_key_file.exists():
            master_key = ChaCha20Poly1305.generate_key()
            with open(master_key_file, 'wb') as f:
                f.write(master_key)
            os.chmod(master_key_file, 0o600)
            keys['master'] = master_key
            logger.critical("[BACKUP_ENCRYPTION] Generated new backup master key")
        else:
            with open(master_key_file, 'rb') as f:
                keys['master'] = f.read()
        
        return keys
    
    def encrypt_database_backup(self, database_path: str, backup_id: Optional[str] = None) -> Tuple[bool, str, BackupMetadata]:
        """Encrypt database backup with separate encryption key"""
        
        if backup_id is None:
            backup_id = f"db_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"[BACKUP_ENCRYPTION] Starting database backup encryption: {backup_id}")
        
        try:
            # Create database dump
            dump_file = Path(self.config.database_backup_path) / f"{backup_id}.sql"
            
            if database_path.endswith('.db') or database_path.endswith('.sqlite'):
                # SQLite database
                success = self._create_sqlite_dump(database_path, dump_file)
            elif database_path.startswith('postgresql://') or database_path.startswith('postgres://'):
                # PostgreSQL database
                success = self._create_postgresql_dump(database_path, dump_file)
            else:
                raise ValueError(f"Unsupported database type: {database_path}")
            
            if not success:
                return False, "Database dump creation failed", None
            
            # Get file sizes
            original_size = dump_file.stat().st_size
            
            # Compress backup if enabled
            compressed_file = dump_file
            compressed_size = original_size
            compression_algorithm = "none"
            
            if self.config.compression_enabled:
                compressed_file = Path(str(dump_file) + ".gz")
                success = self._compress_file(dump_file, compressed_file)
                if success:
                    compressed_size = compressed_file.stat().st_size
                    compression_algorithm = "gzip"
                    dump_file.unlink()  # Remove uncompressed version
                    dump_file = compressed_file
            
            # Read backup data
            with open(dump_file, 'rb') as f:
                backup_data = f.read()
            
            # Calculate hash for integrity
            backup_hash = hashlib.sha256(backup_data).hexdigest()
            
            # Encrypt using ChaCha20Poly1305 (different from main encryption)
            cipher = ChaCha20Poly1305(self._backup_keys['database'])
            nonce = secrets.token_bytes(12)
            
            # Additional authenticated data
            aad = json.dumps({
                'backup_id': backup_id,
                'backup_type': 'DATABASE',
                'created_at': datetime.utcnow().isoformat(),
                'original_hash': backup_hash
            }).encode('utf-8')
            
            # Perform encryption
            encrypted_data = cipher.encrypt(nonce, backup_data, aad)
            
            # Create encrypted backup container
            encrypted_container = {
                'version': '2.0',
                'algorithm': 'ChaCha20Poly1305',
                'backup_id': backup_id,
                'backup_type': 'DATABASE',
                'nonce': base64.b64encode(nonce).decode('utf-8'),
                'aad': base64.b64encode(aad).decode('utf-8'),
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'original_hash': backup_hash,
                'created_at': datetime.utcnow().isoformat(),
                'key_id': hashlib.sha256(self._backup_keys['database']).hexdigest()[:16],
                'compression': compression_algorithm
            }
            
            # Write encrypted backup
            encrypted_file = Path(self.config.encrypted_backup_path) / f"{backup_id}.encrypted"
            with open(encrypted_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_container, f, indent=2)
            os.chmod(encrypted_file, 0o600)
            
            encrypted_size = encrypted_file.stat().st_size
            
            # Create backup metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type='DATABASE',
                created_at=datetime.utcnow(),
                encrypted_at=datetime.utcnow(),
                original_size_bytes=original_size,
                compressed_size_bytes=compressed_size,
                encrypted_size_bytes=encrypted_size,
                backup_hash_sha256=backup_hash,
                encryption_key_id=encrypted_container['key_id'],
                encryption_algorithm='ChaCha20Poly1305',
                compression_algorithm=compression_algorithm,
                verification_status='PENDING',
                retention_until=datetime.utcnow() + timedelta(days=self.config.backup_retention_days)
            )
            
            # Save metadata
            self._save_backup_metadata(backup_id, metadata)
            
            # Clean up temporary files
            if dump_file.exists():
                dump_file.unlink()
            
            # Log backup creation
            self._log_backup_event('DATABASE_BACKUP_ENCRYPTED', {
                'backup_id': backup_id,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'encrypted_size': encrypted_size,
                'compression_ratio': f"{(1 - compressed_size/original_size)*100:.1f}%",
                'encryption_algorithm': 'ChaCha20Poly1305'
            })
            
            logger.info(f"[BACKUP_ENCRYPTION] Database backup encrypted successfully: {backup_id}")
            
            return True, str(encrypted_file), metadata
            
        except Exception as e:
            error_msg = f"Database backup encryption failed: {str(e)}"
            logger.error(f"[BACKUP_ENCRYPTION] {error_msg}", exc_info=True)
            
            self._log_backup_event('DATABASE_BACKUP_FAILED', {
                'backup_id': backup_id,
                'error': str(e)
            })
            
            return False, error_msg, None
    
    def _create_sqlite_dump(self, db_path: str, output_file: Path) -> bool:
        """Create SQLite database dump"""
        try:
            with sqlite3.connect(db_path) as conn:
                with open(output_file, 'w') as f:
                    for line in conn.iterdump():
                        f.write(f"{line}\\n")
            return True
        except Exception as e:
            logger.error(f"[BACKUP_ENCRYPTION] SQLite dump failed: {e}")
            return False
    
    def _create_postgresql_dump(self, connection_string: str, output_file: Path) -> bool:
        """Create PostgreSQL database dump"""
        try:
            # Use pg_dump command
            result = subprocess.run([
                'pg_dump', connection_string,
                '--no-password',
                '--file', str(output_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                logger.error(f"[BACKUP_ENCRYPTION] pg_dump failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"[BACKUP_ENCRYPTION] PostgreSQL dump failed: {e}")
            return False
    
    def _compress_file(self, input_file: Path, output_file: Path) -> bool:
        """Compress file using gzip"""
        try:
            import gzip
            with open(input_file, 'rb') as f_in:
                with gzip.open(output_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            return True
        except Exception as e:
            logger.error(f"[BACKUP_ENCRYPTION] Compression failed: {e}")
            return False
    
    def decrypt_backup(self, backup_id: str, output_path: Optional[Path] = None) -> Tuple[bool, bytes, str]:
        """Decrypt backup for restoration"""
        
        logger.info(f"[BACKUP_ENCRYPTION] Decrypting backup: {backup_id}")
        
        try:
            # Load encrypted backup
            encrypted_file = Path(self.config.encrypted_backup_path) / f"{backup_id}.encrypted"
            if not encrypted_file.exists():
                raise FileNotFoundError(f"Encrypted backup not found: {backup_id}")
            
            # Load metadata
            metadata = self._load_backup_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup metadata not found: {backup_id}")
            
            # Load encrypted container
            with open(encrypted_file, 'r', encoding='utf-8') as f:
                container = json.load(f)
            
            # Extract encryption parameters
            nonce = base64.b64decode(container['nonce'])
            aad = base64.b64decode(container['aad'])
            encrypted_data = base64.b64decode(container['encrypted_data'])
            
            # Get appropriate key based on backup type
            key_type = metadata.backup_type.lower()
            if key_type == 'database':
                key = self._backup_keys['database']
            elif key_type in ['documents', 'system']:
                key = self._backup_keys[key_type]
            else:
                key = self._backup_keys['archive']
            
            # Decrypt data
            cipher = ChaCha20Poly1305(key)
            decrypted_data = cipher.decrypt(nonce, encrypted_data, aad)
            
            # Verify integrity
            decrypted_hash = hashlib.sha256(decrypted_data).hexdigest()
            if decrypted_hash != container['original_hash']:
                raise ValueError("Backup integrity verification failed")
            
            # Decompress if needed
            if container.get('compression') == 'gzip':
                import gzip
                decrypted_data = gzip.decompress(decrypted_data)
            
            # Write to output file if specified
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(decrypted_data)
                os.chmod(output_path, 0o600)
            
            # Log successful decryption
            self._log_backup_event('BACKUP_DECRYPTED', {
                'backup_id': backup_id,
                'backup_type': metadata.backup_type,
                'decrypted_size': len(decrypted_data)
            })
            
            logger.info(f"[BACKUP_ENCRYPTION] Backup decrypted successfully: {backup_id}")
            
            return True, decrypted_data, ""
            
        except Exception as e:
            error_msg = f"Backup decryption failed for {backup_id}: {str(e)}"
            logger.error(f"[BACKUP_ENCRYPTION] {error_msg}", exc_info=True)
            
            self._log_backup_event('BACKUP_DECRYPTION_FAILED', {
                'backup_id': backup_id,
                'error': str(e)
            })
            
            return False, b"", error_msg
    
    def test_backup_restoration(self, backup_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Test backup restoration without actually restoring"""
        
        logger.info(f"[BACKUP_ENCRYPTION] Testing backup restoration: {backup_id}")
        
        test_results = {
            'backup_id': backup_id,
            'test_started_at': datetime.utcnow().isoformat(),
            'decryption_successful': False,
            'integrity_verified': False,
            'data_readable': False,
            'metadata_valid': False,
            'test_duration_seconds': 0,
            'errors': []
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Test 1: Load and validate metadata
            metadata = self._load_backup_metadata(backup_id)
            if metadata:
                test_results['metadata_valid'] = True
            else:
                test_results['errors'].append("Metadata not found or invalid")
            
            # Test 2: Decrypt backup
            success, decrypted_data, error = self.decrypt_backup(backup_id)
            if success:
                test_results['decryption_successful'] = True
                test_results['integrity_verified'] = True
                
                # Test 3: Validate data is readable
                if len(decrypted_data) > 0:
                    test_results['data_readable'] = True
                    
                    # For database backups, try to parse SQL
                    if metadata and metadata.backup_type == 'DATABASE':
                        try:
                            data_str = decrypted_data.decode('utf-8')
                            if 'CREATE TABLE' in data_str or 'INSERT INTO' in data_str:
                                test_results['sql_valid'] = True
                            else:
                                test_results['errors'].append("Decrypted data doesn't appear to be valid SQL")
                        except UnicodeDecodeError:
                            test_results['errors'].append("Decrypted data is not valid text")
                else:
                    test_results['errors'].append("Decrypted data is empty")
            else:
                test_results['errors'].append(f"Decryption failed: {error}")
            
            # Calculate test duration
            end_time = datetime.utcnow()
            test_results['test_duration_seconds'] = (end_time - start_time).total_seconds()
            test_results['test_completed_at'] = end_time.isoformat()
            
            # Overall test result
            overall_success = (
                test_results['metadata_valid'] and 
                test_results['decryption_successful'] and 
                test_results['integrity_verified'] and 
                test_results['data_readable']
            )
            
            test_results['overall_success'] = overall_success
            
            # Update metadata verification status
            if metadata and overall_success:
                metadata.verification_status = 'VERIFIED'
                self._save_backup_metadata(backup_id, metadata)
            elif metadata:
                metadata.verification_status = 'FAILED'
                self._save_backup_metadata(backup_id, metadata)
            
            # Log test results
            self._log_backup_event('BACKUP_RESTORATION_TEST', test_results)
            
            logger.info(f"[BACKUP_ENCRYPTION] Backup restoration test completed: {backup_id} - Success: {overall_success}")
            
            return overall_success, test_results
            
        except Exception as e:
            test_results['errors'].append(f"Test failed with exception: {str(e)}")
            test_results['test_completed_at'] = datetime.utcnow().isoformat()
            test_results['overall_success'] = False
            
            logger.error(f"[BACKUP_ENCRYPTION] Backup restoration test failed: {backup_id} - {e}", exc_info=True)
            
            return False, test_results
    
    def rotate_backup_keys(self) -> Dict[str, bool]:
        """Rotate all backup encryption keys"""
        
        logger.info("[BACKUP_ENCRYPTION] Starting backup key rotation")
        
        rotation_results = {}
        
        for key_type in ['database', 'documents', 'system', 'archive']:
            try:
                # Generate new key
                new_key = ChaCha20Poly1305.generate_key()
                
                # Backup old key
                old_key_backup = Path(self.config.backup_key_path) / f"backup_{key_type}_old_{datetime.utcnow().strftime('%Y%m%d')}.key"
                key_file = Path(self.config.backup_key_path) / f"backup_{key_type}.key"
                
                if key_file.exists():
                    # Backup old key
                    with open(key_file, 'rb') as f:
                        old_key = f.read()
                    with open(old_key_backup, 'wb') as f:
                        f.write(old_key)
                    os.chmod(old_key_backup, 0o600)
                
                # Write new key
                with open(key_file, 'wb') as f:
                    f.write(new_key)
                os.chmod(key_file, 0o600)
                
                # Update in-memory keys
                self._backup_keys[key_type] = new_key
                
                rotation_results[key_type] = True
                
                logger.info(f"[BACKUP_ENCRYPTION] Key rotated successfully: {key_type}")
                
            except Exception as e:
                logger.error(f"[BACKUP_ENCRYPTION] Key rotation failed for {key_type}: {e}")
                rotation_results[key_type] = False
        
        # Log rotation event
        self._log_backup_event('BACKUP_KEY_ROTATION', {
            'rotation_date': datetime.utcnow().isoformat(),
            'rotated_keys': list(rotation_results.keys()),
            'successful_rotations': sum(rotation_results.values()),
            'failed_rotations': len(rotation_results) - sum(rotation_results.values())
        })
        
        self._key_rotation_log.append({
            'rotation_date': datetime.utcnow(),
            'results': rotation_results
        })
        
        logger.info(f"[BACKUP_ENCRYPTION] Key rotation completed: {sum(rotation_results.values())}/{len(rotation_results)} successful")
        
        return rotation_results
    
    def list_backups(self) -> List[BackupMetadata]:
        """List all available backups with metadata"""
        backups = []
        metadata_dir = Path("backup/metadata")
        
        if metadata_dir.exists():
            for metadata_file in metadata_dir.glob("*_backup_metadata.json"):
                try:
                    backup_id = metadata_file.stem.replace('_backup_metadata', '')
                    metadata = self._load_backup_metadata(backup_id)
                    if metadata:
                        backups.append(metadata)
                except Exception as e:
                    logger.error(f"[BACKUP_ENCRYPTION] Error loading backup metadata: {e}")
        
        return backups
    
    def _save_backup_metadata(self, backup_id: str, metadata: BackupMetadata):
        """Save backup metadata"""
        metadata_dir = Path("backup/metadata")
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / f"{backup_id}_backup_metadata.json"
        
        # Convert to dict for JSON serialization
        metadata_dict = asdict(metadata)
        metadata_dict['created_at'] = metadata.created_at.isoformat()
        metadata_dict['encrypted_at'] = metadata.encrypted_at.isoformat()
        metadata_dict['retention_until'] = metadata.retention_until.isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        os.chmod(metadata_file, 0o600)
    
    def _load_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Load backup metadata"""
        metadata_file = Path("backup/metadata") / f"{backup_id}_backup_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            
            # Convert ISO strings back to datetime
            metadata_dict['created_at'] = datetime.fromisoformat(metadata_dict['created_at'])
            metadata_dict['encrypted_at'] = datetime.fromisoformat(metadata_dict['encrypted_at'])
            metadata_dict['retention_until'] = datetime.fromisoformat(metadata_dict['retention_until'])
            
            return BackupMetadata(**metadata_dict)
        except Exception as e:
            logger.error(f"[BACKUP_ENCRYPTION] Error loading metadata for {backup_id}: {e}")
            return None
    
    def _log_backup_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log backup encryption events for audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'service': 'backup_encryption_service',
            'event_data': event_data,
            'compliance_audit': True,
            'backup_encryption': True
        }
        
        logger.info(f"[BACKUP_ENCRYPTION_AUDIT] {json.dumps(log_entry)}")

# Global backup encryption service instance
backup_encryption_service = BackupEncryptionService()

__all__ = [
    'BackupEncryptionService',
    'BackupEncryptionConfig', 
    'BackupMetadata',
    'backup_encryption_service'
]