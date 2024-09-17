import streamlit as st
import os
import base64

# 创建一个文件夹来保存录制的音频
if not os.path.exists("recordings"):
    os.makedirs("recordings")

# 定义一个函数来保存录制的音频
def save_audio(audio_data, filename):
    with open(filename, "wb") as f:
        f.write(audio_data)

# 定义一个函数来显示录制的音频
def show_audio(filename):
    with open(filename, "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode()
    audio_tag = f'<audio controls src="data:audio/wav;base64,{b64}"></audio>'
    st.markdown(audio_tag, unsafe_allow_html=True)

# 定义一个函数来录制音频
def record_audio():
    st.write("请点击按钮开始录制音频")
    if st.button("开始录制"):
        st.write("录制中... 请点击停止按钮结束录制")
        st.write("""
        <script>
        const startRecording = () => {
            const constraints = { audio: true };
            navigator.mediaDevices.getUserMedia(constraints)
                .then(stream => {
                    const mediaRecorder = new MediaRecorder(stream);
                    const audioChunks = [];

                    mediaRecorder.addEventListener("dataavailable", event => {
                        audioChunks.push(event.data);
                    });

                    mediaRecorder.addEventListener("stop", () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = () => {
                            const base64data = reader.result;
                            const audioData = base64data.split(',')[1];
                            const audioBytes = atob(audioData);
                            const audioArray = new Uint8Array(audioBytes.length);
                            for (let i = 0; i < audioBytes.length; i++) {
                                audioArray[i] = audioBytes.charCodeAt(i);
                            }
                            const audioBuffer = audioArray.buffer;
                            const filename = "recordings/recording.wav";
                            save_audio(audioBuffer, filename);
                            show_audio(filename);
                        };
                    });

                    mediaRecorder.start();

                    st.button("停止录制", on_click=() => {
                        mediaRecorder.stop();
                    });
                });
        };
        startRecording();
        </script>
        """, unsafe_allow_html=True)

# 主函数
def main():
    st.title("Streamlit 音频录制示例")
    record_audio()

if __name__ == "__main__":
    main()
main()