import streamlit as st
import requests
import time

st.title("TailorTalk Booking Agent")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input box for user message
user_input = st.chat_input("What would you like to schedule?")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call FastAPI backend with retry logic
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post("http://localhost:8000/process_message", json={"message": user_input}, timeout=10)
            response.raise_for_status()
            agent_response = response.json()["response"]
            break
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                agent_response = f"❌ Error connecting to backend after {max_retries} attempts: {str(e)}. Please ensure the backend is running at http://localhost:8000."
            else:
                time.sleep(2)  # Wait before retrying
                continue

    # Add agent response to history
    st.session_state.messages.append({"role": "assistant", "content": agent_response})
    with st.chat_message("assistant"):
        st.markdown(agent_response)