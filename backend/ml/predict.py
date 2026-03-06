"""
Multi-model prediction for keystroke verification
Uses three models for robust authentication:
1. One-Class SVM
2. Isolation Forest
3. DTW Similarity
"""

import numpy as np
from .train_model import load_model, model_exists


def dtw_distance(seq1: np.ndarray, seq2: np.ndarray) -> float:
    """
    Compute Dynamic Time Warping distance between two sequences.
    Simple implementation without external dependency.
    
    Args:
        seq1: First sequence (1D array)
        seq2: Second sequence (1D array)
    
    Returns:
        DTW distance (lower = more similar)
    """
    n, m = len(seq1), len(seq2)
    
    # Create cost matrix
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(seq1[i - 1] - seq2[j - 1])
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j],      # insertion
                dtw_matrix[i, j - 1],      # deletion
                dtw_matrix[i - 1, j - 1]   # match
            )
    
    return dtw_matrix[n, m]


def compute_dtw_similarity(features: np.ndarray, reference_samples: np.ndarray, scaler) -> float:
    """
    Compute DTW similarity score against reference samples.
    
    Args:
        features: Single feature vector (16 features)
        reference_samples: Array of reference feature vectors
        scaler: StandardScaler fitted on reference samples
    
    Returns:
        Similarity score (0.0 to 1.0, higher = more similar)
    """
    # Normalize the input features using the same scaler
    normalized_features = scaler.transform([features])[0]
    
    # Compute DTW distance to each reference sample
    distances = []
    for ref_sample in reference_samples:
        dist = dtw_distance(normalized_features, ref_sample)
        distances.append(dist)
    
    # Use minimum distance (best match)
    min_dist = min(distances)
    avg_dist = np.mean(distances)
    
    # Convert distance to similarity score using exponential decay
    # Typical normalized feature distances range from 0-20 for 16-feature vectors
    similarity = np.exp(-min_dist / 10.0)  # Decay factor of 10 for 16 features
    
    return float(similarity)


def verify_user(features: list, user_id: int) -> dict:
    """
    Verify if typing pattern matches user's profile using all three models.
    
    Args:
        features: 16-feature vector [mean_hold, std_hold, mean_flight, std_flight,
                                     hold_0..hold_5, flight_0..flight_5]
                  First 4 are statistical features, remaining 12 are normalized
                  per-key timing values that capture unique typing rhythm.
        user_id: User ID to verify against
    
    Returns:
        dict with prediction, confidence, and individual model scores
    """
    # Check if model exists for this user
    if not model_exists(user_id):
        return {
            "prediction": -1,
            "confidence": 0.0,
            "model_scores": {},
            "error": "Model not trained for this user"
        }
    
    # Load the model package
    model_package = load_model(user_id)
    
    if model_package is None:
        return {
            "prediction": -1,
            "confidence": 0.0,
            "model_scores": {},
            "error": "Failed to load model"
        }
    
    # Convert features to numpy array
    X = np.array([features])
    
    model_scores = {}
    predictions = []
    
    # ========== One-Class SVM ==========
    svm_model = model_package['svm']
    svm_pred = svm_model.predict(X)[0]
    svm_score = svm_model.decision_function(X)[0]
    svm_confidence = 1 / (1 + np.exp(-svm_score * 2))
    model_scores['svm'] = round(float(svm_confidence), 2)
    predictions.append(svm_pred)
    
    # ========== Isolation Forest ==========
    iforest_model = model_package['iforest']
    iforest_pred = iforest_model.predict(X)[0]
    iforest_score = iforest_model.decision_function(X)[0]
    # IsolationForest scores are typically in [-0.5, 0.5] range
    iforest_confidence = 1 / (1 + np.exp(-iforest_score * 10))
    model_scores['iforest'] = round(float(iforest_confidence), 2)
    predictions.append(iforest_pred)
    
    # ========== DTW Similarity ==========
    dtw_reference = model_package['dtw_reference']
    dtw_scaler = model_package['dtw_scaler']
    dtw_similarity = compute_dtw_similarity(np.array(features), dtw_reference, dtw_scaler)
    model_scores['dtw'] = round(float(dtw_similarity), 2)
    # Convert DTW similarity to prediction (-1 or 1)
    # Threshold of 0.45 requires stronger similarity match
    dtw_pred = 1 if dtw_similarity > 0.45 else -1
    predictions.append(dtw_pred)
    
    # ========== Ensemble Decision ==========
    # Final confidence: weighted average of scores
    # Give slightly more weight to SVM (proven for small samples)
    weights = {'svm': 0.4, 'iforest': 0.3, 'dtw': 0.3}
    weighted_confidence = sum(model_scores[m] * weights[m] for m in weights)
    
    # Strict majority vote: at least 2 of 3 models must agree
    # sum(predictions) can be -3, -1, 1, or 3
    # -3: all reject, -1: 2 reject/1 accept, 1: 2 accept/1 reject, 3: all accept
    vote_prediction = 1 if sum(predictions) >= 1 else -1
    
    # Final prediction based on strict criteria:
    # 1. Must pass majority vote AND
    # 2. Must have minimum confidence of 0.35
    final_prediction = -1  # Default to reject
    if vote_prediction == 1 and weighted_confidence >= 0.35:
        final_prediction = 1
    
    return {
        "prediction": int(final_prediction),
        "confidence": round(float(weighted_confidence), 2),
        "model_scores": model_scores
    }
