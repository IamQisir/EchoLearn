import gradio as gr
import random
import time
import google.generativeai as genai

GOOGLE_API_KEY="AIzaSyBi8IrHJYkw7wSfbo2t8tmUH1zhNkgfHH0"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

with gr.Blocks() as demo:
    # Chatbox is a page presented as a chat interface
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(history):
        bot_message = model.generate_content(history[-1][0]).text
        time.sleep(2)
        history[-1][1] = bot_message
        return history
    
    # set queue to False to avoid waiting for the response before sending the next message
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    # lambda function receives no arguments and returns None to clear the chatbot
    clear.click(lambda: None, None, chatbot, queue=False)
# make sure the app is executed as a queue
# only when the first task is over, then the next task will be executed
demo.queue()
# deploy the app
demo.launch()
