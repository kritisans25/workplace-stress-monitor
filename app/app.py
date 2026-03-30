from flask import Flask, render_template, request, redirect, url_for, session
import os, sys, sqlite3, joblib, requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import jsonify


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
from email_alert import send_heart_rate_alert
from chatbot import generate_chat_response
from mood_detector import detect_mood

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
def get_mental_state(stress_score, mood, heart_rate):

    if stress_score >= 45 and mood in ["sad", "angry", "lonely"] and heart_rate > 100:
        return "Critical 🚨"

    elif stress_score >= 40 or mood in ["stressed", "anxious"]:
        return "High Stress ⚠️"

    elif stress_score >= 25:
        return "Mild Stress ⚡"

    else:
        return "Stable ✅"

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

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # ---------- Stress History ----------
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

    # ---------- Heart Rate ----------
    cursor.execute("""
        SELECT timestamp, heart_rate
        FROM heart_rate_data
        WHERE user_id=?
        ORDER BY timestamp ASC
    """, (session["user_id"],))

    hr_rows = cursor.fetchall()

    hr_timestamps = []
    heart_rates = []

    import pytz
    utc = pytz.utc
    ist = pytz.timezone('Asia/Kolkata')

    now = datetime.now(ist)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    for ts, hr in hr_rows:
        dt_naive = datetime.fromisoformat(ts)
        try:
            dt_utc = utc.localize(dt_naive)
        except ValueError:
            dt_utc = dt_naive.astimezone(utc)
        dt = dt_utc.astimezone(ist)
        
        if start_of_day <= dt < end_of_day:
            formatted = dt.strftime("%I:%M %p")
            hr_timestamps.append(formatted)
            heart_rates.append(hr)

    if not heart_rates:
        recent = hr_rows[-10:]

        for ts, hr in recent:
            dt_naive = datetime.fromisoformat(ts)
            try:
                dt_utc = utc.localize(dt_naive)
            except ValueError:
                dt_utc = dt_naive.astimezone(utc)
            dt = dt_utc.astimezone(ist)
            
            formatted = dt.strftime("%d %b %I:%M %p")
            hr_timestamps.append(formatted)
            heart_rates.append(hr)

    # Limit to last 20 readings
    hr_timestamps = hr_timestamps[-20:]
    heart_rates = heart_rates[-20:]

    # Compute latest heart rate
    latest_hr = heart_rates[-1] if heart_rates else None

    # Get user email
    cursor.execute("SELECT email FROM users WHERE id=?", (session["user_id"],))
    user_email = cursor.fetchone()[0]

    # ---------- Spike Detection ----------
    if heart_rates and len(heart_rates) >= 6:

        recent = heart_rates[-6:]
        current_hr = recent[-1]

        if detect_heart_rate_spike(recent[:-1], current_hr):

            session["alert"] = "⚠️ Sudden heart rate spike detected"
            send_heart_rate_alert(user_email, current_hr)

    stress_trend = compute_stress_trend(DB_PATH, session["user_id"])

    # ---------- Mental State & Insights ----------
    latest_stress = scores[-1] if scores else 0
    hr_for_calc = latest_hr if latest_hr is not None else 0
    
    cursor.execute("""
        SELECT mood FROM mood_history
        WHERE user_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (session["user_id"],))
    last_mood_row = cursor.fetchone()
    current_mood = last_mood_row[0] if last_mood_row else "neutral"
    
    mental_state = get_mental_state(latest_stress, current_mood, hr_for_calc)
    is_critical = "Critical" in mental_state
    
    insights = []
    if latest_stress >= 40:
        insights.append("Your recent stress levels are quite high. Taking short breaks might help.")
    if stress_trend == "Increasing":
        insights.append("Your stress levels are showing an upward trend lately.")
    if current_mood in ["sad", "angry", "lonely"]:
        insights.append("Your recent chats suggest a negative mood. Don't hesitate to seek support.")
    if current_mood in ["stressed", "anxious"]:
        insights.append("You've expressed feeling stressed/anxious recently. Try to practice breathing exercises.")
    if len(heart_rates) >= 2 and sum(heart_rates[-3:])/len(heart_rates[-3:]) > 90:
        insights.append("Your heart rate has been on the higher side today.")
    if heart_rates and heart_rates[-1] > 110:
        insights.append("Your heart rate is elevated. Try relaxation techniques.")

    conn.close()

    alert = session.pop("alert", None)

    return render_template(
        "dashboard.html",
        history=history,
        stress_trend=stress_trend,
        timestamps=timestamps,
        scores=scores,
        hr_timestamps=hr_timestamps,
        heart_rates=heart_rates,
        latest_hr=latest_hr,
        alert=alert,
        mental_state=mental_state,
        is_critical=is_critical,
        insights=insights
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

    if not access_token:
        return "Google authentication failed."

    session["google_access_token"] = access_token

    # ---- Fetch Heart Rate Data ----
    data = fetch_recent_heart_rate(access_token)

    conn = get_db()
    cursor = conn.cursor()

    points = data.get("point", [])

    inserted_count = 0

    for point in points:
        bpm = int(point["value"][0]["fpVal"])

        ts_nanos = int(point["endTimeNanos"])
        ts_seconds = ts_nanos / 1e9
        dt = datetime.fromtimestamp(ts_seconds)

        cursor.execute("""
            INSERT INTO heart_rate_data (user_id, timestamp, heart_rate)
            VALUES (?, ?, ?)
        """, (session["user_id"], dt.isoformat(), bpm))

        inserted_count += 1

    conn.commit()
    conn.close()

    print(f"Inserted {inserted_count} heart rate records")

    return redirect(url_for("dashboard"))
# Chatbot
@app.route("/chat", methods=["POST"])
def chat():

    data = request.json
    user_message = data.get("message")

    mood = detect_mood(user_message)
    positive_keywords = ["energetic", "excited", "motivated", "great", "good", "happy", "awesome"]
    if any(word in user_message.lower() for word in positive_keywords):
        mood = "happy"

    # ✅ NEW: Get user_id from session
    user_id = session.get("user_id")

    # ✅ NEW: Save mood (only if user is logged in)
    if user_id:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Optional: avoid duplicate consecutive moods
        cur.execute("""
            SELECT mood FROM mood_history
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (user_id,))

        last = cur.fetchone()

        if not last or last[0] != mood:
            cur.execute("""
                INSERT INTO mood_history (user_id, mood)
                VALUES (?, ?)
            """, (user_id, mood))

        conn.commit()
        conn.close()

    # ================= CHAT HISTORY =================

    if "chat_history" not in session:
        session["chat_history"] = []

    chat_history = session["chat_history"]

    chat_history.append({
        "role": "user",
        "content": f"(User mood: {mood}) {user_message}"
    })

    chat_history = chat_history[-10:]

    response = generate_chat_response(chat_history)

    chat_history.append({
        "role": "assistant",
        "content": response
    })

    session["chat_history"] = chat_history

    mood_score = {
        "happy": 5,
        "neutral": 3,
        "stressed": 2,
        "anxious": 2,
        "sad": 1,
        "angry": 1,
        "lonely": 1
    }.get(mood, 3)
    return {
        "response": response,
        "mood": mood,
        "mood_score": mood_score
    }
#MOOD DATA
@app.route("/mood_data")
def mood_data():
    user_id = session['user_id']

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT mood, timestamp 
        FROM mood_history 
        WHERE user_id = ?
        ORDER BY timestamp ASC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    # Convert mood to score
    mood_map = {
        "happy": 5,
        "neutral": 3,
        "stressed": 2,
        "anxious": 2,
        "sad": 1,
        "angry": 1,
        "lonely": 1
    }

    moods = []
    scores = []
    timestamps = []

    for mood, ts in rows:
        moods.append(mood)
        scores.append(mood_map.get(mood, 3))
        timestamps.append(ts)

    # Trend logic
    if len(scores) >= 3:
        recent_avg = sum(scores[-3:]) / 3
        overall_avg = sum(scores) / len(scores)
        if recent_avg > overall_avg:
            trend = "Improving 📈"
        elif recent_avg < overall_avg:
            trend = "Declining 📉"
        else:
            trend = "Stable ➖"
    else:
        trend = "Not enough data"

    avg = round(sum(scores)/len(scores), 2) if scores else 0

    return jsonify({
        "moods": moods,
        "scores": scores,
        "timestamps": timestamps,
        "trend": trend,
        "average": avg
    })
# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=False)