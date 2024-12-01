import io
import os
import json
import librosa
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import soundfile as sf
import azure.cognitiveservices.speech as speechsdk
from audio_recorder_streamlit import audio_recorder
from streamlit_extras.grid import grid as extras_grid
from dataset import Dataset
from datetime import datetime
import traceback
from streamlit_extras.let_it_rain import rain
from streamlit_extras.image_coordinates import streamlit_image_coordinates

import sys
import os
# Ensure the tools directory is in the Python path
sys.path.append(os.path.abspath("app/tools"))	

# Initialize global variables for storing radar chart per attempt and error types
plt.rcParams["font.family"] = "MS Gothic"


def get_color(score):
    """
    Convert score to a continuous heatmap color
    Args:
        score (float): Score value between 0-100
    Returns:
        str: Color in hex format
    """
    # Ensure score is between 0-100
    score = np.clip(score, 0, 100)
    
    # Normalize score to 0-1 range
    normalized_score = score / 100.0
    
    # Use RdYlGn colormap (Red-Yellow-Green)
    cmap = plt.cm.RdYlGn
    
    # Get RGB color values 
    rgb = cmap(normalized_score)
    
    # Convert RGB to hex format (exclude alpha channel)
    hex_color = '#{:02x}{:02x}{:02x}'.format(
        int(rgb[0]*255),
        int(rgb[1]*255),
        int(rgb[2]*255)
    )
    
    return hex_color


# Function to create radar chart
def create_radar_chart(pronunciation_result):
    overall_assessment = pronunciation_result["NBest"][0]["PronunciationAssessment"]

    categories = {
        "正確性スコア": "AccuracyScore",
        "流暢性スコア": "FluencyScore",
        "完全性スコア": "CompletenessScore",
        "発音スコア": "PronScore",
    }

    scores = [overall_assessment.get(categories[cat], 0) for cat in categories]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection="polar"))

    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
    scores += scores[:1]  # repeat the first value to close the polygon
    angles += angles[:1]

    ax.plot(angles, scores, linewidth=1, linestyle="solid")
    ax.fill(angles, scores, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories.keys())
    ax.set_ylim(0, 100)

    plt.title("発音評価のレーダーチャート")

    return fig

def create_waveform_plot(audio_file, pronunciation_result):
    y, sr = librosa.load(audio_file)
    duration = len(y) / sr

    fig, ax = plt.subplots(figsize=(12, 6))
    times = np.linspace(0, duration, num=len(y))

    ax.plot(times, y, color="gray", alpha=0.5)

    words = pronunciation_result["NBest"][0]["Words"]
    for word in words:
        if (
            "PronunciationAssessment" not in word
            or "ErrorType" not in word["PronunciationAssessment"]
        ):
            continue
        if word["PronunciationAssessment"]["ErrorType"] == "Omission":
            continue

        start_time = word["Offset"] / 10000000
        word_duration = word["Duration"] / 10000000
        end_time = start_time + word_duration

        start_idx = int(start_time * sr)
        end_idx = int(end_time * sr)
        word_y = y[start_idx:end_idx]
        word_times = times[start_idx:end_idx]

        score = word["PronunciationAssessment"].get("AccuracyScore", 0)
        color = get_color(score)

        ax.plot(word_times, word_y, color=color)
        ax.text(
            (start_time + end_time) / 2,
            ax.get_ylim()[0],
            word["Word"],
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=45,
        )
        ax.axvline(x=start_time, color="gray", linestyle="--", alpha=0.5)

        if "Phonemes" in word:
            for phoneme in word["Phonemes"]:
                phoneme_start = phoneme["Offset"] / 10000000
                phoneme_duration = phoneme["Duration"] / 10000000
                phoneme_end = phoneme_start + phoneme_duration

                phoneme_score = phoneme["PronunciationAssessment"].get(
                    "AccuracyScore", 0
                )
                phoneme_color = get_color(phoneme_score)

                # 绘制音节的垂直线
                # ax.axvline(x=phoneme_start, color='black', linestyle='--', alpha=0.5)
                # ax.axvline(x=phoneme_end, color='black', linestyle='--', alpha=0.5)

                # 添加音节 Phoneme 标签
                ax.text(
                    phoneme_start,
                    ax.get_ylim()[1],
                    phoneme["Phoneme"],
                    ha="left",
                    va="top",
                    fontsize=6,
                    color=phoneme_color,
                )
        ax.axvline(x=end_time, color="gray", linestyle="--", alpha=0.5)

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Amplitude")
    ax.set_title("音声の波形と発音評価")
    plt.tight_layout()

    return fig

def pronunciation_assessment(audio_file, reference_text):
    print("進入 pronunciation_assessment 関数")

    # Be Aware!!! We are using free keys here but nonfree keys in Avatar
    speech_key, service_region = (
        st.secrets["Azure_Speech"]["SPEECH_KEY"],
        st.secrets["Azure_Speech"]["SPEECH_REGION"],
    )
    print(f"SPEECH_KEY: {speech_key}, SPEECH_REGION: {service_region}")

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=service_region
    )
    print("SpeechConfig 作成成功")

    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    print("AudioConfig 作成成功")

    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True,
    )
    print("PronunciationAssessmentConfig 作成成功")

    try:
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )
        print("SpeechRecognizer 作成成功")

        pronunciation_config.apply_to(speech_recognizer)
        print("PronunciationConfig 適用成功")

        result = speech_recognizer.recognize_once_async().get()
        print(f"識別結果: {result}")

        pronunciation_result = json.loads(
            result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
        )
        print("JSON 結果解析成功")

        return pronunciation_result
    except Exception as e:
        st.error(f"pronunciation_assessment 関数で例外をキャッチしました: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        raise

def main():
    if st.session_state.user is None:
        st.warning("No user is logined! Something wrong happened!")
    # reset the ai_intial_input to None for state control    
    st.session_state.ai_initial_input = None    
    user = st.session_state.user
    dataset = Dataset(user.name)
    dataset.load_data()

    st.title("エコー英語学習システム😆")
    # the layout of the grid structure
    my_grid = extras_grid(1, [0.2, 0.8], 1, [0.3, 0.7], 1, 1, vertical_align="center")
    # when using my_grid, we need the help of st to avoid wrong layout
    # we could load only some rows of my_grid, which is a useful trick

    # row1: selectbox and blank
    # TODO: should make the selectionbox more efficient
    @st.fragment
    def learning_header():
        selection = my_grid.selectbox(
        "レッソンを選ぶ", ["レッソン1", "レッソン2", "レッソン3"]
        )
        if selection == "レッソン1":
            selected_lessons = {
                "text": dataset.text_data[0],
                "video": dataset.video_data[0],
            }
        elif selection == "レッソン2":
            selected_lessons = {
                "text": dataset.text_data[1],
                "video": dataset.video_data[1],
            }
        elif selection == "レッソン3":
            selected_lessons = {
                "text": dataset.text_data[2],
                "video": dataset.video_data[2],
            }
            
with st.spinner("ロード中..."):
    main()
