# DeskmateAI/backend/core/memory.py

import os
import sys

# ============================================================
# MEMORY MANAGER FOR DESKMATEAI
# Handles loading and saving of ALL persistent data
# Intent examples, intent memory, user profiles
# Everything persists even after system closes
# ============================================================

# Add base dir to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.utils import (
    load_json, save_json,
    get_intent_examples_path,
    get_intent_memory_path,
    get_profile_path,
    get_user_dir,
    list_users,
    get_timestamp,
    ensure_dir,
    get_intents_dir
)
from backend.utils.logger import log_info, log_error, log_debug

# ── Default Intent Examples ───────────────────────────────────

DEFAULT_INTENT_EXAMPLES = {
    "open_app": [
        "open chrome",
        "launch browser",
        "start firefox",
        "open an app",
        "run spotify",
        "open notepad",
        "launch word",
        "start excel",
        "open vlc",
        "run application"
    ],
    "close_app": [
        "close chrome",
        "exit app",
        "shut down browser",
        "close this window",
        "exit notepad",
        "close word",
        "quit application",
        "close firefox"
    ],
    "search": [
        "search for cats",
        "look up python",
        "google something",
        "find information about",
        "search on google",
        "search youtube",
        "look for videos",
        "find me information"
    ],
    "volume_up": [
        "increase volume",
        "turn up the sound",
        "make it louder",
        "volume up",
        "raise the volume",
        "louder please",
        "increase the audio"
    ],
    "volume_down": [
        "decrease volume",
        "turn down the sound",
        "make it quieter",
        "volume down",
        "lower the volume",
        "quieter please",
        "reduce audio"
    ],
    "mute": [
        "mute the sound",
        "turn off sound",
        "silence",
        "mute audio",
        "turn off volume",
        "no sound please"
    ],
    "unmute": [
        "unmute",
        "turn on sound",
        "unmute audio",
        "restore sound",
        "sound on"
    ],
    "brightness_up": [
        "increase brightness",
        "make screen brighter",
        "brightness up",
        "turn up brightness",
        "more brightness"
    ],
    "brightness_down": [
        "decrease brightness",
        "make screen dimmer",
        "brightness down",
        "turn down brightness",
        "less brightness"
    ],
    "system_shutdown": [
        "shutdown the system",
        "turn off computer",
        "power off",
        "shut down",
        "turn off the pc"
    ],
    "system_restart": [
        "restart the computer",
        "reboot system",
        "restart",
        "reboot the pc",
        "restart computer"
    ],
    "system_sleep": [
        "sleep mode",
        "put computer to sleep",
        "hibernate",
        "sleep the system"
    ],
    "system_lock": [
        "lock the screen",
        "lock computer",
        "lock screen",
        "lock the system"
    ],
    "write_text": [
        "write an email",
        "type something",
        "dictate a letter",
        "write this for me",
        "compose a message",
        "type this text",
        "write a document",
        "start dictation"
    ],
    "undo_command": [
        "undo that",
        "undo",
        "go back",
        "reverse that",
        "undo last action",
        "take that back"
    ],
    "redo_command": [
        "redo that",
        "redo",
        "do it again",
        "repeat that",
        "redo last action"
    ],
    "media_play": [
        "play music",
        "play video",
        "resume",
        "play",
        "resume music",
        "start playing"
    ],
    "media_pause": [
        "pause music",
        "pause video",
        "pause",
        "stop playing",
        "pause playback"
    ],
    "media_next": [
        "next song",
        "skip song",
        "next track",
        "skip to next",
        "play next"
    ],
    "media_previous": [
        "previous song",
        "go back song",
        "previous track",
        "play previous",
        "last song"
    ],
    "screenshot": [
        "take a screenshot",
        "capture screen",
        "screenshot",
        "take screenshot",
        "capture the screen"
    ],
    "minimize_window": [
        "minimize window",
        "minimize this",
        "hide window",
        "minimize the window"
    ],
    "maximize_window": [
        "maximize window",
        "maximize this",
        "full screen",
        "make window bigger",
        "expand window"
    ],
    "close_window": [
        "close window",
        "close this",
        "exit this",
        "close current window"
    ],
    "scroll_up": [
        "scroll up",
        "go up",
        "move up",
        "scroll to top"
    ],
    "scroll_down": [
        "scroll down",
        "go down",
        "move down",
        "scroll to bottom"
    ],
    "click_element": [
        "click",
        "click on",
        "press",
        "tap",
        "click the button",
        "press the button"
    ],
    "switch_window": [
        "switch window",
        "change window",
        "go to next window",
        "switch to",
        "open other window"
    ],
    "copy_text": [
        "copy that",
        "copy this",
        "copy text",
        "copy selected"
    ],
    "paste_text": [
        "paste that",
        "paste this",
        "paste text",
        "paste here"
    ],
    "select_all": [
        "select all",
        "select everything",
        "highlight all"
    ],
    "save_file": [
        "save file",
        "save this",
        "save document",
        "save the file"
    ],
    "new_tab": [
        "open new tab",
        "new tab",
        "create new tab"
    ],
    "close_tab": [
        "close tab",
        "close this tab",
        "close current tab"
    ],
    "zoom_in": [
        "zoom in",
        "make bigger",
        "increase zoom",
        "zoom"
    ],
    "zoom_out": [
        "zoom out",
        "make smaller",
        "decrease zoom"
    ]
}

# ── Memory Class ──────────────────────────────────────────────

class MemoryManager:

    def __init__(self):
        # print("[MEMORY] Initializing MemoryManager...")
        self._intent_examples = None
        self._intent_memory = None
        self._ensure_intent_files()
        log_info("MemoryManager initialized")

    def _ensure_intent_files(self):
        # print("[MEMORY] Ensuring intent files exist...")
        ensure_dir(get_intents_dir())

        # Create intent_examples.json if empty or missing
        examples_path = get_intent_examples_path()
        existing = load_json(examples_path)
        if not existing:
            # print("[MEMORY] Creating default intent examples...")
            save_json(examples_path, DEFAULT_INTENT_EXAMPLES)
            log_info("Default intent examples created")

        # Create intent_memory.json if missing
        memory_path = get_intent_memory_path()
        existing_memory = load_json(memory_path)
        if not existing_memory:
            # print("[MEMORY] Creating empty intent memory...")
            save_json(memory_path, {})
            log_info("Empty intent memory created")

    # ── Intent Examples ───────────────────────────────────────

    def load_intent_examples(self):
        # print("[MEMORY] Loading intent examples...")
        data = load_json(get_intent_examples_path())
        if not data:
            data = DEFAULT_INTENT_EXAMPLES
        self._intent_examples = data
        # print(f"[MEMORY] Loaded {len(data)} intent categories")
        log_debug(f"Loaded {len(data)} intent categories from examples")
        return data

    def save_intent_examples(self, examples):
        # print("[MEMORY] Saving intent examples...")
        result = save_json(get_intent_examples_path(), examples)
        if result:
            self._intent_examples = examples
            log_info(f"Saved {len(examples)} intent categories to examples")
        return result

    def add_intent_example(self, intent, example_text):
        # print(f"[MEMORY] Adding example to intent '{intent}': {example_text}")
        examples = self.load_intent_examples()
        if intent not in examples:
            examples[intent] = []
        if example_text not in examples[intent]:
            examples[intent].append(example_text)
            self.save_intent_examples(examples)
            log_info(f"Added example to intent '{intent}': {example_text}")
            return True
        return False

    def remove_intent(self, intent):
        # print(f"[MEMORY] Removing intent: {intent}")
        examples = self.load_intent_examples()
        if intent in examples:
            del examples[intent]
            self.save_intent_examples(examples)
            log_info(f"Removed intent: {intent}")
            return True
        return False

    def add_new_intent(self, intent_name, examples_list):
        # print(f"[MEMORY] Adding new intent: {intent_name}")
        examples = self.load_intent_examples()
        examples[intent_name] = examples_list
        self.save_intent_examples(examples)
        log_info(f"Added new intent: {intent_name} with {len(examples_list)} examples")
        return True

    # ── Intent Memory (Learned) ───────────────────────────────

    def load_intent_memory(self):
        # print("[MEMORY] Loading intent memory...")
        data = load_json(get_intent_memory_path())
        self._intent_memory = data
        # print(f"[MEMORY] Loaded {len(data)} learned intents")
        log_debug(f"Loaded {len(data)} learned intents from memory")
        return data

    def save_intent_memory(self, memory):
        # print("[MEMORY] Saving intent memory...")
        result = save_json(get_intent_memory_path(), memory)
        if result:
            self._intent_memory = memory
            log_info(f"Saved {len(memory)} learned intents to memory")
        return result

    def learn_new_command(self, command, intent):
        # print(f"[MEMORY] Learning new command: '{command}' → {intent}")
        memory = self.load_intent_memory()
        if intent not in memory:
            memory[intent] = []
        if command not in memory[intent]:
            memory[intent].append(command)
            self.save_intent_memory(memory)
            log_info(f"Learned: '{command}' → {intent}")
            return True
        return False

    def get_all_intents(self):
        # print("[MEMORY] Getting all intents (examples + memory)...")
        examples = self.load_intent_examples()
        memory = self.load_intent_memory()

        # Merge both
        all_intents = {}
        for intent, commands in examples.items():
            all_intents[intent] = list(commands)

        for intent, commands in memory.items():
            if intent in all_intents:
                # Add learned commands to existing intent
                for cmd in commands:
                    if cmd not in all_intents[intent]:
                        all_intents[intent].append(cmd)
            else:
                # New intent from memory
                all_intents[intent] = list(commands)

        # print(f"[MEMORY] Total intents: {len(all_intents)}")
        return all_intents

    # ── User Profile Memory ───────────────────────────────────

    def load_user_profile(self, username):
        # print(f"[MEMORY] Loading profile for: {username}")
        return load_json(get_profile_path(username))

    def save_user_profile(self, username, profile):
        # print(f"[MEMORY] Saving profile for: {username}")
        result = save_json(get_profile_path(username), profile)
        if result:
            log_info(f"Profile saved for user: {username}")
        return result

    def update_last_login(self, username):
        # print(f"[MEMORY] Updating last login for: {username}")
        profile = self.load_user_profile(username)
        profile['last_login'] = get_timestamp()
        self.save_user_profile(username, profile)

    def get_all_users(self):
        # print("[MEMORY] Getting all users...")
        return list_users()

    def get_admin_user(self):
        # print("[MEMORY] Getting admin user...")
        users = self.get_all_users()
        for username in users:
            profile = self.load_user_profile(username)
            if profile.get('is_admin', False):
                # print(f"[MEMORY] Admin found: {username}")
                return username
        return None

    # ── Stats ─────────────────────────────────────────────────

    def get_memory_stats(self):
        # print("[MEMORY] Getting memory stats...")
        examples = self.load_intent_examples()
        memory = self.load_intent_memory()
        users = self.get_all_users()

        stats = {
            "total_base_intents": len(examples),
            "total_learned_intents": len(memory),
            "total_base_examples": sum(len(v) for v in examples.values()),
            "total_learned_examples": sum(len(v) for v in memory.values()),
            "total_users": len(users)
        }
        # print(f"[MEMORY] Stats: {stats}")
        return stats


# ── Singleton Instance ────────────────────────────────────────

_memory_manager = None

def get_memory_manager():
    global _memory_manager
    if _memory_manager is None:
        # print("[MEMORY] Creating singleton MemoryManager...")
        _memory_manager = MemoryManager()
    return _memory_manager