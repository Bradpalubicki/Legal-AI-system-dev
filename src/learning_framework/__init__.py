"""
Continuous Learning Framework

Advanced continuous learning system for legal AI that adapts and improves
based on user feedback, case outcomes, and real-world performance data.

Features:
- Automated model retraining based on new data
- Feedback integration and quality assessment
- Performance monitoring and drift detection
- Knowledge base evolution and expansion
- A/B testing framework for model improvements
- Reinforcement learning from user interactions
- Domain adaptation for specialized legal areas
- Explainability and bias detection systems
"""

from .learning_coordinator import LearningCoordinator, LearningObjective, LearningStatus
from .feedback_processor import FeedbackProcessor, FeedbackType, FeedbackEntry, QualityScore
from .model_trainer import ModelTrainer, TrainingStrategy, ModelVersion, TrainingResult
from .knowledge_updater import KnowledgeUpdater, KnowledgeType, KnowledgeEntry, UpdateStrategy
from .performance_monitor import PerformanceMonitor, MetricType, PerformanceMetric, DriftDetector
from .adaptive_engine import AdaptiveEngine, AdaptationType, AdaptationRule, AdaptationResult
from .experiment_manager import ExperimentManager, ExperimentType, Experiment, ExperimentResult
from .quality_controller import QualityController, QualityCheck, QualityReport, ValidationResult
from .bias_detector import BiasDetector, BiasType, BiasMetric, MitigationStrategy
from .explainability_engine import ExplainabilityEngine, ExplanationType, Explanation, ExplanationRequest

# Version info
__version__ = "1.0.0"
__author__ = "Legal AI System"

# Public API
__all__ = [
    # Core Learning System
    "LearningCoordinator",
    "LearningObjective",
    "LearningStatus",
    
    # Feedback Processing
    "FeedbackProcessor",
    "FeedbackType",
    "FeedbackEntry",
    "QualityScore",
    
    # Model Training
    "ModelTrainer",
    "TrainingStrategy",
    "ModelVersion",
    "TrainingResult",
    
    # Knowledge Management
    "KnowledgeUpdater",
    "KnowledgeType",
    "KnowledgeEntry",
    "UpdateStrategy",
    
    # Performance Monitoring
    "PerformanceMonitor",
    "MetricType",
    "PerformanceMetric",
    "DriftDetector",
    
    # Adaptive Learning
    "AdaptiveEngine",
    "AdaptationType",
    "AdaptationRule",
    "AdaptationResult",
    
    # Experimentation
    "ExperimentManager",
    "ExperimentType", 
    "Experiment",
    "ExperimentResult",
    
    # Quality Control
    "QualityController",
    "QualityCheck",
    "QualityReport",
    "ValidationResult",
    
    # Bias Detection
    "BiasDetector",
    "BiasType",
    "BiasMetric",
    "MitigationStrategy",
    
    # Explainability
    "ExplainabilityEngine",
    "ExplanationType",
    "Explanation",
    "ExplanationRequest"
]