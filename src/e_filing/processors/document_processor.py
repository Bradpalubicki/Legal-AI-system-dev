"""
Document Processor

Core document processing for e-filing system including validation,
conversion, metadata extraction, and format standardization.
"""

import hashlib
import logging
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from ..models import CourtDocument, DocumentMetadata, DocumentType

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Central document processor for e-filing system handling validation,
    conversion, and metadata extraction for court documents.
    """
    
    def __init__(self):
        self.supported_formats = [
            "application/pdf",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        self.max_file_size_bytes = 50 * 1024 * 1024  # 50MB default
        self.max_page_count = 500
        
        # Document type detection patterns
        self.type_patterns = {
            DocumentType.COMPLAINT: [
                "complaint", "petition", "initial pleading", "civil action"
            ],
            DocumentType.MOTION: [
                "motion", "application", "request for", "motion to", "motion for"
            ],
            DocumentType.RESPONSE: [
                "response", "answer", "reply", "opposition", "counter"
            ],
            DocumentType.BRIEF: [
                "brief", "memorandum of law", "legal brief", "appellate brief"
            ],
            DocumentType.MEMORANDUM: [
                "memorandum", "memo", "legal memorandum", "supporting memorandum"
            ],
            DocumentType.ORDER: [
                "order", "judgment", "ruling", "decision", "decree"
            ],
            DocumentType.NOTICE: [
                "notice", "notification", "service", "summons"
            ],
            DocumentType.EXHIBIT: [
                "exhibit", "attachment", "appendix", "schedule"
            ],
            DocumentType.AFFIDAVIT: [
                "affidavit", "sworn statement", "declaration under penalty"
            ],
            DocumentType.DECLARATION: [
                "declaration", "statement", "testimony", "witness statement"
            ]
        }
        
        logger.info("Document processor initialized")
    
    async def process_document(self, document: CourtDocument) -> CourtDocument:
        """
        Process a court document for e-filing including validation,
        metadata extraction, and format standardization.
        """
        try:
            logger.info(f"Processing document: {document.file_name}")
            
            # Validate document format
            validation_errors = await self.validate_document(document)
            if validation_errors:
                document.validation_errors.extend(validation_errors)
                document.status = "validation_failed"
                return document
            
            # Extract and enhance metadata
            enhanced_metadata = await self.extract_metadata(document)
            document.metadata = enhanced_metadata
            
            # Generate file hash for integrity
            if document.file_content:
                document.metadata.file_hash = self._generate_file_hash(document.file_content)
                document.metadata.file_size_bytes = len(document.file_content)
            
            # Convert to standard format if needed
            if document.mime_type != "application/pdf":
                converted_doc = await self.convert_to_pdf(document)
                if converted_doc:
                    document = converted_doc
            
            # Extract text content for indexing
            text_content = await self.extract_text_content(document)
            if text_content:
                document.metadata.word_count = len(text_content.split())
            
            # Validate final document
            final_validation = await self.validate_processed_document(document)
            if final_validation:
                document.validation_errors.extend(final_validation)
                document.status = "processing_failed"
            else:
                document.status = "processed"
            
            logger.info(f"Document processing completed: {document.file_name}")
            return document
            
        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            logger.error(error_msg)
            document.validation_errors.append(error_msg)
            document.status = "processing_failed"
            return document
    
    async def validate_document(self, document: CourtDocument) -> List[str]:
        """
        Validate document against e-filing requirements
        """
        errors = []
        
        try:
            # Check file name
            if not document.file_name:
                errors.append("Document file name is required")
            elif len(document.file_name) > 255:
                errors.append("File name too long (max 255 characters)")
            elif not self._is_valid_filename(document.file_name):
                errors.append("File name contains invalid characters")
            
            # Check MIME type
            if document.mime_type not in self.supported_formats:
                errors.append(f"Unsupported file format: {document.mime_type}")
            
            # Check file content
            if not document.file_content and not document.file_url:
                errors.append("Document content or URL is required")
            
            # Check file size
            if document.file_content:
                if len(document.file_content) == 0:
                    errors.append("Document file is empty")
                elif len(document.file_content) > self.max_file_size_bytes:
                    size_mb = len(document.file_content) / (1024 * 1024)
                    errors.append(f"File size ({size_mb:.1f}MB) exceeds limit ({self.max_file_size_bytes / (1024 * 1024):.0f}MB)")
            
            # Check metadata
            if not document.metadata.title:
                errors.append("Document title is required")
            
            if document.metadata.page_count and document.metadata.page_count > self.max_page_count:
                errors.append(f"Document has {document.metadata.page_count} pages, exceeds limit of {self.max_page_count}")
            
            # Validate security level
            valid_security_levels = ["public", "sealed", "restricted"]
            if document.metadata.security_level not in valid_security_levels:
                errors.append(f"Invalid security level: {document.metadata.security_level}")
            
            return errors
            
        except Exception as e:
            logger.error(f"Document validation error: {str(e)}")
            return [f"Validation error: {str(e)}"]
    
    async def extract_metadata(self, document: CourtDocument) -> DocumentMetadata:
        """
        Extract and enhance document metadata
        """
        try:
            metadata = document.metadata
            
            # Auto-detect document type if not set
            if metadata.document_type == DocumentType.OTHER:
                detected_type = await self._detect_document_type(
                    metadata.title, document.file_name
                )
                metadata.document_type = detected_type
            
            # Set creation date if not provided
            if not metadata.created_date:
                metadata.created_date = datetime.utcnow()
            
            # Extract page count if PDF and not already set
            if (document.mime_type == "application/pdf" and 
                not metadata.page_count and 
                document.file_content):
                page_count = await self._extract_pdf_page_count(document.file_content)
                metadata.page_count = page_count
            
            # Generate description if not provided
            if not metadata.description:
                metadata.description = self._generate_description(
                    metadata.title, metadata.document_type
                )
            
            # Set redacted flag based on content analysis
            if document.file_content:
                is_redacted = await self._check_for_redactions(document.file_content)
                metadata.redacted = is_redacted
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return document.metadata
    
    async def convert_to_pdf(self, document: CourtDocument) -> Optional[CourtDocument]:
        """
        Convert document to PDF format if needed
        """
        try:
            if document.mime_type == "application/pdf":
                return document  # Already PDF
            
            # In production, would use actual conversion libraries
            # For now, simulate conversion
            logger.info(f"Converting {document.file_name} to PDF")
            
            # Simulate conversion process
            if document.mime_type == "text/plain":
                # Would convert text to PDF
                converted_content = await self._text_to_pdf(document.file_content)
            elif document.mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                # Would convert Word document to PDF
                converted_content = await self._word_to_pdf(document.file_content)
            else:
                logger.warning(f"Cannot convert {document.mime_type} to PDF")
                return None
            
            if converted_content:
                # Update document with converted content
                document.file_content = converted_content
                document.mime_type = "application/pdf"
                document.file_name = document.file_name.rsplit('.', 1)[0] + ".pdf"
                
                logger.info(f"Document converted to PDF: {document.file_name}")
                return document
            
            return None
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            return None
    
    async def extract_text_content(self, document: CourtDocument) -> Optional[str]:
        """
        Extract text content from document for indexing and analysis
        """
        try:
            if not document.file_content:
                return None
            
            if document.mime_type == "application/pdf":
                return await self._extract_pdf_text(document.file_content)
            elif document.mime_type == "text/plain":
                return document.file_content.decode('utf-8', errors='ignore')
            elif document.mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                return await self._extract_word_text(document.file_content)
            
            return None
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return None
    
    async def validate_processed_document(self, document: CourtDocument) -> List[str]:
        """
        Final validation of processed document
        """
        errors = []
        
        try:
            # Ensure document is in PDF format
            if document.mime_type != "application/pdf":
                errors.append("Document must be in PDF format for filing")
            
            # Check for required metadata
            if not document.metadata.file_hash:
                errors.append("Document hash is required for integrity verification")
            
            if not document.metadata.page_count or document.metadata.page_count == 0:
                errors.append("Valid page count is required")
            
            # Check for corruption
            if document.file_content and len(document.file_content) < 100:
                errors.append("Document appears to be corrupted or too small")
            
            return errors
            
        except Exception as e:
            logger.error(f"Final validation error: {str(e)}")
            return [f"Final validation error: {str(e)}"]
    
    def _generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _is_valid_filename(self, filename: str) -> bool:
        """Check if filename contains valid characters"""
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\']
        return not any(char in filename for char in invalid_chars)
    
    async def _detect_document_type(self, title: str, filename: str) -> DocumentType:
        """
        Detect document type based on title and filename
        """
        combined_text = f"{title} {filename}".lower()
        
        for doc_type, patterns in self.type_patterns.items():
            if any(pattern in combined_text for pattern in patterns):
                return doc_type
        
        return DocumentType.OTHER
    
    def _generate_description(self, title: str, doc_type: DocumentType) -> str:
        """
        Generate document description based on title and type
        """
        if doc_type != DocumentType.OTHER:
            return f"{doc_type.value.replace('_', ' ').title()}: {title}"
        else:
            return title
    
    async def _extract_pdf_page_count(self, pdf_content: bytes) -> int:
        """
        Extract page count from PDF content
        In production, would use PyPDF2 or similar library
        """
        try:
            # Simplified page count extraction
            # In production, would use proper PDF library
            content_str = pdf_content.decode('latin-1', errors='ignore')
            page_count = content_str.count('/Type/Page')
            return max(1, page_count)  # At least 1 page
        except:
            return 1  # Default to 1 page if extraction fails
    
    async def _check_for_redactions(self, file_content: bytes) -> bool:
        """
        Check if document contains redacted content
        """
        try:
            # Simple check for redaction indicators
            content_str = file_content.decode('utf-8', errors='ignore').lower()
            redaction_indicators = ['[redacted]', '***', 'blacked out', 'redaction']
            return any(indicator in content_str for indicator in redaction_indicators)
        except:
            return False
    
    async def _text_to_pdf(self, text_content: bytes) -> bytes:
        """
        Convert text content to PDF
        In production, would use libraries like reportlab
        """
        # Placeholder - would implement actual text to PDF conversion
        logger.info("Converting text to PDF (placeholder)")
        return text_content  # Placeholder
    
    async def _word_to_pdf(self, word_content: bytes) -> bytes:
        """
        Convert Word document to PDF
        In production, would use libraries like python-docx + reportlab
        """
        # Placeholder - would implement actual Word to PDF conversion
        logger.info("Converting Word document to PDF (placeholder)")
        return word_content  # Placeholder
    
    async def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF content
        In production, would use PyPDF2, pdfplumber, or similar
        """
        try:
            # Placeholder for PDF text extraction
            # In production, would use proper PDF parsing
            content_str = pdf_content.decode('latin-1', errors='ignore')
            
            # Extract basic text (very simplified)
            text_parts = []
            lines = content_str.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('%') and not line.startswith('<<'):
                    text_parts.append(line.strip())
            
            return ' '.join(text_parts[:1000])  # Limit extraction for demo
        except:
            return ""
    
    async def _extract_word_text(self, word_content: bytes) -> str:
        """
        Extract text from Word document
        In production, would use python-docx or similar
        """
        try:
            # Placeholder for Word text extraction
            logger.info("Extracting text from Word document (placeholder)")
            return "Word document text extraction placeholder"
        except:
            return ""
    
    async def batch_process_documents(self, documents: List[CourtDocument]) -> List[CourtDocument]:
        """
        Process multiple documents in batch
        """
        processed_documents = []
        
        for document in documents:
            try:
                processed_doc = await self.process_document(document)
                processed_documents.append(processed_doc)
            except Exception as e:
                logger.error(f"Batch processing failed for {document.file_name}: {str(e)}")
                document.validation_errors.append(f"Batch processing error: {str(e)}")
                document.status = "processing_failed"
                processed_documents.append(document)
        
        return processed_documents
    
    def get_processing_stats(self) -> Dict[str, any]:
        """
        Get document processing statistics
        """
        return {
            "supported_formats": self.supported_formats,
            "max_file_size_mb": self.max_file_size_bytes / (1024 * 1024),
            "max_page_count": self.max_page_count,
            "supported_document_types": [dt.value for dt in DocumentType],
            "processor_version": "1.0.0"
        }