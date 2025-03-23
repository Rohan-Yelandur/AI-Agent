from dotenv import load_dotenv
import streamlit as st
import os
from google import genai
from PIL import Image
import base64

# Load environment variables
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Supported file types
SUPPORTED_MIME_TYPES = [
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    # Text
    "text/plain",
    "text/csv",
    "text/html",
    "text/javascript",
    "application/json",
    # PDFs
    "application/pdf",
]

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "context" not in st.session_state:
    st.session_state.context = ""

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []



# Query Gemini and get its response
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
    message_str = " ".join(message)
    
    constraint = " File constraint: Response should NOT mention the file unless referenced by user."

    try:
        # Handle file if uploaded
        if st.session_state.uploaded_file is not None:
            file = st.session_state.uploaded_file
            
            # Check if file type is supported
            if file.type not in SUPPORTED_MIME_TYPES:
                return f"Sorry, the file type {file.type} is not supported by Gemini. Supported types include images, PDFs, and text files."
            
            # Process based on file type
            if file.type.startswith('image/'):
                # Process as image
                image = Image.open(file)
                
                # Generate content with text and image
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[message_str + constraint, image]
                )
            else:
                # For non-image files
                file_bytes = file.getvalue()
                
                # Use the Part creation properly for files
                file_part = {
                    "inline_data": {
                        "mime_type": file.type,
                        "data": base64.b64encode(file_bytes).decode('utf-8')
                    }
                }
                
                # Generate content with text and file
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[message_str + constraint, file_part]
                )
        else:
            # Generate content with text only
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=message_str
            )

        # Update chat history immediately
        st.session_state.history.append(f"User: {question}")
        st.session_state.history.append(f"Bot: {response.text}")
        
        update_chat_history()  # Update chat history for Streamlit

        return response.text
    
    except Exception as e:
        error_message = f"Error: {str(e)}"
        st.error(error_message)
        return f"Sorry, I encountered an error processing your request: {str(e)}"





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






# ------ Streamlit Frontend ----------------------------------------------------------------

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
        st.session_state.uploaded_file = None
        st.rerun()  # Refresh the page

    # Sidebar for context input
    st.sidebar.title("Chat Context")
    st.sidebar.write("Add context for the chatbot to consider in its responses.")
    st.session_state.context = st.sidebar.text_area("Context:", placeholder="Enter additional context here...")

    # File uploader with supported file types information
    st.sidebar.title("Upload a File")
    st.sidebar.caption("Supported files: Images (JPEG, PNG, etc.), PDF, and text files")
    uploaded_file = st.sidebar.file_uploader("Choose a file")
    
    if uploaded_file is not None:
        # Check if file type is supported
        if uploaded_file.type not in SUPPORTED_MIME_TYPES:
            st.sidebar.error(f"File type {uploaded_file.type} is not supported. Please upload a supported file type.")
        else:
            st.session_state.uploaded_file = uploaded_file
            
            # Only display preview for image files
            if uploaded_file.type.startswith('image/'):
                st.sidebar.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
            else:
                st.sidebar.success(f"File uploaded: {uploaded_file.name}")

    # Handle user input 
    handle_user_input()
    display_conversation()  

if __name__ == "__main__":
    run_app()