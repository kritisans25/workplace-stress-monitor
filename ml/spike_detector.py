def detect_heart_rate_spike(previous, current):

    if not previous:
        return False

    avg = sum(previous) / len(previous)

    # Condition 1: Sudden jump from last reading
    sudden_jump = current - previous[-1] >= 20

    # Condition 2: High abnormal value
    abnormal_level = current >= 100

    # Condition 3: Significant increase from average
    above_average = current >= avg + 15

    return sudden_jump or abnormal_level or above_average