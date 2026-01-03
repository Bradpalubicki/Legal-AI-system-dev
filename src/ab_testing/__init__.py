"""
A/B Testing and Model Performance Tracking

Comprehensive A/B testing framework for model comparison, performance tracking,
and statistical analysis of model effectiveness in legal AI applications.

Features:
- Multi-variant model testing with traffic splitting
- Statistical significance testing and power analysis
- Real-time performance tracking and monitoring
- Automated experiment lifecycle management
- Advanced metrics collection and analysis
- Risk-based traffic allocation and safety controls
- Bayesian and frequentist statistical approaches
- Model champion/challenger framework
- Rollout strategies with gradual traffic shifting
"""

from .experiment_framework import (
    ExperimentFramework, 
    ExperimentType, 
    ExperimentStatus,
    TrafficSplitStrategy,
    Experiment,
    ExperimentVariant,
    ExperimentResult
)
from .traffic_splitter import (
    TrafficSplitter,
    SplitMethod,
    TrafficAllocation,
    UserAssignment,
    SplitRule
)
from .metrics_collector import (
    MetricsCollector,
    MetricType,
    MetricDefinition,
    MetricValue,
    MetricAggregation
)
from .statistical_analyzer import (
    StatisticalAnalyzer,
    TestMethod,
    StatisticalTest,
    TestResult,
    PowerAnalysis,
    EffectSize
)
from .performance_tracker import (
    PerformanceTracker,
    PerformanceMetric,
    PerformanceSnapshot,
    PerformanceComparison,
    ModelHealthCheck
)
from .experiment_monitor import (
    ExperimentMonitor,
    MonitoringRule,
    SafetyCheck,
    AlertCondition,
    ExperimentAlert
)
from .rollout_manager import (
    RolloutManager,
    RolloutStrategy,
    RolloutPhase,
    RolloutPlan,
    RolloutStatus
)

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    # Core Framework
    "ExperimentFramework",
    "ExperimentType",
    "ExperimentStatus", 
    "TrafficSplitStrategy",
    "Experiment",
    "ExperimentVariant",
    "ExperimentResult",
    
    # Traffic Management
    "TrafficSplitter",
    "SplitMethod",
    "TrafficAllocation",
    "UserAssignment",
    "SplitRule",
    
    # Metrics Collection
    "MetricsCollector",
    "MetricType",
    "MetricDefinition",
    "MetricValue",
    "MetricAggregation",
    
    # Statistical Analysis
    "StatisticalAnalyzer",
    "TestMethod",
    "StatisticalTest",
    "TestResult",
    "PowerAnalysis",
    "EffectSize",
    
    # Performance Tracking
    "PerformanceTracker",
    "PerformanceMetric",
    "PerformanceSnapshot",
    "PerformanceComparison",
    "ModelHealthCheck",
    
    # Monitoring
    "ExperimentMonitor",
    "MonitoringRule",
    "SafetyCheck",
    "AlertCondition",
    "ExperimentAlert",
    
    # Rollout Management
    "RolloutManager",
    "RolloutStrategy",
    "RolloutPhase",
    "RolloutPlan",
    "RolloutStatus"
]