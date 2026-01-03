"""
Experiment Framework

Core A/B testing framework for managing model experiments, traffic allocation,
and statistical evaluation of model variants in legal AI systems.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging
import uuid
import asyncio
import hashlib
import json
import numpy as np
import pandas as pd
from collections import defaultdict
import warnings

logger = logging.getLogger(__name__)

class ExperimentType(Enum):
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    CHAMPION_CHALLENGER = "champion_challenger"
    GRADUAL_ROLLOUT = "gradual_rollout"
    CANARY_RELEASE = "canary_release"
    BLUE_GREEN = "blue_green"
    SHADOW_MODE = "shadow_mode"
    INTERLEAVING = "interleaving"

class ExperimentStatus(Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"

class TrafficSplitStrategy(Enum):
    RANDOM = "random"
    USER_ID_HASH = "user_id_hash"
    SESSION_BASED = "session_based"
    GEOGRAPHY = "geography"
    PRACTICE_AREA = "practice_area"
    CASE_TYPE = "case_type"
    ATTORNEY_TIER = "attorney_tier"
    CUSTOM = "custom"

class VariantType(Enum):
    CONTROL = "control"
    TREATMENT = "treatment"
    BASELINE = "baseline"
    CHALLENGER = "challenger"
    CHAMPION = "champion"

@dataclass
class ExperimentVariant:
    variant_id: str = ""
    name: str = ""
    variant_type: VariantType = VariantType.TREATMENT
    model_id: str = ""
    model_version: str = ""
    traffic_allocation: float = 0.0
    configuration: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    expected_improvement: Optional[float] = None
    risk_level: str = "low"  # low, medium, high
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    custom_parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""

@dataclass
class ExperimentResult:
    experiment_id: str = ""
    variant_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    statistical_significance: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    effect_sizes: Dict[str, float] = field(default_factory=dict)
    p_values: Dict[str, float] = field(default_factory=dict)
    winner: Optional[str] = None
    recommendation: str = ""
    business_impact: Dict[str, float] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    sample_sizes: Dict[str, int] = field(default_factory=dict)
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    analyst_notes: str = ""
    next_steps: List[str] = field(default_factory=list)

@dataclass
class Experiment:
    experiment_id: str = ""
    name: str = ""
    description: str = ""
    experiment_type: ExperimentType = ExperimentType.AB_TEST
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: List[ExperimentVariant] = field(default_factory=list)
    traffic_split_strategy: TrafficSplitStrategy = TrafficSplitStrategy.RANDOM
    target_metrics: List[str] = field(default_factory=list)
    guardrail_metrics: List[str] = field(default_factory=list)
    minimum_detectable_effect: float = 0.05
    statistical_power: float = 0.8
    confidence_level: float = 0.95
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    planned_duration_days: int = 14
    actual_duration_days: Optional[int] = None
    sample_size_required: Dict[str, int] = field(default_factory=dict)
    sample_size_achieved: Dict[str, int] = field(default_factory=dict)
    inclusion_criteria: Dict[str, Any] = field(default_factory=dict)
    exclusion_criteria: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)
    stopping_rules: List[str] = field(default_factory=list)
    results: Optional[ExperimentResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = ""

class ExperimentFramework:
    def __init__(self):
        self.active_experiments: Dict[str, Experiment] = {}
        self.experiment_history: List[Experiment] = []
        self.variant_assignments: Dict[str, str] = {}  # user_id -> variant_id
        self.experiment_config = {
            'max_concurrent_experiments': 10,
            'default_test_duration_days': 14,
            'minimum_sample_size': 1000,
            'maximum_sample_size': 100000,
            'early_stopping_enabled': True,
            'safety_checks_enabled': True,
            'auto_analysis_enabled': True,
            'significance_threshold': 0.05,
            'minimum_effect_size': 0.02,
            'maximum_runtime_days': 90
        }
        
        # Statistical configurations
        self.statistical_config = {
            'bonferroni_correction': True,
            'multiple_testing_adjustment': True,
            'sequential_testing': False,
            'bayesian_analysis': True,
            'bootstrap_samples': 10000,
            'confidence_intervals': True
        }

    async def create_experiment(
        self,
        name: str,
        description: str,
        experiment_type: ExperimentType,
        variants: List[ExperimentVariant],
        target_metrics: List[str],
        created_by: str,
        traffic_split_strategy: TrafficSplitStrategy = TrafficSplitStrategy.RANDOM,
        planned_duration_days: int = 14,
        minimum_detectable_effect: float = 0.05,
        statistical_power: float = 0.8,
        confidence_level: float = 0.95,
        db: Optional[AsyncSession] = None
    ) -> Experiment:
        """Create a new A/B test experiment."""
        try:
            # Generate experiment ID
            experiment_id = f"exp_{uuid.uuid4().hex[:12]}"
            
            # Validate experiment configuration
            validation_result = await self._validate_experiment_config(
                variants, target_metrics, planned_duration_days
            )
            
            if not validation_result['valid']:
                raise ValueError(f"Invalid experiment configuration: {validation_result['errors']}")
            
            # Calculate required sample sizes
            sample_sizes = await self._calculate_sample_sizes(
                variants, minimum_detectable_effect, statistical_power, confidence_level
            )
            
            # Create experiment
            experiment = Experiment(
                experiment_id=experiment_id,
                name=name,
                description=description,
                experiment_type=experiment_type,
                variants=variants,
                traffic_split_strategy=traffic_split_strategy,
                target_metrics=target_metrics,
                planned_duration_days=planned_duration_days,
                minimum_detectable_effect=minimum_detectable_effect,
                statistical_power=statistical_power,
                confidence_level=confidence_level,
                sample_size_required=sample_sizes,
                created_by=created_by
            )
            
            # Store experiment
            self.active_experiments[experiment_id] = experiment
            
            # Persist to database
            if db:
                await self._persist_experiment(experiment, db)
            
            logger.info(f"Created experiment: {experiment_id} - {name}")
            return experiment
            
        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            raise

    async def start_experiment(
        self,
        experiment_id: str,
        start_immediately: bool = True,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Start an A/B test experiment."""
        try:
            if experiment_id not in self.active_experiments:
                logger.error(f"Experiment {experiment_id} not found")
                return False
            
            experiment = self.active_experiments[experiment_id]
            
            # Pre-flight checks
            preflight_result = await self._run_preflight_checks(experiment)
            if not preflight_result['passed']:
                logger.error(f"Preflight checks failed: {preflight_result['failures']}")
                experiment.status = ExperimentStatus.FAILED
                return False
            
            # Validate traffic allocation
            total_allocation = sum(variant.traffic_allocation for variant in experiment.variants)
            if abs(total_allocation - 1.0) > 0.001:
                logger.error(f"Traffic allocation doesn't sum to 1.0: {total_allocation}")
                return False
            
            # Set experiment status and dates
            if start_immediately:
                experiment.status = ExperimentStatus.RUNNING
                experiment.start_date = datetime.utcnow()
                experiment.end_date = experiment.start_date + timedelta(days=experiment.planned_duration_days)
            else:
                experiment.status = ExperimentStatus.READY
            
            experiment.updated_at = datetime.utcnow()
            
            # Initialize variant assignments tracking
            for variant in experiment.variants:
                experiment.sample_size_achieved[variant.variant_id] = 0
            
            # Start monitoring if running
            if experiment.status == ExperimentStatus.RUNNING:
                await self._start_experiment_monitoring(experiment)
            
            # Persist changes
            if db:
                await self._update_experiment(experiment, db)
            
            logger.info(f"Started experiment: {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting experiment {experiment_id}: {e}")
            return False

    async def assign_variant(
        self,
        experiment_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Assign a user to a variant in an experiment."""
        try:
            if experiment_id not in self.active_experiments:
                return None
            
            experiment = self.active_experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.RUNNING:
                return None
            
            # Check if user already assigned
            assignment_key = f"{experiment_id}_{user_id}"
            if assignment_key in self.variant_assignments:
                return self.variant_assignments[assignment_key]
            
            # Check inclusion/exclusion criteria
            if not await self._check_user_eligibility(user_id, experiment, context):
                return None
            
            # Assign variant based on strategy
            variant_id = await self._assign_variant_by_strategy(
                user_id, experiment, context
            )
            
            if variant_id:
                # Store assignment
                self.variant_assignments[assignment_key] = variant_id
                
                # Update sample size tracking
                experiment.sample_size_achieved[variant_id] = experiment.sample_size_achieved.get(variant_id, 0) + 1
                
                logger.debug(f"Assigned user {user_id} to variant {variant_id} in experiment {experiment_id}")
                return variant_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error assigning variant for experiment {experiment_id}: {e}")
            return None

    async def record_experiment_event(
        self,
        experiment_id: str,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Record an event for experiment analysis."""
        try:
            if experiment_id not in self.active_experiments:
                return False
            
            experiment = self.active_experiments[experiment_id]
            
            # Get user's variant assignment
            assignment_key = f"{experiment_id}_{user_id}"
            if assignment_key not in self.variant_assignments:
                return False
            
            variant_id = self.variant_assignments[assignment_key]
            
            # Create event record
            event_record = {
                'experiment_id': experiment_id,
                'variant_id': variant_id,
                'user_id': user_id,
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': timestamp or datetime.utcnow()
            }
            
            # Store event for analysis (this would typically go to a data warehouse)
            await self._store_experiment_event(event_record)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording experiment event: {e}")
            return False

    async def analyze_experiment(
        self,
        experiment_id: str,
        force_analysis: bool = False,
        db: Optional[AsyncSession] = None
    ) -> Optional[ExperimentResult]:
        """Analyze experiment results and determine statistical significance."""
        try:
            if experiment_id not in self.active_experiments:
                logger.error(f"Experiment {experiment_id} not found")
                return None
            
            experiment = self.active_experiments[experiment_id]
            
            # Check if analysis should be run
            if not force_analysis and experiment.status not in [ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED]:
                return experiment.results
            
            # Get experiment data
            experiment_data = await self._get_experiment_data(experiment_id, db)
            
            if not experiment_data or len(experiment_data) < 100:  # Minimum data threshold
                logger.warning(f"Insufficient data for analysis: {experiment_id}")
                return None
            
            # Analyze each target metric
            variant_results = {}
            statistical_significance = {}
            confidence_intervals = {}
            effect_sizes = {}
            p_values = {}
            sample_sizes = {}
            
            for metric in experiment.target_metrics:
                metric_analysis = await self._analyze_metric(
                    experiment_data, metric, experiment.variants, experiment.confidence_level
                )
                
                for variant_id, analysis in metric_analysis.items():
                    if variant_id not in variant_results:
                        variant_results[variant_id] = {}
                    
                    variant_results[variant_id][metric] = {
                        'mean': analysis['mean'],
                        'std': analysis['std'],
                        'count': analysis['count'],
                        'conversion_rate': analysis.get('conversion_rate'),
                        'percentiles': analysis.get('percentiles', {})
                    }
                    
                    # Store statistical test results
                    if 'control' in metric_analysis and variant_id != 'control':
                        test_key = f"{metric}_{variant_id}_vs_control"
                        statistical_significance[test_key] = analysis.get('significant', False)
                        confidence_intervals[test_key] = analysis.get('confidence_interval', (0, 0))
                        effect_sizes[test_key] = analysis.get('effect_size', 0)
                        p_values[test_key] = analysis.get('p_value', 1.0)
                    
                    sample_sizes[variant_id] = analysis['count']
            
            # Determine winner
            winner = await self._determine_experiment_winner(
                experiment, variant_results, statistical_significance, effect_sizes
            )
            
            # Generate recommendations
            recommendation = await self._generate_experiment_recommendation(
                experiment, variant_results, statistical_significance, winner
            )
            
            # Calculate business impact
            business_impact = await self._calculate_business_impact(
                experiment, variant_results, winner
            )
            
            # Create experiment result
            result = ExperimentResult(
                experiment_id=experiment_id,
                variant_results=variant_results,
                statistical_significance=statistical_significance,
                confidence_intervals=confidence_intervals,
                effect_sizes=effect_sizes,
                p_values=p_values,
                winner=winner,
                recommendation=recommendation,
                business_impact=business_impact,
                sample_sizes=sample_sizes,
                analysis_timestamp=datetime.utcnow()
            )
            
            # Update experiment with results
            experiment.results = result
            experiment.updated_at = datetime.utcnow()
            
            # Check if experiment should be stopped
            if await self._should_stop_experiment(experiment, result):
                await self.stop_experiment(experiment_id, "Stopping criteria met", db)
            
            # Persist results
            if db:
                await self._persist_experiment_results(result, db)
            
            logger.info(f"Analyzed experiment {experiment_id}: Winner = {winner}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing experiment {experiment_id}: {e}")
            return None

    async def stop_experiment(
        self,
        experiment_id: str,
        reason: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Stop a running experiment."""
        try:
            if experiment_id not in self.active_experiments:
                logger.error(f"Experiment {experiment_id} not found")
                return False
            
            experiment = self.active_experiments[experiment_id]
            
            if experiment.status not in [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]:
                logger.warning(f"Experiment {experiment_id} is not running")
                return False
            
            # Update experiment status
            experiment.status = ExperimentStatus.STOPPED
            experiment.updated_at = datetime.utcnow()
            experiment.actual_duration_days = (datetime.utcnow() - experiment.start_date).days if experiment.start_date else 0
            experiment.metadata['stop_reason'] = reason
            
            # Run final analysis
            if not experiment.results:
                await self.analyze_experiment(experiment_id, force_analysis=True, db=db)
            
            # Move to history
            self.experiment_history.append(experiment)
            if experiment_id in self.active_experiments:
                del self.active_experiments[experiment_id]
            
            # Persist changes
            if db:
                await self._update_experiment(experiment, db)
            
            logger.info(f"Stopped experiment {experiment_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping experiment {experiment_id}: {e}")
            return False

    async def get_experiment_status(
        self,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current status and progress of an experiment."""
        try:
            experiment = None
            
            # Check active experiments
            if experiment_id in self.active_experiments:
                experiment = self.active_experiments[experiment_id]
            else:
                # Check experiment history
                for hist_exp in self.experiment_history:
                    if hist_exp.experiment_id == experiment_id:
                        experiment = hist_exp
                        break
            
            if not experiment:
                return None
            
            # Calculate progress metrics
            total_required = sum(experiment.sample_size_required.values())
            total_achieved = sum(experiment.sample_size_achieved.values())
            progress_percent = (total_achieved / total_required * 100) if total_required > 0 else 0
            
            # Calculate time progress
            time_progress = 0
            if experiment.start_date and experiment.end_date:
                total_duration = (experiment.end_date - experiment.start_date).total_seconds()
                elapsed_duration = (datetime.utcnow() - experiment.start_date).total_seconds()
                time_progress = min(100, (elapsed_duration / total_duration * 100)) if total_duration > 0 else 0
            
            status_info = {
                'experiment_id': experiment_id,
                'name': experiment.name,
                'status': experiment.status.value,
                'experiment_type': experiment.experiment_type.value,
                'start_date': experiment.start_date.isoformat() if experiment.start_date else None,
                'end_date': experiment.end_date.isoformat() if experiment.end_date else None,
                'progress': {
                    'sample_progress_percent': min(100, progress_percent),
                    'time_progress_percent': time_progress,
                    'samples_collected': total_achieved,
                    'samples_required': total_required,
                    'days_elapsed': experiment.actual_duration_days or 0,
                    'days_planned': experiment.planned_duration_days
                },
                'variants': [
                    {
                        'variant_id': variant.variant_id,
                        'name': variant.name,
                        'traffic_allocation': variant.traffic_allocation,
                        'samples_achieved': experiment.sample_size_achieved.get(variant.variant_id, 0),
                        'samples_required': experiment.sample_size_required.get(variant.variant_id, 0)
                    }
                    for variant in experiment.variants
                ],
                'target_metrics': experiment.target_metrics,
                'has_results': experiment.results is not None,
                'winner': experiment.results.winner if experiment.results else None
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting experiment status: {e}")
            return None

    # Private helper methods
    
    async def _validate_experiment_config(
        self,
        variants: List[ExperimentVariant],
        target_metrics: List[str],
        duration_days: int
    ) -> Dict[str, Any]:
        """Validate experiment configuration."""
        errors = []
        
        # Check variants
        if len(variants) < 2:
            errors.append("At least 2 variants required")
        
        # Check traffic allocation
        total_allocation = sum(variant.traffic_allocation for variant in variants)
        if abs(total_allocation - 1.0) > 0.001:
            errors.append(f"Traffic allocation must sum to 1.0, got {total_allocation}")
        
        # Check for control variant
        has_control = any(variant.variant_type == VariantType.CONTROL for variant in variants)
        if not has_control:
            errors.append("At least one control variant required")
        
        # Check metrics
        if not target_metrics:
            errors.append("At least one target metric required")
        
        # Check duration
        if duration_days < 7 or duration_days > 90:
            errors.append("Duration must be between 7 and 90 days")
        
        return {'valid': len(errors) == 0, 'errors': errors}

    async def _calculate_sample_sizes(
        self,
        variants: List[ExperimentVariant],
        mde: float,
        power: float,
        confidence: float
    ) -> Dict[str, int]:
        """Calculate required sample sizes for statistical power."""
        try:
            # Simplified power analysis calculation
            # In practice, you would use more sophisticated statistical libraries
            
            alpha = 1 - confidence
            z_alpha = 1.96  # For 95% confidence
            z_beta = 0.84   # For 80% power
            
            # Assume baseline conversion rate of 20% for calculation
            p1 = 0.20
            p2 = p1 * (1 + mde)
            
            # Calculate sample size per variant
            pooled_p = (p1 + p2) / 2
            sample_size = 2 * ((z_alpha + z_beta) ** 2) * pooled_p * (1 - pooled_p) / ((p2 - p1) ** 2)
            sample_size = int(sample_size * 1.1)  # Add 10% buffer
            
            # Apply minimum and maximum constraints
            sample_size = max(self.experiment_config['minimum_sample_size'], sample_size)
            sample_size = min(self.experiment_config['maximum_sample_size'], sample_size)
            
            # Return sample size for each variant
            sample_sizes = {}
            for variant in variants:
                sample_sizes[variant.variant_id] = int(sample_size * variant.traffic_allocation)
            
            return sample_sizes
            
        except Exception as e:
            logger.error(f"Error calculating sample sizes: {e}")
            return {variant.variant_id: 1000 for variant in variants}

    async def _run_preflight_checks(self, experiment: Experiment) -> Dict[str, Any]:
        """Run preflight checks before starting experiment."""
        checks = []
        failures = []
        
        # Check model availability
        for variant in experiment.variants:
            # This would check if the model is deployed and healthy
            model_available = True  # Mock check
            if not model_available:
                failures.append(f"Model {variant.model_id} not available for variant {variant.variant_id}")
        
        # Check metric collection setup
        for metric in experiment.target_metrics:
            # This would verify metric collection is configured
            metric_configured = True  # Mock check
            if not metric_configured:
                failures.append(f"Metric {metric} collection not configured")
        
        # Check traffic capacity
        if len(self.active_experiments) >= self.experiment_config['max_concurrent_experiments']:
            failures.append("Maximum concurrent experiments limit reached")
        
        return {
            'passed': len(failures) == 0,
            'failures': failures
        }

    async def _check_user_eligibility(
        self,
        user_id: str,
        experiment: Experiment,
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if user is eligible for the experiment."""
        try:
            # Check inclusion criteria
            if experiment.inclusion_criteria:
                for criterion, value in experiment.inclusion_criteria.items():
                    if context and context.get(criterion) != value:
                        return False
            
            # Check exclusion criteria
            if experiment.exclusion_criteria:
                for criterion, value in experiment.exclusion_criteria.items():
                    if context and context.get(criterion) == value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking user eligibility: {e}")
            return True  # Default to eligible on error

    async def _assign_variant_by_strategy(
        self,
        user_id: str,
        experiment: Experiment,
        context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Assign variant based on traffic split strategy."""
        try:
            if experiment.traffic_split_strategy == TrafficSplitStrategy.RANDOM:
                # Use user_id hash for consistent random assignment
                hash_value = int(hashlib.md5(f"{user_id}_{experiment.experiment_id}".encode()).hexdigest(), 16)
                random_value = (hash_value % 10000) / 10000.0
                
                cumulative_allocation = 0
                for variant in experiment.variants:
                    cumulative_allocation += variant.traffic_allocation
                    if random_value <= cumulative_allocation:
                        return variant.variant_id
            
            elif experiment.traffic_split_strategy == TrafficSplitStrategy.USER_ID_HASH:
                # Similar to random but using a different hash seed
                hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                bucket = hash_value % len(experiment.variants)
                return experiment.variants[bucket].variant_id
            
            # Add other strategies as needed...
            
            # Default fallback
            return experiment.variants[0].variant_id if experiment.variants else None
            
        except Exception as e:
            logger.error(f"Error assigning variant: {e}")
            return None

    async def _get_experiment_data(
        self,
        experiment_id: str,
        db: Optional[AsyncSession]
    ) -> Optional[pd.DataFrame]:
        """Get experiment data for analysis."""
        try:
            # This would typically query a data warehouse or analytics database
            # For now, return mock data
            
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                return None
            
            # Generate mock experiment data
            np.random.seed(42)  # For reproducible results
            data = []
            
            for variant in experiment.variants:
                n_samples = experiment.sample_size_achieved.get(variant.variant_id, 100)
                
                for _ in range(n_samples):
                    # Mock user data
                    data.append({
                        'experiment_id': experiment_id,
                        'variant_id': variant.variant_id,
                        'user_id': f"user_{np.random.randint(1000000)}",
                        'conversion': np.random.choice([0, 1], p=[0.8, 0.2]),
                        'response_time': np.random.lognormal(5.0, 0.5),
                        'accuracy_score': np.random.beta(8, 2),
                        'user_satisfaction': np.random.normal(4.0, 1.0),
                        'timestamp': datetime.utcnow() - timedelta(days=np.random.randint(0, 14))
                    })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error getting experiment data: {e}")
            return None

    async def _analyze_metric(
        self,
        data: pd.DataFrame,
        metric: str,
        variants: List[ExperimentVariant],
        confidence_level: float
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze a specific metric across variants."""
        try:
            results = {}
            
            # Get control group for comparison
            control_variant = None
            for variant in variants:
                if variant.variant_type == VariantType.CONTROL:
                    control_variant = variant
                    break
            
            for variant in variants:
                variant_data = data[data['variant_id'] == variant.variant_id]
                
                if len(variant_data) == 0:
                    continue
                
                # Calculate basic statistics
                if metric in variant_data.columns:
                    metric_values = variant_data[metric].dropna()
                    
                    analysis = {
                        'mean': float(metric_values.mean()),
                        'std': float(metric_values.std()),
                        'count': len(metric_values),
                        'median': float(metric_values.median()),
                        'percentiles': {
                            '25': float(metric_values.quantile(0.25)),
                            '75': float(metric_values.quantile(0.75)),
                            '95': float(metric_values.quantile(0.95))
                        }
                    }
                    
                    # For binary metrics, calculate conversion rate
                    if metric == 'conversion':
                        analysis['conversion_rate'] = float(metric_values.mean())
                    
                    # Statistical comparison with control (if not control)
                    if control_variant and variant.variant_id != control_variant.variant_id:
                        control_data = data[data['variant_id'] == control_variant.variant_id]
                        if len(control_data) > 0 and metric in control_data.columns:
                            control_values = control_data[metric].dropna()
                            
                            # Perform t-test
                            from scipy import stats
                            try:
                                statistic, p_value = stats.ttest_ind(metric_values, control_values)
                                
                                analysis['p_value'] = float(p_value)
                                analysis['significant'] = p_value < (1 - confidence_level)
                                
                                # Effect size (Cohen's d)
                                pooled_std = np.sqrt(((len(metric_values) - 1) * metric_values.var() + 
                                                    (len(control_values) - 1) * control_values.var()) / 
                                                   (len(metric_values) + len(control_values) - 2))
                                
                                if pooled_std > 0:
                                    cohens_d = (metric_values.mean() - control_values.mean()) / pooled_std
                                    analysis['effect_size'] = float(cohens_d)
                                
                                # Confidence interval for difference
                                diff_mean = metric_values.mean() - control_values.mean()
                                diff_se = np.sqrt(metric_values.var()/len(metric_values) + control_values.var()/len(control_values))
                                
                                alpha = 1 - confidence_level
                                t_crit = stats.t.ppf(1 - alpha/2, len(metric_values) + len(control_values) - 2)
                                margin_error = t_crit * diff_se
                                
                                analysis['confidence_interval'] = (
                                    float(diff_mean - margin_error),
                                    float(diff_mean + margin_error)
                                )
                                
                            except Exception as test_error:
                                logger.error(f"Statistical test failed: {test_error}")
                                analysis['p_value'] = 1.0
                                analysis['significant'] = False
                    
                    results[variant.variant_id] = analysis
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing metric {metric}: {e}")
            return {}

    async def _determine_experiment_winner(
        self,
        experiment: Experiment,
        variant_results: Dict[str, Dict[str, Any]],
        statistical_significance: Dict[str, float],
        effect_sizes: Dict[str, float]
    ) -> Optional[str]:
        """Determine the winning variant based on results."""
        try:
            # Find control variant
            control_variant = None
            for variant in experiment.variants:
                if variant.variant_type == VariantType.CONTROL:
                    control_variant = variant.variant_id
                    break
            
            if not control_variant or control_variant not in variant_results:
                return None
            
            # Score each treatment variant
            variant_scores = {}
            
            for variant in experiment.variants:
                if variant.variant_id == control_variant:
                    continue
                
                score = 0
                metric_count = 0
                
                for metric in experiment.target_metrics:
                    test_key = f"{metric}_{variant.variant_id}_vs_control"
                    
                    if test_key in statistical_significance and statistical_significance[test_key]:
                        # Significant improvement
                        effect_size = effect_sizes.get(test_key, 0)
                        
                        # For conversion-type metrics, positive effect is good
                        if metric in ['conversion', 'accuracy_score', 'user_satisfaction']:
                            if effect_size > 0:
                                score += effect_size
                        # For latency/error metrics, negative effect is good
                        elif metric in ['response_time', 'error_rate']:
                            if effect_size < 0:
                                score += abs(effect_size)
                        
                        metric_count += 1
                
                if metric_count > 0:
                    variant_scores[variant.variant_id] = score / metric_count
            
            # Return variant with highest score, or None if no clear winner
            if variant_scores:
                winner = max(variant_scores.items(), key=lambda x: x[1])
                # Only declare winner if improvement is meaningful
                if winner[1] > 0.1:  # Minimum meaningful effect size
                    return winner[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error determining winner: {e}")
            return None

    async def _generate_experiment_recommendation(
        self,
        experiment: Experiment,
        variant_results: Dict[str, Dict[str, Any]],
        statistical_significance: Dict[str, float],
        winner: Optional[str]
    ) -> str:
        """Generate experiment recommendation."""
        try:
            if winner:
                winner_variant = next((v for v in experiment.variants if v.variant_id == winner), None)
                if winner_variant:
                    return f"Recommend deploying {winner_variant.name} ({winner}) as it showed statistically significant improvements"
            
            # Check if any variants showed promise
            promising_variants = []
            for variant in experiment.variants:
                if variant.variant_type == VariantType.CONTROL:
                    continue
                
                has_positive_signal = False
                for metric in experiment.target_metrics:
                    test_key = f"{metric}_{variant.variant_id}_vs_control"
                    if test_key in statistical_significance:
                        # Even if not significant, check for positive trend
                        variant_mean = variant_results.get(variant.variant_id, {}).get(metric, {}).get('mean', 0)
                        control_mean = variant_results.get('control', {}).get(metric, {}).get('mean', 0)
                        
                        if variant_mean > control_mean:
                            has_positive_signal = True
                            break
                
                if has_positive_signal:
                    promising_variants.append(variant.variant_id)
            
            if promising_variants:
                return f"No clear winner, but variants {promising_variants} show promise. Consider extending experiment or running follow-up tests."
            else:
                return "No significant improvements detected. Recommend keeping current implementation (control)."
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "Unable to generate recommendation due to analysis error."

    async def _calculate_business_impact(
        self,
        experiment: Experiment,
        variant_results: Dict[str, Dict[str, Any]],
        winner: Optional[str]
    ) -> Dict[str, float]:
        """Calculate estimated business impact of experiment results."""
        try:
            impact = {}
            
            if not winner:
                return impact
            
            # Mock business impact calculation
            # In practice, this would use business metrics and projections
            
            control_variant = None
            for variant in experiment.variants:
                if variant.variant_type == VariantType.CONTROL:
                    control_variant = variant.variant_id
                    break
            
            if control_variant and winner != control_variant:
                winner_results = variant_results.get(winner, {})
                control_results = variant_results.get(control_variant, {})
                
                for metric in experiment.target_metrics:
                    winner_value = winner_results.get(metric, {}).get('mean', 0)
                    control_value = control_results.get(metric, {}).get('mean', 0)
                    
                    if control_value > 0:
                        improvement = (winner_value - control_value) / control_value
                        
                        # Mock monetary impact calculation
                        if metric == 'conversion':
                            impact['revenue_increase_percent'] = improvement * 100
                            impact['estimated_annual_revenue_increase'] = improvement * 1000000  # Mock $1M baseline
                        elif metric == 'user_satisfaction':
                            impact['satisfaction_increase_percent'] = improvement * 100
                            impact['estimated_retention_improvement'] = improvement * 0.1  # Mock multiplier
            
            return impact
            
        except Exception as e:
            logger.error(f"Error calculating business impact: {e}")
            return {}

    async def _should_stop_experiment(self, experiment: Experiment, result: ExperimentResult) -> bool:
        """Determine if experiment should be stopped early."""
        try:
            if not self.experiment_config['early_stopping_enabled']:
                return False
            
            # Check if we have a clear winner with high confidence
            if result.winner and any(p < 0.01 for p in result.p_values.values()):
                significant_effects = [es for es in result.effect_sizes.values() if abs(es) > 0.2]
                if significant_effects:
                    return True
            
            # Check if experiment has run for minimum duration
            if experiment.start_date:
                days_running = (datetime.utcnow() - experiment.start_date).days
                if days_running >= experiment.planned_duration_days:
                    return True
            
            # Check if we've reached required sample sizes
            total_required = sum(experiment.sample_size_required.values())
            total_achieved = sum(experiment.sample_size_achieved.values())
            if total_achieved >= total_required:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking stopping criteria: {e}")
            return False

    # Additional helper methods for persistence, monitoring, etc.
    
    async def _persist_experiment(self, experiment: Experiment, db: AsyncSession) -> None:
        """Persist experiment to database."""
        try:
            # This would typically involve database operations
            logger.debug(f"Persisting experiment {experiment.experiment_id} to database")
        except Exception as e:
            logger.error(f"Error persisting experiment: {e}")

    async def _update_experiment(self, experiment: Experiment, db: AsyncSession) -> None:
        """Update experiment in database."""
        try:
            logger.debug(f"Updating experiment {experiment.experiment_id} in database")
        except Exception as e:
            logger.error(f"Error updating experiment: {e}")

    async def _persist_experiment_results(self, result: ExperimentResult, db: AsyncSession) -> None:
        """Persist experiment results to database."""
        try:
            logger.debug(f"Persisting results for experiment {result.experiment_id} to database")
        except Exception as e:
            logger.error(f"Error persisting results: {e}")

    async def _store_experiment_event(self, event: Dict[str, Any]) -> None:
        """Store experiment event for analysis."""
        try:
            # This would typically go to a data warehouse or event store
            logger.debug(f"Storing experiment event: {event['event_type']}")
        except Exception as e:
            logger.error(f"Error storing experiment event: {e}")

    async def _start_experiment_monitoring(self, experiment: Experiment) -> None:
        """Start monitoring for the experiment."""
        try:
            # This would set up monitoring dashboards, alerts, etc.
            logger.debug(f"Started monitoring for experiment {experiment.experiment_id}")
        except Exception as e:
            logger.error(f"Error starting experiment monitoring: {e}")