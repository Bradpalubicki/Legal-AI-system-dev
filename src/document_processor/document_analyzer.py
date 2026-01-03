"""
Advanced document analysis system with AI-powered content extraction, categorization, and legal analysis.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import json
import asyncio
from pathlib import Path
import hashlib

from ..shared.utils.ai_client import AIClient
from ..shared.database.models import Document, Case
from .upload_manager import FileInfo, FileType


class DocumentCategory(Enum):
    """Document categories for legal documents."""
    PLEADINGS = "pleadings"
    MOTIONS = "motions"
    CONTRACTS = "contracts"
    CORRESPONDENCE = "correspondence"
    DISCOVERY = "discovery"
    EVIDENCE = "evidence"
    EXPERT_REPORTS = "expert_reports"
    MEDICAL_RECORDS = "medical_records"
    FINANCIAL_RECORDS = "financial_records"
    DEPOSITION_TRANSCRIPTS = "deposition_transcripts"
    COURT_ORDERS = "court_orders"
    JUDGMENTS = "judgments"
    SETTLEMENTS = "settlements"
    INSURANCE_DOCUMENTS = "insurance_documents"
    REGULATORY_FILINGS = "regulatory_filings"
    PATENTS_IP = "patents_ip"
    EMPLOYMENT_DOCS = "employment_docs"
    REAL_ESTATE = "real_estate"
    CORPORATE_DOCS = "corporate_docs"
    COMPLIANCE = "compliance"
    LITIGATION_SUPPORT = "litigation_support"
    RESEARCH_MEMOS = "research_memos"
    CASE_SUMMARIES = "case_summaries"
    ADMINISTRATIVE = "administrative"
    UNKNOWN = "unknown"


class AnalysisType(Enum):
    """Types of document analysis."""
    CONTENT_EXTRACTION = "content_extraction"
    CATEGORIZATION = "categorization"
    ENTITY_RECOGNITION = "entity_recognition"
    KEY_TERMS = "key_terms"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PRIVILEGE_REVIEW = "privilege_review"
    PII_DETECTION = "pii_detection"
    CONFIDENTIALITY = "confidentiality"
    LEGAL_CONCEPTS = "legal_concepts"
    CITATION_EXTRACTION = "citation_extraction"
    DATE_EXTRACTION = "date_extraction"
    CURRENCY_AMOUNTS = "currency_amounts"
    RISK_ASSESSMENT = "risk_assessment"
    SUMMARY_GENERATION = "summary_generation"


class ConfidentialityLevel(Enum):
    """Confidentiality levels for documents."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"
    ATTORNEY_CLIENT_PRIVILEGED = "attorney_client_privileged"
    ATTORNEY_WORK_PRODUCT = "attorney_work_product"


@dataclass
class ExtractedEntity:
    """Extracted entity from document."""
    entity_type: str
    text: str
    confidence: float
    start_position: int
    end_position: int
    context: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LegalConcept:
    """Identified legal concept."""
    concept_type: str
    concept_name: str
    confidence: float
    relevance_score: float
    text_references: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentAnalysis:
    """Complete document analysis results."""
    file_id: str
    analysis_timestamp: datetime
    
    # Content analysis
    extracted_text: str
    word_count: int
    character_count: int
    page_count: Optional[int]
    
    # Categorization
    primary_category: DocumentCategory
    secondary_categories: List[DocumentCategory]
    category_confidence: float
    
    # Entities
    entities: List[ExtractedEntity]
    key_terms: List[str]
    
    # Legal analysis
    legal_concepts: List[LegalConcept]
    citations: List[Dict[str, Any]]
    important_dates: List[Dict[str, Any]]
    currency_amounts: List[Dict[str, Any]]
    
    # Risk and privilege
    confidentiality_level: ConfidentialityLevel
    privilege_risk: float
    pii_detected: List[Dict[str, Any]]
    risk_factors: List[str]
    
    # Summary
    executive_summary: str
    key_points: List[str]
    sentiment_score: Optional[float]
    
    # Quality metrics
    analysis_confidence: float
    processing_time: float
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentAnalyzer:
    """Advanced document analysis system with AI-powered capabilities."""
    
    def __init__(self):
        self.ai_client = AIClient()
        
        # Legal entity patterns
        self.entity_patterns = {
            'person_names': [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
                r'\b[A-Z][a-z]+, [A-Z][a-z]+\b'
            ],
            'company_names': [
                r'\b[A-Z][a-zA-Z\s]+ (?:Inc|Corp|LLC|Ltd|Co|Company|Corporation|Partnership|LLP|LP)\b',
                r'\b[A-Z][a-zA-Z\s]+ (?:Inc\.|Corp\.|LLC|Ltd\.|Co\.|Company|Corporation)\b'
            ],
            'addresses': [
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Court|Ct|Place|Pl)',
                r'\b[A-Z][a-zA-Z\s]+,\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?\b'
            ],
            'phone_numbers': [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                r'\(\d{3}\)\s*\d{3}[-.]?\d{4}\b'
            ],
            'email_addresses': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'ssn': [
                r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{9}\b'
            ],
            'case_numbers': [
                r'\bCase\s+No\.?\s*[A-Z0-9-]+\b',
                r'\b\d{2,4}-[A-Z]{1,3}-\d{2,6}\b'
            ]
        }
        
        # Legal concept patterns
        self.legal_concept_patterns = {
            'contract_terms': [
                'force majeure', 'indemnification', 'liquidated damages',
                'breach of contract', 'consideration', 'covenant',
                'warranty', 'representation', 'termination clause'
            ],
            'tort_concepts': [
                'negligence', 'strict liability', 'intentional tort',
                'defamation', 'invasion of privacy', 'emotional distress'
            ],
            'procedure_concepts': [
                'motion to dismiss', 'summary judgment', 'discovery',
                'deposition', 'interrogatories', 'requests for production'
            ],
            'evidence_concepts': [
                'hearsay', 'best evidence rule', 'authentication',
                'privilege', 'relevance', 'probative value'
            ]
        }
        
        # Citation patterns
        self.citation_patterns = {
            'case_citations': [
                r'\b\d+\s+[A-Z]\w*\s+\d+\b',  # 123 F.3d 456
                r'\b\d+\s+U\.S\.\s+\d+\b',    # 123 U.S. 456
                r'\b\d+\s+S\.\s*Ct\.\s+\d+\b'  # 123 S. Ct. 456
            ],
            'statute_citations': [
                r'\b\d+\s+U\.S\.C\.\s*§?\s*\d+\b',  # 42 U.S.C. § 1983
                r'\b\d+\s+C\.F\.R\.\s*§?\s*\d+\b'   # 29 C.F.R. § 1630
            ]
        }

    async def analyze_document(
        self, 
        file_info: FileInfo, 
        case_context: Optional[Case] = None,
        analysis_types: List[AnalysisType] = None
    ) -> DocumentAnalysis:
        """Perform comprehensive document analysis."""
        try:
            start_time = datetime.utcnow()
            
            # Default to all analysis types if none specified
            if analysis_types is None:
                analysis_types = list(AnalysisType)
            
            print(f"Starting analysis for: {file_info.original_filename}")
            
            # Extract text content
            extracted_text = await self._extract_text_content(file_info)
            
            # Initialize analysis object
            analysis = DocumentAnalysis(
                file_id=file_info.file_id,
                analysis_timestamp=start_time,
                extracted_text=extracted_text,
                word_count=len(extracted_text.split()) if extracted_text else 0,
                character_count=len(extracted_text) if extracted_text else 0,
                page_count=file_info.metadata.get('page_count'),
                entities=[],
                key_terms=[],
                legal_concepts=[],
                citations=[],
                important_dates=[],
                currency_amounts=[],
                pii_detected=[],
                risk_factors=[],
                primary_category=DocumentCategory.UNKNOWN,
                secondary_categories=[],
                category_confidence=0.0,
                confidentiality_level=ConfidentialityLevel.INTERNAL,
                privilege_risk=0.0,
                executive_summary="",
                key_points=[],
                sentiment_score=None,
                analysis_confidence=0.0,
                processing_time=0.0,
                metadata={}
            )
            
            # Perform requested analyses
            analysis_tasks = []
            
            if AnalysisType.CONTENT_EXTRACTION in analysis_types:
                analysis_tasks.append(self._analyze_content_structure(analysis, extracted_text))
            
            if AnalysisType.CATEGORIZATION in analysis_types:
                analysis_tasks.append(self._categorize_document(analysis, extracted_text, case_context))
            
            if AnalysisType.ENTITY_RECOGNITION in analysis_types:
                analysis_tasks.append(self._extract_entities(analysis, extracted_text))
            
            if AnalysisType.KEY_TERMS in analysis_types:
                analysis_tasks.append(self._extract_key_terms(analysis, extracted_text))
            
            if AnalysisType.LEGAL_CONCEPTS in analysis_types:
                analysis_tasks.append(self._identify_legal_concepts(analysis, extracted_text))
            
            if AnalysisType.CITATION_EXTRACTION in analysis_types:
                analysis_tasks.append(self._extract_citations(analysis, extracted_text))
            
            if AnalysisType.DATE_EXTRACTION in analysis_types:
                analysis_tasks.append(self._extract_dates(analysis, extracted_text))
            
            if AnalysisType.CURRENCY_AMOUNTS in analysis_types:
                analysis_tasks.append(self._extract_currency_amounts(analysis, extracted_text))
            
            if AnalysisType.PII_DETECTION in analysis_types:
                analysis_tasks.append(self._detect_pii(analysis, extracted_text))
            
            if AnalysisType.PRIVILEGE_REVIEW in analysis_types:
                analysis_tasks.append(self._assess_privilege_risk(analysis, extracted_text))
            
            if AnalysisType.CONFIDENTIALITY in analysis_types:
                analysis_tasks.append(self._assess_confidentiality(analysis, extracted_text))
            
            if AnalysisType.RISK_ASSESSMENT in analysis_types:
                analysis_tasks.append(self._assess_risks(analysis, extracted_text))
            
            if AnalysisType.SENTIMENT_ANALYSIS in analysis_types:
                analysis_tasks.append(self._analyze_sentiment(analysis, extracted_text))
            
            if AnalysisType.SUMMARY_GENERATION in analysis_types:
                analysis_tasks.append(self._generate_summary(analysis, extracted_text, case_context))
            
            # Execute all analyses in parallel
            await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            analysis.processing_time = (end_time - start_time).total_seconds()
            
            # Calculate overall confidence
            analysis.analysis_confidence = await self._calculate_overall_confidence(analysis)
            
            print(f"Analysis completed for: {file_info.original_filename}")
            
            return analysis
            
        except Exception as e:
            print(f"Error in document analysis: {e}")
            raise

    async def _extract_text_content(self, file_info: FileInfo) -> str:
        """Extract text content from various file types."""
        try:
            if not file_info.final_path:
                return ""
            
            text_content = ""
            
            if file_info.file_type == FileType.TXT:
                with open(file_info.final_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()
            
            elif file_info.file_type == FileType.PDF:
                text_content = await self._extract_pdf_text(file_info.final_path)
            
            elif file_info.file_type in [FileType.DOCX, FileType.DOC]:
                text_content = await self._extract_office_text(file_info.final_path)
            
            elif file_info.file_type == FileType.RTF:
                text_content = await self._extract_rtf_text(file_info.final_path)
            
            elif file_info.file_type == FileType.HTML:
                text_content = await self._extract_html_text(file_info.final_path)
            
            elif file_info.file_type in [FileType.EML, FileType.MSG]:
                text_content = await self._extract_email_text(file_info.final_path)
            
            # Use OCR text if available
            elif 'extracted_text' in file_info.metadata:
                text_content = file_info.metadata['extracted_text']
            
            return text_content.strip()
            
        except Exception as e:
            print(f"Error extracting text content: {e}")
            return ""

    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            # Placeholder for PDF text extraction
            # In production, would use PyPDF2, pdfplumber, or similar
            return "Extracted PDF text would be here"
            
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""

    async def _extract_office_text(self, file_path: str) -> str:
        """Extract text from Office documents."""
        try:
            # Placeholder for Office document text extraction
            # In production, would use python-docx, python-pptx, etc.
            return "Extracted Office document text would be here"
            
        except Exception as e:
            print(f"Error extracting Office text: {e}")
            return ""

    async def _extract_rtf_text(self, file_path: str) -> str:
        """Extract text from RTF file."""
        try:
            # Placeholder for RTF text extraction
            return "Extracted RTF text would be here"
            
        except Exception as e:
            print(f"Error extracting RTF text: {e}")
            return ""

    async def _extract_html_text(self, file_path: str) -> str:
        """Extract text from HTML file."""
        try:
            # Placeholder for HTML text extraction
            # In production, would use BeautifulSoup
            return "Extracted HTML text would be here"
            
        except Exception as e:
            print(f"Error extracting HTML text: {e}")
            return ""

    async def _extract_email_text(self, file_path: str) -> str:
        """Extract text from email files."""
        try:
            # Placeholder for email text extraction
            return "Extracted email text would be here"
            
        except Exception as e:
            print(f"Error extracting email text: {e}")
            return ""

    async def _analyze_content_structure(self, analysis: DocumentAnalysis, text: str):
        """Analyze document content structure."""
        try:
            # Count paragraphs, sentences, etc.
            paragraphs = text.split('\n\n')
            sentences = re.split(r'[.!?]+', text)
            
            analysis.metadata.update({
                'paragraph_count': len([p for p in paragraphs if p.strip()]),
                'sentence_count': len([s for s in sentences if s.strip()]),
                'average_sentence_length': analysis.word_count / len([s for s in sentences if s.strip()]) if sentences else 0,
                'content_structure_analyzed': True
            })
            
        except Exception as e:
            print(f"Error analyzing content structure: {e}")

    async def _categorize_document(
        self, 
        analysis: DocumentAnalysis, 
        text: str, 
        case_context: Optional[Case]
    ):
        """Categorize document using AI and rule-based approaches."""
        try:
            # Rule-based categorization
            rule_based_category = self._rule_based_categorization(text)
            
            # AI-based categorization
            ai_category, confidence = await self._ai_categorization(text, case_context)
            
            # Combine results
            if confidence > 0.8:
                analysis.primary_category = ai_category
                analysis.category_confidence = confidence
            else:
                analysis.primary_category = rule_based_category
                analysis.category_confidence = 0.7
            
            # Add secondary categories
            analysis.secondary_categories = self._identify_secondary_categories(text)
            
        except Exception as e:
            print(f"Error categorizing document: {e}")
            analysis.primary_category = DocumentCategory.UNKNOWN
            analysis.category_confidence = 0.0

    def _rule_based_categorization(self, text: str) -> DocumentCategory:
        """Perform rule-based document categorization."""
        text_lower = text.lower()
        
        # Contract indicators
        if any(term in text_lower for term in [
            'agreement', 'contract', 'whereas', 'party of the first part',
            'consideration', 'covenant', 'terms and conditions'
        ]):
            return DocumentCategory.CONTRACTS
        
        # Motion indicators
        elif any(term in text_lower for term in [
            'motion for', 'moves the court', 'respectfully moves',
            'motion to dismiss', 'summary judgment'
        ]):
            return DocumentCategory.MOTIONS
        
        # Discovery indicators
        elif any(term in text_lower for term in [
            'interrogatories', 'requests for production', 'deposition',
            'request for admissions', 'discovery'
        ]):
            return DocumentCategory.DISCOVERY
        
        # Correspondence indicators
        elif any(term in text_lower for term in [
            'dear', 'sincerely', 'regards', 'cc:', 'subject:'
        ]):
            return DocumentCategory.CORRESPONDENCE
        
        # Court order indicators
        elif any(term in text_lower for term in [
            'it is hereby ordered', 'the court finds', 'judgment is entered'
        ]):
            return DocumentCategory.COURT_ORDERS
        
        return DocumentCategory.UNKNOWN

    async def _ai_categorization(
        self, 
        text: str, 
        case_context: Optional[Case]
    ) -> Tuple[DocumentCategory, float]:
        """Use AI for document categorization."""
        try:
            context_info = ""
            if case_context:
                context_info = f"Case context: {case_context.case_type}, {case_context.title}"
            
            prompt = f"""
            Analyze this legal document and categorize it. Consider the content, language, and structure.
            
            {context_info}
            
            Document text (first 2000 characters):
            {text[:2000]}...
            
            Available categories:
            - pleadings: Complaints, answers, motions to dismiss
            - motions: Various motions filed with the court
            - contracts: Agreements, contracts, MOUs
            - correspondence: Letters, emails, communications
            - discovery: Interrogatories, depositions, document requests
            - evidence: Exhibits, evidence documents
            - court_orders: Orders, judgments from the court
            - expert_reports: Expert witness reports and opinions
            - medical_records: Medical documents and records
            - financial_records: Financial statements, records
            - unknown: Cannot determine category
            
            Respond with JSON format:
            {{
                "category": "category_name",
                "confidence": 0.85,
                "reasoning": "Brief explanation"
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response)
            category_name = result.get("category", "unknown")
            confidence = result.get("confidence", 0.0)
            
            # Convert to DocumentCategory enum
            try:
                category = DocumentCategory(category_name)
                return category, confidence
            except ValueError:
                return DocumentCategory.UNKNOWN, 0.0
                
        except Exception as e:
            print(f"Error in AI categorization: {e}")
            return DocumentCategory.UNKNOWN, 0.0

    def _identify_secondary_categories(self, text: str) -> List[DocumentCategory]:
        """Identify secondary document categories."""
        secondary_categories = []
        text_lower = text.lower()
        
        # Check for multiple category indicators
        if any(term in text_lower for term in ['exhibit', 'evidence']):
            secondary_categories.append(DocumentCategory.EVIDENCE)
        
        if any(term in text_lower for term in ['expert', 'opinion', 'analysis']):
            secondary_categories.append(DocumentCategory.EXPERT_REPORTS)
        
        if any(term in text_lower for term in ['medical', 'diagnosis', 'treatment']):
            secondary_categories.append(DocumentCategory.MEDICAL_RECORDS)
        
        return secondary_categories

    async def _extract_entities(self, analysis: DocumentAnalysis, text: str):
        """Extract named entities from document text."""
        try:
            entities = []
            
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entity = ExtractedEntity(
                            entity_type=entity_type,
                            text=match.group(),
                            confidence=0.8,  # Would be calculated by NER model
                            start_position=match.start(),
                            end_position=match.end(),
                            context=text[max(0, match.start()-50):match.end()+50]
                        )
                        entities.append(entity)
            
            # AI-based entity extraction for higher accuracy
            ai_entities = await self._ai_entity_extraction(text)
            entities.extend(ai_entities)
            
            analysis.entities = entities
            
        except Exception as e:
            print(f"Error extracting entities: {e}")

    async def _ai_entity_extraction(self, text: str) -> List[ExtractedEntity]:
        """Use AI for advanced entity extraction."""
        try:
            # Placeholder for AI entity extraction
            # In production, would use spaCy, Hugging Face NER, or cloud NER services
            return []
            
        except Exception as e:
            print(f"Error in AI entity extraction: {e}")
            return []

    async def _extract_key_terms(self, analysis: DocumentAnalysis, text: str):
        """Extract key terms and phrases from document."""
        try:
            # Use AI to extract key terms
            prompt = f"""
            Extract the most important legal terms, phrases, and concepts from this document text.
            Focus on legally significant terms, key phrases, and important concepts.
            
            Text (first 3000 characters):
            {text[:3000]}...
            
            Return as JSON array of terms:
            ["term1", "term2", "term3", ...]
            
            Limit to top 15 most important terms.
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.2,
                max_tokens=300
            )
            
            key_terms = json.loads(response)
            analysis.key_terms = key_terms[:15] if isinstance(key_terms, list) else []
            
        except Exception as e:
            print(f"Error extracting key terms: {e}")
            analysis.key_terms = []

    async def _identify_legal_concepts(self, analysis: DocumentAnalysis, text: str):
        """Identify legal concepts in the document."""
        try:
            concepts = []
            text_lower = text.lower()
            
            for concept_category, concept_terms in self.legal_concept_patterns.items():
                for term in concept_terms:
                    if term.lower() in text_lower:
                        # Find all occurrences
                        references = []
                        start = 0
                        while True:
                            pos = text_lower.find(term.lower(), start)
                            if pos == -1:
                                break
                            
                            # Get context around the term
                            context_start = max(0, pos - 100)
                            context_end = min(len(text), pos + len(term) + 100)
                            context = text[context_start:context_end]
                            references.append(context)
                            
                            start = pos + len(term)
                        
                        if references:
                            concept = LegalConcept(
                                concept_type=concept_category,
                                concept_name=term,
                                confidence=0.8,
                                relevance_score=len(references) / 10.0,  # Simple scoring
                                text_references=references[:5]  # Limit to 5 references
                            )
                            concepts.append(concept)
            
            analysis.legal_concepts = concepts
            
        except Exception as e:
            print(f"Error identifying legal concepts: {e}")

    async def _extract_citations(self, analysis: DocumentAnalysis, text: str):
        """Extract legal citations from document."""
        try:
            citations = []
            
            for citation_type, patterns in self.citation_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        citation = {
                            "type": citation_type,
                            "text": match.group(),
                            "position": match.span(),
                            "confidence": 0.9
                        }
                        citations.append(citation)
            
            analysis.citations = citations
            
        except Exception as e:
            print(f"Error extracting citations: {e}")

    async def _extract_dates(self, analysis: DocumentAnalysis, text: str):
        """Extract important dates from document."""
        try:
            date_patterns = [
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{1,2}-\d{1,2}-\d{4}\b',
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            ]
            
            dates = []
            for pattern in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    date_info = {
                        "text": match.group(),
                        "position": match.span(),
                        "context": text[max(0, match.start()-50):match.end()+50],
                        "confidence": 0.8
                    }
                    dates.append(date_info)
            
            analysis.important_dates = dates
            
        except Exception as e:
            print(f"Error extracting dates: {e}")

    async def _extract_currency_amounts(self, analysis: DocumentAnalysis, text: str):
        """Extract currency amounts from document."""
        try:
            currency_patterns = [
                r'\$[\d,]+\.?\d*',
                r'\b\d+\s+dollars?\b',
                r'\b\d+\s+USD\b'
            ]
            
            amounts = []
            for pattern in currency_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    amount_info = {
                        "text": match.group(),
                        "position": match.span(),
                        "context": text[max(0, match.start()-30):match.end()+30],
                        "confidence": 0.9
                    }
                    amounts.append(amount_info)
            
            analysis.currency_amounts = amounts
            
        except Exception as e:
            print(f"Error extracting currency amounts: {e}")

    async def _detect_pii(self, analysis: DocumentAnalysis, text: str):
        """Detect personally identifiable information."""
        try:
            pii_items = []
            
            # SSN detection
            ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
            matches = re.finditer(ssn_pattern, text)
            for match in matches:
                pii_items.append({
                    "type": "ssn",
                    "text": match.group(),
                    "position": match.span(),
                    "risk_level": "high"
                })
            
            # Email addresses (already in entity patterns)
            for entity in analysis.entities:
                if entity.entity_type == 'email_addresses':
                    pii_items.append({
                        "type": "email",
                        "text": entity.text,
                        "position": (entity.start_position, entity.end_position),
                        "risk_level": "medium"
                    })
            
            analysis.pii_detected = pii_items
            
        except Exception as e:
            print(f"Error detecting PII: {e}")

    async def _assess_privilege_risk(self, analysis: DocumentAnalysis, text: str):
        """Assess attorney-client privilege risk."""
        try:
            privilege_indicators = [
                'attorney-client', 'privileged', 'confidential attorney',
                'legal advice', 'counsel', 'attorney work product'
            ]
            
            risk_score = 0.0
            text_lower = text.lower()
            
            for indicator in privilege_indicators:
                if indicator in text_lower:
                    risk_score += 0.2
            
            analysis.privilege_risk = min(risk_score, 1.0)
            
            if analysis.privilege_risk > 0.6:
                analysis.confidentiality_level = ConfidentialityLevel.ATTORNEY_CLIENT_PRIVILEGED
            elif analysis.privilege_risk > 0.4:
                analysis.confidentiality_level = ConfidentialityLevel.ATTORNEY_WORK_PRODUCT
            
        except Exception as e:
            print(f"Error assessing privilege risk: {e}")

    async def _assess_confidentiality(self, analysis: DocumentAnalysis, text: str):
        """Assess document confidentiality level."""
        try:
            confidentiality_markers = {
                ConfidentialityLevel.HIGHLY_CONFIDENTIAL: [
                    'highly confidential', 'top secret', 'classified'
                ],
                ConfidentialityLevel.CONFIDENTIAL: [
                    'confidential', 'proprietary', 'internal only'
                ],
                ConfidentialityLevel.INTERNAL: [
                    'internal', 'company confidential'
                ]
            }
            
            text_lower = text.lower()
            highest_level = ConfidentialityLevel.PUBLIC
            
            for level, markers in confidentiality_markers.items():
                if any(marker in text_lower for marker in markers):
                    if level.value > highest_level.value:
                        highest_level = level
            
            # Consider privilege risk
            if analysis.privilege_risk > 0.6:
                highest_level = ConfidentialityLevel.ATTORNEY_CLIENT_PRIVILEGED
            
            analysis.confidentiality_level = highest_level
            
        except Exception as e:
            print(f"Error assessing confidentiality: {e}")

    async def _assess_risks(self, analysis: DocumentAnalysis, text: str):
        """Assess various risks in the document."""
        try:
            risk_factors = []
            
            # PII risk
            if analysis.pii_detected:
                risk_factors.append(f"Contains {len(analysis.pii_detected)} PII items")
            
            # Privilege risk
            if analysis.privilege_risk > 0.5:
                risk_factors.append("High attorney-client privilege risk")
            
            # Confidentiality risk
            if analysis.confidentiality_level in [ConfidentialityLevel.CONFIDENTIAL, ConfidentialityLevel.HIGHLY_CONFIDENTIAL]:
                risk_factors.append("Contains confidential information")
            
            # Financial information risk
            if analysis.currency_amounts:
                risk_factors.append("Contains financial information")
            
            analysis.risk_factors = risk_factors
            
        except Exception as e:
            print(f"Error assessing risks: {e}")

    async def _analyze_sentiment(self, analysis: DocumentAnalysis, text: str):
        """Analyze sentiment of the document."""
        try:
            # Use AI for sentiment analysis
            prompt = f"""
            Analyze the sentiment/tone of this legal document text.
            Consider the language, tone, and overall sentiment.
            
            Text (first 2000 characters):
            {text[:2000]}...
            
            Return a sentiment score from -1.0 (very negative) to 1.0 (very positive),
            where 0.0 is neutral.
            
            Return only the numeric score as a float.
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.1,
                max_tokens=50
            )
            
            try:
                sentiment_score = float(response.strip())
                analysis.sentiment_score = max(-1.0, min(1.0, sentiment_score))
            except ValueError:
                analysis.sentiment_score = 0.0
                
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            analysis.sentiment_score = None

    async def _generate_summary(
        self, 
        analysis: DocumentAnalysis, 
        text: str, 
        case_context: Optional[Case]
    ):
        """Generate executive summary and key points."""
        try:
            context_info = ""
            if case_context:
                context_info = f"Case context: {case_context.case_type} - {case_context.title}"
            
            prompt = f"""
            Create an executive summary and key points for this legal document.
            
            {context_info}
            Document category: {analysis.primary_category.value}
            
            Text (first 3000 characters):
            {text[:3000]}...
            
            Generate:
            1. A concise executive summary (2-3 sentences)
            2. 3-5 key points/takeaways
            
            Return as JSON:
            {{
                "executive_summary": "Brief 2-3 sentence summary",
                "key_points": ["Point 1", "Point 2", "Point 3"]
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.2,
                max_tokens=500
            )
            
            summary_data = json.loads(response)
            analysis.executive_summary = summary_data.get("executive_summary", "")
            analysis.key_points = summary_data.get("key_points", [])
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            analysis.executive_summary = "Summary generation failed"
            analysis.key_points = []

    async def _calculate_overall_confidence(self, analysis: DocumentAnalysis) -> float:
        """Calculate overall confidence score for the analysis."""
        try:
            confidence_factors = []
            
            # Category confidence
            confidence_factors.append(analysis.category_confidence)
            
            # Entity extraction confidence
            if analysis.entities:
                avg_entity_confidence = sum(e.confidence for e in analysis.entities) / len(analysis.entities)
                confidence_factors.append(avg_entity_confidence)
            
            # Citation confidence
            if analysis.citations:
                avg_citation_confidence = sum(c.get("confidence", 0.0) for c in analysis.citations) / len(analysis.citations)
                confidence_factors.append(avg_citation_confidence)
            
            # Text quality factors
            if analysis.word_count > 100:
                confidence_factors.append(0.8)  # Good text length
            else:
                confidence_factors.append(0.4)  # Short text, lower confidence
            
            # Calculate weighted average
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5
                
        except Exception as e:
            print(f"Error calculating confidence: {e}")
            return 0.0

    async def batch_analyze_documents(
        self, 
        file_infos: List[FileInfo], 
        case_context: Optional[Case] = None,
        max_concurrent: int = 5
    ) -> List[DocumentAnalysis]:
        """Analyze multiple documents concurrently."""
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def analyze_with_semaphore(file_info):
                async with semaphore:
                    return await self.analyze_document(file_info, case_context)
            
            tasks = [analyze_with_semaphore(file_info) for file_info in file_infos]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful analyses
            successful_analyses = [
                result for result in results 
                if isinstance(result, DocumentAnalysis)
            ]
            
            return successful_analyses
            
        except Exception as e:
            print(f"Error in batch analysis: {e}")
            return []

    def export_analysis_report(self, analysis: DocumentAnalysis, format: str = "json") -> str:
        """Export document analysis report in specified format."""
        try:
            if format.lower() == "json":
                return json.dumps({
                    "file_id": analysis.file_id,
                    "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
                    "content_stats": {
                        "word_count": analysis.word_count,
                        "character_count": analysis.character_count,
                        "page_count": analysis.page_count
                    },
                    "categorization": {
                        "primary_category": analysis.primary_category.value,
                        "secondary_categories": [cat.value for cat in analysis.secondary_categories],
                        "confidence": analysis.category_confidence
                    },
                    "entities": [
                        {
                            "type": entity.entity_type,
                            "text": entity.text,
                            "confidence": entity.confidence
                        }
                        for entity in analysis.entities
                    ],
                    "key_terms": analysis.key_terms,
                    "legal_concepts": [
                        {
                            "type": concept.concept_type,
                            "name": concept.concept_name,
                            "confidence": concept.confidence
                        }
                        for concept in analysis.legal_concepts
                    ],
                    "citations": analysis.citations,
                    "important_dates": analysis.important_dates,
                    "currency_amounts": analysis.currency_amounts,
                    "confidentiality": {
                        "level": analysis.confidentiality_level.value,
                        "privilege_risk": analysis.privilege_risk
                    },
                    "pii_detected": analysis.pii_detected,
                    "risk_factors": analysis.risk_factors,
                    "summary": {
                        "executive_summary": analysis.executive_summary,
                        "key_points": analysis.key_points,
                        "sentiment_score": analysis.sentiment_score
                    },
                    "quality_metrics": {
                        "analysis_confidence": analysis.analysis_confidence,
                        "processing_time": analysis.processing_time
                    },
                    "metadata": analysis.metadata
                }, indent=2, default=str)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            print(f"Error exporting analysis report: {e}")
            return ""