from dotenv import load_dotenv
import streamlit as st
import os
from google import genai

# Load environment variables
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "context" not in st.session_state:
    st.session_state.context = ""

# Function to handle sending messages
def send_message():
    if st.session_state.widget_input:
        user_question = st.session_state.widget_input
        ask_gemini(user_question)
        st.session_state.widget_input = ""

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

# Run Streamlit frontend
def run_app():
    st.title("My Chatbot")

    # Sidebar for context input
    st.sidebar.title("Chat Context")
    st.sidebar.write("Add context for the chatbot to consider in its responses.")
    st.session_state.context = st.sidebar.text_area("Context:", placeholder="Enter additional context here...")

    conversation_placeholder = st.empty()

    # Display conversation history
    with conversation_placeholder.container():
        for line in st.session_state.history:
            # Styling for User input
            if line.startswith("User:"):
                label, message = line.split(":", 1)
                st.markdown(
                    f"""
                    <div style="background-color:#333333; padding:10px; border-radius:10px; margin-bottom:10px;">
                        <span style="color:#007BFF; font-weight:bold; font-size:30px;">{label}:</span> 
                        <span style="color:#FFFFFF;">{message}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            # Styling for Bot ouptut
            elif line.startswith("Bot:"):
                label, message = line.split(":", 1)
                st.markdown(
                    f"""
                    <div style="background-color:#333333; padding:10px; border-radius:10px; margin-bottom:10px;">
                        <span style="color:#388E3C; font-weight:bold; font-size:30px;">{label}:</span> 
                        <span style="color:#FFFFFF;">{message}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


    col1, col2 = st.columns([4, 1]) # Column widths

    with col1:
        st.text_input(
            "Your question:",
            placeholder="Ask a question...",
            key="widget_input", 
            label_visibility="collapsed",
            on_change=send_message
        )

    with col2:
        st.button("⬆️", on_click=send_message)


if __name__ == "__main__":
    run_app()