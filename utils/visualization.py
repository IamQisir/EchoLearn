# utils/visualization.py

from typing import Dict, Any
import altair as alt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

def get_color(score: float) -> str:
    """Get color based on score value"""
    if score >= 90:
        return "#00ff00"  # green
    elif score >= 75:
        return "#ffc000"  # yellow
    elif score >= 50:
        return "#ff4b4b"  # orange
    else:
        return "#ff0000"  # red

def create_radar_chart(pronunciation_result: Dict[str, Any]) -> Figure:
    """Create radar chart for pronunciation assessment"""
    # Extract overall assessment
    overall_assessment = pronunciation_result["NBest"][0]["PronunciationAssessment"]

    # Define categories with Japanese labels
    categories = {
        "総合": "PronScore",
        "正確性": "AccuracyScore",
        "流暢性": "FluencyScore",
        "完全性": "CompletenessScore",
        "韻律": "ProsodyScore"
    }

    # Get scores
    scores = [overall_assessment.get(categories[cat], 0) for cat in categories]

    # Create figure and polar axis
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection="polar"))

    # Calculate angles for each category
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)

    # Close the plot by appending first values
    scores += scores[:1]
    angles = np.concatenate((angles, [angles[0]]))

    # Plot data
    ax.plot(angles, scores, 'o-', linewidth=3, color='#2E86C1', markersize=10)
    ax.fill(angles, scores, alpha=0.25, color='#2E86C1')

    # Set chart properties
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories.keys(), size=20)
    
    # Add gridlines
    ax.set_rgrids([20, 40, 60, 80, 100], 
                  labels=['20', '40', '60', '80', '100'],
                  angle=0,
                  fontsize=14)

    # Add score labels
    for angle, score in zip(angles[:-1], scores[:-1]):
        ax.text(angle, score + 5, f'{score:.1f}', 
                ha='center', va='center',
                fontsize=20,
                fontweight='bold')

    # Customize grid
    ax.grid(True, linestyle='--', alpha=0.7, linewidth=1.5)
    
    # Set chart limits and direction
    ax.set_ylim(0, 100)
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2)
    
    # Style
    ax.set_facecolor('#F8F9F9')
    fig.patch.set_facecolor('white')
    plt.title("発音評価レーダーチャート\nPronunciation Assessment Radar Chart", 
              pad=20, size=20, fontweight='bold')

    plt.tight_layout()
    return fig

def create_waveform_plot(audio_file: str, pronunciation_result: Dict[str, Any]) -> Figure:
    """Create waveform plot with pronunciation assessment"""
    import librosa
    y, sr = librosa.load(audio_file)
    duration = len(y) / sr

    fig, ax = plt.subplots(figsize=(12, 6))
    times = np.linspace(0, duration, num=len(y))

    # Plot base waveform
    ax.plot(times, y, color="gray", alpha=0.5)

    # Process each word
    words = pronunciation_result["NBest"][0]["Words"]
    for word in words:
        if ("PronunciationAssessment" not in word or 
            "ErrorType" not in word["PronunciationAssessment"]):
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

        # Color based on accuracy score
        score = word["PronunciationAssessment"].get("AccuracyScore", 0)
        color = get_color(score)

        # Plot word segment
        ax.plot(word_times, word_y, color=color)
        
        # Add word label
        ax.text(
            (start_time + end_time) / 2,
            ax.get_ylim()[0],
            word["Word"],
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=45,
        )
        
        # Add vertical lines
        ax.axvline(x=start_time, color="gray", linestyle="--", alpha=0.5)

        # Process phonemes if available
        if "Phonemes" in word:
            for phoneme in word["Phonemes"]:
                phoneme_start = phoneme["Offset"] / 10000000
                
                # Get phoneme score and color
                phoneme_score = phoneme["PronunciationAssessment"].get("AccuracyScore", 0)
                phoneme_color = get_color(phoneme_score)

                # Add phoneme label
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

def create_doughnut_chart(data: Dict[str, float], title: str) -> alt.Chart:
    """Create a doughnut chart using Altair"""
    # Convert data to DataFrame
    df = pd.DataFrame(list(data.items()), columns=['Error', 'Count'])
    
    return alt.Chart(df).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Count", type="quantitative"),
        color=alt.Color(
            field="Error",
            type="nominal",
            scale=alt.Scale(range=['#FF4B4B', '#FFC000', '#00B050', '#2F75B5', '#7030A0', '#000000'])
        ),
        tooltip=['Error', 'Count']
    ).properties(
        title=title,
        width=300,
        height=300
    )

def create_syllable_table(pronunciation_result: Dict[str, Any]) -> str:
    """Create syllable analysis table in HTML format"""
    output = """
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid black; padding: 8px; text-align: left; }
        th { background-color: #00008B; color: white; }
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
                phoneme_text = convert_to_ipa(phoneme["Phoneme"])
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

def convert_to_ipa(pronunciation: str) -> str:
    """Convert Azure phonemes to IPA symbols"""
    phoneme_map = {
        # Vowels
        'aa': 'ɑ', 'ae': 'æ', 'ah': 'ʌ', 'ao': 'ɔ',
        'aw': 'aʊ', 'ax': 'ə', 'ay': 'aɪ', 'eh': 'ɛ',
        'er': 'ɝ', 'ey': 'eɪ', 'ih': 'ɪ', 'iy': 'i',
        'ow': 'oʊ', 'oy': 'ɔɪ', 'uh': 'ʊ', 'uw': 'u',
        # Consonants
        'b': 'b', 'ch': 'tʃ', 'd': 'd', 'dh': 'ð',
        'f': 'f', 'g': 'g', 'hh': 'h', 'jh': 'dʒ',
        'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
        'ng': 'ŋ', 'p': 'p', 'r': 'r', 's': 's',
        'sh': 'ʃ', 't': 't', 'th': 'θ', 'v': 'v',
        'w': 'w', 'y': 'j', 'z': 'z', 'zh': 'ʒ'
    }
    
    # Special combinations
    special_combinations = {
        'dx': 'ɾ', 'nx': 'ɾ̃', 'el': 'ḷ',
        'em': 'm̩', 'en': 'n̩'
    }
    
    def convert_phoneme(phoneme):
        if phoneme in special_combinations:
            return special_combinations[phoneme]
        return phoneme_map.get(phoneme, phoneme)
    
    phonemes = pronunciation.strip().split()
    ipa = ' '.join(convert_phoneme(p) for p in phonemes)
    
    # Fix stress mark spacing
    ipa = ipa.replace('ˈ ', 'ˈ').replace('ˌ ', 'ˌ')
    
    return ipa

def create_score_progress_charts(data: pd.DataFrame) -> alt.Chart:
    """Create combined score progress charts"""
    # Overall score chart
    overall_chart = create_overall_score_chart(data)
    
    # Detail scores chart
    detail_chart = create_detail_scores_chart(data)
    
    # Combine charts vertically
    return alt.vconcat(overall_chart, detail_chart)

def create_overall_score_chart(data: pd.DataFrame) -> alt.Chart:
    """Create overall score progress chart"""
    y_min = max(0, data['PronScore'].min() - 5)
    y_max = min(100, data['PronScore'].max() + 5)
    
    return alt.Chart(data).mark_line(
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
                scale=alt.Scale(domain=[y_min, y_max])),
        tooltip=['Attempt', 'PronScore']
    ).properties(
        title='総合点スコア',
        width=600,
        height=300
    ).interactive()

def create_detail_scores_chart(data: pd.DataFrame) -> alt.Chart:
    """Create detailed scores progress chart"""
    metrics = ['AccuracyScore', 'FluencyScore', 'CompletenessScore', 'ProsodyScore']
    detail_data = data.melt(
        id_vars=['Attempt'],
        value_vars=metrics,
        var_name='Metric',
        value_name='Score'
    )
    
    y_min = max(0, min(data[metrics].min()) - 5)
    y_max = min(100, max(data[metrics].max()) + 5)
    
    return alt.Chart(detail_data).mark_line(
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
                scale=alt.Scale(domain=[y_min, y_max])),
        color=alt.Color('Metric:N',
                       scale=alt.Scale(
                           range=['#00C957', '#4169E1', '#FFD700', '#FF69B4']
                       ),
                       legend=alt.Legend(
                           title='評価指標',
                           orient='right'
                       )),
        tooltip=['Attempt', 'Score', 'Metric']
    ).properties(
        title='詳細スコア',
        width=600,
        height=300
    ).interactive()