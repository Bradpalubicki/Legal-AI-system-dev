"""
Intelligent document categorization system.

Advanced categorization engine that uses AI, rule-based systems, and content
analysis to automatically classify legal documents into appropriate categories.
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

from ..shared.utils import BaseAPIClient
from ..filing_analyzer.classifier import DocumentClassifier, ClassificationResult
from .models import (
    DocumentCategory, CategoryConfidence, DocumentMetadata, ProcessingStatus,
    get_category_from_filename, get_category_confidence_from_score
)


@dataclass
class CategoryRule:
    """Rule for document categorization."""
    rule_id: str
    name: str
    description: str
    category: DocumentCategory
    priority: int  # Higher number = higher priority
    
    # Matching criteria
    filename_patterns: List[str] = field(default_factory=list)
    content_patterns: List[str] = field(default_factory=list)
    metadata_conditions: Dict[str, Any] = field(default_factory=dict)
    file_type_conditions: List[str] = field(default_factory=list)
    
    # Rule configuration
    requires_content_analysis: bool = False
    min_confidence_threshold: float = 0.5
    enabled: bool = True
    
    def matches_filename(self, filename: str) -> bool:
        """Check if filename matches this rule."""
        if not self.filename_patterns:
            return False
        
        filename_lower = filename.lower()
        return any(
            re.search(pattern, filename_lower, re.IGNORECASE)
            for pattern in self.filename_patterns
        )
    
    def matches_content(self, content: str) -> float:
        """Check if content matches this rule and return confidence score."""
        if not self.content_patterns:
            return 0.0
        
        content_lower = content.lower()
        matches = 0
        
        for pattern in self.content_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                matches += 1
        
        return matches / len(self.content_patterns)
    
    def matches_metadata(self, metadata: DocumentMetadata) -> bool:
        """Check if metadata matches this rule."""
        if not self.metadata_conditions:
            return False
        
        for field, expected_value in self.metadata_conditions.items():
            actual_value = getattr(metadata, field, None)
            
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif isinstance(expected_value, str):
                if not actual_value or expected_value.lower() not in str(actual_value).lower():
                    return False
            elif actual_value != expected_value:
                return False
        
        return True


@dataclass
class CategoryResult:
    """Result of document categorization."""
    document_id: str
    primary_category: DocumentCategory
    confidence: CategoryConfidence
    confidence_score: float
    
    # Alternative categories with scores
    alternative_categories: List[Tuple[DocumentCategory, float]] = field(default_factory=list)
    
    # Categorization details
    method_used: str = "unknown"  # ai, rules, filename, hybrid
    rules_applied: List[str] = field(default_factory=list)
    features_analyzed: List[str] = field(default_factory=list)
    
    # Content analysis results
    key_terms: List[str] = field(default_factory=list)
    legal_entities: List[str] = field(default_factory=list)
    dates_found: List[str] = field(default_factory=list)
    
    # Subcategories and tags
    subcategories: List[str] = field(default_factory=list)
    suggested_tags: List[str] = field(default_factory=list)
    
    # Processing metadata
    processing_time: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    warnings: List[str] = field(default_factory=list)


class DocumentCategorizer:
    """Advanced document categorization system."""
    
    def __init__(self, api_client: Optional[BaseAPIClient] = None):
        self.api_client = api_client
        self.document_classifier = DocumentClassifier(api_client) if api_client else None
        self.categorization_rules = self._initialize_rules()
        self.category_keywords = self._initialize_category_keywords()
        self.logger = logging.getLogger(__name__)
        
    def _initialize_rules(self) -> List[CategoryRule]:
        """Initialize categorization rules."""
        rules = []
        
        # Complaint rules
        rules.append(CategoryRule(
            rule_id="complaint_001",
            name="Complaint Detection",
            description="Identifies complaint documents",
            category=DocumentCategory.COMPLAINT,
            priority=90,
            filename_patterns=[
                r"complaint", r"petition", r"^vs?\.", r"v\.", r"complaint.*pdf$"
            ],
            content_patterns=[
                r"plaintiff.*alleges", r"cause.*of.*action", r"complaint.*filed",
                r"comes.*now.*plaintiff", r"wherefore.*plaintiff.*prays"
            ]
        ))
        
        # Motion rules
        rules.append(CategoryRule(
            rule_id="motion_001",
            name="Motion Detection",
            description="Identifies motion documents",
            category=DocumentCategory.MOTION,
            priority=85,
            filename_patterns=[
                r"motion", r"mtd", r"msj", r"motion.*dismiss", r"motion.*summary"
            ],
            content_patterns=[
                r"motion.*for", r"moves.*court", r"respectfully.*moves",
                r"motion.*dismiss", r"summary.*judgment", r"motion.*compel"
            ]
        ))
        
        # Brief rules
        rules.append(CategoryRule(
            rule_id="brief_001",
            name="Brief Detection", 
            description="Identifies legal briefs",
            category=DocumentCategory.BRIEF,
            priority=80,
            filename_patterns=[
                r"brief", r"memorandum", r"memo.*law", r"brief.*support"
            ],
            content_patterns=[
                r"brief.*in.*support", r"memorandum.*of.*law", r"argument.*follows",
                r"legal.*standard", r"statement.*of.*facts"
            ]
        ))
        
        # Contract rules
        rules.append(CategoryRule(
            rule_id="contract_001",
            name="Contract Detection",
            description="Identifies contracts and agreements",
            category=DocumentCategory.CONTRACT,
            priority=75,
            filename_patterns=[
                r"contract", r"agreement", r"agmt", r"service.*agreement"
            ],
            content_patterns=[
                r"this.*agreement", r"parties.*agree", r"terms.*conditions",
                r"whereas.*parties", r"effective.*date", r"consideration"
            ]
        ))
        
        # NDA rules
        rules.append(CategoryRule(
            rule_id="nda_001", 
            name="NDA Detection",
            description="Identifies non-disclosure agreements",
            category=DocumentCategory.NDA,
            priority=85,
            filename_patterns=[
                r"nda", r"non.*disclosure", r"confidentiality.*agreement"
            ],
            content_patterns=[
                r"confidential.*information", r"non.*disclosure", r"proprietary.*information",
                r"confidentiality.*agreement", r"receiving.*party", r"disclosing.*party"
            ]
        ))
        
        # Discovery rules
        rules.append(CategoryRule(
            rule_id="discovery_001",
            name="Discovery Detection",
            description="Identifies discovery documents",
            category=DocumentCategory.DISCOVERY,
            priority=80,
            filename_patterns=[
                r"discovery", r"interrogator", r"request.*production", r"request.*admission"
            ],
            content_patterns=[
                r"request.*for.*production", r"interrogator.*number", r"request.*admission",
                r"please.*produce", r"describe.*in.*detail", r"identify.*all.*documents"
            ]
        ))
        
        # Court order rules
        rules.append(CategoryRule(
            rule_id="order_001",
            name="Court Order Detection",
            description="Identifies court orders and judgments",
            category=DocumentCategory.ORDER,
            priority=90,
            filename_patterns=[
                r"order", r"judgment", r"decree", r"ruling"
            ],
            content_patterns=[
                r"it.*is.*hereby.*ordered", r"court.*orders", r"judgment.*entered",
                r"so.*ordered", r"this.*court.*finds", r"court.*hereby.*grants"
            ]
        ))
        
        # Patent rules
        rules.append(CategoryRule(
            rule_id="patent_001",
            name="Patent Detection",
            description="Identifies patent documents",
            category=DocumentCategory.PATENT,
            priority=85,
            filename_patterns=[
                r"patent", r"uspto", r"invention", r"patent.*application"
            ],
            content_patterns=[
                r"patent.*application", r"field.*of.*invention", r"background.*invention",
                r"claims.*invention", r"patent.*number", r"prior.*art"
            ]
        ))
        
        # Financial document rules
        rules.append(CategoryRule(
            rule_id="financial_001",
            name="Financial Statement Detection",
            description="Identifies financial statements and reports",
            category=DocumentCategory.FINANCIAL_STATEMENT,
            priority=75,
            filename_patterns=[
                r"financial.*statement", r"balance.*sheet", r"income.*statement", r"cash.*flow"
            ],
            content_patterns=[
                r"balance.*sheet", r"income.*statement", r"cash.*flow.*statement",
                r"assets.*liabilities", r"revenue.*expenses", r"net.*income"
            ]
        ))
        
        # Email rules
        rules.append(CategoryRule(
            rule_id="email_001",
            name="Email Detection",
            description="Identifies email communications",
            category=DocumentCategory.EMAIL,
            priority=70,
            filename_patterns=[
                r"email", r"\.eml$", r"\.msg$", r"message"
            ],
            content_patterns=[
                r"from.*to.*subject", r"sent.*received", r"dear.*regards",
                r"@.*\.com", r"subject.*re:", r"original.*message"
            ]
        ))
        
        return rules
    
    def _initialize_category_keywords(self) -> Dict[DocumentCategory, List[str]]:
        """Initialize keyword mappings for each category."""
        return {
            DocumentCategory.COMPLAINT: [
                "plaintiff", "defendant", "alleges", "cause of action", "damages",
                "relief", "wherefore", "jury trial", "violation"
            ],
            DocumentCategory.MOTION: [
                "motion", "moves", "respectfully", "dismiss", "summary judgment",
                "compel", "sanctions", "protective order", "stay"
            ],
            DocumentCategory.BRIEF: [
                "brief", "argument", "memorandum", "legal standard", "case law",
                "precedent", "holding", "reasoning", "conclusion"
            ],
            DocumentCategory.CONTRACT: [
                "agreement", "parties", "consideration", "terms", "conditions",
                "obligations", "breach", "performance", "termination"
            ],
            DocumentCategory.DISCOVERY: [
                "interrogatories", "production", "admission", "deposition",
                "subpoena", "privilege", "work product", "confidential"
            ],
            DocumentCategory.ORDER: [
                "ordered", "adjudged", "decreed", "granted", "denied",
                "sustained", "overruled", "judgment", "so ordered"
            ],
            DocumentCategory.PATENT: [
                "invention", "claims", "prior art", "embodiment", "specification",
                "patent", "uspto", "intellectual property", "novelty"
            ],
            DocumentCategory.FINANCIAL_STATEMENT: [
                "assets", "liabilities", "equity", "revenue", "expenses",
                "net income", "balance sheet", "cash flow", "gaap"
            ]
        }
    
    async def categorize_document(self, 
                                metadata: DocumentMetadata,
                                content: Optional[str] = None) -> CategoryResult:
        """
        Categorize a document using multiple methods.
        
        Args:
            metadata: Document metadata
            content: Optional document text content
            
        Returns:
            CategoryResult with categorization details
        """
        start_time = datetime.utcnow()
        
        # Initialize result
        result = CategoryResult(
            document_id=metadata.document_id,
            primary_category=DocumentCategory.UNKNOWN,
            confidence=CategoryConfidence.VERY_LOW,
            confidence_score=0.0
        )
        
        try:
            # Method 1: Filename-based categorization
            filename_category = self._categorize_by_filename(metadata.filename)
            filename_confidence = 0.3 if filename_category != DocumentCategory.UNKNOWN else 0.0
            
            # Method 2: Rule-based categorization
            rule_result = await self._categorize_by_rules(metadata, content)
            
            # Method 3: AI-based categorization (if available and content provided)
            ai_result = None
            if self.document_classifier and content:
                try:
                    classification = await self.document_classifier.classify_document(content)
                    ai_result = {
                        "category": self._map_filing_type_to_category(classification.filing_type),
                        "confidence": classification.confidence_score,
                        "method": "ai"
                    }
                except Exception as e:
                    self.logger.warning(f"AI classification failed: {e}")
                    result.warnings.append(f"AI classification failed: {str(e)}")
            
            # Method 4: Content keyword analysis
            keyword_result = self._categorize_by_keywords(content) if content else None
            
            # Combine results to determine final category
            final_result = self._combine_categorization_results(
                filename_result=(filename_category, filename_confidence),
                rule_result=rule_result,
                ai_result=ai_result,
                keyword_result=keyword_result
            )
            
            # Update result with final categorization
            result.primary_category = final_result["category"]
            result.confidence_score = final_result["confidence"]
            result.confidence = get_category_confidence_from_score(final_result["confidence"])
            result.method_used = final_result["method"]
            result.alternative_categories = final_result.get("alternatives", [])
            result.rules_applied = final_result.get("rules_applied", [])
            
            # Extract additional information if content is available
            if content:
                result.key_terms = self._extract_key_terms(content, result.primary_category)
                result.legal_entities = self._extract_legal_entities(content)
                result.dates_found = self._extract_dates(content)
                result.subcategories = self._determine_subcategories(
                    result.primary_category, content
                )
                result.suggested_tags = self._generate_tags(
                    result.primary_category, content, metadata
                )
            
            # Update metadata with categorization results
            metadata.category = result.primary_category
            metadata.category_confidence = result.confidence
            metadata.subcategories = result.subcategories
            metadata.processing_status = ProcessingStatus.CATEGORIZING
            metadata.updated_at = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Categorization failed for {metadata.document_id}: {e}")
            result.warnings.append(f"Categorization error: {str(e)}")
        
        # Calculate processing time
        result.processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return result
    
    def _categorize_by_filename(self, filename: str) -> DocumentCategory:
        """Categorize document based on filename patterns."""
        return get_category_from_filename(filename)
    
    async def _categorize_by_rules(self, 
                                 metadata: DocumentMetadata,
                                 content: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Categorize document using rule-based system."""
        best_match = None
        best_score = 0.0
        applied_rules = []
        
        for rule in self.categorization_rules:
            if not rule.enabled:
                continue
            
            score = 0.0
            reasons = []
            
            # Check filename match
            if rule.matches_filename(metadata.filename):
                score += 0.4
                reasons.append("filename")
            
            # Check metadata conditions
            if rule.matches_metadata(metadata):
                score += 0.2
                reasons.append("metadata")
            
            # Check file type conditions
            if rule.file_type_conditions and metadata.file_type in rule.file_type_conditions:
                score += 0.1
                reasons.append("file_type")
            
            # Check content patterns (if content available and required)
            if content and rule.content_patterns:
                content_score = rule.matches_content(content)
                score += content_score * 0.5
                if content_score > 0:
                    reasons.append("content")
            
            # Apply rule priority weight
            weighted_score = score * (rule.priority / 100)
            
            if weighted_score > best_score and weighted_score >= rule.min_confidence_threshold:
                best_match = {
                    "category": rule.category,
                    "confidence": weighted_score,
                    "rule": rule,
                    "reasons": reasons
                }
                best_score = weighted_score
            
            if weighted_score > 0.1:  # Track rules that had some match
                applied_rules.append(rule.rule_id)
        
        if best_match:
            return {
                "category": best_match["category"],
                "confidence": best_match["confidence"],
                "method": "rules",
                "rules_applied": applied_rules,
                "rule_details": best_match
            }
        
        return None
    
    def _categorize_by_keywords(self, content: str) -> Optional[Dict[str, Any]]:
        """Categorize document based on keyword analysis."""
        if not content:
            return None
        
        content_lower = content.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0.0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    # Weight keywords by their specificity (longer = more specific)
                    keyword_weight = len(keyword.split()) * 0.1
                    score += 1.0 + keyword_weight
                    matched_keywords.append(keyword)
            
            if score > 0:
                # Normalize by total possible keywords
                normalized_score = min(score / len(keywords), 1.0)
                category_scores[category] = {
                    "score": normalized_score,
                    "keywords": matched_keywords
                }
        
        if category_scores:
            best_category = max(category_scores.keys(), 
                              key=lambda cat: category_scores[cat]["score"])
            best_score = category_scores[best_category]["score"]
            
            return {
                "category": best_category,
                "confidence": best_score * 0.6,  # Keyword analysis is less reliable
                "method": "keywords",
                "matched_keywords": category_scores[best_category]["keywords"]
            }
        
        return None
    
    def _combine_categorization_results(self, 
                                      filename_result: Tuple[DocumentCategory, float],
                                      rule_result: Optional[Dict[str, Any]],
                                      ai_result: Optional[Dict[str, Any]],
                                      keyword_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine results from different categorization methods."""
        
        candidates = []
        
        # Add filename result
        filename_category, filename_confidence = filename_result
        if filename_category != DocumentCategory.UNKNOWN:
            candidates.append({
                "category": filename_category,
                "confidence": filename_confidence,
                "method": "filename",
                "weight": 0.2
            })
        
        # Add rule result
        if rule_result:
            candidates.append({
                "category": rule_result["category"],
                "confidence": rule_result["confidence"],
                "method": "rules",
                "weight": 0.4,
                "rules_applied": rule_result.get("rules_applied", [])
            })
        
        # Add AI result
        if ai_result:
            candidates.append({
                "category": ai_result["category"],
                "confidence": ai_result["confidence"],
                "method": "ai",
                "weight": 0.5
            })
        
        # Add keyword result
        if keyword_result:
            candidates.append({
                "category": keyword_result["category"],
                "confidence": keyword_result["confidence"],
                "method": "keywords",
                "weight": 0.3
            })
        
        if not candidates:
            return {
                "category": DocumentCategory.UNKNOWN,
                "confidence": 0.0,
                "method": "none",
                "alternatives": []
            }
        
        # Calculate weighted scores
        category_scores = {}
        methods_used = []
        all_rules = []
        
        for candidate in candidates:
            category = candidate["category"]
            weighted_score = candidate["confidence"] * candidate["weight"]
            methods_used.append(candidate["method"])
            
            if "rules_applied" in candidate:
                all_rules.extend(candidate["rules_applied"])
            
            if category in category_scores:
                category_scores[category]["score"] += weighted_score
                category_scores[category]["methods"].append(candidate["method"])
            else:
                category_scores[category] = {
                    "score": weighted_score,
                    "methods": [candidate["method"]]
                }
        
        # Find best category
        best_category = max(category_scores.keys(), 
                          key=lambda cat: category_scores[cat]["score"])
        best_score = category_scores[best_category]["score"]
        best_methods = category_scores[best_category]["methods"]
        
        # Create alternatives list
        alternatives = []
        for category, data in category_scores.items():
            if category != best_category:
                alternatives.append((category, data["score"]))
        
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "category": best_category,
            "confidence": min(best_score, 1.0),
            "method": "+".join(set(best_methods)),
            "alternatives": alternatives[:3],  # Top 3 alternatives
            "rules_applied": list(set(all_rules))
        }
    
    def _map_filing_type_to_category(self, filing_type) -> DocumentCategory:
        """Map filing analyzer filing type to document category."""
        # This would map from filing_analyzer.FilingType to DocumentCategory
        # For now, return a reasonable default
        filing_str = str(filing_type).lower()
        
        if "complaint" in filing_str:
            return DocumentCategory.COMPLAINT
        elif "motion" in filing_str:
            return DocumentCategory.MOTION
        elif "brief" in filing_str:
            return DocumentCategory.BRIEF
        elif "contract" in filing_str:
            return DocumentCategory.CONTRACT
        elif "discovery" in filing_str:
            return DocumentCategory.DISCOVERY
        else:
            return DocumentCategory.OTHER
    
    def _extract_key_terms(self, content: str, category: DocumentCategory) -> List[str]:
        """Extract key terms relevant to the document category."""
        key_terms = []
        content_lower = content.lower()
        
        # Category-specific term extraction
        category_terms = self.category_keywords.get(category, [])
        for term in category_terms:
            if term.lower() in content_lower:
                key_terms.append(term)
        
        # Legal-specific terms
        legal_terms = [
            "jurisdiction", "venue", "statute of limitations", "due process",
            "burden of proof", "prima facie", "res judicata", "collateral estoppel",
            "injunctive relief", "monetary damages", "attorney fees", "costs"
        ]
        
        for term in legal_terms:
            if term.lower() in content_lower:
                key_terms.append(term)
        
        return list(set(key_terms[:20]))  # Return unique terms, max 20
    
    def _extract_legal_entities(self, content: str) -> List[str]:
        """Extract legal entities (companies, people, organizations)."""
        entities = []
        
        # Simple patterns for common legal entity types
        patterns = [
            r'([A-Z][a-zA-Z\s&]+(?:Inc\.|LLC|Corp\.|Corporation|Company|Co\.))',
            r'([A-Z][a-zA-Z\s]+v\.?\s+[A-Z][a-zA-Z\s&]+)',  # Case names
            r'(United States|State of [A-Z][a-z]+|City of [A-Z][a-z]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            entities.extend(matches)
        
        return list(set(entities[:10]))  # Return unique entities, max 10
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract important dates from content."""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'[A-Za-z]+ \d{1,2}, \d{4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            dates.extend(matches)
        
        return list(set(dates[:10]))  # Return unique dates, max 10
    
    def _determine_subcategories(self, category: DocumentCategory, content: str) -> List[str]:
        """Determine subcategories based on primary category and content."""
        subcategories = []
        content_lower = content.lower()
        
        if category == DocumentCategory.MOTION:
            motion_types = {
                "motion to dismiss": ["dismiss", "12(b)(6)", "failure to state"],
                "summary judgment": ["summary judgment", "undisputed facts"],
                "preliminary injunction": ["preliminary injunction", "irreparable harm"],
                "discovery motion": ["compel discovery", "protective order"]
            }
            
            for subcat, keywords in motion_types.items():
                if any(keyword in content_lower for keyword in keywords):
                    subcategories.append(subcat)
        
        elif category == DocumentCategory.CONTRACT:
            contract_types = {
                "employment": ["employment", "employee", "employer"],
                "service": ["services", "perform", "deliverables"],
                "licensing": ["license", "licensed", "licensor"],
                "purchase": ["purchase", "sale", "buy", "sell"]
            }
            
            for subcat, keywords in contract_types.items():
                if any(keyword in content_lower for keyword in keywords):
                    subcategories.append(subcat)
        
        return subcategories
    
    def _generate_tags(self, 
                      category: DocumentCategory,
                      content: str,
                      metadata: DocumentMetadata) -> List[str]:
        """Generate suggested tags for the document."""
        tags = []
        
        # Add category-based tags
        tags.append(category.value)
        
        # Add source-based tags
        tags.append(metadata.download_source.value)
        
        # Add content-based tags
        content_lower = content.lower()
        
        if "urgent" in content_lower or "emergency" in content_lower:
            tags.append("urgent")
        
        if "confidential" in content_lower:
            tags.append("confidential")
        
        if "settlement" in content_lower:
            tags.append("settlement")
        
        if "class action" in content_lower:
            tags.append("class-action")
        
        if metadata.case_number:
            tags.append(f"case-{metadata.case_number}")
        
        return list(set(tags[:10]))  # Return unique tags, max 10
    
    async def categorize_batch(self, 
                             documents: List[Tuple[DocumentMetadata, Optional[str]]],
                             progress_callback: Optional[callable] = None) -> List[CategoryResult]:
        """Categorize multiple documents concurrently."""
        self.logger.info(f"Starting batch categorization of {len(documents)} documents")
        
        # Create categorization tasks
        tasks = [
            self.categorize_document(metadata, content)
            for metadata, content in documents
        ]
        
        # Execute categorization with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            
            if progress_callback:
                await progress_callback(
                    result.document_id, 
                    "categorized", 
                    {"category": result.primary_category.value, "confidence": result.confidence.value}
                )
        
        successful = sum(1 for r in results if r.primary_category != DocumentCategory.UNKNOWN)
        self.logger.info(f"Batch categorization completed: {successful}/{len(documents)} successful")
        
        return results