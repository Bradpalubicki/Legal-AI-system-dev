"""
Legal Document Extraction Patterns

Comprehensive regex patterns for extracting:
- Case numbers (federal, state, bankruptcy)
- Party names and roles
- Legal citations (cases, statutes, rules)
- Dates and deadlines
- Dollar amounts and damages
- Attorney information

EDUCATIONAL CONTENT DISCLAIMER: This module provides informational analysis
of legal documents and does not constitute legal advice.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Pattern, Match
from enum import Enum


# ============================================================================
# CASE NUMBER PATTERNS
# ============================================================================

class CourtType(Enum):
    """Types of courts"""
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_APPELLATE = "federal_appellate"
    FEDERAL_BANKRUPTCY = "federal_bankruptcy"
    SUPREME_COURT = "supreme_court"
    STATE_TRIAL = "state_trial"
    STATE_APPELLATE = "state_appellate"
    STATE_SUPREME = "state_supreme"
    ADMINISTRATIVE = "administrative"
    UNKNOWN = "unknown"


@dataclass
class CaseNumberPattern:
    """Pattern for matching case numbers"""
    name: str
    pattern: str
    court_type: CourtType
    example: str
    extract_groups: List[str]


# Federal District Court patterns
FEDERAL_DISTRICT_PATTERNS = [
    CaseNumberPattern(
        name="federal_cv",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{1,2}):(\d{2})-cv-(\d{4,5})(?:-([A-Z]{2,4}))?(?:-([A-Z]{2,4}))?",
        court_type=CourtType.FEDERAL_DISTRICT,
        example="2:24-cv-01234-ABC-XYZ",
        extract_groups=["district", "year", "number", "judge_initials", "magistrate_initials"]
    ),
    CaseNumberPattern(
        name="federal_cr",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{1,2}):(\d{2})-cr-(\d{4,5})(?:-([A-Z]{2,4}))?",
        court_type=CourtType.FEDERAL_DISTRICT,
        example="1:23-cr-00567-JKL",
        extract_groups=["district", "year", "number", "judge_initials"]
    ),
    CaseNumberPattern(
        name="federal_mc",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{1,2}):(\d{2})-mc-(\d{4,5})",
        court_type=CourtType.FEDERAL_DISTRICT,
        example="3:24-mc-00123",
        extract_groups=["district", "year", "number"]
    ),
    CaseNumberPattern(
        name="federal_mj",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{1,2}):(\d{2})-mj-(\d{4,5})",
        court_type=CourtType.FEDERAL_DISTRICT,
        example="2:24-mj-00456",
        extract_groups=["district", "year", "number"]
    ),
]

# Bankruptcy Court patterns
BANKRUPTCY_PATTERNS = [
    CaseNumberPattern(
        name="bankruptcy_case",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{1,2})-(\d{5})(?:-([A-Z]{2,4}))?",
        court_type=CourtType.FEDERAL_BANKRUPTCY,
        example="24-12345-ABC",
        extract_groups=["year", "number", "judge_initials"]
    ),
    CaseNumberPattern(
        name="bankruptcy_bk",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{1,2}):(\d{2})-bk-(\d{4,5})",
        court_type=CourtType.FEDERAL_BANKRUPTCY,
        example="2:24-bk-01234",
        extract_groups=["district", "year", "number"]
    ),
    CaseNumberPattern(
        name="bankruptcy_ap",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{1,2}):(\d{2})-ap-(\d{4,5})",
        court_type=CourtType.FEDERAL_BANKRUPTCY,
        example="2:24-ap-00567",
        extract_groups=["district", "year", "number"]
    ),
]

# State Court patterns (examples for major states)
STATE_COURT_PATTERNS = [
    # California
    CaseNumberPattern(
        name="california_superior",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?([A-Z]{2,4})(\d{6,8})",
        court_type=CourtType.STATE_TRIAL,
        example="BC123456",
        extract_groups=["court_code", "number"]
    ),
    # New York
    CaseNumberPattern(
        name="new_york_index",
        pattern=r"(?:Index\s*(?:No\.?|Number)?:?\s*)?(\d{6})/(\d{4})",
        court_type=CourtType.STATE_TRIAL,
        example="123456/2024",
        extract_groups=["number", "year"]
    ),
    # Texas
    CaseNumberPattern(
        name="texas_district",
        pattern=r"(?:Cause\s*(?:No\.?|Number)?:?\s*)?(\d{4})-(\d{4,6})-(\d{3})",
        court_type=CourtType.STATE_TRIAL,
        example="2024-12345-001",
        extract_groups=["year", "number", "court"]
    ),
    # Florida
    CaseNumberPattern(
        name="florida_circuit",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{4})-([A-Z]{2})-(\d{6})-([A-Z]{1,4})",
        court_type=CourtType.STATE_TRIAL,
        example="2024-CA-012345-A",
        extract_groups=["year", "case_type", "number", "division"]
    ),
]

# Appellate patterns
APPELLATE_PATTERNS = [
    CaseNumberPattern(
        name="federal_appellate",
        pattern=r"(?:Case\s*(?:No\.?|Number)?:?\s*)?(\d{2})-(\d{4,5})",
        court_type=CourtType.FEDERAL_APPELLATE,
        example="24-1234",
        extract_groups=["year", "number"]
    ),
    CaseNumberPattern(
        name="supreme_court",
        pattern=r"(?:No\.?\s*)?(\d{2})-(\d{1,4})",
        court_type=CourtType.SUPREME_COURT,
        example="23-456",
        extract_groups=["year", "number"]
    ),
]

ALL_CASE_NUMBER_PATTERNS = (
    FEDERAL_DISTRICT_PATTERNS +
    BANKRUPTCY_PATTERNS +
    STATE_COURT_PATTERNS +
    APPELLATE_PATTERNS
)


# ============================================================================
# PARTY NAME PATTERNS
# ============================================================================

@dataclass
class PartyExtractionResult:
    """Result of party name extraction"""
    raw_name: str
    cleaned_name: str
    entity_type: str  # individual, corporation, llc, government, etc.
    role: str  # plaintiff, defendant, petitioner, etc.
    aliases: List[str] = field(default_factory=list)
    doing_business_as: Optional[str] = None
    formerly_known_as: Optional[str] = None
    in_capacity_of: Optional[str] = None


# Entity type indicators
ENTITY_TYPE_PATTERNS = {
    "corporation": [
        r"\b(?:Inc\.?|Incorporated|Corp\.?|Corporation)\b",
        r"\bCompany\b",
        r"\bCo\.?\b(?!\s+v\.)",
    ],
    "llc": [
        r"\bL\.?L\.?C\.?\b",
        r"\bLimited\s+Liability\s+Company\b",
    ],
    "lp": [
        r"\bL\.?P\.?\b",
        r"\bLimited\s+Partnership\b",
    ],
    "llp": [
        r"\bL\.?L\.?P\.?\b",
        r"\bLimited\s+Liability\s+Partnership\b",
    ],
    "trust": [
        r"\bTrust\b",
        r"\bas\s+Trustee\s+(?:of|for)\b",
    ],
    "government": [
        r"\bUnited\s+States\s+of\s+America\b",
        r"\bState\s+of\s+\w+\b",
        r"\bCounty\s+of\s+\w+\b",
        r"\bCity\s+of\s+\w+\b",
        r"\bDepartment\s+of\b",
        r"\bCommission(?:er)?\b",
        r"\bAgency\b",
    ],
    "individual": [
        r"^[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+$",
        r"\ban\s+individual\b",
    ],
}

# Party role indicators
PARTY_ROLE_PATTERNS = {
    "plaintiff": r"\bPlaintiff(?:s)?\b",
    "defendant": r"\bDefendant(?:s)?\b",
    "petitioner": r"\bPetitioner(?:s)?\b",
    "respondent": r"\bRespondent(?:s)?\b",
    "appellant": r"\bAppellant(?:s)?\b",
    "appellee": r"\bAppellee(?:s)?\b",
    "debtor": r"\bDebtor(?:s)?\b",
    "creditor": r"\bCreditor(?:s)?\b",
    "intervenor": r"\bIntervenor(?:s)?\b",
    "cross_claimant": r"\bCross[\-\s]?Claimant(?:s)?\b",
    "cross_defendant": r"\bCross[\-\s]?Defendant(?:s)?\b",
    "third_party_plaintiff": r"\bThird[\-\s]?Party\s+Plaintiff(?:s)?\b",
    "third_party_defendant": r"\bThird[\-\s]?Party\s+Defendant(?:s)?\b",
    "counter_claimant": r"\bCounter[\-\s]?Claimant(?:s)?\b",
    "counter_defendant": r"\bCounter[\-\s]?Defendant(?:s)?\b",
    "real_party_in_interest": r"\bReal\s+Part(?:y|ies)\s+in\s+Interest\b",
}

# Special designations
SPECIAL_DESIGNATION_PATTERNS = {
    "dba": r"(?:d/?b/?a|doing\s+business\s+as)\s+([^,;]+)",
    "fka": r"(?:f/?k/?a|formerly\s+known\s+as)\s+([^,;]+)",
    "aka": r"(?:a/?k/?a|also\s+known\s+as)\s+([^,;]+)",
    "nka": r"(?:n/?k/?a|now\s+known\s+as)\s+([^,;]+)",
    "trustee": r"as\s+Trustee\s+(?:of|for)\s+([^,;]+)",
    "executor": r"as\s+Executor\s+of\s+([^,;]+)",
    "administrator": r"as\s+Administrator\s+of\s+([^,;]+)",
    "guardian": r"as\s+Guardian\s+(?:of|for)\s+([^,;]+)",
    "personal_representative": r"as\s+Personal\s+Representative\s+of\s+([^,;]+)",
    "successor_in_interest": r"as\s+Successor\s+in\s+Interest\s+to\s+([^,;]+)",
}


# ============================================================================
# LEGAL CITATION PATTERNS
# ============================================================================

@dataclass
class CitationResult:
    """Parsed legal citation"""
    raw_citation: str
    citation_type: str  # case, statute, rule, regulation, secondary
    reporter: Optional[str] = None
    volume: Optional[str] = None
    page: Optional[str] = None
    year: Optional[str] = None
    court: Optional[str] = None
    title: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    pinpoint: Optional[str] = None  # Specific page cite
    parallel_citations: List[str] = field(default_factory=list)

    def to_bluebook(self) -> str:
        """Format as Bluebook citation (simplified)"""
        return self.raw_citation


# Case citation patterns
CASE_CITATION_PATTERNS = [
    # U.S. Supreme Court
    {
        "name": "us_supreme_court",
        "pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc\.|Corp\.|Co\.|LLC|LP|LLP))?)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc\.|Corp\.|Co\.|LLC|LP|LLP))?),\s*(\d+)\s+U\.?\s*S\.?\s+(\d+)(?:,\s*(\d+))?\s*\((\d{4})\)",
        "groups": ["party1", "party2", "volume", "page", "pinpoint", "year"],
        "reporter": "U.S.",
    },
    # Supreme Court Reporter
    {
        "name": "supreme_court_reporter",
        "pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d+)\s+S\.?\s*Ct\.?\s+(\d+)(?:,\s*(\d+))?\s*\((\d{4})\)",
        "groups": ["party1", "party2", "volume", "page", "pinpoint", "year"],
        "reporter": "S. Ct.",
    },
    # Federal Reporter (F.2d, F.3d, F.4th)
    {
        "name": "federal_reporter",
        "pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc\.|Corp\.|Co\.|LLC))?)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc\.|Corp\.|Co\.|LLC))?),\s*(\d+)\s+F\.?\s*(2d|3d|4th)\s+(\d+)(?:,\s*(\d+))?\s*\(([^)]+)\s*(\d{4})\)",
        "groups": ["party1", "party2", "volume", "series", "page", "pinpoint", "court", "year"],
        "reporter": "F.",
    },
    # Federal Supplement (F. Supp., F. Supp. 2d, F. Supp. 3d)
    {
        "name": "federal_supplement",
        "pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d+)\s+F\.?\s*Supp\.?\s*(2d|3d)?\s*(\d+)(?:,\s*(\d+))?\s*\(([^)]+)\s*(\d{4})\)",
        "groups": ["party1", "party2", "volume", "series", "page", "pinpoint", "court", "year"],
        "reporter": "F. Supp.",
    },
    # Bankruptcy Reporter
    {
        "name": "bankruptcy_reporter",
        "pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d+)\s+B\.?\s*R\.?\s+(\d+)(?:,\s*(\d+))?\s*\(([^)]+)\s*(\d{4})\)",
        "groups": ["party1", "party2", "volume", "page", "pinpoint", "court", "year"],
        "reporter": "B.R.",
    },
    # State reporters - California
    {
        "name": "california_reporter",
        "pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d+)\s+Cal\.?\s*(2d|3d|4th|5th|App\.?\s*(2d|3d|4th|5th)?)?\s*(\d+)(?:,\s*(\d+))?\s*\((\d{4})\)",
        "groups": ["party1", "party2", "volume", "series", "app_series", "page", "pinpoint", "year"],
        "reporter": "Cal.",
    },
    # State reporters - New York
    {
        "name": "new_york_reporter",
        "pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d+)\s+N\.?\s*Y\.?\s*(2d|3d)?\s*(\d+)(?:,\s*(\d+))?\s*\((\d{4})\)",
        "groups": ["party1", "party2", "volume", "series", "page", "pinpoint", "year"],
        "reporter": "N.Y.",
    },
]

# Statutory citation patterns
STATUTE_CITATION_PATTERNS = [
    # U.S. Code
    {
        "name": "usc",
        "pattern": r"(\d+)\s*U\.?\s*S\.?\s*C\.?\s*§?\s*(\d+[a-z]?)(?:\s*\(([a-z0-9]+)\))?(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["title", "section", "subsection1", "subsection2"],
        "type": "federal_statute",
    },
    # U.S. Code Annotated
    {
        "name": "usca",
        "pattern": r"(\d+)\s*U\.?\s*S\.?\s*C\.?\s*A\.?\s*§?\s*(\d+[a-z]?)(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["title", "section", "subsection"],
        "type": "federal_statute",
    },
    # Code of Federal Regulations
    {
        "name": "cfr",
        "pattern": r"(\d+)\s*C\.?\s*F\.?\s*R\.?\s*§?\s*([\d\.]+)(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["title", "section", "subsection"],
        "type": "federal_regulation",
    },
    # Federal Register
    {
        "name": "fed_reg",
        "pattern": r"(\d+)\s*Fed\.?\s*Reg\.?\s*([\d,]+)(?:\s*\(([^)]+)\))?",
        "groups": ["volume", "page", "date"],
        "type": "federal_regulation",
    },
    # Public Law
    {
        "name": "pub_law",
        "pattern": r"Pub\.?\s*L\.?\s*(?:No\.?)?\s*(\d+)-(\d+)",
        "groups": ["congress", "number"],
        "type": "federal_statute",
    },
    # California statutes
    {
        "name": "california_code",
        "pattern": r"Cal\.?\s*(Civ\.?\s*Code|Bus\.?\s*(?:&|and)\s*Prof\.?\s*Code|Pen\.?\s*Code|Fam\.?\s*Code|Lab\.?\s*Code|Corp\.?\s*Code|Prob\.?\s*Code|Gov\.?\s*Code|Evid\.?\s*Code|Civ\.?\s*Proc\.?\s*Code)\s*§?\s*(\d+(?:\.\d+)?)",
        "groups": ["code", "section"],
        "type": "state_statute",
    },
    # New York statutes
    {
        "name": "new_york_code",
        "pattern": r"N\.?\s*Y\.?\s*(CPLR|Gen\.?\s*Bus\.?\s*Law|Lab\.?\s*Law|Exec\.?\s*Law|Pen\.?\s*Law|Real\s*Prop\.?\s*Law)\s*§?\s*(\d+(?:-[a-z])?)",
        "groups": ["code", "section"],
        "type": "state_statute",
    },
    # Texas statutes
    {
        "name": "texas_code",
        "pattern": r"Tex\.?\s*(Bus\.?\s*(?:&|and)\s*Com\.?\s*Code|Civ\.?\s*Prac\.?\s*(?:&|and)\s*Rem\.?\s*Code|Fam\.?\s*Code|Lab\.?\s*Code|Prop\.?\s*Code)\s*(?:Ann\.?)?\s*§?\s*(\d+(?:\.\d+)?)",
        "groups": ["code", "section"],
        "type": "state_statute",
    },
]

# Federal Rules patterns
FEDERAL_RULES_PATTERNS = [
    # Federal Rules of Civil Procedure
    {
        "name": "frcp",
        "pattern": r"Fed\.?\s*R\.?\s*Civ\.?\s*P\.?\s*(\d+)(?:\s*\(([a-z0-9]+)\))?(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["rule", "subsection1", "subsection2"],
        "full_name": "Federal Rules of Civil Procedure",
    },
    # Alternative FRCP pattern
    {
        "name": "frcp_alt",
        "pattern": r"Rule\s+(\d+)(?:\s*\(([a-z0-9]+)\))?\s*(?:of\s+the\s+)?(?:Federal\s+Rules?\s+of\s+Civil\s+Procedure|FRCP|F\.?\s*R\.?\s*C\.?\s*P\.?)",
        "groups": ["rule", "subsection"],
        "full_name": "Federal Rules of Civil Procedure",
    },
    # Federal Rules of Criminal Procedure
    {
        "name": "frcrp",
        "pattern": r"Fed\.?\s*R\.?\s*Crim\.?\s*P\.?\s*(\d+)(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["rule", "subsection"],
        "full_name": "Federal Rules of Criminal Procedure",
    },
    # Federal Rules of Evidence
    {
        "name": "fre",
        "pattern": r"Fed\.?\s*R\.?\s*Evid\.?\s*(\d+)(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["rule", "subsection"],
        "full_name": "Federal Rules of Evidence",
    },
    # Alternative FRE pattern
    {
        "name": "fre_alt",
        "pattern": r"Rule\s+(\d+)(?:\s*\(([a-z0-9]+)\))?\s*(?:of\s+the\s+)?(?:Federal\s+Rules?\s+of\s+Evidence|FRE|F\.?\s*R\.?\s*E\.?)",
        "groups": ["rule", "subsection"],
        "full_name": "Federal Rules of Evidence",
    },
    # Federal Rules of Appellate Procedure
    {
        "name": "frap",
        "pattern": r"Fed\.?\s*R\.?\s*App\.?\s*P\.?\s*(\d+)(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["rule", "subsection"],
        "full_name": "Federal Rules of Appellate Procedure",
    },
    # Federal Rules of Bankruptcy Procedure
    {
        "name": "frbp",
        "pattern": r"Fed\.?\s*R\.?\s*Bankr\.?\s*P\.?\s*(\d+)(?:\s*\(([a-z0-9]+)\))?",
        "groups": ["rule", "subsection"],
        "full_name": "Federal Rules of Bankruptcy Procedure",
    },
]

# Secondary source patterns
SECONDARY_SOURCE_PATTERNS = [
    # Restatements
    {
        "name": "restatement",
        "pattern": r"Restatement\s*\((?:Second|Third|Fourth)\)\s*of\s*(\w+(?:\s+\w+)*)\s*§?\s*(\d+)",
        "groups": ["subject", "section"],
        "type": "restatement",
    },
    # American Law Reports
    {
        "name": "alr",
        "pattern": r"(\d+)\s*A\.?\s*L\.?\s*R\.?\s*(2d|3d|4th|5th|6th|Fed\.?)?\s*(\d+)",
        "groups": ["volume", "series", "page"],
        "type": "annotation",
    },
    # Law Reviews
    {
        "name": "law_review",
        "pattern": r"(\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:L\.?\s*(?:Rev\.?|J\.?))\s+(\d+)\s*\((\d{4})\)",
        "groups": ["volume", "journal", "page", "year"],
        "type": "law_review",
    },
]


# ============================================================================
# DATE AND DEADLINE PATTERNS
# ============================================================================

DATE_PATTERNS = [
    # Standard formats
    r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",  # MM/DD/YYYY or MM-DD-YYYY
    r"(\w+)\s+(\d{1,2}),?\s+(\d{4})",  # Month DD, YYYY
    r"(\d{1,2})\s+(\w+)\s+(\d{4})",  # DD Month YYYY
    r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})",  # YYYY-MM-DD (ISO format)
]

DEADLINE_INDICATOR_PATTERNS = [
    r"(?:within|no later than|by|before|on or before)\s+(\d+)\s+(days?|weeks?|months?|years?)",
    r"(\d+)\s+(days?|weeks?|months?)\s+(?:from|after|following)",
    r"(?:due|deadline|must be filed)(?:\s+(?:on|by))?\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    r"(?:response|opposition|reply)\s+(?:due|deadline)(?:\s*:)?\s*(\w+\s+\d{1,2},?\s+\d{4})",
]

FILING_DATE_PATTERNS = [
    r"(?:Filed|Date\s+Filed|Filing\s+Date)(?:\s*:)?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    r"(?:Filed|Date\s+Filed|Filing\s+Date)(?:\s*:)?\s*(\w+\s+\d{1,2},?\s+\d{4})",
    r"(?:ECF|CM/ECF)\s+(?:Filing\s+)?(?:Date|Timestamp)(?:\s*:)?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
]

SERVICE_DATE_PATTERNS = [
    r"(?:Served|Date\s+(?:of\s+)?Serv(?:ice|ed))(?:\s*:)?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    r"(?:Served|Date\s+(?:of\s+)?Serv(?:ice|ed))(?:\s*:)?\s*(\w+\s+\d{1,2},?\s+\d{4})",
]


# ============================================================================
# MONETARY AMOUNT PATTERNS
# ============================================================================

MONETARY_PATTERNS = [
    # Dollar amounts with optional cents
    r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|billion)?",
    r"([\d,]+(?:\.\d{2})?)\s*(?:dollars?|USD)",
    # Amounts in words
    r"(\w+)\s+(?:million|billion)\s+dollars?",
    # Ranges
    r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:to|-)\s*\$?\s*([\d,]+(?:\.\d{2})?)",
    # "in excess of" amounts
    r"in\s+excess\s+of\s+\$\s*([\d,]+(?:\.\d{2})?)",
    # "exceeding" amounts
    r"exceed(?:s|ing)?\s+\$\s*([\d,]+(?:\.\d{2})?)",
    # "at least" amounts
    r"at\s+least\s+\$\s*([\d,]+(?:\.\d{2})?)",
    # "not less than" amounts
    r"not\s+less\s+than\s+\$\s*([\d,]+(?:\.\d{2})?)",
    # Jurisdictional amount
    r"(?:amount\s+in\s+controversy|jurisdictional\s+amount).*?\$\s*([\d,]+(?:\.\d{2})?)",
]

DAMAGES_TYPE_PATTERNS = {
    "compensatory": r"compensatory\s+damages?",
    "punitive": r"punitive\s+damages?",
    "treble": r"treble\s+damages?",
    "statutory": r"statutory\s+damages?",
    "liquidated": r"liquidated\s+damages?",
    "nominal": r"nominal\s+damages?",
    "consequential": r"consequential\s+damages?",
    "special": r"special\s+damages?",
    "general": r"general\s+damages?",
    "actual": r"actual\s+damages?",
    "exemplary": r"exemplary\s+damages?",
}


# ============================================================================
# ATTORNEY INFORMATION PATTERNS
# ============================================================================

ATTORNEY_PATTERNS = {
    "attorney_block": r"(?:Attorney(?:s)?\s+for\s+(?:Plaintiff|Defendant|Petitioner|Respondent|Appellant|Appellee|Debtor|Creditor)s?)[:\s]*\n((?:[^\n]+\n){1,10})",
    "bar_number": r"(?:Bar\s+(?:No\.?|Number|#)|State\s+Bar\s+(?:No\.?|#)|SBN)\s*:?\s*(\d+)",
    "firm_name": r"(?:Law\s+(?:Firm|Office(?:s)?)\s+of\s+)?([A-Z][A-Za-z]+(?:\s*(?:,|&|and)\s*[A-Z][A-Za-z]+)*(?:\s+(?:LLP|LLC|PC|P\.?C\.?|PLLC|APC))?)",
    "email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    "phone": r"(?:Tel(?:ephone)?|Ph(?:one)?|Fax)?\s*:?\s*\(?(\d{3})\)?[\s\-.]?(\d{3})[\s\-.]?(\d{4})",
    "address": r"(\d+[^,\n]+(?:Street|St\.|Avenue|Ave\.|Boulevard|Blvd\.|Road|Rd\.|Drive|Dr\.|Suite|Ste\.|Floor|Fl\.)[^,\n]*),?\s*([^,\n]+),?\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)",
}


# ============================================================================
# COURT AND JUDGE PATTERNS
# ============================================================================

FEDERAL_COURT_PATTERNS = [
    r"(?:UNITED\s+STATES\s+)?DISTRICT\s+COURT\s+(?:FOR\s+THE\s+)?([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*)\s+DISTRICT\s+OF\s+([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*)",
    r"(?:U\.?\s*S\.?\s*)?DISTRICT\s+COURT\s*[-—]\s*([A-Z]\.?\s*D\.?\s*[A-Z][a-z]+\.?)",
    r"(?:UNITED\s+STATES\s+)?BANKRUPTCY\s+COURT\s+(?:FOR\s+THE\s+)?([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*)\s+DISTRICT\s+OF\s+([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*)",
    r"(?:UNITED\s+STATES\s+)?COURT\s+OF\s+APPEALS?\s+(?:FOR\s+THE\s+)?(\w+)\s+CIRCUIT",
]

JUDGE_PATTERNS = [
    r"(?:Hon(?:orable)?\.?|Judge)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
    r"(?:Before|Presiding)(?:\s*:)?\s*(?:Hon(?:orable)?\.?|Judge)?\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
    r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+),\s*(?:United\s+States\s+)?(?:District\s+)?(?:Judge|Magistrate)",
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def compile_pattern(pattern: str, flags: int = re.IGNORECASE | re.MULTILINE) -> Pattern:
    """Compile a regex pattern with standard flags"""
    return re.compile(pattern, flags)


def compile_all_patterns() -> Dict[str, List[Pattern]]:
    """Compile all patterns for efficient matching"""
    compiled = {}

    # Case number patterns
    compiled["case_numbers"] = [
        compile_pattern(p.pattern) for p in ALL_CASE_NUMBER_PATTERNS
    ]

    # Citation patterns
    compiled["case_citations"] = [
        compile_pattern(p["pattern"]) for p in CASE_CITATION_PATTERNS
    ]
    compiled["statutes"] = [
        compile_pattern(p["pattern"]) for p in STATUTE_CITATION_PATTERNS
    ]
    compiled["rules"] = [
        compile_pattern(p["pattern"]) for p in FEDERAL_RULES_PATTERNS
    ]

    # Date patterns
    compiled["dates"] = [compile_pattern(p) for p in DATE_PATTERNS]
    compiled["deadlines"] = [compile_pattern(p) for p in DEADLINE_INDICATOR_PATTERNS]
    compiled["filing_dates"] = [compile_pattern(p) for p in FILING_DATE_PATTERNS]

    # Money patterns
    compiled["monetary"] = [compile_pattern(p) for p in MONETARY_PATTERNS]

    # Court patterns
    compiled["courts"] = [compile_pattern(p) for p in FEDERAL_COURT_PATTERNS]
    compiled["judges"] = [compile_pattern(p) for p in JUDGE_PATTERNS]

    return compiled


def extract_case_number(text: str) -> Optional[Dict[str, str]]:
    """Extract case number from text"""
    for pattern_def in ALL_CASE_NUMBER_PATTERNS:
        pattern = compile_pattern(pattern_def.pattern)
        match = pattern.search(text)
        if match:
            result = {
                "raw": match.group(0),
                "court_type": pattern_def.court_type.value,
                "pattern_name": pattern_def.name,
            }
            for i, group_name in enumerate(pattern_def.extract_groups, 1):
                if i <= len(match.groups()) and match.group(i):
                    result[group_name] = match.group(i)
            return result
    return None


def extract_all_citations(text: str) -> List[CitationResult]:
    """Extract all legal citations from text"""
    citations = []

    # Case citations
    for pattern_def in CASE_CITATION_PATTERNS:
        pattern = compile_pattern(pattern_def["pattern"])
        for match in pattern.finditer(text):
            citations.append(CitationResult(
                raw_citation=match.group(0),
                citation_type="case",
                reporter=pattern_def.get("reporter"),
                volume=match.group(3) if len(match.groups()) >= 3 else None,
                page=match.group(4) if len(match.groups()) >= 4 else None,
                year=match.group(len(match.groups())) if match.groups() else None,
            ))

    # Statutory citations
    for pattern_def in STATUTE_CITATION_PATTERNS:
        pattern = compile_pattern(pattern_def["pattern"])
        for match in pattern.finditer(text):
            citations.append(CitationResult(
                raw_citation=match.group(0),
                citation_type=pattern_def.get("type", "statute"),
                title=match.group(1) if len(match.groups()) >= 1 else None,
                section=match.group(2) if len(match.groups()) >= 2 else None,
            ))

    # Federal Rules
    for pattern_def in FEDERAL_RULES_PATTERNS:
        pattern = compile_pattern(pattern_def["pattern"])
        for match in pattern.finditer(text):
            citations.append(CitationResult(
                raw_citation=match.group(0),
                citation_type="rule",
                section=match.group(1) if len(match.groups()) >= 1 else None,
                subsection=match.group(2) if len(match.groups()) >= 2 else None,
            ))

    return citations


def extract_monetary_amounts(text: str) -> List[Dict[str, any]]:
    """Extract all monetary amounts from text"""
    amounts = []
    for pattern in MONETARY_PATTERNS:
        compiled = compile_pattern(pattern)
        for match in compiled.finditer(text):
            raw = match.group(0)
            # Extract numeric value
            amount_str = match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
                # Check for million/billion
                if "million" in raw.lower():
                    amount *= 1_000_000
                elif "billion" in raw.lower():
                    amount *= 1_000_000_000
                amounts.append({
                    "raw": raw,
                    "amount": amount,
                    "currency": "USD",
                })
            except (ValueError, IndexError):
                continue
    return amounts


def extract_parties_from_caption(caption_text: str) -> Dict[str, List[str]]:
    """Extract party names from case caption"""
    parties = {"plaintiffs": [], "defendants": []}

    # Look for v. or vs. to split caption
    v_pattern = compile_pattern(r"(.+?)\s+v\.?\s*(?:s\.?)?\s+(.+)", re.DOTALL)
    match = v_pattern.search(caption_text)

    if match:
        plaintiff_section = match.group(1)
        defendant_section = match.group(2)

        # Split on common separators
        for name in re.split(r"[;,]\s*(?:and\s+)?|\s+and\s+", plaintiff_section):
            cleaned = name.strip()
            if cleaned and len(cleaned) > 2:
                parties["plaintiffs"].append(cleaned)

        for name in re.split(r"[;,]\s*(?:and\s+)?|\s+and\s+", defendant_section):
            cleaned = name.strip()
            # Remove trailing et al.
            cleaned = re.sub(r"\s+et\s+al\.?\s*$", "", cleaned, flags=re.IGNORECASE)
            if cleaned and len(cleaned) > 2:
                parties["defendants"].append(cleaned)

    return parties


def determine_entity_type(name: str) -> str:
    """Determine entity type from name"""
    name_upper = name.upper()

    for entity_type, patterns in ENTITY_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return entity_type

    return "unknown"


# Pre-compile patterns on module load
COMPILED_PATTERNS = compile_all_patterns()


# Export all
__all__ = [
    'CourtType',
    'CaseNumberPattern',
    'PartyExtractionResult',
    'CitationResult',
    'FEDERAL_DISTRICT_PATTERNS',
    'BANKRUPTCY_PATTERNS',
    'STATE_COURT_PATTERNS',
    'APPELLATE_PATTERNS',
    'ALL_CASE_NUMBER_PATTERNS',
    'ENTITY_TYPE_PATTERNS',
    'PARTY_ROLE_PATTERNS',
    'SPECIAL_DESIGNATION_PATTERNS',
    'CASE_CITATION_PATTERNS',
    'STATUTE_CITATION_PATTERNS',
    'FEDERAL_RULES_PATTERNS',
    'SECONDARY_SOURCE_PATTERNS',
    'DATE_PATTERNS',
    'DEADLINE_INDICATOR_PATTERNS',
    'FILING_DATE_PATTERNS',
    'SERVICE_DATE_PATTERNS',
    'MONETARY_PATTERNS',
    'DAMAGES_TYPE_PATTERNS',
    'ATTORNEY_PATTERNS',
    'FEDERAL_COURT_PATTERNS',
    'JUDGE_PATTERNS',
    'compile_pattern',
    'compile_all_patterns',
    'extract_case_number',
    'extract_all_citations',
    'extract_monetary_amounts',
    'extract_parties_from_caption',
    'determine_entity_type',
    'COMPILED_PATTERNS',
]
