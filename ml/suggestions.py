def generate_suggestions(stress_trend, contributors):
    """
    stress_trend: Increasing / Decreasing / Stable
    contributors: dict of stress dimensions
    returns: list of suggestions (strings)
    """

    suggestions = []

    # ---- TREND-BASED SUGGESTIONS ----
    if stress_trend == "Increasing":
        suggestions.append(
            "Your stress levels appear to be increasing. It may help to pause and review your daily workload and recovery habits."
        )

    elif stress_trend == "Decreasing":
        suggestions.append(
            "Your stress levels are decreasing. This suggests that your current coping strategies may be working well."
        )

    elif stress_trend == "Stable":
        suggestions.append(
            "Your stress levels appear stable. Maintaining consistent routines can help preserve balance."
        )

    # ---- DIMENSION-BASED SUGGESTIONS ----
    for dimension in contributors.keys():

        if dimension == "Workload Stress":
            suggestions.append(
                "Consider breaking tasks into smaller steps and setting realistic deadlines to manage workload pressure."
            )

        elif dimension == "Physical Stress":
            suggestions.append(
                "Light physical activity, regular breaks, and proper rest may help reduce physical strain."
            )

        elif dimension == "Cognitive Stress":
            suggestions.append(
                "Taking short mental breaks and reducing multitasking may help ease mental fatigue."
            )

        elif dimension == "Emotional Stress":
            suggestions.append(
                "Talking things through with someone you trust or practicing relaxation techniques may help manage emotional stress."
            )

        elif dimension == "Work–Life Balance":
            suggestions.append(
                "Setting clearer boundaries between work and personal time may help improve overall balance."
            )

    # Fallback if no contributors
    if not contributors:
        suggestions.append(
            "You appear to have a balanced stress profile. Continuing healthy routines can help maintain this state."
        )

    return suggestions
