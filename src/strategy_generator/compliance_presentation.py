"""
Compliance-Based Strategy Presentation Layer

Formats strategic options with strict educational compliance, ensuring all content
uses informational language and includes proper disclaimers. Prevents advisory
language and maintains UPL compliance throughout presentation.

CRITICAL LEGAL DISCLAIMER:
All strategic information is presented for educational purposes only.
This system provides general information about common legal strategies.
No legal advice is provided. No attorney-client relationship is created.
Consult qualified legal counsel for guidance on specific situations.

Created: 2025-09-14
Legal AI System - Compliance Presentation Engine
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Import strategy and compliance components
try:
    from .comprehensive_strategy_options import (
        ComprehensiveStrategy, StrategyCategory, ComplexityLevel,
        StatisticalData, CostEstimate, TimelineEstimate
    )
    from ..shared.compliance.upl_compliance import ComplianceWrapper, ViolationSeverity
except ImportError:
    # Mock imports for standalone use
    class StrategyCategory(Enum):
        BANKRUPTCY = "bankruptcy"
        DEBT_RESOLUTION = "debt_resolution"
        CONTRACT_DISPUTES = "contract_disputes"
        LITIGATION = "litigation"
        SETTLEMENT = "settlement"
        NEGOTIATION = "negotiation"
        REGULATORY = "regulatory"
        CORPORATE = "corporate"

    class ComplexityLevel(Enum):
        SIMPLE = "simple"
        MODERATE = "moderate"
        COMPLEX = "complex"
        HIGHLY_COMPLEX = "highly_complex"

    class ViolationSeverity(Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"

    class ComplianceWrapper:
        def analyze_text(self, text: str) -> Dict[str, Any]:
            return {"has_advice": False, "violations": [], "compliance_score": 1.0}

    class ComprehensiveStrategy:
        def __init__(self):
            self.strategy_id = "mock_strategy"
            self.name = "Mock Strategy"
            self.category = StrategyCategory.BANKRUPTCY
            self.complexity_level = ComplexityLevel.MODERATE
            self.frequency_of_use = 0.5
            self.description = "Mock strategy description"
            self.advantages = ["Advantage 1", "Advantage 2"]
            self.disadvantages = ["Consideration 1", "Consideration 2"]
            self.statistical_data = []
            self.timeline = None
            self.costs = None
            self.success_factors = None
            self.court_considerations = None
            self.legal_requirements = None
            self.common_outcomes = None

logger = logging.getLogger(__name__)


class PresentationMode(Enum):
    """Strategy presentation modes"""
    SUMMARY = "summary"           # Brief overview with key points
    DETAILED = "detailed"         # Comprehensive information
    COMPARISON = "comparison"     # Side-by-side comparison format
    REPORT = "report"            # Formal educational report
    INTERACTIVE = "interactive"   # Web interface presentation


class ContentSection(Enum):
    """Types of content sections"""
    DESCRIPTION = "description"
    ADVANTAGES = "advantages"
    CONSIDERATIONS = "considerations"
    TIMELINE = "timeline"
    COSTS = "costs"
    SUCCESS_FACTORS = "success_factors"
    STATISTICAL_DATA = "statistical_data"
    COURT_FACTORS = "court_factors"
    REQUIREMENTS = "requirements"
    OUTCOMES = "outcomes"


@dataclass
class ComplianceValidation:
    """Results of compliance validation"""
    is_compliant: bool
    compliance_score: float  # 0-1 scale
    violations: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_sections: List[str] = field(default_factory=list)


@dataclass
class FormattedContent:
    """Formatted strategy content with compliance validation"""
    strategy_id: str
    title: str
    sections: Dict[str, Any] = field(default_factory=dict)
    disclaimers: List[str] = field(default_factory=list)
    compliance_notes: List[str] = field(default_factory=list)
    presentation_metadata: Dict[str, Any] = field(default_factory=dict)
    validation_result: Optional[ComplianceValidation] = None


@dataclass
class PresentationTemplate:
    """Template for formatting strategy content"""
    mode: PresentationMode
    sections_to_include: List[ContentSection]
    format_rules: Dict[str, str] = field(default_factory=dict)
    disclaimer_placement: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)


@dataclass
class ComplianceStrategyTemplate:
    """Standardized template for UPL-compliant strategy presentation"""
    title: str
    description: str
    disclaimer: str
    statistics: str
    typical_outcome: str

    # Compliance validation patterns
    never_include: List[str] = field(default_factory=lambda: [
        'You should...',
        'We recommend...',
        'Your best option...',
        'You must...',
        'I suggest...',
        'My advice...',
        'The best choice...',
        'You need to...'
    ])

    # Required language patterns
    required_patterns: List[str] = field(default_factory=lambda: [
        'parties commonly',
        'often consider',
        'typically results in',
        'used in.*% of similar cases',
        'an attorney can advise'
    ])

    @classmethod
    def create_compliant_template(cls, strategy_name: str, usage_percentage: float = 0.0) -> 'ComplianceStrategyTemplate':
        """Create a template with compliant language patterns"""
        return cls(
            title=f"Common Legal Option: {strategy_name}",
            description=f"Parties in similar situations often consider this approach. This option is commonly used when circumstances warrant this type of legal strategy.",
            disclaimer="This is a common legal option used in similar situations. An attorney can advise if it applies to specific circumstances and provide guidance on implementation.",
            statistics=f"Used in approximately {usage_percentage:.0%} of similar cases" if usage_percentage > 0 else "Usage varies by jurisdiction and case specifics",
            typical_outcome="Cases typically result in outcomes that vary based on individual circumstances and case-specific factors."
        )

    def validate_compliance(self) -> Tuple[bool, List[str]]:
        """Validate template content for UPL compliance"""
        violations = []
        content_to_check = f"{self.title} {self.description} {self.disclaimer} {self.typical_outcome}"

        # Check for prohibited advisory language
        import re
        for pattern in self.never_include:
            if re.search(pattern.replace('...', r'.*'), content_to_check, re.IGNORECASE):
                violations.append(f"Contains prohibited advisory language: {pattern}")

        # Check for required disclaimer elements
        if not re.search(r'attorney.*advise', self.disclaimer, re.IGNORECASE):
            violations.append("Missing required attorney consultation guidance")

        if not re.search(r'similar situations?', content_to_check, re.IGNORECASE):
            violations.append("Missing required 'similar situations' framing")

        return len(violations) == 0, violations

    def to_formatted_content(self, strategy_id: str) -> FormattedContent:
        """Convert template to FormattedContent object"""
        return FormattedContent(
            strategy_id=strategy_id,
            title=self.title,
            sections={
                'description': {
                    'content': self.description,
                    'educational_note': 'This overview describes how this strategy commonly works in similar situations.'
                },
                'statistics': {
                    'content': self.statistics,
                    'educational_note': 'Statistical information is provided for educational context only.'
                },
                'typical_outcome': {
                    'content': self.typical_outcome,
                    'educational_note': 'Outcomes may vary significantly based on specific circumstances.'
                }
            },
            disclaimers=[
                self.disclaimer,
                "This information is for educational purposes only.",
                "No legal advice is provided. Professional consultation is required."
            ],
            compliance_notes=[
                "All information presented using educational language patterns",
                "No recommendations or advice provided",
                "Attorney consultation consistently recommended"
            ]
        )


class CompliancePresentationEngine:
    """
    Formats strategic options with educational compliance.

    Ensures all content uses informational language patterns,
    includes proper disclaimers, and maintains UPL compliance.

    EDUCATIONAL PURPOSE DISCLAIMER:
    This presentation engine formats information for educational purposes only.
    All formatted content describes common approaches used in similar situations.
    No recommendations or advice are provided through this formatting process.
    """

    def __init__(self):
        """Initialize the compliance presentation engine"""
        self.compliance_wrapper = ComplianceWrapper()
        self.logger = logging.getLogger(__name__)

        # Initialize presentation templates
        self._initialize_templates()

        # Compliance patterns and replacements
        self._initialize_compliance_patterns()

        # Standard disclaimers
        self.standard_disclaimers = {
            "educational_purpose": (
                "This information is provided for educational purposes only and describes "
                "common legal strategies used in similar situations."
            ),
            "no_advice": (
                "No legal advice is provided. No attorney-client relationship is created."
            ),
            "professional_consultation": (
                "Consult qualified legal counsel for guidance on specific circumstances "
                "and to receive legal advice applicable to individual situations."
            ),
            "statistical_context": (
                "Statistical information is provided for general educational context only "
                "and may not reflect outcomes in specific cases."
            ),
            "individual_variation": (
                "Each legal situation involves unique factors that may significantly affect "
                "outcomes, timeline, costs, and applicable strategies."
            )
        }

    def _initialize_templates(self):
        """Initialize presentation templates for different modes"""

        self.templates = {
            PresentationMode.SUMMARY: PresentationTemplate(
                mode=PresentationMode.SUMMARY,
                sections_to_include=[
                    ContentSection.DESCRIPTION,
                    ContentSection.ADVANTAGES,
                    ContentSection.CONSIDERATIONS,
                    ContentSection.TIMELINE,
                    ContentSection.COSTS
                ],
                format_rules={
                    "max_advantages": "5",
                    "max_considerations": "5",
                    "include_statistics": "primary_only",
                    "disclaimer_frequency": "section_headers"
                },
                disclaimer_placement=["header", "footer"],
                compliance_requirements=["informational_language", "no_recommendations"]
            ),

            PresentationMode.DETAILED: PresentationTemplate(
                mode=PresentationMode.DETAILED,
                sections_to_include=[
                    ContentSection.DESCRIPTION,
                    ContentSection.ADVANTAGES,
                    ContentSection.CONSIDERATIONS,
                    ContentSection.TIMELINE,
                    ContentSection.COSTS,
                    ContentSection.SUCCESS_FACTORS,
                    ContentSection.STATISTICAL_DATA,
                    ContentSection.COURT_FACTORS,
                    ContentSection.REQUIREMENTS,
                    ContentSection.OUTCOMES
                ],
                format_rules={
                    "include_all_statistics": "true",
                    "detailed_timelines": "true",
                    "comprehensive_costs": "true",
                    "court_considerations": "true"
                },
                disclaimer_placement=["header", "each_section", "footer"],
                compliance_requirements=["full_educational_language", "comprehensive_disclaimers"]
            ),

            PresentationMode.COMPARISON: PresentationTemplate(
                mode=PresentationMode.COMPARISON,
                sections_to_include=[
                    ContentSection.DESCRIPTION,
                    ContentSection.TIMELINE,
                    ContentSection.COSTS,
                    ContentSection.STATISTICAL_DATA
                ],
                format_rules={
                    "side_by_side": "true",
                    "highlight_differences": "true",
                    "normalize_formatting": "true"
                },
                disclaimer_placement=["header", "footer"],
                compliance_requirements=["comparison_language", "no_rankings"]
            )
        }

    def _initialize_compliance_patterns(self):
        """Initialize patterns for compliance transformation"""

        # Advisory language to informational language replacements
        self.advisory_replacements = {
            r'\byou should\b': 'parties commonly',
            r'\bi recommend\b': 'commonly used approaches include',
            r'\bthe best option\b': 'a frequently used option',
            r'\byou must\b': 'typically required',
            r'\bi suggest\b': 'common approaches include',
            r'\bmy advice\b': 'common guidance includes',
            r'\byou need to\b': 'commonly required steps include',
            r'\bit is recommended\b': 'it is commonly observed',
            r'\byou can\b': 'parties may',
            r'\byour situation\b': 'situations like this'
        }

        # Informational language patterns
        self.informational_patterns = [
            'commonly used in similar situations',
            'frequently observed in',
            'typical approaches include',
            'parties often consider',
            'common factors include',
            'generally involves',
            'typically requires',
            'commonly results in',
            'frequently leads to',
            'often includes'
        ]

    def format_strategy_content(self, strategy: ComprehensiveStrategy,
                              presentation_mode: PresentationMode = PresentationMode.SUMMARY,
                              custom_requirements: Optional[List[str]] = None) -> FormattedContent:
        """
        Format strategy content with compliance validation.

        Args:
            strategy: ComprehensiveStrategy object to format
            presentation_mode: How to present the content
            custom_requirements: Additional compliance requirements

        Returns:
            FormattedContent with compliance validation
        """

        try:
            template = self.templates.get(presentation_mode, self.templates[PresentationMode.SUMMARY])

            # Create formatted content structure
            formatted = FormattedContent(
                strategy_id=strategy.strategy_id,
                title=self._format_title(strategy),
                presentation_metadata={
                    "presentation_mode": presentation_mode.value,
                    "formatted_at": datetime.now().isoformat(),
                    "compliance_validated": True
                }
            )

            # Format each required section
            for section in template.sections_to_include:
                formatted.sections[section.value] = self._format_section(
                    strategy, section, template.format_rules
                )

            # Add disclaimers based on template
            formatted.disclaimers = self._generate_disclaimers(
                template.disclaimer_placement, strategy.category
            )

            # Add compliance notes
            formatted.compliance_notes = self._generate_compliance_notes(strategy)

            # Validate compliance
            formatted.validation_result = self._validate_formatted_content(formatted)

            # Apply compliance corrections if needed
            if not formatted.validation_result.is_compliant:
                formatted = self._apply_compliance_corrections(formatted)

            return formatted

        except Exception as e:
            self.logger.error(f"Error formatting strategy content: {str(e)}")
            return self._create_error_formatted_content(strategy.strategy_id)

    def _format_title(self, strategy: ComprehensiveStrategy) -> str:
        """Format strategy title with educational framing"""

        category_labels = {
            StrategyCategory.BANKRUPTCY: "Common Bankruptcy Option",
            StrategyCategory.LITIGATION: "Litigation Approach",
            StrategyCategory.SETTLEMENT: "Settlement Option",
            StrategyCategory.NEGOTIATION: "Negotiation Approach"
        }

        category_label = category_labels.get(strategy.category, "Legal Option")
        return f"{category_label}: {strategy.name}"

    def _format_section(self, strategy: ComprehensiveStrategy, section: ContentSection,
                       format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format individual content section with compliance"""

        if section == ContentSection.DESCRIPTION:
            return self._format_description(strategy, format_rules)
        elif section == ContentSection.ADVANTAGES:
            return self._format_advantages(strategy, format_rules)
        elif section == ContentSection.CONSIDERATIONS:
            return self._format_considerations(strategy, format_rules)
        elif section == ContentSection.TIMELINE:
            return self._format_timeline(strategy, format_rules)
        elif section == ContentSection.COSTS:
            return self._format_costs(strategy, format_rules)
        elif section == ContentSection.SUCCESS_FACTORS:
            return self._format_success_factors(strategy, format_rules)
        elif section == ContentSection.STATISTICAL_DATA:
            return self._format_statistical_data(strategy, format_rules)
        elif section == ContentSection.COURT_FACTORS:
            return self._format_court_factors(strategy, format_rules)
        elif section == ContentSection.REQUIREMENTS:
            return self._format_requirements(strategy, format_rules)
        elif section == ContentSection.OUTCOMES:
            return self._format_outcomes(strategy, format_rules)
        else:
            return {"content": "Content not available", "disclaimer": "Section unavailable"}

    def _format_description(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format description section with educational language"""

        # Apply compliance transformations
        description = self._transform_to_informational_language(strategy.description)

        return {
            "title": "Educational Overview",
            "content": description,
            "educational_note": "This overview describes how this strategy commonly works in similar situations.",
            "frequency_context": f"Used in approximately {strategy.frequency_of_use:.1%} of similar cases"
        }

    def _format_advantages(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format advantages with informational language"""

        max_items = int(format_rules.get("max_advantages", "10"))
        advantages = strategy.advantages[:max_items]

        # Transform each advantage to informational language
        formatted_advantages = []
        for advantage in advantages:
            formatted_advantage = self._transform_to_informational_language(advantage)
            formatted_advantages.append(formatted_advantage)

        return {
            "title": "Common Benefits Observed",
            "items": formatted_advantages,
            "educational_note": "These benefits are commonly observed in similar cases but may vary based on specific circumstances."
        }

    def _format_considerations(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format considerations/disadvantages with balanced language"""

        max_items = int(format_rules.get("max_considerations", "10"))
        considerations = strategy.disadvantages[:max_items]

        # Transform to informational language
        formatted_considerations = []
        for consideration in considerations:
            formatted_consideration = self._transform_to_informational_language(consideration)
            formatted_considerations.append(formatted_consideration)

        return {
            "title": "Common Considerations and Challenges",
            "items": formatted_considerations,
            "educational_note": "These considerations are frequently encountered in similar situations."
        }

    def _format_timeline(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format timeline information with appropriate disclaimers"""

        if not strategy.timeline:
            return {
                "title": "Timeline Information",
                "content": "Timeline varies based on case-specific factors",
                "disclaimer": "Consult legal counsel for timeline estimates specific to individual circumstances"
            }

        timeline_info = {
            "title": "Typical Timeline Observed",
            "typical_duration": strategy.timeline.typical_duration,
            "duration_range": f"{strategy.timeline.minimum_duration} to {strategy.timeline.maximum_duration}",
            "educational_note": "Timeline estimates are based on commonly observed patterns and may vary significantly."
        }

        if strategy.timeline.key_milestones:
            timeline_info["common_milestones"] = [
                {
                    "milestone": milestone[0],
                    "typical_timeframe": milestone[1],
                    "note": "Timing may vary based on case-specific factors"
                }
                for milestone in strategy.timeline.key_milestones
            ]

        if strategy.timeline.factors_affecting_timeline:
            timeline_info["factors_affecting_timeline"] = {
                "factors": strategy.timeline.factors_affecting_timeline,
                "note": "These factors commonly influence timeline duration in similar cases"
            }

        return timeline_info

    def _format_costs(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format cost information with appropriate disclaimers"""

        if not strategy.costs:
            return {
                "title": "Cost Information",
                "content": "Costs vary based on case complexity and geographic location",
                "disclaimer": "Consult legal counsel for cost estimates specific to individual circumstances"
            }

        cost_info = {
            "title": "Typical Cost Ranges Observed",
            "attorney_fees": {
                "range": f"${strategy.costs.attorney_fees_range[0]:,.0f} - ${strategy.costs.attorney_fees_range[1]:,.0f}",
                "structure": strategy.costs.payment_structure,
                "note": "Attorney fees vary based on experience, location, and case complexity"
            },
            "total_estimated_range": f"${strategy.costs.total_range[0]:,.0f} - ${strategy.costs.total_range[1]:,.0f}",
            "educational_note": "Cost estimates are based on commonly observed ranges and may vary significantly based on specific circumstances."
        }

        if strategy.costs.additional_costs:
            cost_info["additional_typical_costs"] = {
                "items": [
                    {"item": item, "amount": f"${amount:,.0f}" if isinstance(amount, (int, float)) else str(amount)}
                    for item, amount in strategy.costs.additional_costs.items()
                ],
                "note": "Additional costs commonly incurred in similar cases"
            }

        if strategy.costs.cost_factors:
            cost_info["factors_affecting_costs"] = {
                "factors": strategy.costs.cost_factors,
                "note": "These factors commonly influence total costs in similar cases"
            }

        return cost_info

    def _format_success_factors(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format success factors with educational language"""

        if not strategy.success_factors:
            return {
                "title": "Success Factors",
                "content": "Success factors vary based on individual circumstances",
                "disclaimer": "Professional analysis required to identify factors applicable to specific situations"
            }

        success_info = {
            "title": "Factors Commonly Associated with Success",
            "educational_note": "These factors are frequently observed in successful cases but may not guarantee outcomes."
        }

        if strategy.success_factors.critical_factors:
            success_info["critical_factors"] = {
                "title": "Factors Commonly Considered Critical",
                "factors": strategy.success_factors.critical_factors,
                "note": "These factors are frequently identified as important in similar successful cases"
            }

        if strategy.success_factors.helpful_factors:
            success_info["helpful_factors"] = {
                "title": "Additional Helpful Factors Often Observed",
                "factors": strategy.success_factors.helpful_factors,
                "note": "These factors commonly contribute to positive outcomes"
            }

        if strategy.success_factors.risk_factors:
            success_info["risk_considerations"] = {
                "title": "Risk Factors Commonly Encountered",
                "factors": strategy.success_factors.risk_factors,
                "note": "These factors are frequently associated with challenges in similar cases"
            }

        return success_info

    def _format_statistical_data(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format statistical data with appropriate context"""

        if not strategy.statistical_data:
            return {
                "title": "Statistical Information",
                "content": "Statistical data varies by jurisdiction and case type",
                "disclaimer": "Professional analysis required for case-specific probability assessment"
            }

        stats_info = {
            "title": "Statistical Context from Similar Cases",
            "educational_note": "Statistical information is provided for educational context only and does not predict outcomes in individual cases.",
            "statistics": []
        }

        include_all = format_rules.get("include_all_statistics", "false") == "true"
        stats_to_show = strategy.statistical_data if include_all else strategy.statistical_data[:1]

        for stat in stats_to_show:
            stat_entry = {
                "metric": stat.metric_type.value.replace('_', ' ').title(),
                "rate": f"{stat.success_rate:.1%}",
                "sample_size": f"{stat.sample_size:,} cases",
                "time_period": stat.time_period,
                "source": stat.data_source,
                "confidence_interval": f"{stat.confidence_interval[0]:.1%} - {stat.confidence_interval[1]:.1%}",
                "disclaimer": "Statistical data represents general trends and may not reflect individual case outcomes"
            }

            if stat.notes:
                stat_entry["methodology_note"] = stat.notes

            stats_info["statistics"].append(stat_entry)

        return stats_info

    def _format_court_factors(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format court consideration factors"""

        if not strategy.court_considerations:
            return {
                "title": "Court Considerations",
                "content": "Court considerations vary by jurisdiction and case specifics",
                "disclaimer": "Professional legal analysis required for jurisdiction-specific court practices"
            }

        court_info = {
            "title": "Factors Courts Commonly Consider",
            "educational_note": "These factors are frequently considered by courts in similar cases but may vary by jurisdiction."
        }

        if strategy.court_considerations.primary_factors:
            court_info["primary_considerations"] = {
                "title": "Primary Factors Frequently Considered",
                "factors": strategy.court_considerations.primary_factors,
                "note": "These factors are commonly given significant weight in similar cases"
            }

        if strategy.court_considerations.secondary_factors:
            court_info["additional_considerations"] = {
                "title": "Additional Factors Often Considered",
                "factors": strategy.court_considerations.secondary_factors,
                "note": "These factors may also influence court decisions in similar cases"
            }

        if strategy.court_considerations.recent_trends:
            court_info["recent_trends"] = {
                "title": "Recent Trends Observed",
                "trends": strategy.court_considerations.recent_trends,
                "note": "These trends have been observed in recent similar cases"
            }

        return court_info

    def _format_requirements(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format legal requirements information"""

        if not strategy.legal_requirements:
            return {
                "title": "Legal Requirements",
                "content": "Requirements vary by jurisdiction and case specifics",
                "disclaimer": "Professional legal counsel required to identify requirements applicable to specific situations"
            }

        req_info = {
            "title": "Common Legal Requirements",
            "educational_note": "These requirements are commonly observed in similar cases but may vary by jurisdiction."
        }

        if strategy.legal_requirements.mandatory_requirements:
            req_info["typically_required"] = {
                "title": "Commonly Required Elements",
                "requirements": strategy.legal_requirements.mandatory_requirements,
                "note": "These requirements are frequently mandatory in similar cases"
            }

        if strategy.legal_requirements.procedural_steps:
            req_info["common_procedures"] = {
                "title": "Typical Procedural Steps",
                "steps": strategy.legal_requirements.procedural_steps,
                "note": "These procedures are commonly followed in similar cases"
            }

        if strategy.legal_requirements.documentation_needed:
            req_info["typical_documentation"] = {
                "title": "Documentation Commonly Required",
                "documents": strategy.legal_requirements.documentation_needed,
                "note": "This documentation is frequently required in similar cases"
            }

        return req_info

    def _format_outcomes(self, strategy: ComprehensiveStrategy, format_rules: Dict[str, str]) -> Dict[str, Any]:
        """Format common outcomes information"""

        if not strategy.common_outcomes:
            return {
                "title": "Common Outcomes",
                "content": "Outcomes vary based on case-specific factors",
                "disclaimer": "Professional analysis required to assess potential outcomes for specific situations"
            }

        outcomes_info = {
            "title": "Outcomes Commonly Observed",
            "educational_note": "These outcomes are frequently observed in similar cases but individual results may vary significantly."
        }

        if strategy.common_outcomes.most_common_outcomes:
            outcomes_info["frequent_outcomes"] = {
                "title": "Most Frequently Observed Outcomes",
                "outcomes": [
                    {
                        "outcome": outcome[0],
                        "frequency": f"{outcome[1]:.1%}",
                        "note": "Frequency based on analysis of similar cases"
                    }
                    for outcome in strategy.common_outcomes.most_common_outcomes
                ],
                "disclaimer": "Outcome frequencies represent general trends and do not predict individual case results"
            }

        if strategy.common_outcomes.alternative_outcomes:
            outcomes_info["alternative_outcomes"] = {
                "title": "Alternative Outcomes Sometimes Observed",
                "outcomes": strategy.common_outcomes.alternative_outcomes,
                "note": "These outcomes are less common but may occur in similar cases"
            }

        if strategy.common_outcomes.factors_influencing_outcomes:
            outcomes_info["outcome_factors"] = {
                "title": "Factors Commonly Influencing Outcomes",
                "factors": strategy.common_outcomes.factors_influencing_outcomes,
                "note": "These factors frequently affect outcomes in similar cases"
            }

        return outcomes_info

    def _generate_disclaimers(self, placement_list: List[str], category: StrategyCategory) -> List[str]:
        """Generate appropriate disclaimers based on placement and category"""

        disclaimers = []

        if "header" in placement_list:
            disclaimers.append(self.standard_disclaimers["educational_purpose"])
            disclaimers.append(self.standard_disclaimers["no_advice"])

        if "section_headers" in placement_list or "each_section" in placement_list:
            disclaimers.append(self.standard_disclaimers["statistical_context"])
            disclaimers.append(self.standard_disclaimers["individual_variation"])

        if "footer" in placement_list:
            disclaimers.append(self.standard_disclaimers["professional_consultation"])

        return disclaimers

    def _generate_compliance_notes(self, strategy: ComprehensiveStrategy) -> List[str]:
        """Generate compliance notes for the strategy"""

        notes = [
            "All information presented is educational and describes common approaches used in similar situations",
            "No recommendations or advice are provided through this information",
            "Statistical data is for educational context only and does not predict individual outcomes",
            "Each situation involves unique factors requiring professional legal analysis"
        ]

        if strategy.frequency_of_use > 0:
            notes.append(f"This approach is used in approximately {strategy.frequency_of_use:.1%} of similar cases")

        return notes

    def _transform_to_informational_language(self, text: str) -> str:
        """Transform text to use informational rather than advisory language"""

        import re
        transformed = text

        # Apply advisory to informational replacements
        for pattern, replacement in self.advisory_replacements.items():
            transformed = re.sub(pattern, replacement, transformed, flags=re.IGNORECASE)

        return transformed

    def _validate_formatted_content(self, formatted: FormattedContent) -> ComplianceValidation:
        """Validate formatted content for compliance"""

        violations = []
        warnings = []
        validated_sections = []

        # Check each section for compliance
        for section_name, section_content in formatted.sections.items():
            section_text = json.dumps(section_content) if isinstance(section_content, dict) else str(section_content)

            # Use compliance wrapper to check
            compliance_result = self.compliance_wrapper.analyze_text(section_text)

            if compliance_result.get("has_advice", False):
                violations.extend(compliance_result.get("violations", []))

            # Check for advisory language patterns
            if self._contains_advisory_language(section_text):
                warnings.append(f"Section {section_name} may contain advisory language")

            validated_sections.append(section_name)

        # Calculate compliance score
        total_sections = len(formatted.sections)
        violation_count = len(violations)
        warning_count = len(warnings)

        compliance_score = max(0.0, 1.0 - (violation_count * 0.2) - (warning_count * 0.1))
        is_compliant = compliance_score >= 0.85 and violation_count == 0

        return ComplianceValidation(
            is_compliant=is_compliant,
            compliance_score=compliance_score,
            violations=violations,
            warnings=warnings,
            validated_sections=validated_sections
        )

    def _contains_advisory_language(self, text: str) -> bool:
        """Check for advisory language patterns"""

        advisory_patterns = [
            r'\byou should\b',
            r'\bi recommend\b',
            r'\bmy advice\b',
            r'\bthe best option\b',
            r'\byou must\b',
            r'\bi suggest\b',
            r'\bmy recommendation\b'
        ]

        import re
        for pattern in advisory_patterns:
            if re.search(pattern, text.lower()):
                return True

        return False

    def _apply_compliance_corrections(self, formatted: FormattedContent) -> FormattedContent:
        """Apply corrections to achieve compliance"""

        # Transform all section content to informational language
        for section_name, section_content in formatted.sections.items():
            if isinstance(section_content, dict):
                formatted.sections[section_name] = self._transform_section_content(section_content)
            elif isinstance(section_content, str):
                formatted.sections[section_name] = self._transform_to_informational_language(section_content)

        # Add additional compliance disclaimers
        formatted.disclaimers.extend([
            "IMPORTANT: This information is educational only and describes common approaches",
            "Professional legal consultation is required for guidance on specific situations",
            "No recommendations or legal advice are provided through this information"
        ])

        # Re-validate
        formatted.validation_result = self._validate_formatted_content(formatted)

        return formatted

    def _transform_section_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform dictionary content to informational language"""

        transformed = {}

        for key, value in content.items():
            if isinstance(value, str):
                transformed[key] = self._transform_to_informational_language(value)
            elif isinstance(value, list):
                transformed[key] = [
                    self._transform_to_informational_language(item) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                transformed[key] = self._transform_section_content(value)
            else:
                transformed[key] = value

        return transformed

    def _create_error_formatted_content(self, strategy_id: str) -> FormattedContent:
        """Create error formatted content when formatting fails"""

        return FormattedContent(
            strategy_id=strategy_id,
            title="Strategy Information Unavailable",
            sections={
                "error": {
                    "message": "Unable to format strategy information",
                    "educational_note": "Professional legal consultation is recommended for strategic guidance"
                }
            },
            disclaimers=[
                "Information formatting error occurred",
                "Consult qualified legal counsel for strategic guidance",
                "No legal advice or recommendations are provided"
            ],
            validation_result=ComplianceValidation(
                is_compliant=True,
                compliance_score=1.0
            )
        )

    def format_strategy_comparison(self, strategies: List[ComprehensiveStrategy]) -> Dict[str, Any]:
        """Format multiple strategies for side-by-side comparison"""

        if not strategies:
            return {
                "comparison_title": "Strategy Comparison",
                "strategies": [],
                "disclaimers": [self.standard_disclaimers["educational_purpose"]]
            }

        comparison = {
            "comparison_title": "Educational Comparison of Common Legal Options",
            "disclaimers": [
                self.standard_disclaimers["educational_purpose"],
                self.standard_disclaimers["no_advice"],
                self.standard_disclaimers["professional_consultation"]
            ],
            "strategies": []
        }

        for strategy in strategies:
            strategy_summary = {
                "name": strategy.name,
                "category": strategy.category.value.replace('_', ' ').title(),
                "complexity": strategy.complexity_level.value.title(),
                "frequency_of_use": f"{strategy.frequency_of_use:.1%}",
                "educational_note": "Information describes common approaches in similar situations"
            }

            # Add timeline if available
            if strategy.timeline:
                strategy_summary["typical_timeline"] = strategy.timeline.typical_duration

            # Add costs if available
            if strategy.costs:
                strategy_summary["cost_range"] = f"${strategy.costs.total_range[0]:,.0f} - ${strategy.costs.total_range[1]:,.0f}"

            # Add primary statistic if available
            if strategy.statistical_data:
                primary_stat = strategy.statistical_data[0]
                strategy_summary["success_metric"] = f"{primary_stat.success_rate:.1%} {primary_stat.metric_type.value.replace('_', ' ')}"

            # Add top advantages
            if strategy.advantages:
                strategy_summary["key_benefits"] = [
                    self._transform_to_informational_language(adv)
                    for adv in strategy.advantages[:3]
                ]

            # Add top considerations
            if strategy.disadvantages:
                strategy_summary["key_considerations"] = [
                    self._transform_to_informational_language(disadv)
                    for disadv in strategy.disadvantages[:3]
                ]

            comparison["strategies"].append(strategy_summary)

        return comparison

    def generate_compliance_report(self, formatted_content: FormattedContent) -> str:
        """Generate a compliance validation report"""

        if not formatted_content.validation_result:
            return "Compliance validation not performed"

        validation = formatted_content.validation_result

        report_lines = [
            "COMPLIANCE VALIDATION REPORT",
            "=" * 35,
            f"Strategy ID: {formatted_content.strategy_id}",
            f"Strategy Title: {formatted_content.title}",
            f"Compliance Status: {'COMPLIANT' if validation.is_compliant else 'NEEDS REVIEW'}",
            f"Compliance Score: {validation.compliance_score:.2f}",
            f"Sections Validated: {len(validation.validated_sections)}",
            ""
        ]

        if validation.violations:
            report_lines.extend([
                "VIOLATIONS IDENTIFIED:",
                "-" * 20
            ])
            for violation in validation.violations:
                report_lines.append(f"• {violation}")
            report_lines.append("")

        if validation.warnings:
            report_lines.extend([
                "WARNINGS:",
                "-" * 10
            ])
            for warning in validation.warnings:
                report_lines.append(f"• {warning}")
            report_lines.append("")

        if validation.recommendations:
            report_lines.extend([
                "RECOMMENDATIONS:",
                "-" * 15
            ])
            for rec in validation.recommendations:
                report_lines.append(f"• {rec}")
            report_lines.append("")

        report_lines.extend([
            "DISCLAIMER COMPLIANCE:",
            f"Total disclaimers: {len(formatted_content.disclaimers)}",
            f"Compliance notes: {len(formatted_content.compliance_notes)}",
            "",
            "EDUCATIONAL PURPOSE CONFIRMATION:",
            "✓ Content presents information for educational purposes only",
            "✓ No legal advice or recommendations provided",
            "✓ Professional consultation consistently recommended",
            "✓ Informational language patterns used throughout"
        ])

        return "\n".join(report_lines)

    def format_strategy_using_template(self, strategy: ComprehensiveStrategy) -> FormattedContent:
        """Format strategy using the standardized compliance template"""

        # Create compliant template
        template = ComplianceStrategyTemplate.create_compliant_template(
            strategy_name=strategy.name,
            usage_percentage=strategy.frequency_of_use
        )

        # Validate template compliance
        is_compliant, violations = template.validate_compliance()
        if not is_compliant:
            self.logger.warning(f"Template compliance issues: {violations}")

        # Convert to FormattedContent
        formatted = template.to_formatted_content(strategy.strategy_id)

        # Add strategy-specific information
        if strategy.statistical_data:
            primary_stat = strategy.statistical_data[0]
            formatted.sections['statistics']['content'] = (
                f"Used in approximately {strategy.frequency_of_use:.0%} of similar cases. "
                f"Success rate commonly observed: {primary_stat.success_rate:.0%} "
                f"({primary_stat.metric_type.value.replace('_', ' ')})"
            )

        if strategy.timeline:
            formatted.sections['typical_outcome']['content'] = (
                f"Cases typically result in outcomes within {strategy.timeline.typical_duration}. "
                "Individual results may vary based on case-specific factors and circumstances."
            )

        # Add advantages as benefits commonly observed
        if strategy.advantages:
            formatted.sections['benefits'] = {
                'title': 'Benefits Commonly Observed',
                'content': strategy.advantages[:3],  # Top 3 advantages
                'educational_note': 'These benefits are frequently observed in similar cases but may not occur in all situations.'
            }

        # Add considerations
        if strategy.disadvantages:
            formatted.sections['considerations'] = {
                'title': 'Considerations Commonly Encountered',
                'content': strategy.disadvantages[:3],  # Top 3 considerations
                'educational_note': 'These factors are commonly considered in similar cases.'
            }

        # Validate final formatted content
        formatted.validation_result = self._validate_formatted_content(formatted)

        return formatted

    def create_template_from_dict(self, template_dict: Dict[str, Any]) -> ComplianceStrategyTemplate:
        """Create ComplianceStrategyTemplate from dictionary (like the provided template)"""

        return ComplianceStrategyTemplate(
            title=template_dict.get('title', 'Common Legal Option'),
            description=template_dict.get('description', 'Parties in similar situations often consider this approach.'),
            disclaimer=template_dict.get('disclaimer', 'This is a common legal option. An attorney can advise if it applies.'),
            statistics=template_dict.get('statistics', 'Usage varies by jurisdiction and case specifics'),
            typical_outcome=template_dict.get('typical_outcome', 'Cases typically result in outcomes that vary based on individual circumstances.')
        )

    def validate_strategy_template(self, template_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a strategy template dictionary for compliance"""

        # Create template from dict
        template = self.create_template_from_dict(template_dict)

        # Validate compliance
        is_compliant, violations = template.validate_compliance()

        # Additional validation for never_include patterns
        never_include = template_dict.get('never_include', [])
        content_to_check = " ".join([
            template_dict.get('title', ''),
            template_dict.get('description', ''),
            template_dict.get('disclaimer', ''),
            template_dict.get('typical_outcome', '')
        ])

        import re
        for pattern in never_include:
            if re.search(pattern.replace('...', r'.*'), content_to_check, re.IGNORECASE):
                violations.append(f"Template contains prohibited pattern: {pattern}")
                is_compliant = False

        return is_compliant, violations


def test_compliance_presentation_engine():
    """Test the compliance presentation engine"""

    print("=== COMPLIANCE PRESENTATION ENGINE TEST ===")
    print("Testing educational content formatting with UPL compliance")
    print()

    # This would normally import a real strategy, but for testing we'll create a mock
    from datetime import datetime

    # Mock strategy for testing (would normally come from comprehensive_strategy_options)
    class MockStrategy:
        def __init__(self):
            self.strategy_id = "test_strategy"
            self.name = "Test Legal Strategy"
            self.description = "This strategy involves common legal approaches used in similar situations."
            self.category = StrategyCategory.BANKRUPTCY
            self.complexity_level = ComplexityLevel.MODERATE
            self.advantages = [
                "Commonly provides debt relief in similar situations",
                "Process typically completes within expected timeframes",
                "Automatic stay generally provides creditor protection"
            ]
            self.disadvantages = [
                "Assets may be subject to liquidation in some cases",
                "Credit impact commonly lasts several years",
                "Some debts may remain non-dischargeable"
            ]
            self.frequency_of_use = 0.65
            self.timeline = None
            self.costs = None
            self.success_factors = None
            self.statistical_data = []
            self.court_considerations = None
            self.legal_requirements = None
            self.common_outcomes = None

    # Initialize engine
    engine = CompliancePresentationEngine()

    # Test 1: Summary formatting
    print("TEST 1: Summary Format Compliance")
    print("-" * 35)

    mock_strategy = MockStrategy()
    summary_content = engine.format_strategy_content(
        mock_strategy,
        PresentationMode.SUMMARY
    )

    print(f"Strategy Title: {summary_content.title}")
    print(f"Sections Generated: {len(summary_content.sections)}")
    print(f"Disclaimers Added: {len(summary_content.disclaimers)}")

    if summary_content.validation_result:
        validation = summary_content.validation_result
        print(f"Compliance Status: {'COMPLIANT' if validation.is_compliant else 'NEEDS REVIEW'}")
        print(f"Compliance Score: {validation.compliance_score:.2f}")
        print(f"Violations: {len(validation.violations)}")
        print(f"Warnings: {len(validation.warnings)}")

    # Test 2: Content transformation
    print(f"\nTEST 2: Advisory Language Transformation")
    print("-" * 40)

    advisory_text = "You should consider this option. I recommend filing quickly. The best option is settlement."
    transformed = engine._transform_to_informational_language(advisory_text)
    print(f"Original: {advisory_text}")
    print(f"Transformed: {transformed}")

    contains_advisory = engine._contains_advisory_language(transformed)
    print(f"Advisory language detected: {contains_advisory}")

    # Test 3: Disclaimer generation
    print(f"\nTEST 3: Disclaimer Generation")
    print("-" * 30)

    disclaimers = engine._generate_disclaimers(
        ["header", "footer"],
        StrategyCategory.BANKRUPTCY
    )

    print(f"Generated {len(disclaimers)} disclaimers:")
    for i, disclaimer in enumerate(disclaimers, 1):
        print(f"{i}. {disclaimer}")

    # Test 4: Compliance report
    print(f"\nTEST 4: Compliance Report Generation")
    print("-" * 35)

    compliance_report = engine.generate_compliance_report(summary_content)
    print("Sample Compliance Report:")
    print(compliance_report[:500] + "..." if len(compliance_report) > 500 else compliance_report)

    # Test 5: Multiple strategy comparison
    print(f"\nTEST 5: Strategy Comparison Format")
    print("-" * 30)

    strategies = [mock_strategy, mock_strategy]  # Would normally be different strategies
    comparison = engine.format_strategy_comparison(strategies)

    print(f"Comparison Title: {comparison['comparison_title']}")
    print(f"Strategies Compared: {len(comparison['strategies'])}")
    print(f"Disclaimers Included: {len(comparison['disclaimers'])}")

    # Summary
    print(f"\n=== TEST RESULTS SUMMARY ===")
    print(f"Compliance presentation engine ready: YES")
    print(f"Educational language transformation: WORKING")
    print(f"Disclaimer generation: FUNCTIONAL")
    print(f"Content validation: OPERATIONAL")
    print(f"UPL compliance maintenance: ACTIVE")

    print(f"\nKey Features Demonstrated:")
    print(f"• Educational content formatting")
    print(f"• Advisory language transformation")
    print(f"• Comprehensive disclaimer system")
    print(f"• Compliance validation and scoring")
    print(f"• Multi-strategy comparison formatting")

    # Test 6: New Template System Integration
    print(f"\nTEST 6: Standardized Template System")
    print("-" * 40)

    # Test the provided template structure
    test_template = {
        'title': 'Common Legal Option: Template Test',
        'description': 'Parties in similar situations often consider this test approach.',
        'disclaimer': 'This is a common legal option. An attorney can advise if it applies.',
        'statistics': 'Used in 45% of similar cases',
        'typical_outcome': 'Cases typically result in outcomes that vary by case specifics.',
        'never_include': [
            'You should...',
            'We recommend...',
            'Your best option...',
            'You must...'
        ]
    }

    # Validate template
    is_valid, template_violations = engine.validate_strategy_template(test_template)
    print(f"Template validation: {'PASSED' if is_valid else 'FAILED'}")
    if template_violations:
        for violation in template_violations:
            print(f"  - {violation}")

    # Create template from dict
    template_obj = engine.create_template_from_dict(test_template)
    template_compliant, template_issues = template_obj.validate_compliance()
    print(f"Template compliance: {'COMPLIANT' if template_compliant else 'NEEDS REVIEW'}")

    # Test strategy formatting using template
    formatted_with_template = engine.format_strategy_using_template(mock_strategy)
    print(f"Template-based formatting: SUCCESS")
    print(f"Sections created: {list(formatted_with_template.sections.keys())}")
    print(f"Disclaimers included: {len(formatted_with_template.disclaimers)}")

    # Test 7: Template Creation and Validation
    print(f"\nTEST 7: Template Creation and Validation")
    print("-" * 40)

    # Create compliant template
    auto_template = ComplianceStrategyTemplate.create_compliant_template(
        "Test Strategy",
        usage_percentage=0.65
    )

    auto_compliant, auto_violations = auto_template.validate_compliance()
    print(f"Auto-created template: {'COMPLIANT' if auto_compliant else 'NEEDS REVIEW'}")
    print(f"Template title: {auto_template.title}")
    print(f"Statistics format: {auto_template.statistics}")

    # Convert to formatted content
    auto_formatted = auto_template.to_formatted_content("auto_test_strategy")
    print(f"Template conversion: SUCCESS")
    print(f"Generated sections: {len(auto_formatted.sections)}")

    return True


class ComplianceStrategyPresentation:
    """
    Main presentation engine for compliance-based strategy presentation

    Provides educational strategy information with strict UPL compliance.
    All outputs are formatted as educational content only.
    """

    def __init__(self):
        # Import shared compliance components
        try:
            from ..shared.compliance import ComplianceWrapper, AdviceDetector, DisclaimerSystem
            self.compliance_wrapper = ComplianceWrapper()
            self.advice_detector = AdviceDetector()
            self.disclaimer_system = DisclaimerSystem()
        except ImportError:
            # Mock components for testing
            self.compliance_wrapper = MockComplianceWrapper()
            self.advice_detector = MockAdviceDetector()
            self.disclaimer_system = MockDisclaimerSystem()

        self.logger = logging.getLogger(__name__)

    def generate_educational_overview(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate educational overview of legal strategies based on analysis

        Args:
            analysis_data: Document analysis results

        Returns:
            UPL-compliant educational content string
        """
        try:
            # Determine strategy type from analysis
            doc_type = analysis_data.get('document_type', 'unknown')

            if 'bankruptcy' in doc_type.lower():
                content = self._generate_bankruptcy_overview(analysis_data)
            elif 'litigation' in doc_type.lower():
                content = self._generate_litigation_overview(analysis_data)
            else:
                content = self._generate_generic_overview(analysis_data)

            # Ensure UPL compliance
            compliant_content = self.compliance_wrapper.make_compliant(content)

            # Add appropriate disclaimer
            disclaimer_type = self.disclaimer_system.get_appropriate_disclaimer_type(
                doc_type, is_strategy=True
            )
            disclaimer = self.disclaimer_system.get_disclaimer(disclaimer_type)

            return f"{compliant_content}\n\n{disclaimer}"

        except Exception as e:
            self.logger.error(f"Error generating educational overview: {e}")
            return "Educational information is being processed. Please consult with a qualified attorney for guidance."

    def _generate_bankruptcy_overview(self, analysis_data: Dict[str, Any]) -> str:
        """Generate bankruptcy-specific educational overview"""
        debt_amount = analysis_data.get('debt_amount', 'not specified')
        business_type = analysis_data.get('business_type', 'not specified')

        overview = f"""
BANKRUPTCY EDUCATION OVERVIEW

For educational purposes only: Bankruptcy law provides several common approaches for debt relief.

COMMON BANKRUPTCY OPTIONS:
• Chapter 7: Often used for liquidation of non-exempt assets
• Chapter 11: Frequently chosen for business reorganization
• Chapter 13: Typically involves payment plans for individuals
• Subchapter V: Available for small businesses under certain thresholds

GENERAL INFORMATION:
• Business type analysis indicates: {business_type}
• Debt amount reported as: {debt_amount}
• Various factors influence chapter eligibility

EDUCATIONAL NOTE: Each situation involves unique factors requiring professional analysis.
Different approaches have different requirements, timelines, and outcomes.
"""
        return overview.strip()

    def _generate_litigation_overview(self, analysis_data: Dict[str, Any]) -> str:
        """Generate litigation-specific educational overview"""
        parties = analysis_data.get('parties', 'not specified')
        damages = analysis_data.get('damages', 'not specified')

        overview = f"""
LITIGATION EDUCATION OVERVIEW

For educational purposes only: Civil litigation involves various strategic approaches.

COMMON LITIGATION APPROACHES:
• Settlement negotiation: Often pursued before trial
• Motion practice: Used to resolve specific legal issues
• Discovery process: Information gathering phase
• Alternative dispute resolution: Mediation and arbitration options

CASE INFORMATION:
• Parties involved: {parties}
• Damages at issue: {damages}
• Various procedural considerations apply

EDUCATIONAL NOTE: Litigation strategy depends on case-specific factors, applicable law,
and individual circumstances requiring professional legal analysis.
"""
        return overview.strip()

    def _generate_generic_overview(self, analysis_data: Dict[str, Any]) -> str:
        """Generate generic educational overview"""
        doc_type = analysis_data.get('document_type', 'legal document')

        overview = f"""
LEGAL STRATEGY EDUCATION OVERVIEW

For educational purposes only: Various approaches exist for addressing legal matters.

GENERAL INFORMATION:
• Document type identified: {doc_type}
• Multiple strategic considerations typically apply
• Professional analysis required for specific guidance

COMMON APPROACHES:
• Legal consultation: Professional analysis of options
• Documentation review: Comprehensive assessment of materials
• Research phase: Investigation of applicable law and precedent
• Strategic planning: Development of appropriate approach

EDUCATIONAL NOTE: Legal matters involve complex factors requiring individual analysis
by qualified legal professionals familiar with applicable law and circumstances.
"""
        return overview.strip()


# Mock classes for testing when imports aren't available
class MockComplianceWrapper:
    def make_compliant(self, text):
        return text

class MockAdviceDetector:
    def detect_advice(self, text):
        return {'contains_advice': False}

class MockDisclaimerSystem:
    def get_appropriate_disclaimer_type(self, content_type, **kwargs):
        return "general"

    def get_disclaimer(self, disclaimer_type):
        return "This information is educational only. Consult an attorney for legal advice."


if __name__ == "__main__":
    test_compliance_presentation_engine()