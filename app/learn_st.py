import streamlit as st
from time import sleep

placeholder = st.empty()

# Replace the placeholder with some text:
placeholder.text("Hello")
sleep(4)
# Replace the text with a chart:
placeholder.line_chart({"data": [1, 5, 2, 6]})
sleep(4)
# Replace the chart with several elements:
with placeholder.container():
    st.write("This is one element")
    st.write("This is another")

sleep(4)
# Clear all those elements:
placeholder.empty()