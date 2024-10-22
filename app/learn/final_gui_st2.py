import io
import os
import json
import librosa
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import google.generativeai as genai
import soundfile as sf
import azure.cognitiveservices.speech as speechsdk
from audio_recorder_streamlit import audio_recorder
from streamlit_extras.grid import grid as extras_grid
from user import User
from dataset import Dataset
from datetime import date
from datetime import datetime
import traceback

import sys
import os

# Ensure the tools directory is in the Python path
sys.path.append(os.path.abspath("app/tools"))

# Initialize global variables for storing radar chart per attempt and error types
plt.rcParams["font.family"] = "MS Gothic"

# Obtain your API key from the Google AI Studio
genai.configure(api_key=st.secrets["Gemini"]["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-pro")

# Function to get color based on score
def get_color(score):
    if score >= 90:
        # green
        return "#00ff00"
    elif score >= 75:
        # yellow
        return "#ffff00"
    elif score >= 50:
        # orange
        return "#ffa500"
    else:
        # red
        return "#ff0000"

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


# Function to create error statistics table
def create_error_table(pronunciation_result):
    error_types = {
        "省略 (Omission)": 0,  # Omission
        "挿入 (Insertion)": 0,  # Insertion
        "発音ミス (Mispronunciation)": 0,  # Mispronunciation
        "不適切な間 (UnexpectedBreak)": 0,  # UnexpectedBreak
        "間の欠如 (MissingBreak)": 0,  # MissingBreak
        "単調 (Monoton)": 0,  # Monoton
    }

    words = pronunciation_result["NBest"][0]["Words"]
    for word in words:
        if (
            "PronunciationAssessment" in word
            and "ErrorType" in word["PronunciationAssessment"]
        ):
            error_type = word["PronunciationAssessment"]["ErrorType"]
            if error_type == "Omission":
                error_types["省略 (Omission)"] += 1
            elif error_type == "Insertion":
                error_types["挿入 (Insertion)"] += 1
            elif error_type == "Mispronunciation":
                error_types["発音ミス (Mispronunciation)"] += 1
            elif error_type == "UnexpectedBreak":
                error_types["不適切な間 (UnexpectedBreak)"] += 1
            elif error_type == "MissingBreak":
                error_types["間の欠如 (MissingBreak)"] += 1
            elif error_type == "Monoton":
                error_types["単調 (Monotone)"] += 1

    # Create DataFrame
    df = pd.DataFrame(list(error_types.items()), columns=["エラータイプ", "回数"])
    return df


def create_syllable_table(pronunciation_result):
    output = """
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid black; padding: 8px; text-align: left; }
        th { background-color: #00008B; }
    </style>
    <table>
        <tr><th>Word</th><th>Pronunciation</th><th>Score</th></tr>
    """
    for word in pronunciation_result["NBest"][0]["Words"]:
        word_text = word["Word"]
        accuracy_score = word.get("PronunciationAssessment", {}).get("AccuracyScore", 0)
        color = get_color(accuracy_score)

        output += f"<tr><td>{word_text}</td><td>"

        if "Phonemes" in word:
            for phoneme in word["Phonemes"]:
                phoneme_text = phoneme["Phoneme"]
                phoneme_score = phoneme.get("PronunciationAssessment", {}).get(
                    "AccuracyScore", 0
                )
                phoneme_color = get_color(phoneme_score)
                output += f"<span style='color: {phoneme_color};'>{phoneme_text}</span>"
        else:
            output += word_text

        output += f"</td><td style='background-color: {color};'>{accuracy_score:.2f}</td></tr>"

    output += "</table>"
    return output

# Function to respond to chatbot
def ai_respond(message, chat_history):
    bot_message = model.generate_content(message).text
    chat_history.append((message, bot_message))
    time.sleep(0.5)
    return chat_history

def get_audio_from_mic(user, selection) -> str:
    # record audio from mic and save it to a wav file, and return the name of the file
    sample_rate = 16000

    # user is an obj of User and selection is the name of selected lession
    def save_audio_bytes_to_wav(
        audio_bytes, output_filename, sample_rate=sample_rate, channels=1
    ):
        # Convert audio_bytes to a numpy array
        audio_data, sr = sf.read(io.BytesIO(audio_bytes), dtype="int16")
        # Save the numpy array to a .wav file
        sf.write(
            output_filename, audio_data, sample_rate, format="WAV", subtype="PCM_16"
        )

    # collect voice bytes data from audio_recorder
    audio_bytes = audio_recorder(
        text="クリックして録音", neutral_color="#e6ff33", sample_rate=16000
    )
    if audio_bytes:
        # save audio_bytes to a file
        st.audio(audio_bytes)
        # save io.BytesIO obj into a file whose name is date_time.now()
        # save the wav in a mono channel for Azure pronunciation assessment
        file_name = f"{user.today_path}/{selection}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"
        save_audio_bytes_to_wav(audio_bytes, file_name, sample_rate, channels=1)
        
        return file_name

# layout of learning page
def main():
    if st.session_state.user is None:
        st.warning("No user is logined! Something wrong happened!")
    user = st.session_state.user
    dataset = Dataset(user.name)
    dataset.load_data()

    st.title("エコー英語学習システム")
    # the layout of the grid structure
    my_grid = extras_grid(1, [0.2, 0.8], [0.3, 0.4], 2, 1, 1, vertical_align="bottom")
    # when using my_grid, we need the help of st to avoid wrong layout

    # row1: selectbox and blank
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

    # row2: video, text
    my_grid.video(dataset.path + selected_lessons["video"])
    with open(dataset.path + selected_lessons["text"], "r") as f:
        text_content = f.read()
    # TODO: how to set the font and size?
    my_grid.markdown(dataset.path + text_content)

    # row3: mic and learning button
    # main working
    # initialize all the elements with None
    overall_score = radar_chart = waveform_plot = error_table = syllable_table = None
    with my_grid.container(border=True):
        audio_file_name = get_audio_from_mic(user, selection)
    with my_grid.container(border=True):
        if st.button("学習開始！", use_container_width=True) and audio_file_name:
            try:
                pronunciation_result = pronunciation_assessment(
                    audio_file=audio_file_name, reference_text=text_content
                )
                # save the pronunciation_result to disk
                user.save_pron_history(selection, pronunciation_result)

                overall_score = pronunciation_result["NBest"][0][
                    "PronunciationAssessment"
                ]
                radar_chart = create_radar_chart(pronunciation_result)
                waveform_plot = create_waveform_plot(
                    audio_file_name, pronunciation_result
                )
                error_table = create_error_table(pronunciation_result)
                syllable_table = create_syllable_table(pronunciation_result)
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.error(
                    "音声ファイルの処理中に問題が発生した可能性があります。もう一度試すか、別の音声ファイルを使用してください。"
                )
                print(traceback.format_exc())
    # row4: radar chart and errors' type
    # TODO: is it to initialize all the elements with None
    if radar_chart:
        my_grid.pyplot(radar_chart)
    if error_table is not None:
        my_grid.dataframe(error_table)

    # row5: waveform
    if waveform_plot:
        my_grid.pyplot(waveform_plot)

    # row6: summarization of syllable mistakes and feedback of AI
    if syllable_table:
        my_grid.markdown(syllable_table, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
main()
