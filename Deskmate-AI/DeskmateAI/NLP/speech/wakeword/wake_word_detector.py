# DeskmateAI/NLP/speech/wake_word/wake_word_detector.py

import os
import sys
import time
import threading
import numpy as np

# ============================================================
# WAKE WORD DETECTOR FOR DESKMATEAI
# Continuously listens for user's custom wake word
# Uses Whisper small model (already in stack)
# Processes 1.5 second audio chunks
# Triggers when wake word detected in transcription
# Zero internet dependency
# Zero API key needed
# CPU usage ~3-5% in background
# User can set any wake word in any language
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Constants ─────────────────────────────────────────────────

SAMPLE_RATE = 16000
MIC_DEVICE  = None   # Realtek HD Audio Mic — cleaner signal
CHUNK_DURATION = 1.5      # seconds per chunk
CHUNK_SAMPLES = int(CHUNK_DURATION * SAMPLE_RATE)
DEFAULT_WAKE_WORD = "hey deskmate"
DEFAULT_SENSITIVITY = 0.6

# ── Wake Word Detector Class ──────────────────────────────────

class WakeWordDetector:

    def __init__(self):
        # print("[WAKE] Initializing WakeWordDetector...")
        self._model = None
        self._running = False
        self._detected = False
        self._lock = threading.Lock()
        try:
            from NLP.speech.preprocessing.noise_reduction import NoiseReducer
            from NLP.speech.preprocessing.silence_trim import SilenceTrimmer
            from NLP.speech.preprocessing.normalize_audio import AudioNormalizer
            self._noise_reducer  = NoiseReducer()
            self._silence_trimmer = SilenceTrimmer()
            self._normalizer     = AudioNormalizer()
        except Exception as e:
            self._noise_reducer  = None
            self._silence_trimmer = None
            self._normalizer     = None
            log_warning(f"Preprocessors not available: {e}")
        log_info("WakeWordDetector initialized")

    def _get_model(self):
        """Get Whisper model from ASR loader singleton"""
        # print("[WAKE] Getting Whisper model...")
        try:
            from NLP.speech.asr.asr_loader import get_asr_model
            model = get_asr_model()
            if model is None:
                log_error("Whisper model not available for wake word")
            return model
        except Exception as e:
            # print(f"[WAKE] Model get error: {e}")
            log_error(f"Wake word model error: {e}")
            return None

    # ── Record Chunk ──────────────────────────────────────────

    def _record_chunk(self, duration=CHUNK_DURATION):
        try:
            import sounddevice as sd
            audio = sd.rec(
                int(duration * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                blocking=True,
                device=MIC_DEVICE
            )
            audio = audio.flatten()

            # Check RMS on RAW audio before preprocessing
            rms = float(np.sqrt(np.mean(np.square(audio))))
            log_debug(f"Raw RMS: {rms:.6f}")
            # Apply preprocessing using cached instances
            try:
                if self._noise_reducer:
                    audio = self._noise_reducer.reduce(audio, SAMPLE_RATE)
                if self._silence_trimmer:
                    audio = self._silence_trimmer.trim(audio, SAMPLE_RATE)
                if self._normalizer:
                    audio = self._normalizer.normalize(audio)
            except Exception as e:
                log_debug(f"Preprocessing error: {e}")

            return audio

        except Exception as e:
            log_error(f"Wake word record error: {e}")
            return None
    # ── Transcribe Chunk ──────────────────────────────────────

    def _transcribe_chunk(self, audio, language='en'):
        """
        Transcribe audio chunk using Whisper
        Returns transcribed text in lowercase
        """
        # print("[WAKE] Transcribing chunk...")
        try:
            import tempfile
            import soundfile as sf

            model = self._get_model()
            if model is None:
                return ""

            # Save to temp file
            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"wake_chunk_{int(time.time() * 1000)}.wav"
            )

            try:
                sf.write(temp_path, audio, SAMPLE_RATE)

                # Transcribe with Whisper
                segments, info = model.transcribe(
                    temp_path,
                    language=language,
                    beam_size=1,         # Fastest setting
                    best_of=1,           # Fastest setting
                    temperature=0.0,     # Deterministic
                    condition_on_previous_text=False,
                    word_timestamps=False
                )

                text = " ".join([s.text for s in segments]).lower().strip()
                log_info(f"Transcribed: '{text}'")
                # print(f"[WAKE] Transcribed: '{text}'")
                return text

            finally:
                # Always delete temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            # print(f"[WAKE] Transcription error: {e}")
            log_error(f"Wake word transcription error: {e}")  # ERROR not DEBUG
            return ""

    # ── Check Wake Word ───────────────────────────────────────

    def _check_wake_word(self, text, wake_word, sensitivity=DEFAULT_SENSITIVITY):
        """
        Check if wake word is in transcribed text
        Flexible matching for natural speech variations
        """
        # print(f"[WAKE] Checking: '{text}' for '{wake_word}'")

        if not text or not wake_word:
            return False

        text_lower = text.lower().strip()
        wake_lower = wake_word.lower().strip()

        # Exact match
        if wake_lower in text_lower:
            # print(f"[WAKE] Exact match: '{wake_lower}' in '{text_lower}'")
            log_debug(f"Wake word exact match: '{wake_lower}'")
            return True

        # Word-level partial match
        wake_words = set(wake_lower.split())
        text_words = set(text_lower.split())

        if not wake_words:
            return False

        # Check how many wake word parts were detected
        common = wake_words.intersection(text_words)
        match_ratio = len(common) / len(wake_words)

        # print(f"[WAKE] Word match ratio: {match_ratio:.2f} (threshold: {sensitivity})")

        if match_ratio >= sensitivity:
            # print(f"[WAKE] Partial match: {match_ratio:.2f}")
            log_debug(f"Wake word partial match: {match_ratio:.2f}")
            return True

        return False

    # ── Main Listen ───────────────────────────────────────────

    def listen(self, wake_word=DEFAULT_WAKE_WORD,
               sensitivity=DEFAULT_SENSITIVITY,
               language='en'):
        """
        Listen for single wake word detection
        Called in loop from pipeline wake_word_loop
        Blocks until wake word detected or timeout
        Returns True when wake word detected
        """
        # print(f"[WAKE] Listening for: '{wake_word}'")

        try:
            # Record chunk
            audio = self._record_chunk()
            if audio is None:
                return False

            # Check if audio has any signal
            rms = float(np.sqrt(np.mean(np.square(audio))))
            log_info(f"RMS: {rms:.6f}")
            if rms < 0.001:
                # print("[WAKE] Silence detected, skipping transcription")
                return False

            # Transcribe
            text = self._transcribe_chunk(audio, language)
            if not text:
                return False

            # Check wake word
            detected = self._check_wake_word(text, wake_word, sensitivity)

            if detected:
                log_info(f"Wake word detected: '{text}'")
                # print(f"[WAKE] 🎤 WAKE WORD DETECTED: '{text}'")

            return detected

        except Exception as e:
            # print(f"[WAKE] Listen error: {e}")
            log_error(f"Wake word listen error: {e}")
            return False

    def stop(self):
        """Stop wake word detection"""
        # print("[WAKE] Stopping wake word detector...")
        self._running = False
        log_info("Wake word detector stopped")

    # ── Test Wake Word ────────────────────────────────────────

    def test_wake_word(self, wake_word, language='en', timeout=10):
        """
        Test if wake word is detectable
        Records for timeout seconds
        Returns True if detected
        Used in settings for testing
        """
        # print(f"[WAKE] Testing wake word: '{wake_word}'")
        log_info(f"Testing wake word: '{wake_word}'")

        start_time = time.time()

        while time.time() - start_time < timeout:
            detected = self.listen(wake_word, 0.5, language)
            if detected:
                # print(f"[WAKE] ✅ Wake word test successful: '{wake_word}'")
                log_info(f"Wake word test successful: '{wake_word}'")
                return True

        # print(f"[WAKE] ❌ Wake word test failed: '{wake_word}'")
        log_warning(f"Wake word test failed: '{wake_word}'")
        return False

    # ── Update Settings ───────────────────────────────────────

    def update_wake_word_settings(self, wake_word, sensitivity):
        """Update wake word settings"""
        # print(f"[WAKE] Settings updated: '{wake_word}' | sensitivity: {sensitivity}")
        log_info(f"Wake word settings: '{wake_word}' | sensitivity: {sensitivity}")
        # Settings are passed per-call from context
        # No storage needed here — context manager handles it


# ── Singleton Instance ────────────────────────────────────────

_wake_word_detector = None

def get_wake_word_detector():
    global _wake_word_detector
    if _wake_word_detector is None:
        # print("[WAKE] Creating singleton WakeWordDetector...")
        _wake_word_detector = WakeWordDetector()
    return _wake_word_detector