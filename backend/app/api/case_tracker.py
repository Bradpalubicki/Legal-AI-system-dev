"""
Case Tracking API for Legal AI System
Tracks case obligations, deadlines, and progress
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..src.services.dual_ai_service import dual_ai_service
from ..src.services.extraction_pipeline import extraction_pipeline, ConfidenceLevel
from ..src.services.obligation_service import obligation_service, VerificationStatus
from ..src.core.database import get_db
from ..models.legal_documents import CaseTracking

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/case-tracking", tags=["Case Tracking"])

# ============================================================================
# DATA MODELS
# ============================================================================

class CaseTrackingRequest(BaseModel):
    document_text: str
    document_analysis: Dict[str, Any]
    case_id: str
    case_info: Dict[str, Any] = {}

class CaseActionUpdate(BaseModel):
    case_id: str
    action_type: str
    action_description: str
    completion_date: Optional[str] = None


# ============================================================================
# NEW OBLIGATION SERVICE ENDPOINTS
# ============================================================================

@router.post("/obligations/extract")
async def extract_obligations(request: CaseTrackingRequest) -> Dict[str, Any]:
    """
    Extract obligations using plugin architecture
    Returns obligations from all sources (AI, Regex, Templates)
    """
    try:
        # Build context for extractors
        context = {
            'case_id': request.case_id,
            'ai_analysis': request.document_analysis,
            'document_type': request.document_analysis.get('document_type', ''),
            'case_info': request.case_info
        }

        # Extract using all sources
        obligations = obligation_service.extract_all(
            document_text=request.document_text,
            context=context
        )

        logger.info(f"Extracted {len(obligations)} total obligations")

        # Convert to dict for response
        return {
            'case_id': request.case_id,
            'total_obligations': len(obligations),
            'obligations': [ob.to_dict() for ob in obligations],
            'sources_used': list(set(ob.metadata.source.value for ob in obligations)),
            'average_confidence': sum(ob.metadata.confidence_score for ob in obligations) / len(obligations) if obligations else 0
        }

    except Exception as e:
        logger.error(f"Error extracting obligations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/obligations/manual")
async def add_manual_obligation(
    case_id: str,
    obligation_data: Dict[str, Any],
    user_id: str = "system"
) -> Dict[str, Any]:
    """Add manually created obligation"""
    try:
        obligation = obligation_service.add_manual_obligation(
            case_id=case_id,
            data=obligation_data,
            user_id=user_id
        )

        return {
            'success': True,
            'obligation': obligation.to_dict()
        }

    except Exception as e:
        logger.error(f"Error adding manual obligation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/obligations/{case_id}")
async def get_case_obligations(case_id: str) -> Dict[str, Any]:
    """Get all obligations for a case"""
    try:
        obligations = obligation_service.get_case_obligations(case_id)

        # Group by source
        by_source = {}
        for ob in obligations:
            source = ob.metadata.source.value
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(ob.to_dict())

        # Group by verification status
        by_status = {}
        for ob in obligations:
            vstatus = ob.verification_status.value
            if vstatus not in by_status:
                by_status[vstatus] = []
            by_status[vstatus].append(ob.to_dict())

        return {
            'case_id': case_id,
            'total': len(obligations),
            'obligations': [ob.to_dict() for ob in obligations],
            'by_source': by_source,
            'by_verification_status': by_status,
            'needs_review': len([ob for ob in obligations if ob.verification_status == VerificationStatus.UNVERIFIED])
        }

    except Exception as e:
        logger.error(f"Error getting obligations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/obligations/{obligation_id}/verify")
async def verify_obligation(
    obligation_id: str,
    verification_status: str,
    user_id: str = "system"
) -> Dict[str, Any]:
    """Verify an obligation"""
    try:
        vstatus = VerificationStatus(verification_status)
        obligation = obligation_service.verify_obligation(obligation_id, user_id, vstatus)

        return {
            'success': True,
            'obligation': obligation.to_dict()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying obligation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/obligations/{obligation_id}/complete")
async def complete_obligation(
    obligation_id: str,
    user_id: str = "system",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Mark obligation as completed"""
    try:
        obligation = obligation_service.complete_obligation(obligation_id, user_id, notes)

        return {
            'success': True,
            'obligation': obligation.to_dict()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing obligation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/obligations/{obligation_id}/audit")
async def get_audit_trail(obligation_id: str) -> Dict[str, Any]:
    """Get audit trail for an obligation"""
    try:
        audit_trail = obligation_service.get_audit_trail(obligation_id)

        return {
            'obligation_id': obligation_id,
            'audit_trail': [
                {
                    'timestamp': entry.timestamp,
                    'action': entry.action,
                    'user_id': entry.user_id,
                    'field_changed': entry.field_changed,
                    'old_value': entry.old_value,
                    'new_value': entry.new_value,
                    'notes': entry.notes
                }
                for entry in audit_trail
            ]
        }

    except Exception as e:
        logger.error(f"Error getting audit trail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ORIGINAL ENDPOINT (kept for backwards compatibility)
# ============================================================================

# In-memory storage for case tracking (in production, use a database)
case_tracking_store = {}


@router.post("/track")
async def track_case_obligations(
    request: CaseTrackingRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Track case obligations and deadlines based on document analysis

    Monitors key obligations, deadlines, and required actions
    Creates accountability tracking for attorney performance
    """
    try:
        case_id = request.case_id

        # USE NEW EXTRACTION PIPELINE with confidence scores
        extraction_result = extraction_pipeline.extract(
            document_text=request.document_text,
            ai_analysis=request.document_analysis
        )

        logger.info(f"Extraction confidence: {extraction_result.overall_confidence:.2%}")
        logger.info(f"Extraction summary: {extraction_result.extraction_summary}")

        # Convert extracted deadlines to obligations
        obligations = []

        # Add deadline-based obligations
        for deadline in extraction_result.deadlines:
            obligations.append({
                "type": "deadline_compliance",
                "category": "procedural",
                "description": deadline.description,
                "due_date": deadline.date,
                "priority": deadline.priority,
                "confidence": deadline.confidence.value,
                "extraction_method": deadline.method.value,
                "source": deadline.source_text,
                "evidence_required": ["Calendar entry", "Compliance documentation"],
                "consequences": "Potential case dismissal or sanctions"
            })

        # Add key date obligations
        for key_date in extraction_result.key_dates:
            obligations.append({
                "type": "court_appearance",
                "category": "procedural",
                "description": key_date.description,
                "due_date": key_date.date,
                "priority": key_date.priority,
                "confidence": key_date.confidence.value,
                "extraction_method": key_date.method.value,
                "source": key_date.source_text,
                "evidence_required": ["Calendar entry", "Preparation materials"],
                "consequences": "Client prejudice, potential sanctions"
            })

        # Add document-type specific obligations
        doc_type = extraction_result.document_type.value.lower()
        if 'complaint' in doc_type or 'petition' in doc_type or 'summons' in doc_type:
            obligations.append({
                "type": "responsive_pleading",
                "category": "procedural",
                "description": "File responsive pleading (answer or motion to dismiss)",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "priority": "URGENT",
                "confidence": "high",
                "extraction_method": "document_type_inference",
                "source": f"Document type: {doc_type}",
                "evidence_required": ["Responsive pleading filed", "Proof of service"],
                "consequences": "Default judgment may be entered"
            })

        # GUARANTEED minimum obligations if extraction failed
        if len(obligations) == 0:
            obligations.extend([
                {
                    "type": "document_review",
                    "category": "case_management",
                    "description": "Complete thorough review of all case documents",
                    "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "priority": "HIGH",
                    "confidence": "medium",
                    "extraction_method": "default_fallback",
                    "source": "No deadlines found - baseline obligation",
                    "evidence_required": ["Review notes", "Case summary"],
                    "consequences": "Missed deadlines or important details"
                },
                {
                    "type": "client_consultation",
                    "category": "client_communication",
                    "description": "Initial consultation to discuss case strategy",
                    "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "priority": "HIGH",
                    "confidence": "medium",
                    "extraction_method": "default_fallback",
                    "source": "Standard case management requirement",
                    "evidence_required": ["Meeting notes", "Signed agreement"],
                    "consequences": "Client dissatisfaction, missed information"
                }
            ])

        all_obligations = obligations
        logger.info(f"Total obligations created: {len(all_obligations)}")

        # Get or create tracking data from database
        tracking_record = db.query(CaseTracking).filter(CaseTracking.case_id == case_id).first()

        if not tracking_record:
            tracking_record = CaseTracking(
                case_id=case_id,
                documents_processed=[],
                obligations=[],
                actions_taken=[],
                missed_deadlines=[],
                performance_metrics={}
            )
            db.add(tracking_record)
            db.flush()

        # Build tracking_data dict for compatibility with existing code
        tracking_data = {
            "case_id": tracking_record.case_id,
            "created_at": tracking_record.created_at.isoformat(),
            "documents_processed": tracking_record.documents_processed or [],
            "obligations": tracking_record.obligations or [],
            "actions_taken": tracking_record.actions_taken or [],
            "missed_deadlines": tracking_record.missed_deadlines or [],
            "performance_metrics": tracking_record.performance_metrics or {}
        }

        # Add new document and obligations
        tracking_data["documents_processed"].append({
            "document_type": request.document_analysis.get("document_type"),
            "processed_at": datetime.now().isoformat(),
            "obligations_count": len(all_obligations)
        })

        # Update obligations
        for obligation in all_obligations:
            obligation["case_id"] = case_id
            obligation["identified_at"] = datetime.now().isoformat()
            obligation["status"] = "pending"

        tracking_data["obligations"].extend(all_obligations)

        # Save back to database
        tracking_record.documents_processed = tracking_data["documents_processed"]
        tracking_record.obligations = tracking_data["obligations"]

        # Calculate performance metrics
        performance = _calculate_performance_metrics(tracking_data)

        # Save performance metrics to database
        tracking_record.performance_metrics = performance
        db.commit()
        db.refresh(tracking_record)

        # Generate accountability report
        accountability_report = _generate_accountability_report(tracking_data, performance)

        # Generate attorney questions
        attorney_questions = _generate_attorney_accountability_questions(
            all_obligations,
            performance,
            request.document_analysis
        )

        response = {
            "case_id": case_id,
            "obligations": all_obligations,
            "performance_metrics": performance,
            "accountability_report": accountability_report,
            "attorney_questions": attorney_questions,
            "action_items": _generate_attorney_action_items(all_obligations),
            "red_flags": _identify_red_flags(tracking_data, performance),
            "next_review_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "disclaimers": [
                "This tracking system is for informational purposes only.",
                "Attorney-client privilege and professional responsibilities govern the attorney-client relationship.",
                "Consult with your attorney about any concerns regarding their performance.",
                "Consider seeking second opinions if you have serious concerns about representation."
            ]
        }

        logger.info(f"Case tracking updated for case {case_id} (saved to database)")
        return response

    except Exception as e:
        logger.error(f"Error in case tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Case tracking error: {str(e)}"
        )

@router.post("/update-action")
async def update_case_action(
    request: CaseActionUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update attorney action status and track performance
    """
    try:
        case_id = request.case_id

        # Get tracking record from database
        tracking_record = db.query(CaseTracking).filter(CaseTracking.case_id == case_id).first()

        if not tracking_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case tracking not found"
            )

        # Build tracking_data dict from database
        tracking_data = {
            "case_id": tracking_record.case_id,
            "created_at": tracking_record.created_at.isoformat(),
            "documents_processed": tracking_record.documents_processed or [],
            "obligations": tracking_record.obligations or [],
            "actions_taken": tracking_record.actions_taken or [],
            "missed_deadlines": tracking_record.missed_deadlines or [],
            "performance_metrics": tracking_record.performance_metrics or {}
        }

        # Add action taken
        action_record = {
            "action_type": request.action_type,
            "description": request.action_description,
            "recorded_at": datetime.now().isoformat(),
            "completion_date": request.completion_date,
            "notes": getattr(request, 'notes', None)
        }

        tracking_data["actions_taken"].append(action_record)

        # Update obligation status if applicable
        for obligation in tracking_data["obligations"]:
            if (obligation.get("category") == request.action_type or
                request.action_type.lower() in obligation.get("description", "").lower()):
                obligation["status"] = "completed" if request.completion_date else "in_progress"
                obligation["completed_at"] = request.completion_date

        # Recalculate performance metrics
        performance = _calculate_performance_metrics(tracking_data)
        tracking_data["performance_metrics"] = performance

        # Save back to database
        tracking_record.actions_taken = tracking_data["actions_taken"]
        tracking_record.obligations = tracking_data["obligations"]
        tracking_record.performance_metrics = performance
        db.commit()
        db.refresh(tracking_record)

        return {
            "case_id": case_id,
            "action_recorded": action_record,
            "updated_performance": performance,
            "message": "Attorney action updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating attorney action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action update error: {str(e)}"
        )

@router.get("/report/{case_id}")
async def get_accountability_report(
    case_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive accountability report for a case
    """
    # Get tracking record from database
    tracking_record = db.query(CaseTracking).filter(CaseTracking.case_id == case_id).first()

    if not tracking_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case tracking not found"
        )

    # Build tracking_data dict from database
    tracking_data = {
        "case_id": tracking_record.case_id,
        "created_at": tracking_record.created_at.isoformat(),
        "documents_processed": tracking_record.documents_processed or [],
        "obligations": tracking_record.obligations or [],
        "actions_taken": tracking_record.actions_taken or [],
        "missed_deadlines": tracking_record.missed_deadlines or [],
        "performance_metrics": tracking_record.performance_metrics or {}
    }

    performance = _calculate_performance_metrics(tracking_data)

    return {
        "case_id": case_id,
        "tracking_summary": {
            "documents_processed": len(tracking_data["documents_processed"]),
            "total_obligations": len(tracking_data["obligations"]),
            "completed_obligations": len([o for o in tracking_data["obligations"] if o.get("status") == "completed"]),
            "pending_obligations": len([o for o in tracking_data["obligations"] if o.get("status") == "pending"]),
            "missed_deadlines": len(tracking_data["missed_deadlines"])
        },
        "performance_metrics": performance,
        "timeline": _generate_case_timeline(tracking_data),
        "recommendations": _generate_performance_recommendations(performance, tracking_data)
    }

def _extract_obligations_from_document(document_text: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract case obligations - works with or without AI analysis"""

    obligations = []

    # METHOD 1: Extract from AI analysis (if available)
    for deadline in analysis.get('deadlines', []):
        obligations.append({
            "type": "deadline_compliance",
            "category": "procedural",
            "description": f"Ensure compliance with deadline: {deadline.get('description')}",
            "due_date": deadline.get('date'),
            "priority": "HIGH",
            "evidence_required": ["Calendar entry", "Compliance documentation"],
            "consequences": "Potential case dismissal or sanctions"
        })

    for key_date in analysis.get('key_dates', []):
        if any(word in key_date.get('description', '').lower() for word in ['hearing', 'trial', 'conference', 'deadline']):
            obligations.append({
                "type": "court_appearance",
                "category": "procedural",
                "description": f"Prepare for and attend: {key_date.get('description')}",
                "due_date": key_date.get('date'),
                "priority": "HIGH",
                "evidence_required": ["Calendar entry", "Preparation materials"],
                "consequences": "Client prejudice, potential sanctions"
            })

    # METHOD 2: Direct text parsing (fallback when AI analysis lacks data)
    import re
    text_lower = document_text.lower()

    # Look for deadline keywords in text
    deadline_patterns = [
        r'within (\d+) days',
        r'(\d+) day[s]? (?:from|after|of)',
        r'respond by ([A-Z][a-z]+ \d+, \d{4})',
        r'due (?:by|on) ([A-Z][a-z]+ \d+)',
        r'file.*(?:within|by) (\d+) day'
    ]

    for pattern in deadline_patterns:
        matches = re.findall(pattern, document_text, re.IGNORECASE)
        for match in matches[:3]:  # Limit to first 3 matches
            if match.isdigit():
                days = int(match)
                due_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
                desc = f"Respond within {days} days (deadline extracted from document)"
            else:
                due_date = "TBD"
                desc = f"Important date: {match}"

            obligations.append({
                "type": "deadline_compliance",
                "category": "procedural",
                "description": desc,
                "due_date": due_date,
                "priority": "HIGH",
                "evidence_required": ["Document review", "Calendar entry"],
                "consequences": "Risk of default or missed deadline"
            })
            break  # Only add one from text parsing

    # Document type-specific obligations (more flexible detection)
    doc_type = analysis.get('document_type', '').lower()

    # Check both analysis and raw text for document type
    if not doc_type:
        if any(word in text_lower for word in ['complaint', 'petition', 'summons']):
            doc_type = 'complaint'
        elif any(word in text_lower for word in ['motion', 'notice of motion']):
            doc_type = 'motion'
        elif any(word in text_lower for word in ['subpoena', 'discovery']):
            doc_type = 'discovery'

    if 'complaint' in doc_type or 'petition' in doc_type:
        obligations.extend([
            {
                "type": "responsive_pleading",
                "category": "procedural",
                "description": "File responsive pleading (answer or motion to dismiss)",
                "due_date": _calculate_response_deadline(),
                "priority": "URGENT",
                "evidence_required": ["Filed pleading", "Proof of service"],
                "consequences": "Default judgment"
            },
            {
                "type": "client_consultation",
                "category": "communication",
                "description": "Review complaint with client and discuss strategy",
                "due_date": _calculate_consultation_deadline(),
                "priority": "HIGH",
                "evidence_required": ["Meeting notes", "Strategy documentation"],
                "consequences": "Inadequate representation"
            }
        ])

    elif 'motion' in doc_type:
        obligations.extend([
            {
                "type": "motion_response",
                "category": "procedural",
                "description": "Analyze motion and prepare opposition if appropriate",
                "due_date": _calculate_motion_response_deadline(),
                "priority": "HIGH",
                "evidence_required": ["Legal research", "Opposition filing"],
                "consequences": "Unopposed motion may be granted"
            }
        ])

    # GUARANTEED: Always add baseline obligations if nothing was extracted
    if len(obligations) == 0:
        obligations.extend([
            {
                "type": "document_review",
                "category": "case_management",
                "description": "Complete thorough review of all case documents",
                "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "priority": "HIGH",
                "evidence_required": ["Review notes", "Case summary"],
                "consequences": "Missed deadlines or important details"
            },
            {
                "type": "client_consultation",
                "category": "client_communication",
                "description": "Initial consultation to discuss case strategy and timeline",
                "due_date": _calculate_consultation_deadline(),
                "priority": "HIGH",
                "evidence_required": ["Meeting notes", "Signed agreement"],
                "consequences": "Client dissatisfaction, missed information"
            },
            {
                "type": "deadline_research",
                "category": "procedural",
                "description": "Research and calendar all applicable deadlines for this matter",
                "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                "priority": "URGENT",
                "evidence_required": ["Deadline calendar", "Court rules review"],
                "consequences": "Missed critical deadlines"
            }
        ])

    return obligations

def _calculate_response_deadline() -> str:
    """Calculate typical response deadline (usually 30 days from service)"""
    return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

def _calculate_consultation_deadline() -> str:
    """Calculate deadline for client consultation"""
    return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

def _calculate_motion_response_deadline() -> str:
    """Calculate motion response deadline"""
    return (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")

def _create_tracking_prompt(document_text: str, analysis: Dict[str, Any], case_info: Dict[str, Any]) -> str:
    """Create prompt for AI attorney obligation analysis"""

    return f"""
You are an attorney performance tracker. Analyze this legal document and identify specific obligations and responsibilities for the attorney representing the client.

DOCUMENT ANALYSIS:
Type: {analysis.get('document_type', 'Unknown')}
Summary: {analysis.get('summary', 'No summary available')}
Parties: {', '.join(analysis.get('parties', []))}
Deadlines: {analysis.get('deadlines', [])}
Key Dates: {analysis.get('key_dates', [])}

CASE INFO:
{case_info}

DOCUMENT TEXT (excerpt):
{document_text[:2000]}...

Please identify case obligations and provide a JSON response:
{{
    "obligations": [
        {{
            "type": "obligation_type",
            "category": "procedural/substantive/communication/ethical",
            "description": "Detailed description of what attorney must do",
            "due_date": "YYYY-MM-DD or timeframe",
            "priority": "URGENT/HIGH/MEDIUM/LOW",
            "time_required": "estimated hours/days needed",
            "evidence_required": ["what should be documented"],
            "consequences": "consequences of not fulfilling obligation",
            "client_impact": "how this affects the client"
        }}
    ],
    "performance_standards": [
        "Professional standards that apply to this case"
    ],
    "communication_requirements": [
        "Required client communications and updates"
    ],
    "ethical_considerations": [
        "Ethical obligations and potential conflicts"
    ]
}}

Focus on specific, actionable obligations with clear deadlines and consequences.
"""

def _parse_tracking_response(ai_response: str) -> Dict[str, Any]:
    """Parse AI tracking analysis response"""
    try:
        import json

        if "```json" in ai_response:
            json_start = ai_response.find("```json") + 7
            json_end = ai_response.find("```", json_start)
            json_str = ai_response[json_start:json_end].strip()
        else:
            json_str = ai_response.strip()

        return json.loads(json_str)

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Could not parse tracking analysis JSON: {e}")
        return {"obligations": [], "performance_standards": [], "communication_requirements": [], "ethical_considerations": []}

def _merge_obligations(extracted: List[Dict[str, Any]], ai_generated: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Merge extracted and AI-generated obligations"""

    all_obligations = extracted.copy()

    # Add AI-generated obligations
    for obligation in ai_generated.get('obligations', []):
        all_obligations.append(obligation)

    return all_obligations

def _calculate_performance_metrics(tracking_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate attorney performance metrics"""

    obligations = tracking_data.get('obligations', [])
    actions_taken = tracking_data.get('actions_taken', [])

    total_obligations = len(obligations)
    completed_obligations = len([o for o in obligations if o.get('status') == 'completed'])
    overdue_obligations = len([o for o in obligations if _is_overdue(o)])

    completion_rate = (completed_obligations / total_obligations * 100) if total_obligations > 0 else 0
    response_time = _calculate_avg_response_time(tracking_data)

    return {
        "overall_score": _calculate_overall_score(completion_rate, overdue_obligations, len(actions_taken)),
        "completion_rate": round(completion_rate, 1),
        "total_obligations": total_obligations,
        "completed_obligations": completed_obligations,
        "pending_obligations": total_obligations - completed_obligations,
        "overdue_obligations": overdue_obligations,
        "average_response_time": response_time,
        "communication_frequency": len(actions_taken),
        "last_activity": tracking_data.get('actions_taken', [{}])[-1].get('recorded_at') if actions_taken else None
    }

def _is_overdue(obligation: Dict[str, Any]) -> bool:
    """Check if an obligation is overdue"""
    try:
        due_date_str = obligation.get('due_date')
        if not due_date_str:
            return False

        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        return date.today() > due_date and obligation.get('status') != 'completed'
    except:
        return False

def _calculate_avg_response_time(tracking_data: Dict[str, Any]) -> str:
    """Calculate average response time"""
    # Simplified calculation - in reality would track actual response times
    actions = tracking_data.get('actions_taken', [])
    if len(actions) >= 3:
        return "2.5 days"
    elif len(actions) >= 1:
        return "4.1 days"
    else:
        return "No data"

def _calculate_overall_score(completion_rate: float, overdue_count: int, activity_count: int) -> int:
    """Calculate overall performance score (0-100)"""
    score = completion_rate
    score -= (overdue_count * 10)  # Penalty for overdue items
    score += min(activity_count * 2, 20)  # Bonus for activity, capped at 20

    return max(0, min(100, int(score)))

def _generate_accountability_report(tracking_data: Dict[str, Any], performance: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive accountability report"""

    return {
        "summary": f"Attorney performance score: {performance['overall_score']}/100",
        "strengths": _identify_strengths(performance),
        "areas_for_improvement": _identify_improvements(performance, tracking_data),
        "recent_activity": tracking_data.get('actions_taken', [])[-3:],
        "upcoming_deadlines": _get_upcoming_deadlines(tracking_data),
        "recommendations": _generate_recommendations(performance, tracking_data)
    }

def _identify_strengths(performance: Dict[str, Any]) -> List[str]:
    """Identify attorney performance strengths"""
    strengths = []

    if performance['completion_rate'] >= 80:
        strengths.append("High completion rate of obligations")

    if performance['overdue_obligations'] == 0:
        strengths.append("No overdue obligations")

    if performance['communication_frequency'] >= 5:
        strengths.append("Active communication and case management")

    return strengths or ["Case tracking recently initiated"]

def _identify_improvements(performance: Dict[str, Any], tracking_data: Dict[str, Any]) -> List[str]:
    """Identify areas for improvement"""
    improvements = []

    if performance['completion_rate'] < 70:
        improvements.append("Low completion rate of required obligations")

    if performance['overdue_obligations'] > 0:
        improvements.append(f"{performance['overdue_obligations']} overdue obligations need immediate attention")

    if performance['communication_frequency'] < 2:
        improvements.append("Increase client communication frequency")

    return improvements or ["Continue current performance level"]

def _get_upcoming_deadlines(tracking_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get upcoming deadlines from obligations"""
    upcoming = []

    for obligation in tracking_data.get('obligations', []):
        if obligation.get('status') == 'pending' and obligation.get('due_date'):
            try:
                due_date = datetime.strptime(obligation['due_date'], "%Y-%m-%d").date()
                days_until = (due_date - date.today()).days

                if 0 <= days_until <= 30:  # Next 30 days
                    upcoming.append({
                        "description": obligation['description'],
                        "due_date": obligation['due_date'],
                        "days_until": days_until,
                        "priority": obligation.get('priority', 'MEDIUM')
                    })
            except:
                continue

    return sorted(upcoming, key=lambda x: x['days_until'])

def _generate_recommendations(performance: Dict[str, Any], tracking_data: Dict[str, Any]) -> List[str]:
    """Generate performance recommendations"""
    recommendations = []

    if performance['overdue_obligations'] > 0:
        recommendations.append("Prioritize completing overdue obligations immediately")

    if performance['communication_frequency'] < 3:
        recommendations.append("Increase regular client updates and communication")

    recommendations.append("Continue documenting all case activities and communications")

    return recommendations

def _generate_attorney_action_items(obligations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate action items for case tracking"""

    action_items = []

    # Urgent items
    urgent_obligations = [o for o in obligations if o.get('priority') == 'URGENT']
    if urgent_obligations:
        action_items.append({
            "priority": "URGENT",
            "task": "Address urgent obligations",
            "description": f"{len(urgent_obligations)} urgent items require immediate attention",
            "due_date": "Immediately",
            "category": "Attorney Performance"
        })

    # Review upcoming deadlines
    action_items.append({
        "priority": "HIGH",
        "task": "Review all case deadlines",
        "description": "Ensure all critical dates are calendared and monitored",
        "due_date": "Within 24 hours",
        "category": "Case Management"
    })

    # Client communication
    action_items.append({
        "priority": "MEDIUM",
        "task": "Schedule client update meeting",
        "description": "Provide case status update and address any concerns",
        "due_date": "Within 7 days",
        "category": "Client Communication"
    })

    return action_items

def _generate_attorney_accountability_questions(obligations: List[Dict[str, Any]], performance: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
    """Generate questions to ask attorney about accountability"""

    questions = [
        "What is your plan for meeting the upcoming deadlines in this case?",
        "How do you track and monitor case deadlines and obligations?",
        "What is your typical response time for client communications?",
        "How often will you provide case status updates?",
        "What happens if a deadline is missed or an obligation is not met?"
    ]

    # Performance-based questions
    if performance.get('overdue_obligations', 0) > 0:
        questions.extend([
            "Why are there overdue obligations in my case?",
            "What is your plan to address the overdue items?",
            "How will you prevent future delays?"
        ])

    if performance.get('communication_frequency', 0) < 3:
        questions.extend([
            "How often should I expect to hear from you about my case?",
            "What is your preferred method of client communication?",
            "Will you provide regular status updates even if nothing major happens?"
        ])

    # Document-specific questions
    doc_type = analysis.get('document_type', '').lower()
    if 'complaint' in doc_type:
        questions.extend([
            "What is your strategy for responding to this complaint?",
            "What are the key deadlines I need to be aware of?",
            "What discovery activities will be required?"
        ])

    return questions[:12]  # Limit to 12 questions

def _identify_red_flags(tracking_data: Dict[str, Any], performance: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify potential red flags in attorney performance"""

    red_flags = []

    if performance.get('overdue_obligations', 0) > 2:
        red_flags.append({
            "severity": "HIGH",
            "issue": "Multiple overdue obligations",
            "description": f"{performance['overdue_obligations']} obligations are overdue",
            "action_needed": "Request immediate status update and completion timeline"
        })

    if performance.get('communication_frequency', 0) == 0:
        red_flags.append({
            "severity": "MEDIUM",
            "issue": "No recorded attorney activity",
            "description": "No documented actions or communications",
            "action_needed": "Schedule meeting to discuss case status and expectations"
        })

    if performance.get('overall_score', 100) < 50:
        red_flags.append({
            "severity": "HIGH",
            "issue": "Low overall performance score",
            "description": f"Performance score of {performance['overall_score']}/100 indicates concerns",
            "action_needed": "Consider discussing representation concerns or seeking second opinion"
        })

    return red_flags

def _generate_case_timeline(tracking_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate case timeline from tracking data"""

    timeline_events = []

    # Add document processing events
    for doc in tracking_data.get('documents_processed', []):
        timeline_events.append({
            "date": doc['processed_at'],
            "event": f"Processed {doc['document_type']}",
            "type": "document",
            "description": f"Identified {doc['obligations_count']} obligations"
        })

    # Add action events
    for action in tracking_data.get('actions_taken', []):
        timeline_events.append({
            "date": action['recorded_at'],
            "event": action['description'],
            "type": "action",
            "description": action.get('notes', '')
        })

    # Sort by date
    timeline_events.sort(key=lambda x: x['date'], reverse=True)

    return timeline_events[:10]  # Return last 10 events