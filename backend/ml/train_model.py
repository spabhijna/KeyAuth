"""
Multi-model training for keystroke biometrics
Trains three models per user:
1. One-Class SVM - Fast, good with small samples
2. Isolation Forest - Tree-based anomaly detection
3. DTW Reference - Stores raw samples for Dynamic Time Warping similarity
"""

import joblib
import numpy as np
from sklearn.svm import OneClassSVM
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from pathlib import Path


# Directory to store trained models
MODELS_DIR = Path(__file__).parent / "models"


def train_model(samples: list, user_id: int) -> dict:
    """
    Train all models (SVM, IsolationForest, DTW reference) for a specific user.
    
    Args:
        samples: List of 16-feature vectors from typing sessions
                 Each vector: [mean_hold, std_hold, mean_flight, std_flight,
                              hold_0..hold_5, flight_0..flight_5]
                 First 4 are statistical features, remaining 12 are normalized
                 per-key timing values that capture typing rhythm.
        user_id: User ID to associate the models with
    
    Returns:
        Dict containing all trained models and reference data
    """
    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert to numpy array for scikit-learn
    X = np.array(samples)
    
    # ========== Model 1: One-Class SVM ==========
    # Fast, good decision boundary for small sample size
    svm_model = Pipeline([
        ('scaler', StandardScaler()),
        ('svm', OneClassSVM(
            kernel='rbf',
            nu=0.15,              # More lenient - allows 15% margin for natural variation
            gamma='auto'
        ))
    ])
    svm_model.fit(X)
    
    # ========== Model 2: Isolation Forest ==========
    # Tree-based anomaly detection, good for multivariate data
    iforest_model = Pipeline([
        ('scaler', StandardScaler()),
        ('iforest', IsolationForest(
            n_estimators=100,
            contamination=0.05,   # Very few outliers expected in training data
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        ))
    ])
    iforest_model.fit(X)
    
    # ========== Model 3: DTW Reference Data ==========
    # Store normalized samples for DTW similarity comparison
    scaler = StandardScaler()
    dtw_reference = scaler.fit_transform(X)
    
    # Package all models together
    model_package = {
        'svm': svm_model,
        'iforest': iforest_model,
        'dtw_reference': dtw_reference,
        'dtw_scaler': scaler,
        'raw_samples': X  # Keep raw samples for potential retraining
    }
    
    # Save the model package
    model_path = MODELS_DIR / f"user_{user_id}.pkl"
    joblib.dump(model_package, model_path)
    
    return model_package


def load_model(user_id: int) -> dict | None:
    """
    Load trained models for a specific user.
    
    Args:
        user_id: User ID to load models for
    
    Returns:
        Dict with all models or None if not found
    """
    model_path = MODELS_DIR / f"user_{user_id}.pkl"
    
    if not model_path.exists():
        return None
    
    return joblib.load(model_path)


def model_exists(user_id: int) -> bool:
    """
    Check if trained models exist for a user.
    
    Args:
        user_id: User ID to check
    
    Returns:
        True if models exist, False otherwise
    """
    model_path = MODELS_DIR / f"user_{user_id}.pkl"
    return model_path.exists()


def update_model(new_sample: list, user_id: int) -> dict | None:
    """
    Add a new verified sample and retrain all models (adaptive learning).
    
    Args:
        new_sample: 16-feature vector from a verified typing session
        user_id: User ID to update model for
    
    Returns:
        Updated model package or None if model doesn't exist
    """
    # Load existing model package
    model_package = load_model(user_id)
    if model_package is None:
        return None
    
    # Get existing samples and add new one
    raw_samples = model_package.get('raw_samples')
    if raw_samples is None:
        return None
    
    # Append new sample
    new_sample_array = np.array([new_sample])
    updated_samples = np.vstack([raw_samples, new_sample_array])
    
    # Keep only the last 50 samples to prevent model drift from old patterns
    if len(updated_samples) > 50:
        updated_samples = updated_samples[-50:]
    
    # Retrain all models with updated samples
    print(f"[ADAPTIVE] Retraining user {user_id} with {len(updated_samples)} samples")
    
    return train_model(updated_samples.tolist(), user_id)
