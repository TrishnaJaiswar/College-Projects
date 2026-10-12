# DeskmateAI/backend/core/pipeline.py

import os
import sys
import threading
import time

# ============================================================
# MAIN PIPELINE FOR DESKMATEAI
# Orchestrates entire voice assistant flow
# Wake word → ASR → Translation → NLP → Auth → Execute
# Runs in background thread
# Communicates with UI via callbacks
# Handles dictation mode separately
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.context import get_context_manager
from backend.core.command_handler import get_handler
from backend.core.responder import get_responder
from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Pipeline Class ────────────────────────────────────────────

class Pipeline:

    def __init__(self):
        # print("[PIPELINE] Initializing Pipeline...")

        self.context = get_context_manager()
        self.handler = get_handler()
        self.responder = get_responder()

        # Pipeline components (lazy loaded)
        self._wake_word_detector = None
        self._speech_handler = None
        self._translator = None
        self._intent_pipeline = None
        self._speech_auth = None
        self._mic_stream = None

        # State
        self._running = False
        self._pipeline_thread = None
        self._wake_word_thread = None

        # UI Callbacks
        self.on_wake_word_detected = None
        self.on_listening_start = None
        self.on_listening_end = None
        self.on_processing_start = None
        self.on_processing_end = None
        self.on_transcription = None
        self.on_intent_classified = None
        self.on_command_executed = None
        self.on_error = None
        self.on_status_change = None
        self.on_dictation_mode = None

        log_info("Pipeline initialized")
        # print("[PIPELINE] Pipeline initialized")

    # ── Component Loading ─────────────────────────────────────

    def _load_components(self):
        """Lazy load all pipeline components"""
        # print("[PIPELINE] Loading pipeline components...")
        log_info("Loading pipeline components...")

        try:
            # Load wake word detector
            # print("[PIPELINE] Loading wake word detector...")
            from NLP.speech.wakeword.wake_word_detector import get_wake_word_detector
            self._wake_word_detector = get_wake_word_detector()
            # print("[PIPELINE] ✅ Wake word detector loaded")

            # Load speech handler
            # print("[PIPELINE] Loading speech handler...")
            from NLP.speech.asr.speech_handler import get_speech_handler
            self._speech_handler = get_speech_handler()
            # print("[PIPELINE] ✅ Speech handler loaded")

            # Load translator
            # print("[PIPELINE] Loading translator...")
            from NLP.translation.translator import get_translator
            self._translator = get_translator()
            # print("[PIPELINE] ✅ Translator loaded")

            # Load intent pipeline
            # print("[PIPELINE] Loading intent pipeline...")
            from NLP.nlp.intent_pipeline import get_intent_pipeline
            self._intent_pipeline = get_intent_pipeline()
            # print("[PIPELINE] ✅ Intent pipeline loaded")

            # Load speech auth
            # print("[PIPELINE] Loading speech auth...")
            from backend.security.speech_auth import get_speech_auth
            self._speech_auth = get_speech_auth()
            # print("[PIPELINE] ✅ Speech auth loaded")

            log_info("All pipeline components loaded successfully")
            # print("[PIPELINE] ✅ All components loaded")
            return True

        except Exception as e:
            # print(f"[PIPELINE] ❌ Error loading components: {e}")
            log_error(f"Error loading pipeline components: {e}")
            return False

    # ── Start / Stop ──────────────────────────────────────────

    def start(self, user_profile):
        """
        Start the pipeline
        Called after successful login
        """
        # print(f"[PIPELINE] Starting pipeline for user: {user_profile.get('username')}")
        log_info(f"Starting pipeline for: {user_profile.get('username')}")

        # Set user context
        self.context.set_user(
            user_profile.get('username'),
            user_profile
        )

        # Set responder language
        self.responder.set_language(user_profile.get('language', 'en'))

        # Load components
        if not self._load_components():
            # print("[PIPELINE] ❌ Failed to load components")
            log_error("Failed to load pipeline components")
            return False

        # Start running
        self._running = True

        # Start wake word detection in background
        self._wake_word_thread = threading.Thread(
            target=self._wake_word_loop,
            daemon=True,
            name="WakeWordThread"
        )
        self._wake_word_thread.start()
        # print("[PIPELINE] ✅ Wake word thread started")

        # Speak ready message
        self.responder.speak("ready")
        log_info("Pipeline started successfully")
        return True

    def stop(self):
        """Stop the pipeline"""
        # print("[PIPELINE] Stopping pipeline...")
        log_info("Stopping pipeline")
        self._running = False

        # Stop wake word detector
        if self._wake_word_detector:
            self._wake_word_detector.stop()

        log_info("Pipeline stopped")
        # print("[PIPELINE] Pipeline stopped")

    # ── Wake Word Loop ────────────────────────────────────────

    def _wake_word_loop(self):
        """
        Continuously listen for wake word
        Runs in background thread at ~3-5% CPU
        """
        # print("[PIPELINE] Wake word loop started")
        log_info("Wake word loop started")

        while self._running:
            try:
                # Get wake word from context
                wake_word = self.context.get_wake_word()
                sensitivity = self.context.get_wake_word_sensitivity()
                language = self.context.get_language()

                # print(f"[PIPELINE] Listening for wake word: '{wake_word}'")

                # Listen for wake word
                detected = self._wake_word_detector.listen(
                    wake_word=wake_word,
                    sensitivity=sensitivity,
                    language=language
                )

                if detected and self._running:
                    # print(f"[PIPELINE] 🎤 Wake word detected!")
                    log_info("Wake word detected - starting command listening")
                    self._on_wake_word()

            except Exception as e:
                # print(f"[PIPELINE] Wake word loop error: {e}")
                log_error(f"Wake word loop error: {e}")
                time.sleep(1)  # Wait before retrying

        # print("[PIPELINE] Wake word loop ended")
        log_info("Wake word loop ended")

    def _on_wake_word(self):
        """
        Called when wake word is detected
        Starts command listening
        """
        # print("[PIPELINE] Wake word callback triggered")

        # Notify UI
        if self.on_wake_word_detected:
            self.on_wake_word_detected()

        # Update context
        self.context.set_listening(True)

        # Check if in dictation mode
        if self.context.is_in_dictation_mode():
            # print("[PIPELINE] In dictation mode - handling dictation")
            self._handle_dictation_input()
        else:
            # print("[PIPELINE] Normal command mode")
            self._handle_command_input()

        self.context.set_listening(False)

    # ── Command Input ─────────────────────────────────────────

    def _handle_command_input(self):
        """
        Record and process voice command
        Full pipeline with PARALLEL speaker verification + command preparation
        """
        # print("[PIPELINE] Handling command input...")
        import concurrent.futures

        try:
            # ── Step 1: Record audio ──────────────────────────
            # print("[PIPELINE] Step 1: Recording audio...")
            if self.on_listening_start:
                self.on_listening_start()
            self._set_status("listening")

            audio = self._speech_handler.record_command()

            if self.on_listening_end:
                self.on_listening_end()

            if audio is None:
                # print("[PIPELINE] No audio recorded")
                log_warning("No audio recorded")
                return

            # print("[PIPELINE] ✅ Audio recorded")

            # ── Step 2: Set processing ────────────────────────
            self.context.set_processing(True)
            if self.on_processing_start:
                self.on_processing_start()
            self._set_status("processing")

            # ── Step 3: Transcribe ────────────────────────────
            # print("[PIPELINE] Step 3: Transcribing...")
            language = self.context.get_language()
            transcription = self._speech_handler.transcribe(audio, self._whisper_language(language))

            if not transcription or not transcription.strip():
                # print("[PIPELINE] Empty transcription")
                log_warning("Empty transcription")
                self.context.set_processing(False)
                return

            # print(f"[PIPELINE] ✅ Transcription: '{transcription}'")
            log_info(f"Transcription: '{transcription}'")

            if self.on_transcription:
                self.on_transcription(transcription)

            # ── Step 4: Translate ─────────────────────────────
            # print("[PIPELINE] Step 4: Translating...")
            english_text = self._translator.translate(
                transcription,
                source_language=language
            )
            # print(f"[PIPELINE] ✅ Translation: '{english_text}'")
            log_info(f"Translation: '{english_text}'")

            # ── Step 5: Get context ───────────────────────────
            # print("[PIPELINE] Step 5: Getting context...")
            context = self.context.get_context()

            # ── Step 6: Classify intent ───────────────────────
            # print("[PIPELINE] Step 6: Classifying intent...")
            intent, score, source = self._intent_pipeline.classify(
                english_text,
                context
            )
            # print(f"[PIPELINE] ✅ Intent: '{intent}' | Score: {score:.2f} | Source: {source}")
            log_info(f"Intent: '{intent}' | Score: {score:.2f} | Source: {source}")

            if self.on_intent_classified:
                self.on_intent_classified(intent, score, source)

            # ── Step 7+8: PARALLEL verification + preparation ─
            # print("[PIPELINE] Step 7+8: Parallel verify + prepare...")
            username = context.get("current_user")

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

                # Thread 1: Speaker verification
                verify_future = executor.submit(
                    self._speech_auth.verify,
                    audio,
                    username
                ) if username else None

                # Thread 2: Command preparation
                prepare_future = executor.submit(
                    self.handler.prepare,
                    intent,
                    english_text,
                    context
                )

                # Wait for both
                prepared = prepare_future.result()
                # print(f"[PIPELINE] ✅ Command prepared: {intent}")

                if verify_future:
                    is_authorized = verify_future.result()
                    # print(f"[PIPELINE] ✅ Speaker verified: {is_authorized}")
                    if not is_authorized:
                        # print("[PIPELINE] ❌ Speaker verification failed")
                        log_warning("Speaker verification failed")
                        self.responder.speak("unauthorized")
                        self.context.set_processing(False)
                        self._set_status("idle")
                        return

            # ── Step 9: Execute prepared command ─────────────
            # print("[PIPELINE] Step 9: Executing prepared command...")
            self._set_status("executing")

            success, response_key, entity = self.handler.execute_prepared(
                prepared,
                context
            )

            # print(f"[PIPELINE] ✅ Execution complete: success={success}")

            if self.on_command_executed:
                self.on_command_executed(intent, success, entity)

            # ── Step 10: Finalize ─────────────────────────────
            self.context.set_processing(False)
            self._set_status("idle")

            if self.on_processing_end:
                self.on_processing_end(success)

            log_info(f"Pipeline cycle complete: {intent} | success={success}")

        except Exception as e:
            # print(f"[PIPELINE] ❌ Pipeline error: {e}")
            log_error(f"Pipeline error: {e}")
            self.context.set_processing(False)
            self._set_status("idle")
            if self.on_error:
                self.on_error(str(e))

    # ── Dictation Input ───────────────────────────────────────

    def _handle_dictation_input(self):
        """
        Handle dictation mode input
        Records longer audio and types it
        """
        # print("[PIPELINE] Handling dictation input...")
        log_info("Handling dictation input")

        try:
            # Notify UI
            if self.on_dictation_mode:
                self.on_dictation_mode(True)

            # Record dictation audio (longer duration)
            if self.on_listening_start:
                self.on_listening_start()

            audio = self._speech_handler.record_dictation()

            if self.on_listening_end:
                self.on_listening_end()

            if audio is None:
                # print("[PIPELINE] No dictation audio")
                log_warning("No dictation audio recorded")
                self.context.exit_dictation_mode()
                return

            # Transcribe in user's language
            language = self.context.get_language()
            # print(f"[PIPELINE] Transcribing dictation in: {language}")

            dictated_text = self._speech_handler.transcribe(audio, self._whisper_language(language))
            if not dictated_text or not dictated_text.strip():
                # print("[PIPELINE] Empty dictation")
                log_warning("Empty dictation received")
                self.context.exit_dictation_mode()
                return

            # print(f"[PIPELINE] ✅ Dictation: '{dictated_text}'")
            log_info(f"Dictation text: '{dictated_text}'")

            # Check if user said stop/cancel
            stop_words = {
                'en': ['stop dictation', 'cancel dictation', 'stop', 'cancel'],
                'hi': ['रुको', 'बंद करो', 'रद्द करो'],
                'mr': ['थांबा', 'बंद करा', 'रद्द करा']
            }

            lang_stops = stop_words.get(language, stop_words['en'])
            if any(stop in dictated_text.lower() for stop in lang_stops):
                # print("[PIPELINE] Dictation cancelled by user")
                log_info("Dictation cancelled by user")
                self.context.exit_dictation_mode()
                self.responder.speak("dictation_cancelled")
                if self.on_dictation_mode:
                    self.on_dictation_mode(False)
                return

            # Handle dictated text
            success, response_key, result = self.handler.handle_dictation_text(
                dictated_text,
                self.context.get_context()
            )

            if self.on_dictation_mode:
                self.on_dictation_mode(False)

            # print(f"[PIPELINE] ✅ Dictation handled: success={success}")
            log_info(f"Dictation handled: success={success}")

        except Exception as e:
            # print(f"[PIPELINE] ❌ Dictation error: {e}")
            log_error(f"Dictation error: {e}")
            self.context.exit_dictation_mode()
            if self.on_dictation_mode:
                self.on_dictation_mode(False)

    # ── Status ────────────────────────────────────────────────

    def _set_status(self, status):
        """Update system status and notify UI"""
        # print(f"[PIPELINE] Status: {status}")
        if self.on_status_change:
            self.on_status_change(status)
        return True

    # ── Language Update ───────────────────────────────────────
    _MIXED_LANGUAGE_CODES = {'hinglish', 'minglish'}

    def _whisper_language(self, lang_code):
        """Convert app language code to Whisper language param.
        Hinglish/Minglish pass None so Whisper auto-detects per segment."""
        if lang_code in self._MIXED_LANGUAGE_CODES:
            return None
        return lang_code
    def update_language(self, language_code, language_name):
        """Update language mid-session"""
        # print(f"[PIPELINE] Updating language: {language_code}")
        self.context.update_language(language_code, language_name)
        self.responder.set_language(language_code)
        log_info(f"Language updated: {language_name}")

    # ── Wake Word Update ──────────────────────────────────────

    def update_wake_word(self, wake_word, sensitivity=0.6):
        """Update wake word mid-session"""
        # print(f"[PIPELINE] Updating wake word: {wake_word}")
        self.context.update_wake_word(wake_word, sensitivity)
        log_info(f"Wake word updated: {wake_word}")

    # ── Callbacks Registration ────────────────────────────────

    def register_callbacks(self, callbacks):
        """
        Register UI callbacks
        Called from ui/controller.py
        """
        # print("[PIPELINE] Registering UI callbacks...")
        self.on_wake_word_detected = callbacks.get('on_wake_word_detected')
        self.on_listening_start = callbacks.get('on_listening_start')
        self.on_listening_end = callbacks.get('on_listening_end')
        self.on_processing_start = callbacks.get('on_processing_start')
        self.on_processing_end = callbacks.get('on_processing_end')
        self.on_transcription = callbacks.get('on_transcription')
        self.on_intent_classified = callbacks.get('on_intent_classified')
        self.on_command_executed = callbacks.get('on_command_executed')
        self.on_error = callbacks.get('on_error')
        self.on_status_change = callbacks.get('on_status_change')
        self.on_dictation_mode = callbacks.get('on_dictation_mode')
        # print("[PIPELINE] ✅ Callbacks registered")
        log_info("UI callbacks registered")

    def is_running(self):
        return self._running

    def get_context(self):
        return self.context.get_context()


# ── Singleton Instance ────────────────────────────────────────

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        # print("[PIPELINE] Creating singleton Pipeline...")
        _pipeline = Pipeline()
    return _pipeline
'''

## What this file does:

| Function | Purpose |
|---|---|
| `_load_components()` | Lazy loads all modules once |
| `start()` | Starts pipeline after login |
| `stop()` | Stops pipeline cleanly |
| `_wake_word_loop()` | Background thread listening for wake word |
| `_on_wake_word()` | Called when wake word detected |
| `_handle_command_input()` | Full 9-step pipeline |
| `_handle_dictation_input()` | Dictation mode pipeline |
| `_set_status()` | Updates UI status |
| `update_language()` | Changes language mid-session |
| `update_wake_word()` | Changes wake word mid-session |
| `register_callbacks()` | Connects UI callbacks |
| `get_pipeline()` | Singleton — creates once |

---

## Complete 9-step pipeline:
```
Step 1: Record audio
Step 2: Set processing state
Step 3: Transcribe (Whisper small)
Step 4: Translate (Helsinki-NLP)
Step 5: Get context
Step 6: Classify intent (SBERT/Ollama)
Step 7: Verify speaker (Resemblyzer)
Step 8: Handle command
Step 9: Update context + UI
'''