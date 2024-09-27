import os
import azure.cognitiveservices.speech as speechsdk

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# The neural multilingual voice can speak different languages based on the input text.
speech_config.speech_synthesis_voice_name='en-US-AndrewMultilingualNeural'

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

def text_to_speech(text: str, file_path: str = None):
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    audio_stream = speechsdk.AudioDataStream(speech_synthesis_result)
    # audio_file_path = "../outputs_v2/gemini_source_output.mp3" 
    audio_file_path = file_path
    audio_stream.save_to_wav_file(audio_file_path)

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")


def main(): 
    text = "Hello, I am OpenVoice. How can I help you?"
    text_to_speech(text, 'output.mp3')

if __name__ == "__main__":
    main()