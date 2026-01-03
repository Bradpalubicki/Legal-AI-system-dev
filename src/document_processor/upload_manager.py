"""
Bulk document upload manager with support for multiple file formats, batch processing, and progress tracking.
"""
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import os
import uuid
import shutil
import asyncio
from pathlib import Path
import mimetypes
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

from ..shared.database.models import Case, User, Document
from ..shared.database.connection import get_db
from ..shared.utils.file_storage import FileStorageManager


class UploadStatus(Enum):
    """Status of document upload."""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    QUARANTINED = "quarantined"


class FileType(Enum):
    """Supported file types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    RTF = "rtf"
    HTML = "html"
    XML = "xml"
    TIFF = "tiff"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    ZIP = "zip"
    RAR = "rar"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    EML = "eml"
    MSG = "msg"


class ProcessingPriority(Enum):
    """Processing priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class UploadConfig:
    """Upload configuration settings."""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_batch_size: int = 50
    allowed_file_types: List[FileType] = field(default_factory=lambda: list(FileType))
    scan_for_viruses: bool = True
    extract_metadata: bool = True
    auto_categorize: bool = True
    create_thumbnails: bool = True
    ocr_scanned_documents: bool = True
    concurrent_uploads: int = 5
    chunk_size: int = 8192
    temp_directory: str = "/tmp/legal_uploads"
    storage_directory: str = "/storage/documents"
    quarantine_directory: str = "/storage/quarantine"


@dataclass
class FileInfo:
    """Information about an uploaded file."""
    file_id: str
    original_filename: str
    file_size: int
    file_type: FileType
    mime_type: str
    file_hash: str
    upload_timestamp: datetime
    temp_path: Optional[str] = None
    final_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UploadBatch:
    """Batch of files being uploaded together."""
    batch_id: str
    case_id: str
    user_id: str
    files: List[FileInfo]
    status: UploadStatus
    priority: ProcessingPriority
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UploadProgress:
    """Upload progress information."""
    batch_id: str
    total_files: int
    completed_files: int
    failed_files: int
    current_file: Optional[str]
    bytes_uploaded: int
    total_bytes: int
    status: UploadStatus
    estimated_completion: Optional[datetime]
    processing_stage: str
    error_details: List[Dict[str, Any]] = field(default_factory=list)


class UploadManager:
    """Manages bulk document uploads with batch processing."""
    
    def __init__(self, config: UploadConfig):
        self.config = config
        self.file_storage = FileStorageManager()
        self.active_batches: Dict[str, UploadBatch] = {}
        self.upload_progress: Dict[str, UploadProgress] = {}
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=config.concurrent_uploads)
        
        # Ensure directories exist
        os.makedirs(config.temp_directory, exist_ok=True)
        os.makedirs(config.storage_directory, exist_ok=True)
        os.makedirs(config.quarantine_directory, exist_ok=True)

    async def create_upload_batch(
        self, 
        case_id: str, 
        user_id: str,
        priority: ProcessingPriority = ProcessingPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new upload batch."""
        try:
            batch_id = str(uuid.uuid4())
            
            batch = UploadBatch(
                batch_id=batch_id,
                case_id=case_id,
                user_id=user_id,
                files=[],
                status=UploadStatus.PENDING,
                priority=priority,
                created_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self.active_batches[batch_id] = batch
            
            # Initialize progress tracking
            self.upload_progress[batch_id] = UploadProgress(
                batch_id=batch_id,
                total_files=0,
                completed_files=0,
                failed_files=0,
                current_file=None,
                bytes_uploaded=0,
                total_bytes=0,
                status=UploadStatus.PENDING,
                estimated_completion=None,
                processing_stage="initialized"
            )
            
            return batch_id
            
        except Exception as e:
            print(f"Error creating upload batch: {e}")
            raise

    async def add_file_to_batch(
        self, 
        batch_id: str, 
        file_data: bytes, 
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """Add a file to an existing batch."""
        try:
            if batch_id not in self.active_batches:
                raise ValueError(f"Batch {batch_id} not found")
            
            batch = self.active_batches[batch_id]
            
            if batch.status != UploadStatus.PENDING:
                raise ValueError(f"Cannot add files to batch in status: {batch.status.value}")
            
            if len(batch.files) >= self.config.max_batch_size:
                raise ValueError(f"Batch size limit exceeded ({self.config.max_batch_size})")
            
            # Validate file
            file_info = await self._validate_and_process_file(
                file_data, filename, content_type
            )
            
            # Add to batch
            batch.files.append(file_info)
            
            # Update progress
            progress = self.upload_progress[batch_id]
            progress.total_files = len(batch.files)
            progress.total_bytes += file_info.file_size
            
            return file_info.file_id
            
        except Exception as e:
            print(f"Error adding file to batch: {e}")
            raise

    async def _validate_and_process_file(
        self, 
        file_data: bytes, 
        filename: str, 
        content_type: Optional[str] = None
    ) -> FileInfo:
        """Validate and process uploaded file."""
        try:
            # Check file size
            if len(file_data) > self.config.max_file_size:
                raise ValueError(f"File size exceeds limit: {len(file_data)} > {self.config.max_file_size}")
            
            # Determine file type
            file_extension = Path(filename).suffix.lower().lstrip('.')
            
            try:
                file_type = FileType(file_extension)
            except ValueError:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            if file_type not in self.config.allowed_file_types:
                raise ValueError(f"File type not allowed: {file_type.value}")
            
            # Generate file ID and hash
            file_id = str(uuid.uuid4())
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Determine MIME type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or "application/octet-stream"
            
            # Save to temporary location
            temp_path = os.path.join(
                self.config.temp_directory, 
                f"{file_id}_{filename}"
            )
            
            with open(temp_path, 'wb') as f:
                f.write(file_data)
            
            # Create file info
            file_info = FileInfo(
                file_id=file_id,
                original_filename=filename,
                file_size=len(file_data),
                file_type=file_type,
                mime_type=content_type,
                file_hash=file_hash,
                upload_timestamp=datetime.utcnow(),
                temp_path=temp_path
            )
            
            # Extract basic metadata
            if self.config.extract_metadata:
                file_info.metadata = await self._extract_basic_metadata(temp_path, file_info)
            
            return file_info
            
        except Exception as e:
            print(f"Error validating file: {e}")
            raise

    async def _extract_basic_metadata(self, file_path: str, file_info: FileInfo) -> Dict[str, Any]:
        """Extract basic metadata from file."""
        try:
            metadata = {
                "file_size": file_info.file_size,
                "file_type": file_info.file_type.value,
                "upload_timestamp": file_info.upload_timestamp.isoformat(),
                "file_hash": file_info.file_hash
            }
            
            # Get file stats
            stat = os.stat(file_path)
            metadata.update({
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            })
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}

    async def start_batch_processing(self, batch_id: str) -> bool:
        """Start processing a batch of uploaded files."""
        try:
            if batch_id not in self.active_batches:
                raise ValueError(f"Batch {batch_id} not found")
            
            batch = self.active_batches[batch_id]
            
            if batch.status != UploadStatus.PENDING:
                raise ValueError(f"Batch not in pending status: {batch.status.value}")
            
            if not batch.files:
                raise ValueError("No files in batch to process")
            
            # Update status
            batch.status = UploadStatus.PROCESSING
            progress = self.upload_progress[batch_id]
            progress.status = UploadStatus.PROCESSING
            progress.processing_stage = "starting"
            
            # Add to processing queue
            await self.processing_queue.put(batch_id)
            
            # Start processing task
            asyncio.create_task(self._process_batch(batch_id))
            
            return True
            
        except Exception as e:
            print(f"Error starting batch processing: {e}")
            
            # Update status to failed
            if batch_id in self.active_batches:
                self.active_batches[batch_id].status = UploadStatus.FAILED
                self.active_batches[batch_id].error_message = str(e)
            
            if batch_id in self.upload_progress:
                self.upload_progress[batch_id].status = UploadStatus.FAILED
            
            return False

    async def _process_batch(self, batch_id: str):
        """Process all files in a batch."""
        try:
            batch = self.active_batches[batch_id]
            progress = self.upload_progress[batch_id]
            
            print(f"Starting batch processing: {batch_id}")
            
            # Process each file
            completed_files = 0
            failed_files = 0
            
            for i, file_info in enumerate(batch.files):
                try:
                    progress.current_file = file_info.original_filename
                    progress.processing_stage = f"processing_file_{i+1}_of_{len(batch.files)}"
                    
                    # Process individual file
                    success = await self._process_individual_file(batch, file_info)
                    
                    if success:
                        completed_files += 1
                        progress.bytes_uploaded += file_info.file_size
                    else:
                        failed_files += 1
                        progress.error_details.append({
                            "file": file_info.original_filename,
                            "error": "Processing failed",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    progress.completed_files = completed_files
                    progress.failed_files = failed_files
                    progress.progress = (completed_files + failed_files) / len(batch.files) * 100
                    
                    # Estimate completion time
                    if completed_files > 0:
                        elapsed = datetime.utcnow() - batch.created_at
                        estimated_total = elapsed * len(batch.files) / (completed_files + failed_files)
                        progress.estimated_completion = batch.created_at + estimated_total
                    
                except Exception as e:
                    print(f"Error processing file {file_info.original_filename}: {e}")
                    failed_files += 1
                    progress.failed_files = failed_files
                    progress.error_details.append({
                        "file": file_info.original_filename,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Update final status
            if failed_files == 0:
                batch.status = UploadStatus.COMPLETED
                progress.status = UploadStatus.COMPLETED
                progress.processing_stage = "completed"
            elif completed_files > 0:
                batch.status = UploadStatus.COMPLETED  # Partial success
                progress.status = UploadStatus.COMPLETED
                progress.processing_stage = "completed_with_errors"
            else:
                batch.status = UploadStatus.FAILED
                progress.status = UploadStatus.FAILED
                progress.processing_stage = "failed"
            
            batch.completed_at = datetime.utcnow()
            progress.current_file = None
            
            print(f"Batch processing completed: {batch_id}, Success: {completed_files}, Failed: {failed_files}")
            
        except Exception as e:
            print(f"Error in batch processing: {e}")
            
            batch.status = UploadStatus.FAILED
            batch.error_message = str(e)
            batch.completed_at = datetime.utcnow()
            
            progress.status = UploadStatus.FAILED
            progress.processing_stage = "error"

    async def _process_individual_file(self, batch: UploadBatch, file_info: FileInfo) -> bool:
        """Process an individual file."""
        try:
            print(f"Processing file: {file_info.original_filename}")
            
            # Security scan
            if self.config.scan_for_viruses:
                if not await self._security_scan(file_info):
                    await self._quarantine_file(file_info)
                    return False
            
            # Move to permanent storage
            final_path = await self._move_to_storage(batch, file_info)
            file_info.final_path = final_path
            
            # Extract detailed metadata
            if self.config.extract_metadata:
                detailed_metadata = await self._extract_detailed_metadata(file_info)
                file_info.metadata.update(detailed_metadata)
            
            # Create thumbnails
            if self.config.create_thumbnails:
                await self._create_thumbnails(file_info)
            
            # OCR processing for scanned documents
            if self.config.ocr_scanned_documents and self._needs_ocr(file_info):
                await self._perform_ocr(file_info)
            
            # Auto-categorization
            if self.config.auto_categorize:
                await self._auto_categorize_document(file_info)
            
            # Create database record
            await self._create_document_record(batch, file_info)
            
            # Clean up temp file
            if file_info.temp_path and os.path.exists(file_info.temp_path):
                os.remove(file_info.temp_path)
                file_info.temp_path = None
            
            return True
            
        except Exception as e:
            print(f"Error processing individual file: {e}")
            return False

    async def _security_scan(self, file_info: FileInfo) -> bool:
        """Perform security scan on file."""
        try:
            # Basic security checks
            
            # Check file size (already done, but double-check)
            if file_info.file_size > self.config.max_file_size:
                return False
            
            # Check for suspicious file patterns
            suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.com', '.pif']
            if any(file_info.original_filename.lower().endswith(ext) for ext in suspicious_extensions):
                return False
            
            # Check for embedded executables (basic check)
            if file_info.temp_path:
                with open(file_info.temp_path, 'rb') as f:
                    content = f.read(1024)  # Check first 1KB
                    
                    # Look for PE header (Windows executable)
                    if b'MZ' in content[:2] or b'\x7fELF' in content[:4]:
                        return False
            
            # In production, integrate with antivirus API
            # For now, assume all files pass
            return True
            
        except Exception as e:
            print(f"Error in security scan: {e}")
            return False

    async def _quarantine_file(self, file_info: FileInfo):
        """Move suspicious file to quarantine."""
        try:
            if not file_info.temp_path:
                return
            
            quarantine_path = os.path.join(
                self.config.quarantine_directory,
                f"{file_info.file_id}_{file_info.original_filename}"
            )
            
            shutil.move(file_info.temp_path, quarantine_path)
            file_info.temp_path = None
            file_info.metadata['quarantined'] = True
            file_info.metadata['quarantine_path'] = quarantine_path
            file_info.metadata['quarantine_timestamp'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            print(f"Error quarantining file: {e}")

    async def _move_to_storage(self, batch: UploadBatch, file_info: FileInfo) -> str:
        """Move file to permanent storage."""
        try:
            if not file_info.temp_path:
                raise ValueError("No temporary file to move")
            
            # Create storage path
            date_path = datetime.utcnow().strftime('%Y/%m/%d')
            storage_subdir = os.path.join(
                self.config.storage_directory,
                batch.case_id,
                date_path
            )
            
            os.makedirs(storage_subdir, exist_ok=True)
            
            # Generate final filename
            final_filename = f"{file_info.file_id}_{file_info.original_filename}"
            final_path = os.path.join(storage_subdir, final_filename)
            
            # Move file
            shutil.move(file_info.temp_path, final_path)
            file_info.temp_path = None
            
            return final_path
            
        except Exception as e:
            print(f"Error moving file to storage: {e}")
            raise

    async def _extract_detailed_metadata(self, file_info: FileInfo) -> Dict[str, Any]:
        """Extract detailed metadata from file."""
        try:
            metadata = {}
            
            if file_info.file_type == FileType.PDF:
                metadata.update(await self._extract_pdf_metadata(file_info.final_path))
            elif file_info.file_type in [FileType.DOCX, FileType.DOC]:
                metadata.update(await self._extract_office_metadata(file_info.final_path))
            elif file_info.file_type in [FileType.JPG, FileType.JPEG, FileType.PNG, FileType.TIFF]:
                metadata.update(await self._extract_image_metadata(file_info.final_path))
            elif file_info.file_type in [FileType.EML, FileType.MSG]:
                metadata.update(await self._extract_email_metadata(file_info.final_path))
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting detailed metadata: {e}")
            return {}

    async def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file."""
        try:
            # This would use a PDF library like PyPDF2 or pdfplumber
            metadata = {
                "document_type": "pdf",
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # Placeholder for actual PDF metadata extraction
            # In production, would extract:
            # - Page count
            # - Author, title, subject
            # - Creation/modification dates
            # - Text content
            # - Form fields
            # - Digital signatures
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
            return {}

    async def _extract_office_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Office documents."""
        try:
            # This would use python-docx or similar libraries
            metadata = {
                "document_type": "office_document",
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # Placeholder for actual Office metadata extraction
            # In production, would extract:
            # - Document properties
            # - Author, company, comments
            # - Creation/modification dates
            # - Page/word count
            # - Revision information
            # - Text content
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting Office metadata: {e}")
            return {}

    async def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from image files."""
        try:
            # This would use PIL/Pillow or similar
            metadata = {
                "document_type": "image",
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # Placeholder for actual image metadata extraction
            # In production, would extract:
            # - Image dimensions
            # - Color mode, format
            # - EXIF data
            # - Creation date
            # - Camera information
            # - GPS coordinates
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting image metadata: {e}")
            return {}

    async def _extract_email_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from email files."""
        try:
            # This would use email library for EML or win32com for MSG
            metadata = {
                "document_type": "email",
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # Placeholder for actual email metadata extraction
            # In production, would extract:
            # - From, To, CC, BCC
            # - Subject, date sent/received
            # - Message ID, thread ID
            # - Attachments list
            # - Headers
            # - Body text/HTML
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting email metadata: {e}")
            return {}

    async def _create_thumbnails(self, file_info: FileInfo):
        """Create thumbnails for supported file types."""
        try:
            if file_info.file_type in [FileType.PDF, FileType.JPG, FileType.JPEG, FileType.PNG, FileType.TIFF]:
                # Placeholder for thumbnail creation
                # In production, would create multiple sizes:
                # - Small (150x150)
                # - Medium (300x300)
                # - Large (600x600)
                
                thumbnail_dir = os.path.join(
                    os.path.dirname(file_info.final_path),
                    "thumbnails"
                )
                os.makedirs(thumbnail_dir, exist_ok=True)
                
                file_info.metadata['has_thumbnails'] = True
                file_info.metadata['thumbnail_directory'] = thumbnail_dir
                
        except Exception as e:
            print(f"Error creating thumbnails: {e}")

    def _needs_ocr(self, file_info: FileInfo) -> bool:
        """Determine if file needs OCR processing."""
        return file_info.file_type in [
            FileType.PDF, FileType.TIFF, FileType.PNG, FileType.JPG, FileType.JPEG
        ]

    async def _perform_ocr(self, file_info: FileInfo):
        """Perform OCR on scanned documents."""
        try:
            # Placeholder for OCR processing
            # In production, would use Tesseract or cloud OCR service
            
            ocr_text = "Placeholder OCR text content"  # Would be actual extracted text
            
            file_info.metadata.update({
                'ocr_performed': True,
                'ocr_timestamp': datetime.utcnow().isoformat(),
                'extracted_text': ocr_text,
                'ocr_confidence': 0.95  # Would be actual confidence score
            })
            
        except Exception as e:
            print(f"Error performing OCR: {e}")
            file_info.metadata['ocr_error'] = str(e)

    async def _auto_categorize_document(self, file_info: FileInfo):
        """Auto-categorize document based on content and metadata."""
        try:
            # Placeholder for auto-categorization
            # In production, would use ML models or rule-based classification
            
            categories = []
            
            # Basic categorization based on filename
            filename_lower = file_info.original_filename.lower()
            
            if any(term in filename_lower for term in ['contract', 'agreement', 'mou']):
                categories.append('contracts')
            elif any(term in filename_lower for term in ['motion', 'brief', 'pleading']):
                categories.append('pleadings')
            elif any(term in filename_lower for term in ['discovery', 'interrogatory', 'deposition']):
                categories.append('discovery')
            elif any(term in filename_lower for term in ['evidence', 'exhibit']):
                categories.append('evidence')
            elif any(term in filename_lower for term in ['correspondence', 'letter', 'email']):
                categories.append('correspondence')
            else:
                categories.append('general')
            
            file_info.metadata.update({
                'auto_categories': categories,
                'categorization_timestamp': datetime.utcnow().isoformat(),
                'categorization_confidence': 0.8
            })
            
        except Exception as e:
            print(f"Error in auto-categorization: {e}")

    async def _create_document_record(self, batch: UploadBatch, file_info: FileInfo):
        """Create database record for processed document."""
        try:
            # This would create a Document record in the database
            # For now, just add to metadata
            
            file_info.metadata.update({
                'database_record_created': True,
                'case_id': batch.case_id,
                'uploaded_by': batch.user_id,
                'batch_id': batch.batch_id,
                'document_created_at': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f"Error creating document record: {e}")

    async def get_batch_progress(self, batch_id: str) -> Optional[UploadProgress]:
        """Get current progress of a batch."""
        return self.upload_progress.get(batch_id)

    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel batch processing."""
        try:
            if batch_id not in self.active_batches:
                return False
            
            batch = self.active_batches[batch_id]
            
            if batch.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                return False
            
            batch.status = UploadStatus.CANCELLED
            
            if batch_id in self.upload_progress:
                self.upload_progress[batch_id].status = UploadStatus.CANCELLED
                self.upload_progress[batch_id].processing_stage = "cancelled"
            
            # Clean up temp files
            for file_info in batch.files:
                if file_info.temp_path and os.path.exists(file_info.temp_path):
                    os.remove(file_info.temp_path)
            
            return True
            
        except Exception as e:
            print(f"Error cancelling batch: {e}")
            return False

    async def retry_failed_files(self, batch_id: str) -> bool:
        """Retry processing failed files in a batch."""
        try:
            if batch_id not in self.active_batches:
                return False
            
            batch = self.active_batches[batch_id]
            
            if batch.status != UploadStatus.FAILED:
                return False
            
            # Reset status and retry
            batch.status = UploadStatus.PROCESSING
            
            progress = self.upload_progress[batch_id]
            progress.status = UploadStatus.PROCESSING
            progress.processing_stage = "retrying"
            progress.failed_files = 0
            progress.error_details = []
            
            # Start processing again
            asyncio.create_task(self._process_batch(batch_id))
            
            return True
            
        except Exception as e:
            print(f"Error retrying failed files: {e}")
            return False

    async def get_batch_summary(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive summary of a batch."""
        try:
            if batch_id not in self.active_batches:
                return None
            
            batch = self.active_batches[batch_id]
            progress = self.upload_progress.get(batch_id)
            
            return {
                "batch_id": batch_id,
                "case_id": batch.case_id,
                "user_id": batch.user_id,
                "status": batch.status.value,
                "priority": batch.priority.value,
                "created_at": batch.created_at.isoformat(),
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                "total_files": len(batch.files),
                "file_types": list(set(f.file_type.value for f in batch.files)),
                "total_size": sum(f.file_size for f in batch.files),
                "progress": {
                    "completed_files": progress.completed_files if progress else 0,
                    "failed_files": progress.failed_files if progress else 0,
                    "progress_percentage": progress.progress if progress else 0,
                    "current_stage": progress.processing_stage if progress else "unknown",
                    "estimated_completion": progress.estimated_completion.isoformat() if progress and progress.estimated_completion else None
                },
                "error_message": batch.error_message,
                "metadata": batch.metadata
            }
            
        except Exception as e:
            print(f"Error getting batch summary: {e}")
            return None

    async def cleanup_old_batches(self, days_old: int = 7):
        """Clean up old completed/failed batches."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            batches_to_remove = []
            
            for batch_id, batch in self.active_batches.items():
                if (batch.status in [UploadStatus.COMPLETED, UploadStatus.FAILED, UploadStatus.CANCELLED] and
                    batch.created_at < cutoff_date):
                    
                    # Clean up any remaining temp files
                    for file_info in batch.files:
                        if file_info.temp_path and os.path.exists(file_info.temp_path):
                            os.remove(file_info.temp_path)
                    
                    batches_to_remove.append(batch_id)
            
            # Remove from memory
            for batch_id in batches_to_remove:
                del self.active_batches[batch_id]
                if batch_id in self.upload_progress:
                    del self.upload_progress[batch_id]
            
            print(f"Cleaned up {len(batches_to_remove)} old batches")
            
        except Exception as e:
            print(f"Error cleaning up old batches: {e}")

    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get upload system statistics."""
        try:
            total_batches = len(self.active_batches)
            
            status_counts = {}
            for status in UploadStatus:
                status_counts[status.value] = sum(
                    1 for batch in self.active_batches.values() 
                    if batch.status == status
                )
            
            total_files = sum(len(batch.files) for batch in self.active_batches.values())
            total_size = sum(
                sum(f.file_size for f in batch.files)
                for batch in self.active_batches.values()
            )
            
            file_type_counts = {}
            for batch in self.active_batches.values():
                for file_info in batch.files:
                    file_type = file_info.file_type.value
                    file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
            
            return {
                "total_batches": total_batches,
                "status_distribution": status_counts,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "file_type_distribution": file_type_counts,
                "processing_queue_size": self.processing_queue.qsize(),
                "temp_directory": self.config.temp_directory,
                "storage_directory": self.config.storage_directory,
                "concurrent_uploads": self.config.concurrent_uploads
            }
            
        except Exception as e:
            print(f"Error getting system statistics: {e}")
            return {}