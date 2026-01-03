"""
Continuous Learning Framework
Orchestrates feedback collection, training, and deployment for ongoing AI improvement.
"""

import asyncio
import json
import logging
import schedule
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import threading
from enum import Enum

# Internal imports
try:
    from src.feedback.collector import FeedbackCollector, FeedbackType, AccuracyRating
    from src.training.pipeline import TrainingPipeline
    from src.models.version_manager import ModelVersionManager, ModelStatus, PerformanceMetrics, ModelMetadata
except ImportError:
    # Fallback for standalone testing
    class FeedbackCollector:
        def __init__(self, config_path: str = None): pass
        async def get_feedback_stats(self) -> Dict[str, Any]: return {}
        async def get_training_queue_data(self) -> List[Dict[str, Any]]: return []

    class TrainingPipeline:
        def __init__(self, config_path: str = None): pass
        async def aggregate_weekly_feedback(self): return None
        async def train_model(self, dataset, base_model: str): return None
        async def start_ab_test(self, model_a: str, model_b: str): return None
        async def evaluate_ab_test(self, test_id: str): return None
        async def gradual_deployment(self, model_id: str) -> bool: return True
        async def get_training_stats(self) -> Dict[str, Any]: return {}

    class ModelVersionManager:
        def __init__(self, storage_path: str = None): pass
        async def register_model(self, metadata) -> bool: return True
        async def record_performance_metrics(self, metrics) -> bool: return True
        async def deploy_model(self, model_id: str, deployment_type, target_environment: str = "production", traffic_percentage: int = 100, configuration: Dict[str, Any] = None) -> str: return "deploy_123"
        async def rollback_model(self, from_model_id: str, to_model_id: str, reason: str, initiated_by: str = "system") -> bool: return True
        async def compare_models(self, model_a_id: str, model_b_id: str, test_dataset_id: str): return None
        async def get_production_models(self): return []
        async def get_version_stats(self) -> Dict[str, Any]: return {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningPhase(Enum):
    COLLECTING = "collecting"
    TRAINING = "training"
    TESTING = "testing"
    DEPLOYING = "deploying"
    MONITORING = "monitoring"
    OPTIMIZING = "optimizing"

@dataclass
class LearningCycle:
    """Represents a complete learning cycle"""
    cycle_id: str
    start_time: datetime
    end_time: Optional[datetime]
    phase: LearningPhase
    feedback_count: int
    models_trained: int
    models_deployed: int
    improvements_detected: List[str]
    performance_gains: Dict[str, float]
    issues_encountered: List[str]
    status: str  # 'running', 'completed', 'failed'

@dataclass
class LearningConfig:
    """Configuration for continuous learning"""
    feedback_collection: Dict[str, Any]
    training_schedule: Dict[str, Any]
    model_management: Dict[str, Any]
    quality_thresholds: Dict[str, float]
    automation_settings: Dict[str, bool]
    safety_checks: Dict[str, Any]

class ContinuousLearningFramework:
    """
    Orchestrates continuous learning across feedback collection, training, and deployment
    """

    def __init__(self, config_path: str = "learning_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize components
        self.feedback_collector = FeedbackCollector()
        self.training_pipeline = TrainingPipeline()
        self.version_manager = ModelVersionManager()

        # Learning state
        self.current_cycle: Optional[LearningCycle] = None
        self.learning_history: List[LearningCycle] = []
        self.scheduler_running = False
        self.scheduler_thread: Optional[threading.Thread] = None

        # Performance tracking
        self.baseline_metrics: Dict[str, float] = {}
        self.improvement_trends: Dict[str, List[float]] = {}

        # Safety mechanisms
        self.error_count = 0
        self.max_errors = self.config.get("safety_checks", {}).get("max_errors", 5)
        self.emergency_stop = False

    def _load_config(self) -> Dict[str, Any]:
        """Load continuous learning configuration"""
        default_config = {
            "feedback_collection": {
                "min_feedback_for_training": 100,
                "quality_threshold": 0.8,
                "attorney_verification_weight": 2.0,
                "real_time_processing": True
            },
            "training_schedule": {
                "weekly_training": True,
                "auto_training_enabled": True,
                "training_day": "sunday",
                "training_hour": 2,  # 2 AM
                "emergency_training_threshold": 0.1  # 10% performance drop
            },
            "model_management": {
                "auto_deployment": True,
                "gradual_rollout": True,
                "performance_monitoring_hours": 48,
                "rollback_threshold": 0.05,  # 5% performance drop
                "max_concurrent_models": 3
            },
            "quality_thresholds": {
                "minimum_accuracy": 0.85,
                "minimum_user_satisfaction": 4.0,
                "maximum_error_rate": 0.05,
                "maximum_response_time_ms": 5000,
                "minimum_safety_score": 0.9
            },
            "automation_settings": {
                "auto_feedback_processing": True,
                "auto_model_training": True,
                "auto_model_deployment": False,  # Require manual approval
                "auto_rollback": True,
                "auto_optimization": True
            },
            "safety_checks": {
                "max_errors": 5,
                "performance_monitoring": True,
                "human_oversight_required": True,
                "bias_detection": True,
                "safety_validation": True
            },
            "optimization": {
                "adaptive_learning_rate": True,
                "dynamic_batch_sizing": True,
                "hyperparameter_tuning": True,
                "ensemble_methods": True
            }
        }

        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
        except Exception as e:
            logger.warning(f"Could not load learning config: {e}, using defaults")

        return default_config

    async def start_continuous_learning(self):
        """Start the continuous learning process"""
        logger.info("Starting continuous learning framework")

        try:
            # Initialize baseline metrics
            await self._establish_baseline_metrics()

            # Start scheduler
            self._setup_scheduler()
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()

            # Start real-time feedback processing if enabled
            if self.config["feedback_collection"]["real_time_processing"]:
                await self._start_real_time_processing()

            logger.info("Continuous learning framework started successfully")

        except Exception as e:
            logger.error(f"Failed to start continuous learning: {e}")
            self.emergency_stop = True
            raise

    async def stop_continuous_learning(self):
        """Stop the continuous learning process"""
        logger.info("Stopping continuous learning framework")

        self.scheduler_running = False
        self.emergency_stop = True

        if self.current_cycle:
            await self._complete_learning_cycle("stopped")

        logger.info("Continuous learning framework stopped")

    async def run_learning_cycle(self) -> LearningCycle:
        """Execute a complete learning cycle"""
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting learning cycle {cycle_id}")

        cycle = LearningCycle(
            cycle_id=cycle_id,
            start_time=datetime.now(),
            end_time=None,
            phase=LearningPhase.COLLECTING,
            feedback_count=0,
            models_trained=0,
            models_deployed=0,
            improvements_detected=[],
            performance_gains={},
            issues_encountered=[],
            status="running"
        )

        self.current_cycle = cycle

        try:
            # Phase 1: Collect and analyze feedback
            await self._phase_collect_feedback(cycle)

            # Phase 2: Train new models if needed
            await self._phase_train_models(cycle)

            # Phase 3: Test new models
            await self._phase_test_models(cycle)

            # Phase 4: Deploy successful models
            await self._phase_deploy_models(cycle)

            # Phase 5: Monitor performance
            await self._phase_monitor_performance(cycle)

            # Phase 6: Optimize and learn
            await self._phase_optimize_system(cycle)

            cycle.status = "completed"
            cycle.end_time = datetime.now()

            logger.info(f"Learning cycle {cycle_id} completed successfully")

        except Exception as e:
            logger.error(f"Learning cycle {cycle_id} failed: {e}")
            cycle.issues_encountered.append(str(e))
            cycle.status = "failed"
            cycle.end_time = datetime.now()

            # Handle failure
            await self._handle_cycle_failure(cycle, e)

        finally:
            self.learning_history.append(cycle)
            self.current_cycle = None

        return cycle

    async def _phase_collect_feedback(self, cycle: LearningCycle):
        """Phase 1: Collect and analyze feedback"""
        logger.info("Phase 1: Collecting feedback")
        cycle.phase = LearningPhase.COLLECTING

        # Get feedback statistics
        feedback_stats = await self.feedback_collector.get_feedback_stats()
        cycle.feedback_count = feedback_stats.get('total_feedback', 0)

        # Check if we have enough quality feedback for training
        quality_feedback = feedback_stats.get('high_quality_count', 0)
        min_threshold = self.config["feedback_collection"]["min_feedback_for_training"]

        if quality_feedback < min_threshold:
            logger.info(f"Insufficient quality feedback: {quality_feedback} < {min_threshold}")
            cycle.improvements_detected.append("insufficient_feedback")
            return

        # Analyze feedback patterns
        await self._analyze_feedback_patterns(cycle)

    async def _phase_train_models(self, cycle: LearningCycle):
        """Phase 2: Train new models based on feedback"""
        logger.info("Phase 2: Training models")
        cycle.phase = LearningPhase.TRAINING

        if not self.config["automation_settings"]["auto_model_training"]:
            logger.info("Auto training disabled, skipping model training")
            return

        # Aggregate feedback into training dataset
        dataset = await self.training_pipeline.aggregate_weekly_feedback()

        if not dataset:
            logger.info("No suitable training dataset available")
            return

        # Train models for different scenarios
        model_types = ["gpt-4", "claude-3-opus"]

        for model_type in model_types:
            try:
                logger.info(f"Training {model_type} model")
                model = await self.training_pipeline.train_model(dataset, model_type)

                if model:
                    cycle.models_trained += 1
                    cycle.improvements_detected.append(f"trained_{model_type}")

                    # Register model with version manager
                    await self._register_new_model(model)

            except Exception as e:
                logger.error(f"Failed to train {model_type}: {e}")
                cycle.issues_encountered.append(f"training_failed_{model_type}: {str(e)}")

    async def _phase_test_models(self, cycle: LearningCycle):
        """Phase 3: Test newly trained models"""
        logger.info("Phase 3: Testing models")
        cycle.phase = LearningPhase.TESTING

        # Get production models for comparison
        production_models = await self.version_manager.get_production_models()

        if not production_models:
            logger.warning("No production models found for comparison")
            return

        # Get recently trained models
        recent_models = await self._get_recent_models(hours=24)

        for new_model in recent_models:
            for prod_model in production_models:
                try:
                    # Compare models
                    comparison = await self.version_manager.compare_models(
                        new_model.model_id,
                        prod_model.model_id,
                        "test_dataset_001"
                    )

                    if comparison and comparison.winner == new_model.model_id:
                        cycle.improvements_detected.append(f"superior_model_{new_model.model_id}")

                        # Calculate performance gains
                        for metric, values in comparison.metrics_comparison.items():
                            if values['difference'] > 0:
                                cycle.performance_gains[metric] = values['difference']

                except Exception as e:
                    logger.error(f"Failed to compare models: {e}")
                    cycle.issues_encountered.append(f"comparison_failed: {str(e)}")

    async def _phase_deploy_models(self, cycle: LearningCycle):
        """Phase 4: Deploy successful models"""
        logger.info("Phase 4: Deploying models")
        cycle.phase = LearningPhase.DEPLOYING

        if not self.config["automation_settings"]["auto_model_deployment"]:
            logger.info("Auto deployment disabled, skipping deployment")
            return

        # Deploy models that showed improvements
        for improvement in cycle.improvements_detected:
            if improvement.startswith("superior_model_"):
                model_id = improvement.replace("superior_model_", "")

                try:
                    if self.config["model_management"]["gradual_rollout"]:
                        success = await self.training_pipeline.gradual_deployment(model_id)
                    else:
                        deployment_id = await self.version_manager.deploy_model(
                            model_id,
                            "full",
                            "production"
                        )
                        success = deployment_id is not None

                    if success:
                        cycle.models_deployed += 1
                        logger.info(f"Successfully deployed model {model_id}")
                    else:
                        cycle.issues_encountered.append(f"deployment_failed_{model_id}")

                except Exception as e:
                    logger.error(f"Failed to deploy model {model_id}: {e}")
                    cycle.issues_encountered.append(f"deployment_error_{model_id}: {str(e)}")

    async def _phase_monitor_performance(self, cycle: LearningCycle):
        """Phase 5: Monitor performance of deployed models"""
        logger.info("Phase 5: Monitoring performance")
        cycle.phase = LearningPhase.MONITORING

        # Monitor for configured duration
        monitoring_hours = self.config["model_management"]["performance_monitoring_hours"]
        monitoring_start = datetime.now()

        # In real implementation, this would be ongoing monitoring
        # For simulation, we'll check current metrics
        await self._check_model_performance(cycle)

    async def _phase_optimize_system(self, cycle: LearningCycle):
        """Phase 6: Optimize system based on learnings"""
        logger.info("Phase 6: Optimizing system")
        cycle.phase = LearningPhase.OPTIMIZING

        if not self.config["automation_settings"]["auto_optimization"]:
            logger.info("Auto optimization disabled, skipping optimization")
            return

        # Analyze performance trends
        await self._analyze_performance_trends(cycle)

        # Optimize hyperparameters if enabled
        if self.config["optimization"]["hyperparameter_tuning"]:
            await self._optimize_hyperparameters(cycle)

        # Update learning strategies
        await self._update_learning_strategies(cycle)

    async def _analyze_feedback_patterns(self, cycle: LearningCycle):
        """Analyze feedback patterns for insights"""
        feedback_stats = await self.feedback_collector.get_feedback_stats()

        # Look for common error patterns
        common_errors = feedback_stats.get('common_errors', [])
        if common_errors:
            cycle.improvements_detected.extend([f"error_pattern_{error}" for error in common_errors])

        # Check for legal domain improvements needed
        legal_accuracy = feedback_stats.get('legal_accuracy', 0)
        if legal_accuracy < self.config["quality_thresholds"]["minimum_accuracy"]:
            cycle.improvements_detected.append("legal_accuracy_below_threshold")

    async def _register_new_model(self, model):
        """Register a newly trained model"""
        # Create metadata from training pipeline model
        metadata = ModelMetadata(
            model_id=model.model_id,
            version=model.version,
            name=f"Continuous Learning Model {model.version}",
            description="Model trained through continuous learning framework",
            model_type=model.model_type,
            base_model=model.base_model,
            training_dataset_id=model.training_dataset_id,
            created_at=model.created_at,
            created_by="continuous_learning_framework",
            tags=["continuous_learning", "auto_trained"],
            config=model.config
        )

        await self.version_manager.register_model(metadata)

        # Record performance metrics
        if hasattr(model, 'performance_metrics') and model.performance_metrics:
            # Convert to PerformanceMetrics format
            await self._record_model_metrics(model)

    async def _get_recent_models(self, hours: int = 24) -> List:
        """Get models created in the last N hours"""
        # In real implementation, this would query the database
        # For simulation, return empty list
        return []

    async def _check_model_performance(self, cycle: LearningCycle):
        """Check current model performance"""
        production_models = await self.version_manager.get_production_models()

        for model in production_models:
            metrics = await self.version_manager.get_latest_performance_metrics(model.model_id)

            if metrics:
                # Check against thresholds
                thresholds = self.config["quality_thresholds"]

                if metrics.accuracy < thresholds["minimum_accuracy"]:
                    cycle.issues_encountered.append(f"accuracy_below_threshold_{model.model_id}")

                    # Trigger rollback if enabled
                    if self.config["automation_settings"]["auto_rollback"]:
                        await self._trigger_emergency_rollback(model.model_id, "accuracy_threshold")

    async def _analyze_performance_trends(self, cycle: LearningCycle):
        """Analyze performance trends over time"""
        version_stats = await self.version_manager.get_version_stats()

        # Track trends in key metrics
        avg_accuracy = version_stats.get('average_metrics', {}).get('accuracy', 0)

        if 'accuracy' not in self.improvement_trends:
            self.improvement_trends['accuracy'] = []

        self.improvement_trends['accuracy'].append(avg_accuracy)

        # Detect if we're improving over time
        if len(self.improvement_trends['accuracy']) >= 3:
            recent_trend = self.improvement_trends['accuracy'][-3:]
            if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                cycle.improvements_detected.append("positive_accuracy_trend")

    async def _optimize_hyperparameters(self, cycle: LearningCycle):
        """Optimize hyperparameters based on performance"""
        logger.info("Optimizing hyperparameters")

        # In real implementation, this would use hyperparameter optimization libraries
        # For simulation, just log the action
        cycle.improvements_detected.append("hyperparameters_optimized")

    async def _update_learning_strategies(self, cycle: LearningCycle):
        """Update learning strategies based on cycle results"""
        # Adapt learning rate based on performance
        if cycle.performance_gains:
            avg_gain = sum(cycle.performance_gains.values()) / len(cycle.performance_gains)
            if avg_gain > 0.05:  # 5% improvement
                # Increase learning frequency
                cycle.improvements_detected.append("increased_learning_frequency")

    async def _trigger_emergency_rollback(self, model_id: str, reason: str):
        """Trigger emergency rollback"""
        logger.warning(f"Triggering emergency rollback for {model_id}: {reason}")

        # Find previous stable model
        production_models = await self.version_manager.get_production_models()

        # In real implementation, would select best previous model
        # For simulation, just log the action
        logger.info(f"Emergency rollback completed for {model_id}")

    async def _handle_cycle_failure(self, cycle: LearningCycle, error: Exception):
        """Handle learning cycle failure"""
        self.error_count += 1

        logger.error(f"Learning cycle failed: {error}")

        if self.error_count >= self.max_errors:
            logger.critical("Maximum error count reached, stopping continuous learning")
            self.emergency_stop = True

    async def _establish_baseline_metrics(self):
        """Establish baseline performance metrics"""
        version_stats = await self.version_manager.get_version_stats()
        self.baseline_metrics = version_stats.get('average_metrics', {})
        logger.info(f"Established baseline metrics: {self.baseline_metrics}")

    async def _start_real_time_processing(self):
        """Start real-time feedback processing"""
        logger.info("Starting real-time feedback processing")
        # In real implementation, this would set up event listeners
        # For simulation, just log the action

    def _setup_scheduler(self):
        """Setup the learning schedule"""
        training_config = self.config["training_schedule"]

        if training_config["weekly_training"]:
            training_day = training_config["training_day"]
            training_hour = training_config["training_hour"]

            # Schedule weekly training
            getattr(schedule.every(), training_day).at(f"{training_hour:02d}:00").do(
                lambda: asyncio.create_task(self.run_learning_cycle())
            )

            logger.info(f"Scheduled weekly training on {training_day} at {training_hour}:00")

    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.scheduler_running and not self.emergency_stop:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning framework statistics"""
        # Get component stats
        feedback_stats = await self.feedback_collector.get_feedback_stats()
        training_stats = await self.training_pipeline.get_training_stats()
        version_stats = await self.version_manager.get_version_stats()

        # Calculate learning-specific stats
        total_cycles = len(self.learning_history)
        successful_cycles = len([c for c in self.learning_history if c.status == "completed"])
        total_improvements = sum(len(c.improvements_detected) for c in self.learning_history)

        return {
            'framework_status': {
                'running': self.scheduler_running,
                'emergency_stop': self.emergency_stop,
                'current_cycle': self.current_cycle.cycle_id if self.current_cycle else None,
                'error_count': self.error_count
            },
            'learning_cycles': {
                'total_cycles': total_cycles,
                'successful_cycles': successful_cycles,
                'success_rate': successful_cycles / max(total_cycles, 1),
                'total_improvements': total_improvements
            },
            'component_stats': {
                'feedback': feedback_stats,
                'training': training_stats,
                'versioning': version_stats
            },
            'performance_trends': self.improvement_trends,
            'baseline_metrics': self.baseline_metrics,
            'last_updated': datetime.now().isoformat()
        }

    async def _record_model_metrics(self, model):
        """Record performance metrics for a model"""
        # Convert training pipeline metrics to PerformanceMetrics format
        # This is a simplified version - real implementation would have proper conversion
        pass

    async def _complete_learning_cycle(self, status: str):
        """Complete the current learning cycle"""
        if self.current_cycle:
            self.current_cycle.status = status
            self.current_cycle.end_time = datetime.now()
            self.learning_history.append(self.current_cycle)
            self.current_cycle = None

# Example usage
async def main():
    """Example usage of the continuous learning framework"""
    framework = ContinuousLearningFramework()

    # Start continuous learning
    await framework.start_continuous_learning()

    # Run a single cycle for demonstration
    cycle = await framework.run_learning_cycle()
    print(f"Learning cycle completed: {cycle.cycle_id}")
    print(f"Improvements detected: {cycle.improvements_detected}")
    print(f"Models trained: {cycle.models_trained}")
    print(f"Models deployed: {cycle.models_deployed}")

    # Get stats
    stats = await framework.get_learning_stats()
    print(f"Learning stats: {json.dumps(stats, indent=2, default=str)}")

    # Stop framework
    await framework.stop_continuous_learning()

if __name__ == "__main__":
    asyncio.run(main())