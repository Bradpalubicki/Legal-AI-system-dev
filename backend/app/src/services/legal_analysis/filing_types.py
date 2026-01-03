"""
Legal Filing Type Registry

Comprehensive registry of all court filing types with:
- Classification codes (A01, B01, C01, etc.)
- Regex patterns for detection
- Required extraction fields per type
- Practice area mappings

EDUCATIONAL CONTENT DISCLAIMER: This module provides informational analysis
of legal documents and does not constitute legal advice.
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Pattern, Set, Any


class PracticeArea(Enum):
    """Legal practice areas"""
    CIVIL_LITIGATION = "civil_litigation"
    CRIMINAL = "criminal"
    BANKRUPTCY = "bankruptcy"
    FAMILY_LAW = "family_law"
    EMPLOYMENT = "employment"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    REAL_ESTATE = "real_estate"
    PROBATE = "probate"
    IMMIGRATION = "immigration"
    TAX = "tax"
    ADMINISTRATIVE = "administrative"
    APPELLATE = "appellate"
    ARBITRATION = "arbitration"
    SECURITIES = "securities"
    ANTITRUST = "antitrust"
    ENVIRONMENTAL = "environmental"
    HEALTHCARE = "healthcare"
    SMALL_CLAIMS = "small_claims"


class FilingCategory(Enum):
    """Filing categories"""
    INITIATING = "A"          # Initiating documents (complaints, petitions)
    RESPONSIVE = "B"          # Responsive pleadings (answers, replies)
    DISPOSITIVE = "C"         # Dispositive motions
    NON_DISPOSITIVE = "D"     # Non-dispositive motions
    OPPOSITION_REPLY = "E"    # Oppositions and replies
    COURT_ORDERS = "F"        # Court orders
    BRIEFS = "G"              # Briefs and memoranda
    DISCOVERY = "H"           # Discovery documents
    SPECIALIZED = "S"         # Specialized filings
    APPEALS = "P"             # Appellate filings
    ADMINISTRATIVE = "R"      # Administrative agency filings
    OTHER = "X"               # Unclassified


@dataclass
class FilingType:
    """Definition of a court filing type"""
    code: str                           # e.g., "A01", "C04"
    name: str                           # e.g., "COMPLAINT"
    display_name: str                   # e.g., "Civil Complaint"
    category: FilingCategory
    practice_areas: List[PracticeArea]
    trigger_patterns: List[str]         # Regex patterns for detection
    secondary_indicators: List[str]     # Additional text indicators
    required_fields: List[str]          # Fields that must be extracted
    optional_fields: List[str] = field(default_factory=list)
    description: str = ""
    response_deadline_days: Optional[int] = None  # Default response deadline

    def compile_patterns(self) -> List[Pattern]:
        """Compile regex patterns for efficient matching"""
        return [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.trigger_patterns]


# ============================================================================
# CATEGORY A: INITIATING DOCUMENTS
# ============================================================================

FILING_TYPES: Dict[str, FilingType] = {}

# A01 - COMPLAINT
FILING_TYPES["A01"] = FilingType(
    code="A01",
    name="COMPLAINT",
    display_name="Civil Complaint",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"COMPLAINT\s+(FOR|AND)",
        r"CIVIL\s+COMPLAINT",
        r"COMPLAINT\s+FOR\s+DAMAGES",
        r"^COMPLAINT$",
    ],
    secondary_indicators=[
        "COMES NOW", "Plaintiff alleges", "CAUSES OF ACTION",
        "PRAYER FOR RELIEF", "JURY DEMAND", "WHEREFORE"
    ],
    required_fields=[
        "case_number", "court_name", "plaintiffs", "defendants",
        "filing_date", "causes_of_action", "prayer_for_relief"
    ],
    optional_fields=[
        "jurisdiction_type", "venue_basis", "damages_amount",
        "jury_demand", "factual_background", "class_allegations"
    ],
    description="Civil complaint initiating lawsuit",
    response_deadline_days=21
)

# A02 - AMENDED COMPLAINT
FILING_TYPES["A02"] = FilingType(
    code="A02",
    name="AMENDED_COMPLAINT",
    display_name="Amended Complaint",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"(FIRST|SECOND|THIRD|FOURTH|\d+(?:ST|ND|RD|TH)?)\s+AMENDED\s+COMPLAINT",
        r"AMENDED\s+COMPLAINT",
        r"SUPPLEMENTAL\s+COMPLAINT",
    ],
    secondary_indicators=[
        "COMES NOW", "Plaintiff alleges", "amends and restates"
    ],
    required_fields=[
        "case_number", "court_name", "plaintiffs", "defendants",
        "filing_date", "amendment_number", "causes_of_action"
    ],
    optional_fields=["changes_from_original", "new_claims", "dropped_claims"],
    description="Modified complaint (note amendment number)",
    response_deadline_days=21
)

# A03 - CLASS ACTION COMPLAINT
FILING_TYPES["A03"] = FilingType(
    code="A03",
    name="CLASS_ACTION_COMPLAINT",
    display_name="Class Action Complaint",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"CLASS\s+ACTION\s+COMPLAINT",
        r"CLASS\s+ACTION\s+AND\s+REPRESENTATIVE\s+ACTION",
        r"COMPLAINT.{0,50}CLASS\s+ACTION",
    ],
    secondary_indicators=[
        "Rule 23", "class certification", "numerosity", "commonality",
        "typicality", "adequacy", "on behalf of all others similarly situated"
    ],
    required_fields=[
        "case_number", "court_name", "plaintiffs", "defendants",
        "class_definition", "causes_of_action", "rule_23_factors"
    ],
    optional_fields=["estimated_class_size", "class_representatives"],
    description="Complaint seeking class certification",
    response_deadline_days=21
)

# A04 - PETITION
FILING_TYPES["A04"] = FilingType(
    code="A04",
    name="PETITION",
    display_name="Petition",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION, PracticeArea.FAMILY_LAW, PracticeArea.PROBATE],
    trigger_patterns=[
        r"^PETITION\s+(FOR|TO)",
        r"PETITION\s+FOR\s+WRIT",
        r"VERIFIED\s+PETITION",
    ],
    secondary_indicators=[
        "Petitioner respectfully", "prays this Court", "relief sought"
    ],
    required_fields=[
        "case_number", "court_name", "petitioner", "respondent",
        "filing_date", "relief_sought"
    ],
    description="Non-complaint initiating document",
    response_deadline_days=30
)

# A05 - CROSSCLAIM
FILING_TYPES["A05"] = FilingType(
    code="A05",
    name="CROSSCLAIM",
    display_name="Crossclaim",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"CROSS[\-\s]?CLAIM",
        r"CROSS[\-\s]?COMPLAINT",
    ],
    secondary_indicators=[
        "against co-defendant", "contribution", "indemnification"
    ],
    required_fields=[
        "case_number", "crossclaim_plaintiff", "crossclaim_defendant",
        "claims_asserted"
    ],
    description="Claim against co-party",
    response_deadline_days=21
)

# A06 - COUNTERCLAIM
FILING_TYPES["A06"] = FilingType(
    code="A06",
    name="COUNTERCLAIM",
    display_name="Counterclaim",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"COUNTER[\-\s]?CLAIM",
        r"DEFENDANT'?S?\s+COUNTER[\-\s]?CLAIM",
    ],
    secondary_indicators=[
        "counter-plaintiff", "counter-defendant", "setoff"
    ],
    required_fields=[
        "case_number", "counterclaim_plaintiff", "counterclaim_defendant",
        "claims_asserted"
    ],
    description="Defendant's claim against plaintiff",
    response_deadline_days=21
)

# A07 - THIRD PARTY COMPLAINT
FILING_TYPES["A07"] = FilingType(
    code="A07",
    name="THIRD_PARTY_COMPLAINT",
    display_name="Third Party Complaint",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"THIRD[\-\s]?PARTY\s+COMPLAINT",
        r"IMPLEADER",
        r"Rule\s+14",
    ],
    secondary_indicators=[
        "third-party plaintiff", "third-party defendant", "contribution",
        "indemnification", "liable over"
    ],
    required_fields=[
        "case_number", "third_party_plaintiff", "third_party_defendant",
        "claims_asserted"
    ],
    description="Impleader claim",
    response_deadline_days=21
)

# A08 - INDICTMENT
FILING_TYPES["A08"] = FilingType(
    code="A08",
    name="INDICTMENT",
    display_name="Indictment",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CRIMINAL],
    trigger_patterns=[
        r"INDICTMENT",
        r"GRAND\s+JURY\s+INDICTMENT",
        r"SEALED\s+INDICTMENT",
        r"SUPERSEDING\s+INDICTMENT",
    ],
    secondary_indicators=[
        "grand jury", "true bill", "COUNT", "in violation of"
    ],
    required_fields=[
        "case_number", "court_name", "defendant", "charges",
        "statutory_citations"
    ],
    description="Grand jury criminal charge"
)

# A09 - INFORMATION
FILING_TYPES["A09"] = FilingType(
    code="A09",
    name="INFORMATION",
    display_name="Criminal Information",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CRIMINAL],
    trigger_patterns=[
        r"CRIMINAL\s+INFORMATION",
        r"^INFORMATION$",
    ],
    secondary_indicators=[
        "United States Attorney", "District Attorney", "charges"
    ],
    required_fields=[
        "case_number", "court_name", "defendant", "charges"
    ],
    description="Prosecutor's criminal charge"
)

# A10 - NOTICE OF REMOVAL
FILING_TYPES["A10"] = FilingType(
    code="A10",
    name="NOTICE_OF_REMOVAL",
    display_name="Notice of Removal",
    category=FilingCategory.INITIATING,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"NOTICE\s+OF\s+REMOVAL",
        r"28\s*U\.?S\.?C\.?\s*§?\s*1441",
        r"28\s*U\.?S\.?C\.?\s*§?\s*1446",
    ],
    secondary_indicators=[
        "removed from state court", "federal question", "diversity jurisdiction",
        "timely filed", "within 30 days"
    ],
    required_fields=[
        "case_number", "state_court_case", "removal_basis",
        "filing_date", "state_filing_date"
    ],
    description="Federal removal from state court",
    response_deadline_days=30  # Motion to remand deadline
)

# ============================================================================
# CATEGORY B: RESPONSIVE PLEADINGS
# ============================================================================

# B01 - ANSWER
FILING_TYPES["B01"] = FilingType(
    code="B01",
    name="ANSWER",
    display_name="Answer to Complaint",
    category=FilingCategory.RESPONSIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"ANSWER\s+(TO|AND)",
        r"DEFENDANT'?S?\s+ANSWER",
        r"^ANSWER$",
    ],
    secondary_indicators=[
        "ADMITS", "DENIES", "lacks knowledge", "AFFIRMATIVE DEFENSES",
        "demands strict proof"
    ],
    required_fields=[
        "case_number", "responding_party", "admissions", "denials",
        "affirmative_defenses"
    ],
    optional_fields=["counterclaim", "crossclaim"],
    description="Response to complaint"
)

# B02 - AMENDED ANSWER
FILING_TYPES["B02"] = FilingType(
    code="B02",
    name="AMENDED_ANSWER",
    display_name="Amended Answer",
    category=FilingCategory.RESPONSIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"AMENDED\s+ANSWER",
        r"(FIRST|SECOND|THIRD|\d+(?:ST|ND|RD|TH)?)\s+AMENDED\s+ANSWER",
    ],
    secondary_indicators=["amends", "restates"],
    required_fields=[
        "case_number", "responding_party", "amendment_number"
    ],
    description="Modified answer"
)

# B03 - REPLY TO COUNTERCLAIM
FILING_TYPES["B03"] = FilingType(
    code="B03",
    name="REPLY",
    display_name="Reply to Counterclaim",
    category=FilingCategory.RESPONSIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"REPLY\s+TO\s+COUNTER[\-\s]?CLAIM",
        r"PLAINTIFF'?S?\s+REPLY",
    ],
    secondary_indicators=["denies", "admits"],
    required_fields=["case_number", "responding_party"],
    description="Response to counterclaim or affirmative defenses"
)

# B04 - RESPONSE TO PETITION
FILING_TYPES["B04"] = FilingType(
    code="B04",
    name="RESPONSE_TO_PETITION",
    display_name="Response to Petition",
    category=FilingCategory.RESPONSIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION, PracticeArea.FAMILY_LAW],
    trigger_patterns=[
        r"RESPONSE\s+TO\s+PETITION",
        r"ANSWER\s+TO\s+PETITION",
        r"RESPONDENT'?S?\s+(RESPONSE|ANSWER)",
    ],
    secondary_indicators=["Respondent"],
    required_fields=["case_number", "respondent"],
    description="Answer to petition"
)

# ============================================================================
# CATEGORY C: DISPOSITIVE MOTIONS
# ============================================================================

# C01 - MTD 12(b)(1)
FILING_TYPES["C01"] = FilingType(
    code="C01",
    name="MTD_12B1",
    display_name="Motion to Dismiss - Subject Matter Jurisdiction",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"12\s*\(\s*b\s*\)\s*\(\s*1\s*\)",
        r"SUBJECT\s+MATTER\s+JURISDICTION",
        r"LACK\s+OF\s+JURISDICTION",
    ],
    secondary_indicators=[
        "Article III", "standing", "ripeness", "mootness", "case or controversy"
    ],
    required_fields=[
        "case_number", "moving_party", "jurisdictional_defect",
        "relief_sought"
    ],
    description="Motion to Dismiss: Subject Matter Jurisdiction",
    response_deadline_days=21
)

# C02 - MTD 12(b)(2)
FILING_TYPES["C02"] = FilingType(
    code="C02",
    name="MTD_12B2",
    display_name="Motion to Dismiss - Personal Jurisdiction",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"12\s*\(\s*b\s*\)\s*\(\s*2\s*\)",
        r"PERSONAL\s+JURISDICTION",
        r"LACK\s+OF\s+PERSONAL\s+JURISDICTION",
    ],
    secondary_indicators=[
        "minimum contacts", "long-arm statute", "due process",
        "purposeful availment", "specific jurisdiction", "general jurisdiction"
    ],
    required_fields=[
        "case_number", "moving_party", "jurisdictional_argument"
    ],
    description="Motion to Dismiss: Personal Jurisdiction",
    response_deadline_days=21
)

# C03 - MTD 12(b)(3)
FILING_TYPES["C03"] = FilingType(
    code="C03",
    name="MTD_12B3",
    display_name="Motion to Dismiss - Improper Venue",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"12\s*\(\s*b\s*\)\s*\(\s*3\s*\)",
        r"IMPROPER\s+VENUE",
        r"MOTION\s+TO\s+TRANSFER\s+VENUE",
    ],
    secondary_indicators=[
        "28 U.S.C. § 1391", "forum non conveniens", "transfer"
    ],
    required_fields=[
        "case_number", "moving_party", "venue_argument", "proper_venue"
    ],
    description="Motion to Dismiss: Improper Venue",
    response_deadline_days=21
)

# C04 - MTD 12(b)(6)
FILING_TYPES["C04"] = FilingType(
    code="C04",
    name="MTD_12B6",
    display_name="Motion to Dismiss - Failure to State a Claim",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"12\s*\(\s*b\s*\)\s*\(\s*6\s*\)",
        r"FAILURE\s+TO\s+STATE\s+A?\s*CLAIM",
        r"MOTION\s+TO\s+DISMISS.*STATE\s+A\s+CLAIM",
    ],
    secondary_indicators=[
        "Twombly", "Iqbal", "plausibility", "conclusory", "well-pleaded facts",
        "facial plausibility", "entitled to relief"
    ],
    required_fields=[
        "case_number", "moving_party", "claims_challenged",
        "legal_arguments", "relief_sought"
    ],
    optional_fields=["key_authorities", "factual_deficiencies"],
    description="Motion to Dismiss: Failure to State a Claim",
    response_deadline_days=21
)

# C05 - MOTION FOR SUMMARY JUDGMENT
FILING_TYPES["C05"] = FilingType(
    code="C05",
    name="MSJ",
    display_name="Motion for Summary Judgment",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+(FOR)?\s*SUMMARY\s+JUDGMENT",
        r"Rule\s+56",
        r"MSJ",
    ],
    secondary_indicators=[
        "undisputed material fact", "judgment as a matter of law",
        "SUF", "STATEMENT OF UNDISPUTED FACTS", "Celotex", "genuine issue"
    ],
    required_fields=[
        "case_number", "moving_party", "claims_at_issue",
        "undisputed_facts", "legal_arguments"
    ],
    optional_fields=["exhibits", "declarations", "expert_reports"],
    description="Motion for Summary Judgment",
    response_deadline_days=21
)

# C06 - PARTIAL SUMMARY JUDGMENT
FILING_TYPES["C06"] = FilingType(
    code="C06",
    name="PARTIAL_MSJ",
    display_name="Motion for Partial Summary Judgment",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"PARTIAL\s+SUMMARY\s+JUDGMENT",
        r"SUMMARY\s+JUDGMENT.*SPECIFIC\s+CLAIMS?",
    ],
    secondary_indicators=["specific claims", "partial adjudication"],
    required_fields=[
        "case_number", "moving_party", "specific_claims_addressed"
    ],
    description="Partial Summary Judgment",
    response_deadline_days=21
)

# C07 - JUDGMENT AS A MATTER OF LAW (JMOL)
FILING_TYPES["C07"] = FilingType(
    code="C07",
    name="JMOL",
    display_name="Motion for Judgment as a Matter of Law",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"JUDGMENT\s+AS\s+A\s+MATTER\s+OF\s+LAW",
        r"RULE\s+50",
        r"JMOL",
        r"RENEWED\s+MOTION.*JUDGMENT",
    ],
    secondary_indicators=[
        "directed verdict", "insufficient evidence", "no reasonable jury"
    ],
    required_fields=[
        "case_number", "moving_party", "claims_at_issue"
    ],
    description="Judgment as a Matter of Law (Rule 50)",
    response_deadline_days=14
)

# C08 - JUDGMENT ON THE PLEADINGS
FILING_TYPES["C08"] = FilingType(
    code="C08",
    name="MJOP",
    display_name="Motion for Judgment on the Pleadings",
    category=FilingCategory.DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"JUDGMENT\s+ON\s+THE\s+PLEADINGS",
        r"RULE\s+12\s*\(\s*c\s*\)",
    ],
    secondary_indicators=["12(c)", "after pleadings close"],
    required_fields=["case_number", "moving_party"],
    description="Motion for Judgment on the Pleadings",
    response_deadline_days=21
)

# ============================================================================
# CATEGORY D: NON-DISPOSITIVE MOTIONS
# ============================================================================

# D01 - MOTION TO COMPEL
FILING_TYPES["D01"] = FilingType(
    code="D01",
    name="MTC",
    display_name="Motion to Compel Discovery",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+TO\s+COMPEL",
        r"COMPEL\s+DISCOVERY",
        r"COMPEL\s+(RESPONSES?|ANSWERS?|PRODUCTION)",
    ],
    secondary_indicators=[
        "interrogatories", "requests for production", "deposition",
        "Rule 37", "meet and confer", "discovery dispute"
    ],
    required_fields=[
        "case_number", "moving_party", "discovery_at_issue",
        "meet_confer_efforts"
    ],
    description="Motion to Compel Discovery",
    response_deadline_days=14
)

# D02 - MOTION FOR PROTECTIVE ORDER
FILING_TYPES["D02"] = FilingType(
    code="D02",
    name="MPO",
    display_name="Motion for Protective Order",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+FOR\s+PROTECTIVE\s+ORDER",
        r"PROTECTIVE\s+ORDER",
        r"RULE\s+26\s*\(\s*c\s*\)",
    ],
    secondary_indicators=[
        "undue burden", "privileged", "trade secret", "confidential",
        "harassment", "annoyance"
    ],
    required_fields=[
        "case_number", "moving_party", "protection_sought"
    ],
    description="Motion for Protective Order",
    response_deadline_days=14
)

# D03 - MOTION TO QUASH
FILING_TYPES["D03"] = FilingType(
    code="D03",
    name="MTQ",
    display_name="Motion to Quash Subpoena",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+TO\s+QUASH",
        r"QUASH\s+SUBPOENA",
    ],
    secondary_indicators=[
        "subpoena", "undue burden", "Rule 45", "non-party"
    ],
    required_fields=[
        "case_number", "moving_party", "subpoena_details"
    ],
    description="Motion to Quash Subpoena",
    response_deadline_days=14
)

# D04 - MOTION IN LIMINE
FILING_TYPES["D04"] = FilingType(
    code="D04",
    name="MIL",
    display_name="Motion in Limine",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION, PracticeArea.CRIMINAL],
    trigger_patterns=[
        r"MOTION\s+IN\s+LIMINE",
        r"IN\s+LIMINE",
        r"MIL(?:\s+NO\.?\s*\d+)?",
    ],
    secondary_indicators=[
        "exclude evidence", "prejudicial", "Rule 403", "Rule 404",
        "prior acts", "character evidence"
    ],
    required_fields=[
        "case_number", "moving_party", "evidence_at_issue",
        "exclusion_basis"
    ],
    description="Motion in Limine",
    response_deadline_days=14
)

# D05 - DAUBERT MOTION
FILING_TYPES["D05"] = FilingType(
    code="D05",
    name="DAUBERT",
    display_name="Daubert Motion to Exclude Expert",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"DAUBERT",
        r"EXCLUDE\s+EXPERT",
        r"RULE\s+702",
        r"EXPERT\s+TESTIMONY",
    ],
    secondary_indicators=[
        "reliability", "methodology", "scientific validity",
        "Kumho Tire", "gatekeeping", "qualifications"
    ],
    required_fields=[
        "case_number", "moving_party", "expert_at_issue",
        "exclusion_grounds"
    ],
    description="Motion to Exclude Expert",
    response_deadline_days=21
)

# D06 - MOTION TO AMEND
FILING_TYPES["D06"] = FilingType(
    code="D06",
    name="MTA",
    display_name="Motion for Leave to Amend",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+(FOR\s+LEAVE\s+)?TO\s+AMEND",
        r"LEAVE\s+TO\s+AMEND",
        r"RULE\s+15",
    ],
    secondary_indicators=[
        "amendment", "futility", "undue delay", "prejudice"
    ],
    required_fields=[
        "case_number", "moving_party", "proposed_amendment"
    ],
    description="Motion to Amend Pleading",
    response_deadline_days=14
)

# D07 - MOTION FOR EXTENSION
FILING_TYPES["D07"] = FilingType(
    code="D07",
    name="EXTENSION",
    display_name="Motion for Extension of Time",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+(FOR\s+)?(EXTENSION|ENLARGE)",
        r"EXTEND\s+TIME",
        r"ADDITIONAL\s+TIME",
    ],
    secondary_indicators=[
        "good cause", "excusable neglect", "stipulated"
    ],
    required_fields=[
        "case_number", "moving_party", "deadline_at_issue",
        "requested_extension", "cause_shown"
    ],
    description="Motion for Extension of Time",
    response_deadline_days=7
)

# D08 - MOTION TO CONTINUE
FILING_TYPES["D08"] = FilingType(
    code="D08",
    name="CONTINUANCE",
    display_name="Motion to Continue",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+TO\s+CONTINUE",
        r"CONTINUANCE",
        r"POSTPONE\s+(HEARING|TRIAL)",
    ],
    secondary_indicators=["reschedule", "unavailable", "conflict"],
    required_fields=[
        "case_number", "moving_party", "event_to_continue",
        "reason", "proposed_date"
    ],
    description="Motion to Continue Hearing/Trial",
    response_deadline_days=7
)

# D09 - TRO
FILING_TYPES["D09"] = FilingType(
    code="D09",
    name="TRO",
    display_name="Temporary Restraining Order Application",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"TEMPORARY\s+RESTRAINING\s+ORDER",
        r"TRO",
        r"EX\s+PARTE\s+APPLICATION",
    ],
    secondary_indicators=[
        "irreparable harm", "likelihood of success", "balance of hardships",
        "public interest", "Rule 65"
    ],
    required_fields=[
        "case_number", "moving_party", "relief_sought",
        "irreparable_harm_showing"
    ],
    description="Temporary Restraining Order Request"
)

# D10 - PRELIMINARY INJUNCTION
FILING_TYPES["D10"] = FilingType(
    code="D10",
    name="PI",
    display_name="Motion for Preliminary Injunction",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"PRELIMINARY\s+INJUNCTION",
        r"MOTION\s+FOR\s+INJUNCTIVE\s+RELIEF",
    ],
    secondary_indicators=[
        "Winter factors", "likelihood of success", "irreparable injury",
        "balance of equities", "public interest"
    ],
    required_fields=[
        "case_number", "moving_party", "relief_sought",
        "winter_factors_analysis"
    ],
    description="Preliminary Injunction Request",
    response_deadline_days=21
)

# D11 - CLASS CERTIFICATION
FILING_TYPES["D11"] = FilingType(
    code="D11",
    name="CLASS_CERT",
    display_name="Motion for Class Certification",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"CLASS\s+CERTIFICATION",
        r"CERTIFY\s+(THE\s+)?CLASS",
        r"RULE\s+23",
    ],
    secondary_indicators=[
        "numerosity", "commonality", "typicality", "adequacy",
        "predominance", "superiority", "23(a)", "23(b)"
    ],
    required_fields=[
        "case_number", "moving_party", "proposed_class",
        "rule_23_requirements"
    ],
    description="Motion for Class Certification",
    response_deadline_days=28
)

# D12 - MOTION TO REMAND
FILING_TYPES["D12"] = FilingType(
    code="D12",
    name="REMAND",
    display_name="Motion to Remand",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+TO\s+REMAND",
        r"REMAND\s+TO\s+STATE\s+COURT",
    ],
    secondary_indicators=[
        "improper removal", "lack of federal jurisdiction",
        "28 U.S.C. § 1447"
    ],
    required_fields=[
        "case_number", "moving_party", "remand_basis"
    ],
    description="Motion to Remand to State Court",
    response_deadline_days=14
)

# D13 - MOTION FOR SANCTIONS
FILING_TYPES["D13"] = FilingType(
    code="D13",
    name="SANCTIONS",
    display_name="Motion for Sanctions",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MOTION\s+FOR\s+SANCTIONS",
        r"RULE\s+11",
        r"28\s*U\.?S\.?C\.?\s*§?\s*1927",
    ],
    secondary_indicators=[
        "frivolous", "bad faith", "vexatious", "harassment",
        "safe harbor"
    ],
    required_fields=[
        "case_number", "moving_party", "sanctionable_conduct",
        "sanctions_sought"
    ],
    description="Motion for Sanctions",
    response_deadline_days=21
)

# D14 - MOTION FOR DEFAULT JUDGMENT
FILING_TYPES["D14"] = FilingType(
    code="D14",
    name="DEFAULT",
    display_name="Motion for Default Judgment",
    category=FilingCategory.NON_DISPOSITIVE,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"(MOTION\s+FOR\s+)?DEFAULT\s+JUDGMENT",
        r"RULE\s+55",
        r"ENTRY\s+OF\s+DEFAULT",
    ],
    secondary_indicators=[
        "failed to appear", "failed to respond", "clerk's entry"
    ],
    required_fields=[
        "case_number", "moving_party", "defaulting_party",
        "damages_sought"
    ],
    description="Motion for Default Judgment",
    response_deadline_days=14
)

# ============================================================================
# CATEGORY E: OPPOSITIONS AND REPLIES
# ============================================================================

# E01 - OPPOSITION
FILING_TYPES["E01"] = FilingType(
    code="E01",
    name="OPPOSITION",
    display_name="Opposition to Motion",
    category=FilingCategory.OPPOSITION_REPLY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"OPPOSITION\s+TO",
        r"RESPONSE\s+IN\s+OPPOSITION",
        r"MEMORANDUM\s+IN\s+OPPOSITION",
        r"OBJECTION\s+TO",
    ],
    secondary_indicators=[
        "opposes", "should be denied", "fails to establish"
    ],
    required_fields=[
        "case_number", "opposing_party", "motion_opposed",
        "opposition_arguments"
    ],
    description="Opposition to any motion"
)

# E02 - REPLY BRIEF
FILING_TYPES["E02"] = FilingType(
    code="E02",
    name="REPLY_BRIEF",
    display_name="Reply in Support of Motion",
    category=FilingCategory.OPPOSITION_REPLY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"REPLY\s+(BRIEF\s+)?(IN\s+SUPPORT)?",
        r"REPLY\s+MEMORANDUM",
        r"REPLY\s+TO\s+OPPOSITION",
    ],
    secondary_indicators=[
        "in reply", "responds to", "opposition fails"
    ],
    required_fields=[
        "case_number", "replying_party", "motion_at_issue"
    ],
    description="Reply in support of motion"
)

# E03 - SUR-REPLY
FILING_TYPES["E03"] = FilingType(
    code="E03",
    name="SUR_REPLY",
    display_name="Sur-Reply",
    category=FilingCategory.OPPOSITION_REPLY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"SUR[\-\s]?REPLY",
        r"LEAVE\s+TO\s+FILE\s+SUR[\-\s]?REPLY",
    ],
    secondary_indicators=[
        "new arguments", "new evidence", "with leave"
    ],
    required_fields=["case_number", "filing_party"],
    description="Sur-reply (if permitted)"
)

# ============================================================================
# CATEGORY F: COURT ORDERS
# ============================================================================

# F01 - SCHEDULING ORDER
FILING_TYPES["F01"] = FilingType(
    code="F01",
    name="SCHEDULING_ORDER",
    display_name="Scheduling Order",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"SCHEDULING\s+ORDER",
        r"CASE\s+MANAGEMENT\s+ORDER",
        r"CMO",
        r"RULE\s+16",
    ],
    secondary_indicators=[
        "discovery cutoff", "dispositive motion deadline",
        "pretrial conference", "trial date"
    ],
    required_fields=[
        "case_number", "court_name", "judge",
        "key_dates", "deadlines"
    ],
    description="Case management/scheduling order"
)

# F02 - ORDER ON MOTION TO DISMISS
FILING_TYPES["F02"] = FilingType(
    code="F02",
    name="ORDER_MTD",
    display_name="Order on Motion to Dismiss",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"ORDER.*MOTION\s+TO\s+DISMISS",
        r"ORDER\s+GRANTING.*DISMISS",
        r"ORDER\s+DENYING.*DISMISS",
    ],
    secondary_indicators=[
        "GRANTED", "DENIED", "with prejudice", "without prejudice",
        "leave to amend"
    ],
    required_fields=[
        "case_number", "judge", "disposition", "claims_affected",
        "reasoning"
    ],
    optional_fields=["leave_to_amend", "amendment_deadline"],
    description="Order on Motion to Dismiss"
)

# F03 - ORDER ON SUMMARY JUDGMENT
FILING_TYPES["F03"] = FilingType(
    code="F03",
    name="ORDER_MSJ",
    display_name="Order on Summary Judgment",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"ORDER.*SUMMARY\s+JUDGMENT",
        r"ORDER\s+GRANTING.*SUMMARY",
        r"ORDER\s+DENYING.*SUMMARY",
    ],
    secondary_indicators=[
        "GRANTED", "DENIED", "genuine issue", "material fact"
    ],
    required_fields=[
        "case_number", "judge", "disposition", "claims_resolved",
        "reasoning"
    ],
    description="Order on Summary Judgment"
)

# F04 - JUDGMENT
FILING_TYPES["F04"] = FilingType(
    code="F04",
    name="JUDGMENT",
    display_name="Final Judgment",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"^JUDGMENT$",
        r"FINAL\s+JUDGMENT",
        r"JUDGMENT\s+IS\s+ENTERED",
    ],
    secondary_indicators=[
        "judgment is entered", "costs", "prevailing party"
    ],
    required_fields=[
        "case_number", "judge", "prevailing_party",
        "relief_granted", "entry_date"
    ],
    description="Final judgment"
)

# F05 - DEFAULT JUDGMENT
FILING_TYPES["F05"] = FilingType(
    code="F05",
    name="DEFAULT_JUDGMENT",
    display_name="Default Judgment",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"DEFAULT\s+JUDGMENT",
        r"JUDGMENT\s+BY\s+DEFAULT",
    ],
    secondary_indicators=["failure to respond", "damages awarded"],
    required_fields=[
        "case_number", "defaulting_party", "judgment_amount"
    ],
    description="Default judgment"
)

# F06 - CONSENT DECREE
FILING_TYPES["F06"] = FilingType(
    code="F06",
    name="CONSENT_DECREE",
    display_name="Consent Decree/Order",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"CONSENT\s+(DECREE|ORDER|JUDGMENT)",
        r"STIPULATED\s+(JUDGMENT|ORDER)",
    ],
    secondary_indicators=[
        "agreed", "stipulated", "settlement", "parties consent"
    ],
    required_fields=[
        "case_number", "parties_to_consent", "terms",
        "obligations"
    ],
    optional_fields=["settlement_amount", "injunctive_terms"],
    description="Court-approved settlement"
)

# F07 - TRO ORDER
FILING_TYPES["F07"] = FilingType(
    code="F07",
    name="TRO_ORDER",
    display_name="TRO Order",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"ORDER\s+GRANTING.*TRO",
        r"TEMPORARY\s+RESTRAINING\s+ORDER\s+(IS\s+)?GRANTED",
    ],
    secondary_indicators=[
        "restrained", "enjoined", "expires", "14 days"
    ],
    required_fields=[
        "case_number", "judge", "restraints_imposed",
        "expiration_date", "bond_amount"
    ],
    description="TRO granted/denied"
)

# F08 - PI ORDER
FILING_TYPES["F08"] = FilingType(
    code="F08",
    name="PI_ORDER",
    display_name="Preliminary Injunction Order",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"ORDER\s+GRANTING.*PRELIMINARY\s+INJUNCTION",
        r"PRELIMINARY\s+INJUNCTION\s+(IS\s+)?GRANTED",
    ],
    secondary_indicators=[
        "enjoined", "Winter factors", "bond"
    ],
    required_fields=[
        "case_number", "judge", "injunctive_relief",
        "bond_amount"
    ],
    description="Preliminary injunction order"
)

# F09 - MINUTE ORDER
FILING_TYPES["F09"] = FilingType(
    code="F09",
    name="MINUTE_ORDER",
    display_name="Minute Order",
    category=FilingCategory.COURT_ORDERS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MINUTE\s+ORDER",
        r"MINUTES\s+OF",
        r"CIVIL\s+MINUTES",
    ],
    secondary_indicators=[
        "proceedings", "appearances", "Court orders"
    ],
    required_fields=[
        "case_number", "date", "proceedings_summary"
    ],
    description="Brief procedural order"
)

# ============================================================================
# CATEGORY G: BRIEFS AND MEMORANDA
# ============================================================================

# G01 - MEMORANDUM IN SUPPORT
FILING_TYPES["G01"] = FilingType(
    code="G01",
    name="MEMO_ISO",
    display_name="Memorandum in Support",
    category=FilingCategory.BRIEFS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"MEMORANDUM\s+(OF\s+POINTS\s+AND\s+AUTHORITIES\s+)?IN\s+SUPPORT",
        r"BRIEF\s+IN\s+SUPPORT",
        r"POINTS\s+AND\s+AUTHORITIES",
    ],
    secondary_indicators=[
        "legal standard", "argument", "conclusion"
    ],
    required_fields=[
        "case_number", "filing_party", "motion_supported",
        "arguments", "authorities_cited"
    ],
    description="Memorandum in Support of Motion"
)

# G02 - OPENING BRIEF (APPEAL)
FILING_TYPES["G02"] = FilingType(
    code="G02",
    name="OPENING_BRIEF",
    display_name="Appellant's Opening Brief",
    category=FilingCategory.BRIEFS,
    practice_areas=[PracticeArea.APPELLATE],
    trigger_patterns=[
        r"(APPELLANT'?S?|PETITIONER'?S?)\s+OPENING\s+BRIEF",
        r"OPENING\s+BRIEF",
        r"BRIEF\s+OF\s+APPELLANT",
    ],
    secondary_indicators=[
        "standard of review", "statement of issues", "statement of the case",
        "argument", "FRAP"
    ],
    required_fields=[
        "case_number", "appellant", "appellee",
        "issues_on_appeal", "arguments"
    ],
    description="Appellant's Opening Brief"
)

# G03 - ANSWERING BRIEF
FILING_TYPES["G03"] = FilingType(
    code="G03",
    name="ANSWERING_BRIEF",
    display_name="Appellee's Answering Brief",
    category=FilingCategory.BRIEFS,
    practice_areas=[PracticeArea.APPELLATE],
    trigger_patterns=[
        r"(APPELLEE'?S?|RESPONDENT'?S?)\s+(ANSWERING|RESPONSE)\s+BRIEF",
        r"ANSWERING\s+BRIEF",
        r"BRIEF\s+OF\s+APPELLEE",
    ],
    secondary_indicators=[
        "affirm", "standard of review", "response to"
    ],
    required_fields=[
        "case_number", "appellee", "response_arguments"
    ],
    description="Appellee's Answering Brief"
)

# G04 - REPLY BRIEF (APPEAL)
FILING_TYPES["G04"] = FilingType(
    code="G04",
    name="REPLY_BRIEF_APPEAL",
    display_name="Appellant's Reply Brief",
    category=FilingCategory.BRIEFS,
    practice_areas=[PracticeArea.APPELLATE],
    trigger_patterns=[
        r"(APPELLANT'?S?|PETITIONER'?S?)\s+REPLY\s+BRIEF",
        r"REPLY\s+BRIEF",
    ],
    secondary_indicators=["in reply", "response fails"],
    required_fields=["case_number", "appellant", "reply_arguments"],
    description="Appellant's Reply Brief"
)

# G05 - AMICUS BRIEF
FILING_TYPES["G05"] = FilingType(
    code="G05",
    name="AMICUS",
    display_name="Amicus Curiae Brief",
    category=FilingCategory.BRIEFS,
    practice_areas=[PracticeArea.APPELLATE, PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"AMICUS\s+CURIAE",
        r"BRIEF\s+OF\s+AMICUS",
        r"FRIEND\s+OF\s+THE\s+COURT",
    ],
    secondary_indicators=[
        "interest of amicus", "leave of court", "consent of parties"
    ],
    required_fields=[
        "case_number", "amicus_identity", "interest_statement",
        "arguments"
    ],
    description="Amicus Curiae Brief"
)

# G06 - TRIAL BRIEF
FILING_TYPES["G06"] = FilingType(
    code="G06",
    name="TRIAL_BRIEF",
    display_name="Trial Brief",
    category=FilingCategory.BRIEFS,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"TRIAL\s+BRIEF",
        r"PRE[\-\s]?TRIAL\s+BRIEF",
    ],
    secondary_indicators=[
        "evidence at trial", "witnesses", "exhibits", "jury instructions"
    ],
    required_fields=[
        "case_number", "filing_party", "issues_for_trial",
        "anticipated_evidence"
    ],
    description="Pre-trial brief"
)

# ============================================================================
# CATEGORY H: DISCOVERY DOCUMENTS
# ============================================================================

# H01 - INTERROGATORIES
FILING_TYPES["H01"] = FilingType(
    code="H01",
    name="INTERROGATORIES",
    display_name="Interrogatories",
    category=FilingCategory.DISCOVERY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"INTERROGATOR(Y|IES)",
        r"FORM\s+INTERROGATOR(Y|IES)",
        r"SPECIAL\s+INTERROGATOR(Y|IES)",
    ],
    secondary_indicators=[
        "INTERROGATORY NO.", "Please state", "Identify"
    ],
    required_fields=[
        "case_number", "propounding_party", "responding_party",
        "number_of_interrogatories"
    ],
    description="Written questions"
)

# H02 - REQUESTS FOR PRODUCTION
FILING_TYPES["H02"] = FilingType(
    code="H02",
    name="RFP",
    display_name="Requests for Production",
    category=FilingCategory.DISCOVERY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"REQUEST(S)?\s+FOR\s+PRODUCTION",
        r"RFP(S)?",
        r"DOCUMENT\s+REQUEST(S)?",
    ],
    secondary_indicators=[
        "REQUEST NO.", "produce", "documents", "things"
    ],
    required_fields=[
        "case_number", "propounding_party", "responding_party",
        "number_of_requests"
    ],
    description="Requests for Production"
)

# H03 - REQUESTS FOR ADMISSION
FILING_TYPES["H03"] = FilingType(
    code="H03",
    name="RFA",
    display_name="Requests for Admission",
    category=FilingCategory.DISCOVERY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"REQUEST(S)?\s+FOR\s+ADMISSION",
        r"RFA(S)?",
    ],
    secondary_indicators=[
        "REQUEST NO.", "Admit that", "admit or deny"
    ],
    required_fields=[
        "case_number", "propounding_party", "responding_party",
        "number_of_requests"
    ],
    description="Requests for Admission"
)

# H04 - DEPOSITION NOTICE
FILING_TYPES["H04"] = FilingType(
    code="H04",
    name="DEPO_NOTICE",
    display_name="Deposition Notice",
    category=FilingCategory.DISCOVERY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"NOTICE\s+OF\s+DEPOSITION",
        r"NOTICE\s+OF\s+(TAKING\s+)?DEPO",
        r"RULE\s+30",
    ],
    secondary_indicators=[
        "deponent", "date and time", "location", "Rule 30(b)(6)"
    ],
    required_fields=[
        "case_number", "noticing_party", "deponent",
        "deposition_date", "location"
    ],
    description="Deposition Notice"
)

# H05 - SUBPOENA
FILING_TYPES["H05"] = FilingType(
    code="H05",
    name="SUBPOENA",
    display_name="Subpoena",
    category=FilingCategory.DISCOVERY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"SUBPOENA",
        r"SUBPOENA\s+DUCES\s+TECUM",
        r"RULE\s+45",
    ],
    secondary_indicators=[
        "YOU ARE COMMANDED", "documents", "testimony", "appearance"
    ],
    required_fields=[
        "case_number", "issuing_party", "recipient",
        "response_date", "documents_or_testimony"
    ],
    description="Subpoena (testimony or documents)"
)

# H06 - EXPERT REPORT
FILING_TYPES["H06"] = FilingType(
    code="H06",
    name="EXPERT_REPORT",
    display_name="Expert Report",
    category=FilingCategory.DISCOVERY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"EXPERT\s+(WITNESS\s+)?REPORT",
        r"RULE\s+26\s*\(\s*a\s*\)\s*\(\s*2\s*\)",
    ],
    secondary_indicators=[
        "qualifications", "opinions", "methodology", "basis",
        "compensation", "prior testimony"
    ],
    required_fields=[
        "case_number", "expert_name", "retaining_party",
        "subject_matter", "opinions"
    ],
    description="Expert witness report"
)

# H07 - INITIAL DISCLOSURES
FILING_TYPES["H07"] = FilingType(
    code="H07",
    name="INITIAL_DISCLOSURES",
    display_name="Initial Disclosures",
    category=FilingCategory.DISCOVERY,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[
        r"INITIAL\s+DISCLOSURE(S)?",
        r"RULE\s+26\s*\(\s*a\s*\)\s*\(\s*1\s*\)",
    ],
    secondary_indicators=[
        "individuals with knowledge", "documents", "damages computation",
        "insurance"
    ],
    required_fields=[
        "case_number", "disclosing_party", "witnesses_identified",
        "documents_identified"
    ],
    description="Rule 26 disclosures"
)

# ============================================================================
# CATEGORY S: SPECIALIZED FILINGS
# ============================================================================

# S01 - BANKRUPTCY PETITION
FILING_TYPES["S01"] = FilingType(
    code="S01",
    name="BK_PETITION",
    display_name="Bankruptcy Petition",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.BANKRUPTCY],
    trigger_patterns=[
        r"VOLUNTARY\s+PETITION",
        r"Chapter\s+(7|11|13)",
        r"Form\s+B?101",
        r"PETITION\s+FOR\s+RELIEF",
    ],
    secondary_indicators=[
        "debtor", "bankruptcy", "schedules", "341 meeting", "automatic stay",
        "creditor matrix"
    ],
    required_fields=[
        "case_number", "debtor", "chapter", "assets_total",
        "liabilities_total", "filing_date"
    ],
    optional_fields=["attorney", "venue", "joint_debtor"],
    description="Bankruptcy Petition"
)

# S02 - BANKRUPTCY SCHEDULES
FILING_TYPES["S02"] = FilingType(
    code="S02",
    name="BK_SCHEDULES",
    display_name="Bankruptcy Schedules",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.BANKRUPTCY],
    trigger_patterns=[
        r"SCHEDULE\s+[A-J]",
        r"SCHEDULES?\s+A/?B",
        r"SCHEDULES?\s+D/?E/?F",
        r"SUMMARY\s+OF\s+SCHEDULES",
    ],
    secondary_indicators=[
        "real property", "personal property", "secured claims",
        "priority claims", "unsecured claims", "executory contracts"
    ],
    required_fields=[
        "case_number", "debtor", "schedules_included",
        "total_assets", "total_liabilities"
    ],
    description="Bankruptcy Schedules A-J"
)

# S03 - PROOF OF CLAIM
FILING_TYPES["S03"] = FilingType(
    code="S03",
    name="PROOF_OF_CLAIM",
    display_name="Proof of Claim",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.BANKRUPTCY],
    trigger_patterns=[
        r"PROOF\s+OF\s+CLAIM",
        r"Form\s+B?410",
    ],
    secondary_indicators=[
        "claim amount", "basis for claim", "secured", "priority", "unsecured"
    ],
    required_fields=[
        "case_number", "creditor", "claim_amount",
        "claim_type", "basis_for_claim"
    ],
    description="Bankruptcy proof of claim"
)

# S04 - CHAPTER 11 PLAN
FILING_TYPES["S04"] = FilingType(
    code="S04",
    name="REORG_PLAN",
    display_name="Chapter 11 Reorganization Plan",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.BANKRUPTCY],
    trigger_patterns=[
        r"(CHAPTER\s+11\s+)?PLAN\s+OF\s+REORGANIZATION",
        r"DISCLOSURE\s+STATEMENT",
        r"PLAN\s+OF\s+LIQUIDATION",
    ],
    secondary_indicators=[
        "classes of claims", "treatment", "distributions",
        "effective date", "confirmation"
    ],
    required_fields=[
        "case_number", "debtor", "plan_proponent",
        "classes_of_claims", "proposed_treatment"
    ],
    description="Chapter 11 plan"
)

# S05 - DISSOLUTION PETITION
FILING_TYPES["S05"] = FilingType(
    code="S05",
    name="DISSOLUTION",
    display_name="Dissolution/Divorce Petition",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.FAMILY_LAW],
    trigger_patterns=[
        r"PETITION\s+FOR\s+DISSOLUTION",
        r"PETITION\s+FOR\s+DIVORCE",
        r"PETITION\s+FOR\s+LEGAL\s+SEPARATION",
    ],
    secondary_indicators=[
        "marriage", "irreconcilable differences", "property",
        "spousal support", "custody"
    ],
    required_fields=[
        "case_number", "petitioner", "respondent",
        "marriage_date", "separation_date", "relief_sought"
    ],
    description="Divorce/dissolution petition"
)

# S06 - CUSTODY PETITION/MOTION
FILING_TYPES["S06"] = FilingType(
    code="S06",
    name="CUSTODY",
    display_name="Custody Petition/Motion",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.FAMILY_LAW],
    trigger_patterns=[
        r"PETITION.*CUSTODY",
        r"MOTION.*(CUSTODY|VISITATION|PARENTING\s+TIME)",
        r"(LEGAL|PHYSICAL)\s+CUSTODY",
    ],
    secondary_indicators=[
        "best interest of child", "parenting plan", "visitation schedule"
    ],
    required_fields=[
        "case_number", "petitioner", "children",
        "custody_sought"
    ],
    description="Custody petition/motion"
)

# S07 - DV RESTRAINING ORDER
FILING_TYPES["S07"] = FilingType(
    code="S07",
    name="DV_RESTRAINING",
    display_name="Domestic Violence Restraining Order",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.FAMILY_LAW],
    trigger_patterns=[
        r"DOMESTIC\s+VIOLENCE",
        r"RESTRAINING\s+ORDER",
        r"PROTECTIVE\s+ORDER",
        r"DV[\-\s]?(RO|TRO)",
    ],
    secondary_indicators=[
        "abuse", "harassment", "stay away", "no contact", "protected person"
    ],
    required_fields=[
        "case_number", "protected_party", "restrained_party",
        "allegations", "relief_sought"
    ],
    description="Domestic violence restraining order"
)

# S08 - PROBATE PETITION
FILING_TYPES["S08"] = FilingType(
    code="S08",
    name="PROBATE_PETITION",
    display_name="Probate Petition",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.PROBATE],
    trigger_patterns=[
        r"PETITION\s+FOR\s+PROBATE",
        r"PETITION\s+FOR\s+LETTERS",
        r"PETITION\s+TO\s+ADMINISTER\s+ESTATE",
    ],
    secondary_indicators=[
        "decedent", "estate", "executor", "administrator", "will"
    ],
    required_fields=[
        "case_number", "decedent", "petitioner",
        "estate_value", "heirs"
    ],
    description="Probate petition"
)

# S09 - HABEAS CORPUS
FILING_TYPES["S09"] = FilingType(
    code="S09",
    name="HABEAS",
    display_name="Habeas Corpus Petition",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.CRIMINAL],
    trigger_patterns=[
        r"HABEAS\s+CORPUS",
        r"28\s*U\.?S\.?C\.?\s*§?\s*2254",
        r"28\s*U\.?S\.?C\.?\s*§?\s*2255",
    ],
    secondary_indicators=[
        "unlawful custody", "constitutional violation",
        "ineffective assistance", "exhaustion"
    ],
    required_fields=[
        "case_number", "petitioner", "respondent",
        "conviction_challenged", "grounds_for_relief"
    ],
    description="Habeas corpus petition"
)

# S10 - EEOC CHARGE
FILING_TYPES["S10"] = FilingType(
    code="S10",
    name="EEOC_CHARGE",
    display_name="EEOC Discrimination Charge",
    category=FilingCategory.SPECIALIZED,
    practice_areas=[PracticeArea.EMPLOYMENT],
    trigger_patterns=[
        r"EEOC\s+CHARGE",
        r"CHARGE\s+OF\s+DISCRIMINATION",
        r"TITLE\s+VII",
    ],
    secondary_indicators=[
        "discrimination", "harassment", "retaliation",
        "protected class", "adverse action"
    ],
    required_fields=[
        "charge_number", "charging_party", "respondent_employer",
        "protected_class", "adverse_action", "allegations"
    ],
    description="EEOC discrimination charge"
)

# ============================================================================
# CATEGORY P: APPELLATE FILINGS
# ============================================================================

# P01 - NOTICE OF APPEAL
FILING_TYPES["P01"] = FilingType(
    code="P01",
    name="NOTICE_OF_APPEAL",
    display_name="Notice of Appeal",
    category=FilingCategory.APPEALS,
    practice_areas=[PracticeArea.APPELLATE],
    trigger_patterns=[
        r"NOTICE\s+OF\s+APPEAL",
        r"FRAP\s+3",
        r"APPEALS?\s+FROM",
    ],
    secondary_indicators=[
        "appeals from", "judgment entered", "final order"
    ],
    required_fields=[
        "case_number", "appellant", "appellee",
        "judgment_appealed", "judgment_date"
    ],
    description="Notice of Appeal"
)

# P02 - PETITION FOR WRIT OF CERTIORARI
FILING_TYPES["P02"] = FilingType(
    code="P02",
    name="CERT_PETITION",
    display_name="Petition for Writ of Certiorari",
    category=FilingCategory.APPEALS,
    practice_areas=[PracticeArea.APPELLATE],
    trigger_patterns=[
        r"WRIT\s+OF\s+CERTIORARI",
        r"PETITION\s+FOR\s+CERT",
        r"CERTIORARI",
    ],
    secondary_indicators=[
        "Supreme Court", "circuit split", "question presented"
    ],
    required_fields=[
        "case_number", "petitioner", "respondent",
        "questions_presented", "lower_court_decision"
    ],
    description="Petition for Writ of Certiorari"
)

# P03 - PETITION FOR WRIT OF MANDAMUS
FILING_TYPES["P03"] = FilingType(
    code="P03",
    name="MANDAMUS",
    display_name="Petition for Writ of Mandamus",
    category=FilingCategory.APPEALS,
    practice_areas=[PracticeArea.APPELLATE],
    trigger_patterns=[
        r"WRIT\s+OF\s+MANDAMUS",
        r"MANDAMUS",
        r"PETITION\s+FOR\s+EXTRAORDINARY\s+RELIEF",
    ],
    secondary_indicators=[
        "clear and indisputable right", "ministerial duty", "no adequate remedy"
    ],
    required_fields=[
        "case_number", "petitioner", "respondent_court",
        "relief_sought", "basis_for_writ"
    ],
    description="Petition for Writ of Mandamus"
)

# ============================================================================
# CATEGORY R: ADMINISTRATIVE FILINGS
# ============================================================================

# R01 - NLRB CHARGE
FILING_TYPES["R01"] = FilingType(
    code="R01",
    name="NLRB_CHARGE",
    display_name="NLRB Unfair Labor Practice Charge",
    category=FilingCategory.ADMINISTRATIVE,
    practice_areas=[PracticeArea.ADMINISTRATIVE, PracticeArea.EMPLOYMENT],
    trigger_patterns=[
        r"NLRB",
        r"UNFAIR\s+LABOR\s+PRACTICE",
        r"CHARGE\s+AGAINST\s+EMPLOYER",
    ],
    secondary_indicators=[
        "Section 8(a)", "Section 8(b)", "interference", "discrimination"
    ],
    required_fields=[
        "case_number", "charging_party", "charged_party",
        "allegations"
    ],
    description="NLRB Unfair Labor Practice Charge"
)

# R02 - SEC FILING
FILING_TYPES["R02"] = FilingType(
    code="R02",
    name="SEC_ENFORCEMENT",
    display_name="SEC Enforcement Action",
    category=FilingCategory.ADMINISTRATIVE,
    practice_areas=[PracticeArea.SECURITIES, PracticeArea.ADMINISTRATIVE],
    trigger_patterns=[
        r"SECURITIES\s+AND\s+EXCHANGE\s+COMMISSION",
        r"SEC\s+v\.",
        r"15\s*U\.?S\.?C\.?\s*§?\s*78",
    ],
    secondary_indicators=[
        "securities fraud", "insider trading", "registration violation"
    ],
    required_fields=[
        "case_number", "respondent", "violations_alleged",
        "relief_sought"
    ],
    description="SEC Enforcement Action"
)

# R03 - FTC ACTION
FILING_TYPES["R03"] = FilingType(
    code="R03",
    name="FTC_ACTION",
    display_name="FTC Enforcement Action",
    category=FilingCategory.ADMINISTRATIVE,
    practice_areas=[PracticeArea.ANTITRUST, PracticeArea.ADMINISTRATIVE],
    trigger_patterns=[
        r"FEDERAL\s+TRADE\s+COMMISSION",
        r"FTC\s+v\.",
        r"15\s*U\.?S\.?C\.?\s*§?\s*45",
    ],
    secondary_indicators=[
        "unfair trade practices", "deceptive acts", "antitrust"
    ],
    required_fields=[
        "case_number", "respondent", "violations_alleged"
    ],
    description="FTC Enforcement Action"
)

# ============================================================================
# CATEGORY X: OTHER/UNCLASSIFIED
# ============================================================================

# X01 - UNCLASSIFIED
FILING_TYPES["X01"] = FilingType(
    code="X01",
    name="OTHER",
    display_name="Other/Unclassified Filing",
    category=FilingCategory.OTHER,
    practice_areas=[PracticeArea.CIVIL_LITIGATION],
    trigger_patterns=[],
    secondary_indicators=[],
    required_fields=["case_number"],
    description="Unclassified filing type"
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_filing_type(code: str) -> Optional[FilingType]:
    """Get filing type by code"""
    return FILING_TYPES.get(code)


def get_filing_types_by_category(category: FilingCategory) -> List[FilingType]:
    """Get all filing types in a category"""
    return [ft for ft in FILING_TYPES.values() if ft.category == category]


def get_filing_types_by_practice_area(practice_area: PracticeArea) -> List[FilingType]:
    """Get all filing types for a practice area"""
    return [ft for ft in FILING_TYPES.values() if practice_area in ft.practice_areas]


def get_all_codes() -> List[str]:
    """Get all filing type codes"""
    return list(FILING_TYPES.keys())


def get_code_to_name_mapping() -> Dict[str, str]:
    """Get mapping of codes to display names"""
    return {code: ft.display_name for code, ft in FILING_TYPES.items()}


# Create compiled pattern cache for efficient classification
COMPILED_PATTERNS: Dict[str, List[Pattern]] = {}

def get_compiled_patterns(code: str) -> List[Pattern]:
    """Get compiled regex patterns for a filing type (cached)"""
    if code not in COMPILED_PATTERNS:
        ft = FILING_TYPES.get(code)
        if ft:
            COMPILED_PATTERNS[code] = ft.compile_patterns()
        else:
            COMPILED_PATTERNS[code] = []
    return COMPILED_PATTERNS[code]


def get_all_filing_types() -> Dict[str, 'FilingType']:
    """Get all filing types as a dictionary"""
    return FILING_TYPES


def search_filing_types(query: str) -> List['FilingType']:
    """
    Search filing types by name, description, or display name

    Args:
        query: Search query string

    Returns:
        List of matching FilingType objects
    """
    query = query.lower()
    results = []

    for ft in FILING_TYPES.values():
        # Search in name, display_name, and description
        if (query in ft.name.lower() or
            query in ft.display_name.lower() or
            query in ft.description.lower()):
            results.append(ft)

    return results


def classify_filing_by_patterns(text: str) -> List[Dict[str, Any]]:
    """
    Classify a filing based on text patterns

    Args:
        text: Document text or title to classify

    Returns:
        List of matches with code, name, and confidence
    """
    import re
    matches = []
    text_lower = text.lower()

    for code, ft in FILING_TYPES.items():
        patterns = get_compiled_patterns(code)
        for pattern in patterns:
            if pattern.search(text_lower):
                matches.append({
                    'code': code,
                    'name': ft.display_name,
                    'confidence': 0.85,
                    'category': ft.category.value if hasattr(ft.category, 'value') else str(ft.category)
                })
                break  # Only one match per filing type

    # Sort by confidence (all same for now) and return
    return sorted(matches, key=lambda x: x['confidence'], reverse=True)


# Filing categories for reference
FILING_CATEGORIES = {
    'A': 'Complaints and Initial Pleadings',
    'B': 'Answers and Responsive Pleadings',
    'C': 'Pre-Answer Motions',
    'D': 'Discovery Motions',
    'E': 'Dispositive Motions',
    'F': 'Trial Motions',
    'G': 'Evidence/Witness Motions',
    'H': 'Settlement and ADR',
    'I': 'Default and Compliance',
    'J': 'Procedural/Administrative',
    'K': 'Status and Case Management',
    'L': 'Emergency Motions',
    'M': 'Special Proceedings',
    'N': 'Consolidation/Transfer',
    'O': 'Post-Trial Motions',
    'P': 'Appeal Filings',
    'R': 'Administrative Proceedings',
    'S': 'Pro Se and IFP',
    'X': 'Other/Miscellaneous',
}


# Export all filing types for easy access
__all__ = [
    'FilingType',
    'FilingCategory',
    'PracticeArea',
    'FILING_TYPES',
    'FILING_CATEGORIES',
    'get_filing_type',
    'get_filing_types_by_category',
    'get_filing_types_by_practice_area',
    'get_all_codes',
    'get_code_to_name_mapping',
    'get_compiled_patterns',
    'get_all_filing_types',
    'search_filing_types',
    'classify_filing_by_patterns',
]
