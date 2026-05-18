from openai import OpenAI  
from rag.retriever import retrieve_context

client = OpenAI()

# Base system prompt
system_prompt = """
You are a compassionate emotional support companion.

Talk like a calm, emotionally intelligent human being having a genuine conversation.

Your responses should feel:
- warm
- emotionally aware
- natural
- conversational
- supportive

IMPORTANT:
- Validate emotions naturally.
- Keep responses personal and human.
- Avoid sounding like a therapist, coach, or article.
- Avoid generic self-help language.
- Avoid overexplaining emotions.
- Avoid formal advice-heavy responses.
- Do not use bullet points.
- Do not sound robotic or scripted.
- Keep responses emotionally grounded and gentle.

Use the retrieved wellness context naturally when relevant,
but blend it subtly into the conversation.

Do not directly repeat retrieved context.

Focus more on:
- emotional understanding
- calm conversation
- thoughtful reflection

Less on:
- advice
- instruction
- problem-solving

Never provide medical diagnosis.
"""


def generate_chat_response(messages, mood=None, stress_level=None):

    # Latest user message
    latest_user_message = messages[-1]["content"]

    # Build retrieval query
    retrieval_query = f"""
    User Message: {latest_user_message}

    Detected Mood: {mood}

    Stress Level: {stress_level}
    """

    # Retrieve contextual wellness information
    retrieved_context = retrieve_context(retrieval_query, top_k=2)

    # Debugging (optional)
    print("\n===== RAG DEBUG =====")
    print("Retrieval Query:")
    print(retrieval_query)

    print("\nRetrieved Context:")
    print(retrieved_context)
    print("=====================\n")

    # Enhanced prompt with RAG context
    enhanced_system_prompt = f"""
    {system_prompt}

    Detected Mood: {mood}

    Stress Level: {stress_level}

    IMPORTANT WELLNESS CONTEXT:
    {retrieved_context}

    Use this context naturally when relevant.
    Do not directly repeat it.
    Blend it into the conversation smoothly.
    """

    # Generate chatbot response
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": enhanced_system_prompt
            },
            {
                "role": "system",
                "content": f"""
                Use the following emotional wellness knowledge
                naturally within the conversation when appropriate:

                {retrieved_context}
                """
            }
        ] + messages,
        temperature=0.8
    )

    return response.choices[0].message.content