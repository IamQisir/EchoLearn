import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from audio_recorder_streamlit import audio_recorder
import librosa
import io
import soundfile as sf
from streamlit_extras.customize_running import center_running
from time import sleep


st.set_page_config(layout="wide")

def audio_page():
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        with st.container(border=True):
            audio_bytes = audio_recorder(neutral_color="#e6ff33", sample_rate=16000)
            if audio_bytes:
                # make audio_bytes to a file
                audio_file = io.BytesIO(audio_bytes)

                # load data using soundfile
                y, sr = sf.read(audio_file, dtype='float32')

                # running man in the center!
                center_running()
                sleep(2)

                # plot the waveform of the audio file
                fig, ax = plt.subplots(figsize=(10, 4))
                librosa.display.waveshow(y, sr=sr)
                plt.title("Audio Waveform")
                plt.xlabel("Time [s]")
                plt.ylabel("Amplitude")
                plt.grid(True)
                st.pyplot(fig)
    with col2:
        with st.container(border=True):
            youglish_html = """
            <div style="width:50%;max-width:640px;">
                <a id="yg-widget-0" class="youglish-widget" data-query="great power" data-lang="english" 
                data-components="8415" data-bkg-color="theme_light" rel="nofollow" 
                href="https://youglish.com">Visit YouGlish.com</a>
            </div>
            """
            st.components.v1.html(youglish_html, height=300)


audio_page()