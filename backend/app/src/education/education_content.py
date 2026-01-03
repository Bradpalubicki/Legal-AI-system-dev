from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class LegalTopicCategory(str, Enum):
    BANKRUPTCY = "bankruptcy"
    CIVIL_LITIGATION = "civil_litigation"
    CRIMINAL_PROCEDURE = "criminal_procedure"
    FAMILY_LAW = "family_law"
    REAL_ESTATE = "real_estate"
    BUSINESS_FORMATION = "business_formation"


@dataclass
class ContentSection:
    title: str
    content: str
    level: int  # 1=beginner, 2=intermediate, 3=advanced
    estimated_read_time: int  # minutes
    prerequisites: List[str] = None
    related_topics: List[str] = None

    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.related_topics is None:
            self.related_topics = []


@dataclass
class LegalTopic:
    id: str
    title: str
    category: LegalTopicCategory
    description: str
    sections: List[ContentSection]
    keywords: List[str]
    last_updated: datetime
    difficulty_level: int  # 1-3


class EducationContent:
    def __init__(self):
        self._topics = self._initialize_content()
    
    def _initialize_content(self) -> Dict[str, LegalTopic]:
        topics = {}
        
        # Bankruptcy Law Content
        bankruptcy_sections = [
            ContentSection(
                title="Introduction to Bankruptcy",
                content="""
                Bankruptcy is a legal process that provides relief to individuals and businesses 
                unable to pay their debts. The U.S. Bankruptcy Code is found in Title 11 of the 
                United States Code and provides several different types of bankruptcy proceedings.
                
                Key Principles:
                • Automatic Stay: Immediately stops most collection actions
                • Discharge: Elimination of personal liability for certain debts
                • Fresh Start: Opportunity to rebuild financial life
                • Creditor Protection: Fair distribution of available assets
                """,
                level=1,
                estimated_read_time=5,
                related_topics=["debt_relief", "creditor_rights"]
            ),
            ContentSection(
                title="Chapter 7 Bankruptcy - Liquidation",
                content="""
                Chapter 7 bankruptcy, often called "liquidation bankruptcy," involves the sale 
                of a debtor's non-exempt assets to pay creditors.
                
                Eligibility Requirements:
                • Means Test: Income must be below state median or pass means test
                • Credit counseling requirement within 180 days
                • Cannot have had Chapter 7 discharge within 8 years
                
                Process Overview:
                1. File petition with required schedules
                2. Meeting of creditors (341 meeting)
                3. Trustee liquidates non-exempt assets
                4. Discharge typically within 4-6 months
                
                Exempt vs. Non-Exempt Assets:
                • Exempt: Primary residence (up to limits), basic personal property, retirement accounts
                • Non-Exempt: Luxury items, investment property, substantial cash
                """,
                level=2,
                estimated_read_time=8,
                prerequisites=["Introduction to Bankruptcy"],
                related_topics=["means_test", "exemptions", "trustee_role"]
            ),
            ContentSection(
                title="Chapter 11 Bankruptcy - Reorganization",
                content="""
                Chapter 11 allows businesses and individuals with substantial assets/debts to 
                reorganize their financial affairs while continuing operations.
                
                Key Features:
                • Debtor-in-possession: Debtor usually retains control
                • Automatic stay protection
                • Ability to reject/assume executory contracts
                • Cramdown provisions for dissenting creditor classes
                
                Plan Requirements:
                • Must be feasible and proposed in good faith
                • Priority claims must be paid in full
                • Best interests test: creditors receive at least liquidation value
                
                Timeline:
                • Exclusive period: 120 days to file plan (extendable)
                • Small business cases: expedited procedures
                • Complex cases may take years to confirm plan
                """,
                level=3,
                estimated_read_time=12,
                prerequisites=["Introduction to Bankruptcy"],
                related_topics=["business_reorganization", "creditor_committees", "plan_confirmation"]
            ),
            ContentSection(
                title="Chapter 13 Bankruptcy - Wage Earner Plans",
                content="""
                Chapter 13 allows individuals with regular income to develop a plan to repay 
                all or part of their debts over 3-5 years.
                
                Eligibility:
                • Regular income requirement
                • Unsecured debt under $394,725
                • Secured debt under $1,184,200
                • Must be individual (not corporation/partnership)
                
                Plan Requirements:
                • 3-5 year payment period
                • Priority debts paid in full
                • Disposable income must go to unsecured creditors
                • Cannot modify home mortgage (except for arrearages)
                
                Advantages:
                • Keep all property
                • Catch up on mortgage/car payments
                • Co-debtor stay protects co-signers
                • Strip off unsecured liens
                """,
                level=2,
                estimated_read_time=10,
                prerequisites=["Introduction to Bankruptcy"],
                related_topics=["payment_plans", "disposable_income", "lien_stripping"]
            ),
            ContentSection(
                title="Subchapter V - Small Business Reorganization",
                content="""
                Subchapter V of Chapter 11, effective February 2020, provides streamlined 
                reorganization procedures for small businesses.
                
                Eligibility:
                • Aggregate debts under $7.5 million (temporarily increased from $2.725M)
                • At least 50% of debts from business operations
                • Elect Subchapter V treatment
                
                Key Benefits:
                • No creditors' committee required
                • Debtor retains property without absolute priority rule
                • Trustee appointed to facilitate reorganization
                • Shorter deadlines for plan filing and confirmation
                
                Unique Features:
                • 90-day exclusive period for plan filing
                • Consensual plan: no creditor classes vote
                • Non-consensual plan: cramdown available with best efforts test
                • 3-5 year plan payment period
                """,
                level=3,
                estimated_read_time=8,
                prerequisites=["Chapter 11 Bankruptcy - Reorganization"],
                related_topics=["small_business_debt", "streamlined_procedures"]
            )
        ]
        
        topics["bankruptcy_basics"] = LegalTopic(
            id="bankruptcy_basics",
            title="Bankruptcy Law Fundamentals",
            category=LegalTopicCategory.BANKRUPTCY,
            description="Comprehensive guide to U.S. bankruptcy law including Chapters 7, 11, 13, and Subchapter V",
            sections=bankruptcy_sections,
            keywords=["bankruptcy", "chapter 7", "chapter 11", "chapter 13", "subchapter v", "discharge", "automatic stay"],
            last_updated=datetime.now(),
            difficulty_level=2
        )
        
        # Civil Litigation Content
        civil_litigation_sections = [
            ContentSection(
                title="Overview of Civil Litigation Process",
                content="""
                Civil litigation is the process of resolving disputes between private parties 
                through the court system. It encompasses everything from pre-suit investigation 
                to final judgment and appeals.
                
                Phases of Civil Litigation:
                1. Pre-litigation: Investigation, demand letters, settlement negotiations
                2. Pleadings: Complaint, answer, motions to dismiss
                3. Discovery: Information gathering through various methods
                4. Pre-trial: Summary judgment, settlement conferences
                5. Trial: Jury selection, opening statements, evidence, closing arguments
                6. Post-trial: Judgment, appeals, enforcement
                
                Key Participants:
                • Plaintiff: Party bringing the lawsuit
                • Defendant: Party being sued
                • Attorneys: Legal representation for parties
                • Judge: Presides over proceedings and makes legal rulings
                • Jury: Fact-finder in jury trials
                """,
                level=1,
                estimated_read_time=7,
                related_topics=["court_procedures", "legal_system"]
            ),
            ContentSection(
                title="Pleadings and Initial Motions",
                content="""
                Pleadings are formal written statements filed with the court that outline 
                each party's claims and defenses.
                
                The Complaint:
                • Statement of jurisdiction and venue
                • Facts giving rise to the claim
                • Legal theories of liability
                • Prayer for relief (damages sought)
                
                The Answer:
                • Admit or deny each allegation
                • Assert affirmative defenses
                • File counterclaims if applicable
                • Generally due within 21 days
                
                Common Pre-Answer Motions:
                • Motion to Dismiss (Rule 12(b)(6)): Failure to state a claim
                • Motion for More Definite Statement: Unclear pleadings
                • Motion to Strike: Remove irrelevant/prejudicial matter
                """,
                level=2,
                estimated_read_time=10,
                prerequisites=["Overview of Civil Litigation Process"],
                related_topics=["federal_rules_civil_procedure", "motion_practice"]
            ),
            ContentSection(
                title="Discovery Process",
                content="""
                Discovery allows parties to obtain information from each other and third parties 
                to prepare for trial.
                
                Discovery Tools:
                1. Interrogatories: Written questions requiring sworn answers
                2. Requests for Production: Documents, ESI, tangible items
                3. Requests for Admissions: Admit/deny specific facts
                4. Depositions: Oral examination under oath
                5. Physical/Mental Examinations: When condition is in controversy
                
                Discovery Rules:
                • Scope: Relevant to claims/defenses and proportional to case
                • Privilege: Attorney-client, work product, other recognized privileges
                • Timing: Initial disclosures within 14 days of Rule 26(f) conference
                • Meet and Confer: Required before filing discovery motions
                
                Electronic Discovery (e-Discovery):
                • Preservation duties trigger early in litigation
                • Form of production agreements
                • Privilege logs and clawback agreements
                • Cost-shifting considerations
                """,
                level=2,
                estimated_read_time=15,
                prerequisites=["Pleadings and Initial Motions"],
                related_topics=["e_discovery", "privilege", "depositions"]
            )
        ]
        
        topics["civil_litigation"] = LegalTopic(
            id="civil_litigation",
            title="Civil Litigation Overview",
            category=LegalTopicCategory.CIVIL_LITIGATION,
            description="Comprehensive guide to the civil litigation process from filing to judgment",
            sections=civil_litigation_sections,
            keywords=["civil litigation", "pleadings", "discovery", "trial", "motions", "federal rules"],
            last_updated=datetime.now(),
            difficulty_level=2
        )
        
        # Criminal Procedure Content
        criminal_procedure_sections = [
            ContentSection(
                title="Constitutional Foundations",
                content="""
                Criminal procedure is governed by several constitutional amendments that protect 
                individual rights against government overreach.
                
                Fourth Amendment - Search and Seizure:
                • Protects against unreasonable searches and seizures
                • Warrant requirement with probable cause
                • Exceptions: exigent circumstances, plain view, consent, etc.
                
                Fifth Amendment - Due Process and Self-Incrimination:
                • Right against self-incrimination
                • Double jeopardy protection
                • Due process clause
                • Grand jury requirement for felonies (federal)
                
                Sixth Amendment - Right to Counsel and Fair Trial:
                • Right to speedy and public trial
                • Right to jury trial
                • Right to confront witnesses
                • Right to counsel (Gideon v. Wainwright)
                
                Eighth Amendment - Cruel and Unusual Punishment:
                • Prohibition on excessive bail
                • Protection against cruel and unusual punishment
                """,
                level=1,
                estimated_read_time=8,
                related_topics=["constitutional_law", "bill_of_rights"]
            ),
            ContentSection(
                title="Arrest and Investigation",
                content="""
                The investigation and arrest process involves law enforcement gathering evidence 
                and taking suspects into custody.
                
                Arrest Requirements:
                • Probable cause that person committed a crime
                • Warrant preferred but not always required
                • Miranda warnings required for custodial interrogation
                
                Search and Seizure Rules:
                • Warrant requirement: neutral magistrate, probable cause, particularity
                • Warrant exceptions: exigent circumstances, hot pursuit, plain view
                • Search incident to arrest: person and immediate area
                • Automobile exception: mobile conveyances with probable cause
                
                Miranda Rights:
                • Custody + interrogation = Miranda required
                • Right to remain silent
                • Right to attorney
                • Statements may be used against you
                • Waiver must be knowing, intelligent, and voluntary
                """,
                level=2,
                estimated_read_time=12,
                prerequisites=["Constitutional Foundations"],
                related_topics=["miranda_rights", "search_warrants", "probable_cause"]
            )
        ]
        
        topics["criminal_procedure"] = LegalTopic(
            id="criminal_procedure",
            title="Criminal Procedure Basics",
            category=LegalTopicCategory.CRIMINAL_PROCEDURE,
            description="Fundamental concepts in criminal procedure and constitutional protections",
            sections=criminal_procedure_sections,
            keywords=["criminal procedure", "fourth amendment", "miranda", "arrest", "search", "seizure"],
            last_updated=datetime.now(),
            difficulty_level=2
        )
        
        # Family Law Content
        family_law_sections = [
            ContentSection(
                title="Divorce and Dissolution",
                content="""
                Divorce (dissolution of marriage) is the legal termination of a marital relationship.
                
                Grounds for Divorce:
                • No-fault: Irreconcilable differences, irretrievable breakdown
                • Fault-based: Adultery, cruelty, abandonment (varies by state)
                
                Types of Divorce:
                • Contested: Parties disagree on major issues
                • Uncontested: Parties agree on all terms
                • Collaborative: Team-based approach with professionals
                • Mediated: Neutral third party helps reach agreement
                
                Key Issues to Resolve:
                • Property division (equitable distribution vs. community property)
                • Spousal support/alimony
                • Child custody and visitation
                • Child support
                • Debt allocation
                
                Process Overview:
                1. File petition for dissolution
                2. Serve spouse and receive response
                3. Temporary orders hearing (if needed)
                4. Discovery and financial disclosures
                5. Settlement negotiations or trial
                6. Final judgment and decree
                """,
                level=2,
                estimated_read_time=10,
                related_topics=["property_division", "child_custody", "spousal_support"]
            ),
            ContentSection(
                title="Child Custody and Support",
                content="""
                Child custody and support laws prioritize the best interests of the child 
                while balancing parental rights.
                
                Types of Custody:
                • Legal custody: Decision-making authority for major decisions
                • Physical custody: Where child primarily resides
                • Sole vs. joint custody arrangements
                • Shared parenting plans
                
                Best Interest Factors:
                • Child's physical, emotional, and educational needs
                • Parental fitness and stability
                • Existing relationship between child and each parent
                • Child's preference (depending on age and maturity)
                • Geographic proximity and practical considerations
                
                Child Support Guidelines:
                • Based on both parents' income
                • Considers custody arrangement
                • Includes basic needs: housing, food, clothing, healthcare
                • May include additional expenses: childcare, extraordinary medical
                • Modifiable upon substantial change in circumstances
                """,
                level=2,
                estimated_read_time=8,
                prerequisites=["Divorce and Dissolution"],
                related_topics=["parenting_plans", "modification_proceedings"]
            )
        ]
        
        topics["family_law"] = LegalTopic(
            id="family_law",
            title="Family Law Fundamentals",
            category=LegalTopicCategory.FAMILY_LAW,
            description="Essential concepts in family law including divorce, custody, and support",
            sections=family_law_sections,
            keywords=["family law", "divorce", "child custody", "child support", "alimony", "dissolution"],
            last_updated=datetime.now(),
            difficulty_level=2
        )
        
        # Real Estate Content
        real_estate_sections = [
            ContentSection(
                title="Real Estate Transaction Process",
                content="""
                Real estate transactions involve the transfer of property ownership rights 
                and require careful attention to legal requirements.
                
                Purchase and Sale Agreement:
                • Identifies parties, property, and purchase price
                • Contingencies: financing, inspection, appraisal
                • Earnest money deposit
                • Closing date and possession terms
                
                Due Diligence Period:
                • Property inspection for defects
                • Review of title commitment
                • Survey and boundary verification
                • Environmental assessments (if applicable)
                
                Financing Arrangements:
                • Pre-approval vs. pre-qualification
                • Loan types: conventional, FHA, VA, jumbo
                • Interest rates and loan terms
                • Private mortgage insurance requirements
                
                Closing Process:
                • Final walkthrough
                • Title search and insurance
                • Closing disclosure review
                • Deed preparation and recording
                • Fund disbursement and key transfer
                """,
                level=2,
                estimated_read_time=12,
                related_topics=["title_insurance", "financing", "due_diligence"]
            ),
            ContentSection(
                title="Property Ownership Types",
                content="""
                Understanding different forms of property ownership is crucial for real estate 
                transactions and estate planning.
                
                Sole Ownership:
                • Fee simple absolute: Complete ownership rights
                • Life estate: Ownership for duration of life
                • Leasehold: Temporary possession rights
                
                Joint Ownership:
                • Joint tenancy: Right of survivorship
                • Tenancy in common: No survivorship rights
                • Tenancy by entirety: Married couples only (some states)
                
                Other Ownership Forms:
                • Community property: Marital property in community property states
                • Trust ownership: Property held in trust
                • Corporate ownership: Property owned by business entities
                • Condominium: Individual unit + shared common areas
                • Cooperative: Shares in corporation that owns building
                """,
                level=2,
                estimated_read_time=8,
                prerequisites=["Real Estate Transaction Process"],
                related_topics=["estate_planning", "property_rights", "marital_property"]
            )
        ]
        
        topics["real_estate"] = LegalTopic(
            id="real_estate",
            title="Real Estate Transactions",
            category=LegalTopicCategory.REAL_ESTATE,
            description="Guide to real estate transactions and property ownership concepts",
            sections=real_estate_sections,
            keywords=["real estate", "property", "closing", "deed", "title", "mortgage", "ownership"],
            last_updated=datetime.now(),
            difficulty_level=2
        )
        
        # Business Formation Content
        business_formation_sections = [
            ContentSection(
                title="Choosing a Business Entity",
                content="""
                Selecting the appropriate business entity affects taxation, liability, 
                management structure, and operational flexibility.
                
                Sole Proprietorship:
                • Simplest form of business
                • No separate legal entity
                • Personal liability for business debts
                • Pass-through taxation
                
                Partnership:
                • Two or more owners
                • General partnership: shared management and liability
                • Limited partnership: general and limited partners
                • Pass-through taxation
                
                Limited Liability Company (LLC):
                • Flexible management structure
                • Limited liability protection
                • Pass-through or corporate taxation (election)
                • Operating agreement governs internal affairs
                
                Corporation:
                • Separate legal entity
                • Limited liability for shareholders
                • Double taxation (C-Corp) or pass-through (S-Corp)
                • Board of directors and officers structure
                
                Selection Factors:
                • Liability protection needs
                • Tax implications
                • Management preferences
                • Ownership transfer flexibility
                • Regulatory requirements
                """,
                level=2,
                estimated_read_time=10,
                related_topics=["liability_protection", "taxation", "business_planning"]
            ),
            ContentSection(
                title="Corporate Formation Requirements",
                content="""
                Forming a corporation requires compliance with state law requirements 
                and ongoing corporate formalities.
                
                Articles of Incorporation:
                • Corporate name and purpose
                • Number and type of authorized shares
                • Registered agent and office
                • Incorporator information
                
                Initial Corporate Actions:
                • Adopt bylaws
                • Elect directors
                • Appoint officers
                • Issue stock certificates
                • Open corporate bank account
                
                Corporate Formalities:
                • Hold annual shareholder meetings
                • Maintain corporate records
                • File annual reports
                • Keep personal and corporate assets separate
                • Document major decisions in meeting minutes
                
                S-Corporation Election:
                • File Form 2553 within 75 days
                • Pass-through taxation
                • Restrictions: 100 shareholders, one class of stock, U.S. residents
                """,
                level=3,
                estimated_read_time=12,
                prerequisites=["Choosing a Business Entity"],
                related_topics=["corporate_governance", "shareholder_agreements", "securities_law"]
            )
        ]
        
        topics["business_formation"] = LegalTopic(
            id="business_formation",
            title="Business Formation Options",
            category=LegalTopicCategory.BUSINESS_FORMATION,
            description="Comprehensive guide to business entity selection and formation",
            sections=business_formation_sections,
            keywords=["business formation", "corporation", "LLC", "partnership", "sole proprietorship", "entity selection"],
            last_updated=datetime.now(),
            difficulty_level=2
        )
        
        return topics
    
    def get_all_topics(self) -> List[LegalTopic]:
        return list(self._topics.values())
    
    def get_topic(self, topic_id: str) -> Optional[LegalTopic]:
        return self._topics.get(topic_id)
    
    def get_topics_by_category(self, category: LegalTopicCategory) -> List[LegalTopic]:
        return [topic for topic in self._topics.values() if topic.category == category]
    
    def search_topics(self, query: str) -> List[LegalTopic]:
        query_lower = query.lower()
        matching_topics = []
        
        for topic in self._topics.values():
            # Search in title, description, and keywords
            if (query_lower in topic.title.lower() or 
                query_lower in topic.description.lower() or
                any(query_lower in keyword.lower() for keyword in topic.keywords)):
                matching_topics.append(topic)
                continue
            
            # Search in section content
            for section in topic.sections:
                if (query_lower in section.title.lower() or 
                    query_lower in section.content.lower()):
                    matching_topics.append(topic)
                    break
        
        return matching_topics
    
    def get_topic_section(self, topic_id: str, section_index: int) -> Optional[ContentSection]:
        topic = self.get_topic(topic_id)
        if topic and 0 <= section_index < len(topic.sections):
            return topic.sections[section_index]
        return None
    
    def get_prerequisites(self, topic_id: str) -> List[str]:
        topic = self.get_topic(topic_id)
        if not topic:
            return []
        
        all_prerequisites = set()
        for section in topic.sections:
            all_prerequisites.update(section.prerequisites)
        
        return list(all_prerequisites)
    
    def get_related_topics(self, topic_id: str) -> List[str]:
        topic = self.get_topic(topic_id)
        if not topic:
            return []
        
        all_related = set()
        for section in topic.sections:
            all_related.update(section.related_topics)
        
        return list(all_related)