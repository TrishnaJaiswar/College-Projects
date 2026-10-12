# DeskmateAI/backend/core/registry.py

import os
import sys

# ============================================================
# COMMAND REGISTRY FOR DESKMATEAI
# Central registry that maps every intent to its handler
# Every intent defined here with:
# - Handler function
# - Whether it needs entity extraction
# - Whether it is undoable
# - Response key for TTS
# - Description
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug

# ── Registry Entry Class ──────────────────────────────────────

class RegistryEntry:
    def __init__(
        self,
        intent,
        handler_module,
        handler_function,
        needs_entity=False,
        entity_type=None,
        is_undoable=False,
        response_key=None,
        description="",
        requires_confirmation=False
    ):
        """
        intent              → intent name
        handler_module      → which automation module handles it
        handler_function    → function name in that module
        needs_entity        → does it need an extracted entity?
        entity_type         → what type of entity (app_name, query, level)
        is_undoable         → can this be undone?
        response_key        → key in RESPONSES dict for TTS
        description         → human readable description
        requires_confirmation → ask user before executing (e.g. shutdown)
        """
        self.intent = intent
        self.handler_module = handler_module
        self.handler_function = handler_function
        self.needs_entity = needs_entity
        self.entity_type = entity_type
        self.is_undoable = is_undoable
        self.response_key = response_key
        self.description = description
        self.requires_confirmation = requires_confirmation


# ── Command Registry ──────────────────────────────────────────

class CommandRegistry:

    def __init__(self):
        # print("[REGISTRY] Initializing CommandRegistry...")
        self._registry = {}
        self._register_all()
        log_info(f"CommandRegistry initialized with {len(self._registry)} intents")
        # print(f"[REGISTRY] Registered {len(self._registry)} intents")

    def _register_all(self):
        """Register all intents"""
        # print("[REGISTRY] Registering all intents...")

        # ── App Control ───────────────────────────────────────
        self._register(RegistryEntry(
            intent="open_app",
            handler_module="automation.app_launcher",
            handler_function="open_app",
            needs_entity=True,
            entity_type="app_name",
            is_undoable=True,
            response_key="opening_app",
            description="Open an application"
        ))

        self._register(RegistryEntry(
            intent="close_app",
            handler_module="automation.app_launcher",
            handler_function="close_app",
            needs_entity=True,
            entity_type="app_name",
            is_undoable=True,
            response_key="closing_app",
            description="Close an application"
        ))

        # ── Volume Control ────────────────────────────────────
        self._register(RegistryEntry(
            intent="volume_up",
            handler_module="automation.system_controls",
            handler_function="volume_up",
            needs_entity=False,
            is_undoable=True,
            response_key="volume_up",
            description="Increase volume"
        ))

        self._register(RegistryEntry(
            intent="volume_down",
            handler_module="automation.system_controls",
            handler_function="volume_down",
            needs_entity=False,
            is_undoable=True,
            response_key="volume_down",
            description="Decrease volume"
        ))

        self._register(RegistryEntry(
            intent="mute",
            handler_module="automation.system_controls",
            handler_function="mute",
            needs_entity=False,
            is_undoable=True,
            response_key="muted",
            description="Mute audio"
        ))

        self._register(RegistryEntry(
            intent="unmute",
            handler_module="automation.system_controls",
            handler_function="unmute",
            needs_entity=False,
            is_undoable=True,
            response_key="unmuted",
            description="Unmute audio"
        ))

        # ── Brightness Control ────────────────────────────────
        self._register(RegistryEntry(
            intent="brightness_up",
            handler_module="automation.system_controls",
            handler_function="brightness_up",
            needs_entity=False,
            is_undoable=True,
            response_key="brightness_up",
            description="Increase brightness"
        ))

        self._register(RegistryEntry(
            intent="brightness_down",
            handler_module="automation.system_controls",
            handler_function="brightness_down",
            needs_entity=False,
            is_undoable=True,
            response_key="brightness_down",
            description="Decrease brightness"
        ))

        # ── System Control ────────────────────────────────────
        self._register(RegistryEntry(
            intent="system_shutdown",
            handler_module="automation.system_controls",
            handler_function="shutdown",
            needs_entity=False,
            is_undoable=False,
            response_key="shutting_down",
            description="Shutdown system",
            requires_confirmation=True
        ))

        self._register(RegistryEntry(
            intent="system_restart",
            handler_module="automation.system_controls",
            handler_function="restart",
            needs_entity=False,
            is_undoable=False,
            response_key="restarting",
            description="Restart system",
            requires_confirmation=True
        ))

        self._register(RegistryEntry(
            intent="system_sleep",
            handler_module="automation.system_controls",
            handler_function="sleep",
            needs_entity=False,
            is_undoable=False,
            response_key="sleeping",
            description="Sleep system"
        ))

        self._register(RegistryEntry(
            intent="system_lock",
            handler_module="automation.system_controls",
            handler_function="lock_screen",
            needs_entity=False,
            is_undoable=False,
            response_key="locking",
            description="Lock screen"
        ))

        # ── Web/Search ────────────────────────────────────────
        self._register(RegistryEntry(
            intent="search",
            handler_module="automation.web_interaction",
            handler_function="search",
            needs_entity=True,
            entity_type="query",
            is_undoable=True,
            response_key="searching",
            description="Search on Google"
        ))

        self._register(RegistryEntry(
            intent="new_tab",
            handler_module="automation.web_interaction",
            handler_function="new_tab",
            needs_entity=False,
            is_undoable=True,
            response_key="new_tab_opened",
            description="Open new browser tab"
        ))

        self._register(RegistryEntry(
            intent="close_tab",
            handler_module="automation.web_interaction",
            handler_function="close_tab",
            needs_entity=False,
            is_undoable=True,
            response_key="tab_closed",
            description="Close browser tab"
        ))

        # ── Media Control ─────────────────────────────────────
        self._register(RegistryEntry(
            intent="media_play",
            handler_module="automation.media_controls",
            handler_function="play_pause",
            needs_entity=False,
            is_undoable=False,
            response_key="playing",
            description="Play media"
        ))

        self._register(RegistryEntry(
            intent="media_pause",
            handler_module="automation.media_controls",
            handler_function="play_pause",
            needs_entity=False,
            is_undoable=False,
            response_key="pausing",
            description="Pause media"
        ))

        self._register(RegistryEntry(
            intent="media_next",
            handler_module="automation.media_controls",
            handler_function="next_track",
            needs_entity=False,
            is_undoable=False,
            response_key="next_track",
            description="Next media track"
        ))

        self._register(RegistryEntry(
            intent="media_previous",
            handler_module="automation.media_controls",
            handler_function="previous_track",
            needs_entity=False,
            is_undoable=False,
            response_key="previous_track",
            description="Previous media track"
        ))

        # ── Window Control ────────────────────────────────────
        self._register(RegistryEntry(
            intent="minimize_window",
            handler_module="automation.app_workflows",
            handler_function="minimize_window",
            needs_entity=False,
            is_undoable=True,
            response_key="minimizing",
            description="Minimize window"
        ))

        self._register(RegistryEntry(
            intent="maximize_window",
            handler_module="automation.app_workflows",
            handler_function="maximize_window",
            needs_entity=False,
            is_undoable=True,
            response_key="maximizing",
            description="Maximize window"
        ))

        self._register(RegistryEntry(
            intent="close_window",
            handler_module="automation.app_workflows",
            handler_function="close_window",
            needs_entity=False,
            is_undoable=False,
            response_key="closing_window",
            description="Close window"
        ))

        self._register(RegistryEntry(
            intent="switch_window",
            handler_module="automation.app_workflows",
            handler_function="switch_window",
            needs_entity=True,
            entity_type="app_name",
            is_undoable=False,
            response_key="switching_window",
            description="Switch to window"
        ))

        # ── Dictation/Typing ──────────────────────────────────
        self._register(RegistryEntry(
            intent="write_text",
            handler_module="automation.ui_typing",
            handler_function="start_dictation",
            needs_entity=False,
            is_undoable=True,
            response_key="dictation_start",
            description="Start voice dictation"
        ))

        self._register(RegistryEntry(
            intent="copy_text",
            handler_module="automation.ui_typing",
            handler_function="copy_text",
            needs_entity=False,
            is_undoable=False,
            response_key="copied",
            description="Copy selected text"
        ))

        self._register(RegistryEntry(
            intent="paste_text",
            handler_module="automation.ui_typing",
            handler_function="paste_text",
            needs_entity=False,
            is_undoable=True,
            response_key="pasted",
            description="Paste text"
        ))

        self._register(RegistryEntry(
            intent="select_all",
            handler_module="automation.ui_typing",
            handler_function="select_all",
            needs_entity=False,
            is_undoable=True,
            response_key="selected_all",
            description="Select all text"
        ))

        self._register(RegistryEntry(
            intent="save_file",
            handler_module="automation.ui_typing",
            handler_function="save_file",
            needs_entity=False,
            is_undoable=False,
            response_key="file_saved",
            description="Save current file"
        ))

        # ── Screenshot ────────────────────────────────────────
        self._register(RegistryEntry(
            intent="screenshot",
            handler_module="automation.app_workflows",
            handler_function="take_screenshot",
            needs_entity=False,
            is_undoable=False,
            response_key="screenshot_taken",
            description="Take screenshot"
        ))

        # ── Scroll ────────────────────────────────────────────
        self._register(RegistryEntry(
            intent="scroll_up",
            handler_module="automation.ui_clicking",
            handler_function="scroll_up",
            needs_entity=False,
            is_undoable=True,
            response_key="scrolling_up",
            description="Scroll up"
        ))

        self._register(RegistryEntry(
            intent="scroll_down",
            handler_module="automation.ui_clicking",
            handler_function="scroll_down",
            needs_entity=False,
            is_undoable=True,
            response_key="scrolling_down",
            description="Scroll down"
        ))

        # ── Click ─────────────────────────────────────────────
        self._register(RegistryEntry(
            intent="click_element",
            handler_module="automation.ui_clicking",
            handler_function="click_element",
            needs_entity=True,
            entity_type="element_name",
            is_undoable=False,
            response_key="clicked",
            description="Click UI element"
        ))

        # ── Zoom ──────────────────────────────────────────────
        self._register(RegistryEntry(
            intent="zoom_in",
            handler_module="automation.ui_clicking",
            handler_function="zoom_in",
            needs_entity=False,
            is_undoable=True,
            response_key="zoomed_in",
            description="Zoom in"
        ))

        self._register(RegistryEntry(
            intent="zoom_out",
            handler_module="automation.ui_clicking",
            handler_function="zoom_out",
            needs_entity=False,
            is_undoable=True,
            response_key="zoomed_out",
            description="Zoom out"
        ))

        # ── Undo/Redo ─────────────────────────────────────────
        self._register(RegistryEntry(
            intent="undo_command",
            handler_module="core.command_executor",
            handler_function="undo",
            needs_entity=False,
            is_undoable=False,
            response_key="undone",
            description="Undo last action"
        ))

        self._register(RegistryEntry(
            intent="redo_command",
            handler_module="core.command_executor",
            handler_function="redo",
            needs_entity=False,
            is_undoable=False,
            response_key="redone",
            description="Redo last action"
        ))

        # print(f"[REGISTRY] All intents registered: {list(self._registry.keys())}")

    def _register(self, entry):
        """Register single entry"""
        self._registry[entry.intent] = entry
        # print(f"[REGISTRY] Registered: {entry.intent}")

    def get(self, intent):
        """Get registry entry for intent"""
        # print(f"[REGISTRY] Getting entry for: {intent}")
        entry = self._registry.get(intent)
        if not entry:
            log_debug(f"Intent not found in registry: {intent}")
        return entry

    def get_all_intents(self):
        """Get list of all registered intents"""
        return list(self._registry.keys())

    def is_registered(self, intent):
        """Check if intent is registered"""
        return intent in self._registry

    def get_all_entries(self):
        """Get all registry entries"""
        return self._registry

    def register_custom(self, intent, handler_module, handler_function,
                       needs_entity=False, entity_type=None,
                       response_key="done", description=""):
        """
        Register custom intent from UI settings
        Called when user adds new intent from settings window
        """
        # print(f"[REGISTRY] Registering custom intent: {intent}")
        entry = RegistryEntry(
            intent=intent,
            handler_module=handler_module,
            handler_function=handler_function,
            needs_entity=needs_entity,
            entity_type=entity_type,
            is_undoable=False,
            response_key=response_key,
            description=description
        )
        self._register(entry)
        log_info(f"Custom intent registered: {intent}")
        return True

    def get_intent_info(self, intent):
        """Get human readable info about intent"""
        entry = self.get(intent)
        if not entry:
            return None
        return {
            "intent": entry.intent,
            "description": entry.description,
            "needs_entity": entry.needs_entity,
            "entity_type": entry.entity_type,
            "is_undoable": entry.is_undoable,
            "requires_confirmation": entry.requires_confirmation,
            "response_key": entry.response_key
        }


# ── Singleton Instance ────────────────────────────────────────

_registry = None

def get_registry():
    global _registry
    if _registry is None:
        # print("[REGISTRY] Creating singleton CommandRegistry...")
        _registry = CommandRegistry()
    return _registry