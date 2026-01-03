"""
Case Management API Endpoints
Comprehensive REST API for legal case tracking and management
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..src.core.database import get_db
from ..api.deps.auth import get_current_user, CurrentUser
from ..models.case_management import (
    LegalCase as Case, CaseParty as Party, LegalCaseDocument as CaseDocument,
    CaseTimelineEvent as TimelineEvent, CaseFinancialTransaction as FinancialTransaction,
    CaseAsset as Asset, CaseBiddingProcess as BiddingProcess, CaseObjection as Objection,
    CaseEventParty as EventParty,
    CaseStatus, CaseType, PartyRole, EventType, EventStatus,
    TransactionType, AssetStatus, ObjectionStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["Case Management"])


# ============================================================================
# PYDANTIC MODELS - Request/Response Schemas
# ============================================================================

class CaseCreate(BaseModel):
    case_number: str
    case_name: str
    case_type: CaseType
    court_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    judge_name: Optional[str] = None
    filing_date: Optional[datetime] = None
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    case_name: Optional[str] = None
    status: Optional[CaseStatus] = None
    current_phase: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CaseResponse(BaseModel):
    id: str
    case_number: str
    case_name: str
    case_type: str
    status: str
    court_name: Optional[str]
    jurisdiction: Optional[str]
    filing_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PartyCreate(BaseModel):
    case_id: str
    role: PartyRole
    name: str
    party_type: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class PartyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    authorization_level: Optional[str] = None
    notes: Optional[str] = None


class TimelineEventCreate(BaseModel):
    case_id: str
    event_type: EventType
    title: str
    event_date: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    required_actions: Optional[List[Dict[str, Any]]] = None


class TimelineEventUpdate(BaseModel):
    title: Optional[str] = None
    event_date: Optional[datetime] = None
    status: Optional[EventStatus] = None
    description: Optional[str] = None
    outcome: Optional[str] = None
    completion_percentage: Optional[int] = None


class FinancialTransactionCreate(BaseModel):
    case_id: str
    transaction_type: TransactionType
    transaction_date: datetime
    amount: float
    description: Optional[str] = None
    party_id: Optional[str] = None


class AssetCreate(BaseModel):
    case_id: str
    asset_type: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    estimated_value: Optional[float] = None
    status: Optional[AssetStatus] = AssetStatus.PENDING


class BiddingProcessCreate(BaseModel):
    case_id: str
    asset_id: str
    process_name: str
    bidding_start_date: datetime
    bidding_end_date: datetime
    minimum_bid: Optional[float] = None
    deposit_required: bool = True


class ObjectionCreate(BaseModel):
    case_id: str
    objection_type: str
    title: str
    grounds: str
    filed_by_party_id: str
    filing_date: datetime
    response_deadline: Optional[datetime] = None


# ============================================================================
# CASE ENDPOINTS
# ============================================================================

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db)
) -> Case:
    """Create a new case"""
    try:
        new_case = Case(
            id=str(uuid.uuid4()),
            case_number=case.case_number,
            case_name=case.case_name,
            case_type=case.case_type,
            court_name=case.court_name,
            jurisdiction=case.jurisdiction,
            judge_name=case.judge_name,
            filing_date=case.filing_date,
            description=case.description,
            status=CaseStatus.ACTIVE
        )

        db.add(new_case)
        db.commit()
        db.refresh(new_case)

        logger.info(f"Created case: {new_case.case_number}")
        return new_case

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case: {str(e)}"
        )


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    status_filter: Optional[CaseStatus] = None,
    case_type_filter: Optional[CaseType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Case]:
    """List all cases for the current user with optional filtering"""
    try:
        # Filter by current user AND not deleted
        query = db.query(Case).filter(
            Case.is_deleted == False,
            Case.created_by == str(current_user.user_id)
        )

        if status_filter:
            query = query.filter(Case.status == status_filter)
        if case_type_filter:
            query = query.filter(Case.case_type == case_type_filter)

        cases = query.order_by(Case.filing_date.desc()).offset(skip).limit(limit).all()

        return cases

    except Exception as e:
        logger.error(f"Error listing cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cases: {str(e)}"
        )


@router.get("/{case_id}")
async def get_case(
    case_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed case information including all related data"""
    try:
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.is_deleted == False
        ).first()

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Get related data counts
        parties_count = db.query(Party).filter(Party.case_id == case_id).count()
        events_count = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).count()
        assets_count = db.query(Asset).filter(Asset.case_id == case_id).count()

        return {
            "id": case.id,
            "case_number": case.case_number,
            "case_name": case.case_name,
            "case_type": case.case_type.value,
            "status": case.status.value,
            "court_name": case.court_name,
            "jurisdiction": case.jurisdiction,
            "judge_name": case.judge_name,
            "filing_date": case.filing_date.isoformat() if case.filing_date else None,
            "current_phase": case.current_phase,
            "description": case.description,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
            "notes": case.notes,
            "tags": case.tags,
            "counts": {
                "parties": parties_count,
                "events": events_count,
                "assets": assets_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get case: {str(e)}"
        )


@router.patch("/{case_id}")
async def update_case(
    case_id: str,
    case_update: CaseUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update case information"""
    try:
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.is_deleted == False
        ).first()

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Update fields if provided
        update_data = case_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)

        case.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(case)

        logger.info(f"Updated case: {case.case_number}")

        return {
            "id": case.id,
            "case_number": case.case_number,
            "status": case.status.value,
            "updated_at": case.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update case: {str(e)}"
        )


@router.delete("/{case_id}")
async def delete_case(
    case_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Soft delete a case"""
    try:
        case = db.query(Case).filter(Case.id == case_id).first()

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        case.is_deleted = True
        case.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Deleted case: {case.case_number}")

        return {"message": "Case deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete case: {str(e)}"
        )


# ============================================================================
# PARTY ENDPOINTS
# ============================================================================

@router.post("/{case_id}/parties", status_code=status.HTTP_201_CREATED)
async def create_party(
    case_id: str,
    party: PartyCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Add a party to a case"""
    try:
        # Verify case exists
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        new_party = Party(
            id=str(uuid.uuid4()),
            case_id=case_id,
            role=party.role,
            name=party.name,
            party_type=party.party_type,
            email=party.email,
            phone=party.phone,
            address=party.address
        )

        db.add(new_party)
        db.commit()
        db.refresh(new_party)

        logger.info(f"Created party: {new_party.name} for case {case_id}")

        return {
            "id": new_party.id,
            "name": new_party.name,
            "role": new_party.role.value,
            "created_at": new_party.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating party: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create party: {str(e)}"
        )


@router.get("/{case_id}/parties")
async def list_parties(
    case_id: str,
    role_filter: Optional[PartyRole] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all parties in a case"""
    try:
        query = db.query(Party).filter(
            Party.case_id == case_id,
            Party.is_active == True
        )

        if role_filter:
            query = query.filter(Party.role == role_filter)

        parties = query.all()

        return [{
            "id": p.id,
            "name": p.name,
            "role": p.role.value,
            "email": p.email,
            "phone": p.phone,
            "authorization_level": p.authorization_level,
            "created_at": p.created_at.isoformat()
        } for p in parties]

    except Exception as e:
        logger.error(f"Error listing parties: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list parties: {str(e)}"
        )


@router.get("/{case_id}/parties/{party_id}")
async def get_party(
    case_id: str,
    party_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed party information"""
    try:
        party = db.query(Party).filter(
            Party.id == party_id,
            Party.case_id == case_id,
            Party.is_active == True
        ).first()

        if not party:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Party not found"
            )

        return {
            "id": party.id,
            "name": party.name,
            "legal_name": party.legal_name,
            "role": party.role.value,
            "party_type": party.party_type,
            "email": party.email,
            "phone": party.phone,
            "address": party.address,
            "claims_held": party.claims_held,
            "interest_amount": float(party.interest_amount) if party.interest_amount else None,
            "authorization_level": party.authorization_level,
            "preferred_contact_method": party.preferred_contact_method,
            "notes": party.notes,
            "created_at": party.created_at.isoformat(),
            "updated_at": party.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting party: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get party: {str(e)}"
        )


# ============================================================================
# TIMELINE EVENT ENDPOINTS
# ============================================================================

@router.post("/{case_id}/events", status_code=status.HTTP_201_CREATED)
async def create_timeline_event(
    case_id: str,
    event: TimelineEventCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a timeline event for a case"""
    try:
        new_event = TimelineEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type=event.event_type,
            title=event.title,
            event_date=event.event_date,
            description=event.description,
            location=event.location,
            required_actions=event.required_actions
        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        logger.info(f"Created event: {new_event.title} for case {case_id}")

        return {
            "id": new_event.id,
            "title": new_event.title,
            "event_type": new_event.event_type.value,
            "event_date": new_event.event_date.isoformat(),
            "status": new_event.status.value,
            "created_at": new_event.created_at.isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )


@router.get("/{case_id}/events")
async def list_timeline_events(
    case_id: str,
    event_type_filter: Optional[EventType] = None,
    status_filter: Optional[EventStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all timeline events for a case"""
    try:
        query = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id)

        if event_type_filter:
            query = query.filter(TimelineEvent.event_type == event_type_filter)
        if status_filter:
            query = query.filter(TimelineEvent.status == status_filter)
        if start_date:
            query = query.filter(TimelineEvent.event_date >= start_date)
        if end_date:
            query = query.filter(TimelineEvent.event_date <= end_date)

        events = query.order_by(TimelineEvent.event_date.asc()).all()

        return [{
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type.value,
            "event_date": e.event_date.isoformat(),
            "status": e.status.value,
            "location": e.location,
            "is_critical_path": e.is_critical_path,
            "priority_level": e.priority_level
        } for e in events]

    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {str(e)}"
        )


@router.patch("/{case_id}/events/{event_id}")
async def update_timeline_event(
    case_id: str,
    event_id: str,
    event_update: TimelineEventUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update a timeline event"""
    try:
        event = db.query(TimelineEvent).filter(
            TimelineEvent.id == event_id,
            TimelineEvent.case_id == case_id
        ).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        update_data = event_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        if event_update.status == EventStatus.COMPLETED and not event.completed_at:
            event.completed_at = datetime.utcnow()

        event.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(event)

        logger.info(f"Updated event: {event.title}")

        return {
            "id": event.id,
            "title": event.title,
            "status": event.status.value,
            "updated_at": event.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}"
        )


# ============================================================================
# DASHBOARD & ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/{case_id}/dashboard")
async def get_case_dashboard(
    case_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive dashboard data for a case"""
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Get upcoming deadlines (next 30 days)
        upcoming_deadlines = db.query(TimelineEvent).filter(
            TimelineEvent.case_id == case_id,
            TimelineEvent.event_type == EventType.DEADLINE,
            TimelineEvent.event_date >= datetime.utcnow(),
            TimelineEvent.status != EventStatus.COMPLETED
        ).order_by(TimelineEvent.event_date.asc()).limit(10).all()

        # Get at-risk items (deadlines within 7 days)
        at_risk_items = db.query(TimelineEvent).filter(
            TimelineEvent.case_id == case_id,
            TimelineEvent.event_date >= datetime.utcnow(),
            TimelineEvent.event_date <= datetime.utcnow() + timedelta(days=7),
            TimelineEvent.status != EventStatus.COMPLETED
        ).count()

        # Get active assets
        active_assets = db.query(Asset).filter(
            Asset.case_id == case_id,
            Asset.status.in_([AssetStatus.INCLUDED, AssetStatus.PENDING])
        ).all()

        # Get pending objections
        pending_objections = db.query(Objection).filter(
            Objection.case_id == case_id,
            Objection.status.in_([ObjectionStatus.FILED, ObjectionStatus.PENDING])
        ).count()

        return {
            "case_info": {
                "id": case.id,
                "case_number": case.case_number,
                "case_name": case.case_name,
                "status": case.status.value,
                "current_phase": case.current_phase
            },
            "deadlines": {
                "upcoming": [{
                    "id": d.id,
                    "title": d.title,
                    "date": d.event_date.isoformat(),
                    "days_until": (d.event_date - datetime.utcnow()).days
                } for d in upcoming_deadlines],
                "at_risk_count": at_risk_items
            },
            "assets": {
                "count": len(active_assets),
                "total_value": sum(float(a.estimated_value or 0) for a in active_assets)
            },
            "objections": {
                "pending_count": pending_objections
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


# Import timedelta for dashboard endpoint
from datetime import timedelta


# ============================================================================
# FINANCIAL TRANSACTION ENDPOINTS
# ============================================================================

@router.post("/{case_id}/transactions", status_code=status.HTTP_201_CREATED)
async def create_financial_transaction(
    case_id: str,
    transaction: FinancialTransactionCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a financial transaction for a case"""
    try:
        new_transaction = FinancialTransaction(
            id=str(uuid.uuid4()),
            case_id=case_id,
            transaction_type=transaction.transaction_type,
            transaction_date=transaction.transaction_date,
            amount=transaction.amount,
            description=transaction.description,
            party_id=transaction.party_id
        )

        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        logger.info(f"Created transaction: {new_transaction.transaction_type} for case {case_id}")

        return {
            "id": new_transaction.id,
            "transaction_type": new_transaction.transaction_type.value,
            "amount": float(new_transaction.amount),
            "transaction_date": new_transaction.transaction_date.isoformat(),
            "created_at": new_transaction.created_at.isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )


@router.get("/{case_id}/transactions")
async def list_transactions(
    case_id: str,
    transaction_type_filter: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all financial transactions for a case"""
    try:
        query = db.query(FinancialTransaction).filter(
            FinancialTransaction.case_id == case_id
        )

        if transaction_type_filter:
            query = query.filter(FinancialTransaction.transaction_type == transaction_type_filter)
        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)

        transactions = query.order_by(FinancialTransaction.transaction_date.desc()).all()

        return [{
            "id": t.id,
            "transaction_type": t.transaction_type.value,
            "amount": float(t.amount),
            "transaction_date": t.transaction_date.isoformat(),
            "description": t.description,
            "payment_status": t.payment_status,
            "approval_status": t.approval_status
        } for t in transactions]

    except Exception as e:
        logger.error(f"Error listing transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list transactions: {str(e)}"
        )


# ============================================================================
# ASSET ENDPOINTS
# ============================================================================

@router.post("/{case_id}/assets", status_code=status.HTTP_201_CREATED)
async def create_asset(
    case_id: str,
    asset: AssetCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Add an asset to a case"""
    try:
        new_asset = Asset(
            id=str(uuid.uuid4()),
            case_id=case_id,
            asset_type=asset.asset_type,
            name=asset.name,
            category=asset.category,
            description=asset.description,
            estimated_value=asset.estimated_value,
            status=asset.status
        )

        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)

        logger.info(f"Created asset: {new_asset.name} for case {case_id}")

        return {
            "id": new_asset.id,
            "name": new_asset.name,
            "asset_type": new_asset.asset_type,
            "status": new_asset.status.value,
            "estimated_value": float(new_asset.estimated_value) if new_asset.estimated_value else None,
            "created_at": new_asset.created_at.isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create asset: {str(e)}"
        )


@router.get("/{case_id}/assets")
async def list_assets(
    case_id: str,
    status_filter: Optional[AssetStatus] = None,
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all assets in a case"""
    try:
        query = db.query(Asset).filter(Asset.case_id == case_id)

        if status_filter:
            query = query.filter(Asset.status == status_filter)
        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)

        assets = query.all()

        return [{
            "id": a.id,
            "name": a.name,
            "asset_type": a.asset_type,
            "category": a.category,
            "status": a.status.value,
            "estimated_value": float(a.estimated_value) if a.estimated_value else None,
            "has_liens": a.has_liens,
            "lien_amount": float(a.lien_amount) if a.lien_amount else None,
            "created_at": a.created_at.isoformat()
        } for a in assets]

    except Exception as e:
        logger.error(f"Error listing assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list assets: {str(e)}"
        )


@router.get("/{case_id}/assets/{asset_id}")
async def get_asset_details(
    case_id: str,
    asset_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed asset information"""
    try:
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.case_id == case_id
        ).first()

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )

        return {
            "id": asset.id,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "category": asset.category,
            "description": asset.description,
            "status": asset.status.value,
            "location": asset.location,
            "identification_number": asset.identification_number,
            "estimated_value": float(asset.estimated_value) if asset.estimated_value else None,
            "appraised_value": float(asset.appraised_value) if asset.appraised_value else None,
            "market_value": float(asset.market_value) if asset.market_value else None,
            "valuation_date": asset.valuation_date.isoformat() if asset.valuation_date else None,
            "has_liens": asset.has_liens,
            "lien_amount": float(asset.lien_amount) if asset.lien_amount else None,
            "lien_holders": asset.lien_holders,
            "encumbrances": asset.encumbrances,
            "has_contracts": asset.has_contracts,
            "contract_details": asset.contract_details,
            "minimum_bid": float(asset.minimum_bid) if asset.minimum_bid else None,
            "current_high_bid": float(asset.current_high_bid) if asset.current_high_bid else None,
            "notes": asset.notes,
            "created_at": asset.created_at.isoformat(),
            "updated_at": asset.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset: {str(e)}"
        )


# ============================================================================
# BIDDING PROCESS ENDPOINTS
# ============================================================================

@router.post("/{case_id}/bidding", status_code=status.HTTP_201_CREATED)
async def create_bidding_process(
    case_id: str,
    bidding: BiddingProcessCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a bidding process for an asset"""
    try:
        # Verify asset exists
        asset = db.query(Asset).filter(Asset.id == bidding.asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )

        new_bidding = BiddingProcess(
            id=str(uuid.uuid4()),
            case_id=case_id,
            asset_id=bidding.asset_id,
            process_name=bidding.process_name,
            bidding_start_date=bidding.bidding_start_date,
            bidding_end_date=bidding.bidding_end_date,
            minimum_bid=bidding.minimum_bid,
            deposit_required=bidding.deposit_required
        )

        db.add(new_bidding)
        db.commit()
        db.refresh(new_bidding)

        logger.info(f"Created bidding process: {new_bidding.process_name} for case {case_id}")

        return {
            "id": new_bidding.id,
            "process_name": new_bidding.process_name,
            "asset_id": new_bidding.asset_id,
            "bidding_start_date": new_bidding.bidding_start_date.isoformat(),
            "bidding_end_date": new_bidding.bidding_end_date.isoformat(),
            "status": new_bidding.status,
            "created_at": new_bidding.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating bidding process: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bidding process: {str(e)}"
        )


@router.get("/{case_id}/bidding")
async def list_bidding_processes(
    case_id: str,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all bidding processes for a case"""
    try:
        query = db.query(BiddingProcess).filter(BiddingProcess.case_id == case_id)

        if status_filter:
            query = query.filter(BiddingProcess.status == status_filter)

        processes = query.order_by(BiddingProcess.bidding_start_date.desc()).all()

        return [{
            "id": p.id,
            "process_name": p.process_name,
            "asset_id": p.asset_id,
            "status": p.status,
            "bidding_start_date": p.bidding_start_date.isoformat(),
            "bidding_end_date": p.bidding_end_date.isoformat(),
            "minimum_bid": float(p.minimum_bid) if p.minimum_bid else None,
            "highest_bid_amount": float(p.highest_bid_amount) if p.highest_bid_amount else None,
            "deposit_required": p.deposit_required
        } for p in processes]

    except Exception as e:
        logger.error(f"Error listing bidding processes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list bidding processes: {str(e)}"
        )


@router.get("/{case_id}/bidding/{bidding_id}")
async def get_bidding_details(
    case_id: str,
    bidding_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed bidding process information"""
    try:
        bidding = db.query(BiddingProcess).filter(
            BiddingProcess.id == bidding_id,
            BiddingProcess.case_id == case_id
        ).first()

        if not bidding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bidding process not found"
            )

        return {
            "id": bidding.id,
            "process_name": bidding.process_name,
            "process_type": bidding.process_type,
            "status": bidding.status,
            "asset_id": bidding.asset_id,
            "bidding_start_date": bidding.bidding_start_date.isoformat(),
            "bidding_end_date": bidding.bidding_end_date.isoformat(),
            "qualified_bidder_criteria": bidding.qualified_bidder_criteria,
            "approved_bidders": bidding.approved_bidders,
            "deposit_required": bidding.deposit_required,
            "deposit_amount": float(bidding.deposit_amount) if bidding.deposit_amount else None,
            "deposit_percentage": float(bidding.deposit_percentage) if bidding.deposit_percentage else None,
            "minimum_bid": float(bidding.minimum_bid) if bidding.minimum_bid else None,
            "bid_increment": float(bidding.bid_increment) if bidding.bid_increment else None,
            "reserve_price": float(bidding.reserve_price) if bidding.reserve_price else None,
            "allows_credit_bid": bidding.allows_credit_bid,
            "bids": bidding.bids,
            "highest_bid_amount": float(bidding.highest_bid_amount) if bidding.highest_bid_amount else None,
            "highest_bidder_id": bidding.highest_bidder_id,
            "evaluation_criteria": bidding.evaluation_criteria,
            "sale_approved": bidding.sale_approved,
            "final_sale_price": float(bidding.final_sale_price) if bidding.final_sale_price else None,
            "notes": bidding.notes,
            "created_at": bidding.created_at.isoformat(),
            "updated_at": bidding.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bidding details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bidding details: {str(e)}"
        )


@router.post("/{case_id}/bidding/{bidding_id}/bids", status_code=status.HTTP_201_CREATED)
async def submit_bid(
    case_id: str,
    bidding_id: str,
    bid_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Submit a bid in a bidding process"""
    try:
        bidding = db.query(BiddingProcess).filter(
            BiddingProcess.id == bidding_id,
            BiddingProcess.case_id == case_id
        ).first()

        if not bidding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bidding process not found"
            )

        if bidding.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bidding process is not open"
            )

        # Validate bid amount
        bid_amount = bid_data.get("amount")
        if not bid_amount or bid_amount < float(bidding.minimum_bid or 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bid must be at least {bidding.minimum_bid}"
            )

        # Add bid to bids array
        current_bids = bidding.bids or []
        new_bid = {
            "id": str(uuid.uuid4()),
            "bidder_id": bid_data.get("bidder_id"),
            "amount": bid_amount,
            "timestamp": datetime.utcnow().isoformat(),
            "notes": bid_data.get("notes")
        }
        current_bids.append(new_bid)
        bidding.bids = current_bids

        # Update highest bid if applicable
        if not bidding.highest_bid_amount or bid_amount > float(bidding.highest_bid_amount):
            bidding.highest_bid_amount = bid_amount
            bidding.highest_bidder_id = bid_data.get("bidder_id")

        db.commit()
        db.refresh(bidding)

        logger.info(f"Bid submitted: ${bid_amount} for bidding process {bidding_id}")

        return {
            "success": True,
            "bid": new_bid,
            "is_highest_bid": bid_amount == float(bidding.highest_bid_amount)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting bid: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit bid: {str(e)}"
        )


# ============================================================================
# OBJECTION ENDPOINTS
# ============================================================================

@router.post("/{case_id}/objections", status_code=status.HTTP_201_CREATED)
async def create_objection(
    case_id: str,
    objection: ObjectionCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """File an objection in a case"""
    try:
        new_objection = Objection(
            id=str(uuid.uuid4()),
            case_id=case_id,
            objection_type=objection.objection_type,
            title=objection.title,
            grounds=objection.grounds,
            filed_by_party_id=objection.filed_by_party_id,
            filing_date=objection.filing_date,
            response_deadline=objection.response_deadline
        )

        db.add(new_objection)
        db.commit()
        db.refresh(new_objection)

        logger.info(f"Created objection: {new_objection.title} for case {case_id}")

        return {
            "id": new_objection.id,
            "title": new_objection.title,
            "objection_type": new_objection.objection_type,
            "status": new_objection.status.value,
            "filing_date": new_objection.filing_date.isoformat(),
            "response_deadline": new_objection.response_deadline.isoformat() if new_objection.response_deadline else None,
            "created_at": new_objection.created_at.isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating objection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create objection: {str(e)}"
        )


@router.get("/{case_id}/objections")
async def list_objections(
    case_id: str,
    status_filter: Optional[ObjectionStatus] = None,
    objection_type: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all objections in a case"""
    try:
        query = db.query(Objection).filter(Objection.case_id == case_id)

        if status_filter:
            query = query.filter(Objection.status == status_filter)
        if objection_type:
            query = query.filter(Objection.objection_type == objection_type)

        objections = query.order_by(Objection.filing_date.desc()).all()

        return [{
            "id": o.id,
            "title": o.title,
            "objection_type": o.objection_type,
            "status": o.status.value,
            "filing_date": o.filing_date.isoformat(),
            "response_deadline": o.response_deadline.isoformat() if o.response_deadline else None,
            "filed_by_party_id": o.filed_by_party_id,
            "impact_on_timeline": o.impact_on_timeline
        } for o in objections]

    except Exception as e:
        logger.error(f"Error listing objections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list objections: {str(e)}"
        )


@router.get("/{case_id}/objections/{objection_id}")
async def get_objection_details(
    case_id: str,
    objection_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed objection information"""
    try:
        objection = db.query(Objection).filter(
            Objection.id == objection_id,
            Objection.case_id == case_id
        ).first()

        if not objection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Objection not found"
            )

        return {
            "id": objection.id,
            "title": objection.title,
            "objection_type": objection.objection_type,
            "description": objection.description,
            "grounds": objection.grounds,
            "status": objection.status.value,
            "filed_by_party_id": objection.filed_by_party_id,
            "objection_to_party_id": objection.objection_to_party_id,
            "affected_parties": objection.affected_parties,
            "filing_date": objection.filing_date.isoformat(),
            "response_deadline": objection.response_deadline.isoformat() if objection.response_deadline else None,
            "hearing_date": objection.hearing_date.isoformat() if objection.hearing_date else None,
            "resolution_date": objection.resolution_date.isoformat() if objection.resolution_date else None,
            "resolution": objection.resolution,
            "resolution_type": objection.resolution_type,
            "impact_on_timeline": objection.impact_on_timeline,
            "blocks_event_ids": objection.blocks_event_ids,
            "delays_days": objection.delays_days,
            "responses_required_from": objection.responses_required_from,
            "responses_received": objection.responses_received,
            "response_status": objection.response_status,
            "legal_authority": objection.legal_authority,
            "precedent_cases": objection.precedent_cases,
            "notes": objection.notes,
            "created_at": objection.created_at.isoformat(),
            "updated_at": objection.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting objection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get objection: {str(e)}"
        )


# ============================================================================
# WORKFLOW & INTELLIGENCE ENDPOINTS
# ============================================================================

@router.get("/{case_id}/timeline/critical-path")
async def get_critical_path(
    case_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get critical path analysis for case timeline"""
    try:
        from ..src.services.case_workflow_service import timeline_workflow_engine

        # Get all timeline events
        events_query = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()

        events = [{
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type.value,
            "event_date": e.event_date,
            "status": e.status.value,
            "blocked_by_event_ids": e.blocked_by_event_ids or [],
            "blocks_event_ids": e.blocks_event_ids or [],
            "is_critical_path": e.is_critical_path
        } for e in events_query]

        # Calculate critical path
        critical_path = timeline_workflow_engine.calculate_critical_path(events)

        # Calculate parallel opportunities
        parallel_opportunities = timeline_workflow_engine.check_parallel_opportunities(events)

        return {
            "case_id": case_id,
            "total_events": len(events),
            "critical_path_events": critical_path,
            "parallel_opportunities": parallel_opportunities,
            "estimated_completion": max([e['event_date'] for e in events]) if events else None
        }

    except Exception as e:
        logger.error(f"Error calculating critical path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate critical path: {str(e)}"
        )


@router.get("/{case_id}/timeline/{event_id}/impact")
async def analyze_event_impact(
    case_id: str,
    event_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze impact of changing an event's deadline"""
    try:
        from ..src.services.case_workflow_service import timeline_workflow_engine

        # Get the event
        event = db.query(TimelineEvent).filter(
            TimelineEvent.id == event_id,
            TimelineEvent.case_id == case_id
        ).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Get all events for cascade analysis
        all_events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()

        events_data = [{
            "id": e.id,
            "title": e.title,
            "event_date": e.event_date,
            "blocked_by_event_ids": e.blocked_by_event_ids or [],
            "blocks_event_ids": e.blocks_event_ids or []
        } for e in all_events]

        event_data = {
            "id": event.id,
            "title": event.title,
            "event_date": event.event_date,
            "blocked_by_event_ids": event.blocked_by_event_ids or [],
            "blocks_event_ids": event.blocks_event_ids or []
        }

        # Identify cascade effects
        cascade = timeline_workflow_engine.identify_deadline_cascades(event_data, events_data)

        # Suggest buffer time
        buffer = timeline_workflow_engine.suggest_buffer_time(event.event_type.value)

        return {
            "event": {
                "id": event.id,
                "title": event.title,
                "event_date": event.event_date.isoformat()
            },
            "affected_events": cascade,
            "total_impacted": len(cascade),
            "suggested_buffer_days": buffer,
            "risk_level": "HIGH" if len(cascade) > 3 else "MEDIUM" if len(cascade) > 0 else "LOW"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing event impact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze event impact: {str(e)}"
        )


@router.get("/{case_id}/briefing/strategic-summary")
async def get_strategic_briefing(
    case_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate strategic briefing for attorneys"""
    try:
        from ..src.services.attorney_briefing_service import attorney_briefing_generator

        # Get case data
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Get related data
        events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()
        parties = db.query(Party).filter(Party.case_id == case_id).all()
        assets = db.query(Asset).filter(Asset.case_id == case_id).all()

        # Convert to dicts
        case_data = {
            "case_number": case.case_number,
            "case_name": case.case_name,
            "current_phase": case.current_phase,
            "status": case.status.value,
            "filing_date": case.filing_date or datetime.utcnow()
        }

        events_data = [{
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type.value,
            "event_date": e.event_date,
            "status": e.status.value,
            "priority_level": e.priority_level,
            "is_critical_path": e.is_critical_path
        } for e in events]

        parties_data = [{"id": p.id, "name": p.name, "role": p.role.value} for p in parties]
        assets_data = [{"id": a.id, "name": a.name, "estimated_value": a.estimated_value} for a in assets]

        # Generate strategic summary
        summary = attorney_briefing_generator.generate_strategic_summary(
            case_data, events_data, parties_data, assets_data
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating strategic briefing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate strategic briefing: {str(e)}"
        )


@router.get("/{case_id}/briefing/talking-points")
async def get_talking_points(
    case_id: str,
    next_hearing_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate talking points for hearings and negotiations"""
    try:
        from ..src.services.attorney_briefing_service import attorney_briefing_generator

        # Get case data
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        case_data = {
            "case_number": case.case_number,
            "case_name": case.case_name,
            "status": case.status.value
        }

        # Get next hearing if specified
        next_hearing = None
        if next_hearing_id:
            hearing = db.query(TimelineEvent).filter(TimelineEvent.id == next_hearing_id).first()
            if hearing:
                next_hearing = {
                    "id": hearing.id,
                    "title": hearing.title,
                    "event_type": hearing.event_type.value,
                    "event_date": hearing.event_date
                }

        # Get objections
        objections = db.query(Objection).filter(
            Objection.case_id == case_id,
            Objection.status.in_([ObjectionStatus.FILED, ObjectionStatus.PENDING])
        ).all()

        objections_data = [{
            "id": o.id,
            "title": o.title,
            "objection_type": o.objection_type,
            "legal_authority": o.legal_authority
        } for o in objections]

        # Generate talking points
        talking_points = attorney_briefing_generator.generate_talking_points(
            case_data, next_hearing, objections_data
        )

        return talking_points

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating talking points: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate talking points: {str(e)}"
        )


@router.get("/{case_id}/briefing/action-items")
async def get_action_items(
    case_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate prioritized action items for case"""
    try:
        from ..src.services.attorney_briefing_service import attorney_briefing_generator

        # Get case data
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Get events and objections
        events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()
        objections = db.query(Objection).filter(Objection.case_id == case_id).all()

        case_data = {"case_number": case.case_number, "status": case.status.value}

        events_data = [{
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type.value,
            "event_date": e.event_date,
            "status": e.status.value,
            "description": e.description,
            "required_actions": e.required_actions,
            "responsible_parties": e.required_parties,
            "blocked_by_event_ids": e.blocked_by_event_ids
        } for e in events]

        objections_data = [{"id": o.id, "title": o.title, "status": o.status.value} for o in objections]

        # Generate action items
        action_items = attorney_briefing_generator.generate_action_items(
            case_data, events_data, objections_data
        )

        return {
            "case_id": case_id,
            "generated_at": datetime.utcnow().isoformat(),
            "total_action_items": len(action_items),
            "urgent_items": len([a for a in action_items if a.get('priority') == 'URGENT']),
            "action_items": action_items
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating action items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate action items: {str(e)}"
        )


@router.post("/{case_id}/bidding/{bidding_id}/calculate")
async def calculate_bidding_amounts(
    case_id: str,
    bidding_id: str,
    calculation_type: str = Query(..., description="Type of calculation: increment, deposit, distribution"),
    params: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Calculate bidding-related amounts using business logic"""
    try:
        from ..src.services.case_workflow_service import business_logic_calculator

        # Get bidding process
        bidding = db.query(BiddingProcess).filter(
            BiddingProcess.id == bidding_id,
            BiddingProcess.case_id == case_id
        ).first()

        if not bidding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bidding process not found"
            )

        # Get asset for value reference
        asset = db.query(Asset).filter(Asset.id == bidding.asset_id).first()

        result = {}

        if calculation_type == "increment":
            current_bid = params.get('current_bid', float(bidding.highest_bid_amount or bidding.minimum_bid or 0))
            increment = business_logic_calculator.calculate_bid_increment(
                Decimal(str(current_bid)),
                Decimal(str(asset.estimated_value)) if asset and asset.estimated_value else None
            )
            result = {
                "current_bid": current_bid,
                "minimum_increment": float(increment),
                "next_minimum_bid": current_bid + float(increment)
            }

        elif calculation_type == "deposit":
            bid_amount = params.get('bid_amount', float(bidding.minimum_bid or 0))
            deposit = business_logic_calculator.calculate_deposit_requirement(
                Decimal(str(bid_amount)),
                Decimal(str(bidding.deposit_percentage)) if bidding.deposit_percentage else None
            )
            result = {
                "bid_amount": bid_amount,
                "required_deposit": float(deposit),
                "deposit_percentage": float(deposit / Decimal(str(bid_amount)) * 100) if bid_amount > 0 else 0
            }

        elif calculation_type == "credit_bid":
            params_required = ['claim_amount', 'secured_amount']
            if not all(k in params for k in params_required):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameters: {params_required}"
                )

            credit_bid_calc = business_logic_calculator.calculate_credit_bid_conversion(
                Decimal(str(params['claim_amount'])),
                Decimal(str(params['secured_amount'])),
                Decimal(str(asset.estimated_value)) if asset and asset.estimated_value else Decimal("0")
            )
            result = {k: float(v) for k, v in credit_bid_calc.items()}

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown calculation type: {calculation_type}"
            )

        return {
            "calculation_type": calculation_type,
            "bidding_process_id": bidding_id,
            "result": result,
            "calculated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating bidding amounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate bidding amounts: {str(e)}"
        )


# ============================================================================
# DOCUMENT LINKING ENDPOINTS
# ============================================================================

@router.post("/{case_id}/documents", status_code=status.HTTP_201_CREATED)
async def link_document_to_case(
    case_id: str,
    document_id: str = Body(..., embed=True),
    document_role: Optional[str] = Body(None),
    filing_date: Optional[datetime] = Body(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Link an existing document to a case"""
    try:
        # Verify case exists
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Check if link already exists
        existing_link = db.query(CaseDocument).filter(
            and_(
                CaseDocument.case_id == case_id,
                CaseDocument.document_id == document_id
            )
        ).first()

        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is already linked to this case"
            )

        # Create link
        new_link = CaseDocument(
            id=str(uuid.uuid4()),
            case_id=case_id,
            document_id=document_id,
            document_role=document_role,
            filing_date=filing_date or datetime.utcnow(),
            is_current_version=True
        )

        db.add(new_link)
        db.commit()
        db.refresh(new_link)

        logger.info(f"Linked document {document_id} to case {case_id}")

        return {
            "id": new_link.id,
            "case_id": new_link.case_id,
            "document_id": new_link.document_id,
            "document_role": new_link.document_role,
            "filing_date": new_link.filing_date.isoformat() if new_link.filing_date else None,
            "created_at": new_link.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error linking document to case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link document: {str(e)}"
        )


@router.get("/{case_id}/documents")
async def get_case_documents(
    case_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all documents linked to a case"""
    try:
        # Verify case exists
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Get linked documents
        from ..models.legal_documents import Document

        links = db.query(CaseDocument).filter(
            CaseDocument.case_id == case_id
        ).all()

        documents = []
        for link in links:
            # Get the actual document
            doc = db.query(Document).filter(
                Document.id == link.document_id,
                Document.is_deleted == False
            ).first()

            if doc:
                documents.append({
                    "link_id": link.id,
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "upload_date": doc.upload_date.isoformat(),
                    "document_role": link.document_role,
                    "filing_date": link.filing_date.isoformat() if link.filing_date else None,
                    "summary": doc.summary,
                    "parties": doc.parties,
                    "keywords": doc.keywords
                })

        return documents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting case documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.delete("/{case_id}/documents/{link_id}")
async def unlink_document_from_case(
    case_id: str,
    link_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Unlink a document from a case"""
    try:
        # Get the link
        link = db.query(CaseDocument).filter(
            and_(
                CaseDocument.id == link_id,
                CaseDocument.case_id == case_id
            )
        ).first()

        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document link not found"
            )

        # Delete the link
        db.delete(link)
        db.commit()

        logger.info(f"Unlinked document from case {case_id}")

        return {
            "success": True,
            "message": "Document unlinked from case"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error unlinking document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlink document: {str(e)}"
        )


# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================

@router.post("/{case_id}/notifications/send-reminder")
async def send_event_reminder(
    case_id: str,
    event_id: str = Body(..., embed=True),
    to_email: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send email reminder for a specific event"""
    try:
        from ..src.services.notification_service import get_notification_service

        # Get case
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )

        # Get event
        event = db.query(TimelineEvent).filter(
            and_(
                TimelineEvent.id == event_id,
                TimelineEvent.case_id == case_id
            )
        ).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Calculate days until event
        days_until = (event.event_date - datetime.utcnow()).days

        # Send notification
        notification_service = get_notification_service()
        success = notification_service.send_deadline_reminder(
            to_email=to_email,
            case_name=case.case_name,
            case_id=case.id,
            event_title=event.title,
            event_date=event.event_date,
            event_location=event.location,
            days_until=max(0, days_until)
        )

        if success:
            logger.info(f"Sent reminder for event {event_id} to {to_email}")
            return {
                "success": True,
                "message": f"Reminder sent to {to_email}",
                "event_id": event_id,
                "to_email": to_email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email - check SMTP configuration"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reminder: {str(e)}"
        )


@router.post("/notifications/send-digest")
async def send_deadlines_digest(
    to_email: str = Body(..., embed=True),
    days_ahead: int = Body(14, embed=True),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send digest email of upcoming deadlines across all cases"""
    try:
        from ..src.services.notification_service import get_notification_service

        notification_service = get_notification_service()

        # Get upcoming deadlines
        upcoming_deadlines = notification_service.get_upcoming_deadlines(
            db=db,
            days_ahead=days_ahead
        )

        if not upcoming_deadlines:
            return {
                "success": True,
                "message": "No upcoming deadlines to send",
                "deadline_count": 0
            }

        # Send digest
        success = notification_service.send_deadline_digest(
            to_email=to_email,
            upcoming_deadlines=upcoming_deadlines
        )

        if success:
            logger.info(f"Sent digest with {len(upcoming_deadlines)} deadlines to {to_email}")
            return {
                "success": True,
                "message": f"Digest sent to {to_email}",
                "deadline_count": len(upcoming_deadlines),
                "to_email": to_email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email - check SMTP configuration"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending digest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send digest: {str(e)}"
        )


@router.get("/notifications/upcoming-deadlines")
async def get_upcoming_deadlines(
    days_ahead: int = Query(14, description="Number of days to look ahead"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get list of upcoming deadlines across all cases"""
    try:
        from ..src.services.notification_service import get_notification_service

        notification_service = get_notification_service()
        deadlines = notification_service.get_upcoming_deadlines(
            db=db,
            days_ahead=days_ahead
        )

        return deadlines

    except Exception as e:
        logger.error(f"Error fetching upcoming deadlines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch deadlines: {str(e)}"
        )


@router.get("/notifications/next-reminders")
async def get_next_scheduled_reminders(
    days_ahead: int = Query(14, description="Number of days to look ahead"),
    limit: int = Query(10, description="Maximum number of reminders to return"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get list of next scheduled automatic reminders"""
    try:
        from ..src.services.reminder_scheduler import get_reminder_scheduler

        scheduler = get_reminder_scheduler()
        reminders = scheduler.get_next_reminders(
            db=db,
            days_ahead=days_ahead,
            limit=limit
        )

        return reminders

    except Exception as e:
        logger.error(f"Error fetching next reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reminders: {str(e)}"
        )


@router.get("/notifications/scheduler-status")
async def get_scheduler_status() -> Dict[str, Any]:
    """Get status of the automated reminder scheduler"""
    try:
        from ..src.services.reminder_scheduler import get_reminder_scheduler

        scheduler = get_reminder_scheduler()

        return {
            "running": scheduler.running,
            "check_interval_minutes": scheduler.check_interval_minutes,
            "enabled": scheduler.running
        }

    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler status: {str(e)}"
        )
