from openai import OpenAI

client = OpenAI()

def generate_explanation(stress_level, contributors):
    """
    stress_level: string (Low / Medium / High)
    contributors: dict of stress dimensions
    """

    if stress_level == "Low":
        tone = "reassuring and positive"
    elif stress_level == "Medium":
        tone = "cautious and supportive"
    else:
        tone = "empathetic and encouraging"

    factors_text = ", ".join(contributors.keys()) if contributors else "overall balance"

    prompt = f"""
    The user has a {stress_level} level of workplace stress.

    Main contributing factors: {factors_text}.

    Explain this in a {tone} tone.
    Do not use medical advice.
    Keep the explanation simple and human-friendly.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
