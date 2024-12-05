import streamlit as st
import google.generativeai as genai
import time
import pandas as pd

class AIChat:
    def __init__(self):
        genai.configure(api_key=st.secrets["Gemini"]["GOOGLE_API_KEY"])
        self.model = genai.GenerativeModel("gemini-pro")
        self.prompt = ""

    def set_prompt(self, error_data):
        """Generate conversational prompt for Gemini API"""
        base_prompt = """
        You are a friendly and supportive English pronunciation tutor. I've just finished a pronunciation practice session and would like your help improving. Here are my mistakes:

        {error_summary}

        Please act as my personal tutor and:
        1. 🎯 First, give me encouraging feedback about my practice attempt
        2. 💡 Explain in a conversational way why these errors might have occurred
        3. 🗣️ Provide practical examples and demonstrations using simple words
        4. ✨ Give me 2-3 quick exercises I can try right now to improve
        5. 🌟 End with an encouraging message for my next practice

        Please keep your response friendly and supportive, as if we're having a face-to-face tutoring session!
        """
        
        self.prompt = base_prompt.format(error_summary=error_data)
    
    def format_errors_for_gemini(self, current_errors):
        """Format error data into prompt text"""
        if not current_errors:
            return None
            
        error_summary = []
        for error_type, data in current_errors.items():
            if isinstance(data, dict) and data.get('count', 0) > 0:
                error_summary.append(
                    f"I made {data['count']} {error_type} mistakes "
                    f"with these words: {', '.join(data['words'])}"
                )
        
        if not error_summary:
            return None
            
        return "\n".join(error_summary)

    def stream_generator(self, response):
        # used to save the full response in a streaming mode
        full_response = ""
        for chunk in response:
            if chunk.text:
                new_content = chunk.text
                full_response += new_content
                time.sleep(0.01)
                yield new_content

    def initial_output(self, error_data):
        formatted_errors = self.format_errors_for_gemini(error_data)
        if not formatted_errors:
            return None
        self.set_prompt(formatted_errors)

        response = self.model.generate_content(self.prompt, stream=True)
        full_response = ""
        for content in self.stream_generator(response):
            full_response += content
        st.session_state.initial_response = full_response
        return full_response

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