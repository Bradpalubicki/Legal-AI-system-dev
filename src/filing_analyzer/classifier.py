"""
AI-powered document classification for legal filings.

Provides intelligent classification of legal documents using multiple AI models
and rule-based systems to determine filing types, jurisdictions, and relevance.
"""

import re
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..shared.utils import BaseAPIClient
from .models import FilingType, ImpactLevel, UrgencyLevel


@dataclass
class ClassificationFeatures:
    """Features extracted from document for classification."""
    document_title: str
    content_preview: str
    court_mentions: List[str]
    case_numbers: List[str]
    legal_terms: List[str]
    document_structure: Dict[str, Any]
    filing_keywords: List[str]
    jurisdictional_indicators: List[str]
    metadata: Dict[str, Any]


@dataclass
class ClassificationResult:
    """Result of document classification analysis."""
    filing_type: FilingType
    confidence_score: float
    jurisdiction: Optional[str]
    court_level: Optional[str]
    case_number: Optional[str]
    is_time_sensitive: bool
    estimated_complexity: str
    ai_reasoning: str
    features_used: List[str]
    alternative_classifications: List[Tuple[FilingType, float]]
    processing_metadata: Dict[str, Any]


class DocumentClassifier:
    """AI-powered legal document classifier."""
    
    def __init__(self, api_client: BaseAPIClient):
        self.api_client = api_client
        self.legal_patterns = self._initialize_patterns()
        self.court_patterns = self._initialize_court_patterns()
        
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for legal document recognition."""
        return {
            "motion_patterns": [
                r"motion\s+(?:for|to)\s+(?:dismiss|summary\s+judgment|compel)",
                r"plaintiff.{0,50}motion",
                r"defendant.{0,50}motion",
                r"emergency\s+motion",
                r"motion\s+in\s+limine"
            ],
            "brief_patterns": [
                r"brief\s+(?:in\s+support|in\s+opposition)",
                r"memorandum\s+(?:of\s+law|in\s+support)",
                r"appellate\s+brief",
                r"trial\s+brief"
            ],
            "complaint_patterns": [
                r"complaint\s+(?:for|seeking)",
                r"verified\s+complaint",
                r"amended\s+complaint",
                r"class\s+action\s+complaint"
            ],
            "discovery_patterns": [
                r"request\s+for\s+(?:production|admission)",
                r"interrogator(?:y|ies)",
                r"deposition\s+(?:notice|transcript)",
                r"discovery\s+dispute"
            ],
            "contract_patterns": [
                r"(?:service|employment|purchase)\s+agreement",
                r"terms\s+(?:of|and)\s+conditions",
                r"memorandum\s+of\s+understanding",
                r"non-disclosure\s+agreement"
            ]
        }
    
    def _initialize_court_patterns(self) -> Dict[str, str]:
        """Initialize patterns for court level identification."""
        return {
            r"supreme\s+court": "supreme",
            r"court\s+of\s+appeals": "appellate",
            r"district\s+court": "district",
            r"bankruptcy\s+court": "bankruptcy",
            r"tax\s+court": "tax",
            r"family\s+court": "family",
            r"probate\s+court": "probate",
            r"municipal\s+court": "municipal"
        }
    
    async def classify_document(self, 
                              content: str,
                              metadata: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """
        Classify a legal document using AI and rule-based analysis.
        
        Args:
            content: Full text content of the document
            metadata: Optional document metadata (filename, source, etc.)
            
        Returns:
            ClassificationResult with filing type and analysis details
        """
        metadata = metadata or {}
        
        # Extract features from document
        features = self._extract_features(content, metadata)
        
        # Get rule-based classification
        rule_based_result = self._classify_with_rules(features)
        
        # Get AI-powered classification
        ai_result = await self._classify_with_ai(content, features)
        
        # Combine results
        final_result = self._combine_classifications(
            rule_based_result, ai_result, features
        )
        
        return final_result
    
    def _extract_features(self, 
                         content: str,
                         metadata: Dict[str, Any]) -> ClassificationFeatures:
        """Extract relevant features from document content."""
        content_lower = content.lower()
        
        return ClassificationFeatures(
            document_title=self._extract_title(content, metadata),
            content_preview=content[:1000],
            court_mentions=self._extract_court_mentions(content),
            case_numbers=self._extract_case_numbers(content),
            legal_terms=self._extract_legal_terms(content_lower),
            document_structure=self._analyze_structure(content),
            filing_keywords=self._extract_filing_keywords(content_lower),
            jurisdictional_indicators=self._extract_jurisdictions(content),
            metadata=metadata
        )
    
    def _extract_title(self, content: str, metadata: Dict[str, Any]) -> str:
        """Extract document title from content or metadata."""
        if "filename" in metadata:
            return Path(metadata["filename"]).stem
        
        lines = content.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                return line
        
        return "Unknown Document"
    
    def _extract_court_mentions(self, content: str) -> List[str]:
        """Extract court names and references from content."""
        courts = []
        court_patterns = [
            r"(?:united states|u\.s\.)\s+(?:district\s+)?court",
            r"(?:state\s+)?supreme\s+court",
            r"court\s+of\s+appeals",
            r"bankruptcy\s+court",
            r"(?:circuit|district)\s+court"
        ]
        
        for pattern in court_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            courts.extend([match.group() for match in matches])
        
        return list(set(courts))
    
    def _extract_case_numbers(self, content: str) -> List[str]:
        """Extract case numbers from document content."""
        case_patterns = [
            r"(?:case\s+(?:no\.?|number):?\s*)?(\d{1,2}:\d{2}-cv-\d{5})",
            r"(?:case\s+(?:no\.?|number):?\s*)?(\d{4}-\d{4,6})",
            r"(?:docket\s+(?:no\.?|number):?\s*)?([A-Z]{1,3}-?\d{2,4}-\d{3,6})"
        ]
        
        case_numbers = []
        for pattern in case_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            case_numbers.extend([match.group(1) for match in matches])
        
        return list(set(case_numbers))
    
    def _extract_legal_terms(self, content: str) -> List[str]:
        """Extract legal terminology and key phrases."""
        legal_terms = [
            "plaintiff", "defendant", "petitioner", "respondent",
            "appellant", "appellee", "deposition", "discovery",
            "motion", "brief", "complaint", "answer", "counterclaim",
            "injunction", "damages", "jurisdiction", "venue",
            "summary judgment", "due process", "constitutional"
        ]
        
        found_terms = []
        for term in legal_terms:
            if term in content:
                found_terms.append(term)
        
        return found_terms
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze document structure and formatting."""
        lines = content.split('\n')
        
        return {
            "total_lines": len(lines),
            "paragraph_count": len([line for line in lines if line.strip()]),
            "has_numbered_sections": bool(re.search(r'^\s*\d+\.', content, re.MULTILINE)),
            "has_signature_block": bool(re.search(r'respectfully\s+submitted|signature', content, re.IGNORECASE)),
            "has_certificate": bool(re.search(r'certificate\s+of\s+service', content, re.IGNORECASE)),
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
        }
    
    def _extract_filing_keywords(self, content: str) -> List[str]:
        """Extract keywords that indicate specific filing types."""
        keyword_groups = {
            "motion": ["move", "moving", "motion", "request", "ask", "seek"],
            "brief": ["argument", "brief", "memorandum", "support", "opposition"],
            "complaint": ["complaint", "alleges", "plaintiff", "cause of action"],
            "discovery": ["discovery", "interrogatory", "production", "admission"],
            "contract": ["agreement", "contract", "terms", "conditions", "parties"]
        }
        
        found_keywords = []
        for category, keywords in keyword_groups.items():
            for keyword in keywords:
                if keyword in content:
                    found_keywords.append(f"{category}:{keyword}")
        
        return found_keywords
    
    def _extract_jurisdictions(self, content: str) -> List[str]:
        """Extract jurisdictional indicators from content."""
        jurisdictions = []
        
        state_patterns = [
            r"state\s+of\s+(\w+)",
            r"commonwealth\s+of\s+(\w+)",
            r"district\s+of\s+columbia"
        ]
        
        federal_patterns = [
            r"united\s+states",
            r"federal\s+(?:court|district)",
            r"u\.s\.\s+district"
        ]
        
        for pattern in state_patterns + federal_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            jurisdictions.extend([match.group() for match in matches])
        
        return list(set(jurisdictions))
    
    def _classify_with_rules(self, features: ClassificationFeatures) -> Dict[str, Any]:
        """Apply rule-based classification logic."""
        scores = {}
        
        # Check against pattern groups
        content_combined = (features.content_preview + " " + 
                          features.document_title + " " +
                          " ".join(features.filing_keywords)).lower()
        
        for filing_type_name, patterns in self.legal_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, content_combined, re.IGNORECASE):
                    score += 1
            scores[filing_type_name] = score / len(patterns)
        
        # Determine best match
        best_match = max(scores, key=scores.get) if scores else "other"
        confidence = scores.get(best_match, 0.0)
        
        # Map pattern names to FilingType
        filing_type_map = {
            "motion_patterns": FilingType.MOTION,
            "brief_patterns": FilingType.BRIEF,
            "complaint_patterns": FilingType.COMPLAINT,
            "discovery_patterns": FilingType.DISCOVERY_REQUEST,
            "contract_patterns": FilingType.CONTRACT
        }
        
        filing_type = filing_type_map.get(best_match, FilingType.OTHER)
        
        return {
            "filing_type": filing_type,
            "confidence": confidence,
            "reasoning": f"Rule-based match on {best_match}",
            "scores": scores
        }
    
    async def _classify_with_ai(self, 
                               content: str,
                               features: ClassificationFeatures) -> Dict[str, Any]:
        """Use AI model to classify the document."""
        prompt = self._build_classification_prompt(content, features)
        
        try:
            response = await self.api_client.post(
                "/ai/classify",
                json={
                    "prompt": prompt,
                    "model": "gpt-4",
                    "temperature": 0.1,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            
            ai_analysis = response.get("analysis", {})
            
            return {
                "filing_type": FilingType(ai_analysis.get("filing_type", "other")),
                "confidence": ai_analysis.get("confidence", 0.0),
                "reasoning": ai_analysis.get("reasoning", "AI classification"),
                "complexity": ai_analysis.get("complexity", "medium"),
                "time_sensitive": ai_analysis.get("time_sensitive", False)
            }
            
        except Exception as e:
            # Fallback to rule-based if AI fails
            return {
                "filing_type": FilingType.OTHER,
                "confidence": 0.0,
                "reasoning": f"AI classification failed: {str(e)}",
                "complexity": "unknown",
                "time_sensitive": False
            }
    
    def _build_classification_prompt(self, 
                                   content: str,
                                   features: ClassificationFeatures) -> str:
        """Build prompt for AI classification."""
        filing_types = ", ".join([ft.value for ft in FilingType])
        
        return f"""
Classify this legal document and provide analysis:

Document Title: {features.document_title}
Court Mentions: {', '.join(features.court_mentions)}
Case Numbers: {', '.join(features.case_numbers)}
Legal Terms Found: {', '.join(features.legal_terms[:10])}

Content Preview:
{content[:2000]}

Please classify this document as one of: {filing_types}

Provide your response in this JSON format:
{{
    "filing_type": "one_of_the_types_above",
    "confidence": 0.85,
    "reasoning": "Explanation of classification decision",
    "complexity": "low|medium|high",
    "time_sensitive": true/false,
    "jurisdiction": "federal|state|local",
    "court_level": "district|appellate|supreme|bankruptcy|other"
}}
"""
    
    def _combine_classifications(self,
                               rule_result: Dict[str, Any],
                               ai_result: Dict[str, Any],
                               features: ClassificationFeatures) -> ClassificationResult:
        """Combine rule-based and AI classification results."""
        
        # Weight the results (AI gets higher weight if confident)
        ai_confidence = ai_result.get("confidence", 0.0)
        rule_confidence = rule_result.get("confidence", 0.0)
        
        if ai_confidence > 0.7:
            primary_result = ai_result
            confidence = ai_confidence
        elif rule_confidence > 0.5:
            primary_result = rule_result
            confidence = rule_confidence
        else:
            # Low confidence, combine scores
            primary_result = ai_result if ai_confidence >= rule_confidence else rule_result
            confidence = max(ai_confidence, rule_confidence) * 0.7  # Reduce confidence
        
        # Determine court level
        court_level = None
        for pattern, level in self.court_patterns.items():
            if any(re.search(pattern, court, re.IGNORECASE) for court in features.court_mentions):
                court_level = level
                break
        
        # Build alternative classifications
        alternatives = []
        if ai_result["filing_type"] != rule_result["filing_type"]:
            alternatives.append((
                rule_result["filing_type"] if primary_result == ai_result else ai_result["filing_type"],
                rule_result["confidence"] if primary_result == ai_result else ai_result["confidence"]
            ))
        
        return ClassificationResult(
            filing_type=primary_result["filing_type"],
            confidence_score=confidence,
            jurisdiction=ai_result.get("jurisdiction"),
            court_level=court_level or ai_result.get("court_level"),
            case_number=features.case_numbers[0] if features.case_numbers else None,
            is_time_sensitive=ai_result.get("time_sensitive", False),
            estimated_complexity=ai_result.get("complexity", "medium"),
            ai_reasoning=f"Rule-based: {rule_result['reasoning']}; AI: {ai_result['reasoning']}",
            features_used=[
                f"court_mentions: {len(features.court_mentions)}",
                f"case_numbers: {len(features.case_numbers)}",
                f"legal_terms: {len(features.legal_terms)}",
                f"filing_keywords: {len(features.filing_keywords)}"
            ],
            alternative_classifications=alternatives,
            processing_metadata={
                "rule_confidence": rule_confidence,
                "ai_confidence": ai_confidence,
                "features_extracted": len(features.legal_terms) + len(features.filing_keywords),
                "classification_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def batch_classify(self, 
                           documents: List[Tuple[str, Optional[Dict[str, Any]]]]) -> List[ClassificationResult]:
        """Classify multiple documents concurrently."""
        tasks = [
            self.classify_document(content, metadata)
            for content, metadata in documents
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)