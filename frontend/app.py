import json
import requests
import streamlit as st
import os

st.set_page_config(page_title="Cloudstok Inventory Agent", page_icon=":package:", layout="wide")
st.title("Cloudstok Inventory Agent")
st.caption("Ask me anything about warehouse inventory in plain English.")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

sample_queries = [
    "Check stock for SKU-1001",
    "Do we have any 220V compatible power supplies?",
    "Generate a low stock report",
    "Add 50 units to SKU-1004, reason: new shipment received",
]

with st.sidebar:
    st.header("Sample Queries")
    for q in sample_queries:
        if st.button(q, use_container_width=True):
            st.session_state.pending_query = q

prompt = st.chat_input("Ask the inventory agent...")
if st.session_state.pending_query and not prompt:
    prompt = st.session_state.pending_query
    st.session_state.pending_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={"message": prompt},
                    stream=True,
                    timeout=60,
                )
                res.raise_for_status()
                response_text = ""
                for line in res.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line.removeprefix("data: ").strip()
                    if payload == "[DONE]":
                        break
                    try:
                        response_text = json.loads(payload).get("text", response_text)
                    except Exception:
                        response_text = payload
                if not response_text:
                    response_text = "Error connecting to agent."
            except Exception as exc:
                response_text = f"Backend request failed: {exc}"
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
