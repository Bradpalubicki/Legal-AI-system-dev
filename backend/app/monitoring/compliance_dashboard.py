#!/usr/bin/env python3
"""
COMPLIANCE MONITORING DASHBOARD

Real-time compliance monitoring with:
- Legal advice detection accuracy tracking
- Audit system health monitoring
- Security event monitoring
- Performance compliance tracking
- Regulatory compliance reporting
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio
from collections import defaultdict

@dataclass
class ComplianceMetric:
    """Compliance metric data structure"""
    name: str
    current_value: float
    target_value: float
    threshold_warning: float
    threshold_critical: float
    status: str  # 'healthy', 'warning', 'critical'
    last_updated: datetime
    trend: str  # 'improving', 'stable', 'degrading'

class ComplianceDashboard:
    """Production compliance monitoring dashboard"""
    
    def __init__(self):
        self.metrics_history = defaultdict(list)
        self.compliance_targets = self._load_compliance_targets()
        self.dashboard_config = self._load_dashboard_config()
        
        print("[COMPLIANCE] Compliance dashboard initialized")
    
    def _load_compliance_targets(self) -> Dict[str, Dict[str, float]]:
        """Load compliance targets and thresholds"""
        return {
            'advice_detection_accuracy': {
                'target': 95.0,
                'warning_threshold': 90.0,
                'critical_threshold': 85.0
            },
            'audit_system_availability': {
                'target': 99.9,
                'warning_threshold': 99.0,
                'critical_threshold': 95.0
            },
            'response_time_p95': {
                'target': 500.0,  # milliseconds
                'warning_threshold': 1000.0,
                'critical_threshold': 2000.0
            },
            'security_detection_rate': {
                'target': 99.0,
                'warning_threshold': 95.0,
                'critical_threshold': 90.0
            },
            'data_retention_compliance': {
                'target': 100.0,
                'warning_threshold': 98.0,
                'critical_threshold': 95.0
            },
            'encryption_compliance': {
                'target': 100.0,
                'warning_threshold': 99.0,
                'critical_threshold': 95.0
            },
            'backup_success_rate': {
                'target': 100.0,
                'warning_threshold': 98.0,
                'critical_threshold': 90.0
            },
            'disaster_recovery_rto': {
                'target': 15.0,  # minutes
                'warning_threshold': 30.0,
                'critical_threshold': 60.0
            }
        }
    
    def _load_dashboard_config(self) -> Dict[str, Any]:
        """Load dashboard configuration"""
        return {
            'refresh_interval': 30,  # seconds
            'retention_days': 90,
            'alert_channels': ['datadog', 'slack', 'email'],
            'widgets': [
                {
                    'name': 'Legal Advice Detection',
                    'type': 'gauge',
                    'metrics': ['advice_detection_accuracy'],
                    'position': {'row': 1, 'col': 1}
                },
                {
                    'name': 'System Health',
                    'type': 'status_grid',
                    'metrics': ['audit_system_availability', 'security_detection_rate'],
                    'position': {'row': 1, 'col': 2}
                },
                {
                    'name': 'Performance Metrics',
                    'type': 'time_series',
                    'metrics': ['response_time_p95'],
                    'position': {'row': 2, 'col': 1}
                },
                {
                    'name': 'Compliance Overview',
                    'type': 'compliance_score',
                    'metrics': ['data_retention_compliance', 'encryption_compliance'],
                    'position': {'row': 2, 'col': 2}
                }
            ]
        }
    
    def update_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """Update a compliance metric"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Store in history
        self.metrics_history[metric_name].append({
            'value': value,
            'timestamp': timestamp.isoformat()
        })
        
        # Keep only last 1000 points
        if len(self.metrics_history[metric_name]) > 1000:
            self.metrics_history[metric_name] = self.metrics_history[metric_name][-1000:]
        
        # Calculate compliance status
        compliance_metric = self._calculate_compliance_status(metric_name, value)
        
        # Log significant changes
        if compliance_metric.status in ['warning', 'critical']:
            print(f"[COMPLIANCE] {compliance_metric.status.upper()}: {metric_name} = {value} "
                  f"(target: {compliance_metric.target_value})")
    
    def _calculate_compliance_status(self, metric_name: str, current_value: float) -> ComplianceMetric:
        """Calculate compliance status for a metric"""
        targets = self.compliance_targets.get(metric_name, {})
        
        target = targets.get('target', 100.0)
        warning_threshold = targets.get('warning_threshold', 90.0)
        critical_threshold = targets.get('critical_threshold', 80.0)
        
        # Determine status based on thresholds
        if metric_name in ['response_time_p95', 'disaster_recovery_rto']:
            # Lower is better for these metrics
            if current_value <= target:
                status = 'healthy'
            elif current_value <= warning_threshold:
                status = 'warning'
            else:
                status = 'critical'
        else:
            # Higher is better for most metrics
            if current_value >= target:
                status = 'healthy'
            elif current_value >= warning_threshold:
                status = 'warning'
            else:
                status = 'critical'
        
        # Calculate trend
        trend = self._calculate_trend(metric_name)
        
        return ComplianceMetric(
            name=metric_name,
            current_value=current_value,
            target_value=target,
            threshold_warning=warning_threshold,
            threshold_critical=critical_threshold,
            status=status,
            last_updated=datetime.utcnow(),
            trend=trend
        )
    
    def _calculate_trend(self, metric_name: str) -> str:
        """Calculate trend for a metric"""
        history = self.metrics_history.get(metric_name, [])
        if len(history) < 2:
            return 'stable'
        
        # Compare last 5 points with previous 5 points
        recent_points = history[-5:]
        previous_points = history[-10:-5] if len(history) >= 10 else history[:-5]
        
        if not previous_points:
            return 'stable'
        
        recent_avg = sum(p['value'] for p in recent_points) / len(recent_points)
        previous_avg = sum(p['value'] for p in previous_points) / len(previous_points)
        
        difference = recent_avg - previous_avg
        threshold = previous_avg * 0.05  # 5% change threshold
        
        if difference > threshold:
            return 'improving'
        elif difference < -threshold:
            return 'degrading'
        else:
            return 'stable'
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        current_metrics = {}
        
        # Get latest values for all metrics
        for metric_name in self.compliance_targets.keys():
            history = self.metrics_history.get(metric_name, [])
            if history:
                latest_value = history[-1]['value']
                current_metrics[metric_name] = self._calculate_compliance_status(metric_name, latest_value)
        
        # Calculate overall compliance score
        overall_score = self._calculate_overall_compliance_score(current_metrics)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_compliance_score': overall_score,
            'metrics': {name: asdict(metric) for name, metric in current_metrics.items()},
            'dashboard_config': self.dashboard_config,
            'summary': self._generate_summary(current_metrics)
        }
    
    def _calculate_overall_compliance_score(self, metrics: Dict[str, ComplianceMetric]) -> float:
        """Calculate overall compliance score"""
        if not metrics:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        # Weight different metrics by importance
        weights = {
            'advice_detection_accuracy': 3.0,  # Most important
            'audit_system_availability': 2.5,
            'security_detection_rate': 2.5,
            'encryption_compliance': 2.0,
            'data_retention_compliance': 2.0,
            'response_time_p95': 1.5,
            'backup_success_rate': 1.5,
            'disaster_recovery_rto': 1.0
        }
        
        for name, metric in metrics.items():
            weight = weights.get(name, 1.0)
            
            # Calculate metric score as percentage of target
            if name in ['response_time_p95', 'disaster_recovery_rto']:
                # Lower is better - calculate inverse score
                if metric.current_value <= metric.target_value:
                    metric_score = 100.0
                else:
                    metric_score = max(0.0, 100.0 * (metric.target_value / metric.current_value))
            else:
                # Higher is better
                metric_score = min(100.0, 100.0 * (metric.current_value / metric.target_value))
            
            total_score += metric_score * weight
            total_weight += weight
        
        return round(total_score / total_weight, 1) if total_weight > 0 else 0.0
    
    def _generate_summary(self, metrics: Dict[str, ComplianceMetric]) -> Dict[str, Any]:
        """Generate compliance summary"""
        status_counts = defaultdict(int)
        trend_counts = defaultdict(int)
        
        for metric in metrics.values():
            status_counts[metric.status] += 1
            trend_counts[metric.trend] += 1
        
        return {
            'total_metrics': len(metrics),
            'healthy_metrics': status_counts['healthy'],
            'warning_metrics': status_counts['warning'],
            'critical_metrics': status_counts['critical'],
            'improving_trends': trend_counts['improving'],
            'stable_trends': trend_counts['stable'],
            'degrading_trends': trend_counts['degrading'],
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def generate_compliance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate compliance report for specified period"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        report_data = {
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days
            },
            'metrics_summary': {},
            'sla_compliance': {},
            'incidents': [],
            'recommendations': []
        }
        
        # Analyze each metric over the period
        for metric_name in self.compliance_targets.keys():
            history = self.metrics_history.get(metric_name, [])
            period_data = [
                h for h in history 
                if start_time <= datetime.fromisoformat(h['timestamp']) <= end_time
            ]
            
            if period_data:
                values = [h['value'] for h in period_data]
                report_data['metrics_summary'][metric_name] = {
                    'average': round(sum(values) / len(values), 2),
                    'minimum': min(values),
                    'maximum': max(values),
                    'data_points': len(values),
                    'target_achievement': self._calculate_target_achievement(metric_name, values)
                }
        
        return report_data
    
    def _calculate_target_achievement(self, metric_name: str, values: List[float]) -> float:
        """Calculate percentage of time target was achieved"""
        target = self.compliance_targets[metric_name]['target']
        
        if metric_name in ['response_time_p95', 'disaster_recovery_rto']:
            # Lower is better
            achieved = sum(1 for v in values if v <= target)
        else:
            # Higher is better
            achieved = sum(1 for v in values if v >= target)
        
        return round(100.0 * achieved / len(values), 1) if values else 0.0

# Global dashboard instance
compliance_dashboard = ComplianceDashboard()