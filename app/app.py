from flask import Flask, render_template, request, redirect, url_for, session
import os, sys, sqlite3, joblib, requests
from datetime import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv

# ================= ENV =================
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# ================= PATH SETUP =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, "..")

sys.path.append(os.path.join(PROJECT_ROOT, "ml"))
sys.path.append(os.path.join(PROJECT_ROOT, "llm"))

# ================= IMPORTS =================
from explainability import compute_stress_dimensions, get_top_contributors
from trend_analysis import compute_stress_trend
from suggestions import generate_suggestions
from llm_explainer import generate_explanation
from auth_utils import hash_password, verify_password
from google_fit_reader import fetch_recent_heart_rate
from spike_detector import detect_heart_rate_spike

# ================= APP =================
app = Flask(__name__)
app.secret_key = "super-secret-key"

# ================= DATABASE =================
DB_PATH = os.path.join(PROJECT_ROOT, "database", "app.db")

def get_db():
    return sqlite3.connect(DB_PATH)

# ================= LOAD ML =================
model = joblib.load(os.path.join(PROJECT_ROOT, "ml", "model.pkl"))
scaler = joblib.load(os.path.join(PROJECT_ROOT, "ml", "scaler.pkl"))

# ================= ROUTES =================

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = hash_password(request.form["password"])

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="User already exists")
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and verify_password(user[1], password):
            session["user_id"] = user[0]
            return redirect(url_for("assessment"))
        else:
            return render_template(
                "login.html",
                error="Invalid credentials. If new, please register."
            )

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ---------- ASSESSMENT ----------
@app.route("/assessment")
def assessment():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

# ---------- PREDICT ----------
@app.route("/predict", methods=["POST"])
def predict():
    if "user_id" not in session:
        return redirect(url_for("login"))

    answers = [int(request.form[f"Q{i}"]) for i in range(1, 16)]

    X_scaled = scaler.transform([answers])
    stress_level = model.predict(X_scaled)[0]
    stress_score = sum(answers)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stress_history (user_id, timestamp, stress_score, stress_level)
        VALUES (?, ?, ?, ?)
    """, (session["user_id"], datetime.now().isoformat(), stress_score, stress_level))
    conn.commit()
    conn.close()

    dimensions = compute_stress_dimensions(answers)
    contributors = get_top_contributors(dimensions)
    stress_trend = compute_stress_trend(DB_PATH, session["user_id"])
    suggestions = generate_suggestions(stress_trend, contributors)
    explanation = generate_explanation(stress_level, contributors)

    return render_template(
        "result.html",
        stress_level=stress_level,
        stress_score=stress_score,
        stress_trend=stress_trend,
        dimensions=dimensions,
        explanation=explanation,
        suggestions=suggestions
    )

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # ---- Stress History ----
    cursor.execute("""
        SELECT timestamp, stress_score, stress_level
        FROM stress_history
        WHERE user_id=?
        ORDER BY timestamp ASC
    """, (session["user_id"],))

    stress_rows = cursor.fetchall()

    history = []
    timestamps = []
    scores = []

    for ts, score, level in stress_rows:
        dt = datetime.fromisoformat(ts)
        formatted = dt.strftime("%d %b %Y, %I:%M %p")
        history.append((formatted, score, level))
        timestamps.append(formatted)
        scores.append(score)

    # ---- Heart Rate ----
    cursor.execute("""
        SELECT timestamp, heart_rate
        FROM heart_rate_data
        WHERE user_id=?
        ORDER BY timestamp ASC
    """, (session["user_id"],))

    hr_rows = cursor.fetchall()

    hr_timestamps = []
    heart_rates = []

    for ts, hr in hr_rows:
        dt = datetime.fromisoformat(ts)
        formatted = dt.strftime("%d %b %Y, %I:%M %p")
        hr_timestamps.append(formatted)
        heart_rates.append(hr)

    # ---- Spike Detection ----
    if len(heart_rates) >= 6:
        recent = heart_rates[-10:]
        current_hr = heart_rates[-1]
        if detect_heart_rate_spike(recent[:-1], current_hr):
            session["alert"] = "⚠️ Sudden heart rate spike detected"

    stress_trend = compute_stress_trend(DB_PATH, session["user_id"])
    conn.close()

    return render_template(
        "dashboard.html",
        history=history,
        stress_trend=stress_trend,
        timestamps=timestamps,
        scores=scores,
        hr_timestamps=hr_timestamps,
        heart_rates=heart_rates
    )

# ================= GOOGLE FIT =================

@app.route("/google/connect")
def google_connect():
    if "user_id" not in session:
        return redirect(url_for("login"))

    scopes = [
        "https://www.googleapis.com/auth/fitness.heart_rate.read",
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.sleep.read"
    ]

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent"
    }

    return redirect(
        "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    )

@app.route("/google/callback")
def google_callback():
    code = request.args.get("code")

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI
        }
    ).json()

    access_token = token_response.get("access_token")
    session["google_access_token"] = access_token

    data = fetch_recent_heart_rate(access_token)

    conn = get_db()
    cursor = conn.cursor()

    for bucket in data.get("bucket", []):
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                if "value" in point:
                    bpm = int(point["value"][0]["fpVal"])
                    ts_nanos = int(point["endTimeNanos"])
                    ts_seconds = ts_nanos / 1e9
                    dt = datetime.fromtimestamp(ts_seconds)

                    cursor.execute("""
                        INSERT INTO heart_rate_data (user_id, timestamp, heart_rate)
                        VALUES (?, ?, ?)
                    """, (session["user_id"], dt.isoformat(), bpm))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=False)