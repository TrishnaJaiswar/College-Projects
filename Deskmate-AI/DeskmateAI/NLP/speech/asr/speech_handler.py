# DeskmateAI/NLP/speech/asr/speech_handler.py

import os
import sys
import time
import tempfile
import numpy as np

# ============================================================
# SPEECH HANDLER FOR DESKMATEAI
# Main ASR processing unit
# Coordinates:
# - Microphone recording (mic_stream)
# - Audio preprocessing (noise, silence, normalize)
# - Whisper transcription (asr_loader)
# Handles both command and dictation modes
# Supports English, Hindi, Marathi
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Constants ─────────────────────────────────────────────────

SAMPLE_RATE = 16000
BEAM_SIZE = 1# Transcription beam size
VAD_FILTER = False    # Use Whisper's built-in VAD

# ── Speech Handler Class ──────────────────────────────────────

class SpeechHandler:

    def __init__(self):
        # print("[SPEECH] Initializing SpeechHandler...")
        self._mic = None
        self._noise_reducer = None
        self._silence_trimmer = None
        self._normalizer = None
        self._model = None
        self._prompt = None
        self._load_components()
        log_info("SpeechHandler initialized")

    def _load_components(self):
        """Load all speech processing components"""
        # print("[SPEECH] Loading speech components...")
        try:
            from NLP.speech.asr.mic_stream import get_mic_stream
            from NLP.speech.preprocessing.noise_reduction import get_noise_reducer
            from NLP.speech.preprocessing.silence_trim import get_silence_trimmer
            from NLP.speech.preprocessing.normalize_audio import get_normalizer
            from NLP.speech.asr.asr_loader import get_asr_model

            self._mic = get_mic_stream()
            self._noise_reducer = get_noise_reducer()
            self._silence_trimmer = get_silence_trimmer()
            self._normalizer = get_normalizer()
            self._model = get_asr_model()

            # print("[SPEECH] ✅ All components loaded")
            log_info("Speech components loaded")

        except Exception as e:
            # print(f"[SPEECH] Component load error: {e}")
            log_error(f"Speech component load error: {e}")

    def _get_model(self):
        """Get ASR model, load if needed"""
        if self._model is None:
            from NLP.speech.asr.asr_loader import get_asr_model
            self._model = get_asr_model()
        return self._model

    # ── Record Command ────────────────────────────────────────

    def record_command(self):
        """
        Record voice command from microphone
        Uses VAD to automatically stop
        Returns raw audio array
        """
        # print("[SPEECH] Recording command...")
        log_info("Recording voice command")

        try:
            if self._mic is None:
                from NLP.speech.asr.mic_stream import get_mic_stream
                self._mic = get_mic_stream()

            audio = self._mic.record_command()

            if audio is None:
                # print("[SPEECH] No audio recorded")
                log_warning("No audio recorded for command")
                return None

            # print(f"[SPEECH] ✅ Command recorded: {len(audio)/SAMPLE_RATE:.2f}s")
            log_debug(f"Command recorded: {len(audio)/SAMPLE_RATE:.2f}s")
            return audio

        except Exception as e:
            # print(f"[SPEECH] Record command error: {e}")
            log_error(f"Record command error: {e}")
            return None

    # ── Record Dictation ──────────────────────────────────────

    def record_dictation(self):
        """
        Record dictation audio from microphone
        Longer recording with longer silence tolerance
        Returns raw audio array
        """
        # print("[SPEECH] Recording dictation...")
        log_info("Recording dictation")

        try:
            if self._mic is None:
                from NLP.speech.asr.mic_stream import get_mic_stream
                self._mic = get_mic_stream()

            audio = self._mic.record_dictation()

            if audio is None:
                # print("[SPEECH] No dictation audio")
                log_warning("No dictation audio recorded")
                return None

            # print(f"[SPEECH] ✅ Dictation recorded: {len(audio)/SAMPLE_RATE:.2f}s")
            log_debug(f"Dictation recorded: {len(audio)/SAMPLE_RATE:.2f}s")
            return audio

        except Exception as e:
            # print(f"[SPEECH] Record dictation error: {e}")
            log_error(f"Record dictation error: {e}")
            return None

    # ── Preprocess Audio ──────────────────────────────────────

    def preprocess(self, audio):
        """
        Full audio preprocessing pipeline
        1. Noise reduction
        2. Silence trim
        3. Normalize for Whisper
        Returns preprocessed audio
        """
        print("[SPEECH] Preprocessing audio...")
        log_debug("Preprocessing audio")

        if audio is None or len(audio) == 0:
            return audio

        try:
            # Step 1: Noise reduction
            if self._noise_reducer:
                audio = self._noise_reducer.smart_reduce(audio, SAMPLE_RATE)
                # print("[SPEECH] ✅ Noise reduced")

            # Step 2: Silence trim
            if self._silence_trimmer:
                audio = self._silence_trimmer.full_process(audio, SAMPLE_RATE)
                # print("[SPEECH] ✅ Silence trimmed")

            # Step 3: Normalize
            if self._normalizer:
                audio = self._normalizer.prepare_for_whisper(audio, SAMPLE_RATE)
                # print("[SPEECH] ✅ Audio normalized")

            # print("[SPEECH] ✅ Preprocessing complete")
            log_debug("Audio preprocessing complete")
            return audio

        except Exception as e:
            # print(f"[SPEECH] Preprocessing error: {e}")
            log_error(f"Audio preprocessing error: {e}")
            return audio

    # ── Transcribe ────────────────────────────────────────────
    def _get_initial_prompt(self):
        try:
            from backend.core.context import get_context
            lang = get_context().get_language()
        except:
            lang = 'en'

        prompts = {
            'en':       "Voice assistant commands: open, close, play, stop, search, volume.",
            'hi':       "वॉयस असिस्टेंट कमांड: खोलो, बंद करो, चलाओ, रोको, खोजो, वॉल्यूम।",
            'mr':       "व्हॉइस असिस्टंट कमांड: उघडा, बंद करा, चालवा, थांबवा, शोधा.",
            'hinglish': "Hinglish voice commands: open karo, band karo, volume badhao, search karo.",
            'minglish': "Minglish voice commands: open kara, band kara, volume vaddhav, search kara.",
        }
        return prompts.get(lang, prompts['en'])
    def transcribe(self, audio, language='en'):
        """
        Transcribe audio to text using Whisper small
        Supports English, Hindi, Marathi
        Returns transcribed text string
        """
        # print(f"[SPEECH] Transcribing in: {language}")
        log_info(f"Transcribing audio in: {language}")

        if audio is None or len(audio) == 0:
            log_warning("Empty audio for transcription")
            return ""

        temp_path = None

        try:
            # Preprocess audio
            processed_audio = self.preprocess(audio)

            if processed_audio is None or len(processed_audio) == 0:
                log_warning("Audio empty after preprocessing")
                return ""

            # Check has speech
            # if self._silence_trimmer:
            #     has_speech = self._silence_trimmer.has_speech(
            #         processed_audio, SAMPLE_RATE
            #     )
            #     if not has_speech:
            #         # print("[SPEECH] No speech detected in audio")
            #         log_warning("No speech detected")
            #         return ""

            # Get model
            model = self._get_model()
            if model is None:
                log_error("ASR model not available")
                return ""

            # Save to temp file for Whisper
            import soundfile as sf
            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"transcribe_{int(time.time() * 1000)}.wav"
            )

            sf.write(temp_path, processed_audio, SAMPLE_RATE)

            # Transcribe with Whisper
            # print(f"[SPEECH] Running Whisper transcription...")
            start_time = time.time()

            # ── NEW CODE ──────────────────────────────────────
            segments, info = model.transcribe(
                temp_path,
                language=language,
                beam_size=BEAM_SIZE,
                vad_filter=VAD_FILTER,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                ),
                initial_prompt=self._get_initial_prompt(),
                word_timestamps=False,
                condition_on_previous_text=False
            )

            # Collect transcription
            text = " ".join([segment.text for segment in segments])
            text = text.strip()

            elapsed = time.time() - start_time
            # print(f"[SPEECH] ✅ Transcription: '{text}' ({elapsed:.3f}s)")
            log_info(f"Transcription: '{text}' ({elapsed:.3f}s)")

            return text

        except Exception as e:
            # print(f"[SPEECH] Transcription error: {e}")
            log_error(f"Transcription error: {e}")
            return ""

        finally:
            # Always clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    # print("[SPEECH] Temp file deleted")
                except:
                    pass

    # ── Record and Transcribe ─────────────────────────────────

    def record_and_transcribe(self, language='en'):
        """
        Convenience method: Record then transcribe
        Returns (audio, text) tuple
        """
        # print(f"[SPEECH] Record and transcribe: {language}")
        log_info(f"Record and transcribe: {language}")

        audio = self.record_command()
        if audio is None:
            return None, ""

        text = self.transcribe(audio, language)
        return audio, text

    def record_dictation_and_transcribe(self, language='en'):
        """
        Record dictation and transcribe
        Returns (audio, text) tuple
        """
        # print(f"[SPEECH] Record dictation and transcribe: {language}")
        log_info(f"Record dictation and transcribe: {language}")

        audio = self.record_dictation()
        if audio is None:
            return None, ""

        text = self.transcribe(audio, language)
        return audio, text

    # ── Language Support ──────────────────────────────────────

    def get_supported_languages(self):
        """Get list of supported languages"""
        return {
            'en':       'English',
            'hi':       'Hindi',
            'mr':       'Marathi',
            'hinglish': 'Hinglish (Hindi+English)',
            'minglish': 'Minglish (Marathi+English)',
        }

    def detect_language(self, audio):
        """
        Detect language of spoken audio
        Returns language code
        """
        # print("[SPEECH] Detecting language...")
        log_info("Detecting audio language")

        temp_path = None
        try:
            model = self._get_model()
            if model is None:
                return 'en'

            import soundfile as sf
            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"detect_lang_{int(time.time())}.wav"
            )

            processed = self.preprocess(audio)
            sf.write(temp_path, processed, SAMPLE_RATE)

            # Detect language
            _, info = model.transcribe(temp_path, beam_size=1)
            detected = info.language
            # print(f"[SPEECH] Detected language: {detected}")
            log_info(f"Detected language: {detected}")
            return detected

        except Exception as e:
            # print(f"[SPEECH] Language detection error: {e}")
            log_error(f"Language detection error: {e}")
            return 'en'

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    # ── Microphone Status ─────────────────────────────────────

    def test_microphone(self):
        """Test microphone availability"""
        # print("[SPEECH] Testing microphone...")
        if self._mic:
            return self._mic.test_microphone()
        return False, "Microphone not initialized"

    def get_audio_level(self):
        """Get current microphone level for UI"""
        if self._mic:
            return self._mic.get_audio_level()
        return 0.0

    def stream_audio_levels(self, callback, stop_event):
        """Stream audio levels for waveform animation"""
        if self._mic:
            self._mic.stream_audio_levels(callback, stop_event)

    # ── Model Info ────────────────────────────────────────────

    def get_model_info(self):
        """Get ASR model information"""
        from NLP.speech.asr.asr_loader import get_asr_loader
        return get_asr_loader().get_model_info()


# ── Singleton Instance ────────────────────────────────────────

_speech_handler = None

def get_speech_handler():
    global _speech_handler
    if _speech_handler is None:
        # print("[SPEECH] Creating singleton SpeechHandler...")
        _speech_handler = SpeechHandler()
    return _speech_handler

'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `_load_components()` | Load all sub-components |
| `record_command()` | Record voice command |
| `record_dictation()` | Record dictation audio |
| `preprocess()` | Noise→Silence→Normalize |
| `transcribe()` | Whisper transcription |
| `record_and_transcribe()` | Record + transcribe in one call |
| `record_dictation_and_transcribe()` | Dictation version |
| `detect_language()` | Auto detect spoken language |
| `test_microphone()` | Check mic working |
| `get_audio_level()` | Level for waveform UI |
| `stream_audio_levels()` | Continuous level stream |
| `get_speech_handler()` | Singleton — creates once |

---

## Complete speech pipeline:
```
Microphone input
        ↓
mic_stream.record_command() → raw audio
        ↓
noise_reducer.smart_reduce() → clean audio
        ↓
silence_trimmer.full_process() → trimmed audio
        ↓
normalizer.prepare_for_whisper() → normalized audio
        ↓
Whisper small transcribe() → text ✅
'''