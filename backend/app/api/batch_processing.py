"""
Batch Document Processing API
Handles bulk document uploads with background processing, progress tracking, and rate limiting
"""

import logging
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..src.core.database import get_db
from ..src.services.dual_ai_service import dual_ai_service
from ..src.services.pdf_service import pdf_service
from ..models.legal_documents import Document, BatchJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/batch", tags=["Batch Processing"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class BatchJobStatus(BaseModel):
    """Status of a batch processing job"""
    job_id: str
    session_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    total_documents: int
    processed_documents: int
    successful_documents: int
    failed_documents: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float
    estimated_time_remaining: Optional[int] = None  # seconds
    errors: List[Dict[str, str]] = []


class BatchDocument(BaseModel):
    """Single document in a batch result"""
    document_id: str
    filename: str
    status: str  # success, failed, pending
    summary: Optional[str] = None
    document_type: Optional[str] = None
    error: Optional[str] = None
    processed_at: Optional[datetime] = None


class BatchResult(BaseModel):
    """Result of batch processing"""
    job_id: str
    session_id: str
    total_documents: int
    successful_count: int
    failed_count: int
    documents: List[BatchDocument]
    processing_time_seconds: float


# =============================================================================
# DATABASE-BACKED JOB TRACKING
# =============================================================================

# Keep in-memory dict as fallback for backward compatibility
batch_jobs: Dict[str, Dict[str, Any]] = {}


def create_batch_job(job_id: str, session_id: str, total_docs: int, db: Session):
    """Create a new batch job tracker in database"""
    batch_job = BatchJob(
        id=job_id,
        session_id=session_id,
        status="pending",
        total_documents=total_docs,
        processed_documents=0,
        successful_documents=0,
        failed_documents=0,
        errors=[],
        documents=[]
    )
    db.add(batch_job)
    db.commit()
    db.refresh(batch_job)

    logger.info(f"Created batch job in database: {job_id}")
    return batch_job


def update_batch_job(job_id: str, db: Session, **kwargs):
    """Update batch job status in database"""
    batch_job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
    if batch_job:
        for key, value in kwargs.items():
            if hasattr(batch_job, key):
                setattr(batch_job, key, value)
        db.commit()
        db.refresh(batch_job)
        logger.debug(f"Updated batch job {job_id}: {kwargs}")
    return batch_job


def get_batch_job(job_id: str, db: Session) -> Optional[BatchJob]:
    """Get batch job from database"""
    return db.query(BatchJob).filter(BatchJob.id == job_id).first()


# =============================================================================
# BATCH PROCESSING LOGIC
# =============================================================================

async def process_document_async(
    file_contents: bytes,
    filename: str,
    session_id: str,
    job_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Process a single document asynchronously.

    Returns:
        Result dict with status, document_id, and any errors
    """
    document_id = str(uuid.uuid4())

    try:
        # Validate PDF
        if not pdf_service.validate_pdf(file_contents):
            return {
                "status": "failed",
                "filename": filename,
                "document_id": None,
                "error": "Invalid PDF file"
            }

        # Extract text
        extracted_text = pdf_service.extract_text_from_pdf(file_contents, filename)

        if not extracted_text or len(extracted_text.strip()) < 10:
            return {
                "status": "failed",
                "filename": filename,
                "document_id": None,
                "error": "Could not extract text from PDF"
            }

        # Add small delay to avoid rate limits (adjust based on your API tier)
        await asyncio.sleep(0.5)

        # Analyze with AI
        analysis_result = await dual_ai_service.analyze_document(extracted_text, filename)

        # Save to database
        document = Document(
            id=document_id,
            session_id=session_id,
            file_name=filename,
            file_type="application/pdf",
            file_size=len(file_contents),
            text_content=extracted_text,
            summary=analysis_result.get('summary'),
            document_type=analysis_result.get('document_type'),
            parties=analysis_result.get('parties', []),
            important_dates=analysis_result.get('key_dates', []),
            key_figures=analysis_result.get('key_figures', []),
            keywords=analysis_result.get('key_terms', []),
            analysis_data=analysis_result
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"[{job_id}] Successfully processed: {filename}")

        return {
            "status": "success",
            "filename": filename,
            "document_id": document_id,
            "summary": analysis_result.get('summary'),
            "document_type": analysis_result.get('document_type'),
            "error": None,
            "processed_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"[{job_id}] Error processing {filename}: {str(e)}")
        return {
            "status": "failed",
            "filename": filename,
            "document_id": None,
            "error": str(e),
            "processed_at": datetime.utcnow()
        }


async def process_batch_job(
    job_id: str,
    session_id: str,
    files_data: List[tuple],  # List of (file_contents, filename)
    db: Session,
    max_concurrent: int = 3  # Process 3 documents at a time
):
    """
    Background task to process a batch of documents.

    Args:
        job_id: Batch job identifier
        session_id: Session identifier
        files_data: List of (file_contents, filename) tuples
        db: Database session
        max_concurrent: Maximum concurrent processing tasks
    """
    # Update job to processing status
    update_batch_job(job_id, db, status="processing", started_at=datetime.utcnow())

    logger.info(f"[{job_id}] Starting batch processing: {len(files_data)} documents")

    # Process documents in chunks to avoid overwhelming the API
    results = []
    for i in range(0, len(files_data), max_concurrent):
        chunk = files_data[i:i + max_concurrent]

        # Process chunk concurrently
        tasks = [
            process_document_async(file_contents, filename, session_id, job_id, db)
            for file_contents, filename in chunk
        ]

        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Get current job state from database
        job = get_batch_job(job_id, db)
        if not job:
            logger.error(f"[{job_id}] Job not found in database!")
            return

        # Update job status
        for result in chunk_results:
            if isinstance(result, Exception):
                job.failed_documents += 1
                job.errors = job.errors + [{"error": str(result)}]
                logger.error(f"[{job_id}] Task exception: {result}")
            else:
                results.append(result)
                job.processed_documents += 1

                if result["status"] == "success":
                    job.successful_documents += 1
                else:
                    job.failed_documents += 1
                    job.errors = job.errors + [{
                        "filename": result["filename"],
                        "error": result["error"]
                    }]

        # Save progress to database
        job.documents = results
        db.commit()

        # Update progress
        progress = (job.processed_documents / job.total_documents) * 100
        logger.info(f"[{job_id}] Progress: {progress:.1f}% ({job.processed_documents}/{job.total_documents})")

    # Mark job as completed
    job = get_batch_job(job_id, db)
    if job:
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.documents = results
        db.commit()

        if job.started_at:
            processing_time = (job.completed_at - job.started_at).total_seconds()
            logger.info(
                f"[{job_id}] Batch completed: {job.successful_documents} succeeded, "
                f"{job.failed_documents} failed in {processing_time:.1f}s"
            )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def batch_upload_documents(
    files: List[UploadFile] = File(..., description="Multiple files to process"),
    session_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload and process multiple documents in the background.

    This endpoint:
    1. Accepts multiple PDF files
    2. Validates all files
    3. Starts background processing
    4. Returns immediately with job_id for status tracking

    Args:
        files: List of PDF files to process
        session_id: Optional session identifier (generated if not provided)

    Returns:
        - job_id: Use this to check processing status
        - session_id: Session identifier for retrieving documents
        - total_documents: Number of documents queued
        - estimated_time: Rough estimate of completion time
    """
    try:
        # Log received files for debugging
        logger.info(f"[BATCH UPLOAD DEBUG] Received {len(files)} files for batch upload")
        for idx, file in enumerate(files):
            logger.info(f"[BATCH UPLOAD DEBUG] File {idx + 1}: {file.filename}")

        # Validate input
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )

        if len(files) > 500:  # Safety limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 500 documents per batch"
            )

        # Validate file types (allow PDF, images, Word documents)
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        for file in files:
            if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.filename}. Allowed: {', '.join(allowed_extensions)}"
                )

        # Generate IDs
        job_id = str(uuid.uuid4())
        if not session_id:
            session_id = str(uuid.uuid4())

        # Create job tracker in database
        create_batch_job(job_id, session_id, len(files), db)

        # Read all files into memory (for background task)
        files_data = []
        total_size = 0
        logger.info(f"[BATCH UPLOAD DEBUG] Reading file contents...")
        for idx, file in enumerate(files):
            contents = await file.read()
            file_size = len(contents)
            total_size += file_size
            logger.info(f"[BATCH UPLOAD DEBUG] File {idx + 1} read: {file.filename} - Size: {file_size} bytes ({file_size / 1024:.2f} KB)")
            files_data.append((contents, file.filename))

        logger.info(f"[BATCH UPLOAD DEBUG] Total size of all files: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)")

        # Check total size (prevent memory issues)
        max_batch_size = 100 * 1024 * 1024  # 100 MB total
        if total_size > max_batch_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Total batch size exceeds {max_batch_size / 1024 / 1024:.0f}MB limit"
            )

        # Start background processing
        background_tasks.add_task(
            process_batch_job,
            job_id,
            session_id,
            files_data,
            db
        )

        # Estimate completion time (rough: 5 seconds per document)
        estimated_seconds = len(files) * 5

        logger.info(
            f"Batch upload initiated: job_id={job_id}, "
            f"documents={len(files)}, size={total_size/1024:.1f}KB"
        )

        response_data = {
            "success": True,
            "job_id": job_id,
            "session_id": session_id,
            "total_documents": len(files),
            "status": "processing",
            "message": "Batch processing started in background",
            "estimated_completion_seconds": estimated_seconds,
            "check_status_url": f"/api/v1/batch/status/{job_id}"
        }

        logger.info(f"[BATCH UPLOAD DEBUG] Returning response: {response_data}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=BatchJobStatus)
async def get_batch_status(job_id: str, db: Session = Depends(get_db)) -> BatchJobStatus:
    """
    Get the status of a batch processing job.

    Poll this endpoint to track progress of your batch upload.

    Returns:
        - status: pending, processing, completed, or failed
        - progress_percentage: How much is done (0-100)
        - processed_documents: Count of processed documents
        - successful_documents: Count of successful analyses
        - failed_documents: Count of failures
        - errors: List of error details
    """
    job = get_batch_job(job_id, db)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job not found: {job_id}"
        )

    # Calculate progress
    progress = 0.0
    estimated_remaining = None

    if job.total_documents > 0:
        progress = (job.processed_documents / job.total_documents) * 100

        # Estimate time remaining
        if job.started_at and job.processed_documents > 0:
            elapsed = (datetime.utcnow() - job.started_at).total_seconds()
            avg_time_per_doc = elapsed / job.processed_documents
            remaining_docs = job.total_documents - job.processed_documents
            estimated_remaining = int(avg_time_per_doc * remaining_docs)

    return BatchJobStatus(
        job_id=job.id,
        session_id=job.session_id,
        status=job.status,
        total_documents=job.total_documents,
        processed_documents=job.processed_documents,
        successful_documents=job.successful_documents,
        failed_documents=job.failed_documents,
        started_at=job.started_at,
        completed_at=job.completed_at,
        progress_percentage=round(progress, 2),
        estimated_time_remaining=estimated_remaining,
        errors=job.errors or []
    )


@router.get("/result/{job_id}", response_model=BatchResult)
async def get_batch_result(job_id: str, db: Session = Depends(get_db)) -> BatchResult:
    """
    Get the final results of a completed batch job.

    Only call this after status shows 'completed'.

    Returns:
        - Full list of all processed documents
        - Success/failure breakdown
        - Document IDs for successful uploads
    """
    job = get_batch_job(job_id, db)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job not found: {job_id}"
        )

    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch job not yet completed. Current status: {job.status}"
        )

    processing_time = 0.0
    if job.started_at and job.completed_at:
        processing_time = (job.completed_at - job.started_at).total_seconds()

    documents = [
        BatchDocument(
            document_id=doc.get("document_id") or "",
            filename=doc.get("filename", ""),
            status=doc.get("status", "unknown"),
            summary=doc.get("summary"),
            document_type=doc.get("document_type"),
            error=doc.get("error"),
            processed_at=doc.get("processed_at")
        )
        for doc in (job.documents or [])
    ]

    return BatchResult(
        job_id=job.id,
        session_id=job.session_id,
        total_documents=job.total_documents,
        successful_count=job.successful_documents,
        failed_count=job.failed_documents,
        documents=documents,
        processing_time_seconds=processing_time
    )


@router.delete("/job/{job_id}")
async def cancel_batch_job(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Cancel a batch processing job (if still running) or delete job records.

    Note: Cannot stop documents currently being processed,
    but will prevent new documents from starting.
    """
    job = get_batch_job(job_id, db)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job not found: {job_id}"
        )

    if job.status == "processing":
        # Mark as cancelled (background task should check this)
        update_batch_job(job_id, db, status="cancelled")
        logger.info(f"Batch job cancelled: {job_id}")
        return {"message": "Batch job cancellation requested", "job_id": job_id}
    else:
        # Delete completed/failed jobs from database
        db.delete(job)
        db.commit()
        logger.info(f"Batch job deleted: {job_id}")
        return {"message": "Batch job deleted", "job_id": job_id}


@router.get("/jobs")
async def list_batch_jobs(
    session_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all batch jobs, optionally filtered by session or status.

    Args:
        session_id: Filter by session
        status: Filter by status (pending, processing, completed, failed)

    Returns:
        List of batch jobs with summary information
    """
    # Query database with filters
    query = db.query(BatchJob)

    # Filter by session_id
    if session_id:
        query = query.filter(BatchJob.session_id == session_id)

    # Filter by status
    if status:
        query = query.filter(BatchJob.status == status)

    jobs = query.order_by(BatchJob.created_at.desc()).all()

    # Return summary (without full document list)
    return {
        "total_jobs": len(jobs),
        "jobs": [
            {
                "job_id": j.id,
                "session_id": j.session_id,
                "status": j.status,
                "total_documents": j.total_documents,
                "processed_documents": j.processed_documents,
                "successful_documents": j.successful_documents,
                "failed_documents": j.failed_documents,
                "started_at": j.started_at,
                "completed_at": j.completed_at
            }
            for j in jobs
        ]
    }
