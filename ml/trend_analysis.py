import sqlite3
import numpy as np

def compute_stress_trend(db_path, user_id, window=5):
    """
    Computes stress trend for a specific user using SQLite data.
    """

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT stress_score
        FROM stress_history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, window)
    )

    rows = cursor.fetchall()
    conn.close()

    # Not enough data
    if len(rows) < 2:
        return "Not enough data"

    # Convert to list (latest last for trend direction)
    scores = [r[0] for r in reversed(rows)]

    diff = scores[-1] - scores[0]

    if diff > 2:
        return "Increasing"
    elif diff < -2:
        return "Decreasing"
    else:
        return "Stable"