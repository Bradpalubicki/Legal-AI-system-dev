# =============================================================================
# Legal AI System - Capacity Planning and Forecasting
# =============================================================================
# Advanced capacity planning system for legal document processing workloads,
# AI service usage, storage requirements, and compliance resource allocation
# =============================================================================

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.declarative import declarative_base
import uuid

from ..database import get_db
from .models import MetricSample, AggregatedMetric
from .analytics import PerformanceAnalytics, TrendAnalysis

logger = logging.getLogger(__name__)

# =============================================================================
# CAPACITY MODELS
# =============================================================================

Base = declarative_base()

class CapacityForecast(Base):
    """Database model for storing capacity forecasts."""
    __tablename__ = "capacity_forecasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_name = Column(String(255), nullable=False, index=True)
    
    # Forecast metadata
    forecast_horizon_days = Column(Integer, nullable=False)
    forecast_method = Column(String(50), nullable=False)
    confidence_level = Column(Float, nullable=False, default=95.0)
    
    # Current and forecasted values
    current_utilization = Column(Float, nullable=False)
    current_capacity = Column(Float, nullable=False)
    forecasted_demand = Column(JSON, nullable=False)  # Time series predictions
    recommended_capacity = Column(Float, nullable=False)
    
    # Forecast accuracy
    training_period_days = Column(Integer, nullable=False)
    model_accuracy_score = Column(Float, nullable=True)
    forecast_uncertainty = Column(Float, nullable=True)
    
    # Legal-specific fields
    compliance_buffer_percent = Column(Float, nullable=False, default=20.0)
    peak_season_multiplier = Column(Float, nullable=False, default=1.5)
    
    # Risk assessment
    risk_level = Column(String(20), nullable=False, default="medium")
    capacity_alerts = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    forecast_valid_until = Column(DateTime, nullable=False)

class ResourceUtilizationHistory(Base):
    """Historical resource utilization for capacity planning."""
    __tablename__ = "resource_utilization_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_name = Column(String(255), nullable=False, index=True)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    utilization_percent = Column(Float, nullable=False)
    absolute_usage = Column(Float, nullable=False)
    available_capacity = Column(Float, nullable=False)
    
    # Context metadata
    workload_type = Column(String(100), nullable=True)
    client_tier = Column(String(50), nullable=True)
    compliance_requirements = Column(JSON, nullable=True)

# =============================================================================
# CAPACITY PLANNING TYPES
# =============================================================================

class ResourceType(str, Enum):
    """Types of resources to monitor for capacity planning."""
    COMPUTE_CPU = "compute_cpu"
    COMPUTE_MEMORY = "compute_memory"
    STORAGE_DOCUMENTS = "storage_documents"
    STORAGE_METRICS = "storage_metrics"
    AI_TOKENS_MONTHLY = "ai_tokens_monthly"
    AI_REQUESTS_PER_MINUTE = "ai_requests_per_minute"
    DOCUMENT_PROCESSING_QUEUE = "document_processing_queue"
    COMPLIANCE_AUDIT_CAPACITY = "compliance_audit_capacity"
    USER_SESSIONS = "user_sessions"
    DATABASE_CONNECTIONS = "database_connections"

class ForecastMethod(str, Enum):
    """Forecasting methods for capacity planning."""
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ARIMA = "arima"
    GROWTH_TREND = "growth_trend"

@dataclass
class CapacityRecommendation:
    """Capacity planning recommendation."""
    resource_type: ResourceType
    resource_name: str
    current_capacity: float
    current_utilization: float
    recommended_capacity: float
    timeline_days: int
    confidence_level: float
    cost_impact_estimate: Optional[float]
    risk_level: str
    justification: str
    implementation_steps: List[str]

@dataclass
class ForecastResult:
    """Result of a capacity forecast."""
    timestamps: List[datetime]
    predicted_values: List[float]
    upper_bounds: List[float]
    lower_bounds: List[float]
    confidence_intervals: List[float]
    method_used: ForecastMethod
    accuracy_score: Optional[float]
    forecast_uncertainty: float

# =============================================================================
# TIME SERIES FORECASTING
# =============================================================================

class TimeSeriesForecaster:
    """Time series forecasting for capacity planning."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.models = {}
    
    async def forecast_linear_regression(
        self,
        timestamps: List[datetime],
        values: List[float],
        horizon_days: int,
        confidence_level: float = 95.0
    ) -> ForecastResult:
        """Linear regression forecasting with confidence intervals."""
        if len(values) < 7:  # Need minimum data points
            raise ValueError("Insufficient data for forecasting (minimum 7 points required)")
        
        # Prepare data
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })
        df = df.sort_values('timestamp')
        
        # Convert timestamps to numerical values (days since first timestamp)
        start_date = df['timestamp'].min()
        df['days'] = (df['timestamp'] - start_date).dt.total_seconds() / (24 * 3600)
        
        # Prepare features
        X = df[['days']].values
        y = df['value'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        # Generate future timestamps
        future_days = np.arange(
            df['days'].max() + 1,
            df['days'].max() + horizon_days + 1
        )
        future_timestamps = [
            start_date + timedelta(days=float(day))
            for day in future_days
        ]
        
        # Make predictions
        future_X = future_days.reshape(-1, 1)
        future_X_scaled = self.scaler.transform(future_X)
        predictions = model.predict(future_X_scaled)
        
        # Calculate confidence intervals
        mse = mean_squared_error(y, model.predict(X_scaled))
        std_error = np.sqrt(mse)
        
        # For 95% confidence interval (z-score = 1.96)
        z_score = 1.96 if confidence_level == 95.0 else 2.58  # 99%
        margin_of_error = z_score * std_error
        
        upper_bounds = predictions + margin_of_error
        lower_bounds = predictions - margin_of_error
        confidence_intervals = [margin_of_error] * len(predictions)
        
        # Calculate accuracy
        train_predictions = model.predict(X_scaled)
        accuracy_score = 1.0 - (mean_absolute_error(y, train_predictions) / np.mean(y))
        
        return ForecastResult(
            timestamps=future_timestamps,
            predicted_values=predictions.tolist(),
            upper_bounds=upper_bounds.tolist(),
            lower_bounds=lower_bounds.tolist(),
            confidence_intervals=confidence_intervals,
            method_used=ForecastMethod.LINEAR_REGRESSION,
            accuracy_score=max(0.0, accuracy_score),
            forecast_uncertainty=margin_of_error / np.mean(predictions) if np.mean(predictions) > 0 else 1.0
        )
    
    async def forecast_seasonal_trend(
        self,
        timestamps: List[datetime],
        values: List[float],
        horizon_days: int,
        seasonal_period: int = 7  # Weekly seasonality
    ) -> ForecastResult:
        """Seasonal trend forecasting for workloads with patterns."""
        if len(values) < seasonal_period * 3:
            # Fall back to linear regression if insufficient seasonal data
            return await self.forecast_linear_regression(timestamps, values, horizon_days)
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })
        df = df.sort_values('timestamp')
        
        # Calculate trend using moving average
        trend = df['value'].rolling(window=seasonal_period, center=True).mean()
        
        # Calculate seasonal component
        detrended = df['value'] - trend
        seasonal_pattern = []
        for i in range(seasonal_period):
            seasonal_values = [
                detrended.iloc[j] for j in range(i, len(detrended), seasonal_period)
                if not pd.isna(detrended.iloc[j])
            ]
            if seasonal_values:
                seasonal_pattern.append(np.mean(seasonal_values))
            else:
                seasonal_pattern.append(0.0)
        
        # Extend trend linearly
        trend_slope = (trend.iloc[-1] - trend.iloc[-seasonal_period]) / seasonal_period
        future_timestamps = []
        predictions = []
        
        for i in range(1, horizon_days + 1):
            future_timestamp = timestamps[-1] + timedelta(days=i)
            future_timestamps.append(future_timestamp)
            
            # Extend trend
            future_trend = trend.iloc[-1] + (trend_slope * i)
            
            # Add seasonal component
            seasonal_index = (i - 1) % seasonal_period
            seasonal_component = seasonal_pattern[seasonal_index]
            
            prediction = future_trend + seasonal_component
            predictions.append(max(0.0, prediction))  # Ensure non-negative
        
        # Calculate uncertainty
        residuals = df['value'] - (trend + [seasonal_pattern[i % seasonal_period] for i in range(len(df))])
        residuals = residuals.dropna()
        forecast_uncertainty = np.std(residuals)
        
        # Confidence bounds
        upper_bounds = [p + (1.96 * forecast_uncertainty) for p in predictions]
        lower_bounds = [max(0.0, p - (1.96 * forecast_uncertainty)) for p in predictions]
        
        return ForecastResult(
            timestamps=future_timestamps,
            predicted_values=predictions,
            upper_bounds=upper_bounds,
            lower_bounds=lower_bounds,
            confidence_intervals=[1.96 * forecast_uncertainty] * len(predictions),
            method_used=ForecastMethod.SEASONAL_DECOMPOSITION,
            accuracy_score=0.85,  # Estimated accuracy for seasonal models
            forecast_uncertainty=forecast_uncertainty / np.mean(values) if np.mean(values) > 0 else 1.0
        )

# =============================================================================
# CAPACITY PLANNING ENGINE
# =============================================================================

class CapacityPlanningEngine:
    """Main engine for capacity planning and forecasting."""
    
    def __init__(self):
        self.forecaster = TimeSeriesForecaster()
        self.resource_configs = self._initialize_resource_configurations()
    
    def _initialize_resource_configurations(self) -> Dict[ResourceType, Dict[str, Any]]:
        """Initialize resource-specific configurations."""
        return {
            ResourceType.COMPUTE_CPU: {
                "target_utilization": 70.0,  # Target 70% CPU utilization
                "alert_threshold": 85.0,
                "critical_threshold": 95.0,
                "scaling_unit": 1.0,  # 1 CPU core
                "cost_per_unit": 50.0,  # USD per month per core
                "compliance_buffer": 15.0  # 15% buffer for compliance workloads
            },
            ResourceType.COMPUTE_MEMORY: {
                "target_utilization": 75.0,
                "alert_threshold": 85.0,
                "critical_threshold": 95.0,
                "scaling_unit": 8.0,  # 8 GB
                "cost_per_unit": 30.0,
                "compliance_buffer": 20.0
            },
            ResourceType.STORAGE_DOCUMENTS: {
                "target_utilization": 80.0,
                "alert_threshold": 90.0,
                "critical_threshold": 95.0,
                "scaling_unit": 1024.0,  # 1 TB
                "cost_per_unit": 100.0,
                "compliance_buffer": 25.0  # Legal documents need extra retention space
            },
            ResourceType.AI_TOKENS_MONTHLY: {
                "target_utilization": 80.0,
                "alert_threshold": 90.0,
                "critical_threshold": 98.0,
                "scaling_unit": 1000000.0,  # 1M tokens
                "cost_per_unit": 200.0,
                "compliance_buffer": 20.0
            },
            ResourceType.DOCUMENT_PROCESSING_QUEUE: {
                "target_utilization": 60.0,  # Lower target for responsiveness
                "alert_threshold": 75.0,
                "critical_threshold": 90.0,
                "scaling_unit": 10.0,  # 10 concurrent processors
                "cost_per_unit": 500.0,  # Cost of scaling processing capacity
                "compliance_buffer": 30.0  # Extra capacity for urgent legal work
            }
        }
    
    async def analyze_current_capacity(
        self,
        db: AsyncSession,
        resource_type: ResourceType,
        resource_name: str,
        lookback_days: int = 7
    ) -> Dict[str, Any]:
        """Analyze current capacity utilization for a resource."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=lookback_days)
        
        # Get historical utilization data
        query = select(ResourceUtilizationHistory).where(
            and_(
                ResourceUtilizationHistory.resource_type == resource_type.value,
                ResourceUtilizationHistory.resource_name == resource_name,
                ResourceUtilizationHistory.timestamp >= start_time
            )
        ).order_by(ResourceUtilizationHistory.timestamp)
        
        result = await db.execute(query)
        history = result.scalars().all()
        
        if not history:
            return {"error": "No historical data available"}
        
        utilizations = [h.utilization_percent for h in history]
        absolute_usages = [h.absolute_usage for h in history]
        
        # Calculate statistics
        current_utilization = utilizations[-1]
        avg_utilization = np.mean(utilizations)
        peak_utilization = np.max(utilizations)
        utilization_trend = (utilizations[-1] - utilizations[0]) / len(utilizations)
        
        # Get resource configuration
        config = self.resource_configs.get(resource_type, {})
        target_util = config.get("target_utilization", 80.0)
        alert_threshold = config.get("alert_threshold", 90.0)
        
        # Assess current state
        status = "healthy"
        if current_utilization > alert_threshold:
            status = "warning"
        if current_utilization > config.get("critical_threshold", 95.0):
            status = "critical"
        
        return {
            "resource_type": resource_type.value,
            "resource_name": resource_name,
            "current_utilization": current_utilization,
            "average_utilization": avg_utilization,
            "peak_utilization": peak_utilization,
            "utilization_trend": utilization_trend,
            "status": status,
            "target_utilization": target_util,
            "headroom_percent": max(0, target_util - current_utilization),
            "days_analyzed": lookback_days,
            "data_points": len(history)
        }
    
    async def generate_capacity_forecast(
        self,
        db: AsyncSession,
        resource_type: ResourceType,
        resource_name: str,
        forecast_horizon_days: int = 30,
        training_period_days: int = 30
    ) -> CapacityForecast:
        """Generate capacity forecast for a specific resource."""
        # Get historical data for training
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=training_period_days)
        
        query = select(ResourceUtilizationHistory).where(
            and_(
                ResourceUtilizationHistory.resource_type == resource_type.value,
                ResourceUtilizationHistory.resource_name == resource_name,
                ResourceUtilizationHistory.timestamp >= start_time
            )
        ).order_by(ResourceUtilizationHistory.timestamp)
        
        result = await db.execute(query)
        history = result.scalars().all()
        
        if len(history) < 7:
            raise ValueError(f"Insufficient data for forecasting {resource_name} (need at least 7 days)")
        
        # Prepare data for forecasting
        timestamps = [h.timestamp for h in history]
        utilizations = [h.utilization_percent for h in history]
        
        # Choose forecasting method based on data characteristics
        method = self._select_forecasting_method(utilizations)
        
        # Generate forecast
        if method == ForecastMethod.LINEAR_REGRESSION:
            forecast = await self.forecaster.forecast_linear_regression(
                timestamps, utilizations, forecast_horizon_days
            )
        elif method == ForecastMethod.SEASONAL_DECOMPOSITION:
            forecast = await self.forecaster.forecast_seasonal_trend(
                timestamps, utilizations, forecast_horizon_days
            )
        else:
            # Default to linear regression
            forecast = await self.forecaster.forecast_linear_regression(
                timestamps, utilizations, forecast_horizon_days
            )
        
        # Calculate capacity recommendations
        config = self.resource_configs.get(resource_type, {})
        target_utilization = config.get("target_utilization", 80.0)
        compliance_buffer = config.get("compliance_buffer", 20.0)
        
        # Find peak forecasted utilization
        peak_forecasted = max(forecast.predicted_values)
        current_utilization = utilizations[-1]
        current_capacity = history[-1].available_capacity
        
        # Calculate recommended capacity with compliance buffer
        if peak_forecasted > target_utilization:
            capacity_multiplier = (peak_forecasted + compliance_buffer) / target_utilization
            recommended_capacity = current_capacity * capacity_multiplier
        else:
            recommended_capacity = current_capacity
        
        # Assess risk level
        risk_level = self._assess_capacity_risk(
            current_utilization, peak_forecasted, target_utilization, forecast.forecast_uncertainty
        )
        
        # Generate alerts if needed
        alerts = []
        if peak_forecasted > config.get("alert_threshold", 90.0):
            alerts.append({
                "type": "capacity_warning",
                "message": f"Forecasted peak utilization ({peak_forecasted:.1f}%) exceeds alert threshold",
                "recommended_action": "Scale up capacity before peak period"
            })
        
        # Create forecast record
        capacity_forecast = CapacityForecast(
            resource_type=resource_type.value,
            resource_name=resource_name,
            forecast_horizon_days=forecast_horizon_days,
            forecast_method=method.value,
            confidence_level=95.0,
            current_utilization=current_utilization,
            current_capacity=current_capacity,
            forecasted_demand={
                "timestamps": [ts.isoformat() for ts in forecast.timestamps],
                "predicted_values": forecast.predicted_values,
                "upper_bounds": forecast.upper_bounds,
                "lower_bounds": forecast.lower_bounds
            },
            recommended_capacity=recommended_capacity,
            training_period_days=training_period_days,
            model_accuracy_score=forecast.accuracy_score,
            forecast_uncertainty=forecast.forecast_uncertainty,
            compliance_buffer_percent=compliance_buffer,
            peak_season_multiplier=1.5,  # Legal industry often has seasonal peaks
            risk_level=risk_level,
            capacity_alerts=alerts,
            forecast_valid_until=datetime.utcnow() + timedelta(days=forecast_horizon_days // 2)
        )
        
        # Store forecast in database
        db.add(capacity_forecast)
        await db.commit()
        await db.refresh(capacity_forecast)
        
        return capacity_forecast
    
    def _select_forecasting_method(self, values: List[float]) -> ForecastMethod:
        """Select the best forecasting method based on data characteristics."""
        if len(values) < 14:
            return ForecastMethod.LINEAR_REGRESSION
        
        # Check for seasonality (simple weekly pattern detection)
        if len(values) >= 21:  # Need at least 3 weeks of data
            weekly_correlation = np.corrcoef(values[:-7], values[7:])[0, 1]
            if weekly_correlation > 0.3:  # Moderate weekly correlation
                return ForecastMethod.SEASONAL_DECOMPOSITION
        
        # Default to linear regression for trending data
        return ForecastMethod.LINEAR_REGRESSION
    
    def _assess_capacity_risk(
        self,
        current_utilization: float,
        peak_forecasted: float,
        target_utilization: float,
        forecast_uncertainty: float
    ) -> str:
        """Assess the risk level of capacity constraints."""
        # Risk factors
        utilization_risk = peak_forecasted / target_utilization
        uncertainty_risk = forecast_uncertainty
        current_stress = current_utilization / target_utilization
        
        # Combined risk score
        risk_score = (utilization_risk * 0.5) + (uncertainty_risk * 0.3) + (current_stress * 0.2)
        
        if risk_score > 1.3:
            return "high"
        elif risk_score > 1.1:
            return "medium"
        else:
            return "low"
    
    async def generate_capacity_recommendations(
        self,
        db: AsyncSession,
        resource_type: Optional[ResourceType] = None,
        timeline_days: int = 30
    ) -> List[CapacityRecommendation]:
        """Generate capacity recommendations for resources."""
        recommendations = []
        
        # Get resource types to analyze
        resource_types = [resource_type] if resource_type else list(ResourceType)
        
        for rt in resource_types:
            try:
                # Get unique resource names for this type
                query = select(ResourceUtilizationHistory.resource_name).where(
                    ResourceUtilizationHistory.resource_type == rt.value
                ).distinct()
                
                result = await db.execute(query)
                resource_names = [row[0] for row in result]
                
                for resource_name in resource_names:
                    # Generate forecast
                    forecast = await self.generate_capacity_forecast(
                        db, rt, resource_name, timeline_days
                    )
                    
                    # Create recommendation
                    config = self.resource_configs.get(rt, {})
                    scaling_unit = config.get("scaling_unit", 1.0)
                    cost_per_unit = config.get("cost_per_unit", 0.0)
                    
                    capacity_increase = forecast.recommended_capacity - forecast.current_capacity
                    cost_impact = (capacity_increase / scaling_unit) * cost_per_unit if scaling_unit > 0 else None
                    
                    # Generate implementation steps
                    implementation_steps = self._generate_implementation_steps(rt, capacity_increase)
                    
                    recommendation = CapacityRecommendation(
                        resource_type=rt,
                        resource_name=resource_name,
                        current_capacity=forecast.current_capacity,
                        current_utilization=forecast.current_utilization,
                        recommended_capacity=forecast.recommended_capacity,
                        timeline_days=timeline_days,
                        confidence_level=95.0,
                        cost_impact_estimate=cost_impact,
                        risk_level=forecast.risk_level,
                        justification=self._generate_justification(forecast),
                        implementation_steps=implementation_steps
                    )
                    
                    recommendations.append(recommendation)
                    
            except Exception as e:
                logger.error(f"Error generating recommendation for {rt.value}: {e}")
                continue
        
        return recommendations
    
    def _generate_implementation_steps(
        self,
        resource_type: ResourceType,
        capacity_increase: float
    ) -> List[str]:
        """Generate implementation steps for capacity scaling."""
        steps = []
        
        if capacity_increase <= 0:
            return ["No scaling required at this time"]
        
        if resource_type == ResourceType.COMPUTE_CPU:
            steps = [
                "1. Review current CPU utilization patterns and identify peak periods",
                "2. Plan scaling during maintenance window to minimize service disruption",
                "3. Add CPU cores to existing instances or deploy additional instances",
                "4. Update load balancer configuration if deploying new instances",
                "5. Monitor performance after scaling and adjust if needed"
            ]
        elif resource_type == ResourceType.AI_TOKENS_MONTHLY:
            steps = [
                "1. Review AI usage patterns and identify high-consumption features",
                "2. Contact AI providers to increase token limits or discuss pricing",
                "3. Implement token usage monitoring and alerting",
                "4. Consider optimizing AI prompts to reduce token consumption",
                "5. Plan budget allocation for increased AI costs"
            ]
        elif resource_type == ResourceType.STORAGE_DOCUMENTS:
            steps = [
                "1. Analyze document storage growth patterns and retention policies",
                "2. Archive old documents to cold storage if compliance allows",
                "3. Provision additional storage capacity",
                "4. Update backup and disaster recovery procedures",
                "5. Implement storage tiering for cost optimization"
            ]
        else:
            steps = [
                "1. Analyze current resource utilization and bottlenecks",
                "2. Plan scaling approach based on resource type and constraints",
                "3. Implement scaling during maintenance window",
                "4. Monitor and validate scaling effectiveness",
                "5. Update monitoring and alerting thresholds"
            ]
        
        return steps
    
    def _generate_justification(self, forecast: CapacityForecast) -> str:
        """Generate justification for capacity recommendation."""
        current_util = forecast.current_utilization
        forecasted_data = forecast.forecasted_demand
        peak_forecasted = max(forecasted_data["predicted_values"]) if forecasted_data["predicted_values"] else current_util
        
        justification = f"Current utilization: {current_util:.1f}%. "
        justification += f"Forecasted peak: {peak_forecasted:.1f}% over next {forecast.forecast_horizon_days} days. "
        
        if forecast.risk_level == "high":
            justification += "High risk of capacity constraints affecting legal service delivery. "
        elif forecast.risk_level == "medium":
            justification += "Moderate risk requiring proactive capacity planning. "
        
        if forecast.compliance_buffer_percent > 0:
            justification += f"Including {forecast.compliance_buffer_percent:.1f}% compliance buffer for legal workload requirements."
        
        return justification

# =============================================================================
# LEGAL WORKLOAD PATTERNS
# =============================================================================

class LegalWorkloadAnalyzer:
    """Analyzes legal-specific workload patterns for capacity planning."""
    
    def __init__(self):
        self.legal_seasons = {
            "tax_season": {"start_month": 1, "end_month": 4, "multiplier": 1.8},
            "fiscal_year_end": {"start_month": 11, "end_month": 12, "multiplier": 1.5},
            "litigation_prep": {"start_month": 9, "end_month": 10, "multiplier": 1.3}
        }
    
    async def analyze_legal_workload_patterns(
        self,
        db: AsyncSession,
        lookback_months: int = 12
    ) -> Dict[str, Any]:
        """Analyze legal workload patterns for capacity planning."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=lookback_months * 30)
        
        # Analyze document processing patterns
        doc_processing_query = select(
            func.date_trunc('month', ResourceUtilizationHistory.timestamp).label('month'),
            func.avg(ResourceUtilizationHistory.utilization_percent).label('avg_utilization'),
            func.max(ResourceUtilizationHistory.utilization_percent).label('peak_utilization'),
            ResourceUtilizationHistory.workload_type
        ).where(
            and_(
                ResourceUtilizationHistory.resource_type == ResourceType.DOCUMENT_PROCESSING_QUEUE.value,
                ResourceUtilizationHistory.timestamp >= start_time
            )
        ).group_by('month', ResourceUtilizationHistory.workload_type)
        
        result = await db.execute(doc_processing_query)
        monthly_patterns = result.fetchall()
        
        # Identify seasonal patterns
        seasonal_analysis = {}
        for season, config in self.legal_seasons.items():
            seasonal_data = [
                row for row in monthly_patterns
                if config["start_month"] <= row.month.month <= config["end_month"]
            ]
            
            if seasonal_data:
                avg_seasonal_utilization = np.mean([row.avg_utilization for row in seasonal_data])
                seasonal_analysis[season] = {
                    "average_utilization": avg_seasonal_utilization,
                    "expected_multiplier": config["multiplier"],
                    "data_points": len(seasonal_data)
                }
        
        return {
            "analysis_period_months": lookback_months,
            "seasonal_patterns": seasonal_analysis,
            "monthly_data_points": len(monthly_patterns),
            "recommendations": self._generate_legal_capacity_recommendations(seasonal_analysis)
        }
    
    def _generate_legal_capacity_recommendations(
        self,
        seasonal_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate legal-specific capacity recommendations."""
        recommendations = []
        
        for season, data in seasonal_analysis.items():
            if data["average_utilization"] > 75.0:
                recommendations.append(
                    f"Plan for {season} capacity increase: "
                    f"historical utilization {data['average_utilization']:.1f}% suggests "
                    f"scaling resources by {data['expected_multiplier']}x"
                )
        
        if not recommendations:
            recommendations.append("Current capacity appears adequate for seasonal variations")
        
        return recommendations

# =============================================================================
# INITIALIZATION
# =============================================================================

def init_capacity_planning():
    """Initialize the capacity planning system."""
    logger.info("Initializing capacity planning and forecasting system")
    logger.info("Capacity planning system initialized")

# Initialize on import
init_capacity_planning()

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CapacityPlanningEngine",
    "LegalWorkloadAnalyzer",
    "CapacityForecast",
    "ResourceUtilizationHistory",
    "CapacityRecommendation",
    "ForecastResult",
    "ResourceType",
    "ForecastMethod",
    "TimeSeriesForecaster",
    "init_capacity_planning"
]