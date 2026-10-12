# DeskmateAI/backend/core/undo_redo.py

import os
import sys

# ============================================================
# UNDO/REDO MANAGER FOR DESKMATEAI
# Tracks every executed action
# Provides undo and redo functionality
# Each action has a reverse action defined
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import get_timestamp

# ── Action Class ──────────────────────────────────────────────

class Action:
    def __init__(self, intent, command, entity, execute_fn, undo_fn, description):
        """
        intent      → intent name e.g. 'open_app'
        command     → original command text
        entity      → e.g. app name, volume level
        execute_fn  → function to execute action
        undo_fn     → function to undo action (None if not undoable)
        description → human readable description
        """
        self.intent = intent
        self.command = command
        self.entity = entity
        self.execute_fn = execute_fn
        self.undo_fn = undo_fn
        self.description = description
        self.timestamp = get_timestamp()
        self.is_undoable = undo_fn is not None

    def execute(self):
        # print(f"[ACTION] Executing: {self.description}")
        try:
            if self.execute_fn:
                self.execute_fn()
                return True
            return False
        except Exception as e:
            # print(f"[ACTION] Error executing: {e}")
            log_error(f"Error executing action {self.description}: {e}")
            return False

    def undo(self):
        # print(f"[ACTION] Undoing: {self.description}")
        try:
            if self.undo_fn:
                self.undo_fn()
                return True
            # print(f"[ACTION] Action not undoable: {self.description}")
            return False
        except Exception as e:
            # print(f"[ACTION] Error undoing: {e}")
            log_error(f"Error undoing action {self.description}: {e}")
            return False


# ── Undo Redo Manager ─────────────────────────────────────────

class UndoRedoManager:

    def __init__(self):
        # print("[UNDO_REDO] Initializing UndoRedoManager...")
        self._undo_stack = []   # executed actions
        self._redo_stack = []   # undone actions
        self.MAX_STACK_SIZE = 20
        log_info("UndoRedoManager initialized")

    def push_action(self, action):
        """Push new action to undo stack"""
        # print(f"[UNDO_REDO] Pushing action: {action.description}")
        self._undo_stack.append(action)

        # Clear redo stack when new action is pushed
        self._redo_stack.clear()

        # Limit stack size
        if len(self._undo_stack) > self.MAX_STACK_SIZE:
            self._undo_stack.pop(0)

        log_debug(f"Action pushed: {action.description} | Stack size: {len(self._undo_stack)}")
        # print(f"[UNDO_REDO] Stack size: {len(self._undo_stack)}")

    def undo(self):
        """Undo last action"""
        # print("[UNDO_REDO] Attempting undo...")

        if not self._undo_stack:
            # print("[UNDO_REDO] Nothing to undo")
            log_warning("Nothing to undo")
            return False, "Nothing to undo"

        # Get last action
        action = self._undo_stack[-1]

        if not action.is_undoable:
            # print(f"[UNDO_REDO] Action not undoable: {action.description}")
            log_warning(f"Action cannot be undone: {action.description}")
            return False, f"Cannot undo: {action.description}"

        # Execute undo
        result = action.undo()

        if result:
            # Move from undo to redo stack
            self._undo_stack.pop()
            self._redo_stack.append(action)
            log_info(f"Undone: {action.description}")
            # print(f"[UNDO_REDO] ✅ Undone: {action.description}")
            return True, f"Undone: {action.description}"
        else:
            log_error(f"Failed to undo: {action.description}")
            return False, f"Failed to undo: {action.description}"

    def redo(self):
        """Redo last undone action"""
        # print("[UNDO_REDO] Attempting redo...")

        if not self._redo_stack:
            # print("[UNDO_REDO] Nothing to redo")
            log_warning("Nothing to redo")
            return False, "Nothing to redo"

        # Get last undone action
        action = self._redo_stack[-1]

        # Execute action again
        result = action.execute()

        if result:
            # Move back to undo stack
            self._redo_stack.pop()
            self._undo_stack.append(action)
            log_info(f"Redone: {action.description}")
            # print(f"[UNDO_REDO] ✅ Redone: {action.description}")
            return True, f"Redone: {action.description}"
        else:
            log_error(f"Failed to redo: {action.description}")
            return False, f"Failed to redo: {action.description}"

    def can_undo(self):
        """Check if undo is possible"""
        if not self._undo_stack:
            return False
        return self._undo_stack[-1].is_undoable

    def can_redo(self):
        """Check if redo is possible"""
        return len(self._redo_stack) > 0

    def get_undo_description(self):
        """Get description of what will be undone"""
        if self._undo_stack and self._undo_stack[-1].is_undoable:
            return self._undo_stack[-1].description
        return None

    def get_redo_description(self):
        """Get description of what will be redone"""
        if self._redo_stack:
            return self._redo_stack[-1].description
        return None

    def clear(self):
        """Clear both stacks"""
        # print("[UNDO_REDO] Clearing stacks...")
        self._undo_stack.clear()
        self._redo_stack.clear()
        log_info("Undo/Redo stacks cleared")

    def get_history(self):
        """Get action history"""
        # print("[UNDO_REDO] Getting history...")
        return [
            {
                "description": a.description,
                "intent": a.intent,
                "timestamp": a.timestamp,
                "is_undoable": a.is_undoable
            }
            for a in self._undo_stack
        ]

    def get_stack_info(self):
        """Get stack sizes for UI"""
        return {
            "undo_count": len(self._undo_stack),
            "redo_count": len(self._redo_stack),
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "undo_description": self.get_undo_description(),
            "redo_description": self.get_redo_description()
        }


# ── Action Factory ────────────────────────────────────────────
# Creates Action objects for each intent type
# Each action has its undo counterpart defined

class ActionFactory:

    @staticmethod
    def create_open_app_action(app_name, open_fn, close_fn):
        """Open app → undo closes it"""
        # print(f"[ACTION_FACTORY] Creating open_app action: {app_name}")
        return Action(
            intent="open_app",
            command=f"open {app_name}",
            entity=app_name,
            execute_fn=open_fn,
            undo_fn=close_fn,
            description=f"Opened {app_name}"
        )

    @staticmethod
    def create_close_app_action(app_name, close_fn, open_fn):
        """Close app → undo reopens it"""
        # print(f"[ACTION_FACTORY] Creating close_app action: {app_name}")
        return Action(
            intent="close_app",
            command=f"close {app_name}",
            entity=app_name,
            execute_fn=close_fn,
            undo_fn=open_fn,
            description=f"Closed {app_name}"
        )

    @staticmethod
    def create_volume_up_action(steps, volume_up_fn, volume_down_fn):
        """Volume up → undo decreases same steps"""
        # print(f"[ACTION_FACTORY] Creating volume_up action: {steps} steps")
        return Action(
            intent="volume_up",
            command="volume up",
            entity=steps,
            execute_fn=volume_up_fn,
            undo_fn=volume_down_fn,
            description=f"Volume increased by {steps} steps"
        )

    @staticmethod
    def create_volume_down_action(steps, volume_down_fn, volume_up_fn):
        """Volume down → undo increases same steps"""
        # print(f"[ACTION_FACTORY] Creating volume_down action: {steps} steps")
        return Action(
            intent="volume_down",
            command="volume down",
            entity=steps,
            execute_fn=volume_down_fn,
            undo_fn=volume_up_fn,
            description=f"Volume decreased by {steps} steps"
        )

    @staticmethod
    def create_mute_action(mute_fn, unmute_fn):
        """Mute → undo unmutes"""
        # print("[ACTION_FACTORY] Creating mute action")
        return Action(
            intent="mute",
            command="mute",
            entity=None,
            execute_fn=mute_fn,
            undo_fn=unmute_fn,
            description="Muted audio"
        )

    @staticmethod
    def create_unmute_action(unmute_fn, mute_fn):
        """Unmute → undo mutes"""
        # print("[ACTION_FACTORY] Creating unmute action")
        return Action(
            intent="unmute",
            command="unmute",
            entity=None,
            execute_fn=unmute_fn,
            undo_fn=mute_fn,
            description="Unmuted audio"
        )

    @staticmethod
    def create_brightness_up_action(steps, brightness_up_fn, brightness_down_fn):
        """Brightness up → undo decreases"""
        # print(f"[ACTION_FACTORY] Creating brightness_up action")
        return Action(
            intent="brightness_up",
            command="brightness up",
            entity=steps,
            execute_fn=brightness_up_fn,
            undo_fn=brightness_down_fn,
            description=f"Brightness increased"
        )

    @staticmethod
    def create_brightness_down_action(steps, brightness_down_fn, brightness_up_fn):
        """Brightness down → undo increases"""
        # print(f"[ACTION_FACTORY] Creating brightness_down action")
        return Action(
            intent="brightness_down",
            command="brightness down",
            entity=steps,
            execute_fn=brightness_down_fn,
            undo_fn=brightness_up_fn,
            description=f"Brightness decreased"
        )

    @staticmethod
    def create_type_text_action(text, type_fn, undo_type_fn):
        """Type text → undo deletes it"""
        # print(f"[ACTION_FACTORY] Creating type_text action")
        return Action(
            intent="write_text",
            command="write text",
            entity=text,
            execute_fn=type_fn,
            undo_fn=undo_type_fn,
            description=f"Typed text"
        )

    @staticmethod
    def create_search_action(query, search_fn, close_tab_fn):
        """Search → undo closes tab"""
        # print(f"[ACTION_FACTORY] Creating search action: {query}")
        return Action(
            intent="search",
            command=f"search {query}",
            entity=query,
            execute_fn=search_fn,
            undo_fn=close_tab_fn,
            description=f"Searched: {query}"
        )

    @staticmethod
    def create_minimize_action(minimize_fn, restore_fn):
        """Minimize → undo restores"""
        # print("[ACTION_FACTORY] Creating minimize action")
        return Action(
            intent="minimize_window",
            command="minimize window",
            entity=None,
            execute_fn=minimize_fn,
            undo_fn=restore_fn,
            description="Minimized window"
        )

    @staticmethod
    def create_maximize_action(maximize_fn, restore_fn):
        """Maximize → undo restores"""
        # print("[ACTION_FACTORY] Creating maximize action")
        return Action(
            intent="maximize_window",
            command="maximize window",
            entity=None,
            execute_fn=maximize_fn,
            undo_fn=restore_fn,
            description="Maximized window"
        )

    @staticmethod
    def create_screenshot_action(screenshot_fn):
        """Screenshot → cannot be undone"""
        # print("[ACTION_FACTORY] Creating screenshot action")
        return Action(
            intent="screenshot",
            command="take screenshot",
            entity=None,
            execute_fn=screenshot_fn,
            undo_fn=None,   # Cannot undo screenshot
            description="Took screenshot"
        )

    @staticmethod
    def create_shutdown_action(shutdown_fn):
        """Shutdown → cannot be undone"""
        # print("[ACTION_FACTORY] Creating shutdown action")
        return Action(
            intent="system_shutdown",
            command="shutdown",
            entity=None,
            execute_fn=shutdown_fn,
            undo_fn=None,   # Cannot undo shutdown
            description="System shutdown"
        )

    @staticmethod
    def create_new_tab_action(new_tab_fn, close_tab_fn):
        """New tab → undo closes it"""
        # print("[ACTION_FACTORY] Creating new_tab action")
        return Action(
            intent="new_tab",
            command="open new tab",
            entity=None,
            execute_fn=new_tab_fn,
            undo_fn=close_tab_fn,
            description="Opened new tab"
        )

    @staticmethod
    def create_scroll_action(direction, scroll_fn, reverse_scroll_fn):
        """Scroll → undo scrolls opposite"""
        # print(f"[ACTION_FACTORY] Creating scroll action: {direction}")
        return Action(
            intent=f"scroll_{direction}",
            command=f"scroll {direction}",
            entity=direction,
            execute_fn=scroll_fn,
            undo_fn=reverse_scroll_fn,
            description=f"Scrolled {direction}"
        )

    @staticmethod
    def create_generic_action(intent, command, execute_fn, undo_fn=None):
        """Generic action for anything not covered above"""
        # print(f"[ACTION_FACTORY] Creating generic action: {intent}")
        return Action(
            intent=intent,
            command=command,
            entity=None,
            execute_fn=execute_fn,
            undo_fn=undo_fn,
            description=f"Executed: {command}"
        )


# ── Singleton Instance ────────────────────────────────────────

_undo_redo_manager = None

def get_undo_redo_manager():
    global _undo_redo_manager
    if _undo_redo_manager is None:
        # print("[UNDO_REDO] Creating singleton UndoRedoManager...")
        _undo_redo_manager = UndoRedoManager()
    return _undo_redo_manager


def get_action_factory():
    return ActionFactory()