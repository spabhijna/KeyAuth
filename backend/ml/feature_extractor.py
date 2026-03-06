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
    
    Output format (feature vector):
    [avg_hold_time, hold_time_std, avg_flight_time, flight_time_std, typing_speed, backspace_rate]
    """
    if not keystrokes or len(keystrokes) < 2:
        return [100.0, 10.0, 80.0, 15.0, 5.0, 0.02]
    
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
    
    avg_hold_time = mean(hold_times) if hold_times else 100.0
    hold_time_std = std(hold_times) if hold_times else 10.0
    avg_flight_time = mean(flight_times) if flight_times else 80.0
    flight_time_std = std(flight_times) if flight_times else 15.0
    
    # Typing speed (keys per second)
    if keystrokes:
        total_time = max(e["time"] for e in keystrokes) - min(e["time"] for e in keystrokes)
        num_keys = len([e for e in keystrokes if e["type"] == "down"])
        typing_speed = (num_keys / (total_time / 1000)) if total_time > 0 else 5.0
    else:
        typing_speed = 5.0
    
    # Backspace rate
    backspace_count = sum(1 for e in keystrokes if e["key"].lower() == "backspace" and e["type"] == "down")
    total_keys = len([e for e in keystrokes if e["type"] == "down"])
    backspace_rate = backspace_count / total_keys if total_keys > 0 else 0.0
    
    return [avg_hold_time, hold_time_std, avg_flight_time, flight_time_std, typing_speed, backspace_rate]
