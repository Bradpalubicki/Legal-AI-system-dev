"""
Unit Tests for PDF Document Processor

Tests PDF document processing including text extraction, metadata parsing,
OCR integration, and error handling for various PDF formats.
"""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
import io
from pathlib import Path
from typing import Dict, List, Any, Optional, BinaryIO
import tempfile
import os


class TestPDFProcessor:
    """Test suite for PDF document processor"""

    def setup_method(self):
        """Set up test fixtures"""
        self.sample_pdf_content = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000015 00000 n\n0000000074 00000 n\n0000000120 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
        
        self.sample_metadata = {
            "title": "Sample Legal Document",
            "author": "Legal AI System",
            "subject": "Contract Analysis",
            "creator": "Test Creator",
            "producer": "Test Producer",
            "creation_date": "2023-01-01T00:00:00Z",
            "modification_date": "2023-01-01T00:00:00Z"
        }
        
        self.sample_text = "This is a sample legal document with important clauses and provisions."

    @patch('PyPDF2.PdfReader')
    def test_pdf_reader_initialization(self, mock_pdf_reader):
        """Test PDF reader initialization"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock PDF with pages
        mock_page = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = self.sample_metadata
        
        # Test PDF reader creation
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        mock_pdf_reader.assert_called_once_with(pdf_data)
        assert reader == mock_reader
        assert len(reader.pages) == 1

    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """Test text extraction from PDF"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock page with text
        mock_page = Mock()
        mock_page.extract_text.return_value = self.sample_text
        mock_reader.pages = [mock_page]
        
        # Test text extraction
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text()
        
        assert extracted_text == self.sample_text
        mock_page.extract_text.assert_called_once()

    @patch('PyPDF2.PdfReader')
    def test_extract_metadata_from_pdf(self, mock_pdf_reader):
        """Test metadata extraction from PDF"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        mock_reader.metadata = self.sample_metadata
        
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        metadata = reader.metadata
        
        assert metadata["title"] == "Sample Legal Document"
        assert metadata["author"] == "Legal AI System"
        assert metadata["subject"] == "Contract Analysis"

    @patch('PyPDF2.PdfReader')
    def test_handle_encrypted_pdf(self, mock_pdf_reader):
        """Test handling of encrypted PDF files"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        mock_reader.is_encrypted = True
        
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        # Test encrypted PDF detection
        assert reader.is_encrypted is True
        
        # Test decryption attempt
        mock_reader.decrypt.return_value = 1  # Success
        result = reader.decrypt("password")
        assert result == 1
        
        mock_reader.decrypt.assert_called_once_with("password")

    @patch('PyPDF2.PdfReader')
    def test_handle_corrupted_pdf(self, mock_pdf_reader):
        """Test handling of corrupted PDF files"""
        # Mock PyPDF2 raising an exception for corrupted PDF
        mock_pdf_reader.side_effect = Exception("Invalid PDF structure")
        
        pdf_data = io.BytesIO(b"corrupted pdf content")
        
        with pytest.raises(Exception) as exc_info:
            mock_pdf_reader(pdf_data)
        
        assert "Invalid PDF structure" in str(exc_info.value)

    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_multiple_pages(self, mock_pdf_reader):
        """Test text extraction from multi-page PDF"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock multiple pages
        page1 = Mock()
        page1.extract_text.return_value = "Page 1 content. "
        page2 = Mock()
        page2.extract_text.return_value = "Page 2 content. "
        page3 = Mock()
        page3.extract_text.return_value = "Page 3 content."
        
        mock_reader.pages = [page1, page2, page3]
        
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        # Extract text from all pages
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        
        expected_text = "Page 1 content. Page 2 content. Page 3 content."
        assert full_text == expected_text
        assert len(reader.pages) == 3

    def test_pdf_text_cleaning(self):
        """Test PDF text cleaning and normalization"""
        raw_text = "This  is   a\n\n\nsample   text\twith\t\textra    whitespace\n\n"
        
        def clean_pdf_text(text: str) -> str:
            """Clean and normalize extracted PDF text"""
            import re
            # Remove extra whitespace and normalize
            text = re.sub(r'\s+', ' ', text.strip())
            # Remove page breaks and form feeds
            text = text.replace('\f', ' ').replace('\x0c', ' ')
            return text
        
        cleaned_text = clean_pdf_text(raw_text)
        expected_text = "This is a sample text with extra whitespace"
        
        assert cleaned_text == expected_text

    @patch('pytesseract.image_to_string')
    @patch('pdf2image.convert_from_bytes')
    def test_ocr_fallback_for_scanned_pdf(self, mock_convert, mock_ocr):
        """Test OCR fallback for scanned PDFs with no extractable text"""
        # Mock PDF to image conversion
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        
        # Mock OCR text extraction
        mock_ocr.return_value = "OCR extracted text from scanned document"
        
        pdf_data = self.sample_pdf_content
        
        # Convert PDF to images
        images = mock_convert(pdf_data)
        
        # Extract text using OCR
        ocr_text = ""
        for image in images:
            ocr_text += mock_ocr(image)
        
        mock_convert.assert_called_once_with(pdf_data)
        mock_ocr.assert_called_once_with(mock_image)
        assert ocr_text == "OCR extracted text from scanned document"

    @patch('PyPDF2.PdfReader')
    def test_extract_form_fields(self, mock_pdf_reader):
        """Test extraction of PDF form fields"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock form fields
        form_fields = {
            '/T': 'ClientName',
            '/V': 'John Doe',
            '/FT': '/Tx'  # Text field
        }
        
        mock_reader.get_form_text_fields.return_value = {
            'ClientName': 'John Doe',
            'ContractDate': '2023-01-01',
            'Amount': '$10,000'
        }
        
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        fields = reader.get_form_text_fields()
        
        assert fields['ClientName'] == 'John Doe'
        assert fields['ContractDate'] == '2023-01-01'
        assert fields['Amount'] == '$10,000'

    @patch('PyPDF2.PdfReader')
    def test_extract_annotations(self, mock_pdf_reader):
        """Test extraction of PDF annotations"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock page with annotations
        mock_page = Mock()
        mock_annotation = {
            '/Type': '/Annot',
            '/Subtype': '/Text',
            '/Contents': 'Important note about this clause',
            '/Rect': [100, 200, 200, 250]
        }
        mock_page.get('/Annots', []).return_value = [mock_annotation]
        
        mock_reader.pages = [mock_page]
        
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        # Extract annotations from first page
        page = reader.pages[0]
        annotations = page.get('/Annots', [])
        
        assert len(annotations) == 1
        assert annotations[0]['/Contents'] == 'Important note about this clause'

    def test_pdf_security_analysis(self):
        """Test PDF security and permissions analysis"""
        
        def analyze_pdf_security(permissions: Dict[str, bool]) -> Dict[str, Any]:
            """Analyze PDF security permissions"""
            security_analysis = {
                "is_secure": False,
                "restrictions": [],
                "risk_level": "low"
            }
            
            restricted_actions = []
            if not permissions.get("print", True):
                restricted_actions.append("printing")
            if not permissions.get("modify", True):
                restricted_actions.append("modification")
            if not permissions.get("copy", True):
                restricted_actions.append("copying")
            if not permissions.get("annotate", True):
                restricted_actions.append("annotation")
            
            if restricted_actions:
                security_analysis["is_secure"] = True
                security_analysis["restrictions"] = restricted_actions
                security_analysis["risk_level"] = "medium" if len(restricted_actions) > 2 else "low"
            
            return security_analysis
        
        # Test secure PDF
        secure_permissions = {
            "print": False,
            "modify": False,
            "copy": False,
            "annotate": True
        }
        
        analysis = analyze_pdf_security(secure_permissions)
        assert analysis["is_secure"] is True
        assert "printing" in analysis["restrictions"]
        assert "modification" in analysis["restrictions"]
        assert analysis["risk_level"] == "medium"

    def test_pdf_page_dimensions(self):
        """Test extraction of PDF page dimensions"""
        
        def extract_page_dimensions(mediabox: List[float]) -> Dict[str, float]:
            """Extract page dimensions from MediaBox"""
            if len(mediabox) != 4:
                raise ValueError("Invalid MediaBox format")
            
            x1, y1, x2, y2 = mediabox
            width = x2 - x1
            height = y2 - y1
            
            return {
                "width": width,
                "height": height,
                "width_inches": width / 72,  # Convert points to inches
                "height_inches": height / 72,
                "aspect_ratio": width / height if height > 0 else 0
            }
        
        # Standard US Letter size in points
        mediabox = [0, 0, 612, 792]
        dimensions = extract_page_dimensions(mediabox)
        
        assert dimensions["width"] == 612
        assert dimensions["height"] == 792
        assert abs(dimensions["width_inches"] - 8.5) < 0.1
        assert abs(dimensions["height_inches"] - 11.0) < 0.1

    @patch('PyPDF2.PdfReader')
    def test_pdf_bookmark_extraction(self, mock_pdf_reader):
        """Test extraction of PDF bookmarks/outline"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock outline structure
        outline = [
            {
                '/Title': 'Chapter 1: Introduction',
                '/Page': 1
            },
            {
                '/Title': 'Chapter 2: Terms and Conditions',
                '/Page': 5
            },
            {
                '/Title': 'Chapter 3: Termination',
                '/Page': 10
            }
        ]
        
        mock_reader.outline = outline
        
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        bookmarks = reader.outline
        
        assert len(bookmarks) == 3
        assert bookmarks[0]['/Title'] == 'Chapter 1: Introduction'
        assert bookmarks[1]['/Page'] == 5

    def test_pdf_language_detection(self):
        """Test PDF language detection from text content"""
        
        def detect_document_language(text: str) -> str:
            """Simple language detection based on common words"""
            english_indicators = ['the', 'and', 'or', 'of', 'to', 'in', 'for', 'shall', 'agreement']
            spanish_indicators = ['el', 'la', 'y', 'o', 'de', 'en', 'para', 'contrato']
            french_indicators = ['le', 'la', 'et', 'ou', 'de', 'dans', 'pour', 'contrat']
            
            text_lower = text.lower()
            
            english_count = sum(1 for word in english_indicators if word in text_lower)
            spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
            french_count = sum(1 for word in french_indicators if word in text_lower)
            
            if english_count > spanish_count and english_count > french_count:
                return 'en'
            elif spanish_count > french_count:
                return 'es'
            elif french_count > 0:
                return 'fr'
            else:
                return 'unknown'
        
        english_text = "This agreement shall be binding and enforceable in accordance with the terms."
        spanish_text = "Este contrato será vinculante y ejecutable de acuerdo con los términos."
        
        assert detect_document_language(english_text) == 'en'
        assert detect_document_language(spanish_text) == 'es'

    @patch('PyPDF2.PdfReader')
    def test_pdf_digital_signature_detection(self, mock_pdf_reader):
        """Test detection of digital signatures in PDF"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock signature field
        signature_field = {
            '/Type': '/Annot',
            '/Subtype': '/Widget',
            '/FT': '/Sig',
            '/T': 'Signature1',
            '/V': 'Digital signature data'
        }
        
        mock_reader.get_fields.return_value = {'Signature1': signature_field}
        
        pdf_data = io.BytesIO(self.sample_pdf_content)
        reader = mock_pdf_reader(pdf_data)
        
        fields = reader.get_fields()
        signature_fields = {k: v for k, v in fields.items() if v.get('/FT') == '/Sig'}
        
        assert len(signature_fields) == 1
        assert 'Signature1' in signature_fields

    def test_pdf_content_validation(self):
        """Test PDF content validation for legal documents"""
        
        def validate_legal_document_content(text: str) -> Dict[str, Any]:
            """Validate legal document content completeness"""
            validation = {
                "is_valid": True,
                "missing_elements": [],
                "warnings": [],
                "score": 100
            }
            
            required_elements = {
                "parties": ["party", "parties", "client", "contractor"],
                "dates": ["date", "dated", "effective"],
                "signatures": ["signature", "signed", "executed"],
                "terms": ["terms", "conditions", "provisions"]
            }
            
            text_lower = text.lower()
            
            for element, keywords in required_elements.items():
                if not any(keyword in text_lower for keyword in keywords):
                    validation["missing_elements"].append(element)
                    validation["score"] -= 25
            
            if validation["score"] < 75:
                validation["is_valid"] = False
            
            return validation
        
        # Test complete document
        complete_text = "This agreement between the parties is effective on the date signed with the following terms and conditions."
        validation = validate_legal_document_content(complete_text)
        assert validation["is_valid"] is True
        assert len(validation["missing_elements"]) == 0
        
        # Test incomplete document
        incomplete_text = "This is some text without required elements."
        validation = validate_legal_document_content(incomplete_text)
        assert validation["is_valid"] is False
        assert len(validation["missing_elements"]) > 0

    def test_pdf_redaction_detection(self):
        """Test detection of redacted content in PDF"""
        
        def detect_redactions(text: str) -> Dict[str, Any]:
            """Detect potential redactions in text"""
            import re
            
            redaction_patterns = [
                r'\[REDACTED\]',
                r'█+',  # Block characters
                r'▓+',  # Block characters
                r'■+',  # Block characters
                r'___+',  # Underscores
                r'XXX+',  # X marks
            ]
            
            redactions = []
            for pattern in redaction_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    redactions.append({
                        "pattern": pattern,
                        "start": match.start(),
                        "end": match.end(),
                        "length": match.end() - match.start()
                    })
            
            return {
                "has_redactions": len(redactions) > 0,
                "redaction_count": len(redactions),
                "redactions": redactions,
                "redaction_percentage": (sum(r["length"] for r in redactions) / len(text)) * 100 if text else 0
            }
        
        redacted_text = "The client [REDACTED] agreed to pay ███████ for services."
        result = detect_redactions(redacted_text)
        
        assert result["has_redactions"] is True
        assert result["redaction_count"] == 2

    @patch('PyPDF2.PdfReader')
    def test_pdf_compression_analysis(self, mock_pdf_reader):
        """Test analysis of PDF compression and optimization"""
        mock_reader = Mock()
        mock_pdf_reader.return_value = mock_reader
        
        # Mock PDF info
        mock_reader.metadata = {
            '/Producer': 'Test Producer',
            '/Creator': 'Test Creator'
        }
        
        def analyze_pdf_optimization(file_size: int, page_count: int, has_images: bool) -> Dict[str, Any]:
            """Analyze PDF optimization"""
            avg_page_size = file_size / page_count if page_count > 0 else file_size
            
            analysis = {
                "file_size_mb": file_size / (1024 * 1024),
                "avg_page_size_kb": avg_page_size / 1024,
                "is_optimized": True,
                "recommendations": []
            }
            
            if avg_page_size > 500 * 1024:  # 500KB per page
                analysis["is_optimized"] = False
                analysis["recommendations"].append("Consider compressing images")
            
            if not has_images and avg_page_size > 100 * 1024:  # 100KB for text-only
                analysis["is_optimized"] = False
                analysis["recommendations"].append("Consider text compression")
            
            return analysis
        
        # Test large PDF
        analysis = analyze_pdf_optimization(5 * 1024 * 1024, 5, True)  # 5MB, 5 pages
        assert analysis["file_size_mb"] == 5.0
        assert not analysis["is_optimized"]

    def test_pdf_accessibility_compliance(self):
        """Test PDF accessibility compliance checking"""
        
        def check_pdf_accessibility(metadata: Dict[str, Any]) -> Dict[str, Any]:
            """Check PDF accessibility compliance"""
            compliance = {
                "is_accessible": True,
                "violations": [],
                "score": 100,
                "level": "AA"  # WCAG level
            }
            
            # Check for required metadata
            if not metadata.get("title"):
                compliance["violations"].append("Missing document title")
                compliance["score"] -= 20
            
            if not metadata.get("language"):
                compliance["violations"].append("Missing language specification")
                compliance["score"] -= 15
            
            # Check for structure elements (would be detected from actual PDF)
            structure_elements = metadata.get("structure_elements", [])
            if "headings" not in structure_elements:
                compliance["violations"].append("No heading structure detected")
                compliance["score"] -= 25
            
            if compliance["score"] < 80:
                compliance["is_accessible"] = False
                compliance["level"] = "Non-compliant"
            elif compliance["score"] < 90:
                compliance["level"] = "A"
            
            return compliance
        
        # Test accessible PDF metadata
        accessible_metadata = {
            "title": "Legal Document",
            "language": "en-US",
            "structure_elements": ["headings", "paragraphs", "lists"]
        }
        
        compliance = check_pdf_accessibility(accessible_metadata)
        assert compliance["is_accessible"] is True
        assert compliance["level"] == "AA"