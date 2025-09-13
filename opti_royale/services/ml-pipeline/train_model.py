#!/usr/bin/env python3
"""
Continuous Learning Pipeline for Clash Royale Optimization

This script implements the continuous learning system that:
1. Collects new analysis data from users
2. Preprocesses and validates the data
3. Retrains models with improved data
4. Evaluates model performance
5. Deploys better models automatically
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import mlflow
import mlflow.pytorch
from feast import FeatureStore
import redis
import psycopg2
from sqlalchemy import create_engine
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClashRoyaleOptimizationModel(nn.Module):
    """
    Neural network for predicting optimal card placements
    """
    def __init__(self, input_dim: int = 256, hidden_dims: List[int] = [512, 256, 128]):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.BatchNorm1d(hidden_dim)
            ])
            prev_dim = hidden_dim
        
        # Output layer for 18x32 grid (576 positions) + confidence score
        layers.append(nn.Linear(prev_dim, 577))
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.network(x)

class ContinuousLearningPipeline:
    """
    Main pipeline for continuous model improvement
    """
    
    def __init__(self):
        self.db_engine = create_engine(os.getenv('DATABASE_URL'))
        self.redis_client = redis.from_url(os.getenv('REDIS_URL'))
        self.feature_store = FeatureStore(repo_path="./feature_store")
        self.mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
        
        # Model configuration
        self.model_version = "1.0.0"
        self.retrain_threshold = int(os.getenv('MODEL_RETRAIN_THRESHOLD', 1000))
        self.performance_threshold = 0.85  # Minimum accuracy to deploy
        
        # Initialize MLflow
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment("clash_royale_optimization")
        
    async def collect_new_training_data(self) -> pd.DataFrame:
        """
        Collect new analysis data since last training run
        """
        logger.info("Collecting new training data...")
        
        query = """
        SELECT 
            ah.id as analysis_id,
            ah.user_id,
            ah.overall_score,
            ah.placement_accuracy,
            ah.elixir_efficiency,
            ah.card_placements,
            ah.optimal_placements,
            ah.user_rating,
            ah.model_version,
            ah.confidence_score,
            cp.card_name,
            cp.x_coordinate,
            cp.y_coordinate,
            cp.optimal_x,
            cp.optimal_y,
            cp.placement_score,
            cp.elixir_available,
            cp.enemy_units_nearby,
            cp.friendly_units_nearby
        FROM analysis_history ah
        JOIN card_placements cp ON ah.id = cp.analysis_id
        WHERE ah.analysis_timestamp > NOW() - INTERVAL '24 hours'
        AND ah.user_rating IS NOT NULL
        AND ah.user_rating >= 3  -- Only use positively rated analyses
        ORDER BY ah.analysis_timestamp DESC
        """
        
        df = pd.read_sql(query, self.db_engine)
        logger.info(f"Collected {len(df)} new training samples")
        
        return df
    
    def preprocess_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert raw data into ML features and labels
        """
        logger.info("Preprocessing features...")
        
        # Extract features from game state
        features = []
        labels = []
        
        for _, row in df.iterrows():
            # Game context features
            feature_vector = [
                row['elixir_available'],
                row['placement_score'],
                len(eval(row['enemy_units_nearby']) if row['enemy_units_nearby'] else []),
                len(eval(row['friendly_units_nearby']) if row['friendly_units_nearby'] else []),
                row['x_coordinate'],
                row['y_coordinate'],
            ]
            
            # Card encoding (one-hot for card types)
            card_features = self._encode_card(row['card_name'])
            feature_vector.extend(card_features)
            
            # Board state encoding
            board_features = self._encode_board_state(row)
            feature_vector.extend(board_features)
            
            # Pad to fixed size
            while len(feature_vector) < 256:
                feature_vector.append(0.0)
            
            features.append(feature_vector[:256])
            
            # Label: optimal position as one-hot encoding
            optimal_pos = row['optimal_x'] * 32 + row['optimal_y']
            label = [0.0] * 577
            label[optimal_pos] = 1.0
            label[576] = row['confidence_score']  # Confidence score
            
            labels.append(label)
        
        return np.array(features, dtype=np.float32), np.array(labels, dtype=np.float32)
    
    def _encode_card(self, card_name: str) -> List[float]:
        """
        Encode card name into feature vector
        """
        # Simplified card encoding - in production, use proper embeddings
        card_map = {
            'knight': [1, 0, 0, 0, 3],  # ground, melee, common, medium, 3 elixir
            'archers': [0, 1, 1, 0, 3],  # air+ground, ranged, common, medium, 3 elixir
            'fireball': [0, 0, 0, 1, 4],  # spell, area, common, high, 4 elixir
            # Add more cards...
        }
        
        return card_map.get(card_name.lower(), [0, 0, 0, 0, 0])
    
    def _encode_board_state(self, row: Dict) -> List[float]:
        """
        Encode current board state into features
        """
        # Simplified board encoding
        # In production, this would be much more sophisticated
        board_features = []
        
        # Enemy unit positions and types
        enemy_units = eval(row['enemy_units_nearby']) if row['enemy_units_nearby'] else []
        for i in range(10):  # Max 10 enemy units
            if i < len(enemy_units):
                unit = enemy_units[i]
                board_features.extend([
                    unit.get('x', 0), 
                    unit.get('y', 0), 
                    unit.get('health', 0) / 1000.0,  # Normalized health
                    unit.get('damage', 0) / 1000.0    # Normalized damage
                ])
            else:
                board_features.extend([0, 0, 0, 0])
        
        # Friendly unit positions and types  
        friendly_units = eval(row['friendly_units_nearby']) if row['friendly_units_nearby'] else []
        for i in range(10):  # Max 10 friendly units
            if i < len(friendly_units):
                unit = friendly_units[i]
                board_features.extend([
                    unit.get('x', 0),
                    unit.get('y', 0),
                    unit.get('health', 0) / 1000.0,
                    unit.get('damage', 0) / 1000.0
                ])
            else:
                board_features.extend([0, 0, 0, 0])
        
        return board_features
    
    async def train_model(self, X: np.ndarray, y: np.ndarray) -> torch.nn.Module:
        """
        Train the optimization model
        """
        logger.info("Training model...")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Convert to PyTorch tensors
        X_train = torch.FloatTensor(X_train)
        y_train = torch.FloatTensor(y_train)
        X_val = torch.FloatTensor(X_val)
        y_val = torch.FloatTensor(y_val)
        
        # Initialize model
        model = ClashRoyaleOptimizationModel()
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        # Training loop
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        with mlflow.start_run():
            for epoch in range(100):  # Max 100 epochs
                model.train()
                optimizer.zero_grad()
                
                # Forward pass
                outputs = model(X_train)
                loss = criterion(outputs, y_train)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                # Validation
                model.eval()
                with torch.no_grad():
                    val_outputs = model(X_val)
                    val_loss = criterion(val_outputs, y_val)
                
                # Logging
                mlflow.log_metric("train_loss", loss.item(), step=epoch)
                mlflow.log_metric("val_loss", val_loss.item(), step=epoch)
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Train Loss: {loss.item():.4f}, Val Loss: {val_loss.item():.4f}")
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Save best model
                    torch.save(model.state_dict(), 'best_model.pth')
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info(f"Early stopping at epoch {epoch}")
                        break
            
            # Load best model
            model.load_state_dict(torch.load('best_model.pth'))
            
            # Calculate final metrics
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val)
                val_predictions = torch.argmax(val_outputs[:, :576], dim=1)
                val_targets = torch.argmax(y_val[:, :576], dim=1)
                accuracy = (val_predictions == val_targets).float().mean().item()
                
                mlflow.log_metric("final_accuracy", accuracy)
                mlflow.pytorch.log_model(model, "model")
                
                logger.info(f"Final model accuracy: {accuracy:.4f}")
        
        return model, accuracy
    
    async def evaluate_model_performance(self, model: torch.nn.Module) -> Dict[str, float]:
        """
        Evaluate model on recent production data
        """
        logger.info("Evaluating model performance...")
        
        # Get recent production data for evaluation
        query = """
        SELECT * FROM analysis_history 
        WHERE analysis_timestamp > NOW() - INTERVAL '7 days'
        AND user_rating IS NOT NULL
        ORDER BY analysis_timestamp DESC
        LIMIT 1000
        """
        
        eval_df = pd.read_sql(query, self.db_engine)
        
        if len(eval_df) == 0:
            logger.warning("No evaluation data available")
            return {"accuracy": 0.0}
        
        # Preprocess evaluation data
        X_eval, y_eval = self.preprocess_features(eval_df)
        
        # Convert to tensors
        X_eval = torch.FloatTensor(X_eval)
        y_eval = torch.FloatTensor(y_eval)
        
        # Evaluate
        model.eval()
        with torch.no_grad():
            predictions = model(X_eval)
            pred_positions = torch.argmax(predictions[:, :576], dim=1)
            true_positions = torch.argmax(y_eval[:, :576], dim=1)
            
            accuracy = (pred_positions == true_positions).float().mean().item()
            
            # Calculate additional metrics
            precision, recall, f1, _ = precision_recall_fscore_support(
                true_positions.numpy(), pred_positions.numpy(), average='weighted'
            )
        
        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
        
        logger.info(f"Model evaluation metrics: {metrics}")
        return metrics
    
    async def deploy_model(self, model: torch.nn.Module, metrics: Dict[str, float]):
        """
        Deploy model if it meets performance criteria
        """
        if metrics["accuracy"] >= self.performance_threshold:
            logger.info(f"Deploying model with accuracy {metrics['accuracy']:.4f}")
            
            # Save model for production serving
            model_path = f"models/clash_royale_model_v{self.model_version}.pth"
            torch.save(model.state_dict(), model_path)
            
            # Update model version in Redis
            self.redis_client.set("current_model_version", self.model_version)
            self.redis_client.set("current_model_path", model_path)
            
            # Store model metadata
            model_metadata = {
                "version": self.model_version,
                "accuracy": metrics["accuracy"],
                "deployment_time": datetime.now().isoformat(),
                "training_samples": await self._get_training_sample_count()
            }
            
            # Update database
            query = """
            INSERT INTO model_performance 
            (model_version, model_type, accuracy, precision_score, recall_score, f1_score, deployment_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            with self.db_engine.connect() as conn:
                conn.execute(query, (
                    self.model_version,
                    "neural_network",
                    metrics["accuracy"],
                    metrics["precision"], 
                    metrics["recall"],
                    metrics["f1_score"],
                    datetime.now()
                ))
            
            logger.info("Model deployed successfully")
        else:
            logger.warning(f"Model accuracy {metrics['accuracy']:.4f} below threshold {self.performance_threshold}")
    
    async def _get_training_sample_count(self) -> int:
        """Get count of training samples used"""
        query = "SELECT COUNT(*) FROM analysis_history WHERE analysis_timestamp > NOW() - INTERVAL '24 hours'"
        with self.db_engine.connect() as conn:
            result = conn.execute(query)
            return result.fetchone()[0]
    
    async def run_training_pipeline(self):
        """
        Main training pipeline execution
        """
        logger.info("Starting continuous learning pipeline...")
        
        try:
            # Check if we have enough new data to retrain
            new_data = await self.collect_new_training_data()
            
            if len(new_data) < self.retrain_threshold:
                logger.info(f"Not enough new data ({len(new_data)} < {self.retrain_threshold}). Skipping training.")
                return
            
            # Preprocess data
            X, y = self.preprocess_features(new_data)
            
            # Train model
            model, accuracy = await self.train_model(X, y)
            
            # Evaluate performance
            metrics = await self.evaluate_model_performance(model)
            
            # Deploy if good enough
            await self.deploy_model(model, metrics)
            
            logger.info("Training pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {str(e)}")
            raise

async def main():
    """
    Main entry point for continuous learning
    """
    pipeline = ContinuousLearningPipeline()
    await pipeline.run_training_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
