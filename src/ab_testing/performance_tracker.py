"""
Performance Tracker

Advanced performance tracking system for monitoring model performance,
collecting metrics, and providing real-time insights for A/B testing.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import json
import warnings
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class MetricCategory(Enum):
    BUSINESS = "business"
    TECHNICAL = "technical"
    USER_EXPERIENCE = "user_experience"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    SATISFACTION = "satisfaction"
    RELIABILITY = "reliability"

class AggregationType(Enum):
    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"
    RATE = "rate"
    RATIO = "ratio"

class AlertThresholdType(Enum):
    ABSOLUTE = "absolute"
    PERCENTAGE_CHANGE = "percentage_change"
    STANDARD_DEVIATION = "standard_deviation"
    PERCENTILE = "percentile"

@dataclass
class PerformanceMetric:
    metric_id: str = ""
    name: str = ""
    description: str = ""
    category: MetricCategory = MetricCategory.TECHNICAL
    aggregation_type: AggregationType = AggregationType.MEAN
    unit: str = ""
    higher_is_better: bool = True
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    collection_frequency_seconds: int = 300  # 5 minutes default
    retention_days: int = 90
    is_primary: bool = False  # Primary metric for decision making
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PerformanceSnapshot:
    snapshot_id: str = ""
    experiment_id: str = ""
    variant_id: str = ""
    metric_values: Dict[str, float] = field(default_factory=dict)
    sample_sizes: Dict[str, int] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0  # Data quality score (0-1)
    completeness_score: float = 1.0  # Completeness score (0-1)

@dataclass
class PerformanceComparison:
    comparison_id: str = ""
    experiment_id: str = ""
    baseline_variant: str = ""
    treatment_variant: str = ""
    metric_comparisons: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    statistical_tests: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    effect_sizes: Dict[str, float] = field(default_factory=dict)
    confidence_levels: Dict[str, float] = field(default_factory=dict)
    practical_significance: Dict[str, bool] = field(default_factory=dict)
    recommendation: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ModelHealthCheck:
    model_id: str = ""
    variant_id: str = ""
    health_score: float = 0.0  # Overall health score (0-100)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    reliability_metrics: Dict[str, float] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    last_check: datetime = field(default_factory=datetime.utcnow)
    trend_analysis: Dict[str, str] = field(default_factory=dict)  # improving, stable, declining
    risk_level: str = "low"  # low, medium, high, critical

class PerformanceTracker:
    def __init__(self):
        self.metrics_registry: Dict[str, PerformanceMetric] = {}
        self.performance_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.snapshots: List[PerformanceSnapshot] = []
        self.health_checks: Dict[str, ModelHealthCheck] = {}
        
        # Configuration
        self.config = {
            'collection_batch_size': 1000,
            'alert_cooldown_minutes': 30,
            'health_check_interval_minutes': 15,
            'data_retention_days': 90,
            'outlier_detection_enabled': True,
            'outlier_threshold_std': 3.0,
            'min_sample_size_for_analysis': 30,
            'statistical_significance_threshold': 0.05,
            'practical_significance_threshold': 0.02,
            'auto_baseline_update': True,
            'seasonal_adjustment_enabled': False
        }
        
        # Statistical configurations
        self.statistical_config = {
            'bootstrap_samples': 10000,
            'confidence_level': 0.95,
            'bonferroni_correction': True,
            'welch_ttest': True,  # Assume unequal variances
            'mann_whitney_fallback': True,  # For non-normal distributions
            'effect_size_methods': ['cohen_d', 'glass_delta', 'hedges_g']
        }
        
        # Initialize default metrics
        asyncio.create_task(self._initialize_default_metrics())

    async def register_metric(
        self,
        metric_id: str,
        name: str,
        description: str,
        category: MetricCategory,
        aggregation_type: AggregationType = AggregationType.MEAN,
        unit: str = "",
        higher_is_better: bool = True,
        is_primary: bool = False,
        baseline_value: Optional[float] = None,
        target_value: Optional[float] = None,
        alert_thresholds: Optional[Dict[str, float]] = None
    ) -> bool:
        """Register a new performance metric."""
        try:
            metric = PerformanceMetric(
                metric_id=metric_id,
                name=name,
                description=description,
                category=category,
                aggregation_type=aggregation_type,
                unit=unit,
                higher_is_better=higher_is_better,
                is_primary=is_primary,
                baseline_value=baseline_value,
                target_value=target_value,
                alert_thresholds=alert_thresholds or {}
            )
            
            self.metrics_registry[metric_id] = metric
            logger.info(f"Registered metric: {metric_id} - {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering metric {metric_id}: {e}")
            return False

    async def record_metric(
        self,
        experiment_id: str,
        variant_id: str,
        metric_id: str,
        value: float,
        timestamp: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """Record a single metric value."""
        try:
            if metric_id not in self.metrics_registry:
                logger.warning(f"Metric {metric_id} not registered")
                return False
            
            # Validate value
            if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                logger.warning(f"Invalid metric value: {value}")
                return False
            
            # Create metric record
            record = {
                'experiment_id': experiment_id,
                'variant_id': variant_id,
                'metric_id': metric_id,
                'value': float(value),
                'timestamp': timestamp or datetime.utcnow(),
                'context': context or {},
                'user_id': user_id
            }
            
            # Store in performance data
            key = f"{experiment_id}_{variant_id}_{metric_id}"
            self.performance_data[key].append(record)
            
            # Check for outliers if enabled
            if self.config['outlier_detection_enabled']:
                await self._check_for_outliers(key, record)
            
            # Check alert thresholds
            await self._check_alert_thresholds(metric_id, value, experiment_id, variant_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
            return False

    async def record_metrics_batch(
        self,
        experiment_id: str,
        variant_id: str,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, bool]:
        """Record a batch of metrics."""
        try:
            results = {}
            
            for metric_id, value in metrics.items():
                success = await self.record_metric(
                    experiment_id, variant_id, metric_id, value, timestamp, context, user_id
                )
                results[metric_id] = success
            
            return results
            
        except Exception as e:
            logger.error(f"Error recording metrics batch: {e}")
            return {metric_id: False for metric_id in metrics.keys()}

    async def get_performance_snapshot(
        self,
        experiment_id: str,
        variant_id: str,
        metric_ids: Optional[List[str]] = None,
        time_window_minutes: Optional[int] = None
    ) -> Optional[PerformanceSnapshot]:
        """Get a performance snapshot for a variant."""
        try:
            if metric_ids is None:
                metric_ids = list(self.metrics_registry.keys())
            
            # Define time window
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes or 60)
            
            # Collect metrics
            metric_values = {}
            sample_sizes = {}
            confidence_intervals = {}
            
            for metric_id in metric_ids:
                key = f"{experiment_id}_{variant_id}_{metric_id}"
                
                if key not in self.performance_data:
                    continue
                
                # Filter by time window
                relevant_records = [
                    record for record in self.performance_data[key]
                    if start_time <= record['timestamp'] <= end_time
                ]
                
                if not relevant_records:
                    continue
                
                values = [record['value'] for record in relevant_records]
                
                if not values:
                    continue
                
                # Calculate aggregated value
                metric_config = self.metrics_registry[metric_id]
                
                if metric_config.aggregation_type == AggregationType.MEAN:
                    metric_values[metric_id] = np.mean(values)
                elif metric_config.aggregation_type == AggregationType.MEDIAN:
                    metric_values[metric_id] = np.median(values)
                elif metric_config.aggregation_type == AggregationType.SUM:
                    metric_values[metric_id] = np.sum(values)
                elif metric_config.aggregation_type == AggregationType.COUNT:
                    metric_values[metric_id] = len(values)
                elif metric_config.aggregation_type == AggregationType.MIN:
                    metric_values[metric_id] = np.min(values)
                elif metric_config.aggregation_type == AggregationType.MAX:
                    metric_values[metric_id] = np.max(values)
                elif metric_config.aggregation_type == AggregationType.PERCENTILE_95:
                    metric_values[metric_id] = np.percentile(values, 95)
                elif metric_config.aggregation_type == AggregationType.PERCENTILE_99:
                    metric_values[metric_id] = np.percentile(values, 99)
                else:
                    metric_values[metric_id] = np.mean(values)  # Default to mean
                
                sample_sizes[metric_id] = len(values)
                
                # Calculate confidence interval
                if len(values) >= self.config['min_sample_size_for_analysis']:
                    ci = self._calculate_confidence_interval(values, self.statistical_config['confidence_level'])
                    confidence_intervals[metric_id] = ci
            
            if not metric_values:
                return None
            
            # Create snapshot
            snapshot = PerformanceSnapshot(
                snapshot_id=f"snap_{experiment_id}_{variant_id}_{int(end_time.timestamp())}",
                experiment_id=experiment_id,
                variant_id=variant_id,
                metric_values=metric_values,
                sample_sizes=sample_sizes,
                confidence_intervals=confidence_intervals,
                timestamp=end_time
            )
            
            # Calculate quality scores
            snapshot.quality_score = await self._calculate_data_quality_score(experiment_id, variant_id, start_time, end_time)
            snapshot.completeness_score = len(metric_values) / len(metric_ids) if metric_ids else 1.0
            
            self.snapshots.append(snapshot)
            return snapshot
            
        except Exception as e:
            logger.error(f"Error getting performance snapshot: {e}")
            return None

    async def compare_variants(
        self,
        experiment_id: str,
        baseline_variant: str,
        treatment_variant: str,
        metric_ids: Optional[List[str]] = None,
        time_window_minutes: Optional[int] = None
    ) -> Optional[PerformanceComparison]:
        """Compare performance between two variants."""
        try:
            if metric_ids is None:
                # Use primary metrics for comparison
                metric_ids = [mid for mid, metric in self.metrics_registry.items() if metric.is_primary]
                if not metric_ids:
                    metric_ids = list(self.metrics_registry.keys())
            
            # Get data for both variants
            baseline_data = await self._get_variant_data(experiment_id, baseline_variant, metric_ids, time_window_minutes)
            treatment_data = await self._get_variant_data(experiment_id, treatment_variant, metric_ids, time_window_minutes)
            
            if not baseline_data or not treatment_data:
                return None
            
            comparison_id = f"comp_{experiment_id}_{baseline_variant}_vs_{treatment_variant}_{int(datetime.utcnow().timestamp())}"
            
            # Perform statistical comparisons
            metric_comparisons = {}
            statistical_tests = {}
            effect_sizes = {}
            confidence_levels = {}
            practical_significance = {}
            
            for metric_id in metric_ids:
                if metric_id not in baseline_data or metric_id not in treatment_data:
                    continue
                
                baseline_values = baseline_data[metric_id]
                treatment_values = treatment_data[metric_id]
                
                if len(baseline_values) < 10 or len(treatment_values) < 10:
                    continue
                
                # Basic statistics
                metric_comparisons[metric_id] = {
                    'baseline': {
                        'mean': np.mean(baseline_values),
                        'std': np.std(baseline_values),
                        'median': np.median(baseline_values),
                        'count': len(baseline_values)
                    },
                    'treatment': {
                        'mean': np.mean(treatment_values),
                        'std': np.std(treatment_values),
                        'median': np.median(treatment_values),
                        'count': len(treatment_values)
                    },
                    'difference': {
                        'absolute': np.mean(treatment_values) - np.mean(baseline_values),
                        'relative': ((np.mean(treatment_values) - np.mean(baseline_values)) / np.mean(baseline_values)) * 100 if np.mean(baseline_values) != 0 else 0
                    }
                }
                
                # Statistical tests
                test_results = await self._perform_statistical_tests(baseline_values, treatment_values)
                statistical_tests[metric_id] = test_results
                
                # Effect size
                effect_size = self._calculate_effect_size(baseline_values, treatment_values)
                effect_sizes[metric_id] = effect_size
                
                # Confidence level
                confidence_levels[metric_id] = 1 - test_results.get('p_value', 1.0)
                
                # Practical significance
                metric_config = self.metrics_registry.get(metric_id)
                if metric_config:
                    relative_change = abs(metric_comparisons[metric_id]['difference']['relative'])
                    practical_significance[metric_id] = relative_change >= self.config['practical_significance_threshold'] * 100
            
            # Generate recommendation
            recommendation = await self._generate_comparison_recommendation(
                metric_comparisons, statistical_tests, effect_sizes, practical_significance
            )
            
            comparison = PerformanceComparison(
                comparison_id=comparison_id,
                experiment_id=experiment_id,
                baseline_variant=baseline_variant,
                treatment_variant=treatment_variant,
                metric_comparisons=metric_comparisons,
                statistical_tests=statistical_tests,
                effect_sizes=effect_sizes,
                confidence_levels=confidence_levels,
                practical_significance=practical_significance,
                recommendation=recommendation
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing variants: {e}")
            return None

    async def perform_health_check(
        self,
        model_id: str,
        variant_id: str,
        experiment_id: Optional[str] = None
    ) -> ModelHealthCheck:
        """Perform comprehensive health check on a model variant."""
        try:
            # Collect performance metrics
            performance_metrics = {}
            quality_metrics = {}
            reliability_metrics = {}
            alerts = []
            recommendations = []
            
            # Get recent performance data
            recent_window_minutes = 60
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=recent_window_minutes)
            
            # Analyze each registered metric
            for metric_id, metric_config in self.metrics_registry.items():
                key = f"{experiment_id or 'default'}_{variant_id}_{metric_id}"
                
                if key not in self.performance_data:
                    continue
                
                recent_records = [
                    record for record in self.performance_data[key]
                    if start_time <= record['timestamp'] <= end_time
                ]
                
                if not recent_records:
                    continue
                
                values = [record['value'] for record in recent_records]
                current_value = np.mean(values) if values else 0
                
                # Categorize metrics
                if metric_config.category in [MetricCategory.PERFORMANCE, MetricCategory.TECHNICAL]:
                    performance_metrics[metric_id] = current_value
                elif metric_config.category in [MetricCategory.QUALITY]:
                    quality_metrics[metric_id] = current_value
                elif metric_config.category in [MetricCategory.RELIABILITY]:
                    reliability_metrics[metric_id] = current_value
                
                # Check against thresholds and baselines
                if metric_config.baseline_value:
                    deviation = abs(current_value - metric_config.baseline_value) / metric_config.baseline_value
                    if deviation > 0.2:  # 20% deviation threshold
                        alerts.append(f"{metric_config.name} deviates {deviation:.1%} from baseline")
                
                # Check alert thresholds
                for threshold_name, threshold_value in metric_config.alert_thresholds.items():
                    if metric_config.higher_is_better:
                        if current_value < threshold_value:
                            alerts.append(f"{metric_config.name} below {threshold_name} threshold: {current_value:.3f} < {threshold_value}")
                    else:
                        if current_value > threshold_value:
                            alerts.append(f"{metric_config.name} above {threshold_name} threshold: {current_value:.3f} > {threshold_value}")
            
            # Calculate overall health score
            health_score = await self._calculate_health_score(
                performance_metrics, quality_metrics, reliability_metrics, alerts
            )
            
            # Determine risk level
            risk_level = "low"
            if health_score < 50:
                risk_level = "critical"
            elif health_score < 70:
                risk_level = "high"
            elif health_score < 85:
                risk_level = "medium"
            
            # Generate recommendations
            if health_score < 85:
                recommendations.extend(await self._generate_health_recommendations(
                    performance_metrics, quality_metrics, reliability_metrics, alerts
                ))
            
            # Analyze trends
            trend_analysis = await self._analyze_performance_trends(model_id, variant_id, experiment_id)
            
            health_check = ModelHealthCheck(
                model_id=model_id,
                variant_id=variant_id,
                health_score=health_score,
                performance_metrics=performance_metrics,
                quality_metrics=quality_metrics,
                reliability_metrics=reliability_metrics,
                alerts=alerts,
                recommendations=recommendations,
                trend_analysis=trend_analysis,
                risk_level=risk_level
            )
            
            self.health_checks[f"{model_id}_{variant_id}"] = health_check
            return health_check
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return ModelHealthCheck(model_id=model_id, variant_id=variant_id, health_score=0)

    async def generate_performance_report(
        self,
        experiment_id: str,
        report_type: str = "comprehensive",
        time_window_hours: int = 24,
        include_visualizations: bool = False
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            report = {
                'experiment_id': experiment_id,
                'report_type': report_type,
                'time_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'hours': time_window_hours
                },
                'summary': {},
                'variant_performance': {},
                'metric_analysis': {},
                'alerts_and_anomalies': [],
                'recommendations': [],
                'data_quality': {},
                'visualizations': {} if include_visualizations else None,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Get all variants in the experiment
            variants = set()
            for key in self.performance_data.keys():
                if key.startswith(experiment_id):
                    parts = key.split('_')
                    if len(parts) >= 3:
                        variant_id = parts[1]
                        variants.add(variant_id)
            
            if not variants:
                report['summary']['message'] = 'No performance data found for experiment'
                return report
            
            # Analyze each variant
            variant_snapshots = {}
            for variant_id in variants:
                snapshot = await self.get_performance_snapshot(
                    experiment_id, variant_id, time_window_minutes=time_window_hours * 60
                )
                if snapshot:
                    variant_snapshots[variant_id] = snapshot
                    
                    report['variant_performance'][variant_id] = {
                        'metrics': snapshot.metric_values,
                        'sample_sizes': snapshot.sample_sizes,
                        'confidence_intervals': snapshot.confidence_intervals,
                        'quality_score': snapshot.quality_score,
                        'completeness_score': snapshot.completeness_score
                    }
            
            # Perform variant comparisons
            variant_list = list(variants)
            if len(variant_list) >= 2:
                # Compare each variant to the first one (assumed baseline)
                baseline_variant = variant_list[0]
                
                for treatment_variant in variant_list[1:]:
                    comparison = await self.compare_variants(
                        experiment_id, baseline_variant, treatment_variant, 
                        time_window_minutes=time_window_hours * 60
                    )
                    
                    if comparison:
                        comparison_key = f"{baseline_variant}_vs_{treatment_variant}"
                        report['variant_performance'][comparison_key] = {
                            'metric_comparisons': comparison.metric_comparisons,
                            'statistical_significance': comparison.statistical_tests,
                            'effect_sizes': comparison.effect_sizes,
                            'practical_significance': comparison.practical_significance,
                            'recommendation': comparison.recommendation
                        }
            
            # Analyze metrics across all variants
            for metric_id in self.metrics_registry.keys():
                metric_data = {}
                
                for variant_id in variants:
                    if variant_id in variant_snapshots:
                        snapshot = variant_snapshots[variant_id]
                        if metric_id in snapshot.metric_values:
                            metric_data[variant_id] = {
                                'value': snapshot.metric_values[metric_id],
                                'sample_size': snapshot.sample_sizes.get(metric_id, 0),
                                'confidence_interval': snapshot.confidence_intervals.get(metric_id)
                            }
                
                if metric_data:
                    report['metric_analysis'][metric_id] = {
                        'variant_data': metric_data,
                        'best_variant': max(metric_data.items(), key=lambda x: x[1]['value'])[0] if metric_data else None,
                        'metric_config': {
                            'name': self.metrics_registry[metric_id].name,
                            'category': self.metrics_registry[metric_id].category.value,
                            'higher_is_better': self.metrics_registry[metric_id].higher_is_better,
                            'unit': self.metrics_registry[metric_id].unit
                        }
                    }
            
            # Collect alerts and anomalies
            report['alerts_and_anomalies'] = await self._get_recent_alerts(experiment_id, time_window_hours)
            
            # Generate overall recommendations
            report['recommendations'] = await self._generate_report_recommendations(report)
            
            # Calculate summary metrics
            report['summary'] = {
                'total_variants': len(variants),
                'metrics_tracked': len(report['metric_analysis']),
                'alerts_count': len(report['alerts_and_anomalies']),
                'data_completeness': np.mean([
                    snapshot.completeness_score for snapshot in variant_snapshots.values()
                ]) if variant_snapshots else 0,
                'overall_data_quality': np.mean([
                    snapshot.quality_score for snapshot in variant_snapshots.values()
                ]) if variant_snapshots else 0
            }
            
            # Generate visualizations if requested
            if include_visualizations:
                report['visualizations'] = await self._generate_performance_visualizations(
                    experiment_id, variant_snapshots, time_window_hours
                )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}

    # Private helper methods
    
    async def _initialize_default_metrics(self) -> None:
        """Initialize default performance metrics."""
        try:
            default_metrics = [
                {
                    'metric_id': 'response_time',
                    'name': 'Response Time',
                    'description': 'Average response time in milliseconds',
                    'category': MetricCategory.PERFORMANCE,
                    'unit': 'ms',
                    'higher_is_better': False,
                    'alert_thresholds': {'warning': 1000, 'critical': 5000}
                },
                {
                    'metric_id': 'accuracy',
                    'name': 'Model Accuracy',
                    'description': 'Model prediction accuracy',
                    'category': MetricCategory.QUALITY,
                    'unit': '%',
                    'higher_is_better': True,
                    'is_primary': True,
                    'alert_thresholds': {'warning': 0.8, 'critical': 0.7}
                },
                {
                    'metric_id': 'throughput',
                    'name': 'Throughput',
                    'description': 'Requests processed per second',
                    'category': MetricCategory.PERFORMANCE,
                    'aggregation_type': AggregationType.RATE,
                    'unit': 'req/s',
                    'higher_is_better': True
                },
                {
                    'metric_id': 'error_rate',
                    'name': 'Error Rate',
                    'description': 'Percentage of requests resulting in errors',
                    'category': MetricCategory.RELIABILITY,
                    'unit': '%',
                    'higher_is_better': False,
                    'alert_thresholds': {'warning': 0.01, 'critical': 0.05}
                },
                {
                    'metric_id': 'user_satisfaction',
                    'name': 'User Satisfaction',
                    'description': 'User satisfaction score',
                    'category': MetricCategory.USER_EXPERIENCE,
                    'unit': 'score',
                    'higher_is_better': True,
                    'is_primary': True,
                    'alert_thresholds': {'warning': 4.0, 'critical': 3.0}
                },
                {
                    'metric_id': 'conversion_rate',
                    'name': 'Conversion Rate',
                    'description': 'Percentage of users completing target action',
                    'category': MetricCategory.CONVERSION,
                    'unit': '%',
                    'higher_is_better': True,
                    'is_primary': True
                }
            ]
            
            for metric_config in default_metrics:
                await self.register_metric(**metric_config)
                
        except Exception as e:
            logger.error(f"Error initializing default metrics: {e}")

    def _calculate_confidence_interval(self, values: List[float], confidence_level: float) -> Tuple[float, float]:
        """Calculate confidence interval for a set of values."""
        try:
            if len(values) < 2:
                mean_val = np.mean(values) if values else 0
                return (mean_val, mean_val)
            
            mean = np.mean(values)
            sem = stats.sem(values)  # Standard error of mean
            
            # Calculate t-critical value
            df = len(values) - 1
            alpha = 1 - confidence_level
            t_crit = stats.t.ppf(1 - alpha/2, df)
            
            margin_error = t_crit * sem
            
            return (mean - margin_error, mean + margin_error)
            
        except Exception as e:
            logger.error(f"Error calculating confidence interval: {e}")
            mean_val = np.mean(values) if values else 0
            return (mean_val, mean_val)

    async def _get_variant_data(
        self, 
        experiment_id: str, 
        variant_id: str, 
        metric_ids: List[str], 
        time_window_minutes: Optional[int]
    ) -> Dict[str, List[float]]:
        """Get raw data for a variant."""
        try:
            if time_window_minutes:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=time_window_minutes)
            else:
                start_time = datetime.min
                end_time = datetime.utcnow()
            
            variant_data = {}
            
            for metric_id in metric_ids:
                key = f"{experiment_id}_{variant_id}_{metric_id}"
                
                if key not in self.performance_data:
                    continue
                
                # Filter by time window
                relevant_records = [
                    record for record in self.performance_data[key]
                    if start_time <= record['timestamp'] <= end_time
                ]
                
                if relevant_records:
                    values = [record['value'] for record in relevant_records]
                    variant_data[metric_id] = values
            
            return variant_data
            
        except Exception as e:
            logger.error(f"Error getting variant data: {e}")
            return {}

    async def _perform_statistical_tests(
        self, 
        baseline_values: List[float], 
        treatment_values: List[float]
    ) -> Dict[str, Any]:
        """Perform statistical tests between two groups."""
        try:
            results = {}
            
            # Basic descriptive statistics
            results['baseline_mean'] = np.mean(baseline_values)
            results['treatment_mean'] = np.mean(treatment_values)
            results['difference'] = results['treatment_mean'] - results['baseline_mean']
            
            # Check normality (Shapiro-Wilk test)
            if len(baseline_values) >= 3 and len(treatment_values) >= 3:
                try:
                    _, p_baseline_normal = stats.shapiro(baseline_values[:5000])  # Limit for computational efficiency
                    _, p_treatment_normal = stats.shapiro(treatment_values[:5000])
                    
                    both_normal = p_baseline_normal > 0.05 and p_treatment_normal > 0.05
                    results['normality_assumption'] = both_normal
                except:
                    both_normal = True  # Assume normal if test fails
                    results['normality_assumption'] = True
            else:
                both_normal = True
                results['normality_assumption'] = True
            
            # Perform appropriate test
            if both_normal and self.statistical_config['welch_ttest']:
                # Welch's t-test (assumes unequal variances)
                try:
                    statistic, p_value = stats.ttest_ind(treatment_values, baseline_values, equal_var=False)
                    results['test_type'] = 'welch_ttest'
                    results['statistic'] = statistic
                    results['p_value'] = p_value
                    results['significant'] = p_value < self.config['statistical_significance_threshold']
                except Exception as e:
                    logger.error(f"Welch's t-test failed: {e}")
                    # Fallback to Mann-Whitney U test
                    both_normal = False
            
            if not both_normal and self.statistical_config['mann_whitney_fallback']:
                # Mann-Whitney U test (non-parametric)
                try:
                    statistic, p_value = stats.mannwhitneyu(
                        treatment_values, baseline_values, alternative='two-sided'
                    )
                    results['test_type'] = 'mann_whitney'
                    results['statistic'] = statistic
                    results['p_value'] = p_value
                    results['significant'] = p_value < self.config['statistical_significance_threshold']
                except Exception as e:
                    logger.error(f"Mann-Whitney U test failed: {e}")
                    results['test_type'] = 'failed'
                    results['p_value'] = 1.0
                    results['significant'] = False
            
            # Calculate confidence interval for the difference
            if 'p_value' in results:
                try:
                    # Bootstrap confidence interval for difference in means
                    n_bootstrap = min(1000, self.statistical_config['bootstrap_samples'])
                    bootstrap_diffs = []
                    
                    for _ in range(n_bootstrap):
                        baseline_sample = np.random.choice(baseline_values, size=len(baseline_values), replace=True)
                        treatment_sample = np.random.choice(treatment_values, size=len(treatment_values), replace=True)
                        bootstrap_diffs.append(np.mean(treatment_sample) - np.mean(baseline_sample))
                    
                    alpha = 1 - self.statistical_config['confidence_level']
                    lower = np.percentile(bootstrap_diffs, (alpha/2) * 100)
                    upper = np.percentile(bootstrap_diffs, (1 - alpha/2) * 100)
                    
                    results['confidence_interval'] = (lower, upper)
                except Exception as e:
                    logger.error(f"Bootstrap confidence interval failed: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing statistical tests: {e}")
            return {'test_type': 'error', 'p_value': 1.0, 'significant': False}

    def _calculate_effect_size(self, baseline_values: List[float], treatment_values: List[float]) -> float:
        """Calculate Cohen's d effect size."""
        try:
            baseline_mean = np.mean(baseline_values)
            treatment_mean = np.mean(treatment_values)
            
            # Pooled standard deviation
            baseline_var = np.var(baseline_values, ddof=1)
            treatment_var = np.var(treatment_values, ddof=1)
            
            n_baseline = len(baseline_values)
            n_treatment = len(treatment_values)
            
            pooled_std = np.sqrt(((n_baseline - 1) * baseline_var + (n_treatment - 1) * treatment_var) / 
                               (n_baseline + n_treatment - 2))
            
            if pooled_std == 0:
                return 0.0
            
            cohens_d = (treatment_mean - baseline_mean) / pooled_std
            return cohens_d
            
        except Exception as e:
            logger.error(f"Error calculating effect size: {e}")
            return 0.0

    async def _calculate_data_quality_score(
        self, 
        experiment_id: str, 
        variant_id: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> float:
        """Calculate data quality score based on various factors."""
        try:
            quality_factors = []
            
            # Check data completeness
            expected_metrics = len(self.metrics_registry)
            actual_metrics = 0
            
            for metric_id in self.metrics_registry.keys():
                key = f"{experiment_id}_{variant_id}_{metric_id}"
                if key in self.performance_data:
                    recent_records = [
                        record for record in self.performance_data[key]
                        if start_time <= record['timestamp'] <= end_time
                    ]
                    if recent_records:
                        actual_metrics += 1
            
            completeness = actual_metrics / expected_metrics if expected_metrics > 0 else 1.0
            quality_factors.append(completeness)
            
            # Check data freshness (recency of last data point)
            latest_timestamp = datetime.min
            for metric_id in self.metrics_registry.keys():
                key = f"{experiment_id}_{variant_id}_{metric_id}"
                if key in self.performance_data and self.performance_data[key]:
                    last_record = max(self.performance_data[key], key=lambda r: r['timestamp'])
                    if last_record['timestamp'] > latest_timestamp:
                        latest_timestamp = last_record['timestamp']
            
            if latest_timestamp > datetime.min:
                freshness_hours = (end_time - latest_timestamp).total_seconds() / 3600
                freshness_score = max(0, 1 - freshness_hours / 24)  # Decay over 24 hours
                quality_factors.append(freshness_score)
            
            # Check for outliers ratio
            outlier_ratios = []
            for metric_id in self.metrics_registry.keys():
                key = f"{experiment_id}_{variant_id}_{metric_id}"
                if key in self.performance_data:
                    recent_records = [
                        record for record in self.performance_data[key]
                        if start_time <= record['timestamp'] <= end_time
                    ]
                    
                    if len(recent_records) >= 10:
                        values = [record['value'] for record in recent_records]
                        q1, q3 = np.percentile(values, [25, 75])
                        iqr = q3 - q1
                        
                        if iqr > 0:
                            lower_bound = q1 - 1.5 * iqr
                            upper_bound = q3 + 1.5 * iqr
                            
                            outliers = [v for v in values if v < lower_bound or v > upper_bound]
                            outlier_ratio = len(outliers) / len(values)
                            outlier_ratios.append(1 - outlier_ratio)  # Higher score for fewer outliers
            
            if outlier_ratios:
                quality_factors.append(np.mean(outlier_ratios))
            
            # Return average of all quality factors
            return np.mean(quality_factors) if quality_factors else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating data quality score: {e}")
            return 0.5

    async def _calculate_health_score(
        self,
        performance_metrics: Dict[str, float],
        quality_metrics: Dict[str, float],
        reliability_metrics: Dict[str, float],
        alerts: List[str]
    ) -> float:
        """Calculate overall model health score."""
        try:
            score_components = []
            
            # Performance score
            if performance_metrics:
                perf_scores = []
                for metric_id, value in performance_metrics.items():
                    metric_config = self.metrics_registry.get(metric_id)
                    if metric_config and metric_config.baseline_value:
                        if metric_config.higher_is_better:
                            ratio = value / metric_config.baseline_value
                        else:
                            ratio = metric_config.baseline_value / value if value > 0 else 0
                        
                        # Cap ratio and convert to 0-100 scale
                        normalized_score = min(100, max(0, ratio * 100))
                        perf_scores.append(normalized_score)
                
                if perf_scores:
                    score_components.append(np.mean(perf_scores))
            
            # Quality score
            if quality_metrics:
                quality_scores = [min(100, max(0, value * 100)) for value in quality_metrics.values()]
                score_components.append(np.mean(quality_scores))
            
            # Reliability score
            if reliability_metrics:
                reliability_scores = []
                for metric_id, value in reliability_metrics.items():
                    metric_config = self.metrics_registry.get(metric_id)
                    if metric_config:
                        if metric_config.higher_is_better:
                            score = min(100, max(0, value * 100))
                        else:
                            score = min(100, max(0, (1 - value) * 100))
                        reliability_scores.append(score)
                
                if reliability_scores:
                    score_components.append(np.mean(reliability_scores))
            
            # Alert penalty
            alert_penalty = min(50, len(alerts) * 10)  # Up to 50 point penalty
            
            # Calculate final score
            base_score = np.mean(score_components) if score_components else 50
            final_score = max(0, base_score - alert_penalty)
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0

    # Additional helper methods would continue here for:
    # - _check_for_outliers
    # - _check_alert_thresholds  
    # - _analyze_performance_trends
    # - _generate_health_recommendations
    # - _get_recent_alerts
    # - _generate_report_recommendations
    # - _generate_performance_visualizations
    # - _generate_comparison_recommendation

    async def _check_for_outliers(self, data_key: str, record: Dict[str, Any]) -> None:
        """Check if a metric value is an outlier."""
        try:
            if len(self.performance_data[data_key]) < 10:
                return  # Need more data for outlier detection
            
            recent_values = [r['value'] for r in list(self.performance_data[data_key])[-100:]]
            current_value = record['value']
            
            mean_val = np.mean(recent_values)
            std_val = np.std(recent_values)
            
            if std_val > 0:
                z_score = abs((current_value - mean_val) / std_val)
                if z_score > self.config['outlier_threshold_std']:
                    logger.warning(f"Outlier detected in {data_key}: value={current_value}, z_score={z_score:.2f}")
        except Exception as e:
            logger.error(f"Error checking for outliers: {e}")

    async def _check_alert_thresholds(
        self, 
        metric_id: str, 
        value: float, 
        experiment_id: str, 
        variant_id: str
    ) -> None:
        """Check if metric value crosses alert thresholds."""
        try:
            metric_config = self.metrics_registry.get(metric_id)
            if not metric_config or not metric_config.alert_thresholds:
                return
            
            for threshold_name, threshold_value in metric_config.alert_thresholds.items():
                alert_triggered = False
                
                if metric_config.higher_is_better:
                    if value < threshold_value:
                        alert_triggered = True
                else:
                    if value > threshold_value:
                        alert_triggered = True
                
                if alert_triggered:
                    logger.warning(f"Alert triggered for {metric_id} in {experiment_id}/{variant_id}: "
                                 f"{threshold_name} threshold crossed (value={value}, threshold={threshold_value})")
        except Exception as e:
            logger.error(f"Error checking alert thresholds: {e}")

    async def _generate_comparison_recommendation(
        self,
        metric_comparisons: Dict[str, Dict[str, Any]],
        statistical_tests: Dict[str, Dict[str, Any]],
        effect_sizes: Dict[str, float],
        practical_significance: Dict[str, bool]
    ) -> str:
        """Generate recommendation based on variant comparison."""
        try:
            significant_improvements = 0
            significant_regressions = 0
            practical_improvements = 0
            
            for metric_id in metric_comparisons.keys():
                if metric_id in statistical_tests and statistical_tests[metric_id].get('significant', False):
                    effect_size = effect_sizes.get(metric_id, 0)
                    is_practical = practical_significance.get(metric_id, False)
                    
                    if effect_size > 0:
                        significant_improvements += 1
                        if is_practical:
                            practical_improvements += 1
                    else:
                        significant_regressions += 1
            
            if significant_improvements > significant_regressions and practical_improvements > 0:
                return "Treatment variant shows statistically significant and practically meaningful improvements. Recommend deployment."
            elif significant_improvements > 0 and significant_regressions == 0:
                return "Treatment variant shows positive results but may need longer testing for practical significance."
            elif significant_regressions > significant_improvements:
                return "Treatment variant shows concerning regressions. Recommend staying with baseline."
            else:
                return "Results are inconclusive. Consider extending test duration or increasing sample size."
                
        except Exception as e:
            logger.error(f"Error generating comparison recommendation: {e}")
            return "Unable to generate recommendation due to analysis error."