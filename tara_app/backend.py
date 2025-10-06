import webrtcvad
import pyaudio
import wave
import time
import requests
import pybase64
from pathlib import Path
import numpy as np
import noisereduce as nr
import speech_recognition as sr
import os
from kivy.core.audio import SoundLoader

try:
    from .config import API_KEY
except ImportError:
    API_KEY = "YOUR_API_KEY"


# Trigger and termination words
TRIGGERS = ["hello tara", "hey tara", "hi tara", "tara let's play", "tara story time", "wake up tara", "ok tara", "tara start", "listen tara", "tara are you there"]
TERMINATORS = ["goodbye tara", "sleep now tara", "that's all tara", "stop tara", "the end tara", "tara bye", "tara stop listening", "tara exit", "tara shutdown"]

def detect_keywords(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio).lower()
        print(f"Detected speech: {text}")
        if any(t in text for t in TRIGGERS):
            print("✅ Trigger word detected!")
            return "TRIGGER"
        if any(t in text for t in TERMINATORS):
            print("🛑 Termination word detected!")
            return "TERMINATE"
    except sr.UnknownValueError:
        print("Could not understand audio.")
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
    except FileNotFoundError:
        print("Audio file not found for keyword detection.")
    return None

class AudioRecorder:
    def __init__(self, status_callback, sample_rate=16000, frame_duration=10):
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frames_per_buffer = int(sample_rate * frame_duration / 1000)
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(2)
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_listening = False
        self.status_callback = status_callback

    def start_stream(self):
        if self.stream is None:
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=self.frames_per_buffer)
        self.is_listening = True

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        if self.p:
            self.p.terminate()
            self.p = None
        self.is_listening = False

    def listen_and_record(self):
        self.start_stream()
        self.status_callback("Listening...", "listening")
        print("Listening...")
        frames = []
        recording = False
        last_speech_time = time.time()

        while self.is_listening:
            try:
                frame = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                is_speech = self.vad.is_speech(frame, self.sample_rate)

                if is_speech:
                    if not recording:
                        recording = True
                        frames = []
                        self.status_callback("Recording...", "active")
                        print("Speech detected, starting recording...")
                    frames.append(frame)
                    last_speech_time = time.time()
                elif recording and time.time() - last_speech_time > 1.0: # 1 second of silence
                    print("Silence detected, stopping recording.")
                    self.save_recording(frames)
                    return True # Audio saved
            except (IOError, AttributeError) as e:
                if self.is_listening:
                    print(f"Error during recording stream: {e}")
                return False
        return False # No audio saved

    def save_recording(self, frames):
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)

        # Noise reduction
        reduced_noise = nr.reduce_noise(y=audio_data, sr=self.sample_rate)

        # Save the cleaned audio
        with wave.open("recorded_audio.wav", 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(reduced_noise.astype(np.int16).tobytes())
        print("Audio recorded and cleaned successfully!")

def play_audio(file_path, status_callback):
    try:
        status_callback("Playing response...", "speaking")
        sound = SoundLoader.load(file_path)
        if sound:
            sound.play()
            while sound.state == 'play':
                time.sleep(0.1)
        else:
            print(f"Could not load sound from {file_path}")
    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        status_callback("Listening...", "listening")

class RequestHandler:
    def __init__(self):
        self.api_url = "https://voice-bot-backend-147374697476.asia-south1.run.app/api/ai"
        self.api_key = API_KEY

    def _send_request(self, data):
        try:
            response = requests.post(f"{self.api_url}/answer-query", json=data, timeout=20)
            response.raise_for_status()
            response_data = response.json()
            if 'audioFile' in response_data:
                self.save_base64_audio(response_data['audioFile'], "response_audio.wav")
            return response_data
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
        return None

    def send_audio(self, audio_path, user_id, conversation_id):
        with open(audio_path, "rb") as audio_file:
            audio_data = pybase64.b64encode(audio_file.read()).decode('utf-8')

        data = {
            'audioData': audio_data,
            'userId': user_id,
            'conversationId': conversation_id,
            'api_key': self.api_key
        }
        return self._send_request(data)

    def ask_question(self, user_id, conversation_id):
        data = {
            'audioData': None,
            'userId': user_id,
            'conversationId': conversation_id,
            'api_key': self.api_key
        }
        return self._send_request(data)

    def save_base64_audio(self, base64_audio_data, output_path):
        audio_bytes = pybase64.b64decode(base64_audio_data)
        with open(output_path, 'wb') as audio_file:
            audio_file.write(audio_bytes)
        print(f"Audio file saved to: {output_path}")


class TaraBackend:
    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.user_id = None
        self.conversation_id = None
        self.active = False
        self.running = False
        self.audio_recorder = AudioRecorder(status_callback)
        self.request_handler = RequestHandler()

    def start(self):
        if self.request_handler.api_key == "YOUR_API_KEY":
            self.status_callback("API key not set. Please edit tara_app/config.py", "listening")
            return

        self.running = True
        self.main_loop()

    def stop(self):
        self.running = False
        self.audio_recorder.stop_stream()

    def main_loop(self):
        while self.running:
            has_audio = self.audio_recorder.listen_and_record()

            if not self.running:
                break

            if has_audio:
                self.status_callback("Processing...", "processing")
                keyword = detect_keywords("recorded_audio.wav")

                if not self.active:
                    if keyword == "TRIGGER":
                        self.active = True
                        self.status_callback("Tara is now active!", "active")
                    else:
                        self.status_callback("Waiting for trigger word.", "listening")
                    continue

                if keyword == "TERMINATE":
                    self.active = False
                    self.status_callback("Conversation ended.", "listening")
                    continue

                response = self.request_handler.send_audio("recorded_audio.wav", self.user_id, self.conversation_id)
                if response:
                    self.user_id = response.get('userId')
                    self.conversation_id = response.get('conversationId')
                    play_audio("response_audio.wav", self.status_callback)
                else:
                    self.status_callback("Error: No response from server.", "listening")

            elif self.active: # Timeout case
                self.status_callback("Asking a follow-up...", "processing")
                response = self.request_handler.ask_question(self.user_id, self.conversation_id)
                if response:
                    self.user_id = response.get('userId')
                    self.conversation_id = response.get('conversationId')
                    play_audio("response_audio.wav", self.status_callback)
                else:
                    self.status_callback("Error: No response from server.", "listening")

        print("Backend loop stopped.")