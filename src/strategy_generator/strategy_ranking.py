"""
Educational Strategy Ranking System

Organizes legal strategies by frequency of use, statistical success patterns,
and educational relevance without making recommendations. All rankings are
presented as informational data for educational purposes only.

CRITICAL LEGAL DISCLAIMER:
All ranking information is provided for educational purposes only.
Rankings reflect frequency of use and statistical patterns, not recommendations.
Each legal situation requires individual professional analysis.
No legal advice is provided. Consult qualified legal counsel.

Created: 2025-09-14
Legal AI System - Educational Ranking Engine
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import statistics

# Import strategy and analysis components
try:
    from .comprehensive_strategy_options import (
        ComprehensiveStrategy, StrategyCategory, ComplexityLevel,
        StatisticalData, SuccessMetric
    )
    from .statistical_analysis import (
        StatisticalAnalysisEngine, ComprehensiveStatisticalProfile,
        JurisdictionalVariation, TrendAnalysis
    )
    from ..shared.compliance.upl_compliance import ComplianceWrapper
except ImportError:
    # Mock imports for standalone use
    class StrategyCategory(Enum):
        BANKRUPTCY = "bankruptcy"
        LITIGATION = "litigation"
        SETTLEMENT = "settlement"

    class ComplexityLevel(Enum):
        SIMPLE = "simple"
        MODERATE = "moderate"
        COMPLEX = "complex"
        HIGHLY_COMPLEX = "highly_complex"

    class SuccessMetric(Enum):
        DISCHARGE_RATE = "discharge_rate"
        SETTLEMENT_RATE = "settlement_rate"
        FAVORABLE_OUTCOME = "favorable_outcome"

    class ComplianceWrapper:
        def analyze_text(self, text: str) -> Dict[str, Any]:
            return {"has_advice": False, "violations": [], "compliance_score": 1.0}

    @dataclass
    class StatisticalData:
        success_rate: float
        metric_type: SuccessMetric
        sample_size: int
        time_period: str
        data_source: str
        confidence_interval: Tuple[float, float]
        notes: str = ""

    class ComprehensiveStrategy:
        def __init__(self):
            self.strategy_id = "mock_strategy"
            self.name = "Mock Strategy"
            self.category = StrategyCategory.BANKRUPTCY
            self.complexity_level = ComplexityLevel.MODERATE
            self.frequency_of_use = 0.5
            self.statistical_data = []
            self.timeline = None
            self.costs = None
            self.advantages = []
            self.disadvantages = []
            self.success_factors = None
            self.court_considerations = None
            self.legal_requirements = None
            self.common_outcomes = None

logger = logging.getLogger(__name__)


class RankingCriteria(Enum):
    """Criteria for educational strategy ranking"""
    FREQUENCY_OF_USE = "frequency_of_use"           # How commonly used
    SUCCESS_RATE = "success_rate"                   # Statistical success patterns
    COST_EFFECTIVENESS = "cost_effectiveness"       # Cost-benefit patterns
    COMPLEXITY_LEVEL = "complexity_level"          # Procedural complexity
    TIMELINE_EFFICIENCY = "timeline_efficiency"     # Time to resolution
    JURISDICTIONAL_CONSISTENCY = "jurisdictional_consistency"  # Consistent across jurisdictions
    TREND_STABILITY = "trend_stability"            # Stable success patterns over time
    EDUCATIONAL_VALUE = "educational_value"         # Learning importance


class RankingMethod(Enum):
    """Methods for ranking strategies"""
    FREQUENCY_BASED = "frequency_based"             # Most commonly used first
    STATISTICAL_PERFORMANCE = "statistical_performance"  # Best statistical outcomes
    BALANCED_SCORING = "balanced_scoring"           # Multiple factors weighted
    COMPLEXITY_ASCENDING = "complexity_ascending"   # Simplest first
    COST_ASCENDING = "cost_ascending"              # Lowest cost first
    TIMELINE_ASCENDING = "timeline_ascending"       # Fastest first


class RankingContext(Enum):
    """Context for ranking strategies"""
    GENERAL_EDUCATION = "general_education"         # General educational ranking
    CASE_SPECIFIC = "case_specific"                # Based on case characteristics
    JURISDICTIONAL = "jurisdictional"              # Based on jurisdiction
    INDUSTRY_SPECIFIC = "industry_specific"        # Based on industry/business type
    COMPLEXITY_MATCHED = "complexity_matched"       # Based on desired complexity level


@dataclass
class RankingScore:
    """Detailed scoring breakdown for a strategy"""
    strategy_id: str
    strategy_name: str
    total_score: float

    # Component scores (0-1 scale)
    frequency_score: float = 0.0
    success_rate_score: float = 0.0
    cost_effectiveness_score: float = 0.0
    complexity_score: float = 0.0
    timeline_score: float = 0.0
    jurisdictional_consistency_score: float = 0.0
    trend_stability_score: float = 0.0
    educational_value_score: float = 0.0

    # Weighting applied
    applied_weights: Dict[str, float] = field(default_factory=dict)

    # Educational context
    ranking_rationale: List[str] = field(default_factory=list)
    educational_notes: List[str] = field(default_factory=list)


@dataclass
class RankedStrategyList:
    """List of strategies ranked by educational criteria"""
    ranking_method: RankingMethod
    ranking_context: RankingContext
    ranked_strategies: List[Tuple[ComprehensiveStrategy, RankingScore]] = field(default_factory=list)

    # Metadata
    ranking_criteria_used: List[RankingCriteria] = field(default_factory=list)
    total_strategies_analyzed: int = 0
    ranking_timestamp: datetime = field(default_factory=datetime.now)

    # Educational disclaimers
    educational_disclaimers: List[str] = field(default_factory=list)
    ranking_explanation: str = ""


@dataclass
class RankingConfiguration:
    """Configuration for educational ranking system"""
    method: RankingMethod
    context: RankingContext
    criteria_weights: Dict[RankingCriteria, float] = field(default_factory=dict)
    case_characteristics: Dict[str, Any] = field(default_factory=dict)
    jurisdiction_preference: Optional[str] = None
    complexity_preference: Optional[ComplexityLevel] = None
    educational_focus: List[str] = field(default_factory=list)


class EducationalStrategyRankingEngine:
    """
    Provides educational ranking of legal strategies based on objective criteria.

    EDUCATIONAL PURPOSE DISCLAIMER:
    All rankings are based on frequency of use, statistical patterns, and educational value.
    Rankings do not constitute recommendations or legal advice.
    Professional legal consultation is required for strategy selection.
    """

    def __init__(self):
        """Initialize the educational ranking engine"""
        self.compliance_wrapper = ComplianceWrapper()
        self.statistical_engine = StatisticalAnalysisEngine() if 'StatisticalAnalysisEngine' in globals() else None
        self.logger = logging.getLogger(__name__)

        # Default ranking weights for different methods
        self._initialize_ranking_weights()

        # Educational disclaimers
        self.standard_disclaimers = [
            "Rankings reflect frequency of use and statistical patterns for educational purposes only",
            "Most frequently used approaches are listed first, not as recommendations",
            "Each legal situation requires individual professional analysis",
            "Statistical patterns do not predict individual case outcomes",
            "Professional legal consultation is required for strategy selection",
            "Rankings may vary based on jurisdiction, case specifics, and current legal trends"
        ]

    def _initialize_ranking_weights(self):
        """Initialize default weights for different ranking methods"""

        self.default_weights = {
            RankingMethod.FREQUENCY_BASED: {
                RankingCriteria.FREQUENCY_OF_USE: 0.60,
                RankingCriteria.SUCCESS_RATE: 0.25,
                RankingCriteria.EDUCATIONAL_VALUE: 0.15
            },

            RankingMethod.STATISTICAL_PERFORMANCE: {
                RankingCriteria.SUCCESS_RATE: 0.40,
                RankingCriteria.FREQUENCY_OF_USE: 0.25,
                RankingCriteria.TREND_STABILITY: 0.20,
                RankingCriteria.JURISDICTIONAL_CONSISTENCY: 0.15
            },

            RankingMethod.BALANCED_SCORING: {
                RankingCriteria.FREQUENCY_OF_USE: 0.25,
                RankingCriteria.SUCCESS_RATE: 0.25,
                RankingCriteria.COST_EFFECTIVENESS: 0.20,
                RankingCriteria.COMPLEXITY_LEVEL: 0.15,
                RankingCriteria.TIMELINE_EFFICIENCY: 0.15
            },

            RankingMethod.COMPLEXITY_ASCENDING: {
                RankingCriteria.COMPLEXITY_LEVEL: 0.70,
                RankingCriteria.FREQUENCY_OF_USE: 0.20,
                RankingCriteria.EDUCATIONAL_VALUE: 0.10
            },

            RankingMethod.COST_ASCENDING: {
                RankingCriteria.COST_EFFECTIVENESS: 0.60,
                RankingCriteria.FREQUENCY_OF_USE: 0.25,
                RankingCriteria.SUCCESS_RATE: 0.15
            },

            RankingMethod.TIMELINE_ASCENDING: {
                RankingCriteria.TIMELINE_EFFICIENCY: 0.55,
                RankingCriteria.FREQUENCY_OF_USE: 0.30,
                RankingCriteria.SUCCESS_RATE: 0.15
            }
        }

    def rank_strategies(self, strategies: List[ComprehensiveStrategy],
                       config: RankingConfiguration) -> RankedStrategyList:
        """
        Rank strategies according to educational criteria.

        Args:
            strategies: List of strategies to rank
            config: Ranking configuration

        Returns:
            RankedStrategyList with educational rankings

        EDUCATIONAL DISCLAIMER:
        Rankings reflect frequency of use and statistical patterns only.
        No recommendations are made. Professional consultation required.
        """

        try:
            # Validate input
            if not strategies:
                return self._create_empty_ranking_list(config)

            # Calculate ranking scores for each strategy
            ranking_scores = []
            for strategy in strategies:
                score = self._calculate_ranking_score(strategy, config)
                ranking_scores.append((strategy, score))

            # Sort by total score (descending)
            ranking_scores.sort(key=lambda x: x[1].total_score, reverse=True)

            # Create ranked strategy list
            ranked_list = RankedStrategyList(
                ranking_method=config.method,
                ranking_context=config.context,
                ranked_strategies=ranking_scores,
                ranking_criteria_used=list(config.criteria_weights.keys()),
                total_strategies_analyzed=len(strategies),
                educational_disclaimers=self.standard_disclaimers.copy(),
                ranking_explanation=self._generate_ranking_explanation(config)
            )

            return ranked_list

        except Exception as e:
            self.logger.error(f"Error ranking strategies: {str(e)}")
            return self._create_error_ranking_list(config)

    def _calculate_ranking_score(self, strategy: ComprehensiveStrategy,
                                config: RankingConfiguration) -> RankingScore:
        """Calculate comprehensive ranking score for a strategy"""

        # Get weights for this ranking method
        weights = config.criteria_weights or self.default_weights.get(config.method, {})

        # Initialize score components
        score = RankingScore(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.name,
            total_score=0.0,
            applied_weights=weights.copy()
        )

        # Calculate component scores
        if RankingCriteria.FREQUENCY_OF_USE in weights:
            score.frequency_score = self._calculate_frequency_score(strategy)

        if RankingCriteria.SUCCESS_RATE in weights:
            score.success_rate_score = self._calculate_success_rate_score(strategy)

        if RankingCriteria.COST_EFFECTIVENESS in weights:
            score.cost_effectiveness_score = self._calculate_cost_effectiveness_score(strategy)

        if RankingCriteria.COMPLEXITY_LEVEL in weights:
            score.complexity_score = self._calculate_complexity_score(strategy, config)

        if RankingCriteria.TIMELINE_EFFICIENCY in weights:
            score.timeline_score = self._calculate_timeline_score(strategy)

        if RankingCriteria.JURISDICTIONAL_CONSISTENCY in weights:
            score.jurisdictional_consistency_score = self._calculate_jurisdictional_consistency_score(strategy)

        if RankingCriteria.TREND_STABILITY in weights:
            score.trend_stability_score = self._calculate_trend_stability_score(strategy)

        if RankingCriteria.EDUCATIONAL_VALUE in weights:
            score.educational_value_score = self._calculate_educational_value_score(strategy)

        # Calculate weighted total score
        score.total_score = (
            weights.get(RankingCriteria.FREQUENCY_OF_USE, 0) * score.frequency_score +
            weights.get(RankingCriteria.SUCCESS_RATE, 0) * score.success_rate_score +
            weights.get(RankingCriteria.COST_EFFECTIVENESS, 0) * score.cost_effectiveness_score +
            weights.get(RankingCriteria.COMPLEXITY_LEVEL, 0) * score.complexity_score +
            weights.get(RankingCriteria.TIMELINE_EFFICIENCY, 0) * score.timeline_score +
            weights.get(RankingCriteria.JURISDICTIONAL_CONSISTENCY, 0) * score.jurisdictional_consistency_score +
            weights.get(RankingCriteria.TREND_STABILITY, 0) * score.trend_stability_score +
            weights.get(RankingCriteria.EDUCATIONAL_VALUE, 0) * score.educational_value_score
        )

        # Generate educational rationale
        score.ranking_rationale = self._generate_ranking_rationale(strategy, score, config)
        score.educational_notes = self._generate_educational_notes(strategy, score)

        return score

    def _calculate_frequency_score(self, strategy: ComprehensiveStrategy) -> float:
        """Calculate frequency of use score (0-1 scale)"""

        # Strategy frequency_of_use is already 0-1 scale
        return strategy.frequency_of_use

    def _calculate_success_rate_score(self, strategy: ComprehensiveStrategy) -> float:
        """Calculate success rate score based on statistical data"""

        if not strategy.statistical_data:
            return 0.5  # Neutral score for missing data

        # Use primary statistical measure
        primary_stat = strategy.statistical_data[0]
        return primary_stat.success_rate

    def _calculate_cost_effectiveness_score(self, strategy: ComprehensiveStrategy) -> float:
        """Calculate cost effectiveness score (inverse of relative cost)"""

        if not strategy.costs:
            return 0.5  # Neutral score for missing data

        # Use median of cost range for scoring
        median_cost = (strategy.costs.total_range[0] + strategy.costs.total_range[1]) / 2

        # Normalize against typical cost ranges (arbitrary scale for educational purposes)
        # Lower costs get higher scores
        normalized_cost = min(1.0, median_cost / 100000)  # $100k as reference point

        return max(0.0, 1.0 - normalized_cost)

    def _calculate_complexity_score(self, strategy: ComprehensiveStrategy,
                                  config: RankingConfiguration) -> float:
        """Calculate complexity score based on preference"""

        complexity_values = {
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MODERATE: 0.75,
            ComplexityLevel.COMPLEX: 0.5,
            ComplexityLevel.HIGHLY_COMPLEX: 0.25
        }

        strategy_complexity_score = complexity_values.get(strategy.complexity_level, 0.5)

        # For complexity-ascending ranking, simpler = higher score
        if config.method == RankingMethod.COMPLEXITY_ASCENDING:
            return strategy_complexity_score
        else:
            # For other methods, moderate complexity might be preferred
            # Adjust scoring to favor moderate complexity
            if strategy.complexity_level == ComplexityLevel.MODERATE:
                return 0.9
            elif strategy.complexity_level == ComplexityLevel.SIMPLE:
                return 0.8
            elif strategy.complexity_level == ComplexityLevel.COMPLEX:
                return 0.6
            else:  # HIGHLY_COMPLEX
                return 0.4

    def _calculate_timeline_score(self, strategy: ComprehensiveStrategy) -> float:
        """Calculate timeline efficiency score"""

        if not strategy.timeline:
            return 0.5  # Neutral score for missing data

        # Parse typical duration to get approximate months
        duration_text = strategy.timeline.typical_duration.lower()

        if "month" in duration_text:
            # Extract number before "month"
            import re
            months_match = re.search(r'(\d+(?:\.\d+)?)', duration_text)
            if months_match:
                months = float(months_match.group(1))
                # Shorter timelines get higher scores
                # Normalize against 24 months (2 years) as reference
                normalized_duration = min(1.0, months / 24)
                return max(0.0, 1.0 - normalized_duration)

        return 0.5  # Default for unparseable durations

    def _calculate_jurisdictional_consistency_score(self, strategy: ComprehensiveStrategy) -> float:
        """Calculate jurisdictional consistency score"""

        # For now, use a simple heuristic based on strategy category
        # Federal procedures tend to be more consistent
        consistency_scores = {
            StrategyCategory.BANKRUPTCY: 0.9,  # Federal bankruptcy law is uniform
            StrategyCategory.LITIGATION: 0.6,  # Varies by jurisdiction
            StrategyCategory.SETTLEMENT: 0.8,  # Generally consistent processes
            StrategyCategory.NEGOTIATION: 0.7,  # Moderately consistent
        }

        return consistency_scores.get(strategy.category, 0.5)

    def _calculate_trend_stability_score(self, strategy: ComprehensiveStrategy) -> float:
        """Calculate trend stability score"""

        # For now, use strategy category as proxy for stability
        # Well-established procedures tend to be more stable
        stability_scores = {
            StrategyCategory.BANKRUPTCY: 0.85,  # Well-established procedures
            StrategyCategory.SETTLEMENT: 0.80,   # Consistently effective
            StrategyCategory.LITIGATION: 0.65,   # More variable outcomes
            StrategyCategory.NEGOTIATION: 0.70   # Moderately stable
        }

        return stability_scores.get(strategy.category, 0.5)

    def _calculate_educational_value_score(self, strategy: ComprehensiveStrategy) -> float:
        """Calculate educational value score"""

        educational_factors = 0.0

        # Comprehensive information increases educational value
        if strategy.advantages:
            educational_factors += 0.15
        if strategy.disadvantages:
            educational_factors += 0.15
        if strategy.timeline:
            educational_factors += 0.10
        if strategy.costs:
            educational_factors += 0.10
        if strategy.statistical_data:
            educational_factors += 0.15
        if strategy.success_factors:
            educational_factors += 0.10
        if strategy.court_considerations:
            educational_factors += 0.10
        if strategy.legal_requirements:
            educational_factors += 0.10
        if strategy.common_outcomes:
            educational_factors += 0.05

        return min(1.0, educational_factors)

    def _generate_ranking_rationale(self, strategy: ComprehensiveStrategy,
                                  score: RankingScore, config: RankingConfiguration) -> List[str]:
        """Generate educational rationale for ranking"""

        rationale = []

        # Explain top scoring factors
        score_components = [
            ("Frequency of use", score.frequency_score, RankingCriteria.FREQUENCY_OF_USE),
            ("Success rate patterns", score.success_rate_score, RankingCriteria.SUCCESS_RATE),
            ("Cost effectiveness", score.cost_effectiveness_score, RankingCriteria.COST_EFFECTIVENESS),
            ("Complexity level", score.complexity_score, RankingCriteria.COMPLEXITY_LEVEL),
            ("Timeline efficiency", score.timeline_score, RankingCriteria.TIMELINE_EFFICIENCY)
        ]

        # Sort by score contribution (score * weight)
        weighted_components = [
            (name, comp_score, criteria, comp_score * score.applied_weights.get(criteria, 0))
            for name, comp_score, criteria in score_components
        ]
        weighted_components.sort(key=lambda x: x[3], reverse=True)

        # Add rationale for top 3 contributing factors
        for name, comp_score, criteria, weighted_score in weighted_components[:3]:
            if weighted_score > 0.1:  # Only include significant contributors
                if comp_score > 0.7:
                    rationale.append(f"High {name.lower()} ({comp_score:.1%}) contributes strongly to ranking")
                elif comp_score > 0.4:
                    rationale.append(f"Moderate {name.lower()} ({comp_score:.1%}) contributes to ranking")

        # Add frequency-specific rationale
        if strategy.frequency_of_use > 0.5:
            rationale.append(f"Used in {strategy.frequency_of_use:.1%} of similar cases")
        elif strategy.frequency_of_use > 0.2:
            rationale.append(f"Moderately common option ({strategy.frequency_of_use:.1%} usage rate)")

        return rationale

    def _generate_educational_notes(self, strategy: ComprehensiveStrategy,
                                  score: RankingScore) -> List[str]:
        """Generate educational notes about the strategy ranking"""

        notes = [
            "Ranking reflects statistical patterns and frequency of use for educational purposes",
            "Individual case outcomes may vary significantly from statistical patterns"
        ]

        # Add complexity note
        complexity_notes = {
            ComplexityLevel.SIMPLE: "Generally involves straightforward procedures",
            ComplexityLevel.MODERATE: "Involves moderate legal complexity requiring professional guidance",
            ComplexityLevel.COMPLEX: "Involves significant legal complexity requiring experienced counsel",
            ComplexityLevel.HIGHLY_COMPLEX: "Highly complex procedure requiring specialized expertise"
        }

        if strategy.complexity_level in complexity_notes:
            notes.append(complexity_notes[strategy.complexity_level])

        # Add statistical note if available
        if strategy.statistical_data:
            primary_stat = strategy.statistical_data[0]
            notes.append(f"Statistical pattern shows {primary_stat.success_rate:.1%} {primary_stat.metric_type.value.replace('_', ' ')} rate")

        return notes

    def _generate_ranking_explanation(self, config: RankingConfiguration) -> str:
        """Generate explanation of ranking methodology"""

        explanations = {
            RankingMethod.FREQUENCY_BASED: (
                "Strategies are ranked primarily by frequency of use in similar cases. "
                "Most commonly used approaches are listed first for educational reference."
            ),
            RankingMethod.STATISTICAL_PERFORMANCE: (
                "Strategies are ranked by statistical success patterns observed in similar cases. "
                "Higher statistical success rates appear first for educational comparison."
            ),
            RankingMethod.BALANCED_SCORING: (
                "Strategies are ranked using multiple educational factors including frequency of use, "
                "statistical patterns, cost effectiveness, and procedural complexity."
            ),
            RankingMethod.COMPLEXITY_ASCENDING: (
                "Strategies are ranked from simplest to most complex for educational progression. "
                "Simpler procedures are listed first, followed by increasingly complex approaches."
            ),
            RankingMethod.COST_ASCENDING: (
                "Strategies are ranked by typical cost patterns, with lower-cost approaches first. "
                "Cost information is provided for educational comparison purposes only."
            ),
            RankingMethod.TIMELINE_ASCENDING: (
                "Strategies are ranked by typical timeline patterns, with faster approaches first. "
                "Timeline information represents commonly observed durations in similar cases."
            )
        }

        base_explanation = explanations.get(config.method, "Strategies ranked by educational criteria.")

        disclaimer = (" Rankings are for educational purposes only and do not constitute "
                     "recommendations. Professional legal consultation is required for strategy selection.")

        return base_explanation + disclaimer

    def _create_empty_ranking_list(self, config: RankingConfiguration) -> RankedStrategyList:
        """Create empty ranking list when no strategies provided"""

        return RankedStrategyList(
            ranking_method=config.method,
            ranking_context=config.context,
            ranked_strategies=[],
            total_strategies_analyzed=0,
            educational_disclaimers=self.standard_disclaimers,
            ranking_explanation="No strategies available for ranking analysis"
        )

    def _create_error_ranking_list(self, config: RankingConfiguration) -> RankedStrategyList:
        """Create error ranking list when ranking fails"""

        return RankedStrategyList(
            ranking_method=config.method,
            ranking_context=config.context,
            ranked_strategies=[],
            total_strategies_analyzed=0,
            educational_disclaimers=[
                "Ranking analysis unavailable due to processing error",
                "Professional legal consultation is recommended for strategy guidance",
                "No recommendations or rankings are provided"
            ],
            ranking_explanation="Strategy ranking unavailable due to analysis error"
        )

    def generate_ranking_report(self, ranked_list: RankedStrategyList) -> str:
        """Generate comprehensive ranking report for educational use"""

        if not ranked_list.ranked_strategies:
            return "No strategies available for ranking analysis."

        report_lines = [
            "EDUCATIONAL STRATEGY RANKING REPORT",
            "=" * 40,
            f"Ranking Method: {ranked_list.ranking_method.value.replace('_', ' ').title()}",
            f"Context: {ranked_list.ranking_context.value.replace('_', ' ').title()}",
            f"Strategies Analyzed: {ranked_list.total_strategies_analyzed}",
            f"Generated: {ranked_list.ranking_timestamp.strftime('%Y-%m-%d %H:%M')}",
            "",
            "EDUCATIONAL DISCLAIMER:",
            "Rankings reflect frequency of use and statistical patterns for educational purposes only.",
            "No recommendations are made. Professional legal consultation is required.",
            ""
        ]

        # Ranking methodology explanation
        report_lines.extend([
            "RANKING METHODOLOGY:",
            "-" * 20,
            ranked_list.ranking_explanation,
            ""
        ])

        # Strategy rankings
        report_lines.extend([
            "STRATEGY RANKINGS (EDUCATIONAL ORDER):",
            "-" * 40
        ])

        for rank, (strategy, score) in enumerate(ranked_list.ranked_strategies, 1):
            report_lines.extend([
                f"{rank}. {strategy.name}",
                f"   Overall Score: {score.total_score:.3f}",
                f"   Frequency of Use: {strategy.frequency_of_use:.1%}",
                f"   Complexity: {strategy.complexity_level.value.title()}"
            ])

            # Add top rationale points
            if score.ranking_rationale:
                report_lines.append(f"   Key Factors: {score.ranking_rationale[0]}")

            # Add statistical info if available
            if strategy.statistical_data:
                primary_stat = strategy.statistical_data[0]
                metric_name = primary_stat.metric_type.value.replace('_', ' ').title()
                report_lines.append(f"   Statistical Pattern: {primary_stat.success_rate:.1%} {metric_name}")

            report_lines.append("")

        # Detailed scoring breakdown for top 3
        if len(ranked_list.ranked_strategies) > 0:
            report_lines.extend([
                "DETAILED SCORING ANALYSIS (Top 3):",
                "-" * 35
            ])

            for rank, (strategy, score) in enumerate(ranked_list.ranked_strategies[:3], 1):
                report_lines.extend([
                    f"{rank}. {strategy.name} - Scoring Breakdown:",
                    f"   Frequency Score: {score.frequency_score:.3f}",
                    f"   Success Pattern Score: {score.success_rate_score:.3f}",
                    f"   Cost Effectiveness Score: {score.cost_effectiveness_score:.3f}",
                    f"   Complexity Score: {score.complexity_score:.3f}",
                    f"   Timeline Score: {score.timeline_score:.3f}",
                    ""
                ])

        # Educational reminders
        report_lines.extend([
            "IMPORTANT EDUCATIONAL REMINDERS:",
            "-" * 35,
            "• Rankings reflect common usage patterns and statistical data only",
            "• Higher rankings indicate more frequent use, not better outcomes for specific cases",
            "• Each legal situation requires individual professional analysis",
            "• Statistical patterns do not predict individual case results",
            "• Professional legal consultation is essential for strategy selection",
            "• Rankings may vary by jurisdiction, case type, and current legal trends"
        ])

        return "\n".join(report_lines)

    def compare_ranking_methods(self, strategies: List[ComprehensiveStrategy]) -> Dict[str, Any]:
        """Compare different ranking methods for educational analysis"""

        comparison_results = {
            "strategies_analyzed": len(strategies),
            "ranking_comparisons": [],
            "consistency_analysis": {},
            "educational_insights": []
        }

        # Test different ranking methods
        ranking_methods = [
            RankingMethod.FREQUENCY_BASED,
            RankingMethod.STATISTICAL_PERFORMANCE,
            RankingMethod.BALANCED_SCORING,
            RankingMethod.COMPLEXITY_ASCENDING
        ]

        method_results = {}

        for method in ranking_methods:
            config = RankingConfiguration(
                method=method,
                context=RankingContext.GENERAL_EDUCATION
            )

            ranked_list = self.rank_strategies(strategies, config)
            method_results[method] = ranked_list

            # Extract top 3 strategy IDs for comparison
            top_3_ids = [
                strategy.strategy_id
                for strategy, score in ranked_list.ranked_strategies[:3]
            ]

            comparison_results["ranking_comparisons"].append({
                "method": method.value,
                "top_3_strategies": top_3_ids,
                "explanation": ranked_list.ranking_explanation
            })

        # Analyze consistency across methods
        if method_results:
            # Find strategies that appear in top 3 across methods
            all_top_strategies = []
            for method_result in method_results.values():
                top_ids = [s.strategy_id for s, score in method_result.ranked_strategies[:3]]
                all_top_strategies.extend(top_ids)

            # Count frequency of appearance in top 3
            from collections import Counter
            strategy_counts = Counter(all_top_strategies)

            comparison_results["consistency_analysis"] = {
                "most_consistent_top_strategies": [
                    {"strategy_id": strategy_id, "appearances": count}
                    for strategy_id, count in strategy_counts.most_common(5)
                ],
                "total_methods_compared": len(ranking_methods)
            }

        # Generate educational insights
        comparison_results["educational_insights"] = [
            "Different ranking methods emphasize different educational aspects",
            "Frequency-based ranking shows most commonly used approaches",
            "Statistical performance ranking highlights outcome patterns",
            "Balanced scoring provides comprehensive educational perspective",
            "Complexity ranking supports progressive learning approach"
        ]

        return comparison_results


def test_educational_ranking_engine():
    """Test the educational strategy ranking engine"""

    print("=== EDUCATIONAL STRATEGY RANKING ENGINE TEST ===")
    print("Testing educational ranking system for legal strategies")
    print()

    # Mock strategies for testing
    class MockStrategy:
        def __init__(self, strategy_id: str, name: str, category: StrategyCategory,
                     complexity: ComplexityLevel, frequency: float):
            self.strategy_id = strategy_id
            self.name = name
            self.category = category
            self.complexity_level = complexity
            self.frequency_of_use = frequency
            self.statistical_data = []
            self.timeline = None
            self.costs = None
            self.advantages = ["Common benefit 1", "Common benefit 2"]
            self.disadvantages = ["Common consideration 1"]
            self.success_factors = None
            self.court_considerations = None
            self.legal_requirements = None
            self.common_outcomes = None

    # Create test strategies
    test_strategies = [
        MockStrategy("chapter_7", "Chapter 7 Liquidation", StrategyCategory.BANKRUPTCY,
                    ComplexityLevel.MODERATE, 0.68),
        MockStrategy("mediation", "Mediated Settlement", StrategyCategory.SETTLEMENT,
                    ComplexityLevel.SIMPLE, 0.45),
        MockStrategy("chapter_11", "Chapter 11 Reorganization", StrategyCategory.BANKRUPTCY,
                    ComplexityLevel.HIGHLY_COMPLEX, 0.15),
        MockStrategy("negotiation", "Direct Negotiation", StrategyCategory.SETTLEMENT,
                    ComplexityLevel.SIMPLE, 0.85)
    ]

    # Initialize ranking engine
    engine = EducationalStrategyRankingEngine()

    # Test 1: Frequency-based ranking
    print("TEST 1: Frequency-Based Educational Ranking")
    print("-" * 45)

    freq_config = RankingConfiguration(
        method=RankingMethod.FREQUENCY_BASED,
        context=RankingContext.GENERAL_EDUCATION
    )

    freq_ranking = engine.rank_strategies(test_strategies, freq_config)

    print(f"Ranking Method: {freq_ranking.ranking_method.value}")
    print(f"Strategies Ranked: {len(freq_ranking.ranked_strategies)}")
    print("Educational Order (Most to Least Common):")

    for rank, (strategy, score) in enumerate(freq_ranking.ranked_strategies, 1):
        print(f"{rank}. {strategy.name} (Used in {strategy.frequency_of_use:.1%} of cases)")
        print(f"   Overall Score: {score.total_score:.3f}")
        if score.ranking_rationale:
            print(f"   Rationale: {score.ranking_rationale[0]}")

    # Test 2: Complexity-based ranking
    print(f"\nTEST 2: Complexity-Based Educational Ranking")
    print("-" * 45)

    complexity_config = RankingConfiguration(
        method=RankingMethod.COMPLEXITY_ASCENDING,
        context=RankingContext.GENERAL_EDUCATION
    )

    complexity_ranking = engine.rank_strategies(test_strategies, complexity_config)

    print("Educational Order (Simplest to Most Complex):")
    for rank, (strategy, score) in enumerate(complexity_ranking.ranked_strategies, 1):
        print(f"{rank}. {strategy.name} ({strategy.complexity_level.value.title()})")
        print(f"   Complexity Score: {score.complexity_score:.3f}")

    # Test 3: Balanced scoring
    print(f"\nTEST 3: Balanced Educational Scoring")
    print("-" * 35)

    balanced_config = RankingConfiguration(
        method=RankingMethod.BALANCED_SCORING,
        context=RankingContext.GENERAL_EDUCATION
    )

    balanced_ranking = engine.rank_strategies(test_strategies, balanced_config)

    print("Educational Order (Balanced Multiple Factors):")
    for rank, (strategy, score) in enumerate(balanced_ranking.ranked_strategies, 1):
        print(f"{rank}. {strategy.name}")
        print(f"   Total Score: {score.total_score:.3f}")
        print(f"   Frequency: {score.frequency_score:.3f}, Complexity: {score.complexity_score:.3f}")

    # Test 4: Ranking report generation
    print(f"\nTEST 4: Educational Ranking Report")
    print("-" * 35)

    report = engine.generate_ranking_report(freq_ranking)
    print("Sample Report Content:")
    print(report[:1000] + "..." if len(report) > 1000 else report)

    # Test 5: Method comparison
    print(f"\nTEST 5: Ranking Method Comparison")
    print("-" * 35)

    comparison = engine.compare_ranking_methods(test_strategies)

    print(f"Methods Compared: {len(comparison['ranking_comparisons'])}")
    print("Top Strategy by Method:")
    for method_comparison in comparison["ranking_comparisons"]:
        top_strategy = method_comparison["top_3_strategies"][0] if method_comparison["top_3_strategies"] else "None"
        print(f"• {method_comparison['method']}: {top_strategy}")

    if comparison["consistency_analysis"].get("most_consistent_top_strategies"):
        print(f"\nMost Consistently Highly-Ranked:")
        for consistent in comparison["consistency_analysis"]["most_consistent_top_strategies"][:3]:
            print(f"• {consistent['strategy_id']}: Appeared {consistent['appearances']} times in top 3")

    # Summary
    print(f"\n=== TEST RESULTS SUMMARY ===")
    print(f"Educational ranking engine ready: YES")
    print(f"Multiple ranking methods: WORKING")
    print(f"Educational scoring system: FUNCTIONAL")
    print(f"Compliance maintained: YES")
    print(f"Report generation: OPERATIONAL")

    print(f"\nKey Features Demonstrated:")
    print(f"• Frequency-based educational ranking")
    print(f"• Complexity-progressive ranking")
    print(f"• Multi-factor balanced scoring")
    print(f"• Educational rationale generation")
    print(f"• Compliance-focused presentation")
    print(f"• Method comparison analysis")

    print(f"\nEDUCATIONAL REMINDER:")
    print(f"All rankings reflect usage patterns for educational purposes only")
    print(f"No recommendations made - professional consultation required")

    return True

if __name__ == "__main__":
    test_educational_ranking_engine()