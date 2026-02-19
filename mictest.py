import pyaudio
import json
from vosk import Model, KaldiRecognizer

# 1. Load the pre-trained Hindi model
print("Loading Vosk model (this takes a few seconds)...")
model = Model("model") 
recognizer = KaldiRecognizer(model, 16000)

# 2. Initialize the microphone stream via PyAudio
audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, 
                    channels=1, 
                    rate=16000, 
                    input=True, 
                    frames_per_buffer=8000)

print("\nMicrophone is live! Start speaking Hindi (e.g., 'namaste', 'samay kya hai')...")
print("Press Ctrl+C to stop.\n")

# 3. The Event Loop: Listen and transcribe continuously
try:
    while True:
        # Read raw audio data from the laptop mic
        data = stream.read(4000, exception_on_overflow=False)
        
        # Pass the audio chunk to the Vosk recognizer
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if result['text']:
                print(f"✅ You said: {result['text']}")
        else:
            # Vosk also gives partial real-time guesses
            partial = json.loads(recognizer.PartialResult())
            if partial['partial']:
                print(f"   Listening... {partial['partial']}", end='\r')

except KeyboardInterrupt:
    print("\n\nStopping the microphone...")
    stream.stop_stream()
    stream.close()
    audio.terminate()