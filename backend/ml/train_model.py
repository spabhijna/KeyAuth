"""
Model training logic for keystroke biometrics
Trains a Pipeline (StandardScaler + Isolation Forest) model for each user
"""

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from pathlib import Path


# Directory to store trained models
MODELS_DIR = Path(__file__).parent / "models"


def train_model(samples: list, user_id: int) -> Pipeline:
    """
    Train a Pipeline model (StandardScaler + IsolationForest) for a specific user.
    
    Args:
        samples: List of 12-feature vectors from typing sessions
                 Each vector: [mean_hold, std_hold, median_hold, min_hold, max_hold,
                              mean_flight, std_flight, median_flight,
                              typing_speed, total_time, duration_per_char, backspace_rate]
        user_id: User ID to associate the model with
    
    Returns:
        Trained Pipeline model
    """
    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert to numpy array for scikit-learn
    X = np.array(samples)
    
    # Create Pipeline with StandardScaler and IsolationForest
    # Parameters optimized for keystroke biometrics with small sample size:
    #   StandardScaler: with_mean=True, with_std=True (defaults)
    #   IsolationForest: n_estimators=200, contamination=0.03, bootstrap=True
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('isolation_forest', IsolationForest(
            n_estimators=200,
            contamination=0.03,
            max_samples=1.0,      # Use all training samples
            max_features=1.0,     # Use all 6 features
            bootstrap=True,       # Helps with small sample size
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    model.fit(X)
    
    # Save the trained model
    model_path = MODELS_DIR / f"user_{user_id}.pkl"
    joblib.dump(model, model_path)
    
    return model


def load_model(user_id: int) -> Pipeline | None:
    """
    Load a trained model for a specific user.
    
    Args:
        user_id: User ID to load model for
    
    Returns:
        Trained Pipeline model or None if not found
    """
    model_path = MODELS_DIR / f"user_{user_id}.pkl"
    
    if not model_path.exists():
        return None
    
    return joblib.load(model_path)


def model_exists(user_id: int) -> bool:
    """
    Check if a trained model exists for a user.
    
    Args:
        user_id: User ID to check
    
    Returns:
        True if model exists, False otherwise
    """
    model_path = MODELS_DIR / f"user_{user_id}.pkl"
    return model_path.exists()
