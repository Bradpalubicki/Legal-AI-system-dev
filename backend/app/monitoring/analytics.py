# =============================================================================
# Legal AI System - Performance Analytics and Trend Analysis
# =============================================================================
# Advanced analytics engine for performance data with trend analysis,
# anomaly detection, forecasting, and actionable insights
# =============================================================================

from typing import Optional, Dict, Any, List, Tuple, Set, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path
import asyncio
import logging
import json
import uuid
import statistics
import math
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc, func, text
from sqlalchemy.sql import extract

from .models import (
    MetricDefinition, MetricSample, AggregatedMetric, PerformanceInsight,
    MetricType, MetricCategory
)
from ..audit.service import AuditLoggingService, AuditEventCreate
from ..audit.models import AuditEventType, AuditSeverity, AuditStatus
# Simplified - no config needed

logger = logging.getLogger(__name__)

# =============================================================================
# ANALYTICS ENUMS AND MODELS
# =============================================================================

class TrendDirection(Enum):
    """Trend direction classification."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"

class AnomalyType(Enum):
    """Anomaly classification types."""
    SPIKE = "spike"
    DIP = "dip"
    FLATLINE = "flatline"
    OSCILLATION = "oscillation"
    DRIFT = "drift"

class InsightType(Enum):
    """Performance insight types."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    EFFICIENCY_OPPORTUNITY = "efficiency_opportunity"
    CAPACITY_PLANNING = "capacity_planning"
    COMPLIANCE_RISK = "compliance_risk"
    COST_OPTIMIZATION = "cost_optimization"

@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric_name: str
    direction: TrendDirection
    slope: float
    r_squared: float
    confidence: float
    time_period: str
    data_points: int
    trend_strength: str  # weak, moderate, strong
    seasonal_component: Optional[Dict[str, Any]] = None
    
@dataclass
class AnomalyDetectionResult:
    """Anomaly detection result."""
    metric_name: str
    timestamp: datetime
    value: float
    expected_value: float
    anomaly_score: float
    anomaly_type: AnomalyType
    confidence: float
    context: Dict[str, Any]

@dataclass
class PerformancePattern:
    """Performance pattern identification."""
    pattern_id: str
    pattern_type: str
    metrics_involved: List[str]
    pattern_strength: float
    frequency: str  # hourly, daily, weekly
    business_impact: str
    recommendations: List[str]

@dataclass
class CapacityForecast:
    """Capacity forecasting result."""
    metric_name: str
    current_value: float
    forecast_horizon_days: int
    predicted_values: List[Tuple[datetime, float]]
    capacity_threshold: float
    days_to_capacity: Optional[int]
    confidence_intervals: List[Tuple[float, float]]
    forecast_accuracy: float

# =============================================================================
# TIME SERIES ANALYSIS ENGINE
# =============================================================================

class TimeSeriesAnalyzer:
    """Advanced time series analysis for metrics."""
    
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
    
    def analyze_trend(self, timestamps: List[datetime], values: List[float], metric_name: str) -> TrendAnalysis:
        """Analyze trend in time series data."""
        if len(values) < 3:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.STABLE,
                slope=0.0,
                r_squared=0.0,
                confidence=0.0,
                time_period="insufficient_data",
                data_points=len(values),
                trend_strength="none"
            )
        
        # Convert timestamps to numeric values (hours since first timestamp)
        start_time = timestamps[0]
        x_values = [(ts - start_time).total_seconds() / 3600 for ts in timestamps]
        
        # Perform linear regression
        X = np.array(x_values).reshape(-1, 1)
        y = np.array(values)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate metrics
        slope = model.coef_[0]
        r_squared = model.score(X, y)
        
        # Determine trend direction
        if abs(slope) < 0.001:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Check for volatility
        residuals = y - model.predict(X)
        volatility = np.std(residuals)
        mean_value = np.mean(values)
        cv = volatility / mean_value if mean_value != 0 else 0
        
        if cv > 0.3:  # High coefficient of variation
            direction = TrendDirection.VOLATILE
        
        # Determine trend strength
        if r_squared < 0.3:
            trend_strength = "weak"
        elif r_squared < 0.7:
            trend_strength = "moderate"
        else:
            trend_strength = "strong"
        
        # Calculate confidence based on R-squared and data points
        confidence = min(r_squared * (len(values) / 100), 1.0)
        
        # Analyze seasonal patterns if enough data
        seasonal_component = None
        if len(values) >= 24:  # At least 24 hours of hourly data
            seasonal_component = self._analyze_seasonality(timestamps, values)
            if seasonal_component and seasonal_component.get('seasonal_strength', 0) > 0.3:
                direction = TrendDirection.SEASONAL
        
        time_period = f"{(timestamps[-1] - timestamps[0]).total_seconds() / 3600:.1f}h"
        
        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            slope=slope,
            r_squared=r_squared,
            confidence=confidence,
            time_period=time_period,
            data_points=len(values),
            trend_strength=trend_strength,
            seasonal_component=seasonal_component
        )
    
    def _analyze_seasonality(self, timestamps: List[datetime], values: List[float]) -> Dict[str, Any]:
        """Analyze seasonal patterns in the data."""
        try:
            df = pd.DataFrame({
                'timestamp': timestamps,
                'value': values
            })
            df.set_index('timestamp', inplace=True)
            
            # Extract time components
            df['hour'] = df.index.hour
            df['day_of_week'] = df.index.dayofweek
            
            # Calculate hourly patterns
            hourly_pattern = df.groupby('hour')['value'].agg(['mean', 'std']).to_dict()
            
            # Calculate daily patterns
            daily_pattern = df.groupby('day_of_week')['value'].agg(['mean', 'std']).to_dict()
            
            # Calculate seasonal strength (variation between hours/days)
            overall_mean = df['value'].mean()
            hourly_variation = df.groupby('hour')['value'].mean().std()
            seasonal_strength = (hourly_variation / overall_mean) if overall_mean != 0 else 0
            
            return {
                'hourly_pattern': hourly_pattern,
                'daily_pattern': daily_pattern,
                'seasonal_strength': seasonal_strength,
                'peak_hour': df.groupby('hour')['value'].mean().idxmax(),
                'low_hour': df.groupby('hour')['value'].mean().idxmin()
            }
            
        except Exception as e:
            logger.error(f"Seasonality analysis failed: {e}")
            return {}
    
    def detect_anomalies(self, timestamps: List[datetime], values: List[float], metric_name: str) -> List[AnomalyDetectionResult]:
        """Detect anomalies in time series data."""
        if len(values) < 10:
            return []
        
        anomalies = []
        
        try:
            # Prepare data
            X = np.array(values).reshape(-1, 1)
            X_scaled = self.scaler.fit_transform(X)
            
            # Detect anomalies using Isolation Forest
            outliers = self.anomaly_detector.fit_predict(X_scaled)
            anomaly_scores = self.anomaly_detector.decision_function(X_scaled)
            
            # Also use statistical methods
            mean_val = np.mean(values)
            std_val = np.std(values)
            z_scores = [(val - mean_val) / std_val for val in values]
            
            for i, (timestamp, value) in enumerate(zip(timestamps, values)):
                is_anomaly = False
                anomaly_type = None
                confidence = 0.0
                expected_value = mean_val
                
                # Isolation Forest detection
                if outliers[i] == -1:
                    is_anomaly = True
                    confidence = min(abs(anomaly_scores[i]) / 0.5, 1.0)
                
                # Z-score detection (3-sigma rule)
                if abs(z_scores[i]) > 3:
                    is_anomaly = True
                    confidence = max(confidence, min(abs(z_scores[i]) / 3, 1.0))
                
                if is_anomaly:
                    # Determine anomaly type
                    if value > mean_val + 2 * std_val:
                        anomaly_type = AnomalyType.SPIKE
                    elif value < mean_val - 2 * std_val:
                        anomaly_type = AnomalyType.DIP
                    elif std_val < 0.01 * mean_val:  # Very low variance
                        anomaly_type = AnomalyType.FLATLINE
                    else:
                        anomaly_type = AnomalyType.SPIKE if value > mean_val else AnomalyType.DIP
                    
                    # Calculate expected value based on trend
                    if i > 0:
                        if i < len(values) - 1:
                            expected_value = (values[i-1] + values[i+1]) / 2
                        else:
                            expected_value = values[i-1]
                    
                    anomalies.append(AnomalyDetectionResult(
                        metric_name=metric_name,
                        timestamp=timestamp,
                        value=value,
                        expected_value=expected_value,
                        anomaly_score=abs(anomaly_scores[i]) if i < len(anomaly_scores) else abs(z_scores[i]),
                        anomaly_type=anomaly_type,
                        confidence=confidence,
                        context={
                            'z_score': z_scores[i],
                            'isolation_score': anomaly_scores[i] if i < len(anomaly_scores) else 0,
                            'mean_value': mean_val,
                            'std_dev': std_val
                        }
                    ))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

# =============================================================================
# PERFORMANCE PATTERN DETECTOR
# =============================================================================

class PerformancePatternDetector:
    """Detects performance patterns and correlations."""
    
    def __init__(self):
        pass
    
    async def detect_patterns(
        self,
        db: AsyncSession,
        metrics_data: Dict[str, List[Tuple[datetime, float]]],
        analysis_window_hours: int = 24
    ) -> List[PerformancePattern]:
        """Detect performance patterns across metrics."""
        patterns = []
        
        try:
            # Pattern 1: Resource exhaustion pattern
            resource_pattern = await self._detect_resource_exhaustion_pattern(metrics_data)
            if resource_pattern:
                patterns.append(resource_pattern)
            
            # Pattern 2: AI processing bottleneck
            ai_pattern = await self._detect_ai_processing_pattern(metrics_data)
            if ai_pattern:
                patterns.append(ai_pattern)
            
            # Pattern 3: Database performance degradation
            db_pattern = await self._detect_database_pattern(metrics_data)
            if db_pattern:
                patterns.append(db_pattern)
            
            # Pattern 4: Legal compliance risk pattern
            compliance_pattern = await self._detect_compliance_pattern(db, metrics_data)
            if compliance_pattern:
                patterns.append(compliance_pattern)
                
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
        
        return patterns
    
    async def _detect_resource_exhaustion_pattern(
        self,
        metrics_data: Dict[str, List[Tuple[datetime, float]]]
    ) -> Optional[PerformancePattern]:
        """Detect resource exhaustion patterns."""
        resource_metrics = [
            'system_cpu_usage_percent',
            'system_memory_used_percent', 
            'system_disk_used_percent'
        ]
        
        available_metrics = [m for m in resource_metrics if m in metrics_data]
        if len(available_metrics) < 2:
            return None
        
        # Check if multiple resource metrics are trending upward
        high_usage_count = 0
        trend_strength_sum = 0
        
        for metric_name in available_metrics:
            data = metrics_data[metric_name]
            if not data:
                continue
                
            timestamps, values = zip(*data)
            recent_values = values[-10:]  # Last 10 data points
            
            if len(recent_values) > 5:
                avg_recent = sum(recent_values) / len(recent_values)
                if avg_recent > 80:  # High usage threshold
                    high_usage_count += 1
                    # Calculate trend strength
                    if len(values) > 10:
                        early_values = values[:10]
                        avg_early = sum(early_values) / len(early_values)
                        trend_strength = (avg_recent - avg_early) / avg_early if avg_early > 0 else 0
                        trend_strength_sum += max(trend_strength, 0)
        
        if high_usage_count >= 2 and trend_strength_sum > 0.1:
            return PerformancePattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="resource_exhaustion",
                metrics_involved=available_metrics,
                pattern_strength=min(trend_strength_sum, 1.0),
                frequency="ongoing",
                business_impact="high",
                recommendations=[
                    "Consider scaling up system resources",
                    "Review resource-intensive processes",
                    "Implement resource monitoring alerts",
                    "Evaluate load balancing configuration"
                ]
            )
        
        return None
    
    async def _detect_ai_processing_pattern(
        self,
        metrics_data: Dict[str, List[Tuple[datetime, float]]]
    ) -> Optional[PerformancePattern]:
        """Detect AI processing performance patterns."""
        ai_metrics = [
            'ai_request_duration_seconds',
            'ai_token_usage_total',
            'ai_api_rate_limit_errors_total'
        ]
        
        available_metrics = [m for m in ai_metrics if m in metrics_data]
        if len(available_metrics) < 1:
            return None
        
        # Analyze AI request duration trends
        duration_metric = 'ai_request_duration_seconds'
        if duration_metric in metrics_data:
            data = metrics_data[duration_metric]
            if data:
                timestamps, values = zip(*data)
                
                # Check for increasing response times
                if len(values) > 20:
                    recent_avg = sum(values[-10:]) / 10
                    earlier_avg = sum(values[:10]) / 10
                    
                    if recent_avg > earlier_avg * 1.5:  # 50% increase
                        return PerformancePattern(
                            pattern_id=str(uuid.uuid4()),
                            pattern_type="ai_processing_degradation",
                            metrics_involved=[duration_metric],
                            pattern_strength=min((recent_avg - earlier_avg) / earlier_avg, 1.0),
                            frequency="trending",
                            business_impact="medium",
                            recommendations=[
                                "Review AI model performance",
                                "Check API rate limits and quotas",
                                "Consider optimizing prompt sizes",
                                "Implement caching for common requests",
                                "Monitor token usage efficiency"
                            ]
                        )
        
        return None
    
    async def _detect_database_pattern(
        self,
        metrics_data: Dict[str, List[Tuple[datetime, float]]]
    ) -> Optional[PerformancePattern]:
        """Detect database performance patterns."""
        db_metrics = [
            'database_connection_pool_active',
            'http_request_duration_seconds'
        ]
        
        # Look for correlation between database connections and response time
        if all(m in metrics_data for m in db_metrics):
            conn_data = metrics_data['database_connection_pool_active']
            response_data = metrics_data['http_request_duration_seconds']
            
            if conn_data and response_data and len(conn_data) > 10 and len(response_data) > 10:
                # Simple correlation check
                conn_values = [v for _, v in conn_data[-20:]]
                response_values = [v for _, v in response_data[-20:]]
                
                if len(conn_values) == len(response_values):
                    correlation = np.corrcoef(conn_values, response_values)[0, 1]
                    
                    if correlation > 0.7:  # Strong positive correlation
                        return PerformancePattern(
                            pattern_id=str(uuid.uuid4()),
                            pattern_type="database_bottleneck",
                            metrics_involved=db_metrics,
                            pattern_strength=correlation,
                            frequency="ongoing",
                            business_impact="high",
                            recommendations=[
                                "Optimize database queries",
                                "Review database connection pooling",
                                "Consider database performance tuning",
                                "Implement query caching",
                                "Monitor slow query logs"
                            ]
                        )
        
        return None
    
    async def _detect_compliance_pattern(
        self,
        db: AsyncSession,
        metrics_data: Dict[str, List[Tuple[datetime, float]]]
    ) -> Optional[PerformancePattern]:
        """Detect compliance risk patterns."""
        compliance_metrics = [
            'compliance_violations_detected',
            'audit_events_generated'
        ]
        
        # Check for increasing compliance violations
        if 'compliance_violations_detected' in metrics_data:
            data = metrics_data['compliance_violations_detected']
            if data and len(data) > 10:
                timestamps, values = zip(*data)
                
                # Check trend in violations
                recent_violations = sum(values[-7:])  # Last 7 data points
                earlier_violations = sum(values[:7])   # First 7 data points
                
                if recent_violations > earlier_violations * 1.5 and recent_violations > 0:
                    return PerformancePattern(
                        pattern_id=str(uuid.uuid4()),
                        pattern_type="compliance_risk_increase",
                        metrics_involved=['compliance_violations_detected'],
                        pattern_strength=min((recent_violations - earlier_violations) / max(earlier_violations, 1), 1.0),
                        frequency="increasing",
                        business_impact="critical",
                        recommendations=[
                            "Review compliance monitoring rules",
                            "Audit recent system changes",
                            "Increase compliance training",
                            "Review data handling procedures",
                            "Consult with legal compliance team"
                        ]
                    )
        
        return None

# =============================================================================
# CAPACITY FORECASTING ENGINE
# =============================================================================

class CapacityForecastingEngine:
    """Forecasts capacity requirements and resource needs."""
    
    def __init__(self):
        pass
    
    def forecast_capacity(
        self,
        timestamps: List[datetime],
        values: List[float],
        metric_name: str,
        forecast_days: int = 30,
        capacity_threshold: float = 80.0
    ) -> CapacityForecast:
        """Forecast capacity requirements."""
        if len(values) < 10:
            return CapacityForecast(
                metric_name=metric_name,
                current_value=values[-1] if values else 0,
                forecast_horizon_days=forecast_days,
                predicted_values=[],
                capacity_threshold=capacity_threshold,
                days_to_capacity=None,
                confidence_intervals=[],
                forecast_accuracy=0.0
            )
        
        try:
            # Prepare data for forecasting
            current_value = values[-1]
            
            # Simple linear trend forecasting
            x_hours = [(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]
            X = np.array(x_hours).reshape(-1, 1)
            y = np.array(values)
            
            # Fit linear regression model
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate future predictions
            last_hour = x_hours[-1]
            future_hours = np.arange(last_hour + 1, last_hour + 1 + (forecast_days * 24))
            future_X = future_hours.reshape(-1, 1)
            predictions = model.predict(future_X)
            
            # Create prediction timestamps
            predicted_values = []
            for i, pred in enumerate(predictions):
                future_time = timestamps[-1] + timedelta(hours=i+1)
                predicted_values.append((future_time, max(pred, 0)))  # Ensure non-negative
            
            # Calculate confidence intervals (simple approach using residuals)
            residuals = y - model.predict(X)
            residual_std = np.std(residuals)
            confidence_intervals = [
                (max(pred - 2 * residual_std, 0), pred + 2 * residual_std)
                for _, pred in predicted_values
            ]
            
            # Calculate days to capacity
            days_to_capacity = None
            for i, (future_time, pred_value) in enumerate(predicted_values):
                if pred_value >= capacity_threshold:
                    days_to_capacity = i // 24  # Convert hours to days
                    break
            
            # Calculate forecast accuracy based on R-squared
            forecast_accuracy = max(model.score(X, y), 0.0)
            
            return CapacityForecast(
                metric_name=metric_name,
                current_value=current_value,
                forecast_horizon_days=forecast_days,
                predicted_values=predicted_values,
                capacity_threshold=capacity_threshold,
                days_to_capacity=days_to_capacity,
                confidence_intervals=confidence_intervals,
                forecast_accuracy=forecast_accuracy
            )
            
        except Exception as e:
            logger.error(f"Capacity forecasting failed: {e}")
            return CapacityForecast(
                metric_name=metric_name,
                current_value=values[-1] if values else 0,
                forecast_horizon_days=forecast_days,
                predicted_values=[],
                capacity_threshold=capacity_threshold,
                days_to_capacity=None,
                confidence_intervals=[],
                forecast_accuracy=0.0
            )

# =============================================================================
# MAIN ANALYTICS SERVICE
# =============================================================================

class PerformanceAnalyticsService:
    """Main performance analytics service."""
    
    def __init__(self):
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.pattern_detector = PerformancePatternDetector()
        self.forecasting_engine = CapacityForecastingEngine()
        self.audit_service = AuditLoggingService()
        
    async def start_analytics_service(self, db: AsyncSession):
        """Start performance analytics service."""
        logger.info("Starting performance analytics service")
        
        # Start analytics tasks
        tasks = [
            asyncio.create_task(self._run_trend_analysis_loop(db)),
            asyncio.create_task(self._run_anomaly_detection_loop(db)),
            asyncio.create_task(self._run_pattern_detection_loop(db)),
            asyncio.create_task(self._run_capacity_forecasting_loop(db)),
            asyncio.create_task(self._generate_insights_loop(db))
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Analytics service error: {e}")
            # Restart after delay
            await asyncio.sleep(300)
            await self.start_analytics_service(db)
    
    async def _run_trend_analysis_loop(self, db: AsyncSession):
        """Run trend analysis periodically."""
        while True:
            try:
                logger.info("Running trend analysis")
                
                # Get metrics for trend analysis
                metrics_data = await self._get_recent_metrics_data(db, hours=24)
                
                for metric_name, data in metrics_data.items():
                    if len(data) >= 10:  # Need sufficient data
                        timestamps, values = zip(*data)
                        
                        # Analyze trend
                        trend_analysis = self.time_series_analyzer.analyze_trend(
                            list(timestamps), list(values), metric_name
                        )
                        
                        # Store significant trends as insights
                        if trend_analysis.confidence > 0.5:
                            await self._create_trend_insight(db, trend_analysis)
                
                # Wait 4 hours before next analysis
                await asyncio.sleep(14400)
                
            except Exception as e:
                logger.error(f"Trend analysis loop failed: {e}")
                await asyncio.sleep(3600)
    
    async def _run_anomaly_detection_loop(self, db: AsyncSession):
        """Run anomaly detection periodically."""
        while True:
            try:
                logger.info("Running anomaly detection")
                
                # Get recent metrics data
                metrics_data = await self._get_recent_metrics_data(db, hours=4)
                
                for metric_name, data in metrics_data.items():
                    if len(data) >= 20:  # Need sufficient data
                        timestamps, values = zip(*data)
                        
                        # Detect anomalies
                        anomalies = self.time_series_analyzer.detect_anomalies(
                            list(timestamps), list(values), metric_name
                        )
                        
                        # Store significant anomalies as insights
                        for anomaly in anomalies:
                            if anomaly.confidence > 0.7:
                                await self._create_anomaly_insight(db, anomaly)
                
                # Wait 1 hour before next detection
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Anomaly detection loop failed: {e}")
                await asyncio.sleep(1800)
    
    async def _run_pattern_detection_loop(self, db: AsyncSession):
        """Run pattern detection periodically."""
        while True:
            try:
                logger.info("Running pattern detection")
                
                # Get metrics data for pattern analysis
                metrics_data = await self._get_recent_metrics_data(db, hours=24)
                
                # Detect patterns
                patterns = await self.pattern_detector.detect_patterns(db, metrics_data)
                
                # Store patterns as insights
                for pattern in patterns:
                    await self._create_pattern_insight(db, pattern)
                
                # Wait 6 hours before next detection
                await asyncio.sleep(21600)
                
            except Exception as e:
                logger.error(f"Pattern detection loop failed: {e}")
                await asyncio.sleep(3600)
    
    async def _run_capacity_forecasting_loop(self, db: AsyncSession):
        """Run capacity forecasting periodically."""
        while True:
            try:
                logger.info("Running capacity forecasting")
                
                # Metrics to forecast
                capacity_metrics = [
                    'system_cpu_usage_percent',
                    'system_memory_used_percent',
                    'system_disk_used_percent',
                    'database_connection_pool_active'
                ]
                
                metrics_data = await self._get_recent_metrics_data(db, hours=168)  # 1 week
                
                for metric_name in capacity_metrics:
                    if metric_name in metrics_data and len(metrics_data[metric_name]) >= 50:
                        data = metrics_data[metric_name]
                        timestamps, values = zip(*data)
                        
                        # Generate forecast
                        forecast = self.forecasting_engine.forecast_capacity(
                            list(timestamps), list(values), metric_name
                        )
                        
                        # Create insight if capacity issues predicted
                        if forecast.days_to_capacity and forecast.days_to_capacity <= 30:
                            await self._create_capacity_insight(db, forecast)
                
                # Wait 24 hours before next forecast
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Capacity forecasting loop failed: {e}")
                await asyncio.sleep(7200)
    
    async def _run_insights_loop(self, db: AsyncSession):
        """Generate performance insights periodically."""
        while True:
            try:
                # Clean up old insights
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                delete_query = text("""
                    DELETE FROM performance_insights 
                    WHERE status = 'resolved' AND resolved_at < :cutoff_date
                """)
                await db.execute(delete_query, {"cutoff_date": cutoff_date})
                await db.commit()
                
                # Wait 24 hours
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Insights loop failed: {e}")
                await asyncio.sleep(3600)
    
    async def _get_recent_metrics_data(
        self,
        db: AsyncSession,
        hours: int = 24
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """Get recent metrics data for analysis."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Get aggregated metrics (using 5-minute windows for efficiency)
        result = await db.execute(
            select(AggregatedMetric, MetricDefinition.name)
            .join(MetricDefinition)
            .where(and_(
                AggregatedMetric.window_start >= start_time,
                AggregatedMetric.window_size_seconds == 300,  # 5-minute windows
                MetricDefinition.enabled == True
            ))
            .order_by(AggregatedMetric.window_start)
        )
        
        metrics_data = {}
        for agg_metric, metric_name in result.fetchall():
            if metric_name not in metrics_data:
                metrics_data[metric_name] = []
            
            # Use average value for trend analysis
            value = float(agg_metric.avg_value) if agg_metric.avg_value else 0.0
            metrics_data[metric_name].append((agg_metric.window_start, value))
        
        return metrics_data
    
    async def _create_trend_insight(self, db: AsyncSession, trend: TrendAnalysis):
        """Create performance insight from trend analysis."""
        try:
            # Determine insight severity
            severity = "info"
            if trend.direction == TrendDirection.INCREASING and "usage" in trend.metric_name:
                severity = "warning" if trend.confidence > 0.7 else "info"
            elif trend.direction == TrendDirection.VOLATILE:
                severity = "warning"
            
            insight = PerformanceInsight(
                title=f"Performance Trend: {trend.metric_name}",
                description=f"{trend.metric_name} shows {trend.direction.value} trend over {trend.time_period}",
                insight_type=InsightType.PERFORMANCE_DEGRADATION.value if trend.direction == TrendDirection.INCREASING else "trend_analysis",
                category=MetricCategory.SYSTEM.value,
                severity=severity,
                affected_services=[trend.metric_name],
                affected_metrics=[trend.metric_name],
                impact_assessment={
                    "trend_direction": trend.direction.value,
                    "trend_strength": trend.trend_strength,
                    "confidence": trend.confidence,
                    "r_squared": trend.r_squared
                },
                recommendations=[
                    f"Monitor {trend.metric_name} closely",
                    f"Review processes affecting {trend.metric_name}",
                    "Consider capacity planning if trend continues"
                ],
                detection_method="statistical_analysis",
                confidence_score=trend.confidence
            )
            
            db.add(insight)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create trend insight: {e}")
    
    async def _create_anomaly_insight(self, db: AsyncSession, anomaly: AnomalyDetectionResult):
        """Create performance insight from anomaly detection."""
        try:
            insight = PerformanceInsight(
                title=f"Anomaly Detected: {anomaly.metric_name}",
                description=f"Anomalous {anomaly.anomaly_type.value} detected in {anomaly.metric_name}",
                insight_type="anomaly",
                category=MetricCategory.SYSTEM.value,
                severity="warning" if anomaly.confidence > 0.8 else "info",
                affected_services=[anomaly.metric_name],
                affected_metrics=[anomaly.metric_name],
                impact_assessment={
                    "anomaly_type": anomaly.anomaly_type.value,
                    "anomaly_score": anomaly.anomaly_score,
                    "expected_value": anomaly.expected_value,
                    "actual_value": anomaly.value,
                    "deviation": abs(anomaly.value - anomaly.expected_value)
                },
                recommendations=[
                    f"Investigate cause of {anomaly.anomaly_type.value} in {anomaly.metric_name}",
                    "Review system logs around anomaly time",
                    "Check for related system events"
                ],
                detection_method="anomaly_detection",
                confidence_score=anomaly.confidence,
                detection_data=anomaly.context
            )
            
            db.add(insight)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create anomaly insight: {e}")
    
    async def _create_pattern_insight(self, db: AsyncSession, pattern: PerformancePattern):
        """Create performance insight from pattern detection."""
        try:
            insight = PerformanceInsight(
                title=f"Performance Pattern: {pattern.pattern_type}",
                description=f"Detected {pattern.pattern_type} pattern affecting {len(pattern.metrics_involved)} metrics",
                insight_type=pattern.pattern_type,
                category=MetricCategory.SYSTEM.value,
                severity="warning" if pattern.business_impact == "high" else "info",
                affected_services=pattern.metrics_involved,
                affected_metrics=pattern.metrics_involved,
                impact_assessment={
                    "pattern_strength": pattern.pattern_strength,
                    "frequency": pattern.frequency,
                    "business_impact": pattern.business_impact
                },
                recommendations=pattern.recommendations,
                detection_method="pattern_analysis",
                confidence_score=pattern.pattern_strength
            )
            
            db.add(insight)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create pattern insight: {e}")
    
    async def _create_capacity_insight(self, db: AsyncSession, forecast: CapacityForecast):
        """Create performance insight from capacity forecast."""
        try:
            insight = PerformanceInsight(
                title=f"Capacity Planning: {forecast.metric_name}",
                description=f"{forecast.metric_name} predicted to reach capacity in {forecast.days_to_capacity} days",
                insight_type=InsightType.CAPACITY_PLANNING.value,
                category=MetricCategory.SYSTEM.value,
                severity="warning" if forecast.days_to_capacity <= 7 else "info",
                affected_services=[forecast.metric_name],
                affected_metrics=[forecast.metric_name],
                impact_assessment={
                    "current_value": forecast.current_value,
                    "capacity_threshold": forecast.capacity_threshold,
                    "days_to_capacity": forecast.days_to_capacity,
                    "forecast_accuracy": forecast.forecast_accuracy
                },
                recommendations=[
                    f"Plan capacity expansion for {forecast.metric_name}",
                    "Review resource utilization patterns",
                    "Consider optimization opportunities",
                    "Schedule capacity review meeting"
                ],
                detection_method="capacity_forecasting",
                confidence_score=forecast.forecast_accuracy
            )
            
            db.add(insight)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create capacity insight: {e}")

# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

performance_analytics_service = PerformanceAnalyticsService()
time_series_analyzer = TimeSeriesAnalyzer()
performance_pattern_detector = PerformancePatternDetector()
capacity_forecasting_engine = CapacityForecastingEngine()