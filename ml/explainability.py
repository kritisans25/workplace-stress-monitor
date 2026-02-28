def compute_stress_dimensions(answers):
    """
    answers: list of 15 integers (Q1–Q15)
    returns: dictionary of dimension scores
    """

    dimensions = {
        "Workload Stress": sum(answers[0:3]),        # Q1–Q3
        "Physical Stress": sum(answers[3:6]),        # Q4–Q6
        "Cognitive Stress": sum(answers[6:9]),       # Q7–Q9
        "Emotional Stress": sum(answers[9:12]),      # Q10–Q12
        "Work–Life Balance": sum(answers[12:15])     # Q13–Q15
    }

    return dimensions


def get_top_contributors(dimensions, threshold=5):
    """
    Filters dimensions with meaningful contribution
    """

    important = {
        k: v for k, v in dimensions.items()
        if v >= threshold
    }

    return important
if __name__ == "__main__":
    sample_answers = [3,3,4,1,0,1,2,3,3,1,2,2,0,1,1]
    dims = compute_stress_dimensions(sample_answers)
    print(dims)
    print(get_top_contributors(dims))
