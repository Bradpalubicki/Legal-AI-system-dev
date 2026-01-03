"""
Base Court Adapter

Abstract base class for court system adapters providing common
interface for different e-filing systems.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from ..models import (
    FilingRequest,
    FilingResponse,
    CourtDocument,
    EFilingCredentials
)


class BaseCourtAdapter(ABC):
    """
    Abstract base class for court system adapters
    """
    
    def __init__(self, system_name: str):
        self.system_name = system_name
        self.base_url: Optional[str] = None
        self.timeout_seconds = 30
        self.max_retries = 3
        
    @abstractmethod
    async def submit_filing(
        self,
        filing_request: FilingRequest,
        documents: List[CourtDocument],
        credentials: EFilingCredentials
    ) -> FilingResponse:
        """
        Submit a filing to the court system
        """
        pass
    
    @abstractmethod
    async def check_filing_status(
        self,
        external_filing_id: str,
        credentials: EFilingCredentials
    ) -> FilingResponse:
        """
        Check the status of a submitted filing
        """
        pass
    
    @abstractmethod
    async def cancel_filing(
        self,
        external_filing_id: str,
        credentials: EFilingCredentials,
        reason: Optional[str] = None
    ) -> FilingResponse:
        """
        Cancel a pending filing
        """
        pass
    
    @abstractmethod
    async def validate_filing(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, any]:
        """
        Validate a filing request against court-specific requirements
        """
        pass
    
    @abstractmethod
    async def calculate_fees(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, Decimal]:
        """
        Calculate filing fees for a request
        """
        pass
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, any]:
        """
        Get the health status of the court system
        """
        pass
    
    @abstractmethod
    async def authenticate(
        self,
        credentials: EFilingCredentials
    ) -> Dict[str, any]:
        """
        Authenticate with the court system
        """
        pass
    
    # Common utility methods that can be overridden
    
    async def format_case_number(self, case_number: str, court_info) -> str:
        """
        Format case number according to court requirements
        """
        return case_number
    
    async def format_document_title(self, title: str) -> str:
        """
        Format document title according to court requirements
        """
        return title.strip()
    
    async def validate_document_format(self, document: CourtDocument) -> List[str]:
        """
        Validate document format requirements
        """
        errors = []
        
        # Check file format
        if not document.file_name.lower().endswith('.pdf'):
            errors.append("Document must be in PDF format")
        
        # Check file size (assuming max 50MB default)
        if document.file_content and len(document.file_content) > 50 * 1024 * 1024:
            errors.append("Document exceeds maximum file size")
        
        # Check page count if available
        if (document.metadata.page_count and 
            document.metadata.page_count > 500):
            errors.append("Document exceeds maximum page count")
        
        return errors
    
    def _create_error_response(
        self,
        filing_id: UUID,
        message: str,
        errors: List[str]
    ) -> FilingResponse:
        """
        Create a standardized error response
        """
        return FilingResponse(
            filing_id=filing_id,
            success=False,
            status="rejected",
            message=message,
            errors=errors
        )
    
    def _create_success_response(
        self,
        filing_id: UUID,
        message: str,
        confirmation_number: Optional[str] = None,
        transaction_id: Optional[str] = None
    ) -> FilingResponse:
        """
        Create a standardized success response
        """
        return FilingResponse(
            filing_id=filing_id,
            success=True,
            status="submitted",
            message=message,
            confirmation_number=confirmation_number,
            transaction_id=transaction_id
        )