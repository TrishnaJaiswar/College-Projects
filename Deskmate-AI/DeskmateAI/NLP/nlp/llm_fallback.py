# DeskmateAI/NLP/nlp/llm_fallback.py

import os
import sys
import time
import json

# ============================================================
# LLM FALLBACK FOR DESKMATEAI
# Called when SBERT confidence is below threshold
# Uses locally running Ollama phi3.5 model
# Completely offline - no internet needed
# Returns structured intent classification
# Result saved to intent memory for future SBERT use
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Constants ─────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3.5"
OLLAMA_TIMEOUT = 30      # seconds
MAX_TOKENS = 50          # Short response needed
UNKNOWN_INTENT = "unknown"

# ── LLM Fallback Class ────────────────────────────────────────

class LLMFallback:

    def __init__(self):
        # print("[LLM] Initializing LLMFallback...")
        self._available = None  # None = not checked yet
        self._intent_list = []
        log_info("LLMFallback initialized")

    def _check_ollama_available(self):
        """Check if Ollama is running"""
        # print("[LLM] Checking Ollama availability...")
        try:
            import requests
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=3
            )
            available = response.status_code == 200
            # print(f"[LLM] Ollama available: {available}")
            log_debug(f"Ollama available: {available}")
            return available
        except Exception as e:
            # print(f"[LLM] Ollama not available: {e}")
            log_warning(f"Ollama not available: {e}")
            return False

    def _ensure_model_available(self):
        """Check if phi3.5 model is pulled"""
        # print("[LLM] Checking phi3.5 model...")
        try:
            import requests
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=3
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                # print(f"[LLM] Available models: {model_names}")
                for name in model_names:
                    if 'phi3.5' in name or 'phi3' in name:
                        # print(f"[LLM] ✅ phi3.5 model found: {name}")
                        log_debug(f"phi3.5 model found: {name}")
                        return True
                # print("[LLM] phi3.5 not found in available models")
                log_warning("phi3.5 model not found. Run: ollama pull phi3.5")
                return False
        except Exception as e:
            # print(f"[LLM] Model check error: {e}")
            log_error(f"Model check error: {e}")
            return False

    def _build_prompt(self, command, available_intents):
        """
        Build classification prompt for LLM
        Clear and structured for best results
        """
        intents_str = ", ".join(available_intents)

        prompt = f"""You are a voice command classifier for a desktop assistant.
Classify the following command into exactly one intent from the list.

Command: "{command}"

Available intents: {intents_str}

Rules:
- Return ONLY the intent name, nothing else
- No explanation, no punctuation, no extra words
- If no intent matches, return: unknown
- Must be one of the available intents or unknown

Intent:"""

        return prompt

    def _parse_response(self, response_text, available_intents):
        """
        Parse LLM response to extract intent
        Handles various response formats
        """
        # print(f"[LLM] Parsing response: '{response_text}'")

        if not response_text:
            return UNKNOWN_INTENT

        # Clean response
        cleaned = response_text.strip().lower()

        # Remove common prefixes LLM might add
        prefixes_to_remove = [
            "intent:", "the intent is", "answer:",
            "classification:", "result:", "output:"
        ]
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()

        # Remove punctuation
        cleaned = cleaned.strip('.,!?:;"\' ')

        # Check exact match
        if cleaned in available_intents:
            # print(f"[LLM] Exact match: '{cleaned}'")
            return cleaned

        # Check if unknown
        if cleaned == UNKNOWN_INTENT or 'unknown' in cleaned:
            return UNKNOWN_INTENT

        # Check partial match
        for intent in available_intents:
            if intent in cleaned or cleaned in intent:
                # print(f"[LLM] Partial match: '{cleaned}' → '{intent}'")
                return intent

        # print(f"[LLM] No match found for: '{cleaned}'")
        return UNKNOWN_INTENT

    def classify(self, command, available_intents=None):
        """
        Classify command using local Ollama LLM
        Returns (intent, confidence)
        Called when SBERT confidence is low
        """
        # print(f"[LLM] Classifying: '{command}'")
        log_info(f"LLM classifying: '{command}'")

        if not command or not command.strip():
            return UNKNOWN_INTENT, 0.0

        # Load available intents if not provided
        if available_intents is None:
            available_intents = self._get_available_intents()

        if not available_intents:
            log_warning("No intents available for LLM classification")
            return UNKNOWN_INTENT, 0.0

        # Check Ollama available
        if not self._check_ollama_available():
            # print("[LLM] Ollama not running")
            log_warning("Ollama not running - cannot classify")
            return UNKNOWN_INTENT, 0.0

        try:
            import requests

            # Build prompt
            prompt = self._build_prompt(command, available_intents)
            # print(f"[LLM] Prompt built, calling Ollama...")

            start_time = time.time()

            # Call Ollama API
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,    # Deterministic
                        "top_p": 1.0,
                        "num_predict": MAX_TOKENS,
                        "stop": ["\n", ".", "Command", "Available"]
                    }
                },
                timeout=OLLAMA_TIMEOUT
            )

            elapsed = time.time() - start_time
            # print(f"[LLM] Ollama response in {elapsed:.3f}s")

            if response.status_code != 200:
                # print(f"[LLM] Ollama error: {response.status_code}")
                log_error(f"Ollama error: {response.status_code}")
                return UNKNOWN_INTENT, 0.0

            # Parse response
            result = response.json()
            response_text = result.get('response', '').strip()
            # print(f"[LLM] Raw response: '{response_text}'")

            # Extract intent
            intent = self._parse_response(response_text, available_intents)

            if intent != UNKNOWN_INTENT:
                # print(f"[LLM] ✅ Classified: '{command}' → '{intent}' ({elapsed:.3f}s)")
                log_info(f"LLM classified: '{command}' → '{intent}' ({elapsed:.3f}s)")
                return intent, 0.85  # LLM confidence is high when it finds a match
            else:
                # print(f"[LLM] Unknown intent for: '{command}'")
                log_warning(f"LLM returned unknown for: '{command}'")
                return UNKNOWN_INTENT, 0.0

        except requests.exceptions.Timeout:
            # print(f"[LLM] Ollama timeout after {OLLAMA_TIMEOUT}s")
            log_error(f"Ollama timeout after {OLLAMA_TIMEOUT}s")
            return UNKNOWN_INTENT, 0.0

        except requests.exceptions.ConnectionError:
            # print("[LLM] Cannot connect to Ollama")
            log_error("Cannot connect to Ollama - is it running?")
            return UNKNOWN_INTENT, 0.0

        except Exception as e:
            # print(f"[LLM] Classification error: {e}")
            log_error(f"LLM classification error: {e}")
            return UNKNOWN_INTENT, 0.0

    def classify_free_form(self, command):
        """
        Free form classification
        LLM decides intent AND action without constraints
        Used for completely unknown commands
        Returns (intent_name, action_description)
        """
        # print(f"[LLM] Free form classification: '{command}'")
        log_info(f"LLM free form: '{command}'")

        if not self._check_ollama_available():
            return UNKNOWN_INTENT, ""

        try:
            import requests

            prompt = f"""You are a desktop assistant. The user said: "{command}"

What desktop action should be performed?
Respond in this exact format:
INTENT: <short_intent_name_with_underscores>
ACTION: <brief description of what to do>

Response:"""

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 100
                    }
                },
                timeout=OLLAMA_TIMEOUT
            )

            if response.status_code == 200:
                text = response.json().get('response', '')
                # print(f"[LLM] Free form response: '{text}'")

                # Parse INTENT and ACTION
                intent = UNKNOWN_INTENT
                action = ""

                for line in text.split('\n'):
                    line = line.strip()
                    if line.startswith('INTENT:'):
                        intent = line.replace('INTENT:', '').strip().lower()
                        intent = intent.replace(' ', '_')
                    elif line.startswith('ACTION:'):
                        action = line.replace('ACTION:', '').strip()

                # print(f"[LLM] Free form: intent='{intent}' action='{action}'")
                log_info(f"LLM free form: '{intent}' | '{action}'")
                return intent, action

        except Exception as e:
            # print(f"[LLM] Free form error: {e}")
            log_error(f"LLM free form error: {e}")

        return UNKNOWN_INTENT, ""

    def _get_available_intents(self):
        """Get list of available intents from registry"""
        # print("[LLM] Getting available intents...")
        try:
            from backend.core.registry import get_registry
            registry = get_registry()
            intents = registry.get_all_intents()
            self._intent_list = intents
            # print(f"[LLM] Available intents: {len(intents)}")
            return intents
        except Exception as e:
            # print(f"[LLM] Get intents error: {e}")
            log_error(f"Get available intents error: {e}")
            return []

    def is_available(self):
        """Check if LLM fallback is available"""
        # print("[LLM] Checking availability...")
        ollama_running = self._check_ollama_available()
        if ollama_running:
            model_ready = self._ensure_model_available()
            # print(f"[LLM] Available: {model_ready}")
            return model_ready
        return False

    def get_status(self):
        """Get LLM fallback status"""
        ollama_running = self._check_ollama_available()
        return {
            "ollama_running": ollama_running,
            "model": OLLAMA_MODEL,
            "url": OLLAMA_URL,
            "timeout": OLLAMA_TIMEOUT,
            "available": ollama_running and self._ensure_model_available() if ollama_running else False
        }

    def warm_up(self):
        """
        Warm up LLM model
        Sends test query to load model into RAM
        Reduces latency on first real call
        """
        # print("[LLM] Warming up LLM...")
        log_info("Warming up LLM model")
        try:
            if not self._check_ollama_available():
                return False

            import requests
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": "hello",
                    "stream": False,
                    "options": {"num_predict": 5}
                },
                timeout=30
            )

            if response.status_code == 200:
                # print("[LLM] ✅ LLM warmed up")
                log_info("LLM model warmed up")
                return True
            return False

        except Exception as e:
            # print(f"[LLM] Warm up error: {e}")
            log_warning(f"LLM warm up error: {e}")
            return False


# ── Singleton Instance ────────────────────────────────────────

_llm_fallback = None

def get_llm_fallback():
    global _llm_fallback
    if _llm_fallback is None:
        # print("[LLM] Creating singleton LLMFallback...")
        _llm_fallback = LLMFallback()
    return _llm_fallback

'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `_check_ollama_available()` | Ping Ollama service |
| `_ensure_model_available()` | Check phi3.5 is pulled |
| `_build_prompt()` | Structured classification prompt |
| `_parse_response()` | Extract intent from LLM response |
| `classify()` | Main LLM classification |
| `classify_free_form()` | Open-ended classification |
| `_get_available_intents()` | Load from registry |
| `is_available()` | Full availability check |
| `warm_up()` | Pre-load model into RAM |
| `get_llm_fallback()` | Singleton — creates once |

---

## LLM prompt design:
```
Command: "write an email for me"

Available intents: open_app, close_app, search,
volume_up, volume_down, write_text...

Rules:
- Return ONLY the intent name
- No explanation
- Return unknown if no match

Intent: write_text ✅
'''