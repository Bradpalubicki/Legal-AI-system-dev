"""
State Court Adapter

Adapter for integrating with various state court e-filing systems
including California, New York, Texas, and other state systems.
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

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


class StateCourtAdapter(BaseCourtAdapter):
    """
    Adapter for state court e-filing systems with support for
    multiple state-specific implementations
    """
    
    def __init__(self):
        super().__init__("state_courts")
        
        # State-specific configurations
        self.state_configs = {
            "CA": {
                "system_name": "California Courts E-Filing",
                "endpoints": {
                    "login": "/login",
                    "filing": "/file",
                    "status": "/status",
                    "cancel": "/cancel"
                },
                "max_file_size_mb": 25,
                "case_number_format": r"^\d{2}-\w{2}-\d{6}$",  # e.g., 21-CV-123456
                "fee_multiplier": 1.0
            },
            "NY": {
                "system_name": "New York State Courts E-Filing (NYSCEF)",
                "endpoints": {
                    "login": "/nyscef/login",
                    "filing": "/nyscef/efile",
                    "status": "/nyscef/status",
                    "cancel": "/nyscef/withdraw"
                },
                "max_file_size_mb": 35,
                "case_number_format": r"^\d{6}/\d{4}$",  # e.g., 123456/2021
                "fee_multiplier": 1.15
            },
            "TX": {
                "system_name": "Texas E-File",
                "endpoints": {
                    "login": "/texas/auth",
                    "filing": "/texas/submit",
                    "status": "/texas/track",
                    "cancel": "/texas/cancel"
                },
                "max_file_size_mb": 30,
                "case_number_format": r"^\d{2}-\d{4}-\d{6}$",  # e.g., 21-2021-123456
                "fee_multiplier": 0.95
            },
            "IL": {
                "system_name": "Illinois E-File",
                "endpoints": {
                    "login": "/illinois/login",
                    "filing": "/illinois/efile",
                    "status": "/illinois/status",
                    "cancel": "/illinois/cancel"
                },
                "max_file_size_mb": 40,
                "case_number_format": r"^\d{4}[A-Z]{2}\d{6}$",  # e.g., 2021CH123456
                "fee_multiplier": 1.05
            }
        }
        
        # Base state court fees (varies by state)
        self.base_fees = {
            "case_opening_civil": Decimal("435.00"),
            "case_opening_family": Decimal("365.00"),
            "motion": Decimal("60.00"),
            "response": Decimal("35.00"),
            "appeal": Decimal("450.00"),
            "copy_fee": Decimal("0.25"),  # per page
            "service_fee": Decimal("40.00")
        }
        
        logger.info("State court adapter initialized")
    
    async def submit_filing(
        self,
        filing_request: FilingRequest,
        documents: List[CourtDocument],
        credentials: EFilingCredentials
    ) -> FilingResponse:
        """
        Submit filing to state court e-filing system
        """
        try:
            # Get state-specific configuration
            state = filing_request.case_info.court.state
            state_config = self.state_configs.get(state, self.state_configs["CA"])  # Default to CA
            
            # Authenticate with state system
            auth_result = await self.authenticate(credentials)
            if not auth_result.get("success"):
                return self._create_error_response(
                    filing_request.id,
                    "Authentication failed",
                    [auth_result.get("error", "Authentication error")]
                )
            
            session_token = auth_result.get("session_token")
            
            # Prepare state-specific filing data
            filing_data = await self._prepare_state_filing_data(
                filing_request, documents, state_config
            )
            
            # Submit to state system
            submission_result = await self._submit_to_state_system(
                filing_data, session_token, state_config, state
            )
            
            if submission_result.get("success"):
                # Process successful submission
                confirmation_number = submission_result.get("confirmation_number")
                filing_id = submission_result.get("filing_id")
                
                # Update filing request
                filing_request.external_id = filing_id
                filing_request.confirmation_number = confirmation_number
                filing_request.status = FilingStatus.SUBMITTED
                
                response = FilingResponse(
                    filing_id=filing_request.id,
                    success=True,
                    status=FilingStatus.SUBMITTED,
                    message=f"Filing submitted successfully to {state_config['system_name']}",
                    confirmation_number=confirmation_number,
                    transaction_id=filing_id,
                    accepted_documents=[doc.id for doc in documents],
                    next_actions=await self._get_state_next_actions(state, filing_request)
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
            logger.error(f"State filing submission failed: {str(e)}")
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
        Check filing status in state court system
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
            
            # Query state system for status
            status_result = await self._query_state_status(
                external_filing_id,
                auth_result.get("session_token"),
                credentials
            )
            
            if status_result.get("found"):
                filing_status = self._map_state_status(status_result.get("status"))
                
                response = FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=True,
                    status=filing_status,
                    message=f"Filing status: {filing_status.value}",
                    transaction_id=external_filing_id,
                    service_complete=status_result.get("service_complete", False)
                )
                
                # Add state-specific status information
                if status_result.get("court_response"):
                    response.next_actions.append("Review court response")
                
                if status_result.get("hearing_scheduled"):
                    response.deadlines.append({
                        "type": "hearing",
                        "date": status_result.get("hearing_date"),
                        "description": "Court hearing scheduled"
                    })
                
                return response
            else:
                return FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=False,
                    status=FilingStatus.REJECTED,
                    message="Filing not found in state court system",
                    errors=["Filing ID not found"]
                )
                
        except Exception as e:
            logger.error(f"State status check failed: {str(e)}")
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
        Cancel a filing in state court system
        """
        try:
            # Authenticate
            auth_result = await self.authenticate(credentials)
            if not auth_result.get("success"):
                return FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=False,
                    status=FilingStatus.REJECTED,
                    message="Authentication failed for cancellation",
                    errors=[auth_result.get("error", "Auth error")]
                )
            
            # Attempt cancellation with state system
            cancel_result = await self._cancel_state_filing(
                external_filing_id,
                auth_result.get("session_token"),
                reason or "Requested by filer"
            )
            
            if cancel_result.get("success"):
                return FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=True,
                    status=FilingStatus.CANCELLED,
                    message=f"Filing cancelled successfully. {cancel_result.get('message', '')}",
                    transaction_id=external_filing_id,
                    next_actions=[
                        "Confirmation email will be sent",
                        "Fees may be refunded according to court policy"
                    ]
                )
            else:
                return FilingResponse(
                    filing_id=UUID("00000000-0000-0000-0000-000000000000"),
                    success=False,
                    status=FilingStatus.SUBMITTED,
                    message="Filing cancellation failed",
                    errors=cancel_result.get("errors", ["Cancellation not permitted"]),
                    next_actions=[
                        "Contact court clerk for assistance",
                        "Consider filing motion to withdraw"
                    ]
                )
                
        except Exception as e:
            logger.error(f"State cancellation failed: {str(e)}")
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
        Validate filing against state court requirements
        """
        errors = []
        warnings = []
        
        try:
            state = filing_request.case_info.court.state
            state_config = self.state_configs.get(state, self.state_configs["CA"])
            
            # Validate case number format
            case_number = filing_request.case_info.case_number
            if case_number and not re.match(state_config["case_number_format"], case_number):
                errors.append(f"Invalid case number format for {state}: {case_number}")
            
            # Validate court type
            court_type = filing_request.case_info.court.court_type
            if court_type.value.startswith("federal"):
                errors.append("Federal court type not supported by state adapter")
            
            # State-specific document validation
            for document in filing_request.documents:
                # Check file size against state limits
                if (document.file_content and 
                    len(document.file_content) > state_config["max_file_size_mb"] * 1024 * 1024):
                    errors.append(f"Document {document.file_name} exceeds {state} file size limit")
                
                # Basic format validation
                doc_errors = await self.validate_document_format(document)
                errors.extend(doc_errors)
            
            # State-specific validation rules
            if state == "CA":
                errors.extend(await self._validate_california_requirements(filing_request))
            elif state == "NY":
                errors.extend(await self._validate_new_york_requirements(filing_request))
            elif state == "TX":
                errors.extend(await self._validate_texas_requirements(filing_request))
            
            # Validate service requirements
            service_type = filing_request.service_info.service_type.value
            if service_type not in ["electronic", "mail", "hand_delivery"]:
                warnings.append("Unusual service method - verify court acceptance")
            
            # Check attorney bar admission
            attorney = filing_request.filing_attorney
            if attorney.state_bar != state:
                warnings.append(f"Attorney bar admission is {attorney.state_bar}, filing in {state}")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "state_requirements_met": len(errors) == 0,
                "state": state,
                "system": state_config["system_name"]
            }
            
        except Exception as e:
            logger.error(f"State validation failed: {str(e)}")
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
        Calculate state court filing fees
        """
        try:
            state = filing_request.case_info.court.state
            state_config = self.state_configs.get(state, self.state_configs["CA"])
            multiplier = Decimal(str(state_config["fee_multiplier"]))
            
            fees = {}
            
            # Base filing fees
            filing_type = filing_request.filing_type.lower()
            case_type = filing_request.case_info.case_type.lower()
            
            if "initial" in filing_type or "complaint" in filing_type:
                if "family" in case_type:
                    fees["case_opening"] = self.base_fees["case_opening_family"] * multiplier
                else:
                    fees["case_opening"] = self.base_fees["case_opening_civil"] * multiplier
            elif "motion" in filing_type:
                fees["motion"] = self.base_fees["motion"] * multiplier
            elif "response" in filing_type:
                fees["response"] = self.base_fees["response"] * multiplier
            elif "appeal" in filing_type:
                fees["appeal"] = self.base_fees["appeal"] * multiplier
            
            # Service fees
            if filing_request.service_info.service_type.value != "electronic":
                fees["service"] = self.base_fees["service_fee"] * multiplier
            
            # Document fees (per page for some states)
            if state in ["CA", "NY"]:
                total_pages = sum(
                    doc.metadata.page_count or 0
                    for doc in filing_request.documents
                )
                if total_pages > 10:  # First 10 pages typically free
                    excess_pages = total_pages - 10
                    fees["copy_fee"] = self.base_fees["copy_fee"] * Decimal(excess_pages) * multiplier
            
            # State-specific fees
            if state == "CA":
                # California court construction fund fee
                if fees.get("case_opening", Decimal("0")) > 0:
                    fees["court_construction"] = Decimal("1.00")
            elif state == "NY":
                # New York attorney registration fee
                if fees.get("case_opening", Decimal("0")) > 0:
                    fees["attorney_registration"] = Decimal("25.00")
            
            # Calculate total
            total_fee = sum(fees.values())
            fees["total"] = total_fee
            
            return fees
            
        except Exception as e:
            logger.error(f"State fee calculation failed: {str(e)}")
            return {"error": Decimal("0"), "total": Decimal("0")}
    
    async def get_health_status(self) -> Dict[str, any]:
        """
        Get health status of state court systems
        """
        try:
            # Check status of major state systems
            system_status = {}
            
            for state, config in self.state_configs.items():
                # In production, would check actual state system endpoints
                system_status[state] = {
                    "system_name": config["system_name"],
                    "status": "operational",
                    "available": True,
                    "response_time_ms": 250
                }
            
            operational_count = sum(1 for status in system_status.values() if status["available"])
            total_count = len(system_status)
            
            return {
                "system": "State Courts",
                "overall_status": "operational" if operational_count == total_count else "degraded",
                "available_systems": operational_count,
                "total_systems": total_count,
                "last_checked": datetime.utcnow().isoformat(),
                "state_systems": system_status
            }
            
        except Exception as e:
            logger.error(f"State health check failed: {str(e)}")
            return {
                "system": "State Courts",
                "status": "error",
                "available": False,
                "error": str(e)
            }
    
    async def authenticate(
        self,
        credentials: EFilingCredentials
    ) -> Dict[str, any]:
        """
        Authenticate with state court system
        """
        try:
            # Validate credentials
            if not credentials.username or not credentials.password_hash:
                return {
                    "success": False,
                    "error": "Username and password required"
                }
            
            if not credentials.bar_number:
                return {
                    "success": False,
                    "error": "State bar number required"
                }
            
            # In production, would make actual authentication request
            # For now, simulate successful authentication
            
            # Generate session token
            session_data = f"{credentials.username}:{credentials.bar_number}:{datetime.utcnow()}"
            session_token = hashlib.md5(session_data.encode()).hexdigest()
            
            return {
                "success": True,
                "session_token": session_token,
                "expires_at": (datetime.utcnow().timestamp() + 7200),  # 2 hours
                "user_info": {
                    "username": credentials.username,
                    "bar_number": credentials.bar_number,
                    "state_bar": credentials.state_bar
                }
            }
            
        except Exception as e:
            logger.error(f"State authentication failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_california_requirements(self, filing_request: FilingRequest) -> List[str]:
        """Validate California-specific requirements"""
        errors = []
        
        # California requires proof of service for most filings
        if not filing_request.service_info.certificate_required:
            errors.append("Proof of service required for California filings")
        
        # Check for required California forms
        case_type = filing_request.case_info.case_type.lower()
        if "family" in case_type:
            # Family law cases require specific forms
            if not any("fl-" in doc.file_name.lower() for doc in filing_request.documents):
                errors.append("California family law cases require FL-series forms")
        
        return errors
    
    async def _validate_new_york_requirements(self, filing_request: FilingRequest) -> List[str]:
        """Validate New York-specific requirements"""
        errors = []
        
        # New York requires attorney affirmation
        if not filing_request.filing_attorney.federal_bar_id:
            # Check for attorney affirmation in documents
            has_affirmation = any(
                "affirmation" in doc.metadata.title.lower()
                for doc in filing_request.documents
            )
            if not has_affirmation:
                errors.append("Attorney affirmation required for New York filings")
        
        return errors
    
    async def _validate_texas_requirements(self, filing_request: FilingRequest) -> List[str]:
        """Validate Texas-specific requirements"""
        errors = []
        
        # Texas requires specific citation format
        # This would be more comprehensive in production
        if filing_request.case_info.nature_of_suit and "contract" in filing_request.case_info.nature_of_suit.lower():
            # Contract cases have specific requirements
            pass
        
        return errors
    
    async def _prepare_state_filing_data(
        self,
        filing_request: FilingRequest,
        documents: List[CourtDocument],
        state_config: Dict
    ) -> Dict:
        """Prepare filing data for state court submission"""
        filing_data = {
            "case_number": filing_request.case_info.case_number,
            "case_title": filing_request.case_info.case_title,
            "case_type": filing_request.case_info.case_type,
            "filing_type": filing_request.filing_type,
            "description": filing_request.filing_description,
            "court": {
                "name": filing_request.case_info.court.name,
                "location": f"{filing_request.case_info.court.city}, {filing_request.case_info.court.state}"
            },
            "attorney": {
                "name": filing_request.filing_attorney.full_name,
                "bar_number": filing_request.filing_attorney.bar_number,
                "state_bar": filing_request.filing_attorney.state_bar,
                "contact": filing_request.filing_attorney.contact_info.dict()
            },
            "documents": [],
            "service": {
                "method": filing_request.service_info.service_type.value,
                "parties": len(filing_request.service_info.served_parties),
                "certificate_included": filing_request.service_info.certificate_required
            },
            "fees": [],
            "system_config": state_config["system_name"]
        }
        
        # Add document details
        for doc in documents:
            doc_data = {
                "id": str(doc.id),
                "title": doc.metadata.title,
                "type": doc.metadata.document_type.value,
                "file_name": doc.file_name,
                "pages": doc.metadata.page_count,
                "security_level": doc.metadata.security_level
            }
            filing_data["documents"].append(doc_data)
        
        return filing_data
    
    async def _submit_to_state_system(
        self,
        filing_data: Dict,
        session_token: str,
        state_config: Dict,
        state: str
    ) -> Dict:
        """Submit filing to state court system"""
        try:
            # In production, would make actual HTTP requests
            # Simulate state-specific processing
            
            await asyncio.sleep(0.2)  # Simulate processing time
            
            # Generate state-specific confirmation
            confirmation_number = f"{state}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            filing_id = f"SF-{state}-{hash(str(filing_data)) % 100000:05d}"
            
            return {
                "success": True,
                "confirmation_number": confirmation_number,
                "filing_id": filing_id,
                "submission_time": datetime.utcnow().isoformat(),
                "message": f"Filing submitted to {state_config['system_name']}"
            }
            
        except Exception as e:
            logger.error(f"State system submission failed: {str(e)}")
            return {
                "success": False,
                "errors": [str(e)]
            }
    
    async def _query_state_status(
        self,
        filing_id: str,
        session_token: str,
        credentials: EFilingCredentials
    ) -> Dict:
        """Query state system for filing status"""
        try:
            # Simulate status query
            import time
            status_code = int(time.time()) % 5
            
            status_map = {
                0: "submitted",
                1: "under_review",
                2: "accepted",
                3: "served",
                4: "completed"
            }
            
            return {
                "found": True,
                "status": status_map[status_code],
                "service_complete": status_code >= 3,
                "court_response": status_code >= 2,
                "hearing_scheduled": status_code == 2,
                "hearing_date": "2024-02-15T14:00:00Z" if status_code == 2 else None,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    async def _cancel_state_filing(
        self,
        filing_id: str,
        session_token: str,
        reason: str
    ) -> Dict:
        """Cancel filing in state system"""
        try:
            # Simulate cancellation process
            # Some state systems allow cancellation within certain timeframes
            
            await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "message": "Filing cancelled successfully",
                "cancellation_time": datetime.utcnow().isoformat(),
                "refund_eligible": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [str(e)]
            }
    
    async def _get_state_next_actions(
        self,
        state: str,
        filing_request: FilingRequest
    ) -> List[str]:
        """Get state-specific next actions after filing"""
        actions = [
            "Monitor email for court notifications",
            "Check court system for status updates"
        ]
        
        if state == "CA":
            actions.append("Serve opposing parties if not done electronically")
            actions.append("Calendar deadline for response (30 days typically)")
        elif state == "NY":
            actions.append("File proof of service if required")
            actions.append("Monitor NYSCEF for court responses")
        elif state == "TX":
            actions.append("Verify service completion")
            actions.append("Prepare for potential hearing")
        
        return actions
    
    def _map_state_status(self, state_status: str) -> FilingStatus:
        """Map state system status to internal filing status"""
        status_mapping = {
            "submitted": FilingStatus.SUBMITTED,
            "under_review": FilingStatus.SUBMITTED,
            "accepted": FilingStatus.ACCEPTED,
            "served": FilingStatus.SERVED,
            "completed": FilingStatus.SERVED,
            "rejected": FilingStatus.REJECTED,
            "cancelled": FilingStatus.CANCELLED,
            "withdrawn": FilingStatus.CANCELLED
        }
        
        return status_mapping.get(state_status.lower(), FilingStatus.SUBMITTED)