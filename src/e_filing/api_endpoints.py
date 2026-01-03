"""
E-Filing API Endpoints

FastAPI endpoints for electronic court filing system supporting
Federal (CM/ECF) and state court integrations with comprehensive
document processing and validation.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import (
    FilingRequest,
    FilingResponse,
    CourtDocument,
    DocumentMetadata,
    DocumentType,
    EFilingCredentials,
    CaseInfo,
    Attorney,
    CourtInfo
)
from .services.filing_service import EFilingService
from .services.court_service import CourtService
from .processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

# Create router
efiling_router = APIRouter(prefix="/api/v1/e-filing", tags=["e-filing"])
security = HTTPBearer()


class EFilingHandler:
    """
    Handler for e-filing API endpoints that manages services
    and coordinates filing operations.
    """
    
    def __init__(self):
        self.filing_service: Optional[EFilingService] = None
        self.court_service: Optional[CourtService] = None
        self.document_processor: Optional[DocumentProcessor] = None
    
    def set_services(
        self,
        filing_service: EFilingService,
        court_service: CourtService,
        document_processor: DocumentProcessor
    ):
        self.filing_service = filing_service
        self.court_service = court_service
        self.document_processor = document_processor


# Global handler instance
efiling_handler = EFilingHandler()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependency to get current user from JWT token
    """
    # In production, this would verify the JWT token
    # For now, returning mock user data
    return {
        "user_id": "12345678-1234-5678-9abc-123456789012",
        "attorney_id": "attorney-123",
        "bar_number": "123456",
        "state_bar": "CA"
    }


@efiling_router.post("/submit", response_model=FilingResponse)
async def submit_filing(
    filing_request: FilingRequest,
    validate_only: bool = Form(default=False),
    current_user: Dict = Depends(get_current_user)
):
    """
    Submit an electronic filing to the appropriate court system
    """
    if not efiling_handler.filing_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-filing service not available"
        )
    
    try:
        # Get user credentials (in production, would be stored securely)
        credentials = EFilingCredentials(
            attorney_id=UUID(current_user["attorney_id"]),
            court_system="cm_ecf",  # Default
            username=current_user.get("username", "demo_user"),
            password_hash="hashed_password",  # Would be actual hash
            bar_number=current_user["bar_number"],
            pacer_id="demo_pacer_id"
        )
        
        # Submit filing
        response = await efiling_handler.filing_service.submit_filing(
            filing_request, credentials, validate_only
        )
        
        logger.info(f"Filing submission result: {response.status} for user {current_user['user_id']}")
        return response
        
    except Exception as e:
        logger.error(f"Filing submission failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filing submission failed: {str(e)}"
        )


@efiling_router.get("/status/{filing_id}", response_model=FilingResponse)
async def check_filing_status(
    filing_id: UUID,
    current_user: Dict = Depends(get_current_user)
):
    """
    Check the status of a submitted filing
    """
    if not efiling_handler.filing_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-filing service not available"
        )
    
    try:
        # Get user credentials
        credentials = EFilingCredentials(
            attorney_id=UUID(current_user["attorney_id"]),
            court_system="cm_ecf",
            username=current_user.get("username", "demo_user"),
            password_hash="hashed_password",
            bar_number=current_user["bar_number"]
        )
        
        response = await efiling_handler.filing_service.check_filing_status(
            filing_id, credentials
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )


@efiling_router.post("/cancel/{filing_id}", response_model=FilingResponse)
async def cancel_filing(
    filing_id: UUID,
    reason: Optional[str] = Form(None),
    current_user: Dict = Depends(get_current_user)
):
    """
    Cancel a pending filing
    """
    if not efiling_handler.filing_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-filing service not available"
        )
    
    try:
        credentials = EFilingCredentials(
            attorney_id=UUID(current_user["attorney_id"]),
            court_system="cm_ecf",
            username=current_user.get("username", "demo_user"),
            password_hash="hashed_password",
            bar_number=current_user["bar_number"]
        )
        
        response = await efiling_handler.filing_service.cancel_filing(
            filing_id, credentials, reason
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Filing cancellation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cancellation failed: {str(e)}"
        )


@efiling_router.post("/documents/upload", response_model=Dict)
async def upload_document(
    file: UploadFile = File(...),
    document_title: str = Form(...),
    document_type: DocumentType = Form(...),
    security_level: str = Form(default="public"),
    case_id: UUID = Form(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Upload and process a document for e-filing
    """
    if not efiling_handler.document_processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document processing service not available"
        )
    
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith(("application/pdf", "text/", "application/msword")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF, text, and Word documents are supported"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Create document metadata
        metadata = DocumentMetadata(
            title=document_title,
            document_type=document_type,
            security_level=security_level,
            file_size_bytes=len(file_content),
            created_date=datetime.utcnow()
        )
        
        # Create court document
        document = CourtDocument(
            file_name=file.filename,
            file_content=file_content,
            mime_type=file.content_type,
            metadata=metadata,
            case_id=case_id,
            attorney_id=UUID(current_user["attorney_id"])
        )
        
        # Process document
        processed_doc = await efiling_handler.document_processor.process_document(document)
        
        return {
            "document_id": str(processed_doc.id),
            "status": processed_doc.status,
            "file_name": processed_doc.file_name,
            "metadata": processed_doc.metadata.dict(),
            "validation_errors": processed_doc.validation_errors,
            "processing_complete": processed_doc.status in ["processed", "validation_failed"]
        }
        
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@efiling_router.get("/documents/{document_id}", response_model=Dict)
async def get_document(
    document_id: UUID,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get document information and metadata
    """
    try:
        # In production, would retrieve from database
        return {
            "document_id": str(document_id),
            "status": "processed",
            "message": "Document retrieval not fully implemented",
            "note": "In production, would retrieve document from database"
        }
        
    except Exception as e:
        logger.error(f"Document retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document retrieval failed: {str(e)}"
        )


@efiling_router.get("/courts", response_model=List[Dict])
async def get_courts(
    state: Optional[str] = None,
    court_type: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get list of available courts for e-filing
    """
    if not efiling_handler.court_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Court service not available"
        )
    
    try:
        from .models import CourtType
        
        # Convert string to enum if provided
        court_type_enum = None
        if court_type:
            try:
                court_type_enum = CourtType(court_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid court type: {court_type}"
                )
        
        courts = await efiling_handler.court_service.search_courts(
            state=state,
            court_type=court_type_enum
        )
        
        return [court.dict() for court in courts]
        
    except Exception as e:
        logger.error(f"Court search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Court search failed: {str(e)}"
        )


@efiling_router.get("/courts/{court_id}/requirements", response_model=Dict)
async def get_court_requirements(
    court_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get filing requirements for a specific court
    """
    if not efiling_handler.court_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Court service not available"
        )
    
    try:
        requirements = await efiling_handler.court_service.get_filing_requirements(court_id)
        
        if "error" in requirements:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=requirements["error"]
            )
        
        return requirements
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Court requirements retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirements retrieval failed: {str(e)}"
        )


@efiling_router.get("/courts/{court_id}/status", response_model=Dict)
async def get_court_status(
    court_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Check the status of a court's e-filing system
    """
    if not efiling_handler.court_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Court service not available"
        )
    
    try:
        status_info = await efiling_handler.court_service.check_court_system_status(court_id)
        return status_info
        
    except Exception as e:
        logger.error(f"Court status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Court status check failed: {str(e)}"
        )


@efiling_router.post("/fees/estimate", response_model=Dict)
async def estimate_filing_fees(
    filing_request: FilingRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Estimate filing fees for a given filing request
    """
    if not efiling_handler.filing_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-filing service not available"
        )
    
    try:
        fee_estimate = await efiling_handler.filing_service.estimate_filing_fees(
            filing_request
        )
        
        return {
            "filing_id": str(filing_request.id),
            "court": filing_request.case_info.court.name,
            "filing_type": filing_request.filing_type,
            "fee_breakdown": {
                str(fee_type): float(amount) 
                for fee_type, amount in fee_estimate.items()
            },
            "currency": "USD",
            "estimated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fee estimation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fee estimation failed: {str(e)}"
        )


@efiling_router.get("/history", response_model=List[FilingResponse])
async def get_filing_history(
    limit: int = 50,
    status_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get filing history for the current user
    """
    if not efiling_handler.filing_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-filing service not available"
        )
    
    try:
        from .models import FilingStatus
        
        # Parse parameters
        status_enum = None
        if status_filter:
            try:
                status_enum = FilingStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            date_from_dt = datetime.fromisoformat(date_from)
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to)
        
        history = await efiling_handler.filing_service.get_filing_history(
            attorney_id=UUID(current_user["attorney_id"]),
            status=status_enum,
            date_from=date_from_dt,
            date_to=date_to_dt,
            limit=min(limit, 100)  # Cap at 100
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Filing history retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"History retrieval failed: {str(e)}"
        )


@efiling_router.post("/validate", response_model=Dict)
async def validate_filing(
    filing_request: FilingRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Validate a filing request without submitting
    """
    if not efiling_handler.filing_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-filing service not available"
        )
    
    try:
        credentials = EFilingCredentials(
            attorney_id=UUID(current_user["attorney_id"]),
            court_system="cm_ecf",
            username=current_user.get("username", "demo_user"),
            password_hash="hashed_password",
            bar_number=current_user["bar_number"]
        )
        
        # Validate only (don't submit)
        response = await efiling_handler.filing_service.submit_filing(
            filing_request, credentials, validate_only=True
        )
        
        return {
            "filing_id": str(filing_request.id),
            "validation_result": response.dict(),
            "ready_for_submission": response.success,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Filing validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@efiling_router.get("/service/status", response_model=Dict)
async def get_service_status(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get e-filing service status and statistics
    """
    try:
        service_status = {}
        
        if efiling_handler.filing_service:
            filing_status = await efiling_handler.filing_service.get_service_status()
            service_status["filing_service"] = filing_status
        
        if efiling_handler.court_service:
            court_status = await efiling_handler.court_service.get_system_health()
            service_status["court_service"] = court_status
        
        if efiling_handler.document_processor:
            doc_stats = efiling_handler.document_processor.get_processing_stats()
            service_status["document_processor"] = doc_stats
        
        service_status["timestamp"] = datetime.utcnow().isoformat()
        service_status["overall_status"] = "operational"
        
        return service_status
        
    except Exception as e:
        logger.error(f"Service status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service status check failed: {str(e)}"
        )


@efiling_router.post("/retry/{filing_id}", response_model=FilingResponse)
async def retry_failed_filing(
    filing_id: UUID,
    current_user: Dict = Depends(get_current_user)
):
    """
    Retry a failed filing submission
    """
    if not efiling_handler.filing_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-filing service not available"
        )
    
    try:
        credentials = EFilingCredentials(
            attorney_id=UUID(current_user["attorney_id"]),
            court_system="cm_ecf",
            username=current_user.get("username", "demo_user"),
            password_hash="hashed_password",
            bar_number=current_user["bar_number"]
        )
        
        response = await efiling_handler.filing_service.retry_failed_filing(
            filing_id, credentials
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Filing retry failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retry failed: {str(e)}"
        )


@efiling_router.get("/health", response_model=Dict)
async def health_check():
    """
    Health check endpoint for e-filing system
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "filing_service": efiling_handler.filing_service is not None,
                "court_service": efiling_handler.court_service is not None,
                "document_processor": efiling_handler.document_processor is not None
            }
        }
        
        # Check if all critical services are available
        if not all(health_status["services"].values()):
            health_status["status"] = "degraded"
            health_status["message"] = "Some services are not available"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Dependency injection function for initialization
def init_efiling_api(
    filing_service: EFilingService,
    court_service: CourtService,
    document_processor: DocumentProcessor
):
    """
    Initialize e-filing API with required services
    """
    efiling_handler.set_services(filing_service, court_service, document_processor)
    logger.info("E-filing API initialized successfully")