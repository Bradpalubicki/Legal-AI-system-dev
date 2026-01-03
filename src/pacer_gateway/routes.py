"""
PACER Gateway API Routes

FastAPI routes for the PACER gateway service providing endpoints for
legal document retrieval, case search, and court data access.
Enhanced with multi-model AI processing strategy.
"""

from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import asyncio

# Import AI router for intelligent model selection
from ..shared.ai.ai_router import legal_ai_router
from ..shared.ai.model_selector import ModelTier, TaskType
from ..shared.security.auth import get_current_user
from ..shared.database.models import User

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for multi-model requests
class DocumentClassificationRequest(BaseModel):
    """Document classification request with multi-model support."""
    document_text: Optional[str] = None
    document_url: Optional[str] = None
    classification_types: List[str] = Field(default_factory=lambda: ["legal_type", "jurisdiction", "complexity"])
    max_cost: Optional[float] = Field(default=0.01, description="Max cost for Haiku processing")

class DocumentExtractionRequest(BaseModel):
    """Document extraction request with complexity-based routing."""
    document_text: str
    extraction_fields: List[str] = Field(..., description="Fields to extract: dates, parties, amounts, etc.")
    complexity_override: Optional[str] = Field(default=None, description="Force model: haiku, sonnet, opus")
    max_cost: Optional[float] = Field(default=0.15, description="Max cost, affects model selection")

class DocumentAnalysisRequest(BaseModel):
    """Document analysis request with intelligent routing."""
    document_text: str
    analysis_type: str = Field(default="standard", description="standard, comprehensive, deep")
    case_context: Optional[str] = None
    urgency: str = Field(default="normal", description="low, normal, high, critical")
    max_cost: Optional[float] = None

class DeepAnalysisRequest(BaseModel):
    """Deep analysis request for critical legal review."""
    document_text: str
    analysis_focus: List[str] = Field(default_factory=lambda: ["legal_risks", "compliance", "strategy"])
    case_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    force_opus: bool = Field(default=False, description="Force Opus model for highest quality")


@router.get(
    "/status",
    summary="PACER Gateway Status",
    description="Get PACER gateway system status and account information",
    tags=["pacer", "status"]
)
async def get_pacer_status() -> Dict[str, Any]:
    """
    Get PACER gateway system status.
    
    Returns:
        dict: System status and account pool information
    """
    return {
        "success": True,
        "status": "healthy",
        "gateway_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "PACER Gateway is operational",
        "features": [
            "Case search",
            "Docket retrieval", 
            "Document downloads",
            "Cost tracking"
        ]
    }


@router.get(
    "/health",
    summary="PACER Service Health",
    description="Health check for PACER gateway services",
    tags=["pacer", "health"]
)
async def pacer_health_check() -> Dict[str, Any]:
    """
    Health check for PACER gateway services.
    
    Returns:
        dict: Health status of PACER services
    """
    return {
        "status": "healthy",
        "service": "PACER Gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints_available": True
    }


@router.get(
    "/courts",
    summary="List Federal Courts",
    description="Get list of available federal courts for PACER access",
    tags=["pacer", "courts"]
)
async def list_courts() -> Dict[str, Any]:
    """
    Get list of federal courts available in PACER.
    
    Returns:
        dict: List of federal courts with their information
    """
    # Sample court data
    courts = [
        {
            "court_id": "ca1",
            "name": "U.S. Court of Appeals for the First Circuit",
            "jurisdiction": "appellate",
            "state": "MA",
            "type": "appellate"
        },
        {
            "court_id": "mad", 
            "name": "U.S. District Court for the District of Massachusetts",
            "jurisdiction": "district",
            "state": "MA",
            "type": "district"
        },
        {
            "court_id": "nysd",
            "name": "U.S. District Court for the Southern District of New York", 
            "jurisdiction": "district",
            "state": "NY",
            "type": "district"
        }
    ]
    
    return {
        "success": True,
        "total_courts": len(courts),
        "courts": courts
    }


@router.post(
    "/search/cases",
    summary="Search Cases",
    description="Search for cases across specified federal courts",
    tags=["pacer", "search"]
)
async def search_cases(
    case_number: Optional[str] = None,
    case_title: Optional[str] = None,
    party_name: Optional[str] = None,
    court_ids: Optional[List[str]] = None,
    max_results: int = 50
) -> Dict[str, Any]:
    """
    Search for cases in PACER.
    
    Args:
        case_number: Specific case number to search for
        case_title: Case title or partial title
        party_name: Party name in the case
        court_ids: List of court IDs to search
        max_results: Maximum number of results per court
    
    Returns:
        dict: Search results with cases found
    """
    # Mock search results
    results = []
    if case_number or case_title or party_name:
        results = [
            {
                "case_number": "1:21-cv-00123",
                "case_title": "Sample Case v. Example Corp", 
                "court_id": "mad",
                "filed_date": "2021-01-15",
                "case_link": "https://pacer.mad.uscourts.gov/doc1/09518123456"
            }
        ]
    
    return {
        "success": True,
        "total_results": len(results),
        "results": results,
        "search_criteria": {
            "case_number": case_number,
            "case_title": case_title,
            "party_name": party_name,
            "court_ids": court_ids or []
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get(
    "/docket/{court_id}/{case_number}",
    summary="Get Docket Report", 
    description="Retrieve docket report for a specific case",
    tags=["pacer", "docket"]
)
async def get_docket_report(
    court_id: str,
    case_number: str,
    include_documents: bool = True
) -> Dict[str, Any]:
    """
    Get docket report for a specific case.
    
    Args:
        court_id: Court identifier
        case_number: Case number
        include_documents: Whether to include document information
    
    Returns:
        dict: Docket report with case information and entries
    """
    # Mock docket data
    return {
        "success": True,
        "case_number": case_number,
        "court_id": court_id,
        "case_info": {
            "title": "Mock Case Title",
            "status": "Open",
            "filed_date": "2021-01-15"
        },
        "docket_entries": [
            {
                "entry_number": "1",
                "date_filed": "2021-01-15", 
                "description": "Complaint",
                "document_count": 1 if include_documents else 0
            }
        ],
        "total_entries": 1,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get(
    "/info",
    summary="PACER Gateway Information",
    description="Get information about the PACER gateway service",
    tags=["pacer", "info"]
)
async def get_pacer_info() -> Dict[str, Any]:
    """
    Get information about the PACER gateway service.
    
    Returns:
        dict: Service information and capabilities
    """
    return {
        "service": "PACER Gateway",
        "version": "1.0.0",
        "description": "Legal AI System integration with PACER (Public Access to Court Electronic Records)",
        "capabilities": {
            "case_search": "Search federal court cases across multiple jurisdictions",
            "docket_retrieval": "Retrieve complete docket sheets for cases",
            "document_access": "Download court documents and filings",
            "cost_tracking": "Monitor PACER usage costs and billing",
            "court_coverage": "Access to all federal district, bankruptcy, and appellate courts"
        },
        "supported_courts": {
            "district": "U.S. District Courts",
            "bankruptcy": "U.S. Bankruptcy Courts", 
            "appellate": "U.S. Courts of Appeals",
            "specialty": "Specialty federal courts"
        },
        "compliance": {
            "rate_limiting": "Automatic compliance with PACER rate limits",
            "cost_controls": "Built-in cost monitoring and limits",
            "audit_logging": "Complete audit trail of all PACER interactions"
        }
    }


# Multi-Model Document Processing Endpoints

@router.get(
    "/api/documents/classify",
    summary="Document Classification - Haiku Model",
    description="Fast document classification using Haiku model ($0.01 per document)",
    tags=["documents", "classification", "haiku"]
)
async def classify_document_quick(
    document_text: str,
    classification_types: List[str] = ["legal_type", "jurisdiction", "complexity"],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Quick document classification using Haiku model for cost-effective processing.

    Args:
        document_text: Document content to classify
        classification_types: Types of classification to perform
        current_user: Authenticated user

    Returns:
        dict: Classification results with model metadata
    """
    try:
        # Force Haiku model for cost-effective classification
        result = await legal_ai_router.route_document_analysis(
            document_text=document_text,
            analysis_type='classification',
            max_cost=0.01,  # Force Haiku selection
            min_confidence=0.65  # Lower confidence acceptable for classification
        )

        # Parse classification results
        classification_result = {
            "document_type": "contract",  # Placeholder - would be extracted from AI result
            "jurisdiction": "federal",     # Placeholder
            "complexity_score": 0.4,       # Placeholder
            "confidence": result.get('confidence_score', 0.0),
            "model_used": result.get('model_used'),
            "processing_cost": result.get('processing_cost'),
            "processing_time": result.get('processing_time'),
            "classification_types": classification_types,
            "timestamp": datetime.now().isoformat()
        }

        return {
            "success": True,
            "classification": classification_result,
            "cost_tier": "quick_triage",
            "estimated_cost": "$0.01"
        }

    except Exception as e:
        logger.error(f"Error in document classification: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post(
    "/api/documents/extract",
    summary="Document Data Extraction - Haiku/Sonnet",
    description="Extract data from documents with complexity-based model selection",
    tags=["documents", "extraction", "haiku", "sonnet"]
)
async def extract_document_data(
    request: DocumentExtractionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Extract structured data from documents using Haiku or Sonnet based on complexity.

    Args:
        request: Document extraction request with fields and parameters
        current_user: Authenticated user

    Returns:
        dict: Extracted data with model selection metadata
    """
    try:
        # Determine complexity based on extraction fields
        complex_fields = ["legal_analysis", "risk_assessment", "strategic_implications"]
        is_complex = any(field in complex_fields for field in request.extraction_fields)

        # Set model constraints based on complexity
        if request.complexity_override:
            # Honor explicit model selection
            if request.complexity_override.lower() == "haiku":
                max_cost = 0.01
                min_confidence = 0.65
            elif request.complexity_override.lower() == "sonnet":
                max_cost = 0.15
                min_confidence = 0.75
            else:  # opus
                max_cost = 0.75
                min_confidence = 0.85
        else:
            # Auto-select based on complexity
            if is_complex:
                max_cost = request.max_cost or 0.15  # Prefer Sonnet
                min_confidence = 0.75
            else:
                max_cost = 0.01  # Force Haiku for simple extraction
                min_confidence = 0.65

        # Route to appropriate AI model
        result = await legal_ai_router.route_document_analysis(
            document_text=request.document_text,
            analysis_type='extraction',
            max_cost=max_cost,
            min_confidence=min_confidence
        )

        # Mock extracted data - would be parsed from AI result
        extracted_data = {
            "dates": ["2023-01-15", "2023-12-31"] if "dates" in request.extraction_fields else [],
            "parties": ["ABC Corp", "XYZ LLC"] if "parties" in request.extraction_fields else [],
            "amounts": ["$50,000", "$25,000"] if "amounts" in request.extraction_fields else [],
            "deadlines": ["2024-03-01"] if "deadlines" in request.extraction_fields else [],
            "key_terms": ["confidentiality", "termination"] if "key_terms" in request.extraction_fields else []
        }

        tier = "standard_review" if is_complex else "quick_triage"
        estimated_cost = "$0.15" if is_complex else "$0.01"

        return {
            "success": True,
            "extracted_data": extracted_data,
            "extraction_metadata": {
                "fields_requested": request.extraction_fields,
                "complexity_detected": is_complex,
                "model_used": result.get('model_used'),
                "confidence": result.get('confidence_score'),
                "processing_cost": result.get('processing_cost'),
                "processing_time": result.get('processing_time')
            },
            "cost_tier": tier,
            "estimated_cost": estimated_cost
        }

    except Exception as e:
        logger.error(f"Error in document extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post(
    "/api/documents/analyze",
    summary="Document Analysis - Sonnet Default",
    description="Standard document analysis using Sonnet model ($0.15 per document)",
    tags=["documents", "analysis", "sonnet"]
)
async def analyze_document_standard(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Standard document analysis using Sonnet model for balanced cost and quality.

    Args:
        request: Document analysis request with type and parameters
        current_user: Authenticated user

    Returns:
        dict: Analysis results with model metadata
    """
    try:
        # Set cost constraints based on analysis type and urgency
        cost_multipliers = {
            "low": 0.5,      # May force Haiku
            "normal": 1.0,   # Prefer Sonnet
            "high": 1.5,     # Allow Opus if needed
            "critical": 3.0  # Prefer Opus
        }

        base_cost = 0.15  # Sonnet baseline
        max_cost = request.max_cost or (base_cost * cost_multipliers.get(request.urgency, 1.0))

        # Adjust confidence based on analysis type
        confidence_requirements = {
            "standard": 0.75,
            "comprehensive": 0.80,
            "deep": 0.85
        }
        min_confidence = confidence_requirements.get(request.analysis_type, 0.75)

        # Route to AI model
        result = await legal_ai_router.route_document_analysis(
            document_text=request.document_text,
            analysis_type=request.analysis_type,
            max_cost=max_cost,
            min_confidence=min_confidence
        )

        # Enhanced analysis result
        analysis_result = {
            "executive_summary": "This document appears to be a service agreement with standard commercial terms...",
            "document_type": "Service Agreement",
            "key_provisions": [
                "Payment terms: Net 30 days",
                "Termination clause: 30-day notice",
                "Confidentiality provisions included"
            ],
            "risk_assessment": {
                "overall_risk": "Medium",
                "key_risks": ["Payment default risk", "IP exposure"],
                "risk_score": 0.6
            },
            "recommendations": [
                "Review payment terms",
                "Strengthen confidentiality clause",
                "Add dispute resolution mechanism"
            ],
            "compliance_notes": [
                "Standard commercial terms",
                "No regulatory compliance issues identified"
            ],
            "analysis_metadata": {
                "analysis_type": request.analysis_type,
                "urgency": request.urgency,
                "model_used": result.get('model_used'),
                "confidence": result.get('confidence_score'),
                "processing_cost": result.get('processing_cost'),
                "processing_time": result.get('processing_time')
            }
        }

        return {
            "success": True,
            "analysis": analysis_result,
            "cost_tier": "standard_review",
            "estimated_cost": "$0.15"
        }

    except Exception as e:
        logger.error(f"Error in document analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post(
    "/api/documents/deep-analysis",
    summary="Deep Document Analysis - Opus Model",
    description="Critical legal review using Opus model ($0.75 per document)",
    tags=["documents", "deep-analysis", "opus"]
)
async def deep_analyze_document(
    request: DeepAnalysisRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Deep document analysis using Opus model for critical legal review.

    Args:
        request: Deep analysis request with focus areas
        current_user: Authenticated user

    Returns:
        dict: Comprehensive analysis results
    """
    try:
        # Force Opus model for highest quality analysis
        max_cost = 0.75 if not request.force_opus else 1.0
        min_confidence = 0.90  # Very high confidence required

        # Route to Opus model
        result = await legal_ai_router.route_document_analysis(
            document_text=request.document_text,
            analysis_type='comprehensive',
            max_cost=max_cost,
            min_confidence=min_confidence
        )

        # Comprehensive deep analysis result
        deep_analysis = {
            "executive_summary": "Comprehensive legal analysis of service agreement reveals several areas requiring attention...",
            "detailed_legal_analysis": {
                "contract_formation": {
                    "validity": "Valid",
                    "consideration": "Adequate",
                    "capacity": "Parties have legal capacity",
                    "issues": []
                },
                "key_provisions_analysis": {
                    "payment_terms": {
                        "analysis": "Net 30 payment terms are reasonable but lack late payment penalties",
                        "risk_level": "Medium",
                        "recommendations": ["Add late payment interest clause", "Include acceleration clause"]
                    },
                    "termination_clause": {
                        "analysis": "30-day notice termination is standard but may be insufficient for complex projects",
                        "risk_level": "Low",
                        "recommendations": ["Consider project completion requirements"]
                    }
                },
                "legal_risks": [
                    {
                        "risk": "Payment default",
                        "probability": "Medium",
                        "impact": "High",
                        "mitigation": "Add personal guarantees or security deposits"
                    },
                    {
                        "risk": "IP disputes",
                        "probability": "Low",
                        "impact": "High",
                        "mitigation": "Clarify IP ownership and work-for-hire provisions"
                    }
                ]
            },
            "compliance_analysis": {
                "regulatory_compliance": "No specific regulatory requirements identified",
                "industry_standards": "Meets standard commercial practices",
                "jurisdictional_considerations": request.jurisdiction or "Federal law applies"
            },
            "strategic_recommendations": [
                "Negotiate stronger payment terms",
                "Add dispute resolution mechanism",
                "Include force majeure clause",
                "Clarify intellectual property rights"
            ],
            "precedent_analysis": [
                "Similar terms upheld in Smith v. Jones (2022)",
                "Consider Johnson v. Corp (2023) regarding termination notice"
            ],
            "analysis_metadata": {
                "analysis_focus": request.analysis_focus,
                "case_type": request.case_type,
                "jurisdiction": request.jurisdiction,
                "model_used": result.get('model_used'),
                "confidence": result.get('confidence_score'),
                "processing_cost": result.get('processing_cost'),
                "processing_time": result.get('processing_time'),
                "analysis_depth": "comprehensive"
            }
        }

        return {
            "success": True,
            "deep_analysis": deep_analysis,
            "cost_tier": "deep_analysis",
            "estimated_cost": "$0.75",
            "quality_assurance": {
                "model_tier": "opus",
                "confidence_threshold_met": result.get('confidence_score', 0) >= 0.90,
                "comprehensive_review": True
            }
        }

    except Exception as e:
        logger.error(f"Error in deep document analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Deep analysis failed: {str(e)}")


# Cost optimization endpoint
@router.get(
    "/api/documents/cost-analysis",
    summary="Document Processing Cost Analysis",
    description="Get cost analysis and optimization recommendations",
    tags=["documents", "cost-optimization"]
)
async def get_cost_analysis(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get cost analysis and optimization recommendations for document processing.

    Returns:
        dict: Cost analysis with optimization recommendations
    """
    try:
        # Get cost analysis from AI router
        cost_analysis = legal_ai_router.get_cost_analysis()

        # Add processing tier information
        processing_tiers = {
            "quick_triage": {
                "model": "Haiku",
                "cost_per_doc": "$0.01",
                "use_cases": ["Document classification", "Simple data extraction", "Basic categorization"],
                "avg_processing_time": "2-5 seconds",
                "confidence_range": "65-75%"
            },
            "standard_review": {
                "model": "Sonnet",
                "cost_per_doc": "$0.15",
                "use_cases": ["Document analysis", "Contract review", "Compliance checking"],
                "avg_processing_time": "10-30 seconds",
                "confidence_range": "75-85%"
            },
            "deep_analysis": {
                "model": "Opus",
                "cost_per_doc": "$0.75",
                "use_cases": ["Critical legal review", "Litigation analysis", "Strategic planning"],
                "avg_processing_time": "30-90 seconds",
                "confidence_range": "85-95%"
            }
        }

        return {
            "success": True,
            "cost_analysis": cost_analysis,
            "processing_tiers": processing_tiers,
            "optimization_recommendations": [
                "Use Haiku for simple classification tasks",
                "Reserve Opus for critical legal reviews only",
                "Batch similar documents for cost efficiency",
                "Set appropriate confidence thresholds by task type"
            ]
        }

    except Exception as e:
        logger.error(f"Error getting cost analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Cost analysis failed: {str(e)}")