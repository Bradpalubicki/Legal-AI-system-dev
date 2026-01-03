#!/usr/bin/env python3
"""
Educational Content Library
Legal AI System - Comprehensive Educational Resources

This module provides a comprehensive library of educational legal content including:
- General bankruptcy information for learning purposes
- Court procedure explanations
- Legal term glossary with definitions
- Common document types and their purposes
- Typical legal timelines for educational understanding

ALL CONTENT IS FOR EDUCATIONAL PURPOSES ONLY - NOT LEGAL ADVICE
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import compliance components
try:
    from ..core.attorney_review import AttorneyReviewSystem
except ImportError:
    class AttorneyReviewSystem:
        def review_content(self, **kwargs):
            class MockResult:
                requires_review = False
                risk_level = type('obj', (object,), {'value': 'low'})()
            return MockResult()

try:
    from ..core.audit_logger import AuditLogger
except ImportError:
    class AuditLogger:
        def log_document_event(self, **kwargs): pass

# Setup logging
logger = logging.getLogger('educational_content')

class ContentType(str, Enum):
    """Types of educational content"""
    BANKRUPTCY_INFO = "bankruptcy_info"
    COURT_PROCEDURE = "court_procedure"
    LEGAL_GLOSSARY = "legal_glossary"
    DOCUMENT_TYPES = "document_types"
    TIMELINES = "timelines"
    FAQ = "faq"
    GENERAL_INFO = "general_info"

class SubjectArea(str, Enum):
    """Subject areas for legal education"""
    BANKRUPTCY = "bankruptcy"
    CIVIL_PROCEDURE = "civil_procedure"
    FAMILY_LAW = "family_law"
    CONTRACT_LAW = "contract_law"
    CRIMINAL_LAW = "criminal_law"
    EMPLOYMENT_LAW = "employment_law"
    REAL_ESTATE = "real_estate"
    GENERAL = "general"

class EducationLevel(str, Enum):
    """Educational complexity levels"""
    BEGINNER = "beginner"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class EducationalContent:
    """Individual piece of educational content"""
    content_id: str
    title: str
    content_type: ContentType
    subject_area: SubjectArea
    education_level: EducationLevel
    summary: str
    detailed_content: str
    key_concepts: List[str]
    related_topics: List[str]
    official_sources: List[str]
    last_updated: datetime
    educational_objectives: List[str]
    disclaimers: List[str]
    attorney_review_notes: Optional[str] = None

@dataclass
class ContentQuery:
    """Query for educational content"""
    query_id: str
    subject_areas: List[SubjectArea]
    content_types: List[ContentType]
    education_level: EducationLevel
    keywords: List[str]
    document_context: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class ContentResponse:
    """Response containing educational content"""
    response_id: str
    matched_content: List[EducationalContent]
    related_content: List[EducationalContent]
    official_resources: List[Dict[str, str]]
    disclaimers: List[str]
    attorney_consultation_notice: str
    educational_warnings: List[str]
    relevance_score: float = 0.8

    @property
    def results(self) -> List[EducationalContent]:
        """Alias for matched_content to maintain compatibility"""
        return self.matched_content

class EducationalContentLibrary:
    """
    Comprehensive educational content library with compliance safeguards
    """

    def __init__(self, storage_root: str = "storage/educational_content"):
        self.logger = logger
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Initialize compliance components
        self.attorney_review = AttorneyReviewSystem()
        self.audit_logger = AuditLogger()

        # Standard disclaimers for educational content
        self.disclaimers = [
            "This content is for educational purposes only and does not constitute legal advice.",
            "Laws and procedures vary by jurisdiction - consult local legal resources.",
            "Always seek qualified legal counsel for specific legal matters.",
            "This information may not reflect current law - verify with official sources."
        ]

        # Load educational content
        self.content_database = {}
        self._initialize_content_library()

    def _initialize_content_library(self):
        """Initialize the educational content library"""
        self._load_bankruptcy_content()
        self._load_court_procedure_content()
        self._load_legal_glossary()
        self._load_document_types()
        self._load_timeline_information()
        self._load_faq_content()

    def _load_bankruptcy_content(self):
        """Load bankruptcy educational content"""
        bankruptcy_content = [
            EducationalContent(
                content_id="bankruptcy_001",
                title="Introduction to Bankruptcy Law",
                content_type=ContentType.BANKRUPTCY_INFO,
                subject_area=SubjectArea.BANKRUPTCY,
                education_level=EducationLevel.BASIC,
                summary="Educational overview of bankruptcy law and its purposes",
                detailed_content="""
                Bankruptcy law is a federal law designed to help individuals and businesses eliminate or repay their debts.
                The primary goals of bankruptcy are to give debtors a fresh start and ensure fair treatment of creditors.

                Key Educational Points:
                • Bankruptcy is governed by federal law (Title 11 of the U.S. Code)
                • There are several chapters of bankruptcy, each serving different purposes
                • The process involves court supervision and appointed trustees
                • Automatic stay provisions protect debtors from collection activities
                • Not all debts can be discharged in bankruptcy

                Common Bankruptcy Chapters:
                • Chapter 7: Liquidation bankruptcy for individuals and businesses
                • Chapter 11: Reorganization for businesses and high-income individuals
                • Chapter 13: Payment plan for individuals with regular income

                This information is for educational purposes only. Bankruptcy law is complex and varies by jurisdiction.
                """,
                key_concepts=["discharge", "automatic stay", "trustee", "creditors", "fresh start"],
                related_topics=["debt relief", "court procedures", "financial planning"],
                official_sources=[
                    "https://www.uscourts.gov/services-forms/bankruptcy",
                    "https://www.justice.gov/ust"
                ],
                last_updated=datetime.now(),
                educational_objectives=[
                    "Understand the basic purpose of bankruptcy law",
                    "Learn about different bankruptcy chapters",
                    "Recognize key bankruptcy concepts and terminology"
                ],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="bankruptcy_002",
                title="Chapter 7 Bankruptcy Process",
                content_type=ContentType.BANKRUPTCY_INFO,
                subject_area=SubjectArea.BANKRUPTCY,
                education_level=EducationLevel.INTERMEDIATE,
                summary="Educational overview of Chapter 7 bankruptcy procedures",
                detailed_content="""
                Chapter 7 bankruptcy, also known as "liquidation bankruptcy," is designed for debtors who cannot
                pay their debts. This educational overview covers the typical process:

                1. Filing the Petition:
                   • Voluntary petition filed by debtor
                   • Required schedules listing assets, debts, income, and expenses
                   • Filing fee and credit counseling certificate required

                2. Automatic Stay:
                   • Immediately stops most collection activities
                   • Protects debtor's property from seizure
                   • Prevents lawsuits and wage garnishment

                3. Trustee Appointment:
                   • Court appoints trustee to administer the case
                   • Trustee reviews documents and may sell non-exempt property
                   • Trustee distributes proceeds to creditors

                4. Meeting of Creditors:
                   • Also called "341 meeting"
                   • Debtor answers questions under oath
                   • Creditors may attend but rarely do

                5. Discharge:
                   • Court order eliminating qualifying debts
                   • Usually occurs 3-4 months after filing
                   • Some debts are not dischargeable

                Educational Note: This process can vary significantly based on individual circumstances and jurisdiction.
                """,
                key_concepts=["liquidation", "341 meeting", "exemptions", "discharge", "non-exempt property"],
                related_topics=["automatic stay", "trustee duties", "creditor rights"],
                official_sources=[
                    "https://www.uscourts.gov/services-forms/bankruptcy/bankruptcy-basics/chapter-7-bankruptcy-basics"
                ],
                last_updated=datetime.now(),
                educational_objectives=[
                    "Learn the Chapter 7 bankruptcy process",
                    "Understand the role of trustees and creditors",
                    "Recognize key deadlines and requirements"
                ],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="bankruptcy_003",
                title="Automatic Stay Provisions",
                content_type=ContentType.BANKRUPTCY_INFO,
                subject_area=SubjectArea.BANKRUPTCY,
                education_level=EducationLevel.INTERMEDIATE,
                summary="Educational explanation of automatic stay protections",
                detailed_content="""
                The automatic stay is one of the most important protections in bankruptcy law. It takes effect
                immediately upon filing a bankruptcy petition.

                What the Automatic Stay Does (Educational Overview):
                • Stops most collection activities against the debtor
                • Prevents creditors from starting or continuing lawsuits
                • Halts wage garnishment and bank account freezes
                • Stops foreclosure proceedings (temporarily)
                • Prevents utility shut-offs for 20 days

                What the Automatic Stay Does NOT Cover:
                • Criminal proceedings
                • Certain tax proceedings
                • Domestic support obligations (alimony, child support)
                • Some regulatory actions

                Relief from Stay:
                • Creditors can request court permission to continue collection
                • Common in secured debt cases (mortgages, car loans)
                • Court considers factors like equity and necessity

                Violations of the Stay:
                • Creditors who violate the stay may face sanctions
                • Debtors can seek damages for willful violations
                • Automatic stay violations are taken seriously by courts

                Educational Note: Stay provisions have many exceptions and limitations that vary by case type.
                """,
                key_concepts=["automatic stay", "relief from stay", "secured debt", "violations", "sanctions"],
                related_topics=["creditor rights", "court procedures", "debt collection"],
                official_sources=[
                    "https://www.law.cornell.edu/uscode/text/11/362"
                ],
                last_updated=datetime.now(),
                educational_objectives=[
                    "Understand automatic stay protections",
                    "Learn about exceptions and limitations",
                    "Recognize relief from stay procedures"
                ],
                disclaimers=self.disclaimers
            )
        ]

        for content in bankruptcy_content:
            self.content_database[content.content_id] = content

    def _load_court_procedure_content(self):
        """Load court procedure educational content"""
        procedure_content = [
            EducationalContent(
                content_id="procedure_001",
                title="Federal Court System Overview",
                content_type=ContentType.COURT_PROCEDURE,
                subject_area=SubjectArea.CIVIL_PROCEDURE,
                education_level=EducationLevel.BASIC,
                summary="Educational overview of the federal court system structure",
                detailed_content="""
                The federal court system is organized into three main levels, each serving specific functions
                in the administration of justice.

                District Courts (Trial Level):
                • 94 federal judicial districts nationwide
                • Handle most federal cases initially
                • One judge typically presides over trials
                • Jury trials available for most cases

                Courts of Appeals (Appellate Level):
                • 13 circuit courts of appeals
                • Review decisions from district courts
                • Panels of three judges typically hear cases
                • Focus on legal issues, not factual disputes

                Supreme Court (Highest Level):
                • Final arbiter of federal law
                • Nine justices serve for life
                • Discretionary jurisdiction (chooses most cases)
                • Issues binding precedent for all courts

                Specialized Courts:
                • Bankruptcy courts (under district courts)
                • Tax courts
                • Claims courts
                • Military courts

                Educational Note: This overview covers federal courts only. State court systems have different structures.
                """,
                key_concepts=["jurisdiction", "appellate review", "precedent", "trial court", "specialized courts"],
                related_topics=["legal procedures", "appeals process", "court rules"],
                official_sources=[
                    "https://www.uscourts.gov/about-federal-courts"
                ],
                last_updated=datetime.now(),
                educational_objectives=[
                    "Understand federal court structure",
                    "Learn the role of different court levels",
                    "Recognize specialized court functions"
                ],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="procedure_002",
                title="Civil Litigation Process",
                content_type=ContentType.COURT_PROCEDURE,
                subject_area=SubjectArea.CIVIL_PROCEDURE,
                education_level=EducationLevel.INTERMEDIATE,
                summary="Educational overview of civil litigation procedures",
                detailed_content="""
                Civil litigation follows a structured process designed to ensure fair resolution of disputes.
                This educational overview covers typical stages:

                1. Pleading Stage:
                   • Complaint: Initial document stating claims
                   • Answer: Defendant's response to complaint
                   • Motions to dismiss or for more definite statement

                2. Discovery Phase:
                   • Interrogatories: Written questions under oath
                   • Depositions: Oral testimony under oath
                   • Document requests: Production of relevant papers
                   • Expert witness disclosure and testimony

                3. Pre-Trial Motions:
                   • Summary judgment motions
                   • Motions in limine (evidence rulings)
                   • Settlement conferences

                4. Trial:
                   • Jury selection (if jury trial)
                   • Opening statements
                   • Presentation of evidence
                   • Closing arguments and jury instructions

                5. Post-Trial:
                   • Verdict and judgment
                   • Post-trial motions
                   • Appeals process

                Educational Note: Procedures vary significantly between courts and case types.
                """,
                key_concepts=["pleadings", "discovery", "summary judgment", "voir dire", "appeals"],
                related_topics=["evidence rules", "settlement", "jury trials"],
                official_sources=[
                    "https://www.law.cornell.edu/rules/frcp"
                ],
                last_updated=datetime.now(),
                educational_objectives=[
                    "Learn civil litigation stages",
                    "Understand discovery procedures",
                    "Recognize key procedural concepts"
                ],
                disclaimers=self.disclaimers
            )
        ]

        for content in procedure_content:
            self.content_database[content.content_id] = content

    def _load_legal_glossary(self):
        """Load legal terminology glossary"""
        glossary_terms = [
            EducationalContent(
                content_id="glossary_001",
                title="Affidavit",
                content_type=ContentType.LEGAL_GLOSSARY,
                subject_area=SubjectArea.GENERAL,
                education_level=EducationLevel.BASIC,
                summary="A written statement made under oath",
                detailed_content="""
                An affidavit is a written statement of facts that is sworn to be true by the person making it (the affiant).
                The statement is made under oath before a notary public or other authorized official.

                Key Characteristics:
                • Must be sworn to under penalty of perjury
                • Requires notarization or similar authentication
                • Used as evidence in legal proceedings
                • Can be used when live testimony is not practical

                Common Uses:
                • Supporting motions in court
                • Providing evidence for summary judgment
                • Establishing facts in uncontested matters
                • Immigration and family law proceedings

                Educational Note: Requirements for affidavits vary by jurisdiction and purpose.
                """,
                key_concepts=["oath", "notarization", "perjury", "evidence", "sworn statement"],
                related_topics=["testimony", "court procedures", "evidence rules"],
                official_sources=["https://www.law.cornell.edu/wex/affidavit"],
                last_updated=datetime.now(),
                educational_objectives=["Understand what constitutes an affidavit", "Learn about oath requirements"],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="glossary_002",
                title="Jurisdiction",
                content_type=ContentType.LEGAL_GLOSSARY,
                subject_area=SubjectArea.GENERAL,
                education_level=EducationLevel.INTERMEDIATE,
                summary="The authority of a court to hear and decide cases",
                detailed_content="""
                Jurisdiction refers to a court's legal authority to hear and decide cases. It encompasses both
                the power to hear certain types of cases and the geographical area where that power can be exercised.

                Types of Jurisdiction:
                • Subject Matter Jurisdiction: Authority over specific types of cases
                • Personal Jurisdiction: Authority over specific persons or entities
                • Territorial Jurisdiction: Authority within geographic boundaries

                Federal vs. State Jurisdiction:
                • Federal courts have limited jurisdiction defined by Constitution and statute
                • State courts have general jurisdiction over most legal matters
                • Some cases can be heard in either federal or state court

                Jurisdictional Requirements:
                • Must be established before a court can hear a case
                • Cannot be waived for subject matter jurisdiction
                • Personal jurisdiction can sometimes be waived

                Educational Note: Jurisdictional rules are complex and case-specific.
                """,
                key_concepts=["subject matter jurisdiction", "personal jurisdiction", "venue", "federal courts"],
                related_topics=["court system", "legal procedures", "constitutional law"],
                official_sources=["https://www.law.cornell.edu/wex/jurisdiction"],
                last_updated=datetime.now(),
                educational_objectives=["Understand different types of jurisdiction", "Learn federal vs state authority"],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="glossary_003",
                title="Due Process",
                content_type=ContentType.LEGAL_GLOSSARY,
                subject_area=SubjectArea.GENERAL,
                education_level=EducationLevel.INTERMEDIATE,
                summary="Constitutional requirement for fair legal procedures",
                detailed_content="""
                Due process is a constitutional principle requiring that legal proceedings be fair and that
                individuals receive adequate notice and opportunity to be heard before government action affects their rights.

                Procedural Due Process:
                • Right to adequate notice of charges or proceedings
                • Right to a fair hearing before an impartial tribunal
                • Right to present evidence and cross-examine witnesses
                • Right to legal representation in criminal cases

                Substantive Due Process:
                • Protection against arbitrary government action
                • Right to fundamental freedoms (speech, religion, etc.)
                • Protection of property rights
                • Right to privacy in certain matters

                Applications:
                • Criminal prosecutions
                • Civil commitment proceedings
                • Administrative hearings
                • School disciplinary actions

                Educational Note: Due process requirements vary based on the type of proceeding and rights at stake.
                """,
                key_concepts=["procedural due process", "substantive due process", "fair hearing", "constitutional rights"],
                related_topics=["constitutional law", "criminal procedure", "administrative law"],
                official_sources=["https://www.law.cornell.edu/wex/due_process"],
                last_updated=datetime.now(),
                educational_objectives=["Understand due process concepts", "Learn procedural vs substantive rights"],
                disclaimers=self.disclaimers
            )
        ]

        for content in glossary_terms:
            self.content_database[content.content_id] = content

    def _load_document_types(self):
        """Load document type educational content"""
        document_content = [
            EducationalContent(
                content_id="doc_types_001",
                title="Legal Motions",
                content_type=ContentType.DOCUMENT_TYPES,
                subject_area=SubjectArea.CIVIL_PROCEDURE,
                education_level=EducationLevel.BASIC,
                summary="Educational overview of legal motions and their purposes",
                detailed_content="""
                A motion is a formal request asking a court to issue a specific ruling or order. Motions are
                fundamental tools in litigation for addressing procedural and substantive issues.

                Common Types of Motions:
                • Motion to Dismiss: Requests court to dismiss case for legal reasons
                • Motion for Summary Judgment: Argues no material facts are in dispute
                • Motion to Compel: Requests court to order compliance with discovery
                • Motion in Limine: Seeks advance ruling on evidence admissibility
                • Motion for Continuance: Requests postponement of proceedings

                Motion Components:
                • Caption identifying the court and parties
                • Statement of the relief requested
                • Legal and factual basis for the request
                • Supporting evidence or affidavits
                • Proposed order for the court's signature

                Procedure:
                • Must be filed with the court
                • Opposing party typically has right to respond
                • Court may hold hearing before ruling
                • Court issues written order granting or denying motion

                Educational Note: Motion practice varies significantly between courts and jurisdictions.
                """,
                key_concepts=["motion practice", "relief requested", "legal basis", "supporting evidence"],
                related_topics=["court procedures", "litigation strategy", "legal writing"],
                official_sources=["https://www.law.cornell.edu/rules/frcp/rule_7"],
                last_updated=datetime.now(),
                educational_objectives=["Learn about different motion types", "Understand motion procedures"],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="doc_types_002",
                title="Complaints and Petitions",
                content_type=ContentType.DOCUMENT_TYPES,
                subject_area=SubjectArea.CIVIL_PROCEDURE,
                education_level=EducationLevel.BASIC,
                summary="Educational overview of complaints and petitions",
                detailed_content="""
                Complaints and petitions are initial pleadings that start legal proceedings. While similar in
                function, they are used in different types of cases.

                Complaints (Civil Cases):
                • Initiates lawsuit in civil court
                • States factual allegations against defendant
                • Specifies legal claims and theories
                • Requests specific relief (damages, injunctions, etc.)

                Petitions (Various Proceedings):
                • Used in family law (divorce, custody)
                • Bankruptcy proceedings
                • Administrative matters
                • Appeals to higher courts

                Required Elements:
                • Identification of parties
                • Statement of jurisdiction
                • Factual allegations
                • Legal claims or grounds
                • Prayer for relief

                Service Requirements:
                • Must be properly served on opposing parties
                • Service methods specified by court rules
                • Proof of service must be filed with court

                Educational Note: Specific requirements vary by court and case type.
                """,
                key_concepts=["pleadings", "factual allegations", "legal claims", "service of process"],
                related_topics=["civil procedure", "court rules", "legal writing"],
                official_sources=["https://www.law.cornell.edu/rules/frcp/rule_8"],
                last_updated=datetime.now(),
                educational_objectives=["Understand complaint vs petition", "Learn pleading requirements"],
                disclaimers=self.disclaimers
            )
        ]

        for content in document_content:
            self.content_database[content.content_id] = content

    def _load_timeline_information(self):
        """Load timeline educational content"""
        timeline_content = [
            EducationalContent(
                content_id="timeline_001",
                title="Bankruptcy Case Timeline",
                content_type=ContentType.TIMELINES,
                subject_area=SubjectArea.BANKRUPTCY,
                education_level=EducationLevel.BASIC,
                summary="Educational overview of typical bankruptcy case timelines",
                detailed_content="""
                Bankruptcy cases follow specific timelines that vary by chapter and case complexity.
                This educational overview covers typical timeframes:

                Chapter 7 Bankruptcy Timeline (Educational Overview):
                • Day 0: Petition filed, automatic stay takes effect
                • Day 1-30: Trustee appointed, creditors receive notice
                • Day 20-40: Meeting of creditors scheduled
                • Day 30-60: Claims filing deadline set (if needed)
                • Day 60-90: Deadlines for objecting to discharge
                • Day 90-120: Discharge typically granted

                Chapter 13 Bankruptcy Timeline:
                • Day 0: Petition filed, automatic stay takes effect
                • Day 14: Payment plan payments must begin
                • Day 20-50: Meeting of creditors held
                • Day 45: Confirmation hearing for payment plan
                • 3-5 years: Plan completion and discharge

                Key Factors Affecting Timeline:
                • Case complexity and disputes
                • Creditor objections
                • Asset administration requirements
                • Court scheduling and local rules

                Educational Note: These are general timeframes. Actual cases may vary significantly.
                """,
                key_concepts=["filing date", "meeting of creditors", "discharge", "confirmation", "automatic stay"],
                related_topics=["bankruptcy procedures", "court deadlines", "trustee duties"],
                official_sources=["https://www.uscourts.gov/services-forms/bankruptcy"],
                last_updated=datetime.now(),
                educational_objectives=["Learn typical bankruptcy timelines", "Understand key deadline concepts"],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="timeline_002",
                title="Civil Litigation Timeline",
                content_type=ContentType.TIMELINES,
                subject_area=SubjectArea.CIVIL_PROCEDURE,
                education_level=EducationLevel.INTERMEDIATE,
                summary="Educational overview of civil litigation timelines",
                detailed_content="""
                Civil litigation timelines vary greatly depending on case complexity, court schedules, and
                discovery needs. This educational overview covers typical phases:

                Pre-Filing (Variable):
                • Investigation and fact-gathering
                • Attempt at settlement negotiations
                • Statute of limitations considerations

                Initial Pleadings (0-6 months):
                • Complaint filed and served
                • Defendant's answer or motion to dismiss
                • Reply if necessary
                • Initial case management conference

                Discovery Phase (6-24 months):
                • Discovery plan development
                • Interrogatories and document requests
                • Depositions of parties and witnesses
                • Expert witness disclosure and deposition

                Pre-Trial (2-4 months before trial):
                • Summary judgment motions
                • Pretrial conferences
                • Settlement discussions
                • Trial preparation

                Trial and Post-Trial (Variable):
                • Trial proceedings (days to weeks)
                • Post-trial motions
                • Appeals (if any)

                Educational Note: Federal courts often move faster than state courts, but timing varies widely.
                """,
                key_concepts=["statute of limitations", "discovery deadlines", "pretrial conference", "trial schedule"],
                related_topics=["civil procedure", "court management", "litigation strategy"],
                official_sources=["https://www.law.cornell.edu/rules/frcp"],
                last_updated=datetime.now(),
                educational_objectives=["Learn litigation phases", "Understand typical timeframes"],
                disclaimers=self.disclaimers
            )
        ]

        for content in timeline_content:
            self.content_database[content.content_id] = content

    def _load_faq_content(self):
        """Load frequently asked questions"""
        faq_content = [
            EducationalContent(
                content_id="faq_001",
                title="What is the difference between Chapter 7 and Chapter 13 bankruptcy?",
                content_type=ContentType.FAQ,
                subject_area=SubjectArea.BANKRUPTCY,
                education_level=EducationLevel.BASIC,
                summary="Educational comparison of Chapter 7 and Chapter 13 bankruptcy",
                detailed_content="""
                Chapter 7 and Chapter 13 are the most common types of consumer bankruptcy, each serving
                different purposes and having different requirements.

                Chapter 7 (Liquidation):
                • Designed for debtors with limited income
                • Assets may be sold to pay creditors
                • Most debts are discharged quickly (3-4 months)
                • Income limits apply (means test)
                • Cannot file again for 8 years

                Chapter 13 (Reorganization):
                • For debtors with regular income
                • Keep assets while paying creditors over time
                • 3-5 year payment plan required
                • Can catch up on mortgage or car payments
                • Cannot file again for 6 years (from Chapter 13)

                Key Educational Differences:
                • Asset retention: Chapter 13 allows keeping more assets
                • Payment requirements: Chapter 13 requires ongoing payments
                • Time to discharge: Chapter 7 is much faster
                • Income requirements: Chapter 13 requires steady income
                • Debt limits: Chapter 13 has debt ceiling limits

                Educational Note: Eligibility and procedures vary by jurisdiction and individual circumstances.
                """,
                key_concepts=["liquidation", "reorganization", "means test", "payment plan", "discharge"],
                related_topics=["bankruptcy options", "debt relief", "financial planning"],
                official_sources=["https://www.uscourts.gov/services-forms/bankruptcy/bankruptcy-basics"],
                last_updated=datetime.now(),
                educational_objectives=["Compare bankruptcy chapters", "Understand key differences"],
                disclaimers=self.disclaimers
            ),

            EducationalContent(
                content_id="faq_002",
                title="What happens at a meeting of creditors?",
                content_type=ContentType.FAQ,
                subject_area=SubjectArea.BANKRUPTCY,
                education_level=EducationLevel.BASIC,
                summary="Educational explanation of creditors' meetings in bankruptcy",
                detailed_content="""
                The meeting of creditors (also called a "341 meeting") is a required proceeding in all
                bankruptcy cases where the debtor answers questions under oath.

                Educational Overview of the Process:
                • Conducted by the bankruptcy trustee, not a judge
                • Held in a meeting room, not a courtroom
                • Debtor must attend and bring required documents
                • Questions focus on financial affairs and bankruptcy schedules

                Typical Questions Asked:
                • Have you read your bankruptcy petition?
                • Are all assets and debts listed accurately?
                • Have you made any large payments to creditors recently?
                • Do you have any pending lawsuits?
                • Have you transferred any property recently?

                Who May Attend:
                • The debtor (required)
                • Debtor's attorney (recommended)
                • Bankruptcy trustee (required)
                • Creditors (optional, rarely attend)

                What to Expect:
                • Meeting typically lasts 5-15 minutes
                • Questions are usually routine
                • Documents may be requested
                • Additional meetings may be scheduled if needed

                Educational Note: Preparation and documentation requirements vary by case and trustee.
                """,
                key_concepts=["341 meeting", "trustee examination", "under oath", "creditor attendance"],
                related_topics=["bankruptcy procedures", "trustee duties", "debtor obligations"],
                official_sources=["https://www.law.cornell.edu/uscode/text/11/341"],
                last_updated=datetime.now(),
                educational_objectives=["Understand meeting purpose", "Learn what to expect"],
                disclaimers=self.disclaimers
            )
        ]

        for content in faq_content:
            self.content_database[content.content_id] = content

    def search_content(self, query=None, subject_area=None, education_level="beginner", **kwargs) -> ContentResponse:
        """Search educational content based on query parameters"""
        try:
            search_id = f"search_{uuid.uuid4().hex[:8]}"
            self.logger.info(f"Searching educational content: {search_id}")

            # Convert parameters to standardized format
            search_query = str(query) if query else ""
            target_subject = SubjectArea(subject_area) if subject_area else SubjectArea.GENERAL
            target_level = EducationLevel(education_level) if isinstance(education_level, str) else education_level

            # Find matching content
            matched_content = []
            related_content = []

            for content_id, content in self.content_database.items():
                score = self._calculate_relevance_score_simple(content, search_query, target_subject, target_level)

                if score >= 0.7:  # High relevance threshold
                    matched_content.append(content)
                elif score >= 0.4:  # Related content threshold
                    related_content.append(content)

            # Sort by relevance
            matched_content.sort(key=lambda c: self._calculate_relevance_score_simple(c, search_query, target_subject, target_level), reverse=True)
            related_content.sort(key=lambda c: self._calculate_relevance_score_simple(c, search_query, target_subject, target_level), reverse=True)

            # Limit results
            matched_content = matched_content[:5]
            related_content = related_content[:3]

            # Generate official resources
            official_resources = self._get_official_resources([target_subject])

            # Calculate overall relevance score
            avg_relevance = 0.0
            if matched_content:
                total_score = sum(self._calculate_relevance_score_simple(c, search_query, target_subject, target_level)
                                for c in matched_content)
                avg_relevance = total_score / len(matched_content)
            elif related_content:
                total_score = sum(self._calculate_relevance_score_simple(c, search_query, target_subject, target_level)
                                for c in related_content)
                avg_relevance = total_score / len(related_content)
            else:
                avg_relevance = 0.5  # Default relevance for educational content

            # Create response
            response = ContentResponse(
                response_id=f"resp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
                matched_content=matched_content,
                related_content=related_content,
                official_resources=official_resources,
                disclaimers=self.disclaimers,
                attorney_consultation_notice=self._get_attorney_consultation_notice(),
                educational_warnings=self._get_educational_warnings(search_query),
                relevance_score=avg_relevance
            )

            # Log content access for audit
            self._log_content_access(search_query, response)

            return response

        except Exception as e:
            self.logger.error(f"Content search failed: {e}")
            return self._create_error_response(search_id, str(e))

    def _calculate_relevance_score_simple(self, content: EducationalContent,
                                        search_query: str, target_subject: SubjectArea,
                                        target_level: EducationLevel) -> float:
        """Calculate relevance score for content matching with simple parameters"""
        score = 0.0

        # Subject area matching
        if content.subject_area == target_subject:
            score += 0.4
        elif target_subject == SubjectArea.GENERAL:
            score += 0.2

        # Education level matching
        if content.education_level == target_level:
            score += 0.3
        elif abs(list(EducationLevel).index(content.education_level) -
                list(EducationLevel).index(target_level)) == 1:
            score += 0.1

        # Text matching
        if search_query:
            content_text = (content.title + " " + content.detailed_content).lower()
            search_terms = search_query.lower().split()

            matching_terms = 0
            for term in search_terms:
                if term in content_text:
                    matching_terms += 1

            if search_terms:
                score += 0.3 * (matching_terms / len(search_terms))

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_relevance_score(self, content: EducationalContent, query: ContentQuery) -> float:
        """Calculate relevance score for content matching"""
        score = 0.0

        # Subject area matching
        if content.subject_area in query.subject_areas:
            score += 0.4

        # Content type matching
        if content.content_type in query.content_types:
            score += 0.3

        # Education level matching
        if content.education_level == query.education_level:
            score += 0.2
        elif abs(list(EducationLevel).index(content.education_level) -
                list(EducationLevel).index(query.education_level)) == 1:
            score += 0.1

        # Keyword matching
        if query.keywords:
            keyword_score = 0
            content_text = (content.title + " " + content.summary + " " +
                          " ".join(content.key_concepts)).lower()

            for keyword in query.keywords:
                if keyword.lower() in content_text:
                    keyword_score += 1

            score += min(0.3, keyword_score / len(query.keywords) * 0.3)

        return min(1.0, score)

    def _get_official_resources(self, subject_areas: List[SubjectArea]) -> List[Dict[str, str]]:
        """Get official government and educational resources"""
        resources = []

        base_resources = [
            {
                "title": "U.S. Courts - Official Site",
                "url": "https://www.uscourts.gov",
                "description": "Official information about federal courts and procedures"
            },
            {
                "title": "Legal Information Institute - Cornell Law",
                "url": "https://www.law.cornell.edu",
                "description": "Free legal information and educational resources"
            }
        ]

        subject_specific = {
            SubjectArea.BANKRUPTCY: [
                {
                    "title": "U.S. Trustee Program",
                    "url": "https://www.justice.gov/ust",
                    "description": "Official bankruptcy administration information"
                },
                {
                    "title": "Bankruptcy Basics - U.S. Courts",
                    "url": "https://www.uscourts.gov/services-forms/bankruptcy/bankruptcy-basics",
                    "description": "Educational materials about bankruptcy procedures"
                }
            ],
            SubjectArea.CIVIL_PROCEDURE: [
                {
                    "title": "Federal Rules of Civil Procedure",
                    "url": "https://www.law.cornell.edu/rules/frcp",
                    "description": "Official rules governing federal civil cases"
                }
            ]
        }

        resources.extend(base_resources)
        for subject in subject_areas:
            resources.extend(subject_specific.get(subject, []))

        return resources

    def _get_attorney_consultation_notice(self) -> str:
        """Get attorney consultation notice"""
        return """
        IMPORTANT: ATTORNEY CONSULTATION REQUIRED

        This educational information cannot replace professional legal advice.
        For any legal matter affecting your rights or obligations, you must
        consult with a qualified attorney licensed in your jurisdiction.

        Legal requirements, procedures, and deadlines vary significantly by
        location and individual circumstances. Only a qualified attorney can
        provide advice specific to your situation.
        """

    def _get_educational_warnings(self, query: ContentQuery) -> List[str]:
        """Generate educational warnings based on query"""
        warnings = []

        if SubjectArea.BANKRUPTCY in query.subject_areas:
            warnings.append("Bankruptcy has serious long-term consequences - professional guidance essential")

        if query.document_context:
            warnings.append("Document-specific analysis requires attorney review for practical application")

        warnings.append("Laws and procedures change frequently - verify current requirements")
        warnings.append("Educational content may not reflect your specific jurisdiction's requirements")

        return warnings

    def _log_content_access(self, query: ContentQuery, response: ContentResponse):
        """Log content access for audit purposes"""
        self.audit_logger.log_document_event(
            event_type="educational_content_accessed",
            document_id=query.query_id,
            user_id=query.user_id or "anonymous",
            details={
                "response_id": response.response_id,
                "subject_areas": [area.value for area in query.subject_areas],
                "content_types": [ct.value for ct in query.content_types],
                "matched_content_count": len(response.matched_content),
                "related_content_count": len(response.related_content)
            }
        )

    def _create_error_response(self, query_id: str, error_message: str) -> ContentResponse:
        """Create error response"""
        return ContentResponse(
            response_id=f"error_{query_id}",
            matched_content=[],
            related_content=[],
            official_resources=self._get_official_resources([SubjectArea.GENERAL]),
            disclaimers=self.disclaimers,
            attorney_consultation_notice=self._get_attorney_consultation_notice(),
            educational_warnings=[f"Content search error: {error_message}",
                                "Please consult official resources or qualified attorney"]
        )

    def get_content_statistics(self) -> Dict[str, Any]:
        """Get educational content library statistics"""
        try:
            stats = {
                "total_content_items": len(self.content_database),
                "content_by_type": {},
                "content_by_subject": {},
                "content_by_level": {},
                "last_updated": max([content.last_updated for content in self.content_database.values()]).isoformat() if self.content_database else None
            }

            for content in self.content_database.values():
                # Count by type
                content_type = content.content_type.value
                stats["content_by_type"][content_type] = stats["content_by_type"].get(content_type, 0) + 1

                # Count by subject
                subject = content.subject_area.value
                stats["content_by_subject"][subject] = stats["content_by_subject"].get(subject, 0) + 1

                # Count by level
                level = content.education_level.value
                stats["content_by_level"][level] = stats["content_by_level"].get(level, 0) + 1

            return stats

        except Exception as e:
            self.logger.error(f"Failed to generate content statistics: {e}")
            return {"error": str(e)}

# Global content library instance
educational_content_library = EducationalContentLibrary()

def validate_content_library():
    """Validate educational content library"""
    try:
        print("Testing Educational Content Library...")

        # Test content search
        test_query = ContentQuery(
            query_id="test_001",
            subject_areas=[SubjectArea.BANKRUPTCY],
            content_types=[ContentType.BANKRUPTCY_INFO, ContentType.FAQ],
            education_level=EducationLevel.BASIC,
            keywords=["chapter 7", "discharge"],
            user_id="test_user"
        )

        response = content_library.search_content(test_query)

        print(f"[PASS] Content search completed: {response.response_id}")
        print(f"   Matched content: {len(response.matched_content)} items")
        print(f"   Related content: {len(response.related_content)} items")
        print(f"   Official resources: {len(response.official_resources)} links")

        if response.matched_content:
            first_content = response.matched_content[0]
            print(f"   First match: {first_content.title}")
            print(f"   Subject: {first_content.subject_area.value}")

        # Test statistics
        stats = content_library.get_content_statistics()
        print(f"[PASS] Content statistics generated")
        print(f"   Total items: {stats['total_content_items']}")

        print("\n[INFO] EDUCATIONAL DISCLAIMER:")
        print(response.disclaimers[0])

        print("\n[INFO] ATTORNEY CONSULTATION NOTICE:")
        print(response.attorney_consultation_notice)

        return True

    except Exception as e:
        print(f"[FAIL] Content library validation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Educational Content Library...")
    print("=" * 50)

    if validate_content_library():
        print("\nEducational Content Library is operational")

        # Display content statistics
        stats = content_library.get_content_statistics()
        print(f"\nContent Library Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("Content library validation failed")