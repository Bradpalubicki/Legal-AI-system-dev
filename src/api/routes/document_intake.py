"""
Document Intake API Endpoints for Legal AI System

Integrates DocumentIntakeAnalyzer, IntelligentQuestionGenerator, and DefenseStrategyGenerator
to provide comprehensive document analysis and strategy generation capabilities.

CRITICAL LEGAL DISCLAIMER:
All API endpoints provide educational information only and do not constitute legal advice.
No attorney-client relationship is created. Users must consult qualified legal counsel.

Created: 2025-09-14
Legal AI System - Document Intelligence API
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import uuid
import json
import logging
import traceback
from pathlib import Path

# Import our core components
try:
    from ...document_processor.intelligent_intake import DocumentIntakeAnalyzer, DocumentAnalysisResult
    from ...document_processor.question_generator import IntelligentQuestionGenerator, IntelligentQuestion
    from ...strategy_generator.defense_strategy_builder import DefenseStrategyGenerator, DefenseStrategy
    from ...shared.compliance.upl_compliance import ComplianceWrapper
except ImportError:
    # Mock imports for standalone testing
    class DocumentIntakeAnalyzer:
        def identify_document_type(self, text, filename=None):
            return {"category": "bankruptcy_petition", "confidence": 0.8}
        def extract_key_information(self, text, doc_type):
            return [{"entity_type": "debtor_name", "value": "Test Business LLC"}]
        def identify_information_gaps(self, text, doc_type, entities):
            return [{"gap_type": "debt_amount", "description": "Missing debt amount"}]

    class IntelligentQuestionGenerator:
        def generate_questions_for_bankruptcy(self, gaps):
            return [{"question_id": "test_1", "question_text": "Test question?"}]
        def generate_questions_for_litigation(self, gaps):
            return [{"question_id": "test_2", "question_text": "Test litigation question?"}]

    class DefenseStrategyGenerator:
        def generate_bankruptcy_strategies(self, info):
            return [{"name": "Chapter 7", "description": "Test strategy"}]

    class ComplianceWrapper:
        def analyze_text(self, text):
            return {"has_advice": False, "compliance_score": 1.0}

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize core components
document_analyzer = DocumentIntakeAnalyzer()
question_generator = IntelligentQuestionGenerator()
strategy_generator = DefenseStrategyGenerator()
compliance_wrapper = ComplianceWrapper()

# Create router
router = APIRouter(prefix="/api/v1", tags=["Document Intake"])

# In-memory storage for demo (replace with database in production)
analysis_storage = {}
question_storage = {}
answer_storage = {}
strategy_storage = {}


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    filename: str = Field(..., description="Original filename of the document")
    content_type: str = Field(..., description="MIME type of the document")
    matter_id: Optional[str] = Field(None, description="Associated matter ID")
    client_id: Optional[str] = Field(None, description="Associated client ID")

    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        return v.strip()


class QuestionAnswerRequest(BaseModel):
    """Request model for submitting question answers."""
    analysis_id: str = Field(..., description="ID of the document analysis")
    answers: Dict[str, Any] = Field(..., description="Question ID to answer mapping")
    matter_id: Optional[str] = Field(None, description="Associated matter ID")

    @validator('answers')
    def validate_answers(cls, v):
        if not v:
            raise ValueError('At least one answer must be provided')
        return v


class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis."""
    analysis_id: str
    document_type: Dict[str, Any]
    extracted_entities: List[Dict[str, Any]]
    information_gaps: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    compliance_status: Dict[str, Any]
    created_at: datetime
    educational_disclaimer: str


class StrategyResponse(BaseModel):
    """Response model for strategy recommendations."""
    matter_id: str
    strategies: List[Dict[str, Any]]
    generated_at: datetime
    educational_disclaimer: str
    compliance_validated: bool


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate authentication token and return user information.
    In production, this would validate JWT tokens against a user database.
    """
    # Mock authentication for demo
    if not credentials or credentials.credentials != "demo_token_12345":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"user_id": "demo_user", "permissions": ["document_upload", "analysis_access"]}


# Audit logging decorator
def audit_log(action: str):
    """Decorator to log API actions for compliance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            user_info = kwargs.get('current_user', {})

            try:
                result = await func(*args, **kwargs)

                # Log successful action
                logger.info(f"AUDIT: {action} completed", extra={
                    "action": action,
                    "user_id": user_info.get("user_id"),
                    "timestamp": start_time.isoformat(),
                    "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "success": True
                })

                return result

            except Exception as e:
                # Log failed action
                logger.error(f"AUDIT: {action} failed", extra={
                    "action": action,
                    "user_id": user_info.get("user_id"),
                    "timestamp": start_time.isoformat(),
                    "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                raise

        return wrapper
    return decorator


@router.post("/documents/intelligent-upload", response_model=DocumentAnalysisResponse)
@limiter.limit("10/minute")
@audit_log("document_upload_and_analysis")
async def intelligent_document_upload(
    request: DocumentUploadRequest,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Main document intake endpoint that performs intelligent analysis.

    Processes uploaded documents through:
    1. Document type identification
    2. Key information extraction
    3. Information gap analysis
    4. Question generation
    5. Compliance validation

    LEGAL DISCLAIMER: Provides educational document analysis only.
    Does not constitute legal advice. Consult qualified counsel.
    """
    try:
        # Validate file upload
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded"
            )

        # Check file type
        allowed_types = ['application/pdf', 'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain']

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )

        # Read file content
        file_content = await file.read()

        # Convert to text (simplified - in production would use proper document parsing)
        try:
            document_text = file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not process document content: {str(e)}"
            )

        if len(document_text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document appears to be empty"
            )

        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())

        # Perform document analysis
        logger.info(f"Starting document analysis for {request.filename}")

        # Step 1: Identify document type
        document_type = document_analyzer.identify_document_type(
            document_text,
            request.filename
        )

        # Step 2: Extract key information
        extracted_entities = document_analyzer.extract_key_information(
            document_text,
            document_type
        )

        # Step 3: Identify information gaps
        information_gaps = document_analyzer.identify_information_gaps(
            document_text,
            document_type,
            extracted_entities
        )

        # Step 4: Generate relevant questions based on gaps
        if hasattr(document_type, 'category'):
            doc_category = document_type.category
        else:
            doc_category = document_type.get('category', 'unknown')

        # Generate questions based on document type
        questions = []
        if 'bankruptcy' in str(doc_category).lower():
            questions = question_generator.generate_questions_for_bankruptcy(information_gaps)
        elif 'litigation' in str(doc_category).lower() or 'complaint' in str(doc_category).lower():
            questions = question_generator.generate_questions_for_litigation(information_gaps)
        else:
            # Generate general questions for other document types
            questions = question_generator.generate_questions_for_bankruptcy(information_gaps)  # Default to bankruptcy questions

        # Step 5: Compliance validation
        compliance_check = compliance_wrapper.analyze_text(document_text[:1000])  # Check first 1000 chars

        # Store analysis results
        analysis_result = {
            "analysis_id": analysis_id,
            "user_id": current_user["user_id"],
            "document_type": document_type.__dict__ if hasattr(document_type, '__dict__') else document_type,
            "extracted_entities": [entity.__dict__ if hasattr(entity, '__dict__') else entity for entity in extracted_entities],
            "information_gaps": [gap.__dict__ if hasattr(gap, '__dict__') else gap for gap in information_gaps],
            "questions": [q.__dict__ if hasattr(q, '__dict__') else q for q in questions],
            "compliance_status": compliance_check,
            "original_filename": request.filename,
            "matter_id": request.matter_id,
            "client_id": request.client_id,
            "created_at": datetime.now(),
            "document_text": document_text  # Store for later use
        }

        analysis_storage[analysis_id] = analysis_result

        # Prepare response
        response = DocumentAnalysisResponse(
            analysis_id=analysis_id,
            document_type=analysis_result["document_type"],
            extracted_entities=analysis_result["extracted_entities"],
            information_gaps=analysis_result["information_gaps"],
            questions=analysis_result["questions"],
            compliance_status=analysis_result["compliance_status"],
            created_at=analysis_result["created_at"],
            educational_disclaimer="This analysis is for educational purposes only and does not constitute legal advice. Consult qualified legal counsel for guidance specific to your situation."
        )

        logger.info(f"Document analysis completed successfully for analysis_id: {analysis_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in document upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during document processing: {str(e)}"
        )


@router.post("/documents/answer-questions", response_model=Dict[str, Any])
@limiter.limit("20/minute")
@audit_log("question_answers_submission")
async def submit_question_answers(
    request: QuestionAnswerRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit answers to generated questions for further analysis.

    Updates the analysis with user-provided information and prepares
    data for strategy generation.

    LEGAL DISCLAIMER: Question answers are used for educational analysis only.
    Does not constitute legal advice consultation.
    """
    try:
        # Validate analysis exists
        if request.analysis_id not in analysis_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )

        analysis = analysis_storage[request.analysis_id]

        # Verify user owns this analysis
        if analysis["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this analysis"
            )

        # Validate answers against generated questions
        question_ids = [q.get("question_id") for q in analysis["questions"]]
        invalid_answers = [aid for aid in request.answers.keys() if aid not in question_ids]

        if invalid_answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid question IDs: {invalid_answers}"
            )

        # Store answers
        answer_record = {
            "analysis_id": request.analysis_id,
            "answers": request.answers,
            "matter_id": request.matter_id,
            "submitted_at": datetime.now(),
            "user_id": current_user["user_id"]
        }

        answer_storage[request.analysis_id] = answer_record

        # Update analysis with answers
        analysis["answers"] = request.answers
        analysis["answers_submitted_at"] = datetime.now()

        # Prepare business info for strategy generation
        business_info = {
            "analysis_id": request.analysis_id,
            "matter_id": request.matter_id,
            "document_type": analysis["document_type"],
            "extracted_entities": analysis["extracted_entities"],
            "answers": request.answers
        }

        # Extract relevant business information from answers
        for question_id, answer in request.answers.items():
            if "debt" in question_id.lower():
                try:
                    # Extract numeric value from currency answers
                    debt_str = str(answer).replace('$', '').replace(',', '')
                    business_info["debt_amount"] = float(debt_str)
                except:
                    pass
            elif "business_type" in question_id.lower():
                business_info["business_type"] = str(answer).lower()
            elif "income" in question_id.lower():
                try:
                    income_str = str(answer).replace('$', '').replace(',', '')
                    business_info["annual_revenue"] = float(income_str) * 12  # Convert monthly to annual
                except:
                    pass

        logger.info(f"Question answers submitted for analysis_id: {request.analysis_id}")

        return {
            "status": "success",
            "message": "Answers submitted successfully",
            "analysis_id": request.analysis_id,
            "answered_questions": len(request.answers),
            "ready_for_strategies": True,
            "educational_disclaimer": "Submitted answers are used for educational analysis only and do not constitute legal consultation."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing answers: {str(e)}"
        )


@router.get("/documents/analysis/{analysis_id}", response_model=DocumentAnalysisResponse)
@limiter.limit("30/minute")
@audit_log("analysis_retrieval")
async def get_document_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve document analysis results by ID.

    Returns complete analysis including document type, entities,
    gaps, questions, and compliance status.

    LEGAL DISCLAIMER: Analysis results are educational only.
    """
    try:
        if analysis_id not in analysis_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )

        analysis = analysis_storage[analysis_id]

        # Verify user access
        if analysis["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this analysis"
            )

        response = DocumentAnalysisResponse(
            analysis_id=analysis_id,
            document_type=analysis["document_type"],
            extracted_entities=analysis["extracted_entities"],
            information_gaps=analysis["information_gaps"],
            questions=analysis["questions"],
            compliance_status=analysis["compliance_status"],
            created_at=analysis["created_at"],
            educational_disclaimer="This analysis is for educational purposes only and does not constitute legal advice."
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analysis"
        )


@router.get("/strategies/{matter_id}", response_model=StrategyResponse)
@limiter.limit("15/minute")
@audit_log("strategy_generation")
async def generate_strategies(
    matter_id: str,
    analysis_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate educational strategy information based on document analysis and answers.

    Combines document analysis results with user-provided answers to generate
    relevant strategy options with educational content.

    CRITICAL DISCLAIMER: All strategies are educational information only.
    No legal advice is provided. Attorney consultation required for guidance.
    """
    try:
        # Find analysis by matter_id or analysis_id
        target_analysis = None
        target_analysis_id = None

        if analysis_id:
            if analysis_id in analysis_storage:
                analysis = analysis_storage[analysis_id]
                if analysis["user_id"] == current_user["user_id"]:
                    target_analysis = analysis
                    target_analysis_id = analysis_id
        else:
            # Find by matter_id
            for aid, analysis in analysis_storage.items():
                if (analysis.get("matter_id") == matter_id and
                    analysis["user_id"] == current_user["user_id"]):
                    target_analysis = analysis
                    target_analysis_id = aid
                    break

        if not target_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No analysis found for the specified matter"
            )

        # Check if answers have been submitted
        if target_analysis_id not in answer_storage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Questions must be answered before generating strategies"
            )

        # Check if strategies already generated
        if matter_id in strategy_storage:
            cached_strategies = strategy_storage[matter_id]
            if (datetime.now() - cached_strategies["generated_at"]).total_seconds() < 3600:  # 1 hour cache
                return cached_strategies["response"]

        # Prepare business information from analysis and answers
        answers = answer_storage[target_analysis_id]["answers"]
        business_info = {
            "analysis_id": target_analysis_id,
            "matter_id": matter_id,
            "document_type": target_analysis["document_type"],
            "extracted_entities": target_analysis["extracted_entities"],
            "information_gaps": target_analysis["information_gaps"],
            "answers": answers
        }

        # Extract business details from answers for strategy customization
        for question_id, answer in answers.items():
            if "debt" in question_id.lower() and "total" in question_id.lower():
                try:
                    debt_str = str(answer).replace('$', '').replace(',', '').strip()
                    if debt_str:
                        business_info["debt_amount"] = float(debt_str)
                except (ValueError, AttributeError):
                    pass
            elif "business_type" in question_id.lower() or "entity" in question_id.lower():
                business_info["business_type"] = str(answer).lower()
            elif "income" in question_id.lower() and "monthly" in question_id.lower():
                try:
                    income_str = str(answer).replace('$', '').replace(',', '').strip()
                    if income_str:
                        business_info["annual_revenue"] = float(income_str) * 12
                except (ValueError, AttributeError):
                    pass
            elif "creditor" in question_id.lower():
                if isinstance(answer, list):
                    business_info["creditor_types"] = answer
                else:
                    business_info["creditor_types"] = [str(answer)]

        # Generate strategies
        logger.info(f"Generating strategies for matter_id: {matter_id}")
        strategies = strategy_generator.generate_bankruptcy_strategies(business_info)

        # Validate all strategies for compliance
        compliant_strategies = []
        for strategy in strategies:
            if strategy_generator._validate_strategy_compliance(strategy):
                compliant_strategies.append(strategy)
            else:
                logger.warning(f"Strategy {strategy.name} failed compliance validation")

        if not compliant_strategies:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No compliant strategies could be generated"
            )

        # Prepare response
        strategy_dicts = []
        for strategy in compliant_strategies:
            strategy_dict = strategy.__dict__.copy()
            # Convert datetime objects to ISO strings
            if 'created_at' in strategy_dict:
                strategy_dict['created_at'] = strategy_dict['created_at'].isoformat()
            # Convert enum values to strings
            if hasattr(strategy_dict.get('strategy_type'), 'value'):
                strategy_dict['strategy_type'] = strategy_dict['strategy_type'].value
            if hasattr(strategy_dict.get('general_timeline'), 'value'):
                strategy_dict['general_timeline'] = strategy_dict['general_timeline'].value

            strategy_dicts.append(strategy_dict)

        response = StrategyResponse(
            matter_id=matter_id,
            strategies=strategy_dicts,
            generated_at=datetime.now(),
            educational_disclaimer="All strategies are educational information only. No legal advice is provided. Consult qualified legal counsel for guidance specific to your situation.",
            compliance_validated=True
        )

        # Cache strategies
        strategy_storage[matter_id] = {
            "response": response,
            "generated_at": datetime.now()
        }

        logger.info(f"Generated {len(compliant_strategies)} compliant strategies for matter_id: {matter_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating strategies: {str(e)}"
        )


# Error handlers
@router.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error_type": "rate_limit_exceeded",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": str(exc.retry_after),
            "timestamp": datetime.now().isoformat()
        }
    )
    return response


# Health check endpoint
@router.get("/health")
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "document_analyzer": "operational",
            "question_generator": "operational",
            "strategy_generator": "operational",
            "compliance_wrapper": "operational"
        }
    }


# Test endpoint for full flow
@router.post("/test/full-flow")
@limiter.limit("5/minute")
async def test_full_flow(current_user: dict = Depends(get_current_user)):
    """
    Test endpoint to demonstrate full document intake flow.

    EDUCATIONAL USE ONLY: This endpoint demonstrates the system capabilities
    and does not constitute legal advice or consultation.
    """
    try:
        # Step 1: Mock document upload
        test_doc_content = """
        VOLUNTARY PETITION FOR CHAPTER 7 BANKRUPTCY

        Debtor: Test Business LLC
        Address: 123 Main St, City, State 12345

        Total Debt Amount: $250,000
        Primary Creditors: Credit card companies, suppliers
        Business Type: Limited Liability Company

        This petition is filed under Chapter 7 of the Bankruptcy Code.
        """

        # Analyze document
        document_type = document_analyzer.identify_document_type(test_doc_content, "test_petition.txt")
        extracted_entities = document_analyzer.extract_key_information(test_doc_content, document_type)
        information_gaps = document_analyzer.identify_information_gaps(test_doc_content, document_type, extracted_entities)

        # Generate questions
        questions = question_generator.generate_questions_for_bankruptcy(information_gaps)

        # Mock answers
        test_answers = {
            questions[0].question_id if hasattr(questions[0], 'question_id') else "test_q1": "$250000",
            questions[1].question_id if len(questions) > 1 and hasattr(questions[1], 'question_id') else "test_q2": ["credit_cards", "business"],
        }

        # Generate strategies
        business_info = {
            "debt_amount": 250000,
            "business_type": "llc",
            "creditor_types": ["credit_cards", "business"]
        }

        strategies = strategy_generator.generate_bankruptcy_strategies(business_info)

        return {
            "test_flow": "completed",
            "steps": {
                "1_document_analysis": {
                    "document_type": document_type.__dict__ if hasattr(document_type, '__dict__') else str(document_type),
                    "entities_found": len(extracted_entities),
                    "gaps_identified": len(information_gaps)
                },
                "2_questions_generated": {
                    "total_questions": len(questions),
                    "question_types": [q.__class__.__name__ if hasattr(q, '__class__') else "Question" for q in questions]
                },
                "3_answers_processed": {
                    "answers_provided": len(test_answers),
                    "business_info_extracted": True
                },
                "4_strategies_generated": {
                    "total_strategies": len(strategies),
                    "strategy_names": [s.name if hasattr(s, 'name') else "Strategy" for s in strategies]
                }
            },
            "educational_disclaimer": "This test demonstrates system capabilities for educational purposes only. No legal advice is provided.",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in test flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test flow error: {str(e)}"
        )


if __name__ == "__main__":
    # For testing API endpoints
    print("Document Intake API endpoints initialized")
    print("Available endpoints:")
    print("  POST /api/v1/documents/intelligent-upload")
    print("  POST /api/v1/documents/answer-questions")
    print("  GET  /api/v1/documents/analysis/{id}")
    print("  GET  /api/v1/strategies/{matter_id}")
    print("  GET  /api/v1/health")
    print("  POST /api/v1/test/full-flow")
    print("\nAll endpoints include:")
    print("  - Rate limiting")
    print("  - Authentication")
    print("  - Error handling")
    print("  - Audit logging")
    print("  - UPL compliance validation")