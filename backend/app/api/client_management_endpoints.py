"""
Client Management API Endpoints

Comprehensive client relationship management for law firms.
Manages clients, cases, document sharing, and communications.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import secrets
import hashlib

from ..src.core.database import get_db
from ..models.client_management import (
    Client, Case, SharedDocument, ClientCommunication,
    ClientStatus, ClientType, CaseStatus, DocumentShareStatus, AccessLevel
)
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/clients", tags=["client-management"])


# =============================================================================
# REQUEST & RESPONSE MODELS
# =============================================================================

class ClientCreateRequest(BaseModel):
    """Request to create a new client"""
    client_type: str = Field(..., description="Type of client: individual, business, government, nonprofit")

    # Individual
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    # Business
    company_name: Optional[str] = None
    business_type: Optional[str] = None

    # Contact
    email: EmailStr
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "USA"

    # Metadata
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    referral_source: Optional[str] = None


class ClientUpdateRequest(BaseModel):
    """Request to update client information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ClientResponse(BaseModel):
    """Client response model"""
    id: int
    client_number: str
    client_type: str
    status: str
    display_name: str
    email: Optional[str]
    phone: Optional[str]
    portal_access_enabled: bool
    created_at: str

    class Config:
        from_attributes = True


class CaseCreateRequest(BaseModel):
    """Request to create a new case"""
    case_name: str = Field(..., min_length=3, max_length=500)
    case_type: Optional[str] = None
    practice_area: Optional[str] = None
    description: Optional[str] = None
    billing_type: str = "hourly"
    priority: str = "medium"


class CaseResponse(BaseModel):
    """Case response model"""
    id: int
    case_number: str
    case_name: str
    case_type: Optional[str]
    practice_area: Optional[str]
    status: str
    client_id: int
    opened_date: str

    class Config:
        from_attributes = True


class DocumentShareRequest(BaseModel):
    """Request to share a document with client"""
    filename: str
    title: Optional[str] = None
    description: Optional[str] = None
    case_id: Optional[int] = None
    access_level: str = "download"
    expires_days: Optional[int] = None
    password_protect: bool = False
    password: Optional[str] = None
    category: Optional[str] = None


class DocumentShareResponse(BaseModel):
    """Shared document response"""
    id: int
    filename: str
    title: Optional[str]
    status: str
    share_token: str
    share_url: str
    expires_at: Optional[str]
    view_count: int
    download_count: int

    class Config:
        from_attributes = True


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_client_number() -> str:
    """Generate unique client number"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(3).upper()
    return f"CL-{timestamp}-{random_suffix}"


def generate_case_number(client_number: str) -> str:
    """Generate case number based on client"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(2).upper()
    return f"{client_number}-CASE-{timestamp}-{random_suffix}"


def generate_share_token() -> str:
    """Generate secure share token for document access"""
    return secrets.token_urlsafe(32)


def require_user(request) -> Dict[str, Any]:
    """Get current user from request"""
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.user


# =============================================================================
# CLIENT CRUD ENDPOINTS
# =============================================================================

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    request_data: ClientCreateRequest,
    request: Any,
    db: Session = Depends(get_db)
):
    """
    Create a new client.

    **Required Fields**:
    - `client_type`: individual, business, government, or nonprofit
    - `email`: Primary email address

    **Individual Clients**:
    - `first_name` and `last_name`

    **Business Clients**:
    - `company_name`

    **Returns**:
    - Created client with unique client number
    """
    user = require_user(request)

    try:
        # Validate client type
        try:
            client_type_enum = ClientType(request_data.client_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid client type: {request_data.client_type}"
            )

        # Validate required fields based on type
        if client_type_enum == ClientType.INDIVIDUAL:
            if not request_data.first_name or not request_data.last_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="first_name and last_name required for individual clients"
                )
        elif client_type_enum == ClientType.BUSINESS:
            if not request_data.company_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="company_name required for business clients"
                )

        # Generate unique client number
        client_number = generate_client_number()

        # Create client
        client = Client(
            client_number=client_number,
            client_type=client_type_enum,
            first_name=request_data.first_name,
            last_name=request_data.last_name,
            company_name=request_data.company_name,
            business_type=request_data.business_type,
            email=request_data.email,
            phone_primary=request_data.phone_primary,
            phone_secondary=request_data.phone_secondary,
            address_line1=request_data.address_line1,
            address_line2=request_data.address_line2,
            city=request_data.city,
            state=request_data.state,
            postal_code=request_data.postal_code,
            country=request_data.country,
            notes=request_data.notes,
            tags=request_data.tags or [],
            referral_source=request_data.referral_source,
            status=ClientStatus.ACTIVE
        )

        # Set full name for individuals
        if client_type_enum == ClientType.INDIVIDUAL:
            client.full_name = f"{request_data.first_name} {request_data.last_name}"

        db.add(client)
        db.commit()
        db.refresh(client)

        logger.info(f"Created client {client.client_number} by user {user['id']}")

        return ClientResponse(
            id=client.id,
            client_number=client.client_number,
            client_type=client.client_type.value,
            status=client.status.value,
            display_name=client.display_name,
            email=client.email,
            phone=client.phone_primary,
            portal_access_enabled=client.portal_access_enabled,
            created_at=client.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    request: Any,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all clients.

    **Query Parameters**:
    - `status_filter`: Filter by status (active, inactive, suspended, archived)
    - `search`: Search by name, email, or client number
    - `limit`: Maximum results (default: 100, max: 1000)
    - `offset`: Pagination offset
    """
    user = require_user(request)

    try:
        query = db.query(Client).filter(Client.deleted_at.is_(None))

        # Filter by status
        if status_filter:
            try:
                status_enum = ClientStatus(status_filter)
                query = query.filter(Client.status == status_enum)
            except ValueError:
                pass

        # Search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Client.first_name.ilike(search_term),
                    Client.last_name.ilike(search_term),
                    Client.full_name.ilike(search_term),
                    Client.company_name.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.client_number.ilike(search_term)
                )
            )

        # Order by most recent
        query = query.order_by(Client.created_at.desc())

        # Paginate
        clients = query.offset(offset).limit(limit).all()

        return [
            ClientResponse(
                id=client.id,
                client_number=client.client_number,
                client_type=client.client_type.value,
                status=client.status.value,
                display_name=client.display_name,
                email=client.email,
                phone=client.phone_primary,
                portal_access_enabled=client.portal_access_enabled,
                created_at=client.created_at.isoformat()
            )
            for client in clients
        ]

    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list clients: {str(e)}"
        )


@router.get("/{client_id}")
async def get_client(
    client_id: int,
    request: Any,
    db: Session = Depends(get_db)
):
    """Get detailed client information"""
    user = require_user(request)

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.deleted_at.is_(None)
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found"
        )

    return client.to_dict(include_sensitive=True)


@router.patch("/{client_id}")
async def update_client(
    client_id: int,
    update_data: ClientUpdateRequest,
    request: Any,
    db: Session = Depends(get_db)
):
    """Update client information"""
    user = require_user(request)

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.deleted_at.is_(None)
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found"
        )

    # Update fields
    update_fields = update_data.dict(exclude_unset=True)

    for field, value in update_fields.items():
        if field == "status" and value:
            try:
                client.status = ClientStatus(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {value}"
                )
        elif hasattr(client, field):
            setattr(client, field, value)

    db.commit()
    db.refresh(client)

    logger.info(f"Updated client {client.client_number} by user {user['id']}")

    return client.to_dict(include_sensitive=True)


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    request: Any,
    db: Session = Depends(get_db)
):
    """
    Delete (archive) a client.

    This is a soft delete - the client record is archived, not permanently removed.
    """
    user = require_user(request)

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.deleted_at.is_(None)
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found"
        )

    # Soft delete
    client.deleted_at = datetime.utcnow()
    client.status = ClientStatus.ARCHIVED

    db.commit()

    logger.info(f"Archived client {client.client_number} by user {user['id']}")

    return {"success": True, "message": f"Client {client.client_number} archived"}


# =============================================================================
# CASE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/{client_id}/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    client_id: int,
    case_data: CaseCreateRequest,
    request: Any,
    db: Session = Depends(get_db)
):
    """
    Create a new case for a client.

    **Required**:
    - `case_name`: Name/title of the case

    **Optional**:
    - `case_type`: litigation, transactional, estate, etc.
    - `practice_area`: family, criminal, corporate, etc.
    - `billing_type`: hourly, flat_fee, contingency
    """
    user = require_user(request)

    # Verify client exists
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.deleted_at.is_(None)
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found"
        )

    try:
        # Generate case number
        case_number = generate_case_number(client.client_number)

        # Create case
        case = Case(
            case_number=case_number,
            case_name=case_data.case_name,
            case_type=case_data.case_type,
            practice_area=case_data.practice_area,
            description=case_data.description,
            billing_type=case_data.billing_type,
            priority=case_data.priority,
            client_id=client_id,
            status=CaseStatus.OPEN,
            opened_date=datetime.utcnow()
        )

        db.add(case)
        db.commit()
        db.refresh(case)

        logger.info(f"Created case {case.case_number} for client {client.client_number}")

        return CaseResponse(
            id=case.id,
            case_number=case.case_number,
            case_name=case.case_name,
            case_type=case.case_type,
            practice_area=case.practice_area,
            status=case.status.value,
            client_id=case.client_id,
            opened_date=case.opened_date.isoformat()
        )

    except Exception as e:
        logger.error(f"Error creating case: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case: {str(e)}"
        )


@router.get("/{client_id}/cases", response_model=List[CaseResponse])
async def list_client_cases(
    client_id: int,
    request: Any,
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all cases for a client.

    **Query Parameters**:
    - `status_filter`: Filter by status (open, pending, closed, archived)
    """
    user = require_user(request)

    # Verify client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found"
        )

    query = db.query(Case).filter(
        Case.client_id == client_id,
        Case.deleted_at.is_(None)
    )

    if status_filter:
        try:
            status_enum = CaseStatus(status_filter)
            query = query.filter(Case.status == status_enum)
        except ValueError:
            pass

    cases = query.order_by(Case.opened_date.desc()).all()

    return [
        CaseResponse(
            id=case.id,
            case_number=case.case_number,
            case_name=case.case_name,
            case_type=case.case_type,
            practice_area=case.practice_area,
            status=case.status.value,
            client_id=case.client_id,
            opened_date=case.opened_date.isoformat()
        )
        for case in cases
    ]


# =============================================================================
# DOCUMENT SHARING ENDPOINTS
# =============================================================================

@router.post("/{client_id}/documents/share", response_model=DocumentShareResponse)
async def share_document(
    client_id: int,
    share_data: DocumentShareRequest,
    request: Any,
    db: Session = Depends(get_db)
):
    """
    Share a document with a client.

    **Features**:
    - Secure token-based access
    - Optional password protection
    - Expiration dates
    - Access level control
    - View/download tracking

    **Access Levels**:
    - `read_only`: View only
    - `comment`: View and comment
    - `download`: View and download
    - `full`: Full access
    """
    user = require_user(request)

    # Verify client exists
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.deleted_at.is_(None)
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {client_id} not found"
        )

    try:
        # Generate share token
        share_token = generate_share_token()

        # Calculate expiration
        expires_at = None
        if share_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=share_data.expires_days)

        # Hash password if provided
        password_hash = None
        if share_data.password_protect and share_data.password:
            password_hash = hashlib.sha256(share_data.password.encode()).hexdigest()

        # Create shared document
        shared_doc = SharedDocument(
            filename=share_data.filename,
            title=share_data.title or share_data.filename,
            description=share_data.description,
            client_id=client_id,
            case_id=share_data.case_id,
            shared_by_user_id=user['id'],
            share_token=share_token,
            password_protected=share_data.password_protect,
            password_hash=password_hash,
            expires_at=expires_at,
            access_level=AccessLevel(share_data.access_level),
            category=share_data.category,
            status=DocumentShareStatus.PENDING
        )

        db.add(shared_doc)
        db.commit()
        db.refresh(shared_doc)

        # Generate share URL (would be configured in production)
        share_url = f"https://portal.legal-ai.example.com/shared/{share_token}"

        logger.info(f"Shared document {share_data.filename} with client {client.client_number}")

        return DocumentShareResponse(
            id=shared_doc.id,
            filename=shared_doc.filename,
            title=shared_doc.title,
            status=shared_doc.status.value,
            share_token=shared_doc.share_token,
            share_url=share_url,
            expires_at=shared_doc.expires_at.isoformat() if shared_doc.expires_at else None,
            view_count=shared_doc.view_count,
            download_count=shared_doc.download_count
        )

    except Exception as e:
        logger.error(f"Error sharing document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share document: {str(e)}"
        )


@router.get("/{client_id}/documents", response_model=List[DocumentShareResponse])
async def list_shared_documents(
    client_id: int,
    request: Any,
    case_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List documents shared with a client.

    **Query Parameters**:
    - `case_id`: Filter by specific case
    """
    user = require_user(request)

    query = db.query(SharedDocument).filter(
        SharedDocument.client_id == client_id,
        SharedDocument.deleted_at.is_(None)
    )

    if case_id:
        query = query.filter(SharedDocument.case_id == case_id)

    shared_docs = query.order_by(SharedDocument.shared_at.desc()).all()

    return [
        DocumentShareResponse(
            id=doc.id,
            filename=doc.filename,
            title=doc.title,
            status=doc.status.value,
            share_token=doc.share_token,
            share_url=f"https://portal.legal-ai.example.com/shared/{doc.share_token}",
            expires_at=doc.expires_at.isoformat() if doc.expires_at else None,
            view_count=doc.view_count,
            download_count=doc.download_count
        )
        for doc in shared_docs
    ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['router']
