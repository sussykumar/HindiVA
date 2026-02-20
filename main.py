import os
import sys
import json
import pyaudio
import subprocess
import threading
import time
import re
from datetime import datetime, timedelta
from vosk import Model, KaldiRecognizer
from intentparser import parse_multiple_intents
import hardware 

# ==========================================
# CONFIGURATION & BLUETOOTH OPTIMIZATION
# ==========================================
VOSK_MODEL_PATH = "vosk"
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

def trigger_alarm(message):
    print(f"\n⏰ [SYSTEM ALARM]: {message}")
    speak_hindi(message)

# ==========================================
# 🧠 OFFLINE MEMORY ENGINE (ALARM & REMINDERS)
# ==========================================
DB_FILE = "memory.json"

def save_event(event_type, minutes_from_now, message):
    """Calculates exact future time from minutes and writes it to hard drive."""
    trigger_time = datetime.now() + timedelta(minutes=minutes_from_now)
    
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({
        "type": event_type,
        "trigger_time": trigger_time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "status": "pending"
    })
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"💾 [MEMORY]: Saved {event_type} for {trigger_time.strftime('%H:%M')}")

def save_scheduled_event(event_type, exact_trigger_time, message):
    """Saves a specific future date/time to the offline JSON memory."""
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({
        "type": event_type,
        "trigger_time": exact_trigger_time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "status": "pending"
    })
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"💾 [MEMORY]: Scheduled {event_type} for {exact_trigger_time.strftime('%Y-%m-%d %H:%M')}")

def timekeeper_daemon():
    """Runs in the background forever. Checks the clock every 10 seconds."""
    while True:
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            now = datetime.now()
            db_updated = False

            for event in data:
                if event["status"] == "pending":
                    trigger_time = datetime.strptime(event["trigger_time"], "%Y-%m-%d %H:%M:%S")
                    
                    if now >= trigger_time:
                        print(f"\n⏰ [ALARM TRIGGERED]: {event['message']}")
                        trigger_alarm(event["message"]) 
                        event["status"] = "done"
                        db_updated = True

            if db_updated:
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

        except Exception as e:
            pass 

        time.sleep(10)

# ==========================================
# OFFLINE NLP EXTRACTORS
# ==========================================
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
    """Parses exact Hindi times (digits or words) and calculates the future datetime."""
    now = datetime.now()
    days_to_add = 0
    
    if "कल" in phrase: days_to_add = 1
    elif "परसों" in phrase: days_to_add = 2
    
    target_date = now + timedelta(days=days_to_add)
    
    hour = None
    minute = 0
    
    time_match = re.search(r'(\d{1,2})(?:\s*बजकर\s*(\d{1,2})\s*मिनट|:(\d{2})|\s*बजे)', phrase)
    
    if time_match:
        hour = int(time_match.group(1))
        if time_match.group(2): 
            minute = int(time_match.group(2))
        elif time_match.group(3): 
            minute = int(time_match.group(3))
    else:
        hindi_numbers = {
            "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, 
            "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12
        }
        for word, num in hindi_numbers.items():
            if f"{word} बजे" in phrase:
                hour = num
                break

    if hour is not None:
        if "साढ़े" in phrase: minute = 30
        elif "सवा" in phrase: minute = 15
        elif "पौने" in phrase:
            hour = hour - 1 if hour > 1 else 12
            minute = 45

    if hour is not None:
        if hour < 12 and any(word in phrase for word in ["शाम", "रात", "दोपहर"]):
            hour += 12
        elif hour == 12 and "सुबह" in phrase:
            hour = 0
    else:
        hour = 10 
        if "सुबह" in phrase: hour = 9
        elif "दोपहर" in phrase: hour = 13
        elif "शाम" in phrase: hour = 18
        elif "रात" in phrase: hour = 21

    event = "रिमाइंडर" 
    if "बर्थडे" in phrase or "जन्मदिन" in phrase: event = "जन्मदिन"
    elif "मीटिंग" in phrase or "बैठक" in phrase: event = "मीटिंग"
    elif "वैक्सीन" in phrase or "टीका" in phrase: event = "वैक्सीनेशन"
    elif "दवाई" in phrase or "मेडिसिन" in phrase: event = "दवाई खाने"
    
    trigger_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if trigger_time <= now:
        trigger_time += timedelta(days=1)
        
    return event, trigger_time

# ==========================================
# 100% OFFLINE RESPONSE GENERATOR
# ==========================================
def generate_response(intent, phrase):
    now = datetime.now()
    
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
            save_event("alarm", minutes, "आपका अलार्म का समय हो गया है।")
            return f"ठीक है, मैंने {minutes} मिनट का अलार्म सेट कर दिया है।"
        else:
            save_event("alarm", 1, "अलार्म का समय हो गया है!")
            return "आपने समय नहीं बताया, इसलिए मैंने एक मिनट का डेमो अलार्म सेट कर दिया है।"

    elif intent == "REMINDER_SET":
        minutes = extract_minutes(phrase)
        if minutes and "कल" not in phrase and "परसों" not in phrase:
            save_event("reminder", minutes, f"आपके {minutes} मिनट पूरे हो गए हैं।")
            return f"ठीक है, मैंने {minutes} मिनट का रिमाइंडर सेट कर दिया है।"
        
        event, exact_time = extract_long_term_event(phrase)
        message = f"ध्यान दें! आपका {event} का समय हो गया है।"
        
        save_scheduled_event("reminder", exact_time, message)
        
        day_str = "आज"
        if "कल" in phrase: day_str = "कल"
        elif "परसों" in phrase: day_str = "परसों"
        
        return f"ठीक है, मैंने {day_str} के लिए आपके {event} का रिमाइंडर सेव कर लिया है।"

    # --- Volume Control ---
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

    print("Loading Hybrid Intent Parser (Brain)... Done.")
    print("Loading Piper TTS Engine (Voice)... Done.")
    
    print("Starting Offline Memory Daemon...")
    time_thread = threading.Thread(target=timekeeper_daemon, daemon=True)
    time_thread.start()
    
    print("\n" + "=" * 50)
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
                            
                            print(f"🧠 [Brain]: Mapped '{phrase}' to '{detected_intent}' ({confidence}%)")
                            
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