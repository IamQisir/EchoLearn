# services/ai_chat.py

from typing import Dict, Optional, Generator, Any
import time
import streamlit as st
from openai import AzureOpenAI
from dataclasses import dataclass

@dataclass
class ErrorSummary:
    """Summarizes pronunciation errors"""
    error_type: str
    count: int
    words: list[str]

class AIChat:
    """Manages AI chat interactions for pronunciation feedback"""
    
    BASE_PROMPT = """
    You are a friendly and supportive English pronunciation tutor. I've just finished a pronunciation practice session and would like your help improving. Here are my mistakes:

    {error_summary}

    Please act as my personal tutor and:
    1. 🎯 First, give me encouraging feedback about my practice attempt
    2. 💡 Explain in a conversational way why these errors might have occurred
    3. 🗣️ Provide practical examples and demonstrations using simple words
    4. ✨ Give me 2-3 quick exercises I can try right now to improve
    5. 🌟 End with an encouraging message for my next practice

    Please keep your response friendly and supportive, as if we're having a face-to-face tutoring session!
    Don't forget respond in Japanese! But don't teach with Katanana or Hiragana.
    """
    
    def __init__(self):
        self._initialize_client()
        
    def _initialize_client(self) -> None:
        """Initialize Azure OpenAI client"""
        try:
            self.client = AzureOpenAI(
                azure_endpoint=st.secrets['AzureGPT']["AZURE_OPENAI_ENDPOINT"],
                api_key=st.secrets['AzureGPT']["AZURE_OPENAI_API_KEY"],
                api_version="2024-02-15-preview"
            )
        except Exception as e:
            st.warning(f"Error initializing Azure OpenAI: {str(e)}")
            self.client = None
            
    def format_error_summary(self, errors: Dict[str, ErrorSummary]) -> Optional[str]:
        """Format error data into summary text"""
        if not errors:
            return None
            
        summaries = []
        for error_type, data in errors.items():
            if data.count > 0:
                summaries.append(
                    f"I made {data.count} {error_type} mistakes "
                    f"with these words: {', '.join(data.words)}"
                )
        
        return "\n".join(summaries) if summaries else None
    
    def get_chat_response(self, errors: Dict[str, Any]) -> Optional[Generator[str, None, None]]:
        """Get streaming response from Azure GPT"""
        if not self.client:
            st.error("AI chat service is not initialized")
            return None
            
        error_summary = self.format_error_summary(errors)
        if not error_summary:
            return None
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful English pronunciation tutor."},
                    {"role": "user", "content": self.BASE_PROMPT.format(error_summary=error_summary)}
                ],
                stream=True,
                temperature=0.7,
                max_tokens=800
            )
            
            return self._stream_response(response)
            
        except Exception as e:
            st.error(f"Error getting chat response: {str(e)}")
            return None
    
    def _stream_response(self, response: Any) -> Generator[str, None, None]:
        """Generate streaming response"""
        for chunk in response:
            try:
                if chunk.choices and hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        time.sleep(0.01)
                        yield content
            except Exception as e:
                st.error(f"Streaming error: {str(e)}")
                continue