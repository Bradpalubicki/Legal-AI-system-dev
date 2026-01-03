"""
Performance Monitor Module

Advanced performance monitoring system for tracking model performance,
detecting data drift, and maintaining model quality over time.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import asyncio
import json
import warnings
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class MetricType(Enum):
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    AUC_ROC = "auc_roc"
    MSE = "mse"
    RMSE = "rmse"
    MAE = "mae"
    R2_SCORE = "r2_score"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    USER_SATISFACTION = "user_satisfaction"
    PREDICTION_CONFIDENCE = "prediction_confidence"
    FEATURE_DRIFT = "feature_drift"
    LABEL_DRIFT = "label_drift"
    CONCEPT_DRIFT = "concept_drift"
    DATA_QUALITY = "data_quality"
    MODEL_STABILITY = "model_stability"
    FAIRNESS = "fairness"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DriftType(Enum):
    FEATURE_DRIFT = "feature_drift"
    LABEL_DRIFT = "label_drift"
    CONCEPT_DRIFT = "concept_drift"
    PREDICTION_DRIFT = "prediction_drift"
    PERFORMANCE_DRIFT = "performance_drift"

@dataclass
class PerformanceMetric:
    id: Optional[int] = None
    metric_type: MetricType = MetricType.ACCURACY
    model_id: str = ""
    model_version: str = ""
    metric_value: float = 0.0
    baseline_value: Optional[float] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    data_window_start: datetime = field(default_factory=datetime.utcnow)
    data_window_end: datetime = field(default_factory=datetime.utcnow)
    sample_size: int = 0
    confidence_interval: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    statistical_significance: Optional[float] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    alert_triggered: bool = False
    alert_severity: Optional[AlertSeverity] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DriftDetector:
    drift_type: DriftType = DriftType.FEATURE_DRIFT
    detection_method: str = "statistical"
    sensitivity: float = 0.05  # p-value threshold
    window_size: int = 1000  # Number of samples for comparison
    reference_data: Optional[np.ndarray] = None
    current_data: Optional[np.ndarray] = None
    drift_score: float = 0.0
    drift_detected: bool = False
    detection_timestamp: Optional[datetime] = None
    affected_features: List[str] = field(default_factory=list)
    test_statistic: Optional[float] = None
    p_value: Optional[float] = None
    drift_magnitude: str = "none"  # none, mild, moderate, severe
    mitigation_suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    def __init__(self):
        self.metrics_history: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.baseline_metrics: Dict[str, Dict[MetricType, float]] = {}
        self.alert_rules: Dict[MetricType, Dict[str, float]] = {}
        self.drift_detectors: Dict[str, DriftDetector] = {}
        self.monitoring_config = {
            'monitoring_interval_minutes': 15,
            'retention_days': 90,
            'alert_cooldown_minutes': 60,
            'statistical_confidence': 0.95,
            'performance_alert_threshold': 0.05,  # 5% degradation
            'drift_sensitivity': 0.05,
            'min_samples_for_drift': 100,
            'batch_size': 1000
        }
        
        # Default thresholds for different metrics
        self.default_thresholds = {
            MetricType.ACCURACY: {'min': 0.7, 'degradation_threshold': 0.05},
            MetricType.PRECISION: {'min': 0.7, 'degradation_threshold': 0.05},
            MetricType.RECALL: {'min': 0.7, 'degradation_threshold': 0.05},
            MetricType.F1_SCORE: {'min': 0.7, 'degradation_threshold': 0.05},
            MetricType.R2_SCORE: {'min': 0.5, 'degradation_threshold': 0.1},
            MetricType.MSE: {'max': 1.0, 'degradation_threshold': 0.2},
            MetricType.RESPONSE_TIME: {'max': 5000, 'degradation_threshold': 0.5},  # milliseconds
            MetricType.ERROR_RATE: {'max': 0.05, 'degradation_threshold': 0.02},
        }

    async def record_metric(
        self,
        model_id: str,
        model_version: str,
        metric_type: MetricType,
        metric_value: float,
        sample_size: int = 1,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> PerformanceMetric:
        """Record a performance metric."""
        try:
            # Create metric record
            metric = PerformanceMetric(
                metric_type=metric_type,
                model_id=model_id,
                model_version=model_version,
                metric_value=metric_value,
                sample_size=sample_size,
                context_data=context_data or {},
                data_window_end=datetime.utcnow()
            )
            
            # Calculate confidence interval if sample size is sufficient
            if sample_size > 30:
                confidence_level = self.monitoring_config['statistical_confidence']
                margin_of_error = stats.norm.ppf((1 + confidence_level) / 2) * np.sqrt(metric_value * (1 - metric_value) / sample_size)
                metric.confidence_interval = (
                    max(0, metric_value - margin_of_error),
                    min(1, metric_value + margin_of_error)
                )
            
            # Set baseline if this is the first metric for this model-metric combination
            model_metric_key = f"{model_id}_{metric_type.value}"
            if model_id not in self.baseline_metrics:
                self.baseline_metrics[model_id] = {}
            
            if metric_type not in self.baseline_metrics[model_id]:
                self.baseline_metrics[model_id][metric_type] = metric_value
                metric.baseline_value = metric_value
            else:
                metric.baseline_value = self.baseline_metrics[model_id][metric_type]
            
            # Check for alerts
            alert_result = await self._check_metric_alerts(metric)
            metric.alert_triggered = alert_result['triggered']
            metric.alert_severity = alert_result['severity']
            
            # Store metric
            self.metrics_history[model_metric_key].append(metric)
            
            # Persist to database
            if db:
                await self._persist_metric(metric, db)
            
            # Cleanup old metrics
            await self._cleanup_old_metrics()
            
            logger.info(f"Recorded metric: {metric_type.value} = {metric_value:.4f} for {model_id}")
            return metric
            
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
            raise

    async def detect_drift(
        self,
        model_id: str,
        current_data: np.ndarray,
        drift_type: DriftType = DriftType.FEATURE_DRIFT,
        feature_names: Optional[List[str]] = None,
        reference_window_days: int = 30
    ) -> DriftDetector:
        """Detect data drift using statistical tests."""
        try:
            # Get reference data from historical metrics
            reference_data = await self._get_reference_data(model_id, reference_window_days, drift_type)
            
            if reference_data is None or len(reference_data) < self.monitoring_config['min_samples_for_drift']:
                logger.warning(f"Insufficient reference data for drift detection: {model_id}")
                return DriftDetector(
                    drift_type=drift_type,
                    drift_detected=False,
                    drift_magnitude="insufficient_data"
                )
            
            # Create drift detector
            detector = DriftDetector(
                drift_type=drift_type,
                reference_data=reference_data,
                current_data=current_data,
                window_size=len(current_data),
                detection_timestamp=datetime.utcnow()
            )
            
            # Perform drift detection based on type
            if drift_type == DriftType.FEATURE_DRIFT:
                await self._detect_feature_drift(detector, feature_names)
            elif drift_type == DriftType.LABEL_DRIFT:
                await self._detect_label_drift(detector)
            elif drift_type == DriftType.PREDICTION_DRIFT:
                await self._detect_prediction_drift(detector)
            elif drift_type == DriftType.PERFORMANCE_DRIFT:
                await self._detect_performance_drift(detector, model_id)
            
            # Store drift detector
            detector_key = f"{model_id}_{drift_type.value}"
            self.drift_detectors[detector_key] = detector
            
            # Generate mitigation suggestions if drift detected
            if detector.drift_detected:
                detector.mitigation_suggestions = await self._generate_drift_mitigation(detector)
                logger.warning(f"Drift detected for {model_id}: {drift_type.value} (magnitude: {detector.drift_magnitude})")
            
            return detector
            
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return DriftDetector(drift_type=drift_type, drift_detected=False, drift_magnitude="error")

    async def get_performance_dashboard(
        self,
        model_id: Optional[str] = None,
        time_window_hours: int = 24,
        include_charts: bool = False
    ) -> Dict[str, Any]:
        """Generate comprehensive performance dashboard."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            dashboard = {
                'time_window': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'hours': time_window_hours
                },
                'models': {},
                'alerts': [],
                'drift_status': {},
                'summary': {},
                'charts': {} if include_charts else None
            }
            
            # Filter metrics by time window and model
            relevant_metrics = []
            for key, metrics_list in self.metrics_history.items():
                filtered_metrics = [
                    m for m in metrics_list
                    if m.created_at >= start_time and (not model_id or m.model_id == model_id)
                ]
                relevant_metrics.extend(filtered_metrics)
            
            if not relevant_metrics:
                dashboard['message'] = 'No performance data available for the specified criteria'
                return dashboard
            
            # Group metrics by model
            metrics_by_model = defaultdict(lambda: defaultdict(list))
            for metric in relevant_metrics:
                metrics_by_model[metric.model_id][metric.metric_type].append(metric)
            
            # Analyze each model
            for model_name, model_metrics in metrics_by_model.items():
                model_analysis = {
                    'metrics': {},
                    'trends': {},
                    'alerts': [],
                    'health_score': 0.0
                }
                
                # Analyze each metric type
                health_scores = []
                for metric_type, metrics_list in model_metrics.items():
                    if not metrics_list:
                        continue
                    
                    # Calculate statistics
                    values = [m.metric_value for m in metrics_list]
                    metric_analysis = {
                        'current_value': values[-1],
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'count': len(values),
                        'trend': self._calculate_trend(values),
                        'baseline_comparison': None
                    }
                    
                    # Compare to baseline
                    if model_name in self.baseline_metrics and metric_type in self.baseline_metrics[model_name]:
                        baseline = self.baseline_metrics[model_name][metric_type]
                        current = values[-1]
                        change = ((current - baseline) / baseline) * 100 if baseline != 0 else 0
                        metric_analysis['baseline_comparison'] = {
                            'baseline_value': baseline,
                            'change_percent': change,
                            'improvement': self._is_improvement(metric_type, change)
                        }
                    
                    model_analysis['metrics'][metric_type.value] = metric_analysis
                    
                    # Calculate health score contribution
                    health_score = self._calculate_metric_health_score(metric_type, values[-1])
                    health_scores.append(health_score)
                    
                    # Check for alerts
                    alerts = [m for m in metrics_list if m.alert_triggered]
                    if alerts:
                        model_analysis['alerts'].extend([{
                            'metric_type': metric_type.value,
                            'severity': alert.alert_severity.value if alert.alert_severity else 'unknown',
                            'value': alert.metric_value,
                            'timestamp': alert.created_at.isoformat()
                        } for alert in alerts])
                
                # Overall model health score
                model_analysis['health_score'] = np.mean(health_scores) if health_scores else 0.5
                dashboard['models'][model_name] = model_analysis
                
                # Add to global alerts
                dashboard['alerts'].extend(model_analysis['alerts'])
            
            # Drift status
            for detector_key, detector in self.drift_detectors.items():
                if detector.detection_timestamp and detector.detection_timestamp >= start_time:
                    if not model_id or model_id in detector_key:
                        dashboard['drift_status'][detector_key] = {
                            'drift_type': detector.drift_type.value,
                            'drift_detected': detector.drift_detected,
                            'drift_magnitude': detector.drift_magnitude,
                            'drift_score': detector.drift_score,
                            'affected_features': detector.affected_features,
                            'detection_timestamp': detector.detection_timestamp.isoformat()
                        }
            
            # Summary statistics
            all_health_scores = [model_data['health_score'] for model_data in dashboard['models'].values()]
            dashboard['summary'] = {
                'models_monitored': len(dashboard['models']),
                'total_alerts': len(dashboard['alerts']),
                'critical_alerts': len([a for a in dashboard['alerts'] if a['severity'] == 'critical']),
                'drift_detections': len([d for d in dashboard['drift_status'].values() if d['drift_detected']]),
                'avg_health_score': np.mean(all_health_scores) if all_health_scores else 0.0,
                'overall_status': self._determine_overall_status(dashboard)
            }
            
            # Generate charts if requested
            if include_charts:
                dashboard['charts'] = await self._generate_performance_charts(relevant_metrics)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating performance dashboard: {e}")
            return {'error': str(e)}

    async def set_alert_rules(
        self,
        model_id: str,
        metric_type: MetricType,
        min_threshold: Optional[float] = None,
        max_threshold: Optional[float] = None,
        degradation_threshold: Optional[float] = None,
        enabled: bool = True
    ) -> bool:
        """Set custom alert rules for a specific metric."""
        try:
            if metric_type not in self.alert_rules:
                self.alert_rules[metric_type] = {}
            
            rule_key = f"{model_id}_{metric_type.value}"
            self.alert_rules[metric_type][rule_key] = {
                'model_id': model_id,
                'min_threshold': min_threshold,
                'max_threshold': max_threshold,
                'degradation_threshold': degradation_threshold,
                'enabled': enabled,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Set alert rule for {model_id} {metric_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting alert rules: {e}")
            return False

    async def get_model_trends(
        self,
        model_id: str,
        metric_types: Optional[List[MetricType]] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Analyze performance trends for a specific model."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            trends = {
                'model_id': model_id,
                'analysis_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days_back
                },
                'metrics': {},
                'overall_trend': 'stable',
                'insights': [],
                'recommendations': []
            }
            
            if not metric_types:
                metric_types = list(MetricType)
            
            overall_trends = []
            
            for metric_type in metric_types:
                metric_key = f"{model_id}_{metric_type.value}"
                
                if metric_key not in self.metrics_history:
                    continue
                
                # Filter metrics by time window
                relevant_metrics = [
                    m for m in self.metrics_history[metric_key]
                    if start_time <= m.created_at <= end_time
                ]
                
                if len(relevant_metrics) < 5:  # Need at least 5 points for trend analysis
                    continue
                
                # Extract time series data
                timestamps = [m.created_at for m in relevant_metrics]
                values = [m.metric_value for m in relevant_metrics]
                
                # Perform trend analysis
                trend_analysis = await self._analyze_metric_trend(timestamps, values, metric_type)
                trends['metrics'][metric_type.value] = trend_analysis
                
                # Contribute to overall trend
                overall_trends.append(trend_analysis['direction'])
            
            # Determine overall trend
            if overall_trends:
                improving_count = overall_trends.count('improving')
                declining_count = overall_trends.count('declining')
                
                if improving_count > declining_count:
                    trends['overall_trend'] = 'improving'
                elif declining_count > improving_count:
                    trends['overall_trend'] = 'declining'
                else:
                    trends['overall_trend'] = 'stable'
            
            # Generate insights and recommendations
            trends['insights'] = await self._generate_trend_insights(trends['metrics'])
            trends['recommendations'] = await self._generate_trend_recommendations(trends)
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing model trends: {e}")
            return {'error': str(e)}

    async def compare_model_versions(
        self,
        model_id: str,
        version1: str,
        version2: str,
        metric_types: Optional[List[MetricType]] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Compare performance between two model versions."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            comparison = {
                'model_id': model_id,
                'version1': version1,
                'version2': version2,
                'time_window_hours': time_window_hours,
                'metrics_comparison': {},
                'winner': None,
                'significant_differences': [],
                'recommendations': []
            }
            
            if not metric_types:
                metric_types = [MetricType.ACCURACY, MetricType.PRECISION, MetricType.RECALL, MetricType.F1_SCORE]
            
            version_scores = {version1: [], version2: []}
            
            for metric_type in metric_types:
                # Get metrics for both versions
                version1_metrics = await self._get_version_metrics(
                    model_id, version1, metric_type, start_time, end_time
                )
                version2_metrics = await self._get_version_metrics(
                    model_id, version2, metric_type, start_time, end_time
                )
                
                if not version1_metrics or not version2_metrics:
                    continue
                
                # Calculate statistics
                v1_values = [m.metric_value for m in version1_metrics]
                v2_values = [m.metric_value for m in version2_metrics]
                
                v1_mean = np.mean(v1_values)
                v2_mean = np.mean(v2_values)
                
                # Statistical significance test
                try:
                    statistic, p_value = stats.ttest_ind(v1_values, v2_values)
                    is_significant = p_value < 0.05
                except:
                    statistic, p_value, is_significant = 0, 1.0, False
                
                metric_comparison = {
                    'version1': {
                        'mean': v1_mean,
                        'std': np.std(v1_values),
                        'count': len(v1_values)
                    },
                    'version2': {
                        'mean': v2_mean,
                        'std': np.std(v2_values),
                        'count': len(v2_values)
                    },
                    'difference': v2_mean - v1_mean,
                    'percent_change': ((v2_mean - v1_mean) / v1_mean * 100) if v1_mean != 0 else 0,
                    'statistically_significant': is_significant,
                    'p_value': p_value,
                    'winner': version2 if v2_mean > v1_mean else version1
                }
                
                comparison['metrics_comparison'][metric_type.value] = metric_comparison
                
                # For error metrics, lower is better
                if metric_type in [MetricType.MSE, MetricType.RMSE, MetricType.MAE, MetricType.ERROR_RATE]:
                    score = 1 if v2_mean < v1_mean else 0
                else:
                    score = 1 if v2_mean > v1_mean else 0
                
                version_scores[version1].append(1 - score)
                version_scores[version2].append(score)
                
                # Track significant differences
                if is_significant and abs(metric_comparison['percent_change']) > 5:  # >5% change
                    comparison['significant_differences'].append({
                        'metric': metric_type.value,
                        'change_percent': metric_comparison['percent_change'],
                        'improvement': metric_comparison['winner'] == version2
                    })
            
            # Determine overall winner
            if version_scores[version1] and version_scores[version2]:
                v1_total = sum(version_scores[version1])
                v2_total = sum(version_scores[version2])
                
                if v2_total > v1_total:
                    comparison['winner'] = version2
                elif v1_total > v2_total:
                    comparison['winner'] = version1
                else:
                    comparison['winner'] = 'tie'
            
            # Generate recommendations
            comparison['recommendations'] = await self._generate_version_comparison_recommendations(comparison)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing model versions: {e}")
            return {'error': str(e)}

    # Private helper methods
    
    async def _check_metric_alerts(self, metric: PerformanceMetric) -> Dict[str, Any]:
        """Check if metric triggers any alerts."""
        try:
            alert_result = {'triggered': False, 'severity': None, 'reasons': []}
            
            # Get alert rules for this metric
            rule_key = f"{metric.model_id}_{metric.metric_type.value}"
            custom_rule = None
            
            if metric.metric_type in self.alert_rules and rule_key in self.alert_rules[metric.metric_type]:
                custom_rule = self.alert_rules[metric.metric_type][rule_key]
                if not custom_rule.get('enabled', True):
                    return alert_result
            
            # Get thresholds (custom or default)
            if custom_rule:
                min_threshold = custom_rule.get('min_threshold')
                max_threshold = custom_rule.get('max_threshold')
                degradation_threshold = custom_rule.get('degradation_threshold')
            else:
                default_config = self.default_thresholds.get(metric.metric_type, {})
                min_threshold = default_config.get('min')
                max_threshold = default_config.get('max')
                degradation_threshold = default_config.get('degradation_threshold')
            
            # Check absolute thresholds
            if min_threshold and metric.metric_value < min_threshold:
                alert_result['triggered'] = True
                alert_result['reasons'].append(f"Value {metric.metric_value:.3f} below minimum threshold {min_threshold}")
                alert_result['severity'] = AlertSeverity.HIGH
            
            if max_threshold and metric.metric_value > max_threshold:
                alert_result['triggered'] = True
                alert_result['reasons'].append(f"Value {metric.metric_value:.3f} above maximum threshold {max_threshold}")
                alert_result['severity'] = AlertSeverity.HIGH
            
            # Check degradation from baseline
            if (degradation_threshold and metric.baseline_value and 
                metric.baseline_value != 0):
                
                if metric.metric_type in [MetricType.MSE, MetricType.RMSE, MetricType.MAE, MetricType.ERROR_RATE]:
                    # For error metrics, increase is degradation
                    degradation = (metric.metric_value - metric.baseline_value) / metric.baseline_value
                else:
                    # For performance metrics, decrease is degradation
                    degradation = (metric.baseline_value - metric.metric_value) / metric.baseline_value
                
                if degradation > degradation_threshold:
                    alert_result['triggered'] = True
                    alert_result['reasons'].append(f"Performance degraded by {degradation:.1%} from baseline")
                    alert_result['severity'] = AlertSeverity.MEDIUM if degradation < 0.15 else AlertSeverity.HIGH
            
            return alert_result
            
        except Exception as e:
            logger.error(f"Error checking metric alerts: {e}")
            return {'triggered': False, 'severity': None, 'reasons': []}

    async def _detect_feature_drift(
        self, 
        detector: DriftDetector, 
        feature_names: Optional[List[str]] = None
    ) -> None:
        """Detect feature drift using statistical tests."""
        try:
            if detector.reference_data is None or detector.current_data is None:
                return
            
            # Ensure data is 2D
            ref_data = detector.reference_data.reshape(-1, 1) if detector.reference_data.ndim == 1 else detector.reference_data
            cur_data = detector.current_data.reshape(-1, 1) if detector.current_data.ndim == 1 else detector.current_data
            
            if ref_data.shape[1] != cur_data.shape[1]:
                logger.warning("Reference and current data have different number of features")
                return
            
            # Perform Kolmogorov-Smirnov test for each feature
            n_features = ref_data.shape[1]
            drift_scores = []
            p_values = []
            drifted_features = []
            
            for i in range(n_features):
                try:
                    statistic, p_value = stats.ks_2samp(ref_data[:, i], cur_data[:, i])
                    drift_scores.append(statistic)
                    p_values.append(p_value)
                    
                    if p_value < detector.sensitivity:
                        feature_name = feature_names[i] if feature_names and i < len(feature_names) else f"feature_{i}"
                        drifted_features.append(feature_name)
                        
                except Exception as e:
                    logger.warning(f"Error testing feature {i}: {e}")
                    drift_scores.append(0.0)
                    p_values.append(1.0)
            
            # Aggregate results
            if drift_scores:
                detector.drift_score = np.mean(drift_scores)
                detector.p_value = np.mean(p_values)
                detector.test_statistic = np.mean(drift_scores)
                detector.affected_features = drifted_features
                detector.drift_detected = len(drifted_features) > 0
                
                # Determine drift magnitude
                if not detector.drift_detected:
                    detector.drift_magnitude = "none"
                elif len(drifted_features) / n_features < 0.25:
                    detector.drift_magnitude = "mild"
                elif len(drifted_features) / n_features < 0.5:
                    detector.drift_magnitude = "moderate"
                else:
                    detector.drift_magnitude = "severe"
            
        except Exception as e:
            logger.error(f"Error detecting feature drift: {e}")

    async def _detect_performance_drift(self, detector: DriftDetector, model_id: str) -> None:
        """Detect performance drift by comparing recent vs historical performance."""
        try:
            # Get recent performance metrics
            recent_window = datetime.utcnow() - timedelta(days=7)
            baseline_window = datetime.utcnow() - timedelta(days=30)
            
            recent_metrics = []
            baseline_metrics = []
            
            for key, metrics_list in self.metrics_history.items():
                if model_id in key and MetricType.ACCURACY.value in key:  # Focus on accuracy for simplicity
                    for metric in metrics_list:
                        if metric.created_at >= recent_window:
                            recent_metrics.append(metric.metric_value)
                        elif baseline_window <= metric.created_at < recent_window:
                            baseline_metrics.append(metric.metric_value)
            
            if len(recent_metrics) < 5 or len(baseline_metrics) < 5:
                detector.drift_magnitude = "insufficient_data"
                return
            
            # Compare performance distributions
            try:
                statistic, p_value = stats.ttest_ind(baseline_metrics, recent_metrics)
                detector.test_statistic = statistic
                detector.p_value = p_value
                detector.drift_detected = p_value < detector.sensitivity
                
                if detector.drift_detected:
                    recent_mean = np.mean(recent_metrics)
                    baseline_mean = np.mean(baseline_metrics)
                    performance_change = (recent_mean - baseline_mean) / baseline_mean
                    
                    if abs(performance_change) < 0.05:
                        detector.drift_magnitude = "mild"
                    elif abs(performance_change) < 0.15:
                        detector.drift_magnitude = "moderate"
                    else:
                        detector.drift_magnitude = "severe"
                        
                    detector.drift_score = abs(performance_change)
                else:
                    detector.drift_magnitude = "none"
                    
            except Exception as e:
                logger.error(f"Error in performance drift statistical test: {e}")
                detector.drift_magnitude = "error"
            
        except Exception as e:
            logger.error(f"Error detecting performance drift: {e}")

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 3:
            return "insufficient_data"
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        if abs(slope) < 0.001:  # Very small slope
            return "stable"
        elif slope > 0:
            return "improving" if r_value > 0.5 else "stable"
        else:
            return "declining" if r_value < -0.5 else "stable"

    def _is_improvement(self, metric_type: MetricType, change_percent: float) -> bool:
        """Determine if a change represents an improvement for the given metric."""
        # For error metrics, negative change (decrease) is improvement
        if metric_type in [MetricType.MSE, MetricType.RMSE, MetricType.MAE, MetricType.ERROR_RATE]:
            return change_percent < 0
        # For performance metrics, positive change (increase) is improvement
        else:
            return change_percent > 0

    def _calculate_metric_health_score(self, metric_type: MetricType, value: float) -> float:
        """Calculate a health score (0-1) for a metric value."""
        try:
            thresholds = self.default_thresholds.get(metric_type, {})
            
            if 'min' in thresholds:
                min_threshold = thresholds['min']
                if value >= min_threshold:
                    return min(1.0, value)  # Cap at 1.0
                else:
                    return max(0.0, value / min_threshold)  # Proportional below threshold
            
            elif 'max' in thresholds:
                max_threshold = thresholds['max']
                if value <= max_threshold:
                    return 1.0 - (value / max_threshold) if max_threshold > 0 else 1.0
                else:
                    return max(0.0, 1.0 - (value / max_threshold))
            
            else:
                # Default: assume higher is better and cap at 1.0
                return min(1.0, max(0.0, value))
                
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.5  # Default neutral score

    def _determine_overall_status(self, dashboard: Dict[str, Any]) -> str:
        """Determine overall system status from dashboard data."""
        try:
            critical_alerts = dashboard['summary']['critical_alerts']
            drift_detections = dashboard['summary']['drift_detections']
            avg_health_score = dashboard['summary']['avg_health_score']
            
            if critical_alerts > 0:
                return "critical"
            elif drift_detections > 0 or avg_health_score < 0.7:
                return "warning"
            elif avg_health_score >= 0.8:
                return "healthy"
            else:
                return "caution"
                
        except Exception as e:
            logger.error(f"Error determining overall status: {e}")
            return "unknown"

    async def _cleanup_old_metrics(self) -> None:
        """Remove old metrics beyond retention period."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.monitoring_config['retention_days'])
            
            for key, metrics_list in self.metrics_history.items():
                # Keep metrics within retention period
                self.metrics_history[key] = [
                    m for m in metrics_list if m.created_at >= cutoff_date
                ]
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

    async def _persist_metric(self, metric: PerformanceMetric, db: AsyncSession) -> None:
        """Persist metric to database."""
        try:
            # This would typically involve database operations
            logger.debug(f"Persisting metric {metric.metric_type.value} to database")
        except Exception as e:
            logger.error(f"Error persisting metric: {e}")

    # Additional helper methods would be implemented here for:
    # - _get_reference_data
    # - _detect_label_drift
    # - _detect_prediction_drift
    # - _generate_drift_mitigation
    # - _generate_performance_charts
    # - _analyze_metric_trend
    # - _generate_trend_insights
    # - _generate_trend_recommendations
    # - _get_version_metrics
    # - _generate_version_comparison_recommendations

    async def _get_reference_data(
        self, 
        model_id: str, 
        window_days: int, 
        drift_type: DriftType
    ) -> Optional[np.ndarray]:
        """Get reference data for drift detection."""
        try:
            # This would typically query historical data
            # For now, return mock reference data
            if drift_type == DriftType.FEATURE_DRIFT:
                return np.random.randn(1000, 5)  # Mock feature data
            else:
                return np.random.randn(1000)  # Mock single-value data
        except Exception as e:
            logger.error(f"Error getting reference data: {e}")
            return None

    async def _generate_drift_mitigation(self, detector: DriftDetector) -> List[str]:
        """Generate mitigation suggestions for detected drift."""
        suggestions = []
        
        if detector.drift_detected:
            suggestions.append("Consider retraining the model with recent data")
            
            if detector.drift_type == DriftType.FEATURE_DRIFT:
                suggestions.append("Review data preprocessing pipeline for changes")
                suggestions.append("Investigate data source quality and consistency")
                
                if detector.affected_features:
                    suggestions.append(f"Focus on features showing drift: {', '.join(detector.affected_features[:3])}")
            
            elif detector.drift_type == DriftType.PERFORMANCE_DRIFT:
                suggestions.append("Analyze recent model predictions for quality issues")
                suggestions.append("Consider gradual model rollback if performance continues to degrade")
            
            if detector.drift_magnitude == "severe":
                suggestions.append("Immediate intervention recommended - consider emergency model rollback")
        
        return suggestions

    async def _analyze_metric_trend(
        self, 
        timestamps: List[datetime], 
        values: List[float], 
        metric_type: MetricType
    ) -> Dict[str, Any]:
        """Analyze trend for a specific metric."""
        try:
            # Convert timestamps to numeric values for regression
            start_time = min(timestamps)
            x = [(ts - start_time).total_seconds() for ts in timestamps]
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Determine trend direction
            if abs(slope) < 1e-6:  # Very small slope
                direction = "stable"
            elif slope > 0:
                direction = "improving" if abs(r_value) > 0.5 else "stable"
            else:
                direction = "declining" if abs(r_value) > 0.5 else "stable"
            
            # Calculate trend strength
            strength = min(1.0, abs(r_value))
            
            return {
                'direction': direction,
                'strength': strength,
                'slope': slope,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'current_value': values[-1],
                'mean_value': np.mean(values),
                'volatility': np.std(values)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing metric trend: {e}")
            return {'direction': 'unknown', 'strength': 0.0}