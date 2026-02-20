import pyaudio
import json
import sys
import os
from vosk import Model, KaldiRecognizer

# Universal path handling for Windows and Linux
MODEL_PATH = "model"

if not os.path.exists(MODEL_PATH):
    print(f"❌ Error: Model folder not found at {MODEL_PATH}")
    sys.exit(1)

model = Model(MODEL_PATH) 
recognizer = KaldiRecognizer(model, 16000)

audio = pyaudio.PyAudio()

# RPi Tweak: Linux sometimes requires specific device_index. 
# For now, we stay with default, but we wrap it in a cleaner start.
stream = audio.open(format=pyaudio.paInt16, 
                    channels=1, 
                    rate=16000, 
                    input=True, 
                    frames_per_buffer=8000)

print(f"🟢 Mic Live on {sys.platform}! Speak Hindi...")

try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if result['text']:
                print(f"✅ You said: {result['text']}")
        else:
            partial = json.loads(recognizer.PartialResult())
            if partial['partial']:
                print(f"   Listening... {partial['partial']}", end='\r')
except KeyboardInterrupt:
    print("\nStopping...")
    stream.stop_stream()
    stream.close()
    audio.terminate()