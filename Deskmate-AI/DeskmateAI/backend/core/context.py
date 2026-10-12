# DeskmateAI/backend/core/context.py

import os
import sys

# ============================================================
# CONTEXT MANAGER FOR DESKMATEAI
# Tracks system state at all times
# - Which app is active
# - Last intent executed
# - Current user
# - Current language
# - Wake word
# - Dictation mode state
# Context is passed through entire pipeline
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_debug, log_error
from backend.utils.utils import get_timestamp

# ── Context Manager Class ─────────────────────────────────────

class ContextManager:

    def __init__(self):
        # print("[CONTEXT] Initializing ContextManager...")

        # Current active app
        self.active_app = None
        self.active_window_title = None

        # Intent tracking
        self.last_intent = None
        self.last_command = None
        self.last_entity = None
        self.last_action_time = None

        # User session
        self.current_user = None
        self.current_language = 'en'
        self.current_language_name = 'English'
        self.wake_word = 'hey deskmate'
        self.wake_word_sensitivity = 0.6

        # Dictation mode
        self.dictation_mode = False
        self.dictation_target_app = None

        # System state
        self.is_listening = False
        self.is_processing = False
        self.is_authenticated = False
        self.system_muted = False

        # Command history (last 10 commands)
        self.command_history = []
        self.MAX_HISTORY = 10

        # Screen info
        self.active_screen = 0
        self.active_window_region = None

        log_info("ContextManager initialized")
        # print("[CONTEXT] ContextManager initialized")

    # ── Session Setup ─────────────────────────────────────────

    def set_user(self, username, profile):
        """Load user context from profile"""
        # print(f"[CONTEXT] Setting user: {username}")
        self.current_user = username
        self.current_language = profile.get('language', 'en')
        self.current_language_name = profile.get('language_name', 'English')
        self.wake_word = profile.get('wake_word', 'hey deskmate')
        self.wake_word_sensitivity = profile.get('wake_word_sensitivity', 0.6)
        self.is_authenticated = True
        log_info(f"Context set for user: {username} | Language: {self.current_language}")
        # print(f"[CONTEXT] User context loaded: {username} | {self.current_language}")

    def clear_user(self):
        """Clear user session"""
        # print("[CONTEXT] Clearing user context...")
        self.current_user = None
        self.is_authenticated = False
        self.dictation_mode = False
        self.command_history = []
        log_info("User context cleared")

    # ── App Tracking ──────────────────────────────────────────

    def set_active_app(self, app_name, window_title=None):
        """Update active app"""
        # print(f"[CONTEXT] Active app: {app_name}")
        self.active_app = app_name
        self.active_window_title = window_title
        log_debug(f"Active app updated: {app_name}")

    def get_active_app(self):
        # print(f"[CONTEXT] Getting active app: {self.active_app}")
        return self.active_app

    def update_active_window(self):
        """Get currently focused window from Windows"""
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            self.active_window_title = title
            self.active_window_region = rect
            # print(f"[CONTEXT] Active window: {title} | Region: {rect}")
            log_debug(f"Active window: {title}")
            return title, rect
        except Exception as e:
            # print(f"[CONTEXT] Error getting active window: {e}")
            log_error(f"Error getting active window: {e}")
            return None, None

    # ── Intent Tracking ───────────────────────────────────────

    def update(self, intent, command, entity=None):
        """Update context after command execution"""
        # print(f"[CONTEXT] Updating context: intent={intent} | command={command} | entity={entity}")

        self.last_intent = intent
        self.last_command = command
        self.last_entity = entity
        self.last_action_time = get_timestamp()

        # Update active app if intent is open_app
        if intent == 'open_app' and entity:
            self.set_active_app(entity)

        # Track close_app
        if intent == 'close_app':
            if entity and entity == self.active_app:
                self.active_app = None

        # Add to history
        self._add_to_history(intent, command, entity)

        log_debug(f"Context updated: {intent} | {command}")

    def _add_to_history(self, intent, command, entity):
        """Add command to history"""
        entry = {
            "intent": intent,
            "command": command,
            "entity": entity,
            "timestamp": get_timestamp()
        }
        self.command_history.append(entry)

        # Keep only last MAX_HISTORY commands
        if len(self.command_history) > self.MAX_HISTORY:
            self.command_history.pop(0)
        # print(f"[CONTEXT] History updated, total: {len(self.command_history)}")

    def get_context(self):
        """Get full context dict for pipeline"""
        # print("[CONTEXT] Getting full context...")
        context = {
            "active_app": self.active_app,
            "active_window_title": self.active_window_title,
            "active_window_region": self.active_window_region,
            "last_intent": self.last_intent,
            "last_command": self.last_command,
            "last_entity": self.last_entity,
            "last_action_time": self.last_action_time,
            "current_user": self.current_user,
            "current_language": self.current_language,
            "current_language_name": self.current_language_name,
            "wake_word": self.wake_word,
            "wake_word_sensitivity": self.wake_word_sensitivity,
            "dictation_mode": self.dictation_mode,
            "dictation_target_app": self.dictation_target_app,
            "is_listening": self.is_listening,
            "is_processing": self.is_processing,
            "is_authenticated": self.is_authenticated,
            "system_muted": self.system_muted,
            "command_history": self.command_history,
        }
        return context

    # ── Dictation Mode ────────────────────────────────────────

    def enter_dictation_mode(self):
        """Enter dictation mode"""
        # print("[CONTEXT] Entering dictation mode...")
        self.dictation_mode = True
        # Get current active window for dictation target
        title, region = self.update_active_window()
        self.dictation_target_app = title
        log_info(f"Dictation mode ON | Target: {title}")
        # print(f"[CONTEXT] Dictation mode ON | Target: {title}")

    def exit_dictation_mode(self):
        """Exit dictation mode"""
        # print("[CONTEXT] Exiting dictation mode...")
        self.dictation_mode = False
        self.dictation_target_app = None
        log_info("Dictation mode OFF")
        # print("[CONTEXT] Dictation mode OFF")

    def is_in_dictation_mode(self):
        return self.dictation_mode

    # ── System State ──────────────────────────────────────────

    def set_listening(self, state):
        # print(f"[CONTEXT] Listening state: {state}")
        self.is_listening = state

    def set_processing(self, state):
        # print(f"[CONTEXT] Processing state: {state}")
        self.is_processing = state

    def set_muted(self, state):
        # print(f"[CONTEXT] Muted state: {state}")
        self.system_muted = state

    # ── Language ──────────────────────────────────────────────

    def update_language(self, language_code, language_name):
        """Update current language"""
        # print(f"[CONTEXT] Language updated: {language_code}")
        self.current_language = language_code
        self.current_language_name = language_name
        log_info(f"Language updated: {language_name}")

    def get_language(self):
        return self.current_language

    # ── Wake Word ─────────────────────────────────────────────

    def update_wake_word(self, wake_word, sensitivity=0.6):
        """Update wake word"""
        # print(f"[CONTEXT] Wake word updated: {wake_word}")
        self.wake_word = wake_word.lower().strip()
        self.wake_word_sensitivity = sensitivity
        log_info(f"Wake word updated: {wake_word}")

    def get_wake_word(self):
        return self.wake_word

    def get_wake_word_sensitivity(self):
        return self.wake_word_sensitivity

    # ── History ───────────────────────────────────────────────

    def get_last_n_commands(self, n=5):
        """Get last n commands from history"""
        # print(f"[CONTEXT] Getting last {n} commands...")
        return self.command_history[-n:] if self.command_history else []

    def get_last_command(self):
        if self.command_history:
            return self.command_history[-1]
        return None

    def clear_history(self):
        # print("[CONTEXT] Clearing command history...")
        self.command_history = []
        log_info("Command history cleared")

    # ── Screen ────────────────────────────────────────────────

    def get_active_window_region(self):
        """Get active window region for screenshot"""
        # print(f"[CONTEXT] Getting active window region: {self.active_window_region}")
        return self.active_window_region

    def refresh_window_info(self):
        """Refresh active window info"""
        # print("[CONTEXT] Refreshing window info...")
        return self.update_active_window()


# ── Singleton Instance ────────────────────────────────────────

_context_manager = None

def get_context_manager():
    global _context_manager
    if _context_manager is None:
        # print("[CONTEXT] Creating singleton ContextManager...")
        _context_manager = ContextManager()
    return _context_manager
'''

## What this file does:

| Function | Purpose |
|---|---|
| `set_user()` | Loads user language, wake word from profile |
| `set_active_app()` | Tracks which app is open |
| `update_active_window()` | Gets focused window via win32gui |
| `update()` | Updates after every command |
| `get_context()` | Returns full context dict to pipeline |
| `enter_dictation_mode()` | Activates dictation |
| `exit_dictation_mode()` | Deactivates dictation |
| `update_language()` | Changes language mid-session |
| `update_wake_word()` | Updates wake word mid-session |
| `get_last_n_commands()` | Returns command history |
| `refresh_window_info()` | Updates active window region for OCR |
| `get_context_manager()` | Singleton — creates once |

---

## How it connects to pipeline:
```
Every pipeline step receives context
        ↓
ASR uses context.current_language
Translation uses context.current_language
SBERT uses context.last_intent
Command handler uses context.active_app
Dictation uses context.dictation_mode
Wake word uses context.wake_word

'''