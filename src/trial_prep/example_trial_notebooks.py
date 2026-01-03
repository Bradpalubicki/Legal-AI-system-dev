"""
Comprehensive Example Trial Notebooks for Different Case Types

This module provides complete example trial notebooks for:
1. Personal Injury Cases
2. Contract Dispute Cases  
3. Criminal Defense Cases

Each example includes witness lists, exhibit indexes, jury instructions,
and day-by-day trial schedules with customization notes for attorneys.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, date, time
from enum import Enum
import json

class CaseType(Enum):
    PERSONAL_INJURY = "personal_injury"
    CONTRACT_DISPUTE = "contract_dispute"
    CRIMINAL_DEFENSE = "criminal_defense"

class WitnessType(Enum):
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant" 
    EXPERT = "expert"
    FACT = "fact"
    CHARACTER = "character"

class ExhibitType(Enum):
    DOCUMENT = "document"
    PHOTO = "photo"
    MEDICAL_RECORD = "medical_record"
    CONTRACT = "contract"
    FINANCIAL = "financial"
    PHYSICAL_EVIDENCE = "physical_evidence"
    VIDEO = "video"
    AUDIO = "audio"

@dataclass
class ExampleWitness:
    name: str
    witness_type: WitnessType
    role: str
    key_testimony: List[str]
    estimated_time: str
    preparation_notes: str
    potential_objections: List[str]
    customization_tips: str

@dataclass
class ExampleExhibit:
    exhibit_number: str
    description: str
    exhibit_type: ExhibitType
    source: str
    relevance: str
    foundation_requirements: List[str]
    potential_objections: List[str]
    customization_tips: str

@dataclass
class ExampleJuryInstruction:
    instruction_id: str
    title: str
    category: str
    instruction_text: str
    applicable_law: str
    customization_notes: str

@dataclass
class TrialDay:
    day_number: int
    date: Optional[date]
    theme: str
    objectives: List[str]
    witnesses: List[str]
    exhibits: List[str]
    time_blocks: Dict[str, str]
    preparation_tasks: List[str]
    contingency_plans: List[str]
    customization_notes: str

@dataclass
class ExampleTrialNotebook:
    case_type: CaseType
    case_title: str
    case_overview: str
    theory_of_case: str
    key_themes: List[str]
    witnesses: List[ExampleWitness]
    exhibits: List[ExampleExhibit]
    jury_instructions: List[ExampleJuryInstruction]
    trial_schedule: List[TrialDay]
    opening_statement_outline: str
    closing_argument_outline: str
    general_customization_guide: str

class ExampleTrialNotebooks:
    """Comprehensive example trial notebooks for different case types."""
    
    def __init__(self):
        self.notebooks = {
            CaseType.PERSONAL_INJURY: self._create_personal_injury_example(),
            CaseType.CONTRACT_DISPUTE: self._create_contract_dispute_example(),
            CaseType.CRIMINAL_DEFENSE: self._create_criminal_defense_example()
        }
    
    def get_example_notebook(self, case_type: CaseType) -> ExampleTrialNotebook:
        """Get example trial notebook for specified case type."""
        return self.notebooks.get(case_type)
    
    def get_all_examples(self) -> Dict[CaseType, ExampleTrialNotebook]:
        """Get all example trial notebooks."""
        return self.notebooks
    
    def _create_personal_injury_example(self) -> ExampleTrialNotebook:
        """Create comprehensive personal injury trial notebook example."""
        
        witnesses = [
            ExampleWitness(
                name="Jane Smith (Plaintiff)",
                witness_type=WitnessType.PLAINTIFF,
                role="Injured Party",
                key_testimony=[
                    "Description of the accident and immediate aftermath",
                    "Pain and suffering experienced since the incident",
                    "Impact on daily activities and work capacity",
                    "Medical treatments and ongoing care needs",
                    "Financial losses and out-of-pocket expenses"
                ],
                estimated_time="2-3 hours",
                preparation_notes="Focus on emotional impact while maintaining credibility. Practice describing pain levels consistently. Review medical timeline thoroughly.",
                potential_objections=["Speculation about causation", "Hearsay regarding medical advice", "Opinion testimony about damages"],
                customization_tips="Adapt testimony focus based on specific injury type. For brain injuries, emphasize cognitive changes. For spinal injuries, focus on mobility limitations."
            ),
            ExampleWitness(
                name="Dr. Michael Johnson, M.D.",
                witness_type=WitnessType.EXPERT,
                role="Treating Physician/Medical Expert",
                key_testimony=[
                    "Diagnosis and treatment of plaintiff's injuries",
                    "Causal relationship between accident and injuries",
                    "Prognosis and future medical needs",
                    "Disability ratings and work restrictions",
                    "Cost of future medical care"
                ],
                estimated_time="1.5-2 hours",
                preparation_notes="Review all medical records and imaging. Prepare visual aids showing injury progression. Calculate future medical costs with supporting data.",
                potential_objections=["Lack of foundation for expert opinion", "Speculation about future costs", "Bias due to treating relationship"],
                customization_tips="For complex injuries, consider multiple medical experts. Orthopedic surgeons for bone/joint injuries, neurologists for brain injuries, psychiatrists for PTSD."
            ),
            ExampleWitness(
                name="Officer Sarah Williams",
                witness_type=WitnessType.FACT,
                role="Investigating Police Officer",
                key_testimony=[
                    "Scene observations and measurements",
                    "Defendant's statements at the scene",
                    "Physical evidence collected",
                    "Weather and road conditions",
                    "Traffic citations issued"
                ],
                estimated_time="45 minutes",
                preparation_notes="Review police report thoroughly. Prepare scene diagrams and photographs. Clarify any inconsistencies in the report.",
                potential_objections=["Hearsay statements", "Lack of personal knowledge", "Opinion testimony about fault"],
                customization_tips="For workplace injuries, substitute safety inspector. For product liability, include investigating engineer or safety expert."
            ),
            ExampleWitness(
                name="Robert Chen",
                witness_type=WitnessType.FACT,
                role="Eyewitness",
                key_testimony=[
                    "Direct observation of the accident",
                    "Defendant's driving behavior before impact",
                    "Plaintiff's condition immediately after accident",
                    "Emergency response timeline"
                ],
                estimated_time="30-45 minutes",
                preparation_notes="Walk through testimony chronologically. Address any inconsistencies with prior statements. Prepare for cross-examination on visibility and attention.",
                potential_objections=["Lack of foundation for speed estimates", "Speculation about intent", "Memory issues"],
                customization_tips="Identify multiple eyewitnesses when available. Prioritize witnesses with clear view and no bias. For workplace injuries, include coworkers who saw the incident."
            ),
            ExampleWitness(
                name="Lisa Thompson, CPA",
                witness_type=WitnessType.EXPERT,
                role="Economic Damages Expert",
                key_testimony=[
                    "Lost wage calculations",
                    "Lost earning capacity analysis",
                    "Present value of future losses",
                    "Benefit losses and replacement costs",
                    "Methodology and assumptions used"
                ],
                estimated_time="1-1.5 hours",
                preparation_notes="Review employment records, tax returns, and career trajectory. Prepare charts showing calculations. Address plaintiff's work-life expectancy.",
                potential_objections=["Speculative assumptions", "Failure to consider other factors", "Bias in methodology"],
                customization_tips="For self-employed plaintiffs, focus on business records and profit trends. For homemakers, calculate replacement value of household services."
            )
        ]
        
        exhibits = [
            ExampleExhibit(
                exhibit_number="P-1",
                description="Police Report and Accident Reconstruction Diagram",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Metropolitan Police Department",
                relevance="Shows fault determination, scene measurements, and witness statements",
                foundation_requirements=["Authentication by investigating officer", "Chain of custody", "Business records exception"],
                potential_objections=["Hearsay", "Lack of foundation", "Contains conclusions"],
                customization_tips="Redact any prejudicial conclusions. For workplace injuries, substitute OSHA report or internal incident report."
            ),
            ExampleExhibit(
                exhibit_number="P-2 through P-15",
                description="Scene Photographs (Day of Accident)",
                exhibit_type=ExhibitType.PHOTO,
                source="Police Department and Plaintiff's Attorney Investigation",
                relevance="Shows vehicle damage, road conditions, and accident scene layout",
                foundation_requirements=["Authentication by photographer", "Accurate representation of scene", "Relevance to case facts"],
                potential_objections=["Prejudicial impact", "Not accurate representation", "Cumulative evidence"],
                customization_tips="Include both overview and detail shots. For product liability, focus on product defect photos. For premises liability, emphasize dangerous conditions."
            ),
            ExampleExhibit(
                exhibit_number="P-16",
                description="Complete Medical Records from City General Hospital",
                exhibit_type=ExhibitType.MEDICAL_RECORD,
                source="City General Hospital Medical Records Department",
                relevance="Documents initial diagnosis, treatment, and injury severity",
                foundation_requirements=["Business records foundation", "Custodian testimony", "Regular course of business"],
                potential_objections=["Hearsay", "Incomplete records", "Prejudicial diagnostic images"],
                potential_objections=["Hearsay within hearsay", "Lack of foundation", "Prejudicial content"],
                customization_tips="Organize chronologically by treatment provider. Highlight key diagnostic findings and treatment recommendations."
            ),
            ExampleExhibit(
                exhibit_number="P-17",
                description="MRI and X-ray Images with Radiologist Reports",
                exhibit_type=ExhibitType.MEDICAL_RECORD,
                source="Advanced Imaging Center",
                relevance="Shows extent of internal injuries and validates medical testimony",
                foundation_requirements=["Authentication by radiologist", "Chain of custody", "Proper medical procedure"],
                potential_objections=["Prejudicial impact", "Lack of foundation", "Cumulative with other medical evidence"],
                customization_tips="Use enlarged images for jury presentation. Consider animation for complex injuries. Prepare simplified explanations of medical terminology."
            ),
            ExampleExhibit(
                exhibit_number="P-18",
                description="Employment Records and Wage Statements (5 years)",
                exhibit_type=ExhibitType.FINANCIAL,
                source="Plaintiff's Employer HR Department",
                relevance="Establishes earning capacity and lost wages calculation basis",
                foundation_requirements=["Business records exception", "Custodian testimony", "Authentication"],
                potential_objections=["Relevance to future earnings", "Incomplete records", "Privacy concerns"],
                customization_tips="Include promotion history and performance reviews. For self-employed, use tax returns and business records. Address any employment gaps."
            ),
            ExampleExhibit(
                exhibit_number="P-19",
                description="Economic Damages Calculation Summary",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Lisa Thompson, CPA - Economic Expert",
                relevance="Shows methodology and calculations for economic losses",
                foundation_requirements=["Expert qualification", "Basis for opinion", "Reliable methodology"],
                potential_objections=["Speculative assumptions", "Improper foundation", "Prejudicial presentation"],
                customization_tips="Present in clear, understandable format. Include alternative scenarios for different recovery levels. Break down assumptions clearly."
            ),
            ExampleExhibit(
                exhibit_number="P-20",
                description="Day in the Life Documentary Video",
                exhibit_type=ExhibitType.VIDEO,
                source="Professional Videographer",
                relevance="Demonstrates impact of injuries on plaintiff's daily activities",
                foundation_requirements=["Authentication", "Accurate representation", "Relevance without prejudice"],
                potential_objections=["Prejudicial impact", "Staged presentation", "Cumulative evidence"],
                customization_tips="Keep professional and factual. Focus on legitimate daily struggles. Avoid overly emotional content that could backfire."
            )
        ]
        
        jury_instructions = [
            ExampleJuryInstruction(
                instruction_id="PI-1",
                title="Negligence - Elements of Proof",
                category="Liability",
                instruction_text="""To prove negligence, the plaintiff must establish by a preponderance of the evidence:
1. The defendant owed a duty of care to the plaintiff
2. The defendant breached that duty by failing to act as a reasonably prudent person
3. The defendant's breach of duty was a proximate cause of plaintiff's injuries
4. The plaintiff suffered actual damages as a result""",
                applicable_law="State tort law regarding negligence standards",
                customization_notes="Modify duty standard based on case type (professional negligence, premises liability, etc.). Add specific statutory duties if applicable."
            ),
            ExampleJuryInstruction(
                instruction_id="PI-2",
                title="Proximate Cause",
                category="Causation",
                instruction_text="""Proximate cause means that the defendant's act or failure to act was a substantial factor in bringing about the plaintiff's injuries. The defendant's conduct is a proximate cause if the injuries were a natural and probable consequence of the conduct.""",
                applicable_law="State causation standards in tort cases",
                customization_notes="For complex causation issues, consider multiple proximate cause instruction. Address intervening causes if relevant to case facts."
            ),
            ExampleJuryInstruction(
                instruction_id="PI-3", 
                title="Damages - Medical Expenses",
                category="Damages",
                instruction_text="""If you find for the plaintiff, you may award damages for reasonable and necessary medical expenses incurred as a result of the defendant's negligence. This includes both past medical expenses and future medical expenses that are reasonably certain to be incurred.""",
                applicable_law="State damages law for personal injury cases",
                customization_notes="Add specific language about medical insurance payments and collateral source rule based on state law."
            ),
            ExampleJuryInstruction(
                instruction_id="PI-4",
                title="Damages - Pain and Suffering", 
                category="Damages",
                instruction_text="""You may award damages for pain and suffering, including physical pain, mental anguish, and loss of enjoyment of life. There is no exact standard for measuring such damages. You should use your judgment based on the evidence presented.""",
                applicable_law="State non-economic damages standards",
                customization_notes="Check for state caps on non-economic damages. Consider per diem or golden rule instruction limitations."
            ),
            ExampleJuryInstruction(
                instruction_id="PI-5",
                title="Comparative Negligence",
                category="Defenses",
                instruction_text="""If you find that both parties were negligent, you must determine the percentage of fault attributable to each party. The plaintiff's damages will be reduced by the percentage of fault assigned to the plaintiff.""",
                applicable_law="State comparative negligence statute",
                customization_notes="Modify based on pure vs. modified comparative negligence state law. Include threshold percentages if applicable."
            )
        ]
        
        trial_schedule = [
            TrialDay(
                day_number=1,
                date=None,
                theme="Setting the Stage - The Accident and Its Immediate Impact",
                objectives=[
                    "Establish liability through compelling opening statement",
                    "Present clear accident reconstruction evidence",
                    "Show immediate severity of plaintiff's injuries",
                    "Create emotional connection with plaintiff's experience"
                ],
                witnesses=["Officer Sarah Williams", "Robert Chen (Eyewitness)"],
                exhibits=["P-1 (Police Report)", "P-2 through P-15 (Scene Photos)", "P-20 (Day in Life Video - excerpt)"],
                time_blocks={
                    "9:00 AM - 10:30 AM": "Opening Statements (30 min plaintiff, 20 min defense)",
                    "10:45 AM - 12:00 PM": "Officer Williams - Scene investigation and evidence",
                    "1:30 PM - 2:30 PM": "Robert Chen - Eyewitness testimony",
                    "2:45 PM - 4:30 PM": "Begin plaintiff testimony - background and accident description"
                },
                preparation_tasks=[
                    "Final rehearsal of opening statement with visual aids",
                    "Prepare police officer for cross-examination on report inconsistencies",
                    "Review eyewitness prior statements for consistency",
                    "Set up demonstrative exhibits and technology"
                ],
                contingency_plans=[
                    "If police officer unavailable, introduce report through records custodian",
                    "If eyewitness testimony excluded, emphasize physical evidence",
                    "If defendant objects to video, have still photos ready as backup"
                ],
                customization_notes="For premises liability cases, lead with property owner's knowledge of dangerous condition. For product liability, start with product failure evidence."
            ),
            TrialDay(
                day_number=2,
                date=None,
                theme="The Human Impact - Plaintiff's Testimony and Immediate Medical Care",
                objectives=[
                    "Complete plaintiff's direct examination with emotional impact",
                    "Establish medical treatment timeline and severity",
                    "Document immediate medical needs and emergency care",
                    "Survive defense cross-examination of plaintiff"
                ],
                witnesses=["Jane Smith (Plaintiff) - continued", "Dr. Emergency Room Physician"],
                exhibits=["P-16 (Hospital Records)", "P-17 (Initial X-rays)", "Medical bills from emergency treatment"],
                time_blocks={
                    "9:00 AM - 11:00 AM": "Complete plaintiff direct examination - pain, suffering, life impact",
                    "11:15 AM - 12:30 PM": "Defense cross-examination of plaintiff", 
                    "1:30 PM - 2:45 PM": "Plaintiff redirect and emergency room physician testimony",
                    "3:00 PM - 4:30 PM": "Introduce medical records and initial treatment evidence"
                },
                preparation_tasks=[
                    "Intensive preparation of plaintiff for cross-examination",
                    "Review all medical records with emergency physician",
                    "Prepare plaintiff for difficult questions about pre-existing conditions",
                    "Organize medical exhibits chronologically"
                ],
                contingency_plans=[
                    "If plaintiff struggles under cross, use redirect to rehabilitate key points",
                    "If medical records are challenged, have custodian available to testify",
                    "If emergency physician unavailable, use records and other treating doctors"
                ],
                customization_notes="For catastrophic injuries, spend more time on life impact. For soft tissue injuries, focus on credibility and consistency of pain descriptions."
            ),
            TrialDay(
                day_number=3,
                date=None,
                theme="Medical Proof - Establishing the Full Extent of Injuries",
                objectives=[
                    "Prove causal relationship between accident and all injuries",
                    "Establish permanency of injuries and ongoing treatment needs",
                    "Present credible medical evidence through treating physicians",
                    "Lay foundation for future medical care damages"
                ],
                witnesses=["Dr. Michael Johnson (Treating Physician)", "Physical Therapist", "Additional specialists as needed"],
                exhibits=["Complete medical records", "P-17 (All imaging studies)", "Medical illustrations/anatomical models"],
                time_blocks=[
                    "9:00 AM - 11:30 AM: Dr. Johnson - diagnosis, treatment, causation, prognosis",
                    "11:45 AM - 12:30 PM: Physical therapist - ongoing treatment and functional limitations",
                    "1:30 PM - 3:00 PM: Additional medical witnesses (orthopedist, neurologist, etc.)",
                    "3:15 PM - 4:30 PM: Introduction of comprehensive medical records and imaging"
                ],
                preparation_tasks=[
                    "Detailed medical preparation sessions with all physician witnesses",
                    "Prepare medical demonstrative aids and anatomical models",
                    "Organize medical records by treating provider and chronology",
                    "Prepare physicians for defense attacks on causation"
                ],
                contingency_plans=[
                    "If treating physician unavailable, use medical records and other doctors",
                    "If causation challenged, have additional medical literature ready",
                    "If imaging excluded, rely on clinical findings and physician observations"
                ],
                customization_notes="For complex medical cases, consider limiting to key physicians to avoid jury fatigue. For mild injuries, focus on credibility and objective findings."
            ),
            TrialDay(
                day_number=4,
                date=None,
                theme="Economic Impact - Proving Financial Damages",
                objectives=[
                    "Establish plaintiff's earning capacity before the accident",
                    "Prove lost wages and diminished earning capacity",
                    "Present credible economic damages calculations",
                    "Demonstrate financial impact on plaintiff and family"
                ],
                witnesses=["Lisa Thompson, CPA (Economic Expert)", "Plaintiff's Supervisor", "Vocational Rehabilitation Expert"],
                exhibits=["P-18 (Employment Records)", "P-19 (Economic Calculations)", "Tax returns and financial records"],
                time_blocks={
                    "9:00 AM - 11:00 AM": "Economic expert - lost wages and earning capacity analysis",
                    "11:15 AM - 12:00 PM": "Plaintiff's supervisor - work performance and career trajectory",
                    "1:30 PM - 2:30 PM": "Vocational expert - work restrictions and alternative employment",
                    "2:45 PM - 4:30 PM": "Financial documents and economic exhibits introduction"
                },
                preparation_tasks=[
                    "Review all economic calculations and assumptions with expert",
                    "Prepare employer witness for testimony about plaintiff's value",
                    "Organize financial exhibits for clear presentation",
                    "Prepare for defense challenges to economic assumptions"
                ],
                contingency_plans=[
                    "If economic expert attacked, have alternative calculation methods ready",
                    "If employer unavailable, use HR records and performance evaluations",
                    "If vocational expert excluded, rely on treating physician work restrictions"
                ],
                customization_notes="For young plaintiffs, emphasize career growth potential. For older plaintiffs, focus on experience value. For unemployed plaintiffs, use household services methodology."
            ),
            TrialDay(
                day_number=5,
                date=None,
                theme="Closing the Case - Final Evidence and Powerful Closing",
                objectives=[
                    "Present any remaining evidence to complete the case",
                    "Address any defense evidence through rebuttal",
                    "Deliver compelling closing argument that ties everything together",
                    "Provide clear damages request with supporting calculations"
                ],
                witnesses=["Rebuttal witnesses as needed", "Character witnesses if appropriate"],
                exhibits=["Day in Life video (complete)", "Damages summary exhibit", "Timeline of plaintiff's treatment"],
                time_blocks={
                    "9:00 AM - 10:30 AM": "Final plaintiff witnesses and rebuttal evidence",
                    "10:45 AM - 12:00 PM": "Defense case (if any) or preparation for closing",
                    "1:30 PM - 2:30 PM": "Plaintiff's closing argument",
                    "2:30 PM - 3:30 PM": "Defense closing argument", 
                    "3:45 PM - 4:00 PM": "Plaintiff's rebuttal argument"
                ],
                preparation_tasks=[
                    "Prepare powerful closing argument with visual aids",
                    "Calculate specific damages request with supporting exhibits",
                    "Prepare rebuttal argument anticipating defense themes",
                    "Review jury instructions and prepare requested modifications"
                ],
                contingency_plans=[
                    "If defense presents unexpected evidence, request time for rebuttal preparation",
                    "If jury instructions disputed, have supporting case law ready",
                    "If technical difficulties with closing exhibits, have backup presentation ready"
                ],
                customization_notes="Tailor closing to jury composition and observed reactions. For conservative juries, emphasize facts over emotion. For sympathetic juries, balance emotion with credible damages."
            )
        ]
        
        return ExampleTrialNotebook(
            case_type=CaseType.PERSONAL_INJURY,
            case_title="Smith v. Johnson - Motor Vehicle Collision",
            case_overview="""
            Plaintiff Jane Smith sustained significant injuries in a motor vehicle collision 
            caused by defendant Robert Johnson's negligent driving. This notebook provides 
            a comprehensive trial preparation framework for personal injury cases involving 
            vehicle accidents, with adaptable elements for other personal injury contexts.
            """,
            theory_of_case="Defendant's careless driving caused a preventable accident that has permanently altered plaintiff's life, resulting in significant physical, emotional, and financial damages that require fair compensation.",
            key_themes=[
                "Preventable tragedy - this accident didn't have to happen",
                "Life forever changed - plaintiff's struggles with daily activities",
                "Accountability matters - defendant must take responsibility", 
                "Fair compensation - restoring what was taken from plaintiff",
                "Credible evidence - medical proof supports all claims"
            ],
            witnesses=witnesses,
            exhibits=exhibits,
            jury_instructions=jury_instructions,
            trial_schedule=trial_schedule,
            opening_statement_outline="""
            1. Hook: 'In three seconds, Jane Smith's life changed forever.'
            2. Introduce plaintiff as real person with hopes and dreams
            3. Set scene: normal day that became a nightmare
            4. Describe the collision with defendant's negligent choices
            5. Walk through plaintiff's journey of pain and recovery
            6. Preview the evidence that will prove defendant's fault
            7. Explain what fair compensation means in this case
            8. Promise: 'By the end of this trial, you'll know what justice requires.'
            """,
            closing_argument_outline="""
            1. Remind jury of their role as voice of the community
            2. Review undisputed facts that prove defendant's negligence
            3. Address defense arguments with factual responses
            4. Walk through plaintiff's injuries with medical evidence
            5. Explain economic damages with expert calculations
            6. Discuss pain and suffering with specific examples
            7. Request specific damages amount with justification
            8. Call for verdict that provides justice and accountability
            """,
            general_customization_guide="""
            PERSONAL INJURY CUSTOMIZATION GUIDE:
            
            1. CASE TYPE ADAPTATIONS:
               - Motor Vehicle: Focus on traffic laws and driving standards
               - Premises Liability: Emphasize property owner's knowledge and duty
               - Product Liability: Highlight design defects and manufacturer responsibility
               - Medical Malpractice: Address standard of care and expert battles
               - Workplace Injury: Include safety regulations and employer duties
            
            2. INJURY SEVERITY MODIFICATIONS:
               - Catastrophic Injuries: More medical experts, life care planning, family impact
               - Soft Tissue: Focus on credibility, consistency, objective findings
               - Brain Injuries: Neuropsychological testing, cognitive impact evidence
               - Spinal Injuries: Functional capacity evaluations, mobility demonstrations
            
            3. PLAINTIFF CHARACTERISTICS:
               - Young Plaintiffs: Emphasize lost potential, career impact, family planning
               - Elderly Plaintiffs: Focus on dignity, independence, remaining quality years
               - High Earners: Detailed economic analysis, lifestyle impact
               - Unemployed/Low Income: Household services, personal care needs
            
            4. DEFENDANT CONSIDERATIONS:
               - Individual Defendants: Personal responsibility, insurance coverage
               - Corporate Defendants: Policies, training, systemic problems
               - Government Entities: Notice requirements, sovereign immunity issues
               - Multiple Defendants: Joint liability, contribution claims
            
            5. VENUE AND JURY CONSIDERATIONS:
               - Conservative Venues: Focus on facts, medical proof, reasonable damages
               - Liberal Venues: More emphasis on accountability, corporate responsibility
               - Rural Areas: Relate to plaintiff's background, avoid complex theories
               - Urban Areas: Address skepticism with strong evidence
            
            6. EVIDENCE ADAPTATIONS:
               - Surveillance Video: Authenticate carefully, address privacy objections
               - Social Media: Foundation requirements, privacy settings, authenticity
               - Electronic Records: Metadata, chain of custody, technical witnesses
               - Expert Testimony: Daubert challenges, alternative experts, cost considerations
            
            7. DAMAGES MODIFICATIONS:
               - High Damages Cases: Break down into understandable components
               - Modest Damages Cases: Focus on legitimacy of all claimed damages
               - Future Care: Life care planners, medical inflation, alternative scenarios
               - Economic Losses: Multiple methodologies, sensitivity analysis
            """
        )
    
    def _create_contract_dispute_example(self) -> ExampleTrialNotebook:
        """Create comprehensive contract dispute trial notebook example."""
        
        witnesses = [
            ExampleWitness(
                name="Michael Rodriguez (Plaintiff CEO)",
                witness_type=WitnessType.PLAINTIFF,
                role="Chief Executive Officer - TechStart Solutions",
                key_testimony=[
                    "Contract negotiation process and agreed terms",
                    "Performance by plaintiff under the contract",
                    "Defendant's material breaches and their timing",
                    "Damages suffered including lost profits and additional costs",
                    "Attempts to mitigate damages and resolve disputes"
                ],
                estimated_time="2.5-3 hours",
                preparation_notes="Review all contract communications chronologically. Prepare for credibility attacks on damages claims. Practice explaining technical aspects in lay terms.",
                potential_objections=["Self-serving testimony", "Speculation about damages", "Lack of foundation for business practices"],
                customization_tips="For construction contracts, focus on project timeline and change orders. For employment contracts, emphasize performance standards and termination procedures."
            ),
            ExampleWitness(
                name="Sarah Kim, CPA",
                witness_type=WitnessType.EXPERT,
                role="Forensic Accountant - Damages Expert",
                key_testimony=[
                    "Analysis of financial records and lost profit calculations",
                    "Methodology for determining contract damages",
                    "Mitigation of damages efforts and results",
                    "Comparison of actual vs. projected performance",
                    "Industry standards for similar business arrangements"
                ],
                estimated_time="1.5-2 hours",
                preparation_notes="Prepare detailed damage calculations with multiple scenarios. Review opposing expert's report for weaknesses. Create clear visual presentations of financial analysis.",
                potential_objections=["Speculative damages", "Unreliable methodology", "Lack of foundation for industry comparisons"],
                customization_tips="For service contracts, focus on cost of replacement services. For sales contracts, emphasize market price differentials and cover damages."
            ),
            ExampleWitness(
                name="Jennifer Walsh",
                witness_type=WitnessType.FACT,
                role="Project Manager - TechStart Solutions",
                key_testimony=[
                    "Day-to-day contract performance and communications",
                    "Specific instances of defendant's non-performance",
                    "Impact of delays on other business operations",
                    "Documentation of performance issues and complaints",
                    "Attempts to work with defendant to resolve problems"
                ],
                estimated_time="1-1.5 hours",
                preparation_notes="Review project files and communication records thoroughly. Prepare timeline of key events. Practice explaining technical project management concepts.",
                potential_objections=["Hearsay statements", "Lack of personal knowledge of contract terms", "Opinion testimony"],
                customization_tips="For manufacturing contracts, include quality control manager. For licensing agreements, substitute compliance or legal affairs manager."
            ),
            ExampleWitness(
                name="David Chen",
                witness_type=WitnessType.EXPERT,
                role="Industry Expert - Software Development Standards",
                key_testimony=[
                    "Industry standards for software development contracts",
                    "Reasonable expectations for project deliverables",
                    "Standard practices for change management and scope",
                    "Analysis of defendant's performance against industry norms",
                    "Opinion on whether defendant's conduct met professional standards"
                ],
                estimated_time="1.5 hours",
                preparation_notes="Review contract terms against industry standards. Prepare examples of similar successful projects. Address defendant's justifications for non-performance.",
                potential_objections=["Lack of foundation for industry standards", "Opinion on legal conclusions", "Bias due to consulting relationship"],
                customization_tips="Adapt expert to contract type - construction expert for building contracts, finance expert for loan agreements, technology expert for IT contracts."
            ),
            ExampleWitness(
                name="Amanda Foster",
                witness_type=WitnessType.FACT,
                role="Client Representative - Affected by Contract Breach",
                key_testimony=[
                    "Impact of defendant's breach on third-party relationships",
                    "Additional costs incurred due to performance delays",
                    "Lost business opportunities and customer relationships",
                    "Efforts to find alternative service providers",
                    "Ongoing effects of the contract breach"
                ],
                estimated_time="45 minutes",
                preparation_notes="Prepare documentation of third-party impacts. Quantify additional costs with supporting records. Address any alternative arrangements made.",
                potential_objections=["Relevance to contract damages", "Speculation about lost opportunities", "Hearsay regarding third-party communications"],
                customization_tips="For supply contracts, substitute end customer. For service contracts, include internal stakeholders affected by poor performance."
            )
        ]
        
        exhibits = [
            ExampleExhibit(
                exhibit_number="P-1",
                description="Original Software Development Agreement with all amendments",
                exhibit_type=ExhibitType.CONTRACT,
                source="Company contract files and legal counsel",
                relevance="Establishes the parties' contractual obligations and performance standards",
                foundation_requirements=["Authentication by signatory", "Chain of custody", "Complete agreement including modifications"],
                potential_objections=["Parole evidence rule", "Incomplete document", "Lack of foundation"],
                customization_tips="For oral contracts, use written confirmations and conduct evidence. For implied contracts, gather course of dealing evidence."
            ),
            ExampleExhibit(
                exhibit_number="P-2 through P-25", 
                description="Email Communications Between Parties (Chronological)",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Company email systems and personal records",
                relevance="Shows contract interpretation, performance issues, and breach notifications",
                foundation_requirements=["Authentication of email systems", "Chain of custody", "Accurate copies"],
                potential_objections=["Hearsay", "Authentication challenges", "Selective production"],
                potential_objections=["Best evidence rule", "Hearsay", "Incomplete exchanges"],
                customization_tips="Organize by topic and chronology. Redact privileged communications. Include metadata for disputed authenticity."
            ),
            ExampleExhibit(
                exhibit_number="P-26",
                description="Project Deliverables and Work Product Analysis",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Technical review by plaintiff's IT department",
                relevance="Demonstrates quality and completeness of defendant's performance",
                foundation_requirements=["Technical expert testimony", "Comparison to contract specifications", "Industry standard analysis"],
                potential_objections=["Opinion testimony", "Lack of foundation", "Prejudicial presentation"],
                customization_tips="Use visual comparisons for contract vs. actual performance. For service contracts, document service level failures."
            ),
            ExampleExhibit(
                exhibit_number="P-27",
                description="Financial Records - Damages Calculation Workpapers",
                exhibit_type=ExhibitType.FINANCIAL,
                source="Plaintiff's accounting records and expert analysis",
                relevance="Shows methodology and basis for claimed damages",
                foundation_requirements=["Business records exception", "Expert foundation", "Reliable methodology"],
                potential_objections=["Speculative damages", "Unreliable calculations", "Missing supporting data"],
                customization_tips="Break down complex calculations into understandable components. Include sensitivity analysis for key assumptions."
            ),
            ExampleExhibit(
                exhibit_number="P-28",
                description="Industry Benchmarking Study and Comparative Analysis",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Industry expert research and analysis",
                relevance="Provides context for performance standards and damage calculations",
                foundation_requirements=["Expert qualification", "Reliable methodology", "Relevant comparison data"],
                potential_objections=["Lack of foundation", "Irrelevant comparisons", "Unreliable data sources"],
                customization_tips="Ensure comparisons are truly comparable. Address limitations and assumptions in benchmarking data."
            ),
            ExampleExhibit(
                exhibit_number="P-29",
                description="Mitigation Efforts Documentation",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Plaintiff's business records and third-party agreements",
                relevance="Shows reasonable efforts to minimize damages from defendant's breach",
                foundation_requirements=["Business records", "Third-party confirmations", "Cost documentation"],
                potential_objections=["Failure to mitigate", "Unreasonable mitigation costs", "Lack of causation"],
                customization_tips="Document all reasonable alternatives considered. Show cost-benefit analysis of mitigation decisions."
            ),
            ExampleExhibit(
                exhibit_number="P-30",
                description="Lost Opportunity Documentation and Analysis",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Business development records and client communications",
                relevance="Demonstrates specific business opportunities lost due to defendant's breach",
                foundation_requirements=["Business records", "Third-party confirmations", "Causation evidence"],
                potential_objections=["Speculative damages", "Lack of causation", "Failure to prove lost profits"],
                customization_tips="Focus on specific, identifiable opportunities rather than general market speculation. Include probability analysis."
            )
        ]
        
        jury_instructions = [
            ExampleJuryInstruction(
                instruction_id="CD-1",
                title="Contract Formation and Validity",
                category="Contract Law",
                instruction_text="""A contract is formed when there is: (1) an offer, (2) acceptance of that offer, (3) consideration (something of value exchanged by both parties), and (4) mutual assent to the essential terms. The parties must have intended to create a legally binding agreement.""",
                applicable_law="State contract law and Uniform Commercial Code if applicable",
                customization_notes="Modify for specific contract types. Add UCC provisions for goods sales. Include statute of frauds if writing requirement applies."
            ),
            ExampleJuryInstruction(
                instruction_id="CD-2",
                title="Material Breach of Contract",
                category="Breach",
                instruction_text="""A material breach is a failure to perform a contractual duty that is so significant it defeats the purpose of the contract. In determining whether a breach is material, consider: (1) the extent to which the injured party will be deprived of the benefit reasonably expected, (2) whether the injured party can be adequately compensated for damages, (3) the extent of partial performance, and (4) the likelihood that the breaching party will cure the breach.""",
                applicable_law="State contract law regarding material breach standards",
                customization_notes="Adapt for specific performance obligations. Include time is of the essence provisions if applicable to contract."
            ),
            ExampleJuryInstruction(
                instruction_id="CD-3",
                title="Contract Damages - Expectation Damages",
                category="Damages", 
                instruction_text="""If you find that defendant breached the contract, plaintiff is entitled to damages that would put plaintiff in the same position as if the contract had been properly performed. These damages must be: (1) reasonably certain, (2) foreseeable at the time of contract formation, and (3) unavoidable despite reasonable efforts to mitigate.""",
                applicable_law="State contract damages law and UCC if applicable",
                customization_notes="Add specific language for consequential damages, lost profits, or incidental damages based on case facts."
            ),
            ExampleJuryInstruction(
                instruction_id="CD-4", 
                title="Lost Profits as Contract Damages",
                category="Damages",
                instruction_text="""Lost profits may be recovered if they were: (1) reasonably foreseeable when the contract was made, (2) reasonably certain in amount, and (3) not speculative. The plaintiff must prove lost profits with reasonable certainty, but exactness is not required.""",
                applicable_law="State law regarding lost profit recovery in contract cases",
                customization_notes="Include new business rule limitations if plaintiff is startup. Address established vs. new business profit standards."
            ),
            ExampleJuryInstruction(
                instruction_id="CD-5",
                title="Duty to Mitigate Damages",
                category="Defenses",
                instruction_text="""A party claiming contract damages has a duty to make reasonable efforts to minimize or avoid those damages. If plaintiff failed to make reasonable efforts to mitigate damages, the damages award should be reduced by the amount that could have been reasonably avoided.""",
                applicable_law="State mitigation of damages doctrine",
                customization_notes="Define reasonableness standard based on industry practices and specific contract circumstances."
            ),
            ExampleJuryInstruction(
                instruction_id="CD-6",
                title="Contract Interpretation",
                category="Contract Law",
                instruction_text="""When interpreting a contract, give words their ordinary meaning unless the parties clearly intended a special meaning. Consider the entire contract, not just isolated provisions. If the contract is ambiguous, you may consider the parties' conduct and communications to determine their intent.""",
                applicable_law="State contract interpretation principles",
                customization_notes="Add parole evidence rule limitations. Include course of dealing and usage of trade if relevant."
            )
        ]
        
        trial_schedule = [
            TrialDay(
                day_number=1,
                date=None,
                theme="Contract Foundation - Establishing the Agreement and Its Terms",
                objectives=[
                    "Prove formation of valid enforceable contract",
                    "Establish plaintiff's complete performance or excuse for non-performance", 
                    "Introduce key contract terms and expectations",
                    "Set foundation for breach and damages claims"
                ],
                witnesses=["Michael Rodriguez (Plaintiff CEO) - Part 1"],
                exhibits=["P-1 (Software Development Agreement)", "P-2 through P-10 (Early contract communications)"],
                time_blocks={
                    "9:00 AM - 10:30 AM": "Opening Statements (plaintiff 25 min, defense 20 min)",
                    "10:45 AM - 12:00 PM": "Plaintiff CEO - contract formation and terms",
                    "1:30 PM - 3:30 PM": "Plaintiff CEO - performance and early relationship",
                    "3:45 PM - 4:30 PM": "Contract and early communications exhibits"
                },
                preparation_tasks=[
                    "Final contract interpretation review with client",
                    "Prepare clear contract explanation for jury",
                    "Review contract formation elements and evidence",
                    "Organize exhibits chronologically for smooth presentation"
                ],
                contingency_plans=[
                    "If contract interpretation disputed, have parole evidence ready",
                    "If formation challenged, prepare additional formation evidence",
                    "If CEO unavailable, substitute other contract signatory"
                ],
                customization_notes="For complex contracts, use visual aids to explain key terms. For standard form contracts, address any unconscionability arguments."
            ),
            TrialDay(
                day_number=2,
                date=None,
                theme="Performance and Problems - Showing Plaintiff's Performance and Defendant's Failures",
                objectives=[
                    "Complete plaintiff CEO testimony on performance",
                    "Document specific instances of defendant's breach",
                    "Show attempts to resolve performance issues",
                    "Establish timeline and severity of breaches"
                ],
                witnesses=["Michael Rodriguez (continued)", "Jennifer Walsh (Project Manager)"],
                exhibits=["P-11 through P-20 (Performance communications)", "P-26 (Work product analysis)"],
                time_blocks={
                    "9:00 AM - 10:30 AM": "Complete CEO direct - breach instances and damages",
                    "10:45 AM - 12:30 PM": "Defense cross-examination of CEO",
                    "1:30 PM - 2:30 PM": "CEO redirect and Project Manager direct",
                    "2:45 PM - 4:30 PM": "Project Manager - detailed performance issues"
                },
                preparation_tasks=[
                    "Intensive CEO cross-examination preparation",
                    "Prepare project manager for technical testimony",
                    "Review performance documentation chronologically",
                    "Prepare redirect themes to rehabilitate any damage from cross"
                ],
                contingency_plans=[
                    "If CEO damaged on cross, use project manager to rehabilitate",
                    "If performance issues minimized, emphasize material impact",
                    "If work product analysis challenged, have technical expert ready"
                ],
                customization_notes="For service contracts, focus on service level failures. For manufacturing contracts, emphasize quality control issues and specifications."
            ),
            TrialDay(
                day_number=3,
                date=None,  
                theme="Industry Standards and Technical Analysis",
                objectives=[
                    "Establish industry performance standards",
                    "Show defendant's performance fell below acceptable standards",
                    "Provide technical analysis of work product deficiencies",
                    "Support damages claims with industry context"
                ],
                witnesses=["David Chen (Industry Expert)", "Technical witnesses as needed"],
                exhibits=["P-28 (Industry benchmarking)", "P-26 (Work product analysis)", "Technical comparison exhibits"],
                time_blocks={
                    "9:00 AM - 11:00 AM": "Industry expert - standards and defendant's performance",
                    "11:15 AM - 12:00 PM": "Industry expert cross-examination",
                    "1:30 PM - 2:30 PM": "Technical analysis of work product and deliverables",
                    "2:45 PM - 4:30 PM": "Industry benchmarking and comparative exhibits"
                },
                preparation_tasks=[
                    "Prepare industry expert for Daubert challenges",
                    "Review technical analysis for accuracy and clarity",
                    "Prepare simple explanations of technical concepts",
                    "Organize benchmarking data for clear presentation"
                ],
                contingency_plans=[
                    "If industry expert excluded, rely on fact witness technical testimony",
                    "If benchmarking challenged, have alternative comparison methods",
                    "If technical analysis disputed, emphasize contract specification failures"
                ],
                customization_notes="Adapt technical complexity to jury sophistication. For construction contracts, use visual demonstrations. For professional services, focus on standard practices."
            ),
            TrialDay(
                day_number=4,
                date=None,
                theme="Damages and Financial Impact",
                objectives=[
                    "Prove specific damages with reasonable certainty",
                    "Show causation between breach and damages",
                    "Demonstrate mitigation efforts and reasonableness",
                    "Establish total damages amount with supporting calculations"
                ],
                witnesses=["Sarah Kim, CPA (Damages Expert)", "Amanda Foster (Client Impact)"],
                exhibits=["P-27 (Damages calculations)", "P-29 (Mitigation efforts)", "P-30 (Lost opportunities)"],
                time_blocks={
                    "9:00 AM - 11:30 AM": "CPA expert - damages methodology and calculations",
                    "11:45 AM - 12:30 PM": "CPA expert cross-examination",
                    "1:30 PM - 2:15 PM": "Client impact witness - third-party effects",
                    "2:30 PM - 4:30 PM": "Damages exhibits and mitigation evidence"
                },
                preparation_tasks=[
                    "Prepare damages expert for methodology challenges",
                    "Review all damage calculations for accuracy",
                    "Organize mitigation evidence chronologically",
                    "Prepare alternative damages theories if primary challenged"
                ],
                contingency_plans=[
                    "If lost profits excluded, focus on out-of-pocket damages",
                    "If damages expert attacked, have supporting business records",
                    "If mitigation challenged, show reasonableness of efforts"
                ],
                customization_notes="For speculative damages, emphasize certainty of calculation method. For new businesses, address established business vs. startup standards."
            ),
            TrialDay(
                day_number=5,
                date=None,
                theme="Closing Arguments and Final Resolution",
                objectives=[
                    "Address any remaining evidentiary gaps",
                    "Respond to defense case through rebuttal if needed",
                    "Deliver compelling closing argument summarizing proof",
                    "Request specific damages amount with clear justification"
                ],
                witnesses=["Rebuttal witnesses as needed"],
                exhibits=["Summary exhibits", "Damages timeline", "Contract performance comparison"],
                time_blocks={
                    "9:00 AM - 10:30 AM": "Final evidence and rebuttal witnesses",
                    "10:45 AM - 12:00 PM": "Defense case presentation (if any)",
                    "1:30 PM - 2:30 PM": "Plaintiff closing argument",
                    "2:30 PM - 3:30 PM": "Defense closing argument",
                    "3:45 PM - 4:00 PM": "Plaintiff rebuttal argument"
                ],
                preparation_tasks=[
                    "Prepare comprehensive closing argument with visual aids",
                    "Calculate final damages request with all supporting evidence",
                    "Prepare rebuttal argument anticipating defense themes",
                    "Review jury instructions for favorable language"
                ],
                contingency_plans=[
                    "If defense presents surprise evidence, request rebuttal time",
                    "If damages amount challenged in closing, have alternative calculations",
                    "If jury instructions disputed, have supporting case authority"
                ],
                customization_notes="Tailor closing to contract complexity and jury sophistication. Emphasize fairness and holding parties accountable to their agreements."
            )
        ]
        
        return ExampleTrialNotebook(
            case_type=CaseType.CONTRACT_DISPUTE,
            case_title="TechStart Solutions v. DevCorp Industries - Software Development Agreement Breach",
            case_overview="""
            Plaintiff TechStart Solutions contracted with defendant DevCorp Industries for 
            custom software development services. Defendant materially breached the agreement 
            through delayed delivery, substandard work product, and failure to meet 
            contractual specifications, resulting in significant damages to plaintiff.
            """,
            theory_of_case="Defendant accepted contractual obligations, received payment, but failed to perform as promised, causing foreseeable damages that must be compensated to make plaintiff whole.",
            key_themes=[
                "A deal is a deal - contracts must be honored",
                "Broken promises have real consequences for businesses",
                "Professional standards matter in business relationships", 
                "Accountability promotes trust in commercial relationships",
                "Fair compensation restores the benefit of the bargain"
            ],
            witnesses=witnesses,
            exhibits=exhibits,
            jury_instructions=jury_instructions,
            trial_schedule=trial_schedule,
            opening_statement_outline="""
            1. Start with universal truth: 'When you make a promise, you keep it'
            2. Introduce parties and their business relationship
            3. Describe the contract and its importance to plaintiff
            4. Explain defendant's promises and plaintiff's reliance
            5. Detail defendant's breaches and their impact
            6. Preview evidence proving breach and damages
            7. Explain what the law requires for fair resolution
            8. Promise to prove every element with credible evidence
            """,
            closing_argument_outline="""
            1. Remind jury of their role in enforcing contracts
            2. Review undisputed evidence of contract formation
            3. Walk through each material breach with specific evidence
            4. Address defense justifications with factual responses
            5. Explain damages calculation with expert analysis
            6. Show mitigation efforts and reasonableness
            7. Request specific damages with supporting evidence
            8. Call for verdict that enforces contractual accountability
            """,
            general_customization_guide="""
            CONTRACT DISPUTE CUSTOMIZATION GUIDE:
            
            1. CONTRACT TYPE ADAPTATIONS:
               - Service Agreements: Focus on performance standards and deliverable quality
               - Sales Contracts: Emphasize conformity, warranty, and UCC provisions
               - Construction Contracts: Include change orders, progress payments, substantial completion
               - Employment Contracts: Address termination procedures, non-compete issues, severance
               - Licensing Agreements: Focus on usage rights, royalty calculations, compliance
            
            2. BREACH TYPE MODIFICATIONS:
               - Total Breach: Emphasize complete failure to perform, justify damages
               - Partial Breach: Show material impact despite partial performance
               - Anticipatory Breach: Document repudiation, mitigation efforts, cover purchases
               - Delay Breach: Time is of essence provisions, consequential damages
            
            3. PLAINTIFF CHARACTERISTICS:
               - Established Business: Historical performance, lost profit patterns
               - Startup/New Business: Limited profit history, use different damages theories
               - Individual Plaintiffs: Personal impact, simplified damages calculations
               - Corporate Plaintiffs: Business impact, shareholder effects, operational disruption
            
            4. DEFENDANT CONSIDERATIONS:
               - Individual Defendants: Personal liability, asset availability
               - Corporate Defendants: Insurance coverage, successor liability, alter ego
               - Government Contracts: Sovereign immunity, administrative procedures
               - International Parties: Choice of law, enforcement challenges
            
            5. COMPLEXITY ADJUSTMENTS:
               - Simple Contracts: Focus on basic formation and breach elements
               - Complex Contracts: Visual aids, expert interpretation, industry context
               - Technical Contracts: Industry experts, simplified explanations, demonstratives
               - Multi-party Contracts: Joint obligations, contribution, indemnification
            
            6. REMEDIES CONSIDERATIONS:
               - Monetary Damages: Lost profits, consequential, incidental, cover damages
               - Specific Performance: Unique property, inadequate legal remedy, feasibility
               - Rescission: Fraud, mistake, unconscionability, restitution
               - Reformation: Mutual mistake, scrivener's error, clear evidence of intent
            
            7. DEFENSES TO ADDRESS:
               - Statute of Frauds: Writing requirements, partial performance exceptions
               - Unconscionability: Procedural and substantive unconscionability elements
               - Impossibility/Impracticability: Unforeseen circumstances, risk allocation
               - Frustration of Purpose: Changed circumstances, basis of contract destroyed
               - Duress/Undue Influence: Improper pressure, lack of reasonable alternatives
            
            8. EVIDENCE STRATEGIES:
               - Document Heavy Cases: Organization, authentication, demonstratives
               - Oral Contract Cases: Corroboration, course of dealing, part performance
               - Industry Custom: Expert testimony, trade usage, course of dealing
               - Damages Proof: Business records, expert analysis, mitigation evidence
            """
        )
    
    def _create_criminal_defense_example(self) -> ExampleTrialNotebook:
        """Create comprehensive criminal defense trial notebook example."""
        
        witnesses = [
            ExampleWitness(
                name="Detective Maria Gonzalez",
                witness_type=WitnessType.FACT,
                role="Lead Investigating Officer", 
                key_testimony=[
                    "Initial investigation and evidence collection",
                    "Interview process and Miranda rights administration",
                    "Chain of custody for physical evidence",
                    "Coordination with other agencies and experts",
                    "Report writing and documentation procedures"
                ],
                estimated_time="1.5-2 hours",
                preparation_notes="Challenge inconsistencies in police report. Focus on procedural violations and constitutional issues. Prepare for cross on bias and tunnel vision.",
                potential_objections=["Hearsay statements", "Opinion testimony", "Lack of foundation for conclusions"],
                customization_tips="For drug cases, focus on search and seizure issues. For violent crimes, challenge forensic evidence handling. For white collar, examine financial investigation methods."
            ),
            ExampleWitness(
                name="Sarah Johnson",
                witness_type=WitnessType.FACT,
                role="Prosecution Eyewitness",
                key_testimony=[
                    "Observation of alleged criminal activity",
                    "Identification of defendant at scene",
                    "Description of events as they unfolded",
                    "Lighting conditions and distance factors",
                    "Communications with law enforcement"
                ],
                estimated_time="1 hour",
                preparation_notes="Cross-examine on identification reliability. Address lighting, distance, stress factors. Challenge consistency with prior statements.",
                potential_objections=["Leading questions", "Speculation", "Improper opinion testimony"],
                customization_tips="For identification cases, focus on cross-racial identification issues. For domestic violence, address bias and motive to fabricate."
            ),
            ExampleWitness(
                name="Dr. Robert Mitchell",
                witness_type=WitnessType.EXPERT,
                role="Forensic Science Expert - Defense",
                key_testimony=[
                    "Analysis of prosecution's forensic evidence",
                    "Alternative explanations for physical evidence",
                    "Critique of forensic methodology and conclusions",
                    "Chain of custody issues and contamination possibilities",
                    "Statistical significance and interpretation errors"
                ],
                estimated_time="2-2.5 hours",
                preparation_notes="Prepare detailed critique of prosecution forensics. Focus on methodology flaws and alternative explanations. Use visual aids for complex scientific concepts.",
                potential_objections=["Lack of foundation", "Unreliable methodology", "Exceeding scope of expertise"],
                customization_tips="For DNA cases, focus on mixture interpretation and statistical errors. For ballistics, challenge matching methodology. For digital evidence, address forensic imaging issues."
            ),
            ExampleWitness(
                name="James Wilson (Defendant)",
                witness_type=WitnessType.DEFENDANT,
                role="Defendant - Testifying in Own Defense",
                key_testimony=[
                    "Account of events from defendant's perspective",
                    "Explanation of defendant's actions and intent",
                    "Response to prosecution's evidence and allegations",
                    "Character evidence and background information",
                    "Relationship to other witnesses and parties"
                ],
                estimated_time="2-3 hours",
                preparation_notes="Extensive preparation for direct and cross-examination. Practice staying calm under pressure. Address all major prosecution evidence points.",
                potential_objections=["Self-serving statements", "Prior bad acts", "Hearsay"],
                customization_tips="Consider carefully whether defendant should testify. For self-defense cases, necessary to explain reasonableness. For complex fraud, may need defendant to explain intent."
            ),
            ExampleWitness(
                name="Dr. Amanda Foster",
                witness_type=WitnessType.EXPERT,
                role="Mental Health Expert - Defense",
                key_testimony=[
                    "Defendant's mental health evaluation and diagnosis",
                    "Impact of mental illness on behavior and decision-making",
                    "Relationship between mental state and alleged crimes",
                    "Treatment history and medication compliance",
                    "Opinion on competency and criminal responsibility"
                ],
                estimated_time="1.5-2 hours",
                preparation_notes="Review complete mental health history. Prepare for challenges on reliability of diagnosis. Address any malingering concerns.",
                potential_objections=["Reliability of mental health diagnosis", "Lack of foundation", "Ultimate issue testimony"],
                customization_tips="For insanity defense, focus on legal standards. For diminished capacity, address specific intent elements. For competency, current mental state assessment."
            ),
            ExampleWitness(
                name="Michael Thompson",
                witness_type=WitnessType.CHARACTER,
                role="Character Witness - Defendant's Employer",
                key_testimony=[
                    "Defendant's character for honesty and integrity",
                    "Work performance and reliability",
                    "Reputation in the community",
                    "Specific instances of good character (if door opened)",
                    "Opinion on defendant's likelihood to commit alleged crime"
                ],
                estimated_time="30-45 minutes",
                preparation_notes="Prepare for prosecution cross on knowledge of defendant's bad acts. Focus on specific character traits relevant to charged crimes.",
                potential_objections=["Relevance to character trait", "Lack of foundation", "Improper character evidence"],
                customization_tips="Match character evidence to elements of crime. For theft charges, honesty character. For violence charges, peaceful character. Limit number to avoid repetition."
            )
        ]
        
        exhibits = [
            ExampleExhibit(
                exhibit_number="D-1",
                description="Police Report with Supplemental Reports",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Police Department Records",
                relevance="Shows inconsistencies in investigation and evidence of bias",
                foundation_requirements=["Business records exception", "Chain of custody", "Authentication by records custodian"],
                potential_objections=["Hearsay", "Conclusions and opinions", "Prejudicial content"],
                customization_tips="Highlight inconsistencies between initial and supplemental reports. For drug cases, focus on search warrant affidavit problems."
            ),
            ExampleExhibit(
                exhibit_number="D-2 through D-8",
                description="Crime Scene Photographs",
                exhibit_type=ExhibitType.PHOTO,
                source="Police Crime Scene Unit",
                relevance="Shows physical evidence supports defense theory rather than prosecution",
                foundation_requirements=["Authentication by photographer", "Accurate representation", "Relevance over prejudice"],
                potential_objections=["Prejudicial impact", "Cumulative evidence", "Lack of foundation"],
                customization_tips="Use photos to support defense theory. For self-defense, show victim's size or weapon accessibility. For alibi, show timeline impossibility."
            ),
            ExampleExhibit(
                exhibit_number="D-9",
                description="Surveillance Video from Nearby Business",
                exhibit_type=ExhibitType.VIDEO,
                source="Business security system",
                relevance="Contradicts prosecution witness testimony about defendant's actions",
                foundation_requirements=["Chain of custody", "Authentication of system", "Accuracy of date/time"],
                potential_objections=["Authentication", "Best evidence rule", "Chain of custody"],
                customization_tips="Focus on timestamp accuracy and video quality. For identification cases, highlight poor lighting or distance factors."
            ),
            ExampleExhibit(
                exhibit_number="D-10",
                description="Cell Phone Location Data and Records",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Cellular service provider records",
                relevance="Establishes defendant's location contradicting prosecution timeline",
                foundation_requirements=["Business records", "Chain of custody", "Technical foundation for location accuracy"],
                potential_objections=["Hearsay", "Lack of foundation", "Privacy concerns"],
                customization_tips="Prepare technical witness for location accuracy testimony. Address any gaps in coverage or data."
            ),
            ExampleExhibit(
                exhibit_number="D-11",
                description="Independent Forensic Analysis Report",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Defense forensic expert",
                relevance="Contradicts prosecution forensic conclusions with alternative analysis",
                foundation_requirements=["Expert qualification", "Reliable methodology", "Proper foundation"],
                potential_objections=["Reliability under Daubert", "Lack of foundation", "Bias due to defense retention"],
                customization_tips="Focus on methodology differences rather than attacking prosecution expert personally. Use visual aids for complex analysis."
            ),
            ExampleExhibit(
                exhibit_number="D-12",
                description="Medical Records and Mental Health Treatment History",
                exhibit_type=ExhibitType.MEDICAL_RECORD,
                source="Various medical providers",
                relevance="Shows defendant's mental health condition affecting ability to form intent",
                foundation_requirements=["Medical records exception", "Chain of custody", "Relevance to mental state"],
                potential_objections=["Hearsay", "Privacy violation", "Prejudicial content"],
                customization_tips="Organize chronologically to show progression of mental health issues. Redact irrelevant or prejudicial information."
            ),
            ExampleExhibit(
                exhibit_number="D-13",
                description="Character Reference Letters and Employment Records",
                exhibit_type=ExhibitType.DOCUMENT,
                source="Community members and employers",
                relevance="Shows defendant's character inconsistent with charged crimes",
                foundation_requirements=["Authentication by authors", "Personal knowledge", "Relevant character traits"],
                potential_objections=["Relevance", "Hearsay", "Cumulative evidence"],
                customization_tips="Match character evidence to specific elements of charged crimes. Quality over quantity in character witnesses."
            )
        ]
        
        jury_instructions = [
            ExampleJuryInstruction(
                instruction_id="CR-1",
                title="Burden of Proof - Beyond a Reasonable Doubt",
                category="Burden of Proof",
                instruction_text="""The prosecution has the burden to prove the defendant guilty beyond a reasonable doubt. This means the evidence must be so convincing that a reasonable person would not hesitate to rely and act upon it. Proof beyond a reasonable doubt is proof that leaves you firmly convinced of the defendant's guilt. If you are not firmly convinced, you must find the defendant not guilty.""",
                applicable_law="Constitutional due process requirements and state criminal law",
                customization_notes="Emphasize high burden standard. Some jurisdictions prohibit quantifying reasonable doubt as percentage."
            ),
            ExampleJuryInstruction(
                instruction_id="CR-2",
                title="Presumption of Innocence",
                category="Defendant's Rights", 
                instruction_text="""The defendant is presumed innocent. This presumption continues throughout the trial and is not overcome unless you are convinced beyond a reasonable doubt that the defendant is guilty. The defendant has no obligation to prove innocence or present any evidence.""",
                applicable_law="Constitutional presumption of innocence",
                customization_notes="Reinforce that defendant need not testify or present evidence. Address any negative inferences from defendant's silence."
            ),
            ExampleJuryInstruction(
                instruction_id="CR-3",
                title="Elements of the Crime - [Specific Charge]",
                category="Elements",
                instruction_text="""To find the defendant guilty of [specific crime], the prosecution must prove beyond a reasonable doubt: 
                1. [Element 1 - specific to crime]
                2. [Element 2 - specific to crime] 
                3. [Element 3 - specific to crime]
                If you find that the prosecution has failed to prove any of these elements beyond a reasonable doubt, you must find the defendant not guilty.""",
                applicable_law="State criminal statute defining specific offense",
                customization_notes="Customize for specific charged crimes. Include lesser included offense instructions if applicable. Address any specific intent requirements."
            ),
            ExampleJuryInstruction(
                instruction_id="CR-4",
                title="Eyewitness Identification",
                category="Evidence Evaluation",
                instruction_text="""In evaluating eyewitness identification testimony, you should consider: the witness's opportunity to observe; the length of observation; lighting conditions; distance; whether the witness was under stress; any physical impairments; prior familiarity with the defendant; any inconsistencies in descriptions; and the time between the event and identification.""",
                applicable_law="State law regarding eyewitness identification reliability",
                customization_notes="Adapt factors to case-specific identification issues. Include cross-racial identification concerns if applicable."
            ),
            ExampleJuryInstruction(
                instruction_id="CR-5",
                title="Expert Testimony",
                category="Evidence Evaluation",
                instruction_text="""You have heard testimony from expert witnesses. You should consider the expert's qualifications, the facts or data the expert relied upon, and whether the expert's opinion is reasonable. You are not required to accept an expert's opinion simply because the person is an expert.""",
                applicable_law="State and federal evidence rules regarding expert testimony",
                customization_notes="Address any competing expert opinions. Include instructions about limitations of forensic evidence if applicable."
            ),
            ExampleJuryInstruction(
                instruction_id="CR-6", 
                title="Mental State/Intent",
                category="Mental State",
                instruction_text="""Intent may be proven by the defendant's acts, conduct, and words, and by all the facts and circumstances in evidence. You may consider whether the defendant's acts were done deliberately and with knowledge of their probable consequences.""",
                applicable_law="State law regarding proof of criminal intent",
                customization_notes="Modify based on specific intent vs. general intent crimes. Include diminished capacity instructions if mental health evidence presented."
            ),
            ExampleJuryInstruction(
                instruction_id="CR-7",
                title="Character Evidence",
                category="Character Evidence", 
                instruction_text="""Evidence of the defendant's good character may be sufficient to raise a reasonable doubt about guilt, even if you might otherwise be convinced of guilt. You should consider character evidence along with all other evidence in deciding whether the prosecution has proved guilt beyond a reasonable doubt.""",
                applicable_law="Federal Rule 404(a) and state equivalents regarding character evidence",
                customization_notes="Include only if character evidence presented. Specify which character traits are relevant to charged crimes."
            )
        ]
        
        trial_schedule = [
            TrialDay(
                day_number=1,
                date=None,
                theme="Opening and Prosecution Case - Setting Defense Theory Early",
                objectives=[
                    "Establish defense theory and reasonable doubt themes in opening",
                    "Begin cross-examination strategy to undermine prosecution case",
                    "Identify weaknesses in prosecution's first witnesses",
                    "Preserve constitutional objections and create appellate record"
                ],
                witnesses=["Detective Maria Gonzalez", "Crime Scene Technician"],
                exhibits=["D-1 (Police Report inconsistencies)", "D-2 through D-8 (Scene photos supporting defense theory)"],
                time_blocks={
                    "9:00 AM - 9:30 AM": "Defense opening statement - reasonable doubt theme",
                    "9:30 AM - 10:45 AM": "Prosecution opening and first witness",
                    "11:00 AM - 12:00 PM": "Cross-examination of detective - focus on procedural issues",
                    "1:30 PM - 3:00 PM": "Crime scene technician testimony and cross",
                    "3:15 PM - 4:30 PM": "Begin prosecution's key witness testimony"
                ],
                preparation_tasks=[
                    "Final opening statement rehearsal emphasizing reasonable doubt",
                    "Prepare aggressive but professional cross-examinations",
                    "Review all police reports for inconsistencies and procedural violations",
                    "Organize constitutional objections and preserve record for appeal"
                ],
                contingency_plans=[
                    "If detective testimony stronger than expected, emphasize procedural violations",
                    "If physical evidence more damaging, focus on chain of custody issues",
                    "If witness unavailable, use prior testimony or depositions"
                ],
                customization_notes="For drug cases, focus on Fourth Amendment issues. For violent crimes, emphasize self-defense early. For white collar, attack government investigation methods."
            ),
            TrialDay(
                day_number=2,
                date=None,
                theme="Challenging Prosecution Witnesses - Credibility and Reliability",
                objectives=[
                    "Systematically undermine prosecution witnesses through cross-examination",
                    "Highlight inconsistencies in witness statements and testimony",
                    "Introduce evidence contradicting prosecution timeline",
                    "Establish foundation for defense case and reasonable doubt"
                ],
                witnesses=["Sarah Johnson (Eyewitness)", "Additional prosecution witnesses"],
                exhibits=["D-9 (Surveillance video contradicting witness)", "D-10 (Cell phone location data)"],
                time_blocks={
                    "9:00 AM - 10:30 AM": "Complete previous witness and begin eyewitness testimony",
                    "10:45 AM - 12:00 PM": "Aggressive cross-examination of eyewitness - identification issues",
                    "1:30 PM - 2:30 PM": "Introduce surveillance video contradicting witness testimony",
                    "2:45 PM - 4:30 PM": "Cell phone location evidence supporting defense timeline"
                },
                preparation_tasks=[
                    "Prepare detailed cross-examination outline for identification witness",
                    "Review surveillance video frame by frame for defense points",
                    "Prepare technical foundation for cell phone location evidence",
                    "Identify all inconsistencies in prosecution witness statements"
                ],
                contingency_plans=[
                    "If eyewitness identification holds up, emphasize poor viewing conditions",
                    "If surveillance video excluded, use still photos and witness testimony",
                    "If location data challenged, have backup alibi witnesses ready"
                ],
                customization_notes="For identification cases, use lineup procedures and suggestive identification techniques. For domestic violence, address victim recantation sensitively."
            ),
            TrialDay(
                day_number=3,
                date=None,
                theme="Forensic Evidence Defense - Challenging Scientific Proof",
                objectives=[
                    "Present defense forensic expert to counter prosecution science",
                    "Highlight methodology problems and alternative explanations",
                    "Address chain of custody and contamination issues",
                    "Simplify complex scientific concepts for jury understanding"
                ],
                witnesses=["Dr. Robert Mitchell (Defense Forensic Expert)", "Chain of custody witnesses"],
                exhibits=["D-11 (Independent forensic analysis)", "Chain of custody documentation"],
                time_blocks={
                    "9:00 AM - 11:30 AM": "Defense forensic expert direct examination - methodology critique",
                    "11:45 AM - 12:30 PM": "Prosecution cross of defense expert",
                    "1:30 PM - 2:30 PM": "Defense expert redirect - address prosecution challenges",
                    "2:45 PM - 4:30 PM": "Chain of custody evidence and contamination possibilities"
                },
                preparation_tasks=[
                    "Extensive preparation of forensic expert for cross-examination",
                    "Prepare visual aids explaining complex scientific concepts",
                    "Review chain of custody documentation for gaps or irregularities",
                    "Practice simplified explanations of technical concepts"
                ],
                contingency_plans=[
                    "If forensic expert excluded under Daubert, use lay witness observations",
                    "If methodology critique fails, emphasize statistical interpretation errors",
                    "If chain of custody solid, focus on contamination possibilities"
                ],
                customization_tips="For DNA cases, focus on mixture interpretation and degraded samples. For ballistics, challenge bullet matching reliability. For digital evidence, address forensic imaging protocols."
            ),
            TrialDay(
                day_number=4,
                date=None,
                theme="Mental Health and Character Defense",
                objectives=[
                    "Present evidence of defendant's mental health issues affecting intent",
                    "Introduce positive character evidence to contradict prosecution theory",
                    "Establish mitigation evidence for potential sentencing",
                    "Prepare foundation for defendant's potential testimony"
                ],
                witnesses=["Dr. Amanda Foster (Mental Health Expert)", "Michael Thompson (Character Witness)"],
                exhibits=["D-12 (Medical and mental health records)", "D-13 (Character references)"],
                time_blocks={
                    "9:00 AM - 11:00 AM": "Mental health expert - diagnosis and impact on behavior",
                    "11:15 AM - 12:00 PM": "Prosecution cross of mental health expert",
                    "1:30 PM - 2:15 PM": "Character witness testimony - reputation and opinion",
                    "2:30 PM - 4:30 PM": "Additional character evidence and community support"
                },
                preparation_tasks=[
                    "Prepare mental health expert for malingering accusations",
                    "Review character witnesses for potential prosecution impeachment",
                    "Organize medical records chronologically to show mental health progression",
                    "Prepare character witnesses for cross-examination on knowledge of bad acts"
                ],
                contingency_plans=[
                    "If mental health expert attacked successfully, rely on medical records",
                    "If character witnesses impeached, emphasize lack of knowledge vs. bad character",
                    "If medical records excluded, use family testimony about behavioral changes"
                ],
                customization_notes="For insanity defense, focus on legal standard and timing of mental illness. For diminished capacity, address specific intent requirements of charged crimes."
            ),
            TrialDay(
                day_number=5,
                date=None,
                theme="Defendant's Testimony and Closing Arguments",
                objectives=[
                    "Present defendant's testimony if strategically advisable",
                    "Address prosecution case comprehensively in closing argument",
                    "Reinforce reasonable doubt standard and burden of proof",
                    "Request specific verdict and provide clear path to acquittal"
                ],
                witnesses=["James Wilson (Defendant) - if testifying"],
                exhibits=["Summary exhibits and timeline", "Reasonable doubt demonstratives"],
                time_blocks={
                    "9:00 AM - 11:30 AM": "Defendant testimony (if testifying) - direct examination",
                    "11:45 AM - 12:30 PM": "Prosecution cross-examination of defendant",
                    "1:30 PM - 2:00 PM": "Defendant redirect and close of evidence",
                    "2:15 PM - 3:15 PM": "Prosecution closing argument",
                    "3:30 PM - 4:30 PM": "Defense closing argument - reasonable doubt focus"
                ],
                preparation_tasks=[
                    "Make final decision on defendant testimony with extensive preparation",
                    "Prepare comprehensive closing argument addressing all prosecution evidence",
                    "Create visual aids emphasizing reasonable doubt and burden of proof",
                    "Review jury instructions and argue for favorable language"
                ],
                contingency_plans=[
                    "If defendant performs poorly, minimize damage in closing argument",
                    "If prosecution closing especially strong, request additional rebuttal time",
                    "If jury instructions unfavorable, preserve objections for appeal"
                ],
                customization_notes="Consider defendant testimony carefully - often unnecessary if reasonable doubt established. Focus closing on strongest defense arguments and prosecution weaknesses."
            )
        ]
        
        return ExampleTrialNotebook(
            case_type=CaseType.CRIMINAL_DEFENSE,
            case_title="State v. Wilson - Aggravated Assault and Weapons Charges",
            case_overview="""
            Defendant James Wilson is charged with aggravated assault and weapons violations 
            arising from an alleged altercation outside a local bar. The defense challenges 
            the prosecution's case through eyewitness credibility issues, forensic evidence 
            problems, and self-defense claims. This notebook provides comprehensive criminal 
            defense trial preparation adaptable to various criminal charges.
            """,
            theory_of_case="The prosecution has failed to prove guilt beyond a reasonable doubt due to unreliable witness identification, flawed forensic evidence, and the defendant's reasonable belief that force was necessary for self-defense.",
            key_themes=[
                "Innocent until proven guilty - prosecution hasn't met their burden",
                "Reasonable doubt exists throughout the prosecution's case",
                "Self-defense is not a crime - protecting yourself is a right",
                "Police rushed to judgment without thorough investigation",
                "Eyewitness testimony is unreliable and contradicted by physical evidence"
            ],
            witnesses=witnesses,
            exhibits=exhibits,
            jury_instructions=jury_instructions,
            trial_schedule=trial_schedule,
            opening_statement_outline="""
            1. Remind jury of presumption of innocence and burden of proof
            2. Introduce defendant as real person with constitutional rights
            3. Outline the prosecution's burden and what they must prove
            4. Preview major weaknesses in prosecution case
            5. Explain self-defense law and defendant's right to protect himself
            6. Promise to show reasonable doubt exists throughout case
            7. Ask jury to hold prosecution to their burden of proof
            8. End with request to keep open mind and follow the law
            """,
            closing_argument_outline="""
            1. Remind jury of their sworn duty to follow burden of proof
            2. Review each element prosecution must prove beyond reasonable doubt
            3. Systematically address weaknesses in prosecution evidence
            4. Highlight inconsistencies and contradictions in witness testimony
            5. Explain how physical evidence supports defense theory
            6. Address self-defense law and defendant's reasonable actions
            7. Emphasize that doubt is reasonable throughout prosecution case
            8. Request not guilty verdict based on failure to meet burden of proof
            """,
            general_customization_guide="""
            CRIMINAL DEFENSE CUSTOMIZATION GUIDE:
            
            1. CRIME TYPE ADAPTATIONS:
               - Violent Crimes: Self-defense, identification issues, forensic evidence challenges
               - Drug Offenses: Fourth Amendment violations, search and seizure, chain of custody
               - DUI/DWI: Field sobriety testing, breathalyzer reliability, probable cause
               - Theft Crimes: Intent elements, ownership issues, valuation problems
               - White Collar: Complex financial evidence, intent, regulatory compliance
               - Sex Crimes: Consent issues, false accusations, expert testimony limitations
            
            2. EVIDENCE TYPE STRATEGIES:
               - DNA Evidence: Mixture interpretation, degradation, contamination, statistics
               - Digital Evidence: Chain of custody, forensic imaging, metadata analysis
               - Eyewitness ID: Cross-racial identification, stress factors, suggestive procedures
               - Confession Evidence: Miranda violations, coercion, false confession expert
               - Forensic Evidence: Methodology challenges, error rates, alternative explanations
            
            3. DEFENDANT CHARACTERISTICS:
               - First-Time Offender: Character evidence, sentencing mitigation, probation suitability
               - Repeat Offender: Focus on current charges, avoid prior bad act evidence
               - Mental Health Issues: Competency, diminished capacity, mitigation evidence
               - Juvenile Defendants: Transfer hearing issues, rehabilitation potential
               - High-Profile Cases: Media attention, jury selection challenges, gag orders
            
            4. PROSECUTION STRENGTH RESPONSES:
               - Strong Physical Evidence: Chain of custody, alternative explanations, contamination
               - Multiple Witnesses: Inconsistencies, bias, coaching, collusion possibilities
               - Confession: Miranda violations, coercion tactics, false confession syndrome
               - Expert Testimony: Daubert challenges, methodology critique, opposing experts
               - Video Evidence: Authentication, editing possibilities, perspective limitations
            
            5. CONSTITUTIONAL ISSUES:
               - Fourth Amendment: Warrantless searches, probable cause, exclusionary rule
               - Fifth Amendment: Miranda rights, double jeopardy, self-incrimination
               - Sixth Amendment: Right to counsel, confrontation clause, speedy trial
               - Due Process: Brady violations, prosecutorial misconduct, fundamental fairness
            
            6. JURY SELECTION CONSIDERATIONS:
               - Death Qualification: Life-qualified juries in capital cases
               - Bias Assessment: Pretrial publicity, victim sympathy, law enforcement bias  
               - Demographic Factors: Age, education, employment, prior jury service
               - Hardship Issues: Length of trial, financial impact, family obligations
            
            7. SENTENCING PREPARATION:
               - Mitigation Evidence: Family history, mental health, substance abuse, employment
               - Character Witnesses: Community support, rehabilitation potential, remorse
               - Victim Impact: Address appropriately while protecting client's rights
               - Alternative Sentences: Treatment programs, community service, probation conditions
            
            8. APPELLATE CONSIDERATIONS:
               - Preserve Record: Object to evidence, request jury instructions, note exceptions
               - Constitutional Issues: Develop record for ineffective assistance claims
               - Prosecutorial Misconduct: Document improper arguments, Brady violations
               - Judicial Error: Evidentiary rulings, jury instruction refusals, sentencing errors
            
            9. PLEA NEGOTIATION FACTORS:
               - Strength of Evidence: Realistic assessment of trial prospects
               - Client Goals: Risk tolerance, family considerations, immigration consequences
               - Sentencing Exposure: Guidelines calculations, mandatory minimums, enhancements
               - Collateral Consequences: Professional licenses, immigration, civil liability
            """
        )
    
    def export_example_to_json(self, case_type: CaseType, file_path: str) -> bool:
        """Export example trial notebook to JSON format."""
        try:
            notebook = self.get_example_notebook(case_type)
            if not notebook:
                return False
            
            # Convert to dictionary for JSON serialization
            notebook_dict = {
                'case_type': notebook.case_type.value,
                'case_title': notebook.case_title,
                'case_overview': notebook.case_overview,
                'theory_of_case': notebook.theory_of_case,
                'key_themes': notebook.key_themes,
                'witnesses': [
                    {
                        'name': w.name,
                        'witness_type': w.witness_type.value,
                        'role': w.role,
                        'key_testimony': w.key_testimony,
                        'estimated_time': w.estimated_time,
                        'preparation_notes': w.preparation_notes,
                        'potential_objections': w.potential_objections,
                        'customization_tips': w.customization_tips
                    } for w in notebook.witnesses
                ],
                'exhibits': [
                    {
                        'exhibit_number': e.exhibit_number,
                        'description': e.description,
                        'exhibit_type': e.exhibit_type.value,
                        'source': e.source,
                        'relevance': e.relevance,
                        'foundation_requirements': e.foundation_requirements,
                        'potential_objections': e.potential_objections,
                        'customization_tips': e.customization_tips
                    } for e in notebook.exhibits
                ],
                'jury_instructions': [
                    {
                        'instruction_id': j.instruction_id,
                        'title': j.title,
                        'category': j.category,
                        'instruction_text': j.instruction_text,
                        'applicable_law': j.applicable_law,
                        'customization_notes': j.customization_notes
                    } for j in notebook.jury_instructions
                ],
                'trial_schedule': [
                    {
                        'day_number': t.day_number,
                        'date': t.date.isoformat() if t.date else None,
                        'theme': t.theme,
                        'objectives': t.objectives,
                        'witnesses': t.witnesses,
                        'exhibits': t.exhibits,
                        'time_blocks': t.time_blocks,
                        'preparation_tasks': t.preparation_tasks,
                        'contingency_plans': t.contingency_plans,
                        'customization_notes': t.customization_notes
                    } for t in notebook.trial_schedule
                ],
                'opening_statement_outline': notebook.opening_statement_outline,
                'closing_argument_outline': notebook.closing_argument_outline,
                'general_customization_guide': notebook.general_customization_guide
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(notebook_dict, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting example to JSON: {str(e)}")
            return False
    
    def print_customization_summary(self, case_type: CaseType) -> str:
        """Generate a summary of customization options for a specific case type."""
        notebook = self.get_example_notebook(case_type)
        if not notebook:
            return "Case type not found."
        
        summary = f"""
CUSTOMIZATION SUMMARY FOR {case_type.value.upper().replace('_', ' ')} CASES

CASE OVERVIEW:
{notebook.case_overview.strip()}

KEY CUSTOMIZATION AREAS:

1. WITNESS ADAPTATIONS:
"""
        for witness in notebook.witnesses[:3]:  # Show first 3 witnesses as examples
            summary += f"   • {witness.name}: {witness.customization_tips[:100]}...\n"
        
        summary += f"""
2. EXHIBIT MODIFICATIONS:
"""
        for exhibit in notebook.exhibits[:3]:  # Show first 3 exhibits as examples
            summary += f"   • {exhibit.exhibit_number}: {exhibit.customization_tips[:100]}...\n"
        
        summary += f"""
3. TRIAL SCHEDULE ADJUSTMENTS:
"""
        for day in notebook.trial_schedule[:2]:  # Show first 2 days as examples
            summary += f"   • Day {day.day_number}: {day.customization_notes[:100]}...\n"
        
        summary += f"""
4. GENERAL CUSTOMIZATION PRINCIPLES:
{notebook.general_customization_guide[:500]}...

For complete customization details, review the full trial notebook example and 
adapt each component to your specific case facts, jurisdiction, and client needs.
"""
        
        return summary

# Usage example and testing
if __name__ == "__main__":
    # Create example notebooks
    examples = ExampleTrialNotebooks()
    
    # Get personal injury example
    pi_notebook = examples.get_example_notebook(CaseType.PERSONAL_INJURY)
    print("Personal Injury Example Created")
    print(f"Witnesses: {len(pi_notebook.witnesses)}")
    print(f"Exhibits: {len(pi_notebook.exhibits)}")
    print(f"Trial Days: {len(pi_notebook.trial_schedule)}")
    
    # Get contract dispute example  
    cd_notebook = examples.get_example_notebook(CaseType.CONTRACT_DISPUTE)
    print("Contract Dispute Example Created")
    print(f"Witnesses: {len(cd_notebook.witnesses)}")
    print(f"Exhibits: {len(cd_notebook.exhibits)}")
    print(f"Trial Days: {len(cd_notebook.trial_schedule)}")
    
    # Get criminal defense example
    cr_notebook = examples.get_example_notebook(CaseType.CRIMINAL_DEFENSE)
    print("Criminal Defense Example Created")
    print(f"Witnesses: {len(cr_notebook.witnesses)}")
    print(f"Exhibits: {len(cr_notebook.exhibits)}")
    print(f"Trial Days: {len(cr_notebook.trial_schedule)}")
    
    # Print customization summary
    print("\n" + "="*80)
    print(examples.print_customization_summary(CaseType.PERSONAL_INJURY))