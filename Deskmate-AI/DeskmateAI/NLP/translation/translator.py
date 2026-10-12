# DeskmateAI/NLP/translation/translator.py

import os
import sys
import time

# ============================================================
# TRANSLATOR FOR DESKMATEAI
# Translates Hindi and Marathi commands to English
# Uses Helsinki-NLP Opus-MT models
# Fully offline after first download
# Models stored in NLP/models/translation/
# English commands pass through without translation
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import get_translation_model_dir, ensure_dir

# ── Constants ─────────────────────────────────────────────────

# Helsinki-NLP model names for each language pair
TRANSLATION_MODELS = {
    'hi': 'Helsinki-NLP/opus-mt-hi-en',   # Hindi → English
    'mr': 'Helsinki-NLP/opus-mt-mr-en',   # Marathi → English
}

# Languages that don't need translation
NO_TRANSLATION_NEEDED = ['en', 'english']

# ── Translator Class ──────────────────────────────────────────

class Translator:

    def __init__(self):
        # print("[TRANSLATOR] Initializing Translator...")
        self._models = {}       # Loaded translation models
        self._tokenizers = {}   # Loaded tokenizers
        self._model_dir = get_translation_model_dir()
        ensure_dir(self._model_dir)
        log_info("Translator initialized")
        # print(f"[TRANSLATOR] Model dir: {self._model_dir}")

    def _load_model(self, language_code):
        """
        Load translation model for language
        Downloads to NLP/models/translation/ on first run
        Subsequent runs load from local storage
        Returns (model, tokenizer) or (None, None)
        """
        # print(f"[TRANSLATOR] Loading model for: {language_code}")
        log_info(f"Loading translation model: {language_code}")

        if language_code in self._models:
            # print(f"[TRANSLATOR] Model already loaded: {language_code}")
            return self._models[language_code], self._tokenizers[language_code]

        model_name = TRANSLATION_MODELS.get(language_code)
        if not model_name:
            # print(f"[TRANSLATOR] No model for: {language_code}")
            log_warning(f"No translation model for: {language_code}")
            return None, None

        try:
            from transformers import MarianMTModel, MarianTokenizer

            # print(f"[TRANSLATOR] Downloading/loading: {model_name}")
            log_info(f"Loading: {model_name}")

            # Build local cache path
            local_path = os.path.join(
                self._model_dir,
                language_code
            )

            # Try loading from local first
            if os.path.exists(local_path) and os.listdir(local_path):
                # print(f"[TRANSLATOR] Loading from local: {local_path}")
                try:
                    tokenizer = MarianTokenizer.from_pretrained(local_path)
                    model = MarianMTModel.from_pretrained(local_path)
                    # print(f"[TRANSLATOR] ✅ Loaded from local: {language_code}")
                    log_info(f"Translation model loaded from local: {language_code}")
                except Exception as local_e:
                    # print(f"[TRANSLATOR] Local load failed: {local_e}, downloading...")
                    log_warning(f"Local load failed, downloading: {local_e}")
                    tokenizer = MarianTokenizer.from_pretrained(
                        model_name,
                        cache_dir=self._model_dir
                    )
                    model = MarianMTModel.from_pretrained(
                        model_name,
                        cache_dir=self._model_dir
                    )
            else:
                # Download model
                # print(f"[TRANSLATOR] Downloading: {model_name}")
                ensure_dir(local_path)
                tokenizer = MarianTokenizer.from_pretrained(
                    model_name,
                    cache_dir=self._model_dir
                )
                model = MarianMTModel.from_pretrained(
                    model_name,
                    cache_dir=self._model_dir
                )
                # Save locally for next time
                try:
                    tokenizer.save_pretrained(local_path)
                    model.save_pretrained(local_path)
                    # print(f"[TRANSLATOR] ✅ Model saved locally: {local_path}")
                    log_info(f"Translation model saved locally: {language_code}")
                except Exception as save_e:
                    # print(f"[TRANSLATOR] Save failed: {save_e}")
                    log_warning(f"Could not save model locally: {save_e}")

            # Cache in memory
            self._models[language_code] = model
            self._tokenizers[language_code] = tokenizer

            # print(f"[TRANSLATOR] ✅ Model ready: {language_code}")
            log_info(f"Translation model ready: {language_code}")
            return model, tokenizer

        except Exception as e:
            # print(f"[TRANSLATOR] Model load error: {e}")
            log_error(f"Translation model load error: {e}")
            return None, None

    def translate(self, text, source_language='en'):
        # print(f"[TRANSLATOR] Translating from {source_language}: '{text}'")
        log_info(f"Translating [{source_language}]: '{text}'")

        if not text or not text.strip():
            log_warning("Empty text for translation")
            return text

        # ── Normalize language code ───────────────────────
        # Handles full names Whisper might return
        lang_normalize = {
            'hindi':   'hi',
            'marathi': 'mr',
            'english': 'en',
            'hi':      'hi',
            'mr':      'mr',
            'en':      'en',
        }
        source_language = lang_normalize.get(
            source_language.lower(),
            source_language
        )
        # print(f"[TRANSLATOR] Normalized language: {source_language}")
        # ─────────────────────────────────────────────────

        # Check if translation needed
        if source_language.lower() in NO_TRANSLATION_NEEDED:
            # print(f"[TRANSLATOR] No translation needed: {source_language}")
            log_debug(f"No translation needed: {source_language}")
            return text

        if source_language not in TRANSLATION_MODELS:
            # print(f"[TRANSLATOR] Unsupported language: {source_language}")
            log_warning(f"Unsupported language: {source_language}")
            return text

        try:
            # Load model (cached after first load)
            model, tokenizer = self._load_model(source_language)

            if model is None or tokenizer is None:
                # print(f"[TRANSLATOR] Model not available, returning original")
                log_error("Translation model not available")
                return text

            start_time = time.time()

            # Tokenize
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )

            # Translate
            translated = model.generate(
                **inputs,
                num_beams=4,
                max_length=512,
                early_stopping=True
            )

            # Decode
            result = tokenizer.decode(
                translated[0],
                skip_special_tokens=True
            )

            elapsed = time.time() - start_time
            # print(f"[TRANSLATOR] ✅ Translation: '{result}' ({elapsed:.3f}s)")
            log_info(f"Translation: '{text}' → '{result}' ({elapsed:.3f}s)")
            return result

        except Exception as e:
            # print(f"[TRANSLATOR] Translation error: {e}")
            log_error(f"Translation error: {e}")
            return text  # Return original on error

    def translate_batch(self, texts, source_language='en'):
        """
        Translate multiple texts at once
        More efficient than individual calls
        """
        # print(f"[TRANSLATOR] Batch translate: {len(texts)} texts")
        log_info(f"Batch translate: {len(texts)} texts")

        if not texts:
            return []

        if source_language.lower() in NO_TRANSLATION_NEEDED:
            return texts

        if source_language not in TRANSLATION_MODELS:
            return texts

        try:
            model, tokenizer = self._load_model(source_language)
            if model is None or tokenizer is None:
                return texts

            # Tokenize all texts
            inputs = tokenizer(
                texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )

            # Translate batch
            translated = model.generate(
                **inputs,
                num_beams=4,
                max_length=512,
                early_stopping=True
            )

            # Decode all
            results = [
                tokenizer.decode(t, skip_special_tokens=True)
                for t in translated
            ]

            # print(f"[TRANSLATOR] ✅ Batch translated: {len(results)} texts")
            log_info(f"Batch translated: {len(results)} texts")
            return results

        except Exception as e:
            # print(f"[TRANSLATOR] Batch translation error: {e}")
            log_error(f"Batch translation error: {e}")
            return texts

    def is_language_supported(self, language_code):
        """Check if language is supported"""
        # print(f"[TRANSLATOR] Checking language support: {language_code}")
        if language_code.lower() in NO_TRANSLATION_NEEDED:
            return True
        return language_code in TRANSLATION_MODELS

    def get_supported_languages(self):
        """Get list of supported languages"""
        supported = {
            'en': 'English (no translation needed)',
        }
        for code in TRANSLATION_MODELS:
            lang_names = {'hi': 'Hindi', 'mr': 'Marathi'}
            supported[code] = lang_names.get(code, code)
        # print(f"[TRANSLATOR] Supported: {supported}")
        return supported

    def preload_model(self, language_code):
        """
        Preload translation model
        Call during startup for faster first translation
        """
        # print(f"[TRANSLATOR] Preloading model: {language_code}")
        log_info(f"Preloading translation model: {language_code}")
        if language_code not in NO_TRANSLATION_NEEDED:
            model, tokenizer = self._load_model(language_code)
            return model is not None
        return True

    def preload_user_language(self, language_code):
        """
        Preload model for specific user's language
        Called when user logs in
        """
        # print(f"[TRANSLATOR] Preloading user language: {language_code}")
        if language_code and language_code not in NO_TRANSLATION_NEEDED:
            return self.preload_model(language_code)
        return True

    def get_loaded_models(self):
        """Get list of currently loaded models"""
        # print(f"[TRANSLATOR] Loaded models: {list(self._models.keys())}")
        return list(self._models.keys())

    def clear_models(self):
        """Clear loaded models from memory"""
        # print("[TRANSLATOR] Clearing models from memory...")
        self._models.clear()
        self._tokenizers.clear()
        log_info("Translation models cleared")

    def detect_if_translation_needed(self, language_code):
        """
        Simple check if translation is needed
        Returns True if translation needed
        """
        return language_code not in NO_TRANSLATION_NEEDED


# ── Singleton Instance ────────────────────────────────────────

_translator = None

def get_translator():
    global _translator
    if _translator is None:
        # print("[TRANSLATOR] Creating singleton Translator...")
        _translator = Translator()
    return _translator


def translate(text, source_language='en'):
    """Convenience function for translation"""
    return get_translator().translate(text, source_language)

'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `_load_model()` | Load Helsinki-NLP model |
| `translate()` | Translate single text |
| `translate_batch()` | Translate multiple texts |
| `is_language_supported()` | Check language support |
| `get_supported_languages()` | List supported languages |
| `preload_model()` | Preload for faster first use |
| `preload_user_language()` | Preload on user login |
| `detect_if_translation_needed()` | Quick check |
| `get_translator()` | Singleton — creates once |

---

## Translation flow:
```
User speaks Hindi command:
"क्रोम खोलो"
        ↓
Whisper transcribes in Hindi
        ↓
translator.translate("क्रोम खोलो", "hi")
        ↓
Helsinki-NLP translates
        ↓
"open chrome" ✅
        ↓
SBERT classifies intent
        ↓
open_app intent found ✅
```

---

## Model storage:
```
NLP/models/translation/
├── hi/          ← Hindi model (saved after first download)
│   ├── config.json
│   ├── vocab.json
│   └── ...
└── mr/          ← Marathi model (saved after first download)
    ├── config.json
    ├── vocab.json
    └── ...
'''