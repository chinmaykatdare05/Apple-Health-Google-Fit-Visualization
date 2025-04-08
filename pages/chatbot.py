import streamlit as st
import time
from typing import List, Generator, Tuple
import numpy as np
import pandas as pd
from pandasai import Agent

# from pandasai.llm.openai import OpenAI

# Set page configuration
st.set_page_config(
    page_title="Vitalize - Chatbot",
    layout="wide",
    page_icon="💪",
    initial_sidebar_state="auto",
)

st.logo(
    "./logo.png",
    size="large",
    icon_image="./logo.png",
)


def response_generator(response: str) -> Generator[str, None, None]:
    """
    Generator that yields one word at a time from the response, emulating a streaming effect.

    Parameters:
        response (str): The full response string.

    Yields:
        str: The next word in the response, followed by a space.
    """
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


# Main Streamlit App
st.title("Vitalize Chatbot")

if "data" not in st.session_state:
    st.write("Please upload a file to enable chatbot.")
else:
    data: pd.DataFrame = st.session_state.get("data", None)
    if data is not None:
        api_key = st.text_input("Enter your OpenAI API key:", type="password")
        if not api_key:
            st.warning("Please enter your OpenAI API key to proceed.")
            st.stop()
        try:
            # llm = OpenAI(api_token=api_key)
            agent = Agent(data)
        except Exception as e:
            st.error(f"An error occurred while initializing the AI: {e}")
            st.stop()

    # Initialize chat history if not already present.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input and Response Handling.
    prompt: str = st.chat_input("Hi there! How can I assist you today?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Retrieve documents and generate answer.
        with st.chat_message("assistant"):
            try:
                answer = agent.chat(prompt)
                # Simulate streaming response.
                st.markdown(response_generator(answer), unsafe_allow_html=False)

            except Exception as e:
                answer = f"An error occurred: {e}"
                st.error(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    # Button to clear chat history.
    if st.button("Clear Chat"):
        st.session_state.messages = []
