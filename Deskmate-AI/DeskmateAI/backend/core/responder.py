# DeskmateAI/backend/core/responder.py

import os
import sys
import threading

# ============================================================
# RESPONDER FOR DESKMATEAI
# Handles all text-to-speech responses
# Responds in user's chosen language
# Uses pyttsx3 - fully offline
# Runs in separate thread so it never blocks pipeline
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Response Templates ────────────────────────────────────────

RESPONSES = {
    "en": {
        # App control
        "opening_app":          "Opening {entity}",
        "closing_app":          "Closing {entity}",
        "app_not_found":        "Could not find {entity}",

        # Volume
        "volume_up":            "Volume increased",
        "volume_down":          "Volume decreased",
        "muted":                "Audio muted",
        "unmuted":              "Audio unmuted",
        "volume_set":           "Volume set to {entity} percent",

        # Brightness
        "brightness_up":        "Brightness increased",
        "brightness_down":      "Brightness decreased",
        "brightness_set":       "Brightness set to {entity} percent",

        # System
        "shutting_down":        "Shutting down the system",
        "restarting":           "Restarting the system",
        "sleeping":             "Going to sleep",
        "locking":              "Locking the screen",

        # Search
        "searching":            "Searching for {entity}",

        # Media
        "playing":              "Playing",
        "pausing":              "Pausing",
        "next_track":           "Next track",
        "previous_track":       "Previous track",

        # Window
        "minimizing":           "Minimizing window",
        "maximizing":           "Maximizing window",
        "closing_window":       "Closing window",
        "switching_window":     "Switching window",

        # Screenshot
        "screenshot_taken":     "Screenshot taken",

        # Dictation
        "dictation_start":      "Listening for dictation. Speak now",
        "dictation_done":       "Text written",
        "dictation_cancelled":  "Dictation cancelled",

        # Scroll
        "scrolling_up":         "Scrolling up",
        "scrolling_down":       "Scrolling down",

        # Undo Redo
        "undone":               "Action undone",
        "redone":               "Action redone",
        "nothing_to_undo":      "Nothing to undo",
        "nothing_to_redo":      "Nothing to redo",
        "cannot_undo":          "This action cannot be undone",

        # Auth
        "welcome":              "Welcome {entity}",
        "goodbye":              "Goodbye {entity}",
        "unauthorized":         "Unauthorized access detected",
        "auth_failed":          "Authentication failed",

        # Errors
        "not_understood":       "Sorry, I did not understand that",
        "command_failed":       "Command failed. Please try again",
        "low_confidence":       "I am not sure what you meant",
        "out_of_scope":         "Sorry, I cannot do that",

        # Wake word
        "wake_word_detected":   "Yes, I am listening",
        "ready":                "Deskmate AI is ready",

        # Copy paste
        "copied":               "Text copied",
        "pasted":               "Text pasted",
        "selected_all":         "All text selected",

        # File
        "file_saved":           "File saved",
        "new_tab_opened":       "New tab opened",
        "tab_closed":           "Tab closed",

        # Zoom
        "zoomed_in":            "Zoomed in",
        "zoomed_out":           "Zoomed out",

        # Click
        "clicked":              "Clicked {entity}",
        "element_not_found":    "Could not find {entity} on screen",

        # Custom
        "done":                 "Done",
        "ok":                   "Okay",
        "error":                "Something went wrong",
    },

    "hi": {
        # App control
        "opening_app":          "{entity} खोल रहा हूं",
        "closing_app":          "{entity} बंद कर रहा हूं",
        "app_not_found":        "{entity} नहीं मिला",

        # Volume
        "volume_up":            "आवाज़ बढ़ा दी",
        "volume_down":          "आवाज़ कम कर दी",
        "muted":                "आवाज़ बंद कर दी",
        "unmuted":              "आवाज़ चालू कर दी",
        "volume_set":           "आवाज़ {entity} प्रतिशत कर दी",

        # Brightness
        "brightness_up":        "चमक बढ़ा दी",
        "brightness_down":      "चमक कम कर दी",
        "brightness_set":       "चमक {entity} प्रतिशत कर दी",

        # System
        "shutting_down":        "सिस्टम बंद हो रहा है",
        "restarting":           "सिस्टम पुनः शुरू हो रहा है",
        "sleeping":             "स्लीप मोड में जा रहा है",
        "locking":              "स्क्रीन लॉक हो रही है",

        # Search
        "searching":            "{entity} खोज रहा हूं",

        # Media
        "playing":              "चला रहा हूं",
        "pausing":              "रोक रहा हूं",
        "next_track":           "अगला गाना",
        "previous_track":       "पिछला गाना",

        # Window
        "minimizing":           "विंडो छोटी कर रहा हूं",
        "maximizing":           "विंडो बड़ी कर रहा हूं",
        "closing_window":       "विंडो बंद कर रहा हूं",
        "switching_window":     "विंडो बदल रहा हूं",

        # Screenshot
        "screenshot_taken":     "स्क्रीनशॉट लिया",

        # Dictation
        "dictation_start":      "बोलिए, मैं सुन रहा हूं",
        "dictation_done":       "टेक्स्ट लिख दिया",
        "dictation_cancelled":  "डिक्टेशन रद्द",

        # Scroll
        "scrolling_up":         "ऊपर स्क्रॉल कर रहा हूं",
        "scrolling_down":       "नीचे स्क्रॉल कर रहा हूं",

        # Undo Redo
        "undone":               "कार्य वापस किया",
        "redone":               "कार्य दोबारा किया",
        "nothing_to_undo":      "वापस करने के लिए कुछ नहीं",
        "nothing_to_redo":      "दोबारा करने के लिए कुछ नहीं",
        "cannot_undo":          "यह कार्य वापस नहीं हो सकता",

        # Auth
        "welcome":              "स्वागत है {entity}",
        "goodbye":              "अलविदा {entity}",
        "unauthorized":         "अनधिकृत पहुंच का पता चला",
        "auth_failed":          "प्रमाणीकरण विफल",

        # Errors
        "not_understood":       "माफ़ करें, समझ नहीं आया",
        "command_failed":       "कमांड विफल। कृपया पुनः प्रयास करें",
        "low_confidence":       "मुझे समझ नहीं आया",
        "out_of_scope":         "माफ़ करें, यह मेरे लिए संभव नहीं",

        # Wake word
        "wake_word_detected":   "जी, मैं सुन रहा हूं",
        "ready":                "डेस्कमेट AI तैयार है",

        # Copy paste
        "copied":               "टेक्स्ट कॉपी हुआ",
        "pasted":               "टेक्स्ट पेस्ट हुआ",
        "selected_all":         "सभी टेक्स्ट चुना",

        # File
        "file_saved":           "फाइल सेव हुई",
        "new_tab_opened":       "नया टैब खुला",
        "tab_closed":           "टैब बंद हुआ",

        # Zoom
        "zoomed_in":            "ज़ूम इन हुआ",
        "zoomed_out":           "ज़ूम आउट हुआ",

        # Click
        "clicked":              "{entity} क्लिक किया",
        "element_not_found":    "स्क्रीन पर {entity} नहीं मिला",

        # Custom
        "done":                 "हो गया",
        "ok":                   "ठीक है",
        "error":                "कुछ गलत हुआ",
    },

    "mr": {
        # App control
        "opening_app":          "{entity} उघडत आहे",
        "closing_app":          "{entity} बंद करत आहे",
        "app_not_found":        "{entity} सापडले नाही",

        # Volume
        "volume_up":            "आवाज वाढवली",
        "volume_down":          "आवाज कमी केली",
        "muted":                "आवाज बंद केली",
        "unmuted":              "आवाज सुरू केली",
        "volume_set":           "आवाज {entity} टक्के केली",

        # Brightness
        "brightness_up":        "प्रकाश वाढवला",
        "brightness_down":      "प्रकाश कमी केला",
        "brightness_set":       "प्रकाश {entity} टक्के केला",

        # System
        "shutting_down":        "सिस्टम बंद होत आहे",
        "restarting":           "सिस्टम पुन्हा सुरू होत आहे",
        "sleeping":             "झोप मोडमध्ये जात आहे",
        "locking":              "स्क्रीन लॉक होत आहे",

        # Search
        "searching":            "{entity} शोधत आहे",

        # Media
        "playing":              "चालवत आहे",
        "pausing":              "थांबवत आहे",
        "next_track":           "पुढचे गाणे",
        "previous_track":       "मागचे गाणे",

        # Window
        "minimizing":           "विंडो लहान करत आहे",
        "maximizing":           "विंडो मोठी करत आहे",
        "closing_window":       "विंडो बंद करत आहे",
        "switching_window":     "विंडो बदलत आहे",

        # Screenshot
        "screenshot_taken":     "स्क्रीनशॉट घेतला",

        # Dictation
        "dictation_start":      "बोला, मी ऐकतो आहे",
        "dictation_done":       "मजकूर लिहिला",
        "dictation_cancelled":  "डिक्टेशन रद्द",

        # Scroll
        "scrolling_up":         "वर स्क्रोल करत आहे",
        "scrolling_down":       "खाली स्क्रोल करत आहे",

        # Undo Redo
        "undone":               "क्रिया परत केली",
        "redone":               "क्रिया पुन्हा केली",
        "nothing_to_undo":      "परत करण्यासाठी काही नाही",
        "nothing_to_redo":      "पुन्हा करण्यासाठी काही नाही",
        "cannot_undo":          "ही क्रिया परत होऊ शकत नाही",

        # Auth
        "welcome":              "स्वागत आहे {entity}",
        "goodbye":              "निरोप {entity}",
        "unauthorized":         "अनधिकृत प्रवेश आढळला",
        "auth_failed":          "प्रमाणीकरण अयशस्वी",

        # Errors
        "not_understood":       "माफ करा, समजले नाही",
        "command_failed":       "आदेश अयशस्वी. कृपया पुन्हा प्रयत्न करा",
        "low_confidence":       "मला नक्की समजले नाही",
        "out_of_scope":         "माफ करा, हे मला शक्य नाही",

        # Wake word
        "wake_word_detected":   "होय, मी ऐकतो आहे",
        "ready":                "डेस्कमेट AI तयार आहे",

        # Copy paste
        "copied":               "मजकूर कॉपी झाला",
        "pasted":               "मजकूर पेस्ट झाला",
        "selected_all":         "सर्व मजकूर निवडला",

        # File
        "file_saved":           "फाइल सेव्ह झाली",
        "new_tab_opened":       "नवीन टॅब उघडला",
        "tab_closed":           "टॅब बंद झाला",

        # Zoom
        "zoomed_in":            "झूम इन झाला",
        "zoomed_out":           "झूम आउट झाला",

        # Click
        "clicked":              "{entity} क्लिक केले",
        "element_not_found":    "स्क्रीनवर {entity} सापडले नाही",

        # Custom
        "done":                 "झाले",
        "ok":                   "ठीक आहे",
        "error":                "काहीतरी चुकले",
    }
}

# ── Responder Class ───────────────────────────────────────────

class Responder:

    def __init__(self):
        # print("[RESPONDER] Initializing Responder...")
        self._engine = None
        self._current_language = 'en'
        self._enabled = True
        self._speaking = False
        self._init_engine()
        log_info("Responder initialized")

    def _init_engine(self):
        """Initialize pyttsx3 engine"""
        # print("[RESPONDER] Initializing TTS engine...")
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 175)    # Speed
            self._engine.setProperty('volume', 1.0)  # Volume

            # Try to set a good voice
            voices = self._engine.getProperty('voices')
            # print(f"[RESPONDER] Available voices: {len(voices)}")

            # Prefer female voice for English
            for voice in voices:
                if 'english' in voice.name.lower() or 'zira' in voice.name.lower():
                    self._engine.setProperty('voice', voice.id)
                    # print(f"[RESPONDER] Voice set: {voice.name}")
                    break

            log_info("TTS engine initialized")
            # print("[RESPONDER] TTS engine ready")

        except Exception as e:
            # print(f"[RESPONDER] Error initializing TTS: {e}")
            log_error(f"Error initializing TTS engine: {e}")
            self._engine = None

    def set_language(self, language_code):
        """Set current language for responses"""
        # print(f"[RESPONDER] Language set to: {language_code}")
        if language_code in RESPONSES:
            self._current_language = language_code
            self._try_set_language_voice(language_code)
        else:
            self._current_language = 'en'

    def _try_set_language_voice(self, language_code):
        """Try to set voice for given language"""
        # print(f"[RESPONDER] Trying to set voice for: {language_code}")
        if not self._engine:
            return
        try:
            voices = self._engine.getProperty('voices')
            lang_voice_map = {
                'hi': ['hindi', 'hemant', 'kalpana'],
                'mr': ['marathi'],
                'en': ['english', 'zira', 'david']
            }
            preferred = lang_voice_map.get(language_code, ['english'])
            for voice in voices:
                for pref in preferred:
                    if pref in voice.name.lower():
                        self._engine.setProperty('voice', voice.id)
                        # print(f"[RESPONDER] Voice found for {language_code}: {voice.name}")
                        return
            # print(f"[RESPONDER] No specific voice for {language_code}, using default")
        except Exception as e:
            # print(f"[RESPONDER] Error setting voice: {e}")
            log_error(f"Error setting voice: {e}")

    def get_response_text(self, response_key, entity=None, language=None):
        """Get response text in correct language"""
        # print(f"[RESPONDER] Getting response: {response_key} | entity: {entity}")
        lang = language or self._current_language
        if lang not in RESPONSES:
            lang = 'en'

        template = RESPONSES[lang].get(response_key)
        if not template:
            template = RESPONSES['en'].get(response_key, "Done")

        if entity and '{entity}' in template:
            return template.replace('{entity}', str(entity))
        return template

    def speak(self, response_key, entity=None, language=None):
        """
        Speak response in background thread
        Never blocks the pipeline
        """
        # print(f"[RESPONDER] Speaking: {response_key}")
        if not self._enabled:
            return

        text = self.get_response_text(response_key, entity, language)
        # print(f"[RESPONDER] Text to speak: {text}")
        log_debug(f"Speaking: {text}")

        # Run in background thread
        thread = threading.Thread(
            target=self._speak_text,
            args=(text,),
            daemon=True
        )
        thread.start()

    def speak_text(self, text):
        """
        Speak any custom text directly
        Runs in background thread
        """
        # print(f"[RESPONDER] Speaking text: {text}")
        if not self._enabled or not text:
            return
        log_debug(f"Speaking custom text: {text}")
        thread = threading.Thread(
            target=self._speak_text,
            args=(text,),
            daemon=True
        )
        thread.start()

    def _speak_text(self, text):
        """Internal - runs in thread"""
        # print(f"[RESPONDER] TTS thread started: {text}")
        try:
            if not self._engine:
                self._init_engine()
            if self._engine:
                self._speaking = True
                self._engine.say(text)
                self._engine.runAndWait()
                self._speaking = False
                # print(f"[RESPONDER] TTS done: {text}")
        except Exception as e:
            self._speaking = False
            # print(f"[RESPONDER] TTS error: {e}")
            log_error(f"TTS error: {e}")

    def is_speaking(self):
        return self._speaking

    def enable(self):
        """Enable TTS"""
        # print("[RESPONDER] TTS enabled")
        self._enabled = True

    def disable(self):
        """Disable TTS"""
        # print("[RESPONDER] TTS disabled")
        self._enabled = False

    def is_enabled(self):
        return self._enabled

    def set_rate(self, rate):
        """Set speech rate"""
        # print(f"[RESPONDER] Setting rate: {rate}")
        if self._engine:
            self._engine.setProperty('rate', rate)

    def set_volume(self, volume):
        """Set TTS volume 0.0 to 1.0"""
        # print(f"[RESPONDER] Setting TTS volume: {volume}")
        if self._engine:
            self._engine.setProperty('volume', volume)

    def get_available_voices(self):
        """Get list of available voices"""
        # print("[RESPONDER] Getting available voices...")
        if not self._engine:
            return []
        try:
            voices = self._engine.getProperty('voices')
            return [{"id": v.id, "name": v.name} for v in voices]
        except Exception as e:
            # print(f"[RESPONDER] Error getting voices: {e}")
            log_error(f"Error getting voices: {e}")
            return []

    def stop(self):
        """Stop current speech"""
        # print("[RESPONDER] Stopping speech...")
        try:
            if self._engine and self._speaking:
                self._engine.stop()
                self._speaking = False
        except Exception as e:
            # print(f"[RESPONDER] Error stopping speech: {e}")
            log_error(f"Error stopping speech: {e}")


# ── Singleton Instance ────────────────────────────────────────

_responder = None

def get_responder():
    global _responder
    if _responder is None:
        # print("[RESPONDER] Creating singleton Responder...")
        _responder = Responder()
    return _responder