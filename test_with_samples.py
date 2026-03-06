#!/usr/bin/env python3
"""
Test keystroke authentication using saved samples from JSON file.

Usage:
    python3 test_with_samples.py <samples.json>
    
This script will:
1. Register a test user with the samples
2. Verify using one of the training samples (should pass)
3. Verify using a modified sample (should fail)
"""

import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"


def post_json(url, data):
    """Make a POST request with JSON data."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8')), response.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8')), e.code


def load_samples(filepath):
    """Load samples from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def create_intruder_sample(original_sample):
    """Create a sample with different timing pattern (simulates intruder).
    
    We need to change the RELATIVE timing between keys, not just scale uniformly.
    This simulates someone with a different typing rhythm.
    """
    import random
    intruder = []
    
    # Group into keydown/keyup pairs and shuffle their relative timing
    for i, event in enumerate(original_sample):
        new_event = {**event}
        
        # Add random perturbation to timing (±50% variation per keystroke)
        # This changes the rhythm pattern, not just speed
        if i > 0:
            prev_time = intruder[i-1]['time']
            original_gap = event['time'] - original_sample[i-1]['time']
            # Randomize the gap significantly
            new_gap = max(10, original_gap * random.uniform(0.3, 2.0))
            new_event['time'] = int(prev_time + new_gap)
        else:
            new_event['time'] = 0
        
        intruder.append(new_event)
    
    return intruder


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_with_samples.py <samples.json>")
        print("\nExample: python3 test_with_samples.py ~/Downloads/typing_samples_*.json")
        sys.exit(1)
    
    filepath = sys.argv[1]
    print(f"Loading samples from: {filepath}")
    
    try:
        data = load_samples(filepath)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON file: {filepath}")
        sys.exit(1)
    
    samples = data.get('samples', [])
    phrase = data.get('phrase', 'Unknown phrase')
    
    print(f"Phrase: {phrase}")
    print(f"Samples loaded: {len(samples)}")
    
    if len(samples) < 20:
        print(f"Warning: Only {len(samples)} samples. Need 20 for training.")
        if len(samples) == 0:
            sys.exit(1)
    
    # Register user with samples
    print("\n" + "="*50)
    print("STEP 1: Registering user with samples...")
    print("="*50)
    
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "samples": samples[:20]  # Use first 20 samples
    }
    
    result, status = post_json(f"{BASE_URL}/register", register_data)
    
    if status == 200:
        user_id = result.get('user_id')
        print(f"✓ User registered with ID: {user_id}")
    elif status == 400 and 'already exists' in str(result):
        print("User already exists, will use existing user")
        # Login to get user_id
        login_result, _ = post_json(f"{BASE_URL}/login", {
            "username": "testuser",
            "password": "testpass123"
        })
        user_id = login_result.get('user_id', 1)
        print(f"Using existing user ID: {user_id}")
    else:
        print(f"Registration failed: {result}")
        sys.exit(1)
    
    # Test 1: Verify with same user's sample
    print("\n" + "="*50)
    print("TEST 1: Verifying with SAME USER sample (should PASS)")
    print("="*50)
    
    # Use a sample that wasn't used for training if possible
    test_sample = samples[20] if len(samples) > 20 else samples[0]
    
    verify_result, status = post_json(f"{BASE_URL}/verify", {
        "user_id": user_id,
        "keystrokes": test_sample
    })
    
    print(f"Status: {verify_result.get('status', 'unknown')}")
    print(f"Confidence: {verify_result.get('confidence', 'N/A')}")
    print(f"Model scores: {verify_result.get('model_scores', {})}")
    
    if verify_result.get('status') == 'verified':
        print("✓ PASS: User verified successfully!")
    else:
        print("✗ UNEXPECTED: User not verified (may need threshold tuning)")
    
    # Test 2: Verify with intruder pattern
    print("\n" + "="*50)
    print("TEST 2: Verifying with INTRUDER pattern (should FAIL)")
    print("="*50)
    
    intruder_sample = create_intruder_sample(samples[0])
    
    verify_result, status = post_json(f"{BASE_URL}/verify", {
        "user_id": user_id,
        "keystrokes": intruder_sample
    })
    
    print(f"Status: {verify_result.get('status', 'unknown')}")
    print(f"Confidence: {verify_result.get('confidence', 'N/A')}")
    print(f"Model scores: {verify_result.get('model_scores', {})}")
    
    if verify_result.get('status') == 'suspicious':
        print("✓ PASS: Intruder correctly detected!")
    else:
        print("✗ UNEXPECTED: Intruder passed verification")
    
    print("\n" + "="*50)
    print("Testing complete!")
    print("="*50)


if __name__ == "__main__":
    main()
