import streamlit as st
from streamlit_extras.image_coordinates import streamlit_image_coordinates
import random

def example():
    "# Click on the image"
    last_coordinates = streamlit_image_coordinates("./logo/EchoLearn.png")

    st.write(last_coordinates)

example()
st.write(f"Hey! There is a random number: {random.random()}")