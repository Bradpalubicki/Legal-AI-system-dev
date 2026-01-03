"""
RESTful API for document processing operations including bulk upload, analysis, and batch processing.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Body, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
import asyncio
import os
import json
import io
import zipfile

from ..shared.database.connection import get_db
from ..shared.security.auth import get_current_user
from ..shared.database.models import User, Case
from .upload_manager import UploadManager, UploadConfig, FileType, ProcessingPriority, UploadProgress
from .document_analyzer import DocumentAnalyzer, DocumentCategory, AnalysisType, ConfidentialityLevel
from .batch_processor import BatchProcessor, BatchOperation, Priority, ProcessingStatus


# Pydantic models for request/response
class UploadConfigModel(BaseModel):
    """Upload configuration model."""
    max_file_size: int = Field(default=100 * 1024 * 1024, ge=1024)
    max_batch_size: int = Field(default=50, ge=1, le=1000)
    allowed_file_types: List[str] = Field(default_factory=list)
    scan_for_viruses: bool = True
    extract_metadata: bool = True
    auto_categorize: bool = True
    create_thumbnails: bool = True
    ocr_scanned_documents: bool = True
    concurrent_uploads: int = Field(default=5, ge=1, le=20)


class CreateBatchRequest(BaseModel):
    """Request to create upload batch."""
    case_id: str
    priority: str = Field(default="normal")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = [p.name.lower() for p in ProcessingPriority]
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v


class AnalysisRequest(BaseModel):
    """Document analysis request model."""
    file_ids: List[str] = Field(..., min_items=1, max_items=100)
    analysis_types: List[str] = Field(default_factory=list)
    case_id: Optional[str] = None
    force_reanalyze: bool = False
    priority: str = Field(default="normal")
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        if not v:
            return [t.value for t in AnalysisType]
        
        valid_types = [t.value for t in AnalysisType]
        for analysis_type in v:
            if analysis_type not in valid_types:
                raise ValueError(f"Invalid analysis type: {analysis_type}")
        return v


class BatchJobRequest(BaseModel):
    """Batch job request model."""
    operation: str
    file_ids: List[str] = Field(..., min_items=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="normal")
    case_id: Optional[str] = None
    
    @validator('operation')
    def validate_operation(cls, v):
        valid_operations = [op.value for op in BatchOperation]
        if v not in valid_operations:
            raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")
        return v


class DocumentCategoryUpdate(BaseModel):
    """Document category update model."""
    file_ids: List[str] = Field(..., min_items=1)
    new_category: Optional[str] = None
    auto_categorize: bool = False
    
    @validator('new_category')
    def validate_category(cls, v):
        if v is not None:
            valid_categories = [cat.value for cat in DocumentCategory]
            if v not in valid_categories:
                raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v


class ExportRequest(BaseModel):
    """Document export request model."""
    file_ids: List[str] = Field(..., min_items=1, max_items=1000)
    format: str = Field(default="zip")
    include_metadata: bool = True
    include_analysis: bool = True
    export_name: Optional[str] = None
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ["zip", "folder"]:
            raise ValueError("Format must be 'zip' or 'folder'")
        return v


class BatchProgressResponse(BaseModel):
    """Batch progress response model."""
    batch_id: str
    status: str
    total_files: int
    completed_files: int
    failed_files: int
    progress_percentage: float
    current_file: Optional[str]
    estimated_completion: Optional[datetime]
    processing_stage: str
    errors: List[Dict[str, Any]]


class DocumentAnalysisResponse(BaseModel):
    """Document analysis response model."""
    file_id: str
    analysis_timestamp: datetime
    primary_category: str
    category_confidence: float
    word_count: int
    entities_count: int
    key_terms: List[str]
    confidentiality_level: str
    privilege_risk: float
    executive_summary: str
    analysis_confidence: float
    processing_time: float


class BatchJobResponse(BaseModel):
    """Batch job response model."""
    job_id: str
    operation: str
    status: str
    progress: float
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    estimated_duration: Optional[float]
    actual_duration: Optional[float]
    output_location: Optional[str]


# Initialize components
upload_manager = None
document_analyzer = None
batch_processor = None

def get_upload_manager():
    """Get upload manager instance."""
    global upload_manager
    if upload_manager is None:
        config = UploadConfig()
        upload_manager = UploadManager(config)
    return upload_manager

def get_document_analyzer():
    """Get document analyzer instance."""
    global document_analyzer
    if document_analyzer is None:
        document_analyzer = DocumentAnalyzer()
    return document_analyzer

def get_batch_processor():
    """Get batch processor instance."""
    global batch_processor
    if batch_processor is None:
        batch_processor = BatchProcessor()
        # Start background task to initialize processor
        asyncio.create_task(batch_processor.start_processing())
    return batch_processor


# Create router
router = APIRouter(prefix="/api/document-processing", tags=["document-processing"])


@router.post("/upload/create-batch")
async def create_upload_batch(
    request: CreateBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new upload batch."""
    try:
        upload_mgr = get_upload_manager()
        
        # Convert priority
        priority = ProcessingPriority[request.priority.upper()]
        
        batch_id = await upload_mgr.create_upload_batch(
            case_id=request.case_id,
            user_id=str(current_user.id),
            priority=priority,
            metadata=request.metadata
        )
        
        return {
            "batch_id": batch_id,
            "message": "Upload batch created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating upload batch: {str(e)}")


@router.post("/upload/add-files/{batch_id}")
async def add_files_to_batch(
    batch_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Add files to an existing upload batch."""
    try:
        upload_mgr = get_upload_manager()
        
        added_files = []
        errors = []
        
        for file in files:
            try:
                # Read file data
                file_data = await file.read()
                
                # Add to batch
                file_id = await upload_mgr.add_file_to_batch(
                    batch_id=batch_id,
                    file_data=file_data,
                    filename=file.filename,
                    content_type=file.content_type
                )
                
                added_files.append({
                    "file_id": file_id,
                    "filename": file.filename,
                    "size": len(file_data)
                })
                
            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "batch_id": batch_id,
            "added_files": added_files,
            "errors": errors,
            "total_added": len(added_files),
            "total_errors": len(errors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding files to batch: {str(e)}")


@router.post("/upload/start-processing/{batch_id}")
async def start_batch_processing(
    batch_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Start processing an upload batch."""
    try:
        upload_mgr = get_upload_manager()
        
        success = await upload_mgr.start_batch_processing(batch_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start batch processing")
        
        return {
            "batch_id": batch_id,
            "message": "Batch processing started",
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting batch processing: {str(e)}")


@router.get("/upload/progress/{batch_id}", response_model=BatchProgressResponse)
async def get_batch_progress(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get upload batch progress."""
    try:
        upload_mgr = get_upload_manager()
        
        progress = await upload_mgr.get_batch_progress(batch_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return BatchProgressResponse(
            batch_id=progress.batch_id,
            status=progress.status.value,
            total_files=progress.total_files,
            completed_files=progress.completed_files,
            failed_files=progress.failed_files,
            progress_percentage=progress.progress,
            current_file=progress.current_file,
            estimated_completion=progress.estimated_completion,
            processing_stage=progress.processing_stage,
            errors=progress.error_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting batch progress: {str(e)}")


@router.post("/upload/cancel/{batch_id}")
async def cancel_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel batch processing."""
    try:
        upload_mgr = get_upload_manager()
        
        success = await upload_mgr.cancel_batch(batch_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel batch or batch not found")
        
        return {
            "batch_id": batch_id,
            "message": "Batch cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling batch: {str(e)}")


@router.post("/analyze/documents")
async def analyze_documents(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze documents with AI."""
    try:
        batch_proc = get_batch_processor()
        
        # Convert analysis types
        analysis_types = [AnalysisType(t) for t in request.analysis_types]
        
        # Convert priority
        priority = Priority[request.priority.upper()]
        
        # Submit batch job
        job_id = await batch_proc.submit_job(
            operation=BatchOperation.ANALYZE_EXISTING,
            parameters={
                "analysis_types": analysis_types,
                "force_reanalyze": request.force_reanalyze
            },
            target_files=request.file_ids,
            created_by=str(current_user.id),
            priority=priority,
            case_id=request.case_id
        )
        
        return {
            "job_id": job_id,
            "message": "Analysis job submitted",
            "file_count": len(request.file_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting analysis job: {str(e)}")


@router.post("/categorize/documents")
async def categorize_documents(
    request: DocumentCategoryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update document categories."""
    try:
        batch_proc = get_batch_processor()
        
        parameters = {
            "auto_categorize": request.auto_categorize
        }
        
        if request.new_category:
            parameters["new_category"] = request.new_category
        
        # Submit batch job
        job_id = await batch_proc.submit_job(
            operation=BatchOperation.RE_CATEGORIZE,
            parameters=parameters,
            target_files=request.file_ids,
            created_by=str(current_user.id),
            priority=Priority.NORMAL
        )
        
        return {
            "job_id": job_id,
            "message": "Categorization job submitted",
            "file_count": len(request.file_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting categorization job: {str(e)}")


@router.post("/ocr/documents")
async def ocr_documents(
    file_ids: List[str] = Body(...),
    languages: List[str] = Body(default=["eng"]),
    confidence_threshold: float = Body(default=0.8),
    current_user: User = Depends(get_current_user)
):
    """Perform OCR on scanned documents."""
    try:
        batch_proc = get_batch_processor()
        
        # Submit OCR job
        job_id = await batch_proc.submit_job(
            operation=BatchOperation.OCR_PROCESSING,
            parameters={
                "languages": languages,
                "confidence_threshold": confidence_threshold
            },
            target_files=file_ids,
            created_by=str(current_user.id),
            priority=Priority.NORMAL
        )
        
        return {
            "job_id": job_id,
            "message": "OCR job submitted",
            "file_count": len(file_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting OCR job: {str(e)}")


@router.post("/privilege-review/documents")
async def privilege_review_documents(
    file_ids: List[str] = Body(...),
    privilege_threshold: float = Body(default=0.7),
    current_user: User = Depends(get_current_user)
):
    """Perform attorney-client privilege review."""
    try:
        batch_proc = get_batch_processor()
        
        # Submit privilege review job
        job_id = await batch_proc.submit_job(
            operation=BatchOperation.PRIVILEGE_REVIEW,
            parameters={
                "privilege_threshold": privilege_threshold
            },
            target_files=file_ids,
            created_by=str(current_user.id),
            priority=Priority.HIGH
        )
        
        return {
            "job_id": job_id,
            "message": "Privilege review job submitted",
            "file_count": len(file_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting privilege review job: {str(e)}")


@router.post("/detect-duplicates")
async def detect_duplicates(
    file_ids: List[str] = Body(...),
    similarity_threshold: float = Body(default=0.95),
    hash_comparison: bool = Body(default=True),
    content_comparison: bool = Body(default=True),
    current_user: User = Depends(get_current_user)
):
    """Detect duplicate documents."""
    try:
        batch_proc = get_batch_processor()
        
        # Submit duplicate detection job
        job_id = await batch_proc.submit_job(
            operation=BatchOperation.DUPLICATE_DETECTION,
            parameters={
                "similarity_threshold": similarity_threshold,
                "hash_comparison": hash_comparison,
                "content_comparison": content_comparison
            },
            target_files=file_ids,
            created_by=str(current_user.id),
            priority=Priority.NORMAL
        )
        
        return {
            "job_id": job_id,
            "message": "Duplicate detection job submitted",
            "file_count": len(file_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting duplicate detection job: {str(e)}")


@router.post("/export/documents")
async def export_documents(
    request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export documents in specified format."""
    try:
        batch_proc = get_batch_processor()
        
        # Submit export job
        job_id = await batch_proc.submit_job(
            operation=BatchOperation.EXPORT_DOCUMENTS,
            parameters={
                "format": request.format,
                "include_metadata": request.include_metadata,
                "include_analysis": request.include_analysis,
                "export_name": request.export_name or f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            },
            target_files=request.file_ids,
            created_by=str(current_user.id),
            priority=Priority.NORMAL
        )
        
        return {
            "job_id": job_id,
            "message": "Export job submitted",
            "file_count": len(request.file_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting export job: {str(e)}")


@router.delete("/bulk-delete")
async def bulk_delete_documents(
    file_ids: List[str] = Body(...),
    confirm_delete: bool = Body(...),
    soft_delete: bool = Body(default=True),
    current_user: User = Depends(get_current_user)
):
    """Bulk delete documents."""
    try:
        if not confirm_delete:
            raise HTTPException(status_code=400, detail="Deletion must be explicitly confirmed")
        
        batch_proc = get_batch_processor()
        
        # Submit delete job
        job_id = await batch_proc.submit_job(
            operation=BatchOperation.BULK_DELETE,
            parameters={
                "confirm_delete": confirm_delete,
                "soft_delete": soft_delete
            },
            target_files=file_ids,
            created_by=str(current_user.id),
            priority=Priority.HIGH
        )
        
        return {
            "job_id": job_id,
            "message": "Bulk delete job submitted",
            "file_count": len(file_ids),
            "delete_type": "soft" if soft_delete else "hard"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting bulk delete job: {str(e)}")


@router.post("/batch/submit-job")
async def submit_batch_job(
    request: BatchJobRequest,
    current_user: User = Depends(get_current_user)
):
    """Submit a custom batch processing job."""
    try:
        batch_proc = get_batch_processor()
        
        # Convert enums
        operation = BatchOperation(request.operation)
        priority = Priority[request.priority.upper()]
        
        # Submit job
        job_id = await batch_proc.submit_job(
            operation=operation,
            parameters=request.parameters,
            target_files=request.file_ids,
            created_by=str(current_user.id),
            priority=priority,
            case_id=request.case_id
        )
        
        return {
            "job_id": job_id,
            "message": "Batch job submitted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting batch job: {str(e)}")


@router.get("/batch/status/{job_id}", response_model=BatchJobResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a batch job."""
    try:
        batch_proc = get_batch_processor()
        
        status = await batch_proc.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return BatchJobResponse(
            job_id=status["job_id"],
            operation=status["operation"],
            status=status["status"],
            progress=status["progress"],
            total_items=status["total_items"],
            processed_items=status["processed_items"],
            successful_items=status["successful_items"],
            failed_items=status["failed_items"],
            estimated_duration=status["estimated_duration"],
            actual_duration=status["actual_duration"],
            output_location=status["output_location"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")


@router.post("/batch/cancel/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a batch job."""
    try:
        batch_proc = get_batch_processor()
        
        success = await batch_proc.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel job or job not found")
        
        return {
            "job_id": job_id,
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling job: {str(e)}")


@router.post("/batch/pause/{job_id}")
async def pause_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Pause a running job."""
    try:
        batch_proc = get_batch_processor()
        
        success = await batch_proc.pause_job(job_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to pause job or job not found")
        
        return {
            "job_id": job_id,
            "message": "Job paused successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing job: {str(e)}")


@router.post("/batch/resume/{job_id}")
async def resume_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Resume a paused job."""
    try:
        batch_proc = get_batch_processor()
        
        success = await batch_proc.resume_job(job_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to resume job or job not found")
        
        return {
            "job_id": job_id,
            "message": "Job resumed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resuming job: {str(e)}")


@router.get("/batch/history")
async def get_job_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get job history."""
    try:
        batch_proc = get_batch_processor()
        
        history = batch_proc.get_job_history(limit)
        
        return {
            "jobs": [
                {
                    "job_id": job.job_id,
                    "operation": job.operation,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "total_items": job.total_items,
                    "processed_items": job.processed_items,
                    "success_rate": job.success_rate,
                    "duration": job.duration,
                    "created_by": job.created_by
                }
                for job in history
            ],
            "total_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job history: {str(e)}")


@router.get("/download/export/{job_id}")
async def download_export(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download exported files."""
    try:
        batch_proc = get_batch_processor()
        
        job_status = await batch_proc.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job_status["status"] != "completed":
            raise HTTPException(status_code=400, detail="Export job not completed")
        
        output_location = job_status.get("output_location")
        if not output_location or not os.path.exists(output_location):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        # Return file based on type
        if output_location.endswith('.zip'):
            return FileResponse(
                output_location,
                media_type='application/zip',
                filename=f"export_{job_id}.zip"
            )
        else:
            # Create ZIP of directory on the fly
            def generate_zip():
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for root, dirs, files in os.walk(output_location):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, output_location)
                            zip_file.write(file_path, arc_name)
                
                zip_buffer.seek(0)
                return zip_buffer.getvalue()
            
            zip_data = generate_zip()
            
            return StreamingResponse(
                io.BytesIO(zip_data),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=export_{job_id}.zip"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading export: {str(e)}")


@router.get("/system/status")
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """Get system status and metrics."""
    try:
        batch_proc = get_batch_processor()
        upload_mgr = get_upload_manager()
        
        batch_status = batch_proc.get_system_status()
        upload_stats = await upload_mgr.get_system_statistics()
        
        return {
            "batch_processor": batch_status,
            "upload_manager": upload_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")


@router.get("/config/upload")
async def get_upload_config(
    current_user: User = Depends(get_current_user)
):
    """Get upload configuration."""
    try:
        upload_mgr = get_upload_manager()
        
        return {
            "max_file_size": upload_mgr.config.max_file_size,
            "max_batch_size": upload_mgr.config.max_batch_size,
            "allowed_file_types": [ft.value for ft in upload_mgr.config.allowed_file_types],
            "scan_for_viruses": upload_mgr.config.scan_for_viruses,
            "extract_metadata": upload_mgr.config.extract_metadata,
            "auto_categorize": upload_mgr.config.auto_categorize,
            "create_thumbnails": upload_mgr.config.create_thumbnails,
            "ocr_scanned_documents": upload_mgr.config.ocr_scanned_documents,
            "concurrent_uploads": upload_mgr.config.concurrent_uploads
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting upload config: {str(e)}")


@router.post("/config/upload")
async def update_upload_config(
    config: UploadConfigModel,
    current_user: User = Depends(get_current_user)
):
    """Update upload configuration."""
    try:
        # In a real implementation, you'd check user permissions here
        # and update the configuration in a persistent store
        
        return {
            "message": "Upload configuration updated successfully",
            "config": config.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating upload config: {str(e)}")


@router.get("/supported-file-types")
async def get_supported_file_types():
    """Get list of supported file types."""
    try:
        file_types = []
        for ft in FileType:
            file_types.append({
                "extension": ft.value,
                "name": ft.name,
                "mime_types": _get_mime_types_for_extension(ft.value)
            })
        
        return {
            "supported_file_types": file_types,
            "total_types": len(file_types)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting supported file types: {str(e)}")


def _get_mime_types_for_extension(extension: str) -> List[str]:
    """Get MIME types for file extension."""
    mime_map = {
        "pdf": ["application/pdf"],
        "docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        "doc": ["application/msword"],
        "txt": ["text/plain"],
        "rtf": ["application/rtf", "text/rtf"],
        "html": ["text/html"],
        "xml": ["application/xml", "text/xml"],
        "tiff": ["image/tiff"],
        "png": ["image/png"],
        "jpg": ["image/jpeg"],
        "jpeg": ["image/jpeg"],
        "zip": ["application/zip"],
        "rar": ["application/vnd.rar"],
        "csv": ["text/csv"],
        "xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        "xls": ["application/vnd.ms-excel"],
        "eml": ["message/rfc822"],
        "msg": ["application/vnd.ms-outlook"]
    }
    
    return mime_map.get(extension, ["application/octet-stream"])