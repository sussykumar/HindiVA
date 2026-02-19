import pyaudio
import json
import datetime
from vosk import Model, KaldiRecognizer
import requests

from intentparser import parse_multiple_intents
from speaker import speak_hindi

import datetime # Make sure this is at the top of main.py!

def generate_response(intent):
    """Maps the detected intent to a spoken Hindi response."""
    now = datetime.datetime.now()
    
    # --- Home Automation ---
    if intent == "LIGHT_ON":
        return "ठीक है, मैं बत्ती चालू कर रही हूँ।" 
        
    elif intent == "LIGHT_OFF":
        return "ठीक है, मैं बत्ती बंद कर रही हूँ।" 
        
    elif intent == "FAN_ON":
        return "ठीक है, मैंने पंखा चालू कर दिया है।" 
        
    elif intent == "FAN_OFF":
        return "ठीक है, पंखा बंद कर दिया गया है।" 
        
    elif intent == "AC_ON":
        return "ठीक है, एसी चालू कर दिया गया है।"
        
    # --- Time and Date ---
    elif intent == "TIME_ASK":
        hour = now.hour % 12 or 12
        return f"अभी समय {hour} बजकर {now.minute} मिनट हो रहा है।"
        
    elif intent == "DATE_ASK":
        return f"आज {now.day} तारीख है।" 
        
    elif intent == "DAY_ASK":
        hindi_days = ["सोमवार", "मंगलवार", "बुधवार", "बृहस्पतिवार", "शुक्रवार", "शनिवार", "रविवार"]
        today_hindi = hindi_days[now.weekday()]
        return f"आज {today_hindi} है।"
        
    # --- Temperature and Weather (Offline Mock Data) ---
    elif intent == "WEATHER_ASK" or intent == "TEMP_ASK":
        return "कमरे का तापमान पच्चीस डिग्री है, और मौसम साफ़ है।" 
        
    elif intent == "RAIN_ASK":
        return "अभी बारिश की कोई संभावना नहीं है।"
        
    # --- Reminders and Alarms ---
    elif intent == "ALARM_SET":
        return "अलार्म सेट कर दिया गया है।"
        
    elif intent == "REMINDER_SET":
        return "ठीक है, मैं आपको याद दिला दूँगी।"
        
    elif intent == "ALARM_STOP":
        return "अलार्म बंद कर दिया गया है।"
        
    # --- Translation ---
    elif intent == "TRANSLATE_ASK":
        return "माफ़ कीजिए, मेरा अनुवाद सिस्टम अभी ऑफ़लाइन है।"
        
    # --- Fallbacks ---
    elif intent == "UNKNOWN_COMMAND":
        return "माफ़ कीजिए, मुझे समझ नहीं आया।"
        
    else:
        # Developer fallback for missing intents
        return "मैंने कमांड समझ लिया है, लेकिन जवाब देना नहीं आता।"
def ask_ollama_translator(text_to_translate):
    """Uses Qwen 3B purely for linguistic translation."""
    url = "http://localhost:11434/api/generate"
    
    # We force the LLM to act ONLY as a translator, outputting pure Hindi
    system_prompt = "You are an expert offline language translator. Translate the user's input into natural, conversational Hindi. Output ONLY the Hindi translation. Do not explain anything."
    
    payload = {
        "model": "qwen2.5:3b", # The intelligent linguistic model
        "prompt": f"{system_prompt}\nUser: {text_to_translate}",
        "stream": False
    }
    
    try:
        # 60-second timeout to give the 3B model time to boot into the GPU
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['response']
        else:
            return "माफ़ कीजिए, मेरे अनुवाद सिस्टम में कुछ खराबी है।"
    except requests.exceptions.ConnectionError:
        return "माफ़ कीजिए, मेरा लोकल सर्वर अभी बंद है।"
    except requests.exceptions.ReadTimeout:
        return "माफ़ कीजिए, मुझे अनुवाद करने में बहुत समय लग रहा है।"
# ==========================================
# 1. INITIALIZE ALL AI MODELS
# ==========================================
print("Loading Vosk Acoustic Model (Ears)...")
model = Model("model")

# THE UPGRADE: Two Recognizers sharing the same brain
# 1. The Bouncer: Only knows how to listen for the wake word
wake_word_grammar = '["नमस्ते", "सुनो", "[unk]"]'
wake_recognizer = KaldiRecognizer(model, 16000, wake_word_grammar)

# 2. The Command Listener: Knows the whole Hindi dictionary
main_recognizer = KaldiRecognizer(model, 16000)

print("Loading Intent Parser (Brain)... Done.")
print("Loading Piper TTS Engine (Voice)... Done.")

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)

print("\n" + "="*50)
print("🟢 SOVEREIGN SENTRY: ONLINE & AIR-GAPPED")
print("Say 'Namaste' or 'Suno' to wake me up.")
print("Press Ctrl+C to shut down.")
print("="*50 + "\n")

# State tracking
is_awake = False

try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        
        # ==========================================
        # STATE 1: SLEEPING (Listening for Wake Word)
        # ==========================================
        if not is_awake:
            if wake_recognizer.AcceptWaveform(data):
                result = json.loads(wake_recognizer.Result())
                text = result.get('text', '')
                
                if "नमस्ते" in text or "सुनो" in text:
                    print("\n🔔 [Wake Word Detected]: Waking up system...")
                    speak_hindi("हाँ क्वार्क, बताइये?") # "Yes Quark, tell me?"
                    
                    # Switch state and flush the audio buffer
                    is_awake = True
                    stream.stop_stream()
                    stream.start_stream()
                    print("Listening for command...")

        # ==========================================
        # STATE 2: AWAKE (Listening for Command)
        # ==========================================
      
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
                        
                        # 1. THE GARBAGE & HALLUCINATION FILTER
                        if detected_intent == "UNKNOWN_COMMAND":
                            word_count = len(phrase.split())
                            if word_count > 2:
                                # They asked a trivia question. Reject it to prevent LLM hallucinations.
                                print("🛑 [Router]: Rejecting trivia to stay in Smart Home/Translator mode.")
                                combined_replies.append("माफ़ कीजिए, मैं केवल घर के उपकरणों को नियंत्रित कर सकती हूँ या अनुवाद कर सकती हूँ।")
                            else:
                                # It was just static/garbage audio
                                print("🛑 [Router]: Discarding garbage audio.")
                                combined_replies.append("माफ़ कीजिए, मुझे स्पष्ट सुनाई नहीं दिया।") 

                        # 2. THE NEW INTELLIGENT TRANSLATOR
                        elif detected_intent == "TRANSLATE_ASK":
                            print("🌐 [Router]: Translation request detected. Faking latency with audio cue...")
                            
                            # UX Hack: Buy time while the 3B model loads into the GPU
                            stream.stop_stream()
                            speak_hindi("मैं अनुवाद कर रही हूँ...") # "I am translating..."
                            stream.start_stream()
                            
                            print("🧠 [LLM]: Qwen 3B is translating...")
                            translated_text = ask_ollama_translator(phrase)
                            combined_replies.append(translated_text)
                            
                        # 3. STANDARD SMART HOME COMMANDS (Lights, Fan, Alarm, Time)
                        else:
                            reply_text = generate_response(detected_intent)
                            combined_replies.append(reply_text)
                            
                    # Combine and speak
                    final_spoken_response = " ".join(combined_replies)
                    print(f"🤖 [Assistant]: {final_spoken_response}")
                    
                    if final_spoken_response.strip(): # Only speak if there is actual text
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