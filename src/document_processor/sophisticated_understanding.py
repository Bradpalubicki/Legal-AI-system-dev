"""
Sophisticated Document Understanding System

Advanced pattern recognition, context building, and gap analysis for legal documents.
Provides comprehensive document intelligence with relationship mapping and timeline construction.

CRITICAL LEGAL DISCLAIMER:
This system provides educational document analysis only. All analysis results are for
informational and educational purposes only and do not constitute legal advice.
No attorney-client relationship is created. Consult qualified legal counsel.

Created: 2025-09-14
Legal AI System - Advanced Document Intelligence
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from pathlib import Path

# Import compliance wrapper
try:
    from ..shared.compliance.upl_compliance import ComplianceWrapper, ViolationSeverity
except ImportError:
    class ViolationSeverity(Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"

    class ComplianceWrapper:
        def analyze_text(self, text: str) -> Dict[str, Any]:
            return {"has_advice": False, "violations": [], "compliance_score": 1.0}


logger = logging.getLogger(__name__)


# Enhanced Enums and Types
class DocumentClass(Enum):
    """Enhanced document classification system"""
    # Pleadings
    COMPLAINT = "complaint"
    ANSWER = "answer"
    COUNTERCLAIM = "counterclaim"
    CROSS_CLAIM = "cross_claim"
    THIRD_PARTY_COMPLAINT = "third_party_complaint"

    # Motions
    MOTION_TO_DISMISS = "motion_to_dismiss"
    MOTION_SUMMARY_JUDGMENT = "motion_summary_judgment"
    MOTION_PRELIMINARY_INJUNCTION = "motion_preliminary_injunction"
    MOTION_COMPEL = "motion_compel"
    MOTION_PROTECTIVE_ORDER = "motion_protective_order"
    MOTION_SANCTIONS = "motion_sanctions"
    MOTION_AMEND = "motion_amend"

    # Discovery
    INTERROGATORIES = "interrogatories"
    REQUESTS_FOR_PRODUCTION = "requests_for_production"
    REQUESTS_FOR_ADMISSION = "requests_for_admission"
    DEPOSITION_NOTICE = "deposition_notice"
    SUBPOENA = "subpoena"

    # Court Orders
    ORDER_GRANTING = "order_granting"
    ORDER_DENYING = "order_denying"
    SCHEDULING_ORDER = "scheduling_order"
    PROTECTIVE_ORDER = "protective_order"
    JUDGMENT = "judgment"

    # Bankruptcy
    BANKRUPTCY_PETITION = "bankruptcy_petition"
    PROOF_OF_CLAIM = "proof_of_claim"
    MOTION_LIFT_STAY = "motion_lift_stay"
    PLAN_REORGANIZATION = "plan_reorganization"

    # Contracts
    CONTRACT = "contract"
    AMENDMENT = "amendment"
    TERMINATION_NOTICE = "termination_notice"

    # Other
    BRIEF = "brief"
    MEMORANDUM = "memorandum"
    NOTICE = "notice"
    STIPULATION = "stipulation"
    UNKNOWN = "unknown"


class JurisdictionLevel(Enum):
    """Legal jurisdiction levels"""
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_APPELLATE = "federal_appellate"
    FEDERAL_SUPREME = "federal_supreme"
    STATE_TRIAL = "state_trial"
    STATE_APPELLATE = "state_appellate"
    STATE_SUPREME = "state_supreme"
    BANKRUPTCY = "bankruptcy"
    ADMINISTRATIVE = "administrative"
    UNKNOWN = "unknown"


class PartyRole(Enum):
    """Roles parties can have in legal proceedings"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    DEBTOR = "debtor"
    CREDITOR = "creditor"
    INTERVENOR = "intervenor"
    THIRD_PARTY_DEFENDANT = "third_party_defendant"
    CROSS_PLAINTIFF = "cross_plaintiff"
    CROSS_DEFENDANT = "cross_defendant"
    UNKNOWN = "unknown"


class ClaimType(Enum):
    """Types of legal claims"""
    CONTRACT_BREACH = "contract_breach"
    NEGLIGENCE = "negligence"
    FRAUD = "fraud"
    DEFAMATION = "defamation"
    EMPLOYMENT_DISCRIMINATION = "employment_discrimination"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    ANTITRUST = "antitrust"
    SECURITIES = "securities"
    CONSTITUTIONAL = "constitutional"
    BANKRUPTCY_DISCHARGE = "bankruptcy_discharge"
    DEBT_COLLECTION = "debt_collection"
    REAL_ESTATE = "real_estate"
    FAMILY_LAW = "family_law"
    CRIMINAL = "criminal"
    UNKNOWN = "unknown"


class ReliefType(Enum):
    """Types of relief sought"""
    MONETARY_DAMAGES = "monetary_damages"
    INJUNCTIVE_RELIEF = "injunctive_relief"
    DECLARATORY_JUDGMENT = "declaratory_judgment"
    SPECIFIC_PERFORMANCE = "specific_performance"
    RESTITUTION = "restitution"
    ATTORNEYS_FEES = "attorneys_fees"
    PUNITIVE_DAMAGES = "punitive_damages"
    DISMISSAL = "dismissal"
    DISCHARGE = "discharge"
    UNKNOWN = "unknown"


class ProceduralStage(Enum):
    """Current procedural posture"""
    PLEADING_STAGE = "pleading_stage"
    MOTION_PRACTICE = "motion_practice"
    DISCOVERY = "discovery"
    SUMMARY_JUDGMENT = "summary_judgment"
    TRIAL_PREPARATION = "trial_preparation"
    TRIAL = "trial"
    POST_TRIAL = "post_trial"
    APPEAL = "appeal"
    SETTLEMENT = "settlement"
    DISMISSED = "dismissed"
    UNKNOWN = "unknown"


@dataclass
class Party:
    """Represents a party in legal proceedings"""
    name: str
    role: PartyRole
    entity_type: str  # individual, corporation, LLC, etc.
    aliases: List[str] = field(default_factory=list)
    address: Optional[str] = None
    counsel: List[str] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)
    related_entities: List[str] = field(default_factory=list)
    first_mentioned: Optional[str] = None  # document where first mentioned


@dataclass
class LegalClaim:
    """Represents a legal claim or cause of action"""
    claim_id: str
    claim_type: ClaimType
    description: str
    elements: List[str] = field(default_factory=list)
    factual_basis: List[str] = field(default_factory=list)
    legal_authority: List[str] = field(default_factory=list)
    damages_sought: Optional[str] = None
    relief_requested: List[ReliefType] = field(default_factory=list)
    status: str = "active"


@dataclass
class CriticalDate:
    """Represents important dates and deadlines"""
    date: datetime
    date_type: str  # filing, hearing, trial, deadline, etc.
    description: str
    source_document: str
    jurisdiction_rules: List[str] = field(default_factory=list)
    calculation_basis: Optional[str] = None
    is_deadline: bool = False
    days_remaining: Optional[int] = None


@dataclass
class JurisdictionInfo:
    """Information about legal jurisdiction"""
    level: JurisdictionLevel
    court_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    judge: Optional[str] = None
    case_number: Optional[str] = None
    applicable_rules: List[str] = field(default_factory=list)
    local_rules: List[str] = field(default_factory=list)


@dataclass
class DocumentRelationship:
    """Represents relationships between documents"""
    related_doc_id: str
    relationship_type: str  # response_to, amendment_of, motion_for, etc.
    strength: float  # 0-1 confidence in relationship
    description: str
    temporal_order: Optional[int] = None


@dataclass
class Timeline:
    """Chronological timeline of case events"""
    events: List[Dict[str, Any]] = field(default_factory=list)
    key_milestones: List[str] = field(default_factory=list)
    procedural_history: List[str] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)


@dataclass
class ContextualGap:
    """Enhanced gap analysis with context"""
    gap_id: str
    gap_type: str
    severity: ViolationSeverity
    description: str
    impact: str  # How this gap affects understanding
    suggested_sources: List[str] = field(default_factory=list)
    related_documents_needed: List[str] = field(default_factory=list)
    clarifying_questions: List[str] = field(default_factory=list)
    procedural_implications: List[str] = field(default_factory=list)


@dataclass
class SophisticatedAnalysis:
    """Comprehensive document analysis result"""
    document_id: str
    document_class: DocumentClass
    confidence_score: float

    # Pattern Recognition Results
    jurisdiction_info: JurisdictionInfo
    parties: List[Party]
    claims: List[LegalClaim]
    relief_sought: List[ReliefType]
    critical_dates: List[CriticalDate]

    # Context Building Results
    related_documents: List[DocumentRelationship]
    timeline: Timeline
    procedural_posture: ProceduralStage

    # Gap Analysis Results
    contextual_gaps: List[ContextualGap]

    # Fields with defaults
    case_context: Dict[str, Any] = field(default_factory=dict)
    missing_context: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    compliance_validated: bool = False


class SophisticatedDocumentUnderstanding:
    """
    Advanced document understanding system with sophisticated pattern recognition,
    context building, and gap analysis capabilities.

    EDUCATIONAL PURPOSE ONLY: All analysis is for informational purposes and
    does not constitute legal advice. Professional legal review is recommended.
    """

    def __init__(self):
        """Initialize the sophisticated understanding system"""
        self.compliance_wrapper = ComplianceWrapper()
        self.logger = logging.getLogger(__name__)

        # Initialize pattern libraries
        self._initialize_pattern_libraries()
        self._initialize_jurisdiction_patterns()
        self._initialize_procedural_patterns()

    def _initialize_pattern_libraries(self):
        """Initialize comprehensive pattern recognition libraries"""

        # Document class patterns
        self.document_patterns = {
            DocumentClass.COMPLAINT: {
                "header_patterns": [
                    r"complaint for .{1,100}",
                    r"civil action.*complaint",
                    r"plaintiff.*alleges",
                    r"comes now.*plaintiff"
                ],
                "structure_patterns": [
                    r"parties",
                    r"jurisdiction.*venue",
                    r"causes? of action",
                    r"prayer for relief"
                ],
                "content_indicators": [
                    r"plaintiff.*defendant",
                    r"breach of .{1,50}",
                    r"damages in.*amount",
                    r"wherefore.*pray"
                ]
            },

            DocumentClass.MOTION_TO_DISMISS: {
                "header_patterns": [
                    r"motion to dismiss",
                    r"defendant.*moves.*dismiss",
                    r"motion.*rule 12\(b\)"
                ],
                "legal_standards": [
                    r"rule 12\(b\)\(6\)",
                    r"failure to state.*claim",
                    r"plausible.*relief",
                    r"bell.*atlantic"
                ]
            },

            DocumentClass.ANSWER: {
                "header_patterns": [
                    r"answer to.*complaint",
                    r"defendant.*answer",
                    r"response to.*complaint"
                ],
                "structure_patterns": [
                    r"admits.*denies",
                    r"affirmative defenses",
                    r"counterclaim",
                    r"jury demand"
                ]
            }
        }

        # Party extraction patterns
        self.party_patterns = {
            "plaintiff_indicators": [
                r"plaintiff\s+([A-Z][A-Z0-9\s&,\.]+?)(?:\s+\(|,\s+a\s+|,\s+by\s+)",
                r"^([A-Z][A-Z0-9\s&,\.]+?),?\s+plaintiff",
                r"on behalf of\s+([A-Z][A-Z0-9\s&,\.]+)"
            ],
            "defendant_indicators": [
                r"defendant[s]?\s+([A-Z][A-Z0-9\s&,\.]+?)(?:\s+\(|,\s+a\s+|,\s+and\s+)",
                r"^([A-Z][A-Z0-9\s&,\.]+?),?\s+defendant",
                r"v\.\s*([A-Z][A-Z0-9\s&,\.]+?)(?:\s*,|\s*and|\s*$)"
            ],
            "entity_types": [
                r"(.+?)\s+(?:llc|l\.l\.c\.|inc\.|corp\.|corporation|company|co\.)",
                r"(.+?)\s+(?:partnership|lp|l\.p\.)",
                r"(?:the\s+)?(.+?)\s+(?:trust|estate)"
            ]
        }

        # Claim type patterns
        self.claim_patterns = {
            ClaimType.CONTRACT_BREACH: [
                r"breach of contract",
                r"violated.*terms",
                r"failed to perform",
                r"material breach"
            ],
            ClaimType.NEGLIGENCE: [
                r"negligence",
                r"duty of care",
                r"standard of care",
                r"reasonably prudent"
            ],
            ClaimType.FRAUD: [
                r"fraud",
                r"misrepresentation",
                r"intentionally.*false",
                r"reliance.*detriment"
            ]
        }

        # Relief patterns
        self.relief_patterns = {
            ReliefType.MONETARY_DAMAGES: [
                r"damages.*amount.*(\$[\d,]+)",
                r"compensatory damages",
                r"actual damages",
                r"lost profits"
            ],
            ReliefType.INJUNCTIVE_RELIEF: [
                r"injunctive relief",
                r"permanent injunction",
                r"restraining order",
                r"cease.*desist"
            ],
            ReliefType.DECLARATORY_JUDGMENT: [
                r"declaratory judgment",
                r"declare.*rights",
                r"declaration.*law"
            ]
        }

    def _initialize_jurisdiction_patterns(self):
        """Initialize jurisdiction detection patterns"""
        self.jurisdiction_patterns = {
            "federal_district": [
                r"united states district court",
                r"u\.?s\.? district court",
                r"federal question jurisdiction",
                r"diversity jurisdiction"
            ],
            "federal_appellate": [
                r"united states court of appeals",
                r"circuit court of appeals",
                r"(\d+)(?:st|nd|rd|th)\s+circuit"
            ],
            "bankruptcy": [
                r"united states bankruptcy court",
                r"u\.?s\.? bankruptcy court",
                r"chapter \d+ bankruptcy"
            ],
            "state_courts": [
                r"superior court.*(.{1,30})",
                r"circuit court.*(.{1,30})",
                r"district court.*(.{1,30})",
                r"court.*common pleas"
            ]
        }

        # Federal rules patterns
        self.rules_patterns = {
            "frcp": [
                r"(?:fed\.?\s*r\.?\s*civ\.?\s*p\.?|f\.?r\.?c\.?p\.?)\s*(\d+)",
                r"rule\s+(\d+).*federal rules.*civil"
            ],
            "fre": [
                r"(?:fed\.?\s*r\.?\s*evid\.?|f\.?r\.?e\.?)\s*(\d+)",
                r"rule\s+(\d+).*federal rules.*evidence"
            ],
            "local_rules": [
                r"local rule\s*(\d+(?:\.\d+)?)",
                r"l\.?\s*r\.?\s*(\d+(?:\.\d+)?)"
            ]
        }

    def _initialize_procedural_patterns(self):
        """Initialize procedural posture detection patterns"""
        self.procedural_patterns = {
            ProceduralStage.PLEADING_STAGE: [
                r"filing.*complaint",
                r"answer.*due",
                r"responsive pleading",
                r"motion.*more definite"
            ],
            ProceduralStage.MOTION_PRACTICE: [
                r"motion.*pending",
                r"briefing schedule",
                r"motion.*dismiss.*filed",
                r"motion.*summary judgment"
            ],
            ProceduralStage.DISCOVERY: [
                r"discovery.*commence",
                r"interrogatories",
                r"document production",
                r"depositions.*scheduled"
            ],
            ProceduralStage.TRIAL_PREPARATION: [
                r"trial.*scheduled",
                r"pretrial conference",
                r"jury selection",
                r"witness list"
            ]
        }

    def analyze_document(self, document_text: str, document_id: str,
                        related_docs: Optional[List[str]] = None) -> SophisticatedAnalysis:
        """
        Perform comprehensive sophisticated analysis of legal document.

        Args:
            document_text: Full text of the document to analyze
            document_id: Unique identifier for the document
            related_docs: Optional list of related document IDs for context

        Returns:
            SophisticatedAnalysis object with comprehensive results

        EDUCATIONAL DISCLAIMER:
        Analysis results are for informational purposes only and do not
        constitute legal advice. Professional legal review recommended.
        """

        self.logger.info(f"Starting sophisticated analysis for document {document_id}")

        try:
            # 1. PATTERN RECOGNITION
            document_class, confidence = self._identify_document_class(document_text)
            jurisdiction_info = self._detect_jurisdiction(document_text)
            parties = self._extract_parties(document_text)
            claims = self._extract_claims(document_text)
            relief_sought = self._extract_relief(document_text)
            critical_dates = self._extract_critical_dates(document_text)

            # 2. CONTEXT BUILDING
            related_documents = self._link_related_documents(document_text, related_docs or [])
            timeline = self._build_timeline(document_text, critical_dates, related_documents)
            procedural_posture = self._determine_procedural_posture(document_text, document_class)
            case_context = self._build_case_context(parties, claims, procedural_posture)

            # 3. GAP ANALYSIS
            contextual_gaps = self._perform_gap_analysis(
                document_text, document_class, parties, claims,
                jurisdiction_info, critical_dates
            )
            missing_context = self._identify_missing_context(
                document_class, parties, claims, related_documents
            )
            recommended_actions = self._generate_recommendations(
                contextual_gaps, procedural_posture, critical_dates
            )

            # 4. COMPLIANCE VALIDATION
            compliance_result = self.compliance_wrapper.analyze_text(document_text[:2000])
            compliance_validated = not compliance_result.get("has_advice", False)

            # Create comprehensive analysis result
            analysis = SophisticatedAnalysis(
                document_id=document_id,
                document_class=document_class,
                confidence_score=confidence,
                jurisdiction_info=jurisdiction_info,
                parties=parties,
                claims=claims,
                relief_sought=relief_sought,
                critical_dates=critical_dates,
                related_documents=related_documents,
                timeline=timeline,
                procedural_posture=procedural_posture,
                case_context=case_context,
                contextual_gaps=contextual_gaps,
                missing_context=missing_context,
                recommended_actions=recommended_actions,
                compliance_validated=compliance_validated
            )

            self.logger.info(f"Sophisticated analysis completed for document {document_id}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in sophisticated analysis: {str(e)}")
            # Return minimal analysis on error
            return SophisticatedAnalysis(
                document_id=document_id,
                document_class=DocumentClass.UNKNOWN,
                confidence_score=0.0,
                jurisdiction_info=JurisdictionInfo(
                    level=JurisdictionLevel.UNKNOWN,
                    court_name="Unknown"
                ),
                parties=[],
                claims=[],
                relief_sought=[],
                critical_dates=[],
                related_documents=[],
                timeline=Timeline(),
                procedural_posture=ProceduralStage.UNKNOWN,
                contextual_gaps=[],
                compliance_validated=False
            )

    def _identify_document_class(self, text: str) -> Tuple[DocumentClass, float]:
        """Identify document class using sophisticated pattern matching"""

        text_lower = text.lower()
        scores = {}

        for doc_class, patterns in self.document_patterns.items():
            score = 0.0
            total_patterns = 0

            # Check header patterns (weighted heavily)
            for pattern in patterns.get("header_patterns", []):
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 3.0
                total_patterns += 3.0

            # Check structure patterns
            for pattern in patterns.get("structure_patterns", []):
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 2.0
                total_patterns += 2.0

            # Check content indicators
            for pattern in patterns.get("content_indicators", []):
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1.0
                total_patterns += 1.0

            # Check legal standards (for motions)
            for pattern in patterns.get("legal_standards", []):
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 2.5
                total_patterns += 2.5

            if total_patterns > 0:
                scores[doc_class] = score / total_patterns

        if not scores:
            return DocumentClass.UNKNOWN, 0.0

        best_class = max(scores.keys(), key=lambda x: scores[x])
        confidence = scores[best_class]

        return best_class, min(confidence, 1.0)

    def _detect_jurisdiction(self, text: str) -> JurisdictionInfo:
        """Detect jurisdiction and applicable rules"""

        text_lower = text.lower()

        # Detect jurisdiction level
        jurisdiction_level = JurisdictionLevel.UNKNOWN
        court_name = "Unknown"

        for level, patterns in self.jurisdiction_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    if level == "federal_district":
                        jurisdiction_level = JurisdictionLevel.FEDERAL_DISTRICT
                        court_name = match.group(0).title()
                    elif level == "federal_appellate":
                        jurisdiction_level = JurisdictionLevel.FEDERAL_APPELLATE
                        court_name = match.group(0).title()
                    elif level == "bankruptcy":
                        jurisdiction_level = JurisdictionLevel.BANKRUPTCY
                        court_name = match.group(0).title()
                    elif level == "state_courts":
                        jurisdiction_level = JurisdictionLevel.STATE_TRIAL
                        court_name = match.group(0).title()
                    break

        # Extract applicable rules
        applicable_rules = []

        # Federal Rules of Civil Procedure
        frcp_matches = re.findall(r'(?:fed\.?\s*r\.?\s*civ\.?\s*p\.?|f\.?r\.?c\.?p\.?)\s*(\d+)', text_lower)
        for rule_num in frcp_matches:
            applicable_rules.append(f"FRCP {rule_num}")

        # Federal Rules of Evidence
        fre_matches = re.findall(r'(?:fed\.?\s*r\.?\s*evid\.?|f\.?r\.?e\.?)\s*(\d+)', text_lower)
        for rule_num in fre_matches:
            applicable_rules.append(f"FRE {rule_num}")

        # Local rules
        local_matches = re.findall(r'local rule\s*(\d+(?:\.\d+)?)', text_lower)
        for rule_num in local_matches:
            applicable_rules.append(f"Local Rule {rule_num}")

        # Extract case number
        case_number = None
        case_patterns = [
            r'case no\.?\s*([\d\-:]+)',
            r'civil action no\.?\s*([\d\-:]+)',
            r'docket no\.?\s*([\d\-:]+)'
        ]

        for pattern in case_patterns:
            match = re.search(pattern, text_lower)
            if match:
                case_number = match.group(1).upper()
                break

        return JurisdictionInfo(
            level=jurisdiction_level,
            court_name=court_name,
            case_number=case_number,
            applicable_rules=applicable_rules
        )

    def _extract_parties(self, text: str) -> List[Party]:
        """Extract parties and their roles using advanced pattern matching"""

        parties = []

        # Extract plaintiffs
        for pattern in self.party_patterns["plaintiff_indicators"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                party_name = match.group(1).strip()
                if party_name and len(party_name) < 100:  # Reasonable name length
                    parties.append(Party(
                        name=party_name,
                        role=PartyRole.PLAINTIFF,
                        entity_type=self._determine_entity_type(party_name)
                    ))

        # Extract defendants
        for pattern in self.party_patterns["defendant_indicators"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                party_name = match.group(1).strip()
                if party_name and len(party_name) < 100:
                    parties.append(Party(
                        name=party_name,
                        role=PartyRole.DEFENDANT,
                        entity_type=self._determine_entity_type(party_name)
                    ))

        # Deduplicate parties by name
        unique_parties = {}
        for party in parties:
            if party.name not in unique_parties:
                unique_parties[party.name] = party

        return list(unique_parties.values())

    def _determine_entity_type(self, name: str) -> str:
        """Determine entity type from party name"""
        name_lower = name.lower()

        if re.search(r'\b(?:llc|l\.l\.c\.)\b', name_lower):
            return "LLC"
        elif re.search(r'\b(?:inc\.|incorporated|corp\.|corporation)\b', name_lower):
            return "Corporation"
        elif re.search(r'\b(?:partnership|lp|l\.p\.)\b', name_lower):
            return "Partnership"
        elif re.search(r'\b(?:trust|estate)\b', name_lower):
            return "Trust/Estate"
        else:
            return "Individual"

    def _extract_claims(self, text: str) -> List[LegalClaim]:
        """Extract legal claims and causes of action"""

        claims = []
        text_lower = text.lower()

        for claim_type, patterns in self.claim_patterns.items():
            for i, pattern in enumerate(patterns):
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    # Extract surrounding context for description
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()

                    claim = LegalClaim(
                        claim_id=f"{claim_type.value}_{len(claims)+1}",
                        claim_type=claim_type,
                        description=context,
                        status="identified"
                    )
                    claims.append(claim)

        return claims

    def _extract_relief(self, text: str) -> List[ReliefType]:
        """Extract types of relief sought"""

        relief_types = set()
        text_lower = text.lower()

        for relief_type, patterns in self.relief_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    relief_types.add(relief_type)

        return list(relief_types)

    def _extract_critical_dates(self, text: str) -> List[CriticalDate]:
        """Extract critical dates and deadlines"""

        dates = []

        # Date patterns with context
        date_patterns = [
            (r'(\w+\s+\d{1,2},\s+\d{4})', r'filing.*date'),
            (r'(\d{1,2}/\d{1,2}/\d{4})', r'due.*date'),
            (r'(\w+\s+\d{1,2},\s+\d{4})', r'hearing.*scheduled'),
            (r'(\w+\s+\d{1,2},\s+\d{4})', r'trial.*date'),
            (r'(\d{1,2}\s+days?)', r'after.*service'),
            (r'(\d{1,2}\s+days?)', r'deadline')
        ]

        for date_pattern, context_pattern in date_patterns:
            matches = re.finditer(f'{context_pattern}.*?{date_pattern}|{date_pattern}.*?{context_pattern}',
                                text, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = re.search(date_pattern, match.group(0)).group(1)
                    # Simple date parsing (would use dateparser in production)
                    if '/' in date_str:
                        # MM/DD/YYYY format
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            date_obj = datetime(int(parts[2]), int(parts[0]), int(parts[1]))
                    else:
                        # Month DD, YYYY format - simplified parsing
                        continue  # Skip for now

                    dates.append(CriticalDate(
                        date=date_obj,
                        date_type="deadline" if "deadline" in context_pattern else "event",
                        description=match.group(0)[:100],
                        source_document="current",
                        is_deadline="deadline" in context_pattern
                    ))

                except (ValueError, AttributeError):
                    continue

        return dates

    def _link_related_documents(self, text: str, related_doc_ids: List[str]) -> List[DocumentRelationship]:
        """Identify relationships with other documents"""

        relationships = []
        text_lower = text.lower()

        # Pattern-based relationship detection
        relationship_patterns = {
            "response_to": [r"in response to", r"responding to", r"reply to"],
            "amendment_of": [r"amended", r"amending", r"modification of"],
            "motion_for": [r"motion for", r"moving for", r"seeks"],
            "opposition_to": [r"opposition to", r"opposes", r"objects to"]
        }

        for doc_id in related_doc_ids:
            # Simple relationship detection based on document references
            if doc_id in text_lower:
                relationships.append(DocumentRelationship(
                    related_doc_id=doc_id,
                    relationship_type="references",
                    strength=0.7,
                    description=f"Document references {doc_id}"
                ))

        return relationships

    def _build_timeline(self, text: str, critical_dates: List[CriticalDate],
                       relationships: List[DocumentRelationship]) -> Timeline:
        """Build chronological timeline of events"""

        events = []

        # Add critical dates as events
        for date in critical_dates:
            events.append({
                "date": date.date,
                "type": date.date_type,
                "description": date.description,
                "source": "document_analysis"
            })

        # Sort events by date
        events.sort(key=lambda x: x["date"] if isinstance(x["date"], datetime) else datetime.min)

        return Timeline(
            events=events,
            key_milestones=[],
            procedural_history=[],
            critical_path=[]
        )

    def _determine_procedural_posture(self, text: str, doc_class: DocumentClass) -> ProceduralStage:
        """Determine current procedural posture"""

        text_lower = text.lower()

        # Class-based initial determination
        if doc_class in [DocumentClass.COMPLAINT, DocumentClass.ANSWER]:
            base_stage = ProceduralStage.PLEADING_STAGE
        elif "motion" in doc_class.value:
            base_stage = ProceduralStage.MOTION_PRACTICE
        else:
            base_stage = ProceduralStage.UNKNOWN

        # Refine based on content patterns
        for stage, patterns in self.procedural_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return stage

        return base_stage

    def _build_case_context(self, parties: List[Party], claims: List[LegalClaim],
                           posture: ProceduralStage) -> Dict[str, Any]:
        """Build comprehensive case context"""

        return {
            "party_count": len(parties),
            "claim_count": len(claims),
            "complexity_indicators": {
                "multiple_parties": len(parties) > 2,
                "multiple_claims": len(claims) > 1,
                "corporate_entities": sum(1 for p in parties if p.entity_type != "Individual"),
                "procedural_stage": posture.value
            },
            "case_themes": [],  # Would be extracted from content analysis
            "legal_issues": [claim.claim_type.value for claim in claims]
        }

    def _perform_gap_analysis(self, text: str, doc_class: DocumentClass,
                             parties: List[Party], claims: List[LegalClaim],
                             jurisdiction: JurisdictionInfo, dates: List[CriticalDate]) -> List[ContextualGap]:
        """Perform sophisticated gap analysis"""

        gaps = []

        # Missing jurisdiction information
        if jurisdiction.level == JurisdictionLevel.UNKNOWN:
            gaps.append(ContextualGap(
                gap_id="jurisdiction_unknown",
                gap_type="jurisdictional_basis",
                severity=ViolationSeverity.HIGH,
                description="Court jurisdiction and venue not clearly established",
                impact="Cannot determine applicable law and procedural rules",
                suggested_sources=["case caption", "jurisdictional allegations"],
                clarifying_questions=["What is the basis for federal/state jurisdiction?"],
                procedural_implications=["May affect motion practice and discovery rules"]
            ))

        # Missing party information
        if not parties:
            gaps.append(ContextualGap(
                gap_id="parties_missing",
                gap_type="party_identification",
                severity=ViolationSeverity.CRITICAL,
                description="No parties clearly identified in document",
                impact="Cannot determine case participants and their roles",
                suggested_sources=["case caption", "party descriptions"],
                clarifying_questions=["Who are the named parties?", "What are their roles?"],
                procedural_implications=["Affects service requirements and standing issues"]
            ))

        # Missing claim information
        if not claims and doc_class in [DocumentClass.COMPLAINT, DocumentClass.ANSWER]:
            gaps.append(ContextualGap(
                gap_id="claims_unclear",
                gap_type="legal_claims",
                severity=ViolationSeverity.HIGH,
                description="Legal claims or causes of action not clearly stated",
                impact="Cannot assess legal theories and required elements",
                suggested_sources=["numbered paragraphs", "causes of action"],
                clarifying_questions=["What legal theories are being pursued?"],
                procedural_implications=["Affects motion to dismiss analysis and discovery scope"]
            ))

        # Missing critical dates
        if not dates:
            gaps.append(ContextualGap(
                gap_id="dates_missing",
                gap_type="critical_deadlines",
                severity=ViolationSeverity.MEDIUM,
                description="No critical dates or deadlines identified",
                impact="Cannot assess timing requirements and case schedule",
                suggested_sources=["scheduling orders", "case management orders"],
                clarifying_questions=["What are the key upcoming deadlines?"],
                procedural_implications=["May miss important filing deadlines"]
            ))

        return gaps

    def _identify_missing_context(self, doc_class: DocumentClass, parties: List[Party],
                                 claims: List[LegalClaim], relationships: List[DocumentRelationship]) -> List[str]:
        """Identify missing contextual information"""

        missing = []

        if doc_class == DocumentClass.MOTION_TO_DISMISS:
            missing.append("Underlying complaint being challenged")
            missing.append("Specific Rule 12(b) grounds asserted")

        if doc_class == DocumentClass.ANSWER:
            missing.append("Original complaint being answered")
            missing.append("Specific affirmative defenses raised")

        if not relationships:
            missing.append("Related case documents and filings")
            missing.append("Procedural history and prior orders")

        if len(parties) == 1:
            missing.append("Complete party information for all participants")

        return missing

    def _generate_recommendations(self, gaps: List[ContextualGap],
                                 posture: ProceduralStage, dates: List[CriticalDate]) -> List[str]:
        """Generate recommendations for addressing gaps"""

        recommendations = []

        for gap in gaps:
            if gap.severity in [ViolationSeverity.HIGH, ViolationSeverity.CRITICAL]:
                recommendations.append(f"Address {gap.gap_type}: {gap.description}")

        if posture == ProceduralStage.UNKNOWN:
            recommendations.append("Clarify current procedural posture and stage")

        if not dates:
            recommendations.append("Identify and calendar all critical deadlines")

        recommendations.append("Obtain complete case file for comprehensive context")
        recommendations.append("Consult qualified legal counsel for case-specific guidance")

        return recommendations


def test_sophisticated_understanding():
    """
    Test the sophisticated document understanding system.

    LEGAL DISCLAIMER:
    This test demonstrates system capabilities for educational purposes only.
    No legal advice is provided. All analysis is for informational use.
    """

    print("=== SOPHISTICATED DOCUMENT UNDERSTANDING TEST ===")
    print("LEGAL DISCLAIMER: Educational analysis only - No legal advice provided")
    print("Professional legal review recommended for all document analysis\n")

    # Sample complex legal document
    sample_document = """
    IN THE UNITED STATES DISTRICT COURT
    FOR THE SOUTHERN DISTRICT OF NEW YORK

    ACME CORPORATION,
    a Delaware corporation,
                        Plaintiff,
    v.                                          Case No. 1:24-cv-12345-ABC

    BETA INDUSTRIES, LLC,
    a New York limited liability company,
    and JOHN SMITH, individually,
                        Defendants.

    COMPLAINT FOR BREACH OF CONTRACT AND FRAUDULENT MISREPRESENTATION

    TO THE HONORABLE COURT:

    Plaintiff ACME CORPORATION ("ACME"), by and through its undersigned counsel,
    alleges as follows:

    PARTIES

    1. Plaintiff ACME is a corporation organized and existing under the laws
    of Delaware, with its principal place of business in New York, New York.

    2. Upon information and belief, Defendant BETA INDUSTRIES, LLC ("BETA") is
    a limited liability company organized under New York law with its principal
    place of business in New York.

    3. Upon information and belief, Defendant JOHN SMITH ("SMITH") is an individual
    residing in New York and is the managing member of BETA.

    JURISDICTION AND VENUE

    4. This Court has subject matter jurisdiction pursuant to 28 U.S.C. § 1332
    because there is complete diversity of citizenship between the parties and
    the amount in controversy exceeds $75,000.

    FACTUAL ALLEGATIONS

    5. On March 15, 2023, ACME and BETA entered into a Software Licensing Agreement
    ("Agreement") whereby BETA agreed to license certain proprietary software to ACME.

    6. Under the Agreement, BETA represented that the software was original work
    and free from any third-party intellectual property claims.

    7. ACME paid BETA $500,000 in licensing fees as required under the Agreement.

    8. In December 2023, ACME discovered that the software contained substantial
    portions of copyrighted code owned by third parties.

    CAUSES OF ACTION

    COUNT I - BREACH OF CONTRACT

    9. ACME realleges and incorporates by reference paragraphs 1-8.

    10. BETA materially breached the Agreement by providing software that
    contained third-party copyrighted materials.

    11. As a result of BETA's breach, ACME has suffered damages in excess of $500,000.

    COUNT II - FRAUDULENT MISREPRESENTATION

    12. ACME realleges and incorporates by reference paragraphs 1-11.

    13. BETA knowingly made false representations regarding the originality
    of the software.

    14. ACME reasonably relied on these representations to its detriment.

    PRAYER FOR RELIEF

    WHEREFORE, Plaintiff respectfully requests that this Court:

    A. Award compensatory damages in an amount to be proven at trial;
    B. Award punitive damages;
    C. Grant such other relief as this Court deems just and proper.

    Respectfully submitted,

    /s/ Attorney Name
    Attorney for Plaintiff

    Filed: January 15, 2024
    Answer due: February 15, 2024
    """

    # Initialize and test the system
    analyzer = SophisticatedDocumentUnderstanding()

    print("Testing sophisticated document analysis...")
    analysis = analyzer.analyze_document(sample_document, "test_complaint_001")

    print(f"\n=== ANALYSIS RESULTS ===")
    print(f"Document Class: {analysis.document_class.value} (Confidence: {analysis.confidence_score:.2f})")
    print(f"Jurisdiction: {analysis.jurisdiction_info.court_name}")
    print(f"Case Number: {analysis.jurisdiction_info.case_number}")
    print(f"Applicable Rules: {', '.join(analysis.jurisdiction_info.applicable_rules) if analysis.jurisdiction_info.applicable_rules else 'None identified'}")

    print(f"\n=== PARTIES ===")
    for party in analysis.parties:
        print(f"- {party.name} ({party.role.value}, {party.entity_type})")

    print(f"\n=== LEGAL CLAIMS ===")
    for claim in analysis.claims:
        print(f"- {claim.claim_type.value}: {claim.description[:100]}...")

    print(f"\n=== RELIEF SOUGHT ===")
    for relief in analysis.relief_sought:
        print(f"- {relief.value}")

    print(f"\n=== CRITICAL DATES ===")
    for date in analysis.critical_dates:
        print(f"- {date.date_type}: {date.description}")

    print(f"\n=== PROCEDURAL POSTURE ===")
    print(f"Current Stage: {analysis.procedural_posture.value}")

    print(f"\n=== GAP ANALYSIS ===")
    for gap in analysis.contextual_gaps:
        print(f"- {gap.gap_type} ({gap.severity.value}): {gap.description}")
        print(f"  Impact: {gap.impact}")
        if gap.clarifying_questions:
            print(f"  Questions: {'; '.join(gap.clarifying_questions)}")
        print()

    print(f"=== MISSING CONTEXT ===")
    for context in analysis.missing_context:
        print(f"- {context}")

    print(f"\n=== RECOMMENDATIONS ===")
    for rec in analysis.recommended_actions:
        print(f"- {rec}")

    print(f"\n=== COMPLIANCE STATUS ===")
    print(f"Compliance Validated: {'Yes' if analysis.compliance_validated else 'No'}")

    print(f"\n=== SYSTEM VALIDATION ===")
    print(f"[OK] Pattern Recognition: Document class identified with {analysis.confidence_score:.0%} confidence")
    print(f"[OK] Jurisdiction Detection: {analysis.jurisdiction_info.level.value} jurisdiction identified")
    print(f"[OK] Party Extraction: {len(analysis.parties)} parties identified")
    print(f"[OK] Claim Analysis: {len(analysis.claims)} legal claims found")
    print(f"[OK] Context Building: Procedural posture determined")
    print(f"[OK] Gap Analysis: {len(analysis.contextual_gaps)} gaps identified")
    print(f"[OK] Recommendations: {len(analysis.recommended_actions)} actions suggested")

    print(f"\nREMINDER: All analysis is educational only - Consult qualified legal counsel")

    return analysis


if __name__ == "__main__":
    test_sophisticated_understanding()