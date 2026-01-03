"""
Pattern Detection System

Advanced pattern detection and analysis system for legal case activity
with machine learning-powered insights and predictive analytics.

Features:
- Case activity pattern recognition
- Anomaly detection in legal workflows
- Predictive case outcome analysis
- Attorney workload pattern analysis
- Client behavior pattern recognition
- Court proceeding pattern analysis
- Time-based trend detection
- Resource utilization patterns
"""

from .pattern_analyzer import PatternAnalyzer, PatternType, PatternSeverity, DetectedPattern
from .activity_tracker import ActivityTracker, ActivityType, ActivityEvent, ActivityMetrics
from .anomaly_detector import AnomalyDetector, AnomalyType, Anomaly, AnomalyThreshold
from .trend_analyzer import TrendAnalyzer, TrendType, Trend, TrendDirection
from .predictive_engine import PredictiveEngine, PredictionModel, Prediction, OutcomeType
from .workflow_analyzer import WorkflowAnalyzer, WorkflowPattern, ProcessStep, WorkflowMetrics
from .resource_optimizer import ResourceOptimizer, ResourceAllocation, OptimizationSuggestion
from .pattern_coordinator import PatternDetectionCoordinator

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    # Core Pattern Detection
    "PatternAnalyzer",
    "PatternType",
    "PatternSeverity", 
    "DetectedPattern",
    
    # Activity Tracking
    "ActivityTracker",
    "ActivityType",
    "ActivityEvent",
    "ActivityMetrics",
    
    # Anomaly Detection
    "AnomalyDetector",
    "AnomalyType",
    "Anomaly",
    "AnomalyThreshold",
    
    # Trend Analysis
    "TrendAnalyzer",
    "TrendType",
    "Trend",
    "TrendDirection",
    
    # Predictive Analytics
    "PredictiveEngine",
    "PredictionModel",
    "Prediction",
    "OutcomeType",
    
    # Workflow Analysis
    "WorkflowAnalyzer",
    "WorkflowPattern",
    "ProcessStep",
    "WorkflowMetrics",
    
    # Resource Optimization
    "ResourceOptimizer",
    "ResourceAllocation",
    "OptimizationSuggestion",
    
    # Main Coordinator
    "PatternDetectionCoordinator"
]