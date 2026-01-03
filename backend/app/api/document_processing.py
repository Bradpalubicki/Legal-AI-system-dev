"""
Document Processing API for Legal AI System
Real AI-powered document analysis using OpenAI
"""
# Force reload v4 - thread-based background analysis

import logging
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Body, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import threading

# Thread pool for running background analysis tasks
_analysis_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="analysis_")

from ..src.services.dual_ai_service import dual_ai_service
from ..src.services.pdf_service import pdf_service
from ..src.services.multi_layer_analyzer import multi_layer_analyzer
from ..src.services.analysis_progress_tracker import progress_tracker, AnalysisStage
from ..src.core.database import get_db, SessionLocal
from ..models.legal_documents import Document
from ..api.deps.auth import get_current_user, CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Document Processing"])

# ============================================================
# ANALYSIS RESULTS STORAGE (for async analysis)
# ============================================================
# Thread-safe storage for completed analysis results
_analysis_results: Dict[str, Dict[str, Any]] = {}
_results_lock = threading.Lock()

def store_analysis_result(job_id: str, result: Dict[str, Any]):
    """Store completed analysis result for retrieval"""
    with _results_lock:
        _analysis_results[job_id] = {
            "result": result,
            "stored_at": datetime.now()
        }

def get_analysis_result(job_id: str) -> Dict[str, Any]:
    """Get stored analysis result"""
    with _results_lock:
        return _analysis_results.get(job_id, {}).get("result")

def cleanup_old_results(max_age_seconds: int = 3600):
    """Remove results older than max_age_seconds"""
    with _results_lock:
        now = datetime.now()
        expired = [
            jid for jid, data in _analysis_results.items()
            if (now - data["stored_at"]).total_seconds() > max_age_seconds
        ]
        for jid in expired:
            del _analysis_results[jid]


# Generic phrases that should be replaced with specific text
GENERIC_PHRASES = [
    "this date is significant",
    "significant to the proceedings",
    "this is important",
    "this matters for the case",
    "important deadline",
    "critical deadline",
    "serious legal consequences",
    "serious consequences",
    "adverse consequences",
    "could have consequences",
    "missing this deadline could result in adverse consequences",
    "failure to meet this deadline could have serious legal consequences",
    "this is a critical deadline that requires action",
]

# Specific risk text based on deadline type keywords
DEADLINE_RISK_MAP = {
    "response": (
        "Failure to file a response by this date may result in waiving the right to oppose. "
        "The court could rule on the matter without your input, potentially resulting in an adverse ruling."
    ),
    "answer": (
        "If no answer is filed by this date, the court may enter a default judgment against you. "
        "This means the opposing party could win automatically without a trial."
    ),
    "reply": (
        "Missing this deadline waives the right to file a reply brief. "
        "Your initial arguments will stand without the opportunity to address opposing arguments."
    ),
    "hearing": (
        "Failure to appear at this hearing may result in: (1) the court ruling in your absence, "
        "(2) sanctions for non-appearance, or (3) dismissal of your claims or defenses."
    ),
    "discovery": (
        "Discovery not completed by this deadline may be excluded from the case. "
        "This could prevent you from presenting key evidence at trial."
    ),
    "appeal": (
        "This is an appeal deadline - it is JURISDICTIONAL. Missing it permanently waives "
        "all appeal rights. The lower court decision becomes final and unappealable."
    ),
    "claim": (
        "Claims not filed by the bar date will be disallowed entirely. "
        "You will lose all rights to recover on this claim in the bankruptcy."
    ),
    "objection": (
        "Failure to file an objection by this deadline constitutes waiver. "
        "The matter will proceed as if you have no objection."
    ),
    "motion": (
        "If this motion deadline is missed, you may lose the ability to seek this relief. "
        "Some motions have strict timing requirements that cannot be extended."
    ),
    "disclosure": (
        "Failure to make required disclosures by this date may result in exclusion of witnesses "
        "or evidence, sanctions, or adverse inference instructions to the jury."
    ),
    "trial": (
        "Trial dates are generally firm. Failure to be prepared or appear may result in "
        "dismissal, default judgment, or sanctions."
    ),
    "briefing": (
        "Missing a briefing deadline may result in the court deciding the issue without "
        "your input or striking your previously filed documents."
    ),
    "settlement": (
        "Settlement deadlines are typically set by court order. Missing this date may affect "
        "your settlement options and the court's willingness to grant extensions."
    ),
}


def get_specific_risk_text(deadline_type: str, description: str, existing_risk: str) -> str:
    """
    Replace generic risk text with specific risk based on deadline type.

    Args:
        deadline_type: Type of deadline (e.g., "response", "motion", "hearing")
        description: Description of the deadline
        existing_risk: Existing risk text to check if generic

    Returns:
        Specific risk text
    """
    # Check if existing risk is generic
    if existing_risk:
        existing_lower = existing_risk.lower()
        is_generic = any(phrase in existing_lower for phrase in GENERIC_PHRASES)
        if not is_generic:
            return existing_risk  # Keep the existing specific risk

    # Combine deadline_type and description for keyword matching
    search_text = f"{deadline_type} {description}".lower()

    # Find matching risk text
    for keyword, risk_text in DEADLINE_RISK_MAP.items():
        if keyword in search_text:
            return risk_text

    # Default fallback - still more specific than generic
    return (
        "This deadline requires timely action. Failure to comply may result in "
        "procedural consequences that could affect your case. Review the specific "
        "requirements and consult with your attorney."
    )


def get_specific_significance(date_type: str, description: str, existing_sig: str) -> str:
    """
    Replace generic significance text with specific text.

    Args:
        date_type: Type of date (e.g., "deadline", "hearing", "filing")
        description: Description of the date
        existing_sig: Existing significance to check if generic

    Returns:
        Specific significance text
    """
    # Check if existing significance is generic
    if existing_sig:
        existing_lower = existing_sig.lower()
        is_generic = any(phrase in existing_lower for phrase in GENERIC_PHRASES)
        if not is_generic:
            return existing_sig  # Keep the existing specific significance

    # Generate significance based on type and description
    search_text = f"{date_type} {description}".lower()

    if "hearing" in search_text:
        return f"Court hearing date - {description}. You must be prepared to appear or have representation."
    elif "deadline" in search_text or "due" in search_text:
        return f"Filing deadline - {description}. Documents must be submitted to the court by this date."
    elif "trial" in search_text:
        return f"Trial date - {description}. This is when your case will be heard before the court."
    elif "conference" in search_text:
        return f"Conference date - {description}. A meeting with the court to discuss case progress."
    elif "response" in search_text or "answer" in search_text:
        return f"Response deadline - {description}. A written response must be filed by this date."
    elif "motion" in search_text:
        return f"Motion deadline - {description}. The deadline to file or respond to this motion."
    else:
        return f"{description}" if description else "See document for details about this date."


def deduplicate_dates(dates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate dates by date value, merging information from duplicates.

    If same date appears multiple times with different events,
    combine them into a single entry with the most complete information.
    """
    if not dates or not isinstance(dates, list):
        return []

    date_map = {}

    for date_obj in dates:
        if not isinstance(date_obj, dict):
            continue

        # Get the date key (try multiple possible field names)
        date_key = date_obj.get("date") or date_obj.get("deadline") or date_obj.get("event_date")
        if not date_key:
            continue

        # Normalize date key for comparison
        date_key_normalized = str(date_key).strip().lower()

        if date_key_normalized in date_map:
            # Merge with existing entry
            existing = date_map[date_key_normalized]

            # Combine descriptions/events if different
            existing_event = existing.get("event", "") or existing.get("description", "")
            new_event = date_obj.get("event", "") or date_obj.get("description", "")
            if new_event and new_event not in existing_event:
                combined_event = f"{existing_event}; {new_event}".strip("; ")
                existing["event"] = combined_event
                existing["description"] = combined_event

            # Combine significance if different
            existing_sig = existing.get("significance", "") or existing.get("why_important", "")
            new_sig = date_obj.get("significance", "") or date_obj.get("why_important", "")
            if new_sig and new_sig not in existing_sig:
                existing["significance"] = f"{existing_sig} Additionally: {new_sig}".strip()
                existing["why_important"] = existing["significance"]

            # Keep highest urgency
            urgency_order = {"low": 1, "medium": 2, "normal": 2, "high": 3, "critical": 4, "urgent": 4}
            existing_urg = urgency_order.get(str(existing.get("urgency", "medium")).lower(), 2)
            new_urg = urgency_order.get(str(date_obj.get("urgency", "medium")).lower(), 2)
            if new_urg > existing_urg:
                existing["urgency"] = date_obj.get("urgency")

            # Mark as deadline if either entry is a deadline
            if date_obj.get("is_deadline"):
                existing["is_deadline"] = True

            # Keep the most specific consequence
            if date_obj.get("consequence_if_missed") and not existing.get("consequence_if_missed"):
                existing["consequence_if_missed"] = date_obj.get("consequence_if_missed")

            # Merge action_required
            if date_obj.get("action_required") and not existing.get("action_required"):
                existing["action_required"] = date_obj.get("action_required")

        else:
            # New entry
            date_map[date_key_normalized] = date_obj.copy()
            # Ensure we keep the original date key format
            date_map[date_key_normalized]["date"] = date_key

    # Convert back to list and sort by date
    result = list(date_map.values())

    # Try to sort by date if possible
    def parse_date_for_sort(d):
        date_str = d.get("date", "")
        try:
            # Try common formats
            from datetime import datetime as dt
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%d %B %Y", "%m-%d-%Y"]:
                try:
                    return dt.strptime(str(date_str), fmt)
                except ValueError:
                    continue
            return dt.max  # Unknown dates go to end
        except:
            return dt.max

    try:
        result.sort(key=parse_date_for_sort)
    except:
        pass  # Keep original order if sorting fails

    return result


def generate_plain_english_summary(analysis: Dict[str, Any]) -> str:
    """
    Generate a plain English summary of the document analysis.
    This creates a user-friendly explanation without legal jargon.

    The summary follows the structure:
    - What's Happening (The Big Picture)
    - What This Means For You
    - What You Need To Do
    - Key Points
    """
    document_type = analysis.get("document_type", "legal document")
    summary = analysis.get("summary", "")
    parties = analysis.get("parties", [])
    deadlines = analysis.get("deadlines", [])
    key_arguments = analysis.get("key_arguments", [])

    # Document type translations for plain English
    DOC_TYPE_EXPLANATIONS = {
        "complaint": "a formal lawsuit being filed against someone",
        "answer": "a formal response to a lawsuit",
        "motion to dismiss": "a request to throw out all or part of a case",
        "motion for summary judgment": "a request to win without a trial because the facts are clear",
        "order": "an official decision or instruction from the court",
        "petition": "a formal request filed with the court",
        "voluntary petition": "a filing to start a bankruptcy case",
        "notice": "an official notification about something happening in your case",
        "default judgment": "an automatic decision against someone who didn't respond",
        "summons": "a notice that you're being sued and must respond",
        "subpoena": "a legal order to appear in court or provide documents",
        "brief": "a written argument explaining one side's legal position",
        "declaration": "a written statement made under oath",
        "deposition": "a recorded interview under oath as part of gathering evidence",
    }

    # Get plain English doc type
    doc_type_lower = document_type.lower()
    doc_type_plain = DOC_TYPE_EXPLANATIONS.get(doc_type_lower, f"a {document_type}")

    for key, value in DOC_TYPE_EXPLANATIONS.items():
        if key in doc_type_lower:
            doc_type_plain = value
            break

    # Build the plain English summary
    sections = []

    # 1. What's Happening (The Big Picture)
    big_picture = f"**What's Happening (The Big Picture)**\n\n"
    big_picture += f"This document is {doc_type_plain}. "

    if parties:
        # Format parties for plain English
        party_names = []
        for p in parties[:3]:  # Limit to first 3
            if isinstance(p, str):
                name = p.split('(')[0].strip() if '(' in p else p
                party_names.append(name)
            elif isinstance(p, dict):
                party_names.append(p.get("name", str(p)))
        if party_names:
            big_picture += f"It involves {', '.join(party_names[:2])}"
            if len(party_names) > 2:
                big_picture += f" and others"
            big_picture += ". "

    if summary:
        # Use first 2 sentences of summary, cleaned up
        sentences = [s.strip() for s in summary.split('.') if s.strip()][:2]
        if sentences:
            big_picture += ' '.join(sentences) + ". "

    sections.append(big_picture.strip())

    # 2. What This Means For You
    meaning = "\n\n**What This Means For You**\n\n"
    if "complaint" in doc_type_lower or "summons" in doc_type_lower:
        meaning += "You are being notified of a legal action. This is a serious matter that requires your attention. "
        meaning += "Ignoring this could result in a default judgment (an automatic decision) against you."
    elif "motion" in doc_type_lower:
        meaning += "Someone is asking the court to make a decision about something in your case. "
        meaning += "You may need to respond or the court will decide based only on what the other side says."
    elif "order" in doc_type_lower or "judgment" in doc_type_lower:
        meaning += "The court has made a decision. This may require you to take specific actions. "
        meaning += "Court orders must be followed."
    elif "petition" in doc_type_lower and "bankruptcy" in doc_type_lower:
        meaning += "A bankruptcy case has been filed. This affects how debts can be collected and may change payment obligations."
    elif "notice" in doc_type_lower:
        meaning += "You're being officially informed about something happening in the case. "
        meaning += "Read carefully to understand what's changing or what's required."
    else:
        meaning += "This document is part of the legal proceedings. Review it carefully to understand how it affects you."

    sections.append(meaning.strip())

    # 3. What You Need To Do
    actions = "\n\n**What You Need To Do**\n\n"
    if deadlines:
        actions += "**Important Deadlines:**\n"
        for i, deadline in enumerate(deadlines[:3], 1):  # Limit to 3 deadlines
            if isinstance(deadline, dict):
                date = deadline.get("date", deadline.get("deadline", "Unknown date"))
                event = deadline.get("event", deadline.get("description", "Action required"))
                actions += f"{i}. **{date}**: {event}\n"
        actions += "\n"
    else:
        actions += "No specific deadlines were identified in this document, but you should:\n"

    actions += """
1. Read the entire document carefully
2. Note any dates, deadlines, or required actions
3. Consider consulting with an attorney if you're unsure what to do
4. Keep this document in a safe place for your records
"""
    sections.append(actions.strip())

    # 4. Key Points To Understand
    key_points = "\n\n**Key Points To Understand**\n\n"
    if key_arguments and isinstance(key_arguments, list):
        for arg in key_arguments[:3]:  # Limit to 3 points
            if isinstance(arg, str):
                key_points += f"• {arg}\n"
            elif isinstance(arg, dict):
                argument = arg.get("argument", arg.get("description", ""))
                if argument:
                    key_points += f"• {argument}\n"
    else:
        key_points += f"• This is {doc_type_plain}\n"
        if parties:
            key_points += "• Multiple parties are involved in this matter\n"
        if deadlines:
            key_points += "• There are important deadlines to be aware of\n"
        key_points += "• You should keep copies of all related documents\n"

    sections.append(key_points.strip())

    # 5. Reminder
    reminder = "\n\n---\n\n*Remember: This summary is for informational purposes only and does not constitute legal advice. For specific legal questions about your situation, please consult with a licensed attorney.*"
    sections.append(reminder)

    return ''.join(sections)


class AnalyzeTextRequest(BaseModel):
    text: str
    filename: str = "unknown.txt"
    session_id: str = None  # Frontend session ID
    document_id: str = None  # Optional: update existing document
    include_operational_details: bool = True  # Extract action items, obligations, etc.
    include_financial_details: bool = True  # Extract detailed financial information
    use_multi_layer_analysis: bool = True  # Enable comprehensive 4-layer verification for accuracy
    # Analysis modes:
    # - use_multi_layer_analysis=False: Fast single-model (Claude or GPT-4) - ~10-15 seconds
    # - use_multi_layer_analysis=True, thorough_analysis=False: Quick multi-layer - ~20-30 seconds
    # - use_multi_layer_analysis=True, thorough_analysis=True: Full pipeline with inspections - ~45-60 seconds
    thorough_analysis: bool = True  # Full pipeline for maximum accuracy (~3-5min)


# ============================================================
# ANALYSIS PROGRESS TRACKING ENDPOINTS
# ============================================================

@router.get("/ai-health-check")
async def ai_health_check() -> Dict[str, Any]:
    """
    Test AI client connections and model availability.
    Call this to diagnose why document analysis might be failing.
    """
    import os
    results = {
        "timestamp": datetime.now().isoformat(),
        "anthropic": {"status": "not_tested"},
        "openai": {"status": "not_tested"}
    }

    # Test Anthropic/Claude
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_key:
        results["anthropic"] = {"status": "error", "error": "ANTHROPIC_API_KEY not set"}
    else:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            # Try a simple message with the model we use
            model_id = "claude-opus-4-20250514"
            response = client.messages.create(
                model=model_id,
                max_tokens=100,
                messages=[{"role": "user", "content": "Say 'OK' if you can read this."}]
            )
            response_text = response.content[0].text if response.content else ""
            results["anthropic"] = {
                "status": "ok",
                "model": model_id,
                "response": response_text[:100],
                "usage": {"input": response.usage.input_tokens, "output": response.usage.output_tokens}
            }
        except Exception as e:
            results["anthropic"] = {
                "status": "error",
                "model": "claude-opus-4-20250514",
                "error_type": type(e).__name__,
                "error": str(e)[:500]
            }

    # Test OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        results["openai"] = {"status": "error", "error": "OPENAI_API_KEY not set"}
    else:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=50,
                messages=[{"role": "user", "content": "Say 'OK' if you can read this."}]
            )
            response_text = response.choices[0].message.content if response.choices else ""
            results["openai"] = {
                "status": "ok",
                "model": "gpt-4o",
                "response": response_text[:100]
            }
        except Exception as e:
            results["openai"] = {
                "status": "error",
                "model": "gpt-4o",
                "error_type": type(e).__name__,
                "error": str(e)[:500]
            }

    return results


@router.get("/analysis-progress/{job_id}")
async def get_analysis_progress(job_id: str) -> Dict[str, Any]:
    """
    Get the current progress of a document analysis job.

    Returns real-time status of multi-layer analysis including:
    - Current stage (extraction, verification, hallucination detection, etc.)
    - Progress percentage
    - Stage descriptions for user display
    - Elapsed time
    - Items extracted, errors corrected, etc.

    Poll this endpoint every 2-3 seconds during analysis for live updates.
    """
    job_status = progress_tracker.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis job not found: {job_id}"
        )
    return job_status


@router.get("/active-analyses")
async def get_active_analyses(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all active (in-progress) analysis jobs.

    Returns a list of currently running document analyses.
    Useful for showing a global progress indicator.
    """
    active_jobs = progress_tracker.get_active_jobs()
    return {
        "active_count": len(active_jobs),
        "jobs": active_jobs
    }


@router.get("/analysis-result/{job_id}")
async def get_completed_analysis_result(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the completed analysis result for a job.

    Use this endpoint after polling analysis-progress shows is_complete=true.
    Returns the full analysis result that was stored when the background task completed.
    """
    # First check if job exists and is complete
    job_status = progress_tracker.get_job_status(job_id)

    if not job_status:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis job not found: {job_id}"
        )

    if job_status.get("is_failed"):
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {job_status.get('error', 'Unknown error')}"
        )

    if not job_status.get("is_complete"):
        return {
            "status": "in_progress",
            "job_id": job_id,
            "progress": job_status.get("progress", 0),
            "stage": job_status.get("stage_title", "Processing"),
            "message": "Analysis still in progress. Poll /analysis-progress/{job_id} for updates."
        }

    # Get the stored result
    result = get_analysis_result(job_id)
    if not result:
        # Result might have been cleaned up or job was processed synchronously
        raise HTTPException(
            status_code=404,
            detail="Analysis result not found. It may have expired or the analysis was processed synchronously."
        )

    # DEBUG: Log what we're returning
    logger.info(f"[DEBUG] Returning analysis result for job {job_id}")
    logger.info(f"[DEBUG] Result has summary: {'summary' in result}, parties: {len(result.get('parties', []))}, dates: {len(result.get('key_dates', []))}")

    return result


@router.get("/analysis-audit/{job_id}")
async def get_analysis_audit_trail(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the full audit trail for a completed analysis.

    Returns comprehensive documentation of:
    - All analysis stages with timing and model info
    - Hallucinations detected with details
    - Corrections applied with before/after values
    - False positives restored
    - Confidence score changes
    - Document evidence for corrections

    This data is essential for:
    - Compliance and regulatory requirements
    - Debugging analysis issues
    - Understanding how final results were derived
    - Quality assurance reviews
    """
    # Get the stored result
    result = get_analysis_result(job_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Analysis result not found. It may have expired."
        )

    # Extract audit trail from result
    audit_trail = result.get("audit_trail")
    if not audit_trail:
        return {
            "status": "no_audit_trail",
            "job_id": job_id,
            "message": "This analysis was completed without audit trail (possibly in quick mode)"
        }

    return {
        "status": "success",
        "job_id": job_id,
        "audit_trail": audit_trail
    }


@router.get("/analysis-hallucinations/{job_id}")
async def get_analysis_hallucinations(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a summary of all hallucinations detected during analysis.

    Returns:
    - Total hallucinations detected
    - How many were corrected vs removed
    - False positives that were restored
    - Details of each hallucination with:
        - What was detected
        - Why it was flagged
        - What action was taken
        - Correction applied (if any)
    """
    result = get_analysis_result(job_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Analysis result not found. It may have expired."
        )

    audit_trail = result.get("audit_trail")
    if not audit_trail:
        return {
            "status": "no_audit_trail",
            "job_id": job_id,
            "hallucinations_detected": result.get("hallucinations_detected", 0),
            "message": "Detailed hallucination tracking not available for this analysis"
        }

    return {
        "status": "success",
        "job_id": job_id,
        "summary": audit_trail.get("summary", {}),
        "hallucinations": audit_trail.get("hallucinations", []),
        "by_type": _group_by_key(audit_trail.get("hallucinations", []), "item_type"),
        "by_action": _group_by_key(audit_trail.get("hallucinations", []), "action_taken")
    }


@router.get("/analysis-corrections/{job_id}")
async def get_analysis_corrections(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a summary of all corrections applied during analysis.

    Returns:
    - Total corrections applied
    - Corrections by source (layer2, expert_review, etc.)
    - Corrections by field type
    - Details of each correction with:
        - Original value
        - Corrected value
        - Why the correction was made
        - Document evidence (if found)
    """
    result = get_analysis_result(job_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Analysis result not found. It may have expired."
        )

    audit_trail = result.get("audit_trail")
    if not audit_trail:
        return {
            "status": "no_audit_trail",
            "job_id": job_id,
            "corrections_made": result.get("corrections_made", 0),
            "message": "Detailed correction tracking not available for this analysis"
        }

    return {
        "status": "success",
        "job_id": job_id,
        "total_corrections": len(audit_trail.get("corrections", [])),
        "corrections": audit_trail.get("corrections", []),
        "by_source": _group_by_key(audit_trail.get("corrections", []), "correction_source"),
        "verified_count": sum(1 for c in audit_trail.get("corrections", [])
                            if c.get("verified_against_document"))
    }


def _group_by_key(items: List[Dict], key: str) -> Dict[str, int]:
    """Helper to group items by a key and count occurrences"""
    counts = {}
    for item in items:
        value = item.get(key, "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _run_analysis_in_thread(
    job_id: str,
    document_id: str,
    text: str,
    filename: str,
    session_id: str,
    user_id: str,
    use_multi_layer: bool,
    thorough: bool,
    include_operational: bool,
    include_financial: bool
):
    """
    Runs document analysis in a separate thread with its own event loop.
    This ensures the analysis runs truly in the background without blocking
    the main FastAPI event loop.
    """
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _run_background_analysis(
                job_id=job_id,
                document_id=document_id,
                text=text,
                filename=filename,
                session_id=session_id,
                user_id=user_id,
                use_multi_layer=use_multi_layer,
                thorough=thorough,
                include_operational=include_operational,
                include_financial=include_financial
            )
        )
    finally:
        loop.close()


async def _run_background_analysis(
    job_id: str,
    document_id: str,
    text: str,
    filename: str,
    session_id: str,
    user_id: str,
    use_multi_layer: bool,
    thorough: bool,
    include_operational: bool,
    include_financial: bool
):
    """
    Background task to run document analysis asynchronously.
    Updates progress tracker as it runs and stores result when complete.
    """
    try:
        logger.info(f"Starting background analysis for job {job_id}, document {filename}")

        # Update progress to "extracting" state so the first poll sees activity
        progress_tracker.update_stage(
            job_id,
            AnalysisStage.EXTRACTING_TEXT,
            f"Preparing to analyze {filename}"
        )

        # Run the analysis
        if use_multi_layer:
            mode_desc = "thorough" if thorough else "quick"
            logger.info(f"Using multi-layer {mode_desc} analysis for: {filename} (job: {job_id})")
            verified_analysis = await multi_layer_analyzer.analyze_document(
                document_text=text,
                document_id=document_id,
                filename=filename,
                quick_mode=not thorough,
                job_id=job_id
            )
            analysis_result = _convert_verified_analysis_to_standard(verified_analysis, text)
            # DEBUG: Log what was extracted
            logger.info(f"[DEBUG] Analysis result summary: {analysis_result.get('summary', 'NO SUMMARY')[:100]}")
            logger.info(f"[DEBUG] Analysis result parties count: {len(analysis_result.get('parties', []))}")
            logger.info(f"[DEBUG] Analysis result dates count: {len(analysis_result.get('key_dates', []))}")
            logger.info(f"[DEBUG] Analysis result figures count: {len(analysis_result.get('key_figures', []))}")
        else:
            analysis_result = await dual_ai_service.analyze_document(
                text,
                filename,
                include_operational_details=include_operational,
                include_financial_details=include_financial
            )

        # Validate and normalize
        analysis_result = _validate_analysis_response(analysis_result)

        # Save to database
        try:
            db = SessionLocal()
            try:
                existing_doc = db.query(Document).filter(
                    Document.id == document_id,
                    Document.user_id == user_id
                ).first()

                if existing_doc:
                    existing_doc.text_content = text
                    existing_doc.summary = analysis_result.get('summary')
                    existing_doc.document_type = analysis_result.get('document_type')
                    existing_doc.parties = analysis_result.get('parties', [])
                    existing_doc.important_dates = analysis_result.get('key_dates', [])
                    existing_doc.key_figures = analysis_result.get('key_figures', [])
                    existing_doc.keywords = analysis_result.get('key_terms', [])
                    existing_doc.analysis_data = analysis_result
                    existing_doc.operational_details = analysis_result.get('operational_details')
                    existing_doc.financial_details = analysis_result.get('financial_details')
                    existing_doc.updated_at = datetime.utcnow()
                else:
                    document = Document(
                        id=document_id,
                        user_id=user_id,
                        session_id=session_id,
                        file_name=filename,
                        file_type="text/plain",
                        file_size=len(text),
                        text_content=text,
                        summary=analysis_result.get('summary'),
                        document_type=analysis_result.get('document_type'),
                        parties=analysis_result.get('parties', []),
                        important_dates=analysis_result.get('key_dates', []),
                        key_figures=analysis_result.get('key_figures', []),
                        keywords=analysis_result.get('key_terms', []),
                        analysis_data=analysis_result,
                        operational_details=analysis_result.get('operational_details'),
                        financial_details=analysis_result.get('financial_details')
                    )
                    db.add(document)

                db.commit()
                logger.info(f"Background analysis saved document to database: {filename}")
            finally:
                db.close()
        except Exception as db_error:
            logger.error(f"Background analysis database error: {str(db_error)}")

        # Store result for retrieval
        full_result = {
            "success": True,
            "document_id": document_id,
            "job_id": job_id,
            "session_id": session_id,
            "filename": filename,
            "text_length": len(text),
            "analyzed_at": datetime.now().isoformat(),
            **analysis_result
        }
        store_analysis_result(job_id, full_result)

        # Mark job as complete
        progress_tracker.update_stage(
            job_id,
            AnalysisStage.COMPLETED,
            "Analysis complete",
            confidence=analysis_result.get('confidence', 0.0)
        )

        logger.info(f"Background analysis completed for job {job_id}")

    except Exception as e:
        logger.error(f"Background analysis failed for job {job_id}: {str(e)}")
        progress_tracker.fail_job(job_id, str(e))


@router.post("/analyze-text-async")
async def analyze_text_async(
    request: AnalyzeTextRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start document analysis asynchronously and return immediately with job_id.

    This endpoint returns immediately with a job_id that can be used to:
    1. Poll /analysis-progress/{job_id} for real-time progress updates
    2. Fetch /analysis-result/{job_id} when complete

    This is the preferred endpoint for frontend integration as it enables
    real-time progress tracking during the analysis.
    """
    text = request.text
    filename = request.filename
    session_id = request.session_id or str(uuid.uuid4())
    document_id = request.document_id or str(uuid.uuid4())

    if not text or len(text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required and must be at least 10 characters"
        )

    # Create job for progress tracking (include user info)
    job_id = str(uuid.uuid4())
    progress_tracker.create_job(
        job_id,
        document_id,
        filename,
        user_id=current_user.user_id,
        user_email=current_user.email,
        user_name=getattr(current_user, 'username', None) or getattr(current_user, 'full_name', None)
    )
    progress_tracker.update_stage(job_id, AnalysisStage.QUEUED, "Analysis queued")

    # Submit analysis to thread pool executor
    # This runs the analysis in a completely separate thread with its own event loop,
    # ensuring the HTTP response returns immediately while analysis continues in background
    _analysis_executor.submit(
        _run_analysis_in_thread,
        job_id=job_id,
        document_id=document_id,
        text=text,
        filename=filename,
        session_id=session_id,
        user_id=current_user.user_id,
        use_multi_layer=request.use_multi_layer_analysis,
        thorough=request.thorough_analysis,
        include_operational=request.include_operational_details,
        include_financial=request.include_financial_details
    )

    logger.info(f"Started threaded analysis for {filename}, job_id: {job_id}, thorough={request.thorough_analysis}")

    # Return immediately with job info
    return {
        "success": True,
        "async": True,
        "job_id": job_id,
        "document_id": document_id,
        "session_id": session_id,
        "filename": filename,
        "status": "queued",
        "message": "Analysis started. Poll /api/v1/documents/analysis-progress/{job_id} for updates.",
        "progress_url": f"/api/v1/documents/analysis-progress/{job_id}",
        "result_url": f"/api/v1/documents/analysis-result/{job_id}"
    }


def _validate_analysis_response(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize the analysis response to ensure consistent structure
    for frontend consumption. Adds all required structured fields for comprehensive display.

    Args:
        analysis: Raw analysis result from dual AI service

    Returns:
        Normalized analysis with guaranteed array structures and comprehensive fields
    """
    # Ensure deadlines is always an array
    if not analysis.get("deadlines"):
        analysis["deadlines"] = []
    if not isinstance(analysis["deadlines"], list):
        deadlines = analysis["deadlines"]
        if isinstance(deadlines, str):
            analysis["deadlines"] = [{"date": "Unknown", "description": deadlines}]
        elif isinstance(deadlines, dict):
            analysis["deadlines"] = [deadlines]
        else:
            analysis["deadlines"] = []

    # DEDUPLICATE deadlines - same date should only appear once
    analysis["deadlines"] = deduplicate_dates(analysis["deadlines"])

    # Ensure key_dates is always an array
    if not analysis.get("key_dates"):
        analysis["key_dates"] = []
    if not isinstance(analysis["key_dates"], list):
        key_dates = analysis["key_dates"]
        if isinstance(key_dates, str):
            analysis["key_dates"] = [{"date": "Unknown", "description": key_dates}]
        elif isinstance(key_dates, dict):
            analysis["key_dates"] = [key_dates]
        else:
            analysis["key_dates"] = []

    # DEDUPLICATE key_dates - same date should only appear once
    analysis["key_dates"] = deduplicate_dates(analysis["key_dates"])

    # Ensure key_terms is always an array of strings
    if not analysis.get("key_terms") or len(analysis.get("key_terms", [])) == 0:
        # Try to extract from legal_terms.terms_explained
        legal_terms = analysis.get("legal_terms", {})
        if isinstance(legal_terms, dict) and legal_terms.get("terms_explained"):
            analysis["key_terms"] = list(legal_terms["terms_explained"].keys())
        else:
            analysis["key_terms"] = []
    if not isinstance(analysis["key_terms"], list):
        key_terms = analysis["key_terms"]
        if isinstance(key_terms, str):
            for delimiter in [',', ';', '\n', '|']:
                if delimiter in key_terms:
                    analysis["key_terms"] = [term.strip() for term in key_terms.split(delimiter) if term.strip()]
                    break
            else:
                analysis["key_terms"] = [key_terms.strip()]
        else:
            analysis["key_terms"] = []

    # Ensure parties is always an array - extract from parties_analysis if available
    if not analysis.get("parties") or len(analysis.get("parties", [])) == 0:
        # Try to extract from parties_analysis
        parties_analysis = analysis.get("parties_analysis", {})
        if isinstance(parties_analysis, dict) and parties_analysis.get("parties"):
            extracted_parties = []
            for party in parties_analysis["parties"]:
                if isinstance(party, dict):
                    name = party.get("name", "")
                    role = party.get("role", "")
                    if name:
                        extracted_parties.append(f"{name} ({role})" if role else name)
                elif isinstance(party, str):
                    extracted_parties.append(party)
            analysis["parties"] = extracted_parties
        else:
            analysis["parties"] = []
    if not isinstance(analysis["parties"], list):
        parties = analysis["parties"]
        if isinstance(parties, str):
            analysis["parties"] = [parties.strip()]
        else:
            analysis["parties"] = []

    # Ensure financial_amounts is always an array of objects
    for field_name in ["financial_amounts", "all_financial_amounts", "key_figures"]:
        field_value = analysis.get(field_name)
        if field_value is None:
            analysis[field_name] = []
        elif isinstance(field_value, str):
            # String was returned instead of array - try to parse or wrap
            import re
            amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', field_value)
            if amounts:
                analysis[field_name] = [{"amount": amt, "description": "Amount", "label": "Amount", "value": amt} for amt in amounts]
            else:
                analysis[field_name] = []
        elif isinstance(field_value, dict):
            # Single object instead of array
            analysis[field_name] = [field_value]
        elif not isinstance(field_value, list):
            analysis[field_name] = []
        else:
            # It's a list - ensure each item is a dict
            validated_items = []
            for item in field_value:
                if isinstance(item, dict):
                    validated_items.append(item)
                elif isinstance(item, str):
                    # String item - check if it's an amount
                    if '$' in item or item.replace(',', '').replace('.', '').isdigit():
                        validated_items.append({"amount": item, "description": "Amount", "label": "Amount", "value": item})
                    else:
                        validated_items.append({"description": item, "label": item, "amount": "", "value": ""})
            analysis[field_name] = validated_items

    # Ensure summary is always a string
    if not analysis.get("summary"):
        analysis["summary"] = "No summary available"
    if not isinstance(analysis["summary"], str):
        analysis["summary"] = str(analysis["summary"])

    # Ensure confidence is a number
    if not analysis.get("confidence"):
        analysis["confidence"] = 0.0
    if not isinstance(analysis["confidence"], (int, float)):
        try:
            analysis["confidence"] = float(analysis["confidence"])
        except (ValueError, TypeError):
            analysis["confidence"] = 0.0

    # Ensure document_type is a string
    if not analysis.get("document_type"):
        analysis["document_type"] = "Unknown Document Type"
    if not isinstance(analysis["document_type"], str):
        analysis["document_type"] = str(analysis["document_type"])

    # === ADD COMPREHENSIVE STRUCTURED FIELDS ===

    # 1. Plain English Summary - Enhanced with structured explanation
    if not analysis.get("plain_english_summary") or len(analysis.get("plain_english_summary", "")) < 100:
        analysis["plain_english_summary"] = generate_plain_english_summary(analysis)

    # 2. Parties Analysis
    if not analysis.get("parties_analysis"):
        parties = analysis.get("parties", [])
        parties_list = []
        for party in parties:
            if isinstance(party, str):
                name = party.split('(')[0].strip() if '(' in party else party
                role = party.split('(')[1].replace(')', '').strip() if '(' in party else "Party"
                parties_list.append({
                    "name": name,
                    "role": role,
                    "entity_type": "Corporation" if any(c in name.upper() for c in ['LLC', 'INC', 'CORP', 'LTD', 'CORPORATION']) else "Individual",
                    "what_they_want": f"See document for {role}'s position",
                    "relationship_to_case": role
                })
            elif isinstance(party, dict):
                parties_list.append(party)
        analysis["parties_analysis"] = {
            "total_parties": len(parties_list),
            "relationship_type": "adversarial" if any(r in str(parties).lower() for r in ['plaintiff', 'defendant', 'debtor', 'creditor']) else "contractual",
            "parties": parties_list
        }

    # 3. Timeline Analysis
    if not analysis.get("timeline_analysis"):
        key_dates = analysis.get("key_dates", [])
        deadlines = analysis.get("deadlines", [])
        timeline_events = []
        for d in key_dates:
            if isinstance(d, dict):
                timeline_events.append({
                    "date": d.get("date", "Unknown"),
                    "event": d.get("description", "Event"),
                    "importance": "Medium",
                    "significance": d.get("description", "See document")
                })
        critical_deadlines = []
        for dl in deadlines:
            if isinstance(dl, dict):
                critical_deadlines.append({
                    "date": dl.get("date", "Unknown"),
                    "description": dl.get("description", "Deadline"),
                    "consequence": "Failure to meet this deadline may result in adverse consequences",
                    "urgency": dl.get("urgency", "high")
                })
        analysis["timeline_analysis"] = {
            "total_dates": len(timeline_events),
            "critical_deadlines": critical_deadlines,
            "timeline_events": timeline_events
        }

    # 4. Legal Terms with Explanations
    if not analysis.get("legal_terms") or not analysis.get("legal_terms", {}).get("terms_explained"):
        key_terms = analysis.get("key_terms", [])
        term_definitions = {
            'motion': ('A formal request to the court', 'Asking the judge to make a decision'),
            'settlement': ('An agreement to resolve a dispute', 'A deal where both sides agree to end the fight'),
            'debtor': ('Person or entity that owes money', 'The one who owes money'),
            'creditor': ('Person or entity owed money', 'The one who is owed money'),
            'plaintiff': ('Party bringing a lawsuit', 'The person suing'),
            'defendant': ('Party being sued', 'The person being sued'),
            'breach': ('Violation of contract terms', 'Breaking a promise in a contract'),
            'damages': ('Money compensation for harm', 'Money to make up for harm caused'),
            'chapter 11': ('Business bankruptcy reorganization', 'A way for companies to reorganize debts'),
            'chapter 7': ('Liquidation bankruptcy', 'Selling assets to pay off debts'),
            'relief': ('Remedy sought from court', 'What you are asking the court to do'),
            'jurisdiction': ('Court authority over case', 'Whether the court can decide this case'),
            'petition': ('Formal written request to court', 'A formal ask to the court'),
            'complaint': ('Initial document starting lawsuit', 'The paper that starts the lawsuit'),
            'judgment': ('Final decision of court', 'The judge final ruling'),
        }
        terms_explained = {}
        for term in key_terms:
            term_lower = term.lower() if isinstance(term, str) else str(term).lower()
            for key, (definition, plain) in term_definitions.items():
                if key in term_lower:
                    terms_explained[term_lower] = {
                        "definition": definition,
                        "plain_english": plain,
                        "importance_level": "high" if key in ['motion', 'breach', 'damages', 'deadline'] else "medium",
                        "why_it_matters": "This term affects how your case will proceed"
                    }
                    break
            else:
                terms_explained[term_lower] = {
                    "definition": "Legal term found in document",
                    "plain_english": "A legal concept in your document",
                    "importance_level": "medium",
                    "why_it_matters": "Consult with an attorney for specific meaning"
                }
        analysis["legal_terms"] = {"terms_explained": terms_explained}

    # 5. Financial Analysis
    if not analysis.get("financial_analysis"):
        financial_amounts = analysis.get("financial_amounts", [])
        amount_claimed = analysis.get("amount_claimed", "Unknown")
        payment_amounts = []
        breakdown = []
        for fa in financial_amounts:
            if isinstance(fa, dict):
                payment_amounts.append(f"{fa.get('amount', 'Unknown')} - {fa.get('description', 'Amount')}")
                breakdown.append({
                    "category": fa.get("description", "Amount"),
                    "amount": fa.get("amount", "Unknown"),
                    "description": fa.get("description", ""),
                    "disputed": fa.get("type", "") == "disputed"
                })
        analysis["financial_analysis"] = {
            "total_amount_at_stake": amount_claimed if amount_claimed else (financial_amounts[0].get("amount") if financial_amounts else "Unknown"),
            "payment_amounts": payment_amounts,
            "payment_frequency": "See document for payment terms",
            "breakdown": breakdown
        }

    # 6. Risk Assessment
    if not analysis.get("risk_assessment"):
        potential_risks = analysis.get("potential_risks", [])
        identified_risks = []
        for risk in potential_risks:
            if isinstance(risk, str):
                identified_risks.append({
                    "risk": risk,
                    "likelihood": "Medium",
                    "impact": "Could affect case outcome",
                    "mitigation": "Consult with attorney for guidance"
                })
            elif isinstance(risk, dict):
                identified_risks.append(risk)
        if not identified_risks:
            identified_risks = [
                {"risk": "Missing response deadlines", "likelihood": "High", "impact": "Could result in default judgment", "mitigation": "Calendar all deadlines"},
                {"risk": "Incomplete understanding", "likelihood": "Medium", "impact": "May miss defenses", "mitigation": "Consult qualified attorney"}
            ]
        analysis["risk_assessment"] = {
            "overall_risk_level": "High" if analysis.get("deadlines") else "Medium",
            "risk_count": len(identified_risks),
            "identified_risks": identified_risks,
            "worst_case_scenario": "Failure to respond could result in adverse judgment",
            "best_case_scenario": "With proper response, matter may be resolved favorably"
        }

    # 7. Next Steps
    if not analysis.get("next_steps"):
        immediate_actions = analysis.get("immediate_actions", [])
        deadlines = analysis.get("deadlines", [])
        next_steps = []
        for dl in deadlines[:2]:
            if isinstance(dl, dict):
                next_steps.append(f"CRITICAL: {dl.get('description', 'Meet deadline')} by {dl.get('date', 'specified date')}")
        for action in immediate_actions[:3]:
            if isinstance(action, str) and action not in next_steps:
                next_steps.append(action)
        defaults = [
            "READ THE ENTIRE DOCUMENT CAREFULLY - Note all dates, amounts, and requirements",
            "IDENTIFY ALL DEADLINES - Missing a deadline could have serious consequences",
            "GATHER SUPPORTING DOCUMENTS - Collect all relevant records and correspondence",
            "CONSULT AN ATTORNEY - Get professional legal advice about your options",
            "DO NOT IGNORE THIS DOCUMENT - Failing to respond could result in default judgment"
        ]
        for step in defaults:
            if len(next_steps) < 5:
                next_steps.append(step)
        analysis["next_steps"] = next_steps[:5]

    # 8. Attorney Questions
    if not analysis.get("attorney_questions"):
        doc_type = analysis.get("document_type", "").lower()
        questions = [
            "What are my options for responding to this document?",
            "What are the strongest defenses available?",
            "What is the likely timeline and cost for resolving this?",
            "What are potential outcomes if this goes to trial vs settling?"
        ]
        if "bankruptcy" in doc_type:
            questions.insert(0, "How will this affect my assets and financial situation?")
        elif "motion" in doc_type:
            questions.insert(0, "Should I file a response or opposition to this motion?")
        elif "complaint" in doc_type or "lawsuit" in doc_type:
            questions.insert(0, "What defenses should I raise in my answer?")
        analysis["attorney_questions"] = questions[:4]

    # 9. Potential Defenses
    if not analysis.get("potential_defenses"):
        analysis["potential_defenses"] = [
            "Review with attorney to identify applicable defenses",
            "Check for procedural defects or improper service",
            "Evaluate statute of limitations issues",
            "Consider counterclaims or affirmative defenses"
        ]

    # 10. Key Figures - extract from financial_analysis if not present
    if not analysis.get("key_figures") or len(analysis.get("key_figures", [])) == 0:
        key_figures = []
        # Try to extract from financial_analysis
        financial_analysis = analysis.get("financial_analysis", {})
        if isinstance(financial_analysis, dict):
            total = financial_analysis.get("total_amount_at_stake")
            if total and total != "Unknown":
                key_figures.append({"label": "Total Amount at Stake", "value": total})
            breakdown = financial_analysis.get("breakdown", [])
            for item in breakdown[:3]:
                if isinstance(item, dict):
                    key_figures.append({
                        "label": item.get("category", "Amount"),
                        "value": item.get("amount", "Unknown")
                    })
        # Also check amount_claimed
        amount_claimed = analysis.get("amount_claimed")
        if amount_claimed and amount_claimed != "Unknown" and not key_figures:
            key_figures.append({"label": "Amount Claimed", "value": amount_claimed})
        # Check case_number
        case_number = analysis.get("case_number")
        if case_number:
            key_figures.append({"label": "Case Number", "value": case_number})
        analysis["key_figures"] = key_figures

    # 11. Key Arguments - CRITICAL: Ensure always an array to prevent frontend character-by-character bug
    key_arguments = analysis.get("key_arguments")
    if key_arguments is None:
        analysis["key_arguments"] = []
    elif isinstance(key_arguments, str):
        # String was returned instead of array - wrap it in an array
        logger.warning(f"key_arguments was a string, not array. Converting.")
        if key_arguments.strip():
            analysis["key_arguments"] = [{"argument": key_arguments.strip()}]
        else:
            analysis["key_arguments"] = []
    elif not isinstance(key_arguments, list):
        logger.warning(f"key_arguments was unexpected type: {type(key_arguments)}. Converting.")
        analysis["key_arguments"] = []
    else:
        # Validate each item in the array
        validated_args = []
        for arg in key_arguments:
            if isinstance(arg, str) and arg.strip():
                validated_args.append({"argument": arg.strip()})
            elif isinstance(arg, dict):
                if arg.get("argument") or arg.get("description"):
                    validated_args.append({
                        "argument": arg.get("argument") or arg.get("description", ""),
                        "supporting_facts": arg.get("supporting_facts", arg.get("supporting_evidence", "")),
                        "legal_basis": arg.get("legal_basis", "")
                    })
            # Skip invalid items
        analysis["key_arguments"] = validated_args

    logger.debug(f"Validated analysis - fields: {list(analysis.keys())}")
    return analysis


def _convert_verified_analysis_to_standard(verified_analysis, document_text: str) -> Dict[str, Any]:
    """
    Convert VerifiedAnalysis object from multi-layer analyzer to standard response format.

    This function bridges the new multi-layer verification system with the existing
    frontend expectations, ensuring backward compatibility while adding confidence metadata.
    """
    from ..src.services.multi_layer_analyzer import VerifiedAnalysis, ConfidenceLevel

    result = {}

    # Document type
    result["document_type"] = verified_analysis.document_type or "Unknown Document"

    # Summary - extract value from ExtractedItem
    if verified_analysis.summary:
        summary_val = verified_analysis.summary.value
        if isinstance(summary_val, dict):
            result["summary"] = summary_val.get("text", str(summary_val))
            result["summary_key_points"] = summary_val.get("key_points", [])
        else:
            result["summary"] = str(summary_val)

    # Parties - extract with source text for verification transparency
    result["parties"] = []
    for party in verified_analysis.parties:
        if isinstance(party.value, dict):
            result["parties"].append({
                "name": party.value.get("name", str(party.value)),
                "role": party.value.get("role", "Unknown"),
                "source_text": party.source_text or party.value.get("source_text", ""),
                "confidence": party.confidence.value,
                "confidence_score": party.confidence_score
            })
        else:
            result["parties"].append({
                "name": str(party.value),
                "confidence": party.confidence.value,
                "confidence_score": party.confidence_score
            })

    # Key dates
    result["key_dates"] = []
    for date_item in verified_analysis.dates:
        if isinstance(date_item.value, dict):
            result["key_dates"].append({
                "date": date_item.value.get("date", "Unknown"),
                "description": date_item.value.get("description", ""),
                "source_text": date_item.source_text or date_item.value.get("source_text", ""),
                "is_deadline": date_item.value.get("is_deadline", False),
                "urgency": date_item.value.get("urgency", "MEDIUM"),
                "confidence": date_item.confidence.value,
                "confidence_score": date_item.confidence_score
            })
        else:
            result["key_dates"].append({
                "date": str(date_item.value),
                "description": "",
                "confidence": date_item.confidence.value
            })

    # Key figures (monetary amounts)
    result["key_figures"] = []
    for amt in verified_analysis.monetary_amounts:
        if isinstance(amt.value, dict):
            result["key_figures"].append({
                "amount": amt.value.get("amount", str(amt.value)),
                "description": amt.value.get("description", ""),
                "type": amt.value.get("type", "unknown"),
                "source_text": amt.source_text or amt.value.get("source_text", ""),
                "confidence": amt.confidence.value,
                "confidence_score": amt.confidence_score
            })
        else:
            result["key_figures"].append({
                "amount": str(amt.value),
                "confidence": amt.confidence.value
            })

    # Key terms
    result["key_terms"] = []
    for term in verified_analysis.key_terms:
        if isinstance(term.value, dict):
            result["key_terms"].append({
                "term": term.value.get("term", str(term.value)),
                "explanation": term.value.get("explanation", ""),
                "importance": term.value.get("importance", "MEDIUM"),
                "confidence": term.confidence.value
            })
        else:
            result["key_terms"].append(str(term.value))

    # Deadlines with urgency
    result["deadlines"] = []
    for deadline in verified_analysis.deadlines:
        if isinstance(deadline.value, dict):
            result["deadlines"].append({
                "date": deadline.value.get("date", "Unknown"),
                "description": deadline.value.get("action_required", deadline.value.get("description", "")),
                "urgency": deadline.value.get("urgency", "HIGH"),
                "days_remaining": deadline.value.get("days_remaining", "UNKNOWN"),
                "source_text": deadline.source_text or deadline.value.get("source_text", ""),
                "confidence": deadline.confidence.value,
                "confidence_score": deadline.confidence_score
            })
        else:
            result["deadlines"].append({
                "date": str(deadline.value),
                "description": "See document",
                "urgency": "HIGH"
            })

    # Obligations
    result["obligations"] = []
    for obl in verified_analysis.obligations:
        if isinstance(obl.value, dict):
            result["obligations"].append({
                "description": obl.value.get("description", str(obl.value)),
                "obligated_party": obl.value.get("obligated_party", "Unknown"),
                "deadline": obl.value.get("deadline", ""),
                "consequences": obl.value.get("consequences", ""),
                "confidence": obl.confidence.value
            })
        else:
            result["obligations"].append({
                "description": str(obl.value),
                "confidence": obl.confidence.value
            })

    # Keywords
    result["keywords"] = [
        kw.value if isinstance(kw.value, str) else str(kw.value)
        for kw in verified_analysis.keywords
    ]

    # Add verification metadata for transparency
    result["verification_metadata"] = {
        "overall_confidence": verified_analysis.overall_confidence.value,
        "overall_confidence_score": verified_analysis.overall_confidence_score,
        "hallucinations_detected": verified_analysis.hallucinations_detected,
        "corrections_made": verified_analysis.corrections_made,
        "total_processing_time": verified_analysis.total_processing_time,
        "analyzed_at": verified_analysis.analyzed_at,
        "layers_completed": list(verified_analysis.layer_results.keys()),
        "analysis_method": "multi_layer_verified"
    }

    # Add layer-specific information
    for layer_name, layer_result in verified_analysis.layer_results.items():
        result["verification_metadata"][f"{layer_name}_model"] = layer_result.model_used
        if layer_result.warnings:
            result["verification_metadata"][f"{layer_name}_warnings"] = layer_result.warnings

    # ============================================================
    # ADD COMPREHENSIVE FIELDS FOR ENHANCED FRONTEND DISPLAY
    # ============================================================

    # Build comprehensive summary with all key information
    summary_parts = []
    if result.get("summary"):
        summary_parts.append(f"DOCUMENT INFO: {result['summary']}")

    if result.get("parties"):
        party_names = [p.get("name", str(p)) for p in result["parties"][:5]]
        summary_parts.append(f"KEY PARTIES: {'; '.join(party_names)}")

    if result.get("key_figures"):
        amounts = [f"{kf.get('description', 'Amount')}: {kf.get('amount', kf.get('value', 'N/A'))}"
                   for kf in result["key_figures"][:5]]
        summary_parts.append(f"FINANCIAL AMOUNTS: {'; '.join(amounts)}")

    if result.get("deadlines"):
        deadline_strs = [f"{dl.get('date', 'TBD')} - {dl.get('description', 'Action required')}"
                        for dl in result["deadlines"][:5]]
        summary_parts.append(f"CRITICAL DEADLINES: {'; '.join(deadline_strs)}")

    if result.get("key_dates"):
        date_strs = [f"{d.get('date', 'Unknown')}: {d.get('description', '')}"
                    for d in result["key_dates"][:5]]
        summary_parts.append(f"KEY DATES: {'; '.join(date_strs)}")

    result["comprehensive_summary"] = "\n\n".join(summary_parts) if summary_parts else result.get("summary", "")

    # Map all_dates with why_important explanations - using SPECIFIC text, not generic
    result["all_dates"] = []
    for date_item in result.get("key_dates", []):
        description = date_item.get("description", "")
        date_type = date_item.get("type", "date")

        # Get specific significance text (not generic)
        significance = get_specific_significance(
            date_type,
            description,
            date_item.get("source_text", "")
        )

        all_date = {
            "date": date_item.get("date", "Unknown"),
            "event": description,
            "description": description,
            "significance": significance,
            "why_important": significance,
            "action_required": date_item.get("action_required", ""),
            "consequence_if_missed": "",
            "urgency": date_item.get("urgency", "normal")
        }
        # If it's marked as a deadline, add specific consequence
        if date_item.get("is_deadline"):
            all_date["consequence_if_missed"] = get_specific_risk_text(
                date_type, description, ""
            )
            all_date["urgency"] = "HIGH"
        result["all_dates"].append(all_date)

    # Also include deadlines in all_dates with SPECIFIC risk text
    for deadline in result.get("deadlines", []):
        description = deadline.get("description", "Deadline")
        deadline_type = deadline.get("type", "deadline")

        # Get specific significance and risk text
        significance = get_specific_significance("deadline", description, "")
        risk_text = get_specific_risk_text(
            deadline_type,
            description,
            deadline.get("consequence_if_missed", "")
        )

        result["all_dates"].append({
            "date": deadline.get("date", "Unknown"),
            "event": description,
            "description": description,
            "significance": significance,
            "why_important": significance,
            "action_required": description,
            "consequence_if_missed": risk_text,
            "urgency": deadline.get("urgency", "HIGH")
        })

    # DEDUPLICATE all_dates - same date should only appear once with merged information
    result["all_dates"] = deduplicate_dates(result["all_dates"])

    # FIX 2: Populate all_parties with same data as parties (for frontend compatibility)
    # Frontend checks all_parties first, so we need to provide it
    if result.get("parties") and len(result["parties"]) > 0:
        result["all_parties"] = result["parties"]
    # Don't set all_parties if parties is empty - let frontend fallback work

    # Map all_financial_amounts with disputed info
    # FIX 3: Ensure this is always an array of objects, never a string
    result["all_financial_amounts"] = []
    key_figures = result.get("key_figures", [])

    # Handle case where key_figures might be a string (from AI hallucination)
    if isinstance(key_figures, str):
        logger.warning(f"key_figures was a string, not array: {key_figures[:100]}...")
        # Try to extract amounts from the string
        import re
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', key_figures)
        key_figures = [{"amount": amt, "description": "Extracted amount"} for amt in amounts]
    elif not isinstance(key_figures, list):
        logger.warning(f"key_figures was unexpected type: {type(key_figures)}")
        key_figures = []

    for kf in key_figures:
        # Handle case where individual items might be strings
        if isinstance(kf, str):
            result["all_financial_amounts"].append({
                "amount": kf if '$' in kf else "Unknown",
                "description": kf if '$' not in kf else "Amount",
                "type": "monetary",
                "disputed": False,
                "dispute_reason": "",
                "source_text": ""
            })
        elif isinstance(kf, dict):
            result["all_financial_amounts"].append({
                "amount": kf.get("amount", kf.get("value", "Unknown")),
                "description": kf.get("description", "Financial amount"),
                "type": kf.get("type", "monetary"),
                "disputed": kf.get("disputed", False),
                "dispute_reason": kf.get("dispute_reason", ""),
                "source_text": kf.get("source_text", "")
            })

    # Add all_deadlines for consistency
    result["all_deadlines"] = result.get("deadlines", [])

    # Try to extract case information from summary/document
    result["case_number"] = ""
    result["court"] = ""
    result["filing_date"] = ""
    result["core_dispute"] = ""
    result["plain_english_summary"] = result.get("summary", "")
    result["key_arguments"] = []
    result["relief_requested"] = []
    result["cited_authority"] = []
    result["hearing_info"] = None

    # Extract from parties for filer info
    for party in result.get("parties", []):
        if "trustee" in str(party.get("role", "")).lower():
            result["core_dispute"] = f"Matter involving {party.get('name', 'a party')} as {party.get('role', 'party')}"
            break
        elif "plaintiff" in str(party.get("role", "")).lower():
            result["core_dispute"] = f"Case brought by {party.get('name', 'plaintiff')}"
            break

    # Build key_arguments from obligations if available
    for obl in result.get("obligations", []):
        result["key_arguments"].append({
            "argument": obl.get("description", ""),
            "supporting_facts": obl.get("consequences", ""),
            "legal_basis": ""
        })

    logger.info(f"Converted verified analysis - confidence: {verified_analysis.overall_confidence.value} ({verified_analysis.overall_confidence_score:.1f}%)")

    return result


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(..., description="PDF document to analyze"),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze a legal document using AI

    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text from the PDF
    3. Sends the text to OpenAI for analysis
    4. Returns structured analysis results

    Returns:
        - document_type: Type of legal document
        - summary: Brief summary of the document
        - parties: Parties involved
        - key_dates: Important dates found
        - deadlines: Legal deadlines
        - confidence: AI confidence score
        - And more detailed analysis
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )

        # Read file contents
        file_contents = await file.read()

        # Validate PDF
        if not pdf_service.validate_pdf(file_contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        # Extract text from PDF
        extracted_text = pdf_service.extract_text_from_pdf(
            file_contents,
            file.filename
        )

        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract meaningful text from PDF"
            )

        # Detect document type to route to specialized processor
        from ..src.services.expert_agents import detect_document_type, DocumentType
        detected_type = detect_document_type(extracted_text)
        logger.info(f"Detected document type: {detected_type.value} for {file.filename}")

        # Route BANKRUPTCY documents to specialized processor
        if detected_type == DocumentType.BANKRUPTCY:
            logger.info(f"Routing {file.filename} to bankruptcy processor")

            # Use bankruptcy-specific extraction
            from ..src.services.bankruptcy_document_processor import bankruptcy_processor
            from ..src.services.ai_backup_extractor import ai_backup_extractor
            from ..src.services.bankruptcy_metrics import (
                calculate_settlement_metrics,
                calculate_creditor_recovery_rates,
                identify_fraudulent_conveyances
            )

            # Use FULL bankruptcy document processing (includes all new extractors)
            bankruptcy_result = bankruptcy_processor.process_bankruptcy_document(extracted_text, file.filename)

            # Extract component data
            financial_data = bankruptcy_result.get('financial_data', {})
            ownership_data = bankruptcy_result.get('ownership_structure', {})
            legal_issues = bankruptcy_result.get('legal_issues', {})
            case_info = bankruptcy_result.get('case_info', {})
            invoice_data = bankruptcy_result.get('invoice_data', {})
            attorney_info = bankruptcy_result.get('attorney_info', {})
            fraud_indicators = bankruptcy_result.get('fraud_indicators', {})

            logger.info(f"Bankruptcy extraction found: {len(financial_data.get('monetary_amounts', []))} amounts, "
                       f"{len(financial_data.get('claims', []))} claims, "
                       f"{len(case_info.get('related_cases', []))} related cases, "
                       f"{len(invoice_data.get('counterparties', []))} counterparties")

            # Use AI backup if extraction seems incomplete
            if len(financial_data.get('monetary_amounts', [])) < 3:
                logger.warning("Low monetary amount extraction, using AI backup")
                ai_financial = await ai_backup_extractor.extract_with_ai(
                    extracted_text, "financial", financial_data
                )
                financial_data = merge_extraction_results(financial_data, ai_financial)

            if not ownership_data.get('voting_control') and not ownership_data.get('economic_ownership'):
                logger.warning("No ownership data found, using AI backup")
                ai_ownership = await ai_backup_extractor.extract_with_ai(
                    extracted_text, "ownership", ownership_data
                )
                ownership_data = merge_extraction_results(ownership_data, ai_ownership)

            if len(legal_issues.get('case_citations', [])) + len(legal_issues.get('precedent_violations', [])) == 0:
                logger.warning("No legal citations found, using AI backup")
                ai_legal = await ai_backup_extractor.extract_with_ai(
                    extracted_text, "legal", legal_issues
                )
                legal_issues = merge_extraction_results(legal_issues, ai_legal)

            # Calculate metrics
            metrics = calculate_settlement_metrics(financial_data)
            creditor_recovery = calculate_creditor_recovery_rates(
                financial_data.get('claims', []),
                financial_data.get('settlements', [])
            )
            fraudulent_conveyances = identify_fraudulent_conveyances(
                financial_data.get('monetary_amounts', []),
                ownership_data
            )

            # Also run AI analysis to get summary and other fields
            ai_analysis = await dual_ai_service.analyze_document(
                extracted_text,
                file.filename,
                include_operational_details=True
            )
            ai_analysis = _validate_analysis_response(ai_analysis)

            # Merge bankruptcy-specific data into AI analysis
            analysis_result = ai_analysis
            analysis_result["document_type"] = "Bankruptcy Document"
            analysis_result["bankruptcy_data"] = {
                "financial": financial_data,
                "ownership": ownership_data,
                "legal": legal_issues,
                "metrics": metrics,
                "creditor_recovery": creditor_recovery,
                "fraudulent_conveyances": fraudulent_conveyances,
                # NEW: Enhanced data
                "case_info": case_info,
                "invoice_data": invoice_data,
                "attorney_info": attorney_info,
                "fraud_indicators": fraud_indicators,
            }

            # NEW: Top-level fields for easier frontend access
            analysis_result["case_number"] = case_info.get('primary_case_number')
            analysis_result["court"] = case_info.get('court')
            analysis_result["judge"] = case_info.get('judge')
            analysis_result["related_cases"] = case_info.get('related_cases', [])
            analysis_result["ecf_references"] = case_info.get('ecf_references', [])
            analysis_result["counterparties"] = invoice_data.get('counterparties', [])
            analysis_result["attorneys"] = attorney_info.get('attorneys', [])
            analysis_result["law_firms"] = attorney_info.get('law_firms', [])
            analysis_result["fraud_risk_level"] = fraud_indicators.get('risk_level', 'LOW')
            analysis_result["claim_inflation"] = fraud_indicators.get('claim_analysis', {})

            analysis_result["extraction_stats"] = {
                "amounts_found": len(financial_data.get('monetary_amounts', [])),
                "claims_found": len(financial_data.get('claims', [])),
                "settlements_found": len(financial_data.get('settlements', [])),
                "case_citations": len(legal_issues.get('case_citations', [])),
                "precedent_violations": len(legal_issues.get('precedent_violations', [])),
                # NEW stats
                "related_cases": len(case_info.get('related_cases', [])),
                "ecf_references": len(case_info.get('ecf_references', [])),
                "invoices": invoice_data.get('invoice_count', 0),
                "counterparties": len(invoice_data.get('counterparties', [])),
                "attorneys": len(attorney_info.get('attorneys', [])),
                "fraud_indicators": len(fraud_indicators.get('indicators', [])),
            }
            analysis_result["alerts"] = generate_alerts(
                financial_data, ownership_data, legal_issues, metrics, fraudulent_conveyances
            )

            # Format for UI
            from ..src.services.ui_formatter import format_results_for_display
            bankruptcy_response = {
                "success": True,
                "financial": financial_data,
                "ownership": ownership_data,
                "legal": legal_issues,
                "metrics": metrics,
            }
            analysis_result["ui_display"] = format_results_for_display(bankruptcy_response)

        else:
            # Non-bankruptcy: use standard Dual-AI analysis
            analysis_result = await dual_ai_service.analyze_document(
                extracted_text,
                file.filename,
                include_operational_details=True
            )
            analysis_result = _validate_analysis_response(analysis_result)

        # Add metadata
        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(file_contents),
            "text_length": len(extracted_text),
            "analyzed_at": datetime.now().isoformat(),
            "detected_type": detected_type.value,
            "analysis": analysis_result
        }

        logger.info(f"Successfully analyzed document: {file.filename}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error analyzing document {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document analysis failed: {str(e)}"
        )

@router.post("/extract-text")
async def extract_text_only(
    file: UploadFile = File(..., description="PDF document to extract text from"),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Extract text from a PDF document without AI analysis

    Useful for:
    - Testing text extraction
    - Getting raw text for manual review
    - Debugging PDF processing issues

    Returns:
        - extracted_text: The full text content
        - page_count: Number of pages processed
        - metadata: File information
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )

        # Read file contents
        file_contents = await file.read()

        # Validate PDF
        if not pdf_service.validate_pdf(file_contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        # Extract text
        extracted_text = pdf_service.extract_text_from_pdf(
            file_contents,
            file.filename
        )

        # Count pages (rough estimate from page markers)
        page_count = extracted_text.count("--- Page") if "--- Page" in extracted_text else 1

        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(file_contents),
            "extracted_text": extracted_text,
            "text_length": len(extracted_text),
            "estimated_pages": page_count,
            "extracted_at": datetime.now().isoformat()
        }

        logger.info(f"Successfully extracted text from: {file.filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text from {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {str(e)}"
        )

@router.post("/analyze-text")
async def analyze_text(
    request: AnalyzeTextRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze extracted document text using AI and save to database

    This endpoint accepts already-extracted text instead of a file upload.
    Useful when text has already been extracted and you want to analyze it.

    Request body:
        - text: The document text to analyze
        - filename: Original filename (for context)
        - session_id: Frontend session ID (for persistence)
        - document_id: Optional document ID to update existing

    Returns:
        - document_id: ID for retrieving this document later
        - summary: Brief summary of the document
        - parties: Parties involved
        - key_dates: Important dates found
        - key_figures: Key monetary amounts or figures
        - key_terms: Important legal terms
        - And more detailed analysis
    """
    try:
        text = request.text
        filename = request.filename
        session_id = request.session_id or str(uuid.uuid4())
        document_id = request.document_id or str(uuid.uuid4())

        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required and must be at least 10 characters"
            )

        # Create job for progress tracking (include user info)
        job_id = str(uuid.uuid4())
        progress_tracker.create_job(
            job_id,
            document_id,
            filename,
            user_id=current_user.user_id,
            user_email=current_user.email,
            user_name=getattr(current_user, 'username', None) or getattr(current_user, 'full_name', None)
        )
        progress_tracker.update_stage(job_id, AnalysisStage.EXTRACTING_TEXT, "Processing document text")

        # Use multi-layer analysis (4-layer verification) or standard dual-AI
        if request.use_multi_layer_analysis:
            # Multi-layer analysis with Claude Opus + GPT-4o verification
            # quick_mode=True (~30s) skips inspections, quick_mode=False (~100s) is thorough
            mode_desc = "thorough" if request.thorough_analysis else "quick"
            logger.info(f"Using multi-layer {mode_desc} analysis for: {filename} (job: {job_id})")
            verified_analysis = await multi_layer_analyzer.analyze_document(
                document_text=text,
                document_id=document_id,
                filename=filename,
                quick_mode=not request.thorough_analysis,
                job_id=job_id  # Pass job ID for progress tracking
            )

            # Convert VerifiedAnalysis to standard format
            analysis_result = _convert_verified_analysis_to_standard(verified_analysis, text)

            # NOTE: Multi-layer analysis already extracts comprehensive data.
            # We DON'T call dual_ai_service again - that was causing redundant API calls
            # and doubling analysis time. The multi-layer analyzer output is complete.
            logger.info(f"Multi-layer analysis complete - skipping redundant supplemental extraction")
        else:
            # Standard Dual-AI (OpenAI + Claude) analysis
            analysis_result = await dual_ai_service.analyze_document(
                text,
                filename,
                include_operational_details=request.include_operational_details,
                include_financial_details=request.include_financial_details
            )

        # Validate and normalize response structure
        analysis_result = _validate_analysis_response(analysis_result)

        # Save to database
        try:
            # Security: Check if document exists AND belongs to current user
            existing_doc = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == current_user.user_id
            ).first()

            if existing_doc:
                # Update existing document (already verified ownership above)
                existing_doc.text_content = text
                existing_doc.summary = analysis_result.get('summary')
                existing_doc.document_type = analysis_result.get('document_type')
                existing_doc.parties = analysis_result.get('parties', [])
                existing_doc.important_dates = analysis_result.get('key_dates', [])
                existing_doc.key_figures = analysis_result.get('key_figures', [])
                existing_doc.keywords = analysis_result.get('key_terms', [])
                existing_doc.analysis_data = analysis_result
                existing_doc.operational_details = analysis_result.get('operational_details')
                existing_doc.financial_details = analysis_result.get('financial_details')
                existing_doc.updated_at = datetime.utcnow()
                logger.info(f"Updated existing document: {document_id} for user {current_user.user_id}")
            else:
                # Create new document with user ownership
                document = Document(
                    id=document_id,
                    user_id=current_user.user_id,  # SECURITY: Associate document with user
                    session_id=session_id,
                    file_name=filename,
                    file_type="text/plain",
                    file_size=len(text),
                    text_content=text,
                    summary=analysis_result.get('summary'),
                    document_type=analysis_result.get('document_type'),
                    parties=analysis_result.get('parties', []),
                    important_dates=analysis_result.get('key_dates', []),
                    key_figures=analysis_result.get('key_figures', []),
                    keywords=analysis_result.get('key_terms', []),
                    analysis_data=analysis_result,
                    operational_details=analysis_result.get('operational_details'),
                    financial_details=analysis_result.get('financial_details')
                )
                db.add(document)
                logger.info(f"Created new document: {document_id} for user {current_user.user_id}")

            db.commit()
            logger.info(f"Saved document to database: {filename}")
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            db.rollback()
            # Continue even if DB save fails

        # Add metadata to response
        response = {
            "success": True,
            "document_id": document_id,  # Return ID for frontend
            "job_id": job_id,            # Return job ID for progress tracking
            "session_id": session_id,    # Return session ID
            "filename": filename,
            "text_length": len(text),
            "analyzed_at": datetime.now().isoformat(),
            **analysis_result  # Flatten the analysis into the response
        }

        logger.info(f"Successfully analyzed text from: {filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text analysis failed: {str(e)}"
        )

@router.get("/session/{session_id}")
async def get_session_documents(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retrieve all documents for a session (owned by the current user)

    Returns all documents associated with the given session_id,
    allowing frontend to restore state after page refresh.
    SECURITY: Only returns documents owned by the authenticated user.
    """
    try:
        # SECURITY: Filter by both session_id AND user_id
        documents = db.query(Document).filter(
            Document.session_id == session_id,
            Document.user_id == current_user.user_id,  # Only user's own documents
            Document.is_deleted == False
        ).order_by(Document.upload_date.desc()).all()

        return {
            "session_id": session_id,
            "document_count": len(documents),
            "documents": [
                {
                    "id": doc.id,
                    "fileName": doc.file_name,
                    "fileType": doc.file_type,
                    "uploadDate": doc.upload_date.isoformat(),
                    "text": doc.text_content,
                    "summary": doc.summary,
                    "parties": doc.parties,
                    "importantDates": doc.important_dates,
                    "keyFigures": doc.key_figures,
                    "keywords": doc.keywords,
                    "analysis": doc.analysis_data
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving session documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session data: {str(e)}"
        )


@router.get("/document/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retrieve a specific document by ID (must be owned by current user)
    SECURITY: Only returns documents owned by the authenticated user.
    """
    try:
        # SECURITY: Filter by document_id AND user_id
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.user_id,  # Only user's own documents
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return {
            "id": document.id,
            "session_id": document.session_id,
            "fileName": document.file_name,
            "fileType": document.file_type,
            "uploadDate": document.upload_date.isoformat(),
            "text": document.text_content,
            "summary": document.summary,
            "parties": document.parties,
            "importantDates": document.important_dates,
            "keyFigures": document.key_figures,
            "keywords": document.keywords,
            "analysis": document.analysis_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/document/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a document (soft delete) - must be owned by current user

    Marks the document as deleted in the database.
    The document will no longer appear in session queries.
    SECURITY: Only allows deleting documents owned by the authenticated user.
    """
    try:
        # SECURITY: Filter by document_id AND user_id
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.user_id,  # Only user's own documents
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Soft delete
        document.is_deleted = True
        document.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Deleted document: {document_id} ({document.file_name})")

        return {
            "success": True,
            "message": f"Document '{document.file_name}' has been deleted",
            "document_id": document_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/document/{document_id}/operational-details")
async def get_operational_details(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get operational details for a specific document (must be owned by current user)

    Returns detailed extraction including:
    - Action items with deadlines (shall/must obligations)
    - Conditional obligations (if X then Y)
    - Permanent restrictions
    - Notice/contact information
    - Financial implications
    - Legal jurisdiction details
    - Critical review dates
    SECURITY: Only returns data for documents owned by the authenticated user.
    """
    try:
        # SECURITY: Filter by document_id AND user_id
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.user_id,  # Only user's own documents
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        operational_details = document.operational_details

        if not operational_details:
            # If not already extracted, extract now
            from ..src.services.enhanced_document_extractor import enhanced_extractor

            logger.info(f"Extracting operational details on-demand for document: {document_id}")

            basic_analysis = document.analysis_data if document.analysis_data else {}
            operational_details = await enhanced_extractor.extract_operational_details(
                document.text_content,
                document.file_name,
                basic_analysis
            )

            # Save to database
            document.operational_details = operational_details
            document.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Extracted and saved operational details for document: {document_id}")

        return {
            "document_id": document_id,
            "filename": document.file_name,
            "extracted_at": document.updated_at.isoformat() if document.updated_at else None,
            **operational_details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving operational details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve operational details: {str(e)}"
        )


@router.post("/document/{document_id}/extract-operational-details")
async def extract_operational_details(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Force re-extraction of operational details for an existing document

    Useful when:
    - Document was analyzed before operational extraction was available
    - You want to refresh the extraction with updated algorithms
    - Previous extraction failed or was incomplete
    SECURITY: Only allows operations on documents owned by the authenticated user.
    """
    try:
        # SECURITY: Filter by document_id AND user_id
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.user_id,  # Only user's own documents
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        from ..src.services.enhanced_document_extractor import enhanced_extractor

        logger.info(f"Re-extracting operational details for document: {document_id}")

        basic_analysis = document.analysis_data if document.analysis_data else {}
        operational_details = await enhanced_extractor.extract_operational_details(
            document.text_content,
            document.file_name,
            basic_analysis
        )

        # Save to database
        document.operational_details = operational_details
        document.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Re-extracted and saved operational details for document: {document_id}")

        return {
            "success": True,
            "message": f"Operational details extracted for '{document.file_name}'",
            "document_id": document_id,
            "extracted_at": document.updated_at.isoformat(),
            **operational_details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting operational details: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract operational details: {str(e)}"
        )


@router.post("/process-document")
async def process_document(
    file: UploadFile = File(..., description="Bankruptcy PDF document to process"),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    COMPREHENSIVE BANKRUPTCY DOCUMENT PROCESSOR
    THIS ENDPOINT MUST RETURN ALL EXTRACTED DATA

    This is the main endpoint for processing bankruptcy documents with:
    1. Complete text extraction (pdfplumber)
    2. Pattern-based extraction (BankruptcyDocumentProcessor)
    3. AI backup extraction (when patterns fail)
    4. Settlement metrics calculation
    5. Fraud detection
    6. Comprehensive validation

    Returns EVERYTHING extracted from the document.
    """
    import tempfile
    from pathlib import Path

    try:
        # Step 1: Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            file_path = tmp_file.name

        logger.info(f"Processing bankruptcy document: {file.filename}")

        # Step 2: Extract text using pdfplumber (better OCR than pypdf)
        try:
            import pdfplumber
            full_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"

            logger.info(f"Extracted {len(full_text)} characters from {file.filename}")

        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}, trying pypdf")
            # Fallback to pypdf
            full_text = pdf_service.extract_text_from_pdf(content, file.filename)

        if not full_text or len(full_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract meaningful text from PDF"
            )

        # Step 3: Run the COMPLETE extraction with bankruptcy processor
        from ..src.services.bankruptcy_document_processor import bankruptcy_processor

        financial_data = bankruptcy_processor.extract_all_financial_data(full_text)
        ownership_data = bankruptcy_processor.extract_ownership_structure(full_text)
        legal_issues = bankruptcy_processor.extract_legal_issues(full_text)

        logger.info(f"Pattern extraction found: {len(financial_data.get('monetary_amounts', []))} amounts, "
                   f"{len(financial_data.get('claims', []))} claims, "
                   f"{len(legal_issues.get('precedent_violations', []))} violations")

        # Step 4: Validate we got everything - if not, use AI backup
        from ..src.services.ai_backup_extractor import ai_backup_extractor

        # Check if financial extraction seems incomplete
        if len(financial_data.get('monetary_amounts', [])) < 3:
            logger.warning("Low monetary amount extraction, using AI backup")
            ai_financial = await ai_backup_extractor.extract_with_ai(
                full_text,
                "financial",
                financial_data
            )
            # Merge AI results with pattern results
            financial_data = merge_extraction_results(financial_data, ai_financial)

        # Check if ownership data is missing
        if not ownership_data.get('voting_control') and not ownership_data.get('economic_ownership'):
            logger.warning("No ownership data found, using AI backup")
            ai_ownership = await ai_backup_extractor.extract_with_ai(
                full_text,
                "ownership",
                ownership_data
            )
            ownership_data = merge_extraction_results(ownership_data, ai_ownership)

        # Check if legal issues seem incomplete
        if len(legal_issues.get('case_citations', [])) + len(legal_issues.get('precedent_violations', [])) == 0:
            logger.warning("No legal citations found, using AI backup")
            ai_legal = await ai_backup_extractor.extract_with_ai(
                full_text,
                "legal",
                legal_issues
            )
            legal_issues = merge_extraction_results(legal_issues, ai_legal)

        # Step 5: Calculate derived metrics and fraud detection
        from ..src.services.bankruptcy_metrics import (
            calculate_settlement_metrics,
            calculate_creditor_recovery_rates,
            identify_fraudulent_conveyances
        )

        metrics = calculate_settlement_metrics(financial_data)

        # Calculate creditor recovery rates
        creditor_recovery = calculate_creditor_recovery_rates(
            financial_data.get('claims', []),
            financial_data.get('settlements', [])
        )

        # Identify potentially fraudulent conveyances
        fraudulent_conveyances = identify_fraudulent_conveyances(
            financial_data.get('monetary_amounts', []),
            ownership_data
        )

        # Step 6: Return EVERYTHING
        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(content),
            "text_length": len(full_text),
            "processed_at": datetime.now().isoformat(),

            # Complete extraction results
            "financial": financial_data,
            "ownership": ownership_data,
            "legal": legal_issues,

            # Calculated metrics
            "metrics": metrics,
            "creditor_recovery": creditor_recovery,
            "fraudulent_conveyances": fraudulent_conveyances,

            # Statistics for validation
            "extraction_stats": {
                "amounts_found": len(financial_data.get('monetary_amounts', [])),
                "unique_amounts": len(set(a.get('amount', 0) for a in financial_data.get('monetary_amounts', []))),
                "percentages_found": len(financial_data.get('percentages', [])),
                "shares_found": len(financial_data.get('shares', [])),
                "claims_found": len(financial_data.get('claims', [])),
                "settlements_found": len(financial_data.get('settlements', [])),
                "case_citations": len(legal_issues.get('case_citations', [])),
                "precedent_violations": len(legal_issues.get('precedent_violations', [])),
                "statutory_references": len(legal_issues.get('statutory_references', [])),
                "legal_issues": len(legal_issues.get('precedent_violations', [])) + len(legal_issues.get('authority_limitations', [])),
                "fraud_indicators": metrics.get('overall_statistics', {}).get('fraud_indicators', 0),
                "extraction_complete": True,
                "ai_backup_used": len(financial_data.get('monetary_amounts', [])) >= 3  # Heuristic
            },

            # Red flags and alerts
            "alerts": generate_alerts(financial_data, ownership_data, legal_issues, metrics, fraudulent_conveyances),

            # UI-formatted data
            "ui_display": None  # Will be populated by /process-document/formatted endpoint
        }

        # Add UI-formatted version for easier frontend consumption
        from ..src.services.ui_formatter import format_results_for_display
        response["ui_display"] = format_results_for_display(response)

        # Clean up temp file
        try:
            Path(file_path).unlink()
        except:
            pass

        logger.info(f"Successfully processed bankruptcy document: {file.filename}")
        logger.info(f"Extraction stats: {response['extraction_stats']}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing bankruptcy document {file.filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


def merge_extraction_results(pattern_results: Dict[str, Any], ai_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge pattern-based and AI extraction results

    Prefers pattern results but adds AI findings that were missed
    """
    merged = pattern_results.copy()

    for key, ai_value in ai_results.items():
        if isinstance(ai_value, list):
            # Merge lists, avoiding duplicates
            pattern_value = merged.get(key, [])

            # Simple deduplication by checking if similar items exist
            for ai_item in ai_value:
                # Check if this item is already in pattern results
                is_duplicate = False

                for pattern_item in pattern_value:
                    # Check for duplicate based on amount/value
                    if isinstance(ai_item, dict) and isinstance(pattern_item, dict):
                        if ai_item.get('amount') == pattern_item.get('amount'):
                            is_duplicate = True
                            break
                        if ai_item.get('value') == pattern_item.get('value'):
                            is_duplicate = True
                            break

                if not is_duplicate:
                    pattern_value.append(ai_item)

            merged[key] = pattern_value

        elif isinstance(ai_value, dict):
            # Merge dictionaries
            pattern_value = merged.get(key, {})
            for k, v in ai_value.items():
                if k not in pattern_value or not pattern_value[k]:
                    pattern_value[k] = v
            merged[key] = pattern_value

        else:
            # For other types, prefer pattern result if it exists
            if key not in merged or not merged[key]:
                merged[key] = ai_value

    return merged


def generate_alerts(
    financial_data: Dict[str, Any],
    ownership_data: Dict[str, Any],
    legal_issues: Dict[str, Any],
    metrics: Dict[str, Any],
    fraudulent_conveyances: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Generate user-facing alerts about red flags in the document
    """
    alerts = []

    # Check for preferential treatments
    pref_treatments = metrics.get('preferential_treatments', [])
    if pref_treatments:
        for treatment in pref_treatments:
            if treatment.get('potential_fraud', False):
                alerts.append({
                    'level': 'CRITICAL',
                    'type': 'POTENTIAL_FRAUD',
                    'message': f"Settlement at {treatment['premium_multiple']}x premium to {treatment['beneficiary']} - HIGHLY SUSPICIOUS",
                    'details': f"Payment: ${treatment['payment_amount']:,.2f}, Original: ${treatment['original_claim']:,.2f}"
                })
            else:
                alerts.append({
                    'level': 'WARNING',
                    'type': 'PREFERENTIAL_TREATMENT',
                    'message': f"Preferential treatment detected: {treatment['beneficiary']} receiving {treatment['premium_multiple']}x",
                    'details': f"Excess payment: ${treatment['excess_payment']:,.2f}"
                })

    # Check for control disparities
    disparities = ownership_data.get('control_disparities', [])
    if disparities:
        for disparity in disparities:
            alerts.append({
                'level': 'WARNING',
                'type': 'CONTROL_DISPARITY',
                'message': f"{disparity['entity']} has {disparity['voting_control']}% voting control with only {disparity['economic_ownership']}% economic ownership",
                'details': f"Disparity: {disparity['disparity']}%"
            })

    # Check for precedent violations
    violations = legal_issues.get('precedent_violations', [])
    if violations:
        for violation in violations:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'LEGAL_VIOLATION',
                'message': f"Violates {violation['case']}",
                'details': f"Violation type: {violation.get('violation_type', 'Unknown')}"
            })

    # Check for fraudulent conveyances
    if fraudulent_conveyances:
        for conveyance in fraudulent_conveyances:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'FRAUDULENT_CONVEYANCE',
                'message': f"Suspicious transfer of ${conveyance['amount']:,.2f}",
                'details': f"Red flags: {', '.join([f for f in conveyance['red_flags'] if f])}"
            })

    # Check overall recovery rate
    recovery = metrics.get('recovery_analysis', {})
    if recovery.get('suspicious', False):
        alerts.append({
            'level': 'CRITICAL',
            'type': 'SUSPICIOUS_RECOVERY',
            'message': f"Total payments exceed total claims - recovery rate: {recovery.get('overall_recovery_rate', 0):.1%}",
            'details': "This is mathematically impossible in legitimate bankruptcy"
        })

    return alerts


@router.post("/analyze-bankruptcy")
async def analyze_bankruptcy_document(
    file: UploadFile = File(..., description="Bankruptcy PDF document to analyze"),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze a bankruptcy legal document with comprehensive financial and legal extraction

    This endpoint is specialized for bankruptcy cases and extracts:
    - ALL monetary amounts (claims, settlements, premiums)
    - Ownership structures (voting control vs economic ownership)
    - Share distributions and equity structures
    - Legal issues (case citations, precedent violations)
    - Authority limitations and jurisdictional problems

    This is NOT a generic text parser - it understands bankruptcy document structure.

    Returns comprehensive extraction including:
        - financial_data: All monetary amounts, percentages, shares, claims, settlements
        - ownership_structure: Voting control, economic ownership, control disparities
        - legal_issues: Case citations, statutory references, violations
        - summary_statistics: Aggregated counts and metrics
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for bankruptcy analysis"
            )

        # Read file contents
        file_contents = await file.read()

        # Validate PDF
        if not pdf_service.validate_pdf(file_contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        # Extract text from PDF
        extracted_text = pdf_service.extract_text_from_pdf(
            file_contents,
            file.filename
        )

        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract meaningful text from PDF"
            )

        # Process with bankruptcy-specific processor
        from ..src.services.bankruptcy_document_processor import bankruptcy_processor

        logger.info(f"Processing bankruptcy document: {file.filename}")

        bankruptcy_analysis = bankruptcy_processor.process_bankruptcy_document(
            extracted_text,
            file.filename
        )

        # Add file metadata
        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(file_contents),
            "text_length": len(extracted_text),
            "analyzed_at": datetime.now().isoformat(),
            "analysis_type": "bankruptcy_specialized",
            **bankruptcy_analysis
        }

        logger.info(f"Successfully analyzed bankruptcy document: {file.filename}")
        logger.info(f"Extracted: {bankruptcy_analysis['summary_statistics']}")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error analyzing bankruptcy document {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bankruptcy document analysis failed: {str(e)}"
        )


@router.post("/analyze-bankruptcy-text")
async def analyze_bankruptcy_text(
    request: AnalyzeTextRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze bankruptcy document text (already extracted) with comprehensive extraction

    This endpoint accepts already-extracted text and performs specialized bankruptcy analysis.

    Request body:
        - text: The document text to analyze
        - filename: Original filename (for context)
        - session_id: Frontend session ID (for persistence)
        - document_id: Optional document ID to update existing

    Returns comprehensive extraction including all financial and legal data.
    """
    try:
        text = request.text
        filename = request.filename
        session_id = request.session_id or str(uuid.uuid4())
        document_id = request.document_id or str(uuid.uuid4())

        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required and must be at least 10 characters"
            )

        # Process with bankruptcy-specific processor
        from ..src.services.bankruptcy_document_processor import bankruptcy_processor

        logger.info(f"Processing bankruptcy text: {filename}")

        bankruptcy_analysis = bankruptcy_processor.process_bankruptcy_document(
            text,
            filename
        )

        # Save to database with bankruptcy-specific data
        try:
            # SECURITY: Check if document exists AND belongs to current user
            existing_doc = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == current_user.user_id
            ).first()

            # Prepare bankruptcy-specific data for storage
            bankruptcy_data = {
                'financial_data': bankruptcy_analysis['financial_data'],
                'ownership_structure': bankruptcy_analysis['ownership_structure'],
                'legal_issues': bankruptcy_analysis['legal_issues'],
                'summary_statistics': bankruptcy_analysis['summary_statistics']
            }

            if existing_doc:
                # Update existing document (already verified ownership above)
                existing_doc.text_content = text
                existing_doc.document_type = "Bankruptcy Legal Document"
                existing_doc.analysis_data = bankruptcy_data
                existing_doc.financial_details = bankruptcy_analysis['financial_data']
                existing_doc.updated_at = datetime.utcnow()
                logger.info(f"Updated existing bankruptcy document: {document_id} for user {current_user.user_id}")
            else:
                # Create new document with user ownership
                document = Document(
                    id=document_id,
                    user_id=current_user.user_id,  # SECURITY: Associate document with user
                    session_id=session_id,
                    file_name=filename,
                    file_type="application/pdf",
                    file_size=len(text),
                    text_content=text,
                    summary=f"Bankruptcy document with {bankruptcy_analysis['summary_statistics']['total_monetary_amounts']} monetary amounts, "
                            f"{bankruptcy_analysis['summary_statistics']['total_claims']} claims, "
                            f"{bankruptcy_analysis['summary_statistics']['precedent_violations']} precedent violations",
                    document_type="Bankruptcy Legal Document",
                    analysis_data=bankruptcy_data,
                    financial_details=bankruptcy_analysis['financial_data']
                )
                db.add(document)
                logger.info(f"Created new bankruptcy document: {document_id} for user {current_user.user_id}")

            db.commit()
            logger.info(f"Saved bankruptcy document to database: {filename}")
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            db.rollback()
            # Continue even if DB save fails

        # Add metadata to response
        response = {
            "success": True,
            "document_id": document_id,
            "session_id": session_id,
            "filename": filename,
            "text_length": len(text),
            "analyzed_at": datetime.now().isoformat(),
            "analysis_type": "bankruptcy_specialized",
            **bankruptcy_analysis
        }

        logger.info(f"Successfully analyzed bankruptcy text from: {filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing bankruptcy text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bankruptcy text analysis failed: {str(e)}"
        )


class ProcessRecapDocumentRequest(BaseModel):
    file_path: str
    document_id: int
    description: str = "Court Document"
    page_count: int = None


@router.post("/process-recap-document")
async def process_recap_document(
    request: ProcessRecapDocumentRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process a RECAP document from app storage for analysis

    This endpoint:
    1. Reads the PDF from storage
    2. Extracts text
    3. Analyzes the document using dual AI service
    4. Saves to database with session tracking
    5. Returns the analysis results

    Args:
        request: Contains file_path, document_id, description, page_count

    Returns:
        Analysis results including text, summary, parties, dates, etc.
    """
    import os
    from pathlib import Path

    try:
        # Normalize file path (handle Windows backslashes)
        normalized_path = request.file_path.replace('\\', '/')
        file_path = Path(normalized_path)

        # If path is relative, make it absolute from backend directory
        if not file_path.is_absolute():
            file_path = Path(os.getcwd()) / normalized_path

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document file not found: {file_path}"
            )

        logger.info(f"Processing RECAP document: {request.description} (ID: {request.document_id})")

        # Step 1: Extract text from PDF
        try:
            import pdfplumber
            full_text = ""
            with pdfplumber.open(str(file_path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"

            logger.info(f"Extracted {len(full_text)} characters from RECAP document")

        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}, trying pypdf")
            # Fallback to pypdf
            with open(file_path, 'rb') as f:
                content = f.read()
            full_text = pdf_service.extract_text_from_pdf(content, file_path.name)

        if not full_text or len(full_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract meaningful text from PDF"
            )

        # Step 2: Analyze the document using dual AI service
        analysis_result = await dual_ai_service.analyze_document(
            full_text,
            filename=f"{request.description}.pdf",
            include_operational_details=True,
            include_financial_details=True
        )

        # Validate analysis response structure
        analysis_result = _validate_analysis_response(analysis_result)

        logger.info(f"Analysis complete for RECAP document {request.document_id}")

        # Step 3: Save to database
        document_id = f"recap_{request.document_id}"

        # SECURITY: Check if document already exists AND belongs to current user
        existing_doc = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.user_id
        ).first()

        if existing_doc:
            # Update existing document (already verified ownership above)
            existing_doc.text_content = full_text
            existing_doc.summary = analysis_result.get('summary')
            existing_doc.document_type = analysis_result.get('document_type')
            existing_doc.parties = analysis_result.get('parties', [])
            existing_doc.important_dates = analysis_result.get('key_dates', [])
            existing_doc.keywords = analysis_result.get('key_terms', [])
            existing_doc.analysis_data = analysis_result
            existing_doc.operational_details = analysis_result.get('operational_details', {})
            existing_doc.financial_details = analysis_result.get('financial_details', {})
        else:
            # Create new document with user ownership
            new_document = Document(
                id=document_id,
                user_id=current_user.user_id,  # SECURITY: Associate document with user
                file_name=f"{request.description}.pdf",
                file_type="application/pdf",
                text_content=full_text,
                summary=analysis_result.get('summary'),
                document_type=analysis_result.get('document_type'),
                parties=analysis_result.get('parties', []),
                important_dates=analysis_result.get('key_dates', []),
                keywords=analysis_result.get('key_terms', []),
                analysis_data=analysis_result,
                operational_details=analysis_result.get('operational_details', {}),
                financial_details=analysis_result.get('financial_details', {}),
                session_id=None,  # No session for RECAP documents
                upload_date=datetime.utcnow()
            )
            db.add(new_document)

        db.commit()

        # Step 4: Return formatted response for frontend
        return {
            "success": True,
            "document_id": document_id,
            "text": full_text,
            "summary": analysis_result.get('summary'),
            "parties": analysis_result.get('parties', []),
            "important_dates": [
                {"date": d.get("date", ""), "description": d.get("description", "")}
                for d in analysis_result.get('key_dates', [])
            ],
            "key_figures": analysis_result.get('financial_details', {}).get('key_figures', []),
            "keywords": analysis_result.get('key_terms', []),
            "analysis": analysis_result,
            "message": "RECAP document processed and analyzed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error processing RECAP document: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process RECAP document: {str(e)}"
        )


@router.get("/status")
async def get_service_status() -> Dict[str, Any]:
    """
    Get the status of document processing services

    Returns:
        - AI service status
        - Available models
        - Service configuration
    """
    import os

    openai_configured = bool(os.getenv('OPENAI_API_KEY'))
    claude_configured = bool(os.getenv('CLAUDE_API_KEY'))
    dual_ai_available = openai_configured and claude_configured

    return {
        "document_processing": "available",
        "pdf_extraction": "available",
        "bankruptcy_specialized": "available",
        "ai_analysis": "dual_ai_enhanced" if dual_ai_available else "single_ai" if (openai_configured or claude_configured) else "fallback_mode",
        "openai_configured": openai_configured,
        "claude_configured": claude_configured,
        "dual_ai_pipeline": dual_ai_available,
        "harvard_professor_mode": claude_configured,
        "supported_formats": ["pdf"],
        "max_file_size": "10MB",
        "ai_models": "OpenAI GPT-4 + Claude-3 Opus (Dual-AI)" if dual_ai_available else "Single AI fallback",
        "analysis_features": [
            "OpenAI heavy-lifting extraction",
            "Claude legal enhancement",
            "Harvard lawyer explanations",
            "3rd-grade simplification",
            "Bankruptcy-specialized financial extraction",
            "Ownership structure analysis",
            "Legal violation detection"
        ] if dual_ai_available else ["Basic AI analysis", "Bankruptcy-specialized extraction"],
        "bankruptcy_features": [
            "Comprehensive financial data extraction",
            "Voting control vs economic ownership analysis",
            "Settlement premium calculations",
            "Case law violation detection",
            "Statutory reference extraction",
            "Authority limitation identification"
        ],
        "status": "operational"
    }
