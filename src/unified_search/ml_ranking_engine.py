"""
Machine Learning-based ranking engine for legal document search results.
Uses neural networks and ensemble methods to learn optimal ranking patterns.
"""

import asyncio
import logging
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. ML ranking will use simplified algorithms.")

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import ndcg_score, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. ML ranking capabilities limited.")

from ..types.unified_types import UnifiedDocument, UnifiedQuery, ContentType
from .composite_ranking_engine import CompositeScore, CompositeRankingEngine


class MLModelType(Enum):
    """Types of machine learning models for ranking."""
    LINEAR = "linear"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


class LearningToRankModel(Enum):
    """Learning-to-rank model types."""
    POINTWISE = "pointwise"
    PAIRWISE = "pairwise"
    LISTWISE = "listwise"


@dataclass
class TrainingExample:
    """Training example for ML ranking."""
    query: str
    document_features: np.ndarray
    relevance_score: float
    authority_score: float
    composite_score: float
    user_feedback: Optional[float] = None
    click_through: bool = False
    dwell_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MLRankingFeatures:
    """Feature vector for ML ranking."""
    textual_similarity: float
    legal_concept_overlap: float
    authority_score: float
    citation_count: int
    recency_score: float
    practice_area_relevance: float
    document_length: float
    query_complexity: float
    semantic_similarity: float
    historical_performance: float
    user_interaction_score: float
    source_quality: float
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for ML models."""
        return np.array([
            self.textual_similarity,
            self.legal_concept_overlap,
            self.authority_score,
            float(self.citation_count),
            self.recency_score,
            self.practice_area_relevance,
            self.document_length,
            self.query_complexity,
            self.semantic_similarity,
            self.historical_performance,
            self.user_interaction_score,
            self.source_quality
        ])


@dataclass
class MLRankingResult:
    """Result from ML ranking."""
    document_id: str
    ml_score: float
    feature_importance: Dict[str, float]
    confidence: float
    model_used: MLModelType


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for ML models."""
    ndcg_at_5: float
    ndcg_at_10: float
    map_score: float
    mrr_score: float
    precision_at_5: float
    recall_at_5: float
    training_loss: float
    validation_loss: float
    feature_importance: Dict[str, float]


class NeuralRankingNet(nn.Module):
    """Neural network for document ranking."""
    
    def __init__(self, input_dim: int = 12, hidden_dims: List[int] = None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [64, 32, 16]
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x).squeeze(-1)


class MachineLearningRankingEngine:
    """
    Advanced machine learning-based ranking engine for legal documents.
    
    Combines traditional ranking signals with learned patterns from user interactions
    and document relevance feedback to optimize search results.
    """
    
    def __init__(self, 
                 composite_engine: CompositeRankingEngine,
                 model_cache_dir: str = "models/ranking",
                 enable_online_learning: bool = True):
        self.composite_engine = composite_engine
        self.model_cache_dir = Path(model_cache_dir)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        self.enable_online_learning = enable_online_learning
        
        self.models: Dict[MLModelType, Any] = {}
        self.scalers: Dict[MLModelType, Any] = {}
        self.training_data: List[TrainingExample] = []
        self.feature_importance: Dict[str, float] = {}
        
        self.logger = logging.getLogger(__name__)
        
        self._initialize_models()
        self._load_cached_models()
    
    def _initialize_models(self):
        """Initialize ML models."""
        if SKLEARN_AVAILABLE:
            self.models[MLModelType.LINEAR] = LinearRegression()
            self.models[MLModelType.RANDOM_FOREST] = RandomForestRegressor(
                n_estimators=100, 
                max_depth=10, 
                random_state=42
            )
            self.models[MLModelType.GRADIENT_BOOSTING] = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            for model_type in [MLModelType.LINEAR, MLModelType.RANDOM_FOREST, MLModelType.GRADIENT_BOOSTING]:
                self.scalers[model_type] = StandardScaler()
        
        if TORCH_AVAILABLE:
            self.models[MLModelType.NEURAL_NETWORK] = NeuralRankingNet()
            self.scalers[MLModelType.NEURAL_NETWORK] = StandardScaler()
    
    def _load_cached_models(self):
        """Load previously trained models from cache."""
        for model_type in list(self.models.keys()):
            model_path = self.model_cache_dir / f"{model_type.value}_model.pkl"
            scaler_path = self.model_cache_dir / f"{model_type.value}_scaler.pkl"
            
            if model_path.exists() and scaler_path.exists():
                try:
                    if model_type == MLModelType.NEURAL_NETWORK and TORCH_AVAILABLE:
                        self.models[model_type].load_state_dict(torch.load(model_path))
                        with open(scaler_path, 'rb') as f:
                            self.scalers[model_type] = pickle.load(f)
                    elif SKLEARN_AVAILABLE:
                        with open(model_path, 'rb') as f:
                            self.models[model_type] = pickle.load(f)
                        with open(scaler_path, 'rb') as f:
                            self.scalers[model_type] = pickle.load(f)
                    
                    self.logger.info(f"Loaded cached {model_type.value} model")
                except Exception as e:
                    self.logger.warning(f"Failed to load cached {model_type.value} model: {e}")
    
    def _save_models(self):
        """Save trained models to cache."""
        for model_type, model in self.models.items():
            try:
                model_path = self.model_cache_dir / f"{model_type.value}_model.pkl"
                scaler_path = self.model_cache_dir / f"{model_type.value}_scaler.pkl"
                
                if model_type == MLModelType.NEURAL_NETWORK and TORCH_AVAILABLE:
                    torch.save(model.state_dict(), model_path)
                elif SKLEARN_AVAILABLE:
                    with open(model_path, 'wb') as f:
                        pickle.dump(model, f)
                
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scalers[model_type], f)
                
                self.logger.info(f"Saved {model_type.value} model to cache")
            except Exception as e:
                self.logger.error(f"Failed to save {model_type.value} model: {e}")
    
    async def extract_features(self, 
                             document: UnifiedDocument, 
                             query: UnifiedQuery,
                             composite_score: CompositeScore) -> MLRankingFeatures:
        """Extract features for ML ranking."""
        
        # Get historical performance if available
        historical_performance = await self._get_historical_performance(
            document.id, query.query_text
        )
        
        # Calculate document length score
        content_length = len(document.content) if document.content else 0
        length_score = min(content_length / 10000, 1.0)  # Normalize to 0-1
        
        # Query complexity (number of terms, legal concepts)
        query_terms = query.query_text.split()
        query_complexity = min(len(query_terms) / 10, 1.0)
        
        # User interaction score (placeholder - would be populated from analytics)
        user_interaction_score = 0.5  # Default neutral score
        
        # Source quality score based on document metadata
        source_quality = await self._calculate_source_quality(document)
        
        return MLRankingFeatures(
            textual_similarity=composite_score.relevance_score,
            legal_concept_overlap=composite_score.context_score,
            authority_score=composite_score.authority_score,
            citation_count=len(document.citations) if document.citations else 0,
            recency_score=composite_score.recency_score,
            practice_area_relevance=composite_score.context_score,  # Approximation
            document_length=length_score,
            query_complexity=query_complexity,
            semantic_similarity=composite_score.relevance_score * 0.8,  # Approximation
            historical_performance=historical_performance,
            user_interaction_score=user_interaction_score,
            source_quality=source_quality
        )
    
    async def _get_historical_performance(self, document_id: str, query: str) -> float:
        """Get historical performance score for document-query pair."""
        # Placeholder implementation - would query analytics database
        return 0.5
    
    async def _calculate_source_quality(self, document: UnifiedDocument) -> float:
        """Calculate quality score based on document source."""
        quality_scores = {
            ContentType.CASE_LAW: 0.9,
            ContentType.STATUTE: 0.95,
            ContentType.REGULATION: 0.85,
            ContentType.LEGAL_BRIEF: 0.7,
            ContentType.LAW_REVIEW: 0.8,
            ContentType.PRACTICE_GUIDE: 0.75
        }
        return quality_scores.get(document.content_type, 0.5)
    
    async def rank_documents(self, 
                           documents: List[UnifiedDocument],
                           query: UnifiedQuery,
                           model_type: MLModelType = MLModelType.ENSEMBLE,
                           use_composite_fallback: bool = True) -> Tuple[List[MLRankingResult], Dict[str, Any]]:
        """
        Rank documents using machine learning models.
        
        Args:
            documents: Documents to rank
            query: Search query
            model_type: Type of ML model to use
            use_composite_fallback: Fall back to composite ranking if ML fails
            
        Returns:
            Tuple of ranked results and metadata
        """
        try:
            # First get composite scores as base features
            composite_scores, _ = await self.composite_engine.rank_documents(
                documents, query, enable_deduplication=False
            )
            
            if not composite_scores:
                return [], {"error": "No composite scores available"}
            
            # Extract ML features
            feature_vectors = []
            document_map = {}
            
            for i, composite_score in enumerate(composite_scores):
                document = next(
                    (doc for doc in documents if doc.id == composite_score.document_id),
                    None
                )
                if not document:
                    continue
                
                features = await self.extract_features(document, query, composite_score)
                feature_vectors.append(features.to_array())
                document_map[i] = {
                    'document': document,
                    'composite_score': composite_score,
                    'features': features
                }
            
            if not feature_vectors:
                return [], {"error": "No features extracted"}
            
            X = np.array(feature_vectors)
            
            # Apply ML ranking
            if model_type == MLModelType.ENSEMBLE:
                ml_scores, feature_importance, confidence_scores = await self._ensemble_predict(X)
            else:
                ml_scores, feature_importance, confidence_scores = await self._single_model_predict(
                    X, model_type
                )
            
            # Create ranking results
            results = []
            for i, (ml_score, confidence) in enumerate(zip(ml_scores, confidence_scores)):
                if i in document_map:
                    result = MLRankingResult(
                        document_id=document_map[i]['document'].id,
                        ml_score=float(ml_score),
                        feature_importance=feature_importance,
                        confidence=float(confidence),
                        model_used=model_type
                    )
                    results.append(result)
            
            # Sort by ML score
            results.sort(key=lambda x: x.ml_score, reverse=True)
            
            metadata = {
                "total_documents": len(results),
                "model_type": model_type.value,
                "feature_importance": feature_importance,
                "average_confidence": float(np.mean(confidence_scores))
            }
            
            return results, metadata
            
        except Exception as e:
            self.logger.error(f"ML ranking failed: {e}")
            if use_composite_fallback:
                # Fall back to composite ranking
                composite_scores, composite_metadata = await self.composite_engine.rank_documents(
                    documents, query
                )
                fallback_results = [
                    MLRankingResult(
                        document_id=score.document_id,
                        ml_score=score.final_score,
                        feature_importance={},
                        confidence=score.confidence,
                        model_used=MLModelType.LINEAR  # Fallback indicator
                    )
                    for score in composite_scores
                ]
                return fallback_results, {"fallback": True, "error": str(e)}
            else:
                raise
    
    async def _single_model_predict(self, X: np.ndarray, model_type: MLModelType) -> Tuple[np.ndarray, Dict[str, float], np.ndarray]:
        """Make predictions using a single model."""
        if model_type not in self.models:
            raise ValueError(f"Model {model_type} not available")
        
        model = self.models[model_type]
        scaler = self.scalers[model_type]
        
        # Scale features
        X_scaled = scaler.transform(X) if hasattr(scaler, 'transform') else X
        
        if model_type == MLModelType.NEURAL_NETWORK and TORCH_AVAILABLE:
            model.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X_scaled)
                predictions = model(X_tensor).numpy()
                confidence = np.ones_like(predictions) * 0.8  # Placeholder
        elif SKLEARN_AVAILABLE:
            predictions = model.predict(X_scaled)
            if hasattr(model, 'predict_proba'):
                confidence = np.max(model.predict_proba(X_scaled), axis=1)
            else:
                confidence = np.ones_like(predictions) * 0.7  # Placeholder
        else:
            raise RuntimeError("No ML framework available")
        
        # Get feature importance
        feature_importance = self._get_feature_importance(model, model_type)
        
        return predictions, feature_importance, confidence
    
    async def _ensemble_predict(self, X: np.ndarray) -> Tuple[np.ndarray, Dict[str, float], np.ndarray]:
        """Make predictions using ensemble of models."""
        all_predictions = []
        all_confidences = []
        combined_importance = {}
        
        available_models = [
            model_type for model_type in self.models.keys()
            if model_type != MLModelType.ENSEMBLE
        ]
        
        for model_type in available_models:
            try:
                predictions, importance, confidence = await self._single_model_predict(X, model_type)
                all_predictions.append(predictions)
                all_confidences.append(confidence)
                
                # Combine feature importance
                for feature, score in importance.items():
                    if feature in combined_importance:
                        combined_importance[feature] += score / len(available_models)
                    else:
                        combined_importance[feature] = score / len(available_models)
                
            except Exception as e:
                self.logger.warning(f"Model {model_type} failed in ensemble: {e}")
                continue
        
        if not all_predictions:
            raise RuntimeError("No models available for ensemble prediction")
        
        # Weighted ensemble (can be made more sophisticated)
        weights = np.array([1.0] * len(all_predictions))  # Equal weights for now
        weights = weights / np.sum(weights)
        
        ensemble_predictions = np.average(all_predictions, axis=0, weights=weights)
        ensemble_confidence = np.average(all_confidences, axis=0, weights=weights)
        
        return ensemble_predictions, combined_importance, ensemble_confidence
    
    def _get_feature_importance(self, model: Any, model_type: MLModelType) -> Dict[str, float]:
        """Extract feature importance from model."""
        feature_names = [
            'textual_similarity', 'legal_concept_overlap', 'authority_score',
            'citation_count', 'recency_score', 'practice_area_relevance',
            'document_length', 'query_complexity', 'semantic_similarity',
            'historical_performance', 'user_interaction_score', 'source_quality'
        ]
        
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
        else:
            # Default uniform importance
            importances = np.ones(len(feature_names)) / len(feature_names)
        
        return dict(zip(feature_names, importances))
    
    async def add_training_example(self, 
                                 query: UnifiedQuery,
                                 document: UnifiedDocument,
                                 composite_score: CompositeScore,
                                 user_feedback: Optional[float] = None,
                                 click_through: bool = False,
                                 dwell_time: Optional[float] = None):
        """Add training example from user interaction."""
        if not self.enable_online_learning:
            return
        
        features = await self.extract_features(document, query, composite_score)
        
        example = TrainingExample(
            query=query.query_text,
            document_features=features.to_array(),
            relevance_score=composite_score.relevance_score,
            authority_score=composite_score.authority_score,
            composite_score=composite_score.final_score,
            user_feedback=user_feedback,
            click_through=click_through,
            dwell_time=dwell_time
        )
        
        self.training_data.append(example)
        
        # Trigger retraining if enough new examples
        if len(self.training_data) % 100 == 0:
            await self.retrain_models()
    
    async def retrain_models(self, validation_split: float = 0.2) -> Dict[MLModelType, ModelPerformanceMetrics]:
        """Retrain models with accumulated training data."""
        if len(self.training_data) < 10:
            self.logger.warning("Insufficient training data for retraining")
            return {}
        
        # Prepare training data
        X = np.array([example.document_features for example in self.training_data])
        y = np.array([
            example.user_feedback if example.user_feedback is not None 
            else example.composite_score 
            for example in self.training_data
        ])
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        performance_metrics = {}
        
        # Train each model
        for model_type in self.models.keys():
            if model_type == MLModelType.ENSEMBLE:
                continue
                
            try:
                metrics = await self._train_single_model(
                    model_type, X_train, y_train, X_val, y_val
                )
                performance_metrics[model_type] = metrics
                self.logger.info(f"Retrained {model_type.value} model - NDCG@10: {metrics.ndcg_at_10:.3f}")
            except Exception as e:
                self.logger.error(f"Failed to retrain {model_type.value}: {e}")
        
        # Save updated models
        self._save_models()
        
        return performance_metrics
    
    async def _train_single_model(self, 
                                model_type: MLModelType,
                                X_train: np.ndarray, 
                                y_train: np.ndarray,
                                X_val: np.ndarray, 
                                y_val: np.ndarray) -> ModelPerformanceMetrics:
        """Train a single model and return performance metrics."""
        
        model = self.models[model_type]
        scaler = self.scalers[model_type]
        
        # Scale features
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        if model_type == MLModelType.NEURAL_NETWORK and TORCH_AVAILABLE:
            # Neural network training
            model.train()
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            train_dataset = TensorDataset(
                torch.FloatTensor(X_train_scaled),
                torch.FloatTensor(y_train)
            )
            train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
            
            epochs = 50
            for epoch in range(epochs):
                epoch_loss = 0
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()
            
            # Validation
            model.eval()
            with torch.no_grad():
                val_predictions = model(torch.FloatTensor(X_val_scaled)).numpy()
                train_predictions = model(torch.FloatTensor(X_train_scaled)).numpy()
            
        elif SKLEARN_AVAILABLE:
            # Scikit-learn model training
            model.fit(X_train_scaled, y_train)
            val_predictions = model.predict(X_val_scaled)
            train_predictions = model.predict(X_train_scaled)
        
        # Calculate metrics
        train_loss = mean_squared_error(y_train, train_predictions)
        val_loss = mean_squared_error(y_val, val_predictions)
        
        # For ranking metrics, we need to group by query (simplified here)
        ndcg_10 = self._calculate_ndcg(y_val, val_predictions, k=10)
        ndcg_5 = self._calculate_ndcg(y_val, val_predictions, k=5)
        
        feature_importance = self._get_feature_importance(model, model_type)
        
        return ModelPerformanceMetrics(
            ndcg_at_5=ndcg_5,
            ndcg_at_10=ndcg_10,
            map_score=0.5,  # Placeholder
            mrr_score=0.5,  # Placeholder
            precision_at_5=0.5,  # Placeholder
            recall_at_5=0.5,  # Placeholder
            training_loss=train_loss,
            validation_loss=val_loss,
            feature_importance=feature_importance
        )
    
    def _calculate_ndcg(self, y_true: np.ndarray, y_pred: np.ndarray, k: int) -> float:
        """Calculate NDCG@k score."""
        try:
            if SKLEARN_AVAILABLE:
                # Reshape for sklearn's ndcg_score function
                return ndcg_score([y_true], [y_pred], k=k)
            else:
                # Simple approximation
                sorted_indices = np.argsort(y_pred)[::-1][:k]
                dcg = np.sum(y_true[sorted_indices] / np.log2(np.arange(2, k + 2)))
                ideal_indices = np.argsort(y_true)[::-1][:k]
                idcg = np.sum(y_true[ideal_indices] / np.log2(np.arange(2, k + 2)))
                return dcg / idcg if idcg > 0 else 0.0
        except:
            return 0.5  # Fallback
    
    async def get_model_performance(self) -> Dict[MLModelType, Dict[str, Any]]:
        """Get performance statistics for all models."""
        performance = {}
        
        for model_type in self.models.keys():
            if model_type == MLModelType.ENSEMBLE:
                continue
                
            performance[model_type] = {
                "trained": hasattr(self.models[model_type], 'fit') or 
                          (TORCH_AVAILABLE and hasattr(self.models[model_type], 'training')),
                "feature_importance": self._get_feature_importance(
                    self.models[model_type], model_type
                ),
                "training_examples": len(self.training_data)
            }
        
        return performance
    
    async def explain_ranking(self, 
                            document_id: str, 
                            ml_result: MLRankingResult) -> Dict[str, Any]:
        """Provide explanation for ML ranking decision."""
        
        explanation = {
            "document_id": document_id,
            "ml_score": ml_result.ml_score,
            "confidence": ml_result.confidence,
            "model_used": ml_result.model_used.value,
            "top_features": sorted(
                ml_result.feature_importance.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5],
            "feature_contributions": ml_result.feature_importance
        }
        
        return explanation


# Integration helper functions
async def create_ml_ranking_engine(composite_engine: CompositeRankingEngine) -> MachineLearningRankingEngine:
    """Create and initialize ML ranking engine."""
    return MachineLearningRankingEngine(composite_engine)