import json
import streamlit as st
import requests
import uuid
from streamlit.components.v1 import html


# CHATBOT_SERVICE_URL = "https://api-dev.edvoy.com"
CHATBOT_SERVICE_URL = "https://chatbot.loca.lt"
    
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
                            response_placeholder.markdown(f'<div class="genie-message"><strong>Genie:</strong> {full_response}</div>', unsafe_allow_html=True)
                        if chunk_data.get("type") == "ai_response_completed":
                            sources = [{'name': 'Manchester Metropolitan University', 'slug': 'manchester-metropolitan-university', 'refId': 'manchester-metropolitan-university', 'logoUrl': 'live/images/institutions/manchester-metropolitan-university.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'London Metropolitan University', 'slug': 'london-metropolitan-university', 'refId': 'london-metropolitan-university', 'logoUrl': 'live/images/institutions/london-metropolitan-university.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'The University of Law', 'slug': 'the-university-of-law', 'refId': 'the-university-of-law', 'logoUrl': 'live/images/institutions/the-university-of-law.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'Cardiff Metropolitan University', 'slug': 'cardiff-metropolitan-university', 'refId': 'cardiff-metropolitan-university', 'logoUrl': 'live/images/institutions/cardiff-metropolitan-university.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'QA Higher Education', 'slug': 'qa-higher-education', 'refId': 'qa-higher-education', 'logoUrl': None, 'address': {'country': 'United Kingdom'}}, {'name': 'Bangor University', 'slug': 'bangor-university', 'refId': 'bangor-university', 'logoUrl': 'live/images/institutions/bangor-university-logo.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'University of Reading', 'slug': 'university-of-reading', 'refId': 'university-of-reading', 'logoUrl': 'live/images/institutions/university-of-reading-new-logo.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'Swansea University', 'slug': 'swansea-university', 'refId': 'swansea-university', 'logoUrl': 'live/images/institutions/swansea-university-logo.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'London South Bank University', 'slug': 'london-south-bank-university', 'refId': 'london-south-bank-university', 'logoUrl': 'live/images/institutions/london-south-bank-university.svg', 'address': {'country': 'United Kingdom'}}, {'name': 'Northumbria University', 'slug': 'northumbria-university', 'refId': 'northumbria-university', 'logoUrl': 'live/images/institutions/Northumbria-University.svg', 'address': {'country': 'United Kingdom'}}] #chunk_data["data"].get("sources", [])
                            if sources:
                                st.write("DEBUG sources:", sources)
                                st.subheader("🎓 Recommended Courses & Universities")
                                
                                # Custom CSS for course cards
                                st.markdown("""
                                <style>
                                .course-card {
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    border-radius: 15px;
                                    padding: 20px;
                                    margin: 10px 0;
                                    color: white;
                                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                                }
                                .course-card:hover {
                                    transform: translateY(-5px);
                                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
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
                                for source in sources:
                                    # institution = source.get("institution", {})
                                    # address = institution.get("address", {})
                                    # course_name = source.get("name", "Course Title")
                                    # university_name = institution.get("name", "Unknown University")
                                    # location = address.get('country', 'N/A')
                                    # course_url = source.get("url", "#")
                                    
                                    # Render each course card
                                    st.markdown(f"""
                                    <div class="course-card">
                                        {source}
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
            
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