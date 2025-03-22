from dotenv import load_dotenv
import streamlit as st
import os
import json
import google.generativeai as genai
import re

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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "json_summaries" not in st.session_state:
    st.session_state.json_summaries = []



# Query Gemini and get its natural language and JSON responses
def ask_gemini(question: str) -> tuple:
    # Add system prompt with context
    system_instruction = f"Consider this context information: {st.session_state.context}"
    
    # Start conversation with system message if we have context
    if st.session_state.context:
        messages = [{"role": "user", "parts": [{"text": system_instruction}]}, 
                    {"role": "model", "parts": [{"text": "I'll keep that context in mind."}]}]
        messages.extend(st.session_state.chat_history)
    else:
        messages = st.session_state.chat_history
    
    need_structured_output = should_use_structured_output(question)
    if need_structured_output:
        # For JSON output, request structured data only
        final_question = f"""Original question: {question}.
                        Please respond with ONLY a valid JSON object containing key information.
                        No introduction text, no explanation, just pure JSON.
                        
                        The JSON should be properly formatted with double quotes around keys and string values.
                        Example format:
                        {{
                            "key_points": [
                                "First important point",
                                "Second important point"
                            ],
                            "summary": "Brief summary text"
                        }}
                        """
    else:
        # For natural language output, just ask the question directly
        final_question = question

    # Add current question
    messages.append({"role": "user", "parts": [{"text": final_question}]})
    
    # Send query to Gemini
    response = client.generate_content(messages)

    # Parse the response for structured output if necessary
    if need_structured_output:
        try:
            # Try to parse the response as pure JSON
            json_summary = json.loads(response.text)
            natural_response = "Structured data response (see summary in sidebar)"
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from text
            natural_response, json_summary = extract_json_from_text(response.text)
            
            # Final safety check - ensure no markdown or HTML remains
            natural_response = re.sub(r'```(?:json)?|```', '', natural_response)
            natural_response = re.sub(r'</?div>|</?span.*?>|</?p>', '', natural_response)
            
            # If the cleaned response is too short, use the default message
            if len(natural_response.strip()) < 5:
                natural_response = "Structured data response (see summary in sidebar)"
    else:
        natural_response = response.text
        json_summary = {}

    # Update conversation history - only include the natural language part
    st.session_state.history.append(f"User: {question}")
    st.session_state.history.append(f"Bot: {natural_response}")
    
    # Update chat_history
    update_chat_history()
    
    return natural_response, json_summary

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

# Is structured output needed in Gemini's response?
def should_use_structured_output(question: str):
    return True

# filepath: c:\APP\Github Workspace\AI-Agent\chat.py
def extract_json_from_text(text):
    """
    Attempts to extract JSON from text when the model doesn't return pure JSON.
    """
    # Initialize with default values
    natural_text = text
    json_data = {"error": "No valid JSON found"}
    
    # First, clean up any markdown code block markers
    natural_text = re.sub(r'```(?:json)?|```', '', natural_text)
    
    # Look for JSON-like pattern
    json_pattern = r'\{[\s\S]*\}'  # Match anything between { and } including newlines
    matches = re.search(json_pattern, text)
    
    if matches:
        json_candidate = matches.group(0)
        try:
            # Try to parse the JSON
            json_data = json.loads(json_candidate)
            # If successful, remove the JSON part from the natural text
            natural_text = text.replace(json_candidate, "").strip()
            
            # Clean any leftover HTML tags and markdown
            natural_text = re.sub(r'</?div>|</?span.*?>|</?p>|</?code>|</?pre>', '', natural_text)
            natural_text = re.sub(r'```(?:json)?|```', '', natural_text)
            natural_text = re.sub(r'^\s*[\[\{\]\}]\s*$', '', natural_text, flags=re.MULTILINE)
            
            # If we're left with only backticks or empty text, replace with standard message
            if re.match(r'^(\s|`|\\)*$', natural_text):
                natural_text = "Structured data response (see summary in sidebar)"
                
            return natural_text, json_data
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            try:
                # Fix quotes and other common issues
                fixed_json = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_candidate)
                fixed_json = fixed_json.replace("'", '"')
                json_data = json.loads(fixed_json)
                natural_text = text.replace(json_candidate, "").strip()
                
                # Clean any leftover HTML tags and markdown
                natural_text = re.sub(r'</?div>|</?span.*?>|</?p>|</?code>|</?pre>', '', natural_text)
                natural_text = re.sub(r'```(?:json)?|```', '', natural_text)
                natural_text = re.sub(r'^\s*[\[\{\]\}]\s*$', '', natural_text, flags=re.MULTILINE)
                
                # If we're left with only backticks or empty text, replace with standard message
                if re.match(r'^(\s|`|\\)*$', natural_text):
                    natural_text = "Structured data response (see summary in sidebar)"
                    
                return natural_text, json_data
            except:
                # If all parsing fails, return a clean default message
                return "Structured data response (see summary in sidebar)", {"error": "Invalid JSON format", "raw_text": json_candidate[:100] + "..."}
    
    # Clean the text even if no JSON is found
    natural_text = re.sub(r'</?div>|</?span.*?>|</?p>|</?code>|</?pre>', '', natural_text)
    natural_text = re.sub(r'```(?:json)?|```', '', natural_text)
    
    # If after cleanup, we're left with something very short or empty, use default message
    if len(natural_text.strip()) < 3:
        natural_text = "Structured data response (see summary in sidebar)"
        
    return natural_text, json_data




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

# Function to handle sending messages
def send_message():
    if st.session_state.widget_input:
        user_question = st.session_state.widget_input
        # Get both the natural language response and JSON summary
        natural_language, json_summary = ask_gemini(user_question)
        
        # Store the JSON summary in session state if needed for later use
        if json_summary:
            st.session_state.json_summaries.append(json_summary)
        
        # Clear the input field
        st.session_state.widget_input = ""

# Handles user input and sends the question to the chatbot.
def handle_user_input():
    col1, col2 = st.columns([4, 1])  # Column widths
    with col1:
        st.text_input(
            "Your question:",
            placeholder="Ask a question...",
            key="widget_input",
            label_visibility="collapsed",
            on_change=send_message,
        )
    with col2:
        st.button("⬆️", on_click=send_message)

# Run the Streamlit frontend
def run_app():
    st.title("Gemini Chatbot")

    # Add this to your run_app function
    if st.sidebar.button("Clear Chat History"):
        st.session_state.history = []
        st.session_state.chat_history = []
        st.session_state.json_summaries = []
        st.rerun()  # Refresh the page

    # Sidebar for context input
    st.sidebar.title("Chat Context")
    st.sidebar.write("Add context for the chatbot to consider in its responses.")
    st.session_state.context = st.sidebar.text_area("Context:", placeholder="Enter additional context here...")
    
    # Add JSON summaries display in sidebar
    st.sidebar.title("Most Recent JSON Request")
    if "json_summaries" in st.session_state and st.session_state.json_summaries:
        with st.sidebar.expander("View JSON Summary"):
            last_summary = st.session_state.json_summaries[-1]
            st.sidebar.json(last_summary)
            
            # Show debug info if there's an error
            if "error" in last_summary:
                st.sidebar.error("JSON parsing failed")
                if "raw_text" in last_summary:
                    st.sidebar.code(last_summary["raw_text"], language="json")

    # Display conversation history
    display_conversation()

    # Handle user input
    handle_user_input()



if __name__ == "__main__":
    run_app()