import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# ---------------- PATH SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "stress_dataset.csv")

# ---------------- LOAD DATA ----------------
df = pd.read_csv(DATA_PATH)

X = df.iloc[:, :15]          # Q1–Q15
y = df["stress_label"]       # Low / Medium / High

# ---------------- SCALE FEATURES ----------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ---------------- SPLIT DATA ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# ---------------- TRAIN MODEL ----------------
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# ---------------- PREDICT ----------------
y_pred = model.predict(X_test)

# ---------------- EVALUATION ----------------
print("\n===== MODEL USED =====")
print(type(model).__name__)

print("\n===== ACCURACY =====")
print("Accuracy:", accuracy_score(y_test, y_pred))

print("\n===== PRECISION =====")
print("Precision (macro):", precision_score(y_test, y_pred, average="macro"))

print("\n===== RECALL =====")
print("Recall (macro):", recall_score(y_test, y_pred, average="macro"))

print("\n===== F1 SCORE =====")
print("F1-score (macro):", f1_score(y_test, y_pred, average="macro"))

print("\n===== CLASSIFICATION REPORT =====")
print(classification_report(y_test, y_pred))

print("\n===== CONFUSION MATRIX =====")
print(confusion_matrix(y_test, y_pred))

# ---------------- SAVE MODEL ----------------
joblib.dump(model, os.path.join(BASE_DIR, "model.pkl"))
joblib.dump(scaler, os.path.join(BASE_DIR, "scaler.pkl"))

print("\nModel and scaler saved successfully")
