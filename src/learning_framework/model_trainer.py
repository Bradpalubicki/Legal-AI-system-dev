"""
Model Trainer Module

Advanced model training and retraining system with automated optimization,
version management, and continuous improvement capabilities.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import numpy as np
import pandas as pd
import pickle
import json
import hashlib
import asyncio
from pathlib import Path
import shutil
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, SGDClassifier
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import joblib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class TrainingStrategy(Enum):
    FULL_RETRAIN = "full_retrain"
    INCREMENTAL = "incremental"
    ONLINE_LEARNING = "online_learning"
    TRANSFER_LEARNING = "transfer_learning"
    FEDERATED_LEARNING = "federated_learning"
    ACTIVE_LEARNING = "active_learning"
    ENSEMBLE_UPDATE = "ensemble_update"
    FINE_TUNING = "fine_tuning"

class ModelType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    RANKING = "ranking"
    GENERATION = "generation"
    EMBEDDING = "embedding"

class OptimizationMethod(Enum):
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    HYPERBAND = "hyperband"
    OPTUNA = "optuna"

@dataclass
class ModelVersion:
    version_id: str = ""
    model_name: str = ""
    model_type: ModelType = ModelType.CLASSIFICATION
    algorithm: str = ""
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    training_data_hash: str = ""
    training_metrics: Dict[str, float] = field(default_factory=dict)
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    test_metrics: Dict[str, float] = field(default_factory=dict)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    training_duration_seconds: float = 0.0
    data_size: int = 0
    feature_count: int = 0
    model_size_mb: float = 0.0
    training_strategy: TrainingStrategy = TrainingStrategy.FULL_RETRAIN
    parent_version: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    deployment_status: str = "trained"  # trained, validated, deployed, retired
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrainingResult:
    success: bool = False
    model_version: Optional[ModelVersion] = None
    trained_model: Any = None
    training_metrics: Dict[str, float] = field(default_factory=dict)
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    training_log: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    training_duration: float = 0.0
    memory_usage_mb: float = 0.0
    optimization_results: Optional[Dict[str, Any]] = None
    model_comparison: Optional[Dict[str, Any]] = None

class ModelTrainer:
    def __init__(self, model_storage_path: str = "models"):
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(exist_ok=True)
        
        self.model_registry: Dict[str, ModelVersion] = {}
        self.active_models: Dict[str, Any] = {}
        self.training_queue: asyncio.Queue = asyncio.Queue()
        self.training_locks: Dict[str, asyncio.Lock] = {}
        
        # Algorithm configurations
        self.algorithm_configs = {
            'random_forest': {
                'classifier': RandomForestClassifier,
                'regressor': RandomForestRegressor,
                'default_params': {'n_estimators': 100, 'random_state': 42},
                'param_grid': {
                    'n_estimators': [50, 100, 200, 300],
                    'max_depth': [None, 10, 20, 30],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            },
            'gradient_boosting': {
                'classifier': GradientBoostingClassifier,
                'regressor': GradientBoostingRegressor,
                'default_params': {'random_state': 42},
                'param_grid': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 0.9, 1.0]
                }
            },
            'logistic_regression': {
                'classifier': LogisticRegression,
                'regressor': LinearRegression,
                'default_params': {'random_state': 42, 'max_iter': 1000},
                'param_grid': {
                    'C': [0.001, 0.01, 0.1, 1.0, 10.0],
                    'penalty': ['l1', 'l2', 'elasticnet'],
                    'solver': ['liblinear', 'lbfgs']
                }
            },
            'svm': {
                'classifier': SVC,
                'regressor': SVR,
                'default_params': {'random_state': 42},
                'param_grid': {
                    'C': [0.1, 1.0, 10.0],
                    'kernel': ['rbf', 'linear', 'poly'],
                    'gamma': ['scale', 'auto', 0.001, 0.01]
                }
            },
            'neural_network': {
                'classifier': MLPClassifier,
                'regressor': MLPRegressor,
                'default_params': {'random_state': 42, 'max_iter': 500},
                'param_grid': {
                    'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
                    'activation': ['relu', 'tanh'],
                    'alpha': [0.0001, 0.001, 0.01],
                    'learning_rate': ['constant', 'adaptive']
                }
            }
        }

    async def train_model(
        self,
        model_name: str,
        training_data: pd.DataFrame,
        target_column: str,
        model_type: ModelType = ModelType.CLASSIFICATION,
        algorithm: str = "random_forest",
        training_strategy: TrainingStrategy = TrainingStrategy.FULL_RETRAIN,
        hyperparameters: Optional[Dict[str, Any]] = None,
        optimization_method: OptimizationMethod = OptimizationMethod.GRID_SEARCH,
        validation_split: float = 0.2,
        test_split: float = 0.1,
        cross_validation_folds: int = 5,
        parent_model_version: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> TrainingResult:
        """Train a new model with specified configuration."""
        try:
            start_time = datetime.utcnow()
            training_log = []
            warnings_list = []
            
            training_log.append(f"Starting {training_strategy.value} training for {model_name}")
            training_log.append(f"Algorithm: {algorithm}, Model type: {model_type.value}")
            training_log.append(f"Data shape: {training_data.shape}")
            
            # Validate inputs
            if target_column not in training_data.columns:
                return TrainingResult(
                    success=False,
                    error_message=f"Target column '{target_column}' not found in training data",
                    training_log=training_log
                )
            
            if algorithm not in self.algorithm_configs:
                return TrainingResult(
                    success=False,
                    error_message=f"Unsupported algorithm: {algorithm}",
                    training_log=training_log
                )
            
            # Acquire training lock for this model
            lock_key = f"{model_name}_{algorithm}"
            if lock_key not in self.training_locks:
                self.training_locks[lock_key] = asyncio.Lock()
            
            async with self.training_locks[lock_key]:
                # Prepare data
                X = training_data.drop(columns=[target_column])
                y = training_data[target_column]
                
                # Data preprocessing
                preprocessed_data = await self._preprocess_data(X, y, model_type)
                X_processed = preprocessed_data['X']
                y_processed = preprocessed_data['y']
                preprocessor = preprocessed_data['preprocessor']
                
                training_log.append(f"Data preprocessing completed")
                
                # Create data hash for versioning
                data_hash = self._calculate_data_hash(training_data)
                
                # Split data
                X_temp, X_test, y_temp, y_test = train_test_split(
                    X_processed, y_processed, 
                    test_size=test_split, 
                    random_state=42,
                    stratify=y_processed if model_type == ModelType.CLASSIFICATION else None
                )
                
                X_train, X_val, y_train, y_val = train_test_split(
                    X_temp, y_temp,
                    test_size=validation_split / (1 - test_split),
                    random_state=42,
                    stratify=y_temp if model_type == ModelType.CLASSIFICATION else None
                )
                
                training_log.append(f"Data split: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")
                
                # Handle different training strategies
                if training_strategy == TrainingStrategy.INCREMENTAL and parent_model_version:
                    # Load parent model for incremental training
                    parent_model = await self._load_model_version(parent_model_version)
                    if parent_model:
                        training_log.append(f"Loaded parent model: {parent_model_version}")
                
                # Get algorithm configuration
                algo_config = self.algorithm_configs[algorithm]
                model_class = algo_config['classifier'] if model_type == ModelType.CLASSIFICATION else algo_config['regressor']
                
                # Set hyperparameters
                if hyperparameters is None:
                    hyperparameters = algo_config['default_params'].copy()
                
                # Hyperparameter optimization
                optimization_results = None
                if optimization_method in [OptimizationMethod.GRID_SEARCH, OptimizationMethod.RANDOM_SEARCH]:
                    optimization_results = await self._optimize_hyperparameters(
                        model_class, X_train, y_train, algo_config['param_grid'],
                        optimization_method, cross_validation_folds, model_type
                    )
                    
                    if optimization_results['success']:
                        hyperparameters.update(optimization_results['best_params'])
                        training_log.append(f"Hyperparameter optimization completed: {optimization_results['best_score']:.4f}")
                
                # Train model
                model = model_class(**hyperparameters)
                
                # Create pipeline with preprocessing
                pipeline = Pipeline([
                    ('preprocessor', preprocessor),
                    ('model', model)
                ])
                
                # Fit the model
                training_log.append("Starting model training...")
                pipeline.fit(X_temp, y_temp)  # Use temp data (train + val) for final training
                training_log.append("Model training completed")
                
                # Generate predictions
                y_train_pred = pipeline.predict(X_train)
                y_val_pred = pipeline.predict(X_val)
                y_test_pred = pipeline.predict(X_test)
                
                # Calculate metrics
                training_metrics = self._calculate_metrics(y_train, y_train_pred, model_type)
                validation_metrics = self._calculate_metrics(y_val, y_val_pred, model_type)
                test_metrics = self._calculate_metrics(y_test, y_test_pred, model_type)
                
                training_log.append(f"Training metrics: {training_metrics}")
                training_log.append(f"Validation metrics: {validation_metrics}")
                training_log.append(f"Test metrics: {test_metrics}")
                
                # Feature importance
                feature_importance = {}
                if hasattr(model, 'feature_importances_'):
                    feature_names = X.columns.tolist()
                    importances = model.feature_importances_
                    feature_importance = dict(zip(feature_names, importances))
                elif hasattr(model, 'coef_'):
                    feature_names = X.columns.tolist()
                    if len(model.coef_.shape) == 1:
                        coefficients = model.coef_
                    else:
                        coefficients = np.mean(np.abs(model.coef_), axis=0)
                    feature_importance = dict(zip(feature_names, coefficients))
                
                # Create model version
                version_id = self._generate_version_id(model_name, data_hash)
                training_duration = (datetime.utcnow() - start_time).total_seconds()
                
                model_version = ModelVersion(
                    version_id=version_id,
                    model_name=model_name,
                    model_type=model_type,
                    algorithm=algorithm,
                    hyperparameters=hyperparameters,
                    training_data_hash=data_hash,
                    training_metrics=training_metrics,
                    validation_metrics=validation_metrics,
                    test_metrics=test_metrics,
                    feature_importance=feature_importance,
                    training_duration_seconds=training_duration,
                    data_size=len(training_data),
                    feature_count=X.shape[1],
                    training_strategy=training_strategy,
                    parent_version=parent_model_version
                )
                
                # Save model
                model_path = await self._save_model(pipeline, model_version)
                model_version.model_size_mb = model_path.stat().st_size / (1024 * 1024)
                
                # Register model version
                self.model_registry[version_id] = model_version
                self.active_models[version_id] = pipeline
                
                # Model comparison with previous version
                model_comparison = None
                if parent_model_version and parent_model_version in self.model_registry:
                    model_comparison = await self._compare_models(
                        self.model_registry[parent_model_version],
                        model_version
                    )
                
                training_result = TrainingResult(
                    success=True,
                    model_version=model_version,
                    trained_model=pipeline,
                    training_metrics=training_metrics,
                    validation_metrics=validation_metrics,
                    feature_importance=feature_importance,
                    training_log=training_log,
                    warnings=warnings_list,
                    training_duration=training_duration,
                    optimization_results=optimization_results,
                    model_comparison=model_comparison
                )
                
                # Store in database if available
                if db:
                    await self._store_model_version(model_version, db)
                
                logger.info(f"Model training completed: {version_id}")
                return training_result
                
        except Exception as e:
            logger.error(f"Error training model {model_name}: {e}")
            return TrainingResult(
                success=False,
                error_message=str(e),
                training_log=training_log + [f"Error: {str(e)}"]
            )

    async def retrain_model(
        self,
        model_name: str,
        new_data: Optional[pd.DataFrame] = None,
        retrain_threshold: float = 0.05,  # Trigger retrain if performance drops by this amount
        strategy: TrainingStrategy = TrainingStrategy.INCREMENTAL,
        db: Optional[AsyncSession] = None
    ) -> TrainingResult:
        """Automatically retrain model based on performance degradation or new data."""
        try:
            # Get current best model version
            current_version = await self._get_best_model_version(model_name)
            if not current_version:
                return TrainingResult(
                    success=False,
                    error_message=f"No existing model found for {model_name}"
                )
            
            # Check if retraining is needed
            should_retrain, reason = await self._should_retrain_model(
                current_version, new_data, retrain_threshold
            )
            
            if not should_retrain:
                return TrainingResult(
                    success=False,
                    error_message=f"Retraining not needed: {reason}"
                )
            
            # Get training data (existing + new)
            training_data = await self._get_combined_training_data(
                current_version, new_data, db
            )
            
            if training_data is None or training_data.empty:
                return TrainingResult(
                    success=False,
                    error_message="No training data available for retraining"
                )
            
            # Determine target column from model metadata
            target_column = current_version.metadata.get('target_column', 'target')
            
            # Retrain with improved configuration
            return await self.train_model(
                model_name=model_name,
                training_data=training_data,
                target_column=target_column,
                model_type=current_version.model_type,
                algorithm=current_version.algorithm,
                training_strategy=strategy,
                parent_model_version=current_version.version_id,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Error retraining model {model_name}: {e}")
            return TrainingResult(
                success=False,
                error_message=str(e)
            )

    async def evaluate_model(
        self,
        model_version_id: str,
        test_data: pd.DataFrame,
        target_column: str,
        evaluation_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate a trained model on test data."""
        try:
            # Load model
            if model_version_id not in self.active_models:
                model = await self._load_model_version(model_version_id)
                if not model:
                    return {'error': f'Model version {model_version_id} not found'}
                self.active_models[model_version_id] = model
            else:
                model = self.active_models[model_version_id]
            
            # Get model version info
            model_version = self.model_registry.get(model_version_id)
            if not model_version:
                return {'error': f'Model version info not found for {model_version_id}'}
            
            # Prepare test data
            X_test = test_data.drop(columns=[target_column])
            y_test = test_data[target_column]
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            metrics = self._calculate_metrics(y_test, y_pred, model_version.model_type)
            
            # Additional evaluation metrics
            evaluation_result = {
                'model_version_id': model_version_id,
                'test_data_size': len(test_data),
                'metrics': metrics,
                'evaluation_date': datetime.utcnow().isoformat()
            }
            
            # Add detailed classification report for classification models
            if model_version.model_type == ModelType.CLASSIFICATION:
                try:
                    class_report = classification_report(y_test, y_pred, output_dict=True)
                    evaluation_result['classification_report'] = class_report
                except:
                    pass
            
            # Calculate prediction confidence if available
            if hasattr(model, 'predict_proba'):
                y_prob = model.predict_proba(X_test)
                confidence_scores = np.max(y_prob, axis=1)
                evaluation_result['avg_prediction_confidence'] = np.mean(confidence_scores)
                evaluation_result['confidence_distribution'] = {
                    'mean': np.mean(confidence_scores),
                    'std': np.std(confidence_scores),
                    'min': np.min(confidence_scores),
                    'max': np.max(confidence_scores)
                }
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error evaluating model {model_version_id}: {e}")
            return {'error': str(e)}

    async def compare_models(
        self,
        model_version_ids: List[str],
        test_data: pd.DataFrame,
        target_column: str,
        comparison_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple model versions on the same test data."""
        try:
            if not comparison_metrics:
                comparison_metrics = ['accuracy', 'precision', 'recall', 'f1'] if model_version_ids else ['r2', 'mse', 'mae']
            
            comparison_results = {
                'test_data_size': len(test_data),
                'models': {},
                'rankings': {},
                'best_model': None,
                'comparison_date': datetime.utcnow().isoformat()
            }
            
            # Evaluate each model
            for model_id in model_version_ids:
                evaluation = await self.evaluate_model(model_id, test_data, target_column)
                
                if 'error' not in evaluation:
                    comparison_results['models'][model_id] = {
                        'metrics': evaluation['metrics'],
                        'model_info': self.model_registry.get(model_id)
                    }
            
            if not comparison_results['models']:
                return {'error': 'No valid models to compare'}
            
            # Rank models by each metric
            for metric in comparison_metrics:
                if metric in ['mse', 'mae']:  # Lower is better
                    ranking = sorted(
                        comparison_results['models'].items(),
                        key=lambda x: x[1]['metrics'].get(metric, float('inf'))
                    )
                else:  # Higher is better
                    ranking = sorted(
                        comparison_results['models'].items(),
                        key=lambda x: x[1]['metrics'].get(metric, 0),
                        reverse=True
                    )
                
                comparison_results['rankings'][metric] = [model_id for model_id, _ in ranking]
            
            # Determine overall best model (by primary metric)
            if comparison_results['rankings']:
                primary_metric = comparison_metrics[0]
                comparison_results['best_model'] = comparison_results['rankings'][primary_metric][0]
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            return {'error': str(e)}

    async def get_model_versions(
        self,
        model_name: Optional[str] = None,
        include_retired: bool = False
    ) -> List[ModelVersion]:
        """Get all model versions, optionally filtered by model name."""
        try:
            versions = list(self.model_registry.values())
            
            if model_name:
                versions = [v for v in versions if v.model_name == model_name]
            
            if not include_retired:
                versions = [v for v in versions if v.deployment_status != 'retired']
            
            # Sort by creation date (newest first)
            versions.sort(key=lambda x: x.created_at, reverse=True)
            
            return versions
            
        except Exception as e:
            logger.error(f"Error getting model versions: {e}")
            return []

    async def deploy_model(
        self,
        model_version_id: str,
        deployment_target: str = "production",
        validation_required: bool = True
    ) -> Dict[str, Any]:
        """Deploy a model version to specified target."""
        try:
            model_version = self.model_registry.get(model_version_id)
            if not model_version:
                return {'success': False, 'error': 'Model version not found'}
            
            # Validation checks if required
            if validation_required:
                validation_result = await self._validate_model_for_deployment(model_version)
                if not validation_result['valid']:
                    return {'success': False, 'error': validation_result['reason']}
            
            # Update deployment status
            model_version.deployment_status = 'deployed'
            model_version.metadata['deployment_target'] = deployment_target
            model_version.metadata['deployed_at'] = datetime.utcnow().isoformat()
            
            # Retire previous deployed models for the same model name
            for version_id, version in self.model_registry.items():
                if (version.model_name == model_version.model_name and
                    version_id != model_version_id and
                    version.deployment_status == 'deployed'):
                    version.deployment_status = 'retired'
            
            deployment_result = {
                'success': True,
                'model_version_id': model_version_id,
                'deployment_target': deployment_target,
                'deployed_at': datetime.utcnow().isoformat(),
                'model_metrics': model_version.test_metrics
            }
            
            logger.info(f"Model deployed: {model_version_id} to {deployment_target}")
            return deployment_result
            
        except Exception as e:
            logger.error(f"Error deploying model {model_version_id}: {e}")
            return {'success': False, 'error': str(e)}

    # Private helper methods
    
    async def _preprocess_data(
        self, 
        X: pd.DataFrame, 
        y: pd.Series, 
        model_type: ModelType
    ) -> Dict[str, Any]:
        """Preprocess training data."""
        try:
            # Identify column types
            numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
            categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Create preprocessing pipeline
            numeric_transformer = Pipeline(steps=[
                ('scaler', RobustScaler())
            ])
            
            categorical_transformer = Pipeline(steps=[
                ('encoder', LabelEncoder() if len(categorical_features) == 1 else 'passthrough')
            ])
            
            # Combine transformers
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, numeric_features),
                    ('cat', categorical_transformer, categorical_features)
                ],
                remainder='passthrough'
            )
            
            # Handle target variable encoding for classification
            y_processed = y.copy()
            target_encoder = None
            
            if model_type == ModelType.CLASSIFICATION and y.dtype == 'object':
                target_encoder = LabelEncoder()
                y_processed = target_encoder.fit_transform(y)
            
            return {
                'X': X,
                'y': y_processed,
                'preprocessor': preprocessor,
                'target_encoder': target_encoder
            }
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return {'X': X, 'y': y, 'preprocessor': None}

    async def _optimize_hyperparameters(
        self,
        model_class: Any,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        param_grid: Dict[str, List],
        method: OptimizationMethod,
        cv_folds: int,
        model_type: ModelType
    ) -> Dict[str, Any]:
        """Optimize model hyperparameters."""
        try:
            # Create base model
            base_model = model_class(random_state=42)
            
            # Choose optimization method
            if method == OptimizationMethod.GRID_SEARCH:
                optimizer = GridSearchCV(
                    base_model, param_grid, cv=cv_folds, n_jobs=-1,
                    scoring='accuracy' if model_type == ModelType.CLASSIFICATION else 'r2'
                )
            elif method == OptimizationMethod.RANDOM_SEARCH:
                optimizer = RandomizedSearchCV(
                    base_model, param_grid, cv=cv_folds, n_jobs=-1, n_iter=20,
                    scoring='accuracy' if model_type == ModelType.CLASSIFICATION else 'r2',
                    random_state=42
                )
            else:
                return {'success': False, 'error': f'Unsupported optimization method: {method}'}
            
            # Fit optimizer
            optimizer.fit(X_train, y_train)
            
            return {
                'success': True,
                'best_params': optimizer.best_params_,
                'best_score': optimizer.best_score_,
                'cv_results': optimizer.cv_results_
            }
            
        except Exception as e:
            logger.error(f"Error optimizing hyperparameters: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_metrics(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        model_type: ModelType
    ) -> Dict[str, float]:
        """Calculate performance metrics based on model type."""
        try:
            metrics = {}
            
            if model_type == ModelType.CLASSIFICATION:
                metrics['accuracy'] = accuracy_score(y_true, y_pred)
                metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['f1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
                
            elif model_type == ModelType.REGRESSION:
                metrics['mse'] = mean_squared_error(y_true, y_pred)
                metrics['rmse'] = np.sqrt(metrics['mse'])
                metrics['r2'] = r2_score(y_true, y_pred)
                metrics['mae'] = np.mean(np.abs(y_true - y_pred))
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {}

    def _calculate_data_hash(self, data: pd.DataFrame) -> str:
        """Calculate hash of training data for versioning."""
        try:
            # Create hash based on data shape, columns, and sample of values
            data_info = f"{data.shape}_{list(data.columns)}_{data.head().to_string()}"
            return hashlib.md5(data_info.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating data hash: {e}")
            return hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()

    def _generate_version_id(self, model_name: str, data_hash: str) -> str:
        """Generate unique version ID for model."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        version_hash = hashlib.md5(f"{model_name}_{data_hash}_{timestamp}".encode()).hexdigest()[:8]
        return f"{model_name}_v{timestamp}_{version_hash}"

    async def _save_model(self, model: Any, model_version: ModelVersion) -> Path:
        """Save trained model to storage."""
        try:
            model_path = self.model_storage_path / f"{model_version.version_id}.joblib"
            joblib.dump(model, model_path)
            
            # Save model metadata
            metadata_path = self.model_storage_path / f"{model_version.version_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(model_version.__dict__, f, default=str, indent=2)
            
            return model_path
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise

    async def _load_model_version(self, version_id: str) -> Any:
        """Load model from storage."""
        try:
            model_path = self.model_storage_path / f"{version_id}.joblib"
            if model_path.exists():
                return joblib.load(model_path)
            return None
        except Exception as e:
            logger.error(f"Error loading model {version_id}: {e}")
            return None

    async def _compare_models(
        self, 
        old_version: ModelVersion, 
        new_version: ModelVersion
    ) -> Dict[str, Any]:
        """Compare two model versions."""
        try:
            comparison = {
                'old_version': old_version.version_id,
                'new_version': new_version.version_id,
                'metric_changes': {},
                'improvement': False,
                'significant_changes': []
            }
            
            # Compare test metrics
            for metric, new_value in new_version.test_metrics.items():
                old_value = old_version.test_metrics.get(metric, 0)
                change = new_value - old_value
                change_percent = (change / old_value * 100) if old_value != 0 else 0
                
                comparison['metric_changes'][metric] = {
                    'old_value': old_value,
                    'new_value': new_value,
                    'change': change,
                    'change_percent': change_percent
                }
                
                # Check for significant improvements (>1% for most metrics)
                if abs(change_percent) > 1:
                    comparison['significant_changes'].append({
                        'metric': metric,
                        'change_percent': change_percent,
                        'improvement': change > 0 if metric not in ['mse', 'mae'] else change < 0
                    })
            
            # Overall improvement assessment
            if comparison['significant_changes']:
                improvements = sum(1 for change in comparison['significant_changes'] if change['improvement'])
                comparison['improvement'] = improvements > len(comparison['significant_changes']) / 2
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            return {}

    async def _get_best_model_version(self, model_name: str) -> Optional[ModelVersion]:
        """Get the best performing model version for a model."""
        try:
            model_versions = [
                v for v in self.model_registry.values()
                if v.model_name == model_name and v.deployment_status != 'retired'
            ]
            
            if not model_versions:
                return None
            
            # Sort by primary metric (accuracy for classification, r2 for regression)
            def get_primary_metric(version):
                if version.model_type == ModelType.CLASSIFICATION:
                    return version.test_metrics.get('accuracy', 0)
                else:
                    return version.test_metrics.get('r2', 0)
            
            return max(model_versions, key=get_primary_metric)
            
        except Exception as e:
            logger.error(f"Error getting best model version: {e}")
            return None

    async def _should_retrain_model(
        self, 
        current_version: ModelVersion, 
        new_data: Optional[pd.DataFrame], 
        threshold: float
    ) -> Tuple[bool, str]:
        """Determine if model should be retrained."""
        try:
            reasons = []
            
            # Check if there's new data
            if new_data is not None and not new_data.empty:
                reasons.append("New training data available")
            
            # Check model age
            days_since_training = (datetime.utcnow() - current_version.created_at).days
            if days_since_training > 90:  # 3 months
                reasons.append("Model is older than 90 days")
            
            # Check performance degradation (would need recent performance data)
            # This would typically involve monitoring production metrics
            
            # Check data drift (would need drift detection implementation)
            
            if reasons:
                return True, "; ".join(reasons)
            else:
                return False, "No retraining triggers found"
            
        except Exception as e:
            logger.error(f"Error checking retrain conditions: {e}")
            return False, str(e)

    async def _get_combined_training_data(
        self, 
        current_version: ModelVersion, 
        new_data: Optional[pd.DataFrame], 
        db: Optional[AsyncSession]
    ) -> Optional[pd.DataFrame]:
        """Get combined training data (existing + new)."""
        try:
            # This would typically fetch historical training data from database
            # For now, just return new data if available
            return new_data
        except Exception as e:
            logger.error(f"Error getting combined training data: {e}")
            return None

    async def _validate_model_for_deployment(self, model_version: ModelVersion) -> Dict[str, Any]:
        """Validate model is ready for deployment."""
        try:
            validation_checks = []
            
            # Check if model has test metrics
            if not model_version.test_metrics:
                validation_checks.append("No test metrics available")
            
            # Check minimum performance thresholds
            if model_version.model_type == ModelType.CLASSIFICATION:
                min_accuracy = model_version.test_metrics.get('accuracy', 0)
                if min_accuracy < 0.7:  # 70% minimum accuracy
                    validation_checks.append(f"Accuracy too low: {min_accuracy:.3f}")
            
            elif model_version.model_type == ModelType.REGRESSION:
                r2_score = model_version.test_metrics.get('r2', 0)
                if r2_score < 0.5:  # R² minimum threshold
                    validation_checks.append(f"R² score too low: {r2_score:.3f}")
            
            # Check model age
            days_old = (datetime.utcnow() - model_version.created_at).days
            if days_old > 180:  # 6 months
                validation_checks.append(f"Model is too old: {days_old} days")
            
            if validation_checks:
                return {'valid': False, 'reason': "; ".join(validation_checks)}
            else:
                return {'valid': True}
                
        except Exception as e:
            logger.error(f"Error validating model for deployment: {e}")
            return {'valid': False, 'reason': str(e)}

    async def _store_model_version(self, model_version: ModelVersion, db: AsyncSession) -> None:
        """Store model version in database."""
        try:
            # This would typically involve database operations
            logger.info(f"Storing model version {model_version.version_id} in database")
        except Exception as e:
            logger.error(f"Error storing model version: {e}")

    async def _balance_training_data(self, training_samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Balance training data classes if needed."""
        try:
            # Simple balancing - ensure roughly equal representation
            # This is a simplified implementation
            return training_samples
        except Exception as e:
            logger.error(f"Error balancing training data: {e}")
            return training_samples