"""
Specialized processor for handwritten notes with advanced preprocessing and AI enhancement.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import asyncio
import json
from datetime import datetime

from ..shared.utils.ai_client import AIClient
from .ocr_engine import TesseractOCREngine, OCRResult, OCRMode, PreprocessingStep
from .upload_manager import FileInfo


class HandwritingType(Enum):
    """Types of handwriting styles."""
    CURSIVE = "cursive"
    PRINT = "print"
    MIXED = "mixed"
    MEDICAL = "medical"
    LEGAL_NOTES = "legal_notes"
    SIGNATURES = "signatures"
    ANNOTATIONS = "annotations"


class HandwritingQuality(Enum):
    """Quality levels of handwriting."""
    EXCELLENT = "excellent"      # Very clear, easy to read
    GOOD = "good"               # Mostly clear with minor issues
    FAIR = "fair"               # Readable but challenging
    POOR = "poor"               # Difficult to read
    ILLEGIBLE = "illegible"     # Nearly impossible to read


class WritingInstrument(Enum):
    """Types of writing instruments detected."""
    BALLPOINT_PEN = "ballpoint_pen"
    FOUNTAIN_PEN = "fountain_pen"
    PENCIL = "pencil"
    MARKER = "marker"
    FELT_TIP = "felt_tip"
    CRAYON = "crayon"
    DIGITAL_STYLUS = "digital_stylus"
    UNKNOWN = "unknown"


@dataclass
class HandwritingAnalysis:
    """Analysis results for handwritten content."""
    handwriting_type: HandwritingType
    quality: HandwritingQuality
    writing_instrument: WritingInstrument
    line_spacing: float
    character_size: float
    slant_angle: float
    pressure_variation: float
    consistency_score: float
    readability_score: float
    confidence: float
    challenges: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class HandwritingRegion:
    """Region of handwritten text within a document."""
    x: int
    y: int
    width: int
    height: int
    text: str
    confidence: float
    analysis: HandwritingAnalysis
    original_image: Optional[np.ndarray] = None
    processed_image: Optional[np.ndarray] = None


class HandwritingProcessor:
    """Advanced processor for handwritten notes and documents."""
    
    def __init__(self):
        self.ocr_engine = TesseractOCREngine()
        self.ai_client = AIClient()
        
        # Handwriting-specific configurations
        self.handwriting_configs = {
            HandwritingType.CURSIVE: {
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.GAUSSIAN_BLUR,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.MORPHOLOGICAL,
                    PreprocessingStep.NOISE_REMOVAL
                ],
                'tesseract_config': '--psm 6 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()\'"- '
            },
            HandwritingType.PRINT: {
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.NOISE_REMOVAL
                ],
                'tesseract_config': '--psm 6 --oem 1'
            },
            HandwritingType.MIXED: {
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.GAUSSIAN_BLUR,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.MORPHOLOGICAL,
                    PreprocessingStep.NOISE_REMOVAL
                ],
                'tesseract_config': '--psm 6 --oem 1'
            },
            HandwritingType.MEDICAL: {
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.GAUSSIAN_BLUR,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.SHARPENING,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.MORPHOLOGICAL
                ],
                'tesseract_config': '--psm 6 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()\'"- /mg'
            },
            HandwritingType.LEGAL_NOTES: {
                'preprocessing': [
                    PreprocessingStep.GRAYSCALE,
                    PreprocessingStep.DESKEW,
                    PreprocessingStep.CONTRAST_ENHANCEMENT,
                    PreprocessingStep.ADAPTIVE_THRESHOLD,
                    PreprocessingStep.NOISE_REMOVAL
                ],
                'tesseract_config': '--psm 6 --oem 1'
            }
        }

    async def process_handwritten_document(
        self, 
        file_info: FileInfo,
        handwriting_type: Optional[HandwritingType] = None,
        enhance_quality: bool = True,
        languages: List[str] = None
    ) -> OCRResult:
        """Process handwritten document with specialized handling."""
        try:
            print(f"Processing handwritten document: {file_info.original_filename}")
            
            # Convert to images
            images = await self.ocr_engine._convert_to_images(file_info)
            if not images:
                raise ValueError("Could not convert file to images")
            
            # Analyze handwriting if type not specified
            if not handwriting_type:
                handwriting_type = await self._detect_handwriting_type(images[0])
            
            # Get configuration for handwriting type
            config = self.handwriting_configs.get(handwriting_type, self.handwriting_configs[HandwritingType.MIXED])
            
            # Process with enhanced preprocessing
            if enhance_quality:
                enhanced_images = []
                for image in images:
                    enhanced = await self._enhance_handwriting_image(image, handwriting_type)
                    enhanced_images.append(enhanced)
                images = enhanced_images
            
            # Use handwriting-specific OCR mode
            ocr_result = await self.ocr_engine.process_document(
                file_info=file_info,
                ocr_mode=OCRMode.HANDWRITTEN,
                languages=languages or ['eng'],
                enhance_with_ai=True,
                custom_config={
                    'preprocessing': config['preprocessing'],
                    'psm': 6,  # Uniform block of text
                    'oem': 1   # LSTM engine
                }
            )
            
            # Add handwriting-specific metadata
            ocr_result.metadata.update({
                'handwriting_type': handwriting_type.value,
                'enhanced_for_handwriting': enhance_quality,
                'specialized_processing': True
            })
            
            # Perform handwriting analysis for each page
            for i, page in enumerate(ocr_result.pages):
                if i < len(images):
                    analysis = await self._analyze_handwriting_quality(images[i])
                    page.metadata['handwriting_analysis'] = analysis
            
            print(f"Handwritten document processed: {file_info.original_filename}")
            return ocr_result
            
        except Exception as e:
            print(f"Error processing handwritten document: {e}")
            raise

    async def _detect_handwriting_type(self, image: np.ndarray) -> HandwritingType:
        """Detect the type of handwriting in the image."""
        try:
            # Preprocess for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours (letters/words)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return HandwritingType.MIXED
            
            # Analyze characteristics
            aspect_ratios = []
            areas = []
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                if area > 50:  # Filter out noise
                    aspect_ratios.append(w / h if h > 0 else 1)
                    areas.append(area)
            
            if not aspect_ratios:
                return HandwritingType.MIXED
            
            avg_aspect_ratio = np.mean(aspect_ratios)
            std_aspect_ratio = np.std(aspect_ratios)
            
            # Heuristic classification
            if avg_aspect_ratio > 3.0 and std_aspect_ratio > 1.0:
                return HandwritingType.CURSIVE
            elif avg_aspect_ratio < 1.5 and std_aspect_ratio < 0.5:
                return HandwritingType.PRINT
            else:
                return HandwritingType.MIXED
                
        except Exception as e:
            print(f"Error detecting handwriting type: {e}")
            return HandwritingType.MIXED

    async def _enhance_handwriting_image(
        self, 
        image: np.ndarray, 
        handwriting_type: HandwritingType
    ) -> np.ndarray:
        """Apply specialized enhancement for handwritten text."""
        try:
            # Convert to PIL for advanced processing
            if len(image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image)
            
            # Apply handwriting-specific enhancements
            if handwriting_type == HandwritingType.CURSIVE:
                # Enhance cursive writing
                enhanced = self._enhance_cursive_writing(pil_image)
            elif handwriting_type == HandwritingType.PRINT:
                # Enhance print handwriting
                enhanced = self._enhance_print_writing(pil_image)
            elif handwriting_type == HandwritingType.MEDICAL:
                # Enhance medical notes (often challenging)
                enhanced = self._enhance_medical_writing(pil_image)
            elif handwriting_type == HandwritingType.LEGAL_NOTES:
                # Enhance legal annotations
                enhanced = self._enhance_legal_notes(pil_image)
            else:
                # General enhancement
                enhanced = self._enhance_general_handwriting(pil_image)
            
            # Convert back to OpenCV format
            if len(image.shape) == 3:
                return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)
            else:
                return np.array(enhanced)
                
        except Exception as e:
            print(f"Error enhancing handwriting image: {e}")
            return image

    def _enhance_cursive_writing(self, image: Image.Image) -> Image.Image:
        """Enhance cursive handwriting for better OCR."""
        try:
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast more aggressively for cursive
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(2.0)
            
            # Apply slight blur to connect broken strokes
            enhanced = enhanced.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Enhance sharpness
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.5)
            
            # Apply unsharp mask for edge enhancement
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing cursive writing: {e}")
            return image

    def _enhance_print_writing(self, image: Image.Image) -> Image.Image:
        """Enhance print handwriting for better OCR."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Moderate contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.5)
            
            # Sharpen for print text
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.3)
            
            # Apply edge enhancement
            enhanced = enhanced.filter(ImageFilter.EDGE_ENHANCE)
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing print writing: {e}")
            return image

    def _enhance_medical_writing(self, image: Image.Image) -> Image.Image:
        """Enhance medical handwriting (often challenging)."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Aggressive contrast enhancement for medical notes
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(2.5)
            
            # Apply brightness adjustment
            brightness_enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = brightness_enhancer.enhance(1.2)
            
            # Heavy sharpening
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(2.0)
            
            # Apply multiple filters
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=2, percent=200, threshold=2))
            enhanced = enhanced.filter(ImageFilter.EDGE_ENHANCE_MORE)
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing medical writing: {e}")
            return image

    def _enhance_legal_notes(self, image: Image.Image) -> Image.Image:
        """Enhance legal handwritten notes and annotations."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Balanced enhancement for legal notes
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.8)
            
            # Moderate sharpening
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.4)
            
            # Apply edge enhancement
            enhanced = enhanced.filter(ImageFilter.EDGE_ENHANCE)
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3))
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing legal notes: {e}")
            return image

    def _enhance_general_handwriting(self, image: Image.Image) -> Image.Image:
        """General handwriting enhancement."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Standard enhancements
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.6)
            
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.3)
            
            # Apply noise reduction and edge enhancement
            enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing general handwriting: {e}")
            return image

    async def _analyze_handwriting_quality(self, image: np.ndarray) -> HandwritingAnalysis:
        """Analyze the quality and characteristics of handwriting."""
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return HandwritingAnalysis(
                    handwriting_type=HandwritingType.MIXED,
                    quality=HandwritingQuality.POOR,
                    writing_instrument=WritingInstrument.UNKNOWN,
                    line_spacing=0,
                    character_size=0,
                    slant_angle=0,
                    pressure_variation=0,
                    consistency_score=0,
                    readability_score=0,
                    confidence=0,
                    challenges=["No text detected"],
                    recommendations=["Check image quality"]
                )
            
            # Analyze characteristics
            character_sizes = []
            aspect_ratios = []
            areas = []
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                if area > 20:  # Filter small noise
                    character_sizes.append(h)  # Use height as character size
                    aspect_ratios.append(w / h if h > 0 else 1)
                    areas.append(area)
            
            # Calculate metrics
            avg_char_size = np.mean(character_sizes) if character_sizes else 0
            char_size_std = np.std(character_sizes) if character_sizes else 0
            avg_aspect_ratio = np.mean(aspect_ratios) if aspect_ratios else 1
            
            # Estimate line spacing (simplified)
            line_spacing = self._estimate_line_spacing(binary)
            
            # Estimate slant angle (simplified)
            slant_angle = self._estimate_slant_angle(binary)
            
            # Calculate consistency score
            consistency_score = max(0, 1 - (char_size_std / avg_char_size)) if avg_char_size > 0 else 0
            
            # Determine quality
            quality = self._determine_writing_quality(consistency_score, len(contours), avg_char_size)
            
            # Detect writing instrument (simplified heuristic)
            instrument = self._detect_writing_instrument(binary, areas)
            
            # Determine handwriting type
            handwriting_type = await self._classify_handwriting_type(avg_aspect_ratio, char_size_std, slant_angle)
            
            # Calculate readability score
            readability_score = self._calculate_readability_score(quality, consistency_score, avg_char_size)
            
            # Generate challenges and recommendations
            challenges, recommendations = self._generate_analysis_feedback(
                quality, consistency_score, avg_char_size, line_spacing
            )
            
            return HandwritingAnalysis(
                handwriting_type=handwriting_type,
                quality=quality,
                writing_instrument=instrument,
                line_spacing=line_spacing,
                character_size=avg_char_size,
                slant_angle=slant_angle,
                pressure_variation=char_size_std / avg_char_size if avg_char_size > 0 else 0,
                consistency_score=consistency_score,
                readability_score=readability_score,
                confidence=min(consistency_score + 0.3, 1.0),
                challenges=challenges,
                recommendations=recommendations
            )
            
        except Exception as e:
            print(f"Error analyzing handwriting quality: {e}")
            return HandwritingAnalysis(
                handwriting_type=HandwritingType.MIXED,
                quality=HandwritingQuality.FAIR,
                writing_instrument=WritingInstrument.UNKNOWN,
                line_spacing=0,
                character_size=0,
                slant_angle=0,
                pressure_variation=0,
                consistency_score=0.5,
                readability_score=0.5,
                confidence=0.5
            )

    def _estimate_line_spacing(self, binary_image: np.ndarray) -> float:
        """Estimate line spacing in handwritten text."""
        try:
            # Project pixels horizontally to find line gaps
            horizontal_projection = np.sum(binary_image, axis=1)
            
            # Find gaps between lines
            gaps = []
            in_gap = False
            gap_start = 0
            
            for i, count in enumerate(horizontal_projection):
                if count == 0 and not in_gap:
                    in_gap = True
                    gap_start = i
                elif count > 0 and in_gap:
                    in_gap = False
                    gap_size = i - gap_start
                    if gap_size > 5:  # Minimum gap size
                        gaps.append(gap_size)
            
            return np.mean(gaps) if gaps else 0
            
        except Exception as e:
            print(f"Error estimating line spacing: {e}")
            return 0

    def _estimate_slant_angle(self, binary_image: np.ndarray) -> float:
        """Estimate the slant angle of handwritten text."""
        try:
            # Find contours
            contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            angles = []
            
            for contour in contours:
                if cv2.contourArea(contour) > 100:  # Filter small contours
                    # Fit ellipse to get orientation
                    if len(contour) >= 5:
                        ellipse = cv2.fitEllipse(contour)
                        angle = ellipse[2]  # Angle in degrees
                        
                        # Normalize angle to reasonable range
                        if angle > 90:
                            angle = 180 - angle
                        
                        angles.append(angle)
            
            return np.mean(angles) if angles else 0
            
        except Exception as e:
            print(f"Error estimating slant angle: {e}")
            return 0

    def _determine_writing_quality(
        self, 
        consistency_score: float, 
        contour_count: int, 
        avg_char_size: float
    ) -> HandwritingQuality:
        """Determine overall writing quality."""
        try:
            # Combine multiple factors
            quality_score = 0
            
            # Consistency factor
            if consistency_score > 0.8:
                quality_score += 2
            elif consistency_score > 0.6:
                quality_score += 1
            
            # Character count factor (more characters usually means more readable)
            if contour_count > 100:
                quality_score += 2
            elif contour_count > 50:
                quality_score += 1
            
            # Character size factor (moderate size is best)
            if 15 <= avg_char_size <= 40:
                quality_score += 2
            elif 10 <= avg_char_size <= 50:
                quality_score += 1
            
            # Map score to quality level
            if quality_score >= 5:
                return HandwritingQuality.EXCELLENT
            elif quality_score >= 4:
                return HandwritingQuality.GOOD
            elif quality_score >= 2:
                return HandwritingQuality.FAIR
            elif quality_score >= 1:
                return HandwritingQuality.POOR
            else:
                return HandwritingQuality.ILLEGIBLE
                
        except Exception as e:
            print(f"Error determining writing quality: {e}")
            return HandwritingQuality.FAIR

    def _detect_writing_instrument(self, binary_image: np.ndarray, areas: List[float]) -> WritingInstrument:
        """Detect the writing instrument based on stroke characteristics."""
        try:
            if not areas:
                return WritingInstrument.UNKNOWN
            
            avg_area = np.mean(areas)
            area_std = np.std(areas)
            
            # Simple heuristics based on stroke characteristics
            if avg_area > 500 and area_std > 200:
                return WritingInstrument.MARKER
            elif avg_area > 200 and area_std < 100:
                return WritingInstrument.BALLPOINT_PEN
            elif avg_area > 300 and area_std > 150:
                return WritingInstrument.FOUNTAIN_PEN
            elif avg_area < 150:
                return WritingInstrument.PENCIL
            else:
                return WritingInstrument.BALLPOINT_PEN  # Most common default
                
        except Exception as e:
            print(f"Error detecting writing instrument: {e}")
            return WritingInstrument.UNKNOWN

    async def _classify_handwriting_type(
        self, 
        avg_aspect_ratio: float, 
        char_size_std: float, 
        slant_angle: float
    ) -> HandwritingType:
        """Classify handwriting type based on characteristics."""
        try:
            # Use characteristics to classify
            if avg_aspect_ratio > 2.5 and abs(slant_angle) > 10:
                return HandwritingType.CURSIVE
            elif avg_aspect_ratio < 1.5 and char_size_std < 5:
                return HandwritingType.PRINT
            elif abs(slant_angle) > 15:
                return HandwritingType.CURSIVE
            else:
                return HandwritingType.MIXED
                
        except Exception as e:
            print(f"Error classifying handwriting type: {e}")
            return HandwritingType.MIXED

    def _calculate_readability_score(
        self, 
        quality: HandwritingQuality, 
        consistency: float, 
        char_size: float
    ) -> float:
        """Calculate overall readability score."""
        try:
            base_score = {
                HandwritingQuality.EXCELLENT: 0.95,
                HandwritingQuality.GOOD: 0.8,
                HandwritingQuality.FAIR: 0.6,
                HandwritingQuality.POOR: 0.4,
                HandwritingQuality.ILLEGIBLE: 0.2
            }.get(quality, 0.5)
            
            # Adjust based on consistency
            consistency_bonus = consistency * 0.2
            
            # Adjust based on character size (optimal range bonus)
            size_bonus = 0
            if 15 <= char_size <= 35:
                size_bonus = 0.1
            elif 10 <= char_size <= 45:
                size_bonus = 0.05
            
            return min(1.0, base_score + consistency_bonus + size_bonus)
            
        except Exception as e:
            print(f"Error calculating readability score: {e}")
            return 0.5

    def _generate_analysis_feedback(
        self, 
        quality: HandwritingQuality,
        consistency: float,
        char_size: float,
        line_spacing: float
    ) -> Tuple[List[str], List[str]]:
        """Generate challenges and recommendations based on analysis."""
        challenges = []
        recommendations = []
        
        # Quality-based feedback
        if quality == HandwritingQuality.ILLEGIBLE:
            challenges.extend(["Text is largely illegible", "Very low OCR confidence expected"])
            recommendations.extend(["Consider manual transcription", "Use higher resolution scanning"])
        elif quality == HandwritingQuality.POOR:
            challenges.extend(["Text is difficult to read", "Low OCR accuracy expected"])
            recommendations.extend(["Apply additional preprocessing", "Consider AI enhancement"])
        
        # Consistency feedback
        if consistency < 0.3:
            challenges.append("Inconsistent character sizing")
            recommendations.append("Use morphological operations to normalize character sizes")
        
        # Character size feedback
        if char_size < 10:
            challenges.append("Very small text size")
            recommendations.append("Increase image resolution or apply magnification")
        elif char_size > 50:
            challenges.append("Very large text size")
            recommendations.append("Consider text segmentation for better processing")
        
        # Line spacing feedback
        if line_spacing < 5:
            challenges.append("Lines are too close together")
            recommendations.append("Use line separation algorithms")
        
        return challenges, recommendations

    async def extract_handwriting_regions(
        self, 
        file_info: FileInfo,
        min_region_size: int = 500
    ) -> List[HandwritingRegion]:
        """Extract individual handwriting regions from a document."""
        try:
            # Convert to images
            images = await self.ocr_engine._convert_to_images(file_info)
            if not images:
                return []
            
            regions = []
            
            for i, image in enumerate(images):
                # Convert to grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
                
                # Apply threshold
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Find contours
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Group nearby contours into regions
                region_contours = self._group_contours_into_regions(contours, min_region_size)
                
                for j, region_contour in enumerate(region_contours):
                    x, y, w, h = cv2.boundingRect(region_contour)
                    
                    if w * h >= min_region_size:
                        # Extract region image
                        region_image = image[y:y+h, x:x+w]
                        
                        # Perform OCR on region
                        region_text = await self._ocr_region(region_image)
                        
                        # Analyze region
                        analysis = await self._analyze_handwriting_quality(region_image)
                        
                        region = HandwritingRegion(
                            x=x, y=y, width=w, height=h,
                            text=region_text['text'],
                            confidence=region_text['confidence'],
                            analysis=analysis,
                            original_image=region_image.copy(),
                            processed_image=None
                        )
                        
                        regions.append(region)
            
            return regions
            
        except Exception as e:
            print(f"Error extracting handwriting regions: {e}")
            return []

    def _group_contours_into_regions(self, contours: List, min_size: int) -> List:
        """Group nearby contours into larger regions."""
        try:
            if not contours:
                return []
            
            # Calculate bounding rectangles
            bounding_rects = [cv2.boundingRect(c) for c in contours]
            
            # Group nearby rectangles
            grouped = []
            used = set()
            
            for i, rect1 in enumerate(bounding_rects):
                if i in used:
                    continue
                
                group = [i]
                x1, y1, w1, h1 = rect1
                
                for j, rect2 in enumerate(bounding_rects):
                    if i == j or j in used:
                        continue
                    
                    x2, y2, w2, h2 = rect2
                    
                    # Check if rectangles are close enough to group
                    horizontal_gap = min(abs(x1 + w1 - x2), abs(x2 + w2 - x1))
                    vertical_gap = min(abs(y1 + h1 - y2), abs(y2 + h2 - y1))
                    
                    if horizontal_gap < 20 or vertical_gap < 10:  # Adjust thresholds as needed
                        group.append(j)
                        used.add(j)
                
                used.update(group)
                
                # Combine contours in group
                group_contours = [contours[idx] for idx in group]
                combined_contour = np.vstack(group_contours)
                
                grouped.append(combined_contour)
            
            return grouped
            
        except Exception as e:
            print(f"Error grouping contours: {e}")
            return contours

    async def _ocr_region(self, region_image: np.ndarray) -> Dict[str, Any]:
        """Perform OCR on a handwriting region."""
        try:
            import pytesseract
            
            # Use handwriting-specific configuration
            config = '--psm 6 --oem 1'
            
            text = pytesseract.image_to_string(region_image, config=config, lang='eng')
            data = pytesseract.image_to_data(region_image, config=config, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text.strip(),
                'confidence': avg_confidence,
                'word_count': len([word for word in text.split() if word.strip()])
            }
            
        except Exception as e:
            print(f"Error in region OCR: {e}")
            return {'text': '', 'confidence': 0, 'word_count': 0}

    async def enhance_handwriting_with_ai(self, ocr_result: OCRResult) -> Optional[str]:
        """Use AI to enhance and correct handwriting OCR results."""
        try:
            if not ocr_result.total_text.strip() or len(ocr_result.total_text.strip()) < 20:
                return None
            
            prompt = f"""
            This is OCR text extracted from handwritten notes. Please enhance and correct it:

            Original handwritten text (OCR confidence: {ocr_result.average_confidence:.1f}%):
            {ocr_result.total_text[:2000]}

            Please:
            1. Correct obvious OCR errors common in handwritten text
            2. Fix spelling mistakes while preserving intended meaning
            3. Improve punctuation and sentence structure
            4. Handle common handwriting OCR issues (like 'rn' -> 'm', 'cl' -> 'd')
            5. Maintain the original tone and style
            6. Keep abbreviations and informal language if appropriate
            7. Preserve any technical or domain-specific terms

            Return only the corrected text, maintaining the original paragraph structure.
            """
            
            enhanced_text = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.1,
                max_tokens=2500
            )
            
            return enhanced_text.strip() if enhanced_text else None
            
        except Exception as e:
            print(f"Error enhancing handwriting with AI: {e}")
            return None

    def export_handwriting_analysis(
        self, 
        ocr_result: OCRResult, 
        regions: List[HandwritingRegion] = None,
        format: str = "json"
    ) -> str:
        """Export handwriting analysis results."""
        try:
            if format.lower() == "json":
                export_data = {
                    "document_info": {
                        "file_id": ocr_result.file_id,
                        "filename": ocr_result.original_filename,
                        "pages": ocr_result.total_pages,
                        "processing_time": ocr_result.processing_time
                    },
                    "ocr_results": {
                        "total_text": ocr_result.total_text,
                        "enhanced_text": ocr_result.enhanced_text,
                        "confidence": ocr_result.average_confidence,
                        "confidence_level": ocr_result.confidence_level.value,
                        "word_count": ocr_result.word_count,
                        "low_confidence_words": ocr_result.low_confidence_words
                    },
                    "handwriting_analysis": {
                        "specialized_processing": ocr_result.metadata.get('specialized_processing', False),
                        "handwriting_type": ocr_result.metadata.get('handwriting_type', 'mixed'),
                        "enhanced_for_handwriting": ocr_result.metadata.get('enhanced_for_handwriting', False)
                    }
                }
                
                # Add page-specific analysis
                if ocr_result.pages:
                    export_data["page_analysis"] = []
                    for page in ocr_result.pages:
                        page_analysis = page.metadata.get('handwriting_analysis')
                        if page_analysis:
                            export_data["page_analysis"].append({
                                "page_num": page.page_num,
                                "handwriting_type": page_analysis.handwriting_type.value,
                                "quality": page_analysis.quality.value,
                                "readability_score": page_analysis.readability_score,
                                "consistency_score": page_analysis.consistency_score,
                                "challenges": page_analysis.challenges,
                                "recommendations": page_analysis.recommendations
                            })
                
                # Add region analysis if available
                if regions:
                    export_data["regions"] = []
                    for region in regions:
                        export_data["regions"].append({
                            "bounds": f"{region.x},{region.y},{region.width},{region.height}",
                            "text": region.text,
                            "confidence": region.confidence,
                            "handwriting_type": region.analysis.handwriting_type.value,
                            "quality": region.analysis.quality.value,
                            "readability_score": region.analysis.readability_score
                        })
                
                return json.dumps(export_data, indent=2, default=str)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            print(f"Error exporting handwriting analysis: {e}")
            return ""