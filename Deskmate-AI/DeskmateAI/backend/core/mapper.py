# DeskmateAI/backend/core/mapper.py

import os
import sys
import importlib

# ============================================================
# COMMAND MAPPER FOR DESKMATEAI
# Takes intent from registry
# Loads correct automation module
# Returns callable function ready to execute
# Handles entity extraction for each intent type
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.registry import get_registry
from backend.core.context import get_context_manager
from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import (
    extract_app_name,
    extract_search_query,
    extract_volume_level,
    extract_brightness_level,
    normalize_text
)

# ── Mapper Class ──────────────────────────────────────────────

class CommandMapper:

    def __init__(self):
        # print("[MAPPER] Initializing CommandMapper...")
        self.registry = get_registry()
        self.context = get_context_manager()
        self._module_cache = {}  # Cache loaded modules
        log_info("CommandMapper initialized")

    def map(self, intent, command, context):
        """
        Maps intent to executable function
        Returns (callable, entity, registry_entry) or (None, None, None)
        """
        # print(f"[MAPPER] Mapping intent: {intent} | command: {command}")

        # Get registry entry
        entry = self.registry.get(intent)
        if not entry:
            # print(f"[MAPPER] Intent not found in registry: {intent}")
            log_warning(f"Intent not in registry: {intent}")
            return None, None, None

        # Extract entity if needed
        entity = None
        if entry.needs_entity:
            entity = self._extract_entity(
                command,
                entry.entity_type,
                context
            )
            # print(f"[MAPPER] Extracted entity: {entity} (type: {entry.entity_type})")

        # Load handler function
        handler_fn = self._load_handler(
            entry.handler_module,
            entry.handler_function
        )

        if not handler_fn:
            # print(f"[MAPPER] Handler not found: {entry.handler_module}.{entry.handler_function}")
            log_error(f"Handler not found: {entry.handler_module}.{entry.handler_function}")
            return None, entity, entry

        # print(f"[MAPPER] ✅ Mapped: {intent} → {entry.handler_module}.{entry.handler_function}")
        log_debug(f"Mapped: {intent} → {entry.handler_module}.{entry.handler_function}")
        return handler_fn, entity, entry

    def _load_handler(self, module_path, function_name):
        """
        Dynamically load handler function from module
        Uses cache to avoid reloading
        """
        # print(f"[MAPPER] Loading handler: {module_path}.{function_name}")

        try:
            # Check cache first
            cache_key = f"{module_path}.{function_name}"
            if cache_key in self._module_cache:
                # print(f"[MAPPER] Handler from cache: {cache_key}")
                return self._module_cache[cache_key]

            # Build full module path
            # handler_module is like "automation.app_launcher"
            # We need "backend.automation.app_launcher"
            if module_path.startswith("core."):
                full_module_path = f"backend.{module_path}"
            elif module_path.startswith("automation."):
                full_module_path = f"backend.{module_path}"
            else:
                full_module_path = f"backend.{module_path}"

            # print(f"[MAPPER] Importing module: {full_module_path}")

            # Import module
            module = importlib.import_module(full_module_path)

            # Get function
            if not hasattr(module, function_name):
                # print(f"[MAPPER] Function not found in module: {function_name}")
                log_error(f"Function {function_name} not in {full_module_path}")
                return None

            fn = getattr(module, function_name)

            # Cache it
            self._module_cache[cache_key] = fn
            # print(f"[MAPPER] Handler loaded and cached: {cache_key}")
            return fn

        except Exception as e:
            # print(f"[MAPPER] Error loading handler: {e}")
            log_error(f"Error loading handler {module_path}.{function_name}: {e}")
            return None

    def _extract_entity(self, command, entity_type, context):
        """
        Extract entity from command based on entity type
        """
        # print(f"[MAPPER] Extracting entity of type '{entity_type}' from: '{command}'")

        if not entity_type:
            return None

        try:
            if entity_type == "app_name":
                entity = self._extract_app_entity(command, context)
                # print(f"[MAPPER] App entity: {entity}")
                return entity

            elif entity_type == "query":
                entity = extract_search_query(command)
                # print(f"[MAPPER] Search query entity: {entity}")
                return entity if entity else command

            elif entity_type == "level":
                # Try volume level first
                level = extract_volume_level(command)
                if level is None:
                    level = extract_brightness_level(command)
                # print(f"[MAPPER] Level entity: {level}")
                return level

            elif entity_type == "element_name":
                entity = self._extract_element_name(command)
                # print(f"[MAPPER] Element entity: {entity}")
                return entity

            elif entity_type == "text":
                # Return full command as text
                return command

            else:
                # print(f"[MAPPER] Unknown entity type: {entity_type}")
                return None

        except Exception as e:
            # print(f"[MAPPER] Error extracting entity: {e}")
            log_error(f"Error extracting entity: {e}")
            return None

    def _extract_app_entity(self, command, context):
        """Extract app name from command"""
        # print(f"[MAPPER] Extracting app name from: {command}")

        # Common app name mappings
        APP_ALIASES = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "browser": "chrome",
            "firefox": "firefox",
            "mozilla": "firefox",
            "word": "winword",
            "microsoft word": "winword",
            "excel": "excel",
            "microsoft excel": "excel",
            "powerpoint": "powerpnt",
            "notepad": "notepad",
            "paint": "mspaint",
            "calculator": "calc",
            "file explorer": "explorer",
            "explorer": "explorer",
            "task manager": "taskmgr",
            "spotify": "spotify",
            "vlc": "vlc",
            "vs code": "code",
            "visual studio code": "code",
            "vscode": "code",
            "cmd": "cmd",
            "command prompt": "cmd",
            "terminal": "cmd",
            "settings": "ms-settings:",
            "control panel": "control",
            "outlook": "outlook",
            "teams": "teams",
            "zoom": "zoom",
            "discord": "discord",
            "whatsapp": "whatsapp",
            "telegram": "telegram",
            "edge": "msedge",
            "microsoft edge": "msedge",
            "opera": "opera",
            "brave": "brave",
            "steam": "steam",
            "skype": "skype",
            "photoshop": "photoshop",
            "premiere": "premiere",
            "after effects": "afterfx",
        }

        # Extract raw app name
        raw_name = extract_app_name(command)
        # print(f"[MAPPER] Raw app name: {raw_name}")

        # Check aliases
        normalized = raw_name.lower().strip()
        if normalized in APP_ALIASES:
            mapped = APP_ALIASES[normalized]
            # print(f"[MAPPER] App alias found: {normalized} → {mapped}")
            return mapped

        # Check partial matches
        for alias, app in APP_ALIASES.items():
            if alias in normalized or normalized in alias:
                # print(f"[MAPPER] Partial app match: {normalized} → {app}")
                return app

        # Return raw name if no alias found
        # print(f"[MAPPER] No alias found, using raw: {raw_name}")
        return raw_name if raw_name else None

    def _extract_element_name(self, command):
        """Extract UI element name for click commands"""
        # print(f"[MAPPER] Extracting element name from: {command}")

        remove_words = [
            'click', 'press', 'tap', 'on', 'the', 'button',
            'click on', 'please', 'can', 'you'
        ]
        words = command.lower().split()
        element_words = [w for w in words if w not in remove_words]
        result = ' '.join(element_words).strip()
        # print(f"[MAPPER] Element name: {result}")
        return result if result else None

    def get_all_mapped_intents(self):
        """Get list of all mappable intents"""
        # print("[MAPPER] Getting all mapped intents...")
        return self.registry.get_all_intents()

    def clear_cache(self):
        """Clear module cache"""
        # print("[MAPPER] Clearing module cache...")
        self._module_cache.clear()
        log_debug("Module cache cleared")

    def requires_confirmation(self, intent):
        """Check if intent requires user confirmation before executing"""
        # print(f"[MAPPER] Checking confirmation for: {intent}")
        entry = self.registry.get(intent)
        if entry:
            return entry.requires_confirmation
        return False

    def get_response_key(self, intent):
        """Get TTS response key for intent"""
        # print(f"[MAPPER] Getting response key for: {intent}")
        entry = self.registry.get(intent)
        if entry:
            return entry.response_key
        return "done"

    def is_undoable(self, intent):
        """Check if intent action is undoable"""
        # print(f"[MAPPER] Checking undoable for: {intent}")
        entry = self.registry.get(intent)
        if entry:
            return entry.is_undoable
        return False


# ── Singleton Instance ────────────────────────────────────────

_mapper = None

def get_mapper():
    global _mapper
    if _mapper is None:
        # print("[MAPPER] Creating singleton CommandMapper...")
        _mapper = CommandMapper()
    return _mapper
