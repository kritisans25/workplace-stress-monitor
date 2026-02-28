import requests
from datetime import datetime, timedelta

def fetch_recent_heart_rate(access_token):
    end_time = int(datetime.utcnow().timestamp() * 1e9)
    start_time = int((datetime.utcnow() - timedelta(hours=2)).timestamp() * 1e9)

    body = {
        "aggregateBy": [{
            "dataTypeName": "com.google.heart_rate.bpm"
        }],
        "bucketByTime": {"durationMillis": 600000},
        "startTimeNanos": start_time,
        "endTimeNanos": end_time
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
        json=body,
        headers=headers
    )

    return response.json()