"""
Document and File Migration Module

Handles secure migration of documents and files with:
- Encryption and re-encryption
- Integrity verification
- Metadata preservation
- Storage optimization
- Access permission migration
"""

import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
import tempfile
import zipfile

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import magic
from PIL import Image
import pymupdf  # PyMuPDF for PDF handling
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)

@dataclass
class DocumentMigrationStats:
    """Statistics for document migration"""
    total_files: int = 0
    migrated_files: int = 0
    failed_files: int = 0
    total_size_bytes: int = 0
    migrated_size_bytes: int = 0
    encrypted_files: int = 0
    compressed_files: int = 0
    deduplicated_files: int = 0
    metadata_records: int = 0
    permission_records: int = 0
    errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentInfo:
    """Information about a document"""
    file_path: Path
    original_path: Path
    file_size: int
    file_hash: str
    mime_type: str
    file_extension: str
    metadata: Dict[str, Any]
    encryption_status: str = "none"  # none, encrypted, re-encrypted
    compression_ratio: float = 1.0
    owner_id: Optional[int] = None
    permissions: List[str] = field(default_factory=list)

class DocumentMigrator:
    """
    Comprehensive document and file migration system

    Features:
    - Multi-source file discovery and migration
    - Encryption with key rotation support
    - File deduplication
    - Metadata extraction and preservation
    - Access permission migration
    - Storage optimization
    - Integrity verification
    """

    def __init__(self,
                 target_db_url: str,
                 target_storage_path: str,
                 encryption_key: Optional[str] = None,
                 enable_compression: bool = True,
                 enable_deduplication: bool = True):

        self.target_db_url = target_db_url
        self.target_storage_path = Path(target_storage_path)
        self.enable_compression = enable_compression
        self.enable_deduplication = enable_deduplication

        # Initialize encryption
        self.encryption_key = None
        if encryption_key:
            self.encryption_key = Fernet(encryption_key.encode())

        # Create target storage directory
        self.target_storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize file hash cache for deduplication
        self.file_hash_cache: Dict[str, Path] = {}

        # Initialize statistics
        self.stats = DocumentMigrationStats()

    async def migrate_documents_comprehensive(self,
                                            source_storage_paths: List[str],
                                            source_databases: Dict[str, str]) -> DocumentMigrationStats:
        """
        Comprehensive document migration from multiple sources

        Args:
            source_storage_paths: List of storage directory paths
            source_databases: Dict of database names to paths containing document metadata

        Returns:
            DocumentMigrationStats: Complete migration statistics
        """
        logger.info("Starting comprehensive document migration...")

        try:
            # Phase 1: Discovery and inventory
            await self._discover_and_inventory_files(source_storage_paths, source_databases)

            # Phase 2: Prepare target storage structure
            await self._prepare_target_storage()

            # Phase 3: Migrate files with encryption and optimization
            await self._migrate_files()

            # Phase 4: Migrate document metadata
            await self._migrate_document_metadata(source_databases)

            # Phase 5: Migrate access permissions
            await self._migrate_access_permissions(source_databases)

            # Phase 6: Verify migration integrity
            await self._verify_migration_integrity()

            # Phase 7: Optimize storage
            await self._optimize_storage()

            logger.info(f"Document migration completed successfully: {self.stats}")

        except Exception as e:
            logger.error(f"Document migration failed: {str(e)}")
            raise

        return self.stats

    async def _discover_and_inventory_files(self,
                                          source_paths: List[str],
                                          source_databases: Dict[str, str]):
        """Discover and inventory all files to be migrated"""
        logger.info("Discovering and inventorying files...")

        self.discovered_files: List[DocumentInfo] = []

        # Discover files from storage directories
        for storage_path in source_paths:
            if not os.path.exists(storage_path):
                logger.warning(f"Storage path not found: {storage_path}")
                continue

            await self._discover_files_in_directory(Path(storage_path))

        # Discover files referenced in databases
        for db_name, db_path in source_databases.items():
            await self._discover_files_in_database(db_name, db_path)

        self.stats.total_files = len(self.discovered_files)
        self.stats.total_size_bytes = sum(doc.file_size for doc in self.discovered_files)

        logger.info(f"Discovered {self.stats.total_files} files ({self.stats.total_size_bytes / 1024 / 1024:.1f}MB)")

    async def _discover_files_in_directory(self, directory_path: Path):
        """Discover files recursively in a directory"""
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = Path(root) / file

                try:
                    doc_info = await self._create_document_info(file_path)
                    self.discovered_files.append(doc_info)

                    if len(self.discovered_files) % 1000 == 0:
                        logger.info(f"Discovered {len(self.discovered_files)} files...")

                except Exception as e:
                    logger.error(f"Failed to process file {file_path}: {str(e)}")
                    self.stats.errors.append(f"Discovery failed for {file_path}: {str(e)}")

    async def _discover_files_in_database(self, db_name: str, db_path: str):
        """Discover files referenced in database records"""
        if not os.path.exists(db_path):
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Find tables that might contain file references
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            for table_name in tables:
                # Get table schema
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]

                # Look for file-related columns
                file_columns = [col for col in columns if any(
                    keyword in col.lower() for keyword in
                    ['file', 'path', 'document', 'attachment', 'upload']
                )]

                if file_columns:
                    await self._extract_file_references(conn, table_name, file_columns)

        finally:
            conn.close()

    async def _extract_file_references(self, conn, table_name: str, file_columns: List[str]):
        """Extract file references from database table"""
        for column in file_columns:
            cursor = conn.execute(f"SELECT DISTINCT {column} FROM {table_name} WHERE {column} IS NOT NULL")

            for row in cursor.fetchall():
                file_ref = row[0]
                if file_ref and isinstance(file_ref, str):
                    # Try to resolve file path
                    potential_paths = [
                        Path(file_ref),
                        Path('./storage') / file_ref,
                        Path('./documents') / file_ref,
                        Path('./uploads') / file_ref
                    ]

                    for path in potential_paths:
                        if path.exists() and path.is_file():
                            try:
                                doc_info = await self._create_document_info(path)
                                # Add database context
                                doc_info.metadata['source_table'] = table_name
                                doc_info.metadata['source_column'] = column
                                self.discovered_files.append(doc_info)
                                break
                            except Exception as e:
                                logger.error(f"Failed to process database file {path}: {str(e)}")

    async def _create_document_info(self, file_path: Path) -> DocumentInfo:
        """Create comprehensive document information"""
        stat = file_path.stat()

        # Calculate file hash
        file_hash = await self._calculate_file_hash(file_path)

        # Determine MIME type
        mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'

        # Extract metadata based on file type
        metadata = await self._extract_file_metadata(file_path, mime_type)

        return DocumentInfo(
            file_path=file_path,
            original_path=file_path,
            file_size=stat.st_size,
            file_hash=file_hash,
            mime_type=mime_type,
            file_extension=file_path.suffix.lower(),
            metadata={
                'created_time': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                'size_bytes': stat.st_size,
                **metadata
            }
        )

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def _extract_file_metadata(self, file_path: Path, mime_type: str) -> Dict[str, Any]:
        """Extract metadata based on file type"""
        metadata = {}

        try:
            if mime_type.startswith('image/'):
                metadata.update(await self._extract_image_metadata(file_path))
            elif mime_type == 'application/pdf':
                metadata.update(await self._extract_pdf_metadata(file_path))
            elif mime_type.startswith('text/'):
                metadata.update(await self._extract_text_metadata(file_path))

            # Add file type detection
            if hasattr(magic, 'from_file'):
                file_type = magic.from_file(str(file_path))
                metadata['detected_type'] = file_type

        except Exception as e:
            logger.warning(f"Failed to extract metadata from {file_path}: {str(e)}")
            metadata['metadata_extraction_error'] = str(e)

        return metadata

    async def _extract_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract image metadata"""
        try:
            with Image.open(file_path) as img:
                return {
                    'image_width': img.width,
                    'image_height': img.height,
                    'image_mode': img.mode,
                    'image_format': img.format,
                    'has_exif': bool(getattr(img, '_getexif', lambda: None)())
                }
        except Exception:
            return {}

    async def _extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract PDF metadata"""
        try:
            doc = pymupdf.open(str(file_path))
            metadata = {
                'pdf_pages': doc.page_count,
                'pdf_title': doc.metadata.get('title', ''),
                'pdf_author': doc.metadata.get('author', ''),
                'pdf_subject': doc.metadata.get('subject', ''),
                'pdf_creator': doc.metadata.get('creator', ''),
                'pdf_encrypted': doc.needs_pass,
                'pdf_size_kb': file_path.stat().st_size // 1024
            }
            doc.close()
            return metadata
        except Exception:
            return {}

    async def _extract_text_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract text file metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return {
                    'text_length': len(content),
                    'text_lines': content.count('\n') + 1,
                    'text_words': len(content.split()),
                    'text_encoding': 'utf-8'
                }
        except Exception:
            return {}

    async def _prepare_target_storage(self):
        """Prepare target storage structure"""
        logger.info("Preparing target storage structure...")

        # Create organized directory structure
        storage_dirs = [
            'documents',
            'images',
            'pdfs',
            'archives',
            'temp',
            'encrypted',
            'metadata'
        ]

        for dir_name in storage_dirs:
            (self.target_storage_path / dir_name).mkdir(exist_ok=True)

        # Initialize storage database
        await self._initialize_storage_database()

    async def _initialize_storage_database(self):
        """Initialize storage tracking database"""
        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as conn:
                # Create storage tracking tables
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS migrated_documents (
                        id SERIAL PRIMARY KEY,
                        original_path TEXT NOT NULL,
                        target_path TEXT NOT NULL,
                        file_hash VARCHAR(64) UNIQUE NOT NULL,
                        file_size BIGINT NOT NULL,
                        mime_type VARCHAR(100),
                        encryption_status VARCHAR(20) DEFAULT 'none',
                        compression_ratio DECIMAL(5,3) DEFAULT 1.0,
                        metadata JSONB,
                        migrated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        verified_at TIMESTAMP WITH TIME ZONE,
                        owner_id INTEGER,
                        INDEX(file_hash),
                        INDEX(original_path),
                        INDEX(migrated_at)
                    )
                """))

                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS document_permissions (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES migrated_documents(id),
                        user_id INTEGER,
                        permission_type VARCHAR(50),
                        granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        granted_by INTEGER
                    )
                """))

                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS file_deduplication (
                        id SERIAL PRIMARY KEY,
                        file_hash VARCHAR(64) UNIQUE NOT NULL,
                        canonical_path TEXT NOT NULL,
                        duplicate_count INTEGER DEFAULT 1,
                        total_size_saved BIGINT DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))

        finally:
            await engine.dispose()

    async def _migrate_files(self):
        """Migrate all discovered files"""
        logger.info("Starting file migration...")

        # Process files in batches for memory efficiency
        batch_size = 100
        processed = 0

        for i in range(0, len(self.discovered_files), batch_size):
            batch = self.discovered_files[i:i + batch_size]

            # Process batch with limited concurrency
            semaphore = asyncio.Semaphore(10)
            tasks = [self._migrate_single_file(doc_info, semaphore) for doc_info in batch]

            await asyncio.gather(*tasks, return_exceptions=True)

            processed += len(batch)
            logger.info(f"Migrated {processed}/{self.stats.total_files} files...")

    async def _migrate_single_file(self, doc_info: DocumentInfo, semaphore: asyncio.Semaphore):
        """Migrate a single file with all optimizations"""
        async with semaphore:
            try:
                # Check for deduplication
                if self.enable_deduplication and doc_info.file_hash in self.file_hash_cache:
                    await self._handle_duplicate_file(doc_info)
                    return

                # Determine target path
                target_path = await self._determine_target_path(doc_info)

                # Copy/encrypt file
                if self.encryption_key:
                    await self._encrypt_and_copy_file(doc_info, target_path)
                else:
                    await self._copy_file(doc_info, target_path)

                # Compress if enabled and beneficial
                if self.enable_compression:
                    await self._compress_file_if_beneficial(doc_info, target_path)

                # Update document info with final path
                doc_info.file_path = target_path

                # Store in database
                await self._store_document_record(doc_info)

                # Update cache for deduplication
                if self.enable_deduplication:
                    self.file_hash_cache[doc_info.file_hash] = target_path

                self.stats.migrated_files += 1
                self.stats.migrated_size_bytes += doc_info.file_size

            except Exception as e:
                self.stats.failed_files += 1
                error_msg = f"Failed to migrate {doc_info.original_path}: {str(e)}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)

    async def _determine_target_path(self, doc_info: DocumentInfo) -> Path:
        """Determine target path for file based on type and organization"""
        # Organize by file type
        if doc_info.mime_type.startswith('image/'):
            base_dir = 'images'
        elif doc_info.mime_type == 'application/pdf':
            base_dir = 'pdfs'
        elif doc_info.mime_type.startswith('application/'):
            base_dir = 'documents'
        else:
            base_dir = 'documents'

        # Create date-based subdirectory
        now = datetime.now()
        date_dir = f"{now.year}/{now.month:02d}"

        target_dir = self.target_storage_path / base_dir / date_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        base_name = doc_info.original_path.stem
        extension = doc_info.original_path.suffix

        # Add hash prefix to avoid collisions
        hash_prefix = doc_info.file_hash[:8]
        target_filename = f"{hash_prefix}_{base_name}{extension}"

        return target_dir / target_filename

    async def _encrypt_and_copy_file(self, doc_info: DocumentInfo, target_path: Path):
        """Encrypt file during copy operation"""
        with open(doc_info.original_path, 'rb') as src_file:
            data = src_file.read()

            # Encrypt data
            encrypted_data = self.encryption_key.encrypt(data)

            with open(target_path, 'wb') as dest_file:
                dest_file.write(encrypted_data)

        doc_info.encryption_status = "encrypted"
        self.stats.encrypted_files += 1

    async def _copy_file(self, doc_info: DocumentInfo, target_path: Path):
        """Copy file without encryption"""
        shutil.copy2(doc_info.original_path, target_path)

    async def _compress_file_if_beneficial(self, doc_info: DocumentInfo, target_path: Path):
        """Compress file if it would result in significant space savings"""
        # Only compress certain file types
        compressible_types = [
            'text/', 'application/json', 'application/xml',
            'application/javascript', 'application/css'
        ]

        if not any(doc_info.mime_type.startswith(t) for t in compressible_types):
            return

        # Create compressed version
        compressed_path = target_path.with_suffix(target_path.suffix + '.gz')

        try:
            import gzip
            with open(target_path, 'rb') as src:
                with gzip.open(compressed_path, 'wb') as dest:
                    shutil.copyfileobj(src, dest)

            # Check if compression is beneficial (>20% reduction)
            original_size = target_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            compression_ratio = compressed_size / original_size

            if compression_ratio < 0.8:  # 20% or better compression
                # Replace original with compressed version
                target_path.unlink()
                compressed_path.rename(target_path)

                doc_info.compression_ratio = compression_ratio
                self.stats.compressed_files += 1

                logger.debug(f"Compressed {target_path.name}: {compression_ratio:.2%} of original size")
            else:
                # Remove compressed version, keep original
                compressed_path.unlink()

        except Exception as e:
            logger.warning(f"Compression failed for {target_path}: {str(e)}")
            if compressed_path.exists():
                compressed_path.unlink()

    async def _handle_duplicate_file(self, doc_info: DocumentInfo):
        """Handle duplicate file found during deduplication"""
        canonical_path = self.file_hash_cache[doc_info.file_hash]

        # Create symlink or reference instead of copying
        logger.info(f"Duplicate file detected: {doc_info.original_path} -> {canonical_path}")

        # Record deduplication
        engine = create_async_engine(self.target_db_url)
        try:
            async with engine.begin() as conn:
                await conn.execute(text("""
                    INSERT INTO file_deduplication (file_hash, canonical_path, duplicate_count, total_size_saved)
                    VALUES (:hash, :path, 1, :size)
                    ON CONFLICT (file_hash) DO UPDATE SET
                        duplicate_count = file_deduplication.duplicate_count + 1,
                        total_size_saved = file_deduplication.total_size_saved + :size
                """), {
                    'hash': doc_info.file_hash,
                    'path': str(canonical_path),
                    'size': doc_info.file_size
                })
        finally:
            await engine.dispose()

        self.stats.deduplicated_files += 1

    async def _store_document_record(self, doc_info: DocumentInfo):
        """Store document record in database"""
        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    INSERT INTO migrated_documents
                    (original_path, target_path, file_hash, file_size, mime_type,
                     encryption_status, compression_ratio, metadata, owner_id)
                    VALUES (:original_path, :target_path, :file_hash, :file_size,
                            :mime_type, :encryption_status, :compression_ratio, :metadata, :owner_id)
                    RETURNING id
                """), {
                    'original_path': str(doc_info.original_path),
                    'target_path': str(doc_info.file_path),
                    'file_hash': doc_info.file_hash,
                    'file_size': doc_info.file_size,
                    'mime_type': doc_info.mime_type,
                    'encryption_status': doc_info.encryption_status,
                    'compression_ratio': float(doc_info.compression_ratio),
                    'metadata': json.dumps(doc_info.metadata),
                    'owner_id': doc_info.owner_id
                })

                doc_id = result.scalar()
                doc_info.metadata['migrated_document_id'] = doc_id

        finally:
            await engine.dispose()

    async def _migrate_document_metadata(self, source_databases: Dict[str, str]):
        """Migrate document metadata from source databases"""
        logger.info("Migrating document metadata...")

        for db_name, db_path in source_databases.items():
            if not os.path.exists(db_path):
                continue

            await self._migrate_metadata_from_database(db_name, db_path)

    async def _migrate_metadata_from_database(self, db_name: str, db_path: str):
        """Migrate metadata from a specific database"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Look for document metadata tables
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            metadata_tables = [t for t in tables if any(
                keyword in t.lower() for keyword in
                ['document', 'file', 'metadata', 'attachment']
            )]

            for table_name in metadata_tables:
                await self._extract_metadata_from_table(conn, table_name)

        finally:
            conn.close()

    async def _extract_metadata_from_table(self, conn, table_name: str):
        """Extract metadata from a specific table"""
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            return

        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as pg_conn:
                for row in rows:
                    try:
                        row_dict = dict(row)

                        # Try to match with migrated documents
                        file_path = self._extract_file_path_from_row(row_dict)
                        if file_path:
                            await self._update_document_metadata(pg_conn, file_path, row_dict)

                        self.stats.metadata_records += 1

                    except Exception as e:
                        logger.error(f"Failed to process metadata row: {str(e)}")

        finally:
            await engine.dispose()

    def _extract_file_path_from_row(self, row_dict: Dict[str, Any]) -> Optional[str]:
        """Extract file path from database row"""
        path_fields = ['file_path', 'path', 'document_path', 'filename', 'file_name']

        for field in path_fields:
            if field in row_dict and row_dict[field]:
                return str(row_dict[field])

        return None

    async def _update_document_metadata(self, conn, file_path: str, metadata: Dict[str, Any]):
        """Update document metadata in the target database"""
        # Find document by original path
        result = await conn.execute(text("""
            SELECT id, metadata FROM migrated_documents
            WHERE original_path = :path OR original_path LIKE :path_pattern
        """), {
            'path': file_path,
            'path_pattern': f"%{Path(file_path).name}"
        })

        doc_record = result.fetchone()
        if doc_record:
            doc_id, existing_metadata = doc_record

            # Merge metadata
            if existing_metadata:
                merged_metadata = json.loads(existing_metadata)
            else:
                merged_metadata = {}

            merged_metadata.update({f"db_{k}": v for k, v in metadata.items()})

            # Update document record
            await conn.execute(text("""
                UPDATE migrated_documents
                SET metadata = :metadata
                WHERE id = :doc_id
            """), {
                'metadata': json.dumps(merged_metadata),
                'doc_id': doc_id
            })

    async def _migrate_access_permissions(self, source_databases: Dict[str, str]):
        """Migrate document access permissions"""
        logger.info("Migrating access permissions...")

        for db_name, db_path in source_databases.items():
            await self._migrate_permissions_from_database(db_name, db_path)

    async def _migrate_permissions_from_database(self, db_name: str, db_path: str):
        """Migrate permissions from a specific database"""
        if not os.path.exists(db_path):
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Look for permission-related tables
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            permission_tables = [t for t in tables if any(
                keyword in t.lower() for keyword in
                ['permission', 'access', 'share', 'owner']
            )]

            for table_name in permission_tables:
                await self._extract_permissions_from_table(conn, table_name)

        finally:
            conn.close()

    async def _extract_permissions_from_table(self, conn, table_name: str):
        """Extract permissions from a specific table"""
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            return

        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as pg_conn:
                for row in rows:
                    try:
                        row_dict = dict(row)
                        await self._store_document_permission(pg_conn, row_dict)
                        self.stats.permission_records += 1

                    except Exception as e:
                        logger.error(f"Failed to migrate permission: {str(e)}")

        finally:
            await engine.dispose()

    async def _store_document_permission(self, conn, permission_data: Dict[str, Any]):
        """Store document permission in target database"""
        # Extract relevant fields
        document_id = permission_data.get('document_id')
        user_id = permission_data.get('user_id')
        permission_type = permission_data.get('permission', 'read')

        if document_id and user_id:
            await conn.execute(text("""
                INSERT INTO document_permissions (document_id, user_id, permission_type)
                VALUES (:doc_id, :user_id, :permission)
                ON CONFLICT DO NOTHING
            """), {
                'doc_id': document_id,
                'user_id': user_id,
                'permission': permission_type
            })

    async def _verify_migration_integrity(self):
        """Verify the integrity of migrated documents"""
        logger.info("Verifying migration integrity...")

        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as conn:
                # Verify file count
                result = await conn.execute(text("SELECT COUNT(*) FROM migrated_documents"))
                db_count = result.scalar()

                logger.info(f"Database records: {db_count}, Migrated files: {self.stats.migrated_files}")

                # Verify file integrity (sample verification)
                sample_size = min(100, self.stats.migrated_files)
                result = await conn.execute(text("""
                    SELECT target_path, file_hash, file_size
                    FROM migrated_documents
                    ORDER BY RANDOM()
                    LIMIT :limit
                """), {'limit': sample_size})

                verified_count = 0
                for row in result.fetchall():
                    target_path, expected_hash, expected_size = row

                    if await self._verify_file_integrity(Path(target_path), expected_hash, expected_size):
                        verified_count += 1

                integrity_score = (verified_count / sample_size) * 100 if sample_size > 0 else 100
                logger.info(f"Integrity verification: {integrity_score:.1f}% ({verified_count}/{sample_size})")

                if integrity_score < 95:
                    raise Exception(f"Integrity verification failed: {integrity_score:.1f}%")

        finally:
            await engine.dispose()

    async def _verify_file_integrity(self, file_path: Path, expected_hash: str, expected_size: int) -> bool:
        """Verify individual file integrity"""
        try:
            if not file_path.exists():
                return False

            # Check size
            actual_size = file_path.stat().st_size
            if actual_size != expected_size:
                logger.warning(f"Size mismatch for {file_path}: expected {expected_size}, got {actual_size}")
                return False

            # For encrypted files, we can't verify hash directly
            # but we can verify the file can be read
            if self.encryption_key:
                try:
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                        self.encryption_key.decrypt(encrypted_data)
                    return True
                except Exception:
                    return False
            else:
                # Verify hash for non-encrypted files
                actual_hash = await self._calculate_file_hash(file_path)
                return actual_hash == expected_hash

        except Exception as e:
            logger.error(f"Failed to verify {file_path}: {str(e)}")
            return False

    async def _optimize_storage(self):
        """Optimize storage after migration"""
        logger.info("Optimizing storage...")

        # Generate storage statistics
        await self._generate_storage_statistics()

        # Clean up temporary files
        temp_dir = self.target_storage_path / 'temp'
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        # Create storage index for fast lookups
        await self._create_storage_indexes()

    async def _generate_storage_statistics(self):
        """Generate comprehensive storage statistics"""
        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as conn:
                # Storage by type
                result = await conn.execute(text("""
                    SELECT mime_type, COUNT(*) as count, SUM(file_size) as total_size
                    FROM migrated_documents
                    GROUP BY mime_type
                    ORDER BY total_size DESC
                """))

                storage_by_type = {}
                for row in result.fetchall():
                    mime_type, count, total_size = row
                    storage_by_type[mime_type] = {
                        'count': count,
                        'total_size': total_size,
                        'avg_size': total_size / count if count > 0 else 0
                    }

                # Compression statistics
                result = await conn.execute(text("""
                    SELECT
                        COUNT(*) as compressed_files,
                        AVG(compression_ratio) as avg_compression,
                        SUM(file_size * (1 - compression_ratio)) as space_saved
                    FROM migrated_documents
                    WHERE compression_ratio < 1.0
                """))

                compression_stats = result.fetchone()

                # Deduplication statistics
                result = await conn.execute(text("""
                    SELECT
                        COUNT(*) as dedup_groups,
                        SUM(duplicate_count) as total_duplicates,
                        SUM(total_size_saved) as space_saved
                    FROM file_deduplication
                    WHERE duplicate_count > 1
                """))

                dedup_stats = result.fetchone()

                self.stats.performance_metrics = {
                    'storage_by_type': storage_by_type,
                    'compression_stats': compression_stats._asdict() if compression_stats else {},
                    'deduplication_stats': dedup_stats._asdict() if dedup_stats else {},
                    'storage_efficiency': {
                        'compression_ratio': compression_stats[1] if compression_stats and compression_stats[1] else 1.0,
                        'space_saved_compression': compression_stats[2] if compression_stats else 0,
                        'space_saved_dedup': dedup_stats[2] if dedup_stats else 0
                    }
                }

        finally:
            await engine.dispose()

    async def _create_storage_indexes(self):
        """Create database indexes for optimized storage lookups"""
        engine = create_async_engine(self.target_db_url)

        try:
            async with engine.begin() as conn:
                # Create performance indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_migrated_docs_hash ON migrated_documents(file_hash)",
                    "CREATE INDEX IF NOT EXISTS idx_migrated_docs_mime ON migrated_documents(mime_type)",
                    "CREATE INDEX IF NOT EXISTS idx_migrated_docs_owner ON migrated_documents(owner_id)",
                    "CREATE INDEX IF NOT EXISTS idx_migrated_docs_path ON migrated_documents(target_path)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_permissions_user ON document_permissions(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_permissions_doc ON document_permissions(document_id)"
                ]

                for index_sql in indexes:
                    await conn.execute(text(index_sql))

        finally:
            await engine.dispose()


# Export the main class
__all__ = ['DocumentMigrator', 'DocumentMigrationStats', 'DocumentInfo']