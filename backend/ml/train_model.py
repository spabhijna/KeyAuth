"""
Model training logic for keystroke biometrics
Trains an Isolation Forest model for each user
"""

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from pathlib import Path


# Directory to store trained models
MODELS_DIR = Path(__file__).parent / "models"


def train_model(samples: list, user_id: int) -> IsolationForest:
    """
    Train an Isolation Forest model for a specific user.
    
    Args:
        samples: List of feature vectors from typing sessions
                 Each vector: [avg_hold_time, hold_time_std, avg_flight_time, 
                              flight_time_std, typing_speed, backspace_rate]
        user_id: User ID to associate the model with
    
    Returns:
        Trained IsolationForest model
    """
    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert to numpy array for scikit-learn
    X = np.array(samples)
    
    # Train Isolation Forest
    # contamination='auto' since all training samples are genuine user data
    # n_estimators=100 for good anomaly detection performance
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,  # Expect up to 10% anomalies in real usage
        random_state=42,
        n_jobs=-1  # Use all available cores
    )
    
    model.fit(X)
    
    # Save the trained model
    model_path = MODELS_DIR / f"user_{user_id}.pkl"
    joblib.dump(model, model_path)
    
    return model


def load_model(user_id: int) -> IsolationForest | None:
    """
    Load a trained model for a specific user.
    
    Args:
        user_id: User ID to load model for
    
    Returns:
        Trained IsolationForest model or None if not found
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
