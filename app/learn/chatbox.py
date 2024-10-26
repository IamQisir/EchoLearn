import streamlit as st
from ai_chat import AIChat


def main():
    st.title("エコー発音先生🤖🧠🇦🇮👾")

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

main()