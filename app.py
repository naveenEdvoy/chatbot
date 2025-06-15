import json
import streamlit as st
import requests
import uuid
import os

CHATBOT_SERVICE_URL = "https://api-dev.edvoy.com"
    
st.set_page_config(page_title="Genie 🎓 Assistant", layout="wide")
st.title("Genie 🎓 Study Abroad Assistant")

# Initialize session vars
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []
if "task_id" not in st.session_state:
    st.session_state.task_id = None
if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0

# Create a form for better handling of input clearing
with st.form(key="chat_form", clear_on_submit=True):
    query = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

# Handle form submission
if submitted and query.strip():
    try:
        # Add user message to history immediately
        st.session_state.history.append({"sender": "user", "text": query})
        
        # Make API call
        resp = requests.post(
            f"{CHATBOT_SERVICE_URL}/chat-bot/chat",
            json={"session_id": st.session_state.session_id, "message": query},
            timeout=10
        )
        resp.raise_for_status()
        st.session_state.task_id = resp.json().get("task_id")
        st.rerun()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error sending message: {e}")
        # Remove the user message from history if API call failed
        if st.session_state.history and st.session_state.history[-1]["sender"] == "user":
            st.session_state.history.pop()

# Display chat history
chat_container = st.container()
with chat_container:
    for entry in st.session_state.history:
        if entry["sender"] == "user":
            st.markdown(f"**You:** {entry['text']}")
        else:
            st.markdown(f"**Genie:** {entry['text']}")

# Handle streaming response
if st.session_state.task_id:
    # Create a placeholder for the streaming response
    response_placeholder = st.empty()
    response_placeholder.markdown("*Genie is typing...*")
    
    try:
        with requests.get(
            f"{CHATBOT_SERVICE_URL}/chat-bot/chat-stream/{st.session_state.task_id}",
            stream=True,
            timeout=30
        ) as resp:
            resp.raise_for_status()
            full_response = ""
            
            # Stream the response
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    try:

                        data = line.lstrip("data: ")
                        # Parse each line as JSON
                        chunk_data = json.loads(data)                        
                        # Only process content_chunk messages
                        if chunk_data.get("type") == "content_chunk":
                            text_chunk = chunk_data.get("text_chunk", "")
                            full_response += text_chunk
                            # Update the placeholder with accumulated response
                            response_placeholder.markdown(f"**Genie:** {full_response}")
                            
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
                    # chunk = line.lstrip("data: ")
                    # full_response += chunk
                    # # Update the placeholder with accumulated response
                    # response_placeholder.markdown(f"**Genie:** {full_response}")
            
            # Add complete response to history and clear task
            if full_response:
                st.session_state.history.append({"sender": "genie", "text": full_response})
            
        # Clear task and rerun to show final state
        st.session_state.task_id = None
        st.rerun()
            
    except requests.exceptions.RequestException as e:
        response_placeholder.error(f"Error streaming response: {e}")
        st.session_state.task_id = None
    except Exception as e:
        response_placeholder.error(f"Unexpected error: {e}")
        st.session_state.task_id = None