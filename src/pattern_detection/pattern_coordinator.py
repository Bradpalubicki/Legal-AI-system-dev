"""
Pattern Detection Coordinator

Central coordinator for all pattern detection and analysis components,
orchestrating comprehensive legal case analytics and optimization.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio
import json

from .pattern_analyzer import PatternAnalyzer, PatternType, DetectedPattern
from .activity_tracker import ActivityTracker, ActivityType, ActivityEvent, ActivityMetrics
from .anomaly_detector import AnomalyDetector, AnomalyType, Anomaly
from .trend_analyzer import TrendAnalyzer, TrendType, Trend
from .predictive_engine import PredictiveEngine, PredictionModel, Prediction
from .workflow_analyzer import WorkflowAnalyzer, WorkflowPattern, WorkflowMetrics
from .resource_optimizer import ResourceOptimizer, OptimizationType, OptimizationSuggestion

logger = logging.getLogger(__name__)

class AnalysisScope(Enum):
    REAL_TIME = "real_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"

@dataclass
class AnalysisReport:
    id: Optional[int] = None
    analysis_scope: AnalysisScope = AnalysisScope.DAILY
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime = field(default_factory=datetime.utcnow)
    patterns_detected: List[DetectedPattern] = field(default_factory=list)
    anomalies_found: List[Anomaly] = field(default_factory=list)
    trends_identified: List[Trend] = field(default_factory=list)
    predictions_generated: List[Prediction] = field(default_factory=list)
    workflow_metrics: List[WorkflowMetrics] = field(default_factory=list)
    optimization_suggestions: List[OptimizationSuggestion] = field(default_factory=list)
    activity_summary: Optional[ActivityMetrics] = None
    key_insights: List[str] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    performance_score: float = 0.0
    confidence_level: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

class PatternDetectionCoordinator:
    def __init__(self):
        # Initialize all component analyzers
        self.pattern_analyzer = PatternAnalyzer()
        self.activity_tracker = ActivityTracker()
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.predictive_engine = PredictiveEngine()
        self.workflow_analyzer = WorkflowAnalyzer()
        self.resource_optimizer = ResourceOptimizer()
        
        # Coordination state
        self.analysis_cache: Dict[str, AnalysisReport] = {}
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.configuration = {
            'real_time_monitoring': True,
            'analysis_intervals': {
                AnalysisScope.REAL_TIME: 300,  # 5 minutes
                AnalysisScope.DAILY: 86400,    # 24 hours
                AnalysisScope.WEEKLY: 604800,  # 7 days
                AnalysisScope.MONTHLY: 2592000 # 30 days
            },
            'alert_thresholds': {
                'critical_pattern_count': 5,
                'anomaly_severity_threshold': 0.8,
                'trend_confidence_threshold': 0.7,
                'optimization_impact_threshold': 0.2
            }
        }

    async def run_comprehensive_analysis(
        self,
        scope: AnalysisScope = AnalysisScope.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        case_ids: Optional[List[int]] = None,
        attorney_ids: Optional[List[int]] = None,
        include_predictions: bool = True,
        db: Optional[AsyncSession] = None
    ) -> AnalysisReport:
        """Run comprehensive pattern detection and analysis across all components."""
        try:
            logger.info(f"Starting comprehensive analysis with scope: {scope.value}")
            
            # Set default date range based on scope
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                if scope == AnalysisScope.REAL_TIME:
                    start_date = end_date - timedelta(hours=1)
                elif scope == AnalysisScope.DAILY:
                    start_date = end_date - timedelta(days=1)
                elif scope == AnalysisScope.WEEKLY:
                    start_date = end_date - timedelta(days=7)
                elif scope == AnalysisScope.MONTHLY:
                    start_date = end_date - timedelta(days=30)
                elif scope == AnalysisScope.QUARTERLY:
                    start_date = end_date - timedelta(days=90)
                elif scope == AnalysisScope.ANNUAL:
                    start_date = end_date - timedelta(days=365)
                else:
                    start_date = end_date - timedelta(days=7)  # Default to weekly
            
            # Initialize analysis report
            report = AnalysisReport(
                analysis_scope=scope,
                start_date=start_date,
                end_date=end_date
            )
            
            # Run parallel analysis across all components
            analysis_tasks = []
            
            # Pattern Analysis
            analysis_tasks.append(
                self._analyze_patterns(start_date, end_date, case_ids, attorney_ids, db)
            )
            
            # Activity Analysis
            analysis_tasks.append(
                self._analyze_activities(start_date, end_date, case_ids, attorney_ids, db)
            )
            
            # Anomaly Detection
            analysis_tasks.append(
                self._detect_anomalies(start_date, end_date, case_ids, attorney_ids, db)
            )
            
            # Trend Analysis
            analysis_tasks.append(
                self._analyze_trends(start_date, end_date, case_ids, attorney_ids, db)
            )
            
            # Workflow Analysis
            analysis_tasks.append(
                self._analyze_workflows(start_date, end_date, case_ids, db)
            )
            
            # Resource Optimization
            analysis_tasks.append(
                self._optimize_resources(start_date, end_date, case_ids, db)
            )
            
            # Execute all analyses in parallel
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis task {i} failed: {result}")
                    continue
                
                if i == 0:  # Pattern Analysis
                    report.patterns_detected = result or []
                elif i == 1:  # Activity Analysis
                    report.activity_summary = result
                elif i == 2:  # Anomaly Detection
                    report.anomalies_found = result or []
                elif i == 3:  # Trend Analysis
                    report.trends_identified = result or []
                elif i == 4:  # Workflow Analysis
                    report.workflow_metrics = result or []
                elif i == 5:  # Resource Optimization
                    report.optimization_suggestions = result or []
            
            # Generate predictions if requested
            if include_predictions:
                report.predictions_generated = await self._generate_predictions(
                    start_date, end_date, case_ids, attorney_ids, db
                )
            
            # Generate insights and alerts
            report.key_insights = await self._generate_key_insights(report)
            report.alerts = await self._generate_alerts(report)
            report.recommendations = await self._generate_recommendations(report)
            
            # Calculate overall performance score
            report.performance_score = await self._calculate_performance_score(report)
            report.confidence_level = await self._calculate_confidence_level(report)
            
            # Cache the report
            cache_key = f"{scope.value}_{start_date.date()}_{end_date.date()}"
            self.analysis_cache[cache_key] = report
            
            logger.info(f"Comprehensive analysis completed: {len(report.patterns_detected)} patterns, "
                       f"{len(report.anomalies_found)} anomalies, {len(report.trends_identified)} trends")
            
            return report
            
        except Exception as e:
            logger.error(f"Error running comprehensive analysis: {e}")
            return AnalysisReport(
                analysis_scope=scope,
                start_date=start_date or datetime.utcnow(),
                end_date=end_date or datetime.utcnow()
            )

    async def start_real_time_monitoring(
        self,
        monitoring_interval_seconds: int = 300,  # 5 minutes
        db: Optional[AsyncSession] = None
    ) -> None:
        """Start real-time monitoring of patterns and anomalies."""
        try:
            logger.info("Starting real-time pattern detection monitoring")
            
            # Stop existing monitoring if running
            await self.stop_real_time_monitoring()
            
            # Start monitoring task
            self.active_monitors['real_time'] = asyncio.create_task(
                self._real_time_monitoring_loop(monitoring_interval_seconds, db)
            )
            
        except Exception as e:
            logger.error(f"Error starting real-time monitoring: {e}")

    async def stop_real_time_monitoring(self) -> None:
        """Stop real-time monitoring."""
        try:
            for monitor_name, task in list(self.active_monitors.items()):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.active_monitors[monitor_name]
            
            logger.info("Real-time monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping real-time monitoring: {e}")

    async def get_analysis_dashboard(
        self,
        scope: AnalysisScope = AnalysisScope.WEEKLY,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard data for analysis visualization."""
        try:
            # Get latest analysis report
            latest_report = await self.run_comprehensive_analysis(scope=scope, db=db)
            
            dashboard = {
                'overview': {
                    'analysis_period': {
                        'start_date': latest_report.start_date.isoformat(),
                        'end_date': latest_report.end_date.isoformat(),
                        'scope': latest_report.analysis_scope.value
                    },
                    'summary_metrics': {
                        'patterns_detected': len(latest_report.patterns_detected),
                        'anomalies_found': len(latest_report.anomalies_found),
                        'trends_identified': len(latest_report.trends_identified),
                        'predictions_generated': len(latest_report.predictions_generated),
                        'optimization_suggestions': len(latest_report.optimization_suggestions),
                        'performance_score': latest_report.performance_score,
                        'confidence_level': latest_report.confidence_level
                    },
                    'alerts': latest_report.alerts,
                    'key_insights': latest_report.key_insights[:5],  # Top 5 insights
                    'recommendations': latest_report.recommendations[:5]  # Top 5 recommendations
                },
                'patterns': await self._format_patterns_for_dashboard(latest_report.patterns_detected),
                'anomalies': await self._format_anomalies_for_dashboard(latest_report.anomalies_found),
                'trends': await self._format_trends_for_dashboard(latest_report.trends_identified),
                'predictions': await self._format_predictions_for_dashboard(latest_report.predictions_generated),
                'workflows': await self._format_workflows_for_dashboard(latest_report.workflow_metrics),
                'optimizations': await self._format_optimizations_for_dashboard(latest_report.optimization_suggestions),
                'activity': await self._format_activity_for_dashboard(latest_report.activity_summary)
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating analysis dashboard: {e}")
            return {}

    async def get_alert_summary(
        self,
        alert_level: Optional[AlertLevel] = None,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """Get summary of recent alerts."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            recent_alerts = [
                alert for alert in self.alert_history
                if alert['timestamp'] >= cutoff_time and
                   (not alert_level or alert['level'] == alert_level.value)
            ]
            
            # Group alerts by level
            alerts_by_level = {}
            for level in AlertLevel:
                level_alerts = [a for a in recent_alerts if a['level'] == level.value]
                alerts_by_level[level.value] = {
                    'count': len(level_alerts),
                    'alerts': level_alerts
                }
            
            # Get most recent critical alerts
            critical_alerts = [a for a in recent_alerts if a['level'] in ['critical', 'urgent']]
            critical_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            summary = {
                'lookback_hours': lookback_hours,
                'total_alerts': len(recent_alerts),
                'alerts_by_level': alerts_by_level,
                'recent_critical': critical_alerts[:10],  # Most recent 10 critical alerts
                'alert_rate': len(recent_alerts) / lookback_hours,  # Alerts per hour
                'generated_at': datetime.utcnow()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating alert summary: {e}")
            return {}

    async def export_analysis_report(
        self,
        report: AnalysisReport,
        export_format: str = "json",
        include_raw_data: bool = False
    ) -> Dict[str, Any]:
        """Export analysis report in specified format."""
        try:
            export_data = {
                'report_metadata': {
                    'id': report.id,
                    'scope': report.analysis_scope.value,
                    'start_date': report.start_date.isoformat(),
                    'end_date': report.end_date.isoformat(),
                    'generated_at': report.generated_at.isoformat(),
                    'performance_score': report.performance_score,
                    'confidence_level': report.confidence_level
                },
                'executive_summary': {
                    'key_insights': report.key_insights,
                    'recommendations': report.recommendations,
                    'alerts': report.alerts,
                    'summary_counts': {
                        'patterns': len(report.patterns_detected),
                        'anomalies': len(report.anomalies_found),
                        'trends': len(report.trends_identified),
                        'predictions': len(report.predictions_generated),
                        'optimizations': len(report.optimization_suggestions)
                    }
                }
            }
            
            if include_raw_data:
                export_data['detailed_findings'] = {
                    'patterns': [self._serialize_pattern(p) for p in report.patterns_detected],
                    'anomalies': [self._serialize_anomaly(a) for a in report.anomalies_found],
                    'trends': [self._serialize_trend(t) for t in report.trends_identified],
                    'predictions': [self._serialize_prediction(p) for p in report.predictions_generated],
                    'workflows': [self._serialize_workflow(w) for w in report.workflow_metrics],
                    'optimizations': [self._serialize_optimization(o) for o in report.optimization_suggestions]
                }
                
                if report.activity_summary:
                    export_data['detailed_findings']['activity_summary'] = self._serialize_activity_metrics(report.activity_summary)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting analysis report: {e}")
            return {}

    # Private helper methods
    
    async def _real_time_monitoring_loop(
        self,
        interval_seconds: int,
        db: Optional[AsyncSession]
    ) -> None:
        """Real-time monitoring loop."""
        try:
            while True:
                # Run real-time analysis
                report = await self.run_comprehensive_analysis(
                    scope=AnalysisScope.REAL_TIME,
                    db=db
                )
                
                # Check for critical alerts
                critical_alerts = [
                    alert for alert in report.alerts
                    if alert['level'] in ['critical', 'urgent']
                ]
                
                if critical_alerts:
                    await self._handle_critical_alerts(critical_alerts)
                
                # Add to alert history
                for alert in report.alerts:
                    alert['timestamp'] = datetime.utcnow()
                    self.alert_history.append(alert)
                
                # Cleanup old alerts (keep last 1000)
                if len(self.alert_history) > 1000:
                    self.alert_history = self.alert_history[-1000:]
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
        except asyncio.CancelledError:
            logger.info("Real-time monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in real-time monitoring loop: {e}")

    async def _analyze_patterns(
        self,
        start_date: datetime,
        end_date: datetime,
        case_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: Optional[AsyncSession]
    ) -> List[DetectedPattern]:
        """Analyze patterns using pattern analyzer."""
        try:
            patterns = await self.pattern_analyzer.analyze_patterns(
                case_ids=case_ids,
                attorney_ids=attorney_ids,
                db=db
            )
            return patterns
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return []

    async def _analyze_activities(
        self,
        start_date: datetime,
        end_date: datetime,
        case_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: Optional[AsyncSession]
    ) -> Optional[ActivityMetrics]:
        """Analyze activities using activity tracker."""
        try:
            metrics = await self.activity_tracker.get_activity_metrics(
                start_date=start_date,
                end_date=end_date,
                case_ids=case_ids,
                attorney_ids=attorney_ids,
                db=db
            )
            return metrics
        except Exception as e:
            logger.error(f"Error in activity analysis: {e}")
            return None

    async def _detect_anomalies(
        self,
        start_date: datetime,
        end_date: datetime,
        case_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: Optional[AsyncSession]
    ) -> List[Anomaly]:
        """Detect anomalies using anomaly detector."""
        try:
            # Create a mock data snapshot for anomaly detection
            data_snapshot = {
                'case_activity': 150,  # Mock values
                'attorney_productivity': 0.85,
                'billing_rate': 250.0,
                'deadline_compliance': 0.92,
                'settlement_rate': 0.68
            }
            
            anomalies = await self.anomaly_detector.detect_anomalies(
                data_snapshot=data_snapshot
            )
            return anomalies
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return []

    async def _analyze_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        case_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: Optional[AsyncSession]
    ) -> List[Trend]:
        """Analyze trends using trend analyzer."""
        try:
            trends = await self.trend_analyzer.analyze_trends(
                start_date=start_date,
                end_date=end_date,
                db=db
            )
            return trends
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return []

    async def _analyze_workflows(
        self,
        start_date: datetime,
        end_date: datetime,
        case_ids: Optional[List[int]],
        db: Optional[AsyncSession]
    ) -> List[WorkflowMetrics]:
        """Analyze workflows using workflow analyzer."""
        try:
            # Analyze common workflow types
            workflow_metrics = []
            workflow_types = ['case_intake', 'document_review', 'trial_prep']
            
            for workflow_type in workflow_types:
                metrics = await self.workflow_analyzer.analyze_workflow(
                    workflow_id=workflow_type,
                    case_ids=case_ids,
                    date_range=(start_date, end_date),
                    db=db
                )
                if metrics.total_steps > 0:
                    workflow_metrics.append(metrics)
            
            return workflow_metrics
        except Exception as e:
            logger.error(f"Error in workflow analysis: {e}")
            return []

    async def _optimize_resources(
        self,
        start_date: datetime,
        end_date: datetime,
        case_ids: Optional[List[int]],
        db: Optional[AsyncSession]
    ) -> List[OptimizationSuggestion]:
        """Optimize resources using resource optimizer."""
        try:
            suggestions = await self.resource_optimizer.optimize_resource_allocation(
                optimization_type=OptimizationType.WORKLOAD_BALANCING,
                case_ids=case_ids,
                db=db
            )
            return suggestions
        except Exception as e:
            logger.error(f"Error in resource optimization: {e}")
            return []

    async def _generate_predictions(
        self,
        start_date: datetime,
        end_date: datetime,
        case_ids: Optional[List[int]],
        attorney_ids: Optional[List[int]],
        db: Optional[AsyncSession]
    ) -> List[Prediction]:
        """Generate predictions using predictive engine."""
        try:
            predictions = []
            
            # Generate predictions for different models
            model_types = [PredictionModel.CASE_OUTCOME, PredictionModel.SETTLEMENT_AMOUNT]
            
            for model_type in model_types:
                # Mock input features for prediction
                mock_features = {
                    'case_type': 'personal_injury',
                    'attorney_experience': 10,
                    'case_value': 100000,
                    'complexity_score': 5.5
                }
                
                prediction = await self.predictive_engine.predict(
                    model_type=model_type,
                    input_features=mock_features,
                    target_entity_id=case_ids[0] if case_ids else None
                )
                
                if prediction:
                    predictions.append(prediction)
            
            return predictions
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return []

    async def _generate_key_insights(self, report: AnalysisReport) -> List[str]:
        """Generate key insights from analysis report."""
        insights = []
        
        # Pattern insights
        if report.patterns_detected:
            high_severity_patterns = [p for p in report.patterns_detected if p.severity.value in ['high', 'critical']]
            if high_severity_patterns:
                insights.append(f"Detected {len(high_severity_patterns)} high-severity patterns requiring attention")
        
        # Anomaly insights
        if report.anomalies_found:
            critical_anomalies = [a for a in report.anomalies_found if a.severity > 0.8]
            if critical_anomalies:
                insights.append(f"Found {len(critical_anomalies)} critical anomalies that may indicate operational issues")
        
        # Trend insights
        if report.trends_identified:
            significant_trends = [t for t in report.trends_identified if t.confidence_score > 0.8]
            improving_trends = [t for t in significant_trends if t.direction.value == 'increasing']
            declining_trends = [t for t in significant_trends if t.direction.value == 'decreasing']
            
            if improving_trends:
                insights.append(f"Positive trends identified in {len(improving_trends)} key metrics")
            if declining_trends:
                insights.append(f"Declining performance detected in {len(declining_trends)} areas")
        
        # Optimization insights
        if report.optimization_suggestions:
            high_impact_optimizations = [o for o in report.optimization_suggestions if sum(o.expected_improvement.values()) > 0.5]
            if high_impact_optimizations:
                insights.append(f"{len(high_impact_optimizations)} high-impact optimization opportunities identified")
        
        # Activity insights
        if report.activity_summary:
            if report.activity_summary.error_rate > 0.1:
                insights.append(f"Elevated error rate detected: {report.activity_summary.error_rate:.1%}")
            
            if report.activity_summary.activity_velocity > 0:
                insights.append(f"Current activity velocity: {report.activity_summary.activity_velocity:.1f} activities/hour")
        
        return insights

    async def _generate_alerts(self, report: AnalysisReport) -> List[Dict[str, Any]]:
        """Generate alerts based on analysis findings."""
        alerts = []
        
        # Critical pattern alerts
        critical_patterns = [p for p in report.patterns_detected if p.severity.value == 'critical']
        for pattern in critical_patterns:
            alerts.append({
                'type': 'pattern',
                'level': AlertLevel.CRITICAL.value,
                'title': f"Critical Pattern Detected: {pattern.pattern_type.value}",
                'description': pattern.description,
                'confidence': pattern.confidence,
                'affected_entities': pattern.affected_entities
            })
        
        # Anomaly alerts
        severe_anomalies = [a for a in report.anomalies_found if a.severity > 0.8]
        for anomaly in severe_anomalies:
            alerts.append({
                'type': 'anomaly',
                'level': AlertLevel.WARNING.value if anomaly.severity < 0.9 else AlertLevel.CRITICAL.value,
                'title': f"Anomaly Detected: {anomaly.anomaly_type.value}",
                'description': anomaly.description,
                'severity': anomaly.severity,
                'value': anomaly.anomaly_value
            })
        
        # Trend alerts
        concerning_trends = [t for t in report.trends_identified if t.direction.value == 'decreasing' and t.confidence_score > 0.7]
        for trend in concerning_trends:
            alerts.append({
                'type': 'trend',
                'level': AlertLevel.WARNING.value,
                'title': f"Declining Trend: {trend.trend_type.value}",
                'description': trend.summary,
                'confidence': trend.confidence_score,
                'slope': trend.slope
            })
        
        return alerts

    async def _generate_recommendations(self, report: AnalysisReport) -> List[str]:
        """Generate recommendations based on analysis findings."""
        recommendations = []
        
        # Pattern-based recommendations
        pattern_types = [p.pattern_type for p in report.patterns_detected]
        if PatternType.CASE_LIFECYCLE in pattern_types:
            recommendations.append("Review case lifecycle patterns to identify process improvement opportunities")
        
        # Anomaly-based recommendations
        if report.anomalies_found:
            billing_anomalies = [a for a in report.anomalies_found if 'billing' in a.anomaly_type.value.lower()]
            if billing_anomalies:
                recommendations.append("Investigate billing anomalies to ensure accurate client invoicing")
        
        # Trend-based recommendations
        for trend in report.trends_identified:
            if trend.recommendations:
                recommendations.extend(trend.recommendations[:2])  # Top 2 recommendations per trend
        
        # Optimization recommendations
        for optimization in report.optimization_suggestions[:5]:  # Top 5 optimizations
            if optimization.justification:
                recommendations.append(optimization.justification)
        
        # Remove duplicates and limit
        recommendations = list(dict.fromkeys(recommendations))  # Remove duplicates
        return recommendations[:10]  # Limit to top 10

    async def _calculate_performance_score(self, report: AnalysisReport) -> float:
        """Calculate overall performance score based on analysis results."""
        try:
            score_components = []
            
            # Pattern score (fewer critical patterns = better)
            critical_patterns = len([p for p in report.patterns_detected if p.severity.value == 'critical'])
            pattern_score = max(0, 1 - critical_patterns * 0.2)
            score_components.append(pattern_score)
            
            # Anomaly score (fewer severe anomalies = better)
            severe_anomalies = len([a for a in report.anomalies_found if a.severity > 0.8])
            anomaly_score = max(0, 1 - severe_anomalies * 0.15)
            score_components.append(anomaly_score)
            
            # Trend score (more positive trends = better)
            if report.trends_identified:
                positive_trends = len([t for t in report.trends_identified if t.direction.value == 'increasing'])
                trend_score = min(1, positive_trends / len(report.trends_identified))
            else:
                trend_score = 0.5
            score_components.append(trend_score)
            
            # Activity score
            if report.activity_summary:
                activity_score = 1 - min(1, report.activity_summary.error_rate * 5)
            else:
                activity_score = 0.5
            score_components.append(activity_score)
            
            # Calculate weighted average
            return sum(score_components) / len(score_components)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.5

    async def _calculate_confidence_level(self, report: AnalysisReport) -> float:
        """Calculate overall confidence level of analysis."""
        try:
            confidence_scores = []
            
            # Pattern confidence
            if report.patterns_detected:
                pattern_confidences = [p.confidence for p in report.patterns_detected]
                confidence_scores.extend(pattern_confidences)
            
            # Trend confidence
            if report.trends_identified:
                trend_confidences = [t.confidence_score for t in report.trends_identified]
                confidence_scores.extend(trend_confidences)
            
            # Prediction confidence
            if report.predictions_generated:
                prediction_confidences = [p.confidence_score for p in report.predictions_generated]
                confidence_scores.extend(prediction_confidences)
            
            if confidence_scores:
                return sum(confidence_scores) / len(confidence_scores)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating confidence level: {e}")
            return 0.5

    async def _handle_critical_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Handle critical alerts that require immediate attention."""
        try:
            for alert in alerts:
                logger.critical(f"CRITICAL ALERT: {alert['title']} - {alert.get('description', '')}")
                
                # Here you would typically:
                # - Send notifications to administrators
                # - Trigger automated responses
                # - Create incident tickets
                # - Log to external monitoring systems
                
        except Exception as e:
            logger.error(f"Error handling critical alerts: {e}")

    # Dashboard formatting methods
    
    async def _format_patterns_for_dashboard(self, patterns: List[DetectedPattern]) -> Dict[str, Any]:
        """Format patterns for dashboard display."""
        return {
            'total': len(patterns),
            'by_severity': {
                severity.value: len([p for p in patterns if p.severity == severity])
                for severity in {p.severity for p in patterns}
            },
            'by_type': {
                pattern_type.value: len([p for p in patterns if p.pattern_type == pattern_type])
                for pattern_type in {p.pattern_type for p in patterns}
            },
            'recent': [self._serialize_pattern(p) for p in patterns[:5]]
        }

    async def _format_anomalies_for_dashboard(self, anomalies: List[Anomaly]) -> Dict[str, Any]:
        """Format anomalies for dashboard display."""
        return {
            'total': len(anomalies),
            'severe': len([a for a in anomalies if a.severity > 0.8]),
            'by_type': {
                anomaly_type.value: len([a for a in anomalies if a.anomaly_type == anomaly_type])
                for anomaly_type in {a.anomaly_type for a in anomalies}
            },
            'recent': [self._serialize_anomaly(a) for a in anomalies[:5]]
        }

    async def _format_trends_for_dashboard(self, trends: List[Trend]) -> Dict[str, Any]:
        """Format trends for dashboard display."""
        return {
            'total': len(trends),
            'by_direction': {
                direction.value: len([t for t in trends if t.direction == direction])
                for direction in {t.direction for t in trends}
            },
            'significant': len([t for t in trends if t.confidence_score > 0.7]),
            'recent': [self._serialize_trend(t) for t in trends[:5]]
        }

    async def _format_predictions_for_dashboard(self, predictions: List[Prediction]) -> Dict[str, Any]:
        """Format predictions for dashboard display."""
        return {
            'total': len(predictions),
            'by_model': {
                model.value: len([p for p in predictions if p.model_type == model])
                for model in {p.model_type for p in predictions}
            },
            'high_confidence': len([p for p in predictions if p.confidence_score > 0.8]),
            'recent': [self._serialize_prediction(p) for p in predictions[:5]]
        }

    async def _format_workflows_for_dashboard(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Format workflows for dashboard display."""
        return {
            'total': len(workflows),
            'avg_efficiency': sum([w.parallel_efficiency for w in workflows]) / len(workflows) if workflows else 0,
            'total_optimizations': sum([len(w.optimization_opportunities) for w in workflows]),
            'recent': [self._serialize_workflow(w) for w in workflows[:5]]
        }

    async def _format_optimizations_for_dashboard(self, optimizations: List[OptimizationSuggestion]) -> Dict[str, Any]:
        """Format optimizations for dashboard display."""
        return {
            'total': len(optimizations),
            'by_type': {
                opt_type.value: len([o for o in optimizations if o.optimization_type == opt_type])
                for opt_type in {o.optimization_type for o in optimizations}
            },
            'high_impact': len([o for o in optimizations if sum(o.expected_improvement.values()) > 0.5]),
            'top_suggestions': [self._serialize_optimization(o) for o in optimizations[:5]]
        }

    async def _format_activity_for_dashboard(self, activity: Optional[ActivityMetrics]) -> Dict[str, Any]:
        """Format activity for dashboard display."""
        if not activity:
            return {}
        
        return {
            'total_activities': activity.total_activities,
            'velocity': activity.activity_velocity,
            'error_rate': activity.error_rate,
            'peak_hour': activity.peak_activity_hour,
            'most_active_attorney': activity.most_active_attorney
        }

    # Serialization methods
    
    def _serialize_pattern(self, pattern: DetectedPattern) -> Dict[str, Any]:
        """Serialize pattern for export."""
        return {
            'pattern_type': pattern.pattern_type.value,
            'severity': pattern.severity.value,
            'confidence': pattern.confidence,
            'description': pattern.description,
            'affected_entities': pattern.affected_entities,
            'detected_at': pattern.detected_at.isoformat()
        }

    def _serialize_anomaly(self, anomaly: Anomaly) -> Dict[str, Any]:
        """Serialize anomaly for export."""
        return {
            'anomaly_type': anomaly.anomaly_type.value,
            'severity': anomaly.severity,
            'description': anomaly.description,
            'anomaly_value': anomaly.anomaly_value,
            'expected_value': anomaly.expected_value,
            'detected_at': anomaly.detected_at.isoformat()
        }

    def _serialize_trend(self, trend: Trend) -> Dict[str, Any]:
        """Serialize trend for export."""
        return {
            'trend_type': trend.trend_type.value,
            'direction': trend.direction.value,
            'confidence_score': trend.confidence_score,
            'strength': trend.strength,
            'summary': trend.summary,
            'recommendations': trend.recommendations
        }

    def _serialize_prediction(self, prediction: Prediction) -> Dict[str, Any]:
        """Serialize prediction for export."""
        return {
            'model_type': prediction.model_type.value,
            'predicted_value': prediction.predicted_value,
            'confidence_score': prediction.confidence_score,
            'explanation': prediction.explanation,
            'recommendations': prediction.recommendations
        }

    def _serialize_workflow(self, workflow: WorkflowMetrics) -> Dict[str, Any]:
        """Serialize workflow for export."""
        return {
            'workflow_id': workflow.workflow_id,
            'total_steps': workflow.total_steps,
            'cycle_time': workflow.cycle_time,
            'parallel_efficiency': workflow.parallel_efficiency,
            'optimization_opportunities': workflow.optimization_opportunities
        }

    def _serialize_optimization(self, optimization: OptimizationSuggestion) -> Dict[str, Any]:
        """Serialize optimization for export."""
        return {
            'optimization_type': optimization.optimization_type.value,
            'expected_improvement': optimization.expected_improvement,
            'confidence_score': optimization.confidence_score,
            'cost_impact': optimization.cost_impact,
            'justification': optimization.justification,
            'priority': optimization.priority
        }

    def _serialize_activity_metrics(self, metrics: ActivityMetrics) -> Dict[str, Any]:
        """Serialize activity metrics for export."""
        return {
            'total_activities': metrics.total_activities,
            'activity_velocity': metrics.activity_velocity,
            'error_rate': metrics.error_rate,
            'avg_activities_per_day': metrics.avg_activities_per_day,
            'peak_activity_hour': metrics.peak_activity_hour,
            'most_active_attorney': metrics.most_active_attorney
        }