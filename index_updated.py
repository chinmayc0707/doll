
import webrtcvad
import pyaudio
import wave
import time
import requests
import pybase64
from pathlib import Path
import pygame
import numpy as np
import noisereduce as nr
import speech_recognition as sr
import os


# ✅ Tara trigger & termination words
TRIGGERS = [
    "hello tara",
    "hey tara",
    "hi tara",
    "tara let's play",
    "tara story time",
    "wake up tara",
    "ok tara",
    "tara start",
    "listen tara",
    "tara are you there"
]

TERMINATORS = [
    "goodbye tara",
    "sleep now tara",
    "that's all tara",
    "stop tara",
    "the end tara",
    "tara bye",
    "tara stop listening",
    "tara exit",
    "tara shutdown"
]


def detect_keywords(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"Detected speech: {text}")
        for t in TRIGGERS:
            if t in text:
                print("✅ Trigger word detected!")
                return "TRIGGER"
        for t in TERMINATORS:
            if t in text:
                print("🛑 Termination word detected!")
                return "TERMINATE"
    except sr.UnknownValueError:
        print("Could not understand audio.")
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
    return None


class AudioRecorder:
    def __init__(self, sample_rate=16000, frame_duration=10):
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frames_per_buffer = int(sample_rate * frame_duration / 1000)
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(2)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=self.sample_rate,
                                  input=True,
                                  frames_per_buffer=self.frames_per_buffer)
        self.isListening = True
        self.hasGotAudioFile = False

    def _detect_noise_level(self, audio_data):
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)) / 32768.0
        if rms < 0.01:
            return "mild"
        elif rms < 0.03:
            return "medium"
        else:
            return "aggressive"

    def record_audio(self, frames, sample_rate=16000, recorded_time=5):
        if recorded_time < 2:
            print("Recording time is less than 2 seconds. Discarding audio...")
            return

        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        noise_sample = audio_data[:sample_rate] if len(audio_data) > sample_rate else audio_data
        strength = self._detect_noise_level(noise_sample)

        if strength == "mild":
            prop_decrease = 0.4
        elif strength == "aggressive":
            prop_decrease = 1.0
        else:
            prop_decrease = 0.7

        print(f"Environment detected as {strength.upper()} noise. Applying {strength} noise reduction...")
        reduced_noise = nr.reduce_noise(y=audio_data, sr=sample_rate, prop_decrease=prop_decrease)

        wf = wave.open("recorded_audio.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(reduced_noise.astype(np.int16).tobytes())
        wf.close()

        print("Audio recorded and cleaned successfully!")
        self.hasGotAudioFile = True
        self.stop_stream()

    def stop_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.isListening = False

    def listen_audio(self):
        print("Listening...")
        try:
            recording = False
            frames = []
            start_time_loop = time.time()
            start_time = None
            last_speech_time = None

            while self.isListening:
                frame = self.stream.read(self.frames_per_buffer)
                frame_np = np.frombuffer(frame, dtype=np.int16)
                frame = frame_np.astype(np.int16).tobytes()

                if self.vad.is_speech(frame, self.sample_rate):
                    if not recording:
                        print("Speech detected! Starting recording...")
                        recording = True
                        frames = []
                        start_time = time.time()
                    frames.append(frame)
                    last_speech_time = time.time()
                    if time.time() - start_time > 5:
                        print("Recording time exceeded 5 seconds. Stopping recording...")
                        recorded_time = time.time() - start_time
                        self.record_audio(frames, self.sample_rate, recorded_time)
                        recording = False
                else:
                    if recording:
                        frames.append(frame)
                        if time.time() - last_speech_time > 1:
                            print("No speech detected for 1 second. Stopping recording...")
                            recorded_time = time.time() - start_time
                            self.record_audio(frames, self.sample_rate, recorded_time)
                            recording = False
                    elif time.time() - start_time_loop > 10:
                        print("No speech detected for 10 seconds. Stopping stream...")
                        self.stop_stream()
        except KeyboardInterrupt:
            print("Terminating...")
            self.stop_stream()
        return self.hasGotAudioFile


def play_audio(file_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("response_audio.wav")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        print("Audio played successfully!")
        pygame.mixer.music.unload()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except wave.Error as e:
        print(f"Error reading the audio file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


class requestResponse:
    def __init__(self):
        self.api_url = "https://voice-bot-backend-147374697476.asia-south1.run.app/api/ai"

    def create_base64_audio_file(self, audio_path):
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
        return pybase64.b64encode(audio_data).decode('utf-8')

    def save_base64_audio_file(self, base64_audio_data, output_path):
        audio_bytes = pybase64.b64decode(base64_audio_data)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'wb') as audio_file:
            audio_file.write(audio_bytes)
        print(f"Audio file saved to: {output_path}")

    def send_audio(self, audio_path, user_id, conversation_id):
        data = {
            'audioData': self.create_base64_audio_file(audio_path),
            'userId': user_id,
            'conversationId': conversation_id,
            'api_key': 'be3a0d00-c7ff-4537-8cbb-bed8090f8b5b'
        }
        response = requests.post(f"{self.api_url}/answer-query", json=data)
        if response.status_code == 201:
            print("Audio sent successfully!")
            data = response.json()
            audioData = data['audioFile']
            self.save_base64_audio_file(audioData, "response_audio.wav")
            return data
        else:
            print("Failed to send audio.")
            return None

    def ask_question(self, user_id, conversation_id):
        data = {
            'audioData': None,
            'userId': user_id,
            'conversationId': conversation_id,
            'api_key': 'be3a0d00-c7ff-4537-8cbb-bed8090f8b5b'
        }
        response = requests.post(f"{self.api_url}/answer-query", json=data)
        if response.status_code == 201:
            print("Audio sent successfully!")
            data = response.json()
            audioData = data['audioFile']
            self.save_base64_audio_file(audioData, "response_audio.wav")
            return data
        else:
            print("Failed to send audio.")
            return None


# ✅ Main loop with wake-word logic
user_id = None
conversation_id = None
active = False   # ✅ Tara only listens after a trigger

for _ in range(20):
    audio_recorder = AudioRecorder()
    hasGotAudioFile = audio_recorder.listen_audio()
    request = requestResponse()

    if hasGotAudioFile:
        keyword = detect_keywords("recorded_audio.wav")

        if not active:
            if keyword == "TRIGGER":
                active = True
                print("Tara is now ACTIVE 🌟")
            else:
                print("Ignored speech (waiting for trigger word).")
                continue

        if active:
            if keyword == "TERMINATE":
                print("Conversation ended by termination word.")
                break
            else:
                response = request.send_audio("recorded_audio.wav", user_id, conversation_id)
                if response:
                    user_id = response.get('userId')
                    conversation_id = response.get('conversationId')
                play_audio("response_audio.wav")

    else:
        if active:  # Only ask questions if Tara has been triggered
            response = request.ask_question(user_id, conversation_id)
            if response:
                user_id = response.get('userId')
                conversation_id = response.get('conversationId')
            play_audio("response_audio.wav")
