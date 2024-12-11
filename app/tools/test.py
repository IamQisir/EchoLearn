import streamlit as st
import librosa
import plotly.graph_objects as go
import numpy as np
import base64
from streamlit_plotly_events import plotly_events
import json

if 'audio_loaded' not in st.session_state:
    st.session_state.audio_loaded = False

def get_color(score):
    if score >= 80:
        return 'rgb(0, 200, 0)'
    elif score >= 60:   
        return 'rgb(255, 165, 0)'
    else:
        return 'rgb(255, 0, 0)'

def get_audio_html(file_path, start_time, duration):
    audio_html = f"""
        <style>
            audio {{
                display: none;
            }}
        </style>
        <div id="audio-container">
            <audio id="audio-player">
                <source src="data:audio/wav;base64,{get_audio_base64(file_path)}" type="audio/wav">
            </audio>
        </div>
        <script>
            var audio = document.getElementById("audio-player");
            audio.currentTime = {start_time};
            audio.play().catch(e => console.log("Play prevented:", e));
            setTimeout(() => {{
                audio.pause();
            }}, {duration * 1000});
        </script>
    """
    return audio_html

@st.cache_data
def get_audio_base64(file_path):
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    return base64.b64encode(audio_bytes).decode()

@st.cache_data
def load_audio(file_path):
    y, sr = librosa.load(file_path)
    return y, sr

def main():
    st.title("発音評価の可視化")

    # 配置一个空的容器用于音频播放
    audio_player = st.empty()
    
    # 文件上传
    audio_file = st.file_uploader("音声ファイルをアップロード", type=['wav'])
    
    if audio_file is not None:
        # 保存上传的文件
        with open("temp.wav", "wb") as f:
            f.write(audio_file.getbuffer())
        
        # 加载音频
        y, sr = load_audio("temp.wav")
        duration = len(y) / sr
        times = np.linspace(0, duration, num=len(y))

        # 配置固定的图表容器
        plot_container = st.empty()
        
        # 读取JSON文件
        with open(r'E:\Code\EchoLearn\database\qi\practice_history\2024-12-06\レッソン1-2024-12-06_15-29-52.json', 'r') as f:
            pronunciation_result = json.load(f)
        
        # 创建图表
        fig = go.Figure()
        
        # 添加基础波形
        fig.add_trace(go.Scatter(
            x=times,
            y=y,
            mode='lines',
            name='waveform',
            line=dict(color='lightgray', width=1),
            opacity=0.3
        ))
        
        # 处理每个单词
        words = pronunciation_result["NBest"][0]["Words"]
        for word in words:
            if ("PronunciationAssessment" not in word or 
                "ErrorType" not in word["PronunciationAssessment"] or
                word["PronunciationAssessment"]["ErrorType"] == "Omission"):
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
            
            # 添加单词波形
            fig.add_trace(go.Scatter(
                x=word_times,
                y=word_y,
                mode='lines',
                name=word["Word"],
                line=dict(color=color, width=2),
                customdata=[[start_time, word_duration]],
                hovertemplate=f"{word['Word']}<br>Score: {score}<extra></extra>"
            ))
            
            # 添加垂直线和标注
            fig.add_vline(x=start_time, line_dash="dash", line_color="gray", opacity=0.5)
            fig.add_vline(x=end_time, line_dash="dash", line_color="gray", opacity=0.5)
            
            # 添加单词标注
            fig.add_annotation(
                x=(start_time + end_time) / 2,
                y=min(y),
                text=f"{word['Word']} ({score})",
                showarrow=False,
                textangle=45,
                font=dict(size=10),
                yanchor='top'
            )
            
            # 添加音素标注
            if "Phonemes" in word:
                for phoneme in word["Phonemes"]:
                    phoneme_start = phoneme["Offset"] / 10000000
                    phoneme_score = phoneme["PronunciationAssessment"].get("AccuracyScore", 0)
                    phoneme_color = get_color(phoneme_score)
                    
                    fig.add_annotation(
                        x=phoneme_start,
                        y=max(y),
                        text=phoneme["Phoneme"],
                        showarrow=False,
                        font=dict(size=8, color=phoneme_color),
                        yanchor='bottom'
                    )

        # 更新布局
        fig.update_layout(
            title=dict(
                text='発音評価の可視化（单词をクリックして音声を再生）',
                y=0.95
            ),
            xaxis=dict(
                title='Time (seconds)',
                fixedrange=True,
                showgrid=False,
                rangeslider=dict(visible=False)
            ),
            yaxis=dict(
                title='Amplitude',
                fixedrange=True,
                showgrid=False,
                range=[min(y) * 1.2, max(y) * 1.2]
            ),
            showlegend=False,
            height=600,
            hovermode='closest',
            margin=dict(l=50, r=50, t=50, b=50),
            plot_bgcolor='white',
            modebar=dict(remove=['zoom', 'pan', 'autoscale', 'zoomin', 'zoomout'])
        )

        # 使用 st.empty() 显示图表并获取点击事件
        with plot_container:
            clicked = plotly_events(fig, override_width="100%", click_event=True)
            
            if clicked:
                point = clicked[0]
                trace_index = point.get('curveNumber', 0)
                if trace_index > 0:  # 跳过基础波形
                    point_data = fig.data[trace_index]
                    if hasattr(point_data, 'customdata') and len(point_data.customdata) > 0:
                        start_time, duration = point_data.customdata[0]
                        with audio_player:
                            st.components.v1.html(
                                get_audio_html("temp.wav", start_time, duration),
                                height=0
                            )

if __name__ == "__main__":
    main()