"""
Trend Analyzer Module

Advanced trend analysis system for identifying patterns and trends
in legal case data, attorney performance, and system usage.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging
import numpy as np
from scipy import stats
from scipy.signal import find_peaks
import pandas as pd
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

class TrendType(Enum):
    CASE_VOLUME = "case_volume"
    CASE_DURATION = "case_duration"
    SETTLEMENT_RATES = "settlement_rates"
    SETTLEMENT_AMOUNTS = "settlement_amounts"
    ATTORNEY_PRODUCTIVITY = "attorney_productivity"
    BILLING_PATTERNS = "billing_patterns"
    DOCUMENT_ACTIVITY = "document_activity"
    CLIENT_SATISFACTION = "client_satisfaction"
    DEADLINE_COMPLIANCE = "deadline_compliance"
    COURT_OUTCOMES = "court_outcomes"
    RESEARCH_EFFICIENCY = "research_efficiency"
    TIME_TO_RESOLUTION = "time_to_resolution"
    COST_PER_CASE = "cost_per_case"
    REVENUE_TRENDS = "revenue_trends"
    WORKLOAD_DISTRIBUTION = "workload_distribution"
    SEASONAL_PATTERNS = "seasonal_patterns"
    PRACTICE_AREA_GROWTH = "practice_area_growth"
    CLIENT_ACQUISITION = "client_acquisition"
    SYSTEM_USAGE = "system_usage"
    ERROR_RATES = "error_rates"

class TrendDirection(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    CYCLICAL = "cyclical"
    SEASONAL = "seasonal"

@dataclass
class Trend:
    id: Optional[int] = None
    trend_type: TrendType = TrendType.CASE_VOLUME
    direction: TrendDirection = TrendDirection.STABLE
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime = field(default_factory=datetime.utcnow)
    duration_days: int = 0
    confidence_score: float = 0.0
    strength: float = 0.0  # How strong the trend is (0-1)
    slope: float = 0.0  # Rate of change
    r_squared: float = 0.0  # Goodness of fit
    p_value: float = 1.0  # Statistical significance
    data_points: int = 0
    summary: str = ""
    detailed_analysis: Dict[str, Any] = field(default_factory=dict)
    seasonality_detected: bool = False
    cyclical_period: Optional[int] = None  # Days
    outliers: List[Dict[str, Any]] = field(default_factory=list)
    forecast: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)
    affected_entities: Dict[str, List[int]] = field(default_factory=dict)  # cases, attorneys, clients
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

class TrendAnalyzer:
    def __init__(self):
        self.trend_cache: Dict[str, List[Trend]] = {}
        self.analysis_config = {
            'min_data_points': 10,
            'confidence_threshold': 0.7,
            'significance_threshold': 0.05,
            'seasonal_period_days': [7, 30, 90, 365],  # Weekly, monthly, quarterly, yearly
            'forecast_periods': 30,  # Days to forecast
            'outlier_threshold': 2.0  # Standard deviations
        }

    async def analyze_trends(
        self,
        trend_types: Optional[List[TrendType]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_filters: Optional[Dict[str, List[int]]] = None,
        db: Optional[AsyncSession] = None
    ) -> List[Trend]:
        """Perform comprehensive trend analysis."""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)
            
            if not trend_types:
                trend_types = list(TrendType)
            
            trends = []
            
            for trend_type in trend_types:
                trend_data = await self._get_trend_data(
                    trend_type, start_date, end_date, entity_filters, db
                )
                
                if len(trend_data) >= self.analysis_config['min_data_points']:
                    trend = await self._analyze_single_trend(
                        trend_type, trend_data, start_date, end_date
                    )
                    if trend:
                        trends.append(trend)
            
            # Cache results
            cache_key = f"{start_date.date()}_{end_date.date()}"
            self.trend_cache[cache_key] = trends
            
            logger.info(f"Analyzed {len(trends)} trends from {start_date.date()} to {end_date.date()}")
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return []

    async def detect_seasonal_patterns(
        self,
        trend_type: TrendType,
        lookback_months: int = 24,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Detect seasonal patterns in trend data."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_months * 30)
            
            trend_data = await self._get_trend_data(trend_type, start_date, end_date, None, db)
            
            if len(trend_data) < 50:  # Need sufficient data for seasonal analysis
                return {}
            
            # Convert to pandas for analysis
            df = pd.DataFrame(trend_data)
            df['date'] = pd.to_datetime(df['timestamp'])
            df.set_index('date', inplace=True)
            
            seasonal_patterns = {}
            
            # Weekly seasonality
            df['weekday'] = df.index.dayofweek
            weekly_pattern = df.groupby('weekday')['value'].agg(['mean', 'std', 'count'])
            seasonal_patterns['weekly'] = {
                'pattern': weekly_pattern.to_dict(),
                'strength': self._calculate_seasonality_strength(weekly_pattern['mean'].values),
                'peak_day': weekly_pattern['mean'].idxmax(),
                'low_day': weekly_pattern['mean'].idxmin()
            }
            
            # Monthly seasonality
            df['month'] = df.index.month
            monthly_pattern = df.groupby('month')['value'].agg(['mean', 'std', 'count'])
            seasonal_patterns['monthly'] = {
                'pattern': monthly_pattern.to_dict(),
                'strength': self._calculate_seasonality_strength(monthly_pattern['mean'].values),
                'peak_month': monthly_pattern['mean'].idxmax(),
                'low_month': monthly_pattern['mean'].idxmin()
            }
            
            # Quarterly seasonality
            df['quarter'] = df.index.quarter
            quarterly_pattern = df.groupby('quarter')['value'].agg(['mean', 'std', 'count'])
            seasonal_patterns['quarterly'] = {
                'pattern': quarterly_pattern.to_dict(),
                'strength': self._calculate_seasonality_strength(quarterly_pattern['mean'].values),
                'peak_quarter': quarterly_pattern['mean'].idxmax(),
                'low_quarter': quarterly_pattern['mean'].idxmin()
            }
            
            # Detect cyclical patterns using FFT
            seasonal_patterns['cyclical'] = await self._detect_cyclical_patterns(df['value'].values)
            
            return seasonal_patterns
            
        except Exception as e:
            logger.error(f"Error detecting seasonal patterns: {e}")
            return {}

    async def forecast_trend(
        self,
        trend_type: TrendType,
        forecast_days: int = 30,
        confidence_interval: float = 0.95,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Generate trend forecast using multiple methods."""
        try:
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=180)  # 6 months of history
            
            trend_data = await self._get_trend_data(trend_type, start_date, end_date, None, db)
            
            if len(trend_data) < 30:
                return {'error': 'Insufficient data for forecasting'}
            
            # Convert to numpy arrays
            timestamps = np.array([d['timestamp'] for d in trend_data])
            values = np.array([d['value'] for d in trend_data])
            
            # Normalize timestamps to days from start
            time_days = np.array([(t - timestamps[0]).total_seconds() / 86400 for t in timestamps])
            
            forecast_results = {}
            
            # Linear trend forecast
            linear_forecast = await self._linear_trend_forecast(
                time_days, values, forecast_days, confidence_interval
            )
            forecast_results['linear'] = linear_forecast
            
            # Moving average forecast
            ma_forecast = await self._moving_average_forecast(
                values, forecast_days, window_size=7
            )
            forecast_results['moving_average'] = ma_forecast
            
            # Exponential smoothing forecast
            exp_forecast = await self._exponential_smoothing_forecast(
                values, forecast_days, alpha=0.3
            )
            forecast_results['exponential_smoothing'] = exp_forecast
            
            # Seasonal decomposition forecast (if seasonal patterns detected)
            seasonal_patterns = await self.detect_seasonal_patterns(trend_type, 12, db)
            if seasonal_patterns and any(p['strength'] > 0.3 for p in seasonal_patterns.values()):
                seasonal_forecast = await self._seasonal_forecast(
                    values, forecast_days, seasonal_patterns
                )
                forecast_results['seasonal'] = seasonal_forecast
            
            # Ensemble forecast (average of all methods)
            ensemble_forecast = await self._ensemble_forecast(forecast_results)
            forecast_results['ensemble'] = ensemble_forecast
            
            # Add metadata
            forecast_results['metadata'] = {
                'forecast_days': forecast_days,
                'historical_days': len(trend_data),
                'confidence_interval': confidence_interval,
                'generated_at': datetime.utcnow(),
                'trend_type': trend_type.value
            }
            
            return forecast_results
            
        except Exception as e:
            logger.error(f"Error forecasting trend: {e}")
            return {'error': str(e)}

    async def compare_trends(
        self,
        trend_comparisons: List[Tuple[TrendType, Dict[str, Any]]],
        comparison_period_days: int = 90
    ) -> Dict[str, Any]:
        """Compare multiple trends across different dimensions."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=comparison_period_days)
            
            comparison_results = {
                'trends': {},
                'correlations': {},
                'divergences': {},
                'rankings': {},
                'summary': {}
            }
            
            # Analyze each trend
            all_trend_data = {}
            for trend_type, filters in trend_comparisons:
                trend_data = await self._get_trend_data(trend_type, start_date, end_date, filters, None)
                trend = await self._analyze_single_trend(trend_type, trend_data, start_date, end_date)
                
                if trend:
                    comparison_results['trends'][trend_type.value] = {
                        'direction': trend.direction.value,
                        'strength': trend.strength,
                        'confidence': trend.confidence_score,
                        'slope': trend.slope,
                        'r_squared': trend.r_squared
                    }
                    all_trend_data[trend_type.value] = np.array([d['value'] for d in trend_data])
            
            # Calculate correlations
            trend_names = list(all_trend_data.keys())
            for i, trend1 in enumerate(trend_names):
                for j, trend2 in enumerate(trend_names[i+1:], i+1):
                    if len(all_trend_data[trend1]) == len(all_trend_data[trend2]):
                        correlation = np.corrcoef(
                            all_trend_data[trend1], 
                            all_trend_data[trend2]
                        )[0, 1]
                        comparison_results['correlations'][f"{trend1}_vs_{trend2}"] = correlation
            
            # Rank trends by various metrics
            if comparison_results['trends']:
                comparison_results['rankings'] = {
                    'strongest_growth': sorted(
                        comparison_results['trends'].items(),
                        key=lambda x: x[1]['slope'] if x[1]['direction'] == 'increasing' else -x[1]['slope'],
                        reverse=True
                    )[:3],
                    'most_stable': sorted(
                        comparison_results['trends'].items(),
                        key=lambda x: abs(x[1]['slope']),
                        reverse=False
                    )[:3],
                    'highest_confidence': sorted(
                        comparison_results['trends'].items(),
                        key=lambda x: x[1]['confidence'],
                        reverse=True
                    )[:3]
                }
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error comparing trends: {e}")
            return {}

    async def identify_trend_anomalies(
        self,
        trend: Trend,
        anomaly_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Identify anomalous data points in trend data."""
        try:
            if not trend.detailed_analysis.get('raw_data'):
                return []
            
            values = np.array([d['value'] for d in trend.detailed_analysis['raw_data']])
            timestamps = [d['timestamp'] for d in trend.detailed_analysis['raw_data']]
            
            # Calculate moving statistics
            window_size = min(7, len(values) // 3)
            if window_size < 3:
                return []
            
            # Rolling mean and standard deviation
            rolling_mean = pd.Series(values).rolling(window=window_size, center=True).mean()
            rolling_std = pd.Series(values).rolling(window=window_size, center=True).std()
            
            anomalies = []
            for i, (value, mean, std) in enumerate(zip(values, rolling_mean, rolling_std)):
                if pd.isna(mean) or pd.isna(std) or std == 0:
                    continue
                
                z_score = abs((value - mean) / std)
                if z_score > anomaly_threshold:
                    anomalies.append({
                        'timestamp': timestamps[i],
                        'value': value,
                        'expected_value': mean,
                        'z_score': z_score,
                        'deviation': value - mean,
                        'severity': 'high' if z_score > 3 else 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error identifying trend anomalies: {e}")
            return []

    async def _get_trend_data(
        self,
        trend_type: TrendType,
        start_date: datetime,
        end_date: datetime,
        entity_filters: Optional[Dict[str, List[int]]],
        db: Optional[AsyncSession]
    ) -> List[Dict[str, Any]]:
        """Get raw data for trend analysis."""
        try:
            # This is a mock implementation - in practice, you would query your database
            # based on the trend_type and return time-series data
            
            # Generate mock data for demonstration
            data_points = []
            current_date = start_date
            base_value = 100
            
            while current_date <= end_date:
                # Add some realistic variation based on trend type
                if trend_type == TrendType.CASE_VOLUME:
                    # Weekly cycle with growth trend
                    week_cycle = np.sin(2 * np.pi * current_date.weekday() / 7) * 10
                    growth_trend = (current_date - start_date).days * 0.1
                    noise = np.random.normal(0, 5)
                    value = base_value + week_cycle + growth_trend + noise
                    
                elif trend_type == TrendType.SETTLEMENT_AMOUNTS:
                    # More volatile with monthly cycles
                    month_cycle = np.sin(2 * np.pi * current_date.day / 30) * 20
                    trend = (current_date - start_date).days * 0.05
                    noise = np.random.normal(0, 15)
                    value = base_value + month_cycle + trend + noise
                    
                else:
                    # Generic pattern
                    seasonal = np.sin(2 * np.pi * (current_date - start_date).days / 365) * 15
                    trend = (current_date - start_date).days * 0.02
                    noise = np.random.normal(0, 8)
                    value = base_value + seasonal + trend + noise
                
                data_points.append({
                    'timestamp': current_date,
                    'value': max(0, value),  # Ensure non-negative values
                    'entity_id': None
                })
                
                current_date += timedelta(days=1)
            
            return data_points
            
        except Exception as e:
            logger.error(f"Error getting trend data: {e}")
            return []

    async def _analyze_single_trend(
        self,
        trend_type: TrendType,
        trend_data: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Trend]:
        """Analyze a single trend from raw data."""
        try:
            if len(trend_data) < self.analysis_config['min_data_points']:
                return None
            
            # Extract values and timestamps
            values = np.array([d['value'] for d in trend_data])
            timestamps = np.array([d['timestamp'] for d in trend_data])
            
            # Convert timestamps to numeric (days from start)
            time_numeric = np.array([(t - timestamps[0]).total_seconds() / 86400 for t in timestamps])
            
            # Linear regression for trend analysis
            slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, values)
            
            # Determine trend direction
            direction = TrendDirection.STABLE
            if abs(slope) > 0.1 and p_value < self.analysis_config['significance_threshold']:
                if slope > 0:
                    direction = TrendDirection.INCREASING
                else:
                    direction = TrendDirection.DECREASING
            elif np.std(values) > np.mean(values) * 0.3:
                direction = TrendDirection.VOLATILE
            
            # Calculate trend strength
            strength = min(abs(r_value), 1.0)
            
            # Calculate confidence score
            confidence_score = (1 - p_value) * strength
            
            # Detect seasonality
            seasonality_detected = False
            cyclical_period = None
            
            if len(values) > 20:
                # Simple seasonality detection using autocorrelation
                for period in self.analysis_config['seasonal_period_days']:
                    if period < len(values):
                        autocorr = np.corrcoef(values[:-period], values[period:])[0, 1]
                        if not np.isnan(autocorr) and autocorr > 0.5:
                            seasonality_detected = True
                            cyclical_period = period
                            break
            
            # Identify outliers
            outliers = await self._identify_outliers(values, timestamps)
            
            # Generate summary
            summary = f"{trend_type.value.replace('_', ' ').title()}: "
            if direction == TrendDirection.INCREASING:
                summary += f"Increasing trend (slope: {slope:.3f})"
            elif direction == TrendDirection.DECREASING:
                summary += f"Decreasing trend (slope: {slope:.3f})"
            elif direction == TrendDirection.VOLATILE:
                summary += "High volatility detected"
            else:
                summary += "Stable pattern"
            
            summary += f" with {confidence_score:.1%} confidence"
            
            # Generate recommendations
            recommendations = await self._generate_trend_recommendations(
                trend_type, direction, strength, confidence_score
            )
            
            # Create trend object
            trend = Trend(
                trend_type=trend_type,
                direction=direction,
                start_date=start_date,
                end_date=end_date,
                duration_days=(end_date - start_date).days,
                confidence_score=confidence_score,
                strength=strength,
                slope=slope,
                r_squared=r_value ** 2,
                p_value=p_value,
                data_points=len(trend_data),
                summary=summary,
                detailed_analysis={
                    'raw_data': trend_data,
                    'intercept': intercept,
                    'std_error': std_err,
                    'mean_value': np.mean(values),
                    'std_value': np.std(values),
                    'min_value': np.min(values),
                    'max_value': np.max(values),
                    'value_range': np.max(values) - np.min(values)
                },
                seasonality_detected=seasonality_detected,
                cyclical_period=cyclical_period,
                outliers=outliers,
                recommendations=recommendations
            )
            
            return trend
            
        except Exception as e:
            logger.error(f"Error analyzing single trend: {e}")
            return None

    def _calculate_seasonality_strength(self, values: np.ndarray) -> float:
        """Calculate the strength of seasonal patterns."""
        if len(values) < 2:
            return 0.0
        
        mean_val = np.mean(values)
        if mean_val == 0:
            return 0.0
        
        # Coefficient of variation as a measure of seasonality strength
        cv = np.std(values) / mean_val
        return min(cv, 1.0)

    async def _detect_cyclical_patterns(self, values: np.ndarray) -> Dict[str, Any]:
        """Detect cyclical patterns using frequency analysis."""
        try:
            if len(values) < 20:
                return {}
            
            # Remove trend
            detrended = stats.detrend(values)
            
            # Find peaks in the detrended data
            peaks, properties = find_peaks(
                detrended, 
                height=np.std(detrended) * 0.5,
                distance=3
            )
            
            # Calculate average period between peaks
            if len(peaks) > 2:
                peak_distances = np.diff(peaks)
                avg_period = np.mean(peak_distances)
                period_std = np.std(peak_distances)
                
                return {
                    'detected': True,
                    'avg_period': float(avg_period),
                    'period_std': float(period_std),
                    'num_cycles': len(peaks) - 1,
                    'regularity': 1.0 - (period_std / avg_period) if avg_period > 0 else 0.0
                }
            
            return {'detected': False}
            
        except Exception as e:
            logger.error(f"Error detecting cyclical patterns: {e}")
            return {'detected': False, 'error': str(e)}

    async def _identify_outliers(
        self, 
        values: np.ndarray, 
        timestamps: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Identify outliers in the data."""
        try:
            outliers = []
            
            # Z-score method
            z_scores = np.abs(stats.zscore(values))
            outlier_indices = np.where(z_scores > self.analysis_config['outlier_threshold'])[0]
            
            for idx in outlier_indices:
                outliers.append({
                    'timestamp': timestamps[idx],
                    'value': values[idx],
                    'z_score': z_scores[idx],
                    'method': 'z_score'
                })
            
            return outliers
            
        except Exception as e:
            logger.error(f"Error identifying outliers: {e}")
            return []

    async def _generate_trend_recommendations(
        self,
        trend_type: TrendType,
        direction: TrendDirection,
        strength: float,
        confidence: float
    ) -> List[str]:
        """Generate actionable recommendations based on trend analysis."""
        recommendations = []
        
        if confidence < 0.5:
            recommendations.append("Collect more data to improve trend confidence")
        
        if trend_type == TrendType.CASE_VOLUME:
            if direction == TrendDirection.INCREASING and strength > 0.7:
                recommendations.append("Consider hiring additional attorneys or staff")
                recommendations.append("Review resource allocation and capacity planning")
            elif direction == TrendDirection.DECREASING:
                recommendations.append("Investigate causes of declining case volume")
                recommendations.append("Consider marketing or business development initiatives")
        
        elif trend_type == TrendType.SETTLEMENT_AMOUNTS:
            if direction == TrendDirection.DECREASING:
                recommendations.append("Review negotiation strategies and tactics")
                recommendations.append("Analyze case quality and selection criteria")
            elif direction == TrendDirection.INCREASING:
                recommendations.append("Document successful settlement strategies")
                recommendations.append("Consider expanding similar case types")
        
        elif trend_type == TrendType.ATTORNEY_PRODUCTIVITY:
            if direction == TrendDirection.DECREASING:
                recommendations.append("Provide additional training or support")
                recommendations.append("Review workload distribution and balance")
            elif strength > 0.8 and direction == TrendDirection.VOLATILE:
                recommendations.append("Investigate causes of productivity fluctuations")
        
        return recommendations

    async def _linear_trend_forecast(
        self,
        time_days: np.ndarray,
        values: np.ndarray,
        forecast_days: int,
        confidence_interval: float
    ) -> Dict[str, Any]:
        """Generate linear trend forecast."""
        try:
            # Fit linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(time_days, values)
            
            # Generate forecast points
            last_day = time_days[-1]
            forecast_time = np.arange(last_day + 1, last_day + 1 + forecast_days)
            forecast_values = slope * forecast_time + intercept
            
            # Calculate confidence intervals
            confidence_width = stats.t.ppf((1 + confidence_interval) / 2, len(values) - 2) * std_err
            upper_bound = forecast_values + confidence_width * np.sqrt(1 + 1/len(values))
            lower_bound = forecast_values - confidence_width * np.sqrt(1 + 1/len(values))
            
            return {
                'method': 'linear_trend',
                'forecast_values': forecast_values.tolist(),
                'upper_bound': upper_bound.tolist(),
                'lower_bound': lower_bound.tolist(),
                'r_squared': r_value ** 2,
                'p_value': p_value
            }
            
        except Exception as e:
            logger.error(f"Error in linear trend forecast: {e}")
            return {}

    async def _moving_average_forecast(
        self,
        values: np.ndarray,
        forecast_days: int,
        window_size: int
    ) -> Dict[str, Any]:
        """Generate moving average forecast."""
        try:
            if len(values) < window_size:
                window_size = len(values)
            
            # Calculate moving average
            ma_value = np.mean(values[-window_size:])
            
            # Simple forecast: extend the last moving average
            forecast_values = np.full(forecast_days, ma_value)
            
            # Estimate uncertainty based on recent volatility
            recent_std = np.std(values[-window_size:])
            upper_bound = forecast_values + 1.96 * recent_std
            lower_bound = forecast_values - 1.96 * recent_std
            
            return {
                'method': 'moving_average',
                'forecast_values': forecast_values.tolist(),
                'upper_bound': upper_bound.tolist(),
                'lower_bound': lower_bound.tolist(),
                'window_size': window_size,
                'moving_average': ma_value
            }
            
        except Exception as e:
            logger.error(f"Error in moving average forecast: {e}")
            return {}

    async def _exponential_smoothing_forecast(
        self,
        values: np.ndarray,
        forecast_days: int,
        alpha: float
    ) -> Dict[str, Any]:
        """Generate exponential smoothing forecast."""
        try:
            # Initialize with first value
            smoothed = [values[0]]
            
            # Calculate exponentially smoothed values
            for i in range(1, len(values)):
                smoothed_value = alpha * values[i] + (1 - alpha) * smoothed[-1]
                smoothed.append(smoothed_value)
            
            # Forecast: extend the last smoothed value
            last_smoothed = smoothed[-1]
            forecast_values = np.full(forecast_days, last_smoothed)
            
            # Estimate uncertainty
            residuals = values - np.array(smoothed)
            residual_std = np.std(residuals)
            
            upper_bound = forecast_values + 1.96 * residual_std
            lower_bound = forecast_values - 1.96 * residual_std
            
            return {
                'method': 'exponential_smoothing',
                'forecast_values': forecast_values.tolist(),
                'upper_bound': upper_bound.tolist(),
                'lower_bound': lower_bound.tolist(),
                'alpha': alpha,
                'last_smoothed': last_smoothed
            }
            
        except Exception as e:
            logger.error(f"Error in exponential smoothing forecast: {e}")
            return {}

    async def _seasonal_forecast(
        self,
        values: np.ndarray,
        forecast_days: int,
        seasonal_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate seasonal forecast."""
        try:
            # Use weekly pattern as primary seasonal component
            weekly_pattern = seasonal_patterns.get('weekly', {}).get('pattern', {})
            
            if not weekly_pattern:
                return {}
            
            # Get mean values for each day of week
            weekly_means = weekly_pattern.get('mean', {})
            if not weekly_means:
                return {}
            
            # Generate forecast based on day of week pattern
            forecast_values = []
            base_date = datetime.utcnow()
            
            for i in range(forecast_days):
                forecast_date = base_date + timedelta(days=i)
                weekday = forecast_date.weekday()
                
                if weekday in weekly_means:
                    seasonal_value = weekly_means[weekday]
                else:
                    seasonal_value = np.mean(list(weekly_means.values()))
                
                forecast_values.append(seasonal_value)
            
            # Add trend component
            if len(values) > 7:
                recent_trend = np.mean(values[-7:]) - np.mean(values[-14:-7])
                for i in range(len(forecast_values)):
                    forecast_values[i] += recent_trend * (i + 1) / 7
            
            forecast_values = np.array(forecast_values)
            
            # Estimate uncertainty
            seasonal_std = np.mean([
                weekly_pattern.get('std', {}).get(str(day), np.std(values))
                for day in range(7)
            ])
            
            upper_bound = forecast_values + 1.96 * seasonal_std
            lower_bound = forecast_values - 1.96 * seasonal_std
            
            return {
                'method': 'seasonal',
                'forecast_values': forecast_values.tolist(),
                'upper_bound': upper_bound.tolist(),
                'lower_bound': lower_bound.tolist(),
                'seasonal_strength': seasonal_patterns.get('weekly', {}).get('strength', 0)
            }
            
        except Exception as e:
            logger.error(f"Error in seasonal forecast: {e}")
            return {}

    async def _ensemble_forecast(self, forecast_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ensemble forecast by averaging multiple methods."""
        try:
            available_forecasts = [
                result for result in forecast_results.values()
                if isinstance(result, dict) and 'forecast_values' in result
            ]
            
            if not available_forecasts:
                return {}
            
            # Average the forecasts
            forecast_arrays = [np.array(f['forecast_values']) for f in available_forecasts]
            ensemble_forecast = np.mean(forecast_arrays, axis=0)
            
            # Calculate ensemble bounds (average of bounds)
            upper_bounds = []
            lower_bounds = []
            
            for forecast in available_forecasts:
                if 'upper_bound' in forecast and 'lower_bound' in forecast:
                    upper_bounds.append(np.array(forecast['upper_bound']))
                    lower_bounds.append(np.array(forecast['lower_bound']))
            
            if upper_bounds and lower_bounds:
                ensemble_upper = np.mean(upper_bounds, axis=0)
                ensemble_lower = np.mean(lower_bounds, axis=0)
            else:
                # Use standard deviation of individual forecasts as uncertainty
                forecast_std = np.std(forecast_arrays, axis=0)
                ensemble_upper = ensemble_forecast + 1.96 * forecast_std
                ensemble_lower = ensemble_forecast - 1.96 * forecast_std
            
            return {
                'method': 'ensemble',
                'forecast_values': ensemble_forecast.tolist(),
                'upper_bound': ensemble_upper.tolist(),
                'lower_bound': ensemble_lower.tolist(),
                'num_methods': len(available_forecasts),
                'methods_used': [f.get('method', 'unknown') for f in available_forecasts]
            }
            
        except Exception as e:
            logger.error(f"Error in ensemble forecast: {e}")
            return {}