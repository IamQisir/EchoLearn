import time
import streamlit as st
from openai import AzureOpenAI

class AIChat:
    def __init__(self):
        try:
            self.client = AzureOpenAI(
                azure_endpoint=st.secrets['AzureGPT']["AZURE_OPENAI_ENDPOINT"],
                api_key=st.secrets['AzureGPT']["AZURE_OPENAI_API_KEY"],
                api_version="2024-02-15-preview"
            )
        except Exception as e:
            st.warning(f"Error initializing Azure OpenAI: {str(e)}")
        self.prompt = ""

    def set_prompt(self, error_data):
        """Generate conversational prompt for Azure GPT"""
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

    def format_errors_for_azure(self, current_errors):
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
        
        return "\n".join(error_summary) if error_summary else None

    def stream_generator(self, response):
        """Stream Azure GPT response chunks"""
        full_response = ""
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'content'):
                new_content = chunk.choices[0].delta.content
                if new_content:
                    full_response += new_content
                    time.sleep(0.01)
                    yield new_content

    def get_chat_response(self, error_data):
        """Get streaming response from Azure GPT"""
        formatted_errors = self.format_errors_for_azure(error_data)
        if not formatted_errors:
            return None
            
        self.set_prompt(formatted_errors)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Use your deployment name
                messages=[
                    {"role": "system", "content": "You are a helpful English pronunciation tutor."},
                    {"role": "user", "content": self.prompt}
                ],
                stream=True,
                temperature=0.7,
                max_tokens=800
            )
            return self.stream_generator(response)
            
        except Exception as e:
            st.error(f"Error getting chat response: {str(e)}")
            return None