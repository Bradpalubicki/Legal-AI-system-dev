"""
Federal Court Adapter

Adapter for integrating with Federal court systems including
CM/ECF (Case Management/Electronic Case Files) and PACER.
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

import httpx

from .base_adapter import BaseCourtAdapter
from ..models import (
    FilingRequest,
    FilingResponse,
    FilingStatus,
    CourtDocument,
    EFilingCredentials,
    CourtType
)

logger = logging.getLogger(__name__)


class FederalCourtAdapter(BaseCourtAdapter):
    """
    Adapter for Federal court systems (CM/ECF, PACER)
    """
    
    def __init__(self):
        super().__init__("federal_cmecf")
        
        # Federal court system endpoints
        self.cm_ecf_endpoints = {
            "login": "/cgi-bin/login.pl",
            "filing": "/cgi-bin/DktRpt.pl",
            "query": "/cgi-bin/iquery.pl",
            "upload": "/cgi-bin/upload.pl",
            "status": "/cgi-bin/possible.pl"
        }
        
        # Federal filing requirements
        self.federal_requirements = {
            "max_file_size_mb": 50,
            "accepted_formats": ["PDF"],
            "requires_pacer_id": True,
            "requires_ecf_registration": True,
            "max_documents_per_filing": 99
        }
        
        # Federal fee schedule (in dollars)
        self.federal_fees = {
            "district": {
                "case_opening_civil": Decimal("402.00"),
                "case_opening_criminal": Decimal("0.00"),
                "motion": Decimal("0.00"),
                "appeal_civil": Decimal("505.00"),
                "search_fee": Decimal("0.10"),  # per page
                "copy_fee": Decimal("0.50")     # per page
            },
            "bankruptcy": {
                "case_opening_chapter7": Decimal("338.00"),
                "case_opening_chapter11": Decimal("1738.00"),
                "case_opening_chapter13": Decimal("313.00"),
                "motion": Decimal("0.00"),
                "appeal": Decimal("298.00")
            },
            "appeals": {
                "case_opening": Decimal("505.00"),
                "motion": Decimal("0.00")
            }
        }
        
        logger.info("Federal court adapter initialized")
    
    async def submit_filing(
        self,
        filing_request: FilingRequest,
        documents: List[CourtDocument],
        credentials: EFilingCredentials
    ) -> FilingResponse:
        """
        Submit filing to Federal CM/ECF system
        """
        try:
            # Authenticate with CM/ECF
            auth_result = await self.authenticate(credentials)
            if not auth_result.get("success"):
                return self._create_error_response(
                    filing_request.id,
                    "Authentication failed",
                    [auth_result.get("error", "Authentication error")]
                )
            
            session_token = auth_result.get("session_token")
            
            # Prepare filing data
            filing_data = await self._prepare_federal_filing_data(
                filing_request, documents
            )
            
            # Submit to CM/ECF
            submission_result = await self._submit_to_cmecf(
                filing_data, session_token, filing_request.case_info.court.cm_ecf_url
            )
            
            if submission_result.get("success"):
                # Process successful submission
                confirmation_number = submission_result.get("confirmation_number")
                nef_number = submission_result.get("nef_number")  # Notice of Electronic Filing
                
                # Update filing request
                filing_request.external_id = nef_number
                filing_request.confirmation_number = confirmation_number
                filing_request.status = FilingStatus.SUBMITTED
                
                response = FilingResponse(
                    filing_id=filing_request.id,
                    success=True,
                    status=FilingStatus.SUBMITTED,
                    message="Filing submitted successfully to CM/ECF",
                    confirmation_number=confirmation_number,
                    transaction_id=nef_number,
                    accepted_documents=[doc.id for doc in documents],
                    next_actions=[
                        "Monitor for NEF (Notice of Electronic Filing)",
                        "Serve non-ECF participants if required",
                        "Monitor for court response"
                    ]
                )
                
                # Calculate and set fees
                fees = await self.calculate_fees(filing_request)
                response.total_fees_charged = fees.get("total", Decimal("0"))
                
                return response
            else:
                return self._create_error_response(
                    filing_request.id,
                    "Filing submission failed",
                    submission_result.get("errors", ["Unknown submission error"])
                )
                
        except Exception as e:
            logger.error(f"Federal filing submission failed: {str(e)}")
            return self._create_error_response(
                filing_request.id,
                f"Filing submission error: {str(e)}",
                [str(e)]
            )
    
    async def check_filing_status(
        self,
        external_filing_id: str,
        credentials: EFilingCredentials
    ) -> FilingResponse:
        """
        Check filing status in CM/ECF system
        """
        try:
            # Authenticate
            auth_result = await self.authenticate(credentials)
            if not auth_result.get("success"):
                return FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=False,
                    status=FilingStatus.REJECTED,
                    message="Authentication failed for status check",
                    errors=[auth_result.get("error", "Auth error")]
                )
            
            # Query CM/ECF for status
            status_result = await self._query_cmecf_status(
                external_filing_id,
                auth_result.get("session_token"),
                credentials
            )
            
            if status_result.get("found"):
                filing_status = self._map_cmecf_status(status_result.get("status"))
                
                return FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=True,
                    status=filing_status,
                    message=f"Filing status: {filing_status.value}",
                    transaction_id=external_filing_id,
                    service_complete=status_result.get("service_complete", False)
                )
            else:
                return FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=False,
                    status=FilingStatus.REJECTED,
                    message="Filing not found in CM/ECF system",
                    errors=["Filing ID not found"]
                )
                
        except Exception as e:
            logger.error(f"Federal status check failed: {str(e)}")
            return FilingResponse(
                filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                success=False,
                status=FilingStatus.REJECTED,
                message=f"Status check error: {str(e)}",
                errors=[str(e)]
            )
    
    async def cancel_filing(
        self,
        external_filing_id: str,
        credentials: EFilingCredentials,
        reason: Optional[str] = None
    ) -> FilingResponse:
        """
        Cancel a filing in CM/ECF (limited availability)
        """
        try:
            # Note: CM/ECF has very limited cancellation capabilities
            # Most filings cannot be cancelled once submitted
            
            return FilingResponse(
                filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                success=False,
                status=FilingStatus.SUBMITTED,
                message="CM/ECF does not support filing cancellation after submission",
                errors=["Federal filings cannot be cancelled once submitted to CM/ECF"],
                next_actions=[
                    "Contact court clerk for assistance",
                    "File amended/corrected document if needed",
                    "Consider motion to withdraw filing"
                ]
            )
            
        except Exception as e:
            logger.error(f"Federal cancellation attempt failed: {str(e)}")
            return FilingResponse(
                filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                success=False,
                status=FilingStatus.REJECTED,
                message=f"Cancellation error: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate_filing(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, any]:
        """
        Validate filing against Federal court requirements
        """
        errors = []
        warnings = []
        
        try:
            # Validate case number format
            case_number = filing_request.case_info.case_number
            if case_number and not self._validate_federal_case_number(case_number):
                errors.append(f"Invalid federal case number format: {case_number}")
            
            # Validate court type
            court_type = filing_request.case_info.court.court_type
            if not court_type.value.startswith("federal"):
                errors.append("Court type must be federal for this adapter")
            
            # Validate documents
            for document in filing_request.documents:
                doc_errors = await self.validate_document_format(document)
                errors.extend(doc_errors)
                
                # Federal-specific document validation
                if document.metadata.page_count and document.metadata.page_count > 500:
                    warnings.append(f"Document {document.file_name} has {document.metadata.page_count} pages (consider splitting)")
            
            # Validate attorney credentials
            attorney = filing_request.filing_attorney
            if not attorney.federal_bar_id and court_type.value.startswith("federal"):
                warnings.append("Federal bar admission recommended for federal courts")
            
            # Validate service requirements
            if filing_request.service_info.service_type.value != "electronic":
                warnings.append("Electronic service is preferred in federal courts")
            
            # Check for required fields
            required_fields = ["case_number", "document_title", "filing_attorney"]
            for field in required_fields:
                if field == "case_number" and not case_number:
                    errors.append("Case number is required")
                elif field == "document_title" and not filing_request.filing_description:
                    errors.append("Document title/description is required")
                elif field == "filing_attorney" and not attorney:
                    errors.append("Filing attorney information is required")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "federal_requirements_met": len(errors) == 0
            }
            
        except Exception as e:
            logger.error(f"Federal validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": warnings
            }
    
    async def calculate_fees(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, Decimal]:
        """
        Calculate federal court filing fees
        """
        try:
            court_type = filing_request.case_info.court.court_type
            fees = {}
            
            # Get appropriate fee schedule
            if court_type == CourtType.FEDERAL_DISTRICT:
                fee_schedule = self.federal_fees["district"]
            elif court_type == CourtType.FEDERAL_BANKRUPTCY:
                fee_schedule = self.federal_fees["bankruptcy"]
            elif court_type == CourtType.FEDERAL_APPEALS:
                fee_schedule = self.federal_fees["appeals"]
            else:
                fee_schedule = self.federal_fees["district"]  # Default
            
            # Calculate based on filing type
            filing_type = filing_request.filing_type.lower()
            
            if "initial" in filing_type or "complaint" in filing_type:
                if court_type == CourtType.FEDERAL_BANKRUPTCY:
                    # Determine chapter type (simplified)
                    if "chapter 7" in filing_request.filing_description.lower():
                        fees["case_opening"] = fee_schedule["case_opening_chapter7"]
                    elif "chapter 11" in filing_request.filing_description.lower():
                        fees["case_opening"] = fee_schedule["case_opening_chapter11"]
                    elif "chapter 13" in filing_request.filing_description.lower():
                        fees["case_opening"] = fee_schedule["case_opening_chapter13"]
                    else:
                        fees["case_opening"] = fee_schedule["case_opening_chapter7"]  # Default
                else:
                    fees["case_opening"] = fee_schedule.get("case_opening_civil", Decimal("402.00"))
            elif "motion" in filing_type:
                fees["motion"] = fee_schedule.get("motion", Decimal("0.00"))
            elif "appeal" in filing_type:
                fees["appeal"] = fee_schedule.get("appeal", Decimal("505.00"))
            
            # Add miscellaneous fees
            total_pages = sum(
                doc.metadata.page_count or 0 
                for doc in filing_request.documents
            )
            
            if total_pages > 0:
                fees["copy_fee"] = fee_schedule.get("copy_fee", Decimal("0.50")) * total_pages
            
            # Calculate total
            total_fee = sum(fees.values())
            fees["total"] = total_fee
            
            return fees
            
        except Exception as e:
            logger.error(f"Federal fee calculation failed: {str(e)}")
            return {"error": Decimal("0"), "total": Decimal("0")}
    
    async def get_health_status(self) -> Dict[str, any]:
        """
        Get health status of Federal court systems
        """
        try:
            # In production, would check actual CM/ECF endpoints
            return {
                "system": "CM/ECF Federal",
                "status": "operational",
                "available": True,
                "response_time_ms": 200,
                "last_checked": datetime.utcnow().isoformat(),
                "services": {
                    "authentication": "available",
                    "filing": "available", 
                    "query": "available",
                    "pacer": "available"
                },
                "maintenance_windows": [
                    {"day": "Sunday", "time": "12:00 AM - 6:00 AM EST"}
                ]
            }
            
        except Exception as e:
            logger.error(f"Federal health check failed: {str(e)}")
            return {
                "system": "CM/ECF Federal",
                "status": "error",
                "available": False,
                "error": str(e)
            }
    
    async def authenticate(
        self,
        credentials: EFilingCredentials
    ) -> Dict[str, any]:
        """
        Authenticate with CM/ECF system
        """
        try:
            # Validate credentials
            if not credentials.pacer_id:
                return {
                    "success": False,
                    "error": "PACER ID required for federal courts"
                }
            
            if not credentials.username or not credentials.password_hash:
                return {
                    "success": False,
                    "error": "Username and password required"
                }
            
            # In production, would make actual authentication request to CM/ECF
            # For now, simulate successful authentication
            
            # Generate session token (simplified)
            session_data = f"{credentials.username}:{credentials.pacer_id}:{datetime.utcnow()}"
            session_token = hashlib.md5(session_data.encode()).hexdigest()
            
            return {
                "success": True,
                "session_token": session_token,
                "expires_at": (datetime.utcnow().timestamp() + 3600),  # 1 hour
                "user_info": {
                    "username": credentials.username,
                    "pacer_id": credentials.pacer_id,
                    "bar_number": credentials.bar_number
                }
            }
            
        except Exception as e:
            logger.error(f"Federal authentication failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_federal_case_number(self, case_number: str) -> bool:
        """
        Validate federal case number format (e.g., 1:21-cv-12345)
        """
        # Federal format: D:YY-TT-NNNNN
        # D = division, YY = year, TT = type (cv, cr, bk, etc.), NNNNN = sequential number
        pattern = r'^\d:\d{2}-[a-z]{2}-\d{5}(-[a-zA-Z]{1,3})?$'
        return bool(re.match(pattern, case_number, re.IGNORECASE))
    
    async def _prepare_federal_filing_data(
        self,
        filing_request: FilingRequest,
        documents: List[CourtDocument]
    ) -> Dict:
        """
        Prepare filing data for CM/ECF submission
        """
        filing_data = {
            "case_number": filing_request.case_info.case_number,
            "case_title": filing_request.case_info.case_title,
            "filing_type": filing_request.filing_type,
            "description": filing_request.filing_description,
            "attorney": {
                "name": filing_request.filing_attorney.full_name,
                "bar_number": filing_request.filing_attorney.bar_number,
                "ecf_login": filing_request.filing_attorney.ecf_login
            },
            "documents": [],
            "service_info": {
                "type": filing_request.service_info.service_type.value,
                "parties": filing_request.service_info.served_parties
            },
            "fees": []
        }
        
        # Add document information
        for doc in documents:
            doc_data = {
                "id": str(doc.id),
                "title": doc.metadata.title,
                "type": doc.metadata.document_type.value,
                "security_level": doc.metadata.security_level,
                "file_name": doc.file_name,
                "page_count": doc.metadata.page_count
            }
            filing_data["documents"].append(doc_data)
        
        # Add fee information
        fees = await self.calculate_fees(filing_request)
        for fee_type, amount in fees.items():
            if fee_type != "total" and amount > 0:
                filing_data["fees"].append({
                    "type": fee_type,
                    "amount": str(amount)
                })
        
        return filing_data
    
    async def _submit_to_cmecf(
        self,
        filing_data: Dict,
        session_token: str,
        cm_ecf_url: str
    ) -> Dict:
        """
        Submit filing data to CM/ECF system
        """
        try:
            # In production, this would make actual HTTP requests to CM/ECF
            # For now, simulate successful submission
            
            # Generate confirmation numbers
            confirmation_number = f"CF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            nef_number = f"NEF-{datetime.now().strftime('%Y%m%d')}-{hash(str(filing_data)) % 10000:04d}"
            
            # Simulate processing delay
            await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "confirmation_number": confirmation_number,
                "nef_number": nef_number,
                "submission_time": datetime.utcnow().isoformat(),
                "message": "Filing submitted successfully to CM/ECF"
            }
            
        except Exception as e:
            logger.error(f"CM/ECF submission failed: {str(e)}")
            return {
                "success": False,
                "errors": [str(e)]
            }
    
    async def _query_cmecf_status(
        self,
        nef_number: str,
        session_token: str,
        credentials: EFilingCredentials
    ) -> Dict:
        """
        Query CM/ECF for filing status
        """
        try:
            # In production, would query actual CM/ECF system
            # For now, simulate status response
            
            # Simulate different statuses based on time
            import time
            status_code = int(time.time()) % 4
            
            status_map = {
                0: "submitted",
                1: "accepted", 
                2: "served",
                3: "completed"
            }
            
            return {
                "found": True,
                "status": status_map[status_code],
                "service_complete": status_code >= 2,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"CM/ECF status query failed: {str(e)}")
            return {
                "found": False,
                "error": str(e)
            }
    
    def _map_cmecf_status(self, cmecf_status: str) -> FilingStatus:
        """
        Map CM/ECF status to internal filing status
        """
        status_mapping = {
            "submitted": FilingStatus.SUBMITTED,
            "accepted": FilingStatus.ACCEPTED,
            "served": FilingStatus.SERVED,
            "completed": FilingStatus.SERVED,
            "rejected": FilingStatus.REJECTED,
            "cancelled": FilingStatus.CANCELLED
        }
        
        return status_mapping.get(cmecf_status.lower(), FilingStatus.SUBMITTED)