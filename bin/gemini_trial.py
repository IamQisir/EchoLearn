import google.generativeai as genai
from speech_synthesis import text_to_speech
import gradio as gr
import random
import time

#Obtain your API key from the Google AI Studio
GOOGLE_API_KEY="AIzaSyBi8IrHJYkw7wSfbo2t8tmUH1zhNkgfHH0"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.ClearButton([msg, chatbot])

    def respond(message, chat_history):
        global model
        bot_message = model.generate_content(message).text
        # chat_history contains all the previous messages
        chat_history.append((message, bot_message))
        time.sleep(1)
        return "", chat_history

    msg.submit(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

if __name__ == "__main__":
    demo.launch()