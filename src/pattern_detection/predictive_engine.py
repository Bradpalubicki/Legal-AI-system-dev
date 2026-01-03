"""
Predictive Engine Module

Advanced predictive analytics system for legal case outcomes,
settlement predictions, and attorney performance forecasting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
import pickle
import asyncio
import json

logger = logging.getLogger(__name__)

class PredictionModel(Enum):
    CASE_OUTCOME = "case_outcome"
    SETTLEMENT_AMOUNT = "settlement_amount"
    CASE_DURATION = "case_duration"
    WIN_PROBABILITY = "win_probability"
    SETTLEMENT_PROBABILITY = "settlement_probability"
    ATTORNEY_WORKLOAD = "attorney_workload"
    CLIENT_SATISFACTION = "client_satisfaction"
    BILLING_FORECAST = "billing_forecast"
    DEADLINE_RISK = "deadline_risk"
    COST_PREDICTION = "cost_prediction"
    RESOURCE_NEEDS = "resource_needs"
    CASE_COMPLEXITY = "case_complexity"
    TRIAL_LENGTH = "trial_length"
    APPEAL_PROBABILITY = "appeal_probability"
    NEGOTIATION_SUCCESS = "negotiation_success"

class OutcomeType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    PROBABILITY = "probability"
    TIME_SERIES = "time_series"

@dataclass
class Prediction:
    id: Optional[int] = None
    model_type: PredictionModel = PredictionModel.CASE_OUTCOME
    outcome_type: OutcomeType = OutcomeType.CLASSIFICATION
    target_entity_id: Optional[int] = None  # case_id, attorney_id, etc.
    predicted_value: Any = None
    confidence_score: float = 0.0
    probability_distribution: Optional[Dict[str, float]] = None
    feature_importance: Dict[str, float] = field(default_factory=dict)
    prediction_date: datetime = field(default_factory=datetime.utcnow)
    prediction_horizon: Optional[int] = None  # Days into the future
    actual_outcome: Optional[Any] = None
    accuracy_score: Optional[float] = None
    model_version: str = "1.0.0"
    input_features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class PredictiveEngine:
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        self.feature_selectors: Dict[str, SelectKBest] = {}
        self.model_performance: Dict[str, Dict[str, float]] = {}
        self.prediction_cache: Dict[str, List[Prediction]] = {}
        
        # Model configurations
        self.model_configs = {
            PredictionModel.CASE_OUTCOME: {
                'type': OutcomeType.CLASSIFICATION,
                'algorithms': ['random_forest', 'gradient_boosting', 'logistic_regression'],
                'features': ['case_type', 'attorney_experience', 'case_value', 'complexity_score', 'jurisdiction'],
                'target': 'outcome',
                'min_samples': 100
            },
            PredictionModel.SETTLEMENT_AMOUNT: {
                'type': OutcomeType.REGRESSION,
                'algorithms': ['random_forest', 'gradient_boosting', 'linear_regression'],
                'features': ['case_type', 'initial_demand', 'case_value', 'attorney_experience', 'defendant_type'],
                'target': 'settlement_amount',
                'min_samples': 50
            },
            PredictionModel.CASE_DURATION: {
                'type': OutcomeType.REGRESSION,
                'algorithms': ['random_forest', 'gradient_boosting'],
                'features': ['case_type', 'complexity_score', 'attorney_count', 'court_backlog', 'case_value'],
                'target': 'duration_days',
                'min_samples': 75
            },
            PredictionModel.WIN_PROBABILITY: {
                'type': OutcomeType.PROBABILITY,
                'algorithms': ['random_forest', 'gradient_boosting', 'logistic_regression'],
                'features': ['case_strength', 'attorney_win_rate', 'judge_ruling_history', 'case_type', 'evidence_quality'],
                'target': 'won_case',
                'min_samples': 100
            }
        }

    async def train_model(
        self,
        model_type: PredictionModel,
        training_data: Optional[pd.DataFrame] = None,
        validation_split: float = 0.2,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Train a predictive model."""
        try:
            config = self.model_configs.get(model_type)
            if not config:
                return {'error': f'No configuration found for model type {model_type.value}'}
            
            # Get training data
            if training_data is None:
                training_data = await self._get_training_data(model_type, db)
            
            if training_data.empty or len(training_data) < config['min_samples']:
                return {'error': f'Insufficient training data. Need at least {config["min_samples"]} samples'}
            
            # Prepare features and target
            feature_columns = [col for col in config['features'] if col in training_data.columns]
            if not feature_columns:
                return {'error': 'Required features not found in training data'}
            
            X = training_data[feature_columns].copy()
            y = training_data[config['target']] if config['target'] in training_data.columns else None
            
            if y is None:
                return {'error': f'Target variable {config["target"]} not found in training data'}
            
            # Handle missing values
            X = X.fillna(X.mean() if X.select_dtypes(include=[np.number]).shape[1] > 0 else 0)
            
            # Encode categorical variables
            categorical_columns = X.select_dtypes(include=['object']).columns
            for col in categorical_columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                X[col] = self.encoders[col].fit_transform(X[col].astype(str))
            
            # Scale features
            scaler_key = f"{model_type.value}_scaler"
            if scaler_key not in self.scalers:
                self.scalers[scaler_key] = StandardScaler()
            X_scaled = self.scalers[scaler_key].fit_transform(X)
            
            # Feature selection
            selector_key = f"{model_type.value}_selector"
            if config['type'] in [OutcomeType.CLASSIFICATION, OutcomeType.PROBABILITY]:
                self.feature_selectors[selector_key] = SelectKBest(f_classif, k=min(10, len(feature_columns)))
            else:
                self.feature_selectors[selector_key] = SelectKBest(f_regression, k=min(10, len(feature_columns)))
            
            X_selected = self.feature_selectors[selector_key].fit_transform(X_scaled, y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_selected, y, test_size=validation_split, random_state=42, stratify=y if config['type'] == OutcomeType.CLASSIFICATION else None
            )
            
            # Train multiple algorithms
            best_model = None
            best_score = -np.inf
            model_results = {}
            
            for algorithm in config['algorithms']:
                model = await self._create_model(algorithm, config['type'])
                
                # Train model
                model.fit(X_train, y_train)
                
                # Evaluate model
                y_pred = model.predict(X_test)
                
                if config['type'] in [OutcomeType.CLASSIFICATION, OutcomeType.PROBABILITY]:
                    score = accuracy_score(y_test, y_pred)
                    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                    
                    model_results[algorithm] = {
                        'accuracy': score,
                        'precision': precision,
                        'recall': recall,
                        'f1_score': f1
                    }
                else:
                    score = r2_score(y_test, y_pred)
                    mse = mean_squared_error(y_test, y_pred)
                    rmse = np.sqrt(mse)
                    
                    model_results[algorithm] = {
                        'r2_score': score,
                        'mse': mse,
                        'rmse': rmse
                    }
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_selected, y, cv=5)
                model_results[algorithm]['cv_mean'] = cv_scores.mean()
                model_results[algorithm]['cv_std'] = cv_scores.std()
                
                # Select best model
                if score > best_score:
                    best_score = score
                    best_model = model
            
            # Store best model
            self.models[model_type.value] = best_model
            self.model_performance[model_type.value] = model_results
            
            # Calculate feature importance
            feature_importance = {}
            if hasattr(best_model, 'feature_importances_'):
                selected_features = self.feature_selectors[selector_key].get_support()
                important_features = [feature_columns[i] for i, selected in enumerate(selected_features) if selected]
                
                for i, importance in enumerate(best_model.feature_importances_):
                    if i < len(important_features):
                        feature_importance[important_features[i]] = float(importance)
            
            training_summary = {
                'model_type': model_type.value,
                'best_algorithm': max(model_results.keys(), key=lambda k: model_results[k].get('accuracy', model_results[k].get('r2_score', 0))),
                'best_score': best_score,
                'training_samples': len(training_data),
                'features_used': len(feature_columns),
                'features_selected': X_selected.shape[1],
                'feature_importance': feature_importance,
                'model_results': model_results,
                'trained_at': datetime.utcnow()
            }
            
            logger.info(f"Model {model_type.value} trained successfully with score {best_score:.3f}")
            return training_summary
            
        except Exception as e:
            logger.error(f"Error training model {model_type.value}: {e}")
            return {'error': str(e)}

    async def predict(
        self,
        model_type: PredictionModel,
        input_features: Dict[str, Any],
        target_entity_id: Optional[int] = None,
        prediction_horizon: Optional[int] = None
    ) -> Optional[Prediction]:
        """Make a prediction using trained model."""
        try:
            if model_type.value not in self.models:
                return None
            
            config = self.model_configs.get(model_type)
            if not config:
                return None
            
            model = self.models[model_type.value]
            
            # Prepare input features
            feature_df = pd.DataFrame([input_features])
            
            # Get required features
            required_features = [col for col in config['features'] if col in feature_df.columns]
            if not required_features:
                return None
            
            X = feature_df[required_features].copy()
            
            # Handle missing values
            X = X.fillna(X.mean() if X.select_dtypes(include=[np.number]).shape[1] > 0 else 0)
            
            # Encode categorical variables
            categorical_columns = X.select_dtypes(include=['object']).columns
            for col in categorical_columns:
                if col in self.encoders:
                    # Handle unseen categories
                    try:
                        X[col] = self.encoders[col].transform(X[col].astype(str))
                    except ValueError:
                        # Use most frequent category for unseen values
                        X[col] = 0  # Or handle differently
            
            # Scale features
            scaler_key = f"{model_type.value}_scaler"
            if scaler_key in self.scalers:
                X_scaled = self.scalers[scaler_key].transform(X)
            else:
                X_scaled = X.values
            
            # Feature selection
            selector_key = f"{model_type.value}_selector"
            if selector_key in self.feature_selectors:
                X_selected = self.feature_selectors[selector_key].transform(X_scaled)
            else:
                X_selected = X_scaled
            
            # Make prediction
            predicted_value = model.predict(X_selected)[0]
            
            # Calculate confidence/probability
            confidence_score = 0.0
            probability_distribution = None
            
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X_selected)[0]
                confidence_score = float(np.max(probabilities))
                
                if config['type'] in [OutcomeType.CLASSIFICATION, OutcomeType.PROBABILITY]:
                    classes = model.classes_
                    probability_distribution = {
                        str(cls): float(prob) for cls, prob in zip(classes, probabilities)
                    }
            else:
                # For regression, use a simpler confidence estimate
                confidence_score = 0.8  # Default confidence for regression
            
            # Get feature importance for this prediction
            feature_importance = {}
            if hasattr(model, 'feature_importances_') and selector_key in self.feature_selectors:
                selected_features = self.feature_selectors[selector_key].get_support()
                important_features = [required_features[i] for i, selected in enumerate(selected_features) if selected]
                
                for i, importance in enumerate(model.feature_importances_):
                    if i < len(important_features):
                        feature_importance[important_features[i]] = float(importance)
            
            # Generate explanation and recommendations
            explanation, recommendations, risk_factors = await self._generate_prediction_insights(
                model_type, predicted_value, input_features, feature_importance, confidence_score
            )
            
            prediction = Prediction(
                model_type=model_type,
                outcome_type=config['type'],
                target_entity_id=target_entity_id,
                predicted_value=predicted_value,
                confidence_score=confidence_score,
                probability_distribution=probability_distribution,
                feature_importance=feature_importance,
                prediction_horizon=prediction_horizon,
                input_features=input_features,
                explanation=explanation,
                recommendations=recommendations,
                risk_factors=risk_factors
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction for {model_type.value}: {e}")
            return None

    async def batch_predict(
        self,
        model_type: PredictionModel,
        input_data: List[Dict[str, Any]],
        target_entity_ids: Optional[List[int]] = None
    ) -> List[Prediction]:
        """Make batch predictions."""
        try:
            predictions = []
            
            for i, input_features in enumerate(input_data):
                entity_id = target_entity_ids[i] if target_entity_ids and i < len(target_entity_ids) else None
                
                prediction = await self.predict(model_type, input_features, entity_id)
                if prediction:
                    predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making batch predictions: {e}")
            return []

    async def get_model_performance(
        self,
        model_type: Optional[PredictionModel] = None
    ) -> Dict[str, Any]:
        """Get model performance metrics."""
        try:
            if model_type:
                return self.model_performance.get(model_type.value, {})
            else:
                return self.model_performance
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {}

    async def update_prediction_accuracy(
        self,
        prediction_id: int,
        actual_outcome: Any,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Update prediction with actual outcome for accuracy tracking."""
        try:
            # This would typically update the prediction in the database
            # and recalculate model accuracy metrics
            
            # For now, just log the update
            logger.info(f"Updated prediction {prediction_id} with actual outcome: {actual_outcome}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating prediction accuracy: {e}")
            return False

    async def retrain_model(
        self,
        model_type: PredictionModel,
        include_recent_data: bool = True,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Retrain model with updated data."""
        try:
            logger.info(f"Retraining model: {model_type.value}")
            
            # Get fresh training data
            training_data = await self._get_training_data(model_type, db, include_recent=include_recent_data)
            
            # Retrain model
            training_result = await self.train_model(model_type, training_data, db=db)
            
            if 'error' not in training_result:
                logger.info(f"Model {model_type.value} retrained successfully")
            
            return training_result
            
        except Exception as e:
            logger.error(f"Error retraining model {model_type.value}: {e}")
            return {'error': str(e)}

    async def save_models(self, file_path: str) -> bool:
        """Save trained models to disk."""
        try:
            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'encoders': self.encoders,
                'feature_selectors': self.feature_selectors,
                'model_performance': self.model_performance,
                'saved_at': datetime.utcnow()
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Models saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False

    async def load_models(self, file_path: str) -> bool:
        """Load trained models from disk."""
        try:
            with open(file_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data.get('models', {})
            self.scalers = model_data.get('scalers', {})
            self.encoders = model_data.get('encoders', {})
            self.feature_selectors = model_data.get('feature_selectors', {})
            self.model_performance = model_data.get('model_performance', {})
            
            logger.info(f"Models loaded from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    async def _get_training_data(
        self,
        model_type: PredictionModel,
        db: Optional[AsyncSession],
        include_recent: bool = True
    ) -> pd.DataFrame:
        """Get training data for model."""
        try:
            # This is a mock implementation - in practice, you would query your database
            # to get historical data for training
            
            # Generate mock training data for demonstration
            np.random.seed(42)
            n_samples = 500
            
            data = {}
            config = self.model_configs.get(model_type, {})
            
            if model_type == PredictionModel.CASE_OUTCOME:
                data = {
                    'case_type': np.random.choice(['personal_injury', 'contract', 'employment', 'malpractice'], n_samples),
                    'attorney_experience': np.random.randint(1, 25, n_samples),
                    'case_value': np.random.lognormal(10, 1, n_samples),
                    'complexity_score': np.random.uniform(1, 10, n_samples),
                    'jurisdiction': np.random.choice(['federal', 'state_superior', 'state_district'], n_samples),
                    'outcome': np.random.choice(['won', 'lost', 'settled'], n_samples)
                }
                
            elif model_type == PredictionModel.SETTLEMENT_AMOUNT:
                data = {
                    'case_type': np.random.choice(['personal_injury', 'contract', 'employment'], n_samples),
                    'initial_demand': np.random.lognormal(11, 0.5, n_samples),
                    'case_value': np.random.lognormal(10, 1, n_samples),
                    'attorney_experience': np.random.randint(1, 25, n_samples),
                    'defendant_type': np.random.choice(['individual', 'corporation', 'government'], n_samples),
                    'settlement_amount': np.random.lognormal(9.5, 0.8, n_samples)
                }
                
            elif model_type == PredictionModel.CASE_DURATION:
                data = {
                    'case_type': np.random.choice(['personal_injury', 'contract', 'employment'], n_samples),
                    'complexity_score': np.random.uniform(1, 10, n_samples),
                    'attorney_count': np.random.randint(1, 5, n_samples),
                    'court_backlog': np.random.uniform(0, 1, n_samples),
                    'case_value': np.random.lognormal(10, 1, n_samples),
                    'duration_days': np.random.lognormal(5, 0.5, n_samples)
                }
                
            elif model_type == PredictionModel.WIN_PROBABILITY:
                data = {
                    'case_strength': np.random.uniform(0, 1, n_samples),
                    'attorney_win_rate': np.random.uniform(0.3, 0.9, n_samples),
                    'judge_ruling_history': np.random.uniform(0, 1, n_samples),
                    'case_type': np.random.choice(['personal_injury', 'contract', 'employment'], n_samples),
                    'evidence_quality': np.random.uniform(0, 1, n_samples),
                    'won_case': np.random.choice([0, 1], n_samples, p=[0.4, 0.6])
                }
            
            else:
                # Default mock data
                data = {
                    'feature_1': np.random.randn(n_samples),
                    'feature_2': np.random.randn(n_samples),
                    'feature_3': np.random.choice(['A', 'B', 'C'], n_samples),
                    'target': np.random.randn(n_samples)
                }
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()

    async def _create_model(self, algorithm: str, outcome_type: OutcomeType):
        """Create ML model based on algorithm and outcome type."""
        if outcome_type in [OutcomeType.CLASSIFICATION, OutcomeType.PROBABILITY]:
            if algorithm == 'random_forest':
                return RandomForestClassifier(n_estimators=100, random_state=42)
            elif algorithm == 'gradient_boosting':
                return GradientBoostingClassifier(random_state=42)
            elif algorithm == 'logistic_regression':
                return LogisticRegression(random_state=42, max_iter=1000)
        else:  # Regression
            if algorithm == 'random_forest':
                return RandomForestRegressor(n_estimators=100, random_state=42)
            elif algorithm == 'gradient_boosting':
                return GradientBoostingRegressor(random_state=42)
            elif algorithm == 'linear_regression':
                return LinearRegression()
        
        # Default to random forest
        if outcome_type in [OutcomeType.CLASSIFICATION, OutcomeType.PROBABILITY]:
            return RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            return RandomForestRegressor(n_estimators=100, random_state=42)

    async def _generate_prediction_insights(
        self,
        model_type: PredictionModel,
        predicted_value: Any,
        input_features: Dict[str, Any],
        feature_importance: Dict[str, float],
        confidence_score: float
    ) -> Tuple[str, List[str], List[str]]:
        """Generate explanation, recommendations, and risk factors for prediction."""
        try:
            explanation = ""
            recommendations = []
            risk_factors = []
            
            if model_type == PredictionModel.CASE_OUTCOME:
                explanation = f"Based on case characteristics, the predicted outcome is '{predicted_value}' with {confidence_score:.1%} confidence."
                
                if predicted_value == 'won':
                    recommendations.append("Focus on strengths identified in case analysis")
                    recommendations.append("Prepare comprehensive evidence presentation")
                elif predicted_value == 'lost':
                    recommendations.append("Consider settlement negotiations")
                    recommendations.append("Review case strategy and potential weaknesses")
                    risk_factors.append("Low win probability based on historical patterns")
                else:  # settled
                    recommendations.append("Prepare settlement negotiation strategy")
                    recommendations.append("Establish acceptable settlement range")
                
                # Add feature-based insights
                if 'attorney_experience' in feature_importance and feature_importance['attorney_experience'] > 0.2:
                    if input_features.get('attorney_experience', 0) < 5:
                        risk_factors.append("Limited attorney experience may impact outcome")
                    
            elif model_type == PredictionModel.SETTLEMENT_AMOUNT:
                explanation = f"Predicted settlement amount: ${predicted_value:,.2f} based on case factors."
                
                recommendations.append(f"Target settlement range: ${predicted_value * 0.8:,.2f} - ${predicted_value * 1.2:,.2f}")
                recommendations.append("Document all damages and losses comprehensively")
                
                if input_features.get('case_value', 0) > predicted_value * 2:
                    risk_factors.append("Settlement amount significantly lower than claimed damages")
                    
            elif model_type == PredictionModel.CASE_DURATION:
                explanation = f"Estimated case duration: {predicted_value:.0f} days ({predicted_value/30:.1f} months)."
                
                if predicted_value > 365:
                    recommendations.append("Plan for extended litigation timeline")
                    recommendations.append("Consider interim cost management strategies")
                    risk_factors.append("Extended case duration may increase costs")
                else:
                    recommendations.append("Case likely to resolve within reasonable timeframe")
                    
            elif model_type == PredictionModel.WIN_PROBABILITY:
                explanation = f"Win probability: {predicted_value:.1%} based on case analysis."
                
                if predicted_value > 0.7:
                    recommendations.append("Strong case - proceed with confidence")
                    recommendations.append("Consider aggressive trial strategy")
                elif predicted_value < 0.3:
                    recommendations.append("Consider settlement or case review")
                    risk_factors.append("Low win probability indicates challenging case")
                else:
                    recommendations.append("Moderate case strength - prepare thoroughly")
                    recommendations.append("Keep settlement options open")
            
            # Add general confidence-based insights
            if confidence_score < 0.6:
                risk_factors.append("Prediction confidence is moderate - monitor case developments")
            elif confidence_score > 0.9:
                recommendations.append("High prediction confidence supports strategic planning")
            
            return explanation, recommendations, risk_factors
            
        except Exception as e:
            logger.error(f"Error generating prediction insights: {e}")
            return "Prediction generated", [], []