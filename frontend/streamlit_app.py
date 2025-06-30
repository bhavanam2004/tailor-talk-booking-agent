import streamlit as st
import requests
import time

# Title
st.title("🤖 TailorTalk Booking Agent")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input from user
user_input = st.chat_input("What would you like to schedule?")

# 🌐 Your deployed backend URL on Railway
BACKEND_URL = "https://tailor-talk-booking-agent-production.up.railway.app/process_message"

# If user types a message
if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call FastAPI backend with retry logic
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(
                BACKEND_URL,
                json={"message": user_input},
                timeout=10
            )
            response.raise_for_status()
            agent_response = response.json().get("response", "❌ Unexpected response format.")
            break
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                agent_response = (
                    f"❌ Error connecting to backend after {max_retries} attempts:\n{str(e)}"
                )
            else:
                time.sleep(2)

    # Show assistant message
    st.session_state.messages.append({"role": "assistant", "content": agent_response})
    with st.chat_message("assistant"):
        st.markdown(agent_response)
