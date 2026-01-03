"""
Filing Validator

Comprehensive validation for electronic court filings including
document requirements, case information, and court-specific rules.
"""

import logging
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from ..models import (
    FilingRequest,
    CourtDocument,
    FilingStatus,
    CourtType,
    DocumentType,
    ServiceType
)

logger = logging.getLogger(__name__)


class FilingValidator:
    """
    Comprehensive validator for e-filing requests ensuring compliance
    with court requirements and legal filing standards.
    """
    
    def __init__(self):
        # Standard validation rules
        self.validation_rules = {
            "max_documents_per_filing": 99,
            "max_case_title_length": 200,
            "max_description_length": 1000,
            "required_metadata_fields": [
                "title", "document_type", "created_date"
            ],
            "valid_security_levels": ["public", "sealed", "restricted"],
            "max_party_count": 50
        }
        
        # Court-specific requirements
        self.court_requirements = {
            "federal": {
                "requires_pacer_id": True,
                "requires_case_number": True,
                "max_file_size_mb": 50,
                "supports_sealed_docs": True,
                "certificate_of_service_required": True
            },
            "state": {
                "requires_bar_number": True,
                "requires_case_number": True,
                "max_file_size_mb": 35,
                "supports_sealed_docs": False,
                "certificate_of_service_required": False
            }
        }
        
        logger.info("Filing validator initialized")
    
    async def validate_basic_requirements(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, any]:
        """
        Validate basic filing requirements that apply to all courts
        """
        errors = []
        warnings = []
        
        try:
            # Validate case information
            case_errors = await self._validate_case_info(filing_request.case_info)
            errors.extend(case_errors)
            
            # Validate documents
            if not filing_request.documents:
                errors.append("Filing must include at least one document")
            else:
                if len(filing_request.documents) > self.validation_rules["max_documents_per_filing"]:
                    errors.append(f"Too many documents ({len(filing_request.documents)}), maximum is {self.validation_rules['max_documents_per_filing']}")
                
                # Validate primary document exists
                primary_doc_exists = any(
                    doc.id == filing_request.primary_document 
                    for doc in filing_request.documents
                )
                if not primary_doc_exists:
                    errors.append("Primary document not found in documents list")
            
            # Validate filing description
            if not filing_request.filing_description:
                errors.append("Filing description is required")
            elif len(filing_request.filing_description) > self.validation_rules["max_description_length"]:
                errors.append("Filing description too long")
            
            # Validate filing attorney
            attorney_errors = await self._validate_attorney_info(filing_request.filing_attorney)
            errors.extend(attorney_errors)
            
            # Validate service information
            service_errors = await self._validate_service_info(filing_request.service_info)
            errors.extend(service_errors)
            
            # Validate fees
            fee_errors = await self._validate_fees(filing_request.filing_fees)
            errors.extend(fee_errors)
            
            # Check for warnings
            if filing_request.hearing_date and filing_request.hearing_date < datetime.utcnow():
                warnings.append("Hearing date is in the past")
            
            if len(filing_request.case_info.parties) > 10:
                warnings.append("Large number of parties may require special handling")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validation_type": "basic_requirements"
            }
            
        except Exception as e:
            logger.error(f"Basic validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": warnings
            }
    
    async def validate_documents(
        self,
        documents: List[CourtDocument]
    ) -> Dict[str, any]:
        """
        Validate all documents in a filing
        """
        errors = []
        warnings = []
        
        try:
            for i, document in enumerate(documents):
                doc_errors = await self._validate_single_document(document, i + 1)
                errors.extend(doc_errors)
                
                # Document-specific warnings
                if document.metadata.page_count and document.metadata.page_count > 100:
                    warnings.append(f"Document {i + 1} ({document.file_name}) has {document.metadata.page_count} pages - consider splitting")
                
                if document.metadata.security_level == "sealed" and document.metadata.document_type in [DocumentType.EXHIBIT, DocumentType.AFFIDAVIT]:
                    warnings.append(f"Document {i + 1} is marked sealed - verify court authorization")
            
            # Check for duplicate document titles
            titles = [doc.metadata.title for doc in documents]
            duplicates = [title for title in titles if titles.count(title) > 1]
            if duplicates:
                unique_duplicates = list(set(duplicates))
                warnings.append(f"Duplicate document titles found: {', '.join(unique_duplicates)}")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validation_type": "documents",
                "document_count": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Document validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Document validation error: {str(e)}"],
                "warnings": warnings
            }
    
    async def validate_court_specific_requirements(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, any]:
        """
        Validate court-specific requirements
        """
        errors = []
        warnings = []
        
        try:
            court_type = filing_request.case_info.court.court_type
            
            # Determine court category
            if court_type.value.startswith("federal"):
                requirements = self.court_requirements["federal"]
                court_category = "federal"
            else:
                requirements = self.court_requirements["state"]
                court_category = "state"
            
            # Validate based on court category
            if court_category == "federal":
                federal_errors = await self._validate_federal_requirements(filing_request)
                errors.extend(federal_errors)
            else:
                state_errors = await self._validate_state_requirements(filing_request)
                errors.extend(state_errors)
            
            # Common court-specific validations
            if requirements["requires_case_number"] and not filing_request.case_info.case_number:
                errors.append("Case number is required for this court")
            
            if requirements["certificate_of_service_required"]:
                has_certificate = any(
                    doc.metadata.document_type == DocumentType.CERTIFICATE
                    for doc in filing_request.documents
                )
                service_complete = filing_request.service_info.certificate_filed
                
                if not has_certificate and not service_complete:
                    errors.append("Certificate of service is required")
            
            # Check sealed document support
            has_sealed_docs = any(
                doc.metadata.security_level == "sealed"
                for doc in filing_request.documents
            )
            
            if has_sealed_docs and not requirements["supports_sealed_docs"]:
                errors.append("This court does not support sealed documents through e-filing")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validation_type": "court_specific",
                "court_category": court_category,
                "court_type": court_type.value
            }
            
        except Exception as e:
            logger.error(f"Court-specific validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Court validation error: {str(e)}"],
                "warnings": warnings
            }
    
    async def _validate_case_info(self, case_info) -> List[str]:
        """Validate case information"""
        errors = []
        
        if not case_info.case_title:
            errors.append("Case title is required")
        elif len(case_info.case_title) > self.validation_rules["max_case_title_length"]:
            errors.append(f"Case title too long (max {self.validation_rules['max_case_title_length']} characters)")
        
        if not case_info.case_type:
            errors.append("Case type is required")
        
        if not case_info.court:
            errors.append("Court information is required")
        
        # Validate parties
        if not case_info.parties:
            errors.append("At least one party is required")
        elif len(case_info.parties) > self.validation_rules["max_party_count"]:
            errors.append(f"Too many parties (max {self.validation_rules['max_party_count']})")
        
        # Validate case number format if provided
        if case_info.case_number:
            if not self._validate_case_number_format(case_info.case_number, case_info.court.court_type):
                errors.append(f"Invalid case number format: {case_info.case_number}")
        
        return errors
    
    async def _validate_attorney_info(self, attorney) -> List[str]:
        """Validate filing attorney information"""
        errors = []
        
        if not attorney:
            errors.append("Filing attorney information is required")
            return errors
        
        if not attorney.first_name or not attorney.last_name:
            errors.append("Attorney first and last name are required")
        
        if not attorney.bar_number:
            errors.append("Attorney bar number is required")
        
        if not attorney.state_bar:
            errors.append("Attorney state bar admission is required")
        
        # Validate contact information
        if not attorney.contact_info.email:
            errors.append("Attorney email address is required")
        
        if not attorney.contact_info.phone:
            errors.append("Attorney phone number is required")
        
        # Check if attorney is active
        if not attorney.is_active:
            errors.append("Filing attorney must have active bar status")
        
        return errors
    
    async def _validate_service_info(self, service_info) -> List[str]:
        """Validate service of process information"""
        errors = []
        
        if not service_info:
            errors.append("Service information is required")
            return errors
        
        # Validate service type
        valid_service_types = [st.value for st in ServiceType]
        if service_info.service_type.value not in valid_service_types:
            errors.append(f"Invalid service type: {service_info.service_type.value}")
        
        # Validate electronic service requirements
        if service_info.service_type == ServiceType.ELECTRONIC:
            if not service_info.email_addresses:
                errors.append("Email addresses required for electronic service")
            else:
                # Validate email format
                for email in service_info.email_addresses:
                    if not self._validate_email_format(str(email)):
                        errors.append(f"Invalid email format: {email}")
        
        # Check service date
        if service_info.service_date and service_info.service_date > datetime.utcnow():
            errors.append("Service date cannot be in the future")
        
        return errors
    
    async def _validate_fees(self, filing_fees) -> List[str]:
        """Validate filing fees"""
        errors = []
        
        for fee in filing_fees:
            if fee.amount < 0:
                errors.append(f"Filing fee amount cannot be negative: {fee.amount}")
            
            if fee.waiver_requested and not fee.waiver_reason:
                errors.append("Fee waiver reason is required when waiver is requested")
            
            if fee.paid_date and fee.paid_date > datetime.utcnow():
                errors.append("Fee payment date cannot be in the future")
        
        return errors
    
    async def _validate_single_document(self, document: CourtDocument, doc_number: int) -> List[str]:
        """Validate a single document"""
        errors = []
        
        # Basic document validation
        if not document.file_name:
            errors.append(f"Document {doc_number}: File name is required")
        
        if not document.file_content and not document.file_url:
            errors.append(f"Document {doc_number}: File content or URL is required")
        
        # Metadata validation
        metadata = document.metadata
        
        for field in self.validation_rules["required_metadata_fields"]:
            if not getattr(metadata, field, None):
                errors.append(f"Document {doc_number}: {field} is required in metadata")
        
        if metadata.security_level not in self.validation_rules["valid_security_levels"]:
            errors.append(f"Document {doc_number}: Invalid security level: {metadata.security_level}")
        
        # File format validation
        if not document.file_name.lower().endswith('.pdf'):
            errors.append(f"Document {doc_number}: Must be in PDF format")
        
        if document.mime_type != "application/pdf":
            errors.append(f"Document {doc_number}: MIME type must be application/pdf")
        
        # Page count validation
        if metadata.page_count and metadata.page_count > 500:
            errors.append(f"Document {doc_number}: Exceeds maximum page count (500)")
        
        return errors
    
    async def _validate_federal_requirements(self, filing_request: FilingRequest) -> List[str]:
        """Validate federal court specific requirements"""
        errors = []
        
        # Federal case number format
        case_number = filing_request.case_info.case_number
        if case_number and not re.match(r'^\d:\d{2}-[a-z]{2}-\d{5}', case_number, re.IGNORECASE):
            errors.append("Federal case number must follow format: D:YY-TT-NNNNN")
        
        # PACER ID requirement (would check attorney credentials in production)
        attorney = filing_request.filing_attorney
        if not attorney.federal_bar_id and not attorney.pacer_id:
            errors.append("PACER ID or federal bar admission required for federal courts")
        
        # Electronic service preference in federal courts
        if filing_request.service_info.service_type != ServiceType.ELECTRONIC:
            # This is a warning in federal validation, handled elsewhere
            pass
        
        return errors
    
    async def _validate_state_requirements(self, filing_request: FilingRequest) -> List[str]:
        """Validate state court specific requirements"""
        errors = []
        
        state = filing_request.case_info.court.state
        
        # State-specific validations
        if state == "CA":
            errors.extend(await self._validate_california_requirements(filing_request))
        elif state == "NY":
            errors.extend(await self._validate_new_york_requirements(filing_request))
        elif state == "TX":
            errors.extend(await self._validate_texas_requirements(filing_request))
        
        return errors
    
    async def _validate_california_requirements(self, filing_request: FilingRequest) -> List[str]:
        """California-specific validation requirements"""
        errors = []
        
        # California requires proof of service for most filings
        case_type = filing_request.case_info.case_type.lower()
        if "family" not in case_type and not filing_request.service_info.certificate_required:
            # Would be more nuanced in production
            pass
        
        return errors
    
    async def _validate_new_york_requirements(self, filing_request: FilingRequest) -> List[str]:
        """New York-specific validation requirements"""
        errors = []
        
        # NYSCEF specific requirements would go here
        
        return errors
    
    async def _validate_texas_requirements(self, filing_request: FilingRequest) -> List[str]:
        """Texas-specific validation requirements"""
        errors = []
        
        # Texas specific requirements would go here
        
        return errors
    
    def _validate_case_number_format(self, case_number: str, court_type: CourtType) -> bool:
        """Validate case number format based on court type"""
        if court_type.value.startswith("federal"):
            # Federal format: D:YY-TT-NNNNN
            return bool(re.match(r'^\d:\d{2}-[a-z]{2}-\d{5}', case_number, re.IGNORECASE))
        else:
            # State formats vary - basic validation
            return len(case_number.strip()) >= 5
    
    def _validate_email_format(self, email: str) -> bool:
        """Basic email format validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def validate_complete_filing(
        self,
        filing_request: FilingRequest
    ) -> Dict[str, any]:
        """
        Perform complete validation of a filing request
        """
        all_errors = []
        all_warnings = []
        
        try:
            # Basic requirements validation
            basic_result = await self.validate_basic_requirements(filing_request)
            all_errors.extend(basic_result.get("errors", []))
            all_warnings.extend(basic_result.get("warnings", []))
            
            # Document validation
            doc_result = await self.validate_documents(filing_request.documents)
            all_errors.extend(doc_result.get("errors", []))
            all_warnings.extend(doc_result.get("warnings", []))
            
            # Court-specific validation
            court_result = await self.validate_court_specific_requirements(filing_request)
            all_errors.extend(court_result.get("errors", []))
            all_warnings.extend(court_result.get("warnings", []))
            
            return {
                "valid": len(all_errors) == 0,
                "errors": all_errors,
                "warnings": all_warnings,
                "validation_summary": {
                    "basic_requirements": basic_result["valid"],
                    "documents": doc_result["valid"],
                    "court_specific": court_result["valid"],
                    "total_errors": len(all_errors),
                    "total_warnings": len(all_warnings)
                }
            }
            
        except Exception as e:
            logger.error(f"Complete validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation system error: {str(e)}"],
                "warnings": all_warnings
            }