import os
from dotenv import load_dotenv
from groq import Groq

env_path = os.path.join(os.path.dirname(__file__), ".env")

print("ENV PATH:", env_path)
print("ENV EXISTS:", os.path.exists(env_path))

load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")

print("API KEY FOUND:", api_key is not None)

client = Groq(api_key=api_key)


def ask_gemini(prompt):

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1,

        max_tokens=600
    )

    return response.choices[0].message.content