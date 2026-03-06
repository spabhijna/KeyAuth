"""
Feature extraction from raw keystroke events
Converts keystroke timings into 16-feature vector for ML model

Features capture both statistical summaries AND per-key timing rhythm:
- 4 statistical features (mean/std for hold and flight times)
- 6 normalized first hold times (captures typing rhythm pattern)
- 6 normalized first flight times (captures inter-key timing pattern)

The normalization (time / mean_time) captures RHYTHM not absolute speed,
so a user typing slower due to being tired won't trigger false rejection.
"""

# Number of per-key timing features to capture
NUM_TIMING_FEATURES = 6


def extract_features(keystrokes: list) -> list:
    """
    Extract typing features from raw keystroke events.
    
    Input format:
    [
        {"key": "a", "type": "down", "time": 0},
        {"key": "a", "type": "up", "time": 100},
        ...
    ]
    
    Output format (16-feature vector):
    [
        mean_hold, std_hold,           # Statistical hold features
        mean_flight, std_flight,       # Statistical flight features
        hold_0, hold_1, ..., hold_5,   # First 6 normalized hold times
        flight_0, flight_1, ..., flight_5  # First 6 normalized flight times
    ]
    
    Normalized timing = raw_time / mean_time
    This captures typing RHYTHM (pattern) rather than absolute speed.
    """
    # Default 16-feature vector for empty/invalid input
    default_features = [
        100.0, 10.0,  # mean_hold, std_hold
        80.0, 15.0,   # mean_flight, std_flight
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0,  # normalized holds (1.0 = neutral)
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0   # normalized flights (1.0 = neutral)
    ]
    
    if not keystrokes or len(keystrokes) < 2:
        return default_features
    
    # Sort events by time to process sequentially
    sorted_events = sorted(keystrokes, key=lambda e: e["time"])
    
    # Track pending keydown events (key -> list of down times)
    # Using list to handle repeated characters correctly (FIFO)
    pending_downs = {}
    
    # Collect ALL hold times in sequence order
    hold_times = []
    
    for event in sorted_events:
        key = event["key"]
        
        # Skip backspace events entirely - they only indicate typos, not typing rhythm
        if key.lower() == "backspace":
            continue
            
        if event["type"] == "down":
            # Add this keydown to pending list for this key
            if key not in pending_downs:
                pending_downs[key] = []
            pending_downs[key].append(event["time"])
            
        elif event["type"] == "up":
            # Match with earliest pending keydown for this key (FIFO)
            if key in pending_downs and pending_downs[key]:
                down_time = pending_downs[key].pop(0)
                hold_time = event["time"] - down_time
                if hold_time > 0:
                    hold_times.append(hold_time)
    
    # Calculate flight times (time between consecutive key presses)
    # Filter out backspace events
    down_events = sorted(
        [e for e in keystrokes if e["type"] == "down" and e["key"].lower() != "backspace"],
        key=lambda x: x["time"]
    )
    
    flight_times = []
    for i in range(1, len(down_events)):
        flight = down_events[i]["time"] - down_events[i-1]["time"]
        if flight > 0:
            flight_times.append(flight)
    
    # ===== Helper functions =====
    def mean(lst):
        return sum(lst) / len(lst) if lst else 0.0
    
    def std(lst):
        if len(lst) < 2:
            return 0.0
        m = mean(lst)
        variance = sum((x - m) ** 2 for x in lst) / len(lst)
        return variance ** 0.5
    
    # ===== Statistical features =====
    mean_hold = mean(hold_times) if hold_times else 100.0
    std_hold = std(hold_times) if hold_times else 10.0
    mean_flight = mean(flight_times) if flight_times else 80.0
    std_flight = std(flight_times) if flight_times else 15.0
    
    # ===== Normalized per-key timing features =====
    # Normalize by dividing by mean - captures RHYTHM not absolute speed
    # A user typing slower (tired) will still have same normalized pattern
    
    def normalize_and_pad(times: list, mean_time: float, count: int) -> list:
        """Normalize times and pad/truncate to fixed length."""
        if mean_time <= 0:
            mean_time = 1.0  # Avoid division by zero
        
        # Normalize: time / mean gives ratio (1.0 = average)
        normalized = [t / mean_time for t in times[:count]]
        
        # Pad with 1.0 (neutral value) if not enough samples
        while len(normalized) < count:
            normalized.append(1.0)
        
        return normalized
    
    # First 6 normalized hold times
    norm_holds = normalize_and_pad(hold_times, mean_hold, NUM_TIMING_FEATURES)
    
    # First 6 normalized flight times  
    norm_flights = normalize_and_pad(flight_times, mean_flight, NUM_TIMING_FEATURES)
    
    # ===== Build 16-feature vector =====
    return [
        mean_hold, std_hold,
        mean_flight, std_flight,
        *norm_holds,    # 6 normalized hold times
        *norm_flights   # 6 normalized flight times
    ]


def get_feature_names() -> list:
    """Return names of all 16 features for debugging/display."""
    return [
        "mean_hold", "std_hold",
        "mean_flight", "std_flight",
        "hold_0", "hold_1", "hold_2", "hold_3", "hold_4", "hold_5",
        "flight_0", "flight_1", "flight_2", "flight_3", "flight_4", "flight_5"
    ]
