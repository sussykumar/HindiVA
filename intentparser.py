import re
from rapidfuzz import process, fuzz

# ==========================================
# TIER 0: COMPREHENSIVE COMMAND TAXONOMY
# Synthesized from Home Automation, Time, Weather, and Reminders domains
# ==========================================
# ==========================================
# TIER 0: DEVANAGARI COMMAND TAXONOMY (EXPANDED)
# ==========================================
COMMAND_REGISTRY = {
    # Home Automation (Ghar Swachalan)
    "LIGHT_ON": [
        "बत्ती जलाओ", "लाइट ऑन करो", "बत्ती ऑन करो", "रोशनी करो", 
        "लाइट चालू करो", "ट्यूबलाइट जला दो", "बैठक की लाइट जलाओ", 
        "लिविंग रूम की लाइट ऑन करो", "लाइट जला दो", "बत्ती चालू करो",
        "बत्ती जला दो", "लाइट ऑन कर दो", "अंधेरा दूर करो"
    ],
    "LIGHT_OFF": [
        "बत्ती बुझाओ", "लाइट ऑफ करो", "बत्ती बंद करो", "अंधेरा करो", 
        "लाइट बंद कर दो", "सब कुछ बंद करो", "सब ऑफ कर दो", "बत्ती बंद कर दो",
        "लाइट बंद करो", "बत्तियां बुझा दो", "लाइट बुझा दो"
    ],
    "FAN_ON": [
        "पंखा चलाओ", "फैन ऑन कर दो", "पंखा चालू करो", "पंखा ऑन करो", 
        "फैन चालू करो", "पंखा चला दो"
    ],
    "FAN_OFF": [
        "पंखा बंद करो", "फैन ऑफ करो", "पंखा बंद कर दो", "फैन बंद करो", 
        "पंखा ऑफ कर दो"
    ],
    "AC_ON": [
        "वातानुकूलक चलाओ", "एसी ऑन करना", "एसी चला दो", "एसी चालू करो", 
        "एसी ऑन करो"
    ],
    
    # Time and Date (Samay aur Tarikh)
    "TIME_ASK": [
        "समय क्या है", "टाइम बताओ", "कितने बजे हैं", "टाइम क्या हुआ", 
        "घड़ी में क्या टाइम है", "टाइम क्या है", "अभी क्या समय हो रहा है", 
        "अभी टाइम क्या हो रहा है", "क्या बजा है", "समय क्या हो", "समझी"
    ],
    
    "DATE_ASK": [
        "आज क्या तारीख है", "आज की डेट क्या है", "आज कौन सी तारीख है",
        "कल क्या तारीख होगी", "कल की डेट क्या है", "आज कितनी तारीख है",
        "आज कौन सा दिनांक है"
    ],
    "DAY_ASK": [
        "आज कौन सा दिन है", "आज कौन सा डे है", "आज क्या दिन है", "आज कौन वार है"
    ],

    # Temperature and Weather (Tapman aur Mausam)
    "WEATHER_ASK": [
        "मौसम कैसा है", "आज का मौसम कैसा है", "आज वेदर कैसा है", 
        "मौसम का हाल बताओ", "बाहर का मौसम", "कल का मौसम कैसा रहेगा",
        "क्या आज मौसम साफ है", "बाहर मौसम कैसा है"
    ],
    "TEMP_ASK": [
        "तापमान बताओ", "बाहर तापमान क्या है", "बाहर कितना टेंपरेचर है", 
        "गर्मी कितनी है", "कमरे का तापमान बताओ", "रूम टेंपरेचर क्या है",
        "आज कितनी गर्मी है", "टेंपरेचर बताओ"
    ],
    "RAIN_ASK": [
        "आज की बारिश", "क्या आज बारिश होगी", "रेन के चांसेस हैं क्या", 
        "क्या बारिश होने वाली है", "बारिश होगी क्या"
    ],

    # Reminders and Alarms (Yaad-dihani aur Alarm)
    "ALARM_SET": [
        "अलार्म लगाओ", "अलार्म सेट करो", "उठा देना", "अलार्म लगा दो", "मुझे जगा देना"
    ],
    "REMINDER_SET": [
        "याद दिलाना", "रिमाइंडर सेट करो", "मुझे याद दिलाओ", "रिमाइंड मी", "रिमाइंडर लगाओ"
    ],
    "ALARM_STOP": [
        "अलार्म बंद करो", "स्टॉप इट", "चुप हो जाओ", "बंद करो", "अलार्म रोक दो"
    ],
    
    # Translation (Anuvaad)
    "TRANSLATE_ASK": [
        "हिंदी में क्या कहते हैं", "का अनुवाद करो", "ट्रांसलेट करो", 
        "मतलब क्या होता है", "मीनिंग क्या है", "को हिंदी में क्या बोलते हैं"
    ]
}

# ==========================================
# TIER 1: NORMALIZATION
# ==========================================
def normalize_text(text):
    """
    Normalize Hindi/Hinglish text: remove punctuation, extra spaces.
    Unicode range \u0900-\u097F safely covers the Devanagari script.
    """
    # Remove common punctuation, keeping alphanumeric and Devanagari
    text = re.sub(r'[^\w\s\u0900-\u097F]', '', text)
    return text.lower().strip()

# ==========================================
# TIER 2 & 3: THE WATERFALL PARSER
# ==========================================
def split_commands(text):
    """Splits a single Hindi sentence into multiple commands based on conjunctions."""
    # Split by 'aur' (और), 'tatha' (तथा), or 'phir' (फिर)
    parts = re.split(r'\s+(और|तथा|फिर)\s+', text)
    
    # Filter out the conjunction words themselves, keeping only the action phrases
    commands = [p.strip() for p in parts if p.strip() not in ['और', 'तथा', 'फिर'] and p.strip()]
    return commands

def parse_multiple_intents(text):
    """Returns a list of intent dictionaries for a compound sentence."""
    normalized_text = normalize_text(text)
    command_phrases = split_commands(normalized_text)
    
    results = []
    for phrase in command_phrases:
        best_match = None
        highest_score = 0
        
        # Run RapidFuzz on each chopped phrase
        for intent, phrases in COMMAND_REGISTRY.items():
            match = process.extractOne(phrase, phrases, scorer=fuzz.token_set_ratio)
            if match:
                score = match[1]
                if score > highest_score:
                    highest_score = score
                    best_match = intent
                    
        if highest_score >= 85:  # 70% confidence threshold
            results.append({"intent": best_match, "confidence": round(highest_score, 2), "phrase": phrase})
        else:
            results.append({"intent": "UNKNOWN_COMMAND", "confidence": round(highest_score, 2), "phrase": phrase})
            
    return results

    # ---------------------------------------------------------
    # TIER 3: Fuzzy Matching (Handles ASR acoustic errors / typos)
    # ---------------------------------------------------------
    all_phrases = []
    phrase_to_intent = {}
    
    # Flatten the registry for the fuzzy engine
    for intent, phrases in COMMAND_REGISTRY.items():
        for p in phrases:
            all_phrases.append(p)
            phrase_to_intent[p] = intent
            
    # extractOne finds the single best match from the flattened list.
    # token_set_ratio is mathematically ideal for Hinglish as it ignores word order.
    # e.g., "karo light on" will heavily match "light on karo".
    best_match, score, _ = process.extractOne(
        clean_text, all_phrases, scorer=fuzz.token_set_ratio
    )
    
    # 80% is the recommended threshold for command-and-control voice applications
    if score > 80:
        detected_intent = phrase_to_intent[best_match]
        return {
            "intent": detected_intent, 
            "confidence": round(score, 2), 
            "match_type": "fuzzy_probabilistic",
            "matched_phrase": best_match
        }
                
    # ---------------------------------------------------------
    # TIER 4: Semantic Fallback
    # (To be routed to a quantized SLM or handled as an error)
    # ---------------------------------------------------------
    return {
        "intent": "UNKNOWN_COMMAND", 
        "confidence": 0.0, 
        "match_type": "none",
        "matched_phrase": None
    }

# ==========================================
# LOCAL TESTING BLOCK
# ==========================================
if __name__ == "__main__":
    print("🧠 Tiered NLU Intent Parser Initialized.")
    print("Ready for testing. Type 'exit' to quit.\n")
    
    # Test cases demonstrating Hinglish variation, exact matches, and fuzzy matches
    test_queries = [
        "living room ki light on karo", # Exact match
        "karo light on living room ki", # Out of order (Fuzzy token_set_ratio)
        "aaj ka mosam kaisa hai",       # ASR transcription error (mosam vs mausam)
        "batti band kar do jaldi",      # Exact match with extra words
        "mujhe kal subah utha dena",    # Exact match for alarm
        "what is the meaning of life"   # Unknown command
    ]
    
    for query in test_queries:
        print(f"🗣️ Input: '{query}'")
        result = parse_multiple_intents(query)
        print(f"   ↳ Result: {result}\n")