"""
Intelligent Question Generator for Legal Document Processing

CRITICAL LEGAL DISCLAIMER:
This system is designed to assist with document intake and information gathering.
All generated questions are for educational and informational purposes only.
Nothing in this system constitutes legal advice or creates an attorney-client relationship.
Users must consult with qualified legal counsel for legal advice.

Created: 2025-09-14
Legal AI System - Document Intelligence Core
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import re

try:
    from .intelligent_intake import InformationGap, DocumentType, ViolationSeverity
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from intelligent_intake import InformationGap, DocumentType, ViolationSeverity


class GapType(Enum):
    """Common gap types for information gaps (compatible with InformationGap.gap_type string)"""
    DEBT_AMOUNT = "debt_amount"
    CREDITOR_TYPES = "creditor_types"
    CREDITOR_INFO = "creditor_info"
    BUSINESS_TYPE = "business_type"
    INCOME_INFO = "income_info"
    ASSET_INFO = "asset_info"
    CASE_NUMBER = "case_number"
    PARTY_INFO = "party_info"
    PLAINTIFF_INFO = "plaintiff_info"
    COURT_INFO = "court_info"
    DISPUTE_NATURE = "dispute_nature"
    DAMAGES_SOUGHT = "damages_sought"
    MONETARY_DAMAGES = "monetary_damages"


class InputType(Enum):
    """Types of input fields for questions."""
    TEXT = "text"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CURRENCY = "currency"
    DATE = "date"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    BOOLEAN = "boolean"
    TEXTAREA = "textarea"


class ValidationRule(Enum):
    """Validation rules for question inputs."""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    EMAIL_FORMAT = "email_format"
    PHONE_FORMAT = "phone_format"
    DATE_FORMAT = "date_format"
    CURRENCY_FORMAT = "currency_format"
    REGEX_PATTERN = "regex_pattern"
    CUSTOM = "custom"


@dataclass
class Validation:
    """Validation configuration for a question."""
    rule: ValidationRule
    value: Optional[Any] = None
    message: str = ""

    def validate(self, input_value: Any) -> tuple[bool, str]:
        """Validate input against this rule."""
        if self.rule == ValidationRule.REQUIRED:
            if not input_value or (isinstance(input_value, str) and not input_value.strip()):
                return False, self.message or "This field is required"

        elif self.rule == ValidationRule.MIN_LENGTH:
            if isinstance(input_value, str) and len(input_value) < self.value:
                return False, self.message or f"Must be at least {self.value} characters"

        elif self.rule == ValidationRule.MAX_LENGTH:
            if isinstance(input_value, str) and len(input_value) > self.value:
                return False, self.message or f"Must be no more than {self.value} characters"

        elif self.rule == ValidationRule.EMAIL_FORMAT:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(input_value)):
                return False, self.message or "Please enter a valid email address"

        elif self.rule == ValidationRule.CURRENCY_FORMAT:
            if not re.match(r'^\$?[\d,]+\.?\d{0,2}$', str(input_value).replace(' ', '')):
                return False, self.message or "Please enter a valid currency amount"

        return True, ""


@dataclass
class QuestionOption:
    """Option for select/multiselect questions."""
    value: str
    label: str
    description: Optional[str] = None
    follow_up_questions: List[str] = field(default_factory=list)


@dataclass
class IntelligentQuestion:
    """Comprehensive question structure for document intake."""
    # Basic identification
    question_id: str
    question_text: str
    why_needed: str  # Educational explanation

    # Input configuration
    input_type: InputType
    options: List[QuestionOption] = field(default_factory=list)
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None

    # Validation
    validations: List[Validation] = field(default_factory=list)

    # Legal compliance
    disclaimer_text: str = ""

    # Contextual information
    category: str = ""
    priority: int = 1  # 1=highest, 5=lowest
    depends_on: List[str] = field(default_factory=list)  # Other question IDs

    # Follow-up logic
    follow_up_conditions: Dict[str, List[str]] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)

    def is_conditional(self) -> bool:
        """Check if this question depends on other answers."""
        return len(self.depends_on) > 0

    def get_follow_ups(self, answer: Any) -> List[str]:
        """Get follow-up question IDs based on the answer."""
        answer_str = str(answer).lower()
        for condition, follow_ups in self.follow_up_conditions.items():
            if condition.lower() in answer_str:
                return follow_ups
        return []


class ComprehensiveQuestionBank:
    """Must have questions for EVERY scenario"""

    def __init__(self):
        self.question_database = {
            'bankruptcy': {
                'eligibility': [
                    'What is your total debt amount?',
                    'Are debts primarily consumer or business?',
                    'Have you filed bankruptcy in last 8 years?',
                    'Do you pass the means test for Chapter 7?',
                    'Are you facing foreclosure or repossession?',
                    'Have you received credit counseling?',
                    'Are you married filing jointly?',
                    'Do you have any priority debts?',
                    'Have you made preferential payments to creditors?',
                    'Are you current on domestic support obligations?',
                    'Do you have any pending lawsuits?',
                    'Have you transferred any property in last 2 years?',
                    'Are you operating a business?',
                    'Do you have any co-signers on debts?',
                    'Have you incurred debt for luxury goods recently?',
                    'Are you being garnished?',
                    'Do you have secured vs unsecured debt?',
                    'What is your monthly disposable income?',
                    'Are there any criminal charges pending?',
                    'Do you have student loans?',
                    'Are taxes owed to IRS or state?',
                    'Have you filed tax returns for last 4 years?',
                    'Do you have retirement accounts?',
                    'Are you facing utility shut-offs?',
                    'Do you have health insurance?',
                    'Are there medical bills involved?',
                    'Do you rent or own your home?',
                    'What is current household size?',
                    'Do you have dependents?',
                    'Are you employed or unemployed?',
                    'What is your age and health status?',
                    'Do you have disability income?',
                    'Are there inheritance expectations?',
                    'Do you have life insurance policies?',
                    'Are there pending insurance claims?',
                    'Do you have valuable collections?',
                    'Are there business partnerships?',
                    'Do you have rental properties?',
                    'Are there pending contracts?',
                    'Do you have professional licenses?',
                    'Are there workers compensation claims?',
                    'Do you have pending divorce proceedings?',
                    'Are there child support obligations?',
                    'Do you have alimony payments?',
                    'Are there restraining orders?',
                    'Do you have criminal restitution orders?',
                    'Are there HOA dues or liens?',
                    'Do you have boat, RV, or aircraft?',
                    'Are there storage unit contents?',
                    'Do you have cryptocurrency assets?',
                    'Are there foreign bank accounts?'
                ],
                'assets': [
                    'Do you own real estate?',
                    'Value of personal property?',
                    'Bank account balances?',
                    'Investment account values?',
                    'Retirement account balances?',
                    'Cash on hand amount?',
                    'Vehicle values and loans?',
                    'Business assets and values?',
                    'Jewelry and collectibles value?',
                    'Electronics and equipment value?',
                    'Household goods value?',
                    'Clothing and personal items value?',
                    'Tools and equipment value?',
                    'Sporting goods value?',
                    'Art and antiques value?',
                    'Musical instruments value?',
                    'Books and media value?',
                    'Furniture value?',
                    'Appliances value?',
                    'Lawn equipment value?',
                    'Garage contents value?',
                    'Storage unit contents?',
                    'Safety deposit box contents?',
                    'Pending tax refunds?',
                    'Insurance claim proceeds?',
                    'Lawsuit settlement proceeds?',
                    'Inheritance expectations?',
                    'Life insurance cash value?',
                    'Annuity values?',
                    'Stock options?',
                    'Partnership interests?',
                    'Business ownership percentages?',
                    'Intellectual property?',
                    'Patents or trademarks?',
                    'Royalty income streams?',
                    'Trust beneficiary interests?',
                    'Contingent interests in property?',
                    'Security deposits held?',
                    'Utility deposits?',
                    'Club memberships?'
                ],
                'income': [
                    'Current monthly income?',
                    'Income sources?',
                    'Expected changes in income?',
                    'Employment status?',
                    'Spouse employment and income?',
                    'Overtime or bonus income?',
                    'Commission-based income?',
                    'Self-employment income?',
                    'Business income and expenses?',
                    'Rental property income?',
                    'Social Security benefits?',
                    'Disability benefits?',
                    'Unemployment benefits?',
                    'Workers compensation benefits?',
                    'Veteran benefits?',
                    'Retirement income?',
                    'Pension income?',
                    'Annuity payments?',
                    'Investment income?',
                    'Dividend income?',
                    'Interest income?',
                    'Alimony received?',
                    'Child support received?',
                    'Government assistance?',
                    'Food stamp benefits?',
                    'Housing assistance?',
                    'Regular gifts received?',
                    'Family financial support?',
                    'Seasonal income variations?',
                    'Tax refund expectations?'
                ]
            },
            'litigation': {
                'case_basics': [
                    'What type of case is this?',
                    'Who are all parties involved?',
                    'What court has jurisdiction?',
                    'When did the dispute arise?',
                    'What damages are sought?',
                    'Is there a written contract?',
                    'Are there witnesses?',
                    'Is there insurance coverage?',
                    'Have you attempted settlement?',
                    'Are there related cases?',
                    'Is statute of limitations an issue?',
                    'Are there pending motions?',
                    'Is discovery ongoing?',
                    'Are depositions scheduled?',
                    'Is mediation ordered?',
                    'Is arbitration required?',
                    'Are there expert witnesses?',
                    'Is trial scheduled?',
                    'Are appeals likely?',
                    'Are attorney fees recoverable?'
                ],
                'parties': [
                    'Who is the plaintiff?',
                    'Who are the defendants?',
                    'Are there third parties?',
                    'Are there cross-claims?',
                    'Are there counterclaims?',
                    'Who has standing to sue?',
                    'Are parties properly served?',
                    'Are all necessary parties joined?',
                    'Are there insurance companies involved?',
                    'Are there government entities involved?',
                    'Are there foreign parties?',
                    'Are parties represented by counsel?',
                    'Are there conflicts of interest?',
                    'Are there class action issues?',
                    'Are there corporate entities?',
                    'Are there partnership issues?',
                    'Are there trust or estate issues?',
                    'Are there minor or incompetent parties?',
                    'Are there bankruptcy issues?',
                    'Are there succession issues?'
                ],
                'damages': [
                    'What is the claimed damage amount?',
                    'Are damages liquidated or unliquidated?',
                    'Are there economic damages?',
                    'Are there non-economic damages?',
                    'Is pain and suffering claimed?',
                    'Are punitive damages sought?',
                    'Are attorney fees requested?',
                    'Are there mitigation issues?',
                    'Is there a duty to mitigate?',
                    'Are damages speculative?',
                    'Are there offset issues?',
                    'Are there insurance proceeds?',
                    'Are there tax consequences?',
                    'Are there future damages?',
                    'Is there a structured settlement?',
                    'Are there loss of earnings claims?',
                    'Are there medical expense claims?',
                    'Are there property damage claims?',
                    'Are there business interruption claims?',
                    'Are there consequential damages?'
                ]
            },
            'criminal': {
                'charges': [
                    'What specific charges are filed?',
                    'Are charges felony or misdemeanor?',
                    'What is the maximum penalty?',
                    'Are there mandatory minimums?',
                    'Are there enhancement allegations?',
                    'Are charges in state or federal court?',
                    'Are there co-defendants?',
                    'Is this a first offense?',
                    'Are there prior convictions?',
                    'Is probation or parole involved?',
                    'Are there pending charges elsewhere?',
                    'Are there immigration consequences?',
                    'Are professional licenses at risk?',
                    'Is restitution required?',
                    'Are there victim impact considerations?',
                    'Is plea bargaining available?',
                    'Are there cooperation opportunities?',
                    'Is diversion program available?',
                    'Are there mental health issues?',
                    'Is substance abuse treatment needed?'
                ],
                'evidence': [
                    'What evidence does prosecution have?',
                    'Are there witness statements?',
                    'Is there physical evidence?',
                    'Are there recordings or photos?',
                    'Is there DNA evidence?',
                    'Are there fingerprints?',
                    'Is there surveillance video?',
                    'Are there cell phone records?',
                    'Is there computer evidence?',
                    'Are there financial records?',
                    'Is there expert testimony expected?',
                    'Are there search warrant issues?',
                    'Are Miranda rights an issue?',
                    'Are there identification issues?',
                    'Is chain of custody proper?',
                    'Are there lab report issues?',
                    'Is there Brady material?',
                    'Are there discovery violations?',
                    'Is evidence sufficient for conviction?',
                    'Are there suppression motions needed?'
                ]
            }
        }

class IntelligentQuestionGenerator:
    """
    Generates intelligent, contextual questions for legal document intake.

    LEGAL DISCLAIMER:
    This system generates educational questions to assist with document completion.
    All questions and responses are for informational purposes only and do not
    constitute legal advice. Consult qualified legal counsel for legal guidance.
    """

    def __init__(self):
        self.base_disclaimer = (
            "EDUCATIONAL PURPOSES ONLY: This information is requested for document "
            "completion assistance. This does not constitute legal advice. Consult "
            "with a qualified attorney for legal guidance specific to your situation."
        )

        # Initialize comprehensive question bank
        self.question_bank = ComprehensiveQuestionBank()

        # Common validation rules
        self.required_validation = Validation(ValidationRule.REQUIRED, message="This field is required")
        self.currency_validation = Validation(ValidationRule.CURRENCY_FORMAT)
        self.email_validation = Validation(ValidationRule.EMAIL_FORMAT)

    def generate_questions_for_bankruptcy(self, information_gaps: List[InformationGap]) -> List[IntelligentQuestion]:
        """
        Generate bankruptcy-specific questions based on identified information gaps.

        Args:
            information_gaps: List of InformationGap objects from DocumentIntakeAnalyzer

        Returns:
            List of IntelligentQuestion objects for bankruptcy cases
        """
        questions = []
        gap_types = {gap.gap_type for gap in information_gaps}

        # Always generate core bankruptcy questions if we have any gaps
        if information_gaps:
            # Generate standard debt amount question
            questions.append(IntelligentQuestion(
                question_id=f"debt_total_{uuid.uuid4().hex[:8]}",
                question_text="What is your total unsecured debt amount?",
                why_needed="Total debt amount helps determine bankruptcy chapter eligibility and required documentation.",
                input_type=InputType.CURRENCY,
                placeholder="Example: $25000",
                validations=[self.currency_validation, self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Debt Information",
                priority=1,
                tags=["bankruptcy", "debt", "core"]
            ))

            # Generate business type question
            questions.append(IntelligentQuestion(
                question_id=f"business_type_{uuid.uuid4().hex[:8]}",
                question_text="What type of business entity is filing for bankruptcy?",
                why_needed="Business type affects bankruptcy chapter eligibility and procedural requirements.",
                input_type=InputType.SELECT,
                options=[
                    QuestionOption("corporation", "Corporation", "C-Corp or S-Corp"),
                    QuestionOption("llc", "Limited Liability Company", "LLC"),
                    QuestionOption("partnership", "Partnership", "General or Limited Partnership"),
                    QuestionOption("sole_proprietorship", "Sole Proprietorship", "Individual business"),
                    QuestionOption("other", "Other", "Other business structure")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Business Information",
                priority=1,
                tags=["bankruptcy", "business", "core"]
            ))

        # Additional debt questions for specific gaps
        if GapType.DEBT_AMOUNT.value in gap_types or "debt_amount" in gap_types or any("debt" in gap for gap in gap_types):

            questions.append(IntelligentQuestion(
                question_id=f"secured_debt_{uuid.uuid4().hex[:8]}",
                question_text="What is your total secured debt (mortgages, car loans, etc.)?",
                why_needed="Secured debt affects asset protection strategies and bankruptcy planning.",
                input_type=InputType.CURRENCY,
                placeholder="$0.00",
                validations=[self.currency_validation],
                disclaimer_text=self.base_disclaimer,
                category="Financial Information",
                priority=2,
                tags=["bankruptcy", "secured_debt", "assets"]
            ))

        # Creditor information
        if (GapType.CREDITOR_TYPES.value in gap_types or "creditor_types" in gap_types or
            GapType.CREDITOR_INFO.value in gap_types or "creditor_info" in gap_types):
            questions.append(IntelligentQuestion(
                question_id=f"creditor_types_{uuid.uuid4().hex[:8]}",
                question_text="What types of creditors do you owe money to?",
                why_needed="Different creditor types have different rights and priorities in bankruptcy proceedings.",
                input_type=InputType.MULTISELECT,
                options=[
                    QuestionOption("credit_cards", "Credit Card Companies", "Unsecured consumer debt"),
                    QuestionOption("medical", "Medical Providers", "Hospital, doctor, or medical service debt"),
                    QuestionOption("utilities", "Utility Companies", "Electric, gas, water, phone bills"),
                    QuestionOption("landlord", "Landlords", "Rent or lease obligations"),
                    QuestionOption("banks", "Banks/Financial Institutions", "Personal loans, lines of credit"),
                    QuestionOption("government", "Government Agencies", "Tax debt, student loans, fines"),
                    QuestionOption("business", "Business Creditors", "Suppliers, vendors, business loans"),
                    QuestionOption("family", "Family/Friends", "Personal loans from individuals"),
                    QuestionOption("other", "Other", "Other types of creditors")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Creditor Information",
                priority=1,
                tags=["bankruptcy", "creditors"],
                follow_up_conditions={
                    "government": ["tax_debt_details", "student_loan_details"],
                    "business": ["business_type_question", "business_debt_details"],
                    "medical": ["medical_debt_breakdown"]
                }
            ))

        # Business type (if business debt involved)
        if GapType.BUSINESS_TYPE.value in gap_types or "business_type" in gap_types:
            questions.append(IntelligentQuestion(
                question_id=f"business_type_{uuid.uuid4().hex[:8]}",
                question_text="What type of business entity are you filing for?",
                why_needed="Business entity type determines applicable bankruptcy chapters and procedures.",
                input_type=InputType.SELECT,
                options=[
                    QuestionOption("individual", "Individual/Personal", "Personal bankruptcy filing"),
                    QuestionOption("sole_proprietorship", "Sole Proprietorship", "Individual business owner"),
                    QuestionOption("partnership", "Partnership", "Business partnership entity"),
                    QuestionOption("corporation", "Corporation", "Corporate entity"),
                    QuestionOption("llc", "Limited Liability Company (LLC)", "LLC business entity"),
                    QuestionOption("other", "Other", "Other business structure")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Business Information",
                priority=1,
                tags=["bankruptcy", "business_type"],
                follow_up_conditions={
                    "corporation": ["corporate_structure_details"],
                    "llc": ["llc_member_details"],
                    "partnership": ["partnership_details"]
                }
            ))

        # Income information
        if GapType.INCOME_INFO.value in gap_types or "income_info" in gap_types:
            questions.append(IntelligentQuestion(
                question_id=f"monthly_income_{uuid.uuid4().hex[:8]}",
                question_text="What is your current gross monthly income from all sources?",
                why_needed="Income information determines means test eligibility and affects bankruptcy chapter options.",
                input_type=InputType.CURRENCY,
                placeholder="$0.00",
                validations=[
                    self.required_validation,
                    self.currency_validation
                ],
                disclaimer_text=self.base_disclaimer,
                category="Income Information",
                priority=1,
                tags=["bankruptcy", "income", "means_test"]
            ))

        # Asset information
        if GapType.ASSET_INFO.value in gap_types or "asset_info" in gap_types:
            questions.append(IntelligentQuestion(
                question_id=f"major_assets_{uuid.uuid4().hex[:8]}",
                question_text="Do you own any major assets?",
                why_needed="Asset information is critical for determining exemptions and liquidation potential.",
                input_type=InputType.MULTISELECT,
                options=[
                    QuestionOption("real_estate", "Real Estate", "Home, land, rental properties"),
                    QuestionOption("vehicles", "Vehicles", "Cars, trucks, motorcycles, boats"),
                    QuestionOption("bank_accounts", "Bank Accounts", "Checking, savings, CDs"),
                    QuestionOption("investments", "Investments", "Stocks, bonds, retirement accounts"),
                    QuestionOption("business_assets", "Business Assets", "Equipment, inventory, business accounts"),
                    QuestionOption("personal_property", "Valuable Personal Property", "Jewelry, collectibles, electronics"),
                    QuestionOption("none", "No Major Assets", "No significant assets to report")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Asset Information",
                priority=1,
                tags=["bankruptcy", "assets", "exemptions"]
            ))

        return questions

    def generate_questions_for_litigation(self, information_gaps: List[InformationGap]) -> List[IntelligentQuestion]:
        """
        Generate litigation-specific questions based on identified information gaps.

        Args:
            information_gaps: List of InformationGap objects from DocumentIntakeAnalyzer

        Returns:
            List of IntelligentQuestion objects for litigation cases
        """
        questions = []
        gap_types = {gap.gap_type for gap in information_gaps}

        # Case information
        if GapType.CASE_NUMBER.value in gap_types or "case_number" in gap_types:
            questions.append(IntelligentQuestion(
                question_id=f"case_number_{uuid.uuid4().hex[:8]}",
                question_text="What is the court case number (if assigned)?",
                why_needed="Case numbers are essential for court filings and case tracking.",
                input_type=InputType.TEXT,
                placeholder="e.g., CV-2024-123456",
                validations=[
                    Validation(ValidationRule.MAX_LENGTH, 50, "Case number too long")
                ],
                disclaimer_text=self.base_disclaimer,
                category="Case Information",
                priority=1,
                tags=["litigation", "case_number", "court"]
            ))

        # Party information
        if (GapType.PARTY_INFO.value in gap_types or "party_info" in gap_types or
            GapType.PLAINTIFF_INFO.value in gap_types or "plaintiff_info" in gap_types):
            questions.append(IntelligentQuestion(
                question_id=f"opposing_parties_{uuid.uuid4().hex[:8]}",
                question_text="Who are the opposing parties in this litigation?",
                why_needed="Complete party information is required for proper legal service and court filings.",
                input_type=InputType.TEXTAREA,
                placeholder="List all opposing parties with their full legal names and addresses if known",
                validations=[
                    self.required_validation,
                    Validation(ValidationRule.MIN_LENGTH, 10, "Please provide more detailed information")
                ],
                disclaimer_text=self.base_disclaimer,
                category="Party Information",
                priority=1,
                tags=["litigation", "parties", "defendants"]
            ))

            questions.append(IntelligentQuestion(
                question_id=f"party_representatives_{uuid.uuid4().hex[:8]}",
                question_text="Do any parties have legal representation?",
                why_needed="Knowledge of opposing counsel affects communication protocols and procedural requirements.",
                input_type=InputType.SELECT,
                options=[
                    QuestionOption("all_represented", "All parties have attorneys", "All parties are represented by counsel"),
                    QuestionOption("some_represented", "Some parties have attorneys", "Mixed representation status"),
                    QuestionOption("none_represented", "No parties have attorneys", "All parties are pro se"),
                    QuestionOption("unknown", "Unknown", "Representation status unclear")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Party Information",
                priority=2,
                tags=["litigation", "attorneys", "representation"],
                follow_up_conditions={
                    "all_represented": ["attorney_contact_info"],
                    "some_represented": ["partial_representation_details"]
                }
            ))

        # Court and jurisdiction
        if GapType.COURT_INFO.value in gap_types or "court_info" in gap_types:
            questions.append(IntelligentQuestion(
                question_id=f"court_jurisdiction_{uuid.uuid4().hex[:8]}",
                question_text="In which court is this case filed or should be filed?",
                why_needed="Proper jurisdiction and venue are fundamental to case validity and procedural compliance.",
                input_type=InputType.SELECT,
                options=[
                    QuestionOption("federal_district", "Federal District Court", "Federal civil matters"),
                    QuestionOption("state_superior", "State Superior Court", "State civil matters"),
                    QuestionOption("state_district", "State District Court", "Lower-level state matters"),
                    QuestionOption("bankruptcy", "Bankruptcy Court", "Bankruptcy proceedings"),
                    QuestionOption("family", "Family Court", "Family law matters"),
                    QuestionOption("probate", "Probate Court", "Estate and probate matters"),
                    QuestionOption("other", "Other", "Other court type")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Jurisdiction",
                priority=1,
                tags=["litigation", "court", "jurisdiction"]
            ))

        # Dispute nature and damages
        if GapType.DISPUTE_NATURE.value in gap_types or "dispute_nature" in gap_types:
            questions.append(IntelligentQuestion(
                question_id=f"dispute_type_{uuid.uuid4().hex[:8]}",
                question_text="What type of legal dispute is this?",
                why_needed="Dispute classification determines applicable laws, procedures, and potential remedies.",
                input_type=InputType.SELECT,
                options=[
                    QuestionOption("contract", "Contract Dispute", "Breach of contract or agreement"),
                    QuestionOption("tort", "Personal Injury/Tort", "Negligence, intentional torts"),
                    QuestionOption("employment", "Employment Dispute", "Workplace-related legal issues"),
                    QuestionOption("business", "Business/Commercial", "Business operations disputes"),
                    QuestionOption("real_estate", "Real Estate", "Property-related disputes"),
                    QuestionOption("family", "Family Law", "Divorce, custody, support"),
                    QuestionOption("debt_collection", "Debt Collection", "Collection actions"),
                    QuestionOption("other", "Other", "Other type of dispute")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Case Type",
                priority=1,
                tags=["litigation", "dispute_type", "case_classification"],
                follow_up_conditions={
                    "contract": ["contract_details", "breach_specifics"],
                    "tort": ["injury_details", "liability_assessment"],
                    "employment": ["employment_relationship", "violation_type"]
                }
            ))

        # Damages and relief
        if (GapType.DAMAGES_SOUGHT.value in gap_types or "damages_sought" in gap_types or
            GapType.MONETARY_DAMAGES.value in gap_types or "monetary_damages" in gap_types):
            questions.append(IntelligentQuestion(
                question_id=f"damages_amount_{uuid.uuid4().hex[:8]}",
                question_text="What is the estimated monetary value of damages or relief sought?",
                why_needed="Damage amounts affect court jurisdiction, filing fees, and case strategy.",
                input_type=InputType.CURRENCY,
                placeholder="$0.00",
                validations=[
                    self.currency_validation,
                    Validation(ValidationRule.MIN_VALUE, 0, "Amount cannot be negative")
                ],
                disclaimer_text=self.base_disclaimer,
                category="Damages",
                priority=2,
                tags=["litigation", "damages", "relief"]
            ))

            questions.append(IntelligentQuestion(
                question_id=f"relief_type_{uuid.uuid4().hex[:8]}",
                question_text="What type of relief are you seeking?",
                why_needed="Types of relief determine case strategy and available legal remedies.",
                input_type=InputType.MULTISELECT,
                options=[
                    QuestionOption("monetary", "Monetary Damages", "Financial compensation"),
                    QuestionOption("injunctive", "Injunctive Relief", "Court order to do/stop doing something"),
                    QuestionOption("declaratory", "Declaratory Judgment", "Court declaration of rights/obligations"),
                    QuestionOption("specific_performance", "Specific Performance", "Force performance of contract"),
                    QuestionOption("restitution", "Restitution", "Return of property or benefits"),
                    QuestionOption("other", "Other", "Other forms of relief")
                ],
                validations=[self.required_validation],
                disclaimer_text=self.base_disclaimer,
                category="Relief Sought",
                priority=2,
                tags=["litigation", "relief", "remedies"]
            ))

        return questions

    def get_comprehensive_questions(self, category: str, subcategory: Optional[str] = None) -> List[str]:
        """
        Get comprehensive questions from the question bank for any scenario.

        Args:
            category: Main category (e.g., 'bankruptcy', 'litigation', 'criminal')
            subcategory: Optional subcategory (e.g., 'eligibility', 'assets', 'income')

        Returns:
            List of question strings for the specified category/subcategory
        """
        if category not in self.question_bank.question_database:
            return []

        category_questions = self.question_bank.question_database[category]

        if subcategory and subcategory in category_questions:
            return category_questions[subcategory]
        elif subcategory is None:
            # Return all questions from all subcategories
            all_questions = []
            for subcat_questions in category_questions.values():
                all_questions.extend(subcat_questions)
            return all_questions
        else:
            return []

    def create_intelligent_question_from_bank(self, category: str, subcategory: str,
                                            question_text: str, **kwargs) -> IntelligentQuestion:
        """
        Create an IntelligentQuestion object from a question bank question.

        Args:
            category: Main category
            subcategory: Subcategory
            question_text: Question text from bank
            **kwargs: Additional parameters for IntelligentQuestion

        Returns:
            IntelligentQuestion object
        """
        # Determine appropriate input type based on question content
        input_type = self._determine_input_type(question_text)

        # Set up validations based on input type
        validations = self._get_default_validations(input_type)

        # Create question
        return IntelligentQuestion(
            question_id=f"{category}_{subcategory}_{uuid.uuid4().hex[:8]}",
            question_text=question_text,
            why_needed=f"This information is needed for {category} {subcategory} assessment.",
            input_type=input_type,
            validations=validations,
            disclaimer_text=self.base_disclaimer,
            category=f"{category.title()} {subcategory.title()}",
            priority=kwargs.get('priority', 2),
            tags=[category, subcategory],
            **{k: v for k, v in kwargs.items() if k != 'priority'}
        )

    def _determine_input_type(self, question_text: str) -> InputType:
        """Determine appropriate input type based on question content."""
        text_lower = question_text.lower()

        if any(term in text_lower for term in ['amount', 'value', 'cost', 'price', '$']):
            return InputType.CURRENCY
        elif any(term in text_lower for term in ['date', 'when', 'year']):
            return InputType.DATE
        elif any(term in text_lower for term in ['email', 'e-mail']):
            return InputType.EMAIL
        elif any(term in text_lower for term in ['phone', 'telephone', 'number']):
            return InputType.PHONE
        elif question_text.endswith('?') and any(word in text_lower for word in ['are', 'is', 'do', 'does', 'have', 'has']):
            return InputType.BOOLEAN
        elif 'describe' in text_lower or 'explain' in text_lower or 'details' in text_lower:
            return InputType.TEXTAREA
        else:
            return InputType.TEXT

    def _get_default_validations(self, input_type: InputType) -> List[Validation]:
        """Get default validations for an input type."""
        validations = [self.required_validation]

        if input_type == InputType.CURRENCY:
            validations.append(self.currency_validation)
        elif input_type == InputType.EMAIL:
            validations.append(self.email_validation)
        elif input_type == InputType.TEXTAREA:
            validations.append(Validation(ValidationRule.MIN_LENGTH, 20, "Please provide more details"))

        return validations

    def generate_comprehensive_bankruptcy_questions(self) -> List[IntelligentQuestion]:
        """Generate comprehensive bankruptcy questions covering all scenarios."""
        questions = []

        # Generate questions from each subcategory
        for subcategory in ['eligibility', 'assets', 'income']:
            bank_questions = self.get_comprehensive_questions('bankruptcy', subcategory)

            for question_text in bank_questions[:10]:  # First 10 from each category
                question = self.create_intelligent_question_from_bank(
                    'bankruptcy', subcategory, question_text,
                    priority=1 if subcategory == 'eligibility' else 2
                )
                questions.append(question)

        return questions

    def generate_comprehensive_litigation_questions(self) -> List[IntelligentQuestion]:
        """Generate comprehensive litigation questions covering all scenarios."""
        questions = []

        # Generate questions from each subcategory
        for subcategory in ['case_basics', 'parties', 'damages']:
            bank_questions = self.get_comprehensive_questions('litigation', subcategory)

            for question_text in bank_questions[:8]:  # First 8 from each category
                question = self.create_intelligent_question_from_bank(
                    'litigation', subcategory, question_text,
                    priority=1 if subcategory == 'case_basics' else 2
                )
                questions.append(question)

        return questions

    def generate_comprehensive_criminal_questions(self) -> List[IntelligentQuestion]:
        """Generate comprehensive criminal questions covering all scenarios."""
        questions = []

        # Generate questions from each subcategory
        for subcategory in ['charges', 'evidence']:
            bank_questions = self.get_comprehensive_questions('criminal', subcategory)

            for question_text in bank_questions[:10]:  # First 10 from each category
                question = self.create_intelligent_question_from_bank(
                    'criminal', subcategory, question_text,
                    priority=1 if subcategory == 'charges' else 2
                )
                questions.append(question)

        return questions

    def generate_dynamic_follow_ups(self, base_question: IntelligentQuestion, answer: Any) -> List[IntelligentQuestion]:
        """
        Generate dynamic follow-up questions based on a user's answer.

        Args:
            base_question: The original question that was answered
            answer: The user's answer to the base question

        Returns:
            List of follow-up IntelligentQuestion objects
        """
        follow_ups = []

        # Get follow-up question IDs from base question
        follow_up_ids = base_question.get_follow_ups(answer)

        # Generate specific follow-up questions based on context
        for follow_up_id in follow_up_ids:
            if "debt_breakdown" in follow_up_id:
                follow_ups.append(self._generate_debt_breakdown_question(answer))
            elif "tax_debt" in follow_up_id:
                follow_ups.append(self._generate_tax_debt_question())
            elif "business_details" in follow_up_id:
                follow_ups.append(self._generate_business_details_question())
            elif "attorney_contact" in follow_up_id:
                follow_ups.append(self._generate_attorney_contact_question())

        return follow_ups

    def _generate_debt_breakdown_question(self, total_debt: Any) -> IntelligentQuestion:
        """Generate debt breakdown question based on total debt amount."""
        return IntelligentQuestion(
            question_id=f"debt_breakdown_{uuid.uuid4().hex[:8]}",
            question_text="Please provide a breakdown of your largest debts:",
            why_needed="Detailed debt breakdown helps prioritize creditor communications and payment strategies.",
            input_type=InputType.TEXTAREA,
            placeholder="List your top 5-10 largest debts with creditor names and amounts",
            validations=[
                self.required_validation,
                Validation(ValidationRule.MIN_LENGTH, 50, "Please provide more detailed breakdown")
            ],
            disclaimer_text=self.base_disclaimer,
            category="Financial Details",
            priority=1,
            tags=["bankruptcy", "debt_breakdown", "creditors"]
        )

    def _generate_tax_debt_question(self) -> IntelligentQuestion:
        """Generate tax debt specific question."""
        return IntelligentQuestion(
            question_id=f"tax_debt_{uuid.uuid4().hex[:8]}",
            question_text="What tax years and amounts are involved in your tax debt?",
            why_needed="Tax debt has special priority status and different discharge rules in bankruptcy.",
            input_type=InputType.TEXTAREA,
            placeholder="e.g., IRS: 2020 ($5,000), 2021 ($3,000), State: 2021 ($1,500)",
            validations=[self.required_validation],
            disclaimer_text=self.base_disclaimer + " Tax debt involves complex federal and state regulations.",
            category="Tax Information",
            priority=1,
            tags=["bankruptcy", "tax_debt", "government"]
        )

    def _generate_business_details_question(self) -> IntelligentQuestion:
        """Generate business details question."""
        return IntelligentQuestion(
            question_id=f"business_details_{uuid.uuid4().hex[:8]}",
            question_text="Please describe your business operations and current status:",
            why_needed="Business details affect bankruptcy chapter eligibility and asset protection options.",
            input_type=InputType.TEXTAREA,
            placeholder="Business name, type of business, current status (active/closed), number of employees",
            validations=[
                self.required_validation,
                Validation(ValidationRule.MIN_LENGTH, 30, "Please provide more business details")
            ],
            disclaimer_text=self.base_disclaimer,
            category="Business Information",
            priority=1,
            tags=["bankruptcy", "business", "operations"]
        )

    def _generate_attorney_contact_question(self) -> IntelligentQuestion:
        """Generate attorney contact information question."""
        return IntelligentQuestion(
            question_id=f"attorney_contact_{uuid.uuid4().hex[:8]}",
            question_text="Please provide opposing counsel contact information:",
            why_needed="Opposing counsel contact information is required for proper legal communications.",
            input_type=InputType.TEXTAREA,
            placeholder="Attorney name, law firm, phone number, email address",
            validations=[self.required_validation],
            disclaimer_text=self.base_disclaimer + " All communications with opposing counsel must follow legal protocols.",
            category="Attorney Information",
            priority=1,
            tags=["litigation", "opposing_counsel", "contact"]
        )

    def generate_questions(self, gaps: List[str]) -> List[Dict[str, Any]]:
        """
        STANDARDIZED INTERFACE: Generate questions from gaps

        Args:
            gaps (List[str]): List of gap identifiers from DocumentAnalyzer

        Returns:
            List[Dict] with keys: id, text, disclaimer
        """
        questions = []

        # Determine document type from gaps to call appropriate method
        # Check for bankruptcy-related gaps (more comprehensive patterns)
        bankruptcy_patterns = ['debt', 'creditor', 'bankruptcy', 'debtor', 'chapter', 'filing', 'schedules']
        if any(pattern in gap.lower() for gap in gaps for pattern in bankruptcy_patterns):
            # Create InformationGap objects for bankruptcy questions
            info_gaps = [
                InformationGap(
                    gap_type=gap,
                    description=f"Missing information: {gap}",
                    severity=ViolationSeverity.MEDIUM,
                    required_for=[],
                    suggestions=[]
                )
                for gap in gaps
            ]
            raw_questions = self.generate_questions_for_bankruptcy(info_gaps)
        elif any(pattern in gap.lower() for gap in gaps for pattern in ['litigation', 'plaintiff', 'damages', 'court', 'lawsuit', 'complaint']):
            # Create InformationGap objects for litigation questions
            info_gaps = [
                InformationGap(
                    gap_type=gap,
                    description=f"Missing information: {gap}",
                    severity=ViolationSeverity.MEDIUM,
                    required_for=[],
                    suggestions=[]
                )
                for gap in gaps
            ]
            raw_questions = self.generate_questions_for_litigation(info_gaps)
        else:
            # Default to bankruptcy questions for unknown gaps
            info_gaps = [
                InformationGap(
                    gap_type=gap,
                    description=f"Missing information: {gap}",
                    severity=ViolationSeverity.MEDIUM,
                    required_for=[],
                    suggestions=[]
                )
                for gap in gaps
            ]
            raw_questions = self.generate_questions_for_bankruptcy(info_gaps)

        # Convert to standardized format
        for q in raw_questions:
            questions.append({
                'id': q.question_id,
                'text': q.question_text,
                'disclaimer': q.disclaimer_text
            })

        return questions


def test_question_generator():
    """
    Test the IntelligentQuestionGenerator with sample information gaps.

    LEGAL DISCLAIMER:
    This test function is for system validation only. All generated questions
    are for educational purposes and do not constitute legal advice.
    """
    print("=== INTELLIGENT QUESTION GENERATOR TEST ===")
    print("LEGAL DISCLAIMER: All questions generated are for educational purposes only.")
    print("This system does not provide legal advice. Consult qualified legal counsel.\n")

    # Import ViolationSeverity from intelligent_intake
    try:
        from .intelligent_intake import ViolationSeverity
    except ImportError:
        from intelligent_intake import ViolationSeverity

    # Create test information gaps (compatible with InformationGap structure)
    test_gaps = [
        InformationGap(
            gap_type="debt_amount",
            description="Total debt amount not specified",
            severity=ViolationSeverity.HIGH,
            required_for=["bankruptcy filing"],
            suggestions=["What is your total debt?"]
        ),
        InformationGap(
            gap_type="creditor_types",
            description="Types of creditors not identified",
            severity=ViolationSeverity.MEDIUM,
            required_for=["bankruptcy filing"],
            suggestions=["What types of creditors do you have?"]
        ),
        InformationGap(
            gap_type="business_type",
            description="Business entity type unclear",
            severity=ViolationSeverity.HIGH,
            required_for=["business bankruptcy"],
            suggestions=["What type of business entity?"]
        )
    ]

    # Initialize generator
    generator = IntelligentQuestionGenerator()

    # Test bankruptcy questions
    print("TESTING: Bankruptcy Question Generation")
    bankruptcy_questions = generator.generate_questions_for_bankruptcy(test_gaps)

    print(f"Generated {len(bankruptcy_questions)} bankruptcy questions:")
    for i, question in enumerate(bankruptcy_questions[:3], 1):  # Show first 3
        print(f"\n{i}. Question ID: {question.question_id}")
        print(f"   Text: {question.question_text}")
        print(f"   Why Needed: {question.why_needed}")
        print(f"   Input Type: {question.input_type.value}")
        print(f"   Category: {question.category}")
        print(f"   Priority: {question.priority}")
        if question.options:
            print(f"   Options: {len(question.options)} choices available")
        print(f"   Validations: {len(question.validations)} rules")
        print(f"   Disclaimer: {question.disclaimer_text[:50]}...")

    # Test litigation questions
    litigation_gaps = [
        InformationGap(
            gap_type="case_number",
            description="Court case number missing",
            severity=ViolationSeverity.HIGH,
            required_for=["litigation"],
            suggestions=["What is the case number?"]
        ),
        InformationGap(
            gap_type="party_info",
            description="Party information incomplete",
            severity=ViolationSeverity.CRITICAL,
            required_for=["litigation"],
            suggestions=["Who are the parties?"]
        ),
        InformationGap(
            gap_type="damages_sought",
            description="Damages amount not specified",
            severity=ViolationSeverity.HIGH,
            required_for=["litigation"],
            suggestions=["What damages are sought?"]
        )
    ]

    print(f"\n\nTESTING: Litigation Question Generation")
    litigation_questions = generator.generate_questions_for_litigation(litigation_gaps)

    print(f"Generated {len(litigation_questions)} litigation questions:")
    for i, question in enumerate(litigation_questions[:3], 1):  # Show first 3
        print(f"\n{i}. Question ID: {question.question_id}")
        print(f"   Text: {question.question_text}")
        print(f"   Why Needed: {question.why_needed}")
        print(f"   Input Type: {question.input_type.value}")
        print(f"   Category: {question.category}")
        if question.options:
            print(f"   Options: {[opt.label for opt in question.options]}")

    # Test dynamic follow-ups
    print(f"\n\nTESTING: Dynamic Follow-up Generation")
    sample_question = bankruptcy_questions[0]  # Use first bankruptcy question
    sample_answer = "$75000"  # High debt amount should trigger follow-ups

    follow_ups = generator.generate_dynamic_follow_ups(sample_question, sample_answer)
    print(f"Generated {len(follow_ups)} follow-up questions for answer '{sample_answer}'")

    for question in follow_ups:
        print(f"\nFollow-up: {question.question_text}")
        print(f"Why: {question.why_needed}")

    # Test validation
    print(f"\n\nTESTING: Validation System")
    currency_question = bankruptcy_questions[0]  # Should have currency validation
    test_values = ["$50000", "invalid", "", "-1000"]

    for validation in currency_question.validations:
        print(f"\nTesting validation rule: {validation.rule.value}")
        for test_value in test_values:
            is_valid, message = validation.validate(test_value)
            status = "[OK]" if is_valid else "[FAIL]"
            print(f"  {status} '{test_value}': {message}")

    print(f"\n=== TEST COMPLETE ===")
    print(f"Total questions generated: {len(bankruptcy_questions) + len(litigation_questions)}")
    print(f"System ready for document intake assistance.")
    print(f"\nREMINDER: All questions are for educational purposes only.")
    print(f"Users must consult qualified legal counsel for legal advice.")


if __name__ == "__main__":
    test_question_generator()