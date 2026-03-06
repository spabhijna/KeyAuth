"""
Prediction logic for keystroke verification
Uses trained Isolation Forest model for user authentication
"""

import numpy as np
from .train_model import load_model, model_exists


def verify_user(features: list, user_id: int) -> dict:
    """
    Verify if typing pattern matches user's profile.
    
    Args:
        features: Feature vector [avg_hold_time, hold_time_std, avg_flight_time, 
                                  flight_time_std, typing_speed, backspace_rate]
        user_id: User ID to verify against
    
    Returns:
        dict with prediction (1=genuine, -1=anomaly) and confidence score
    """
    # Check if model exists for this user
    if not model_exists(user_id):
        return {
            "prediction": -1,
            "confidence": 0.0,
            "error": "Model not trained for this user"
        }
    
    # Load the trained model
    model = load_model(user_id)
    
    if model is None:
        return {
            "prediction": -1,
            "confidence": 0.0,
            "error": "Failed to load model"
        }
    
    # Convert features to numpy array
    X = np.array([features])
    
    # Get prediction: 1 = inlier (genuine), -1 = outlier (anomaly)
    prediction = model.predict(X)[0]
    
    # Get anomaly score (higher = more normal, lower = more anomalous)
    # decision_function returns negative scores for outliers, positive for inliers
    score = model.decision_function(X)[0]
    
    # Convert score to confidence (0.0 to 1.0)
    # Sigmoid-like transformation to map scores to [0, 1]
    confidence = 1 / (1 + np.exp(-score * 5))
    
    return {
        "prediction": int(prediction),
        "confidence": round(float(confidence), 2)
    }
