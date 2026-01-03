"""
Attorney Management API Endpoints

Provides endpoints for:
- Managing attorney profiles
- Tracking attorney-case relationships
- Scheduling and preparing for meetings
- Logging communications
- Generating meeting prep materials
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from ..src.core.database import get_db
from ..api.deps.auth import get_current_user, CurrentUser
from ..models.attorney_management import (
    Attorney,
    AttorneyCaseAssignment,
    AttorneyMeeting,
    AttorneyCommunication,
    AttorneyRole,
    AttorneyStatus,
    MeetingType,
    MeetingStatus,
    CommunicationType,
    generate_meeting_prep
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/attorneys", tags=["Attorney Management"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AttorneyCreate(BaseModel):
    """Request model for creating an attorney"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bar_number: Optional[str] = None
    bar_state: Optional[str] = None
    firm_name: Optional[str] = None
    title: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    practice_areas: Optional[List[str]] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class AttorneyUpdate(BaseModel):
    """Request model for updating an attorney"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    bar_number: Optional[str] = None
    bar_state: Optional[str] = None
    bar_status: Optional[str] = None
    firm_name: Optional[str] = None
    firm_website: Optional[str] = None
    title: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    practice_areas: Optional[List[str]] = None
    specializations: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    preferred_contact_time: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[AttorneyStatus] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CaseAssignmentCreate(BaseModel):
    """Request model for assigning attorney to case"""
    attorney_id: str
    case_id: Optional[str] = None
    case_number: Optional[str] = None
    role: AttorneyRole
    is_primary: bool = False
    is_opposing: bool = False
    hourly_rate: Optional[str] = None
    billing_arrangement: Optional[str] = None
    notes: Optional[str] = None
    responsibilities: Optional[str] = None


class MeetingCreate(BaseModel):
    """Request model for creating a meeting"""
    attorney_id: str
    case_id: Optional[str] = None
    meeting_type: MeetingType
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    location: Optional[str] = None
    is_virtual: bool = True
    scheduled_date: datetime
    duration_minutes: int = 60
    reminder_date: Optional[datetime] = None


class MeetingUpdate(BaseModel):
    """Request model for updating a meeting"""
    meeting_type: Optional[MeetingType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    is_virtual: Optional[bool] = None
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[MeetingStatus] = None
    meeting_notes: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    outcome_summary: Optional[str] = None


class MeetingPrepRequest(BaseModel):
    """Request model for generating meeting prep"""
    meeting_id: str
    include_case_summary: bool = True
    include_questions: bool = True
    include_documents: bool = True
    custom_agenda: Optional[str] = None


class CommunicationCreate(BaseModel):
    """Request model for logging a communication"""
    attorney_id: str
    case_id: Optional[str] = None
    communication_type: CommunicationType
    direction: str = "outbound"  # "inbound" or "outbound"
    subject: Optional[str] = None
    content: Optional[str] = None
    communication_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    requires_response: bool = False
    response_deadline: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    importance: str = "normal"


# ============================================================================
# ATTORNEY CRUD ENDPOINTS
# ============================================================================

@router.post("")
async def create_attorney(
    request: AttorneyCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new attorney profile.
    """
    try:
        attorney_id = str(uuid.uuid4())

        attorney = Attorney(
            id=attorney_id,
            first_name=request.first_name,
            last_name=request.last_name,
            full_name=f"{request.first_name} {request.last_name}",
            email=request.email,
            phone=request.phone,
            bar_number=request.bar_number,
            bar_state=request.bar_state,
            firm_name=request.firm_name,
            title=request.title,
            address_line1=request.address_line1,
            city=request.city,
            state=request.state,
            zip_code=request.zip_code,
            practice_areas=request.practice_areas,
            notes=request.notes,
            tags=request.tags,
            created_by_user_id=current_user.id,
            status=AttorneyStatus.ACTIVE
        )

        db.add(attorney)
        db.commit()
        db.refresh(attorney)

        return {
            "success": True,
            "attorney_id": attorney_id,
            "attorney": {
                "id": attorney.id,
                "full_name": attorney.full_name,
                "email": attorney.email,
                "firm_name": attorney.firm_name,
                "bar_number": attorney.bar_number
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating attorney: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attorney: {str(e)}"
        )


@router.get("")
async def list_attorneys(
    search: Optional[str] = Query(None, description="Search by name, firm, or bar number"),
    status_filter: Optional[AttorneyStatus] = Query(None, description="Filter by status"),
    role_filter: Optional[AttorneyRole] = Query(None, description="Filter by role in cases"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all attorneys with optional filtering.
    """
    try:
        query = db.query(Attorney).filter(Attorney.is_deleted == False)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Attorney.full_name.ilike(search_pattern),
                    Attorney.firm_name.ilike(search_pattern),
                    Attorney.bar_number.ilike(search_pattern),
                    Attorney.email.ilike(search_pattern)
                )
            )

        # Apply status filter
        if status_filter:
            query = query.filter(Attorney.status == status_filter)

        # Get total count
        total = query.count()

        # Apply pagination
        attorneys = query.order_by(Attorney.full_name).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "attorneys": [
                {
                    "id": att.id,
                    "full_name": att.full_name,
                    "email": att.email,
                    "phone": att.phone,
                    "firm_name": att.firm_name,
                    "bar_number": att.bar_number,
                    "bar_state": att.bar_state,
                    "status": att.status.value if att.status else "active",
                    "practice_areas": att.practice_areas or [],
                    "case_count": len(att.case_assignments) if att.case_assignments else 0
                }
                for att in attorneys
            ]
        }

    except Exception as e:
        logger.error(f"Error listing attorneys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list attorneys: {str(e)}"
        )


@router.get("/{attorney_id}")
async def get_attorney(
    attorney_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get detailed attorney profile.
    """
    try:
        attorney = db.query(Attorney).filter(
            Attorney.id == attorney_id,
            Attorney.is_deleted == False
        ).first()

        if not attorney:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attorney not found"
            )

        # Get case assignments
        assignments = db.query(AttorneyCaseAssignment).filter(
            AttorneyCaseAssignment.attorney_id == attorney_id
        ).all()

        # Get upcoming meetings
        upcoming_meetings = db.query(AttorneyMeeting).filter(
            AttorneyMeeting.attorney_id == attorney_id,
            AttorneyMeeting.scheduled_date >= datetime.utcnow(),
            AttorneyMeeting.status.in_([MeetingStatus.SCHEDULED, MeetingStatus.CONFIRMED])
        ).order_by(AttorneyMeeting.scheduled_date).limit(5).all()

        # Get recent communications
        recent_comms = db.query(AttorneyCommunication).filter(
            AttorneyCommunication.attorney_id == attorney_id
        ).order_by(AttorneyCommunication.communication_date.desc()).limit(10).all()

        return {
            "success": True,
            "attorney": {
                "id": attorney.id,
                "first_name": attorney.first_name,
                "last_name": attorney.last_name,
                "full_name": attorney.full_name,
                "email": attorney.email,
                "phone": attorney.phone,
                "phone_secondary": attorney.phone_secondary,
                "bar_number": attorney.bar_number,
                "bar_state": attorney.bar_state,
                "bar_status": attorney.bar_status,
                "firm_name": attorney.firm_name,
                "firm_website": attorney.firm_website,
                "title": attorney.title,
                "address": {
                    "line1": attorney.address_line1,
                    "line2": attorney.address_line2,
                    "city": attorney.city,
                    "state": attorney.state,
                    "zip_code": attorney.zip_code,
                    "country": attorney.country
                },
                "practice_areas": attorney.practice_areas or [],
                "specializations": attorney.specializations,
                "preferred_contact_method": attorney.preferred_contact_method,
                "preferred_contact_time": attorney.preferred_contact_time,
                "timezone": attorney.timezone,
                "status": attorney.status.value if attorney.status else "active",
                "notes": attorney.notes,
                "tags": attorney.tags or [],
                "created_at": attorney.created_at.isoformat() if attorney.created_at else None
            },
            "case_assignments": [
                {
                    "id": a.id,
                    "case_id": a.case_id,
                    "case_number": a.case_number,
                    "role": a.role.value if a.role else "other",
                    "is_primary": a.is_primary,
                    "is_opposing": a.is_opposing,
                    "assignment_date": a.assignment_date.isoformat() if a.assignment_date else None
                }
                for a in assignments
            ],
            "upcoming_meetings": [
                {
                    "id": m.id,
                    "title": m.title,
                    "meeting_type": m.meeting_type.value if m.meeting_type else "other",
                    "scheduled_date": m.scheduled_date.isoformat() if m.scheduled_date else None,
                    "status": m.status.value if m.status else "scheduled"
                }
                for m in upcoming_meetings
            ],
            "recent_communications": [
                {
                    "id": c.id,
                    "type": c.communication_type.value if c.communication_type else "other",
                    "direction": c.direction,
                    "subject": c.subject,
                    "date": c.communication_date.isoformat() if c.communication_date else None
                }
                for c in recent_comms
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attorney: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attorney: {str(e)}"
        )


@router.put("/{attorney_id}")
async def update_attorney(
    attorney_id: str,
    request: AttorneyUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update attorney profile.
    """
    try:
        attorney = db.query(Attorney).filter(
            Attorney.id == attorney_id,
            Attorney.is_deleted == False
        ).first()

        if not attorney:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attorney not found"
            )

        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(attorney, field):
                setattr(attorney, field, value)

        # Update full name if first or last name changed
        if request.first_name or request.last_name:
            first = request.first_name or attorney.first_name
            last = request.last_name or attorney.last_name
            attorney.full_name = f"{first} {last}"

        attorney.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "message": "Attorney updated successfully",
            "attorney_id": attorney_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating attorney: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update attorney: {str(e)}"
        )


@router.delete("/{attorney_id}")
async def delete_attorney(
    attorney_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Soft delete an attorney.
    """
    try:
        attorney = db.query(Attorney).filter(
            Attorney.id == attorney_id,
            Attorney.is_deleted == False
        ).first()

        if not attorney:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attorney not found"
            )

        attorney.is_deleted = True
        attorney.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "message": "Attorney deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting attorney: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attorney: {str(e)}"
        )


# ============================================================================
# MEETING ENDPOINTS
# ============================================================================

@router.post("/meetings")
async def create_meeting(
    request: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Schedule a new meeting with an attorney.
    """
    try:
        # Verify attorney exists
        attorney = db.query(Attorney).filter(
            Attorney.id == request.attorney_id,
            Attorney.is_deleted == False
        ).first()

        if not attorney:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attorney not found"
            )

        meeting_id = str(uuid.uuid4())

        meeting = AttorneyMeeting(
            id=meeting_id,
            attorney_id=request.attorney_id,
            case_id=request.case_id,
            user_id=current_user.id,
            meeting_type=request.meeting_type,
            title=request.title,
            description=request.description,
            location=request.location,
            is_virtual=request.is_virtual,
            scheduled_date=request.scheduled_date,
            scheduled_end=request.scheduled_date + timedelta(minutes=request.duration_minutes),
            duration_minutes=request.duration_minutes,
            status=MeetingStatus.SCHEDULED,
            reminder_date=request.reminder_date,
            created_by_user_id=current_user.id
        )

        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        return {
            "success": True,
            "meeting_id": meeting_id,
            "meeting": {
                "id": meeting.id,
                "title": meeting.title,
                "attorney_name": attorney.full_name,
                "scheduled_date": meeting.scheduled_date.isoformat() if meeting.scheduled_date else None,
                "meeting_type": meeting.meeting_type.value if meeting.meeting_type else "other",
                "status": meeting.status.value if meeting.status else "scheduled"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating meeting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create meeting: {str(e)}"
        )


@router.get("/meetings")
async def list_meetings(
    attorney_id: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    status_filter: Optional[MeetingStatus] = Query(None),
    upcoming_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List meetings with optional filtering.
    """
    try:
        query = db.query(AttorneyMeeting)

        if attorney_id:
            query = query.filter(AttorneyMeeting.attorney_id == attorney_id)

        if case_id:
            query = query.filter(AttorneyMeeting.case_id == case_id)

        if status_filter:
            query = query.filter(AttorneyMeeting.status == status_filter)

        if upcoming_only:
            query = query.filter(AttorneyMeeting.scheduled_date >= datetime.utcnow())

        total = query.count()

        meetings = query.order_by(AttorneyMeeting.scheduled_date).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "meetings": [
                {
                    "id": m.id,
                    "title": m.title,
                    "attorney_id": m.attorney_id,
                    "case_id": m.case_id,
                    "meeting_type": m.meeting_type.value if m.meeting_type else "other",
                    "scheduled_date": m.scheduled_date.isoformat() if m.scheduled_date else None,
                    "duration_minutes": m.duration_minutes,
                    "is_virtual": m.is_virtual,
                    "location": m.location,
                    "status": m.status.value if m.status else "scheduled",
                    "has_prep": bool(m.prep_document)
                }
                for m in meetings
            ]
        }

    except Exception as e:
        logger.error(f"Error listing meetings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list meetings: {str(e)}"
        )


@router.get("/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get meeting details including prep materials.
    """
    try:
        meeting = db.query(AttorneyMeeting).filter(
            AttorneyMeeting.id == meeting_id
        ).first()

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )

        # Get attorney info
        attorney = db.query(Attorney).filter(Attorney.id == meeting.attorney_id).first()

        return {
            "success": True,
            "meeting": {
                "id": meeting.id,
                "title": meeting.title,
                "description": meeting.description,
                "meeting_type": meeting.meeting_type.value if meeting.meeting_type else "other",
                "scheduled_date": meeting.scheduled_date.isoformat() if meeting.scheduled_date else None,
                "scheduled_end": meeting.scheduled_end.isoformat() if meeting.scheduled_end else None,
                "duration_minutes": meeting.duration_minutes,
                "is_virtual": meeting.is_virtual,
                "location": meeting.location,
                "status": meeting.status.value if meeting.status else "scheduled",
                "attorney": {
                    "id": attorney.id if attorney else None,
                    "full_name": attorney.full_name if attorney else "Unknown",
                    "email": attorney.email if attorney else None,
                    "phone": attorney.phone if attorney else None
                },
                "prep_materials": {
                    "document": meeting.prep_document,
                    "questions": meeting.prep_questions or [],
                    "documents_to_bring": meeting.prep_documents_to_bring or [],
                    "talking_points": meeting.prep_talking_points or [],
                    "case_summary": meeting.prep_case_summary
                },
                "post_meeting": {
                    "notes": meeting.meeting_notes,
                    "action_items": meeting.action_items or [],
                    "follow_up_date": meeting.follow_up_date.isoformat() if meeting.follow_up_date else None,
                    "outcome_summary": meeting.outcome_summary
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get meeting: {str(e)}"
        )


@router.post("/meetings/{meeting_id}/generate-prep")
async def generate_meeting_prep_endpoint(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate meeting preparation materials for a scheduled meeting.
    Uses AI to create questions, talking points, and document recommendations.
    """
    try:
        meeting = db.query(AttorneyMeeting).filter(
            AttorneyMeeting.id == meeting_id
        ).first()

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )

        # Get case information if linked
        case_info = {}
        if meeting.case_id:
            from ..models.case_management import LegalCase
            case = db.query(LegalCase).filter(LegalCase.id == meeting.case_id).first()
            if case:
                case_info = {
                    "case_number": case.case_number,
                    "case_name": case.case_name,
                    "status": case.status.value if case.status else "unknown",
                    "case_type": case.case_type.value if case.case_type else "unknown",
                    "deadlines": [],  # Would fetch from timeline events
                    "recent_documents": []  # Would fetch from documents
                }

        # Get attorney info
        attorney = db.query(Attorney).filter(Attorney.id == meeting.attorney_id).first()

        meeting_info = {
            "meeting_type": meeting.meeting_type.value if meeting.meeting_type else "general",
            "title": meeting.title,
            "attorney_name": attorney.full_name if attorney else "Unknown"
        }

        # Generate prep materials
        prep_materials = generate_meeting_prep(case_info, meeting_info)

        # Update meeting with prep materials
        meeting.prep_document = prep_materials.get("case_summary", "")
        meeting.prep_questions = prep_materials.get("questions", [])
        meeting.prep_talking_points = prep_materials.get("talking_points", [])
        meeting.prep_documents_to_bring = prep_materials.get("documents_needed", [])
        meeting.prep_case_summary = prep_materials.get("case_summary", "")
        meeting.updated_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "message": "Meeting prep materials generated",
            "prep_materials": prep_materials
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating meeting prep: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate meeting prep: {str(e)}"
        )


@router.put("/meetings/{meeting_id}")
async def update_meeting(
    meeting_id: str,
    request: MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update meeting details or add post-meeting notes.
    """
    try:
        meeting = db.query(AttorneyMeeting).filter(
            AttorneyMeeting.id == meeting_id
        ).first()

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )

        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(meeting, field):
                setattr(meeting, field, value)

        # Update end time if date or duration changed
        if request.scheduled_date or request.duration_minutes:
            meeting.scheduled_end = meeting.scheduled_date + timedelta(minutes=meeting.duration_minutes)

        meeting.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "message": "Meeting updated successfully",
            "meeting_id": meeting_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating meeting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update meeting: {str(e)}"
        )


# ============================================================================
# COMMUNICATION ENDPOINTS
# ============================================================================

@router.post("/communications")
async def log_communication(
    request: CommunicationCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Log a communication with an attorney.
    """
    try:
        # Verify attorney exists
        attorney = db.query(Attorney).filter(
            Attorney.id == request.attorney_id,
            Attorney.is_deleted == False
        ).first()

        if not attorney:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attorney not found"
            )

        comm_id = str(uuid.uuid4())

        communication = AttorneyCommunication(
            id=comm_id,
            attorney_id=request.attorney_id,
            case_id=request.case_id,
            user_id=current_user.id,
            communication_type=request.communication_type,
            direction=request.direction,
            subject=request.subject,
            content=request.content,
            communication_date=request.communication_date or datetime.utcnow(),
            duration_minutes=request.duration_minutes,
            requires_response=request.requires_response,
            response_deadline=request.response_deadline,
            attachments=request.attachments,
            importance=request.importance,
            created_by_user_id=current_user.id
        )

        db.add(communication)
        db.commit()

        return {
            "success": True,
            "communication_id": comm_id,
            "message": "Communication logged successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging communication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log communication: {str(e)}"
        )


@router.get("/communications")
async def list_communications(
    attorney_id: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    requires_response: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List communications with optional filtering.
    """
    try:
        query = db.query(AttorneyCommunication)

        if attorney_id:
            query = query.filter(AttorneyCommunication.attorney_id == attorney_id)

        if case_id:
            query = query.filter(AttorneyCommunication.case_id == case_id)

        if requires_response is not None:
            query = query.filter(
                AttorneyCommunication.requires_response == requires_response,
                AttorneyCommunication.responded == False
            )

        total = query.count()

        communications = query.order_by(
            AttorneyCommunication.communication_date.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "success": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "communications": [
                {
                    "id": c.id,
                    "attorney_id": c.attorney_id,
                    "case_id": c.case_id,
                    "type": c.communication_type.value if c.communication_type else "other",
                    "direction": c.direction,
                    "subject": c.subject,
                    "date": c.communication_date.isoformat() if c.communication_date else None,
                    "requires_response": c.requires_response,
                    "response_deadline": c.response_deadline.isoformat() if c.response_deadline else None,
                    "responded": c.responded,
                    "importance": c.importance
                }
                for c in communications
            ]
        }

    except Exception as e:
        logger.error(f"Error listing communications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list communications: {str(e)}"
        )


# ============================================================================
# CASE ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/assignments")
async def assign_attorney_to_case(
    request: CaseAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Assign an attorney to a case.
    """
    try:
        # Verify attorney exists
        attorney = db.query(Attorney).filter(
            Attorney.id == request.attorney_id,
            Attorney.is_deleted == False
        ).first()

        if not attorney:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attorney not found"
            )

        assignment_id = str(uuid.uuid4())

        assignment = AttorneyCaseAssignment(
            id=assignment_id,
            attorney_id=request.attorney_id,
            case_id=request.case_id,
            case_number=request.case_number,
            role=request.role,
            is_primary=request.is_primary,
            is_opposing=request.is_opposing,
            hourly_rate=request.hourly_rate,
            billing_arrangement=request.billing_arrangement,
            notes=request.notes,
            responsibilities=request.responsibilities,
            assignment_date=datetime.utcnow(),
            created_by_user_id=current_user.id
        )

        db.add(assignment)
        db.commit()

        return {
            "success": True,
            "assignment_id": assignment_id,
            "message": f"{attorney.full_name} assigned to case successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning attorney: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign attorney: {str(e)}"
        )
