"""
Enhanced Document Processor with Multi-Model AI Selection

This module provides intelligent document processing with automatic complexity detection
and cost-optimized AI model selection for legal document analysis.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
import re
import statistics

# Import AI components
from ..shared.ai.ai_router import legal_ai_router
from ..shared.ai.model_selector import ModelTier, TaskType, ProcessingResult
from ..shared.ai.claude_client import SmartClaudeClient

# Configure logging
logger = logging.getLogger(__name__)


class DocumentComplexity(Enum):
    """Document complexity levels for model selection."""
    SIMPLE = "simple"           # Haiku tier: $0.01
    MODERATE = "moderate"       # Sonnet tier: $0.15
    COMPLEX = "complex"         # Opus tier: $0.75


class ProcessingTier(Enum):
    """Processing tiers with cost optimization."""
    QUICK_TRIAGE = "quick_triage"        # Haiku: $0.01 per doc
    STANDARD_REVIEW = "standard_review"  # Sonnet: $0.15 per doc
    DEEP_ANALYSIS = "deep_analysis"      # Opus: $0.75 per doc


@dataclass
class DocumentCharacteristics:
    """Document characteristics for complexity analysis."""
    page_count: int
    word_count: int
    legal_term_density: float
    party_count: int
    clause_complexity: float
    has_tables: bool
    has_signatures: bool
    document_type: str
    language_complexity: float
    reference_count: int


@dataclass
class ProcessingResult:
    """Result of document processing with model metadata."""
    content: str
    model_used: ModelTier
    processing_tier: ProcessingTier
    confidence_score: float
    processing_cost: float
    processing_time: float
    complexity_score: float
    task_type: TaskType
    token_usage: Dict[str, int]
    metadata: Dict[str, Any]


class ComplexityAnalyzer:
    """Analyzes document complexity for optimal model selection."""

    def __init__(self):
        self.legal_terms = {
            'high_complexity': [
                'whereas', 'heretofore', 'aforementioned', 'notwithstanding',
                'indemnification', 'liquidated damages', 'force majeure',
                'arbitration', 'jurisdiction', 'governing law', 'severability',
                'intellectual property', 'confidentiality', 'non-disclosure',
                'escrow', 'collateral', 'subordination', 'acceleration'
            ],
            'medium_complexity': [
                'party', 'parties', 'agreement', 'contract', 'terms',
                'conditions', 'obligations', 'rights', 'liability',
                'warranty', 'representation', 'covenant', 'breach',
                'termination', 'amendment', 'assignment', 'consideration'
            ],
            'legal_indicators': [
                'shall', 'may', 'must', 'agrees', 'acknowledges',
                'represents', 'warrants', 'covenants', 'undertakes'
            ]
        }

    def analyze_document_characteristics(self, document_text: str) -> DocumentCharacteristics:
        """Analyze document characteristics for complexity scoring."""

        # Basic metrics
        word_count = len(document_text.split())
        page_count = max(1, word_count // 250)  # Estimate pages

        # Legal term analysis
        legal_term_density = self._calculate_legal_term_density(document_text)

        # Party analysis
        party_count = self._count_parties(document_text)

        # Clause complexity
        clause_complexity = self._analyze_clause_complexity(document_text)

        # Document structure analysis
        has_tables = bool(re.search(r'\|.*\||\t.*\t', document_text))
        has_signatures = bool(re.search(r'signature|signed|executed', document_text, re.IGNORECASE))

        # Document type detection
        document_type = self._detect_document_type(document_text)

        # Language complexity
        language_complexity = self._analyze_language_complexity(document_text)

        # Reference count
        reference_count = self._count_references(document_text)

        return DocumentCharacteristics(
            page_count=page_count,
            word_count=word_count,
            legal_term_density=legal_term_density,
            party_count=party_count,
            clause_complexity=clause_complexity,
            has_tables=has_tables,
            has_signatures=has_signatures,
            document_type=document_type,
            language_complexity=language_complexity,
            reference_count=reference_count
        )

    def calculate_complexity_score(self, characteristics: DocumentCharacteristics) -> float:
        """Calculate overall complexity score (0.0 to 1.0)."""

        # Weight factors for different characteristics
        weights = {
            'page_count': 0.15,
            'legal_term_density': 0.25,
            'party_count': 0.15,
            'clause_complexity': 0.20,
            'language_complexity': 0.15,
            'document_structure': 0.10
        }

        # Normalize individual scores
        page_score = min(1.0, characteristics.page_count / 50)  # 50+ pages = max complexity
        legal_score = min(1.0, characteristics.legal_term_density)
        party_score = min(1.0, characteristics.party_count / 10)  # 10+ parties = max complexity
        clause_score = characteristics.clause_complexity
        language_score = characteristics.language_complexity

        # Document structure complexity
        structure_score = 0.0
        if characteristics.has_tables:
            structure_score += 0.3
        if characteristics.has_signatures:
            structure_score += 0.2
        if characteristics.reference_count > 5:
            structure_score += 0.3
        structure_score += min(0.2, characteristics.reference_count / 25)
        structure_score = min(1.0, structure_score)

        # Calculate weighted score
        complexity_score = (
            weights['page_count'] * page_score +
            weights['legal_term_density'] * legal_score +
            weights['party_count'] * party_score +
            weights['clause_complexity'] * clause_score +
            weights['language_complexity'] * language_score +
            weights['document_structure'] * structure_score
        )

        return min(1.0, complexity_score)

    def determine_complexity_level(self, complexity_score: float) -> DocumentComplexity:
        """Determine complexity level from score."""
        if complexity_score >= 0.7:
            return DocumentComplexity.COMPLEX
        elif complexity_score >= 0.4:
            return DocumentComplexity.MODERATE
        else:
            return DocumentComplexity.SIMPLE

    def _calculate_legal_term_density(self, text: str) -> float:
        """Calculate density of legal terminology."""
        words = text.lower().split()
        if not words:
            return 0.0

        total_legal_terms = 0
        for term_list in self.legal_terms.values():
            total_legal_terms += sum(1 for word in words if word in term_list)

        return min(1.0, total_legal_terms / len(words) * 100)  # Normalize to 0-1

    def _count_parties(self, text: str) -> int:
        """Count number of parties in the document."""
        # Look for party definitions and references
        party_patterns = [
            r'\b(party|parties)\b',
            r'\b(plaintiff|defendant)\b',
            r'\b(licensor|licensee)\b',
            r'\b(buyer|seller)\b',
            r'\b(client|customer)\b',
            r'\b(contractor|subcontractor)\b'
        ]

        party_count = 0
        for pattern in party_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            party_count += len(set(matches))  # Unique matches only

        return min(party_count, 20)  # Cap at reasonable number

    def _analyze_clause_complexity(self, text: str) -> float:
        """Analyze complexity of legal clauses."""
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.0

        complexity_indicators = [
            r'\b(provided that|subject to|notwithstanding)\b',
            r'\b(in the event that|to the extent that)\b',
            r'\b(except as|unless and until)\b',
            r'\([^)]{50,}\)',  # Long parenthetical clauses
            r'[;]{2,}',        # Multiple semicolons indicate complex structure
        ]

        complex_sentences = 0
        for sentence in sentences:
            sentence_complexity = sum(1 for pattern in complexity_indicators
                                    if re.search(pattern, sentence, re.IGNORECASE))
            if sentence_complexity > 0 or len(sentence.split()) > 30:
                complex_sentences += 1

        return min(1.0, complex_sentences / len(sentences))

    def _detect_document_type(self, text: str) -> str:
        """Detect the type of legal document."""
        type_patterns = {
            'contract': r'\b(agreement|contract)\b',
            'lease': r'\b(lease|rental|tenant)\b',
            'litigation': r'\b(complaint|motion|brief|pleading)\b',
            'corporate': r'\b(bylaws|articles|incorporation)\b',
            'intellectual_property': r'\b(patent|trademark|copyright)\b',
            'employment': r'\b(employment|severance|non-compete)\b',
            'merger': r'\b(merger|acquisition|purchase)\b'
        }

        for doc_type, pattern in type_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return doc_type

        return 'general'

    def _analyze_language_complexity(self, text: str) -> float:
        """Analyze language complexity (sentence length, vocabulary)."""
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.0

        # Calculate average sentence length
        sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence.strip()]
        if not sentence_lengths:
            return 0.0

        avg_sentence_length = statistics.mean(sentence_lengths)

        # Normalize: 20+ words per sentence = high complexity
        length_complexity = min(1.0, avg_sentence_length / 20)

        # Vocabulary complexity (long words, Latin phrases)
        words = text.split()
        long_words = sum(1 for word in words if len(word) > 8)
        vocab_complexity = min(1.0, long_words / len(words) * 10) if words else 0.0

        return (length_complexity + vocab_complexity) / 2

    def _count_references(self, text: str) -> int:
        """Count legal references and citations."""
        reference_patterns = [
            r'\b\d+\s+U\.S\.C\.\s+§\s*\d+',  # USC citations
            r'\bSec\.\s*\d+',                 # Section references
            r'\b\d+\s+CFR\s+\d+',            # CFR citations
            r'\bexhibit\s+[A-Z]?\d*\b',      # Exhibit references
            r'\bschedule\s+[A-Z]?\d*\b',     # Schedule references
        ]

        total_references = 0
        for pattern in reference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            total_references += len(matches)

        return total_references


class DocumentProcessor:
    """Enhanced document processor with multi-model AI selection."""

    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.claude_client = SmartClaudeClient()

        # Processing tier mappings
        self.tier_mappings = {
            DocumentComplexity.SIMPLE: ProcessingTier.QUICK_TRIAGE,
            DocumentComplexity.MODERATE: ProcessingTier.STANDARD_REVIEW,
            DocumentComplexity.COMPLEX: ProcessingTier.DEEP_ANALYSIS
        }

        # Cost limits by tier
        self.cost_limits = {
            ProcessingTier.QUICK_TRIAGE: 0.01,
            ProcessingTier.STANDARD_REVIEW: 0.15,
            ProcessingTier.DEEP_ANALYSIS: 0.75
        }

    async def process_document(
        self,
        document_text: str,
        task_type: Optional[str] = None,
        force_tier: Optional[ProcessingTier] = None,
        max_cost: Optional[float] = None,
        min_confidence: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process document with intelligent model selection based on complexity.

        Args:
            document_text: Document content to process
            task_type: Type of processing task (auto-detected if None)
            force_tier: Force specific processing tier
            max_cost: Maximum cost constraint
            min_confidence: Minimum confidence requirement
            user_id: User ID for tracking

        Returns:
            ProcessingResult with analysis and metadata
        """
        start_time = datetime.now()

        try:
            # Analyze document characteristics
            characteristics = self.complexity_analyzer.analyze_document_characteristics(document_text)
            complexity_score = self.complexity_analyzer.calculate_complexity_score(characteristics)
            complexity_level = self.complexity_analyzer.determine_complexity_level(complexity_score)

            # Determine processing tier
            if force_tier:
                processing_tier = force_tier
            else:
                processing_tier = self.tier_mappings[complexity_level]

            # Set cost and confidence constraints
            tier_max_cost = self.cost_limits[processing_tier]
            final_max_cost = min(max_cost or tier_max_cost, tier_max_cost)

            # Adjust confidence based on tier
            tier_confidence = {
                ProcessingTier.QUICK_TRIAGE: 0.65,
                ProcessingTier.STANDARD_REVIEW: 0.75,
                ProcessingTier.DEEP_ANALYSIS: 0.85
            }
            final_min_confidence = max(min_confidence or 0.0, tier_confidence[processing_tier])

            # Route to appropriate AI processing
            if task_type and task_type in ['classification', 'simple_extraction']:
                # Force quick processing for simple tasks
                result = await self._process_simple_task(
                    document_text, task_type, final_max_cost, final_min_confidence
                )
            elif processing_tier == ProcessingTier.DEEP_ANALYSIS:
                # Use comprehensive analysis for complex documents
                result = await self._process_complex_task(
                    document_text, characteristics, final_max_cost, final_min_confidence
                )
            else:
                # Standard processing
                result = await self._process_standard_task(
                    document_text, characteristics, final_max_cost, final_min_confidence
                )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Create processing result
            return ProcessingResult(
                content=result.get('analysis_result', ''),
                model_used=ModelTier(result.get('model_used', 'claude-3-haiku-20240307')),
                processing_tier=processing_tier,
                confidence_score=result.get('confidence_score', 0.0),
                processing_cost=result.get('processing_cost', 0.0),
                processing_time=processing_time,
                complexity_score=complexity_score,
                task_type=TaskType.STANDARD_ANALYSIS,  # Would be determined from actual task
                token_usage=result.get('token_usage', {}),
                metadata={
                    'characteristics': characteristics.__dict__,
                    'complexity_level': complexity_level.value,
                    'tier_selected': processing_tier.value,
                    'document_type': characteristics.document_type,
                    'processing_timestamp': datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error in document processing: {e}")
            # Return error result
            return ProcessingResult(
                content=f"Processing failed: {str(e)}",
                model_used=ModelTier.HAIKU,
                processing_tier=ProcessingTier.QUICK_TRIAGE,
                confidence_score=0.0,
                processing_cost=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                complexity_score=0.0,
                task_type=TaskType.STANDARD_ANALYSIS,
                token_usage={},
                metadata={'error': str(e)}
            )

    async def _process_simple_task(
        self,
        document_text: str,
        task_type: str,
        max_cost: float,
        min_confidence: float
    ) -> Dict[str, Any]:
        """Process simple tasks with Haiku model."""
        return await legal_ai_router.route_document_analysis(
            document_text=document_text,
            analysis_type=task_type,
            max_cost=max_cost,
            min_confidence=min_confidence
        )

    async def _process_standard_task(
        self,
        document_text: str,
        characteristics: DocumentCharacteristics,
        max_cost: float,
        min_confidence: float
    ) -> Dict[str, Any]:
        """Process standard tasks with Sonnet model."""
        analysis_type = 'comprehensive' if characteristics.document_type in ['contract', 'lease'] else 'standard'

        return await legal_ai_router.route_document_analysis(
            document_text=document_text,
            analysis_type=analysis_type,
            max_cost=max_cost,
            min_confidence=min_confidence
        )

    async def _process_complex_task(
        self,
        document_text: str,
        characteristics: DocumentCharacteristics,
        max_cost: float,
        min_confidence: float
    ) -> Dict[str, Any]:
        """Process complex tasks with Opus model for highest quality."""
        # Use Claude client for complex analysis
        try:
            result = await self.claude_client.complex_analysis(
                document=document_text,
                query="Provide comprehensive legal analysis including risks, compliance, and strategic recommendations",
                analysis_type='comprehensive'
            )

            return {
                'analysis_result': result.get('analysis', ''),
                'model_used': result.get('model_used', 'claude-3-opus-latest'),
                'confidence_score': result.get('confidence', 0.0),
                'processing_cost': result.get('cost', 0.0),
                'token_usage': result.get('token_usage', {})
            }

        except Exception as e:
            logger.error(f"Complex analysis failed, falling back to standard: {e}")
            # Fallback to standard processing
            return await self._process_standard_task(
                document_text, characteristics, max_cost, min_confidence
            )

    async def classify_document(
        self,
        document_text: str,
        classification_types: List[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Quick document classification using Haiku model.

        Cost: ~$0.01 per document
        """
        result = await self.process_document(
            document_text=document_text,
            task_type='classification',
            force_tier=ProcessingTier.QUICK_TRIAGE,
            max_cost=0.01,
            min_confidence=0.65,
            user_id=user_id
        )

        return {
            'document_type': result.metadata.get('document_type', 'unknown'),
            'complexity_level': result.metadata.get('complexity_level', 'simple'),
            'confidence': result.confidence_score,
            'model_used': result.model_used.value,
            'processing_cost': result.processing_cost,
            'tier': result.processing_tier.value
        }

    async def extract_data(
        self,
        document_text: str,
        extraction_fields: List[str],
        complexity_override: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract data with complexity-based model selection.

        Cost: $0.01 (Haiku) to $0.15 (Sonnet) based on complexity
        """
        # Determine if extraction is complex
        complex_fields = ['legal_analysis', 'risk_assessment', 'strategic_implications']
        is_complex = any(field in complex_fields for field in extraction_fields)

        # Override tier if specified
        if complexity_override:
            if complexity_override.lower() == 'haiku':
                tier = ProcessingTier.QUICK_TRIAGE
            elif complexity_override.lower() == 'sonnet':
                tier = ProcessingTier.STANDARD_REVIEW
            else:
                tier = ProcessingTier.DEEP_ANALYSIS
        else:
            tier = ProcessingTier.STANDARD_REVIEW if is_complex else ProcessingTier.QUICK_TRIAGE

        result = await self.process_document(
            document_text=document_text,
            task_type='extraction',
            force_tier=tier,
            user_id=user_id
        )

        # Mock extracted data - would be parsed from AI result in real implementation
        extracted_data = {
            'dates': ['2023-01-15', '2023-12-31'] if 'dates' in extraction_fields else [],
            'parties': ['ABC Corp', 'XYZ LLC'] if 'parties' in extraction_fields else [],
            'amounts': ['$50,000', '$25,000'] if 'amounts' in extraction_fields else [],
            'key_terms': ['confidentiality', 'termination'] if 'key_terms' in extraction_fields else []
        }

        return {
            'extracted_data': extracted_data,
            'extraction_metadata': {
                'fields_requested': extraction_fields,
                'complexity_detected': is_complex,
                'model_used': result.model_used.value,
                'confidence': result.confidence_score,
                'processing_cost': result.processing_cost,
                'tier': result.processing_tier.value
            }
        }

    async def analyze_document(
        self,
        document_text: str,
        analysis_type: str = 'standard',
        urgency: str = 'normal',
        max_cost: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document with Sonnet model by default.

        Cost: ~$0.15 per document (standard analysis)
        """
        # Adjust tier based on urgency
        if urgency == 'critical' and analysis_type == 'comprehensive':
            tier = ProcessingTier.DEEP_ANALYSIS
        elif urgency in ['high', 'critical']:
            tier = ProcessingTier.STANDARD_REVIEW
        else:
            tier = None  # Auto-select based on complexity

        result = await self.process_document(
            document_text=document_text,
            task_type=analysis_type,
            force_tier=tier,
            max_cost=max_cost,
            user_id=user_id
        )

        return {
            'analysis': {
                'executive_summary': 'Document analysis completed with intelligent model selection...',
                'document_type': result.metadata.get('document_type', 'unknown'),
                'complexity_score': result.complexity_score,
                'key_findings': ['Finding 1', 'Finding 2', 'Finding 3'],
                'recommendations': ['Recommendation 1', 'Recommendation 2'],
                'risk_level': 'Medium' if result.complexity_score > 0.5 else 'Low'
            },
            'processing_metadata': {
                'model_used': result.model_used.value,
                'confidence': result.confidence_score,
                'processing_cost': result.processing_cost,
                'processing_time': result.processing_time,
                'tier': result.processing_tier.value,
                'complexity_level': result.metadata.get('complexity_level')
            }
        }

    async def deep_analyze_document(
        self,
        document_text: str,
        analysis_focus: List[str] = None,
        force_opus: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deep analysis using Opus model for critical review.

        Cost: ~$0.75 per document
        """
        result = await self.process_document(
            document_text=document_text,
            task_type='comprehensive',
            force_tier=ProcessingTier.DEEP_ANALYSIS,
            max_cost=1.0 if force_opus else 0.75,
            min_confidence=0.90,
            user_id=user_id
        )

        return {
            'deep_analysis': {
                'executive_summary': 'Comprehensive legal analysis completed...',
                'detailed_findings': {
                    'legal_risks': ['Risk 1', 'Risk 2'],
                    'compliance_issues': ['Issue 1', 'Issue 2'],
                    'strategic_recommendations': ['Rec 1', 'Rec 2']
                },
                'confidence_assessment': result.confidence_score,
                'precedent_analysis': ['Case 1', 'Case 2'],
                'quality_score': result.confidence_score
            },
            'processing_metadata': {
                'model_used': result.model_used.value,
                'confidence': result.confidence_score,
                'processing_cost': result.processing_cost,
                'processing_time': result.processing_time,
                'tier': result.processing_tier.value,
                'analysis_depth': 'comprehensive'
            }
        }

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics and cost analysis."""
        # In real implementation, this would track actual usage
        return {
            'tier_usage': {
                'quick_triage': {'count': 100, 'total_cost': 1.00, 'avg_confidence': 0.68},
                'standard_review': {'count': 50, 'total_cost': 7.50, 'avg_confidence': 0.79},
                'deep_analysis': {'count': 10, 'total_cost': 7.50, 'avg_confidence': 0.92}
            },
            'cost_savings': {
                'total_documents': 160,
                'total_cost': 16.00,
                'estimated_cost_all_opus': 120.00,
                'savings_percentage': 86.7
            },
            'recommendations': [
                'Continue using Haiku for simple classification',
                'Standard review tier provides good balance',
                'Reserve deep analysis for critical documents only'
            ]
        }


# Global processor instance
document_processor = DocumentProcessor()


# Convenience functions for backwards compatibility
async def process_document_with_complexity(
    document_text: str,
    task_type: Optional[str] = None,
    **kwargs
) -> ProcessingResult:
    """Process document with automatic complexity detection."""
    return await document_processor.process_document(document_text, task_type, **kwargs)


async def quick_document_classification(document_text: str) -> Dict[str, Any]:
    """Quick classification using Haiku model ($0.01)."""
    return await document_processor.classify_document(document_text)


async def standard_document_analysis(document_text: str) -> Dict[str, Any]:
    """Standard analysis using Sonnet model ($0.15)."""
    return await document_processor.analyze_document(document_text)


async def deep_document_analysis(document_text: str) -> Dict[str, Any]:
    """Deep analysis using Opus model ($0.75)."""
    return await document_processor.deep_analyze_document(document_text)