from openai import OpenAI

client = OpenAI()

def generate_chat_response(user_message):

    system_prompt = """
You are a compassionate emotional support companion.

Your role:
- Listen carefully.
- Validate emotions.
- Respond gently and empathetically.
- Avoid sounding robotic.
- Keep responses short but meaningful.
- Ask thoughtful follow-up questions.
- Suggest simple coping strategies only when appropriate.
- Never give medical diagnosis.

You should feel like a calm, caring friend.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    return response.choices[0].message.content