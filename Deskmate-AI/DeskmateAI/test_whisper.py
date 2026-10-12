# test_whisper.py
# Tests small vs medium multilingual Whisper with different preprocessing combos
# Run from D:\DeskmateAI with venv activated

import os
import sys
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

SAMPLE_RATE = 16000
RECORD_SECONDS = 4

# ── Helpers ───────────────────────────────────────────────────

def record_audio(seconds=RECORD_SECONDS):
    print(f"\n🎤 Recording {seconds}s... speak now!")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype='float32')
    sd.wait()
    audio = audio.flatten()
    print(f"   RMS: {np.sqrt(np.mean(audio**2)):.6f} | Max: {np.max(np.abs(audio)):.4f}")
    return audio

def save_temp(audio):
    path = os.path.join(tempfile.gettempdir(), f"test_{int(time.time()*1000)}.wav")
    sf.write(path, audio, SAMPLE_RATE)
    return path

def transcribe(model, audio, label):
    path = save_temp(audio)
    start = time.time()
    segments, info = model.transcribe(
        path,
        language="en",
        beam_size=1,
        word_timestamps=False,
        condition_on_previous_text=False
    )
    text = " ".join([s.text for s in segments]).strip()
    elapsed = time.time() - start
    os.remove(path)
    print(f"   [{label}] → '{text}' ({elapsed:.2f}s)")
    return text

# ── Preprocessing variants ────────────────────────────────────

def preprocess_none(audio):
    """No preprocessing — raw audio"""
    return audio

def preprocess_normalize_only(audio):
    """Just amplitude normalization"""
    rms = np.sqrt(np.mean(audio**2))
    if rms > 0:
        audio = audio * (0.3 / rms)
    audio = np.clip(audio, -0.95, 0.95)
    return audio.astype(np.float32)

def preprocess_noise_only(audio):
    """Just noise reduction"""
    try:
        import noisereduce as nr
        return nr.reduce_noise(y=audio, sr=SAMPLE_RATE,
                               prop_decrease=0.3, stationary=True, n_jobs=1)
    except Exception as e:
        print(f"   ⚠ Noise reduction failed: {e}")
        return audio

def preprocess_full(audio):
    """Full pipeline: noise + normalize (current approach)"""
    audio = preprocess_noise_only(audio)
    audio = preprocess_normalize_only(audio)
    return audio

def preprocess_light(audio):
    """Light: normalize only, no silence trim, no heavy noise reduction"""
    # Remove DC offset
    audio = audio - np.mean(audio)
    # Normalize
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio * (0.9 / peak)
    return audio.astype(np.float32)

PREPROCESSORS = {
    "No preprocessing":    preprocess_none,
    "Normalize only":      preprocess_normalize_only,
    "Noise only":          preprocess_noise_only,
    "Full pipeline":       preprocess_full,
    "Light (DC+peak)":     preprocess_light,
}

# ── Load Models ───────────────────────────────────────────────

def load_model(size):
    from faster_whisper import WhisperModel
    print(f"\n⏳ Loading whisper-{size} multilingual...")
    start = time.time()
    model = WhisperModel(size, device="cpu", compute_type="int8")
    print(f"   ✅ Loaded in {time.time()-start:.1f}s")
    return model

# ── Main ──────────────────────────────────────────────────────

def run_test(model, model_name, audio):
    print(f"\n{'='*55}")
    print(f"  Model: {model_name}")
    print(f"{'='*55}")
    results = {}
    for label, fn in PREPROCESSORS.items():
        processed = fn(audio.copy())
        text = transcribe(model, processed, label)
        results[label] = text
    return results

def main():
    print("=" * 55)
    print("  Whisper Transcription Test")
    print("  small vs medium | 5 preprocessing variants")
    print("=" * 55)

    # Load both models upfront
    model_small  = load_model("small")
    model_medium = load_model("medium")

    trial = 1
    while True:
        print(f"\n\n{'#'*55}")
        print(f"  Trial {trial} — Say a voice command clearly")
        print(f"{'#'*55}")
        input("  Press Enter when ready...")

        audio = record_audio()

        run_test(model_small,  "whisper-small  (multilingual)", audio)
        run_test(model_medium, "whisper-medium (multilingual)", audio)

        print(f"\n{'─'*55}")
        again = input("  Run another trial? (y/n): ").strip().lower()
        if again != 'y':
            break
        trial += 1

    print("\n✅ Test complete.")

if __name__ == "__main__":
    main()
