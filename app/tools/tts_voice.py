import azure.cognitiveservices.speech as speechsdk
import os
import streamlit as st
from glob import glob
from pathlib import Path

def generate_azure_tts(text: str, output_path: str) -> None:
    """
    Generate American male TTS using Azure Cognitive Services
    Args:
        text: Text to convert to speech
        output_path: Path to save WAV file
    """
    try:
        # Configure speech service
        speech_config = speechsdk.SpeechConfig(
            subscription=st.secrets["Azure_Speech"]["SPEECH_KEY"],
            region=st.secrets["Azure_Speech"]["SPEECH_REGION"]
        )
        
        # Set voice name
        speech_config.speech_synthesis_voice_name = "en-US-GuyNeural"
        
        # Create audio config
        audio_config = speechsdk.AudioConfig(filename=output_path)
        
        # Create synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        # Generate speech
        result = speech_synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"Speech synthesized to: {output_path}")
        else:
            print(f"Error: {result.reason}")
            
    except Exception as e:
        print(f"Error generating TTS: {str(e)}")


def process_txt_files(input_dir: str, output_dir: str) -> None:
    """
    Process all txt files in input directory and generate wav files
    Args:
        input_dir: Directory containing txt files
        output_dir: Directory to save wav files
    """
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all txt files
    txt_files = glob(os.path.join(input_dir, "*.txt"))
    
    for txt_file in txt_files:
        try:
            # Get filename without extension
            base_name = Path(txt_file).stem
            # Create output wav path
            wav_path = os.path.join(output_dir, f"{base_name}.wav")
            
            # Read text content
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            if text:  # Only process if file has content
                print(f"Processing: {txt_file}")
                generate_azure_tts(text, wav_path)
            else:
                print(f"Skipping empty file: {txt_file}")
                
        except Exception as e:
            print(f"Error processing {txt_file}: {str(e)}")

# Example usage
if __name__ == "__main__":
    folder_path = r"D:\Documents\my_voice"
    process_txt_files(folder_path, folder_path)