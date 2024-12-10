import os
from openai import AzureOpenAI
import streamlit as st

def get_code_review(code_snippet: str, question: str):
    """
    Get code review from Azure OpenAI GPT
    Args:
        code_snippet: Code to review
        question: Specific question about the code
    """
    try:
        client = AzureOpenAI(
            azure_endpoint=st.secrets['AzureGPT']["AZURE_OPENAI_ENDPOINT"],
            api_key=st.secrets['AzureGPT']["AZURE_OPENAI_API_KEY"],
            api_version="2024-08-06"  # Update to current version
        )

        prompt = f"""
        Please review this code and answer the specific question:
        
        Code:
        ```python
        {code_snippet}
        ```
        
        Question: {question}
        
        Please provide a detailed analysis and any potential fixes.
        """

        response = client.chat.completions.create(
            model="gpt-4",  # Use your actual deployment name
            messages=[
                {"role": "system", "content": "You are a helpful programming assistant skilled in Python code review."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"

# Example usage
if __name__ == "__main__":
    code = """
    # Your problematic code here
    print(a + '2')
    """
    question = "Why isn't this code working?"
    
    analysis = get_code_review(code, question)
    print(analysis)