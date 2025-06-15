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

# Input and Send button logic
query = st.text_input("You:", key=f"user_input_{st.session_state.input_counter}")
if st.button("Send") and query.strip():
    try:
        resp = requests.post(
            "https://chatbot.loca.lt/chat-bot/chat",
            json={"session_id": st.session_state.session_id, "message": query}
        )
        resp.raise_for_status()
        st.session_state.history.append({"sender": "user", "text": query})
        st.session_state.task_id = resp.json().get("task_id")
        # Increment counter to create new input field (effectively clearing it)
        st.session_state.input_counter += 1
        st.rerun()  # Rerun to refresh the input field
    except requests.RequestException as e:
        st.error(f"Error sending message: {e}")

# Display chat history
for entry in st.session_state.history:
    prefix = "**You:**" if entry["sender"] == "user" else "**Genie:**"
    st.markdown(f"{prefix} {entry['text']}")

# If there's an ongoing task, stream the response
if st.session_state.task_id:
    placeholder = st.empty()
    placeholder.markdown("*Genie is typing...*")
    
    try:
        with requests.get(
            f"https://chatbot.loca.lt/chat-bot/chat-stream/{st.session_state.task_id}",
            stream=True
        ) as resp:
            resp.raise_for_status()
            full_response = ""
            
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    chunk = line.lstrip("data: ")
                    full_response += chunk
                    # Update the placeholder with the accumulated response
                    placeholder.markdown(f"**Genie:** {full_response}")
            
            # Add the complete response to history
            st.session_state.history.append({"sender": "genie", "text": full_response})
            # Clear the task_id and rerun to show final state
            st.session_state.task_id = None
            st.rerun()

    except Exception as e:
        st.error(f"Error streaming response: {e}")
        st.session_state.task_id = None