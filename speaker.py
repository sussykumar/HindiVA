import subprocess
import os

def speak_hindi(text):
    """
    Synthesizes speech using the highly optimized Piper C++ binary.
    This handles Devanagari perfectly and mimics the Raspberry Pi deployment.
    """
    output_filename = "response.wav"
    piper_exe = r"piper\piper.exe"
    model_path = "hi_IN-pratham-medium.onnx"
    
    print("⚙️ Sending Hindi text to Piper C++ Engine...")
    
    # 1. Open a direct pipeline to the executable
    process = subprocess.Popen(
        [piper_exe, "-m", model_path, "-f", output_filename],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 2. Safely encode the Hindi text to UTF-8 and send it
    stdout, stderr = process.communicate(input=text.encode('utf-8'))
    
    # Check if the C++ engine threw any real errors
    if process.returncode != 0:
        print("❌ Piper Engine Error:")
        print(stderr.decode('utf-8', errors='ignore'))
        return

    # 3. Play the generated file via Windows (bypassing PyAudio routing issues)
    print("✅ Audio generated successfully! Playing through AirPods...")
    os.startfile(output_filename)

# --- Local Testing Block ---
if __name__ == "__main__":
    print("\n🗣️ Voice Module Active (Subprocess Mode)!")
    test_phrase = "नमस्ते क्वार्क, मैं अब बोल सकती हूँ। आपका प्रोजेक्ट कैसा चल रहा है?"
    print(f"Speaking: '{test_phrase}'")
    speak_hindi(test_phrase)