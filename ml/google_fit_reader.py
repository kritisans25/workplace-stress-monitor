import requests
import time

NOISE_HEART_SOURCE = "raw:com.google.heart_rate.bpm:com.noisefit:noise_activity - Heart data"

def fetch_recent_heart_rate(access_token):

    end_time = int(time.time() * 1000000000)
    start_time = int(end_time - (3 * 86400 * 1000000000))  # last 3 days

    dataset_id = f"{start_time}-{end_time}"

    url = f"https://www.googleapis.com/fitness/v1/users/me/dataSources/{NOISE_HEART_SOURCE}/datasets/{dataset_id}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    data = response.json()

    print("GOOGLE FIT RAW HEART DATA:")
    print(data)

    return data