# DeskmateAI/backend/core/command_handler.py

import os
import sys

# ============================================================
# COMMAND HANDLER FOR DESKMATEAI
# Central command processing unit
# Split into prepare() + execute_prepared()
# So pipeline can run speaker verification in parallel
# with command preparation — saving latency
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.core.mapper import get_mapper
from backend.core.command_executor import get_executor
from backend.core.undo_redo import get_undo_redo_manager, get_action_factory
from backend.core.responder import get_responder
from backend.core.context import get_context_manager
from backend.utils.logger import log_info, log_error, log_debug, log_warning, log_action

# ── Command Handler Class ─────────────────────────────────────

class CommandHandler:

    def __init__(self):
        # print("[HANDLER] Initializing CommandHandler...")
        self.mapper = get_mapper()
        self.executor = get_executor()
        self.undo_redo = get_undo_redo_manager()
        self.action_factory = get_action_factory()
        self.responder = get_responder()
        self.context = get_context_manager()
        self._pending_confirmation = None
        log_info("CommandHandler initialized")
        # print("[HANDLER] CommandHandler initialized")

    def prepare(self, intent, command, context):
        """
        Step 1 of parallel execution
        Runs SIMULTANEOUSLY with speaker verification
        Maps intent → handler function + extracts entity
        Returns prepared_command dict
        """
        # print(f"[HANDLER] Preparing command: intent={intent} | command={command}")
        log_debug(f"Preparing: {intent} | {command}")

        try:
            # Special intents — no preparation needed
            if intent in ["undo_command", "redo_command", "write_text"]:
                return {
                    "intent": intent,
                    "command": command,
                    "handler_fn": None,
                    "entity": None,
                    "entry": None,
                    "is_special": True
                }

            # Map intent to handler
            handler_fn, entity, entry = self.mapper.map(intent, command, context)

            prepared = {
                "intent": intent,
                "command": command,
                "handler_fn": handler_fn,
                "entity": entity,
                "entry": entry,
                "is_special": False
            }

            # print(f"[HANDLER] ✅ Prepared: intent={intent} | entity={entity}")
            log_debug(f"Prepared: {intent} | entity={entity}")
            return prepared

        except Exception as e:
            # print(f"[HANDLER] Error preparing command: {e}")
            log_error(f"Error preparing command: {e}")
            return {
                "intent": intent,
                "command": command,
                "handler_fn": None,
                "entity": None,
                "entry": None,
                "is_special": False,
                "error": str(e)
            }

    def execute_prepared(self, prepared, context):
        """
        Step 2 of parallel execution
        Called AFTER speaker verification passes
        Executes already prepared command
        Returns (success, response_key, entity)
        """
        # print(f"[HANDLER] Executing prepared command: {prepared.get('intent')}")
        log_info(f"Executing prepared: {prepared.get('intent')}")

        intent = prepared.get("intent")
        command = prepared.get("command")
        entity = prepared.get("entity")
        entry = prepared.get("entry")
        handler_fn = prepared.get("handler_fn")

        try:
            # ── Special intents ───────────────────────────────

            if intent == "undo_command":
                return self._handle_undo()

            if intent == "redo_command":
                return self._handle_redo()

            if intent == "write_text":
                return self._handle_dictation(command, context)

            # ── Confirmation check ────────────────────────────
            if intent in ["yes", "confirm", "no", "cancel"]:
                return self._handle_confirmation(intent)

            # ── Validate preparation ──────────────────────────
            if "error" in prepared:
                # print(f"[HANDLER] Preparation had error: {prepared['error']}")
                self.responder.speak("error")
                return False, "error", None

            if not handler_fn:
                # print(f"[HANDLER] No handler found for: {intent}")
                log_warning(f"No handler for intent: {intent}")
                self.responder.speak("not_understood")
                return False, "not_understood", None

            # ── Confirmation required ─────────────────────────
            if entry and entry.requires_confirmation:
                return self._request_confirmation(intent, handler_fn, entity, entry)

            # ── Execute ───────────────────────────────────────
            success, result = self.executor.execute(
                intent=intent,
                handler_fn=handler_fn,
                entity=entity,
                entry=entry,
                context=context
            )

            if success:
                # print(f"[HANDLER] ✅ Execution successful: {intent}")
                log_action(
                    context.get("current_user", "unknown"),
                    intent,
                    command,
                    "success"
                )

                # Speak response
                response_key = entry.response_key if entry else "done"
                self.responder.speak(response_key, entity=entity)

                # Update context
                self.context.update(intent, command, entity)

                # Push to undo stack
                if entry and entry.is_undoable:
                    self._push_to_undo_stack(
                        intent, command, entity, handler_fn, context
                    )

                return True, response_key, entity

            else:
                # print(f"[HANDLER] ❌ Execution failed: {intent}")
                log_action(
                    context.get("current_user", "unknown"),
                    intent,
                    command,
                    "failed"
                )
                self.responder.speak("command_failed")
                return False, "command_failed", entity

        except Exception as e:
            # print(f"[HANDLER] Error executing prepared command: {e}")
            log_error(f"Error executing prepared: {e}")
            self.responder.speak("error")
            return False, "error", None

    def handle(self, intent, command, context):
        """
        Legacy single-call handle
        Used when parallel execution is not needed
        e.g. confirmation responses
        """
        # print(f"[HANDLER] Legacy handle: {intent}")
        prepared = self.prepare(intent, command, context)
        return self.execute_prepared(prepared, context)

    def _handle_undo(self):
        """Handle undo command"""
        # print("[HANDLER] Handling undo...")
        can_undo = self.undo_redo.can_undo()

        if not can_undo:
            # print("[HANDLER] Nothing to undo")
            self.responder.speak("nothing_to_undo")
            return False, "nothing_to_undo", None

        success, message = self.undo_redo.undo()
        if success:
            # print(f"[HANDLER] ✅ Undo successful: {message}")
            self.responder.speak("undone")
            log_info(f"Undo successful: {message}")
            return True, "undone", None
        else:
            # print(f"[HANDLER] ❌ Undo failed: {message}")
            self.responder.speak("cannot_undo")
            log_warning(f"Undo failed: {message}")
            return False, "cannot_undo", None

    def _handle_redo(self):
        """Handle redo command"""
        # print("[HANDLER] Handling redo...")
        can_redo = self.undo_redo.can_redo()

        if not can_redo:
            # print("[HANDLER] Nothing to redo")
            self.responder.speak("nothing_to_redo")
            return False, "nothing_to_redo", None

        success, message = self.undo_redo.redo()
        if success:
            # print(f"[HANDLER] ✅ Redo successful: {message}")
            self.responder.speak("redone")
            log_info(f"Redo successful: {message}")
            return True, "redone", None
        else:
            # print(f"[HANDLER] ❌ Redo failed: {message}")
            log_warning(f"Redo failed: {message}")
            return False, "error", None

    def _handle_dictation(self, command, context):
        """Handle dictation mode"""
        # print("[HANDLER] Handling dictation mode...")
        log_info("Entering dictation mode")
        self.context.enter_dictation_mode()
        self.responder.speak("dictation_start")
        # print("[HANDLER] Dictation mode activated")
        return True, "dictation_start", None

    def handle_dictation_text(self, text, context):
        """Handle dictated text — types it"""
        # print(f"[HANDLER] Handling dictated text: {text}")
        log_info(f"Handling dictated text: {text[:50]}...")

        try:
            from backend.utils.utils import process_punctuation
            from backend.automation.ui_typing import type_text

            processed_text = process_punctuation(text)
            # print(f"[HANDLER] Processed text: {processed_text}")

            success = type_text(processed_text)

            if success:
                # print("[HANDLER] ✅ Dictation typed successfully")
                self.responder.speak("dictation_done")
                log_info("Dictation typed successfully")

                def undo_type():
                    import pyautogui
                    for _ in range(len(processed_text)):
                        pyautogui.hotkey('backspace')

                from backend.core.undo_redo import Action
                action = Action(
                    intent="write_text",
                    command="dictation",
                    entity=processed_text,
                    execute_fn=lambda: type_text(processed_text),
                    undo_fn=undo_type,
                    description=f"Typed: {processed_text[:30]}..."
                )
                self.undo_redo.push_action(action)
                self.context.exit_dictation_mode()
                return True, "dictation_done", processed_text
            else:
                # print("[HANDLER] ❌ Dictation typing failed")
                self.responder.speak("command_failed")
                self.context.exit_dictation_mode()
                return False, "command_failed", None

        except Exception as e:
            # print(f"[HANDLER] Error in dictation: {e}")
            log_error(f"Error in dictation: {e}")
            self.context.exit_dictation_mode()
            self.responder.speak("error")
            return False, "error", None

    def _request_confirmation(self, intent, handler_fn, entity, entry):
        """Request confirmation for dangerous commands"""
        # print(f"[HANDLER] Requesting confirmation for: {intent}")
        log_info(f"Confirmation requested for: {intent}")

        self._pending_confirmation = {
            "intent": intent,
            "handler_fn": handler_fn,
            "entity": entity,
            "entry": entry
        }

        confirm_messages = {
            "en": f"Are you sure you want to {entry.description}? Say yes to confirm.",
            "hi": f"क्या आप {entry.description} करना चाहते हैं? हाँ कहें।",
            "mr": f"तुम्हाला {entry.description} करायचे आहे का? हो म्हणा।"
        }

        lang = self.context.get_language()
        message = confirm_messages.get(lang, confirm_messages["en"])
        self.responder.speak_text(message)
        # print(f"[HANDLER] Confirmation pending for: {intent}")
        return True, "ok", None

    def _handle_confirmation(self, response):
        """Handle yes/no confirmation"""
        # print(f"[HANDLER] Confirmation response: {response}")

        if not self._pending_confirmation:
            return False, "error", None

        pending = self._pending_confirmation
        self._pending_confirmation = None

        if response in ["yes", "confirm"]:
            # print(f"[HANDLER] Confirmed: {pending['intent']}")
            log_info(f"Confirmed: {pending['intent']}")
            success, result = self.executor.execute(
                intent=pending["intent"],
                handler_fn=pending["handler_fn"],
                entity=pending["entity"],
                entry=pending["entry"],
                context=self.context.get_context()
            )
            if success:
                response_key = pending["entry"].response_key
                self.responder.speak(response_key, entity=pending["entity"])
                return True, response_key, pending["entity"]
            else:
                self.responder.speak("command_failed")
                return False, "command_failed", None
        else:
            # print(f"[HANDLER] Cancelled: {pending['intent']}")
            log_info(f"Cancelled: {pending['intent']}")
            self.responder.speak_text("Cancelled")
            return True, "ok", None

    def _push_to_undo_stack(self, intent, command, entity, handler_fn, context):
        """Push action to undo stack"""
        # print(f"[HANDLER] Pushing to undo stack: {intent}")
        try:
            from backend.core.undo_redo import Action
            import backend.automation.system_controls as sys_ctrl
            import backend.automation.app_launcher as app_ctrl
            import backend.automation.web_interaction as web_ctrl
            import backend.automation.app_workflows as workflow_ctrl
            import backend.automation.ui_clicking as click_ctrl

            undo_fn = None

            if intent == "open_app" and entity:
                undo_fn = lambda: app_ctrl.close_app(entity)
            elif intent == "close_app" and entity:
                undo_fn = lambda: app_ctrl.open_app(entity)
            elif intent == "volume_up":
                undo_fn = lambda: sys_ctrl.volume_down()
            elif intent == "volume_down":
                undo_fn = lambda: sys_ctrl.volume_up()
            elif intent == "mute":
                undo_fn = lambda: sys_ctrl.unmute()
            elif intent == "unmute":
                undo_fn = lambda: sys_ctrl.mute()
            elif intent == "brightness_up":
                undo_fn = lambda: sys_ctrl.brightness_down()
            elif intent == "brightness_down":
                undo_fn = lambda: sys_ctrl.brightness_up()
            elif intent == "minimize_window":
                undo_fn = lambda: workflow_ctrl.restore_window()
            elif intent == "maximize_window":
                undo_fn = lambda: workflow_ctrl.restore_window()
            elif intent == "new_tab":
                undo_fn = lambda: web_ctrl.close_tab()
            elif intent == "search":
                undo_fn = lambda: web_ctrl.close_tab()
            elif intent == "scroll_up":
                undo_fn = lambda: click_ctrl.scroll_down()
            elif intent == "scroll_down":
                undo_fn = lambda: click_ctrl.scroll_up()
            elif intent == "zoom_in":
                undo_fn = lambda: click_ctrl.zoom_out()
            elif intent == "zoom_out":
                undo_fn = lambda: click_ctrl.zoom_in()
            elif intent == "paste_text":
                import pyautogui
                undo_fn = lambda: pyautogui.hotkey('ctrl', 'z')
            elif intent == "select_all":
                import pyautogui
                undo_fn = lambda: pyautogui.key('escape')

            action = Action(
                intent=intent,
                command=command,
                entity=entity,
                execute_fn=lambda: handler_fn(entity) if entity else handler_fn(),
                undo_fn=undo_fn,
                description=f"Executed: {command}"
            )
            self.undo_redo.push_action(action)
            # print(f"[HANDLER] ✅ Pushed to undo stack: {intent}")

        except Exception as e:
            # print(f"[HANDLER] Error pushing to undo stack: {e}")
            log_error(f"Error pushing to undo stack: {e}")

    def has_pending_confirmation(self):
        return self._pending_confirmation is not None

    def cancel_pending_confirmation(self):
        # print("[HANDLER] Cancelling pending confirmation...")
        self._pending_confirmation = None

    def get_undo_redo_info(self):
        return self.undo_redo.get_stack_info()


# ── Singleton Instance ────────────────────────────────────────

_handler = None

def get_handler():
    global _handler
    if _handler is None:
        # print("[HANDLER] Creating singleton CommandHandler...")
        _handler = CommandHandler()
    return _handler