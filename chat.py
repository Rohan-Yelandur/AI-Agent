from dotenv import load_dotenv
import streamlit as st
import os
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


history = []
while True:
    user_input = input("Ask a question: ")
    if user_input == 'q':
        break
    
    query = query = f"""
                    This is the conversation history: {history}.
                    Only refer to this history if the user requests it.
                    This is the user's current question: {user_input}
                    """
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=query
    )
    history.append(user_input)

    print(response.text)