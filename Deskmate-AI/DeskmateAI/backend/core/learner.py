# DeskmateAI/backend/core/learner.py

import os
import sys

# ============================================================
# LEARNER FOR DESKMATEAI
# Handles self-learning of new commands
# When Ollama classifies a new command, learner saves it
# So next time SBERT handles it instantly at <0.1 sec
# Everything persists across sessions via JSON
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.memory import get_memory_manager
from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import get_timestamp

# ── Learner Class ─────────────────────────────────────────────

class Learner:

    def __init__(self):
        # print("[LEARNER] Initializing Learner...")
        self.memory = get_memory_manager()
        self._session_learned = []  # track what was learned this session
        log_info("Learner initialized")

    def learn(self, command, intent):
        """
        Save a new command → intent mapping
        Called after Ollama successfully classifies unknown command
        Next time same/similar command comes → SBERT handles it
        """
        # print(f"[LEARNER] Learning: '{command}' → '{intent}'")

        if not command or not intent:
            # print("[LEARNER] Empty command or intent, skipping...")
            log_warning("Learner received empty command or intent")
            return False

        if intent == "unknown":
            # print("[LEARNER] Intent is unknown, not learning...")
            log_warning(f"Not learning unknown intent for command: {command}")
            return False

        try:
            # Save to intent memory (persists to JSON)
            result = self.memory.learn_new_command(command, intent)

            if result:
                # print(f"[LEARNER] ✅ Successfully learned: '{command}' → '{intent}'")
                log_info(f"Learned new command: '{command}' → '{intent}'")

                # Track session learning
                self._session_learned.append({
                    "command": command,
                    "intent": intent,
                    "timestamp": get_timestamp()
                })
                return True
            else:
                # print(f"[LEARNER] Command already known: '{command}' → '{intent}'")
                log_debug(f"Command already exists: '{command}' → '{intent}'")
                return False

        except Exception as e:
            # print(f"[LEARNER] Error learning command: {e}")
            log_error(f"Error in learner: {e}")
            return False

    def learn_from_feedback(self, command, correct_intent):
        """
        Learn from user correction
        If system got intent wrong and user corrects it
        Save the correct mapping
        """
        # print(f"[LEARNER] Learning from feedback: '{command}' → '{correct_intent}'")
        log_info(f"Learning from user feedback: '{command}' → '{correct_intent}'")
        return self.learn(command, correct_intent)

    def unlearn(self, command, intent):
        """
        Remove a wrongly learned command
        If system learned something incorrectly
        """
        # print(f"[LEARNER] Unlearning: '{command}' from '{intent}'")
        try:
            memory = self.memory.load_intent_memory()
            if intent in memory and command in memory[intent]:
                memory[intent].remove(command)
                if not memory[intent]:
                    del memory[intent]
                self.memory.save_intent_memory(memory)
                log_info(f"Unlearned: '{command}' from '{intent}'")
                # print(f"[LEARNER] Successfully unlearned: '{command}'")
                return True
            # print(f"[LEARNER] Command not found in memory: '{command}'")
            return False
        except Exception as e:
            # print(f"[LEARNER] Error unlearning: {e}")
            log_error(f"Error unlearning command: {e}")
            return False

    def add_custom_intent(self, intent_name, examples):
        """
        Add completely new custom intent from UI settings
        User can add their own intents
        """
        # print(f"[LEARNER] Adding custom intent: '{intent_name}' with {len(examples)} examples")
        try:
            if not intent_name or not examples:
                log_warning("Empty intent name or examples")
                return False

            # Clean examples
            clean_examples = [e.strip().lower() for e in examples if e.strip()]
            if not clean_examples:
                log_warning("No valid examples provided")
                return False

            result = self.memory.add_new_intent(intent_name, clean_examples)
            if result:
                log_info(f"Added custom intent: '{intent_name}' with {len(clean_examples)} examples")
                # print(f"[LEARNER] ✅ Custom intent added: '{intent_name}'")
            return result

        except Exception as e:
            # print(f"[LEARNER] Error adding custom intent: {e}")
            log_error(f"Error adding custom intent: {e}")
            return False

    def add_example_to_intent(self, intent, example):
        """
        Add single example to existing intent from UI
        """
        # print(f"[LEARNER] Adding example to '{intent}': '{example}'")
        try:
            result = self.memory.add_intent_example(intent, example.strip().lower())
            if result:
                log_info(f"Added example to '{intent}': '{example}'")
                # print(f"[LEARNER] ✅ Example added to '{intent}'")
            return result
        except Exception as e:
            # print(f"[LEARNER] Error adding example: {e}")
            log_error(f"Error adding example to intent: {e}")
            return False

    def remove_intent(self, intent_name):
        """
        Remove an intent completely
        """
        # print(f"[LEARNER] Removing intent: '{intent_name}'")
        try:
            result = self.memory.remove_intent(intent_name)
            if result:
                log_info(f"Removed intent: '{intent_name}'")
                # print(f"[LEARNER] ✅ Intent removed: '{intent_name}'")
            return result
        except Exception as e:
            # print(f"[LEARNER] Error removing intent: {e}")
            log_error(f"Error removing intent: {e}")
            return False

    def get_session_learned(self):
        """
        Get list of commands learned this session
        """
        # print(f"[LEARNER] Session learned count: {len(self._session_learned)}")
        return self._session_learned

    def get_learning_stats(self):
        """
        Get statistics about learned commands
        """
        # print("[LEARNER] Getting learning stats...")
        try:
            stats = self.memory.get_memory_stats()
            stats["session_learned"] = len(self._session_learned)
            # print(f"[LEARNER] Stats: {stats}")
            return stats
        except Exception as e:
            # print(f"[LEARNER] Error getting stats: {e}")
            log_error(f"Error getting learning stats: {e}")
            return {}

    def get_all_intents_with_examples(self):
        """
        Get all intents with their examples
        Used by settings window to display intents
        """
        # print("[LEARNER] Getting all intents with examples...")
        try:
            all_intents = self.memory.get_all_intents()
            # print(f"[LEARNER] Total intents: {len(all_intents)}")
            return all_intents
        except Exception as e:
            # print(f"[LEARNER] Error getting intents: {e}")
            log_error(f"Error getting all intents: {e}")
            return {}

    def bulk_learn(self, command_intent_pairs):
        """
        Learn multiple commands at once
        Used for batch learning
        """
        # print(f"[LEARNER] Bulk learning {len(command_intent_pairs)} pairs...")
        learned_count = 0
        for command, intent in command_intent_pairs:
            if self.learn(command, intent):
                learned_count += 1
        # print(f"[LEARNER] Bulk learned: {learned_count}/{len(command_intent_pairs)}")
        log_info(f"Bulk learned: {learned_count}/{len(command_intent_pairs)} commands")
        return learned_count


# ── Singleton Instance ────────────────────────────────────────

_learner = None

def get_learner():
    global _learner
    if _learner is None:
        # print("[LEARNER] Creating singleton Learner...")
        _learner = Learner()
    return _learner



'''
## What this file does:

| Function | Purpose |
|---|---|
| `learn()` | Saves new command after Ollama classifies it |
| `learn_from_feedback()` | Saves user correction |
| `unlearn()` | Removes wrongly learned command |
| `add_custom_intent()` | Adds new intent from UI settings |
| `add_example_to_intent()` | Adds example to existing intent from UI |
| `remove_intent()` | Removes intent completely |
| `get_session_learned()` | Shows what was learned this session |
| `get_learning_stats()` | Returns learning statistics |
| `bulk_learn()` | Learn multiple commands at once |
| `get_learner()` | Singleton — creates once |

---

## How it connects:
```
Ollama classifies unknown command
        ↓
intent_pipeline.py calls learner.learn()
        ↓
learner saves to intent_memory.json
        ↓
Next time SBERT finds it instantly ✅

'''