# utils/audio_handler.py

import streamlit as st
from datetime import datetime
import soundfile as sf
import azure.cognitiveservices.speech as speechsdk

class AudioHandler:
    """Handles audio recording and processing"""
    
    def __init__(self, user):
        self.user = user
        self.setup_azure_speech()

    def setup_azure_speech(self):
        """Setup Azure Speech SDK configuration"""
        self.speech_key = st.secrets["Azure_Speech"]["SPEECH_KEY"]
        self.service_region = st.secrets["Azure_Speech"]["SPEECH_REGION"]
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.service_region
        )

    def record_audio(self):
        """Record audio from microphone"""
        return st.audio_input(
            "マイクのアイコンをクリックして、録音しましょう！",
            key='audio_input'
        )

    def save_audio(self, audio_bytes_io, selection):
        """Save recorded audio to file"""
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"{self.user.today_path}/{selection}-{current_time}.wav"
        
        audio_data, sr = sf.read(audio_bytes_io, dtype="int16")
        sf.write(
            file_name,
            audio_data,
            sr,
            format="WAV",
            subtype="PCM_16"
        )
        return file_name

    def process_audio(self, audio_file, reference_text):
        """Process audio file and return pronunciation assessment"""
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
        pronunciation_config = self.create_pronunciation_config(reference_text)
        
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        pronunciation_config.apply_to(speech_recognizer)
        
        result = speech_recognizer.recognize_once_async().get()
        return self.parse_result(result)

    def create_pronunciation_config(self, reference_text):
        """Create pronunciation assessment configuration"""
        return speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )

    def parse_result(self, result):
        """Parse recognition result"""
        import json
        return json.loads(
            result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult
            )
        )