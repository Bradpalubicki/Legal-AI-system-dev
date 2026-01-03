"""
Batch processing system for handling large-scale document operations with queue management and progress tracking.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os

from ..shared.database.models import Case, User, Document
from ..shared.database.connection import get_db
from .upload_manager import UploadManager, UploadBatch, FileInfo, UploadStatus
from .document_analyzer import DocumentAnalyzer, DocumentAnalysis, AnalysisType


class BatchOperation(Enum):
    """Types of batch operations."""
    UPLOAD_AND_ANALYZE = "upload_and_analyze"
    ANALYZE_EXISTING = "analyze_existing"
    RE_CATEGORIZE = "re_categorize"
    EXTRACT_METADATA = "extract_metadata"
    OCR_PROCESSING = "ocr_processing"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    VIRUS_SCAN = "virus_scan"
    PRIVILEGE_REVIEW = "privilege_review"
    EXPORT_DOCUMENTS = "export_documents"
    BULK_DELETE = "bulk_delete"
    BULK_MOVE = "bulk_move"
    DUPLICATE_DETECTION = "duplicate_detection"


class ProcessingStatus(Enum):
    """Status of batch processing job."""
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class Priority(Enum):
    """Processing priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class BatchJob:
    """Represents a batch processing job."""
    job_id: str
    operation: BatchOperation
    priority: Priority
    created_by: str
    created_at: datetime
    
    # Job configuration
    parameters: Dict[str, Any]
    target_files: List[str]  # File IDs or paths
    case_id: Optional[str] = None
    
    # Status tracking
    status: ProcessingStatus = ProcessingStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    
    # Results and metrics
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    
    # Error handling
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Output
    results: Dict[str, Any] = field(default_factory=dict)
    output_location: Optional[str] = None
    
    # Metadata
    estimated_duration: Optional[timedelta] = None
    actual_duration: Optional[timedelta] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    
    # Callbacks
    on_progress: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None


@dataclass
class BatchJobSummary:
    """Summary of a batch job for reporting."""
    job_id: str
    operation: str
    status: str
    created_at: datetime
    total_items: int
    processed_items: int
    success_rate: float
    duration: Optional[float]
    created_by: str


class BatchProcessor:
    """High-performance batch processing system for document operations."""
    
    def __init__(self, max_concurrent_jobs: int = 5, max_workers: int = 10):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_workers = max_workers
        
        # Processing infrastructure
        self.job_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_history: Dict[str, BatchJob] = {}
        
        # Workers and execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.worker_tasks: List[asyncio.Task] = []
        self.running = False
        
        # Dependencies
        self.upload_manager: Optional[UploadManager] = None
        self.document_analyzer = DocumentAnalyzer()
        
        # Performance tracking
        self.performance_metrics: Dict[str, Any] = {
            "jobs_processed": 0,
            "total_processing_time": 0.0,
            "average_job_time": 0.0,
            "success_rate": 0.0
        }

    async def start_processing(self):
        """Start the batch processing system."""
        try:
            if self.running:
                return
            
            self.running = True
            print("Starting batch processing system...")
            
            # Start worker tasks
            for i in range(self.max_concurrent_jobs):
                worker_task = asyncio.create_task(self._worker(f"worker_{i}"))
                self.worker_tasks.append(worker_task)
            
            # Start monitoring task
            monitor_task = asyncio.create_task(self._monitor_jobs())
            self.worker_tasks.append(monitor_task)
            
            print(f"Batch processing system started with {self.max_concurrent_jobs} workers")
            
        except Exception as e:
            print(f"Error starting batch processing: {e}")
            raise

    async def stop_processing(self):
        """Stop the batch processing system gracefully."""
        try:
            print("Stopping batch processing system...")
            self.running = False
            
            # Cancel all worker tasks
            for task in self.worker_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
            # Cancel active jobs
            for job in self.active_jobs.values():
                job.status = ProcessingStatus.CANCELLED
            
            print("Batch processing system stopped")
            
        except Exception as e:
            print(f"Error stopping batch processing: {e}")

    async def submit_job(
        self, 
        operation: BatchOperation,
        parameters: Dict[str, Any],
        target_files: List[str],
        created_by: str,
        priority: Priority = Priority.NORMAL,
        case_id: Optional[str] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ) -> str:
        """Submit a new batch processing job."""
        try:
            job_id = str(uuid.uuid4())
            
            job = BatchJob(
                job_id=job_id,
                operation=operation,
                priority=priority,
                created_by=created_by,
                created_at=datetime.utcnow(),
                parameters=parameters,
                target_files=target_files,
                case_id=case_id,
                total_items=len(target_files)
            )
            
            # Set callbacks
            if callbacks:
                job.on_progress = callbacks.get("on_progress")
                job.on_complete = callbacks.get("on_complete")
                job.on_error = callbacks.get("on_error")
            
            # Estimate duration based on operation and file count
            job.estimated_duration = self._estimate_job_duration(operation, len(target_files))
            
            # Add to queue with priority
            priority_value = priority.value
            await self.job_queue.put((priority_value, datetime.utcnow(), job))
            
            print(f"Submitted batch job: {job_id} ({operation.value})")
            
            return job_id
            
        except Exception as e:
            print(f"Error submitting job: {e}")
            raise

    async def _worker(self, worker_name: str):
        """Worker process for handling batch jobs."""
        try:
            print(f"Worker {worker_name} started")
            
            while self.running:
                try:
                    # Get next job from queue (with timeout)
                    priority, timestamp, job = await asyncio.wait_for(
                        self.job_queue.get(), timeout=1.0
                    )
                    
                    # Process the job
                    await self._process_job(job, worker_name)
                    
                except asyncio.TimeoutError:
                    # No job available, continue loop
                    continue
                except Exception as e:
                    print(f"Worker {worker_name} error: {e}")
                    await asyncio.sleep(1)
            
            print(f"Worker {worker_name} stopped")
            
        except Exception as e:
            print(f"Worker {worker_name} fatal error: {e}")

    async def _process_job(self, job: BatchJob, worker_name: str):
        """Process an individual batch job."""
        try:
            print(f"Worker {worker_name} processing job {job.job_id} ({job.operation.value})")
            
            # Update job status
            job.status = ProcessingStatus.RUNNING
            job.started_at = datetime.utcnow()
            self.active_jobs[job.job_id] = job
            
            # Route to appropriate processor
            if job.operation == BatchOperation.UPLOAD_AND_ANALYZE:
                await self._process_upload_and_analyze(job)
            elif job.operation == BatchOperation.ANALYZE_EXISTING:
                await self._process_analyze_existing(job)
            elif job.operation == BatchOperation.RE_CATEGORIZE:
                await self._process_re_categorize(job)
            elif job.operation == BatchOperation.EXTRACT_METADATA:
                await self._process_extract_metadata(job)
            elif job.operation == BatchOperation.OCR_PROCESSING:
                await self._process_ocr(job)
            elif job.operation == BatchOperation.PRIVILEGE_REVIEW:
                await self._process_privilege_review(job)
            elif job.operation == BatchOperation.DUPLICATE_DETECTION:
                await self._process_duplicate_detection(job)
            elif job.operation == BatchOperation.EXPORT_DOCUMENTS:
                await self._process_export_documents(job)
            elif job.operation == BatchOperation.BULK_DELETE:
                await self._process_bulk_delete(job)
            else:
                raise ValueError(f"Unsupported operation: {job.operation}")
            
            # Mark job as completed
            job.status = ProcessingStatus.COMPLETED if job.failed_items == 0 else ProcessingStatus.PARTIALLY_COMPLETED
            job.completed_at = datetime.utcnow()
            job.actual_duration = job.completed_at - job.started_at
            job.progress = 100.0
            
            # Execute completion callback
            if job.on_complete:
                try:
                    await job.on_complete(job)
                except Exception as e:
                    print(f"Error in completion callback: {e}")
            
            print(f"Job {job.job_id} completed: {job.successful_items}/{job.total_items} successful")
            
        except Exception as e:
            print(f"Error processing job {job.job_id}: {e}")
            
            # Mark job as failed
            job.status = ProcessingStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.errors.append({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "context": f"Job processing in {worker_name}"
            })
            
            # Execute error callback
            if job.on_error:
                try:
                    await job.on_error(job, e)
                except Exception as callback_error:
                    print(f"Error in error callback: {callback_error}")
        
        finally:
            # Move job to history and remove from active jobs
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
            
            self.job_history[job.job_id] = job
            
            # Update performance metrics
            self._update_performance_metrics(job)

    async def _process_upload_and_analyze(self, job: BatchJob):
        """Process upload and analyze operation."""
        try:
            if not self.upload_manager:
                raise ValueError("Upload manager not configured")
            
            batch_id = job.parameters.get("batch_id")
            if not batch_id:
                raise ValueError("batch_id required for upload and analyze operation")
            
            # Get upload batch
            upload_batch = self.upload_manager.active_batches.get(batch_id)
            if not upload_batch:
                raise ValueError(f"Upload batch {batch_id} not found")
            
            # Process each file
            for i, file_info in enumerate(upload_batch.files):
                try:
                    # Update progress
                    job.progress = (i / len(upload_batch.files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    # Analyze document
                    analysis_types = job.parameters.get("analysis_types", list(AnalysisType))
                    analysis = await self.document_analyzer.analyze_document(
                        file_info, 
                        analysis_types=analysis_types
                    )
                    
                    # Store results
                    job.results[file_info.file_id] = {
                        "analysis": analysis,
                        "status": "completed"
                    }
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error processing file {file_info.original_filename}: {e}")
                    
                    job.errors.append({
                        "file_id": file_info.file_id,
                        "filename": file_info.original_filename,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
        except Exception as e:
            print(f"Error in upload and analyze operation: {e}")
            raise

    async def _process_analyze_existing(self, job: BatchJob):
        """Process analyze existing documents operation."""
        try:
            # Get analysis configuration
            analysis_types = job.parameters.get("analysis_types", list(AnalysisType))
            force_reanalyze = job.parameters.get("force_reanalyze", False)
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    # Get file information (would query database)
                    file_info = await self._get_file_info(file_id)
                    if not file_info:
                        job.skipped_items += 1
                        continue
                    
                    # Check if already analyzed
                    if not force_reanalyze and self._is_already_analyzed(file_id, analysis_types):
                        job.skipped_items += 1
                        continue
                    
                    # Perform analysis
                    analysis = await self.document_analyzer.analyze_document(
                        file_info, 
                        analysis_types=analysis_types
                    )
                    
                    # Store results
                    job.results[file_id] = {
                        "analysis": analysis,
                        "status": "completed"
                    }
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error analyzing document {file_id}: {e}")
                    
                    job.errors.append({
                        "file_id": file_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
        except Exception as e:
            print(f"Error in analyze existing operation: {e}")
            raise

    async def _process_re_categorize(self, job: BatchJob):
        """Process document re-categorization operation."""
        try:
            new_category = job.parameters.get("new_category")
            auto_categorize = job.parameters.get("auto_categorize", False)
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    if auto_categorize:
                        # Use AI to re-categorize
                        file_info = await self._get_file_info(file_id)
                        if file_info:
                            analysis = await self.document_analyzer.analyze_document(
                                file_info, 
                                analysis_types=[AnalysisType.CATEGORIZATION]
                            )
                            
                            new_category = analysis.primary_category.value
                    
                    # Update document category in database
                    await self._update_document_category(file_id, new_category)
                    
                    job.results[file_id] = {
                        "old_category": "unknown",  # Would get from database
                        "new_category": new_category,
                        "status": "completed"
                    }
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error re-categorizing document {file_id}: {e}")
                    
                    job.errors.append({
                        "file_id": file_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
        except Exception as e:
            print(f"Error in re-categorize operation: {e}")
            raise

    async def _process_extract_metadata(self, job: BatchJob):
        """Process metadata extraction operation."""
        try:
            metadata_types = job.parameters.get("metadata_types", ["all"])
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    # Get file information
                    file_info = await self._get_file_info(file_id)
                    if not file_info:
                        job.skipped_items += 1
                        continue
                    
                    # Extract metadata based on file type
                    extracted_metadata = await self._extract_file_metadata(file_info, metadata_types)
                    
                    # Update file metadata in database
                    await self._update_file_metadata(file_id, extracted_metadata)
                    
                    job.results[file_id] = {
                        "extracted_metadata": extracted_metadata,
                        "status": "completed"
                    }
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error extracting metadata for {file_id}: {e}")
                    
                    job.errors.append({
                        "file_id": file_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
        except Exception as e:
            print(f"Error in extract metadata operation: {e}")
            raise

    async def _process_ocr(self, job: BatchJob):
        """Process OCR operation for scanned documents."""
        try:
            ocr_languages = job.parameters.get("languages", ["eng"])
            confidence_threshold = job.parameters.get("confidence_threshold", 0.8)
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    # Get file information
                    file_info = await self._get_file_info(file_id)
                    if not file_info:
                        job.skipped_items += 1
                        continue
                    
                    # Check if file needs OCR
                    if not self._needs_ocr(file_info):
                        job.skipped_items += 1
                        continue
                    
                    # Perform OCR
                    ocr_result = await self._perform_ocr(file_info, ocr_languages)
                    
                    # Check confidence threshold
                    if ocr_result.get("confidence", 0.0) < confidence_threshold:
                        job.warnings.append({
                            "file_id": file_id,
                            "message": f"OCR confidence {ocr_result.get('confidence', 0.0)} below threshold {confidence_threshold}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    # Store OCR results
                    await self._store_ocr_results(file_id, ocr_result)
                    
                    job.results[file_id] = {
                        "ocr_text": ocr_result.get("text", ""),
                        "confidence": ocr_result.get("confidence", 0.0),
                        "status": "completed"
                    }
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error performing OCR on {file_id}: {e}")
                    
                    job.errors.append({
                        "file_id": file_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
        except Exception as e:
            print(f"Error in OCR operation: {e}")
            raise

    async def _process_privilege_review(self, job: BatchJob):
        """Process attorney-client privilege review operation."""
        try:
            privilege_threshold = job.parameters.get("privilege_threshold", 0.7)
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    # Get file information
                    file_info = await self._get_file_info(file_id)
                    if not file_info:
                        job.skipped_items += 1
                        continue
                    
                    # Perform privilege analysis
                    analysis = await self.document_analyzer.analyze_document(
                        file_info, 
                        analysis_types=[AnalysisType.PRIVILEGE_REVIEW, AnalysisType.CONFIDENTIALITY]
                    )
                    
                    # Determine privilege status
                    privilege_status = "not_privileged"
                    if analysis.privilege_risk > privilege_threshold:
                        privilege_status = "privileged"
                    elif analysis.privilege_risk > (privilege_threshold * 0.7):
                        privilege_status = "potentially_privileged"
                    
                    # Update privilege status in database
                    await self._update_privilege_status(file_id, privilege_status, analysis.privilege_risk)
                    
                    job.results[file_id] = {
                        "privilege_status": privilege_status,
                        "privilege_risk": analysis.privilege_risk,
                        "confidentiality_level": analysis.confidentiality_level.value,
                        "status": "completed"
                    }
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error reviewing privilege for {file_id}: {e}")
                    
                    job.errors.append({
                        "file_id": file_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
        except Exception as e:
            print(f"Error in privilege review operation: {e}")
            raise

    async def _process_duplicate_detection(self, job: BatchJob):
        """Process duplicate document detection operation."""
        try:
            similarity_threshold = job.parameters.get("similarity_threshold", 0.95)
            hash_comparison = job.parameters.get("hash_comparison", True)
            content_comparison = job.parameters.get("content_comparison", True)
            
            # Build document fingerprints
            document_fingerprints = {}
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 50  # First 50% for fingerprinting
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    # Get file information
                    file_info = await self._get_file_info(file_id)
                    if not file_info:
                        job.skipped_items += 1
                        continue
                    
                    # Create fingerprint
                    fingerprint = await self._create_document_fingerprint(
                        file_info, hash_comparison, content_comparison
                    )
                    
                    document_fingerprints[file_id] = fingerprint
                    
                except Exception as e:
                    print(f"Error creating fingerprint for {file_id}: {e}")
                    job.failed_items += 1
                
                job.processed_items += 1
            
            # Find duplicates
            duplicates = await self._find_duplicates(document_fingerprints, similarity_threshold)
            
            # Update progress to 100%
            job.progress = 100.0
            if job.on_progress:
                await job.on_progress(job)
            
            job.results = {
                "duplicate_groups": duplicates,
                "total_duplicates": sum(len(group) - 1 for group in duplicates.values()),
                "unique_documents": len(document_fingerprints) - sum(len(group) - 1 for group in duplicates.values())
            }
            
            job.successful_items = len(document_fingerprints)
            
        except Exception as e:
            print(f"Error in duplicate detection operation: {e}")
            raise

    async def _process_export_documents(self, job: BatchJob):
        """Process document export operation."""
        try:
            export_format = job.parameters.get("format", "zip")
            include_metadata = job.parameters.get("include_metadata", True)
            export_path = job.parameters.get("export_path", "/tmp/exports")
            
            # Create export directory
            export_dir = os.path.join(export_path, f"export_{job.job_id}")
            os.makedirs(export_dir, exist_ok=True)
            
            exported_files = []
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    # Get file information
                    file_info = await self._get_file_info(file_id)
                    if not file_info:
                        job.skipped_items += 1
                        continue
                    
                    # Copy file to export directory
                    export_filename = f"{file_info.file_id}_{file_info.original_filename}"
                    export_file_path = os.path.join(export_dir, export_filename)
                    
                    await self._copy_file(file_info.final_path, export_file_path)
                    exported_files.append(export_file_path)
                    
                    # Export metadata if requested
                    if include_metadata:
                        metadata_path = os.path.join(export_dir, f"{file_info.file_id}_metadata.json")
                        await self._export_file_metadata(file_info, metadata_path)
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error exporting file {file_id}: {e}")
                    
                    job.errors.append({
                        "file_id": file_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
            # Create archive if requested
            if export_format == "zip":
                archive_path = await self._create_zip_archive(export_dir, exported_files)
                job.output_location = archive_path
            else:
                job.output_location = export_dir
            
            job.results = {
                "exported_files": len(exported_files),
                "export_location": job.output_location,
                "export_format": export_format
            }
            
        except Exception as e:
            print(f"Error in export documents operation: {e}")
            raise

    async def _process_bulk_delete(self, job: BatchJob):
        """Process bulk delete operation."""
        try:
            confirm_delete = job.parameters.get("confirm_delete", False)
            if not confirm_delete:
                raise ValueError("Bulk delete requires explicit confirmation")
            
            soft_delete = job.parameters.get("soft_delete", True)
            
            for i, file_id in enumerate(job.target_files):
                try:
                    # Update progress
                    job.progress = (i / len(job.target_files)) * 100
                    if job.on_progress:
                        await job.on_progress(job)
                    
                    if soft_delete:
                        # Mark as deleted in database
                        await self._soft_delete_file(file_id)
                    else:
                        # Permanently delete file and database record
                        await self._hard_delete_file(file_id)
                    
                    job.results[file_id] = {
                        "status": "deleted",
                        "delete_type": "soft" if soft_delete else "hard"
                    }
                    
                    job.successful_items += 1
                    
                except Exception as e:
                    print(f"Error deleting file {file_id}: {e}")
                    
                    job.errors.append({
                        "file_id": file_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    job.failed_items += 1
                
                job.processed_items += 1
            
        except Exception as e:
            print(f"Error in bulk delete operation: {e}")
            raise

    # Helper methods (these would implement actual database/file operations)
    
    async def _get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """Get file information from database."""
        # Placeholder - would query database
        return None
    
    def _is_already_analyzed(self, file_id: str, analysis_types: List[AnalysisType]) -> bool:
        """Check if file has already been analyzed."""
        # Placeholder - would check database
        return False
    
    async def _update_document_category(self, file_id: str, category: str):
        """Update document category in database."""
        # Placeholder - would update database
        pass
    
    async def _extract_file_metadata(self, file_info: FileInfo, metadata_types: List[str]) -> Dict[str, Any]:
        """Extract metadata from file."""
        # Placeholder - would extract metadata
        return {}
    
    async def _update_file_metadata(self, file_id: str, metadata: Dict[str, Any]):
        """Update file metadata in database."""
        # Placeholder - would update database
        pass
    
    def _needs_ocr(self, file_info: FileInfo) -> bool:
        """Check if file needs OCR processing."""
        # Placeholder - would check file type and existing OCR data
        return True
    
    async def _perform_ocr(self, file_info: FileInfo, languages: List[str]) -> Dict[str, Any]:
        """Perform OCR on file."""
        # Placeholder - would perform actual OCR
        return {"text": "OCR text", "confidence": 0.9}
    
    async def _store_ocr_results(self, file_id: str, ocr_result: Dict[str, Any]):
        """Store OCR results in database."""
        # Placeholder - would store in database
        pass
    
    async def _update_privilege_status(self, file_id: str, status: str, risk: float):
        """Update privilege status in database."""
        # Placeholder - would update database
        pass
    
    async def _create_document_fingerprint(
        self, 
        file_info: FileInfo, 
        hash_comparison: bool, 
        content_comparison: bool
    ) -> Dict[str, Any]:
        """Create document fingerprint for duplicate detection."""
        # Placeholder - would create actual fingerprint
        return {"hash": "file_hash", "content_hash": "content_hash"}
    
    async def _find_duplicates(
        self, 
        fingerprints: Dict[str, Dict[str, Any]], 
        threshold: float
    ) -> Dict[str, List[str]]:
        """Find duplicate documents based on fingerprints."""
        # Placeholder - would implement duplicate detection algorithm
        return {}
    
    async def _copy_file(self, source_path: str, dest_path: str):
        """Copy file from source to destination."""
        # Placeholder - would copy file
        pass
    
    async def _export_file_metadata(self, file_info: FileInfo, metadata_path: str):
        """Export file metadata to JSON."""
        # Placeholder - would export metadata
        pass
    
    async def _create_zip_archive(self, directory: str, files: List[str]) -> str:
        """Create ZIP archive of files."""
        # Placeholder - would create ZIP archive
        return f"{directory}.zip"
    
    async def _soft_delete_file(self, file_id: str):
        """Mark file as deleted in database."""
        # Placeholder - would update database
        pass
    
    async def _hard_delete_file(self, file_id: str):
        """Permanently delete file and database record."""
        # Placeholder - would delete file and database record
        pass
    
    def _estimate_job_duration(self, operation: BatchOperation, file_count: int) -> timedelta:
        """Estimate job duration based on operation and file count."""
        # Base time per file for different operations (in seconds)
        base_times = {
            BatchOperation.UPLOAD_AND_ANALYZE: 30,
            BatchOperation.ANALYZE_EXISTING: 20,
            BatchOperation.RE_CATEGORIZE: 5,
            BatchOperation.EXTRACT_METADATA: 10,
            BatchOperation.OCR_PROCESSING: 60,
            BatchOperation.PRIVILEGE_REVIEW: 15,
            BatchOperation.DUPLICATE_DETECTION: 5,
            BatchOperation.EXPORT_DOCUMENTS: 2,
            BatchOperation.BULK_DELETE: 1
        }
        
        base_time = base_times.get(operation, 10)
        total_seconds = base_time * file_count
        
        return timedelta(seconds=total_seconds)
    
    def _update_performance_metrics(self, job: BatchJob):
        """Update system performance metrics."""
        try:
            self.performance_metrics["jobs_processed"] += 1
            
            if job.actual_duration:
                self.performance_metrics["total_processing_time"] += job.actual_duration.total_seconds()
                self.performance_metrics["average_job_time"] = (
                    self.performance_metrics["total_processing_time"] / 
                    self.performance_metrics["jobs_processed"]
                )
            
            success_rate = job.successful_items / job.total_items if job.total_items > 0 else 0
            total_success_rate = (
                (self.performance_metrics["success_rate"] * (self.performance_metrics["jobs_processed"] - 1) + success_rate) /
                self.performance_metrics["jobs_processed"]
            )
            self.performance_metrics["success_rate"] = total_success_rate
            
        except Exception as e:
            print(f"Error updating performance metrics: {e}")

    async def _monitor_jobs(self):
        """Monitor job health and performance."""
        try:
            while self.running:
                # Clean up old completed jobs
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                jobs_to_remove = [
                    job_id for job_id, job in self.job_history.items()
                    if job.completed_at and job.completed_at < cutoff_time
                ]
                
                for job_id in jobs_to_remove:
                    del self.job_history[job_id]
                
                # Log system status
                if len(self.active_jobs) > 0:
                    print(f"Active jobs: {len(self.active_jobs)}, Queue size: {self.job_queue.qsize()}")
                
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            print(f"Error in job monitor: {e}")

    # Public API methods

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        try:
            # Check active jobs first
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            elif job_id in self.job_history:
                job = self.job_history[job_id]
            else:
                return None
            
            return {
                "job_id": job.job_id,
                "operation": job.operation.value,
                "status": job.status.value,
                "priority": job.priority.value,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "progress": job.progress,
                "total_items": job.total_items,
                "processed_items": job.processed_items,
                "successful_items": job.successful_items,
                "failed_items": job.failed_items,
                "skipped_items": job.skipped_items,
                "estimated_duration": job.estimated_duration.total_seconds() if job.estimated_duration else None,
                "actual_duration": job.actual_duration.total_seconds() if job.actual_duration else None,
                "errors": job.errors[-5:],  # Last 5 errors
                "warnings": job.warnings[-5:],  # Last 5 warnings
                "output_location": job.output_location
            }
            
        except Exception as e:
            print(f"Error getting job status: {e}")
            return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running or queued job."""
        try:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = ProcessingStatus.CANCELLED
                return True
            
            # TODO: Remove from queue if not started yet
            
            return False
            
        except Exception as e:
            print(f"Error cancelling job: {e}")
            return False

    async def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        try:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                if job.status == ProcessingStatus.RUNNING:
                    job.status = ProcessingStatus.PAUSED
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error pausing job: {e}")
            return False

    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                if job.status == ProcessingStatus.PAUSED:
                    job.status = ProcessingStatus.RUNNING
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error resuming job: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            active_job_statuses = {}
            for status in ProcessingStatus:
                active_job_statuses[status.value] = sum(
                    1 for job in self.active_jobs.values() if job.status == status
                )
            
            return {
                "running": self.running,
                "active_jobs": len(self.active_jobs),
                "queue_size": self.job_queue.qsize(),
                "worker_count": len(self.worker_tasks),
                "max_concurrent_jobs": self.max_concurrent_jobs,
                "job_status_breakdown": active_job_statuses,
                "performance_metrics": self.performance_metrics,
                "total_jobs_processed": len(self.job_history),
                "system_uptime": datetime.utcnow().isoformat()  # Would track actual uptime
            }
            
        except Exception as e:
            print(f"Error getting system status: {e}")
            return {}

    def get_job_history(self, limit: int = 100) -> List[BatchJobSummary]:
        """Get job history summary."""
        try:
            recent_jobs = list(self.job_history.values())[-limit:]
            
            summaries = []
            for job in recent_jobs:
                success_rate = (job.successful_items / job.total_items * 100) if job.total_items > 0 else 0
                duration = job.actual_duration.total_seconds() if job.actual_duration else None
                
                summary = BatchJobSummary(
                    job_id=job.job_id,
                    operation=job.operation.value,
                    status=job.status.value,
                    created_at=job.created_at,
                    total_items=job.total_items,
                    processed_items=job.processed_items,
                    success_rate=success_rate,
                    duration=duration,
                    created_by=job.created_by
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            print(f"Error getting job history: {e}")
            return []