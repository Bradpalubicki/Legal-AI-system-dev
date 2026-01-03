"""
Experiment Monitoring and Safety Controls for A/B Testing

Real-time monitoring system for A/B testing experiments with automated
safety checks, alert generation, and experiment control mechanisms.
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import numpy as np

class AlertCondition(str, Enum):
    """Types of alert conditions"""
    METRIC_THRESHOLD = "metric_threshold"
    CONVERSION_RATE_DROP = "conversion_rate_drop"
    ERROR_RATE_SPIKE = "error_rate_spike"
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    SAMPLE_SIZE_REACHED = "sample_size_reached"
    DURATION_EXCEEDED = "duration_exceeded"
    TRAFFIC_ANOMALY = "traffic_anomaly"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    EARLY_STOPPING = "early_stopping"
    SAFETY_VIOLATION = "safety_violation"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

@dataclass
class MonitoringRule:
    """Monitoring rule configuration"""
    rule_id: str
    name: str
    description: str
    condition: AlertCondition
    parameters: Dict[str, Any]
    severity: AlertSeverity = AlertSeverity.MEDIUM
    is_active: bool = True
    cooldown_minutes: int = 30
    auto_resolve: bool = False
    actions: Optional[List[str]] = None

@dataclass
class SafetyCheck:
    """Safety check configuration"""
    check_id: str
    name: str
    description: str
    check_type: str
    parameters: Dict[str, Any]
    is_active: bool = True
    auto_stop_experiment: bool = False
    notification_channels: Optional[List[str]] = None

@dataclass
class ExperimentAlert:
    """Experiment alert"""
    alert_id: str
    experiment_id: str
    variant_id: Optional[str]
    rule_id: str
    condition: AlertCondition
    severity: AlertSeverity
    message: str
    details: Dict[str, Any]
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

@dataclass
class MonitoringSnapshot:
    """Current monitoring state snapshot"""
    experiment_id: str
    timestamp: datetime
    active_alerts: List[ExperimentAlert]
    safety_violations: List[str]
    key_metrics: Dict[str, float]
    traffic_distribution: Dict[str, float]
    health_score: float

class ExperimentMonitor:
    """
    Real-time experiment monitoring system with automated safety controls.
    
    Provides continuous monitoring of A/B testing experiments with
    customizable rules, safety checks, and automated response actions.
    """
    
    def __init__(self):
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        self.safety_checks: Dict[str, SafetyCheck] = {}
        self.active_alerts: Dict[str, ExperimentAlert] = {}
        self.alert_history: List[ExperimentAlert] = []
        self.monitoring_snapshots: Dict[str, List[MonitoringSnapshot]] = defaultdict(list)
        
        # Alert handlers
        self.alert_handlers: Dict[AlertCondition, Callable] = {}
        self.notification_channels: Dict[str, Callable] = {}
        
        # Monitoring state
        self.experiment_states: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Background tasks
        self._monitoring_task = None
        self._cleanup_task = None
        self._is_running = False
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default monitoring rules."""
        # Conversion rate drop rule
        self.monitoring_rules["conversion_rate_drop"] = MonitoringRule(
            rule_id="conversion_rate_drop",
            name="Conversion Rate Drop",
            description="Alert when conversion rate drops significantly",
            condition=AlertCondition.CONVERSION_RATE_DROP,
            parameters={
                "threshold_percentage": 20.0,  # 20% drop
                "minimum_sample_size": 100,
                "comparison_window_hours": 24
            },
            severity=AlertSeverity.HIGH
        )
        
        # Error rate spike rule
        self.monitoring_rules["error_rate_spike"] = MonitoringRule(
            rule_id="error_rate_spike",
            name="Error Rate Spike",
            description="Alert when error rate increases significantly",
            condition=AlertCondition.ERROR_RATE_SPIKE,
            parameters={
                "threshold_percentage": 50.0,  # 50% increase
                "baseline_window_hours": 1,
                "minimum_requests": 50
            },
            severity=AlertSeverity.CRITICAL,
            auto_resolve=True
        )
        
        # Statistical significance rule
        self.monitoring_rules["statistical_significance"] = MonitoringRule(
            rule_id="statistical_significance",
            name="Statistical Significance Reached",
            description="Alert when statistical significance is reached",
            condition=AlertCondition.STATISTICAL_SIGNIFICANCE,
            parameters={
                "confidence_level": 0.95,
                "minimum_effect_size": 0.05
            },
            severity=AlertSeverity.MEDIUM
        )
    
    async def start_monitoring(self):
        """Start the monitoring system."""
        if self._is_running:
            return
        
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_monitoring(self):
        """Stop the monitoring system."""
        self._is_running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def add_monitoring_rule(self, rule: MonitoringRule) -> bool:
        """Add a new monitoring rule."""
        self.monitoring_rules[rule.rule_id] = rule
        return True
    
    async def remove_monitoring_rule(self, rule_id: str) -> bool:
        """Remove a monitoring rule."""
        if rule_id in self.monitoring_rules:
            del self.monitoring_rules[rule_id]
            return True
        return False
    
    async def add_safety_check(self, safety_check: SafetyCheck) -> bool:
        """Add a new safety check."""
        self.safety_checks[safety_check.check_id] = safety_check
        return True
    
    async def update_experiment_metrics(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        metrics: Dict[str, float]
    ) -> List[ExperimentAlert]:
        """Update experiment metrics and check for alerts."""
        metric_key = f"{experiment_id}:{variant_id or 'control'}"
        
        # Store metrics with timestamp
        timestamped_metrics = {
            'timestamp': datetime.utcnow(),
            'metrics': metrics,
            'variant_id': variant_id
        }
        self.metric_history[metric_key].append(timestamped_metrics)
        
        # Check all monitoring rules
        new_alerts = []
        for rule_id, rule in self.monitoring_rules.items():
            if not rule.is_active:
                continue
            
            alert = await self._check_monitoring_rule(
                experiment_id, variant_id, rule, metrics
            )
            if alert:
                new_alerts.append(alert)
        
        # Run safety checks
        safety_violations = await self._run_safety_checks(
            experiment_id, variant_id, metrics
        )
        
        for violation in safety_violations:
            alert = ExperimentAlert(
                alert_id=f"{experiment_id}_{violation}_{int(datetime.utcnow().timestamp())}",
                experiment_id=experiment_id,
                variant_id=variant_id,
                rule_id="safety_check",
                condition=AlertCondition.SAFETY_VIOLATION,
                severity=AlertSeverity.CRITICAL,
                message=f"Safety violation: {violation}",
                details={'violation': violation}
            )
            new_alerts.append(alert)
        
        # Process new alerts
        for alert in new_alerts:
            await self._process_alert(alert)
        
        return new_alerts
    
    async def _check_monitoring_rule(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        rule: MonitoringRule,
        current_metrics: Dict[str, float]
    ) -> Optional[ExperimentAlert]:
        """Check if a monitoring rule is triggered."""
        
        # Check cooldown
        if await self._is_in_cooldown(experiment_id, rule.rule_id):
            return None
        
        if rule.condition == AlertCondition.CONVERSION_RATE_DROP:
            return await self._check_conversion_rate_drop(
                experiment_id, variant_id, rule, current_metrics
            )
        
        elif rule.condition == AlertCondition.ERROR_RATE_SPIKE:
            return await self._check_error_rate_spike(
                experiment_id, variant_id, rule, current_metrics
            )
        
        elif rule.condition == AlertCondition.METRIC_THRESHOLD:
            return await self._check_metric_threshold(
                experiment_id, variant_id, rule, current_metrics
            )
        
        elif rule.condition == AlertCondition.TRAFFIC_ANOMALY:
            return await self._check_traffic_anomaly(
                experiment_id, variant_id, rule, current_metrics
            )
        
        elif rule.condition == AlertCondition.PERFORMANCE_DEGRADATION:
            return await self._check_performance_degradation(
                experiment_id, variant_id, rule, current_metrics
            )
        
        return None
    
    async def _check_conversion_rate_drop(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        rule: MonitoringRule,
        current_metrics: Dict[str, float]
    ) -> Optional[ExperimentAlert]:
        """Check for conversion rate drops."""
        if 'conversion_rate' not in current_metrics:
            return None
        
        current_rate = current_metrics['conversion_rate']
        threshold = rule.parameters.get('threshold_percentage', 20.0)
        min_sample_size = rule.parameters.get('minimum_sample_size', 100)
        
        # Get historical rates
        metric_key = f"{experiment_id}:{variant_id or 'control'}"
        history = list(self.metric_history[metric_key])
        
        if len(history) < 2:
            return None
        
        # Check sample size
        if current_metrics.get('sample_size', 0) < min_sample_size:
            return None
        
        # Calculate baseline (average of previous rates)
        baseline_rates = [
            h['metrics'].get('conversion_rate', 0) 
            for h in history[:-1] 
            if 'conversion_rate' in h['metrics']
        ]
        
        if not baseline_rates:
            return None
        
        baseline_rate = statistics.mean(baseline_rates)
        
        # Check for significant drop
        if baseline_rate > 0:
            drop_percentage = ((baseline_rate - current_rate) / baseline_rate) * 100
            
            if drop_percentage >= threshold:
                return ExperimentAlert(
                    alert_id=f"{experiment_id}_conv_drop_{int(datetime.utcnow().timestamp())}",
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                    rule_id=rule.rule_id,
                    condition=rule.condition,
                    severity=rule.severity,
                    message=f"Conversion rate dropped by {drop_percentage:.1f}%",
                    details={
                        'current_rate': current_rate,
                        'baseline_rate': baseline_rate,
                        'drop_percentage': drop_percentage
                    }
                )
        
        return None
    
    async def _check_error_rate_spike(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        rule: MonitoringRule,
        current_metrics: Dict[str, float]
    ) -> Optional[ExperimentAlert]:
        """Check for error rate spikes."""
        if 'error_rate' not in current_metrics:
            return None
        
        current_rate = current_metrics['error_rate']
        threshold = rule.parameters.get('threshold_percentage', 50.0)
        min_requests = rule.parameters.get('minimum_requests', 50)
        
        # Check minimum requests
        if current_metrics.get('total_requests', 0) < min_requests:
            return None
        
        # Get baseline from recent history
        metric_key = f"{experiment_id}:{variant_id or 'control'}"
        history = list(self.metric_history[metric_key])
        
        if len(history) < 2:
            return None
        
        # Calculate baseline error rate
        baseline_window = rule.parameters.get('baseline_window_hours', 1)
        cutoff_time = datetime.utcnow() - timedelta(hours=baseline_window)
        
        baseline_rates = [
            h['metrics'].get('error_rate', 0)
            for h in history[:-1]
            if h['timestamp'] >= cutoff_time and 'error_rate' in h['metrics']
        ]
        
        if not baseline_rates:
            return None
        
        baseline_rate = statistics.mean(baseline_rates)
        
        # Check for spike
        if baseline_rate > 0:
            increase_percentage = ((current_rate - baseline_rate) / baseline_rate) * 100
            
            if increase_percentage >= threshold:
                return ExperimentAlert(
                    alert_id=f"{experiment_id}_error_spike_{int(datetime.utcnow().timestamp())}",
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                    rule_id=rule.rule_id,
                    condition=rule.condition,
                    severity=rule.severity,
                    message=f"Error rate spiked by {increase_percentage:.1f}%",
                    details={
                        'current_rate': current_rate,
                        'baseline_rate': baseline_rate,
                        'increase_percentage': increase_percentage
                    }
                )
        
        return None
    
    async def _check_metric_threshold(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        rule: MonitoringRule,
        current_metrics: Dict[str, float]
    ) -> Optional[ExperimentAlert]:
        """Check for metric threshold violations."""
        metric_name = rule.parameters.get('metric_name')
        threshold_value = rule.parameters.get('threshold_value')
        comparison = rule.parameters.get('comparison', 'greater_than')  # 'greater_than', 'less_than'
        
        if not metric_name or threshold_value is None:
            return None
        
        if metric_name not in current_metrics:
            return None
        
        current_value = current_metrics[metric_name]
        triggered = False
        
        if comparison == 'greater_than' and current_value > threshold_value:
            triggered = True
        elif comparison == 'less_than' and current_value < threshold_value:
            triggered = True
        elif comparison == 'equals' and abs(current_value - threshold_value) < 1e-10:
            triggered = True
        
        if triggered:
            return ExperimentAlert(
                alert_id=f"{experiment_id}_threshold_{metric_name}_{int(datetime.utcnow().timestamp())}",
                experiment_id=experiment_id,
                variant_id=variant_id,
                rule_id=rule.rule_id,
                condition=rule.condition,
                severity=rule.severity,
                message=f"Metric {metric_name} threshold violated: {current_value} {comparison} {threshold_value}",
                details={
                    'metric_name': metric_name,
                    'current_value': current_value,
                    'threshold_value': threshold_value,
                    'comparison': comparison
                }
            )
        
        return None
    
    async def _check_traffic_anomaly(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        rule: MonitoringRule,
        current_metrics: Dict[str, float]
    ) -> Optional[ExperimentAlert]:
        """Check for traffic distribution anomalies."""
        if 'traffic_percentage' not in current_metrics:
            return None
        
        current_traffic = current_metrics['traffic_percentage']
        expected_traffic = rule.parameters.get('expected_percentage')
        tolerance = rule.parameters.get('tolerance_percentage', 10.0)
        
        if expected_traffic is None:
            return None
        
        deviation = abs(current_traffic - expected_traffic)
        
        if deviation > tolerance:
            return ExperimentAlert(
                alert_id=f"{experiment_id}_traffic_anomaly_{int(datetime.utcnow().timestamp())}",
                experiment_id=experiment_id,
                variant_id=variant_id,
                rule_id=rule.rule_id,
                condition=rule.condition,
                severity=rule.severity,
                message=f"Traffic anomaly: {current_traffic:.1f}% (expected {expected_traffic:.1f}%)",
                details={
                    'current_traffic': current_traffic,
                    'expected_traffic': expected_traffic,
                    'deviation': deviation,
                    'tolerance': tolerance
                }
            )
        
        return None
    
    async def _check_performance_degradation(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        rule: MonitoringRule,
        current_metrics: Dict[str, float]
    ) -> Optional[ExperimentAlert]:
        """Check for performance degradation."""
        performance_metrics = ['response_time', 'latency', 'cpu_usage', 'memory_usage']
        degradation_threshold = rule.parameters.get('degradation_percentage', 20.0)
        
        # Get baseline performance
        metric_key = f"{experiment_id}:{variant_id or 'control'}"
        history = list(self.metric_history[metric_key])
        
        if len(history) < 5:  # Need sufficient history
            return None
        
        degradations = []
        
        for metric in performance_metrics:
            if metric not in current_metrics:
                continue
            
            current_value = current_metrics[metric]
            
            # Calculate baseline (median of recent history)
            baseline_values = [
                h['metrics'].get(metric, 0)
                for h in history[:-1]
                if metric in h['metrics']
            ]
            
            if len(baseline_values) < 3:
                continue
            
            baseline_value = statistics.median(baseline_values)
            
            if baseline_value > 0:
                degradation = ((current_value - baseline_value) / baseline_value) * 100
                
                if degradation >= degradation_threshold:
                    degradations.append({
                        'metric': metric,
                        'current': current_value,
                        'baseline': baseline_value,
                        'degradation': degradation
                    })
        
        if degradations:
            return ExperimentAlert(
                alert_id=f"{experiment_id}_perf_degradation_{int(datetime.utcnow().timestamp())}",
                experiment_id=experiment_id,
                variant_id=variant_id,
                rule_id=rule.rule_id,
                condition=rule.condition,
                severity=rule.severity,
                message=f"Performance degradation detected in {len(degradations)} metrics",
                details={'degradations': degradations}
            )
        
        return None
    
    async def _run_safety_checks(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        metrics: Dict[str, float]
    ) -> List[str]:
        """Run safety checks and return violations."""
        violations = []
        
        for check_id, check in self.safety_checks.items():
            if not check.is_active:
                continue
            
            violation = await self._evaluate_safety_check(
                experiment_id, variant_id, check, metrics
            )
            
            if violation:
                violations.append(violation)
                
                # Auto-stop experiment if configured
                if check.auto_stop_experiment:
                    # This would integrate with the experiment framework
                    # to actually stop the experiment
                    violations.append(f"Auto-stopping experiment due to {violation}")
        
        return violations
    
    async def _evaluate_safety_check(
        self,
        experiment_id: str,
        variant_id: Optional[str],
        check: SafetyCheck,
        metrics: Dict[str, float]
    ) -> Optional[str]:
        """Evaluate a specific safety check."""
        if check.check_type == "max_error_rate":
            max_error_rate = check.parameters.get('max_rate', 0.05)  # 5%
            current_error_rate = metrics.get('error_rate', 0)
            
            if current_error_rate > max_error_rate:
                return f"Error rate {current_error_rate:.2%} exceeds maximum {max_error_rate:.2%}"
        
        elif check.check_type == "min_conversion_rate":
            min_conversion_rate = check.parameters.get('min_rate', 0.01)  # 1%
            current_conversion_rate = metrics.get('conversion_rate', 0)
            
            if current_conversion_rate < min_conversion_rate:
                return f"Conversion rate {current_conversion_rate:.2%} below minimum {min_conversion_rate:.2%}"
        
        elif check.check_type == "max_response_time":
            max_response_time = check.parameters.get('max_time', 5000)  # 5 seconds
            current_response_time = metrics.get('response_time', 0)
            
            if current_response_time > max_response_time:
                return f"Response time {current_response_time}ms exceeds maximum {max_response_time}ms"
        
        return None
    
    async def _process_alert(self, alert: ExperimentAlert):
        """Process and store a new alert."""
        # Store alert
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        # Execute alert actions
        rule = self.monitoring_rules.get(alert.rule_id)
        if rule and rule.actions:
            for action in rule.actions:
                await self._execute_alert_action(alert, action)
        
        # Send notifications
        await self._send_alert_notifications(alert)
    
    async def _execute_alert_action(self, alert: ExperimentAlert, action: str):
        """Execute an alert action."""
        if action == "log":
            # Log the alert (in real implementation, use proper logging)
            print(f"ALERT: {alert.message}")
        
        elif action == "email":
            # Send email notification
            await self._send_email_alert(alert)
        
        elif action == "slack":
            # Send Slack notification
            await self._send_slack_alert(alert)
        
        elif action == "stop_experiment":
            # Stop the experiment
            await self._stop_experiment(alert.experiment_id)
        
        elif action == "reduce_traffic":
            # Reduce traffic to the problematic variant
            await self._reduce_variant_traffic(alert.experiment_id, alert.variant_id)
    
    async def _send_alert_notifications(self, alert: ExperimentAlert):
        """Send alert notifications through configured channels."""
        for channel_name, handler in self.notification_channels.items():
            try:
                await handler(alert)
            except Exception as e:
                print(f"Failed to send notification via {channel_name}: {e}")
    
    async def _is_in_cooldown(self, experiment_id: str, rule_id: str) -> bool:
        """Check if a rule is in cooldown period."""
        rule = self.monitoring_rules.get(rule_id)
        if not rule or rule.cooldown_minutes <= 0:
            return False
        
        # Check recent alerts for this rule
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
        
        recent_alerts = [
            alert for alert in self.alert_history
            if (alert.experiment_id == experiment_id and 
                alert.rule_id == rule_id and
                alert.created_at > cutoff_time)
        ]
        
        return len(recent_alerts) > 0
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            del self.active_alerts[alert_id]
            return True
        return False
    
    async def get_experiment_alerts(
        self,
        experiment_id: str,
        active_only: bool = True
    ) -> List[ExperimentAlert]:
        """Get alerts for an experiment."""
        if active_only:
            return [
                alert for alert in self.active_alerts.values()
                if alert.experiment_id == experiment_id
            ]
        else:
            return [
                alert for alert in self.alert_history
                if alert.experiment_id == experiment_id
            ]
    
    async def get_monitoring_snapshot(self, experiment_id: str) -> MonitoringSnapshot:
        """Get current monitoring state for an experiment."""
        active_alerts = await self.get_experiment_alerts(experiment_id, active_only=True)
        
        # Calculate health score (0-100)
        health_score = 100.0
        for alert in active_alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                health_score -= 30
            elif alert.severity == AlertSeverity.HIGH:
                health_score -= 20
            elif alert.severity == AlertSeverity.MEDIUM:
                health_score -= 10
            elif alert.severity == AlertSeverity.LOW:
                health_score -= 5
        
        health_score = max(0.0, health_score)
        
        # Get safety violations
        safety_violations = [
            alert.details.get('violation', 'Unknown violation')
            for alert in active_alerts
            if alert.condition == AlertCondition.SAFETY_VIOLATION
        ]
        
        # Get key metrics (latest values)
        key_metrics = {}
        traffic_distribution = {}
        
        for metric_key, history in self.metric_history.items():
            if experiment_id in metric_key and history:
                latest = history[-1]
                variant_id = latest.get('variant_id', 'control')
                
                # Extract key metrics
                metrics = latest['metrics']
                for name, value in metrics.items():
                    if name in ['conversion_rate', 'error_rate', 'response_time', 'revenue']:
                        key_metrics[f"{variant_id}_{name}"] = value
                
                # Traffic distribution
                if 'traffic_percentage' in metrics:
                    traffic_distribution[variant_id] = metrics['traffic_percentage']
        
        return MonitoringSnapshot(
            experiment_id=experiment_id,
            timestamp=datetime.utcnow(),
            active_alerts=active_alerts,
            safety_violations=safety_violations,
            key_metrics=key_metrics,
            traffic_distribution=traffic_distribution,
            health_score=health_score
        )
    
    async def register_notification_channel(
        self,
        channel_name: str,
        handler: Callable[[ExperimentAlert], None]
    ) -> bool:
        """Register a notification channel."""
        self.notification_channels[channel_name] = handler
        return True
    
    # Placeholder methods for actions (would be implemented with actual integrations)
    async def _send_email_alert(self, alert: ExperimentAlert):
        """Send email alert notification."""
        pass  # Implementation would integrate with email service
    
    async def _send_slack_alert(self, alert: ExperimentAlert):
        """Send Slack alert notification."""
        pass  # Implementation would integrate with Slack API
    
    async def _stop_experiment(self, experiment_id: str):
        """Stop an experiment."""
        pass  # Implementation would integrate with experiment framework
    
    async def _reduce_variant_traffic(
        self, 
        experiment_id: str, 
        variant_id: Optional[str]
    ):
        """Reduce traffic to a variant."""
        pass  # Implementation would integrate with traffic splitter
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self._is_running:
            try:
                # Auto-resolve alerts if configured
                await self._auto_resolve_alerts()
                
                # Check for duration-based alerts
                await self._check_duration_alerts()
                
                # Update monitoring snapshots
                await self._update_monitoring_snapshots()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _auto_resolve_alerts(self):
        """Automatically resolve alerts that support auto-resolution."""
        for alert_id, alert in list(self.active_alerts.items()):
            rule = self.monitoring_rules.get(alert.rule_id)
            
            if rule and rule.auto_resolve:
                # Check if alert condition no longer applies
                # This would require re-evaluating the condition
                # For now, we'll implement a simple time-based resolution
                if (datetime.utcnow() - alert.created_at).total_seconds() > 300:  # 5 minutes
                    await self.resolve_alert(alert_id)
    
    async def _check_duration_alerts(self):
        """Check for experiment duration-based alerts."""
        # This would integrate with the experiment framework
        # to check experiment durations and create alerts
        pass
    
    async def _update_monitoring_snapshots(self):
        """Update monitoring snapshots for active experiments."""
        # Get list of active experiments from metric history
        active_experiments = set()
        for metric_key in self.metric_history:
            if ':' in metric_key:
                exp_id = metric_key.split(':')[0]
                active_experiments.add(exp_id)
        
        # Update snapshots
        for experiment_id in active_experiments:
            snapshot = await self.get_monitoring_snapshot(experiment_id)
            self.monitoring_snapshots[experiment_id].append(snapshot)
            
            # Keep only recent snapshots (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.monitoring_snapshots[experiment_id] = [
                s for s in self.monitoring_snapshots[experiment_id]
                if s.timestamp > cutoff_time
            ]
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self._is_running:
            try:
                # Clean up old resolved alerts
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                self.alert_history = [
                    alert for alert in self.alert_history
                    if alert.created_at > cutoff_time or alert.status == AlertStatus.ACTIVE
                ]
                
                # Clean up old metric history
                for metric_key in list(self.metric_history.keys()):
                    # Keep only recent metrics (deque handles this automatically)
                    history = self.metric_history[metric_key]
                    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                    
                    # Convert to list, filter, and recreate deque
                    filtered_history = [
                        h for h in history
                        if h['timestamp'] > recent_cutoff
                    ]
                    
                    new_deque = deque(maxlen=1000)
                    new_deque.extend(filtered_history)
                    self.metric_history[metric_key] = new_deque
                
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                print(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)