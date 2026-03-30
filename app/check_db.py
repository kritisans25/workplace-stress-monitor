
import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

# Check tables first
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cur.fetchall())

print("\nMood History Data:\n")

cur.execute("SELECT * FROM mood_history")
rows = cur.fetchall()

if not rows:
    print("No data found ❌")
else:
    for row in rows:
        print(row)

conn.close()