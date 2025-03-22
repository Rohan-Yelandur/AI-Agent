from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the API key globally
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the GenerativeModel without api_key parameter
client = genai.GenerativeModel(model_name="gemini-2.0-flash")

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
    # Convert history to proper format
    chat_history = []
    
    # Iterate through User and Bot messages
    for i in range(0, len(st.session_state.history), 2):
        if i < len(st.session_state.history):
            user_msg = st.session_state.history[i].replace("User: ", "") # Get rid of the "User" label
            chat_history.append({"role": "user", "parts": [{"text": user_msg}]})
            
            if i+1 < len(st.session_state.history):
                bot_msg = st.session_state.history[i+1].replace("Bot: ", "") # Get rid of the "Bot" label
                chat_history.append({"role": "model", "parts": [{"text": bot_msg}]})
    
    # Add system prompt with context
    system_instruction = f"Consider this context information: {st.session_state.context}"
    
    # Start conversation with system message if we have context
    if st.session_state.context:
        messages = [{"role": "user", "parts": [{"text": system_instruction}]}, 
                   {"role": "model", "parts": [{"text": "I'll keep that context in mind."}]}]
        messages.extend(chat_history)
    else:
        messages = chat_history
    
    # Add current question
    messages.append({"role": "user", "parts": [{"text": question}]})
    
    # Send the request properly formatted
    response = client.generate_content(messages)
    
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