def detect_heart_rate_spike(recent_rates, current_rate):
    if len(recent_rates) < 5:
        return False

    avg = sum(recent_rates) / len(recent_rates)
    return current_rate > avg + 20