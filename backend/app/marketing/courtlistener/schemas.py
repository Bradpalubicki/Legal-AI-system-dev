"""
CourtListener Pydantic Schemas

Request/response models for CourtListener data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocketSearchParams(BaseModel):
    """Parameters for docket search"""
    q: Optional[str] = Field(None, description="Full-text search query")
    court: Optional[str] = Field(None, description="Court ID filter")
    case_name: Optional[str] = Field(None, description="Case name contains")
    date_filed_after: Optional[datetime] = Field(None, description="Filed on or after")
    date_filed_before: Optional[datetime] = Field(None, description="Filed on or before")
    nature_of_suit: Optional[str] = Field(None, description="Nature of suit code")
    order_by: str = Field("-date_filed", description="Sort order")


class DocketSummary(BaseModel):
    """Summary of a docket record"""
    id: int
    case_name: Optional[str]
    docket_number: Optional[str]
    court: Optional[str]
    court_id: Optional[str]
    date_filed: Optional[datetime]
    date_terminated: Optional[datetime]
    nature_of_suit: Optional[str]
    cause: Optional[str]
    assigned_to_str: Optional[str]
    referred_to_str: Optional[str]

    class Config:
        from_attributes = True


class AttorneySummary(BaseModel):
    """Summary of an attorney record"""
    id: int
    name: Optional[str]
    contact_raw_text: Optional[str]
    roles: List[str] = []
    organizations: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class PartySummary(BaseModel):
    """Summary of a party record"""
    id: int
    name: Optional[str]
    party_types: List[Dict[str, Any]] = []
    extra_info: Optional[str]

    class Config:
        from_attributes = True


class MonitorStatusResponse(BaseModel):
    """Response for monitor status endpoint"""
    last_poll_started: Optional[str]
    last_poll_completed: Optional[str]
    last_status: Optional[str]
    last_error: Optional[str]
    dockets_found: int = 0
    dockets_processed: int = 0
    contacts_created: int = 0
    rate_limit_remaining: Optional[int]
    config: Dict[str, Any]


class MonitorTriggerResponse(BaseModel):
    """Response when triggering monitor"""
    status: str
    message: str


class ExtractedContactResponse(BaseModel):
    """Response for an extracted contact"""
    email: Optional[str]
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    firm_name: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    state: Optional[str]
    contact_type: str
    role: str
    courtlistener_attorney_id: Optional[int]
