"""
Bulk document downloader with support for multiple sources.

Handles downloading documents from various sources including PACER, cloud storage,
email systems, and local folders with progress tracking and error handling.
"""

import asyncio
import aiohttp
import aiofiles
import hashlib
import mimetypes
from typing import Dict, List, Optional, Any, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import logging

from ..shared.utils import BaseAPIClient
from .models import (
    DocumentMetadata, DownloadSource, ProcessingStatus, DocumentHash,
    ProcessingError, get_mime_type_from_extension
)


@dataclass
class DownloadRequest:
    """Request for downloading a document."""
    request_id: str
    source: DownloadSource
    source_path: str  # URL, file path, or identifier
    destination_path: Optional[str] = None
    filename: Optional[str] = None
    
    # Authentication/credentials
    credentials: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    
    # Download options
    max_file_size: Optional[int] = None  # bytes
    timeout: int = 300  # seconds
    retry_count: int = 3
    
    # Metadata
    case_number: Optional[str] = None
    document_set: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Processing options
    skip_if_exists: bool = True
    verify_checksum: bool = True
    extract_metadata: bool = True


@dataclass
class DownloadResult:
    """Result of document download operation."""
    request_id: str
    success: bool
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    document_hash: Optional[DocumentHash] = None
    metadata: Optional[DocumentMetadata] = None
    
    # Error information
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    retry_count: int = 0
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    download_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate download duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class DocumentDownloader:
    """Multi-source document downloader with batch processing capabilities."""
    
    def __init__(self, 
                 base_storage_path: str,
                 api_client: Optional[BaseAPIClient] = None,
                 max_concurrent_downloads: int = 10):
        self.base_storage_path = Path(base_storage_path)
        self.api_client = api_client
        self.max_concurrent_downloads = max_concurrent_downloads
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # Ensure storage directory exists
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=600),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def download_batch(self, 
                           requests: List[DownloadRequest],
                           progress_callback: Optional[callable] = None) -> List[DownloadResult]:
        """
        Download multiple documents concurrently.
        
        Args:
            requests: List of download requests
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of download results
        """
        if not self.session:
            raise RuntimeError("DocumentDownloader must be used as async context manager")
        
        self.logger.info(f"Starting batch download of {len(requests)} documents")
        
        # Create download tasks
        tasks = [
            self._download_single(request, progress_callback)
            for request in requests
        ]
        
        # Execute downloads with concurrency control
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(DownloadResult(
                    request_id=requests[i].request_id,
                    success=False,
                    error_message=str(result),
                    error_type=type(result).__name__,
                    completed_at=datetime.utcnow()
                ))
            else:
                final_results.append(result)
        
        successful = sum(1 for r in final_results if r.success)
        self.logger.info(f"Batch download completed: {successful}/{len(requests)} successful")
        
        return final_results
    
    async def _download_single(self, 
                             request: DownloadRequest,
                             progress_callback: Optional[callable] = None) -> DownloadResult:
        """Download a single document with retry logic."""
        async with self.download_semaphore:
            result = DownloadResult(request_id=request.request_id, success=False)
            
            for attempt in range(request.retry_count + 1):
                try:
                    result.retry_count = attempt
                    
                    # Perform download based on source type
                    if request.source == DownloadSource.PACER:
                        success = await self._download_from_pacer(request, result)
                    elif request.source in [DownloadSource.GOOGLE_DRIVE, DownloadSource.DROPBOX]:
                        success = await self._download_from_cloud(request, result)
                    elif request.source == DownloadSource.EMAIL:
                        success = await self._download_from_email(request, result)
                    elif request.source == DownloadSource.FTP:
                        success = await self._download_from_ftp(request, result)
                    elif request.source == DownloadSource.LOCAL_FOLDER:
                        success = await self._copy_from_local(request, result)
                    elif request.source == DownloadSource.WEB_SCRAPING:
                        success = await self._download_from_web(request, result)
                    elif request.source == DownloadSource.API:
                        success = await self._download_from_api(request, result)
                    else:
                        success = await self._download_from_url(request, result)
                    
                    if success:
                        result.success = True
                        result.completed_at = datetime.utcnow()
                        result.download_time = result.duration
                        
                        if progress_callback:
                            await progress_callback(request.request_id, "completed", result)
                        
                        break
                    
                except Exception as e:
                    result.error_message = str(e)
                    result.error_type = type(e).__name__
                    self.logger.warning(
                        f"Download attempt {attempt + 1} failed for {request.request_id}: {e}"
                    )
                    
                    if attempt < request.retry_count:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            result.completed_at = datetime.utcnow()
            return result
    
    async def _download_from_url(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Download document from HTTP/HTTPS URL."""
        try:
            # Determine local path
            local_path = self._get_local_path(request)
            
            # Check if file already exists
            if request.skip_if_exists and local_path.exists():
                result.local_path = str(local_path)
                result.file_size = local_path.stat().st_size
                return True
            
            # Prepare request headers
            headers = request.headers or {}
            
            # Download file
            async with self.session.get(
                request.source_path,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=request.timeout)
            ) as response:
                
                if response.status != 200:
                    result.error_message = f"HTTP {response.status}: {response.reason}"
                    return False
                
                # Check file size
                content_length = response.headers.get('content-length')
                if content_length and request.max_file_size:
                    if int(content_length) > request.max_file_size:
                        result.error_message = f"File too large: {content_length} bytes"
                        return False
                
                # Download and save file
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                async with aiofiles.open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                # Set result data
                result.local_path = str(local_path)
                result.file_size = local_path.stat().st_size
                
                # Calculate hash if requested
                if request.verify_checksum:
                    result.document_hash = await self._calculate_document_hash(local_path)
                
                # Extract metadata if requested
                if request.extract_metadata:
                    result.metadata = await self._extract_basic_metadata(request, local_path)
                
                return True
                
        except Exception as e:
            result.error_message = str(e)
            result.error_type = type(e).__name__
            return False
    
    async def _download_from_pacer(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Download document from PACER system."""
        if not self.api_client:
            result.error_message = "API client required for PACER downloads"
            return False
        
        try:
            # Use PACER gateway service
            response = await self.api_client.post(
                "/pacer/download",
                json={
                    "document_id": request.source_path,
                    "credentials": request.credentials,
                    "case_number": request.case_number
                },
                timeout=request.timeout
            )
            
            if not response.get("success"):
                result.error_message = response.get("error", "PACER download failed")
                return False
            
            # Get download URL and fetch document
            download_url = response.get("download_url")
            if download_url:
                # Create temporary request for URL download
                url_request = DownloadRequest(
                    request_id=request.request_id,
                    source=DownloadSource.API,
                    source_path=download_url,
                    destination_path=request.destination_path,
                    filename=request.filename,
                    headers={"Authorization": f"Bearer {response.get('access_token')}"},
                    timeout=request.timeout
                )
                
                return await self._download_from_url(url_request, result)
            
            result.error_message = "No download URL provided by PACER"
            return False
            
        except Exception as e:
            result.error_message = f"PACER download error: {str(e)}"
            result.error_type = type(e).__name__
            return False
    
    async def _download_from_cloud(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Download document from cloud storage (Google Drive, Dropbox, etc.)."""
        if not self.api_client:
            result.error_message = "API client required for cloud storage downloads"
            return False
        
        try:
            # Use cloud storage integration
            endpoint = f"/{request.source.value}/download"
            response = await self.api_client.post(
                endpoint,
                json={
                    "file_id": request.source_path,
                    "credentials": request.credentials
                },
                timeout=request.timeout
            )
            
            if response.get("download_url"):
                # Download from provided URL
                url_request = DownloadRequest(
                    request_id=request.request_id,
                    source=DownloadSource.API,
                    source_path=response["download_url"],
                    destination_path=request.destination_path,
                    filename=request.filename or response.get("filename"),
                    headers=response.get("headers"),
                    timeout=request.timeout
                )
                
                return await self._download_from_url(url_request, result)
            
            result.error_message = "No download URL provided by cloud service"
            return False
            
        except Exception as e:
            result.error_message = f"Cloud download error: {str(e)}"
            result.error_type = type(e).__name__
            return False
    
    async def _download_from_email(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Download document from email attachment."""
        if not self.api_client:
            result.error_message = "API client required for email downloads"
            return False
        
        try:
            # Use email integration service
            response = await self.api_client.post(
                "/email/download-attachment",
                json={
                    "message_id": request.source_path,
                    "credentials": request.credentials,
                    "attachment_name": request.filename
                },
                timeout=request.timeout
            )
            
            if response.get("success") and response.get("file_data"):
                # Save file data to local path
                local_path = self._get_local_path(request)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                import base64
                file_data = base64.b64decode(response["file_data"])
                
                async with aiofiles.open(local_path, 'wb') as f:
                    await f.write(file_data)
                
                result.local_path = str(local_path)
                result.file_size = len(file_data)
                
                if request.verify_checksum:
                    result.document_hash = await self._calculate_document_hash(local_path)
                
                if request.extract_metadata:
                    result.metadata = await self._extract_basic_metadata(request, local_path)
                
                return True
            
            result.error_message = response.get("error", "Email download failed")
            return False
            
        except Exception as e:
            result.error_message = f"Email download error: {str(e)}"
            result.error_type = type(e).__name__
            return False
    
    async def _download_from_ftp(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Download document from FTP server."""
        try:
            import aioftp
            
            # Parse FTP URL
            url_parts = urlparse(request.source_path)
            host = url_parts.hostname
            port = url_parts.port or 21
            username = request.credentials.get("username") if request.credentials else None
            password = request.credentials.get("password") if request.credentials else None
            remote_path = url_parts.path
            
            # Download file
            async with aioftp.Client() as client:
                await client.connect(host, port)
                
                if username and password:
                    await client.login(username, password)
                
                local_path = self._get_local_path(request)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                await client.download(remote_path, local_path)
                
                result.local_path = str(local_path)
                result.file_size = local_path.stat().st_size
                
                if request.verify_checksum:
                    result.document_hash = await self._calculate_document_hash(local_path)
                
                if request.extract_metadata:
                    result.metadata = await self._extract_basic_metadata(request, local_path)
                
                return True
                
        except Exception as e:
            result.error_message = f"FTP download error: {str(e)}"
            result.error_type = type(e).__name__
            return False
    
    async def _copy_from_local(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Copy document from local file system."""
        try:
            source_path = Path(request.source_path)
            
            if not source_path.exists():
                result.error_message = f"Source file not found: {request.source_path}"
                return False
            
            if request.max_file_size and source_path.stat().st_size > request.max_file_size:
                result.error_message = f"File too large: {source_path.stat().st_size} bytes"
                return False
            
            local_path = self._get_local_path(request)
            
            # Skip if same file
            if source_path.resolve() == local_path.resolve():
                result.local_path = str(local_path)
                result.file_size = local_path.stat().st_size
                return True
            
            # Copy file
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(source_path, local_path)
            
            result.local_path = str(local_path)
            result.file_size = local_path.stat().st_size
            
            if request.verify_checksum:
                result.document_hash = await self._calculate_document_hash(local_path)
            
            if request.extract_metadata:
                result.metadata = await self._extract_basic_metadata(request, local_path)
            
            return True
            
        except Exception as e:
            result.error_message = f"Local copy error: {str(e)}"
            result.error_type = type(e).__name__
            return False
    
    async def _download_from_web(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Download document via web scraping."""
        if not self.api_client:
            result.error_message = "API client required for web scraping downloads"
            return False
        
        try:
            # Use web scraping service
            response = await self.api_client.post(
                "/web-scraper/download",
                json={
                    "url": request.source_path,
                    "selector": request.custom_fields.get("selector"),
                    "headers": request.headers,
                    "credentials": request.credentials
                },
                timeout=request.timeout
            )
            
            if response.get("success") and response.get("download_url"):
                # Download from extracted URL
                url_request = DownloadRequest(
                    request_id=request.request_id,
                    source=DownloadSource.API,
                    source_path=response["download_url"],
                    destination_path=request.destination_path,
                    filename=request.filename or response.get("filename"),
                    timeout=request.timeout
                )
                
                return await self._download_from_url(url_request, result)
            
            result.error_message = response.get("error", "Web scraping failed")
            return False
            
        except Exception as e:
            result.error_message = f"Web scraping error: {str(e)}"
            result.error_type = type(e).__name__
            return False
    
    async def _download_from_api(self, request: DownloadRequest, result: DownloadResult) -> bool:
        """Download document from generic API endpoint."""
        return await self._download_from_url(request, result)
    
    def _get_local_path(self, request: DownloadRequest) -> Path:
        """Determine local file path for download."""
        if request.destination_path:
            return Path(request.destination_path)
        
        # Generate path based on source and filename
        if request.filename:
            filename = request.filename
        else:
            # Extract filename from source path
            if request.source_path.startswith(('http://', 'https://')):
                filename = Path(urlparse(request.source_path).path).name
            else:
                filename = Path(request.source_path).name
            
            # Fallback if no filename could be determined
            if not filename or filename == '.':
                filename = f"{request.request_id}.pdf"
        
        # Organize by source and date
        date_folder = datetime.utcnow().strftime("%Y/%m/%d")
        return self.base_storage_path / request.source.value / date_folder / filename
    
    async def _calculate_document_hash(self, file_path: Path) -> DocumentHash:
        """Calculate various hashes for document."""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        # For content hash, we'd need to extract text content
        # For now, use SHA256 as content hash
        content_hash = sha256_hash.hexdigest()
        
        return DocumentHash(
            md5=md5_hash.hexdigest(),
            sha256=sha256_hash.hexdigest(),
            content_hash=content_hash,
            size=file_path.stat().st_size,
            created_at=datetime.utcnow()
        )
    
    async def _extract_basic_metadata(self, 
                                    request: DownloadRequest, 
                                    file_path: Path) -> DocumentMetadata:
        """Extract basic metadata from downloaded document."""
        file_stat = file_path.stat()
        
        return DocumentMetadata(
            document_id=f"doc_{request.request_id}",
            filename=file_path.name,
            original_path=request.source_path,
            file_size=file_stat.st_size,
            file_type=file_path.suffix.lower(),
            mime_type=get_mime_type_from_extension(file_path.name),
            category=DocumentCategory.UNKNOWN,  # Will be determined by categorizer
            category_confidence=CategoryConfidence.VERY_LOW,
            processing_status=ProcessingStatus.DOWNLOADED,
            download_source=request.source,
            downloaded_at=datetime.utcnow(),
            storage_path=str(file_path),
            case_number=request.case_number,
            document_set=request.document_set,
            tags=request.tags,
            custom_fields=request.custom_fields
        )