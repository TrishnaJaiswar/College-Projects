# DeskmateAI/NLP/speech/asr/asr_loader.py

import os
import sys
import threading
import pkg_resources
# ============================================================
# ASR MODEL LOADER FOR DESKMATEAI
# Loads YOUR fine-tuned multilingual Whisper small model
# Model loaded from local path ONLY
# NO auto-downloading
# Uses int8 quantization for low spec PC optimization
# Single model instance shared across entire system
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import get_whisper_model_dir

# ── Constants ─────────────────────────────────────────────────

COMPUTE_TYPE = "float16" # float16 for GPU (faster than int8 on CUDA)
DEVICE = "cuda"          # GPU acceleration
NUM_WORKERS = 1          # Single worker
CPU_THREADS = 4          # CPU threads (fallback)
BEAM_SIZE = 1            # Greedy decoding for speed

# ── Global lock — prevents two threads loading model at once ──
_model_load_lock = threading.Lock()

# ── ASR Loader Class ──────────────────────────────────────────

class ASRLoader:

    def __init__(self):
        # print("[ASR_LOADER] Initializing ASRLoader...")
        self._model = None
        self._model_loaded = False
        self._model_dir = get_whisper_model_dir()
        log_info(f"ASRLoader initialized | Model dir: {self._model_dir}")
        # print(f"[ASR_LOADER] Model dir: {self._model_dir}")

    def load_model(self):
        """
        Load YOUR fine-tuned Whisper model from local path
        NO downloading — loads from NLP/models/whisper/ only
        Thread-safe: uses global lock so only one thread loads at a time
        """
        # If already loaded, return immediately without acquiring lock
        if self._model_loaded and self._model is not None:
            return self._model

        with _model_load_lock:
            # Double-check inside lock in case another thread loaded it
            if self._model_loaded and self._model is not None:
                return self._model

            # print("[ASR_LOADER] Loading fine-tuned Whisper model...")
            log_info(f"Loading fine-tuned Whisper from: {self._model_dir}")

            # ── Verify model exists ───────────────────────────
            if not os.path.exists(self._model_dir):
                log_error(f"Model directory not found: {self._model_dir}")
                print(f"❌ Whisper model not found at: {self._model_dir}")
                print(f"   Please copy your fine-tuned model to:")
                print(f"   {self._model_dir}")
                return None

            # Check for required model files
            model_files = os.listdir(self._model_dir) if os.path.exists(self._model_dir) else []

            if not model_files:
                log_error("Model directory is empty")
                print(f"❌ Model directory is empty: {self._model_dir}")
                print(f"   Please copy your fine-tuned model files there")
                return None

            # print(f"[ASR_LOADER] Found model files: {model_files}")
            log_info(f"Model files found: {model_files}")

            try:
                from faster_whisper import WhisperModel
                import torch

                # Auto-detect GPU availability
                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute = "float16" if device == "cuda" else "int8"

                if device == "cuda":
                    log_info(f"GPU detected: {torch.cuda.get_device_name(0)} — using float16")
                else:
                    log_warning("GPU not available — falling back to CPU int8")

                # Load medium multilingual model from HuggingFace
                # Falls back to local path if available
                model_source = self._model_dir if os.path.exists(self._model_dir) else "medium"
                log_info(f"Loading model from: {model_source} | device={device} | compute={compute}")

                self._model = WhisperModel(
                    model_source,
                    device=device,
                    compute_type=compute,
                    num_workers=NUM_WORKERS,
                    cpu_threads=CPU_THREADS
                )

                self._model_loaded = True
                # print(f"[ASR_LOADER] ✅ Fine-tuned Whisper loaded successfully")
                log_info("Fine-tuned Whisper model loaded successfully")
                return self._model

            except Exception as e:
                # print(f"[ASR_LOADER] ❌ Model load error: {e}")
                log_error(f"Whisper model load error: {e}")
                self._model = None
                self._model_loaded = False
                return None

    def get_model(self):
        """
        Get model instance
        Loads from local path if not already loaded
        """
        if not self._model_loaded or self._model is None:
            # print("[ASR_LOADER] Model not loaded, loading now...")
            self.load_model()
        return self._model

    def is_loaded(self):
        return self._model_loaded and self._model is not None

    def get_model_info(self):
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        return {
            "model_path": self._model_dir,
            "compute_type": compute,
            "device": device,
            "is_loaded": self.is_loaded(),
            "model_files": (
                os.listdir(self._model_dir)
                if os.path.exists(self._model_dir)
                else []
            )
        }

    def reload_model(self):
        """Force reload model"""
        # print("[ASR_LOADER] Reloading model...")
        log_info("Reloading Whisper model")
        self._model = None
        self._model_loaded = False
        return self.load_model()


# ── Singleton Instance ────────────────────────────────────────

_asr_loader = None

def get_asr_loader():
    global _asr_loader
    if _asr_loader is None:
        # print("[ASR_LOADER] Creating singleton ASRLoader...")
        _asr_loader = ASRLoader()
    return _asr_loader


def get_asr_model():
    """
    Convenience function to get Whisper model
    Used by speech_handler, wake_word_detector, speech_auth
    """
    return get_asr_loader().get_model()