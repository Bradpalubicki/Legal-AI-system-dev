"""
Financial Validation API Endpoints
Provides validation reports and quality checks for extracted financial data
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..src.core.database import get_db
from ..models.legal_documents import Document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/financial", tags=["Financial Validation"])


class ValidationReport(BaseModel):
    """Validation report response model"""
    document_id: str
    filename: str
    validation_status: str  # complete, incomplete, needs_review
    missing_information: List[str]
    quality_flags: List[str]
    total_amounts_found: int
    has_bartenwerfer_citation: bool
    has_jurisdictional_basis: bool
    total_claims_for_relief: int
    total_monetary_exposure: str
    timeline_events_count: int


@router.get("/validation/{document_id}")
async def get_financial_validation(
    document_id: str,
    db: Session = Depends(get_db)
) -> ValidationReport:
    """
    Get financial data validation report for a document

    Returns comprehensive validation including:
    - Missing critical information
    - Data quality flags
    - Specific precedent citations (Bartenwerfer, jurisdictional)
    - Total claims and monetary exposure
    - Timeline completeness
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        financial_details = document.financial_details or {}
        metadata = financial_details.get("extraction_metadata", {})

        # Check for specific precedents
        precedents = financial_details.get("legal_precedents", [])
        has_bartenwerfer = any(
            "Bartenwerfer" in str(p.get("citation", ""))
            for p in precedents
        )

        has_jurisdictional = any(
            ("28 U.S.C." in str(p.get("citation", "")) and
             ("157" in str(p.get("citation", "")) or "1334" in str(p.get("citation", ""))))
            for p in precedents
        )

        # Get summary statistics
        summary = financial_details.get("summary_statistics", {})
        timeline = financial_details.get("timeline_of_events", [])

        return ValidationReport(
            document_id=document_id,
            filename=document.file_name,
            validation_status=metadata.get("validation_status", "unknown"),
            missing_information=metadata.get("missing_critical_information", []),
            quality_flags=metadata.get("data_quality_flags", []),
            total_amounts_found=metadata.get("total_financial_amounts_identified", 0),
            has_bartenwerfer_citation=has_bartenwerfer,
            has_jurisdictional_basis=has_jurisdictional,
            total_claims_for_relief=summary.get("total_claims_for_relief", 0),
            total_monetary_exposure=summary.get("total_monetary_exposure", "$0.00"),
            timeline_events_count=len(timeline)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating validation report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate validation report: {str(e)}"
        )


@router.get("/summary/{document_id}")
async def get_financial_summary(
    document_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive financial summary for a document

    Returns:
    - Total number of claims for relief
    - Total monetary exposure with breakdown
    - Timeline of key events
    - Creditor statistics
    - Precedent citations
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        financial_details = document.financial_details or {}

        return {
            "document_id": document_id,
            "filename": document.file_name,
            "summary_statistics": financial_details.get("summary_statistics", {}),
            "timeline_of_events": financial_details.get("timeline_of_events", []),
            "claims_summary": financial_details.get("claims_summary", {}),
            "total_debt_summary": financial_details.get("total_debt_summary", {}),
            "key_precedents": {
                "bartenwerfer_v_buckley": _find_precedent(
                    financial_details.get("legal_precedents", []),
                    "Bartenwerfer"
                ),
                "usc_28_157": _find_precedent(
                    financial_details.get("legal_precedents", []),
                    "28 U.S.C.",
                    "157"
                ),
                "usc_28_1334": _find_precedent(
                    financial_details.get("legal_precedents", []),
                    "28 U.S.C.",
                    "1334"
                )
            },
            "validation": {
                "status": financial_details.get("extraction_metadata", {}).get("validation_status"),
                "missing_info": financial_details.get("extraction_metadata", {}).get("missing_critical_information", []),
                "quality_flags": financial_details.get("extraction_metadata", {}).get("data_quality_flags", [])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating financial summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate financial summary: {str(e)}"
        )


@router.get("/missing-info/batch")
async def get_documents_with_missing_info(
    db: Session = Depends(get_db),
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get all documents with missing critical financial information

    Useful for:
    - Quality control audits
    - Identifying documents needing manual review
    - Batch re-processing
    """
    try:
        # Get all documents with financial_details
        documents = db.query(Document).filter(
            Document.financial_details.isnot(None),
            Document.is_deleted == False
        ).limit(limit).all()

        incomplete_docs = []
        needs_review_docs = []

        for doc in documents:
            if not doc.financial_details:
                continue

            metadata = doc.financial_details.get("extraction_metadata", {})
            status = metadata.get("validation_status")
            missing = metadata.get("missing_critical_information", [])
            flags = metadata.get("data_quality_flags", [])

            if status == "incomplete" and missing:
                incomplete_docs.append({
                    "document_id": doc.id,
                    "filename": doc.file_name,
                    "missing_info": missing,
                    "uploaded_at": doc.upload_date.isoformat() if doc.upload_date else None
                })

            if status == "needs_review" and flags:
                needs_review_docs.append({
                    "document_id": doc.id,
                    "filename": doc.file_name,
                    "quality_flags": flags,
                    "uploaded_at": doc.upload_date.isoformat() if doc.upload_date else None
                })

        return {
            "total_documents_checked": len(documents),
            "incomplete_documents": incomplete_docs,
            "incomplete_count": len(incomplete_docs),
            "needs_review_documents": needs_review_docs,
            "needs_review_count": len(needs_review_docs),
            "complete_count": len(documents) - len(incomplete_docs) - len(needs_review_docs)
        }

    except Exception as e:
        logger.error(f"Error getting missing info batch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get missing info batch: {str(e)}"
        )


def _find_precedent(precedents: List[Dict], *search_terms: str) -> Dict[str, Any]:
    """
    Find a specific precedent by search terms

    Returns full precedent details if found, or None
    """
    for precedent in precedents:
        citation = str(precedent.get("citation", ""))
        if all(term in citation for term in search_terms):
            return precedent

    return None
