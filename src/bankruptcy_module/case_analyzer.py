"""
Chapter 11 bankruptcy case analyzer for comprehensive case assessment.
Analyzes financial data, legal documents, and procedural compliance.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import re
from decimal import Decimal
from collections import defaultdict

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class CaseStatus(Enum):
    """Chapter 11 case status options."""
    FILED = "filed"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    SUBSTANTIAL_CONSUMMATION = "substantial_consummation"
    CONVERTED = "converted"
    DISMISSED = "dismissed"
    CLOSED = "closed"


class DebtorType(Enum):
    """Types of Chapter 11 debtors."""
    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    PARTNERSHIP = "partnership"
    LLC = "llc"
    SMALL_BUSINESS = "small_business"
    SINGLE_ASSET_REAL_ESTATE = "single_asset_real_estate"
    SUBCHAPTER_V = "subchapter_v"


class PriorityLevel(Enum):
    """Priority levels for bankruptcy claims and issues."""
    CRITICAL = "critical"        # Immediate attention required
    HIGH = "high"               # Address within days
    MEDIUM = "medium"           # Address within weeks
    LOW = "low"                 # Address when convenient
    INFORMATIONAL = "informational"  # For reference only


class RiskLevel(Enum):
    """Risk assessment levels."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class FinancialMetrics:
    """Key financial metrics for bankruptcy case analysis."""
    # Assets
    total_assets: Decimal = Decimal('0')
    liquid_assets: Decimal = Decimal('0')
    real_estate: Decimal = Decimal('0')
    equipment: Decimal = Decimal('0')
    inventory: Decimal = Decimal('0')
    accounts_receivable: Decimal = Decimal('0')
    
    # Liabilities
    total_liabilities: Decimal = Decimal('0')
    secured_debt: Decimal = Decimal('0')
    unsecured_debt: Decimal = Decimal('0')
    priority_debt: Decimal = Decimal('0')
    contingent_liabilities: Decimal = Decimal('0')
    
    # Operations
    monthly_revenue: Decimal = Decimal('0')
    monthly_expenses: Decimal = Decimal('0')
    monthly_cash_flow: Decimal = Decimal('0')
    
    # Ratios (calculated)
    debt_to_asset_ratio: float = 0.0
    current_ratio: float = 0.0
    debt_service_coverage: float = 0.0
    
    def __post_init__(self):
        """Calculate derived financial ratios."""
        # Debt-to-asset ratio
        if self.total_assets > 0:
            self.debt_to_asset_ratio = float(self.total_liabilities / self.total_assets)
        
        # Current ratio (simplified)
        if self.total_liabilities > 0:
            self.current_ratio = float(self.liquid_assets / self.total_liabilities)
        
        # Debt service coverage
        if self.monthly_expenses > 0:
            self.debt_service_coverage = float(self.monthly_cash_flow / self.monthly_expenses)


@dataclass
class CaseAssessment:
    """Comprehensive assessment of Chapter 11 case."""
    case_id: str
    debtor_name: str
    case_status: CaseStatus
    debtor_type: DebtorType
    
    # Financial analysis
    financial_metrics: FinancialMetrics
    
    # Case characteristics
    filing_date: datetime
    confirmation_deadline: Optional[datetime] = None
    exclusivity_deadline: Optional[datetime] = None
    
    # Key issues and risks
    critical_issues: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    compliance_issues: List[str] = field(default_factory=list)
    
    # Stakeholder analysis
    creditor_count: int = 0
    employee_count: int = 0
    has_union: bool = False
    has_pension_obligations: bool = False
    
    # Procedural status
    plan_filed: bool = False
    disclosure_statement_filed: bool = False
    confirmation_hearing_scheduled: bool = False
    
    # Analysis results
    reorganization_feasibility: float = 0.0  # 0-1 score
    liquidation_value: Decimal = Decimal('0')
    going_concern_value: Decimal = Decimal('0')
    
    # Recommendations
    priority_actions: List[str] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    analyst_notes: str = ""


@dataclass
class ComplianceCheck:
    """Bankruptcy code compliance check result."""
    check_id: str
    requirement: str
    status: str  # compliant, non_compliant, unclear, not_applicable
    priority: PriorityLevel
    description: str
    deadline: Optional[datetime] = None
    remediation_steps: List[str] = field(default_factory=list)
    risk_if_non_compliant: RiskLevel = RiskLevel.MEDIUM
    
    # Evidence and documentation
    supporting_evidence: List[str] = field(default_factory=list)
    relevant_code_sections: List[str] = field(default_factory=list)
    case_law_references: List[str] = field(default_factory=list)


@dataclass
class StakeholderAnalysis:
    """Analysis of key stakeholders in bankruptcy case."""
    stakeholder_type: str
    name: str
    role: str
    influence_level: str  # high, medium, low
    cooperation_level: str  # supportive, neutral, adversarial
    key_interests: List[str] = field(default_factory=list)
    potential_objections: List[str] = field(default_factory=list)
    negotiation_strategy: str = ""


class BankruptcyCaseAnalyzer:
    """Comprehensive Chapter 11 bankruptcy case analyzer."""
    
    def __init__(self):
        """Initialize bankruptcy case analyzer."""
        
        # Bankruptcy code requirements and deadlines
        self.code_requirements = {
            'plan_filing': {
                'deadline_days': 120,  # Exclusive period for debtor
                'description': 'Debtor has exclusive right to file plan',
                'code_section': '11 U.S.C. § 1121(b)',
                'priority': PriorityLevel.HIGH
            },
            'disclosure_statement': {
                'description': 'Disclosure statement must be filed with or before plan',
                'code_section': '11 U.S.C. § 1125',
                'priority': PriorityLevel.HIGH
            },
            'monthly_operating_reports': {
                'deadline_days': 20,  # 20th of each month
                'description': 'Monthly operating reports required',
                'code_section': 'Fed. R. Bankr. P. 2015',
                'priority': PriorityLevel.MEDIUM
            },
            'quarterly_fees': {
                'deadline_days': 30,  # Within 30 days after end of quarter
                'description': 'Quarterly fees to U.S. Trustee',
                'code_section': '28 U.S.C. § 1930(a)(6)',
                'priority': PriorityLevel.HIGH
            },
            'insurance_coverage': {
                'description': 'Maintain adequate insurance coverage',
                'code_section': '11 U.S.C. § 1112(b)',
                'priority': PriorityLevel.MEDIUM
            },
            'bank_account_authorization': {
                'description': 'Court authorization required for new bank accounts',
                'code_section': '11 U.S.C. § 345',
                'priority': PriorityLevel.HIGH
            }
        }
        
        # Financial distress indicators
        self.distress_indicators = {
            'debt_to_asset_ratio': {'threshold': 0.8, 'weight': 0.3},
            'current_ratio': {'threshold': 1.0, 'weight': 0.25, 'inverse': True},
            'debt_service_coverage': {'threshold': 1.2, 'weight': 0.25, 'inverse': True},
            'cash_flow_negative': {'weight': 0.2}
        }
        
        # Industry benchmarks (simplified)
        self.industry_benchmarks = {
            'retail': {
                'debt_to_asset_ratio': 0.6,
                'current_ratio': 1.5,
                'debt_service_coverage': 1.3
            },
            'manufacturing': {
                'debt_to_asset_ratio': 0.65,
                'current_ratio': 1.2,
                'debt_service_coverage': 1.4
            },
            'real_estate': {
                'debt_to_asset_ratio': 0.75,
                'current_ratio': 0.8,
                'debt_service_coverage': 1.1
            },
            'technology': {
                'debt_to_asset_ratio': 0.4,
                'current_ratio': 2.0,
                'debt_service_coverage': 1.8
            }
        }
    
    def analyze_case(self, case_data: Dict[str, Any]) -> CaseAssessment:
        """Perform comprehensive analysis of Chapter 11 case.
        
        Args:
            case_data: Dictionary containing case information and financial data
            
        Returns:
            Comprehensive case assessment
        """
        logger.info(f"Analyzing Chapter 11 case: {case_data.get('case_id', 'Unknown')}")
        
        # Extract basic case information
        assessment = self._create_base_assessment(case_data)
        
        # Analyze financial condition
        assessment.financial_metrics = self._analyze_financial_metrics(case_data.get('financial_data', {}))
        
        # Assess reorganization feasibility
        assessment.reorganization_feasibility = self._assess_reorganization_feasibility(assessment)
        
        # Identify critical issues
        assessment.critical_issues = self._identify_critical_issues(assessment, case_data)
        
        # Analyze risk factors
        assessment.risk_factors = self._analyze_risk_factors(assessment, case_data)
        
        # Check compliance
        assessment.compliance_issues = self._check_compliance(assessment, case_data)
        
        # Calculate liquidation vs going concern value
        assessment.liquidation_value, assessment.going_concern_value = self._calculate_valuations(assessment)
        
        # Generate recommendations
        assessment.priority_actions, assessment.strategic_recommendations = self._generate_recommendations(assessment)
        
        return assessment
    
    def _create_base_assessment(self, case_data: Dict[str, Any]) -> CaseAssessment:
        """Create base case assessment from provided data."""
        
        # Parse filing date
        filing_date = datetime.utcnow()
        if 'filing_date' in case_data:
            if isinstance(case_data['filing_date'], str):
                filing_date = datetime.fromisoformat(case_data['filing_date'].replace('Z', '+00:00'))
            elif isinstance(case_data['filing_date'], datetime):
                filing_date = case_data['filing_date']
        
        # Calculate key deadlines
        confirmation_deadline = None
        exclusivity_deadline = None
        
        if filing_date:
            # Standard exclusivity period is 120 days
            exclusivity_deadline = filing_date + timedelta(days=120)
            # Confirmation deadline is typically extended, but start with 18 months
            confirmation_deadline = filing_date + timedelta(days=540)
        
        return CaseAssessment(
            case_id=case_data.get('case_id', 'Unknown'),
            debtor_name=case_data.get('debtor_name', 'Unknown Debtor'),
            case_status=CaseStatus(case_data.get('case_status', 'filed')),
            debtor_type=DebtorType(case_data.get('debtor_type', 'corporation')),
            financial_metrics=FinancialMetrics(),  # Will be populated separately
            filing_date=filing_date,
            confirmation_deadline=confirmation_deadline,
            exclusivity_deadline=exclusivity_deadline,
            creditor_count=case_data.get('creditor_count', 0),
            employee_count=case_data.get('employee_count', 0),
            has_union=case_data.get('has_union', False),
            has_pension_obligations=case_data.get('has_pension_obligations', False),
            plan_filed=case_data.get('plan_filed', False),
            disclosure_statement_filed=case_data.get('disclosure_statement_filed', False),
            confirmation_hearing_scheduled=case_data.get('confirmation_hearing_scheduled', False)
        )
    
    def _analyze_financial_metrics(self, financial_data: Dict[str, Any]) -> FinancialMetrics:
        """Analyze financial metrics from provided data."""
        
        # Convert string values to Decimal
        def to_decimal(value, default=0):
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = re.sub(r'[\$,]', '', value)
                try:
                    return Decimal(cleaned)
                except:
                    return Decimal(str(default))
            return Decimal(str(default))
        
        metrics = FinancialMetrics(
            # Assets
            total_assets=to_decimal(financial_data.get('total_assets')),
            liquid_assets=to_decimal(financial_data.get('liquid_assets')),
            real_estate=to_decimal(financial_data.get('real_estate')),
            equipment=to_decimal(financial_data.get('equipment')),
            inventory=to_decimal(financial_data.get('inventory')),
            accounts_receivable=to_decimal(financial_data.get('accounts_receivable')),
            
            # Liabilities
            total_liabilities=to_decimal(financial_data.get('total_liabilities')),
            secured_debt=to_decimal(financial_data.get('secured_debt')),
            unsecured_debt=to_decimal(financial_data.get('unsecured_debt')),
            priority_debt=to_decimal(financial_data.get('priority_debt')),
            contingent_liabilities=to_decimal(financial_data.get('contingent_liabilities')),
            
            # Operations
            monthly_revenue=to_decimal(financial_data.get('monthly_revenue')),
            monthly_expenses=to_decimal(financial_data.get('monthly_expenses')),
        )
        
        # Calculate cash flow
        metrics.monthly_cash_flow = metrics.monthly_revenue - metrics.monthly_expenses
        
        return metrics
    
    def _assess_reorganization_feasibility(self, assessment: CaseAssessment) -> float:
        """Assess the feasibility of successful reorganization."""
        
        score = 0.0
        max_score = 0.0
        
        metrics = assessment.financial_metrics
        
        # Financial health factors
        financial_factors = [
            # Positive cash flow is critical
            {
                'condition': metrics.monthly_cash_flow > 0,
                'weight': 0.25,
                'score': 1.0 if metrics.monthly_cash_flow > 0 else 0.0
            },
            # Reasonable debt-to-asset ratio
            {
                'weight': 0.2,
                'score': max(0, 1 - (metrics.debt_to_asset_ratio - 0.5) / 0.5) if metrics.debt_to_asset_ratio > 0 else 0.5
            },
            # Adequate liquidity
            {
                'weight': 0.15,
                'score': min(1.0, float(metrics.liquid_assets / max(metrics.monthly_expenses, Decimal('1'))))
            },
            # Asset base
            {
                'weight': 0.15,
                'score': 1.0 if metrics.total_assets > metrics.total_liabilities else 0.3
            }
        ]
        
        for factor in financial_factors:
            score += factor['weight'] * factor['score']
            max_score += factor['weight']
        
        # Business factors
        business_factors = [
            # Size and complexity
            {
                'weight': 0.1,
                'score': 0.8 if assessment.debtor_type == DebtorType.SMALL_BUSINESS else 0.6
            },
            # Stakeholder complexity
            {
                'weight': 0.05,
                'score': max(0.2, 1 - (assessment.creditor_count / 1000))  # More creditors = more complex
            },
            # Employee considerations
            {
                'weight': 0.05,
                'score': 0.7 if assessment.has_union else 0.8  # Union can complicate but also provide stability
            },
            # Timeline pressure
            {
                'weight': 0.05,
                'score': 0.8 if assessment.exclusivity_deadline and assessment.exclusivity_deadline > datetime.utcnow() else 0.3
            }
        ]
        
        for factor in business_factors:
            score += factor['weight'] * factor['score']
            max_score += factor['weight']
        
        # Normalize to 0-1 scale
        feasibility_score = score / max_score if max_score > 0 else 0.0
        
        return min(1.0, max(0.0, feasibility_score))
    
    def _identify_critical_issues(self, assessment: CaseAssessment, case_data: Dict[str, Any]) -> List[str]:
        """Identify critical issues requiring immediate attention."""
        
        issues = []
        
        # Cash flow issues
        if assessment.financial_metrics.monthly_cash_flow < 0:
            issues.append("Negative monthly cash flow - immediate cash management required")
        
        # Liquidity crisis
        if assessment.financial_metrics.liquid_assets < assessment.financial_metrics.monthly_expenses:
            issues.append("Insufficient liquidity - less than one month of expenses in cash")
        
        # Deadline pressures
        if assessment.exclusivity_deadline:
            days_to_exclusivity = (assessment.exclusivity_deadline - datetime.utcnow()).days
            if days_to_exclusivity < 30 and not assessment.plan_filed:
                issues.append(f"Plan filing deadline approaching - {days_to_exclusivity} days remaining")
        
        # Secured debt issues
        if assessment.financial_metrics.secured_debt > assessment.financial_metrics.total_assets * Decimal('0.8'):
            issues.append("High secured debt relative to assets - potential cramdown issues")
        
        # Administrative expenses
        if case_data.get('unpaid_administrative_expenses', 0) > 0:
            issues.append("Unpaid administrative expenses - priority payment required")
        
        # Regulatory compliance
        if case_data.get('missing_monthly_reports', 0) > 1:
            issues.append("Missing monthly operating reports - compliance violation")
        
        # Key contract issues
        if case_data.get('executory_contracts_to_assume', 0) > 50:
            issues.append("Large number of executory contracts requiring assumption/rejection decisions")
        
        # Pension/Union issues
        if assessment.has_pension_obligations:
            issues.append("Pension obligations present - PBGC coordination required")
        
        return issues
    
    def _analyze_risk_factors(self, assessment: CaseAssessment, case_data: Dict[str, Any]) -> List[str]:
        """Analyze risk factors that could impact case success."""
        
        risks = []
        
        # Financial risks
        if assessment.financial_metrics.debt_to_asset_ratio > 0.9:
            risks.append("Very high debt-to-asset ratio increases liquidation risk")
        
        if assessment.financial_metrics.current_ratio < 0.5:
            risks.append("Poor liquidity ratio indicates potential payment difficulties")
        
        # Market risks
        industry = case_data.get('industry', '').lower()
        if industry in ['retail', 'restaurant', 'energy']:
            risks.append(f"Industry sector ({industry}) faces ongoing market challenges")
        
        # Operational risks
        if assessment.employee_count > 1000:
            risks.append("Large workforce increases operational complexity and WARN Act compliance")
        
        # Legal risks
        if case_data.get('pending_litigation_count', 0) > 5:
            risks.append("Significant pending litigation could impact reorganization")
        
        if case_data.get('environmental_liabilities', False):
            risks.append("Environmental liabilities present cleanup and regulatory risks")
        
        # Stakeholder risks
        if assessment.creditor_count > 500:
            risks.append("Large creditor base increases coordination and confirmation challenges")
        
        # Timing risks
        if assessment.case_status == CaseStatus.FILED:
            days_since_filing = (datetime.utcnow() - assessment.filing_date).days
            if days_since_filing > 365:
                risks.append("Extended case duration increases costs and stakeholder fatigue")
        
        return risks
    
    def _check_compliance(self, assessment: CaseAssessment, case_data: Dict[str, Any]) -> List[str]:
        """Check compliance with bankruptcy code requirements."""
        
        compliance_issues = []
        
        # Monthly reporting
        if case_data.get('monthly_reports_current', True) == False:
            compliance_issues.append("Monthly operating reports not current")
        
        # Quarterly fees
        if case_data.get('quarterly_fees_current', True) == False:
            compliance_issues.append("Quarterly U.S. Trustee fees not current")
        
        # Insurance requirements
        if case_data.get('insurance_current', True) == False:
            compliance_issues.append("Insurance coverage not maintained")
        
        # Bank account requirements
        if case_data.get('unauthorized_bank_accounts', False):
            compliance_issues.append("Unauthorized bank accounts detected")
        
        # Wage payments
        if case_data.get('employee_wages_current', True) == False:
            compliance_issues.append("Employee wages not current")
        
        # Tax obligations
        if case_data.get('post_petition_taxes_current', True) == False:
            compliance_issues.append("Post-petition tax obligations not current")
        
        return compliance_issues
    
    def _calculate_valuations(self, assessment: CaseAssessment) -> Tuple[Decimal, Decimal]:
        """Calculate liquidation value vs going concern value."""
        
        metrics = assessment.financial_metrics
        
        # Liquidation value (simplified calculation)
        # Apply liquidation discounts to different asset classes
        liquidation_value = (
            metrics.liquid_assets +  # 100% recovery on cash
            metrics.accounts_receivable * Decimal('0.7') +  # 70% on A/R
            metrics.inventory * Decimal('0.3') +  # 30% on inventory
            metrics.equipment * Decimal('0.4') +  # 40% on equipment
            metrics.real_estate * Decimal('0.8')  # 80% on real estate
        )
        
        # Going concern value (simplified DCF approach)
        # Use current cash flow as basis
        monthly_cf = metrics.monthly_cash_flow
        
        if monthly_cf > 0:
            # Positive cash flow - project forward
            annual_cf = monthly_cf * 12
            # Apply growth assumptions and discount rate
            growth_rate = Decimal('0.02')  # 2% annual growth
            discount_rate = Decimal('0.12')  # 12% discount rate
            terminal_multiple = Decimal('8')  # 8x terminal cash flow
            
            # Simple 5-year DCF
            pv_cash_flows = Decimal('0')
            for year in range(1, 6):
                cf = annual_cf * ((1 + growth_rate) ** year)
                pv = cf / ((1 + discount_rate) ** year)
                pv_cash_flows += pv
            
            # Terminal value
            terminal_cf = annual_cf * ((1 + growth_rate) ** 5)
            terminal_value = terminal_cf * terminal_multiple
            pv_terminal = terminal_value / ((1 + discount_rate) ** 5)
            
            going_concern_value = pv_cash_flows + pv_terminal
        else:
            # Negative cash flow - use asset-based approach with going concern premium
            going_concern_value = metrics.total_assets * Decimal('0.7')
        
        return liquidation_value, going_concern_value
    
    def _generate_recommendations(self, assessment: CaseAssessment) -> Tuple[List[str], List[str]]:
        """Generate priority actions and strategic recommendations."""
        
        priority_actions = []
        strategic_recommendations = []
        
        # Priority actions based on critical issues
        if assessment.financial_metrics.monthly_cash_flow < 0:
            priority_actions.append("Develop 13-week cash flow forecast and implement cash management controls")
            priority_actions.append("Identify non-essential expenses for immediate reduction")
        
        if assessment.financial_metrics.liquid_assets < assessment.financial_metrics.monthly_expenses:
            priority_actions.append("Secure DIP financing or use of cash collateral immediately")
        
        if not assessment.plan_filed and assessment.exclusivity_deadline:
            days_remaining = (assessment.exclusivity_deadline - datetime.utcnow()).days
            if days_remaining < 60:
                priority_actions.append("Accelerate plan development and stakeholder negotiations")
        
        # Strategic recommendations based on case characteristics
        if assessment.reorganization_feasibility > 0.7:
            strategic_recommendations.append("Strong reorganization candidate - focus on comprehensive plan")
            strategic_recommendations.append("Consider equity participation for creditors to maximize value")
        elif assessment.reorganization_feasibility < 0.3:
            strategic_recommendations.append("Consider conversion to Chapter 7 or sale under Section 363")
            strategic_recommendations.append("Maximize liquidation proceeds through controlled wind-down")
        else:
            strategic_recommendations.append("Marginal reorganization case - explore asset sale alternatives")
            strategic_recommendations.append("Consider hybrid approach with partial liquidation")
        
        # Stakeholder-specific recommendations
        if assessment.creditor_count > 100:
            strategic_recommendations.append("Form creditor committee early and maintain regular communication")
        
        if assessment.has_union:
            strategic_recommendations.append("Engage union representatives in plan negotiations early")
        
        if assessment.employee_count > 100:
            strategic_recommendations.append("Develop employee retention and communication strategy")
        
        # Financial structure recommendations
        if assessment.financial_metrics.secured_debt > assessment.financial_metrics.total_assets * Decimal('0.7'):
            strategic_recommendations.append("Negotiate secured debt modifications or consider cramdown")
        
        return priority_actions, strategic_recommendations
    
    def generate_compliance_checklist(self, assessment: CaseAssessment) -> List[ComplianceCheck]:
        """Generate comprehensive compliance checklist for case management."""
        
        checklist = []
        
        # Ongoing reporting requirements
        checklist.append(ComplianceCheck(
            check_id="monthly_reports",
            requirement="Monthly Operating Reports",
            status="compliant",  # Would be determined from case data
            priority=PriorityLevel.HIGH,
            description="File monthly operating reports by 20th of each month",
            deadline=self._next_monthly_deadline(),
            remediation_steps=[
                "Prepare monthly financial statements",
                "Complete MOR form",
                "File with court and serve on U.S. Trustee"
            ],
            risk_if_non_compliant=RiskLevel.HIGH,
            relevant_code_sections=["Fed. R. Bankr. P. 2015(a)(3)"]
        ))
        
        # Quarterly fees
        checklist.append(ComplianceCheck(
            check_id="quarterly_fees",
            requirement="Quarterly U.S. Trustee Fees",
            status="compliant",
            priority=PriorityLevel.HIGH,
            description="Pay quarterly fees to U.S. Trustee",
            deadline=self._next_quarterly_deadline(),
            remediation_steps=[
                "Calculate quarterly disbursements",
                "Prepare fee calculation",
                "Submit payment to U.S. Trustee"
            ],
            risk_if_non_compliant=RiskLevel.VERY_HIGH,
            relevant_code_sections=["28 U.S.C. § 1930(a)(6)"]
        ))
        
        # Plan filing requirement
        if not assessment.plan_filed and assessment.exclusivity_deadline:
            checklist.append(ComplianceCheck(
                check_id="plan_filing",
                requirement="File Plan of Reorganization",
                status="non_compliant" if datetime.utcnow() > assessment.exclusivity_deadline else "unclear",
                priority=PriorityLevel.CRITICAL,
                description="File plan within exclusivity period",
                deadline=assessment.exclusivity_deadline,
                remediation_steps=[
                    "Complete business plan and financial projections",
                    "Negotiate with key stakeholders",
                    "Draft plan and disclosure statement",
                    "File with court"
                ],
                risk_if_non_compliant=RiskLevel.VERY_HIGH,
                relevant_code_sections=["11 U.S.C. § 1121(b)"]
            ))
        
        # Insurance requirements
        checklist.append(ComplianceCheck(
            check_id="insurance",
            requirement="Maintain Adequate Insurance",
            status="compliant",
            priority=PriorityLevel.MEDIUM,
            description="Maintain property, casualty, and other required insurance",
            remediation_steps=[
                "Review current insurance policies",
                "Ensure adequate coverage limits",
                "Provide certificates to secured creditors"
            ],
            risk_if_non_compliant=RiskLevel.MEDIUM,
            relevant_code_sections=["11 U.S.C. § 1112(b)"]
        ))
        
        return checklist
    
    def _next_monthly_deadline(self) -> datetime:
        """Calculate next monthly reporting deadline."""
        now = datetime.utcnow()
        if now.day <= 20:
            return datetime(now.year, now.month, 20)
        else:
            next_month = now.replace(day=1) + timedelta(days=32)
            return datetime(next_month.year, next_month.month, 20)
    
    def _next_quarterly_deadline(self) -> datetime:
        """Calculate next quarterly fee deadline."""
        now = datetime.utcnow()
        current_quarter = ((now.month - 1) // 3) + 1
        
        if current_quarter == 1:
            quarter_end = datetime(now.year, 3, 31)
        elif current_quarter == 2:
            quarter_end = datetime(now.year, 6, 30)
        elif current_quarter == 3:
            quarter_end = datetime(now.year, 9, 30)
        else:
            quarter_end = datetime(now.year, 12, 31)
        
        return quarter_end + timedelta(days=30)
    
    def analyze_stakeholders(self, case_data: Dict[str, Any]) -> List[StakeholderAnalysis]:
        """Analyze key stakeholders and their positions."""
        
        stakeholders = []
        
        # Secured creditors
        secured_creditors = case_data.get('secured_creditors', [])
        for creditor in secured_creditors:
            stakeholders.append(StakeholderAnalysis(
                stakeholder_type="secured_creditor",
                name=creditor.get('name', 'Unknown'),
                role="Senior creditor with collateral",
                influence_level="high",
                cooperation_level="neutral",
                key_interests=[
                    "Full payment of secured claim",
                    "Protection of collateral value",
                    "Adequate protection payments"
                ],
                potential_objections=[
                    "Inadequate protection",
                    "Decline in collateral value",
                    "Extended payment terms"
                ],
                negotiation_strategy="Focus on collateral protection and payment certainty"
            ))
        
        # Unsecured creditor committee
        if case_data.get('creditor_committee_appointed', False):
            stakeholders.append(StakeholderAnalysis(
                stakeholder_type="unsecured_creditor_committee",
                name="Official Committee of Unsecured Creditors",
                role="Representative of unsecured creditor interests",
                influence_level="high",
                cooperation_level="neutral",
                key_interests=[
                    "Maximize recovery for unsecured creditors",
                    "Ensure fair treatment",
                    "Monitor debtor operations"
                ],
                potential_objections=[
                    "Inadequate disclosure",
                    "Unfair treatment",
                    "Poor business projections"
                ],
                negotiation_strategy="Provide transparency and demonstrate value maximization"
            ))
        
        # Unions
        if case_data.get('unions', []):
            for union in case_data['unions']:
                stakeholders.append(StakeholderAnalysis(
                    stakeholder_type="union",
                    name=union.get('name', 'Unknown Union'),
                    role="Employee representative",
                    influence_level="medium",
                    cooperation_level="adversarial",
                    key_interests=[
                        "Protect jobs and wages",
                        "Maintain benefits",
                        "Preserve collective bargaining agreement"
                    ],
                    potential_objections=[
                        "Wage or benefit reductions",
                        "Layoffs",
                        "Work rule changes"
                    ],
                    negotiation_strategy="Emphasize job preservation and business viability"
                ))
        
        return stakeholders
    
    def calculate_best_interests_test(self, assessment: CaseAssessment) -> Dict[str, Any]:
        """Calculate best interests test for confirmation requirements."""
        
        # Best interests test requires that creditors receive at least as much
        # under the plan as they would in a Chapter 7 liquidation
        
        liquidation_value = assessment.liquidation_value
        
        # Administrative costs in liquidation
        admin_costs = liquidation_value * Decimal('0.15')  # Estimate 15%
        net_liquidation = liquidation_value - admin_costs
        
        # Priority claims (must be paid in full)
        priority_claims = assessment.financial_metrics.priority_debt
        remaining_for_unsecured = net_liquidation - priority_claims
        
        # Calculate recovery percentage for unsecured creditors
        unsecured_claims = assessment.financial_metrics.unsecured_debt
        if unsecured_claims > 0:
            unsecured_recovery_pct = float(max(Decimal('0'), remaining_for_unsecured) / unsecured_claims)
        else:
            unsecured_recovery_pct = 1.0
        
        return {
            'gross_liquidation_value': float(liquidation_value),
            'administrative_costs': float(admin_costs),
            'net_liquidation_value': float(net_liquidation),
            'priority_claims': float(priority_claims),
            'unsecured_claims': float(unsecured_claims),
            'unsecured_recovery_percentage': unsecured_recovery_pct,
            'minimum_plan_payment_unsecured': float(remaining_for_unsecured),
            'best_interests_threshold': unsecured_recovery_pct
        }
    
    def generate_cash_flow_analysis(self, assessment: CaseAssessment, 
                                   case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed cash flow analysis and projections."""
        
        # Current monthly metrics
        current_revenue = assessment.financial_metrics.monthly_revenue
        current_expenses = assessment.financial_metrics.monthly_expenses
        current_cash_flow = current_revenue - current_expenses
        
        # 13-week cash flow projection
        weekly_cf = current_cash_flow / Decimal('4.33')  # Average weeks per month
        
        projections = []
        cumulative_cash = assessment.financial_metrics.liquid_assets
        
        for week in range(13):
            cumulative_cash += weekly_cf
            projections.append({
                'week': week + 1,
                'weekly_cash_flow': float(weekly_cf),
                'cumulative_cash': float(cumulative_cash),
                'cash_shortage': cumulative_cash < 0
            })
        
        # Identify cash shortage weeks
        shortage_weeks = [p for p in projections if p['cash_shortage']]
        
        # DIP financing needs
        if shortage_weeks:
            min_cash = min(p['cumulative_cash'] for p in projections)
            dip_need = abs(min_cash) + float(current_expenses)  # Buffer for one month
        else:
            dip_need = 0
        
        return {
            'current_monthly_revenue': float(current_revenue),
            'current_monthly_expenses': float(current_expenses),
            'current_monthly_cash_flow': float(current_cash_flow),
            'current_cash_balance': float(assessment.financial_metrics.liquid_assets),
            'thirteen_week_projections': projections,
            'weeks_with_shortage': len(shortage_weeks),
            'estimated_dip_financing_need': dip_need,
            'cash_runway_weeks': self._calculate_cash_runway(assessment),
            'break_even_required': float(current_expenses) if current_cash_flow < 0 else 0
        }
    
    def _calculate_cash_runway(self, assessment: CaseAssessment) -> int:
        """Calculate how many weeks of cash runway remain."""
        
        if assessment.financial_metrics.monthly_cash_flow >= 0:
            return 999  # Positive cash flow = indefinite runway
        
        monthly_burn = abs(assessment.financial_metrics.monthly_cash_flow)
        if monthly_burn == 0:
            return 999
        
        runway_months = assessment.financial_metrics.liquid_assets / monthly_burn
        return int(runway_months * 4.33)  # Convert to weeks
    
    def export_analysis(self, assessment: CaseAssessment, format: str = "json") -> str:
        """Export case analysis in specified format."""
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            data = {
                "case_id": assessment.case_id,
                "debtor_name": assessment.debtor_name,
                "case_status": assessment.case_status.value,
                "debtor_type": assessment.debtor_type.value,
                "filing_date": assessment.filing_date.isoformat(),
                "financial_metrics": {
                    "total_assets": float(assessment.financial_metrics.total_assets),
                    "total_liabilities": float(assessment.financial_metrics.total_liabilities),
                    "monthly_revenue": float(assessment.financial_metrics.monthly_revenue),
                    "monthly_expenses": float(assessment.financial_metrics.monthly_expenses),
                    "monthly_cash_flow": float(assessment.financial_metrics.monthly_cash_flow),
                    "debt_to_asset_ratio": assessment.financial_metrics.debt_to_asset_ratio,
                    "current_ratio": assessment.financial_metrics.current_ratio
                },
                "analysis_results": {
                    "reorganization_feasibility": assessment.reorganization_feasibility,
                    "liquidation_value": float(assessment.liquidation_value),
                    "going_concern_value": float(assessment.going_concern_value),
                    "critical_issues": assessment.critical_issues,
                    "risk_factors": assessment.risk_factors,
                    "compliance_issues": assessment.compliance_issues,
                    "priority_actions": assessment.priority_actions,
                    "strategic_recommendations": assessment.strategic_recommendations
                },
                "analysis_timestamp": assessment.analysis_timestamp.isoformat()
            }
            
            return json.dumps(data, indent=2, default=str)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get statistics about the analyzer capabilities."""
        
        return {
            "supported_debtor_types": [dt.value for dt in DebtorType],
            "case_statuses": [cs.value for cs in CaseStatus],
            "risk_levels": [rl.value for rl in RiskLevel],
            "priority_levels": [pl.value for pl in PriorityLevel],
            "compliance_checks": len(self.code_requirements),
            "distress_indicators": len(self.distress_indicators),
            "industry_benchmarks": len(self.industry_benchmarks),
            "analysis_capabilities": [
                "Financial metrics analysis",
                "Reorganization feasibility assessment",
                "Compliance checking",
                "Stakeholder analysis",
                "Cash flow projections",
                "Best interests test calculation",
                "Liquidation vs going concern valuation"
            ]
        }