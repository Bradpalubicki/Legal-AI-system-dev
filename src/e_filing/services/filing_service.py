"""
E-Filing Service

Central service for managing electronic court filing operations across
multiple court systems including Federal (CM/ECF) and state systems.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from ..models import (
    FilingRequest,
    FilingResponse,
    FilingStatus,
    CourtDocument,
    CaseInfo,
    EFilingCredentials,
    AuditLog
)
from ..adapters.federal_adapter import FederalCourtAdapter
from ..adapters.state_adapter import StateCourtAdapter
from ..processors.document_processor import DocumentProcessor
from ..validators.filing_validator import FilingValidator

logger = logging.getLogger(__name__)


class EFilingService:
    """
    Central e-filing service that coordinates document filing across
    multiple court systems with validation, processing, and tracking.
    """
    
    def __init__(self):
        self.adapters = {}
        self.document_processor = DocumentProcessor()
        self.filing_validator = FilingValidator()
        
        # Initialize court system adapters
        self.adapters["federal"] = FederalCourtAdapter()
        self.adapters["state"] = StateCourtAdapter()
        
        # Filing queues and tracking
        self.active_filings: Dict[UUID, FilingRequest] = {}
        self.filing_history: List[FilingResponse] = []
        
        # Service configuration
        self.max_concurrent_filings = 10
        self.retry_attempts = 3
        self.retry_delay_seconds = 30
        
        logger.info("E-Filing service initialized")
    
    async def submit_filing(
        self,
        filing_request: FilingRequest,
        credentials: EFilingCredentials,
        validate_only: bool = False
    ) -> FilingResponse:
        """
        Submit an electronic filing to the appropriate court system
        """
        start_time = datetime.utcnow()
        
        try:
            # Add to active filings
            self.active_filings[filing_request.id] = filing_request
            
            # Update filing status
            filing_request.status = FilingStatus.PENDING_VALIDATION
            
            # Validate filing request
            validation_result = await self._validate_filing(filing_request)
            if not validation_result["valid"]:
                filing_request.status = FilingStatus.VALIDATION_FAILED
                filing_request.processing_errors = validation_result["errors"]
                
                return FilingResponse(
                    filing_id=filing_request.id,
                    success=False,
                    status=FilingStatus.VALIDATION_FAILED,
                    message="Filing validation failed",
                    errors=validation_result["errors"]
                )
            
            # Return early if validation only
            if validate_only:
                return FilingResponse(
                    filing_id=filing_request.id,
                    success=True,
                    status=FilingStatus.DRAFT,
                    message="Validation successful - ready for submission",
                    warnings=validation_result.get("warnings", [])
                )
            
            # Process documents
            filing_request.status = FilingStatus.PENDING_SUBMISSION
            processed_docs = await self._process_documents(filing_request.documents)
            
            # Get appropriate court adapter
            adapter = self._get_court_adapter(filing_request.case_info.court)
            
            # Submit to court system
            submission_result = await adapter.submit_filing(
                filing_request, processed_docs, credentials
            )
            
            # Update filing status based on result
            if submission_result.success:
                filing_request.status = FilingStatus.SUBMITTED
                filing_request.submission_date = datetime.utcnow()
                filing_request.confirmation_number = submission_result.confirmation_number
                filing_request.external_id = submission_result.transaction_id
            else:
                filing_request.status = FilingStatus.REJECTED
                filing_request.processing_errors = submission_result.errors
            
            # Log filing activity
            await self._log_filing_activity(
                filing_request, credentials, "submit", submission_result.success
            )
            
            # Add to history
            self.filing_history.append(submission_result)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Filing submission completed in {processing_time:.2f}s")
            
            return submission_result
            
        except Exception as e:
            filing_request.status = FilingStatus.REJECTED
            error_msg = f"Filing submission failed: {str(e)}"
            filing_request.processing_errors.append(error_msg)
            
            logger.error(error_msg)
            
            return FilingResponse(
                filing_id=filing_request.id,
                success=False,
                status=FilingStatus.REJECTED,
                message=error_msg,
                errors=[str(e)]
            )
        
        finally:
            # Remove from active filings
            self.active_filings.pop(filing_request.id, None)
    
    async def check_filing_status(
        self,
        filing_id: UUID,
        credentials: EFilingCredentials
    ) -> FilingResponse:
        """
        Check the status of a submitted filing
        """
        try:
            # Get filing from active filings or history
            filing_request = self.active_filings.get(filing_id)
            
            if not filing_request:
                # Look for it in filing history
                historical_filing = next(
                    (f for f in self.filing_history if f.filing_id == filing_id),
                    None
                )
                if not historical_filing:
                    return FilingResponse(
                        filing_id=filing_id,
                        success=False,
                        status=FilingStatus.REJECTED,
                        message="Filing not found",
                        errors=["Filing ID not found in system"]
                    )
                return historical_filing
            
            # Get court adapter
            adapter = self._get_court_adapter(filing_request.case_info.court)
            
            # Check status with court system
            if filing_request.external_id:
                court_status = await adapter.check_filing_status(
                    filing_request.external_id, credentials
                )
                
                # Update local status if changed
                if court_status.status != filing_request.status:
                    filing_request.status = court_status.status
                    await self._log_filing_activity(
                        filing_request, credentials, "status_update", True
                    )
                
                return court_status
            else:
                # Return current local status
                return FilingResponse(
                    filing_id=filing_id,
                    success=True,
                    status=filing_request.status,
                    message=f"Filing status: {filing_request.status.value}"
                )
                
        except Exception as e:
            logger.error(f"Status check failed for filing {filing_id}: {str(e)}")
            return FilingResponse(
                filing_id=filing_id,
                success=False,
                status=FilingStatus.REJECTED,
                message=f"Status check failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def cancel_filing(
        self,
        filing_id: UUID,
        credentials: EFilingCredentials,
        reason: Optional[str] = None
    ) -> FilingResponse:
        """
        Cancel a pending or submitted filing
        """
        try:
            filing_request = self.active_filings.get(filing_id)
            if not filing_request:
                return FilingResponse(
                    filing_id=filing_id,
                    success=False,
                    status=FilingStatus.REJECTED,
                    message="Filing not found or already completed",
                    errors=["Filing ID not found in active filings"]
                )
            
            # Check if filing can be cancelled
            if filing_request.status in [FilingStatus.ACCEPTED, FilingStatus.SERVED]:
                return FilingResponse(
                    filing_id=filing_id,
                    success=False,
                    status=filing_request.status,
                    message="Filing cannot be cancelled - already accepted/served",
                    errors=["Filing is past cancellation point"]
                )
            
            # Cancel with court system if submitted
            if filing_request.status == FilingStatus.SUBMITTED and filing_request.external_id:
                adapter = self._get_court_adapter(filing_request.case_info.court)
                court_result = await adapter.cancel_filing(
                    filing_request.external_id, credentials, reason
                )
                
                if not court_result.success:
                    return court_result
            
            # Update local status
            filing_request.status = FilingStatus.CANCELLED
            
            # Log cancellation
            await self._log_filing_activity(
                filing_request, credentials, "cancel", True, reason
            )
            
            return FilingResponse(
                filing_id=filing_id,
                success=True,
                status=FilingStatus.CANCELLED,
                message=f"Filing cancelled successfully. Reason: {reason or 'Not specified'}"
            )
            
        except Exception as e:
            logger.error(f"Filing cancellation failed: {str(e)}")
            return FilingResponse(
                filing_id=filing_id,
                success=False,
                status=FilingStatus.REJECTED,
                message=f"Cancellation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def get_filing_history(
        self,
        attorney_id: Optional[UUID] = None,
        case_id: Optional[UUID] = None,
        status: Optional[FilingStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[FilingResponse]:
        """
        Retrieve filing history with optional filters
        """
        try:
            filtered_history = self.filing_history.copy()
            
            # Apply filters
            if attorney_id:
                filtered_history = [
                    f for f in filtered_history
                    if hasattr(f, 'attorney_id') and f.attorney_id == attorney_id
                ]
            
            if status:
                filtered_history = [
                    f for f in filtered_history if f.status == status
                ]
            
            if date_from:
                filtered_history = [
                    f for f in filtered_history if f.timestamp >= date_from
                ]
            
            if date_to:
                filtered_history = [
                    f for f in filtered_history if f.timestamp <= date_to
                ]
            
            # Sort by timestamp (most recent first) and limit
            filtered_history.sort(key=lambda x: x.timestamp, reverse=True)
            return filtered_history[:limit]
            
        except Exception as e:
            logger.error(f"Filing history retrieval failed: {str(e)}")
            return []
    
    async def estimate_filing_fees(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, Decimal]:
        """
        Estimate filing fees for a given filing request
        """
        try:
            adapter = self._get_court_adapter(filing_request.case_info.court)
            fee_estimate = await adapter.calculate_fees(filing_request)
            
            return fee_estimate
            
        except Exception as e:
            logger.error(f"Fee estimation failed: {str(e)}")
            return {"error": Decimal('0'), "estimated_total": Decimal('0')}
    
    async def _validate_filing(self, filing_request: FilingRequest) -> Dict[str, any]:
        """
        Validate filing request before submission
        """
        try:
            # Basic validation
            basic_validation = await self.filing_validator.validate_basic_requirements(
                filing_request
            )
            
            if not basic_validation["valid"]:
                return basic_validation
            
            # Document validation
            document_validation = await self.filing_validator.validate_documents(
                filing_request.documents
            )
            
            if not document_validation["valid"]:
                return document_validation
            
            # Court-specific validation
            adapter = self._get_court_adapter(filing_request.case_info.court)
            court_validation = await adapter.validate_filing(filing_request)
            
            # Combine all validation results
            all_errors = []
            all_warnings = []
            
            for validation in [basic_validation, document_validation, court_validation]:
                all_errors.extend(validation.get("errors", []))
                all_warnings.extend(validation.get("warnings", []))
            
            return {
                "valid": len(all_errors) == 0,
                "errors": all_errors,
                "warnings": all_warnings
            }
            
        except Exception as e:
            logger.error(f"Filing validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    async def _process_documents(
        self,
        documents: List[CourtDocument]
    ) -> List[CourtDocument]:
        """
        Process documents for filing (validation, conversion, etc.)
        """
        processed_docs = []
        
        for doc in documents:
            try:
                # Process document
                processed_doc = await self.document_processor.process_document(doc)
                processed_docs.append(processed_doc)
                
            except Exception as e:
                logger.error(f"Document processing failed for {doc.file_name}: {str(e)}")
                doc.status = "processing_failed"
                doc.validation_errors.append(str(e))
                processed_docs.append(doc)
        
        return processed_docs
    
    def _get_court_adapter(self, court_info):
        """
        Get appropriate court adapter based on court type
        """
        if court_info.court_type.value.startswith("federal"):
            return self.adapters["federal"]
        else:
            return self.adapters["state"]
    
    async def _log_filing_activity(
        self,
        filing_request: FilingRequest,
        credentials: EFilingCredentials,
        action: str,
        success: bool,
        details: Optional[str] = None
    ):
        """
        Log filing activity for audit purposes
        """
        try:
            audit_log = AuditLog(
                action=action,
                entity_type="filing",
                entity_id=filing_request.id,
                attorney_id=credentials.attorney_id,
                description=f"Filing {action} for case {filing_request.case_info.case_number}",
                system="e_filing_service",
                court_system=filing_request.court_system,
                success=success,
                error_message=details if not success else None
            )
            
            # In production, this would be saved to database
            logger.info(f"Audit log: {audit_log.action} - {audit_log.description}")
            
        except Exception as e:
            logger.error(f"Audit logging failed: {str(e)}")
    
    async def get_service_status(self) -> Dict[str, any]:
        """
        Get current service status and statistics
        """
        try:
            total_filings = len(self.filing_history)
            active_filings_count = len(self.active_filings)
            
            # Calculate success rate
            successful_filings = len([f for f in self.filing_history if f.success])
            success_rate = (successful_filings / total_filings) if total_filings > 0 else 0
            
            # Get adapter status
            adapter_status = {}
            for name, adapter in self.adapters.items():
                adapter_status[name] = await adapter.get_health_status()
            
            return {
                "service_status": "healthy",
                "active_filings": active_filings_count,
                "total_filings_processed": total_filings,
                "success_rate": round(success_rate, 3),
                "court_adapters": adapter_status,
                "max_concurrent_filings": self.max_concurrent_filings,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Service status check failed: {str(e)}")
            return {
                "service_status": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def cleanup_completed_filings(self, days_old: int = 30):
        """
        Clean up old completed filings from memory
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Clean up filing history
            original_count = len(self.filing_history)
            self.filing_history = [
                f for f in self.filing_history
                if f.timestamp > cutoff_date
            ]
            
            cleaned_count = original_count - len(self.filing_history)
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old filing records")
            
        except Exception as e:
            logger.error(f"Filing cleanup failed: {str(e)}")
    
    async def retry_failed_filing(
        self,
        filing_id: UUID,
        credentials: EFilingCredentials
    ) -> FilingResponse:
        """
        Retry a failed filing submission
        """
        try:
            # Find the filing in history
            original_filing = next(
                (f for f in self.filing_history if f.filing_id == filing_id),
                None
            )
            
            if not original_filing:
                return FilingResponse(
                    filing_id=filing_id,
                    success=False,
                    status=FilingStatus.REJECTED,
                    message="Original filing not found",
                    errors=["Filing ID not found"]
                )
            
            if original_filing.success:
                return FilingResponse(
                    filing_id=filing_id,
                    success=False,
                    status=original_filing.status,
                    message="Filing was already successful",
                    errors=["Cannot retry successful filing"]
                )
            
            # Recreate filing request (would normally come from database)
            # This is a simplified version
            return FilingResponse(
                filing_id=filing_id,
                success=False,
                status=FilingStatus.REJECTED,
                message="Retry functionality requires database integration",
                errors=["Retry not implemented without persistent storage"]
            )
            
        except Exception as e:
            logger.error(f"Filing retry failed: {str(e)}")
            return FilingResponse(
                filing_id=filing_id,
                success=False,
                status=FilingStatus.REJECTED,
                message=f"Retry failed: {str(e)}",
                errors=[str(e)]
            )