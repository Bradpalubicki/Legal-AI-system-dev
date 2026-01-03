"""
Intelligent document categorization system for legal documents.
Provides AI-powered classification, tagging, and metadata extraction.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from eyecite import get_citations
from eyecite.models import FullCaseCitation, ShortformCitation, SupraCitation

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Legal document types for classification."""
    CONTRACT = "contract"
    MOTION = "motion"
    BRIEF = "brief"
    COMPLAINT = "complaint"
    ANSWER = "answer"
    DISCOVERY = "discovery"
    DEPOSITION = "deposition"
    EXHIBIT = "exhibit"
    CORRESPONDENCE = "correspondence"
    COURT_ORDER = "court_order"
    JUDGMENT = "judgment"
    PLEADING = "pleading"
    MEMORANDUM = "memorandum"
    AFFIDAVIT = "affidavit"
    SUBPOENA = "subpoena"
    SETTLEMENT = "settlement"
    PATENT = "patent"
    TRADEMARK = "trademark"
    COPYRIGHT = "copyright"
    REGULATORY = "regulatory"
    UNKNOWN = "unknown"


class DocumentCategory(Enum):
    """High-level document categories."""
    LITIGATION = "litigation"
    TRANSACTIONAL = "transactional"
    REGULATORY = "regulatory"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CORPORATE = "corporate"
    REAL_ESTATE = "real_estate"
    EMPLOYMENT = "employment"
    FAMILY_LAW = "family_law"
    CRIMINAL = "criminal"
    ADMINISTRATIVE = "administrative"


class PracticeArea(Enum):
    """Legal practice areas."""
    CIVIL_LITIGATION = "civil_litigation"
    COMMERCIAL_LAW = "commercial_law"
    CONTRACT_LAW = "contract_law"
    CORPORATE_LAW = "corporate_law"
    EMPLOYMENT_LAW = "employment_law"
    FAMILY_LAW = "family_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    REAL_ESTATE = "real_estate"
    TAX_LAW = "tax_law"
    SECURITIES_LAW = "securities_law"
    BANKRUPTCY = "bankruptcy"
    IMMIGRATION = "immigration"
    CRIMINAL_LAW = "criminal_law"
    ENVIRONMENTAL_LAW = "environmental_law"
    HEALTHCARE_LAW = "healthcare_law"


class Urgency(Enum):
    """Document urgency levels."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"         # Action required within 24 hours
    MEDIUM = "medium"     # Action required within week
    LOW = "low"          # No immediate action required
    ARCHIVE = "archive"   # Historical/reference only


@dataclass
class DocumentMetadata:
    """Extracted document metadata."""
    document_type: DocumentType
    category: DocumentCategory
    practice_area: PracticeArea
    urgency: Urgency
    confidence_score: float
    key_entities: List[str]
    important_dates: List[datetime]
    citations: List[str]
    parties: List[str]
    jurisdiction: Optional[str]
    court: Optional[str]
    case_number: Optional[str]
    subject_matter: List[str]
    tags: List[str]
    extracted_amounts: List[str]
    deadlines: List[datetime]
    language: str
    page_count: int
    word_count: int
    processing_timestamp: datetime


@dataclass
class ClassificationResult:
    """Document classification result."""
    metadata: DocumentMetadata
    summary: str
    key_points: List[str]
    risk_factors: List[str]
    action_items: List[str]
    related_documents: List[str]
    confidence_breakdown: Dict[str, float]


class DocumentCategorizer:
    """Intelligent document categorization and analysis system."""
    
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased"):
        """Initialize the document categorizer.
        
        Args:
            model_name: Hugging Face model name for legal text classification
        """
        self.model_name = model_name
        self.nlp = None
        self.classifier = None
        self.tokenizer = None
        self.model = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        # Legal document patterns
        self.document_patterns = {
            DocumentType.CONTRACT: [
                r'\bagreement\b', r'\bcontract\b', r'\bparties\b', r'\bwhereas\b',
                r'\bconsideration\b', r'\bterms and conditions\b', r'\bexecuted\b'
            ],
            DocumentType.MOTION: [
                r'\bmotion\b', r'\bmoves\b', r'\bprays\b', r'\brequests\b',
                r'\brelief\b', r'\bgood cause\b', r'\brespectfully\b'
            ],
            DocumentType.BRIEF: [
                r'\bbrief\b', r'\bargument\b', r'\bstatement of facts\b',
                r'\bconclusion\b', r'\bauthority\b', r'\bprecedent\b'
            ],
            DocumentType.COMPLAINT: [
                r'\bcomplaint\b', r'\bplaintiff\b', r'\bdefendant\b', r'\bcause of action\b',
                r'\balleges\b', r'\bjurisdiction\b', r'\bvenue\b'
            ],
            DocumentType.COURT_ORDER: [
                r'\border\b', r'\bdecree\b', r'\bit is ordered\b', r'\bit is adjudged\b',
                r'\bhonore?able\b', r'\bjudge\b', r'\bcourt\b'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'case_number': r'\b(?:case|civil|criminal)\s*(?:no\.?|number)\s*[:\-]?\s*([A-Z0-9\-:]+)\b',
            'court': r'\b(?:court|tribunal)\s+(?:of\s+)?([A-Z][A-Za-z\s]+(?:court|tribunal))\b',
            'amount': r'\$[\d,]+(?:\.\d{2})?',
            'date': r'\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b',
            'party': r'\b([A-Z][A-Za-z\s]+(?:Corp|Inc|LLC|Ltd|Co)\b)',
            'jurisdiction': r'\b(?:state of|commonwealth of)\s+([A-Z][a-z]+)\b'
        }
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models and classifiers."""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model")
            
            # Load legal BERT model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Create classification pipeline
            self.classifier = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info(f"Initialized legal BERT model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            # Fallback to basic classification
            self.nlp = None
            self.classifier = None
    
    def categorize_document(self, text: str, filename: str = "") -> ClassificationResult:
        """Categorize a legal document and extract metadata.
        
        Args:
            text: Document text content
            filename: Optional filename for additional context
            
        Returns:
            Classification result with metadata and analysis
        """
        logger.info(f"Categorizing document: {filename}")
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Extract basic metadata
        word_count = len(cleaned_text.split())
        page_count = max(1, word_count // 250)  # Estimate pages
        
        # Classify document type
        document_type = self._classify_document_type(cleaned_text)
        
        # Determine category and practice area
        category = self._determine_category(document_type, cleaned_text)
        practice_area = self._determine_practice_area(document_type, cleaned_text)
        
        # Assess urgency
        urgency = self._assess_urgency(cleaned_text, document_type)
        
        # Extract entities and metadata
        entities = self._extract_entities(cleaned_text)
        dates = self._extract_dates(cleaned_text)
        citations = self._extract_citations(cleaned_text)
        parties = self._extract_parties(cleaned_text)
        amounts = self._extract_amounts(cleaned_text)
        
        # Generate tags and subject matter
        tags = self._generate_tags(cleaned_text, document_type)
        subject_matter = self._extract_subject_matter(cleaned_text)
        
        # Identify deadlines and action items
        deadlines = self._identify_deadlines(cleaned_text, dates)
        action_items = self._identify_action_items(cleaned_text)
        
        # Generate summary and key points
        summary = self._generate_summary(cleaned_text, document_type)
        key_points = self._extract_key_points(cleaned_text)
        risk_factors = self._identify_risk_factors(cleaned_text, document_type)
        
        # Calculate confidence scores
        confidence_breakdown = self._calculate_confidence_scores(
            cleaned_text, document_type, category, practice_area
        )
        
        # Create metadata object
        metadata = DocumentMetadata(
            document_type=document_type,
            category=category,
            practice_area=practice_area,
            urgency=urgency,
            confidence_score=confidence_breakdown['overall'],
            key_entities=entities,
            important_dates=dates,
            citations=citations,
            parties=parties,
            jurisdiction=entities.get('jurisdiction'),
            court=entities.get('court'),
            case_number=entities.get('case_number'),
            subject_matter=subject_matter,
            tags=tags,
            extracted_amounts=amounts,
            deadlines=deadlines,
            language='en',  # TODO: Add language detection
            page_count=page_count,
            word_count=word_count,
            processing_timestamp=datetime.utcnow()
        )
        
        return ClassificationResult(
            metadata=metadata,
            summary=summary,
            key_points=key_points,
            risk_factors=risk_factors,
            action_items=action_items,
            related_documents=[],  # TODO: Implement similarity matching
            confidence_breakdown=confidence_breakdown
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('–', '-').replace('—', '-')
        
        return text.strip()
    
    def _classify_document_type(self, text: str) -> DocumentType:
        """Classify the document type based on content patterns."""
        text_lower = text.lower()
        scores = {}
        
        # Pattern-based classification
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches
            scores[doc_type] = score
        
        # Use ML classifier if available
        if self.classifier:
            try:
                # Truncate text for BERT model
                truncated_text = text[:512]
                predictions = self.classifier(truncated_text)
                
                # Combine with pattern scores
                for pred in predictions:
                    doc_type = DocumentType.UNKNOWN  # Map label to DocumentType
                    if doc_type in scores:
                        scores[doc_type] += pred['score'] * 10
            except Exception as e:
                logger.warning(f"ML classification failed: {e}")
        
        # Return highest scoring type
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return DocumentType.UNKNOWN
    
    def _determine_category(self, document_type: DocumentType, text: str) -> DocumentCategory:
        """Determine high-level document category."""
        litigation_types = {DocumentType.MOTION, DocumentType.BRIEF, DocumentType.COMPLAINT, 
                          DocumentType.ANSWER, DocumentType.DISCOVERY, DocumentType.DEPOSITION}
        
        transactional_types = {DocumentType.CONTRACT, DocumentType.SETTLEMENT}
        
        ip_types = {DocumentType.PATENT, DocumentType.TRADEMARK, DocumentType.COPYRIGHT}
        
        if document_type in litigation_types:
            return DocumentCategory.LITIGATION
        elif document_type in transactional_types:
            return DocumentCategory.TRANSACTIONAL
        elif document_type in ip_types:
            return DocumentCategory.INTELLECTUAL_PROPERTY
        elif 'regulatory' in text.lower() or 'regulation' in text.lower():
            return DocumentCategory.REGULATORY
        elif 'employment' in text.lower() or 'employee' in text.lower():
            return DocumentCategory.EMPLOYMENT
        elif 'real estate' in text.lower() or 'property' in text.lower():
            return DocumentCategory.REAL_ESTATE
        else:
            return DocumentCategory.LITIGATION  # Default
    
    def _determine_practice_area(self, document_type: DocumentType, text: str) -> PracticeArea:
        """Determine legal practice area."""
        text_lower = text.lower()
        
        # Pattern matching for practice areas
        if any(term in text_lower for term in ['employment', 'employee', 'workplace', 'labor']):
            return PracticeArea.EMPLOYMENT_LAW
        elif any(term in text_lower for term in ['patent', 'trademark', 'copyright', 'ip']):
            return PracticeArea.INTELLECTUAL_PROPERTY
        elif any(term in text_lower for term in ['real estate', 'property', 'lease', 'mortgage']):
            return PracticeArea.REAL_ESTATE
        elif any(term in text_lower for term in ['family', 'divorce', 'custody', 'marriage']):
            return PracticeArea.FAMILY_LAW
        elif any(term in text_lower for term in ['criminal', 'prosecution', 'defendant']):
            return PracticeArea.CRIMINAL_LAW
        elif any(term in text_lower for term in ['corporate', 'corporation', 'merger', 'acquisition']):
            return PracticeArea.CORPORATE_LAW
        elif any(term in text_lower for term in ['contract', 'agreement', 'breach']):
            return PracticeArea.CONTRACT_LAW
        elif any(term in text_lower for term in ['securities', 'stock', 'investment']):
            return PracticeArea.SECURITIES_LAW
        elif any(term in text_lower for term in ['bankruptcy', 'insolvency', 'debtor']):
            return PracticeArea.BANKRUPTCY
        else:
            return PracticeArea.CIVIL_LITIGATION  # Default
    
    def _assess_urgency(self, text: str, document_type: DocumentType) -> Urgency:
        """Assess document urgency based on content."""
        text_lower = text.lower()
        
        # Critical indicators
        critical_terms = ['emergency', 'urgent', 'immediate', 'ex parte', 'restraining order', 
                         'injunction', 'deadline today', 'due today']
        
        high_terms = ['motion', 'response due', 'hearing', 'trial', 'deadline', 'due date']
        
        if any(term in text_lower for term in critical_terms):
            return Urgency.CRITICAL
        elif any(term in text_lower for term in high_terms):
            return Urgency.HIGH
        elif document_type in {DocumentType.MOTION, DocumentType.BRIEF, DocumentType.DISCOVERY}:
            return Urgency.MEDIUM
        else:
            return Urgency.LOW
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract legal entities from text."""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches
        
        # Use spaCy for additional entity extraction
        if self.nlp:
            try:
                doc = self.nlp(text[:1000000])  # Limit text size
                entities['people'] = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
                entities['organizations'] = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
                entities['locations'] = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
            except Exception as e:
                logger.warning(f"spaCy entity extraction failed: {e}")
        
        return entities
    
    def _extract_dates(self, text: str) -> List[datetime]:
        """Extract important dates from text."""
        dates = []
        date_patterns = [
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
            r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Handle different date formats
                        if pattern.endswith(r'(\d{4})\b'):  # Month name format
                            month_name, day, year = groups
                            month_num = {
                                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                                'september': 9, 'october': 10, 'november': 11, 'december': 12
                            }.get(month_name.lower())
                            if month_num:
                                date = datetime(int(year), month_num, int(day))
                                dates.append(date)
                        else:
                            # Handle numeric formats
                            if len(groups[0]) == 4:  # YYYY-MM-DD
                                date = datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                            else:  # MM/DD/YYYY or MM-DD-YYYY
                                date = datetime(int(groups[2]), int(groups[0]), int(groups[1]))
                            dates.append(date)
                except (ValueError, TypeError):
                    continue
        
        return sorted(list(set(dates)))
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text."""
        citations = []
        try:
            found_citations = get_citations(text)
            for citation in found_citations:
                if isinstance(citation, (FullCaseCitation, ShortformCitation, SupraCitation)):
                    citations.append(str(citation))
        except Exception as e:
            logger.warning(f"Citation extraction failed: {e}")
        
        return citations
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names from legal documents."""
        parties = []
        
        # Common legal party patterns
        party_patterns = [
            r'\bplaintiff[s]?:?\s+([A-Z][A-Za-z\s,]+?)(?:\s+v\.|\s+vs\.|\n)',
            r'\bdefendant[s]?:?\s+([A-Z][A-Za-z\s,]+?)(?:\s+v\.|\s+vs\.|\n)',
            r'\b([A-Z][A-Za-z\s]+(?:Corp|Inc|LLC|Ltd|Co|LP)\.?)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+v\.|\s+vs\.)'
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, text)
            parties.extend(matches)
        
        # Clean and deduplicate
        cleaned_parties = []
        for party in parties:
            party = party.strip().rstrip(',')
            if len(party) > 2 and party not in cleaned_parties:
                cleaned_parties.append(party)
        
        return cleaned_parties[:10]  # Limit results
    
    def _extract_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts from text."""
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
        amounts = re.findall(amount_pattern, text)
        return list(set(amounts))
    
    def _generate_tags(self, text: str, document_type: DocumentType) -> List[str]:
        """Generate relevant tags for the document."""
        tags = [document_type.value]
        
        # Legal concept tags
        legal_concepts = {
            'breach of contract': r'\bbreach\s+of\s+contract\b',
            'negligence': r'\bnegligence\b',
            'damages': r'\bdamages\b',
            'injunction': r'\binjunction\b',
            'summary judgment': r'\bsummary\s+judgment\b',
            'discovery': r'\bdiscovery\b',
            'settlement': r'\bsettlement\b',
            'confidentiality': r'\bconfidential\b',
            'non-disclosure': r'\bnon.disclosure\b',
            'intellectual property': r'\bintellectual\s+property\b',
            'employment': r'\bemployment\b',
            'termination': r'\btermination\b'
        }
        
        text_lower = text.lower()
        for concept, pattern in legal_concepts.items():
            if re.search(pattern, text_lower):
                tags.append(concept)
        
        return tags[:10]  # Limit tags
    
    def _extract_subject_matter(self, text: str) -> List[str]:
        """Extract key subject matter topics."""
        # Use TF-IDF to find important terms
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            
            # Get top scoring terms
            top_indices = tfidf_scores.argsort()[-20:][::-1]
            subject_matter = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0.1]
            
            return subject_matter[:10]
        except Exception as e:
            logger.warning(f"Subject matter extraction failed: {e}")
            return []
    
    def _identify_deadlines(self, text: str, dates: List[datetime]) -> List[datetime]:
        """Identify deadline dates from extracted dates."""
        deadline_keywords = ['due', 'deadline', 'expires', 'expiration', 'response', 'reply']
        deadline_dates = []
        
        for date in dates:
            # Look for deadline keywords near the date
            date_str = date.strftime('%m/%d/%Y')
            context_start = max(0, text.find(date_str) - 100)
            context_end = min(len(text), text.find(date_str) + 100)
            context = text[context_start:context_end].lower()
            
            if any(keyword in context for keyword in deadline_keywords):
                deadline_dates.append(date)
        
        return deadline_dates
    
    def _identify_action_items(self, text: str) -> List[str]:
        """Identify required actions from document text."""
        action_items = []
        
        # Pattern for action requirements
        action_patterns = [
            r'(?:must|shall|required to|need to|should)\s+([^.!?]+[.!?])',
            r'(?:deadline|due date|response|reply)\s+[^.!?]*([^.!?]+[.!?])',
            r'(?:motion|request|application)\s+(?:for|to)\s+([^.!?]+[.!?])'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            action_items.extend(matches)
        
        return action_items[:5]  # Limit results
    
    def _generate_summary(self, text: str, document_type: DocumentType) -> str:
        """Generate document summary."""
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', text)
        
        # Score sentences based on key legal terms
        key_terms = ['court', 'plaintiff', 'defendant', 'motion', 'contract', 'agreement', 
                    'damages', 'relief', 'judgment', 'order']
        
        scored_sentences = []
        for sentence in sentences[:50]:  # Limit to first 50 sentences
            sentence = sentence.strip()
            if len(sentence) > 20:
                score = sum(1 for term in key_terms if term in sentence.lower())
                scored_sentences.append((score, sentence))
        
        # Get top 3 sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[0], reverse=True)[:3]
        summary = ' '.join([sentence[1] for sentence in top_sentences])
        
        return summary[:500] + '...' if len(summary) > 500 else summary
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from document."""
        # Look for numbered or bulleted lists
        key_points = []
        
        list_patterns = [
            r'^\s*[\d]+\.\s+([^.!?]+[.!?])',
            r'^\s*[•\-\*]\s+([^.!?]+[.!?])',
            r'(?:WHEREAS|THEREFORE|NOW THEREFORE)[,:\s]+([^.!?]+[.!?])'
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            key_points.extend(matches)
        
        return key_points[:10]  # Limit results
    
    def _identify_risk_factors(self, text: str, document_type: DocumentType) -> List[str]:
        """Identify potential risk factors in the document."""
        risk_factors = []
        
        risk_keywords = {
            'liability': r'\bliabilit[yi]\b',
            'penalty': r'\bpenalt[yi]\b',
            'breach': r'\bbreach\b',
            'default': r'\bdefault\b',
            'termination': r'\btermination\b',
            'damages': r'\bdamages\b',
            'indemnification': r'\bindemnif\b',
            'limitation': r'\blimitation\b',
            'confidentiality': r'\bconfidential\b'
        }
        
        text_lower = text.lower()
        for risk_type, pattern in risk_keywords.items():
            if re.search(pattern, text_lower):
                risk_factors.append(f"Document contains {risk_type} provisions")
        
        return risk_factors
    
    def _calculate_confidence_scores(self, text: str, document_type: DocumentType, 
                                   category: DocumentCategory, practice_area: PracticeArea) -> Dict[str, float]:
        """Calculate confidence scores for classifications."""
        scores = {
            'document_type': 0.8,  # Base confidence
            'category': 0.7,
            'practice_area': 0.6,
            'overall': 0.7
        }
        
        # Adjust based on pattern matches
        if document_type != DocumentType.UNKNOWN:
            type_patterns = self.document_patterns.get(document_type, [])
            pattern_matches = sum(1 for pattern in type_patterns 
                                if re.search(pattern, text.lower()))
            scores['document_type'] = min(0.95, 0.5 + (pattern_matches * 0.1))
        
        # Calculate overall confidence
        scores['overall'] = (scores['document_type'] + scores['category'] + scores['practice_area']) / 3
        
        return scores