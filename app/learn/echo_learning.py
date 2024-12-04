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
import altair as alt

import sys
import os

# Ensure the tools directory is in the Python path
sys.path.append(os.path.abspath("app/tools"))	

# Initialize global variables for storing radar chart per attempt and error types
plt.rcParams["font.family"] = "MS Gothic"

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
        "省略 (Omission)": {'回数': 0, '単語': []},  # Omission
        "挿入 (Insertion)": {'回数': 0, '単語': []},  # Insertion
        "発音ミス (Mispronunciation)": {'回数': 0, '単語': []},  # Mispronunciation
        "不適切な間 (UnexpectedBreak)": {'回数': 0, '単語': []},  # UnexpectedBreak
        "間の欠如 (MissingBreak)": {'回数': 0, '単語': []},  # MissingBreak
        "単調 (Monotone)": {'回数': 0, '単語': []},  # Monotone
    }

    words = pronunciation_result["NBest"][0]["Words"]
    for word in words:
        if (
            "PronunciationAssessment" in word
            and "ErrorType" in word["PronunciationAssessment"]
        ):
            error_type = word["PronunciationAssessment"]["ErrorType"]
            if error_type == "Omission":
                error_types["省略 (Omission)"]["回数"] += 1
                error_types["省略 (Omission)"]["単語"].append(word["Word"])
            elif error_type == "Insertion":
                error_types["挿入 (Insertion)"]["回数"] += 1
                error_types["挿入 (Insertion)"]["単語"].append(word["Word"])
            elif error_type == "Mispronunciation":
                error_types["発音ミス (Mispronunciation)"]["回数"] += 1
                error_types["発音ミス (Mispronunciation)"]["単語"].append(word["Word"])
            elif error_type == "UnexpectedBreak":
                error_types["不適切な間 (UnexpectedBreak)"]["回数"] += 1
                error_types["不適切な間 (UnexpectedBreak)"]["単語"].append(word["Word"])
            elif error_type == "MissingBreak":
                error_types["間の欠如 (MissingBreak)"]["回数"] += 1
                error_types["間の欠如 (MissingBreak)"]["単語"].append(word["Word"])
            elif error_type == "Monoton":
                error_types["単調 (Monotone)"]["回数"] += 1
                error_types["単調 (Monotone)"]["単語"].append(word["Word"])

    # Create DataFrame
    df = pd.DataFrame.from_dict(error_types, orient='index')
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
        print("audio has been saved!")

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

def save_audio_bytes_to_wav(user, audio_bytes, selection, sample_rate=48000, channels=1):
    audio_data, sr = sf.read(audio_bytes, dtype="int16")
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_filename = f"{user.today_path}/{selection}-{current_time}.wav"
    sf.write(output_filename, audio_data, sample_rate, format="WAV", subtype="PCM_16")
    print("Audio saved!")
    return output_filename

def get_audio_from_mic_v2(user, selection):
    # Collect voice bytes data from audio_recorder
    audio_bytes_io = st.audio_input("マイクのアイコンをクリックして、録音しましょう！")
    if audio_bytes_io:
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        # Generate filename for new recording
        file_name = f"{user.today_path}/{selection}-{current_time}.wav"
        # Save new audio
        return audio_bytes_io
    return None

def course_navigation(my_grid, courses):
    # my_grid is the grid element of streamlit_exras
    # Initialize session state for course index
    if 'lesson_index' not in st.session_state:
        st.session_state.lesson_index = 0
    user = st.session_state.user
    # Previous button
    if my_grid.button("◀ 前", disabled=st.session_state.lesson_index == 0, use_container_width=True):
        st.session_state.lesson_index -= 1
        user.load_scores_history(st.session_state.lesson_index)
        st.rerun()
            
    # Next button
    if my_grid.button("次 ▶", disabled=st.session_state.lesson_index == len(courses) - 1, use_container_width=True):
        st.session_state.lesson_index += 1
        user.load_scores_history(st.session_state.lesson_index)
        st.rerun()
            
    # Show current course name
    current_course = courses[st.session_state.lesson_index]
    my_grid.info(f"現在: {current_course}")
        
    return current_course

def save_scores_to_json(user, lesson_index, scores_history):
    scores_dir = os.path.join(user.today_path, "scores")
    if not os.path.exists(scores_dir):
        os.makedirs(scores_dir)
    
    json_file = os.path.join(scores_dir, "lesson_scores.json")
    
    # Load existing data
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            all_scores = json.load(f)
    else:
        all_scores = {}
    
    lesson_key = f"lesson_{lesson_index}"
    
    # If lesson exists, append new scores to existing lists
    if lesson_key in all_scores:
        all_scores[lesson_key]['AccuracyScore'].extend(scores_history['AccuracyScore'])
        all_scores[lesson_key]['FluencyScore'].extend(scores_history['FluencyScore'])  
        all_scores[lesson_key]['CompletenessScore'].extend(scores_history['CompletenessScore'])
        all_scores[lesson_key]['PronScore'].extend(scores_history['PronScore'])
    else:
        # Create new entry for lesson
        all_scores[lesson_key] = {
            'AccuracyScore': scores_history['AccuracyScore'],
            'FluencyScore': scores_history['FluencyScore'],
            'CompletenessScore': scores_history['CompletenessScore'],
            'PronScore': scores_history['PronScore']
        }
    
    # Save updated data
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_scores, f, indent=4)

def store_scores(user, lesson_index, pronunciation_result):
    # Initialize scores history if not exists
    if 'scores_history' not in st.session_state:
        st.session_state.scores_history = {}
    
    # Initialize current lesson if not exists
    if lesson_index not in st.session_state.scores_history:
        st.session_state.scores_history[lesson_index] = {
            'AccuracyScore': [],
            'FluencyScore': [],
            'CompletenessScore': [],
            'PronScore': []
        }
    
    # Add new scores
    scores = pronunciation_result["NBest"][0]["PronunciationAssessment"]
    st.session_state.scores_history[lesson_index]['AccuracyScore'].append(scores['AccuracyScore'])
    st.session_state.scores_history[lesson_index]['FluencyScore'].append(scores['FluencyScore'])
    st.session_state.scores_history[lesson_index]['CompletenessScore'].append(scores['CompletenessScore'])
    st.session_state.scores_history[lesson_index]['PronScore'].append(scores['PronScore'])

    save_scores_to_json(user, lesson_index, st.session_state.scores_history[lesson_index])

def plot_overall_score(data):
    """Plot overall pronunciation score"""
    # Calculate y-axis range
    y_min_pron = max(0, data['PronScore'].min() - 5)
    y_max_pron = min(100, data['PronScore'].max() + 5)
    
    chart = alt.Chart(data).mark_line(
        color='#FF4B4B',
        point=True
    ).encode(
        x=alt.X('Attempt:Q',
                axis=alt.Axis(
                    tickMinStep=1,
                    title='練習回数',
                    values=list(range(1, 11)),
                    tickCount=10,
                    format='d',
                    grid=True
                ),
                scale=alt.Scale(domain=[1, 10])
        ),
        y=alt.Y('PronScore:Q',
                title='スコア',
                scale=alt.Scale(domain=[y_min_pron, y_max_pron])),
        tooltip=['Attempt', 'PronScore']
    ).properties(
        title='総合点スコア',
        width="container",
        height=300
    ).interactive()
    
    return chart

def plot_detail_scores(data):
    """Plot detailed scores components"""
    # Prepare data
    metrics = ['AccuracyScore', 'FluencyScore', 'CompletenessScore']
    detail_data = data.melt(
        id_vars=['Attempt'],
        value_vars=metrics,
        var_name='Metric',
        value_name='Score'
    )
    
    # Calculate y-axis range
    y_min_detail = max(0, min(data[metrics].min()) - 5)
    y_max_detail = min(100, max(data[metrics].max()) + 5)
    
    chart = alt.Chart(detail_data).mark_line(
        point=True
    ).encode(
        x=alt.X('Attempt:Q',
                axis=alt.Axis(
                    tickMinStep=1,
                    title='練習回数',
                    values=list(range(1, 11)),
                    tickCount=10,
                    format='d',
                    grid=True
                ),
                scale=alt.Scale(domain=[1, 10])
        ),
        y=alt.Y('Score:Q',
                title='スコア',
                scale=alt.Scale(domain=[y_min_detail, y_max_detail])),
        color=alt.Color('Metric:N',
                       scale=alt.Scale(
                           range=['#00C957', '#4169E1', '#FFD700']
                       ),
                       legend=alt.Legend(
                           title='評価指標',
                           orient='right'
                       )),
        tooltip=['Attempt', 'Score', 'Metric']
    ).properties(
        title='詳細スコア',
        width="container",
        height=300
    ).interactive()
    
    return chart

def plot_score_history():
    if 'scores_history' not in st.session_state:
        st.warning("まだ学習記録がありません")
        return
    
    lesson_index = st.session_state.lesson_index
    
    if lesson_index not in st.session_state.scores_history:
        st.warning(f"レッスン {lesson_index + 1} の記録がありません")
        return
    
    # Check if data exists
    scores = st.session_state.scores_history[lesson_index]
    if not any(scores.values()):  # Check if all score lists are empty
        st.warning("まだ学習記録がありません")
        return
        
    # Create DataFrame only if we have data
    data = pd.DataFrame(scores)
    if len(data) == 0:
        st.warning("まだ学習記録がありません")
        return
        
    data['Attempt'] = range(1, len(data) + 1)
    
    # Create two columns for charts
    col1, col2 = st.columns([2, 3])
    
    # Plot charts in columns
    with col1:
        overall_chart = plot_overall_score(data)
        st.altair_chart(overall_chart, use_container_width=True)
        
    with col2:
        detail_chart = plot_detail_scores(data)
        st.altair_chart(detail_chart, use_container_width=True)

# layout of learning page
def main():
    if st.session_state.user is None:
        st.warning("No user is logined! Something wrong happened!")
    # reset the ai_intial_input to None for state control    
    st.session_state.ai_initial_input = None    
    user = st.session_state.user
    if 'dataset' not in st.session_state:
        dataset = Dataset(user.name)
        dataset.load_data()
        st.session_state.dataset = dataset
    dataset = st.session_state.dataset
    lessons = [f'レッソン{i}' for i in range(1, len(dataset.text_data) + 1)]
    
    # preload the scores history
    if 'scores_history' not in st.session_state:
        for i in range(len(lessons)):
            user.load_scores_history(i)

    st.title("エコー英語学習システム😆")
    
    # set the names of tabs
    tab1, tab2 = st.tabs(['ラーニング', 'まとめ'])
    with tab1:
        # the layout of the grid structure
        my_grid = extras_grid([0.1, 0.1, 0.8], [0.2, 0.8], 1,  [0.3, 0.7], 1, 1, vertical_align="center")
        # when using my_grid, we need the help of st to avoid wrong layout
        # we could load only some rows of my_grid, which is a useful trick

        # row1: selectbox and blank
        selection = course_navigation(my_grid, lessons)
        # selection = my_grid.selectbox(
        #     "レッソンを選びましょう！", ["レッソン1", "レッソン2", "レッソン3"]
        # )
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
        with open(dataset.path + selected_lessons["text"], "r", encoding='utf-8') as f:
            text_content = f.read()
        # TODO: how to set the font and size?
        my_grid.markdown(
            f"""
            <div style="text-align: left; font-size: 24px; font-weight: bold; color: #F0F0F0;">
                {text_content}
            </div>
            """,
            unsafe_allow_html=True
        )

        # row3: mic and learning button
        # main work will be done here
        # initialize all the elements with None for convenience
        overall_score = radar_chart = waveform_plot = error_table = syllable_table = None
        
        # using form here!
        with my_grid.form(key='learning_phase'):
            audio_file_io = get_audio_from_mic_v2(user, selection)
            if_started = st.form_submit_button('学習開始！')
        if if_started:
            # if overall_score and all the other are all None, don't run this
            # save the audio when the submit button is clicked
            audio_file_name = save_audio_bytes_to_wav(user, audio_file_io, selection)
            if audio_file_name and not overall_score:
                try:
                    pronunciation_result = pronunciation_assessment(
                        audio_file=audio_file_name, reference_text=text_content
                    )
                    # save the pronunciation_result to disk
                    user.save_pron_history(selection, pronunciation_result)

                    overall_score = pronunciation_result["NBest"][0][
                        "PronunciationAssessment"
                    ]
                    # store the pronunciation results into sesstion_state
                    store_scores(user, st.session_state.lesson_index, pronunciation_result)
                    radar_chart = create_radar_chart(pronunciation_result)
                    waveform_plot = create_waveform_plot(
                        audio_file_name, pronunciation_result
                    )
                    error_table = create_error_table(pronunciation_result)
                    syllable_table = create_syllable_table(pronunciation_result)
                    
                    st.session_state['learning_data']['overall_score'] = overall_score
                    st.session_state['learning_data']['radar_chart'] = radar_chart
                    st.session_state['learning_data']['waveform_plot'] = waveform_plot
                    st.session_state['learning_data']['error_table'] = error_table
                    st.session_state['learning_data']['syllable_table'] = syllable_table
                    # the data sent to ai as initial input
                    st.session_state['ai_initial_input'] = error_table
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
                    st.error(
                        "音声ファイルの処理中に問題が発生した可能性があります。もう一度試すか、別の音声ファイルを使用してください。"
                    )
                    print(traceback.format_exc())
        # row4: radar chart and errors' type
        if st.session_state['learning_data']['radar_chart']:
            my_grid.pyplot(st.session_state['learning_data']['radar_chart'])
        if st.session_state['learning_data']['error_table'] is not None:
            my_grid.dataframe(st.session_state['learning_data']['error_table'], use_container_width=True)
        # row5: waveform
        if st.session_state['learning_data']['waveform_plot']:
            my_grid.pyplot(st.session_state['learning_data']['waveform_plot'])
        # row6: summarization of syllable mistakes and feedback of AI
        if st.session_state['learning_data']['syllable_table']:
            my_grid.markdown(st.session_state['learning_data']['syllable_table'], unsafe_allow_html=True)
        
        # if overall score is higher than 80, rain the balloons
        if overall_score and overall_score['PronScore'] >= 80:
            rain(
            emoji="🥳🎉",
            font_size=54,
            falling_speed=5,
            animation_length=10
        )
    
    with tab2:
        progress_plot = plot_score_history()
        if progress_plot:
            st.pyplot(progress_plot)
main()
