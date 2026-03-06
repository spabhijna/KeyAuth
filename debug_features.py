#!/usr/bin/env python3
"""Debug script to understand feature extraction and model behavior."""

from backend.ml.feature_extractor import extract_features
import random

def generate_sample(base_hold=90, base_flight=120, variation=0.15):
    phrase = 'Authentication is the key to security'
    keystrokes = []
    current_time = 0
    
    for i, char in enumerate(phrase):
        hold_variation = 1 + random.uniform(-variation, variation)
        flight_variation = 1 + random.uniform(-variation, variation)
        
        keystrokes.append({'key': char, 'type': 'down', 'time': int(current_time)})
        hold_time = base_hold * hold_variation
        keystrokes.append({'key': char, 'type': 'up', 'time': int(current_time + hold_time)})
        
        if i < len(phrase) - 1:
            current_time += base_flight * flight_variation
    
    return keystrokes

# Set random seed for reproducibility
random.seed(42)

print('=== Feature Extraction Debug ===\n')

print('Sample 1 (user A):')
s1 = extract_features(generate_sample(base_hold=95, base_flight=115))
print([round(x, 2) for x in s1])

random.seed(43)
print('\nSample 2 (user A - same rhythm, different seed):')
s2 = extract_features(generate_sample(base_hold=95, base_flight=115))
print([round(x, 2) for x in s2])

random.seed(44)
print('\nSample 3 (intruder - different rhythm):')
s3 = extract_features(generate_sample(base_hold=60, base_flight=80, variation=0.35))
print([round(x, 2) for x in s3])

random.seed(45)
print('\nSample 4 (user A slower):')
s4 = extract_features(generate_sample(base_hold=140, base_flight=170))
print([round(x, 2) for x in s4])

print('\n--- Comparing ---')
print('Feature names: mean_hold, std_hold, mean_flight, std_flight, h0-h5, f0-f5')
print(f'\nUser A sample 1 mean_hold: {s1[0]:.1f}ms, std: {s1[1]:.1f}')
print(f'User A sample 2 mean_hold: {s2[0]:.1f}ms, std: {s2[1]:.1f}')
print(f'Intruder mean_hold:        {s3[0]:.1f}ms, std: {s3[1]:.1f}')
print(f'User A slower mean_hold:   {s4[0]:.1f}ms, std: {s4[1]:.1f}')

print('\n--- Normalized hold values (should be similar for same user rhythm) ---')
print(f'User A sample 1: {[round(x, 2) for x in s1[4:10]]}')
print(f'User A sample 2: {[round(x, 2) for x in s2[4:10]]}')
print(f'Intruder:        {[round(x, 2) for x in s3[4:10]]}')
print(f'User A slower:   {[round(x, 2) for x in s4[4:10]]}')
