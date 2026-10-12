# DeskmateAI/backend/security/speech_auth.py

import os
import sys
import time
import numpy as np

# ============================================================
# SPEECH AUTHENTICATION FOR DESKMATEAI
# Two responsibilities:
# 1. Voice Password - user says specific passphrase to login
# 2. Speaker Verification - verify speaker on every command
# Uses Resemblyzer for speaker embeddings
# Embeddings stored as .npy files - never raw audio
# Multiple speaker samples for robustness
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import (
    get_user_speaker_dir,
    get_user_voice_pass_dir,
    save_numpy,
    load_numpy,
    load_profile,
    save_profile,
    get_timestamp,
    ensure_dir
)

# ── Constants ─────────────────────────────────────────────────

SPEAKER_SAMPLES_REQUIRED = 3
SPEAKER_SIMILARITY_THRESHOLD = 0.55  # Higher = stricter
VOICE_PASS_THRESHOLD = 0.70
SAMPLE_RATE = 16000
RECORD_DURATION_SPEAKER = 5   # seconds for speaker profile
RECORD_DURATION_COMMAND = 3   # seconds for command verification
RECORD_DURATION_PASS = 3      # seconds for voice password

# ── Speech Auth Class ─────────────────────────────────────────

class SpeechAuth:

    def __init__(self):
        # print("[SPEECH_AUTH] Initializing SpeechAuth...")
        self._encoder = None
        self._load_encoder()
        log_info("SpeechAuth initialized")

    def _load_encoder(self):
        """Load Resemblyzer encoder - lazy loaded"""
        # print("[SPEECH_AUTH] Loading Resemblyzer encoder...")
        try:
            from resemblyzer import VoiceEncoder
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._encoder = VoiceEncoder(device=device)
            log_info(f"Resemblyzer encoder on: {device}")
            # print("[SPEECH_AUTH] ✅ Resemblyzer encoder loaded")
            log_info("Resemblyzer encoder loaded")
        except Exception as e:
            # print(f"[SPEECH_AUTH] Encoder load error: {e}")
            log_error(f"Resemblyzer load error: {e}")
            self._encoder = None

    def _get_encoder(self):
        """Get encoder, load if needed"""
        if self._encoder is None:
            self._load_encoder()
        return self._encoder

    # ── Audio Recording ───────────────────────────────────────

    def _record_audio(self, duration, sample_rate=SAMPLE_RATE):
        """
        Record audio — never blocks Qt event loop
        Uses InputStream with time.sleep instead of sd.wait()
        """
        # print(f"[SPEECH_AUTH] Recording {duration}s...")
        try:
            import sounddevice as sd
            import time
            sd.stop()
            frames = []

            def callback(indata, frame_count, time_info, status):
                frames.append(indata.copy())

            stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype='float32',
                callback=callback,
                blocksize=int(sample_rate * 0.1)  # 100ms chunks
            )

            with stream:
                # Sleep in small increments
                elapsed = 0
                interval = 0.1
                while elapsed < duration:
                    time.sleep(interval)
                    elapsed += interval

            if frames:
                audio = np.concatenate(frames, axis=0).flatten()
                # print(f"[SPEECH_AUTH] ✅ Recorded: {len(audio)} samples")
                log_debug(f"Recorded {len(audio)} samples")
                return audio

            return None

        except Exception as e:
            # print(f"[SPEECH_AUTH] Recording error: {e}")
            log_error(f"Audio recording error: {e}")
            return None

    def record_for_verification(self, audio_data=None, duration=RECORD_DURATION_COMMAND):
        """
        Record or use provided audio for verification
        If audio_data provided (from pipeline), use it
        Otherwise record fresh
        """
        # print("[SPEECH_AUTH] Getting audio for verification...")
        if audio_data is not None:
            # print("[SPEECH_AUTH] Using provided audio data")
            return audio_data
        return self._record_audio(duration)

    # ── Extract Speaker Embedding ─────────────────────────────

    def _extract_speaker_embedding(self, audio):
        """
        Extract speaker embedding from audio
        Uses Resemblyzer VoiceEncoder
        Returns 256-dim embedding array
        """
        # print("[SPEECH_AUTH] Extracting speaker embedding...")
        try:
            encoder = self._get_encoder()
            if encoder is None:
                log_error("Encoder not available")
                return None

            from resemblyzer import preprocess_wav
            import io
            import soundfile as sf

            # Convert numpy array to wav format for resemblyzer
            if isinstance(audio, np.ndarray):
                # Preprocess audio
                wav = preprocess_wav(audio, source_sr=SAMPLE_RATE)
            else:
                wav = audio

            # Extract embedding
            embedding = encoder.embed_utterance(wav)
            # print(f"[SPEECH_AUTH] ✅ Embedding extracted: shape={embedding.shape}")
            log_debug(f"Speaker embedding extracted: shape={embedding.shape}")
            return embedding

        except Exception as e:
            # print(f"[SPEECH_AUTH] Embedding extraction error: {e}")
            log_error(f"Speaker embedding error: {e}")
            return None

    # ── Speaker Profile Registration ──────────────────────────

    def register_speaker_profile(self, username, progress_callback=None):
        """
        Register speaker profile for user
        Records SPEAKER_SAMPLES_REQUIRED voice samples
        Saves embeddings as .npy files
        """
        # print(f"[SPEECH_AUTH] Registering speaker profile: {username}")
        log_info(f"Speaker profile registration: {username}")

        samples_saved = 0

        try:
            # Ensure speaker directory exists
            speaker_dir = get_user_speaker_dir(username)
            ensure_dir(speaker_dir)

            sample_instructions = [
                "Please speak freely for 5 seconds",
                "Say your name and a few words",
                "Count from 1 to 10 slowly"
            ]

            for i in range(SPEAKER_SAMPLES_REQUIRED):
                instruction = sample_instructions[i]
                # print(f"[SPEECH_AUTH] Sample {i+1}/{SPEAKER_SAMPLES_REQUIRED}: {instruction}")

                if progress_callback:
                    progress_callback(
                        i + 1,
                        SPEAKER_SAMPLES_REQUIRED,
                        instruction
                    )

                time.sleep(1.0)

                # Record audio
                audio = self._record_audio(RECORD_DURATION_SPEAKER)
                if audio is None:
                    # print(f"[SPEECH_AUTH] Failed to record sample {i+1}")
                    log_warning(f"Failed to record speaker sample {i+1}")
                    continue

                # Extract embedding
                embedding = self._extract_speaker_embedding(audio)
                if embedding is None:
                    # print(f"[SPEECH_AUTH] No embedding for sample {i+1}")
                    log_warning(f"No embedding for speaker sample {i+1}")
                    continue

                # Save embedding
                filepath = os.path.join(speaker_dir, f"embedding_{i+1}.npy")
                save_numpy(filepath, embedding)
                samples_saved += 1
                # print(f"[SPEECH_AUTH] ✅ Speaker sample {i+1} saved")
                log_info(f"Speaker sample {i+1} saved")

                if progress_callback:
                    progress_callback(
                        i + 1,
                        SPEAKER_SAMPLES_REQUIRED,
                        f"Sample {i+1} recorded successfully"
                    )

            if samples_saved < 1:
                return False, "Failed to record speaker samples"

            # Update profile
            profile = load_profile(username)
            profile['speaker_samples'] = samples_saved
            profile['speaker_registered_at'] = get_timestamp()
            save_profile(username, profile)

            # print(f"[SPEECH_AUTH] ✅ Speaker registration complete: {samples_saved} samples")
            log_info(f"Speaker registration complete: {samples_saved} samples")
            return True, f"Speaker profile registered with {samples_saved} samples"

        except Exception as e:
            # print(f"[SPEECH_AUTH] Speaker registration error: {e}")
            log_error(f"Speaker registration error: {e}")
            return False, str(e)

    # ── Speaker Verification ──────────────────────────────────

    def verify(self, audio, username):
        """
        Verify speaker identity from audio
        Called on EVERY command from pipeline
        Runs in parallel with command preparation
        Returns True if authorized speaker
        """
        # print(f"[SPEECH_AUTH] Verifying speaker: {username}")
        log_debug(f"Speaker verification: {username}")

        try:
            # Load stored embeddings
            stored_embeddings = self._load_speaker_embeddings(username)
            if not stored_embeddings:
                # print(f"[SPEECH_AUTH] No speaker profile for: {username}")
                log_warning(f"No speaker profile: {username}")
                # If no profile registered, allow (first time setup)
                return True

            # Get audio for verification
            if audio is None:
                # print("[SPEECH_AUTH] No audio for verification")
                log_warning("No audio for speaker verification")
                return False

            # Extract live embedding
            live_embedding = self._extract_speaker_embedding(audio)
            if live_embedding is None:
                # print("[SPEECH_AUTH] Could not extract live embedding")
                log_warning("Could not extract live speaker embedding")
                return False

            # Compare against all stored embeddings
            best_similarity = 0.0

            for i, stored_embedding in enumerate(stored_embeddings):
                similarity = self._cosine_similarity(
                    live_embedding,
                    stored_embedding
                )
                # print(f"[SPEECH_AUTH] Sample {i+1} similarity: {similarity:.4f}")
                log_debug(f"Speaker sample {i+1} similarity: {similarity:.4f}")

                if similarity > best_similarity:
                    best_similarity = similarity

            # print(f"[SPEECH_AUTH] Best similarity: {best_similarity:.4f} | Threshold: {SPEAKER_SIMILARITY_THRESHOLD}")
            authorized = best_similarity >= SPEAKER_SIMILARITY_THRESHOLD
            log_info(f"Best similarity: {best_similarity:.4f} | Threshold: {SPEAKER_SIMILARITY_THRESHOLD}")
            
            if authorized:
                # print(f"[SPEECH_AUTH] ✅ Speaker verified: {username}")
                log_debug(f"Speaker verified: {username}")
            else:
                # print(f"[SPEECH_AUTH] ❌ Speaker not recognized: {username}")
                log_warning(f"Speaker not recognized: {username}")

            return authorized

        except Exception as e:
            # print(f"[SPEECH_AUTH] Verification error: {e}")
            log_error(f"Speaker verification error: {e}")
            # On error, allow to prevent blocking
            return True

    # ── Voice Password Registration ───────────────────────────

    def register_voice_password(self, username, passphrase,
                                 language, progress_callback=None):
        """
        Register voice password for user
        Records passphrase 3 times
        Saves average embedding + passphrase text
        """
        # print(f"[SPEECH_AUTH] Registering voice password: {username}")
        log_info(f"Voice password registration: {username}")

        try:
            voice_pass_dir = get_user_voice_pass_dir(username)
            ensure_dir(voice_pass_dir)

            embeddings = []

            for i in range(3):
                # print(f"[SPEECH_AUTH] Voice pass sample {i+1}/3")

                if progress_callback:
                    progress_callback(
                        i + 1, 3,
                        f"Say your passphrase: '{passphrase}'"
                    )

                time.sleep(1.5)

                # Record
                audio = self._record_audio(RECORD_DURATION_PASS)
                if audio is None:
                    continue

                # Extract embedding
                embedding = self._extract_speaker_embedding(audio)
                if embedding is not None:
                    embeddings.append(embedding)
                    # print(f"[SPEECH_AUTH] ✅ Voice pass sample {i+1} recorded")

                if progress_callback:
                    progress_callback(
                        i + 1, 3,
                        f"Sample {i+1} recorded"
                    )

            if not embeddings:
                return False, "Failed to record voice password"

            # Average all embeddings for robustness
            avg_embedding = np.mean(embeddings, axis=0)

            # Save average embedding
            embedding_path = os.path.join(voice_pass_dir, "voice_pass.npy")
            save_numpy(embedding_path, avg_embedding)

            # Save passphrase text in profile
            profile = load_profile(username)
            profile['voice_passphrase'] = passphrase
            profile['voice_passphrase_language'] = language
            profile['voice_pass_registered_at'] = get_timestamp()

            if 'voice' not in profile.get('auth_methods', []):
                profile.setdefault('auth_methods', []).append('voice')

            save_profile(username, profile)

            # print(f"[SPEECH_AUTH] ✅ Voice password registered: {username}")
            log_info(f"Voice password registered: {username}")
            return True, "Voice password registered successfully"

        except Exception as e:
            # print(f"[SPEECH_AUTH] Voice password reg error: {e}")
            log_error(f"Voice password registration error: {e}")
            return False, str(e)

    # ── Voice Password Login ──────────────────────────────────

    def login_with_voice_password(self, username):
        """
        Login using voice password
        Records user saying passphrase
        Verifies BOTH text AND voice similarity
        Returns (success, message)
        """
        # print(f"[SPEECH_AUTH] Voice password login: {username}")
        log_info(f"Voice password login: {username}")

        try:
            # Load profile
            profile = load_profile(username)
            if not profile:
                return False, "User not found"

            stored_passphrase = profile.get('voice_passphrase')
            language = profile.get('voice_passphrase_language', 'en')

            if not stored_passphrase:
                return False, "Voice password not registered"

            # Load stored voice embedding
            voice_pass_dir = get_user_voice_pass_dir(username)
            embedding_path = os.path.join(voice_pass_dir, "voice_pass.npy")
            stored_embedding = load_numpy(embedding_path)

            if stored_embedding is None:
                return False, "Voice password embedding not found"

            # Record live audio
            # print("[SPEECH_AUTH] Recording voice password...")
            audio = self._record_audio(RECORD_DURATION_PASS)
            if audio is None:
                return False, "Failed to record audio"

            # ── Check 1: Text match via Whisper ───────────────
            # print("[SPEECH_AUTH] Transcribing for text match...")
            transcribed = self._transcribe_audio(audio, language)
            # print(f"[SPEECH_AUTH] Transcribed: '{transcribed}'")
            # print(f"[SPEECH_AUTH] Expected: '{stored_passphrase}'")

            text_match = self._check_text_match(
                transcribed,
                stored_passphrase
            )
            # print(f"[SPEECH_AUTH] Text match: {text_match}")

            if not text_match:
                # print("[SPEECH_AUTH] ❌ Passphrase text mismatch")
                log_warning(f"Voice passphrase text mismatch: {username}")
                return False, "Incorrect passphrase"

            # ── Check 2: Voice similarity ─────────────────────
            # print("[SPEECH_AUTH] Checking voice similarity...")
            live_embedding = self._extract_speaker_embedding(audio)

            if live_embedding is None:
                return False, "Could not extract voice features"

            similarity = self._cosine_similarity(live_embedding, stored_embedding)
            # print(f"[SPEECH_AUTH] Voice similarity: {similarity:.4f}")
            log_debug(f"Voice password similarity: {similarity:.4f}")

            if similarity >= VOICE_PASS_THRESHOLD:
                # print(f"[SPEECH_AUTH] ✅ Voice password login: {username}")
                log_info(f"Voice password login successful: {username}")
                return True, "Voice authentication successful"
            else:
                # print(f"[SPEECH_AUTH] ❌ Voice similarity too low: {similarity:.4f}")
                log_warning(f"Voice similarity too low: {similarity:.4f}")
                return False, "Voice not recognized"

        except Exception as e:
            # print(f"[SPEECH_AUTH] Voice login error: {e}")
            log_error(f"Voice password login error: {e}")
            return False, str(e)

    # ── Transcribe Audio ──────────────────────────────────────

    def _transcribe_audio(self, audio, language='en'):
        """Transcribe audio using Whisper small"""
        # print(f"[SPEECH_AUTH] Transcribing audio in: {language}")
        try:
            from NLP.speech.asr.asr_loader import get_asr_model
            model = get_asr_model()

            if model is None:
                log_error("ASR model not available")
                return ""

            import tempfile
            import soundfile as sf

            # Save to temp file
            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"auth_audio_{int(time.time())}.wav"
            )

            try:
                sf.write(temp_path, audio, SAMPLE_RATE)
                segments, info = model.transcribe(
                    temp_path,
                    language=language,
                    beam_size=5
                )
                text = " ".join([s.text for s in segments]).strip().lower()
                # print(f"[SPEECH_AUTH] Transcription: '{text}'")
                return text
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            # print(f"[SPEECH_AUTH] Transcription error: {e}")
            log_error(f"Auth transcription error: {e}")
            return ""

    def _check_text_match(self, transcribed, expected):
        """
        Check if transcribed text matches expected passphrase
        Flexible matching - handles small errors
        """
        # print(f"[SPEECH_AUTH] Text match: '{transcribed}' vs '{expected}'")
        if not transcribed or not expected:
            return False

        transcribed_lower = transcribed.lower().strip()
        expected_lower = expected.lower().strip()

        # Exact match
        if transcribed_lower == expected_lower:
            # print("[SPEECH_AUTH] Exact match")
            return True

        # Check if expected words are in transcription
        expected_words = set(expected_lower.split())
        transcribed_words = set(transcribed_lower.split())

        if not expected_words:
            return False

        # At least 70% of words must match
        common_words = expected_words.intersection(transcribed_words)
        match_ratio = len(common_words) / len(expected_words)
        # print(f"[SPEECH_AUTH] Word match ratio: {match_ratio:.2f}")

        return match_ratio >= 0.70

    # ── Load Speaker Embeddings ───────────────────────────────

    def _load_speaker_embeddings(self, username):
        """Load all stored speaker embeddings"""
        # print(f"[SPEECH_AUTH] Loading speaker embeddings: {username}")
        try:
            speaker_dir = get_user_speaker_dir(username)
            if not os.path.exists(speaker_dir):
                return []

            embeddings = []
            for filename in sorted(os.listdir(speaker_dir)):
                if filename.endswith('.npy'):
                    filepath = os.path.join(speaker_dir, filename)
                    embedding = load_numpy(filepath)
                    if embedding is not None:
                        embeddings.append(embedding)

            # print(f"[SPEECH_AUTH] Loaded {len(embeddings)} speaker embeddings")
            log_debug(f"Loaded {len(embeddings)} speaker embeddings")
            return embeddings

        except Exception as e:
            # print(f"[SPEECH_AUTH] Load embeddings error: {e}")
            log_error(f"Load speaker embeddings error: {e}")
            return []

    # ── Similarity ────────────────────────────────────────────

    def _cosine_similarity(self, embedding1, embedding2):
        """
        Calculate cosine similarity between embeddings
        Higher = more similar (0 to 1)
        """
        try:
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            # print(f"[SPEECH_AUTH] Similarity error: {e}")
            log_error(f"Cosine similarity error: {e}")
            return 0.0

    # ── Add Speaker Sample ────────────────────────────────────

    def add_speaker_sample(self, username, progress_callback=None):
        """Add additional speaker sample"""
        # print(f"[SPEECH_AUTH] Adding speaker sample: {username}")
        log_info(f"Adding speaker sample: {username}")

        try:
            speaker_dir = get_user_speaker_dir(username)
            ensure_dir(speaker_dir)

            existing = [f for f in os.listdir(speaker_dir) if f.endswith('.npy')]
            next_index = len(existing) + 1

            if progress_callback:
                progress_callback(1, 1, "Please speak freely for 5 seconds")

            time.sleep(1.0)
            audio = self._record_audio(RECORD_DURATION_SPEAKER)

            if audio is None:
                return False, "Failed to record audio"

            embedding = self._extract_speaker_embedding(audio)
            if embedding is None:
                return False, "Could not extract voice features"

            filepath = os.path.join(speaker_dir, f"embedding_{next_index}.npy")
            save_numpy(filepath, embedding)

            profile = load_profile(username)
            profile['speaker_samples'] = next_index
            save_profile(username, profile)

            # print(f"[SPEECH_AUTH] ✅ Speaker sample {next_index} added")
            log_info(f"Speaker sample {next_index} added")
            return True, f"Speaker sample {next_index} added"

        except Exception as e:
            # print(f"[SPEECH_AUTH] Add sample error: {e}")
            log_error(f"Add speaker sample error: {e}")
            return False, str(e)

    # ── Delete Data ───────────────────────────────────────────

    def delete_speaker_profile(self, username):
        """Delete speaker profile"""
        # print(f"[SPEECH_AUTH] Deleting speaker profile: {username}")
        log_info(f"Deleting speaker profile: {username}")
        try:
            import shutil
            speaker_dir = get_user_speaker_dir(username)
            if os.path.exists(speaker_dir):
                shutil.rmtree(speaker_dir)
                os.makedirs(speaker_dir)

            profile = load_profile(username)
            profile['speaker_samples'] = 0
            save_profile(username, profile)

            # print(f"[SPEECH_AUTH] ✅ Speaker profile deleted: {username}")
            return True
        except Exception as e:
            # print(f"[SPEECH_AUTH] Delete error: {e}")
            log_error(f"Delete speaker profile error: {e}")
            return False

    def delete_voice_password(self, username):
        """Delete voice password"""
        # print(f"[SPEECH_AUTH] Deleting voice password: {username}")
        log_info(f"Deleting voice password: {username}")
        try:
            voice_pass_dir = get_user_voice_pass_dir(username)
            embedding_path = os.path.join(voice_pass_dir, "voice_pass.npy")

            if os.path.exists(embedding_path):
                os.remove(embedding_path)

            profile = load_profile(username)
            profile['voice_passphrase'] = None
            if 'voice' in profile.get('auth_methods', []):
                profile['auth_methods'].remove('voice')
            save_profile(username, profile)

            # print(f"[SPEECH_AUTH] ✅ Voice password deleted: {username}")
            return True
        except Exception as e:
            # print(f"[SPEECH_AUTH] Delete voice pass error: {e}")
            log_error(f"Delete voice password error: {e}")
            return False

    # ── Check Registration ────────────────────────────────────

    def is_speaker_registered(self, username):
        """Check if speaker profile registered"""
        # print(f"[SPEECH_AUTH] Checking speaker registration: {username}")
        try:
            speaker_dir = get_user_speaker_dir(username)
            if not os.path.exists(speaker_dir):
                return False
            files = [f for f in os.listdir(speaker_dir) if f.endswith('.npy')]
            registered = len(files) > 0
            # print(f"[SPEECH_AUTH] Speaker registered: {registered}")
            return registered
        except Exception as e:
            log_error(f"Check speaker registration error: {e}")
            return False

    def is_voice_password_registered(self, username):
        """Check if voice password registered"""
        # print(f"[SPEECH_AUTH] Checking voice password: {username}")
        try:
            voice_pass_dir = get_user_voice_pass_dir(username)
            embedding_path = os.path.join(voice_pass_dir, "voice_pass.npy")
            registered = os.path.exists(embedding_path)
            # print(f"[SPEECH_AUTH] Voice password registered: {registered}")
            return registered
        except Exception as e:
            log_error(f"Check voice password error: {e}")
            return False


# ── Singleton Instance ────────────────────────────────────────

_speech_auth = None

def get_speech_auth():
    global _speech_auth
    if _speech_auth is None:
        # print("[SPEECH_AUTH] Creating singleton SpeechAuth...")
        _speech_auth = SpeechAuth()
    return _speech_auth
'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `_load_encoder()` | Load Resemblyzer VoiceEncoder |
| `_record_audio()` | Record from microphone |
| `_extract_speaker_embedding()` | 256-dim voice embedding |
| `register_speaker_profile()` | 3 speaker samples saved |
| `verify()` | Per-command speaker check (parallel) |
| `register_voice_password()` | Record passphrase 3 times |
| `login_with_voice_password()` | Text + voice dual check |
| `_transcribe_audio()` | Whisper transcription |
| `_check_text_match()` | 70% word match flexibility |
| `_cosine_similarity()` | Similarity calculation |
| `add_speaker_sample()` | Add extra sample |
| `delete_speaker_profile()` | Remove speaker data |
| `delete_voice_password()` | Remove voice password |
| `get_speech_auth()` | Singleton — creates once |

---

## Dual verification for voice password:
```
User says passphrase
        ↓
Check 1: Text match via Whisper
(did they say the right words?)
        ↓
Check 2: Voice similarity via Resemblyzer
(is it the right person saying it?)
        ↓
Both must pass → Login ✅
'''