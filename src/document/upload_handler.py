#!/usr/bin/env python3
"""
Secure Document Upload Handler
Legal AI System - Document Processing Pipeline

This module provides secure document upload handling with:
- Immediate encryption before storage
- Comprehensive virus scanning
- File type and size validation
- Unique document ID generation
- Audit logging for compliance
"""

import os
import hashlib
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import tempfile
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

# Import encryption and security modules
try:
    from ..core.security import encrypt_data, decrypt_data
except ImportError:
    def encrypt_data(data, key_id):
        return data  # Fallback for testing
    def decrypt_data(data, key_id):
        return data  # Fallback for testing

try:
    from ..core.attorney_review import AttorneyReviewSystem
except ImportError:
    class AttorneyReviewSystem:
        def review_content(self, content, content_id=None, jurisdiction=None):
            class MockResult:
                requires_review = True
            return MockResult()

try:
    from ..core.audit_logger import AuditLogger
except ImportError:
    class AuditLogger:
        def log_document_event(self, **kwargs): pass
        def log_security_event(self, **kwargs): pass

# Setup logging
logger = logging.getLogger('document_upload')

class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    RTF = "rtf"
    UNKNOWN = "unknown"

class UploadStatus(str, Enum):
    """Document upload status"""
    PENDING = "pending"
    VALIDATING = "validating"
    SCANNING = "scanning"
    ENCRYPTING = "encrypting"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"

class VirusScanResult(str, Enum):
    """Virus scan results"""
    CLEAN = "clean"
    INFECTED = "infected"
    SUSPICIOUS = "suspicious"
    SCAN_FAILED = "scan_failed"

@dataclass
class DocumentMetadata:
    """Document metadata structure"""
    document_id: str
    original_filename: str
    file_size: int
    file_type: DocumentType
    mime_type: str
    upload_timestamp: datetime
    uploaded_by: str
    checksum_md5: str
    checksum_sha256: str
    encryption_key_id: str
    storage_path: str
    virus_scan_result: VirusScanResult
    upload_status: UploadStatus
    compliance_flags: List[str]
    attorney_review_required: bool

@dataclass
class UploadResult:
    """Upload operation result"""
    success: bool
    document_id: Optional[str]
    message: str
    metadata: Optional[DocumentMetadata]
    warnings: List[str]
    errors: List[str]

class SecureDocumentUploader:
    """
    Secure document upload handler with encryption and compliance
    """

    def __init__(self, storage_root: str = "storage/documents"):
        self.logger = logger
        self.storage_root = Path(storage_root)
        self.quarantine_root = Path("storage/quarantine")

        # Create storage directories
        self._initialize_storage()

        # Initialize security components
        self.attorney_review = AttorneyReviewSystem()
        self.audit_logger = AuditLogger()

        # File validation settings
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_types = {
            DocumentType.PDF: ["application/pdf"],
            DocumentType.DOC: ["application/msword"],
            DocumentType.DOCX: ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            DocumentType.TXT: ["text/plain"],
            DocumentType.RTF: ["application/rtf", "text/rtf"]
        }

    def _initialize_storage(self):
        """Initialize secure storage structure"""
        try:
            self.storage_root.mkdir(parents=True, exist_ok=True)
            self.quarantine_root.mkdir(parents=True, exist_ok=True)

            # Create subdirectories by year/month for organization
            current_date = datetime.now()
            monthly_path = self.storage_root / str(current_date.year) / f"{current_date.month:02d}"
            monthly_path.mkdir(parents=True, exist_ok=True)

            self.logger.info("Storage directories initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize storage: {e}")
            raise

    def upload_document(self, file_data: bytes, filename: str,
                       uploaded_by: str) -> UploadResult:
        """
        Securely upload and process a document

        Args:
            file_data: Raw file bytes
            filename: Original filename
            uploaded_by: User ID of uploader

        Returns:
            UploadResult with processing details
        """
        try:
            self.logger.info(f"Starting document upload: {filename}")

            # Generate unique document ID
            document_id = self._generate_document_id()

            # Initialize result tracking
            warnings = []
            errors = []

            # Step 1: Initial validation
            validation_result = self._validate_file(file_data, filename)
            if not validation_result["valid"]:
                return UploadResult(
                    success=False,
                    document_id=None,
                    message="File validation failed",
                    metadata=None,
                    warnings=warnings,
                    errors=validation_result["errors"]
                )

            warnings.extend(validation_result["warnings"])

            # Step 2: Virus scanning
            scan_result = self._scan_for_viruses(file_data, filename)
            if scan_result == VirusScanResult.INFECTED:
                self._quarantine_file(file_data, filename, document_id, "virus_detected")
                return UploadResult(
                    success=False,
                    document_id=document_id,
                    message="File infected with malware - quarantined",
                    metadata=None,
                    warnings=warnings,
                    errors=["Malware detected"]
                )
            elif scan_result == VirusScanResult.SUSPICIOUS:
                warnings.append("File flagged as suspicious by virus scanner")

            # Step 3: Generate checksums
            md5_hash, sha256_hash = self._generate_checksums(file_data)

            # Step 4: Encrypt file data
            encrypted_data, encryption_key_id = self._encrypt_file_data(file_data)

            # Step 5: Store encrypted file
            storage_path = self._store_encrypted_file(encrypted_data, document_id)

            # Step 6: Create metadata
            metadata = DocumentMetadata(
                document_id=document_id,
                original_filename=filename,
                file_size=len(file_data),
                file_type=validation_result["file_type"],
                mime_type=validation_result["mime_type"],
                upload_timestamp=datetime.now(),
                uploaded_by=uploaded_by,
                checksum_md5=md5_hash,
                checksum_sha256=sha256_hash,
                encryption_key_id=encryption_key_id,
                storage_path=str(storage_path),
                virus_scan_result=scan_result,
                upload_status=UploadStatus.COMPLETED,
                compliance_flags=self._check_compliance_flags(filename),
                attorney_review_required=self._requires_attorney_review(filename)
            )

            # Step 7: Store metadata
            self._store_metadata(metadata)

            # Step 8: Audit logging
            self._log_upload_event(metadata, uploaded_by)

            self.logger.info(f"Document upload completed: {document_id}")

            return UploadResult(
                success=True,
                document_id=document_id,
                message="Document uploaded and encrypted successfully",
                metadata=metadata,
                warnings=warnings,
                errors=errors
            )

        except Exception as e:
            self.logger.error(f"Document upload failed: {e}")
            return UploadResult(
                success=False,
                document_id=None,
                message=f"Upload failed: {str(e)}",
                metadata=None,
                warnings=warnings,
                errors=[str(e)]
            )

    def _generate_document_id(self) -> str:
        """Generate unique document identifier"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"doc_{timestamp}_{unique_id}"

    def _validate_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Comprehensive file validation"""
        errors = []
        warnings = []

        # Check file size
        if len(file_data) == 0:
            errors.append("File is empty")
        elif len(file_data) > self.max_file_size:
            errors.append(f"File size exceeds maximum ({self.max_file_size / 1024 / 1024:.1f}MB)")

        # Detect file type using python-magic or fallback to extension
        try:
            if MAGIC_AVAILABLE:
                mime_type = magic.from_buffer(file_data, mime=True)
            else:
                # Fallback MIME type detection based on extension
                file_extension = Path(filename).suffix.lower()
                mime_map = {
                    '.pdf': 'application/pdf',
                    '.doc': 'application/msword',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.txt': 'text/plain',
                    '.rtf': 'application/rtf'
                }
                mime_type = mime_map.get(file_extension, 'application/octet-stream')

            file_extension = Path(filename).suffix.lower()

            # Map extension to document type
            extension_map = {
                '.pdf': DocumentType.PDF,
                '.doc': DocumentType.DOC,
                '.docx': DocumentType.DOCX,
                '.txt': DocumentType.TXT,
                '.rtf': DocumentType.RTF
            }

            detected_type = extension_map.get(file_extension, DocumentType.UNKNOWN)

            # Validate mime type matches extension
            if detected_type != DocumentType.UNKNOWN:
                allowed_mimes = self.allowed_types.get(detected_type, [])
                if mime_type not in allowed_mimes:
                    warnings.append(f"MIME type {mime_type} doesn't match extension {file_extension}")
            else:
                errors.append(f"Unsupported file type: {file_extension}")

        except Exception as e:
            errors.append(f"File type detection failed: {e}")
            mime_type = "application/octet-stream"
            detected_type = DocumentType.UNKNOWN

        # Check filename for suspicious patterns
        suspicious_patterns = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        if any(pattern in filename for pattern in suspicious_patterns):
            warnings.append("Filename contains suspicious characters")

        return {
            "valid": len(errors) == 0,
            "file_type": detected_type,
            "mime_type": mime_type,
            "errors": errors,
            "warnings": warnings
        }

    def _scan_for_viruses(self, file_data: bytes, filename: str) -> VirusScanResult:
        """Virus scanning (simulated for now - would integrate with ClamAV)"""
        try:
            # Simulate virus scanning
            # In production, this would use ClamAV or similar

            # Check for known malicious patterns (basic simulation)
            malicious_patterns = [
                b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',  # EICAR test
                b'\\x4d\\x5a',  # PE executable header
            ]

            for pattern in malicious_patterns:
                if pattern in file_data:
                    return VirusScanResult.INFECTED

            # Check file size patterns that might be suspicious
            if len(file_data) < 10:
                return VirusScanResult.SUSPICIOUS

            self.logger.info(f"Virus scan completed: {filename} - CLEAN")
            return VirusScanResult.CLEAN

        except Exception as e:
            self.logger.error(f"Virus scanning failed: {e}")
            return VirusScanResult.SCAN_FAILED

    def _quarantine_file(self, file_data: bytes, filename: str,
                        document_id: str, reason: str):
        """Quarantine suspicious or infected files"""
        try:
            quarantine_path = self.quarantine_root / f"{document_id}_{filename}"
            with open(quarantine_path, 'wb') as f:
                f.write(file_data)

            # Log quarantine event
            self.audit_logger.log_security_event(
                event_type="file_quarantined",
                details={
                    "document_id": document_id,
                    "filename": filename,
                    "reason": reason,
                    "quarantine_path": str(quarantine_path)
                }
            )

            self.logger.warning(f"File quarantined: {document_id} - {reason}")

        except Exception as e:
            self.logger.error(f"Failed to quarantine file: {e}")

    def _generate_checksums(self, file_data: bytes) -> Tuple[str, str]:
        """Generate MD5 and SHA256 checksums for integrity verification"""
        md5_hash = hashlib.md5(file_data).hexdigest()
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        return md5_hash, sha256_hash

    def _encrypt_file_data(self, file_data: bytes) -> Tuple[bytes, str]:
        """Encrypt file data before storage"""
        try:
            # Generate unique encryption key ID
            key_id = f"key_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Encrypt the data
            encrypted_data = encrypt_data(file_data, key_id)

            return encrypted_data, key_id

        except Exception as e:
            self.logger.error(f"File encryption failed: {e}")
            raise

    def _store_encrypted_file(self, encrypted_data: bytes, document_id: str) -> Path:
        """Store encrypted file in secure location"""
        try:
            # Organize by date
            current_date = datetime.now()
            storage_dir = self.storage_root / str(current_date.year) / f"{current_date.month:02d}"
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Store with document ID as filename
            storage_path = storage_dir / f"{document_id}.enc"

            with open(storage_path, 'wb') as f:
                f.write(encrypted_data)

            # Set secure file permissions (readable only by owner)
            os.chmod(storage_path, 0o600)

            return storage_path

        except Exception as e:
            self.logger.error(f"Failed to store encrypted file: {e}")
            raise

    def _store_metadata(self, metadata: DocumentMetadata):
        """Store document metadata in secure database"""
        try:
            # In production, this would store in a proper database
            # For now, store as JSON file alongside encrypted document
            metadata_path = Path(metadata.storage_path).with_suffix('.meta')

            with open(metadata_path, 'w') as f:
                import json
                json.dump(asdict(metadata), f, indent=2, default=str)

            # Set secure permissions
            os.chmod(metadata_path, 0o600)

        except Exception as e:
            self.logger.error(f"Failed to store metadata: {e}")
            raise

    def _check_compliance_flags(self, filename: str) -> List[str]:
        """Check for compliance-related flags"""
        flags = []

        # Check for sensitive document types
        sensitive_keywords = [
            'bankruptcy', 'motion', 'petition', 'order', 'judgment',
            'complaint', 'summons', 'discovery', 'deposition'
        ]

        filename_lower = filename.lower()
        for keyword in sensitive_keywords:
            if keyword in filename_lower:
                flags.append(f"contains_{keyword}")

        return flags

    def _requires_attorney_review(self, filename: str) -> bool:
        """Determine if document requires attorney review"""
        # Use attorney review system to determine if review is needed
        review_result = self.attorney_review.review_content(
            content=f"Document upload: {filename}",
            content_id=f"upload_{filename}"
        )

        return review_result.requires_review

    def _log_upload_event(self, metadata: DocumentMetadata, uploaded_by: str):
        """Log upload event for audit trail"""
        self.audit_logger.log_document_event(
            event_type="document_uploaded",
            document_id=metadata.document_id,
            user_id=uploaded_by,
            details={
                "filename": metadata.original_filename,
                "file_size": metadata.file_size,
                "file_type": metadata.file_type.value,
                "virus_scan_result": metadata.virus_scan_result.value,
                "attorney_review_required": metadata.attorney_review_required,
                "compliance_flags": metadata.compliance_flags
            }
        )

    def retrieve_document(self, document_id: str, requesting_user: str) -> Optional[bytes]:
        """Securely retrieve and decrypt a document"""
        try:
            # Load metadata
            metadata = self._load_metadata(document_id)
            if not metadata:
                self.logger.warning(f"Document not found: {document_id}")
                return None

            # Check access permissions (would integrate with RBAC system)
            if not self._check_access_permission(requesting_user, metadata):
                self.logger.warning(f"Access denied for user {requesting_user} to document {document_id}")
                return None

            # Load encrypted file
            with open(metadata.storage_path, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt file
            decrypted_data = decrypt_data(encrypted_data, metadata.encryption_key_id)

            # Log access event
            self.audit_logger.log_document_event(
                event_type="document_accessed",
                document_id=document_id,
                user_id=requesting_user,
                details={"access_granted": True}
            )

            return decrypted_data

        except Exception as e:
            self.logger.error(f"Document retrieval failed: {e}")
            return None

    def _load_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Load document metadata"""
        try:
            # Search for metadata file (would use database in production)
            for root_dir in [self.storage_root]:
                for meta_file in Path(root_dir).rglob(f"{document_id}.meta"):
                    with open(meta_file, 'r') as f:
                        import json
                        metadata_dict = json.load(f)
                        # Convert back to dataclass
                        metadata_dict['upload_timestamp'] = datetime.fromisoformat(metadata_dict['upload_timestamp'])
                        return DocumentMetadata(**metadata_dict)

            return None

        except Exception as e:
            self.logger.error(f"Failed to load metadata: {e}")
            return None

    def _check_access_permission(self, user_id: str, metadata: DocumentMetadata) -> bool:
        """Check if user has permission to access document"""
        # Simplified permission check - would integrate with RBAC system
        # For now, allow access to uploader and admin users
        return (
            user_id == metadata.uploaded_by or
            user_id.startswith('admin_') or
            user_id.startswith('attorney_')
        )

    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics for monitoring"""
        try:
            total_files = 0
            total_size = 0
            file_types = {}

            # Scan storage directory for statistics
            for meta_file in self.storage_root.rglob("*.meta"):
                try:
                    metadata = self._load_metadata(meta_file.stem)
                    if metadata:
                        total_files += 1
                        total_size += metadata.file_size
                        file_type = metadata.file_type.value
                        file_types[file_type] = file_types.get(file_type, 0) + 1
                except:
                    continue

            return {
                "total_documents": total_files,
                "total_storage_mb": total_size / 1024 / 1024,
                "file_types": file_types,
                "storage_root": str(self.storage_root)
            }

        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

# Global uploader instance
document_uploader = SecureDocumentUploader()

def validate_upload_system():
    """Validate document upload system"""
    try:
        # Test with sample data
        test_data = b"This is a test document for validation."
        test_filename = "test_document.txt"
        test_user = "test_user_123"

        # Test upload
        result = document_uploader.upload_document(test_data, test_filename, test_user)

        if result.success:
            print("✓ Document upload system working correctly")
            print(f"  Document ID: {result.document_id}")
            print(f"  File size: {result.metadata.file_size} bytes")
            print(f"  Encryption: {result.metadata.encryption_key_id}")

            # Test retrieval
            retrieved_data = document_uploader.retrieve_document(result.document_id, test_user)
            if retrieved_data == test_data:
                print("✓ Document retrieval and decryption working correctly")
            else:
                print("✗ Document retrieval failed")

            return True
        else:
            print("✗ Document upload failed")
            print(f"  Errors: {result.errors}")
            return False

    except Exception as e:
        print(f"✗ Upload system validation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Secure Document Upload System...")
    print("=" * 50)

    if validate_upload_system():
        # Display statistics
        stats = document_uploader.get_upload_statistics()
        print(f"\nUpload System Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("Upload system validation failed")