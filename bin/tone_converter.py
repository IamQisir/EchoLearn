import sys
sys.path.append('../../OpenVoice')
import os
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
import google.generativeai as genai
from speech_synthesis import text_to_speech


ckpt_converter = '../checkpoints_v2/converter'
device="cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = '../outputs_v2'

tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')
os.makedirs(output_dir, exist_ok=True)

base_speaker = f"{output_dir}/gemini_source_audio.mp3"
source_se, audio_name = se_extractor.get_se(base_speaker, tone_color_converter, vad=True)

reference_speaker = '../resources/Chyisell_voice.m4a' # This is the voice you want to clone
target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, vad=True)

#Obtain your API key from the Google AI Studio
GOOGLE_API_KEY="AIzaSyBi8IrHJYkw7wSfbo2t8tmUH1zhNkgfHH0"
genai.configure(api_key=GOOGLE_API_KEY)

src_path = f'{output_dir}/gemini_source_output.mp3'
save_path = f'{output_dir}/output_crosslingual.wav'

def func():
    input_text = input('What do you want to ask?\n')
    while input_text != '#':
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(input_text)
        print(response.text)
        text_to_speech(response.text)
        encode_message = "@MyShell"
        tone_color_converter.convert(
            audio_src_path=src_path, 
            src_se=source_se, 
            tgt_se=target_se, 
            output_path=save_path,
            message=encode_message)
        input_text = input('What do you want to ask?\n')

func()