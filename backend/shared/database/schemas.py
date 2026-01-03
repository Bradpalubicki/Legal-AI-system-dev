"""
Pydantic Schemas for Legal AI System Database Models

Request/Response schemas for API endpoints using the TrackedDocket
and RecapTask models. Provides validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator
from pydantic.types import PositiveInt, NonNegativeInt

from .models import (
    DocketTrackingStatus, CourtType, DocumentType,
    RecapTaskStatus, RecapTaskType, Priority
)


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class TimestampSchema(BaseModel):
    """Base schema with timestamp fields"""
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BaseSchema(TimestampSchema):
    """Base schema with common fields"""
    id: int = Field(..., description="Primary key ID")


# =============================================================================
# TRACKED DOCKET SCHEMAS
# =============================================================================

class TrackedDocketBase(BaseModel):
    """Base schema for TrackedDocket"""
    docket_number: str = Field(..., max_length=100, description="Docket number")
    court_id: str = Field(..., max_length=50, description="Court identifier")
    court_name: str = Field(..., max_length=200, description="Court name")
    court_type: CourtType = Field(default=CourtType.DISTRICT, description="Type of court")
    
    case_name: str = Field(..., max_length=500, description="Case name")
    case_title: Optional[str] = Field(None, description="Full case title")
    nature_of_suit: Optional[str] = Field(None, max_length=100, description="Nature of suit")
    cause_of_action: Optional[str] = Field(None, max_length=200, description="Cause of action")
    jurisdiction: Optional[str] = Field(None, max_length=100, description="Jurisdiction")
    
    plaintiff: Optional[str] = Field(None, max_length=300, description="Plaintiff name")
    defendant: Optional[str] = Field(None, max_length=300, description="Defendant name")
    judge_assigned: Optional[str] = Field(None, max_length=200, description="Assigned judge")
    magistrate_judge: Optional[str] = Field(None, max_length=200, description="Magistrate judge")
    
    tracking_status: DocketTrackingStatus = Field(default=DocketTrackingStatus.ACTIVE)
    auto_fetch_enabled: bool = Field(default=True, description="Enable automatic fetching")
    fetch_interval_hours: PositiveInt = Field(default=24, description="Fetch interval in hours")
    notification_enabled: bool = Field(default=True, description="Enable notifications")
    
    tags: Optional[List[str]] = Field(None, description="Organization tags")
    notes: Optional[str] = Field(None, description="Additional notes")


class TrackedDocketCreate(TrackedDocketBase):
    """Schema for creating a new TrackedDocket"""
    pacer_case_id: Optional[str] = Field(None, max_length=50, description="PACER case ID")
    client_id: Optional[int] = Field(None, description="Associated client ID")
    matter_id: Optional[int] = Field(None, description="Associated matter ID")
    assigned_attorney_id: Optional[int] = Field(None, description="Assigned attorney ID")


class TrackedDocketUpdate(BaseModel):
    """Schema for updating a TrackedDocket"""
    case_name: Optional[str] = Field(None, max_length=500)
    case_title: Optional[str] = Field(None)
    tracking_status: Optional[DocketTrackingStatus] = Field(None)
    auto_fetch_enabled: Optional[bool] = Field(None)
    fetch_interval_hours: Optional[PositiveInt] = Field(None)
    notification_enabled: Optional[bool] = Field(None)
    notes: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(None)
    assigned_attorney_id: Optional[int] = Field(None)


class TrackedDocketResponse(TrackedDocketBase, BaseSchema):
    """Schema for TrackedDocket API responses"""
    pacer_case_id: Optional[str] = Field(None, description="PACER case ID")
    pacer_case_guid: Optional[UUID] = Field(None, description="PACER case GUID")
    pacer_last_fetch: Optional[datetime] = Field(None, description="Last PACER fetch time")
    pacer_fetch_count: NonNegativeInt = Field(default=0, description="PACER fetch count")
    
    date_filed: Optional[datetime] = Field(None, description="Case filing date")
    date_terminated: Optional[datetime] = Field(None, description="Case termination date")
    date_last_filing: Optional[datetime] = Field(None, description="Last filing date")
    case_status: Optional[str] = Field(None, description="Case status")
    
    total_documents: NonNegativeInt = Field(default=0, description="Total document count")
    documents_downloaded: NonNegativeInt = Field(default=0, description="Downloaded documents")
    last_document_number: NonNegativeInt = Field(default=0, description="Last document number")
    
    filing_fee: Optional[Decimal] = Field(None, description="Filing fee amount")
    pacer_cost_actual: Optional[Decimal] = Field(None, description="Actual PACER costs")
    
    client_id: Optional[int] = Field(None, description="Associated client ID")
    matter_id: Optional[int] = Field(None, description="Associated matter ID")
    assigned_attorney_id: Optional[int] = Field(None, description="Assigned attorney ID")
    
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    archived: bool = Field(default=False, description="Archived status")
    
    class Config:
        from_attributes = True


class TrackedDocketListResponse(BaseModel):
    """Schema for paginated TrackedDocket list responses"""
    items: List[TrackedDocketResponse]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


# =============================================================================
# RECAP TASK SCHEMAS
# =============================================================================

class RecapTaskBase(BaseModel):
    """Base schema for RecapTask"""
    task_type: RecapTaskType = Field(..., description="Type of task")
    task_name: str = Field(..., max_length=200, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    priority: Priority = Field(default=Priority.NORMAL, description="Task priority")
    
    max_retries: NonNegativeInt = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: PositiveInt = Field(default=300, description="Retry delay in seconds")
    
    task_params: Optional[Dict[str, Any]] = Field(None, description="Task parameters")
    task_config: Optional[Dict[str, Any]] = Field(None, description="Task configuration")
    
    notification_recipients: Optional[List[str]] = Field(None, description="Notification recipients")
    alert_on_failure: bool = Field(default=True, description="Alert on failure")
    alert_on_completion: bool = Field(default=False, description="Alert on completion")


class RecapTaskCreate(RecapTaskBase):
    """Schema for creating a new RecapTask"""
    tracked_docket_id: Optional[int] = Field(None, description="Associated docket ID")
    parent_task_id: Optional[int] = Field(None, description="Parent task ID")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    queue_name: str = Field(default="default", description="Task queue name")


class RecapTaskUpdate(BaseModel):
    """Schema for updating a RecapTask"""
    status: Optional[RecapTaskStatus] = Field(None, description="Task status")
    progress_percent: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    priority: Optional[Priority] = Field(None, description="Task priority")
    task_config: Optional[Dict[str, Any]] = Field(None, description="Task configuration")
    notification_recipients: Optional[List[str]] = Field(None, description="Notification recipients")
    
    @validator('progress_percent')
    def validate_progress(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Progress must be between 0 and 100')
        return v


class RecapTaskResponse(RecapTaskBase, BaseSchema):
    """Schema for RecapTask API responses"""
    task_id: UUID = Field(..., description="Unique task identifier")
    status: RecapTaskStatus = Field(..., description="Current task status")
    progress_percent: NonNegativeInt = Field(default=0, description="Progress percentage")
    
    scheduled_at: datetime = Field(..., description="Scheduled execution time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    
    retry_count: NonNegativeInt = Field(default=0, description="Current retry count")
    last_retry_at: Optional[datetime] = Field(None, description="Last retry time")
    
    result_data: Optional[Dict[str, Any]] = Field(None, description="Task results")
    result_metadata: Optional[Dict[str, Any]] = Field(None, description="Result metadata")
    
    error_message: Optional[str] = Field(None, description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    
    tracked_docket_id: Optional[int] = Field(None, description="Associated docket ID")
    parent_task_id: Optional[int] = Field(None, description="Parent task ID")
    user_id: Optional[int] = Field(None, description="User who created the task")
    
    celery_task_id: Optional[str] = Field(None, description="Celery task ID")
    worker_id: Optional[str] = Field(None, description="Worker ID")
    queue_name: str = Field(default="default", description="Task queue name")
    
    pacer_cost_actual: Optional[Decimal] = Field(None, description="Actual PACER cost")
    memory_usage_mb: Optional[int] = Field(None, description="Memory usage in MB")
    
    notification_sent: bool = Field(default=False, description="Notification sent status")
    archived: bool = Field(default=False, description="Archived status")
    
    class Config:
        from_attributes = True


class RecapTaskListResponse(BaseModel):
    """Schema for paginated RecapTask list responses"""
    items: List[RecapTaskResponse]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


# =============================================================================
# DOCKET DOCUMENT SCHEMAS
# =============================================================================

class DocketDocumentBase(BaseModel):
    """Base schema for DocketDocument"""
    document_number: PositiveInt = Field(..., description="Document number")
    attachment_number: NonNegativeInt = Field(default=0, description="Attachment number")
    description: str = Field(..., description="Document description")
    document_type: DocumentType = Field(default=DocumentType.OTHER, description="Document type")
    
    date_filed: datetime = Field(..., description="Filing date")
    filed_by: Optional[str] = Field(None, max_length=300, description="Filed by")
    docket_text: Optional[str] = Field(None, description="Docket entry text")
    
    is_available: bool = Field(default=True, description="Document availability")
    cost_cents: Optional[int] = Field(None, description="PACER cost in cents")
    is_free: bool = Field(default=False, description="Free document flag")


class DocketDocumentCreate(DocketDocumentBase):
    """Schema for creating a new DocketDocument"""
    tracked_docket_id: int = Field(..., description="Associated docket ID")
    pacer_doc_id: Optional[str] = Field(None, max_length=50, description="PACER document ID")


class DocketDocumentResponse(DocketDocumentBase, BaseSchema):
    """Schema for DocketDocument API responses"""
    pacer_doc_id: Optional[str] = Field(None, description="PACER document ID")
    pacer_seq_number: Optional[int] = Field(None, description="PACER sequence number")
    
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    page_count: Optional[int] = Field(None, description="Number of pages")
    
    downloaded: bool = Field(default=False, description="Download status")
    downloaded_at: Optional[datetime] = Field(None, description="Download timestamp")
    processed: bool = Field(default=False, description="Processing status")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    
    file_path: Optional[str] = Field(None, description="File storage path")
    file_hash: Optional[str] = Field(None, description="File hash (SHA-256)")
    mime_type: Optional[str] = Field(None, description="MIME type")
    
    tracked_docket_id: int = Field(..., description="Associated docket ID")
    
    class Config:
        from_attributes = True


# =============================================================================
# SEARCH AND FILTER SCHEMAS
# =============================================================================

class DocketSearchFilters(BaseModel):
    """Schema for docket search filters"""
    court_id: Optional[str] = Field(None, description="Filter by court ID")
    court_type: Optional[CourtType] = Field(None, description="Filter by court type")
    tracking_status: Optional[DocketTrackingStatus] = Field(None, description="Filter by status")
    case_name: Optional[str] = Field(None, description="Search case name")
    docket_number: Optional[str] = Field(None, description="Search docket number")
    judge_assigned: Optional[str] = Field(None, description="Filter by judge")
    client_id: Optional[int] = Field(None, description="Filter by client")
    matter_id: Optional[int] = Field(None, description="Filter by matter")
    date_filed_from: Optional[datetime] = Field(None, description="Filed date range start")
    date_filed_to: Optional[datetime] = Field(None, description="Filed date range end")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    archived: Optional[bool] = Field(None, description="Filter by archived status")


class TaskSearchFilters(BaseModel):
    """Schema for task search filters"""
    task_type: Optional[RecapTaskType] = Field(None, description="Filter by task type")
    status: Optional[RecapTaskStatus] = Field(None, description="Filter by status")
    priority: Optional[Priority] = Field(None, description="Filter by priority")
    tracked_docket_id: Optional[int] = Field(None, description="Filter by docket ID")
    user_id: Optional[int] = Field(None, description="Filter by user")
    queue_name: Optional[str] = Field(None, description="Filter by queue")
    scheduled_from: Optional[datetime] = Field(None, description="Scheduled date range start")
    scheduled_to: Optional[datetime] = Field(None, description="Scheduled date range end")
    archived: Optional[bool] = Field(None, description="Filter by archived status")


# =============================================================================
# STATISTICS AND SUMMARY SCHEMAS
# =============================================================================

class DocketStats(BaseModel):
    """Schema for docket statistics"""
    total_dockets: int = Field(..., description="Total number of dockets")
    active_dockets: int = Field(..., description="Active dockets")
    paused_dockets: int = Field(..., description="Paused dockets")
    total_documents: int = Field(..., description="Total documents")
    documents_downloaded: int = Field(..., description="Downloaded documents")
    total_pacer_costs: Decimal = Field(..., description="Total PACER costs")
    courts_count: int = Field(..., description="Number of unique courts")
    last_update: datetime = Field(..., description="Last statistics update")


class TaskStats(BaseModel):
    """Schema for task statistics"""
    total_tasks: int = Field(..., description="Total number of tasks")
    pending_tasks: int = Field(..., description="Pending tasks")
    processing_tasks: int = Field(..., description="Processing tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    failed_tasks: int = Field(..., description="Failed tasks")
    avg_duration_seconds: Optional[float] = Field(None, description="Average task duration")
    success_rate: float = Field(..., description="Task success rate (0-1)")
    last_update: datetime = Field(..., description="Last statistics update")


# =============================================================================
# EXPORT ALL SCHEMAS
# =============================================================================

__all__ = [
    # Base schemas
    'TimestampSchema',
    'BaseSchema',
    
    # TrackedDocket schemas
    'TrackedDocketBase',
    'TrackedDocketCreate',
    'TrackedDocketUpdate', 
    'TrackedDocketResponse',
    'TrackedDocketListResponse',
    
    # RecapTask schemas
    'RecapTaskBase',
    'RecapTaskCreate',
    'RecapTaskUpdate',
    'RecapTaskResponse',
    'RecapTaskListResponse',
    
    # DocketDocument schemas
    'DocketDocumentBase',
    'DocketDocumentCreate',
    'DocketDocumentResponse',
    
    # Search and filter schemas
    'DocketSearchFilters',
    'TaskSearchFilters',
    
    # Statistics schemas
    'DocketStats',
    'TaskStats',
]