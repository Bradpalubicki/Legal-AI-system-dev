"""
Model Version Management System
Comprehensive system for tracking, deploying, and managing AI model versions with rollback capabilities.
"""

import asyncio
import json
import logging
import sqlite3
import shutil
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib
import pickle
import numpy as np
from enum import Enum
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    TRAINING = "training"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    FAILED = "failed"

class DeploymentType(Enum):
    FULL = "full"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"

@dataclass
class ModelMetadata:
    """Model metadata and configuration"""
    model_id: str
    version: str
    name: str
    description: str
    model_type: str  # 'openai', 'anthropic', 'local', 'ensemble'
    base_model: str
    training_dataset_id: Optional[str]
    created_at: datetime
    created_by: str
    tags: List[str]
    config: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    model_id: str
    version: str
    evaluation_date: datetime

    # Accuracy metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float

    # Performance metrics
    avg_response_time_ms: float
    p95_response_time_ms: float
    throughput_requests_per_sec: float

    # Business metrics
    user_satisfaction_score: float
    task_completion_rate: float
    error_rate: float

    # Legal-specific metrics
    citation_accuracy: float
    legal_reasoning_quality: float
    compliance_score: float

    # Resource metrics
    memory_usage_mb: float
    cpu_utilization_percent: float
    cost_per_request: float

    # Quality metrics
    hallucination_rate: float
    bias_score: float
    safety_score: float

@dataclass
class DeploymentRecord:
    """Deployment tracking record"""
    deployment_id: str
    model_id: str
    version: str
    deployment_type: DeploymentType
    target_environment: str  # 'staging', 'production'
    traffic_percentage: int
    deployment_time: datetime
    rollback_time: Optional[datetime]
    status: ModelStatus
    configuration: Dict[str, Any]
    performance_snapshot: Optional[PerformanceMetrics]

@dataclass
class ModelComparison:
    """Model comparison results"""
    model_a_id: str
    model_b_id: str
    comparison_date: datetime
    test_dataset_id: str
    metrics_comparison: Dict[str, Dict[str, float]]
    winner: Optional[str]
    confidence_score: float
    recommendation: str

class ModelVersionManager:
    """
    Comprehensive model version management system
    """

    def __init__(self, storage_path: str = "./model_versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        self.db_path = self.storage_path / "model_versions.db"
        self.models_dir = self.storage_path / "models"
        self.artifacts_dir = self.storage_path / "artifacts"
        self.backups_dir = self.storage_path / "backups"

        # Create directories
        self.models_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize the version management database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS model_metadata (
                    model_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    model_type TEXT NOT NULL,
                    base_model TEXT,
                    training_dataset_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    tags TEXT,
                    config TEXT,
                    status TEXT DEFAULT 'training',
                    artifacts_path TEXT
                );

                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accuracy REAL,
                    precision_score REAL,
                    recall_score REAL,
                    f1_score REAL,
                    avg_response_time_ms REAL,
                    p95_response_time_ms REAL,
                    throughput_rps REAL,
                    user_satisfaction_score REAL,
                    task_completion_rate REAL,
                    error_rate REAL,
                    citation_accuracy REAL,
                    legal_reasoning_quality REAL,
                    compliance_score REAL,
                    memory_usage_mb REAL,
                    cpu_utilization_percent REAL,
                    cost_per_request REAL,
                    hallucination_rate REAL,
                    bias_score REAL,
                    safety_score REAL,
                    FOREIGN KEY (model_id) REFERENCES model_metadata (model_id)
                );

                CREATE TABLE IF NOT EXISTS deployments (
                    deployment_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    deployment_type TEXT NOT NULL,
                    target_environment TEXT NOT NULL,
                    traffic_percentage INTEGER DEFAULT 100,
                    deployment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rollback_time TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    configuration TEXT,
                    performance_snapshot_id TEXT,
                    FOREIGN KEY (model_id) REFERENCES model_metadata (model_id),
                    FOREIGN KEY (performance_snapshot_id) REFERENCES performance_metrics (metric_id)
                );

                CREATE TABLE IF NOT EXISTS model_comparisons (
                    comparison_id TEXT PRIMARY KEY,
                    model_a_id TEXT NOT NULL,
                    model_b_id TEXT NOT NULL,
                    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    test_dataset_id TEXT,
                    metrics_comparison TEXT,
                    winner TEXT,
                    confidence_score REAL,
                    recommendation TEXT,
                    FOREIGN KEY (model_a_id) REFERENCES model_metadata (model_id),
                    FOREIGN KEY (model_b_id) REFERENCES model_metadata (model_id)
                );

                CREATE TABLE IF NOT EXISTS rollback_history (
                    rollback_id TEXT PRIMARY KEY,
                    from_model_id TEXT NOT NULL,
                    to_model_id TEXT NOT NULL,
                    rollback_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT NOT NULL,
                    initiated_by TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    rollback_duration_seconds INTEGER,
                    FOREIGN KEY (from_model_id) REFERENCES model_metadata (model_id),
                    FOREIGN KEY (to_model_id) REFERENCES model_metadata (model_id)
                );

                CREATE TABLE IF NOT EXISTS model_lineage (
                    lineage_id TEXT PRIMARY KEY,
                    parent_model_id TEXT,
                    child_model_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_model_id) REFERENCES model_metadata (model_id),
                    FOREIGN KEY (child_model_id) REFERENCES model_metadata (model_id)
                );

                CREATE INDEX IF NOT EXISTS idx_model_version ON model_metadata(version);
                CREATE INDEX IF NOT EXISTS idx_model_status ON model_metadata(status);
                CREATE INDEX IF NOT EXISTS idx_deployment_environment ON deployments(target_environment);
                CREATE INDEX IF NOT EXISTS idx_metrics_date ON performance_metrics(evaluation_date);
            """)

    async def register_model(self, metadata: ModelMetadata) -> bool:
        """Register a new model version"""
        try:
            logger.info(f"Registering model {metadata.model_id} version {metadata.version}")

            # Create model artifacts directory
            model_artifacts_path = self.artifacts_dir / metadata.model_id
            model_artifacts_path.mkdir(exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO model_metadata
                    (model_id, version, name, description, model_type, base_model,
                     training_dataset_id, created_by, tags, config, artifacts_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.model_id,
                    metadata.version,
                    metadata.name,
                    metadata.description,
                    metadata.model_type,
                    metadata.base_model,
                    metadata.training_dataset_id,
                    metadata.created_by,
                    json.dumps(metadata.tags),
                    json.dumps(metadata.config),
                    str(model_artifacts_path)
                ))

            logger.info(f"Successfully registered model {metadata.model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register model {metadata.model_id}: {e}")
            return False

    async def record_performance_metrics(self, metrics: PerformanceMetrics) -> bool:
        """Record performance metrics for a model version"""
        try:
            metric_id = self._generate_id("metric")

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_metrics
                    (metric_id, model_id, version, accuracy, precision_score, recall_score,
                     f1_score, avg_response_time_ms, p95_response_time_ms, throughput_rps,
                     user_satisfaction_score, task_completion_rate, error_rate,
                     citation_accuracy, legal_reasoning_quality, compliance_score,
                     memory_usage_mb, cpu_utilization_percent, cost_per_request,
                     hallucination_rate, bias_score, safety_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric_id,
                    metrics.model_id,
                    metrics.version,
                    metrics.accuracy,
                    metrics.precision,
                    metrics.recall,
                    metrics.f1_score,
                    metrics.avg_response_time_ms,
                    metrics.p95_response_time_ms,
                    metrics.throughput_requests_per_sec,
                    metrics.user_satisfaction_score,
                    metrics.task_completion_rate,
                    metrics.error_rate,
                    metrics.citation_accuracy,
                    metrics.legal_reasoning_quality,
                    metrics.compliance_score,
                    metrics.memory_usage_mb,
                    metrics.cpu_utilization_percent,
                    metrics.cost_per_request,
                    metrics.hallucination_rate,
                    metrics.bias_score,
                    metrics.safety_score
                ))

            logger.info(f"Recorded performance metrics for model {metrics.model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record metrics for model {metrics.model_id}: {e}")
            return False

    async def deploy_model(self,
                          model_id: str,
                          deployment_type: DeploymentType,
                          target_environment: str = "production",
                          traffic_percentage: int = 100,
                          configuration: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Deploy a model version"""
        try:
            deployment_id = self._generate_id("deploy")

            # Get current performance snapshot
            performance_snapshot = await self.get_latest_performance_metrics(model_id)
            performance_snapshot_id = None

            if performance_snapshot:
                # Store performance snapshot
                performance_snapshot_id = await self._store_performance_snapshot(performance_snapshot)

            # Create backup before deployment
            await self._create_deployment_backup(model_id)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO deployments
                    (deployment_id, model_id, version, deployment_type, target_environment,
                     traffic_percentage, configuration, performance_snapshot_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    deployment_id,
                    model_id,
                    await self._get_model_version(model_id),
                    deployment_type.value,
                    target_environment,
                    traffic_percentage,
                    json.dumps(configuration or {}),
                    performance_snapshot_id
                ))

                # Update model status
                conn.execute("""
                    UPDATE model_metadata SET status = ?
                    WHERE model_id = ?
                """, (ModelStatus.PRODUCTION.value, model_id))

            logger.info(f"Deployed model {model_id} as {deployment_id}")
            return deployment_id

        except Exception as e:
            logger.error(f"Failed to deploy model {model_id}: {e}")
            return None

    async def rollback_model(self,
                           from_model_id: str,
                           to_model_id: str,
                           reason: str,
                           initiated_by: str = "system") -> bool:
        """Rollback from one model version to another"""
        try:
            rollback_start = datetime.now()
            rollback_id = self._generate_id("rollback")

            logger.info(f"Starting rollback from {from_model_id} to {to_model_id}")

            # Validate target model exists and is stable
            target_model = await self.get_model_metadata(to_model_id)
            if not target_model:
                raise ValueError(f"Target model {to_model_id} not found")

            # Create rollback checkpoint
            await self._create_rollback_checkpoint(from_model_id)

            # Update deployment status
            with sqlite3.connect(self.db_path) as conn:
                # Mark current deployment as rolled back
                conn.execute("""
                    UPDATE deployments
                    SET rollback_time = CURRENT_TIMESTAMP, status = 'rolled_back'
                    WHERE model_id = ? AND status = 'active'
                """, (from_model_id,))

                # Update model statuses
                conn.execute("""
                    UPDATE model_metadata SET status = ?
                    WHERE model_id = ?
                """, (ModelStatus.DEPRECATED.value, from_model_id))

                conn.execute("""
                    UPDATE model_metadata SET status = ?
                    WHERE model_id = ?
                """, (ModelStatus.PRODUCTION.value, to_model_id))

                # Record rollback
                rollback_duration = (datetime.now() - rollback_start).total_seconds()
                conn.execute("""
                    INSERT INTO rollback_history
                    (rollback_id, from_model_id, to_model_id, reason, initiated_by,
                     rollback_duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rollback_id,
                    from_model_id,
                    to_model_id,
                    reason,
                    initiated_by,
                    int(rollback_duration)
                ))

            logger.info(f"Successfully rolled back to model {to_model_id} in {rollback_duration:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            # Record failed rollback
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO rollback_history
                    (rollback_id, from_model_id, to_model_id, reason, initiated_by, success)
                    VALUES (?, ?, ?, ?, ?, FALSE)
                """, (
                    self._generate_id("rollback"),
                    from_model_id,
                    to_model_id,
                    f"FAILED: {reason} - {str(e)}",
                    initiated_by
                ))
            return False

    async def compare_models(self, model_a_id: str, model_b_id: str, test_dataset_id: str) -> ModelComparison:
        """Compare two model versions"""
        logger.info(f"Comparing models {model_a_id} vs {model_b_id}")

        # Get performance metrics for both models
        metrics_a = await self.get_latest_performance_metrics(model_a_id)
        metrics_b = await self.get_latest_performance_metrics(model_b_id)

        if not metrics_a or not metrics_b:
            raise ValueError("Performance metrics not available for one or both models")

        # Compare key metrics
        metrics_comparison = {
            'accuracy': {
                'model_a': metrics_a.accuracy,
                'model_b': metrics_b.accuracy,
                'difference': metrics_b.accuracy - metrics_a.accuracy
            },
            'response_time': {
                'model_a': metrics_a.avg_response_time_ms,
                'model_b': metrics_b.avg_response_time_ms,
                'difference': metrics_a.avg_response_time_ms - metrics_b.avg_response_time_ms  # Lower is better
            },
            'cost_efficiency': {
                'model_a': metrics_a.cost_per_request,
                'model_b': metrics_b.cost_per_request,
                'difference': metrics_a.cost_per_request - metrics_b.cost_per_request  # Lower is better
            },
            'safety_score': {
                'model_a': metrics_a.safety_score,
                'model_b': metrics_b.safety_score,
                'difference': metrics_b.safety_score - metrics_a.safety_score
            }
        }

        # Determine winner based on weighted scoring
        score_a = self._calculate_composite_score(metrics_a)
        score_b = self._calculate_composite_score(metrics_b)

        winner = model_b_id if score_b > score_a else model_a_id
        confidence_score = abs(score_b - score_a) / max(score_a, score_b)

        # Generate recommendation
        recommendation = self._generate_recommendation(metrics_comparison, winner, confidence_score)

        comparison = ModelComparison(
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            comparison_date=datetime.now(),
            test_dataset_id=test_dataset_id,
            metrics_comparison=metrics_comparison,
            winner=winner,
            confidence_score=confidence_score,
            recommendation=recommendation
        )

        # Save comparison results
        await self._save_model_comparison(comparison)

        return comparison

    async def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM model_metadata WHERE model_id = ?
            """, (model_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return ModelMetadata(
                model_id=row['model_id'],
                version=row['version'],
                name=row['name'],
                description=row['description'],
                model_type=row['model_type'],
                base_model=row['base_model'],
                training_dataset_id=row['training_dataset_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                created_by=row['created_by'],
                tags=json.loads(row['tags']) if row['tags'] else [],
                config=json.loads(row['config']) if row['config'] else {}
            )

    async def get_latest_performance_metrics(self, model_id: str) -> Optional[PerformanceMetrics]:
        """Get the latest performance metrics for a model"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM performance_metrics
                WHERE model_id = ?
                ORDER BY evaluation_date DESC
                LIMIT 1
            """, (model_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return PerformanceMetrics(
                model_id=row['model_id'],
                version=row['version'],
                evaluation_date=datetime.fromisoformat(row['evaluation_date']),
                accuracy=row['accuracy'],
                precision=row['precision_score'],
                recall=row['recall_score'],
                f1_score=row['f1_score'],
                avg_response_time_ms=row['avg_response_time_ms'],
                p95_response_time_ms=row['p95_response_time_ms'],
                throughput_requests_per_sec=row['throughput_rps'],
                user_satisfaction_score=row['user_satisfaction_score'],
                task_completion_rate=row['task_completion_rate'],
                error_rate=row['error_rate'],
                citation_accuracy=row['citation_accuracy'],
                legal_reasoning_quality=row['legal_reasoning_quality'],
                compliance_score=row['compliance_score'],
                memory_usage_mb=row['memory_usage_mb'],
                cpu_utilization_percent=row['cpu_utilization_percent'],
                cost_per_request=row['cost_per_request'],
                hallucination_rate=row['hallucination_rate'],
                bias_score=row['bias_score'],
                safety_score=row['safety_score']
            )

    async def get_production_models(self) -> List[ModelMetadata]:
        """Get all models currently in production"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM model_metadata
                WHERE status = ?
                ORDER BY created_at DESC
            """, (ModelStatus.PRODUCTION.value,))

            models = []
            for row in cursor.fetchall():
                models.append(ModelMetadata(
                    model_id=row['model_id'],
                    version=row['version'],
                    name=row['name'],
                    description=row['description'],
                    model_type=row['model_type'],
                    base_model=row['base_model'],
                    training_dataset_id=row['training_dataset_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    created_by=row['created_by'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    config=json.loads(row['config']) if row['config'] else {}
                ))

            return models

    async def get_rollback_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get rollback history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM rollback_history
                ORDER BY rollback_time DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def _calculate_composite_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate composite performance score"""
        weights = {
            'accuracy': 0.25,
            'response_time': 0.15,  # Lower is better, so we'll invert
            'user_satisfaction': 0.20,
            'safety_score': 0.15,
            'compliance_score': 0.10,
            'cost_efficiency': 0.10,  # Lower cost is better
            'citation_accuracy': 0.05
        }

        score = 0.0
        score += weights['accuracy'] * metrics.accuracy
        score += weights['response_time'] * (1.0 - min(metrics.avg_response_time_ms / 10000, 1.0))  # Normalize and invert
        score += weights['user_satisfaction'] * metrics.user_satisfaction_score
        score += weights['safety_score'] * metrics.safety_score
        score += weights['compliance_score'] * metrics.compliance_score
        score += weights['cost_efficiency'] * (1.0 - min(metrics.cost_per_request / 1.0, 1.0))  # Normalize and invert
        score += weights['citation_accuracy'] * metrics.citation_accuracy

        return score

    def _generate_recommendation(self,
                               metrics_comparison: Dict[str, Dict[str, float]],
                               winner: str,
                               confidence: float) -> str:
        """Generate deployment recommendation"""
        if confidence < 0.1:
            return "Models are too similar for reliable comparison. Consider longer evaluation period."
        elif confidence < 0.3:
            return f"Slight advantage to {winner}. Recommend A/B testing before full deployment."
        elif confidence < 0.6:
            return f"Clear advantage to {winner}. Recommend gradual rollout with monitoring."
        else:
            return f"Strong advantage to {winner}. Safe for immediate deployment."

    async def _get_model_version(self, model_id: str) -> str:
        """Get model version by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM model_metadata WHERE model_id = ?", (model_id,))
            result = cursor.fetchone()
            return result[0] if result else "unknown"

    async def _store_performance_snapshot(self, metrics: PerformanceMetrics) -> str:
        """Store performance snapshot and return ID"""
        snapshot_id = self._generate_id("snapshot")
        # Implementation would store the snapshot
        return snapshot_id

    async def _create_deployment_backup(self, model_id: str):
        """Create backup before deployment"""
        backup_path = self.backups_dir / f"{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path.mkdir(exist_ok=True)
        # Implementation would backup model artifacts

    async def _create_rollback_checkpoint(self, model_id: str):
        """Create rollback checkpoint"""
        checkpoint_path = self.backups_dir / f"rollback_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        checkpoint_path.mkdir(exist_ok=True)
        # Implementation would create checkpoint

    async def _save_model_comparison(self, comparison: ModelComparison):
        """Save model comparison results"""
        comparison_id = self._generate_id("comparison")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO model_comparisons
                (comparison_id, model_a_id, model_b_id, test_dataset_id,
                 metrics_comparison, winner, confidence_score, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comparison_id,
                comparison.model_a_id,
                comparison.model_b_id,
                comparison.test_dataset_id,
                json.dumps(comparison.metrics_comparison),
                comparison.winner,
                comparison.confidence_score,
                comparison.recommendation
            ))

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_obj = hashlib.md5(f"{prefix}_{timestamp}_{np.random.random()}".encode())
        return f"{prefix}_{timestamp}_{hash_obj.hexdigest()[:8]}"

    async def get_version_stats(self) -> Dict[str, Any]:
        """Get comprehensive version management statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Model counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM model_metadata
                GROUP BY status
            """)
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

            # Deployment counts by environment
            cursor.execute("""
                SELECT target_environment, COUNT(*) as count
                FROM deployments
                WHERE status = 'active'
                GROUP BY target_environment
            """)
            deployment_counts = {row['target_environment']: row['count'] for row in cursor.fetchall()}

            # Average performance metrics
            cursor.execute("""
                SELECT AVG(accuracy) as avg_accuracy,
                       AVG(avg_response_time_ms) as avg_response_time,
                       AVG(user_satisfaction_score) as avg_satisfaction
                FROM performance_metrics
                WHERE evaluation_date >= datetime('now', '-30 days')
            """)
            avg_metrics = cursor.fetchone()

            # Rollback frequency
            cursor.execute("""
                SELECT COUNT(*) as rollback_count
                FROM rollback_history
                WHERE rollback_time >= datetime('now', '-30 days')
            """)
            recent_rollbacks = cursor.fetchone()['rollback_count']

            return {
                'models_by_status': status_counts,
                'active_deployments': deployment_counts,
                'average_metrics': {
                    'accuracy': avg_metrics['avg_accuracy'] or 0,
                    'response_time_ms': avg_metrics['avg_response_time'] or 0,
                    'user_satisfaction': avg_metrics['avg_satisfaction'] or 0
                },
                'recent_rollbacks': recent_rollbacks,
                'total_models': sum(status_counts.values()),
                'last_updated': datetime.now().isoformat()
            }

# Example usage
async def main():
    """Example usage of the model version manager"""
    manager = ModelVersionManager()

    # Register a new model
    metadata = ModelMetadata(
        model_id="legal_gpt4_v1",
        version="1.0.0",
        name="Legal GPT-4 Fine-tuned",
        description="GPT-4 fine-tuned on legal documents",
        model_type="openai",
        base_model="gpt-4",
        training_dataset_id="dataset_001",
        created_at=datetime.now(),
        created_by="training_pipeline",
        tags=["legal", "gpt4", "fine-tuned"],
        config={"temperature": 0.1, "max_tokens": 2048}
    )

    await manager.register_model(metadata)

    # Record performance metrics
    metrics = PerformanceMetrics(
        model_id="legal_gpt4_v1",
        version="1.0.0",
        evaluation_date=datetime.now(),
        accuracy=0.92,
        precision=0.89,
        recall=0.87,
        f1_score=0.88,
        avg_response_time_ms=1250.0,
        p95_response_time_ms=3000.0,
        throughput_requests_per_sec=8.5,
        user_satisfaction_score=4.2,
        task_completion_rate=0.94,
        error_rate=0.03,
        citation_accuracy=0.96,
        legal_reasoning_quality=0.88,
        compliance_score=0.95,
        memory_usage_mb=2048.0,
        cpu_utilization_percent=45.0,
        cost_per_request=0.12,
        hallucination_rate=0.02,
        bias_score=0.15,
        safety_score=0.93
    )

    await manager.record_performance_metrics(metrics)

    # Get stats
    stats = await manager.get_version_stats()
    print(f"Version management stats: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())