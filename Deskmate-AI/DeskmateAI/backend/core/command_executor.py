# DeskmateAI/backend/core/command_executor.py

import os
import sys
import time

# ============================================================
# COMMAND EXECUTOR FOR DESKMATEAI
# Final execution layer
# Receives handler function + entity
# Executes with three tier fallback:
# Layer 1: pyautogui
# Layer 2: pywinauto
# Layer 3: ctypes
# Handles all errors gracefully
# Never crashes the system
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Executor Class ────────────────────────────────────────────

class CommandExecutor:

    def __init__(self):
        # print("[EXECUTOR] Initializing CommandExecutor...")
        self._last_execution_time = None
        self._execution_count = 0
        self._failed_count = 0
        log_info("CommandExecutor initialized")
        # print("[EXECUTOR] CommandExecutor initialized")

    def execute(self, intent, handler_fn, entity, entry, context):
        """
        Execute command with full error handling
        Returns (success, result)
        """
        # print(f"[EXECUTOR] Executing: intent={intent} | entity={entity}")
        log_debug(f"Executing: {intent} | entity={entity}")

        start_time = time.time()

        try:
            # Build args based on whether entity is needed
            result = None

            if entry and entry.needs_entity and entity is not None:
                # print(f"[EXECUTOR] Calling handler with entity: {entity}")
                result = handler_fn(entity)
            elif entry and entry.needs_entity and entity is None:
                # print(f"[EXECUTOR] Entity required but not found for: {intent}")
                log_warning(f"Entity required but not found for: {intent}")
                return False, None
            else:
                # print(f"[EXECUTOR] Calling handler without entity")
                result = handler_fn()

            elapsed = time.time() - start_time
            # print(f"[EXECUTOR] ✅ Execution successful in {elapsed:.3f}s: {intent}")
            log_info(f"Executed successfully in {elapsed:.3f}s: {intent}")

            self._execution_count += 1
            self._last_execution_time = elapsed
            return True, result

        except Exception as e:
            elapsed = time.time() - start_time
            # print(f"[EXECUTOR] ❌ Execution failed: {intent} | Error: {e}")
            log_error(f"Execution failed: {intent} | Error: {e}")
            self._failed_count += 1
            return False, None

    def execute_direct(self, fn, *args, **kwargs):
        """
        Execute any function directly
        Used for undo/redo operations
        """
        # print(f"[EXECUTOR] Direct execution: {fn.__name__}")
        try:
            start_time = time.time()
            result = fn(*args, **kwargs)
            elapsed = time.time() - start_time
            # print(f"[EXECUTOR] ✅ Direct execution done in {elapsed:.3f}s")
            log_debug(f"Direct execution done in {elapsed:.3f}s: {fn.__name__}")
            return True, result
        except Exception as e:
            # print(f"[EXECUTOR] ❌ Direct execution failed: {e}")
            log_error(f"Direct execution failed: {e}")
            return False, None

    def execute_with_delay(self, fn, delay=0.5, *args, **kwargs):
        """
        Execute function after a delay
        Used for operations that need time before executing
        """
        # print(f"[EXECUTOR] Delayed execution: {delay}s delay")
        time.sleep(delay)
        return self.execute_direct(fn, *args, **kwargs)

    def execute_sequence(self, steps):
        """
        Execute a sequence of functions
        Used for multi-step operations
        Each step is (fn, args, kwargs, delay_after)
        """
        # print(f"[EXECUTOR] Executing sequence of {len(steps)} steps")
        log_debug(f"Executing sequence of {len(steps)} steps")
        results = []

        for i, step in enumerate(steps):
            fn = step[0]
            args = step[1] if len(step) > 1 else []
            kwargs = step[2] if len(step) > 2 else {}
            delay = step[3] if len(step) > 3 else 0

            # print(f"[EXECUTOR] Step {i+1}/{len(steps)}: {fn.__name__}")
            success, result = self.execute_direct(fn, *args, **kwargs)
            results.append((success, result))

            if not success:
                # print(f"[EXECUTOR] Sequence step {i+1} failed, stopping")
                log_warning(f"Sequence step {i+1} failed, stopping")
                break

            if delay > 0:
                time.sleep(delay)

        all_success = all(r[0] for r in results)
        # print(f"[EXECUTOR] Sequence complete: {'✅' if all_success else '❌'}")
        return all_success, results

    def undo(self):
        """
        Called when undo intent is triggered
        Delegates to undo_redo manager
        """
        # print("[EXECUTOR] Undo triggered from executor")
        try:
            from backend.core.undo_redo import get_undo_redo_manager
            manager = get_undo_redo_manager()
            return manager.undo()
        except Exception as e:
            # print(f"[EXECUTOR] Error in undo: {e}")
            log_error(f"Error in executor undo: {e}")
            return False, "Error"

    def redo(self):
        """
        Called when redo intent is triggered
        Delegates to undo_redo manager
        """
        # print("[EXECUTOR] Redo triggered from executor")
        try:
            from backend.core.undo_redo import get_undo_redo_manager
            manager = get_undo_redo_manager()
            return manager.redo()
        except Exception as e:
            # print(f"[EXECUTOR] Error in redo: {e}")
            log_error(f"Error in executor redo: {e}")
            return False, "Error"

    def safe_execute_pyautogui(self, fn, *args, **kwargs):
        """
        Layer 1: Execute with pyautogui
        Falls back to pywinauto if fails
        """
        # print(f"[EXECUTOR] Layer 1 - pyautogui: {fn.__name__}")
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            result = fn(*args, **kwargs)
            # print(f"[EXECUTOR] ✅ Layer 1 succeeded")
            return True, result
        except Exception as e:
            # print(f"[EXECUTOR] ❌ Layer 1 failed: {e}")
            log_warning(f"pyautogui failed: {e}")
            return False, None

    def safe_execute_pywinauto(self, app_title, action, *args, **kwargs):
        """
        Layer 2: Execute with pywinauto
        For elevated/admin applications
        Falls back to ctypes if fails
        """
        # print(f"[EXECUTOR] Layer 2 - pywinauto: {app_title}")
        try:
            from pywinauto import Desktop, Application
            # Find window by title
            windows = Desktop(backend="uia").windows()
            target = None
            for w in windows:
                if app_title.lower() in w.window_text().lower():
                    target = w
                    break

            if target:
                target.set_focus()
                time.sleep(0.2)
                if action == "close":
                    target.close()
                elif action == "minimize":
                    target.minimize()
                elif action == "maximize":
                    target.maximize()
                elif action == "restore":
                    target.restore()
                # print(f"[EXECUTOR] ✅ Layer 2 succeeded")
                return True, None
            else:
                # print(f"[EXECUTOR] ❌ Layer 2 - window not found: {app_title}")
                return False, None
        except Exception as e:
            # print(f"[EXECUTOR] ❌ Layer 2 failed: {e}")
            log_warning(f"pywinauto failed: {e}")
            return False, None

    def safe_execute_ctypes(self, action, *args, **kwargs):
        """
        Layer 3: Execute with ctypes
        For system level operations
        """
        # print(f"[EXECUTOR] Layer 3 - ctypes: {action}")
        try:
            import ctypes
            if action == "shutdown":
                os.system("shutdown /s /t 5")
            elif action == "restart":
                os.system("shutdown /r /t 5")
            elif action == "sleep":
                ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
            elif action == "lock":
                ctypes.windll.user32.LockWorkStation()
            elif action == "hibernate":
                ctypes.windll.PowrProf.SetSuspendState(1, 1, 0)
            # print(f"[EXECUTOR] ✅ Layer 3 succeeded")
            log_info(f"ctypes executed: {action}")
            return True, None
        except Exception as e:
            # print(f"[EXECUTOR] ❌ Layer 3 failed: {e}")
            log_error(f"ctypes failed: {e}")
            return False, None

    def three_tier_execute(self, pyautogui_fn, pywinauto_fn, ctypes_fn,
                           pyautogui_args=(), pywinauto_args=(), ctypes_args=()):
        """
        Full three tier execution
        Layer 1 → Layer 2 → Layer 3
        """
        # print("[EXECUTOR] Three tier execution starting...")

        # Layer 1
        if pyautogui_fn:
            success, result = self.safe_execute_pyautogui(pyautogui_fn, *pyautogui_args)
            if success:
                # print("[EXECUTOR] ✅ Three tier: Layer 1 succeeded")
                return True, result

        # Layer 2
        if pywinauto_fn:
            success, result = pywinauto_fn(*pywinauto_args)
            if success:
                # print("[EXECUTOR] ✅ Three tier: Layer 2 succeeded")
                return True, result

        # Layer 3
        if ctypes_fn:
            success, result = ctypes_fn(*ctypes_args)
            if success:
                # print("[EXECUTOR] ✅ Three tier: Layer 3 succeeded")
                return True, result

        # print("[EXECUTOR] ❌ All three tiers failed")
        log_error("All three execution tiers failed")
        return False, None

    def get_stats(self):
        """Get execution statistics"""
        # print("[EXECUTOR] Getting stats...")
        return {
            "total_executed": self._execution_count,
            "total_failed": self._failed_count,
            "last_execution_time": self._last_execution_time,
            "success_rate": (
                self._execution_count /
                (self._execution_count + self._failed_count) * 100
                if (self._execution_count + self._failed_count) > 0
                else 0
            )
        }


# ── Singleton Instance ────────────────────────────────────────

_executor = None

def get_executor():
    global _executor
    if _executor is None:
        # print("[EXECUTOR] Creating singleton CommandExecutor...")
        _executor = CommandExecutor()
    return _executor