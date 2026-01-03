"""
AI Training Pipeline System

Comprehensive training pipeline for continuous AI improvement including
feedback aggregation, dataset generation, model fine-tuning, A/B testing,
gradual rollout, and performance monitoring.
"""

import asyncio
import json
import logging
import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import pickle
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import torch
import transformers
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    Trainer, TrainingArguments, EarlyStoppingCallback
)
from datasets import Dataset
import mlflow
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import joblib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import schedule
import time
import sys
import os

# Add the src directory to the path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feedback.collector import FeedbackCollector, AIModelType, FeedbackType

logger = logging.getLogger(__name__)


class TrainingStatus(Enum):
    """Training job status"""
    PENDING = "pending"
    PREPARING_DATA = "preparing_data"
    TRAINING = "training"
    VALIDATING = "validating"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelType(Enum):
    """Model types for training"""
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"


class DeploymentStrategy(Enum):
    """Model deployment strategies"""
    IMMEDIATE = "immediate"
    GRADUAL_ROLLOUT = "gradual_rollout"
    A_B_TEST = "a_b_test"
    CANARY = "canary"
    MANUAL_APPROVAL = "manual_approval"


@dataclass
class TrainingConfig:
    """Configuration for training jobs"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = ""
    model_type: ModelType = ModelType.CLASSIFICATION
    base_model: str = "bert-base-uncased"
    training_args: Dict[str, Any] = field(default_factory=dict)
    data_filters: Dict[str, Any] = field(default_factory=dict)
    validation_split: float = 0.2
    test_split: float = 0.1
    max_samples: Optional[int] = None
    quality_threshold: float = 0.8
    early_stopping_patience: int = 3
    evaluation_metrics: List[str] = field(default_factory=lambda: ["accuracy", "f1", "precision", "recall"])
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.GRADUAL_ROLLOUT
    rollout_percentage: float = 0.1
    success_threshold: float = 0.95
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TrainingJob:
    """Training job data structure"""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: TrainingConfig = field(default_factory=TrainingConfig)
    status: TrainingStatus = TrainingStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    model_path: Optional[str] = None
    dataset_info: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ModelVersion:
    """Model version information"""
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = ""
    version_number: str = ""
    model_type: ModelType = ModelType.CLASSIFICATION
    training_job_id: str = ""
    model_path: str = ""
    config_path: str = ""
    tokenizer_path: str = ""
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    training_data_hash: str = ""
    deployment_status: str = "pending"  # pending, deployed, deprecated, rollback
    deployment_percentage: float = 0.0
    a_b_test_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deployed_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None


@dataclass
class ABTestResult:
    """A/B test result data"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_a_version: str = ""
    model_b_version: str = ""
    test_duration_hours: int = 24
    traffic_split: Dict[str, float] = field(default_factory=lambda: {"a": 0.5, "b": 0.5})
    metrics_a: Dict[str, float] = field(default_factory=dict)
    metrics_b: Dict[str, float] = field(default_factory=dict)
    statistical_significance: Dict[str, float] = field(default_factory=dict)
    winner: Optional[str] = None
    confidence_level: float = 0.0
    sample_size_a: int = 0
    sample_size_b: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, cancelled


@dataclass
class ContinuousLearningMetrics:
    """Metrics for continuous learning system"""
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_version: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accuracy_improvement: float = 0.0
    false_positive_reduction: float = 0.0
    false_negative_reduction: float = 0.0
    user_satisfaction_increase: float = 0.0
    processing_time_improvement: float = 0.0
    feedback_volume: int = 0
    training_iterations: int = 0
    deployment_success_rate: float = 0.0


class TrainingPipeline:
    """
    Comprehensive AI training pipeline system

    Features:
    - Automated feedback aggregation and dataset generation
    - Model fine-tuning with hyperparameter optimization
    - A/B testing and gradual rollout strategies
    - Performance monitoring and rollback capabilities
    - Continuous learning integration
    - Model versioning and lifecycle management
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pipeline_db_path = config.get('pipeline_db_path', 'data/training_pipeline.db')
        self.models_dir = Path(config.get('models_dir', 'models'))
        self.models_dir.mkdir(exist_ok=True)

        # Training configuration
        self.feedback_db_path = config.get('feedback_db_path', 'data/ai_feedback.db')
        self.batch_size = config.get('batch_size', 100)
        self.training_frequency = config.get('training_frequency', 'weekly')
        self.auto_deploy_threshold = config.get('auto_deploy_threshold', 0.95)

        # MLOps integration
        self.use_mlflow = config.get('use_mlflow', True)
        self.mlflow_tracking_uri = config.get('mlflow_tracking_uri', 'sqlite:///mlflow.db')

        # Initialize components
        self._init_pipeline_database()
        self._init_mlops()

        # Job queue and execution
        self.job_queue = []
        self.active_jobs = {}
        self.executor = ThreadPoolExecutor(max_workers=config.get('max_concurrent_jobs', 2))

        # Feedback collector integration
        self.feedback_collector = None
        self._init_feedback_integration()

        # Performance monitoring
        self.performance_cache = {}
        self.cache_duration = timedelta(minutes=30)

        # Continuous learning
        self.learning_enabled = config.get('continuous_learning_enabled', True)
        self.learning_threshold = config.get('learning_threshold', 50)  # Min feedback items

    def _init_pipeline_database(self):
        """Initialize training pipeline database"""
        logger.info("Initializing training pipeline database...")

        Path(self.pipeline_db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            # Training jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_jobs (
                    job_id TEXT PRIMARY KEY,
                    config TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    progress REAL DEFAULT 0.0,
                    current_step TEXT,
                    total_steps INTEGER DEFAULT 0,
                    completed_steps INTEGER DEFAULT 0,
                    metrics TEXT,
                    logs TEXT,
                    error_message TEXT,
                    model_path TEXT,
                    dataset_info TEXT,
                    created_at TIMESTAMP NOT NULL
                )
            """)

            # Model versions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    version_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    version_number TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    training_job_id TEXT NOT NULL,
                    model_path TEXT NOT NULL,
                    config_path TEXT,
                    tokenizer_path TEXT,
                    performance_metrics TEXT,
                    training_data_hash TEXT,
                    deployment_status TEXT DEFAULT 'pending',
                    deployment_percentage REAL DEFAULT 0.0,
                    a_b_test_id TEXT,
                    created_at TIMESTAMP NOT NULL,
                    deployed_at TIMESTAMP,
                    deprecated_at TIMESTAMP,
                    FOREIGN KEY (training_job_id) REFERENCES training_jobs (job_id)
                )
            """)

            # A/B tests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_tests (
                    test_id TEXT PRIMARY KEY,
                    model_a_version TEXT NOT NULL,
                    model_b_version TEXT NOT NULL,
                    test_duration_hours INTEGER DEFAULT 24,
                    traffic_split TEXT,
                    metrics_a TEXT,
                    metrics_b TEXT,
                    statistical_significance TEXT,
                    winner TEXT,
                    confidence_level REAL,
                    sample_size_a INTEGER DEFAULT 0,
                    sample_size_b INTEGER DEFAULT 0,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    FOREIGN KEY (model_a_version) REFERENCES model_versions (version_id),
                    FOREIGN KEY (model_b_version) REFERENCES model_versions (version_id)
                )
            """)

            # Performance monitoring table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    accuracy REAL,
                    precision_score REAL,
                    recall REAL,
                    f1_score REAL,
                    response_time_ms REAL,
                    throughput_requests_per_second REAL,
                    error_rate REAL,
                    user_satisfaction REAL,
                    feedback_count INTEGER DEFAULT 0,
                    FOREIGN KEY (version_id) REFERENCES model_versions (version_id)
                )
            """)

            # Training schedules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    next_run TIMESTAMP NOT NULL,
                    config TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    last_run TIMESTAMP,
                    created_at TIMESTAMP NOT NULL
                )
            """)

            # Continuous learning metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS continuous_learning_metrics (
                    metric_id TEXT PRIMARY KEY,
                    model_version TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    accuracy_improvement REAL DEFAULT 0.0,
                    false_positive_reduction REAL DEFAULT 0.0,
                    false_negative_reduction REAL DEFAULT 0.0,
                    user_satisfaction_increase REAL DEFAULT 0.0,
                    processing_time_improvement REAL DEFAULT 0.0,
                    feedback_volume INTEGER DEFAULT 0,
                    training_iterations INTEGER DEFAULT 0,
                    deployment_success_rate REAL DEFAULT 0.0
                )
            """)

            # Model improvement tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_improvements (
                    improvement_id TEXT PRIMARY KEY,
                    baseline_version TEXT NOT NULL,
                    improved_version TEXT NOT NULL,
                    improvement_type TEXT NOT NULL,
                    metrics_before TEXT,
                    metrics_after TEXT,
                    improvement_score REAL,
                    feedback_sources TEXT,
                    created_at TIMESTAMP NOT NULL
                )
            """)

            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_jobs_status ON training_jobs(status)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_created ON training_jobs(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_versions_model ON model_versions(model_name)",
                "CREATE INDEX IF NOT EXISTS idx_versions_status ON model_versions(deployment_status)",
                "CREATE INDEX IF NOT EXISTS idx_tests_status ON ab_tests(status)",
                "CREATE INDEX IF NOT EXISTS idx_performance_version ON model_performance_history(version_id)",
                "CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON model_performance_history(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_learning_metrics_version ON continuous_learning_metrics(model_version)",
                "CREATE INDEX IF NOT EXISTS idx_improvements_baseline ON model_improvements(baseline_version)"
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

            conn.commit()
            logger.info("✓ Training pipeline database initialized")

        finally:
            conn.close()

    def _init_mlops(self):
        """Initialize MLOps tracking"""
        if self.use_mlflow:
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)
            mlflow.set_experiment("legal-ai-training")

    def _init_feedback_integration(self):
        """Initialize feedback collector integration"""
        try:
            feedback_config = {
                "feedback_db_path": self.feedback_db_path,
                "min_quality_threshold": 0.7,
                "auto_training_enabled": True
            }
            self.feedback_collector = FeedbackCollector(feedback_config)
        except Exception as e:
            logger.warning(f"Could not initialize feedback collector: {str(e)}")

    async def aggregate_feedback_weekly(self) -> Dict[str, Any]:
        """Aggregate feedback data for weekly training"""
        logger.info("Aggregating weekly feedback data...")

        if not self.feedback_collector:
            logger.error("Feedback collector not initialized")
            return {}

        try:
            # Get training data from feedback collector
            training_data = await self.feedback_collector.get_training_data(
                processed=False, limit=self.batch_size
            )

            if not training_data:
                logger.info("No new training data available")
                return {}

            # Group by model type
            data_by_model = defaultdict(list)
            for item in training_data:
                data_by_model[item['model_type']].append(item)

            aggregation_summary = {
                'total_items': len(training_data),
                'items_by_model': {model: len(items) for model, items in data_by_model.items()},
                'quality_distribution': self._analyze_quality_distribution(training_data),
                'priority_distribution': self._analyze_priority_distribution(training_data),
                'feedback_types': self._analyze_feedback_types(training_data),
                'aggregation_timestamp': datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"Aggregated {len(training_data)} training items from {len(data_by_model)} model types")
            return aggregation_summary

        except Exception as e:
            logger.error(f"Error aggregating feedback: {str(e)}")
            return {}

    def _analyze_quality_distribution(self, training_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze quality score distribution"""
        quality_ranges = {
            'high_quality': 0,      # 0.9+
            'good_quality': 0,      # 0.8-0.89
            'medium_quality': 0,    # 0.7-0.79
            'low_quality': 0        # <0.7
        }

        for item in training_data:
            quality = item.get('quality_score', 0)
            if quality >= 0.9:
                quality_ranges['high_quality'] += 1
            elif quality >= 0.8:
                quality_ranges['good_quality'] += 1
            elif quality >= 0.7:
                quality_ranges['medium_quality'] += 1
            else:
                quality_ranges['low_quality'] += 1

        return quality_ranges

    def _analyze_priority_distribution(self, training_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze priority distribution"""
        priority_counts = Counter(item.get('priority', 1) for item in training_data)
        return dict(priority_counts)

    def _analyze_feedback_types(self, training_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze feedback type distribution"""
        feedback_counts = Counter(item.get('feedback_type', 'unknown') for item in training_data)
        return dict(feedback_counts)

    async def generate_training_datasets(self, model_type: AIModelType) -> Dict[str, Dataset]:
        """Generate training datasets from aggregated feedback"""
        logger.info(f"Generating training datasets for {model_type.value}...")

        if not self.feedback_collector:
            raise ValueError("Feedback collector not initialized")

        # Get training data
        training_data = await self.feedback_collector.get_training_data(
            processed=False, limit=10000
        )

        # Filter by model type
        filtered_data = [
            item for item in training_data
            if item['model_type'] == model_type.value
        ]

        if len(filtered_data) < 50:
            raise ValueError(f"Insufficient training data for {model_type.value}: {len(filtered_data)} items")

        # Prepare dataset
        inputs = []
        labels = []
        for item in filtered_data:
            inputs.append(item['input_data'])
            labels.append(item['expected_output'])

        # Create dataset
        dataset_dict = {
            'input_text': inputs,
            'labels': labels,
            'quality_scores': [item['quality_score'] for item in filtered_data],
            'feedback_types': [item['feedback_type'] for item in filtered_data],
            'queue_ids': [item['queue_id'] for item in filtered_data]
        }

        dataset = Dataset.from_dict(dataset_dict)

        # Split dataset
        total_size = len(dataset)
        test_size = int(total_size * 0.1)
        val_size = int(total_size * 0.2)
        train_size = total_size - test_size - val_size

        train_dataset = dataset.select(range(train_size))
        val_dataset = dataset.select(range(train_size, train_size + val_size))
        test_dataset = dataset.select(range(train_size + val_size, total_size))

        logger.info(f"Dataset created: {train_size} train, {val_size} val, {test_size} test samples")

        return {
            'train': train_dataset,
            'validation': val_dataset,
            'test': test_dataset,
            'queue_ids': [item['queue_id'] for item in filtered_data]
        }

    async def fine_tune_model(self, config: TrainingConfig) -> ModelVersion:
        """Fine-tune model with feedback data"""
        logger.info(f"Starting model fine-tuning: {config.model_name}")

        job = TrainingJob(config=config)

        try:
            # Update job status
            job.status = TrainingStatus.PREPARING_DATA
            job.start_time = datetime.now(timezone.utc)
            await self._save_training_job(job)

            # Start MLflow run
            if self.use_mlflow:
                mlflow.start_run(run_name=f"training-{config.model_name}-{job.job_id[:8]}")
                mlflow.log_params(asdict(config))

            # Generate dataset
            model_type = getattr(AIModelType, config.model_name.upper(), AIModelType.DOCUMENT_ANALYZER)
            dataset_info = await self.generate_training_datasets(model_type)

            job.dataset_info = {
                'train_size': len(dataset_info['train']),
                'val_size': len(dataset_info['validation']),
                'test_size': len(dataset_info['test'])
            }

            # Load model and tokenizer
            job.status = TrainingStatus.TRAINING
            job.current_step = "Loading model and tokenizer"
            await self._update_training_job(job)

            tokenizer = AutoTokenizer.from_pretrained(config.base_model)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Determine number of labels for classification
            unique_labels = set(dataset_info['train']['labels'])
            num_labels = len(unique_labels)

            model = AutoModelForSequenceClassification.from_pretrained(
                config.base_model,
                num_labels=num_labels
            )

            # Tokenize dataset
            def tokenize_function(examples):
                return tokenizer(
                    examples['input_text'],
                    truncation=True,
                    padding=True,
                    max_length=512
                )

            train_dataset = dataset_info['train'].map(tokenize_function, batched=True)
            val_dataset = dataset_info['validation'].map(tokenize_function, batched=True)
            test_dataset = dataset_info['test'].map(tokenize_function, batched=True)

            # Create label mapping
            label_to_id = {label: idx for idx, label in enumerate(sorted(unique_labels))}
            id_to_label = {idx: label for label, idx in label_to_id.items()}

            def encode_labels(examples):
                return {'labels': [label_to_id[label] for label in examples['labels']]}

            train_dataset = train_dataset.map(encode_labels, batched=True)
            val_dataset = val_dataset.map(encode_labels, batched=True)
            test_dataset = test_dataset.map(encode_labels, batched=True)

            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.models_dir / job.job_id),
                num_train_epochs=config.training_args.get('num_epochs', 3),
                per_device_train_batch_size=config.training_args.get('batch_size', 16),
                per_device_eval_batch_size=config.training_args.get('eval_batch_size', 16),
                warmup_steps=config.training_args.get('warmup_steps', 500),
                weight_decay=config.training_args.get('weight_decay', 0.01),
                logging_dir=str(self.models_dir / job.job_id / 'logs'),
                logging_steps=config.training_args.get('logging_steps', 10),
                evaluation_strategy="steps",
                eval_steps=config.training_args.get('eval_steps', 500),
                save_steps=config.training_args.get('save_steps', 500),
                load_best_model_at_end=True,
                metric_for_best_model="eval_accuracy",
                greater_is_better=True,
                save_total_limit=3,
                report_to=["mlflow"] if self.use_mlflow else []
            )

            # Training metrics
            def compute_metrics(eval_pred):
                predictions, labels = eval_pred
                predictions = np.argmax(predictions, axis=1)

                precision, recall, f1, _ = precision_recall_fscore_support(
                    labels, predictions, average='weighted'
                )
                accuracy = accuracy_score(labels, predictions)

                return {
                    'accuracy': accuracy,
                    'f1': f1,
                    'precision': precision,
                    'recall': recall
                }

            # Create trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                compute_metrics=compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)]
            )

            # Train model
            job.current_step = "Training model"
            job.total_steps = len(train_dataset) // training_args.per_device_train_batch_size * training_args.num_train_epochs
            await self._update_training_job(job)

            training_result = trainer.train()

            # Evaluate model
            job.status = TrainingStatus.VALIDATING
            job.current_step = "Evaluating model"
            await self._update_training_job(job)

            eval_results = trainer.evaluate(eval_dataset=test_dataset)

            # Save model
            model_path = self.models_dir / job.job_id / "final_model"
            model_path.mkdir(parents=True, exist_ok=True)

            trainer.save_model(str(model_path))
            tokenizer.save_pretrained(str(model_path))

            # Save configuration and label mapping
            config_path = model_path / "training_config.json"
            with open(config_path, 'w') as f:
                json.dump(asdict(config), f, indent=2, default=str)

            label_mapping_path = model_path / "label_mapping.json"
            with open(label_mapping_path, 'w') as f:
                json.dump({"label_to_id": label_to_id, "id_to_label": id_to_label}, f, indent=2)

            # Create model version
            version = ModelVersion(
                model_name=config.model_name,
                version_number=f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_type=config.model_type,
                training_job_id=job.job_id,
                model_path=str(model_path),
                config_path=str(config_path),
                tokenizer_path=str(model_path),
                performance_metrics=eval_results,
                training_data_hash=self._calculate_data_hash(dataset_info['queue_ids'])
            )

            # Save model version
            await self._save_model_version(version)

            # Mark training data as processed
            if self.feedback_collector:
                await self.feedback_collector.mark_training_data_processed(
                    dataset_info['queue_ids'], job.job_id
                )

            # Update job completion
            job.status = TrainingStatus.COMPLETED
            job.end_time = datetime.now(timezone.utc)
            job.progress = 1.0
            job.metrics = eval_results
            job.model_path = str(model_path)
            await self._update_training_job(job)

            # Log to MLflow
            if self.use_mlflow:
                mlflow.log_metrics(eval_results)
                mlflow.log_artifact(str(model_path))
                mlflow.end_run()

            logger.info(f"Model fine-tuning completed: {job.job_id}")

            # Determine deployment strategy
            if (eval_results.get('eval_accuracy', 0) >= self.auto_deploy_threshold and
                config.deployment_strategy == DeploymentStrategy.IMMEDIATE):
                await self.deploy_model_version(version.version_id)
            elif config.deployment_strategy == DeploymentStrategy.A_B_TEST:
                await self.start_ab_test(version.version_id)

            return version

        except Exception as e:
            logger.error(f"Model fine-tuning failed: {job.job_id}, error: {str(e)}")
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            job.end_time = datetime.now(timezone.utc)
            await self._update_training_job(job)

            if self.use_mlflow:
                mlflow.end_run(status="FAILED")

            raise

    def _calculate_data_hash(self, queue_ids: List[str]) -> str:
        """Calculate hash of training data for versioning"""
        queue_ids_str = ''.join(sorted(queue_ids))
        return hashlib.sha256(queue_ids_str.encode()).hexdigest()

    async def start_ab_test(self, new_version_id: str, control_version_id: str = None) -> str:
        """Start A/B test between model versions"""
        if not control_version_id:
            # Use current production model as control
            control_version_id = await self._get_current_production_version()

        if not control_version_id:
            logger.warning("No control version available for A/B test")
            return None

        ab_test = ABTestResult(
            model_a_version=control_version_id,
            model_b_version=new_version_id,
            test_duration_hours=24,
            traffic_split={"a": 0.8, "b": 0.2}  # Start with 20% traffic to new model
        )

        # Save A/B test
        await self._save_ab_test(ab_test)

        logger.info(f"A/B test started: {ab_test.test_id}")
        return ab_test.test_id

    async def gradual_rollout(self, version_id: str) -> bool:
        """Implement gradual rollout with performance monitoring"""
        rollout_percentages = [10, 25, 50, 75, 100]
        rollout_interval_hours = 24

        for percentage in rollout_percentages:
            # Deploy to percentage of traffic
            success = await self.deploy_model_version(version_id, percentage)
            if not success:
                logger.error(f"Failed to deploy to {percentage}%")
                return False

            # Wait for monitoring interval (simulated)
            await asyncio.sleep(5)  # In production, this would be hours

            # Monitor performance
            performance = await self.monitor_model_performance(version_id)

            # Check if performance meets thresholds
            if not self._meets_performance_thresholds(performance):
                logger.warning(f"Performance degradation at {percentage}% rollout")
                await self.rollback_model(version_id, "Performance degradation")
                return False

            logger.info(f"Successfully deployed to {percentage}%")

        return True

    def _meets_performance_thresholds(self, performance: Dict[str, float]) -> bool:
        """Check if performance meets minimum thresholds"""
        thresholds = {
            'accuracy': 0.85,
            'f1_score': 0.80,
            'user_satisfaction': 0.75
        }

        for metric, threshold in thresholds.items():
            if performance.get(metric, 0) < threshold:
                return False
        return True

    async def deploy_model_version(self, version_id: str, percentage: float = 100.0) -> bool:
        """Deploy model version with specified traffic percentage"""
        try:
            # Update deployment status
            conn = sqlite3.connect(self.pipeline_db_path)
            try:
                conn.execute("""
                    UPDATE model_versions
                    SET deployment_status = 'deployed',
                        deployment_percentage = ?,
                        deployed_at = ?
                    WHERE version_id = ?
                """, (percentage, datetime.now(timezone.utc).isoformat(), version_id))
                conn.commit()

            finally:
                conn.close()

            # If this is a full deployment, deprecate previous versions
            if percentage >= 100.0:
                await self._deprecate_previous_versions(version_id)

            logger.info(f"Model version deployed: {version_id} at {percentage}%")
            return True

        except Exception as e:
            logger.error(f"Failed to deploy model version {version_id}: {str(e)}")
            return False

    async def _deprecate_previous_versions(self, current_version_id: str):
        """Deprecate previous versions of the same model"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            # Get model name for current version
            cursor = conn.execute("""
                SELECT model_name FROM model_versions WHERE version_id = ?
            """, (current_version_id,))
            result = cursor.fetchone()

            if result:
                model_name = result[0]

                # Deprecate other deployed versions of the same model
                conn.execute("""
                    UPDATE model_versions
                    SET deployment_status = 'deprecated',
                        deprecated_at = ?
                    WHERE model_name = ? AND version_id != ? AND deployment_status = 'deployed'
                """, (datetime.now(timezone.utc).isoformat(), model_name, current_version_id))
                conn.commit()

        finally:
            conn.close()

    async def monitor_model_performance(self, version_id: str) -> Dict[str, float]:
        """Monitor deployed model performance"""
        # This would integrate with your production monitoring system
        # For now, we'll return simulated metrics
        performance_metrics = {
            'accuracy': 0.92 + np.random.normal(0, 0.02),
            'precision': 0.89 + np.random.normal(0, 0.02),
            'recall': 0.94 + np.random.normal(0, 0.02),
            'f1_score': 0.91 + np.random.normal(0, 0.02),
            'response_time_ms': 150.0 + np.random.normal(0, 20),
            'throughput_rps': 45.0 + np.random.normal(0, 5),
            'error_rate': max(0, 0.02 + np.random.normal(0, 0.005)),
            'user_satisfaction': 0.88 + np.random.normal(0, 0.05)
        }

        # Store performance history
        await self._store_performance_metrics(version_id, performance_metrics)

        return performance_metrics

    async def _store_performance_metrics(self, version_id: str, metrics: Dict[str, float]):
        """Store performance metrics in database"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            conn.execute("""
                INSERT INTO model_performance_history (
                    version_id, timestamp, accuracy, precision_score, recall,
                    f1_score, response_time_ms, throughput_requests_per_second,
                    error_rate, user_satisfaction
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version_id, datetime.now(timezone.utc).isoformat(),
                metrics['accuracy'], metrics['precision'],
                metrics['recall'], metrics['f1_score'],
                metrics['response_time_ms'], metrics['throughput_rps'],
                metrics['error_rate'], metrics['user_satisfaction']
            ))
            conn.commit()

        finally:
            conn.close()

    async def rollback_model(self, version_id: str, reason: str) -> bool:
        """Rollback model to previous stable version"""
        try:
            # Get model name
            conn = sqlite3.connect(self.pipeline_db_path)
            try:
                cursor = conn.execute("""
                    SELECT model_name FROM model_versions WHERE version_id = ?
                """, (version_id,))
                result = cursor.fetchone()

                if not result:
                    logger.error(f"Model version not found: {version_id}")
                    return False

                model_name = result[0]

                # Find previous stable version
                cursor = conn.execute("""
                    SELECT version_id FROM model_versions
                    WHERE model_name = ? AND deployment_status = 'deprecated'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (model_name,))

                rollback_result = cursor.fetchone()
                if not rollback_result:
                    logger.error(f"No previous version found for rollback: {model_name}")
                    return False

                rollback_version_id = rollback_result[0]

                # Update deployment status
                conn.execute("""
                    UPDATE model_versions
                    SET deployment_status = 'rollback'
                    WHERE version_id = ?
                """, (version_id,))

                conn.execute("""
                    UPDATE model_versions
                    SET deployment_status = 'deployed',
                        deployment_percentage = 100.0,
                        deployed_at = ?
                    WHERE version_id = ?
                """, (datetime.now(timezone.utc).isoformat(), rollback_version_id))

                conn.commit()

            finally:
                conn.close()

            logger.warning(f"Model rolled back: {version_id} -> {rollback_version_id}, reason: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback model {version_id}: {str(e)}")
            return False

    async def continuous_learning_cycle(self):
        """Run continuous learning cycle"""
        if not self.learning_enabled:
            return

        logger.info("Starting continuous learning cycle")

        try:
            # Check for new feedback
            if self.feedback_collector:
                training_data = await self.feedback_collector.get_training_data(
                    processed=False, limit=self.learning_threshold
                )

                if len(training_data) >= self.learning_threshold:
                    logger.info(f"Found {len(training_data)} new training items, starting improvement cycle")

                    # Group by model type and start training jobs
                    data_by_model = defaultdict(list)
                    for item in training_data:
                        data_by_model[item['model_type']].append(item)

                    for model_type, items in data_by_model.items():
                        if len(items) >= 20:  # Minimum for model improvement
                            config = TrainingConfig(
                                model_name=model_type,
                                model_type=ModelType.CLASSIFICATION,
                                base_model="bert-base-uncased",
                                deployment_strategy=DeploymentStrategy.A_B_TEST,
                                quality_threshold=0.8
                            )

                            try:
                                version = await self.fine_tune_model(config)
                                await self._track_continuous_learning_metrics(version)
                                logger.info(f"Continuous learning completed for {model_type}")
                            except Exception as e:
                                logger.error(f"Continuous learning failed for {model_type}: {str(e)}")

        except Exception as e:
            logger.error(f"Continuous learning cycle failed: {str(e)}")

    async def _track_continuous_learning_metrics(self, version: ModelVersion):
        """Track metrics for continuous learning"""
        # Get baseline metrics (previous version)
        baseline_metrics = await self._get_baseline_metrics(version.model_name)

        # Calculate improvements
        accuracy_improvement = version.performance_metrics.get('eval_accuracy', 0) - baseline_metrics.get('accuracy', 0)

        # Create continuous learning metrics
        cl_metrics = ContinuousLearningMetrics(
            model_version=version.version_id,
            accuracy_improvement=accuracy_improvement,
            false_positive_reduction=0.0,  # Would be calculated from feedback data
            false_negative_reduction=0.0,  # Would be calculated from feedback data
            user_satisfaction_increase=0.0,  # Would be calculated from user ratings
            processing_time_improvement=0.0,  # Would be measured in production
            feedback_volume=100,  # Would be actual count
            training_iterations=1,
            deployment_success_rate=1.0 if accuracy_improvement > 0 else 0.0
        )

        # Store metrics
        await self._save_continuous_learning_metrics(cl_metrics)

    async def _get_baseline_metrics(self, model_name: str) -> Dict[str, float]:
        """Get baseline metrics for comparison"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            cursor = conn.execute("""
                SELECT performance_metrics FROM model_versions
                WHERE model_name = ? AND deployment_status = 'deployed'
                ORDER BY created_at DESC
                LIMIT 1
            """, (model_name,))

            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return {}

        finally:
            conn.close()

    async def _save_continuous_learning_metrics(self, metrics: ContinuousLearningMetrics):
        """Save continuous learning metrics"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            conn.execute("""
                INSERT INTO continuous_learning_metrics (
                    metric_id, model_version, timestamp, accuracy_improvement,
                    false_positive_reduction, false_negative_reduction,
                    user_satisfaction_increase, processing_time_improvement,
                    feedback_volume, training_iterations, deployment_success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.metric_id, metrics.model_version, metrics.timestamp.isoformat(),
                metrics.accuracy_improvement, metrics.false_positive_reduction,
                metrics.false_negative_reduction, metrics.user_satisfaction_increase,
                metrics.processing_time_improvement, metrics.feedback_volume,
                metrics.training_iterations, metrics.deployment_success_rate
            ))
            conn.commit()

        finally:
            conn.close()

    async def schedule_training(self, model_name: str, frequency: str, config: TrainingConfig):
        """Schedule automated training"""
        schedule_id = str(uuid.uuid4())

        # Calculate next run time
        if frequency == 'daily':
            next_run = datetime.now(timezone.utc) + timedelta(days=1)
        elif frequency == 'weekly':
            next_run = datetime.now(timezone.utc) + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_run = datetime.now(timezone.utc) + timedelta(days=30)
        else:
            raise ValueError(f"Unsupported frequency: {frequency}")

        # Save schedule
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            conn.execute("""
                INSERT INTO training_schedules (
                    schedule_id, model_name, frequency, next_run, config, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                schedule_id, model_name, frequency, next_run.isoformat(),
                json.dumps(asdict(config), default=str),
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

        finally:
            conn.close()

        logger.info(f"Training scheduled: {model_name} every {frequency}")
        return schedule_id

    async def _save_training_job(self, job: TrainingJob):
        """Save training job to database"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            conn.execute("""
                INSERT INTO training_jobs (
                    job_id, config, status, start_time, current_step, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                json.dumps(asdict(job.config), default=str),
                job.status.value,
                job.start_time.isoformat() if job.start_time else None,
                job.current_step,
                job.created_at.isoformat()
            ))
            conn.commit()

        finally:
            conn.close()

    async def _update_training_job(self, job: TrainingJob):
        """Update training job status in database"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            conn.execute("""
                UPDATE training_jobs
                SET status = ?, start_time = ?, end_time = ?, progress = ?,
                    current_step = ?, total_steps = ?, completed_steps = ?,
                    metrics = ?, logs = ?, error_message = ?, model_path = ?,
                    dataset_info = ?
                WHERE job_id = ?
            """, (
                job.status.value,
                job.start_time.isoformat() if job.start_time else None,
                job.end_time.isoformat() if job.end_time else None,
                job.progress,
                job.current_step,
                job.total_steps,
                job.completed_steps,
                json.dumps(job.metrics),
                json.dumps(job.logs),
                job.error_message,
                job.model_path,
                json.dumps(job.dataset_info),
                job.job_id
            ))
            conn.commit()

        finally:
            conn.close()

    async def _save_model_version(self, version: ModelVersion):
        """Save model version to database"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            conn.execute("""
                INSERT INTO model_versions (
                    version_id, model_name, version_number, model_type,
                    training_job_id, model_path, config_path, tokenizer_path,
                    performance_metrics, training_data_hash, deployment_status,
                    deployment_percentage, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version.version_id, version.model_name, version.version_number,
                version.model_type.value, version.training_job_id, version.model_path,
                version.config_path, version.tokenizer_path,
                json.dumps(version.performance_metrics),
                version.training_data_hash, version.deployment_status,
                version.deployment_percentage, version.created_at.isoformat()
            ))
            conn.commit()

        finally:
            conn.close()

    async def _save_ab_test(self, test: ABTestResult):
        """Save A/B test to database"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            conn.execute("""
                INSERT INTO ab_tests (
                    test_id, model_a_version, model_b_version, test_duration_hours,
                    traffic_split, start_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                test.test_id, test.model_a_version, test.model_b_version,
                test.test_duration_hours, json.dumps(test.traffic_split),
                test.start_time.isoformat(), test.status
            ))
            conn.commit()

        finally:
            conn.close()

    async def _get_current_production_version(self) -> Optional[str]:
        """Get current production model version"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            cursor = conn.execute("""
                SELECT version_id FROM model_versions
                WHERE deployment_status = 'deployed' AND deployment_percentage = 100.0
                ORDER BY deployed_at DESC
                LIMIT 1
            """)

            result = cursor.fetchone()
            return result[0] if result else None

        finally:
            conn.close()

    async def get_training_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive training pipeline status"""
        conn = sqlite3.connect(self.pipeline_db_path)
        try:
            # Get active jobs
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM training_jobs
                WHERE status IN ('pending', 'preparing_data', 'training', 'validating', 'testing')
                GROUP BY status
            """)
            active_jobs = dict(cursor.fetchall())

            # Get recent completions
            cursor = conn.execute("""
                SELECT COUNT(*) FROM training_jobs
                WHERE status = 'completed' AND created_at >= ?
            """, ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),))
            recent_completions = cursor.fetchone()[0]

            # Get deployed models
            cursor = conn.execute("""
                SELECT model_name, COUNT(*) FROM model_versions
                WHERE deployment_status = 'deployed'
                GROUP BY model_name
            """)
            deployed_models = dict(cursor.fetchall())

            # Get A/B tests
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM ab_tests
                GROUP BY status
            """)
            ab_test_status = dict(cursor.fetchall())

            # Get continuous learning metrics
            cursor = conn.execute("""
                SELECT AVG(accuracy_improvement), AVG(deployment_success_rate)
                FROM continuous_learning_metrics
                WHERE timestamp >= ?
            """, ((datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),))
            cl_metrics = cursor.fetchone()

            return {
                'active_jobs': active_jobs,
                'recent_completions': recent_completions,
                'deployed_models': deployed_models,
                'ab_test_status': ab_test_status,
                'continuous_learning': {
                    'avg_accuracy_improvement': cl_metrics[0] if cl_metrics[0] else 0.0,
                    'deployment_success_rate': cl_metrics[1] if cl_metrics[1] else 0.0
                },
                'pipeline_health': 'healthy',
                'learning_enabled': self.learning_enabled
            }

        finally:
            conn.close()


# Configuration for training pipeline
TRAINING_CONFIG = {
    "pipeline_db_path": "data/training_pipeline.db",
    "feedback_db_path": "data/ai_feedback.db",
    "models_dir": "models",
    "batch_size": 100,
    "training_frequency": "weekly",
    "auto_deploy_threshold": 0.95,
    "max_concurrent_jobs": 2,
    "use_mlflow": True,
    "mlflow_tracking_uri": "sqlite:///mlflow.db",
    "continuous_learning_enabled": True,
    "learning_threshold": 50
}


# Export main classes
__all__ = [
    'TrainingPipeline',
    'TrainingConfig',
    'TrainingJob',
    'ModelVersion',
    'ABTestResult',
    'ContinuousLearningMetrics',
    'TrainingStatus',
    'ModelType',
    'DeploymentStrategy'
]