import json
import streamlit as st
import requests
import uuid
from streamlit.components.v1 import html


# CHATBOT_SERVICE_URL = "https://api-dev.edvoy.com"
CHATBOT_SERVICE_URL = "https://chatbot.loca.ltjhd"

def render_merged_response(text_response, sources, response_placeholder, intent):
    """Render both text response and sources together. Sources should be HTML strings for proper rendering."""
    # Start with the text response
    merged_html = f'<div class="genie-message"><strong>Genie:</strong> {text_response}</div>'
    
    # Add sources if they exist
    if sources:
        merged_html += '<div class="sources-section">'
        course_content = """
<div class="course-card">
    <div class="course-content">
        <div class="course-title">{course_name}</div>
        <div class="course-university">🏛️ University: {university_name}</div>
        <div class="course-location">📍 Location: {location}</div>
        <a href="{course_url}" target="_blank" class="course-link">View Course ↗</a>
    </div>
</div>
"""
        
        university_content = """
<div class="course-card">
    <div class="course-content">
        <div class="course-title">{university_name}</div>
        <div class="course-location">📍 Location: {location}</div>
        <a href="{university_url}" target="_blank" class="course-link">View University ↗</a>
    </div>
</div>
"""

        for i, source in enumerate(sources[:5]):
            # source should be a valid HTML string
            if intent == "UNIVERSITY_SEARCH":
                university_name = source.get("name", "Unknown University")
                address = source.get("address", {})
                location = address.get('country', 'N/A')
                university_url = source.get("url", f"https://edvoy.com/institutions/{source.get("refId")}/")
                merged_html += university_content.format(university_name=university_name,location=location,university_url=university_url)
            else:
                institution = source.get("institution", {})
                address = institution.get("address", {})
                course_name = source.get("name", "Course Title")
                university_name = institution.get("name", "Unknown University")
                location = address.get('country', 'N/A')
                course_url = source.get("url", f"https://edvoy.com/institutions/{source.get("edpRefId")}/{source.get("courseLevel","").lower()}/{source.get("slug")}/")
                merged_html += course_content.format(course_name=course_name,university_name=university_name,location=location,course_url=course_url)
        merged_html += '</div>'
    
    response_placeholder.markdown(merged_html, unsafe_allow_html=True)

st.set_page_config(page_title="Genie 🎓 Assistant", layout="wide")

# Add some custom styling for the main app
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
    font-weight: bold;
    text-align: center;
    margin-bottom: 30px;
}
.chat-container {
    max-height: 600px;
    overflow-y: auto;
    padding: 20px;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    margin-bottom: 20px;
}
.user-message {
    background: #f0f8ff;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 4px solid #667eea;
    color: #000000;
}
.genie-message {
    background: #f9f9f9;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 4px solid #764ba2;
    color: #000000;
}
.sources-section {
    margin-top: 20px;
}
.sources-header {
    color: #667eea;
    font-size: 1.3em;
    margin-bottom: 15px;
    font-weight: bold;
}
.course-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 20px;
    margin: 15px 0;
    color: white;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    opacity: 0;
    animation: slideInUp 0.6s ease forwards;
    position: relative;
    overflow: hidden;
}
.course-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}
.course-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    transition: left 0.5s;
}
.course-card:hover::before {
    left: 100%;
}
.course-content {
    position: relative;
    z-index: 1;
}
@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.course-title {
    font-size: 1.5em;
    font-weight: bold;
    margin-bottom: 10px;
    color: #ffffff;
}
.course-university {
    font-size: 1.1em;
    margin-bottom: 8px;
    color: #f0f0f0;
}
.course-location {
    font-size: 1em;
    margin-bottom: 15px;
    color: #e0e0e0;
}
.course-link {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    text-decoration: none;
    font-weight: bold;
    transition: background 0.3s ease;
}
.course-link:hover {
    background: rgba(255, 255, 255, 0.3);
    color: white;
    text-decoration: none;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Genie 🎓 Study Abroad Assistant</h1>', unsafe_allow_html=True)

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
    query = st.text_input("Ask me anything about studying abroad:", key="user_input", placeholder="e.g., I want to study Computer Science in Canada")
    col1, col2 = st.columns([1, 5])
    with col1:
        submitted = st.form_submit_button("Send 🚀", use_container_width=True)

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
if st.session_state.history:
    st.subheader("💬 Chat History")
    chat_container = st.container()
    with chat_container:
        for entry in st.session_state.history:
            if entry["sender"] == "user":
                st.markdown(f'<div class="user-message"><strong>You:</strong> {entry["text"]}</div>', unsafe_allow_html=True)
            else:
                # Check if this entry has sources to display as well
                if "sources" in entry:
                    render_merged_response(entry["text"], entry["sources"], st, entry["intent"])
                else:
                    st.markdown(f'<div class="genie-message"><strong>Genie:</strong> {entry["text"]}</div>', unsafe_allow_html=True)

# Handle streaming response
if st.session_state.task_id:
    # Create a placeholder for the streaming response
    response_placeholder = st.empty()
    response_placeholder.markdown("*🧞‍♂️ Genie is thinking...*")
    
    try:
        with requests.get(
            f"{CHATBOT_SERVICE_URL}/chat-bot/chat-stream/{st.session_state.task_id}",
            stream=True,
            timeout=30
        ) as resp:
            resp.raise_for_status()
            full_response = ""
            sources = []
            intent = ""
            
            # Stream the response
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = line.lstrip("data: ")
                        # Parse each line as JSON
                        chunk_data = json.loads(data)                        
                        
                        # Process content_chunk messages
                        if chunk_data.get("type") == "content_chunk":
                            text_chunk = chunk_data.get("text_chunk", "")
                            full_response += text_chunk
                            # Update the placeholder with accumulated response only
                            response_placeholder.markdown(f'<div class="genie-message"><strong>Genie:</strong> {full_response}</div>', unsafe_allow_html=True)
                        
                        # Process ai_response_completed messages
                        elif chunk_data.get("type") == "ai_response_completed":
                            sources = chunk_data["data"].get("sources", [])
                            intent = chunk_data["data"].get("intent","")
                            # Now render both text and sources together
                            render_merged_response(full_response, sources, response_placeholder, intent)
                            
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
            
            # Add complete response to history with sources and clear task
            if full_response:
                history_entry = {"sender": "genie", "text": full_response}
                history_entry["intent"] = intent
                if sources:
                    history_entry["sources"] = sources
                st.session_state.history.append(history_entry)
            
        # Clear task and rerun to show final state
        st.session_state.task_id = None
        st.rerun()
            
    except requests.exceptions.RequestException as e:
        response_placeholder.error(f"Error streaming response: {e}")
        st.session_state.task_id = None
    except Exception as e:
        response_placeholder.error(f"Unexpected error: {e}")
        st.session_state.task_id = None