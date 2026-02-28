import random
import pandas as pd
import os

TARGET_COUNTS = {
    "Low": 420,
    "Medium": 560,
    "High": 420
}

data = {"Low": [], "Medium": [], "High": []}

def assign_label_with_overlap(score):
    """
    Assign label with overlapping boundaries (realistic ambiguity)
    """
    # Clear regions
    if score <= 18:
        return "Low"
    if 23 <= score <= 38:
        return "Medium"
    if score >= 43:
        return "High"

    # Overlap regions
    if 19 <= score <= 22:
        return random.choices(
            ["Low", "Medium"],
            weights=[0.6, 0.4]
        )[0]

    if 39 <= score <= 42:
        return random.choices(
            ["Medium", "High"],
            weights=[0.6, 0.4]
        )[0]

    return "Medium"


while (
    len(data["Low"]) < TARGET_COUNTS["Low"] or
    len(data["Medium"]) < TARGET_COUNTS["Medium"] or
    len(data["High"]) < TARGET_COUNTS["High"]
):
    answers = [random.randint(0, 4) for _ in range(15)]
    stress_score = sum(answers)
    label = assign_label_with_overlap(stress_score)

    if len(data[label]) < TARGET_COUNTS[label]:
        data[label].append(answers + [stress_score, label])

# Combine all data
final_data = data["Low"] + data["Medium"] + data["High"]

columns = [f"Q{i}" for i in range(1, 16)] + ["stress_score", "stress_label"]
df = pd.DataFrame(final_data, columns=columns)

# Save dataset safely
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "stress_dataset.csv")
df.to_csv(DATA_PATH, index=False)

print("Realistic balanced dataset generated")
print(df["stress_label"].value_counts())