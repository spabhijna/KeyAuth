"""
Feature extraction from raw keystroke events
Converts keystroke timings into feature vector for ML model
"""


def extract_features(keystrokes: list) -> list:
    """
    Extract typing features from raw keystroke events.
    
    Input format:
    [
        {"key": "a", "type": "down", "time": 0},
        {"key": "a", "type": "up", "time": 100},
        ...
    ]
    
    Output format (12-feature vector):
    [
        mean_hold, std_hold, median_hold, min_hold, max_hold,
        mean_flight, std_flight, median_flight,
        typing_speed, total_time, duration_per_char, backspace_rate
    ]
    """
    if not keystrokes or len(keystrokes) < 2:
        # Default values for empty/invalid input
        return [100.0, 10.0, 100.0, 50.0, 150.0, 80.0, 15.0, 80.0, 5.0, 5000.0, 200.0, 0.02]
    
    # Group events by key
    key_events = {}
    for event in keystrokes:
        key = event["key"]
        if key not in key_events:
            key_events[key] = {"down": None, "up": None}
        key_events[key][event["type"]] = event["time"]
    
    # Calculate hold times (time between key down and key up)
    hold_times = []
    for key, events in key_events.items():
        if events["down"] is not None and events["up"] is not None:
            hold_time = events["up"] - events["down"]
            if hold_time > 0:
                hold_times.append(hold_time)
    
    # Calculate flight times (time between consecutive key presses)
    down_events = sorted(
        [e for e in keystrokes if e["type"] == "down"],
        key=lambda x: x["time"]
    )
    flight_times = []
    for i in range(1, len(down_events)):
        flight = down_events[i]["time"] - down_events[i-1]["time"]
        if flight > 0:
            flight_times.append(flight)
    
    def mean(lst):
        return sum(lst) / len(lst) if lst else 0.0
    
    def std(lst):
        if len(lst) < 2:
            return 0.0
        m = mean(lst)
        variance = sum((x - m) ** 2 for x in lst) / len(lst)
        return variance ** 0.5
    
    def median(lst):
        if not lst:
            return 0.0
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_lst[mid - 1] + sorted_lst[mid]) / 2
        return sorted_lst[mid]
    
    # Hold time features
    mean_hold = mean(hold_times) if hold_times else 100.0
    std_hold = std(hold_times) if hold_times else 10.0
    median_hold = median(hold_times) if hold_times else 100.0
    min_hold = min(hold_times) if hold_times else 50.0
    max_hold = max(hold_times) if hold_times else 150.0
    
    # Flight time features
    mean_flight = mean(flight_times) if flight_times else 80.0
    std_flight = std(flight_times) if flight_times else 15.0
    median_flight = median(flight_times) if flight_times else 80.0
    
    # Timing features
    total_time = max(e["time"] for e in keystrokes) - min(e["time"] for e in keystrokes)
    num_keys = len([e for e in keystrokes if e["type"] == "down"])
    typing_speed = (num_keys / (total_time / 1000)) if total_time > 0 else 5.0
    duration_per_char = total_time / num_keys if num_keys > 0 else 200.0
    
    # Backspace rate
    backspace_count = sum(1 for e in keystrokes if e["key"].lower() == "backspace" and e["type"] == "down")
    backspace_rate = backspace_count / num_keys if num_keys > 0 else 0.0
    
    return [
        mean_hold, std_hold, median_hold, min_hold, max_hold,
        mean_flight, std_flight, median_flight,
        typing_speed, total_time, duration_per_char, backspace_rate
    ]
