import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ================= USERS =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ================= STRESS HISTORY =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS stress_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    timestamp TEXT,
    stress_score INTEGER,
    stress_level TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# ================= GOOGLE FIT HEART RATE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS heart_rate_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    timestamp TEXT,
    heart_rate INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cursor.execute("""
SELECT bpm, timestamp
FROM heart_rate_data
WHERE user_id = ?
ORDER BY timestamp
""", (user_id,))

rows = cursor.fetchall()

conn.commit()
conn.close()

print("Database initialized successfully")