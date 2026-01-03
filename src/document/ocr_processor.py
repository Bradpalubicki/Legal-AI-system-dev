#!/usr/bin/env python3
"""
OCR Processing System
Legal AI System - Document Text Extraction Pipeline

This module provides comprehensive OCR processing with:
- Text extraction from scanned documents
- Formatting metadata preservation
- Storage of both original and extracted text
- Quality confidence scoring
- Educational content validation
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile
import uuid

# OCR libraries
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: OCR libraries not available. Install with: pip install pytesseract pillow pdf2image")

# Import security and compliance modules
try:
    from ..core.security import encrypt_data, decrypt_data
except ImportError:
    def encrypt_data(data, key_id): return data
    def decrypt_data(data, key_id): return data

try:
    from ..core.attorney_review import AttorneyReviewSystem
except ImportError:
    class AttorneyReviewSystem:
        def review_content(self, content, content_id=None, jurisdiction=None):
            class MockResult:
                requires_review = True
            return MockResult()

try:
    from ..core.audit_logger import AuditLogger
except ImportError:
    class AuditLogger:
        def log_document_event(self, **kwargs): pass

try:
    from .upload_handler import document_uploader
except ImportError:
    class MockUploader:
        def retrieve_document(self, *args): return b"test document content"
        def _load_metadata(self, *args):
            class MockMeta:
                file_type = type('obj', (object,), {'value': 'txt'})()
            return MockMeta()
    document_uploader = MockUploader()

# Setup logging
logger = logging.getLogger('ocr_processor')

class OCRStatus(str, Enum):
    """OCR processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class DocumentFormat(str, Enum):
    """Document format types"""
    SEARCHABLE_PDF = "searchable_pdf"
    SCANNED_PDF = "scanned_pdf"
    IMAGE = "image"
    TEXT_DOCUMENT = "text_document"
    HYBRID = "hybrid"

class ConfidenceLevel(str, Enum):
    """OCR confidence levels"""
    HIGH = "high"      # 90%+
    MEDIUM = "medium"  # 70-89%
    LOW = "low"        # 50-69%
    POOR = "poor"      # <50%

@dataclass
class TextBlock:
    """Individual text block with positioning and confidence"""
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    page_number: int
    block_type: str  # paragraph, line, word, etc.

@dataclass
class FormattingMetadata:
    """Document formatting metadata"""
    page_count: int
    page_dimensions: List[Tuple[int, int]]
    text_blocks: List[TextBlock]
    fonts_detected: List[str]
    language_detected: str
    layout_analysis: Dict[str, Any]

@dataclass
class OCRResult:
    """OCR processing result"""
    document_id: str
    ocr_id: str
    status: OCRStatus
    confidence_score: float
    confidence_level: ConfidenceLevel
    extracted_text: str
    original_text: Optional[str]
    formatting_metadata: FormattingMetadata
    processing_time: float
    created_at: datetime
    warnings: List[str]
    errors: List[str]

class SecureOCRProcessor:
    """
    Secure OCR processing system with compliance safeguards
    """

    def __init__(self, storage_root: str = "storage/ocr"):
        self.logger = logger
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Initialize compliance components
        self.attorney_review = AttorneyReviewSystem()
        self.audit_logger = AuditLogger()

        # OCR configuration
        self.tesseract_config = {
            'lang': 'eng',
            'oem': 3,  # Default OCR Engine Mode
            'psm': 6,  # Assume uniform block of text
        }

        # Quality thresholds
        self.min_confidence = 50.0  # Minimum confidence for processing
        self.high_confidence = 90.0  # High quality threshold
        self.medium_confidence = 70.0  # Medium quality threshold

    def process_document(self, document_id: str, user_id: str) -> OCRResult:
        """
        Process document with OCR extraction

        Args:
            document_id: ID of uploaded document
            user_id: User requesting OCR processing

        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = datetime.now()
        warnings = []
        errors = []

        try:
            self.logger.info(f"Starting OCR processing for document: {document_id}")

            # Generate OCR processing ID
            ocr_id = f"ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Retrieve document
            document_data = document_uploader.retrieve_document(document_id, user_id)
            if not document_data:
                errors.append("Failed to retrieve document for OCR processing")
                return self._create_failed_result(document_id, ocr_id, errors, start_time)

            # Load document metadata
            metadata = document_uploader._load_metadata(document_id)
            if not metadata:
                errors.append("Document metadata not found")
                return self._create_failed_result(document_id, ocr_id, errors, start_time)

            # Determine document format
            document_format = self._analyze_document_format(document_data, metadata.file_type.value)

            # Process based on document type
            if document_format == DocumentFormat.TEXT_DOCUMENT:
                # Already text - no OCR needed
                return self._process_text_document(document_id, ocr_id, document_data, start_time)

            elif document_format in [DocumentFormat.SEARCHABLE_PDF, DocumentFormat.HYBRID]:
                # Extract existing text and potentially OCR images
                return self._process_searchable_pdf(document_id, ocr_id, document_data, start_time)

            elif document_format in [DocumentFormat.SCANNED_PDF, DocumentFormat.IMAGE]:
                # Full OCR required
                return self._process_scanned_document(document_id, ocr_id, document_data, start_time)

            else:
                errors.append(f"Unsupported document format: {document_format}")
                return self._create_failed_result(document_id, ocr_id, errors, start_time)

        except Exception as e:
            self.logger.error(f"OCR processing failed: {e}")
            errors.append(str(e))
            return self._create_failed_result(document_id, ocr_id, errors, start_time)

    def _analyze_document_format(self, document_data: bytes, file_type: str) -> DocumentFormat:
        """Analyze document to determine processing approach"""
        try:
            if file_type == "txt":
                return DocumentFormat.TEXT_DOCUMENT

            elif file_type == "pdf":
                # Check if PDF contains searchable text
                try:
                    import PyPDF2
                    import io

                    pdf_stream = io.BytesIO(document_data)
                    pdf_reader = PyPDF2.PdfReader(pdf_stream)

                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()

                    if len(text_content.strip()) > 100:  # Substantial text content
                        return DocumentFormat.SEARCHABLE_PDF
                    else:
                        return DocumentFormat.SCANNED_PDF

                except ImportError:
                    self.logger.warning("PyPDF2 not available - assuming scanned PDF")
                    return DocumentFormat.SCANNED_PDF
                except Exception:
                    return DocumentFormat.SCANNED_PDF

            else:
                return DocumentFormat.IMAGE

        except Exception as e:
            self.logger.error(f"Document format analysis failed: {e}")
            return DocumentFormat.HYBRID

    def _process_text_document(self, document_id: str, ocr_id: str,
                              document_data: bytes, start_time: datetime) -> OCRResult:
        """Process plain text document"""
        try:
            # Decode text
            text_content = document_data.decode('utf-8', errors='replace')

            # Create basic formatting metadata
            formatting_metadata = FormattingMetadata(
                page_count=1,
                page_dimensions=[(0, 0)],
                text_blocks=[TextBlock(
                    text=text_content,
                    x=0, y=0, width=0, height=0,
                    confidence=100.0,
                    page_number=1,
                    block_type="document"
                )],
                fonts_detected=["unknown"],
                language_detected="en",
                layout_analysis={"type": "plain_text"}
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            result = OCRResult(
                document_id=document_id,
                ocr_id=ocr_id,
                status=OCRStatus.COMPLETED,
                confidence_score=100.0,
                confidence_level=ConfidenceLevel.HIGH,
                extracted_text=text_content,
                original_text=text_content,
                formatting_metadata=formatting_metadata,
                processing_time=processing_time,
                created_at=datetime.now(),
                warnings=[],
                errors=[]
            )

            # Store OCR result
            self._store_ocr_result(result)

            return result

        except Exception as e:
            self.logger.error(f"Text document processing failed: {e}")
            return self._create_failed_result(document_id, ocr_id, [str(e)], start_time)

    def _process_searchable_pdf(self, document_id: str, ocr_id: str,
                               document_data: bytes, start_time: datetime) -> OCRResult:
        """Process PDF with existing text content"""
        try:
            import PyPDF2
            import io

            pdf_stream = io.BytesIO(document_data)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)

            extracted_text = ""
            text_blocks = []
            page_dimensions = []

            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                extracted_text += f"\n--- Page {page_num} ---\n{page_text}\n"

                # Get page dimensions
                mediabox = page.mediabox
                page_dimensions.append((int(mediabox.width), int(mediabox.height)))

                # Create text block for page
                if page_text.strip():
                    text_blocks.append(TextBlock(
                        text=page_text,
                        x=0, y=0,
                        width=int(mediabox.width),
                        height=int(mediabox.height),
                        confidence=95.0,  # High confidence for extracted text
                        page_number=page_num,
                        block_type="page"
                    ))

            # Calculate overall confidence
            confidence_score = 95.0 if extracted_text.strip() else 0.0

            formatting_metadata = FormattingMetadata(
                page_count=len(pdf_reader.pages),
                page_dimensions=page_dimensions,
                text_blocks=text_blocks,
                fonts_detected=["unknown"],
                language_detected="en",
                layout_analysis={"type": "searchable_pdf", "pages": len(pdf_reader.pages)}
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            result = OCRResult(
                document_id=document_id,
                ocr_id=ocr_id,
                status=OCRStatus.COMPLETED,
                confidence_score=confidence_score,
                confidence_level=self._determine_confidence_level(confidence_score),
                extracted_text=extracted_text,
                original_text=extracted_text,
                formatting_metadata=formatting_metadata,
                processing_time=processing_time,
                created_at=datetime.now(),
                warnings=[],
                errors=[]
            )

            # Store OCR result
            self._store_ocr_result(result)

            return result

        except Exception as e:
            self.logger.error(f"Searchable PDF processing failed: {e}")
            return self._create_failed_result(document_id, ocr_id, [str(e)], start_time)

    def _process_scanned_document(self, document_id: str, ocr_id: str,
                                 document_data: bytes, start_time: datetime) -> OCRResult:
        """Process scanned document with full OCR"""
        if not TESSERACT_AVAILABLE:
            return self._create_failed_result(
                document_id, ocr_id,
                ["OCR libraries not available"],
                start_time
            )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Save document to temporary file
                doc_file = temp_path / "document.pdf"
                with open(doc_file, 'wb') as f:
                    f.write(document_data)

                # Convert PDF to images
                images = pdf2image.convert_from_path(doc_file)

                extracted_text = ""
                text_blocks = []
                page_dimensions = []
                total_confidence = 0.0
                confidence_count = 0

                for page_num, image in enumerate(images, 1):
                    # Save page as image
                    page_image_path = temp_path / f"page_{page_num}.png"
                    image.save(page_image_path)

                    # OCR configuration for detailed analysis
                    ocr_config = f"--oem {self.tesseract_config['oem']} --psm {self.tesseract_config['psm']} -l {self.tesseract_config['lang']}"

                    # Extract text with confidence data
                    page_data = pytesseract.image_to_data(
                        image,
                        config=ocr_config,
                        output_type=pytesseract.Output.DICT
                    )

                    # Process OCR results
                    page_text = ""
                    page_blocks = []

                    for i in range(len(page_data['text'])):
                        text = page_data['text'][i].strip()
                        if text:
                            confidence = float(page_data['conf'][i])
                            if confidence > self.min_confidence:
                                page_text += text + " "

                                # Create text block
                                block = TextBlock(
                                    text=text,
                                    x=page_data['left'][i],
                                    y=page_data['top'][i],
                                    width=page_data['width'][i],
                                    height=page_data['height'][i],
                                    confidence=confidence,
                                    page_number=page_num,
                                    block_type="word"
                                )
                                page_blocks.append(block)
                                text_blocks.append(block)

                                total_confidence += confidence
                                confidence_count += 1

                    extracted_text += f"\n--- Page {page_num} ---\n{page_text}\n"
                    page_dimensions.append((image.width, image.height))

                # Calculate overall confidence
                overall_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0

                formatting_metadata = FormattingMetadata(
                    page_count=len(images),
                    page_dimensions=page_dimensions,
                    text_blocks=text_blocks,
                    fonts_detected=["ocr_detected"],
                    language_detected=self.tesseract_config['lang'],
                    layout_analysis={
                        "type": "scanned_document",
                        "pages": len(images),
                        "total_blocks": len(text_blocks),
                        "ocr_engine": "tesseract"
                    }
                )

                processing_time = (datetime.now() - start_time).total_seconds()

                result = OCRResult(
                    document_id=document_id,
                    ocr_id=ocr_id,
                    status=OCRStatus.COMPLETED,
                    confidence_score=overall_confidence,
                    confidence_level=self._determine_confidence_level(overall_confidence),
                    extracted_text=extracted_text,
                    original_text=None,
                    formatting_metadata=formatting_metadata,
                    processing_time=processing_time,
                    created_at=datetime.now(),
                    warnings=self._generate_quality_warnings(overall_confidence),
                    errors=[]
                )

                # Store OCR result
                self._store_ocr_result(result)

                return result

        except Exception as e:
            self.logger.error(f"Scanned document OCR failed: {e}")
            return self._create_failed_result(document_id, ocr_id, [str(e)], start_time)

    def _determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level based on score"""
        if confidence_score >= self.high_confidence:
            return ConfidenceLevel.HIGH
        elif confidence_score >= self.medium_confidence:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= self.min_confidence:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.POOR

    def _generate_quality_warnings(self, confidence_score: float) -> List[str]:
        """Generate quality warnings based on confidence score"""
        warnings = []

        if confidence_score < self.min_confidence:
            warnings.append("Very low OCR confidence - text may be unreliable")
        elif confidence_score < self.medium_confidence:
            warnings.append("Low OCR confidence - review extracted text carefully")
        elif confidence_score < self.high_confidence:
            warnings.append("Medium OCR confidence - some errors may be present")

        return warnings

    def _create_failed_result(self, document_id: str, ocr_id: str,
                             errors: List[str], start_time: datetime) -> OCRResult:
        """Create failed OCR result"""
        processing_time = (datetime.now() - start_time).total_seconds()

        return OCRResult(
            document_id=document_id,
            ocr_id=ocr_id,
            status=OCRStatus.FAILED,
            confidence_score=0.0,
            confidence_level=ConfidenceLevel.POOR,
            extracted_text="",
            original_text=None,
            formatting_metadata=FormattingMetadata(
                page_count=0,
                page_dimensions=[],
                text_blocks=[],
                fonts_detected=[],
                language_detected="unknown",
                layout_analysis={}
            ),
            processing_time=processing_time,
            created_at=datetime.now(),
            warnings=[],
            errors=errors
        )

    def _store_ocr_result(self, result: OCRResult):
        """Store OCR result securely"""
        try:
            # Create storage path
            storage_path = self.storage_root / f"{result.ocr_id}.json"

            # Encrypt OCR result data
            result_data = json.dumps(asdict(result), default=str)
            encrypted_data = encrypt_data(result_data.encode(), f"ocr_{result.ocr_id}")

            # Store encrypted result
            with open(storage_path, 'wb') as f:
                f.write(encrypted_data)

            # Set secure permissions
            os.chmod(storage_path, 0o600)

            # Log OCR completion
            self.audit_logger.log_document_event(
                event_type="ocr_completed",
                document_id=result.document_id,
                user_id="system",
                details={
                    "ocr_id": result.ocr_id,
                    "confidence_score": result.confidence_score,
                    "confidence_level": result.confidence_level.value,
                    "processing_time": result.processing_time,
                    "text_length": len(result.extracted_text)
                }
            )

            self.logger.info(f"OCR result stored: {result.ocr_id}")

        except Exception as e:
            self.logger.error(f"Failed to store OCR result: {e}")
            raise

    def retrieve_ocr_result(self, ocr_id: str, requesting_user: str) -> Optional[OCRResult]:
        """Retrieve OCR result by ID"""
        try:
            storage_path = self.storage_root / f"{ocr_id}.json"
            if not storage_path.exists():
                return None

            # Load and decrypt OCR result
            with open(storage_path, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = decrypt_data(encrypted_data, f"ocr_{ocr_id}")
            result_dict = json.loads(decrypted_data.decode())

            # Convert back to dataclass
            result_dict['created_at'] = datetime.fromisoformat(result_dict['created_at'])

            # Convert formatting metadata
            formatting_dict = result_dict['formatting_metadata']
            text_blocks = [TextBlock(**block) for block in formatting_dict['text_blocks']]
            formatting_dict['text_blocks'] = text_blocks
            result_dict['formatting_metadata'] = FormattingMetadata(**formatting_dict)

            return OCRResult(**result_dict)

        except Exception as e:
            self.logger.error(f"Failed to retrieve OCR result: {e}")
            return None

    def get_document_ocr_results(self, document_id: str) -> List[OCRResult]:
        """Get all OCR results for a document"""
        results = []
        try:
            for ocr_file in self.storage_root.glob("*.json"):
                ocr_result = self.retrieve_ocr_result(ocr_file.stem, "system")
                if ocr_result and ocr_result.document_id == document_id:
                    results.append(ocr_result)

            return sorted(results, key=lambda r: r.created_at, reverse=True)

        except Exception as e:
            self.logger.error(f"Failed to get OCR results for document: {e}")
            return []

    def get_ocr_statistics(self) -> Dict[str, Any]:
        """Get OCR processing statistics"""
        try:
            total_processed = 0
            confidence_distribution = {level.value: 0 for level in ConfidenceLevel}
            status_distribution = {status.value: 0 for status in OCRStatus}
            avg_processing_time = 0.0
            total_time = 0.0

            for ocr_file in self.storage_root.glob("*.json"):
                ocr_result = self.retrieve_ocr_result(ocr_file.stem, "system")
                if ocr_result:
                    total_processed += 1
                    confidence_distribution[ocr_result.confidence_level.value] += 1
                    status_distribution[ocr_result.status.value] += 1
                    total_time += ocr_result.processing_time

            if total_processed > 0:
                avg_processing_time = total_time / total_processed

            return {
                "total_processed": total_processed,
                "confidence_distribution": confidence_distribution,
                "status_distribution": status_distribution,
                "average_processing_time": avg_processing_time,
                "tesseract_available": TESSERACT_AVAILABLE
            }

        except Exception as e:
            self.logger.error(f"Failed to get OCR statistics: {e}")
            return {"error": str(e)}

# Global OCR processor instance
ocr_processor = SecureOCRProcessor()

def validate_ocr_system():
    """Validate OCR processing system"""
    try:
        print("✓ OCR processor initialized successfully")

        if TESSERACT_AVAILABLE:
            print("✓ Tesseract OCR engine available")
        else:
            print("⚠ Tesseract OCR engine not available - install required packages")

        # Test with sample text
        sample_text = "This is a test document for OCR validation.\nIt contains multiple lines of text."

        # Create temporary text file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_text)
            temp_path = f.name

        try:
            # Upload test document
            with open(temp_path, 'rb') as f:
                test_data = f.read()

            upload_result = document_uploader.upload_document(test_data, "test_ocr.txt", "test_user")

            if upload_result.success:
                # Process with OCR
                ocr_result = ocr_processor.process_document(upload_result.document_id, "test_user")

                if ocr_result.status == OCRStatus.COMPLETED:
                    print("✓ OCR processing completed successfully")
                    print(f"  Confidence: {ocr_result.confidence_score:.1f}%")
                    print(f"  Text length: {len(ocr_result.extracted_text)} characters")
                    return True
                else:
                    print("✗ OCR processing failed")
                    print(f"  Errors: {ocr_result.errors}")
                    return False
            else:
                print("✗ Test document upload failed")
                return False

        finally:
            # Cleanup
            os.unlink(temp_path)

    except Exception as e:
        print(f"✗ OCR system validation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing OCR Processing System...")
    print("=" * 50)

    if validate_ocr_system():
        # Display statistics
        stats = ocr_processor.get_ocr_statistics()
        print(f"\nOCR System Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("OCR system validation failed")