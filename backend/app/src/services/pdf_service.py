"""
PDF Processing Service for extracting text from legal documents
"""

import logging
from typing import Optional
import pdfplumber
from pypdf import PdfReader  # pypdf is the successor to PyPDF2
from io import BytesIO

logger = logging.getLogger(__name__)

class PDFService:
    """Service for extracting text from PDF documents"""

    def extract_text_from_pdf(self, pdf_bytes: bytes, filename: str = "") -> str:
        """
        Extract text from PDF using multiple methods for best results

        Args:
            pdf_bytes: PDF file as bytes
            filename: Original filename for logging

        Returns:
            Extracted text string
        """
        try:
            # First, try pdfplumber (better for complex layouts)
            text = self._extract_with_pdfplumber(pdf_bytes)

            if text and len(text.strip()) > 50:
                logger.info(f"Successfully extracted text using pdfplumber from {filename}")
                return text

            # Fallback to pypdf if pdfplumber fails
            text = self._extract_with_pypdf(pdf_bytes)

            if text and len(text.strip()) > 10:
                logger.info(f"Successfully extracted text using pypdf from {filename}")
                return text

            logger.warning(f"Could not extract meaningful text from {filename}")
            return "Error: Could not extract text from this PDF file."

        except Exception as e:
            logger.error(f"Error extracting text from PDF {filename}: {str(e)}")
            return f"Error: Failed to process PDF file - {str(e)}"

    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text using pdfplumber (better for tables and complex layouts)"""
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                text_parts = []

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}\n")
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num} with pdfplumber: {e}")
                        continue

                return "\n".join(text_parts)

        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return None

    def _extract_with_pypdf(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text using pypdf (fallback method)"""
        try:
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            text_parts = []

            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}\n")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num} with pypdf: {e}")
                    continue

            return "\n".join(text_parts)

        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}")
            return None

    def validate_pdf(self, pdf_bytes: bytes) -> bool:
        """
        Validate that the uploaded file is a valid PDF

        Args:
            pdf_bytes: File bytes to validate

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            # Try to open with pypdf
            PdfReader(BytesIO(pdf_bytes))
            return True
        except Exception:
            try:
                # Try to open with pdfplumber
                with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                    # Just check if we can access the first page
                    if len(pdf.pages) > 0:
                        return True
            except Exception:
                pass

        return False

# Global PDF service instance
pdf_service = PDFService()