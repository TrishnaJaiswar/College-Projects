# DeskmateAI/NLP/speech/asr/mic_stream.py

import os
import sys
import time
import threading
import numpy as np

# ============================================================
# MICROPHONE STREAM FOR DESKMATEAI
# Handles all microphone input
# Records command audio and dictation audio
# Detects end of speech automatically
# Uses Voice Activity Detection (VAD) to stop recording
# Optimized for low spec PCs
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Constants ─────────────────────────────────────────────────

SAMPLE_RATE = 16000
MIC_DEVICE  = None       # Realtek HD Audio Mic — cleaner than Intel array mic (device 1)
CHANNELS = 1
DTYPE = 'float32'

# Command recording settings
COMMAND_MAX_DURATION = 8.0      # Max seconds for command
COMMAND_MIN_DURATION = 0.5      # Min seconds before stopping
SILENCE_THRESHOLD = 0.012        # RMS below = silence
SILENCE_DURATION = 1.0          # Seconds of silence to stop

# Dictation recording settings
DICTATION_MAX_DURATION = 30.0   # Max seconds for dictation
DICTATION_SILENCE_DURATION = 2.0 # Longer pause to stop dictation

# ── Mic Stream Class ──────────────────────────────────────────

class MicStream:

    def __init__(self):
        # print("[MIC] Initializing MicStream...")
        self._recording = False
        self._audio_buffer = []
        self._lock = threading.Lock()
        log_info("MicStream initialized")

    # ── Device Info ───────────────────────────────────────────

    def get_input_devices(self):
        """Get list of available input devices"""
        # print("[MIC] Getting input devices...")
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = []
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        "index": i,
                        "name": device['name'],
                        "channels": device['max_input_channels'],
                        "sample_rate": device['default_samplerate']
                    })
            # print(f"[MIC] Found {len(input_devices)} input devices")
            log_debug(f"Input devices: {len(input_devices)}")
            return input_devices
        except Exception as e:
            # print(f"[MIC] Device query error: {e}")
            log_error(f"Input device query error: {e}")
            return []

    def get_default_device(self):
        """Get default input device"""
        # print("[MIC] Getting default device...")
        try:
            import sounddevice as sd
            device = sd.query_devices(kind='input')
            # print(f"[MIC] Default device: {device['name']}")
            log_debug(f"Default input: {device['name']}")
            return device
        except Exception as e:
            # print(f"[MIC] Default device error: {e}")
            log_error(f"Default device error: {e}")
            return None

    def test_microphone(self):
        """Test if microphone is working"""
        # print("[MIC] Testing microphone...")
        log_info("Testing microphone")
        try:
            import sounddevice as sd

            # Record 1 second test
            audio = sd.rec(
                SAMPLE_RATE,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocking=True,
                device=MIC_DEVICE
            )

            rms = float(np.sqrt(np.mean(np.square(audio))))
            # print(f"[MIC] Test RMS: {rms:.4f}")
            log_debug(f"Mic test RMS: {rms:.4f}")

            if rms > 0.0001:
                # print("[MIC] ✅ Microphone working")
                log_info("Microphone test passed")
                return True, "Microphone working"
            else:
                # print("[MIC] ⚠️ Microphone may be muted")
                log_warning("Microphone may be muted or disconnected")
                return False, "Microphone appears silent"

        except Exception as e:
            # print(f"[MIC] Microphone test failed: {e}")
            log_error(f"Microphone test failed: {e}")
            return False, str(e)

    # ── Record Command ────────────────────────────────────────

    def record_command(self):
        """
        Record voice command with automatic VAD stop
        Stops when:
        - User stops speaking (silence detected)
        - Max duration reached
        Returns audio array or None
        """
        # print("[MIC] Recording command...")
        log_info("Recording command")

        return self._record_with_vad(
            max_duration=COMMAND_MAX_DURATION,
            min_duration=COMMAND_MIN_DURATION,
            silence_duration=SILENCE_DURATION,
            silence_threshold=SILENCE_THRESHOLD
        )

    # ── Record Dictation ──────────────────────────────────────

    def record_dictation(self):
        """
        Record dictation audio
        Longer max duration and silence tolerance
        Returns audio array or None
        """
        # print("[MIC] Recording dictation...")
        log_info("Recording dictation")

        return self._record_with_vad(
            max_duration=DICTATION_MAX_DURATION,
            min_duration=1.0,
            silence_duration=DICTATION_SILENCE_DURATION,
            silence_threshold=SILENCE_THRESHOLD
        )

    # ── Record Fixed Duration ─────────────────────────────────

    def record_fixed(self, duration):
        """
        Record fixed duration audio
        Used for speaker verification samples
        Returns audio array or None
        """
        # print(f"[MIC] Recording fixed: {duration}s")
        log_info(f"Recording fixed {duration}s")

        try:
            import sounddevice as sd
            audio = sd.rec(
                        int(duration * SAMPLE_RATE),
                        samplerate=SAMPLE_RATE,
                        channels=CHANNELS,
                        dtype=DTYPE,
                        blocking=False,
                        device=MIC_DEVICE
                    )
                    # Wait without blocking Qt
            import time
            time.sleep(duration + 0.2)
            sd.stop()

            audio = audio.flatten()
            # print(f"[MIC] ✅ Fixed recording done: {len(audio)} samples")
            log_debug(f"Fixed recording: {len(audio)} samples")
            return audio

        except Exception as e:
            # print(f"[MIC] Fixed record error: {e}")
            log_error(f"Fixed record error: {e}")
            return None

    # ── VAD Recording ─────────────────────────────────────────

    def _record_with_vad(self, max_duration, min_duration,
                          silence_duration, silence_threshold):
        """
        Record with Voice Activity Detection
        Automatically stops when user stops speaking
        """
        # print(f"[MIC] VAD recording: max={max_duration}s silence={silence_duration}s")
        log_debug(f"VAD recording: max={max_duration}s")

        try:
            import sounddevice as sd

            # Frame settings
            frame_duration = 0.1  # 100ms frames
            frame_samples = int(frame_duration * SAMPLE_RATE)
            max_frames = int(max_duration / frame_duration)
            min_frames = int(min_duration / frame_duration)
            silence_frames = int(silence_duration / frame_duration)

            audio_frames = []
            silent_frame_count = 0
            speech_detected = False
            frame_count = 0

            # print("[MIC] VAD started, speak now...")

            while frame_count < max_frames:
                # Record one frame
                frame = sd.rec(
                    frame_samples,
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    blocking=False,
                    device=MIC_DEVICE
                )
                import time
                time.sleep(frame_duration + 0.02)
                sd.stop()
                frame = frame.flatten()
                frame_count += 1

                # Calculate RMS
                rms = float(np.sqrt(np.mean(np.square(frame))))

                if rms > silence_threshold:
                    # Speech detected
                    speech_detected = True
                    silent_frame_count = 0
                    # print(f"[MIC] Speech: RMS={rms:.4f}")
                else:
                    # Silence
                    if speech_detected:
                        silent_frame_count += 1
                        # print(f"[MIC] Silence: {silent_frame_count}/{silence_frames}")
                
                # Only keep frames once speech has begun
                if speech_detected:
                    audio_frames.append(frame)
                    
                # Stop conditions
                if (speech_detected and
                    frame_count >= min_frames and
                    silent_frame_count >= silence_frames):
                    # print("[MIC] VAD stop: silence after speech")
                    break

            if not audio_frames:
                log_warning("No audio frames recorded")
                return None

            # Concatenate all frames
            audio = np.concatenate(audio_frames)
            duration = len(audio) / SAMPLE_RATE

            # print(f"[MIC] ✅ VAD recording done: {duration:.2f}s | Speech: {speech_detected}")
            log_info(f"VAD recording: {duration:.2f}s | Speech: {speech_detected}")

            if not speech_detected:
                log_warning("No speech detected in recording")
                return None

            return audio

        except Exception as e:
            # print(f"[MIC] VAD record error: {e}")
            log_error(f"VAD record error: {e}")
            return None

    # ── Audio Level ───────────────────────────────────────────

    def get_audio_level(self):
        """
        Get current microphone audio level
        Used by UI waveform animation
        Returns RMS level 0.0 to 1.0
        """
        try:
            import sounddevice as sd

            frame = sd.rec(
                int(0.05 * SAMPLE_RATE),  # 50ms
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocking=True,
                device=MIC_DEVICE
            )
            rms = float(np.sqrt(np.mean(np.square(frame))))
            # Normalize to 0-1
            level = min(1.0, rms * 10)
            return level

        except Exception as e:
            # print(f"[MIC] Audio level error: {e}")
            return 0.0

    def stream_audio_levels(self, callback, stop_event):
        """
        Stream audio levels continuously
        Calls callback with level value
        Stops when stop_event is set
        Used by waveform animation in UI
        """
        # print("[MIC] Starting audio level stream...")
        log_debug("Audio level stream started")

        try:
            import sounddevice as sd

            def audio_callback(indata, frames, time_info, status):
                if stop_event.is_set():
                    raise sd.CallbackStop()
                rms = float(np.sqrt(np.mean(np.square(indata))))
                level = min(1.0, rms * 10)
                if callback:
                    callback(level)

            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=int(0.05 * SAMPLE_RATE),
                callback=audio_callback,
                device=MIC_DEVICE
            ):
                while not stop_event.is_set():
                    time.sleep(0.05)

        except Exception as e:
            if "CallbackStop" not in str(e):
                # print(f"[MIC] Level stream error: {e}")
                log_error(f"Level stream error: {e}")

        # print("[MIC] Audio level stream stopped")
        log_debug("Audio level stream stopped")


# ── Singleton Instance ────────────────────────────────────────

_mic_stream = None

def get_mic_stream():
    global _mic_stream
    if _mic_stream is None:
        # print("[MIC] Creating singleton MicStream...")
        _mic_stream = MicStream()
    return _mic_stream
'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `get_input_devices()` | List all microphones |
| `get_default_device()` | Get default mic |
| `test_microphone()` | Check if mic working |
| `record_command()` | VAD recording for commands |
| `record_dictation()` | VAD recording for dictation |
| `record_fixed()` | Fixed duration recording |
| `_record_with_vad()` | Core VAD recording engine |
| `get_audio_level()` | Single level reading |
| `stream_audio_levels()` | Continuous level stream for UI |
| `get_mic_stream()` | Singleton — creates once |

---

## VAD (Voice Activity Detection) logic:
```
Start recording 100ms frames
        ↓
Frame RMS > threshold?
    YES → speech_detected = True
           reset silence counter
    NO  → silence counter++
        ↓
speech_detected AND
silence_count >= silence_frames AND
min_duration passed?
        ↓
Stop recording ✅
'''