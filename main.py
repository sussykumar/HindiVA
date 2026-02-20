import os
import sys
import json
import pyaudio
import subprocess
import datetime
import threading
import re
from vosk import Model, KaldiRecognizer
from intentparser import parse_multiple_intents
import hardware 

# ==========================================
# CONFIGURATION & BLUETOOTH OPTIMIZATION
# ==========================================
VOSK_MODEL_PATH = "model"
PIPER_MODEL = "hi_IN-pratham-medium.onnx"
WAKE_WORDS = ["सुनो", "नमस्ते"]

if sys.platform == "win32":
    PIPER_EXE = "piper\\piper.exe"
    PLAY_CMD = "start /wait response.wav"
else:
    PIPER_EXE = "./piper/piper"
    PLAY_CMD = "paplay response.wav" 

# ==========================================
# TEXT-TO-SPEECH (PIPER)
# ==========================================
def speak_hindi(text):
    print(f"⚙️ Synthesizing: '{text}'")
    command = [PIPER_EXE, "-m", PIPER_MODEL, "--output_file", "response.wav"]
    try:
        subprocess.run(
            command, 
            input=text.encode('utf-8'),
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            check=True
        )
        os.system(PLAY_CMD)
        print("✅ Audio played.\n")
    except subprocess.CalledProcessError:
        print("❌ Piper TTS Engine failed to synthesize audio.")

# ==========================================
# OFFLINE NLP EXTRACTORS
# ==========================================
def trigger_alarm(message):
    print(f"\n⏰ [SYSTEM ALARM]: {message}")
    speak_hindi(message)

def extract_minutes(phrase):
    time_map = {
        "एक मिनट": 1, "1 मिनट": 1, "दो मिनट": 2, "2 मिनट": 2, 
        "तीन मिनट": 3, "3 मिनट": 3, "चार मिनट": 4, "4 मिनट": 4, 
        "पांच मिनट": 5, "पाँच मिनट": 5, "5 मिनट": 5, 
        "दस मिनट": 10, "10 मिनट": 10, "पंद्रह मिनट": 15, "15 मिनट": 15, 
        "बीस मिनट": 20, "20 मिनट": 20, "तीस मिनट": 30, "30 मिनट": 30, 
        "आधा घंटा": 30, "आधे घंटे": 30, "एक घंटा": 60, "एक घंटे": 60
    }
    for key, value in time_map.items():
        if key in phrase:
            return value
    return None

def extract_long_term_event(phrase):
    day = "आज" 
    if "कल" in phrase: day = "कल"
    elif "परसों" in phrase: day = "परसों"
        
    event = "रिमाइंडर"
    if "बर्थडे" in phrase or "जन्मदिन" in phrase: event = "जन्मदिन"
    elif "मीटिंग" in phrase or "बैठक" in phrase: event = "मीटिंग"
    elif "वैक्सीन" in phrase or "टीका" in phrase or "वैक्सीनेशन" in phrase: event = "वैक्सीनेशन"
    elif "दवाई" in phrase: event = "दवाई का"
        
    if "मिनट" in phrase or "घंटा" in phrase or "घंटे" in phrase:
        return None, None
        
    return event, day

# ==========================================
# 100% OFFLINE RESPONSE GENERATOR
# ==========================================
def generate_response(intent, phrase):
    now = datetime.datetime.now()
    
    # --- Home Automation ---
    if intent == "LIGHT_ON": 
        hardware.control_appliance("LIGHT", "ON")
        return "ठीक है, बत्ती चालू कर दी गई है।" 
    elif intent == "LIGHT_OFF": 
        hardware.control_appliance("LIGHT", "OFF")
        return "ठीक है, मैंने बत्ती बंद कर दी है।" 
    elif intent == "FAN_ON": 
        hardware.control_appliance("FAN", "ON")
        return "ठीक है, पंखा चालू कर दिया गया है।" 
    elif intent == "FAN_OFF": 
        hardware.control_appliance("FAN", "OFF")
        return "ठीक है, पंखा बंद कर दिया गया है।" 
    elif intent == "AC_ON": 
        hardware.control_appliance("AC", "ON")
        return "ठीक है, एसी चालू कर दिया गया है।"
        
    # --- Time, Date & Weather ---
    elif intent == "TIME_ASK":
        hour = now.hour % 12 or 12
        return f"अभी समय {hour} बजकर {now.minute} मिनट हो रहा है।"
    elif intent == "DATE_ASK":
        return f"आज {now.day} तारीख है।" 
    elif intent == "DAY_ASK":
        hindi_days = ["सोमवार", "मंगलवार", "बुधवार", "बृहस्पतिवार", "शुक्रवार", "शनिवार", "रविवार"]
        return f"आज {hindi_days[now.weekday()]} है।"
    elif intent == "WEATHER_ASK": 
        live_temp = hardware.get_temperature()
        return f"आज मौसम साफ है और तापमान {live_temp} डिग्री है।" 
    elif intent == "TEMP_ASK": 
        live_temp = hardware.get_temperature()
        return f"अभी कमरे का तापमान {live_temp} डिग्री सेल्सियस है।"
    elif intent == "RAIN_ASK": 
        return "आज बारिश की कोई संभावना नहीं है।"
        
    # --- Reminders & Alarms ---
    elif intent == "ALARM_SET":
        minutes = extract_minutes(phrase)
        if minutes:
            threading.Timer(minutes * 60, trigger_alarm, args=["आपका अलार्म का समय हो गया है।"]).start()
            return f"ठीक है, मैंने {minutes} मिनट का अलार्म सेट कर दिया है।"
        else:
            threading.Timer(60.0, trigger_alarm, args=["अलार्म का समय हो गया है!"]).start()
            return "आपने समय नहीं बताया, इसलिए मैंने एक मिनट का डेमो अलार्म सेट कर दिया है।"

    elif intent == "REMINDER_SET":
        event, day = extract_long_term_event(phrase)
        if event and day:
            reminder_data = {"day": day, "event": event, "created_at": str(datetime.datetime.now())}
            with open("offline_database.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(reminder_data, ensure_ascii=False) + "\n")
            return f"ठीक है, मैंने {day} के लिए आपके {event} रिमाइंडर को लोकल डेटाबेस में सुरक्षित कर लिया है।"
        else:
            minutes = extract_minutes(phrase)
            if minutes:
                threading.Timer(minutes * 60, trigger_alarm, args=[f"आपके {minutes} मिनट पूरे हो गए हैं।"]).start()
                return f"ठीक है, मैंने {minutes} मिनट का रिमाइंडर सेट कर दिया है।"
            return "मैंने आपका रिमाइंडर सुरक्षित कर लिया है।"

    # --- Volume Control (REAL OS Integration) ---
    elif intent == "ALARM_STOP": return "अलार्म बंद कर दिया गया है।"
    elif intent == "VOLUME_UP": 
        if sys.platform != "win32":
            os.system("pactl set-sink-volume @DEFAULT_SINK@ +15%")
        return "मैंने आवाज़ बढ़ा दी है।"
    elif intent == "VOLUME_DOWN": 
        if sys.platform != "win32":
            os.system("pactl set-sink-volume @DEFAULT_SINK@ -15%")
        return "मैंने आवाज़ कम कर दी है।"
        
    # --- Fallbacks ---
    elif intent == "UNKNOWN_COMMAND": return "माफ़ कीजिए, मैं केवल घर के उपकरणों को नियंत्रित कर सकती हूँ।"
    else: return "माफ़ कीजिए, मुझे समझ नहीं आया।"

# ==========================================
# MAIN AUDIO PIPELINE
# ==========================================
if __name__ == "__main__":
    print("Loading Vosk Acoustic Model (Ears)...")
    if not os.path.exists(VOSK_MODEL_PATH):
        print(f"Error: Vosk model not found at '{VOSK_MODEL_PATH}'.")
        sys.exit(1)
        
    model = Model(VOSK_MODEL_PATH)
    wake_word_grammar = '["नमस्ते", "सुनो", "[unk]"]'
    wake_recognizer = KaldiRecognizer(model, 16000, wake_word_grammar)
    main_recognizer = KaldiRecognizer(model, 16000)
    
    audio = pyaudio.PyAudio()
    
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    print("Loading Intent Parser (Brain)... Done.")
    print("Loading Piper TTS Engine (Voice)... Done.\n")
    print("=" * 50)
    print(f"🟢 SOVEREIGN SENTRY: ONLINE & AIR-GAPPED ({sys.platform})")
    print("Say 'Namaste' or 'Suno' to wake me up.")
    print("Press Ctrl+C to shut down.")
    print("=" * 50 + "\n")

    is_awake = False

    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)

            if not is_awake:
                if wake_recognizer.AcceptWaveform(data):
                    result = json.loads(wake_recognizer.Result())
                    text = result.get('text', '')
                    if any(word in text for word in WAKE_WORDS):
                        print("\n🔔 [Wake Word Detected]: Waking up system...")
                        stream.stop_stream()
                        speak_hindi("हाँ क्वार्क, बताइये?") 
                        stream.start_stream()
                        is_awake = True
                        print("Listening for command...")
            else:
                if main_recognizer.AcceptWaveform(data):
                    result = json.loads(main_recognizer.Result())
                    transcribed_text = result.get('text', '')
                    if transcribed_text:
                        print(f"\n🗣️ [Quark]: {transcribed_text}")
                        intent_list = parse_multiple_intents(transcribed_text)
                        combined_replies = []
                        
                        for intent_data in intent_list:
                            detected_intent = intent_data['intent']
                            phrase = intent_data['phrase']
                            confidence = intent_data['confidence']
                            
                            print(f"🧠 [Brain]: Detected '{detected_intent}' from '{phrase}' ({confidence}%)")
                            
                            reply_text = generate_response(detected_intent, phrase)
                            
                            if detected_intent == "UNKNOWN_COMMAND" and len(intent_list) > 1: continue
                            combined_replies.append(reply_text)
                                
                        final_spoken_response = " ".join(combined_replies)
                        print(f"🤖 [Assistant]: {final_spoken_response}")
                        
                        if final_spoken_response.strip():
                            stream.stop_stream()
                            speak_hindi(final_spoken_response)
                            stream.start_stream()
                        
                        print("\n💤 Going back to sleep...")
                        is_awake = False
                        
                else:
                    partial = json.loads(main_recognizer.PartialResult())
                    if partial.get('partial'):
                        print(f"Processing... {partial['partial']}", end='\r')

    except KeyboardInterrupt:
        print("\n\nShutting down system safely...")
        stream.stop_stream()
        stream.close()
        audio.terminate()