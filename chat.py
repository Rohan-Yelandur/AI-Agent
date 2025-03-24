from dotenv import load_dotenv
import streamlit as st
import os
from google import genai
from google.genai import types
from PIL import Image
import base64
import io

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

if "media_history" not in st.session_state:
    st.session_state.media_history = []


# Query Gemini and get its response
def ask_gemini(question: str) -> str:
    message = []

    # Add context if available
    if st.session_state.context:
        message.append(f"Context: {st.session_state.context}")

    # Add the chat history to provide conversation context
    if st.session_state.chat_history:
        message.append(f"Conversation history: {st.session_state.chat_history}")

    # Check if question explicitly asks for image generation
    is_image_request = any(phrase in question.lower() for phrase in 
                         ["create image", "generate image", "draw", "show me", "picture of", "image of", "generate", "create", "drawing"])

    # Add model specification for image generation requests
    model_name = "gemini-2.0-flash-exp-image-generation" if is_image_request else "gemini-2.0-flash" 

    # Add question to parts
    message.append(f"Current user question: {question}")
    message_str = " ".join(message)

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
                    model=model_name,
                    contents=[message_str, image]
                )
            else:
                # For non-image files
                file_bytes = file.getvalue()
                
                file_part = {
                    "inline_data": {
                        "mime_type": file.type,
                        "data": base64.b64encode(file_bytes).decode('utf-8')
                    }
                }
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=[message_str, file_part]
                )
        else:
            # If it's likely an image generation request, configure for images
            if is_image_request:
                
                # For image generation requests, add specific instructions
                image_prompt = message_str + " Please generate an image based on this request."
                
                response = client.models.generate_content(
                    model=model_name,  # Using model that supports image generation
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=['Text', 'Image']
                    )
                )
            else:
                # Normal text-only response
                response = client.models.generate_content(
                    model=model_name, 
                    contents=message_str
                )

        # Update chat history immediately
        st.session_state.history.append(f"User: {question}")
        
        # Check if response contains any images
        media_parts = []
        text_parts = []
        
        # Extract text and media from response using Google's recommended approach
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                text_parts.append(part.text)
            elif part.inline_data is not None:
                # Store binary image data directly
                media_parts.append({
                    'mime_type': part.inline_data.mime_type,
                    'data': part.inline_data.data
                })
        
        # Combine all text parts
        response_text = " ".join(text_parts)
        
        # Add to history
        st.session_state.history.append(f"Bot: {response_text}")
        
        # Store any media with message index
        if media_parts:
            msg_idx = len(st.session_state.history) - 1  # Index of the bot message
            st.session_state.media_history.append({
                'msg_idx': msg_idx,
                'media': media_parts
            })
        
        update_chat_history()  # Update chat history for Streamlit

        return response_text
    
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
        for i, line in enumerate(st.session_state.history):
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
                
                # Display any images associated with this message
                for media_item in st.session_state.media_history:
                    if media_item['msg_idx'] == i:
                        for media in media_item['media']:
                            try:
                                # Process the binary image data directly
                                image = Image.open(io.BytesIO(media['data']))
                                st.image(image, use_container_width=True)
                            except Exception as img_error:
                                st.error(f"Error displaying image: {img_error}")

# Handles user input and sends the question to the chatbot.
def handle_user_input():
    user_input = st.chat_input("Ask a question...")
    if user_input:
        response = ask_gemini(user_input)  # Get response from Gemini

# Run the Streamlit frontend
def run_app():
    st.title("TaskMaster")
    st.write("Features unlocked and at your fingertips")

    # Add this to your run_app function
    if st.sidebar.button("Clear Chat History"):
        st.session_state.history = []
        st.session_state.chat_history = []
        st.session_state.media_history = []  # Clear media history too
        st.session_state.uploaded_file = None
        st.rerun()  # Refresh the page

    # Sidebar for context input
    st.sidebar.title("Chat Context")
    st.sidebar.write("Add context for the chatbot to consider in its responses.")
    st.session_state.context = st.sidebar.text_area("Context:", placeholder="Enter additional context here...")

    # File uploader with supported file types information
    st.sidebar.title("Upload a File")
    st.sidebar.caption("Supported files: Images (JPEG, PNG, etc.), PDF, text files")
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