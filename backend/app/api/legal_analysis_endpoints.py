"""
Legal Filing Analysis API Endpoints
REST API for legal document analysis, classification, and deadline calculation

All endpoints require authentication. Results are for educational purposes only.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
import logging

from .deps.auth import get_current_user, get_optional_user
from ..models.user import User

# Import legal analysis module
from ..src.services.legal_analysis import (
    # Analyzer
    LegalFilingAnalyzer,
    create_analyzer,
    FilingAnalysisResult,

    # Filing types
    get_filing_type,
    get_all_filing_types,
    get_filing_types_by_category,
    classify_filing_by_patterns,
    search_filing_types,
    FILING_CATEGORIES,

    # Extraction
    extract_case_number,
    extract_all_citations,
    extract_parties,
    extract_monetary_amounts,

    # Deadlines
    DeadlineCalculator,
    JurisdictionType,
    ServiceMethod,
    get_all_deadline_rules,
    get_deadline_rule,
    ResponseDeadlineCalculator,

    # Templates
    OutputFormat,
    SummaryStyle,
    TemplateContext,
    SummaryRenderer,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/legal-analysis", tags=["Legal Analysis"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class JurisdictionEnum(str, Enum):
    federal = "federal"
    california = "california"
    new_york = "new_york"
    texas = "texas"
    florida = "florida"
    illinois = "illinois"


class ServiceMethodEnum(str, Enum):
    electronic = "electronic"
    personal = "personal"
    mail = "mail"
    overnight = "overnight"


class OutputFormatEnum(str, Enum):
    json = "json"
    html = "html"
    markdown = "markdown"
    plain_text = "plain_text"


class AnalyzeFilingRequest(BaseModel):
    """Request model for filing analysis"""
    document_text: str = Field(..., min_length=50, description="The text content of the court filing")
    filing_date: Optional[str] = Field(None, description="Filing date in ISO format (YYYY-MM-DD)")
    case_number: Optional[str] = Field(None, description="Case number if known")
    jurisdiction: JurisdictionEnum = Field(JurisdictionEnum.federal, description="Court jurisdiction")
    service_method: ServiceMethodEnum = Field(ServiceMethodEnum.electronic, description="Method of service")
    include_ai_analysis: bool = Field(True, description="Whether to include AI-powered analysis")
    output_format: OutputFormatEnum = Field(OutputFormatEnum.json, description="Output format")

    class Config:
        json_schema_extra = {
            "example": {
                "document_text": "UNITED STATES DISTRICT COURT...",
                "filing_date": "2024-01-15",
                "jurisdiction": "federal",
                "service_method": "electronic",
                "include_ai_analysis": True,
                "output_format": "json"
            }
        }


class ClassifyFilingRequest(BaseModel):
    """Request model for filing classification"""
    document_text: str = Field(..., min_length=20, description="The text or title of the filing")


class ExtractDataRequest(BaseModel):
    """Request model for data extraction"""
    document_text: str = Field(..., min_length=50, description="The text content to extract from")
    extract_types: List[str] = Field(
        default=["case_numbers", "parties", "citations", "amounts"],
        description="Types of data to extract"
    )


class CalculateDeadlineRequest(BaseModel):
    """Request model for deadline calculation"""
    filing_type: str = Field(..., description="Filing type code (e.g., 'A1' for complaint)")
    trigger_date: str = Field(..., description="Trigger date in ISO format (YYYY-MM-DD)")
    jurisdiction: JurisdictionEnum = Field(JurisdictionEnum.federal)
    service_method: ServiceMethodEnum = Field(ServiceMethodEnum.electronic)


class AnalysisResponse(BaseModel):
    """Standard analysis response"""
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None
    disclaimer: str = "This analysis is for educational purposes only and does not constitute legal advice."


# =============================================================================
# MAIN ANALYSIS ENDPOINTS
# =============================================================================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_filing(
    request: AnalyzeFilingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive analysis of a legal court filing.

    This endpoint analyzes the document and returns:
    - Filing classification
    - Extracted data (parties, citations, amounts, etc.)
    - Calculated deadlines
    - Risk assessment
    - Executive summary

    **Note:** All information is for educational purposes only.
    """
    try:
        # Map jurisdiction
        jurisdiction_map = {
            JurisdictionEnum.federal: JurisdictionType.FEDERAL,
            JurisdictionEnum.california: JurisdictionType.STATE_CA,
            JurisdictionEnum.new_york: JurisdictionType.STATE_NY,
            JurisdictionEnum.texas: JurisdictionType.STATE_TX,
            JurisdictionEnum.florida: JurisdictionType.STATE_FL,
            JurisdictionEnum.illinois: JurisdictionType.STATE_IL,
        }

        service_map = {
            ServiceMethodEnum.electronic: ServiceMethod.ELECTRONIC,
            ServiceMethodEnum.personal: ServiceMethod.PERSONAL,
            ServiceMethodEnum.mail: ServiceMethod.MAIL,
            ServiceMethodEnum.overnight: ServiceMethod.OVERNIGHT,
        }

        # Create analyzer (without AI service for now - can be added later)
        analyzer = create_analyzer(
            jurisdiction=request.jurisdiction.value,
            enable_ai=request.include_ai_analysis
        )

        # Prepare metadata and options
        metadata = {}
        if request.filing_date:
            metadata['filing_date'] = request.filing_date
        if request.case_number:
            metadata['case_number'] = request.case_number

        options = {
            'jurisdiction': jurisdiction_map[request.jurisdiction],
            'service_method': service_map[request.service_method],
            'include_ai': request.include_ai_analysis
        }

        # Perform analysis
        result = await analyzer.analyze(
            document_text=request.document_text,
            metadata=metadata,
            options=options
        )

        # Format output based on requested format
        if request.output_format == OutputFormatEnum.json:
            return AnalysisResponse(
                success=True,
                data=result.to_dict()
            )
        else:
            # Create template context
            context = TemplateContext.from_analysis_result(result)

            format_map = {
                OutputFormatEnum.html: OutputFormat.HTML,
                OutputFormatEnum.markdown: OutputFormat.MARKDOWN,
                OutputFormatEnum.plain_text: OutputFormat.PLAIN_TEXT,
            }

            formatted_output = SummaryRenderer.render(
                context,
                format_map.get(request.output_format, OutputFormat.HTML)
            )

            return AnalysisResponse(
                success=True,
                data={
                    "analysis_id": result.analysis_id,
                    "format": request.output_format.value,
                    "content": formatted_output
                }
            )

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify")
async def classify_filing(
    request: ClassifyFilingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Classify a legal filing by its type.

    Returns the most likely filing type with confidence score
    and alternative classifications.
    """
    try:
        matches = classify_filing_by_patterns(request.document_text)

        if not matches:
            return {
                "success": True,
                "classification": {
                    "filing_type_code": "X99",
                    "filing_type_name": "Unclassified",
                    "category": "X",
                    "confidence": 0.0,
                },
                "alternatives": [],
                "disclaimer": "Classification is for educational purposes only."
            }

        primary = matches[0]
        filing_type = get_filing_type(primary['code'])

        return {
            "success": True,
            "classification": {
                "filing_type_code": primary['code'],
                "filing_type_name": primary.get('name', filing_type.name if filing_type else 'Unknown'),
                "category": filing_type.category if filing_type else 'X',
                "category_name": FILING_CATEGORIES.get(filing_type.category, 'Unknown') if filing_type else 'Unknown',
                "confidence": primary.get('confidence', 0.8),
                "practice_areas": list(filing_type.practice_areas) if filing_type else [],
            },
            "alternatives": [
                {
                    "filing_type_code": m['code'],
                    "filing_type_name": m.get('name', ''),
                    "confidence": m.get('confidence', 0)
                }
                for m in matches[1:5]
            ],
            "disclaimer": "Classification is for educational purposes only."
        }

    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_data(
    request: ExtractDataRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Extract structured data from legal document text.

    Extracts case numbers, parties, citations, monetary amounts, and more.
    """
    try:
        result = {}

        if "case_numbers" in request.extract_types:
            cn = extract_case_number(request.document_text)
            result["case_numbers"] = [{
                "full_number": cn.full_number,
                "court_type": cn.court_type,
                "year": cn.year,
                "case_type": cn.case_type,
                "district": cn.district
            }] if cn else []

        if "parties" in request.extract_types:
            parties = extract_parties(request.document_text)
            result["parties"] = [
                {
                    "name": p.name,
                    "role": p.role,
                    "entity_type": p.entity_type,
                    "state": p.state
                }
                for p in parties
            ]

        if "citations" in request.extract_types:
            citations = extract_all_citations(request.document_text)
            result["citations"] = {
                "case_law": [c.__dict__ for c in citations if c.citation_type == 'case_law'][:20],
                "statutes": [c.__dict__ for c in citations if c.citation_type == 'statute'][:20],
                "rules": [c.__dict__ for c in citations if c.citation_type == 'rule'][:20],
            }

        if "amounts" in request.extract_types:
            amounts = extract_monetary_amounts(request.document_text)
            result["monetary_amounts"] = [
                {
                    "value": a.value,
                    "currency": a.currency,
                    "type": a.amount_type,
                    "qualifier": a.qualifier
                }
                for a in amounts
            ]

        return {
            "success": True,
            "extracted_data": result,
            "disclaimer": "Extraction is for educational purposes only."
        }

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deadlines/calculate")
async def calculate_deadlines(
    request: CalculateDeadlineRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate response deadlines for a filing type.

    Applies FRCP 6(a) day calculation rules including:
    - Weekend/holiday adjustments
    - Service method additions
    - Jurisdiction-specific rules
    """
    try:
        # Parse trigger date
        try:
            trigger = datetime.fromisoformat(request.trigger_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        # Map jurisdiction
        jurisdiction_map = {
            JurisdictionEnum.federal: JurisdictionType.FEDERAL,
            JurisdictionEnum.california: JurisdictionType.STATE_CA,
            JurisdictionEnum.new_york: JurisdictionType.STATE_NY,
            JurisdictionEnum.texas: JurisdictionType.STATE_TX,
            JurisdictionEnum.florida: JurisdictionType.STATE_FL,
            JurisdictionEnum.illinois: JurisdictionType.STATE_IL,
        }

        service_map = {
            ServiceMethodEnum.electronic: ServiceMethod.ELECTRONIC,
            ServiceMethodEnum.personal: ServiceMethod.PERSONAL,
            ServiceMethodEnum.mail: ServiceMethod.MAIL,
            ServiceMethodEnum.overnight: ServiceMethod.OVERNIGHT,
        }

        jurisdiction = jurisdiction_map[request.jurisdiction]
        service_method = service_map[request.service_method]

        # Calculate based on filing type
        deadlines = []
        filing_code = request.filing_type.upper()

        if filing_code.startswith('A'):
            # Complaint - answer deadline
            deadline = ResponseDeadlineCalculator.calculate_answer_deadline(
                trigger, jurisdiction, waiver=False, service_method=service_method
            )
            if deadline:
                deadlines.append({
                    "description": "Answer/Responsive Pleading Due",
                    "date": deadline.adjusted_deadline.isoformat(),
                    "original_date": deadline.original_deadline.isoformat(),
                    "rule_basis": deadline.rule_applied,
                    "is_jurisdictional": False,
                    "is_extended": deadline.is_extended,
                    "extension_reason": deadline.extension_reason,
                    "calculation_notes": deadline.calculation_notes,
                    "days_until": (deadline.adjusted_deadline - date.today()).days
                })

        elif filing_code.startswith('C') or filing_code.startswith('E'):
            # Motion - opposition deadline
            calc = DeadlineCalculator(jurisdiction)
            opposition_days = 21 if jurisdiction == JurisdictionType.FEDERAL else 14
            deadline_date = calc.add_business_days(trigger, opposition_days)
            deadlines.append({
                "description": "Opposition Due",
                "date": deadline_date.isoformat(),
                "rule_basis": "Local Rule / FRCP 56",
                "is_jurisdictional": False,
                "days_until": (deadline_date - date.today()).days
            })

        elif filing_code.startswith('D'):
            # Discovery - response deadline
            deadline = ResponseDeadlineCalculator.calculate_discovery_response_deadline(
                trigger, jurisdiction, service_method
            )
            if deadline:
                deadlines.append({
                    "description": "Discovery Response Due",
                    "date": deadline.adjusted_deadline.isoformat(),
                    "rule_basis": deadline.rule_applied,
                    "is_jurisdictional": False,
                    "days_until": (deadline.adjusted_deadline - date.today()).days
                })

        elif filing_code.startswith('P'):
            # Appeal - briefing deadlines
            deadline = ResponseDeadlineCalculator.calculate_appeal_deadline(
                trigger, jurisdiction
            )
            if deadline:
                deadlines.append({
                    "description": "Cross-Appeal Deadline",
                    "date": deadline.adjusted_deadline.isoformat(),
                    "rule_basis": deadline.rule_applied,
                    "is_jurisdictional": True,
                    "days_until": (deadline.adjusted_deadline - date.today()).days
                })

        return {
            "success": True,
            "filing_type": request.filing_type,
            "trigger_date": request.trigger_date,
            "jurisdiction": request.jurisdiction.value,
            "service_method": request.service_method.value,
            "deadlines": deadlines,
            "disclaimer": "Deadline calculations are for educational purposes only. Verify all deadlines with applicable rules."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deadline calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# REFERENCE DATA ENDPOINTS
# =============================================================================

@router.get("/filing-types")
async def list_filing_types(
    category: Optional[str] = Query(None, description="Filter by category code (A-S, P, R, X)"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: User = Depends(get_optional_user)
):
    """
    Get list of all supported filing types.

    Optionally filter by category or search by name/description.
    """
    try:
        if search:
            filing_types = search_filing_types(search)
        elif category:
            filing_types = get_filing_types_by_category(category.upper())
        else:
            filing_types = list(get_all_filing_types().values())

        return {
            "success": True,
            "count": len(filing_types),
            "categories": FILING_CATEGORIES,
            "filing_types": [
                {
                    "code": ft.code,
                    "name": ft.name,
                    "category": ft.category,
                    "category_name": FILING_CATEGORIES.get(ft.category, 'Unknown'),
                    "description": ft.description,
                    "practice_areas": list(ft.practice_areas),
                    "response_deadline_days": ft.response_deadline_days
                }
                for ft in filing_types
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching filing types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filing-types/{code}")
async def get_filing_type_details(
    code: str,
    current_user: User = Depends(get_optional_user)
):
    """Get detailed information about a specific filing type."""
    filing_type = get_filing_type(code.upper())

    if not filing_type:
        raise HTTPException(status_code=404, detail=f"Filing type '{code}' not found")

    return {
        "success": True,
        "filing_type": {
            "code": filing_type.code,
            "name": filing_type.name,
            "category": filing_type.category,
            "category_name": FILING_CATEGORIES.get(filing_type.category, 'Unknown'),
            "description": filing_type.description,
            "patterns": filing_type.trigger_patterns,
            "required_fields": filing_type.required_fields,
            "practice_areas": list(filing_type.practice_areas),
            "response_deadline_days": filing_type.response_deadline_days,
        }
    }


@router.get("/deadline-rules")
async def list_deadline_rules(
    jurisdiction: Optional[JurisdictionEnum] = Query(None),
    current_user: User = Depends(get_optional_user)
):
    """
    Get list of all deadline calculation rules.

    Rules include FRCP and state-specific deadlines.
    """
    try:
        all_rules = get_all_deadline_rules()

        # Filter by jurisdiction if specified
        if jurisdiction:
            jurisdiction_map = {
                JurisdictionEnum.federal: JurisdictionType.FEDERAL,
                JurisdictionEnum.california: JurisdictionType.STATE_CA,
                JurisdictionEnum.new_york: JurisdictionType.STATE_NY,
                JurisdictionEnum.texas: JurisdictionType.STATE_TX,
                JurisdictionEnum.florida: JurisdictionType.STATE_FL,
                JurisdictionEnum.illinois: JurisdictionType.STATE_IL,
            }
            target_jurisdiction = jurisdiction_map[jurisdiction]
            all_rules = {
                k: v for k, v in all_rules.items()
                if v.jurisdiction == target_jurisdiction
            }

        return {
            "success": True,
            "count": len(all_rules),
            "rules": [
                {
                    "rule_id": rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "base_days": rule.base_days,
                    "deadline_type": rule.deadline_type.value,
                    "jurisdiction": rule.jurisdiction.value,
                    "rule_citation": rule.rule_citation,
                    "mail_service_days": rule.mail_service_days,
                    "notes": rule.notes
                }
                for rule_id, rule in all_rules.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching deadline rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_optional_user)
):
    """Get list of all filing categories."""
    return {
        "success": True,
        "categories": [
            {"code": code, "name": name}
            for code, name in FILING_CATEGORIES.items()
        ]
    }


# =============================================================================
# FORMATTED OUTPUT ENDPOINTS
# =============================================================================

@router.post("/analyze/html", response_class=HTMLResponse)
async def analyze_filing_html(
    request: AnalyzeFilingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze filing and return HTML-formatted report.
    """
    request.output_format = OutputFormatEnum.html
    result = await analyze_filing(request, current_user)

    if result.success and result.data:
        return HTMLResponse(content=result.data.get("content", ""))
    else:
        raise HTTPException(status_code=500, detail=result.error)


@router.post("/analyze/markdown", response_class=PlainTextResponse)
async def analyze_filing_markdown(
    request: AnalyzeFilingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze filing and return Markdown-formatted report.
    """
    request.output_format = OutputFormatEnum.markdown
    result = await analyze_filing(request, current_user)

    if result.success and result.data:
        return PlainTextResponse(
            content=result.data.get("content", ""),
            media_type="text/markdown"
        )
    else:
        raise HTTPException(status_code=500, detail=result.error)


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def health_check():
    """Check if the legal analysis service is operational."""
    try:
        # Quick test of core functionality
        filing_types = get_all_filing_types()
        rules = get_all_deadline_rules()

        return {
            "status": "healthy",
            "service": "legal-analysis",
            "filing_types_loaded": len(filing_types),
            "deadline_rules_loaded": len(rules),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "legal-analysis",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
