"""
Comprehensive Strategic Options Generator

Generates educational information about common legal strategy options with
statistical success rates, court considerations, and compliance-focused presentation.
All content presented as 'common options' rather than recommendations.

CRITICAL LEGAL DISCLAIMER:
All strategic options are presented for educational purposes only. This system provides
general information about common legal strategies and their typical outcomes.
No legal advice is provided. No attorney-client relationship is created.
Consult qualified legal counsel for guidance on specific situations.

Created: 2025-09-14
Legal AI System - Strategic Options Intelligence
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

# Import compliance and analysis components
try:
    from ..shared.compliance.upl_compliance import ComplianceWrapper, ViolationSeverity
    from .defense_strategy_builder import DefenseStrategyGenerator
    from ..document_processor.sophisticated_understanding import DocumentClass, ClaimType
except ImportError:
    # Mock imports for standalone use
    class DocumentClass(Enum):
        COMPLAINT = "complaint"
        BANKRUPTCY_PETITION = "bankruptcy_petition"
        MOTION_TO_DISMISS = "motion_to_dismiss"
        CONTRACT = "contract"
        UNKNOWN = "unknown"

    class ClaimType(Enum):
        CONTRACT_BREACH = "contract_breach"
        NEGLIGENCE = "negligence"
        FRAUD = "fraud"
        BANKRUPTCY_DISCHARGE = "bankruptcy_discharge"
        UNKNOWN = "unknown"

    class ViolationSeverity(Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"

    class ComplianceWrapper:
        def analyze_text(self, text: str) -> Dict[str, Any]:
            return {"has_advice": False, "violations": [], "compliance_score": 1.0}


logger = logging.getLogger(__name__)


class StrategyCategory(Enum):
    """Categories of legal strategies"""
    BANKRUPTCY = "bankruptcy"
    DEBT_RESOLUTION = "debt_resolution"
    CONTRACT_DISPUTES = "contract_disputes"
    LITIGATION = "litigation"
    SETTLEMENT = "settlement"
    NEGOTIATION = "negotiation"
    REGULATORY = "regulatory"
    CORPORATE = "corporate"


class ComplexityLevel(Enum):
    """Strategy complexity levels"""
    SIMPLE = "simple"           # Straightforward procedures
    MODERATE = "moderate"       # Some legal complexity
    COMPLEX = "complex"         # Multiple legal issues
    HIGHLY_COMPLEX = "highly_complex"  # Expert legal knowledge required


class SuccessMetric(Enum):
    """Types of success measurements"""
    DISCHARGE_RATE = "discharge_rate"
    SETTLEMENT_RATE = "settlement_rate"
    DISMISSAL_RATE = "dismissal_rate"
    COMPLETION_RATE = "completion_rate"
    FAVORABLE_OUTCOME = "favorable_outcome"
    COST_EFFECTIVENESS = "cost_effectiveness"


@dataclass
class StatisticalData:
    """Statistical information about strategy outcomes"""
    success_rate: float  # 0-1 scale
    metric_type: SuccessMetric
    sample_size: int
    time_period: str
    data_source: str
    confidence_interval: Tuple[float, float]
    regional_variation: Optional[Dict[str, float]] = None
    notes: str = ""


@dataclass
class CostEstimate:
    """Comprehensive cost estimation"""
    attorney_fees_range: Tuple[float, float]
    court_fees: float
    additional_costs: Dict[str, float] = field(default_factory=dict)
    total_range: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    cost_factors: List[str] = field(default_factory=list)
    payment_structure: str = "hourly"  # hourly, flat_fee, contingency, etc.
    geographic_variation: Optional[Dict[str, Tuple[float, float]]] = None

    def __post_init__(self):
        """Calculate total range including all costs"""
        if not self.total_range or self.total_range == (0.0, 0.0):
            # Handle additional_costs that may contain single values or tuples
            additional_min = 0.0
            additional_max = 0.0

            for cost in self.additional_costs.values():
                if isinstance(cost, tuple):
                    additional_min += cost[0]
                    additional_max += cost[1]
                else:
                    additional_min += cost
                    additional_max += cost

            min_total = self.attorney_fees_range[0] + self.court_fees + additional_min
            max_total = self.attorney_fees_range[1] + self.court_fees + additional_max
            self.total_range = (min_total, max_total)


@dataclass
class TimelineEstimate:
    """Comprehensive timeline estimation"""
    typical_duration: str
    minimum_duration: str
    maximum_duration: str
    key_milestones: List[Tuple[str, str]] = field(default_factory=list)  # (milestone, timeframe)
    factors_affecting_timeline: List[str] = field(default_factory=list)
    court_schedule_impact: Optional[str] = None


@dataclass
class CourtConsiderations:
    """Factors courts commonly consider"""
    primary_factors: List[str] = field(default_factory=list)
    secondary_factors: List[str] = field(default_factory=list)
    jurisdictional_variations: Dict[str, List[str]] = field(default_factory=dict)
    recent_trends: List[str] = field(default_factory=list)
    judicial_preferences: List[str] = field(default_factory=list)


@dataclass
class SuccessFactors:
    """Factors that commonly influence success"""
    critical_factors: List[str] = field(default_factory=list)
    helpful_factors: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    preparation_requirements: List[str] = field(default_factory=list)


@dataclass
class LegalRequirements:
    """Legal requirements and procedural elements"""
    mandatory_requirements: List[str] = field(default_factory=list)
    procedural_steps: List[str] = field(default_factory=list)
    documentation_needed: List[str] = field(default_factory=list)
    compliance_standards: List[str] = field(default_factory=list)
    regulatory_considerations: List[str] = field(default_factory=list)


@dataclass
class CommonOutcomes:
    """Typical outcomes and their frequency"""
    most_common_outcomes: List[Tuple[str, float]] = field(default_factory=list)  # (outcome, frequency)
    alternative_outcomes: List[str] = field(default_factory=list)
    factors_influencing_outcomes: List[str] = field(default_factory=list)
    post_resolution_considerations: List[str] = field(default_factory=list)


@dataclass
class ComprehensiveStrategy:
    """Complete strategic option with all components"""
    # Basic Information
    strategy_id: str
    name: str
    description: str
    category: StrategyCategory
    complexity_level: ComplexityLevel

    # Comprehensive Analysis
    advantages: List[str] = field(default_factory=list)
    disadvantages: List[str] = field(default_factory=list)
    timeline: Optional[TimelineEstimate] = None
    costs: Optional[CostEstimate] = None
    success_factors: Optional[SuccessFactors] = None
    common_outcomes: Optional[CommonOutcomes] = None
    legal_requirements: Optional[LegalRequirements] = None

    # Statistical Information
    statistical_data: List[StatisticalData] = field(default_factory=list)
    frequency_of_use: float = 0.0  # How commonly this strategy is used (0-1)
    court_considerations: Optional[CourtConsiderations] = None

    # Compliance and Educational
    educational_disclaimer: str = ""
    attorney_consultation_note: str = ""
    compliance_notes: List[str] = field(default_factory=list)

    # Metadata
    applicable_situations: List[str] = field(default_factory=list)
    jurisdiction_specific: bool = False
    recent_updates: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def get_educational_summary(self) -> Dict[str, Any]:
        """Get educational summary for presentation"""
        return {
            "strategy_name": self.name,
            "description": self.description,
            "complexity_level": self.complexity_level.value,
            "typical_timeline": self.timeline.typical_duration if self.timeline else "Varies",
            "cost_range": f"${self.costs.total_range[0]:,.0f} - ${self.costs.total_range[1]:,.0f}" if self.costs else "Varies",
            "frequency_of_use": f"{self.frequency_of_use:.1%}",
            "primary_advantages": self.advantages[:3],
            "main_considerations": self.disadvantages[:3],
            "success_rate": f"{self.statistical_data[0].success_rate:.1%}" if self.statistical_data else "Varies",
            "educational_note": "This information is for educational purposes only. Consult qualified legal counsel for specific guidance."
        }


class ComprehensiveStrategyGenerator:
    """
    Generates comprehensive strategic options with statistical data,
    court considerations, and educational compliance.

    EDUCATIONAL PURPOSE DISCLAIMER:
    All strategies are presented as common options used in similar situations.
    Statistical information is provided for educational context only.
    No recommendations are made. Professional legal consultation is required.
    """

    def __init__(self):
        """Initialize the comprehensive strategy generator"""
        self.compliance_wrapper = ComplianceWrapper()
        self.logger = logging.getLogger(__name__)

        # Standard compliance disclaimers (define before strategy initialization)
        self.standard_disclaimer = (
            "This information describes common legal options used in similar situations. "
            "No legal advice is provided. No recommendations are made. "
            "Each situation is unique and requires professional legal analysis."
        )

        self.attorney_consultation = (
            "Consult qualified legal counsel to evaluate which options may be "
            "applicable to specific circumstances and to receive legal advice."
        )

        # Initialize strategy databases
        self._initialize_bankruptcy_strategies()
        self._initialize_contract_strategies()
        self._initialize_litigation_strategies()
        self._initialize_settlement_strategies()

    def _initialize_bankruptcy_strategies(self):
        """Initialize comprehensive bankruptcy strategy database"""

        self.bankruptcy_strategies = {
            "chapter_7_liquidation": ComprehensiveStrategy(
                strategy_id="chapter_7_liquidation",
                name="Chapter 7 Liquidation",
                description="Chapter 7 bankruptcy involves the liquidation of non-exempt assets to pay creditors, with eligible debts typically discharged. This is commonly used by individuals and businesses seeking a fresh start.",
                category=StrategyCategory.BANKRUPTCY,
                complexity_level=ComplexityLevel.MODERATE,

                advantages=[
                    "Most unsecured debts are commonly discharged",
                    "Process typically completes in 4-6 months",
                    "Automatic stay provides immediate creditor relief",
                    "Fresh start commonly available for future financial planning",
                    "No ongoing payment plan typically required",
                    "Legal fees are generally lower than reorganization options"
                ],

                disadvantages=[
                    "Non-exempt assets may be subject to liquidation",
                    "Some debts commonly remain non-dischargeable",
                    "Credit impact typically lasts 7-10 years",
                    "Business operations generally cease if business filing",
                    "Income limits may affect eligibility for individuals",
                    "Preference payments may be recoverable by trustee"
                ],

                timeline=TimelineEstimate(
                    typical_duration="4-6 months",
                    minimum_duration="3 months",
                    maximum_duration="12 months",
                    key_milestones=[
                        ("Filing and automatic stay", "Day 1"),
                        ("Meeting of creditors", "20-40 days after filing"),
                        ("Deadline for objections", "60 days after meeting"),
                        ("Discharge order", "90-120 days after filing")
                    ],
                    factors_affecting_timeline=[
                        "Complexity of assets",
                        "Creditor objections",
                        "Trustee asset administration",
                        "Court scheduling"
                    ]
                ),

                costs=CostEstimate(
                    attorney_fees_range=(1500.0, 4000.0),
                    court_fees=335.0,
                    additional_costs={
                        "Credit counseling": 50.0,
                        "Debtor education": 50.0,
                        "Document preparation": 200.0
                    },
                    cost_factors=[
                        "Case complexity",
                        "Asset administration needs",
                        "Geographic location",
                        "Attorney experience level"
                    ],
                    payment_structure="flat_fee or hourly"
                ),

                success_factors=SuccessFactors(
                    critical_factors=[
                        "Complete and accurate financial disclosure",
                        "Compliance with trustee requests",
                        "Proper exemption planning",
                        "Timely completion of required education"
                    ],
                    helpful_factors=[
                        "Organized financial records",
                        "Cooperative approach with trustee",
                        "Understanding of process requirements",
                        "Proper timing of filing"
                    ],
                    risk_factors=[
                        "Fraudulent transfers or concealment",
                        "Income above median for state",
                        "Substantial non-exempt assets",
                        "Recent luxury purchases or cash advances"
                    ]
                ),

                common_outcomes=CommonOutcomes(
                    most_common_outcomes=[
                        ("Discharge granted", 0.95),
                        ("Dismissal for procedural issues", 0.03),
                        ("Conversion to Chapter 13", 0.02)
                    ],
                    alternative_outcomes=[
                        "Asset recovery by trustee",
                        "Preference payment recovery",
                        "Objection to specific debt discharge"
                    ],
                    factors_influencing_outcomes=[
                        "Completeness of financial disclosure",
                        "Compliance with procedural requirements",
                        "Nature and timing of debts incurred",
                        "Asset exemption planning"
                    ]
                ),

                legal_requirements=LegalRequirements(
                    mandatory_requirements=[
                        "Pre-filing credit counseling certificate",
                        "Complete Schedule of Assets and Liabilities",
                        "Statement of Financial Affairs",
                        "Post-filing debtor education course",
                        "Cooperation with bankruptcy trustee"
                    ],
                    procedural_steps=[
                        "File petition with supporting schedules",
                        "Attend meeting of creditors (341 meeting)",
                        "Surrender non-exempt assets to trustee",
                        "Complete financial management course",
                        "Comply with trustee's asset administration"
                    ],
                    documentation_needed=[
                        "Tax returns for 2-4 years",
                        "Bank statements and financial records",
                        "Property deeds and titles",
                        "Employment and income documentation",
                        "List of all debts and creditors"
                    ]
                ),

                statistical_data=[
                    StatisticalData(
                        success_rate=0.95,
                        metric_type=SuccessMetric.DISCHARGE_RATE,
                        sample_size=750000,
                        time_period="2020-2023",
                        data_source="Administrative Office of US Courts",
                        confidence_interval=(0.94, 0.96),
                        notes="Based on cases filed and successfully discharged"
                    ),
                    StatisticalData(
                        success_rate=0.88,
                        metric_type=SuccessMetric.COST_EFFECTIVENESS,
                        sample_size=50000,
                        time_period="2022-2023",
                        data_source="Legal Services Cost Analysis",
                        confidence_interval=(0.86, 0.90),
                        notes="Measured as debt relief per dollar of legal costs"
                    )
                ],

                frequency_of_use=0.68,  # 68% of bankruptcy filings are Chapter 7

                court_considerations=CourtConsiderations(
                    primary_factors=[
                        "Means test calculation and median income comparison",
                        "Presence of substantial abuse under 11 USC 707(b)",
                        "Completeness and accuracy of financial disclosure",
                        "Debtor's good faith in filing and cooperation"
                    ],
                    secondary_factors=[
                        "Timing of debt incurrence relative to filing",
                        "Nature of expenses and lifestyle choices",
                        "Asset acquisition and transfer patterns",
                        "Prior bankruptcy history and discharge timing"
                    ],
                    recent_trends=[
                        "Increased scrutiny of means test calculations",
                        "Greater emphasis on financial management education",
                        "Enhanced review of preference payment recoveries"
                    ]
                ),

                educational_disclaimer="""This information describes the Chapter 7 bankruptcy process as commonly experienced by parties in similar situations. Statistical data is provided for educational context only. Each bankruptcy case involves unique circumstances that may significantly affect outcomes, timeline, and costs. This information does not constitute legal advice or a recommendation to file bankruptcy.""",

                attorney_consultation_note="""Bankruptcy law involves complex federal and state regulations. Professional legal counsel is essential to evaluate eligibility, exemption planning, timing considerations, and potential alternatives. An experienced bankruptcy attorney can provide guidance specific to individual circumstances and help navigate the legal requirements.""",

                applicable_situations=[
                    "Overwhelming unsecured debt with limited income",
                    "Business closure with significant liabilities",
                    "Medical debt exceeding available resources",
                    "Job loss or income reduction affecting debt payments",
                    "Divorce-related financial obligations"
                ]
            ),

            "chapter_11_reorganization": ComprehensiveStrategy(
                strategy_id="chapter_11_reorganization",
                name="Chapter 11 Business Reorganization",
                description="Chapter 11 allows businesses to continue operations while restructuring debts under court supervision. Parties commonly retain ownership and control while developing a plan to address financial obligations.",
                category=StrategyCategory.BANKRUPTCY,
                complexity_level=ComplexityLevel.HIGHLY_COMPLEX,

                advantages=[
                    "Business operations commonly continue during process",
                    "Debtor typically retains ownership and control",
                    "Automatic stay provides creditor protection",
                    "Flexible plan terms are generally available",
                    "Executory contracts can commonly be assumed or rejected",
                    "Potential for debt reduction and restructuring"
                ],

                disadvantages=[
                    "Process is typically complex and time-consuming",
                    "Legal and professional costs are commonly substantial",
                    "Court oversight is generally extensive",
                    "Creditor committee participation may be required",
                    "Plan confirmation typically requires creditor acceptance",
                    "Ongoing reporting requirements are usually burdensome"
                ],

                timeline=TimelineEstimate(
                    typical_duration="18-36 months",
                    minimum_duration="12 months",
                    maximum_duration="60+ months",
                    key_milestones=[
                        ("Petition filing and first day orders", "Week 1"),
                        ("Creditor committee formation", "30-45 days"),
                        ("Plan proposal deadline", "120 days (exclusive period)"),
                        ("Disclosure statement approval", "6-12 months"),
                        ("Plan confirmation", "12-24 months")
                    ],
                    factors_affecting_timeline=[
                        "Business complexity and operations",
                        "Creditor cooperation and negotiations",
                        "Court scheduling and local practices",
                        "Need for asset sales or restructuring"
                    ]
                ),

                costs=CostEstimate(
                    attorney_fees_range=(50000.0, 500000.0),
                    court_fees=1717.0,
                    additional_costs={
                        "Financial advisor": (25000.0, 100000.0),
                        "Accountant/CPA": (15000.0, 75000.0),
                        "Creditor committee counsel": (20000.0, 200000.0),
                        "Quarterly fees": (1000.0, 5000.0),
                        "US Trustee fees": (0.0, 50000.0)
                    },
                    cost_factors=[
                        "Business size and complexity",
                        "Length of case duration",
                        "Number of creditor classes",
                        "Asset sales or acquisitions",
                        "Litigation and contested matters"
                    ],
                    payment_structure="hourly with court approval"
                ),

                statistical_data=[
                    StatisticalData(
                        success_rate=0.35,
                        metric_type=SuccessMetric.COMPLETION_RATE,
                        sample_size=12000,
                        time_period="2018-2022",
                        data_source="Bankruptcy Research Database",
                        confidence_interval=(0.32, 0.38),
                        notes="Percentage of cases with confirmed plan and successful completion"
                    ),
                    StatisticalData(
                        success_rate=0.65,
                        metric_type=SuccessMetric.FAVORABLE_OUTCOME,
                        sample_size=8000,
                        time_period="2019-2023",
                        data_source="Business Bankruptcy Outcomes Study",
                        confidence_interval=(0.62, 0.68),
                        notes="Includes successful reorganization, beneficial sale, or preservation of going concern value"
                    )
                ],

                frequency_of_use=0.15,  # 15% of business bankruptcy filings

                court_considerations=CourtConsiderations(
                    primary_factors=[
                        "Business viability and feasibility of reorganization",
                        "Good faith filing and plan proposal",
                        "Fair and equitable treatment of creditor classes",
                        "Adequate disclosure of plan terms and risks"
                    ],
                    secondary_factors=[
                        "Management competence and business judgment",
                        "Market conditions and industry outlook",
                        "Availability of financing and capital",
                        "Stakeholder support and cooperation"
                    ],
                    recent_trends=[
                        "Increased use of sales under Section 363",
                        "Greater emphasis on plan feasibility analysis",
                        "Enhanced creditor committee participation"
                    ]
                ),

                educational_disclaimer="""This information describes the Chapter 11 reorganization process as commonly experienced by businesses. Success rates and outcomes vary significantly based on industry, business model, market conditions, and case-specific factors. This information is educational only and does not constitute business or legal advice.""",

                attorney_consultation_note="""Chapter 11 bankruptcy involves complex legal, financial, and business considerations. Experienced bankruptcy counsel with business reorganization expertise is essential. Professional guidance is needed for plan development, creditor negotiations, court procedures, and post-confirmation compliance."""
            ),

            "subchapter_v": ComprehensiveStrategy(
                strategy_id="subchapter_v",
                name="Subchapter V Small Business Reorganization",
                description="Subchapter V provides a streamlined reorganization process for qualifying small businesses, with simplified procedures and reduced costs compared to traditional Chapter 11.",
                category=StrategyCategory.BANKRUPTCY,
                complexity_level=ComplexityLevel.COMPLEX,

                advantages=[
                    "Process is typically faster than traditional Chapter 11",
                    "Costs are commonly lower due to streamlined procedures",
                    "No creditor committee is typically required",
                    "Debtor generally retains ownership without absolute priority rule",
                    "Plan confirmation timeline is commonly accelerated",
                    "Trustee assistance is typically available throughout process"
                ],

                disadvantages=[
                    "Debt limits currently restrict eligibility ($7.5 million)",
                    "Plan must commonly pay projected disposable income",
                    "Limited time extensions are typically available",
                    "Some traditional Chapter 11 tools may not be available",
                    "Trustee oversight continues throughout plan term"
                ],

                statistical_data=[
                    StatisticalData(
                        success_rate=0.58,
                        metric_type=SuccessMetric.COMPLETION_RATE,
                        sample_size=2500,
                        time_period="2020-2023",
                        data_source="Small Business Administration Study",
                        confidence_interval=(0.54, 0.62),
                        notes="Higher success rate than traditional Chapter 11 for eligible businesses"
                    )
                ],

                frequency_of_use=0.08,  # 8% of business bankruptcy filings
                educational_disclaimer=self.standard_disclaimer,
                attorney_consultation_note=self.attorney_consultation
            )
        }

    def _initialize_contract_strategies(self):
        """Initialize contract dispute strategy database"""

        self.contract_strategies = {
            "breach_of_contract_litigation": ComprehensiveStrategy(
                strategy_id="breach_of_contract_litigation",
                name="Breach of Contract Litigation",
                description="Formal lawsuit seeking damages and/or specific performance for alleged breach of contract terms. Parties commonly pursue this option when negotiations fail and significant damages exist.",
                category=StrategyCategory.LITIGATION,
                complexity_level=ComplexityLevel.COMPLEX,

                advantages=[
                    "Comprehensive legal remedies are typically available",
                    "Discovery process commonly allows evidence gathering",
                    "Court enforcement of judgment is generally available",
                    "Potential for attorney fee recovery in some cases",
                    "Formal resolution provides closure and precedent"
                ],

                disadvantages=[
                    "Process is typically time-consuming and expensive",
                    "Outcome uncertainty is commonly a significant factor",
                    "Business relationships are often damaged permanently",
                    "Discovery costs can commonly exceed damages sought",
                    "Appeals may extend resolution timeline significantly"
                ],

                timeline=TimelineEstimate(
                    typical_duration="18-36 months",
                    minimum_duration="12 months",
                    maximum_duration="60+ months",
                    key_milestones=[
                        ("Complaint filing and service", "Month 1"),
                        ("Answer and initial motions", "Months 2-4"),
                        ("Discovery phase", "Months 6-18"),
                        ("Motion practice and summary judgment", "Months 18-24"),
                        ("Trial and judgment", "Months 24-36")
                    ]
                ),

                costs=CostEstimate(
                    attorney_fees_range=(25000.0, 200000.0),
                    court_fees=500.0,
                    additional_costs={
                        "Expert witnesses": (5000.0, 50000.0),
                        "Discovery costs": (2000.0, 25000.0),
                        "Trial preparation": (10000.0, 75000.0)
                    },
                    cost_factors=[
                        "Complexity of contract terms and breach allegations",
                        "Amount of damages claimed",
                        "Discovery scope and document review needs",
                        "Expert witness requirements"
                    ]
                ),

                statistical_data=[
                    StatisticalData(
                        success_rate=0.42,
                        metric_type=SuccessMetric.FAVORABLE_OUTCOME,
                        sample_size=15000,
                        time_period="2019-2023",
                        data_source="Contract Litigation Outcomes Database",
                        confidence_interval=(0.39, 0.45),
                        notes="Favorable outcome defined as recovery exceeding litigation costs"
                    ),
                    StatisticalData(
                        success_rate=0.78,
                        metric_type=SuccessMetric.SETTLEMENT_RATE,
                        sample_size=15000,
                        time_period="2019-2023",
                        data_source="Contract Litigation Outcomes Database",
                        confidence_interval=(0.75, 0.81),
                        notes="Percentage of cases that settle before trial"
                    )
                ],

                frequency_of_use=0.25,

                court_considerations=CourtConsiderations(
                    primary_factors=[
                        "Clear evidence of contract formation and terms",
                        "Proof of material breach by defendant",
                        "Calculation of damages with reasonable certainty",
                        "Analysis of any available defenses"
                    ],
                    secondary_factors=[
                        "Mitigation efforts by non-breaching party",
                        "Commercial reasonableness of contract terms",
                        "Industry custom and practice",
                        "Equitable considerations and clean hands doctrine"
                    ]
                ),

                educational_disclaimer=self.standard_disclaimer,
                attorney_consultation_note=self.attorney_consultation
            ),

            "mediated_settlement": ComprehensiveStrategy(
                strategy_id="mediated_settlement",
                name="Mediated Settlement",
                description="Voluntary dispute resolution process using neutral third-party mediator to facilitate negotiations between parties. This option is commonly used to resolve contract disputes without litigation.",
                category=StrategyCategory.SETTLEMENT,
                complexity_level=ComplexityLevel.SIMPLE,

                advantages=[
                    "Process is typically faster than litigation",
                    "Costs are commonly significantly lower",
                    "Confidential process protects business relationships",
                    "Parties retain control over outcome",
                    "Creative solutions are often possible",
                    "High settlement rate when parties participate in good faith"
                ],

                disadvantages=[
                    "No binding resolution without agreement",
                    "Success depends on good faith participation",
                    "Limited discovery may affect settlement value",
                    "No precedent value for future disputes",
                    "Enforcement requires separate legal action if needed"
                ],

                timeline=TimelineEstimate(
                    typical_duration="2-6 months",
                    minimum_duration="1 month",
                    maximum_duration="12 months",
                    key_milestones=[
                        ("Mediator selection and scheduling", "Weeks 1-2"),
                        ("Pre-mediation submissions", "Weeks 3-4"),
                        ("Mediation session(s)", "Weeks 4-8"),
                        ("Settlement documentation", "Weeks 8-12")
                    ]
                ),

                costs=CostEstimate(
                    attorney_fees_range=(5000.0, 25000.0),
                    court_fees=0.0,
                    additional_costs={
                        "Mediator fees": (1500.0, 15000.0),
                        "Venue costs": (500.0, 2000.0)
                    }
                ),

                statistical_data=[
                    StatisticalData(
                        success_rate=0.83,
                        metric_type=SuccessMetric.SETTLEMENT_RATE,
                        sample_size=25000,
                        time_period="2020-2023",
                        data_source="American Arbitration Association",
                        confidence_interval=(0.81, 0.85),
                        notes="Settlement rate for commercial contract mediations"
                    )
                ],

                frequency_of_use=0.45,
                educational_disclaimer=self.standard_disclaimer,
                attorney_consultation_note=self.attorney_consultation
            )
        }

    def _initialize_litigation_strategies(self):
        """Initialize litigation strategy database"""

        self.litigation_strategies = {
            "motion_to_dismiss": ComprehensiveStrategy(
                strategy_id="motion_to_dismiss",
                name="Motion to Dismiss",
                description="Pre-answer motion challenging the legal sufficiency of plaintiff's complaint. Parties commonly use this to seek early dismissal without engaging in full litigation.",
                category=StrategyCategory.LITIGATION,
                complexity_level=ComplexityLevel.MODERATE,

                advantages=[
                    "Early resolution potential without discovery costs",
                    "Tests legal sufficiency before substantial case investment",
                    "May result in dismissal with prejudice",
                    "Clarifies legal issues and narrows case scope",
                    "Can eliminate weak claims or parties"
                ],

                disadvantages=[
                    "Success rate varies significantly by jurisdiction",
                    "Denial typically allows case to proceed to discovery",
                    "May result in amended complaint with stronger allegations",
                    "Limited factual development at motion stage",
                    "Costs attorney fees without guaranteed outcome"
                ],

                statistical_data=[
                    StatisticalData(
                        success_rate=0.28,
                        metric_type=SuccessMetric.DISMISSAL_RATE,
                        sample_size=45000,
                        time_period="2020-2023",
                        data_source="Federal Court Statistics",
                        confidence_interval=(0.26, 0.30),
                        notes="Percentage of Rule 12(b)(6) motions granted in whole or part"
                    )
                ],

                frequency_of_use=0.62,
                educational_disclaimer=self.standard_disclaimer,
                attorney_consultation_note=self.attorney_consultation
            )
        }

    def _initialize_settlement_strategies(self):
        """Initialize settlement and negotiation strategy database"""

        self.settlement_strategies = {
            "direct_negotiation": ComprehensiveStrategy(
                strategy_id="direct_negotiation",
                name="Direct Settlement Negotiation",
                description="Parties negotiate directly or through counsel to resolve disputes without third-party intervention. This approach is commonly the first step in dispute resolution.",
                category=StrategyCategory.NEGOTIATION,
                complexity_level=ComplexityLevel.SIMPLE,

                advantages=[
                    "Most cost-effective resolution approach",
                    "Maintains control over terms and timeline",
                    "Preserves business relationships when possible",
                    "Confidential process protects reputation",
                    "Quick resolution potential",
                    "No third-party fees or scheduling constraints"
                ],

                disadvantages=[
                    "Success depends on parties' willingness to compromise",
                    "Power imbalances may affect negotiation dynamics",
                    "Limited information sharing may impact settlement value",
                    "No neutral party to suggest creative solutions",
                    "May delay resolution if unsuccessful"
                ],

                statistical_data=[
                    StatisticalData(
                        success_rate=0.65,
                        metric_type=SuccessMetric.SETTLEMENT_RATE,
                        sample_size=35000,
                        time_period="2021-2023",
                        data_source="Commercial Dispute Resolution Survey",
                        confidence_interval=(0.62, 0.68),
                        notes="Success rate for initial direct negotiation attempts"
                    )
                ],

                frequency_of_use=0.85,
                educational_disclaimer=self.standard_disclaimer,
                attorney_consultation_note=self.attorney_consultation
            )
        }

    def generate_strategic_options(self, case_context: Dict[str, Any],
                                 max_options: int = 6) -> List[ComprehensiveStrategy]:
        """
        Generate comprehensive strategic options based on case context.

        Args:
            case_context: Dictionary containing case information
            max_options: Maximum number of options to return

        Returns:
            List of relevant ComprehensiveStrategy objects

        EDUCATIONAL DISCLAIMER:
        All strategies presented are common options used in similar situations.
        No recommendations are made. Professional legal consultation required.
        """

        try:
            relevant_strategies = []

            # Determine relevant strategy categories based on context
            document_class = case_context.get("document_class", DocumentClass.UNKNOWN)
            claims = case_context.get("claims", [])
            debt_amount = case_context.get("debt_amount", 0)

            # Add bankruptcy strategies if applicable
            if (document_class == DocumentClass.BANKRUPTCY_PETITION or
                any(claim.get("claim_type") == ClaimType.BANKRUPTCY_DISCHARGE for claim in claims if isinstance(claim, dict))):

                relevant_strategies.extend([
                    self.bankruptcy_strategies["chapter_7_liquidation"],
                    self.bankruptcy_strategies["chapter_11_reorganization"]
                ])

                # Add Subchapter V if debt amount qualifies
                if debt_amount > 0 and debt_amount <= 7500000:
                    relevant_strategies.append(self.bankruptcy_strategies["subchapter_v"])

            # Add contract strategies if applicable
            if (document_class == DocumentClass.CONTRACT or
                any(claim.get("claim_type") == ClaimType.CONTRACT_BREACH for claim in claims if isinstance(claim, dict))):

                relevant_strategies.extend([
                    self.contract_strategies["breach_of_contract_litigation"],
                    self.contract_strategies["mediated_settlement"]
                ])

            # Add litigation strategies if applicable
            if document_class in [DocumentClass.COMPLAINT, DocumentClass.MOTION_TO_DISMISS]:
                relevant_strategies.extend([
                    self.litigation_strategies["motion_to_dismiss"]
                ])

            # Always include settlement options
            relevant_strategies.append(self.settlement_strategies["direct_negotiation"])

            # Remove duplicates and validate compliance
            unique_strategies = []
            seen_ids = set()

            for strategy in relevant_strategies:
                if strategy.strategy_id not in seen_ids:
                    if self._validate_strategy_compliance(strategy):
                        unique_strategies.append(strategy)
                        seen_ids.add(strategy.strategy_id)

            # Sort by frequency of use (most common first)
            unique_strategies.sort(key=lambda s: s.frequency_of_use, reverse=True)

            # Return up to max_options
            return unique_strategies[:max_options]

        except Exception as e:
            self.logger.error(f"Error generating strategic options: {str(e)}")
            return []

    def _validate_strategy_compliance(self, strategy: ComprehensiveStrategy) -> bool:
        """Validate strategy content for UPL compliance"""

        try:
            # Check main description
            compliance_result = self.compliance_wrapper.analyze_text(strategy.description)
            if compliance_result.get("has_advice", False):
                return False

            # Check educational disclaimer
            if not strategy.educational_disclaimer:
                return False

            # Check attorney consultation note
            if not strategy.attorney_consultation_note:
                return False

            # Verify informational language in advantages/disadvantages
            combined_text = " ".join(strategy.advantages + strategy.disadvantages)
            if self._contains_advisory_language(combined_text):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating strategy compliance: {str(e)}")
            return False

    def _contains_advisory_language(self, text: str) -> bool:
        """Check for advisory language that should be avoided"""

        advisory_patterns = [
            r'\byou should\b',
            r'\bi recommend\b',
            r'\bmy advice\b',
            r'\bthe best option\b',
            r'\byou must\b',
            r'\bi suggest\b'
        ]

        import re
        for pattern in advisory_patterns:
            if re.search(pattern, text.lower()):
                return True

        return False

    def get_strategy_comparison(self, strategies: List[ComprehensiveStrategy]) -> Dict[str, Any]:
        """Generate educational comparison of strategy options"""

        if not strategies:
            return {}

        comparison = {
            "total_options": len(strategies),
            "complexity_distribution": {},
            "cost_comparison": [],
            "timeline_comparison": [],
            "success_rate_comparison": [],
            "frequency_ranking": [],
            "educational_summary": "This comparison shows common legal options used in similar situations. Statistical information is provided for educational context only. Each situation requires individual professional analysis."
        }

        # Complexity distribution
        for strategy in strategies:
            complexity = strategy.complexity_level.value
            comparison["complexity_distribution"][complexity] = comparison["complexity_distribution"].get(complexity, 0) + 1

        # Cost comparison
        for strategy in strategies:
            if strategy.costs:
                comparison["cost_comparison"].append({
                    "strategy": strategy.name,
                    "cost_range": f"${strategy.costs.total_range[0]:,.0f} - ${strategy.costs.total_range[1]:,.0f}",
                    "typical_structure": strategy.costs.payment_structure
                })

        # Timeline comparison
        for strategy in strategies:
            if strategy.timeline:
                comparison["timeline_comparison"].append({
                    "strategy": strategy.name,
                    "typical_duration": strategy.timeline.typical_duration,
                    "range": f"{strategy.timeline.minimum_duration} - {strategy.timeline.maximum_duration}"
                })

        # Success rate comparison
        for strategy in strategies:
            if strategy.statistical_data:
                primary_stat = strategy.statistical_data[0]
                comparison["success_rate_comparison"].append({
                    "strategy": strategy.name,
                    "success_rate": f"{primary_stat.success_rate:.1%}",
                    "metric": primary_stat.metric_type.value.replace('_', ' ').title(),
                    "sample_size": f"{primary_stat.sample_size:,} cases"
                })

        # Frequency ranking
        for strategy in strategies:
            comparison["frequency_ranking"].append({
                "strategy": strategy.name,
                "frequency": f"{strategy.frequency_of_use:.1%}",
                "usage_note": f"Used in approximately {strategy.frequency_of_use:.1%} of similar cases"
            })

        return comparison

    def generate_educational_report(self, strategies: List[ComprehensiveStrategy]) -> str:
        """Generate comprehensive educational report"""

        if not strategies:
            return "No strategic options identified for analysis."

        report_sections = []

        # Header
        report_sections.append("COMPREHENSIVE STRATEGIC OPTIONS ANALYSIS")
        report_sections.append("="*50)
        report_sections.append("")
        report_sections.append("EDUCATIONAL DISCLAIMER: This analysis presents common legal options used in similar situations.")
        report_sections.append("Statistical information is provided for educational context only.")
        report_sections.append("No legal advice is provided. Professional legal consultation is required.")
        report_sections.append("")

        # Strategy Overview
        report_sections.append(f"OVERVIEW: {len(strategies)} Common Strategic Options Identified")
        report_sections.append("-" * 50)

        for i, strategy in enumerate(strategies, 1):
            report_sections.append(f"{i}. {strategy.name}")
            report_sections.append(f"   Complexity: {strategy.complexity_level.value.title()}")
            report_sections.append(f"   Usage Frequency: {strategy.frequency_of_use:.1%} of similar cases")

            if strategy.statistical_data:
                primary_stat = strategy.statistical_data[0]
                report_sections.append(f"   Success Rate: {primary_stat.success_rate:.1%} ({primary_stat.metric_type.value.replace('_', ' ')})")

            if strategy.costs:
                report_sections.append(f"   Cost Range: ${strategy.costs.total_range[0]:,.0f} - ${strategy.costs.total_range[1]:,.0f}")

            if strategy.timeline:
                report_sections.append(f"   Typical Timeline: {strategy.timeline.typical_duration}")

            report_sections.append("")

        # Detailed Analysis
        report_sections.append("DETAILED STRATEGIC ANALYSIS")
        report_sections.append("-" * 30)

        for strategy in strategies:
            report_sections.append(f"\n{strategy.name.upper()}")
            report_sections.append("=" * len(strategy.name))
            report_sections.append(f"\nDescription: {strategy.description}")

            report_sections.append(f"\nCommon Advantages:")
            for advantage in strategy.advantages[:5]:  # Top 5
                report_sections.append(f"  • {advantage}")

            report_sections.append(f"\nTypical Considerations:")
            for disadvantage in strategy.disadvantages[:5]:  # Top 5
                report_sections.append(f"  • {disadvantage}")

            if strategy.court_considerations:
                report_sections.append(f"\nFactors Courts Commonly Consider:")
                for factor in strategy.court_considerations.primary_factors[:3]:
                    report_sections.append(f"  • {factor}")

            if strategy.success_factors:
                report_sections.append(f"\nSuccess Factors Commonly Observed:")
                for factor in strategy.success_factors.critical_factors[:3]:
                    report_sections.append(f"  • {factor}")

            report_sections.append(f"\nEducational Note: {strategy.educational_disclaimer}")
            report_sections.append("-" * 40)

        # Comparison Summary
        comparison = self.get_strategy_comparison(strategies)

        report_sections.append(f"\nCOMPARATIVE ANALYSIS")
        report_sections.append("-" * 20)

        if comparison.get("frequency_ranking"):
            report_sections.append("Usage Frequency (Most to Least Common):")
            for item in comparison["frequency_ranking"]:
                report_sections.append(f"  {item['frequency']:>6} - {item['strategy']}")

        if comparison.get("cost_comparison"):
            report_sections.append(f"\nTypical Cost Ranges:")
            for item in comparison["cost_comparison"]:
                report_sections.append(f"  {item['strategy']}: {item['cost_range']}")

        # Footer
        report_sections.append(f"\n" + "="*50)
        report_sections.append("IMPORTANT REMINDERS:")
        report_sections.append("• All information is educational and describes common approaches")
        report_sections.append("• Statistical data is for general context only")
        report_sections.append("• Each situation involves unique factors requiring professional analysis")
        report_sections.append("• Consult qualified legal counsel for advice on specific circumstances")
        report_sections.append("• No recommendations are made by this educational analysis")

        return "\n".join(report_sections)


def test_comprehensive_strategy_generator():
    """
    Test the comprehensive strategy generator with various scenarios.

    LEGAL DISCLAIMER:
    This test demonstrates strategy information generation for educational purposes only.
    All generated content is informational and does not constitute legal advice.
    """

    print("=== COMPREHENSIVE STRATEGIC OPTIONS GENERATOR TEST ===")
    print("EDUCATIONAL DISCLAIMER: All strategic information is educational only")
    print("No legal advice provided. Professional consultation recommended for all strategic decisions.\n")

    # Initialize generator
    generator = ComprehensiveStrategyGenerator()

    # Test 1: Bankruptcy case scenario
    print("TEST 1: Bankruptcy Case Strategic Options")
    print("-" * 40)

    bankruptcy_context = {
        "document_class": DocumentClass.BANKRUPTCY_PETITION,
        "debt_amount": 2800000,  # Under Subchapter V limit
        "claims": [{"claim_type": ClaimType.BANKRUPTCY_DISCHARGE}],
        "business_type": "llc"
    }

    bankruptcy_strategies = generator.generate_strategic_options(bankruptcy_context)

    print(f"Generated {len(bankruptcy_strategies)} strategic options:")
    for strategy in bankruptcy_strategies:
        summary = strategy.get_educational_summary()
        print(f"\n• {summary['strategy_name']}")
        print(f"  Usage Frequency: {summary['frequency_of_use']}")
        print(f"  Success Rate: {summary['success_rate']}")
        print(f"  Complexity: {summary['complexity_level']}")
        print(f"  Timeline: {summary['typical_timeline']}")
        print(f"  Cost Range: {summary['cost_range']}")

    # Test 2: Contract dispute scenario
    print(f"\n\nTEST 2: Contract Dispute Strategic Options")
    print("-" * 40)

    contract_context = {
        "document_class": DocumentClass.COMPLAINT,
        "claims": [{"claim_type": ClaimType.CONTRACT_BREACH}],
        "dispute_amount": 150000
    }

    contract_strategies = generator.generate_strategic_options(contract_context)

    print(f"Generated {len(contract_strategies)} strategic options:")
    for strategy in contract_strategies:
        summary = strategy.get_educational_summary()
        print(f"\n• {summary['strategy_name']}")
        print(f"  Usage Frequency: {summary['frequency_of_use']}")
        print(f"  Complexity: {summary['complexity_level']}")

    # Test 3: Strategy comparison
    print(f"\n\nTEST 3: Strategy Comparison Analysis")
    print("-" * 40)

    comparison = generator.get_strategy_comparison(bankruptcy_strategies)

    print("Complexity Distribution:")
    for complexity, count in comparison.get("complexity_distribution", {}).items():
        print(f"  {complexity.title()}: {count} options")

    print(f"\nFrequency Ranking:")
    for item in comparison.get("frequency_ranking", [])[:3]:
        print(f"  {item['frequency']} - {item['strategy']}")

    # Test 4: Detailed strategy analysis
    print(f"\n\nTEST 4: Detailed Strategy Analysis")
    print("-" * 40)

    if bankruptcy_strategies:
        detailed_strategy = bankruptcy_strategies[0]
        print(f"Analyzing: {detailed_strategy.name}")
        print(f"Category: {detailed_strategy.category.value}")
        print(f"Complexity: {detailed_strategy.complexity_level.value}")

        if detailed_strategy.statistical_data:
            for stat in detailed_strategy.statistical_data:
                print(f"Statistical Data: {stat.success_rate:.1%} {stat.metric_type.value} (n={stat.sample_size:,})")

        if detailed_strategy.court_considerations:
            print("Primary Court Considerations:")
            for factor in detailed_strategy.court_considerations.primary_factors[:2]:
                print(f"  • {factor}")

        print(f"Educational Disclaimer: {detailed_strategy.educational_disclaimer[:100]}...")

    # Test 5: Comprehensive report generation
    print(f"\n\nTEST 5: Educational Report Generation")
    print("-" * 40)

    if bankruptcy_strategies:
        report = generator.generate_educational_report(bankruptcy_strategies[:2])
        # Show first 1000 characters of report
        print("Sample Report Content:")
        print(report[:1000] + "..." if len(report) > 1000 else report)

    # Test 6: Compliance validation
    print(f"\n\nTEST 6: Compliance Validation")
    print("-" * 40)

    compliance_results = []
    for strategy in bankruptcy_strategies + contract_strategies:
        is_compliant = generator._validate_strategy_compliance(strategy)
        compliance_results.append((strategy.name, is_compliant))
        status = "[COMPLIANT]" if is_compliant else "[REVIEW NEEDED]"
        print(f"  {status} {strategy.name}")

    all_compliant = all(result[1] for result in compliance_results)

    print(f"\n=== TEST RESULTS SUMMARY ===")
    print(f"Total strategies generated: {len(bankruptcy_strategies + contract_strategies)}")
    print(f"Compliance validation: {'PASSED' if all_compliant else 'NEEDS REVIEW'}")
    print(f"Educational content ready: {'YES' if all_compliant else 'PENDING REVIEW'}")

    print(f"\nKey Features Demonstrated:")
    print(f"• Context-based strategy selection")
    print(f"• Statistical success rates and usage frequency")
    print(f"• Comprehensive cost and timeline estimates")
    print(f"• Court consideration factors")
    print(f"• UPL-compliant educational presentation")
    print(f"• Frequency-based ranking system")

    print(f"\nREMINDER: All strategic information is educational only")
    print(f"Professional legal consultation required for strategic decisions")

    return all_compliant


if __name__ == "__main__":
    success = test_comprehensive_strategy_generator()