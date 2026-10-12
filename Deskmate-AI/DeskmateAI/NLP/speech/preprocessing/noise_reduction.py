# DeskmateAI/NLP/speech/preprocessing/noise_reduction.py

import os
import sys
import numpy as np

# ============================================================
# NOISE REDUCTION FOR DESKMATEAI
# Removes background noise from audio
# Uses noisereduce library
# Optimized for low spec PCs
# Applied before ASR for better transcription
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Constants ─────────────────────────────────────────────────

SAMPLE_RATE = 16000
NOISE_REDUCE_PROP = 0.3      # How aggressively to reduce noise (0-1)
STATIONARY = True              # Use stationary noise reduction (faster)

# ── Noise Reducer Class ───────────────────────────────────────

class NoiseReducer:

    def __init__(self):
        # print("[NOISE] Initializing NoiseReducer...")
        self._nr = None
        self._load_library()
        log_info("NoiseReducer initialized")

    def _load_library(self):
        """Load noisereduce library"""
        # print("[NOISE] Loading noisereduce library...")
        try:
            import noisereduce as nr
            self._nr = nr
            # print("[NOISE] ✅ noisereduce loaded")
            log_debug("noisereduce loaded")
        except ImportError:
            # print("[NOISE] ❌ noisereduce not found")
            log_error("noisereduce not installed. Run: pip install noisereduce")
            self._nr = None

    def reduce_noise(self, audio, sample_rate=SAMPLE_RATE):
        """
        Apply noise reduction to audio
        Returns cleaned audio array
        Falls back to original if reduction fails
        """
        # print("[NOISE] Applying noise reduction...")
        log_debug("Applying noise reduction")

        if audio is None or len(audio) == 0:
            log_warning("Empty audio for noise reduction")
            return audio

        try:
            if self._nr is None:
                self._load_library()

            if self._nr is None:
                # print("[NOISE] Library not available, skipping")
                return audio

            # Apply noise reduction
            # Stationary mode is faster and works well for
            # consistent background noise (fan, AC etc.)
            reduced = self._nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                prop_decrease=NOISE_REDUCE_PROP,
                stationary=STATIONARY,
                n_jobs=1  # Single job for low spec PC
            )

            # print(f"[NOISE] ✅ Noise reduction complete")
            log_debug("Noise reduction complete")
            return reduced

        except Exception as e:
            # print(f"[NOISE] Noise reduction failed: {e}")
            log_warning(f"Noise reduction failed, using original: {e}")
            return audio  # Return original if reduction fails

    def reduce_noise_advanced(self, audio, sample_rate=SAMPLE_RATE):
        """
        Advanced noise reduction
        Uses first 0.5 seconds as noise profile
        Better for varying noise but slower
        """
        # print("[NOISE] Advanced noise reduction...")
        log_debug("Advanced noise reduction")

        if audio is None or len(audio) == 0:
            return audio

        try:
            if self._nr is None:
                self._load_library()

            if self._nr is None:
                return audio

            # Use first 0.5 seconds as noise sample
            noise_sample_duration = int(0.5 * sample_rate)
            if len(audio) > noise_sample_duration:
                noise_clip = audio[:noise_sample_duration]
            else:
                noise_clip = audio

            reduced = self._nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                y_noise=noise_clip,
                prop_decrease=NOISE_REDUCE_PROP,
                stationary=False
            )

            # print("[NOISE] ✅ Advanced noise reduction complete")
            log_debug("Advanced noise reduction complete")
            return reduced

        except Exception as e:
            # print(f"[NOISE] Advanced reduction failed: {e}")
            log_warning(f"Advanced noise reduction failed: {e}")
            return audio

    def estimate_noise_level(self, audio):
        """
        Estimate noise level in audio
        Returns noise level 0.0 to 1.0
        Used to decide if noise reduction needed
        """
        # print("[NOISE] Estimating noise level...")
        try:
            if audio is None or len(audio) == 0:
                return 0.0

            # RMS energy as noise estimate
            rms = np.sqrt(np.mean(np.square(audio)))
            # Normalize to 0-1 range
            noise_level = min(1.0, float(rms) * 10)
            # print(f"[NOISE] Noise level: {noise_level:.3f}")
            return noise_level

        except Exception as e:
            # print(f"[NOISE] Noise estimation failed: {e}")
            log_error(f"Noise estimation failed: {e}")
            return 0.0

    def smart_reduce(self, audio, sample_rate=SAMPLE_RATE):
        """
        Smart noise reduction
        Only applies if noise level is significant
        Saves CPU on quiet recordings
        """
        # print("[NOISE] Smart noise reduction...")

        if audio is None or len(audio) == 0:
            return audio

        noise_level = self.estimate_noise_level(audio)
        # print(f"[NOISE] Noise level: {noise_level:.3f}")

        if noise_level < 0.1:
            # print("[NOISE] Low noise, skipping reduction")
            log_debug(f"Noise level low ({noise_level:.3f}), skipping")
            return audio

        if noise_level < 0.4:
            # print("[NOISE] Medium noise, standard reduction")
            log_debug(f"Medium noise ({noise_level:.3f}), standard reduction")
            return self.reduce_noise(audio, sample_rate)

        # print("[NOISE] High noise, advanced reduction")
        log_debug(f"High noise ({noise_level:.3f}), advanced reduction")
        return self.reduce_noise_advanced(audio, sample_rate)


# ── Singleton Instance ────────────────────────────────────────

_noise_reducer = None

def get_noise_reducer():
    global _noise_reducer
    if _noise_reducer is None:
        # print("[NOISE] Creating singleton NoiseReducer...")
        _noise_reducer = NoiseReducer()
    return _noise_reducer


def reduce_noise(audio, sample_rate=SAMPLE_RATE):
    """Convenience function for noise reduction"""
    return get_noise_reducer().smart_reduce(audio, sample_rate)