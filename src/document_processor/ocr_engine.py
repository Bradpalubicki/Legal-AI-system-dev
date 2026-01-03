"""
Advanced OCR engine using Tesseract for handwritten notes and scanned documents with preprocessing and AI enhancement.
"""
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import os
import tempfile
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pdf2image
import json
import asyncio
from pathlib import Path
import logging

from ..shared.utils.ai_client import AIClient
from .upload_manager import FileInfo, FileType


class OCRMode(Enum):
    """OCR processing modes."""
    PRINTED_TEXT = "printed_text"
    HANDWRITTEN = "handwritten"
    MIXED = "mixed"
    MATHEMATICAL = "mathematical"
    TABLES = "tables"
    FORMS = "forms"
    RECEIPTS = "receipts"
    LEGAL_DOCUMENTS = "legal_documents"


class PreprocessingStep(Enum):
    """Image preprocessing steps."""
    GRAYSCALE = "grayscale"
    GAUSSIAN_BLUR = "gaussian_blur"
    THRESHOLD = "threshold"
    ADAPTIVE_THRESHOLD = "adaptive_threshold"
    MORPHOLOGICAL = "morphological"
    DESKEW = "deskew"
    NOISE_REMOVAL = "noise_removal"
    CONTRAST_ENHANCEMENT = "contrast_enhancement"
    SHARPENING = "sharpening"
    EDGE_DETECTION = "edge_detection"
    ROTATION_CORRECTION = "rotation_correction"


class ConfidenceLevel(Enum):
    """OCR confidence levels."""
    VERY_HIGH = "very_high"      # 90-100%
    HIGH = "high"                # 80-89%
    MEDIUM = "medium"            # 60-79%
    LOW = "low"                  # 40-59%
    VERY_LOW = "very_low"        # 0-39%


@dataclass
class OCRRegion:
    """OCR region within a document."""
    x: int
    y: int
    width: int
    height: int
    text: str
    confidence: float
    word_count: int
    line_count: int
    region_type: str = "text"  # text, table, form, signature, etc.
    language: str = "eng"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OCRWord:
    """Individual word from OCR."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    line_num: int
    word_num: int
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False


@dataclass
class OCRLine:
    """Line of text from OCR."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    words: List[OCRWord]
    line_num: int
    alignment: str = "left"  # left, center, right, justified


@dataclass
class OCRPage:
    """Single page OCR results."""
    page_num: int
    text: str
    confidence: float
    width: int
    height: int
    dpi: int
    regions: List[OCRRegion]
    lines: List[OCRLine]
    words: List[OCRWord]
    preprocessing_applied: List[PreprocessingStep]
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OCRResult:
    """Complete OCR results for a document."""
    file_id: str
    original_filename: str
    total_pages: int
    total_text: str
    average_confidence: float
    confidence_level: ConfidenceLevel
    pages: List[OCRPage]
    languages_detected: List[str]
    ocr_mode: OCRMode
    processing_time: float
    timestamp: datetime
    
    # Quality metrics
    word_count: int
    character_count: int
    low_confidence_words: int
    blank_pages: int
    
    # Enhancement results
    ai_enhanced: bool = False
    enhanced_text: Optional[str] = None
    correction_count: int = 0
    
    # Metadata
    tesseract_version: str = ""
    preprocessing_steps: List[PreprocessingStep] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TesseractOCREngine:
    """Advanced OCR engine using Tesseract with intelligent preprocessing and AI enhancement."""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        # Set Tesseract path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.ai_client = AIClient()
        self.logger = logging.getLogger(__name__)
        
        # Default OCR configurations for different modes
        self.mode_configs = {
            OCRMode.PRINTED_TEXT: {
                'psm': 3,  # Fully automatic page segmentation
                'oem': 3,  # Default OCR Engine Mode
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD
                ]
            },
            OCRMode.HANDWRITTEN: {
                'psm': 6,  # Uniform block of text
                'oem': 1,  # Neural nets LSTM engine only
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.GAUSSIAN_BLUR,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.MORPHOLOGICAL,
                    PreprocessingStep.NOISE_REMOVAL
                ]
            },
            OCRMode.MIXED: {
                'psm': 3,
                'oem': 3,
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.NOISE_REMOVAL
                ]
            },
            OCRMode.MATHEMATICAL: {
                'psm': 6,
                'oem': 3,
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.SHARPENING,
                    PreprocessingStep.THRESHOLD
                ]
            },
            OCRMode.TABLES: {
                'psm': 6,  # Uniform block
                'oem': 3,
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.MORPHOLOGICAL,
                    PreprocessingStep.THRESHOLD
                ]
            },
            OCRMode.LEGAL_DOCUMENTS: {
                'psm': 3,
                'oem': 3,
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.DESKEW,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.NOISE_REMOVAL
                ]
            }
        }
        
        # Language support
        self.supported_languages = [
            'eng', 'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'chi_sim', 'chi_tra',
            'jpn', 'kor', 'ara', 'hin', 'tha', 'vie'
        ]
        
        # Verify Tesseract installation
        self._verify_tesseract()

    def _verify_tesseract(self):
        """Verify Tesseract installation and get version."""
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract version: {version}")
            return True
        except Exception as e:
            self.logger.error(f"Tesseract not found or not properly installed: {e}")
            raise RuntimeError("Tesseract OCR not available")

    async def process_document(
        self, 
        file_info: FileInfo, 
        ocr_mode: OCRMode = OCRMode.MIXED,
        languages: List[str] = None,
        enhance_with_ai: bool = True,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> OCRResult:
        """Process a document with OCR."""
        try:
            start_time = datetime.utcnow()
            self.logger.info(f"Starting OCR processing: {file_info.original_filename}")
            
            # Default to English if no languages specified
            if not languages:
                languages = ['eng']
            
            # Validate languages
            languages = [lang for lang in languages if lang in self.supported_languages]
            if not languages:
                languages = ['eng']
            
            # Get processing configuration
            config = self.mode_configs.get(ocr_mode, self.mode_configs[OCRMode.MIXED])
            if custom_config:
                config.update(custom_config)
            
            # Convert file to images
            images = await self._convert_to_images(file_info)
            if not images:
                raise ValueError("Could not convert file to images for OCR processing")
            
            # Process each page/image
            pages = []
            total_text = ""
            total_confidence = 0.0
            total_words = 0
            low_confidence_words = 0
            blank_pages = 0
            
            for i, image in enumerate(images):
                page_start = datetime.utcnow()
                
                # Preprocess image
                processed_image = await self._preprocess_image(image, config['preprocessing'])
                
                # Perform OCR
                page_result = await self._ocr_image(
                    processed_image, 
                    page_num=i + 1,
                    languages=languages,
                    psm=config['psm'],
                    oem=config['oem'],
                    ocr_mode=ocr_mode
                )
                
                if page_result:
                    page_result.preprocessing_applied = config['preprocessing']
                    page_result.processing_time = (datetime.utcnow() - page_start).total_seconds()
                    
                    pages.append(page_result)
                    total_text += page_result.text + "\n"
                    total_confidence += page_result.confidence
                    total_words += len(page_result.words)
                    
                    # Count low confidence words
                    low_confidence_words += sum(1 for word in page_result.words if word.confidence < 60)
                    
                    # Check for blank pages
                    if len(page_result.text.strip()) < 10:
                        blank_pages += 1
            
            # Calculate averages
            avg_confidence = total_confidence / len(pages) if pages else 0.0
            confidence_level = self._determine_confidence_level(avg_confidence)
            
            # Create OCR result
            ocr_result = OCRResult(
                file_id=file_info.file_id,
                original_filename=file_info.original_filename,
                total_pages=len(pages),
                total_text=total_text.strip(),
                average_confidence=avg_confidence,
                confidence_level=confidence_level,
                pages=pages,
                languages_detected=languages,
                ocr_mode=ocr_mode,
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow(),
                word_count=total_words,
                character_count=len(total_text),
                low_confidence_words=low_confidence_words,
                blank_pages=blank_pages,
                tesseract_version=str(pytesseract.get_tesseract_version()),
                preprocessing_steps=config['preprocessing']
            )
            
            # Enhance with AI if requested
            if enhance_with_ai and ocr_result.total_text.strip():
                enhanced_result = await self._enhance_with_ai(ocr_result)
                if enhanced_result:
                    ocr_result.ai_enhanced = True
                    ocr_result.enhanced_text = enhanced_result['enhanced_text']
                    ocr_result.correction_count = enhanced_result['correction_count']
            
            self.logger.info(f"OCR completed: {file_info.original_filename}, "
                           f"confidence: {avg_confidence:.1f}%, words: {total_words}")
            
            return ocr_result
            
        except Exception as e:
            self.logger.error(f"Error in OCR processing: {e}")
            raise

    async def _convert_to_images(self, file_info: FileInfo) -> List[np.ndarray]:
        """Convert file to images for OCR processing."""
        try:
            images = []
            
            if file_info.file_type == FileType.PDF:
                # Convert PDF to images
                pdf_images = pdf2image.convert_from_path(
                    file_info.final_path,
                    dpi=300,  # High DPI for better OCR
                    fmt='RGB'
                )
                
                for pil_image in pdf_images:
                    # Convert PIL to OpenCV format
                    opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    images.append(opencv_image)
            
            elif file_info.file_type in [FileType.PNG, FileType.JPG, FileType.JPEG, FileType.TIFF]:
                # Load image directly
                image = cv2.imread(file_info.final_path)
                if image is not None:
                    images.append(image)
            
            elif file_info.file_type in [FileType.DOCX, FileType.DOC]:
                # Convert Office document to PDF first, then to images
                # This would require LibreOffice or similar converter
                # For now, return empty list
                self.logger.warning(f"Office document conversion not implemented: {file_info.file_type}")
                return []
            
            return images
            
        except Exception as e:
            self.logger.error(f"Error converting file to images: {e}")
            return []

    async def _preprocess_image(
        self, 
        image: np.ndarray, 
        steps: List[PreprocessingStep]
    ) -> np.ndarray:
        """Apply preprocessing steps to improve OCR accuracy."""
        try:
            processed = image.copy()
            
            for step in steps:
                if step == PreprocessingStep.GRAYSCALE:
                    if len(processed.shape) == 3:
                        processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                
                elif step == PreprocessingStep.GAUSSIAN_BLUR:
                    processed = cv2.GaussianBlur(processed, (5, 5), 0)
                
                elif step == PreprocessingStep.THRESHOLD:
                    if len(processed.shape) == 3:
                        processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                    _, processed = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                elif step == PreprocessingStep.ADAPTIVE_THRESHOLD:
                    if len(processed.shape) == 3:
                        processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                    processed = cv2.adaptiveThreshold(
                        processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                    )
                
                elif step == PreprocessingStep.MORPHOLOGICAL:
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                    processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
                
                elif step == PreprocessingStep.DESKEW:
                    processed = self._deskew_image(processed)
                
                elif step == PreprocessingStep.NOISE_REMOVAL:
                    processed = cv2.medianBlur(processed, 3)
                
                elif step == PreprocessingStep.CONTRAST_ENHANCEMENT:
                    processed = self._enhance_contrast(processed)
                
                elif step == PreprocessingStep.SHARPENING:
                    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                    processed = cv2.filter2D(processed, -1, kernel)
                
                elif step == PreprocessingStep.EDGE_DETECTION:
                    # Use edge detection to enhance text boundaries
                    edges = cv2.Canny(processed, 50, 150)
                    processed = cv2.bitwise_or(processed, edges)
                
                elif step == PreprocessingStep.ROTATION_CORRECTION:
                    processed = self._correct_rotation(processed)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error in image preprocessing: {e}")
            return image

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Correct skew in scanned documents."""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find all white pixels
            coords = np.column_stack(np.where(binary > 0))
            
            # Calculate the minimum area rectangle
            angle = cv2.minAreaRect(coords)[-1]
            
            # Correct the angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Rotate the image
            if abs(angle) > 0.5:  # Only rotate if significant skew
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return rotated
            
            return image
            
        except Exception as e:
            self.logger.error(f"Error in deskewing: {e}")
            return image

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast for better OCR."""
        try:
            # Convert to PIL for easier enhancement
            if len(image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced = enhancer.enhance(1.5)  # Increase contrast by 50%
            
            # Enhance sharpness
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.2)
            
            # Convert back to OpenCV format
            if len(image.shape) == 3:
                return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)
            else:
                return np.array(enhanced)
                
        except Exception as e:
            self.logger.error(f"Error enhancing contrast: {e}")
            return image

    def _correct_rotation(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct text rotation."""
        try:
            # Use Tesseract's orientation detection
            osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
            rotation_angle = osd.get('rotate', 0)
            
            if rotation_angle != 0:
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, -rotation_angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return rotated
            
            return image
            
        except Exception as e:
            self.logger.error(f"Error in rotation correction: {e}")
            return image

    async def _ocr_image(
        self, 
        image: np.ndarray, 
        page_num: int,
        languages: List[str],
        psm: int,
        oem: int,
        ocr_mode: OCRMode
    ) -> Optional[OCRPage]:
        """Perform OCR on a single image."""
        try:
            # Prepare Tesseract configuration
            lang_string = '+'.join(languages)
            custom_config = f'--oem {oem} --psm {psm}'
            
            # Add specific configurations for different modes
            if ocr_mode == OCRMode.HANDWRITTEN:
                custom_config += ' -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()\'"- '
            elif ocr_mode == OCRMode.MATHEMATICAL:
                custom_config += ' -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=*/^()[]{}.,<>≤≥≠∞∑∏∫∂∇'
            
            # Get image dimensions
            height, width = image.shape[:2]
            dpi = 300  # Default DPI
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=lang_string, config=custom_config)
            
            # Get detailed data with bounding boxes and confidence scores
            data = pytesseract.image_to_data(image, lang=lang_string, config=custom_config, output_type=pytesseract.Output.DICT)
            
            # Process word-level data
            words = []
            lines = []
            regions = []
            
            current_line = None
            line_words = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # Only include recognized text
                    word_text = data['text'][i].strip()
                    if word_text:
                        word = OCRWord(
                            text=word_text,
                            confidence=float(data['conf'][i]),
                            bbox=(data['left'][i], data['top'][i], data['width'][i], data['height'][i]),
                            line_num=data['line_num'][i],
                            word_num=data['word_num'][i]
                        )
                        words.append(word)
                        
                        # Group words into lines
                        if current_line is None or current_line != data['line_num'][i]:
                            if current_line is not None and line_words:
                                # Create line from accumulated words
                                line_text = ' '.join([w.text for w in line_words])
                                line_confidence = sum([w.confidence for w in line_words]) / len(line_words)
                                
                                # Calculate line bounding box
                                min_x = min([w.bbox[0] for w in line_words])
                                min_y = min([w.bbox[1] for w in line_words])
                                max_x = max([w.bbox[0] + w.bbox[2] for w in line_words])
                                max_y = max([w.bbox[1] + w.bbox[3] for w in line_words])
                                
                                line = OCRLine(
                                    text=line_text,
                                    confidence=line_confidence,
                                    bbox=(min_x, min_y, max_x - min_x, max_y - min_y),
                                    words=line_words.copy(),
                                    line_num=current_line
                                )
                                lines.append(line)
                            
                            current_line = data['line_num'][i]
                            line_words = []
                        
                        line_words.append(word)
            
            # Add last line
            if line_words:
                line_text = ' '.join([w.text for w in line_words])
                line_confidence = sum([w.confidence for w in line_words]) / len(line_words)
                
                min_x = min([w.bbox[0] for w in line_words])
                min_y = min([w.bbox[1] for w in line_words])
                max_x = max([w.bbox[0] + w.bbox[2] for w in line_words])
                max_y = max([w.bbox[1] + w.bbox[3] for w in line_words])
                
                line = OCRLine(
                    text=line_text,
                    confidence=line_confidence,
                    bbox=(min_x, min_y, max_x - min_x, max_y - min_y),
                    words=line_words,
                    line_num=current_line
                )
                lines.append(line)
            
            # Create main text region
            if words:
                main_region = OCRRegion(
                    x=0,
                    y=0,
                    width=width,
                    height=height,
                    text=text,
                    confidence=sum([w.confidence for w in words]) / len(words),
                    word_count=len(words),
                    line_count=len(lines),
                    region_type="text",
                    language=lang_string
                )
                regions.append(main_region)
            
            # Calculate page confidence
            page_confidence = sum([w.confidence for w in words]) / len(words) if words else 0.0
            
            return OCRPage(
                page_num=page_num,
                text=text,
                confidence=page_confidence,
                width=width,
                height=height,
                dpi=dpi,
                regions=regions,
                lines=lines,
                words=words,
                preprocessing_applied=[],
                processing_time=0.0
            )
            
        except Exception as e:
            self.logger.error(f"Error in OCR processing for page {page_num}: {e}")
            return None

    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from numeric score."""
        if confidence >= 90:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 80:
            return ConfidenceLevel.HIGH
        elif confidence >= 60:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    async def _enhance_with_ai(self, ocr_result: OCRResult) -> Optional[Dict[str, Any]]:
        """Enhance OCR results using AI for error correction and improvement."""
        try:
            if not ocr_result.total_text.strip():
                return None
            
            # Skip enhancement for very short text
            if len(ocr_result.total_text.strip()) < 50:
                return None
            
            prompt = f"""
            Enhance and correct this OCR-extracted text from a legal document. 
            Fix obvious OCR errors, improve formatting, and correct spelling mistakes while preserving the original meaning.
            
            Original OCR confidence: {ocr_result.average_confidence:.1f}%
            Document type: Legal document
            
            OCR Text:
            {ocr_result.total_text[:3000]}  # Limit to first 3000 characters
            
            Please:
            1. Fix obvious OCR errors (like "rn" -> "m", "cl" -> "d", etc.)
            2. Correct spelling mistakes
            3. Improve punctuation and formatting
            4. Preserve legal terminology exactly
            5. Maintain paragraph structure
            
            Return the corrected text maintaining the original structure and meaning.
            Only return the corrected text, no explanations.
            """
            
            enhanced_text = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.1,
                max_tokens=4000
            )
            
            if enhanced_text and len(enhanced_text.strip()) > 10:
                # Count corrections by comparing original and enhanced text
                correction_count = self._count_corrections(ocr_result.total_text, enhanced_text)
                
                return {
                    "enhanced_text": enhanced_text.strip(),
                    "correction_count": correction_count
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error enhancing OCR with AI: {e}")
            return None

    def _count_corrections(self, original: str, enhanced: str) -> int:
        """Estimate the number of corrections made."""
        try:
            # Simple word-based comparison
            original_words = set(original.lower().split())
            enhanced_words = set(enhanced.lower().split())
            
            # Count differences
            differences = len(original_words.symmetric_difference(enhanced_words))
            
            # Estimate corrections (differences could be additions or corrections)
            return max(0, differences // 2)  # Rough estimate
            
        except Exception:
            return 0

    async def process_handwritten_notes(
        self, 
        file_info: FileInfo,
        languages: List[str] = None,
        enhance_preprocessing: bool = True
    ) -> OCRResult:
        """Specialized processing for handwritten notes."""
        try:
            # Use handwritten-specific configuration
            custom_config = {
                'psm': 6,  # Uniform block of text
                'oem': 1,  # LSTM engine (better for handwriting)
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.GAUSSIAN_BLUR,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.MORPHOLOGICAL,
                    PreprocessingStep.NOISE_REMOVAL,
                    PreprocessingStep.DESKEW
                ]
            }
            
            if enhance_preprocessing:
                custom_config['preprocessing'].extend([
                    PreprocessingStep.SHARPENING,
                    PreprocessingStep.ADAPTIVE_THRESHOLD
                ])
            
            return await self.process_document(
                file_info=file_info,
                ocr_mode=OCRMode.HANDWRITTEN,
                languages=languages or ['eng'],
                enhance_with_ai=True,
                custom_config=custom_config
            )
            
        except Exception as e:
            self.logger.error(f"Error processing handwritten notes: {e}")
            raise

    async def process_legal_document(
        self, 
        file_info: FileInfo,
        languages: List[str] = None,
        preserve_formatting: bool = True
    ) -> OCRResult:
        """Specialized processing for legal documents."""
        try:
            # Use legal document-specific configuration
            custom_config = {
                'psm': 3 if preserve_formatting else 6,
                'oem': 3,
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.DESKEW,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.NOISE_REMOVAL
                ]
            }
            
            return await self.process_document(
                file_info=file_info,
                ocr_mode=OCRMode.LEGAL_DOCUMENTS,
                languages=languages or ['eng'],
                enhance_with_ai=True,
                custom_config=custom_config
            )
            
        except Exception as e:
            self.logger.error(f"Error processing legal document: {e}")
            raise

    async def extract_table_data(
        self, 
        file_info: FileInfo,
        page_num: Optional[int] = None
    ) -> Dict[str, Any]:
        """Extract structured table data from documents."""
        try:
            # Convert to images
            images = await self._convert_to_images(file_info)
            if not images:
                raise ValueError("Could not convert file to images")
            
            # Process specific page or all pages
            target_images = [images[page_num - 1]] if page_num and page_num <= len(images) else images
            
            tables = []
            
            for i, image in enumerate(target_images):
                # Preprocess for table extraction
                processed = await self._preprocess_image(image, [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.THRESHOLD,
                    PreprocessingStep.MORPHOLOGICAL
                ])
                
                # Use table-specific OCR configuration
                config = '--psm 6 --oem 3'
                
                # Extract table structure
                table_data = pytesseract.image_to_data(
                    processed, 
                    config=config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Process table data (simplified table detection)
                if table_data:
                    tables.append({
                        "page": (page_num if page_num else i + 1),
                        "raw_data": table_data,
                        "extracted_text": pytesseract.image_to_string(processed, config=config)
                    })
            
            return {
                "tables_found": len(tables),
                "tables": tables
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting table data: {e}")
            return {"tables_found": 0, "tables": []}

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported OCR languages."""
        try:
            # Get installed languages from Tesseract
            installed_langs = pytesseract.get_languages(config='')
            
            # Language name mapping
            lang_names = {
                'eng': 'English',
                'spa': 'Spanish',
                'fra': 'French',
                'deu': 'German',
                'ita': 'Italian',
                'por': 'Portuguese',
                'rus': 'Russian',
                'chi_sim': 'Chinese Simplified',
                'chi_tra': 'Chinese Traditional',
                'jpn': 'Japanese',
                'kor': 'Korean',
                'ara': 'Arabic',
                'hin': 'Hindi',
                'tha': 'Thai',
                'vie': 'Vietnamese'
            }
            
            supported = []
            for lang_code in self.supported_languages:
                if lang_code in installed_langs:
                    supported.append({
                        'code': lang_code,
                        'name': lang_names.get(lang_code, lang_code.upper()),
                        'installed': True
                    })
                else:
                    supported.append({
                        'code': lang_code,
                        'name': lang_names.get(lang_code, lang_code.upper()),
                        'installed': False
                    })
            
            return supported
            
        except Exception as e:
            self.logger.error(f"Error getting supported languages: {e}")
            return [{'code': 'eng', 'name': 'English', 'installed': True}]

    async def batch_process_documents(
        self, 
        file_infos: List[FileInfo],
        ocr_mode: OCRMode = OCRMode.MIXED,
        languages: List[str] = None,
        max_concurrent: int = 3
    ) -> List[OCRResult]:
        """Process multiple documents concurrently."""
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(file_info):
                async with semaphore:
                    return await self.process_document(file_info, ocr_mode, languages)
            
            tasks = [process_with_semaphore(file_info) for file_info in file_infos]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful results
            successful_results = [
                result for result in results 
                if isinstance(result, OCRResult)
            ]
            
            return successful_results
            
        except Exception as e:
            self.logger.error(f"Error in batch OCR processing: {e}")
            return []

    def export_ocr_results(self, ocr_result: OCRResult, format: str = "json") -> str:
        """Export OCR results in specified format."""
        try:
            if format.lower() == "json":
                # Convert to JSON-serializable format
                export_data = {
                    "file_id": ocr_result.file_id,
                    "original_filename": ocr_result.original_filename,
                    "total_pages": ocr_result.total_pages,
                    "total_text": ocr_result.total_text,
                    "enhanced_text": ocr_result.enhanced_text,
                    "average_confidence": ocr_result.average_confidence,
                    "confidence_level": ocr_result.confidence_level.value,
                    "languages_detected": ocr_result.languages_detected,
                    "ocr_mode": ocr_result.ocr_mode.value,
                    "processing_time": ocr_result.processing_time,
                    "timestamp": ocr_result.timestamp.isoformat(),
                    "quality_metrics": {
                        "word_count": ocr_result.word_count,
                        "character_count": ocr_result.character_count,
                        "low_confidence_words": ocr_result.low_confidence_words,
                        "blank_pages": ocr_result.blank_pages
                    },
                    "enhancement": {
                        "ai_enhanced": ocr_result.ai_enhanced,
                        "correction_count": ocr_result.correction_count
                    },
                    "technical_details": {
                        "tesseract_version": ocr_result.tesseract_version,
                        "preprocessing_steps": [step.value for step in ocr_result.preprocessing_steps]
                    },
                    "pages": [
                        {
                            "page_num": page.page_num,
                            "text": page.text,
                            "confidence": page.confidence,
                            "dimensions": f"{page.width}x{page.height}",
                            "word_count": len(page.words),
                            "line_count": len(page.lines),
                            "processing_time": page.processing_time
                        }
                        for page in ocr_result.pages
                    ]
                }
                
                return json.dumps(export_data, indent=2, default=str)
            
            elif format.lower() == "text":
                text_output = f"OCR Results for: {ocr_result.original_filename}\n"
                text_output += f"Confidence: {ocr_result.average_confidence:.1f}%\n"
                text_output += f"Pages: {ocr_result.total_pages}\n"
                text_output += f"Words: {ocr_result.word_count}\n\n"
                
                if ocr_result.enhanced_text:
                    text_output += "Enhanced Text:\n"
                    text_output += "=" * 50 + "\n"
                    text_output += ocr_result.enhanced_text
                else:
                    text_output += "Extracted Text:\n"
                    text_output += "=" * 50 + "\n"
                    text_output += ocr_result.total_text
                
                return text_output
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting OCR results: {e}")
            return ""