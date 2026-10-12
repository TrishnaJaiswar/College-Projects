# DeskmateAI/NLP/speech/preprocessing/silence_trim.py

import os
import sys
import numpy as np

# ============================================================
# SILENCE TRIMMER FOR DESKMATEAI
# Removes silence from beginning and end of audio
# Also removes long silence gaps in middle
# Improves ASR accuracy and reduces processing time
# Optimized for low spec PCs
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Constants ─────────────────────────────────────────────────

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.002      # RMS below this = silence
MIN_SILENCE_DURATION = 0.3    # Minimum silence to trim (seconds)
PADDING = 0.1                 # Keep some silence at edges (seconds)
MAX_SILENCE_GAP = 1.0         # Maximum allowed silence gap (seconds)

# ── Silence Trimmer Class ─────────────────────────────────────

class SilenceTrimmer:

    def __init__(self):
        # print("[SILENCE] Initializing SilenceTrimmer...")
        log_info("SilenceTrimmer initialized")

    def trim_silence(self, audio, sample_rate=SAMPLE_RATE,
                     threshold=SILENCE_THRESHOLD):
        """
        Trim silence from beginning and end of audio
        Returns trimmed audio with small padding kept
        """
        # print("[SILENCE] Trimming silence...")
        log_debug("Trimming silence from audio")

        if audio is None or len(audio) == 0:
            log_warning("Empty audio for silence trim")
            return audio

        try:
            # Calculate frame size
            frame_size = int(0.02 * sample_rate)  # 20ms frames

            if len(audio) < frame_size:
                # print("[SILENCE] Audio too short to trim")
                return audio

            # Calculate RMS for each frame
            frames = self._get_frames(audio, frame_size)
            rms_values = np.array([self._rms(frame) for frame in frames])

            # Find non-silent frames
            non_silent = np.where(rms_values > threshold)[0]

            if len(non_silent) == 0:
                # print("[SILENCE] All silence - returning empty")
                log_warning("Audio is all silence")
                return audio  # Return original if all silent

            # Get start and end indices
            start_frame = max(0, non_silent[0] - int(PADDING / 0.02))
            end_frame = min(
                len(frames),
                non_silent[-1] + int(PADDING / 0.02) + 1
            )

            # Convert to sample indices
            start_sample = start_frame * frame_size
            end_sample = min(len(audio), end_frame * frame_size)

            trimmed = audio[start_sample:end_sample]

            original_duration = len(audio) / sample_rate
            trimmed_duration = len(trimmed) / sample_rate

            # print(f"[SILENCE] ✅ Trimmed: {original_duration:.2f}s → {trimmed_duration:.2f}s")
            log_debug(f"Silence trimmed: {original_duration:.2f}s → {trimmed_duration:.2f}s")
            return trimmed

        except Exception as e:
            # print(f"[SILENCE] Trim error: {e}")
            log_warning(f"Silence trim failed: {e}")
            return audio

    def remove_silence_gaps(self, audio, sample_rate=SAMPLE_RATE,
                             threshold=SILENCE_THRESHOLD,
                             max_gap=MAX_SILENCE_GAP):
        """
        Remove long silence gaps from middle of audio
        Keeps natural pauses but removes dead air
        """
        # print("[SILENCE] Removing silence gaps...")
        log_debug("Removing silence gaps")

        if audio is None or len(audio) == 0:
            return audio

        try:
            frame_size = int(0.02 * sample_rate)  # 20ms frames
            max_silent_frames = int(max_gap / 0.02)
            min_silent_frames = int(MIN_SILENCE_DURATION / 0.02)

            frames = self._get_frames(audio, frame_size)
            rms_values = np.array([self._rms(frame) for frame in frames])

            result_frames = []
            silent_count = 0

            for i, (frame, rms) in enumerate(zip(frames, rms_values)):
                if rms > threshold:
                    # Non-silent frame
                    if silent_count > 0 and silent_count >= min_silent_frames:
                        # Add limited silence gap
                        gap_frames = min(silent_count, max_silent_frames)
                        silence = np.zeros(gap_frames * frame_size)
                        result_frames.append(silence)
                    silent_count = 0
                    result_frames.append(frame)
                else:
                    silent_count += 1

            if not result_frames:
                return audio

            result = np.concatenate(result_frames)
            original_duration = len(audio) / sample_rate
            result_duration = len(result) / sample_rate

            # print(f"[SILENCE] ✅ Gaps removed: {original_duration:.2f}s → {result_duration:.2f}s")
            log_debug(f"Gaps removed: {original_duration:.2f}s → {result_duration:.2f}s")
            return result

        except Exception as e:
            # print(f"[SILENCE] Gap removal error: {e}")
            log_warning(f"Gap removal failed: {e}")
            return audio

    def is_silent(self, audio, threshold=SILENCE_THRESHOLD):
        """
        Check if audio is mostly silent
        Returns True if silent
        """
        # print("[SILENCE] Checking if silent...")
        try:
            if audio is None or len(audio) == 0:
                return True

            rms = self._rms(audio)
            is_silent = rms < threshold
            # print(f"[SILENCE] RMS: {rms:.4f} | Silent: {is_silent}")
            log_debug(f"Audio RMS: {rms:.4f} | Silent: {is_silent}")
            return is_silent

        except Exception as e:
            # print(f"[SILENCE] Silent check error: {e}")
            log_error(f"Silent check error: {e}")
            return False

    def get_speech_duration(self, audio, sample_rate=SAMPLE_RATE,
                            threshold=SILENCE_THRESHOLD):
        """
        Get duration of actual speech (non-silent) in audio
        Returns duration in seconds
        """
        # print("[SILENCE] Getting speech duration...")
        try:
            if audio is None or len(audio) == 0:
                return 0.0

            frame_size = int(0.02 * sample_rate)
            frames = self._get_frames(audio, frame_size)
            rms_values = np.array([self._rms(frame) for frame in frames])

            speech_frames = np.sum(rms_values > threshold)
            duration = (speech_frames * frame_size) / sample_rate

            # print(f"[SILENCE] Speech duration: {duration:.2f}s")
            log_debug(f"Speech duration: {duration:.2f}s")
            return duration

        except Exception as e:
            # print(f"[SILENCE] Duration error: {e}")
            log_error(f"Speech duration error: {e}")
            return len(audio) / sample_rate if audio is not None else 0.0

    def has_speech(self, audio, sample_rate=SAMPLE_RATE,
                   min_speech_duration=0.3):
        """
        Check if audio contains enough speech
        Returns True if speech detected
        """
        # print("[SILENCE] Checking for speech...")
        try:
            duration = self.get_speech_duration(audio, sample_rate)
            has_speech = duration >= min_speech_duration
            # print(f"[SILENCE] Has speech: {has_speech} ({duration:.2f}s)")
            log_debug(f"Has speech: {has_speech} ({duration:.2f}s)")
            return has_speech
        except Exception as e:
            # print(f"[SILENCE] Has speech check error: {e}")
            log_error(f"Has speech check error: {e}")
            return True  # Assume has speech on error

    def full_process(self, audio, sample_rate=SAMPLE_RATE):
        """
        Full silence processing pipeline
        1. Trim edges
        2. Remove long gaps
        Returns processed audio
        """
        # print("[SILENCE] Full silence processing...")
        log_debug("Full silence processing")

        if audio is None or len(audio) == 0:
            return audio

        # Check if has speech first
        if not self.has_speech(audio, sample_rate):
            # print("[SILENCE] No speech detected")
            log_warning("No speech detected in audio")
            return audio

        # Step 1: Trim edges
        trimmed = self.trim_silence(audio, sample_rate)

        # Step 2: Remove gaps
        processed = self.remove_silence_gaps(trimmed, sample_rate)

        # print("[SILENCE] ✅ Full silence processing done")
        log_debug("Silence processing complete")
        return processed

    # ── Helper Functions ──────────────────────────────────────

    def _get_frames(self, audio, frame_size):
        """Split audio into frames"""
        frames = []
        for i in range(0, len(audio) - frame_size + 1, frame_size):
            frames.append(audio[i:i + frame_size])
        return frames

    def _rms(self, frame):
        """Calculate RMS energy of frame"""
        if len(frame) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(frame.astype(np.float32)))))


# ── Singleton Instance ────────────────────────────────────────

_silence_trimmer = None

def get_silence_trimmer():
    global _silence_trimmer
    if _silence_trimmer is None:
        # print("[SILENCE] Creating singleton SilenceTrimmer...")
        _silence_trimmer = SilenceTrimmer()
    return _silence_trimmer


def trim_silence(audio, sample_rate=SAMPLE_RATE):
    """Convenience function for silence trimming"""
    return get_silence_trimmer().full_process(audio, sample_rate)

'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `trim_silence()` | Remove silence from edges |
| `remove_silence_gaps()` | Remove long gaps in middle |
| `is_silent()` | Check if audio is all silence |
| `get_speech_duration()` | Measure actual speech time |
| `has_speech()` | Check minimum speech threshold |
| `full_process()` | Complete silence processing |
| `get_silence_trimmer()` | Singleton — creates once |

---

## Processing pipeline:
```
Raw audio
        ↓
Check has speech (≥0.3s)
        ↓
Trim silence from edges
        ↓
Remove gaps > 1.0s
        ↓
Clean audio ready for ASR ✅
'''