"""
Document Processing Cost Optimizer

This module provides intelligent cost optimization for legal document processing
with multi-tier pricing strategy and usage analytics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import json
import statistics

# Configure logging
logger = logging.getLogger(__name__)


class ProcessingTier(Enum):
    """Processing tiers with cost optimization."""
    QUICK_TRIAGE = "quick_triage"        # Haiku: $0.01 per doc
    STANDARD_REVIEW = "standard_review"  # Sonnet: $0.15 per doc
    DEEP_ANALYSIS = "deep_analysis"      # Opus: $0.75 per doc


@dataclass
class TierMetrics:
    """Metrics for a processing tier."""
    name: str
    model: str
    cost_per_document: float
    total_documents: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    avg_confidence: float = 0.0
    avg_processing_time: float = 0.0
    success_rate: float = 0.0
    use_cases: List[str] = field(default_factory=list)
    confidence_range: Tuple[float, float] = (0.0, 1.0)


@dataclass
class CostAnalysis:
    """Comprehensive cost analysis result."""
    total_cost: float
    total_documents: int
    cost_per_document: float
    tier_breakdown: Dict[str, TierMetrics]
    cost_savings: Dict[str, float]
    optimization_recommendations: List[str]
    usage_trends: Dict[str, Any]
    efficiency_metrics: Dict[str, float]


@dataclass
class ProcessingRecord:
    """Record of a document processing operation."""
    document_id: str
    tier: ProcessingTier
    model_used: str
    cost: float
    tokens: int
    confidence: float
    processing_time: float
    success: bool
    timestamp: datetime
    document_type: str
    complexity_score: float
    user_id: Optional[str] = None


class CostOptimizer:
    """Cost optimizer for document processing operations."""

    def __init__(self):
        # Tier definitions with current pricing
        self.tiers = {
            ProcessingTier.QUICK_TRIAGE: TierMetrics(
                name="Quick Triage",
                model="Claude 3 Haiku",
                cost_per_document=0.01,
                use_cases=[
                    "Document classification",
                    "Simple data extraction",
                    "Basic categorization",
                    "Filing type identification"
                ],
                confidence_range=(0.65, 0.75)
            ),
            ProcessingTier.STANDARD_REVIEW: TierMetrics(
                name="Standard Review",
                model="Claude 3 Sonnet",
                cost_per_document=0.15,
                use_cases=[
                    "Document analysis",
                    "Contract review",
                    "Compliance checking",
                    "Risk assessment"
                ],
                confidence_range=(0.75, 0.85)
            ),
            ProcessingTier.DEEP_ANALYSIS: TierMetrics(
                name="Deep Analysis",
                model="Claude 3 Opus",
                cost_per_document=0.75,
                use_cases=[
                    "Critical legal review",
                    "Litigation analysis",
                    "Strategic planning",
                    "Complex compliance"
                ],
                confidence_range=(0.85, 0.95)
            )
        }

        # Processing records for analytics
        self.processing_records: List[ProcessingRecord] = []

        # Usage statistics
        self.daily_usage = defaultdict(lambda: defaultdict(int))
        self.monthly_costs = defaultdict(float)

        # Cost thresholds
        self.daily_budget = 100.0  # $100 daily budget
        self.monthly_budget = 2000.0  # $2000 monthly budget

        # Optimization settings
        self.efficiency_targets = {
            'cost_per_document': 0.20,  # Target average cost
            'min_confidence': 0.75,     # Minimum acceptable confidence
            'max_processing_time': 30.0  # Maximum processing time in seconds
        }

    def record_processing(self, record: ProcessingRecord) -> None:
        """Record a processing operation for analytics."""
        self.processing_records.append(record)

        # Update tier metrics
        tier_metrics = self.tiers[record.tier]
        tier_metrics.total_documents += 1
        tier_metrics.total_cost += record.cost
        tier_metrics.total_tokens += record.tokens

        # Update averages
        if tier_metrics.total_documents > 0:
            confidences = [r.confidence for r in self.processing_records if r.tier == record.tier]
            times = [r.processing_time for r in self.processing_records if r.tier == record.tier]
            successes = [r.success for r in self.processing_records if r.tier == record.tier]

            tier_metrics.avg_confidence = statistics.mean(confidences) if confidences else 0.0
            tier_metrics.avg_processing_time = statistics.mean(times) if times else 0.0
            tier_metrics.success_rate = sum(successes) / len(successes) if successes else 0.0

        # Update daily usage
        date_key = record.timestamp.strftime('%Y-%m-%d')
        self.daily_usage[date_key][record.tier.value] += 1

        # Update monthly costs
        month_key = record.timestamp.strftime('%Y-%m')
        self.monthly_costs[month_key] += record.cost

    def get_tier_recommendation(
        self,
        document_type: str,
        complexity_score: float,
        task_type: str,
        max_cost: Optional[float] = None,
        min_confidence: Optional[float] = None
    ) -> Tuple[ProcessingTier, str]:
        """
        Get tier recommendation based on document characteristics and constraints.

        Returns:
            Tuple of (recommended_tier, reasoning)
        """

        # Task-specific recommendations
        task_tier_mapping = {
            'classification': ProcessingTier.QUICK_TRIAGE,
            'simple_extraction': ProcessingTier.QUICK_TRIAGE,
            'basic_analysis': ProcessingTier.STANDARD_REVIEW,
            'contract_review': ProcessingTier.STANDARD_REVIEW,
            'compliance_check': ProcessingTier.STANDARD_REVIEW,
            'litigation_analysis': ProcessingTier.DEEP_ANALYSIS,
            'strategic_planning': ProcessingTier.DEEP_ANALYSIS,
            'critical_review': ProcessingTier.DEEP_ANALYSIS
        }

        # Start with task-based recommendation
        recommended_tier = task_tier_mapping.get(task_type, ProcessingTier.STANDARD_REVIEW)
        reasoning = f"Task type '{task_type}' typically requires {recommended_tier.value}"

        # Adjust based on complexity
        if complexity_score >= 0.8:
            if recommended_tier != ProcessingTier.DEEP_ANALYSIS:
                recommended_tier = ProcessingTier.DEEP_ANALYSIS
                reasoning += f"; High complexity ({complexity_score:.2f}) requires deep analysis"
        elif complexity_score >= 0.5:
            if recommended_tier == ProcessingTier.QUICK_TRIAGE:
                recommended_tier = ProcessingTier.STANDARD_REVIEW
                reasoning += f"; Moderate complexity ({complexity_score:.2f}) requires standard review"
        else:
            if recommended_tier == ProcessingTier.DEEP_ANALYSIS and task_type not in ['litigation_analysis', 'critical_review']:
                recommended_tier = ProcessingTier.STANDARD_REVIEW
                reasoning += f"; Low complexity ({complexity_score:.2f}) allows standard review"

        # Apply cost constraints
        if max_cost is not None:
            tier_cost = self.tiers[recommended_tier].cost_per_document
            if tier_cost > max_cost:
                # Find the highest tier within budget
                for tier in [ProcessingTier.DEEP_ANALYSIS, ProcessingTier.STANDARD_REVIEW, ProcessingTier.QUICK_TRIAGE]:
                    if self.tiers[tier].cost_per_document <= max_cost:
                        recommended_tier = tier
                        reasoning += f"; Cost constraint (${max_cost:.2f}) limits to {tier.value}"
                        break

        # Apply confidence constraints
        if min_confidence is not None:
            tier_confidence = self.tiers[recommended_tier].confidence_range[0]
            if tier_confidence < min_confidence:
                # Find the lowest tier that meets confidence requirement
                for tier in [ProcessingTier.QUICK_TRIAGE, ProcessingTier.STANDARD_REVIEW, ProcessingTier.DEEP_ANALYSIS]:
                    if self.tiers[tier].confidence_range[0] >= min_confidence:
                        recommended_tier = tier
                        reasoning += f"; Confidence requirement ({min_confidence:.2f}) requires {tier.value}"
                        break

        return recommended_tier, reasoning

    def calculate_cost_savings(self) -> Dict[str, float]:
        """Calculate cost savings from using multi-tier strategy."""
        if not self.processing_records:
            return {}

        # Calculate actual costs
        actual_total_cost = sum(record.cost for record in self.processing_records)
        total_documents = len(self.processing_records)

        # Calculate what it would cost if all documents used Opus
        opus_cost_per_doc = self.tiers[ProcessingTier.DEEP_ANALYSIS].cost_per_document
        all_opus_cost = total_documents * opus_cost_per_doc

        # Calculate what it would cost if all documents used Sonnet
        sonnet_cost_per_doc = self.tiers[ProcessingTier.STANDARD_REVIEW].cost_per_document
        all_sonnet_cost = total_documents * sonnet_cost_per_doc

        # Calculate savings
        savings_vs_opus = all_opus_cost - actual_total_cost
        savings_vs_sonnet = all_sonnet_cost - actual_total_cost

        savings_percentage_opus = (savings_vs_opus / all_opus_cost * 100) if all_opus_cost > 0 else 0
        savings_percentage_sonnet = (savings_vs_sonnet / all_sonnet_cost * 100) if all_sonnet_cost > 0 else 0

        return {
            'actual_cost': actual_total_cost,
            'all_opus_cost': all_opus_cost,
            'all_sonnet_cost': all_sonnet_cost,
            'savings_vs_opus': savings_vs_opus,
            'savings_vs_sonnet': savings_vs_sonnet,
            'savings_percentage_opus': savings_percentage_opus,
            'savings_percentage_sonnet': savings_percentage_sonnet,
            'cost_per_document': actual_total_cost / total_documents if total_documents > 0 else 0
        }

    def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on usage patterns."""
        recommendations = []

        if not self.processing_records:
            return ["No processing history available for optimization recommendations"]

        # Analyze tier usage
        tier_counts = defaultdict(int)
        tier_costs = defaultdict(float)
        tier_confidences = defaultdict(list)

        for record in self.processing_records:
            tier_counts[record.tier] += 1
            tier_costs[record.tier] += record.cost
            tier_confidences[record.tier].append(record.confidence)

        total_documents = len(self.processing_records)
        total_cost = sum(tier_costs.values())

        # Check for overuse of expensive tiers
        opus_usage = tier_counts.get(ProcessingTier.DEEP_ANALYSIS, 0)
        if opus_usage / total_documents > 0.3:  # More than 30% Opus usage
            recommendations.append(
                f"Consider reducing Opus usage: {opus_usage}/{total_documents} documents ({opus_usage/total_documents*100:.1f}%). "
                "Review if all deep analysis requests truly require highest quality."
            )

        # Check for underuse of efficient tiers
        haiku_usage = tier_counts.get(ProcessingTier.QUICK_TRIAGE, 0)
        if haiku_usage / total_documents < 0.2:  # Less than 20% Haiku usage
            recommendations.append(
                f"Consider increasing Haiku usage for simple tasks: only {haiku_usage}/{total_documents} documents ({haiku_usage/total_documents*100:.1f}%). "
                "Use Haiku for classification and simple extraction to reduce costs."
            )

        # Check confidence levels
        for tier, confidences in tier_confidences.items():
            if confidences:
                avg_confidence = statistics.mean(confidences)
                tier_name = self.tiers[tier].name

                if avg_confidence < 0.7 and tier == ProcessingTier.QUICK_TRIAGE:
                    recommendations.append(
                        f"{tier_name} showing low confidence ({avg_confidence:.2f}). "
                        "Consider upgrading complex documents to Standard Review."
                    )
                elif avg_confidence > 0.9 and tier == ProcessingTier.DEEP_ANALYSIS:
                    recommendations.append(
                        f"{tier_name} showing very high confidence ({avg_confidence:.2f}). "
                        "Some documents might be suitable for Standard Review to save costs."
                    )

        # Cost efficiency recommendations
        cost_per_doc = total_cost / total_documents
        target_cost = self.efficiency_targets['cost_per_document']

        if cost_per_doc > target_cost:
            recommendations.append(
                f"Average cost per document (${cost_per_doc:.2f}) exceeds target (${target_cost:.2f}). "
                "Consider using lower-tier models for appropriate tasks."
            )

        # Budget recommendations
        if total_cost > self.monthly_budget * 0.8:  # 80% of monthly budget
            recommendations.append(
                f"Monthly costs (${total_cost:.2f}) approaching budget limit (${self.monthly_budget:.2f}). "
                "Consider implementing stricter tier selection criteria."
            )

        # Usage pattern recommendations
        recent_records = [r for r in self.processing_records if r.timestamp > datetime.now() - timedelta(days=7)]
        if recent_records:
            recent_tier_usage = defaultdict(int)
            for record in recent_records:
                recent_tier_usage[record.tier] += 1

            recent_opus_percentage = recent_tier_usage[ProcessingTier.DEEP_ANALYSIS] / len(recent_records) * 100
            if recent_opus_percentage > 40:
                recommendations.append(
                    f"Recent Opus usage is high ({recent_opus_percentage:.1f}%). "
                    "Implement batch processing and tier pre-screening to optimize costs."
                )

        if not recommendations:
            recommendations.append("Cost optimization is performing well. Continue current tier selection strategy.")

        return recommendations

    def get_usage_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get usage trends for the specified number of days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_records = [r for r in self.processing_records if r.timestamp > cutoff_date]

        if not recent_records:
            return {"message": "No recent usage data available"}

        # Daily usage trends
        daily_usage = defaultdict(lambda: defaultdict(int))
        daily_costs = defaultdict(float)

        for record in recent_records:
            date_key = record.timestamp.strftime('%Y-%m-%d')
            daily_usage[date_key][record.tier.value] += 1
            daily_costs[date_key] += record.cost

        # Calculate trends
        dates = sorted(daily_costs.keys())
        costs = [daily_costs[date] for date in dates]

        # Simple trend calculation (positive = increasing, negative = decreasing)
        if len(costs) >= 2:
            trend = (costs[-1] - costs[0]) / len(costs) if len(costs) > 1 else 0
        else:
            trend = 0

        return {
            'period_days': days,
            'total_documents': len(recent_records),
            'total_cost': sum(costs),
            'avg_daily_cost': statistics.mean(costs) if costs else 0,
            'cost_trend': trend,
            'daily_breakdown': dict(daily_usage),
            'peak_usage_day': max(daily_costs, key=daily_costs.get) if daily_costs else None,
            'lowest_cost_day': min(daily_costs, key=daily_costs.get) if daily_costs else None
        }

    def get_efficiency_metrics(self) -> Dict[str, float]:
        """Calculate efficiency metrics for the processing system."""
        if not self.processing_records:
            return {}

        # Overall metrics
        total_cost = sum(record.cost for record in self.processing_records)
        total_documents = len(self.processing_records)
        total_tokens = sum(record.tokens for record in self.processing_records)

        # Confidence metrics
        confidences = [record.confidence for record in self.processing_records]
        avg_confidence = statistics.mean(confidences) if confidences else 0

        # Processing time metrics
        times = [record.processing_time for record in self.processing_records]
        avg_processing_time = statistics.mean(times) if times else 0

        # Success rate
        successes = [record.success for record in self.processing_records]
        success_rate = sum(successes) / len(successes) if successes else 0

        # Cost efficiency
        cost_per_document = total_cost / total_documents if total_documents > 0 else 0
        cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0

        # Tier efficiency
        tier_efficiency = {}
        for tier in ProcessingTier:
            tier_records = [r for r in self.processing_records if r.tier == tier]
            if tier_records:
                tier_avg_confidence = statistics.mean([r.confidence for r in tier_records])
                tier_cost = sum([r.cost for r in tier_records])
                tier_success_rate = sum([r.success for r in tier_records]) / len(tier_records)

                # Efficiency score (confidence * success_rate / cost_per_doc)
                tier_cost_per_doc = tier_cost / len(tier_records)
                efficiency_score = (tier_avg_confidence * tier_success_rate) / tier_cost_per_doc if tier_cost_per_doc > 0 else 0
                tier_efficiency[tier.value] = efficiency_score

        return {
            'cost_per_document': cost_per_document,
            'cost_per_token': cost_per_token,
            'avg_confidence': avg_confidence,
            'avg_processing_time': avg_processing_time,
            'success_rate': success_rate,
            'total_documents_processed': total_documents,
            'total_cost': total_cost,
            'tier_efficiency_scores': tier_efficiency,
            'cost_target_performance': (self.efficiency_targets['cost_per_document'] - cost_per_document) / self.efficiency_targets['cost_per_document'] if cost_per_document > 0 else 0
        }

    def generate_cost_analysis(self) -> CostAnalysis:
        """Generate comprehensive cost analysis report."""
        cost_savings = self.calculate_cost_savings()
        optimization_recommendations = self.get_optimization_recommendations()
        usage_trends = self.get_usage_trends()
        efficiency_metrics = self.get_efficiency_metrics()

        return CostAnalysis(
            total_cost=cost_savings.get('actual_cost', 0.0),
            total_documents=len(self.processing_records),
            cost_per_document=cost_savings.get('cost_per_document', 0.0),
            tier_breakdown={tier.value: metrics for tier, metrics in self.tiers.items()},
            cost_savings=cost_savings,
            optimization_recommendations=optimization_recommendations,
            usage_trends=usage_trends,
            efficiency_metrics=efficiency_metrics
        )

    def check_budget_alerts(self) -> List[str]:
        """Check for budget alerts and warnings."""
        alerts = []

        # Daily budget check
        today = datetime.now().strftime('%Y-%m-%d')
        today_cost = sum(record.cost for record in self.processing_records
                        if record.timestamp.strftime('%Y-%m-%d') == today)

        if today_cost > self.daily_budget * 0.9:  # 90% of daily budget
            alerts.append(f"Daily budget alert: ${today_cost:.2f} of ${self.daily_budget:.2f} used today ({today_cost/self.daily_budget*100:.1f}%)")

        # Monthly budget check
        current_month = datetime.now().strftime('%Y-%m')
        month_cost = self.monthly_costs.get(current_month, 0.0)

        if month_cost > self.monthly_budget * 0.8:  # 80% of monthly budget
            alerts.append(f"Monthly budget warning: ${month_cost:.2f} of ${self.monthly_budget:.2f} used this month ({month_cost/self.monthly_budget*100:.1f}%)")

        return alerts

    def export_analytics(self, format: str = 'json') -> str:
        """Export analytics data in specified format."""
        analysis = self.generate_cost_analysis()

        if format.lower() == 'json':
            # Convert dataclasses to dictionaries for JSON serialization
            data = {
                'generated_at': datetime.now().isoformat(),
                'total_cost': analysis.total_cost,
                'total_documents': analysis.total_documents,
                'cost_per_document': analysis.cost_per_document,
                'tier_breakdown': {k: v.__dict__ for k, v in analysis.tier_breakdown.items()},
                'cost_savings': analysis.cost_savings,
                'optimization_recommendations': analysis.optimization_recommendations,
                'usage_trends': analysis.usage_trends,
                'efficiency_metrics': analysis.efficiency_metrics,
                'budget_alerts': self.check_budget_alerts()
            }
            return json.dumps(data, indent=2, default=str)

        elif format.lower() == 'csv':
            # Generate CSV format for processing records
            csv_lines = ['timestamp,tier,model,cost,tokens,confidence,processing_time,success,document_type,complexity_score']
            for record in self.processing_records:
                csv_lines.append(f"{record.timestamp},{record.tier.value},{record.model_used},{record.cost},{record.tokens},{record.confidence},{record.processing_time},{record.success},{record.document_type},{record.complexity_score}")
            return '\n'.join(csv_lines)

        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global cost optimizer instance
cost_optimizer = CostOptimizer()


# Convenience functions
def record_document_processing(
    document_id: str,
    tier: ProcessingTier,
    model_used: str,
    cost: float,
    tokens: int,
    confidence: float,
    processing_time: float,
    success: bool,
    document_type: str,
    complexity_score: float,
    user_id: Optional[str] = None
) -> None:
    """Record a document processing operation for cost tracking."""
    record = ProcessingRecord(
        document_id=document_id,
        tier=tier,
        model_used=model_used,
        cost=cost,
        tokens=tokens,
        confidence=confidence,
        processing_time=processing_time,
        success=success,
        timestamp=datetime.now(),
        document_type=document_type,
        complexity_score=complexity_score,
        user_id=user_id
    )
    cost_optimizer.record_processing(record)


def get_processing_tier_recommendation(
    document_type: str,
    complexity_score: float,
    task_type: str,
    max_cost: Optional[float] = None,
    min_confidence: Optional[float] = None
) -> Tuple[ProcessingTier, str]:
    """Get tier recommendation for document processing."""
    return cost_optimizer.get_tier_recommendation(
        document_type, complexity_score, task_type, max_cost, min_confidence
    )


def get_cost_analysis() -> CostAnalysis:
    """Get comprehensive cost analysis."""
    return cost_optimizer.generate_cost_analysis()


def get_budget_alerts() -> List[str]:
    """Get current budget alerts."""
    return cost_optimizer.check_budget_alerts()