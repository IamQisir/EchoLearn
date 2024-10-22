import io
import os
import base64
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
from streamlit_extras.row import row as extras_row

import sys
import os
# Ensure the tools directory is in the Python path
sys.path.append(os.path.abspath('app/tools'))

# Correct the import statement
# from avatar_synthesis import generate_avatar_video


# Initialize global variables for storing radar chart per attempt and error types
plt.rcParams["font.family"] = "MS Gothic"

# Obtain your API key from the Google AI Studio
genai.configure(api_key=st.secrets['Gemini']['GOOGLE_API_KEY'])
model = genai.GenerativeModel("gemini-pro")


# Function to get color based on score
def get_color(score):
    if score >= 90:
        return "#00ff00"
    elif score >= 75:
        return "#ffff00"
    elif score >= 50:
        return "#ffa500"
    else:
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

                phoneme_score = phoneme["PronunciationAssessment"].get("AccuracyScore", 0)
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
                    color = phoneme_color
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
    speech_key, service_region = st.secrets['Azure_Speech']['SPEECH_KEY'], st.secrets['Azure_Speech']['SPEECH_REGION']
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
                error_types["単調 (Monoton)"] += 1

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

# TODO: get_audio_from_mic
def get_audio_from_mic():
    audio_bytes = audio_recorder(neutral_color="#e6ff33", sample_rate=16000)
    return None

# page layout
def main():
    st.title("エコー英語学習システム")
    # TODO: Doing!
    # row1 = extras_row([0.4, 0.4, 0.2])
    # row1.video()

    st.markdown("音声をアップロードするか、マイクで録音して発音を評価します。")

    input_text = st.text_input(
        "勉強しよう！", "Hello, I am Echo English Trainer. How can I help you?"
    )
    audio_file = st.file_uploader("音声入力", type=["wav", "mp3"])

    if st.button("学習開始！"):
        if audio_file is not None:
            # Save uploaded file temporarily
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_file.getvalue())

            try:
                # Resample the audio to 16kHz
                y, sr = librosa.load("temp_audio.wav", sr=16000)
                sf.write("resampled_audio.wav", y, sr)

                # Perform pronunciation assessment
                pronunciation_result = pronunciation_assessment(
                    "resampled_audio.wav", input_text
                )
                # TODO: save this result to file
                # st.write(pronunciation_result)

                overall_score = pronunciation_result["NBest"][0][
                    "PronunciationAssessment"
                ]

                # Create and display radar chart
                radar_chart = create_radar_chart(pronunciation_result)
                st.pyplot(radar_chart)

                # Create and display waveform plot
                waveform_plot = create_waveform_plot(
                    "resampled_audio.wav", pronunciation_result
                )
                st.pyplot(waveform_plot)

                # Create and display error table
                error_table = create_error_table(pronunciation_result)
                st.dataframe(error_table)

                # Create and display syllable table
                syllable_table = create_syllable_table(pronunciation_result)
                st.markdown(syllable_table, unsafe_allow_html=True)

                # Generate and display avatar video
                # avatar_video = generate_avatar_video(input_text)
                # st.video(avatar_video)

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.error(
                    "音声ファイルの処理中に問題が発生した可能性があります。もう一度試すか、別の音声ファイルを使用してください。"
                )

            finally:
                # Clean up temporary files
                for file in ["temp_audio.wav", "resampled_audio.wav"]:
                    if os.path.exists(file):
                        os.remove(file)
        else:
            st.warning("音声ファイルをアップロードしてください。")

    # Chat interface
    st.header("英語学習コンサルタント")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        st.text(f"You: {message[0]}")
        st.text(f"AI: {message[1]}")

    user_input = st.text_input("質問欄")
    if st.button("送信"):
        st.session_state.chat_history = ai_respond(
            user_input, st.session_state.chat_history
        )

    if st.button("チャットをリセット"):
        st.session_state.chat_history = []


if __name__ == "__main__":
    main()
main()
