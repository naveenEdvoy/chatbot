import streamlit as st
import requests
import uuid

st.set_page_config(page_title="Genie 🎓 Assistant", layout="wide")
st.title("Genie 🎓 Study Abroad Assistant")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []

query = st.text_input("You:", key="user_input")
if st.button("Send") and query:
    res = requests.post(
        "https://chatbot.loca.lt/chatbot/chat",
        json={"user_id": st.session_state.session_id, "query": query}
    )
    res.raise_for_status()
    st.session_state.history.append({"sender": "user", "text": query})
    st.session_state.task_id = res.json()["task_id"]
    st.experimental_rerun()

for entry in st.session_state.history:
    prefix = "**You:**" if entry["sender"] == "user" else "**Genie:**"
    st.markdown(f"{prefix} {entry['text']}")

if "task_id" in st.session_state:
    buffer = ""
    r = requests.get(f"https://chatbot.loca.lt/chatbot/chat-stream/{st.session_state.task_id}", stream=True)
    for line in r.iter_lines(decode_unicode=True):
        if line:
            chunk = line.lstrip("data: ")
            buffer += chunk
            st.session_state.history.append({"sender": "genie", "text": chunk})
            st.experimental_rerun()
    del st.session_state["task_id"]