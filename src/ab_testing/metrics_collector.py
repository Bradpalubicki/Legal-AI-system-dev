"""
Metrics Collection and Aggregation for A/B Testing

Comprehensive metrics collection system for tracking experiment performance,
user behavior, and business metrics across A/B test variants.
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import numpy as np

class MetricType(str, Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"
    PERCENTAGE = "percentage"
    CONVERSION = "conversion"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"

class MetricAggregation(str, Enum):
    """Metric aggregation methods"""
    SUM = "sum"
    AVERAGE = "average"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"
    STANDARD_DEVIATION = "standard_deviation"
    VARIANCE = "variance"

@dataclass
class MetricDefinition:
    """Definition of a metric to collect"""
    name: str
    metric_type: MetricType
    description: str
    unit: str
    aggregation_method: MetricAggregation = MetricAggregation.AVERAGE
    aggregation_window: int = 3600  # seconds
    retention_period: int = 86400 * 30  # 30 days
    filters: Optional[Dict[str, Any]] = None
    transformation: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None

@dataclass
class MetricValue:
    """Individual metric value"""
    metric_name: str
    value: Union[float, int]
    timestamp: datetime
    user_id: Optional[str] = None
    experiment_id: Optional[str] = None
    variant_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None

@dataclass
class MetricSnapshot:
    """Aggregated metric snapshot"""
    metric_name: str
    aggregation_method: MetricAggregation
    value: float
    count: int
    timestamp: datetime
    window_start: datetime
    window_end: datetime
    experiment_id: Optional[str] = None
    variant_id: Optional[str] = None
    percentiles: Optional[Dict[str, float]] = None
    additional_stats: Optional[Dict[str, float]] = None

class MetricsCollector:
    """
    Advanced metrics collection and aggregation system for A/B testing.
    
    Provides real-time metric collection, aggregation, and analysis
    capabilities for experiment tracking and performance monitoring.
    """
    
    def __init__(self, max_memory_metrics: int = 100000):
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.raw_metrics: deque = deque(maxlen=max_memory_metrics)
        self.aggregated_metrics: Dict[str, List[MetricSnapshot]] = defaultdict(list)
        self.metric_buffers: Dict[str, List[MetricValue]] = defaultdict(list)
        self.custom_aggregators: Dict[str, Callable] = {}
        self.metric_processors: Dict[str, Callable] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Background tasks
        self._aggregation_task = None
        self._cleanup_task = None
        self._is_running = False
    
    async def start(self):
        """Start background metric processing tasks."""
        if self._is_running:
            return
        
        self._is_running = True
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop background metric processing tasks."""
        self._is_running = False
        
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def define_metric(self, metric_def: MetricDefinition) -> bool:
        """Define a new metric to collect."""
        # Validate metric definition
        if not self._validate_metric_definition(metric_def):
            return False
        
        self.metric_definitions[metric_def.name] = metric_def
        return True
    
    async def record_metric(
        self,
        metric_name: str,
        value: Union[float, int],
        user_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        variant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Record a single metric value."""
        if metric_name not in self.metric_definitions:
            return False
        
        metric_def = self.metric_definitions[metric_name]
        
        # Validate metric value
        if not self._validate_metric_value(metric_def, value, context):
            return False
        
        # Apply transformation if defined
        if metric_def.transformation:
            value = self._apply_transformation(metric_def.transformation, value, context)
        
        metric_value = MetricValue(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp or datetime.utcnow(),
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            context=context,
            tags=tags
        )
        
        # Add to raw metrics and buffer
        self.raw_metrics.append(metric_value)
        self.metric_buffers[metric_name].append(metric_value)
        
        # Check for immediate processing (real-time metrics)
        if metric_def.aggregation_window <= 60:  # 1 minute or less
            await self._process_metric_buffer(metric_name)
        
        return True
    
    async def record_conversion(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        conversion_type: str = "default",
        value: float = 1.0,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record a conversion event."""
        metric_name = f"conversion_{conversion_type}"
        
        # Auto-define conversion metric if not exists
        if metric_name not in self.metric_definitions:
            await self.define_metric(MetricDefinition(
                name=metric_name,
                metric_type=MetricType.CONVERSION,
                description=f"Conversion metric for {conversion_type}",
                unit="conversions",
                aggregation_method=MetricAggregation.SUM
            ))
        
        return await self.record_metric(
            metric_name=metric_name,
            value=value,
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            context=context
        )
    
    async def record_revenue(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        amount: float,
        currency: str = "USD",
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record a revenue event."""
        metric_name = f"revenue_{currency.lower()}"
        
        # Auto-define revenue metric if not exists
        if metric_name not in self.metric_definitions:
            await self.define_metric(MetricDefinition(
                name=metric_name,
                metric_type=MetricType.REVENUE,
                description=f"Revenue in {currency}",
                unit=currency,
                aggregation_method=MetricAggregation.SUM
            ))
        
        context = context or {}
        context['currency'] = currency
        
        return await self.record_metric(
            metric_name=metric_name,
            value=amount,
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            context=context
        )
    
    async def record_engagement(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        engagement_type: str,
        duration: Optional[float] = None,
        value: float = 1.0,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record an engagement event."""
        metric_name = f"engagement_{engagement_type}"
        
        if metric_name not in self.metric_definitions:
            await self.define_metric(MetricDefinition(
                name=metric_name,
                metric_type=MetricType.ENGAGEMENT,
                description=f"Engagement metric for {engagement_type}",
                unit="events" if duration is None else "seconds",
                aggregation_method=MetricAggregation.SUM if duration is None else MetricAggregation.AVERAGE
            ))
        
        context = context or {}
        if duration is not None:
            context['duration'] = duration
            value = duration
        
        return await self.record_metric(
            metric_name=metric_name,
            value=value,
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            context=context
        )
    
    async def get_metric_snapshot(
        self,
        metric_name: str,
        experiment_id: Optional[str] = None,
        variant_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[MetricSnapshot]:
        """Get current metric snapshot."""
        if metric_name not in self.metric_definitions:
            return None
        
        # Get relevant metric values
        metric_values = self._filter_metric_values(
            metric_name, experiment_id, variant_id, start_time, end_time
        )
        
        if not metric_values:
            return None
        
        metric_def = self.metric_definitions[metric_name]
        
        # Calculate aggregated value
        values = [mv.value for mv in metric_values]
        aggregated_value = self._calculate_aggregation(
            values, metric_def.aggregation_method
        )
        
        # Calculate additional statistics
        additional_stats = self._calculate_additional_stats(values)
        percentiles = self._calculate_percentiles(values)
        
        window_start = min(mv.timestamp for mv in metric_values)
        window_end = max(mv.timestamp for mv in metric_values)
        
        return MetricSnapshot(
            metric_name=metric_name,
            aggregation_method=metric_def.aggregation_method,
            value=aggregated_value,
            count=len(metric_values),
            timestamp=datetime.utcnow(),
            window_start=window_start,
            window_end=window_end,
            experiment_id=experiment_id,
            variant_id=variant_id,
            percentiles=percentiles,
            additional_stats=additional_stats
        )
    
    async def get_experiment_metrics(
        self,
        experiment_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Dict[str, MetricSnapshot]]:
        """Get all metrics for an experiment grouped by variant."""
        results = defaultdict(dict)
        
        # Get all metric values for this experiment
        experiment_metrics = [
            mv for mv in self.raw_metrics
            if mv.experiment_id == experiment_id
            and (start_time is None or mv.timestamp >= start_time)
            and (end_time is None or mv.timestamp <= end_time)
        ]
        
        # Group by variant and metric
        variant_metrics = defaultdict(lambda: defaultdict(list))
        for mv in experiment_metrics:
            variant_metrics[mv.variant_id or 'control'][mv.metric_name].append(mv)
        
        # Calculate snapshots for each variant-metric combination
        for variant_id, metrics in variant_metrics.items():
            for metric_name, values in metrics.items():
                if metric_name in self.metric_definitions:
                    metric_def = self.metric_definitions[metric_name]
                    
                    # Calculate aggregation
                    numeric_values = [mv.value for mv in values]
                    aggregated_value = self._calculate_aggregation(
                        numeric_values, metric_def.aggregation_method
                    )
                    
                    results[variant_id][metric_name] = MetricSnapshot(
                        metric_name=metric_name,
                        aggregation_method=metric_def.aggregation_method,
                        value=aggregated_value,
                        count=len(values),
                        timestamp=datetime.utcnow(),
                        window_start=min(mv.timestamp for mv in values),
                        window_end=max(mv.timestamp for mv in values),
                        experiment_id=experiment_id,
                        variant_id=variant_id,
                        percentiles=self._calculate_percentiles(numeric_values),
                        additional_stats=self._calculate_additional_stats(numeric_values)
                    )
        
        return dict(results)
    
    async def get_conversion_rate(
        self,
        experiment_id: str,
        variant_id: Optional[str] = None,
        conversion_type: str = "default",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[float]:
        """Calculate conversion rate for a variant."""
        # Get conversion events
        conversion_metric = f"conversion_{conversion_type}"
        conversions = len(self._filter_metric_values(
            conversion_metric, experiment_id, variant_id, start_time, end_time
        ))
        
        # Get total users (unique user_ids)
        all_metrics = self._filter_metric_values(
            None, experiment_id, variant_id, start_time, end_time
        )
        unique_users = len(set(mv.user_id for mv in all_metrics if mv.user_id))
        
        if unique_users == 0:
            return None
        
        return conversions / unique_users
    
    async def register_custom_aggregator(
        self,
        metric_name: str,
        aggregator_func: Callable[[List[float]], float]
    ) -> bool:
        """Register a custom aggregation function for a metric."""
        self.custom_aggregators[metric_name] = aggregator_func
        return True
    
    async def register_metric_processor(
        self,
        metric_name: str,
        processor_func: Callable[[MetricValue], MetricValue]
    ) -> bool:
        """Register a custom processor for metric values."""
        self.metric_processors[metric_name] = processor_func
        return True
    
    async def set_alert_threshold(
        self,
        metric_name: str,
        threshold_type: str,  # 'min', 'max', 'change_rate'
        threshold_value: float
    ) -> bool:
        """Set alert threshold for a metric."""
        if metric_name not in self.alert_thresholds:
            self.alert_thresholds[metric_name] = {}
        
        self.alert_thresholds[metric_name][threshold_type] = threshold_value
        return True
    
    def _validate_metric_definition(self, metric_def: MetricDefinition) -> bool:
        """Validate metric definition."""
        if not metric_def.name or not metric_def.description:
            return False
        
        if metric_def.aggregation_window <= 0:
            return False
        
        if metric_def.retention_period <= 0:
            return False
        
        return True
    
    def _validate_metric_value(
        self,
        metric_def: MetricDefinition,
        value: Union[float, int],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Validate metric value against rules."""
        if not isinstance(value, (int, float)):
            return False
        
        if metric_def.validation_rules:
            rules = metric_def.validation_rules
            
            if 'min_value' in rules and value < rules['min_value']:
                return False
            
            if 'max_value' in rules and value > rules['max_value']:
                return False
            
            if 'allowed_values' in rules and value not in rules['allowed_values']:
                return False
        
        # Apply filters
        if metric_def.filters and context:
            for filter_key, filter_value in metric_def.filters.items():
                if filter_key in context:
                    if isinstance(filter_value, list):
                        if context[filter_key] not in filter_value:
                            return False
                    elif context[filter_key] != filter_value:
                        return False
        
        return True
    
    def _apply_transformation(
        self,
        transformation: str,
        value: Union[float, int],
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Apply transformation to metric value."""
        if transformation == "log":
            return np.log(max(value, 1e-10))
        elif transformation == "sqrt":
            return np.sqrt(max(value, 0))
        elif transformation == "square":
            return value ** 2
        elif transformation == "normalize":
            # Simple min-max normalization (would need context for proper implementation)
            return value
        else:
            return float(value)
    
    def _filter_metric_values(
        self,
        metric_name: Optional[str],
        experiment_id: Optional[str],
        variant_id: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[MetricValue]:
        """Filter metric values based on criteria."""
        filtered = []
        
        for mv in self.raw_metrics:
            # Filter by metric name
            if metric_name and mv.metric_name != metric_name:
                continue
            
            # Filter by experiment
            if experiment_id and mv.experiment_id != experiment_id:
                continue
            
            # Filter by variant
            if variant_id and mv.variant_id != variant_id:
                continue
            
            # Filter by time range
            if start_time and mv.timestamp < start_time:
                continue
            
            if end_time and mv.timestamp > end_time:
                continue
            
            filtered.append(mv)
        
        return filtered
    
    def _calculate_aggregation(
        self,
        values: List[float],
        method: MetricAggregation
    ) -> float:
        """Calculate aggregated value."""
        if not values:
            return 0.0
        
        if method == MetricAggregation.SUM:
            return sum(values)
        elif method == MetricAggregation.AVERAGE:
            return statistics.mean(values)
        elif method == MetricAggregation.MEDIAN:
            return statistics.median(values)
        elif method == MetricAggregation.MIN:
            return min(values)
        elif method == MetricAggregation.MAX:
            return max(values)
        elif method == MetricAggregation.COUNT:
            return len(values)
        elif method == MetricAggregation.STANDARD_DEVIATION:
            return statistics.stdev(values) if len(values) > 1 else 0.0
        elif method == MetricAggregation.VARIANCE:
            return statistics.variance(values) if len(values) > 1 else 0.0
        else:
            return statistics.mean(values)
    
    def _calculate_additional_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate additional statistical measures."""
        if not values:
            return {}
        
        stats = {
            'count': len(values),
            'sum': sum(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values)
        }
        
        if len(values) > 1:
            stats.update({
                'std': statistics.stdev(values),
                'variance': statistics.variance(values),
                'median': statistics.median(values)
            })
        
        return stats
    
    def _calculate_percentiles(
        self,
        values: List[float],
        percentiles: List[int] = [25, 50, 75, 90, 95, 99]
    ) -> Dict[str, float]:
        """Calculate percentile values."""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        result = {}
        
        for p in percentiles:
            if p < 0 or p > 100:
                continue
            
            index = (p / 100) * (len(sorted_values) - 1)
            if index.is_integer():
                result[f'p{p}'] = sorted_values[int(index)]
            else:
                lower = sorted_values[int(index)]
                upper = sorted_values[int(index) + 1]
                result[f'p{p}'] = lower + (upper - lower) * (index - int(index))
        
        return result
    
    async def _aggregation_loop(self):
        """Background task for metric aggregation."""
        while self._is_running:
            try:
                # Process metric buffers
                for metric_name in list(self.metric_buffers.keys()):
                    if metric_name in self.metric_definitions:
                        await self._process_metric_buffer(metric_name)
                
                # Sleep for aggregation interval
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                # Log error (in real implementation)
                print(f"Aggregation loop error: {e}")
                await asyncio.sleep(5)
    
    async def _process_metric_buffer(self, metric_name: str):
        """Process accumulated metrics for a specific metric."""
        if metric_name not in self.metric_buffers:
            return
        
        buffer = self.metric_buffers[metric_name]
        if not buffer:
            return
        
        metric_def = self.metric_definitions[metric_name]
        cutoff_time = datetime.utcnow() - timedelta(seconds=metric_def.aggregation_window)
        
        # Get metrics to process
        to_process = [mv for mv in buffer if mv.timestamp <= cutoff_time]
        
        if not to_process:
            return
        
        # Group by experiment and variant
        groups = defaultdict(list)
        for mv in to_process:
            key = (mv.experiment_id, mv.variant_id)
            groups[key].append(mv)
        
        # Process each group
        for (exp_id, var_id), metrics in groups.items():
            values = [mv.value for mv in metrics]
            
            # Apply custom aggregator if available
            if metric_name in self.custom_aggregators:
                aggregated_value = self.custom_aggregators[metric_name](values)
            else:
                aggregated_value = self._calculate_aggregation(
                    values, metric_def.aggregation_method
                )
            
            # Create snapshot
            snapshot = MetricSnapshot(
                metric_name=metric_name,
                aggregation_method=metric_def.aggregation_method,
                value=aggregated_value,
                count=len(values),
                timestamp=datetime.utcnow(),
                window_start=min(mv.timestamp for mv in metrics),
                window_end=max(mv.timestamp for mv in metrics),
                experiment_id=exp_id,
                variant_id=var_id,
                percentiles=self._calculate_percentiles(values),
                additional_stats=self._calculate_additional_stats(values)
            )
            
            self.aggregated_metrics[metric_name].append(snapshot)
        
        # Remove processed metrics from buffer
        self.metric_buffers[metric_name] = [
            mv for mv in buffer if mv.timestamp > cutoff_time
        ]
    
    async def _cleanup_loop(self):
        """Background task for cleaning up old metrics."""
        while self._is_running:
            try:
                current_time = datetime.utcnow()
                
                # Clean up raw metrics based on retention periods
                for metric_name, metric_def in self.metric_definitions.items():
                    cutoff_time = current_time - timedelta(seconds=metric_def.retention_period)
                    
                    # Clean raw metrics (limited by deque maxlen anyway)
                    # Clean aggregated metrics
                    if metric_name in self.aggregated_metrics:
                        self.aggregated_metrics[metric_name] = [
                            snapshot for snapshot in self.aggregated_metrics[metric_name]
                            if snapshot.timestamp > cutoff_time
                        ]
                
                # Sleep for cleanup interval
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                print(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error