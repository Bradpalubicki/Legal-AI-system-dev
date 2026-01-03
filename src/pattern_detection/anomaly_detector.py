"""
Anomaly Detector

Advanced anomaly detection system that identifies unusual patterns and outliers
in legal case activities, attorney behaviors, and system operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import logging
import numpy as np
from scipy import stats
from collections import defaultdict, deque
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ..core.database import get_db_session


logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    STATISTICAL_OUTLIER = "statistical_outlier"
    TIME_SERIES_ANOMALY = "time_series_anomaly"
    BEHAVIORAL_DEVIATION = "behavioral_deviation"
    VOLUME_ANOMALY = "volume_anomaly"
    PATTERN_BREAK = "pattern_break"
    CORRELATION_ANOMALY = "correlation_anomaly"
    SEASONAL_DEVIATION = "seasonal_deviation"
    THRESHOLD_VIOLATION = "threshold_violation"


class AnomalySeverity(str, Enum):
    """Severity levels for anomalies."""
    CRITICAL = "critical"    # Immediate attention required
    HIGH = "high"           # Should be investigated promptly
    MEDIUM = "medium"       # Monitor closely
    LOW = "low"             # Informational
    NOISE = "noise"         # Likely false positive


@dataclass
class Anomaly:
    """Detected anomaly with metadata."""
    id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    
    # Affected entities
    affected_cases: List[int] = field(default_factory=list)
    affected_attorneys: List[int] = field(default_factory=list)
    affected_entities: Dict[str, List[int]] = field(default_factory=dict)
    
    # Statistical information
    observed_value: float = 0.0
    expected_value: float = 0.0
    deviation_score: float = 0.0  # Number of standard deviations
    confidence_level: float = 0.0  # 0.0 to 1.0
    p_value: Optional[float] = None
    
    # Temporal information
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)
    anomaly_start_time: Optional[datetime] = None
    anomaly_end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    
    # Context and analysis
    context: Dict[str, Any] = field(default_factory=dict)
    potential_causes: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    
    # Metadata
    detection_method: str = ""
    is_confirmed: bool = False
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None


class AnomalyThreshold(BaseModel):
    """Threshold configuration for anomaly detection."""
    threshold_id: str
    name: str
    entity_type: str  # case, attorney, system, etc.
    metric_name: str
    threshold_type: str  # absolute, relative, statistical
    
    # Threshold values
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    deviation_threshold: float = 2.0  # Standard deviations
    percentile_threshold: float = 95.0  # Percentile cutoff
    
    # Configuration
    lookback_hours: int = 24
    min_data_points: int = 10
    sensitivity: float = 0.8  # 0.0 to 1.0
    is_active: bool = True
    
    created_by: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnomalyDetector:
    """
    Advanced anomaly detection system using statistical and ML techniques.
    """
    
    def __init__(self):
        self.thresholds: List[AnomalyThreshold] = []
        self.detected_anomalies: Dict[str, Anomaly] = {}
        self.historical_baselines: Dict[str, Dict[str, Any]] = {}
        self.time_series_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Configuration
        self.default_confidence_threshold = 0.8
        self.max_anomalies_per_cycle = 50
        self.baseline_update_interval = 3600  # 1 hour
        
        # Load default thresholds
        self._load_default_thresholds()
        
    def _load_default_thresholds(self):
        """Load default anomaly detection thresholds."""
        default_thresholds = [
            AnomalyThreshold(
                threshold_id="case_activity_volume",
                name="Case Activity Volume",
                entity_type="case",
                metric_name="daily_time_entries",
                threshold_type="statistical",
                deviation_threshold=2.5,
                lookback_hours=168,  # 1 week
                min_data_points=7,
                created_by=0
            ),
            AnomalyThreshold(
                threshold_id="attorney_billing_rate",
                name="Attorney Billing Rate Anomaly",
                entity_type="attorney",
                metric_name="hourly_rate",
                threshold_type="statistical",
                deviation_threshold=3.0,
                lookback_hours=720,  # 30 days
                min_data_points=20,
                created_by=0
            ),
            AnomalyThreshold(
                threshold_id="case_duration_outlier",
                name="Case Duration Outlier",
                entity_type="case",
                metric_name="duration_days",
                threshold_type="percentile",
                percentile_threshold=95.0,
                lookback_hours=8760,  # 1 year
                min_data_points=50,
                created_by=0
            ),
            AnomalyThreshold(
                threshold_id="expense_amount_spike",
                name="Expense Amount Spike",
                entity_type="expense",
                metric_name="amount",
                threshold_type="statistical",
                deviation_threshold=2.0,
                lookback_hours=168,  # 1 week
                min_data_points=10,
                sensitivity=0.9,
                created_by=0
            ),
            AnomalyThreshold(
                threshold_id="system_alert_volume",
                name="System Alert Volume",
                entity_type="system",
                metric_name="alerts_per_hour",
                threshold_type="absolute",
                max_value=50.0,
                lookback_hours=24,
                sensitivity=0.7,
                created_by=0
            ),
            AnomalyThreshold(
                threshold_id="client_communication_gap",
                name="Client Communication Gap",
                entity_type="client",
                metric_name="days_since_contact",
                threshold_type="absolute",
                max_value=30.0,
                lookback_hours=24,
                sensitivity=0.6,
                created_by=0
            )
        ]
        
        self.thresholds.extend(default_thresholds)
        
    async def detect_anomalies(
        self,
        data_snapshot: Dict[str, Any],
        detection_timestamp: Optional[datetime] = None
    ) -> List[Anomaly]:
        """Perform comprehensive anomaly detection on data snapshot."""
        if detection_timestamp is None:
            detection_timestamp = datetime.utcnow()
            
        detected_anomalies = []
        
        # Update time series data
        self._update_time_series(data_snapshot, detection_timestamp)
        
        # Apply each active threshold
        for threshold in self.thresholds:
            if not threshold.is_active:
                continue
                
            try:
                anomalies = await self._apply_threshold(threshold, data_snapshot, detection_timestamp)
                detected_anomalies.extend(anomalies)
                
                if len(detected_anomalies) >= self.max_anomalies_per_cycle:
                    break
                    
            except Exception as e:
                logger.error(f"Error applying threshold {threshold.threshold_id}: {str(e)}")
                
        # Post-process and filter anomalies
        validated_anomalies = await self._validate_anomalies(detected_anomalies)
        
        # Store detected anomalies
        for anomaly in validated_anomalies:
            self.detected_anomalies[anomaly.id] = anomaly
            
        # Update baselines periodically
        if self._should_update_baselines():
            await self._update_baselines(data_snapshot)
            
        logger.info(f"Anomaly detection completed: {len(validated_anomalies)} anomalies detected")
        return validated_anomalies
        
    def _update_time_series(self, data_snapshot: Dict[str, Any], timestamp: datetime):
        """Update time series data with new snapshot."""
        # Store data points with timestamps
        for metric_name, value in data_snapshot.items():
            if isinstance(value, (int, float)):
                self.time_series_data[metric_name].append({
                    'timestamp': timestamp,
                    'value': value
                })
                
        # Clean up old data (keep last 1000 points)
        # This is automatically handled by deque maxlen
        
    async def _apply_threshold(
        self,
        threshold: AnomalyThreshold,
        data_snapshot: Dict[str, Any],
        timestamp: datetime
    ) -> List[Anomaly]:
        """Apply a specific threshold to detect anomalies."""
        anomalies = []
        
        # Get relevant data for this threshold
        metric_data = self._get_metric_data(threshold, data_snapshot, timestamp)
        
        if not metric_data or len(metric_data) < threshold.min_data_points:
            return anomalies
            
        if threshold.threshold_type == "statistical":
            anomalies.extend(await self._detect_statistical_anomalies(threshold, metric_data, timestamp))
        elif threshold.threshold_type == "absolute":
            anomalies.extend(await self._detect_absolute_anomalies(threshold, metric_data, timestamp))
        elif threshold.threshold_type == "percentile":
            anomalies.extend(await self._detect_percentile_anomalies(threshold, metric_data, timestamp))
            
        return anomalies
        
    def _get_metric_data(
        self,
        threshold: AnomalyThreshold,
        data_snapshot: Dict[str, Any],
        timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Get relevant metric data for threshold analysis."""
        metric_name = threshold.metric_name
        
        # Get time series data for the lookback period
        cutoff_time = timestamp - timedelta(hours=threshold.lookback_hours)
        
        if metric_name in self.time_series_data:
            time_series = self.time_series_data[metric_name]
            relevant_data = [
                point for point in time_series 
                if point['timestamp'] >= cutoff_time
            ]
            return relevant_data
            
        # If no time series data, try to get from current snapshot
        if metric_name in data_snapshot:
            return [{'timestamp': timestamp, 'value': data_snapshot[metric_name]}]
            
        return []
        
    async def _detect_statistical_anomalies(
        self,
        threshold: AnomalyThreshold,
        metric_data: List[Dict[str, Any]],
        timestamp: datetime
    ) -> List[Anomaly]:
        """Detect statistical outliers using standard deviation."""
        anomalies = []
        
        if len(metric_data) < threshold.min_data_points:
            return anomalies
            
        values = [point['value'] for point in metric_data]
        
        # Calculate statistical measures
        mean_value = np.mean(values)
        std_value = np.std(values)
        
        if std_value == 0:
            return anomalies  # No variation in data
            
        # Get current value (most recent)
        current_value = values[-1]
        
        # Calculate z-score
        z_score = abs(current_value - mean_value) / std_value
        
        if z_score >= threshold.deviation_threshold:
            # Calculate severity based on z-score
            if z_score >= 4.0:
                severity = AnomalySeverity.CRITICAL
            elif z_score >= 3.0:
                severity = AnomalySeverity.HIGH
            elif z_score >= 2.5:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW
                
            # Calculate p-value for statistical significance
            p_value = 2 * (1 - stats.norm.cdf(z_score))  # Two-tailed test
            
            # Calculate confidence level
            confidence = 1 - p_value
            
            if confidence >= self.default_confidence_threshold:
                anomaly = Anomaly(
                    id=f"stat_{threshold.threshold_id}_{int(timestamp.timestamp())}",
                    anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                    severity=severity,
                    title=f"Statistical Anomaly: {threshold.name}",
                    description=f"Value {current_value:.2f} is {z_score:.1f} standard deviations from mean {mean_value:.2f}",
                    observed_value=current_value,
                    expected_value=mean_value,
                    deviation_score=z_score,
                    confidence_level=confidence,
                    p_value=p_value,
                    detection_timestamp=timestamp,
                    context={
                        "threshold_id": threshold.threshold_id,
                        "metric_name": threshold.metric_name,
                        "entity_type": threshold.entity_type,
                        "historical_mean": mean_value,
                        "historical_std": std_value,
                        "data_points": len(values)
                    },
                    potential_causes=[
                        "Unusual activity pattern",
                        "Data input error",
                        "System malfunction",
                        "Process change"
                    ],
                    recommended_actions=[
                        "Investigate data source",
                        "Verify measurement accuracy",
                        "Check for process changes",
                        "Monitor for recurrence"
                    ],
                    detection_method="Z-score statistical analysis"
                )
                anomalies.append(anomaly)
                
        return anomalies
        
    async def _detect_absolute_anomalies(
        self,
        threshold: AnomalyThreshold,
        metric_data: List[Dict[str, Any]],
        timestamp: datetime
    ) -> List[Anomaly]:
        """Detect anomalies using absolute thresholds."""
        anomalies = []
        
        current_value = metric_data[-1]['value']
        violated_threshold = None
        
        if threshold.min_value is not None and current_value < threshold.min_value:
            violated_threshold = "minimum"
            expected_value = threshold.min_value
            
        elif threshold.max_value is not None and current_value > threshold.max_value:
            violated_threshold = "maximum"
            expected_value = threshold.max_value
            
        if violated_threshold:
            # Calculate severity based on how far the value is from threshold
            if threshold.max_value is not None:
                deviation_ratio = (current_value - threshold.max_value) / threshold.max_value
            else:
                deviation_ratio = (threshold.min_value - current_value) / threshold.min_value
                
            if deviation_ratio >= 1.0:
                severity = AnomalySeverity.CRITICAL
            elif deviation_ratio >= 0.5:
                severity = AnomalySeverity.HIGH
            elif deviation_ratio >= 0.2:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW
                
            anomaly = Anomaly(
                id=f"abs_{threshold.threshold_id}_{int(timestamp.timestamp())}",
                anomaly_type=AnomalyType.THRESHOLD_VIOLATION,
                severity=severity,
                title=f"Threshold Violation: {threshold.name}",
                description=f"Value {current_value:.2f} violates {violated_threshold} threshold {expected_value:.2f}",
                observed_value=current_value,
                expected_value=expected_value,
                deviation_score=deviation_ratio,
                confidence_level=0.95,  # High confidence for absolute thresholds
                detection_timestamp=timestamp,
                context={
                    "threshold_id": threshold.threshold_id,
                    "metric_name": threshold.metric_name,
                    "entity_type": threshold.entity_type,
                    "violated_threshold": violated_threshold,
                    "threshold_value": expected_value
                },
                potential_causes=[
                    f"Value exceeded {violated_threshold} operational limit",
                    "System overload or malfunction",
                    "Configuration error",
                    "Unexpected load increase"
                ],
                recommended_actions=[
                    "Investigate immediate cause",
                    "Check system capacity",
                    "Review operational limits",
                    "Implement corrective measures"
                ],
                detection_method="Absolute threshold comparison"
            )
            anomalies.append(anomaly)
            
        return anomalies
        
    async def _detect_percentile_anomalies(
        self,
        threshold: AnomalyThreshold,
        metric_data: List[Dict[str, Any]],
        timestamp: datetime
    ) -> List[Anomaly]:
        """Detect anomalies using percentile-based thresholds."""
        anomalies = []
        
        if len(metric_data) < threshold.min_data_points:
            return anomalies
            
        values = [point['value'] for point in metric_data]
        current_value = values[-1]
        
        # Calculate percentile threshold
        percentile_value = np.percentile(values[:-1], threshold.percentile_threshold)
        
        if current_value > percentile_value:
            # Current value is above the percentile threshold
            actual_percentile = stats.percentileofscore(values, current_value)
            
            # Calculate severity based on percentile
            if actual_percentile >= 99.5:
                severity = AnomalySeverity.CRITICAL
            elif actual_percentile >= 99.0:
                severity = AnomalySeverity.HIGH
            elif actual_percentile >= 97.5:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW
                
            anomaly = Anomaly(
                id=f"perc_{threshold.threshold_id}_{int(timestamp.timestamp())}",
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                severity=severity,
                title=f"Percentile Anomaly: {threshold.name}",
                description=f"Value {current_value:.2f} exceeds {threshold.percentile_threshold}th percentile ({percentile_value:.2f})",
                observed_value=current_value,
                expected_value=percentile_value,
                deviation_score=(current_value - percentile_value) / percentile_value if percentile_value > 0 else 0,
                confidence_level=0.9,
                detection_timestamp=timestamp,
                context={
                    "threshold_id": threshold.threshold_id,
                    "metric_name": threshold.metric_name,
                    "entity_type": threshold.entity_type,
                    "percentile_threshold": threshold.percentile_threshold,
                    "percentile_value": percentile_value,
                    "actual_percentile": actual_percentile,
                    "data_points": len(values)
                },
                potential_causes=[
                    "Exceptional case or event",
                    "Process inefficiency",
                    "Resource constraint",
                    "Measurement error"
                ],
                recommended_actions=[
                    "Investigate exceptional circumstances",
                    "Review process efficiency",
                    "Check resource availability",
                    "Validate measurement accuracy"
                ],
                detection_method="Percentile-based analysis"
            )
            anomalies.append(anomaly)
            
        return anomalies
        
    async def _validate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Validate detected anomalies to reduce false positives."""
        validated = []
        
        for anomaly in anomalies:
            # Skip if confidence is too low
            if anomaly.confidence_level < self.default_confidence_threshold:
                continue
                
            # Check for duplicate anomalies (same type, entity, recent time)
            is_duplicate = False
            cutoff_time = anomaly.detection_timestamp - timedelta(hours=1)
            
            for existing_id, existing_anomaly in self.detected_anomalies.items():
                if (existing_anomaly.anomaly_type == anomaly.anomaly_type and
                    existing_anomaly.detection_timestamp > cutoff_time and
                    existing_anomaly.context.get("threshold_id") == anomaly.context.get("threshold_id")):
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                validated.append(anomaly)
                
        return validated
        
    def _should_update_baselines(self) -> bool:
        """Check if baselines should be updated."""
        # For simplicity, update baselines every hour
        # In production, this would be more sophisticated
        return True
        
    async def _update_baselines(self, data_snapshot: Dict[str, Any]):
        """Update baseline statistics for comparison."""
        for metric_name, time_series in self.time_series_data.items():
            if len(time_series) < 10:
                continue
                
            values = [point['value'] for point in time_series]
            
            baseline = {
                'mean': np.mean(values),
                'std': np.std(values),
                'median': np.median(values),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99),
                'last_updated': datetime.utcnow(),
                'sample_size': len(values)
            }
            
            self.historical_baselines[metric_name] = baseline
            
    async def detect_time_series_anomalies(
        self,
        metric_name: str,
        lookback_hours: int = 24,
        sensitivity: float = 0.8
    ) -> List[Anomaly]:
        """Detect anomalies in time series data using advanced techniques."""
        anomalies = []
        
        if metric_name not in self.time_series_data:
            return anomalies
            
        time_series = list(self.time_series_data[metric_name])
        
        if len(time_series) < 20:  # Need sufficient data for time series analysis
            return anomalies
            
        # Extract values and timestamps
        values = [point['value'] for point in time_series]
        timestamps = [point['timestamp'] for point in time_series]
        
        # Detect various types of time series anomalies
        anomalies.extend(await self._detect_trend_breaks(metric_name, values, timestamps, sensitivity))
        anomalies.extend(await self._detect_seasonal_anomalies(metric_name, values, timestamps, sensitivity))
        anomalies.extend(await self._detect_volume_anomalies(metric_name, values, timestamps, sensitivity))
        
        return anomalies
        
    async def _detect_trend_breaks(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        sensitivity: float
    ) -> List[Anomaly]:
        """Detect breaks in trends using change point detection."""
        anomalies = []
        
        if len(values) < 30:
            return anomalies
            
        # Simple change point detection using moving averages
        window_size = min(10, len(values) // 3)
        moving_avg = []
        
        for i in range(window_size, len(values) - window_size):
            before_avg = np.mean(values[i-window_size:i])
            after_avg = np.mean(values[i:i+window_size])
            change_magnitude = abs(after_avg - before_avg) / (before_avg + 1e-10)
            moving_avg.append(change_magnitude)
            
        if not moving_avg:
            return anomalies
            
        # Find significant change points
        change_threshold = np.percentile(moving_avg, 95) * sensitivity
        
        for i, change_magnitude in enumerate(moving_avg):
            if change_magnitude > change_threshold:
                actual_index = i + window_size
                
                anomaly = Anomaly(
                    id=f"trend_break_{metric_name}_{int(timestamps[actual_index].timestamp())}",
                    anomaly_type=AnomalyType.PATTERN_BREAK,
                    severity=AnomalySeverity.MEDIUM,
                    title=f"Trend Break Detected: {metric_name}",
                    description=f"Significant trend change detected in {metric_name}",
                    observed_value=values[actual_index],
                    expected_value=np.mean(values[:actual_index]),
                    deviation_score=change_magnitude,
                    confidence_level=min(0.9, sensitivity + 0.1),
                    detection_timestamp=timestamps[actual_index],
                    context={
                        "metric_name": metric_name,
                        "change_magnitude": change_magnitude,
                        "window_size": window_size,
                        "change_threshold": change_threshold
                    },
                    potential_causes=[
                        "Process change or intervention",
                        "System update or configuration change",
                        "External factor influence",
                        "Data quality issue"
                    ],
                    recommended_actions=[
                        "Investigate timing of change",
                        "Check for system changes",
                        "Review process modifications",
                        "Validate data integrity"
                    ],
                    detection_method="Change point detection"
                )
                anomalies.append(anomaly)
                
        return anomalies
        
    async def _detect_seasonal_anomalies(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        sensitivity: float
    ) -> List[Anomaly]:
        """Detect seasonal pattern anomalies."""
        anomalies = []
        
        if len(values) < 168:  # Need at least a week of hourly data
            return anomalies
            
        # Group by hour of day to detect daily patterns
        hourly_patterns = defaultdict(list)
        
        for value, timestamp in zip(values, timestamps):
            hour = timestamp.hour
            hourly_patterns[hour].append(value)
            
        # Calculate expected values for each hour
        hourly_expectations = {}
        for hour, hour_values in hourly_patterns.items():
            if len(hour_values) >= 3:  # Need sufficient data points
                hourly_expectations[hour] = {
                    'mean': np.mean(hour_values),
                    'std': np.std(hour_values)
                }
                
        # Check recent values against hourly patterns
        recent_cutoff = timestamps[-1] - timedelta(hours=24)
        
        for i, (value, timestamp) in enumerate(zip(values, timestamps)):
            if timestamp < recent_cutoff:
                continue
                
            hour = timestamp.hour
            if hour not in hourly_expectations:
                continue
                
            expected = hourly_expectations[hour]
            if expected['std'] == 0:
                continue
                
            z_score = abs(value - expected['mean']) / expected['std']
            
            if z_score >= (3.0 * sensitivity):
                anomaly = Anomaly(
                    id=f"seasonal_{metric_name}_{int(timestamp.timestamp())}",
                    anomaly_type=AnomalyType.SEASONAL_DEVIATION,
                    severity=AnomalySeverity.MEDIUM if z_score >= 4.0 else AnomalySeverity.LOW,
                    title=f"Seasonal Anomaly: {metric_name}",
                    description=f"Value deviates from typical hour-{hour} pattern",
                    observed_value=value,
                    expected_value=expected['mean'],
                    deviation_score=z_score,
                    confidence_level=min(0.85, sensitivity),
                    detection_timestamp=timestamp,
                    context={
                        "metric_name": metric_name,
                        "hour": hour,
                        "expected_mean": expected['mean'],
                        "expected_std": expected['std'],
                        "historical_samples": len(hourly_patterns[hour])
                    },
                    potential_causes=[
                        "Unusual activity timing",
                        "Schedule disruption",
                        "Special event or condition",
                        "Process timing change"
                    ],
                    recommended_actions=[
                        "Check for schedule changes",
                        "Investigate special events",
                        "Review process timing",
                        "Monitor pattern recovery"
                    ],
                    detection_method="Seasonal pattern analysis"
                )
                anomalies.append(anomaly)
                
        return anomalies
        
    async def _detect_volume_anomalies(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        sensitivity: float
    ) -> List[Anomaly]:
        """Detect unusual volume or rate changes."""
        anomalies = []
        
        if len(values) < 10:
            return anomalies
            
        # Calculate moving average and detect sudden spikes/drops
        window_size = min(5, len(values) // 2)
        
        for i in range(window_size, len(values)):
            current_value = values[i]
            recent_avg = np.mean(values[i-window_size:i])
            
            if recent_avg == 0:
                continue
                
            # Calculate relative change
            relative_change = abs(current_value - recent_avg) / recent_avg
            
            # Volume spike threshold based on sensitivity
            spike_threshold = 2.0 * sensitivity
            
            if relative_change >= spike_threshold:
                severity = AnomalySeverity.HIGH if relative_change >= 5.0 else AnomalySeverity.MEDIUM
                
                anomaly = Anomaly(
                    id=f"volume_{metric_name}_{int(timestamps[i].timestamp())}",
                    anomaly_type=AnomalyType.VOLUME_ANOMALY,
                    severity=severity,
                    title=f"Volume Anomaly: {metric_name}",
                    description=f"Sudden volume change: {relative_change:.1%} from recent average",
                    observed_value=current_value,
                    expected_value=recent_avg,
                    deviation_score=relative_change,
                    confidence_level=min(0.9, sensitivity + 0.1),
                    detection_timestamp=timestamps[i],
                    context={
                        "metric_name": metric_name,
                        "relative_change": relative_change,
                        "window_size": window_size,
                        "recent_average": recent_avg
                    },
                    potential_causes=[
                        "Sudden workload increase/decrease",
                        "System performance issue",
                        "Batch processing event",
                        "Data ingestion anomaly"
                    ],
                    recommended_actions=[
                        "Check system load",
                        "Investigate batch processes",
                        "Review recent changes",
                        "Monitor for continuation"
                    ],
                    detection_method="Volume change analysis"
                )
                anomalies.append(anomaly)
                
        return anomalies
        
    # Public API methods
    
    async def get_active_anomalies(
        self,
        anomaly_type: Optional[AnomalyType] = None,
        severity: Optional[AnomalySeverity] = None,
        entity_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Anomaly]:
        """Get active anomalies with optional filtering."""
        anomalies = [a for a in self.detected_anomalies.values() if not a.is_resolved]
        
        if anomaly_type:
            anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]
            
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
            
        if entity_type:
            anomalies = [a for a in anomalies if a.context.get("entity_type") == entity_type]
            
        # Sort by severity and detection time
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3,
            AnomalySeverity.NOISE: 4
        }
        
        anomalies.sort(key=lambda x: (severity_order.get(x.severity, 5), -x.detection_timestamp.timestamp()))
        
        if limit:
            anomalies = anomalies[:limit]
            
        return anomalies
        
    async def confirm_anomaly(self, anomaly_id: str, user_id: int) -> bool:
        """Confirm an anomaly as a true positive."""
        if anomaly_id in self.detected_anomalies:
            self.detected_anomalies[anomaly_id].is_confirmed = True
            logger.info(f"Anomaly {anomaly_id} confirmed by user {user_id}")
            return True
        return False
        
    async def resolve_anomaly(self, anomaly_id: str, user_id: int, resolution_notes: Optional[str] = None) -> bool:
        """Mark an anomaly as resolved."""
        if anomaly_id in self.detected_anomalies:
            anomaly = self.detected_anomalies[anomaly_id]
            anomaly.is_resolved = True
            anomaly.resolved_at = datetime.utcnow()
            if resolution_notes:
                anomaly.context["resolution_notes"] = resolution_notes
                anomaly.context["resolved_by"] = user_id
            logger.info(f"Anomaly {anomaly_id} resolved by user {user_id}")
            return True
        return False
        
    async def add_threshold(self, threshold: AnomalyThreshold) -> bool:
        """Add a new anomaly detection threshold."""
        # Check for duplicate threshold ID
        for existing_threshold in self.thresholds:
            if existing_threshold.threshold_id == threshold.threshold_id:
                return False
                
        self.thresholds.append(threshold)
        logger.info(f"Added anomaly threshold: {threshold.name}")
        return True
        
    async def get_anomaly_statistics(self) -> Dict[str, Any]:
        """Get anomaly detection statistics."""
        all_anomalies = list(self.detected_anomalies.values())
        active_anomalies = [a for a in all_anomalies if not a.is_resolved]
        
        # Count by type
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for anomaly in active_anomalies:
            type_counts[anomaly.anomaly_type] += 1
            severity_counts[anomaly.severity] += 1
            
        return {
            "total_anomalies": len(all_anomalies),
            "active_anomalies": len(active_anomalies),
            "resolved_anomalies": len([a for a in all_anomalies if a.is_resolved]),
            "confirmed_anomalies": len([a for a in all_anomalies if a.is_confirmed]),
            "detection_thresholds": len([t for t in self.thresholds if t.is_active]),
            "type_distribution": dict(type_counts),
            "severity_distribution": dict(severity_counts),
            "false_positive_rate": len([a for a in all_anomalies if not a.is_confirmed and a.is_resolved]) / max(len(all_anomalies), 1)
        }