# DeskmateAI/NLP/nlp/sbert_engine.py

import os
import sys
import time
import numpy as np

# ============================================================
# SBERT ENGINE FOR DESKMATEAI
# Fast intent classification using Sentence-BERT
# Uses all-MiniLM-L6-v2 model (80MB, very fast)
# Loads all intent examples as embeddings at startup
# Classifies commands via cosine similarity
# Sub 100ms latency for known commands
# Falls back to LLM when confidence too low
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import get_intents_dir, ensure_dir

# ── Constants ─────────────────────────────────────────────────

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SBERT_MODEL = "all-MiniLM-L6-v2"
SBERT_MODEL_PATH = os.path.join(BASE_DIR, "NLP", "models", "sbert")
CONFIDENCE_THRESHOLD = 0.50          # Min score for classification
UNKNOWN_INTENT = "unknown"

# ── SBERT Engine Class ────────────────────────────────────────

class SBERTEngine:

    def __init__(self):
        # print("[SBERT] Initializing SBERTEngine...")
        self._model = None
        self._intent_embeddings = {}   # intent → list of embeddings
        self._intent_examples = {}     # intent → list of example texts
        self._model_loaded = False
        self._embeddings_built = False
        log_info("SBERTEngine initialized")

    # ── Model Loading ─────────────────────────────────────────

    def _load_model(self):
        """Load SBERT model"""
        # print("[SBERT] Loading SBERT model...")
        log_info(f"Loading SBERT model: {SBERT_MODEL}")

        try:
            from sentence_transformers import SentenceTransformer

            # Check if model exists locally first
            if os.path.exists(SBERT_MODEL_PATH) and os.listdir(SBERT_MODEL_PATH):
                # print(f"[SBERT] Loading from local: {SBERT_MODEL_PATH}")
                self._model = SentenceTransformer(SBERT_MODEL_PATH)
            else:
                # Download and save locally
                # print(f"[SBERT] Downloading: {SBERT_MODEL}")
                os.makedirs(SBERT_MODEL_PATH, exist_ok=True)
                self._model = SentenceTransformer(SBERT_MODEL)
                self._model.save(SBERT_MODEL_PATH)
                # print(f"[SBERT] ✅ Model saved to: {SBERT_MODEL_PATH}")

            # Move to GPU if available
            import torch
            if torch.cuda.is_available():
                self._model = self._model.to("cuda")
                log_info("SBERT moved to GPU")

            self._model_loaded = True
            # print(f"[SBERT] ✅ SBERT model loaded: {SBERT_MODEL}")
            log_info(f"SBERT model loaded: {SBERT_MODEL}")
            return True

        except Exception as e:
            # print(f"[SBERT] Model load error: {e}")
            log_error(f"SBERT model load error: {e}")
            self._model = None
            self._model_loaded = False
            return False

    def _get_model(self):
        """Get model, load if needed"""
        if not self._model_loaded or self._model is None:
            self._load_model()
        return self._model

    # ── Build Embeddings ──────────────────────────────────────

    def build_embeddings(self, intent_examples):
        """
        Build embeddings for all intent examples
        Called at startup and when new intents added
        intent_examples: dict of intent → list of example texts
        """
        # print(f"[SBERT] Building embeddings for {len(intent_examples)} intents...")
        log_info(f"Building embeddings: {len(intent_examples)} intents")

        model = self._get_model()
        if model is None:
            log_error("SBERT model not available")
            return False

        try:
            start_time = time.time()
            self._intent_embeddings = {}
            self._intent_examples = intent_examples

            for intent, examples in intent_examples.items():
                if not examples:
                    continue

                # Encode all examples for this intent
                embeddings = model.encode(
                    examples,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    batch_size=32
                )

                self._intent_embeddings[intent] = embeddings
                # print(f"[SBERT] Built {len(examples)} embeddings for: {intent}")

            elapsed = time.time() - start_time
            self._embeddings_built = True

            # print(f"[SBERT] ✅ Embeddings built in {elapsed:.3f}s")
            log_info(f"Embeddings built in {elapsed:.3f}s for {len(self._intent_embeddings)} intents")
            return True

        except Exception as e:
            # print(f"[SBERT] Build embeddings error: {e}")
            log_error(f"Build embeddings error: {e}")
            return False

    def refresh_embeddings(self):
        """
        Refresh embeddings from current intent memory
        Called when new commands are learned
        """
        # print("[SBERT] Refreshing embeddings...")
        log_info("Refreshing SBERT embeddings")

        try:
            from backend.core.memory import get_memory_manager
            memory = get_memory_manager()
            all_intents = memory.get_all_intents()
            return self.build_embeddings(all_intents)

        except Exception as e:
            # print(f"[SBERT] Refresh error: {e}")
            log_error(f"Refresh embeddings error: {e}")
            return False

    # ── Classification ────────────────────────────────────────

    def classify(self, text, context=None):
        """
        Classify text into intent using cosine similarity
        Returns (intent, confidence_score)
        If confidence < threshold returns (unknown, score)
        """
        # print(f"[SBERT] Classifying: '{text}'")
        log_debug(f"SBERT classifying: '{text}'")

        if not text or not text.strip():
            log_warning("Empty text for classification")
            return UNKNOWN_INTENT, 0.0

        # Build embeddings if not done
        if not self._embeddings_built:
            # print("[SBERT] Embeddings not built, building now...")
            self.refresh_embeddings()

        if not self._intent_embeddings:
            # print("[SBERT] No embeddings available")
            log_warning("No embeddings available for classification")
            return UNKNOWN_INTENT, 0.0

        model = self._get_model()
        if model is None:
            return UNKNOWN_INTENT, 0.0

        try:
            start_time = time.time()

            # Encode input text
            text_embedding = model.encode(
                [text.lower().strip()],
                convert_to_numpy=True,
                show_progress_bar=False
            )

            # Compare against all intent embeddings
            best_intent = UNKNOWN_INTENT
            best_score = 0.0

            for intent, embeddings in self._intent_embeddings.items():
                # Calculate similarity with all examples
                scores = self._cosine_similarity_batch(
                    text_embedding[0],
                    embeddings
                )

                # Use max similarity score
                max_score = float(np.max(scores))

                if max_score > best_score:
                    best_score = max_score
                    best_intent = intent

            elapsed = time.time() - start_time
            # print(f"[SBERT] Best: '{best_intent}' ({best_score:.3f}) in {elapsed*1000:.1f}ms")
            log_debug(f"SBERT: '{best_intent}' ({best_score:.3f}) in {elapsed*1000:.1f}ms")

            # Apply confidence threshold
            if best_score >= CONFIDENCE_THRESHOLD:
                # print(f"[SBERT] ✅ Confident: '{best_intent}' ({best_score:.3f})")
                log_info(f"SBERT classified: '{best_intent}' ({best_score:.3f})")
                return best_intent, best_score
            else:
                # print(f"[SBERT] Low confidence: {best_score:.3f} < {CONFIDENCE_THRESHOLD}")
                log_debug(f"SBERT low confidence: {best_score:.3f}")
                return UNKNOWN_INTENT, best_score

        except Exception as e:
            # print(f"[SBERT] Classification error: {e}")
            log_error(f"SBERT classification error: {e}")
            return UNKNOWN_INTENT, 0.0

    def classify_with_context(self, text, context):
        """
        Classification with context awareness
        Uses active app and last intent to improve accuracy
        """
        # print(f"[SBERT] Context-aware classification: '{text}'")
        log_debug(f"Context-aware SBERT: '{text}'")

        # Base classification
        intent, score = self.classify(text, context)

        if intent != UNKNOWN_INTENT:
            return intent, score

        # Context boost — if we know active app, try app-specific intents
        if context:
            active_app = context.get('active_app')
            last_intent = context.get('last_intent')

            # If dictation mode and confidence low, treat as dictation
            if context.get('dictation_mode'):
                # print("[SBERT] In dictation mode, skipping intent classification")
                return 'write_text', 0.9

            # If last intent was write_text, check for stop commands
            if last_intent == 'write_text':
                stop_words = ['stop', 'done', 'finish', 'end dictation', 'cancel']
                if any(word in text.lower() for word in stop_words):
                    return 'stop_dictation', 0.9

        return intent, score

    # ── Get Top N Intents ─────────────────────────────────────

    def get_top_n(self, text, n=3):
        """
        Get top N intent classifications with scores
        Useful for debugging and settings UI
        """
        # print(f"[SBERT] Getting top {n} intents for: '{text}'")
        log_debug(f"Getting top {n} for: '{text}'")

        if not text or not self._intent_embeddings:
            return []

        model = self._get_model()
        if model is None:
            return []

        try:
            text_embedding = model.encode(
                [text.lower().strip()],
                convert_to_numpy=True,
                show_progress_bar=False
            )

            scores = []
            for intent, embeddings in self._intent_embeddings.items():
                max_score = float(np.max(
                    self._cosine_similarity_batch(text_embedding[0], embeddings)
                ))
                scores.append((intent, max_score))

            # Sort by score descending
            scores.sort(key=lambda x: x[1], reverse=True)
            top_n = scores[:n]

            # print(f"[SBERT] Top {n}: {top_n}")
            return top_n

        except Exception as e:
            # print(f"[SBERT] Top N error: {e}")
            log_error(f"Top N error: {e}")
            return []

    # ── Add New Intent ────────────────────────────────────────

    def add_intent_embedding(self, intent, new_examples):
        """
        Add embeddings for new intent examples
        Called when user adds custom intent or system learns
        """
        # print(f"[SBERT] Adding embeddings for: {intent}")
        log_info(f"Adding embeddings: {intent}")

        model = self._get_model()
        if model is None:
            return False

        try:
            new_embeddings = model.encode(
                new_examples,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            if intent in self._intent_embeddings:
                # Append to existing
                self._intent_embeddings[intent] = np.vstack([
                    self._intent_embeddings[intent],
                    new_embeddings
                ])
            else:
                self._intent_embeddings[intent] = new_embeddings

            if intent in self._intent_examples:
                self._intent_examples[intent].extend(new_examples)
            else:
                self._intent_examples[intent] = list(new_examples)

            # print(f"[SBERT] ✅ Embeddings added for: {intent}")
            log_info(f"Embeddings added: {intent}")
            return True

        except Exception as e:
            # print(f"[SBERT] Add embedding error: {e}")
            log_error(f"Add embedding error: {e}")
            return False

    def remove_intent_embedding(self, intent):
        """Remove embeddings for intent"""
        # print(f"[SBERT] Removing embeddings: {intent}")
        if intent in self._intent_embeddings:
            del self._intent_embeddings[intent]
        if intent in self._intent_examples:
            del self._intent_examples[intent]
        log_info(f"Embeddings removed: {intent}")

    # ── Similarity ────────────────────────────────────────────

    def _cosine_similarity_batch(self, query_embedding, corpus_embeddings):
        """
        Calculate cosine similarity between query and corpus
        Vectorized for speed
        """
        try:
            # Normalize query
            query_norm = np.linalg.norm(query_embedding)
            if query_norm == 0:
                return np.zeros(len(corpus_embeddings))

            query_normalized = query_embedding / query_norm

            # Normalize corpus
            corpus_norms = np.linalg.norm(corpus_embeddings, axis=1, keepdims=True)
            corpus_norms = np.where(corpus_norms == 0, 1, corpus_norms)
            corpus_normalized = corpus_embeddings / corpus_norms

            # Calculate similarities
            similarities = np.dot(corpus_normalized, query_normalized)
            return similarities

        except Exception as e:
            # print(f"[SBERT] Similarity calc error: {e}")
            log_error(f"Similarity calc error: {e}")
            return np.zeros(len(corpus_embeddings))

    def get_similarity(self, text1, text2):
        """Get similarity between two texts"""
        # print(f"[SBERT] Similarity: '{text1}' vs '{text2}'")
        model = self._get_model()
        if model is None:
            return 0.0
        try:
            embeddings = model.encode(
                [text1, text2],
                convert_to_numpy=True,
                show_progress_bar=False
            )
            sim = self._cosine_similarity_batch(embeddings[0], embeddings[1:])
            return float(sim[0])
        except Exception as e:
            # print(f"[SBERT] Similarity error: {e}")
            log_error(f"Similarity error: {e}")
            return 0.0

    # ── Status ────────────────────────────────────────────────

    def get_status(self):
        """Get SBERT engine status"""
        return {
            "model_loaded": self._model_loaded,
            "embeddings_built": self._embeddings_built,
            "total_intents": len(self._intent_embeddings),
            "total_examples": sum(
                len(e) for e in self._intent_embeddings.values()
            ),
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "model": SBERT_MODEL
        }


# ── Singleton Instance ────────────────────────────────────────

_sbert_engine = None

def get_sbert_engine():
    global _sbert_engine
    if _sbert_engine is None:
        # print("[SBERT] Creating singleton SBERTEngine...")
        _sbert_engine = SBERTEngine()
    return _sbert_engine