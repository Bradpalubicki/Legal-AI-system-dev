"""
Real-time transcript processing and enhancement.

Processes raw transcription output to improve accuracy, add punctuation,
correct legal terminology, and prepare for legal analysis.
"""

import asyncio
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ..shared.utils import BaseAPIClient
from .models import SpeakerType, generate_message_id
from .speech_analyzer import TranscriptionResult, SpeechSegment


@dataclass
class ProcessingConfig:
    """Configuration for transcript processing."""
    # Language processing
    language: str = "en-US"
    enable_punctuation: bool = True
    enable_capitalization: bool = True
    enable_spell_check: bool = True
    
    # Legal processing
    enable_legal_terminology: bool = True
    enable_citation_detection: bool = True
    enable_objection_detection: bool = True
    
    # Quality control
    min_confidence_threshold: float = 0.6
    enable_confidence_filtering: bool = True
    enable_duplicate_removal: bool = True
    
    # Context processing
    context_window_size: int = 10  # sentences
    enable_speaker_context: bool = True
    enable_topic_tracking: bool = True
    
    # Real-time processing
    processing_delay_ms: int = 500
    batch_size: int = 5
    enable_streaming: bool = True


@dataclass
class TextCorrection:
    """Text correction information."""
    original_text: str
    corrected_text: str
    correction_type: str
    confidence: float
    position: int
    suggestions: List[str] = field(default_factory=list)


@dataclass
class TranscriptSegment:
    """Processed transcript segment."""
    segment_id: str
    text: str
    speaker_id: Optional[str]
    speaker_type: Optional[SpeakerType]
    
    # Timing
    start_time: float
    end_time: float
    duration: float
    
    # Quality metrics
    confidence: float
    quality_score: float
    
    # Processing metadata
    original_text: str
    corrections: List[TextCorrection] = field(default_factory=list)
    detected_entities: List[Dict[str, Any]] = field(default_factory=list)
    legal_terms: List[str] = field(default_factory=list)
    
    # Context
    topic: Optional[str] = None
    sentiment: Optional[str] = None
    
    # Events detected in this segment
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    processed_at: datetime = field(default_factory=datetime.utcnow)
    processing_time: float = 0.0
    
    @property
    def word_count(self) -> int:
        """Get word count."""
        return len(self.text.split())
    
    @property
    def has_corrections(self) -> bool:
        """Check if segment has any corrections."""
        return len(self.corrections) > 0
    
    @property
    def correction_ratio(self) -> float:
        """Get ratio of corrections to total words."""
        if self.word_count == 0:
            return 0.0
        return len(self.corrections) / self.word_count


@dataclass
class ProcessingContext:
    """Context for transcript processing."""
    session_id: str
    speaker_history: Dict[str, List[str]] = field(default_factory=dict)
    topic_history: List[str] = field(default_factory=list)
    recent_segments: deque = field(default_factory=lambda: deque(maxlen=10))
    legal_context: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    total_segments: int = 0
    average_confidence: float = 0.0
    correction_stats: Dict[str, int] = field(default_factory=dict)


class TranscriptProcessor:
    """Advanced transcript processing and enhancement system."""
    
    def __init__(self, 
                 config: ProcessingConfig,
                 api_client: Optional[BaseAPIClient] = None):
        self.config = config
        self.api_client = api_client
        
        # Processing contexts per session
        self.session_contexts: Dict[str, ProcessingContext] = {}
        
        # Legal terminology and patterns
        self.legal_dictionary = self._load_legal_dictionary()
        self.legal_patterns = self._compile_legal_patterns()
        self.objection_patterns = self._compile_objection_patterns()
        
        # Correction models
        self.spell_checker = self._initialize_spell_checker()
        self.punctuation_model = self._initialize_punctuation_model()
        
        # Processing queue
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.is_processing = False
        
        # Statistics
        self.total_processed = 0
        self.total_corrections = 0
        self.processing_time_total = 0.0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _load_legal_dictionary(self) -> Dict[str, str]:
        """Load legal terminology dictionary."""
        return {
            # Common legal terms with preferred spellings
            "attorney": "attorney",
            "attourney": "attorney",
            "lawyer": "attorney",
            "council": "counsel",
            "counsel": "counsel",
            "plaintiff": "plaintiff",
            "plaintif": "plaintiff",
            "defendant": "defendant",
            "defendand": "defendant",
            "objection": "objection",
            "objetion": "objection",
            "overruled": "overruled",
            "overulled": "overruled",
            "sustained": "sustained",
            "sustaned": "sustained",
            "hearsay": "hearsay",
            "hersay": "hearsay",
            "relevance": "relevance",
            "relevence": "relevance",
            "foundation": "foundation",
            "foundaton": "foundation",
            "sidebar": "sidebar",
            "sidbar": "sidebar",
            "approach": "approach",
            "aproach": "approach",
            "stipulate": "stipulate",
            "stipulat": "stipulate",
            "voir dire": "voir dire",
            "voir dir": "voir dire",
            "subpoena": "subpoena",
            "supoena": "subpoena",
            "deposition": "deposition",
            "depostion": "deposition",
            "interrogatories": "interrogatories",
            "interogatories": "interrogatories",
            "your honor": "Your Honor",
            "yourhonor": "Your Honor",
            "your honour": "Your Honor",
        }
    
    def _compile_legal_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regular expressions for legal pattern detection."""
        return {
            "case_citations": re.compile(
                r'\b\d+\s+[A-Z][a-z]*\.?\s*(?:\d+d\s+)?\d+(?:,\s+\d+)?\s*\(\d{4}\)',
                re.IGNORECASE
            ),
            "court_references": re.compile(
                r'\b(?:this\s+)?(?:court|judge|bench|tribunal)\b',
                re.IGNORECASE
            ),
            "legal_motions": re.compile(
                r'\b(?:motion\s+(?:for|to)\s+(?:dismiss|compel|strike|summary\s+judgment))\b',
                re.IGNORECASE
            ),
            "evidence_references": re.compile(
                r'\b(?:exhibit\s+[a-z0-9]+|evidence|document|record)\b',
                re.IGNORECASE
            ),
            "procedural_terms": re.compile(
                r'\b(?:sustained|overruled|objection|sidebar|approach|recess)\b',
                re.IGNORECASE
            ),
            "speaker_addresses": re.compile(
                r'\b(?:your\s+honor|counselor?|mr\.?\s+\w+|ms\.?\s+\w+|dr\.?\s+\w+)\b',
                re.IGNORECASE
            )
        }
    
    def _compile_objection_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for objection detection."""
        return {
            "objection": re.compile(r'\bobjection\b', re.IGNORECASE),
            "hearsay": re.compile(r'\bhearsay\b', re.IGNORECASE),
            "relevance": re.compile(r'\brelevance\b|\birrelevant\b', re.IGNORECASE),
            "foundation": re.compile(r'\bfoundation\b|\blacks?\s+foundation\b', re.IGNORECASE),
            "leading": re.compile(r'\bleading\b|\bleading\s+question\b', re.IGNORECASE),
            "compound": re.compile(r'\bcompound\b|\bcompound\s+question\b', re.IGNORECASE),
            "argumentative": re.compile(r'\bargumentative\b', re.IGNORECASE),
            "assumes_facts": re.compile(r'\bassumes?\s+facts?\b', re.IGNORECASE),
            "speculation": re.compile(r'\bspeculat\w+\b|\bcalls?\s+for\s+speculation\b', re.IGNORECASE),
            "narrative": re.compile(r'\bnarrative\b', re.IGNORECASE),
            "non_responsive": re.compile(r'\bnon.?responsive\b', re.IGNORECASE),
            "vague": re.compile(r'\bvague\b|\bambiguous\b', re.IGNORECASE)
        }
    
    def _initialize_spell_checker(self):
        """Initialize spell checking system."""
        # In production, would use libraries like pyspellchecker, hunspell, etc.
        class MockSpellChecker:
            def correction(self, word: str) -> str:
                return word  # Mock implementation
            
            def candidates(self, word: str) -> List[str]:
                return [word]  # Mock implementation
        
        return MockSpellChecker()
    
    def _initialize_punctuation_model(self):
        """Initialize punctuation prediction model."""
        # In production, would use ML models for punctuation prediction
        class MockPunctuationModel:
            def add_punctuation(self, text: str) -> str:
                # Simple mock implementation
                sentences = text.split('.')
                result = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence:
                        # Capitalize first word
                        words = sentence.split()
                        if words:
                            words[0] = words[0].capitalize()
                            result.append(' '.join(words))
                
                return '. '.join(result) + ('.' if not text.endswith('.') else '')
        
        return MockPunctuationModel()
    
    async def process_segment(self,
                            text: str,
                            context_text: str,
                            session_id: str,
                            speaker_id: Optional[str] = None,
                            speaker_type: Optional[SpeakerType] = None,
                            timestamp: Optional[float] = None) -> TranscriptSegment:
        """
        Process a single transcript segment.
        
        Args:
            text: Raw transcript text
            context_text: Context from previous segments
            session_id: Session identifier
            speaker_id: Optional speaker identifier
            speaker_type: Optional speaker type
            timestamp: Optional timestamp
            
        Returns:
            Processed transcript segment
        """
        start_time = datetime.utcnow()
        
        # Get or create session context
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = ProcessingContext(session_id=session_id)
        
        context = self.session_contexts[session_id]
        
        # Create segment
        segment = TranscriptSegment(
            segment_id=generate_message_id(),
            text=text,
            original_text=text,
            speaker_id=speaker_id,
            speaker_type=speaker_type,
            start_time=timestamp or 0.0,
            end_time=timestamp or 0.0,
            duration=0.0,
            confidence=0.8,  # Default confidence
            quality_score=0.0
        )
        
        try:
            # Process text through various enhancement stages
            processed_text = text
            
            # 1. Clean and normalize text
            processed_text = await self._clean_text(processed_text)
            
            # 2. Apply spell checking
            if self.config.enable_spell_check:
                processed_text, spell_corrections = await self._apply_spell_checking(processed_text)
                segment.corrections.extend(spell_corrections)
            
            # 3. Fix legal terminology
            if self.config.enable_legal_terminology:
                processed_text, legal_corrections = await self._fix_legal_terminology(processed_text)
                segment.corrections.extend(legal_corrections)
            
            # 4. Add punctuation and capitalization
            if self.config.enable_punctuation:
                processed_text = await self._add_punctuation(processed_text, context_text)
            
            if self.config.enable_capitalization:
                processed_text = await self._fix_capitalization(processed_text)
            
            # 5. Detect entities and legal terms
            segment.detected_entities = await self._detect_entities(processed_text)
            segment.legal_terms = await self._detect_legal_terms(processed_text)
            
            # 6. Detect events (objections, etc.)
            segment.events = await self._detect_events(processed_text)
            
            # 7. Update segment with processed text
            segment.text = processed_text
            
            # 8. Calculate quality metrics
            segment.quality_score = await self._calculate_quality_score(segment, context)
            
            # 9. Update context
            await self._update_context(context, segment)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            segment.processing_time = processing_time
            
            # Update statistics
            self._update_statistics(segment, processing_time)
            
            self.logger.debug(
                f"Processed segment: '{text[:50]}...' -> '{processed_text[:50]}...' "
                f"({len(segment.corrections)} corrections)"
            )
            
            return segment
            
        except Exception as e:
            self.logger.error(f"Error processing segment: {e}")
            # Return segment with minimal processing
            segment.quality_score = 0.5
            segment.processing_time = (datetime.utcnow() - start_time).total_seconds()
            return segment
    
    async def process_batch(self,
                          segments_data: List[Dict[str, Any]],
                          session_id: str) -> List[TranscriptSegment]:
        """
        Process multiple segments in batch.
        
        Args:
            segments_data: List of segment data dictionaries
            session_id: Session identifier
            
        Returns:
            List of processed transcript segments
        """
        processed_segments = []
        
        # Build context from all segments
        all_text = " ".join([seg.get("text", "") for seg in segments_data])
        
        # Process each segment
        for i, seg_data in enumerate(segments_data):
            # Get context from previous segments
            context_text = " ".join([
                segments_data[j].get("text", "") 
                for j in range(max(0, i - self.config.context_window_size), i)
            ])
            
            segment = await self.process_segment(
                text=seg_data.get("text", ""),
                context_text=context_text,
                session_id=session_id,
                speaker_id=seg_data.get("speaker_id"),
                speaker_type=SpeakerType(seg_data.get("speaker_type", "unknown")) if seg_data.get("speaker_type") else None,
                timestamp=seg_data.get("timestamp")
            )
            
            processed_segments.append(segment)
        
        return processed_segments
    
    async def _clean_text(self, text: str) -> str:
        """Clean and normalize raw transcript text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove filler words in excess
        text = re.sub(r'\b(?:um|uh|ah|er|hmm)\b\s*', '', text, flags=re.IGNORECASE)
        
        # Fix common OCR/STT errors
        text = text.replace(' i ', ' I ')
        text = re.sub(r'\bi\b', 'I', text)
        
        # Remove duplicate punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[!]{2,}', '!', text)
        
        return text.strip()
    
    async def _apply_spell_checking(self, text: str) -> Tuple[str, List[TextCorrection]]:
        """Apply spell checking with legal terminology awareness."""
        corrections = []
        words = text.split()
        corrected_words = []
        
        for i, word in enumerate(words):
            # Skip words that are already in legal dictionary
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            if clean_word in self.legal_dictionary:
                corrected_words.append(self.legal_dictionary[clean_word])
                if word.lower() != self.legal_dictionary[clean_word].lower():
                    corrections.append(TextCorrection(
                        original_text=word,
                        corrected_text=self.legal_dictionary[clean_word],
                        correction_type="legal_terminology",
                        confidence=0.9,
                        position=i
                    ))
            else:
                # Apply general spell checking
                corrected = self.spell_checker.correction(clean_word)
                if corrected != clean_word:
                    # Preserve original capitalization
                    if word.isupper():
                        corrected = corrected.upper()
                    elif word.istitle():
                        corrected = corrected.title()
                    
                    corrected_words.append(corrected)
                    corrections.append(TextCorrection(
                        original_text=word,
                        corrected_text=corrected,
                        correction_type="spelling",
                        confidence=0.7,
                        position=i,
                        suggestions=list(self.spell_checker.candidates(clean_word))
                    ))
                else:
                    corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    async def _fix_legal_terminology(self, text: str) -> Tuple[str, List[TextCorrection]]:
        """Fix legal terminology and standard legal phrases."""
        corrections = []
        corrected_text = text
        
        # Apply legal dictionary corrections
        for incorrect, correct in self.legal_dictionary.items():
            pattern = re.compile(r'\b' + re.escape(incorrect) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(corrected_text)
            
            for match in matches:
                corrections.append(TextCorrection(
                    original_text=match.group(),
                    corrected_text=correct,
                    correction_type="legal_terminology",
                    confidence=0.95,
                    position=match.start()
                ))
            
            corrected_text = pattern.sub(correct, corrected_text)
        
        # Fix common legal phrase patterns
        legal_phrases = {
            r'\byour\s+honour?\b': 'Your Honor',
            r'\bobjection\s+your\s+honor\b': 'Objection, Your Honor',
            r'\bmay\s+it\s+please\s+the\s+court\b': 'May it please the Court',
            r'\bres\s+ipsa\s+loquitur\b': 'res ipsa loquitur',
            r'\bprima\s+facie\b': 'prima facie',
            r'\bhabeas\s+corpus\b': 'habeas corpus',
            r'\bamicus\s+curiae\b': 'amicus curiae',
        }
        
        for pattern, replacement in legal_phrases.items():
            regex = re.compile(pattern, re.IGNORECASE)
            matches = regex.finditer(corrected_text)
            
            for match in matches:
                corrections.append(TextCorrection(
                    original_text=match.group(),
                    corrected_text=replacement,
                    correction_type="legal_phrase",
                    confidence=0.9,
                    position=match.start()
                ))
            
            corrected_text = regex.sub(replacement, corrected_text)
        
        return corrected_text, corrections
    
    async def _add_punctuation(self, text: str, context: str) -> str:
        """Add appropriate punctuation using context."""
        # Use punctuation model if available via API
        if self.api_client:
            try:
                response = await self.api_client.post(
                    "/ai/add-punctuation",
                    json={
                        "text": text,
                        "context": context,
                        "domain": "legal"
                    },
                    timeout=10.0
                )
                
                if response.get("success"):
                    return response.get("punctuated_text", text)
            except Exception as e:
                self.logger.warning(f"API punctuation failed, using fallback: {e}")
        
        # Fallback to rule-based punctuation
        return self.punctuation_model.add_punctuation(text)
    
    async def _fix_capitalization(self, text: str) -> str:
        """Fix capitalization for legal documents."""
        # Capitalize sentence beginnings
        sentences = re.split(r'([.!?]+\s*)', text)
        
        for i in range(0, len(sentences), 2):  # Every other element is text
            if sentences[i].strip():
                sentences[i] = sentences[i].strip()
                if sentences[i]:
                    sentences[i] = sentences[i][0].upper() + sentences[i][1:]
        
        text = ''.join(sentences)
        
        # Capitalize legal terms that should always be capitalized
        legal_caps = {
            r'\byour\s+honor\b': 'Your Honor',
            r'\bcourt\b(?=\s+(?:finds|orders|holds|rules))': 'Court',
            r'\bstate\s+of\s+(\w+)\b': lambda m: f'State of {m.group(1).title()}',
            r'\bunited\s+states\b': 'United States',
        }
        
        for pattern, replacement in legal_caps.items():
            if callable(replacement):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            else:
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    async def _detect_entities(self, text: str) -> List[Dict[str, Any]]:
        """Detect named entities in text."""
        entities = []
        
        # Use NER API if available
        if self.api_client:
            try:
                response = await self.api_client.post(
                    "/ai/extract-entities",
                    json={
                        "text": text,
                        "entity_types": ["PERSON", "ORG", "DATE", "MONEY", "LAW"]
                    },
                    timeout=10.0
                )
                
                if response.get("success"):
                    return response.get("entities", [])
            except Exception as e:
                self.logger.warning(f"Entity detection failed: {e}")
        
        # Fallback to rule-based entity detection
        # Detect money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        for match in re.finditer(money_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "MONEY",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.8
            })
        
        # Detect dates
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "text": match.group(),
                    "label": "DATE",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.7
                })
        
        return entities
    
    async def _detect_legal_terms(self, text: str) -> List[str]:
        """Detect legal terms in text."""
        legal_terms = []
        
        for pattern_name, pattern in self.legal_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                if match not in legal_terms:
                    legal_terms.append(match)
        
        # Also check against legal dictionary
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            if word in self.legal_dictionary:
                term = self.legal_dictionary[word]
                if term not in legal_terms:
                    legal_terms.append(term)
        
        return legal_terms
    
    async def _detect_events(self, text: str) -> List[Dict[str, Any]]:
        """Detect legal events in text (objections, rulings, etc.)."""
        events = []
        
        # Detect objections
        for objection_type, pattern in self.objection_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                events.append({
                    "type": "objection",
                    "subtype": objection_type,
                    "text": match.group(),
                    "position": match.start(),
                    "confidence": 0.9
                })
        
        # Detect rulings
        ruling_patterns = {
            "sustained": re.compile(r'\bsustained\b', re.IGNORECASE),
            "overruled": re.compile(r'\boverruled\b', re.IGNORECASE),
        }
        
        for ruling_type, pattern in ruling_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                events.append({
                    "type": "ruling",
                    "subtype": ruling_type,
                    "text": match.group(),
                    "position": match.start(),
                    "confidence": 0.95
                })
        
        # Detect procedural events
        procedural_events = {
            "recess": r'\b(?:recess|break|adjourn)\b',
            "sidebar": r'\bsidebar\b',
            "approach": r'\bapproach(?:\s+the\s+bench)?\b',
        }
        
        for event_type, pattern in procedural_events.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                events.append({
                    "type": "procedural",
                    "subtype": event_type,
                    "text": match.group(),
                    "position": match.start(),
                    "confidence": 0.8
                })
        
        return events
    
    async def _calculate_quality_score(self, 
                                     segment: TranscriptSegment, 
                                     context: ProcessingContext) -> float:
        """Calculate quality score for processed segment."""
        scores = []
        
        # Base confidence score
        scores.append(segment.confidence)
        
        # Correction ratio (fewer corrections = higher quality)
        correction_penalty = min(segment.correction_ratio * 0.5, 0.3)
        scores.append(1.0 - correction_penalty)
        
        # Legal terms presence (more legal terms = higher quality for legal context)
        legal_term_boost = min(len(segment.legal_terms) * 0.1, 0.2)
        scores.append(0.8 + legal_term_boost)
        
        # Text length (very short or very long segments may be lower quality)
        word_count = segment.word_count
        if 5 <= word_count <= 50:
            scores.append(1.0)
        elif word_count < 5:
            scores.append(0.6)
        else:
            scores.append(0.8)
        
        # Average the scores
        return sum(scores) / len(scores)
    
    async def _update_context(self, context: ProcessingContext, segment: TranscriptSegment):
        """Update processing context with new segment."""
        context.total_segments += 1
        context.recent_segments.append(segment)
        
        # Update speaker history
        if segment.speaker_id:
            if segment.speaker_id not in context.speaker_history:
                context.speaker_history[segment.speaker_id] = []
            context.speaker_history[segment.speaker_id].append(segment.text)
            
            # Limit speaker history
            if len(context.speaker_history[segment.speaker_id]) > 20:
                context.speaker_history[segment.speaker_id].pop(0)
        
        # Update average confidence
        context.average_confidence = (
            (context.average_confidence * (context.total_segments - 1) + segment.confidence) /
            context.total_segments
        )
        
        # Update correction statistics
        for correction in segment.corrections:
            correction_type = correction.correction_type
            context.correction_stats[correction_type] = context.correction_stats.get(correction_type, 0) + 1
    
    def _update_statistics(self, segment: TranscriptSegment, processing_time: float):
        """Update global processing statistics."""
        self.total_processed += 1
        self.total_corrections += len(segment.corrections)
        self.processing_time_total += processing_time
    
    def get_session_context(self, session_id: str) -> Optional[ProcessingContext]:
        """Get processing context for session."""
        return self.session_contexts.get(session_id)
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        avg_processing_time = (
            self.processing_time_total / self.total_processed 
            if self.total_processed > 0 else 0.0
        )
        
        avg_corrections_per_segment = (
            self.total_corrections / self.total_processed
            if self.total_processed > 0 else 0.0
        )
        
        return {
            "total_segments_processed": self.total_processed,
            "total_corrections_made": self.total_corrections,
            "average_processing_time": avg_processing_time,
            "average_corrections_per_segment": avg_corrections_per_segment,
            "active_sessions": len(self.session_contexts),
            "legal_dictionary_size": len(self.legal_dictionary),
            "legal_patterns_loaded": len(self.legal_patterns)
        }
    
    async def cleanup_session(self, session_id: str):
        """Clean up session context."""
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
            self.logger.info(f"Cleaned up processing context for session {session_id}")
    
    def export_corrections_dictionary(self) -> Dict[str, Any]:
        """Export corrections made for dictionary improvement."""
        corrections_by_type = defaultdict(list)
        
        for context in self.session_contexts.values():
            for segment in context.recent_segments:
                for correction in segment.corrections:
                    corrections_by_type[correction.correction_type].append({
                        "original": correction.original_text,
                        "corrected": correction.corrected_text,
                        "confidence": correction.confidence
                    })
        
        return dict(corrections_by_type)