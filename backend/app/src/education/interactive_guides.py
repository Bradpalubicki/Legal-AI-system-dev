from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class GuideCategory(str, Enum):
    COURT_PROCEDURES = "court_procedures"
    DOCUMENT_PREPARATION = "document_preparation" 
    DEADLINE_MANAGEMENT = "deadline_management"
    COURT_ETIQUETTE = "court_etiquette"
    LEGAL_TERMINOLOGY = "legal_terminology"


class StepType(str, Enum):
    ACTION = "action"
    DECISION = "decision"
    INFORMATION = "information"
    WARNING = "warning"
    DEADLINE = "deadline"


@dataclass
class GuideStep:
    id: str
    title: str
    description: str
    step_type: StepType
    estimated_time: Optional[int] = None  # minutes
    required_documents: List[str] = None
    tips: List[str] = None
    warnings: List[str] = None
    next_steps: List[str] = None  # IDs of possible next steps
    deadline_info: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.required_documents is None:
            self.required_documents = []
        if self.tips is None:
            self.tips = []
        if self.warnings is None:
            self.warnings = []
        if self.next_steps is None:
            self.next_steps = []


@dataclass
class InteractiveGuide:
    id: str
    title: str
    category: GuideCategory
    description: str
    difficulty_level: int  # 1-3
    estimated_completion_time: int  # minutes
    prerequisites: List[str]
    steps: List[GuideStep]
    resources: List[Dict[str, str]]  # {"title": "", "url": "", "type": "form|statute|case"}
    last_updated: datetime
    tags: List[str]


@dataclass
class ChecklistItem:
    id: str
    task: str
    description: str
    required: bool
    deadline_days: Optional[int] = None  # days from trigger event
    dependencies: List[str] = None  # IDs of other checklist items
    documents_needed: List[str] = None
    completed: bool = False

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.documents_needed is None:
            self.documents_needed = []


@dataclass
class DocumentChecklist:
    id: str
    title: str
    description: str
    category: str
    items: List[ChecklistItem]
    applicable_jurisdictions: List[str]
    last_updated: datetime


@dataclass
class DeadlineRule:
    id: str
    name: str
    description: str
    jurisdiction: str
    rule_reference: str  # e.g., "FRCP 12(a)(1)(A)"
    base_period: int  # days
    calculation_method: str  # "calendar_days" or "business_days"
    extensions_available: bool
    extension_period: Optional[int] = None
    exclusions: List[str] = None  # holidays, weekends, etc.
    examples: List[str] = None

    def __post_init__(self):
        if self.exclusions is None:
            self.exclusions = []
        if self.examples is None:
            self.examples = []


@dataclass
class CourtEtiquetteRule:
    id: str
    title: str
    description: str
    court_type: str  # "trial", "appellate", "administrative"
    importance_level: int  # 1-3
    examples: List[str]
    violations_consequences: List[str]


@dataclass
class LegalTerm:
    id: str
    term: str
    definition: str
    pronunciation: Optional[str] = None
    etymology: Optional[str] = None
    related_terms: List[str] = None
    examples: List[str] = None
    categories: List[str] = None

    def __post_init__(self):
        if self.related_terms is None:
            self.related_terms = []
        if self.examples is None:
            self.examples = []
        if self.categories is None:
            self.categories = []


class InteractiveGuides:
    def __init__(self):
        self._guides = self._initialize_guides()
        self._checklists = self._initialize_checklists()
        self._deadline_rules = self._initialize_deadline_rules()
        self._etiquette_rules = self._initialize_etiquette_rules()
        self._glossary = self._initialize_glossary()
    
    def _initialize_guides(self) -> Dict[str, InteractiveGuide]:
        guides = {}
        
        # Filing a Civil Lawsuit Guide
        civil_lawsuit_steps = [
            GuideStep(
                id="pre_suit_investigation",
                title="Pre-Suit Investigation",
                description="Thoroughly investigate your case before filing to ensure you have a viable claim.",
                step_type=StepType.ACTION,
                estimated_time=60,
                tips=[
                    "Document everything - keep detailed records of all communications and events",
                    "Gather all relevant documents, photos, and physical evidence",
                    "Identify and interview potential witnesses"
                ],
                warnings=[
                    "Statute of limitations may bar your claim if you wait too long",
                    "Insufficient evidence can lead to case dismissal"
                ],
                next_steps=["determine_jurisdiction"]
            ),
            GuideStep(
                id="determine_jurisdiction",
                title="Determine Proper Jurisdiction and Venue",
                description="Identify the correct court system and location for filing your lawsuit.",
                step_type=StepType.DECISION,
                estimated_time=30,
                tips=[
                    "Federal court: federal question or diversity jurisdiction required",
                    "State court: most common for state law claims",
                    "Venue: where defendant resides or where events occurred"
                ],
                required_documents=["complaint draft", "jurisdictional analysis"],
                next_steps=["draft_complaint"]
            ),
            GuideStep(
                id="draft_complaint",
                title="Draft the Complaint",
                description="Prepare the formal document that initiates the lawsuit.",
                step_type=StepType.ACTION,
                estimated_time=120,
                required_documents=["fact summary", "legal research", "damages calculation"],
                tips=[
                    "Use plain English and be specific about facts",
                    "Include all necessary elements for each cause of action",
                    "Clearly state the relief sought"
                ],
                warnings=[
                    "Insufficient pleading may result in motion to dismiss",
                    "Must include all claims or risk waiving them"
                ],
                next_steps=["file_complaint"]
            ),
            GuideStep(
                id="file_complaint",
                title="File Complaint with Court",
                description="Submit the complaint and pay required filing fees.",
                step_type=StepType.ACTION,
                estimated_time=30,
                required_documents=["signed complaint", "filing fee", "civil cover sheet"],
                deadline_info={
                    "type": "statute_of_limitations",
                    "description": "Must file before statute of limitations expires"
                },
                next_steps=["serve_defendant"]
            ),
            GuideStep(
                id="serve_defendant",
                title="Serve Defendant with Process",
                description="Deliver copies of the complaint and summons to all defendants.",
                step_type=StepType.ACTION,
                estimated_time=15,
                deadline_info={
                    "type": "service_deadline",
                    "description": "Generally must serve within 90-120 days of filing",
                    "rule": "FRCP 4(c)(1)"
                },
                warnings=[
                    "Improper service can void the entire case",
                    "Different rules apply for serving corporations, government entities"
                ],
                next_steps=["await_response"]
            ),
            GuideStep(
                id="await_response",
                title="Wait for Defendant's Response",
                description="Monitor for defendant's answer or motion to dismiss.",
                step_type=StepType.INFORMATION,
                estimated_time=0,
                deadline_info={
                    "type": "response_deadline",
                    "description": "Defendant typically has 21 days to respond",
                    "rule": "FRCP 12(a)(1)(A)"
                },
                tips=[
                    "If no response, consider motion for default judgment",
                    "Prepare for potential motion to dismiss"
                ],
                next_steps=["discovery_phase", "motion_practice"]
            )
        ]
        
        guides["filing_civil_lawsuit"] = InteractiveGuide(
            id="filing_civil_lawsuit",
            title="How to File a Civil Lawsuit",
            category=GuideCategory.COURT_PROCEDURES,
            description="Step-by-step guide to initiating civil litigation",
            difficulty_level=2,
            estimated_completion_time=240,
            prerequisites=["understanding_civil_litigation"],
            steps=civil_lawsuit_steps,
            resources=[
                {"title": "Federal Rules of Civil Procedure", "url": "/resources/frcp", "type": "rules"},
                {"title": "Civil Cover Sheet", "url": "/forms/civil-cover-sheet", "type": "form"},
                {"title": "Sample Complaint", "url": "/templates/complaint", "type": "template"}
            ],
            last_updated=datetime.now(),
            tags=["civil litigation", "complaint", "filing", "procedure"]
        )
        
        # Responding to a Lawsuit Guide
        response_steps = [
            GuideStep(
                id="review_complaint",
                title="Carefully Review the Complaint",
                description="Thoroughly read and analyze the claims against you.",
                step_type=StepType.ACTION,
                estimated_time=60,
                tips=[
                    "Note each specific allegation and claim",
                    "Identify factual and legal issues",
                    "Check for any obvious defects in the complaint"
                ],
                next_steps=["calculate_response_deadline"]
            ),
            GuideStep(
                id="calculate_response_deadline",
                title="Calculate Response Deadline",
                description="Determine when your response is due to avoid default.",
                step_type=StepType.DEADLINE,
                estimated_time=15,
                deadline_info={
                    "type": "response_required",
                    "description": "Usually 21 days from service (30 days if waived service)",
                    "rule": "FRCP 12(a)"
                },
                warnings=[
                    "Missing deadline can result in default judgment",
                    "Different deadlines may apply for government defendants"
                ],
                next_steps=["choose_response_strategy"]
            ),
            GuideStep(
                id="choose_response_strategy",
                title="Choose Response Strategy",
                description="Decide whether to file a motion to dismiss or answer directly.",
                step_type=StepType.DECISION,
                estimated_time=30,
                tips=[
                    "Motion to dismiss: Challenge legal sufficiency of complaint",
                    "Answer: Respond to each allegation and assert defenses",
                    "Consider time implications of each choice"
                ],
                next_steps=["file_motion_dismiss", "draft_answer"]
            )
        ]
        
        guides["responding_to_lawsuit"] = InteractiveGuide(
            id="responding_to_lawsuit",
            title="How to Respond to a Lawsuit",
            category=GuideCategory.COURT_PROCEDURES,
            description="Guide for defendants on responding to civil complaints",
            difficulty_level=2,
            estimated_completion_time=180,
            prerequisites=["understanding_civil_litigation"],
            steps=response_steps,
            resources=[
                {"title": "Answer Template", "url": "/templates/answer", "type": "template"},
                {"title": "Motion to Dismiss Guide", "url": "/guides/motion-to-dismiss", "type": "guide"}
            ],
            last_updated=datetime.now(),
            tags=["civil litigation", "answer", "motion to dismiss", "defense"]
        )
        
        return guides
    
    def _initialize_checklists(self) -> Dict[str, DocumentChecklist]:
        checklists = {}
        
        # Divorce Filing Checklist
        divorce_items = [
            ChecklistItem(
                id="financial_documents",
                task="Gather Financial Documents",
                description="Collect all financial records for asset and debt disclosure",
                required=True,
                documents_needed=[
                    "Tax returns (3 years)",
                    "Bank statements (6 months)",
                    "Investment account statements",
                    "Property deeds",
                    "Credit card statements",
                    "Loan documents",
                    "Employment records/pay stubs"
                ]
            ),
            ChecklistItem(
                id="residence_establishment",
                task="Establish Residency Requirements",
                description="Ensure you meet state residency requirements for filing",
                required=True,
                deadline_days=0,
                documents_needed=["Proof of residency", "Utility bills", "Lease agreement"]
            ),
            ChecklistItem(
                id="grounds_determination",
                task="Determine Grounds for Divorce",
                description="Identify whether filing no-fault or fault-based divorce",
                required=True,
                dependencies=["residence_establishment"]
            ),
            ChecklistItem(
                id="child_custody_plan",
                task="Develop Child Custody Proposal",
                description="Create parenting plan if children are involved",
                required=False,
                documents_needed=[
                    "Children's school records",
                    "Medical records",
                    "Activity schedules"
                ]
            ),
            ChecklistItem(
                id="temporary_orders",
                task="Consider Temporary Orders",
                description="Determine if temporary support or custody orders are needed",
                required=False,
                deadline_days=30,
                dependencies=["grounds_determination"]
            )
        ]
        
        checklists["divorce_filing"] = DocumentChecklist(
            id="divorce_filing",
            title="Divorce Filing Checklist",
            description="Complete checklist for preparing to file for divorce",
            category="family_law",
            items=divorce_items,
            applicable_jurisdictions=["all_states"],
            last_updated=datetime.now()
        )
        
        return checklists
    
    def _initialize_deadline_rules(self) -> Dict[str, DeadlineRule]:
        rules = {}
        
        rules["answer_deadline"] = DeadlineRule(
            id="answer_deadline",
            name="Answer to Complaint Deadline",
            description="Deadline for defendant to file answer or responsive motion",
            jurisdiction="federal",
            rule_reference="FRCP 12(a)(1)(A)",
            base_period=21,
            calculation_method="calendar_days",
            extensions_available=True,
            extension_period=30,
            exclusions=["day_of_service"],
            examples=[
                "Served on Monday, answer due 3 weeks from Tuesday",
                "If served by waiver, 60 days from when request was sent"
            ]
        )
        
        rules["discovery_deadline"] = DeadlineRule(
            id="discovery_deadline",
            name="Discovery Cutoff",
            description="Deadline to complete all discovery activities",
            jurisdiction="federal",
            rule_reference="FRCP 16(b)(3)(A)",
            base_period=30,
            calculation_method="calendar_days",
            extensions_available=True,
            examples=[
                "Typically set 30 days before trial",
                "May be extended by court order or stipulation"
            ]
        )
        
        return rules
    
    def _initialize_etiquette_rules(self) -> Dict[str, CourtEtiquetteRule]:
        rules = {}
        
        rules["courtroom_attire"] = CourtEtiquetteRule(
            id="courtroom_attire",
            title="Proper Courtroom Attire",
            description="Dress professionally and conservatively for all court appearances",
            court_type="trial",
            importance_level=2,
            examples=[
                "Business suit or professional dress",
                "Conservative colors (navy, gray, black)",
                "Minimal jewelry and makeup",
                "Closed-toe shoes"
            ],
            violations_consequences=[
                "Judge may refuse to hear your case",
                "Negative impression on jury",
                "Contempt of court (extreme cases)"
            ]
        )
        
        rules["addressing_court"] = CourtEtiquetteRule(
            id="addressing_court",
            title="How to Address the Court",
            description="Proper forms of address when speaking to judges",
            court_type="trial",
            importance_level=3,
            examples=[
                "'Your Honor' - most common and always appropriate",
                "'Judge [Last Name]' - acceptable alternative",
                "Stand when addressing the court unless told otherwise",
                "Wait for permission before speaking"
            ],
            violations_consequences=[
                "Interruption by judge",
                "Contempt of court citation",
                "Loss of credibility"
            ]
        )
        
        return rules
    
    def _initialize_glossary(self) -> Dict[str, LegalTerm]:
        terms = {}
        
        terms["plaintiff"] = LegalTerm(
            id="plaintiff",
            term="Plaintiff",
            definition="The party who brings a civil lawsuit against another party (the defendant)",
            pronunciation="PLAIN-tiff",
            etymology="From Old French 'plaintif' meaning 'lamenting'",
            related_terms=["defendant", "petitioner", "complainant"],
            examples=[
                "The plaintiff filed a lawsuit seeking damages for breach of contract",
                "In Smith v. Jones, Smith is the plaintiff"
            ],
            categories=["civil_litigation", "parties"]
        )
        
        terms["defendant"] = LegalTerm(
            id="defendant",
            term="Defendant",
            definition="The party against whom a civil lawsuit is brought or who is accused of a crime",
            pronunciation="dih-FEN-dant",
            related_terms=["plaintiff", "respondent"],
            examples=[
                "The defendant filed a motion to dismiss the complaint",
                "In criminal cases, the defendant has the right to remain silent"
            ],
            categories=["civil_litigation", "criminal_law", "parties"]
        )
        
        terms["jurisdiction"] = LegalTerm(
            id="jurisdiction",
            term="Jurisdiction",
            definition="The authority of a court to hear and decide a case",
            pronunciation="joor-is-DIK-shun",
            etymology="From Latin 'jurisdictio' meaning 'administration of the law'",
            related_terms=["venue", "subject_matter_jurisdiction", "personal_jurisdiction"],
            examples=[
                "Federal courts have jurisdiction over federal questions",
                "The court lacked jurisdiction to hear the case"
            ],
            categories=["court_system", "procedure"]
        )
        
        terms["venue"] = LegalTerm(
            id="venue",
            term="Venue",
            definition="The proper geographic location for a trial, usually where the events occurred or where the defendant resides",
            pronunciation="VEN-yoo",
            etymology="From Old French 'venue' meaning 'a coming'",
            related_terms=["jurisdiction", "forum", "change_of_venue"],
            examples=[
                "Venue was proper in the county where the accident occurred",
                "The defendant moved to change venue due to pretrial publicity"
            ],
            categories=["procedure", "geographic"]
        )
        
        terms["discovery"] = LegalTerm(
            id="discovery",
            term="Discovery",
            definition="The pre-trial process where parties exchange information and evidence relevant to the case",
            related_terms=["interrogatories", "depositions", "requests_for_production"],
            examples=[
                "During discovery, both sides exchanged documents",
                "The plaintiff's discovery requests were overly broad"
            ],
            categories=["civil_litigation", "procedure"]
        )
        
        return terms
    
    # Guide Methods
    def get_all_guides(self) -> List[InteractiveGuide]:
        return list(self._guides.values())
    
    def get_guide(self, guide_id: str) -> Optional[InteractiveGuide]:
        return self._guides.get(guide_id)
    
    def get_guides_by_category(self, category: GuideCategory) -> List[InteractiveGuide]:
        return [guide for guide in self._guides.values() if guide.category == category]
    
    def search_guides(self, query: str) -> List[InteractiveGuide]:
        query_lower = query.lower()
        matching_guides = []
        
        for guide in self._guides.values():
            if (query_lower in guide.title.lower() or 
                query_lower in guide.description.lower() or
                any(query_lower in tag.lower() for tag in guide.tags)):
                matching_guides.append(guide)
        
        return matching_guides
    
    # Checklist Methods
    def get_all_checklists(self) -> List[DocumentChecklist]:
        return list(self._checklists.values())
    
    def get_checklist(self, checklist_id: str) -> Optional[DocumentChecklist]:
        return self._checklists.get(checklist_id)
    
    def get_checklists_by_category(self, category: str) -> List[DocumentChecklist]:
        return [checklist for checklist in self._checklists.values() if checklist.category == category]
    
    # Deadline Calculation Methods
    def get_deadline_rule(self, rule_id: str) -> Optional[DeadlineRule]:
        return self._deadline_rules.get(rule_id)
    
    def calculate_deadline(self, rule_id: str, start_date: datetime) -> Optional[datetime]:
        rule = self.get_deadline_rule(rule_id)
        if not rule:
            return None
        
        if rule.calculation_method == "calendar_days":
            return start_date + timedelta(days=rule.base_period)
        elif rule.calculation_method == "business_days":
            # Simple business days calculation (Mon-Fri)
            days_added = 0
            current_date = start_date
            while days_added < rule.base_period:
                current_date += timedelta(days=1)
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    days_added += 1
            return current_date
        
        return None
    
    # Etiquette Methods
    def get_etiquette_rules(self, court_type: str = None) -> List[CourtEtiquetteRule]:
        rules = list(self._etiquette_rules.values())
        if court_type:
            rules = [rule for rule in rules if rule.court_type == court_type]
        return sorted(rules, key=lambda x: x.importance_level, reverse=True)
    
    # Glossary Methods
    def get_glossary_term(self, term_id: str) -> Optional[LegalTerm]:
        return self._glossary.get(term_id)
    
    def search_glossary(self, query: str) -> List[LegalTerm]:
        query_lower = query.lower()
        matching_terms = []
        
        for term in self._glossary.values():
            if (query_lower in term.term.lower() or 
                query_lower in term.definition.lower() or
                any(query_lower in category.lower() for category in term.categories)):
                matching_terms.append(term)
        
        return sorted(matching_terms, key=lambda x: x.term.lower())
    
    def get_related_terms(self, term_id: str) -> List[LegalTerm]:
        term = self.get_glossary_term(term_id)
        if not term:
            return []
        
        related = []
        for related_id in term.related_terms:
            related_term = self.get_glossary_term(related_id)
            if related_term:
                related.append(related_term)
        
        return related