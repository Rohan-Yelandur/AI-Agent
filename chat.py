from dotenv import load_dotenv
import streamlit as st
import os
from google import genai

# Load environment variables
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

if "history" not in st.session_state:
    st.session_state.history = []

# Send questions to Gemini and get its response
def ask_gemini(question: str) -> str:
    query = f"""
    This is context for your response: {st.session_state.context}.
    This is the conversation history: {st.session_state.history}. Remember what has been asked as context for responses, 
    but only refer to this history if the user requests it.
    This is the user's current question: {question}.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=query
    )

    # Update conversation history
    st.session_state.history.append(f"User: {question}")
    st.session_state.history.append(f"Bot: {response.text}")

    return response.text



# Streamlit app
st.title("Gemini Chatbot")

# Sidebar for context input
st.sidebar.title("Chat Context")
st.sidebar.write("Add context for the chatbot to consider in its responses.")
st.session_state.context = st.sidebar.text_area("Context:", placeholder="Enter additional context here...")

st.write("Ask questions to the Gemini chatbot!")
user_input = st.text_input("Your question:", "")

if st.button("Send"):
    if user_input:
        # Call the ask_gemini function with the user-provided context
        bot_response = ask_gemini(user_input)
        st.write(f"Bot: {bot_response}")

st.divider()

# Display conversation history
st.subheader("Conversation History")
for line in st.session_state.history:
    st.write(line)