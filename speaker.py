import subprocess
import os
import sys

def speak_hindi(text):
    output_filename = "response.wav"
    model_path = "hi_IN-pratham-medium.onnx"
    
    # --- OS COMPATIBILITY SWITCH ---
    if sys.platform == "win32":
        piper_exe = r"piper\piper.exe"
        play_command = ["start", "/wait", output_filename]
        is_windows = True
    else:
        # Raspberry Pi / Linux path
        piper_exe = "./piper/piper" 
        play_command = ["aplay", output_filename]
        is_windows = False

    print(f"⚙️ Sending to Piper ({sys.platform})...")
    
    # 1. Pipeline to Executable
    process = subprocess.Popen(
        [piper_exe, "-m", model_path, "-f", output_filename],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 2. Inject Hindi Text
    stdout, stderr = process.communicate(input=text.encode('utf-8'))
    
    if process.returncode != 0:
        print("❌ Piper Error:", stderr.decode('utf-8', errors='ignore'))
        return

    print("✅ Audio generated!")
    
    # 3. Playback Switch
    if is_windows:
        os.system(f"start /wait {output_filename}")
    else:
        # Standard Linux/Pi wave player
        subprocess.run(["aplay", output_filename])

if __name__ == "__main__":
    test_phrase = "नमस्ते, मैं अब रास्पबेरी पाई के लिए तैयार हूँ।"
    speak_hindi(test_phrase)