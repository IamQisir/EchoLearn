import azure.cognitiveservices.speech as speechsdk
import json
import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import logging
import os
import librosa
import librosa.display
import tempfile
import soundfile as sf
from collections import defaultdict
import time

attempts = []
error_types = defaultdict(lambda: defaultdict(int))

def get_color(score):
    if score >= 90:
        return '#00ff00'
    elif score >= 75:
        return '#ffff00'
    elif score >= 50:
        return '#ffa500'
    else:
        return '#ff0000'

def create_radar_chart(scores_list: list):
    categories = list(scores_list[0].keys())
    
    fig, ax = plt.subplots(figsize=(6, 4), subplot_kw=dict(projection='polar'))
    
    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
    angles += angles[:1]
    
    for i, scores in enumerate(scores_list):
        values = list(scores.values())
        values += values[:1]
        ax.plot(angles, values, linewidth=1, linestyle='solid', label=f'Attempt {i+1}')
        ax.fill(angles, values, alpha=0.1)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    img_str = base64.b64encode(buf.getvalue()).decode()
    
    plt.close(fig)
    
    return f'<img src="data:image/png;base64,{img_str}" alt="Radar Chart">'

def create_waveform_plot(audio, words):
    if isinstance(audio, str):
        y, sr = librosa.load(audio)
    else:
        sr, y = audio
    
    duration = len(y) / sr
    
    fig, ax = plt.subplots(figsize=(12, 4))
    times = np.linspace(0, duration, num=len(y))
    
    # 绘制基础波形
    ax.plot(times, y, color='gray', alpha=0.5)
    
    for word in words:
        if word['PronunciationAssessment']['ErrorType'] == 'Omission':
            continue
        start_time = word['Offset'] / 10000000  # 转换为秒
        word_duration = word['Duration'] / 10000000
        end_time = start_time + word_duration
        
        # 获取这个时间范围内的波形数据
        start_idx = int(start_time * sr)
        end_idx = int(end_time * sr)
        word_y = y[start_idx:end_idx]
        word_times = times[start_idx:end_idx]
        
        # 根据准确度评分获取颜色
        score = word['PronunciationAssessment']['AccuracyScore']
        color = get_color(score)
        
        # 绘制这个单词的波形，使用评分对应的颜色
        ax.plot(word_times, word_y, color=color)
        
        # 添加单词标签
        ax.text((start_time + end_time) / 2, ax.get_ylim()[0], word['Word'], 
                ha='center', va='bottom', fontsize=8, rotation=45)
        
        # 添加垂直分隔线
        ax.axvline(x=start_time, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Waveform with Pronunciation Assessment')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    buf.seek(0)
    
    img_str = base64.b64encode(buf.getvalue()).decode()
    
    plt.close(fig)
    
    return f'<img src="data:image/png;base64,{img_str}" alt="Waveform Plot">'

def analyze_errors(pronunciation_result):
    words = pronunciation_result['NBest'][0]['Words']
    errors = defaultdict(int)
    for word in words:
        error_type = word['PronunciationAssessment']['ErrorType']
        if error_type != 'None':
            errors[error_type] += 1
        if 'Phonemes' in word:
            for phoneme in word['Phonemes']:
                if phoneme['PronunciationAssessment']['AccuracyScore'] < 70:
                    errors['LowAccuracyPhoneme'] += 1
    return dict(errors)

def track_progress(attempts):
    progress = {
        "improved": [],
        "not_improved": [],
        "persistent_errors": []
    }
    if len(attempts) < 2:
        return progress
    
    last = attempts[-1]
    second_last = attempts[-2]
    
    for key in last:
        if last[key] > second_last[key]:
            progress["improved"].append(key)
        elif last[key] < second_last[key]:
            progress["not_improved"].append(key)
        else:
            progress["persistent_errors"].append(key)
    
    return progress

def save_progress(attempts, error_types):
    data = {
        "attempts": attempts,
        "error_types": dict(error_types)
    }
    with open("pronunciation_progress.json", "w") as f:
        json.dump(data, f)

def create_waveform_plot(audio, words):
    if isinstance(audio, str):
        y, sr = librosa.load(audio)
    else:
        sr, y = audio
    
    duration = len(y) / sr
    
    fig, ax = plt.subplots(figsize=(12, 4))
    times = np.linspace(0, duration, num=len(y))
    
    # 绘制基础波形
    ax.plot(times, y, color='gray', alpha=0.5)
    
    for word in words:
        if word['error_type'] == 'Omission':
            ax.axvspan(word['offset']/10000, (word['offset'] + word['duration'])/10000, color='red', alpha=0.3)
        elif word['error_type'] == 'Insertion':
            ax.axvspan(word['offset']/10000, (word['offset'] + word['duration'])/10000, color='yellow', alpha=0.3)
        elif word['error_type'] == 'Substitution':
            ax.axvspan(word['offset']/10000, (word['offset'] + word['duration'])/10000, color='blue', alpha=0.3)
        elif word['error_type'] == 'Deletion':
            ax.axvspan(word['offset']/10000, (word['offset'] + word['duration'])/10000, color='green', alpha=0.3)
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    img_str = base64.b64encode(buf.getvalue()).decode()
    
    plt.close(fig)
    
    return f'<img src="data:image/png;base64,{img_str}" alt="Waveform Plot">'


def create_waveform_plot(audio, words):
    if isinstance(audio, str):
        y, sr = librosa.load(audio)
    else:
        sr, y = audio
    
    duration = len(y) / sr
    
    fig, ax = plt.subplots(figsize=(12, 4))
    times = np.linspace(0, duration, num=len(y))
    
    # 绘制基础波形
    ax.plot(times, y, color='gray', alpha=0.5)
    
    for word in words:
        # 模拟时间跨度，使用索引和持续时间
        start_time = 0
        end_time = (len(y) / len(words)) / sr
        if word['error_type'] == 'Omission':
            ax.axvspan(start_time, end_time, color='red', alpha=0.3)
        elif word['error_type'] == 'Insertion':
            ax.axvspan(start_time, end_time, color='yellow', alpha=0.3)
        elif word['error_type'] == 'Substitution':
            ax.axvspan(start_time, end_time, color='blue', alpha=0.3)
        elif word['error_type'] == 'Deletion':
            ax.axvspan(start_time, end_time, color='green', alpha=0.3)
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    img_str = base64.b64encode(buf.getvalue()).decode()
    
    plt.close(fig)
    
    return f'<img src="data:image/png;base64,{img_str}" alt="Waveform Plot">'

def pronunciation_assessment(audio, reference_text):
    try:
        # Setup the subscription info for the Speech Service:
        speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
        
        # 将音频数据写入临时文件
        sample_rate, audio_data = audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            sf.write(temp_audio_file.name, audio_data, sample_rate)
            audio_path = temp_audio_file.name
        
        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
        
        # Creates a recognizer with the given settings
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        # Get the pronunciation assessment configuration
        pron_config = speechsdk.PronunciationAssessmentConfig(reference_text=reference_text, grading_system=speechsdk.PronunciationAssessmentGradingSystem.FivePoint, granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme, enable_miscue=True)
        pron_config.apply_to(recognizer)
        
        # Recognize speech from the audio file
        result = recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
            
            # 提取可用属性
            accuracy_score = pronunciation_result.accuracy_score
            completeness_score = pronunciation_result.completeness_score
            fluency_score = pronunciation_result.fluency_score
            pronunciation_score = pronunciation_result.pronunciation_score
            prosody_score = pronunciation_result.prosody_score
            
            # 调试信息，打印每个 word 对象的属性
            for word in pronunciation_result.words:
                print(word.word, dir(word))
            
            # 提取 word_scores
            word_scores = {word.word: word.accuracy_score for word in pronunciation_result.words}
            
            # 获取评分
            radar_chart = create_radar_chart([{
                'Accuracy': accuracy_score,
                'Completeness': completeness_score,
                'Fluency': fluency_score,
                'Pronunciation': pronunciation_score,
                'Prosody': prosody_score
            }])
            
            waveform_words = [{'word': word.word, 'accuracy_score': word.accuracy_score, 'error_type': word.error_type} for word in pronunciation_result.words]
            waveform_plot = create_waveform_plot((sample_rate, audio_data), waveform_words)
            
            attempts.append(word_scores)
            
            errors = analyze_errors(pronunciation_result)
            for error_type, count in errors.items():
                error_types[error_type][len(attempts)] = count
            
            progress = track_progress(attempts)
            save_progress(attempts, error_types)
            
            # 删除临时文件
            os.unlink(audio_path)
            
            error_summary = f"<h3>Error Summary (Attempt {len(attempts)}):</h3>"
            for error_type, count in errors.items():
                error_summary += f"<p>{error_type}: {count}</p>"
            
            progress_summary = "<h3>Progress Summary:</h3>"
            for key, items in progress.items():
                progress_summary += f"<p>{key.capitalize()}: {', '.join(items)}</p>"
            
            output = f"<br><strong>Overall Scores (Attempt {len(attempts)}):</strong><br>{radar_chart}"
            output += f"<br><strong>Waveform with Pronunciation Assessment:</strong><br>{waveform_plot}"
            output += f"<br>{error_summary}"
            output += f"<br>{progress_summary}"
        
        else:
            output = f"Speech could not be recognized: {result.reason}"
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return str(e), None, None, None

    return output, radar_chart, waveform_plot, json.dumps(errors, indent=2)


with gr.Blocks() as demo:
    gr.Markdown("# Azure Pronunciation Assessment")
    with gr.Row():
        with gr.Column(scale=2):
            audio_input = gr.Audio(label="Record Audio")
            text_input = gr.Textbox(label="Reference Text", value="Hello, I am open voice. How can I help you?")
            submit_btn = gr.Button("Submit")
        with gr.Column(scale=3):
            output = gr.HTML(label="Assessment Results")
    with gr.Row():
        radar_chart = gr.Plot(label="Score Radar Chart")
        waveform_plot = gr.Plot(label="Waveform Plot")
    with gr.Row():
        error_json = gr.JSON(label="Error Summary")
    
    submit_btn.click(pronunciation_assessment, inputs=[audio_input, text_input], outputs=[output, radar_chart, waveform_plot, error_json])

demo.launch(share=True)