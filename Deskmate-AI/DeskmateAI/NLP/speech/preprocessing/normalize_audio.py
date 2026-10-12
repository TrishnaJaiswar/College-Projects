# DeskmateAI/NLP/speech/preprocessing/normalize_audio.py

import os
import sys
import numpy as np

# ============================================================
# AUDIO NORMALIZER FOR DESKMATEAI
# Normalizes audio signal for consistent ASR input
# Handles volume normalization, sample rate conversion
# DC offset removal, clipping prevention
# Optimized for low spec PCs - no heavy processing
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Constants ─────────────────────────────────────────────────

TARGET_SAMPLE_RATE = 16000    # Whisper expects 16kHz
TARGET_RMS = 0.3              # Target RMS level
MAX_AMPLITUDE = 0.95          # Prevent clipping
MIN_AMPLITUDE = 0.001         # Minimum meaningful amplitude

# ── Audio Normalizer Class ────────────────────────────────────

class AudioNormalizer:

    def __init__(self):
        # print("[NORMALIZE] Initializing AudioNormalizer...")
        log_info("AudioNormalizer initialized")

    def normalize(self, audio, sample_rate=TARGET_SAMPLE_RATE):
        """
        Full normalization pipeline
        1. Convert to float32
        2. Remove DC offset
        3. Normalize amplitude
        4. Prevent clipping
        Returns normalized audio
        """
        # print("[NORMALIZE] Normalizing audio...")
        log_debug("Normalizing audio")

        if audio is None or len(audio) == 0:
            log_warning("Empty audio for normalization")
            return audio

        try:
            # Step 1: Convert to float32
            audio = self._to_float32(audio)

            # Step 2: Remove DC offset
            audio = self._remove_dc_offset(audio)

            # Step 3: Normalize amplitude
            audio = self._normalize_amplitude(audio)

            # Step 4: Prevent clipping
            audio = self._prevent_clipping(audio)

            # print("[NORMALIZE] ✅ Normalization complete")
            log_debug("Audio normalization complete")
            return audio

        except Exception as e:
            # print(f"[NORMALIZE] Normalization error: {e}")
            log_warning(f"Normalization failed: {e}")
            return audio

    def _to_float32(self, audio):
        """Convert audio to float32 numpy array"""
        # print("[NORMALIZE] Converting to float32...")
        try:
            if not isinstance(audio, np.ndarray):
                audio = np.array(audio)

            if audio.dtype == np.float32:
                return audio

            if audio.dtype == np.int16:
                # Convert int16 to float32
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            elif audio.dtype == np.uint8:
                audio = (audio.astype(np.float32) - 128) / 128.0
            else:
                audio = audio.astype(np.float32)

            # print("[NORMALIZE] ✅ Converted to float32")
            return audio

        except Exception as e:
            # print(f"[NORMALIZE] Float32 conversion error: {e}")
            log_error(f"Float32 conversion error: {e}")
            return audio

    def _remove_dc_offset(self, audio):
        """
        Remove DC offset from audio
        DC offset causes consistent positive/negative shift
        which degrades ASR quality
        """
        # print("[NORMALIZE] Removing DC offset...")
        try:
            mean = np.mean(audio)
            if abs(mean) > 0.001:
                audio = audio - mean
                # print(f"[NORMALIZE] DC offset removed: {mean:.4f}")
                log_debug(f"DC offset removed: {mean:.4f}")
            return audio
        except Exception as e:
            # print(f"[NORMALIZE] DC offset removal error: {e}")
            log_error(f"DC offset error: {e}")
            return audio

    def _normalize_amplitude(self, audio):
        """
        Normalize audio amplitude to target RMS
        Ensures consistent volume for ASR
        """
        try:
            rms = np.sqrt(np.mean(np.square(audio)))

            if rms < MIN_AMPLITUDE:
                log_warning(f"Audio very quiet: {rms:.6f}")
                return audio

            # Scale to target RMS
            scale = TARGET_RMS / rms
            # Cap at 10x to prevent distortion
            scale = min(scale, 10.0)
            normalized = audio * scale

            log_debug(f"Amplitude: {rms:.4f} → {TARGET_RMS} (scale: {scale:.2f}x)")
            return normalized

        except Exception as e:
            log_error(f"Amplitude normalization error: {e}")
            return audio
    def _prevent_clipping(self, audio):
        """
        Prevent audio clipping
        Clips values outside [-MAX_AMPLITUDE, MAX_AMPLITUDE]
        """
        # print("[NORMALIZE] Preventing clipping...")
        try:
            max_val = np.max(np.abs(audio))
            if max_val > MAX_AMPLITUDE:
                audio = audio * (MAX_AMPLITUDE / max_val)
                # print(f"[NORMALIZE] Clipping prevented: max={max_val:.4f}")
                log_debug(f"Clipping prevented: {max_val:.4f}")
            return audio
        except Exception as e:
            # print(f"[NORMALIZE] Clipping prevention error: {e}")
            log_error(f"Clipping prevention error: {e}")
            return audio

    def resample(self, audio, original_rate, target_rate=TARGET_SAMPLE_RATE):
        """
        Resample audio to target sample rate
        Whisper requires 16kHz
        """
        # print(f"[NORMALIZE] Resampling: {original_rate}Hz → {target_rate}Hz")
        log_debug(f"Resampling: {original_rate} → {target_rate}Hz")

        if original_rate == target_rate:
            # print("[NORMALIZE] No resampling needed")
            return audio

        try:
            import scipy.signal as signal

            # Calculate resampling ratio
            ratio = target_rate / original_rate
            new_length = int(len(audio) * ratio)

            resampled = signal.resample(audio, new_length)
            # print(f"[NORMALIZE] ✅ Resampled: {len(audio)} → {len(resampled)} samples")
            log_debug(f"Resampled: {len(audio)} → {len(resampled)} samples")
            return resampled.astype(np.float32)

        except Exception as e:
            # print(f"[NORMALIZE] Resampling error: {e}")
            log_error(f"Resampling error: {e}")
            return audio

    def convert_to_mono(self, audio):
        """
        Convert stereo audio to mono
        Whisper works with mono audio
        """
        # print("[NORMALIZE] Converting to mono...")
        try:
            if audio.ndim == 1:
                # print("[NORMALIZE] Already mono")
                return audio

            if audio.ndim == 2:
                # Average channels
                mono = np.mean(audio, axis=1)
                # print("[NORMALIZE] ✅ Converted to mono")
                log_debug("Converted stereo to mono")
                return mono.astype(np.float32)

            return audio

        except Exception as e:
            # print(f"[NORMALIZE] Mono conversion error: {e}")
            log_error(f"Mono conversion error: {e}")
            return audio

    def get_audio_stats(self, audio, sample_rate=TARGET_SAMPLE_RATE):
        """
        Get audio statistics for debugging
        Returns dict with audio properties
        """
        # print("[NORMALIZE] Getting audio stats...")
        try:
            if audio is None or len(audio) == 0:
                return {}

            stats = {
                "duration": len(audio) / sample_rate,
                "sample_rate": sample_rate,
                "samples": len(audio),
                "dtype": str(audio.dtype),
                "rms": float(np.sqrt(np.mean(np.square(audio)))),
                "max_amplitude": float(np.max(np.abs(audio))),
                "mean": float(np.mean(audio)),
                "is_mono": audio.ndim == 1
            }

            # print(f"[NORMALIZE] Stats: {stats}")
            return stats

        except Exception as e:
            # print(f"[NORMALIZE] Stats error: {e}")
            log_error(f"Audio stats error: {e}")
            return {}

    def prepare_for_whisper(self, audio, original_sample_rate=TARGET_SAMPLE_RATE):
        """
        Full preparation pipeline for Whisper ASR
        1. Convert to mono
        2. Resample to 16kHz
        3. Full normalization
        Returns whisper-ready audio
        """
        # print("[NORMALIZE] Preparing for Whisper...")
        log_debug("Preparing audio for Whisper")

        if audio is None or len(audio) == 0:
            log_warning("Empty audio for Whisper preparation")
            return audio

        try:
            # Step 1: Convert to mono
            audio = self.convert_to_mono(audio)

            # Step 2: Resample if needed
            if original_sample_rate != TARGET_SAMPLE_RATE:
                audio = self.resample(
                    audio,
                    original_sample_rate,
                    TARGET_SAMPLE_RATE
                )

            # Step 3: Full normalization
            audio = self.normalize(audio, TARGET_SAMPLE_RATE)

            # print("[NORMALIZE] ✅ Audio ready for Whisper")
            log_debug("Audio prepared for Whisper")
            return audio

        except Exception as e:
            # print(f"[NORMALIZE] Whisper preparation error: {e}")
            log_error(f"Whisper preparation error: {e}")
            return audio


# ── Singleton Instance ────────────────────────────────────────

_normalizer = None

def get_normalizer():
    global _normalizer
    if _normalizer is None:
        # print("[NORMALIZE] Creating singleton AudioNormalizer...")
        _normalizer = AudioNormalizer()
    return _normalizer


def normalize_audio(audio, sample_rate=TARGET_SAMPLE_RATE):
    """Convenience function for audio normalization"""
    return get_normalizer().prepare_for_whisper(audio, sample_rate)

'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `normalize()` | Full 4-step normalization |
| `_to_float32()` | Convert any dtype to float32 |
| `_remove_dc_offset()` | Remove DC bias |
| `_normalize_amplitude()` | Scale to target RMS |
| `_prevent_clipping()` | Prevent audio distortion |
| `resample()` | Convert sample rate to 16kHz |
| `convert_to_mono()` | Stereo to mono |
| `get_audio_stats()` | Debug audio properties |
| `prepare_for_whisper()` | Complete Whisper preparation |
| `get_normalizer()` | Singleton — creates once |

---

## Complete preprocessing pipeline:
```
Raw microphone audio
        ↓
noise_reduction.py → Remove background noise
        ↓
silence_trim.py → Remove silence edges + gaps
        ↓
normalize_audio.py → Prepare for Whisper:
    1. Convert to mono
    2. Resample to 16kHz
    3. Remove DC offset
    4. Normalize amplitude
    5. Prevent clipping
        ↓
Clean audio → Whisper ASR ✅
'''