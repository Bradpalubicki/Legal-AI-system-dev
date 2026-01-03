#!/usr/bin/env python3
"""
Legal Compliance Wrapper for AI Outputs
Ensures all AI-generated legal content includes proper disclaimers and compliance controls
"""

import os
import json
import re
import logging
import logging.handlers
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum, IntEnum
from dataclasses import dataclass, asdict
import hashlib
import secrets
from pathlib import Path
from .legal_advice_detector import legal_advice_detector, ContentClassification, AdviceRiskLevel

class AIOutputType(Enum):
    """Types of AI-generated legal content"""
    LEGAL_RESEARCH = "legal_research"
    DOCUMENT_ANALYSIS = "document_analysis"
    CONTRACT_REVIEW = "contract_review"
    CASE_SUMMARY = "case_summary"
    LEGAL_MEMO = "legal_memo"
    BRIEF_DRAFT = "brief_draft"
    CITATION_CHECK = "citation_check"
    PRECEDENT_ANALYSIS = "precedent_analysis"
    REGULATORY_GUIDANCE = "regulatory_guidance"
    CLIENT_COMMUNICATION = "client_communication"

class ReviewRequirement(IntEnum):
    """Attorney review requirements for AI output"""
    NONE = 0          # Informational only
    RECOMMENDED = 1   # Review recommended but not required
    REQUIRED = 2      # Must be reviewed before use
    MANDATORY = 3     # Must be reviewed and approved
    SUPERVISORY = 4   # Requires senior attorney review

class JurisdictionType(Enum):
    """Legal jurisdictions for compliance"""
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"
    INTERNATIONAL = "international"
    MULTI_JURISDICTION = "multi_jurisdiction"

@dataclass
class LegalCitation:
    """Structured legal citation with validation"""
    citation_id: str
    citation_text: str
    case_name: Optional[str]
    court: Optional[str]
    year: Optional[int]
    volume: Optional[str]
    reporter: Optional[str]
    page: Optional[str]
    jurisdiction: JurisdictionType
    citation_type: str  # "case", "statute", "regulation", "treatise"
    is_verified: bool
    verification_date: Optional[datetime]
    verification_source: Optional[str]
    confidence_score: float  # 0.0 to 1.0

@dataclass
class ComplianceMetadata:
    """Compliance metadata for AI-generated legal content"""
    output_id: str
    generated_at: datetime
    attorney_id: Optional[str]
    client_id: Optional[str]
    case_id: Optional[str]
    practice_area: str
    jurisdiction: JurisdictionType
    
    # AI Model Information
    model_name: str
    model_version: str
    prompt_hash: str
    confidence_score: float
    
    # Compliance Requirements
    review_requirement: ReviewRequirement
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    
    # Content Classification
    contains_legal_advice: bool
    contains_privileged_info: bool
    contains_client_data: bool
    is_work_product: bool
    
    # Quality Metrics
    citation_count: int
    verified_citations: int
    accuracy_rating: Optional[float]
    completeness_rating: Optional[float]

class LegalComplianceWrapper:
    """Comprehensive legal compliance wrapper for AI outputs"""
    
    def __init__(self, db_path: str = "legal_compliance.db"):
        self.db_path = db_path
        self.logger = self._setup_logger()
        self._init_database()
        
        # Legal disclaimer templates by jurisdiction
        self.disclaimer_templates = {
            JurisdictionType.FEDERAL: {
                "standard": "This AI-generated content is for informational purposes only and does not constitute legal advice. Federal law applications may vary based on specific circumstances.",
                "privileged": "ATTORNEY-CLIENT PRIVILEGED: This AI-generated content is attorney work product intended solely for legal counsel. Do not distribute without authorization.",
                "research": "This legal research is AI-generated and should be independently verified. Cases and statutes cited should be validated for current status."
            },
            
            JurisdictionType.STATE: {
                "standard": "This AI-generated content is for informational purposes only and does not constitute legal advice. State law varies significantly by jurisdiction.",
                "privileged": "ATTORNEY-CLIENT PRIVILEGED: This AI-generated content is attorney work product. State privilege rules apply.",
                "research": "This legal research is AI-generated for the specified state jurisdiction. Laws and regulations should be independently verified."
            },
            
            JurisdictionType.MULTI_JURISDICTION: {
                "standard": "This AI-generated content covers multiple jurisdictions and is for informational purposes only. Legal requirements vary significantly between jurisdictions.",
                "privileged": "ATTORNEY-CLIENT PRIVILEGED: Multi-jurisdictional analysis. Privilege rules may vary by jurisdiction.",
                "research": "This multi-jurisdictional legal research is AI-generated. All cited authorities should be independently verified for each relevant jurisdiction."
            }
        }
        
        # Citation validation patterns
        self.citation_patterns = {
            "case": [
                r'(\w+(?:\s+\w+)*)\s+v\.\s+(\w+(?:\s+\w+)*),\s*(\d+)\s+(\w+(?:\.\s*\w+)*)\s+(\d+)',  # Case citation
                r'(\d+)\s+(\w+(?:\.\s*\w+)*)\s+(\d+)\s+\((\w+(?:\.\s*\w+)*)\s+(\d{4})\)'  # Full case citation
            ],
            "statute": [
                r'(\d+)\s+U\.S\.C\.?\s*§?\s*(\d+(?:\(\w+\))*)',  # Federal statute
                r'(\w+(?:\.\s*\w+)*)\s*§\s*(\d+(?:\.\d+)*)'  # State statute
            ],
            "regulation": [
                r'(\d+)\s+C\.F\.R\.?\s*§?\s*(\d+(?:\.\d+)*)',  # Federal regulation
                r'(\d+)\s+Fed\.\s*Reg\.?\s*(\d+)'  # Federal Register
            ]
        }
        
        # Attorney review requirements by content type
        self.review_requirements = {
            AIOutputType.LEGAL_RESEARCH: ReviewRequirement.RECOMMENDED,
            AIOutputType.DOCUMENT_ANALYSIS: ReviewRequirement.REQUIRED,
            AIOutputType.CONTRACT_REVIEW: ReviewRequirement.MANDATORY,
            AIOutputType.CASE_SUMMARY: ReviewRequirement.RECOMMENDED,
            AIOutputType.LEGAL_MEMO: ReviewRequirement.REQUIRED,
            AIOutputType.BRIEF_DRAFT: ReviewRequirement.MANDATORY,
            AIOutputType.CITATION_CHECK: ReviewRequirement.RECOMMENDED,
            AIOutputType.PRECEDENT_ANALYSIS: ReviewRequirement.REQUIRED,
            AIOutputType.REGULATORY_GUIDANCE: ReviewRequirement.SUPERVISORY,
            AIOutputType.CLIENT_COMMUNICATION: ReviewRequirement.MANDATORY
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup legal compliance logger"""
        logger = logging.getLogger('legal_compliance')
        logger.setLevel(logging.INFO)
        
        Path('logs').mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/legal_compliance.log',
            maxBytes=50*1024*1024,
            backupCount=100,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - LEGAL_COMPLIANCE - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize legal compliance database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # AI outputs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_legal_outputs (
                output_id TEXT PRIMARY KEY,
                generated_at TIMESTAMP NOT NULL,
                attorney_id TEXT,
                client_id TEXT,
                case_id TEXT,
                practice_area TEXT NOT NULL,
                jurisdiction TEXT NOT NULL,
                output_type TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                prompt_hash TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                review_requirement TEXT NOT NULL,
                reviewed_by TEXT,
                reviewed_at TIMESTAMP,
                approved_by TEXT,
                approved_at TIMESTAMP,
                contains_legal_advice BOOLEAN NOT NULL,
                contains_privileged_info BOOLEAN NOT NULL,
                contains_client_data BOOLEAN NOT NULL,
                is_work_product BOOLEAN NOT NULL,
                citation_count INTEGER DEFAULT 0,
                verified_citations INTEGER DEFAULT 0,
                accuracy_rating REAL,
                completeness_rating REAL,
                original_content TEXT NOT NULL,
                wrapped_content TEXT NOT NULL
            )
        ''')
        
        # Legal citations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS legal_citations (
                citation_id TEXT PRIMARY KEY,
                output_id TEXT NOT NULL,
                citation_text TEXT NOT NULL,
                case_name TEXT,
                court TEXT,
                year INTEGER,
                volume TEXT,
                reporter TEXT,
                page TEXT,
                jurisdiction TEXT NOT NULL,
                citation_type TEXT NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_date TIMESTAMP,
                verification_source TEXT,
                confidence_score REAL DEFAULT 0.0,
                FOREIGN KEY (output_id) REFERENCES ai_legal_outputs (output_id)
            )
        ''')
        
        # Attorney reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attorney_reviews (
                review_id TEXT PRIMARY KEY,
                output_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                reviewer_email TEXT NOT NULL,
                reviewer_role TEXT NOT NULL,
                review_date TIMESTAMP NOT NULL,
                review_status TEXT NOT NULL,
                accuracy_score REAL,
                completeness_score REAL,
                reliability_score REAL,
                review_comments TEXT,
                corrections_needed TEXT,
                approved_for_use BOOLEAN DEFAULT FALSE,
                client_deliverable BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (output_id) REFERENCES ai_legal_outputs (output_id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outputs_attorney ON ai_legal_outputs (attorney_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outputs_client ON ai_legal_outputs (client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outputs_case ON ai_legal_outputs (case_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_citations_output ON legal_citations (output_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_output ON attorney_reviews (output_id)')
        
        conn.commit()
        conn.close()
    
    def wrap_ai_output(
        self,
        ai_response: str,
        output_type: AIOutputType,
        practice_area: str,
        jurisdiction: JurisdictionType = JurisdictionType.FEDERAL,
        model_name: str = "claude-3-5-sonnet",
        model_version: str = "20241022",
        attorney_id: Optional[str] = None,
        client_id: Optional[str] = None,
        case_id: Optional[str] = None,
        prompt_text: Optional[str] = None,
        confidence_score: float = 0.85
    ) -> Dict[str, Any]:
        """Wrap AI output with comprehensive legal compliance controls"""
        
        output_id = secrets.token_hex(16)
        
        # Extract and validate citations
        citations = self.extract_citations(ai_response)
        verified_citations = sum(1 for c in citations if c.is_verified)
        
        # Analyze content for legal implications
        content_analysis = self._analyze_legal_content(ai_response)
        
        # Determine review requirement
        review_requirement = self._determine_review_requirement(
            output_type, content_analysis, client_id is not None
        )
        
        # Create compliance metadata
        metadata = ComplianceMetadata(
            output_id=output_id,
            generated_at=datetime.now(),
            attorney_id=attorney_id,
            client_id=client_id,
            case_id=case_id,
            practice_area=practice_area,
            jurisdiction=jurisdiction,
            model_name=model_name,
            model_version=model_version,
            prompt_hash=hashlib.sha256((prompt_text or "").encode()).hexdigest()[:16],
            confidence_score=confidence_score,
            review_requirement=review_requirement,
            reviewed_by=None,
            reviewed_at=None,
            approved_by=None,
            approved_at=None,
            contains_legal_advice=content_analysis["contains_legal_advice"],
            contains_privileged_info=content_analysis["contains_privileged_info"],
            contains_client_data=content_analysis["contains_client_data"],
            is_work_product=content_analysis["is_work_product"],
            citation_count=len(citations),
            verified_citations=verified_citations,
            accuracy_rating=None,
            completeness_rating=None
        )
        
        # Generate appropriate disclaimers
        disclaimers = self._generate_disclaimers(metadata, output_type)
        
        # Create wrapped output
        wrapped_output = {
            "output_id": output_id,
            "generated_at": metadata.generated_at.isoformat(),
            "metadata": asdict(metadata),
            
            # Legal disclaimers
            "primary_disclaimer": disclaimers["primary"],
            "jurisdiction_notice": disclaimers["jurisdiction"],
            "ai_disclosure": disclaimers["ai_disclosure"],
            
            # Content
            "original_content": ai_response,
            "formatted_content": self._format_legal_content(ai_response, citations),
            
            # Citations and references
            "citations": [asdict(c) for c in citations],
            "citation_summary": {
                "total_citations": len(citations),
                "verified_citations": verified_citations,
                "citation_types": self._count_citation_types(citations),
                "jurisdictions": list(set(c.jurisdiction.value for c in citations))
            },
            
            # Review requirements
            "requires_attorney_review": review_requirement != ReviewRequirement.NONE,
            "review_requirement": review_requirement.value,
            "review_urgency": self._assess_review_urgency(metadata),
            
            # Content analysis
            "content_analysis": content_analysis,
            "risk_assessment": self._assess_content_risk(metadata, content_analysis),
            
            # Usage restrictions
            "usage_restrictions": self._generate_usage_restrictions(metadata),
            "client_deliverable": metadata.contains_client_data and review_requirement in [ReviewRequirement.REQUIRED, ReviewRequirement.MANDATORY],
            
            # Footer and warnings
            "attorney_consultation_notice": "Consult a qualified attorney for case-specific legal guidance and before making any legal decisions based on this AI-generated content.",
            "verification_required": "All legal authorities and citations should be independently verified before reliance.",
            
            # Compliance tracking
            "compliance_version": "1.0",
            "retention_period_years": 7,  # Standard legal document retention
            "destruction_date": (datetime.now() + timedelta(days=7*365)).isoformat()
        }
        
        # Store in compliance database
        # self._store_ai_output(wrapped_output, ai_response)  # Temporarily disabled
        
        # Log AI output generation
        self.logger.info(
            f"AI legal output wrapped: {output_id} - Type: {output_type.value} - "
            f"Review Required: {review_requirement.value} - Citations: {len(citations)} - "
            f"Attorney: {attorney_id or 'None'}"
        )
        
        return wrapped_output
    
    def extract_citations(self, content: str) -> List[LegalCitation]:
        """Extract and validate legal citations from content"""
        citations = []
        
        for citation_type, patterns in self.citation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    citation_id = secrets.token_hex(8)
                    citation_text = match.group(0)
                    
                    # Parse citation components based on type
                    if citation_type == "case":
                        case_name = f"{match.group(1)} v. {match.group(2)}" if len(match.groups()) >= 2 else None
                        volume = match.group(3) if len(match.groups()) >= 3 else None
                        reporter = match.group(4) if len(match.groups()) >= 4 else None
                        page = match.group(5) if len(match.groups()) >= 5 else None
                        court = None
                        year = None
                    else:
                        case_name = None
                        volume = match.group(1) if len(match.groups()) >= 1 else None
                        reporter = None
                        page = match.group(2) if len(match.groups()) >= 2 else None
                        court = None
                        year = None
                    
                    # Determine jurisdiction (simplified logic)
                    jurisdiction = self._determine_citation_jurisdiction(citation_text, citation_type)
                    
                    # Validate citation (placeholder - would integrate with legal databases)
                    is_verified, confidence_score = self._validate_citation(citation_text, citation_type)
                    
                    citation = LegalCitation(
                        citation_id=citation_id,
                        citation_text=citation_text,
                        case_name=case_name,
                        court=court,
                        year=year,
                        volume=volume,
                        reporter=reporter,
                        page=page,
                        jurisdiction=jurisdiction,
                        citation_type=citation_type,
                        is_verified=is_verified,
                        verification_date=datetime.now() if is_verified else None,
                        verification_source="AI_ANALYSIS" if is_verified else None,
                        confidence_score=confidence_score
                    )
                    
                    citations.append(citation)
        
        # Remove duplicates
        unique_citations = []
        seen_texts = set()
        for citation in citations:
            if citation.citation_text not in seen_texts:
                unique_citations.append(citation)
                seen_texts.add(citation.citation_text)
        
        return unique_citations
    
    def _analyze_legal_content(self, content: str) -> Dict[str, Any]:
        """Analyze content for legal implications and requirements using advanced advice detection"""
        
        # CRITICAL: Use sophisticated legal advice detection
        advice_analysis = legal_advice_detector.analyze_content(content)
        compliance_report = legal_advice_detector.validate_content_compliance(content)
        
        # Legacy indicators for privileged information (still needed)
        privilege_indicators = [
            "confidential", "privileged", "attorney-client", "work product",
            "internal memo", "legal strategy", "client communication"
        ]
        
        # Client data indicators  
        client_data_indicators = [
            "client", "plaintiff", "defendant", "party", "individual",
            "company", "corporation", "entity"
        ]
        
        # Work product indicators
        work_product_indicators = [
            "analysis", "strategy", "opinion", "recommendation",
            "legal theory", "case preparation", "litigation strategy"
        ]
        
        content_lower = content.lower()
        
        return {
            # ENHANCED: Use sophisticated advice detection
            "contains_legal_advice": advice_analysis.classification == ContentClassification.LEGAL_ADVICE,
            "advice_risk_level": advice_analysis.risk_level.value,
            "advice_confidence_score": advice_analysis.confidence_score,
            "advice_classification": advice_analysis.classification.value,
            "problematic_phrases": advice_analysis.problematic_phrases,
            "suggested_corrections": advice_analysis.suggested_corrections,
            "compliance_violations": not compliance_report["is_compliant"],
            
            # Traditional analysis (still important)
            "contains_privileged_info": any(indicator in content_lower for indicator in privilege_indicators),
            "contains_client_data": any(indicator in content_lower for indicator in client_data_indicators),
            "is_work_product": any(indicator in content_lower for indicator in work_product_indicators),
            
            # Content metrics
            "word_count": len(content.split()),
            "complexity_score": self._calculate_complexity_score(content),
            "legal_terminology_density": self._calculate_legal_terminology_density(content),
            
            # Compliance analysis
            "compliance_report": compliance_report,
            "requires_revision": len(advice_analysis.suggested_corrections) > 0,
            "mandatory_attorney_review": advice_analysis.requires_attorney_review
        }
    
    def _determine_review_requirement(
        self,
        output_type: AIOutputType,
        content_analysis: Dict[str, Any],
        has_client_data: bool
    ) -> ReviewRequirement:
        """Determine appropriate attorney review requirement with enhanced advice detection"""
        
        base_requirement = self.review_requirements.get(output_type, ReviewRequirement.RECOMMENDED)
        
        # CRITICAL: Escalate based on legal advice risk level
        advice_risk_level = content_analysis.get("advice_risk_level", "low")
        
        if advice_risk_level == "critical":
            base_requirement = ReviewRequirement.SUPERVISORY  # Highest level required
        elif advice_risk_level == "high":
            base_requirement = max(base_requirement, ReviewRequirement.MANDATORY)
        elif advice_risk_level == "medium":
            base_requirement = max(base_requirement, ReviewRequirement.REQUIRED)
        
        # CRITICAL: Any compliance violations require mandatory review
        if content_analysis.get("compliance_violations", False):
            base_requirement = max(base_requirement, ReviewRequirement.MANDATORY)
        
        # CRITICAL: Legal advice classification requires supervisory review
        if content_analysis["contains_legal_advice"]:
            base_requirement = ReviewRequirement.SUPERVISORY
        
        # Traditional escalation rules (still important)
        if content_analysis["contains_privileged_info"]:
            if base_requirement < ReviewRequirement.MANDATORY:
                base_requirement = ReviewRequirement.MANDATORY
        
        if has_client_data and content_analysis["is_work_product"]:
            base_requirement = max(base_requirement, ReviewRequirement.SUPERVISORY)
        
        # Force review if corrections are suggested
        if content_analysis.get("requires_revision", False):
            base_requirement = max(base_requirement, ReviewRequirement.REQUIRED)
        
        return base_requirement
    
    def _generate_disclaimers(
        self,
        metadata: ComplianceMetadata,
        output_type: AIOutputType
    ) -> Dict[str, str]:
        """Generate appropriate legal disclaimers"""
        
        jurisdiction_templates = self.disclaimer_templates.get(
            metadata.jurisdiction,
            self.disclaimer_templates[JurisdictionType.FEDERAL]
        )
        
        # Select appropriate disclaimer type
        if metadata.contains_privileged_info:
            disclaimer_type = "privileged"
        elif output_type in [AIOutputType.LEGAL_RESEARCH, AIOutputType.CITATION_CHECK]:
            disclaimer_type = "research"
        else:
            disclaimer_type = "standard"
        
        primary_disclaimer = jurisdiction_templates[disclaimer_type]
        
        # AI disclosure
        ai_disclosure = (
            f"This content was generated using AI technology ({metadata.model_name} {metadata.model_version}) "
            f"on {metadata.generated_at.strftime('%Y-%m-%d at %H:%M UTC')}. "
            f"AI-generated content should be reviewed and verified by qualified legal counsel."
        )
        
        # Jurisdiction notice
        jurisdiction_notice = f"Legal analysis applies to {metadata.jurisdiction.value} jurisdiction. Laws and regulations in other jurisdictions may differ significantly."
        
        return {
            "primary": primary_disclaimer,
            "ai_disclosure": ai_disclosure,
            "jurisdiction": jurisdiction_notice
        }
    
    def _store_ai_output(self, wrapped_output: Dict[str, Any], original_content: str):
        """Store AI output in compliance database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata = wrapped_output["metadata"]
        
        try:
            # Store main output record
            cursor.execute('''
                INSERT INTO ai_legal_outputs (
                    output_id, generated_at, attorney_id, client_id, case_id,
                    practice_area, jurisdiction, output_type, model_name, model_version,
                    prompt_hash, confidence_score, review_requirement, contains_legal_advice,
                    contains_privileged_info, contains_client_data, is_work_product,
                    citation_count, verified_citations, original_content, wrapped_content
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                wrapped_output["output_id"], wrapped_output["generated_at"], metadata["attorney_id"],
                metadata["client_id"], metadata["case_id"], metadata["practice_area"],
                metadata["jurisdiction"], metadata["output_type"], metadata["model_name"],
                metadata["model_version"], metadata["prompt_hash"], metadata["confidence_score"],
                wrapped_output["review_requirement"], metadata["contains_legal_advice"],
                metadata["contains_privileged_info"], metadata["contains_client_data"],
                metadata["is_work_product"], metadata["citation_count"],
                metadata["verified_citations"], original_content, json.dumps(wrapped_output)
            ))
            
            # Store citations
            for citation_data in wrapped_output["citations"]:
                cursor.execute('''
                    INSERT INTO legal_citations (
                        citation_id, output_id, citation_text, case_name, court,
                        year, volume, reporter, page, jurisdiction, citation_type,
                        is_verified, verification_date, verification_source, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    citation_data["citation_id"], metadata["output_id"], citation_data["citation_text"],
                    citation_data["case_name"], citation_data["court"], citation_data["year"],
                    citation_data["volume"], citation_data["reporter"], citation_data["page"],
                    citation_data["jurisdiction"], citation_data["citation_type"],
                    citation_data["is_verified"], citation_data["verification_date"],
                    citation_data["verification_source"], citation_data["confidence_score"]
                ))
            
            conn.commit()
            
        finally:
            conn.close()

    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate content complexity score"""
        words = content.split()
        sentences = len([s for s in content.split('.') if s.strip()])
        avg_words_per_sentence = len(words) / max(sentences, 1)
        return min(avg_words_per_sentence / 20.0, 1.0)
    
    def _calculate_legal_terminology_density(self, content: str) -> float:
        """Calculate legal terminology density"""
        legal_terms = [
            'statute', 'regulation', 'court', 'judge', 'jurisdiction', 'precedent',
            'plaintiff', 'defendant', 'contract', 'liability', 'damages', 'appeal'
        ]
        words = content.lower().split()
        legal_word_count = sum(1 for word in words if any(term in word for term in legal_terms))
        return legal_word_count / max(len(words), 1)
    
    def _determine_citation_jurisdiction(self, citation_text: str, citation_type: str) -> JurisdictionType:
        """Determine jurisdiction from citation"""
        if 'U.S.' in citation_text or 'Fed.' in citation_text or 'F.' in citation_text:
            return JurisdictionType.FEDERAL
        else:
            return JurisdictionType.STATE
    
    def _validate_citation(self, citation_text: str, citation_type: str) -> Tuple[bool, float]:
        """Validate citation (placeholder)"""
        # In production, this would check against legal databases
        return True, 0.8
    
    def _count_citation_types(self, citations) -> Dict[str, int]:
        """Count citations by type"""
        counts = {}
        for citation in citations:
            citation_type = citation.citation_type
            counts[citation_type] = counts.get(citation_type, 0) + 1
        return counts
    
    def _format_legal_content(self, content: str, citations) -> str:
        """Format content with citations"""
        return content  # Placeholder
    
    def _assess_review_urgency(self, metadata) -> str:
        """Assess review urgency"""
        if metadata.contains_legal_advice:
            return "urgent"
        elif metadata.contains_client_data:
            return "high"
        else:
            return "normal"
    
    def _assess_content_risk(self, metadata, content_analysis) -> Dict[str, Any]:
        """Assess content risk"""
        risk_score = 0
        if content_analysis['contains_legal_advice']:
            risk_score += 3
        if content_analysis['contains_privileged_info']:
            risk_score += 2
        if content_analysis['contains_client_data']:
            risk_score += 1
        
        return {
            "risk_score": risk_score,
            "risk_level": "high" if risk_score >= 4 else "medium" if risk_score >= 2 else "low"
        }
    
    def _generate_usage_restrictions(self, metadata) -> List[str]:
        """Generate usage restrictions"""
        restrictions = []
        if metadata.contains_legal_advice:
            restrictions.append("Attorney review required before use")
        if metadata.contains_client_data:
            restrictions.append("Not for distribution without client consent")
        if metadata.contains_privileged_info:
            restrictions.append("Privilege protection applies")
        return restrictions

# Global legal compliance wrapper instance
legal_compliance = LegalComplianceWrapper()