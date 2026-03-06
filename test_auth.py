#!/usr/bin/env python3
"""
End-to-end test for the keystroke authentication system.
Tests that:
1. Same user with similar rhythm passes
2. Intruder with different rhythm fails  
3. Same user typing slower (but same rhythm) passes (normalization works)
"""

import urllib.request
import urllib.error
import json
import random


def post_json(url, data):
    """Make a POST request with JSON data using urllib."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))


# Define per-character timing fingerprint for a user
# This simulates real typing where each person has consistent per-key timing
USER_A_CHAR_PATTERNS = {
    'A': 110, 'u': 85, 't': 95, 'h': 90, 'e': 80, 'n': 88, 'i': 75, 'c': 92,
    'a': 82, 'o': 87, ' ': 60, 's': 93, 'k': 98, 'y': 105, 'r': 89
}

INTRUDER_CHAR_PATTERNS = {
    'A': 70, 'u': 65, 't': 55, 'h': 50, 'e': 45, 'n': 60, 'i': 40, 'c': 55,
    'a': 48, 'o': 52, ' ': 30, 's': 58, 'k': 62, 'y': 65, 'r': 50
}


def generate_sample_with_pattern(char_patterns, flight_base=115, variation=0.10, speed_multiplier=1.0):
    """
    Generate a typing sample with consistent per-character timing patterns.
    This simulates real typing where users have unique timing for each key.
    """
    phrase = "Authentication is the key to security"
    keystrokes = []
    current_time = 0
    
    for i, char in enumerate(phrase):
        base_hold = char_patterns.get(char, 90) * speed_multiplier
        hold_variation = 1 + random.uniform(-variation, variation)
        
        keystrokes.append({
            "key": char,
            "type": "down",
            "time": int(current_time)
        })
        
        hold_time = base_hold * hold_variation
        keystrokes.append({
            "key": char,
            "type": "up",
            "time": int(current_time + hold_time)
        })
        
        if i < len(phrase) - 1:
            flight_variation = 1 + random.uniform(-variation, variation)
            current_time += flight_base * speed_multiplier * flight_variation
    
    return keystrokes


def main():
    BASE_URL = "http://localhost:8000"
    USER_ID = 1  # Use the newly created user
    
    print("Generating 20 training samples with consistent per-key timing...")
    samples = [generate_sample_with_pattern(USER_A_CHAR_PATTERNS) for _ in range(20)]
    
    print(f"Training model for user {USER_ID}...")
    result = post_json(f"{BASE_URL}/train", {"user_id": USER_ID, "samples": samples})
    print(f"Training response: {result}")
    
    # Test 1: Same user with similar rhythm (should PASS)
    print("\n" + "="*50)
    print("TEST 1: Same user (same per-key pattern) - Should PASS")
    print("="*50)
    test_sample = generate_sample_with_pattern(USER_A_CHAR_PATTERNS)
    result = post_json(f"{BASE_URL}/verify", {"user_id": USER_ID, "keystrokes": test_sample})
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model scores: {result.get('model_scores', {})}")
    
    # Test 2: Intruder with different rhythm (should FAIL)
    print("\n" + "="*50)
    print("TEST 2: Intruder (different per-key pattern) - Should FAIL")
    print("="*50)
    intruder_sample = generate_sample_with_pattern(INTRUDER_CHAR_PATTERNS, variation=0.25)
    result = post_json(f"{BASE_URL}/verify", {"user_id": USER_ID, "keystrokes": intruder_sample})
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model scores: {result.get('model_scores', {})}")
    
    # Test 3: Same user typing slower (should PASS - same pattern, just scaled)
    print("\n" + "="*50)
    print("TEST 3: Same user typing 50% slower - Should PASS (normalized)")
    print("="*50)
    slow_sample = generate_sample_with_pattern(USER_A_CHAR_PATTERNS, speed_multiplier=1.5)
    result = post_json(f"{BASE_URL}/verify", {"user_id": USER_ID, "keystrokes": slow_sample})
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Model scores: {result.get('model_scores', {})}")


if __name__ == "__main__":
    main()
