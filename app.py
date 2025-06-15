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

# Input and Send button logic
query = st.text_input("You:", key="query")
if st.button("Send") and query.strip():
    resp = requests.post(
        "https://chatbot.loca.lt/chat-bot/chat",
        json={"session_id": st.session_state.session_id, "message": query}
    )
    resp.raise_for_status()
    st.session_state.history.append({"sender": "user", "text": query})
    st.session_state.task_id = resp.json().get("task_id")
    st.session_state.query = ""  # clear input

# Display chat history
for entry in st.session_state.history:
    prefix = "**You:**" if entry["sender"] == "user" else "**Genie:**"
    st.markdown(f"{prefix} {entry['text']}")

# If there's an ongoing task, stream the response
if st.session_state.task_id:
    st.markdown("*Genie is typing...*")
    try:
        with requests.get(
            f"https://chatbot.loca.lt/chat-bot/chat-stream/{st.session_state.task_id}",
            stream=True
        ) as resp:
            resp.raise_for_status()
            buffer = ""
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    chunk = line.lstrip("data: ")
                    buffer += chunk
                    # Append chunk to history and show as it's typed
                    st.session_state.history.append({"sender": "genie", "text": chunk})
                    st.empty()  # clear and re-render
                    for e in st.session_state.history:
                        prefix = "**You:**" if e["sender"] == "user" else "**Genie:**"
                        st.markdown(f"{prefix} {e['text']}")
        # Done streaming, clear task_id
        st.session_state.task_id = None

    except Exception as e:
        st.error(f"Error streaming response: {e}")
        st.session_state.task_id = None