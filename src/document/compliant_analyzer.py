#!/usr/bin/env python3
"""
Compliant Document Analysis System
Legal AI System - Educational Analysis with Full Compliance

This module provides compliant document analysis with:
- Educational summaries with mandatory disclaimers
- Key dates and parties extraction (educational only)
- Attorney review flagging for all outputs
- No personalized legal recommendations
- Comprehensive compliance safeguards
"""

import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import system components
from ..core.attorney_review import AttorneyReviewSystem
from ..core.audit_logger import AuditLogger
from ..core.security import encrypt_data, decrypt_data
from .classification_engine import classification_engine
from .ocr_processor import ocr_processor

# Setup logging
logger = logging.getLogger('compliant_analyzer')

class AnalysisType(str, Enum):
    """Types of educational analysis"""
    EDUCATIONAL_SUMMARY = "educational_summary"
    METADATA_EXTRACTION = "metadata_extraction"
    TIMELINE_ANALYSIS = "timeline_analysis"
    PROCEDURAL_OVERVIEW = "procedural_overview"
    DOCUMENT_STRUCTURE = "document_structure"

class ComplianceLevel(str, Enum):
    """Compliance assurance levels"""
    EDUCATIONAL_ONLY = "educational_only"
    REQUIRES_ATTORNEY_REVIEW = "requires_attorney_review"
    FLAGGED_FOR_REVIEW = "flagged_for_review"
    COMPLIANCE_APPROVED = "compliance_approved"

@dataclass
class DisclaimerSet:
    """Comprehensive disclaimer set"""
    primary_disclaimer: str
    educational_disclaimer: str
    no_advice_disclaimer: str
    attorney_consultation_disclaimer: str
    jurisdiction_disclaimer: str

@dataclass
class ExtractedDate:
    """Extracted date with educational context"""
    date: datetime
    description: str
    significance: str
    educational_note: str

@dataclass
class ExtractedParty:
    """Extracted party information (educational only)"""
    party_type: str  # plaintiff, defendant, debtor, etc.
    role_description: str
    educational_context: str

@dataclass
class EducationalSummary:
    """Educational document summary"""
    document_purpose: str
    key_legal_concepts: List[str]
    procedural_context: str
    educational_points: List[str]
    complexity_level: str
    learning_objectives: List[str]

@dataclass
class ComplianceFlags:
    """Compliance and review flags"""
    attorney_review_required: bool
    contains_legal_advice: bool
    contains_privileged_content: bool
    requires_jurisdiction_warning: bool
    needs_educational_context: bool
    upl_risk_level: str

@dataclass
class AnalysisResult:
    """Complete educational analysis result"""
    analysis_id: str
    document_id: str
    classification_id: Optional[str]
    analysis_type: AnalysisType
    educational_summary: EducationalSummary
    extracted_dates: List[ExtractedDate]
    extracted_parties: List[ExtractedParty]
    key_findings: List[str]
    disclaimers: DisclaimerSet
    compliance_flags: ComplianceFlags
    compliance_level: ComplianceLevel
    attorney_review_notes: List[str]
    processing_time: float
    created_at: datetime
    created_by: str
    warnings: List[str]

class CompliantDocumentAnalyzer:
    """
    Educational document analyzer with comprehensive compliance safeguards
    """

    def __init__(self, storage_root: str = "storage/analysis"):
        self.logger = logger
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Initialize compliance components
        self.attorney_review = AttorneyReviewSystem()
        self.audit_logger = AuditLogger()

        # Load disclaimers
        self._initialize_disclaimers()

        # Educational analysis patterns
        self._initialize_analysis_patterns()

    def _initialize_disclaimers(self):
        """Initialize comprehensive disclaimer set"""
        self.standard_disclaimers = DisclaimerSet(
            primary_disclaimer="""
            ⚠️  IMPORTANT LEGAL DISCLAIMER ⚠️

            This analysis is provided for EDUCATIONAL PURPOSES ONLY and does NOT constitute
            legal advice. The information presented is general in nature and may not apply
            to your specific situation.
            """,

            educational_disclaimer="""
            EDUCATIONAL CONTENT NOTICE:

            This analysis is designed to help users understand legal documents and procedures
            for educational purposes. It should be used as a learning tool only and not as
            a substitute for professional legal counsel.
            """,

            no_advice_disclaimer="""
            NO LEGAL ADVICE PROVIDED:

            This system does not provide legal advice, recommendations, or guidance for
            specific legal matters. All content is educational and informational only.
            """,

            attorney_consultation_disclaimer="""
            ATTORNEY CONSULTATION REQUIRED:

            For any legal matter, you must consult with a qualified attorney licensed
            in your jurisdiction. This analysis cannot replace professional legal advice
            tailored to your specific circumstances.
            """,

            jurisdiction_disclaimer="""
            JURISDICTION NOTICE:

            Legal procedures and requirements vary significantly by jurisdiction.
            This educational analysis may not reflect the specific laws, rules,
            or procedures applicable in your location.
            """
        )

    def _initialize_analysis_patterns(self):
        """Initialize educational analysis patterns"""

        # Legal concept patterns for educational identification
        self.legal_concepts = {
            'procedural': [
                'motion', 'hearing', 'discovery', 'deposition', 'interrogatories',
                'summary judgment', 'venue', 'jurisdiction', 'service of process'
            ],
            'bankruptcy': [
                'discharge', 'automatic stay', 'preference', 'fraudulent transfer',
                'exemptions', 'trustee', 'creditor meeting', 'reaffirmation'
            ],
            'contract': [
                'breach', 'consideration', 'specific performance', 'damages',
                'mutual assent', 'statute of frauds', 'impossibility'
            ],
            'civil': [
                'negligence', 'tort', 'liability', 'damages', 'causation',
                'duty of care', 'standard of care', 'proximate cause'
            ]
        }

        # Date significance patterns
        self.date_patterns = {
            'filing': [
                r'filed\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'date\s+filed\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
            ],
            'hearing': [
                r'hearing\s+(?:scheduled\s+)?(?:for\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'court\s+date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
            ],
            'deadline': [
                r'deadline\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'due\s+(?:by\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
            ]
        }

    def analyze_document(self, document_id: str, analysis_type: AnalysisType,
                        user_id: str) -> AnalysisResult:
        """
        Perform compliant educational analysis

        Args:
            document_id: ID of document to analyze
            analysis_type: Type of educational analysis
            user_id: User requesting analysis

        Returns:
            AnalysisResult with educational analysis and compliance safeguards
        """
        start_time = datetime.now()
        warnings = []

        try:
            self.logger.info(f"Starting compliant analysis: {document_id} ({analysis_type.value})")

            # Generate analysis ID
            analysis_id = f"ana_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Get classification results
            classification_results = self._get_classification_results(document_id)
            classification_id = classification_results.classification_id if classification_results else None

            # Get OCR results
            ocr_results = ocr_processor.get_document_ocr_results(document_id)
            if not ocr_results:
                warnings.append("No OCR results available - analysis may be limited")
                text_content = ""
            else:
                text_content = ocr_results[0].extracted_text

            # Perform educational analysis
            educational_summary = self._create_educational_summary(
                text_content, classification_results, analysis_type
            )

            # Extract dates with educational context
            extracted_dates = self._extract_educational_dates(text_content)

            # Extract parties with educational context
            extracted_parties = self._extract_educational_parties(text_content)

            # Generate key educational findings
            key_findings = self._generate_educational_findings(
                text_content, classification_results, educational_summary
            )

            # Assess compliance requirements
            compliance_flags = self._assess_compliance_requirements(
                text_content, educational_summary, key_findings
            )

            # Determine compliance level
            compliance_level = self._determine_compliance_level(compliance_flags)

            # Generate attorney review notes
            attorney_review_notes = self._generate_attorney_review_notes(
                compliance_flags, educational_summary
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            result = AnalysisResult(
                analysis_id=analysis_id,
                document_id=document_id,
                classification_id=classification_id,
                analysis_type=analysis_type,
                educational_summary=educational_summary,
                extracted_dates=extracted_dates,
                extracted_parties=extracted_parties,
                key_findings=key_findings,
                disclaimers=self.standard_disclaimers,
                compliance_flags=compliance_flags,
                compliance_level=compliance_level,
                attorney_review_notes=attorney_review_notes,
                processing_time=processing_time,
                created_at=datetime.now(),
                created_by=user_id,
                warnings=warnings
            )

            # Store analysis result
            self._store_analysis_result(result)

            # Log for audit trail
            self._log_analysis_event(result, user_id)

            # Flag for attorney review if required
            if compliance_flags.attorney_review_required:
                self._flag_for_attorney_review(result)

            return result

        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            return self._create_failed_analysis(document_id, analysis_id, str(e), start_time, user_id)

    def _get_classification_results(self, document_id: str):
        """Get classification results for document"""
        try:
            # Search for classification results
            for cls_file in classification_engine.storage_root.glob("*.json"):
                result = classification_engine.retrieve_classification_result(cls_file.stem)
                if result and result.document_id == document_id:
                    return result
            return None
        except Exception as e:
            self.logger.error(f"Failed to get classification results: {e}")
            return None

    def _create_educational_summary(self, text_content: str, classification_results,
                                   analysis_type: AnalysisType) -> EducationalSummary:
        """Create educational document summary"""
        try:
            # Determine document purpose
            document_purpose = self._determine_document_purpose(text_content, classification_results)

            # Identify key legal concepts
            key_legal_concepts = self._identify_legal_concepts(text_content)

            # Generate procedural context
            procedural_context = self._generate_procedural_context(text_content, classification_results)

            # Create educational points
            educational_points = self._generate_educational_points(
                text_content, key_legal_concepts, procedural_context
            )

            # Assess complexity level
            complexity_level = self._assess_complexity_level(text_content, key_legal_concepts)

            # Generate learning objectives
            learning_objectives = self._generate_learning_objectives(
                document_purpose, key_legal_concepts, analysis_type
            )

            return EducationalSummary(
                document_purpose=document_purpose,
                key_legal_concepts=key_legal_concepts,
                procedural_context=procedural_context,
                educational_points=educational_points,
                complexity_level=complexity_level,
                learning_objectives=learning_objectives
            )

        except Exception as e:
            self.logger.error(f"Failed to create educational summary: {e}")
            return EducationalSummary(
                document_purpose="Educational analysis not available",
                key_legal_concepts=[],
                procedural_context="Context analysis not available",
                educational_points=["Educational analysis requires attorney review"],
                complexity_level="unknown",
                learning_objectives=["Consult with qualified attorney"]
            )

    def _determine_document_purpose(self, text_content: str, classification_results) -> str:
        """Determine document purpose for educational context"""
        if classification_results:
            doc_type = classification_results.document_type.value

            purpose_map = {
                'motion': 'Educational example of a legal motion requesting court action',
                'petition': 'Educational example of a formal request to the court',
                'order': 'Educational example of a court directive or decision',
                'complaint': 'Educational example of a formal legal complaint',
                'brief': 'Educational example of legal argumentation and analysis'
            }

            return purpose_map.get(doc_type, 'Educational legal document for learning purposes')
        else:
            return 'Educational legal document for academic study'

    def _identify_legal_concepts(self, text_content: str) -> List[str]:
        """Identify legal concepts for educational purposes"""
        found_concepts = []
        text_lower = text_content.lower()

        for category, concepts in self.legal_concepts.items():
            for concept in concepts:
                if concept.lower() in text_lower:
                    found_concepts.append(f"{concept} ({category} law)")

        # Limit to top 10 for readability
        return found_concepts[:10]

    def _generate_procedural_context(self, text_content: str, classification_results) -> str:
        """Generate procedural context for educational purposes"""
        try:
            context_parts = []

            if classification_results:
                doc_type = classification_results.document_type.value
                context_parts.append(f"This document is an educational example of a {doc_type}")

                if doc_type == 'motion':
                    context_parts.append("Motions are formal requests asking the court to take specific action")
                elif doc_type == 'petition':
                    context_parts.append("Petitions are formal written requests submitted to a court")
                elif doc_type == 'order':
                    context_parts.append("Orders are official directives or decisions issued by the court")

            # Add general procedural context
            if 'filed' in text_content.lower():
                context_parts.append("Filing documents with the court is a fundamental part of legal procedure")

            if 'hearing' in text_content.lower():
                context_parts.append("Court hearings allow parties to present arguments and evidence")

            return ". ".join(context_parts) + "."

        except Exception as e:
            return "Procedural context analysis requires attorney consultation for your specific situation."

    def _generate_educational_points(self, text_content: str, key_concepts: List[str],
                                   procedural_context: str) -> List[str]:
        """Generate key educational points"""
        points = []

        # Add concept-based educational points
        if any('motion' in concept.lower() for concept in key_concepts):
            points.append("Legal motions follow specific procedural rules that vary by jurisdiction")

        if any('bankruptcy' in concept.lower() for concept in key_concepts):
            points.append("Bankruptcy procedures are governed by federal law but may have local variations")

        if any('contract' in concept.lower() for concept in key_concepts):
            points.append("Contract law principles help understand agreements and obligations")

        # Add document-specific educational points
        if 'deadline' in text_content.lower():
            points.append("Legal deadlines are crucial and missing them can have serious consequences")

        if 'jurisdiction' in text_content.lower():
            points.append("Jurisdiction determines which court has authority over a legal matter")

        # Ensure we have educational content
        if not points:
            points.append("This document illustrates common legal document structure and language")

        # Add mandatory educational reminder
        points.append("This analysis is for educational purposes only - consult an attorney for legal advice")

        return points

    def _assess_complexity_level(self, text_content: str, key_concepts: List[str]) -> str:
        """Assess document complexity for educational purposes"""
        complexity_factors = 0

        # Check for complex legal terminology
        complex_terms = ['heretofore', 'whereas', 'notwithstanding', 'pursuant to', 'inter alia']
        complexity_factors += sum(1 for term in complex_terms if term in text_content.lower())

        # Check for multiple legal concepts
        complexity_factors += len(key_concepts) // 3

        # Check for citations
        citation_pattern = r'\d+\s+[A-Z][a-z]+\s+\d+'
        citations = len(re.findall(citation_pattern, text_content))
        complexity_factors += citations // 2

        if complexity_factors >= 5:
            return "advanced"
        elif complexity_factors >= 3:
            return "intermediate"
        else:
            return "basic"

    def _generate_learning_objectives(self, document_purpose: str, key_concepts: List[str],
                                    analysis_type: AnalysisType) -> List[str]:
        """Generate educational learning objectives"""
        objectives = []

        if analysis_type == AnalysisType.EDUCATIONAL_SUMMARY:
            objectives.append("Understand the structure and purpose of legal documents")
            objectives.append("Recognize common legal terminology and concepts")

        if analysis_type == AnalysisType.METADATA_EXTRACTION:
            objectives.append("Learn to identify key information in legal documents")
            objectives.append("Understand the importance of dates and parties in legal proceedings")

        if analysis_type == AnalysisType.PROCEDURAL_OVERVIEW:
            objectives.append("Understand basic legal procedures and requirements")
            objectives.append("Learn about court processes and documentation")

        # Add concept-specific objectives
        if any('bankruptcy' in concept.lower() for concept in key_concepts):
            objectives.append("Gain educational insight into bankruptcy procedures")

        if any('motion' in concept.lower() for concept in key_concepts):
            objectives.append("Learn about the motion practice in legal proceedings")

        # Always include compliance objective
        objectives.append("Understand the importance of seeking qualified legal counsel")

        return objectives[:5]  # Limit to 5 objectives

    def _extract_educational_dates(self, text_content: str) -> List[ExtractedDate]:
        """Extract dates with educational context"""
        extracted_dates = []

        for date_type, patterns in self.date_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    date_str = match.group(1)
                    parsed_date = self._parse_date(date_str)

                    if parsed_date:
                        educational_context = self._get_date_educational_context(date_type, parsed_date)

                        extracted_dates.append(ExtractedDate(
                            date=parsed_date,
                            description=f"{date_type.title()} date",
                            significance=self._get_date_significance(date_type),
                            educational_note=educational_context
                        ))

        return extracted_dates[:10]  # Limit for performance

    def _get_date_educational_context(self, date_type: str, date: datetime) -> str:
        """Generate educational context for dates"""
        contexts = {
            'filing': "Filing dates establish when documents were officially submitted to the court",
            'hearing': "Hearing dates indicate when court proceedings are scheduled",
            'deadline': "Deadlines are critical in legal proceedings and missing them can have consequences"
        }

        context = contexts.get(date_type, "Important date in the legal proceeding")

        # Add timing context
        if date < datetime.now():
            context += " (This date has passed - for educational reference only)"
        else:
            context += " (Future date - timing is illustrative for educational purposes)"

        return context

    def _get_date_significance(self, date_type: str) -> str:
        """Get educational significance of date types"""
        significance = {
            'filing': "Establishes official record and may affect legal rights",
            'hearing': "Opportunity for parties to present their case to the court",
            'deadline': "Failure to meet deadlines can result in adverse consequences"
        }

        return significance.get(date_type, "Important for legal procedure understanding")

    def _extract_educational_parties(self, text_content: str) -> List[ExtractedParty]:
        """Extract party information with educational context"""
        parties = []

        party_patterns = {
            'plaintiff': r'plaintiff(?:s)?\s*:?\s*([a-z\s,\.]+?)(?:\s+(?:v|vs|versus))',
            'defendant': r'defendant(?:s)?\s*:?\s*([a-z\s,\.]+?)(?:\s+(?:,|;|\n))',
            'debtor': r'debtor(?:s)?\s*:?\s*([a-z\s,\.]+?)(?:\s+(?:,|;|\n))',
            'creditor': r'creditor(?:s)?\s*:?\s*([a-z\s,\.]+?)(?:\s+(?:,|;|\n))'
        }

        for party_type, pattern in party_patterns.items():
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                party_name = match.group(1).strip()
                if len(party_name) > 2:  # Valid party name

                    role_description = self._get_party_role_description(party_type)
                    educational_context = self._get_party_educational_context(party_type)

                    parties.append(ExtractedParty(
                        party_type=party_type,
                        role_description=role_description,
                        educational_context=educational_context
                    ))

        return parties[:5]  # Limit for privacy

    def _get_party_role_description(self, party_type: str) -> str:
        """Get educational description of party roles"""
        descriptions = {
            'plaintiff': "Party who initiates a lawsuit",
            'defendant': "Party against whom a lawsuit is filed",
            'debtor': "Person or entity that owes money in bankruptcy proceedings",
            'creditor': "Person or entity owed money in bankruptcy proceedings"
        }

        return descriptions.get(party_type, "Party to the legal proceeding")

    def _get_party_educational_context(self, party_type: str) -> str:
        """Get educational context for party types"""
        contexts = {
            'plaintiff': "The plaintiff bears the burden of proving their case",
            'defendant': "The defendant has the right to respond and defend against claims",
            'debtor': "Debtors in bankruptcy have certain rights and obligations under federal law",
            'creditor': "Creditors have specific rights in bankruptcy proceedings"
        }

        base_context = contexts.get(party_type, "Each party has specific rights and obligations")
        return base_context + " (Educational overview - specific rights vary by jurisdiction)"

    def _generate_educational_findings(self, text_content: str, classification_results,
                                     educational_summary: EducationalSummary) -> List[str]:
        """Generate key educational findings"""
        findings = []

        # Document structure findings
        if len(text_content) > 5000:
            findings.append("This is a substantial legal document requiring careful review")
        elif len(text_content) < 1000:
            findings.append("This is a brief legal document with focused content")

        # Content-based findings
        if 'motion' in text_content.lower():
            findings.append("Document contains motion practice - educational example of court requests")

        if any(term in text_content.lower() for term in ['deadline', 'due', 'within']):
            findings.append("Document contains time-sensitive elements - timing is crucial in legal matters")

        if re.search(r'\$[\d,]+', text_content):
            findings.append("Document contains financial information - amounts are for educational reference")

        # Educational complexity findings
        complexity = educational_summary.complexity_level
        if complexity == 'advanced':
            findings.append("Advanced legal concepts present - additional study may be beneficial")
        elif complexity == 'intermediate':
            findings.append("Intermediate legal concepts present - good for educational development")

        # Always include educational reminder
        findings.append("All findings are for educational purposes only - not legal advice")

        return findings

    def _assess_compliance_requirements(self, text_content: str, educational_summary: EducationalSummary,
                                      key_findings: List[str]) -> ComplianceFlags:
        """Assess compliance requirements for analysis"""
        try:
            # Use attorney review system
            review_result = self.attorney_review.review_content(
                content=text_content[:1000],  # First 1000 chars
                content_id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Check for legal advice language
            advice_patterns = ['you should', 'recommend', 'advise', 'suggest that you']
            contains_legal_advice = any(pattern in text_content.lower() for pattern in advice_patterns)

            # Check for privileged content
            privileged_patterns = ['attorney-client', 'privileged', 'confidential', 'work product']
            contains_privileged = any(pattern in text_content.lower() for pattern in privileged_patterns)

            # Check for jurisdiction warnings needed
            jurisdiction_patterns = ['state law', 'federal law', 'local rules', 'jurisdiction']
            needs_jurisdiction_warning = any(pattern in text_content.lower() for pattern in jurisdiction_patterns)

            return ComplianceFlags(
                attorney_review_required=review_result.requires_review or contains_legal_advice,
                contains_legal_advice=contains_legal_advice,
                contains_privileged_content=contains_privileged,
                requires_jurisdiction_warning=needs_jurisdiction_warning,
                needs_educational_context=True,  # Always need educational context
                upl_risk_level=review_result.risk_level.value
            )

        except Exception as e:
            self.logger.error(f"Compliance assessment failed: {e}")
            # Default to maximum compliance requirements
            return ComplianceFlags(
                attorney_review_required=True,
                contains_legal_advice=True,
                contains_privileged_content=True,
                requires_jurisdiction_warning=True,
                needs_educational_context=True,
                upl_risk_level="high"
            )

    def _determine_compliance_level(self, compliance_flags: ComplianceFlags) -> ComplianceLevel:
        """Determine overall compliance level"""
        if compliance_flags.attorney_review_required:
            return ComplianceLevel.REQUIRES_ATTORNEY_REVIEW
        elif compliance_flags.contains_legal_advice or compliance_flags.upl_risk_level == "high":
            return ComplianceLevel.FLAGGED_FOR_REVIEW
        elif compliance_flags.needs_educational_context:
            return ComplianceLevel.EDUCATIONAL_ONLY
        else:
            return ComplianceLevel.COMPLIANCE_APPROVED

    def _generate_attorney_review_notes(self, compliance_flags: ComplianceFlags,
                                      educational_summary: EducationalSummary) -> List[str]:
        """Generate notes for attorney review"""
        notes = []

        if compliance_flags.attorney_review_required:
            notes.append("Attorney review required before sharing analysis results")

        if compliance_flags.contains_legal_advice:
            notes.append("Content may contain language that could be construed as legal advice")

        if compliance_flags.contains_privileged_content:
            notes.append("Document may contain privileged or confidential information")

        if compliance_flags.upl_risk_level in ["high", "medium"]:
            notes.append(f"UPL risk level: {compliance_flags.upl_risk_level} - exercise caution")

        if educational_summary.complexity_level == "advanced":
            notes.append("Complex legal concepts present - ensure educational context is clear")

        if not notes:
            notes.append("Standard educational disclaimers apply")

        return notes

    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        try:
            for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None

    def _create_failed_analysis(self, document_id: str, analysis_id: str, error: str,
                              start_time: datetime, user_id: str) -> AnalysisResult:
        """Create failed analysis result"""
        processing_time = (datetime.now() - start_time).total_seconds()

        return AnalysisResult(
            analysis_id=analysis_id,
            document_id=document_id,
            classification_id=None,
            analysis_type=AnalysisType.EDUCATIONAL_SUMMARY,
            educational_summary=EducationalSummary(
                document_purpose="Analysis failed - consult attorney",
                key_legal_concepts=[],
                procedural_context="Unable to analyze - seek professional guidance",
                educational_points=["Analysis could not be completed safely"],
                complexity_level="unknown",
                learning_objectives=["Consult with qualified attorney"]
            ),
            extracted_dates=[],
            extracted_parties=[],
            key_findings=[f"Analysis failed: {error}"],
            disclaimers=self.standard_disclaimers,
            compliance_flags=ComplianceFlags(
                attorney_review_required=True,
                contains_legal_advice=False,
                contains_privileged_content=False,
                requires_jurisdiction_warning=True,
                needs_educational_context=True,
                upl_risk_level="high"
            ),
            compliance_level=ComplianceLevel.REQUIRES_ATTORNEY_REVIEW,
            attorney_review_notes=["Analysis failed - manual review required"],
            processing_time=processing_time,
            created_at=datetime.now(),
            created_by=user_id,
            warnings=[f"Analysis failed: {error}"]
        )

    def _store_analysis_result(self, result: AnalysisResult):
        """Store analysis result securely"""
        try:
            storage_path = self.storage_root / f"{result.analysis_id}.json"

            # Convert to dict and encrypt
            result_dict = asdict(result)
            result_data = json.dumps(result_dict, default=str)
            encrypted_data = encrypt_data(result_data.encode(), f"ana_{result.analysis_id}")

            with open(storage_path, 'wb') as f:
                f.write(encrypted_data)

            import os
            os.chmod(storage_path, 0o600)

            self.logger.info(f"Analysis result stored: {result.analysis_id}")

        except Exception as e:
            self.logger.error(f"Failed to store analysis result: {e}")
            raise

    def _log_analysis_event(self, result: AnalysisResult, user_id: str):
        """Log analysis event for audit"""
        self.audit_logger.log_document_event(
            event_type="document_analyzed",
            document_id=result.document_id,
            user_id=user_id,
            details={
                "analysis_id": result.analysis_id,
                "analysis_type": result.analysis_type.value,
                "compliance_level": result.compliance_level.value,
                "attorney_review_required": result.compliance_flags.attorney_review_required,
                "upl_risk_level": result.compliance_flags.upl_risk_level
            }
        )

    def _flag_for_attorney_review(self, result: AnalysisResult):
        """Flag analysis for attorney review"""
        try:
            # Create attorney review flag
            self.attorney_review.escalate_to_attorney(
                content_id=result.analysis_id,
                reason="Educational analysis requires attorney review",
                risk_level=result.compliance_flags.upl_risk_level,
                details={
                    "document_id": result.document_id,
                    "analysis_type": result.analysis_type.value,
                    "compliance_flags": asdict(result.compliance_flags)
                }
            )

            self.logger.info(f"Analysis flagged for attorney review: {result.analysis_id}")

        except Exception as e:
            self.logger.error(f"Failed to flag for attorney review: {e}")

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            total_analyses = 0
            compliance_distribution = {level.value: 0 for level in ComplianceLevel}
            analysis_type_distribution = {atype.value: 0 for atype in AnalysisType}
            attorney_reviews_required = 0

            for analysis_file in self.storage_root.glob("*.json"):
                # Count files for basic statistics
                total_analyses += 1

            return {
                "total_analyses": total_analyses,
                "compliance_distribution": compliance_distribution,
                "analysis_type_distribution": analysis_type_distribution,
                "attorney_reviews_required": attorney_reviews_required,
                "educational_disclaimer": self.standard_disclaimers.primary_disclaimer
            }

        except Exception as e:
            self.logger.error(f"Failed to get analysis statistics: {e}")
            return {"error": str(e)}

# Global compliant analyzer
compliant_analyzer = CompliantDocumentAnalyzer()

def validate_analysis_system():
    """Validate compliant analysis system"""
    try:
        print("✓ Compliant document analyzer initialized")

        # Test with sample legal text
        sample_text = """
        MOTION FOR SUMMARY JUDGMENT

        Case No. 2023-CV-1234
        Filed: January 15, 2024
        Hearing Date: February 20, 2024

        Plaintiff John Doe moves for summary judgment against Defendant Jane Smith.
        This motion is filed pursuant to Rule 56 of the Federal Rules of Civil Procedure.
        """

        # Create test document
        from .upload_handler import document_uploader
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_text)
            temp_path = f.name

        try:
            # Upload test document
            with open(temp_path, 'rb') as f:
                test_data = f.read()

            upload_result = document_uploader.upload_document(test_data, "test_motion.txt", "test_user")

            if upload_result.success:
                # Process OCR
                ocr_result = ocr_processor.process_document(upload_result.document_id, "test_user")

                if ocr_result.status.value == "completed":
                    # Classify document
                    classification_result = classification_engine.classify_document(
                        upload_result.document_id, "test_user"
                    )

                    # Analyze document
                    analysis_result = compliant_analyzer.analyze_document(
                        upload_result.document_id,
                        AnalysisType.EDUCATIONAL_SUMMARY,
                        "test_user"
                    )

                    print("✓ Compliant document analysis completed")
                    print(f"  Analysis ID: {analysis_result.analysis_id}")
                    print(f"  Compliance Level: {analysis_result.compliance_level.value}")
                    print(f"  Attorney Review Required: {analysis_result.compliance_flags.attorney_review_required}")
                    print(f"  Educational Points: {len(analysis_result.educational_summary.educational_points)}")
                    print(f"  Extracted Dates: {len(analysis_result.extracted_dates)}")

                    # Display disclaimer
                    print("\n" + "="*50)
                    print("MANDATORY DISCLAIMER:")
                    print(analysis_result.disclaimers.primary_disclaimer)

                    return True
                else:
                    print("✗ OCR processing failed for analysis test")
                    return False
            else:
                print("✗ Test document upload failed")
                return False

        finally:
            os.unlink(temp_path)

    except Exception as e:
        print(f"✗ Analysis system validation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Compliant Document Analysis System...")
    print("=" * 60)

    if validate_analysis_system():
        # Display statistics
        stats = compliant_analyzer.get_analysis_statistics()
        print(f"\nAnalysis System Statistics:")
        for key, value in stats.items():
            if key != "educational_disclaimer":
                print(f"  {key}: {value}")
    else:
        print("Analysis system validation failed")