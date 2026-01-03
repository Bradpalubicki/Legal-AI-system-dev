"""
Legal filing impact assessment and urgency scoring.

Analyzes legal filings to determine potential impact on cases, clients,
and business operations. Provides risk assessment and priority scoring.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum

from ..shared.utils import BaseAPIClient
from .models import ImpactLevel, UrgencyLevel, FilingType, ExtractedContent


class RiskCategory(Enum):
    """Categories of legal risk."""
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"
    STRATEGIC = "strategic"
    COMPLIANCE = "compliance"


@dataclass
class RiskFactor:
    """Individual risk factor identified in filing."""
    category: RiskCategory
    description: str
    severity: float  # 0.0 to 1.0
    likelihood: float  # 0.0 to 1.0
    impact_areas: List[str]
    mitigation_suggestions: List[str] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    """Complete impact assessment of legal filing."""
    overall_impact: ImpactLevel
    urgency_level: UrgencyLevel
    risk_score: float  # 0.0 to 10.0
    business_impact_score: float  # 0.0 to 10.0
    
    # Detailed analysis
    identified_risks: List[RiskFactor]
    affected_stakeholders: List[str]
    potential_outcomes: List[Dict[str, Any]]
    
    # Financial implications
    estimated_cost_range: Optional[Tuple[Decimal, Decimal]]
    potential_damages: Optional[Decimal]
    defense_cost_estimate: Optional[Decimal]
    
    # Timeline analysis
    critical_deadlines: List[Tuple[date, str]]
    estimated_resolution_time: Optional[str]
    
    # Strategic considerations
    precedent_implications: List[str]
    regulatory_considerations: List[str]
    public_relations_impact: str
    
    # Recommendations
    immediate_actions: List[str]
    strategic_recommendations: List[str]
    resource_requirements: Dict[str, Any]
    
    # Metadata
    assessment_confidence: float
    analysis_timestamp: datetime
    factors_considered: List[str]


class ImpactAssessor:
    """Intelligent legal filing impact assessment system."""
    
    def __init__(self, api_client: BaseAPIClient):
        self.api_client = api_client
        self.risk_matrices = self._initialize_risk_matrices()
        self.impact_rules = self._initialize_impact_rules()
        
    def _initialize_risk_matrices(self) -> Dict[str, Dict[str, float]]:
        """Initialize risk assessment matrices."""
        return {
            "filing_type_risk": {
                FilingType.COMPLAINT.value: 8.0,
                FilingType.EMERGENCY_MOTION.value: 9.5,
                FilingType.INJUNCTION_REQUEST.value: 9.0,
                FilingType.SUMMARY_JUDGMENT.value: 7.5,
                FilingType.CLASS_ACTION.value: 9.5,
                FilingType.BANKRUPTCY.value: 8.5,
                FilingType.REGULATORY_FILING.value: 7.0,
                FilingType.DISCOVERY_REQUEST.value: 4.0,
                FilingType.MOTION.value: 5.5,
                FilingType.BRIEF.value: 4.5,
                FilingType.APPEAL.value: 7.0,
                FilingType.SETTLEMENT_AGREEMENT.value: 6.0,
                FilingType.CONTRACT.value: 5.0,
                FilingType.NOTICE.value: 3.0,
                FilingType.OTHER.value: 4.0
            },
            "financial_impact": {
                "under_10k": 2.0,
                "10k_to_100k": 4.0,
                "100k_to_1m": 6.0,
                "1m_to_10m": 8.0,
                "over_10m": 10.0
            },
            "timeline_urgency": {
                "immediate": 10.0,
                "24_hours": 9.0,
                "3_days": 8.0,
                "1_week": 6.0,
                "2_weeks": 4.0,
                "1_month": 3.0,
                "over_month": 2.0
            }
        }
    
    def _initialize_impact_rules(self) -> Dict[str, Any]:
        """Initialize business impact assessment rules."""
        return {
            "high_impact_keywords": [
                "emergency", "injunction", "restraining order", "cease",
                "class action", "bankruptcy", "criminal", "federal investigation",
                "regulatory violation", "compliance failure", "data breach",
                "intellectual property", "trade secret", "confidential"
            ],
            "stakeholder_mapping": {
                "executives": ["CEO", "CFO", "general counsel", "board"],
                "legal": ["legal department", "outside counsel", "compliance"],
                "operations": ["operations", "manufacturing", "supply chain"],
                "finance": ["finance", "accounting", "treasury"],
                "hr": ["human resources", "employment", "labor relations"],
                "marketing": ["marketing", "public relations", "communications"]
            },
            "precedent_indicators": [
                "first impression", "novel issue", "circuit split",
                "constitutional", "statutory interpretation",
                "industry standard", "regulatory guidance"
            ]
        }
    
    async def assess_impact(self,
                           filing_type: FilingType,
                           extracted_content: ExtractedContent,
                           case_context: Optional[Dict[str, Any]] = None) -> ImpactAnalysis:
        """
        Perform comprehensive impact assessment of legal filing.
        
        Args:
            filing_type: Type of legal filing
            extracted_content: Extracted content from document
            case_context: Additional case context and history
            
        Returns:
            ImpactAnalysis with comprehensive assessment
        """
        case_context = case_context or {}
        
        # Calculate base risk scores
        risk_score = self._calculate_risk_score(filing_type, extracted_content)
        business_impact_score = await self._assess_business_impact(
            filing_type, extracted_content, case_context
        )
        
        # Determine overall impact and urgency levels
        overall_impact = self._determine_impact_level(risk_score, business_impact_score)
        urgency_level = self._determine_urgency_level(filing_type, extracted_content)
        
        # Identify specific risks
        identified_risks = await self._identify_risks(filing_type, extracted_content)
        
        # Analyze affected stakeholders
        affected_stakeholders = self._identify_stakeholders(extracted_content, identified_risks)
        
        # Assess potential outcomes
        potential_outcomes = await self._analyze_outcomes(
            filing_type, extracted_content, identified_risks
        )
        
        # Financial impact analysis
        financial_analysis = self._analyze_financial_impact(extracted_content, identified_risks)
        
        # Timeline analysis
        timeline_analysis = self._analyze_timeline(extracted_content)
        
        # Strategic considerations
        strategic_analysis = await self._analyze_strategic_implications(
            filing_type, extracted_content, case_context
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            filing_type, extracted_content, identified_risks, overall_impact
        )
        
        return ImpactAnalysis(
            overall_impact=overall_impact,
            urgency_level=urgency_level,
            risk_score=risk_score,
            business_impact_score=business_impact_score,
            identified_risks=identified_risks,
            affected_stakeholders=affected_stakeholders,
            potential_outcomes=potential_outcomes,
            estimated_cost_range=financial_analysis["cost_range"],
            potential_damages=financial_analysis["damages"],
            defense_cost_estimate=financial_analysis["defense_costs"],
            critical_deadlines=timeline_analysis["deadlines"],
            estimated_resolution_time=timeline_analysis["resolution_time"],
            precedent_implications=strategic_analysis["precedent"],
            regulatory_considerations=strategic_analysis["regulatory"],
            public_relations_impact=strategic_analysis["pr_impact"],
            immediate_actions=recommendations["immediate"],
            strategic_recommendations=recommendations["strategic"],
            resource_requirements=recommendations["resources"],
            assessment_confidence=self._calculate_confidence(extracted_content),
            analysis_timestamp=datetime.utcnow(),
            factors_considered=self._get_factors_considered(filing_type, extracted_content)
        )
    
    def _calculate_risk_score(self, filing_type: FilingType, content: ExtractedContent) -> float:
        """Calculate overall risk score based on filing characteristics."""
        base_risk = self.risk_matrices["filing_type_risk"].get(filing_type.value, 5.0)
        
        # Adjust for high-impact keywords
        content_text = " ".join([
            " ".join(content.claims_and_arguments),
            content.document_summary,
            str(content.jurisdiction_info)
        ]).lower()
        
        keyword_multiplier = 1.0
        for keyword in self.impact_rules["high_impact_keywords"]:
            if keyword in content_text:
                keyword_multiplier += 0.2
        
        # Adjust for financial exposure
        if content.financial_info:
            damages = content.financial_info.get("damages_claimed")
            if damages:
                try:
                    amount = float(damages.replace("$", "").replace(",", ""))
                    if amount > 10000000:  # $10M+
                        base_risk += 2.0
                    elif amount > 1000000:  # $1M+
                        base_risk += 1.5
                    elif amount > 100000:  # $100K+
                        base_risk += 1.0
                except (ValueError, AttributeError):
                    pass
        
        # Adjust for timeline pressure
        if content.deadlines_and_actions:
            for action in content.deadlines_and_actions:
                if action.due_date and action.due_date <= date.today() + timedelta(days=7):
                    base_risk += 1.0
                    break
        
        final_score = min(base_risk * keyword_multiplier, 10.0)
        return round(final_score, 1)
    
    async def _assess_business_impact(self,
                                    filing_type: FilingType,
                                    content: ExtractedContent,
                                    case_context: Dict[str, Any]) -> float:
        """Assess potential business impact using AI analysis."""
        prompt = self._build_business_impact_prompt(filing_type, content, case_context)
        
        try:
            response = await self.api_client.post(
                "/ai/assess",
                json={
                    "prompt": prompt,
                    "model": "gpt-4",
                    "temperature": 0.2,
                    "max_tokens": 600
                },
                timeout=30.0
            )
            
            analysis = response.get("impact_analysis", {})
            return min(analysis.get("business_impact_score", 5.0), 10.0)
            
        except Exception:
            # Fallback to rule-based assessment
            return self._assess_business_impact_rules(filing_type, content)
    
    def _build_business_impact_prompt(self,
                                    filing_type: FilingType,
                                    content: ExtractedContent,
                                    case_context: Dict[str, Any]) -> str:
        """Build prompt for AI business impact assessment."""
        return f"""
Assess the business impact of this legal filing:

Filing Type: {filing_type.value}
Parties: {', '.join(content.parties)}
Claims: {'; '.join(content.claims_and_arguments[:3])}
Financial Info: {content.financial_info}
Jurisdiction: {content.jurisdiction_info}

Case Context: {case_context}

Evaluate the potential business impact on a scale of 0-10 considering:
1. Financial exposure and potential damages
2. Operational disruption risk
3. Regulatory/compliance implications
4. Reputational impact
5. Strategic business implications

Provide response as JSON:
{{
    "business_impact_score": 7.5,
    "primary_concerns": ["concern1", "concern2"],
    "affected_operations": ["area1", "area2"],
    "mitigation_priority": "high|medium|low"
}}
"""
    
    def _assess_business_impact_rules(self, filing_type: FilingType, content: ExtractedContent) -> float:
        """Rule-based business impact assessment fallback."""
        base_score = {
            FilingType.COMPLAINT: 7.0,
            FilingType.CLASS_ACTION: 9.0,
            FilingType.EMERGENCY_MOTION: 8.0,
            FilingType.REGULATORY_FILING: 6.0,
            FilingType.CONTRACT: 5.0
        }.get(filing_type, 5.0)
        
        # Adjust for parties involved (company names, government entities)
        for party in content.parties:
            if any(word in party.lower() for word in ["government", "sec", "ftc", "doj"]):
                base_score += 1.5
                break
        
        return min(base_score, 10.0)
    
    def _determine_impact_level(self, risk_score: float, business_impact: float) -> ImpactLevel:
        """Determine overall impact level from scores."""
        combined_score = (risk_score + business_impact) / 2
        
        if combined_score >= 8.0:
            return ImpactLevel.CRITICAL
        elif combined_score >= 6.0:
            return ImpactLevel.HIGH
        elif combined_score >= 4.0:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
    
    def _determine_urgency_level(self, filing_type: FilingType, content: ExtractedContent) -> UrgencyLevel:
        """Determine urgency level based on filing characteristics."""
        # Check for emergency filings
        if filing_type in [FilingType.EMERGENCY_MOTION, FilingType.INJUNCTION_REQUEST]:
            return UrgencyLevel.CRITICAL
        
        # Check document content for urgency indicators
        doc_text = (content.document_summary + " " + " ".join(content.claims_and_arguments)).lower()
        
        if any(word in doc_text for word in ["emergency", "immediate", "urgent", "expedited"]):
            return UrgencyLevel.CRITICAL
        
        # Check deadlines
        if content.deadlines_and_actions:
            for action in content.deadlines_and_actions:
                if action.due_date:
                    days_until = (action.due_date - date.today()).days
                    if days_until <= 1:
                        return UrgencyLevel.CRITICAL
                    elif days_until <= 7:
                        return UrgencyLevel.HIGH
                    elif days_until <= 30:
                        return UrgencyLevel.MEDIUM
        
        # Default based on filing type
        high_urgency_types = [FilingType.COMPLAINT, FilingType.SUMMARY_JUDGMENT, FilingType.APPEAL]
        if filing_type in high_urgency_types:
            return UrgencyLevel.HIGH
        
        return UrgencyLevel.MEDIUM
    
    async def _identify_risks(self, filing_type: FilingType, content: ExtractedContent) -> List[RiskFactor]:
        """Identify specific risk factors from filing content."""
        risks = []
        
        # Financial risks
        if content.financial_info and content.financial_info.get("damages_claimed"):
            risks.append(RiskFactor(
                category=RiskCategory.FINANCIAL,
                description="Potential monetary damages exposure",
                severity=0.8,
                likelihood=0.6,
                impact_areas=["cash flow", "profitability", "financial reporting"]
            ))
        
        # Regulatory risks
        for claim in content.claims_and_arguments:
            if any(word in claim.lower() for word in ["regulation", "compliance", "violation", "sec", "ftc"]):
                risks.append(RiskFactor(
                    category=RiskCategory.REGULATORY,
                    description="Regulatory compliance violation alleged",
                    severity=0.7,
                    likelihood=0.5,
                    impact_areas=["compliance", "regulatory standing", "licensing"]
                ))
                break
        
        # Operational risks
        if filing_type in [FilingType.INJUNCTION_REQUEST, FilingType.EMERGENCY_MOTION]:
            risks.append(RiskFactor(
                category=RiskCategory.OPERATIONAL,
                description="Potential business operations disruption",
                severity=0.9,
                likelihood=0.4,
                impact_areas=["operations", "supply chain", "customer service"]
            ))
        
        # Reputational risks
        if filing_type == FilingType.CLASS_ACTION or "public" in content.document_summary.lower():
            risks.append(RiskFactor(
                category=RiskCategory.REPUTATIONAL,
                description="Potential negative publicity and brand impact",
                severity=0.6,
                likelihood=0.7,
                impact_areas=["brand reputation", "customer trust", "media coverage"]
            ))
        
        return risks
    
    def _identify_stakeholders(self, content: ExtractedContent, risks: List[RiskFactor]) -> List[str]:
        """Identify stakeholders affected by the filing."""
        stakeholders = set()
        
        # Always include legal team
        stakeholders.add("Legal Department")
        
        # Add based on risk categories
        for risk in risks:
            if risk.category == RiskCategory.FINANCIAL:
                stakeholders.update(["CFO", "Finance Team", "Executive Leadership"])
            elif risk.category == RiskCategory.REGULATORY:
                stakeholders.update(["Compliance Officer", "Regulatory Affairs"])
            elif risk.category == RiskCategory.OPERATIONAL:
                stakeholders.update(["Operations Team", "COO"])
            elif risk.category == RiskCategory.REPUTATIONAL:
                stakeholders.update(["PR Team", "Communications", "Marketing"])
        
        # Add based on claims content
        claims_text = " ".join(content.claims_and_arguments).lower()
        if any(word in claims_text for word in ["employment", "hr", "discrimination"]):
            stakeholders.add("Human Resources")
        if any(word in claims_text for word in ["intellectual property", "patent", "trademark"]):
            stakeholders.add("IP Department")
        
        return list(stakeholders)
    
    async def _analyze_outcomes(self,
                              filing_type: FilingType,
                              content: ExtractedContent,
                              risks: List[RiskFactor]) -> List[Dict[str, Any]]:
        """Analyze potential outcomes and scenarios."""
        outcomes = []
        
        # Best case scenario
        outcomes.append({
            "scenario": "Best Case",
            "probability": 0.3,
            "description": "Successful defense with minimal costs",
            "impact": "Low financial impact, case resolved quickly",
            "timeline": "3-6 months"
        })
        
        # Most likely scenario
        outcomes.append({
            "scenario": "Most Likely",
            "probability": 0.5,
            "description": "Settlement or negotiated resolution",
            "impact": "Moderate costs, some operational adjustments",
            "timeline": "6-12 months"
        })
        
        # Worst case scenario
        worst_case_impact = "High"
        if any(risk.severity > 0.8 for risk in risks):
            worst_case_impact = "Severe"
        
        outcomes.append({
            "scenario": "Worst Case",
            "probability": 0.2,
            "description": "Adverse judgment with maximum exposure",
            "impact": f"{worst_case_impact} financial and operational impact",
            "timeline": "12-24 months"
        })
        
        return outcomes
    
    def _analyze_financial_impact(self, content: ExtractedContent, risks: List[RiskFactor]) -> Dict[str, Any]:
        """Analyze potential financial implications."""
        financial_analysis = {
            "cost_range": None,
            "damages": None,
            "defense_costs": None
        }
        
        # Extract claimed damages
        if content.financial_info and content.financial_info.get("damages_claimed"):
            try:
                damages_str = content.financial_info["damages_claimed"]
                damages_amount = Decimal(damages_str.replace("$", "").replace(",", ""))
                financial_analysis["damages"] = damages_amount
                
                # Estimate defense costs as percentage of exposure
                defense_estimate = damages_amount * Decimal("0.1")  # 10% of exposure
                financial_analysis["defense_costs"] = defense_estimate
                
                # Cost range estimate
                low_estimate = defense_estimate
                high_estimate = damages_amount + defense_estimate
                financial_analysis["cost_range"] = (low_estimate, high_estimate)
                
            except (ValueError, TypeError):
                pass
        
        # Default estimates if no financial info
        if not financial_analysis["defense_costs"]:
            financial_analysis["defense_costs"] = Decimal("50000")  # Default $50K
            financial_analysis["cost_range"] = (Decimal("25000"), Decimal("200000"))
        
        return financial_analysis
    
    def _analyze_timeline(self, content: ExtractedContent) -> Dict[str, Any]:
        """Analyze timeline and critical deadlines."""
        deadlines = []
        
        # Extract deadlines from action items
        if content.deadlines_and_actions:
            for action in content.deadlines_and_actions:
                if action.due_date:
                    deadlines.append((action.due_date, action.description))
        
        # Sort by date
        deadlines.sort(key=lambda x: x[0])
        
        # Estimate resolution time
        resolution_time = "12-18 months"  # Default estimate
        if deadlines and len(deadlines) > 3:
            resolution_time = "18-24 months"  # Complex case
        elif deadlines and deadlines[0][0] <= date.today() + timedelta(days=30):
            resolution_time = "6-12 months"  # Fast-moving case
        
        return {
            "deadlines": deadlines[:5],  # Top 5 critical deadlines
            "resolution_time": resolution_time
        }
    
    async def _analyze_strategic_implications(self,
                                           filing_type: FilingType,
                                           content: ExtractedContent,
                                           case_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze strategic and precedential implications."""
        claims_text = " ".join(content.claims_and_arguments + [content.document_summary]).lower()
        
        # Precedent implications
        precedent_implications = []
        for indicator in self.impact_rules["precedent_indicators"]:
            if indicator in claims_text:
                precedent_implications.append(f"Case involves {indicator} - may set precedent")
        
        # Regulatory considerations
        regulatory_considerations = []
        if any(word in claims_text for word in ["regulation", "sec", "ftc", "doj", "compliance"]):
            regulatory_considerations.append("Case has regulatory compliance implications")
        
        # PR impact assessment
        pr_impact = "Low"
        if filing_type == FilingType.CLASS_ACTION:
            pr_impact = "High"
        elif any(word in claims_text for word in ["public", "consumer", "safety", "environment"]):
            pr_impact = "Medium"
        
        return {
            "precedent": precedent_implications,
            "regulatory": regulatory_considerations,
            "pr_impact": pr_impact
        }
    
    async def _generate_recommendations(self,
                                      filing_type: FilingType,
                                      content: ExtractedContent,
                                      risks: List[RiskFactor],
                                      impact_level: ImpactLevel) -> Dict[str, Any]:
        """Generate actionable recommendations."""
        recommendations = {
            "immediate": [],
            "strategic": [],
            "resources": {}
        }
        
        # Immediate actions based on urgency
        recommendations["immediate"].extend([
            "Notify key stakeholders and legal team",
            "Review filing for accuracy and prepare initial response strategy",
            "Gather relevant documents and evidence"
        ])
        
        if impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            recommendations["immediate"].extend([
                "Schedule emergency legal team meeting",
                "Assess need for outside counsel specialization",
                "Review insurance coverage and notify carriers"
            ])
        
        # Strategic recommendations
        recommendations["strategic"].extend([
            "Develop comprehensive defense strategy",
            "Consider settlement opportunities if appropriate",
            "Review and strengthen related business processes"
        ])
        
        # Resource requirements
        recommendations["resources"] = {
            "legal_budget": f"${50000 if impact_level == ImpactLevel.LOW else 200000}",
            "outside_counsel": impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL],
            "internal_resources": ["Legal", "Compliance"] + 
                                 (["Finance", "Operations"] if impact_level != ImpactLevel.LOW else []),
            "estimated_hours": 100 if impact_level == ImpactLevel.LOW else 500
        }
        
        return recommendations
    
    def _calculate_confidence(self, content: ExtractedContent) -> float:
        """Calculate confidence score for the assessment."""
        confidence_factors = []
        
        # Content completeness
        if content.parties:
            confidence_factors.append(0.2)
        if content.claims_and_arguments:
            confidence_factors.append(0.3)
        if content.financial_info:
            confidence_factors.append(0.2)
        if content.legal_citations:
            confidence_factors.append(0.1)
        if content.jurisdiction_info:
            confidence_factors.append(0.2)
        
        return min(sum(confidence_factors), 1.0)
    
    def _get_factors_considered(self, filing_type: FilingType, content: ExtractedContent) -> List[str]:
        """Get list of factors considered in assessment."""
        factors = [
            f"Filing type: {filing_type.value}",
            f"Number of parties: {len(content.parties)}",
            f"Number of claims: {len(content.claims_and_arguments)}",
            f"Financial info present: {'Yes' if content.financial_info else 'No'}",
            f"Citations present: {'Yes' if content.legal_citations else 'No'}",
            f"Action items: {len(content.deadlines_and_actions) if content.deadlines_and_actions else 0}"
        ]
        
        return factors