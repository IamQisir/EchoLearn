# Import necessary libraries
import io
import os
import base64
import json
import librosa
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import gradio as gr
import google.generativeai as genai
import soundfile as sf
from collections import defaultdict
import azure.cognitiveservices.speech as speechsdk
from app.tools.avatar_synthesis import generate_avatar_video

# Initialize global variables for storing radar chart per attempt and error types
plt.rcParams['font.family'] = "MS Gothic"

#Obtain your API key from the Google AI Studio
GOOGLE_API_KEY="AIzaSyBi8IrHJYkw7wSfbo2t8tmUH1zhNkgfHH0"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Function to get color based on score
def get_color(score):
    if score >= 90:
        return '#00ff00'
    elif score >= 75:
        return '#ffff00'
    elif score >= 50:
        return '#ffa500'
    else:
        return '#ff0000'

# Function to create radar chart
def create_radar_chart(pronunciation_result):
    print(f"pronunciation_result 结构: {json.dumps(pronunciation_result, indent=2)}")

    overall_assessment = pronunciation_result['NBest'][0]['PronunciationAssessment']
    
    categories = {
        '正確性スコア': 'AccuracyScore',
        '流暢性スコア': 'FluencyScore',
        '完全性スコア': 'CompletenessScore',
        '発音スコア': 'PronScore'
    }
    
    scores = [overall_assessment.get(categories[cat], 0) for cat in categories]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))

    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
    scores += scores[:1]  # repeat the first value to close the polygon
    angles += angles[:1]

    ax.plot(angles, scores, linewidth=1, linestyle='solid')
    ax.fill(angles, scores, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories.keys())
    ax.set_ylim(0, 100)
    

    plt.title("発音評価のレーダーチャート")

    print(f"分数: {scores}")

    return fig

def create_waveform_plot(audio_file, pronunciation_result):
    y, sr = librosa.load(audio_file)
    duration = len(y) / sr
    
    fig, ax = plt.subplots(figsize=(12, 6))
    times = np.linspace(0, duration, num=len(y))
    
    ax.plot(times, y, color='gray', alpha=0.5)
    
    words = pronunciation_result['NBest'][0]['Words']
    for word in words:
        if 'PronunciationAssessment' not in word or 'ErrorType' not in word['PronunciationAssessment']:
            continue
        if word['PronunciationAssessment']['ErrorType'] == 'Omission':
            continue
        
        start_time = word['Offset'] / 10000000
        word_duration = word['Duration'] / 10000000
        end_time = start_time + word_duration
        
        start_idx = int(start_time * sr)
        end_idx = int(end_time * sr)
        word_y = y[start_idx:end_idx]
        word_times = times[start_idx:end_idx]
        
        score = word['PronunciationAssessment'].get('AccuracyScore', 0)
        color = get_color(score)
        
        ax.plot(word_times, word_y, color=color)
        ax.text((start_time + end_time) / 2, ax.get_ylim()[0], word['Word'], 
                ha='center', va='bottom', fontsize=8, rotation=45)
        ax.axvline(x=start_time, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Waveform with Pronunciation Assessment')
    
    plt.tight_layout()
    
    return fig

def pronunciation_assessment(audio_file, reference_text):
    print("进入 pronunciation_assessment 函数")
    global attempts
    
    # Be Aware!!! We are using free keys here but nonfree keys in Avatar
    speech_key, service_region = os.environ.get('SPEECH_KEY'), os.environ.get('SPEECH_REGION')
    print(f"SPEECH_KEY: {speech_key}, SPEECH_REGION: {service_region}")
    
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    print("SpeechConfig 创建成功")
    
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    print("AudioConfig 创建成功")
    
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True)
    print("PronunciationAssessmentConfig 创建成功")
    
    try:
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, 
            audio_config=audio_config)
        print("SpeechRecognizer 创建成功")
        
        pronunciation_config.apply_to(speech_recognizer)
        print("PronunciationConfig 应用成功")
        
        result = speech_recognizer.recognize_once_async().get()
        print(f"识别结果: {result}")
        
        pronunciation_result = json.loads(result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult))
        print("JSON 结果解析成功")

        return pronunciation_result
    except Exception as e:
        print(f"在 pronunciation_assessment 函数中捕获到异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise  # 重新抛出异常，以便在 main 函数中捕获

# Function to create error statistics table
def create_error_table(pronunciation_result):
    error_types = {
        '省略 (Omission)': 0,                 # Omission
        '挿入 (Insertion)': 0,                # Insertion
        '発音ミス (Mispronunciation)': 0,     # Mispronunciation
        '不適切な間 (UnexpectedBreak)': 0,    # UnexpectedBreak
        '間の欠如 (MissingBreak)': 0,         # MissingBreak
        '単調 (Monoton)': 0                  # Monoton
    }
    
    words = pronunciation_result['NBest'][0]['Words']
    for word in words:
        if 'PronunciationAssessment' in word and 'ErrorType' in word['PronunciationAssessment']:
            error_type = word['PronunciationAssessment']['ErrorType']
            if error_type == 'Omission':
                error_types['省略 (Omission)'] += 1
            elif error_type == 'Insertion':
                error_types['挿入 (Insertion)'] += 1
            elif error_type == 'Mispronunciation':
                error_types['発音ミス (Mispronunciation)'] += 1
            elif error_type == 'UnexpectedBreak':
                error_types['不適切な間 (UnexpectedBreak)'] += 1
            elif error_type == 'MissingBreak':
                error_types['間の欠如 (MissingBreak)'] += 1
            elif error_type == 'Monoton':
                error_types['単調 (Monoton)'] += 1
    
    # 创建 DataFrame
    df = pd.DataFrame(list(error_types.items()), columns=['エラータイプ', '回数'])
    
    print(df)
    return df

def creat_syllable_table(pronunciation_result):
    output = """
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid black; padding: 8px; text-align: left; }
        th { background-color: #00008B; }
    </style>
    <table>
        <tr><th>Word</th><th>Pronunciation</th><th>Score</th></tr>
    """
    for word in pronunciation_result['NBest'][0]['Words']:
        word_text = word['Word']
        accuracy_score = word.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
        color = get_color(accuracy_score)
        
        output += f"<tr><td>{word_text}</td><td>"
        
        if 'Phonemes' in word:
            for phoneme in word['Phonemes']:
                phoneme_text = phoneme['Phoneme']
                phoneme_score = phoneme.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
                phoneme_color = get_color(phoneme_score)
                output += f"<span style='color: {phoneme_color};'>{phoneme_text}</span>"
        else:
            output += word_text
        
        output += f"</td><td style='background-color: {color};'>{accuracy_score:.2f}</td></tr>"
    
    output += "</table>"
    return output

# Function to respond to chatbot
def ai_respond(message, chat_history):
        global model
        bot_message = model.generate_content(message).text
        # chat_history contains all the previous messages
        chat_history.append((message, bot_message))
        time.sleep(0.5)
        return "", chat_history

def main(audio_file, reference_text):
    # resample the audio to 16kHz
    y, sr = librosa.load(audio_file, sr=16000)
    # save the resampled audio
    new_audio_file = 'resampled_audio.wav'
    sf.write(new_audio_file, y, sr)
    os.unlink(audio_file)
    try:
        # Perform pronunciation assessment using Azure Speech Service
        pronunciation_result = pronunciation_assessment(new_audio_file, reference_text)
        print(pronunciation_result)
        
        overall_score = pronunciation_result['NBest'][0]['PronunciationAssessment']
        print(f"Overall Score: {overall_score}")

        radar_chart = create_radar_chart(pronunciation_result)
        waveform_plot = create_waveform_plot(new_audio_file, pronunciation_result)
        error_table = create_error_table(pronunciation_result)
        syllable_table_output = creat_syllable_table(pronunciation_result)
        avatar_video = generate_avatar_video(reference_text)
 
        return radar_chart, waveform_plot, error_table, syllable_table_output, avatar_video
    except Exception as e:
        error_message = f"エラーが発生しました: {str(e)}\n"
        error_message += "音声ファイルの処理中に問題が発生した可能性があります。もう一度試すか、別の音声ファイルを使用してください。"
        return None, None, None, None, None
    finally:
        # DON'T FORGET! delete the resampled audio file
        if os.path.exists(new_audio_file):
            os.unlink(new_audio_file)

with gr.Blocks(title="エコー英語学習システム") as demo:
    gr.Markdown("# エコー英語学習システム")
    gr.Markdown("音声をアップロードするか、マイクで録音して発音を評価します。")
    
    with gr.Row():
        input_text = gr.Textbox("Hello, I am Echo English Trainer. How can I help you?", interactive=True, label="勉強しよう！")
        audio_input = gr.Audio(sources=["microphone", 'upload'], type="filepath", label="音声入力")
        submit_btn = gr.Button("学習開始！")
    with gr.Row():
        avatar_video = gr.Video(label="Generated Avatar Video")
    with gr.Row():
        chatbot = gr.Chatbot(label="英語学習コンサルタント")
    with gr.Row():
        with gr.Column(scale=2):
            msg = gr.Textbox(label="質問欄")
        with gr.Column(scale=1):
            clear = gr.ClearButton([msg, chatbot], value='チャットをリセット')
        msg.submit(ai_respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

    with gr.Row():
        with gr.Column(scale=1): 
            radar_chart_output = gr.Plot(label="レーダーチャート")
        with gr.Column(scale=2): 
            waveform_plot_output = gr.Plot(label="波形プロット")
    
    with gr.Row():
        error_table_output = gr.DataFrame(
            label="エラー統計",
            headers=['エラータイプ', '回数'],
            col_count=(2, "fixed"),
            type="pandas"
        )
    with gr.Row():
        syllable_table_output = gr.HTML(
            label="音節スコア"
        )
    
    submit_btn.click(
        fn=main,
        inputs=[audio_input, input_text],
        outputs=[radar_chart_output, waveform_plot_output, error_table_output, syllable_table_output, avatar_video]
    )

demo.launch(share=True)