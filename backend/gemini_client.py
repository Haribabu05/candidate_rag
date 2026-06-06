import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API KEY FOUND:", api_key is not None)

import os

print(
    "CURRENT DIR:",
    os.getcwd()
)

if api_key:
    print("API KEY PREFIX:", api_key[:10])
    print("FLASK KEY:", os.getenv("GEMINI_API_KEY"))
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

def ask_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text