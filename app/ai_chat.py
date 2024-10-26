import streamlit as st
import google.generativeai as genai
import time
import pandas as pd

class AIChat:
    def __init__(self):
        genai.configure(api_key=st.secrets["Gemini"]["GOOGLE_API_KEY"])
        self.model = genai.GenerativeModel("gemini-pro")
        self.prompt = ""

    def set_prompt(self, df):
        self.prompt = f"""
        あなたは発音の先生です。以下の発音エラーのリストを基に、各単語の正しい発音と改善のためのアドバイスを提供してください。
        発音エラーの統計 [エラータイプ、回数、単語]:
        - 省略 (Omission): 回数: {df.loc['省略 (Omission)', '回数']}, 単語リスト: {df.loc['省略 (Omission)', '単語']}
        - 挿入 (Insertion): 回数: {df.loc['挿入 (Insertion)', '回数']}, 単語リスト: {df.loc['挿入 (Insertion)', '単語']}
        - 発音ミス (Mispronunciation): 回数: {df.loc['発音ミス (Mispronunciation)', '回数']}, 単語リスト: {df.loc['発音ミス (Mispronunciation)', '単語']}
        - 不適切な間 (UnexpectedBreak): 回数: {df.loc['不適切な間 (UnexpectedBreak)', '回数']}, 単語リスト: {df.loc['不適切な間 (UnexpectedBreak)', '単語']}
        - 間の欠如 (MissingBreak): 回数: {df.loc['間の欠如 (MissingBreak)', '回数']}, 単語リスト: {df.loc['間の欠如 (MissingBreak)', '単語']}
        - 単調 (Monotone): 回数: {df.loc['単調 (Monotone)', '回数']}, 単語リスト: {df.loc['単調 (Monotone)', '単語']}

        各単語に対して、以下の形式で回答してください:
        1. 単語: [単語]
        2. 改善のアドバイス: [日本人に対しての改善のアドバイス]
        3. おすすめの練習：[ミニマルペアをおすすめ]
        """

    def stream_generator(self, response):
        # used to save the full response
        full_response = ""
        for chunk in response:
            if chunk.text:
                new_content = chunk.text
                full_response += new_content
                time.sleep(0.01)
                yield new_content

    def initial_output(self):
        if "initial_response" not in st.session_state:
            response = self.model.generate_content(self.prompt, stream=True)
            full_response = ""
            for content in self.stream_generator(response):
                full_response += content
            st.session_state.initial_response = full_response

        with st.chat_message("assistant"):
            st.markdown(st.session_state.initial_response)

# Example usage in Streamlit app
def main():
    st.title("AI Chatbox")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize AIChat instance
    ai_chat = AIChat()

    # Show chat history
    def show_history():
        for message in st.session_state.messages:
            if message is not None:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # Display chat messages from history on app rerun
    show_history()

    # Check if error_table exists and is not empty
    if "error_table" in st.session_state and not st.session_state.error_table.empty:
        # Set the prompt
        ai_chat.set_prompt(st.session_state.error_table)

        # Generate initial output but do not display it yet
        ai_chat.initial_output()

        # Add the initial response to the chat history
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.initial_response})

        # Display the initial response
        with st.chat_message("assistant"):
            st.markdown(st.session_state.initial_response)

    def chat_bot():    
        # React to user input
        if prompt := st.chat_input("What is up?"):
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Generate and display assistant response
            response = ai_chat.model.generate_content(prompt, stream=True)
            full_response = ""
            with st.chat_message("assistant"):
                for content in ai_chat.stream_generator(response):
                    st.markdown(content)
                    full_response += content
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Run the chat bot
    chat_bot()

if __name__ == "__main__":
    main()