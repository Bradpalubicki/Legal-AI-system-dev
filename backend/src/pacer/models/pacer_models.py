# -*- coding: utf-8 -*-
"""
PACER Data Models

Pydantic models for PACER data structures including:
- Cases
- Parties
- Documents
- Dockets
- Courts
- Search results
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class CourtType(str, Enum):
    """PACER court types"""
    DISTRICT = "district"
    BANKRUPTCY = "bankruptcy"
    APPELLATE = "appellate"


class CaseStatus(str, Enum):
    """Case status types"""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    TERMINATED = "terminated"


class PartyRole(str, Enum):
    """Party role in a case"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    DEBTOR = "debtor"
    CREDITOR = "creditor"
    TRUSTEE = "trustee"
    APPELLANT = "appellant"
    APPELLEE = "appellee"
    OTHER = "other"


class DocumentType(str, Enum):
    """Types of court documents"""
    COMPLAINT = "complaint"
    ANSWER = "answer"
    MOTION = "motion"
    ORDER = "order"
    JUDGMENT = "judgment"
    OPINION = "opinion"
    BRIEF = "brief"
    PETITION = "petition"
    NOTICE = "notice"
    TRANSCRIPT = "transcript"
    EXHIBIT = "exhibit"
    DOCKET = "docket"
    OTHER = "other"


# ============================================================================
# Court Models
# ============================================================================

class Court(BaseModel):
    """PACER court information"""
    court_id: str = Field(..., description="Court identifier (e.g., 'nysd', 'cacb')")
    court_name: str = Field(..., description="Full court name")
    court_type: CourtType = Field(..., description="Type of court")
    state: Optional[str] = Field(None, description="State abbreviation")
    district: Optional[str] = Field(None, description="District name")

    class Config:
        json_schema_extra = {
            "example": {
                "court_id": "nysd",
                "court_name": "United States District Court for the Southern District of New York",
                "court_type": "district",
                "state": "NY",
                "district": "Southern"
            }
        }


# ============================================================================
# Party Models
# ============================================================================

class Party(BaseModel):
    """Party in a legal case"""
    name: str = Field(..., description="Party name")
    role: PartyRole = Field(..., description="Role in the case")
    party_type: Optional[str] = Field(None, description="Type (individual, organization, etc.)")
    represented_by: Optional[List[str]] = Field(default_factory=list, description="Attorney names")
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "role": "plaintiff",
                "party_type": "individual",
                "represented_by": ["Jane Attorney, Esq."]
            }
        }


# ============================================================================
# Case Models
# ============================================================================

class Case(BaseModel):
    """PACER case information"""
    case_id: str = Field(..., description="Internal case identifier")
    case_number: str = Field(..., description="Court case number")
    case_title: str = Field(..., description="Case title")
    court_id: str = Field(..., description="Court identifier")
    court_name: Optional[str] = None

    # Dates
    filed_date: Optional[date] = Field(None, description="Filing date")
    closed_date: Optional[date] = Field(None, description="Closing date")
    last_filing_date: Optional[date] = None

    # Case details
    case_type: Optional[str] = Field(None, description="Type of case")
    nature_of_suit: Optional[str] = Field(None, description="Nature of suit code/description")
    jurisdiction: Optional[str] = None
    cause_of_action: Optional[str] = None
    status: CaseStatus = Field(default=CaseStatus.OPEN)

    # Parties and judge
    judge_name: Optional[str] = None
    parties: List[Party] = Field(default_factory=list)

    # Metadata
    docket_entry_count: Optional[int] = Field(None, description="Number of docket entries")
    demand: Optional[str] = Field(None, description="Monetary demand")
    jury_demand: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "pacer-123456",
                "case_number": "1:24-cv-01234",
                "case_title": "Doe v. Roe",
                "court_id": "nysd",
                "filed_date": "2024-01-15",
                "case_type": "Civil",
                "nature_of_suit": "Contract",
                "status": "open",
                "judge_name": "Hon. Jane Judge"
            }
        }


# ============================================================================
# Document Models
# ============================================================================

class Document(BaseModel):
    """PACER document information"""
    document_id: str = Field(..., description="Document identifier")
    case_id: str = Field(..., description="Associated case ID")
    document_number: str = Field(..., description="Document number in case")

    # Document details
    title: str = Field(..., description="Document title/description")
    document_type: DocumentType = Field(default=DocumentType.OTHER)
    filing_date: datetime = Field(..., description="Document filing date/time")

    # File information
    file_size: Optional[int] = Field(None, description="File size in bytes")
    page_count: Optional[int] = Field(None, description="Number of pages")
    file_format: str = Field(default="pdf", description="File format")

    # PACER information
    pacer_url: Optional[str] = Field(None, description="PACER download URL")
    pacer_cost: Optional[float] = Field(None, description="Cost to download ($)")
    pacer_doc_id: Optional[str] = Field(None, description="PACER document ID")

    # Filing party
    filed_by: Optional[str] = Field(None, description="Party who filed document")
    filed_by_attorney: Optional[str] = None

    # Content
    is_sealed: bool = Field(default=False, description="Whether document is sealed")
    is_restricted: bool = Field(default=False, description="Whether access is restricted")
    summary: Optional[str] = Field(None, description="Document summary/abstract")

    # Local storage
    local_path: Optional[str] = Field(None, description="Path to downloaded file")
    downloaded_at: Optional[datetime] = None
    checksum: Optional[str] = Field(None, description="SHA-256 checksum")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-789",
                "case_id": "pacer-123456",
                "document_number": "1",
                "title": "Complaint",
                "document_type": "complaint",
                "filing_date": "2024-01-15T10:30:00Z",
                "page_count": 15,
                "pacer_cost": 1.50
            }
        }


# ============================================================================
# Docket Entry Models
# ============================================================================

class DocketEntry(BaseModel):
    """Individual docket entry"""
    entry_number: int = Field(..., description="Docket entry number")
    entry_date: date = Field(..., description="Date of entry")
    filed_date: Optional[datetime] = Field(None, description="Filing date/time")

    description: str = Field(..., description="Entry description")
    entry_type: Optional[str] = None

    # Associated documents
    document_number: Optional[str] = None
    attachment_count: int = Field(default=0)

    # Filing information
    filed_by: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "entry_number": 1,
                "entry_date": "2024-01-15",
                "description": "COMPLAINT against All Defendants filed by Plaintiff",
                "document_number": "1"
            }
        }


# ============================================================================
# Search Result Models
# ============================================================================

class CaseSearchCriteria(BaseModel):
    """Criteria for case search"""
    case_number: Optional[str] = None
    case_title: Optional[str] = None
    court: Optional[str] = None
    filed_from: Optional[date] = None
    filed_to: Optional[date] = None
    closed_from: Optional[date] = None
    closed_to: Optional[date] = None
    nature_of_suit: Optional[str] = None
    case_status: Optional[str] = None
    judge_name: Optional[str] = None


class PartySearchCriteria(BaseModel):
    """Criteria for party search"""
    party_name: str = Field(..., min_length=2)
    court: Optional[str] = None
    party_role: Optional[PartyRole] = None
    case_filed_from: Optional[date] = None
    case_filed_to: Optional[date] = None


class SearchResult(BaseModel):
    """Generic search result container"""
    results: List[Any] = Field(default_factory=list)
    total_count: int = Field(..., description="Total number of results")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    has_more: bool = Field(default=False)

    search_timestamp: datetime = Field(default_factory=datetime.utcnow)
    query_params: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Authentication Models
# ============================================================================

class PACERCredentials(BaseModel):
    """PACER login credentials"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    client_code: Optional[str] = None
    environment: str = Field(default="production", pattern="^(production|qa)$")


class AuthenticationResult(BaseModel):
    """Result of PACER authentication"""
    success: bool
    token: Optional[str] = Field(None, alias="nextGenCSO")
    username: Optional[str] = None
    environment: Optional[str] = None
    expires_at: Optional[datetime] = None
    cached: bool = Field(default=False)
    error: Optional[str] = None

    class Config:
        populate_by_name = True


# ============================================================================
# Cost Tracking Models
# ============================================================================

class CostRecord(BaseModel):
    """Record of PACER cost"""
    operation: str = Field(..., description="Operation type")
    cost: float = Field(..., ge=0, description="Cost in dollars")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    case_id: Optional[str] = None
    document_id: Optional[str] = None
    court: Optional[str] = None
    pages: int = Field(default=1, ge=0)
    description: str = ""


class UsageReport(BaseModel):
    """PACER usage report"""
    period_days: int
    user_id: Optional[str] = None
    total_cost: float
    total_pages: int
    total_operations: int
    daily_spending: float
    monthly_spending: float
    daily_limit: float
    monthly_limit: float
    by_operation: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    by_court: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


# Example usage
if __name__ == "__main__":
    # Create example case
    case = Case(
        case_id="test-123",
        case_number="1:24-cv-00001",
        case_title="Doe v. Roe",
        court_id="nysd",
        filed_date=date(2024, 1, 15),
        case_type="Civil",
        nature_of_suit="Contract Dispute",
        status=CaseStatus.OPEN,
        judge_name="Hon. Jane Doe",
        parties=[
            Party(name="John Doe", role=PartyRole.PLAINTIFF, party_type="individual"),
            Party(name="Richard Roe", role=PartyRole.DEFENDANT, party_type="individual")
        ]
    )

    print("📄 Example Case Model:")
    print(case.model_dump_json(indent=2))

    # Create example document
    doc = Document(
        document_id="doc-1",
        case_id="test-123",
        document_number="1",
        title="Complaint",
        document_type=DocumentType.COMPLAINT,
        filing_date=datetime(2024, 1, 15, 10, 30),
        page_count=12,
        pacer_cost=1.20
    )

    print("\n📑 Example Document Model:")
    print(doc.model_dump_json(indent=2))
