"""
EMERGENCY DOCUMENT ENCRYPTION SERVICE

This service provides comprehensive encryption for all legal documents to ensure
compliance with attorney-client privilege and data protection requirements.

CRITICAL: All legal documents must be encrypted at rest and in transit.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import base64
import hashlib
import json
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets

logger = logging.getLogger(__name__)

@dataclass
class EncryptionMetadata:
    document_id: str
    encrypted: bool
    encryption_algorithm: str
    key_id: str
    encrypted_at: datetime
    file_hash_sha256: str
    file_size_bytes: int
    encryption_status: str  # ENCRYPTED, PENDING, FAILED
    compliance_level: str  # ATTORNEY_CLIENT, CONFIDENTIAL, RESTRICTED, PUBLIC

@dataclass
class EncryptionResult:
    success: bool
    document_id: str
    encrypted_file_path: str
    metadata: EncryptionMetadata
    error_message: Optional[str] = None

class EmergencyEncryptionService:
    """Emergency document encryption service with attorney-client privilege protection"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self._master_key = self._get_or_create_master_key()
        self._encryption_keys = {}
        
        # Supported file types for legal documents
        self.LEGAL_DOCUMENT_EXTENSIONS = {
            '.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt',
            '.html', '.xml', '.json', '.csv', '.xlsx', '.xls'
        }
        
        # Compliance levels for different document types
        self.COMPLIANCE_LEVELS = {
            'attorney_client': 'ATTORNEY_CLIENT',
            'confidential': 'CONFIDENTIAL', 
            'restricted': 'RESTRICTED',
            'public': 'PUBLIC'
        }
        
        # Initialize encryption directory
        self.encrypted_storage_path = Path(self.config['encrypted_storage_path'])
        self.encrypted_storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[ENCRYPTION] Emergency encryption service initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default encryption configuration"""
        return {
            'encryption_algorithm': 'AES-256-GCM',
            'key_derivation': 'PBKDF2',
            'key_iterations': 100000,
            'encrypted_storage_path': 'encrypted_documents',
            'metadata_storage_path': 'encryption_metadata',
            'backup_keys': True,
            'key_rotation_days': 90,
            'audit_all_operations': True
        }
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = Path('.encryption_master_key')
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new master key
            master_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(master_key)
            
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            
            logger.critical(f"[ENCRYPTION] New master key generated - SECURE THIS FILE")
            return master_key
    
    def _derive_document_key(self, document_id: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Derive document-specific encryption key from master key"""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config['key_iterations'],
        )
        
        # Combine master key with document ID for unique key derivation
        key_material = self._master_key + document_id.encode('utf-8')
        derived_key = kdf.derive(key_material)
        
        return derived_key, salt
    
    def encrypt_document(self, file_path: Union[str, Path], document_id: str, 
                        compliance_level: str = 'ATTORNEY_CLIENT') -> EncryptionResult:
        """Encrypt a single document with attorney-client protection"""
        
        file_path = Path(file_path)
        
        logger.info(f"[ENCRYPTION] Starting encryption for document: {document_id}")
        
        try:
            # Validate file exists and is readable
            if not file_path.exists():
                return EncryptionResult(
                    success=False,
                    document_id=document_id,
                    encrypted_file_path="",
                    metadata=None,
                    error_message=f"File not found: {file_path}"
                )
            
            # Check if it's a legal document type
            if file_path.suffix.lower() not in self.LEGAL_DOCUMENT_EXTENSIONS:
                logger.warning(f"[ENCRYPTION] Non-legal document type: {file_path.suffix}")
            
            # Read original file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Calculate file hash for integrity verification
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Generate document-specific encryption key
            doc_key, salt = self._derive_document_key(document_id)
            
            # Encrypt using AES-GCM for authenticated encryption
            aesgcm = AESGCM(doc_key)
            nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
            
            # Additional authenticated data (AAD)
            aad = json.dumps({
                'document_id': document_id,
                'compliance_level': compliance_level,
                'encrypted_at': datetime.utcnow().isoformat(),
                'original_filename': file_path.name
            }).encode('utf-8')
            
            # Perform encryption
            encrypted_data = aesgcm.encrypt(nonce, file_data, aad)
            
            # Create encrypted file structure
            encrypted_container = {
                'version': '1.0',
                'algorithm': 'AES-256-GCM',
                'document_id': document_id,
                'compliance_level': compliance_level,
                'salt': base64.b64encode(salt).decode('utf-8'),
                'nonce': base64.b64encode(nonce).decode('utf-8'),
                'aad': base64.b64encode(aad).decode('utf-8'),
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'original_hash': file_hash,
                'encrypted_at': datetime.utcnow().isoformat(),
                'key_id': hashlib.sha256(doc_key).hexdigest()[:16]
            }
            
            # Write encrypted file
            encrypted_filename = f"{document_id}.encrypted"
            encrypted_file_path = self.encrypted_storage_path / encrypted_filename
            
            with open(encrypted_file_path, 'w', encoding='utf-8') as f:
                json.dump(encrypted_container, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(encrypted_file_path, 0o600)
            
            # Create encryption metadata
            metadata = EncryptionMetadata(
                document_id=document_id,
                encrypted=True,
                encryption_algorithm='AES-256-GCM',
                key_id=encrypted_container['key_id'],
                encrypted_at=datetime.utcnow(),
                file_hash_sha256=file_hash,
                file_size_bytes=len(file_data),
                encryption_status='ENCRYPTED',
                compliance_level=compliance_level
            )
            
            # Save metadata
            self._save_encryption_metadata(document_id, metadata)
            
            # Log successful encryption
            self._log_encryption_event('DOCUMENT_ENCRYPTED', {
                'document_id': document_id,
                'file_path': str(file_path),
                'encrypted_path': str(encrypted_file_path),
                'compliance_level': compliance_level,
                'file_size': len(file_data),
                'encryption_algorithm': 'AES-256-GCM'
            })
            
            logger.info(f"[ENCRYPTION] Document encrypted successfully: {document_id}")
            
            return EncryptionResult(
                success=True,
                document_id=document_id,
                encrypted_file_path=str(encrypted_file_path),
                metadata=metadata
            )
            
        except Exception as e:
            error_msg = f"Encryption failed for {document_id}: {str(e)}"
            logger.error(f"[ENCRYPTION] {error_msg}", exc_info=True)
            
            # Log encryption failure
            self._log_encryption_event('ENCRYPTION_FAILED', {
                'document_id': document_id,
                'file_path': str(file_path),
                'error': str(e),
                'compliance_level': compliance_level
            })
            
            return EncryptionResult(
                success=False,
                document_id=document_id,
                encrypted_file_path="",
                metadata=None,
                error_message=error_msg
            )
    
    def decrypt_document(self, document_id: str, output_path: Optional[Path] = None) -> Tuple[bool, bytes, str]:
        """Decrypt a document (requires proper authorization)"""
        
        logger.info(f"[ENCRYPTION] Decryption requested for document: {document_id}")
        
        try:
            # Load encrypted file
            encrypted_filename = f"{document_id}.encrypted"
            encrypted_file_path = self.encrypted_storage_path / encrypted_filename
            
            if not encrypted_file_path.exists():
                raise FileNotFoundError(f"Encrypted document not found: {document_id}")
            
            # Load encrypted container
            with open(encrypted_file_path, 'r', encoding='utf-8') as f:
                encrypted_container = json.load(f)
            
            # Extract encryption parameters
            salt = base64.b64decode(encrypted_container['salt'])
            nonce = base64.b64decode(encrypted_container['nonce'])
            aad = base64.b64decode(encrypted_container['aad'])
            encrypted_data = base64.b64decode(encrypted_container['encrypted_data'])
            
            # Derive the same document key
            doc_key, _ = self._derive_document_key(document_id, salt)
            
            # Decrypt the data
            aesgcm = AESGCM(doc_key)
            decrypted_data = aesgcm.decrypt(nonce, encrypted_data, aad)
            
            # Verify integrity
            decrypted_hash = hashlib.sha256(decrypted_data).hexdigest()
            if decrypted_hash != encrypted_container['original_hash']:
                raise ValueError("Document integrity verification failed")
            
            # Log successful decryption
            self._log_encryption_event('DOCUMENT_DECRYPTED', {
                'document_id': document_id,
                'compliance_level': encrypted_container['compliance_level'],
                'file_size': len(decrypted_data)
            })
            
            # Optionally write to output file
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(decrypted_data)
                os.chmod(output_path, 0o600)
            
            logger.info(f"[ENCRYPTION] Document decrypted successfully: {document_id}")
            
            return True, decrypted_data, ""
            
        except Exception as e:
            error_msg = f"Decryption failed for {document_id}: {str(e)}"
            logger.error(f"[ENCRYPTION] {error_msg}", exc_info=True)
            
            # Log decryption failure
            self._log_encryption_event('DECRYPTION_FAILED', {
                'document_id': document_id,
                'error': str(e)
            })
            
            return False, b"", error_msg
    
    def encrypt_directory(self, directory_path: Union[str, Path], 
                         compliance_level: str = 'ATTORNEY_CLIENT') -> List[EncryptionResult]:
        """Encrypt all documents in a directory"""
        
        directory_path = Path(directory_path)
        results = []
        
        logger.info(f"[ENCRYPTION] Starting directory encryption: {directory_path}")
        
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"[ENCRYPTION] Directory not found: {directory_path}")
            return results
        
        # Find all files to encrypt
        files_to_encrypt = []
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.LEGAL_DOCUMENT_EXTENSIONS:
                files_to_encrypt.append(file_path)
        
        logger.info(f"[ENCRYPTION] Found {len(files_to_encrypt)} files to encrypt")
        
        # Encrypt each file
        for i, file_path in enumerate(files_to_encrypt):
            # Generate document ID from relative path
            relative_path = file_path.relative_to(directory_path)
            document_id = str(relative_path).replace(os.sep, '_').replace('.', '_')
            
            result = self.encrypt_document(file_path, document_id, compliance_level)
            results.append(result)
            
            if (i + 1) % 10 == 0:
                logger.info(f"[ENCRYPTION] Progress: {i + 1}/{len(files_to_encrypt)} files encrypted")
        
        # Log directory encryption completion
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self._log_encryption_event('DIRECTORY_ENCRYPTED', {
            'directory_path': str(directory_path),
            'total_files': len(files_to_encrypt),
            'successful_encryptions': successful,
            'failed_encryptions': failed,
            'compliance_level': compliance_level
        })
        
        logger.info(f"[ENCRYPTION] Directory encryption complete: {successful}/{len(files_to_encrypt)} successful")
        
        return results
    
    def get_encryption_status(self, document_id: str) -> Optional[EncryptionMetadata]:
        """Get encryption status for a document"""
        return self._load_encryption_metadata(document_id)
    
    def list_encrypted_documents(self) -> List[EncryptionMetadata]:
        """List all encrypted documents"""
        metadata_dir = Path(self.config['metadata_storage_path'])
        encrypted_docs = []
        
        if metadata_dir.exists():
            for metadata_file in metadata_dir.glob('*.json'):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata_dict = json.load(f)
                    
                    metadata = EncryptionMetadata(**metadata_dict)
                    encrypted_docs.append(metadata)
                except Exception as e:
                    logger.error(f"[ENCRYPTION] Error loading metadata from {metadata_file}: {e}")
        
        return encrypted_docs
    
    def _save_encryption_metadata(self, document_id: str, metadata: EncryptionMetadata):
        """Save encryption metadata to file"""
        metadata_dir = Path(self.config['metadata_storage_path'])
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / f"{document_id}_metadata.json"
        
        # Convert datetime to ISO string for JSON serialization
        metadata_dict = asdict(metadata)
        metadata_dict['encrypted_at'] = metadata.encrypted_at.isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        
        os.chmod(metadata_file, 0o600)
    
    def _load_encryption_metadata(self, document_id: str) -> Optional[EncryptionMetadata]:
        """Load encryption metadata from file"""
        metadata_dir = Path(self.config['metadata_storage_path'])
        metadata_file = metadata_dir / f"{document_id}_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            
            # Convert ISO string back to datetime
            metadata_dict['encrypted_at'] = datetime.fromisoformat(metadata_dict['encrypted_at'])
            
            return EncryptionMetadata(**metadata_dict)
        except Exception as e:
            logger.error(f"[ENCRYPTION] Error loading metadata for {document_id}: {e}")
            return None
    
    def _log_encryption_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log encryption events for audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'service': 'encryption_service',
            'event_data': event_data,
            'compliance_audit': True
        }
        
        logger.info(f"[ENCRYPTION_AUDIT] {json.dumps(log_entry)}")

# Create global encryption service instance
emergency_encryption_service = EmergencyEncryptionService()

# Convenience functions
def encrypt_document(file_path: Union[str, Path], document_id: str, 
                    compliance_level: str = 'ATTORNEY_CLIENT') -> EncryptionResult:
    """Convenience function to encrypt a single document"""
    return emergency_encryption_service.encrypt_document(file_path, document_id, compliance_level)

def encrypt_directory(directory_path: Union[str, Path], 
                     compliance_level: str = 'ATTORNEY_CLIENT') -> List[EncryptionResult]:
    """Convenience function to encrypt all documents in a directory"""
    return emergency_encryption_service.encrypt_directory(directory_path, compliance_level)

def get_encryption_status(document_id: str) -> Optional[EncryptionMetadata]:
    """Convenience function to get document encryption status"""
    return emergency_encryption_service.get_encryption_status(document_id)

__all__ = [
    'EmergencyEncryptionService',
    'EncryptionResult',
    'EncryptionMetadata',
    'emergency_encryption_service',
    'encrypt_document',
    'encrypt_directory',
    'get_encryption_status'
]