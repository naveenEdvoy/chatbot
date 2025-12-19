import json
import logging
import streamlit as st
import requests
import uuid
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


CHATBOT_SERVICE_URL = "https://api-qa.edvoy.com"
# CHATBOT_SERVICE_URL = "http://localhost:4110"

def render_course_cards(sources, intent):
    """Generate HTML for course or university sources."""
    if not sources:
        return ""
    
    html_output = '<div class="sources-section">'
    course_template = """
<div class="course-card">
    <div class="course-content">
        <div class="course-title">{course_name}</div>
        <div class="course-university">🏛️ {university_name}</div>
        <div class="course-location">📍 {location}</div>
        <a href="{course_url}" target="_blank" class="course-link">View Course ↗</a>
    </div>
</div>
"""
    
    university_template = """
<div class="course-card">
    <div class="course-content">
        <div class="course-title">{university_name}</div>
        <div class="course-location">📍 {location}</div>
        <a href="{university_url}" target="_blank" class="course-link">View University ↗</a>
    </div>
</div>
"""

    for source in sources[:5]:
        if intent == "UNIVERSITY_SEARCH":
            university_name = source.get("name", "Unknown University")
            address = source.get("address", {})
            location = address.get('country', 'N/A')
            ref_id = source.get("refId", "")
            university_url = source.get("url", f"https://edvoy.com/institutions/{ref_id}/")
            html_output += university_template.format(university_name=university_name, location=location, university_url=university_url)
        else:
            institution = source.get("institution", {})
            address = institution.get("address", {})
            course_name = source.get("name", "Course Title")
            university_name = institution.get("name", "Unknown University")
            location = address.get('country', 'N/A')
            edp_ref_id = source.get("edpRefId", "")
            course_level = (source.get("courseLevel") or "").lower()
            slug = source.get("slug", "")
            course_url = source.get("url", f"https://edvoy.com/institutions/{edp_ref_id}/{course_level}/{slug}/")
            html_output += course_template.format(course_name=course_name, university_name=university_name, location=location, course_url=course_url)
    
    html_output += '</div>'
    return html_output

def render_message(entry, placeholder=st):
    """Render a single message entry with all its metadata."""
    if entry["sender"] == "user":
        placeholder.markdown(f'<div class="user-message"><strong>You:</strong> {entry["text"]}</div>', unsafe_allow_html=True)
    else:
        # Check for thinking state
        thinking_text = entry.get("thinkingText", "")
        text = entry.get("text", "")
        
        # Display Header
        placeholder.markdown(f'<div class="genie-header"><strong>🧞‍♂️ Genie</strong></div>', unsafe_allow_html=True)
        
        # Thinking State (only show if no text or if it's explicitly a transition)
        if thinking_text and not entry.get("isStreamEnded", False):
            placeholder.markdown(f'<div class="thinking-message"><span class="pulse"></span> {thinking_text}</div>', unsafe_allow_html=True)
        
        if text:
            # Render main response
            placeholder.markdown(text)
            
            # Sources/Cards
            sources = entry.get("sources", [])
            if sources:
                placeholder.markdown(render_course_cards(sources, entry.get("intent", "")), unsafe_allow_html=True)
            
            # Suggestions
            suggestions = entry.get("suggestions", [])
            if suggestions and entry.get("isStreamEnded", False):
                # Using a container for suggestions to keep them grouped
                with placeholder.container():
                    st.write("---") # Visual separator
                    st.caption("Suggested actions:")
                    # Create columns for buttons to simulate chips
                    cols = st.columns(len(suggestions) if len(suggestions) > 0 else 1)
                    for i, sugg in enumerate(suggestions):
                        btn_label = sugg.get("text", sugg.get("prompt", "Option"))
                        # Use a unique key for each button
                        if i < len(cols):
                            if cols[i].button(btn_label, key=f"sugg_{entry.get('id', 'h')}_{i}"):
                                st.session_state.suggestion_clicked = {
                                    "prompt": sugg.get("prompt"),
                                    "action": sugg.get("action")
                                }
                                st.rerun()

st.set_page_config(page_title="Genie 🎓 Assistant", layout="wide")

# Custom CSS
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
.user-message {
    background: #f0f8ff;
    padding: 12px 16px;
    border-radius: 15px 15px 0 15px;
    margin: 10px 0 10px auto;
    border-right: 4px solid #667eea;
    color: #1a1a1a;
    max-width: 80%;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.genie-header {
    color: #764ba2;
    margin-bottom: 4px;
    font-size: 0.9em;
    margin-top: 15px;
}
.thinking-message {
    background: #f9f9f9;
    padding: 10px 16px;
    border-radius: 0 15px 15px 15px;
    border-left: 4px solid #d1d5db;
    color: #6b7280;
    font-style: italic;
    display: flex;
    align-items: center;
    gap: 10px;
}
.pulse {
    width: 8px;
    height: 8px;
    background-color: #d1d5db;
    border-radius: 50%;
    animation: pulse-animation 1.5s infinite;
}
@keyframes pulse-animation {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
}
.course-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.course-title { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
.course-link {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    color: white !important;
    padding: 5px 12px;
    border-radius: 15px;
    text-decoration: none;
    font-size: 0.85em;
    margin-top: 8px;
}
.sources-section {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 15px;
    margin-top: 10px;
}
/* Chat container styling */
.chat-container {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 200px);
    overflow-y: auto;
    padding-bottom: 20px;
}
/* Ensure input stays at bottom */
.stChatInput {
    position: sticky;
    bottom: 0;
    background-color: var(--background-color);
    z-index: 100;
    padding-top: 10px;
}
/* Auto-scroll to bottom */
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 20px;
}
</style>
<script>
function scrollToBottom() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}
// Scroll to bottom on page load
window.addEventListener('load', scrollToBottom);
// Scroll to bottom when content changes
const observer = new MutationObserver(scrollToBottom);
observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Genie 🎓 Study Abroad Assistant</h1>', unsafe_allow_html=True)

# Initialize session vars
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_response" not in st.session_state:
    st.session_state.pending_response = False
if "suggestion_clicked" not in st.session_state:
    st.session_state.suggestion_clicked = None

def send_message(query_text, action_key=""):
    try:
        logger.info(f"Sending message: {query_text[:50]}...")
        st.session_state.history.append({"sender": "user", "text": query_text})
        
        resp = requests.post(
            f"{CHATBOT_SERVICE_URL}/chat-bot/chat",
            json={
                "session_id": st.session_state.session_id,
                "message": query_text,
                "metadata": {
                    "university_name": "University of Derby",
                    "country": "United Kingdom"
                },
                "action_key": action_key
            },
            timeout=10
        )
        resp.raise_for_status()
        st.session_state.pending_response = True
        st.session_state.suggestion_clicked = None
        st.rerun()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        st.error(f"Failed to send message: {e}")

# Handle suggestion clicks
if st.session_state.suggestion_clicked:
    send_message(st.session_state.suggestion_clicked["prompt"], st.session_state.suggestion_clicked["action"] or "")

# Display chat history
if st.session_state.history:
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.session_state.pending_response = False
        st.session_state.session_id = str(uuid.uuid4()) # Start fresh
        st.rerun()

    for i, entry in enumerate(st.session_state.history):
        render_message(entry)

# Input area - moved to bottom after chat history
query = st.chat_input("Ask me anything about studying abroad...")
if query:
    send_message(query)

# Handle streaming response
if st.session_state.pending_response:
    response_placeholder = st.empty()
    
    try:
        sse_url = f"{CHATBOT_SERVICE_URL}/chat-bot/chat-stream/{st.session_state.session_id}"
        logger.info(f"Streaming from: {sse_url}")
        
        with requests.get(sse_url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            
            # Local state for the current streaming message
            current_msg = {
                "id": str(uuid.uuid4()),
                "sender": "genie",
                "text": "",
                "thinkingText": "Genie is thinking...",
                "sources": [],
                "suggestions": [],
                "intent": "",
                "isStreamEnded": False
            }
            
            for line in resp.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    try:
                        data_json = line[6:].strip()
                        if not data_json: continue
                        
                        chunk = json.loads(data_json)
                        ctype = chunk.get("type")
                        logger.debug(f"Event: {ctype}")
                        
                        if ctype == "status_update":
                            current_msg["thinkingText"] = chunk.get("data", {}).get("message") or chunk.get("message") or "Thinking..."
                        
                        elif ctype == "content_chunk":
                            if chunk.get("full_response_for_db"):
                                current_msg["text"] = chunk["full_response_for_db"]
                            elif chunk.get("text_chunk"):
                                current_msg["text"] += chunk["text_chunk"]
                        
                        elif ctype == "ai_response_completed":
                            current_msg["sources"] = chunk.get("data", {}).get("sources", [])
                            current_msg["intent"] = chunk.get("data", {}).get("intent", "")
                        
                        elif ctype == "final_summary":
                            if chunk.get("full_response_for_db"):
                                current_msg["text"] = chunk["full_response_for_db"]
                            elif chunk.get("data", {}).get("text"):
                                current_msg["text"] = chunk["data"]["text"]
                            current_msg["suggestions"] = chunk.get("data", {}).get("suggestions", [])
                            current_msg["isStreamEnded"] = True
                        
                        elif ctype in ["handoff_initiated", "information_gathering_required"]:
                            current_msg["text"] = chunk.get("full_response_for_db") or chunk.get("data", {}).get("text") or "Assistance required."
                            current_msg["isStreamEnded"] = True
                        
                        elif ctype == "stream_end":
                            current_msg["isStreamEnded"] = True
                        
                        elif ctype == "error":
                            current_msg["text"] = f"Error: {chunk.get('message', 'An unknown error occurred.')}"
                            current_msg["isStreamEnded"] = True

                        # Update UI
                        with response_placeholder.container():
                            render_message(current_msg)
                            
                        if current_msg["isStreamEnded"]:
                            st.session_state.history.append(current_msg)
                            st.session_state.pending_response = False
                            st.rerun()
                            break

                    except json.JSONDecodeError:
                        continue
            
    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
        st.session_state.pending_response = False
        st.rerun()
