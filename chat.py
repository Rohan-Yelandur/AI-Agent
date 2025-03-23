from dotenv import load_dotenv
import streamlit as st
import os
from google import genai
import re
from PIL import Image
import io

# Load environment variables
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "context" not in st.session_state:
    st.session_state.context = ""

if "image" not in st.session_state:
    st.session_state.image = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []



# Query Gemini and get its response
def ask_gemini(question: str) -> str:
    message = []

    # Add context if available
    if st.session_state.context:
        message.append(f"Context: {st.session_state.context}")

    # Add the chat history to provide conversation context
    if st.session_state.chat_history:
        message.append(f"Conversation history: {st.session_state.chat_history}")

    # Add question to parts
    message.append(f"Current user question: {question}")

    # Handle image if uploaded
    if st.session_state.image is not None:
        image = Image.open(st.session_state.image)
        message.append(f"Image constraint: Response should NOT contain mention of image unless image is referenced by user.")
        
        # Generate content with text and image
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=[message, image]
        )
    else:
        # Generate content with text only
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=message
        )

    # Update chat history immediately
    st.session_state.history.append(f"User: {question}")
    st.session_state.history.append(f"Bot: {response.text}")
    
    update_chat_history()  # Update chat history for Streamlit

    return response.text



# Function to update chat_history
def update_chat_history():
    chat_history = []
    for i in range(0, len(st.session_state.history), 2):
        if i < len(st.session_state.history):
            user_msg = st.session_state.history[i].replace("User: ", "")
            chat_history.append({"role": "user", "parts": [{"text": user_msg}]})
            
            if i + 1 < len(st.session_state.history):
                bot_msg = st.session_state.history[i + 1].replace("Bot: ", "")
                chat_history.append({"role": "model", "parts": [{"text": bot_msg}]})
    
    st.session_state.chat_history = chat_history






# ------ Streamlit Frontend ----------------------------------------------

# Styles and displays conversation history in Streamlit
def display_conversation():
    conversation_placeholder = st.empty()
    with conversation_placeholder.container():
        for line in st.session_state.history:
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

# Handles user input and sends the question to the chatbot.
def handle_user_input():
    user_input = st.chat_input("Ask a question...")
    if user_input:
        response = ask_gemini(user_input)  # Get response from Gemini

# Run the Streamlit frontend
def run_app():
    st.title("RHN AI Bot")

    # Add this to your run_app function
    if st.sidebar.button("Clear Chat History"):
        st.session_state.history = []
        st.session_state.chat_history = []
        st.rerun()  # Refresh the page

    # Sidebar for context input
    st.sidebar.title("Chat Context")
    st.sidebar.write("Add context for the chatbot to consider in its responses.")
    st.session_state.context = st.sidebar.text_area("Context:", placeholder="Enter additional context here...")

    # Image uploader
    st.sidebar.title("Upload an Image")
    uploaded_image = st.sidebar.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        st.session_state.image = uploaded_image
        st.sidebar.image(uploaded_image, caption="Uploaded Image", use_container_width=True)

    # Handle user input 
    handle_user_input()
    display_conversation()


if __name__ == "__main__":
    run_app()