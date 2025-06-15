import streamlit as st
import requests
import uuid

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

# Custom CSS for chat bubbles
st.markdown("""
<style>
.user-message {
    background-color: #007bff;
    color: white;
    padding: 10px 15px;
    border-radius: 18px 18px 5px 18px;
    margin: 5px 0;
    margin-left: 20%;
    text-align: right;
    max-width: 75%;
    float: right;
    clear: both;
    word-wrap: break-word;
}
.genie-message {
    background-color: #f1f3f5;
    color: #333;
    padding: 10px 15px;
    border-radius: 18px 18px 18px 5px;
    margin: 5px 0;
    margin-right: 20%;
    max-width: 75%;
    float: left;
    clear: both;
    word-wrap: break-word;
}
.chat-container {
    margin-bottom: 20px;
}
.message-wrapper {
    overflow: hidden;
    margin-bottom: 10px;
}
.user-avatar {
    background-color: #007bff;
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 12px;
    float: right;
    margin-left: 10px;
    margin-top: 5px;
}
.genie-avatar {
    background-color: #28a745;
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 12px;
    float: left;
    margin-right: 10px;
    margin-top: 5px;
}
.input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: white;
    padding: 15px;
    border-top: 1px solid #e0e0e0;
    z-index: 1000;
}
.main-content {
    padding-bottom: 100px;
}
</style>
""", unsafe_allow_html=True)

# Display chat history with bubble design
st.markdown('<div class="main-content">', unsafe_allow_html=True)
chat_container = st.container()
with chat_container:
    for entry in st.session_state.history:
        if entry["sender"] == "user":
            st.markdown(f"""
            <div class="message-wrapper">
                <div class="user-avatar">U</div>
                <div class="user-message">
                    {entry['text']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message-wrapper">
                <div class="genie-avatar">🧞</div>
                <div class="genie-message">
                    {entry['text']}
                </div>
            </div>
            """, unsafe_allow_html=True)

# Handle streaming response (keep this before the input form)
if st.session_state.task_id:
    # Create a placeholder for the streaming response
    response_placeholder = st.empty()
    response_placeholder.markdown("""
    <div class="message-wrapper">
        <div class="genie-avatar">🧞</div>
        <div class="genie-message">
            <em>Genie is typing...</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        import json
        
        with requests.get(
            f"https://chatbot.loca.lt/chat-bot/chat-stream/{st.session_state.task_id}",
            stream=True,
            timeout=30
        ) as resp:
            resp.raise_for_status()
            full_response = ""
            
            # Stream the response
            for line in resp.iter_lines(decode_unicode=True):
                if line.strip():
                    try:

                        data = line.lstrip("data: ")
                        # Parse each line as JSON
                        chunk_data = json.loads(data)                        
                        # Only process content_chunk messages
                        if chunk_data.get("type") == "content_chunk":
                            text_chunk = chunk_data.get("text_chunk", "")
                            full_response += text_chunk
                            # Update the placeholder with accumulated response
                            response_placeholder.markdown(f"""
                            <div class="message-wrapper">
                                <div class="genie-avatar">🧞</div>
                                <div class="genie-message">
                                    {full_response}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
            
            # Add complete response to history and clear task
            if full_response.strip():
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

st.markdown('</div>', unsafe_allow_html=True)

# Fixed input at bottom
st.markdown('<div class="input-container">', unsafe_allow_html=True)
with st.form(key="chat_form", clear_on_submit=True):
    query = st.text_input("Type your message...", key="user_input", label_visibility="collapsed")
    col1, col2 = st.columns([6, 1])
    with col2:
        submitted = st.form_submit_button("Send", use_container_width=True)

# Handle form submission
if submitted and query.strip():
    try:
        # Add user message to history immediately
        st.session_state.history.append({"sender": "user", "text": query})
        
        # Make API call
        resp = requests.post(
            "https://chatbot.loca.lt/chat-bot/chat",
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

st.markdown('</div>', unsafe_allow_html=True)