from openai import OpenAI

client = OpenAI()

def detect_mood(user_message):

    prompt = f"""
Classify the emotional tone of the message.

Possible moods:
sad
angry
lonely
stressed
anxious
neutral

Message:
{user_message}

Return only the mood word.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    mood = response.choices[0].message.content.strip().lower()

    return mood