# DeskmateAI/NLP/nlp/intent_pipeline.py

import os
import sys
import time

# ============================================================
# INTENT PIPELINE FOR DESKMATEAI
# Coordinates the full intent classification system:
# Level 1: SBERT fast classification (<0.1s)
# Level 2: Ollama LLM fallback (~1-2s, offline)
# Level 3: Self-learning (saves to intent_memory.json)
# Handles context-aware classification
# Returns (intent, score, source) for every command
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning, log_intent

# ── Constants ─────────────────────────────────────────────────

SBERT_THRESHOLD = 0.50       # Min SBERT score for classification
UNKNOWN_INTENT = "unknown"
SOURCE_SBERT = "sbert"
SOURCE_LLM = "llm"
SOURCE_UNKNOWN = "unknown"

# ── Intent Pipeline Class ─────────────────────────────────────

class IntentPipeline:

    def __init__(self):
        # print("[INTENT] Initializing IntentPipeline...")
        self._sbert = None
        self._llm = None
        self._learner = None
        self._memory = None
        self._initialized = False
        log_info("IntentPipeline initialized")

    def _load_components(self):
        """Lazy load all components"""
        # print("[INTENT] Loading components...")
        try:
            from NLP.nlp.sbert_engine import get_sbert_engine
            from NLP.nlp.llm_fallback import get_llm_fallback
            from backend.core.learner import get_learner
            from backend.core.memory import get_memory_manager

            self._sbert = get_sbert_engine()
            self._llm = get_llm_fallback()
            self._learner = get_learner()
            self._memory = get_memory_manager()

            # Build initial embeddings
            # print("[INTENT] Building initial embeddings...")
            all_intents = self._memory.get_all_intents()
            self._sbert.build_embeddings(all_intents)

            self._initialized = True
            # print(f"[INTENT] ✅ Pipeline ready with {len(all_intents)} intents")
            log_info(f"Intent pipeline ready: {len(all_intents)} intents")

        except Exception as e:
            # print(f"[INTENT] Component load error: {e}")
            log_error(f"Intent pipeline load error: {e}")

    def _ensure_initialized(self):
        """Ensure pipeline is initialized"""
        if not self._initialized:
            self._load_components()

    # ── Main Classification ───────────────────────────────────

    def classify(self, text, context=None):
        """
        Main intent classification
        Level 1: SBERT fast (<0.1s)
        Level 2: LLM fallback (~1-2s)
        Level 3: Learn and cache result
        Returns (intent, score, source)
        """
        # print(f"[INTENT] Classifying: '{text}'")
        log_info(f"Classifying: '{text}'")

        if not text or not text.strip():
            log_warning("Empty text for classification")
            return UNKNOWN_INTENT, 0.0, SOURCE_UNKNOWN

        self._ensure_initialized()

        start_time = time.time()

        # ── Level 1: SBERT ────────────────────────────────────
        # print("[INTENT] Level 1: SBERT classification...")

        if self._sbert:
            intent, score = self._sbert.classify_with_context(
                text.lower().strip(),
                context
            )

            if intent != UNKNOWN_INTENT and score >= SBERT_THRESHOLD:
                elapsed = time.time() - start_time
                # print(f"[INTENT] ✅ SBERT: '{intent}' ({score:.3f}) in {elapsed*1000:.1f}ms")
                log_intent(text, intent, score, SOURCE_SBERT)
                return intent, score, SOURCE_SBERT

            # print(f"[INTENT] SBERT confidence low: {score:.3f} — trying LLM")
            log_debug(f"SBERT low confidence: {score:.3f}")

        # ── Level 2: LLM Fallback ─────────────────────────────
        # print("[INTENT] Level 2: LLM fallback...")

        if self._llm:
            # Get available intents for LLM
            available_intents = self._get_intent_list()

            intent, llm_score = self._llm.classify(
                text,
                available_intents
            )

            if intent != UNKNOWN_INTENT:
                elapsed = time.time() - start_time
                # print(f"[INTENT] ✅ LLM: '{intent}' ({llm_score:.3f}) in {elapsed:.3f}s")
                log_intent(text, intent, llm_score, SOURCE_LLM)

                # ── Level 3: Learn ────────────────────────────
                # Save to intent memory for future SBERT use
                # print(f"[INTENT] Level 3: Learning '{text}' → '{intent}'")
                self._learn_and_refresh(text, intent)

                return intent, llm_score, SOURCE_LLM

            # print(f"[INTENT] LLM also unknown: '{text}'")
            log_warning(f"Both SBERT and LLM failed: '{text}'")

        # ── Unknown ───────────────────────────────────────────
        elapsed = time.time() - start_time
        # print(f"[INTENT] ❌ Unknown intent: '{text}' ({elapsed:.3f}s)")
        log_warning(f"Unknown intent: '{text}'")
        return UNKNOWN_INTENT, 0.0, SOURCE_UNKNOWN

    def _learn_and_refresh(self, command, intent):
        """
        Save new command to memory
        Refresh SBERT embeddings with new command
        So next time SBERT handles it at <0.1s
        """
        # print(f"[INTENT] Learning: '{command}' → '{intent}'")
        try:
            if self._learner:
                learned = self._learner.learn(command, intent)
                if learned:
                    # Add embedding to SBERT immediately
                    if self._sbert:
                        self._sbert.add_intent_embedding(
                            intent,
                            [command]
                        )
                    # print(f"[INTENT] ✅ Learned and SBERT updated: '{command}'")
                    log_info(f"Learned: '{command}' → '{intent}'")
        except Exception as e:
            # print(f"[INTENT] Learn error: {e}")
            log_error(f"Learn error: {e}")

    def _get_intent_list(self):
        """Get list of all available intents"""
        # print("[INTENT] Getting intent list...")
        try:
            from backend.core.registry import get_registry
            registry = get_registry()
            return registry.get_all_intents()
        except Exception as e:
            # print(f"[INTENT] Get intent list error: {e}")
            log_error(f"Get intent list error: {e}")
            if self._memory:
                return list(self._memory.get_all_intents().keys())
            return []

    # ── Custom Intent Management ──────────────────────────────

    def add_custom_intent(self, intent_name, examples, action_handler=None):
        """
        Add custom intent from settings UI
        Adds to memory and rebuilds SBERT embeddings
        """
        # print(f"[INTENT] Adding custom intent: {intent_name}")
        log_info(f"Adding custom intent: {intent_name}")

        self._ensure_initialized()

        try:
            # Add to learner
            if self._learner:
                success = self._learner.add_custom_intent(
                    intent_name,
                    examples
                )
                if not success:
                    return False, "Failed to add intent"

            # Add embeddings to SBERT
            if self._sbert:
                self._sbert.add_intent_embedding(intent_name, examples)

            # Register in command registry if handler provided
            if action_handler:
                from backend.core.registry import get_registry
                registry = get_registry()
                registry.register_custom(
                    intent=intent_name,
                    handler_module=action_handler.get('module', 'automation.app_launcher'),
                    handler_function=action_handler.get('function', 'open_app'),
                    needs_entity=action_handler.get('needs_entity', False),
                    description=action_handler.get('description', intent_name)
                )

            # print(f"[INTENT] ✅ Custom intent added: {intent_name}")
            log_info(f"Custom intent added: {intent_name}")
            return True, f"Intent '{intent_name}' added successfully"

        except Exception as e:
            # print(f"[INTENT] Add custom intent error: {e}")
            log_error(f"Add custom intent error: {e}")
            return False, str(e)

    def add_example_to_intent(self, intent, example):
        """
        Add example to existing intent from settings UI
        Updates SBERT embeddings immediately
        """
        # print(f"[INTENT] Adding example to '{intent}': '{example}'")
        log_info(f"Adding example: '{example}' → '{intent}'")

        self._ensure_initialized()

        try:
            # Add to learner/memory
            if self._learner:
                self._learner.add_example_to_intent(intent, example)

            # Update SBERT embeddings
            if self._sbert:
                self._sbert.add_intent_embedding(intent, [example])

            # print(f"[INTENT] ✅ Example added: '{example}' → '{intent}'")
            log_info(f"Example added: '{example}' → '{intent}'")
            return True

        except Exception as e:
            # print(f"[INTENT] Add example error: {e}")
            log_error(f"Add example error: {e}")
            return False

    def remove_intent(self, intent_name):
        """Remove intent from system"""
        # print(f"[INTENT] Removing intent: {intent_name}")
        log_info(f"Removing intent: {intent_name}")

        self._ensure_initialized()

        try:
            # Remove from learner
            if self._learner:
                self._learner.remove_intent(intent_name)

            # Remove from SBERT
            if self._sbert:
                self._sbert.remove_intent_embedding(intent_name)

            # print(f"[INTENT] ✅ Intent removed: {intent_name}")
            log_info(f"Intent removed: {intent_name}")
            return True

        except Exception as e:
            # print(f"[INTENT] Remove intent error: {e}")
            log_error(f"Remove intent error: {e}")
            return False

    # ── Refresh ───────────────────────────────────────────────

    def refresh(self):
        """
        Refresh pipeline with latest intents
        Called after learning new commands
        """
        # print("[INTENT] Refreshing pipeline...")
        log_info("Refreshing intent pipeline")

        self._ensure_initialized()

        try:
            if self._sbert and self._memory:
                all_intents = self._memory.get_all_intents()
                self._sbert.build_embeddings(all_intents)
                # print(f"[INTENT] ✅ Pipeline refreshed: {len(all_intents)} intents")
                log_info(f"Pipeline refreshed: {len(all_intents)} intents")
                return True
        except Exception as e:
            # print(f"[INTENT] Refresh error: {e}")
            log_error(f"Pipeline refresh error: {e}")
        return False

    # ── Testing ───────────────────────────────────────────────

    def test_classification(self, text):
        """
        Test classification and return detailed results
        Used in settings UI for testing intents
        """
        # print(f"[INTENT] Testing: '{text}'")
        self._ensure_initialized()

        results = {
            "text": text,
            "sbert_result": None,
            "sbert_score": 0.0,
            "top_3_sbert": [],
            "llm_result": None,
            "final_intent": UNKNOWN_INTENT,
            "source": SOURCE_UNKNOWN
        }

        try:
            # SBERT result
            if self._sbert:
                intent, score = self._sbert.classify(text)
                results["sbert_result"] = intent
                results["sbert_score"] = score
                results["top_3_sbert"] = self._sbert.get_top_n(text, 3)

            # Full pipeline result
            final_intent, final_score, source = self.classify(text)
            results["final_intent"] = final_intent
            results["final_score"] = final_score
            results["source"] = source

            # print(f"[INTENT] Test results: {results}")
            return results

        except Exception as e:
            # print(f"[INTENT] Test error: {e}")
            log_error(f"Test classification error: {e}")
            return results

    # ── Status ────────────────────────────────────────────────

    def get_status(self):
        """Get pipeline status"""
        # print("[INTENT] Getting status...")
        self._ensure_initialized()

        status = {
            "initialized": self._initialized,
            "sbert_status": self._sbert.get_status() if self._sbert else None,
            "llm_status": self._llm.get_status() if self._llm else None,
        }

        if self._memory:
            stats = self._memory.get_memory_stats()
            status["memory_stats"] = stats

        # print(f"[INTENT] Status: {status}")
        return status

    def get_all_intents_with_examples(self):
        """Get all intents with examples for settings UI"""
        # print("[INTENT] Getting all intents...")
        self._ensure_initialized()
        if self._memory:
            return self._memory.get_all_intents()
        return {}

    def get_learning_stats(self):
        """Get learning statistics"""
        # print("[INTENT] Getting learning stats...")
        self._ensure_initialized()
        if self._learner:
            return self._learner.get_learning_stats()
        return {}


# ── Singleton Instance ────────────────────────────────────────

_intent_pipeline = None

def get_intent_pipeline():
    global _intent_pipeline
    if _intent_pipeline is None:
        # print("[INTENT] Creating singleton IntentPipeline...")
        _intent_pipeline = IntentPipeline()
    return _intent_pipeline
'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `_load_components()` | Load SBERT + LLM + Learner |
| `classify()` | Full 3-level classification |
| `_learn_and_refresh()` | Save + update SBERT instantly |
| `_get_intent_list()` | All intents from registry |
| `add_custom_intent()` | Add from settings UI |
| `add_example_to_intent()` | Add example from UI |
| `remove_intent()` | Remove intent |
| `refresh()` | Rebuild all embeddings |
| `test_classification()` | Debug tool for settings |
| `get_status()` | Pipeline status |
| `get_intent_pipeline()` | Singleton — creates once |

---

## Complete 3-level flow:
```
Command: "can you write something for me"
        ↓
Level 1: SBERT → score=0.45 (below 0.50) ❌
        ↓
Level 2: LLM → "write_text" ✅ (~1-2s)
        ↓
Level 3: Learn → saved to intent_memory.json
         SBERT updated with new embedding
        ↓
Next time: "write me something"
Level 1: SBERT → score=0.72 ✅ (<0.1s)
'''